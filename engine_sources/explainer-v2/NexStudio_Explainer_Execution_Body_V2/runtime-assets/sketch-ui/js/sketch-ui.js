/* NexStudio Sketch-UI runtime — seekable ink-on-paper scene components.
   Renders a whole film from a spec: NexSketch.start(window.__FILM_SPEC__).
   Every animation lives on NexMotion timelines (addUpdate / tweens) so the
   HyperFrames self-hosted renderer can scrub window.__timelines deterministically. */
window.NexSketch = (() => {
  const SVGNS = 'http://www.w3.org/2000/svg';

  /* ---------- dom helpers ---------- */
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const h = (tag, cls, parent, text) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text != null) el.textContent = text;
    if (parent) parent.appendChild(el);
    return el;
  };
  const sv = (tag, attrs, parent) => {
    const el = document.createElementNS(SVGNS, tag);
    for (const k in (attrs || {})) el.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(el);
    return el;
  };
  const svgRoot = (parent, vb = '0 0 100 100', cls) =>
    sv('svg', { viewBox: vb, class: cls || '', fill: 'none' }, parent);

  /* ---------- rough.js sketch strokes (seeded => deterministic) ----------
     rough writes fill/stroke as SVG presentation attributes, where var() is
     invalid — resolve CSS custom props to literals here. */
  const cssVar = (n, fb = '#2f2a1e') =>
    (getComputedStyle(document.documentElement).getPropertyValue(n) || '').trim() || fb;
  const resCol = (v) => (typeof v === 'string' && v.startsWith('var('))
    ? cssVar(v.slice(4, -1)) : v;
  const R = { seed: 11 };
  function roughFor(svgEl, opts = {}) {
    return window.rough.svg(svgEl, {
      roughness: opts.roughness ?? 0.7,
      bowing: opts.bowing ?? 1.1,
      stroke: '#2f2a1e',
      strokeWidth: opts.strokeWidth ?? 1.8,
      fill: 'none',
      fillStyle: 'solid',
      ...opts,
      seed: opts.seed ?? ++R.seed,
      stroke: resCol(opts.stroke ?? '#2f2a1e'),
      fill: resCol(opts.fill || 'none'),
    });
  }
  function skNode(svgEl, draw, seed, opts = {}) {
    const fillCol = resCol(opts.fill || 'none');
    let fillEl = null;
    if (fillCol !== 'none') {
      // rough's SVG fills are unreliable + its outline paths are open, so draw
      // the fill as a plain shape under the sketchy stroke.
      const a = draw.args;
      const base = { fill: fillCol, stroke: 'none' };
      fillEl =
        draw.kind === 'path' ? sv('path', { ...base, d: a[0] }) :
        draw.kind === 'rectangle' ? sv('rect', { ...base, x: a[0], y: a[1], width: a[2], height: a[3], rx: Math.min(a[2], a[3]) * 0.08 }) :
        draw.kind === 'circle' ? sv('circle', { ...base, cx: a[0], cy: a[1], r: a[2] / 2 }) :
        draw.kind === 'ellipse' ? sv('ellipse', { ...base, cx: a[0], cy: a[1], rx: a[2] / 2, ry: a[3] / 2 }) : null;
      if (fillEl) { if (opts.cls) fillEl.setAttribute('class', opts.cls); svgEl.appendChild(fillEl); }
    }
    const node = roughFor(svgEl, { ...opts, fill: 'none', seed })[draw.kind](...draw.args);
    if (opts.cls) node.setAttribute('class', (node.getAttribute('class') || '') + ' ' + opts.cls);
    if (fillEl) node._fill = fillEl;
    svgEl.appendChild(node);
    return node;
  }
  const skRect = (svgEl, x, y, w, h, seed, opts) => skNode(svgEl, { kind: 'rectangle', args: [x, y, w, h] }, seed, opts);
  const skLine = (svgEl, x1, y1, x2, y2, seed, opts) => skNode(svgEl, { kind: 'line', args: [x1, y1, x2, y2] }, seed, opts);
  const skCircle = (svgEl, x, y, d, seed, opts) => skNode(svgEl, { kind: 'circle', args: [x, y, d] }, seed, opts);
  const skEllipse = (svgEl, x, y, w, hh, seed, opts) => skNode(svgEl, { kind: 'ellipse', args: [x, y, w, hh] }, seed, opts);
  const skPath = (svgEl, d, seed, opts) => skNode(svgEl, { kind: 'path', args: [d] }, seed, opts);

  /* draw-on: dasharray reveal over timeline window */
  function drawOn(tl, root, start, dur, ease = 'none') {
    const paths = root.matches?.('path') ? [root] : [...(root.querySelectorAll?.('path') || [])];
    paths.forEach((p, i) => {
      let len = 120;
      try { len = p.getTotalLength() || 120; } catch (_) { }
      p.style.strokeDasharray = String(len);
      p.style.strokeDashoffset = String(len);
      p.style.opacity = '0';
      const s = start + i * 0.04, d = Math.max(0.05, dur - i * 0.04);
      tl.addUpdate(s, d, (pr) => {
        p.style.strokeDashoffset = String(len * (1 - pr));
        p.style.opacity = pr > 0 ? '1' : '0';
      }, ease);
    });
  }
  /* paper-motion effect applied to an element — returns its child timeline;
     the master collects `[data-active-motion]` elements and seeks their
     `__nexMotionTimeline` at scene-local time, so effects stay seekable */
  const fx = (el, key, opts = {}) => { try { return NexMotion.apply(el, key, opts); } catch { return null; } };
  const fadeIn = (tl, el, s, d = 0.35, dy = 12) => tl.fromTo(el, { opacity: 0, y: dy }, { opacity: 1, y: 0, duration: d, ease: 'power2.out' }, s);
  const popIn = (tl, el, s, d = 0.4) => tl.fromTo(el, { opacity: 0, scale: 0.86 }, { opacity: 1, scale: 1, duration: d, ease: 'back.out(1.7)' }, s);
  /* numeric / text counters driven by seekable updates */
  const counter = (tl, el, s, d, fmt) => tl.addUpdate(s, d, (p) => { el.textContent = fmt(p); }, 'none');
  /* typewriter */
  const typewrite = (tl, el, text, s, d) => tl.addUpdate(s, d, (p) => {
    el.textContent = text.slice(0, Math.round(text.length * p));
  }, 'none');
  const caretBlink = (tl, el, s, d) => tl.addUpdate(s, d, (p, raw, t) => {
    el.style.opacity = (Math.floor(t * 2.2) % 2 === 0) ? '1' : '0';
  }, 'none');

  /* ---------- icons (thin ink strokes, 24x24 vb) ---------- */
  const ICONS = {
    globe: p => { skCircle(p, 12, 12, 18, 1); skPath(p, 'M3 12h18M12 3c-4 4-4 14 0 18M12 3c4 4 4 14 0 18', 2) },
    folder: p => skPath(p, 'M3 6.5h6l2 2h10v11H3z', 3),
    play: p => skPath(p, 'M7 5l12 7-12 7z', 4),
    mail: p => { skRect(p, 3, 5, 18, 14, 5); skPath(p, 'M3 7l9 6 9-6', 6) },
    cards: p => { skRect(p, 6, 3, 13, 15, 7); skRect(p, 4, 6, 13, 15, 8, { fill: cssVar('--sk-surface') }) },
    at: p => { skCircle(p, 12, 12, 15, 9); skPath(p, 'M15.5 9v4.5c0 1.8 2.6 1.8 2.6 0', 10); skCircle(p, 12, 12, 7, 11) },
    up: p => skPath(p, 'M12 19V6M6 11l6-6 6 6', 12),
    plus: p => skPath(p, 'M12 5v14M5 12h14', 13),
    check: p => skPath(p, 'M5 13l4.5 4.5L19 7', 14),
    home: p => skPath(p, 'M4 11l8-7 8 7v9h-5.5v-6h-5v6H4z', 15),
    list: p => skPath(p, 'M8 6h13M8 12h13M8 18h13M3.5 6h.8M3.5 12h.8M3.5 18h.8', 16),
    bell: p => skPath(p, 'M6 16v-5a6 6 0 0 1 12 0v5l1.5 2.5h-15zM10 21a2.2 2.2 0 0 0 4 0', 17),
    sliders: p => skPath(p, 'M4 8h9m4 0h3M4 16h3m4 0h9M15 5.5v5M9 13.5v5', 18),
    image: p => { skRect(p, 3.5, 4.5, 17, 15, 19); skCircle(p, 8.5, 9.5, 4, 20); skPath(p, 'M4 17l5-4 4 3 4-4 3 3', 21) },
    refresh: p => skPath(p, 'M20 8A8.5 8.5 0 0 0 5.5 6.5L4 8m0-4v4h4M4 16a8.5 8.5 0 0 0 14.5 1.5L20 16m0 4v-4h-4', 22),
    spark: p => skPath(p, 'M12 3l2.2 6.1L21 12l-6.8 2.9L12 21l-2.2-6.1L3 12l6.8-2.9z', 23),
    eye: p => { skPath(p, 'M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12', 24); skCircle(p, 12, 12, 6, 25) },
    pause: p => skPath(p, 'M9 6v12M15 6v12', 26),
    dotgrid: p => [5, 12, 19].map(y => [5, 12, 19].forEach(x => skCircle(p, x, y, 2.6, 27 + x + y))),
    clip: p => skPath(p, 'M8 12.5l7-7a3.6 3.6 0 0 1 5 5l-9 9a5.5 5.5 0 0 1-7.7-7.7l8-8', 28),
  };
  function icon(name, parent, cls) {
    const s = svgRoot(parent, '0 0 24 24', cls || 'sk-icon');
    s.setAttribute('stroke', cssVar('--sk-ink')); s.setAttribute('stroke-width', '1.7');
    s.setAttribute('stroke-linecap', 'round'); s.setAttribute('stroke-linejoin', 'round');
    (ICONS[name] || ICONS.spark)(s);
    return s;
  }
  function cursor(parent) {
    const s = svgRoot(parent, '0 0 26 34', 'sk-cursor-glyph');
    s.setAttribute('width', '26'); s.setAttribute('height', '34');
    skPath(s, 'M5 3 L5 26 L11 20.5 L15 30 L18.5 28.2 L14.6 18.7 L21.5 18 z', 31, { fill: cssVar('--sk-paper'), fillStyle: 'solid', roughness: 0.4 });
    return s;
  }

  /* ---------- word split for display type ---------- */
  function splitWords(el, text) {
    el.textContent = '';
    return text.split(/(\s+)/).map(part => {
      if (/^\s+$/.test(part)) { el.appendChild(document.createTextNode(' ')); return null; }
      const w = h('span', 'w', el, part);
      return w;
    }).filter(Boolean);
  }

  /* ============================================================
     SCENE COMPONENTS — each returns { el, tl } with local timeline
     ============================================================ */
  const scenes = {};

  /* --- type card: serif statement, words rise in --- */
  scenes['type-card'] = (spec) => {
    const el = h('div', 'sk-scene-body', null);
    el.style.cssText = 'flex:1;display:flex;align-items:center;justify-content:center;text-align:center;padding:0 9%';
    const t = h('h2', 'sk-display', el);
    t.style.fontSize = spec.fontSize || '56px';
    const words = splitWords(t, spec.text || '');
    const tl = NexMotion.createTimeline();
    words.forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 26, rotation: 1.2 }, { opacity: 1, y: 0, rotation: 0, duration: 0.55, ease: 'power3.out' }, 0.15 + i * 0.11));
    return { el, tl };
  };

  /* --- chat prompt: icon rail + typed prompt + send --- */
  scenes['chat-prompt'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 8%;gap:18px';
    const box = h('div', 'sk-chat', el);
    const frame = h('div', 'sk-chat-box', box);
    const frameSvg = svgRoot(frame, '0 0 640 190');
    frameSvg.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skRect(frameSvg, 6, 6, 628, 178, 41);
    const rail = h('div', 'sk-chat-icorail', frame);
    (spec.icons || ['globe', 'folder', 'play', 'mail', 'cards']).forEach(n => icon(n, rail));
    const row = h('div', 'sk-chat-row', frame);
    const mention = h('span', 'sk-mention', row);
    icon('at', h('i', '', mention));
    h('span', '', mention, spec.mention || 'Agent');
    const typedRow = h('div', 'sk-chat-row', frame);
    typedRow.style.cssText = 'min-height:46px;align-items:flex-start';
    const typed = h('span', 'sk-typed', typedRow);
    const caret = h('span', 'sk-caret', typedRow);
    const sub = h('div', 'sk-chat-sub', frame);
    const chip = h('span', 'sk-chip', sub, spec.mode || 'Auto');
    chip.insertAdjacentHTML('beforeend', '<svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 3.5 5 6.5 8 3.5" fill="none" stroke="var(--sk-ink)" stroke-width="1.6" stroke-linecap="round"/></svg>');
    const send = h('span', 'sk-send', sub); icon('up', send);
    const tl = NexMotion.createTimeline();
    drawOn(tl, frameSvg, 0, 0.7);
    fx(frame, 'cut-paper-pop', { delay: 0.05, duration: 0.72, intensity: 0.9 });
    [...rail.children].forEach((c, i) => popIn(tl, c, 0.5 + i * 0.07, 0.3));
    fadeIn(tl, mention, 0.55);
    fadeIn(tl, chip, 0.9); fadeIn(tl, send, 0.95);
    const text = spec.text || '';
    caretBlink(tl, caret, 0.6, Math.max(1.4, text.length * 0.055 + 1));
    typewrite(tl, typed, text, 1.0, Math.max(0.8, text.length * 0.05));
    tl.addUpdate(1.0 + Math.max(0.8, text.length * 0.05), 0.35, p => { send.style.transform = `scale(${1 + 0.12 * Math.sin(p * Math.PI)})`; }, 'none');
    if (spec.cursor) {
      const cur = h('div', 'sk-cursor', el); cursor(cur);
      /* enters bottom-right, glides to the send button, clicks, drifts off */
      cur.style.left = '58%'; cur.style.top = '64%';
      tl.fromTo(cur, { opacity: 0, x: 70, y: 60 }, { opacity: 1, x: 0, y: 0, duration: 0.9, ease: 'power2.out' }, 0.15);
      tl.to(cur, { x: 92, y: 58, duration: 0.55, ease: 'power2.inOut' }, 0.75);
      tl.to(cur, { scale: 0.82, duration: 0.12, ease: 'power1.out' }, 1.35);
      tl.to(cur, { scale: 1, duration: 0.15, ease: 'back.out(2)' }, 1.5);
      /* nothing stays stray — cursor drifts off once the click lands */
      const leave = Math.max(2.3, (spec.duration || 4) - 0.9);
      tl.to(cur, { opacity: 0, x: -54, y: -78, duration: 0.45, ease: 'power2.in' }, leave);
    }
    /* caret stops blinking and settles once typing is done */
    const caretEnd = 1.0 + Math.max(0.8, text.length * 0.05);
    tl.addUpdate(caretEnd + 1.1, 0.3, p => { caret.style.opacity = String(1 - p); }, 'power1.inOut');
    return { el, tl };
  };

  /* --- agent window: browser chrome + sidebar + chat + checklist --- */
  scenes['agent-window'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;padding:7% 5% 4.5%';
    const win = h('div', 'sk-window', el);
    win.style.flex = '1';
    const ws = svgRoot(win, '0 0 680 600');
    ws.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none';
    skRect(ws, 4, 4, 672, 592, 51);
    skLine(ws, 4, 52, 676, 52, 52);
    skLine(ws, 184, 52, 184, 596, 53);
    const chrome = h('div', 'sk-chrome', win);
    const dots = h('div', 'sk-dots', chrome); dots.append(h('i'), h('i'), h('i'));
    const brand = h('span', 'sk-brand', chrome); icon('spark', brand); h('span', '', brand, spec.brand || 'STUDIO');
    const pill = h('span', 'sk-pill', chrome, spec.project || 'Select Project'); h('i', 'caret-down', pill);
    const chr = h('div', 'sk-chrome-r', chrome);
    icon('eye', chr); icon('image', chr); icon('sliders', chr); icon('list', chr);
    const body = h('div', 'sk-window-body', win);
    const side = h('div', 'sk-sidebar', body);
    const btn = h('span', 'sk-btn', side); icon('plus', btn); h('span', '', btn, spec.cta || 'New Task');
    h('div', 'sk-navlabel', side, 'Task  1');
    const nav = h('div', 'sk-navitem', side); h('span', '', nav, spec.task || 'launch film'); h('small', '', nav, spec.taskSub || 'now');
    const main = h('div', 'sk-main', body);
    const bubble = h('div', 'sk-bubble', main, spec.prompt || 'build me a launch video');
    const agent = h('div', 'sk-agent', main); h('i', 'dot', agent); h('span', '', agent, spec.status || 'Agent — planning the build…');
    const check = h('ul', 'sk-check', main);
    (spec.checks || []).forEach(c => { const li = h('li', '', check); icon('check', li); h('span', '', li, c); });
    const tl = NexMotion.createTimeline();
    drawOn(tl, ws, 0, 0.8);
    fx(win, 'drop-and-settle', { delay: 0, duration: 0.8, intensity: 0.5 });
    [...dots.children].forEach((d, i) => popIn(tl, d, 0.6 + i * 0.06, 0.25));
    fadeIn(tl, brand, 0.7); fadeIn(tl, pill, 0.75);
    [...chr.children].forEach((c, i) => fadeIn(tl, c, 0.8 + i * 0.05, 0.25));
    fadeIn(tl, btn, 0.75); fadeIn(tl, side.children[1], 0.82); fadeIn(tl, nav, 0.88);
    popIn(tl, bubble, 0.95, 0.45);
    fadeIn(tl, agent, 1.2);
    [...check.children].forEach((li, i) => fadeIn(tl, li, 1.4 + i * 0.26, 0.3));
    const cur = h('div', 'sk-cursor', win); cursor(cur);
    cur.style.right = '6%'; cur.style.bottom = '8%';
    tl.fromTo(cur, { opacity: 0, x: 60, y: 40 }, { opacity: 1, x: 0, y: 0, duration: 0.7 }, 0.5);
    tl.to(cur, { x: -90, y: -160, duration: 0.7, ease: 'power2.inOut' }, 2.2);
    tl.to(cur, { x: -60, y: -30, duration: 0.8, ease: 'power2.inOut' }, 3.0);
    tl.to(cur, { opacity: 0, x: -20, y: 46, duration: 0.4, ease: 'power2.in' }, Math.max(3.9, (spec.duration || 5) - 0.7));
    return { el, tl };
  };

  /* --- step scene: kicker + outlined word + sketch illustration --- */
  scenes['step'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;padding:2% 8%;gap:8px';
    const word = h('h2', 'sk-outline', el, spec.word || 'STEP');
    word.style.marginTop = '4%';
    word.style.fontSize = spec.fontSize || '150px';
    const ill = h('div', 'sk-step-ill', el);
    ill.style.cssText += ';height:46%;justify-content:center;align-items:center';
    const tl = NexMotion.createTimeline();
    const letters = spec.word ? splitWords(word, spec.word) : [];
    letters.forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0.1 + i * 0.13));

    const variant = spec.variant || 'build';
    if (variant === 'build') {
      const w = svgRoot(ill, '0 0 560 300'); w.style.width = '92%';
      skRect(w, 24, 18, 330, 264, 60);                       // code window
      skRect(w, 24, 18, 330, 44, 61);
      skCircle(w, 44, 40, 9, 62); skCircle(w, 62, 40, 9, 63); skCircle(w, 80, 40, 9, 64);
      const lnLens = [190, 150, 210, 120, 175];
      lnLens.forEach((len, i) => {
        const y = 96 + i * 40;
        skPath(w, `M52 ${y} h${len}`, 70 + i, { strokeWidth: 6, roughness: 0.35 });
      });
      skRect(w, 386, 70, 150, 150, 80);                      // preview card
      skPath(w, 'M402 192 l34 -44 24 26 30 -34 34 52', 81, { strokeWidth: 2.2 });
      skCircle(w, 504, 100, 18, 82);
      skPath(w, 'M392 238 h132', 83, { strokeWidth: 2.4 });
      drawOn(tl, w, 0.45, 1.7);
    } else if (variant === 'test') {
      const w = svgRoot(ill, '0 0 560 300'); w.style.width = '92%';
      skCircle(w, 170, 152, 210, 90); skCircle(w, 170, 152, 148, 91); skCircle(w, 170, 152, 84, 92);
      skLine(w, 170, 50, 170, 62, 95, { strokeWidth: 2.2 }); skLine(w, 170, 242, 170, 254, 96, { strokeWidth: 2.2 });
      skLine(w, 68, 152, 80, 152, 97, { strokeWidth: 2.2 }); skLine(w, 260, 152, 272, 152, 98, { strokeWidth: 2.2 });
      const needle = skPath(w, 'M170 152 L170 66', 93, { strokeWidth: 2.6 });
      drawOn(tl, w, 0.4, 1.0);
      tl.addUpdate(0.9, 2.2, (p, raw, t) => { needle.setAttribute('transform', `rotate(${Math.sin(t * 2.2) * 52} 170 152)`); }, 'none');
      [[348, 62], [426, 92], [352, 140], [438, 178], [368, 222], [448, 248]].forEach((pt, i) => {
        skCircle(w, pt[0], pt[1], 19, 100 + i, { fill: cssVar('--sk-surface') });
        const tick = skPath(w, `M${pt[0] - 5} ${pt[1]} l4 4 7 -8`, 110 + i, { strokeWidth: 2.4 });
        tick.style.opacity = '0';
        tl.addUpdate(1.15 + i * 0.26, 0.3, p => { tick.style.opacity = p > 0.5 ? '1' : '0'; }, 'none');
        tl.addUpdate(1.15 + i * 0.26, 0.3, p => {
          const col = p > 0.5 ? cssVar('--sk-mint-deep') : cssVar('--sk-ink');
          (tick.matches?.('path') ? [tick] : [...tick.querySelectorAll('path')]).forEach(q => q.setAttribute('stroke', col));
        }, 'none');
      });
      const lbl = h('div', 'sk-mono', ill, 'TESTS 0/12'); lbl.style.cssText = 'position:absolute;left:10%;bottom:9%;font-size:16px;color:var(--sk-ink-2);letter-spacing:.08em';
      tl.addUpdate(1.3, 1.6, p => { lbl.textContent = `TESTS ${Math.round(p * 12)}/12`; }, 'none');
    } else { /* render */
      const w = svgRoot(ill, '0 0 560 300'); w.style.cssText = 'width:94%;overflow:visible';
      skRect(w, 30, 84, 500, 56, 120, { roughness: 0.4 });
      // mint fill drawn full-width once, revealed via scaleX (deterministic seekable)
      const fillFull = skRect(w, 36, 91, 488, 42, 122, { fill: cssVar('--sk-mint'), stroke: 'none', roughness: 0.2 });
      fillFull.setAttribute('fill', cssVar('--sk-mint'));
      fillFull.style.transformOrigin = '36px 112px';
      fillFull.style.transform = 'scaleX(0.002)';
      const pct = h('div', 'sk-mono', ill, '000%'); pct.style.cssText = 'position:absolute;right:6%;top:24%;font-size:19px;color:var(--sk-ink);letter-spacing:.06em';
      const fr = h('div', 'sk-mono', ill, 'FRAMES 0/612'); fr.style.cssText = 'position:absolute;left:9%;bottom:14%;font-size:14px;color:var(--sk-ink-2);letter-spacing:.08em';
      const dots = h('div', 'sk-dotsrow', ill); dots.style.cssText = 'position:absolute;left:7%;bottom:9%';
      for (let i = 0; i < 7; i++) h('i', '', dots);
      const spin = svgRoot(ill, '0 0 64 64', 'sk-spinner'); spin.style.cssText = 'position:absolute;right:9%;bottom:4%;width:72px;height:72px';
      for (let i = 0; i < 12; i++) { const a = i * 30; const l = skLine(spin, 32, 8, 32, 19, 130 + i, { strokeWidth: 3 }); l.setAttribute('transform', `rotate(${a} 32 32)`); l.setAttribute('stroke-opacity', String(0.3 + i * 0.055)); }
      drawOn(tl, w, 0.35, 0.9);
      tl.addUpdate(0.9, 2.5, (p) => {
        fillFull.style.transform = `scaleX(${Math.max(0.002, p)})`;
        pct.textContent = String(Math.round(p * 100)).padStart(3, '0') + '%';
        fr.textContent = `FRAMES ${Math.round(p * 612)}/612`;
        spin.style.transform = `rotate(${p * 760}deg)`;
        [...dots.children].forEach((d, i) => d.classList.toggle('done', p * 7 > i + 0.5));
      }, 'power1.inOut');
    }
    return { el, tl };
  };

  /* --- phone app mock --- */
  scenes['phone-app'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;align-items:center;justify-content:center;gap:7%';
    const left = h('div', '', el); left.style.cssText = 'display:flex;flex-direction:column;gap:10px;max-width:34%';
    if (spec.caption) { const c = h('h3', 'sk-display', left, spec.caption); c.style.fontSize = '40px'; }
    if (spec.sub) { h('p', 'sk-mono', left, spec.sub).style.cssText = 'font-size:13px;color:var(--sk-ink-2);margin:0'; }
    const ph = h('div', 'sk-phone', el); ph.style.cssText = 'width:272px;height:540px;flex:none';
    const ps = svgRoot(ph, '0 0 272 540'); ps.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skRect(ps, 8, 8, 256, 524, 140, { roughness: 1.6 });
    const scr = h('div', 'sk-phone-screen', ph);
    h('div', 'sk-notch', scr);
    const head = h('div', 'sk-apphead', scr);
    h('b', 'sk-ui', head, spec.appTitle || 'my plants').style.cssText = 'font-size:15px';
    const hb = h('span', '', head); hb.style.cssText = 'display:flex;gap:9px'; icon('search', hb); icon('bell', hb);
    const cards = h('div', 'sk-appcards', scr);
    if (spec.hero) {
      const hero = h('div', 'sk-appcard hero', cards);
      hero.style.cssText = 'flex-direction:column;align-items:stretch;padding:0;overflow:hidden;height:118px;position:relative';
      const hv = svgRoot(hero, '0 0 220 118'); hv.style.cssText = 'width:100%;height:100%';
      skRect(hv, 2, 2, 216, 114, 170);
      skPath(hv, 'M108 96 C 78 66 72 46 72 32 a36 36 0 0 1 72 0 c0 14 -6 34 -36 64 z', 171, { strokeWidth: 2.2 });
      skPath(hv, 'M108 96 V 60', 172, { strokeWidth: 2.2 });
      skPath(hv, 'M60 96 h96', 173, { strokeWidth: 2 });
      const cap = h('div', 'sk-mono', hero, spec.hero); cap.style.cssText = 'position:absolute;left:10px;bottom:8px;font-size:10px;letter-spacing:.1em;color:var(--sk-ink-2)';
    }
    (spec.cards || []).forEach(c => {
      const card = h('div', 'sk-appcard', cards);
      const th = h('div', 'th', card);
      if (c.img) { const im = new Image(); im.src = c.img; th.appendChild(im); }
      else { const g = svgRoot(th, '0 0 40 40'); skPath(g, 'M20 33c-7-8-9-14-9-19a9 9 0 0 1 18 0c0 5-2 11-9 19zM20 33v-8', 150, { strokeWidth: 2 }); }
      const ln = h('div', 'ln', card); h('i'); h('i').style.width = '45%';
      if (c.title) { const b = h('b', 'sk-ui', card, c.title); b.style.cssText = 'font-size:12px;position:absolute;right:8px;top:8px'; card.style.position = 'relative'; }
    });
    const pd = h('div', 'sk-pagedots', scr); (spec.dots || 3) && Array.from({ length: spec.dots || 3 }).forEach((_, i) => { const d = h('i', '', pd); if (i === 0) d.classList.add('on'); });
    const tb = h('div', 'sk-tabbar', scr); (spec.tabs || ['home', 'list', 'plus', 'eye']).forEach(n => icon(n, tb));
    const tl = NexMotion.createTimeline();
    drawOn(tl, ps, 0, 1.0);
    fx(ph, 'drop-and-settle', { delay: 0.02, duration: 0.9, intensity: 0.55 });
    fadeIn(tl, head, 0.8); fadeIn(tl, scr.children[0], 0.7);
    [...cards.children].forEach((c, i) => tl.fromTo(c, { opacity: 0, x: -26 }, { opacity: 1, x: 0, duration: 0.4, ease: 'power2.out' }, 1.0 + i * 0.18));
    fadeIn(tl, pd, 1.6); [...tb.children].forEach((c, i) => popIn(tl, c, 1.7 + i * 0.07, 0.3));
    if (spec.caption) tl.fromTo(left, { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }, 0.3);
    return { el, tl };
  };

  /* --- storyboard grid --- */
  scenes['storyboard'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;padding:2% 8%;gap:14px';
    const headRow = h('div', 'sk-board-head', el);
    headRow.style.position = 'relative';
    const title = h('h2', 'sk-outline', headRow, 'STORYBOARD'); title.style.fontSize = spec.fontSize || '72px';
    const meta = h('div', 'sk-mono', headRow); meta.style.cssText = 'position:absolute;right:0;top:0;text-align:right;font-size:14px;color:var(--sk-ink-2);display:flex;flex-direction:column;gap:5px;white-space:nowrap';
    const counterEl = h('span', '', meta, 'FRAMES 0/12');
    if (spec.note) h('span', '', meta, spec.note).style.cssText = 'font-size:10px;letter-spacing:.1em;color:var(--sk-ink-3);line-height:1.5';
    const grid = h('div', 'sk-cells', el);
    const cells = [];
    const nCells = spec.cells ?? 6;
    for (let i = 0; i < nCells; i++) {
      const cell = h('div', 'sk-cell', grid);
      const cs = svgRoot(cell, '0 0 160 100'); cs.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
      skRect(cs, 3, 3, 154, 94, 200 + i);
      const inner = h('div', 'miniframe', cell);
      const g = svgRoot(inner, '0 0 120 70');
      const seed = 230 + i * 7;
      if ((i + (spec.seedOffset || 0)) % 3 === 0) { skRect(g, 14, 12, 92, 46, seed); skPath(g, 'M14 58h92', seed + 1); skCircle(g, 30, 24, 9, seed + 2); }
      else if ((i + (spec.seedOffset || 0)) % 3 === 1) { skPath(g, 'M60 62C50 50 47 40 47 32a13 13 0 0 1 26 0c0 8-3 18-13 30zM60 62V44', seed); skPath(g, 'M40 62h40', seed + 3); }
      else { skRect(g, 20, 18, 80, 36, seed); skCircle(g, 38, 36, 14, seed + 1); skPath(g, 'M34 36l3 3 6-7', seed + 2, { strokeWidth: 2.2 }); }
      h('div', 'lbl', cell, `${spec.cellLabel || 'FRAME'} ${String(i + 1).padStart(2, '0')}`);
      cells.push({ cell, cs });
    }
    const tl = NexMotion.createTimeline();
    tl.fromTo(title, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }, 0.05);
    cells.forEach(({ cell, cs }, i) => { drawOn(tl, cs, 0.4 + i * 0.16, 0.55); fadeIn(tl, cell.children[1], 0.55 + i * 0.16, 0.3); fadeIn(tl, cell.children[2], 0.62 + i * 0.16, 0.25, 4); tl.addUpdate(0.6 + i * 0.16, 0.4, p => { counterEl.textContent = `FRAMES ${Math.min(12, Math.round((i + p) * (12 / nCells)))}/12`; }, 'none'); });
    fadeIn(tl, meta, 0.9);
    return { el, tl };
  };

  /* --- compose graph: labeled nodes + drawn wires --- */
  scenes['compose-graph'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;padding:4% 7%;gap:10px';
    if (spec.title) { const t = h('h2', 'sk-outline', el, spec.title); t.style.fontSize = spec.fontSize || '92px'; }
    const wrap = h('div', 'sk-graph', el); wrap.style.cssText += ';flex:1;min-height:0';
    const wires = svgRoot(wrap, '0 0 620 400', 'sk-wires');
    const nodes = spec.nodes || [
      { id: 'a', x: 4, y: 8, l: 'SCRIPT', s: 'copy.beats' },
      { id: 'b', x: 4, y: 62, l: 'MEDIA', s: 'sketch.frames' },
      { id: 'c', x: 42, y: 34, l: 'COMPOSE', s: 'scene.assembly' },
      { id: 'd', x: 78, y: 8, l: 'AUDIO', s: 'music+sfx' },
      { id: 'e', x: 78, y: 62, l: 'RENDER', s: 'frames→mp4' },
    ];
    const edges = spec.edges || [['a', 'c'], ['b', 'c'], ['c', 'd'], ['c', 'e']];
    const pos = {};
    nodes.forEach(n => {
      const nd = h('div', 'sk-node', wrap); nd.style.left = n.x + '%'; nd.style.top = n.y + '%';
      h('b', '', nd, n.l).style.cssText = 'font-size:14px';
      h('small', '', nd, n.s || '');
      if (n.x > 10) h('i', 'io in', nd); if (n.x < 80) h('i', 'io', nd);
      pos[n.id] = { x: n.x / 100 * 620 + (n.x > 10 ? -10 : 10) + 55, y: n.y / 100 * 400 + 24 };
      n.el = nd;
    });
    const tl = NexMotion.createTimeline();
    if (spec.title) tl.fromTo(el.children[0], { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0);
    nodes.forEach((n, i) => popIn(tl, n.el, 0.3 + i * 0.14, 0.4));
    edges.forEach((ed, i) => {
      const a = pos[ed[0]], b = pos[ed[1]];
      const midX = (a.x + b.x) / 2;
      const wire = skPath(wires, `M${a.x} ${a.y} C${midX} ${a.y} ${midX} ${b.y} ${b.x} ${b.y}`, 300 + i, { strokeWidth: 2 });
      drawOn(tl, wire, 0.9 + i * 0.3, 0.6);
      const dot = skCircle(wires, a.x, a.y, 9, 350 + i, { fill: cssVar('--sk-mint') });
      tl.addUpdate(1.1 + i * 0.3, 0.55, (p) => {
        const bx = (1 - p) * (1 - p) * (1 - p) * a.x + 3 * (1 - p) * (1 - p) * p * midX + 3 * (1 - p) * p * p * midX + p * p * p * b.x;
        const by = (1 - p) * (1 - p) * (1 - p) * a.y + 3 * (1 - p) * (1 - p) * p * a.y + 3 * (1 - p) * p * p * b.y + p * p * p * b.y;
        dot.setAttribute('transform', `translate(${bx - a.x} ${by - a.y})`);
        dot.style.opacity = p > 0 && p < 1 ? '1' : '0';
      }, 'none');
    });
    return { el, tl };
  };

  /* --- render progress scene (standalone, big) --- */
  scenes['render-bar'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 10%;gap:20px';
    const title = h('h2', 'sk-outline', el, spec.word || 'RENDER'); title.style.fontSize = spec.fontSize || '120px';
    const barWrap = h('div', 'sk-prog', el);
    const bar = h('div', 'sk-prog-bar', barWrap);
    const bs = svgRoot(bar, '0 0 560 30', null); bs.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skRect(bs, 3, 3, 554, 24, 400, { roughness: 0.4 });
    const fill = h('i', 'sk-prog-fill', bar);
    const meta = h('div', 'sk-prog-meta', barWrap);
    const l = h('span', '', meta, spec.label || 'frames → mp4');
    const r = h('span', '', meta, '000%');
    const fr = h('div', 'sk-mono', el, 'FRAMES 0/0'); fr.style.cssText = 'font-size:13px;color:var(--sk-ink-2)';
    const tl = NexMotion.createTimeline();
    tl.fromTo(title, { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0);
    drawOn(tl, bs, 0.3, 0.7);
    fadeIn(tl, l, 0.9); fadeIn(tl, fr, 1.0);
    const total = spec.frames || 612;
    tl.addUpdate(1.0, Math.max(1.6, (spec.duration || 4) - 1.6), p => {
      fill.style.width = `calc(${p * 97}%)`;
      r.textContent = String(Math.round(p * 100)).padStart(3, '0') + '%';
      fr.textContent = `FRAMES ${Math.round(p * total)}/${total}`;
    }, 'power1.inOut');
    return { el, tl };
  };

  /* --- video player frame --- */
  scenes['player'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;padding:4% 8%;gap:14px';
    if (spec.caption) { const c = h('div', 'sk-mono', el, spec.caption); c.style.cssText = 'font-size:13px;color:var(--sk-ink-2);text-align:center;letter-spacing:.1em'; }
    const pl = h('div', 'sk-player', el); pl.style.flex = '1'; pl.style.maxHeight = '62%';
    const ps = svgRoot(pl, '0 0 620 420'); ps.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none';
    skRect(ps, 4, 4, 612, 412, 420);
    skLine(ps, 4, 40, 616, 40, 421);
    const chrome = h('div', 'sk-chrome', pl); chrome.style.padding = '9px 14px';
    const dots = h('div', 'sk-dots', chrome); dots.append(h('i'), h('i'), h('i'));
    h('span', 'sk-mono', chrome, spec.file || 'launch.mp4').style.cssText = 'font-size:12px;color:var(--sk-ink-2)';
    const view = h('div', 'sk-player-view', pl);
    let innerTl = null; let innerHeadline = null;
    if (spec.poster) { const img = h('img', '', view); img.src = spec.poster; img.alt = ''; }
    else {
      // sketched mini product frame: card list left, headline right (like the ref)
      const g = svgRoot(view, '0 0 620 380');
      g.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
      const rows = spec.rows || ['MONSTERA', 'FIDDLE LEAF FIG', 'SNAKE PLANT'];
      rows.forEach((r, i) => {
        const y = 38 + i * 76;
        skRect(g, 42, y, 218, 62, 440 + i);
        skCircle(g, 74, y + 31, 30, 450 + i);
        skPath(g, `M66 ${y + 36} q-6 -14 2 -24 M74 ${y + 38} q2 -18 10 -26 M82 ${y + 36} q8 -10 2 -22`, 460 + i, { strokeWidth: 2 });
        skPath(g, `M98 ${y + 24} h110`, 470 + i, { strokeWidth: 5, roughness: 0.35 });
        skPath(g, `M98 ${y + 44} h${70 + (i * 31) % 30}`, 480 + i, { strokeWidth: 4, roughness: 0.35 });
        const tag = skRect(g, 226, y + 40, 30, 16, 490 + i, { strokeWidth: 1.4 });
        void tag;
      });
      const headline = h('div', '', view); innerHeadline = headline;
      headline.style.cssText = 'position:absolute;left:47%;right:5%;top:22%;display:flex;flex-direction:column;gap:10px';
      const hl = h('div', 'sk-ui', headline, spec.innerTitle || 'NEVER MISS A BEAT');
      hl.style.cssText = 'font-weight:800;font-size:26px;letter-spacing:.02em;line-height:1.15';
      const sub = h('div', 'sk-mono', headline, spec.innerSub || 'every scene, on schedule');
      sub.style.cssText = 'font-size:13px;color:var(--sk-ink-2);letter-spacing:.08em';
      innerTl = g;
    }
    const play = h('div', 'sk-playbtn', view); const pb = svgRoot(play, '0 0 34 34'); pb.style.width = '30px'; pb.style.height = '30px';
    skPath(pb, 'M10 5 L29 17 L10 29 z', 432, { fill: cssVar('--sk-surface') });
    const tr = h('div', 'sk-transport', pl);
    const pv = svgRoot(tr, '0 0 24 24'); pv.style.width = '17px'; icon('play', pv).setAttribute('width', '17');
    const track = h('div', 'sk-track', tr); const tf = h('i', '', track);
    h('span', 'sk-timecode', tr, spec.time || '0:00 / 0:12');
    const tl = NexMotion.createTimeline();
    drawOn(tl, ps, 0, 0.8);
    if (innerTl) drawOn(tl, innerTl, 0.7, 1.0);
    [...dots.children].forEach((d, i) => popIn(tl, d, 0.55 + i * 0.06, 0.25));
    popIn(tl, play, 0.9, 0.5);
    if (innerHeadline) fadeIn(tl, innerHeadline, 1.0, 0.4);
    tl.addUpdate(1.0, 1.4, p => { tf.style.width = (p * 22) + '%'; }, 'none');
    if (spec.caption) fadeIn(tl, el.children[0], 0.2);
    tl.addUpdate(0.9, 0.5, p => { play.style.opacity = String(0.95 - 0.55 * p); play.style.transform = `scale(${1 - 0.18 * p})`; }, 'none');
    return { el, tl };
  };

  /* HyperFrames-style mark: two rounded wedges — one pointing right (top),
     one pointing left (bottom) — overlapping like a folded ribbon. */
  const MARK_A = 'M26 14 Q14 12 14 26 L14 86 Q14 100 28 94 L120 62 Q130 58 121 49 L30 14 Z';
  const MARK_B = 'M174 126 Q186 128 186 114 L186 54 Q186 40 172 46 L80 78 Q70 82 79 91 L170 126 Z';
  const markPaths = (w, seedBase, strokeWidth, fill) => ([
    skPath(w, MARK_A, seedBase, { strokeWidth, fill }),
    skPath(w, MARK_B, seedBase + 1, { strokeWidth, fill }),
  ]);

  /* --- logo mark draw-on (two rounded triangles, mint) --- */
  scenes['logo-mark'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;align-items:center;justify-content:center';
    const w = svgRoot(el, '0 0 200 140'); w.style.width = '40%';
    const [p1, p2] = markPaths(w, 500, 2.4, cssVar('--sk-mint'));
    const tl = NexMotion.createTimeline();
    drawOn(tl, p1, 0.15, 0.9);
    drawOn(tl, p2, 0.5, 0.9);
    if (p1._fill) p1._fill.style.opacity = '0';
    if (p2._fill) p2._fill.style.opacity = '0';
    tl.addUpdate(1.55, 0.7, p => {
      if (p1._fill) p1._fill.style.opacity = String(p);
      if (p2._fill) p2._fill.style.opacity = String(p);
    }, 'power1.inOut');
    tl.addUpdate(2.1, 1.0, (p, raw, t) => { w.style.transform = `rotate(${Math.sin(t * 1.6) * 1.7}deg)`; }, 'none');
    return { el, tl };
  };

  /* --- end card lockup --- */
  scenes['end-card'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;text-align:center';
    const wm = h('div', 'sk-wordmark', el);
    wm.style.fontSize = spec.fontSize || '64px'; wm.style.flexWrap = 'wrap'; wm.style.justifyContent = 'center';
    const first = h('span', '', wm, spec.brandA || 'NEX');
    const second = h('span', '', wm, spec.brandB || 'STUDIO');
    if (spec.mark !== false) {
      const mk = h('span', 'mk', wm);
      const w = svgRoot(mk, '0 0 200 140'); w.style.width = '100%'; w.style.height = '100%';
      markPaths(w, 500, 4.5, cssVar('--sk-mint'));
      wm._mark = mk;
    }
    if (spec.sub) h('div', 'sk-subline', el, spec.sub);
    if (spec.pill) { const p = h('span', 'sk-pill-cta', el, spec.pill); icon('up', p); }
    const tl = NexMotion.createTimeline();
    tl.fromTo(first, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.55, ease: 'power3.out' }, 0.1);
    tl.fromTo(second, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.55, ease: 'power3.out' }, 0.25);
    if (wm._mark) { wm._mark.style.opacity = '0'; tl.addUpdate(0.5, 0.2, p => { wm._mark.style.opacity = '1'; }, 'none'); fx(wm._mark, 'stamp-impact', { delay: 0.5, duration: 0.8, intensity: 1 }); }
    if (spec.sub) tl.fromTo(el.children[1], { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.5 }, 0.8);
    if (spec.pill) tl.fromTo(el.children[el.children.length - 1], { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1, duration: 0.45, ease: 'back.out(1.7)' }, 1.15);
    return { el, tl };
  };

  /* --- hero-build: PROGRESSIVE_HERO_BUILD in paper form — semantic phrase
     chunks rise in stages; the payoff keyword promotes in scale; optional
     support object sits at low dominance to the side --- */
  scenes['hero-build'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;gap:6px';
    const lines = spec.lines || [spec.text || 'the whole idea, drawn.'];
    const stage = spec.promote != null ? Math.max(0, lines.length - 1) : -1;
    const lineEls = lines.map((line, i) => {
      const row = h('div', 'sk-display', el);
      row.style.fontSize = spec.fontSize || (i === stage ? '76px' : '60px');
      row.style.lineHeight = '1.06';
      const words = splitWords(row, line);
      return { row, words };
    });
    /* optional support object — a small sketched frame with a glyph, kept
       subordinate (the grammar's "support visual at low dominance") */
    let support = null;
    if (spec.support !== false) {
      support = h('div', '', el);
      support.style.cssText = 'position:absolute;right:4%;bottom:14%;width:150px;height:120px;opacity:.55';
      const ws = svgRoot(support, '0 0 150 120');
      skRect(ws, 4, 4, 142, 112, 700);
      skPath(ws, spec.supportIcon === 'play' ? 'M62 34 L100 60 L62 86 Z' : 'M40 84 L68 56 L82 70 L108 42 M40 84 h72', 701, { strokeWidth: 2 });
    }
    const tl = NexMotion.createTimeline();
    lineEls.forEach(({ row, words }, i) => {
      const at = 0.15 + i * 0.34;
      /* mask-rise per word, tight ~90ms stagger — semantic chunk lands whole */
      words.forEach((w, j) => tl.fromTo(w, { opacity: 0, y: 26, rotation: -1.4 }, { opacity: 1, y: 0, rotation: 0, duration: 0.42, ease: 'expo.out' }, at + j * 0.09));
      if (i === stage) tl.fromTo(row, { scale: 1 }, { scale: 1.09, duration: 0.5, ease: 'back.out(1.7)' }, at + words.length * 0.09 + 0.14);
    });
    if (support) {
      const ws = support.querySelector('svg');
      drawOn(tl, ws, 0.5, 0.9);
      tl.addUpdate(0.4, 1.4, p => { support.style.opacity = String(0.55 * (0.4 + 0.6 * p)); }, 'power2.out');
    }
    if (spec.caption) { const c = h('div', 'sk-mono', el, spec.caption); c.style.cssText = 'margin-top:20px;font-size:13px;color:var(--sk-ink-2);letter-spacing:.1em'; fadeIn(tl, c, 0.5 + lines.length * 0.34, 0.4); }
    return { el, tl };
  };

  /* --- phrase-swap: PHRASE_REPLACEMENT — one word slot swaps in place via a
     paper mask; used for "X, not Y" reframes --- */
  scenes['phrase-swap'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;gap:10px';
    const lead = h('div', 'sk-display', el, spec.lead || 'not another tool —');
    lead.style.fontSize = spec.fontSize || '58px';
    const slot = h('div', '', el);
    slot.style.cssText = 'position:relative;height:1.3em;font-family:var(--sk-serif);font-size:' + (spec.slotSize || '96px') + ';line-height:1.1';
    const wA = h('span', 'sk-outline', slot, spec.swapFrom || 'rendered.');
    const wB = h('span', '', slot, spec.swapTo || 'directed.');
    wB.style.cssText = 'position:absolute;left:0;top:0;color:var(--sk-mint-deep);font-style:italic';
    const tl = NexMotion.createTimeline();
    splitWords(lead, lead.textContent).forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.4, ease: 'expo.out' }, 0.1 + i * 0.1));
    tl.fromTo(wA, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: 'expo.out' }, 0.5);
    const swapAt = spec.swapAt ?? 1.6;
    /* strike through A, then mask-swap to B */
    tl.addUpdate(swapAt, 0.34, p => { wA.style.opacity = String(1 - p); wA.style.transform = `translateY(${-p * 12}px)`; }, 'power2.in');
    tl.addUpdate(swapAt + 0.22, 0.5, p => { wB.style.clipPath = `inset(0 ${(1 - p) * 100}% 0 0)`; wB.style.opacity = '1'; }, 'expo.out');
    if (spec.caption) { const c = h('div', 'sk-mono', el, spec.caption); c.style.cssText = 'margin-top:26px;font-size:13px;color:var(--sk-ink-2);letter-spacing:.1em'; fadeIn(tl, c, swapAt + 0.6, 0.4); }
    return { el, tl };
  };

  /* --- process-rail: PROCESS_RAIL — nodes on a drawn rail; a focal dot
     travels node to node while each label resolves; rail can collapse into
     a payoff word at the end --- */
  scenes['process-rail'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;gap:30px';
    const head = h('div', 'sk-display', el, spec.title || 'how it moves');
    head.style.fontSize = spec.fontSize || '54px';
    const railWrap = h('div', '', el);
    railWrap.style.cssText = 'position:relative;height:240px';
    const svg = svgRoot(railWrap, '0 0 620 240'); svg.style.cssText = 'width:100%;height:100%';
    const steps = (spec.steps || []).slice(0, 4);
    const n = steps.length || 3;
    const xs = n === 1 ? [310] : steps.map((_, i) => 70 + i * ((620 - 140) / (n - 1)));
    const railY = 118;
    /* rail line */
    const rail = skLine(svg, 56, railY, 564, railY, 800, { strokeWidth: 2.2 });
    const nodes = xs.map((x, i) => {
      const g = sv('g', {}, svg);
      const c = skCircle(g, x, railY, 34, 810 + i, { fill: cssVar('--sk-surface') });
      const lbl = sv('text', { x, y: railY + 78, 'text-anchor': 'middle', 'font-family': "'JetBrains Mono',monospace", 'font-size': '15', 'letter-spacing': '.08em', fill: cssVar('--sk-ink-2') }, g);
      lbl.textContent = steps[i] || `step ${i + 1}`;
      const num = sv('text', { x, y: railY + 7, 'text-anchor': 'middle', 'font-family': "'DM Serif Display',serif", 'font-size': '17', fill: cssVar('--sk-ink') }, g);
      num.textContent = `0${i + 1}`;
      return { g, c, lbl, num };
    });
    /* focal dot rides the rail */
    const dot = skCircle(svg, xs[0], railY, 17, 900, { fill: cssVar('--sk-mint'), stroke: cssVar('--sk-ink'), strokeWidth: 1.6 });
    const tl = NexMotion.createTimeline();
    splitWords(head, head.textContent).forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.4, ease: 'expo.out' }, 0.05 + i * 0.09));
    drawOn(tl, rail, 0.35, 0.7, 'power2.inOut');
    nodes.forEach((nd, i) => {
      const at = 0.75 + i * 0.55;
      /* node pop + label resolve + focal dot travel */
      tl.fromTo(nd.g, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(1.7)', transformOrigin: `${xs[i]}px ${railY}px` }, at);
      /* dot is a rough <g> + its _fill sibling — move via translate, not cx */
      tl.addUpdate(at, 0.5, (p, raw) => {
        if (i > 0 && raw < 0.02) return; /* hold position until this leg starts */
        const x0 = xs[Math.max(0, i - 1)], x1 = xs[i];
        const tf = `translateX(${x0 + (x1 - x0) * p - xs[0]}px)`;
        dot.style.transform = tf;
        if (dot._fill) dot._fill.style.transform = tf;
      }, 'power2.inOut');
      tl.fromTo(nd.lbl, { opacity: 0 }, { opacity: 1, duration: 0.3 }, at + 0.28);
    });
    if (spec.payoff) {
      const pw = h('div', 'sk-serif', el, spec.payoff);
      pw.style.cssText = 'font-style:italic;font-size:30px;color:var(--sk-ink);text-align:center';
      fadeIn(tl, pw, 0.9 + n * 0.55, 0.5);
      /* rail relaxes: dot settles to rest, rail fades slightly */
      tl.addUpdate(0.9 + n * 0.55, 0.6, p => { rail.style.opacity = String(1 - p * 0.45); }, 'power2.out');
    }
    return { el, tl };
  };

  /* --- payoff-lockup: PAYOFF_LOCKUP — convergent settle: parts arrive from
     their own edges into one decisive lockup; longest clean hold --- */
  scenes['payoff-lockup'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;text-align:center';
    const hero = h('div', 'sk-display', el, spec.text || 'films that draw themselves.');
    hero.style.fontSize = spec.fontSize || '68px';
    hero.style.maxWidth = '92%';
    const rule = h('div', '', el); rule.style.cssText = 'width:120px;height:8px;position:relative';
    const ruleSvg = svgRoot(rule, '0 0 120 8'); ruleSvg.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skLine(ruleSvg, 2, 4, 118, 4, 950, { strokeWidth: 2.4 });
    if (spec.sub) h('div', 'sk-mono', el, spec.sub).style.cssText = 'font-size:14px;color:var(--sk-ink-2);letter-spacing:.12em';
    if (spec.pill) { const p = h('span', 'sk-pill-cta', el, spec.pill); icon('up', p); }
    const tl = NexMotion.createTimeline();
    /* words converge — each line-half slides in from a different edge */
    const words = splitWords(hero, hero.textContent);
    words.forEach((w, i) => {
      const dir = i % 2 === 0 ? -1 : 1;
      tl.fromTo(w, { opacity: 0, x: dir * 60, rotation: dir * 2.5 }, { opacity: 1, x: 0, rotation: 0, duration: 0.55, ease: 'expo.out' }, 0.15 + i * 0.1);
    });
    drawOn(tl, ruleSvg, 0.15 + words.length * 0.1 + 0.15, 0.5, 'expo.out');
    const after = el.children;
    if (spec.sub) tl.fromTo(after[2], { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.45 }, 0.7 + words.length * 0.1);
    if (spec.pill) tl.fromTo(after[after.length - 1], { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1, duration: 0.45, ease: 'back.out(1.7)' }, 0.95 + words.length * 0.1);
    return { el, tl };
  };

  /* --- word-object-bridge: WORD_OBJECT_BRIDGE — a keyword lands, then a
     sketched object draws out of its anchor point and takes over --- */
  scenes['word-object-bridge'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;gap:12px;position:relative';
    const line = h('div', 'sk-display', el);
    line.style.fontSize = spec.fontSize || '58px';
    const before = h('span', '', line, (spec.before || 'the ') + ' ');
    const key = h('span', '', line, spec.keyword || 'object');
    key.style.cssText = 'position:relative;color:var(--sk-ink);white-space:nowrap';
    const after = h('span', '', line, ' ' + (spec.after || 'does the work.'));
    /* the object draws from under the keyword, then keyword recedes to label */
    const obj = h('div', '', el);
    obj.style.cssText = 'position:absolute;left:8%;top:46%;width:34%;height:44%';
    const ov = svgRoot(obj, '0 0 210 160'); ov.style.cssText = 'width:100%;height:100%';
    const shapeKind = spec.object || 'card';
    const shapes = [];
    if (shapeKind === 'phone') {
      shapes.push(skRect(ov, 70, 8, 76, 144, 960)); shapes.push(skCircle(ov, 108, 136, 8, 961)); shapes.push(skRect(ov, 78, 20, 60, 96, 962));
    } else if (shapeKind === 'window') {
      shapes.push(skRect(ov, 8, 14, 194, 132, 960)); shapes.push(skRect(ov, 8, 14, 194, 26, 961)); shapes.push(skLine(ov, 20, 68, 120, 68, 963)); shapes.push(skLine(ov, 20, 92, 150, 92, 964)); shapes.push(skLine(ov, 20, 116, 96, 116, 965));
    } else { /* card */
      shapes.push(skRect(ov, 12, 18, 186, 124, 960)); shapes.push(skCircle(ov, 46, 62, 34, 961)); shapes.push(skLine(ov, 74, 50, 168, 50, 962)); shapes.push(skLine(ov, 74, 74, 148, 74, 963)); shapes.push(skLine(ov, 26, 112, 184, 112, 964));
    }
    const tag = h('div', 'sk-mono', obj, spec.keyword || 'object');
    tag.style.cssText = 'position:absolute;left:0;bottom:-6px;font-size:12px;color:var(--sk-ink-2);letter-spacing:.12em';
    const tl = NexMotion.createTimeline();
    splitWords(before, before.textContent).forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.35, ease: 'expo.out' }, 0.05 + i * 0.07));
    tl.fromTo(key, { opacity: 0, scale: 1.25, filter: 'none' }, { opacity: 1, scale: 1, duration: 0.45, ease: 'back.out(1.7)' }, 0.32);
    splitWords(after, after.textContent).forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.35, ease: 'expo.out' }, 0.55 + i * 0.07));
    drawOn(tl, ov, 1.0, 1.0);
    tl.addUpdate(1.15, 0.5, p => { tag.style.opacity = String(p); }, 'power2.out');
    /* keyword shrinks into a label over the object it named */
    tl.addUpdate(1.35, 0.6, p => { key.style.transform = `scale(${1 - p * 0.12})`; key.style.opacity = String(1 - p * 0.35); }, 'power2.inOut');
    tag.style.opacity = '0';
    return { el, tl };
  };

  /* ============================================================
     FILM MASTER — spec → stage + per-scene windows + __timelines

     Scene DOM:  <section.sk-scene> (transition transforms + visibility)
                   └─ .sk-cam      (camera push/pan — never fights transitions)
                      └─ .sk-safe  (content area inside furniture margins)
     Furniture (kickers/foot/index) lives in the margins — content can never
     collide with it because .sk-safe owns the inside lane.

     Motion layering: each scene returns a base timeline `tl` that the master
     seeks at local time. Any child element carrying a NexMotion effect
     (`[data-active-motion]`) gets its `__nexMotionTimeline` seeked at the same
     local time — so paper-motion effects stay deterministic under frame
     stepping.
     ============================================================ */
  function furniture(scene, spec, idx, total) {
    if (spec.kicker) h('div', 'sk-kicker', scene, spec.kicker);
    if (spec.kickerR) h('div', 'sk-kicker tr', scene, spec.kickerR);
    if (spec.foot) h('div', 'sk-foot', scene, spec.foot);
    if (spec.index !== false) h('div', 'sk-index', scene, `${String(idx + 1).padStart(2, '0')}/${String(total).padStart(2, '0')}`);
  }

  /* effects applied through NexMotion live on their own child timeline —
     collect them so the master can seek them at scene-local time */
  function collectEffects(root) {
    const out = [];
    (root.querySelectorAll?.('[data-active-motion]') || []).forEach(el => {
      if (el.__nexMotionTimeline) out.push(el.__nexMotionTimeline);
    });
    if (root.__nexMotionTimeline) out.push(root.__nexMotionTimeline);
    return out;
  }

  function buildScene(spec, idx, total) {
    const sec = h('section', 'sk-scene');
    const cam = h('div', 'sk-cam', sec);
    const safe = h('div', 'sk-safe', cam);
    const body = (scenes[spec.type] || scenes['type-card'])(spec);
    safe.appendChild(body.el);
    furniture(sec, spec, idx, total);
    return { spec, el: sec, cam, tl: body.tl, fx: collectEffects(sec) };
  }

  /* spec.transition → NexMotion transition key; 'fade'/'wipe'/'rise' are
     handled inline (no registry def needed) */
  const TRANSITION_KEYS = {
    torn: 'torn-paper-reveal', push: 'collage-push', page: 'page-turn',
    shuffle: 'card-stack-shuffle', tape: 'tape-peel', crumple: 'crumple-transition',
    paper: 'paper-wipe',
  };
  const TRANSITION_DUR = 0.62;

  function start(filmSpec) {
    const stage = document.querySelector('[data-nex-production-canvas]');
    if (!stage) throw new Error('missing [data-nex-production-canvas] stage');
    stage.classList.add('sk-stage');
    document.documentElement.classList.add('sk'); document.body.classList.add('sk');
    stage.style.setProperty('--sk-tex', `url('${filmSpec.paperTexture || 'sketch-ui/textures/paper006-color-1k.jpg'}')`);
    h('div', 'sk-vignette', stage);

    const scenesBuilt = (filmSpec.scenes || []).map((s, i) => { const b = buildScene(s, i, filmSpec.scenes.length); stage.appendChild(b.el); return b; });

    /* pre-build transition timelines for boundary pairs */
    const transitions = [];
    for (let i = 1; i < scenesBuilt.length; i++) {
      const prev = scenesBuilt[i - 1], next = scenesBuilt[i];
      const key = TRANSITION_KEYS[next.spec.transition];
      if (!key) continue;
      try {
        const tl = NexMotion.transition(prev.el, next.el, key, { duration: TRANSITION_DUR, intensity: 1 });
        tl.pause();
        transitions.push({ tl, outEl: prev.el, inEl: next.el, end: next.spec.start, dur: TRANSITION_DUR });
      } catch (_) { /* unknown key → inline fade below */ }
    }

    const total = filmSpec.durationSeconds;
    const master = NexMotion.createTimeline();
    master.pause();

    master.addUpdate(0, total, (p, raw, time) => {
      /* 1) scene visibility + local-time seeks */
      scenesBuilt.forEach((b) => {
        const s0 = b.spec.start, s1 = b.spec.start + b.spec.duration;
        const tr = transitions.find(t => t.inEl === b.el);
        const on = (time >= s0 && time < s1) || (tr && time >= tr.end - tr.dur && time < tr.end) || (transitions.some(t => t.outEl === b.el) && time >= s1 && time < s1 + TRANSITION_DUR);
        b.el.classList.toggle('on', on);
        if (!on) return;
        const local = Math.min(Math.max(time - s0, 0), b.tl.cursor);
        const inDur = b.spec.transition === 'wipe' ? 0.5 : TRANSITION_KEYS[b.spec.transition] ? 0.01 : 0.3;
        const pIn = Math.min(1, local / inDur);
        const out = s1 - time;
        /* driven transition window (incoming or outgoing): the transition
           timeline owns opacity/transform/clip — skip master's writes */
        const driven = transitions.some(t => (t.inEl === b.el || t.outEl === b.el) && time >= t.end - t.dur && time < t.end);
        if (!driven) {
          const rise = b.spec.transition === 'rise';
          b.el.style.opacity = String(Math.min(1, pIn < 1 ? 0.2 + 0.8 * pIn : 1, out < 0.22 && !transitions.some(t => t.outEl === b.el) ? Math.max(0, out / 0.22) : 1));
          b.el.style.transform = pIn < 1 ? `translateY(${(1 - pIn) * (rise ? 60 : 26)}px)` : '';
          if (b.spec.transition === 'wipe' && pIn < 1) b.el.style.clipPath = `inset(0 ${(1 - pIn) * 100}% 0 0)`; else if (!TRANSITION_KEYS[b.spec.transition]) b.el.style.clipPath = '';
        }
        b.tl.seek(local);
        b.fx.forEach(f => f.seek(local));
        /* camera: push/pan on .sk-cam — transition transforms stay on .sk-scene */
        const cam = b.spec.camera || {};
        const cpush = Number(cam.push || 0), cpan = cam.pan || [0, 0];
        if (cpush || cpan[0] || cpan[1]) {
          const cp = Math.min(1, Math.max(0, local / Math.max(0.001, b.spec.duration)));
          const eased = 1 - Math.pow(1 - cp, 3);
          b.cam.style.transform = `translate(${cpan[0] * eased * 100}%, ${cpan[1] * eased * 100}%) scale(${1 + cpush * eased})`;
        }
      });
      /* 2) driven transitions write after scenes so they win the contested props */
      transitions.forEach(t => {
        const lt = clamp((time - (t.end - t.dur)) / t.dur, 0, 1) * t.dur;
        if (time >= t.end - t.dur && time <= t.end) {
          t.outEl.classList.add('on'); t.inEl.classList.add('on');
          t.tl.seek(lt);
        } else if (time >= t.end) {
          t.tl.seek(t.dur);
          t.outEl.classList.remove('on');
        }
      });
    }, 'none');
    master.seek(0);

    window.__timelines = window.__timelines || {};
    window.__timelines[filmSpec.productionId || 'sketch-film'] = master;
    window.seekComposition = t => master.seek(t);
    return master;
  }

  return { scenes, start, icon, cursor, drawOn };
})();
