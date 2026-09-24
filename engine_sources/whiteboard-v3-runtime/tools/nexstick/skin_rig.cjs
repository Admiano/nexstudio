#!/usr/bin/env node
/**
 * Skin-on-skeleton figure renderer — the motion path.
 *
 * The paper-cast rig is a pose-table -> capsule stack: fine for curated
 * upright cast figures, wrong for motion. It discards true joint
 * positions, re-expresses frames as ~20 angles, then rebuilds guessed
 * limb locations — elbows/knees land where the table imagines them.
 *
 * This path never re-parametrises anything. The vault's true 3D joints
 * are yaw-rotated to the presentation facing, then mass is drawn
 * straight onto them: capsule per bone (endpoints shared -> one
 * continuous body by construction), pelvis disc welds thighs to torso,
 * deltoid discs weld arms to chest. Knees are exactly where the captured
 * knee was; hands sit on the real wrist; the sit folds at the real hip.
 *
 * Emits the pb-* class vocabulary so line_cast.figure_strokes consumes it
 * unchanged:
 *   mass classes (union silhouette): pb-limb pb-torso pb-top pb-bottom
 *     pb-neck pb-head pb-hair pb-hand pb-foot pb-joint pb-sleeve
 *   detail strokes (inked on top):    pb-detail
 *   skipped:                          pb-rim pb-shadow pb-fold
 *
 * Usage: node skin_rig.cjs '<req-json>' <outDir> <nFrames> <fps>
 *   req: {action} | {cmuClip} | {say|text} (+ look/face/other)
 */
'use strict';
const fs = require('fs');
const path = require('path');
const sampler = require('./cmu_sampler.cjs');
const BOOT = path.resolve(__dirname, '../../../../engines/explainer/NexStudio_Explainer_Execution_Body_V2/runtime-assets/explainer-motion-v1/library/nexstick-v5.1/runtime/node-bootstrap-v5.js');
let V5 = null;
try { V5 = require(BOOT); } catch (e) { /* nexstick vault absent */ }

const SKIN = '#b07d57';
const TOP = '#7d9cab';
const BOTTOM = '#584f40';
const HAIR = '#241c17';
const SHOE = '#3a332b';
const INK = '#2a1c12';

// bone radii in meters (adult-average capsule around each bone)
const R = {
  spine: 0.085, chest: 0.105, neckSeg: 0.045,
  clavicle: 0.038,
  uarm: 0.048, farm: 0.042, hand: 0.034,
  thigh: 0.082, shin: 0.055, foot: 0.036,
  pelvis: 0.135, hipJoint: 0.075, deltoid: 0.058,
  headX: 0.105, headY: 0.125, neckCap: 0.05,
};
const TEE_W = 1.22, SHORTS_W = 1.28, SHORTS_LEN = 0.42, SLEEVE_LEN = 0.35;

// mouth shape vocabulary baked from the NEX performance-carrier mouth rig
// (NEX_MOUTH_MINIMAL shape keys, head-local x=lateral y=opening, meters)
let MOUTH = null;
try {
  MOUTH = JSON.parse(fs.readFileSync(
    path.resolve(__dirname, 'compiled', 'mouth_shapes.json'), 'utf8'));
} catch (e) { /* mouth shapes not baked */ }
const MOUTH_WIDE = { ah: '#33231b', oh: '#33231b', fv: '#33231b' };

const J = {
  pelvis: 'pelvis', spine: 'spine', chest: 'chest', neck: 'neck', head: 'head',
  clavL: 'clavicle_l', clavR: 'clavicle_r',
  shoL: 'shoulder_l', shoR: 'shoulder_r',
  elbL: 'elbow_l', elbR: 'elbow_r',
  wrL: 'wrist_l', wrR: 'wrist_r',
  hipL: 'hip_l', hipR: 'hip_r',
  kneeL: 'knee_l', kneeR: 'knee_r',
  ankL: 'ankle_l', ankR: 'ankle_r',
  toeL: 'toe_l', toeR: 'toe_r',
};

const DEG = 180 / Math.PI, RAD = Math.PI / 180;
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const len = (a) => Math.hypot(a[0], a[1], a[2]) || 1e-9;
const lerp3 = (a, b, t) => add(a, mul(sub(b, a), t));
const wrap = (a) => ((a + 180) % 360 + 360) % 360 - 180;
const round = (n) => Math.round(n * 100) / 100;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// Body facing azimuth + confidence: atan2 on the clavicle+hip lateral sum
// degenerates (near-zero) on dead-on facings and deep spine twist —
// callers hold the last confident reading when mag is low.
function bodyAzMag(p3) {
  const lc = sub(p3.clavicle_l, p3.clavicle_r);
  const lh = sub(p3.hip_l, p3.hip_r);
  const fx = -(lc[2] + lh[2]), fz = lc[0] + lh[0];
  return { az: Math.atan2(fx, fz) * DEG, mag: Math.hypot(fx, fz) };
}
const AZ_MIN_MAG = 0.12;

