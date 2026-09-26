/**
 * NexStudio Paper Cast — parametric body
 *
 * A body is described by continuous parameters (age in years, build, stature)
 * rather than chosen from a fixed list of archetype proportions. The named
 * proportions the archetypes ship with survive as presets over the same
 * parameters, so an unlisted character — an infant on a back, a toddler
 * mid-step — is still drawable instead of being absent from a catalogue.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastBody = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  /**
   * Age keyframes. Lengths are fractions of the figure's own height, so a
   * toddler is not a small adult: its head takes a quarter of its height and
   * its legs less than a third, which is the whole reason a scaled-down adult
   * never reads as a child.
   *
   * `stature` is height relative to an average adult and is what places the
   * character on the stage at the right size.
   */
  const AGE_KEYS = [
    {
      age: 0,
      stature: 0.28,
      p: { head: 0.114, neck: 0.012, chest: 0.152, pelvisWidth: 0.072, shoulderWidth: 0.076, thigh: 0.156, shin: 0.146, foot: 0.038, upperArm: 0.112, foreArm: 0.102, hand: 0.034, limb: 0.035, torsoTaper: 1, bodyDepth: 0.74 }
    },
    {
      age: 2,
      stature: 0.42,
      p: { head: 0.099, neck: 0.019, chest: 0.168, pelvisWidth: 0.067, shoulderWidth: 0.081, thigh: 0.184, shin: 0.176, foot: 0.042, upperArm: 0.126, foreArm: 0.114, hand: 0.036, limb: 0.032, torsoTaper: 0.96, bodyDepth: 0.7 }
    },
    {
      age: 7,
      stature: 0.65,
      p: { head: 0.093, neck: 0.024, chest: 0.175, pelvisWidth: 0.062, shoulderWidth: 0.082, thigh: 0.198, shin: 0.198, foot: 0.046, upperArm: 0.135, foreArm: 0.122, hand: 0.038, limb: 0.03, torsoTaper: 0.9, bodyDepth: 0.64 }
    },
    {
      age: 14,
      stature: 0.92,
      p: { head: 0.072, neck: 0.028, chest: 0.19, pelvisWidth: 0.068, shoulderWidth: 0.094, thigh: 0.228, shin: 0.228, foot: 0.05, upperArm: 0.155, foreArm: 0.142, hand: 0.04, limb: 0.028, torsoTaper: 0.82, bodyDepth: 0.58 }
    },
    {
      age: 30,
      stature: 1,
      p: { head: 0.066, neck: 0.03, chest: 0.2, pelvisWidth: 0.076, shoulderWidth: 0.107, thigh: 0.235, shin: 0.235, foot: 0.055, upperArm: 0.163, foreArm: 0.15, hand: 0.042, limb: 0.032, torsoTaper: 0.86, bodyDepth: 0.62 }
    },
    {
      age: 70,
      stature: 0.96,
      p: { head: 0.066, neck: 0.028, chest: 0.193, pelvisWidth: 0.08, shoulderWidth: 0.1, thigh: 0.226, shin: 0.226, foot: 0.055, upperArm: 0.158, foreArm: 0.146, hand: 0.042, limb: 0.031, torsoTaper: 0.88, bodyDepth: 0.66 }
    }
  ];

  /** Build shifts frame width, never age. Soft mass is a separate axis. */
  const BUILDS = {
    slight: { widths: 0.9, limb: 0.86, depth: 0.94, taper: 0.93, stature: 1.01 },
    average: { widths: 1, limb: 1, depth: 1, taper: 1, stature: 1 },
    broad: { widths: 1.16, limb: 1.22, depth: 1.1, taper: 1.09, stature: 0.99 },
    tall: { widths: 0.97, limb: 0.92, depth: 0.97, taper: 0.96, stature: 1.06 }
  };

  const AGE_BANDS = { infant: 0.6, toddler: 2, child: 7, teen: 14, adult: 30, senior: 70 };

  /** The archetype proportion names, re-expressed as points in the parameter space. */
  const PRESETS = {
    'adult-average': { age: 30, build: 'average' },
    'adult-broad': { age: 34, build: 'broad' },
    'adult-slight': { age: 27, build: 'slight' },
    'adult-tall': { age: 30, build: 'tall' },
    'adult-heavy': { age: 40, build: 'average', mass: 0.8 },
    teen: { age: 14, build: 'slight' },
    child: { age: 7, build: 'average' },
    senior: { age: 70, build: 'average' },
    toddler: { age: 2, build: 'average' },
    infant: { age: 0.4, build: 'average' }
  };

  const WIDTH_KEYS = ['pelvisWidth', 'shoulderWidth'];

  function interpolate(age) {
    const a = clamp(Number(age), 0, AGE_KEYS[AGE_KEYS.length - 1].age);
    let lo = AGE_KEYS[0];
    let hi = AGE_KEYS[AGE_KEYS.length - 1];
    for (let i = 0; i < AGE_KEYS.length - 1; i += 1) {
      if (a >= AGE_KEYS[i].age && a <= AGE_KEYS[i + 1].age) {
        lo = AGE_KEYS[i];
        hi = AGE_KEYS[i + 1];
        break;
      }
    }
    const span = hi.age - lo.age;
    const t = span ? (a - lo.age) / span : 0;
    const out = {};
    for (const key of Object.keys(lo.p)) out[key] = lo.p[key] + (hi.p[key] - lo.p[key]) * t;
    return { proportion: out, stature: lo.stature + (hi.stature - lo.stature) * t };
  }

  /**
   * @param {object|string} spec `{ age, build, mass, stature }`, an age band, or a preset name
   * @returns {object} rig proportions plus `stature` (height relative to an adult)
   */
  function body(spec) {
    const s = typeof spec === 'string' ? (PRESETS[spec] || { ageBand: spec }) : (spec || {});
    const age = typeof s.age === 'number' ? s.age : AGE_BANDS[s.ageBand] ?? 30;
    const build = BUILDS[s.build] || BUILDS.average;
    const { proportion, stature } = interpolate(age);
    const out = { ...proportion };
    for (const key of WIDTH_KEYS) out[key] *= build.widths;
    out.limb *= build.limb;
    out.bodyDepth = clamp(out.bodyDepth * build.depth, 0.3, 0.95);
    out.torsoTaper = clamp(out.torsoTaper * build.taper, 0.6, 1.2);

    // Mass is its own axis because a heavy body is not a broad one: a broad
    // frame is shoulders and limbs, weight is carried at the waist. Widening
    // `build` alone gives a thicker athlete and never a heavy person, so mass
    // drives the waist and the body's depth and leaves the frame alone.
    const mass = clamp(typeof s.mass === 'number' ? s.mass : 0, 0, 1);
    out.waist = 1 + mass * 0.6;
    out.bodyDepth = clamp(out.bodyDepth * (1 + mass * 0.42), 0.3, 1.1);
    out.pelvisWidth *= 1 + mass * 0.22;
    out.limb *= 1 + mass * 0.3;
    out.torsoTaper = clamp(out.torsoTaper * (1 + mass * 0.16), 0.6, 1.3);
    out.mass = mass;
    out.age = age;
    out.build = s.build && BUILDS[s.build] ? s.build : 'average';
    out.stature = clamp((typeof s.stature === 'number' ? s.stature : stature) * build.stature, 0.15, 1.35);
    return out;
  }

  /** Stage height in pixels for a body, given the height an adult would render at. */
  const heightFor = (spec, adultHeight) => body(spec).stature * Number(adultHeight || 1000);

  const ageBandOf = (age) => {
    const a = Number(age);
    if (a < 1) return 'infant';
    if (a < 4) return 'toddler';
    if (a < 12) return 'child';
    if (a < 19) return 'teen';
    if (a < 60) return 'adult';
    return 'senior';
  };

  return { body, heightFor, ageBandOf, PRESETS, BUILDS, AGE_BANDS, AGE_KEYS };
});
