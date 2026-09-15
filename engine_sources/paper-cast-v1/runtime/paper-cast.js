/**
 * NexStudio Paper Cast — public API
 *
 *   const cast = NexPaperCast.init();            // browser: uses NEX_CAST globals
 *   const scene = cast.renderScene({ script: 'She turns to the whiteboard and points at the spike.' });
 *   container.innerHTML = scene.svg;
 *
 * The script drives who appears, what they do and which way they face; nothing
 * in the pipeline assumes a camera-facing character.
 */
(function (root, factory) {
  const isNode = typeof module === 'object' && !!module.exports;
  const deps = isNode
    ? {
      Rig: require('./paper-cast-rig.js'),
      Renderer: require('./paper-cast-renderer.js'),
      Selector: require('./cast-selector.js'),
      Context: require('./cast-context.js'),
      Performance: require('./cast-performance.js'),
      Body: require('./cast-body.js'),
      Contact: require('./cast-contact.js'),
      Relation: require('./cast-relation.js'),
      Wardrobe: require('./cast-wardrobe.js'),
      Paperbook: require('./paperbook-figure.js'),
      load: () => {
        const fs = require('fs');
        const path = require('path');
        const dir = path.resolve(__dirname, '..', 'manifests');
        return {
          registry: JSON.parse(fs.readFileSync(path.join(dir, 'cast-index.json'), 'utf8')),
          poses: JSON.parse(fs.readFileSync(path.join(dir, 'pose-library.json'), 'utf8'))
        };
      }
    }
    : {
      Rig: root.NexPaperCastRig,
      Renderer: root.NexPaperCastRenderer,
      Selector: root.NexCastSelector,
      Context: root.NexCastContext,
      Performance: root.NexCastPerformance,
      Body: root.NexCastBody,
      Contact: root.NexCastContact,
      Relation: root.NexCastRelation,
      Wardrobe: root.NexCastWardrobe,
      Paperbook: root.NexPaperbookFigure,
      load: () => ({ registry: root.NEX_CAST, poses: root.NEX_CAST_POSES })
    };
  const api = factory(deps);
  if (isNode) module.exports = api;
  root.NexPaperCast = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (deps) {
  const { Rig, Renderer, Selector, Context, Performance, Body, Contact, Relation, Wardrobe, Paperbook, load } = deps;
  const round = (n) => Math.round(Number(n) * 100) / 100;

  const FRAMES = {
    '16:9': { width: 1600, height: 900, figureHeight: 0.66, ground: 0.9 },
    '1:1': { width: 1080, height: 1080, figureHeight: 0.62, ground: 0.88 },
    '9:16': { width: 900, height: 1600, figureHeight: 0.45, ground: 0.8 }
  };

  const THEME = `:root{--paper-bg:#f4efe4;--paper-surface:#fbf7ee;--ink:#241f1c;--ink-muted:#6c6259;--shadow-color:#241f1c;}`;

  let state = null;

  function init(options) {
    const opts = options || {};
    const sources = opts.registry && opts.poses ? { registry: opts.registry, poses: opts.poses } : load();
    if (!sources.registry) throw new Error('paper-cast: no cast registry available');
    Selector.init(sources.registry, sources.poses);
    state = { ...sources, initialised: true };
    return api;
  }

  const ready = () => {
    if (!state) init();
    return state;
  };

  /** Selection only — useful for tooling that wants the plan without SVG. */
  function plan(request) {
    ready();
    return Selector.select(request || {});
  }

  function renderCharacter(member, request, frame, crowd, beat) {
    const req = request || {};
    const share = 1 - Math.min(0.32, ((crowd || 1) - 1) * 0.11);
    const angles = beat ? beat.pose : member.poseAngles;
    const figure = Rig.build({
      proportion: member.proportion,
      height: frame.height * frame.figureHeight * share,
      view: member.view.viewAxis,
      pose: { ...angles, head: { ...(angles.head || {}), yaw: member.view.headYaw } }
    });
    return Renderer.render(figure, {
      paperStyle: req.paperStyle || 'clean-editorial',
      look: { ...member.look, ...(req.look || {}) },
      seed: req.seed ? `${req.seed}:${member.id}` : member.id,
      accessibilityLabel: `${member.role} facing ${member.view.viewAxis}, ${member.pose}`
    });
  }

  /**
   * Spaces members so their rendered silhouettes do not collide, then shrinks
   * the whole line-up if the stage cannot hold it — a four-hander in 9:16 is
   * laid out, not stacked on top of itself.
   */
  function spaceOut(placed, frame) {
    const margin = frame.width * 0.03;
    const sorted = [...placed].sort((a, b) => a.x - b.x);
    for (let i = 1; i < sorted.length; i += 1) {
      const gap = sorted[i - 1].halfWidth + sorted[i].halfWidth;
      if (sorted[i].x - sorted[i - 1].x < gap) sorted[i].x = sorted[i - 1].x + gap;
    }
    if (!sorted.length) return placed;
    const left = sorted[0].x - sorted[0].halfWidth;
    const right = sorted[sorted.length - 1].x + sorted[sorted.length - 1].halfWidth;
    const centre = frame.width / 2 - (left + right) / 2;
    for (const item of sorted) item.x += centre;
    const span = right - left;
    const room = frame.width - margin * 2;
    if (span > room) {
      const shrink = room / span;
      for (const item of sorted) {
        item.x = frame.width / 2 + (item.x - frame.width / 2) * shrink;
        item.scale *= shrink;
        item.halfWidth *= shrink;
      }
    }
    return placed;
  }

  /**
   * Composes the selected cast into one paper stage. Members are drawn far to
   * near and scaled by stage depth, so a character addressing another character
   * upstage genuinely sits behind them.
   */
  function renderScene(request) {
    ready();
    const req = request || {};
    const selection = Selector.select(req);
    const frame = FRAMES[req.aspectRatio] || FRAMES['16:9'];
    const groundY = frame.height * frame.ground;
    const defs = [];
    const layers = [];
    const crowd = Math.max(1, selection.cast.length);

    // `time` runs the performance layer: the same second always yields the same
    // frame, so a paper-motion timeline can seek this stage like any component.
    const timed = typeof req.time === 'number';

    const members = selection.cast
      .map((member) => {
        const beat = timed ? Performance.frame(member, req.time, { duration: req.duration }) : null;
        const rendered = renderCharacter(member, req, frame, crowd, beat);
        const scale = 1 + member.stage.depth * 0.18;
        return {
          member,
          beat,
          rendered,
          scale,
          x: frame.width / 2 + member.stage.x * frame.width * 0.32,
          halfWidth: (rendered.width * scale) / 2
        };
      });
    spaceOut(members, frame);
    members.sort((a, b) => a.member.stage.depth - b.member.stage.depth);

    for (const { member, beat, rendered, scale, x } of members) {
      const lift = round(-rendered.ground);
      const driftX = beat ? beat.offsetX * frame.width * 0.32 : 0;
      const driftY = beat ? beat.offsetY * frame.height : 0;
      if (rendered.defs) defs.push(rendered.defs);
      layers.push(
        `<g class="pc-stage-member" data-id="${member.id}" data-pose="${member.pose}" data-view-axis="${member.view.viewAxis}" data-head-axis="${Rig.nearestViewAxis(Rig.VIEW_AXES[member.view.viewAxis] + member.view.headYaw)}" data-addressing="${member.view.addressing}" transform="translate(${round(x + driftX)} ${round(groundY + driftY)}) scale(${round(scale)}) translate(0 ${lift})"${beat ? ` opacity="${round(beat.opacity)}"` : ''}>${rendered.group}</g>`
      );
    }

    const svg = [
      `<svg class="nex-paper-cast-stage" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${frame.width} ${frame.height}" preserveAspectRatio="xMidYMax meet" role="img" aria-label="${(req.accessibilityLabel || 'Paper cast stage').replace(/"/g, '')}">`,
      `<defs>${defs.join('')}</defs><style>${THEME}</style>`,
      `<rect class="pc-stage-bg" width="${frame.width}" height="${frame.height}" fill="var(--paper-bg)"/>`,
      `<line class="pc-stage-ground" x1="0" y1="${round(groundY)}" x2="${frame.width}" y2="${round(groundY)}" stroke="var(--ink-muted)" stroke-width="2" stroke-dasharray="14 12" opacity="0.35"/>`,
      layers.join(''),
      '</svg>'
    ].join('');

    return { svg, frame, ...selection };
  }

  /** One character, no stage — for explorers, contact sheets and thumbnails. */
  function renderFigure(options) {
    ready();
    const opts = options || {};
    const entry = state.registry.entries.find((e) => e.id === opts.id || e.slug === opts.id) || state.registry.entries[0];
    const posed = state.poses.poses.find((p) => p.id === opts.pose) || state.poses.poses.find((p) => p.id === entry.defaultPose);
    const headYaw = typeof opts.headYaw === 'number' ? opts.headYaw : (posed.pose.head && posed.pose.head.yaw) || 0;
    const figure = Rig.build({
      proportion: opts.proportion || entry.proportion,
      height: opts.height || 900,
      view: opts.viewAxis || entry.defaultViewAxis,
      pose: { ...posed.pose, head: { ...(posed.pose.head || {}), yaw: headYaw } }
    });
    return Renderer.render(figure, {
      paperStyle: opts.paperStyle || 'clean-editorial',
      look: { ...entry.look, ...(opts.look || {}) },
      seed: opts.seed || `${entry.id}:${posed.id}:${opts.viewAxis || entry.defaultViewAxis}`,
      accessibilityLabel: entry.accessibilityLabel
    });
  }

  const api = {
    init,
    plan,
    renderScene,
    renderFigure,
    analyze: (script, hints) => Context.analyze(script, hints),
    search: (query, limit) => {
      ready();
      return Selector.search(query, limit);
    },
    get registry() {
      return ready().registry;
    },
    get poses() {
      return ready().poses;
    },
    /**
     * Illustrates a two-body relation (`carry-on-back`, `support-walk`,
     * `grip-prop`) in the paperbook skin. The relation solves the contacts;
     * this only draws the result.
     */
    illustrate(kind, spec, options) {
      return Paperbook.renderRelation(Relation.relate(kind, spec || {}), options || {});
    },
    /** A single body, posed from goals rather than picked from the pose list. */
    illustrateFigure(options) {
      return Paperbook.renderPose(options || {});
    },
    body: (spec) => Body.body(spec),

    /** What the artist can put on a character: garments, overlays, headwear. */
    wardrobe: () => ({
      garments: Object.keys(Wardrobe.GARMENTS),
      overlays: Object.keys(Wardrobe.OVERLAYS),
      headwear: Object.keys(Wardrobe.HEADWEAR)
    }),
    FRAMES,
    Rig,
    Body,
    Wardrobe,
    Contact,
    Relation,
    Paperbook,
    Renderer,
    Selector,
    Context,
    Performance
  };

  return api;
});
