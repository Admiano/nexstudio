/**
 * NexStudio Paper Cast — renderer
 *
 * Turns a posed rig figure into layered paper cut-out SVG. Every shape is cut
 * with deterministic edge noise so a seed always reproduces the same character,
 * and shapes are emitted in the rig's depth order so far limbs sit behind the
 * body and read as a turned figure rather than a flat, camera-facing sticker.
 */
(function (root, factory) {
  const api = factory(typeof require === 'function' && typeof module === 'object' ? require('./paper-cast-rig.js') : root.NexPaperCastRig);
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexPaperCastRenderer = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Rig) {
  const PAPER_STYLES = {
    'clean-editorial': { jitter: 0.1, segments: 3, outline: 2.4, grain: 0.05, shadow: 0.12, corner: 0.9 },
    'handmade-scrapbook': { jitter: 0.5, segments: 6, outline: 3.4, grain: 0.16, shadow: 0.22, corner: 0.6 },
    'technical-notebook': { jitter: 0.18, segments: 4, outline: 2, grain: 0.08, shadow: 0.1, corner: 1 },
    'bold-paper-collage': { jitter: 0.34, segments: 5, outline: 4.2, grain: 0.12, shadow: 0.26, corner: 0.5 }
  };

  const PALETTE = {
    skin: ['#f0c9a4', '#dda87c', '#c1895f', '#9a6440', '#6f4630'],
    hair: ['#2f2a26', '#5a3a22', '#8c6239', '#c9a227', '#d8d3cc', '#b0462f'],
    ink: '#241f1c'
  };

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const round = (n) => Math.round(Number(n) * 100) / 100;

  function seeded(seed) {
    let h = 1779033703 ^ String(seed).length;
    for (let i = 0; i < String(seed).length; i++) {
      h = Math.imul(h ^ String(seed).charCodeAt(i), 3432918353);
      h = (h << 13) | (h >>> 19);
    }
    let a = h >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function tornEdge(from, to, rnd, style, amplitude) {
    const steps = Math.max(2, style.segments);
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len;
    const ny = dx / len;
    const points = [];
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      const wobble = (rnd() - 0.5) * 2 * style.jitter * amplitude * (i === steps ? 0.25 : 1);
      points.push({ x: from.x + dx * t + nx * wobble, y: from.y + dy * t + ny * wobble });
    }
    return points;
  }

  function cutPolygon(points, rnd, style, amplitude) {
    const cut = [];
    for (let i = 0; i < points.length; i++) {
      const from = points[i];
      const to = points[(i + 1) % points.length];
      cut.push(...tornEdge(from, to, rnd, style, amplitude));
    }
    return `M ${cut.map((p) => `${round(p.x)} ${round(p.y)}`).join(' L ')} Z`;
  }

  function strip(seg, rnd, style, widthScale) {
    const dx = seg.b.x - seg.a.x;
    const dy = seg.b.y - seg.a.y;
    const len = Math.hypot(dx, dy) || 1;
    const nx = (-dy / len) * 0.5;
    const ny = (dx / len) * 0.5;
    const w0 = seg.widthFrom * widthScale;
    const w1 = seg.widthTo * widthScale;
    const ex = (dx / len) * w1 * 0.45;
    const ey = (dy / len) * w1 * 0.45;
    const quad = [
      { x: seg.a.x + nx * w0, y: seg.a.y + ny * w0 },
      { x: seg.b.x + nx * w1 + ex, y: seg.b.y + ny * w1 + ey },
      { x: seg.b.x - nx * w1 + ex, y: seg.b.y - ny * w1 + ey },
      { x: seg.a.x - nx * w0, y: seg.a.y - ny * w0 }
    ];
    return cutPolygon(quad, rnd, style, w0 * 0.3);
  }

  function torsoPath(torso, rnd, style, garment) {
    const spread = garment.spread ?? 1;
    const hem = garment.hem ?? 1;
    const sl = torso.shoulderLeft;
    const sr = torso.shoulderRight;
    const hl = torso.hipLeft;
    const hr = torso.hipRight;
    const widen = (a, b, k) => ({ x: a.x + (a.x - b.x) * k, y: a.y + (a.y - b.y) * k });
    const points = [
      widen(sl, sr, (spread - 1) * 0.5),
      widen(sr, sl, (spread - 1) * 0.5),
      { x: hr.x + (hr.x - hl.x) * (hem - 1) * 0.5, y: hr.y + (torso.pelvis.y - torso.chest.y) * (garment.length ?? 0.18) },
      { x: hl.x + (hl.x - hr.x) * (hem - 1) * 0.5, y: hl.y + (torso.pelvis.y - torso.chest.y) * (garment.length ?? 0.18) }
    ];
    return cutPolygon(points, rnd, style, Math.abs(sr.x - sl.x) * 0.12 + 2);
  }

  /**
   * Hair is cut as a cap that stops at the brow plus a mass behind the skull, so
   * the face stays readable and a turned head shows its hair volume on the far
   * side rather than across the features.
   */
  function hairShapes(head, rnd, style, hair) {
    const r = head.radius;
    const lateral = head.lateral;
    const c = head.center;
    const drop = hair.length ?? 0.35;
    const brow = c.y - r * 0.34;
    const cap = [
      { x: c.x - r * 1.0, y: brow + r * 0.12 },
      { x: c.x - r * 1.02, y: c.y - r * 0.82 },
      { x: c.x - r * 0.5, y: c.y - r * 1.16 },
      { x: c.x + r * 0.5, y: c.y - r * 1.16 },
      { x: c.x + r * 1.02, y: c.y - r * 0.82 },
      { x: c.x + r * 1.0, y: brow + r * 0.12 },
      { x: c.x + r * 0.42 - lateral * r * 0.28, y: brow - r * 0.14 },
      { x: c.x - r * 0.46 - lateral * r * 0.28, y: brow + r * 0.06 }
    ];

    const backDir = lateral >= 0 ? -1 : 1;
    const masses = [];
    for (const side of [-1, 1]) {
      const weight = side === backDir ? 1 : Math.max(0, 1 - Math.abs(lateral) * 1.6);
      const length = drop * weight;
      if (length < 0.08) continue;
      masses.push(cutPolygon([
        { x: c.x + side * r * 0.2, y: c.y - r * 1.0 },
        { x: c.x + side * r * (0.98 + length * 0.35), y: c.y - r * 0.5 },
        { x: c.x + side * r * (0.86 + length * 0.5), y: c.y + r * length * 1.9 },
        { x: c.x + side * r * 0.26, y: c.y + r * length * 1.5 }
      ], rnd, style, r * 0.1));
    }

    return { cap: cutPolygon(cap, rnd, style, r * 0.1), masses };
  }

  /** Face features are placed from the head's own yaw, so a turned head loses the far eye. */
  function facePath(head, palette) {
    const r = head.radius;
    const c = head.center;
    const facing = head.facing;
    const lateral = head.lateral;
    if (facing <= -0.35) return '';
    const eyeY = c.y - r * 0.02 + (head.pitch || 0) * r * 0.012;
    const spacing = r * 0.34;
    const shift = lateral * r * 0.34;
    const open = Math.max(0.2, facing);
    const dir = lateral >= 0 ? 1 : -1;
    const near = { x: c.x + shift + spacing * dir * open, y: eyeY };
    const far = { x: c.x + shift - spacing * dir * open, y: eyeY };
    const eye = (p, squash) => `<ellipse class="pc-eye" cx="${round(p.x)}" cy="${round(p.y)}" rx="${round(r * 0.115 * squash)}" ry="${round(r * 0.14)}" fill="${palette.ink}"/>`;
    const brows = (p, squash) => `<path class="pc-brow" d="M ${round(p.x - r * 0.15 * squash)} ${round(eyeY - r * 0.3)} Q ${round(p.x)} ${round(eyeY - r * 0.38)} ${round(p.x + r * 0.15 * squash)} ${round(eyeY - r * 0.32)}" stroke="${palette.ink}" stroke-width="${round(r * 0.055)}" stroke-linecap="round" fill="none"/>`;
    const features = [eye(near, 1), brows(near, 1)];
    if (Math.abs(lateral) < 0.86) {
      const squash = Math.max(0.35, 1 - Math.abs(lateral));
      features.push(eye(far, squash), brows(far, squash));
    }
    const mouthX = c.x + shift * 1.1;
    features.push(`<path class="pc-mouth" d="M ${round(mouthX - r * 0.22 * open)} ${round(c.y + r * 0.42)} Q ${round(mouthX)} ${round(c.y + r * 0.58)} ${round(mouthX + r * 0.22 * open)} ${round(c.y + r * 0.42)}" fill="none" stroke="${palette.ink}" stroke-width="${round(r * 0.075)}" stroke-linecap="round"/>`);
    if (Math.abs(lateral) < 0.6) {
      for (const side of [-1, 1]) features.push(`<path class="pc-ear" d="M ${round(c.x + side * r * 0.94)} ${round(c.y - r * 0.12)} q ${round(side * r * 0.16)} ${round(r * 0.14)} 0 ${round(r * 0.3)}" fill="none" stroke="${palette.skinShade}" stroke-width="${round(r * 0.08)}" stroke-linecap="round"/>`);
    }
    return features.join('');
  }

  function nosePath(head, palette) {
    const r = head.radius;
    const c = head.center;
    const lateral = head.lateral;
    if (Math.abs(lateral) < 0.5 || head.facing <= -0.2) return '';
    const dir = lateral >= 0 ? 1 : -1;
    const tip = { x: c.x + dir * r * (0.98 + Math.abs(lateral) * 0.14), y: c.y + r * 0.12 };
    return `<path d="M ${round(c.x + dir * r * 0.82)} ${round(c.y - r * 0.08)} Q ${round(tip.x)} ${round(tip.y)} ${round(c.x + dir * r * 0.78)} ${round(c.y + r * 0.3)}" fill="${palette.skinShade}" stroke="none"/>`;
  }

  const shadeFor = (depth, span) => {
    if (!span) return 0;
    const t = (depth + span) / (2 * span);
    return Math.max(0, Math.min(1, 1 - t));
  };

  function mixHex(hex, target, amount) {
    const h = String(hex).replace('#', '');
    const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
    const t = String(target).replace('#', '');
    const tf = t.length === 3 ? t.split('').map((c) => c + c).join('') : t;
    const out = [0, 1, 2].map((i) => {
      const a = parseInt(full.slice(i * 2, i * 2 + 2), 16);
      const b = parseInt(tf.slice(i * 2, i * 2 + 2), 16);
      return Math.round(a + (b - a) * amount).toString(16).padStart(2, '0');
    });
    return `#${out.join('')}`;
  }

  function resolveLook(look) {
    const l = look || {};
    return {
      skin: l.skin || PALETTE.skin[2],
      skinShade: mixHex(l.skin || PALETTE.skin[2], '#000000', 0.16),
      hair: { color: l.hair?.color || PALETTE.hair[0], length: l.hair?.length ?? 0.3 },
      top: { color: l.top?.color || '#4f6d7a', spread: l.top?.spread ?? 1.08, hem: l.top?.hem ?? 1.02, length: l.top?.length ?? 0.24, sleeve: l.top?.sleeve ?? 0.55 },
      bottom: { color: l.bottom?.color || '#33404a', length: l.bottom?.length ?? 1, flare: l.bottom?.flare ?? 1 },
      shoes: { color: l.shoes?.color || '#2b2b2b' },
      accent: l.accent || '#d98032',
      ink: l.ink || PALETTE.ink
    };
  }

  /**
   * @returns {{svg:string, viewBox:string, width:number, height:number, figure:object}}
   */
  function render(figure, options) {
    const opts = options || {};
    const style = PAPER_STYLES[opts.paperStyle] || PAPER_STYLES['clean-editorial'];
    const look = resolveLook(opts.look);
    const seed = opts.seed || 'paper-cast';
    const rnd = seeded(seed);
    const depths = figure.parts.map((p) => p.depth);
    const span = Math.max(1, Math.max(...depths.map(Math.abs)));
    const shapes = [];

    for (const part of figure.parts) {
      const shade = shadeFor(part.depth, span);
      const darken = (hex) => mixHex(hex, '#1a1614', shade * 0.34);
      const stroke = `stroke="${look.ink}" stroke-width="${round(style.outline)}" stroke-linejoin="round"`;
      if (part.kind === 'torso') {
        shapes.push(`<path class="pc-torso" d="${torsoPath(part, rnd, style, look.top)}" fill="${look.top.color}" ${stroke}/>`);
        const pocket = { x: (part.hipLeft.x + part.hipRight.x) / 2, y: (part.chest.y + part.pelvis.y) / 2 };
        shapes.push(`<path class="pc-torso-fold" d="M ${round(pocket.x)} ${round(part.chest.y + 6)} L ${round(pocket.x)} ${round(pocket.y)}" stroke="${mixHex(look.top.color, '#000000', 0.25)}" stroke-width="${round(style.outline * 0.6)}" fill="none" stroke-linecap="round"/>`);
        continue;
      }
      if (part.kind === 'head') {
        const r = part.radius;
        const c = part.center;
        const hair = hairShapes(part, rnd, style, look.hair);
        const neckTop = { x: c.x, y: c.y + r * 0.95 };
        shapes.push(`<path class="pc-neck" d="${strip({ a: neckTop, b: part.neck, widthFrom: r * 0.52, widthTo: r * 0.62 }, rnd, style, 1)}" fill="${mixHex(look.skin, '#000000', 0.12)}" ${stroke}/>`);
        for (const mass of hair.masses) shapes.push(`<path class="pc-hair-back" d="${mass}" fill="${mixHex(look.hair.color, '#000000', 0.18)}" ${stroke}/>`);
        shapes.push(`<ellipse class="pc-head" cx="${round(c.x)}" cy="${round(c.y)}" rx="${round(r * 0.95)}" ry="${round(r * 1.08)}" fill="${look.skin}" ${stroke}/>`);
        shapes.push(nosePath(part, look));
        shapes.push(`<path class="pc-hair" d="${hair.cap}" fill="${look.hair.color}" ${stroke}/>`);
        shapes.push(facePath(part, look));
        continue;
      }
      const isLeg = /thigh|shin/.test(part.id);
      const isFoot = part.kind === 'foot';
      const isHand = part.kind === 'hand';
      const isUpperArm = /upper-arm/.test(part.id);
      const isForeArm = /fore-arm/.test(part.id);
      const base = isFoot ? look.shoes.color : isHand ? look.skin : isLeg ? look.bottom.color : isForeArm && look.top.sleeve < 0.6 ? look.skin : look.top.color;
      const widthScale = isLeg ? look.bottom.flare : isUpperArm ? look.top.spread * 0.96 : 1;
      shapes.push(`<path class="pc-${part.kind} pc-${part.side}" d="${strip(part, rnd, style, widthScale)}" fill="${darken(base)}" ${stroke}/>`);
      if (isUpperArm && look.top.sleeve > 0) {
        const sleeve = { ...part, b: { x: part.a.x + (part.b.x - part.a.x) * look.top.sleeve, y: part.a.y + (part.b.y - part.a.y) * look.top.sleeve }, widthTo: part.widthFrom * 1.02 };
        shapes.push(`<path class="pc-sleeve" d="${strip(sleeve, rnd, style, look.top.spread * 1.08)}" fill="${darken(look.top.color)}" ${stroke}/>`);
      }
    }

    const b = figure.bounds;
    const width = Math.max(1, b.maxX - b.minX);
    const height = Math.max(1, b.maxY - b.minY);
    const viewBox = `${round(b.minX)} ${round(b.minY)} ${round(width)} ${round(height)}`;
    const grainId = `pc-grain-${String(seed).replace(/[^a-z0-9]/gi, '')}`;
    const grain = style.grain
      ? `<filter id="${grainId}"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope="${style.grain}"/></feComponentTransfer><feComposite operator="in" in2="SourceGraphic"/></filter>`
      : '';
    const shadow = `<ellipse class="pc-contact-shadow" cx="${round((figure.joints.leftToe.x + figure.joints.rightToe.x) / 2)}" cy="${round(figure.ground)}" rx="${round(figure.height * 0.09)}" ry="${round(figure.height * 0.016)}" fill="#000" opacity="${style.shadow}"/>`;

    const body = `<g class="pc-figure" data-view-axis="${esc(figure.view.axis)}" data-head-axis="${esc(figure.view.headAxis)}">${shadow}${shapes.join('')}</g>`;
    const overlay = style.grain ? `<rect x="${round(b.minX)}" y="${round(b.minY)}" width="${round(width)}" height="${round(height)}" filter="url(#${grainId})" fill="${look.ink}" opacity="0.35" pointer-events="none"/>` : '';
    const svg = `<svg class="nex-paper-cast" xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" role="img" aria-label="${esc(opts.accessibilityLabel || 'Paper cast character')}"><defs>${grain}</defs>${body}${overlay}</svg>`;
    return { svg, group: body, defs: grain, viewBox, width, height, bounds: b, ground: figure.ground, figure };
  }

  function renderPose(options) {
    const figure = Rig.build(options);
    return render(figure, options);
  }

  return { render, renderPose, resolveLook, seeded, PAPER_STYLES, PALETTE, mixHex };
});
