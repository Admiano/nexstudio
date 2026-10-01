/**
 * NexStudio Editorial Motion — script reading
 *
 * Turns a raw script into beats with a measured editorial weight: what the beat
 * is doing (hook, problem, proof, call to action), how it feels, how strongly it
 * lands relative to the rest of the script, and whether it names a person, a
 * number or something that wants to be shown. Everything downstream — which
 * words animate, which icons appear, whether a character is earned — reads this
 * and nothing else, so no scene is ever decided in advance.
 */
(function (root, factory) {
  const api = factory(
    typeof require === 'function' && typeof module === 'object'
      ? require('../manifests/editorial-lexicon.json')
      : root.NEX_EDITORIAL_LEXICON
  );
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexEditorialScript = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (LEXICON) {
  const lex = LEXICON || {};
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const round = (v, p = 3) => Number(v.toFixed(p));

  function normalise(text) {
    return String(text || '').replace(/\s+/g, ' ').trim();
  }

  function sentences(text) {
    const lines = String(text || '')
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean);
    const out = [];
    for (const line of lines) {
      const parts = line.match(/[^.!?…]+[.!?…]*/g) || [line];
      for (const part of parts) {
        const value = normalise(part);
        if (value) out.push(value);
      }
    }
    return out;
  }

  function words(text) {
    return normalise(text)
      .toLowerCase()
      .replace(/[^a-z0-9'%$£€.\- ]/g, ' ')
      .split(' ')
      .filter(Boolean);
  }

  function keywords(text, limit = 8) {
    const stop = new Set(lex.stopWords || []);
    const counts = new Map();
    words(text).forEach((w, i) => {
      const term = w.replace(/^[^a-z0-9$£€%]+|[^a-z0-9%]+$/g, '');
      if (term.length < 3 || stop.has(term)) return;
      const weight = 1 + (i === 0 ? 0.3 : 0) + (/\d/.test(term) ? 0.5 : 0);
      counts.set(term, (counts.get(term) || 0) + weight);
    });
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, limit)
      .map(([term, score]) => ({ term, score: round(score) }));
  }

  /**
   * Single-word cues match word starts, so "break" reads "breaks" but never
   * "breakfast"; phrase cues match as written.
   */
  function cueHits(haystack, cues) {
    let hits = 0;
    for (const cue of cues || []) {
      const hit = cue.includes(' ')
        ? haystack.includes(cue)
        : new RegExp('\\b' + cue.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i').test(haystack);
      if (hit) hits += 1;
    }
    return hits;
  }

  function readRole(text, index, total) {
    const hay = ' ' + normalise(text).toLowerCase() + ' ';
    const scored = Object.entries(lex.beatRoles || {}).map(([id, def]) => {
      let score = cueHits(hay, def.cues) * 1.2;
      if (total > 1 && def.position === 'opening' && index === 0) score += 0.8;
      if (total > 1 && def.position === 'closing' && index === total - 1) score += 0.8;
      if (id === 'statement') score += 0.35;
      return { id, score: round(score), weight: def.weight };
    });
    scored.sort((a, b) => b.score - a.score || b.weight - a.weight);
    return scored[0];
  }

  function readEmotion(text) {
    const hay = ' ' + normalise(text).toLowerCase() + ' ';
    const hits = [];
    for (const [id, def] of Object.entries(lex.emotion || {})) {
      const n = cueHits(hay, def.cues);
      if (n) hits.push({ id, n, valence: def.valence, arousal: def.arousal });
    }
    if (!hits.length) {
      const neutral = (lex.emotion || {}).neutral || { valence: 0, arousal: 0.25 };
      return { id: 'neutral', valence: neutral.valence, arousal: neutral.arousal, confidence: 0, tags: [] };
    }
    hits.sort((a, b) => b.n - a.n);
    const total = hits.reduce((sum, h) => sum + h.n, 0);
    const valence = hits.reduce((sum, h) => sum + h.valence * h.n, 0) / total;
    const arousal = hits.reduce((sum, h) => sum + h.arousal * h.n, 0) / total;
    return {
      id: hits[0].id,
      valence: round(valence),
      arousal: round(arousal),
      confidence: round(clamp(total / 3)),
      tags: hits.map((h) => h.id)
    };
  }

  function entities(text) {
    const raw = normalise(text);
    const numbers = raw.match(/(?:[$£€]\s?)?\d[\d,.]*\s?(?:%|percent|x|k|m|bn|billion|million|hours?|days?|weeks?|minutes?)?/gi) || [];
    const quoted = raw.match(/[“"']([^“”"']{6,})[”"']/g) || [];
    const proper = (raw.match(/\b[A-Z][a-zA-Z]{2,}\b/g) || []).filter((w, i) => i > 0 || !raw.startsWith(w));
    const list = (lex.listCues || []).some((cue) => raw.toLowerCase().includes(cue));
    return {
      numbers: numbers.map((n) => n.trim()).filter((n) => /\d/.test(n)),
      quotes: quoted.map((q) => q.replace(/^[“"']|[”"']$/g, '')),
      names: [...new Set(proper)].slice(0, 4),
      list
    };
  }

  function cueScore(text, cues) {
    const hay = ' ' + normalise(text).toLowerCase() + ' ';
    return clamp(cueHits(hay, cues) / 2);
  }

  function rawEmphasis(text, role, emotion, ents, index, total) {
    const marks = lex.emphasisMarkers || {};
    const raw = normalise(text);
    const wordCount = words(raw).length;
    let score = (role.weight || 0.5) * 0.55 + emotion.arousal * 0.25 + Math.abs(emotion.valence) * 0.15;
    if (/^[A-Z][a-z]*\s|^[A-Za-z]+\b/.test(raw) && /^(try|start|join|stop|look|see|think|imagine|remember|build|ship|ask|choose)\b/i.test(raw)) {
      score += marks.imperative || 0;
    }
    if (raw.endsWith('!')) score += marks.exclamation || 0;
    if (raw.endsWith('?')) score += marks.question || 0;
    if (ents.numbers.length) score += marks.number || 0;
    if (ents.quotes.length) score += marks.quote || 0;
    if ((lex.superlatives || []).some((s) => raw.toLowerCase().includes(s))) score += marks.superlative || 0;
    if (wordCount && wordCount <= 7) score += marks.shortSentence || 0;
    if (index === 0) score += marks.openingBeat || 0;
    if (index === total - 1) score += marks.closingBeat || 0;
    return round(score);
  }

  /**
   * Beats are grouped by reading load, not sentence count: a long sentence is a
   * beat on its own, so no card ends up holding twice the words of its
   * neighbours.
   */
  function groupBeats(list, targetBeats) {
    if (!targetBeats || targetBeats >= list.length) return list.map((s) => [s]);
    const counts = list.map((s) => words(s).length);
    const totalWords = counts.reduce((a, b) => a + b, 0);
    const groups = [];
    let current = [];
    let load = 0;
    counts.forEach((count, i) => {
      const remainingGroups = targetBeats - groups.length;
      const remainingWords = counts.slice(i).reduce((a, b) => a + b, 0);
      const quota = remainingGroups > 0 ? remainingWords / remainingGroups : totalWords;
      current.push(list[i]);
      load += count;
      const sentencesLeft = counts.length - i - 1;
      if ((load >= quota && groups.length < targetBeats - 1) || sentencesLeft === targetBeats - groups.length - 1) {
        groups.push(current);
        current = [];
        load = 0;
      }
    });
    if (current.length) groups.push(current);
    return groups.filter((g) => g.length);
  }

  /**
   * Time is reading time: each beat gets the seconds its words need at the
   * lexicon's reading rate, nudged by emphasis, held inside the pacing floor
   * and ceiling, then normalised onto the requested runtime.
   */
  function paceBeats(beats, duration) {
    const pacing = lex.pacing || {};
    const rate = pacing.wordsPerSecond || 2.6;
    const min = pacing.minShot || 2;
    const max = pacing.maxShot || 7;
    let want = beats.map((b) => clampRange(((b.wordCount || 4) / rate) * (0.85 + b.emphasis * 0.4), min, max));
    for (let pass = 0; pass < 4; pass += 1) {
      const sum = want.reduce((a, b) => a + b, 0);
      if (!sum) break;
      const scale = duration / sum;
      if (Math.abs(scale - 1) < 0.01) break;
      want = want.map((v) => clampRange(v * scale, min, max));
    }
    // With too few sentences to hold the runtime inside the pacing window, the
    // runtime wins: the film always tiles end to end.
    const sum = want.reduce((a, b) => a + b, 0);
    return sum ? want.map((v) => (v * duration) / sum) : want;
  }

  function clampRange(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  /** How many cards a runtime wants at the lexicon's pacing. */
  function beatTarget(duration) {
    const pacing = lex.pacing || {};
    const min = pacing.minShot || 2;
    const max = pacing.maxShot || 7;
    const preferred = Math.round(duration / ((min + max) / 2));
    return Math.max(2, Math.ceil(duration / max), Math.min(preferred, Math.floor(duration / min)));
  }

  /**
   * @param {string} script
   * @param {{beats?:number, duration?:number}} [options]
   */
  function read(script, options = {}) {
    const all = sentences(script);
    if (!all.length) return { beats: [], keywords: [], duration: 0, emphasisRange: [0, 0] };
    const target = options.beats || (options.duration ? beatTarget(options.duration) : 0);
    const groups = groupBeats(all, target);
    const total = groups.length;

    const beats = groups.map((group, index) => {
      const text = group.join(' ');
      const role = readRole(text, index, total);
      const emotion = readEmotion(text);
      const ents = entities(text);
      return {
        index,
        text,
        sentences: group,
        wordCount: words(text).length,
        role: role.id,
        roleScore: role.score,
        emotion,
        entities: ents,
        keywords: keywords(text),
        person: round(Math.max(
          cueScore(text, (lex.personCues || {}).explicit),
          cueScore(text, (lex.personCues || {}).human) * 0.8
        )),
        showCue: round(cueScore(text, (lex.mediaCues || {}).show)),
        rawEmphasis: rawEmphasis(text, role, emotion, ents, index, total)
      };
    });

    const values = beats.map((b) => b.rawEmphasis);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const sorted = [...values].sort((a, b) => a - b);
    beats.forEach((beat) => {
      beat.emphasis = round((beat.rawEmphasis - min) / span);
      beat.emphasisRank = round(sorted.indexOf(beat.rawEmphasis) / Math.max(1, sorted.length - 1));
    });

    const duration = Number(options.duration) || beats.length * 5;
    const paced = paceBeats(beats, duration);
    let cursor = 0;
    beats.forEach((beat, i) => {
      beat.start = round(cursor, 2);
      // The last card absorbs the rounding so the film tiles the runtime exactly.
      beat.duration = i === beats.length - 1 ? round(duration - beat.start, 2) : round(paced[i], 2);
      cursor = round(cursor + beat.duration, 2);
    });

    return {
      beats,
      duration: round(cursor, 2),
      keywords: keywords(script, 14),
      emphasisRange: [round(min), round(max)]
    };
  }

  /**
   * The disposition a beat asks a still figure for: a measured emotion where the
   * script states one, and the editorial role's own disposition where it does
   * not. Confidence decides the blend, so a flat sentence in a call to action
   * still reads as a call to action.
   */
  function brief(beat) {
    const role = (lex.beatRoles || {})[beat.role] || {};
    const disposition = role.disposition || { valence: 0, arousal: 0.35, formality: 0.5 };
    const measured = beat.emotion || { valence: 0, arousal: 0.3, confidence: 0, tags: [] };
    const w = clamp(measured.confidence ?? 0);
    const valence = measured.valence * w + disposition.valence * (1 - w);
    const arousal = measured.arousal * w + disposition.arousal * (1 - w);
    return {
      emotion: {
        id: w >= 0.34 ? measured.id : beat.role,
        valence: round(valence),
        arousal: round(arousal),
        confidence: round(w),
        tags: [...(measured.tags || []), beat.role]
      },
      energy: round(clamp(arousal * 0.7 + (beat.emphasis ?? 0.5) * 0.3)),
      formality: round(clamp(disposition.formality ?? 0.5)),
      keywords: beat.keywords || [],
      role: beat.role,
      text: beat.text
    };
  }

  return { read, brief, sentences, words, keywords, readRole, readEmotion, entities, LEXICON: lex };
});
