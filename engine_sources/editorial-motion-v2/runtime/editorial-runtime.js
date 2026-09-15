/*
 * Editorial Motion v2 runtime — EXECUTION ONLY.
 *
 * Consumes a NexStudioEditorialPlanV2 (one aspect) and renders it as a
 * deterministic, seekable DOM stage. Every visual state is a pure function of
 * the plan and a time in milliseconds: there are no tweens, timers or
 * accumulating animations, so frame N is identical whether reached by seeking
 * or by playing. The runtime never reads narration, never picks copy, layouts,
 * motifs, figures or media, and never falls back to a house behaviour: what the
 * compiler did not author is not drawn.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.EditorialRuntime = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const RUNTIME_VERSION = 'EDITORIAL_RUNTIME_V2.0';
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const prog = (t, s, e) => (e <= s ? (t >= e ? 1 : 0) : clamp((t - s) / (e - s), 0, 1));

  const EASE = {
    outCubic: (t) => 1 - Math.pow(1 - t, 3),
    outQuint: (t) => 1 - Math.pow(1 - t, 5),
    outExpo: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
    inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    inCubic: (t) => t * t * t,
    // Over-shoot then settle: the "elite AE" landing. Peaks ~1.035 at t≈0.55.
    settle: (t) => 1 + 2.7 * Math.pow(t - 1, 3) + 1.7 * Math.pow(t - 1, 2),
    // Single pulse 0→1→0 with a fast attack and slower release.
    pulse: (t) => (t < 0.32 ? EASE.outCubic(t / 0.32) : 1 - EASE.inOutCubic((t - 0.32) / 0.68)),
  };

  const WEIGHT = { Thin: 100, ExtraLight: 200, Light: 300, Regular: 400, Medium: 500, SemiBold: 600, Bold: 700, ExtraBold: 800, Black: 900 };
  const REVEAL_EVENTS = new Set(['DECISIVE_SLIDE', 'MASK_REVEAL', 'FADE_SCALE_SETTLE', 'LINE_STAGGER', 'PHRASE_REPLACE', 'KEYWORD_HIT', 'HOLD_AND_WIPE']);

  function bboxOf(b) {
    return { x: +b.x, y: +b.y, w: +b.w, h: +b.h };
  }

  function el(tag, style, parent) {
    const node = document.createElement(tag);
    if (style) Object.assign(node.style, style);
    if (parent) parent.appendChild(node);
    return node;
  }

  function px(v) {
    return `${Math.round(v * 100) / 100}px`;
  }

  // ---------------------------------------------------------------------------
  // Fonts
  // ---------------------------------------------------------------------------
  function installFonts(plan, fontBase) {
    const id = 'em2-fonts';
    if (document.getElementById(id)) return;
    const f = plan.fonts;
    const css = `
@font-face{font-family:"${f.families.display}";src:url("${fontBase}${f.display.file}") format("woff2");font-weight:100 900;font-style:normal;font-display:block}
@font-face{font-family:"${f.families.display}";src:url("${fontBase}${f.display_italic.file}") format("woff2");font-weight:100 900;font-style:italic;font-display:block}
@font-face{font-family:"${f.families.text}";src:url("${fontBase}${f.display.file}") format("woff2");font-weight:100 900;font-style:normal;font-display:block}
@font-face{font-family:"${f.families.text}";src:url("${fontBase}${f.display_italic.file}") format("woff2");font-weight:100 900;font-style:italic;font-display:block}
@font-face{font-family:"${f.families.data}";src:url("${fontBase}${f.data.file}") format("truetype");font-weight:600;font-display:block}
.em2-stage,.em2-stage *{box-sizing:border-box;margin:0;padding:0}
.em2-stage{position:relative;overflow:hidden;contain:strict;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
.em2-beat{position:absolute;inset:0}
.em2-line{white-space:nowrap;display:block}
`;
    const style = document.createElement('style');
    style.id = id;
    style.textContent = css;
    document.head.appendChild(style);
  }

  function fontsReady(plan) {
    if (!document.fonts || !document.fonts.load) return Promise.resolve();
    const f = plan.fonts.families;
    return Promise.all([
      document.fonts.load(`900 40px "${f.display}"`),
      document.fonts.load(`italic 600 40px "${f.display}"`),
      document.fonts.load(`600 40px "${f.data}"`),
    ]).then(() => document.fonts.ready);
  }

  // ---------------------------------------------------------------------------
  // Text blocks
  // ---------------------------------------------------------------------------
  function buildTextBlock(block, plan, beatRoot) {
    const fit = block.fit;
    const bb = bboxOf(block.bbox);
    const brand = plan.brand;
    const fam = block.style === 'column_line' && block.role === 'support' ? plan.fonts.families.text : plan.fonts.families.display;
    const isLabel = block.style === 'black_label';
    const wrap = el('div', {
      position: 'absolute', left: px(bb.x), top: px(bb.y), width: px(bb.w), height: px(bb.h),
      zIndex: String(block.z || 20), willChange: 'transform, clip-path, opacity',
      transformOrigin: block.alignment === 'right' ? '100% 100%' : block.alignment === 'center' ? '50% 50%' : '0% 100%',
    }, beatRoot);
    wrap.className = 'em2-block';
    wrap.dataset.unit = String(block.unit_index);
    wrap.dataset.style = block.style;
    const plate = el('div', {
      position: 'absolute', inset: '0', background: brand.ink, transformOrigin: '0% 50%', display: isLabel ? 'block' : 'none',
    }, wrap);
    const text = el('div', {
      position: 'absolute', left: '0', right: '0', top: '50%', transform: 'translateY(-50%)',
      fontFamily: `"${fam}"`, fontSize: px(fit.font_px), lineHeight: String(fit.line_height),
      letterSpacing: `${fit.tracking_em}em`, fontWeight: String(WEIGHT[block.weight] || 800),
      fontStyle: block.italic ? 'italic' : 'normal', color: brand.ink,
      textAlign: block.alignment || 'left', padding: isLabel ? `0 ${px(fit.font_px * 0.28)}` : '0',
    }, wrap);
    const lines = fit.lines.map((l) => {
      const line = el('span', { position: 'relative', willChange: 'transform, clip-path, opacity' }, text);
      line.className = 'em2-line';
      line.textContent = l;
      return line;
    });
    return { block, wrap, plate, text, lines, bb };
  }

  function lineStagger(p, i, n, spread) {
    // Each line owns a slice of the event; slice starts are spread across `spread` of the event.
    if (n <= 1) return p;
    const start = (i / n) * spread;
    return clamp((p - start) / (1 - spread + spread / n), 0, 1);
  }

  function applyTextState(node, lt, beat, ctx) {
    const b = node.block;
    const i = b.unit_index;
    const events = beat.typography.events.filter((e) => e.unit_index === i && REVEAL_EVENTS.has(e.event));
    const perf = beat.typography.performance_events;
    const enter = events.find((e) => e.event !== 'KEYWORD_HIT') || events[0];
    const w = node.wrap.style;
    if (!enter || lt < enter.start_ms) {
      w.visibility = 'hidden';
      return;
    }
    w.visibility = 'visible';
    let opacity = 1, tx = 0, ty = 0, scale = 1, rot = 0, wght = WEIGHT[b.weight] || 800;
    let clip = null; // [top,right,bottom,left] in %
    const em = b.fit.font_px;
    const dirSign = b.alignment === 'right' ? 1 : -1;
    const lineStates = node.lines.map(() => ({ ty: 0, op: 1, clip: null }));

    // --- entry
    const pe = prog(lt, enter.start_ms, enter.end_ms);
    switch (enter.event) {
      case 'DECISIVE_SLIDE': {
        const p = EASE.outQuint(pe);
        tx = dirSign * (1 - p) * node.bb.w * 0.07;
        clip = b.alignment === 'right' ? [0, 0, 0, (1 - EASE.outExpo(pe)) * 100] : [0, (1 - EASE.outExpo(pe)) * 100, 0, 0];
        break;
      }
      case 'MASK_REVEAL':
        node.lines.forEach((_, li) => {
          const pl = EASE.outQuint(lineStagger(pe, li, node.lines.length, 0.45));
          lineStates[li].clip = [0, 0, (1 - pl) * 100, 0];
          lineStates[li].ty = (1 - pl) * em * 0.38;
        });
        break;
      case 'LINE_STAGGER':
        node.lines.forEach((_, li) => {
          const pl = EASE.outCubic(lineStagger(pe, li, node.lines.length, 0.55));
          lineStates[li].op = pl;
          lineStates[li].ty = (1 - pl) * em * 0.32;
        });
        break;
      case 'PHRASE_REPLACE': {
        const p = EASE.outQuint(pe);
        clip = [0, 0, (1 - p) * 100, 0];
        ty = (1 - p) * em * 0.55;
        break;
      }
      case 'HOLD_AND_WIPE':
      case 'KEYWORD_HIT':
      case 'FADE_SCALE_SETTLE':
      default: {
        const p = EASE.outCubic(pe);
        opacity = p;
        scale *= lerp(0.965, 1, p);
        ty = (1 - p) * em * 0.16;
      }
    }

    // --- keyword hits: a punch after the landing, weight and scale together.
    for (const e of events) {
      if (e.event !== 'KEYWORD_HIT' || e === enter) continue;
      if (lt >= e.start_ms && lt <= e.end_ms) {
        const k = EASE.pulse(prog(lt, e.start_ms, e.end_ms)) * e.strength;
        scale *= 1 + 0.055 * k;
        wght = Math.min(900, wght + 90 * k);
      }
    }

    // --- performance events
    for (const e of perf) {
      if (e.unit_index !== i && e.unit_index !== -1) continue;
      const p = prog(lt, e.start_ms, e.end_ms);
      if (e.event === 'WORD_PROMOTION' && e.unit_index === i) {
        const s = lerp(0.52, 1, EASE.settle(p));
        scale *= lt < e.start_ms ? 0.52 : s;
      } else if (e.event === 'SPATIAL_RECONFIGURE') {
        const pre = ctx.reconfigureOffset(node);
        const k = 1 - EASE.inOutCubic(p);
        tx += pre.x * k;
        ty += pre.y * k;
      } else if (e.event === 'LABEL_INVERT' && e.unit_index === i) {
        const k = EASE.outExpo(p);
        node.plate.style.transform = `scaleX(${k.toFixed(4)})`;
        node.text.style.color = k > 0.5 ? ctx.brand.paper : ctx.brand.ink;
        node.plate.style.display = 'block';
      } else if (e.event === 'SUPPORT_ITALIC_DRIFT' && b.role === 'support' && b.italic) {
        const k = 1 - EASE.outCubic(p);
        tx += -em * 0.35 * k;
        rot = (e.tilt_deg || 0) * k;
      }
    }
    if (b.style === 'black_label' && !perf.some((e) => e.event === 'LABEL_INVERT' && e.unit_index === i)) {
      node.text.style.color = ctx.brand.paper;
    }

    // --- replace-stage exit: stage A leaves upward as stage B rises.
    if (typeof b.exit_ms === 'number' && lt >= b.exit_ms) {
      const p = EASE.inCubic(prog(lt, b.exit_ms, b.exit_ms + 300));
      clip = [p * 100, 0, 0, 0];
      ty -= p * em * 0.5;
      if (p >= 1) opacity = 0;
    }

    // --- beat exit / transition carrier
    const ex = ctx.exitState(node, lt);
    if (ex) {
      opacity *= ex.opacity;
      tx += ex.tx;
      ty += ex.ty;
      if (ex.clip) clip = ex.clip;
      if (ex.scale) scale *= ex.scale;
    }

    w.opacity = opacity.toFixed(4);
    w.transform = `translate(${tx.toFixed(2)}px, ${ty.toFixed(2)}px) rotate(${rot.toFixed(3)}deg) scale(${scale.toFixed(4)})`;
    w.clipPath = clip ? `inset(${clip.map((v) => `${clamp(v, 0, 100).toFixed(2)}%`).join(' ')})` : 'none';
    node.text.style.fontVariationSettings = `"wght" ${Math.round(wght)}, "opsz" ${b.role === 'hero' ? 32 : 20}`;
    node.lines.forEach((line, li) => {
      const s = lineStates[li];
      line.style.opacity = s.op.toFixed(4);
      line.style.transform = s.ty ? `translateY(${s.ty.toFixed(2)}px)` : 'none';
      line.style.clipPath = s.clip ? `inset(${s.clip.map((v) => `${clamp(v, 0, 100).toFixed(2)}%`).join(' ')})` : 'none';
    });
  }

  // ---------------------------------------------------------------------------
  // Background
  // ---------------------------------------------------------------------------
  function buildBackground(beat, plan, beatRoot) {
    const bg = beat.composition.background || {};
    const brand = plan.brand;
    const layer = el('div', { position: 'absolute', inset: '0', zIndex: '1', background: brand.paper }, beatRoot);
    let stage = null;
    if (bg.render === 'CARD_STAGE' && bg.stage) {
      const s = bboxOf(bg.stage);
      stage = el('div', {
        position: 'absolute', left: px(s.x), top: px(s.y), width: px(s.w), height: px(s.h),
        background: 'rgba(14,14,14,0.035)', borderRadius: px(Math.min(s.w, s.h) * 0.03),
        transformOrigin: '50% 60%',
      }, layer);
    } else if (bg.render === 'SPOTLIGHT_STAGE' && bg.stage) {
      const s = bboxOf(bg.stage);
      const cx = s.x + s.w / 2, cy = s.y + s.h * 0.62;
      stage = el('div', {
        position: 'absolute', inset: '0',
        background: `radial-gradient(ellipse ${px(s.w * 1.05)} ${px(s.h * 0.9)} at ${px(cx)} ${px(cy)}, rgba(14,14,14,0.055), rgba(14,14,14,0) 70%)`,
        transformOrigin: `${px(cx)} ${px(cy)}`,
      }, layer);
    } else {
      // SOFT_FIELD: a barely-there vignette so the paper reads as a surface, not a void.
      el('div', {
        position: 'absolute', inset: '0',
        background: 'radial-gradient(ellipse 85% 80% at 50% 45%, rgba(14,14,14,0) 55%, rgba(14,14,14,0.03) 100%)',
      }, layer);
    }
    return { layer, stage };
  }

  function applyBackgroundState(bgNode, lt, beat) {
    if (!bgNode.stage) return;
    const settle = beat.ensemble.events.find((e) => e.channel === 'BACKGROUND' && e.event === 'STAGE_SETTLE');
    let p = 1;
    if (settle) p = EASE.outCubic(prog(lt, settle.start_ms, settle.end_ms));
    bgNode.stage.style.opacity = p.toFixed(4);
    bgNode.stage.style.transform = `scale(${lerp(0.985, 1, p).toFixed(4)})`;
  }

  // ---------------------------------------------------------------------------
  // Media (customer-supplied image / video evidence)
  // ---------------------------------------------------------------------------
  function buildMedia(media, plan, beatRoot, assetUrl) {
    const bb = bboxOf(media.bbox);
    const brand = plan.brand;
    const frame = el('div', {
      position: 'absolute', left: px(bb.x), top: px(bb.y), width: px(bb.w), height: px(bb.h), zIndex: '12',
      overflow: 'hidden', borderRadius: px(Math.min(bb.w, bb.h) * 0.035), border: `2px solid ${brand.ink}`,
      background: brand.paper, willChange: 'transform, opacity, clip-path',
    }, beatRoot);
    let node;
    if (media.kind === 'VIDEO') {
      node = document.createElement('video');
      node.muted = true;
      node.playsInline = true;
      node.preload = 'auto';
      node.src = assetUrl(media.path);
    } else {
      node = document.createElement('img');
      node.decoding = 'sync';
      node.src = assetUrl(media.path);
    }
    Object.assign(node.style, { position: 'absolute', left: '0', top: '0', width: '100%', height: '100%', objectFit: 'cover', display: 'block' });
    frame.appendChild(node);
    const m = { media, frame, node, bb, pending: null };
    layoutFocus(m, bb.w, bb.h);
    return m;
  }

  // Focus crop: the authored source region covers the frame without distortion; overflow is centred.
  function layoutFocus(m, fw, fh) {
    const md = m.media;
    if (!md.focus || !md.source_size) return;
    const f = md.focus, sw = md.source_size.w, sh = md.source_size.h;
    const scale = Math.max(fw / (f.w * sw), fh / (f.h * sh));
    const w = sw * scale, h = sh * scale;
    const left = -f.x * w - (f.w * w - fw) / 2;
    const top = -f.y * h - (f.h * h - fh) / 2;
    Object.assign(m.node.style, { objectFit: 'fill', width: px(w), height: px(h), left: px(left), top: px(top) });
  }

  function applyMediaState(m, lt, beat, ctx) {
    const md = m.media;
    const s = m.frame.style;
    if (lt < md.enter_ms) {
      s.visibility = 'hidden';
      return;
    }
    s.visibility = 'visible';
    let tx = 0, ty = 0, opacity = 1, clip = null, scale = 1;
    const p = EASE.outQuint(prog(lt, md.enter_ms, md.enter_ms + md.enter_duration_ms));
    if (md.enter_duration_ms > 0) {
      ty = (1 - p) * m.bb.h * 0.08;
      clip = [0, 0, (1 - p) * 100, 0];
      opacity = Math.min(1, p * 1.6);
    }
    if (md.reframe) {
      const rp = EASE.inOutCubic(prog(lt, md.reframe.start_ms, md.reframe.end_ms));
      const from = bboxOf(md.reframe.from);
      const x = lerp(from.x, m.bb.x, rp), y = lerp(from.y, m.bb.y, rp);
      const w = lerp(from.w, m.bb.w, rp), h = lerp(from.h, m.bb.h, rp);
      s.left = px(x); s.top = px(y); s.width = px(w); s.height = px(h);
      layoutFocus(m, w, h);
    }
    const ex = ctx.exitState({ block: { role: 'media' } }, lt);
    if (ex) { opacity *= ex.opacity; ty += ex.ty; }
    s.opacity = opacity.toFixed(4);
    s.transform = `translate(${tx.toFixed(2)}px, ${ty.toFixed(2)}px) scale(${scale.toFixed(4)})`;
    s.clipPath = clip ? `inset(${clip.map((v) => `${clamp(v, 0, 100).toFixed(2)}%`).join(' ')})` : 'none';
    if (md.kind === 'VIDEO') {
      const trim = md.trim || { start: 0, end: 1e9 };
      const local = (lt - md.enter_ms) / 1000;
      const target = clamp(trim.start + local, trim.start, trim.end - 0.001);
      if (Math.abs((m.node.currentTime || 0) - target) > 1 / 120) {
        m.pending = new Promise((resolve) => {
          const done = () => { m.node.removeEventListener('seeked', done); resolve(); };
          m.node.addEventListener('seeked', done);
          m.node.currentTime = target;
        });
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Still Open Peeps figure
  // ---------------------------------------------------------------------------
  const svgCache = new Map();
  function fetchText(url) {
    if (!svgCache.has(url)) svgCache.set(url, fetch(url).then((r) => { if (!r.ok) throw new Error(`figure part ${url}: ${r.status}`); return r.text(); }));
    return svgCache.get(url);
  }

  function recolor(svgText, palette) {
    let out = svgText;
    for (const [from, to] of Object.entries(palette || {})) {
      out = out.split(from).join(to).split(from.toUpperCase()).join(to);
    }
    return out;
  }

  function buildFigure(fig, plan, beatRoot, peepsUrl) {
    const bb = bboxOf(fig.bbox);
    const host = el('div', {
      position: 'absolute', left: px(bb.x), top: px(bb.y), width: px(bb.w), height: px(bb.h), zIndex: '14',
      willChange: 'transform, opacity', transformOrigin: '50% 100%',
    }, beatRoot);
    const vb = fig.composition.view_box;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', vb.join(' '));
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('preserveAspectRatio', 'xMidYMax meet');
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    if (fig.mirror) g.setAttribute('transform', `translate(${vb[0] * 2 + vb[2]} 0) scale(-1 1)`);
    svg.appendChild(g);
    host.appendChild(svg);
    const ready = Promise.all(fig.parts.map((part) => fetchText(peepsUrl(part.file)).then((txt) => {
      const doc = new DOMParser().parseFromString(recolor(txt, fig.palette), 'image/svg+xml');
      const src = doc.documentElement;
      const vbSrc = (src.getAttribute('viewBox') || `0 0 ${part.source_size.w} ${part.source_size.h}`).split(/[\s,]+/).map(Number);
      const nested = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const sx = part.frame.w / vbSrc[2], sy = part.frame.h / vbSrc[3];
      nested.setAttribute('transform', `translate(${part.frame.x} ${part.frame.y}) scale(${sx.toFixed(5)} ${sy.toFixed(5)}) translate(${-vbSrc[0]} ${-vbSrc[1]})`);
      nested.setAttribute('data-slot', part.slot);
      nested.innerHTML = src.innerHTML;
      return { part, nested };
    }))).then((items) => {
      // Slot order is authored by the compiler: body → head → face.
      for (const it of items) g.appendChild(it.nested);
    });
    return { fig, host, bb, ready };
  }

  function applyFigureState(f, lt, beat, ctx) {
    const fig = f.fig;
    const s = f.host.style;
    if (lt < fig.enter_ms) { s.visibility = 'hidden'; return; }
    s.visibility = 'visible';
    const p = EASE.outQuint(prog(lt, fig.enter_ms, fig.enter_ms + fig.enter_duration_ms));
    let opacity = p, ty = (1 - p) * f.bb.h * 0.05, scale = lerp(0.985, 1, p);
    const ex = ctx.exitState({ block: { role: 'figure' } }, lt);
    if (ex) { opacity *= ex.opacity; ty += ex.ty; }
    s.opacity = opacity.toFixed(4);
    s.transform = `translateY(${ty.toFixed(2)}px) scale(${scale.toFixed(4)})`;
  }

  // ---------------------------------------------------------------------------
  // Data (numbers rendered as typography, not charts)
  // ---------------------------------------------------------------------------
  function buildData(data, plan, beatRoot) {
    const brand = plan.brand;
    const blocks = data.blocks.map((blk) => {
      const bb = bboxOf(blk.bbox);
      const isValue = blk.role === 'value';
      const wrap = el('div', {
        position: 'absolute', left: px(bb.x), top: px(bb.y), width: px(bb.w), height: px(bb.h), zIndex: '16',
        willChange: 'transform, opacity, clip-path', transformOrigin: '50% 100%',
      }, beatRoot);
      const text = el('div', {
        position: 'absolute', left: '0', right: '0', top: '50%', transform: 'translateY(-50%)',
        fontFamily: `"${isValue ? plan.fonts.families.data : plan.fonts.families.display}"`,
        fontSize: px(blk.fit.font_px), lineHeight: String(blk.fit.line_height), letterSpacing: `${blk.fit.tracking_em}em`,
        fontWeight: isValue ? '600' : '500', color: brand.ink, textAlign: 'center', whiteSpace: 'nowrap',
        fontStyle: blk.role === 'label' ? 'italic' : 'normal',
      }, wrap);
      text.textContent = blk.fit.lines.join('\n');
      return { blk, wrap, bb };
    });
    let rule = null;
    if (data.kind === 'COMPARISON') {
      const z = bboxOf(data.zone);
      rule = el('div', {
        position: 'absolute', left: px(z.x + z.w / 2 - 1), top: px(z.y + z.h * 0.08), width: '2px', height: px(z.h * 0.55),
        background: brand.ink, zIndex: '15', transformOrigin: '50% 0%', opacity: '0.35',
      }, beatRoot);
    }
    return { data, blocks, rule };
  }

  function applyDataState(d, lt, beat, ctx) {
    const data = d.data;
    d.blocks.forEach((b, idx) => {
      const order = b.blk.role === 'label' ? d.blocks.length - 1 : (b.blk.side || 0);
      const start = data.enter_ms + order * (data.stagger_ms || 0);
      const s = b.wrap.style;
      if (lt < start) { s.visibility = 'hidden'; return; }
      s.visibility = 'visible';
      const p = prog(lt, start, start + data.enter_duration_ms);
      let opacity = EASE.outCubic(p), ty = (1 - EASE.outQuint(p)) * b.bb.h * 0.12, scale = EASE.settle(p);
      if (b.blk.role === 'label') scale = 1;
      const ex = ctx.exitState({ block: { role: 'data' } }, lt);
      if (ex) { opacity *= ex.opacity; ty += ex.ty; }
      s.opacity = opacity.toFixed(4);
      s.transform = `translateY(${ty.toFixed(2)}px) scale(${scale.toFixed(4)})`;
    });
    if (d.rule) {
      const p = EASE.outQuint(prog(lt, data.enter_ms, data.enter_ms + data.enter_duration_ms));
      d.rule.style.transform = `scaleY(${p.toFixed(4)})`;
      d.rule.style.visibility = lt < data.enter_ms ? 'hidden' : 'visible';
    }
  }

  // ---------------------------------------------------------------------------
  // Beat
  // ---------------------------------------------------------------------------
  function buildBeat(beat, plan, stage, opts, isLast) {
    const root = el('div', { display: 'none', position: 'absolute', inset: '0', overflow: 'hidden' }, stage);
    root.className = 'em2-beat';
    root.dataset.beat = beat.beat_id;
    const bg = buildBackground(beat, plan, root);
    const media = beat.media ? buildMedia(beat.media, plan, root, opts.assetUrl) : null;
    const figure = beat.figure ? buildFigure(beat.figure, plan, root, opts.peepsUrl) : null;
    const data = beat.data ? buildData(beat.data, plan, root) : null;
    const texts = beat.typography.blocks.map((b) => buildTextBlock(b, plan, root));
    const tz = bboxOf(beat.composition.text_zone);
    const tr = beat.transition || { mode: 'SETTLE_CUT' };
    const carrierIndex = (() => {
      if (tr.mode === 'LABEL_EXPAND_WIPE') {
        const lab = beat.typography.blocks.find((b) => b.style === 'black_label');
        if (lab) return lab.unit_index;
      }
      if (typeof tr.unit_index === 'number') return tr.unit_index;
      const fo = beat.typography.focal_order || [];
      return fo.length ? fo[0] : -1;
    })();

    const ctx = {
      brand: plan.brand,
      reconfigureOffset(node) {
        // Pre-reconfiguration state: blocks sit 30% closer to the text-zone centre along their dominant axis.
        const cx = tz.x + tz.w / 2, cy = tz.y + tz.h / 2;
        const bx = node.bb.x + node.bb.w / 2, by = node.bb.y + node.bb.h / 2;
        const dx = cx - bx, dy = cy - by;
        return Math.abs(dx) / tz.w >= Math.abs(dy) / tz.h ? { x: dx * 0.3, y: 0 } : { x: 0, y: dy * 0.3 };
      },
      exitState(node, lt) {
        if (isLast || lt < tr.start_ms) return null;
        const p = prog(lt, tr.start_ms, tr.end_ms);
        const role = node.block.role;
        if (tr.mode === 'SETTLE_CUT') return null; // the settled state is held; the cut is the transition
        if (tr.mode === 'EVIDENCE_PERSISTENCE') {
          // Text leaves, media stays for the next beat to inherit.
          if (role === 'media') return null;
          const k = EASE.inCubic(p);
          return { opacity: 1 - k, tx: 0, ty: -k * 14 };
        }
        if (tr.mode === 'TEXT_MASK_WIPE') {
          if (node.block.unit_index === carrierIndex) {
            const k = EASE.inOutCubic(p);
            return { opacity: 1, tx: 0, ty: 0, clip: [0, 0, 0, k * 100] };
          }
          const k = EASE.inCubic(clamp(p * 1.5, 0, 1));
          return { opacity: 1 - k, tx: 0, ty: -k * 10 };
        }
        if (tr.mode === 'LABEL_EXPAND_WIPE') {
          if (node.block.unit_index === carrierIndex) {
            const k = EASE.inOutCubic(p);
            return { opacity: 1, tx: 0, ty: 0, scale: lerp(1, 6, k) };
          }
          const k = EASE.inCubic(clamp(p * 1.6, 0, 1));
          return { opacity: 1 - k, tx: 0, ty: 0 };
        }
        return null;
      },
    };
    const ready = Promise.all([figure ? figure.ready : null, media ? mediaReady(media) : null]);
    return { beat, root, bg, media, figure, data, texts, ctx, ready };
  }

  function mediaReady(m) {
    return new Promise((resolve, reject) => {
      const n = m.node;
      if (n.tagName === 'IMG') {
        if (n.complete && n.naturalWidth) return resolve();
        n.onload = () => resolve();
        n.onerror = () => reject(new Error(`media failed: ${m.media.asset_id}`));
      } else {
        if (n.readyState >= 2) return resolve();
        n.onloadeddata = () => resolve();
        n.onerror = () => reject(new Error(`media failed: ${m.media.asset_id}`));
      }
    });
  }

  function applyBeat(bn, lt) {
    applyBackgroundState(bn.bg, lt, bn.beat);
    if (bn.media) applyMediaState(bn.media, lt, bn.beat, bn.ctx);
    if (bn.figure) applyFigureState(bn.figure, lt, bn.beat, bn.ctx);
    if (bn.data) applyDataState(bn.data, lt, bn.beat, bn.ctx);
    for (const t of bn.texts) applyTextState(t, lt, bn.beat, bn.ctx);
  }

  // ---------------------------------------------------------------------------
  // Film
  // ---------------------------------------------------------------------------
  function createEditorialFilm(plan, mount, options) {
    if (!plan || plan.schema !== 'NexStudioEditorialPlanV2') throw new Error('EditorialRuntime: plan must be NexStudioEditorialPlanV2');
    if (plan.gate && plan.gate.status !== 'PASS') throw new Error(`EditorialRuntime: refusing to render a plan whose gate is ${plan.gate.status}`);
    const opts = Object.assign({
      fontBase: '../assets/fonts/',
      peepsBase: '../assets/peeps/',
      assetUrl: (p) => p,
    }, options || {});
    opts.peepsUrl = opts.peepsUrl || ((file) => opts.peepsBase + file);
    installFonts(plan, opts.fontBase);

    const W = plan.canvas.w, H = plan.canvas.h;
    const stage = el('div', { position: 'relative', overflow: 'hidden', width: px(W), height: px(H), background: plan.brand.paper, color: plan.brand.ink }, mount);
    stage.className = 'em2-stage';
    stage.dataset.aspect = plan.aspect;

    const beats = plan.beats.map((b, i) => buildBeat(b, plan, stage, opts, i === plan.beats.length - 1));
    const duration = plan.duration_ms;
    let current = -1;
    let time = 0;
    let playing = false;
    let raf = 0;
    let t0 = 0;

    function beatAt(ms) {
      for (let i = beats.length - 1; i >= 0; i -= 1) if (ms >= beats[i].beat.start_ms) return i;
      return 0;
    }

    function seek(ms) {
      time = clamp(ms, 0, duration);
      const idx = beatAt(time);
      if (idx !== current) {
        // display, not visibility: children set their own visibility and would otherwise leak through.
        beats.forEach((bn, i) => { bn.root.style.display = i === idx ? 'block' : 'none'; });
        current = idx;
      }
      const bn = beats[idx];
      applyBeat(bn, time - bn.beat.start_ms);
      const waits = [];
      if (bn.media && bn.media.pending) waits.push(bn.media.pending);
      return Promise.all(waits).then(() => undefined);
    }

    function frame(n) { return seek(Math.round((n * 1000) / plan.fps)); }

    function tick(now) {
      if (!playing) return;
      const t = now - t0;
      seek(t);
      if (t >= duration) { playing = false; return; }
      raf = requestAnimationFrame(tick);
    }
    function play(from) {
      if (typeof from === 'number') time = clamp(from, 0, duration);
      t0 = performance.now() - time;
      playing = true;
      raf = requestAnimationFrame(tick);
    }
    function pause() { playing = false; cancelAnimationFrame(raf); }

    function fit(container) {
      const cw = container.clientWidth, ch = container.clientHeight;
      const s = Math.min(cw / W, ch / H);
      stage.style.transformOrigin = '0 0';
      stage.style.transform = `scale(${s})`;
      stage.style.position = 'absolute';
      stage.style.left = px((cw - W * s) / 2);
      stage.style.top = px((ch - H * s) / 2);
      return s;
    }

    const ready = Promise.all([fontsReady(plan)].concat(beats.map((b) => b.ready))).then(() => seek(0));
    seek(0);

    return {
      version: RUNTIME_VERSION,
      plan, stage, duration, fps: plan.fps, frames: Math.ceil((duration * plan.fps) / 1000),
      seek, frame, play, pause, fit, ready,
      get time() { return time; },
      get playing() { return playing; },
      captions: plan.captions,
      audioEvents() {
        // Everything the mixer needs, flattened: voice segments, semantic accents, music slot.
        const accents = [];
        for (const b of plan.beats) for (const a of b.sound.accents) accents.push(a);
        return { voice: plan.voice, accents, music: plan.music };
      },
    };
  }

  return { createEditorialFilm, RUNTIME_VERSION, EASE, _internals: { prog, lineStagger, recolor } };
});
