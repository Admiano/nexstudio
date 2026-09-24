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
      head: { yaw: 0, pitch: tHead - tNeck },   // nod from the head bone; yaw
                                              // unrecoverable from positions
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
const clipRef = (req.cmuClip || req.action || '').toUpperCase();
const athletic = /^(EX_|.*(CRAWL|CLIMB|LADDER|HOPSCOTCH|CARTWHEEL|STRETCH|YOGA|BOXING|JOG|RUN_|SPRINT|DIVE|SWIM|FALL|ROLL))/.test(clipRef);
const look = athletic
  ? { top: { garment: 'vest' }, bottom: { garment: 'shorts' } }
  : { top: { garment: 'jacket' } };

const meta = [];
for (let i = 0; i < nF; i++) {
  const t = i / fps;
  const st = sampleAny(req, t);
  if (st.blocked) { console.error('blocked', st.failure); break; }
  const { pose, world } = poseFromMocap(st.pose3d);
  const scale = 1000 / 1.55;   // rig units per meter (~adult 1.55m skeleton)
  const pel = world.pelvis || [0, 0.877, 0];
  const out = Renderer.renderPose({
    proportion, height: 1000, view: 'profile-left', pose,
    world: {
      pitch: world.pitch,
      root: {
        x: 0,
        y: (pel[1] - 0.877) * scale,
        z: pel[2] * scale,
      },
    },
    look, face: 'warm', background: false, grain: false,
    hands: {
      left: st.hands && st.hands.left && st.hands.left.pose,
      right: st.hands && st.hands.right && st.hands.right.pose,
    },
  });
  // strip only non-line layers (rim highlights, contact shadow) and any
  // degenerate element (pb-fold can emit a ~2m ellipse under stride poses);
  // every garment/detail stroke stays for the elite look.
  const svg = out.svg
    .replace(/<g class="pb-(rim|shadow)"[^>]*>.*?<\/g>/gs, '')
    .replace(/<defs>.*?<\/defs>/s, '')
    .replace(/<g class="pb-fold"[^>]*>\s*<ellipse[^>]*ry="([0-9.]+)"[^>]*\/><\/g>/gs,
             (m, ry) => (+ry > 200 ? '' : m));
  const p = path.join(outDir, `g${String(i).padStart(3, '0')}.svg`);
  fs.writeFileSync(p, svg);
  meta.push({ t, pose, root: st.pose3d.root });
}
fs.writeFileSync(path.join(outDir, 'poses.json'), JSON.stringify(meta, null, 1));
console.log('wrote', meta.length, 'frames to', outDir);