// CMU captures open with the actor in T-pose for a fraction of a second.
// Detect the end of the marker pose so renders start on the performance.
const isTPose = (p3) => {
  const cdx = Math.hypot(p3.clavicle_l[0] - p3.clavicle_r[0], p3.clavicle_l[2] - p3.clavicle_r[2]);
  const wdx = Math.hypot(p3.wrist_l[0] - p3.wrist_r[0], p3.wrist_l[2] - p3.wrist_r[2]);
  const wy = (p3.wrist_l[1] + p3.wrist_r[1]) / 2;
  const cy = (p3.clavicle_l[1] + p3.clavicle_r[1]) / 2;
  return cdx > 1e-3 && wdx > 1.55 * cdx && wy > cy - 0.06;
};

function capsule2(ax, ay, bx, by, r) {
  const dx = bx - ax, dy = by - ay;
  const l = Math.hypot(dx, dy) || 1e-6;
  const px = (-dy / l) * r, py = (dx / l) * r;
  return `<path d="M ${round(ax - px)} ${round(ay - py)} L ${round(bx - px)} ${round(by - py)} `
    + `A ${round(r)} ${round(r)} 0 0 1 ${round(bx + px)} ${round(by + py)} `
    + `L ${round(ax + px)} ${round(ay + py)} `
    + `A ${round(r)} ${round(r)} 0 0 1 ${round(ax - px)} ${round(ay - py)} Z"/>`;
}
const disc = (x, y, r) => `<circle cx="${round(x)}" cy="${round(y)}" r="${round(r)}"/>`;
const ell = (x, y, rx, ry) => `<ellipse cx="${round(x)}" cy="${round(y)}" rx="${round(rx)}" ry="${round(ry)}"/>`;
const stroke = (d, w) =>
  `<path d="${d}" stroke="${INK}" stroke-width="${round(w)}" fill="none" stroke-linecap="round"/>`;

// perpendicular seam stroke across a segment at point (x,y)
const seam = (x, y, ax, ay, half, w) => {
  const l = Math.hypot(ax, ay) || 1;
  const px = (-ay / l) * half, py = (ax / l) * half;
  return stroke(`M ${round(x - px)} ${round(y - py)} L ${round(x + px)} ${round(y + py)}`, w);
};

// fingers: fan of small capsules from a knuckle point along the forearm dir,
// spread set by the semantic hand state (data-driven, not decoration).
function handSvg(wx, wy, dirx, diry, state, R2, skin) {
  const fl = Math.hypot(dirx, diry) || 1;
  const fx = dirx / fl, fy = diry / fl;
  const px = -fy, py = fx;                    // palm normal
  const knuckle = { x: wx + fx * R2(R.hand * 0.7), y: wy + fy * R2(R.hand * 0.7) };
  const states = {
    open:    { spread: 26, len: 0.11 },
    present: { spread: 30, len: 0.11 },
    wave:    { spread: 34, len: 0.115 },
    spread:  { spread: 40, len: 0.11 },
    point:   { spread: 8,  len: 0.13 },
    tap:     { spread: 10, len: 0.12 },
    pinch:   { spread: 4,  len: 0.10 },
    grip:    { spread: 2,  len: 0.07 },
    curl:    { spread: 2,  len: 0.07 },
    receive: { spread: 22, len: 0.10 },
    give:    { spread: 24, len: 0.10 },
    relaxed: { spread: 6,  len: 0.08 },
  };
  const st = states[state] || states.relaxed;
  let out = disc(wx, wy, R2(R.hand)) +
    capsule2(wx, wy, knuckle.x, knuckle.y, R2(R.hand * 0.85));
  for (let f = -1; f <= 1; f++) {
    const a = f * st.spread * RAD * 0.5;
    const dx = fx * Math.cos(a) - fy * Math.sin(a);
    const dy = fx * Math.sin(a) + fy * Math.cos(a);
    out += capsule2(knuckle.x, knuckle.y,
      knuckle.x + dx * R2(st.len), knuckle.y + dy * R2(st.len),
      R2(R.hand * 0.28));
  }
  return out;
}

// line-art hand: outlined palm + finger strokes, same semantic states
function handLineSvg(wx, wy, dirx, diry, state, R2) {
  const fl = Math.hypot(dirx, diry) || 1;
  const fx = dirx / fl, fy = diry / fl;
  const knuckle = { x: wx + fx * R2(R.hand * 0.85), y: wy + fy * R2(R.hand * 0.85) };
  const spreads = {
    open: 26, present: 30, wave: 34, spread: 40, point: 8, tap: 10,
    pinch: 4, grip: 2, curl: 2, receive: 22, give: 24, relaxed: 6,
  };
  const len = { point: 0.13, tap: 0.12, wave: 0.115 }[state] || 0.10;
  const sp = spreads[state] ?? spreads.relaxed;
  let out = `<circle cx="${round(wx)}" cy="${round(wy)}" r="${round(R2(R.hand * 0.95))}" `
    + `fill="white" stroke="${INK}" stroke-width="${round(R2(0.014))}"/>`;
  for (let f = -1; f <= 1; f++) {
    const a = f * sp * RAD * 0.5;
    const dx = fx * Math.cos(a) - fy * Math.sin(a);
    const dy = fx * Math.sin(a) + fy * Math.cos(a);
    out += stroke(`M ${round(knuckle.x)} ${round(knuckle.y)} L ${round(knuckle.x + dx * R2(len))} ${round(knuckle.y + dy * R2(len))}`, R2(0.016));
  }
  return out;
}

