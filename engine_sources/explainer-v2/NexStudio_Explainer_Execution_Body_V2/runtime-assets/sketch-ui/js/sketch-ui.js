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

  /* ---------- media assets + inkify ----------
     spec.assets {name: rel-path} → bundle 'media/<name><ext>'; a scene
     param referencing a bare name resolves through this index. */
  let assetIndex = {};
  const mediaOf = (v) => {
    if (!v) return null;
    if (v.includes('/') || v.startsWith('data:') || v.startsWith('http')) return v;
    return assetIndex[v] || `media/${v}`;
  };
  /* images join the paper world via the #sk-inkify filter — edges extracted,
     inverted to dark-line-on-white, then multiply-blended onto the sheet */
  const inkifyImg = (img, spec) => {
    if (spec.inkify === false) {
      img.style.filter = 'grayscale(.35) contrast(1.02)';
      img.style.opacity = '.92';
    } else {
      img.style.filter = 'url(#sk-inkify)';
      img.style.mixBlendMode = 'multiply';
      img.style.opacity = '.9';
    }
    return img;
  };
  const INKIFY_DEFS = `<svg width="0" height="0" style="position:absolute;overflow:hidden"><defs>
    <filter id="sk-inkify" x="-8%" y="-8%" width="116%" height="116%">
      <feColorMatrix type="saturate" values="0"/>
      <feGaussianBlur stdDeviation="0.55"/>
      <feConvolveMatrix order="3" kernelMatrix="-1 -1 -1 -1 8 -1 -1 -1 -1" preserveAlpha="true"/>
      <feComponentTransfer>
        <feFuncR type="linear" slope="-4.5" intercept="2.6"/>
        <feFuncG type="linear" slope="-4.5" intercept="2.6"/>
        <feFuncB type="linear" slope="-4.5" intercept="2.6"/>
      </feComponentTransfer>
    </filter></defs></svg>`;

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
    hash: p => skPath(p, 'M9.5 4L8 20M15.5 4L14 20M4.5 8.5h15M3.5 15.5h15', 29),
    mic: p => { skRect(p, 9, 2.5, 6, 11, 30); skPath(p, 'M5 11a7 7 0 0 0 14 0M12 18v3.5M8.5 21.5h7', 31) },
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
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 9%;gap:14px';
    const t = h('h2', 'sk-display', el);
    t.style.fontSize = spec.fontSize || '56px';
    const words = splitWords(t, spec.text || '');
    if (spec.accent) {
      /* paint the matching word mint */
      words.forEach(w => { if (w.textContent === spec.accent) w.style.color = 'var(--sk-mint-deep)'; });
    }
    const rule = h('div', '', el); rule.style.cssText = 'width:96px;height:8px;position:relative';
    const rs = svgRoot(rule, '0 0 96 8'); rs.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skLine(rs, 2, 4, 94, 4, 1005, { strokeWidth: 2.2 });
    if (spec.sub) { const s = h('div', 'sk-mono', el, spec.sub); s.style.cssText = 'font-size:14px;color:var(--sk-ink-2);letter-spacing:.14em;text-transform:uppercase'; }
    const tl = NexMotion.createTimeline();
    words.forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 26, rotation: 1.2 }, { opacity: 1, y: 0, rotation: 0, duration: 0.55, ease: 'power3.out' }, 0.15 + i * 0.11));
    drawOn(tl, rs, 0.3 + words.length * 0.11, 0.4, 'expo.out');
    if (spec.sub) fadeIn(tl, el.children[el.children.length - 1], 0.6 + words.length * 0.1, 0.35);
    return { el, tl };
  };

  /* --- chat prompt: icon rail + mention + typed prompt + tools rail + send.
     The card owns the frame — ~86% width, tall field, bottom tools row. --- */
  scenes['chat-prompt'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 3%;gap:18px';
    const box = h('div', 'sk-chat', el);
    const frame = h('div', 'sk-chat-box', box);
    frame.style.minHeight = '300px';
    const frameSvg = svgRoot(frame, '0 0 640 300');
    frameSvg.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skRect(frameSvg, 6, 6, 628, 288, 41);
    skLine(frameSvg, 6, 248, 634, 248, 42, { strokeWidth: 1.5 });   // tools-rail divider
    const rail = h('div', 'sk-chat-icorail', frame);
    (spec.icons || ['globe', 'folder', 'play', 'mail', 'cards']).forEach(n => icon(n, rail));
    const row = h('div', 'sk-chat-row', frame);
    const mention = h('span', 'sk-mention', row);
    icon('at', h('i', '', mention));
    h('span', '', mention, spec.mention || 'Agent');
    const typedRow = h('div', 'sk-chat-row', frame);
    typedRow.style.cssText = 'min-height:96px;align-items:flex-start;padding-top:6px';
    const typed = h('span', 'sk-typed', typedRow);
    const caret = h('span', 'sk-caret', typedRow);
    const sub = h('div', 'sk-chat-sub', frame);
    sub.style.cssText += ';border-top:0;position:absolute;left:18px;right:18px;bottom:12px';
    const tools = h('span', '', sub); tools.style.cssText = 'display:flex;gap:12px;align-items:center';
    icon('at', tools); icon('hash', tools); icon('mic', tools);
    (spec.tags || []).slice(0, 3).forEach(t => {
      const tag = h('span', 'sk-chip', tools, `#${t}`);
      tag.style.cssText = 'font-size:10px;padding:2px 7px;margin-left:-4px';
    });
    const right = h('span', '', sub); right.style.cssText = 'display:flex;gap:10px;align-items:center';
    const chip = h('span', 'sk-chip', right, spec.mode || 'Auto');
    chip.insertAdjacentHTML('beforeend', '<svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 3.5 5 6.5 8 3.5" fill="none" stroke="var(--sk-ink)" stroke-width="1.6" stroke-linecap="round"/></svg>');
    const send = h('span', 'sk-send', right); icon('up', send);
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

  /* --- agent window: full desk — chrome + task sidebar + chat column +
     checklist + composer input. Fills the safe lane; every region carries
     real structure so the frame never reads empty. --- */
  scenes['agent-window'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;padding:1% 0';
    const win = h('div', 'sk-window', el);
    win.style.flex = '1';
    win.style.minHeight = '0';
    const ws = svgRoot(win, '0 0 680 600');
    ws.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none';
    skRect(ws, 4, 4, 672, 592, 51);
    skLine(ws, 4, 52, 676, 52, 52);            // chrome divider
    skLine(ws, 184, 52, 184, 596, 53);         // sidebar divider
    const chrome = h('div', 'sk-chrome', win);
    const dots = h('div', 'sk-dots', chrome); dots.append(h('i'), h('i'), h('i'));
    const brand = h('span', 'sk-brand', chrome); icon('spark', brand); h('span', '', brand, spec.brand || 'STUDIO');
    const pill = h('span', 'sk-pill', chrome, spec.project || 'Select Project'); h('i', 'caret-down', pill);
    const chr = h('div', 'sk-chrome-r', chrome);
    icon('eye', chr); icon('image', chr); icon('sliders', chr); icon('list', chr);
    const body = h('div', 'sk-window-body', win);
    /* sidebar — task list driven by spec.tasks [{title, sub, on}] */
    const side = h('div', 'sk-sidebar', body);
    const btn = h('span', 'sk-btn', side); icon('plus', btn); h('span', '', btn, spec.cta || 'New Task');
    const taskList = (spec.tasks || [
      { title: spec.task || 'launch film', sub: spec.taskSub || 'now', on: true },
      { title: spec.task2 || 'rough cut', sub: 'idle' },
    ]).slice(0, 3);
    taskList.forEach((t, ti) => {
      h('div', 'sk-navlabel', side, ti === 0 ? 'Task  1' : ti === 1 ? 'Queue' : 'Done');
      const nav = h('div', 'sk-navitem' + (t.on || ti === 0 ? ' on' : ''), side);
      h('span', '', nav, t.title || `task ${ti + 1}`); h('small', '', nav, t.sub || (ti === 0 ? 'now' : 'idle'));
    });
    /* main column — chat transcript (spec.messages), or prompt+status+checklist */
    const main = h('div', 'sk-main', body);
    let bubble = null;
    if (spec.messages && spec.messages.length) {
      spec.messages.slice(0, 4).forEach(m => {
        const b = h('div', 'sk-bubble' + (m.from === 'agent' ? ' alt' : ''), main, m.text || '');
        if (m.from === 'agent') b.style.alignSelf = 'flex-start';
      });
    } else {
      bubble = h('div', 'sk-bubble', main, spec.prompt || 'build me a launch video');
    }
    const agent = h('div', 'sk-agent', main); h('i', 'dot', agent); h('span', '', agent, spec.status || 'Agent — planning the build…');
    const check = h('ul', 'sk-check', main);
    (spec.checks || []).forEach((c, i) => {
      const li = h('li', '', check); icon('check', li); h('span', '', li, c);
      /* items beyond the first two start unchecked — they tick live */
      if (i >= 2) li.querySelector('span').style.opacity = '.55';
    });
    /* composer input bar pinned to the bottom of the main column */
    const composer = h('div', 'sk-inputline sk-composer', main);
    const cb = h('div', 'sk-composer-box', composer);
    h('span', 'sk-mono', cb, spec.composer || 'Reply to the agent…').style.cssText = 'font-size:12px;color:var(--sk-ink-3);letter-spacing:.04em';
    const csend = h('span', 'sk-send', cb); icon('up', csend);
    const tl = NexMotion.createTimeline();
    drawOn(tl, ws, 0, 0.8);
    fx(win, 'drop-and-settle', { delay: 0, duration: 0.8, intensity: 0.5 });
    [...dots.children].forEach((d, i) => popIn(tl, d, 0.6 + i * 0.06, 0.25));
    fadeIn(tl, brand, 0.7); fadeIn(tl, pill, 0.75);
    [...chr.children].forEach((c, i) => fadeIn(tl, c, 0.8 + i * 0.05, 0.25));
    fadeIn(tl, btn, 0.75);
    [...side.children].forEach((c, i) => { if (i > 0) fadeIn(tl, c, 0.82 + i * 0.05, 0.25); });
    if (bubble) popIn(tl, bubble, 0.95, 0.45);
    if (spec.messages) [...main.querySelectorAll('.sk-bubble')].forEach((b, i) => popIn(tl, b, 0.85 + i * 0.3, 0.4));
    fadeIn(tl, agent, 1.2);
    [...check.children].forEach((li, i) => fadeIn(tl, li, 1.4 + i * 0.26, 0.3));
    /* trailing checklist items tick over live */
    [...check.children].forEach((li, i) => {
      if (i < 2) return;
      const span = li.querySelector('span');
      tl.addUpdate(2.6 + (i - 2) * 0.5, 0.3, p => { span.style.opacity = String(0.55 + 0.45 * p); }, 'none');
    });
    fadeIn(tl, composer, 1.5, 0.4);
    const cur = h('div', 'sk-cursor', win); cursor(cur);
    cur.style.right = '6%'; cur.style.bottom = '10%';
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
    if (spec.caption) {
      const cap = h('div', 'sk-mono', el, spec.caption);
      cap.style.cssText = 'margin-top:auto;padding-bottom:2%;font-size:12px;letter-spacing:.1em;color:var(--sk-ink-3);text-transform:uppercase';
    }
    /* metadata column — mono annotations stacked at the right edge,
       plus an optional result badge like the ref's "(ALL PASSING" */
    let metaCol = null;
    if (spec.meta || spec.result) {
      metaCol = h('div', '', el);
      metaCol.style.cssText = 'position:absolute;right:1%;top:52%;display:flex;flex-direction:column;gap:5px;align-items:flex-end;text-align:right;max-width:30%';
      if (spec.result) {
        const rb = h('span', 'sk-mono', metaCol, spec.result);
        rb.style.cssText = 'font-size:14px;font-weight:700;letter-spacing:.04em;color:var(--sk-ink);border:1.6px solid var(--sk-ink);border-radius:8px;padding:4px 9px;background:var(--sk-mint)';
      }
      (spec.meta || []).slice(0, 4).forEach(m => {
        const mm = h('span', 'sk-mono', metaCol, m);
        mm.style.cssText = 'font-size:10px;letter-spacing:.08em;color:var(--sk-ink-3);text-transform:uppercase';
      });
    }
    const tl = NexMotion.createTimeline();
    const letters = spec.word ? splitWords(word, spec.word) : [];
    letters.forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0.1 + i * 0.13));
    if (metaCol) fadeIn(tl, metaCol, 1.05, 0.4);

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
    /* week strip: 7 day ticks, two with droplet dots — reads as a schedule */
    if (spec.week !== false) {
      const wk = h('div', '', scr);
      wk.style.cssText = 'display:flex;justify-content:space-between;padding:2px 6px 8px';
      'MTWTFSS'.split('').forEach((d, i) => {
        const cell = h('span', '', wk); cell.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:3px;width:24px';
        const dd = h('span', 'sk-mono', cell, d); dd.style.cssText = 'font-size:8px;color:var(--sk-ink-3);letter-spacing:.04em';
        const dt = h('i', '', cell); dt.style.cssText = `width:5px;height:5px;border-radius:50%;${(spec.drops || [1, 3]).includes(i) ? 'background:var(--sk-mint);border:1px solid var(--sk-ink)' : 'border:1px solid var(--sk-ink-3)'}`;
        void dd;
      });
    }
    const cards = h('div', 'sk-appcards', scr);
    if (spec.hero) {
      const hero = h('div', 'sk-appcard hero', cards);
      const rich = typeof spec.hero === 'object';
      hero.style.cssText = `flex-direction:column;align-items:stretch;padding:0;overflow:hidden;height:${rich ? 190 : 118}px;position:relative`;
      const hv = svgRoot(hero, '0 0 220 118'); hv.style.cssText = `width:100%;height:${rich ? '104px' : '100%'};flex:none`;
      skRect(hv, 2, 2, 216, 114, 170);
      const heroImg = rich && spec.hero.img ? mediaOf(spec.hero.img) : null;
      if (heroImg) {
        const im = h('img', '', hero); im.src = heroImg;
        im.style.cssText = 'position:absolute;left:2%;top:2%;width:96%;height:96px;object-fit:cover';
        inkifyImg(im, spec);
      } else {
        skPath(hv, 'M108 96 C 78 66 72 46 72 32 a36 36 0 0 1 72 0 c0 14 -6 34 -36 64 z', 171, { strokeWidth: 2.2 });
        skPath(hv, 'M108 96 V 60', 172, { strokeWidth: 2.2 });
        skPath(hv, 'M60 96 h96', 173, { strokeWidth: 2 });
      }
      const heroTitle = rich ? spec.hero.title : spec.hero;
      if (rich) {
        const ttl = h('div', 'sk-mono', hero, heroTitle || '');
        ttl.style.cssText = 'padding:4px 10px 2px;font-size:12px;letter-spacing:.08em;color:var(--sk-ink);font-weight:700';
        const chipRow = h('div', '', hero); chipRow.style.cssText = 'display:flex;gap:5px;padding:2px 10px 4px;flex-wrap:wrap';
        (spec.hero.chips || []).slice(0, 4).forEach(c => { const ch = h('span', 'sk-mono', chipRow, c); ch.style.cssText = 'font-size:8px;letter-spacing:.06em;border:1px solid var(--sk-ink-3);border-radius:5px;padding:2px 5px;color:var(--sk-ink-2)'; });
        if (spec.hero.cta) {
          const b = h('div', 'sk-mono', hero, spec.hero.cta);
          b.style.cssText = 'margin:auto 10px 8px;text-align:center;font-size:9px;letter-spacing:.1em;border:1.5px solid var(--sk-ink);border-radius:7px;padding:5px 0;background:var(--sk-mint);color:var(--sk-ink);font-weight:700';
        }
      } else {
        const cap = h('div', 'sk-mono', hero, heroTitle || '');
        cap.style.cssText = 'position:absolute;left:10px;bottom:8px;font-size:10px;letter-spacing:.1em;color:var(--sk-ink-2)';
      }
    }
    (spec.cards || []).forEach(c => {
      const card = h('div', 'sk-appcard', cards);
      const th = h('div', 'th', card);
      const cimg = mediaOf(c.img);
      if (cimg) { const im = new Image(); im.src = cimg; inkifyImg(im, spec); th.appendChild(im); }
      else if (c.icon && ICONS[c.icon]) { icon(c.icon, th); }
      else { const g = svgRoot(th, '0 0 40 40'); skPath(g, 'M20 33c-7-8-9-14-9-19a9 9 0 0 1 18 0c0 5-2 11-9 19zM20 33v-8', 150, { strokeWidth: 2 }); }
      /* real copy when supplied, drawn stubs otherwise */
      if (c.title || c.sub) {
        const tx = h('div', '', card); tx.style.cssText = 'flex:1;display:flex;flex-direction:column;gap:3px;min-width:0';
        if (c.title) { const b = h('b', 'sk-ui', tx, c.title); b.style.cssText = 'font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'; }
        if (c.sub) { const s = h('span', 'sk-mono', tx, c.sub); s.style.cssText = 'font-size:9px;color:var(--sk-ink-3);letter-spacing:.05em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'; }
      } else {
        const ln = h('div', 'ln', card); h('i'); h('i').style.width = '45%';
      }
      const meta = c.meta || c.badge;
      if (meta) { const m = h('span', 'sk-mono', card, meta); m.style.cssText = 'margin-left:auto;font-size:9px;color:var(--sk-ink-2);letter-spacing:.08em;border:1px solid var(--sk-ink-3);border-radius:6px;padding:2px 5px;flex:none'; }
      else if (c.title) { const b = h('b', 'sk-ui', card, c.tag || ''); if (c.tag) { b.style.cssText = 'font-size:12px;margin-left:auto;flex:none'; card.style.position = 'relative'; } }
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
    /* cells: a count, or an array of labels — e.g. the film's own beat names */
    const cellSpecs = Array.isArray(spec.cells) ? spec.cells : null;
    const nCells = cellSpecs ? cellSpecs.length : (spec.cells ?? 6);
    for (let i = 0; i < nCells; i++) {
      const cell = h('div', 'sk-cell', grid);
      const cs = svgRoot(cell, '0 0 160 100'); cs.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
      skRect(cs, 3, 3, 154, 94, 200 + i);
      const inner = h('div', 'miniframe', cell);
      /* real art when thumbs are supplied — inkified onto the paper */
      const thumbSrc = mediaOf((spec.thumbs || [])[i]);
      if (thumbSrc) {
        const im = h('img', '', inner); im.src = thumbSrc;
        im.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover';
        inkifyImg(im, spec);
      }
      const g = svgRoot(inner, '0 0 120 70');
      if (thumbSrc) g.style.display = 'none';
      const seed = 230 + i * 7;
      /* each cell is a tiny sketched frame of the film — horizon + subject */
      const v = (i + (spec.seedOffset || 0)) % 4;
      if (v === 0) {                                    /* landscape frame */
        skPath(g, `M12 ${44 + (i % 2) * 4} q18 -18 34 -10 q22 -14 40 -2 q12 -8 22 4`, seed, { strokeWidth: 1.8 });
        skCircle(g, 92, 20, 11, seed + 1);
        skPath(g, 'M12 58h96', seed + 2, { strokeWidth: 1.4 });
      } else if (v === 1) {                             /* figure on stage */
        skCircle(g, 60, 24, 12, seed);
        skPath(g, 'M60 36v18M48 42h24M52 54l-6 10M68 54l6 10', seed + 1, { strokeWidth: 1.8 });
        skPath(g, 'M20 64h80', seed + 2, { strokeWidth: 1.4 });
      } else if (v === 2) {                             /* UI card grid */
        skRect(g, 14, 12, 42, 30, seed, { strokeWidth: 1.6 });
        skRect(g, 64, 12, 42, 30, seed + 1, { strokeWidth: 1.6 });
        skRect(g, 14, 50, 92, 12, seed + 2, { strokeWidth: 1.6 });
        skPath(g, 'M20 22h28M20 30h20', seed + 3, { strokeWidth: 2.4, roughness: 0.3 });
      } else {                                          /* type + underline */
        skPath(g, 'M18 26h84', seed, { strokeWidth: 7, roughness: 0.35 });
        skPath(g, 'M18 40h56', seed + 1, { strokeWidth: 4, roughness: 0.35 });
        skPath(g, 'M60 54c14 -4 30 -4 42 0', seed + 2, { strokeWidth: 2.2 });
      }
      const lblText = cellSpecs ? String(cellSpecs[i]) : `${spec.cellLabel || 'FRAME'} ${String(i + 1).padStart(2, '0')}`;
      h('div', 'lbl', cell, lblText);
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
    const posterSrc = mediaOf(spec.poster);
    if (posterSrc) {
      const img = h('img', '', view); img.src = posterSrc; img.alt = '';
      img.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover';
      inkifyImg(img, spec);
      /* headline may overlay the poster like the ref's "KNOW EVERY LEAF" */
      if (spec.innerTitle || spec.innerSub) {
        const headline = h('div', '', view); innerHeadline = headline;
        headline.style.cssText = 'position:absolute;left:47%;right:5%;top:22%;display:flex;flex-direction:column;gap:10px';
        const hl = h('div', 'sk-ui', headline, spec.innerTitle || '');
        hl.style.cssText = 'font-weight:800;font-size:26px;letter-spacing:.02em;line-height:1.15';
        const sub = h('div', 'sk-mono', headline, spec.innerSub || '');
        sub.style.cssText = 'font-size:13px;color:var(--sk-ink-2);letter-spacing:.08em';
      }
    }
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
    const brandB = spec.brandB === undefined ? 'STUDIO' : spec.brandB;
    const second = brandB ? h('span', '', wm, brandB) : null;
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
    if (second) tl.fromTo(second, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.55, ease: 'power3.out' }, 0.25);
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
    railWrap.style.cssText = 'position:relative;height:320px';
    if (spec.sub) { const s = h('p', 'sk-mono', el, spec.sub); s.style.cssText = 'font-size:14px;color:var(--sk-ink-2);margin:-14px 0 0;letter-spacing:.06em'; }
    const svg = svgRoot(railWrap, '0 0 620 320'); svg.style.cssText = 'width:100%;height:100%';
    const steps = (spec.steps || []).slice(0, 4);
    const n = steps.length || 3;
    const xs = n === 1 ? [310] : steps.map((_, i) => 70 + i * ((620 - 140) / (n - 1)));
    const railY = 130;
    /* rail line */
    const rail = skLine(svg, 56, railY, 564, railY, 800, { strokeWidth: 2.2 });
    const nodes = xs.map((x, i) => {
      const g = sv('g', {}, svg);
      const c = skCircle(g, x, railY, 34, 810 + i, { fill: cssVar('--sk-surface') });
      const lbl = sv('text', { x, y: railY + 78, 'text-anchor': 'middle', 'font-family': "'JetBrains Mono',monospace", 'font-size': '15', 'letter-spacing': '.08em', fill: cssVar('--sk-ink-2') }, g);
      lbl.textContent = steps[i] || `step ${i + 1}`;
      const num = sv('text', { x, y: railY + 7, 'text-anchor': 'middle', 'font-family': "'DM Serif Display',serif", 'font-size': '17', fill: cssVar('--sk-ink') }, g);
      num.textContent = `0${i + 1}`;
      /* caption line under the label — spec.subs[i] or a drawn stub */
      let cap = null;
      if ((spec.subs || [])[i]) {
        cap = sv('text', { x, y: railY + 102, 'text-anchor': 'middle', 'font-family': "'JetBrains Mono',monospace", 'font-size': '11.5', 'letter-spacing': '.05em', fill: cssVar('--sk-ink-3') }, g);
        cap.textContent = spec.subs[i];
      } else {
        cap = skPath(g, `M${x - 24} ${railY + 96} h48`, 860 + i, { strokeWidth: 2.6, roughness: 0.35 });
        cap.style.opacity = '.5';
      }
      return { g, c, lbl, num, cap };
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
      if (nd.cap) tl.fromTo(nd.cap, { opacity: 0 }, { opacity: typeof spec.subs?.[i] === 'string' ? 1 : 0.5, duration: 0.3 }, at + 0.4);
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

  /* --- chapter: section marker — index numeral + big title + drawn rule +
     a giant ghost numeral behind the title so the frame reads composed --- */
  scenes['chapter'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;gap:18px;position:relative';
    if (spec.marker) {
      const mk = h('div', 'sk-mono', el, spec.marker);
      mk.style.cssText = 'font-size:15px;color:var(--sk-mint-deep);letter-spacing:.22em;font-weight:600';
    }
    const t = h('h2', 'sk-display', el, spec.text || '');
    t.style.fontSize = spec.fontSize || '76px';
    t.style.position = 'relative';
    t.style.zIndex = '1';
    const rule = h('div', '', el); rule.style.cssText = 'width:110px;height:8px;position:relative';
    const rs = svgRoot(rule, '0 0 110 8'); rs.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skLine(rs, 2, 4, 108, 4, 1000, { strokeWidth: 2.4 });
    if (spec.sub) { const s = h('p', 'sk-mono', el, spec.sub); s.style.cssText = 'font-size:14px;color:var(--sk-ink-2);margin:0;letter-spacing:.06em;max-width:80%'; }
    /* oversized outlined numeral behind, upper-right — furniture-grade filler */
    if (spec.numeral !== false) {
      const gh = h('div', 'sk-outline', el, spec.numeral || '');
      gh.style.cssText = 'position:absolute;right:-1%;top:-4%;font-size:240px;line-height:.8;opacity:.16;pointer-events:none;user-select:none';
      if (spec.numeral === undefined) gh.textContent = String(spec.index ?? 1).padStart(2, '0');
    }
    const tl = NexMotion.createTimeline();
    if (spec.marker) fadeIn(tl, el.children[0], 0.1, 0.3, 6);
    splitWords(t, t.textContent).forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 30, rotation: 1.4 }, { opacity: 1, y: 0, rotation: 0, duration: 0.55, ease: 'power3.out' }, 0.25 + i * 0.1));
    drawOn(tl, rs, 0.35, 0.45, 'expo.out');
    if (spec.sub) fadeIn(tl, el.children[el.children.length - 1], 0.7, 0.4);
    const ghost = el.querySelector('.sk-outline');
    if (ghost) tl.fromTo(ghost, { opacity: 0 }, { opacity: 0.16, duration: 0.8, ease: 'power1.out' }, 0.4);
    return { el, tl };
  };

  /* --- word-list: semantic list — phrases land one at a time, each underlined
     by a mint marker as it lands --- */
  scenes['word-list'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:space-evenly;gap:6px';
    if (spec.title) { const t = h('h2', 'sk-display', el, spec.title); t.style.fontSize = spec.titleSize || '42px'; }
    const items = (spec.items || []).slice(0, 6);
    const rows = items.map((it, i) => {
      const row = h('div', '', el);
      row.style.cssText = 'display:flex;align-items:baseline;gap:14px;position:relative';
      const idx = h('span', 'sk-mono', row, String(i + 1).padStart(2, '0'));
      idx.style.cssText = 'font-size:13px;color:var(--sk-ink-3);letter-spacing:.1em;flex:none;width:26px';
      const txt = h('span', 'sk-display', row, typeof it === 'string' ? it : it.text || '');
      txt.style.cssText = `font-size:${spec.fontSize || (items.length <= 3 ? '46px' : '40px')};position:relative;line-height:1.12`;
      /* mint marker underlines the phrase's last line — never strikes through */
      const mark = h('span', '', txt);
      mark.style.cssText = 'position:absolute;left:-3%;right:-3%;bottom:-0.05em;height:.15em;background:var(--sk-mint);opacity:.75;transform-origin:0 50%;transform:scaleX(0);z-index:-1;border-radius:2px';
      if (typeof it === 'object' && it.sub) { const s = h('span', 'sk-mono', row, it.sub); s.style.cssText = 'margin-left:auto;font-size:13px;color:var(--sk-ink-2)'; }
      /* hairline ink rule spans the lane under each row — the editorial
         baseline grid that keeps short lists from floating */
      const rl = h('span', '', row);
      rl.style.cssText = 'position:absolute;left:-2%;right:-2%;bottom:-10px;height:6px;pointer-events:none';
      const rlSvg = svgRoot(rl, '0 0 600 6'); rlSvg.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
      skLine(rlSvg, 2, 3, 598, 3, 1100 + i, { strokeWidth: 1.1 });
      rlSvg.style.opacity = '.4';
      return { row, mark, rlSvg };
    });
    const tl = NexMotion.createTimeline();
    let at = 0.15;
    if (spec.title) { splitWords(el.children[0], el.children[0].textContent).forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.4, ease: 'expo.out' }, i * 0.08)); at = 0.45; }
    rows.forEach((r, i) => {
      tl.fromTo(r.row, { opacity: 0, x: -34 }, { opacity: 1, x: 0, duration: 0.42, ease: 'expo.out' }, at + i * 0.5);
      tl.addUpdate(at + i * 0.5 + 0.28, 0.34, p => { r.mark.style.transform = `scaleX(${p})`; }, 'expo.out');
      drawOn(tl, r.rlSvg, at + i * 0.5 + 0.1, 0.3, 'expo.out');
    });
    return { el, tl };
  };

  /* --- feature-grid: N sketched cards (glyph + label) popping with settle --- */
  scenes['feature-grid'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;gap:20px';
    if (spec.title) { const t = h('h2', 'sk-display', el, spec.title); t.style.fontSize = spec.titleSize || '44px'; t.style.textAlign = 'center'; }
    const items = (spec.items || []).slice(0, 6);
    const cols = items.length <= 2 ? items.length : items.length === 4 ? 2 : 3;
    const grid = h('div', '', el);
    grid.style.cssText = `display:grid;grid-template-columns:repeat(${cols},1fr);gap:18px;align-self:stretch;width:100%;flex:1;min-height:0;grid-auto-rows:1fr`;
    const cards = items.map((it, i) => {
      const card = h('div', '', grid);
      card.style.cssText = 'position:relative;border-radius:12px;padding:20px 16px 16px;display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center;min-height:150px;justify-content:center';
      const cs = svgRoot(card, '0 0 200 160'); cs.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none';
      skRect(cs, 4, 4, 192, 152, 1100 + i);
      const g = svgRoot(card, '0 0 44 44'); g.style.cssText = 'width:44px;height:44px';
      (typeof it === 'object' && it.icon ? ICONS[it.icon] || ICONS.spark : ICONS[(['leaf', 'cube', 'wrench', 'spark', 'play', 'check'])[i % 6]])(g);
      g.setAttribute('stroke', cssVar('--sk-ink')); g.setAttribute('stroke-width', '1.7'); g.setAttribute('fill', 'none');
      const ttl = h('b', 'sk-ui', card, typeof it === 'string' ? it : it.title || it.text || '');
      ttl.style.cssText = 'font-size:16px;font-weight:600';
      if (typeof it === 'object' && it.sub) { const s = h('span', 'sk-mono', card, it.sub); s.style.cssText = 'font-size:11.5px;color:var(--sk-ink-2)'; }
      return { card, cs };
    });
    const tl = NexMotion.createTimeline();
    if (spec.title) fadeIn(tl, el.children[0], 0.05, 0.4, 10);
    cards.forEach((c, i) => {
      drawOn(tl, c.cs, 0.25 + i * 0.18, 0.55);
      tl.fromTo(c.card, { opacity: 0, scale: 0.9, y: 14 }, { opacity: 1, scale: 1, y: 0, duration: 0.42, ease: 'back.out(1.7)' }, 0.3 + i * 0.18);
    });
    return { el, tl };
  };

  /* --- stat: giant counting figure + rule + label --- */
  scenes['stat'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;text-align:center';
    const figWrap = h('div', '', el); figWrap.style.cssText = 'position:relative;display:flex;align-items:center;justify-content:center';
    const ring = svgRoot(figWrap, '0 0 360 360'); ring.style.cssText = 'position:absolute;width:118%;aspect-ratio:1;left:50%;top:50%;transform:translate(-50%,-50%);pointer-events:none';
    skCircle(ring, 180, 180, 330, 1250, { strokeWidth: 1.8 });
    skCircle(ring, 180, 180, 316, 1251, { strokeWidth: 1.1 });
    for (let k = 0; k < 12; k++) { const a = k * Math.PI / 6; skLine(ring, 180 + Math.cos(a) * 168, 180 + Math.sin(a) * 168, 180 + Math.cos(a) * 160, 180 + Math.sin(a) * 160, 1252 + k, { strokeWidth: 2 }); }
    const big = h('div', 'sk-display', figWrap);
    big.style.cssText = 'font-size:' + (spec.fontSize || '128px') + ';line-height:1;font-variant-numeric:tabular-nums';
    const label = h('div', 'sk-mono', el, spec.label || '');
    label.style.cssText = 'font-size:15px;color:var(--sk-ink-2);letter-spacing:.16em;text-transform:uppercase';
    const rule = h('div', '', el); rule.style.cssText = 'width:140px;height:8px;position:relative';
    const rs = svgRoot(rule, '0 0 140 8'); rs.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skLine(rs, 2, 4, 138, 4, 1200, { strokeWidth: 2.4 });
    if (spec.sub) { const s = h('p', 'sk-serif', el, spec.sub); s.style.cssText = 'font-style:italic;font-size:22px;color:var(--sk-ink);margin:6px 0 0'; }
    const tl = NexMotion.createTimeline();
    popIn(tl, figWrap, 0.15, 0.5);
    drawOn(tl, ring, 0.2, 0.9);
    const fmt = spec.format || ((v) => String(Math.round(v)));
    const suffix = spec.suffix || '';
    counter(tl, big, 0.4, 1.3, p => fmt(p * Number(spec.value || 0)) + suffix);
    drawOn(tl, rs, 0.9, 0.5, 'expo.out');
    fadeIn(tl, label, 1.05, 0.35, 6);
    if (spec.sub) fadeIn(tl, el.children[el.children.length - 1], 1.3, 0.4);
    return { el, tl };
  };

  /* --- quote: pull-quote with drawn marks + attribution --- */
  scenes['quote'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;gap:16px;padding:0 4%';
    const q = h('div', 'sk-serif', el, `“${spec.text || ''}”`);
    q.style.cssText = `font-size:${spec.fontSize || '44px'};line-height:1.22;font-style:italic;color:var(--sk-ink)`;
    const qs = svgRoot(el, '0 0 46 34'); qs.style.cssText = 'position:absolute;width:52px;height:38px;left:2%;top:16%';
    skPath(qs, 'M6 30 C6 16 14 6 24 4 M30 30 C30 16 38 6 46 4', 1300, { strokeWidth: 2.6 });
    if (spec.by) { const b = h('div', 'sk-mono', el, `— ${spec.by}`); b.style.cssText = 'font-size:14px;color:var(--sk-ink-2);letter-spacing:.12em'; }
    const tl = NexMotion.createTimeline();
    drawOn(tl, qs, 0.1, 0.5);
    splitWords(q, q.textContent).forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.4, ease: 'expo.out' }, 0.35 + i * 0.055));
    if (spec.by) fadeIn(tl, el.children[el.children.length - 1], 0.5 + (spec.text || '').split(' ').length * 0.055, 0.35);
    return { el, tl };
  };

  /* --- media-frame: framed visual slot — real image or drawn placeholder --- */
  scenes['media-frame'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:16px';
    const frame = h('div', '', el);
    frame.style.cssText = 'position:relative;width:min(78%,560px);aspect-ratio:4/3';
    const fs = svgRoot(frame, '0 0 560 420'); fs.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    skRect(fs, 6, 6, 548, 408, 1400, { roughness: 1.7 });
    skRect(fs, 22, 22, 516, 340, 1401, { strokeWidth: 1.4 });
    const mediaSrc = mediaOf(spec.media);
    if (mediaSrc) {
      const im = h('img', '', frame); im.src = mediaSrc;
      im.style.cssText = 'position:absolute;left:4.5%;top:5.5%;width:91%;height:81%;object-fit:cover';
      inkifyImg(im, spec);
    } else {
      const g = svgRoot(frame, '0 0 516 340'); g.style.cssText = 'position:absolute;left:4.5%;top:5.5%;width:91%;height:81%';
      skPath(g, 'M60 260 L170 130 L240 210 L300 150 L410 260', 1402, { strokeWidth: 2.4 });
      skCircle(g, 340, 92, 44, 1403);
      skLine(g, 40, 300, 476, 300, 1404, { strokeWidth: 1.6 });
    }
    if (spec.caption) { const c = h('div', 'sk-mono', el, spec.caption); c.style.cssText = 'font-size:13px;color:var(--sk-ink-2);letter-spacing:.12em'; }
    /* figure index, bottom-right inside the frame */
    const fig = h('div', 'sk-mono', frame, spec.fig || 'FIG.');
    fig.style.cssText = 'position:absolute;right:6%;bottom:5%;font-size:10px;letter-spacing:.14em;color:var(--sk-ink-3)';
    const tl = NexMotion.createTimeline();
    fx(frame, 'unfold', { delay: 0.05, duration: 0.85 });
    drawOn(tl, fs, 0.05, 1.0);
    if (spec.media) tl.fromTo(frame.children[1], { opacity: 0, scale: 1.06 }, { opacity: 0.92, scale: 1, duration: 0.7, ease: 'power2.out' }, 0.7);
    if (spec.caption) fadeIn(tl, el.children[el.children.length - 1], 1.1, 0.35);
    return { el, tl };
  };

  /* --- split: two-column contrast (A vs B / before vs after) --- */
  scenes['split'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;align-items:stretch;justify-content:center;gap:0';
    const mk = (side, i) => {
      const col = h('div', '', el);
      col.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:0 5%';
      const h2 = h('div', i === 0 ? 'sk-outline' : 'sk-display', col, side.title || (i ? 'AFTER' : 'BEFORE'));
      h2.style.fontSize = '46px';
      const lines = (side.items || []).slice(0, 3);
      lines.forEach(t => { const l = h('div', 'sk-mono', col, t); l.style.cssText = 'font-size:14px;color:var(--sk-ink-2);letter-spacing:.04em;text-align:center;line-height:1.5'; });
      return col;
    };
    const a = mk(spec.a || {}, 0), b = mk(spec.b || {}, 1);
    const div = h('div', '', el); div.style.cssText = 'width:0;align-self:stretch;position:relative;margin:6% 0';
    const dv = svgRoot(div, '0 0 8 400'); dv.style.cssText = 'position:absolute;top:0;bottom:0;left:-4px;width:8px;height:100%';
    skLine(dv, 4, 6, 4, 394, 1500, { strokeWidth: 2.2 });
    /* versus badge rides the divider midpoint */
    const vs = h('div', '', div, spec.vs || 'vs');
    vs.style.cssText = 'position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:var(--sk-paper);border:var(--sk-w) solid var(--sk-ink);border-radius:50%;width:44px;height:44px;display:flex;align-items:center;justify-content:center;font:600 14px var(--sk-mono);letter-spacing:.04em;color:var(--sk-ink);white-space:nowrap';
    /* reposition divider between the two columns */
    div.style.order = '0'; el.insertBefore(div, b);
    const tl = NexMotion.createTimeline();
    tl.fromTo(a, { opacity: 0, x: -50 }, { opacity: 1, x: 0, duration: 0.6, ease: 'expo.out' }, 0.15);
    drawOn(tl, dv, 0.55, 0.5);
    tl.fromTo(vs, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(2)' }, 0.95);
    tl.fromTo(b, { opacity: 0, x: 50 }, { opacity: 1, x: 0, duration: 0.6, ease: 'expo.out' }, 0.95);
    return { el, tl };
  };

  /* --- marquee-word: one huge word fills the frame, letters cascade --- */
  scenes['marquee-word'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;gap:12px';
    const t = h('h2', 'sk-outline', el, spec.word || '');
    t.style.fontSize = spec.fontSize || '170px';
    t.style.whiteSpace = 'nowrap';
    if (spec.sub) { const s = h('div', 'sk-mono', el, spec.sub); s.style.cssText = 'font-size:15px;color:var(--sk-ink-2);letter-spacing:.18em;text-transform:uppercase'; }
    const tl = NexMotion.createTimeline();
    const letters = spec.word ? splitWords(t, spec.word) : [];
    letters.forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 46, rotation: 3 }, { opacity: 1, y: 0, rotation: 0, duration: 0.5, ease: 'expo.out' }, 0.1 + i * 0.09));
    if (spec.fillMint) {
      /* mint wash sweeps under the word */
      const wash = h('div', '', el);
      wash.style.cssText = 'position:absolute;left:6%;right:6%;top:58%;height:.2em;background:var(--sk-mint);opacity:.7;transform:scaleX(0);transform-origin:0 50%;z-index:-1;border-radius:3px';
      tl.addUpdate(0.5, 0.7, p => { wash.style.transform = `scaleX(${p})`; }, 'expo.out');
    }
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
    if (spec.note) { const n = h('div', 'sk-mono', scene, spec.note); n.style.cssText = 'position:absolute;left:6.5%;bottom:3.4%;font-size:11px;color:var(--sk-ink-3);letter-spacing:.12em;font-style:italic'; }
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
    spec.index = idx;
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
    stage.style.setProperty('--sk-tex', `url('${filmSpec.paperTexture || 'sketch-ui/textures/paper-warm-1k.png'}')`);
    stage.style.setProperty('--sk-grain', `url('${filmSpec.grainTexture || 'sketch-ui/textures/grain-fine-256.png'}')`);
    h('div', 'sk-vignette', stage);
    /* inkify filter + media asset index */
    stage.insertAdjacentHTML('beforeend', INKIFY_DEFS);
    assetIndex = {};
    for (const [name, rel] of Object.entries(filmSpec.assets || {})) {
      const ext = (rel.match(/\.[^./\\]+$/) || ['.png'])[0];
      assetIndex[name] = `media/${name}${ext}`;
    }

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
      scenesBuilt.forEach((b, bi) => {
        const s0 = b.spec.start, s1 = b.spec.start + b.spec.duration;
        const tr = transitions.find(t => t.inEl === b.el);
        const on = (time >= s0 && time < s1) || (tr && time >= tr.end - tr.dur && time < tr.end) || (transitions.some(t => t.outEl === b.el) && time >= s1 && time < s1 + TRANSITION_DUR);
        b.el.classList.toggle('on', on);
        if (!on) return;
        /* no dead air: while a transition is crossing onto this scene it is
           already mid-entrance (pre-rolled), and frame 0 of the film never
           shows an empty stage */
        const inTr = tr && time >= tr.end - tr.dur && time < tr.end;
        const preroll = bi === 0 ? 0.4 : (inTr ? Math.min(0.5, tr.dur * 0.75) : 0);
        const local = Math.min(Math.max(time - s0 + preroll, 0), b.tl.cursor);
        const inDur = b.spec.transition === 'wipe' ? 0.45 : TRANSITION_KEYS[b.spec.transition] ? 0.01 : 0.3;
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
