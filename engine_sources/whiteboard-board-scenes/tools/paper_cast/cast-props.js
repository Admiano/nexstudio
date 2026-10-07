/**
 * NexStudio Paper Cast — held props
 *
 * A prop is two things that have to agree: where the hands go (body-local
 * goals the contact solver can reach) and what gets drawn (paper shapes hung
 * off the hands the solver actually produced). Keeping them in one entry is
 * what stops the oar-over-there / hands-over-here failure that made the
 * Makoko book's rice bag float over its carrier.
 *
 * Grips are pelvis-relative fractions of figure height, +y up, +z forward,
 * +x to the figure's right — the same frame `cast-contact.js` solves in.
 * Shapes are drawn in the rig's pixel space from `figure.joints`.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastProps = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const round = (n) => Math.round(Number(n) * 100) / 100;
  const mirror = (p) => ({ x: -p.x, y: p.y, z: p.z });

  /**
   * Named ways of holding something. `hands` is written for a right-handed
   * hold; asking for the left mirrors it, so every prop works on either side.
   */
  const HOLDS = {
    'hand-down': { hands: { right: { x: 0.17, y: -0.14, z: 0.06 } }, torso: false },
    'both-hands-down': { hands: { right: { x: 0.17, y: -0.14, z: 0.06 }, left: { x: -0.17, y: -0.14, z: 0.06 } }, torso: false },
    'front-cradle': { hands: { right: { x: 0.13, y: 0.02, z: 0.22 }, left: { x: -0.13, y: 0.02, z: 0.22 } }, torso: true },
    'hip-carry': { hands: { right: { x: 0.2, y: 0.02, z: 0.1 } }, torso: false },
    'tray-up': { hands: { right: { x: 0.19, y: 0.19, z: 0.13 } }, torso: false },
    'serve-forward': { hands: { right: { x: 0.14, y: 0.12, z: 0.25 } }, torso: true },
    // Proven by the rowing spread: both grips inside the reach envelope of a
    // stooping body, the far hand low and forward so the shaft runs diagonally.
    'two-hand-shaft': { hands: { right: { x: 0.07, y: 0.09, z: 0.3 }, left: { x: -0.03, y: 0.13, z: 0.2 } }, torso: true },
    'shoulder-shaft': { hands: { right: { x: 0.13, y: 0.24, z: 0.08 } }, torso: false }
  };

  const bag = (ctx, w, h, colour) => {
    const p = ctx.hand;
    const top = p.y + ctx.u * 0.01;
    const half = ctx.u * w * 0.5;
    const bottom = top + ctx.u * h;
    return [
      { fill: ctx.mix(colour, '#241f1c', 0.25), svg: `<path d="M ${round(p.x - half * 0.5)} ${round(top)} Q ${round(p.x)} ${round(top - ctx.u * 0.035)} ${round(p.x + half * 0.5)} ${round(top)}" fill="none" stroke="${ctx.mix(colour, '#241f1c', 0.35)}" stroke-width="${round(ctx.u * 0.012)}"/>` },
      { fill: colour, svg: `<path d="M ${round(p.x - half)} ${round(top)} L ${round(p.x + half)} ${round(top)} L ${round(p.x + half * 0.92)} ${round(bottom)} Q ${round(p.x)} ${round(bottom + ctx.u * 0.014)} ${round(p.x - half * 0.92)} ${round(bottom)} Z"/>` }
    ];
  };

  /** A long tool: shaft through both grips, working end past the far hand. */
  const shaft = (ctx, colour, head) => {
    const a = ctx.hands.left || ctx.hands.right;
    const b = ctx.hands.right || ctx.hands.left;
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    const ux = dx / len;
    const uy = dy / len;
    const back = { x: a.x - ux * ctx.u * 0.06, y: a.y - uy * ctx.u * 0.06 };
    const tip = { x: b.x + ux * ctx.u * (ctx.reach ?? 0.3), y: b.y + uy * ctx.u * (ctx.reach ?? 0.3) };
    const out = [{ fill: colour, svg: `<line x1="${round(back.x)}" y1="${round(back.y)}" x2="${round(tip.x)}" y2="${round(tip.y)}" stroke="${colour}" stroke-width="${round(ctx.u * 0.016)}" stroke-linecap="round"/>` }];
    if (head) out.push(...head(ctx, tip, { x: ux, y: uy }));
    return out;
  };

  const PROPS = {
    'grocery-bag': {
      hold: 'hand-down',
      label: 'a bag of groceries',
      extent: 0.22,
      draw: (ctx) => {
        const body = bag(ctx, 0.11, 0.15, ctx.color || '#b8895a');
        const p = ctx.hand;
        const top = p.y + ctx.u * 0.01;
        return [
          ...body,
          // Greens over the rim: what makes a paper rectangle read as shopping.
          { fill: '#6d8a52', svg: `<ellipse cx="${round(p.x - ctx.u * 0.018)}" cy="${round(top - ctx.u * 0.012)}" rx="${round(ctx.u * 0.022)}" ry="${round(ctx.u * 0.016)}"/><ellipse cx="${round(p.x + ctx.u * 0.02)}" cy="${round(top - ctx.u * 0.02)}" rx="${round(ctx.u * 0.018)}" ry="${round(ctx.u * 0.014)}"/>` }
        ];
      }
    },
    'shopping-bags': { hold: 'both-hands-down', label: 'shopping bags', extent: 0.22, draw: (ctx) => [
      ...bag({ ...ctx, hand: ctx.hands.left }, 0.1, 0.13, ctx.color || '#b8895a'),
      ...bag({ ...ctx, hand: ctx.hands.right }, 0.11, 0.15, ctx.mix(ctx.color || '#b8895a', '#f4efe4', 0.25))
    ] },
    basket: {
      hold: 'front-cradle',
      label: 'a basket',
      extent: 0.24,
      draw: (ctx) => {
        const l = ctx.hands.left;
        const r = ctx.hands.right;
        const cx = (l.x + r.x) / 2;
        const top = Math.min(l.y, r.y) - ctx.u * 0.02;
        const half = Math.max(Math.abs(r.x - l.x) / 2, ctx.u * 0.09);
        const h = ctx.u * 0.13;
        const colour = ctx.color || '#c79c5e';
        return [
          { fill: colour, svg: `<path d="M ${round(cx - half)} ${round(top)} L ${round(cx + half)} ${round(top)} L ${round(cx + half * 0.82)} ${round(top + h)} Q ${round(cx)} ${round(top + h + ctx.u * 0.016)} ${round(cx - half * 0.82)} ${round(top + h)} Z"/>` },
          { fill: ctx.mix(colour, '#241f1c', 0.3), svg: `<rect x="${round(cx - half)}" y="${round(top - ctx.u * 0.012)}" width="${round(half * 2)}" height="${round(ctx.u * 0.018)}" rx="${round(ctx.u * 0.008)}"/>` }
        ];
      }
    },
    crate: {
      hold: 'front-cradle',
      label: 'a crate',
      extent: 0.26,
      draw: (ctx) => {
        const l = ctx.hands.left;
        const r = ctx.hands.right;
        const cx = (l.x + r.x) / 2;
        const top = Math.min(l.y, r.y) - ctx.u * 0.04;
        const half = Math.max(Math.abs(r.x - l.x) / 2, ctx.u * 0.1);
        const colour = ctx.color || '#a9763f';
        return [
          { fill: colour, svg: `<rect x="${round(cx - half)}" y="${round(top)}" width="${round(half * 2)}" height="${round(ctx.u * 0.15)}" rx="${round(ctx.u * 0.008)}"/>` },
          { fill: ctx.mix(colour, '#241f1c', 0.25), svg: `<rect x="${round(cx - half)}" y="${round(top + ctx.u * 0.06)}" width="${round(half * 2)}" height="${round(ctx.u * 0.014)}"/>` }
        ];
      }
    },
    tray: {
      hold: 'tray-up',
      label: 'a tray',
      extent: 0.2,
      draw: (ctx) => {
        const p = ctx.hand;
        const y = p.y - ctx.u * 0.02;
        const half = ctx.u * 0.13;
        const colour = ctx.color || '#8d6a45';
        return [
          { fill: colour, svg: `<ellipse cx="${round(p.x)}" cy="${round(y)}" rx="${round(half)}" ry="${round(half * 0.26)}"/>` },
          // Two dishes, so the tray is carrying rather than empty.
          { fill: '#f4efe4', svg: `<ellipse cx="${round(p.x - half * 0.36)}" cy="${round(y - ctx.u * 0.014)}" rx="${round(half * 0.34)}" ry="${round(half * 0.14)}"/><ellipse cx="${round(p.x + half * 0.38)}" cy="${round(y - ctx.u * 0.01)}" rx="${round(half * 0.28)}" ry="${round(half * 0.12)}"/>` },
          { fill: '#c0663a', svg: `<ellipse cx="${round(p.x - half * 0.36)}" cy="${round(y - ctx.u * 0.018)}" rx="${round(half * 0.18)}" ry="${round(half * 0.07)}"/>` }
        ];
      }
    },
    plate: {
      hold: 'serve-forward',
      label: 'a plate of food',
      extent: 0.14,
      draw: (ctx) => {
        const p = ctx.hand;
        const y = p.y - ctx.u * 0.015;
        const half = ctx.u * 0.075;
        return [
          { fill: ctx.color || '#f4efe4', svg: `<ellipse cx="${round(p.x)}" cy="${round(y)}" rx="${round(half)}" ry="${round(half * 0.3)}"/>` },
          { fill: '#c0663a', svg: `<ellipse cx="${round(p.x)}" cy="${round(y - ctx.u * 0.008)}" rx="${round(half * 0.5)}" ry="${round(half * 0.16)}"/>` }
        ];
      }
    },
    hose: {
      hold: 'two-hand-shaft',
      label: 'a fire hose',
      extent: 0.55,
      draw: (ctx) => {
        const a = ctx.hands.left || ctx.hands.right;
        const b = ctx.hands.right || ctx.hands.left;
        const colour = ctx.color || '#c8b48a';
        const nozzle = shaft({ ...ctx, reach: 0.12 }, '#5f6b70', (c, tip, u) => [
          { fill: '#9aa3a6', svg: `<path d="M ${round(tip.x)} ${round(tip.y)} l ${round(-u.y * c.u * 0.022)} ${round(u.x * c.u * 0.022)} l ${round(u.x * c.u * 0.05)} ${round(u.y * c.u * 0.05)} l ${round(u.y * c.u * 0.044)} ${round(-u.x * c.u * 0.044)} Z"/>` }
        ]);
        // The slack line runs back off the figure: a hose is attached to
        // something, which is half of why it reads as firefighting.
        const slack = `<path d="M ${round(a.x)} ${round(a.y)} C ${round(a.x - ctx.u * 0.18)} ${round(a.y + ctx.u * 0.1)} ${round(a.x - ctx.u * 0.3)} ${round(a.y + ctx.u * 0.24)} ${round(a.x - ctx.u * 0.42)} ${round(a.y + ctx.u * 0.26)}" fill="none" stroke="${colour}" stroke-width="${round(ctx.u * 0.02)}" stroke-linecap="round"/>`;
        return [...nozzle, { fill: colour, svg: slack }, { fill: colour, svg: `<line x1="${round(a.x)}" y1="${round(a.y)}" x2="${round(b.x)}" y2="${round(b.y)}" stroke="${colour}" stroke-width="${round(ctx.u * 0.02)}" stroke-linecap="round"/>` }];
      }
    },
    hoe: {
      hold: 'two-hand-shaft',
      label: 'a hoe',
      extent: 0.55,
      draw: (ctx) => shaft({ ...ctx, reach: 0.42 }, ctx.color || '#9a7245', (c, tip, u) => [
        { fill: '#6b6f72', svg: `<path d="M ${round(tip.x)} ${round(tip.y)} l ${round(-u.y * c.u * 0.06)} ${round(u.x * c.u * 0.06)} l ${round(u.x * c.u * 0.03)} ${round(u.y * c.u * 0.03)} l ${round(u.y * c.u * 0.06)} ${round(-u.x * c.u * 0.06)} Z"/>` }
      ])
    },
    broom: {
      hold: 'two-hand-shaft',
      label: 'a broom',
      extent: 0.55,
      draw: (ctx) => shaft({ ...ctx, reach: 0.4 }, ctx.color || '#9a7245', (c, tip, u) => [
        { fill: '#b98f4e', svg: `<path d="M ${round(tip.x - u.y * c.u * 0.05)} ${round(tip.y + u.x * c.u * 0.05)} L ${round(tip.x + u.y * c.u * 0.05)} ${round(tip.y - u.x * c.u * 0.05)} L ${round(tip.x + u.x * c.u * 0.07 + u.y * c.u * 0.07)} ${round(tip.y + u.y * c.u * 0.07 - u.x * c.u * 0.07)} L ${round(tip.x + u.x * c.u * 0.07 - u.y * c.u * 0.07)} ${round(tip.y + u.y * c.u * 0.07 + u.x * c.u * 0.07)} Z"/>` }
      ])
    },
    oar: { hold: 'two-hand-shaft', label: 'an oar', extent: 0.9, draw: (ctx) => shaft({ ...ctx, reach: 0.75 }, ctx.color || '#8a6a44', (c, tip, u) => [
      { fill: '#8a6a44', svg: `<ellipse cx="${round(tip.x + u.x * c.u * 0.05)}" cy="${round(tip.y + u.y * c.u * 0.05)}" rx="${round(c.u * 0.055)}" ry="${round(c.u * 0.022)}" transform="rotate(${round(Math.atan2(u.y, u.x) * 180 / Math.PI)} ${round(tip.x + u.x * c.u * 0.05)} ${round(tip.y + u.y * c.u * 0.05)})"/>` }
    ]) },
    'watering-can': { hold: 'hand-down', label: 'a watering can', extent: 0.2, draw: (ctx) => {
      const p = ctx.hand;
      const top = p.y + ctx.u * 0.015;
      const half = ctx.u * 0.045;
      const colour = ctx.color || '#6f8b7c';
      return [
        { fill: colour, svg: `<rect x="${round(p.x - half)}" y="${round(top)}" width="${round(half * 2)}" height="${round(ctx.u * 0.09)}" rx="${round(ctx.u * 0.01)}"/>` },
        { fill: colour, svg: `<path d="M ${round(p.x + half)} ${round(top + ctx.u * 0.02)} L ${round(p.x + half * 2.4)} ${round(top + ctx.u * 0.07)} L ${round(p.x + half * 2.4)} ${round(top + ctx.u * 0.09)} L ${round(p.x + half)} ${round(top + ctx.u * 0.05)} Z"/>` }
      ];
    } },
    notebook: { hold: 'serve-forward', label: 'a notebook', extent: 0.14, draw: (ctx) => {
      const p = ctx.hand;
      const w = ctx.u * 0.07;
      const h = ctx.u * 0.09;
      return [
        { fill: ctx.color || '#e8e0cd', svg: `<rect x="${round(p.x - w / 2)}" y="${round(p.y - h * 0.7)}" width="${round(w)}" height="${round(h)}" rx="${round(ctx.u * 0.005)}"/>` },
        { fill: '#8d8578', svg: `<rect x="${round(p.x - w * 0.3)}" y="${round(p.y - h * 0.5)}" width="${round(w * 0.6)}" height="${round(ctx.u * 0.004)}"/><rect x="${round(p.x - w * 0.3)}" y="${round(p.y - h * 0.3)}" width="${round(w * 0.6)}" height="${round(ctx.u * 0.004)}"/>` }
      ];
    } },
    book: { hold: 'front-cradle', label: 'a book', extent: 0.16, draw: (ctx) => {
      const l = ctx.hands.left;
      const r = ctx.hands.right;
      const cx = (l.x + r.x) / 2;
      const y = (l.y + r.y) / 2 - ctx.u * 0.02;
      const half = Math.max(Math.abs(r.x - l.x) / 2, ctx.u * 0.07);
      return [
        { fill: ctx.color || '#a24d3a', svg: `<rect x="${round(cx - half)}" y="${round(y)}" width="${round(half * 2)}" height="${round(ctx.u * 0.055)}" rx="${round(ctx.u * 0.004)}"/>` },
        { fill: '#f4efe4', svg: `<rect x="${round(cx - half * 0.94)}" y="${round(y + ctx.u * 0.006)}" width="${round(half * 1.88)}" height="${round(ctx.u * 0.03)}"/>` }
      ];
    } }
  };

  /**
   * Contact goals for holding `propId`, in the body's own units.
   * @param {string} propId
   * @param {{side?: 'left'|'right', hold?: string}} [spec]
   */
  function grips(propId, spec) {
    const prop = PROPS[propId];
    if (!prop) return [];
    const hold = HOLDS[(spec && spec.hold) || prop.hold];
    if (!hold) return [];
    const flip = (spec && spec.side) === 'left';
    const out = [];
    for (const [side, at] of Object.entries(hold.hands)) {
      const which = flip ? (side === 'right' ? 'left' : 'right') : side;
      out.push({ effector: `${which}Hand`, at: flip ? mirror(at) : at });
    }
    return out;
  }

  /** Whether holding this prop should be allowed to turn the torso. */
  const holdOf = (propId, spec) => HOLDS[(spec && spec.hold) || (PROPS[propId] || {}).hold] || null;

  /**
   * Paper shapes for the prop, drawn off the hands the solver produced.
   * @param {string} propId
   * @param {object} figure rig figure (pixel space)
   * @param {{side?: string, color?: string, mix?: Function}} [spec]
   */
  function shapes(propId, figure, spec) {
    const prop = PROPS[propId];
    if (!prop) return [];
    const s = spec || {};
    const held = grips(propId, s).map((g) => g.effector);
    const hands = {
      left: held.includes('leftHand') ? figure.joints.leftHand : null,
      right: held.includes('rightHand') ? figure.joints.rightHand : null
    };
    const ctx = {
      u: figure.height,
      hands,
      hand: hands.right || hands.left,
      color: s.color,
      mix: s.mix || ((a) => a)
    };
    if (!ctx.hand) return [];
    return prop.draw(ctx).filter(Boolean);
  }

  /**
   * Box the prop needs around the hands holding it. Drawing happens in path
   * strings, so the renderer cannot measure it: each prop declares its reach
   * instead, and an oar is not allowed to run off the edge of the page.
   */
  function extent(propId, figure, spec) {
    const prop = PROPS[propId];
    if (!prop) return null;
    const held = grips(propId, spec).map((g) => g.effector);
    const points = held.map((e) => figure.joints[e]).filter(Boolean);
    if (!points.length) return null;
    const pad = figure.height * (prop.extent ?? 0.25);
    return {
      minX: Math.min(...points.map((p) => p.x)) - pad,
      maxX: Math.max(...points.map((p) => p.x)) + pad,
      minY: Math.min(...points.map((p) => p.y)) - pad,
      maxY: Math.max(...points.map((p) => p.y)) + pad
    };
  }

  return { PROPS, HOLDS, grips, shapes, holdOf, extent };
});
