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

  const RUNTIME_VERSION = 'EDITORIAL_RUNTIME_V3.2';
  const STRESS_SCALE = 1.045; // mirrors typefit.STRESS_SCALE: the compiler reserves this width for stressed words
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const prog = (t, s, e) => (e <= s ? (t >= e ? 1 : 0) : clamp((t - s) / (e - s), 0, 1));

  const DEFAULT_MOTION = { entrance: 'settle', stagger_ms: 90, camera_push: 0, camera_pan_frac: 0, transition: 'blur_dissolve', blur_px: 0, word_landing: 'tonal',
    spring: 'settle', breathe: 0.006, label_lag_ms: 0, motion_blur: 1 };
  const CARRY_MS = 420;      // a carried body travels to its new box in this long
  const BREATHE_PERIOD_MS = 4000;

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

  // Spring solver. Closed-form response of a unit mass launched one unit short of rest, so every
  // arrival is a pure function of normalised time — seekable, no simulation state. `zeta` is the
  // damping ratio: under 1 the body overshoots and rings down, 1 is critically damped (never
  // crosses). `launch` is the initial velocity as a fraction of the natural frequency — a body
  // thrown toward rest rather than released, which is what a hand-keyed AE arrival looks like.
  // Frequency is chosen so the residual at t=1 is SPRING_TOL; the last sliver is closed
  // linearly so the curve ends exactly at 1 without a step.
  const SPRING_TOL = 0.01;
  const SPRING_LAUNCH = 0.35;
  function springCurve(zeta, launch) {
    const v = launch == null ? SPRING_LAUNCH : launch;
    let raw;
    if (zeta >= 1) {
      let w = 6.64; // e^-w (1+w) = SPRING_TOL
      for (let i = 0; i < 8; i += 1) w -= (Math.exp(-w) * (1 + w) - SPRING_TOL) / (-Math.exp(-w) * w);
      raw = (t) => 1 - Math.exp(-w * t) * (1 + (w - v * w) * t);
    } else {
      const w = -Math.log(SPRING_TOL) / zeta;
      const wd = w * Math.sqrt(1 - zeta * zeta);
      const k = (zeta * w - v * w) / wd;
      raw = (t) => 1 - Math.exp(-zeta * w * t) * (Math.cos(wd * t) + k * Math.sin(wd * t));
    }
    const end = raw(1);
    return (t) => (t <= 0 ? 0 : t >= 1 ? 1 : raw(t) + (1 - end) * t);
  }
  // Presets: snap rings once (~9% over at t≈0.5), settle barely crosses (~1%), float never does.
  const SPRING = { snap: springCurve(0.62), settle: springCurve(0.74), float: springCurve(1) };
  const springOf = (motion, role) => SPRING[role === 'arrive' ? (SPRING[motion.spring] ? motion.spring : 'settle') : role] || SPRING.settle;

  function hash01(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i += 1) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return h / 4294967295;
  }

  // Secondary motion: once a node's own program has settled it keeps a slow, tiny drift so holds
  // read as living stills rather than frozen frames. Pure function of lt — fully deterministic.
  // `breathe` is the idle scale amplitude (profile-driven; phase offset per id so held elements never breathe in unison).
  function ambientDrift(lt, id, settledAt, amp, breathe) {
    const ramp = EASE.outCubic(prog(lt, settledAt, settledAt + 750));
    if (ramp <= 0) return { dx: 0, dy: 0, s: 1 };
    const ph = hash01(String(id)) * Math.PI * 2;
    const w = (Math.PI * 2) / 3800;
    const wb = (Math.PI * 2) / BREATHE_PERIOD_MS;
    return {
      dx: amp * ramp * Math.sin(lt * w + ph),
      dy: amp * 0.72 * ramp * Math.sin(lt * w * 1.31 + ph * 1.63),
      s: 1 + (breathe == null ? 0.006 : breathe) * ramp * Math.sin(lt * wb + ph * 0.53),
    };
  }

  // Authorship inspection thresholds (see inspect()): a carried mark must cover a real share of
  // its box and stay inside it; a connector reads as present above CONNECTOR_SHOWN_MIN while a
  // body below ENDPOINT_PRESENT_MIN reads as absent.
  const ICON_FILL_MIN = 0.2;
  const ICON_OVERFLOW_MAX = 0.25;
  const CONNECTOR_SHOWN_MIN = 0.25;
  const ENDPOINT_PRESENT_MIN = 0.2;

  // Motion blur. A 180° shutter smears half a frame of travel: the per-axis blur radius is
  // the distance a body moved since the previous frame, less a threshold that keeps idle
  // drift crisp. Directional, so a lateral move smears sideways and a drop smears downward.
  const BLUR_THRESHOLD_PX = 1.5;
  const BLUR_MAX_PX = 16;
  function motionBlurStd(dxFrame, dyFrame, gain) {
    const g = 0.5 * (gain == null ? 1 : gain);
    return {
      x: clamp((Math.abs(dxFrame) - BLUR_THRESHOLD_PX) * g, 0, BLUR_MAX_PX),
      y: clamp((Math.abs(dyFrame) - BLUR_THRESHOLD_PX) * g, 0, BLUR_MAX_PX),
    };
  }
  // Travel over the last frame along an eased path of length (distX, distY).
  function pathBlur(lt, s, e, easeFn, distX, distY, frameMs, gain) {
    if (lt <= s || lt > e) return { x: 0, y: 0 };
    const dv = easeFn(prog(lt, s, e)) - easeFn(prog(lt - frameMs, s, e));
    return motionBlurStd(dv * distX, dv * distY, gain);
  }
  // One SVG <filter> per moving node, shared by SVG and HTML bodies alike; set() rewrites the
  // deviation every frame and clears the filter decl when the body is still.
  function motionBlurFilter(defs, id) {
    const filter = svgEl('filter', { id, x: '-40%', y: '-40%', width: '180%', height: '180%', 'color-interpolation-filters': 'sRGB' }, defs);
    const blur = svgEl('feGaussianBlur', { stdDeviation: '0 0' }, filter);
    const url = `url(#${id})`;
    return {
      apply(style, std, extra) {
        const on = std.x > 0.05 || std.y > 0.05;
        if (on) blur.setAttribute('stdDeviation', `${std.x.toFixed(2)} ${std.y.toFixed(2)}`);
        style.filter = on ? (extra ? `${extra} ${url}` : url) : (extra || 'none');
      },
    };
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
      document.fonts.load(`700 40px "${f.display}"`),
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

    // Motion blur while the block travels, along the axis it travels: the entry slide or rise,
    // and the exit lift (the transition carrier is clipped, not moved, so it stays sharp).
    let std = { x: 0, y: 0 };
    if (enter && enter.end_ms > enter.start_ms) {
      const slide = enter.event === 'DECISIVE_SLIDE';
      std = pathBlur(lt, enter.start_ms, enter.end_ms, EASE.outQuint, slide ? node.bb.w * 0.07 : 0, slide ? 0 : em * 0.5, ctx.frameMs, ctx.motion.motion_blur);
    }
    if (ex && ex.ty) {
      const tr = ctx.transition;
      const exitStd = pathBlur(lt, tr.start_ms, tr.end_ms, EASE.inCubic, 0, 14 * 1.5, ctx.frameMs, ctx.motion.motion_blur);
      std = { x: Math.max(std.x, exitStd.x), y: Math.max(std.y, exitStd.y) };
    }
    if (node.blur) node.blur.apply(w, std); else w.filter = 'none';

    // Hero copy breathes after its program settles — applied to the text node so block geometry never moves.
    if (b.role === 'hero') {
      const heroS = ambientDrift(lt, `hero-${i}`, (node.cascade ? (b.cascade_end_ms || 0) : (enter ? enter.end_ms : 0)) + 320, 0, Math.min(ctx.motion.breathe, 0.006)).s;
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
      case 'bloom': {
        // The light source: a wide soft ellipse of the atmosphere's bloom tint behind the beat's hero.
        // Drawn centred on its own box and positioned by transform so it can travel from the previous
        // beat's light and breathe without re-painting the gradient.
        const atmo = plan.atmosphere || {};
        const rx = spec.radius.x, ry = spec.radius.y;
        const tint = atmo.bloom || brand.accent || brand.ink;
        const peak = atmo.bloom_opacity == null ? 0.15 : atmo.bloom_opacity;
        // Gaussian-like falloff sampled at five stops: no visible edge, no hot core.
        const stops = [[0, 1], [22, 0.78], [44, 0.38], [66, 0.11], [88, 0]]
          .map(([at, k]) => `${rgbaOf(tint, peak * k)} ${at}%`).join(', ');
        node = el('div', {
          position: 'absolute', left: px(-rx), top: px(-ry), width: px(rx * 2), height: px(ry * 2),
          background: `radial-gradient(ellipse at 50% 50%, ${stops})`,
          transformOrigin: '50% 50%', pointerEvents: 'none',
        }, parent);
        node.className = 'em2-bloom';
        break;
      }
      case 'depth': {
        // Far-plane room: a large defocused disc or tile in a field tint. It moves against the camera
        // at its plane depth (parallax) and never sharpens — it is out of focus by construction.
        const atmo = plan.atmosphere || {};
        const tint = (atmo.depth_tints || [])[spec.tint] || mixColor(brand.paper, brand.ink, 0.1);
        node = el('div', {
          position: 'absolute', left: px(b.x), top: px(b.y), width: px(b.w), height: px(b.h),
          background: tint, borderRadius: spec.shape === 'disc' ? '50%' : px(Math.min(b.w, b.h) * 0.24),
          filter: `blur(${px(spec.blur_px)})`, transformOrigin: '50% 50%', pointerEvents: 'none',
        }, parent);
        node.className = 'em2-depth';
        node.dataset.plane = String(spec.plane);
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
    const atmo = plan.atmosphere || {};
    const layer = el('div', { position: 'absolute', inset: '0', zIndex: '1', background: atmo.field || brand.paper }, beatRoot);
    const layers = (Array.isArray(bg.layers) ? bg.layers : []).map((spec, i) => buildBgLayer(spec, plan, layer, i)).filter((l) => l.node);
    // Vignette: the field darkens toward its edges by the atmosphere's strength so the paper reads as a
    // lit surface, not a void; the dark variant leans on it harder because it has no bloom contrast to spare.
    const vig = atmo.vignette_opacity == null ? 0.03 : atmo.vignette_opacity;
    const vc = atmo.vignette || brand.ink;
    el('div', {
      position: 'absolute', inset: '0', pointerEvents: 'none',
      background: `radial-gradient(ellipse 85% 80% at 50% 45%, ${rgbaOf(vc, 0)} 52%, ${rgbaOf(vc, vig * 0.45)} 82%, ${rgbaOf(vc, vig)} 100%)`,
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
      let scale = 1, tx = 0, ty = 0, opacity = (spec.opacity == null ? 1 : spec.opacity) * p;
      if (spec.kind === 'panel' || spec.kind === 'plane' || spec.kind === 'spotlight') scale = lerp(0.985, 1, EASE.settle(p));
      if (spec.kind === 'dotgrid' || spec.kind === 'plane') {
        const amb = ambientDrift(lt, `bg-${beat.beat_id}-${L.i}`, holdStart, spec.kind === 'dotgrid' ? 2.8 : 1.6);
        tx += amb.dx; ty += amb.dy;
      }
      if (spec.kind === 'bloom') {
        // The light is already on when the beat starts (it was lit for the previous hero) and travels to
        // this hero over the travel window on a settle curve, then breathes: slow, wide, never still.
        // Keyed to the beat's own clock, not the pre-rolled one: under the outgoing transition the
        // light still sits where the previous beat left it, so the hand-over is seamless.
        const k = EASE.settle(prog(lt, 0, spec.travel_ms || 640));
        const amb = ambientDrift(lt, `bloom-${beat.beat_id}`, 0, 9, 0.03);
        tx = lerp(spec.from.x, spec.at.x, k) + amb.dx;
        ty = lerp(spec.from.y, spec.at.y, k) + amb.dy;
        scale = amb.s;
        opacity = spec.opacity == null ? 1 : spec.opacity;
      }
      if (spec.kind === 'depth') {
        // Far plane: fades up with the stage, then drifts more slowly and more widely than anything in
        // focus. The camera adds its counter-move (parallax) after this pass.
        const amb = ambientDrift(lt, `depth-${beat.beat_id}-${L.i}`, 0, 4.5 * (1 - spec.plane) + 1.5, 0.012);
        tx += amb.dx; ty += amb.dy;
        scale = amb.s * lerp(1.04, 1, EASE.settle(p));
      }
      if (spec.rotation_deg) s.rotate = `${spec.rotation_deg}deg`;
      s.opacity = opacity.toFixed(4);
      L.base = { tx, ty, scale };
      s.transform = `translate(${f2(tx)}px, ${f2(ty)}px) scale(${scale.toFixed(4)})`;
    }
  }

  function applyDepthParallax(bgNode, pose, plan) {
    // A depth shape at plane d only receives d of the camera's move: the frame-fixed remainder is
    // undone here so the far plane slides against the content as the camera pushes or drifts.
    const W = plan.canvas.w, H = plan.canvas.h;
    for (const L of bgNode.layers) {
      if (L.spec.kind !== 'depth' || !L.base) continue;
      const d = L.spec.plane, b = L.spec.bbox;
      const cx = b.x + b.w / 2 - W / 2, cy = b.y + b.h / 2 - H / 2;
      const counter = 1 / (1 + (pose.scale - 1) * (1 - d));
      const ptx = -pose.tx * (1 - d) - (cx * (pose.scale - 1) * (1 - d)) / pose.scale;
      const pty = -(cy * (pose.scale - 1) * (1 - d)) / pose.scale;
      L.node.style.transform = `translate(${f2(L.base.tx + ptx)}px, ${f2(L.base.ty + pty)}px) scale(${(L.base.scale * counter).toFixed(4)})`;
    }
  }

  // ---------------------------------------------------------------------------
  // Media (customer-supplied image / video evidence)
  //
  // Every upload is presented inside a device slab — the benchmark's white-bezel handset,
  // screenshot slab, browser window or paper card — never as a bare rectangle. The compiler
  // chose the chassis from the asset's kind and aspect (or the author's param); the runtime
  // draws one housing language for all four so a film never mixes frame styles.
  // ---------------------------------------------------------------------------
  const CHASSIS_GEOMETRY = {
    // bezel: slab inset the screen sits behind (fraction of the slab's short side);
    // radius: outer corner radius; inner: screen corner radius (same unit).
    phone:   { bezel: 0.040, radius: 0.170, inner: 0.135 },
    shot:    { bezel: 0.030, radius: 0.075, inner: 0.048 },
    browser: { bezel: 0.030, radius: 0.075, inner: 0.048 },
    card:    { bezel: 0.030, radius: 0.060, inner: 0.036 },
  };
  const SLAB_FACE = 'linear-gradient(160deg, #fdfdfc 0%, #f2f1ee 100%)';
  const SCREEN_DARK = '#101012';
  // Living stills: a screenshot taller than its screen scrolls through; anything else drifts
  // in a slow push. Both are pure functions of lt so a seek lands on the same frame.
  const SCROLL_TALLER_THAN = 1.15;
  const SCROLL_MAX_TRAVEL_FRAC = 0.9;
  const KEN_BURNS_SCALE = 0.045;
  const SLAB_PARALLAX_DEG = 1.1;

  function buildMedia(media, plan, beatRoot, assetUrl) {
    const bb = bboxOf(media.bbox);
    const chassis = CHASSIS_GEOMETRY[media.chassis] ? media.chassis : 'shot';
    const geo = CHASSIS_GEOMETRY[chassis];
    const m0 = Math.min(bb.w, bb.h);
    const frame = el('div', {
      position: 'absolute', left: px(bb.x), top: px(bb.y), width: px(bb.w), height: px(bb.h), zIndex: '12',
      overflow: 'visible', willChange: 'transform, opacity, clip-path',
    }, beatRoot);
    frame.dataset.mediaAsset = media.asset_id;
    frame.dataset.chassis = chassis;
    const tilt = clamp(Number(media.tilt == null ? 0 : media.tilt), -14, 14);
    const housing = housingOf(plan);
    const shadowRgb = ((plan.atmosphere && plan.atmosphere.shadow_rgb) || [23, 18, 12]).join(',');
    const face = plan.atmosphere ? `linear-gradient(160deg, ${mixColor(housing.light, '#ffffff', 0.35)} 0%, ${housing.light} 100%)` : SLAB_FACE;
    // The slab carries the object's own attitude (tilt + parallax); the frame carries the motion.
    const slab = el('div', {
      position: 'absolute', left: '0', top: '0', width: '100%', height: '100%',
      borderRadius: px(m0 * geo.radius), background: face, transformOrigin: '50% 50%',
      transform: `rotate(${tilt.toFixed(2)}deg)`,
      boxShadow: [
        `0 ${px(bb.h * 0.055)} ${px(bb.h * 0.16)} rgba(${shadowRgb},0.30)`,
        `0 ${px(bb.h * 0.012)} ${px(bb.h * 0.03)} rgba(${shadowRgb},0.16)`,
        `inset 0 0 0 1px rgba(${shadowRgb},0.10)`,
        'inset 0 1px 0 rgba(255,255,255,0.9)',
        `0 1.5px 0 rgba(${shadowRgb},0.14)`,
      ].join(', '),
    }, frame);
    slab.className = 'em2-slab';
    const bezel = m0 * geo.bezel;
    const sw = bb.w - bezel * 2, sh = bb.h - bezel * 2;
    const pc = (v, of) => `${((v / of) * 100).toFixed(3)}%`;
    // Screen and viewport are proportional so a reframed (carried) slab keeps its bezel ratio.
    const screen = el('div', {
      position: 'absolute', left: pc(bezel, bb.w), top: pc(bezel, bb.h), width: pc(sw, bb.w), height: pc(sh, bb.h),
      borderRadius: px(m0 * geo.inner), overflow: 'hidden',
      background: chassis === 'card' ? '#ffffff' : SCREEN_DARK,
    }, slab);
    screen.className = 'em2-screen';
    let host = screen, hostW = sw, hostH = sh;
    if (chassis === 'browser') {
      // Window chrome inside the screen: a light bar with neutral controls and an address field.
      const barH = sh * 0.085;
      const bar = el('div', {
        position: 'absolute', left: '0', top: '0', width: '100%', height: pc(barH, sh), background: '#f4f3f1',
        borderBottom: '1px solid rgba(23,18,12,0.10)', display: 'flex', alignItems: 'center', gap: px(sw * 0.011),
        paddingLeft: px(sw * 0.028), boxSizing: 'border-box',
      }, screen);
      for (let i = 0; i < 3; i += 1) el('div', { width: px(barH * 0.32), height: px(barH * 0.32), borderRadius: '50%', background: 'rgba(23,18,12,0.16)', flex: 'none' }, bar);
      el('div', { flex: '0 1 58%', height: px(barH * 0.46), marginLeft: px(sw * 0.02), borderRadius: px(barH * 0.23), background: 'rgba(23,18,12,0.07)' }, bar);
      hostH = sh - barH;
      host = el('div', { position: 'absolute', left: '0', top: pc(barH, sh), width: '100%', height: pc(hostH, sh), overflow: 'hidden' }, screen);
    }
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
    Object.assign(node.style, { position: 'absolute', left: '0', top: '0', width: '100%', height: '100%', objectFit: 'cover', display: 'block', transformOrigin: '50% 50%' });
    host.appendChild(node);
    if (chassis === 'phone') {
      // Dynamic island: sits over the content, part of the device, never of the upload.
      el('div', {
        position: 'absolute', left: '50%', top: px(sh * 0.016), transform: 'translateX(-50%)',
        width: px(sw * 0.30), height: px(sh * 0.030), borderRadius: px(sh * 0.015), background: '#000', pointerEvents: 'none',
      }, screen);
    }
    // Glass: one soft diagonal highlight across the screen so the slab reads as a surface.
    el('div', {
      position: 'absolute', inset: '0', pointerEvents: 'none',
      background: 'linear-gradient(115deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.03) 30%, rgba(255,255,255,0) 46%)',
    }, screen);
    const m = { media, frame, slab, screen, node, bb, hostW, hostH, tilt, chassis, pending: null };
    layoutFocus(m, hostW, hostH);
    return m;
  }

  // Content life inside the screen. Stills that are much taller than their screen scroll
  // through it over the hold (a phone screenshot reads top-to-bottom); other stills take a
  // slow push. Authored focus crops and live video own their own geometry.
  function applyContentLife(m, lt, settledAt, endMs, hw, hh) {
    const md = m.media;
    if (md.focus || md.kind === 'VIDEO' || !md.source_size) return;
    const sw = md.source_size.w, sh = md.source_size.h;
    if (!sw || !sh) return;
    const span = Math.max(1, endMs - settledAt);
    const p = EASE.inOutCubic(prog(lt, settledAt, settledAt + span));
    const hostAr = hw / hh, srcAr = sw / sh;
    if (hostAr / srcAr > SCROLL_TALLER_THAN) {
      // Width-fit, so the still keeps its own ratio and only its vertical position moves.
      const h = hw / srcAr;
      const travel = Math.min(h - hh, hh * SCROLL_MAX_TRAVEL_FRAC);
      Object.assign(m.node.style, { objectFit: 'fill', width: px(hw), height: px(h), left: '0', top: px(-travel * p), transform: 'none' });
    } else {
      m.node.style.transform = `scale(${(1 + KEN_BURNS_SCALE * p).toFixed(4)})`;
    }
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

  // `ride` (entity-hosted media): the slab is the entity's body, so it takes the body's own pose —
  // pop spring, carry travel, dim — instead of the evidence panel's rise; the housing and its
  // content are one object throughout.
  function applyMediaState(m, lt, beat, ctx, ride) {
    const md = m.media;
    const s = m.frame.style;
    const chrome = md.chrome_ms == null ? md.enter_ms : md.chrome_ms;
    // Pre-chrome still runs the pipeline at p=0 so every driven decl is rewritten — same
    // seek-determinism rule as entities and relations.
    s.visibility = lt < chrome ? 'hidden' : 'visible';
    let tx = 0, ty = 0, opacity = 1, clip = null, sx = 1, sy = 1;
    m.node.style.opacity = '1';
    if (ride) {
      tx = ride.dx; ty = ride.dy; sx = ride.sx; sy = ride.sy; opacity = ride.opacity;
    } else {
      const pf = EASE.outQuint(prog(lt, chrome, chrome + Math.max(md.enter_duration_ms, 320)));
      if (md.enter_duration_ms > 0 || lt < md.enter_ms) {
        ty = (1 - pf) * m.bb.h * 0.08;
        clip = [0, 0, (1 - pf) * 100, 0];
        opacity = Math.min(1, pf * 1.6);
      }
    }
    let hw = m.hostW, hh = m.hostH;
    if (md.reframe) {
      const rp = EASE.inOutCubic(prog(lt, md.reframe.start_ms, md.reframe.end_ms));
      const from = bboxOf(md.reframe.from);
      const x = lerp(from.x, m.bb.x, rp), y = lerp(from.y, m.bb.y, rp);
      const w = lerp(from.w, m.bb.w, rp), h = lerp(from.h, m.bb.h, rp);
      s.left = px(x); s.top = px(y); s.width = px(w); s.height = px(h);
      hw = w * (m.hostW / m.bb.w); hh = h * (m.hostH / m.bb.h);
      layoutFocus(m, hw, hh);
      const std = pathBlur(lt, md.reframe.start_ms, md.reframe.end_ms, EASE.inOutCubic, Math.abs(from.x - m.bb.x) + Math.abs(from.w - m.bb.w) / 2, Math.abs(from.y - m.bb.y) + Math.abs(from.h - m.bb.h) / 2, ctx.frameMs, ctx.motion.motion_blur);
      if (m.blur) m.blur.apply(s, std); else s.filter = 'none';
    }
    // Ambient: after the frame has settled it drifts with the hold, a living still.
    const settledAt = md.reframe ? md.reframe.end_ms : md.enter_ms + (md.enter_duration_ms || 0);
    applyContentLife(m, lt, settledAt, beat.duration_ms, hw, hh);
    // The slab is a physical object: a faint perspective sway on top of its authored tilt.
    const sway = ambientDrift(lt, `slab-${md.asset_id || md.role || 'x'}`, settledAt, 1, 0);
    m.slab.style.transform = `perspective(${px(m.bb.h * 4)}) rotateX(${(-sway.dy * SLAB_PARALLAX_DEG).toFixed(3)}deg) rotateY(${(sway.dx * SLAB_PARALLAX_DEG).toFixed(3)}deg) rotate(${m.tilt.toFixed(2)}deg)`;
    const tzM = beat.composition.text_zone;
    const gapM = Math.max(tzM.x - (m.bb.x + m.bb.w), m.bb.x - (tzM.x + tzM.w), tzM.y - (m.bb.y + m.bb.h), m.bb.y - (tzM.y + tzM.h));
    if (!ride) {
      const amb = ambientDrift(lt, `media-${md.asset_id || md.role || 'x'}`, settledAt, clamp(gapM * 0.35, 0, 1.1), Math.min(ctx.motion.breathe, 0.006));
      tx += amb.dx; ty += amb.dy;
    }
    // A ridden slab already carries its entity's exit; the evidence panel exits as media.
    const ex = ride ? null : ctx.exitState({ block: { role: 'media' } }, lt);
    if (ex) { opacity *= ex.opacity; ty += ex.ty; }
    s.opacity = clamp(opacity, 0, 1).toFixed(4);
    s.transformOrigin = '50% 50%';
    s.transform = `translate(${tx.toFixed(2)}px, ${ty.toFixed(2)}px) scale(${sx.toFixed(4)}, ${sy.toFixed(4)})`;
    if (ride) { if (m.blur) m.blur.apply(s, ride.blur); }
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
  // Every driven property arrives on a spring. Bounded properties (draw, fill, ink, dim, count,
  // emit, connect, strike) ride the critically damped one so they never cross their target;
  // GROW and SWAP are scale and may ring.
  const OP_SPRING = { DRAW: 'float', FILL: 'float', INK: 'float', DIM: 'float', GROW: 'settle', STRIKE: 'float', SWAP: 'settle', COUNT: 'float', EMIT: 'float', CONNECT: 'float' };

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

  // A concept the registry cannot draw is typeset inside its housing — the word, or the figure,
  // set as a designed mark. Measured with the real face so the fit is exact; a word that cannot
  // meet the floor at two lines becomes a monogram rather than a shrunken caption.
  const wordCanvas = document.createElement('canvas').getContext('2d');
  function textWidth(txt, fs, family, weight) {
    wordCanvas.font = `${weight} ${fs}px "${family}"`;
    return wordCanvas.measureText(txt).width;
  }
  function fitLines(word, box, family, weight, maxLines, floorFs, maxFs, tracking) {
    const words = word.split(' ');
    for (let lines = 1; lines <= Math.min(maxLines, words.length); lines += 1) {
      // Balanced split: the break that leaves the longest line shortest.
      let best = null;
      const splits = lines === 1 ? [[words.join(' ')]] : [];
      if (lines === 2) for (let i = 1; i < words.length; i += 1) splits.push([words.slice(0, i).join(' '), words.slice(i).join(' ')]);
      for (const ls of splits) {
        const fs = Math.min(maxFs, (box.h / lines) / 1.12, ...ls.map((l) => (box.w / (textWidth(l, 100, family, weight) / 100 + tracking * l.length))));
        if (!best || fs > best.fs) best = { lines: ls, fs };
      }
      if (best && best.fs >= floorFs) return best;
    }
    return null;
  }
  function wordMark(node, body, box, word, kind, fg, plan) {
    const numeric = kind === 'numeric';
    const family = numeric ? plan.fonts.families.data : plan.fonts.families.display;
    const weight = numeric ? '600' : '700';
    const tracking = numeric ? 0 : -0.015;
    let fit = kind === 'monogram' ? null : fitLines(word, box, family, weight, numeric ? 1 : 2, box.h * 0.2, box.h * (numeric ? 0.62 : 0.5), tracking);
    let set = kind;
    if (!fit) {
      const initials = word.split(/[\s-]+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join('');
      fit = fitLines(initials, box, family, '700', 1, 1, box.h * 0.6, 0.02);
      set = 'monogram';
    }
    const lh = fit.fs * 1.08, total = lh * fit.lines.length;
    const g = svgEl('g', { 'data-word': set }, body);
    fit.lines.forEach((l, i) => {
      const t = svgEl('text', {
        x: f2(box.x + box.w / 2), y: f2(box.y + box.h / 2 - total / 2 + lh * i + lh * 0.5), 'text-anchor': 'middle', 'dominant-baseline': 'central',
        'font-size': f2(fit.fs), 'font-family': family, 'font-weight': weight, fill: fg, 'letter-spacing': f2(fit.fs * tracking),
        'font-variant-numeric': numeric ? 'tabular-nums' : undefined,
      }, g);
      t.textContent = l;
    });
    node.extra.wordBox = box;
    return g;
  }

  // Registry icon loaded into a box inside a glyph group; each part joins the entity's
  // draw-on program (stroke packs dash-draw, fill packs stagger in).
  function loadIconInto(ent, node, host, box, opts) {
    node.extra.iconBox = box;
    host.setAttribute('data-icon-host', ent.id);
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

  // Housing surfaces every chassis draws with, from the film's atmosphere: `light` is the field's own
  // lifted surface, `dark` the contrasting one — so a dark-paper film gets the same grammar inverted.
  function housingOf(plan) {
    const h = plan.atmosphere && plan.atmosphere.housing;
    return h || { light: '#ffffff', dark: mixColor(plan.brand.ink, plan.brand.paper, 0.05) };
  }

  function buildGlyph(ent, il, plan, g, sw, opts) {
    const b = bboxOf(ent.bbox), ink = plan.brand.ink, paper = plan.brand.paper, accent = il.accent || ink;
    const housing = housingOf(plan);
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
        base.setAttribute('fill', dark ? housing.dark : housing.light);
        base.setAttribute('stroke', ink);
        base.setAttribute('stroke-width', f2(sw * 0.55));
        base.setAttribute('stroke-opacity', '0.55');
        node.extra.shadow = { el: base, oy: b.h * 0.07, blur: b.h * 0.13, alpha: 0.28 };
        if (!dark) {
          // Gloss: a light slope across the top half so the tile reads as enamel, not paper.
          svgEl('path', {
            d: `M${f2(b.x + sw / 2)} ${f2(b.y + r + sw / 2)}Q${f2(b.x + sw / 2)} ${f2(b.y + sw / 2)} ${f2(b.x + r + sw / 2)} ${f2(b.y + sw / 2)}L${f2(b.x + b.w - r - sw / 2)} ${f2(b.y + sw / 2)}Q${f2(b.x + b.w - sw / 2)} ${f2(b.y + sw / 2)} ${f2(b.x + b.w - sw / 2)} ${f2(b.y + r + sw / 2)}L${f2(b.x + b.w - sw / 2)} ${f2(b.y + b.h * 0.46)}Q${f2(b.x + b.w * 0.5)} ${f2(b.y + b.h * 0.62)} ${f2(b.x + sw / 2)} ${f2(b.y + b.h * 0.46)}Z`,
            fill: '#ffffff', 'fill-opacity': 0.5,
          }, body);
        }
        node.inkEls.push(svgEl('path', { d: roundRectPath({ x: b.x + sw / 2, y: b.y + sw / 2, w: b.w - sw, h: b.h - sw }, r) + 'Z', fill: accent, 'fill-opacity': 0 }, g));
        const word = params.word ? String(params.word) : '';
        const fg = dark ? paper : ink;
        if (ent.asset) {
          const host = svgEl('g', {}, g);
          host.style.color = fg;
          node.inkEls.push(host);
          node.extra.iconHost = host;
          const pad = b.w * 0.17;
          if (word) {
            // Composite: the mark takes the upper body, the concept's own name is set beneath it.
            const ih = b.h * 0.5;
            loadIconInto(ent, node, host, { x: b.x + (b.w - ih) / 2, y: b.y + pad * 0.8, w: ih, h: ih }, opts);
            wordMark(node, body, { x: b.x + pad * 0.6, y: b.y + pad * 0.8 + ih + b.h * 0.03, w: b.w - pad * 1.2, h: b.h - pad * 0.8 - ih - b.h * 0.03 - pad * 0.7 }, word, params.word_kind || 'name', fg, plan);
          } else {
            loadIconInto(ent, node, host, { x: b.x + pad, y: b.y + pad, w: b.w - pad * 2, h: b.h - pad * 2 }, opts);
          }
        } else if (word) {
          const pad = b.w * 0.14;
          wordMark(node, body, { x: b.x + pad, y: b.y + pad, w: b.w - pad * 2, h: b.h - pad * 2 }, word, params.word_kind || 'name', fg, plan);
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
        disc.setAttribute('fill', dark ? housing.dark : housing.light);
        disc.setAttribute('stroke', ink);
        disc.setAttribute('stroke-width', f2(sw * 0.4));
        disc.setAttribute('stroke-opacity', '0.18');
        node.extra.shadow = { el: disc, oy: R * 0.16, blur: R * 0.3, alpha: 0.26 };
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
        } else if (params.word) {
          // The disc's square inscribed in the circle carries the word or its monogram.
          const side = R * 1.28;
          wordMark(node, body, { x: c.x - side / 2, y: c.y - side / 2, w: side, h: side }, String(params.word), params.word_kind || 'name', dark ? paper : ink, plan);
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
        card.setAttribute('fill', dark ? housing.dark : housing.light);
        card.setAttribute('stroke', ink);
        card.setAttribute('stroke-width', f2(sw * 0.4));
        card.setAttribute('stroke-opacity', '0.18');
        node.extra.shadow = { el: card, oy: b.h * 0.08, blur: b.h * 0.16, alpha: 0.26 };
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
        row.setAttribute('fill', housing.dark);
        node.extra.shadow = { el: row, oy: b.h * 0.1, blur: b.h * 0.2, alpha: 0.3 };
        node.inkEls.push(svgEl('path', { d: roundRectPath({ x: b.x, y: b.y, w: b.w, h: b.h }, r) + 'Z', fill: accent, 'fill-opacity': 0 }, g));
        // Icon peg: a light tile clipped into the left end of the row.
        const peg = Math.min(b.h * 0.62, b.w * 0.14);
        const px0 = b.x + b.h * 0.19, py0 = b.y + (b.h - peg) / 2;
        svgEl('path', { d: roundRectPath({ x: px0, y: py0, w: peg, h: peg }, peg * 0.26) + 'Z', fill: paper }, body);
        if (ent.asset) {
          const host = svgEl('g', {}, g);
          host.style.color = ink;
          node.extra.iconHost = host;
          const pad = peg * 0.16;
          loadIconInto(ent, node, host, { x: px0 + pad, y: py0 + pad, w: peg - pad * 2, h: peg - pad * 2 }, opts);
        } else {
          // No mark: the peg carries the concept's monogram (or the figure), like a product avatar;
          // the name itself is the row's inside label.
          const word = String(params.word || ent.label || '');
          const pad = peg * 0.14;
          wordMark(node, body, { x: px0 + pad, y: py0 + pad, w: peg - pad * 2, h: peg - pad * 2 }, word, params.word_kind === 'numeric' ? 'numeric' : 'monogram', ink, plan);
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
    wrap.dataset.entity = ent.id;
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
      if (media) media.blur = motionBlurFilter(opts.fx.defs, `${opts.fx.scope}-mb-media-${ent.id}`);
      // Ambient life starts once the body has landed; a body waiting on a later op is still a
      // living still, not a freeze-frame.
      const settledAt = ent.enter_ms + (ent.enter_duration_ms || 0);
      const blur = motionBlurFilter(opts.fx.defs, `${opts.fx.scope}-mb-${ent.id}`);
      ents.set(ent.id, { ent, g, glyph, label, media, bb: bboxOf(ent.bbox), ops: opsFor.get(ent.id) || [], state: ent.state_in || {}, settledAt, blur });
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
        const p = SPRING[OP_SPRING[op.op]](prog(lt, op.start_ms, op.end_ms));
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

  // The motion-significant pose of a body at beat-local lt — carry travel, entrance spring and
  // rise — as a pure function of time, so the same evaluator gives the body, its lagging label,
  // the connectors tied to it, and (sampled one frame back) its motion blur.
  //   carry: {sx, sy, dx, dy} the carry reframe about the body's own box (identity once landed)
  //   scale: entrance spring;  ty: entrance rise;  cx/cy: live centre after carry and rise
  function bodyPose(node, lt, motion) {
    const ent = node.ent, T = node.bb;
    const pop = motion.entrance === 'pop';
    const pEnt = ent.enter_duration_ms ? prog(lt, ent.enter_ms, ent.enter_ms + ent.enter_duration_ms) : 1;
    const arrive = springOf(motion, 'arrive')(pEnt);
    const scale = lerp(pop ? 0.6 : 0.94, 1, arrive);
    const ty = (1 - SPRING.settle(pEnt)) * T.h * (pop ? 0.1 : 0.04);
    const carry = { sx: 1, sy: 1, dx: 0, dy: 0 };
    const from = ent.carry_from_bbox;
    if (from) {
      const k = SPRING.float(prog(lt, 0, CARRY_MS));
      if (k < 1) {
        carry.sx = lerp(from.w / T.w, 1, k); carry.sy = lerp(from.h / T.h, 1, k);
        carry.dx = lerp(from.x + from.w / 2 - (T.x + T.w / 2), 0, k); carry.dy = lerp(from.y + from.h / 2 - (T.y + T.h / 2), 0, k);
      }
    }
    return { pEnt, scale, ty, carry, cx: T.x + T.w / 2 + carry.dx, cy: T.y + T.h / 2 + carry.dy + ty };
  }

  function carryTransform(node, carry) {
    if (carry.sx === 1 && carry.sy === 1 && carry.dx === 0 && carry.dy === 0) return '';
    const T = node.bb, cx = T.x + T.w / 2, cy = T.y + T.h / 2;
    return `translate(${f2(cx + carry.dx)} ${f2(cy + carry.dy)}) scale(${carry.sx.toFixed(4)} ${carry.sy.toFixed(4)}) translate(${f2(-cx)} ${f2(-cy)})`;
  }

  // The label rides its body through a carry reframe: same centre path, offset scaled with the
  // body, so it never sits at the destination while the body is still travelling.
  function carryLabelShift(node, carry) {
    if (!node.label) return { x: 0, y: 0 };
    const T = node.bb, cT = centre(T), L = centre(node.label.bb);
    return { x: carry.dx + (L.x - cT.x) * carry.sx - (L.x - cT.x), y: carry.dy + (L.y - cT.y) * carry.sy - (L.y - cT.y) };
  }

  // Motion blur of a body from the travel of its pose over the last frame; scale change reads as
  // travel at the body's rim.
  function bodyBlur(node, lt, ctx) {
    const now = bodyPose(node, lt, ctx.motion), was = bodyPose(node, lt - ctx.frameMs, ctx.motion);
    const T = node.bb;
    const dsx = Math.abs(now.scale * now.carry.sx - was.scale * was.carry.sx) * T.w / 2;
    const dsy = Math.abs(now.scale * now.carry.sy - was.scale * was.carry.sy) * T.h / 2;
    return motionBlurStd(now.cx - was.cx + dsx, now.cy - was.cy + dsy, ctx.motion.motion_blur);
  }

  function retension(path, offA, offB) {
    const a = offA || { dx: 0, dy: 0 }, b = offB || { dx: 0, dy: 0 };
    if (!a.dx && !a.dy && !b.dx && !b.dy) return 'translate(0 0)';
    const p0 = path[0], p1 = path[path.length - 1];
    const vx0 = p1[0] - p0[0], vy0 = p1[1] - p0[1], len0 = Math.hypot(vx0, vy0);
    if (len0 < 1) return `translate(${f2(a.dx)} ${f2(a.dy)})`;
    const vx1 = vx0 + b.dx - a.dx, vy1 = vy0 + b.dy - a.dy, len1 = Math.hypot(vx1, vy1);
    const rot = (Math.atan2(vy1, vx1) - Math.atan2(vy0, vx0)) * 180 / Math.PI;
    return `translate(${f2(p0[0] + a.dx)} ${f2(p0[1] + a.dy)}) rotate(${rot.toFixed(3)}) scale(${(len1 / len0).toFixed(4)}) translate(${f2(-p0[0])} ${f2(-p0[1])})`;
  }

  // A shadow cast by one light over the stage: it leans away from the canvas centre and lifts
  // with the body while it is still arriving.
  function castShadow(sh, cx, cy, canvas, pEnt, shadowRgb) {
    const lean = clamp((cx - canvas.w / 2) / (canvas.w / 2), -1, 1) * 0.35;
    const lift = 1 + 0.5 * (1 - pEnt);
    const rgb = (shadowRgb || [23, 18, 12]).join(',');
    sh.el.style.filter = `drop-shadow(${f2(sh.oy * lean)}px ${f2(sh.oy * lift)}px ${f2(sh.blur * lift)}px rgba(${rgb},${(sh.alpha / lift).toFixed(3)}))`;
  }

  function applyIllustrationState(ill, lt, beat, ctx) {
    const paper = ctx.brand.paper, ink = ctx.brand.ink, accent = ill.accent;
    const ex = ctx.exitState({ block: { role: 'illustration' } }, lt);
    for (const node of ill.ents.values()) {
      const ent = node.ent, g = node.g, gl = node.glyph;
      const preEntry = lt < ent.enter_ms;
      g.style.visibility = 'visible';
      const pose = bodyPose(node, lt, ctx.motion);
      const pEnt = pose.pEnt;
      const dim = propAt(node, 'dim', lt).v;
      const pop = ctx.motion.entrance === 'pop';
      // 'pop' entrance: the element springs from ~60% on the profile's spring with a short rise —
      // the benchmark's app-tile arrival; 'settle' is the editorial 94%→100% landing. Opacity
      // is never sprung: it ramps ahead of the body and cannot cross 1.
      let opacity = (pop ? Math.min(1, EASE.outCubic(pEnt) * 1.6) : EASE.outQuint(pEnt)) * dim;
      let scale = pose.scale;
      let ty = pose.ty;
      // Idle life once this entity's own program has fully run: a drift whose amplitude shrinks
      // with the gap to the text zone so it can never close on the copy, and a breath whose
      // amplitude is capped the same way.
      const tzA = beat.composition.text_zone;
      const gap = Math.max(tzA.x - (node.bb.x + node.bb.w), node.bb.x - (tzA.x + tzA.w), tzA.y - (node.bb.y + node.bb.h), node.bb.y - (tzA.y + tzA.h));
      const breathe = clamp((gap * 0.3) / Math.max(1, Math.max(node.bb.w, node.bb.h) / 2), 0.004, ctx.motion.breathe);
      const amb = ambientDrift(lt, ent.id, node.settledAt, clamp(gap * 0.35, 0, 1.4), breathe);
      let tx = amb.dx; ty += amb.dy; scale *= amb.s;

      // SETTLE: a small confirming pulse; SWAP: the entity pops through a scale-and-clip beat into its new state.
      for (const op of activeOps(node, 'SETTLE', lt)) scale *= 1 + 0.03 * EASE.pulse(prog(lt, op.start_ms, op.end_ms));
      const swap = propAt(node, 'swap', lt);
      if (swap.v > 0 && swap.v < 1) scale *= 1 + 0.08 * EASE.pulse(swap.v);

      const draw = propAt(node, 'draw', lt).v;
      node.drawV = draw;
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
      let transform = carryTransform(node, pose.carry);
      // Motion blur from the body's own travel over the last frame — directional, and 'none'
      // (never '') when still so the decl keeps a stable position in the style attribute.
      node.blur.apply(g.style, bodyBlur(node, lt, ctx));
      if (gl.extra.lens) {
        const p = lensPosition(node, ill, lt);
        gl.extra.lens.setAttribute('transform', `translate(${f2(p.x)} ${f2(p.y)})`);
      }
      if (ex) { opacity *= ex.opacity; ty += ex.ty; }
      const c = centre(node.bb);
      if (scale !== 1 || ty || tx || gl.extra.rotateDeg) transform += ` translate(${f2(c.x + tx)} ${f2(c.y + ty)}) scale(${scale.toFixed(4)})${gl.extra.rotateDeg ? ` rotate(${gl.extra.rotateDeg})` : ''} translate(${f2(-c.x)} ${f2(-c.y)})`;
      g.setAttribute('transform', transform.trim() || 'translate(0 0)');
      g.style.opacity = opacity.toFixed(4);
      if (gl.extra.shadow) castShadow(gl.extra.shadow, pose.cx + tx, pose.cy, ctx.canvas, pEnt, ctx.shadowRgb);
      // Connectors read these: a link is only as present as the bodies it joins, and it follows
      // them — the live offset of the body's centre from its laid-out box.
      node.presence = preEntry ? 0 : dim;
      node.offset = { dx: pose.carry.dx + tx, dy: pose.carry.dy + ty };
      if (node.label) {
        const ls = node.label.wrap.style;
        ls.visibility = 'visible';
        // Secondary motion: the label trails its body's arrival by the profile's lag, then rides
        // the same carry path so it never sits at the destination while the body is travelling.
        const lagged = ctx.motion.label_lag_ms > 0 && pEnt < 1 ? bodyPose(node, lt - ctx.motion.label_lag_ms, ctx.motion) : pose;
        const labelOpacity = (pop ? Math.min(1, EASE.outCubic(lagged.pEnt) * 1.6) : EASE.outQuint(lagged.pEnt)) * dim * (ex ? ex.opacity : 1);
        // A chassis label belongs to its housing: it fades in with the DRAW, not ahead of it.
        ls.opacity = clamp(gl.extra.chassis ? labelOpacity * clamp(draw, 0, 1) : labelOpacity, 0, 1).toFixed(4);
        const shift = carryLabelShift(node, pose.carry);
        const lScale = lagged.scale * amb.s;
        ls.transform = `translate(${f2(shift.x + tx)}px, ${f2(ty - pose.ty + lagged.ty + shift.y)}px) scale(${lScale.toFixed(4)})`;
        node.label.text.style.color = node.label.inside && (inkLevel > 0.5 || ent.glyph === 'CHIP') ? paper : ink;
      }
      if (node.media) {
        applyMediaState(node.media, lt, beat, ctx, {
          dx: pose.carry.dx + tx, dy: pose.carry.dy + ty,
          sx: scale * pose.carry.sx, sy: scale * pose.carry.sy,
          opacity, blur: bodyBlur(node, lt, ctx),
        });
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
      r.con = con;
      const dim = propAt(r, 'dim', lt).v;
      let opacity = dim * (rel.drawn_by_op ? 1 : Math.min(1, pe * 3));
      if (ex) opacity *= ex.opacity;
      // A link between an absent or dimmed body and anything else is a stray line: it inherits
      // the weaker endpoint's presence.
      const endA = ill.ents.get(rel.source), endB = ill.ents.get(rel.target);
      if (endA && endB) opacity *= Math.min(endA.presence == null ? 1 : endA.presence, endB.presence == null ? 1 : endB.presence);
      s.opacity = opacity.toFixed(4);
      // Re-tension: the link follows its bodies. A similarity transform maps the laid-out
      // endpoints onto the bodies' live centres, so a carried or drifting body never leaves
      // its connector behind.
      r.g.setAttribute('transform', retension(rel.path, endA && endA.offset, endB && endB.offset));
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
    // Motion-blur filters for this beat's moving bodies live in one hidden <defs>, scoped by
    // beat so ids never collide across beats.
    const fxSvg = svgEl('svg', { width: 0, height: 0, 'aria-hidden': 'true' }, outer);
    Object.assign(fxSvg.style, { position: 'absolute', width: '0', height: '0', overflow: 'hidden' });
    const fx = { defs: svgEl('defs', {}, fxSvg), scope: `em2fx-b${beatIndex}` };
    const bg = buildBackground(beat, plan, root);
    const media = beat.media ? buildMedia(beat.media, plan, root, opts.assetUrl) : null;
    if (media) media.blur = motionBlurFilter(fx.defs, `${fx.scope}-mb-media`);
    const figure = beat.figure ? buildFigure(beat.figure, plan, root, opts.peepsUrl) : null;
    const data = beat.data ? buildData(beat.data, plan, root) : null;
    const illustration = beat.illustration ? buildIllustration(beat.illustration, plan, root, { ...opts, fx }) : null;
    const texts = beat.typography.blocks.map((b, i) => Object.assign(buildTextBlock(b, plan, root), { blur: motionBlurFilter(fx.defs, `${fx.scope}-mb-text-${i}`) }));
    const camBlur = motionBlurFilter(fx.defs, `${fx.scope}-mb-camera`);
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
      shadowRgb: plan.atmosphere && plan.atmosphere.shadow_rgb,
      canvas: plan.canvas,
      frameMs: 1000 / (plan.fps || 30),
      motion: { ...DEFAULT_MOTION, ...(plan.motion || {}) },
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
    return { beat, root: outer, cam: root, camBlur, bg, media, figure, data, illustration, texts, ctx, ready, index: beatIndex };
  }

  // Film-level camera. Every cut is a matched move the compiler chose from the beats on either
  // side (transition.camera): the outgoing picture makes the move and the incoming picture
  // arrives out of the same move, so the two halves read as one camera. `k` is the outgoing
  // beat's progress through its transition (0 outside it); `arrival` is set on the incoming beat
  // while it dresses underneath: the outgoing beat's camera and the window it arrives over.
  // Plans without camera metadata fall back to the profile's transition name.
  const DRIFT_FRAC = 0.06;
  function cameraMoveOf(cam, m, index) {
    if (cam) return cam;
    return { move: m.transition === 'scale_through' ? 'push_through' : 'dissolve', dir: index % 2 === 0 ? 1 : -1, blur: 1 };
  }
  function applyCamera(bn, lt, k, arrival, plan, preRoll) {
    const m = bn.ctx.motion, W = plan.canvas.w;
    const dur = Math.max(1, bn.beat.duration_ms);
    const cam = cameraMoveOf(arrival ? arrival.camera : (bn.beat.transition && bn.beat.transition.camera), m, bn.index);
    const tr = bn.beat.transition;
    // Slow push over the beat, panning a hair across so nothing is ever perfectly still, then
    // the move itself. Pure in lt so the frame before can be sampled for blur.
    const poseAt = (t) => {
      const p = clamp((t + (preRoll || 0)) / dur, 0, 1);
      let scale = 1 + m.camera_push * p;
      let tx = cam.dir * m.camera_pan_frac * W * (p - 0.5);
      let opacity = 1, defocus = 0;
      const kk = k > 0 && tr ? prog(t, tr.start_ms, tr.end_ms) : 0;
      if (kk > 0) {
        const ko = EASE.inCubic(kk);
        if (cam.move === 'push_through') { scale *= lerp(1, 1.1, ko); defocus += m.blur_px * ko * cam.blur; opacity = 1 - EASE.inOutCubic(kk); }
        else if (cam.move === 'pull_back') { scale *= lerp(1, 0.94, ko); defocus += m.blur_px * 0.6 * ko * cam.blur; opacity = 1 - EASE.inOutCubic(kk); }
        else if (cam.move === 'drift') { tx += -cam.dir * W * DRIFT_FRAC * EASE.inOutCubic(kk); opacity = 1 - EASE.inOutCubic(kk); }
        else if (cam.move === 'dissolve') defocus += m.blur_px * ko * cam.blur;
      }
      if (arrival) {
        const aa = clamp(t / Math.max(1, arrival.window_ms), 0, 1);
        const ka = EASE.outCubic(aa);
        if (cam.move === 'push_through') { scale *= lerp(0.92, 1, ka); defocus += m.blur_px * 0.5 * (1 - ka) * cam.blur; }
        else if (cam.move === 'pull_back') { scale *= lerp(1.06, 1, ka); defocus += m.blur_px * 0.3 * (1 - ka) * cam.blur; }
        else if (cam.move === 'drift') tx += cam.dir * W * DRIFT_FRAC * (1 - EASE.inOutCubic(aa));
        else if (cam.move === 'dissolve') defocus += m.blur_px * 0.4 * (1 - ka) * cam.blur;
      }
      return { scale, tx, opacity, defocus };
    };
    const now = poseAt(lt), was = poseAt(lt - bn.ctx.frameMs);
    const s = bn.cam.style;
    s.transform = `translate(${f2(now.tx)}px, 0px) scale(${now.scale.toFixed(4)})`;
    s.opacity = now.opacity.toFixed(4);
    applyDepthParallax(bn.bg, now, plan);
    bn.camBlur.apply(s, motionBlurStd((now.tx - was.tx) + Math.abs(now.scale - was.scale) * W / 2, 0, m.motion_blur * cam.blur), now.defocus > 0.2 ? `blur(${now.defocus.toFixed(2)}px)` : '');
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
    const atmo = plan.atmosphere || {};
    const stage = el('div', { position: 'relative', overflow: 'hidden', width: px(W), height: px(H), background: atmo.field || plan.brand.paper, color: plan.brand.ink }, mount);
    stage.dataset.theme = atmo.theme || 'light';
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
        // Grain multiplies into a light field; a dark field would swallow it, so it screens instead.
        mixBlendMode: atmo.theme === 'dark' ? 'screen' : 'multiply',
        opacity: String(atmo.grain_opacity != null ? atmo.grain_opacity : (finish === 'PAPER' ? 0.06 : 0.04)),
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
        const hold = atmo.grain_hold_ms > 0 ? atmo.grain_hold_ms : 93;
        const o = OFF[Math.floor(time / hold) % OFF.length];
        grain.style.backgroundPosition = `${-o[0]}px ${-o[1]}px`;
      }
      const t1 = performance.now();
      const kOut = overlapIdx >= 0 ? prog(lt, tr.start_ms, tr.end_ms) : 0;
      applyBeat(bn, lt, stageFade, bn.preRoll);
      applyCamera(bn, lt, kOut, null, plan, bn.preRoll);
      if (overlapIdx >= 0) {
        const nb = beats[overlapIdx];
        applyBeat(nb, lt - tr.start_ms, 1, 0);
        applyCamera(nb, lt - tr.start_ms, 0, { camera: tr.camera || null, window_ms: tr.end_ms - tr.start_ms }, plan, 0);
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

    // Authorship inspection of the scene graph as seeked: what a viewer would read as a
    // generated tell, measured from the driven DOM rather than guessed from the plan.
    //   EMPTY_CHASSIS     a housing body is on stage with nothing inside it
    //   ICON_UNDERFILL    the carried mark renders as a sliver of the box it was given
    //   ICON_OVERFLOW     the carried mark leaks well outside its box (hostile viewBox)
    //   ORPHAN_CONNECTOR  a connector is visible while an endpoint body is not
    // Per-entity pose signatures let a frame walker find holds with no motion at all.
    const GRAPHIC = 'path,circle,ellipse,line,polyline,polygon,rect,text,image,use';
    function iconGeometry(node) {
      const host = node.glyph.extra.iconHost;
      if (!host) return null;
      const inner = host.firstElementChild;
      if (!inner) return null;
      // Painted extent in host space: the union of every graphic part that is not clipped or
      // masked (masked art may legitimately reach past the viewBox and be cut back to shape).
      let hostM;
      try { hostM = host.getScreenCTM(); } catch (e) { hostM = null; }
      if (!hostM) return null;
      const inv = hostM.inverse();
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (const el of inner.querySelectorAll(GRAPHIC)) {
        let a = el, cut = false;
        while (a && a !== host) { if (a.hasAttribute('mask') || a.hasAttribute('clip-path')) cut = true; a = a.parentNode; }
        if (cut || el.closest('defs,clipPath,mask,pattern,marker,symbol')) continue;
        let bb, m;
        try { bb = el.getBBox(); m = el.getScreenCTM(); } catch (e) { continue; }
        if (!m || !(bb.width > 0 || bb.height > 0)) continue;
        const M = inv.multiply(m);
        for (const [qx, qy] of [[bb.x, bb.y], [bb.x + bb.width, bb.y], [bb.x, bb.y + bb.height], [bb.x + bb.width, bb.y + bb.height]]) {
          const X = M.a * qx + M.c * qy + M.e, Y = M.b * qx + M.d * qy + M.f;
          x0 = Math.min(x0, X); y0 = Math.min(y0, Y); x1 = Math.max(x1, X); y1 = Math.max(y1, Y);
        }
      }
      if (!(x1 > x0 && y1 > y0)) return null;
      const box = node.glyph.extra.iconBox;
      const x = x0, y = y0, w = x1 - x0, h = y1 - y0;
      const ix = Math.max(0, Math.min(x + w, box.x + box.w) - Math.max(x, box.x));
      const iy = Math.max(0, Math.min(y + h, box.y + box.h) - Math.max(y, box.y));
      return {
        fill: (ix * iy) / (box.w * box.h),
        overflow: Math.max(box.x - x, box.y - y, x + w - (box.x + box.w), y + h - (box.y + box.h)) / Math.min(box.w, box.h),
      };
    }
    function inspect() {
      const out = { time, entities: {}, findings: [] };
      const flag = (code, beatId, id, detail) => out.findings.push({ code, beat_id: beatId, id, detail });
      const look = (bn) => {
        const ill = bn.illustration;
        if (!ill) return;
        const beatId = bn.beat.beat_id;
        for (const node of ill.ents.values()) {
          const g = node.g, gl = node.glyph;
          const op = Number(g.style.opacity);
          // Undrawn bodies (DRAW still ahead) are on the clock but not on the screen.
          const shown = g.style.visibility !== 'hidden' && op > 0.05 && !(node.drawV < 0.02);
          const key = `${beatId}:${node.ent.id}`;
          out.entities[key] = shown
            ? `${g.getAttribute('transform')}|${g.style.opacity}|${node.label ? node.label.wrap.style.transform : ''}`
            : null;
          if (!shown || !gl.extra.chassis) continue;
          const body = g.querySelector('[data-draw="body"]');
          const bodyOn = body && Number(body.style.opacity === '' ? 1 : body.style.opacity) * op > 0.15;
          if (!bodyOn) continue;
          const host = gl.extra.iconHost;
          const carried = host ? host.querySelectorAll(GRAPHIC).length : 0;
          const readout = gl.extra.countText || body.querySelector('text');
          const inside = node.label && node.label.inside;
          if (!carried && !readout && !inside) flag('EMPTY_CHASSIS', beatId, node.ent.id, `${node.ent.glyph} body on stage with nothing inside`);
          if (host && carried) {
            const geom = iconGeometry(node);
            if (geom && geom.fill < ICON_FILL_MIN) flag('ICON_UNDERFILL', beatId, node.ent.id, `mark covers ${(geom.fill * 100).toFixed(0)}% of its box`);
            if (geom && geom.overflow > ICON_OVERFLOW_MAX) flag('ICON_OVERFLOW', beatId, node.ent.id, `mark leaks ${(geom.overflow * 100).toFixed(0)}% of its box outside it`);
          }
        }
        for (const r of ill.rels.values()) {
          if (!r.path || !r.g) continue;
          const s = r.g.style;
          if (s.visibility === 'hidden' || Number(s.opacity) < CONNECTOR_SHOWN_MIN) continue;
          if (!(r.con > 0.02)) continue;
          for (const endId of [r.rel.source, r.rel.target]) {
            const end = ill.ents.get(endId);
            if (!end) continue;
            const eg = end.g;
            if (eg.style.visibility === 'hidden' || Number(eg.style.opacity) < ENDPOINT_PRESENT_MIN) {
              flag('ORPHAN_CONNECTOR', beatId, r.rel.id, `connector visible while ${endId} is not`);
            }
          }
        }
      };
      if (current >= 0) look(beats[current]);
      if (currentOverlap >= 0) look(beats[currentOverlap]);
      return out;
    }

    return {
      version: RUNTIME_VERSION,
      plan, stage, duration, fps: plan.fps, frames: Math.ceil((duration * plan.fps) / 1000),
      seek, frame, play, pause, fit, ready, inspect,
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