/**
 * Render one skeleton frame to an SVG document.
 * p3: {joint: [x,y,z]} meters y-up.
 * opts.presentAz: azimuth the figure is ROTATED to face (degrees in the
 *   capture's xz convention) before projection — a true 3D yaw, so real
 *   turns survive untouched and the baseline can sit at the good 3/4 axis.
 * opts.handL/handR: semantic hand states; headAz: world head azimuth.
 */
function skeletonSvg(p3, opts = {}) {
  const S = opts.scale || 645;
  const pelvis = p3.pelvis;
  const rot = ((opts.presentAz ?? -38) - (opts.bodyAz ?? -90)) * RAD;
  const cosR = Math.cos(rot), sinR = Math.sin(rot);
  const proj = (j) => {
    const p = p3[j];
    const rx = p[0] - pelvis[0], rz = p[2] - pelvis[2];
    const x2 = rx * cosR - rz * sinR;
    const z2 = rx * sinR + rz * cosR;
    return { x: (z2 + pelvis[2]) * S, y: -p[1] * S, d: -(x2 + pelvis[0]) * S };
  };
  const q = {};
  for (const k of Object.values(J)) q[k] = proj(k);
  const R2 = (m) => m * S;

  const parts = [];
  const push = (d, cls, fill, svg) => parts.push({ d, cls, fill, svg });
  const lineMode = opts.style === 'line';
  // Line-art mode ("stick" style for whiteboards): bones draw as weighted
  // center-line strokes instead of filled capsule masses; garment masses
  // and joint-weld discs are dropped entirely; the head becomes an
  // outlined shape so the face stays anchored; hair keeps its solid ink.
  const capL = (ax, ay, bx, by, r, f = 0.62) => lineMode
    ? stroke(`M ${round(ax)} ${round(ay)} L ${round(bx)} ${round(by)}`, r * 2 * f)
    : capsule2(ax, ay, bx, by, r);
  const capG = (ax, ay, bx, by, r) => lineMode ? '' : capsule2(ax, ay, bx, by, r);
  const dotL = (x, y, r) => lineMode ? '' : disc(x, y, r);
  const ellL = (x, y, rx, ry) => lineMode
    ? `<ellipse cx="${round(x)}" cy="${round(y)}" rx="${round(rx)}" ry="${round(ry)}" fill="white" stroke="${INK}" stroke-width="${round(S * 0.012)}"/>`
    : ell(x, y, rx, ry);

  const handL = opts.handL || 'relaxed', handR = opts.handR || 'relaxed';
  // true projected depth per segment: the near limb sorts above the torso
  // fill, the far limb under it — an arm crossing the body reads as
  // crossing in front or behind, never dissolving into the mass.
  const dSeg = (a, b) => (a.d + b.d) / 2;

  for (const s of ['L', 'R']) {
    const hip = q[J['hip' + s]], knee = q[J['knee' + s]], ank = q[J['ank' + s]], toe = q[J['toe' + s]];
    // far-side limbs draw narrower so they never read as the near arm/leg
    const far = (q[J['sho' + s]].d + q[J['hip' + s]].d) / 2 < 0;
    const LW = far ? 0.8 : 1;
    const R3 = (v) => R2(v * LW);
    const dShin = dSeg(knee, ank), dThigh = dSeg(hip, knee), dFoot = dSeg(ank, toe);
    push(dShin - 0.001, 'pb-limb', SKIN, capL(knee.x, knee.y, ank.x, ank.y, R2(R.shin * LW)));
    const st = lerp3([hip.x, hip.y], [knee.x, knee.y], SHORTS_LEN);
    push(dThigh + 0.002, 'pb-bottom', BOTTOM, capG(hip.x, hip.y, st[0], st[1], R2(R.thigh * SHORTS_W * LW)));
    push(dThigh + 0.001, 'pb-limb', SKIN, capL(hip.x, hip.y, knee.x, knee.y, R2(R.thigh * LW)));
    push(dSeg(knee, knee) - 0.002, 'pb-joint', SKIN, dotL(knee.x, knee.y, R2((R.thigh + R.shin) * 0.42 * LW)));
    push(dFoot + 0.001, 'pb-foot', SHOE, capL(ank.x, ank.y, toe.x, toe.y, R2(R.foot * LW), 0.9));
    push(dFoot + 0.001, 'pb-foot', SHOE, dotL(ank.x, ank.y, R2(R.foot * 1.15 * LW)));
    // sole line along the foot bottom
    push(dFoot + 0.002, 'pb-detail', 'none',
      stroke(`M ${round(ank.x - R2(R.foot) * 0.4)} ${round(ank.y + R2(R.foot))} L ${round(toe.x)} ${round(toe.y + R2(R.foot))}`, S * 0.008));
    // arms
    const sho = q[J['sho' + s]], elb = q[J['elb' + s]], wr = q[J['wr' + s]];
    const dUarm = dSeg(sho, elb), dFarm = dSeg(elb, wr), dHand = wr.d;
    // sleeve: widened capsule over the upper-arm top
    const sl = lerp3([sho.x, sho.y], [elb.x, elb.y], SLEEVE_LEN);
    push(dUarm + 0.002, 'pb-sleeve', TOP, capG(sho.x, sho.y, sl[0], sl[1], R2(R.uarm * TEE_W * LW)));
    // sleeve hem seam
    if (!lineMode) push(dUarm + 0.003, 'pb-detail', 'none',
      seam(sl[0], sl[1], elb.x - sho.x, elb.y - sho.y, R2(R.uarm * TEE_W * LW) * 0.92, S * 0.006));
    push(dFarm, 'pb-limb', SKIN, capL(elb.x, elb.y, wr.x, wr.y, R2(R.farm * LW)));
    push(dUarm + 0.001, 'pb-limb', SKIN, capL(sho.x, sho.y, elb.x, elb.y, R2(R.uarm * LW)));
    push(elb.d + 0.001, 'pb-joint', SKIN, dotL(elb.x, elb.y, R2((R.uarm + R.farm) * 0.4 * LW)));
    // hand on the true wrist, fingers fan along the forearm direction,
    // spread from the clip's semantic hand state
    const st2 = s === 'L' ? handL : handR;
    push(dHand + 0.002, 'pb-hand', SKIN, lineMode
      ? handLineSvg(wr.x, wr.y, wr.x - elb.x, wr.y - elb.y, st2, far ? R3 : R2)
      : handSvg(wr.x, wr.y, wr.x - elb.x, wr.y - elb.y, st2, far ? R3 : R2, SKIN));
  }

  // torso column on the true spine chain + pelvis & chest welds
  const pel = q[J.pelvis], sp = q[J.spine], ch = q[J.chest], nk = q[J.neck], hd = q[J.head];
  if (lineMode) {
    // one weighted stroke along the bent spine — the "body line" of the
    // stick figure (thicker than limbs so it reads as a torso)
    push(0, 'pb-top', TOP, stroke(
      `M ${round(pel.x)} ${round(pel.y)} L ${round(sp.x)} ${round(sp.y)} L ${round(ch.x)} ${round(ch.y)} L ${round(nk.x)} ${round(nk.y)}`,
      R2(R.chest * 1.15)));
    push(0.005, 'pb-limb', SKIN, stroke(
      `M ${round(q[J.hipL].x)} ${round(q[J.hipL].y)} L ${round(q[J.hipR].x)} ${round(q[J.hipR].y)}`,
      R2(R.hipJoint * 1.1)));
  } else {
    const tee = (ax, ay, bx, by, r) => push(0, 'pb-top', TOP, capsule2(ax, ay, bx, by, r));
    tee(pel.x, pel.y, sp.x, sp.y, R2(R.spine * TEE_W));
    tee(sp.x, sp.y, ch.x, ch.y, R2(R.chest * TEE_W));
    tee(ch.x, ch.y, nk.x, nk.y, R2(R.neckSeg * 1.5 * TEE_W));
    push(0.01, 'pb-torso', SKIN, disc(pel.x, pel.y, R2(R.pelvis)));
    push(0.01, 'pb-top', TOP, disc(ch.x, ch.y, R2(R.chest * TEE_W * 0.98)));
  }
  // waistband seam where the tee meets the shorts — perpendicular to the
  // lower-spine bone so it follows the bent torso
  if (!lineMode) {
    const wMid = lerp3([pel.x, pel.y], [sp.x, sp.y], 0.2);
    push(0.02, 'pb-detail', 'none',
      seam(wMid[0], wMid[1], sp.x - pel.x, sp.y - pel.y, R2(R.spine * TEE_W) * 0.9, S * 0.007));
    // collar seam at the neck base
    const cMid = lerp3([ch.x, ch.y], [nk.x, nk.y], 0.75);
    push(0.02, 'pb-detail', 'none',
      seam(cMid[0], cMid[1], nk.x - ch.x, nk.y - ch.y, R2(R.neckSeg * 1.5 * TEE_W) * 0.95, S * 0.007));
  }

  const clL = q[J.clavL], clR = q[J.clavR];
  push(0.02, 'pb-top', TOP, capL(clL.x, clL.y, clR.x, clR.y, R2(R.clavicle), 0.75));
  for (const s of ['L', 'R']) {
    push(0.03, 'pb-joint', TOP, dotL(q[J['sho' + s]].x, q[J['sho' + s]].y, R2(R.deltoid)));
    push(0.03, 'pb-joint', SKIN, dotL(q[J['hip' + s]].x, q[J['hip' + s]].y, R2(R.hipJoint)));
  }

  // neck + head; face rides the head's TRUE azimuth — frontal heads get
  // centered features, profile heads get them on the leading edge,
  // turned-away heads show only hair. No more dead-profile or phantom face.
  push(0.4, 'pb-neck', SKIN, capL(nk.x, nk.y, hd.x, hd.y, R2(R.neckCap), 0.7));
  const hr = { x: hd.x, y: hd.y - R2(0.02) };
  push(0.4, 'pb-head', SKIN, ellL(hr.x, hr.y, R2(R.headX), R2(R.headY)));
  // head world azimuth after the same presentation rotation
  const headAzW = (opts.headAz ?? opts.bodyAz ?? -90) + ((opts.presentAz ?? -38) - (opts.bodyAz ?? -90));
  const camAz = -90;                                  // camera sits on -x
  const rel = wrap(headAzW - camAz) * RAD;            // 0 = facing camera
  const facing = Math.cos(rel);                        // +front / -away
  const fOff = Math.sin(rel);                          // feature side offset
  if (facing > -0.25) {
    // eyes + mouth placed by how much the head faces the camera
    const ex = hr.x + R2(R.headX) * (0.15 + 0.55 * fOff * fOff) * Math.sign(fOff || 1) * 0.9;
    const ey = hr.y - R2(R.headY) * 0.15;
    const spread = Math.abs(fOff) * 0.8;
    push(0.42, 'pb-detail', 'none',
      `<circle cx="${round(ex - R2(R.headX) * spread * 0.5)}" cy="${round(ey)}" r="${round(S * 0.009)}" fill="${INK}"/>`
      + (Math.abs(fOff) > 0.35 ? '' :
        `<circle cx="${round(ex + R2(R.headX) * spread * 0.5)}" cy="${round(ey)}" r="${round(S * 0.009)}" fill="${INK}"/>`));
  }
  // mouth from the carrier rig's real viseme shapes — the loop narrows
  // with the head's turn, so speech reads in any facing direction.
  if (MOUTH && facing > 0.05) {
    const name = (opts.mouth || 'rest').toUpperCase();
    const loop = MOUTH.shapes[name] || MOUTH.shapes.REST;
    const ax = MOUTH.anchor[0], ay = MOUTH.anchor[1];
    const k = R2(R.headX * 1.35) / 0.1545;   // rig mouth ~1.35 head radii wide
    const mx = hr.x + fOff * R2(R.headX) * 0.45;
    const my = hr.y + R2(0.045);
    const d = loop.map((p, i) =>
      `${i ? 'L' : 'M'} ${round(mx + (p[0] - ax) * k * facing)} ${round(my - (p[1] - ay) * k)}`).join(' ') + ' Z';
    const fill = MOUTH_WIDE[name.toLowerCase()] || 'none';
    push(0.43, 'pb-detail', 'none',
      `<path d="${d}" stroke="${INK}" stroke-width="${round(S * 0.007)}" fill="${fill}"/>`);
  }
  // prop layer: line-art props for activity clips. The chair sits UNDER
  // the figure (seated on it); hand props hang off the wrists and draw at
  // the hands' depth so the grip occludes correctly.
  const propList = Array.isArray(opts.prop) ? opts.prop : (opts.prop ? [opts.prop] : []);
  if (propList.includes('chair')) {
    const toek = (q[J.toeL].x + q[J.toeR].x) / 2, hipx = (q[J.hipL].x + q[J.hipR].x) / 2;
    const dir = Math.sign(toek - hipx) || 1;       // where the sitter faces
    const seatY = -0.46 * S, backTop = -0.92 * S;
    const backX = pel.x - dir * R2(0.20), frontX = pel.x + dir * R2(0.14);
    const ink = (d, w) => push(-0.5, 'pb-detail', 'none', stroke(d, w));
    // seat slab (double edge)
    ink(`M ${round(backX)} ${round(seatY)} L ${round(frontX)} ${round(seatY)}`, S * 0.01);
    ink(`M ${round(backX)} ${round(seatY + S * 0.014)} L ${round(frontX)} ${round(seatY + S * 0.014)}`, S * 0.01);
    // backrest
    ink(`M ${round(backX)} ${round(seatY)} L ${round(backX - dir * R2(0.05))} ${round(backTop)}`, S * 0.012);
    ink(`M ${round(backX - dir * R2(0.05))} ${round(backTop)} L ${round(backX + dir * R2(0.05))} ${round(backTop)}`, S * 0.01);
    ink(`M ${round(backX + dir * R2(0.05))} ${round(backTop)} L ${round(backX)} ${round(seatY)}`, S * 0.012);
    // legs to the floor (y=0 in this projection)
    ink(`M ${round(frontX - dir * R2(0.02))} ${round(seatY + S * 0.014)} L ${round(frontX - dir * R2(0.04))} 0`, S * 0.01);
    ink(`M ${round(backX + dir * R2(0.02))} ${round(seatY + S * 0.014)} L ${round(backX + dir * R2(0.04))} 0`, S * 0.01);
  }
  // hand props: broom (shaft through the hands to the floor ahead), box
  // (between the wrists), phone (at the wrist nearer the ear), marker
  // (nib past the near hand), cup (at the near hand).
  const wrA = { x: (q[J.wrL].x + q[J.wrR].x) / 2, y: (q[J.wrL].y + q[J.wrR].y) / 2,
                d: (q[J.wrL].d + q[J.wrR].d) / 2 };
  const dirP = Math.sign((q[J.toeL].x + q[J.toeR].x) / 2 - (q[J.hipL].x + q[J.hipR].x) / 2) || 1;
  const wNear = q[J.wrL].d < q[J.wrR].d ? q[J.wrL] : q[J.wrR];
  const propExt = [];                       // prop tips join the viewBox bbox
  for (const prop of propList) {
    if (prop === 'chair') continue;
    const ink = (d, w, dd = 0) => push(wrA.d - 0.02 + dd, 'pb-detail', 'none', stroke(d, w));
    if (prop === 'broom') {
      const top = { x: wrA.x - dirP * R2(0.10), y: wrA.y - R2(0.30) };
      const tip = { x: wrA.x + dirP * R2(0.30), y: R2(0.015) };
      propExt.push(top, { x: tip.x + dirP * R2(0.08), y: tip.y + R2(0.11) });
      ink(`M ${round(top.x)} ${round(top.y)} L ${round(tip.x)} ${round(tip.y)}`, S * 0.016);
      for (const k of [-2, -1, 0, 1, 2])
        ink(`M ${round(tip.x)} ${round(tip.y)} L ${round(tip.x + dirP * R2(0.03 + k * 0.014))} ${round(tip.y + R2(0.10 - Math.abs(k) * 0.018))}`, S * 0.008, 0.01);
    } else if (prop === 'box') {
      const bw = R2(0.38), bh = R2(0.26), bx = wrA.x, by = wrA.y + R2(0.04);
      ink(`M ${round(bx - bw / 2)} ${round(by)} L ${round(bx + bw / 2)} ${round(by)} L ${round(bx + bw / 2)} ${round(by + bh)} L ${round(bx - bw / 2)} ${round(by + bh)} Z`, S * 0.011);
      ink(`M ${round(bx - bw / 2)} ${round(by)} L ${round(bx - bw / 2 + dirP * bw * 0.16)} ${round(by - R2(0.05))} L ${round(bx + bw / 2 + dirP * bw * 0.16)} ${round(by - R2(0.05))} L ${round(bx + bw / 2)} ${round(by)}`, S * 0.011);
    } else if (prop === 'phone') {
      const wp = Math.hypot(q[J.wrL].x - hr.x, q[J.wrL].y - hr.y) < Math.hypot(q[J.wrR].x - hr.x, q[J.wrR].y - hr.y) ? q[J.wrL] : q[J.wrR];
      push(wp.d - 0.07, 'pb-detail', 'none', stroke(
        `M ${round(wp.x - R2(0.012))} ${round(wp.y - R2(0.045))} L ${round(wp.x + R2(0.018))} ${round(wp.y - R2(0.035))} L ${round(wp.x + R2(0.008))} ${round(wp.y + R2(0.055))} L ${round(wp.x - R2(0.022))} ${round(wp.y + R2(0.045))} Z`, S * 0.008));
    } else if (prop === 'marker') {
      propExt.push({ x: wNear.x + dirP * R2(0.08), y: wNear.y });
      ink(`M ${round(wNear.x - dirP * R2(0.02))} ${round(wNear.y + R2(0.01))} L ${round(wNear.x + dirP * R2(0.055))} ${round(wNear.y - R2(0.02))}`, S * 0.02);
      ink(`M ${round(wNear.x + dirP * R2(0.055))} ${round(wNear.y - R2(0.02))} L ${round(wNear.x + dirP * R2(0.075))} ${round(wNear.y - R2(0.025))}`, S * 0.03, 0.01);
    } else if (prop === 'cup') {
      ink(`M ${round(wNear.x - R2(0.03))} ${round(wNear.y)} L ${round(wNear.x + R2(0.03))} ${round(wNear.y)} L ${round(wNear.x + R2(0.02))} ${round(wNear.y + R2(0.065))} L ${round(wNear.x - R2(0.02))} ${round(wNear.y + R2(0.065))} Z`, S * 0.008);
      ink(`M ${round(wNear.x + R2(0.03))} ${round(wNear.y + R2(0.012))} Q ${round(wNear.x + R2(0.055))} ${round(wNear.y + R2(0.02))} ${round(wNear.x + R2(0.035))} ${round(wNear.y + R2(0.045))}`, S * 0.007);
    }
  }
  // hair: cap biased to the side the head is turned AWAY from
  const hOff = -Math.sign(fOff || 1) * (0.55 + 0.45 * Math.abs(fOff));
  push(0.41, 'pb-hair', HAIR,
    `<path d="M ${round(hr.x + R2(R.headX) * hOff - R2(R.headX) * 0.45)} ${round(hr.y - R2(R.headY) * 0.2)} `
    + `Q ${round(hr.x + R2(R.headX) * hOff - R2(R.headX) * 0.35)} ${round(hr.y - R2(R.headY) * 1.25)} ${round(hr.x + R2(R.headX) * hOff + R2(R.headX) * 0.55)} ${round(hr.y - R2(R.headY) * 1.05)} `
    + `Q ${round(hr.x + R2(R.headX) * hOff + R2(R.headX) * 0.95)} ${round(hr.y - R2(R.headY) * 0.55)} ${round(hr.x + R2(R.headX) * hOff + R2(R.headX) * 0.75)} ${round(hr.y - R2(R.headY) * 0.1)} `
    + `Q ${round(hr.x + R2(R.headX) * hOff)} ${round(hr.y - R2(R.headY) * 0.45)} ${round(hr.x + R2(R.headX) * hOff - R2(R.headX) * 0.45)} ${round(hr.y - R2(R.headY) * 0.2)} Z"/>`);
  push(0.41, 'pb-hair', HAIR, disc(hr.x + R2(R.headX) * hOff - R2(R.headX) * 0.3, hr.y - R2(R.headY) * 0.75, R2(0.055)));

  parts.sort((a, b) => a.d - b.d);
  const body = parts.map((p) => {
    if (p.cls === 'pb-detail') return `<g class="pb-detail" fill="none">${p.svg.replace(/fill="[^"]*"/g, '')}</g>`;
    return `<g class="${p.cls}" fill="${p.fill}">${p.svg}</g>`;
  }).join('\n');

  const xs = [], ys = [];
  for (const k of Object.keys(q)) { xs.push(q[k].x); ys.push(q[k].y); }
  for (const p of propExt) { xs.push(p.x); ys.push(p.y); }
  const pad = R2(0.10);
  const x0 = Math.min(...xs) - pad, x1 = Math.max(...xs) + pad;
  // small headroom for hair/reach above the head joint; feet sit near the
  // bottom edge so strips can bottom-align the figure on the ground line
  const y0 = Math.min(...ys) - pad - R2(0.12), y1 = Math.max(...ys) + pad;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${round(x0)} ${round(y0)} ${round(x1 - x0)} ${round(y1 - y0)}">`
    + `<g class="pb-figure">\n${body}\n</g></svg>`;
}

