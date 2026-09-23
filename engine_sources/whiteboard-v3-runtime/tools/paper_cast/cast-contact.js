/**
 * NexStudio Paper Cast — contact solver
 *
 * A beat states where the body touches the world — "right hand on the oar
 * shaft", "left foot on the canoe floor", "both hands under the child" — and
 * this solves the joint angles that put it there. Poses stop being a closed
 * catalogue: the named poses become starting points, and anything a story asks
 * for is expressed as contact goals against props and other characters.
 *
 *   const pose = NexCastContact.solve({
 *     proportion: NexCastBody.body({ age: 30 }),
 *     pose: basePose,
 *     goals: [{ effector: 'rightHand', at: { x: 0.14, y: 0.52, z: 0.3 } }]
 *   });
 *
 * Goal positions are in body-local units: fractions of the figure's height,
 * measured from the pelvis, +y up, +z forward (the direction the body faces),
 * +x to the character's right.
 */
(function (root, factory) {
  const rig = typeof module === 'object' && module.exports ? require('./paper-cast-rig.js') : root.NexPaperCastRig;
  const api = factory(rig);
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastContact = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Rig) {
  const RAD = Math.PI / 180;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  const add = (a, b, k) => ({ x: a.x + b.x * k, y: a.y + b.y * k, z: a.z + b.z * k });
  const dirDown = (tilt, swing) => {
    const t = tilt * RAD;
    const s = swing * RAD;
    return { x: Math.cos(t) * Math.sin(s), y: -Math.cos(t) * Math.cos(s), z: Math.sin(t) };
  };
  const dirUp = (tilt, swing) => {
    const t = tilt * RAD;
    const s = swing * RAD;
    return { x: Math.sin(s) * Math.cos(t), y: Math.cos(t) * Math.cos(s), z: Math.sin(t) };
  };

  /**
   * Body-local forward kinematics, in the same construction order as the rig.
   * The rig projects through a view yaw; contact is solved before that, so a
   * grip does not change when the camera moves round the figure.
   */
  function joints(proportion, pose) {
    const L = (key) => proportion[key];
    const crouch = clamp(pose.crouch || 0, 0, 1);
    const pelvis = { x: 0, y: 0, z: 0 };
    const spineDir = dirUp(pose.spine.tilt, pose.spine.swing);
    const chest = add(pelvis, spineDir, L('chest') * (1 - crouch * 0.08));
    const chestDir = dirUp(pose.spine.tilt + pose.chest.tilt, pose.spine.swing + pose.chest.swing);
    const neck = add(chest, chestDir, L('neck'));
    const headDir = dirUp(pose.spine.tilt + pose.chest.tilt + pose.neck.tilt, pose.spine.swing + pose.chest.swing + pose.neck.swing);
    const head = add(neck, headDir, L('head') * 1.15);

    const lateral = (half, roll, sign) => ({ x: sign * half * Math.cos(roll * RAD), y: sign * half * Math.sin(roll * RAD), z: 0 });
    const out = { pelvis, chest, neck, head };

    for (const side of ['left', 'right']) {
      const sign = side === 'right' ? 1 : -1;
      const arm = side === 'right' ? pose.armRight : pose.armLeft;
      const leg = side === 'right' ? pose.legRight : pose.legLeft;

      const so = lateral(L('shoulderWidth'), pose.shoulderRoll, sign);
      const shoulder = { x: chest.x + so.x, y: chest.y + so.y + L('neck') * 0.35, z: chest.z };
      const upper = dirDown(arm.shoulder.tilt, sign * arm.shoulder.swing);
      const elbow = add(shoulder, upper, L('upperArm'));
      const fore = dirDown(arm.shoulder.tilt + arm.elbow.tilt, sign * (arm.shoulder.swing + arm.elbow.swing));
      const wrist = add(elbow, fore, L('foreArm'));
      const hand = add(wrist, fore, L('hand'));

      const ho = lateral(L('pelvisWidth'), pose.hipRoll, sign);
      const hip = { x: pelvis.x + ho.x, y: pelvis.y + ho.y, z: pelvis.z };
      const thigh = dirDown(leg.hip.tilt - crouch * 45, sign * leg.hip.swing);
      const knee = add(hip, thigh, L('thigh'));
      const shin = dirDown(leg.hip.tilt - crouch * 45 + leg.knee.tilt + crouch * 85, sign * (leg.hip.swing + leg.knee.swing));
      const ankle = add(knee, shin, L('shin'));
      const toe = add(ankle, dirDown(leg.ankle.tilt + 90, sign * leg.knee.swing * 0.3), L('foot'));

      out[side + 'Shoulder'] = shoulder;
      out[side + 'Elbow'] = elbow;
      out[side + 'Wrist'] = wrist;
      out[side + 'Hand'] = hand;
      out[side + 'Hip'] = hip;
      out[side + 'Knee'] = knee;
      out[side + 'Ankle'] = ankle;
      out[side + 'Toe'] = toe;
      out[side + 'Foot'] = toe;
    }
    return out;
  }

  /** Which angles an effector is allowed to move, and how far each may travel. */
  const CHAINS = {
    rightHand: 'armRight',
    rightWrist: 'armRight',
    rightElbow: 'armRight',
    leftHand: 'armLeft',
    leftWrist: 'armLeft',
    leftElbow: 'armLeft',
    rightFoot: 'legRight',
    rightToe: 'legRight',
    rightAnkle: 'legRight',
    rightKnee: 'legRight',
    leftFoot: 'legLeft',
    leftToe: 'legLeft',
    leftAnkle: 'legLeft',
    leftKnee: 'legLeft'
  };

  const LIMITS = {
    'armRight.shoulder.tilt': [-95, 175],
    'armRight.shoulder.swing': [-48, 170],
    'armRight.elbow.tilt': [-10, 150],
    'armRight.elbow.swing': [-30, 50],
    'armLeft.shoulder.tilt': [-95, 175],
    'armLeft.shoulder.swing': [-48, 170],
    'armLeft.elbow.tilt': [-10, 150],
    'armLeft.elbow.swing': [-30, 50],
    'legRight.hip.tilt': [-70, 105],
    'legRight.hip.swing': [-12, 45],
    'legRight.knee.tilt': [-5, 130],
    'legRight.knee.swing': [-8, 18],
    'legRight.ankle.tilt': [-35, 40],
    'legLeft.hip.tilt': [-70, 105],
    'legLeft.hip.swing': [-12, 45],
    'legLeft.knee.tilt': [-5, 130],
    'legLeft.knee.swing': [-8, 18],
    'legLeft.ankle.tilt': [-35, 40],
    'spine.tilt': [-25, 45],
    'spine.swing': [-18, 18],
    'chest.tilt': [-20, 35],
    'chest.swing': [-20, 20],
    'neck.tilt': [-30, 30],
    'neck.swing': [-25, 25]
  };

  const TORSO_PARAMS = ['spine.tilt', 'spine.swing', 'chest.tilt', 'chest.swing'];

  const paramsFor = (chain) => (chain.startsWith('arm')
    ? [`${chain}.shoulder.tilt`, `${chain}.shoulder.swing`, `${chain}.elbow.tilt`, `${chain}.elbow.swing`]
    // The ankle tilt is part of the chain: a foot goal is about where the foot
    // meets the ground, which the knee alone cannot decide.
    : [`${chain}.hip.tilt`, `${chain}.hip.swing`, `${chain}.knee.tilt`, `${chain}.knee.swing`, `${chain}.ankle.tilt`]);

  const readPath = (obj, path) => path.split('.').reduce((o, k) => (o == null ? o : o[k]), obj);

  function writePath(obj, path, value) {
    const keys = path.split('.');
    let node = obj;
    for (let i = 0; i < keys.length - 1; i += 1) {
      node[keys[i]] = { ...node[keys[i]] };
      node = node[keys[i]];
    }
    node[keys[keys.length - 1]] = value;
  }

  const distance2 = (a, b) => (a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2;

  /**
   * @param {object} spec `{ proportion, pose, goals, torso, iterations }`
   * @param {Array} spec.goals `[{ effector, at:{x,y,z}, weight }]`, positions in
   *   fractions of figure height relative to the pelvis
   * @returns {{pose:object, goals:Array, residual:number, reached:boolean}}
   */
  function solve(spec) {
    const s = spec || {};
    const proportion = Rig.resolveProportion(s.proportion);
    const base = Rig.mergePose(s.pose);
    const goals = (s.goals || []).filter((g) => g && g.effector && g.at);
    if (!goals.length) return { pose: base, goals: [], residual: 0, reached: true };

    const chains = new Set();
    for (const goal of goals) {
      const chain = CHAINS[goal.effector];
      if (chain) chains.add(chain);
    }
    const params = [...chains].flatMap(paramsFor);
    if (s.torso !== false) params.push(...TORSO_PARAMS);

    // Contact is authored in fractions of height; the rig's proportions are the
    // same units, so nothing has to know the pixel height here.
    const targets = goals.map((goal) => ({
      effector: goal.effector,
      weight: typeof goal.weight === 'number' ? goal.weight : 1,
      at: { x: Number(goal.at.x) || 0, y: Number(goal.at.y) || 0, z: Number(goal.at.z) || 0 }
    }));

    const cost = (pose) => {
      const j = joints(proportion, pose);
      let total = 0;
      for (const target of targets) {
        const point = j[target.effector] || j[target.effector.replace('Foot', 'Toe')];
        if (!point) continue;
        total += distance2(point, target.at) * target.weight;
      }
      // Stay near the authored pose so a reach borrows from the whole body
      // without discarding the performance it started from.
      for (const path of params) {
        // A parameter the rest pose never defines would poison the whole cost
        // with NaN and freeze the search, so read it as zero.
        const drift = ((readPath(pose, path) || 0) - (readPath(base, path) || 0)) / 90;
        total += drift * drift * 0.0016;
      }
      return total;
    };

    let pose = base;
    let best = cost(pose);
    const iterations = s.iterations || 5;
    let step = 28;
    for (let pass = 0; pass < iterations * params.length; pass += 1) {
      let improved = false;
      for (const path of params) {
        const limit = LIMITS[path] || [-180, 180];
        for (const direction of [1, -1]) {
          const next = { ...pose };
          const value = clamp((readPath(pose, path) || 0) + step * direction, limit[0], limit[1]);
          if (value === readPath(pose, path)) continue;
          writePath(next, path, value);
          const score = cost(next);
          if (score < best - 1e-9) {
            best = score;
            pose = next;
            improved = true;
            break;
          }
        }
      }
      if (!improved) {
        step /= 2;
        if (step < 0.2) break;
      }
    }

    const final = joints(proportion, pose);
    const reached = targets.map((target) => {
      const point = final[target.effector] || { x: 0, y: 0, z: 0 };
      return { effector: target.effector, error: Math.sqrt(distance2(point, target.at)), at: point };
    });
    const worst = reached.reduce((m, r) => Math.max(m, r.error), 0);

    return { pose, goals: reached, residual: worst, reached: worst <= (s.tolerance ?? 0.02) };
  }

  /**
   * A prop's contact anchors in body-local units, so a beat can say
   * `anchor(oar, 'grip-high')` instead of inventing coordinates per scene.
   */
  function anchor(prop, name) {
    const anchors = (prop && prop.anchors) || {};
    const point = anchors[name] || anchors[Object.keys(anchors)[0]];
    return point ? { x: Number(point.x) || 0, y: Number(point.y) || 0, z: Number(point.z) || 0 } : null;
  }

  return { solve, joints, anchor, CHAINS, LIMITS };
});
