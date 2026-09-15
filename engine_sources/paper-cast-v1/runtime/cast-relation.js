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
    ? { Rig: require('./paper-cast-rig.js'), Body: require('./cast-body.js'), Contact: require('./cast-contact.js'), Props: require('./cast-props.js') }
    : { Rig: root.NexPaperCastRig, Body: root.NexCastBody, Contact: root.NexCastContact, Props: root.NexCastProps };
  const api = factory(deps);
  if (isNode) module.exports = api;
  root.NexCastRelation = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function ({ Rig, Body, Contact, Props }) {
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
    const low = ['leftToe', 'rightToe', 'leftAnkle', 'rightAnkle'].reduce((m, key) => Math.min(m, j[key].y), 0);
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

  const RELATIONS = { 'carry-on-back': carryOnBack, 'support-walk': supportWalk, 'grip-prop': gripProp };

  function relate(name, spec) {
    const fn = RELATIONS[name];
    if (!fn) throw new Error(`unknown relation: ${name}`);
    return fn(spec || {});
  }

  return { relate, RELATIONS, toWorld, toLocal, pelvisLift };
});
