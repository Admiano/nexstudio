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
    vest: { hem: 0.26, spread: 1.04, waist: 1, legs: 'bare', sleeve: 0, trim: ['band'] }
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
   * The clothed torso outline: shoulders, a waist the body's mass actually
   * moves, and a hem. One path serves every garment; the catalogue only
   * changes how wide the waist is, how far the hem falls and how it flares.
   */
  function torsoPath(torso, spec) {
    const s = spec || {};
    const cx = (torso.shoulderLeft.x + torso.shoulderRight.x) / 2;
    const run = torso.pelvis.y - torso.chest.y || 1;
    const spread = s.spread ?? 1;
    const waistK = s.waist ?? 1;
    const hem = (s.hem ?? 0.24) * run;
    const grow = (p, k) => ({ x: cx + (p.x - cx) * k, y: p.y });
    const a = grow(torso.shoulderLeft, spread);
    const b = grow(torso.shoulderRight, spread);
    const waistHalf = Math.abs((torso.waistRight ?? torso.hipRight).x - cx) * waistK;
    const waistY = (torso.chest.y + torso.pelvis.y) / 2 + run * 0.12;
    const hipHalf = Math.abs(torso.hipRight.x - cx);
    // The hem follows the hips, not the waist: letting a heavy waist set the
    // hem turns every garment into a bell that swallows the arms.
    const hemHalf = Math.max(hipHalf * 1.04, waistHalf * 0.84) * (s.flare ?? 1);
    const hemY = torso.hipRight.y + hem;
    return `M ${pt(a)} Q ${round(cx)} ${round(a.y - run * 0.16)} ${pt(b)} `
      + `C ${round(cx + waistHalf)} ${round(waistY)} ${round(cx + hemHalf)} ${round(hemY - hem * 0.55)} ${round(cx + hemHalf)} ${round(hemY)} `
      + `Q ${round(cx)} ${round(hemY + hem * 0.35)} ${round(cx - hemHalf)} ${round(hemY)} `
      + `C ${round(cx - hemHalf)} ${round(hemY - hem * 0.55)} ${round(cx - waistHalf)} ${round(waistY)} ${pt(a)} Z`;
  }

  /** Cloth from the hips down: wrapper, coat skirt, kaftan, dress. */
  function skirtPath(torso, joints, spec) {
    const s = spec || {};
    const hl = torso.hipLeft;
    const hr = torso.hipRight;
    const ankle = Math.max(joints.leftAnkle.y, joints.rightAnkle.y);
    const top = (hl.y + hr.y) / 2;
    const hemY = top + (ankle - top) * (s.length ?? 0.92);
    const half = Math.abs(hr.x - hl.x) * 0.5;
    const cx = (hl.x + hr.x) / 2;
    const flare = half * (s.flare ?? 1.5);
    return `M ${round(cx - half * 1.05)} ${round(top - half * 0.15)} L ${round(cx + half * 1.05)} ${round(top - half * 0.15)} `
      + `L ${round(cx + flare)} ${round(hemY)} Q ${round(cx)} ${round(hemY + half * 0.35)} ${round(cx - flare)} ${round(hemY)} Z`;
  }

  /**
   * Trim: collars, plackets, belts and hi-vis bands. Small marks, but they are
   * what separates a uniform from a shirt in a flat illustration.
   */
  function trimShapes(torso, spec) {
    const s = spec || {};
    const kinds = s.trim || [];
    const cx = (torso.shoulderLeft.x + torso.shoulderRight.x) / 2;
    const run = torso.pelvis.y - torso.chest.y || 1;
    const shoulderY = (torso.shoulderLeft.y + torso.shoulderRight.y) / 2;
    const half = Math.abs(torso.shoulderRight.x - cx);
    const out = [];
    const ink = s.trimColor;

    if (kinds.includes('collar')) {
      out.push({ fill: ink, svg: `<path d="M ${round(cx - half * 0.34)} ${round(shoulderY)} L ${round(cx)} ${round(shoulderY + run * 0.2)} L ${round(cx + half * 0.34)} ${round(shoulderY)} Q ${round(cx)} ${round(shoulderY + run * 0.07)} ${round(cx - half * 0.34)} ${round(shoulderY)} Z"/>` });
    }
    if (kinds.includes('lapel')) {
      out.push({ fill: ink, svg: `<path d="M ${round(cx - half * 0.42)} ${round(shoulderY)} L ${round(cx)} ${round(shoulderY + run * 0.34)} L ${round(cx + half * 0.42)} ${round(shoulderY)} L ${round(cx + half * 0.16)} ${round(shoulderY + run * 0.06)} L ${round(cx)} ${round(shoulderY + run * 0.2)} L ${round(cx - half * 0.16)} ${round(shoulderY + run * 0.06)} Z"/>` });
    }
    if (kinds.includes('placket')) {
      const y0 = shoulderY + run * 0.24;
      const y1 = torso.pelvis.y + run * 0.1;
      const r = run * 0.035;
      const buttons = [0.2, 0.5, 0.8].map((t) => `<circle cx="${round(cx)}" cy="${round(y0 + (y1 - y0) * t)}" r="${round(r)}"/>`).join('');
      out.push({ fill: ink, svg: buttons });
    }
    if (kinds.includes('belt')) {
      const y = torso.pelvis.y - run * 0.04;
      const w = Math.abs(torso.hipRight.x - torso.hipLeft.x) * 1.12;
      out.push({ fill: ink, svg: `<rect x="${round(cx - w / 2)}" y="${round(y)}" width="${round(w)}" height="${round(run * 0.1)}" rx="${round(run * 0.03)}"/>` });
    }
    if (kinds.includes('band')) {
      const y = torso.chest.y + run * 0.42;
      const w = half * 2 * 0.98;
      out.push({ fill: s.bandColor || '#f2d64b', svg: `<rect x="${round(cx - w / 2)}" y="${round(y)}" width="${round(w)}" height="${round(run * 0.11)}"/>` });
    }
    if (kinds.includes('badge')) {
      const x = cx + half * 0.45;
      const y = torso.chest.y + run * 0.18;
      const r = run * 0.07;
      out.push({ fill: s.badgeColor || '#d8b24a', svg: `<circle cx="${round(x)}" cy="${round(y)}" r="${round(r)}"/>` });
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
