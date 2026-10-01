/**
 * NexStudio Editorial Motion — ratio-native layout
 *
 * Each ratio is authored, not scaled. A frame is divided into bands whose
 * proportions belong to that ratio, elements are placed into the bands their
 * kind is allowed to occupy, and the result is proven disjoint before it is
 * handed to the renderer. A layout that cannot be resolved without a collision
 * drops its least important element rather than overlapping it.
 */
(function (root, factory) {
  const node = typeof require === 'function' && typeof module === 'object';
  const api = factory(node ? require('../manifests/editorial-rules.json') : root.NEX_EDITORIAL_RULES);
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexEditorialLayout = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (RULES) {
  const round = (v, p = 4) => Number(Number(v).toFixed(p));
  const RATIOS = ['16:9', '1:1', '9:16'];

  /**
   * Band plans per ratio, in safe-area fractions. Landscape reads left to
   * right, square reads as a stacked card, portrait reads top to bottom.
   */
  const PLANS = {
    '16:9': {
      'text': [{ id: 'text', x: 0, y: 0.12, w: 1, h: 0.76 }],
      'text+icons': [
        { id: 'text', x: 0, y: 0.1, w: 0.66, h: 0.8 },
        { id: 'icons', x: 0.7, y: 0.22, w: 0.3, h: 0.56, flow: 'column' }
      ],
      'text+character': [
        { id: 'text', x: 0, y: 0.1, w: 0.6, h: 0.8 },
        { id: 'character', x: 0.64, y: 0.04, w: 0.36, h: 0.96, anchor: 'bottom' }
      ],
      'text+icons+character': [
        { id: 'text', x: 0, y: 0.08, w: 0.52, h: 0.62 },
        { id: 'icons', x: 0, y: 0.74, w: 0.52, h: 0.18, flow: 'row' },
        { id: 'character', x: 0.62, y: 0.04, w: 0.38, h: 0.96, anchor: 'bottom' }
      ],
      'text+media': [
        { id: 'text', x: 0, y: 0.16, w: 0.44, h: 0.68 },
        { id: 'media', x: 0.49, y: 0.08, w: 0.51, h: 0.84 }
      ],
      'text+icons+media': [
        { id: 'text', x: 0, y: 0.1, w: 0.42, h: 0.56 },
        { id: 'icons', x: 0, y: 0.7, w: 0.42, h: 0.2, flow: 'row' },
        { id: 'media', x: 0.48, y: 0.08, w: 0.52, h: 0.84 }
      ]
    },
    '1:1': {
      'text': [{ id: 'text', x: 0, y: 0.14, w: 1, h: 0.72 }],
      'text+icons': [
        { id: 'text', x: 0, y: 0.06, w: 1, h: 0.62 },
        { id: 'icons', x: 0.06, y: 0.74, w: 0.88, h: 0.2, flow: 'row' }
      ],
      'text+character': [
        { id: 'text', x: 0, y: 0.04, w: 1, h: 0.42 },
        { id: 'character', x: 0.2, y: 0.5, w: 0.6, h: 0.5, anchor: 'bottom' }
      ],
      'text+icons+character': [
        { id: 'text', x: 0, y: 0.03, w: 1, h: 0.36 },
        { id: 'icons', x: 0.02, y: 0.42, w: 0.28, h: 0.5, flow: 'column' },
        { id: 'character', x: 0.34, y: 0.42, w: 0.66, h: 0.58, anchor: 'bottom' }
      ],
      'text+media': [
        { id: 'text', x: 0, y: 0.04, w: 1, h: 0.34 },
        { id: 'media', x: 0.02, y: 0.42, w: 0.96, h: 0.54 }
      ],
      'text+icons+media': [
        { id: 'text', x: 0, y: 0.03, w: 1, h: 0.3 },
        { id: 'media', x: 0.02, y: 0.36, w: 0.96, h: 0.46 },
        { id: 'icons', x: 0.06, y: 0.86, w: 0.88, h: 0.14, flow: 'row' }
      ]
    },
    '9:16': {
      'text': [{ id: 'text', x: 0, y: 0.08, w: 1, h: 0.84 }],
      'text+icons': [
        { id: 'text', x: 0, y: 0.06, w: 1, h: 0.6 },
        { id: 'icons', x: 0.08, y: 0.7, w: 0.84, h: 0.18, flow: 'row' }
      ],
      'text+character': [
        { id: 'text', x: 0, y: 0.05, w: 1, h: 0.42 },
        { id: 'character', x: 0.08, y: 0.49, w: 0.84, h: 0.51, anchor: 'bottom' }
      ],
      'text+icons+character': [
        { id: 'text', x: 0, y: 0.06, w: 1, h: 0.32 },
        { id: 'icons', x: 0.08, y: 0.4, w: 0.84, h: 0.12, flow: 'row' },
        { id: 'character', x: 0.08, y: 0.55, w: 0.84, h: 0.45, anchor: 'bottom' }
      ],
      'text+media': [
        { id: 'text', x: 0, y: 0.08, w: 1, h: 0.32 },
        { id: 'media', x: 0.03, y: 0.44, w: 0.94, h: 0.48 }
      ],
      'text+icons+media': [
        { id: 'text', x: 0, y: 0.06, w: 1, h: 0.28 },
        { id: 'media', x: 0.03, y: 0.37, w: 0.94, h: 0.44 },
        { id: 'icons', x: 0.08, y: 0.84, w: 0.84, h: 0.13, flow: 'row' }
      ]
    }
  };

  const PRIORITY = ['text', 'media', 'character', 'icons'];

  function planKey(kinds) {
    const present = PRIORITY.filter((k) => kinds.includes(k));
    const ordered = ['text', 'icons', 'media', 'character'].filter((k) => present.includes(k));
    return ordered.join('+');
  }

  function intersects(a, b) {
    return a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
  }

  function collisions(regions) {
    const hits = [];
    for (let i = 0; i < regions.length; i += 1) {
      for (let j = i + 1; j < regions.length; j += 1) {
        if (intersects(regions[i], regions[j])) hits.push([regions[i].id, regions[j].id]);
      }
    }
    return hits;
  }

  /**
   * @param {string} ratio one of 16:9, 1:1, 9:16
   * @param {string[]} kinds element kinds present in the shot
   * @returns {{ratio, frame, regions, dropped, key}}
   */
  function solve(ratio, kinds) {
    if (!RATIOS.includes(ratio)) throw new Error('Unsupported ratio: ' + ratio);
    const frame = (RULES.frames || {})[ratio];
    const plans = PLANS[ratio];
    const dropped = [];
    let wanted = kinds.slice();

    if (!wanted.includes('text')) wanted = ['text', ...wanted];
    while (wanted.length > (frame.maxElements || 4)) dropped.push(wanted.pop());

    let key = planKey(wanted);
    while (!plans[key] && wanted.length > 1) {
      dropped.push(wanted.pop());
      key = planKey(wanted);
    }
    const bands = plans[key] || plans.text;

    const safe = frame.safe || 0.05;
    const inner = { x: safe, y: safe, w: 1 - safe * 2, h: 1 - safe * 2 };
    const regions = bands.map((band) => ({
      id: band.id,
      flow: band.flow || null,
      anchor: band.anchor || 'center',
      x: round(inner.x + band.x * inner.w),
      y: round(inner.y + band.y * inner.h),
      w: round(band.w * inner.w),
      h: round(band.h * inner.h),
      px: {
        x: Math.round((inner.x + band.x * inner.w) * frame.width),
        y: Math.round((inner.y + band.y * inner.h) * frame.height),
        w: Math.round(band.w * inner.w * frame.width),
        h: Math.round(band.h * inner.h * frame.height)
      }
    }));

    const hits = collisions(regions);
    if (hits.length) throw new Error(`Layout ${ratio}/${key} overlaps: ${JSON.stringify(hits)}`);

    return { ratio, key, frame, regions, dropped, byId: Object.fromEntries(regions.map((r) => [r.id, r])) };
  }

  function audit() {
    const report = [];
    for (const ratio of RATIOS) {
      for (const key of Object.keys(PLANS[ratio])) {
        const kinds = key.split('+');
        const layout = solve(ratio, kinds);
        report.push({ ratio, key, regions: layout.regions.length, dropped: layout.dropped.length });
      }
    }
    return report;
  }

  return { solve, audit, collisions, intersects, RATIOS, PLANS, planKey };
});
