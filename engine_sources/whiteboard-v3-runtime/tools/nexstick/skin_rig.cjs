#!/usr/bin/env node
/**
 * Skin-on-skeleton figure renderer.
 *
 * The paper-cast rig is a pose-table -> capsule stack: fine for curated
 * upright cast figures, wrong for motion. This path never re-parametrises
 * anything — it draws masses straight onto the 22-joint mocap skeleton
 * (vault frame: meters, y-up, +z forward). Bones share endpoints, so the
 * union silhouette is one continuous body by construction; the pelvis disc
 * welds thighs to torso, deltoid discs weld arms to chest, and limb width
 * tapers follow the bone, not a fixed garment hull.
 *
 * Emits the same pb-* class vocabulary as paperbook-figure so
 * line_cast.figure_strokes consumes it unchanged:
 *   mass classes (union silhouette): pb-limb pb-torso pb-top pb-bottom
 *     pb-neck pb-head pb-hair pb-hand pb-foot pb-joint
 *   detail strokes (inked on top):    pb-detail
 *   skipped:                          pb-rim pb-shadow pb-fold
 *
 * Usage: node skin_rig.cjs '<req-json>' <outDir> <nFrames> <fps>
 *   req: {action} | {cmuClip} — same sampler contract as mocap_rig.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const sampler = require('./cmu_sampler.cjs');
const BOOT = path.resolve(__dirname, '../../../../engines/explainer/NexStudio_Explainer_Execution_Body_V2/runtime-assets/explainer-motion-v1/library/nexstick-v5.1/runtime/node-bootstrap-v5.js');
let V5 = null;
try { V5 = require(BOOT); } catch (e) { /* nexstick vault absent */ }

const SKIN = '#b07d57';        // paper-cast skin tone
const TOP = '#7d9cab';         // fitted top
const BOTTOM = '#584f40';      // shorts
const HAIR = '#241c17';
const SHOE = '#3a332b';
const INK = '#2a1c12';

// bone radii in meters (adult-average, radius of the capsule around the bone)
const R = {
  spine: 0.085, chest: 0.105, neckSeg: 0.045,
  clavicle: 0.038,
  uarm: 0.048, farm: 0.042, hand: 0.034,
  thigh: 0.082, shin: 0.055, foot: 0.036,
  pelvis: 0.135, hipJoint: 0.075, deltoid: 0.058,
  headX: 0.105, headY: 0.125, neckCap: 0.05,
};
// garment read: the tee is just the torso masses a touch wider; shorts
// cover the upper thigh — zero extra geometry, the union does the work.
const TEE_W = 1.22, SHORTS_W = 1.28, SHORTS_LEN = 0.42;

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

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const mid = (a, b) => mul(add(a, b), 0.5);
const len = (a) => Math.hypot(a[0], a[1], a[2]) || 1e-9;
const lerp3 = (a, b, t) => add(a, mul(sub(b, a), t));

const round = (n) => Math.round(n * 100) / 100;

/** capsule mass between two 2D points as an SVG path */
function capsule2(ax, ay, bx, by, r) {
  const dx = bx - ax, dy = by - ay;
  const l = Math.hypot(dx, dy) || 1e-6;
  const px = (-dy / l) * r, py = (dx / l) * r;
  return `M ${round(ax - px)} ${round(ay - py)} L ${round(bx - px)} ${round(by - py)} `
    + `A ${round(r)} ${round(r)} 0 0 1 ${round(bx + px)} ${round(by + py)} `
    + `L ${round(ax + px)} ${round(ay + py)} `
    + `A ${round(r)} ${round(r)} 0 0 1 ${round(ax - px)} ${round(ay - py)} Z`;
}
const disc = (x, y, r) => `<circle cx="${round(x)}" cy="${round(y)}" r="${round(r)}"/>`;
const ell = (x, y, rx, ry) => `<ellipse cx="${round(x)}" cy="${round(y)}" rx="${round(rx)}" ry="${round(ry)}"/>`;

/**
 * Render one skeleton frame to an SVG document.
 * p3: {joint: [x,y,z]} meters y-up. scale: svg units per meter.
 * view 'profile-left': screen-x = +z (forward), screen-y = -y, depth = -x.
 */