// ---------------- CLI ----------------
const req = JSON.parse(process.argv[2] || '{}');
const outDir = process.argv[3] || '/tmp/skin_rig_out';
const nF = Number(process.argv[4] || 16), fps = Number(process.argv[5] || 24);
fs.mkdirSync(outDir, { recursive: true });

function sampleAny(r, t) {
  const off = r.t || 0;
  if (r.cmuClip) return sampler.sample(r.cmuClip, t + off, r);
  if (V5) {
    const st = V5.sample(r, t + off);
    if (!(st && st.blocked)) return st;
    if (!sampler.sample(r.action || '', 0).blocked) return sampler.sample(r.action, t + off, r);
    return st;
  }
  return sampler.sample(r.action || 'CMU_WALK_1', t + off, r);
}

// skip T-pose calibration lead-in
const leadIn = (r) => {
  const s0 = sampleAny(r, 0);
  if (!s0.pose3d || !isTPose(s0.pose3d)) return 0;
  const dur = s0.duration || 2;
  for (let t = 0.1; t < Math.min(2.0, dur); t += 0.1) {
    const s = sampleAny(r, t);
    if (s.pose3d && !isTPose(s.pose3d)) return t;
  }
  return 0;
};
req.t = (req.t || 0) + leadIn(req);

// narration-driven clip pick
if (!req.cmuClip && (req.say || req.text)) {
  const pick = require('./clip_select.cjs')
    .selectClip(req.say || req.text, sampler.vault().clips);
  if (pick) req.cmuClip = pick;
}

