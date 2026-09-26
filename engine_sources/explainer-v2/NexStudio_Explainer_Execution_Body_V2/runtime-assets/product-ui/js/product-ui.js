/* NexStudio Product-UI runtime — clean brand-surface scenes.
   Same spec contract as sketch-ui: NexFilm.start(window.__FILM_SPEC__).
   The surface is what changes — real brand colors, sharp chrome, grotesk
   type — while beats, timing, furniture, camera and audio stay identical.
   Every animation lives on NexMotion timelines: seekable, deterministic. */
window.NexFilm = (() => {
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
  const cssVar = (n, fb = '#f4f3ef') =>
    (getComputedStyle(document.documentElement).getPropertyValue(n) || '').trim() || fb;
  const fsize = (v) => `calc(${v} * var(--pf-display-scale,1))`;
  const fadeIn = (tl, el, s, d = 0.4, dy = 14) => tl.fromTo(el, { opacity: 0, y: dy }, { opacity: 1, y: 0, duration: d, ease: 'power3.out' }, s);
  /* popIn drives the composable CSS scale/opacity properties (not gsap
     transform) so it never stomps a translate(-50%) centering transform */
  const popIn = (tl, el, s, d = 0.45) => {
    el.style.opacity = '0'; el.style.scale = '0.9';
    tl.addUpdate(s, d, (p) => {
      el.style.opacity = String(Math.min(1, p));
      el.style.scale = String(0.9 + 0.1 * p);
    }, 'back.out(1.8)');
  };
  const maskRise = (tl, el, s, d = 0.55, dy = 24) => {
    el.style.overflow = 'hidden';
    const inner = document.createElement('span');
    inner.style.display = 'inline-block';
    while (el.firstChild) inner.appendChild(el.firstChild);
    el.appendChild(inner);
    tl.fromTo(inner, { y: dy + 8, opacity: 0 }, { y: 0, opacity: 1, duration: d, ease: 'power3.out' }, s);
    return inner;
  };
  const counter = (tl, el, s, d, fmt) => tl.addUpdate(s, d, (p) => { el.textContent = fmt(p); }, 'none');
  const typewrite = (tl, el, text, s, d) => tl.addUpdate(s, d, (p) => {
    el.textContent = text.slice(0, Math.round(text.length * p));
  }, 'none');
  const caretBlink = (tl, el, s, d) => tl.addUpdate(s, d, (p, raw, t) => {
    el.style.opacity = (Math.floor(t * 2.4) % 2 === 0) ? '1' : '0';
  }, 'none');
  const splitWords = (el, text) => {
    const words = String(text).split(/\s+/).filter(Boolean);
    el.textContent = '';
    return words.map(w => h('span', 'w', el, w + ' '));
  };
  const drawStroke = (tl, path, s, d, ease = 'power2.out') => {
    let len = 200; try { len = path.getTotalLength() || 200; } catch (_) { }
    path.style.strokeDasharray = String(len); path.style.strokeDashoffset = String(len); path.style.opacity = '0';
    tl.addUpdate(s, d, p => { path.style.strokeDashoffset = String(len * (1 - p)); path.style.opacity = p > 0 ? '1' : '0'; }, ease);
  };
  /* --- decodeIn: scrambl-style decode — chars cycle glyphs then lock L→R.
     Deterministic under seek: glyph choice is a pure hash of (index, step). */
  const GLYPHS = '!<>-_/[]{}=+*^?#·—';
  const decodeIn = (tl, el, text, s, d, lockEnd = 0.8) => {
    const chars = [...text], n = chars.length;
    const glyph = (i, step) => GLYPHS[(((i * 2654435761) ^ (step * 40503)) >>> 0) % GLYPHS.length];
    tl.addUpdate(s, d, (p, raw, t) => {
      const step = Math.floor(t * 22);
      let out = '';
      for (let i = 0; i < n; i++) {
        const lock = 0.08 + 0.72 * (i / Math.max(1, n)) * lockEnd;
        if (chars[i] === ' ') { out += ' '; continue; }
        if (p >= lock) { out += chars[i]; continue; }
        if (p < lock - 0.18) { out += ''; continue; }
        out += glyph(i, step);
      }
      el.textContent = out;
    }, 'none');
    tl.addUpdate(s + d + 0.01, 0.01, (p) => { if (p > 0) el.textContent = text; }, 'none');
  };
  /* --- wheelify: number-flow-style odometer digits — each digit is a masked
     column strip of 0-9 that rolls to its final digit during count-up. */
  const wheelify = (el, prefix, digits, suffix, color) => {
    el.textContent = '';
    el.style.cssText += ';display:inline-flex;align-items:baseline;overflow:hidden;height:1em;line-height:1';
    const cols = [];
    if (prefix) { const p = h('span', '', el, prefix); p.style.lineHeight = '1'; }
    for (let i = 0; i < digits; i++) {
      const col = h('span', '', el);
      col.style.cssText = 'display:inline-block;height:1em;overflow:hidden;vertical-align:top';
      const strip = h('span', '', col);
      strip.style.cssText = 'display:block;will-change:transform';
      for (let d = 0; d <= 9; d++) h('span', '', strip, String(d)).style.cssText = 'display:block;height:1em;line-height:1';
      cols.push(strip);
    }
    if (suffix) { const s = h('span', '', el, suffix); s.style.lineHeight = '1'; if (color) s.style.color = color; }
    return (v) => {
      const str = String(v).padStart(digits, '0');
      cols.forEach((strip, i) => {
        strip.style.transform = `translateY(${-(Number(str[i]) || 0)}em)`;
      });
    };
  };

  /* ---------- media assets ---------- */
  let assetIndex = {};
  let svgAssetIndex = {};
  const mediaOf = (v) => {
    if (!v) return null;
    if (/^(https?:|data:|media\/|\/)/.test(v)) return v;
    return assetIndex[v] || null;
  };
  /* --- pathformer + logoDraw: vivus-style draw-on for supplied SVG marks ---
     Primitives are converted to paths so every logo stroke-draws, then fills
     fade back in once the linework lands. Deterministic under seek. */
  const shapeToPathD = (el) => {
    const tag = el.tagName.toLowerCase();
    const n = (k) => Number(el.getAttribute(k) || 0);
    if (tag === 'rect') {
      const x = n('x'), y = n('y'), w = n('width'), hgt = n('height'), r = Math.min(n('rx'), w / 2);
      return r ? `M${x + r} ${y}H${x + w - r}A${r} ${r} 0 0 1 ${x + w} ${y + r}V${y + hgt - r}A${r} ${r} 0 0 1 ${x + w - r} ${y + hgt}H${x + r}A${r} ${r} 0 0 1 ${x} ${y + hgt - r}V${y + r}A${r} ${r} 0 0 1 ${x + r} ${y}Z`
        : `M${x} ${y}H${x + w}V${y + hgt}H${x}Z`;
    }
    if (tag === 'circle') { const cx = n('cx'), cy = n('cy'), r = n('r'); return `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`; }
    if (tag === 'ellipse') { const cx = n('cx'), cy = n('cy'), rx = n('rx'), ry = n('ry'); return `M${cx - rx} ${cy}a${rx} ${ry} 0 1 0 ${2 * rx} 0a${rx} ${ry} 0 1 0 ${-2 * rx} 0Z`; }
    if (tag === 'line') return `M${n('x1')} ${n('y1')}L${n('x2')} ${n('y2')}`;
    if (tag === 'polyline' || tag === 'polygon') {
      const pts = (el.getAttribute('points') || '').trim().split(/\s+/).join(' L ');
      return `M${pts}${tag === 'polygon' ? 'Z' : ''}`;
    }
    return '';
  };
  const logoSvgIn = (box, svgText) => {
    box.innerHTML = svgText;
    const svg = box.querySelector('svg');
    if (!svg) { box.innerHTML = ''; return null; }
    svg.removeAttribute('width'); svg.removeAttribute('height');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.style.cssText += ';width:100%;height:100%;overflow:visible';
    svg.querySelectorAll('rect,circle,ellipse,line,polyline,polygon').forEach(el2 => {
      const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      p.setAttribute('d', shapeToPathD(el2));
      for (const a of [...el2.attributes]) {
        if (!['x', 'y', 'width', 'height', 'rx', 'ry', 'cx', 'cy', 'r', 'points', 'x1', 'y1', 'x2', 'y2'].includes(a.name)) p.setAttribute(a.name, a.value);
      }
      el2.replaceWith(p);
    });
    const parts = [...svg.querySelectorAll('path')].map(p => {
      let len = 300; try { len = p.getTotalLength() || 300; } catch (_) { }
      const fill = p.getAttribute('fill');
      const stroke = p.getAttribute('stroke');
      p.setAttribute('fill', 'none');
      p.setAttribute('stroke', stroke && stroke !== 'none' ? stroke : cssVar('--pf-fg'));
      p.setAttribute('stroke-width', p.getAttribute('stroke-width') || '1.7');
      p.setAttribute('stroke-linecap', 'round');
      p.style.strokeDasharray = String(len);
      p.style.strokeDashoffset = String(len);
      p.style.opacity = '0';
      return { el: p, len, fill };
    });
    return parts;
  };
  const drawPathSeq = (tl, parts, s, d) => {
    const n = Math.max(1, parts.length);
    const slice = d / n;
    parts.forEach((pt, i) => {
      const st = s + i * slice * 0.62;
      const dur = Math.max(0.05, Math.min(slice * 1.5, s + d - st));
      tl.addUpdate(st, dur, p => { pt.el.style.strokeDashoffset = String(pt.len * (1 - p)); pt.el.style.opacity = p > 0 ? '1' : '0'; }, 'power2.inOut');
      if (pt.fill && pt.fill !== 'none') {
        tl.addUpdate(s + d * 0.92, 0.4, p => { pt.el.setAttribute('fill', pt.fill); pt.el.style.fillOpacity = String(p); }, 'power1.in');
      }
    });
  };
  const mediaImg = (src, cls) => {
    const img = document.createElement('img');
    img.src = src; img.className = cls || 'pf-img';
    img.draggable = false;
    return img;
  };

  /* ---------- clean stroke icons (geometric, currentColor) ---------- */
  const ICONS = {
    spark: 'M12 3l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4z',
    bolt: 'M13 2L4 14h6l-1 8 9-12h-6z',
    cube: 'M12 2l8 4.5v9L12 20l-8-4.5v-9zM12 11l8-4.5M12 11v9M12 11L4 6.5',
    chart: 'M4 20V10M10 20V4M16 20v-8M21 20H3',
    check: 'M4 12.5l5 5L20 6.5',
    arrow: 'M4 12h16m-6-6l6 6-6 6',
    play: 'M7 4.5l13 7.5-13 7.5z',
    image: 'M4 5h16v14H4zM4 15l5-4 4 3 3-2 4 3M9 9.5h.01',
    plus: 'M12 5v14M5 12h14',
    star: 'M12 3l2.7 5.8 6.3.8-4.6 4.3 1.2 6.1L12 17l-5.6 3 1.2-6.1L3 9.6l6.3-.8z',
    globe: 'M12 3a9 9 0 100 18 9 9 0 000-18zM3 12h18M12 3c3 3.5 3 14 0 18-3-4-3-14.5 0-18',
    cpu: 'M8 8h8v8H8zM4 10h4M4 14h4M16 10h4M16 14h4M10 4v4M14 4v4M10 16v4M14 16v4',
    layers: 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5',
    send: 'M3 11l18-7-7 18-2.5-7.5z',
    clock: 'M12 3a9 9 0 100 18 9 9 0 000-18zM12 7v5l3.5 2',
    chat: 'M4 5h16v11H8l-4 4z',
    film: 'M4 4h16v16H4zM4 9h16M4 15h16M9 4v16M15 4v16',
    wand: 'M5 19L17 7m-9-3v3m0 10v3M4 10h3m10 0h3M7 5l2 2m4 8l2 2M7 19l2-2m4-12l2-2',
    node: 'M6 6h4v4H6zM14 14h4v4h-4zM10 8h5v6M8 10v5h6',
    eye: 'M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6zm10 3a3 3 0 100-6 3 3 0 000 6z',
  };
  const icon = (name, parent, cls) => {
    const wrap = h('span', 'pf-icon' + (cls ? ' ' + cls : ''), parent);
    const s = sv('svg', { viewBox: '0 0 24 24' }, wrap);
    sv('path', { d: ICONS[name] || ICONS.spark }, s);
    return wrap;
  };

  /* ---------- brand mark: initial tile | icon | media ---------- */
  function markTile(parent, spec, size = 64) {
    const box = h('div', '', parent);
    box.style.cssText = `position:relative;width:${size}px;height:${size}px;border-radius:${Math.round(size * 0.26)}px;display:flex;align-items:center;justify-content:center;background:var(--pf-card);border:1px solid var(--pf-line);box-shadow:0 12px 32px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.06);overflow:hidden`;
    const m = spec.mark;
    if (m && typeof m === 'string' && m.startsWith('icon:')) {
      const w = icon(m.slice(5), box); w.style.cssText = `width:${size * 0.5}px;height:${size * 0.5}px;color:var(--pf-accent)`;
    } else if (m && svgAssetIndex[m]) {
      const parts = logoSvgIn(box, svgAssetIndex[m]);
      box._svgParts = parts;
      box.style.borderRadius = '0';
      box.style.background = 'transparent';
      box.style.border = 'none';
      box.style.boxShadow = 'none';
    } else if (m && mediaOf(m)) {
      box.appendChild(mediaImg(mediaOf(m)));
    } else {
      const word = spec.brandA || spec.brand || spec.title || spec.appTitle || 'N';
      const ch = h('span', 'pf-display', box, String(word).trim()[0].toUpperCase());
      ch.style.cssText = `font-size:${size * 0.52}px;letter-spacing:0`;
      const ring = sv('svg', { viewBox: '0 0 100 100' }, box);
      ring.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none';
      sv('circle', { cx: 50, cy: 50, r: 44, fill: 'none', stroke: cssVar('--pf-accent'), 'stroke-width': 2.4, 'stroke-dasharray': '7 5', opacity: .9 }, ring);
    }
    return box;
  }

  /* ---------- cursor: clean arrow that glides and clicks ---------- */
  function makeCursor(parent) {
    const c = h('div', 'pf-cursor', parent);
    const s = sv('svg', { viewBox: '0 0 24 24' }, c);
    sv('path', { d: 'M4 3l7 18 2.4-7.2L21 11z', fill: cssVar('--pf-fg'), stroke: 'rgba(0,0,0,.5)', 'stroke-width': 1 }, s);
    c.style.opacity = '0';
    const ring = h('div', '', c);
    ring.style.cssText = 'position:absolute;left:-6px;top:-4px;width:26px;height:26px;border-radius:50%;border:2px solid var(--pf-accent);opacity:0;transform:scale(.4)';
    return { el: c, ring };
  }
  function cursorTo(tl, cursor, s, d, x, y) {
    tl.fromTo(cursor.el, {}, {}, 0); // keep order sane
    const el = cursor.el;
    const cur = { x: null, y: null };
    tl.addUpdate(s, d, p => {
      if (cur.x === null) { cur.x = el._cx ?? x; cur.y = el._cy ?? y; }
      el.style.left = (cur.x + (x - cur.x) * p) + 'px';
      el.style.top = (cur.y + (y - cur.y) * p) + 'px';
      el._cx = x; el._cy = y;
    }, 'power2.inOut');
  }
  function cursorClick(tl, cursor, s) {
    tl.fromTo(cursor.ring, { opacity: .9, scale: .4 }, { opacity: 0, scale: 1.6, duration: 0.5, ease: 'power2.out' }, s);
    tl.fromTo(cursor.el, { scale: 1 }, { scale: .82, duration: 0.12, yoyo: true, repeat: 1, ease: 'power2.inOut' }, s);
  }

  /* ---------- shared furniture ---------- */
  function furniture(scene, spec, idx, total) {
    if (spec.kicker) {
      const k = h('div', 'pf-kicker', scene);
      h('span', '', k).style.cssText = 'display:inline-block;width:7px;height:7px;border-radius:2px;background:var(--pf-accent);margin-right:9px;vertical-align:1px';
      k.appendChild(document.createTextNode(spec.kicker));
    }
    if (spec.kickerR) h('div', 'pf-kicker tr', scene, spec.kickerR);
    if (spec.foot) h('div', 'pf-foot', scene, spec.foot);
    if (spec.note) { const n = h('div', 'pf-note', scene, spec.note); }
    if (spec.index !== false) {
      const ix = h('div', 'pf-index', scene);
      h('span', '', ix, String(idx + 1).padStart(2, '0')).style.color = 'var(--pf-fg)';
      ix.appendChild(document.createTextNode(` / ${String(total).padStart(2, '0')}`));
    }
  }

  /* ---------- small shared parts ---------- */
  const center = (el) => { el.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;text-align:center;position:relative'; return el; };
  const stack = (el, gap = 14, pad = '0') => { el.style.cssText = `flex:1;display:flex;flex-direction:column;justify-content:center;gap:${gap}px;padding:${pad};position:relative`; return el; };
  const sub = (el, text) => { const s = h('div', '', el, text); s.style.cssText = 'font-size:15px;color:var(--pf-muted);letter-spacing:.01em;max-width:80%'; return s; };

  const scenes = {};

  /* --- chapter: index marker + big title + hairline + sub --- */
  scenes['chapter'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 16, '0 4%');
    const row = h('div', '', el);
    row.style.cssText = 'display:flex;align-items:baseline;gap:20px';
    if (spec.marker) {
      const mk = h('div', 'pf-mono', row, String(spec.marker));
      mk.style.cssText = `font-size:${fsize('15px')};letter-spacing:.3em;color:var(--pf-accent);font-weight:600`;
    }
    const decode = spec.reveal === 'decode';
    const head = h('h2', 'pf-display', el, decode ? '' : spec.text || ''); head.dataset.cap = 'title';
    head.style.cssText = `font-size:${fsize(spec.fontSize || '58px')};max-width:94%`;
    const rule = h('div', 'pf-rule', el);
    rule.style.cssText = 'width:120px;transform-origin:0 50%';
    const tl = NexMotion.createTimeline();
    if (spec.marker) fadeIn(tl, row, 0.15, 0.4);
    if (decode) decodeIn(tl, head, spec.text || '', 0.28, 1.4);
    else tl.fromTo(head, { opacity: 0, y: 26, clipPath: 'inset(0 0 60% 0)' }, { opacity: 1, y: 0, clipPath: 'inset(0 0 -10% 0)', duration: 0.7, ease: 'power3.out' }, 0.28);
    tl.fromTo(rule, { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: 'power2.out' }, 0.75);
    if (spec.sub) fadeIn(tl, sub(el, spec.sub), 0.95, 0.45);
    return { el, tl };
  };

  /* --- type-card / hero-build: display lines, masked rise --- */
  scenes['type-card'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const decode = spec.reveal === 'decode';
    const head = h('h2', 'pf-display', el, spec.text || ''); head.dataset.cap = 'title';
    head.style.cssText = `font-size:${fsize(spec.fontSize || '64px')};max-width:92%`;
    const tl = NexMotion.createTimeline();
    if (decode) decodeIn(tl, head, spec.text || '', 0.2, 1.5);
    else splitWords(head, spec.text || '').forEach((w, i) =>
      tl.fromTo(w, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0.15 + i * 0.09));
    if (spec.sub) fadeIn(tl, sub(el, spec.sub), 0.9, 0.4);
    return { el, tl };
  };

  scenes['hero-build'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 6, '0 5%');
    const lines = spec.lines || [spec.text || ''];
    const tl = NexMotion.createTimeline();
    lines.forEach((line, i) => {
      const l = h('h2', 'pf-display', el, line); l.dataset.cap = 'line-' + i;
      l.style.cssText = `font-size:${fsize('66px')};line-height:1.02`;
      tl.fromTo(l, { opacity: 0, y: 34, clipPath: 'inset(-10% 0 80% 0)' }, { opacity: 1, y: 0, clipPath: 'inset(-10% 0 -10% 0)', duration: 0.6, ease: 'power3.out' }, 0.18 + i * 0.32);
    });
    const bar = h('div', 'pf-accbar', el);
    bar.style.cssText = 'width:88px;margin-top:16px;transform-origin:0 50%';
    tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 0.55, ease: 'power2.out' }, 0.3 + lines.length * 0.32);
    return { el, tl };
  };

  /* --- kinetic-headline: words slam with landing kicks --- */
  scenes['kinetic-headline'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const text = spec.text || spec.headline || '';
    const head = h('h2', 'pf-display', el, text); head.dataset.cap = 'title';
    head.style.cssText = `font-size:${fsize(spec.fontSize || '62px')};max-width:94%`;
    const words = splitWords(head, text);
    const accent = spec.accent;
    const accentIdx = typeof accent === 'number' ? accent :
      typeof accent === 'string' ? words.findIndex(w => w.textContent.toLowerCase().trim() === accent.toLowerCase()) : -1;
    const tl = NexMotion.createTimeline();
    words.forEach((wEl, i) => {
      const s = 0.1 + i * 0.24;
      wEl.style.display = 'inline-block'; wEl.style.transformOrigin = '50% 80%'; wEl.dataset.cap = 'word-' + i;
      wEl.style.marginRight = '.09em';
      tl.fromTo(wEl, { opacity: 0, scale: 1.55, y: 26, rotation: i % 2 ? -2 : 2 },
        { opacity: 1, scale: 1, y: 0, rotation: 0, duration: 0.38, ease: 'back.out(2.1)' }, s);
      tl.addUpdate(s + 0.38, 0.16, p => { head.style.transform = `translateY(${-3 * Math.sin(p * Math.PI)}px)`; }, 'none');
      if (i === accentIdx) {
        wEl.style.color = cssVar('--pf-accent');
      }
    });
    const und = h('div', 'pf-accbar', el);
    und.style.cssText = 'width:160px;transform-origin:0 50%;margin-top:6px';
    tl.fromTo(und, { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: 'power3.out' }, 0.1 + words.length * 0.24);
    if (spec.sub) fadeIn(tl, sub(el, spec.sub), 0.35 + words.length * 0.24, 0.4);
    return { el, tl };
  };

  /* --- kinetic-type: per-char velocity stagger + blur-resolve + squash ---
     motionforge's KineticTypography recipe: early chars travel further and
     arrive blurrier (velocity weighting), landing with a brief squash.
     Word wrappers keep line-breaks intact; transform via gsap, squash via
     the CSS `scale` property so the two never stomp. */
  const splitChars = (el, text) => {
    const words = String(text).split(/\s+/).filter(Boolean);
    el.textContent = '';
    const chars = [];
    words.forEach((w, wi) => {
      const wrap = h('span', '', el);
      wrap.style.cssText = 'display:inline-block;white-space:nowrap';
      for (const ch of w) {
        const c = h('span', '', wrap, ch);
        c.style.display = 'inline-block';
        chars.push(c);
      }
      el.appendChild(document.createTextNode(' '));
    });
    return chars;
  };
  scenes['kinetic-type'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const head = h('h2', 'pf-display', el); head.dataset.cap = 'title';
    head.style.cssText = `font-size:${fsize(spec.fontSize || '66px')};max-width:94%;line-height:1.05`;
    const chars = splitChars(head, spec.text || spec.headline || '');
    const n = Math.max(1, chars.length);
    const stagger = spec.stagger ?? 0.028;
    const blurMax = spec.blur ?? 11;
    const accent = spec.accent; // trailing word(s) colored: number = last-N chars, string = word match
    const tl = NexMotion.createTimeline();
    const decode = spec.reveal === 'decode';
    if (decode) chars.forEach(c => { c.style.opacity = '0'; });
    chars.forEach((c, i) => {
      const s = 0.06 + i * stagger;
      if (decode) {
        const orig = c.textContent;
        tl.addUpdate(s, 0.42, (p, raw, t) => {
          const step = Math.floor(t * 22);
          c.textContent = p >= 0.92 ? orig : GLYPHS[(((i * 2654435761) ^ (step * 40503)) >>> 0) % GLYPHS.length];
          c.style.opacity = p > 0 ? '1' : '0';
        }, 'none');
        tl.addUpdate(s + 0.45, 0.01, (p) => { if (p > 0) c.textContent = orig; }, 'none');
        return;
      }
      const depth = 1 - i / n;                     // first chars are "fastest"
      const blur = blurMax * (0.45 + 0.55 * depth);
      const dy = (26 + 22 * depth).toFixed(1);
      c.style.willChange = 'transform,filter';
      tl.fromTo(c, { opacity: 0, y: Number(dy), scaleY: 1.18 },
        { opacity: 1, y: 0, scaleY: 1, duration: 0.32, ease: 'power3.out' }, s);
      tl.addUpdate(s, 0.34, p => { c.style.filter = `blur(${(blur * (1 - p)).toFixed(2)}px)`; }, 'power2.out');
      tl.addUpdate(s + 0.32, 0.16, p => {
        const k = Math.sin(p * Math.PI);
        c.style.scale = `${(1 + 0.045 * k).toFixed(3)} ${(1 - 0.07 * k).toFixed(3)}`;
      }, 'none');
    });
    if (accent != null) {
      const word = typeof accent === 'number' ? null : String(accent).toLowerCase();
      const all = head.querySelectorAll('span>span');
      let hit = [];
      if (typeof accent === 'number') hit = [...all].slice(-Math.abs(accent));
      else head.querySelectorAll('span').forEach(wr => { if (wr.textContent.toLowerCase() === word) hit.push(...wr.querySelectorAll('span')); });
      hit.forEach(c => tl.addUpdate(0.06 + n * stagger + 0.05, 0.25, p => { c.style.color = p > 0.5 ? cssVar('--pf-accent') : ''; }, 'none'));
    }
    const und = h('div', 'pf-accbar', el);
    und.style.cssText = 'width:160px;transform-origin:0 50%;margin-top:8px';
    tl.fromTo(und, { scaleX: 0 }, { scaleX: 1, duration: 0.45, ease: 'power3.out' }, 0.06 + n * stagger + 0.05);
    if (spec.sub) fadeIn(tl, sub(el, spec.sub), 0.2 + n * stagger, 0.4);
    return { el, tl };
  };

  /* --- word-list: ruled rows sliding in --- */
  scenes['word-list'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 0, '0 2%');
    if (spec.title) {
      const t = h('div', 'pf-mono', el, spec.title);
      t.style.cssText = `font-size:${fsize('13px')};letter-spacing:.2em;color:var(--pf-muted);text-transform:uppercase;margin-bottom:14px`;
    }
    const items = (spec.items || []).slice(0, 6);
    const tl = NexMotion.createTimeline();
    if (spec.title) fadeIn(tl, el.firstChild, 0.1, 0.35);
    items.forEach((it, i) => {
      const row = h('div', '', el); row.dataset.cap = 'item-' + i;
      row.style.cssText = 'display:flex;align-items:baseline;gap:18px;padding:13px 0;border-bottom:1px solid var(--pf-line)';
      const no = h('span', 'pf-mono', row, String(i + 1).padStart(2, '0'));
      no.style.cssText = 'font-size:12px;color:var(--pf-accent);letter-spacing:.1em';
      const tx = h('span', 'pf-display', row, typeof it === 'string' ? it : (it.title || it.label || ''));
      tx.style.cssText = `font-size:${fsize('30px')};font-weight:600;letter-spacing:-.02em`;
      const subT = typeof it === 'object' && it.sub ? h('span', '', row, it.sub) : null;
      if (subT) subT.style.cssText = 'margin-left:auto;font-size:13px;color:var(--pf-muted)';
      tl.fromTo(row, { opacity: 0, x: -26 }, { opacity: 1, x: 0, duration: 0.45, ease: 'power3.out' }, 0.25 + i * 0.22);
    });
    return { el, tl };
  };

  /* --- feature-grid: card grid, staggered rise --- */
  scenes['feature-grid'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 16, '0');
    if (spec.title) {
      const t = h('h2', 'pf-display', el, spec.title);
      t.style.cssText = `font-size:${fsize('34px')};font-weight:600`;
    }
    const items = (spec.items || []).slice(0, 6);
    const cols = items.length > 3 ? 3 : items.length;
    const grid = h('div', '', el);
    grid.style.cssText = `display:grid;grid-template-columns:repeat(${cols},1fr);gap:12px;flex:1;align-content:center`;
    const tl = NexMotion.createTimeline();
    if (spec.title) fadeIn(tl, el.firstChild, 0.1, 0.4);
    items.forEach((it, i) => {
      const o = typeof it === 'string' ? { title: it } : it;
      const card = h('div', 'pf-card', grid); card.dataset.cap = 'item-' + i;
      card.style.cssText = 'padding:16px 15px;display:flex;flex-direction:column;gap:9px;min-height:96px;justify-content:center;box-shadow:0 10px 30px rgba(0,0,0,.25),inset 0 1px 0 rgba(255,255,255,.05)';
      const top = h('div', '', card);
      top.style.cssText = 'display:flex;align-items:center;gap:9px';
      const chip = h('span', '', top);
      chip.style.cssText = 'width:26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center;background:color-mix(in srgb,var(--pf-accent) 16%,transparent);color:var(--pf-accent)';
      const ic = icon(o.icon || ['spark', 'cube', 'chart', 'bolt', 'layers', 'globe'][i % 6], chip); ic.style.width = '15px'; ic.style.height = '15px';
      const ttl = h('span', '', top, o.title || o.label || '');
      ttl.style.cssText = `font-family:var(--pf-display);font-weight:600;font-size:${fsize('16px')};letter-spacing:-.01em`;
      if (o.sub) { const s = h('div', '', card, o.sub); s.style.cssText = 'font-size:12.5px;color:var(--pf-muted);line-height:1.35'; }
      popIn(tl, card, 0.25 + i * 0.16, 0.5);
    });
    return { el, tl };
  };

  /* --- stat: counting figure + drawn ring --- */
  scenes['stat'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const wrap = h('div', '', el);
    wrap.style.cssText = 'position:relative;display:flex;align-items:center;justify-content:center';
    const size = 330;
    const ring = sv('svg', { viewBox: '0 0 120 120' }, wrap);
    ring.style.cssText = `width:${size}px;height:${size}px;transform:rotate(-90deg)`;
    sv('circle', { cx: 60, cy: 60, r: 52, fill: 'none', stroke: cssVar('--pf-line'), 'stroke-width': 1.6 }, ring);
    const arc = sv('circle', { cx: 60, cy: 60, r: 52, fill: 'none', stroke: cssVar('--pf-accent'), 'stroke-width': 3, 'stroke-linecap': 'round' }, ring);
    const num = h('div', '', wrap);
    num.style.cssText = 'position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px';
    const val = h('span', 'pf-display', num, '0'); val.dataset.cap = 'stat';
    val.style.cssText = `font-size:${fsize('96px')};font-weight:700;letter-spacing:-.04em`;
    if (spec.label) { const lb = h('span', 'pf-mono', num, spec.label); lb.style.cssText = 'font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--pf-muted);max-width:70%;text-align:center'; }
    const tl = NexMotion.createTimeline();
    const C = 2 * Math.PI * 52;
    arc.style.strokeDasharray = String(C); arc.style.strokeDashoffset = String(C);
    tl.addUpdate(0.2, 1.5, p => { arc.style.strokeDashoffset = String(C * (1 - p * 0.999)); }, 'power3.out');
    const to = Number(spec.value || 0), fmt = spec.format;
    const wheel = spec.digits === 'wheel' || (spec.digits !== 'flat' && !fmt);
    if (wheel) {
      const nd = String(Math.max(1, Math.round(to))).length;
      const set = wheelify(val, '', nd, spec.suffix || '', cssVar('--pf-accent'));
      tl.addUpdate(0.35, 1.5, p => set(Math.round(to * p)), 'power3.out');
    } else {
      const pre = (fmt && fmt.match(/^\D+/)) ? fmt.match(/^\D+/)[0] : '';
      counter(tl, val, 0.35, 1.5, p => pre + Math.round(to * p).toLocaleString() + (spec.suffix || ''));
    }
    popIn(tl, num, 0.15, 0.5);
    if (spec.sub) fadeIn(tl, sub(el, spec.sub), 1.5, 0.4);
    return { el, tl };
  };

  /* --- quote: giant mark + text + byline --- */
  scenes['quote'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 18, '0 7%');
    const mark = h('div', 'pf-display', el, '“');
    mark.style.cssText = `font-size:${fsize('110px')};line-height:.6;color:var(--pf-accent);height:.5em`;
    const q = h('div', 'pf-display', el, spec.text || ''); q.dataset.cap = 'title';
    q.style.cssText = `font-size:${fsize('40px')};font-weight:600;line-height:1.18;letter-spacing:-.015em;max-width:92%`;
    const tl = NexMotion.createTimeline();
    tl.fromTo(mark, { opacity: 0, scale: 1.6 }, { opacity: 1, scale: 1, duration: 0.5, ease: 'back.out(1.8)' }, 0.15);
    splitWords(q, spec.text || '').forEach((w, i) =>
      tl.fromTo(w, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power3.out' }, 0.4 + i * 0.05));
    if (spec.by) {
      const b = h('div', 'pf-mono', el, '— ' + spec.by);
      b.style.cssText = 'font-size:13px;letter-spacing:.12em;color:var(--pf-muted);text-transform:uppercase';
      fadeIn(tl, b, 0.5 + (spec.text || '').split(/\s+/).length * 0.05, 0.4);
    }
    return { el, tl };
  };

  /* --- media-frame: real asset in a framed card --- */
  scenes['media-frame'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 14, '0 4%');
    const frame = h('div', '', el);
    frame.dataset.cap = 'frame';
    frame.style.cssText = 'position:relative;flex:1;border-radius:20px;overflow:hidden;border:1px solid var(--pf-line);box-shadow:0 24px 60px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.06);background:var(--pf-card)';
    const src = mediaOf(spec.media);
    let inner;
    if (src) {
      inner = mediaImg(src); frame.appendChild(inner);
    } else {
      inner = h('div', '', frame);
      inner.style.cssText = 'width:100%;height:100%;background:linear-gradient(135deg,var(--pf-card-2),var(--pf-card));display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:32px;text-align:center';
      const ic = icon(spec.icon || 'image', inner); ic.style.cssText = 'width:52px;height:52px;color:var(--pf-accent)';
      if (spec.title) {
        const tt = h('div', '', inner, spec.title);
        tt.style.cssText = `font:600 ${fsize('30px')}/1.15 var(--pf-display);letter-spacing:-.01em;color:var(--pf-fg)`;
      }
      if (spec.sub) {
        const ss = h('div', 'pf-mono', inner, spec.sub);
        ss.style.cssText = `font-size:${fsize('12px')};letter-spacing:.16em;text-transform:uppercase;color:var(--pf-muted)`;
      }
    }
    const cap = h('div', '', el);
    cap.style.cssText = 'display:flex;align-items:center;gap:10px;font:600 11px/1 var(--pf-mono);letter-spacing:.14em;color:var(--pf-muted);text-transform:uppercase';
    h('span', '', cap).style.cssText = 'width:6px;height:6px;border-radius:50%;background:var(--pf-accent)';
    cap.appendChild(document.createTextNode(spec.caption || ''));
    const tl = NexMotion.createTimeline();
    tl.fromTo(frame, { opacity: 0, scale: 1.04, y: 18 }, { opacity: 1, scale: 1, y: 0, duration: 0.7, ease: 'power3.out' }, 0.15);
    if (src) tl.fromTo(inner, { scale: 1.12 }, { scale: 1, duration: 2.4, ease: 'power2.out' }, 0.15);
    fadeIn(tl, cap, 0.8, 0.4);
    return { el, tl };
  };

  /* --- split: two panels + vs --- */
  scenes['split'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 0, '0');
    const row = h('div', '', el);
    row.style.cssText = 'flex:1;display:flex;gap:12px;position:relative;align-items:stretch';
    const mkPanel = (data, accent) => {
      const p = h('div', 'pf-card', row);
      p.style.cssText = 'flex:1;padding:22px;display:flex;flex-direction:column;gap:10px;justify-content:center';
      const t = h('div', 'pf-mono', p, (data && data.title) || '');
      t.style.cssText = `font-size:${fsize('13px')};letter-spacing:.2em;color:${accent ? 'var(--pf-accent)' : 'var(--pf-muted)'};text-transform:uppercase`;
      ((data && data.items) || []).slice(0, 4).forEach(it => {
        const li = h('div', '', p, it);
        li.style.cssText = 'font-size:15px;color:var(--pf-fg);padding-left:14px;position:relative';
        li.insertAdjacentHTML('afterbegin', '<span style="position:absolute;left:0;top:.62em;width:5px;height:1.5px;background:var(--pf-line)"></span>');
      });
      return p;
    };
    const pa = mkPanel(spec.a, false), pb = mkPanel(spec.b, true);
    pa.dataset.cap = 'a'; pb.dataset.cap = 'b';
    const vs = h('div', '', row, 'vs');
    vs.style.cssText = 'position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:44px;height:44px;border-radius:50%;background:var(--pf-bg);border:1px solid var(--pf-line);display:flex;align-items:center;justify-content:center;font:700 13px var(--pf-display);color:var(--pf-accent);z-index:2';
    const tl = NexMotion.createTimeline();
    tl.fromTo(pa, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.55, ease: 'power3.out' }, 0.15);
    tl.fromTo(pb, { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: 0.55, ease: 'power3.out' }, 0.35);
    popIn(tl, vs, 0.6, 0.4);
    return { el, tl };
  };

  /* --- marquee-word: giant outline word drifting --- */
  scenes['marquee-word'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;flex-direction:column;justify-content:center;overflow:hidden;position:relative';
    const word = String(spec.word || 'FILM').toUpperCase();
    const band = h('div', '', el);
    band.style.cssText = 'white-space:nowrap;display:flex;will-change:transform'; band.dataset.cap = 'title';
    const spans = [];
    for (let i = 0; i < 4; i++) {
      const w = h('span', 'pf-outline', band, word + '  ·  ');
      w.style.cssText = `font-size:${fsize('150px')};flex:none`;
      spans.push(w);
      if (spec.fillMint && i === 1) { w.style.webkitTextStroke = '0'; w.style.color = cssVar('--pf-accent'); w.style.opacity = '.92'; }
    }
    const tl = NexMotion.createTimeline();
    tl.fromTo(band, { x: 40 }, { x: -Math.round(band.scrollWidth / 3), duration: Math.max(2, (spec.duration || 4) - 0.3), ease: 'none' }, 0.1);
    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.4 }, 0);
    return { el, tl };
  };

  /* --- orbit: brand hub + circling items --- */
  scenes['orbit'] = (spec) => {
    const el = h('div', '', null);
    /* width:100% is load-bearing: layout-poster's align-items:center would
       otherwise shrink-wrap this lane around its (all-absolute) children */
    el.style.cssText = 'flex:1;width:100%;position:relative;display:flex;align-items:center;justify-content:center';
    const cx = 313, cy = 268; // centered within ~626x536 safe lane (720 stage)
    const field = h('div', '', el);
    field.style.cssText = 'position:absolute;inset:0';
    /* hairline orbit rings */
    const rings = sv('svg', { viewBox: '0 0 620 536' }, field);
    rings.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    const ringE = sv('ellipse', { cx: cx, cy: cy, rx: 218, ry: 148, fill: 'none', stroke: cssVar('--pf-line'), 'stroke-width': 1.2 }, rings);
    const ringDash = sv('ellipse', { cx: cx, cy: cy, rx: 218, ry: 148, fill: 'none', stroke: cssVar('--pf-accent'), 'stroke-width': 1.4, 'stroke-dasharray': '2 10', opacity: .8 }, rings);
    const centerTile = markTile(field, spec, 96); centerTile.dataset.cap = 'hub';
    const hubParts = centerTile._svgParts;
    centerTile.style.position = 'absolute';
    centerTile.style.left = (cx - 48) + 'px'; centerTile.style.top = (cy - 48) + 'px';
    const items = (spec.items || []).slice(0, 5);
    const tl = NexMotion.createTimeline();
    if (spec.title) {
      const t = h('div', 'pf-mono', field, spec.title);
      t.style.cssText = 'position:absolute;left:0;right:0;top:4%;text-align:center;font-size:13px;letter-spacing:.22em;text-transform:uppercase;color:var(--pf-muted)';
      fadeIn(tl, t, 0.15, 0.4);
    }
    popIn(tl, centerTile, 0.15, 0.6);
    if (hubParts) drawPathSeq(tl, hubParts, 0.25, 1.1);
    tl.addUpdate(0.2, 1.2, p => { ringE.style.opacity = String(p); }, 'power2.out');
    /* slow dash rotation — motion without moving labels */
    tl.addUpdate(0, Math.max(2, (spec.duration || 5) - 0.5), (p, raw, t) => {
      ringDash.style.strokeDashoffset = String(-t * 14);
    }, 'none');
    items.forEach((it, i) => {
      const o = typeof it === 'string' ? { title: it } : it;
      const ang = -Math.PI / 2 + (i / items.length) * Math.PI * 2;
      const x = cx + 218 * Math.cos(ang), y = cy + 148 * Math.sin(ang);
      const chip = h('div', 'pf-chip acc', field); chip.dataset.cap = 'item-' + i;
      chip.style.cssText += `;position:absolute;left:0;top:0;padding:10px 16px;background:var(--pf-card);font-family:var(--pf-display);font-size:15px;font-weight:600;letter-spacing:0;color:var(--pf-fg);white-space:nowrap;box-shadow:0 10px 28px rgba(0,0,0,.4)`;
      const lbl = h('span', '', chip, o.title || '');
      if (o.sub) { const s = h('span', '', chip, o.sub); s.style.cssText = 'color:var(--pf-muted);font-weight:400;font-size:12px'; }
      /* measure-free placement: translate the chip by its anchor, then offset by
         half its box at runtime — transform math, no layout read at seek time */
      /* entrance driven through CSS translate/scale properties — they compose
         with transform so the -50% centering survives (a gsap transform tween
         would stomp it and the chip would anchor top-left, clipping the lane) */
      chip.style.left = x + 'px'; chip.style.top = y + 'px';
      chip.style.transform = 'translate(-50%,-50%)';
      chip.style.opacity = '0'; chip.style.scale = '.6'; chip.style.translate = '0 14px';
      const s = 0.45 + i * 0.22;
      tl.addUpdate(s, 0.5, (p) => {
        chip.style.opacity = String(Math.min(1, p));
        chip.style.scale = String(0.6 + 0.4 * p);
        chip.style.translate = `0 ${14 * (1 - p)}px`;
      }, 'back.out(1.9)');
      /* subtle float after landing */
      tl.addUpdate(s + 0.5, Math.max(1.5, (spec.duration || 5) - s - 1), (p, raw, t) => {
        chip.style.translate = `0 ${Math.sin(t * 1.3 + i * 1.7) * 4}px`;
      }, 'none');
    });
    if (spec.sub) {
      const s = h('div', 'pf-mono', field, spec.sub);
      s.style.cssText = 'position:absolute;left:0;right:0;bottom:2%;text-align:center;font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--pf-muted)';
      fadeIn(tl, s, 0.6 + items.length * 0.22, 0.4);
    }
    return { el, tl };
  };

  /* --- process-rail: nodes on a sweeping line --- */
  scenes['process-rail'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 0, '0 2%');
    if (spec.title) {
      const t = h('h2', 'pf-display', el, spec.title);
      t.style.cssText = `font-size:${fsize('34px')};font-weight:600;margin-bottom:8px`;
    }
    const steps = (spec.steps || spec.items || []).slice(0, 5);
    const railWrap = h('div', '', el);
    railWrap.style.cssText = 'flex:1;display:flex;align-items:center;position:relative';
    const track = h('div', '', railWrap);
    track.style.cssText = 'position:absolute;left:0;right:0;top:50%;height:2px;background:var(--pf-line);border-radius:2px;transform:translateY(-50%)';
    const fill = h('div', '', track);
    fill.style.cssText = 'height:100%;width:0;background:var(--pf-accent);border-radius:2px;box-shadow:0 0 14px color-mix(in srgb,var(--pf-accent) 65%,transparent)';
    const row = h('div', '', railWrap);
    row.style.cssText = 'position:relative;width:100%;display:flex;justify-content:space-between';
    const tl = NexMotion.createTimeline();
    if (spec.title) fadeIn(tl, el.firstChild, 0.1, 0.4);
    const nodes = [];
    steps.forEach((st, i) => {
      const o = typeof st === 'string' ? { label: st } : st;
      const col = h('div', '', row); col.dataset.cap = 'item-' + i;
      col.style.cssText = `display:flex;flex-direction:column;align-items:center;gap:12px;width:${100 / steps.length}%`;
      const node = h('div', '', col);
      node.style.cssText = 'width:52px;height:52px;border-radius:50%;background:var(--pf-card);border:1.5px solid var(--pf-line);display:flex;align-items:center;justify-content:center;position:relative;z-index:1';
      let inner;
      if (o.icon && ICONS[o.icon]) { inner = icon(o.icon, node); inner.style.cssText = 'width:22px;height:22px;color:var(--pf-fg)'; }
      else { inner = h('span', 'pf-mono', node, String(i + 1).padStart(2, '0')); inner.style.cssText = 'font-size:13px;font-weight:600;color:var(--pf-fg)'; }
      const lbl = h('div', '', col, o.label || o.title || '');
      lbl.style.cssText = `font-family:var(--pf-display);font-weight:600;font-size:${fsize('15px')};text-align:center;letter-spacing:-.01em`;
      if (o.sub) { const s = h('div', '', col, o.sub); s.style.cssText = 'font-size:11.5px;color:var(--pf-muted);text-align:center;max-width:90%'; }
      nodes.push(node);
      popIn(tl, col, 0.3 + i * 0.28, 0.5);
    });
    /* progress fill sweeps; node rings light as it passes */
    tl.addUpdate(0.35, Math.max(0.6, (spec.duration || 4) * 0.55), p => {
      fill.style.width = (p * 100) + '%';
      nodes.forEach((n, i) => {
        const at = (i + 0.5) / steps.length;
        const on = p >= at;
        n.style.borderColor = on ? cssVar('--pf-accent') : cssVar('--pf-line');
        n.style.boxShadow = on ? `0 0 0 4px color-mix(in srgb,${cssVar('--pf-accent')} 18%,transparent)` : 'none';
      });
    }, 'power1.inOut');
    if (spec.payoff) {
      const p = h('div', 'pf-mono', el, spec.payoff);
      p.style.cssText = 'margin-top:14px;font-size:12px;letter-spacing:.14em;color:var(--pf-muted);text-transform:uppercase;text-align:center';
      fadeIn(tl, p, 0.5 + steps.length * 0.28, 0.4);
    }
    return { el, tl };
  };

  /* --- payoff-lockup: statement + accent sweep --- */
  scenes['payoff-lockup'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const head = h('h2', 'pf-display', el, spec.text || ''); head.dataset.cap = 'title';
    head.style.cssText = `font-size:${fsize('56px')};max-width:92%`;
    const bar = h('div', 'pf-accbar', el);
    bar.style.cssText = 'width:200px;transform-origin:50% 50%';
    const tl = NexMotion.createTimeline();
    tl.fromTo(head, { opacity: 0, scale: .94, y: 20 }, { opacity: 1, scale: 1, y: 0, duration: 0.7, ease: 'power3.out' }, 0.2);
    tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: 'power2.out' }, 0.7);
    if (spec.sub) fadeIn(tl, sub(el, spec.sub), 1.0, 0.45);
    return { el, tl };
  };

  /* --- end-card: mark + wordmark + tagline + CTA pill --- */
  scenes['end-card'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const bloom = h('div', '', el);
    bloom.style.cssText = 'position:absolute;left:50%;top:44%;width:70%;height:56%;transform:translate(-50%,-50%);border-radius:50%;background:radial-gradient(closest-side,color-mix(in srgb,var(--pf-accent) 26%,transparent),transparent 72%);opacity:0;filter:blur(10px)';
    const tile = markTile(el, spec, 84);
    const name = [spec.brandA, spec.brandB].filter(Boolean).join(' ');
    const wm = h('div', 'pf-display', el, name); wm.dataset.cap = 'brand';
    wm.style.cssText = `font-size:${fsize('46px')};letter-spacing:-.02em`;
    const tag = h('div', '', el, spec.sub || '');
    tag.style.cssText = 'font-size:14px;color:var(--pf-muted)';
    let pill = null;
    if (spec.pill) {
      pill = h('div', '', el, spec.pill); pill.dataset.cap = 'cta';
      pill.style.cssText = 'margin-top:10px;padding:13px 26px;border-radius:99px;background:var(--pf-accent);color:var(--pf-bg);font:600 14px var(--pf-display);letter-spacing:.01em;box-shadow:0 8px 28px color-mix(in srgb,var(--pf-accent) 40%,transparent)';
    }
    const tl = NexMotion.createTimeline();
    if (tile._svgParts) {
      tl.fromTo(tile, { opacity: 0, scale: .85 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, 0.1);
      drawPathSeq(tl, tile._svgParts, 0.2, 1.3);
    } else {
      tl.fromTo(tile, { opacity: 0, scale: .7, rotation: -6 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.6, ease: 'back.out(1.9)' }, 0.15);
    }
    tl.fromTo(wm, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0.5);
    if (spec.sub) fadeIn(tl, tag, 0.75, 0.4);
    if (pill) popIn(tl, pill, 1.0, 0.5);
    tl.addUpdate(0.7, 1.6, p => { bloom.style.opacity = String(p * 0.9); bloom.style.scale = String(0.7 + p * 0.5); }, 'power2.out');
    return { el, tl };
  };

  /* --- chat-prompt → prompt bar: typed brief + send --- */
  scenes['chat-prompt'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const card = h('div', 'pf-card', el); card.dataset.cap = 'input';
    card.style.cssText = 'width:88%;padding:18px 20px;display:flex;align-items:center;gap:14px;box-shadow:0 20px 50px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.05)';
    const av = h('div', '', card);
    av.style.cssText = 'width:34px;height:34px;border-radius:50%;flex:none;background:color-mix(in srgb,var(--pf-accent) 22%,var(--pf-card));display:flex;align-items:center;justify-content:center';
    const ic = icon('spark', av); ic.style.cssText = 'width:16px;height:16px;color:var(--pf-accent)';
    const textWrap = h('div', '', card);
    textWrap.style.cssText = 'flex:1;display:flex;align-items:center;min-height:22px';
    const typed = h('span', '', textWrap);
    typed.style.cssText = 'font-size:16.5px;color:var(--pf-fg);letter-spacing:0;text-align:left';
    const caret = h('span', '', textWrap);
    caret.style.cssText = 'width:2px;height:20px;background:var(--pf-accent);margin-left:2px';
    const send = h('div', '', card);
    send.style.cssText = 'width:36px;height:36px;border-radius:50%;flex:none;border:1px solid var(--pf-line);display:flex;align-items:center;justify-content:center;color:var(--pf-muted)';
    const si = icon('send', send); si.style.cssText = 'width:15px;height:15px';
    const chips = h('div', '', el);
    chips.style.cssText = 'display:flex;gap:8px;margin-top:4px';
    const tl = NexMotion.createTimeline();
    popIn(tl, card, 0.15, 0.5);
    const text = spec.text || '';
    typewrite(tl, typed, text, 0.55, Math.min(1.6, 0.05 * text.length + 0.4));
    caretBlink(tl, caret, 0.55, Math.min(1.7, 0.05 * text.length + 0.5));
    const sendAt = 0.55 + Math.min(1.6, 0.05 * text.length + 0.4) + 0.15;
    tl.addUpdate(sendAt, 0.35, p => {
      send.style.background = `color-mix(in srgb,var(--pf-accent) ${Math.round(p * 100)}%,transparent)`;
      send.style.color = p > 0.5 ? 'var(--pf-bg)' : 'var(--pf-muted)';
      send.style.borderColor = p > 0.5 ? 'transparent' : 'var(--pf-line)';
    }, 'power2.out');
    tl.to(caret, { opacity: 0, duration: 0.1 }, sendAt + 0.35);
    (spec.tags || []).slice(0, 4).forEach((t, i) => {
      const c = h('span', 'pf-chip', chips, t);
      fadeIn(tl, c, sendAt + 0.3 + i * 0.14, 0.35, 8);
    });
    if (spec.mention || spec.mode) {
      const meta = h('div', 'pf-mono', el, [spec.mention, spec.mode].filter(Boolean).join(' · '));
      meta.style.cssText = 'font-size:11px;letter-spacing:.14em;color:var(--pf-muted);text-transform:uppercase;margin-top:2px';
      fadeIn(tl, meta, sendAt + 0.4, 0.4);
    }
    return { el, tl };
  };

  /* --- agent-window: the product desk — titlebar + sidebar + transcript --- */
  scenes['agent-window'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;align-items:center;justify-content:center;position:relative';
    const win = h('div', 'pf-card', el);
    win.style.cssText = 'width:94%;height:88%;border-radius:18px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 30px 80px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.06)';
    /* titlebar */
    const bar = h('div', '', win);
    bar.style.cssText = 'display:flex;align-items:center;gap:8px;padding:11px 14px;border-bottom:1px solid var(--pf-line);flex:none';
    ['#ff5f57', '#febc2e', '#28c840'].forEach(c => { const d = h('span', '', bar); d.style.cssText = `width:9px;height:9px;border-radius:50%;background:${c}`; });
    const url = h('div', 'pf-mono', bar, (spec.brand || 'app').toLowerCase().replace(/\s+/g, '') + ' — workspace');
    url.style.cssText = 'margin-left:10px;font-size:10.5px;letter-spacing:.1em;color:var(--pf-muted)';
    const status = h('span', 'pf-chip acc', bar, spec.status || 'working…');
    status.style.cssText += ';margin-left:auto;padding:5px 10px;font-size:10px';
    /* body */
    const body = h('div', '', win);
    body.style.cssText = 'flex:1;display:flex;min-height:0';
    const side = h('div', '', body);
    side.style.cssText = 'width:30%;border-right:1px solid var(--pf-line);padding:14px 12px;display:flex;flex-direction:column;gap:4px;flex:none';
    const brandRow = h('div', '', side);
    brandRow.style.cssText = 'display:flex;align-items:center;gap:9px;margin-bottom:10px';
    markTile(brandRow, { brandA: spec.brand, mark: spec.mark }, 24);
    const bn = h('span', '', brandRow, spec.brand || 'APP');
    bn.style.cssText = 'font:700 13px var(--pf-display);letter-spacing:.02em';
    const tl = NexMotion.createTimeline();
    (spec.tasks || []).slice(0, 4).forEach((t, i) => {
      const r = h('div', '', side);
      r.style.cssText = `display:flex;flex-direction:column;gap:2px;padding:7px 9px;border-radius:8px;${t.on ? 'background:color-mix(in srgb,var(--pf-accent) 12%,transparent);border:1px solid color-mix(in srgb,var(--pf-accent) 35%,transparent)' : ''}`;
      const tt = h('span', '', r, t.title || '');
      tt.style.cssText = `font-size:12px;font-weight:600;color:${t.on ? 'var(--pf-accent)' : 'var(--pf-fg)'}`;
      if (t.sub) { const s = h('span', 'pf-mono', r, t.sub); s.style.cssText = 'font-size:9.5px;color:var(--pf-muted);letter-spacing:.08em;text-transform:uppercase'; }
      fadeIn(tl, r, 0.5 + i * 0.18, 0.35, 8);
    });
    const main = h('div', '', body);
    main.style.cssText = 'flex:1;padding:16px 16px 12px;display:flex;flex-direction:column;gap:9px;min-width:0';
    /* messages */
    (spec.messages || []).slice(0, 3).forEach((m, i) => {
      const mine = m.from === 'user';
      const b = h('div', '', main);
      b.style.cssText = `max-width:82%;padding:9px 12px;border-radius:12px;font-size:13px;line-height:1.35;${mine ? 'align-self:flex-end;background:color-mix(in srgb,var(--pf-accent) 18%,transparent);border:1px solid color-mix(in srgb,var(--pf-accent) 30%,transparent);border-bottom-right-radius:4px' : 'align-self:flex-start;background:var(--pf-card-2);border:1px solid var(--pf-line);border-bottom-left-radius:4px'}`;
      b.textContent = m.text || '';
      fadeIn(tl, b, 0.7 + i * 0.5, 0.4, 10);
    });
    /* checklist */
    const list = h('div', '', main);
    list.style.cssText = 'display:flex;flex-direction:column;gap:6px;margin-top:2px';
    const checks = (spec.checks || []).slice(0, 4);
    checks.forEach((c, i) => {
      const r = h('div', '', list);
      r.style.cssText = 'display:flex;align-items:center;gap:9px';
      const box = h('span', '', r);
      box.style.cssText = 'width:17px;height:17px;border-radius:5px;border:1.5px solid var(--pf-line);display:flex;align-items:center;justify-content:center;flex:none';
      const tick = icon('check', box); tick.style.cssText = 'width:11px;height:11px;color:var(--pf-accent);opacity:0';
      const ct = h('span', '', r, c);
      ct.style.cssText = 'font-size:12.5px;color:var(--pf-fg)';
      const at = 1.5 + i * 0.42;
      fadeIn(tl, r, at, 0.3, 6);
      tl.addUpdate(at + 0.25, 0.25, p => {
        tick.style.opacity = String(p);
        box.style.borderColor = p > 0.5 ? 'var(--pf-accent)' : 'var(--pf-line)';
        box.style.background = `color-mix(in srgb,var(--pf-accent) ${Math.round(p * 18)}%,transparent)`;
      }, 'power2.out');
    });
    /* composer */
    const comp = h('div', '', main);
    comp.style.cssText = 'margin-top:auto;display:flex;align-items:center;gap:10px;border:1px solid var(--pf-line);border-radius:11px;padding:9px 12px;background:var(--pf-card-2)';
    const ct = h('span', '', comp);
    ct.style.cssText = 'font-size:12.5px;color:var(--pf-muted);flex:1';
    const caret2 = h('span', '', comp);
    caret2.style.cssText = 'width:1.5px;height:15px;background:var(--pf-accent)';
    const go = h('span', '', comp);
    go.style.cssText = 'width:24px;height:24px;border-radius:7px;background:var(--pf-accent);display:flex;align-items:center;justify-content:center;color:var(--pf-bg)';
    const gi = icon('arrow', go); gi.style.cssText = 'width:12px;height:12px';
    tl.fromTo(win, { opacity: 0, y: 30, scale: .97 }, { opacity: 1, y: 0, scale: 1, duration: 0.6, ease: 'power3.out' }, 0.1);
    fadeIn(tl, comp, 1.2, 0.4, 8);
    if (spec.prompt) { typewrite(tl, ct, spec.prompt, 1.5, 1.1); caretBlink(tl, caret2, 1.5, 1.2); tl.to(caret2, { opacity: 0, duration: .1 }, 2.75); }
    else caret2.style.display = 'none';
    return { el, tl };
  };

  /* --- phone-app: clean device card stack --- */
  scenes['phone-app'] = (spec) => {
    const el = h('div', '', null);
    el.style.cssText = 'flex:1;display:flex;align-items:center;justify-content:center;gap:26px;position:relative';
    const tl = NexMotion.createTimeline();
    const phone = h('div', '', el);
    phone.style.cssText = 'width:238px;height:88%;max-height:470px;border-radius:30px;border:1px solid var(--pf-line);background:var(--pf-card);padding:12px;display:flex;flex-direction:column;gap:10px;box-shadow:0 30px 70px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.07);overflow:hidden;flex:none';
    const status = h('div', '', phone);
    status.style.cssText = 'display:flex;justify-content:space-between;padding:2px 8px 0;font:600 9px var(--pf-mono);color:var(--pf-muted)';
    status.innerHTML = '<span>9:41</span><span>●●●</span>';
    const heroSrc = mediaOf(spec.hero && spec.hero.img) || mediaOf((spec.cards || [])[0] && spec.cards[0].img);
    const hero = h('div', '', phone);
    hero.style.cssText = 'border-radius:14px;overflow:hidden;border:1px solid var(--pf-line);flex:none;height:34%;position:relative;background:linear-gradient(150deg,var(--pf-card-2),var(--pf-card))';
    if (heroSrc) hero.appendChild(mediaImg(heroSrc));
    else {
      const glow = h('div', '', hero);
      glow.style.cssText = 'position:absolute;inset:0;background:radial-gradient(circle at 30% 30%,color-mix(in srgb,var(--pf-accent) 30%,transparent),transparent 70%)';
      const ic = icon('film', hero); ic.style.cssText = 'position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:34px;height:34px;color:var(--pf-fg);opacity:.8';
    }
    if (spec.hero && spec.hero.title) {
      const ht = h('div', '', hero, spec.hero.title);
      ht.style.cssText = 'position:absolute;left:10px;bottom:8px;font:700 13px var(--pf-display);letter-spacing:-.01em';
    }
    const cards = (spec.cards || []).slice(0, 4);
    cards.forEach((c, i) => {
      const row = h('div', '', phone);
      row.style.cssText = 'display:flex;align-items:center;gap:10px;padding:9px 10px;border:1px solid var(--pf-line);border-radius:11px;background:var(--pf-card-2);flex:none';
      const th = h('span', '', row);
      th.style.cssText = 'width:30px;height:30px;border-radius:8px;flex:none;overflow:hidden;display:flex;align-items:center;justify-content:center;background:color-mix(in srgb,var(--pf-accent) 14%,transparent);color:var(--pf-accent)';
      if (c.img && mediaOf(c.img)) th.appendChild(mediaImg(mediaOf(c.img)));
      else { const ic2 = icon(c.icon || 'film', th); ic2.style.cssText = 'width:15px;height:15px'; }
      const tt = h('div', '', row);
      tt.style.cssText = 'display:flex;flex-direction:column;min-width:0';
      const t1 = h('span', '', tt, c.title || '');
      t1.style.cssText = 'font-size:11.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
      if (c.sub || c.meta) { const t2 = h('span', '', tt, c.sub || c.meta); t2.style.cssText = 'font-size:9.5px;color:var(--pf-muted)'; }
      fadeIn(tl, row, 0.6 + i * 0.22, 0.4, 10);
    });
    const caption = h('div', '', el);
    caption.style.cssText = 'display:flex;flex-direction:column;gap:8px;max-width:38%';
    const cap = h('div', 'pf-display', caption, spec.caption || '');
    cap.style.cssText = `font-size:${fsize('26px')};font-weight:600;line-height:1.15;letter-spacing:-.015em`;
    if (spec.sub) { const s = h('div', '', caption, spec.sub); s.style.cssText = 'font-size:13px;color:var(--pf-muted)'; }
    tl.fromTo(phone, { opacity: 0, y: 40, rotation: 2 }, { opacity: 1, y: 0, rotation: 0, duration: 0.65, ease: 'power3.out' }, 0.15);
    fadeIn(tl, caption, 0.5, 0.5, 18);
    return { el, tl };
  };

  /* --- storyboard: mini frames grid --- */
  scenes['storyboard'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 12, '0');
    const cells = spec.cells;
    const labels = Array.isArray(cells) ? cells.slice(0, 6) : [];
    const n = Array.isArray(cells) ? labels.length : (Number(cells) || 6);
    const cols = n > 4 ? 3 : n;
    const grid = h('div', '', el);
    grid.style.cssText = `flex:1;display:grid;grid-template-columns:repeat(${cols},1fr);grid-auto-rows:1fr;gap:11px`;
    const tl = NexMotion.createTimeline();
    for (let i = 0; i < n; i++) {
      const cell = h('div', 'pf-card', grid);
      cell.style.cssText = 'position:relative;overflow:hidden;display:flex;align-items:flex-end;padding:9px;border-radius:13px';
      const th = spec.thumbs && spec.thumbs[i] ? mediaOf(spec.thumbs[i]) : null;
      if (th) cell.appendChild(mediaImg(th));
      else {
        const inner = h('div', '', cell);
        inner.style.cssText = 'position:absolute;inset:8px;border-radius:8px;border:1px dashed var(--pf-line);display:flex;align-items:center;justify-content:center';
        const ic = icon(['film', 'image', 'chart', 'chat', 'cube', 'play'][i % 6], inner); ic.style.cssText = 'width:22px;height:22px;color:var(--pf-muted)';
      }
      const lb = h('span', 'pf-mono', cell, labels[i] || `S${i + 1}`);
      lb.style.cssText = 'position:relative;z-index:1;font-size:9px;letter-spacing:.12em;color:var(--pf-muted);background:color-mix(in srgb,var(--pf-bg) 78%,transparent);padding:3px 7px;border-radius:5px';
      if (i === 1) cell.style.borderColor = 'color-mix(in srgb,var(--pf-accent) 55%,transparent)';
      popIn(tl, cell, 0.15 + i * 0.14, 0.45);
    }
    return { el, tl };
  };

  /* --- render-bar: progress + ticking log --- */
  scenes['render-bar'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 20, '0 8%');
    const file = h('div', 'pf-mono', el, spec.file || 'output.mp4');
    file.style.cssText = 'font-size:12px;letter-spacing:.14em;color:var(--pf-muted);text-transform:uppercase;display:flex;align-items:center;gap:10px';
    const dot = h('span', '', file); dot.style.cssText = 'width:7px;height:7px;border-radius:50%;background:var(--pf-accent)';
    const track = h('div', '', el);
    track.style.cssText = 'height:10px;border-radius:99px;background:var(--pf-card);border:1px solid var(--pf-line);overflow:hidden';
    const fill = h('div', '', track);
    fill.style.cssText = 'height:100%;width:0;background:var(--pf-accent);border-radius:99px;box-shadow:0 0 16px color-mix(in srgb,var(--pf-accent) 60%,transparent)';
    const pct = h('div', 'pf-display', el, '0%');
    pct.style.cssText = `font-size:${fsize('54px')};font-weight:700;letter-spacing:-.03em`;
    const log = h('div', 'pf-mono', el);
    log.style.cssText = 'font-size:11px;color:var(--pf-muted);display:flex;flex-direction:column;gap:4px;letter-spacing:.06em';
    const tl = NexMotion.createTimeline();
    fadeIn(tl, file, 0.1, 0.4);
    const dur = Math.max(1.4, (spec.duration || 4) - 1.2);
    tl.addUpdate(0.4, dur, p => {
      fill.style.width = (p * 100) + '%';
      pct.textContent = Math.round(p * 100) + '%';
    }, 'power1.inOut');
    const lines = ['resolving beats…', 'composing scenes…', 'mixing audio…', 'writing frames…'];
    lines.forEach((l, i) => {
      const li = h('div', '', log, l);
      const at = 0.5 + (i / lines.length) * dur * 0.8;
      fadeIn(tl, li, at, 0.3, 6);
      tl.addUpdate(at + 0.3, 0.2, p => { li.style.color = p > 0.5 ? 'var(--pf-accent)' : 'var(--pf-muted)'; }, 'none');
    });
    return { el, tl };
  };

  /* --- step: giant index + title + meta column --- */
  scenes['step'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 10, '0 4%');
    const num = h('div', 'pf-outline', el, String(spec.word || spec.marker || '01'));
    num.style.cssText = `font-size:${fsize('120px')};-webkit-text-stroke-color:color-mix(in srgb,var(--pf-fg) 40%,transparent)`;
    const head = h('h2', 'pf-display', el, spec.head || spec.caption || '');
    head.style.cssText = `font-size:${fsize('46px')};margin-top:-14px`;
    const tl = NexMotion.createTimeline();
    tl.fromTo(num, { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: 0.55, ease: 'power3.out' }, 0.15);
    tl.fromTo(head, { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0.4);
    let metaCol = null;
    if (spec.meta || spec.result) {
      metaCol = h('div', '', el);
      metaCol.style.cssText = 'position:absolute;right:2%;top:8%;display:flex;flex-direction:column;gap:7px;align-items:flex-end;text-align:right;max-width:32%';
      if (spec.result) {
        const rb = h('span', 'pf-chip acc', metaCol, spec.result);
        rb.style.cssText += ';font-size:11px;color:var(--pf-accent)';
      }
      (spec.meta || []).slice(0, 4).forEach(m => {
        const mm = h('span', 'pf-mono', metaCol, m);
        mm.style.cssText = 'font-size:10px;letter-spacing:.1em;color:var(--pf-muted);text-transform:uppercase';
      });
      fadeIn(tl, metaCol, 0.8, 0.4);
    }
    if (spec.sub) fadeIn(tl, sub(el, spec.sub), 0.9, 0.4);
    return { el, tl };
  };

  /* --- player: media card with progress --- */
  scenes['player'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 14, '0 4%');
    const card = h('div', 'pf-card', el);
    card.style.cssText = 'flex:1;display:flex;flex-direction:column;overflow:hidden;padding:0;border-radius:20px;box-shadow:0 24px 60px rgba(0,0,0,.45)';
    const stage = h('div', '', card);
    stage.style.cssText = 'flex:1;position:relative;overflow:hidden;background:linear-gradient(140deg,var(--pf-card-2),var(--pf-card))';
    const poster = mediaOf(spec.poster || spec.media);
    if (poster) stage.appendChild(mediaImg(poster));
    else {
      const g = h('div', '', stage);
      g.style.cssText = 'position:absolute;inset:0;background:radial-gradient(circle at 50% 40%,color-mix(in srgb,var(--pf-accent) 22%,transparent),transparent 65%)';
    }
    if (spec.innerTitle) {
      const it = h('div', 'pf-display', stage, spec.innerTitle);
      it.style.cssText = `position:absolute;left:18px;bottom:14px;font-size:${fsize('30px')};font-weight:700;letter-spacing:-.02em;text-shadow:0 2px 14px rgba(0,0,0,.55)`;
      if (spec.innerSub) { const is = h('div', '', stage, spec.innerSub); is.style.cssText = 'position:absolute;left:18px;bottom:48px;font-size:12px;color:rgba(255,255,255,.75)'; }
    }
    const play = h('div', '', stage);
    play.style.cssText = 'position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:64px;height:64px;border-radius:50%;background:color-mix(in srgb,var(--pf-bg) 55%,transparent);backdrop-filter:blur(6px);border:1px solid var(--pf-line);display:flex;align-items:center;justify-content:center';
    const pi = icon('play', play); pi.style.cssText = 'width:22px;height:22px;color:var(--pf-fg);margin-left:3px';
    const ctrl = h('div', '', card);
    ctrl.style.cssText = 'flex:none;display:flex;align-items:center;gap:12px;padding:12px 16px;border-top:1px solid var(--pf-line)';
    const pt = h('span', 'pf-mono', ctrl, '0:00');
    pt.style.cssText = 'font-size:10.5px;color:var(--pf-muted)';
    const bar = h('div', '', ctrl);
    bar.style.cssText = 'flex:1;height:4px;border-radius:99px;background:var(--pf-card-2);overflow:hidden';
    const bf = h('div', '', bar);
    bf.style.cssText = 'height:100%;width:0;background:var(--pf-accent);border-radius:99px';
    const dur = h('span', 'pf-mono', ctrl, spec.durationLabel || '0:38');
    dur.style.cssText = 'font-size:10.5px;color:var(--pf-muted)';
    const tl = NexMotion.createTimeline();
    tl.fromTo(card, { opacity: 0, y: 26, scale: .98 }, { opacity: 1, y: 0, scale: 1, duration: 0.6, ease: 'power3.out' }, 0.12);
    popIn(tl, play, 0.5, 0.45);
    tl.addUpdate(0.8, Math.max(1, (spec.duration || 4) - 1.4), p => {
      bf.style.width = (p * 100) + '%';
      const sec = Math.round(p * 38);
      pt.textContent = `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;
    }, 'none');
    return { el, tl };
  };

  /* --- phrase-swap: fixed lead + rotating tail word --- */
  scenes['phrase-swap'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const line = h('div', '', el);
    line.style.cssText = 'display:flex;align-items:baseline;gap:.28em;flex-wrap:wrap;justify-content:center;max-width:92%';
    const lead = h('span', 'pf-display', line, spec.lead || '');
    lead.style.cssText = `font-size:${fsize('54px')}`;
    const mask = h('span', '', line);
    mask.style.cssText = 'display:inline-block;overflow:hidden;vertical-align:bottom;height:1.1em;position:relative';
    const wA = h('span', 'pf-display', mask, spec.swapFrom || '');
    wA.style.cssText = `font-size:${fsize('54px')};display:block;color:var(--pf-muted)`;
    const wB = h('span', 'pf-display', mask, spec.swapTo || '');
    wB.style.cssText = `font-size:${fsize('54px')};display:block;color:var(--pf-accent);position:absolute;left:0;top:0;transform:translateY(105%)`;
    const tl = NexMotion.createTimeline();
    tl.fromTo(lead, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0.2);
    tl.fromTo(wA, { y: 30 }, { y: 0, duration: 0.45, ease: 'power3.out' }, 0.45);
    tl.to(wA, { y: '-105%', duration: 0.5, ease: 'power3.inOut' }, 1.35);
    tl.to(wB, { y: '0%', duration: 0.5, ease: 'power3.inOut' }, 1.35);
    return { el, tl };
  };

  /* --- word-object-bridge: word crossfades into the thing --- */
  scenes['word-object-bridge'] = (spec) => {
    const el = h('div', '', null);
    center(el);
    const kw = h('h2', 'pf-display', el, `${spec.before || ''} ${spec.keyword || ''}`.trim());
    kw.style.cssText = `font-size:${fsize('58px')}`;
    const src = mediaOf(spec.object || spec.media);
    const obj = h('div', 'pf-card', el);
    obj.style.cssText = 'width:200px;height:200px;border-radius:20px;overflow:hidden;display:flex;align-items:center;justify-content:center;position:absolute;opacity:0';
    if (src) obj.appendChild(mediaImg(src));
    else { const ic = icon(spec.icon || 'cube', obj); ic.style.cssText = 'width:70px;height:70px;color:var(--pf-accent)'; }
    const after = h('div', '', el, spec.after || '');
    after.style.cssText = 'font-size:16px;color:var(--pf-muted)';
    const tl = NexMotion.createTimeline();
    tl.fromTo(kw, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, 0.15);
    tl.to(kw, { opacity: 0, scale: .86, duration: 0.45, ease: 'power2.in' }, 1.1);
    tl.fromTo(obj, { opacity: 0, scale: .6, rotation: -4 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.55, ease: 'back.out(1.8)' }, 1.35);
    fadeIn(tl, after, 1.8, 0.4);
    return { el, tl };
  };

  /* --- compose-graph: node map --- */
  scenes['compose-graph'] = (spec) => {
    const el = h('div', '', null);
    stack(el, 12, '0');
    if (spec.title) {
      const t = h('h2', 'pf-display', el, spec.title);
      t.style.cssText = `font-size:${fsize('32px')};font-weight:600`;
    }
    const wrap = h('div', '', el);
    wrap.style.cssText = 'flex:1;position:relative';
    const g = sv('svg', { viewBox: '0 0 620 460' }, wrap);
    g.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    const P = [[110, 230], [260, 110], [260, 350], [430, 110], [430, 350], [540, 230]];
    const E = [[0, 1], [0, 2], [1, 3], [2, 4], [3, 5], [4, 5]];
    const tl = NexMotion.createTimeline();
    if (spec.title) fadeIn(tl, el.firstChild, 0.1, 0.4);
    E.forEach(([a, b], i) => {
      const [x1, y1] = P[a], [x2, y2] = P[b];
      const p = sv('path', { d: `M${x1} ${y1} C${(x1 + x2) / 2} ${y1} ${(x1 + x2) / 2} ${y2} ${x2} ${y2}`, fill: 'none', stroke: cssVar('--pf-line'), 'stroke-width': 1.6 }, g);
      drawStroke(tl, p, 0.3 + i * 0.18, 0.5);
    });
    P.forEach(([x, y], i) => {
      const n = sv('g', {}, g);
      sv('circle', { cx: x, cy: y, r: 30, fill: cssVar('--pf-card'), stroke: i === 0 || i === 5 ? cssVar('--pf-accent') : cssVar('--pf-line'), 'stroke-width': 1.6 }, n);
      const lbl = sv('text', { x, y: y + 4, 'text-anchor': 'middle', fill: cssVar('--pf-fg'), 'font-size': 10, 'font-family': 'JetBrains Mono,monospace', 'letter-spacing': '1' }, n);
      lbl.textContent = (spec.nodes && spec.nodes[i]) || ['BRIEF', 'PLAN', 'DRAW', 'MIX', 'CHECK', 'FILM'][i] || `N${i}`;
      tl.fromTo(n, { opacity: 0, scale: .5, transformOrigin: `${x}px ${y}px` }, { opacity: 1, scale: 1, duration: 0.45, ease: 'back.out(1.8)' }, 0.25 + i * 0.16);
    });
    return { el, tl };
  };

  /* --- logo-mark / brandMark: centered mark --- */
  const markScene = (spec) => {
    const el = h('div', '', null);
    center(el);
    const tile = markTile(el, spec, 160);
    tile.dataset.cap = 'brand';
    const tl = NexMotion.createTimeline();
    if (tile._svgParts) {
      tl.fromTo(tile, { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0.1);
      drawPathSeq(tl, tile._svgParts, 0.2, 1.4);
    } else {
      tl.fromTo(tile, { opacity: 0, scale: .7, rotation: -5 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.65, ease: 'back.out(1.8)' }, 0.15);
    }
    return { el, tl };
  };
  scenes['logo-mark'] = markScene;
  scenes['brandMark'] = markScene;

  /* fallbacks — types with no dedicated product builder resolve to
     the closest cousin so every spec type renders */
  scenes['word-object-bridge'] = scenes['word-object-bridge'];

  /* ============================================================
     FILM MASTER — identical contract to sketch-ui: section windows,
     driven transitions, camera on its own layer, zero dead air.
     ============================================================ */
  function collectEffects(root) {
    const out = [];
    (root.querySelectorAll?.('[data-active-motion]') || []).forEach(el => {
      if (el.__nexMotionTimeline) out.push(el.__nexMotionTimeline);
    });
    if (root.__nexMotionTimeline) out.push(root.__nexMotionTimeline);
    return out;
  }

  function buildScene(spec, idx, total, filmSpec) {
    const sec = h('section', 'pf-scene');
    const layout = spec.layout || (filmSpec && filmSpec.layout);
    if (layout) sec.classList.add(`layout-${layout}`);
    const cam = h('div', 'pf-cam', sec);
    const safe = h('div', 'pf-safe', cam);
    spec.index = idx;
    const body = (scenes[spec.type] || scenes['type-card'])(spec);
    safe.appendChild(body.el);
    furniture(sec, spec, idx, total);
    mountCallouts(sec, spec, body.tl);
    return { spec, el: sec, cam, tl: body.tl, fx: collectEffects(sec) };
  }

  /* --- callouts: rough-notation-style annotations over live elements -------
     spec.callouts: [{ type, target, at, dur, color, pad }]
     type: 'circle'|'underline'|'box'|'strike'|'highlight'|'bracket'|'crossed'
     target: data-cap name ('title','stat','frame','brand','cta','hub','input'…)
             or a number → item-N / word-N. Empty → first tagged element. */
  const mulberry = (a) => () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const resolveCap = (sec, target) => {
    if (target == null) return sec.querySelector('[data-cap]');
    if (typeof target === 'number')
      return sec.querySelector(`[data-cap="item-${target}"]`) || sec.querySelector(`[data-cap="word-${target}"]`) || sec.querySelectorAll('[data-cap]')[target] || null;
    return sec.querySelector(`[data-cap="${target}"]`);
  };
  const jitterPath = (pts, rnd, amp) => pts.map((p, i) => (i === 0 ? `M` : `L`) + (p[0] + (rnd() - 0.5) * amp).toFixed(1) + ' ' + (p[1] + (rnd() - 0.5) * amp).toFixed(1)).join(' ');
  const ellipsePts = (cx, cy, rx, ry, n = 26, rot = 0) => Array.from({ length: n + 1 }, (_, i) => {
    const a = (i / n) * Math.PI * 2 + rot;
    return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
  });
  /* returns [{d, w2}] stroke paths or {fill:true,d} — lengths measured at mount */
  const calloutPaths = (type, w, hgt, rnd) => {
    const J = 2.2;
    switch (type) {
      case 'circle': {
        const a = jitterPath(ellipsePts(w / 2, hgt / 2, w / 2 * 0.96, hgt / 2 * 0.88, 30), rnd, J) + ' Z';
        const b = jitterPath(ellipsePts(w / 2, hgt / 2, w / 2 * 0.93, hgt / 2 * 0.91, 30, 0.35), rnd, J) + ' Z';
        return [{ d: a }, { d: b }];
      }
      case 'underline': {
        const y = hgt - 3;
        const wave = (dy) => jitterPath([[0, y + dy], [w * 0.25, y - 1.5 + dy], [w * 0.5, y + 0.5 + dy], [w * 0.75, y - 1 + dy], [w, y + dy]], rnd, 1.4);
        return [{ d: wave(0) }, { d: wave(2.4) }];
      }
      case 'strike': {
        const y = hgt * 0.55;
        return [{ d: jitterPath([[0, y], [w * 0.33, y - 2], [w * 0.66, y + 1.5], [w, y - 1]], rnd, 1.6) }];
      }
      case 'box': {
        const a = jitterPath([[0, 0], [w, 0], [w, hgt], [0, hgt], [0, 0]], rnd, J);
        const b = jitterPath([[1.5, 1.5], [w + 1, -1], [w - 1, hgt + 1], [-1, hgt - 1], [1.5, 1.5]], rnd, J);
        return [{ d: a }, { d: b }];
      }
      case 'bracket': {
        const bx = 7;
        return [
          { d: jitterPath([[bx + 8, 2], [2, 2], [2, hgt - 2], [bx + 8, hgt - 2]], rnd, 1.2) },
          { d: jitterPath([[w - bx - 8, 2], [w - 2, 2], [w - 2, hgt - 2], [w - bx - 8, hgt - 2]], rnd, 1.2) },
        ];
      }
      case 'crossed': {
        return [
          { d: jitterPath([[2, 2], [w / 2, hgt / 2], [w - 2, hgt - 2]], rnd, 1.8) },
          { d: jitterPath([[w - 2, 2], [w / 2, hgt / 2], [2, hgt - 2]], rnd, 1.8) },
        ];
      }
      case 'highlight':
      default: /* highlight */
        return [{ fill: true, d: `M0 ${hgt * 0.12} L${w} ${hgt * 0.1} L${w} ${hgt * 0.92} L0 ${hgt * 0.9} Z` }];
    }
  };
  const mountCallouts = (sec, spec, tl) => {
    const list = spec.callouts || [];
    if (!list.length) return;
    const rnd = mulberry((spec.index || 0) * 7919 + 13);
    /* mount lazily at each callout's own start — by then the target's entrance
       has settled, so its rect is the final box (mounting at t=0 would pin the
       mark to the mid-entrance position) */
    list.forEach((c, ci) => {
      const at = typeof c.at === 'number' ? c.at : 1.1 + ci * 0.55;
      let done = false;
      tl.addUpdate(Math.max(0.02, at - 0.02), 0.02, (p) => {
        if (done || p <= 0) return; done = true;
        const target = resolveCap(sec, c.target);
        if (!target) return;
        const r = target.getBoundingClientRect(), hr = sec.getBoundingClientRect();
        const pad = c.pad ?? (c.type === 'circle' ? 12 : 6);
        const x = r.left - hr.left - pad, y = r.top - hr.top - pad;
        const w = r.width + pad * 2, hg = r.height + pad * 2;
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${hg}px;overflow:visible;pointer-events:none;z-index:7`;
        sec.appendChild(svg);
        const color = c.color || cssVar('--pf-accent');
        const paths = calloutPaths(c.type || 'circle', w, hg, rnd);
        const dur = c.dur ?? 0.55;
        paths.forEach((pp, pi) => {
          const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          if (pp.fill) {
            p.setAttribute('d', pp.d);
            p.setAttribute('fill', color); p.setAttribute('fill-opacity', '0.24');
            p.setAttribute('stroke', color); p.setAttribute('stroke-opacity', '0.5'); p.setAttribute('stroke-width', '1');
            p.style.transformOrigin = '0 50%';
            const pi_at = at + pi * 0.08;
            p.style.transform = 'scaleX(0)';
            tl.addUpdate(pi_at, dur, (q) => { p.style.transform = `scaleX(${q})`; }, 'power3.out');
          } else {
            p.setAttribute('d', pp.d);
            p.setAttribute('fill', 'none');
            p.setAttribute('stroke', color);
            p.setAttribute('stroke-width', String(c.strokeWidth || 2.2));
            p.setAttribute('stroke-linecap', 'round');
            p.setAttribute('stroke-linejoin', 'round');
            svg.appendChild(p);
            const L = p.getTotalLength() || w * 2 + hg * 2;
            p.style.strokeDasharray = String(L);
            p.style.strokeDashoffset = String(L);
            const pi_at = at + pi * (dur * 0.55);
            tl.addUpdate(pi_at, dur, (q) => { p.style.strokeDashoffset = String(L * (1 - q)); }, 'power2.out');
          }
          svg.appendChild(p);
        });
      }, 'none');
    });
  };
  const T_MAP = {
    torn: 'mask', push: 'slide', page: 'zoom', shuffle: 'slide',
    tape: 'wipe', crumple: 'zoom', paper: 'slide',
  };
  const TRANSITION_DUR = 0.62;
  const transitionStyle = (key, outEl, inEl, p) => {
    const e = p * p * (3 - 2 * p); // smoothstep
    switch (key) {
      case 'slide':
        outEl.style.opacity = String(1 - e * 0.9); outEl.style.transform = `translateX(${-9 * e}%)`;
        inEl.style.opacity = String(0.2 + 0.8 * e); inEl.style.transform = `translateX(${9 * (1 - e)}%)`;
        break;
      case 'zoom':
        outEl.style.opacity = String(1 - e); outEl.style.transform = `scale(${1 + 0.08 * e})`; outEl.style.filter = `blur(${8 * e}px)`;
        inEl.style.opacity = String(e); inEl.style.transform = `scale(${0.94 + 0.06 * e})`; inEl.style.filter = `blur(${8 * (1 - e)}px)`;
        break;
      case 'blur':
        outEl.style.opacity = String(1 - e); outEl.style.filter = `blur(${10 * e}px)`;
        inEl.style.opacity = String(e); inEl.style.filter = `blur(${10 * (1 - e)}px)`;
        break;
      case 'mask':
        outEl.style.opacity = String(1 - e * 0.85);
        inEl.style.opacity = '1';
        inEl.style.clipPath = `circle(${e * 78}% at 50% 44%)`;
        break;
      case 'wipe':
        outEl.style.opacity = String(1 - e * 0.9);
        inEl.style.opacity = '1';
        inEl.style.clipPath = `inset(0 ${(1 - e) * 100}% 0 0)`;
        break;
      case 'rise':
        outEl.style.opacity = String(1 - e * 0.9);
        inEl.style.opacity = String(e); inEl.style.transform = `translateY(${34 * (1 - e)}px)`;
        break;
      case 'cut':
        outEl.style.opacity = p < 0.5 ? '1' : '0';
        inEl.style.opacity = p < 0.5 ? '0' : '1';
        break;
      /* --- gl-transitions ports: shape/mask/transform writers, shared with
         the sketch surface (same key → same move on either skin) --- */
      case 'iris':
        outEl.style.opacity = String(1 - e * 0.85);
        inEl.style.opacity = '1';
        inEl.style.clipPath = `circle(${e * 78}% at 50% 50%)`;
        break;
      case 'diamond':
        outEl.style.opacity = String(1 - e * 0.85);
        inEl.style.opacity = '1';
        inEl.style.clipPath = `polygon(50% ${50 - 52 * e}%, ${50 + 52 * e}% 50%, 50% ${50 + 52 * e}%, ${50 - 52 * e}% 50%)`;
        break;
      case 'clockwipe':
        outEl.style.opacity = String(1 - e * 0.8);
        inEl.style.opacity = '1';
        inEl.style.maskImage = `conic-gradient(from -90deg at 50% 50%, #000 ${e * 360}deg, transparent ${e * 360}deg)`;
        inEl.style.webkitMaskImage = inEl.style.maskImage;
        break;
      case 'blinds':
        outEl.style.opacity = String(1 - e * 0.8);
        inEl.style.opacity = '1';
        inEl.style.maskImage = `repeating-linear-gradient(90deg, #000 0 ${e * 64}px, transparent ${e * 64}px 64px)`;
        inEl.style.webkitMaskImage = inEl.style.maskImage;
        break;
      case 'crosshatch': {
        const w = 64 * e;
        outEl.style.opacity = String(1 - e * 0.85);
        inEl.style.opacity = '1';
        const g = `repeating-linear-gradient(45deg, #000 0 ${w}px, transparent ${w}px 64px), repeating-linear-gradient(-45deg, #000 0 ${w}px, transparent ${w}px 64px)`;
        inEl.style.maskImage = g; inEl.style.webkitMaskImage = g;
        inEl.style.maskComposite = 'intersect'; inEl.style.webkitMaskComposite = 'source-in';
        break;
      }
      case 'doors':
        outEl.style.opacity = String(1 - e * 0.85);
        inEl.style.opacity = '1';
        inEl.style.maskImage = 'linear-gradient(90deg,#000,#000),linear-gradient(90deg,#000,#000)';
        inEl.style.webkitMaskImage = inEl.style.maskImage;
        inEl.style.maskSize = `${e * 51}% 100%, ${e * 51}% 100%`;
        inEl.style.webkitMaskSize = inEl.style.maskSize;
        inEl.style.maskPosition = '0% 0%, 100% 0%';
        inEl.style.webkitMaskPosition = inEl.style.maskPosition;
        inEl.style.maskRepeat = 'no-repeat, no-repeat';
        inEl.style.webkitMaskRepeat = inEl.style.maskRepeat;
        break;
      case 'squeeze':
        outEl.style.opacity = String(1 - e); outEl.style.transform = `scaleX(${1 - 0.38 * e}) translateX(${-14 * e}%)`;
        inEl.style.opacity = String(0.3 + 0.7 * e); inEl.style.transform = `scaleX(${0.8 + 0.2 * e}) translateX(${14 * (1 - e)}%)`;
        break;
      case 'crosswarp':
        outEl.style.opacity = String(1 - e); outEl.style.transform = `scale(${1 + 0.45 * e})`;
        inEl.style.opacity = String(Math.min(1, e * 1.7)); inEl.style.transform = `scale(${1.45 - 0.45 * e})`;
        break;
      case 'dreamy':
        outEl.style.opacity = String(1 - e); outEl.style.filter = `blur(${14 * e}px)`; outEl.style.transform = `scale(${1 + 0.12 * e})`;
        inEl.style.opacity = String(e); inEl.style.filter = `blur(${14 * (1 - e)}px)`; inEl.style.transform = `scale(${1.08 - 0.08 * e})`;
        break;
      case 'swirl':
        outEl.style.opacity = String(1 - e); outEl.style.transform = `rotate(${-9 * e}deg) scale(${1 + 0.28 * e})`;
        inEl.style.opacity = String(e); inEl.style.transform = `rotate(${9 * (1 - e)}deg) scale(${0.72 + 0.28 * e})`;
        break;
      case 'linearblur':
        outEl.style.opacity = String(1 - e); outEl.style.filter = `blur(${10 * e}px)`; outEl.style.transform = `translateX(${-16 * e}%)`;
        inEl.style.opacity = String(e); inEl.style.filter = `blur(${10 * (1 - e)}px)`; inEl.style.transform = `translateX(${16 * (1 - e)}%)`;
        break;
      case 'fadefilter':
        outEl.style.opacity = String(1 - e); outEl.style.filter = `grayscale(${e}) brightness(${1 - 0.3 * e})`;
        inEl.style.opacity = String(e); inEl.style.filter = `grayscale(${1 - e}) brightness(${0.7 + 0.3 * e})`;
        break;
      case 'dissolve':
        outEl.style.opacity = String(1 - e);
        inEl.style.opacity = String(Math.min(1, e * 1.25));
        inEl.style.maskImage = `url('product-ui/textures/grain-fine-256.png')`;
        inEl.style.webkitMaskImage = inEl.style.maskImage;
        inEl.style.maskSize = `${140 + 60 * (1 - e)}%`;
        inEl.style.webkitMaskSize = inEl.style.maskSize;
        break;
      case 'starwipe': {
        const pts = [];
        for (let i = 0; i < 10; i++) {
          const r = (i % 2 === 0 ? 80 : 34) * e;
          const a = (-90 + i * 36) * Math.PI / 180;
          pts.push(`${50 + r * Math.cos(a)}% ${50 + r * Math.sin(a)}%`);
        }
        outEl.style.opacity = String(1 - e * 0.85);
        inEl.style.opacity = '1';
        inEl.style.clipPath = `polygon(${pts.join(',')})`;
        break;
      }
      default: /* fade */
        outEl.style.opacity = String(1 - e);
        inEl.style.opacity = String(e);
    }
  };
  const transitionReset = (outEl, inEl) => {
    for (const el of [outEl, inEl]) {
      el.style.transform = ''; el.style.clipPath = ''; el.style.filter = '';
      el.style.maskImage = ''; el.style.webkitMaskImage = ''; el.style.maskSize = '';
      el.style.maskPosition = ''; el.style.maskRepeat = ''; el.style.maskComposite = '';
      el.style.webkitMaskSize = ''; el.style.webkitMaskPosition = ''; el.style.webkitMaskRepeat = ''; el.style.webkitMaskComposite = '';
    }
    outEl.style.opacity = '0'; inEl.style.opacity = '1';
  };

  function start(filmSpec) {
    const stage = document.querySelector('[data-nex-production-canvas]');
    if (!stage) throw new Error('missing [data-nex-production-canvas] stage');
    stage.classList.add('pf-stage');
    document.documentElement.classList.add('pf'); document.body.classList.add('pf');
    /* theme tokens → --pf-* on stage AND documentElement */
    const theme = filmSpec.theme || {};
    const THEME_VARS = {
      bg: '--pf-bg', paper: '--pf-bg', fg: '--pf-fg', ink: '--pf-fg', muted: '--pf-muted',
      card: '--pf-card', surface: '--pf-card', card2: '--pf-card-2', line: '--pf-line',
      accent: '--pf-accent', accentDeep: '--pf-accent-2', accent2: '--pf-accent-2',
      display: '--pf-display', sans: '--pf-sans', mono: '--pf-mono',
    };
    for (const [k, v] of Object.entries(THEME_VARS)) {
      const val = theme[k];
      if (val) { stage.style.setProperty(v, val); document.documentElement.style.setProperty(v, val); }
    }
    if (filmSpec.layout) stage.classList.add(`layout-${filmSpec.layout}`);
    if (filmSpec.grainTexture) stage.style.setProperty('--pf-grain', `url('${filmSpec.grainTexture}')`);
    h('div', 'pf-glow', stage);
    assetIndex = {};
    svgAssetIndex = filmSpec.svgAssets || {};
    for (const [name, rel] of Object.entries(filmSpec.assets || {})) {
      const ext = (rel.match(/\.[^./\\]+$/) || ['.png'])[0];
      assetIndex[name] = `media/${name}${ext}`;
    }

    const scenesBuilt = (filmSpec.scenes || []).map((s, i) => { const b = buildScene(s, i, filmSpec.scenes.length, filmSpec); stage.appendChild(b.el); return b; });

    /* transition pairs */
    const transitions = [];
    for (let i = 1; i < scenesBuilt.length; i++) {
      const prev = scenesBuilt[i - 1], next = scenesBuilt[i];
      const raw = next.spec.transition || 'fade';
      const key = T_MAP[raw] || raw;
      transitions.push({ key, outEl: prev.el, inEl: next.el, end: next.spec.start, dur: TRANSITION_DUR });
    }

    const total = filmSpec.durationSeconds;
    const master = NexMotion.createTimeline();
    master.pause();

    master.addUpdate(0, total, (p, raw, time) => {
      scenesBuilt.forEach((b, bi) => {
        const s0 = b.spec.start, s1 = b.spec.start + b.spec.duration;
        const tr = transitions.find(t => t.inEl === b.el);
        const on = (time >= s0 && time < s1) || (tr && time >= tr.end - tr.dur && time < tr.end) || (transitions.some(t => t.outEl === b.el) && time >= s1 && time < s1 + TRANSITION_DUR);
        b.el.classList.toggle('on', on);
        if (!on) return;
        const inTr = tr && time >= tr.end - tr.dur && time < tr.end;
        const preroll = bi === 0 ? 0.4 : (inTr ? Math.min(0.5, tr.dur * 0.75) : 0);
        const local = Math.min(Math.max(time - s0 + preroll, 0), b.tl.cursor);
        const driven = transitions.some(t => (t.inEl === b.el || t.outEl === b.el) && time >= t.end - t.dur && time < t.end);
        if (!driven) {
          b.el.style.opacity = '1';
          b.el.style.transform = ''; b.el.style.clipPath = ''; b.el.style.filter = '';
          b.el.style.maskImage = ''; b.el.style.webkitMaskImage = ''; b.el.style.maskSize = '';
          b.el.style.maskPosition = ''; b.el.style.maskRepeat = ''; b.el.style.maskComposite = '';
          b.el.style.webkitMaskSize = ''; b.el.style.webkitMaskPosition = ''; b.el.style.webkitMaskRepeat = ''; b.el.style.webkitMaskComposite = '';
        }
        b.tl.seek(local);
        b.fx.forEach(f => f.seek(local));
        const cam = b.spec.camera || {};
        const cpush = Number(cam.push || 0), cpan = cam.pan || [0, 0];
        if (cpush || cpan[0] || cpan[1]) {
          const cp = Math.min(1, Math.max(0, local / Math.max(0.001, b.spec.duration)));
          const eased = 1 - Math.pow(1 - cp, 3);
          b.cam.style.transform = `translate(${cpan[0] * eased * 100}%, ${cpan[1] * eased * 100}%) scale(${1 + cpush * eased})`;
        }
      });
      transitions.forEach(t => {
        const active = time >= t.end - t.dur && time < t.end;
        if (active) {
          t.outEl.classList.add('on'); t.inEl.classList.add('on');
          transitionStyle(t.key, t.outEl, t.inEl, clamp((time - (t.end - t.dur)) / t.dur, 0, 1));
        } else if (time >= t.end && time < t.end + 0.05) {
          transitionReset(t.outEl, t.inEl);
        }
      });
    }, 'none');
    master.seek(0);

    window.__timelines = window.__timelines || {};
    window.__timelines[filmSpec.productionId || 'product-film'] = master;
    window.seekComposition = t => master.seek(t);
    return master;
  }

  return { scenes, start, icon, markTile };
})();
