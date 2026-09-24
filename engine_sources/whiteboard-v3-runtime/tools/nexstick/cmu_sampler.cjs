/* CMU mocap vault sampler — same contract as NexUAL2SamplerV5.
 * sample(clipName, t, opts) -> {pose3d, hands, footPlant, donorContacts, ...}
 * Vault: tools/nexstick/compiled/cmu_motion_vault_v5.json (converted by
 * bvh_to_vault.py from the CMU Graphics Lab corpus — free for all uses).
 */
'use strict';
const path = require('path');
const fs = require('fs');
const VAULT_PATH = path.resolve(__dirname, 'compiled', 'cmu_motion_vault_v5.json');
let V = null;
function vault() {
  if (!V) V = JSON.parse(fs.readFileSync(VAULT_PATH, 'utf8'));
  return V;
}
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
function binaryIndex(times, t) {
  let lo = 0, hi = times.length - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (times[m] <= t) lo = m; else hi = m; }
  return lo;
}
function mirrorPose(pose) {
  const out = {};
  for (const k in pose) {
    let nk = k;
    if (k.endsWith('_l')) nk = k.slice(0, -2) + '_r';
    else if (k.endsWith('_r')) nk = k.slice(0, -2) + '_l';
    const p = pose[k];
    out[nk] = [-p[0], p[1], p[2]];
  }
  return out;
}
function sample(ref, t, opts = {}) {
  const V = vault();
  const c = V.clips[ref];
  if (!c) return { blocked: true, failure: 'CMU_UNKNOWN_CLIP', ref };
  const raw = Math.max(0, +t || 0);
  const loop = opts.loop ?? c.loop;
  let cycle = 0, tt = raw;
  if (loop && c.duration > 0) { cycle = Math.floor(raw / c.duration); tt = raw - cycle * c.duration; }
  else tt = clamp(raw, 0, c.duration);
  const i = binaryIndex(c.times, tt), a = c.times[i], b = c.times[i + 1];
  const w = b === a ? 0 : (tt - a) / (b - a);
  let pose = {};
  for (let j = 0; j < V.joints.length; j++) {
    const n = V.joints[j], p0 = c.frames[i][j], p1 = c.frames[i + 1][j] || c.frames[i][j];
    pose[n] = [p0[0] + (p1[0] - p0[0]) * w, p0[1] + (p1[0] - p0[1]) * w, p0[2] + (p1[0] - p0[2]) * w];
  }
  let cycleOffset = [0, 0, 0];
  if (loop && cycle && c.rootDelta) {
    cycleOffset = [c.rootDelta[0] * cycle, c.rootDelta[1] * cycle, c.rootDelta[2] * cycle];
    for (const n in pose) pose[n] = [pose[n][0] + cycleOffset[0], pose[n][1] + cycleOffset[1], pose[n][2] + cycleOffset[2]];
  }
  const mirror = !!opts.mirror;
  if (mirror) { pose = mirrorPose(pose); cycleOffset = [-cycleOffset[0], cycleOffset[1], cycleOffset[2]]; }
  // foot plant contacts
  const plant = { l: 0, r: 0 };
  const active = [];
  for (const side of ['l', 'r']) {
    const src = mirror ? (side === 'l' ? 'r' : 'l') : side;
    for (const seg of (c.contacts && c.contacts[src]) || []) {
      if (tt >= seg.start && tt <= seg.end) {
        plant[side] = 1;
        const an = mirror ? [-seg.anchor[0], seg.anchor[1], seg.anchor[2]] : seg.anchor;
        active.push({ side, sourceSide: src, weight: 1, anchor: an, sourceSegment: [seg.start, seg.end] });
      }
    }
  }
  const hands = c.hands || {};
  return {
    engine: 'NexCMUSamplerV5', action: c.semantic, time: raw, duration: c.duration,
    pose3d: pose,
    hands: { left: { pose: hands.left || 'relaxed', orientation: 'edge-left' }, right: { pose: hands.right || 'relaxed', orientation: 'edge-right' } },
    motion: { source: 'cmu-mocap', license: 'CMU-free-all-uses', clip: ref, semantic: c.semantic },
    donorContacts: active, footPlant: plant, blocked: false,
  };
}
function catalog() { const V = vault(); return Object.keys(V.clips).map((k) => ({ ref: k, semantic: V.clips[k].semantic, duration: V.clips[k].duration, tags: V.clips[k].tags })); }
module.exports = { version: '5.0.0-cmu-corpus', sample, catalog, vault };
