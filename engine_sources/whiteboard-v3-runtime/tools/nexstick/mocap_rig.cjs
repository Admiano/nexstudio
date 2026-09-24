/* Bridge: nexstick mocap (V5 pose3d joints) -> paper-cast rig pose -> SVG.
 * Real certified motion driving the merged-silhouette figure look.
 * usage: node mocap_rig.cjs '<json request>' <outDir> <nFrames> <fps> [proportion]
 */
const path = require('path');
const fs = require('fs');
const BOOT = path.resolve(__dirname, '../../../../engines/explainer/NexStudio_Explainer_Execution_Body_V2/runtime-assets/explainer-motion-v1/library/nexstick-v5.1/runtime/node-bootstrap-v5.js');
const nodeReq = require;
const cache = {};
function load(f) {
  const abs = path.resolve(__dirname, '../paper_cast', f);
  if (cache[abs]) return cache[abs];
  const src = fs.readFileSync(abs, 'utf8');
  const m = { exports: {} };
  const req = (p) => p.startsWith('./') ? load(p.slice(2)) : nodeReq(p);
  new Function('module', 'exports', 'require', src)(m, m.exports, req);
  cache[abs] = m.exports;
  return m.exports;
}
const Renderer = load('paperbook-figure.js');
const Acting = load('cast-acting.js');
const Rig = load('paper-cast-rig.js');
const V5 = nodeReq(BOOT);
let CMU = null;
try { CMU = nodeReq(path.resolve(__dirname, 'cmu_sampler.cjs')); } catch (e) { /* vault not built yet */ }
function sampleAny(req, t) {
  if (CMU && req.cmuClip) return CMU.sample(req.cmuClip, t, req);
  const st = V5.sample(req, t);
  if (st.blocked && CMU && !CMU.sample(req.action || '', 0).blocked) return CMU.sample(req.action, t, req);
  return st;
}

const DEG = 180 / Math.PI;
const nrm = v => { const l = Math.hypot(v[0], v[1], v[2]) || 1e-9; return [v[0] / l, v[1] / l, v[2] / l]; };
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
// Full-range sagittal pitch: 0 = straight down/up, +90 = forward,
// -90 = backward, ±180 = straight up/down. asin() degenerates on
// overhead/lying poses (pull-up arms, prone legs) — atan2 covers them.
const tiltDown = d => Math.atan2(d[2], -d[1]) * DEG;                        // from -y
const swingDown = d => Math.atan2(d[0], -d[1]) * DEG;                       // x lateral
const tiltUp = d => Math.atan2(d[2], d[1]) * DEG;                           // from +y
const swingUp = d => Math.atan2(d[0], d[1]) * DEG;
const wrap = a => { a = ((a + 180) % 360 + 360) % 360 - 180; return a; };
const bone = (p, a, b) => nrm(sub(p[b], p[a]));

// Body facing azimuth from the lateral skeleton axes (clavicle + hip
// lines): a person facing +z has their LEFT side at +x, so
// facing = (-dz, dx) of the (left - right) lateral vector. Positions
// carry this whole-body turn that a fixed view would flatten away.
function bodyAz(p3) {
  const lc = sub(p3['clavicle_l'], p3['clavicle_r']);
  const lh = sub(p3['hip_l'], p3['hip_r']);
  const fx = -(lc[2] + lh[2]), fz = lc[0] + lh[0];
  return Math.atan2(fx, fz) * DEG;
}

