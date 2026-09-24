/**
 * NexStudio Paper Cast — performance layer
 *
 * Turns a staged cast member plus a time in seconds into a pose and a stage
 * offset. Everything here is a pure function of (member, time): the same beat
 * seeked to the same second always draws the same frame, which is what the
 * paper-motion timeline contract requires.
 */
(function (root, factory) {
  const rig = typeof module === 'object' && module.exports ? require('./paper-cast-rig.js') : root.NexPaperCastRig;
  const api = factory(rig);
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastPerformance = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Rig) {
  const TAU = Math.PI * 2;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const easeOut = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);
  const LOCOMOTION = /walk|stride|passing|run/;

  /** Deterministic per-member phase so a line-up never breathes in lockstep. */
  function phase(member) {
    const id = String(member.id || '');
    let h = 0;
    for (let i = 0; i < id.length; i += 1) h = (h * 31 + id.charCodeAt(i)) % 997;
    return (h / 997) * TAU;
  }

  const mirror = (pose) => ({
    ...pose,
    armLeft: pose.armRight,
    armRight: pose.armLeft,
    legLeft: pose.legRight,
    legRight: pose.legLeft
  });

  function moving(member) {
    const addressing = member.view && member.view.addressing;
    return LOCOMOTION.test(String(member.pose || '')) || addressing === 'travel' || addressing === 'exit';
  }

  /**
   * @param {object} member  a staged member from the selector
   * @param {number} time    seconds into the beat
   * @param {object} [options] `{ duration, entry }`
   * @returns {{pose:object, offsetX:number, offsetY:number, opacity:number}}
   */
  function frame(member, time, options) {
    const opts = options || {};
    const duration = opts.duration || 5;
    const t = clamp(time, 0, duration);
    const rest = Rig.mergePose({});
    const target = Rig.mergePose(member.poseAngles || {});
    const ph = phase(member);
    const enter = easeOut(t / Math.max(0.35, duration * 0.18));
    const gait = moving(member);

    let pose = Rig.blend(rest, target, enter);

    if (gait) {
      // A stride is the pose and its mirror traded back and forth, so the
      // character walks rather than sliding as a static cut-out.
      const cycle = (t / 1.05 + ph / TAU) % 1;
      const swing = Math.sin(cycle * TAU) * 0.5 + 0.5;
      pose = Rig.blend(pose, mirror(target), swing * enter);
    }

    // Breath and weight shift keep a standing figure alive without reading as
    // a bobbing sprite.
    const breath = Math.sin(t * 1.6 + ph);
    const sway = Math.sin(t * 0.7 + ph * 1.3);
    pose = {
      ...pose,
      spine: { tilt: pose.spine.tilt + breath * 0.5, swing: pose.spine.swing + sway * 0.8 },
      chest: { tilt: pose.chest.tilt + breath * 0.7, swing: pose.chest.swing },
      neck: { tilt: pose.neck.tilt - breath * 0.4, swing: pose.neck.swing },
      head: { ...pose.head, pitch: pose.head.pitch + breath * 0.6 }
    };

    const direction = (member.view && member.view.addressing === 'exit') || (member.stage && member.stage.x > 0) ? 1 : -1;
    const travel = gait ? direction * (t / duration) * 0.42 : 0;
    const bob = gait ? Math.abs(Math.sin((t / 1.05 + ph / TAU) * TAU)) * 0.008 : 0;

    return {
      pose,
      offsetX: travel - direction * 0.06 * (1 - enter),
      offsetY: -bob,
      opacity: clamp(t / Math.max(0.2, duration * 0.08), 0, 1)
    };
  }

  return { frame, moving, phase };
});
