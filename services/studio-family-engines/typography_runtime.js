/* Explicit native scene graph. Layout and animation are supplied by the author. */
(() => {
  'use strict';
  const plan = JSON.parse(document.getElementById('nex-plan').textContent);
  const scene = plan.typographyScene, stage = document.getElementById('nex-stage');
  const elements = new Map();
  for (const node of scene.nodes) {
    const el = document.createElement('div');
    el.dataset.semanticId = node.id; el.className = 'native-node ' + node.kind;
    if (node.kind === 'text') {
      el.textContent = node.text;
      el.style.fontFamily = {didone:'NativeDidone',sans:'Arial',mono:'monospace'}[node.font];
      el.style.fontWeight = node.weight || 400; el.style.textAlign = node.align || 'left';
      if (node.deboss) el.style.textShadow = '0 1px 0 rgba(255,255,255,.45),0 -0.4px 0 rgba(0,0,0,.12)';
    }
    if (node.kind === 'paper' && node.grain) {
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" seed="${node.seed || 0}" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#g)" opacity="${node.grain}"/></svg>`;
      el.style.backgroundImage = `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
    }
    stage.appendChild(el); elements.set(node.id, el);
  }
  function value(track, t) {
    const keys = track.keys;
    if (t <= keys[0].time) return keys[0].value;
    for (let i = 1; i < keys.length; i++) {
      const a = keys[i-1], b = keys[i];
      if (t < b.time) {
        let p = (t-a.time)/(b.time-a.time);
        if (a.ease === 'hold') p = 0;
        else if (a.ease === 'easeOut') p = 1-Math.pow(1-p,3);
        else if (a.ease === 'easeInOut') p = p*p*(3-2*p);
        return a.value + (b.value-a.value)*p;
      }
    }
    return keys[keys.length-1].value;
  }
  function seek(t) {
    const width = innerWidth, height = innerHeight, states = new Map(scene.nodes.map(n => [n.id,{...n}]));
    for (const track of scene.tracks) states.get(track.nodeId)[track.property] = value(track,t);
    let visible = 0; const nodes = [], lineRects = [];
    for (const [id,n] of states) {
      const el = elements.get(id);
      const brightness = n.brightness ?? 1;
      const ink = '#' + [1,3,5].map(i => Math.min(255,Math.round(parseInt(n.color.slice(i,i+2),16)*brightness)).toString(16).padStart(2,'0')).join('');
      const filters = [];
      if (n.blur > 0) filters.push(`blur(${n.blur*height/720}px)`);
      if (n.kind === 'paper' && brightness !== 1) filters.push(`brightness(${brightness})`);
      Object.assign(el.style,{left:n.x*width+'px',top:n.y*height+'px',width:n.width*width+'px',height:n.height*height+'px',
        opacity:String(n.opacity),color:ink,fontSize:(n.fontSize || .02)*height+'px',
        filter:filters.join(' ') || 'none',transform:!n.scale || n.scale === 1 ? 'none' : `scale(${n.scale})`});
      if (n.kind !== 'text') el.style.backgroundColor = n.kind === 'paper' ? n.color : ink;
      if (n.kind === 'text' && n.opacity > .01) {
        visible++; const range = document.createRange(); range.selectNodeContents(el);
        const rect = range.getBoundingClientRect(); lineRects.push([rect.x,rect.y,rect.width,rect.height]);
      }
      nodes.push({id,text:n.text,kind:n.kind,opacity:n.opacity,blur:n.blur || 0,x:n.x,y:n.y,fontSize:n.fontSize});
    }
    return {time:t,visibleSemanticCount:visible,visibleAnonymousHelperCount:0,lineRects,nodes,
      fontLoaded:document.fonts.check('48px NativeDidone')};
  }
  window.NexFacelessRenderer = {seek}; seek(0);
})();