function poseFromMocap(p3) {
  // Body frame: the spine axis (pelvis->neck) IS the figure's up-axis.
  // World pitch P is how far that axis leans/lies in the sagittal plane;
  // every absolute bone tilt is expressed relative to it, so the rig can
  // re-apply P as a whole-figure world rotation (stand -> sit -> prone).
  const spineDir = nrm(sub(p3['neck'], p3['pelvis']));
  const P = Math.atan2(spineDir[2], spineDir[1]) * DEG;      // + = lies forward
  const S = Math.atan2(spineDir[0], spineDir[1]) * DEG;      // lateral lean

  const tSpine = tiltUp(bone(p3, 'pelvis', 'spine'));
  const tChest = tiltUp(bone(p3, 'spine', 'chest'));
  const tNeck = tiltUp(bone(p3, 'chest', 'neck'));
  const sSpine = swingUp(bone(p3, 'pelvis', 'spine')) - S;
  const sChest = swingUp(bone(p3, 'spine', 'chest'));
  const sNeck = swingUp(bone(p3, 'chest', 'neck'));

  const limb = (side, sgn) => {
    const th = bone(p3, `hip_${side}`, `knee_${side}`);
    const sh = bone(p3, `knee_${side}`, `ankle_${side}`);
    const ft = bone(p3, `ankle_${side}`, `toe_${side}`);
    const ua = bone(p3, `shoulder_${side}`, `elbow_${side}`);
    const fa = bone(p3, `elbow_${side}`, `wrist_${side}`);
    // Body-frame tilts: body-down sits at pitch -P in world terms, so a
    // limb's deviation from the body's own down-axis is tilt + P.
    const leg = {
      hip: { tilt: tiltDown(th) + P, swing: sgn * swingDown(th) },
      knee: { tilt: wrap(tiltDown(sh) - tiltDown(th)), swing: sgn * wrap(swingDown(sh) - swingDown(th)) },
      ankle: { tilt: wrap(tiltDown(ft) + P - 90) },
    };
    const arm = {
      shoulder: { tilt: wrap(tiltDown(ua) + P), swing: sgn * swingDown(ua) },
      elbow: { tilt: wrap(tiltDown(fa) - tiltDown(ua)), swing: sgn * wrap(swingDown(fa) - swingDown(ua)) },
    };
    return { leg, arm };
  };
  const L = limb('l', -1), R = limb('r', +1);
  const tHead = tiltUp(bone(p3, 'neck', 'head'));

  // Arms hanging near vertical: settle them just behind the hip line so
  // hands rest at the body's edge instead of landing ON the torso front
  // (the "arms inside the clothes" read at profile views). Poses that
  // genuinely carry the arm forward/back (|tilt| >= 14) are untouched.
  for (const arm of [L.arm, R.arm]) {
    const t = arm.shoulder.tilt;
    if (Math.abs(t) < 14) arm.shoulder.tilt = Math.min(t, -9);
  }

  // Pelvic coupling: a real pelvis rotates with deep hip flexion (sit,
  // squat, bend). The rigid torso slab must pitch with it or the thigh
  // reads as bolted onto a pillar — the "dislocated waist" look.
  const hipFlex = Math.max(L.leg.hip.tilt, R.leg.hip.tilt);
  const pelvicTuck = Math.max(0, Math.min(55, hipFlex - 72)) * 0.55;

  return {
    pose: {
      spine: { tilt: wrap(tSpine - P) + pelvicTuck, swing: sSpine },
      chest: { tilt: wrap(tChest - tSpine), swing: sChest - sSpine },
      neck: { tilt: wrap(tNeck - tChest), swing: sNeck - sChest },
      head: { yaw: 0, pitch: tHead - tNeck },   // yaw injected by caller
                                              // when the clip carries roty
      legLeft: L.leg, legRight: R.leg,
      armLeft: L.arm, armRight: R.arm,
    },
    world: { pitch: P, pelvis: p3.pelvis },
  };
}

const req = JSON.parse(process.argv[2] || '{"action":"walk","speedMps":1.15}');
const outDir = process.argv[3] || '/tmp/mocap_rig_frames';
const nF = Number(process.argv[4] || 16), fps = Number(process.argv[5] || 24);
const proportion = process.argv[6] || 'adult-average';
fs.mkdirSync(outDir, { recursive: true });

// Wardrobe follows physics: nobody deadlifts in an A-line skirt. Floor /
// hang / athletic clips dress fitted (vest + shorts) so the garment reads
// as body contour; upright story motions keep the draped wardrobe.
// narration-driven clip pick: "say"/"text" resolves through clip_select
// when no explicit clip was requested.
if (!req.cmuClip && (req.say || req.text)) {
  const pick = require('./clip_select.cjs')
    .selectClip(req.say || req.text, CMU ? CMU.vault().clips : null);
  if (pick) req.cmuClip = pick;
}

const clipRef = (req.cmuClip || req.action || '').toUpperCase();
const athletic = /^(EX_|.*(CRAWL|CLIMB|LADDER|HOPSCOTCH|CARTWHEEL|STRETCH|YOGA|BOXING|JOG|RUN_|SPRINT|DIVE|SWIM|FALL|ROLL))/.test(clipRef);
const look = athletic
  ? { top: { garment: 'vest' }, bottom: { garment: 'shorts' } }
  : { top: { garment: 'jacket' } };