function skeletonSvg(p3, opts = {}) {
  const S = opts.scale || 645;
  const proj = (j) => {
    const p = p3[j];
    return { x: p[2] * S, y: -p[1] * S, d: -p[0] * S };   // d: +nearer camera
  };
  const q = {};
  for (const k of Object.values(J)) q[k] = proj(k);
  const R2 = (m) => m * S;

  const parts = [];   // {d, cls, fill, svg} — painted far -> near
  const push = (d, cls, fill, svg) => parts.push({ d, cls, fill, svg });

  // depth: far-side limbs first, torso, then near-side limbs/head
  const sideDepth = (s) => q[J['sho' + s]].d;   // l/r by shoulder depth

  for (const s of ['L', 'R']) {
    const far = sideDepth(s) < 0;
    const dArm = -10 + (far ? -0.2 : 0.2);
    const dLeg = -10 + (far ? -0.1 : 0.1);
    // legs
    const hip = q[J['hip' + s]], knee = q[J['knee' + s]], ank = q[J['ank' + s]], toe = q[J['toe' + s]];
    push(dLeg, 'pb-limb', SKIN, capsule2(knee.x, knee.y, ank.x, ank.y, R2(R.shin)));
    // shorts: widened thigh-top capsule (classed as bottom garment)
    const st = lerp3([hip.x, hip.y], [knee.x, knee.y], SHORTS_LEN);
    push(dLeg + 0.01, 'pb-bottom', BOTTOM, capsule2(hip.x, hip.y, st[0], st[1], R2(R.thigh * SHORTS_W)));
    push(dLeg + 0.02, 'pb-limb', SKIN, capsule2(hip.x, hip.y, knee.x, knee.y, R2(R.thigh)));
    push(dLeg, 'pb-joint', SKIN, disc(knee.x, knee.y, R2((R.thigh + R.shin) * 0.42)));
    // foot: capsule ankle->toe + heel disc + shoe slab under it
    push(dLeg + 0.03, 'pb-foot', SHOE, capsule2(ank.x, ank.y, toe.x, toe.y, R2(R.foot)));
    push(dLeg + 0.03, 'pb-foot', SHOE, disc(ank.x, ank.y, R2(R.foot * 1.15)));
    push(dLeg + 0.04, 'pb-detail', 'none',
      `<path d="M ${round(ank.x - R2(R.foot) * 0.4)} ${round(ank.y + R2(R.foot))} L ${round(toe.x)} ${round(toe.y + R2(R.foot))}" stroke="${INK}" stroke-width="${round(S * 0.008)}" fill="none"/>`);
    // arms
    const sho = q[J['sho' + s]], elb = q[J['elb' + s]], wr = q[J['wr' + s]];
    push(dArm, 'pb-limb', SKIN, capsule2(elb.x, elb.y, wr.x, wr.y, R2(R.farm)));
    push(dArm, 'pb-limb', SKIN, capsule2(sho.x, sho.y, elb.x, elb.y, R2(R.uarm)));
    push(dArm, 'pb-joint', SKIN, disc(elb.x, elb.y, R2((R.uarm + R.farm) * 0.4)));
    // hand: palm disc + finger stub along the forearm direction
    const fd = sub([wr.x, wr.y, 0], [elb.x, elb.y, 0]);
    const fl = Math.hypot(fd[0], fd[1]) || 1;
    const hx = wr.x + (fd[0] / fl) * R2(R.hand * 1.15);
    const hy = wr.y + (fd[1] / fl) * R2(R.hand * 1.15);
    push(dArm + 0.02, 'pb-hand', SKIN, disc(wr.x, wr.y, R2(R.hand)));
    push(dArm + 0.02, 'pb-hand', SKIN, capsule2(wr.x, wr.y, hx, hy, R2(R.hand * 0.92)));
  }

  // torso column: capsule per spine bone + pelvis & chest discs
  const pel = q[J.pelvis], sp = q[J.spine], ch = q[J.chest], nk = q[J.neck], hd = q[J.head];
  const tee = (ax, ay, bx, by, r) => push(0, 'pb-top', TOP, capsule2(ax, ay, bx, by, r));
  tee(pel.x, pel.y, sp.x, sp.y, R2(R.spine * TEE_W));
  tee(sp.x, sp.y, ch.x, ch.y, R2(R.chest * TEE_W));
  tee(ch.x, ch.y, nk.x, nk.y, R2(R.neckSeg * 1.5 * TEE_W));
  push(0.01, 'pb-torso', SKIN, disc(pel.x, pel.y, R2(R.pelvis)));
  push(0.01, 'pb-top', TOP, disc(ch.x, ch.y, R2(R.chest * TEE_W * 0.98)));
  // waistband seam where the tee meets the shorts
  const wMid = lerp3([sp.x, sp.y], [pel.x, pel.y], 0.25);
  push(0.02, 'pb-detail', 'none',
    `<path d="M ${round(wMid[0] - R2(R.spine * TEE_W) * 0.9)} ${round(wMid[1])} L ${round(wMid[0] + R2(R.spine * TEE_W) * 0.9)} ${round(wMid[1])}" stroke="${INK}" stroke-width="${round(S * 0.007)}" fill="none" stroke-linecap="round"/>`);

  // clavicle bar + deltoid welds (arm roots live on the chest)
  const clL = q[J.clavL], clR = q[J.clavR];
  push(0.02, 'pb-top', TOP, capsule2(clL.x, clL.y, clR.x, clR.y, R2(R.clavicle)));
  for (const s of ['L', 'R']) {
    push(0.03, 'pb-joint', TOP, disc(q[J['sho' + s]].x, q[J['sho' + s]].y, R2(R.deltoid)));
    push(0.03, 'pb-joint', SKIN, disc(q[J['hip' + s]].x, q[J['hip' + s]].y, R2(R.hipJoint)));
  }

  // neck + head (+ hair cap + face dots, details inked on top)
  push(0.4, 'pb-neck', SKIN, capsule2(nk.x, nk.y, hd.x, hd.y, R2(R.neckCap)));
  const hr = { x: hd.x, y: hd.y - R2(0.02) };
  push(0.4, 'pb-head', SKIN, ell(hr.x, hr.y, R2(R.headX), R2(R.headY)));
  // hair: back-of-skull cap (toward -x in profile) + bun disc
  push(0.41, 'pb-hair', HAIR,
    `<path d="M ${round(hr.x - R2(R.headX))} ${round(hr.y - R2(R.headY) * 0.2)} `
    + `Q ${round(hr.x - R2(R.headX) * 0.9)} ${round(hr.y - R2(R.headY) * 1.25)} ${round(hr.x + R2(R.headX) * 0.55)} ${round(hr.y - R2(R.headY) * 1.05)} `
    + `Q ${round(hr.x + R2(R.headX) * 1.0)} ${round(hr.y - R2(R.headY) * 0.55)} ${round(hr.x + R2(R.headX) * 0.75)} ${round(hr.y - R2(R.headY) * 0.1)} `
    + `Q ${round(hr.x)} ${round(hr.y - R2(R.headY) * 0.45)} ${round(hr.x - R2(R.headX))} ${round(hr.y - R2(R.headY) * 0.2)} Z"/>`);
  push(0.41, 'pb-hair', HAIR, disc(hr.x - R2(R.headX) * 0.85, hr.y - R2(R.headY) * 0.75, R2(0.055)));
  // face: eye dot + smile arc on the leading edge
  const ex = hr.x + R2(R.headX) * 0.55, ey = hr.y - R2(R.headY) * 0.15;
  push(0.42, 'pb-detail', 'none',
    `<circle cx="${round(ex)}" cy="${round(ey)}" r="${round(S * 0.009)}" fill="${INK}"/>`
    + `<path d="M ${round(ex - R2(0.012))} ${round(ey + R2(0.035))} Q ${round(ex + R2(0.01))} ${round(ey + R2(0.05))} ${round(ex + R2(0.03))} ${round(ey + R2(0.03))}" stroke="${INK}" stroke-width="${round(S * 0.007)}" fill="none"/>`);

  parts.sort((a, b) => a.d - b.d);
  const body = parts.map((p) => {
    if (p.cls === 'pb-detail') return `<g class="pb-detail" fill="none">${p.svg.replace(/fill="[^"]*"/g, '')}</g>`;
    return `<g class="${p.cls}" fill="${p.fill}">${p.svg}</g>`;
  }).join('\n');

  // bounds
  const xs = [], ys = [];
  for (const k of Object.keys(q)) { xs.push(q[k].x); ys.push(q[k].y); }
  const pad = R2(0.35);
  const x0 = Math.min(...xs) - pad, x1 = Math.max(...xs) + pad;
  const y0 = Math.min(...ys) - pad - R2(0.35), y1 = Math.max(...ys) + pad + R2(0.25);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${round(x0)} ${round(y0)} ${round(x1 - x0)} ${round(y1 - y0)}">`
    + `<g class="pb-figure">\n${body}\n</g></svg>`;
}

