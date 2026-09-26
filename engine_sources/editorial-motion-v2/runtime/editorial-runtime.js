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
    const s = String(hex).trim();
    const m = /^#?([0-9a-f]{6})$/i.exec(s);
    if (m) return [parseInt(m[1].slice(0, 2), 16), parseInt(m[1].slice(2, 4), 16), parseInt(m[1].slice(4, 6), 16)];
    // mixColor emits `rgb(r g b)` — parse it too instead of collapsing to black.
    const g = /^rgba?\(\s*(\d+)\s*[ ,]\s*(\d+)\s*[ ,]\s*(\d+)/i.exec(s);
    if (g) return [Number(g[1]), Number(g[2]), Number(g[3])];
    return [0, 0, 0];
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
@font-face{font-family:"EB Garamond";src:url("${fontBase}EBGaramond-var.woff2") format("woff2");font-weight:100 900;font-style:normal;font-display:block}
@font-face{font-family:"EB Garamond";src:url("${fontBase}EBGaramond-italic-var.woff2") format("woff2");font-weight:100 900;font-style:italic;font-display:block}
@font-face{font-family:"Playpen Sans";src:url("${fontBase}PlaypenSans-var.ttf") format("truetype");font-weight:100 800;font-style:normal;font-display:block}
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
      document.fonts.load(`600 40px "EB Garamond"`),
      document.fonts.load(`italic 400 40px "EB Garamond"`),
      document.fonts.load(`600 40px "Playpen Sans"`),
      document.fonts.load(`800 40px "Playpen Sans"`),
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
  // Scene-engine primitives: flat paper objects — a window, a hill, a planet — drawn as
  // svg silhouettes in the film's palette inside a 0..100 box (each with a hard shadow
  // from the 'piece' wrapper). The artist's vocabulary for "any environment".
  // ---------------------------------------------------------------------------
  function scenePiece(shape, seed, tone, plan) {
    const brand = plan.brand;
    const dk = (k) => mixColor(tone, '#000000', k);
    const lt = (k) => mixColor(tone, '#ffffff', k);
    const inkL = (k) => mixColor(brand.ink, tone, k);
    const paperTone = (k) => mixColor(brand.paper, tone, k);
    const svg = svgEl('svg', { viewBox: '0 0 100 100', preserveAspectRatio: 'none' });
    Object.assign(svg.style, { width: '100%', height: '100%', display: 'block', overflow: 'visible' });
    const r = rng(seed ^ 0x5a17);
    const P = (d, fill, op) => svgEl('path', { d, fill: fill || tone, 'fill-opacity': op == null ? 1 : op }, svg);
    const R = (x, y, w, h, fill, op) => svgEl('rect', { x: f2(x), y: f2(y), width: f2(w), height: f2(h), fill: fill || tone, 'fill-opacity': op == null ? 1 : op }, svg);
    const C = (cx, cy, rad, fill, op) => svgEl('circle', { cx: f2(cx), cy: f2(cy), r: f2(rad), fill: fill || tone, 'fill-opacity': op == null ? 1 : op }, svg);
    const E = (cx, cy, rx, ry, fill, op) => svgEl('ellipse', { cx: f2(cx), cy: f2(cy), rx: f2(rx), ry: f2(ry), fill: fill || tone, 'fill-opacity': op == null ? 1 : op }, svg);
    const speck = () => {
      // Gouache grain inside the silhouette: seeded pinpricks of paper showing through.
      for (let i = 0; i < 14; i++) {
        svgEl('circle', { cx: f2(8 + r() * 84), cy: f2(8 + r() * 84), r: f2(0.5 + r() * 0.9), fill: paperTone(0.9), 'fill-opacity': f2(0.10 + r() * 0.10) }, svg);
      }
    };
    switch (shape) {
      case 'sun': { C(50, 50, 26); for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; P(`M${f2(50 + Math.cos(a) * 34)} ${f2(50 + Math.sin(a) * 34)} L${f2(50 + Math.cos(a + 0.12) * 48)} ${f2(50 + Math.sin(a + 0.12) * 48)} L${f2(50 + Math.cos(a - 0.12) * 48)} ${f2(50 + Math.sin(a - 0.12) * 48)}Z`); } speck(); break; }
      case 'moon': { P('M50 12 A38 38 0 1 0 50 88 A30 38 0 1 1 50 12 Z'); C(38, 40, 5, dk(0.12), 0.5); C(58, 62, 3.4, dk(0.12), 0.5); break; }
      case 'planet': { C(50, 52, 30); P('M14 66 Q50 50 86 34 L86 44 Q50 60 14 76Z', lt(0.35), 0.9); C(42, 42, 7, lt(0.25), 0.6); speck(); break; }
      case 'disc': { C(50, 50, 44); speck(); break; }
      case 'star': { P('M50 8 L58 38 L90 40 L64 58 L73 90 L50 70 L27 90 L36 58 L10 40 L42 38 Z'); speck(); break; }
      case 'comet': { E(70, 50, 20, 9); P('M62 46 L4 50 L62 54Z'); P('M60 41 L20 38 L62 47Z', lt(0.4), 0.7); break; }
      case 'ring': { E(50, 50, 46, 14, 'none'); svgEl('ellipse', { cx: 50, cy: 50, rx: 46, ry: 14, fill: 'none', stroke: tone, 'stroke-width': 5 }, svg); break; }
      case 'cloud': { P('M8 72 Q2 52 22 50 Q20 32 42 32 Q52 18 68 30 Q88 26 90 46 Q98 58 88 70 L10 74Z'); speck(); break; }
      case 'hill': { P(`M0 100 L0 ${f2(70 - r() * 20)} Q${f2(30 + r() * 40)} ${f2(20 + r() * 30)} 100 ${f2(66 - r() * 18)} L100 100Z`); speck(); break; }
      case 'mountain': { P('M0 100 L38 20 L52 46 L68 14 L100 100Z'); P('M30 32 L38 20 L48 40 L42 38Z', paperTone(0.7)); P('M60 28 L68 14 L80 44 L70 40Z', paperTone(0.7)); speck(); break; }
      case 'cliff': { P(`M0 100 L0 ${f2(20 + r() * 15)} L${f2(30 + r() * 20)} ${f2(30 + r() * 10)} L${f2(50 + r() * 15)} 100Z`); speck(); break; }
      case 'rock': case 'stone': case 'pebble': { P(`M10 82 Q4 60 24 52 Q34 34 56 40 Q82 42 90 62 Q94 80 78 86 L14 88Z`); speck(); break; }
      case 'log': { R(4, 40, 92, 26); C(6, 53, 13, lt(0.3)); P('M20 40 L20 66 M46 40 L46 66 M70 40 L70 66', 'none'); for (const x of [20, 46, 70]) svgEl('line', { x1: x, y1: 42, x2: x, y2: 64, stroke: dk(0.3), 'stroke-width': 2 }, svg); break; }
      case 'house': { R(16, 44, 68, 56); P('M8 44 L50 12 L92 44Z', dk(0.25)); R(42, 66, 16, 34, dk(0.4)); R(24, 54, 12, 12, paperTone(0.8)); R(64, 54, 12, 12, paperTone(0.8)); break; }
      case 'hut': { P('M18 46 Q50 30 82 46 L82 88 L18 88Z'); P('M10 44 Q50 6 90 44 L82 46 Q50 16 18 46Z', dk(0.3)); R(44, 62, 13, 26, dk(0.4)); break; }
      case 'tent': { P('M8 92 L50 16 L92 92Z'); P('M50 16 L50 92 L92 92Z', dk(0.18)); P('M38 92 L50 62 L62 92Z', dk(0.45)); break; }
      case 'fence': { for (let i = 0; i < 6; i++) R(4 + i * 16, 20, 9, 66, i % 2 ? tone : dk(0.08)); R(0, 38, 100, 9, dk(0.15)); R(0, 62, 100, 9, dk(0.15)); break; }
      case 'sign': { R(46, 34, 8, 66); R(22, 10, 60, 30, lt(0.2)); R(26, 17, 52, 4, dk(0.2), 0.6); R(26, 26, 40, 4, dk(0.2), 0.6); break; }
      case 'window': { R(10, 8, 80, 84, paperTone(0.85)); R(14, 12, 72, 76, lt(0.55)); R(46, 12, 8, 76, paperTone(0.9)); R(14, 46, 72, 8, paperTone(0.9)); P('M10 8 L90 8 L90 92 L10 92Z M14 12 L14 88 L86 88 L86 12Z', tone); break; }
      case 'door': { P('M20 92 L20 26 Q20 10 50 10 Q80 10 80 26 L80 92Z'); C(70, 58, 3.4, dk(0.4)); P('M24 30 Q50 16 76 30 L76 36 Q50 24 24 36Z', dk(0.15)); break; }
      case 'table': { R(4, 34, 92, 9); R(10, 43, 8, 50, dk(0.2)); R(82, 43, 8, 50, dk(0.2)); break; }
      case 'chair': { R(18, 8, 10, 84); R(18, 44, 60, 10); R(24, 54, 9, 38, dk(0.15)); R(66, 54, 9, 38, dk(0.15)); break; }
      case 'stool': { E(50, 30, 34, 12); R(30, 38, 8, 52, dk(0.15)); R(62, 38, 8, 52, dk(0.15)); break; }
      case 'shelf': case 'beam': { R(0, 40, 100, 16); for (let i = 0; i < 4; i++) R(10 + i * 24, 18, 14, 22, lt(0.25 + (i % 2) * 0.15)); break; }
      case 'bookshelf': { R(6, 6, 88, 88, dk(0.15)); for (const yy of [12, 42, 72]) { for (let i = 0; i < 5; i++) R(12 + i * 15 + r() * 3, yy + r() * 4, 11, 20, i % 2 ? lt(0.3) : paperTone(0.6)); } break; }
      case 'lamp': { R(46, 40, 8, 50); P('M30 40 L40 8 L60 8 L70 40Z', lt(0.3)); E(50, 90, 20, 6, dk(0.25)); break; }
      case 'streetlamp': { R(46, 16, 8, 84); P('M38 16 Q50 2 62 16 L58 28 L42 28Z', lt(0.4)); C(50, 20, 6, paperTone(0.9)); break; }
      case 'rug': { E(50, 50, 48, 34); E(50, 50, 34, 22, dk(0.12)); E(50, 50, 20, 12, lt(0.2)); break; }
      case 'bed': { R(4, 50, 92, 34); R(4, 26, 12, 58, dk(0.2)); R(8, 30, 30, 16, paperTone(0.8)); R(42, 52, 52, 26, lt(0.25)); break; }
      case 'sofa': { R(10, 40, 80, 40); R(4, 30, 16, 54, dk(0.15)); R(80, 30, 16, 54, dk(0.15)); R(16, 36, 68, 16, lt(0.2)); break; }
      case 'poster': case 'frame': { R(16, 10, 68, 80, dk(0.2)); R(21, 15, 58, 70, paperTone(0.75)); P('M30 60 Q50 30 70 60Z', lt(0.4)); C(62, 32, 8, lt(0.5)); break; }
      case 'pot': { P('M28 44 L72 44 L66 92 L34 92Z'); R(24, 36, 52, 10, dk(0.15)); P('M50 36 Q36 14 26 20 Q40 22 50 36 M50 36 Q64 12 76 18 Q62 22 50 36', dk(0.35)); break; }
      case 'vase': { P('M40 30 L60 30 L66 46 L62 92 L38 92 L34 46Z'); break; }
      case 'curtain': { P('M14 6 L86 6 L82 94 L74 88 L66 94 L58 88 L50 94 L42 88 L34 94 L26 88 L18 94Z'); for (const x of [30, 50, 70]) P(`M${x} 8 L${x - 4} 90 L${x + 2} 90Z`, dk(0.12), 0.5); break; }
      case 'pillar': { R(24, 16, 52, 72); R(18, 8, 64, 10, lt(0.2)); R(18, 86, 64, 10, dk(0.2)); for (const x of [34, 50, 66]) P(`M${x - 3} 18 L${x - 3} 84 L${x + 3} 84 L${x + 3} 18Z`, dk(0.08)); break; }
      case 'arch': { P('M12 92 L12 40 Q50 4 88 40 L88 92 L74 92 L74 44 Q50 22 26 44 L26 92Z'); break; }
      case 'crate': { R(8, 20, 84, 72); P('M8 20 L92 92 M92 20 L8 92', 'none'); svgEl('line', { x1: 10, y1: 22, x2: 90, y2: 90, stroke: dk(0.3), 'stroke-width': 4 }, svg); svgEl('line', { x1: 90, y1: 22, x2: 10, y2: 90, stroke: dk(0.3), 'stroke-width': 4 }, svg); break; }
      case 'barrel': { E(50, 50, 40, 46); R(10, 32, 80, 10, dk(0.2), 0.6); R(10, 60, 80, 10, dk(0.2), 0.6); break; }
      case 'kelp': { for (const [ox, h] of [[-16, 80], [2, 95], [18, 70]]) { P(`M${f2(50 + ox)} 100 Q${f2(42 + ox)} ${f2(60 - h * 0.1)} ${f2(52 + ox)} ${f2(50 - h * 0.25)} Q${f2(62 + ox)} ${f2(45 - h * 0.3)} ${f2(50 + ox)} ${f2(100 - h)} L${f2(56 + ox)} ${f2(100 - h)} Q${f2(64 + ox)} ${f2(50 - h * 0.2)} ${f2(56 + ox)} ${f2(60 - h * 0.05)} L${f2(58 + ox)} 100Z`, mixColor(tone, brand.accent || tone, 0.4)); } break; }
      case 'coral': { for (const [ox, s] of [[-20, 0.9], [0, 1], [18, 0.8]]) { P(`M${f2(50 + ox)} 90 Q${f2(44 + ox)} 60 ${f2(50 + ox)} 44 L${f2(50 + ox)} ${f2(50 - 22 * s)} M${f2(50 + ox)} 66 Q${f2(60 + ox)} 58 ${f2(64 + ox)} ${f2(48 - 16 * s)} M${f2(50 + ox)} 72 Q${f2(38 + ox)} 66 ${f2(36 + ox)} ${f2(52 - 14 * s)}`, 'none'); svgEl('path', { d: `M${f2(50 + ox)} 90 Q${f2(44 + ox)} 60 ${f2(50 + ox)} 44 L${f2(50 + ox)} ${f2(50 - 22 * s)} M${f2(50 + ox)} 66 Q${f2(60 + ox)} 58 ${f2(64 + ox)} ${f2(48 - 16 * s)} M${f2(50 + ox)} 72 Q${f2(38 + ox)} 66 ${f2(36 + ox)} ${f2(52 - 14 * s)}`, stroke: tone, 'stroke-width': 7, fill: 'none', 'stroke-linecap': 'round' }, svg); } break; }
      case 'sandcastle': { R(20, 56, 60, 36); R(14, 40, 16, 52); R(70, 40, 16, 52); P('M14 40 L14 30 L22 36 L30 30 L30 40Z', dk(0.15)); P('M70 40 L70 30 L78 36 L86 30 L86 40Z', dk(0.15)); R(46, 66, 10, 26, dk(0.3)); break; }
      case 'building': case 'tower': { R(18, 6, 64, 90); for (let yy = 0; yy < 6; yy++) for (let xx = 0; xx < 3; xx++) if (r() < 0.5) R(24 + xx * 19, 12 + yy * 14, 10, 8, paperTone(0.85)); break; }
      case 'skyline': { let x = 0; while (x < 100) { const tw2 = 8 + r() * 10, th = 30 + r() * 68; R(x, 100 - th, tw2, th, tone); if (r() < 0.3) R(x + tw2 * 0.3, 100 - th - 8, tw2 * 0.4, 9, dk(0.2)); x += tw2 * (0.9 + r() * 0.3); } break; }
      case 'car': { P('M8 64 L16 44 L40 38 L70 38 L88 46 L94 64 L92 74 L8 74Z'); C(28, 74, 9, dk(0.45)); C(72, 74, 9, dk(0.45)); R(20, 46, 22, 12, paperTone(0.85)); R(50, 46, 24, 12, paperTone(0.85)); break; }
      case 'boat': { P('M10 62 L90 62 L78 84 L22 84Z'); R(48, 14, 5, 48, dk(0.3)); P('M53 16 L82 58 L53 58Z', paperTone(0.75)); P('M47 20 L22 58 L47 58Z', lt(0.3)); break; }
      case 'wave': { P(`M0 70 Q12 ${f2(55 + r() * 10)} 25 70 T50 70 T75 70 T100 70 L100 100 L0 100Z`); break; }
      case 'shaft': { P('M30 0 L70 0 L96 100 L4 100Z', tone, 0.9); break; }
      case 'tuft': { for (const [ox, lean, hh] of [[-22, -0.3, 74], [-8, -0.08, 96], [6, 0.1, 86], [20, 0.32, 66]]) { P(`M${f2(50 + ox)} 100 Q${f2(50 + ox + lean * 26)} ${f2(100 - hh * 0.55)} ${f2(50 + ox + lean * 40)} ${f2(100 - hh)} Q${f2(50 + ox + lean * 30)} ${f2(100 - hh * 0.5)} ${f2(52 + ox)} 100Z`, dk(0.06 * (Math.abs(ox) % 3))); } break; }
      case 'bush': { C(34, 66, 24); C(58, 56, 30); C(76, 70, 20); P('M8 100 L8 86 Q50 76 92 86 L92 100Z', dk(0.12)); speck(); break; }
      case 'flower': { for (let i = 0; i < 5; i++) { const a = i * Math.PI * 2 / 5 - Math.PI / 2; svgEl('ellipse', { cx: f2(50 + Math.cos(a) * 17), cy: f2(38 + Math.sin(a) * 15), rx: 10, ry: 8, fill: i % 2 ? tone : lt(0.18) }, svg); } C(50, 38, 9, paperTone(0.85)); P('M50 46 Q46 70 48 100 L54 100 Q52 70 50 46Z', dk(0.3)); P('M50 78 Q34 74 30 62 Q44 66 50 78Z', dk(0.25)); P('M50 84 Q66 80 70 68 Q56 72 50 84Z', dk(0.25)); break; }
      case 'bubble': { C(50, 50, 40, 'none'); svgEl('circle', { cx: 50, cy: 50, r: 40, fill: lt(0.5), 'fill-opacity': 0.22, stroke: lt(0.6), 'stroke-width': 4 }, svg); C(36, 34, 9, paperTone(0.9)); break; }
      case 'reed': { for (const [ox, hh, head] of [[-18, 78, 1], [2, 96, 1], [22, 62, 0]]) { P(`M${f2(50 + ox)} 100 Q${f2(48 + ox)} ${f2(100 - hh * 0.5)} ${f2(50 + ox)} ${f2(100 - hh)} L${f2(53 + ox)} ${f2(100 - hh)} Q${f2(51 + ox)} ${f2(100 - hh * 0.5)} ${f2(53 + ox)} 100Z`); if (head) E(50 + ox + 1.5, 100 - hh - 7, 7, 12, dk(0.35)); } break; }
      default: { P(cutBlobPath(50, 50, 42, 40, seed)); break; }
    }
    return svg;
  }

  // The silhouette shapes whose first path IS the whole body — those get interior
  // volume: a light wash on the lit half and an ink shade on the dark half, both
  // clipped to the silhouette so the shading lives inside the paper, not on the page.
  const _VOLUME_SHAPES = new Set(['hill', 'mountain', 'cliff', 'rock', 'stone', 'pebble',
    'tent', 'hut', 'door', 'boat', 'planet', 'moon', 'star', 'blob']);

  function shadeVolume(svg, ldx, seed, plan) {
    const brand = plan.brand;
    const silhouette = svg.querySelector('path');
    if (!silhouette) return;
    const cid = `vol_${(seed >>> 0).toString(36)}`;
    const cp = svgEl('clipPath', { id: cid }, svg);
    cp.appendChild(silhouette.cloneNode(true));
    const g = svgEl('g', { 'clip-path': `url(#${cid})` }, svg);
    if (ldx === 0) {
      // Overhead light: crown light, base shade.
      svgEl('rect', { x: -10, y: -10, width: 120, height: 34, fill: rgbaOf('#ffffff', 0.13) }, g);
      svgEl('rect', { x: -10, y: 62, width: 120, height: 50, fill: rgbaOf(brand.ink, 0.15) }, g);
    } else {
      const l = ldx < 0;
      svgEl('rect', { x: l ? -10 : 58, y: -10, width: 52, height: 120, fill: rgbaOf('#ffffff', 0.13) }, g);
      svgEl('rect', { x: l ? 58 : -10, y: -10, width: 52, height: 120, fill: rgbaOf(brand.ink, 0.15) }, g);
      // Core shadow band hugging the dark edge — deeper than the wash.
      svgEl('rect', { x: l ? 82 : -10, y: -10, width: 28, height: 120, fill: rgbaOf(brand.ink, 0.13) }, g);
    }
  }

  // ---------------------------------------------------------------------------
  // Background
  // ---------------------------------------------------------------------------
  function buildBgLayer(spec, plan, parent, idx, assetUrl) {
    const brand = plan.brand;
    const W = plan.canvas.w, H = plan.canvas.h;
    const b = spec.bbox;
    let node = null;
    // Paperbook plates are matte paper, not a lit field: glow furniture (blooms, spotlights,
    // defocused depth discs) never enters — its blurred blobs are what read as drifting
    // bubbles. Nor does editorial stage furniture (lifted panels, hairline boxes, dot
    // grids, ruled fields): a printed page carries its own stock, not a UI card.
    if (PAPERBOOK(plan) && (spec.kind === 'bloom' || spec.kind === 'spotlight' || spec.kind === 'depth'
      || spec.kind === 'panel' || spec.kind === 'hairline' || spec.kind === 'plane'
      || spec.kind === 'dotgrid' || spec.kind === 'ruled' || spec.kind === 'wash')) {
      return { spec, node: null, i: idx };
    }
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
      case 'band': {
        // Diorama plane: a cut-paper band spanning the stage at its parallax depth. `ragged`
        // gives the fill a torn top edge seeded by the compiler; a resolved mark perches on
        // that edge — a cut-out pinned to its own plane (the wrapper stays unclipped so the
        // mark can stand proud of the band).
        node = el('div', {
          position: 'absolute', left: px(b.x), top: px(b.y), width: px(b.w), height: px(b.h),
          transformOrigin: '50% 50%', pointerEvents: 'none',
        }, parent);
        // Painted-paper silhouette: an feTurbulence displacement wobbles the band's edges so it
        // reads torn/wet, not machine-cut. A shared field keeps the torn lip parallel to the edge.
        // Paperbook skips it — page stills clone the cam and url(#) filters do not paint inside
        // the clipped slot tree in capture; the torn clip-path profile carries the edge instead.
        const wraps = el('div', { position: 'absolute', inset: '0' }, node);
        if (!PAPERBOOK(plan)) {
          const tid = `em2tex${(spec.seed >>> 0).toString(36)}`;
          const texSvg = svgEl('svg', { width: '0', height: '0', viewBox: '0 0 1 1' }, node);
          Object.assign(texSvg.style, { position: 'absolute' });
          const texDefs = svgEl('defs', {}, texSvg);
          const texFilter = svgEl('filter', { id: tid, x: '-5%', y: '-30%', width: '110%', height: '160%' }, texDefs);
          svgEl('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.011 0.05', numOctaves: '2', seed: String(spec.seed % 89), result: 'n' }, texFilter);
          svgEl('feDisplacementMap', { in: 'SourceGraphic', in2: 'n', scale: f2(Math.min(b.h * 0.16, 13)), xChannelSelector: 'R', yChannelSelector: 'G' }, texFilter);
          wraps.style.filter = `url(#${tid})`;
        }
        const fill = el('div', { position: 'absolute', inset: '0', background: spec.tone }, wraps);
        if (PAPERBOOK(plan)) {
          // Matte gouache, hand-laid: url(#) filters do not paint inside the cloned slot
          // tree, so the pigment stack is pure CSS — a light slope, seeded sponge
          // blotches, pigment pooling toward the lower edge, a tonal halftone field
          // denser in the shadow half, then the sheet's fibre speckle.
          const br = rng(spec.seed ^ 0x51ab);
          const lt = mixColor(spec.tone, '#ffffff', 0.55);
          const dk = mixColor(spec.tone, '#000000', 0.5);
          const blot = [
            `linear-gradient(168deg, ${rgbaOf(lt, 0.16)} 0%, ${rgbaOf(spec.tone, 0)} 44%, ${rgbaOf(dk, 0.10)} 100%)`,
            `linear-gradient(180deg, ${rgbaOf(dk, 0)} 55%, ${rgbaOf(dk, 0.22)} 100%)`,
          ];
          for (let bi = 0; bi < 4; bi += 1) {
            const bx = b.w * (0.08 + 0.84 * br()), by = b.h * (0.12 + 0.76 * br());
            const bw2 = b.w * (0.24 + 0.34 * br()), bh2 = b.h * (0.5 + 0.5 * br());
            const ct = br() < 0.5 ? lt : dk;
            blot.push(`radial-gradient(ellipse ${px(bw2)} ${px(bh2)} at ${px(bx)} ${px(by)}, ${rgbaOf(ct, 0.10)}, ${rgbaOf(spec.tone, 0)} 68%)`);
          }
          fill.style.backgroundImage = blot.join(',');
          // Tonal halftone: a dot field masked to the shadow side — print texture that
          // dies out across the light, not a uniform screen.
          const half = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, fill);
          const dotDir = 120 + br() * 60;
          half.style.backgroundImage = `radial-gradient(circle, ${rgbaOf(dk, 0.5)} ${f2(b.w * 0.0035)}px, transparent ${f2(b.w * 0.0042)}px)`;
          half.style.backgroundSize = `${px(b.w * 0.028)} ${px(b.w * 0.028)}`;
          half.style.webkitMaskImage = `linear-gradient(${f2(dotDir)}deg, rgba(0,0,0,0.16), rgba(0,0,0,0) 62%)`;
          half.style.maskImage = half.style.webkitMaskImage;
          const fibre = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, fill);
          fibre.style.backgroundImage = pbSpeckle(plan);
          fibre.style.opacity = '0.5';
        } else {
          // Painted fill: a light slope plus two seeded blotches read as watercolour settling into
          // the paper rather than a flat vector field.
          const br = rng(spec.seed ^ 0x51ab);
          fill.style.backgroundImage = [
            `linear-gradient(165deg, ${rgbaOf(mixColor(spec.tone, '#ffffff', 0.5), 0.22)} 0%, ${rgbaOf(spec.tone, 0)} 42%, ${rgbaOf(mixColor(spec.tone, '#000000', 0.5), 0.14)} 100%)`,
            `radial-gradient(ellipse ${px(b.w * 0.5)} ${px(b.h * 0.9)} at ${px(b.w * (0.15 + 0.35 * br()))} ${px(b.h * (0.2 + 0.5 * br()))}, ${rgbaOf(mixColor(spec.tone, '#ffffff', 0.65), 0.2)}, ${rgbaOf(spec.tone, 0)} 70%)`,
            `radial-gradient(ellipse ${px(b.w * 0.42)} ${px(b.h * 0.8)} at ${px(b.w * (0.5 + 0.45 * br()))} ${px(b.h * (0.25 + 0.55 * br()))}, ${rgbaOf(mixColor(spec.tone, '#000000', 0.5), 0.14)}, ${rgbaOf(spec.tone, 0)} 70%)`,
          ].join(',');
        }
        if (spec.ragged) {
          const edge = Math.min(b.h * 0.3, Math.min(W, H) * 0.022);
          const er = rng(spec.seed ^ 0x7ab1);
          // One torn profile drives all three layers — the lip, the fill and the pool
          // share the same rip (low-freq wobble + hi-freq fuzz, scraps profile).
          const prof = edgeProfile(b.w, 'torn', edge, er, 0);
          const clip = (k, lift) => {
            let pts = `0px ${px(b.h)}`;
            for (const p of prof) pts += `,${px(p.t)} ${px(Math.max(0, b.h * 0.02 + edge * k - p.off * 0.5 - lift))}`;
            pts += `,${px(b.w)} ${px(b.h)}`;
            return `polygon(${pts})`;
          };
          // The exposed paper edge: the same tear, a sliver taller, in near-white behind the fill.
          const lip = el('div', { position: 'absolute', inset: '0', background: mixColor(brand.paper, '#ffffff', 0.55) }, wraps);
          lip.style.clipPath = clip(0.4, edge * 0.45);
          wraps.insertBefore(lip, fill);
          fill.style.clipPath = clip(0.4, 0);
          // Pigment pools along the torn edge and settles low — the band reads painted,
          // not filled.
          const pool = el('div', { position: 'absolute', inset: '0',
            background: `linear-gradient(180deg, ${rgbaOf(mixColor(spec.tone, '#000000', 0.4), 0)} 38%, ${rgbaOf(mixColor(spec.tone, '#000000', 0.4), 0.24)} 88%, ${rgbaOf(mixColor(spec.tone, '#000000', 0.5), 0.34)} 100%)` }, wraps);
          pool.style.clipPath = clip(0.52, 0);
        }
        if (spec.mark) {
          const mb = spec.mark.bbox;
          const mk = spec.mark.concept && paperArtKey(spec.mark.concept);
          if (mk) {
            // Perched illustration: the same composed collage as glyph marks — a
            // die-cut sticker pinned to its own plane.
            const pad = Math.max(4, mb.w * 0.06);
            const pw = mb.w + pad * 2, ph = mb.h + pad * 2;
            const psvg = svgEl('svg', { viewBox: `0 0 ${pw} ${ph}` }, node);
            Object.assign(psvg.style, { position: 'absolute', left: px(mb.x - b.x - pad), top: px(mb.y - b.y - pad), width: px(pw), height: px(ph), overflow: 'visible', pointerEvents: 'none', filter: `drop-shadow(0 ${px(ph * 0.03)} ${px(ph * 0.05)} ${rgbaOf(brand.ink, 0.22)})` });
            const art = paperArtGroup(mk, spec.seed ^ 0x7e5, plan, `bm_${(spec.seed >>> 0).toString(36)}`);
            if (art) {
              const inner = svgEl('g', { transform: `translate(${f2(pad)} ${f2(pad)}) scale(${f2(mb.w / 100)} ${f2(mb.h / 100)})` }, psvg);
              inner.appendChild(art.g);
            }
          } else {
            // Fallback silhouette: a wobbly paper edge peeks out from under the art.
            const pad = Math.max(6, mb.w * 0.2);
            const pw = mb.w + pad * 2, ph = mb.h + pad * 2;
            const psvg = svgEl('svg', { viewBox: `0 0 ${pw} ${ph}` }, node);
            Object.assign(psvg.style, { position: 'absolute', left: px(mb.x - b.x - pad), top: px(mb.y - b.y - pad), width: px(pw), height: px(ph), overflow: 'visible', pointerEvents: 'none', filter: `drop-shadow(0 ${px(ph * 0.03)} ${px(ph * 0.05)} ${rgbaOf(brand.ink, 0.22)})` });
            svgEl('path', { d: cutBlobPath(pw / 2, ph / 2, pw * 0.46, ph * 0.46, spec.seed ^ 0x7e5), fill: mixColor(brand.paper, '#ffffff', 0.7), 'fill-opacity': 0.95 }, psvg);
            const img = el('img', {
              position: 'absolute', left: px(mb.x - b.x), top: px(mb.y - b.y),
              width: px(mb.w), height: px(mb.h), opacity: '0.9', pointerEvents: 'none',
            }, node);
            img.src = assetUrl ? assetUrl(spec.mark.path) : spec.mark.path;
            img.style.filter = `blur(${((1 - spec.plane) * 1.6).toFixed(2)}px)`;
          }
        }
        node.className = 'em2-band';
        node.dataset.plane = String(spec.plane);
        break;
      }
      case 'piece': {
        // Scene-engine primitive: one flat paper object of the environment — a window, a hill,
        // a planet, kelp — cut in the film's palette with a hard offset shadow. `art` pieces are
        // resolved concept marks standing in the world instead of a primitive shape.
        // lit_dx: the page's single light source — a pale offset silhouette peeks past the lit
        // edge (rim light), the ink shadow falls to the dark side. Shape-following via CSS
        // drop-shadow, safe inside leaf clones.
        const pb = spec.bbox;
        const k0 = Math.min(W, H);
        const ldx = typeof spec.lit_dx === 'number' ? spec.lit_dx : null;
        const shx = -(ldx || 0) * k0 * 0.006 + k0 * 0.002;
        const rims = [];
        if (ldx !== null) {
          rims.push(ldx !== 0
            ? `drop-shadow(${px(ldx * k0 * 0.006)} ${px(-k0 * 0.004)} 0 ${rgbaOf('#ffffff', 0.33)})`
            : `drop-shadow(0 ${px(-k0 * 0.005)} 0 ${rgbaOf('#ffffff', 0.26)})`);
        }
        rims.push(`drop-shadow(${px(shx)} ${px(k0 * 0.009)} 0 ${rgbaOf(brand.ink, 0.28)})`);
        node = el('div', {
          position: 'absolute', left: px(pb.x), top: px(pb.y), width: px(pb.w), height: px(pb.h),
          transformOrigin: '50% 100%', pointerEvents: 'none',
          filter: rims.join(' '),
        }, parent);
        if (spec.contact) {
          // Contact shadow: a soft ink pool the object stands in, offset to the dark side.
          el('div', {
            position: 'absolute', left: '6%', bottom: '-3%', width: '88%', height: '14%',
            background: `radial-gradient(ellipse at center, ${rgbaOf(brand.ink, 0.24)}, ${rgbaOf(brand.ink, 0)} 68%)`,
            transform: `translateX(${px(-(ldx || 0) * k0 * 0.006)})`, pointerEvents: 'none',
          }, node);
        }
        if (spec.shape === 'art') {
          const art = spec.concept && paperArtKey(spec.concept);
          if (art) {
            const psvg = svgEl('svg', { viewBox: `0 0 ${pb.w} ${pb.h}` }, node);
            Object.assign(psvg.style, { width: '100%', height: '100%', overflow: 'visible' });
            const g = paperArtGroup(art, spec.seed, plan, `sp_${(spec.seed >>> 0).toString(36)}`);
            if (g && g.g) {
              const inner = svgEl('g', { transform: `scale(${f2(pb.w / 100)} ${f2(pb.h / 100)})` }, psvg);
              inner.appendChild(g.g);
            }
          } else if (spec.asset && spec.asset.path) {
            const img = el('img', { position: 'absolute', inset: '0', width: '100%', height: '100%', opacity: '0.9' }, node);
            img.src = assetUrl ? assetUrl(spec.asset.path) : spec.asset.path;
          }
        } else {
          const body = scenePiece(spec.shape, spec.seed, spec.tone, plan);
          if (body) {
            if (ldx !== null && _VOLUME_SHAPES.has(spec.shape)) shadeVolume(body, ldx, spec.seed, plan);
            node.appendChild(body);
          }
        }
        node.className = 'em2-piece';
        node.dataset.plane = String(spec.plane);
        break;
      }
      case 'stars': {
        // A seeded scatter of cut-paper stars — tiny diamonds and dots, matte ink-on-paper,
        // no glow. Parallax-barely-moving (near plane 0) so the field sits still behind all.
        node = svgEl('svg', { viewBox: `0 0 ${spec.bbox.w} ${spec.bbox.h}` }, parent);
        Object.assign(node.style, { position: 'absolute', left: px(spec.bbox.x), top: px(spec.bbox.y), width: px(spec.bbox.w), height: px(spec.bbox.h), pointerEvents: 'none' });
        const sr = rng(spec.seed);
        for (let i = 0; i < spec.count; i++) {
          const sx = sr() * spec.bbox.w, sy = sr() * spec.bbox.h, r = (0.6 + sr() * 2.1) * (Math.min(W, H) / 720);
          const st = sr() < 0.22
            ? svgEl('path', { d: `M${f2(sx)} ${f2(sy - r * 2)} L${f2(sx + r * 0.55)} ${f2(sy - r * 0.55)} L${f2(sx + r * 2)} ${f2(sy)} L${f2(sx + r * 0.55)} ${f2(sy + r * 0.55)} L${f2(sx)} ${f2(sy + r * 2)} L${f2(sx - r * 0.55)} ${f2(sy + r * 0.55)} L${f2(sx - r * 2)} ${f2(sy)} L${f2(sx - r * 0.55)} ${f2(sy - r * 0.55)}Z`, fill: mixColor(brand.paper, '#ffffff', 0.7), 'fill-opacity': f2(0.55 + sr() * 0.4) }, node)
            : svgEl('circle', { cx: f2(sx), cy: f2(sy), r: f2(r), fill: mixColor(brand.paper, '#ffffff', 0.7), 'fill-opacity': f2(0.35 + sr() * 0.5) }, node);
          // Twinkle tags: seek() pulses each star on its own phase.
          st.dataset.ph = f2(sr());
          st.dataset.o = st.getAttribute('fill-opacity');
        }
        node.setAttribute('class', 'em2-stars');
        node.setAttribute('data-plane', String(spec.plane));
        break;
      }
      case 'shaft': {
        // A light shaft is a sheet of translucent vellum-cut paper, not a beam of photons —
        // flat pale strip, tilted, in front of the deep planes.
        node = el('div', {
          position: 'absolute', left: px(spec.bbox.x), top: px(spec.bbox.y), width: px(spec.bbox.w), height: px(spec.bbox.h),
          background: rgbaOf(spec.tone, 0.16), pointerEvents: 'none',
          transform: `rotate(${f2(spec.tilt_deg)}deg)`, transformOrigin: '50% 0%',
        }, parent);
        node.className = 'em2-shaft';
        node.dataset.plane = String(spec.plane);
        break;
      }
      case 'windows': {
        // Urban silhouette: a strip of cut towers with lit windows — the night-city read.
        node = svgEl('svg', { viewBox: `0 0 ${spec.bbox.w} ${spec.bbox.h}`, preserveAspectRatio: 'none' }, parent);
        Object.assign(node.style, { position: 'absolute', left: px(spec.bbox.x), top: px(spec.bbox.y), width: px(spec.bbox.w), height: px(spec.bbox.h), pointerEvents: 'none' });
        const wr = rng(spec.seed), bw2 = spec.bbox.w, bh2 = spec.bbox.h;
        let cx2 = 0;
        const towers = [];
        while (cx2 < bw2) {
          const tw = bw2 * (0.07 + wr() * 0.09);
          const th = bh2 * (0.45 + wr() * 0.55);
          towers.push({ x: cx2, w: tw, h: th });
          cx2 += tw * (0.82 + wr() * 0.30);
        }
        for (const t of towers) {
          svgEl('rect', { x: f2(t.x), y: f2(bh2 - t.h), width: f2(t.w), height: f2(t.h), fill: spec.tone }, node);
          if (spec.silhouette) {
            const cols = Math.max(1, Math.floor(t.w / (spec.bbox.w * 0.022)));
            const rows = Math.max(2, Math.floor(t.h / (spec.bbox.h * 0.13)));
            for (let ry = 0; ry < rows; ry++) for (let cxr = 0; cxr < cols; cxr++) {
              if (wr() < 0.30) {
                const lit = svgEl('rect', {
                  x: f2(t.x + t.w * 0.14 + cxr * (t.w * 0.72 / cols)), y: f2(bh2 - t.h + t.h * 0.10 + ry * (t.h * 0.8 / rows)),
                  width: f2(t.w * 0.10), height: f2(t.h * 0.10), fill: spec.lit, 'fill-opacity': f2(0.5 + wr() * 0.5),
                }, node);
                lit.dataset.lit = '1'; lit.dataset.ph = f2(wr()); lit.dataset.o = lit.getAttribute('fill-opacity');
              }
            }
          }
        }
        node.setAttribute('class', 'em2-windows');
        node.setAttribute('data-plane', String(spec.plane));
        if (typeof spec.lit_dx === 'number' && spec.lit_dx !== 0) {
          const wk = Math.min(W, H);
          node.style.filter = `drop-shadow(${px(spec.lit_dx * wk * 0.004)} ${px(-wk * 0.003)} 0 ${rgbaOf('#ffffff', 0.24)}) drop-shadow(${px(-spec.lit_dx * wk * 0.005)} ${px(wk * 0.007)} 0 ${rgbaOf(brand.ink, 0.30)})`;
        }
        break;
      }
      case 'rain': {
        // Falling rain: a field of slanted paper streaks. Children carry data-ph
        // (phase) so seek() loops each drop's fall — deterministic at any frame.
        node = svgEl('svg', { viewBox: `0 0 ${spec.bbox.w} ${spec.bbox.h}`, preserveAspectRatio: 'none' }, parent);
        Object.assign(node.style, { position: 'absolute', left: px(spec.bbox.x), top: px(spec.bbox.y), width: px(spec.bbox.w), height: px(spec.bbox.h), pointerEvents: 'none' });
        const rr = rng(spec.seed);
        const slant = spec.bbox.h * 0.045;
        for (let i = 0; i < spec.count; i++) {
          const rx = rr() * spec.bbox.w, ry = rr() * spec.bbox.h, rl = spec.bbox.h * (0.035 + rr() * 0.05);
          const drop = svgEl('line', {
            x1: f2(rx), y1: f2(ry), x2: f2(rx + slant), y2: f2(ry + rl),
            stroke: spec.tone, 'stroke-width': f2(Math.min(W, H) * 0.0016), 'stroke-linecap': 'round', 'stroke-opacity': f2(0.3 + rr() * 0.4),
          }, node);
          drop.dataset.ph = f2(rr());
          drop.dataset.sp = f2(0.55 + rr() * 0.5);
        }
        node.setAttribute('class', 'em2-rain');
        node.dataset.plane = String(spec.plane);
        break;
      }
      case 'birds': {
        // Distant birds crossing the sky — small paired-wing strokes that fly and flap.
        node = svgEl('svg', { viewBox: `0 0 ${spec.bbox.w} ${spec.bbox.h}`, preserveAspectRatio: 'none' }, parent);
        Object.assign(node.style, { position: 'absolute', left: px(spec.bbox.x), top: px(spec.bbox.y), width: px(spec.bbox.w), height: px(spec.bbox.h), pointerEvents: 'none' });
        const vr = rng(spec.seed);
        for (let i = 0; i < spec.count; i++) {
          const bs = spec.bbox.w * (0.008 + vr() * 0.008);
          const bird = svgEl('path', {
            d: `M${f2(-bs)} 0 Q${f2(-bs * 0.5)} ${f2(-bs * 0.55)} 0 0 Q${f2(bs * 0.5)} ${f2(-bs * 0.55)} ${f2(bs)} 0`,
            fill: 'none', stroke: spec.tone, 'stroke-width': f2(bs * 0.16), 'stroke-linecap': 'round',
          }, node);
          bird.dataset.ph = f2(vr());
          bird.dataset.sp = f2(0.35 + vr() * 0.4);
          bird.dataset.y = f2(vr() * spec.bbox.h);
          bird.dataset.s = f2(bs);
        }
        node.setAttribute('class', 'em2-birds');
        node.dataset.plane = String(spec.plane);
        break;
      }
      case 'fireflies': {
        // Wandering sparks — small discs that drift and pulse while the page is read.
        node = svgEl('svg', { viewBox: `0 0 ${spec.bbox.w} ${spec.bbox.h}`, preserveAspectRatio: 'none' }, parent);
        Object.assign(node.style, { position: 'absolute', left: px(spec.bbox.x), top: px(spec.bbox.y), width: px(spec.bbox.w), height: px(spec.bbox.h), pointerEvents: 'none' });
        const fr = rng(spec.seed);
        for (let i = 0; i < spec.count; i++) {
          const fly = svgEl('circle', {
            cx: f2(fr() * spec.bbox.w), cy: f2(fr() * spec.bbox.h), r: f2(Math.min(W, H) * (0.004 + fr() * 0.004)),
            fill: spec.tone, 'fill-opacity': f2(0.5 + fr() * 0.4),
          }, node);
          fly.dataset.ph = f2(fr());
          fly.dataset.sp = f2(0.5 + fr() * 0.6);
          fly.dataset.ox = fly.getAttribute('cx'); fly.dataset.oy = fly.getAttribute('cy');
          fly.dataset.o = fly.getAttribute('fill-opacity');
        }
        node.setAttribute('class', 'em2-fireflies');
        node.dataset.plane = String(spec.plane);
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

  function buildBackground(beat, plan, beatRoot, assetUrl) {
    const bg = beat.composition.background || {};
    const brand = plan.brand;
    const atmo = plan.atmosphere || {};
    const layer = el('div', { position: 'absolute', inset: '0', zIndex: '1', background: atmo.field || brand.paper }, beatRoot);
    const layers = (Array.isArray(bg.layers) ? bg.layers : []).map((spec, i) => buildBgLayer(spec, plan, layer, i, assetUrl)).filter((l) => l.node);
    // Book-mode sky: when the authored diorama leaves the page's upper region bare, a tall washed
    // band drops from the page top to the first horizon — every spread reads as a full painted
    // plate, not a sticker field on empty paper.
    if (plan.book) {
      const pr = bookPageRect(plan);
      const bands = (Array.isArray(bg.layers) ? bg.layers : []).filter((s) => s.kind === 'band');
      if (pr) {
        const horizon = bands.length ? Math.min(...bands.map((s) => s.bbox.y)) : pr.y + pr.h;
        if (horizon > pr.y + pr.h * 0.4) {
          const field = atmo.field || brand.paper;
          const topBand = bands.reduce((a, s) => (a && a.bbox.y <= s.bbox.y ? a : s), null);
          const tone = topBand ? mixColor(topBand.tone, field, 0.55) : mixColor(field, brand.accent || brand.ink, 0.14);
          const sky = buildBgLayer(
            { kind: 'band', bbox: { x: -W * 0.05, y: -H * 0.02, w: W * 1.1, h: horizon + H * 0.04 }, tone, seed: seedHash(`${beat.beat_id}-sky`), plane: 0.14, opacity: 0.85 },
            plan, layer, -1, assetUrl,
          );
          if (sky.node) {
            layer.insertBefore(sky.node, layers.length ? layers[0].node : layer.firstChild);
            layers.unshift(sky);
          }
        }
      }
    }
    // Vignette: the field darkens toward its edges by the atmosphere's strength so the paper reads as a
    // lit surface, not a void; the dark variant leans on it harder because it has no bloom contrast to spare.
    // Paperbook plates skip it — matte stock stays one tone to the edge.
    if (!PAPERBOOK(plan)) {
      const vig = atmo.vignette_opacity == null ? 0.03 : atmo.vignette_opacity;
      const vc = atmo.vignette || brand.ink;
      el('div', {
        position: 'absolute', inset: '0', pointerEvents: 'none',
        background: `radial-gradient(ellipse 85% 80% at 50% 45%, ${rgbaOf(vc, 0)} 52%, ${rgbaOf(vc, vig * 0.45)} 82%, ${rgbaOf(vc, vig)} 100%)`,
      }, layer);
    }
    return { layer, layers };
  }

  function applyBackgroundState(bgNode, lt, beat, stageFade, preRoll, canvas, plan) {
    if (stageFade != null) bgNode.layer.style.opacity = stageFade.toFixed(4);
    if (!bgNode.layers.length) return;
    const W = canvas.w, H = canvas.h;
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
      if (spec.kind === 'dotgrid' || spec.kind === 'plane' || spec.kind === 'band') {
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
      // Painting performance (mona-lisa/autoportrait pattern in our dialect): the
      // plate doesn't pop in — it paints itself. Far planes wash in first as a
      // bottom-up wipe (paint floods a page upward), mid pieces stamp down with a
      // paper-press settle, details (stars, windows, weather) speckle in last.
      const paintT = EASE.outCubic(prog(lt, spec.plane * 260, spec.plane * 260 + 620));
      if (spec.kind === 'band') {
        if (paintT < 1) L.node.style.clipPath = `inset(${(100 - paintT * 100).toFixed(2)}% -2% -4% -2%)`;
        else if (L.node.style.clipPath) L.node.style.clipPath = '';
      } else if (spec.kind === 'piece' || spec.kind === 'windows') {
        opacity *= Math.min(1, paintT * 1.6);
        scale *= lerp(0.72, 1, EASE.settle(paintT));
      } else if (spec.kind === 'stars' || spec.kind === 'fireflies' || spec.kind === 'rain' || spec.kind === 'birds') {
        // Speckle-in: each child waits its own moment inside the first 1.1s.
        for (const c of L.node.children) {
          const cT = EASE.outCubic(prog(lt, Number(c.dataset.ph) * 900, Number(c.dataset.ph) * 900 + 320));
          c.style.opacity = cT < 1 ? cT.toFixed(3) : '';
        }
      }
      // Living scene: the world's children keep moving while the page is read —
      // weather falls, birds cross, flora sways, lights flicker. All pure
      // functions of lt: a seek lands on the same frame. Under the paperbook a
      // printed page is still: the book turns, the figure acts, the picture sits.
      let rot = spec.rotation_deg || 0;
      const living = !PAPERBOOK(plan);
      if (living) {
      if (spec.kind === 'stars') {
        for (const c of L.node.children) {
          const o = Number(c.dataset.o || 0.5);
          c.setAttribute('fill-opacity', f2(o * (0.55 + 0.45 * Math.sin(lt * 0.0016 + Number(c.dataset.ph) * 6.28))));
        }
      } else if (spec.kind === 'windows') {
        for (const c of L.node.children) {
          if (!c.dataset.lit) continue;
          const o = Number(c.dataset.o || 0.6);
          c.setAttribute('fill-opacity', f2(o * (0.7 + 0.3 * Math.sin(lt * 0.0011 + Number(c.dataset.ph) * 12.57))));
        }
      } else if (spec.kind === 'shaft') {
        // Light sheets sway a breath around their tilt.
        rot = spec.tilt_deg + Math.sin(lt * 0.0006 + spec.seed % 7) * 1.6;
        opacity *= 0.85 + 0.15 * Math.sin(lt * 0.0009 + spec.seed % 13);
      } else if (spec.kind === 'piece') {
        const shp = spec.shape, ph = (spec.seed % 997) / 997 * 6.283;
        if (shp === 'cloud') {
          // Clouds sail — a slow loop across the sky; the wrap point sits
          // off-stage so the re-entry is never seen.
          const span = W * 1.35, spd = W * 0.007;
          tx += ((lt * spd / 1000 + ph * span) % span) - span * 0.5;
          ty += Math.sin(lt * 0.0005 + ph) * H * 0.004;
        } else if (shp === 'bubble') {
          // Bubbles rise on a loop, fading near the surface.
          const span = spec.bbox.y + spec.bbox.h;
          ty -= (lt * 0.028 * (0.7 + ph * 0.2) + ph * span) % span;
          opacity *= 0.55 + 0.45 * Math.sin(lt * 0.003 + ph * 9);
        } else if (shp === 'kelp' || shp === 'tuft' || shp === 'bush' || shp === 'flower') {
          rot += Math.sin(lt * 0.0011 + ph) * 2.4; // rooted sway
        } else if (shp === 'comet' || shp === 'rock') {
          tx += Math.sin(lt * 0.0004 + ph) * W * 0.008;
          ty += Math.cos(lt * 0.0005 + ph) * H * 0.006;
        } else if (shp === 'sun' || shp === 'moon' || shp === 'planet') {
          scale *= 1 + Math.sin(lt * 0.0007 + ph) * 0.008; // celestial bodies breathe
        }
      } else if (spec.kind === 'rain') {
        const bh = spec.bbox.h;
        for (const c of L.node.children) {
          const off = ((lt * Number(c.dataset.sp) * 0.9 + Number(c.dataset.ph) * bh) % bh);
          c.setAttribute('transform', `translate(0 ${f2(off - bh * 0.05)})`);
        }
      } else if (spec.kind === 'birds') {
        const bw2 = spec.bbox.w;
        for (const c of L.node.children) {
          const x = ((lt * Number(c.dataset.sp) * 0.05 + Number(c.dataset.ph) * bw2) % (bw2 * 1.1)) - bw2 * 0.05;
          const flap = Math.sin(lt * 0.012 + Number(c.dataset.ph) * 40);
          c.setAttribute('transform', `translate(${f2(x)} ${f2(Number(c.dataset.y) + Math.sin(lt * 0.001 + Number(c.dataset.ph) * 9) * spec.bbox.h * 0.05)}) scale(${f2(1)} ${f2(0.55 + 0.45 * Math.abs(flap))})`);
        }
      } else if (spec.kind === 'fireflies') {
        for (const c of L.node.children) {
          const ph = Number(c.dataset.ph) * 6.283, sp = Number(c.dataset.sp);
          const wx = Math.sin(lt * 0.0006 * sp + ph) * spec.bbox.w * 0.05;
          const wy = Math.cos(lt * 0.0008 * sp + ph * 1.7) * spec.bbox.h * 0.06;
          c.setAttribute('transform', `translate(${f2(wx)} ${f2(wy)})`);
          c.setAttribute('fill-opacity', f2(Number(c.dataset.o || 0.6) * (0.45 + 0.55 * Math.abs(Math.sin(lt * 0.002 * sp + ph)))));
        }
      }
      }
      if (rot) s.rotate = `${f2(rot)}deg`;
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
      if (!/^(depth|band|piece|stars|shaft|windows)$/.test(L.spec.kind) || !L.base) continue;
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


  function buildFigure(fig, plan, beatRoot, opts, beat) {
    const bb = bboxOf(fig.bbox);
    const host = el('div', {
      position: 'absolute', left: px(bb.x), top: px(bb.y), width: px(bb.w), height: px(bb.h), zIndex: '14',
      willChange: 'transform, opacity', transformOrigin: '50% 100%',
    }, beatRoot);
    // The performer is cut paper, same material as every mark on stage: a 100×140
    // sheet of layered pieces — no borrowed clip-art.
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100 140');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('preserveAspectRatio', 'xMidYMax meet');
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    if (fig.mirror) g.setAttribute('transform', 'translate(100 0) scale(-1 1)');
    svg.appendChild(g);
    host.appendChild(svg);
    // Lifted off the page: the puppet reads as a cut-out sitting on the paper, not flat ink.
    svg.style.filter = `drop-shadow(0 ${px(bb.h * 0.012)} ${px(bb.h * 0.022)} ${rgbaOf(plan.brand.ink, 0.3)})`;
    // Contact pool: the performer stands IN the scene, not on the page — a soft ink
    // ellipse at the feet, thrown slightly away from the scene's light side.
    if (PAPERBOOK(plan)) {
      const sceneLdx = ((((beat || {}).composition || {}).background || {}).layers || [])
        .map((l) => l.lit_dx).find((v) => typeof v === 'number' && v !== 0) || 0;
      el('div', {
        position: 'absolute', left: '8%', bottom: '-2.5%', width: '84%', height: '7%',
        background: `radial-gradient(ellipse at center, ${rgbaOf(plan.brand.ink, 0.30)}, ${rgbaOf(plan.brand.ink, 0)} 68%)`,
        transform: `translateX(${px(-sceneLdx * bb.w * 0.05)})`, pointerEvents: 'none', zIndex: '-1',
      }, host);
    }
    const f = { fig, host, bb, ready: null, slotEls: {}, stateSwaps: null, appliedState: -1, prop: null };
    const figSeed = seedHash(`figure:${fig.character || 'anon'}:${fig.pose && fig.pose.id || ''}`);
    const built = paperFigureSlots(fig, figSeed, plan, `fig_${fig.character || 'f'}`);
    // Under the paperbook the performer is print, not a sticker: no die-cut rim —
    // the ink sits flush in the page like the reference's flat-drawn figures.
    if (!PAPERBOOK(plan)) g.appendChild(built.edge);
    for (const slot of ['body', 'head', 'face']) { g.appendChild(built.slots[slot]); f.slotEls[slot] = built.slots[slot]; }
    // State morph parts are pre-rendered paper slots too: the swap is instant at lt.
    for (const st of fig.states || []) for (const sw of st.swaps) {
      (st._prepared = st._prepared || []).push({ slot: sw.slot, innerHTML: paperSlotInner(sw.slot, sw.part_id, fig, figSeed, plan), transform: '' });
    }
    let ready = Promise.resolve();
    if (fig.states) f.stateSwaps = fig.states;
    // Mocap sprite: when the plan carries a baked motion clip, a second svg swaps
    // frame groups per seek. The paper figure stays as fallback until the fetch lands.
    if (fig.motion && fig.motion.asset) {
      f.motion = fig.motion;
      f.motionData = null;
      const msvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      msvg.setAttribute('width', '100%');
      msvg.setAttribute('height', '100%');
      msvg.setAttribute('preserveAspectRatio', 'xMidYMax meet');
      msvg.style.filter = svg.style.filter;
      msvg.style.display = 'none';
      if (fig.mirror) msvg.style.transform = 'scaleX(-1)';
      const mframe = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      msvg.appendChild(mframe);
      host.appendChild(msvg);
      f.mframe = mframe; f.msvg = msvg; f._lastFrame = -1;
      // Expression overlay: the sprite bakes a body but not a face. A small ink
      // face rides the head region of the host — eyes/brows/mouth from the same
      // FIGURE_FACE grammar as the paper figure, blinking on its own clock.
      {
        const fk = FIGURE_FACE[paperFaceKind(fig.emotion && fig.emotion.face)] || FIGURE_FACE.calm;
        const fsvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        fsvg.setAttribute('viewBox', '0 0 40 24');
        fsvg.style.cssText = `position:absolute;left:50%;top:7%;width:34%;height:auto;transform:translateX(-50%);pointer-events:none;z-index:3`;
        const inkC = plan.brand.ink;
        const eyesG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        if (fk.eyes === 'closed') {
          for (const sx of [-7, 7]) {
            const e = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            e.setAttribute('d', `M${20 + sx - 2.6} 10 q2.6 2.4 5.2 0`); e.setAttribute('stroke', inkC);
            e.setAttribute('stroke-width', '1.8'); e.setAttribute('fill', 'none'); e.setAttribute('stroke-linecap', 'round');
            eyesG.appendChild(e);
          }
        } else {
          for (const sx of [-7, 7]) {
            const e = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            e.setAttribute('cx', String(20 + sx)); e.setAttribute('cy', '10'); e.setAttribute('r', fk.eyes === 'open' ? '2.7' : '2.1'); e.setAttribute('fill', inkC);
            eyesG.appendChild(e);
          }
        }
        fsvg.appendChild(eyesG);
        f._eyes = eyesG;
        if (fk.brows !== 'none') for (const sx of [-7, 7]) {
          const b2 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          b2.setAttribute('d', `M${20 + sx - 3} ${fk.brows === 'up' ? 3.2 : 4.6} q3 ${fk.brows === 'up' ? -1.8 : 1.6} 6 0`);
          b2.setAttribute('stroke', inkC); b2.setAttribute('stroke-width', '1.5'); b2.setAttribute('fill', 'none'); b2.setAttribute('stroke-linecap', 'round');
          fsvg.appendChild(b2);
        }
        const mouthD = { smile: 'M14 18 q6 5 12 0', calm: 'M15 18.5 q5 2 10 0', flat: 'M15 19 h10', sad: 'M14 20 q6 -4.5 12 0', o: null }[fk.mouth];
        if (fk.mouth === 'o') {
          const m = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
          m.setAttribute('cx', '20'); m.setAttribute('cy', '19'); m.setAttribute('rx', '3.8'); m.setAttribute('ry', '4.4');
          m.setAttribute('fill', 'none'); m.setAttribute('stroke', inkC); m.setAttribute('stroke-width', '1.7');
          fsvg.appendChild(m);
        } else if (mouthD) {
          const m = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          m.setAttribute('d', mouthD); m.setAttribute('stroke', inkC); m.setAttribute('stroke-width', '1.8');
          m.setAttribute('fill', 'none'); m.setAttribute('stroke-linecap', 'round');
          fsvg.appendChild(m);
        }
        for (const sx of [-12, 12]) {
          const ch = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          ch.setAttribute('cx', String(20 + sx)); ch.setAttribute('cy', '14.5'); ch.setAttribute('r', '2.4');
          ch.setAttribute('fill', paintTone('petal', plan)); ch.setAttribute('opacity', '0.4');
          fsvg.appendChild(ch);
        }
        host.appendChild(fsvg);
        f.faceSvg = fsvg;
        f.faceBaseY = 7;
      }
      ready = fetchText(opts.assetUrl(fig.motion.asset)).then((txt) => {
        const md = JSON.parse(txt);
        md._inner = md.frames.map((fr) => fr.replace(/^<svg[^>]*>/, '').replace(/<\/svg>\s*$/, ''));
        md._vb = md.frame_vb || md.frames.map(() => md.viewBox);
        md.loop_from = Math.min(md.loop_from ?? md.frames.length - 1, md.frames.length - 1);
        msvg.setAttribute('viewBox', md._vb[0].join(' '));
        f.motionData = md;
        msvg.style.display = '';
        svg.style.display = 'none';
      }).catch(() => { f.motionData = null; });
    }
    if (fig.prop) {
      const p = fig.prop;
      const size = bb.w * 0.3;
      const prop = el('div', {
        position: 'absolute', left: `${(p.anchor.x * 100).toFixed(2)}%`, top: `${(p.anchor.y * 100).toFixed(2)}%`,
        width: px(size), height: px(size), transform: 'translate(-50%,-50%)', transformOrigin: '50% 15%',
        willChange: 'transform', filter: `drop-shadow(0 ${px(size * 0.05)} ${px(size * 0.08)} ${rgbaOf(plan.brand.ink, 0.28)})`,
      }, host);
      f.prop = prop;
      const propArtKey = paperArtKey(p.concept);
      const propReady = propArtKey
        ? Promise.resolve((() => {
            const psvg = paperArtSvg(propArtKey, seedHash(`prop:${p.concept}`), plan, `prop_${fig.name || 'f'}`);
            if (psvg) { psvg.setAttribute('width', '100%'); psvg.setAttribute('height', '100%'); prop.appendChild(psvg); }
          })())
        : p.asset && p.asset.path
        ? fetchText(opts.assetUrl(p.asset.path)).then((txt) => {
            const doc = new DOMParser().parseFromString(txt, 'image/svg+xml');
            const psvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            psvg.setAttribute('viewBox', doc.documentElement.getAttribute('viewBox') || `0 0 ${p.asset.width || 400} ${p.asset.height || 400}`);
            psvg.setAttribute('width', '100%'); psvg.setAttribute('height', '100%');
            psvg.innerHTML = doc.documentElement.innerHTML;
            prop.appendChild(psvg);
          })
        : p.photo && p.photo.path
          ? Promise.resolve(prop.appendChild(Object.assign(el('img', { width: '100%', height: '100%', objectFit: 'cover', borderRadius: px(size * 0.08) }), { src: opts.assetUrl(p.photo.path) })))
          : Promise.resolve((() => {
              prop.style.cssText += `;background:${plan.brand.paper};border:${px(Math.max(1, size * 0.02))} solid ${plan.brand.ink};border-radius:${px(size * 0.1)};box-shadow:0 ${px(size * 0.05)} ${px(size * 0.12)} rgba(0,0,0,.25);display:flex;align-items:center;justify-content:center;`;
              const tag = el('span', { fontFamily: `"${plan.fonts.families.display}"`, fontWeight: '700', fontSize: px(size * 0.3), color: plan.brand.ink, whiteSpace: 'nowrap' }, prop);
              tag.textContent = String(p.word || p.concept || '');
            })());
      f.ready = Promise.all([ready, propReady]);
    } else {
      f.ready = ready;
    }
    return f;
  }

  function applyFigureState(f, lt, beat, ctx) {
    const fig = f.fig;
    const s = f.host.style;
    s.visibility = lt < fig.enter_ms ? 'hidden' : 'visible';
    const p = EASE.outQuint(prog(lt, fig.enter_ms, fig.enter_ms + fig.enter_duration_ms));
    let opacity = p, ty = (1 - p) * f.bb.h * 0.05, scale = lerp(0.985, 1, p), tx = 0, tilt = 0;
    const tr = fig.track;
    if (tr) {
      const stage = f.bb.w * 1.3 + 60;
      if (tr.enter !== 'none' && lt < tr.enter_ms + tr.enter_duration_ms) {
        // Walking in from a wing: horizontal travel with a two-step bob and a hair of tilt.
        const q = EASE.outCubic(prog(lt, tr.enter_ms, tr.enter_ms + tr.enter_duration_ms));
        const dir = tr.enter === 'left' ? -1 : 1;
        tx = dir * stage * (1 - q);
        tilt = dir * (1 - q) * 4;
        ty += Math.abs(Math.sin(q * Math.PI * 3)) * f.bb.h * 0.012;
        opacity = Math.max(opacity, Math.min(1, q * 3));
      } else if (tr.exit !== 'none' && lt >= tr.exit_start_ms) {
        const q = EASE.inCubic(prog(lt, tr.exit_start_ms, tr.exit_start_ms + tr.exit_duration_ms));
        const dir = tr.exit === 'left' ? -1 : 1;
        tx = dir * stage * q;
        tilt = dir * q * 4;
        ty += Math.abs(Math.sin(q * Math.PI * 3)) * f.bb.h * 0.012;
      }
    }
    const ex = ctx.exitState({ block: { role: 'figure' } }, lt);
    if (ex) { opacity *= ex.opacity; ty += ex.ty; }
    s.opacity = opacity.toFixed(4);
    s.transform = `translateX(${tx.toFixed(2)}px) translateY(${ty.toFixed(2)}px) rotate(${tilt.toFixed(2)}deg) scale(${scale.toFixed(4)})`;
    if (f.motionData && f.mframe) {
      const md = f.motionData;
      const fi = Math.max(0, Math.floor((Math.max(0, lt - fig.enter_ms) / 1000) * md.fps));
      const tail = Math.max(1, md.frames.length - md.loop_from);
      const i2 = fi < md.loop_from ? fi : md.loop_from + ((fi - md.loop_from) % tail);
      if (i2 !== f._lastFrame) {
        f._lastFrame = i2;
        f.msvg.setAttribute('viewBox', md._vb[i2].join(' '));
        f.mframe.innerHTML = md._inner[i2];
      }
    }
    if (f._eyes) {
      // Blink: a 140ms lid dip every ~4.2s, phase-offset per figure so casts
      // never blink in unison; plus a light head-sway following the body.
      const phase = (fig.character ? String(fig.character).length : 1) * 731;
      const bt = (lt + phase) % 4200;
      const lid = bt < 140 ? Math.sin((bt / 140) * Math.PI) : 0;
      f._eyes.setAttribute('transform', `translate(0 ${f2(10 * lid)}) scale(1 ${f2(1 - lid * 0.92)}) translate(0 ${f2(-10 * lid)})`);
      f.faceSvg.style.top = `${(f.faceBaseY + Math.sin(lt * 0.0016 + phase) * 0.6).toFixed(2)}%`;
    }
    if (f.prop) {
      const sway = Math.sin(lt * 0.0042) * 3.5;
      f.prop.style.transform = `translate(-50%,-50%) rotate(${sway.toFixed(2)}deg)`;
    }
    // Performer states: a puppet cuts poses, it does not tween — instant swap at its authored ms.
    if (f.stateSwaps) {
      let idx = -1;
      for (let i = 0; i < f.stateSwaps.length; i++) if (lt >= f.stateSwaps[i].at_ms) idx = i;
      if (idx !== f.appliedState) {
        f.appliedState = idx;
        if (idx >= 0) {
          for (const sw of f.stateSwaps[idx]._prepared || []) {
            const el2 = f.slotEls[sw.slot];
            if (el2) { el2.innerHTML = sw.innerHTML; el2.setAttribute('transform', sw.transform); }
          }
        }
      }
    }
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

  function seedHash(s) {
    let h = 0x811C9DC5;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function rng(seed) {
    let t = seed >>> 0;
    return () => { t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  // Paper edge profile (after og2701/scraps' tear model): a torn edge is low-frequency
  // wobble — anchors about every 1/26 of the run, smoothstep-interpolated — plus
  // high-frequency fuzz sampled every ~1/60. A cut edge is 1-3 near-straight scissor
  // strokes with tiny drift. `bias` shifts the whole line outward (the fibrous lip).
  function edgeProfile(len, style, amp, r, bias) {
    const pts = [];
    if (style === 'cut') {
      const n = 1 + Math.floor(r() * 2);
      pts.push({ t: 0, off: (r() * 2 - 1) * amp * 0.35 });
      for (let i = 1; i < n; i++) pts.push({ t: (len * i) / n + (r() * 2 - 1) * len * 0.06, off: (r() * 2 - 1) * amp });
      pts.push({ t: len, off: (r() * 2 - 1) * amp * 0.35 });
      return pts.map((p) => ({ t: p.t, off: p.off + bias }));
    }
    const nA = Math.max(2, Math.round(len / 26));
    const anchors = [];
    for (let i = 0; i <= nA; i++) anchors.push((r() * 2 - 1) * amp);
    const step = Math.max(1, len / 60);
    for (let t = 0; t < len; t += step) {
      const u = (t / len) * nA, i = Math.min(nA - 1, Math.floor(u)), f = u - i;
      const s = f * f * (3 - 2 * f);
      pts.push({ t, off: anchors[i] * (1 - s) + anchors[i + 1] * s + (r() * 2 - 1) * amp * 0.55 });
    }
    pts.push({ t: len, off: anchors[nA] });
    return pts.map((p) => ({ t: p.t, off: p.off + bias }));
  }
  // Walk the rect perimeter clockwise; positive offsets push outward.
  function edgeRectPts(b, style, amp, r, bias) {
    const sides = [
      { len: b.w, map: (t, o) => [b.x + t, b.y - o] },
      { len: b.h, map: (t, o) => [b.x + b.w + o, b.y + t] },
      { len: b.w, map: (t, o) => [b.x + b.w - t, b.y + b.h + o] },
      { len: b.h, map: (t, o) => [b.x - o, b.y + b.h - t] },
    ];
    const out = [];
    for (const s of sides) for (const p of edgeProfile(s.len, style, amp, r, bias || 0)) out.push(s.map(p.t, p.off));
    return out;
  }
  // Hand-cut card edge: a torn two-frequency wobble around the rect — the die-cut edge
  // around every sticker in the paper language.
  function cutRectPath(b, seed, j) {
    return polyPath(edgeRectPts(b, 'torn', j, rng(seed), 0)) + 'Z';
  }
  // The fibrous fringe of a tear: the same wobble a little wider and a hair outward —
  // the white core of the paper showing along the rip.
  function tornFringePath(b, seed, j) {
    return polyPath(edgeRectPts(b, 'torn', j * 1.25, rng(seed ^ 0x51ab), Math.max(1, j * 0.5))) + 'Z';
  }
  // Organic die-cut blob: low-frequency wobble plus fuzz on the radius — the irregular
  // white edge a sticker is cut along.
  function cutBlobPath(cx, cy, rx, ry, seed) {
    const r = rng(seed);
    const n = 26, anchors = [];
    for (let i = 0; i < 9; i++) anchors.push((r() * 2 - 1) * 0.14);
    const pts = [];
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const u = (i / n) * (anchors.length - 1), ai = Math.min(anchors.length - 2, Math.floor(u)), f = u - ai;
      const s = f * f * (3 - 2 * f);
      const k = 1 + anchors[ai] * (1 - s) + anchors[ai + 1] * s + (r() - 0.5) * 0.075;
      pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
    }
    return polyPath(pts) + 'Z';
  }
  // ----------------------------- Paper art ----------------------------------
  // The paper language's picture vocabulary: every concept the film names is drawn
  // as a composed collage of cut-paper pieces — filled, wobbly-edged shapes laid
  // over a white die-cut edge — never a stroked icon glyph. Pieces are authored in
  // a normalized 100x100 space; `edge !== 0` pieces contribute to the union white
  // border, `op`/`rot` plus seeded jitter keep every cut unique. Tones resolve
  // against the film's palette where symbolic, else a fixed watercolour register.
  const PAPER_TONES = {
    sun: '#f2b54a', sunlit: '#f7d98b', brass: '#e0b352',
    snow: '#f7f4ec', moonlit: '#e8dfc6', moonshade: '#b5a988', night: '#2f3c60', slate: '#5b6b8c',
    grey: '#b9b4a6', steel: '#8a94a6', sky: '#a9c9de', water: '#7fb3d5', deep: '#3f5a80',
    leaf: '#6fa86f', sage: '#93b58a', stem: '#4e7a4e', soil: '#6b4f3a', wood: '#9a7856',
    skin: '#e8b98e', petal: '#e79fb0', blush: '#d96a6a', warm: '#d97f4e', fire: '#e0684a',
  };
  function paintTone(tone, plan) {
    if (!tone) return plan.brand.ink;
    if (tone[0] === '#') return tone;
    if (tone === 'ink') return plan.brand.ink;
    if (tone === 'accent') return plan.brand.accent || plan.brand.ink;
    if (tone === 'paper') return plan.brand.paper;
    return PAPER_TONES[tone] || plan.brand.ink;
  }
  const STAR_PTS = [[50, 4], [62, 37], [96, 38], [69, 60], [78, 94], [50, 73], [22, 94], [31, 60], [4, 38], [38, 37]];
  const PAPER_ART = {
    sun: [
      { s: 'rays', cx: 50, cy: 50, r0: 32, r1: 47, n: 10, w: 9, tone: 'sun' },
      { s: 'blob', cx: 50, cy: 50, r: 25, tone: 'sun' },
      { s: 'blob', cx: 41, cy: 40, rx: 9, ry: 6, tone: 'sunlit', op: 0.55, edge: 0 },
    ],
    'moon-full': [
      { s: 'blob', cx: 50, cy: 50, r: 30, tone: 'moonlit' },
      { s: 'blob', cx: 39, cy: 41, rx: 7, ry: 5.5, tone: 'moonshade', op: 0.7, edge: 0 },
      { s: 'blob', cx: 59, cy: 58, rx: 4.5, ry: 4, tone: 'moonshade', op: 0.6, edge: 0 },
      { s: 'blob', cx: 53, cy: 33, rx: 3, ry: 2.5, tone: 'moonshade', op: 0.5, edge: 0 },
    ],
    'moon-crescent': [
      { s: 'crescent', cx: 48, cy: 50, r: 30, bite: 0.62, tone: 'moonlit' },
      { s: 'blob', cx: 40, cy: 42, rx: 3.5, ry: 3, tone: 'moonshade', op: 0.5, edge: 0 },
    ],
    'moon-half': [
      { s: 'halfdisc', cx: 50, cy: 50, r: 30, tone: 'moonlit' },
      { s: 'blob', cx: 56, cy: 43, rx: 4, ry: 3.4, tone: 'moonshade', op: 0.6, edge: 0 },
      { s: 'blob', cx: 58, cy: 60, rx: 3, ry: 2.6, tone: 'moonshade', op: 0.5, edge: 0 },
    ],
    star: [{ s: 'path', pts: STAR_PTS, tone: 'brass' }],
    stars: [
      { s: 'path', pts: STAR_PTS, k: 0.42, ox: 8, oy: 10, tone: 'brass' },
      { s: 'path', pts: STAR_PTS, k: 0.3, ox: 58, oy: 30, tone: 'snow' },
      { s: 'path', pts: STAR_PTS, k: 0.22, ox: 42, oy: 62, tone: 'brass', op: 0.85 },
    ],
    cloud: [
      { s: 'blob', cx: 50, cy: 62, rx: 34, ry: 18, tone: 'snow' },
      { s: 'blob', cx: 33, cy: 52, rx: 15, ry: 13, tone: 'snow' },
      { s: 'blob', cx: 62, cy: 48, rx: 19, ry: 16, tone: 'snow' },
      { s: 'blob', cx: 44, cy: 58, rx: 20, ry: 14, tone: 'snow' },
      { s: 'blob', cx: 62, cy: 52, rx: 8, ry: 6, tone: 'paper', op: 0.5, edge: 0 },
    ],
    rain: [
      { s: 'blob', cx: 50, cy: 40, rx: 30, ry: 15, tone: 'sky' },
      { s: 'blob', cx: 36, cy: 32, rx: 13, ry: 11, tone: 'sky' },
      { s: 'blob', cx: 60, cy: 29, rx: 17, ry: 14, tone: 'sky' },
      { s: 'petal', cx: 32, cy: 66, rx: 4.5, ry: 8, tone: 'water' },
      { s: 'petal', cx: 50, cy: 72, rx: 4.5, ry: 8, tone: 'water' },
      { s: 'petal', cx: 68, cy: 64, rx: 4.5, ry: 8, tone: 'water' },
    ],
    storm: [
      { s: 'blob', cx: 50, cy: 36, rx: 30, ry: 15, tone: 'slate' },
      { s: 'blob', cx: 62, cy: 27, rx: 17, ry: 13, tone: 'slate' },
      { s: 'path', pts: [[55, 52], [40, 74], [49, 74], [43, 94], [64, 68], [54, 68]], tone: 'brass' },
    ],
    rainbow: [
      { s: 'arc', cx: 50, cy: 82, r: 42, a0: 180, a1: 360, t: 7, tone: 'blush' },
      { s: 'arc', cx: 50, cy: 82, r: 33, a0: 180, a1: 360, t: 7, tone: 'brass' },
      { s: 'arc', cx: 50, cy: 82, r: 24, a0: 180, a1: 360, t: 7, tone: 'leaf' },
      { s: 'blob', cx: 16, cy: 78, rx: 11, ry: 7, tone: 'snow' },
      { s: 'blob', cx: 84, cy: 78, rx: 11, ry: 7, tone: 'snow' },
    ],
    earth: [
      { s: 'blob', cx: 50, cy: 50, r: 31, tone: 'water' },
      { s: 'blob', cx: 38, cy: 40, rx: 13, ry: 9, rot: -20, tone: 'leaf', edge: 0 },
      { s: 'blob', cx: 61, cy: 58, rx: 11, ry: 8, rot: 30, tone: 'leaf', edge: 0 },
      { s: 'blob', cx: 55, cy: 30, rx: 7, ry: 4.5, rot: 15, tone: 'leaf', edge: 0 },
    ],
    seed: [
      { s: 'blob', cx: 50, cy: 55, rx: 13, ry: 17, rot: -18, tone: 'soil' },
      { s: 'blob', cx: 45, cy: 47, rx: 4, ry: 6, rot: -18, tone: 'skin', op: 0.4, edge: 0 },
    ],
    sprout: [
      { s: 'blob', cx: 50, cy: 84, rx: 27, ry: 9, tone: 'soil' },
      { s: 'rect', x: 48, y: 44, w: 4.5, h: 34, tone: 'stem' },
      { s: 'petal', cx: 38, cy: 52, rx: 13, ry: 6.5, rot: -28, tone: 'leaf' },
      { s: 'petal', cx: 62, cy: 48, rx: 13, ry: 6.5, rot: 28, tone: 'leaf' },
      { s: 'petal', cx: 50, cy: 40, rx: 11, ry: 6, rot: 90, tone: 'sage' },
    ],
    plant: [
      { s: 'path', pts: [[34, 62], [66, 62], [61, 92], [39, 92]], tone: 'wood' },
      { s: 'rect', x: 48, y: 36, w: 4.5, h: 28, tone: 'stem' },
      { s: 'petal', cx: 39, cy: 46, rx: 12, ry: 6, rot: -28, tone: 'leaf' },
      { s: 'petal', cx: 61, cy: 42, rx: 12, ry: 6, rot: 28, tone: 'leaf' },
    ],
    leaf: [
      { s: 'petal', cx: 50, cy: 48, rx: 17, ry: 34, rot: -25, tone: 'leaf' },
      { s: 'path', pts: [[44, 78], [47, 50], [50, 22]], tone: 'stem', stroke: 2.4, edge: 0 },
    ],
    leaves: [
      { s: 'petal', cx: 34, cy: 52, rx: 12, ry: 26, rot: -35, tone: 'leaf' },
      { s: 'petal', cx: 62, cy: 48, rx: 12, ry: 26, rot: 30, tone: 'sage' },
      { s: 'petal', cx: 50, cy: 60, rx: 10, ry: 22, rot: 0, tone: 'leaf', op: 0.9 },
    ],
    flower: [
      { s: 'rect', x: 48, y: 52, w: 4.5, h: 38, tone: 'stem' },
      { s: 'petal', cx: 50, cy: 22, rx: 8, ry: 13, tone: 'petal' },
      { s: 'petal', cx: 30, cy: 36, rx: 8, ry: 13, rot: -62, tone: 'petal' },
      { s: 'petal', cx: 70, cy: 36, rx: 8, ry: 13, rot: 62, tone: 'petal' },
      { s: 'petal', cx: 37, cy: 50, rx: 8, ry: 12, rot: -130, tone: 'petal' },
      { s: 'petal', cx: 63, cy: 50, rx: 8, ry: 12, rot: 130, tone: 'petal' },
      { s: 'blob', cx: 50, cy: 38, r: 9, tone: 'sun' },
      { s: 'petal', cx: 40, cy: 72, rx: 11, ry: 5, rot: -20, tone: 'leaf' },
    ],
    sunflower: [
      { s: 'rect', x: 48, y: 55, w: 5, h: 38, tone: 'stem' },
      { s: 'petal', cx: 50, cy: 20, rx: 7, ry: 12, tone: 'brass' },
      { s: 'petal', cx: 68, cy: 28, rx: 7, ry: 12, rot: 55, tone: 'brass' },
      { s: 'petal', cx: 72, cy: 48, rx: 7, ry: 12, rot: 105, tone: 'brass' },
      { s: 'petal', cx: 32, cy: 28, rx: 7, ry: 12, rot: -55, tone: 'brass' },
      { s: 'petal', cx: 28, cy: 48, rx: 7, ry: 12, rot: -105, tone: 'brass' },
      { s: 'blob', cx: 50, cy: 38, r: 12, tone: 'soil' },
    ],
    tree: [
      { s: 'rect', x: 45, y: 58, w: 10, h: 34, tone: 'wood' },
      { s: 'blob', cx: 50, cy: 40, rx: 27, ry: 25, tone: 'leaf' },
      { s: 'blob', cx: 32, cy: 50, rx: 14, ry: 12, tone: 'leaf' },
      { s: 'blob', cx: 68, cy: 50, rx: 14, ry: 12, tone: 'sage' },
    ],
    pine: [
      { s: 'path', pts: [[50, 8], [72, 42], [28, 42]], tone: 'leaf' },
      { s: 'path', pts: [[50, 30], [78, 66], [22, 66]], tone: 'sage' },
      { s: 'rect', x: 45, y: 66, w: 10, h: 22, tone: 'wood' },
    ],
    roots: [
      { s: 'path', pts: [[48, 30], [52, 30], [44, 62], [34, 80], [42, 60]], tone: 'soil' },
      { s: 'path', pts: [[48, 30], [52, 30], [52, 66], [48, 86], [48, 60]], tone: 'wood' },
      { s: 'path', pts: [[48, 30], [52, 30], [60, 60], [70, 76], [58, 62]], tone: 'soil' },
      { s: 'blob', cx: 50, cy: 30, rx: 14, ry: 7, tone: 'soil' },
    ],
    drop: [
      { s: 'petal', cx: 50, cy: 52, rx: 20, ry: 28, tone: 'water' },
      { s: 'blob', cx: 42, cy: 44, rx: 5, ry: 8, rot: -15, tone: 'snow', op: 0.55, edge: 0 },
    ],
    wave: [
      { s: 'path', pts: [[4, 62], [22, 46], [40, 62], [58, 46], [76, 62], [94, 52], [94, 92], [4, 92]], tone: 'water' },
      { s: 'path', pts: [[4, 76], [24, 64], [44, 76], [64, 64], [94, 78], [94, 94], [4, 94]], tone: 'deep', op: 0.7 },
    ],
    mountain: [
      { s: 'path', pts: [[8, 90], [38, 30], [50, 52], [64, 26], [92, 90]], tone: 'slate' },
      { s: 'path', pts: [[38, 30], [44, 42], [38, 45], [32, 42]], tone: 'snow' },
      { s: 'path', pts: [[64, 26], [71, 39], [64, 42], [57, 39]], tone: 'snow' },
    ],
    hill: [
      { s: 'path', pts: [[2, 96], [24, 62], [52, 76], [78, 58], [98, 84], [98, 98], [2, 98]], tone: 'sage' },
      { s: 'path', pts: [[2, 98], [40, 80], [70, 88], [98, 78], [98, 98]], tone: 'leaf' },
    ],
    fire: [
      { s: 'petal', cx: 50, cy: 56, rx: 21, ry: 30, tone: 'fire' },
      { s: 'petal', cx: 50, cy: 62, rx: 13, ry: 21, tone: 'warm', edge: 0 },
      { s: 'petal', cx: 50, cy: 68, rx: 6.5, ry: 13, tone: 'sunlit', edge: 0 },
    ],
    hand: [
      { s: 'blob', cx: 50, cy: 60, rx: 21, ry: 20, tone: 'skin' },
      { s: 'rect', x: 30, y: 28, w: 9, h: 30, rot: -8, tone: 'skin' },
      { s: 'rect', x: 43, y: 24, w: 9, h: 32, tone: 'skin' },
      { s: 'rect', x: 56, y: 26, w: 9, h: 30, rot: 4, tone: 'skin' },
      { s: 'rect', x: 68, y: 34, w: 9, h: 24, rot: 14, tone: 'skin' },
      { s: 'blob', cx: 28, cy: 62, rx: 9, ry: 11, rot: -35, tone: 'skin' },
    ],
    eye: [
      { s: 'petal', cx: 50, cy: 50, rx: 34, ry: 18, rot: 90, tone: 'snow' },
      { s: 'blob', cx: 50, cy: 50, r: 11, tone: 'deep', edge: 0 },
      { s: 'blob', cx: 50, cy: 50, r: 4.5, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 46, cy: 45, r: 2.5, tone: 'snow', edge: 0 },
    ],
    heart: [
      { s: 'path', pts: [[50, 84], [20, 54], [14, 32], [28, 16], [44, 20], [50, 32], [56, 20], [72, 16], [86, 32], [80, 54]], tone: 'blush' },
    ],
    magnifier: [
      { s: 'blob', cx: 42, cy: 42, r: 21, tone: 'sky', op: 0.45, edge: 0 },
      { s: 'ring', cx: 42, cy: 42, r: 23, t: 7, tone: 'steel' },
      { s: 'rect', x: 58, y: 58, w: 10, h: 30, rot: -45, tone: 'wood' },
    ],
    telescope: [
      { s: 'rect', x: 18, y: 38, w: 46, h: 15, rot: -18, tone: 'brass' },
      { s: 'rect', x: 60, y: 44, w: 14, h: 11, rot: -18, tone: 'wood' },
      { s: 'rect', x: 36, y: 52, w: 5, h: 32, rot: -8, tone: 'wood' },
      { s: 'rect', x: 24, y: 82, w: 30, h: 6, tone: 'wood' },
    ],
    book: [
      { s: 'rect', x: 26, y: 24, w: 50, h: 56, rot: -3, tone: 'accent' },
      { s: 'rect', x: 22, y: 28, w: 50, h: 52, rot: -3, tone: 'paper' },
      { s: 'rect', x: 22, y: 28, w: 6, h: 52, rot: -3, tone: 'blush' },
    ],
    gift: [
      { s: 'rect', x: 24, y: 44, w: 52, h: 42, tone: 'blush' },
      { s: 'rect', x: 19, y: 32, w: 62, h: 14, tone: 'accent' },
      { s: 'rect', x: 44, y: 32, w: 12, h: 54, tone: 'paper', op: 0.9 },
      { s: 'petal', cx: 42, cy: 24, rx: 9, ry: 6, rot: -30, tone: 'paper' },
      { s: 'petal', cx: 58, cy: 24, rx: 9, ry: 6, rot: 30, tone: 'paper' },
    ],
    lightbulb: [
      { s: 'blob', cx: 50, cy: 40, r: 23, tone: 'sun' },
      { s: 'blob', cx: 42, cy: 33, rx: 7, ry: 5, tone: 'sunlit', op: 0.6, edge: 0 },
      { s: 'rect', x: 41, y: 62, w: 18, h: 10, tone: 'steel' },
      { s: 'rect', x: 43, y: 73, w: 14, h: 6, tone: 'steel' },
    ],
    key: [
      { s: 'ring', cx: 34, cy: 40, r: 14, t: 7, tone: 'brass' },
      { s: 'rect', x: 44, y: 36, w: 44, h: 9, tone: 'brass' },
      { s: 'rect', x: 76, y: 44, w: 7, h: 12, tone: 'brass' },
      { s: 'rect', x: 63, y: 44, w: 7, h: 12, tone: 'brass' },
    ],
    house: [
      { s: 'rect', x: 28, y: 46, w: 44, h: 38, tone: 'paper' },
      { s: 'path', pts: [[20, 46], [50, 20], [80, 46]], tone: 'blush' },
      { s: 'rect', x: 44, y: 62, w: 13, h: 22, tone: 'wood' },
      { s: 'rect', x: 60, y: 52, w: 9, h: 9, tone: 'sky' },
    ],
    cup: [
      { s: 'path', pts: [[32, 40], [68, 40], [64, 80], [36, 80]], tone: 'accent' },
      { s: 'arc', cx: 71, cy: 55, r: 10, a0: -80, a1: 80, t: 6, tone: 'accent' },
      { s: 'rect', x: 28, y: 84, w: 44, h: 5, tone: 'wood' },
    ],
    clock: [
      { s: 'blob', cx: 50, cy: 50, r: 31, tone: 'paper' },
      { s: 'rect', x: 48, y: 30, w: 4, h: 20, tone: 'ink', edge: 0 },
      { s: 'rect', x: 50, y: 48, w: 16, h: 4, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 50, cy: 50, r: 3, tone: 'blush', edge: 0 },
    ],
    compass: [
      { s: 'blob', cx: 50, cy: 50, r: 32, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 50, cy: 50, r: 28, tone: 'paper', edge: 0 },
      { s: 'rect', x: 48.4, y: 23, w: 3.2, h: 9, tone: 'ink', edge: 0 },
      { s: 'rect', x: 48.4, y: 68, w: 3.2, h: 9, tone: 'ink', edge: 0 },
      { s: 'rect', x: 23, y: 48.4, w: 9, h: 3.2, tone: 'ink', edge: 0 },
      { s: 'rect', x: 68, y: 48.4, w: 9, h: 3.2, tone: 'ink', edge: 0 },
      { s: 'path', pts: [[50, 30], [55.5, 50], [50, 52], [44.5, 50]], tone: 'blush', edge: 0 },
      { s: 'path', pts: [[50, 70], [55.5, 50], [50, 48], [44.5, 50]], tone: 'slate', edge: 0 },
      { s: 'blob', cx: 50, cy: 50, r: 3.4, tone: 'ink', edge: 0 },
    ],
    letter: [
      { s: 'rect', x: 20, y: 32, w: 60, h: 40, tone: 'paper' },
      { s: 'path', pts: [[21, 33], [50, 56], [79, 33]], tone: 'snow', edge: 0 },
    ],
    balloon: [
      { s: 'blob', cx: 50, cy: 34, rx: 19, ry: 23, tone: 'blush' },
      { s: 'path', pts: [[50, 57], [46, 63], [54, 63]], tone: 'blush' },
      { s: 'path', pts: [[49, 63], [46, 76], [53, 86], [50, 93]], tone: 'grey', stroke: 2.2, edge: 0 },
    ],
    kite: [
      { s: 'path', pts: [[50, 12], [74, 40], [50, 68], [26, 40]], tone: 'sky' },
      { s: 'path', pts: [[49, 68], [46, 80], [53, 88]], tone: 'grey', stroke: 2.2, edge: 0 },
      { s: 'rect', x: 44, y: 74, w: 8, h: 5, rot: -30, tone: 'blush', edge: 0 },
      { s: 'rect', x: 50, y: 82, w: 8, h: 5, rot: 30, tone: 'brass', edge: 0 },
    ],
    bird: [
      { s: 'path', pts: [[30, 54], [14, 44], [16, 62]], tone: 'slate' },
      { s: 'blob', cx: 48, cy: 52, rx: 20, ry: 14, tone: 'slate' },
      { s: 'blob', cx: 62, cy: 40, r: 9, tone: 'slate' },
      { s: 'path', pts: [[70, 38], [82, 42], [70, 46]], tone: 'brass' },
      { s: 'petal', cx: 44, cy: 48, rx: 12, ry: 7, rot: -25, tone: 'sky', edge: 0 },
      { s: 'blob', cx: 64, cy: 37, r: 2.2, tone: 'ink', edge: 0 },
      { s: 'rect', x: 46, y: 66, w: 3, h: 10, tone: 'wood' },
    ],
    butterfly: [
      { s: 'petal', cx: 34, cy: 42, rx: 13, ry: 19, rot: -18, tone: 'blush' },
      { s: 'petal', cx: 66, cy: 42, rx: 13, ry: 19, rot: 18, tone: 'blush' },
      { s: 'petal', cx: 38, cy: 64, rx: 9, ry: 12, rot: -35, tone: 'sky' },
      { s: 'petal', cx: 62, cy: 64, rx: 9, ry: 12, rot: 35, tone: 'sky' },
      { s: 'rect', x: 48.5, y: 30, w: 3, h: 34, tone: 'ink', edge: 0 },
    ],
    cat: [
      { s: 'path', pts: [[36, 30], [40, 14], [48, 26]], tone: 'grey' },
      { s: 'path', pts: [[64, 30], [60, 14], [52, 26]], tone: 'grey' },
      { s: 'blob', cx: 50, cy: 38, r: 15, tone: 'grey' },
      { s: 'blob', cx: 48, cy: 68, rx: 22, ry: 18, tone: 'grey' },
      { s: 'path', pts: [[66, 74], [84, 58], [90, 66], [72, 82]], tone: 'grey' },
      { s: 'blob', cx: 44, cy: 35, r: 2.4, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 56, cy: 35, r: 2.4, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 50, cy: 42, r: 2, tone: 'blush', edge: 0 },
    ],
    fish: [
      { s: 'blob', cx: 46, cy: 52, rx: 23, ry: 14, tone: 'water' },
      { s: 'path', pts: [[66, 52], [86, 38], [86, 66]], tone: 'deep' },
      { s: 'blob', cx: 38, cy: 47, r: 2.6, tone: 'ink', edge: 0 },
      { s: 'petal', cx: 52, cy: 52, rx: 8, ry: 5, rot: -15, tone: 'deep', op: 0.4, edge: 0 },
    ],
    boat: [
      { s: 'path', pts: [[18, 62], [82, 62], [70, 80], [30, 80]], tone: 'wood' },
      { s: 'rect', x: 48.5, y: 24, w: 3.5, h: 38, tone: 'wood' },
      { s: 'path', pts: [[54, 26], [54, 58], [78, 58]], tone: 'paper' },
      { s: 'path', pts: [[46, 32], [46, 58], [26, 58]], tone: 'snow' },
    ],
    lighthouse: [
      { s: 'path', pts: [[41, 90], [59, 90], [56, 34], [44, 34]], tone: 'paper' },
      { s: 'rect', x: 43, y: 48, w: 14, h: 8, rot: -2, tone: 'blush' },
      { s: 'rect', x: 43.5, y: 64, w: 13.5, h: 8, rot: -2, tone: 'blush' },
      { s: 'rect', x: 42, y: 24, w: 16, h: 10, tone: 'slate' },
      { s: 'path', pts: [[58, 28], [88, 20], [88, 38]], tone: 'sunlit', op: 0.55, edge: 0 },
    ],
    wind: [
      { s: 'arc', cx: 44, cy: 34, r: 16, a0: 185, a1: 340, t: 6, tone: 'grey', edge: 0 },
      { s: 'arc', cx: 56, cy: 58, r: 21, a0: 185, a1: 340, t: 6, tone: 'grey', edge: 0 },
      { s: 'arc', cx: 40, cy: 78, r: 11, a0: 185, a1: 330, t: 5, tone: 'grey', edge: 0 },
    ],
    apple: [
      { s: 'blob', cx: 50, cy: 56, r: 22, tone: 'blush' },
      { s: 'rect', x: 49, y: 26, w: 3.5, h: 12, rot: 12, tone: 'wood' },
      { s: 'petal', cx: 60, cy: 32, rx: 9, ry: 5, rot: 35, tone: 'leaf' },
      { s: 'blob', cx: 41, cy: 48, rx: 5, ry: 7, tone: 'snow', op: 0.35, edge: 0 },
    ],
    mushroom: [
      { s: 'path', pts: [[38, 92], [44, 56], [56, 56], [62, 92]], tone: 'paper' },
      { s: 'blob', cx: 50, cy: 44, rx: 28, ry: 18, tone: 'blush' },
      { s: 'blob', cx: 38, cy: 38, r: 4, tone: 'snow', edge: 0 },
      { s: 'blob', cx: 58, cy: 46, r: 5, tone: 'snow', edge: 0 },
    ],
    snowflake: [
      { s: 'rect', x: 48, y: 20, w: 4, h: 60, tone: 'sky' },
      { s: 'rect', x: 48, y: 20, w: 4, h: 60, rot: 60, tone: 'sky' },
      { s: 'rect', x: 48, y: 20, w: 4, h: 60, rot: -60, tone: 'sky' },
      { s: 'blob', cx: 50, cy: 50, r: 6, tone: 'snow', edge: 0 },
    ],
    candle: [
      { s: 'rect', x: 42, y: 52, w: 16, h: 36, tone: 'paper' },
      { s: 'petal', cx: 50, cy: 40, rx: 7, ry: 12, tone: 'sun' },
      { s: 'petal', cx: 50, cy: 44, rx: 3.5, ry: 7, tone: 'sunlit', edge: 0 },
    ],
    // Transport — driving/riding/flying all read as paper vehicles on the same wheels.
    car: [
      { s: 'rect', x: 14, y: 46, w: 72, h: 24, tone: 'accent' },
      { s: 'blob', cx: 38, cy: 42, r: 14, tone: 'accent' },
      { s: 'rect', x: 40, y: 30, w: 26, h: 18, tone: 'accent' },
      { s: 'rect', x: 44, y: 33, w: 9, h: 13, tone: 'sky', edge: 0 },
      { s: 'rect', x: 55, y: 33, w: 9, h: 13, tone: 'sky', edge: 0 },
      { s: 'blob', cx: 28, cy: 72, r: 8, tone: 'ink' },
      { s: 'blob', cx: 72, cy: 72, r: 8, tone: 'ink' },
      { s: 'blob', cx: 28, cy: 72, r: 3.4, tone: 'paper', edge: 0 },
      { s: 'blob', cx: 72, cy: 72, r: 3.4, tone: 'paper', edge: 0 },
    ],
    bus: [
      { s: 'rect', x: 12, y: 34, w: 76, h: 36, tone: 'sun' },
      { s: 'rect', x: 18, y: 40, w: 14, h: 12, tone: 'sky', edge: 0 },
      { s: 'rect', x: 36, y: 40, w: 14, h: 12, tone: 'sky', edge: 0 },
      { s: 'rect', x: 54, y: 40, w: 14, h: 12, tone: 'sky', edge: 0 },
      { s: 'rect', x: 72, y: 40, w: 10, h: 12, tone: 'sky', edge: 0 },
      { s: 'blob', cx: 26, cy: 72, r: 7.5, tone: 'ink' },
      { s: 'blob', cx: 74, cy: 72, r: 7.5, tone: 'ink' },
    ],
    bicycle: [
      { s: 'ring', cx: 28, cy: 64, r: 16, t: 4, tone: 'ink' },
      { s: 'ring', cx: 72, cy: 64, r: 16, t: 4, tone: 'ink' },
      { s: 'path', pts: [[28, 64], [46, 38], [60, 64], [28, 64]], tone: 'accent' },
      { s: 'path', pts: [[60, 64], [72, 64], [70, 36]], tone: 'accent' },
      { s: 'rect', x: 40, y: 32, w: 16, h: 6, tone: 'ink' },
      { s: 'rect', x: 66, y: 30, w: 14, h: 5, tone: 'ink' },
    ],
    train: [
      { s: 'rect', x: 10, y: 40, w: 80, h: 28, tone: 'brass' },
      { s: 'rect', x: 60, y: 26, w: 24, h: 16, tone: 'brass' },
      { s: 'rect', x: 16, y: 48, w: 72, h: 6, tone: 'paper', edge: 0 },
      { s: 'rect', x: 20, y: 20, w: 10, h: 14, tone: 'ink' },
      { s: 'blob', cx: 25, cy: 14, r: 6, tone: 'grey' },
      { s: 'blob', cx: 24, cy: 72, r: 7, tone: 'ink' },
      { s: 'blob', cx: 48, cy: 72, r: 7, tone: 'ink' },
      { s: 'blob', cx: 74, cy: 72, r: 7, tone: 'ink' },
    ],
    rocket: [
      { s: 'path', pts: [[50, 12], [64, 36], [64, 66], [36, 66], [36, 36]], tone: 'paper' },
      { s: 'blob', cx: 50, cy: 44, r: 8, tone: 'sky', edge: 0 },
      { s: 'path', pts: [[36, 56], [22, 78], [36, 70]], tone: 'accent' },
      { s: 'path', pts: [[64, 56], [78, 78], [64, 70]], tone: 'accent' },
      { s: 'petal', cx: 50, cy: 78, rx: 7, ry: 13, tone: 'sun' },
      { s: 'petal', cx: 50, cy: 80, rx: 3.5, ry: 7, tone: 'sunlit', edge: 0 },
    ],
    plane: [
      { s: 'path', pts: [[12, 56], [88, 44], [88, 54], [52, 62], [12, 62]], tone: 'paper' },
      { s: 'path', pts: [[46, 44], [60, 20], [68, 44]], tone: 'accent' },
      { s: 'path', pts: [[16, 56], [10, 36], [22, 52]], tone: 'accent' },
    ],
    // Home + waking.
    sunrise: [
      { s: 'halfdisc', cx: 50, cy: 66, r: 24, tone: 'sun' },
      { s: 'halfdisc', cx: 50, cy: 66, r: 15, tone: 'sunlit', edge: 0 },
      { s: 'path', pts: [[0, 78], [30, 62], [60, 74], [100, 66], [100, 100], [0, 100]], tone: 'soil' },
      { s: 'rect', x: 46, y: 30, w: 8, h: 14, tone: 'sun', edge: 0 },
      { s: 'rect', x: 24, y: 42, w: 8, h: 12, rot: -38, tone: 'sun', edge: 0 },
      { s: 'rect', x: 68, y: 42, w: 8, h: 12, rot: 38, tone: 'sun', edge: 0 },
    ],
    alarm_clock: [
      { s: 'blob', cx: 50, cy: 54, r: 26, tone: 'paper' },
      { s: 'blob', cx: 50, cy: 54, r: 20, tone: 'accent', edge: 0 },
      { s: 'blob', cx: 50, cy: 54, r: 16, tone: 'paper', edge: 0 },
      { s: 'rect', x: 48.5, y: 40, w: 3, h: 15, tone: 'ink', edge: 0 },
      { s: 'rect', x: 50, y: 52, w: 11, h: 3, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 36, cy: 24, r: 7, tone: 'accent' },
      { s: 'blob', cx: 64, cy: 24, r: 7, tone: 'accent' },
      { s: 'rect', x: 40, y: 80, w: 7, h: 8, rot: 18, tone: 'ink' },
      { s: 'rect', x: 56, y: 80, w: 7, h: 8, rot: -18, tone: 'ink' },
    ],
    bed: [
      { s: 'rect', x: 12, y: 30, w: 8, h: 44, tone: 'wood' },
      { s: 'rect', x: 16, y: 52, w: 74, h: 20, tone: 'accent' },
      { s: 'rect', x: 50, y: 46, w: 40, h: 10, tone: 'paper' },
      { s: 'blob', cx: 26, cy: 46, r: 9, tone: 'paper' },
      { s: 'rect', x: 12, y: 72, w: 8, h: 10, tone: 'wood' },
      { s: 'rect', x: 82, y: 72, w: 8, h: 10, tone: 'wood' },
    ],
    door: [
      { s: 'rect', x: 26, y: 16, w: 48, h: 72, tone: 'wood' },
      { s: 'rect', x: 33, y: 24, w: 15, h: 24, tone: 'soil', edge: 0 },
      { s: 'rect', x: 33, y: 56, w: 15, h: 24, tone: 'soil', edge: 0 },
      { s: 'rect', x: 53, y: 24, w: 15, h: 24, tone: 'soil', edge: 0 },
      { s: 'rect', x: 53, y: 56, w: 15, h: 24, tone: 'soil', edge: 0 },
      { s: 'blob', cx: 66, cy: 52, r: 3.5, tone: 'brass', edge: 0 },
    ],
    window: [
      { s: 'rect', x: 20, y: 20, w: 60, h: 60, tone: 'sky' },
      { s: 'rect', x: 20, y: 20, w: 60, h: 6, tone: 'wood', edge: 0 },
      { s: 'rect', x: 20, y: 74, w: 60, h: 6, tone: 'wood', edge: 0 },
      { s: 'rect', x: 47, y: 20, w: 6, h: 60, tone: 'wood', edge: 0 },
      { s: 'rect', x: 20, y: 47, w: 60, h: 6, tone: 'wood', edge: 0 },
      { s: 'blob', cx: 64, cy: 34, r: 7, tone: 'sun', edge: 0 },
    ],
    // Tools + marks.
    pencil: [
      { s: 'rect', x: 43, y: 18, w: 14, h: 52, tone: 'sun' },
      { s: 'path', pts: [[43, 70], [57, 70], [50, 88]], tone: 'wood' },
      { s: 'path', pts: [[46.5, 76], [53.5, 76], [50, 86]], tone: 'ink', edge: 0 },
      { s: 'rect', x: 43, y: 18, w: 14, h: 8, tone: 'accent', edge: 0 },
    ],
    scissors: [
      { s: 'ring', cx: 36, cy: 66, r: 10, t: 6, tone: 'accent' },
      { s: 'ring', cx: 64, cy: 66, r: 10, t: 6, tone: 'accent' },
      { s: 'path', pts: [[40, 60], [52, 18], [58, 22], [48, 60]], tone: 'steel' },
      { s: 'path', pts: [[60, 60], [48, 18], [42, 22], [52, 60]], tone: 'steel' },
      { s: 'blob', cx: 50, cy: 44, r: 3.5, tone: 'ink', edge: 0 },
    ],
    gear: [
      { s: 'ring', cx: 50, cy: 50, r: 22, t: 10, tone: 'steel' },
      { s: 'blob', cx: 50, cy: 50, r: 8, tone: 'paper', edge: 0 },
      { s: 'rect', x: 45, y: 14, w: 10, h: 14, tone: 'steel' },
      { s: 'rect', x: 45, y: 72, w: 10, h: 14, tone: 'steel' },
      { s: 'rect', x: 14, y: 45, w: 14, h: 10, tone: 'steel' },
      { s: 'rect', x: 72, y: 45, w: 14, h: 10, tone: 'steel' },
      { s: 'rect', x: 22, y: 24, w: 10, h: 12, rot: -45, tone: 'steel' },
      { s: 'rect', x: 68, y: 24, w: 10, h: 12, rot: 45, tone: 'steel' },
      { s: 'rect', x: 22, y: 66, w: 10, h: 12, rot: 45, tone: 'steel' },
      { s: 'rect', x: 68, y: 66, w: 10, h: 12, rot: -45, tone: 'steel' },
    ],
    lock: [
      { s: 'rect', x: 26, y: 42, w: 48, h: 44, tone: 'brass' },
      { s: 'arc', cx: 50, cy: 42, r: 16, a0: 180, a1: 360, t: 7, tone: 'steel' },
      { s: 'blob', cx: 50, cy: 60, r: 6, tone: 'ink', edge: 0 },
      { s: 'rect', x: 47, y: 62, w: 6, h: 12, tone: 'ink', edge: 0 },
    ],
    shield: [
      { s: 'path', pts: [[50, 12], [82, 24], [82, 52], [50, 88], [18, 52], [18, 24]], tone: 'steel' },
      { s: 'path', pts: [[50, 22], [72, 30], [72, 50], [50, 76], [28, 50], [28, 30]], tone: 'paper', edge: 0 },
      { s: 'path', pts: [[40, 48], [47, 58], [62, 34], [66, 38], [48, 68], [36, 52]], tone: 'accent', edge: 0 },
    ],
    flag: [
      { s: 'rect', x: 28, y: 14, w: 5, h: 72, tone: 'wood' },
      { s: 'path', pts: [[33, 16], [80, 24], [72, 40], [80, 56], [33, 48]], tone: 'accent' },
    ],
    anchor: [
      { s: 'ring', cx: 50, cy: 22, r: 9, t: 5, tone: 'steel' },
      { s: 'rect', x: 46, y: 28, w: 8, h: 48, tone: 'steel' },
      { s: 'rect', x: 28, y: 40, w: 44, h: 7, tone: 'steel' },
      { s: 'arc', cx: 50, cy: 62, r: 26, a0: 15, a1: 165, t: 8, tone: 'steel' },
      { s: 'path', pts: [[24, 66], [18, 78], [32, 76]], tone: 'steel' },
      { s: 'path', pts: [[76, 66], [82, 78], [68, 76]], tone: 'steel' },
    ],
    map: [
      { s: 'path', pts: [[14, 26], [38, 18], [62, 26], [86, 18], [86, 66], [62, 74], [38, 66], [14, 74]], tone: 'paper' },
      { s: 'path', pts: [[14, 26], [14, 74], [38, 66], [38, 18]], tone: 'sky', edge: 0 },
      { s: 'path', pts: [[62, 26], [62, 74], [86, 66], [86, 18]], tone: 'leaf', edge: 0 },
      { s: 'petal', cx: 50, cy: 40, rx: 7, ry: 9, rot: 180, tone: 'accent', edge: 0 },
      { s: 'blob', cx: 50, cy: 44, r: 2.6, tone: 'paper', edge: 0 },
    ],
    target: [
      { s: 'blob', cx: 50, cy: 50, r: 34, tone: 'accent' },
      { s: 'ring', cx: 50, cy: 50, r: 24, t: 8, tone: 'paper' },
      { s: 'blob', cx: 50, cy: 50, r: 14, tone: 'accent' },
      { s: 'blob', cx: 50, cy: 50, r: 5, tone: 'paper', edge: 0 },
      { s: 'path', pts: [[74, 26], [88, 12], [90, 20], [80, 30]], tone: 'ink', edge: 0 },
    ],
    ladder: [
      { s: 'rect', x: 30, y: 10, w: 6, h: 80, tone: 'wood' },
      { s: 'rect', x: 64, y: 10, w: 6, h: 80, tone: 'wood' },
      { s: 'rect', x: 30, y: 22, w: 40, h: 6, tone: 'wood' },
      { s: 'rect', x: 30, y: 40, w: 40, h: 6, tone: 'wood' },
      { s: 'rect', x: 30, y: 58, w: 40, h: 6, tone: 'wood' },
      { s: 'rect', x: 30, y: 76, w: 40, h: 6, tone: 'wood' },
    ],
    stairs: [
      { s: 'rect', x: 14, y: 66, w: 20, h: 20, tone: 'wood' },
      { s: 'rect', x: 34, y: 48, w: 20, h: 38, tone: 'wood' },
      { s: 'rect', x: 54, y: 30, w: 20, h: 56, tone: 'wood' },
      { s: 'rect', x: 74, y: 14, w: 20, h: 72, tone: 'wood' },
    ],
    hourglass: [
      { s: 'path', pts: [[26, 18], [74, 18], [58, 48], [42, 48]], tone: 'sky' },
      { s: 'path', pts: [[42, 54], [58, 54], [74, 82], [26, 82]], tone: 'sky' },
      { s: 'path', pts: [[42, 56], [58, 56], [68, 78], [32, 78]], tone: 'sun', edge: 0 },
      { s: 'rect', x: 22, y: 12, w: 56, h: 8, tone: 'wood' },
      { s: 'rect', x: 22, y: 80, w: 56, h: 8, tone: 'wood' },
    ],
    coin: [
      { s: 'blob', cx: 50, cy: 50, r: 32, tone: 'brass' },
      { s: 'ring', cx: 50, cy: 50, r: 23, t: 3, tone: 'sunlit', edge: 0 },
      { s: 'rect', x: 46, y: 30, w: 8, h: 40, tone: 'sunlit', edge: 0 },
      { s: 'rect', x: 38, y: 36, w: 24, h: 5, tone: 'sunlit', edge: 0 },
      { s: 'rect', x: 38, y: 59, w: 24, h: 5, tone: 'sunlit', edge: 0 },
    ],
    trophy: [
      { s: 'path', pts: [[30, 20], [70, 20], [66, 52], [50, 62], [34, 52]], tone: 'brass' },
      { s: 'ring', cx: 24, cy: 32, r: 8, t: 5, tone: 'brass' },
      { s: 'ring', cx: 76, cy: 32, r: 8, t: 5, tone: 'brass' },
      { s: 'rect', x: 45, y: 60, w: 10, h: 12, tone: 'brass' },
      { s: 'rect', x: 32, y: 72, w: 36, h: 10, tone: 'wood' },
    ],
    crown: [
      { s: 'path', pts: [[22, 66], [22, 38], [36, 52], [50, 30], [64, 52], [78, 38], [78, 66]], tone: 'brass' },
      { s: 'rect', x: 22, y: 66, w: 56, h: 10, tone: 'brass' },
      { s: 'blob', cx: 50, cy: 60, r: 4, tone: 'accent', edge: 0 },
    ],
    phone: [
      { s: 'rect', x: 32, y: 14, w: 36, h: 72, tone: 'ink' },
      { s: 'rect', x: 36, y: 22, w: 28, h: 52, tone: 'paper', edge: 0 },
      { s: 'blob', cx: 50, cy: 80, r: 3, tone: 'paper', edge: 0 },
    ],
    laptop: [
      { s: 'rect', x: 22, y: 24, w: 56, h: 38, tone: 'ink' },
      { s: 'rect', x: 27, y: 29, w: 46, h: 28, tone: 'paper', edge: 0 },
      { s: 'path', pts: [[14, 68], [86, 68], [80, 78], [20, 78]], tone: 'ink' },
    ],
    camera: [
      { s: 'rect', x: 16, y: 34, w: 68, h: 44, tone: 'ink' },
      { s: 'blob', cx: 50, cy: 56, r: 15, tone: 'paper', edge: 0 },
      { s: 'blob', cx: 50, cy: 56, r: 8, tone: 'steel', edge: 0 },
      { s: 'rect', x: 22, y: 26, w: 18, h: 10, tone: 'ink' },
      { s: 'blob', cx: 74, cy: 42, r: 4, tone: 'accent', edge: 0 },
    ],
    dog: [
      { s: 'blob', cx: 52, cy: 58, r: 22, tone: 'wood' },
      { s: 'blob', cx: 34, cy: 34, r: 15, tone: 'wood' },
      { s: 'path', pts: [[24, 24], [16, 40], [28, 40]], tone: 'soil' },
      { s: 'path', pts: [[44, 24], [52, 40], [40, 40]], tone: 'soil' },
      { s: 'blob', cx: 34, cy: 40, r: 5.5, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 30, cy: 32, r: 2, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 38, cy: 32, r: 2, tone: 'ink', edge: 0 },
      { s: 'path', pts: [[70, 44], [88, 34], [82, 50]], tone: 'wood' },
    ],
    music_note: [
      { s: 'blob', cx: 34, cy: 72, rx: 10, ry: 8, tone: 'ink' },
      { s: 'blob', cx: 66, cy: 64, rx: 10, ry: 8, tone: 'ink' },
      { s: 'rect', x: 41, y: 24, w: 5, h: 48, tone: 'ink' },
      { s: 'rect', x: 73, y: 16, w: 5, h: 48, tone: 'ink' },
      { s: 'rect', x: 41, y: 18, w: 37, h: 9, rot: -8, tone: 'ink' },
    ],
    moon_stars: [],
    // ---- Domain pack: science + space ----
    atom: [
      { s: 'blob', cx: 50, cy: 50, r: 8, tone: 'accent' },
      { s: 'ring', cx: 50, cy: 50, r: 30, t: 3.4, tone: 'ink', edge: 0 },
      { s: 'ring', cx: 50, cy: 50, r: 30, t: 3.4, tone: 'ink', edge: 0, rot: 60, squash: 0.34 },
      { s: 'ring', cx: 50, cy: 50, r: 30, t: 3.4, tone: 'ink', edge: 0, rot: -60, squash: 0.34 },
    ],
    dna: [
      { s: 'rect', x: 38, y: 18, w: 5, h: 64, rot: -14, tone: 'water' },
      { s: 'rect', x: 57, y: 18, w: 5, h: 64, rot: 14, tone: 'water' },
      { s: 'rect', x: 36, y: 30, w: 28, h: 5, tone: 'accent', edge: 0 },
      { s: 'rect', x: 38, y: 48, w: 24, h: 5, tone: 'leaf', edge: 0 },
      { s: 'rect', x: 36, y: 66, w: 28, h: 5, tone: 'blush', edge: 0 },
    ],
    microscope: [
      { s: 'rect', x: 30, y: 82, w: 40, h: 7, tone: 'ink' },
      { s: 'path', pts: [[34, 82], [34, 30], [46, 30], [46, 48], [56, 56], [56, 82]], tone: 'steel' },
      { s: 'rect', x: 40, y: 14, w: 10, h: 22, rot: -12, tone: 'ink' },
      { s: 'rect', x: 42, y: 60, w: 18, h: 4, tone: 'brass', edge: 0 },
    ],
    brain: [
      { s: 'blob', cx: 50, cy: 52, rx: 32, ry: 26, tone: 'blush' },
      { s: 'blob', cx: 36, cy: 44, rx: 14, ry: 12, tone: 'blush', edge: 0 },
      { s: 'blob', cx: 64, cy: 44, rx: 14, ry: 12, tone: 'blush', edge: 0 },
      { s: 'path', pts: [[34, 58], [44, 50], [52, 60], [64, 52]], tone: 'accent', stroke: 3, edge: 0 },
      { s: 'path', pts: [[40, 38], [50, 44], [60, 36]], tone: 'accent', stroke: 3, edge: 0 },
    ],
    robot: [
      { s: 'rect', x: 26, y: 18, w: 48, h: 36, tone: 'steel' },
      { s: 'blob', cx: 40, cy: 34, r: 6, tone: 'sky', edge: 0 },
      { s: 'blob', cx: 60, cy: 34, r: 6, tone: 'sky', edge: 0 },
      { s: 'rect', x: 38, y: 45, w: 24, h: 4, tone: 'ink', edge: 0 },
      { s: 'rect', x: 48, y: 8, w: 4, h: 12, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 50, cy: 8, r: 4, tone: 'accent', edge: 0 },
      { s: 'rect', x: 32, y: 58, w: 36, h: 30, tone: 'steel' },
      { s: 'rect', x: 18, y: 58, w: 8, h: 22, tone: 'ink' },
      { s: 'rect', x: 74, y: 58, w: 8, h: 22, tone: 'ink' },
    ],
    chip: [
      { s: 'rect', x: 30, y: 30, w: 40, h: 40, tone: 'ink' },
      { s: 'rect', x: 38, y: 38, w: 24, h: 24, tone: 'leaf', edge: 0 },
      { s: 'rect', x: 22, y: 36, w: 8, h: 4, tone: 'ink' },
      { s: 'rect', x: 22, y: 48, w: 8, h: 4, tone: 'ink' },
      { s: 'rect', x: 22, y: 60, w: 8, h: 4, tone: 'ink' },
      { s: 'rect', x: 70, y: 36, w: 8, h: 4, tone: 'ink' },
      { s: 'rect', x: 70, y: 48, w: 8, h: 4, tone: 'ink' },
      { s: 'rect', x: 70, y: 60, w: 8, h: 4, tone: 'ink' },
    ],
    satellite: [
      { s: 'rect', x: 40, y: 38, w: 20, h: 24, rot: -20, tone: 'steel' },
      { s: 'rect', x: 14, y: 40, w: 20, h: 12, rot: -20, tone: 'sky' },
      { s: 'rect', x: 66, y: 40, w: 20, h: 12, rot: -20, tone: 'sky' },
      { s: 'blob', cx: 50, cy: 50, r: 3.4, tone: 'accent', edge: 0 },
      { s: 'arc', cx: 50, cy: 84, r: 18, a0: 200, a1: 340, t: 3, tone: 'ink', edge: 0 },
    ],
    planet_ringed: [
      { s: 'blob', cx: 50, cy: 50, r: 24, tone: 'accent' },
      { s: 'blob', cx: 42, cy: 42, rx: 8, ry: 6, tone: 'sunlit', op: 0.5, edge: 0 },
      { s: 'ring', cx: 50, cy: 50, r: 36, t: 6, tone: 'brass', rot: -18, squash: 0.32 },
    ],
    galaxy: [
      { s: 'path', pts: [[50, 50], [62, 44], [74, 46], [80, 56], [72, 64], [58, 62], [50, 56], [40, 58], [30, 52], [34, 42]], tone: 'sky', op: 0.85 },
      { s: 'blob', cx: 50, cy: 50, r: 7, tone: 'sunlit', edge: 0 },
      { s: 'path', pts: STAR_PTS, k: 0.16, ox: 16, oy: 20, tone: 'snow', edge: 0 },
      { s: 'path', pts: STAR_PTS, k: 0.13, ox: 72, oy: 72, tone: 'snow', edge: 0 },
    ],
    // ---- Domain pack: sport ----
    soccer_ball: [
      { s: 'blob', cx: 50, cy: 50, r: 30, tone: 'snow' },
      { s: 'path', pts: [[50, 38], [61, 46], [57, 59], [43, 59], [39, 46]], tone: 'ink', edge: 0 },
      { s: 'path', pts: [[50, 22], [58, 30], [42, 30]], tone: 'ink', edge: 0, op: 0.85 },
      { s: 'path', pts: [[22, 46], [34, 50], [30, 62], [20, 58]], tone: 'ink', edge: 0, op: 0.85 },
      { s: 'path', pts: [[78, 46], [66, 50], [70, 62], [80, 58]], tone: 'ink', edge: 0, op: 0.85 },
    ],
    basketball: [
      { s: 'blob', cx: 50, cy: 50, r: 30, tone: 'fire' },
      { s: 'rect', x: 20, y: 48, w: 60, h: 4, tone: 'ink', edge: 0 },
      { s: 'rect', x: 48, y: 20, w: 4, h: 60, tone: 'ink', edge: 0 },
      { s: 'path', pts: [[22, 30], [40, 44], [60, 44], [78, 30]], tone: 'ink', stroke: 4, edge: 0 },
      { s: 'path', pts: [[22, 70], [40, 56], [60, 56], [78, 70]], tone: 'ink', stroke: 4, edge: 0 },
    ],
    tennis: [
      { s: 'blob', cx: 50, cy: 50, r: 26, tone: 'sun' },
      { s: 'arc', cx: 50, cy: 50, r: 20, a0: 140, a1: 260, t: 5, tone: 'snow', edge: 0 },
      { s: 'arc', cx: 50, cy: 50, r: 20, a0: -40, a1: 80, t: 5, tone: 'snow', edge: 0 },
    ],
    racket: [
      { s: 'blob', cx: 50, cy: 38, rx: 20, ry: 26, tone: 'accent' },
      { s: 'blob', cx: 50, cy: 38, rx: 14, ry: 19, tone: 'paper', edge: 0 },
      { s: 'rect', x: 47, y: 62, w: 7, h: 28, rot: 8, tone: 'wood' },
    ],
    medal: [
      { s: 'blob', cx: 50, cy: 62, r: 18, tone: 'brass' },
      { s: 'path', pts: [[38, 8], [50, 40], [62, 8]], tone: 'accent', edge: 0 },
      { s: 'blob', cx: 50, cy: 62, r: 9, tone: 'sunlit', edge: 0 },
    ],
    whistle: [
      { s: 'blob', cx: 44, cy: 56, rx: 24, ry: 18, tone: 'steel' },
      { s: 'rect', x: 62, y: 44, w: 22, h: 12, tone: 'steel' },
      { s: 'blob', cx: 40, cy: 54, r: 6, tone: 'ink', edge: 0 },
    ],
    // ---- Domain pack: animals ----
    rabbit: [
      { s: 'blob', cx: 50, cy: 62, rx: 18, ry: 16, tone: 'paper' },
      { s: 'blob', cx: 50, cy: 34, r: 13, tone: 'paper' },
      { s: 'petal', cx: 42, cy: 16, rx: 5, ry: 13, rot: -10, tone: 'paper' },
      { s: 'petal', cx: 58, cy: 16, rx: 5, ry: 13, rot: 10, tone: 'paper' },
      { s: 'blob', cx: 45, cy: 32, r: 2.2, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 55, cy: 32, r: 2.2, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 50, cy: 38, r: 2, tone: 'blush', edge: 0 },
    ],
    owl: [
      { s: 'blob', cx: 50, cy: 54, rx: 22, ry: 26, tone: 'wood' },
      { s: 'blob', cx: 40, cy: 38, r: 9, tone: 'paper' },
      { s: 'blob', cx: 60, cy: 38, r: 9, tone: 'paper' },
      { s: 'blob', cx: 40, cy: 38, r: 3.6, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 60, cy: 38, r: 3.6, tone: 'ink', edge: 0 },
      { s: 'path', pts: [[50, 44], [46, 52], [54, 52]], tone: 'brass', edge: 0 },
      { s: 'path', pts: [[34, 18], [42, 30], [30, 28]], tone: 'wood' },
      { s: 'path', pts: [[66, 18], [58, 30], [70, 28]], tone: 'wood' },
    ],
    whale: [
      { s: 'blob', cx: 46, cy: 56, rx: 34, ry: 18, tone: 'deep' },
      { s: 'path', pts: [[74, 50], [92, 40], [86, 58], [92, 72], [72, 62]], tone: 'deep' },
      { s: 'blob', cx: 30, cy: 52, r: 3, tone: 'paper', edge: 0 },
      { s: 'path', pts: [[20, 70], [46, 76], [72, 68]], tone: 'paper', stroke: 4, edge: 0 },
      { s: 'path', pts: [[40, 30], [38, 18], [44, 22]], tone: 'deep' },
      { s: 'path', pts: [[50, 30], [52, 16], [46, 22]], tone: 'deep' },
    ],
    turtle: [
      { s: 'blob', cx: 50, cy: 56, rx: 26, ry: 18, tone: 'leaf' },
      { s: 'path', pts: [[36, 48], [50, 42], [64, 48], [60, 60], [40, 60]], tone: 'sage', edge: 0 },
      { s: 'blob', cx: 18, cy: 54, r: 8, tone: 'leaf' },
      { s: 'blob', cx: 16, cy: 52, r: 2, tone: 'ink', edge: 0 },
      { s: 'petal', cx: 78, cy: 62, rx: 8, ry: 4, rot: 20, tone: 'leaf' },
    ],
    bee: [
      { s: 'blob', cx: 50, cy: 56, rx: 20, ry: 14, tone: 'sun' },
      { s: 'rect', x: 40, y: 44, w: 6, h: 26, rot: 90, tone: 'ink', edge: 0 },
      { s: 'rect', x: 54, y: 44, w: 6, h: 26, rot: 90, tone: 'ink', edge: 0 },
      { s: 'petal', cx: 42, cy: 34, rx: 10, ry: 6, rot: -30, tone: 'snow', op: 0.8 },
      { s: 'petal', cx: 58, cy: 34, rx: 10, ry: 6, rot: 30, tone: 'snow', op: 0.8 },
      { s: 'path', pts: [[70, 56], [80, 58], [70, 62]], tone: 'ink', edge: 0 },
    ],
    frog: [
      { s: 'blob', cx: 50, cy: 62, rx: 26, ry: 18, tone: 'leaf' },
      { s: 'blob', cx: 38, cy: 42, r: 8, tone: 'leaf' },
      { s: 'blob', cx: 62, cy: 42, r: 8, tone: 'leaf' },
      { s: 'blob', cx: 38, cy: 42, r: 3, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 62, cy: 42, r: 3, tone: 'ink', edge: 0 },
      { s: 'path', pts: [[38, 66], [50, 72], [62, 66]], tone: 'ink', stroke: 3, edge: 0 },
    ],
    fox: [
      { s: 'blob', cx: 50, cy: 56, rx: 22, ry: 18, tone: 'fire' },
      { s: 'path', pts: [[34, 40], [30, 16], [46, 32]], tone: 'fire' },
      { s: 'path', pts: [[66, 40], [70, 16], [54, 32]], tone: 'fire' },
      { s: 'path', pts: [[36, 56], [50, 76], [64, 56], [64, 42], [36, 42]], tone: 'paper', edge: 0, op: 0.9 },
      { s: 'blob', cx: 43, cy: 48, r: 2.6, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 57, cy: 48, r: 2.6, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 50, cy: 66, r: 3, tone: 'ink', edge: 0 },
    ],
    lion: [
      { s: 'blob', cx: 50, cy: 50, r: 32, tone: 'soil' },
      { s: 'blob', cx: 50, cy: 50, r: 22, tone: 'sun' },
      { s: 'blob', cx: 42, cy: 46, r: 3, tone: 'ink', edge: 0 },
      { s: 'blob', cx: 58, cy: 46, r: 3, tone: 'ink', edge: 0 },
      { s: 'path', pts: [[46, 58], [50, 62], [54, 58]], tone: 'ink', edge: 0 },
      { s: 'blob', cx: 50, cy: 54, r: 3, tone: 'soil', edge: 0 },
    ],
    elephant: [
      { s: 'blob', cx: 48, cy: 52, rx: 26, ry: 20, tone: 'grey' },
      { s: 'blob', cx: 74, cy: 44, rx: 14, ry: 12, tone: 'grey' },
      { s: 'rect', x: 76, y: 50, w: 9, h: 26, rot: 12, tone: 'grey' },
      { s: 'blob', cx: 30, cy: 40, rx: 12, ry: 14, tone: 'slate' },
      { s: 'blob', cx: 72, cy: 42, r: 2.6, tone: 'ink', edge: 0 },
      { s: 'rect', x: 34, y: 68, w: 8, h: 18, tone: 'grey' },
      { s: 'rect', x: 58, y: 68, w: 8, h: 18, tone: 'grey' },
    ],
    // ---- Domain pack: nature / weather ----
    volcano: [
      { s: 'path', pts: [[10, 90], [38, 30], [62, 30], [90, 90]], tone: 'soil' },
      { s: 'path', pts: [[38, 30], [62, 30], [56, 42], [44, 42]], tone: 'fire' },
      { s: 'petal', cx: 50, cy: 20, rx: 6, ry: 10, tone: 'fire' },
      { s: 'blob', cx: 44, cy: 14, r: 5, tone: 'warm' },
      { s: 'blob', cx: 58, cy: 18, r: 4, tone: 'warm' },
    ],
    cactus: [
      { s: 'rect', x: 44, y: 24, w: 12, h: 62, tone: 'leaf' },
      { s: 'path', pts: [[44, 44], [30, 44], [30, 30], [24, 30], [24, 52], [44, 52]], tone: 'leaf' },
      { s: 'path', pts: [[56, 58], [70, 58], [70, 44], [76, 44], [76, 66], [56, 66]], tone: 'sage' },
      { s: 'blob', cx: 50, cy: 20, r: 6, tone: 'blush', edge: 0 },
    ],
    iceberg: [
      { s: 'path', pts: [[20, 56], [34, 26], [48, 40], [62, 22], [80, 56]], tone: 'snow' },
      { s: 'rect', x: 10, y: 56, w: 80, h: 4, tone: 'water', edge: 0 },
      { s: 'path', pts: [[28, 60], [44, 88], [60, 78], [72, 60]], tone: 'sky', op: 0.8 },
    ],
    tornado: [
      { s: 'path', pts: [[26, 20], [74, 20], [66, 34], [34, 34]], tone: 'slate' },
      { s: 'path', pts: [[34, 38], [68, 38], [60, 52], [40, 52]], tone: 'grey' },
      { s: 'path', pts: [[42, 56], [60, 56], [55, 70], [46, 70]], tone: 'slate' },
      { s: 'path', pts: [[46, 74], [56, 74], [50, 88]], tone: 'grey' },
    ],
    umbrella: [
      { s: 'path', pts: [[50, 22], [86, 50], [68, 44], [50, 50], [32, 44], [14, 50]], tone: 'blush' },
      { s: 'rect', x: 48, y: 48, w: 4.5, h: 36, tone: 'wood' },
      { s: 'arc', cx: 55, cy: 84, r: 7, a0: 0, a1: 180, t: 4.5, tone: 'wood' },
      { s: 'path', pts: [[50, 14], [50, 24], [53, 20]], tone: 'wood', edge: 0 },
    ],
    shell: [
      { s: 'path', pts: [[50, 84], [22, 60], [30, 34], [50, 22], [70, 34], [78, 60]], tone: 'blush' },
      { s: 'path', pts: [[50, 82], [50, 30]], tone: 'paper', stroke: 3, edge: 0 },
      { s: 'path', pts: [[34, 74], [38, 36]], tone: 'paper', stroke: 3, edge: 0 },
      { s: 'path', pts: [[66, 74], [62, 36]], tone: 'paper', stroke: 3, edge: 0 },
    ],
    coral: [
      { s: 'rect', x: 46, y: 44, w: 8, h: 44, tone: 'blush' },
      { s: 'rect', x: 32, y: 54, w: 8, h: 30, rot: -24, tone: 'blush' },
      { s: 'rect', x: 60, y: 50, w: 8, h: 34, rot: 24, tone: 'accent' },
      { s: 'rect', x: 20, y: 62, w: 7, h: 22, rot: -38, tone: 'accent' },
      { s: 'rect', x: 72, y: 62, w: 7, h: 22, rot: 38, tone: 'blush' },
    ],
    mushroom_cluster: [
      { s: 'path', pts: [[30, 92], [34, 66], [42, 66], [46, 92]], tone: 'paper' },
      { s: 'blob', cx: 38, cy: 58, rx: 16, ry: 10, tone: 'blush' },
      { s: 'path', pts: [[56, 92], [60, 74], [66, 74], [70, 92]], tone: 'paper' },
      { s: 'blob', cx: 63, cy: 68, rx: 12, ry: 8, tone: 'accent' },
    ],
    // ---- Domain pack: arts + music ----
    guitar: [
      { s: 'blob', cx: 50, cy: 64, rx: 20, ry: 16, tone: 'wood' },
      { s: 'blob', cx: 50, cy: 48, rx: 14, ry: 12, tone: 'wood' },
      { s: 'blob', cx: 50, cy: 52, r: 5, tone: 'ink', edge: 0 },
      { s: 'rect', x: 48, y: 10, w: 4.5, h: 40, tone: 'wood' },
      { s: 'rect', x: 43, y: 6, w: 14, h: 8, tone: 'ink' },
    ],
    drum: [
      { s: 'rect', x: 28, y: 44, w: 44, h: 34, tone: 'accent' },
      { s: 'blob', cx: 50, cy: 44, rx: 22, ry: 7, tone: 'paper' },
      { s: 'rect', x: 20, y: 20, w: 4, h: 22, rot: 20, tone: 'wood' },
      { s: 'rect', x: 76, y: 20, w: 4, h: 22, rot: -20, tone: 'wood' },
      { s: 'blob', cx: 26, cy: 18, r: 4, tone: 'wood', edge: 0 },
      { s: 'blob', cx: 74, cy: 18, r: 4, tone: 'wood', edge: 0 },
    ],
    palette_art: [
      { s: 'blob', cx: 48, cy: 50, rx: 32, ry: 26, tone: 'wood' },
      { s: 'blob', cx: 34, cy: 42, r: 4.5, tone: 'blush', edge: 0 },
      { s: 'blob', cx: 46, cy: 34, r: 4.5, tone: 'sun', edge: 0 },
      { s: 'blob', cx: 60, cy: 38, r: 4.5, tone: 'leaf', edge: 0 },
      { s: 'blob', cx: 66, cy: 52, r: 4.5, tone: 'water', edge: 0 },
      { s: 'blob', cx: 62, cy: 62, r: 6, tone: 'paper', edge: 0 },
    ],
    paintbrush: [
      { s: 'rect', x: 46, y: 14, w: 7, h: 46, rot: -22, tone: 'wood' },
      { s: 'path', pts: [[38, 62], [52, 66], [48, 88], [34, 80]], tone: 'blush' },
      { s: 'rect', x: 41, y: 56, w: 10, h: 6, rot: -22, tone: 'brass', edge: 0 },
    ],
    // ---- Domain pack: misc life ----
    bell: [
      { s: 'path', pts: [[32, 70], [36, 44], [42, 28], [50, 24], [58, 28], [64, 44], [68, 70]], tone: 'brass' },
      { s: 'rect', x: 28, y: 70, w: 44, h: 7, tone: 'brass' },
      { s: 'blob', cx: 50, cy: 82, r: 5, tone: 'ink' },
    ],
    candle_lantern: [
      { s: 'rect', x: 32, y: 26, w: 36, h: 52, tone: 'ink' },
      { s: 'rect', x: 37, y: 32, w: 26, h: 40, tone: 'sunlit', edge: 0 },
      { s: 'petal', cx: 50, cy: 52, rx: 4.5, ry: 8, tone: 'sun', edge: 0 },
      { s: 'arc', cx: 50, cy: 26, r: 10, a0: 180, a1: 360, t: 4, tone: 'ink', edge: 0 },
    ],
    paper_boat: [
      { s: 'path', pts: [[14, 62], [86, 62], [66, 82], [34, 82]], tone: 'paper' },
      { s: 'path', pts: [[50, 30], [72, 62], [50, 62]], tone: 'paper', edge: 0 },
      { s: 'path', pts: [[50, 38], [28, 62], [50, 62]], tone: 'snow', edge: 0 },
    ],
    hot_air_balloon: [
      { s: 'blob', cx: 50, cy: 40, rx: 26, ry: 30, tone: 'blush' },
      { s: 'path', pts: [[50, 10], [64, 22], [64, 56], [50, 68], [36, 56], [36, 22]], tone: 'accent', edge: 0, op: 0.5 },
      { s: 'rect', x: 42, y: 76, w: 16, h: 12, tone: 'wood' },
      { s: 'rect', x: 38, y: 66, w: 3, h: 12, tone: 'ink', edge: 0 },
      { s: 'rect', x: 59, y: 66, w: 3, h: 12, tone: 'ink', edge: 0 },
    ],
  };
  // Phrases collapse onto the nearest drawn concept — modifiers (colours, moods,
  // counts) never block the mark the noun beneath them owns.
  const PAPER_ALIAS = {
    moon: 'moon-full', 'full-moon': 'moon-full', 'same-moon': 'moon-full',
    'crescent-moon': 'moon-crescent', crescent: 'moon-crescent', 'half-moon': 'moon-half',
    'cloudy-night': 'cloud', 'heavy-rain': 'rain', drizzle: 'rain', shower: 'rain',
    'rain-cloud': 'rain', lightning: 'storm', thunder: 'storm',
    globe: 'earth', world: 'earth', planet: 'earth',
    seedling: 'sprout', sapling: 'sprout', shoot: 'sprout', sprig: 'sprout',
    'hand-down': 'hand', 'magnifying-glass': 'magnifier', magnifying: 'magnifier',
    envelope: 'letter', mail: 'letter', sailboat: 'boat', ship: 'boat',
    sunflower: 'sunflower', bulb: 'lightbulb', idea: 'lightbulb', light: 'sun',
    sunshine: 'sun', firelight: 'fire', flame: 'fire', droplet: 'drop', water: 'drop',
    ocean: 'wave', sea: 'wave', hills: 'hill', mountains: 'mountain', dove: 'bird',
    'night-sky': 'stars', snowflake: 'snowflake', 'gift-box': 'gift', present: 'gift',
    breeze: 'wind', question: 'lightbulb',
    drive: 'car', driving: 'car', taxi: 'car', ride: 'car', vehicle: 'car',
    van: 'bus', tram: 'train', subway: 'train', locomotive: 'train', bike: 'bicycle', cycle: 'bicycle',
    cycling: 'bicycle', launch: 'rocket', spaceship: 'rocket', shuttle: 'rocket', jet: 'plane',
    airplane: 'plane', flight: 'plane', fly: 'plane',
    morning: 'sunrise', sunrise: 'sunrise', dawn: 'sunrise', wakeup: 'alarm_clock', 'wake-up': 'alarm_clock',
    'alarm-clock': 'alarm_clock', sleep: 'bed', bedtime: 'bed', doorway: 'door', exit: 'door',
    money: 'coin', dollar: 'coin', cents: 'coin', payment: 'coin', gold: 'coin', prize: 'trophy',
    winner: 'trophy', award: 'trophy', trophy: 'trophy', goal: 'target', aim: 'target', bullseye: 'target',
    progress: 'stairs', climb: 'ladder', climbing: 'ladder', steps: 'stairs', engine: 'gear', machine: 'gear',
    settings: 'gear', motor: 'gear', security: 'lock', safe: 'lock', locked: 'lock', protect: 'shield',
    defense: 'shield', camera: 'camera', photo: 'camera', picture: 'camera', computer: 'laptop',
    device: 'phone', mobile: 'phone', telephone: 'phone', call: 'phone', pen: 'pencil', write: 'pencil',
    writing: 'pencil', draw: 'pencil', cut: 'scissors', craft: 'scissors', map: 'map', navigate: 'map',
    direction: 'map', country: 'flag', nation: 'flag', puppy: 'dog', hound: 'dog', song: 'music_note',
    tune: 'music_note', melody: 'music_note', music: 'music_note', 'music-note': 'music_note',
    timer: 'hourglass', waiting: 'hourglass', 'old': 'hourglass', royalty: 'crown', king: 'crown',
    queen: 'crown', 'alarm': 'alarm_clock',
    // ---- Domain pack aliases ----
    molecule: 'atom', particle: 'atom', physics: 'atom', nucleus: 'atom',
    gene: 'dna', genetics: 'dna', helix: 'dna', chromosome: 'dna', heredity: 'dna',
    laboratory: 'microscope', lab: 'microscope', biology: 'microscope', cells: 'microscope',
    mind: 'brain', think: 'brain', thinking: 'brain', intelligence: 'brain', ai: 'brain',
    bot: 'robot', android: 'robot', machine_ai: 'robot',
    processor: 'chip', computer_chip: 'chip', circuit: 'chip', microchip: 'chip', cpu: 'chip',
    satellite_dish: 'satellite', 'satellite-dish': 'satellite', orbit: 'satellite',
    saturn: 'planet_ringed', 'ringed-planet': 'planet_ringed', planets: 'planet_ringed',
    universe: 'galaxy', cosmos: 'galaxy', milkyway: 'galaxy', 'milky-way': 'galaxy',
    football: 'soccer_ball', soccer: 'soccer_ball', 'soccer-ball': 'soccer_ball', ball: 'soccer_ball',
    hoop: 'basketball', 'basket-ball': 'basketball',
    'tennis-ball': 'tennis', golf: 'tennis', 'ping-pong': 'tennis',
    'tennis-racket': 'racket', bat: 'racket',
    champion: 'medal', gold_medal: 'medal', 'gold-medal': 'medal', olympic: 'medal', olympics: 'medal',
    referee: 'whistle',
    bunny: 'rabbit', hare: 'rabbit',
    'night-owl': 'owl', wise: 'owl',
    'blue-whale': 'whale', orca: 'whale',
    tortoise: 'turtle', 'sea-turtle': 'turtle',
    honeybee: 'bee', insect: 'bee', bug: 'bee',
    toad: 'frog',
    wolf: 'fox', clever: 'fox',
    'lion-king': 'lion', jungle: 'lion',
    mammoth: 'elephant',
    eruption: 'volcano', lava: 'volcano',
    desert: 'cactus', succulent: 'cactus',
    arctic: 'iceberg', antarctic: 'iceberg', glacier: 'iceberg',
    hurricane: 'tornado', cyclone: 'tornado', twister: 'tornado',
    rain_protection: 'umbrella', parasol: 'umbrella',
    seashell: 'shell', beach: 'shell',
    reef: 'coral', 'coral-reef': 'coral',
    mushrooms: 'mushroom_cluster', fungi: 'mushroom_cluster',
    acoustic: 'guitar', rock_music: 'guitar',
    percussion: 'drum', beat: 'drum',
    painting: 'palette_art', painter: 'palette_art', artist: 'palette_art',
    brush: 'paintbrush',
    school_bell: 'bell', church: 'bell', notification: 'bell',
    lantern: 'candle_lantern', lamp: 'candle_lantern',
    'paper-boat': 'paper_boat', origami: 'paper_boat',
    balloon_ride: 'hot_air_balloon', 'hot-air-balloon': 'hot_air_balloon',
    snow: 'snowflake', winter: 'snowflake',
  };
  function paperArtKey(concept) {
    if (!concept) return null;
    const norm = String(concept).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
    if (!norm) return null;
    const k = norm.replace(/\s+/g, '-');
    const direct = PAPER_ALIAS[k] || k;
    if (PAPER_ART[direct]) return direct;
    const words = norm.split(' ');
    for (let drop = 1; drop < words.length; drop += 1) {
      for (const c of [words.slice(drop).join('-'), words.slice(0, words.length - drop).join('-')]) {
        const a = PAPER_ALIAS[c] || c;
        if (PAPER_ART[a]) return a;
      }
    }
    for (const w of words) {
      const a = PAPER_ALIAS[w] || w;
      if (PAPER_ART[a]) return a;
    }
    return null;
  }
  // Expand one authored piece into flat parts in normalized space. `stroke` pieces
  // draw as ink lines (veins, strings); everything else is a filled cut shape.
  function paperPieceParts(pc, seed) {
    const r = rng(seed);
    const jx = (r() - 0.5) * 2.4, jy = (r() - 0.5) * 2.4;
    const rot = (pc.rot || 0) + (r() - 0.5) * 4;
    const cx = pc.cx != null ? pc.cx : (pc.x != null ? pc.x + pc.w / 2 : 50);
    const cy = pc.cy != null ? pc.cy : (pc.y != null ? pc.y + pc.h / 2 : 50);
    const tf = `translate(${f2(jx)} ${f2(jy)}) rotate(${f2(rot)} ${f2(cx)} ${f2(cy)})`;
    const edge = pc.edge !== 0;
    const out = [];
    const push = (d, o) => out.push({ d, tf, edge, tone: pc.tone, op: pc.op == null ? 1 : pc.op, sw: pc.stroke || 0, ...o });
    const arcD = (rax, ray, x0, y0, x1, y1, sweep) => `M${f2(x0)} ${f2(y0)}A${f2(rax)} ${f2(ray)} 0 0 ${sweep} ${f2(x1)} ${f2(y1)}`;
    switch (pc.s) {
      case 'blob':
        push(cutBlobPath(cx, cy, pc.rx || pc.r || 10, pc.ry || pc.r || 10, seed));
        break;
      case 'rect':
        push(cutRectPath({ x: pc.x, y: pc.y, w: pc.w, h: pc.h }, seed, Math.min(pc.w, pc.h) * 0.16));
        break;
      case 'path': {
        const k = pc.k || 1, ox = pc.ox || 0, oy = pc.oy || 0;
        if (pc.stroke) {
          push(polyPath(pc.pts.map((p) => [ox + p[0] * k, oy + p[1] * k])), { edge: 0 });
        } else {
          const pts = pc.pts.map((p) => [ox + p[0] * k + (r() - 0.5) * 1.6, oy + p[1] * k + (r() - 0.5) * 1.6]);
          push(polyPath(pts) + 'Z');
        }
        break;
      }
      case 'petal': {
        const rx = pc.rx || 8, ry = pc.ry || 14, k = 1 + (r() - 0.5) * 0.12;
        push(`M${f2(cx)} ${f2(cy - ry)}Q${f2(cx + rx * k)} ${f2(cy - ry * 0.1)} ${f2(cx)} ${f2(cy + ry)}Q${f2(cx - rx * k)} ${f2(cy - ry * 0.1)} ${f2(cx)} ${f2(cy - ry)}Z`);
        break;
      }
      case 'crescent': {
        const rr = pc.r || 26, bite = pc.bite == null ? 0.62 : pc.bite;
        push(`M${f2(cx + rr * 0.1)} ${f2(cy - rr)}A${f2(rr)} ${f2(rr)} 0 1 0 ${f2(cx + rr * 0.1)} ${f2(cy + rr)}A${f2(rr * bite)} ${f2(rr * bite)} 0 1 1 ${f2(cx + rr * 0.1)} ${f2(cy - rr)}Z`);
        break;
      }
      case 'halfdisc': {
        const rr = pc.r || 26;
        push(`M${f2(cx)} ${f2(cy - rr)}A${f2(rr)} ${f2(rr)} 0 0 1 ${f2(cx)} ${f2(cy + rr)}Z`);
        break;
      }
      case 'rays': {
        for (let i = 0; i < (pc.n || 8); i += 1) {
          const a = (i / (pc.n || 8)) * 360 + (r() - 0.5) * 8;
          out.push({
            d: cutRectPath({ x: cx - (pc.w || 7) / 2, y: cy - pc.r1, w: pc.w || 7, h: pc.r1 - pc.r0 }, seed ^ (i * 0x9e37), 1.4),
            tf: `translate(${f2(jx)} ${f2(jy)}) rotate(${f2(a)} ${f2(cx)} ${f2(cy)})`,
            edge, tone: pc.tone, op: pc.op == null ? 1 : pc.op, sw: 0,
          });
        }
        break;
      }
      case 'ring': {
        const rr = pc.r || 20, sq = pc.squash || 1;
        const ry2 = rr * sq;
        push(`${arcD(rr, ry2, cx - rr, cy, cx + rr, cy, 1)}${arcD(rr, ry2, cx + rr, cy, cx - rr, cy, 1)}`, { sw: pc.t || 5 });
        break;
      }
      case 'arc': {
        const rr = pc.r || 20, a0 = (pc.a0 == null ? 0 : pc.a0) * Math.PI / 180, a1 = (pc.a1 == null ? 180 : pc.a1) * Math.PI / 180;
        const x0 = cx + Math.cos(a0) * rr, y0 = cy + Math.sin(a0) * rr;
        const x1 = cx + Math.cos(a1) * rr, y1 = cy + Math.sin(a1) * rr;
        const sweep = ((a1 - a0 + Math.PI * 4) % (Math.PI * 2)) <= Math.PI ? 1 : 0;
        push(arcD(rr, rr, x0, y0, x1, y1, sweep), { sw: pc.t || 5, edge: 0 });
        break;
      }
      default:
        break;
    }
    return out;
  }
  // One composed illustration: die-cut edge under all pieces, each piece a painted
  // fill, a clipped wash + two seeded blotches over the union for the watercolour
  // settle. Returns the art's <g> in normalized 100x100 space plus its flat els
  // for draw-on staggering.
  function paperArtGroup(key, seed, plan, uid, hero) {
    const pieces = PAPER_ART[key] || [];
    const parts = [];
    pieces.forEach((pc, i) => parts.push(...paperPieceParts(pc, seed ^ (i * 0x9e3779b1))));
    if (!parts.length) return null;
    const g = svgEl('g', {}, null);
    const edgeParts = parts.filter((p) => p.edge && !p.sw);
    const els = [];
    if (edgeParts.length && plan.book !== 'paperbook') {
      const under = svgEl('g', { transform: 'translate(50 50) scale(1.09) translate(-50 -50)' }, g);
      for (const p of edgeParts) svgEl('path', { d: p.d, fill: mixColor(plan.brand.paper, '#ffffff', 0.62), transform: p.tf || undefined }, under);
      els.push(under);
    }
    const body = svgEl('g', {}, g);
    const poolBlur = `pabl_${uid}`;
    {
      const defs0 = svgEl('defs', {}, body);
      const bf = svgEl('filter', { id: poolBlur, x: '-15%', y: '-15%', width: '130%', height: '130%' }, defs0);
      svgEl('feGaussianBlur', { stdDeviation: '1.1' }, bf);
    }
    const mr = rng(seed ^ 0x61c3);
    const mdx = f2(0.7 + mr() * 0.9), mdy = f2(0.5 + mr() * 0.8);
    for (const p of parts) {
      if (!p.sw && p.op >= 0.4 && p.tone !== 'paper') {
        // Plate misregistration: a darker copy of the fill offset a hair reads as a
        // second print pass gone a touch off-register — and stands in for the pooled
        // rim inside cloned slots, where url(#) filters do not paint.
        const dupe = svgEl('path', { d: p.d, fill: mixColor(paintTone(p.tone, plan), plan.brand.ink, 0.42), 'fill-opacity': f2(Math.min(0.16, p.op * 0.16)), transform: `translate(${mdx} ${mdy}) ${p.tf || ''}`.trim() }, body);
        els.push(dupe);
        if (plan.book !== 'paperbook') {
          svgEl('path', { d: p.d, fill: mixColor(paintTone(p.tone, plan), plan.brand.ink, 0.3), 'fill-opacity': f2(Math.min(0.4, p.op * 0.3)), transform: p.tf || undefined, filter: `url(#${poolBlur})` }, body);
        }
      }
      // Pigment edge: a same-path stroke a tone deeper than the fill reads as paint
      // gathered at the cut edge — hand-laid, not bucket-filled.
      const edgeInk = p.sw || p.op < 0.35 || p.tone === 'paper' ? 'none' : mixColor(paintTone(p.tone, plan), plan.brand.ink, 0.45);
      // Sumi bleed: pigment wicks a hair into the fibres — a wider ghost copy of
      // the same mark in diluted ink laid down first (InkPainting's soak model).
      if (plan.book === 'paperbook' && p.op >= 0.4) {
        if (p.sw) {
          els.push(svgEl('path', { d: p.d, fill: 'none', stroke: mixColor(paintTone(p.tone, plan), plan.brand.ink, 0.5), 'stroke-width': f2(p.sw * 1.9), 'stroke-linecap': 'round', 'stroke-opacity': '0.10', transform: p.tf || undefined }, body));
        } else if (p.tone !== 'paper') {
          els.push(svgEl('path', { d: p.d, fill: 'none', stroke: mixColor(paintTone(p.tone, plan), plan.brand.ink, 0.55), 'stroke-width': '2.6', 'stroke-opacity': '0.09', 'stroke-linejoin': 'round', transform: p.tf || undefined }, body));
        }
      }
      const elp = p.sw
        ? svgEl('path', { d: p.d, fill: 'none', stroke: paintTone(p.tone, plan), 'stroke-width': f2(p.sw), 'stroke-linecap': 'round', 'stroke-opacity': f2(p.op), transform: p.tf || undefined }, body)
        : svgEl('path', { d: p.d, fill: paintTone(p.tone, plan), 'fill-opacity': f2(p.op), stroke: edgeInk, 'stroke-width': f2(1.1), 'stroke-opacity': edgeInk === 'none' ? '0' : '0.3', 'stroke-linejoin': 'round', transform: p.tf || undefined }, body);
      els.push(elp);
    }
    if (edgeParts.length) {
      const defs = svgEl('defs', {}, g);
      const clip = svgEl('clipPath', { id: `pac_${uid}` }, defs);
      for (const p of edgeParts) svgEl('path', { d: p.d, transform: p.tf || undefined }, clip);
      const grad = svgEl('linearGradient', { id: `paw_${uid}`, x1: '0', y1: '0', x2: '0.3', y2: '1' }, defs);
      svgEl('stop', { offset: '0', 'stop-color': '#ffffff', 'stop-opacity': '0.16' }, grad);
      svgEl('stop', { offset: '0.45', 'stop-color': '#ffffff', 'stop-opacity': '0' }, grad);
      svgEl('stop', { offset: '1', 'stop-color': plan.brand.ink, 'stop-opacity': '0.1' }, grad);
      const wr = rng(seed ^ 0x51ab);
      const wash = svgEl('g', { 'clip-path': `url(#pac_${uid})` }, g);
      svgEl('rect', { x: '-10', y: '-10', width: '120', height: '120', fill: `url(#paw_${uid})` }, wash);
      for (let bi = 0; bi < 5; bi += 1) {
        const bt = wr() < 0.55 ? '#ffffff' : plan.brand.ink;
        svgEl('path', { d: cutBlobPath(12 + wr() * 76, 14 + wr() * 72, 14 + wr() * 22, 12 + wr() * 20, seed ^ (0x77aa + bi * 0x1f1f)), fill: bt, 'fill-opacity': f2(bt === '#ffffff' ? 0.05 + wr() * 0.09 : 0.04 + wr() * 0.08) }, wash);
      }
      // Halftone shading: seeded dots concentrated toward the shadowed corner so the
      // pigment reads printed, not flat.
      const hd = rng(seed ^ 0x2bd1);
      const hx = 30 + hd() * 40, hy = 58 + hd() * 30;
      for (let di = 0; di < 34; di += 1) {
        const a = hd() * Math.PI * 2, dd = Math.pow(hd(), 1.6) * 26;
        svgEl('circle', { cx: f2(hx + Math.cos(a) * dd), cy: f2(hy + Math.sin(a) * dd * 0.72), r: f2(0.55 + hd() * 0.85), fill: plan.brand.ink, 'fill-opacity': f2(0.05 + hd() * 0.1) }, wash);
      }
      if (hero && plan.book === 'paperbook') {
        // Engraving hatching on the hero subject: seeded parallel strokes inside the
        // silhouette — the mark reads etched into the plate, not flat-filled.
        const hr = rng(seed ^ 0x3a11);
        const hang = 0.5 + hr() * 0.35;
        const hg = svgEl('g', { 'clip-path': `url(#pac_${uid})` }, wash);
        for (let hy = -30; hy < 140; hy += 3.8) {
          svgEl('path', {
            d: `M-20 ${f2(hy)} L130 ${f2(hy - 150 * hang)}`,
            stroke: plan.brand.ink, 'stroke-width': f2(0.5 + hr() * 0.4),
            'stroke-opacity': f2(0.05 + hr() * 0.07), fill: 'none',
          }, hg);
        }
      }
      els.push(wash);
    }
    return { g, els };
  }
  // Nominal extent of an art composition in normalized space — the fit that
  // scales each illustration to fill its sticker rather than float inside it.
  function paperBounds(key) {
    let x0 = 100, y0 = 100, x1 = 0, y1 = 0;
    const box = (a, b, c, d) => { x0 = Math.min(x0, a); y0 = Math.min(y0, b); x1 = Math.max(x1, c); y1 = Math.max(y1, d); };
    for (const pc of PAPER_ART[key] || []) {
      const cx = pc.cx != null ? pc.cx : (pc.x != null ? pc.x + pc.w / 2 : 50);
      const cy = pc.cy != null ? pc.cy : (pc.y != null ? pc.y + pc.h / 2 : 50);
      switch (pc.s) {
        case 'blob': box(cx - (pc.rx || pc.r || 10), cy - (pc.ry || pc.r || 10), cx + (pc.rx || pc.r || 10), cy + (pc.ry || pc.r || 10)); break;
        case 'rect': box(pc.x, pc.y, pc.x + pc.w, pc.y + pc.h); break;
        case 'path': {
          const k = pc.k || 1, xs = pc.pts.map((p) => (pc.ox || 0) + p[0] * k), ys = pc.pts.map((p) => (pc.oy || 0) + p[1] * k);
          box(Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys));
          break;
        }
        case 'petal': { const m = Math.max(pc.rx || 8, pc.ry || 14); box(cx - m, cy - m, cx + m, cy + m); break; }
        case 'crescent': case 'halfdisc': box(cx - (pc.r || 26), cy - (pc.r || 26), cx + (pc.r || 26), cy + (pc.r || 26)); break;
        case 'rays': box(cx - pc.r1, cy - pc.r1, cx + pc.r1, cy + pc.r1); break;
        case 'ring': case 'arc': { const m = (pc.r || 20) + (pc.t || 5); box(cx - m, cy - m, cx + m, cy + m); break; }
        default: break;
      }
    }
    return { x: x0, y: y0, w: Math.max(1, x1 - x0), h: Math.max(1, y1 - y0), cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
  }
  // Animated mount: art draws on piece by piece inside `box` (stage coords), lifted
  // by a soft shadow. Falls back to the registry icon, then the typeset word.
  function paintPaperArt(ent, node, host, box, plan, opts) {
    const key = paperArtKey(ent.concept);
    if (key) {
      const isHero = box.h >= (plan.canvas.h || 720) * 0.20;
      const art = paperArtGroup(key, seedHash(`${ent.id}:${key}`), plan, `${ent.id}_${++iconInstance}`, isHero);
      if (art) {
        const bb = paperBounds(key);
        const s = Math.min((box.w * 0.9) / bb.w, (box.h * 0.9) / bb.h);
        const wrap = svgEl('g', { transform: `translate(${f2(box.x + box.w / 2)} ${f2(box.y + box.h / 2)}) scale(${f2(s)}) translate(${f2(-bb.cx)} ${f2(-bb.cy)})` }, host);
        wrap.appendChild(art.g);
        node.extra.iconBox = box;
        node.extra.shadow = { el: wrap, oy: box.h * 0.045, blur: box.h * 0.09, alpha: 0.2 };
        host.setAttribute('data-icon-host', ent.id);
        const n = art.els.length;
        art.els.forEach((e, i) => node.outline.push({ path: e, len: 0, set(v) { e.style.opacity = clamp(v * n - i, 0, 1).toFixed(4); } }));
        return true;
      }
    }
    if (ent.asset) { loadIconInto(ent, node, host, box, opts); return true; }
    return false;
  }
  // Static mount (backdrop marks, the motif stamp): same art, no draw-on program.
  function paperArtSvg(key, seed, plan, uid) {
    const art = paperArtGroup(key, seed, plan, uid);
    if (!art) return null;
    const s = svgEl('svg', { viewBox: '0 0 100 100' }, null);
    const bb = paperBounds(key);
    const k = Math.min(88 / bb.w, 88 / bb.h);
    const fit = svgEl('g', { transform: `translate(50 50) scale(${f2(k)}) translate(${f2(-bb.cx)} ${f2(-bb.cy)})` }, s);
    fit.appendChild(art.g);
    return s;
  }

  // ---------------------------------------------------------------------------
  // Paper performer — the film's character is cut from the same paper as every
  // other mark: no clip-art bodies, no icon men. Built in a 100×140 space as
  // stacked die-cut pieces: shadowed paper silhouette behind, painted pieces on
  // top. Slots ('body' | 'head' | 'face') are addressable so performer states
  // cut poses and faces the way a puppeteer swaps a head.
  // ---------------------------------------------------------------------------
  const FIGURE_FACE = {
    // face keyword family -> {brows, eyes, mouth}
    smile: { brows: 'up', eyes: 'dot', mouth: 'smile' },
    calm: { brows: 'none', eyes: 'dot', mouth: 'calm' },
    surprised: { brows: 'up', eyes: 'open', mouth: 'o' },
    sleepy: { brows: 'none', eyes: 'closed', mouth: 'calm' },
    determined: { brows: 'down', eyes: 'dot', mouth: 'flat' },
    concerned: { brows: 'down', eyes: 'dot', mouth: 'sad' },
  };
  function paperFaceKind(id) {
    const s = String(id || '').toLowerCase();
    if (/smile|happy|cheers|laugh|grin|loving|excited/.test(s)) return 'smile';
    if (/surprised|shock|awe|wonder/.test(s)) return 'surprised';
    if (/sleep|tired|meditate|calm-down|rested/.test(s)) return 'sleepy';
    if (/angry|grumpy|furious|rage|determined|serious/.test(s)) return 'determined';
    if (/sad|concern|worr|suspicious|fear|doubt|confus/.test(s)) return 'concerned';
    return 'calm';
  }
  function paperHairKind(id, seed) {
    const s = String(id || '').toLowerCase();
    if (/beanie|hat|cap|fedora|turban|hijab/.test(s)) return 'cap';
    if (/bun|topknot/.test(s)) return 'bun';
    if (/afro|curly|curl/.test(s)) return 'curls';
    if (/braid|pony|long|straight/.test(s)) return 'bob';
    if (/bald|shaved|none|gray/.test(s)) return seed % 3 === 0 ? 'bald' : 'crop';
    if (/hood/.test(s)) return 'hood';
    return ['mop', 'crop', 'bob', 'curls'][seed % 4];
  }
  function paperArmPose(poseId, posture) {
    const s = String(poseId || '').toLowerCase();
    if (posture === 'sitting') return 'seated';
    if (/hold|carry|bucket|bag|read|phone|book|selfie|present/.test(s)) return 'carry';
    if (/wave|point|reach|teach|explain|dance|walk/.test(s)) return 'reach';
    return 'rest';
  }

  // One figure: {slots: {body:[els], head:[els], face:[els]}, edge: els} in 100×140 space.
  // Silhouette pieces double as the die-cut edge in paper white behind everything.
  function paperFigureSlots(fig, seed, plan, uid) {
    const ink = plan.brand.ink;
    const skin = fig.palette && fig.palette['#d08b5b'] || '#e8b98e';
    const garment = (plan.brand.accent && plan.brand.accent !== '#000000') ? plan.brand.accent : paintTone('warm', plan);
    const garmentDark = mixColor(garment, ink, 0.25);
    const hairTone = [ink, paintTone('soil', plan), paintTone('wood', plan), paintTone('grey', plan), paintTone('sun', plan)][seed % 5];
    const posture = fig.posture || 'standing';
    const sitting = posture === 'sitting';
    // A figure holding a prop carries it in that hand; the other arm rests. The hand is a
    // screen side — mirrored figures flip the drawing, so the carry arm XORs with the mirror.
    const arms = fig.prop && fig.prop.hand
      ? `carry-${(fig.prop.hand === 'left') !== Boolean(fig.mirror) ? 'left' : 'right'}`
      : paperArmPose(fig.pose && fig.pose.id, posture);
    const hair = paperHairKind(fig.parts && fig.parts.find((p) => p.slot === 'head') && fig.parts.find((p) => p.slot === 'head').part_id, seed);
    const faceKind = paperFaceKind(fig.emotion && fig.emotion.face);
    const pieces = { body: [], head: [], face: [] };
    const edge = [];
    const put = (slot, e) => pieces[slot].push(e);
    const edgePut = (e) => { e.setAttribute('fill', '#fdfcf8'); e.setAttribute('stroke', 'none'); edge.push(e); };

    // Legs + feet (or a seated lap).
    if (sitting) {
      for (const sx of [-9, 9]) {
        const leg = svgEl('ellipse', { cx: 50 + sx, cy: 116, rx: 8.5, ry: 5.6, fill: garmentDark });
        put('body', leg);
      }
      edgePut(svgEl('ellipse', { cx: 50, cy: 113, rx: 21, ry: 10 }));
    } else {
      for (const sx of [-7.5, 7.5]) {
        put('body', svgEl('rect', { x: 50 + sx - 4.4, y: 96, width: 8.8, height: 30, rx: 4.2, fill: garmentDark }));
        put('body', svgEl('ellipse', { cx: 50 + sx, cy: 127.5, rx: 7.6, ry: 4.6, fill: ink }));
        edgePut(svgEl('rect', { x: 50 + sx - 5.4, y: 95, width: 10.8, height: 34, rx: 5.4 }));
      }
    }
    // Torso: a rounded paper tunic, slightly wider at the hips.
    const torso = svgEl('path', { d: 'M32 62 Q50 55 68 62 L71 100 Q50 107 29 100 Z', fill: garment });
    put('body', torso);
    edgePut(svgEl('path', { d: 'M30 60 Q50 52 70 60 L73.5 102 Q50 110 26.5 102 Z' }));
    // Arms by posture: rested at the sides, reached forward (prop hand), or one raised.
    const armAt = (sx, kind) => {
      if (kind === 'rest') return svgEl('rect', { x: 50 + sx * 24 - 4, y: 63, width: 8, height: 26, rx: 4, fill: garment, transform: `rotate(${sx * 8} ${50 + sx * 24} 63)` });
      if (kind === 'seated') return svgEl('rect', { x: 50 + sx * 20 - 4, y: 74, width: 8, height: 24, rx: 4, fill: garment, transform: `rotate(${sx * 46} ${50 + sx * 20} 74)` });
      if (kind === 'reach' && sx < 0) return svgEl('rect', { x: 0, y: 0, width: 8, height: 28, rx: 4, fill: garment, transform: `translate(${50 + sx * 24} 60) rotate(${sx * 58})` });
      if (kind === 'carry') return svgEl('rect', { x: 0, y: 0, width: 8, height: 24, rx: 4, fill: garment, transform: `translate(${50 + sx * 24} 64) rotate(${sx * 30})` });
      return svgEl('rect', { x: 50 + sx * 24 - 4, y: 63, width: 8, height: 26, rx: 4, fill: garment, transform: `rotate(${sx * 8} ${50 + sx * 24} 63)` });
    };
    const armLeft = arms === 'reach' ? 'reach' : arms === 'carry-left' ? 'carry' : arms === 'carry-right' ? 'rest' : arms;
    const armRight = arms === 'reach' || arms === 'carry-left' ? 'rest' : arms === 'carry-right' ? 'carry' : arms;
    put('body', armAt(-1, armLeft));
    put('body', armAt(1, armRight));
    edgePut(svgEl('rect', { x: 21, y: 60, width: 10, height: 29, rx: 5, transform: 'rotate(-8 26 60)' }));
    edgePut(svgEl('rect', { x: 69, y: 60, width: 10, height: 29, rx: 5, transform: 'rotate(8 74 60)' }));
    // Hands on the arm ends (skin dots).
    for (const sx of [-1, 1]) {
      const hx = arms === 'reach' && sx < 0 ? 50 + sx * 34 : 50 + sx * 24;
      const hy = arms === 'reach' && sx < 0 ? 88 : 92;
      put('body', svgEl('circle', { cx: hx, cy: hy, r: 4.4, fill: skin }));
    }
    // Head: skin blob + neck.
    put('body', svgEl('rect', { x: 45.5, y: 50, width: 9, height: 12, rx: 3.4, fill: skin }));
    put('head', svgEl('ellipse', { cx: 50, cy: 32, rx: 17.5, ry: 19, fill: skin }));
    edgePut(svgEl('ellipse', { cx: 50, cy: 31.5, rx: 19.5, ry: 21 }));
    // Ears as tiny skin dots; hair sits over the skull.
    put('head', svgEl('circle', { cx: 32.6, cy: 33, r: 2.6, fill: skin }));
    put('head', svgEl('circle', { cx: 67.4, cy: 33, r: 2.6, fill: skin }));
    if (hair === 'mop') put('head', svgEl('path', { d: 'M33 30 Q31 12 50 11 Q69 12 67 30 Q63 20 57 22 Q61 15 50 15 Q39 15 43 22 Q37 20 33 30 Z', fill: hairTone }));
    else if (hair === 'crop') put('head', svgEl('path', { d: 'M34 27 Q36 12 50 12 Q64 12 66 27 Q60 18 50 18 Q40 18 34 27 Z', fill: hairTone }));
    else if (hair === 'bob') { put('head', svgEl('path', { d: 'M31 32 Q29 10 50 10 Q71 10 69 32 L66 44 Q68 26 60 22 Q62 14 50 14 Q38 14 40 22 Q32 26 34 44 Z', fill: hairTone })); }
    else if (hair === 'curls') { for (let i = 0; i < 5; i += 1) put('head', svgEl('circle', { cx: 36 + i * 7, cy: 16 + Math.abs(i - 2) * 1.5, r: 5.6, fill: hairTone })); }
    else if (hair === 'bun') { put('head', svgEl('path', { d: 'M34 28 Q35 12 50 12 Q65 12 66 28 Q60 19 50 19 Q40 19 34 28 Z', fill: hairTone })); put('head', svgEl('circle', { cx: 50, cy: 9, r: 5.5, fill: hairTone })); }
    else if (hair === 'cap') { put('head', svgEl('path', { d: 'M32 28 Q34 10 50 10 Q66 10 68 28 Z', fill: garmentDark })); put('head', svgEl('rect', { x: 30, y: 26, width: 40, height: 4.4, rx: 2.2, fill: garmentDark })); }
    else if (hair === 'hood') put('head', svgEl('path', { d: 'M29 34 Q27 8 50 8 Q73 8 71 34 L66 30 Q70 16 50 15 Q30 16 34 30 Z', fill: garmentDark }));
    // Face: ink strokes — dots or closed arcs, a mouth by family, brows when shown.
    const fk = FIGURE_FACE[faceKind] || FIGURE_FACE.calm;
    const eyeY = 32;
    if (fk.eyes === 'closed') {
      for (const sx of [-6.4, 6.4]) put('face', svgEl('path', { d: `M${50 + sx - 2.4} ${eyeY} q2.4 2.2 4.8 0`, stroke: ink, 'stroke-width': 1.6, fill: 'none', 'stroke-linecap': 'round' }));
    } else {
      for (const sx of [-6.4, 6.4]) put('face', svgEl('circle', { cx: 50 + sx, cy: eyeY, r: fk.eyes === 'open' ? 2.4 : 1.9, fill: ink }));
    }
    const mouth = { smile: 'M45 41 q5 4.5 10 0', calm: 'M46 41.5 q4 1.6 8 0', flat: 'M46 42 h8', sad: 'M45 43.5 q5 -4 10 0', o: null }[fk.mouth];
    if (fk.mouth === 'o') put('face', svgEl('ellipse', { cx: 50, cy: 43, rx: 3.4, ry: 4, fill: 'none', stroke: ink, 'stroke-width': 1.5 }));
    else put('face', svgEl('path', { d: mouth, stroke: ink, 'stroke-width': 1.6, fill: 'none', 'stroke-linecap': 'round' }));
    if (fk.brows !== 'none') for (const sx of [-6.4, 6.4]) {
      put('face', svgEl('path', { d: `M${50 + sx - 2.6} ${fk.brows === 'up' ? 25.4 : 26.4} q2.6 ${fk.brows === 'up' ? -1.6 : 1.4} 5.2 0`, stroke: ink, 'stroke-width': 1.3, fill: 'none', 'stroke-linecap': 'round' }));
    }
    // Cheek blush dots, faint — the puppet reads warm without them being loud.
    for (const sx of [-10.4, 10.4]) put('face', svgEl('circle', { cx: 50 + sx, cy: 38.5, r: 2.1, fill: paintTone('petal', plan), opacity: 0.4 }));

    const wrap = {};
    for (const [slot, els] of Object.entries(pieces)) {
      const g = svgEl('g', { 'data-slot': slot }, null);
      for (const e of els) g.appendChild(e);
      wrap[slot] = g;
    }
    const edgeG = svgEl('g', { opacity: 1 }, null);
    for (const e of edge) edgeG.appendChild(e);
    // The die-cut edge is the silhouette grown ~4% about the body centre.
    edgeG.setAttribute('transform', 'translate(50 74) scale(1.045) translate(-50 -74)');
    return { slots: wrap, edge: edgeG, sitting, arms };
  }

  // A state's swap is re-rendered as a paper slot: face ids pick expressions,
  // head ids pick hair, pose ids pick arm postures — same contract, new material.
  function paperSlotInner(slot, partId, fig, seed, plan) {
    if (slot === 'face') {
      const kind = paperFaceKind(partId);
      const fake = { ...fig, emotion: { ...fig.emotion, face: partId } };
      const s = paperFigureSlots(fake, seed, plan, 'sw');
      return s.slots.face.innerHTML;
    }
    if (slot === 'head') {
      const fake = { ...fig, parts: fig.parts.map((p) => p.slot === 'head' ? { ...p, part_id: partId } : p) };
      const s = paperFigureSlots(fake, seed, plan, 'sw');
      return s.slots.head.innerHTML;
    }
    if (slot === 'body') {
      const fake = { ...fig, pose: { ...fig.pose, id: partId } };
      const s = paperFigureSlots(fake, seed, plan, 'sw');
      return s.slots.body.innerHTML;
    }
    return '';
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

  // Cloned DOM (page stills, leaf faces) duplicates every def id — url(#id) then resolves to the
  // first match in document order, often an element hidden inside a display:none tree, and the
  // filtered node vanishes. Re-scoping rewrites ids and every url(#)/href reference in the clone
  // so each copy binds only to its own defs.
  function rescopeCloneIds(root, scope) {
    const tag = `em2c${scope}`;
    const map = new Map();
    root.querySelectorAll('[id]').forEach((n) => { const nid = `${tag}__${n.id}`; map.set(n.id, nid); n.id = nid; });
    if (!map.size) return;
    const ATTRS = ['filter', 'clip-path', 'mask', 'fill', 'stroke', 'href', 'xlink:href', 'marker-start', 'marker-mid', 'marker-end'];
    root.querySelectorAll('*').forEach((n) => {
      ATTRS.forEach((a) => {
        const v = n.getAttribute && n.getAttribute(a);
        if (!v || v.indexOf('#') < 0) return;
        let nv = v;
        map.forEach((nid, oid) => { nv = nv.split(`#${oid}`).join(`#${nid}`); });
        if (nv !== v) n.setAttribute(a, nv);
      });
      ['filter', 'clipPath', 'maskImage', 'WebkitMaskImage'].forEach((p) => {
        const v = n.style && n.style[p];
        if (!v || v.indexOf('#') < 0) return;
        let nv = v;
        map.forEach((nid, oid) => { nv = nv.split(`#${oid}`).join(`#${nid}`); });
        n.style[p] = nv;
      });
    });
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

  // A photograph set into a housing's well: the concept ladder's evidence rung. The well is the
  // same rounded geometry the housing itself uses (a circle for a disc), the picture fills it
  // edge to edge and a hairline rim seats it, so it reads as an inset card, not a pasted bitmap.
  function loadPhotoInto(ent, node, host, box, radius, opts) {
    node.extra.iconBox = box;
    host.setAttribute('data-icon-host', ent.id);
    host.setAttribute('data-photo', ent.photo.source);
    const cid = `pw_${ent.id}_${++iconInstance}`;
    const round = radius >= Math.min(box.w, box.h) / 2;
    const inner = svgEl('g', { 'clip-path': `url(#${cid})` }, host);
    const img = svgEl('image', { x: f2(box.x), y: f2(box.y), width: f2(box.w), height: f2(box.h), preserveAspectRatio: 'xMidYMid slice' }, inner);
    img.setAttribute('href', opts.assetUrl(ent.photo.path));
    const clip = svgEl('clipPath', { id: cid }, host);
    if (round) svgEl('circle', { cx: f2(box.x + box.w / 2), cy: f2(box.y + box.h / 2), r: f2(Math.min(box.w, box.h) / 2) }, clip);
    else svgEl('path', { d: roundRectPath(box, radius) + 'Z' }, clip);
    const rim = round
      ? svgEl('circle', { cx: f2(box.x + box.w / 2), cy: f2(box.y + box.h / 2), r: f2(Math.min(box.w, box.h) / 2), fill: 'none' }, host)
      : svgEl('path', { d: roundRectPath(box, radius) + 'Z', fill: 'none' }, host);
    rim.setAttribute('stroke', host.style.color || '#000');
    rim.setAttribute('stroke-width', f2(Math.max(1, box.w * 0.012)));
    rim.setAttribute('stroke-opacity', '0.22');
    node.outline.push({ path: inner, len: 0, set(v) { const o = clamp(v, 0, 1).toFixed(4); inner.style.opacity = o; rim.style.opacity = o; } });
    node.ready = new Promise((resolve) => {
      img.addEventListener('load', () => resolve(), { once: true });
      img.addEventListener('error', () => resolve(), { once: true });
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
        const body = chassisBody(node, g);
        if (plan.book !== 'paperbook') {
          // Die-cut sticker: the mark rides on its own wobbly paper edge with a soft shadow —
          // the collage register, not a floating icon.
          const c = centre(b), seed = seedHash(String(ent.id));
          const blob = svgEl('path', {
            d: cutBlobPath(c.x, c.y, Math.max(b.w, sw * 8) * 0.58, Math.max(b.h, sw * 8) * 0.58, seed),
            fill: mixColor(plan.brand.paper, '#ffffff', 0.62), 'fill-opacity': 0.96,
          }, body);
          node.extra.shadow = { el: blob, oy: b.h * 0.05, blur: b.h * 0.11, alpha: 0.24 };
        }
        const host = svgEl('g', {}, g);
        host.style.color = ink;
        node.inkEls.push(host);
        node.extra.iconHost = host;
        if (!paintPaperArt(ent, node, host, { x: b.x + b.w * 0.08, y: b.y + b.h * 0.08, w: b.w * 0.84, h: b.h * 0.84 }, plan, opts)) {
          wordMark(node, host, b, String(params.word || ent.concept || ent.id), 'name', ink, plan);
        }
        node.strike = strikeFor(b);
        break;
      }
      case 'TILE': {
        // Die-cut paper card: an irregular hand-cut edge around the mark — the evidence-board
        // atom, not an app icon. No gloss, a whisper of ink rim, and a few degrees off true.
        const dark = params.tone === 'dark';
        const seed = seedHash(String(ent.id));
        const m = sw * 1.3, r = Math.min(b.w, b.h) * 0.06;
        const cardB = { x: b.x + m, y: b.y + m, w: b.w - m * 2, h: b.h - m * 2 };
        const shape = cutRectPath(cardB, seed, Math.min(b.w, b.h) * 0.05);
        const body = chassisBody(node, g);
        if (plan.book !== 'paperbook') {
          // The fibrous fringe: the rip's white core peeks a hair past the face.
          svgEl('path', { d: tornFringePath(cardB, seed, Math.min(b.w, b.h) * 0.05), fill: mixColor(plan.brand.paper, '#ffffff', 0.85), 'fill-opacity': dark ? 0.5 : 0.9 }, body);
          const base = svgEl('path', { d: shape, fill: dark ? housing.dark : mixColor(plan.brand.paper, '#ffffff', 0.55) }, body);
          node.extra.shadow = { el: base, oy: b.h * 0.07, blur: b.h * 0.13, alpha: 0.28 };
          svgEl('path', { d: shape, fill: 'none', stroke: ink, 'stroke-width': f2(sw * 0.4), 'stroke-opacity': dark ? 0.14 : 0.2 }, body);
        }
        node.inkEls.push(svgEl('path', { d: shape, fill: accent, 'fill-opacity': 0 }, g));
        const word = params.word ? String(params.word) : '';
        const fg = dark ? paper : ink;
        // The name sits above the accent fill so an inked tile keeps it, in the paper colour.
        const wordHost = svgEl('g', {}, g);
        node.extra.wordHost = wordHost;
        node.inkEls.push(wordHost);
        if (plan.book === 'paperbook' && ent.photo && /^bank:/.test(ent.photo.source || '')) {
          // A page in a picture book: the bank painting IS the plate — no card
          // housing, no tape, no label pasted on the art. The torn mask cuts it
          // like a tipped-in plate, an ink rim seats it in the stock.
          const plateSeed = seedHash(`${ent.id}-plate`);
          const tear = cutRectPath(b, plateSeed, Math.min(b.w, b.h) * 0.035) + 'Z';
          const cid = `bp_${ent.id}_${++iconInstance}`;
          const clip = svgEl('clipPath', { id: cid }, g);
          svgEl('path', { d: tear }, clip);
          const inner = svgEl('g', { 'clip-path': `url(#${cid})` }, g);
          const img = svgEl('image', { x: f2(b.x), y: f2(b.y), width: f2(b.w), height: f2(b.h), preserveAspectRatio: 'xMidYMid slice' }, inner);
          img.setAttribute('href', opts.assetUrl(ent.photo.path));
          img.setAttribute('data-photo', ent.photo.source);
          svgEl('path', { d: tear, fill: 'none', stroke: ink, 'stroke-width': f2(sw * 0.5), 'stroke-opacity': 0.3 }, g);
          node.extra.iconBox = { ...b };
          node.extra.iconHost = inner;
          node.outline.push({ path: inner, len: 0, set(v) { inner.style.opacity = clamp(v, 0, 1).toFixed(4); } });
          node.ready = new Promise((resolve) => {
            img.addEventListener('load', () => resolve(), { once: true });
            img.addEventListener('error', () => resolve(), { once: true });
          });
        } else if (ent.photo) {
          const host = svgEl('g', {}, g);
          host.style.color = fg;
          node.extra.iconHost = host;
          const pad = b.w * 0.11;
          if (word) {
            // Evidence: the photograph takes the upper body as an inset card, the concept's own name beneath.
            const ih = b.h * 0.56;
            loadPhotoInto(ent, node, host, { x: b.x + pad, y: b.y + pad, w: b.w - pad * 2, h: ih }, r * 0.55, opts);
            wordMark(node, wordHost, { x: b.x + pad * 1.2, y: b.y + pad + ih + b.h * 0.03, w: b.w - pad * 2.4, h: b.h - pad - ih - b.h * 0.03 - pad * 0.9 }, word, params.word_kind || 'name', fg, plan);
          } else {
            loadPhotoInto(ent, node, host, { x: b.x + pad, y: b.y + pad, w: b.w - pad * 2, h: b.h - pad * 2 }, r * 0.6, opts);
          }
        } else if (paperArtKey(ent.concept)) {
          // Painted collage art in place of the icon: the concept is illustrated,
          // not indexed. The word still rides beneath when the housing carries one.
          const host = svgEl('g', {}, g);
          node.extra.iconHost = host;
          const pad = b.w * 0.13;
          if (word) {
            const ih = b.h * 0.56;
            paintPaperArt(ent, node, host, { x: b.x + (b.w - ih) / 2, y: b.y + pad * 0.7, w: ih, h: ih }, plan, opts);
            wordMark(node, wordHost, { x: b.x + pad * 0.6, y: b.y + pad * 0.7 + ih + b.h * 0.02, w: b.w - pad * 1.2, h: b.h - pad * 0.7 - ih - b.h * 0.02 - pad * 0.7 }, word, params.word_kind || 'name', fg, plan);
          } else {
            paintPaperArt(ent, node, host, { x: b.x + pad, y: b.y + pad, w: b.w - pad * 2, h: b.h - pad * 2 }, plan, opts);
          }
        } else if (ent.asset && !word) {
          const host = svgEl('g', {}, g);
          host.style.color = fg;
          node.inkEls.push(host);
          node.extra.iconHost = host;
          const pad = b.w * 0.17;
          loadIconInto(ent, node, host, { x: b.x + pad, y: b.y + pad, w: b.w - pad * 2, h: b.h - pad * 2 }, opts);
        } else if (word) {
          const pad = b.w * 0.14;
          wordMark(node, wordHost, { x: b.x + pad, y: b.y + pad, w: b.w - pad * 2, h: b.h - pad * 2 }, word, params.word_kind || 'name', fg, plan);
        }
        // Hand-placed: every card sits a few degrees off true.
        const trr = rng(seed ^ 0x5bd1e995);
        node.extra.rotateDeg = f2((trr() - 0.5) * 5.6);
        if (ent.photo) {
          // Washi tape across the top of an evidence photo — the cork-board gesture.
          const tw = b.w * 0.34, th = b.h * 0.085, tx = b.x + b.w * 0.5, ty = b.y + b.h * 0.02;
          const td = `M${f2(-tw / 2)} ${f2(th * 0.28)}L${f2(tw / 2)} 0L${f2(tw / 2)} ${f2(th * 0.82)}L${f2(-tw / 2)} ${f2(th)}Z`;
          svgEl('path', { d: td, fill: accent, 'fill-opacity': 0.38, transform: `translate(${f2(tx)} ${f2(ty)}) rotate(${f2(-5 + (trr() - 0.5) * 8)})` }, g);
        }
        node.strike = strikeFor(b);
        break;
      }
      case 'BADGE': {
        // Die-cut disc: a wobbly paper circle — the sticker version of the old glossy badge.
        const dark = params.tone === 'dark';
        const c = centre(b), R = Math.min(b.w, b.h) / 2 - sw / 2;
        const body = chassisBody(node, g);
        const discD = cutBlobPath(c.x, c.y, R, R, seedHash(String(ent.id)));
        const disc = svgEl('path', { d: discD }, body);
        disc.setAttribute('fill', dark ? housing.dark : mixColor(plan.brand.paper, '#ffffff', 0.55));
        disc.setAttribute('stroke', ink);
        disc.setAttribute('stroke-width', f2(sw * 0.4));
        disc.setAttribute('stroke-opacity', '0.2');
        node.extra.shadow = { el: disc, oy: R * 0.16, blur: R * 0.3, alpha: 0.26 };
        node.inkEls.push(svgEl('path', { d: discD, fill: accent, 'fill-opacity': 0 }, g));
        if (ent.photo) {
          // A disc is too small for a picture and a name: the photograph alone fills the well.
          const host = svgEl('g', {}, g);
          host.style.color = dark ? paper : ink;
          node.extra.iconHost = host;
          const pad = R * 0.14;
          loadPhotoInto(ent, node, host, { x: c.x - R + pad, y: c.y - R + pad, w: 2 * (R - pad), h: 2 * (R - pad) }, R, opts);
        } else if (paperArtKey(ent.concept)) {
          const host = svgEl('g', {}, g);
          node.extra.iconHost = host;
          const pad = R * 0.5;
          paintPaperArt(ent, node, host, { x: c.x - R + pad, y: c.y - R + pad, w: 2 * (R - pad), h: 2 * (R - pad) }, plan, opts);
        } else if (ent.asset && !params.word) {
          const host = svgEl('g', {}, g);
          host.style.color = dark ? paper : ink;
          node.inkEls.push(host);
          node.extra.iconHost = host;
          const pad = R * 0.48;
          loadIconInto(ent, node, host, { x: c.x - R + pad, y: c.y - R + pad, w: 2 * (R - pad), h: 2 * (R - pad) }, opts);
        } else if (params.word) {
          // The disc's square inscribed in the circle carries the word or its monogram, above the accent fill.
          const wordHost = svgEl('g', {}, g);
          node.extra.wordHost = wordHost;
          node.inkEls.push(wordHost);
          const side = R * 1.28;
          wordMark(node, wordHost, { x: c.x - side / 2, y: c.y - side / 2, w: side, h: side }, String(params.word), params.word_kind || 'name', dark ? paper : ink, plan);
        }
        node.strike = strikeFor(b);
        break;
      }
      case 'COUNTER': {
        // Stat card: a big tabular figure (prefix/suffix aware) over a small caption, on a light or dark body.
        const dark = params.tone === 'dark';
        const r = Math.min(b.w, b.h) * 0.18;
        const body = chassisBody(node, g);
        const statB = { x: b.x + sw / 2, y: b.y + sw / 2, w: b.w - sw, h: b.h - sw };
        const statSeed = seedHash(String(ent.id));
        svgEl('path', { d: tornFringePath(statB, statSeed, Math.min(b.w, b.h) * 0.04), fill: mixColor(plan.brand.paper, '#ffffff', 0.85), 'fill-opacity': dark ? 0.5 : 0.9 }, body);
        const card = svgEl('path', { d: cutRectPath(statB, statSeed, Math.min(b.w, b.h) * 0.04) }, body);
        card.setAttribute('fill', dark ? housing.dark : mixColor(plan.brand.paper, '#ffffff', 0.5));
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
        if (ent.photo) {
          const host = svgEl('g', {}, g);
          host.style.color = ink;
          node.extra.iconHost = host;
          loadPhotoInto(ent, node, host, { x: px0, y: py0, w: peg, h: peg }, peg * 0.26, opts);
        } else if (ent.asset) {
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
      if (!PAPERBOOK(plan) && (plan.motion || DEFAULT_MOTION).entrance === 'pop') {
        // Collage register: the pulse is a soft accent bloom behind the body, never a drawn ring.
        // Under the paperbook a blurred halo is out of register — the pulse draws as a ring instead.
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
        if (e === gl.extra.wordHost) {
          const onDark = (ent.params && ent.params.tone === 'dark') || (inkLevel > 0.5 && (inkP.accent || swap.accent));
          for (const t of e.querySelectorAll('text')) t.setAttribute('fill', onDark ? paper : ink);
        } else if (e === gl.extra.iconHost) {
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
    const bg = buildBackground(beat, plan, root, opts.assetUrl);
    const media = beat.media ? buildMedia(beat.media, plan, root, opts.assetUrl) : null;
    if (media) media.blur = motionBlurFilter(fx.defs, `${fx.scope}-mb-media`);
    const figure = beat.figure ? buildFigure(beat.figure, plan, root, opts, beat) : null;
    const data = beat.data ? buildData(beat.data, plan, root) : null;
    const illustration = beat.illustration ? buildIllustration(beat.illustration, plan, root, { ...opts, fx }) : null;
    // All typography lives in one layer so book mode can demote the whole lockup at once.
    const textHost = el('div', { position: 'absolute', inset: '0', zIndex: '40', pointerEvents: 'none' }, root);
    // Picture-book captioning: the page's art is the hero — the spread prints its own words,
    // so no text blocks are built for the plate at all (a display:none wrap still carries a
    // plate child that can paint over the illustration).
    const texts = plan.book === 'paperbook'
      ? []
      : beat.typography.blocks.map((b, i) => Object.assign(buildTextBlock(b, plan, textHost), { blur: motionBlurFilter(fx.defs, `${fx.scope}-mb-text-${i}`) }));
    if (plan.book && plan.book !== 'paperbook' && texts.length) {
      const pr = bookPageRect(plan);
      const caps = texts.filter((t) => { const hero = t.block.role === 'hero'; if (hero) t.wrap.style.display = 'none'; return !hero; });
      const u = caps.reduce((a, t) => ({ x0: Math.min(a.x0, t.bb.x), y0: Math.min(a.y0, t.bb.y), x1: Math.max(a.x1, t.bb.x + t.bb.w), y1: Math.max(a.y1, t.bb.y + t.bb.h) }), { x0: 1e9, y0: 1e9, x1: -1e9, y1: -1e9 });
      if (caps.length) {
        const s = Math.min(1, (pr.w * 0.7) / (u.x1 - u.x0), (pr.h * 0.055) / (u.y1 - u.y0));
        textHost.style.transformOrigin = '0 0';
        textHost.style.transform = `translate(${f2(pr.x + pr.w / 2 - s * (u.x0 + u.x1) / 2)}px,${f2(pr.y + pr.h * 0.875 - s * u.y1)}px) scale(${f2(s)})`;
      }
    }
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
    return { beat, root: outer, cam: root, camBlur, bg, media, figure, data, illustration, texts, ctx, ready, index: beatIndex, _hasVideo: Boolean(media && media.media && media.media.kind === 'VIDEO') };
  }

  // Film-level camera. Every cut is a matched move the compiler chose from the beats on either
  // side (transition.camera): the outgoing picture makes the move and the incoming picture
  // arrives out of the same move, so the two halves read as one camera. `k` is the outgoing
  // beat's progress through its transition (0 outside it); `arrival` is set on the incoming beat
  // while it dresses underneath: the outgoing beat's camera and the window it arrives over.
  // Plans without camera metadata fall back to the profile's transition name.
  // A real page turn, geometry after MengTo/sketchbook: the outgoing scene becomes a leaf of
  // N nested strips whose tangent sweeps an arc — the sheet bends instead of pivoting like a
  // door. Each strip carries a front face (the scene, sliced) and a back face (the print
  // ghosted through the paper); |cos(theta)| per strip drives shade and specular, a shadow
  // band tracks the fold across the page below, and the leaf leaves the stage entirely.
  const PAGE_STRIPS = 20, PAGE_BETA = 0.6;
  // The page the animated paperbook lives inside: a deckled aged leaf inset on a lit desk.
  function bookPageRect(plan) {
    if (!plan.book) return null;
    const W = plan.canvas.w, H = plan.canvas.h;
    // Enough desk around the leaf for the binding, the page stack and the lamp pool to read
    // as an object — a page edge-to-edge stops looking like a book at all.
    const ix = Math.round(W * 0.078), iy = Math.round(H * 0.088);
    return { x: ix, y: iy, w: W - ix * 2, h: H - iy * 2 };
  }
  function buildPageLeaf(bn, plan) {
    const W = plan.canvas.w, H = plan.canvas.h;
    const dir = bn._leafDir > 0 ? 1 : -1;
    const hinge = plan.book ? (bookPageRect(plan) || { x: 0 }).x : (dir > 0 ? 0 : W);
    const sw = W / PAGE_STRIPS;
    const shade = `rgba(${((plan.atmosphere && plan.atmosphere.shadow_rgb) || [52, 38, 20]).join(',')},A)`;
    const leaf = el('div', {
      position: 'absolute', left: '0', top: '0', width: px(W), height: px(H), display: 'none',
      transformStyle: 'preserve-3d', transformOrigin: `${px(hinge)} 50%`,
      willChange: 'transform', pointerEvents: 'none',
    });
    // The shadow the lifting leaf throws onto the page beneath it.
    const shadow = el('div', {
      position: 'absolute', top: '0', bottom: '0', width: px(W * 0.24), left: '0', opacity: '0',
      background: `linear-gradient(90deg, transparent 0%, ${shade.replace('A', '0.5')} 50%, transparent 100%)`,
      filter: `blur(${px(W * 0.012)})`, pointerEvents: 'none', willChange: 'transform, opacity',
    });
    // Snapshot the settled picture once per leaf — a turning page is printed paper, not live ink.
    const snap = (() => {
      const s = bn.cam.cloneNode(true);
      s.style.transform = 'none'; s.style.opacity = '1'; s.style.visibility = 'visible'; s.style.filter = 'none';
      return s;
    })();
    const origin = dir > 0 ? '0% 50%' : '100% 50%';
    const side = dir > 0 ? 'left' : 'right';
    let host = leaf;
    const strips = [];
    for (let i = 0; i < PAGE_STRIPS; i++) {
      const st = el('div', { position: 'absolute', top: '0', bottom: '0', width: px(sw), transformStyle: 'preserve-3d', transformOrigin: origin }, host);
      st.style[side] = i === 0 ? '0' : '100%';
      if (i > 0) st.style.transform = `rotateY(calc(${dir > 0 ? '' : '-1 * '}var(--ptd)))`;
      const fi = dir > 0 ? i : PAGE_STRIPS - 1 - i;
      const front = el('div', { position: 'absolute', inset: '0', overflow: 'hidden', backfaceVisibility: 'hidden', webkitBackfaceVisibility: 'hidden', filter: 'blur(var(--pb,0px))' }, st);
      const fw = el('div', { position: 'absolute', left: px(-fi * sw), top: '0', width: px(W), height: px(H) }, front);
      const fc = snap.cloneNode(true); rescopeCloneIds(fc, `pf${bn.index}f${i}`); fw.appendChild(fc);
      const back = el('div', { position: 'absolute', inset: '0', overflow: 'hidden', backfaceVisibility: 'hidden', webkitBackfaceVisibility: 'hidden', transform: 'rotateY(180deg)', filter: 'blur(var(--pb,0px))' }, st);
      const bw = el('div', { position: 'absolute', left: px(-fi * sw), top: '0', width: px(W), height: px(H) }, back);
      const bc = snap.cloneNode(true); rescopeCloneIds(bc, `pf${bn.index}b${i}`); bw.appendChild(bc);
      // Print-through: ink ghosts faintly through the back of the sheet.
      el('div', { position: 'absolute', inset: '0', background: rgbaOf(plan.brand.paper, 0.62) }, back);
      const shF = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, front);
      const glF = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, front);
      const shB = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, back);
      const glB = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, back);
      strips.push({ st, shF, glF, shB, glB });
      host = st;
    }
    return { el: leaf, shadow, strips, dir, sw, hinge };
  }
  function drivePageLeaf(bn, kke, plan) {
    const leaf = bn._leaf;
    if (!leaf) return;
    const W = plan.canvas.w, D = 180 / Math.PI;
    const th = Math.PI * kke;
    const beta = PAGE_BETA * Math.sin(Math.PI * kke);
    const tt = th + beta, td = (2 * beta) / PAGE_STRIPS;
    leaf.el.style.display = '';
    leaf.el.style.transform = `rotateY(${f2(-leaf.dir * tt * D)}deg)`;
    leaf.el.style.setProperty('--ptd', `${f2(td * D)}deg`);
    leaf.el.style.setProperty('--pb', `${f2(Math.sin(Math.PI * kke) * 2.2)}px`);
    for (let i = 0; i < PAGE_STRIPS; i++) {
      const l1 = Math.abs(Math.cos(tt - i * td)), l2 = Math.abs(Math.cos(tt - (i + 1) * td));
      const a1 = (1 - l1) * 0.55, a2 = (1 - l2) * 0.55;
      const g1 = Math.max(0, l1 - 0.72) * 0.5, g2 = Math.max(0, l2 - 0.72) * 0.5;
      const { shF, glF, shB, glB } = leaf.strips[i];
      shF.style.background = `linear-gradient(90deg, rgba(52,38,20,${f2(a1)}), rgba(52,38,20,${f2(a2)}))`;
      shB.style.background = `linear-gradient(90deg, rgba(52,38,20,${f2(a2)}), rgba(52,38,20,${f2(a1)}))`;
      glF.style.background = `linear-gradient(105deg, transparent 32%, rgba(255,255,255,${f2(g1)}) 50%, transparent 68%)`;
      glB.style.background = `linear-gradient(105deg, transparent 32%, rgba(255,255,255,${f2(g2)}) 50%, transparent 68%)`;
    }
    // The fold's leading edge: where the sheet still touches the page below.
    const xEdge = leaf.hinge + (leaf.dir > 0 ? W * 0.5 * (1 + Math.cos(tt)) : W * 0.5 * (1 - Math.cos(tt)));
    leaf.shadow.style.transform = `translateX(${f2(xEdge - W * 0.12)}px)`;
    leaf.shadow.style.opacity = f2(Math.sin(Math.PI * kke) * 0.6);
  }
  function settlePageLeaf(bn) {
    if (!bn._leaf) return;
    bn._leaf.el.style.display = 'none';
    bn._leaf.shadow.style.opacity = '0';
  }

  // The book object the animated paperbook lives inside: the remaining pages peeking past the
  // fore-edge and tail, the binding gutter shadow at the spine, an engraved illustration frame
  // inside the page edge, and a soft aged vignette so the page reads lit rather than flat.
  function buildBookChrome(stage, plan, pr) {
    const W = plan.canvas.w, H = plan.canvas.h;
    const chrome = el('div', { position: 'absolute', inset: '0', zIndex: '30', pointerEvents: 'none' }, stage);
    const minDim = Math.min(W, H);
    const paperDark = mixColor(plan.brand.paper, '#c9b490', 0.55);
    const shadeRgb = (plan.atmosphere && plan.atmosphere.shadow_rgb) || [52, 38, 20];
    const sh = shadeRgb.join(',');
    const edgeW = Math.max(2, minDim * 0.004);
    for (const [ox, oy] of [[6, 3], [13, 7]]) {
      el('div', {
        position: 'absolute', left: px(pr.x + ox * 0.5), top: px(pr.y + pr.h + oy), width: px(pr.w - ox), height: px(edgeW),
        background: `linear-gradient(180deg, ${paperDark}, ${mixColor(paperDark, '#8f7a55', 0.5)})`,
        borderRadius: '0 0 45% 45%', opacity: '0.9',
      }, chrome);
      el('div', {
        position: 'absolute', left: px(pr.x + pr.w + ox), top: px(pr.y + oy * 0.5), width: px(edgeW), height: px(pr.h - oy),
        background: `linear-gradient(90deg, ${paperDark}, ${mixColor(paperDark, '#8f7a55', 0.5)})`,
        borderRadius: '0 45% 45% 0', opacity: '0.9',
      }, chrome);
    }
    // Spine gutter: the binding shadow inside the left edge and the crease line itself.
    el('div', {
      position: 'absolute', left: px(pr.x), top: px(pr.y), width: px(pr.w * 0.09), height: px(pr.h),
      background: `linear-gradient(90deg, rgba(${sh},0.42) 0%, rgba(${sh},0.14) 50%, transparent 100%)`,
    }, chrome);
    el('div', {
      position: 'absolute', left: px(pr.x + pr.w * 0.014), top: px(pr.y), width: px(Math.max(1.5, W * 0.0014)), height: px(pr.h),
      background: `linear-gradient(180deg, rgba(${sh},0.45), rgba(${sh},0.68) 50%, rgba(${sh},0.45))`,
    }, chrome);
    // Engraved illustration frame: two hairline rules a little inside the page edge.
    const fr = minDim * 0.016;
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' }, chrome);
    Object.assign(svg.style, { position: 'absolute', inset: '0', width: '100%', height: '100%' });
    const framePath = (rect, seed, amp, wpx, op) => svgEl('path', {
      d: polyPath(edgeRectPts(rect, 'cut', amp, rng(seedHash(seed)), 0)) + 'Z',
      fill: 'none', stroke: plan.brand.ink, 'stroke-width': f2(wpx), 'stroke-opacity': op,
    }, svg);
    framePath({ x: pr.x + fr, y: pr.y + fr, w: pr.w - fr * 2, h: pr.h - fr * 2 }, 'book-frame-outer', minDim * 0.0022, Math.max(1, minDim * 0.0028), '0.5');
    framePath({ x: pr.x + fr * 1.5, y: pr.y + fr * 1.5, w: pr.w - fr * 3, h: pr.h - fr * 3 }, 'book-frame-inner', minDim * 0.0016, Math.max(0.8, minDim * 0.0016), '0.35');
    // Printer's ornaments: the film's motif mark stamped into the frame's four inner corners,
    // turned to face the page's heart — the fleuron furniture of an old picture book.
    const fleu = paperArtSvg((plan.motif && plan.motif.concept) || 'leaf', 'book-fleuron', plan, 'bf');
    if (fleu) {
      const fs = minDim * 0.036, frs = pr.x + fr * 2.3, frt = pr.y + fr * 2.3, frx = pr.x + pr.w - fr * 2.3, fry = pr.y + pr.h - fr * 2.3;
      for (const [fx2, fy2, rot] of [[frs, frt, -45], [frx, frt, 45], [frx, fry, 135], [frs, fry, -135]]) {
        const holder = el('div', {
          position: 'absolute', left: px(fx2 - fs / 2), top: px(fy2 - fs / 2), width: px(fs), height: px(fs),
          transform: `rotate(${rot}deg)`, opacity: '0.6',
        }, chrome);
        holder.appendChild(fleu.cloneNode(true));
      }
    }
    // Aged light.
    el('div', {
      position: 'absolute', left: px(pr.x), top: px(pr.y), width: px(pr.w), height: px(pr.h),
      background: `radial-gradient(115% 120% at 46% 42%, transparent 62%, rgba(${sh},0.1) 100%)`,
    }, chrome);
    // Lamp light: a slow warm pool over the spread, driven per frame in seek() — firelight on
    // paper, and the ambient motion that keeps a settled page alive.
    const lamp = el('div', {
      position: 'absolute', inset: '0', zIndex: '2', pointerEvents: 'none', mixBlendMode: 'soft-light',
      background: `radial-gradient(92% 80% at 30% 9%, rgba(255,240,196,0.9) 0%, rgba(255,240,196,0.22) 48%, rgba(52,38,20,0.34) 100%)`,
      opacity: '0.7',
    }, chrome);
    return lamp;
  }

  // ---------------------------------------------------------------------------
  // The paperbook (uploaded storybook system): an open spread on a warm surface.
  // Every beat is one page — a serif title, a prose column of its narration, a
  // gouache illustration panel beneath — and once a page is read its leaf turns
  // at the spine, printed face and all. Two beats read per spread: left then right.
  // ---------------------------------------------------------------------------
  const PAPERBOOK = (plan) => Boolean(plan && plan.book === 'paperbook');
  const PB_SERIF = '"EB Garamond","Iowan Old Style","Liberation Serif","DejaVu Serif",Georgia,serif';
  // The hand face: children's-book lettering with per-glyph alternates baked into
  // the font (calt) — letterforms vary like handwriting, never a uniform UI face.
  const PB_HAND = '"Playpen Sans","Segoe Print","Comic Sans MS",cursive';

  function paperbookRects(plan) {
    const W = plan.canvas.w, H = plan.canvas.h;
    const bw = Math.round(W * 0.76), bh = Math.round(H * 0.80);
    const bx = Math.round((W - bw) / 2), by = Math.round(H * 0.072);
    const pw = Math.round(bw / 2);
    return {
      book: { x: bx, y: by, w: bw, h: bh },
      left: { x: bx, y: by, w: pw, h: bh },
      right: { x: bx + bw - pw, y: by, w: pw, h: bh },
      spine: bx + bw / 2,
    };
  }

  // The little irregular dashes and flecks of the stock — sparse, seeded, everywhere on a page.
  function pbSpeckle(plan) {
    // Handmade stock (Rollpie washi recipe): long kozo fibres, speck, and the
    // faint laid lines the paper mould's bamboo screen leaves in the sheet.
    const r = rng(seedHash(`pb-speckle:${plan.film_id}`));
    let marks = '';
    for (let i = 0; i < 42; i += 1) {
      const x = f2(r() * 120), y = f2(r() * 120);
      if (r() > 0.45) {
        const w = f2(1.6 + r() * 5.2), rot = f2(r() * 90 - 45);
        marks += `<rect x="${x}" y="${y}" width="${w}" height="0.7" rx="0.35" fill="${plan.brand.ink}" opacity="${f2(0.04 + r() * 0.09)}" transform="rotate(${rot} ${x} ${y})"/>`;
      } else {
        marks += `<circle cx="${x}" cy="${y}" r="${f2(0.5 + r() * 0.9)}" fill="${plan.brand.ink}" opacity="${f2(0.03 + r() * 0.07)}"/>`;
      }
    }
    for (let y = 7; y < 120; y += 7) {
      marks += `<line x1="0" y1="${y}" x2="120" y2="${y}" stroke="${plan.brand.ink}" stroke-width="0.35" opacity="0.028"/>`;
    }
    return `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120">${marks}</svg>`)}")`;
  }

  // Foxing + tide lines: seeded rust specks and pale water rings, denser toward
  // the leaf's edges the way age works in from the exposed margins.
  function pbAge(face, rect, plan, key) {
    const ink = plan.brand.ink;
    const rust = mixColor('#9a5f2a', ink, 0.15), tide = mixColor('#8a6a3c', ink, 0.2);
    const r = rng(seedHash(`pb-age:${plan.film_id}:${key}`));
    const svg = svgEl('svg', { viewBox: `0 0 ${rect.w} ${rect.h}`, 'aria-hidden': 'true' }, face);
    Object.assign(svg.style, { position: 'absolute', left: '0', top: '0', width: px(rect.w), height: px(rect.h), pointerEvents: 'none', zIndex: '5' });
    const edgeBias = () => {
      const t = r();
      return t < 0.4 ? t * 0.35 : t > 0.6 ? 0.65 + (t - 0.6) * 0.875 : t;
    };
    for (let i = 0; i < 26; i++) {
      const x = edgeBias() * rect.w, y = r() * rect.h;
      const rad = rect.w * (0.003 + r() * 0.011);
      svgEl('circle', { cx: f2(x), cy: f2(y), r: f2(rad), fill: rgbaOf(rust, 0.05 + r() * 0.10) }, svg);
    }
    for (let i = 0; i < 2; i++) {
      const x = rect.w * (0.2 + r() * 0.6), y = rect.h * (0.15 + r() * 0.7), rad = rect.w * (0.08 + r() * 0.10);
      svgEl('ellipse', { cx: f2(x), cy: f2(y), rx: f2(rad), ry: f2(rad * (0.6 + r() * 0.5)), fill: 'none', stroke: rgbaOf(tide, 0.06 + r() * 0.05), 'stroke-width': f2(rect.w * 0.006) }, svg);
    }
    // Tonal mottle: age never falls evenly — a few broad, faint darker drifts.
    for (let i = 0; i < 4; i++) {
      const x = r() * rect.w, y = r() * rect.h, rad = rect.w * (0.16 + r() * 0.22);
      svgEl('ellipse', { cx: f2(x), cy: f2(y), rx: f2(rad), ry: f2(rad * 0.7), fill: rgbaOf(tide, 0.035 + r() * 0.03) }, svg);
    }
  }

  function pbOrnamentArc(face, rect, plan) {
    const w = rect.w * 0.105, h = w * 0.36;
    const arc = svgEl('svg', { viewBox: '0 0 60 22', width: px(w), height: px(h), 'aria-hidden': 'true' }, face);
    Object.assign(arc.style, { position: 'absolute', left: px(rect.w / 2 - w / 2), top: px(rect.h * 0.048), opacity: '0.55' });
    const tone = mixColor(plan.brand.ink, '#b0766a', 0.72);
    svgEl('path', { d: 'M 5 19 A 25 14 0 0 1 55 19', fill: 'none', stroke: tone, 'stroke-width': '1.7', 'stroke-linecap': 'round' }, arc);
  }

  // The printed page's own ink: fine wavy rows drifting across the whole leaf and a
  // scatter of tiny bird ticks along the head — the hand-drawn water field the
  // reference book runs under every page, plus the odd pale sun behind the text.
  function pbPageInk(face, rect, plan, i, side, layout, slotRect, colRect) {
    const ink = plan.brand.ink, paper = plan.brand.paper;
    const pw = rect.w, ph = rect.h;
    const r = rng(seedHash(`pb-ink:${plan.film_id}:${i}`));
    const svg = svgEl('svg', { viewBox: `0 0 ${pw} ${ph}`, 'aria-hidden': 'true' }, face);
    Object.assign(svg.style, { position: 'absolute', left: '0', top: '0', width: px(pw), height: px(ph), pointerEvents: 'none', zIndex: '1' });
    // Pale halo: the soft sun/moon a picture-book page keeps behind its content —
    // it belongs in the open ink field, never bleeding onto a mounted plate, so
    // candidate positions are rejected until one clears the plate's rect.
    if (r() > 0.35 && !(layout === 'vignette' || layout === 'full')) {
      const hr = pw * (0.10 + r() * 0.08);
      const hit = (hx, hy, rc) => rc && hx + hr * 0.55 > rc.x && hx - hr * 0.55 < rc.x + rc.w
        && hy + hr * 0.55 > rc.y && hy - hr * 0.55 < rc.y + rc.h;
      for (let t = 0; t < 14; t++) {
        const hx = pw * (0.16 + r() * 0.62), hy = ph * (0.09 + r() * 0.30);
        if (!hit(hx, hy, slotRect) && !hit(hx, hy, colRect)) {
          // The halo is a pale bloom, brighter than the stock — never a shadow.
          // (mixColor returns rgb(); alpha goes on fill-opacity, not rgbaOf.)
          svgEl('circle', { cx: f2(hx), cy: f2(hy), r: f2(hr), fill: mixColor(paper, '#fffaf0', 0.72), 'fill-opacity': '0.55' }, svg);
          break;
        }
      }
    }
    // Wavy rows: long pen strokes run edge to edge, every row with its own drift.
    for (let y = ph * 0.13; y < ph * 0.97; y += ph * 0.0355) {
      const jy = y + (r() - 0.5) * ph * 0.012;
      let d = `M${f2(-pw * 0.02)} ${f2(jy)}`;
      const amp = ph * 0.0035 + r() * ph * 0.002, wl = pw * (0.10 + r() * 0.05);
      for (let x = 0; x < pw * 1.05; x += wl) {
        d += ` q${f2(wl * 0.5)} ${f2((r() > 0.5 ? 1 : -1) * amp)} ${f2(wl)} 0`;
      }
      svgEl('path', { d, fill: 'none', stroke: rgbaOf(ink, 0.045 + r() * 0.05), 'stroke-width': f2(Math.max(0.6, pw * 0.0016)), 'stroke-linecap': 'round' }, svg);
    }
    // Bird ticks: the little flock row an illustrator drops along the head.
    const nB = 3 + Math.floor(r() * 4);
    for (let b = 0; b < nB; b++) {
      const bx = pw * (0.06 + r() * 0.88), by = ph * (0.055 + r() * 0.055), bs = pw * (0.006 + r() * 0.004);
      svgEl('path', { d: `M${f2(bx - bs)} ${f2(by)} Q${f2(bx - bs * 0.5)} ${f2(by - bs * 0.8)} ${f2(bx)} ${f2(by)} Q${f2(bx + bs * 0.5)} ${f2(by - bs * 0.8)} ${f2(bx + bs)} ${f2(by)}`, fill: 'none', stroke: rgbaOf(ink, 0.30), 'stroke-width': f2(Math.max(0.7, pw * 0.002)), 'stroke-linecap': 'round' }, svg);
    }
  }

  // One page of the book for one beat: title + prose + illustration panel + folio.
  function buildPageFace(bn, i, side, plan, R, speckleUrl) {
    const rect = { w: R.left.w, h: R.left.h };
    const ink = plan.brand.ink, paper = plan.brand.paper;
    const pw = rect.w, ph = rect.h;
    const face = el('div', {
      position: 'absolute', inset: '0', overflow: 'hidden',
      background: `linear-gradient(${side === 'left' ? '97deg' : '83deg'}, ${mixColor(paper, '#e2d0ac', 0.26)} 0%, ${paper} 58%, ${mixColor(paper, '#e6d4b2', 0.2)} 100%)`,
    });
    face.dataset.page = String(i + 1);
    el('div', { position: 'absolute', inset: '0', backgroundImage: speckleUrl, opacity: '0.55', pointerEvents: 'none' }, face);
    pbOrnamentArc(face, rect, plan);
    const pg = (bn.beat && bn.beat.page) || {};
    const hero = (bn.beat && bn.beat.typography && (bn.beat.typography.blocks || []).find((b) => b.role === 'hero')) || null;
    const titleText = pg.title || (hero && hero.text) || (bn.beat.narration || '').split(/\s+/).slice(0, 6).join(' ');
    const pad = pw * 0.082;
    const layout = pg.layout || 'half';
    const pcut = pg.cut || '';
    const mats = pg.materials || [];
    // Layout grammar — each page carries its print and its plate its own way:
    //   full     the plate is the page, no print at all (illustration alone)
    //   half     print column above, plate below (the classic spread)
    //   diagonal the page is cut on a diagonal — plate fills the upper triangle,
    //            print sits in the lower corner, a cut lip runs along the join
    //   zipped   a zigzag cut divides art above from print below
    //   scissor  the same split torn by hand — a ragged deckle lip
    let slotRect, colRect = null, slotClip = null, divider = null, slotMask = null, framed = true;
    if (layout === 'full') {
      slotRect = { x: pad * 0.5, y: ph * 0.055, w: pw - pad, h: ph * 0.86 };
      slotMask = `radial-gradient(ellipse 104% 104% at 50% 50%, rgba(0,0,0,1) 78%, rgba(0,0,0,0.55) 92%, rgba(0,0,0,0) 100%)`;
      framed = false;
    } else if (layout === 'vignette') {
      // The world page: the painting washes the whole leaf and the print is set
      // straight onto it — the reference's lagoon page. The art fades off at the
      // page's own edge, no plate, no keyline.
      slotRect = { x: 0, y: 0, w: pw, h: ph };
      slotMask = `radial-gradient(ellipse 96% 96% at 50% 50%, rgba(0,0,0,1) 72%, rgba(0,0,0,0.5) 88%, rgba(0,0,0,0) 99%)`;
      framed = false;
      colRect = { x: pad, y: ph * 0.085, w: pw * 0.56 };
    } else if (layout === 'portrait') {
      // The character page: the figure stands on the paper itself at storybook
      // size — the slot is an invisible window so the page's own ink field is
      // the ground it walks on. Text sits clear at the head.
      slotRect = { x: pad * 0.4, y: ph * 0.30, w: pw - pad * 0.8, h: ph * 0.62 };
      framed = false;
      colRect = { x: pad, y: ph * 0.085, w: pw - pad * 2 };
    } else if (layout === 'spot') {
      // A spot illustration: the small free-floating mark picture-books drop in the
      // margin — art unframed mid-page, generous prose beneath.
      slotRect = { x: pw * 0.20, y: ph * 0.10, w: pw * 0.60, h: ph * 0.44 };
      slotMask = `radial-gradient(ellipse 86% 84% at 50% 50%, rgba(0,0,0,1) 56%, rgba(0,0,0,0.5) 78%, rgba(0,0,0,0) 90%)`;
      framed = false;
      colRect = { x: pad, y: ph * 0.58, w: pw - pad * 2 };
    } else if (layout === 'diagonal') {
      // The plate's bottom edge is cut on a slant — art above, the whole print block
      // safe in the strip under the cut's lowest point.
      slotRect = { x: pad * 0.4, y: ph * 0.05, w: pw - pad * 0.8, h: ph * 0.78 };
      const flip = pcut === 'left' ? -1 : 1; // right default: the cut dips toward the fore-edge
      const a = flip === 1 ? [[0, 0], [1, 0], [1, 0.80], [0, 0.60]] : [[0, 0], [1, 0], [1, 0.60], [0, 0.80]];
      slotClip = `polygon(${a.map(([px2, py2]) => `${f2(px2 * 100)}% ${f2(py2 * 100)}%`).join(',')})`;
      divider = { kind: 'diag', pts: a, rect: slotRect };
      colRect = { x: pad, y: ph * 0.72, w: pw - pad * 2 };
    } else if (layout === 'series') {
      // The sequence page: a strip of framed panels, one subject per cell with
      // torn paper gutters between them — phases, steps, before/afters.
      slotRect = { x: pad * 0.5, y: ph * 0.13, w: pw - pad, h: ph * 0.44 };
      const nCells = Math.max(2, Math.min(5, ((((bn.beat || {}).illustration || {}).entities || []).length) || 3));
      divider = { kind: 'series', n: nCells, seed: seedHash(`pbser:${plan.film_id}:${i}`), rect: slotRect };
      colRect = { x: pad, y: ph * 0.62, w: pw - pad * 2 };
    } else if (layout === 'zipped' || layout === 'scissor') {
      const cutY = ph * 0.56;
      slotRect = { x: pad * 0.4, y: ph * 0.055, w: pw - pad * 0.8, h: cutY - ph * 0.055 };
      const n = layout === 'zipped' ? 14 : 26;
      const er = rng(seedHash(`pbcut:${plan.film_id}:${i}`));
      let pts = `0% 0%, 100% 0%, `;
      const tail = [];
      for (let k = n; k >= 0; k--) {
        const xx = (k / n) * 100;
        const dy = layout === 'zipped'
          ? (k % 2 ? slotRect.h * 0.92 : slotRect.h)
          : slotRect.h * (0.96 + (er() - 0.5) * 0.10);
        tail.push(`${f2(xx)}% ${f2(dy / slotRect.h * 100)}%`);
      }
      slotClip = `polygon(0% 0%, 100% 0%, ${tail.join(', ')})`;
      divider = { kind: layout, n, seed: seedHash(`pbcut:${plan.film_id}:${i}`), y: slotRect.y + slotRect.h };
      colRect = { x: pad, y: cutY + ph * 0.02, w: pw - pad * 2 };
    } else {
      // half — the classic spread: print column above, a soft-edged painted
      // vignette below, art dissolving into the stock like the reference plates.
      slotRect = { x: pad * 0.7, y: ph * 0.40, w: pw - pad * 1.4, h: ph * 0.50 };
      slotMask = `radial-gradient(ellipse 94% 92% at 50% 52%, rgba(0,0,0,1) 64%, rgba(0,0,0,0.45) 84%, rgba(0,0,0,0) 96%)`;
      framed = false;
      colRect = { x: pad, y: ph * 0.10, w: pw - pad * 2 };
    }
    pbPageInk(face, rect, plan, i, side, layout, slotRect, colRect && { x: colRect.x, y: colRect.y, w: colRect.w, h: ph * 0.34 });
    if (colRect) {
      const col = el('div', { position: 'absolute', left: px(colRect.x), top: px(colRect.y), width: px(colRect.w) }, face);
      // Display vs text: titles set in the serif face, body in the hand — the
      // hierarchy a printed page carries.
      const titleEl = el('div', { fontFamily: PB_SERIF, fontWeight: '700', fontSize: px(pw * (layout === 'half' || layout === 'portrait' ? 0.054 : layout === 'full' || layout === 'vignette' ? 0.048 : 0.042)), lineHeight: '1.14', color: ink, letterSpacing: '0.006em' }, col);
      // Letterpress bite: light caught on the pressed edge below, ink shade above.
      titleEl.style.textShadow = `0 ${px(Math.max(0.5, pw * 0.0011))} 0 rgba(255,252,240,0.55), 0 ${px(-Math.max(0.5, pw * 0.0011))} 0 ${rgbaOf(ink, 0.22)}`;
      titleEl.textContent = titleText;
      if (mats.includes('foil')) {
        // Foil stamping: a gold leaf pressed into the letterforms.
        titleEl.style.backgroundImage = `linear-gradient(115deg, ${mixColor(ink, '#caa94e', 0.75)} 0%, ${mixColor('#caa94e', '#fff4d0', 0.6)} 38%, ${mixColor(ink, '#a07c2e', 0.6)} 62%, ${mixColor('#caa94e', '#fff0c0', 0.55)} 100%)`;
        titleEl.style.webkitBackgroundClip = 'text';
        titleEl.style.backgroundClip = 'text';
        titleEl.style.color = 'transparent';
      }
      const prose = el('div', {
        fontFamily: PB_HAND, fontWeight: '430', fontSize: px(pw * 0.0305), lineHeight: '1.5', color: rgbaOf(ink, 0.86),
        marginTop: px(ph * 0.018), maxWidth: px(colRect.w * 0.94),
        // Jittered hand: contextual alternates make each glyph draw a different
        // allograph (kako-jun/jitter baked into the typeface, not post-editing).
        fontFeatureSettings: '"calt" 1', fontVariationSettings: '"wght" 430',
      }, col);
      // Ink soak: the letterform blooms a hair into the absorbent stock.
      prose.style.textShadow = `0 0 ${px(Math.max(0.4, pw * 0.0008))} ${rgbaOf(ink, 0.30)}`;
      const narration = bn.beat.narration || '';
      prose.textContent = narration;
      if (pg.quote && layout !== 'half') {
        // On cut layouts the quote closes the column — inside the safe triangle, never
        // laid across the cut lip.
        const q = el('div', {
          fontFamily: PB_SERIF, fontStyle: 'italic', fontSize: px(pw * 0.029), lineHeight: '1.3',
          color: rgbaOf(ink, 0.70), marginTop: px(ph * 0.020),
        }, col);
        q.textContent = `“${pg.quote}”`;
      }
    }
    // The illustration: the beat's own scene pressed into the plate this layout cut — a
    // square plate with an engraved keyline, ink sunk into the stock, never a rounded card.
    const slot = el('div', {
      position: 'absolute', left: px(slotRect.x), top: px(slotRect.y), width: px(slotRect.w), height: px(slotRect.h),
      overflow: 'hidden',
      boxShadow: framed ? `inset 0 0 0 ${px(Math.max(0.8, pw * 0.0012))} ${rgbaOf(ink, 0.24)}, 0 ${px(ph * 0.004)} ${px(ph * 0.010)} ${rgbaOf(ink, 0.13)}` : 'none',
    }, face);
    if (slotClip) slot.style.clipPath = slotClip;
    if (slotMask) { slot.style.webkitMaskImage = slotMask; slot.style.maskImage = slotMask; }
    if (divider) {
      // The cut edge: a sliver of exposed raw stock running along the cut — torn or zigzagged,
      // the white lip a real paper cut leaves.
      const dEl = svgEl('svg', { viewBox: `0 0 ${slotRect.w} ${f2(ph * 0.05)}` }, face);
      const dh = ph * 0.05;
      let dp;
      if (divider.kind === 'diag') {
        const [p1, p2] = [divider.pts[divider.pts.length - 2], divider.pts[divider.pts.length - 1]];
        Object.assign(dEl.style, { position: 'absolute', left: px(slotRect.x), top: px(slotRect.y), width: px(slotRect.w), height: px(slotRect.h), pointerEvents: 'none' });
        dEl.setAttribute('viewBox', `0 0 ${slotRect.w} ${slotRect.h}`);
        const x1 = p1[0] * slotRect.w, y1 = p1[1] * slotRect.h, x2 = p2[0] * slotRect.w, y2 = p2[1] * slotRect.h;
        svgEl('path', { d: `M${f2(x1)} ${f2(y1)} L${f2(x2)} ${f2(y2)}`, stroke: mixColor(paper, '#ffffff', 0.7), 'stroke-width': f2(ph * 0.012), 'stroke-linecap': 'round' }, dEl);
        svgEl('path', { d: `M${f2(x1)} ${f2(y1)} L${f2(x2)} ${f2(y2)}`, stroke: rgbaOf(ink, 0.25), 'stroke-width': f2(ph * 0.003), 'stroke-linecap': 'round' }, dEl);
      } else if (divider.kind === 'series') {
        // Torn gutters between the sequence panels — raw stock showing where the
        // strip was cut, with the faint ink line a printed panel border leaves.
        Object.assign(dEl.style, { position: 'absolute', left: px(slotRect.x), top: px(slotRect.y), width: px(slotRect.w), height: px(slotRect.h), pointerEvents: 'none', overflow: 'visible' });
        dEl.setAttribute('viewBox', `0 0 ${slotRect.w} ${slotRect.h}`);
        const dr = rng(divider.seed ^ 0x55);
        for (let g = 1; g < divider.n; g++) {
          const gx = (g / divider.n) * slotRect.w;
          let gp = `M${f2(gx)} 0 `;
          for (let s2 = 1; s2 <= 7; s2++) gp += `L${f2(gx + (dr() - 0.5) * slotRect.w * 0.014)} ${f2((s2 / 7) * slotRect.h)} `;
          svgEl('path', { d: gp, fill: 'none', stroke: mixColor(paper, '#ffffff', 0.82), 'stroke-width': f2(ph * 0.016), 'stroke-linejoin': 'round' }, dEl);
          svgEl('path', { d: gp, fill: 'none', stroke: rgbaOf(ink, 0.22), 'stroke-width': f2(ph * 0.0032), 'stroke-linejoin': 'round' }, dEl);
        }
      } else {
        Object.assign(dEl.style, { position: 'absolute', left: px(slotRect.x), top: px(divider.y - dh * 0.5), width: px(slotRect.w), height: px(dh), pointerEvents: 'none', overflow: 'visible' });
        const dr = rng(divider.seed ^ 0x33);
        dp = `M0 ${f2(dh * 0.5)} `;
        for (let k = 1; k <= divider.n; k++) {
          const xx = (k / divider.n) * slotRect.w;
          const yy = divider.kind === 'zipped' ? dh * (k % 2 ? 0.15 : 0.85) : dh * (0.3 + dr() * 0.45);
          dp += `L${f2(xx)} ${f2(yy)} `;
        }
        svgEl('path', { d: dp, fill: 'none', stroke: mixColor(paper, '#ffffff', 0.7), 'stroke-width': f2(ph * 0.010), 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, dEl);
      }
    }
    const W0 = plan.canvas.w, H0 = plan.canvas.h;
    const k = Math.max(slotRect.w / W0, slotRect.h / H0);
    const tf = `translate(${f2((slotRect.w - W0 * k) / 2)}px,${f2((slotRect.h - H0 * k) / 2)}px) scale(${k.toFixed(4)})`;
    // 'paper' scenes have no base of their own — the slot stays transparent so the
    // leaf's own ink field and stock show through as the figure's ground.
    const onPaper = ((((bn.beat || {}).scene || {}).setting) === 'paper');
    const vpBg = onPaper ? 'transparent' : plan.brand.paper;
    // Viewports carry the canvas box at canvas scale; the slot does the clipping.
    const stillVp = el('div', { position: 'absolute', left: '0', top: '0', width: px(W0), height: px(H0), transformOrigin: '0 0', transform: tf, background: vpBg }, slot);
    const liveVp = el('div', { position: 'absolute', left: '0', top: '0', width: px(W0), height: px(H0), transformOrigin: '0 0', transform: tf, display: 'none' }, slot);
    if (framed) {
      // A plate that IS cut into the page keeps a painter's edge shade just inside
      // its cut — the only edge a cut layout draws.
      el('div', {
        position: 'absolute', inset: '0', pointerEvents: 'none', zIndex: '5',
        boxShadow: `inset 0 0 ${px(Math.max(slotRect.w, slotRect.h) * 0.07)} ${rgbaOf(ink, 0.10)}`,
      }, slot);
    }
    if (pg.quote && colRect && layout === 'half') {
      // The pull-quote lives as the line under the plate on a 'half' page.
      const qTop = slotRect.y + slotRect.h + ph * 0.018;
      const q = el('div', {
        position: 'absolute', left: px(slotRect.x), top: px(qTop), width: px(slotRect.w),
        fontFamily: PB_SERIF, fontStyle: 'italic', fontSize: px(pw * 0.031), color: rgbaOf(ink, 0.72), textAlign: 'center',
      }, face);
      q.textContent = `“${pg.quote}”`;
    }
    const folio = el('div', {
      position: 'absolute', bottom: px(ph * 0.03), [side === 'left' ? 'left' : 'right']: px(pw * 0.05),
      fontFamily: PB_HAND, fontWeight: '450', fontSize: px(pw * 0.026), color: rgbaOf(ink, 0.55),
      fontFeatureSettings: '"calt" 1',
    }, face);
    folio.textContent = String(i + 1);
    // Bank-art attribution: picture books credit their illustrators — a hairline
    // line under the plate in faint ink, like the copyright margin of a real book.
    const credits = (((bn.beat || {}).illustration || {}).entities || [])
      .filter((e) => e.photo && /^bank:/.test(e.photo.source || '') && e.photo.credit)
      .map((e) => e.photo.credit);
    if (credits.length) {
      const cr = el('div', {
        position: 'absolute', bottom: px(ph * 0.068), left: px(pad),
        fontFamily: PB_SERIF, fontStyle: 'italic', fontSize: px(pw * 0.016), color: rgbaOf(ink, 0.5),
      }, face);
      cr.textContent = `Illustration: ${[...new Set(credits)].join(' · ')}`;
    }
    // Material drops — the modern paper-book furniture this page carries.
    if (mats.includes('vellum')) {
      // A tissue guard: a translucent vellum sheet laid over the plate, deckled at its
      // free edge and a degree off-square, throwing the faintest hard shadow.
      const vv = el('div', {
        position: 'absolute', left: px(slotRect.x - pw * 0.012), top: px(slotRect.y - ph * 0.01),
        width: px(slotRect.w + pw * 0.024), height: px(slotRect.h + ph * 0.02),
        background: rgbaOf(mixColor(paper, '#ffffff', 0.5), 0.42), pointerEvents: 'none',
        transform: `rotate(${side === 'left' ? -0.8 : 0.8}deg)`, transformOrigin: '50% 0%',
        boxShadow: `${px(pw * 0.008)} ${px(ph * 0.01)} 0 ${rgbaOf(ink, 0.10)}`,
      }, face);
      vv.style.clipPath = `polygon(0% 0%, 100% 0%, 100% 96%, 96% 100%, 4% 100%, 0% 97%)`;
    }
    if (mats.includes('deckle') || mats.includes('sticker')) {
      // A loose die-cut sticker tucked at the page's outer corner — the motif mark,
      // deckled and tilted like a child pressed it into the book.
      const sArt = paperArtSvg((plan.motif && plan.motif.concept) || 'leaf', seedHash(`pbstk:${i}`), plan, `stk${i}`);
      if (sArt) {
        const sz = pw * (mats.includes('sticker') ? 0.16 : 0.11);
        const st = el('div', {
          position: 'absolute',
          [side === 'left' ? 'left' : 'right']: px(pw * 0.03), bottom: px(ph * 0.10),
          width: px(sz), height: px(sz), pointerEvents: 'none',
          transform: `rotate(${side === 'left' ? -14 : 12}deg)`,
          filter: `drop-shadow(${px(pw * 0.006)} ${px(ph * 0.007)} 0 ${rgbaOf(ink, 0.3)})`,
        }, face);
        st.appendChild(sArt);
      }
    }
    return { el: face, stillVp, liveVp, slot, index: i };
  }

  function buildEndpaper(plan, R, side, speckleUrl) {
    const rect = { w: R.left.w, h: R.left.h };
    const face = el('div', {
      position: 'absolute', inset: '0', overflow: 'hidden',
      background: `linear-gradient(${side === 'left' ? '97deg' : '83deg'}, ${mixColor(plan.brand.paper, '#e2d0ac', 0.26)} 0%, ${plan.brand.paper} 58%, ${mixColor(plan.brand.paper, '#e6d4b2', 0.2)} 100%)`,
    });
    el('div', { position: 'absolute', inset: '0', backgroundImage: speckleUrl, opacity: '0.55' }, face);
    pbOrnamentArc(face, rect, plan);
    if (side === 'right') {
      // The book always closes on words: the last right page is the colophon,
      // printed on a marbled endpaper — suminagashi ink rings dragged into swirls.
      const ink2 = plan.brand.ink;
      const acc = plan.brand.accent || ink2;
      const mSvg = svgEl('svg', { viewBox: `0 0 ${rect.w} ${rect.h}` }, face);
      Object.assign(mSvg.style, { position: 'absolute', left: '0', top: '0', width: px(rect.w), height: px(rect.h), pointerEvents: 'none' });
      const mr = rng(seedHash(`marble:${plan.film_id}`));
      for (let ring = 0; ring < 7; ring++) {
        const cx = rect.w * (0.22 + mr() * 0.56), cy = rect.h * (0.20 + mr() * 0.56);
        const base = rect.w * (0.05 + ring * 0.016);
        const col = ring % 3 === 2 ? acc : ink2;
        const op = ring % 3 === 2 ? 0.10 : 0.07;
        let d = '';
        for (let a = 0; a <= 32; a++) {
          const t = (a / 32) * Math.PI * 2;
          const wob = base * (1 + 0.22 * Math.sin(t * 3 + ring) + (mr() - 0.5) * 0.10);
          const x = cx + Math.cos(t) * wob, y = cy + Math.sin(t) * wob * 0.62;
          d += (a === 0 ? 'M' : 'L') + `${f2(x)} ${f2(y)} `;
        }
        svgEl('path', { d: d + 'Z', fill: 'none', stroke: rgbaOf(col, op), 'stroke-width': f2(rect.w * 0.006) }, mSvg);
      }
      const fin = el('div', {
        position: 'absolute', left: '0', right: '0', top: px(rect.h * 0.42), textAlign: 'center',
        fontFamily: PB_SERIF, fontWeight: '600', fontSize: px(rect.w * 0.075), letterSpacing: '0.04em',
        color: rgbaOf(ink2, 0.62),
      }, face);
      fin.textContent = 'The End';
      el('div', {
        position: 'absolute', left: px(rect.w * 0.38), top: px(rect.h * 0.55), width: px(rect.w * 0.24), height: px(Math.max(0.8, rect.w * 0.003)),
        background: rgbaOf(ink2, 0.3),
      }, face);
      el('div', {
        position: 'absolute', left: '0', right: '0', top: px(rect.h * 0.60), textAlign: 'center',
        fontFamily: PB_SERIF, fontStyle: 'italic', fontSize: px(rect.w * 0.026), color: rgbaOf(ink2, 0.45),
      }, face).textContent = plan.film_id ? plan.film_id.replace(/[-_]+/g, ' ') : '';
    }
    return { el: face, stillVp: null, liveVp: null, slot: null, index: -1 };
  }

  // The bound volume, built as a physical object: cast shadows pooled on the desk, cloth
  // cover boards overhanging the page block, the striped edges of the unread leaves at the
  // fore-edge and tail, a gutter valley at the spine, and a marker ribbon draping out.
  function buildPaperbook(bookGroup, plan, beats, opts) {
    const W = plan.canvas.w, H = plan.canvas.h;
    const R = paperbookRects(plan);
    const ink = plan.brand.ink, paper = plan.brand.paper;
    const speckleUrl = pbSpeckle(plan);
    const sh = ((plan.atmosphere && plan.atmosphere.shadow_rgb) || [52, 38, 20]).join(',');
    const minDim = Math.min(W, H);
    const castY = R.book.y + R.book.h;
    // The book sits on a surface: its shadow is a soft pool underneath, three densities —
    // ambient, contact, and the hair-thin line at the board's edge — fading to nothing.
    for (const [iw, ih, iy, op, blur] of [[1.10, 0.17, -0.055, 0.30, 26], [0.88, 0.105, -0.028, 0.38, 10], [0.68, 0.055, -0.012, 0.34, 4]]) {
      el('div', {
        position: 'absolute', left: px(R.book.x + R.book.w * (1 - iw) / 2), top: px(castY + R.book.h * iy),
        width: px(R.book.w * iw), height: px(R.book.h * ih), borderRadius: '50%', pointerEvents: 'none',
        background: `radial-gradient(50% 50% at 50% 50%, rgba(${sh},${op}) 0%, transparent 72%)`,
        filter: `blur(${px(blur)})`,
      }, bookGroup);
    }
    // The cover: cloth boards edging the page block on three sides — the rim of the volume
    // you see before its pages. Woven fine lines + a blind-embossed border on the lip.
    const over = R.book.h * 0.019, overTop = R.book.h * 0.012;
    const cloth = mixColor('#43362a', ink, 0.30), cloth2 = mixColor('#2e211a', ink, 0.34);
    const cover = el('div', {
      position: 'absolute', left: px(R.book.x - over), top: px(R.book.y - overTop),
      width: px(R.book.w + over * 2), height: px(R.book.h + overTop + over),
      borderRadius: px(minDim * 0.006), pointerEvents: 'none',
      background: `linear-gradient(168deg, ${mixColor(cloth, '#8a6a4a', 0.30)} 0%, ${cloth} 44%, ${cloth2} 100%)`,
      boxShadow: `0 ${px(H * 0.005)} ${px(H * 0.016)} rgba(${sh},0.42)`,
    }, bookGroup);
    el('div', {
      position: 'absolute', inset: '0', borderRadius: 'inherit', opacity: '0.5',
      backgroundImage: `repeating-linear-gradient(0deg, rgba(255,250,240,0.032) 0 1px, transparent 1px ${px(Math.max(2.4, minDim * 0.004))}), repeating-linear-gradient(90deg, rgba(16,10,5,0.11) 0 1px, transparent 1px ${px(Math.max(2.4, minDim * 0.004))})`,
    }, cover);
    el('div', {
      position: 'absolute', inset: px(R.book.h * 0.006), borderRadius: 'inherit',
      border: `${px(Math.max(1, minDim * 0.0016))} solid rgba(${sh},0.30)`,
    }, cover);
    // The page block: hairline stripes of leaf-ends at the fore-edges and tail. The
    // right stack visibly thins as spreads are read and the left fills in — tracked in seek.
    const edgeMax = Math.max(4.5, R.book.h * 0.016);
    const edgeTone = mixColor(paper, '#cbb694', 0.42), edgeLine = mixColor(paper, '#9c835c', 0.5);
    const edgeBg = (vert) => `repeating-linear-gradient(${vert ? '0deg' : '90deg'}, ${edgeLine} 0 ${px(Math.max(0.8, minDim * 0.0011))}, ${edgeTone} ${px(Math.max(0.8, minDim * 0.0011))} ${px(Math.max(1.9, minDim * 0.0028))}), linear-gradient(${vert ? '90deg' : '0deg'}, rgba(${sh},0.30), rgba(${sh},0) 26%, rgba(${sh},0) 74%, rgba(${sh},0.36))`;
    const foreR = el('div', {
      position: 'absolute', left: px(R.right.x + R.right.w), top: px(R.book.y - edgeMax * 0.1),
      width: px(edgeMax), height: px(R.book.h + edgeMax * 0.2), pointerEvents: 'none',
      background: edgeBg(true), borderRadius: '0 2px 2px 0',
    }, bookGroup);
    const foreL = el('div', {
      position: 'absolute', left: px(R.left.x - edgeMax * 0.2 - 1.2), top: px(R.book.y - edgeMax * 0.1),
      width: px(edgeMax * 0.2 + 1.2), height: px(R.book.h + edgeMax * 0.2), pointerEvents: 'none',
      background: edgeBg(true), borderRadius: '2px 0 0 2px',
    }, bookGroup);
    el('div', {
      position: 'absolute', left: px(R.book.x - edgeMax * 0.08), top: px(castY),
      width: px(R.book.w + edgeMax * 0.16), height: px(edgeMax * 0.75), pointerEvents: 'none',
      background: edgeBg(false), borderRadius: '0 0 2px 2px',
    }, bookGroup);
    // The gutter valley: the pages rolling down into the binding — a dark crease with its
    // soft falloff and the bright roll where the page lifts out of it.
    const gw = R.book.w * 0.020;
    el('div', {
      position: 'absolute', left: px(R.spine - gw * 1.6), top: px(R.book.y - edgeMax * 0.1),
      width: px(gw * 3.2), height: px(R.book.h + edgeMax * 0.2), zIndex: '5', pointerEvents: 'none',
      background: `linear-gradient(90deg, transparent, rgba(${sh},0.15) 20%, rgba(${sh},0.46) 50%, rgba(${sh},0.15) 80%, transparent)`,
    }, bookGroup);
    el('div', {
      position: 'absolute', left: px(R.spine - minDim * 0.0012), top: px(R.book.y - edgeMax * 0.1),
      width: px(minDim * 0.0024), height: px(R.book.h + edgeMax * 0.2), zIndex: '5', pointerEvents: 'none',
      background: `linear-gradient(180deg, rgba(${sh},0.22), rgba(${sh},0.62) 30%, rgba(${sh},0.62) 70%, rgba(${sh},0.22))`,
    }, bookGroup);
    const mkPage = (rect, side) => {
      const base = el('div', { position: 'absolute', left: px(rect.x), top: px(rect.y), width: px(rect.w), height: px(rect.h), overflow: 'hidden', zIndex: '3' }, bookGroup);
      base.style.background = `linear-gradient(${side === 'left' ? '97deg' : '83deg'}, ${mixColor(paper, '#e2d0ac', 0.26)} 0%, ${paper} 58%, ${mixColor(paper, '#e6d4b2', 0.2)} 100%)`;
      const chromeEls = [];
      // The gutter roll: light falls off into the spine on each page's inner edge.
      chromeEls.push(el('div', {
        position: 'absolute', top: '0', bottom: '0', width: px(rect.w * 0.10),
        [side === 'left' ? 'right' : 'left']: '0', zIndex: '4', pointerEvents: 'none',
        background: `linear-gradient(${side === 'left' ? '270deg' : '90deg'}, rgba(${sh},0.32) 0%, rgba(${sh},0.11) 45%, transparent 100%)`,
      }, base));
      // The fore-edge catching light — a bright hairline where the leaf meets the air.
      chromeEls.push(el('div', {
        position: 'absolute', top: '0', bottom: '0', width: px(Math.max(1.6, rect.w * 0.005)),
        [side === 'left' ? 'left' : 'right']: '0', zIndex: '4', pointerEvents: 'none',
        background: `linear-gradient(${side === 'left' ? '90deg' : '270deg'}, rgba(255,252,240,0.45), transparent)`,
      }, base));
      // The leaf's faint warm falloff toward its edges — light, not age.
      chromeEls.push(el('div', {
        position: 'absolute', inset: '0', zIndex: '4', pointerEvents: 'none',
        background: `radial-gradient(125% 112% at ${side === 'left' ? '10%' : '90%'} 50%, transparent 68%, rgba(176,138,78,0.06) 92%, rgba(118,88,45,0.10) 100%)`,
      }, base));
      base._chrome = chromeEls;
      return base;
    };
    const leftBase = mkPage(R.left, 'left');
    const rightBase = mkPage(R.right, 'right');
    const leafHost = el('div', { position: 'absolute', inset: '0', zIndex: '6', pointerEvents: 'none', transformStyle: 'preserve-3d' }, bookGroup);
    const lamp = el('div', {
      position: 'absolute', inset: '0', zIndex: '7', pointerEvents: 'none', mixBlendMode: 'soft-light', display: 'none',
      background: `radial-gradient(95% 82% at 34% 10%, rgba(255,242,205,0.85) 0%, rgba(255,242,205,0.20) 52%, rgba(${sh},0.30) 100%)`,
      opacity: '0.65',
    }, bookGroup);
    const faces = beats.map((bn, i) => buildPageFace(bn, i, i % 2 === 1 ? 'right' : 'left', plan, R, speckleUrl));
    const endL = buildEndpaper(plan, R, 'left', speckleUrl);
    const endR = buildEndpaper(plan, R, 'right', speckleUrl);
    const spread = {
      R, leftBase, rightBase, leafHost, lamp, faces, foreL, foreR, edgeMax,
      ends: { left: endL, right: endR },
      leaf: null, leafIdx: -1, _l: null, _r: null,
    };
    setPbFace(leftBase, faces[0] || endL);
    setPbFace(rightBase, faces[1] || endR);
    return spread;
  }

  function setPbFace(base, face) {
    if (base._face === face) return;
    base.replaceChildren(face.el, ...(base._chrome || []));
    base._face = face;
  }

  // The turning leaf: right page lifts at the spine and lands on the left — the
  // same bent-strip geometry as the single-page book, hinged on the gutter line.
  function buildSpreadLeaf(plan, spread, frontFace, backFace) {
    const rect = spread.R.right;
    const sh = ((plan.atmosphere && plan.atmosphere.shadow_rgb) || [52, 38, 20]).join(',');
    const leaf = el('div', {
      position: 'absolute', left: px(rect.x), top: px(rect.y), width: px(rect.w), height: px(rect.h), display: 'none',
      transformStyle: 'preserve-3d', transformOrigin: '0% 50%', willChange: 'transform', pointerEvents: 'none', zIndex: '8',
    });
    const shadow = el('div', {
      position: 'absolute', top: px(rect.y), height: px(rect.h), width: px(rect.w * 0.3), opacity: '0',
      background: `linear-gradient(90deg, transparent 0%, rgba(${sh},0.42) 50%, transparent 100%)`,
      filter: `blur(${px(rect.w * 0.035)})`, pointerEvents: 'none', willChange: 'transform, opacity',
    });
    const sw = rect.w / PAGE_STRIPS;
    let host = leaf;
    const strips = [];
    for (let i = 0; i < PAGE_STRIPS; i++) {
      const st = el('div', { position: 'absolute', top: '0', bottom: '0', width: px(sw), transformStyle: 'preserve-3d', transformOrigin: '0% 50%' }, host);
      st.style.left = i === 0 ? '0' : '100%';
      if (i > 0) st.style.transform = 'rotateY(var(--ptd))';
      const front = el('div', { position: 'absolute', inset: '0', overflow: 'hidden', backfaceVisibility: 'hidden', webkitBackfaceVisibility: 'hidden', filter: 'blur(var(--pb,0px))' }, st);
      const fw = el('div', { position: 'absolute', left: px(-i * sw), top: '0', width: px(rect.w), height: px(rect.h) }, front);
      const fc = frontFace.el.cloneNode(true); rescopeCloneIds(fc, `sl${frontFace.index}f${i}`); fw.appendChild(fc);
      const back = el('div', { position: 'absolute', inset: '0', overflow: 'hidden', backfaceVisibility: 'hidden', webkitBackfaceVisibility: 'hidden', transform: 'rotateY(180deg)', filter: 'blur(var(--pb,0px))' }, st);
      // The back of the sheet is the next left page: at strip i (leaf-local x' = [i*sw,(i+1)*sw])
      // it shows the face's slice [rect.w-(i+1)*sw, rect.w-i*sw] — mirrored by the clip's own
      // rotateY(180deg), so the print reads correctly mid-turn and lies right when it lands.
      const bw = el('div', { position: 'absolute', left: px((i + 1) * sw - rect.w), top: '0', width: px(rect.w), height: px(rect.h) }, back);
      const bc = backFace.el.cloneNode(true); rescopeCloneIds(bc, `sl${backFace.index}b${i}`); bw.appendChild(bc);
      el('div', { position: 'absolute', inset: '0', background: rgbaOf(plan.brand.paper, 0.14) }, back);
      const shF = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, front);
      const glF = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, front);
      const shB = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, back);
      const glB = el('div', { position: 'absolute', inset: '0', pointerEvents: 'none' }, back);
      strips.push({ st, shF, glF, shB, glB });
      host = st;
    }
    return { el: leaf, shadow, strips, sw, rect };
  }

  function driveSpreadLeaf(leaf, kke, plan) {
    const D = 180 / Math.PI, rect = leaf.rect;
    const th = Math.PI * kke;
    const beta = PAGE_BETA * Math.sin(Math.PI * kke);
    const tt = th + beta, td = (2 * beta) / PAGE_STRIPS;
    leaf.el.style.display = '';
    leaf.el.style.transform = `rotateY(${f2(-tt * D)}deg)`;
    leaf.el.style.setProperty('--ptd', `${f2(td * D)}deg`);
    leaf.el.style.setProperty('--pb', `${f2(Math.sin(Math.PI * kke) * 1.8)}px`);
    for (let i = 0; i < PAGE_STRIPS; i++) {
      const l1 = Math.abs(Math.cos(tt - i * td)), l2 = Math.abs(Math.cos(tt - (i + 1) * td));
      const a1 = (1 - l1) * 0.5, a2 = (1 - l2) * 0.5;
      const g1 = Math.max(0, l1 - 0.72) * 0.5, g2 = Math.max(0, l2 - 0.72) * 0.5;
      const { shF, glF, shB, glB } = leaf.strips[i];
      shF.style.background = `linear-gradient(90deg, rgba(52,38,20,${f2(a1)}), rgba(52,38,20,${f2(a2)}))`;
      shB.style.background = `linear-gradient(90deg, rgba(52,38,20,${f2(a2)}), rgba(52,38,20,${f2(a1)}))`;
      glF.style.background = `linear-gradient(105deg, transparent 32%, rgba(255,255,255,${f2(g1)}) 50%, transparent 68%)`;
      glB.style.background = `linear-gradient(105deg, transparent 32%, rgba(255,255,255,${f2(g2)}) 50%, transparent 68%)`;
    }
    const xEdge = rect.x + rect.w * Math.cos(tt);
    leaf.shadow.style.left = px(xEdge - rect.w * 0.15);
    leaf.shadow.style.opacity = f2(Math.sin(Math.PI * kke) * 0.55);
  }

  function settleSpreadLeaf(spread) {
    if (!spread.leaf) return;
    spread.leaf.el.style.display = 'none';
    spread.leaf.shadow.style.opacity = '0';
    spread.leaf = null;
    spread.leafIdx = -1;
  }

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
      const kk = !PAPERBOOK(plan) && k > 0 && tr ? prog(t, tr.start_ms, tr.end_ms) : 0;
      let rot = 0, ty = 0;
      if (kk > 0) {
        const ko = EASE.inCubic(kk);
        if (cam.move === 'push_through') { scale *= lerp(1, 1.1, ko); defocus += m.blur_px * ko * cam.blur; opacity = 1 - EASE.inOutCubic(kk); }
        else if (cam.move === 'pull_back') { scale *= lerp(1, 0.94, ko); defocus += m.blur_px * 0.6 * ko * cam.blur; opacity = 1 - EASE.inOutCubic(kk); }
        else if (cam.move === 'drift') { tx += -cam.dir * W * DRIFT_FRAC * EASE.inOutCubic(kk); opacity = 1 - EASE.inOutCubic(kk); }
        else if (cam.move === 'dissolve') defocus += m.blur_px * ko * cam.blur;
        // 'page' is not a pose: the leaf overlay turns the picture — the cam itself hides.
      }
      if (arrival) {
        const aa = clamp(t / Math.max(1, arrival.window_ms), 0, 1);
        const ka = EASE.outCubic(aa);
        if (cam.move === 'push_through') { scale *= lerp(0.92, 1, ka); defocus += m.blur_px * 0.5 * (1 - ka) * cam.blur; }
        else if (cam.move === 'pull_back') { scale *= lerp(1.06, 1, ka); defocus += m.blur_px * 0.3 * (1 - ka) * cam.blur; }
        else if (cam.move === 'drift') tx += cam.dir * W * DRIFT_FRAC * (1 - EASE.inOutCubic(aa));
        else if (cam.move === 'dissolve') defocus += m.blur_px * 0.4 * (1 - ka) * cam.blur;
        // 'page': the incoming page lies flat under the turning leaf — no arrival move.
      }
      return { scale, tx, ty, rot, opacity, defocus };
    };
    const now = poseAt(lt), was = poseAt(lt - bn.ctx.frameMs);
    const s = bn.cam.style;
    s.transform = `translate(${f2(now.tx)}px, ${f2(now.ty || 0)}px) rotate(${(now.rot || 0).toFixed(3)}deg) scale(${now.scale.toFixed(4)})`;
    s.opacity = now.opacity.toFixed(4);
    // The leaf swap: during a page turn the cam yields to the printed leaf; outside it the
    // leaf rests. Built lazily on the first transition frame so the snapshot is the settled
    // picture; live video media can't freeze into print, so it falls back to the flat peel.
    // In the paperbook every cut is a page turn — the leaf is the film's signature move.
    const pageActive = !PAPERBOOK(plan) && (cam.move === 'page' || plan.book) && tr && lt >= tr.start_ms && lt <= tr.end_ms && !arrival;
    if (bn._hasVideo === undefined) bn._hasVideo = Boolean(bn.cam.querySelector('video'));
    if (pageActive && !bn._hasVideo) {
      if (!bn._leaf) {
        bn._leafDir = plan.book ? 1 : (cam.dir >= 0 ? 1 : -1);
        bn._leaf = buildPageLeaf(bn, plan);
        bn.root.appendChild(bn._leaf.shadow);
        bn.root.appendChild(bn._leaf.el);
      }
      drivePageLeaf(bn, EASE.inOutCubic(prog(lt, tr.start_ms, tr.end_ms)), plan);
      s.visibility = 'hidden';
    } else {
      settlePageLeaf(bn);
      if (pageActive) {
        // Video fallback: the flat peel for pages carrying live media.
        const kp = EASE.inOutCubic(prog(lt, tr.start_ms, tr.end_ms));
        s.transform += ` translateY(${f2(-plan.canvas.h * 0.62 * kp)}px) rotate(${(cam.dir * 7.5 * kp).toFixed(3)}deg)`;
        s.opacity = kp < 0.9 ? '1' : f2(1 - (kp - 0.9) / 0.1);
      }
      // Once the leaf has taken this beat's picture the cam must not reappear over the
      // revealed next scene — a turned page stays turned until the beat ends. Before the
      // transition (a backward scrub) the live picture is still the truth.
      s.visibility = bn._leaf && tr && lt >= tr.start_ms ? 'hidden' : '';
    }
    applyDepthParallax(bn.bg, now, plan);
    bn.camBlur.apply(s, motionBlurStd((now.tx - was.tx) + Math.abs(now.scale - was.scale) * W / 2, Math.abs((now.ty || 0) - (was.ty || 0)), m.motion_blur * cam.blur), now.defocus > 0.2 ? `blur(${now.defocus.toFixed(2)}px)` : '');
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

  function applyBeat(bn, lt, stageFade, preRoll, plan) {
    applyBackgroundState(bn.bg, lt, bn.beat, stageFade, preRoll, bn.ctx.canvas, plan);
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
      assetUrl: (p) => p,
    }, options || {});
    installFonts(plan, opts.fontBase);

    const W = plan.canvas.w, H = plan.canvas.h;
    const atmo = plan.atmosphere || {};
    const stage = el('div', { position: 'relative', overflow: 'hidden', width: px(W), height: px(H), background: atmo.field || plan.brand.paper, color: plan.brand.ink, perspective: px(W * 2.4) }, mount);
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
    // Animated-paperbook chassis: the film lives inside a bound old book — a deckled aged page
    // clipped over the art on a lit desk. Every cut turns the curled leaf at the spine.
    const paperbook = PAPERBOOK(plan);
    const bookPage = paperbook ? null : bookPageRect(plan);
    let beatHost = stage;
    let bookGroup = null;
    let bookLamp = null;
    if (paperbook) {
      // A warm putty surface under the spread — table light, not walnut gloom.
      stage.style.background = `radial-gradient(130% 115% at 50% 38%, ${mixColor('#b8ac9a', plan.brand.paper, 0.12)} 0%, ${mixColor('#8f8271', plan.brand.ink, 0.10)} 74%, #6e6355 100%)`;
      bookGroup = el('div', {
        position: 'absolute', inset: '0', transformOrigin: '50% 58%', willChange: 'transform', transformStyle: 'preserve-3d',
      }, stage);
      // The book reads front-on — the reference spread is shot square to the
      // camera, so the volume sits flat and only the leaf turns in perspective.
      bookGroup._tilt = el('div', {
        position: 'absolute', inset: '0', transformStyle: 'preserve-3d',
      }, bookGroup);
      // Beats build hidden: their scenes mount inside the pages' illustration plates.
      beatHost = el('div', { position: 'absolute', left: '0', top: '0', width: px(W), height: px(H), visibility: 'hidden' }, bookGroup);
    } else if (bookPage) {
      // Warm walnut desk under the lamp pool: deep but alive, not burnt.
      const deskA = mixColor('#43311f', plan.brand.ink, 0.22), deskB = mixColor('#6b5438', plan.brand.accent || '#8a6a3a', 0.2);
      stage.style.background = `radial-gradient(120% 110% at 50% 42%, ${deskB} 0%, ${deskA} 64%, #2a1f12 100%)`;
      const pts = edgeRectPts(bookPage, 'torn', Math.min(W, H) * 0.011, rng(seedHash('book-page-deckle')), 0)
        .map((p) => `${f2(p[0])}px ${f2(p[1])}px`).join(',');
      // Everything bound to the book — page, beats, chrome — lives in one group so seek() can
      // breathe the whole volume: a slow drift and turn, like a book resting on a desk.
      bookGroup = el('div', {
        position: 'absolute', inset: '0', transformOrigin: '50% 58%', willChange: 'transform',
      }, stage);
      beatHost = el('div', {
        position: 'absolute', inset: '0', zIndex: '0',
        background: `linear-gradient(100deg, ${mixColor(plan.brand.paper, '#e6d6b4', 0.32)} 0%, ${plan.brand.paper} 55%, ${mixColor(plan.brand.paper, '#dfcba6', 0.24)} 100%)`,
        clipPath: `polygon(${pts})`,
      }, bookGroup);
    }
    const beats = plan.beats.map((b, i) => buildBeat(b, plan, beatHost, opts, i === plan.beats.length - 1, i));
    let spread = null;
    if (paperbook) {
      spread = buildPaperbook(bookGroup._tilt, plan, beats, opts);
      beats.forEach((b) => { b.root.style.display = 'none'; });
      // Each page's plate mounts its own beat's cam permanently — an inactive cam stays
      // frozen at its end state (it is the pressed still); only the live beat is driven.
      for (const bn of beats) {
        const ltEnd = bn.beat.duration_ms;
        applyBeat(bn, ltEnd, 1, 0, plan);
        applyCamera(bn, ltEnd, 0, null, plan, 0);
        spread.faces[bn.index].liveVp.appendChild(bn.cam);
      }
    } else if (bookPage) bookLamp = buildBookChrome(bookGroup, plan, bookPage);
    // World-bible motif: the film's signature mark, stamped in a corner of every beat — the
    // through-line the eye follows across scenes. Quiet by design: tonal ink, paper-card clipped.
    const motifEl = (() => {
      const m = plan.motif;
      if (!m || bookPage || paperbook) return null;
      const size = Math.round(Math.min(W, H) * 0.085);
      const inset = Math.round(Math.min(W, H) * 0.045);
      const pos = { left: 'auto', right: 'auto', top: 'auto', bottom: 'auto' };
      const [v, h] = (m.corner || 'bottom-right').split('-');
      pos[v === 'top' ? 'top' : 'bottom'] = px(inset);
      pos[h === 'left' ? 'left' : 'right'] = px(inset);
      const host = el('div', {
        position: 'absolute', ...pos, width: px(size), height: px(size), zIndex: '25',
        opacity: '0.24', pointerEvents: 'none', willChange: 'transform',
        transform: `rotate(${h === 'left' ? -4 : 4}deg)`,
        filter: 'drop-shadow(0 1px 2px rgba(0,0,0,.18))',
      }, stage);
      const motifArt = paperArtKey(m.concept) && paperArtSvg(paperArtKey(m.concept), seedHash(String(m.concept)), plan, 'motif');
      if (motifArt) {
        motifArt.setAttribute('width', '100%');
        motifArt.setAttribute('height', '100%');
        host.appendChild(motifArt);
      } else if (m.asset && m.asset.path) {
        fetchText(opts.assetUrl(m.asset.path)).then((txt) => {
          const doc = new DOMParser().parseFromString(txt, 'image/svg+xml');
          const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
          s.setAttribute('viewBox', doc.documentElement.getAttribute('viewBox') || '0 0 400 400');
          s.setAttribute('width', '100%'); s.setAttribute('height', '100%');
          s.innerHTML = doc.documentElement.innerHTML;
          host.appendChild(s);
        }).catch(() => host.remove());
      } else if (m.photo && m.photo.path) {
        const img = el('img', { width: '100%', height: '100%', objectFit: 'cover',
                                borderRadius: px(size * 0.1), border: `${px(Math.max(1, size * 0.02))} solid ${plan.brand.ink}` });
        img.src = opts.assetUrl(m.photo.path);
        host.appendChild(img);
      } else {
        // typographic tag — the word itself becomes the emblem
        host.style.cssText += `;display:flex;align-items:center;justify-content:center;width:auto;height:auto;padding:${px(size * 0.18)} ${px(size * 0.34)};background:${plan.brand.paper};border:${px(Math.max(1, size * 0.02))} solid ${plan.brand.ink};border-radius:${px(size * 0.16)};`;
        const t = el('span', { fontFamily: `"${plan.fonts.families.display}"`, fontSize: px(size * 0.34),
                               fontWeight: '600', letterSpacing: '0.04em', color: plan.brand.ink, whiteSpace: 'nowrap' }, host);
        t.textContent = m.word || m.concept || '';
      }
      return host;
    })();
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
      // Under the paperbook the grain lives on the book — paper grain belongs on paper,
      // not scattered across the desk. Elsewhere it textures the whole field.
      const gb = paperbook ? paperbookRects(plan).book : null;
      grain = el('div', {
        position: 'absolute', zIndex: '30', pointerEvents: 'none',
        ...(gb ? { left: px(gb.x - gb.w * 0.03), top: px(gb.y - gb.h * 0.03), width: px(gb.w * 1.06), height: px(gb.h * 1.06) } : { inset: '0' }),
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
      const overlapIdx = spread ? -1 : (tr && lt >= tr.start_ms && idx + 1 < beats.length ? idx + 1 : -1);
      if (idx !== current || overlapIdx !== currentOverlap) {
        // display, not visibility: children set their own visibility and would otherwise leak through.
        if (!spread) {
          beats.forEach((b, i) => { b.root.style.display = i === idx || i === overlapIdx ? 'block' : 'none'; });
          bn.root.style.zIndex = overlapIdx >= 0 ? '1' : '';
          if (overlapIdx >= 0) beats[overlapIdx].root.style.zIndex = '0';
        }
        current = idx;
        currentOverlap = overlapIdx;
      }
      const stageFade = overlapIdx >= 0 ? 1 - EASE.inOutCubic(prog(lt, tr.start_ms, tr.end_ms)) : 1;
      if (spread) {
        // Two pages per spread: even beats read on the left, odd on the right. A page turn
        // happens only at an odd beat's end — the leaf carries its whole printed face over.
        const odd = idx % 2 === 1;
        const flipping = odd && tr && lt >= tr.start_ms && lt < tr.end_ms;
        const passed = odd && tr && lt >= tr.end_ms;
        const sIdx = Math.floor(idx / 2) + (passed ? 1 : 0);
        const lIdx = sIdx * 2, rIdx = sIdx * 2 + 1;
        setPbFace(spread.leftBase, spread.faces[lIdx] || spread.ends.left);
        // While the leaf travels, the right side already shows the next spread's right page.
        const rShow = rIdx + (flipping ? 2 : 0);
        setPbFace(spread.rightBase, spread.faces[rShow] || spread.ends.right);
        // The book spends its leaves: the right fore-edge thins and the left fills in as
        // spreads turn — the thickness of pages still to read against pages already read.
        const maxS = Math.max(1, Math.ceil(beats.length / 2) - 1);
        const sprog = clamp(sIdx / maxS, 0, 1);
        spread.foreR.style.width = px(spread.edgeMax * (1 - sprog * 0.78) + 1.2);
        const lw = spread.edgeMax * (0.22 + sprog * 0.78) + 1.2;
        spread.foreL.style.width = px(lw);
        spread.foreL.style.left = px(spread.R.left.x - lw);
        // The live scene mounts only in the page currently being read; every other plate
        // shows its pressed still.
        for (let j = 0; j < beats.length; j += 1) {
          const fj = spread.faces[j], bj = beats[j];
          if (bj._hasVideo) {
            // Video beats park their cam in root and show only the pressed still.
            if (bj.cam.parentNode !== bj.root) bj.root.appendChild(bj.cam);
            fj.liveVp.style.display = 'none';
            fj.stillVp.style.display = '';
          } else {
            // Every face permanently mounts its own cam; inactive ones freeze at end state.
            if (bj.cam.parentNode !== fj.liveVp) fj.liveVp.appendChild(bj.cam);
            fj.liveVp.style.display = '';
            fj.stillVp.style.display = 'none';
          }
        }
        if (flipping) {
          if (!spread.leaf || spread.leafIdx !== idx) {
            settleSpreadLeaf(spread);
            const backFace = spread.faces[idx + 1] || spread.ends.left;
            spread.leaf = buildSpreadLeaf(plan, spread, spread.faces[idx], backFace);
            spread.leafIdx = idx;
            spread.leafHost.appendChild(spread.leaf.el);
            spread.leafHost.appendChild(spread.leaf.shadow);
          }
          driveSpreadLeaf(spread.leaf, EASE.inOutCubic(prog(lt, tr.start_ms, tr.end_ms)), plan);
        } else if (spread.leaf) settleSpreadLeaf(spread);
      }
      if (grain) {
        const OFF = [[0, 0], [41, 17], [23, 88], [97, 53], [61, 131], [13, 73], [109, 29], [73, 107]];
        const hold = atmo.grain_hold_ms > 0 ? atmo.grain_hold_ms : 93;
        const o = OFF[Math.floor(time / hold) % OFF.length];
        grain.style.backgroundPosition = `${-o[0]}px ${-o[1]}px`;
      }
      if (bookGroup) {
        bookGroup.style.transform = `translate(${f2(1.6 * Math.sin(time * 0.00105))}px,${f2(1.1 * Math.sin(time * 0.00087 + 1.4))}px) rotate(${f2(0.05 * Math.sin(time * 0.00062))}deg)`;
        if (bookLamp) bookLamp.style.opacity = f2(0.55 + 0.3 * Math.sin(time * 0.00078 + 0.5));
      }
      const t1 = performance.now();
      const kOut = overlapIdx >= 0 ? prog(lt, tr.start_ms, tr.end_ms) : 0;
      applyBeat(bn, lt, stageFade, bn.preRoll, plan);
      applyCamera(bn, lt, kOut, null, plan, bn.preRoll);
      if (overlapIdx >= 0) {
        const nb = beats[overlapIdx];
        applyBeat(nb, lt - tr.start_ms, 1, 0, plan);
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
      let hostM, inv;
      try { hostM = host.getScreenCTM(); } catch (e) { hostM = null; }
      if (!hostM) return null;
      try { inv = hostM.inverse(); } catch (e) { return null; }
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
          const readout = gl.extra.countText || body.querySelector('text') ||
            (gl.extra.wordHost && gl.extra.wordHost.querySelector('text'));
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

  return { createEditorialFilm, RUNTIME_VERSION, EASE, _internals: { prog, lineStagger, propAt, pointAlong, polyLength, OP_PROPERTY, PROPERTY_REST } };
});
