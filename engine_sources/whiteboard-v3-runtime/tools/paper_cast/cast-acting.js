/**
 * NexStudio Paper Cast — acting layer
 *
 * `cast-performance.js` keeps a standing figure alive: breath, sway, a stride.
 * That is idling, not acting. A character who points at something does four
 * distinct things — draws back, strikes, holds, and settles — and a book that
 * only ever draws the hold ends up with the same raised arm on every spread.
 *
 * So a beat is written as acting:
 *
 *   const act = Acting.perform({
 *     id: 'adanna',
 *     beats: [{ at: 0.4, kind: 'point', target: { x: 0.3, y: 0.4, z: 0.4 }, say: 'over there' }]
 *   });
 *   act.at(1.2)   // -> { pose, face, phase: 'stroke', weight, offsetX }
 *
 * `at(t)` is a pure function of the spec and the time: the same second always
 * gives the same drawing, which is what a paperbook spread needs — a spread is
 * one frozen instant of a performance, and it has to freeze the same way every
 * time it renders.
 */
(function (root, factory) {
  const isNode = typeof module === 'object' && module.exports;
  const deps = isNode
    ? { Rig: require('./paper-cast-rig.js'), Contact: require('./cast-contact.js'), Face: require('./cast-face.js') }
    : { Rig: root.NexPaperCastRig, Contact: root.NexCastContact, Face: root.NexCastFace };
  const api = factory(deps);
  if (isNode) module.exports = api;
  root.NexCastActing = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function ({ Rig, Contact, Face }) {
  const TAU = Math.PI * 2;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const num = (v, fallback) => (Number.isFinite(Number(v)) ? Number(v) : fallback);
  const easeOut = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);
  const easeInOut = (t) => {
    const k = clamp(t, 0, 1);
    return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
  };

  /**
   * Where a gesture puts the hand, in body-local units. These are the handful
   * of shapes a storybook figure makes; anything else is a `reach` with the
   * point written out.
   */
  const GESTURES = {
    point: { at: { x: 0.2, y: 0.3, z: 0.38 }, hold: 0.9, emotion: 'attentive' },
    offer: { at: { x: 0.15, y: 0.12, z: 0.32 }, hold: 1.1, emotion: 'warm' },
    show: { at: { x: 0.17, y: 0.26, z: 0.3 }, hold: 1.0, emotion: 'attentive' },
    wave: { at: { x: 0.21, y: 0.48, z: 0.14 }, hold: 1.2, emotion: 'warm', sway: 0.5 },
    beckon: { at: { x: 0.18, y: 0.3, z: 0.24 }, hold: 0.8, emotion: 'warm', sway: 0.3 },
    explain: { at: { x: 0.16, y: 0.22, z: 0.28 }, hold: 0.7, emotion: 'attentive', sway: 0.18 },
    reach: { at: null, hold: 0.6, emotion: 'attentive' },
    lift: { at: { x: 0.14, y: 0.1, z: 0.26 }, hold: 0.9, emotion: 'effort' },
    place: { at: { x: 0.14, y: -0.02, z: 0.3 }, hold: 0.7, emotion: 'attentive' },
    // Head-only beats: no arm moves, so the acting reads in the neck.
    nod: { at: null, hold: 0.5, emotion: 'attentive', head: { pitch: 9, cycles: 2 } },
    shake: { at: null, hold: 0.5, emotion: 'concern', head: { yaw: 11, cycles: 2 } },
    look: { at: null, hold: 0.9, emotion: null }
  };

  /** Feeling changes timing before it changes shape: grief is slow, joy is quick. */
  const TEMPO = { joy: 0.82, surprise: 0.7, warm: 0.95, attentive: 1, neutral: 1, effort: 1.18, concern: 1.1, thoughtful: 1.2, sad: 1.38, tired: 1.45, stern: 1.05 };

  const PHASES = ['prepare', 'stroke', 'hold', 'release'];

  function resolveBeat(spec, index) {
    const s = spec || {};
    const kind = GESTURES[s.kind] ? s.kind : (s.target ? 'reach' : 'explain');
    const base = GESTURES[kind];
    const emotion = s.emotion || base.emotion || null;
    const tempo = num(s.tempo, TEMPO[emotion] || 1) / clamp(num(s.emphasis, 1), 0.4, 2);
    const durations = {
      prepare: num(s.prepare, 0.26) * tempo,
      stroke: num(s.stroke, 0.3) * tempo,
      hold: num(s.hold, base.hold) * tempo,
      release: num(s.release, 0.42) * tempo
    };
    const span = durations.prepare + durations.stroke + durations.hold + durations.release;
    return {
      index,
      kind,
      at: num(s.at, 0),
      end: num(s.at, 0) + span,
      span,
      durations,
      hand: s.hand === 'left' ? 'left' : 'right',
      target: s.target || base.at,
      head: s.head || base.head || null,
      sway: num(s.sway, base.sway || 0),
      emphasis: clamp(num(s.emphasis, 1), 0.4, 2),
      emotion,
      intensity: num(s.intensity, 1),
      gaze: s.gaze || null,
      say: s.say || null,
      listen: !!s.listen,
      weight: s.weight === 'left' ? -1 : s.weight === 'right' ? 1 : null
    };
  }

  /** Which phase of a beat a time falls in, and how far through it is. */
  function phaseAt(beat, time) {
    let start = beat.at;
    for (const phase of PHASES) {
      const length = beat.durations[phase];
      if (time < start + length) return { phase, t: length > 0 ? (time - start) / length : 1 };
      start += length;
    }
    return { phase: 'done', t: 1 };
  }

  const withArm = (pose, hand, arm) => (hand === 'left' ? { ...pose, armLeft: arm } : { ...pose, armRight: arm });

  /**
   * Builds the stroke pose for a beat once. Solving is the expensive part, so
   * a performance solves each beat a single time and interpolates from there;
   * sampling a hundred frames must not cost a hundred solves.
   */
  function poses(beat, proportion, basePose) {
    if (!beat.target) {
      return { stroke: basePose, anticipation: basePose };
    }
    const effector = `${beat.hand}Hand`;
    const solved = Contact.solve({ proportion, pose: basePose, goals: [{ effector, at: beat.target }], torso: true, tolerance: 0.02 });
    const arm = beat.hand === 'left' ? solved.pose.armLeft : solved.pose.armRight;
    const baseArm = beat.hand === 'left' ? basePose.armLeft : basePose.armRight;
    // Anticipation is the stroke run backwards a little: the arm drops away
    // from where it is about to go, and the torso counters it.
    const anticipation = withArm({
      ...basePose,
      spine: { tilt: basePose.spine.tilt - (solved.pose.spine.tilt - basePose.spine.tilt) * 0.35, swing: basePose.spine.swing }
    }, beat.hand, {
      shoulder: { tilt: baseArm.shoulder.tilt - (arm.shoulder.tilt - baseArm.shoulder.tilt) * 0.22, swing: baseArm.shoulder.swing },
      elbow: { tilt: baseArm.elbow.tilt + 6, swing: baseArm.elbow.swing }
    });
    return { stroke: Rig.mergePose(solved.pose), anticipation: Rig.mergePose(anticipation), residual: solved.residual };
  }

  /** Head-only beats move the neck rather than the arm. */
  function headMotion(beat, phase, t) {
    if (!beat.head) return null;
    const active = phase === 'stroke' || phase === 'hold';
    if (!active) return null;
    const cycles = beat.head.cycles || 2;
    const wave = Math.sin(clamp(t, 0, 1) * TAU * cycles);
    return { pitch: (beat.head.pitch || 0) * wave, yaw: (beat.head.yaw || 0) * wave };
  }

  /**
   * @param {object} spec `{ id, proportion, pose, beats, duration, emotion, personality }`
   * @returns {{ at:(t:number)=>object, beats:Array, duration:number, residual:number }}
   */
  function perform(spec) {
    const s = spec || {};
    const proportion = Rig.resolveProportion(s.proportion);
    const basePose = Rig.mergePose(s.pose);
    const beats = (s.beats || []).map(resolveBeat).sort((a, b) => a.at - b.at);
    const solvedBeats = beats.map((beat) => ({ beat, poses: poses(beat, proportion, basePose) }));
    const duration = num(s.duration, beats.reduce((m, b) => Math.max(m, b.end), 0) + 0.6);
    const seed = Face.seedOf(s.id || 'cast');
    // Personality is two numbers, not a library of styles: how much a body
    // moves at rest, and how far its gestures travel.
    const life = clamp(num(s.personality && s.personality.life, 1), 0, 2);
    const scale = clamp(num(s.personality && s.personality.scale, 1), 0.4, 1.6);
    const restEmotion = s.emotion || 'neutral';

    function at(time) {
      const t = clamp(num(time, 0), 0, duration);
      const ph = seed * TAU;
      const current = solvedBeats.find((entry) => t >= entry.beat.at && t < entry.beat.end) || null;
      const previous = solvedBeats.filter((entry) => entry.beat.end <= t).pop() || null;

      let pose = basePose;
      let phase = 'idle';
      let weight = Math.sin(t * 0.5 + ph) * 0.35 * life;
      let beatRef = null;

      if (current) {
        const { beat, poses: shapes } = current;
        const step = phaseAt(beat, t);
        phase = step.phase;
        beatRef = beat;
        const reach = (target, k) => Rig.blend(basePose, target, clamp(k, 0, 1) * scale);
        if (phase === 'prepare') {
          pose = reach(shapes.anticipation, easeInOut(step.t));
        } else if (phase === 'stroke') {
          pose = Rig.blend(shapes.anticipation, shapes.stroke, easeOut(step.t) * scale);
        } else if (phase === 'hold') {
          pose = reach(shapes.stroke, 1);
          if (beat.sway) {
            // A held gesture is not frozen: a wave waves.
            const swing = Math.sin(step.t * TAU * 2 + ph) * beat.sway * 9;
            const arm = beat.hand === 'left' ? pose.armLeft : pose.armRight;
            pose = withArm(pose, beat.hand, { shoulder: arm.shoulder, elbow: { tilt: arm.elbow.tilt + swing, swing: arm.elbow.swing } });
          }
        } else if (phase === 'release') {
          // Settle: the body comes back past rest and returns, damped. Without
          // it a gesture snaps off like a switch.
          const k = easeOut(step.t);
          const overshoot = Math.sin(step.t * TAU) * Math.exp(-step.t * 3.4) * 0.12;
          pose = Rig.blend(shapes.stroke, basePose, clamp(k - overshoot, 0, 1));
        }
        // Weight shifts onto the leg away from the working hand.
        const sign = beat.weight != null ? beat.weight : (beat.hand === 'right' ? -1 : 1);
        const engagement = phase === 'prepare' ? easeInOut(step.t) * 0.5 : phase === 'release' ? 1 - easeOut(step.t) : 1;
        weight = weight * 0.3 + sign * engagement * beat.emphasis;
      } else if (previous) {
        const since = t - previous.beat.end;
        // Residual settle after the last beat, so a figure does not arrive at
        // rest exactly as the gesture ends.
        const ring = Math.sin(since * 5.2) * Math.exp(-since * 2.6) * 0.05;
        pose = Rig.blend(basePose, previous.poses.stroke, Math.max(0, ring));
      }

      // Breath everywhere, quieter during a stroke: people hold breath to act.
      const amplitude = (phase === 'stroke' ? 0.5 : 1) * life;
      const breath = Math.sin(t * 1.6 + ph) * amplitude;
      const sway = Math.sin(t * 0.7 + ph * 1.3) * amplitude;
      const head = headMotion(beatRef || {}, phase, beatRef ? phaseAt(beatRef, t).t : 0);
      pose = {
        ...pose,
        spine: { tilt: pose.spine.tilt + breath * 0.5, swing: pose.spine.swing + sway * 0.8 + weight * 1.2 },
        chest: { tilt: pose.chest.tilt + breath * 0.7, swing: pose.chest.swing },
        neck: { tilt: pose.neck.tilt - breath * 0.4 + (head ? head.pitch * 0.4 : 0), swing: pose.neck.swing },
        head: { yaw: pose.head.yaw + (head ? head.yaw : 0), pitch: pose.head.pitch + breath * 0.6 + (head ? head.pitch : 0) },
        hipRoll: pose.hipRoll + weight * 2.4
      };

      const speaking = !!(beatRef && beatRef.say) && (phase === 'stroke' || phase === 'hold');
      const face = Face.at({
        id: s.id,
        emotion: (beatRef && beatRef.emotion) || restEmotion,
        intensity: beatRef ? clamp(beatRef.intensity * (phase === 'hold' ? 1 : 0.8), 0, 1.5) : 0.8,
        speaking,
        listening: !!(beatRef && beatRef.listen) || (!beatRef && !!s.listening),
        gaze: (beatRef && beatRef.gaze) || s.gaze || 'ahead'
      }, t);

      return {
        time: t,
        phase,
        beat: beatRef ? { index: beatRef.index, kind: beatRef.kind, hand: beatRef.hand, say: beatRef.say } : null,
        pose: Rig.mergePose(pose),
        face,
        weight: Math.round(weight * 1000) / 1000,
        offsetX: weight * 0.006,
        offsetY: 0
      };
    }

    return { at, beats, duration, residual: solvedBeats.reduce((m, e) => Math.max(m, e.poses.residual || 0), 0) };
  }

  /**
   * Turn-taking for a scene of dialogue. Each line gives its speaker a beat to
   * play and every other character something to do while it happens: look at
   * whoever is talking, and nod into the gaps. Listening is a performance too
   * — a room of characters staring ahead is the tell of a dead illustration.
   */
  function dialogue(spec) {
    const s = spec || {};
    const cast = (s.cast || []).map((member) => (typeof member === 'string' ? { id: member } : member));
    const lines = (s.lines || []).map((line, i) => ({
      speaker: String(line.speaker),
      at: num(line.at, i * 2.2),
      duration: num(line.duration, 1.8),
      text: line.text || null,
      emotion: line.emotion || null,
      kind: line.kind || 'explain',
      gaze: line.gaze || null
    }));
    const byId = new Map();
    for (const member of cast) {
      const beats = [];
      for (const line of lines) {
        if (line.speaker === member.id) {
          beats.push({
            at: line.at,
            kind: line.kind,
            emotion: line.emotion || 'attentive',
            hold: Math.max(0.3, line.duration - 0.6),
            say: line.text || true,
            gaze: line.gaze || 'partner',
            emphasis: 1
          });
        } else {
          // Listeners turn to the speaker as the line starts and nod towards
          // its end, which is what makes an exchange read as an exchange.
          beats.push({ at: line.at - 0.15, kind: 'look', gaze: 'partner', listen: true, hold: Math.max(0.2, line.duration * 0.55), emotion: line.emotion === 'concern' ? 'concern' : 'attentive' });
          beats.push({ at: line.at + line.duration * 0.62, kind: 'nod', listen: true, gaze: 'partner', hold: 0.2 });
        }
      }
      byId.set(member.id, perform({ ...member, beats, duration: s.duration }));
    }
    return {
      lines,
      duration: num(s.duration, lines.reduce((m, l) => Math.max(m, l.at + l.duration), 0) + 0.8),
      get: (id) => byId.get(String(id)) || null,
      at(time) {
        const out = {};
        for (const [id, performance] of byId) out[id] = performance.at(time);
        return out;
      },
      speakerAt(time) {
        const t = num(time, 0);
        const line = lines.find((l) => t >= l.at && t < l.at + l.duration);
        return line ? line.speaker : null;
      }
    };
  }

  return { perform, dialogue, resolveBeat, phaseAt, GESTURES, TEMPO, PHASES };
});