// locomotion reads cleanest near-profile (legs split, each arm keeps its
// own silhouette edge); hosts/gestures keep the 3/4 presentation.
const LOCO_CLIP = req.cmuClip ? sampler.vault().clips[req.cmuClip] : null;
const LOCO = !!(LOCO_CLIP && (LOCO_CLIP.rootDelta ||
  /WALK|RUN|JOG|PACE|CYCLE|CLIMB|STAIR|HOP|MARCH|CARRY|CRAWL/i.test(req.cmuClip || '')));
const BASE_AZ = LOCO ? -16 : -38;

// confident-sample baselines (degenerate lateral frames excluded)
const st0 = sampleAny(req, 0);
const az0 = (() => {
  const dur = st0.duration || nF / fps;
  for (let k = 0; k < 16; k++) {
    const s = sampleAny(req, Math.min(dur * k / 15 * 0.5, dur));
    if (s.pose3d) { const c = bodyAzMag(s.pose3d); if (c.mag > AZ_MIN_MAG) return c.az; }
  }
  return st0.pose3d ? bodyAzMag(st0.pose3d).az : 0;
})();
const azBase = (() => {
  let sx = 0, sz = 0, n = 0;
  const dur = st0.duration || nF / fps;
  for (let k = 0; k < 16 && n < 8; k++) {
    const s = sampleAny(req, dur * k / 16);
    if (!s.pose3d) continue;
    const c = bodyAzMag(s.pose3d);
    if (c.mag <= AZ_MIN_MAG) continue;
    const a = c.az / DEG;
    sx += Math.sin(a); sz += Math.cos(a); n++;
  }
  return n ? Math.atan2(sx / n, sz / n) * DEG : az0;
})();
const headOff = (() => {
  const ds = [];
  const dur = st0.duration || nF / fps;
  for (let k = 0; k < 24 && ds.length < 12; k++) {
    const s = sampleAny(req, dur * k / 24);
    if (s.roty !== null && s.roty !== undefined && s.pose3d) {
      const c = bodyAzMag(s.pose3d);
      if (c.mag > AZ_MIN_MAG) ds.push(wrap(s.roty - c.az));
    }
  }
  ds.sort((a, b) => a - b);
  return ds.length ? ds[ds.length >> 1] : 0;
})();

