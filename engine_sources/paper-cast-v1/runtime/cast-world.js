/**
 * NexStudio Paper Cast — world anchors
 *
 * Paper Cast can already solve a body to a point. What it could not do was
 * find the point: nothing told it how high this chair's seat is, where the
 * table's near edge runs, or which way a figure has to stand to use the shelf.
 * Guessing those is how characters end up hovering above stools and reaching
 * through counters.
 *
 * So the environment states them. Paperbook knows the world; this is the shape
 * of what it hands over, and the same shape an author can write by hand:
 *
 *   const scene = World.scene({ features: [
 *     { id: 'stool', kind: 'stool', at: { x: 0.1 }, facing: 0 },
 *     { id: 'table', kind: 'table', at: { x: 0, z: 0.45 }, facing: 180 }
 *   ]});
 *   scene.anchor('table.edge')     // -> { x, y, z } in world units
 *   scene.approach('table')        // -> where to stand, and which way to face
 *
 * World units are fractions of the primary figure's height, ground plane at
 * y = 0, +x to the right, +z toward the viewer — the frame `cast-relation.js`
 * stages in, so an anchor can be passed straight to a contact goal.
 *
 * Default heights are the real ones expressed against a 1.7 m adult: a 0.45 m
 * seat is 0.26, a 0.74 m table top is 0.43, a 0.95 m counter is 0.55.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastWorld = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const RAD = Math.PI / 180;
  const round = (n) => Math.round(Number(n) * 100) / 100;
  const num = (v, fallback) => (Number.isFinite(Number(v)) ? Number(v) : fallback);

  /**
   * What each kind of thing offers a body. `sit` and `surface` are the two
   * behaviours that matter to the solver; the rest is drawing and reach.
   */
  const FEATURES = {
    chair: { role: 'sit', seat: 0.26, depth: 0.17, width: 0.2, back: 0.51, label: 'a chair' },
    stool: { role: 'sit', seat: 0.28, depth: 0.15, width: 0.16, back: null, label: 'a stool' },
    bench: { role: 'sit', seat: 0.25, depth: 0.18, width: 0.52, back: null, label: 'a bench' },
    step: { role: 'sit', seat: 0.13, depth: 0.2, width: 0.6, back: null, label: 'a step' },
    table: { role: 'surface', top: 0.43, depth: 0.32, width: 0.64, label: 'a table' },
    desk: { role: 'surface', top: 0.42, depth: 0.28, width: 0.52, label: 'a desk' },
    counter: { role: 'surface', top: 0.55, depth: 0.24, width: 0.72, label: 'a counter' },
    shelf: { role: 'wall', top: 0.98, bottom: 0.2, shelves: 3, reach: 0.72, depth: 0.14, width: 0.5, label: 'a shelf' },
    crate: { role: 'surface', top: 0.18, depth: 0.18, width: 0.2, label: 'a crate' },
    board: { role: 'wall', top: 1.05, bottom: 0.46, depth: 0.02, width: 0.72, label: 'a board' },
    door: { role: 'wall', top: 1.18, bottom: 0, depth: 0.03, width: 0.44, handle: 0.6, label: 'a door' }
  };

  const rotateY = (p, deg) => {
    const c = Math.cos(deg * RAD);
    const s = Math.sin(deg * RAD);
    return { x: p.x * c + p.z * s, y: p.y, z: -p.x * s + p.z * c };
  };

  /**
   * Normalises one piece of the world. `facing` is the direction the thing
   * presents to a user, in degrees, 0 meaning it faces the viewer: a table
   * facing 180 is approached from the viewer's side of it.
   */
  function feature(spec) {
    const s = spec || {};
    const kind = FEATURES[s.kind] ? s.kind : 'table';
    const base = FEATURES[kind];
    const at = { x: num(s.at && s.at.x, num(s.x, 0)), y: num(s.at && s.at.y, num(s.y, 0)), z: num(s.at && s.at.z, num(s.z, 0)) };
    const metrics = {
      role: base.role,
      seat: num(s.seat, base.seat),
      top: num(s.top, base.top),
      bottom: num(s.bottom, base.bottom),
      back: s.back === null ? null : num(s.back, base.back),
      handle: num(s.handle, base.handle),
      shelves: num(s.shelves, base.shelves),
      reach: num(s.reach, base.reach),
      depth: num(s.depth, base.depth),
      width: num(s.width, base.width)
    };
    const out = {
      id: String(s.id || kind),
      kind,
      label: s.label || base.label,
      facing: num(s.facing, 0),
      at,
      metrics
    };
    out.anchors = anchorsOf(out);
    return out;
  }

  /** A point on the feature, in world units, with its facing already applied. */
  const local = (f, point) => {
    const turned = rotateY({ x: point.x, y: 0, z: point.z }, f.facing);
    return { x: round(f.at.x + turned.x), y: round(f.at.y + point.y), z: round(f.at.z + turned.z) };
  };

  function anchorsOf(f) {
    const m = f.metrics;
    const half = m.depth / 2;
    const side = m.width / 2;
    const out = {};
    if (m.role === 'sit') {
      // The seat point is where the pelvis lands: back from the front edge,
      // because nobody perches on the lip of a chair by default.
      out.seat = local(f, { x: 0, y: m.seat, z: -half * 0.25 });
      out.seatFront = local(f, { x: 0, y: m.seat, z: half });
      out.feet = local(f, { x: 0, y: 0, z: half + 0.1 });
      out.armLeft = local(f, { x: -side, y: m.seat + 0.07, z: 0 });
      out.armRight = local(f, { x: side, y: m.seat + 0.07, z: 0 });
      if (m.back) out.back = local(f, { x: 0, y: m.back, z: -half });
    } else if (m.role === 'surface') {
      // `edge` is the near lip — the thing a leaning forearm or a set-down
      // object actually meets — and `top` is the middle of the surface.
      out.edge = local(f, { x: 0, y: m.top, z: half });
      out.top = local(f, { x: 0, y: m.top, z: 0 });
      out.far = local(f, { x: 0, y: m.top, z: -half });
      out.left = local(f, { x: -side * 0.6, y: m.top, z: half * 0.4 });
      out.right = local(f, { x: side * 0.6, y: m.top, z: half * 0.4 });
      out.under = local(f, { x: 0, y: 0, z: half * 0.4 });
    } else {
      out.face = local(f, { x: 0, y: (m.top + m.bottom) / 2, z: half });
      out.top = local(f, { x: 0, y: m.top, z: half });
      out.bottom = local(f, { x: 0, y: m.bottom, z: half });
      out.left = local(f, { x: -side * 0.5, y: (m.top + m.bottom) / 2, z: half });
      out.right = local(f, { x: side * 0.5, y: (m.top + m.bottom) / 2, z: half });
      // The height a standing body actually takes something from, as opposed
      // to the top of the unit, which may be over their head.
      if (Number.isFinite(m.reach)) out.reach = local(f, { x: side * 0.25, y: m.reach, z: half });
      if (Number.isFinite(m.handle)) out.handle = local(f, { x: side * 0.7, y: m.handle, z: half });
    }
    out.centre = local(f, { x: 0, y: 0, z: 0 });
    return out;
  }

  const anchor = (f, name) => {
    const set = (f && f.anchors) || {};
    return set[name] || set[Object.keys(set)[0]] || null;
  };

  /**
   * Where a body stands to use this thing, and which way it turns to do it.
   * Staging is part of grounding: a figure solved to the far edge of a table
   * while standing behind it is reaching through the furniture.
   */
  function approach(f, spec) {
    const s = spec || {};
    const gap = num(s.gap, f.metrics.role === 'sit' ? f.metrics.depth * 0.5 + 0.02 : f.metrics.depth * 0.5 + 0.12);
    const out = rotateY({ x: num(s.offset, 0), y: 0, z: gap }, f.facing);
    return {
      at: { x: round(f.at.x + out.x), y: 0, z: round(f.at.z + out.z) },
      // Turn to look back at the thing being used.
      yaw: ((f.facing + 180) % 360 + 540) % 360 - 180
    };
  }

  /** Ground is not always flat: a slope answers "how high is the floor here". */
  function groundPlane(spec) {
    const s = spec || {};
    const slope = num(s.slope, 0);
    const y0 = num(s.y, 0);
    const pivot = num(s.at, 0);
    return { slope, y: y0, at: pivot, height: (x) => round(y0 + Math.tan(slope * RAD) * (num(x, 0) - pivot)) };
  }

  /**
   * A staged world: features by id, one ground plane, and dotted-path anchor
   * lookup so a relation can be written against `'table.edge'` rather than
   * against coordinates that drift when the furniture moves.
   */
  function scene(spec) {
    const s = spec || {};
    const features = (s.features || []).map(feature);
    const byId = new Map(features.map((f) => [f.id, f]));
    const ground = groundPlane(s.ground);
    return {
      unit: num(s.unit, 1000),
      ground,
      features,
      get: (id) => byId.get(String(id)) || null,
      anchor(ref) {
        if (ref && typeof ref === 'object') return ref.x != null ? ref : null;
        const [id, name] = String(ref || '').split('.');
        const f = byId.get(id);
        return f ? anchor(f, name) : null;
      },
      approach(id, options) {
        const f = byId.get(String(id));
        return f ? approach(f, options) : null;
      }
    };
  }

  /**
   * Flat paperbook shapes for a feature. Paperbook draws the real environment;
   * this exists so a contact proof can show what the body is sitting on or
   * leaning against instead of asking the reader to imagine it.
   */
  function shapes(f, unit, options) {
    const o = options || {};
    const u = num(unit, 1000);
    const tone = o.color || '#c2ad8c';
    const dark = o.shadeColor || '#a48f6f';
    const shadowTone = o.shadowColor || '#7a6a58';
    const m = f.metrics;
    const px = (v) => round(v * u);
    // Same flat mapping the figures use — x across, y up from the ground, and
    // z carried as draw order rather than perspective. A feature drawn with
    // its own projection would not line up with the hand solved onto it.
    const x = f.at.x * u;
    const halfW = (m.width / 2) * u;
    const out = [];
    const slab = (cx, top, w, h) => `<rect x="${round(cx - w / 2)}" y="${round(top)}" width="${round(w)}" height="${round(Math.max(1, h))}" rx="${round(u * 0.006)}"/>`;
    const grounded = (w) => ({ fill: shadowTone, svg: `<ellipse cx="${round(x)}" cy="0" rx="${round(w)}" ry="${round(u * 0.016)}" opacity="0.18"/>` });
    const edge = (cx, top, w) => ({ fill: dark, svg: slab(cx, top, w, u * 0.008) });

    if (m.role === 'sit') {
      const seatY = -px(m.seat);
      const legW = u * 0.024;
      out.push(grounded(halfW * 1.1));
      out.push({ fill: dark, svg: `${slab(x - halfW * 0.78, seatY, legW, px(m.seat))}${slab(x + halfW * 0.78, seatY, legW, px(m.seat))}` });
      if (m.back) {
        // The back is at the back of the chair, so it carries the depth that
        // puts it behind the sitter rather than across their shoulders.
        out.push({ dz: -m.depth, fill: dark, svg: slab(x, -px(m.back), halfW * 1.7, px(m.back - m.seat) * 0.9) });
        out.push({ dz: -m.depth, fill: tone, svg: slab(x, -px(m.back), halfW * 1.62, px(m.back - m.seat) * 0.86) });
      }
      // The seat itself is in front of the sitter's hips: the front edge is
      // what hides the back of their thighs.
      out.push({ dz: m.depth / 2, fill: tone, svg: slab(x, seatY, halfW * 2, u * 0.03) });
      out.push({ dz: m.depth / 2, ...edge(x, seatY + u * 0.03, halfW * 2) });
    } else if (m.role === 'surface') {
      const topY = -px(m.top);
      const legW = u * 0.028;
      out.push(grounded(halfW * 1.1));
      out.push({ fill: dark, svg: `${slab(x - halfW * 0.84, topY, legW, px(m.top))}${slab(x + halfW * 0.84, topY, legW, px(m.top))}` });
      // An apron under the top gives the slab thickness; a single line reads
      // as a plank floating at hip height.
      out.push({ dz: m.depth / 2, fill: dark, svg: slab(x, topY + u * 0.03, halfW * 1.9, u * 0.03) });
      out.push({ dz: m.depth / 2, fill: tone, svg: slab(x, topY, halfW * 2, u * 0.032) });
    } else {
      out.push(grounded(halfW));
      out.push({ fill: dark, svg: slab(x, -px(m.top), halfW * 2.04, px(m.top - m.bottom)) });
      out.push({ fill: tone, svg: slab(x, -px(m.top), halfW * 2, px(m.top - m.bottom) * 0.98) });
      if (Number.isFinite(m.shelves)) {
        for (let i = 1; i <= m.shelves; i += 1) {
          const y = -px(m.bottom + (m.top - m.bottom) * (i / (m.shelves + 1)));
          out.push(edge(x, y, halfW * 2));
        }
      }
      if (Number.isFinite(m.handle)) out.push({ fill: dark, svg: `<circle cx="${round(x + halfW * 0.7)}" cy="${round(-px(m.handle))}" r="${round(u * 0.014)}"/>` });
    }
    return out;
  }

  /** The box a drawn feature occupies, in the same pixel space as `shapes`. */
  function extent(f, unit) {
    const u = num(unit, 1000);
    const m = f.metrics;
    const top = m.role === 'sit' ? (m.back || m.seat) : m.top;
    const half = (m.width / 2) * u * 1.05;
    return { minX: f.at.x * u - half, maxX: f.at.x * u + half, minY: -top * u, maxY: u * 0.02 };
  }

  return { FEATURES, feature, anchor, anchorsOf, approach, scene, groundPlane, shapes, extent };
});
