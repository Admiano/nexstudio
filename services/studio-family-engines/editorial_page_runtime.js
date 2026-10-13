(() => {
  'use strict';
  const plan = JSON.parse(document.getElementById('nex-plan').textContent);
  const page = plan.authoredPage;
  const stage = document.getElementById('nex-stage');
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const width = innerWidth, height = innerHeight;
  const fontSize = Math.min(42, height / (page.lines.length + 4) * .65);
  const lineHeight = fontSize * 1.42;
  const measure = document.createElement('canvas').getContext('2d');
  measure.font = `${fontSize}px "Segoe UI", sans-serif`;
  const columnWidth = Math.min(width * .82, Math.max(...page.lines.map(line => measure.measureText(line).width)) + fontSize * .4);
  const root = document.createElement('section');
  root.className = 'semantic-world authored-page';
  root.dataset.continuityId = 'authored-page';
  root.dataset.semanticEntityId = 'P8 authored editorial page';
  root.dataset.assetId = 'P8-AUTHORED-TYPOGRAPHY';
  root.classList.add('semantic-node');
  root.style.fontSize = `${fontSize}px`;
  root.style.lineHeight = `${lineHeight}px`;
  root.style.color = plan.brand.secondary;
  const lines = [];
  let insertion;
  page.lines.forEach((text, index) => {
    const row = document.createElement('div');
    row.className = 'authored-line';
    row.dataset.sourceLineIndex = String(index);
    if (index === page.vacancy.lineIndex) {
      row.append(document.createTextNode(text.slice(0, page.vacancy.start)));
      insertion = document.createElement('span');
      insertion.className = 'authored-insertion';
      insertion.dataset.continuityId = 'authored-insertion';
      insertion.dataset.semanticEntityId = page.insertion;
      insertion.style.color = plan.brand.ink;
      row.append(insertion, document.createTextNode(text.slice(page.vacancy.end)));
    } else row.textContent = text;
    root.appendChild(row);
    lines.push(row);
  });
  stage.appendChild(root);

  function seek(value) {
    const t = clamp(Number(value) || 0, 0, plan.duration);
    const revealed = t >= page.arrival;
    const progress = revealed ? clamp((t - page.arrival) / Math.max(.001, page.revealEnd - page.arrival)) : 0;
    // Text is the exact accepted Art copy. Only the explicitly withheld word
    // enters; layout reflow never rewrites or removes surrounding words.
    insertion.textContent = revealed ? ` ${page.insertion} ` : page.lines[page.vacancy.lineIndex].slice(page.vacancy.start, page.vacancy.end);
    insertion.style.fontSize = `${revealed ? 1 + 1.2 * progress : 1}em`;
    insertion.style.fontWeight = revealed ? '800' : '400';
    insertion.style.opacity = '1';
    root.style.width = `${columnWidth * (1 - .14 * progress)}px`;
    const scroll = clamp(t / Math.max(.001, page.scrollEnd));
    const vacancyTop = lines[page.vacancy.lineIndex].offsetTop;
    const padding = height * .05;
    const endY = clamp(height * .48 - vacancyTop - lineHeight / 2, padding, Math.max(padding, height - root.offsetHeight - padding));
    const startY = height * .40;
    root.style.top = `${startY + (endY - startY) * scroll}px`;
    const scene = page.scenes.find(s => t >= s.start && t < s.end) || page.scenes.at(-1);
    stage.dataset.sceneId = scene.beatId;
    return probe(t);
  }

  function probe(t = 0) {
    const rect = root.getBoundingClientRect();
    return {time:t, sceneId:stage.dataset.sceneId, eventId:stage.dataset.sceneId,
      visibleSemanticCount:1, visibleAnonymousHelperCount:0, duplicateContinuityIds:[],
      visible:[{continuityId:'authored-page',semanticEntityId:'P8 authored editorial page',assetId:'P8-AUTHORED-TYPOGRAPHY',role:'hero',kind:'authored-typography',rect:[rect.x,rect.y,rect.width,rect.height]}],
      sourceLines:page.lines, renderedLines:lines.map(line => line.textContent),
      insertionVisible:insertion.textContent.trim() === page.insertion && Number(insertion.style.opacity) > 0,
      insertionOpacity:Number(insertion.style.opacity),pageTop:parseFloat(root.style.top),
      insertionRect:(() => {const r=insertion.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})(),
      lineRects:lines.map(line => {const r=line.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}),
      cameraTransform:'native reading-column scroll'};
  }
  window.NexFacelessRenderer = {plan, seek, probe, duration:plan.duration, ratio:plan.ratio};
  seek(0);
})();
