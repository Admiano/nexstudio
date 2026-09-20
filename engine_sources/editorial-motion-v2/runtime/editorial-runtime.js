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

  const RUNTIME_VERSION = 'EDITORIAL_RUNTIME_V3.0';
  const STRESS_SCALE = 1.045; // mirrors typefit.STRESS_SCALE: the compiler reserves this width for stressed words
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const prog = (t, s, e) => (e <= s ? (t >= e ? 1 : 0) : clamp((t - s) / (e - s), 0, 1));

  const DEFAULT_MOTION = { entrance: 'settle', stagger_ms: 90, camera_push: 0, camera_pan_frac: 0, transition: 'blur_dissolve', blur_px: 0, word_landing: 'tonal' };

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

  // Role eases from the vendored easing vocabulary (assets/community/easings.json), evaluated as
  // cubic-bezier solvers: entries decelerate hard, exits accelerate away, wipes are symmetric.
  function cubicBezier(x1, y1, x2, y2) {
    const ax = 3 * x1 - 3 * x2 + 1, bx = 3 * x2 - 6 * x1, cx = 3 * x1;
    const ay = 3 * y1 - 3 * y2 + 1, by = 3 * y2 - 6 * y1, cy = 3 * y1;
    const xs = (t) => ((ax * t + bx) * t + cx) * t;
    const ys = (t) => ((ay * t + by) * t + cy) * t;
    const dxs = (t) => (3 * ax * t + 2 * bx) * t + cx;
    return (x) => {
      let t = x, lo = 0, hi = 1;
      for (let i = 0; i < 6; i += 1) {
        const err = xs(t) - x, d = dxs(t);
        if (Math.abs(err) < 1e-6 || Math.abs(d) < 1e-7) break;
        t -= err / d;
      }
      for (let i = 0; i < 24 && Math.abs(xs(t) - x) > 1e-6; i += 1) {
        if (xs(t) < x) lo = t; else hi = t;
        t = (lo + hi) / 2;
      }
      return ys(clamp(t, 0, 1));
    };
  }
  EASE.enter = cubicBezier(0.16, 1, 0.3, 1);        // easeOutExpo
  EASE.exit = cubicBezier(0.64, 0, 0.78, 0);        // easeInQuint
  EASE.emphasize = cubicBezier(0.34, 1.56, 0.64, 1); // easeOutBack — controlled overshoot
  EASE.wipe = cubicBezier(0.76, 0, 0.24, 1);        // easeInOutQuart

  function hash01(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i += 1) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return h / 4294967295;
  }

  // Secondary motion: once a node's own program has settled it keeps a slow, tiny drift so holds
  // read as living stills rather than frozen frames. Pure function of lt — fully deterministic.
  function ambientDrift(lt, id, settledAt, amp) {
    const ramp = EASE.outCubic(prog(lt, settledAt, settledAt + 750));
    if (ramp <= 0) return { dx: 0, dy: 0, s: 1 };
    const ph = hash01(String(id)) * Math.PI * 2;
    const w = (Math.PI * 2) / 3800;
    return {
      dx: amp * ramp * Math.sin(lt * w + ph),
      dy: amp * 0.72 * ramp * Math.sin(lt * w * 1.31 + ph * 1.63),
      s: 1 + 0.006 * ramp * Math.sin(lt * w * 0.84 + ph * 0.53),
    };
  }

  // Velocity-proportional blur during fast moves — the illusion of shutter speed.
  function velocityBlur(lt, s, e, easeFn, distPx) {
    if (lt <= s || lt >= e) return 0;
    const dv = Math.abs(easeFn(prog(Math.min(e, lt + 40), s, e)) - easeFn(prog(lt, s, e)));
    return clamp(dv * distPx * 0.02, 0, 2.4);
  }

  function hexRgb(hex) {
    const m = /^#?([0-9a-f]{6})$/i.exec(String(hex).trim());
    return m ? [parseInt(m[1].slice(0, 2), 16), parseInt(m[1].slice(2, 4), 16), parseInt(m[1].slice(4, 6), 16)] : [0, 0, 0];
  }
  function mixColor(a, b, k) {
    const ca = hexRgb(a), cb = hexRgb(b);
    return `rgb(${Math.round(lerp(ca[0], cb[0], k))} ${Math.round(lerp(ca[1], cb[1], k))} ${Math.round(lerp(ca[2], cb[2], k))})`;
  }
  function rgbaOf(hex, alpha) {
    const c = hexRgb(hex);
    return `rgba(${c[0]},${c[1]},${c[2]},${alpha})`;
  }

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
    const cascade = block.reveal === 'WORD_CASCADE' && Array.isArray(block.words) && block.words.length > 0;
    const words = [];
    const lines = fit.lines.map((l, li) => {
      const line = el('span', { position: 'relative', willChange: 'transform, clip-path, opacity' }, text);
      line.className = 'em2-line';
      if (!cascade) { line.textContent = l; return line; }
      // Word cascade: each word is its own composited span so it can land on its voice timing.
      const lineWords = block.words.filter((w) => w.line === li);
      lineWords.forEach((w, wi) => {
        if (wi) line.appendChild(document.createTextNode(' '));
        const span = el('span', { display: 'inline-block', willChange: 'transform, opacity, filter', transformOrigin: '0% 85%' }, line);
        span.className = 'em2-word';
        span.textContent = w.text;
        if (w.stress) {
          // The compiler reserved this width: the stressed word is set larger for real, never scaled into the word space.
          span.dataset.stress = '1';
          span.style.fontSize = `${STRESS_SCALE}em`;
          span.style.lineHeight = String(fit.line_height / STRESS_SCALE);
          span.style.verticalAlign = 'baseline';
        }
        words.push({ w, span });
      });
      return line;
    });
    return { block, wrap, plate, text, lines, bb, words, cascade };
  }

  // One word landing: rises out of blur into focus and overshoots by a hair — weight, scale and opacity together.
  // While the unit is still being spoken, words already said fall back to the tonal ink so the current word carries;
  // once the cascade has ended every word returns to full ink. Stressed words never fall back.
  function applyWordState(item, lt, em, tonalInk, baseWght, promoted, nextStart, cascadeEnd, muteColor, landing) {
    const s = item.span.style;
    // 'rise' landing (collage finish): words climb further out of a softer blur and hold full ink once said.
    const rise = landing === 'rise' ? 0.9 : 0.42, blurPx = landing === 'rise' ? 4 : 6;
    const start = item.w.start_ms, dur = landing === 'rise' ? 300 : 260;
    const isStress = item.w.stress;
    // The stressed word is set larger and lands heavier and stays there: the emphasis is a state, not a flash.
    // Every word lands ~90 weight heavy on the variable axis and relaxes to its rest weight — kinetic ink.
    const swell = 90 * (1 - EASE.outCubic(prog(lt, start + dur, start + dur + 420)));
    const wght = Math.min(900, (isStress ? baseWght + 100 : baseWght) + swell);
    s.fontVariationSettings = `"wght" ${Math.round(wght)}`;
    // tone: 'mute' words read grey — the benchmark's mixed-tone lockup inside one sentence.
    s.color = item.w.tone === 'mute' ? muteColor : 'inherit';
    if (lt < start) { s.opacity = '0'; s.transform = `translateY(${f2(em * rise)}px) scale(0.96)`; s.filter = `blur(${blurPx}px)`; return; }
    const p = prog(lt, start, start + dur);
    const k = EASE.outQuint(p), st = EASE.settle(p);
    let scale = lerp(0.96, 1, st);
    const ty = (1 - k) * em * rise;
    if (isStress && promoted) scale *= lerp(1, 1.02, EASE.pulse(prog(lt, start, start + 520)));
    let opacity = Math.min(1, k * 1.25);
    if (!isStress && nextStart !== null && landing !== 'rise') {
      const tonal = lerp(1, tonalInk, EASE.inOutCubic(prog(lt, nextStart, nextStart + 220)));
      opacity = Math.min(opacity, lerp(tonal, 1, EASE.outCubic(prog(lt, cascadeEnd, cascadeEnd + 260))));
    }
    s.opacity = opacity.toFixed(4);
    s.transform = `translateY(${f2(ty)}px) scale(${scale.toFixed(4)})`;
    s.filter = p >= 1 ? 'none' : `blur(${f2((1 - k) * blurPx)}px)`;
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
    let enter = events.find((e) => e.event !== 'KEYWORD_HIT') || events[0];
    if (node.cascade) {
      // The block's reveal is its words: the block itself is simply present from the first landing.
      const first = node.words[0].w.start_ms;
      enter = { event: 'WORD_CASCADE', start_ms: first, end_ms: first };
    }
    const w = node.wrap.style;
    // Seek determinism: pre-entry still runs the whole pipeline at p=0 so every decl is
    // (re)written — an early return would leave stale styles behind after scrubbing back.
    const hidden = !enter || lt < enter.start_ms;
    w.visibility = hidden ? 'hidden' : 'visible';
    let opacity = 1, tx = 0, ty = 0, scale = 1, rot = 0, wght = WEIGHT[b.weight] || 800;
    let clip = null; // [top,right,bottom,left] in %
    const em = b.fit.font_px;
    const dirSign = b.alignment === 'right' ? 1 : -1;
    const lineStates = node.lines.map(() => ({ ty: 0, op: 1, clip: null }));

    // --- entry
    const pe = enter ? prog(lt, enter.start_ms, enter.end_ms) : 0;
    switch (enter && enter.event) {
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
      case 'WORD_CASCADE':
        break;
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

    // Velocity blur while the block travels: entry slide, exit rise, carrier wipes.
    let blur = enter && enter.end_ms > enter.start_ms ? velocityBlur(lt, enter.start_ms, enter.end_ms, EASE.enter, node.bb.w * 0.1 + em * 0.5) : 0;
    const tr = ctx.transition;
    if (tr && lt >= tr.start_ms) blur = Math.max(blur, velocityBlur(lt, tr.start_ms, tr.end_ms, EASE.exit, node.bb.h * 0.6));
    w.filter = blur > 0.15 ? `blur(${blur.toFixed(2)}px)` : '';

    // Hero copy breathes after its program settles — applied to the text node so block geometry never moves.
    if (b.role === 'hero') {
      const heroS = ambientDrift(lt, `hero-${i}`, (node.cascade ? (b.cascade_end_ms || 0) : (enter ? enter.end_ms : 0)) + 320, 0).s;
      node.text.style.transform = `translateY(-50%) scale(${heroS.toFixed(4)})`;
    }

    w.opacity = opacity.toFixed(4);
    w.transform = `translate(${tx.toFixed(2)}px, ${ty.toFixed(2)}px) rotate(${rot.toFixed(3)}deg) scale(${scale.toFixed(4)})`;
    w.clipPath = clip ? `inset(${clip.map((v) => `${clamp(v, 0, 100).toFixed(2)}%`).join(' ')})` : 'none';
    node.text.style.fontVariationSettings = `"wght" ${Math.round(wght)}, "opsz" ${b.role === 'hero' ? 32 : 20}`;
    if (node.cascade) {
      const promoted = perf.some((e) => e.event === 'WORD_PROMOTION' && e.unit_index === i);
      const end = b.cascade_end_ms || node.words[node.words.length - 1].w.start_ms + 260;
      const muteColor = rgbaOf(ctx.brand.ink, 0.5);
      node.words.forEach((item, wi) => applyWordState(item, lt, em, ctx.tonalInk, wght, promoted, wi + 1 < node.words.length ? node.words[wi + 1].w.start_ms : null, end, muteColor, ctx.motion.word_landing));
    }
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
  function buildBgLayer(spec, plan, parent, idx) {
    const brand = plan.brand;
    const W = plan.canvas.w, H = plan.canvas.h;
    const b = spec.bbox;
    let node = null;
    switch (spec.kind) {
      case 'panel': {
        const fill = spec.fill === 'paper_lift' ? mixColor(brand.paper, '#ffffff', 0.55) : brand.paper;
        node = el('div', {
          position: 'absolute', left: px(b.x), top: px(b.y), width: px(b.w), height: px(b.h),
          background: fill, borderRadius: px(Math.min(b.w, b.h) * (spec.radius_frac || 0.03)),
          transformOrigin: '50% 60%',
        }, parent);
        if (spec.shadow) {
          const blur = Math.min(W, H) * (spec.shadow.blur_frac || 0.02);
          const dy = H * (spec.shadow.dy_frac || 0.012);
          node.style.boxShadow = `0 ${px(dy)} ${px(blur)} ${rgbaOf(brand.ink, spec.shadow.opacity || 0.13)}`;
        }
        break;
      }
      case 'plane':
        node = el('div', {
          position: 'absolute', left: px(b.x), top: px(b.y), width: px(b.w), height: px(b.h),
          background: mixColor(brand.paper, '#ffffff', 0.4), border: `1px solid ${rgbaOf(brand.ink, 0.06)}`,
          borderRadius: px(Math.min(b.w, b.h) * 0.02), transformOrigin: '50% 50%',
        }, parent);
        break;
      case 'hairline':
        node = el('div', {
          position: 'absolute', left: px(b.x), top: px(b.y), width: px(b.w), height: px(b.h),
          border: `1px solid ${brand.ink}`, borderRadius: px(Math.min(b.w, b.h) * 0.02),
        }, parent);
        break;
      case 'dotgrid': {
        const spacing = Math.max(26, Math.min(W, H) * (spec.spacing_frac || 0.055));
        const r = Math.max(1.1, Math.min(W, H) * (spec.radius_frac || 0.0022));
        node = el('div', {
          position: 'absolute', left: px(b.x), top: px(b.y), width: px(b.w), height: px(b.h),
          backgroundImage: `radial-gradient(circle, ${rgbaOf(brand.ink, 0.14)} ${r.toFixed(2)}px, transparent ${(r + 0.6).toFixed(2)}px)`,
          backgroundSize: `${spacing.toFixed(2)}px ${spacing.toFixed(2)}px`,
          backgroundPosition: `${px(b.x)} ${px(b.y)}`,
        }, parent);
        break;
      }
      case 'spotlight': {
        const cx = b.x + b.w / 2, cy = b.y + b.h * 0.62;
        node = el('div', {
          position: 'absolute', inset: '0',
          background: `radial-gradient(ellipse ${px(b.w * 1.05)} ${px(b.h * 0.9)} at ${px(cx)} ${px(cy)}, ${rgbaOf(brand.ink, 0.06)}, ${rgbaOf(brand.ink, 0)} 70%)`,
          transformOrigin: `${px(cx)} ${px(cy)}`,
        }, parent);
        break;
      }
      case 'ruled': {
        // Editorial ruling: hairlines so quiet the field reads as ledger paper, not empty space.
        const spacing = Math.max(34, Math.min(W, H) * (spec.spacing_frac || 0.075));
        node = el('div', {
          position: 'absolute', left: px(b.x), top: px(b.y), width: px(b.w), height: px(b.h),
          backgroundImage: `repeating-linear-gradient(to bottom, transparent 0, transparent ${(spacing - 1).toFixed(2)}px, ${rgbaOf(brand.ink, 0.05)} ${spacing.toFixed(2)}px)`,
          opacity: spec.opacity == null ? 1 : spec.opacity,
        }, parent);
        break;
      }
      case 'wash': {
        // A soft off-paper tonal band behind the stage — a breath of colour without a second panel.
        const cx = b.x + b.w * (spec.align === 'left' ? 0.28 : spec.align === 'right' ? 0.72 : 0.5);
        node = el('div', {
          position: 'absolute', inset: '0',
          background: `radial-gradient(ellipse ${px(b.w * 1.2)} ${px(b.h)} at ${px(cx)} ${px(b.y + b.h * 0.5)}, ${rgbaOf(brand.accent || brand.ink, 0.05)}, ${rgbaOf(brand.ink, 0)} 62%)`,
        }, parent);
        break;
      }
      case 'glow': {
        // Collage field: a wide warm glow that drifts with the beat — the only "stage" a free canvas gets.
        const cx = b.x + b.w * (spec.align === 'left' ? 0.3 : spec.align === 'right' ? 0.7 : 0.5);
        const cy = b.y + b.h * 0.46;
        node = el('div', {
          position: 'absolute', inset: '0',
          background: `radial-gradient(ellipse ${px(b.w * 0.9)} ${px(b.h * 0.8)} at ${px(cx)} ${px(cy)}, ${rgbaOf(brand.accent || brand.ink, 0.07)}, ${rgbaOf('#ffffff', 0.3)} 45%, ${rgbaOf(brand.ink, 0)} 75%)`,
          transformOrigin: `${px(cx)} ${px(cy)}`,
        }, parent);
        break;
      }
      case 'arc': {
        // A giant ring segment grazing the field — ambient geometry, never a diagram part.
        node = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H }, parent);
        Object.assign(node.style, { position: 'absolute', left: '0', top: '0' });
        const corner = spec.corner || 0;
        const cx = corner % 2 === 0 ? b.x + b.w * 0.98 : b.x + b.w * 0.02;
        const cy = corner < 2 ? b.y + b.h * 0.04 : b.y + b.h * 0.96;
        const R = Math.min(W, H) * 0.62;
        svgEl('circle', { cx, cy, r: R, fill: 'none', stroke: brand.ink, 'stroke-width': Math.max(1.2, Math.min(W, H) * 0.002), 'stroke-opacity': 0.14 }, node);
        svgEl('circle', { cx, cy, r: R * 0.78, fill: 'none', stroke: brand.ink, 'stroke-width': Math.max(1, Math.min(W, H) * 0.0014), 'stroke-opacity': 0.08 }, node);
        break;
      }
      default:
        break;
    }
    return { spec, node, i: idx };
  }

  function buildBackground(beat, plan, beatRoot) {
    const bg = beat.composition.background || {};
    const brand = plan.brand;
    const layer = el('div', { position: 'absolute', inset: '0', zIndex: '1', background: brand.paper }, beatRoot);
    const layers = (Array.isArray(bg.layers) ? bg.layers : []).map((spec, i) => buildBgLayer(spec, plan, layer, i)).filter((l) => l.node);
    // A barely-there vignette on every beat so the paper reads as a surface, not a void.
    el('div', {
      position: 'absolute', inset: '0',
      background: 'radial-gradient(ellipse 85% 80% at 50% 45%, rgba(14,14,14,0) 55%, rgba(14,14,14,0.03) 100%)',
    }, layer);
    return { layer, layers };
  }

  function applyBackgroundState(bgNode, lt, beat, stageFade, preRoll) {
    if (stageFade != null) bgNode.layer.style.opacity = stageFade.toFixed(4);
    if (!bgNode.layers.length) return;
    const settle = (beat.ensemble.events || []).find((e) => e.channel === 'BACKGROUND' && e.event === 'STAGE_SETTLE');
    const ss = settle ? settle.start_ms : 0, se = settle ? settle.end_ms : 0;
    // The ensemble's settled-hold window owns the ambient pass: parallax engages only inside it.
    const holdStart = ((beat.ensemble.hold_window || {}).start_ms) || Number.MAX_SAFE_INTEGER;
    // Stage furniture runs on the pre-rolled clock: a beat that dressed under the previous
    // beat's transition continues from that point at takeover instead of re-fading from zero.
    const ltFx = lt + (preRoll || 0);
    for (const L of bgNode.layers) {
      const spec = L.spec, s = L.node.style;
      // Each layer lands within ~170ms of its stagger slot — the stage is dressed before
      // the first content frame regardless of how long the ensemble's settle window runs.
      const ls = ss + L.i * 40, le = Math.min(se + L.i * 40, ls + 170);
      const p = EASE.outCubic(prog(ltFx, ls, Math.max(le, ls + 1)));
      let scale = 1, tx = 0, ty = 0;
      if (spec.kind === 'panel' || spec.kind === 'plane' || spec.kind === 'spotlight') scale = lerp(0.985, 1, EASE.settle(p));
      if (spec.kind === 'dotgrid' || spec.kind === 'plane' || spec.kind === 'glow') {
        const amb = ambientDrift(lt, `bg-${beat.beat_id}-${L.i}`, holdStart, spec.kind === 'dotgrid' ? 2.8 : spec.kind === 'glow' ? 6 : 1.6);
        tx += amb.dx; ty += amb.dy;
      }
      if (spec.kind === 'glow') scale = lerp(1.06, 1, EASE.settle(p));
      if (spec.rotation_deg) s.rotate = `${spec.rotation_deg}deg`;
      s.opacity = ((spec.opacity == null ? 1 : spec.opacity) * p).toFixed(4);
      s.transform = `translate(${f2(tx)}px, ${f2(ty)}px) scale(${scale.toFixed(4)})`;
    }
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
    frame.dataset.mediaAsset = media.asset_id;
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
    const chassis = media.chassis || 'card';
    let host = frame, hostW = bb.w, hostH = bb.h;
    if (chassis === 'phone') {
      // Device bezel: ink body, the media is its screen; a camera slit tops the bezel.
      const m = Math.min(bb.w, bb.h);
      Object.assign(frame.style, {
        borderRadius: px(m * 0.11), border: 'none', background: '#161311',
        boxShadow: `0 ${px(bb.h * 0.025)} ${px(bb.h * 0.07)} rgba(23,18,12,0.35), inset 0 0 0 ${px(m * 0.008)} #2c2620`,
      });
      hostW = bb.w * 0.91; hostH = bb.h * 0.944;
      host = el('div', {
        position: 'absolute', left: px(bb.w * 0.045), top: px(bb.h * 0.028),
        width: px(hostW), height: px(hostH),
        borderRadius: px(m * 0.075), overflow: 'hidden', background: '#000',
      }, frame);
      el('div', {
        position: 'absolute', left: '50%', top: px(bb.h * 0.011), transform: 'translateX(-50%)',
        width: px(bb.w * 0.16), height: px(bb.h * 0.009), borderRadius: px(bb.h * 0.005), background: '#2c2620',
      }, frame);
    } else if (chassis === 'browser') {
      // Window chrome: a top bar with traffic dots and an address pill; media is the viewport.
      const barH = bb.h * 0.1;
      Object.assign(frame.style, { borderRadius: px(Math.min(bb.w, bb.h) * 0.05), background: brand.paper });
      const bar = el('div', {
        position: 'absolute', left: '0', top: '0', width: '100%', height: px(barH),
        borderBottom: `1.5px solid ${brand.ink}22`, display: 'flex', alignItems: 'center', gap: px(bb.w * 0.012), paddingLeft: px(bb.w * 0.03), boxSizing: 'border-box',
      }, frame);
      for (const c of ['#e0635a', '#e8b13e', '#5fbb63']) el('div', { width: px(barH * 0.34), height: px(barH * 0.34), borderRadius: '50%', background: c, flex: 'none' }, bar);
      el('div', { flex: '0 1 62%', height: px(barH * 0.44), marginLeft: px(bb.w * 0.02), borderRadius: px(barH * 0.22), background: `${brand.ink}12` }, bar);
      hostH = bb.h - barH;
      host = el('div', {
        position: 'absolute', left: '0', top: px(barH), width: '100%', height: px(hostH), overflow: 'hidden',
      }, frame);
    } else if (chassis === 'shot') {
      // Floating screenshot card: no chrome — tilted, deeply shadowed, dark-rimmed like the
      // product stills in the benchmark films. tilt is authored in degrees (params.tilt).
      const tilt = clamp(Number(media.tilt == null ? -3.5 : media.tilt), -14, 14);
      // The frame releases the card: no border, no clipping — the shadow belongs to the tilted host.
      Object.assign(frame.style, { overflow: 'visible', border: 'none', borderRadius: '0', background: 'transparent' });
      host = el('div', {
        position: 'absolute', left: '0', top: '0', width: px(bb.w), height: px(bb.h),
        transform: `rotate(${tilt.toFixed(2)}deg)`, transformOrigin: '50% 50%',
        borderRadius: px(Math.min(bb.w, bb.h) * 0.045), overflow: 'hidden',
        boxShadow: `0 ${px(bb.h * 0.05)} ${px(bb.h * 0.13)} rgba(23,18,12,0.34), 0 ${px(bb.h * 0.012)} ${px(bb.h * 0.028)} rgba(23,18,12,0.22)`,
        outline: `1.5px solid rgba(23,18,12,0.28)`,
      }, frame);
    }
    Object.assign(node.style, { position: 'absolute', left: '0', top: '0', width: '100%', height: '100%', objectFit: 'cover', display: 'block' });
    host.appendChild(node);
    const m = { media, frame, node, bb, hostW, hostH, pending: null };
    layoutFocus(m, hostW, hostH);
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
    const chrome = md.chrome_ms == null ? md.enter_ms : md.chrome_ms;
    // Pre-chrome still runs the pipeline at p=0 so every driven decl is rewritten — same
    // seek-determinism rule as entities and relations.
    s.visibility = lt < chrome ? 'hidden' : 'visible';
    let tx = 0, ty = 0, opacity = 1, clip = null, scale = 1;
    const p = EASE.outQuint(prog(lt, md.enter_ms, md.enter_ms + md.enter_duration_ms));
    // The empty card dresses the stage first; the exhibit itself still lands on its word.
    m.node.style.opacity = md.enter_duration_ms ? Math.min(1, p * 1.6).toFixed(4) : '1';
    const pf = EASE.outQuint(prog(lt, chrome, chrome + Math.max(md.enter_duration_ms, 320)));
    if (md.enter_duration_ms > 0 || lt < md.enter_ms) {
      ty = (1 - pf) * m.bb.h * 0.08;
      clip = [0, 0, (1 - pf) * 100, 0];
      opacity = Math.min(1, pf * 1.6);
    }
    if (md.reframe) {
      const rp = EASE.inOutCubic(prog(lt, md.reframe.start_ms, md.reframe.end_ms));
      const from = bboxOf(md.reframe.from);
      const x = lerp(from.x, m.bb.x, rp), y = lerp(from.y, m.bb.y, rp);
      const w = lerp(from.w, m.bb.w, rp), h = lerp(from.h, m.bb.h, rp);
      s.left = px(x); s.top = px(y); s.width = px(w); s.height = px(h);
      layoutFocus(m, w * (m.hostW / m.bb.w), h * (m.hostH / m.bb.h));
      const dist = Math.hypot(from.x - m.bb.x, from.y - m.bb.y) + Math.abs(from.w - m.bb.w);
      const blur = velocityBlur(lt, md.reframe.start_ms, md.reframe.end_ms, EASE.inOutCubic, dist);
      s.filter = blur > 0.15 ? `blur(${blur.toFixed(2)}px)` : '';
    }
    // Ambient: after the frame has settled it drifts with the hold, a living still.
    const settledAt = md.reframe ? md.reframe.end_ms : md.enter_ms + (md.enter_duration_ms || 0);
    const tzM = beat.composition.text_zone;
    const gapM = Math.max(tzM.x - (m.bb.x + m.bb.w), m.bb.x - (tzM.x + tzM.w), tzM.y - (m.bb.y + m.bb.h), m.bb.y - (tzM.y + tzM.h));
    const amb = ambientDrift(lt, `media-${md.asset_id || md.role || 'x'}`, settledAt, clamp(gapM * 0.35, 0, 1.1));
    tx += amb.dx; ty += amb.dy;
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
    s.visibility = lt < fig.enter_ms ? 'hidden' : 'visible';
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
    let chrome = null;
    if (data.chrome_ms != null) {
      const z = bboxOf(data.zone);
      chrome = el('div', {
        position: 'absolute', left: px(z.x), top: px(z.y + z.h - 2), width: px(z.w), height: '2px',
        background: brand.ink, zIndex: '15', transformOrigin: '0% 50%', opacity: '0.22',
      }, beatRoot);
    }
    return { data, blocks, rule, chrome };
  }

  function applyDataState(d, lt, beat, ctx) {
    const data = d.data;
    d.blocks.forEach((b, idx) => {
      const order = b.blk.role === 'label' ? d.blocks.length - 1 : (b.blk.side || 0);
      const start = data.enter_ms + order * (data.stagger_ms || 0);
      const s = b.wrap.style;
      s.visibility = lt < start ? 'hidden' : 'visible';
      const p = prog(lt, start, start + data.enter_duration_ms);
      let opacity = EASE.outCubic(p), ty = (1 - EASE.outQuint(p)) * b.bb.h * 0.12, scale = EASE.settle(p);
      if (b.blk.role === 'label') scale = 1;
      const tzA = beat.composition.text_zone;
      const gap = Math.max(tzA.x - (b.bb.x + b.bb.w), b.bb.x - (tzA.x + tzA.w), tzA.y - (b.bb.y + b.bb.h), b.bb.y - (tzA.y + tzA.h));
      const amb = ambientDrift(lt, `data-${b.blk.role}-${idx}`, start + data.enter_duration_ms, clamp(gap * 0.35, 0, 0.9));
      ty += amb.dy;
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
    if (d.chrome) {
      const p = EASE.outQuint(prog(lt, data.chrome_ms, data.chrome_ms + 340));
      d.chrome.style.transform = `scaleX(${p.toFixed(4)})`;
      d.chrome.style.visibility = lt < data.chrome_ms ? 'hidden' : 'visible';
    }
  }

  // ---------------------------------------------------------------------------
  // Illustration (compiled entity / relation / op program → persistent SVG)
  //
  // Every entity is built once as an SVG group with the parts each op can drive
  // (outline for DRAW, fill mask for FILL, accent overlay for INK, strike line,
  // …). Per frame we only write transforms, opacities and dash offsets. The
  // value of a driven property at time t is: the inherited state_in, else the
  // first op's `from`, else the rest value; then each op interpolates to its
  // `to`. The compiler bakes the same rule into carried entities.
  // ---------------------------------------------------------------------------
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const OP_PROPERTY = { DRAW: 'draw', FILL: 'fill', INK: 'ink', DIM: 'dim', GROW: 'grow', STRIKE: 'strike', SWAP: 'swap', COUNT: 'count', EMIT: 'emit', CONNECT: 'connect' };
  const PROPERTY_REST = { draw: 1, fill: 0, ink: 0, dim: 1, grow: 1, strike: 0, swap: 0, count: 1, emit: 0, connect: 1 };
  const OP_EASE = { DRAW: 'outQuint', FILL: 'inOutCubic', INK: 'outCubic', DIM: 'inOutCubic', GROW: 'settle', STRIKE: 'outQuint', SWAP: 'settle', COUNT: 'outCubic', EMIT: 'outCubic', CONNECT: 'outQuint' };

  function svgEl(tag, attrs, parent) {
    const n = document.createElementNS(SVG_NS, tag);
    for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) n.setAttribute(k, String(attrs[k]));
    if (parent) parent.appendChild(n);
    return n;
  }
  const f2 = (v) => Math.round(v * 100) / 100;
  const centre = (b) => ({ x: b.x + b.w / 2, y: b.y + b.h / 2 });

  function roundRectPath(b, r) {
    const x = b.x, y = b.y, w = b.w, h = b.h, rr = Math.min(r, w / 2, h / 2);
    return `M${f2(x + rr)} ${f2(y)}H${f2(x + w - rr)}A${f2(rr)} ${f2(rr)} 0 0 1 ${f2(x + w)} ${f2(y + rr)}V${f2(y + h - rr)}A${f2(rr)} ${f2(rr)} 0 0 1 ${f2(x + w - rr)} ${f2(y + h)}H${f2(x + rr)}A${f2(rr)} ${f2(rr)} 0 0 1 ${f2(x)} ${f2(y + h - rr)}V${f2(y + rr)}A${f2(rr)} ${f2(rr)} 0 0 1 ${f2(x + rr)} ${f2(y)}Z`;
  }
  function polyPath(pts) {
    return pts.map((p, i) => `${i ? 'L' : 'M'}${f2(p[0])} ${f2(p[1])}`).join('');
  }
  function polyLength(pts) {
    let l = 0;
    for (let i = 1; i < pts.length; i += 1) l += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    return l;
  }
  function pointAlong(pts, k) {
    const total = polyLength(pts);
    let d = clamp(k, 0, 1) * total;
    for (let i = 1; i < pts.length; i += 1) {
      const seg = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      if (d <= seg || i === pts.length - 1) {
        const t = seg ? clamp(d / seg, 0, 1) : 1;
        return { x: lerp(pts[i - 1][0], pts[i][0], t), y: lerp(pts[i - 1][1], pts[i][1], t) };
      }
      d -= seg;
    }
    return { x: pts[0][0], y: pts[0][1] };
  }

  // A stroked path whose reveal is a dash offset: length is taken once at build.
  function drawable(path, len, role) {
    path.style.strokeDasharray = `${f2(len)} ${f2(len + 4)}`;
    path.dataset.draw = role || 'outline';
    return {
      path,
      len,
      set(p) {
        path.style.strokeDasharray = `${f2(len)} ${f2(len + 4)}`;
        path.style.strokeDashoffset = `${f2((1 - clamp(p, 0, 1)) * len)}`;
      },
      // Draw-then-erase: a fixed-length comet sweeps the path — the head draws, the tail
      // erases behind it, and the stroke is gone again once the sweep has passed.
      setWipe(p) {
        const w = Math.max(10, len * 0.42);
        path.style.strokeDasharray = `${f2(w)} ${f2(len + w)}`;
        path.style.strokeDashoffset = `${f2(w - clamp(p, 0, 1) * (len + w))}`;
      },
    };
  }
  // A dashed outline cannot reveal by its own dash offset; a paper-coloured cover stroke recedes along it instead.
  function dashedDrawable(path, len, paper, sw, parent) {
    const cover = svgEl('path', { d: path.getAttribute('d') || '', fill: 'none', stroke: paper, 'stroke-width': sw * 1.9, 'stroke-linecap': 'butt' }, parent);
    if (path.tagName === 'circle') {
      const cx = +path.getAttribute('cx'), cy = +path.getAttribute('cy'), r = +path.getAttribute('r');
      cover.setAttribute('d', `M${f2(cx)} ${f2(cy - r)}A${f2(r)} ${f2(r)} 0 1 1 ${f2(cx)} ${f2(cy + r)}A${f2(r)} ${f2(r)} 0 1 1 ${f2(cx)} ${f2(cy - r)}`);
    }
    cover.style.strokeDasharray = `${f2(len)} ${f2(len)}`;
    cover.dataset.draw = 'cover';
    path.dataset.draw = 'outline-dashed';
    return {
      path,
      len,
      set(p) {
        cover.style.strokeDasharray = `${f2(len)} ${f2(len)}`;
        cover.style.strokeDashoffset = `${f2(-clamp(p, 0, 1) * len)}`;
      },
      // Wipe for a dashed stroke: the cover re-closes behind the head — it masks
      // everything except the traveling window [tail, head].
      setWipe(p) {
        const w = Math.max(10, len * 0.42);
        const head = clamp(p, 0, 1) * (len + w), tail = head - w;
        const a = Math.max(0, tail), b = Math.min(len, head);
        cover.style.strokeDashoffset = '0';
        cover.style.strokeDasharray = b <= a ? `${f2(len)} ${f2(len)}` : `${f2(a)} ${f2(b - a)} ${f2(len - b + w)} ${f2(len)}`;
      },
    };
  }

  function clusterCentres(b, count) {
    const c = centre(b), n = Math.max(1, count);
    if (n === 1) return [{ x: c.x, y: c.y, r: Math.min(b.w, b.h) / 2 }];
    const R = Math.min(b.w, b.h) / 2;
    const r = n === 2 ? R * 0.48 : n === 3 ? R * 0.44 : R / (1 + 1.15 * Math.sin(Math.PI / n)) * Math.sin(Math.PI / n) * 0.98;
    const ring = R - r;
    const out = [];
    for (let i = 0; i < n; i += 1) {
      const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
      out.push({ x: c.x + Math.cos(a) * ring, y: c.y + Math.sin(a) * ring, r });
    }
    return out;
  }

  // Colour packs reuse ids (gradients, clip paths, filters) across icons; scope them per
  // instance so two emoji on one stage do not paint with each other's defs. A carried entity is
  // rebuilt per beat, so the scope is a running counter rather than the entity id.
  let iconInstance = 0;

  function scopeSvgIds(markup, scope) {
    const ids = new Set();
    markup.replace(/\bid="([^"]+)"/g, (m, id) => { ids.add(id); return m; });
    if (!ids.size) return markup;
    const tag = String(scope).replace(/[^a-zA-Z0-9_-]/g, '_');
    let out = markup;
    for (const id of ids) {
      const esc = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      out = out.replace(new RegExp(`\\bid="${esc}"`, 'g'), `id="${tag}__${id}"`)
        .replace(new RegExp(`url\\(#${esc}\\)`, 'g'), `url(#${tag}__${id})`)
        .replace(new RegExp(`url\\("#${esc}"\\)`, 'g'), `url("#${tag}__${id}")`)
        .replace(new RegExp(`(xlink:href|href)="#${esc}"`, 'g'), `$1="#${tag}__${id}"`);
    }
    return out;
  }

  // Registry icon loaded into a box inside a glyph group; each part joins the entity's
  // draw-on program (stroke packs dash-draw, fill packs stagger in).
  function loadIconInto(ent, node, host, box, opts) {
    node.ready = fetchText(opts.assetUrl(ent.asset.path)).then((txt) => {
      const doc = new DOMParser().parseFromString(txt, 'image/svg+xml');
      const src = doc.documentElement;
      if (src.nodeName === 'parsererror' || !src.getAttribute) throw new Error(`icon ${ent.asset.id}: not an svg`);
      const vb = (src.getAttribute('viewBox') || `0 0 ${src.getAttribute('width') || 100} ${src.getAttribute('height') || 100}`).split(/[\s,]+/).map(Number);
      const s = Math.min(box.w / vb[2], box.h / vb[3]);
      const inner = svgEl('g', { transform: `translate(${f2(box.x + (box.w - vb[2] * s) / 2)} ${f2(box.y + (box.h - vb[3] * s) / 2)}) scale(${s.toFixed(5)}) translate(${-vb[0]} ${-vb[1]})` }, host);
      inner.innerHTML = scopeSvgIds(src.innerHTML, `${ent.id}_${++iconInstance}`);
      const colour = ent.asset.colour || 'mono';
      if (colour === 'brand' && ent.asset.brand_hex) host.dataset.brandHex = ent.asset.brand_hex;
      const rootStroke = src.getAttribute('stroke');
      const parts = Array.from(inner.querySelectorAll('path,circle,ellipse,line,polyline,polygon,rect'));
      const n = Math.max(1, parts.length);
      if (colour === 'native') {
        // Colour art keeps its own paint; it draws on as one body (opacity), never dash-by-dash.
        node.outline.push({ path: inner, len: 0, set(v) { inner.style.opacity = clamp(v, 0, 1).toFixed(4); } });
        return;
      }
      parts.forEach((p, i) => {
        p.dataset.draw = 'outline';
        const stroked = (p.getAttribute('stroke') || rootStroke || 'none') !== 'none';
        let len = 0;
        if (stroked) { try { len = p.getTotalLength() || 0; } catch (e) { len = 0; } }
        if (stroked && len > 0) {
          p.style.strokeDasharray = `${f2(len)} ${f2(len + 4)}`;
          node.outline.push({ path: p, len, set(v) { p.style.strokeDashoffset = `${f2((1 - clamp(v * n - i, 0, 1)) * len)}`; } });
        } else {
          node.outline.push({ path: p, len: 0, set(v) { p.style.opacity = clamp(v * n - i, 0, 1).toFixed(4); p.style.strokeDashoffset = '0'; } });
        }
      });
    });
  }

  function buildGlyph(ent, il, plan, g, sw, opts) {
    const b = bboxOf(ent.bbox), ink = plan.brand.ink, paper = plan.brand.paper, accent = il.accent || ink;
    const params = ent.params || {};
    const node = { outline: [], inkEls: [], count: [], strike: null, fill: null, extra: {} };
    const line = { fill: 'none', stroke: ink, 'stroke-width': sw, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' };
    const dash = params.dashed ? `${f2(sw * 2.2)} ${f2(sw * 2.6)}` : null;

    // The strike is one decisive diagonal, the "no" of the language; it sits above every other part.
    const strikeFor = (box) => {
      const p = svgEl('path', { ...line, d: polyPath([[box.x + box.w * 0.06, box.y + box.h * 0.82], [box.x + box.w * 0.94, box.y + box.h * 0.18]]), 'stroke-width': sw * 1.35, 'stroke-linecap': 'round' }, g);
      const d = drawable(p, Math.hypot(box.w * 0.88, box.h * 0.64), 'strike');
      d.set(0);
      return d;
    };

    switch (ent.glyph) {
      case 'VESSEL': {
        const top = b.w, bot = b.w * 0.78, lip = b.h * 0.035;
        const x0 = b.x + (b.w - top) / 2, x1 = b.x + (b.w - bot) / 2, r = b.w * 0.14;
        const body = `M${f2(x0)} ${f2(b.y + lip)}L${f2(x1)} ${f2(b.y + b.h - r)}Q${f2(x1)} ${f2(b.y + b.h)} ${f2(x1 + r)} ${f2(b.y + b.h)}H${f2(x1 + bot - r)}Q${f2(x1 + bot)} ${f2(b.y + b.h)} ${f2(x1 + bot)} ${f2(b.y + b.h - r)}L${f2(x0 + top)} ${f2(b.y + lip)}`;
        const clipId = `em2clip-${il.zone.x}-${ent.id}-${Math.round(b.y)}`.replace(/[^a-z0-9-]/gi, '');
        const defs = svgEl('defs', {}, g);
        const clip = svgEl('clipPath', { id: clipId }, defs);
        svgEl('path', { d: body + 'Z' }, clip);
        node.fill = svgEl('rect', { x: b.x, y: b.y + b.h, width: b.w, height: 0, fill: accent, 'clip-path': `url(#${clipId})` }, g);
        const outline = svgEl('path', { ...line, d: body }, g);
        node.outline.push(drawable(outline, b.h * 2.05 + bot));
        node.extra.setFill = (p, useAccent) => {
          const h = clamp(p, 0, 1) * (b.h - lip - sw);
          node.fill.setAttribute('y', f2(b.y + b.h - h));
          node.fill.setAttribute('height', f2(h));
          node.fill.setAttribute('fill', useAccent ? accent : ink);
          node.fill.setAttribute('fill-opacity', useAccent ? '1' : '0.85');
        };
        node.strike = strikeFor(b);
        break;
      }
      case 'NODE': {
        const cs = clusterCentres(b, params.count || 1);
        cs.forEach((c) => {
          const base = svgEl('circle', { cx: c.x, cy: c.y, r: c.r - sw / 2, fill: paper }, g);
          const inkEl = svgEl('circle', { cx: c.x, cy: c.y, r: c.r - sw / 2, fill: accent, 'fill-opacity': 0 }, g);
          const o = svgEl('circle', { ...line, cx: c.x, cy: c.y, r: c.r - sw / 2, 'stroke-dasharray': dash }, g);
          node.count.push({ els: [base, inkEl, o] });
          node.inkEls.push(inkEl);
          const len = 2 * Math.PI * (c.r - sw / 2);
          if (dash) { const dd = dashedDrawable(o, len, paper, sw, g); node.count[node.count.length - 1].els.push(dd.path.nextSibling); node.outline.push(dd); } else node.outline.push(drawable(o, len));
        });
        node.strike = strikeFor(b);
        break;
      }
      case 'CARD':
      case 'PILL': {
        const r = ent.glyph === 'PILL' ? b.h / 2 : Math.min(b.w, b.h) * 0.09;
        const inner = { x: b.x + sw / 2, y: b.y + sw / 2, w: b.w - sw, h: b.h - sw };
        svgEl('path', { d: roundRectPath(inner, r), fill: paper }, g);
        node.inkEls.push(svgEl('path', { d: roundRectPath(inner, r), fill: accent, 'fill-opacity': 0 }, g));
        if (ent.glyph === 'CARD') {
          // A card carries a header rule: the object reads as a document, not a button.
          svgEl('path', { ...line, d: polyPath([[b.x + b.w * 0.1, b.y + b.h * 0.3], [b.x + b.w * 0.62, b.y + b.h * 0.3]]), 'stroke-width': sw * 0.8, 'stroke-opacity': 0.55 }, g);
          svgEl('path', { ...line, d: polyPath([[b.x + b.w * 0.1, b.y + b.h * 0.42], [b.x + b.w * 0.45, b.y + b.h * 0.42]]), 'stroke-width': sw * 0.8, 'stroke-opacity': 0.35 }, g);
        }
        const o = svgEl('path', { ...line, d: roundRectPath(inner, r), 'stroke-dasharray': dash }, g);
        const len = 2 * (inner.w + inner.h) - (8 - 2 * Math.PI) * r;
        node.outline.push(dash ? dashedDrawable(o, len, paper, sw, g) : drawable(o, len));
        node.strike = strikeFor(b);
        break;
      }
      case 'LENS': {
        // Built at the origin; positioned per frame by translate, so travel is one transform write.
        const w = sw * 1.5;
        const lens = svgEl('g', {}, g);
        let o, r;
        if (b.w > b.h * 1.5) {
          // Loupe framing a wide subject: an open ellipse around it, never a wash over its label.
          const rx = b.w / 2 - w, ry = b.h / 2 - w;
          o = svgEl('ellipse', { ...line, cx: 0, cy: 0, rx: rx, ry: ry, 'stroke-width': w }, lens);
          r = ry;
          const a = Math.PI / 4;
          const handle = svgEl('path', { ...line, d: polyPath([[rx * Math.cos(a), ry * Math.sin(a)], [rx * Math.cos(a) + ry * 0.7, ry * Math.sin(a) + ry * 0.7]]), 'stroke-width': w * 1.35 }, lens);
          node.outline.push(drawable(o, Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry)))), drawable(handle, ry));
        } else {
          const d = Math.min(b.w, b.h);
          r = d * 0.36;
          svgEl('circle', { cx: 0, cy: 0, r: r, fill: paper, 'fill-opacity': 0.32 }, lens);
          o = svgEl('circle', { ...line, cx: 0, cy: 0, r: r, 'stroke-width': w }, lens);
          const handle = svgEl('path', { ...line, d: polyPath([[r * 0.72, r * 0.72], [r * 1.42, r * 1.42]]), 'stroke-width': w * 1.35 }, lens);
          node.outline.push(drawable(o, 2 * Math.PI * r), drawable(handle, r));
        }
        node.extra.lens = lens;
        node.extra.lensR = r;
        break;
      }
      case 'RING': {
        const c = centre(b), R = Math.min(b.w, b.h) / 2 - sw, n = params.rings || 3;
        // The glyph is a set of concentric rings; EMIT still layers its own pulse rings on top.
        for (let i = 0; i < n; i += 1) {
          const r = R * (n === 1 ? 1 : 0.42 + 0.58 * (i / (n - 1)));
          node.outline.push(drawable(svgEl('circle', { ...line, cx: c.x, cy: c.y, r: f2(r) }, g), 2 * Math.PI * r));
        }
        node.extra.R = R;
        break;
      }
      case 'CHART_LINE': {
        const pts = (params.points || [0.2, 0.8]).map((v, i, arr) => [b.x + (i / (arr.length - 1)) * b.w, b.y + b.h - clamp(v, 0, 1) * b.h * 0.9]);
        svgEl('path', { ...line, d: polyPath([[b.x, b.y + b.h], [b.x + b.w, b.y + b.h]]), 'stroke-width': sw * 0.7, 'stroke-opacity': 0.45 }, g);
        const p = svgEl('path', { ...line, d: polyPath(pts), 'stroke-width': sw * 1.2 }, g);
        const dot = svgEl('circle', { cx: pts[0][0], cy: pts[0][1], r: sw * 1.4, fill: ink }, g);
        node.outline.push(drawable(p, polyLength(pts)));
        node.extra.setGrow = (k) => {
          node.outline[0].set(k);
          const q = pointAlong(pts, k);
          dot.setAttribute('cx', f2(q.x));
          dot.setAttribute('cy', f2(q.y));
        };
        break;
      }
      case 'BAR': {
        // The full extent stays as a ghost so a bar that shrinks shows what it lost, not just what is left.
        const ghost = svgEl('rect', { x: b.x, y: b.y, width: b.w, height: b.h, fill: 'none', stroke: ink, 'stroke-width': sw * 0.6, 'stroke-opacity': 0, 'stroke-dasharray': `${f2(sw * 1.4)} ${f2(sw * 1.8)}`, rx: sw }, g);
        const base = svgEl('rect', { x: b.x, y: b.y, width: b.w, height: b.h, fill: ink, rx: sw, 'data-grow': 'bar' }, g);
        const inkEl = svgEl('rect', { x: b.x, y: b.y, width: b.w, height: b.h, fill: accent, 'fill-opacity': 0, rx: sw }, g);
        node.inkEls.push(inkEl);
        svgEl('path', { ...line, d: polyPath([[b.x - sw, b.y + b.h], [b.x + b.w + sw, b.y + b.h]]), 'stroke-width': sw * 0.7 }, g);
        node.extra.setGrow = (k) => {
          const kk = clamp(k, 0, 1), h = Math.max(sw, kk * b.h);
          node.extra.growK = kk;
          for (const r of [base, inkEl]) { r.setAttribute('y', f2(b.y + b.h - h)); r.setAttribute('height', f2(h)); }
          ghost.setAttribute('stroke-opacity', (clamp((1 - kk) * 1.6, 0, 1) * 0.42).toFixed(4));
        };
        // COUNT reads as the value ticking up; the readout rides the bar's own top edge and only
        // exists when a COUNT op drives it — a bare count param is just the datum's value.
        if (params.count && il.ops.some((o) => o.op === 'COUNT' && o.target === ent.id)) {
          node.extra.countMax = Math.max(1, params.count);
          node.extra.countText = svgEl('text', {
            x: f2(b.x + b.w / 2), y: f2(b.y - sw), 'text-anchor': 'middle', 'font-size': f2(Math.min(b.w * 0.42, sw * 6.5)),
            'font-family': plan.fonts.families.text, 'font-weight': '600', fill: ink, 'font-variant-numeric': 'tabular-nums', 'fill-opacity': 0,
          }, g);
        }
        break;
      }
      case 'PROHIBIT': {
        const c = centre(b), r = Math.min(b.w, b.h) / 2 - sw;
        const o = svgEl('circle', { ...line, cx: c.x, cy: c.y, r: r, 'stroke-width': sw * 1.4 }, g);
        const s = svgEl('path', { ...line, d: polyPath([[c.x - r * 0.7, c.y - r * 0.7], [c.x + r * 0.7, c.y + r * 0.7]]), 'stroke-width': sw * 1.4 }, g);
        node.outline.push(drawable(o, 2 * Math.PI * r), drawable(s, r * 1.98));
        break;
      }
      case 'BRACKET': {
        const k = Math.min(b.w * 0.25, b.h * 0.12);
        const l = svgEl('path', { ...line, d: polyPath([[b.x + k, b.y], [b.x, b.y], [b.x, b.y + b.h], [b.x + k, b.y + b.h]]) }, g);
        const r = svgEl('path', { ...line, d: polyPath([[b.x + b.w - k, b.y], [b.x + b.w, b.y], [b.x + b.w, b.y + b.h], [b.x + b.w - k, b.y + b.h]]) }, g);
        node.outline.push(drawable(l, b.h + 2 * k), drawable(r, b.h + 2 * k));
        break;
      }
      case 'ARROW': {
        // A gestural arc-arrow: quadratic sweep + a two-stroke head; `bend` bows it, `flip` mirrors it.
        const flip = params.flip ? -1 : 1;
        const bend = params.bend != null ? clamp(Number(params.bend), -1, 1) : -0.45;
        const p0 = [b.x + b.w * (flip > 0 ? 0.06 : 0.94), b.y + b.h * 0.8];
        const p1 = [b.x + b.w * (flip > 0 ? 0.94 : 0.06), b.y + b.h * 0.2];
        const cx = (p0[0] + p1[0]) / 2, cy = (p0[1] + p1[1]) / 2 + bend * b.h;
        const pts = [];
        for (let i = 0; i <= 14; i += 1) {
          const t = i / 14, u = 1 - t;
          pts.push([u * u * p0[0] + 2 * u * t * cx + t * t * p1[0], u * u * p0[1] + 2 * u * t * cy + t * t * p1[1]]);
        }
        node.outline.push(drawable(svgEl('path', { ...line, d: polyPath(pts), 'stroke-width': sw * 1.55 }, g), polyLength(pts)));
        const dx = p1[0] - cx, dy = p1[1] - cy, ang = Math.atan2(dy, dx);
        const hl = Math.min(b.w, b.h) * 0.24;
        const head = polyPath([[p1[0] + Math.cos(ang + Math.PI * 0.8) * hl, p1[1] + Math.sin(ang + Math.PI * 0.8) * hl], p1,
                               [p1[0] + Math.cos(ang - Math.PI * 0.8) * hl, p1[1] + Math.sin(ang - Math.PI * 0.8) * hl]]);
        node.outline.push(drawable(svgEl('path', { ...line, d: head, 'stroke-width': sw * 1.55 }, g), hl * 2));
        node.inkEls.push(svgEl('path', { d: head + 'Z', fill: accent, 'fill-opacity': 0 }, g));
        node.strike = strikeFor(b);
        break;
      }
      case 'MARK_CIRCLE': {
        // A hand-marked loop: starts ~200°, wobbles ±3% in radius, and overshoots a full turn by ~40°.
        const c = centre(b), rx = b.w / 2 - sw, ry = b.h / 2 - sw;
        const a0 = Math.PI * 1.12, sweep = Math.PI * 2.22, pts = [];
        for (let i = 0; i <= 30; i += 1) {
          const t = i / 30, a = a0 + sweep * t;
          const wob = 1 + 0.032 * Math.sin(a * 3.1 + 0.7);
          pts.push([c.x + Math.cos(a) * rx * wob, c.y + Math.sin(a) * ry * wob]);
        }
        node.outline.push(drawable(svgEl('path', { ...line, d: polyPath(pts), 'stroke-width': sw * 1.3 }, g), polyLength(pts)));
        node.strike = strikeFor(b);
        break;
      }
      case 'UNDERLINE': {
        // A two-stroke swash: a waved main stroke and a shorter echo that trails it.
        const main = [[b.x, b.y + b.h * 0.5], [b.x + b.w * 0.32, b.y + b.h * 0.7], [b.x + b.w * 0.66, b.y + b.h * 0.44], [b.x + b.w, b.y + b.h * 0.56]];
        const echo = [[b.x + b.w * 0.06, b.y + b.h * 0.9], [b.x + b.w * 0.62, b.y + b.h * 0.96]];
        node.outline.push(drawable(svgEl('path', { ...line, d: polyPath(main), 'stroke-width': sw * 1.5 }, g), polyLength(main)));
        const ep = svgEl('path', { ...line, d: polyPath(echo), 'stroke-width': sw * 0.9, 'stroke-opacity': 0 }, g);
        ep.dataset.draw = 'outline';
        node.outline.push({ path: ep, len: 0, set(v) { ep.setAttribute('stroke-opacity', (clamp(v * 1.6 - 0.6, 0, 1) * 0.55).toFixed(4)); } });
        break;
      }
      case 'BURST': {
        // Radiating rays with a hollow centre; rays stagger in through the shared draw value.
        const c = centre(b), R = Math.min(b.w, b.h) / 2 - sw, n = Math.max(5, params.rays || 11);
        for (let i = 0; i < n; i += 1) {
          const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
          const r0 = R * 0.36, r1 = R * (i % 2 === 0 ? 1 : 0.74);
          const len = r1 - r0;
          const p = svgEl('path', { ...line, d: polyPath([[c.x + Math.cos(a) * r0, c.y + Math.sin(a) * r0], [c.x + Math.cos(a) * r1, c.y + Math.sin(a) * r1]]), 'stroke-width': sw * 1.45 }, g);
          p.style.strokeDasharray = `${f2(len)} ${f2(len + 4)}`;
          p.dataset.draw = 'outline';
          node.outline.push({ path: p, len, set(v) { p.style.strokeDashoffset = `${f2((1 - clamp(v * n - i, 0, 1)) * len)}`; } });
        }
        break;
      }
      case 'CALLOUT': {
        // A speech bubble: rounded body + a tail that points at whatever sits below it.
        const r = Math.min(b.w, b.h) * 0.14, tail = params.tail || 'bl';
        const inner = { x: b.x + sw / 2, y: b.y + sw / 2, w: b.w - sw, h: b.h * 0.78 - sw };
        const tx = b.x + b.w * (tail === 'br' ? 0.74 : tail === 'b' ? 0.5 : 0.26);
        const tp = [[tx - b.w * 0.1, inner.y + inner.h], [tx + b.w * 0.02, b.y + b.h - sw / 2], [tx + b.w * 0.17, inner.y + inner.h]];
        const dBody = roundRectPath(inner, r);
        svgEl('path', { d: dBody + polyPath(tp) + 'Z', fill: paper }, g);
        node.inkEls.push(svgEl('path', { d: dBody + polyPath(tp) + 'Z', fill: accent, 'fill-opacity': 0 }, g));
        node.outline.push(drawable(svgEl('path', { ...line, d: dBody.slice(0, -1) + 'L' + f2(tp[0][0]) + ' ' + f2(tp[0][1]) + 'L' + f2(tp[1][0]) + ' ' + f2(tp[1][1]) + 'L' + f2(tp[2][0]) + ' ' + f2(tp[2][1]) + 'Z' }, g), 2 * (inner.w + inner.h) + b.w * 0.4));
        node.strike = strikeFor(b);
        break;
      }
      case 'STICKY': {
        // A sticky note: paper square with a folded top-right corner, held at a slight rotation.
        const fold = Math.min(b.w, b.h) * 0.22;
        const body = [[b.x, b.y], [b.x + b.w - fold, b.y], [b.x + b.w, b.y + fold], [b.x + b.w, b.y + b.h], [b.x, b.y + b.h]];
        const bodyD = polyPath(body) + 'Z';
        svgEl('path', { d: bodyD, fill: paper }, g);
        node.inkEls.push(svgEl('path', { d: bodyD, fill: accent, 'fill-opacity': 0 }, g));
        const foldPts = [[b.x + b.w - fold, b.y], [b.x + b.w - fold, b.y + fold], [b.x + b.w, b.y + fold]];
        const foldD = polyPath(foldPts);
        svgEl('path', { d: foldD + 'Z', fill: ink, 'fill-opacity': 0.1 }, g);
        node.outline.push(drawable(svgEl('path', { ...line, d: bodyD }, g), polyLength(body) + Math.hypot(body[0][0] - body[4][0], body[0][1] - body[4][1])));
        node.outline.push(drawable(svgEl('path', { ...line, d: foldD, 'stroke-width': sw * 0.8 }, g), polyLength(foldPts)));
        node.strike = strikeFor(b);
        node.extra.rotateDeg = -2.4;
        break;
      }
      case 'DONUT': {
        // A progress ring: paper track + an arc that GROW sweeps, with an optional COUNT readout.
        const c = centre(b), R = Math.min(b.w, b.h) / 2 - sw * 1.6;
        svgEl('circle', { cx: c.x, cy: c.y, r: R, fill: 'none', stroke: ink, 'stroke-width': sw * 1.5, 'stroke-opacity': 0.16 }, g);
        const arc = svgEl('circle', { ...line, cx: c.x, cy: c.y, r: R, 'stroke-width': sw * 2.6, transform: `rotate(-90 ${f2(c.x)} ${f2(c.y)})` }, g);
        arc.dataset.draw = 'outline';
        const circ = 2 * Math.PI * R;
        node.outline.push({ path: arc, len: circ, set(v) { arc.style.strokeDasharray = `${f2(circ * clamp(v, 0, 1))} ${f2(circ)}`; arc.style.strokeDashoffset = '0'; } });
        node.extra.setGrow = (k) => node.outline[0].set(k);
        if (params.count && il.ops.some((o) => o.op === 'COUNT' && o.target === ent.id)) {
          node.extra.countMax = Math.max(1, params.count);
          node.extra.countSuffix = params.suffix ? String(params.suffix) : '';
          const digits = (Math.round(params.count).toLocaleString('en-US') + node.extra.countSuffix).length;
          node.extra.countText = svgEl('text', {
            x: f2(c.x), y: f2(c.y + sw * 1.4), 'text-anchor': 'middle', 'font-size': f2(Math.min(R * 0.72, (R * 1.7) / Math.max(1, digits * 0.6))),
            'font-family': plan.fonts.families.data, 'font-weight': '600', fill: ink, 'font-variant-numeric': 'tabular-nums', 'fill-opacity': 0,
          }, g);
        }
        node.strike = strikeFor(b);
        break;
      }
      case 'FRAME': {
        // Crop marks: four corner ticks framing the box — reads as a selection, not a container.
        const k = Math.min(b.w, b.h) * 0.24;
        const corners = [
          [[b.x + k, b.y], [b.x, b.y], [b.x, b.y + k]],
          [[b.x + b.w - k, b.y], [b.x + b.w, b.y], [b.x + b.w, b.y + k]],
          [[b.x + k, b.y + b.h], [b.x, b.y + b.h], [b.x, b.y + b.h - k]],
          [[b.x + b.w - k, b.y + b.h], [b.x + b.w, b.y + b.h], [b.x + b.w, b.y + b.h - k]],
        ];
        for (const pts of corners) {
          node.outline.push(drawable(svgEl('path', { ...line, d: polyPath(pts), 'stroke-width': sw * 1.35 }, g), polyLength(pts)));
        }
        break;
      }
      case 'ICON': {
        const host = svgEl('g', {}, g);
        host.style.color = ink;
        node.inkEls.push(host);
        node.extra.iconHost = host;
        loadIconInto(ent, node, host, b, opts);
        node.strike = strikeFor(b);
        break;
      }
      case 'TILE': {
        // The product-collage atom: a glossy rounded-square app tile carrying a registry icon.
        const dark = params.tone === 'dark';
        const r = Math.min(b.w, b.h) * 0.24;
        const body = chassisBody(node, g);
        const base = svgEl('path', { d: roundRectPath({ x: b.x + sw / 2, y: b.y + sw / 2, w: b.w - sw, h: b.h - sw }, r) + 'Z' }, body);
        base.setAttribute('fill', dark ? '#171310' : mixColor(paper, '#ffffff', 0.72));
        base.setAttribute('stroke', ink);
        base.setAttribute('stroke-width', f2(sw * 0.55));
        base.setAttribute('stroke-opacity', '0.55');
        base.style.filter = `drop-shadow(0 ${f2(b.h * 0.07)}px ${f2(b.h * 0.13)}px rgba(23,18,12,0.28))`;
        if (!dark) {
          // Gloss: a light slope across the top half so the tile reads as enamel, not paper.
          svgEl('path', {
            d: `M${f2(b.x + sw / 2)} ${f2(b.y + r + sw / 2)}Q${f2(b.x + sw / 2)} ${f2(b.y + sw / 2)} ${f2(b.x + r + sw / 2)} ${f2(b.y + sw / 2)}L${f2(b.x + b.w - r - sw / 2)} ${f2(b.y + sw / 2)}Q${f2(b.x + b.w - sw / 2)} ${f2(b.y + sw / 2)} ${f2(b.x + b.w - sw / 2)} ${f2(b.y + r + sw / 2)}L${f2(b.x + b.w - sw / 2)} ${f2(b.y + b.h * 0.46)}Q${f2(b.x + b.w * 0.5)} ${f2(b.y + b.h * 0.62)} ${f2(b.x + sw / 2)} ${f2(b.y + b.h * 0.46)}Z`,
            fill: '#ffffff', 'fill-opacity': 0.5,
          }, body);
        }
        node.inkEls.push(svgEl('path', { d: roundRectPath({ x: b.x + sw / 2, y: b.y + sw / 2, w: b.w - sw, h: b.h - sw }, r) + 'Z', fill: accent, 'fill-opacity': 0 }, g));
        if (ent.asset) {
          const host = svgEl('g', {}, g);
          host.style.color = dark ? paper : ink;
          node.inkEls.push(host);
          node.extra.iconHost = host;
          const pad = b.w * 0.17;
          loadIconInto(ent, node, host, { x: b.x + pad, y: b.y + pad, w: b.w - pad * 2, h: b.h - pad * 2 }, opts);
        }
        node.strike = strikeFor(b);
        break;
      }
      case 'BADGE': {
        // Glossy white disc with a deep soft shadow carrying a brand mark or colour icon.
        const dark = params.tone === 'dark';
        const c = centre(b), R = Math.min(b.w, b.h) / 2 - sw / 2;
        const body = chassisBody(node, g);
        const disc = svgEl('circle', { cx: f2(c.x), cy: f2(c.y), r: f2(R) }, body);
        disc.setAttribute('fill', dark ? '#171310' : '#ffffff');
        disc.setAttribute('stroke', ink);
        disc.setAttribute('stroke-width', f2(sw * 0.4));
        disc.setAttribute('stroke-opacity', '0.18');
        disc.style.filter = `drop-shadow(0 ${f2(R * 0.16)}px ${f2(R * 0.3)}px rgba(23,18,12,0.26))`;
        if (!dark) {
          svgEl('path', {
            d: `M${f2(c.x - R * 0.82)} ${f2(c.y - R * 0.1)}A${f2(R * 0.82)} ${f2(R * 0.82)} 0 0 1 ${f2(c.x + R * 0.82)} ${f2(c.y - R * 0.1)}Q${f2(c.x)} ${f2(c.y + R * 0.18)} ${f2(c.x - R * 0.82)} ${f2(c.y - R * 0.1)}Z`,
            fill: '#ffffff', 'fill-opacity': 0.55,
          }, body);
        }
        node.inkEls.push(svgEl('circle', { cx: f2(c.x), cy: f2(c.y), r: f2(R), fill: accent, 'fill-opacity': 0 }, g));
        if (ent.asset) {
          const host = svgEl('g', {}, g);
          host.style.color = dark ? paper : ink;
          node.inkEls.push(host);
          node.extra.iconHost = host;
          const pad = R * 0.48;
          loadIconInto(ent, node, host, { x: c.x - R + pad, y: c.y - R + pad, w: 2 * (R - pad), h: 2 * (R - pad) }, opts);
        }
        node.strike = strikeFor(b);
        break;
      }
      case 'COUNTER': {
        // Stat card: a big tabular figure (prefix/suffix aware) over a small caption, on a light or dark body.
        const dark = params.tone === 'dark';
        const r = Math.min(b.w, b.h) * 0.18;
        const body = chassisBody(node, g);
        const card = svgEl('path', { d: roundRectPath({ x: b.x + sw / 2, y: b.y + sw / 2, w: b.w - sw, h: b.h - sw }, r) + 'Z' }, body);
        card.setAttribute('fill', dark ? '#171310' : '#ffffff');
        card.setAttribute('stroke', ink);
        card.setAttribute('stroke-width', f2(sw * 0.4));
        card.setAttribute('stroke-opacity', '0.18');
        card.style.filter = `drop-shadow(0 ${f2(b.h * 0.08)}px ${f2(b.h * 0.16)}px rgba(23,18,12,0.26))`;
        node.inkEls.push(svgEl('path', { d: roundRectPath({ x: b.x + sw / 2, y: b.y + sw / 2, w: b.w - sw, h: b.h - sw }, r) + 'Z', fill: accent, 'fill-opacity': 0 }, g));
        const fg = dark ? paper : ink;
        const caption = params.caption ? String(params.caption) : '';
        const max = Math.max(1, Number(params.count) || 1);
        const pre = params.prefix ? String(params.prefix) : '', suf = params.suffix ? String(params.suffix) : '';
        const full = pre + Math.round(max).toLocaleString('en-US') + suf;
        const fs = Math.min(b.h * (caption ? 0.42 : 0.5), (b.w * 0.86) / Math.max(1, full.length * 0.6));
        const cy = caption ? b.y + b.h * 0.5 : b.y + b.h * 0.5 + fs * 0.36;
        node.extra.countMax = max;
        node.extra.countPrefix = pre;
        node.extra.countSuffix = suf;
        node.extra.countText = svgEl('text', {
          x: f2(b.x + b.w / 2), y: f2(cy), 'text-anchor': 'middle', 'font-size': f2(fs), 'font-family': plan.fonts.families.data,
          'font-weight': '700', fill: fg, 'font-variant-numeric': 'tabular-nums', 'letter-spacing': f2(-fs * 0.03), 'fill-opacity': 0,
        }, g);
        node.extra.countText.textContent = full;
        if (caption) {
          const cap = svgEl('text', {
            x: f2(b.x + b.w / 2), y: f2(b.y + b.h * 0.78), 'text-anchor': 'middle', 'font-size': f2(Math.min(b.h * 0.14, (b.w * 0.86) / Math.max(1, caption.length * 0.55))),
            'font-family': plan.fonts.families.data, 'font-weight': '500', fill: fg, 'fill-opacity': 0.62,
          }, body);
          cap.textContent = caption;
        }
        // Static readout when no COUNT op ticks it: the figure is simply part of the drawn body.
        if (!il.ops.some((o) => o.op === 'COUNT' && o.target === ent.id)) {
          node.extra.countText.setAttribute('fill-opacity', '1');
          body.appendChild(node.extra.countText);
          node.extra.countText = null;
        }
        node.strike = strikeFor(b);
        break;
      }
      case 'CHIP': {
        // Dark product row: icon peg left, name typeset mid-left (the inside label), tag pills right.
        const r = b.h * 0.42;
        const body = chassisBody(node, g);
        const row = svgEl('path', { d: roundRectPath({ x: b.x, y: b.y, w: b.w, h: b.h }, r) + 'Z' }, body);
        row.setAttribute('fill', '#181410');
        row.style.filter = `drop-shadow(0 ${f2(b.h * 0.1)}px ${f2(b.h * 0.2)}px rgba(23,18,12,0.3))`;
        node.inkEls.push(svgEl('path', { d: roundRectPath({ x: b.x, y: b.y, w: b.w, h: b.h }, r) + 'Z', fill: accent, 'fill-opacity': 0 }, g));
        // Icon peg: a light tile clipped into the left end of the row.
        const peg = Math.min(b.h * 0.62, b.w * 0.14);
        const px0 = b.x + b.h * 0.19, py0 = b.y + (b.h - peg) / 2;
        svgEl('path', { d: roundRectPath({ x: px0, y: py0, w: peg, h: peg }, peg * 0.26) + 'Z', fill: paper }, body);
        if (ent.asset) {
          const host = svgEl('g', {}, g);
          host.style.color = ink;
          const pad = peg * 0.16;
          loadIconInto(ent, node, host, { x: px0 + pad, y: py0 + pad, w: peg - pad * 2, h: peg - pad * 2 }, opts);
        } else {
          svgEl('circle', { cx: px0 + peg / 2, cy: py0 + peg / 2, r: peg * 0.22, fill: ink }, body);
        }
        // Tag pills, right-aligned, hairline strokes on the dark field.
        // Pills own the right third of the row (the label strip ends at 63%); tags that would not
        // fit inside that budget are dropped from the end rather than run under the name.
        const fs = b.h * 0.17, tp = b.h * 0.08;
        const tagW = (t) => t.length * fs * 0.62 + tp * 2.6;
        const tags = (Array.isArray(params.tags) ? params.tags : []).slice(0, 3).map((t) => String(t));
        const budget = b.w * 0.37 - b.h * 0.15;
        while (tags.length && tags.reduce((a, t) => a + tagW(t), 0) + b.h * 0.1 * (tags.length - 1) > budget) tags.pop();
        let tx = b.x + b.w - b.h * 0.2;
        for (let i = tags.length - 1; i >= 0; i--) {
          const tw = tagW(tags[i]);
          tx -= tw;
          const th = b.h * 0.42, ty = b.y + (b.h - th) / 2;
          svgEl('path', { d: roundRectPath({ x: tx, y: ty, w: tw, h: th }, th / 2) + 'Z', fill: 'none', stroke: paper, 'stroke-width': Math.max(1, sw * 0.4), 'stroke-opacity': 0.5 }, body);
          const te = svgEl('text', { x: tx + tw / 2, y: ty + th / 2, 'text-anchor': 'middle', 'dominant-baseline': 'central', fill: paper, 'fill-opacity': 0.72, 'font-size': fs, 'font-weight': '500', 'font-family': plan.fonts.families.text }, body);
          te.textContent = tags[i];
          tx -= b.h * 0.1;
        }
        node.strike = strikeFor(b);
        break;
      }
      case 'MEDIA': {
        node.extra.media = true;
        node.strike = strikeFor(b);
        break;
      }
      default:
        throw new Error(`EditorialRuntime: unsupported glyph ${ent.glyph} (${ent.id})`);
    }
    // Any entity can earn an EMIT pulse: build its ring lazily so the op works on every glyph.
    if (!node.extra.rings && il.ops.some((o) => o.op === 'EMIT' && o.target === ent.id)) {
      const c = centre(b), R = Math.hypot(b.w, b.h) / 2;
      node.extra.R = R;
      if ((plan.motion || DEFAULT_MOTION).entrance === 'pop') {
        // Collage register: the pulse is a soft accent bloom behind the body, never a drawn ring.
        const rr = Math.min(b.w, b.h) / 2;
        const halo = svgEl('path', { d: roundRectPath({ x: b.x, y: b.y, w: b.w, h: b.h }, rr) + 'Z', fill: accent, 'fill-opacity': 0, 'data-halo': '' }, g);
        halo.style.filter = `blur(${f2(Math.min(b.w, b.h) * 0.22)}px)`;
        halo.style.transformOrigin = `${f2(c.x)}px ${f2(c.y)}px`;
        g.insertBefore(halo, g.firstChild);
        node.extra.halo = halo;
      } else {
        node.extra.rings = [svgEl('circle', { ...line, cx: c.x, cy: c.y, r: R * 0.3, stroke: accent, 'stroke-opacity': 0 }, g)];
      }
    }
    return node;
  }

  // Chassis glyphs (tile / badge / counter / chip) reveal as one body: the housing is never on
  // stage before what it carries, so DRAW fades the whole housing instead of tracing its rim.
  function chassisBody(node, g) {
    const body = svgEl('g', { 'data-draw': 'body' }, g);
    node.extra.chassis = true;
    node.outline.push({ path: body, len: 0, set(v) { body.style.opacity = clamp(v, 0, 1).toFixed(4); } });
    return body;
  }

  function buildLabel(ent, plan, beatRoot) {
    const lb = ent.label;
    if (!lb) return null;
    const bb = bboxOf(lb.bbox);
    const wrap = el('div', {
      position: 'absolute', left: px(bb.x), top: px(bb.y), width: px(bb.w), height: px(bb.h), zIndex: '13',
      willChange: 'transform, opacity', transformOrigin: '50% 50%',
    }, beatRoot);
    wrap.className = 'em2-il-label';
    const onDark = ent.glyph === 'CHIP';
    const text = el('div', {
      position: 'absolute', left: '0', right: '0', top: '50%', transform: 'translateY(-50%)',
      fontFamily: `"${plan.fonts.families.text}"`, fontSize: px(lb.fit.font_px), lineHeight: String(lb.fit.line_height),
      letterSpacing: `${lb.fit.tracking_em}em`, fontWeight: '600', color: onDark ? plan.brand.paper : plan.brand.ink, textAlign: ent.glyph === 'CHIP' ? 'left' : 'center', whiteSpace: 'nowrap',
    }, wrap);
    lb.fit.lines.forEach((l) => { const s = el('span', { display: 'block' }, text); s.className = 'em2-line'; s.textContent = l; });
    return { wrap, text, bb, inside: lb.placement === 'inside' };
  }

  function buildIllustration(il, plan, beatRoot, opts) {
    const W = plan.canvas.w, H = plan.canvas.h;
    const sw = Math.max(2.5, Math.min(W, H) * 0.0046);
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H }, beatRoot);
    Object.assign(svg.style, { position: 'absolute', left: '0', top: '0', zIndex: '10', overflow: 'visible', willChange: 'transform' });
    svg.classList.add('em2-illustration');
    const ink = plan.brand.ink, accent = il.accent || ink;
    const relLayer = svgEl('g', {}, svg);
    const entLayer = svgEl('g', {}, svg);
    const ents = new Map();
    const rels = new Map();
    const opsFor = new Map();
    for (const op of il.ops) {
      if (!opsFor.has(op.target)) opsFor.set(op.target, []);
      opsFor.get(op.target).push(op);
    }
    for (const list of opsFor.values()) list.sort((a, b) => a.start_ms - b.start_ms || a.end_ms - b.end_ms);

    const ready = [];
    for (const ent of il.entities) {
      const g = svgEl('g', { 'data-entity': ent.id }, entLayer);
      g.style.willChange = 'transform, opacity';
      const glyph = buildGlyph(ent, il, plan, g, sw, opts);
      if (glyph.ready) ready.push(glyph.ready);
      const label = buildLabel(ent, plan, beatRoot);
      let media = null;
      if (ent.glyph === 'MEDIA') {
        media = buildMedia({ ...ent.media, bbox: ent.bbox, enter_ms: ent.enter_ms, enter_duration_ms: ent.enter_duration_ms }, plan, beatRoot, opts.assetUrl);
        ready.push(mediaReady(media));
      }
      const settledAt = Math.max(ent.enter_ms + (ent.enter_duration_ms || 0), (opsFor.get(ent.id) || []).reduce((m, o) => Math.max(m, o.end_ms), 0));
      ents.set(ent.id, { ent, g, glyph, label, media, bb: bboxOf(ent.bbox), ops: opsFor.get(ent.id) || [], state: ent.state_in || {}, settledAt });
    }
    for (const rel of il.relations) {
      const r = { rel, ops: opsFor.get(rel.id) || [], state: rel.state_in || {}, path: null, arrow: null, bar: null, trace: null, strike: null, len: 0 };
      if (rel.path) {
        const g = svgEl('g', { 'data-relation': rel.id }, relLayer);
        r.g = g;
        r.len = rel.length || polyLength(rel.path);
        const line = { fill: 'none', stroke: ink, 'stroke-width': rel.thin ? Math.max(1.4, sw * 0.55) : sw, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' };
        const dash = rel.rule ? `${f2(sw * 1.6)} ${f2(sw * 2.2)}` : rel.dashed ? `${f2(sw * 1.5)} ${f2(sw * 2.6)}` : null;
        const p = svgEl('path', { ...line, d: polyPath(rel.path) }, g);
        if (dash) p.style.strokeDasharray = dash;
        r.path = rel.rule ? { path: p, len: r.len, set() {} } : rel.dashed ? dashedDrawable(p, r.len, plan.brand.paper, sw, g) : drawable(p, r.len);
        if (rel.dots) {
          // Product-diagram endpoints: a dot at each rim, appearing with the line's arrival.
          const p0 = rel.path[0], p1 = rel.path[rel.path.length - 1];
          r.dots = [
            svgEl('circle', { cx: p0[0], cy: p0[1], r: Math.max(2.2, sw * 1.05), fill: ink }, g),
            svgEl('circle', { cx: p1[0], cy: p1[1], r: Math.max(2.2, sw * 1.05), fill: ink }, g),
          ];
        }
        const n = rel.path.length, a = rel.path[n - 2], z = rel.path[n - 1];
        const ang = Math.atan2(z[1] - a[1], z[0] - a[0]);
        if (rel.arrow) {
          const s = sw * 2.6;
          r.arrow = svgEl('path', { d: polyPath([[-s, -s * 0.72], [0, 0], [-s, s * 0.72]]), ...line, transform: `translate(${f2(z[0])} ${f2(z[1])}) rotate(${f2((ang * 180) / Math.PI)})` }, g);
        }
        if (rel.bar) {
          const s = sw * 2.4;
          r.bar = svgEl('path', { d: polyPath([[0, -s], [0, s]]), ...line, 'stroke-width': sw * 1.4, transform: `translate(${f2(z[0])} ${f2(z[1])}) rotate(${f2((ang * 180) / Math.PI)})` }, g);
        }
        // TRACE: a short accent dash running along the drawn connector.
        r.trace = svgEl('path', { ...line, d: polyPath(rel.path), stroke: accent, 'stroke-width': sw * 1.3, 'stroke-opacity': 0 }, g);
        r.trace.style.strokeDasharray = `${f2(r.len * 0.18)} ${f2(r.len)}`;
        r.trace.dataset.draw = 'trace';
        const m = pointAlong(rel.path, 0.5), k = clamp(r.len * 0.16, sw * 3.2, sw * 6);
        const sp = svgEl('path', { ...line, d: polyPath([[m.x - k, m.y + k], [m.x + k, m.y - k]]), 'stroke-width': sw * 1.35 }, g);
        r.strike = drawable(sp, k * 2.83, 'strike');
        r.strike.set(0);
      }
      rels.set(rel.id, r);
    }
    return { il, svg, ents, rels, sw, accent, ready: Promise.all(ready) };
  }

  // Value of a driven property at beat-local time lt.
  function propAt(target, prop, lt) {
    let v = target.state[prop];
    let colorAccent = prop === 'ink' || prop === 'fill' || prop === 'emit' || prop === 'swap' || prop === 'strike' ? v !== undefined && v > 0 : false;
    let first = true;
    for (const op of target.ops) {
      if (OP_PROPERTY[op.op] !== prop) continue;
      if (first && v === undefined) v = op.from;
      first = false;
      if (lt >= op.start_ms) {
        const p = EASE[OP_EASE[op.op]](prog(lt, op.start_ms, op.end_ms));
        v = lerp(op.from, op.to, p);
        colorAccent = op.state_change;
      }
    }
    if (v === undefined) v = PROPERTY_REST[prop];
    return { v, accent: colorAccent };
  }

  function activeOps(target, name, lt) {
    return target.ops.filter((o) => o.op === name && lt >= o.start_ms && lt <= o.end_ms);
  }

  // The op currently owning a driven property: the last matching op that has started.
  function propDriver(target, prop, lt) {
    let d = null;
    for (const op of target.ops) {
      if (OP_PROPERTY[op.op] === prop && lt >= op.start_ms) d = op;
    }
    return d;
  }

  function lensPosition(node, ill, lt) {
    const start = node.state.at && ill.ents.has(node.state.at) ? centre(ill.ents.get(node.state.at).bb) : centre(node.bb);
    let pos = start;
    for (const op of node.ops) {
      if (op.op !== 'TRAVEL' || lt < op.start_ms) continue;
      const pts = [[pos.x, pos.y]].concat(op.params.over.map((id) => { const c = centre(ill.ents.get(id).bb); return [c.x, c.y]; }));
      const q = pointAlong(pts, EASE.inOutCubic(prog(lt, op.start_ms, op.end_ms)));
      pos = { x: q.x, y: q.y };
    }
    return pos;
  }

  function carryTransform(node, lt) {
    const from = node.ent.carry_from_bbox;
    if (!from) return '';
    const k = EASE.inOutCubic(prog(lt, 0, 420));
    if (k >= 1) return '';
    const T = node.bb, sx = lerp(from.w / T.w, 1, k), sy = lerp(from.h / T.h, 1, k);
    const tx = lerp(from.x - T.x, 0, k), ty = lerp(from.y - T.y, 0, k);
    return `translate(${f2(T.x + tx)} ${f2(T.y + ty)}) scale(${sx.toFixed(4)} ${sy.toFixed(4)}) translate(${f2(-T.x)} ${f2(-T.y)})`;
  }

  // The label rides its body through a carry reframe: same centre path, offset scaled with the
  // body, so it never sits at the destination while the body is still travelling.
  function carryLabelShift(node, lt) {
    const from = node.ent.carry_from_bbox;
    if (!from || !node.label) return { x: 0, y: 0 };
    const k = EASE.inOutCubic(prog(lt, 0, 420));
    if (k >= 1) return { x: 0, y: 0 };
    const T = node.bb, cT = centre(T), L = centre(node.label.bb);
    const sx = lerp(from.w / T.w, 1, k), sy = lerp(from.h / T.h, 1, k);
    const cx = lerp(from.x + from.w / 2, cT.x, k), cy = lerp(from.y + from.h / 2, cT.y, k);
    return { x: cx + (L.x - cT.x) * sx - L.x, y: cy + (L.y - cT.y) * sy - L.y };
  }

  function applyIllustrationState(ill, lt, beat, ctx) {
    const paper = ctx.brand.paper, ink = ctx.brand.ink, accent = ill.accent;
    const ex = ctx.exitState({ block: { role: 'illustration' } }, lt);
    for (const node of ill.ents.values()) {
      const ent = node.ent, g = node.g, gl = node.glyph;
      const preEntry = lt < ent.enter_ms;
      g.style.visibility = 'visible';
      const pEnt = ent.enter_duration_ms ? prog(lt, ent.enter_ms, ent.enter_ms + ent.enter_duration_ms) : 1;
      const pe = EASE.outQuint(pEnt);
      const dim = propAt(node, 'dim', lt).v;
      const pop = ctx.motion.entrance === 'pop';
      // 'pop' entrance: the element springs from ~60% with an easeOutBack overshoot and a short rise —
      // the benchmark's app-tile arrival; 'settle' is the editorial 94%→100% landing.
      let opacity = (pop ? Math.min(1, EASE.outCubic(pEnt) * 1.6) : pe) * dim;
      let scale = pop ? lerp(0.6, 1, EASE.emphasize(pEnt)) : lerp(0.94, 1, EASE.settle(pEnt));
      let ty = (1 - pe) * node.bb.h * (pop ? 0.1 : 0.04);
      // Ambient secondary motion once this entity's own program has fully run; the amplitude
      // shrinks with the gap to the text zone so drift can never close on the copy.
      const tzA = beat.composition.text_zone;
      const gap = Math.max(tzA.x - (node.bb.x + node.bb.w), node.bb.x - (tzA.x + tzA.w), tzA.y - (node.bb.y + node.bb.h), node.bb.y - (tzA.y + tzA.h));
      const amb = ambientDrift(lt, ent.id, node.settledAt, clamp(gap * 0.35, 0, 1.4));
      let tx = amb.dx; ty += amb.dy; scale *= amb.s;

      // SETTLE: a small confirming pulse; SWAP: the entity pops through a scale-and-clip beat into its new state.
      for (const op of activeOps(node, 'SETTLE', lt)) scale *= 1 + 0.03 * EASE.pulse(prog(lt, op.start_ms, op.end_ms));
      const swap = propAt(node, 'swap', lt);
      if (swap.v > 0 && swap.v < 1) scale *= 1 + 0.08 * EASE.pulse(swap.v);

      const draw = propAt(node, 'draw', lt).v;
      const drawOp = propDriver(node, 'draw', lt);
      if (drawOp && drawOp.params && drawOp.params.wipe) {
        // Wipe: stroked parts run the traveling comet; non-stroked parts pulse with the sweep.
        const pulse = Math.sin(Math.PI * clamp(draw, 0, 1));
        for (const d of gl.outline) { if (d.setWipe) d.setWipe(draw); else d.set(pulse); }
      } else {
        for (const d of gl.outline) d.set(draw);
      }

      const inkP = propAt(node, 'ink', lt);
      const inkLevel = clamp(Math.max(inkP.v, swap.v >= 0.5 ? swap.v : 0), 0, 1);
      for (const e of gl.inkEls) {
        if (e === gl.extra.iconHost) {
          const onDark = (ent.glyph === 'TILE' || ent.glyph === 'BADGE') && ((ent.params && ent.params.tone === 'dark') || (inkLevel > 0.5 && (inkP.accent || swap.accent)));
          // Brand marks paint in their brand hex on light bodies; enamel tiles keep a light glyph on dark bodies and accent fills.
          if (e.dataset.brandHex) e.style.color = onDark ? paper : e.dataset.brandHex;
          else if (ent.glyph === 'TILE' || ent.glyph === 'BADGE') e.style.color = onDark ? paper : ink;
          else e.style.color = inkLevel > 0.5 ? (inkP.accent || swap.accent ? accent : ink) : ink;
        }
        else { e.setAttribute('fill', inkP.accent || swap.accent ? accent : ink); e.setAttribute('fill-opacity', inkLevel.toFixed(4)); }
      }
      if (gl.extra.setFill) { const f = propAt(node, 'fill', lt); gl.extra.setFill(f.v, f.accent); }
      if (gl.extra.setGrow) gl.extra.setGrow(propAt(node, 'grow', lt).v);
      else if (ent.glyph !== 'BAR' && ent.glyph !== 'CHART_LINE') { const gr = propAt(node, 'grow', lt).v; if (gr !== 1) scale *= gr; }
      if (gl.count.length > 1) {
        const c = propAt(node, 'count', lt).v;
        gl.count.forEach((item, i) => {
          const k = clamp(c * gl.count.length - i, 0, 1);
          for (const e of item.els) e.style.opacity = EASE.outCubic(k).toFixed(4);
        });
      }
      if (gl.extra.countText) {
        const c = propAt(node, 'count', lt).v;
        gl.extra.countText.textContent = (gl.extra.countPrefix || '') + Math.round(c * gl.extra.countMax).toLocaleString('en-US') + (gl.extra.countSuffix || '');
        gl.extra.countText.setAttribute('fill-opacity', (c > 0 ? Math.min(1, c * 4) : 0).toFixed(4));
        if (gl.extra.growK !== undefined) {
          const topY = node.bb.y + node.bb.h - Math.max(ill.sw, gl.extra.growK * node.bb.h);
          gl.extra.countText.setAttribute('y', f2(topY - ill.sw));
        }
      }
      if (gl.strike) {
        const s = propAt(node, 'strike', lt);
        gl.strike.set(s.v);
        gl.strike.path.setAttribute('stroke', s.accent ? accent : ink);
      }
      if (gl.extra.halo) {
        const em = propAt(node, 'emit', lt);
        const live = activeOps(node, 'EMIT', lt)[0];
        let bloom = em.v > 0 ? 0.12 * em.v : 0, grow = 1.06;
        if (live) {
          const p = prog(lt, live.start_ms, live.end_ms);
          bloom = Math.max(bloom, 0.34 * EASE.pulse(p));
          grow = lerp(0.96, 1.22, EASE.outCubic(p));
          scale *= 1 + 0.035 * EASE.pulse(p);
        }
        gl.extra.halo.setAttribute('fill-opacity', bloom.toFixed(4));
        gl.extra.halo.style.transform = `scale(${grow.toFixed(4)})`;
      }
      if (gl.extra.rings) {
        const em = propAt(node, 'emit', lt);
        const live = activeOps(node, 'EMIT', lt)[0];
        const contained = Math.min(node.bb.w, node.bb.h) / 2;
        gl.extra.rings.forEach((ring, i, arr) => {
          let r, op;
          if (live) {
            const p = clamp((prog(lt, live.start_ms, live.end_ms) - i * 0.22) / (1 - 0.22 * (arr.length - 1)), 0, 1);
            r = lerp(gl.extra.R * 0.25, gl.extra.R, EASE.outCubic(p));
            op = p <= 0 ? 0 : (1 - p) * 0.9 + 0.1;
          } else {
            // Embers scale with the settled emit level and stay inside the entity so a
            // quiet halo never inflates the entity's box into the copy.
            r = contained * (0.3 + 0.55 * em.v) * (1 - i * 0.18);
            op = em.v > 0 ? 0.55 * em.v * (1 - i * 0.22) : 0;
          }
          ring.setAttribute('r', f2(r));
          ring.setAttribute('stroke-opacity', op.toFixed(4));
          ring.setAttribute('stroke', em.accent || live ? accent : ink);
        });
      }
      let transform = carryTransform(node, lt);
      // 'none' (never '') keeps the declaration at a stable position in the style attribute —
      // clearing then rewriting a decl moves it to the end, which makes the DOM differ across seek paths.
      if (ent.carry_from_bbox) {
        const from = ent.carry_from_bbox;
        const blur = velocityBlur(lt, 0, 420, EASE.inOutCubic, Math.hypot(from.x - node.bb.x, from.y - node.bb.y) + Math.abs(from.w - node.bb.w));
        g.style.filter = blur > 0.15 ? `blur(${blur.toFixed(2)}px)` : 'none';
      } else if (ent.enter_duration_ms) {
        const blur = velocityBlur(lt, ent.enter_ms, ent.enter_ms + ent.enter_duration_ms, EASE.outQuint, node.bb.h * 0.4);
        g.style.filter = blur > 0.15 ? `blur(${blur.toFixed(2)}px)` : 'none';
      }
      if (gl.extra.lens) {
        const p = lensPosition(node, ill, lt);
        gl.extra.lens.setAttribute('transform', `translate(${f2(p.x)} ${f2(p.y)})`);
      }
      if (ex) { opacity *= ex.opacity; ty += ex.ty; }
      const c = centre(node.bb);
      if (scale !== 1 || ty || tx || gl.extra.rotateDeg) transform += ` translate(${f2(c.x + tx)} ${f2(c.y + ty)}) scale(${scale.toFixed(4)})${gl.extra.rotateDeg ? ` rotate(${gl.extra.rotateDeg})` : ''} translate(${f2(-c.x)} ${f2(-c.y)})`;
      g.setAttribute('transform', transform.trim() || 'translate(0 0)');
      g.style.opacity = opacity.toFixed(4);
      // Connectors read this: a link is only as present as the bodies it joins.
      node.presence = preEntry ? 0 : dim;
      if (node.label) {
        const ls = node.label.wrap.style;
        ls.visibility = 'visible';
        // A chassis label belongs to its housing: it fades in with the DRAW, not ahead of it.
        ls.opacity = (gl.extra.chassis ? opacity * clamp(draw, 0, 1) : opacity).toFixed(4);
        const shift = carryLabelShift(node, lt);
        ls.transform = `translate(${f2(shift.x)}px, ${f2(ty + shift.y)}px) scale(${scale.toFixed(4)})`;
        node.label.text.style.color = node.label.inside && (inkLevel > 0.5 || ent.glyph === 'CHIP') ? paper : ink;
      }
      if (node.media) {
        applyMediaState(node.media, lt, beat, ctx);
        node.media.frame.style.opacity = (Number(node.media.frame.style.opacity || 1) * dim).toFixed(4);
      }
      // Pre-entry entities still run the full property pipeline above so seek() produces the
      // same driven-attribute set regardless of the path taken; only visibility is forced.
      if (preEntry) {
        g.style.visibility = 'hidden';
        if (node.label) node.label.wrap.style.visibility = 'hidden';
        if (node.media) node.media.frame.style.visibility = 'hidden';
      }
    }
    for (const r of ill.rels.values()) {
      if (!r.path) continue;
      const rel = r.rel, s = r.g.style;
      // Pre-entry still runs the pipeline (prog clamps to 0) so the arrow/bar/trace decls
      // are rewritten every visit — scrubbing back must produce the same DOM.
      s.visibility = lt < rel.enter_ms ? 'hidden' : 'visible';
      const pe = rel.enter_duration_ms ? prog(lt, rel.enter_ms, rel.enter_ms + rel.enter_duration_ms) : 1;
      const con = rel.drawn_by_op ? propAt(r, 'connect', lt).v : EASE.outQuint(pe);
      const conDriver = rel.drawn_by_op ? propDriver(r, 'connect', lt) : null;
      const wiping = Boolean(conDriver && conDriver.params && conDriver.params.wipe);
      if (wiping && r.path.setWipe) r.path.setWipe(con); else r.path.set(con);
      const dim = propAt(r, 'dim', lt).v;
      let opacity = dim * (rel.drawn_by_op ? 1 : Math.min(1, pe * 3));
      if (ex) opacity *= ex.opacity;
      // A link between an absent or dimmed body and anything else is a stray line: it inherits
      // the weaker endpoint's presence.
      const endA = ill.ents.get(rel.source), endB = ill.ents.get(rel.target);
      if (endA && endB) opacity *= Math.min(endA.presence == null ? 1 : endA.presence, endB.presence == null ? 1 : endB.presence);
      s.opacity = opacity.toFixed(4);
      // Under a wipe the endpoints belong to the sweep: a dot or arrowhead shows only while
      // the traveling window covers its end of the path, and is erased with the tail.
      let head = con >= 0.985 ? 1 : 0;
      let head0 = con > 0.02 ? 1 : 0;
      if (wiping) {
        const w = Math.max(10, r.len * 0.42), hd = con * (r.len + w), tl = hd - w;
        head = hd >= r.len - 0.5 && tl < r.len ? 1 : 0;
        head0 = hd > 0 && tl <= 0 ? 1 : 0;
      }
      if (r.arrow) r.arrow.style.opacity = String(head);
      if (r.bar) r.bar.style.opacity = String(head);
      if (r.dots) {
        r.dots[0].style.opacity = String(head0);
        r.dots[1].style.opacity = String(head);
        const dstroke = propAt(r, 'ink', lt);
        const dc = dstroke.v > 0.5 && dstroke.accent ? accent : ink;
        r.dots.forEach((d) => d.setAttribute('fill', dc));
      }
      const inkP = propAt(r, 'ink', lt);
      const stroke = inkP.v > 0.5 && inkP.accent ? accent : ink;
      r.path.path.setAttribute('stroke', stroke);
      if (r.arrow) r.arrow.setAttribute('stroke', stroke);
      const trace = activeOps(r, 'TRACE', lt)[0];
      if (trace) {
        const p = EASE.inOutCubic(prog(lt, trace.start_ms, trace.end_ms));
        r.trace.style.strokeDashoffset = `${f2(r.len * 0.18 - p * r.len * 1.18)}`;
        r.trace.setAttribute('stroke-opacity', EASE.pulse(p).toFixed(4));
      } else {
        r.trace.setAttribute('stroke-opacity', '0');
        // Write the rest offset unconditionally: a decl left over from an earlier seek
        // would make the DOM differ by path taken.
        r.trace.style.strokeDashoffset = f2(r.len * 0.18);
      }
      const st = propAt(r, 'strike', lt);
      r.strike.set(st.v);
      r.strike.path.setAttribute('stroke', st.accent ? accent : ink);
    }
  }

  // ---------------------------------------------------------------------------
  // Beat
  // ---------------------------------------------------------------------------
  function buildBeat(beat, plan, stage, opts, isLast, beatIndex) {
    const outer = el('div', { display: 'none', position: 'absolute', inset: '0', overflow: 'hidden' }, stage);
    outer.className = 'em2-beat';
    outer.dataset.beat = beat.beat_id;
    // Camera: every beat's picture lives inside a wrapper the film pushes/pans/dissolves as a whole.
    const root = el('div', { position: 'absolute', inset: '0', transformOrigin: '50% 50%', willChange: 'transform, opacity, filter' }, outer);
    const bg = buildBackground(beat, plan, root);
    const media = beat.media ? buildMedia(beat.media, plan, root, opts.assetUrl) : null;
    const figure = beat.figure ? buildFigure(beat.figure, plan, root, opts.peepsUrl) : null;
    const data = beat.data ? buildData(beat.data, plan, root) : null;
    const illustration = beat.illustration ? buildIllustration(beat.illustration, plan, root, opts) : null;
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
      motion: plan.motion || DEFAULT_MOTION,
      transition: tr,
      tonalInk: (plan.typography && plan.typography.tonal_ink) || 1,
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
        if (tr.mode === 'EVIDENCE_PERSISTENCE' || tr.mode === 'ILLUSTRATION_PERSISTENCE') {
          // Text leaves; the evidence or illustration stays for the next beat to inherit.
          if (role === 'media' || role === 'illustration') return null;
          const k = EASE.inCubic(p);
          return { opacity: 1 - k, tx: 0, ty: -k * 14 };
        }
        if (role === 'illustration') {
          const k = EASE.inCubic(clamp(p * 1.5, 0, 1));
          return { opacity: 1 - k, tx: 0, ty: -k * 8 };
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
    const ready = Promise.all([figure ? figure.ready : null, media ? mediaReady(media) : null, illustration ? illustration.ready : null]);
    return { beat, root: outer, cam: root, bg, media, figure, data, illustration, texts, ctx, ready, index: beatIndex };
  }

  // Film-level camera and cut treatment from the plan's motion profile. `k` is the outgoing beat's
  // progress through its transition (0 outside it); `arrive` is the incoming beat's progress through
  // the same window while it dresses underneath. Both are pure functions of time.
  function applyCamera(bn, lt, k, arrive, plan, preRoll) {
    const m = bn.ctx.motion, W = plan.canvas.w;
    const dur = Math.max(1, bn.beat.duration_ms);
    const p = clamp((lt + (preRoll || 0)) / dur, 0, 1);
    const dir = bn.index % 2 === 0 ? 1 : -1;
    // Slow push over the beat, panning a hair across so nothing is ever perfectly still.
    let scale = 1 + m.camera_push * p;
    let tx = dir * m.camera_pan_frac * W * (p - 0.5);
    let opacity = 1, blur = 0;
    if (m.transition === 'scale_through') {
      if (k > 0) { scale *= lerp(1, 1.1, EASE.inCubic(k)); blur += m.blur_px * EASE.inCubic(k); opacity = 1 - EASE.inOutCubic(k); }
      if (arrive != null) { scale *= lerp(0.92, 1, EASE.outCubic(arrive)); blur += m.blur_px * 0.5 * (1 - EASE.outCubic(arrive)); }
    } else if (m.transition === 'blur_dissolve') {
      if (k > 0) blur += m.blur_px * EASE.inCubic(k);
      if (arrive != null) blur += m.blur_px * 0.4 * (1 - EASE.outCubic(arrive));
    }
    const s = bn.cam.style;
    s.transform = `translate(${f2(tx)}px, 0px) scale(${scale.toFixed(4)})`;
    s.opacity = opacity.toFixed(4);
    s.filter = blur > 0.2 ? `blur(${blur.toFixed(2)}px)` : 'none';
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

  function applyBeat(bn, lt, stageFade, preRoll) {
    applyBackgroundState(bn.bg, lt, bn.beat, stageFade, preRoll);
    if (bn.media) applyMediaState(bn.media, lt, bn.beat, bn.ctx);
    if (bn.figure) applyFigureState(bn.figure, lt, bn.beat, bn.ctx);
    if (bn.data) applyDataState(bn.data, lt, bn.beat, bn.ctx);
    if (bn.illustration) applyIllustrationState(bn.illustration, lt, bn.beat, bn.ctx);
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

    // Surface finish: vendored monochrome grain tile over the whole film, stepping offsets ~every
    // 93ms like real film grain; a paper texture under everything when the brand asks for PAPER.
    const surf = plan.surfaces || {};
    const finish = plan.brand.finish || 'EDITORIAL_FLAT';
    if (surf.paper && surf.paper.path && finish === 'PAPER') {
      el('div', {
        position: 'absolute', inset: '0', zIndex: '0', pointerEvents: 'none',
        backgroundImage: `url(${opts.assetUrl(surf.paper.path)})`, backgroundSize: 'cover',
        opacity: '0.3', mixBlendMode: 'multiply',
      }, stage);
    }
    const beats = plan.beats.map((b, i) => buildBeat(b, plan, stage, opts, i === plan.beats.length - 1, i));
    // Beats that ran under the previous beat's transition get that overlap time back as a
    // furniture pre-roll at takeover — voice-anchored content keeps the plan's clock.
    beats.forEach((bn, i) => {
      const pt = i > 0 ? plan.beats[i - 1].transition : null;
      const prev = plan.beats[i - 1];
      bn.preRoll = pt && prev && prev.start_ms + prev.duration_ms === bn.beat.start_ms
        ? pt.end_ms - pt.start_ms
        : 0;
    });
    let grain = null;
    if (surf.grain && surf.grain.path) {
      grain = el('div', {
        position: 'absolute', inset: '0', zIndex: '30', pointerEvents: 'none',
        backgroundImage: `url(${opts.assetUrl(surf.grain.path)})`, backgroundSize: '256px 256px',
        mixBlendMode: 'multiply', opacity: finish === 'PAPER' ? '0.06' : '0.04',
      }, stage);
    }
    const duration = plan.duration_ms;
    let current = -1;
    let time = 0;
    let playing = false;
    let raf = 0;
    let t0 = 0;
    const perf = { frames: 0, total_ms: 0, max_ms: 0 };
    let currentOverlap = -1;

    function beatAt(ms) {
      for (let i = beats.length - 1; i >= 0; i -= 1) if (ms >= beats[i].beat.start_ms) return i;
      return 0;
    }

    function seek(ms) {
      time = clamp(ms, 0, duration);
      const idx = beatAt(time);
      const bn = beats[idx];
      const lt = time - bn.beat.start_ms;
      const tr = bn.beat.transition;
      // L-cut overlap: while the outgoing beat runs its exit transition, the incoming
      // beat's stage is already dressing underneath, so a cut lands on a set that is
      // mid-arrival — never on bare paper.
      const overlapIdx = tr && lt >= tr.start_ms && idx + 1 < beats.length ? idx + 1 : -1;
      if (idx !== current || overlapIdx !== currentOverlap) {
        // display, not visibility: children set their own visibility and would otherwise leak through.
        beats.forEach((b, i) => { b.root.style.display = i === idx || i === overlapIdx ? 'block' : 'none'; });
        bn.root.style.zIndex = overlapIdx >= 0 ? '1' : '';
        if (overlapIdx >= 0) beats[overlapIdx].root.style.zIndex = '0';
        current = idx;
        currentOverlap = overlapIdx;
      }
      const stageFade = overlapIdx >= 0 ? 1 - EASE.inOutCubic(prog(lt, tr.start_ms, tr.end_ms)) : 1;
      if (grain) {
        const OFF = [[0, 0], [41, 17], [23, 88], [97, 53], [61, 131], [13, 73], [109, 29], [73, 107]];
        const o = OFF[Math.floor(time / 93) % OFF.length];
        grain.style.backgroundPosition = `${-o[0]}px ${-o[1]}px`;
      }
      const t1 = performance.now();
      const kOut = overlapIdx >= 0 ? prog(lt, tr.start_ms, tr.end_ms) : 0;
      applyBeat(bn, lt, stageFade, bn.preRoll);
      applyCamera(bn, lt, kOut, null, plan, bn.preRoll);
      if (overlapIdx >= 0) {
        const nb = beats[overlapIdx];
        applyBeat(nb, lt - tr.start_ms, 1, 0);
        applyCamera(nb, lt - tr.start_ms, 0, kOut, plan, 0);
      }
      const dt = performance.now() - t1;
      perf.frames += 1;
      perf.total_ms += dt;
      if (dt > perf.max_ms) perf.max_ms = dt;
      const waits = [];
      const collectMedia = (b) => {
        if (!b) return;
        if (b.media && b.media.pending) waits.push(b.media.pending);
        if (b.illustration) for (const e of b.illustration.ents.values()) if (e.media && e.media.pending) waits.push(e.media.pending);
      };
      collectMedia(bn);
      if (overlapIdx >= 0) collectMedia(beats[overlapIdx]);
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
      // Scene-graph update cost per seek (script side only; paint is the compositor's).
      get perf() { return { frames: perf.frames, avg_ms: perf.frames ? perf.total_ms / perf.frames : 0, max_ms: perf.max_ms }; },
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

  return { createEditorialFilm, RUNTIME_VERSION, EASE, _internals: { prog, lineStagger, recolor, propAt, pointAlong, polyLength, OP_PROPERTY, PROPERTY_REST } };
});