// smoothed facing tracker (holds on degenerate frames, eases on confident)
let azSm = az0;
const trackAz = (p3) => {
  const c = bodyAzMag(p3);
  if (c.mag > AZ_MIN_MAG) azSm += wrap(c.az - azSm) * 0.35;
  return azSm;
};

// chair prop for seated actions (pelvis parked at chair height + name hint)
const SEATED = (req.cmuClip || req.action || '')
  .match(/SIT|SEATED|GESTURE|ATTENTION|PHRASE|THINK|LISTEN|QUESTION|PRESENT|EXPLAIN|EMPHASIS|AGREE|REST|RECOVER/i)
  && st0.pose3d && st0.pose3d.pelvis[1] < 0.85;
// activity props auto-attach by clip name (same pattern as the chair)
const PROP_RULES = [
  [/SWEEP|BROOM/i, 'broom'],
  [/PICKUP|CARRY|CARRYING|SUITCASE|LUGGAGE|\bBOX\b/i, 'box'],
  [/PHONE|CALL/i, 'phone'],
  [/WRITE|WRITING|MARKER/i, 'marker'],
  [/DRINK|COFFEE|SIP|CUP/i, 'cup'],
];
const autoProps = PROP_RULES.filter(([re]) => re.test(req.cmuClip || '')).map(([, p]) => p);