// viseme timeline: req.visemes = path to visemes.py output (rhubarb cues)
// or an inline [{start,end,viseme}] array — speaking figures lip-sync to VO.
let VISEMES = null;
if (req.visemes) {
  const raw = typeof req.visemes === 'string'
    ? JSON.parse(fs.readFileSync(req.visemes, 'utf8'))
    : req.visemes;
  VISEMES = raw.cues || raw;
}
const visemeAt = (t) => {
  if (!VISEMES) return null;
  const c = VISEMES.find(c => c.start <= t && t <= c.end);
  return c ? c.viseme : 'rest';
};

// cartoon mark layer: speed streaks + impact bursts + foot-plant dust,
// all derived from the same motion data driving the skeleton.
const FX = req.fx ? require('./fx_marks.cjs') : null;
const BALLISTIC = /^(EX_BURPEE|EX_JUMPING_JACK|.*(JUMP|HOPSCOTCH|CARTWHEEL|DIVE|SPRINT))/.test(clipRef);
const SCALE = 1000 / 1.55;
// world-space joint -> figure screen coords (mirrors paper-cast-rig's
// world transform + profile-left projection: x_screen = -z, y = -y)
const jointScreen = (j, pel, pitchDeg, root, yawRad) => {
  const dx = (j[0] - pel[0]) * SCALE, dy = (j[1] - pel[1]) * SCALE,
        dz = (j[2] - pel[2]) * SCALE;
  const p = pitchDeg * Math.PI / 180, pc = Math.cos(p), ps = Math.sin(p);
  const ry = dy * pc - dz * ps, rz = dy * ps + dz * pc;
  const yw = (yawRad === undefined ? -Math.PI / 2 : yawRad);
  return { x: dx * Math.cos(yw) + (rz + root.z) * Math.sin(yw),
           y: -(ry + root.y) };
};

// acting layer: breath + sway + weight + head life on top of the mocap
// pose, plus timed gesture beats (req.beats) and Face.at (blink/gaze).
// The mocap pose is rebuilt per frame as the performer's base, so gesture
// reaches blend from wherever the body actually is.
const ACTING = !!(req.acting || (req.beats && req.beats.length));
const beatClock = req.beatOffset || 0;

// Baseline facing at t=0: the head's relative yaw = its world azimuth
// change vs its own t=0, re-expressed in the current body frame
// (local BVH joint axes are arbitrary, so differences cancel the offset).
const NOYAW = !!process.env.NOYAW;
const st0 = sampleAny(req, 0);
const az0 = st0.pose3d ? bodyAz(st0.pose3d) : 0;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
// Constant offset between the head joint's world azimuth and the body's
// facing azimuth: BVH local axes are arbitrary, so measure the median
// (roty - az) over the clip and cancel it — real turns survive, the
// convention bias doesn't.
const headOff = (() => {
  const ds = [];
  const dur = st0.duration || nF / fps;
  for (let k = 0; k < 12; k++) {
    const s = sampleAny(req, dur * k / 12);
    if (s.roty !== null && s.roty !== undefined && s.pose3d) {
      ds.push(wrap(s.roty - bodyAz(s.pose3d)));
    }
  }
  ds.sort((a, b) => a - b);
  return ds.length ? ds[ds.length >> 1] : 0;
})();
// Baseline facing for the view: circular mean of the body azimuth over
// the clip — frame 0 can be a calibration pose (actor turning to mark),
// so the dominant facing is the honest "forward" of the performance.
const azBase = (() => {
  let sx = 0, sz = 0, n = 0;
  const dur = (st0.duration || nF / fps);
  for (let k = 0; k < 8; k++) {
    const s = sampleAny(req, dur * k / 8);
    if (!s.pose3d) continue;
    const a = bodyAz(s.pose3d) / DEG;
    sx += Math.sin(a); sz += Math.cos(a); n++;
  }
  return n ? Math.atan2(sx / n, sz / n) * DEG : az0;
})();

// ---- optional second figure: two-person scenes (shake hands, talk,
// comfort). req.other = {cmuClip|say|action, z, facing:'left'|'right',
// proportion, front}. Each figure keeps its own facing baseline.
const OTHER = req.other && (req.other.cmuClip || req.other.say || req.other.text || req.other.action);
let oAzBase = 0, oAz0 = 0, oReq = null, oHeadOff = 0;
if (OTHER) {
  oReq = { ...req.other };
  if (!oReq.cmuClip && (oReq.say || oReq.text)) {
    const pk = require('./clip_select.cjs')
      .selectClip(oReq.say || oReq.text, CMU ? CMU.vault().clips : null);
    if (pk) oReq.cmuClip = pk;
  }
  const s0 = sampleAny(oReq, 0);
  oAz0 = s0.pose3d ? bodyAz(s0.pose3d) : 0;
  let sx = 0, sz = 0, n = 0;
  const dur = s0.duration || nF / fps;
  for (let k = 0; k < 8; k++) {
    const s = sampleAny(oReq, dur * k / 8);
    if (!s.pose3d) continue;
    const a = bodyAz(s.pose3d) / DEG;
    sx += Math.sin(a); sz += Math.cos(a); n++;
  }
  oAzBase = n ? Math.atan2(sx / n, sz / n) * DEG : oAz0;
  const ds = [];
  for (let k = 0; k < 12; k++) {
    const s = sampleAny(oReq, dur * k / 12);
    if (s.roty !== null && s.roty !== undefined && s.pose3d) {
      ds.push(wrap(s.roty - bodyAz(s.pose3d)));
    }
  }
  ds.sort((a, b) => a - b);
  oHeadOff = ds.length ? ds[ds.length >> 1] : 0;
}

