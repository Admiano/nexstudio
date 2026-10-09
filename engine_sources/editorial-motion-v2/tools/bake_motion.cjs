#!/usr/bin/env node
/**
 * Bake mocap clips into a seekable paper-figure sprite JSON.
 *
 * Real NexStick V5 mocap (UAL2/rokoko/CMU vaults, 22-joint skeleton) drives the
 * paper-cast rig through the whiteboard-v3 bridge; this wrapper calls it as a
 * subprocess and normalizes every emitted frame onto ONE union viewBox, so a
 * travelling clip (a walk-in) literally crosses its own frame while an in-place
 * clip (idle, wave, sit) holds a stable silhouette. A `chain` (walk in, then
 * idle) concatenates segments into one frame list with `loop_from` marking the
 * last segment's first frame, so the tail loops while the intro plays once.
 * The result is a single JSON the editorial runtime fetches and swaps
 * frame-by-frame — vector paper all the way down, no live mocap at render time.
 *
 * usage: node bake_motion.cjs '<req json>' <out.json>
 *   req: { chain: [{clip|action, seconds}..], loop?, fps?, look?, proportion?,
 *          emotion?, t? }   — or flat {clip|action, seconds, ...}
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const MOCAP_RIG = path.resolve(__dirname, '../../whiteboard-v3-runtime/tools/nexstick/mocap_rig.cjs');

const VBX = /viewBox="(-?[0-9.e]+) (-?[0-9.e]+) ([0-9.e]+) ([0-9.e]+)"/;

function bakeSegment(req, fps, tmpRoot) {
  const tmp = fs.mkdtempSync(path.join(tmpRoot, 'seg_'));
  const arg = JSON.stringify({
    cmuClip: req.clip || undefined,
    action: req.action || undefined,
    say: req.say || undefined,
    text: req.text || undefined,
    speedMps: req.speedMps || req.speed_mps || 1.1,
    look: req.look || undefined,
    emotion: req.emotion || 'warm',
    personality: req.personality || undefined,
    beats: req.beats || undefined,
    acting: req.acting || undefined,
    visemes: req.visemes || undefined,
    other: req.other || undefined,
    t: req.t || 0,
  });
  const nF = Math.max(2, Math.round(req.seconds * fps));
  execFileSync(process.execPath, [MOCAP_RIG, arg, tmp, String(nF), String(fps), req.proportion || 'adult-average'],
    { stdio: ['ignore', 'pipe', 'pipe'] });
  const files = fs.readdirSync(tmp).filter((f) => /^g\d+\.svg$/.test(f)).sort();
  const meta = JSON.parse(fs.readFileSync(path.join(tmp, 'poses.json'), 'utf8'));
  return files.map((f, i) => ({ svg: fs.readFileSync(path.join(tmp, f), 'utf8'), root: meta[i] && meta[i].root }));
}

function main() {
  const req = JSON.parse(process.argv[2] || '{}');
  const out = process.argv[3];
  if (!out) throw new Error('usage: bake_motion.cjs <req json> <out.json>');
  const fps = Math.max(1, Math.min(60, req.fps || 24));
  const chain = (req.chain || [req]).map((s) => ({
    ...s, seconds: Math.max(0.5, Math.min(30, s.seconds || 3)), speedMps: s.speed_mps || s.speedMps || req.speed_mps || 1.1,
    look: s.look || req.look, emotion: s.emotion || req.emotion || 'warm', proportion: s.proportion || req.proportion || 'adult-average',
  }));

  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'mocap_bake_'));
  const segs = [];
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const segReq of chain) {
    let frames;
    try {
      frames = bakeSegment(segReq, fps, tmpRoot);
    } catch (e) {
      throw new Error(`mocap bake failed for ${segReq.clip || segReq.action}: ${String(e.stderr || e.message).slice(0, 300)}`);
    }
    if (!frames.length) throw new Error(`mocap bake emitted no frames for ${segReq.clip || segReq.action}`);
    for (const fr of frames) {
      const m = fr.svg.match(VBX);
      if (!m) throw new Error('frame has no viewBox');
      fr.vb = [+m[1], +m[2], +m[3], +m[4]];
      x0 = Math.min(x0, +m[1]); y0 = Math.min(y0, +m[2]);
      x1 = Math.max(x1, +m[1] + +m[3]); y1 = Math.max(y1, +m[2] + +m[4]);
    }
    segs.push(frames);
  }
  // Camera-follow framing: a fixed-size window that tracks the silhouette's centre
  // horizontally and holds the union height, so a travelling clip (a walk) keeps the
  // figure large and centred instead of shrinking into a union of its whole travel.
  const hFixed = (y1 - y0) * 1.1;
  const widths = segs.flat().map((fr) => fr.vb[2]).sort((a, b) => a - b);
  const wFixed = Math.max(widths[Math.floor(widths.length / 2)] * 1.22, hFixed * 0.5);
  const viewBox = [0, y0 - hFixed * 0.05, wFixed, hFixed].map((v) => +v.toFixed(2));

  const frames = [], roots = [], frameVb = [];
  let loopFrom = 0;
  segs.forEach((seg, i) => {
    if (i === segs.length - 1) loopFrom = frames.length;
    seg.forEach((fr) => {
      const cx = fr.vb[0] + fr.vb[2] / 2;
      const vb = [cx - wFixed / 2, viewBox[1], wFixed, hFixed].map((v) => +v.toFixed(2));
      frameVb.push(vb);
      frames.push(fr.svg.replace(VBX, `viewBox="${vb.join(' ')}"`));
      roots.push(fr.root || null);
    });
  });
  const loop = req.loop !== false ? loopFrom : frames.length - 1;

  fs.writeFileSync(out, JSON.stringify({
    schema: 'NexStudioFigureSpriteV1',
    fps, viewBox, frames, roots, frame_vb: frameVb,
    duration_ms: Math.round(frames.length / fps * 1000),
    loop_from: loop,
  }));
  console.log(`bake_motion: ${frames.length} frames @ ${fps}fps (${segs.length} seg${segs.length > 1 ? 's' : ''}, loop@${loop}) -> ${out}`);
}
main();
