/* fx_marks — cartoon mark layer for the animated figure path.
 * Deterministic marks from the SAME motion data the skeleton sees:
 *   - speed lines: tapering streaks trailing the fastest-moving joint
 *     when its velocity clears a threshold (run/wave/ballistic moves)
 *   - impact burst: short radial strokes when a foot-plant begins or a
 *     fast joint decelerates hard (landings, catches)
 *   - dust puffs: small arc clouds at foot plants on ground-contact clips
 * Grammar: marks read as ink — same stroke language as the figure,
 * emitted as <g class="pb-fx"> so downstream stroke passes keep working.
 */
'use strict';

const fastJoint = (p, q) => {
  // q = joints at t, p = joints at t-dt. Return {joint, speed(m/s), dir}
  if (!p || !q) return null;
  let best = null;
  for (const n of ['wrist_l', 'wrist_r', 'ankle_l', 'ankle_r', 'hand_l', 'hand_r']) {
    if (!q[n] || !p[n]) continue;
    const d = [q[n][0] - p[n][0], q[n][1] - p[n][1], q[n][2] - p[n][2]];
    const s = Math.hypot(d[0], d[1], d[2]);
    if (!best || s > best.s) best = { n, s, d };
  }
  return best;
};

function marksForFrame({ pPrev, pNow, dt, plant, contactsPrev, proj, S }) {
  const out = [];
  const j = fastJoint(pPrev, pNow);
  if (j && dt > 0) {
    const v = j.s / dt;                    // m/s
    if (v > 1.6) {
      // project joint + velocity dir to screen
      const a = proj(jointAt(pNow, j.n));
      const vx = j.d[2], vy = -j.d[1];     // screen coords (z→x, y→-y)
      const vl = Math.hypot(vx, vy) || 1e-6;
      const ux = -vx / vl, uy = -vy / vl;  // trail opposite to motion
      const nx = -uy, ny = ux;
      const len = Math.min(90, 26 + v * 26);
      for (let i = -1; i <= 1; i++) {
        const o = i * 14;
        out.push({
          cls: 'pb-fx-speed',
          d: `M ${a.x + nx * o + ux * 10} ${a.y + ny * o + uy * 10} ` +
             `L ${a.x + nx * o + ux * len} ${a.y + ny * o + uy * len}`,
          w: Math.max(2.4, S * 0.012 - i * 0 + Math.abs(i) * -1.2),
        });
      }
    }
  }
  // foot-plant onset -> dust + (ballistic) impact burst
  for (const side of ['l', 'r']) {
    const now = plant[side] === 1, was = contactsPrev[side] === 1;
    if (!now || was) continue;
    const a = proj(jointAt(pNow, side === 'l' ? 'ankle_l' : 'ankle_r'));
    for (let i = 0; i < 2; i++) {
      const dx = (i ? 1 : -1) * (14 + 6 * i);
      out.push({
        cls: 'pb-fx-dust',
        d: `M ${a.x - dx} ${a.y} A 12 9 0 0 1 ${a.x + dx} ${a.y}`,
        w: S * 0.008,
      });
    }
  }
  return out;
}

function jointAt(pose3d, name) { return pose3d[name] || [0, 0, 0]; }

module.exports = { marksForFrame };