const meta = [];
let prevPose3d = null, prevPlant = { l: 0, r: 0 };
for (let i = 0; i < nF; i++) {
  const t = i / fps;
  const st = sampleAny(req, t);
  if (st.blocked) { console.error('blocked', st.failure); break; }
  const { pose: mocapPose, world } = poseFromMocap(st.pose3d);
  const az = bodyAz(st.pose3d);
  if (st.roty !== null && st.roty !== undefined && !NOYAW) {
    // relative head yaw = head's world-azimuth delta vs clip baseline,
    // re-expressed in the body frame (cancels arbitrary BVH local axes)
    mocapPose.head.yaw = clamp(
      wrap(st.roty - az - headOff), -80, 80);
  }
  // Capture world axes are arbitrary — re-baseline facing to the clip's
  // dominant azimuth so every clip opens profile-left. Real turns damp
  // into the rig's good envelope (±~35° lean toward camera): the paper-
  // rig silhouette reads broken near-frontal, so a turn reads as lean +
  // head yaw rather than crossing into frontal/back territory.
  const viewYaw = NOYAW ? -90 : -90 + 38 * Math.tanh(wrap(az - azBase) / 55);
  let pose = mocapPose;
  let actingFace = null;
  if (ACTING) {
    const perf = Acting.perform({
      pose: mocapPose, proportion,
      beats: (req.beats || []).map(b => ({ ...b, at: b.at + beatClock, end: b.end + beatClock })),
      personality: req.personality,
      emotion: req.emotion || 'warm',
      gaze: req.gaze, listening: req.listening,
      id: req.id || 'mocap-fig',
    });
    const a = perf.at(t);
    pose = a.pose;
    actingFace = a.face;
  }
  const scale = SCALE;         // rig units per meter (~adult 1.55m skeleton)
  const pel = world.pelvis || [0, 0.877, 0];
  const root = {
    x: 0,
    y: (pel[1] - 0.877) * scale,
    z: pel[2] * scale,
  };
  const viseme = visemeAt(t);
  const face = actingFace
    ? actingFace
    : VISEMES
      ? { emotion: 'warm', speaking: true, viseme: viseme || 'rest', id: 'fig' }
      : 'warm';
  const out = Renderer.renderPose({
    proportion, height: 1000, view: viewYaw, pose,
    world: { pitch: world.pitch, root },
    look, face, background: false, grain: false,
    hands: {
      left: st.hands && st.hands.left && st.hands.left.pose,
      right: st.hands && st.hands.right && st.hands.right.pose,
    },
  });
  // strip only non-line layers (rim highlights, contact shadow) and any
  // degenerate element (pb-fold can emit a ~2m ellipse under stride poses);
  // every garment/detail stroke stays for the elite look.
  let svg = out.svg
    .replace(/<g class="pb-(rim|shadow)"[^>]*>.*?<\/g>/gs, '')
    .replace(/<defs>.*?<\/defs>/s, '')
    .replace(/<g class="pb-fold"[^>]*>\s*<ellipse[^>]*ry="([0-9.]+)"[^>]*\/><\/g>/gs,
             (m, ry) => (+ry > 200 ? '' : m));
  // squash on impact onset for ballistic clips — a ~3-frame cartoon
  // settle when a foot plants after airborne motion (sx+, sy-).
  const plantNow = st.plant || { l: 0, r: 0 };
  const impact = BALLISTIC &&
    ((plantNow.l === 1 && prevPlant.l !== 1) ||
     (plantNow.r === 1 && prevPlant.r !== 1));
  if (impact) {
    const a = jointScreen(pel, pel, world.pitch, root);
    svg = svg.replace(/<svg([^>]*)>([\s\S]*)<\/svg>/,
      `<svg$1><g transform="translate(${a.x.toFixed(1)},${a.y.toFixed(1)}) scale(1.05,0.92) translate(${(-a.x).toFixed(1)},${(-a.y).toFixed(1)})">$2</g></svg>`);
  }
  if (FX) {
    const marks = FX.marksForFrame({
      pPrev: prevPose3d, pNow: st.pose3d, dt: 1 / fps,
      plant: plantNow, contactsPrev: prevPlant,
      proj: (j) => jointScreen(j, pel, world.pitch, root), S: scale,
    });
    if (BALLISTIC && impact) {
      // radial burst around the contact ankle
      for (const side of ['l', 'r']) {
        if (!(plantNow[side] === 1 && prevPlant[side] !== 1)) continue;
        const a = jointScreen(st.pose3d['ankle_' + side], pel, world.pitch, root);
        for (let k = 0; k < 8; k++) {
          const th = (k / 8) * Math.PI * 2 + 0.3;
          marks.push({
            cls: 'pb-fx-burst',
            d: `M ${a.x + Math.cos(th) * 22} ${a.y + Math.sin(th) * 22} ` +
               `L ${a.x + Math.cos(th) * 48} ${a.y + Math.sin(th) * 48}`,
            w: scale * 0.011,
          });
        }
      }
    }
    if (marks.length) {
      const g = marks.map(m =>
        `<g class="${m.cls}" fill="none"><path d="${m.d}" stroke="#2a1c12" stroke-width="${m.w.toFixed(1)}" stroke-linecap="round"/></g>`).join('');
      svg = svg.replace('</svg>', g + '</svg>');
    }
  }
  if (OTHER) {
    const st2 = sampleAny(oReq, t + (oReq.t || 0));
    if (st2 && !st2.blocked) {
      const { pose: p2, world: w2 } = poseFromMocap(st2.pose3d);
      const az2 = bodyAz(st2.pose3d);
      if (st2.roty !== null && st2.roty !== undefined && !NOYAW) {
        p2.head.yaw = clamp(wrap(st2.roty - az2 - oHeadOff), -80, 80);
      }
      const pel2 = w2.pelvis || [0, 0.877, 0];
      const out2 = Renderer.renderPose({
        proportion: oReq.proportion || proportion, height: 1000,
        view: (oReq.facing === 'right' ? 90 : -90) + wrap(az2 - oAzBase),
        pose: p2,
        world: { pitch: w2.pitch,
                 root: { x: 0, y: (pel2[1] - 0.877) * scale,
                         z: ((oReq.z || 0) + pel2[2]) * scale } },
        look: oReq.look || look, face: oReq.emotion || 'warm',
        background: false, grain: false,
        hands: {
          left: st2.hands && st2.hands.left && st2.hands.left.pose,
          right: st2.hands && st2.hands.right && st2.hands.right.pose,
        },
      });
      let svg2 = out2.svg
        .replace(/<g class="pb-(rim|shadow)"[^>]*>.*?<\/g>/gs, '')
        .replace(/<defs>.*?<\/defs>/s, '')
        .replace(/<svg[^>]*>/, '').replace(/<\/svg>/, '');
      if (oReq.front) svg = svg.replace('</svg>', svg2 + '</svg>');
      else svg = svg.replace(/(<svg[^>]*>)/, '$1' + svg2);
      // the first figure's viewBox only spans its own silhouette — grow
      // the canvas to cover the partner's offset + body width.
      svg = svg.replace(/viewBox="(-?[0-9.]+) (-?[0-9.]+) ([0-9.]+) ([0-9.]+)"/,
        (m, x0, y0, w, h) => {
          const need = Math.abs((oReq.z || 0)) * scale + 520;
          const x0n = Math.min(+x0, +x0 + Math.min(0, (oReq.z || 0) * scale) - 120);
          const x1n = Math.max(+x0 + +w, +x0 + Math.max(0, (oReq.z || 0) * scale) + need);
          return `viewBox="${x0n.toFixed(1)} ${y0} ${(x1n - x0n).toFixed(1)} ${h}"`;
        });
    }
  }
  prevPose3d = st.pose3d;
  prevPlant = plantNow;
  const p = path.join(outDir, `g${String(i).padStart(3, '0')}.svg`);
  fs.writeFileSync(p, svg);
  meta.push({ t, pose, root: st.pose3d.root });
}
fs.writeFileSync(path.join(outDir, 'poses.json'), JSON.stringify(meta, null, 1));
console.log('wrote', meta.length, 'frames to', outDir);