// ---------------- CLI ----------------
const req = JSON.parse(process.argv[2] || '{}');
const outDir = process.argv[3] || '/tmp/skin_rig_out';
const nF = Number(process.argv[4] || 16), fps = Number(process.argv[5] || 24);
fs.mkdirSync(outDir, { recursive: true });

function sampleAny(r, t) {
  if (r.cmuClip) return sampler.sample(r.cmuClip, t, r);
  if (V5) {
    const st = V5.sample(r, t);
    if (!(st && st.blocked)) return st;
    if (!sampler.sample(r.action || '', 0).blocked) return sampler.sample(r.action, t, r);
    return st;
  }
  return sampler.sample(r.action || 'CMU_WALK_1', t, r);
}

const meta = [];
for (let i = 0; i < nF; i++) {
  const t = i / fps;
  const st = sampleAny(req, t);
  if (st.blocked) { console.error('blocked', st.failure); break; }
  const svg = skeletonSvg(st.pose3d, { scale: 645 });
  fs.writeFileSync(path.join(outDir, `g${String(i).padStart(3, '0')}.svg`), svg);
  meta.push({ t, root: st.pose3d.root || [0, 0, 0] });
}
fs.writeFileSync(path.join(outDir, 'poses.json'), JSON.stringify(meta));
console.log('wrote', meta.length, 'frames to', outDir);
