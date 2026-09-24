/**
 * NexStudio Paper Cast — rig
 *
 * A 2.5D paper rig: the figure is posed in body-local 3D, then projected to the
 * picture plane through a view yaw. Characters therefore hold any orientation
 * (front, three-quarter, profile, back) instead of always facing the camera,
 * and near/far limbs are separated by projected depth rather than by authoring.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexPaperCastRig = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const RAD = Math.PI / 180;
  const num = (v, fallback) => (Number.isFinite(Number(v)) ? Number(v) : fallback);

  const VIEW_AXES = {
    front: 0,
    'three-quarter-right': 38,
    'profile-right': 90,
    'back-right': 140,
    back: 180,
    'back-left': -140,
    'profile-left': -90,
    'three-quarter-left': -38
  };

  const PROPORTIONS = {
    'adult-average': { head: 0.066, neck: 0.03, chest: 0.2, pelvisWidth: 0.076, shoulderWidth: 0.107, thigh: 0.235, shin: 0.235, foot: 0.055, upperArm: 0.163, foreArm: 0.15, hand: 0.042, limb: 0.032, torsoTaper: 0.86, bodyDepth: 0.62 },
    'adult-broad': { head: 0.064, neck: 0.031, chest: 0.2, pelvisWidth: 0.09, shoulderWidth: 0.125, thigh: 0.231, shin: 0.231, foot: 0.058, upperArm: 0.166, foreArm: 0.152, hand: 0.044, limb: 0.039, torsoTaper: 0.94, bodyDepth: 0.68 },
    'adult-slight': { head: 0.066, neck: 0.03, chest: 0.198, pelvisWidth: 0.068, shoulderWidth: 0.096, thigh: 0.24, shin: 0.24, foot: 0.052, upperArm: 0.162, foreArm: 0.15, hand: 0.04, limb: 0.027, torsoTaper: 0.8, bodyDepth: 0.58 },
    'adult-tall': { head: 0.061, neck: 0.032, chest: 0.202, pelvisWidth: 0.072, shoulderWidth: 0.104, thigh: 0.248, shin: 0.248, foot: 0.055, upperArm: 0.168, foreArm: 0.156, hand: 0.042, limb: 0.029, torsoTaper: 0.83, bodyDepth: 0.6 },
    teen: { head: 0.072, neck: 0.028, chest: 0.19, pelvisWidth: 0.068, shoulderWidth: 0.094, thigh: 0.228, shin: 0.228, foot: 0.05, upperArm: 0.155, foreArm: 0.142, hand: 0.04, limb: 0.028, torsoTaper: 0.82, bodyDepth: 0.58 },
    child: { head: 0.093, neck: 0.024, chest: 0.175, pelvisWidth: 0.062, shoulderWidth: 0.082, thigh: 0.198, shin: 0.198, foot: 0.046, upperArm: 0.135, foreArm: 0.122, hand: 0.038, limb: 0.03, torsoTaper: 0.9, bodyDepth: 0.64 },
    senior: { head: 0.066, neck: 0.028, chest: 0.193, pelvisWidth: 0.08, shoulderWidth: 0.1, thigh: 0.226, shin: 0.226, foot: 0.055, upperArm: 0.158, foreArm: 0.146, hand: 0.042, limb: 0.031, torsoTaper: 0.88, bodyDepth: 0.66 }
  };

  const REST = {
    spine: { tilt: 0, swing: 0 },
    chest: { tilt: 0, swing: 0 },
    neck: { tilt: 0, swing: 0 },
    head: { yaw: 0, pitch: 0 },
    shoulderRoll: 0,
    hipRoll: 0,
    arms: { left: { shoulder: { tilt: 2, swing: 7 }, elbow: { tilt: 6, swing: 3 } }, right: { shoulder: { tilt: 2, swing: 7 }, elbow: { tilt: 6, swing: 3 } } },
    legs: { left: { hip: { tilt: 0, swing: 3 }, knee: { tilt: 2, swing: 0 }, ankle: { tilt: 0 } }, right: { hip: { tilt: 0, swing: 3 }, knee: { tilt: 2, swing: 0 }, ankle: { tilt: 0 } } }
  };

  function mergePose(pose) {
    const p = pose || {};
    const side = (key, rest) => ({
      shoulder: { tilt: num(p[key]?.shoulder?.tilt, rest.shoulder.tilt), swing: num(p[key]?.shoulder?.swing, rest.shoulder.swing) },
      elbow: { tilt: num(p[key]?.elbow?.tilt, rest.elbow.tilt), swing: num(p[key]?.elbow?.swing, rest.elbow.swing) }
    });
    const leg = (key, rest) => ({
      hip: { tilt: num(p[key]?.hip?.tilt, rest.hip.tilt), swing: num(p[key]?.hip?.swing, rest.hip.swing) },
      knee: { tilt: num(p[key]?.knee?.tilt, rest.knee.tilt), swing: num(p[key]?.knee?.swing, rest.knee.swing) },
      ankle: { tilt: num(p[key]?.ankle?.tilt, rest.ankle.tilt) }
    });
    return {
      spine: { tilt: num(p.spine?.tilt, REST.spine.tilt), swing: num(p.spine?.swing, REST.spine.swing) },
      chest: { tilt: num(p.chest?.tilt, REST.chest.tilt), swing: num(p.chest?.swing, REST.chest.swing) },
      neck: { tilt: num(p.neck?.tilt, REST.neck.tilt), swing: num(p.neck?.swing, REST.neck.swing) },
      head: { yaw: num(p.head?.yaw, REST.head.yaw), pitch: num(p.head?.pitch, REST.head.pitch) },
      shoulderRoll: num(p.shoulderRoll, REST.shoulderRoll),
      hipRoll: num(p.hipRoll, REST.hipRoll),
      crouch: num(p.crouch, 0),
      seated: !!p.seated,
      armLeft: side('armLeft', REST.arms.left),
      armRight: side('armRight', REST.arms.right),
      legLeft: leg('legLeft', REST.legs.left),
      legRight: leg('legRight', REST.legs.right)
    };
  }

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

  function resolveYaw(view) {
    if (typeof view === 'number') return view;
    if (view && typeof view === 'object') return resolveYaw(view.viewAxis ?? view.yaw);
    if (typeof view === 'string' && view in VIEW_AXES) return VIEW_AXES[view];
    return 0;
  }

  function nearestViewAxis(yaw) {
    const wrapped = ((Number(yaw) || 0) + 540) % 360 - 180;
    let best = 'front';
    let bestDelta = Infinity;
    for (const [name, value] of Object.entries(VIEW_AXES)) {
      const delta = Math.abs(((wrapped - value + 540) % 360) - 180);
      if (delta < bestDelta) {
        bestDelta = delta;
        best = name;
      }
    }
    return best;
  }

  /**
   * Builds the posed figure in screen space.
   * Returned joints carry `depth`: positive is nearer the camera, which is what
   * the renderer sorts on so the far arm and far leg fall behind the torso.
   */
  function resolveProportion(spec) {
    if (spec && typeof spec === 'object') return { ...PROPORTIONS['adult-average'], ...spec };
    return PROPORTIONS[spec] || PROPORTIONS['adult-average'];
  }

  function build(options) {
    const opts = options || {};
    const proportion = resolveProportion(opts.proportion);
    const pose = mergePose(opts.pose);
    const height = num(opts.height, 1000);
    const yaw = resolveYaw(opts.view ?? opts.viewAxis ?? 0);
    const cos = Math.cos(yaw * RAD);
    const sin = Math.sin(yaw * RAD);
    const L = (key) => proportion[key] * height;
    const crouch = Math.max(0, Math.min(1, pose.crouch));

    const pelvis = { x: 0, y: 0, z: 0 };
    const hipHalf = L('pelvisWidth');
    const shoulderHalf = L('shoulderWidth');

    const spineDir = dirUp(pose.spine.tilt, pose.spine.swing);
    const chestPoint = add(pelvis, spineDir, L('chest') * (1 - crouch * 0.08));
    const chestDir = dirUp(pose.spine.tilt + pose.chest.tilt, pose.spine.swing + pose.chest.swing);
    const neck = add(chestPoint, chestDir, L('neck'));
    const headDir = dirUp(pose.spine.tilt + pose.chest.tilt + pose.neck.tilt, pose.spine.swing + pose.chest.swing + pose.neck.swing);
    const headCenter = add(neck, headDir, L('head') * 1.15);

    // A heavy body is wider at the waist than at the shoulders, so an arm
    // hung straight down disappears into the belly. Weight pushes the arms
    // out; the amount is part of the body, so contact solving sees it too.
    const spill = Math.min(Math.max((num(proportion.waist, 1) - 1) * 30, 0), 20);

    const lateral = (half, roll, sign) => {
      const r = roll * RAD;
      return { x: sign * half * Math.cos(r), y: sign * half * Math.sin(r), z: 0 };
    };

    const joints = { pelvis, chest: chestPoint, neck, head: headCenter };
    const segments = [];

    const limbSide = (side) => {
      const sign = side === 'right' ? 1 : -1;
      const armPose = side === 'right' ? pose.armRight : pose.armLeft;
      const legPose = side === 'right' ? pose.legRight : pose.legLeft;

      const shoulderOffset = lateral(shoulderHalf, pose.shoulderRoll, sign);
      const shoulder = { x: chestPoint.x + shoulderOffset.x, y: chestPoint.y + shoulderOffset.y + L('neck') * 0.35, z: chestPoint.z };
      const upperDir = dirDown(armPose.shoulder.tilt, sign * (armPose.shoulder.swing + spill));
      const elbow = add(shoulder, upperDir, L('upperArm'));
      const foreDir = dirDown(armPose.shoulder.tilt + armPose.elbow.tilt, sign * (armPose.shoulder.swing + spill + armPose.elbow.swing));
      const wrist = add(elbow, foreDir, L('foreArm'));
      const hand = add(wrist, foreDir, L('hand'));

      const hipOffset = lateral(hipHalf, pose.hipRoll, sign);
      const hip = { x: pelvis.x + hipOffset.x, y: pelvis.y + hipOffset.y, z: pelvis.z };
      const thighDir = dirDown(legPose.hip.tilt - crouch * 45, sign * legPose.hip.swing);
      const knee = add(hip, thighDir, L('thigh'));
      const shinDir = dirDown(legPose.hip.tilt - crouch * 45 + legPose.knee.tilt + crouch * 85, sign * (legPose.hip.swing + legPose.knee.swing));
      const ankle = add(knee, shinDir, L('shin'));
      const footDir = dirDown(legPose.ankle.tilt + 90, sign * legPose.knee.swing * 0.3);
      const toe = add(ankle, footDir, L('foot'));

      joints[side + 'Shoulder'] = shoulder;
      joints[side + 'Elbow'] = elbow;
      joints[side + 'Wrist'] = wrist;
      joints[side + 'Hand'] = hand;
      joints[side + 'Hip'] = hip;
      joints[side + 'Knee'] = knee;
      joints[side + 'Ankle'] = ankle;
      joints[side + 'Toe'] = toe;

      const limb = L('limb');
      segments.push(
        { id: side + '-upper-arm', kind: 'limb', side, from: shoulder, to: elbow, widthFrom: limb * 1.45, widthTo: limb * 1.2 },
        { id: side + '-fore-arm', kind: 'limb', side, from: elbow, to: wrist, widthFrom: limb * 1.2, widthTo: limb * 1 },
        { id: side + '-hand', kind: 'hand', side, from: wrist, to: hand, widthFrom: limb * 1.08, widthTo: limb * 0.9 },
        { id: side + '-thigh', kind: 'limb', side, from: hip, to: knee, widthFrom: limb * 2.05, widthTo: limb * 1.6 },
        { id: side + '-shin', kind: 'limb', side, from: knee, to: ankle, widthFrom: limb * 1.6, widthTo: limb * 1.2 },
        { id: side + '-foot', kind: 'foot', side, from: ankle, to: toe, widthFrom: limb * 1.35, widthTo: limb * 1.15 }
      );
    };

    limbSide('left');
    limbSide('right');

    // World transform: pitch rotates the whole figure about the x axis
    // (standing -> prone/supine/leaning), root translates pelvis — what
    // sits, lies, hangs, or jumps actually is.
    const world = opts.world || null;
    if (world && (world.pitch || world.root)) {
      const pitch = num(world.pitch, 0) * RAD;
      const pc = Math.cos(pitch), ps = Math.sin(pitch);
      const root = world.root || { x: 0, y: 0, z: 0 };
      const px = joints.pelvis.x, py = joints.pelvis.y, pz = joints.pelvis.z;
      for (const j of Object.values(joints)) {
        const y = j.y * pc - j.z * ps;
        const z = j.y * ps + j.z * pc;
        j.x = j.x + (root.x || 0) - px;
        j.y = y + (root.y || 0) - py;
        j.z = z + (root.z || 0) - pz;
      }
    }

    const project = (p) => ({
      x: p.x * cos + p.z * sin,
      y: -p.y,
      depth: -p.x * sin + p.z * cos
    });

    const screen = {};
    for (const [name, point] of Object.entries(joints)) screen[name] = project(point);

    const parts = segments.map((seg) => {
      const a = project(seg.from);
      const b = project(seg.to);
      return { ...seg, a, b, depth: (a.depth + b.depth) / 2 };
    });

    // A foot points along the body's forward axis, so it projects to nothing in
    // a frontal view. Giving it the shoe's standing height keeps it on screen at
    // every yaw and lets it read as a shoe seen head-on.
    const shoeRise = L('limb') * 0.62;
    for (const part of parts) {
      if (part.kind !== 'foot') continue;
      part.b = { x: part.b.x, y: Math.max(part.b.y, part.a.y + shoeRise), depth: part.b.depth };
    }

    // Body depth: the torso is a box, not a plane, so its projected silhouette
    // keeps width when the figure turns to profile.
    const bodyDepth = proportion.bodyDepth ?? 0.6;
    const support = (half) => Math.abs(half * cos) + Math.abs(half * bodyDepth * sin);
    const shoulderSpan = support(shoulderHalf);
    const hipSpan = support(hipHalf);
    const waistFactor = proportion.waist ?? 1;
    const waistSpan = support(((shoulderHalf + hipHalf) / 2) * waistFactor);
    const waistY = (screen.chest.y + screen.pelvis.y) / 2 + (screen.pelvis.y - screen.chest.y) * 0.12;
    const torso = {
      id: 'torso',
      kind: 'torso',
      depth: (screen.chest.depth + screen.pelvis.depth) / 2,
      shoulderLeft: { x: screen.chest.x - shoulderSpan, y: screen.leftShoulder.y },
      shoulderRight: { x: screen.chest.x + shoulderSpan, y: screen.rightShoulder.y },
      hipLeft: { x: screen.pelvis.x - hipSpan, y: screen.leftHip.y },
      hipRight: { x: screen.pelvis.x + hipSpan, y: screen.rightHip.y },
      chest: screen.chest,
      pelvis: screen.pelvis,
      taper: proportion.torsoTaper,
      // The waist is where soft mass shows, so it is projected like the
      // shoulders and hips rather than interpolated between them by whatever
      // draws the clothes.
      waistLeft: { x: screen.chest.x - waistSpan, y: waistY },
      waistRight: { x: screen.chest.x + waistSpan, y: waistY },
      waist: waistFactor
    };

    const headYaw = yaw + pose.head.yaw;
    const head = {
      id: 'head',
      kind: 'head',
      depth: screen.head.depth + L('head'),
      center: screen.head,
      neck: screen.neck,
      radius: L('head'),
      yaw: headYaw,
      pitch: pose.head.pitch,
      facing: Math.cos(headYaw * RAD),
      lateral: Math.sin(headYaw * RAD),
      viewAxis: nearestViewAxis(headYaw)
    };

    const all = [...parts, torso, head].sort((p, q) => p.depth - q.depth);
    const xs = all.flatMap((p) => (p.kind === 'head' ? [p.center.x - p.radius, p.center.x + p.radius] : p.kind === 'torso' ? [p.shoulderLeft.x, p.shoulderRight.x, p.hipLeft.x, p.hipRight.x, p.waistLeft.x, p.waistRight.x] : [p.a.x, p.b.x]));
    const ys = all.flatMap((p) => (p.kind === 'head' ? [p.center.y - p.radius * 1.35, p.center.y + p.radius] : p.kind === 'torso' ? [p.chest.y, p.pelvis.y] : [p.a.y, p.b.y]));
    const pad = L('limb') * 2.2;
    const ground = Math.max(...parts.filter((p) => p.kind === 'foot').map((p) => p.b.y + p.widthTo * 0.5), screen.leftAnkle.y, screen.rightAnkle.y);

    return {
      proportion: typeof opts.proportion === 'string' ? opts.proportion : (opts.proportion ? 'parametric' : 'adult-average'),
      proportions: proportion,
      height,
      view: { yaw, axis: nearestViewAxis(yaw), headYaw, headAxis: head.viewAxis, facing: Math.cos(yaw * RAD), lateral: Math.sin(yaw * RAD) },
      pose,
      joints: screen,
      // Body-local, unprojected joints: what a contact solver aims at, since a
      // hand on an oar is a fact about the body, not about the camera.
      localJoints: joints,
      parts: all,
      head,
      torso,
      ground,
      bounds: { minX: Math.min(...xs) - pad, maxX: Math.max(...xs) + pad, minY: Math.min(...ys) - pad, maxY: Math.max(...ys) + pad }
    };
  }

  function blend(a, b, t) {
    const k = Math.max(0, Math.min(1, t));
    const mix = (x, y) => x + (y - x) * k;
    const walk = (x, y) => {
      if (typeof x === 'number' && typeof y === 'number') return mix(x, y);
      if (x && y && typeof x === 'object' && typeof y === 'object') {
        const out = {};
        for (const key of new Set([...Object.keys(x), ...Object.keys(y)])) out[key] = walk(x[key], y[key]);
        return out;
      }
      return k < 0.5 ? x : y;
    };
    return walk(mergePose(a), mergePose(b));
  }

  return { build, blend, mergePose, resolveYaw, resolveProportion, nearestViewAxis, VIEW_AXES, PROPORTIONS, REST };
});
