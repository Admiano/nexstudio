/**
 * NexStudio Paper Cast — facial performance
 *
 * The paperbook face is quiet: two eyes and a mouth, no rendering of muscle.
 * Quiet is not the same as blank, though, and a blank face is what made every
 * spread of the Makoko book read the same however the story turned. So the
 * face is a small state — brow, eye aperture, gaze, mouth — that a beat sets
 * and the renderer draws in the book's own flat shapes.
 *
 *   Face.at({ emotion: 'concern', speaking: true, gaze: 'left' }, 2.4)
 *   Face.shapes(headPart, look, state)
 *
 * Everything is a pure function of (state, time): the same second of the same
 * beat always draws the same face, including the blink.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastFace = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const round = (n) => Math.round(Number(n) * 100) / 100;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const num = (v, fallback) => (Number.isFinite(Number(v)) ? Number(v) : fallback);

  /**
   * Emotions as the four dials the drawing actually has. `browTilt` is the
   * inner end of the brow: up is worry, down is anger — the single line that
   * separates a concerned face from a cross one.
   */
  const EMOTIONS = {
    neutral: { brow: 0, browTilt: 0, eyeOpen: 1, mouthCurve: 0.06, mouthOpen: 0, mouthWidth: 1 },
    attentive: { brow: 0.22, browTilt: 0, eyeOpen: 1.08, mouthCurve: 0.1, mouthOpen: 0, mouthWidth: 0.95 },
    warm: { brow: 0.12, browTilt: 0, eyeOpen: 0.9, mouthCurve: 0.5, mouthOpen: 0, mouthWidth: 1.08 },
    joy: { brow: 0.3, browTilt: 0, eyeOpen: 0.5, mouthCurve: 0.95, mouthOpen: 0.42, mouthWidth: 1.2 },
    concern: { brow: 0.34, browTilt: 0.6, eyeOpen: 0.94, mouthCurve: -0.35, mouthOpen: 0, mouthWidth: 0.9 },
    sad: { brow: 0.16, browTilt: 0.8, eyeOpen: 0.72, mouthCurve: -0.6, mouthOpen: 0, mouthWidth: 0.86 },
    surprise: { brow: 0.85, browTilt: -0.1, eyeOpen: 1.35, mouthCurve: 0.1, mouthOpen: 0.7, mouthWidth: 0.8 },
    stern: { brow: -0.45, browTilt: -0.55, eyeOpen: 0.86, mouthCurve: -0.2, mouthOpen: 0, mouthWidth: 0.92 },
    effort: { brow: -0.3, browTilt: -0.3, eyeOpen: 0.6, mouthCurve: -0.12, mouthOpen: 0.22, mouthWidth: 0.82 },
    thoughtful: { brow: 0.1, browTilt: 0.3, eyeOpen: 0.82, mouthCurve: -0.05, mouthOpen: 0, mouthWidth: 0.88 },
    tired: { brow: -0.1, browTilt: 0.45, eyeOpen: 0.45, mouthCurve: -0.18, mouthOpen: 0, mouthWidth: 0.9 }
  };

  /** Mouth shapes for speech. Not lip-sync — enough that a talker isn't still. */
  const VISEMES = {
    rest: { open: 0, width: 1 },
    ah: { open: 0.62, width: 1.02 },
    oh: { open: 0.5, width: 0.66 },
    ee: { open: 0.22, width: 1.24 },
    mm: { open: 0.04, width: 0.9 }
  };

  const GAZE = {
    ahead: { x: 0, y: 0 },
    left: { x: -0.8, y: 0 },
    right: { x: 0.8, y: 0 },
    up: { x: 0, y: -0.7 },
    down: { x: 0, y: 0.7 },
    away: { x: 0.55, y: -0.4 },
    partner: { x: 0.6, y: -0.05 }
  };

  /** Stable per-character phase, so a crowd does not blink in unison. */
  function seedOf(id) {
    const s = String(id == null ? '' : id);
    let h = 7;
    for (let i = 0; i < s.length; i += 1) h = (h * 31 + s.charCodeAt(i)) % 9973;
    return h / 9973;
  }

  const resolveGaze = (gaze) => {
    if (typeof gaze === 'string') return GAZE[gaze] || GAZE.ahead;
    if (gaze && typeof gaze === 'object') return { x: clamp(num(gaze.x, 0), -1, 1), y: clamp(num(gaze.y, 0), -1, 1) };
    return GAZE.ahead;
  };

  /**
   * @param {object} spec `{ emotion, intensity, speaking, listening, gaze, eyeOpen, brow, viseme, id }`
   * @returns {object} a resolved, inspectable face state
   */
  function state(spec) {
    const s = spec || {};
    const name = EMOTIONS[s.emotion] ? s.emotion : 'neutral';
    const base = EMOTIONS[name];
    const intensity = clamp(num(s.intensity, 1), 0, 1.5);
    const gaze = resolveGaze(s.gaze);
    const viseme = VISEMES[s.viseme] ? s.viseme : null;
    const speaking = !!s.speaking;
    const listening = !!s.listening && !speaking;
    const mouth = viseme ? VISEMES[viseme] : null;
    return {
      emotion: name,
      intensity,
      speaking,
      listening,
      viseme: viseme || (speaking ? 'rest' : null),
      // Listening lifts the brow a little and opens the eyes: attention is
      // mostly drawn above the eyes, not with the mouth.
      brow: clamp(num(s.brow, base.brow * intensity + (listening ? 0.16 : 0)), -1, 1),
      browTilt: clamp(num(s.browTilt, base.browTilt * intensity), -1, 1),
      eyeOpen: clamp(num(s.eyeOpen, base.eyeOpen * (1 - (1 - intensity) * 0.3) + (listening ? 0.06 : 0)), 0, 1.5),
      mouthCurve: clamp(num(s.mouthCurve, base.mouthCurve * intensity), -1, 1),
      mouthOpen: clamp(num(s.mouthOpen, mouth ? mouth.open : base.mouthOpen * intensity), 0, 1),
      mouthWidth: clamp(num(s.mouthWidth, (mouth ? mouth.width : 1) * base.mouthWidth), 0.4, 1.6),
      gaze,
      id: s.id == null ? null : String(s.id)
    };
  }

  const SPEECH = ['ah', 'ee', 'oh', 'mm', 'ah', 'oh', 'ee', 'rest'];

  /**
   * The same state, sampled at a time: adds the blink and, while speaking,
   * moves the mouth through a fixed viseme cycle.
   * @param {object} spec face spec
   * @param {number} time seconds
   */
  function at(spec, time) {
    const s = state(spec);
    const t = num(time, 0);
    const seed = seedOf(s.id != null ? s.id : s.emotion);
    const period = 3.1 + seed * 2.2;
    const phase = (t + seed * period) % period;
    // A blink is 140 ms of eyelid: closing, shut, opening.
    const blink = phase < 0.14 ? 1 - Math.abs(phase - 0.07) / 0.07 : 0;
    let mouthOpen = s.mouthOpen;
    let mouthWidth = s.mouthWidth;
    let viseme = s.viseme;
    if (s.speaking) {
      viseme = SPEECH[Math.floor(Math.abs(t) / 0.16 + seed * 8) % SPEECH.length];
      const shape = VISEMES[viseme];
      mouthOpen = clamp(Math.max(s.mouthOpen, shape.open * 0.9), 0, 1);
      mouthWidth = clamp(s.mouthWidth * shape.width, 0.4, 1.6);
    }
    return { ...s, viseme, mouthOpen, mouthWidth, blink: round(blink), eyeOpen: round(s.eyeOpen * (1 - blink)), time: t };
  }

  const mixHex = (hex, target, amount) => {
    const norm = (h) => {
      const v = String(h).replace('#', '');
      return v.length === 3 ? v.split('').map((c) => c + c).join('') : v;
    };
    const a = norm(hex);
    const b = norm(target);
    return `#${[0, 1, 2].map((i) => {
      const x = parseInt(a.slice(i * 2, i * 2 + 2), 16);
      const y = parseInt(b.slice(i * 2, i * 2 + 2), 16);
      return Math.round(x + (y - x) * amount).toString(16).padStart(2, '0');
    }).join('')}`;
  };

  /**
   * Draws a face state in the rig's pixel space.
   * @param {object} head the head part from `Rig.build`
   * @param {object} look resolved look (skin, hair colour)
   * @param {object} face a state from `state()` or `at()`
   * @returns {Array<{fill:string, svg:string}>}
   */
  function shapes(head, look, face) {
    // Accepts either a resolved state or the loose spec an author writes.
    const f = face && face.gaze && typeof face.gaze === 'object' && Number.isFinite(face.gaze.x) ? face : state(face);
    const r = head.radius;
    const c = head.center;
    // A head turned away has no face to draw; the profile keeps one eye.
    if (head.facing <= -0.3) return [];
    const lateral = head.lateral;
    const dir = lateral >= 0 ? 1 : -1;
    const open = Math.max(0.18, head.facing);
    const shift = lateral * r * 0.3;
    const skin = look && look.skin ? look.skin : '#c1895f';
    const ink = mixHex(skin, '#181009', 0.86);
    const soft = mixHex(skin, '#181009', 0.4);
    const pitch = (head.pitch || 0) / 90;
    const eyeY = c.y - r * 0.05 + pitch * r * 0.2;
    const out = [];

    const eyeX = (sign) => c.x + shift + sign * r * 0.3 * dir * open;
    const visible = [{ sign: 1, squash: 1 }];
    if (Math.abs(lateral) < 0.82) visible.push({ sign: -1, squash: Math.max(0.3, 1 - Math.abs(lateral)) });

    // Brows: two short strokes whose height and inner tilt carry most of the
    // expression. Drawn above the eye, never touching it.
    const browLift = r * (0.3 + f.brow * 0.16);
    for (const eye of visible) {
      const x = eyeX(eye.sign);
      const half = r * 0.15 * eye.squash;
      const inner = eye.sign * dir >= 0 ? -1 : 1;
      const tilt = f.browTilt * r * 0.11;
      const y = eyeY - browLift;
      out.push({
        fill: 'none',
        svg: `<path d="M ${round(x - half)} ${round(y + (inner < 0 ? tilt : -tilt) * 0.6)} Q ${round(x)} ${round(y - r * 0.05 - f.brow * r * 0.03)} ${round(x + half)} ${round(y + (inner < 0 ? -tilt : tilt) * 0.6)}" fill="none" stroke="${soft}" stroke-width="${round(r * 0.06)}" stroke-linecap="round"/>`
      });
    }

    // Eyes: aperture is the drawn height. Fully closed is a stroke, which is
    // what a blink has to look like in a book with no eyelids.
    for (const eye of visible) {
      const x = eyeX(eye.sign);
      const rx = r * 0.1 * eye.squash;
      const ry = r * 0.12 * clamp(f.eyeOpen, 0, 1.4);
      if (ry < r * 0.02) {
        out.push({ fill: 'none', svg: `<path d="M ${round(x - rx)} ${round(eyeY)} Q ${round(x)} ${round(eyeY + r * 0.03)} ${round(x + rx)} ${round(eyeY)}" fill="none" stroke="${ink}" stroke-width="${round(r * 0.05)}" stroke-linecap="round"/>` });
        continue;
      }
      // Gaze moves the eye within its socket rather than adding a pupil: at
      // this scale a pupil inside a 6-pixel eye is mud.
      const gx = x + f.gaze.x * rx * 0.7 * (dir >= 0 ? 1 : -1);
      const gy = eyeY + f.gaze.y * ry * 0.5;
      out.push({ fill: ink, svg: `<ellipse cx="${round(gx)}" cy="${round(gy)}" rx="${round(rx)}" ry="${round(ry)}" fill="${ink}"/>` });
    }

    // Mouth: a curve when closed, a filled shape when open. Width narrows an
    // "oh" and widens an "ee" without drawing teeth.
    const mouthY = c.y + r * (0.44 + pitch * 0.1);
    const half = r * 0.19 * open * f.mouthWidth;
    if (f.mouthOpen > 0.06) {
      const h = r * 0.1 + r * 0.2 * f.mouthOpen;
      out.push({
        fill: mixHex(skin, '#2a0f0c', 0.7),
        svg: `<path d="M ${round(c.x + shift - half)} ${round(mouthY)} Q ${round(c.x + shift)} ${round(mouthY - r * 0.06 * f.mouthCurve)} ${round(c.x + shift + half)} ${round(mouthY)} Q ${round(c.x + shift)} ${round(mouthY + h)} ${round(c.x + shift - half)} ${round(mouthY)} Z"/>`
      });
    } else {
      const bend = r * (0.14 * f.mouthCurve + 0.04);
      out.push({
        fill: 'none',
        svg: `<path d="M ${round(c.x + shift - half)} ${round(mouthY - bend * 0.35)} Q ${round(c.x + shift)} ${round(mouthY + bend)} ${round(c.x + shift + half)} ${round(mouthY - bend * 0.35)}" fill="none" stroke="${ink}" stroke-width="${round(r * 0.07)}" stroke-linecap="round"/>`
      });
    }

    if (f.emotion === 'joy' || f.emotion === 'warm') {
      const blush = mixHex(skin, '#c0553f', 0.32);
      for (const eye of visible) {
        out.push({ fill: blush, svg: `<ellipse cx="${round(eyeX(eye.sign))}" cy="${round(eyeY + r * 0.28)}" rx="${round(r * 0.14 * eye.squash)}" ry="${round(r * 0.07)}" fill="${blush}" opacity="0.5"/>` });
      }
    }
    return out;
  }

  return { state, at, shapes, EMOTIONS, VISEMES, GAZE, seedOf };
});
