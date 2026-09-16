/**
 * NexStudio Editorial Motion — the director
 *
 * Reads a script into beats and decides, per beat and per ratio, what the frame
 * is allowed to contain: one typographic component that carries the line, icons
 * only where a word actually names one, uploaded media only where it belongs,
 * and a still Open Peeps figure only where the beat has earned human emphasis.
 * Anything that does not earn its place is left out, so nothing strays.
 */
(function (root, factory) {
  const node = typeof require === 'function' && typeof module === 'object';
  const api = factory(
    node ? require('./script-context.js') : root.NexEditorialScript,
    node ? require('./layout-engine.js') : root.NexEditorialLayout,
    node ? require('./peeps-library.js') : root.NexPeeps,
    node ? require('../manifests/editorial-rules.json') : root.NEX_EDITORIAL_RULES
  );
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexEditorialDirector = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Script, Layout, Peeps, RULES) {
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const round = (v, p = 3) => Number(Number(v).toFixed(p));
  const lower = (v) => String(v || '').toLowerCase();

  function overlap(a = [], b = []) {
    if (!a.length || !b.length) return 0;
    const set = new Set(b.map(lower));
    let hits = 0;
    for (const item of a) if (set.has(lower(item))) hits += 1;
    return hits / Math.sqrt(a.length * b.length);
  }

  /** Whole-word cue matching, so "call" never fires on "calligraphy". */
  function termHits(terms, text) {
    const said = new Set(lower(text).split(/[^a-z0-9]+/).filter(Boolean));
    let score = 0;
    for (const term of terms) if (said.has(lower(term))) score += 1;
    return score;
  }

  /** Conditions a beat presents to the typography layer. */
  function conditions(beat) {
    const rules = RULES.typography;
    const text = lower(beat.text);
    const out = [];
    if (text.trim().endsWith('?')) out.push('question');
    if (beat.entities.quotes.length) out.push('quote');
    if (beat.entities.numbers.length) out.push('statistic');
    if (beat.entities.list || beat.sentences.length > 2) out.push('list');
    if (beat.wordCount <= 2) out.push('singleWord');
    else if (beat.wordCount <= rules.shortPhraseWords) out.push('shortPhrase');
    if (beat.wordCount >= rules.longBodyWords) out.push('longBody');
    if (beat.entities.names.length && beat.entities.quotes.length) out.push('attribution');
    if (termHits(rules.cautionCues, ' ' + text + ' ')) out.push('caution');
    return out;
  }

  function scoreTypography(def, beat, conds, ratio, recent) {
    const rules = RULES.typography;
    const w = rules.conditionWeights;
    const roleIntents = rules.roleIntents[beat.role] || [];
    const condIntents = conds.flatMap((c) => rules.conditionIntents[c] || []);
    let score = overlap(def.intents, roleIntents) * w.role + overlap(def.intents, condIntents) * w.condition;
    score += overlap(def.keywords, (beat.keywords || []).map((k) => k.term)) * w.keyword;
    if ((def.aspectRatios || []).includes(ratio)) score += w.ratio;
    if (recent.includes(def.slug)) score -= rules.repeatPenalty;
    return score;
  }

  /**
   * A component is only eligible when the beat actually carries what it is
   * built to show: a list needs list items, a quote card needs a quote. Without
   * this the component would pad itself by repeating the sentence.
   */
  function canFill(def, beat) {
    const need = (RULES.typography.contentRequirements || {})[def.slug];
    if (!need) return true;
    const have = {
      sentences: beat.sentences.length,
      quotes: beat.entities.quotes.length,
      numbers: beat.entities.numbers.length,
      names: beat.entities.names.length
    };
    return Object.entries(need).every(([key, min]) => (have[key] || 0) >= min);
  }

  function pickTypography(registry, beat, conds, ratio, recent) {
    const eligible = registry.filter((def) => canFill(def, beat));
    const ranked = (eligible.length ? eligible : registry)
      .map((def) => ({ def, score: scoreTypography(def, beat, conds, ratio, recent) }))
      .sort((a, b) => b.score - a.score || a.def.order - b.def.order);
    return ranked[0];
  }

  /** Content for the chosen typographic component, taken from the beat itself. */
  function typographyContent(def, beat) {
    // What the card shows is the beat's readable excerpt, not necessarily every
    // word it was analysed from.
    const sentences = (beat.displaySentences || beat.sentences).slice();
    const shown = beat.display || beat.text;
    const head = sentences[0] || shown;
    const rest = sentences.slice(1).join(' ');
    const keywords = (beat.keywords || []).map((k) => k.term);
    const content = {
      title: head,
      body: rest,
      meta: '',
      // Every string shown on screen is the script's own: no kickers, labels or
      // stingers are invented to fill a component slot.
      kicker: '',
      emphasisWords: keywords.slice(0, 3).join(','),
      items: []
    };
    switch (def.slug) {
      case 'statistic-headline':
        // The figure is the one the shown sentence actually states, so a card
        // can never headline a number the reader cannot see underneath it.
        content.title = (beat.entities.numbers.find((n) => shown.includes(n)) || beat.entities.numbers[0] || head);
        // The sentence stays whole under the figure: cutting the number out of
        // it leaves a hole in the copy ("cut reporting time by  in the month").
        content.body = shown;
        break;
      case 'quote-card':
        content.title = beat.entities.quotes[0] || head;
        content.meta = beat.entities.names[0] || '';
        break;
      case 'numbered-list':
      case 'bullet-list':
        content.title = beat.role === 'step' ? head : '';
        content.items = (sentences.length > 1 ? sentences.slice(beat.role === 'step' ? 1 : 0) : [shown]).slice(0, 4);
        if (!content.items.length) content.items = [shown];
        break;
      case 'kinetic-keyword':
        content.title = keywords[0] ? keywords[0].toUpperCase() : head;
        content.body = rest || '';
        break;
      case 'call-to-action-card':
        content.title = head;
        content.meta = keywords[0] ? keywords[0].toUpperCase() : '';
        break;
      case 'name-role-card':
      case 'speaker-identification':
        content.title = beat.entities.names[0] || head;
        content.body = rest || shown;
        break;
      default:
        break;
    }
    if (!content.body && sentences.length === 1 && def.slug !== 'kinetic-keyword') content.body = '';
    return content;
  }

  const GENERIC_KEYWORDS = new Set(['icon', 'universal', 'paper', 'typography', 'animated', 'responsive', 'media', 'container']);

  /** Words the script actually says, as whole words — never substrings. */
  function spoken(beat) {
    return new Set(lower(beat.text).split(/[^a-z0-9]+/).filter(Boolean));
  }

  const ambiguityCache = new WeakMap();

  /**
   * How many icons in the registry claim each keyword. A word several icons
   * claim ('start', 'open') names no particular drawing, so it earns none.
   */
  function ambiguity(registry) {
    if (ambiguityCache.has(registry)) return ambiguityCache.get(registry);
    const counts = new Map();
    for (const def of registry) {
      for (const keyword of new Set((def.keywords || []).map(lower))) {
        counts.set(keyword, (counts.get(keyword) || 0) + 1);
      }
    }
    ambiguityCache.set(registry, counts);
    return counts;
  }

  /**
   * An icon appears only when the script names the thing it draws. Matching is
   * on whole words against the beat's own vocabulary, so no icon arrives on the
   * strength of a coincidental substring.
   */
  function pickIcons(registry, beat, budget, recent) {
    if (budget <= 0) return [];
    const rules = RULES.icons;
    const terms = new Set((beat.keywords || []).map((k) => k.term));
    const said = spoken(beat);
    const shared = ambiguity(registry);
    const ranked = registry
      .map((def) => {
        const denied = new Set(((rules.keywordDenylist || {})[def.slug] || []).map(lower));
        const own = (def.keywords || []).filter((k) =>
          !GENERIC_KEYWORDS.has(lower(k)) && !denied.has(lower(k)) && lower(k).length > 2);
        const matched = own.filter((k) => said.has(lower(k)) &&
          (lower(k) === lower(def.slug) || (shared.get(lower(k)) || 0) < 2));
        if (!matched.length) return { def, score: 0, matched };
        const topical = matched.filter((k) => terms.has(lower(k))).length;
        let score = rules.keywordWeight * (topical ? 0.5 : 0.28) + (topical ? rules.intentWeight * 0.25 : 0);
        score += Math.min(2, matched.length - 1) * 0.12 + beat.emphasis * rules.emphasisBias;
        if (recent.includes(def.slug)) return { def, score: 0, matched: [] };
        return { def, score: round(score), matched, topical };
      })
      .filter((x) => x.score >= rules.minScore)
      .sort((a, b) => b.score - a.score);

    // One icon may ride on a plain word; every further icon has to name a term
    // the beat is actually about, and no two icons may share a matched word.
    const kept = [];
    const claimed = new Set();
    for (const candidate of ranked) {
      if (kept.length >= budget) break;
      if (kept.length && !candidate.topical) continue;
      if (candidate.matched.some((k) => claimed.has(lower(k)))) continue;
      candidate.matched.forEach((k) => claimed.add(lower(k)));
      kept.push(candidate);
    }
    return kept;
  }

  function mediaTokens(item) {
    const raw = [item.name, item.src, item.caption, ...(item.tags || [])].filter(Boolean).join(' ');
    return lower(raw).split(/[^a-z0-9]+/).filter((t) => t.length > 2);
  }

  function pickMedia(beat, library, used) {
    const rules = RULES.media;
    if (!library.length) return null;
    const terms = (beat.keywords || []).map((k) => k.term);
    const ranked = library
      .map((item, index) => {
        const tokens = mediaTokens(item);
        const named = overlap(tokens, terms);
        let score = named * rules.keywordWeight + beat.showCue * rules.showCueWeight;
        // "Show me" is not enough on its own: an upload has to be about the
        // beat, or a volcano line borrows whatever file happens to be loaded.
        if (rules.requireKeywordMatch && !named) score = 0;
        if ((used[index] || 0) >= rules.maxReuse) score -= 2;
        return { item, index, tokens, score: round(score) };
      })
      .sort((a, b) => b.score - a.score);
    const best = ranked[0];
    if (!best || best.score < rules.minScore) return null;
    const hinted = Object.entries(rules.hintContainers).find(([hint]) =>
      best.tokens.includes(hint) || lower(beat.text).includes(hint));
    const type = lower(best.item.type || 'image');
    const container = hinted ? hinted[1] : (rules.defaultContainer[type] || rules.defaultContainer.image);
    return { ...best, container, type };
  }

  /**
   * A still figure is a punctuation mark, not a presenter: it appears only on
   * the strongest beats that actually speak about people, never twice in a row,
   * and never in a frame that is already carrying media.
   */
  function characterGate(beat, ratio, previousShot, shotsWithCharacter, totalShots) {
    const rules = RULES.character;
    const score = beat.emphasis + beat.person * rules.personWeight + Math.abs(beat.emotion.valence) * rules.emotionWeight;
    if (beat.person < rules.personFloor) return { allowed: false, reason: 'no-person-in-beat', score: round(score) };
    if (score < rules.emphasisGate) return { allowed: false, reason: 'below-emphasis-gate', score: round(score) };
    if (previousShot && previousShot.character) return { allowed: false, reason: 'spacing', score: round(score) };
    if ((shotsWithCharacter + 1) / totalShots > rules.maxShare) return { allowed: false, reason: 'share-cap', score: round(score) };
    return { allowed: true, score: round(score) };
  }

  /**
   * Figures are full body: standing, or seated where the beat is set at a desk.
   * Busts are never staged — a cropped head reads as a stock portrait, not as
   * an editorial emphasis.
   */
  function framingFor(beat, ratio) {
    const rules = RULES.character;
    const hay = ' ' + lower(beat.text) + ' ';
    if (termHits(rules.sittingCues, hay)) return 'sitting';
    const weights = rules.framingByRatio[ratio] || { standing: 1 };
    const ranked = Object.entries(weights)
      .filter(([id]) => !rules.fullBodyOnly || id !== 'bust')
      .sort((a, b) => b[1] - a[1]);
    return (ranked[0] || ['standing'])[0];
  }

  /**
   * @param {string} script
   * @param {object} options ratio, duration, registries {typography, icons, media}, media library, seed
   * @returns {{ratio, duration, shots}}
   */
  function direct(script, options = {}) {
    const ratio = options.ratio || '16:9';
    if (!Layout.RATIOS.includes(ratio)) throw new Error('Unsupported ratio: ' + ratio);
    const registries = options.registries || {};
    const typographyRegistry = registries.typography || [];
    const iconRegistry = registries.icons || [];
    const mediaRegistry = registries.media || [];
    const library = options.media || [];
    const seed = options.seed || 'editorial';

    const doc = Script.read(script, { duration: options.duration, beats: options.beats });
    const iconBudget = (RULES.icons.maxPerShot || {})[ratio] ?? 2;
    const usedMedia = {};
    const recentTypography = [];
    const recentIcons = [];
    const shots = [];
    let withCharacter = 0;

    doc.beats.forEach((beat) => {
      const conds = conditions(beat);
      const typography = pickTypography(typographyRegistry, beat, conds, ratio, recentTypography.slice(-2));
      const media = pickMedia(beat, library, usedMedia);
      if (media) usedMedia[media.index] = (usedMedia[media.index] || 0) + 1;

      const gate = characterGate(beat, ratio, shots[shots.length - 1], withCharacter, doc.beats.length);
      const wantsCharacter = gate.allowed && !(media && !RULES.character.allowWithMedia);
      let character = null;
      if (wantsCharacter) {
        const brief = Script.brief(beat);
        const framing = framingFor(beat, ratio);
        const selection = Peeps.resolve({ ...brief, framing, seed: `${seed}:${ratio}:${beat.index}` });
        character = { ...selection, gate };
        withCharacter += 1;
      }

      let budget = iconBudget;
      if (media) budget -= RULES.icons.suppressWithMedia;
      if (character) budget -= RULES.icons.suppressWithCharacter;
      const icons = pickIcons(iconRegistry, beat, Math.max(0, budget), recentIcons.slice(-RULES.icons.cooldownShots));

      const kinds = ['text'];
      if (icons.length) kinds.push('icons');
      if (media) kinds.push('media');
      if (character) kinds.push('character');
      const layout = Layout.solve(ratio, kinds);
      const keptIcons = layout.byId.icons ? icons : [];
      const keptMedia = layout.byId.media ? media : null;
      const keptCharacter = layout.byId.character ? character : null;
      if (character && !keptCharacter) withCharacter -= 1;

      recentTypography.push(typography.def.slug);
      keptIcons.forEach((i) => recentIcons.push(i.def.slug));

      const mediaDef = keptMedia
        ? mediaRegistry.find((d) => d.slug === keptMedia.container) || mediaRegistry[0] || null
        : null;

      shots.push({
        index: beat.index,
        start: beat.start,
        duration: beat.duration,
        role: beat.role,
        emphasis: beat.emphasis,
        text: beat.display || beat.text,
        sourceText: beat.text,
        conditions: conds,
        typography: {
          id: typography.def.id,
          slug: typography.def.slug,
          score: round(typography.score),
          content: typographyContent(typography.def, beat)
        },
        icons: keptIcons.map((i) => ({ id: i.def.id, slug: i.def.slug, score: i.score, matched: i.matched })),
        media: keptMedia && mediaDef
          ? { id: mediaDef.id, slug: mediaDef.slug, source: keptMedia.item, score: keptMedia.score, type: keptMedia.type }
          : null,
        character: keptCharacter,
        layout
      });
    });

    return {
      ratio,
      duration: doc.duration,
      keywords: doc.keywords,
      shots,
      stats: {
        beats: shots.length,
        withCharacter: shots.filter((s) => s.character).length,
        withMedia: shots.filter((s) => s.media).length,
        withIcons: shots.filter((s) => s.icons.length).length
      }
    };
  }

  return { direct, conditions, characterGate, pickIcons, pickMedia, pickTypography, typographyContent, RULES };
});
