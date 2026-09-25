/* Sample the NexStick Unified Performance engine -> JSON pose3d joints.
 * usage: node mocap.cjs '<json request>' <seconds> <fps>
 * request: {action:'walk'|'run'|'walk_carry'|'jump_start'|..., speedMps?} */
const path = require('path');
const BOOT = path.resolve(__dirname, '../../../../engines/explainer/NexStudio_Explainer_Execution_Body_V2/runtime-assets/explainer-motion-v1/library/nexstick-v5.1/runtime/node-bootstrap-v5.js');
const V5 = require(BOOT);
const req = JSON.parse(process.argv[2] || '{"action":"walk"}');
const dur = Number(process.argv[3] || 4), fps = Number(process.argv[4] || 24);
const clipDur = V5.duration ? V5.duration(req) : 0;
const out = { action: req.action, clipSeconds: clipDur, fps, joints: null, frames: [] };
for (let i = 0; i < Math.round(dur * fps); i++) {
  const t = i / fps;
  const st = V5.sample(req, t);
  if (st.blocked) { out.blocked = st.failure || true; break; }
  if (!out.joints) out.joints = Object.keys(st.pose3d);
  out.frames.push({ t, pose: st.pose3d, root: st.pose3d.root, plant: st.footPlant || null });
}
process.stdout.write(JSON.stringify(out));