// optional viseme timeline (rhubarb cues json) -> per-frame mouth shape
let VTL = null;
if (req.visemes) {
  try {
    const vc = JSON.parse(fs.readFileSync(req.visemes, 'utf8'));
    const cues = vc.cues || vc;
    const vo = req.visOffset || 0;
    VTL = (t) => {
      for (const c of cues) if (c.start - vo <= t && t <= c.end - vo) return c.viseme;
      return 'rest';
    };
  } catch (e) { /* visemes unreadable */ }
}

const meta = [];
for (let i = 0; i < nF; i++) {
  const t = i / fps;
  const st = sampleAny(req, t);
  if (st.blocked) { console.error('blocked', st.failure); break; }
  const az = trackAz(st.pose3d);
  // presentation: baseline at the clip family's readable axis, real turns
  // damped through tanh — a true joint-space yaw rotation, so the body
  // keeps its captured pose under any facing.
  const presentAz = clamp(BASE_AZ - BASE_AZ * Math.tanh(wrap(az - azBase) / 55),
    LOCO ? -62 : -76, LOCO ? 12 : 0);
  const headAz = (st.roty !== null && st.roty !== undefined)
    ? az + clamp(wrap(st.roty - az - headOff), -80, 80)
    : az;
  const svg = skeletonSvg(st.pose3d, {
    scale: 645, bodyAz: az, presentAz, headAz,
    handL: st.hands && st.hands.left && st.hands.left.pose,
    handR: st.hands && st.hands.right && st.hands.right.pose,
    mouth: req.mouth || (VTL ? VTL(t) : undefined),
    style: req.style,
    prop: req.prop
      ? (Array.isArray(req.prop) ? req.prop : [req.prop])
      : [...autoProps, ...(SEATED ? ['chair'] : [])],
  });
  fs.writeFileSync(path.join(outDir, `g${String(i).padStart(3, '0')}.svg`), svg);
  meta.push({ t, root: st.pose3d.root || [0, 0, 0] });
}
fs.writeFileSync(path.join(outDir, 'poses.json'), JSON.stringify(meta));
console.log('wrote', meta.length, 'frames to', outDir);
