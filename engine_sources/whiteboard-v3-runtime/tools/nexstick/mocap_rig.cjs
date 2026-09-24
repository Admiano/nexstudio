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
const tiltDown = d => Math.asin(Math.max(-1, Math.min(1, d[2]))) * DEG;      // z fwd
const swingDown = d => Math.atan2(d[0], -d[1]) * DEG;                       // x lateral
const tiltUp = d => Math.asin(Math.max(-1, Math.min(1, d[2]))) * DEG;
const swingUp = d => Math.atan2(d[0], d[1]) * DEG;
const bone = (p, a, b) => nrm(sub(p[b], p[a]));

function poseFromMocap(p3) {
  const tSpine = tiltUp(bone(p3, 'pelvis', 'spine'));
  const tChest = tiltUp(bone(p3, 'spine', 'chest'));
  const tNeck = tiltUp(bone(p3, 'chest', 'neck'));
  const sSpine = swingUp(bone(p3, 'pelvis', 'spine'));
  const sChest = swingUp(bone(p3, 'spine', 'chest'));
  const sNeck = swingUp(bone(p3, 'chest', 'neck'));

  const limb = (side, sgn) => {
    const th = bone(p3, `hip_${side}`, `knee_${side}`);
    const sh = bone(p3, `knee_${side}`, `ankle_${side}`);
    const ft = bone(p3, `ankle_${side}`, `toe_${side}`);
    const ua = bone(p3, `shoulder_${side}`, `elbow_${side}`);
    const fa = bone(p3, `elbow_${side}`, `wrist_${side}`);
    const leg = {
      hip: { tilt: tiltDown(th), swing: sgn * swingDown(th) },
      knee: { tilt: tiltDown(sh) - tiltDown(th), swing: sgn * (swingDown(sh) - swingDown(th)) },
      ankle: { tilt: tiltDown(ft) - 90 },
    };
    const arm = {
      shoulder: { tilt: tiltDown(ua), swing: sgn * swingDown(ua) },
      elbow: { tilt: tiltDown(fa) - tiltDown(ua), swing: sgn * (swingDown(fa) - swingDown(ua)) },
    };
    return { leg, arm };
  };
  const L = limb('l', -1), R = limb('r', +1);
  const tHead = tiltUp(bone(p3, 'neck', 'head'));

  return {
    spine: { tilt: tSpine, swing: sSpine },
    chest: { tilt: tChest - tSpine, swing: sChest - sSpine },
    neck: { tilt: tNeck - tChest, swing: sNeck - sChest },
    head: { yaw: 0, pitch: tHead - tNeck },   // nod from the head bone; yaw
                                            // unrecoverable from positions
    legLeft: L.leg, legRight: R.leg,
    armLeft: L.arm, armRight: R.arm,
  };
}

const req = JSON.parse(process.argv[2] || '{"action":"walk","speedMps":1.15}');
const outDir = process.argv[3] || '/tmp/mocap_rig_frames';
const nF = Number(process.argv[4] || 16), fps = Number(process.argv[5] || 24);
const proportion = process.argv[6] || 'adult-average';
fs.mkdirSync(outDir, { recursive: true });

const meta = [];
for (let i = 0; i < nF; i++) {
  const t = i / fps;
  const st = sampleAny(req, t);
  if (st.blocked) { console.error('blocked', st.failure); break; }
  const pose = poseFromMocap(st.pose3d);
  const out = Renderer.renderPose({
    proportion, height: 1000, view: 'profile-left', pose,
    look: { top: { garment: 'jacket' } }, face: 'warm', background: false, grain: false,
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
