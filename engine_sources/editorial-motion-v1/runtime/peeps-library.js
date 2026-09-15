/**
 * NexStudio Editorial Motion — Open Peeps still cast
 *
 * Open Peeps parts (pose, body, head, face, facial hair, accessories) resolved
 * against a beat's emotion and posture, then composed into one flat SVG using
 * the slot geometry the library itself ships with. The figure is a still: it is
 * cut into the frame and held. Nothing here animates.
 */
(function (root, factory) {
  const node = typeof require === 'function' && typeof module === 'object';
  const api = factory(
    node ? require('../assets/peeps/parts-index.json') : root.NEX_PEEPS_PARTS,
    node ? require('../manifests/peeps-semantics.json') : root.NEX_PEEPS_SEMANTICS
  );
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexPeeps = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (INDEX, SEMANTICS) {
  const parts = (INDEX && INDEX.parts) || {};
  const compositions = (INDEX && INDEX.compositions) || {};
  const sem = SEMANTICS || {};
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const round = (v, p = 2) => Number(Number(v).toFixed(p));

  function hash(seed) {
    let h = 2166136261;
    for (const ch of String(seed)) {
      h ^= ch.charCodeAt(0);
      h = Math.imul(h, 16777619);
    }
    return ((h >>> 0) % 100000) / 100000;
  }

  const meta = (group, id) => ((sem[group] || {})[id] || (sem[group] || {}).defaults || {});
  const list = (group) => parts[group] || [];

  function overlap(a = [], b = []) {
    if (!a.length || !b.length) return 0;
    const set = new Set(b);
    let hits = 0;
    for (const tag of a) if (set.has(tag)) hits += 1;
    return hits / Math.sqrt(a.length * b.length);
  }

  /** Words a beat offers the library: keywords plus emotion tags. */
  function beatTags(context = {}) {
    const tags = [];
    for (const k of context.keywords || []) tags.push(typeof k === 'string' ? k : k.term);
    for (const t of (context.emotion && context.emotion.tags) || []) tags.push(t);
    if (context.role) tags.push(context.role);
    return tags.map((t) => String(t).toLowerCase());
  }

  function scoreFace(id, context) {
    const m = meta('face', id);
    const emotion = context.emotion || { valence: 0, arousal: 0.3 };
    const dv = Math.abs((m.valence ?? 0) - (emotion.valence ?? 0));
    const da = Math.abs((m.arousal ?? 0.3) - (emotion.arousal ?? 0.3));
    let score = 1 - (dv * 0.55 + da * 0.45);
    score += overlap(m.tags, beatTags(context)) * 0.8;
    if (m.rare) score -= 0.6;
    if ((m.requires || {}).mask && !context.mask) score -= 1.2;
    return score;
  }

  function scorePose(id, context) {
    const m = meta('pose', id);
    const posture = context.posture;
    let score = 0.5;
    if (posture && m.posture !== posture) score -= 0.8;
    const energy = context.energy ?? ((context.emotion && context.emotion.arousal) ?? 0.4);
    score -= Math.abs((m.energy ?? 0.4) - energy) * 0.7;
    if (context.formality != null) score -= Math.abs((m.formality ?? 0.5) - context.formality) * 0.4;
    score += overlap(m.tags, beatTags(context)) * 1.1;
    if (m.rare) score -= 0.6;
    return score;
  }

  function scoreBody(id, context) {
    const m = meta('body', id);
    let score = 0.5;
    if (context.formality != null) score -= Math.abs((m.formality ?? 0.5) - context.formality) * 0.5;
    score += overlap(m.tags, beatTags(context)) * 1.1;
    if (m.rare) score -= 0.6;
    return score;
  }

  function scoreTagged(group, id, context) {
    const m = meta(group, id);
    let score = overlap(m.tags, beatTags(context));
    if (m.rare) score -= 0.8;
    return score;
  }

  function pick(group, scorer, context, seed) {
    const items = list(group);
    if (!items.length) return null;
    const ranked = items
      .map((item) => ({ item, score: scorer(item.id, context) + hash(seed + ':' + item.id) * 0.06 }))
      .sort((a, b) => b.score - a.score);
    return ranked[0];
  }

  /** Heads that belong to a costume follow the body that wears it, never a tee. */
  function scoreHead(id, context) {
    const m = meta('head', id);
    let score = overlap(m.tags, beatTags(context)) * 1.4;
    if (m.pairs && m.pairs.length) {
      score += m.pairs.includes(context.bodyId) ? 1 : -1.4;
    }
    if (m.rare) score -= 0.8;
    return score;
  }

  /**
   * Resolve every part of one still figure. Pure: no SVG is read here, so the
   * choice can be inspected and tested without the artwork.
   */
  function resolve(context = {}) {
    const seed = String(context.seed ?? context.text ?? 'peep');
    const posture = context.posture || (context.compose === 'bust' ? null : 'standing');
    const framing = context.framing || (context.compose === 'bust' ? 'bust' : posture === 'sitting' ? 'sitting' : 'standing');
    const poseContext = { ...context, posture: framing === 'bust' ? null : posture };

    const bodyPart = framing === 'bust'
      ? pick('body', scoreBody, context, seed + ':body')
      : pick('pose', scorePose, poseContext, seed + ':pose');
    const face = pick('face', scoreFace, context, seed + ':face');
    const head = pick('head', scoreHead, { ...context, bodyId: bodyPart ? bodyPart.item.id : null }, seed + ':head');

    const accessory = pick('accessories', (id, ctx) => scoreTagged('accessories', id, ctx), context, seed + ':acc');
    const facialHair = pick('facial-hair', () => 0, context, seed + ':hair');
    const tones = (sem.skinTones || {}).palette || [];
    const skinTone = context.skinTone || tones[Math.floor(hash(seed + ':skin') * tones.length)] || null;

    const wearsAccessory = accessory && accessory.score > 0.35;
    const wearsFacialHair = hash(seed + ':beard') > 0.72;

    return {
      framing,
      composition: framing === 'bust' ? 'bust' : framing === 'sitting' ? 'sitting' : 'standing',
      parts: {
        [framing === 'bust' ? 'body' : 'body']: bodyPart ? bodyPart.item : null,
        head: head ? head.item : null,
        face: face ? face.item : null,
        accessories: wearsAccessory ? accessory.item : null,
        'facial-hair': wearsFacialHair && facialHair ? facialHair.item : null
      },
      emotion: face ? meta('face', face.item.id) : null,
      posture: bodyPart && framing !== 'bust' ? meta('pose', bodyPart.item.id).posture : 'bust',
      skinTone,
      scores: {
        face: face ? round(face.score, 3) : null,
        body: bodyPart ? round(bodyPart.score, 3) : null
      }
    };
  }

  function recolour(svg, skinTone) {
    const source = (sem.skinTones || {}).source;
    if (!skinTone || !source || skinTone.toLowerCase() === source.toLowerCase()) return svg;
    return svg.split(source).join(skinTone).split(source.toUpperCase()).join(skinTone);
  }

  function inner(svg) {
    const match = String(svg).match(/<svg[^>]*>([\s\S]*)<\/svg>/i);
    return match ? match[1] : '';
  }

  /**
   * Compose the resolved parts into one SVG string.
   * @param {object} selection result of resolve()
   * @param {(file:string)=>string} readPart returns the raw SVG for a part file
   */
  function compose(selection, readPart, options = {}) {
    const layout = compositions[selection.composition];
    if (!layout) throw new Error('Unknown peeps composition: ' + selection.composition);
    const order = ['body', 'head', 'facial-hair', 'mask', 'accessories', 'face'];
    const box = { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity };
    const layers = [];

    for (const slot of order) {
      const part = selection.parts[slot];
      const frame = layout.slots[slot];
      if (!part || !frame) continue;
      const svg = recolour(readPart(part.file), selection.skinTone);
      const scaleX = frame.width / part.width;
      const scaleY = frame.height / part.height;
      layers.push(
        `<g class="peep-${slot}" data-part="${part.id}" transform="translate(${round(frame.x)} ${round(frame.y)}) scale(${round(scaleX, 4)} ${round(scaleY, 4)})">${inner(svg)}</g>`
      );
      box.minX = Math.min(box.minX, frame.x);
      box.minY = Math.min(box.minY, frame.y);
      box.maxX = Math.max(box.maxX, frame.x + frame.width);
      box.maxY = Math.max(box.maxY, frame.y + frame.height);
    }

    const pad = Number(options.padding ?? 12);
    const x = round(box.minX - pad);
    const y = round(box.minY - pad);
    const width = round(box.maxX - box.minX + pad * 2);
    const height = round(box.maxY - box.minY + pad * 2);
    const viewBox = `${x} ${y} ${width} ${height}`;
    const label = options.label || `Still illustration of a person, ${selection.emotion ? selection.emotion.emotion : 'neutral'}`;

    return {
      viewBox,
      width,
      height,
      aspect: round(width / height, 4),
      svg: `<svg xmlns="http://www.w3.org/2000/svg" class="peep-figure" viewBox="${viewBox}" preserveAspectRatio="xMidYMax meet" role="img" aria-label="${label}">${layers.join('')}</svg>`
    };
  }

  function partFiles(selection) {
    return Object.values(selection.parts).filter(Boolean).map((p) => p.file);
  }

  return { resolve, compose, partFiles, parts, compositions, semantics: sem, meta, hash };
});
