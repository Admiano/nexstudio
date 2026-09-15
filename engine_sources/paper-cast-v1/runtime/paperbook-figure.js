/**
 * NexStudio Paper Cast — paperbook figure skin
 *
 * The paperbook's art direction is flat gouache shapes on toned paper: no ink
 * outline, rounded limb masses that merge into the body, garment silhouettes
 * (wrapper, tunic, headwrap) carrying the pattern, and a soft contact shadow.
 * The cut-paper renderer's torn edges and ink seams read as a different book,
 * so this is a second skin over the same rig rather than a change to it.
 *
 * Same contract as the cut-paper renderer — `render(figure, options)` — plus
 * `renderRelation(relation, options)`, which composites the several bodies of
 * a relation into one spread illustration.
 */
(function (root, factory) {
  const isNode = typeof module === 'object' && module.exports;
  const deps = isNode
    ? { Rig: require('./paper-cast-rig.js'), Body: require('./cast-body.js'), Wardrobe: require('./cast-wardrobe.js'), Props: require('./cast-props.js') }
    : { Rig: root.NexPaperCastRig, Body: root.NexCastBody, Wardrobe: root.NexCastWardrobe, Props: root.NexCastProps };
  const api = factory(deps);
  if (isNode) module.exports = api;
  root.NexPaperbookFigure = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function ({ Rig, Body, Wardrobe, Props }) {
  const round = (n) => Math.round(Number(n) * 100) / 100;
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const PAPER = {
    page: '#efe7d8',
    ink: '#3a3028',
    shadow: '#7a6a58'
  };

  const SKIN = ['#f0cfa8', '#dda87c', '#c1895f', '#98603c', '#6d452c'];

  function mix(hex, target, amount) {
    const norm = (h) => {
      const s = String(h).replace('#', '');
      return s.length === 3 ? s.split('').map((c) => c + c).join('') : s;
    };
    const a = norm(hex);
    const b = norm(target);
    return `#${[0, 1, 2].map((i) => {
      const x = parseInt(a.slice(i * 2, i * 2 + 2), 16);
      const y = parseInt(b.slice(i * 2, i * 2 + 2), 16);
      return Math.round(x + (y - x) * amount).toString(16).padStart(2, '0');
    }).join('')}`;
  }

  const shade = (hex, depth, span) => (span ? mix(hex, '#2a211a', Math.max(0, Math.min(0.26, (0.5 - (depth + span) / (2 * span)) * 0.5))) : hex);

  /** Cloth patterns: the paperbook carries its identity in the wrapper, not the face. */
  const PATTERNS = {
    diamond: (id, fg, bg, s) => `<pattern id="${id}" width="${s}" height="${s}" patternUnits="userSpaceOnUse"><rect width="${s}" height="${s}" fill="${bg}"/><path d="M ${s / 2} 1 L ${s - 1} ${s / 2} L ${s / 2} ${s - 1} L 1 ${s / 2} Z" fill="none" stroke="${fg}" stroke-width="${round(s * 0.16)}"/></pattern>`,
    zigzag: (id, fg, bg, s) => `<pattern id="${id}" width="${s}" height="${s}" patternUnits="userSpaceOnUse"><rect width="${s}" height="${s}" fill="${bg}"/><path d="M 0 ${s * 0.75} L ${s / 2} ${s * 0.25} L ${s} ${s * 0.75}" fill="none" stroke="${fg}" stroke-width="${round(s * 0.16)}"/></pattern>`,
    dots: (id, fg, bg, s) => `<pattern id="${id}" width="${s}" height="${s}" patternUnits="userSpaceOnUse"><rect width="${s}" height="${s}" fill="${bg}"/><circle cx="${s / 2}" cy="${s / 2}" r="${round(s * 0.16)}" fill="${fg}"/></pattern>`,
    stripe: (id, fg, bg, s) => `<pattern id="${id}" width="${s}" height="${s}" patternUnits="userSpaceOnUse"><rect width="${s}" height="${s}" fill="${bg}"/><rect width="${round(s * 0.34)}" height="${s}" fill="${fg}"/></pattern>`
  };

  function resolveLook(look, proportion) {
    const l = look || {};
    const young = (proportion && proportion.age != null ? proportion.age : 30) < 5;
    // The garment chosen from the catalogue supplies the defaults — sleeve
    // length, hem, trim — so `{ garment: 'jacket' }` is a jacket rather than a
    // tunic that has to be dressed up field by field.
    const cut = Wardrobe.GARMENTS[l.top?.garment] || Wardrobe.GARMENTS.tunic;
    return {
      skin: l.skin || SKIN[2],
      hair: { color: l.hair?.color || '#241c17', style: l.hair?.style || (young ? 'tuft' : 'bun'), wrap: l.hair?.wrap || null, beard: l.hair?.beard || false },
      head: l.head ? { kind: l.head.kind || l.head, color: l.head.color, trimColor: l.head.trimColor } : null,
      over: l.over ? { kind: l.over.kind || l.over, color: l.over.color } : null,
      top: {
        color: l.top?.color || '#7d9cab',
        garment: Wardrobe.GARMENTS[l.top?.garment] ? l.top.garment : 'tunic',
        cut,
        trim: l.top?.trim || cut.trim,
        trimColor: l.top?.trimColor || mix(l.top?.color || '#7d9cab', '#241c17', 0.4),
        bandColor: l.top?.bandColor,
        badgeColor: l.top?.badgeColor,
        sleeve: l.top?.sleeve ?? cut.sleeve ?? 0.35,
        length: l.top?.length ?? cut.hem ?? 0.24,
        spread: l.top?.spread ?? cut.spread ?? 1
      },
      bottom: {
        color: l.bottom?.color || '#5d5445',
        garment: l.bottom?.garment || (young ? 'shorts' : 'trousers'),
        pattern: l.bottom?.pattern || null,
        patternColor: l.bottom?.patternColor || '#b4622f',
        patternScale: l.bottom?.patternScale ?? 0.06
      },
      shoes: { color: l.shoes?.color || '#3d342b', bare: l.shoes?.bare ?? young },
      ink: l.ink || PAPER.ink
    };
  }

  const limbMass = (a, b, w0, w1) => {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len;
    const ny = dx / len;
    const quad = [
      { x: a.x + nx * w0 * 0.5, y: a.y + ny * w0 * 0.5 },
      { x: b.x + nx * w1 * 0.5, y: b.y + ny * w1 * 0.5 },
      { x: b.x - nx * w1 * 0.5, y: b.y - ny * w1 * 0.5 },
      { x: a.x - nx * w0 * 0.5, y: a.y - ny * w0 * 0.5 }
    ];
    // Round caps at both ends: joints merge into one mass instead of showing
    // the notch that makes a figure read as assembled tubes.
    return `<path d="M ${quad.map((p) => `${round(p.x)} ${round(p.y)}`).join(' L ')} Z"/><circle cx="${round(a.x)}" cy="${round(a.y)}" r="${round(w0 * 0.5)}"/><circle cx="${round(b.x)}" cy="${round(b.y)}" r="${round(w1 * 0.5)}"/>`;
  };

  const piece = (fill, geometry, cls) => `<g class="${cls}" fill="${fill}">${geometry}</g>`;

  const topPath = (torso, look) => Wardrobe.torsoPath(torso, {
    spread: look.top.spread,
    waist: look.top.cut.waist,
    hem: look.top.length,
    flare: look.top.cut.flare
  });

  const wrapperPath = (torso, joints, length, flare) => Wardrobe.skirtPath(torso, joints, { length, flare });

  function hairShapes(head, look) {
    const r = head.radius;
    const c = head.center;
    const lateral = head.lateral;
    const out = [];
    if (look.hair.style === 'afro' || look.hair.style === 'coils') {
      const k = look.hair.style === 'afro' ? 1.42 : 1.2;
      out.push(`<ellipse cx="${round(c.x)}" cy="${round(c.y - r * 0.34)}" rx="${round(r * k)}" ry="${round(r * k * 0.92)}"/>`);
      return { fill: look.hair.color, shapes: out };
    }
    if (look.hair.style === 'shaved') {
      out.push(`<path d="M ${round(c.x - r * 0.98)} ${round(c.y - r * 0.2)} Q ${round(c.x)} ${round(c.y - r * 1.12)} ${round(c.x + r * 0.98)} ${round(c.y - r * 0.2)} Q ${round(c.x)} ${round(c.y - r * 0.66)} ${round(c.x - r * 0.98)} ${round(c.y - r * 0.2)} Z"/>`);
      return { fill: look.hair.color, shapes: out };
    }
    if (look.hair.wrap) {
      out.push(`<path d="M ${round(c.x - r * 1.02)} ${round(c.y - r * 0.18)} Q ${round(c.x)} ${round(c.y - r * 1.5)} ${round(c.x + r * 1.02)} ${round(c.y - r * 0.18)} Q ${round(c.x)} ${round(c.y - r * 0.5)} ${round(c.x - r * 1.02)} ${round(c.y - r * 0.18)} Z"/>`);
      return { fill: look.hair.wrap, shapes: out };
    }
    out.push(`<path d="M ${round(c.x - r * 1.0)} ${round(c.y - r * 0.1)} Q ${round(c.x - r * 1.05)} ${round(c.y - r * 1.25)} ${round(c.x)} ${round(c.y - r * 1.2)} Q ${round(c.x + r * 1.05)} ${round(c.y - r * 1.25)} ${round(c.x + r * 1.0)} ${round(c.y - r * 0.1)} Q ${round(c.x)} ${round(c.y - r * 0.62)} ${round(c.x - r * 1.0)} ${round(c.y - r * 0.1)} Z"/>`);
    if (look.hair.style === 'bun') {
      out.push(`<ellipse cx="${round(c.x - lateral * r * 0.5)}" cy="${round(c.y - r * 1.24)}" rx="${round(r * 0.44)}" ry="${round(r * 0.4)}"/>`);
    } else if (look.hair.style === 'tuft') {
      out.push(`<ellipse cx="${round(c.x - lateral * r * 0.2)}" cy="${round(c.y - r * 1.16)}" rx="${round(r * 0.2)}" ry="${round(r * 0.22)}"/>`);
    } else if (look.hair.style === 'long') {
      out.push(`<path d="M ${round(c.x - r * 0.98)} ${round(c.y - r * 0.3)} Q ${round(c.x - r * 1.3)} ${round(c.y + r * 1.3)} ${round(c.x - r * 0.5)} ${round(c.y + r * 1.25)} L ${round(c.x + r * 0.5)} ${round(c.y + r * 1.25)} Q ${round(c.x + r * 1.3)} ${round(c.y + r * 1.3)} ${round(c.x + r * 0.98)} ${round(c.y - r * 0.3)} Z"/>`);
    }
    return { fill: look.hair.color, shapes: out };
  }

  /** Drawn over the jaw rather than with the hair, which sits behind the head. */
  const beardShape = (head) => {
    const r = head.radius;
    const c = head.center;
    return `<path d="M ${round(c.x - r * 0.82)} ${round(c.y + r * 0.3)} Q ${round(c.x)} ${round(c.y + r * 1.5)} ${round(c.x + r * 0.82)} ${round(c.y + r * 0.3)} Q ${round(c.x)} ${round(c.y + r * 0.78)} ${round(c.x - r * 0.82)} ${round(c.y + r * 0.3)} Z"/>`;
  };

  /** Faces in this book are quiet: eyes, a mouth, nothing that fights the page. */
  function facePath(head, look) {
    const r = head.radius;
    const c = head.center;
    if (head.facing <= -0.3) return '';
    const lateral = head.lateral;
    const dir = lateral >= 0 ? 1 : -1;
    const open = Math.max(0.18, head.facing);
    const shift = lateral * r * 0.3;
    const eyeY = c.y - r * 0.05;
    const ink = mix(look.skin, '#1a120c', 0.82);
    const eye = (x, squash) => `<ellipse cx="${round(x)}" cy="${round(eyeY)}" rx="${round(r * 0.1 * squash)}" ry="${round(r * 0.12)}" fill="${ink}"/>`;
    const parts = [eye(c.x + shift + r * 0.3 * dir * open, 1)];
    if (Math.abs(lateral) < 0.82) parts.push(eye(c.x + shift - r * 0.3 * dir * open, Math.max(0.3, 1 - Math.abs(lateral))));
    parts.push(`<path d="M ${round(c.x + shift - r * 0.18 * open)} ${round(c.y + r * 0.42)} Q ${round(c.x + shift)} ${round(c.y + r * 0.56)} ${round(c.x + shift + r * 0.18 * open)} ${round(c.y + r * 0.42)}" fill="none" stroke="${ink}" stroke-width="${round(r * 0.07)}" stroke-linecap="round"/>`);
    return parts.join('');
  }

  /**
   * Collects one figure's shapes as depth-tagged layers. Layers rather than a
   * finished group, because two bodies in contact interleave: the child's leg
   * in front of the carrier's hip has to sort against the carrier's own parts,
   * not be stacked behind the whole body.
   */
  function collect(figure, opts, out) {
    const look = resolveLook(opts.look, figure.proportions);
    const id = String(opts.id || 'pb').replace(/[^a-z0-9]/gi, '');
    const height = figure.height;
    const span = Math.max(1, ...figure.parts.map((p) => Math.abs(p.depth)));
    const torso = figure.parts.find((p) => p.kind === 'torso');
    const headPart = figure.parts.find((p) => p.kind === 'head');

    const defs = out.defs;
    let bottomFill = look.bottom.color;
    if (look.bottom.pattern && PATTERNS[look.bottom.pattern]) {
      const pid = `pb-${look.bottom.pattern}-${id}`;
      defs.push(PATTERNS[look.bottom.pattern](pid, look.bottom.patternColor, look.bottom.color, round(height * look.bottom.patternScale)));
      bottomFill = `url(#${pid})`;
    }

    const legs = look.top.cut.legs || 'bare';
    const wrapped = look.bottom.garment === 'wrapper' || legs === 'skirt';
    const shortLegs = look.bottom.garment === 'shorts';
    const layers = out.layers;
    const emit = (depth, svg) => layers.push({ depth, svg });

    // Head sits with the torso: depth alone would let a swinging arm cross the
    // face on every three-quarter view.
    const ordered = figure.parts
      .map((p) => ({ part: p, depth: p.kind === 'head' ? (torso ? torso.depth + 0.5 : p.depth) : p.depth }))
      .sort((a, b) => a.depth - b.depth);

    for (const { part, depth } of ordered) {
      if (part.kind === 'torso') {
        emit(depth, piece(shade(look.top.color, part.depth, span), `<path d="${topPath(part, look)}"/>`, 'pb-top'));
        continue;
      }
      if (part.kind === 'head') {
        const r = part.radius;
        const c = part.center;
        const hair = hairShapes(part, look);
        const worn = Wardrobe.headwearShapes(part, look.head);
        emit(depth, piece(mix(look.skin, '#2a1c12', 0.16), limbMass({ x: c.x, y: c.y + r * 0.9 }, part.neck, r * 0.5, r * 0.6), 'pb-neck'));
        // Headwear that covers the hair replaces it: a hijab or a helmet with
        // a bun still poking out reads as a costume over a wig.
        if (!worn.coversHair) emit(depth, piece(hair.fill, hair.shapes.join(''), 'pb-hair'));
        for (const s of worn.shapes) emit(depth, piece(s.fill, s.svg, 'pb-headwear'));
        emit(depth, piece(look.skin, `<ellipse cx="${round(c.x)}" cy="${round(c.y)}" rx="${round(r * 0.94)}" ry="${round(r * 1.06)}"/>`, 'pb-head'));
        if (look.hair.beard) emit(depth, piece(look.hair.color, beardShape(part), 'pb-beard'));
        emit(depth, `<g class="pb-face">${facePath(part, look)}</g>`);
        for (const s of worn.front) emit(depth, piece(s.fill, s.svg, 'pb-headwear'));
        continue;
      }
      const isLeg = /thigh|shin/.test(part.id);
      const isFoot = part.kind === 'foot';
      const isHand = part.kind === 'hand';
      const isUpper = /upper-arm/.test(part.id);
      const isFore = /fore-arm/.test(part.id);
      const sleeved = isUpper ? look.top.sleeve > 0.05 : isFore ? look.top.sleeve > 0.85 : false;
      let fill = look.skin;
      if (isFoot) fill = look.shoes.bare ? look.skin : look.shoes.color;
      else if (isLeg) fill = legs === 'fill' ? look.top.color : wrapped ? look.skin : (shortLegs && /shin/.test(part.id) ? look.skin : bottomFill);
      else if (sleeved) fill = look.top.color;
      if (isHand) fill = look.skin;

      const w = isFoot ? 1.1 : 1;
      const solid = fill.startsWith('url') ? fill : shade(fill, part.depth, span);
      emit(depth, piece(solid, limbMass(part.a, part.b, part.widthFrom * w, part.widthTo * w), `pb-${part.kind}`));

      if (isUpper && look.top.sleeve > 0.05 && look.top.sleeve < 1) {
        const end = { x: part.a.x + (part.b.x - part.a.x) * look.top.sleeve, y: part.a.y + (part.b.y - part.a.y) * look.top.sleeve };
        emit(depth, piece(shade(look.top.color, part.depth, span), limbMass(part.a, end, part.widthFrom * 1.18, part.widthFrom * 1.02), 'pb-sleeve'));
      }
    }

    if (wrapped && torso) {
      // In front of both legs, which it covers, but still behind the arms.
      const legDepth = Math.max(...figure.parts.filter((p) => /thigh|shin|foot/.test(p.id)).map((p) => p.depth), torso.depth);
      const skirtFill = legs === 'skirt' ? shade(look.top.color, torso.depth, span) : bottomFill;
      const length = legs === 'skirt' ? Math.min(1, look.top.length) : (look.bottom.length ?? 0.92);
      emit(legDepth + 0.01, piece(skirtFill, `<path d="${wrapperPath(torso, figure.joints, length, look.top.cut.flare)}"/>`, 'pb-wrapper'));
    }

    if (torso) {
      // Trim and overlays ride on the front of the body, ahead of the garment
      // but behind whichever arm crosses it.
      const face = torso.depth + 0.02;
      for (const t of Wardrobe.trimShapes(torso, look.top)) emit(face, piece(t.fill, t.svg, 'pb-trim'));
      if (look.over) {
        for (const o of Wardrobe.overlayShapes(torso, figure.joints, look.over)) emit(face + 0.01, piece(o.fill, o.svg, 'pb-overlay'));
      }
    }

    const shadowX = (figure.joints.leftToe.x + figure.joints.rightToe.x) / 2;
    emit(-Infinity, `<ellipse class="pb-shadow" cx="${round(shadowX)}" cy="${round(figure.ground)}" rx="${round(height * 0.1)}" ry="${round(height * 0.018)}" fill="${PAPER.shadow}" opacity="0.22"/>`);

    // Held props are drawn from the hands the solver produced, in front of
    // the body: a bag behind the arm holding it is the floating-rice-bag bug.
    const held = (opts.props || []).map((p) => (typeof p === 'string' ? { id: p } : p)).filter((p) => p && p.id);
    let reach = null;
    if (held.length) {
      const front = Math.max(...figure.parts.map((p) => p.depth)) + 1;
      for (const p of held) {
        for (const s of Props.shapes(p.id, figure, { side: p.side, color: p.color, mix })) {
          emit(p.behind ? -span : front, piece(s.fill, s.svg, 'pb-prop'));
        }
        const box = Props.extent(p.id, figure, { side: p.side });
        if (box) {
          reach = reach ? { minX: Math.min(reach.minX, box.minX), maxX: Math.max(reach.maxX, box.maxX), minY: Math.min(reach.minY, box.minY), maxY: Math.max(reach.maxY, box.maxY) } : box;
        }
      }
    }

    const pad = height * 0.05;
    const b = reach
      ? { minX: Math.min(figure.bounds.minX, reach.minX), maxX: Math.max(figure.bounds.maxX, reach.maxX), minY: Math.min(figure.bounds.minY, reach.minY), maxY: Math.max(figure.bounds.maxY, reach.maxY) }
      : figure.bounds;
    out.bounds = { minX: b.minX - pad, maxX: b.maxX + pad, minY: b.minY - pad, maxY: b.maxY + pad };
    out.figure = figure;
    return out;
  }

  const stableSort = (layers) => layers
    .map((layer, index) => ({ ...layer, index }))
    .sort((a, b) => (a.depth - b.depth) || (a.index - b.index))
    .map((layer) => layer.svg)
    .join('');

  /**
   * @param {object} figure rig figure from `Rig.build`
   * @returns {{svg:string, group:string, defs:string, viewBox:string, bounds:object}}
   */
  function render(figure, options) {
    const opts = options || {};
    const collected = collect(figure, opts, { layers: [], defs: [] });
    const bounds = collected.bounds;
    const width = bounds.maxX - bounds.minX;
    const boxHeight = bounds.maxY - bounds.minY;
    const viewBox = `${round(bounds.minX)} ${round(bounds.minY)} ${round(width)} ${round(boxHeight)}`;
    const group = `<g class="pb-figure" data-view-axis="${esc(figure.view.axis)}">${stableSort(collected.layers)}</g>`;
    const defsBlock = collected.defs.join('');
    const svg = `<svg class="nex-paperbook-figure" xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" role="img" aria-label="${esc(opts.accessibilityLabel || 'Paperbook character')}"><defs>${defsBlock}</defs>${group}</svg>`;
    return { svg, group, defs: defsBlock, viewBox, width, height: boxHeight, bounds, ground: figure.ground, figure };
  }

  function renderPose(options) {
    return render(Rig.build(options), options);
  }

  /**
   * Composites the bodies of a relation into one illustration: each participant
   * is built at its own height and placed on the shared ground plane, so a
   * carried child is drawn small and in contact rather than pasted alongside.
   */
  function renderRelation(relation, options) {
    const opts = options || {};
    const unit = relation.unit || 1000;
    const looks = opts.looks || {};
    const layers = [];
    const defs = [];
    let box = null;

    for (const p of relation.participants) {
      const figure = Rig.build({ proportion: p.proportion, height: p.height, pose: p.pose, view: p.yaw });
      const props = (opts.props && (opts.props[p.id] || opts.props[p.role])) || p.props;
      const collected = collect(figure, { look: looks[p.id] || looks[p.role] || opts.look, id: p.id, props }, { layers: [], defs });
      const dx = p.origin.x * unit;
      const dy = -p.origin.y * unit;
      // Each body's parts keep their own depth, offset by where the body
      // stands, so the two figures interleave: a leg wrapped round the
      // carrier's hip is drawn in front of it, not behind the whole body.
      const bodyDepth = (p.origin.z || 0) * unit;
      for (const layer of collected.layers) {
        layers.push({
          depth: layer.depth === -Infinity ? -Infinity : layer.depth + bodyDepth,
          svg: `<g class="pb-body" data-id="${esc(p.id)}" transform="translate(${round(dx)} ${round(dy)})">${layer.svg}</g>`
        });
      }
      const b = collected.bounds;
      const moved = { minX: b.minX + dx, maxX: b.maxX + dx, minY: b.minY + dy, maxY: b.maxY + dy };
      box = box
        ? { minX: Math.min(box.minX, moved.minX), maxX: Math.max(box.maxX, moved.maxX), minY: Math.min(box.minY, moved.minY), maxY: Math.max(box.maxY, moved.maxY) }
        : moved;
    }

    const width = box.maxX - box.minX;
    const height = box.maxY - box.minY;
    const viewBox = `${round(box.minX)} ${round(box.minY)} ${round(width)} ${round(height)}`;
    const group = `<g class="pb-relation" data-relation="${esc(relation.relation)}">${stableSort(layers)}</g>`;
    const background = opts.background === false ? '' : `<rect x="${round(box.minX)}" y="${round(box.minY)}" width="${round(width)}" height="${round(height)}" fill="${opts.page || PAPER.page}"/>`;
    const svg = `<svg class="nex-paperbook-scene" xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" role="img" aria-label="${esc(opts.accessibilityLabel || relation.relation)}"><defs>${defs.join('')}</defs>${background}${group}</svg>`;
    return { svg, group, defs: defs.join(''), viewBox, width, height, bounds: box };
  }

  return { render, renderPose, renderRelation, resolveLook, PATTERNS, PAPER, SKIN, mix, Body };
});
