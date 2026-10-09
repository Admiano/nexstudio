/**
 * NexStudio Paper Cast — two-body relations
 *
 * Carrying, holding and supporting are not poses: no number of single-body
 * poses can express "the mother's hands are under this particular child's
 * thighs", because the answer depends on the other body. A relation places
 * both figures in a shared frame and solves each one against contact points
 * that belong to the pair.
 *
 * World units are fractions of the primary figure's height, ground plane at
 * y = 0, +z toward the viewer-facing direction of the primary, +x to its right.
 */
(function (root, factory) {
  const isNode = typeof module === 'object' && module.exports;
  const deps = isNode
    ? { Rig: require('./paper-cast-rig.js'), Body: require('./cast-body.js'), Contact: require('./cast-contact.js'), Props: require('./cast-props.js'), World: require('./cast-world.js') }
    : { Rig: root.NexPaperCastRig, Body: root.NexCastBody, Contact: root.NexCastContact, Props: root.NexCastProps, World: root.NexCastWorld };
  const api = factory(deps);
  if (isNode) module.exports = api;
  root.NexCastRelation = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function ({ Rig, Body, Contact, Props, World }) {
  const RAD = Math.PI / 180;

  const rotateY = (p, deg) => {
    const c = Math.cos(deg * RAD);
    const s = Math.sin(deg * RAD);
    return { x: p.x * c + p.z * s, y: p.y, z: -p.x * s + p.z * c };
  };

  const toWorld = (point, participant) => {
    const scaled = { x: point.x * participant.scale, y: point.y * participant.scale, z: point.z * participant.scale };
    const turned = rotateY(scaled, participant.yaw);
    return { x: turned.x + participant.origin.x, y: turned.y + participant.origin.y, z: turned.z + participant.origin.z };
  };

  const toLocal = (point, participant) => {
    const moved = { x: point.x - participant.origin.x, y: point.y - participant.origin.y, z: point.z - participant.origin.z };
    const turned = rotateY(moved, -participant.yaw);
    return { x: turned.x / participant.scale, y: turned.y / participant.scale, z: turned.z / participant.scale };
  };

  /** Pelvis height above ground for a posed body, in its own units. */
  function pelvisLift(proportion, pose) {
    const j = Contact.joints(proportion, pose);
    // Knees count: on one knee they are what the body rests on, and standing
    // they are never the lowest point, so including them costs nothing.
    const low = ['leftToe', 'rightToe', 'leftAnkle', 'rightAnkle', 'leftKnee', 'rightKnee'].reduce((m, key) => Math.min(m, j[key].y), 0);
    return -low;
  }

  function resolveBody(spec) {
    if (spec.proportion && typeof spec.proportion === 'object') return spec.proportion;
    if (spec.body) return Body.body(spec.body);
    if (spec.age != null || spec.build) return Body.body({ age: spec.age, build: spec.build });
    return Body.body(spec.proportion || 'adult-average');
  }

  function participant(spec, primaryStature) {
    const proportion = resolveBody(spec);
    const scale = (proportion.stature || 1) / primaryStature;
    return {
      id: spec.id,
      role: spec.role || spec.id,
      proportion,
      scale,
      yaw: Number(spec.yaw) || 0,
      origin: { x: 0, y: 0, z: 0 },
      pose: Rig.mergePose(spec.pose),
      goals: []
    };
  }

  const settle = (p) => {
    p.origin.y = pelvisLift(p.proportion, p.pose) * p.scale;
    return p;
  };

  function solveAgainst(p, worldGoals, options) {
    if (!worldGoals.length) return p;
    const result = Contact.solve({
      proportion: p.proportion,
      pose: p.pose,
      goals: worldGoals.map((g) => ({ effector: g.effector, at: toLocal(g.at, p), weight: g.weight })),
      torso: options && options.torso,
      tolerance: 0.03
    });
    p.pose = result.pose;
    p.residual = result.residual;
    p.goals = result.goals.map((g, i) => ({ effector: g.effector, error: g.error, at: worldGoals[i].at }));
    return p;
  }

  /** Adult carries a child on the back: child's arms over the shoulders, adult's hands under the thighs. */
  function carryOnBack(spec) {
    const carrier = settle(participant({ id: 'carrier', role: 'carrier', ...(spec.carrier || {}) }, 1));
    const primaryStature = carrier.proportion.stature || 1;
    const child = participant({ id: 'carried', role: 'carried', ...(spec.carried || {}) }, primaryStature);
    child.scale = (child.proportion.stature || 1) / primaryStature;

    // Lean into the load, and set the child riding high on the back.
    carrier.pose = Rig.mergePose({ ...carrier.pose, spine: { tilt: 13, swing: 0 }, chest: { tilt: 6, swing: 0 }, neck: { tilt: -6, swing: 0 } });
    settle(carrier);

    const carrierJoints = Contact.joints(carrier.proportion, carrier.pose);
    // Seated on the small of the back and off to one side, so the child reads
    // over the shoulder instead of disappearing behind the carrier's head.
    const seat = toWorld({ x: carrierJoints.chest.x + 0.05, y: carrierJoints.chest.y * 0.84, z: -0.06 }, carrier);
    child.yaw = carrier.yaw;
    child.origin = { x: seat.x, y: seat.y, z: seat.z };

    // Child clings: legs round the ribs, arms over the shoulders.
    child.pose = Rig.mergePose({
      spine: { tilt: -6, swing: 0 },
      armLeft: { shoulder: { tilt: 128, swing: 26 }, elbow: { tilt: 58, swing: 0 } },
      armRight: { shoulder: { tilt: 128, swing: 26 }, elbow: { tilt: 58, swing: 0 } },
      // Thighs clamp round the carrier's waist, shins hang forward.
      legLeft: { hip: { tilt: 58, swing: 48 }, knee: { tilt: 70, swing: 0 } },
      legRight: { hip: { tilt: 58, swing: 48 }, knee: { tilt: 70, swing: 0 } },
      neck: { tilt: -10, swing: 0 }
    });

    const shoulders = Contact.joints(carrier.proportion, carrier.pose);
    solveAgainst(child, [
      // Small arms cannot span adult shoulders: the grip is near the neck.
      { effector: 'leftHand', at: toWorld({ x: shoulders.leftShoulder.x * 0.45, y: shoulders.leftShoulder.y, z: 0.05 }, carrier) },
      { effector: 'rightHand', at: toWorld({ x: shoulders.rightShoulder.x * 0.45, y: shoulders.rightShoulder.y, z: 0.05 }, carrier) }
    ], { torso: false });

    const childJoints = Contact.joints(child.proportion, child.pose);
    // The grip is under the knees, which a straddling child holds out at the
    // carrier's sides — close to the midline there is nothing to hold.
    const support = ['left', 'right'].map((side) => {
      const knee = childJoints[side + 'Knee'];
      return toWorld({ x: knee.x * 1.1, y: knee.y - child.proportion.limb * 1.2, z: knee.z }, child);
    });

    solveAgainst(carrier, [
      { effector: 'leftHand', at: support[0] },
      { effector: 'rightHand', at: support[1] }
    ], { torso: false });

    // A body behind another body is a body the reader cannot see. The pair is
    // only legible off-axis, so the relation states the views that work and the
    // compositor picks the camera instead of guessing.
    return compose('carry-on-back', [carrier, child], spec, null, ['profile-right', 'three-quarter-right', 'profile-left']);
  }

  /** Adult holds a toddler's raised hand while the toddler takes a step. */
  function supportWalk(spec) {
    const adult = settle(participant({ id: 'adult', role: 'supporter', ...(spec.adult || spec.carrier || {}) }, 1));
    const primaryStature = adult.proportion.stature || 1;
    const toddler = participant({ id: 'toddler', role: 'supported', ...(spec.toddler || spec.carried || {}) }, primaryStature);

    // `side` is the adult's hand; the toddler reaches up with the hand on the
    // side it stands on, so the two arms meet instead of crossing the bodies.
    const side = spec.side === 'left' ? 'left' : 'right';
    const childSide = side === 'right' ? 'left' : 'right';
    const gap = typeof spec.gap === 'number' ? spec.gap : 0.22;

    // Mid-step: weight on the back foot, the leading foot reaching out and
    // still off the ground, which is what makes it read as learning to walk.
    toddler.pose = Rig.mergePose({
      spine: { tilt: 9, swing: 0 },
      chest: { tilt: 4, swing: 0 },
      legLeft: { hip: { tilt: 26, swing: 7 }, knee: { tilt: 22, swing: 0 }, ankle: { tilt: -8, swing: 0 } },
      legRight: { hip: { tilt: -14, swing: 5 }, knee: { tilt: 9, swing: 0 } },
      [`arm${childSide === 'right' ? 'Left' : 'Right'}`]: { shoulder: { tilt: -14, swing: 44 }, elbow: { tilt: 30, swing: 0 } },
      neck: { tilt: -6, swing: 0 }
    });
    settle(toddler);
    toddler.origin.x = side === 'right' ? gap : -gap;
    toddler.yaw = Number(spec.toddlerYaw) || 0;

    const toddlerJoints = Contact.joints(toddler.proportion, toddler.pose);
    // Meet where a small raised arm and a lowered adult arm can both arrive:
    // just above the toddler's head, between the two bodies.
    const toward = Math.sign(adult.origin.x - toddler.origin.x) || -1;
    const handHold = {
      x: toddler.origin.x + toward * 0.06,
      y: toddler.origin.y + (toddlerJoints.head.y + toddler.proportion.head * 0.9) * toddler.scale,
      z: 0.03
    };

    // The adult has to stoop: a hand held at toddler-head height is below where
    // an upright adult arm ends, so the torso is part of the solve here.
    solveAgainst(adult, [{ effector: `${side}Hand`, at: handHold }], { torso: true });
    solveAgainst(toddler, [{ effector: `${childSide}Hand`, at: handHold }], { torso: false });

    return compose('support-walk', [adult, toddler], spec, [{ between: [`adult.${side}Hand`, `toddler.${childSide}Hand`], at: handHold }]);
  }

  /**
   * Single body gripping a prop at one or more of its anchors. A prop is held
   * by the body, so its anchors are authored in the actor's own units and
   * travel with it; the reported contacts are converted back to world.
   */
  function gripProp(spec) {
    const actor = settle(participant({ id: 'actor', ...(spec.actor || {}) }, 1));
    // Either name a prop from the catalogue and let it say where the hands go,
    // or author the anchors for something the catalogue has never seen.
    const propId = spec.propId && Props.PROPS[spec.propId] ? spec.propId : null;
    const authored = spec.grips || (propId ? Props.grips(propId, { side: spec.side }) : []);
    const grips = authored.filter((g) => g && g.effector && g.at);
    solveAgainst(actor, grips.map((g) => ({ effector: g.effector, at: toWorld(g.at, actor), weight: g.weight })), { torso: spec.torso !== false });
    if (propId) actor.props = [{ id: propId, side: spec.side }];
    return compose('grip-prop', [actor], spec, (actor.goals || []).map((g) => ({ between: [`actor.${g.effector}`, spec.propId || 'prop'], at: g.at, error: g.error })));
  }

  /* ---------------------------------------------------------------------- *
   * Relations against the world
   *
   * Everything below takes its target from `cast-world.js` rather than from
   * numbers written into the beat: a chair states its own seat height, a
   * counter its own edge, and the body is solved to that. Swap the stool for
   * a bench and the figure sits lower without a line changing.
   * ---------------------------------------------------------------------- */

  /** Resolves `{ scene, feature }` however the caller chose to supply them. */
  function staging(spec, defaultKind) {
    const scene = spec.scene && typeof spec.scene.anchor === 'function'
      ? spec.scene
      : (spec.scene ? World.scene(spec.scene) : null);
    let feature = null;
    if (spec.feature && spec.feature.anchors) feature = spec.feature;
    else if (spec.feature) feature = World.feature(spec.feature);
    else if (scene && spec.at && typeof spec.at === 'string') feature = scene.get(String(spec.at).split('.')[0]);
    if (!feature && defaultKind) feature = World.feature({ id: defaultKind, kind: defaultKind });
    return { scene, feature, ground: scene ? scene.ground : World.groundPlane() };
  }

  /** A world point from an anchor reference, a dotted scene path, or literal coordinates. */
  function pointOf(ctx, ref, fallbackName) {
    if (ref && typeof ref === 'object' && Number.isFinite(Number(ref.x))) {
      return { x: Number(ref.x) || 0, y: Number(ref.y) || 0, z: Number(ref.z) || 0 };
    }
    if (typeof ref === 'string') {
      if (ctx.scene) {
        const fromScene = ctx.scene.anchor(ref);
        if (fromScene) return fromScene;
      }
      if (ctx.feature) {
        const named = World.anchor(ctx.feature, ref.includes('.') ? ref.split('.')[1] : ref);
        if (named) return named;
      }
    }
    return ctx.feature ? World.anchor(ctx.feature, fallbackName) : null;
  }

  /** Puts a body on the ground at a place, facing a direction. */
  function stand(p, at, yaw, groundY) {
    p.yaw = Number(yaw) || 0;
    p.origin.x = (at && Number(at.x)) || 0;
    p.origin.z = (at && Number(at.z)) || 0;
    p.origin.y = pelvisLift(p.proportion, p.pose) * p.scale + (Number(groundY) || 0);
    return p;
  }

  /**
   * Which hand a body would actually use for a point in the world. Asking
   * for the right hand is asking for a cross-body reach whenever the thing
   * is on the other side, and that is what a 14%-of-height residual looks
   * like: an arm stretched across the chest, not a shelf being used.
   */
  const nearerSide = (p, point, preferred) => {
    if (preferred === 'left' || preferred === 'right') return preferred;
    return toLocal(point, p).x >= 0 ? 'right' : 'left';
  };

  const worldJoint = (p, name) => {
    const j = Contact.joints(p.proportion, p.pose);
    return toWorld(j[name], p);
  };

  /**
   * Drops the feet to the floor from a seat. A seated body cannot go through
   * the contact solver — the knee angle a chair needs is outside the standing
   * range it is allowed to search — so the two unknowns, thigh slope and shin
   * angle, are fitted directly. A stool too tall for the body leaves the feet
   * hanging and says so in the residual rather than stretching the legs.
   */
  function fitSeatedLegs(p, seatY, groundY) {
    const posed = (hip, knee) => Rig.mergePose({
      ...p.pose,
      legLeft: { ...p.pose.legLeft, hip: { ...p.pose.legLeft.hip, tilt: hip }, knee: { ...p.pose.legLeft.knee, tilt: knee } },
      legRight: { ...p.pose.legRight, hip: { ...p.pose.legRight.hip, tilt: hip }, knee: { ...p.pose.legRight.knee, tilt: knee } }
    });
    const errorOf = (hip, knee) => {
      const pose = posed(hip, knee);
      const j = Contact.joints(p.proportion, pose);
      const low = Math.min(j.leftToe.y, j.rightToe.y, j.leftAnkle.y, j.rightAnkle.y);
      return { pose, hip, knee, error: Math.abs(seatY + low * p.scale - groundY) };
    };

    let best = errorOf(82, -80);
    // Thigh slope first, then shin: coarse sweep, then a local refinement, so
    // the fit is deterministic and does not depend on a starting guess.
    for (let hip = 68; hip <= 94; hip += 2) {
      for (let knee = -108; knee <= -46; knee += 2) {
        const candidate = errorOf(hip, knee);
        if (candidate.error < best.error) best = candidate;
      }
    }
    for (let hip = best.hip - 2; hip <= best.hip + 2; hip += 0.5) {
      for (let knee = best.knee - 2; knee <= best.knee + 2; knee += 0.5) {
        const candidate = errorOf(hip, knee);
        if (candidate.error < best.error) best = candidate;
      }
    }
    p.pose = best.pose;
    return best.error;
  }

  /** Sits a body on a seat the world described, feet on the floor. */
  function sitOn(spec) {
    const ctx = staging(spec, 'chair');
    const actor = participant({ id: 'actor', ...(spec.actor || {}) }, 1);
    const seat = pointOf(ctx, spec.at || spec.seat, 'seat') || { x: 0, y: 0.26, z: 0 };
    const groundY = ctx.ground.height(seat.x);

    actor.yaw = Number.isFinite(Number(spec.yaw)) ? Number(spec.yaw) : (ctx.feature ? ctx.feature.facing : 0);
    actor.pose = Rig.mergePose({
      seated: true,
      spine: { tilt: Number(spec.lean) || 4, swing: 0 },
      chest: { tilt: 2, swing: 0 },
      // Thighs along the seat; the shin angle is fitted to the floor below.
      legLeft: { hip: { tilt: 82, swing: 6 }, knee: { tilt: -80, swing: 0 }, ankle: { tilt: 0 } },
      legRight: { hip: { tilt: 82, swing: 6 }, knee: { tilt: -80, swing: 0 }, ankle: { tilt: 0 } },
      armLeft: { shoulder: { tilt: 18, swing: 8 }, elbow: { tilt: 44, swing: 0 } },
      armRight: { shoulder: { tilt: 18, swing: 8 }, elbow: { tilt: 44, swing: 0 } }
    });

    actor.origin = { x: seat.x, y: seat.y, z: seat.z };
    const footError = fitSeatedLegs(actor, seat.y, groundY);

    // Hands: on the thighs by default, or wherever the beat puts them.
    const hands = [];
    if (spec.hands && spec.hands !== 'lap') {
      for (const goal of [].concat(spec.hands)) {
        const at = pointOf(ctx, goal.at || goal, 'top');
        if (at) hands.push({ effector: goal.effector || 'rightHand', at });
      }
    }
    if (hands.length) solveAgainst(actor, hands, { torso: true });

    const seated = Contact.joints(actor.proportion, actor.pose);
    const contacts = [
      { between: ['actor.pelvis', `${ctx.feature ? ctx.feature.id : 'seat'}.seat`], at: seat, error: 0 },
      ...['left', 'right'].map((side) => ({ between: [`actor.${side}Foot`, 'ground'], at: toWorld(seated[`${side}Toe`], actor), error: footError }))
    ];
    actor.residual = Math.max(actor.residual || 0, footError);
    return compose('sit-on', [actor], spec, contacts.concat(actor.goals.map((g) => ({ between: [`actor.${g.effector}`], at: g.at, error: g.error }))), ['three-quarter-right', 'profile-right']);
  }

  /** A forearm or hand resting on a counter, weight on the far leg. */
  function leanOn(spec) {
    const ctx = staging(spec, 'counter');
    const actor = participant({ id: 'actor', ...(spec.actor || {}) }, 1);
    const side = spec.side === 'left' ? 'left' : 'right';
    const edge = pointOf(ctx, spec.at, 'edge') || { x: 0, y: 0.55, z: 0 };
    const post = ctx.feature ? World.approach(ctx.feature, { offset: side === 'right' ? -0.2 : 0.2, gap: (ctx.feature.metrics.depth / 2) + 0.14 }) : { at: { x: side === 'right' ? -0.2 : 0.2, z: 0.26 }, yaw: 180 };

    actor.pose = Rig.mergePose({
      spine: { tilt: 6, swing: side === 'right' ? 5 : -5 },
      chest: { tilt: 3, swing: 0 },
      hipRoll: side === 'right' ? -5 : 5,
      // Weight on the leg away from the surface: the lean has to come from
      // somewhere or the figure reads as standing beside the counter.
      legLeft: { hip: { tilt: side === 'right' ? -4 : 3, swing: 4 }, knee: { tilt: 3, swing: 0 } },
      legRight: { hip: { tilt: side === 'right' ? 3 : -4, swing: 4 }, knee: { tilt: 3, swing: 0 } }
    });
    stand(actor, post.at, Number.isFinite(Number(spec.yaw)) ? Number(spec.yaw) : post.yaw, ctx.ground.height(post.at.x));
    solveAgainst(actor, [{ effector: `${side}Hand`, at: edge }], { torso: true });
    return compose('lean-on', [actor], spec, [{ between: [`actor.${side}Hand`, ctx.feature ? `${ctx.feature.id}.edge` : 'surface'], at: edge, error: actor.residual }], ['three-quarter-right', 'profile-right']);
  }

  /** Reaching a point the world named: a shelf, a handle, a board. */
  function reachTo(spec) {
    const ctx = staging(spec, 'shelf');
    const actor = participant({ id: 'actor', ...(spec.actor || {}) }, 1);
    const target = pointOf(ctx, spec.at, ctx.feature && ctx.feature.metrics.role === 'wall' ? 'face' : 'edge') || { x: 0.2, y: 0.9, z: 0.2 };
    const post = ctx.feature ? World.approach(ctx.feature, { offset: Number(spec.offset) || 0, gap: Number(spec.gap) || ((ctx.feature.metrics.depth / 2) + 0.16) }) : { at: { x: 0, z: 0 }, yaw: 0 };

    actor.pose = Rig.mergePose(spec.pose || {});
    stand(actor, post.at, Number.isFinite(Number(spec.yaw)) ? Number(spec.yaw) : post.yaw, ctx.ground.height(post.at.x));
    const side = nearerSide(actor, target, spec.side);

    // A high shelf is taken on the toes; a low one is not.
    const shoulder = worldJoint(actor, `${side}Shoulder`).y;
    if (target.y > shoulder + 0.12) {
      actor.pose = Rig.mergePose({ ...actor.pose, legLeft: { ...actor.pose.legLeft, ankle: { tilt: 22 } }, legRight: { ...actor.pose.legRight, ankle: { tilt: 22 } }, spine: { tilt: -4, swing: actor.pose.spine.swing } });
      stand(actor, post.at, actor.yaw, ctx.ground.height(post.at.x));
    }

    solveAgainst(actor, [{ effector: `${side}Hand`, at: target }], { torso: true });
    if (spec.propId && Props.PROPS[spec.propId]) actor.props = [{ id: spec.propId, side }];
    return compose('reach-to', [actor], spec, [{ between: [`actor.${side}Hand`, ctx.feature ? ctx.feature.id : 'target'], at: target, error: actor.residual }], ['three-quarter-right', 'profile-right']);
  }

  /** Both hands down on a table, head over the work. */
  function workAtTable(spec) {
    const ctx = staging(spec, 'table');
    const actor = participant({ id: 'actor', ...(spec.actor || {}) }, 1);
    const left = pointOf(ctx, spec.leftAt, 'left');
    const right = pointOf(ctx, spec.rightAt, 'right');
    const post = ctx.feature ? World.approach(ctx.feature, { offset: Number(spec.offset) || 0, gap: (ctx.feature.metrics.depth / 2) + 0.1 }) : { at: { x: 0, z: 0.26 }, yaw: 180 };

    actor.pose = Rig.mergePose({
      spine: { tilt: 12, swing: 0 },
      chest: { tilt: 6, swing: 0 },
      neck: { tilt: -14, swing: 0 },
      head: { yaw: 0, pitch: -12 }
    });
    stand(actor, post.at, Number.isFinite(Number(spec.yaw)) ? Number(spec.yaw) : post.yaw, ctx.ground.height(post.at.x));
    // The anchors are the table's left and right; which hand that is depends
    // on which side of the table the body was placed on, and getting it wrong
    // crosses the arms over the work.
    const goals = [];
    if (right) goals.push({ effector: `${nearerSide(actor, right)}Hand`, at: right });
    if (left) goals.push({ effector: `${nearerSide(actor, left)}Hand`, at: left });
    if (goals.length === 2 && goals[0].effector === goals[1].effector) goals[1].effector = goals[0].effector === 'rightHand' ? 'leftHand' : 'rightHand';
    solveAgainst(actor, goals, { torso: true });
    if (spec.propId && Props.PROPS[spec.propId]) actor.props = [{ id: spec.propId, side: spec.side }];
    return compose('work-at-table', [actor], spec, actor.goals.map((g) => ({ between: [`actor.${g.effector}`, ctx.feature ? `${ctx.feature.id}.top` : 'surface'], at: g.at, error: g.error })), ['three-quarter-right', 'front']);
  }

  /**
   * Down on one knee: the back shin folded flat on the floor, the front foot
   * fitted to the same level. Like sitting, this is authored rather than
   * solved, because a folded knee is outside the standing joint range.
   */
  function kneelPose(p, side) {
    const back = side === 'left' ? 'legRight' : 'legLeft';
    const front = side === 'left' ? 'legLeft' : 'legRight';
    const base = Rig.mergePose({
      ...p.pose,
      spine: { tilt: 14, swing: 0 },
      chest: { tilt: 6, swing: 0 },
      neck: { tilt: -12, swing: 0 },
      crouch: 0,
      [back]: { hip: { tilt: 2, swing: 4 }, knee: { tilt: -92, swing: 0 }, ankle: { tilt: -20 } },
      [front]: { hip: { tilt: 62, swing: 8 }, knee: { tilt: -70, swing: 0 }, ankle: { tilt: 0 } }
    });
    const floor = Contact.joints(p.proportion, base)[`${back === 'legLeft' ? 'left' : 'right'}Knee`].y;
    const frontSide = front === 'legLeft' ? 'left' : 'right';
    // Both front-leg angles are searched: with the thigh angle fixed, the
    // shin can only reach the floor plane the back knee defines by accident,
    // and the foot ends up planted below the knee it kneels on.
    const errorOf = (hip, knee) => {
      const pose = Rig.mergePose({ ...base, [front]: { hip: { tilt: hip, swing: 8 }, knee: { tilt: knee, swing: 0 }, ankle: { tilt: 0 } } });
      const j = Contact.joints(p.proportion, pose);
      const ankle = j[`${frontSide}Ankle`].y;
      const toe = j[`${frontSide}Toe`].y;
      // The sole is flat on the same floor as the kneeling shin, and the
      // shin stays roughly upright so the pose reads as a knee, not a squat.
      const upright = Math.abs(j[`${frontSide}Knee`].z - j[`${frontSide}Ankle`].z) * 0.3;
      return { pose, hip, knee, error: Math.abs(toe - floor) + Math.abs(ankle - floor) + upright };
    };
    let best = errorOf(62, -70);
    for (let hip = 30; hip <= 86; hip += 2) {
      for (let knee = -120; knee <= -20; knee += 2) {
        const candidate = errorOf(hip, knee);
        if (candidate.error < best.error) best = candidate;
      }
    }
    for (let hip = best.hip - 2; hip <= best.hip + 2; hip += 0.5) {
      for (let knee = best.knee - 2; knee <= best.knee + 2; knee += 0.5) {
        const candidate = errorOf(hip, knee);
        if (candidate.error < best.error) best = candidate;
      }
    }
    return best.pose;
  }

  /** Crouching to a low point and taking hold of it. */
  function pickUp(spec) {
    const ctx = staging(spec, null);
    const actor = participant({ id: 'actor', ...(spec.actor || {}) }, 1);
    const target = pointOf(ctx, spec.at, 'under') || { x: 0.1, y: 0.06, z: 0.22 };
    const hands = spec.hands === 1 ? 1 : 2;
    const side = spec.side === 'left' ? 'left' : 'right';

    // How far down the body has to go is a fact about the target, not a style
    // choice: a crate at knee height is a stoop, a coin on the floor is a
    // squat. The crouch is fitted so the shoulders end up about an arm above
    // the object — the difference between reaching it and pawing the air.
    const arm = actor.proportion.upperArm + actor.proportion.foreArm + actor.proportion.hand;
    const fit = (crouch) => {
      const pose = Rig.mergePose({ crouch, spine: { tilt: 14 + crouch * 16, swing: 0 }, chest: { tilt: 6, swing: 0 }, neck: { tilt: -10, swing: 0 } });
      const lift = pelvisLift(actor.proportion, pose) * actor.scale + ctx.ground.height(target.x);
      const j = Contact.joints(actor.proportion, pose);
      const shoulder = lift + Math.min(j.leftShoulder.y, j.rightShoulder.y) * actor.scale;
      return { pose, error: Math.abs(shoulder - (target.y + arm * 0.84 * actor.scale)) };
    };
    let best = fit(0);
    for (let c = 0; c <= 1.0001; c += 0.02) {
      const candidate = fit(c);
      if (candidate.error < best.error) best = candidate;
    }
    // Below a squat's reach the body stops squatting and goes down on a knee,
    // which is what people actually do for something on the floor.
    const kneeling = spec.kneel === true || (spec.kneel !== false && best.pose.crouch >= 0.999 && best.error > 0.06);
    actor.pose = kneeling ? kneelPose(actor, side) : best.pose;
    stand(actor, { x: target.x, z: target.z - (kneeling ? 0.1 : 0.18) }, Number(spec.yaw) || 0, ctx.ground.height(target.x));

    const spread = Number(spec.spread) || 0.06;
    const goals = hands === 2
      ? [{ effector: 'rightHand', at: { ...target, x: target.x + spread } }, { effector: 'leftHand', at: { ...target, x: target.x - spread } }]
      : [{ effector: `${side}Hand`, at: target }];
    solveAgainst(actor, goals, { torso: true });
    if (spec.propId && Props.PROPS[spec.propId]) actor.props = [{ id: spec.propId, side }];
    return compose('pick-up', [actor], spec, actor.goals.map((g) => ({ between: [`actor.${g.effector}`, spec.propId || 'object'], at: g.at, error: g.error })), ['three-quarter-right', 'profile-right']);
  }

  /** Setting something down on a surface the world described. */
  function placeOn(spec) {
    const ctx = staging(spec, 'table');
    const actor = participant({ id: 'actor', ...(spec.actor || {}) }, 1);
    const target = pointOf(ctx, spec.at, 'top') || { x: 0, y: 0.43, z: 0 };
    const post = ctx.feature ? World.approach(ctx.feature, { offset: Number(spec.offset) || 0, gap: (ctx.feature.metrics.depth / 2) + 0.14 }) : { at: { x: 0, z: 0.3 }, yaw: 180 };
    const spread = Number(spec.spread) || 0.05;

    actor.pose = Rig.mergePose({ spine: { tilt: 10, swing: 0 }, chest: { tilt: 5, swing: 0 }, neck: { tilt: -10, swing: 0 } });
    stand(actor, post.at, Number.isFinite(Number(spec.yaw)) ? Number(spec.yaw) : post.yaw, ctx.ground.height(post.at.x));
    solveAgainst(actor, [
      { effector: 'rightHand', at: { x: target.x + spread, y: target.y + 0.02, z: target.z } },
      { effector: 'leftHand', at: { x: target.x - spread, y: target.y + 0.02, z: target.z } }
    ], { torso: true });
    if (spec.propId && Props.PROPS[spec.propId]) actor.props = [{ id: spec.propId, side: spec.side }];
    return compose('place-on', [actor], spec, actor.goals.map((g) => ({ between: [`actor.${g.effector}`, ctx.feature ? `${ctx.feature.id}.top` : 'surface'], at: g.at, error: g.error })), ['three-quarter-right', 'profile-right']);
  }

  /** Two bodies placed facing one another across a gap, both angled to camera. */
  function facingPair(spec, ids) {
    const gap = typeof spec.gap === 'number' ? spec.gap : 0.52;
    const turn = typeof spec.turn === 'number' ? spec.turn : 62;
    const a = participant({ id: ids[0], role: ids[0], ...(spec[ids[0]] || {}) }, 1);
    const primaryStature = a.proportion.stature || 1;
    const b = participant({ id: ids[1], role: ids[1], ...(spec[ids[1]] || {}) }, primaryStature);
    a.pose = Rig.mergePose({ ...a.pose, head: { yaw: 10, pitch: 0 } });
    b.pose = Rig.mergePose({ ...b.pose, head: { yaw: -10, pitch: 0 } });
    stand(a, { x: -gap / 2, z: 0 }, turn, 0);
    stand(b, { x: gap / 2, z: 0 }, -turn, 0);
    return { a, b };
  }

  /** Something passes from one pair of hands to another. */
  function handOver(spec) {
    const { a: giver, b: receiver } = facingPair(spec, ['giver', 'receiver']);
    const giverHand = spec.giverHand || 'leftHand';
    const receiverHand = spec.receiverHand || 'rightHand';

    // The exchange happens between the two chests, at the height of the
    // shorter body so the smaller pair of arms is not asked for a miracle.
    const height = Math.min(worldJoint(giver, 'chest').y, worldJoint(receiver, 'chest').y);
    const meet = { x: (giver.origin.x + receiver.origin.x) / 2, y: height * 0.94, z: 0.08 };
    solveAgainst(giver, [{ effector: giverHand, at: meet }], { torso: true });
    solveAgainst(receiver, [{ effector: receiverHand, at: meet }], { torso: true });
    if (spec.propId && Props.PROPS[spec.propId]) giver.props = [{ id: spec.propId, side: giverHand.startsWith('left') ? 'left' : 'right' }];
    return compose('hand-over', [giver, receiver], spec, [{ between: [`giver.${giverHand}`, `receiver.${receiverHand}`], at: meet, error: Math.max(giver.residual || 0, receiver.residual || 0) }], ['front', 'three-quarter-right']);
  }

  /** Right hands meet: same solve, a firmer height, both bodies leaning in. */
  function shakeHands(spec) {
    const { a, b } = facingPair({ gap: 0.58, ...spec }, ['first', 'second']);
    const height = Math.min(worldJoint(a, 'chest').y, worldJoint(b, 'chest').y);
    const meet = { x: (a.origin.x + b.origin.x) / 2, y: height * 0.8, z: 0.06 };
    solveAgainst(a, [{ effector: 'rightHand', at: meet }], { torso: true });
    solveAgainst(b, [{ effector: 'rightHand', at: meet }], { torso: true });
    return compose('shake-hands', [a, b], spec, [{ between: ['first.rightHand', 'second.rightHand'], at: meet, error: Math.max(a.residual || 0, b.residual || 0) }], ['front', 'three-quarter-right']);
  }

  /**
   * Walking hand in hand. Unlike `support-walk` this is two bodies of any
   * size side by side, so the join lands at whichever hand is lower.
   */
  function holdHands(spec) {
    const gap = typeof spec.gap === 'number' ? spec.gap : 0.34;
    const left = participant({ id: 'left', role: 'left', ...(spec.left || {}) }, 1);
    const primaryStature = left.proportion.stature || 1;
    const right = participant({ id: 'right', role: 'right', ...(spec.right || {}) }, primaryStature);
    const yaw = Number(spec.yaw) || 0;
    stand(left, { x: -gap / 2, z: 0 }, yaw, 0);
    stand(right, { x: gap / 2, z: 0 }, yaw, 0);

    // The join sits below the shorter body's shoulder: hand in hand with a
    // child means the adult's arm comes down, not the child's arm stretched
    // up to adult height.
    const shoulder = Math.min(worldJoint(left, 'rightShoulder').y, worldJoint(right, 'leftShoulder').y);
    const meet = { x: 0, y: shoulder * 0.86, z: 0.06 };
    solveAgainst(left, [{ effector: 'rightHand', at: meet }], { torso: true });
    solveAgainst(right, [{ effector: 'leftHand', at: meet }], { torso: true });
    return compose('hold-hands', [left, right], spec, [{ between: ['left.rightHand', 'right.leftHand'], at: meet, error: Math.max(left.residual || 0, right.residual || 0) }], ['front', 'three-quarter-right']);
  }

  function compose(name, participants, spec, contacts, preferredViews) {
    const unit = Number(spec && spec.height) || 1000;
    return {
      relation: name,
      unit,
      preferredViews: preferredViews || null,
      participants: participants.map((p) => ({
        id: p.id,
        role: p.role,
        proportion: p.proportion,
        pose: p.pose,
        scale: p.scale,
        yaw: p.yaw,
        origin: p.origin,
        props: p.props || null,
        height: unit * p.scale,
        // Stage placement in pixels, ground at y = 0, for the scene renderer.
        stage: { x: p.origin.x * unit, y: p.origin.y * unit, depth: p.origin.z * unit },
        residual: p.residual || 0,
        goals: p.goals || []
      })),
      contacts: contacts || participants.flatMap((p) => (p.goals || []).map((g) => ({ between: [`${p.id}.${g.effector}`], at: g.at, error: g.error }))),
      residual: participants.reduce((m, p) => Math.max(m, p.residual || 0), 0)
    };
  }

  const RELATIONS = {
    'carry-on-back': carryOnBack,
    'support-walk': supportWalk,
    'grip-prop': gripProp,
    'sit-on': sitOn,
    'lean-on': leanOn,
    'reach-to': reachTo,
    'work-at-table': workAtTable,
    'pick-up': pickUp,
    'place-on': placeOn,
    'hand-over': handOver,
    'shake-hands': shakeHands,
    'hold-hands': holdHands
  };

  function relate(name, spec) {
    const fn = RELATIONS[name];
    if (!fn) throw new Error(`unknown relation: ${name}`);
    return fn(spec || {});
  }

  return { relate, RELATIONS, toWorld, toLocal, pelvisLift, staging, pointOf };
});
