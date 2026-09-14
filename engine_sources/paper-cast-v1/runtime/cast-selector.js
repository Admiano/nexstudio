/**
 * NexStudio Paper Cast — contextual selector and staging resolver
 *
 * Mirrors the scene path (NexAgentSelector): script context in, ranked cast out.
 * The difference is staging — every cast member is placed on the stage and
 * oriented toward whatever it is actually addressing, so orientation is derived
 * from the beat rather than defaulting to camera-facing.
 */
(function (root, factory) {
  const rig = typeof module === 'object' && module.exports ? require('./paper-cast-rig.js') : root.NexPaperCastRig;
  const context = typeof module === 'object' && module.exports ? require('./cast-context.js') : root.NexCastContext;
  const api = factory(rig, context);
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastSelector = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Rig, Context) {
  const DEG = 180 / Math.PI;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const unique = (list) => [...new Set(list)];

  let REGISTRY = null;
  let POSES = null;

  function init(registry, poseLibrary) {
    REGISTRY = registry && registry.entries ? registry : { entries: [] };
    POSES = poseLibrary && poseLibrary.poses ? poseLibrary : { poses: [] };
    return { characters: REGISTRY.entries.length, poses: POSES.poses.length };
  }

  const pose = (id) => POSES.poses.find((p) => p.id === id) || null;

  function scoreCharacter(entry, ctx) {
    let score = 0;
    const reasons = [];
    const add = (points, reason) => {
      score += points;
      reasons.push(reason);
    };

    if (ctx.role && entry.role === ctx.role) add(40, `role:${entry.role}`);
    else if (ctx.roles && ctx.roles.includes(entry.role)) add(24, `role-candidate:${entry.role}`);

    const intentHits = (ctx.intents || []).filter((i) => entry.intents.includes(i));
    if (intentHits.length) add(Math.min(30, intentHits.length * 12), `intent:${intentHits.join('+')}`);

    const words = unique(String(ctx.script || '').toLowerCase().match(/[a-z][a-z-]{2,}/g) || []);
    const keywordHits = entry.keywords.filter((k) => words.some((w) => w.startsWith(k) || k.startsWith(w)));
    if (keywordHits.length) add(Math.min(18, keywordHits.length * 6), `keyword:${keywordHits.slice(0, 3).join('+')}`);

    if (ctx.ageBand && entry.ageBand === ctx.ageBand) add(16, `age:${entry.ageBand}`);
    else if (ctx.ageBand) score -= 10;

    if (ctx.useCase && entry.useCases.includes(ctx.useCase)) add(12, `useCase:${ctx.useCase}`);
    if (ctx.personality && entry.personalities.includes(ctx.personality)) add(8, `personality:${ctx.personality}`);
    if (ctx.motionEnergy && entry.motionEnergy.includes(ctx.motionEnergy)) add(6, `energy:${ctx.motionEnergy}`);
    if (ctx.action && entry.poses.includes(ctx.action)) add(14, `action:${ctx.action}`);
    if (ctx.paperStyle && !entry.paperStyles.includes(ctx.paperStyle)) score -= 25;

    return { entry, score, reasons };
  }

  function choosePose(entry, ctx, requested) {
    const candidates = unique([requested, ctx.action, ...(ctx.actions || []), ...entry.poses].filter(Boolean))
      .map(pose)
      .filter(Boolean);
    const supported = candidates.find((p) => entry.poses.includes(p.id));
    const byIntent = candidates.find((p) => (ctx.intents || []).some((i) => p.intents.includes(i)));
    const byEnergy = candidates.find((p) => p.energy.includes(ctx.motionEnergy));
    return supported || byIntent || byEnergy || pose(entry.defaultPose) || POSES.poses[0];
  }

  /** Stage coordinates: x spans the frame (-1 left, +1 right), depth is +1 toward the camera. */
  function stagePositions(size, options) {
    const opts = options || {};
    const spread = typeof opts.spread === 'number' ? opts.spread : 0.55;
    if (size <= 1) return [{ x: typeof opts.anchorX === 'number' ? opts.anchorX : -0.3, depth: 0 }];
    const step = (spread * 2) / (size - 1);
    return Array.from({ length: size }, (_, i) => ({ x: -spread + step * i, depth: i % 2 === 0 ? 0 : -0.12 }));
  }

  function targetPoint(target, self, members, contentAnchor) {
    const camera = { x: self.x, depth: self.depth + 2.2, kind: 'camera' };
    if (typeof target === 'number') {
      const other = members[target];
      return other && other !== self ? { x: other.x, depth: other.depth, kind: 'peer' } : camera;
    }
    if (!target || target === 'camera') return camera;
    if (target === 'content' || target === 'scene') return { ...contentAnchor, kind: 'content' };
    const other = members.find((m) => m.id === target || m.slug === target || m.role === target);
    return other ? { x: other.x, depth: other.depth, kind: 'peer' } : camera;
  }

  /**
   * Yaw that points the character's front at `to`.
   * Local +z projects to screen x = sin(yaw) and depth = cos(yaw), so the yaw
   * that faces a target is atan2(dx, d-depth) — a target upstage yields a
   * three-quarter or back view instead of a camera-facing one.
   */
  function yawToward(from, to) {
    const dx = to.x - from.x;
    const dz = to.depth - from.depth;
    if (Math.abs(dx) < 1e-6 && Math.abs(dz) < 1e-6) return 0;
    return Math.atan2(dx, dz) * DEG;
  }

  function snapToAllowed(yaw, allowed) {
    const axes = (allowed && allowed.length ? allowed : Object.keys(Rig.VIEW_AXES)).filter((a) => a in Rig.VIEW_AXES);
    let best = axes[0];
    let bestDelta = Infinity;
    for (const axis of axes) {
      const delta = Math.abs(((yaw - Rig.VIEW_AXES[axis] + 540) % 360) - 180);
      if (delta < bestDelta) {
        bestDelta = delta;
        best = axis;
      }
    }
    return { axis: best, yaw: Rig.VIEW_AXES[best], residual: ((yaw - Rig.VIEW_AXES[best] + 540) % 360) - 180 };
  }

  /**
   * Resolves body orientation and head yaw for one member.
   * The body snaps to the view axis its pose is authored for; whatever turn is
   * left over goes to the head, which is how a character can work at a surface
   * upstage while glancing back at the viewer.
   */
  function orient(member, members, ctx, contentAnchor, posed) {
    const bodyTarget = targetPoint(member.addressing, member, members, contentAnchor);
    const desired = yawToward(member, bodyTarget);
    const snapped = snapToAllowed(desired, posed.viewAxes);
    const gazeTarget = targetPoint(member.gazeAt ?? member.addressing, member, members, contentAnchor);
    const gazeYaw = yawToward(member, gazeTarget);
    const headYaw = clamp(((gazeYaw - snapped.yaw + 540) % 360) - 180, -62, 62);
    return {
      viewAxis: snapped.axis,
      yaw: snapped.yaw,
      headYaw,
      addressing: bodyTarget.kind,
      gazeAt: gazeTarget.kind,
      unreachableTurn: Math.abs(snapped.residual) > 62 ? Math.round(snapped.residual) : 0
    };
  }

  /**
   * @param {object} request script/intent context plus optional explicit cast
   * @returns {{context: object, cast: Array, alternates: Array, warnings: string[]}}
   */
  function select(request) {
    if (!REGISTRY) throw new Error('NexCastSelector.init(registry, poseLibrary) must run first');
    const req = request || {};
    const ctx = Context.analyze(req.script || '', {
      role: req.role,
      intent: req.intent,
      intents: req.intents,
      action: req.action,
      ageBand: req.ageBand,
      useCase: req.useCase,
      paperStyle: req.paperStyle,
      aspectRatio: req.aspectRatio,
      motionEnergy: req.motionEnergy,
      castSize: req.castSize
    });
    const warnings = [];

    const requested = Array.isArray(req.cast) && req.cast.length ? req.cast : null;
    const size = requested ? requested.length : clamp(ctx.castSize || 1, 1, 4);
    const positions = stagePositions(size, req.staging);
    const contentAnchor = (req.staging && req.staging.contentAnchor)
      || { x: ctx.direction === 'left' ? -0.85 : 0.85, depth: -0.5 };

    const taken = new Set();
    const members = [];
    const alternates = [];

    for (let i = 0; i < size; i += 1) {
      const slot = requested ? requested[i] : {};
      const slotCtx = { ...ctx, ...slot, script: slot.script || ctx.script };
      const ranked = REGISTRY.entries
        .map((entry) => scoreCharacter(entry, slotCtx))
        .sort((a, b) => b.score - a.score || a.entry.id.localeCompare(b.entry.id));
      const pick = ranked.find((r) => (slot.id ? r.entry.id === slot.id || r.entry.slug === slot.id : !taken.has(r.entry.id))) || ranked[0];
      if (!pick) {
        warnings.push('no cast entries registered');
        break;
      }
      taken.add(pick.entry.id);
      if (i === 0) alternates.push(...ranked.slice(1, 4).map((r) => ({ id: r.entry.id, score: r.score, reasons: r.reasons })));
      if (pick.score <= 0) warnings.push(`weak match for slot ${i}: ${pick.entry.id} scored ${pick.score}`);

      const chosen = choosePose(pick.entry, slotCtx, slot.pose);
      members.push({
        index: i,
        id: pick.entry.id,
        slug: pick.entry.slug,
        role: pick.entry.role,
        entry: pick.entry,
        score: pick.score,
        reasons: pick.reasons,
        posed: chosen,
        x: typeof slot.x === 'number' ? slot.x : positions[i].x,
        depth: typeof slot.depth === 'number' ? slot.depth : positions[i].depth,
        addressing: slot.addressing ?? defaultTarget(ctx, i, size),
        gazeAt: slot.gazeAt ?? null,
        name: slot.name || null,
        line: slot.line || null
      });
    }

    const cast = members.map((member) => {
      const orientation = orient(member, members, ctx, contentAnchor, member.posed);
      if (orientation.unreachableTurn) {
        warnings.push(`${member.id}: pose ${member.posed.id} cannot face its target (${orientation.unreachableTurn}° short)`);
      }
      return {
        id: member.id,
        slug: member.slug,
        role: member.role,
        name: member.name,
        line: member.line,
        score: member.score,
        reasons: member.reasons,
        pose: member.posed.id,
        poseAngles: member.posed.pose,
        proportion: member.entry.proportion,
        look: member.entry.look,
        stage: { x: member.x, depth: member.depth },
        view: orientation,
        manifest: member.entry.id
      };
    });

    return { context: ctx, contentAnchor, cast, alternates, warnings };
  }

  function defaultTarget(ctx, index, size) {
    if (ctx.addressing === 'peer' && size > 1) return index === 0 ? 1 : 0;
    if (ctx.addressing) return ctx.addressing;
    if (size > 1) return index === 0 ? 1 : 0;
    const contentIntents = ['guide_attention', 'show_data', 'demonstrate', 'compare_options', 'show_work', 'investigate', 'move_through_story'];
    if ((ctx.intents || []).some((i) => contentIntents.includes(i))) return 'content';
    return 'camera';
  }

  function search(query, limit) {
    if (!REGISTRY) throw new Error('NexCastSelector.init(registry, poseLibrary) must run first');
    const ctx = Context.analyze(query || '');
    return REGISTRY.entries
      .map((entry) => scoreCharacter(entry, ctx))
      .sort((a, b) => b.score - a.score || a.entry.id.localeCompare(b.entry.id))
      .slice(0, limit || 5)
      .map((r) => ({ id: r.entry.id, name: r.entry.name, score: r.score, reasons: r.reasons }));
  }

  return { init, select, search, scoreCharacter, choosePose, stagePositions, yawToward, snapToAllowed, orient };
});
