/**
 * NexStudio Paper Cast — wardrobe
 *
 * Clothing as silhouette rather than as a colour. A fireman, a waiter and a
 * farmer differ first in the shape of the garment and what is on the head; a
 * recolour of one tunic makes them the same person six times. This module owns
 * that geometry — garment outlines, trim, headwear — and keeps it out of the
 * figure renderer, which only decides depth and fill.
 *
 * Every shape is built from the projected torso/head the rig already returns,
 * so a garment follows the body at any view axis without its own rig.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastWardrobe = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const round = (n) => Math.round(n * 100) / 100;
  const pt = (p) => `${round(p.x)} ${round(p.y)}`;

  /**
   * Garment catalogue. `hem` is a fraction of the chest-to-pelvis run for
   * garments that stop at the body, `legs` says what happens below the hips:
   *   'bare'  — the bottom garment shows (tunic, shirt, jacket)
   *   'fill'  — the legs take the garment's own colour (coverall, scrubs)
   *   'skirt' — a flaring panel is drawn over the legs (robe, coat, kaftan)
   */
  const GARMENTS = {
    tunic: { hem: 0.24, spread: 1, waist: 1, legs: 'bare', sleeve: 0.35, trim: [] },
    shirt: { hem: 0.2, spread: 0.98, waist: 0.94, legs: 'bare', sleeve: 0.55, trim: ['collar', 'placket'] },
    jacket: { hem: 0.36, spread: 1.07, waist: 1.02, legs: 'bare', sleeve: 1, trim: ['lapel', 'placket', 'belt'] },
    coverall: { hem: 0.3, spread: 1.05, waist: 1.04, legs: 'fill', sleeve: 1, trim: ['collar', 'placket', 'belt'] },
    coat: { hem: 0.95, spread: 1.06, waist: 1.02, legs: 'skirt', flare: 1.25, sleeve: 1, trim: ['lapel', 'belt'] },
    robe: { hem: 1.02, spread: 1.04, waist: 1.12, legs: 'skirt', flare: 1.5, sleeve: 1, trim: [] },
    kurta: { hem: 0.62, spread: 1.02, waist: 1.02, legs: 'bare', sleeve: 0.7, trim: ['placket'] },
    dress: { hem: 1, spread: 0.98, waist: 0.88, legs: 'skirt', flare: 1.6, sleeve: 0.2, trim: [] },
    vest: { hem: 0.26, spread: 1.04, waist: 1, legs: 'bare', sleeve: 0, trim: [] }
  };

  /** Worn over the garment: an apron is the waiter, the cook and the smith. */
  const OVERLAYS = {
    apron: { hem: 0.95, width: 0.62, bib: true },
    'waist-apron': { hem: 0.55, width: 0.72, bib: false },
    tabard: { hem: 0.5, width: 0.78, bib: true }
  };

  const HEADWEAR = {
    hijab: { coversHair: true, drape: true, height: 1.18, width: 1.16 },
    headtie: { coversHair: true, drape: false, height: 1.6, width: 1.25, knot: true },
    turban: { coversHair: true, drape: false, height: 1.42, width: 1.2, bands: 3 },
    kufi: { coversHair: false, drape: false, height: 1.1, width: 0.86, dome: true },
    cap: { coversHair: false, drape: false, height: 1.12, width: 1.02, brim: 1.1 },
    helmet: { coversHair: true, drape: false, height: 1.22, width: 1.14, brim: 1.35, crest: true },
    hat: { coversHair: false, drape: false, height: 1.16, width: 1.0, brim: 1.8 }
  };

  /**
   * The clothed torso outline. Garments hang off the BODY, not the canvas:
   * the down-axis follows the chest->pelvis line and the across-axis is its
   * normal, so the same cut sits right whether the figure stands, bends,
   * sits or lies prone. Half-widths are segment lengths at each level —
   * measuring them off a shared vertical midline let a leaning pelvis
   * inflate the hem into a sail.
   */
  /**
   * The spine hinges where pelvis->chest meets chest->neck, so garment geometry
   * walks a two-segment centerline (shoulders -> waist -> hips) instead of one
   * straight axis: each level keeps its own across-direction, and the hem
   * continues along the lower segment. On a straight spine the frame is
   * identical to the old single axis.
   */
  function torsoFrame(torso) {
    const mid = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });
    const unit = (a, b) => {
      const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.hypot(dx, dy) || 1;
      return { x: dx / d, y: dy / d, len: d };
    };
    const S = mid(torso.shoulderLeft, torso.shoulderRight);
    const H = mid(torso.hipLeft, torso.hipRight);
    const W = (torso.waistLeft && torso.waistRight)
      ? mid(torso.waistLeft, torso.waistRight)
      : { x: S.x + (H.x - S.x) * 0.62, y: S.y + (H.y - S.y) * 0.62 };
    const ud = unit(S, W);                            // down the upper torso
    const ld = unit(W, H);                            // down the lower torso
    const shd = unit(torso.shoulderLeft, torso.shoulderRight);
    const wad = (torso.waistLeft && torso.waistRight)
      ? unit(torso.waistLeft, torso.waistRight)
      : unit(torso.hipLeft, torso.hipRight);
    const hpd = unit(torso.hipLeft, torso.hipRight);
    return { S, W, H, ud, ld, shd, wad, hpd, run: ud.len + ld.len };
  }

  function torsoPath(torso, spec) {
    const s = spec || {};
    const f = torsoFrame(torso);
    const segHalf = (p, q) => Math.hypot(q.x - p.x, q.y - p.y) / 2;
    const shHalf = segHalf(torso.shoulderLeft, torso.shoulderRight) * (s.spread ?? 1);
    const hipHalf = segHalf(torso.hipLeft, torso.hipRight);
    const waistHalf = (torso.waistRight && torso.waistLeft
      ? segHalf(torso.waistLeft, torso.waistRight)
      : hipHalf) * (s.waist ?? 1);
    // The hem follows the hips, not the waist: letting a heavy waist set the
    // hem turns every garment into a bell that swallows the arms.
    const hemHalf = Math.max(hipHalf * 1.04, waistHalf * 0.84) * (s.flare ?? 1);
    const hem = (s.hem ?? 0.24) * f.run;
    const hmx2 = f.H.x + f.ld.x * hem, hmy2 = f.H.y + f.ld.y * hem;   // hem centre, past hips
    const A = { x: f.S.x - f.shd.x * shHalf, y: f.S.y - f.shd.y * shHalf };
    const B = { x: f.S.x + f.shd.x * shHalf, y: f.S.y + f.shd.y * shHalf };
    const WaR = { x: f.W.x + f.wad.x * waistHalf, y: f.W.y + f.wad.y * waistHalf };
    const WaL = { x: f.W.x - f.wad.x * waistHalf, y: f.W.y - f.wad.y * waistHalf };
    const HeR = { x: hmx2 + f.hpd.x * hemHalf, y: hmy2 + f.hpd.y * hemHalf };
    const HeL = { x: hmx2 - f.hpd.x * hemHalf, y: hmy2 - f.hpd.y * hemHalf };
    // Down from the shoulder before out to the waist. Running a single curve
    // from shoulder to waist balloons the chest sideways over the arms, which
    // is what made broad and heavy figures read as shoulder pads.
    const armhole = f.run * 0.3;
    return `M ${pt(A)} Q ${round(f.S.x - f.ud.x * f.run * 0.16)} ${round(f.S.y - f.ud.y * f.run * 0.16)} ${pt(B)} `
      + `C ${round(B.x + f.ud.x * armhole)} ${round(B.y + f.ud.y * armhole)} ${round(WaR.x - f.ud.x * f.run * 0.12)} ${round(WaR.y - f.ud.y * f.run * 0.12)} ${pt(WaR)} `
      + `C ${round(WaR.x + f.ld.x * f.run * 0.1)} ${round(WaR.y + f.ld.y * f.run * 0.1)} ${round(HeR.x - f.ld.x * hem * 0.55)} ${round(HeR.y - f.ld.y * hem * 0.55)} ${pt(HeR)} `
      + `Q ${round(hmx2 + f.ld.x * hem * 0.35)} ${round(hmy2 + f.ld.y * hem * 0.35)} ${pt(HeL)} `
      + `C ${round(HeL.x - f.ld.x * hem * 0.55)} ${round(HeL.y - f.ld.y * hem * 0.55)} ${round(WaL.x + f.ld.x * f.run * 0.1)} ${round(WaL.y + f.ld.y * f.run * 0.1)} ${pt(WaL)} `
      + `C ${round(WaL.x - f.ud.x * f.run * 0.12)} ${round(WaL.y - f.ud.y * f.run * 0.12)} ${round(A.x + f.ud.x * armhole)} ${round(A.y + f.ud.y * armhole)} ${pt(A)} Z`;
  }

  /** Cloth from the hips down: wrapper, coat skirt, kaftan, dress. */
  function skirtPath(torso, joints, spec) {
    const s = spec || {};
    const f = torsoFrame(torso);
    const hl = torso.hipLeft;
    const hr = torso.hipRight;
    const hmx = f.H.x, hmy = f.H.y;
    // Skirts continue along the lower-spine axis past the hips — the same
    // cloth sits right on a seated or leaning figure.
    const dx = f.ld.x, dy = f.ld.y;
    const nx = f.hpd.x, ny = f.hpd.y;
    const run0 = f.run;
    const half = Math.hypot(hr.x - hl.x, hr.y - hl.y) * 0.5;
    const amx = (joints.leftAnkle.x + joints.rightAnkle.x) / 2;
    const amy = (joints.leftAnkle.y + joints.rightAnkle.y) / 2;
    const legLen = Math.hypot(amx - hmx, amy - hmy) || run0 * 1.2;
    const len = legLen * (s.length ?? 0.92);
    const tx = hmx - dx * half * 0.15, ty = hmy - dy * half * 0.15;   // waistband sits a touch above the hips
    const ex = hmx + dx * len, ey = hmy + dy * len;                 // hem centre
    const flare = half * (s.flare ?? 1.5);
    return `M ${round(tx - nx * half * 1.05)} ${round(ty - ny * half * 1.05)} L ${round(tx + nx * half * 1.05)} ${round(ty + ny * half * 1.05)} `
      + `L ${round(ex + nx * flare)} ${round(ey + ny * flare)} Q ${round(ex + dx * half * 0.35)} ${round(ey + dy * half * 0.35)} ${round(ex - nx * flare)} ${round(ey - ny * flare)} Z`;
  }

  /**
   * Trim: collars, plackets, belts and hi-vis bands. Small marks, but they are
   * what separates a uniform from a shirt in a flat illustration.
   */
  function trimShapes(torso, spec) {
    const s = spec || {};
    const kinds = s.trim || [];
    // Trims walk the same bent centerline as torsoPath — a collar on a leaning
    // or prone figure still sits at the neck, and a belt follows the pelvis
    // plane instead of a screen-horizontal line.
    const f = torsoFrame(torso);
    const run = f.run;
    const shHalf = Math.hypot(torso.shoulderRight.x - torso.shoulderLeft.x,
                              torso.shoulderRight.y - torso.shoulderLeft.y) / 2;
    const waHalf = (torso.waistLeft && torso.waistRight)
      ? Math.hypot(torso.waistRight.x - torso.waistLeft.x,
                   torso.waistRight.y - torso.waistLeft.y) / 2
      : shHalf;
    const hipHalf = Math.hypot(torso.hipRight.x - torso.hipLeft.x,
                               torso.hipRight.y - torso.hipLeft.y) / 2;
    const hipSpan = hipHalf * 2;
    // P(fx, fy): fx = fraction of the local half-width across the body,
    // fy = fraction of the torso run down the bent centerline.
    const P = (fx, fy) => {
      if (fy <= 0.5) {
        const u = fy / 0.5;
        const ax = f.shd.x + (f.wad.x - f.shd.x) * u;
        const ay = f.shd.y + (f.wad.y - f.shd.y) * u;
        const h = shHalf + (waHalf - shHalf) * u;
        return { x: f.S.x + f.ud.x * f.ud.len * u + ax * h * fx,
                 y: f.S.y + f.ud.y * f.ud.len * u + ay * h * fx };
      }
      const u = (fy - 0.5) / 0.5;
      const ax = f.wad.x + (f.hpd.x - f.wad.x) * u;
      const ay = f.wad.y + (f.hpd.y - f.wad.y) * u;
      const h = waHalf + (hipHalf - waHalf) * u;
      return { x: f.W.x + f.ld.x * f.ld.len * u + ax * h * fx,
               y: f.W.y + f.ld.y * f.ld.len * u + ay * h * fx };
    };
    const seg = (a, b, st, sw) => `<path d="M ${round(a.x)} ${round(a.y)} L ${round(b.x)} ${round(b.y)}" fill="none" stroke="${st}" stroke-width="${round(sw)}" stroke-linecap="round"/>`;
    const out = [];
    const ink = s.trimColor;

    if (kinds.includes('collar')) {
      const a = P(-0.34, 0), b = P(0, 0.2), c = P(0.34, 0), q = P(0, 0.07);
      out.push({ fill: ink, svg: `<path d="M ${round(a.x)} ${round(a.y)} L ${round(b.x)} ${round(b.y)} L ${round(c.x)} ${round(c.y)} Q ${round(q.x)} ${round(q.y)} ${round(a.x)} ${round(a.y)} Z"/>` });
    }
    if (kinds.includes('lapel')) {
      const p1 = P(-0.42, 0), p2 = P(0, 0.34), p3 = P(0.42, 0), p4 = P(0.16, 0.06), p5 = P(0, 0.2), p6 = P(-0.16, 0.06);
      out.push({ fill: ink, svg: `<path d="M ${round(p1.x)} ${round(p1.y)} L ${round(p2.x)} ${round(p2.y)} L ${round(p3.x)} ${round(p3.y)} L ${round(p4.x)} ${round(p4.y)} L ${round(p5.x)} ${round(p5.y)} L ${round(p6.x)} ${round(p6.y)} Z"/>` });
    }
    if (kinds.includes('placket')) {
      const r = run * 0.035;
      const buttons = [0.34, 0.6, 0.86].map((t) => { const c = P(0, t); return `<circle cx="${round(c.x)}" cy="${round(c.y)}" r="${round(r)}"/>`; }).join('');
      out.push({ fill: ink, svg: buttons });
    }
    if (kinds.includes('belt')) {
      const k = hipSpan / (shHalf * 2) * 0.56;
      out.push({ fill: ink, svg: seg(P(-k, 0.96), P(k, 0.96), ink, run * 0.1) });
    }
    if (kinds.includes('band')) {
      out.push({ fill: s.bandColor || '#f2d64b', svg: seg(P(-0.98, 0.42), P(0.98, 0.42), s.bandColor || '#f2d64b', run * 0.11) });
    }
    if (kinds.includes('badge')) {
      const c = P(0.45, 0.18);
      const r = run * 0.07;
      out.push({ fill: s.badgeColor || '#d8b24a', svg: `<circle cx="${round(c.x)}" cy="${round(c.y)}" r="${round(r)}"/>` });
    }
    return out;
  }

  /** Apron/tabard worn over everything the torso has on. */
  function overlayShapes(torso, joints, spec) {
    const kind = spec && spec.kind;
    const over = OVERLAYS[kind];
    if (!over) return [];
    const cx = (torso.hipLeft.x + torso.hipRight.x) / 2;
    const run = torso.pelvis.y - torso.chest.y || 1;
    const ankle = Math.max(joints.leftAnkle.y, joints.rightAnkle.y);
    const top = torso.pelvis.y - run * 0.1;
    const hemY = top + (ankle - top) * over.hem;
    const half = Math.abs(torso.hipRight.x - torso.hipLeft.x) * 0.5 * (over.width * 1.6);
    const shapes = [`<path d="M ${round(cx - half)} ${round(top)} L ${round(cx + half)} ${round(top)} L ${round(cx + half * 1.04)} ${round(hemY)} L ${round(cx - half * 1.04)} ${round(hemY)} Z"/>`];
    if (over.bib) {
      const bibHalf = half * 0.62;
      const bibTop = torso.chest.y + run * 0.2;
      shapes.push(`<path d="M ${round(cx - bibHalf)} ${round(bibTop)} L ${round(cx + bibHalf)} ${round(bibTop)} L ${round(cx + bibHalf)} ${round(top)} L ${round(cx - bibHalf)} ${round(top)} Z"/>`);
    }
    return [{ fill: (spec && spec.color) || '#efe7d8', svg: shapes.join('') }];
  }

  /**
   * Headwear, split into what sits behind the head and what sits in front of
   * it. `coversHair` decides whether the hair is drawn at all: a hijab or a
   * helmet replaces the hair shape rather than sitting on top of it.
   */
  function headwearShapes(head, spec) {
    const kind = spec && spec.kind;
    const hw = HEADWEAR[kind];
    if (!hw) return { shapes: [], front: [], coversHair: false };
    const r = head.radius;
    const c = head.center;
    const lateral = head.lateral;
    const color = (spec && spec.color) || '#3b4450';
    const shapes = [];

    if (hw.drape) {
      // Falls past the jaw and over the shoulders: the silhouette, not the
      // colour, is what makes a headscarf read. The body of it goes behind the
      // head and only the brow edge comes forward, so the face stays open.
      shapes.push({ fill: color, svg: `<path d="M ${round(c.x - r * hw.width)} ${round(c.y + r * 1.7)} `
        + `L ${round(c.x - r * hw.width)} ${round(c.y - r * 0.1)} `
        + `Q ${round(c.x)} ${round(c.y - r * hw.height * 1.55)} ${round(c.x + r * hw.width)} ${round(c.y - r * 0.1)} `
        + `L ${round(c.x + r * hw.width)} ${round(c.y + r * 1.7)} `
        + `Q ${round(c.x)} ${round(c.y + r * 2)} ${round(c.x - r * hw.width)} ${round(c.y + r * 1.7)} Z"/>` });
      const brow = [{ fill: color, svg: `<path d="M ${round(c.x - r * hw.width)} ${round(c.y - r * 0.3)} `
        + `Q ${round(c.x)} ${round(c.y - r * hw.height * 1.4)} ${round(c.x + r * hw.width)} ${round(c.y - r * 0.3)} `
        + `Q ${round(c.x)} ${round(c.y - r * 0.8)} ${round(c.x - r * hw.width)} ${round(c.y - r * 0.3)} Z"/>` }];
      return { shapes, front: brow, coversHair: true };
    }

    // Everything sits on or above the brow: a cap that reaches the eyes reads
    // as a blindfold in a flat drawing.
    const brow = c.y - r * 0.42;
    const capTop = c.y - r * hw.height;
    // The control point overshoots the crown: a quadratic through it peaks
    // around halfway, which otherwise leaves a band of hair above the cap.
    shapes.push({ fill: color, svg: `<path d="M ${round(c.x - r * hw.width)} ${round(brow)} Q ${round(c.x)} ${round(capTop - r * 0.62)} ${round(c.x + r * hw.width)} ${round(brow)} Q ${round(c.x)} ${round(brow - r * 0.32)} ${round(c.x - r * hw.width)} ${round(brow)} Z"/>` });

    if (hw.bands) {
      for (let i = 0; i < hw.bands; i += 1) {
        const t = (i + 1) / (hw.bands + 1);
        const y = brow - r * (hw.height - 0.42) * t;
        shapes.push({ fill: 'none', stroke: (spec && spec.trimColor) || '#00000022', svg: `<path d="M ${round(c.x - r * hw.width * 0.96)} ${round(y)} Q ${round(c.x)} ${round(y - r * 0.34)} ${round(c.x + r * hw.width * 0.96)} ${round(y)}" fill="none" stroke="${(spec && spec.trimColor) || 'rgba(0,0,0,0.18)'}" stroke-width="${round(r * 0.08)}"/>` });
      }
    }
    if (hw.knot) {
      shapes.push({ fill: color, svg: `<ellipse cx="${round(c.x - lateral * r * 0.35)}" cy="${round(capTop + r * 0.22)}" rx="${round(r * 0.5)}" ry="${round(r * 0.3)}"/>` });
    }
    if (hw.brim) {
      const dir = lateral >= 0 ? 1 : -1;
      const reach = r * hw.brim;
      const y = brow;
      const forward = Math.max(0.25, Math.abs(head.facing));
      shapes.push({ fill: (spec && spec.trimColor) || color, svg: `<path d="M ${round(c.x - r * hw.width * 0.96)} ${round(y)} L ${round(c.x + reach * dir * forward)} ${round(y - r * 0.05)} Q ${round(c.x + reach * dir * forward * 1.04)} ${round(y + r * 0.12)} ${round(c.x - r * hw.width * 0.9)} ${round(y + r * 0.12)} Z"/>` });
    }
    if (hw.crest) {
      shapes.push({ fill: (spec && spec.trimColor) || color, svg: `<path d="M ${round(c.x - r * 0.1)} ${round(capTop - r * 0.02)} L ${round(c.x + r * 0.1)} ${round(capTop - r * 0.02)} L ${round(c.x + r * 0.06)} ${round(c.y - r * 0.3)} L ${round(c.x - r * 0.06)} ${round(c.y - r * 0.3)} Z"/>` });
    }
    // A cap sits on the skull, so all of it is in front of the head.
    return { shapes: [], front: shapes, coversHair: !!hw.coversHair };
  }

  return { GARMENTS, OVERLAYS, HEADWEAR, torsoPath, skirtPath, trimShapes, overlayShapes, headwearShapes };
});
