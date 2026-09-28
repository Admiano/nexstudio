"""Story director: which element on a printed page acts, how, and on which spoken word.

A paperbook page is a still print. The narration decides the one thing that moves:
the sentence's verb picks the motion ("kicked" -> kick arc, "blinked" -> shine,
"went dark" -> dim, "grew" -> grow), the noun it governs picks the element, and
the aligned voice timestamp of that verb (or noun) is the moment it starts. Counted
sets pop in reading order on their spoken numbers. Everything is a pure function of
the plan inputs — the same beat always directs the same way.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .illustration import _action_for, _is_focus

NUMBER_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
    'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
}

IRREGULAR = {
    'grew': 'grow', 'grown': 'grow', 'fell': 'fall', 'fallen': 'fall', 'rose': 'rise', 'risen': 'rise',
    'flew': 'fly', 'flown': 'fly', 'spun': 'spin', 'shone': 'shine', 'blew': 'blow', 'broke': 'break',
    'ran': 'run', 'swam': 'swim', 'sank': 'sink', 'threw': 'throw', 'thrown': 'throw', 'came': 'come',
    'went': 'go', 'gone': 'go', 'hid': 'hide', 'shook': 'shake', 'lit': 'light', 'dove': 'dive',
    'leapt': 'leap', 'sprang': 'spring', 'drove': 'drive', 'rode': 'ride', 'woke': 'wake',
    'caught': 'catch', 'struck': 'strike', 'slid': 'slide', 'swung': 'swing', 'flung': 'fling',
    'burst': 'burst', 'bloomed': 'bloom', 'took': 'take', 'taken': 'take', 'blown': 'blow', 'sprung': 'spring',
    'hidden': 'hide', 'ate': 'eat', 'eaten': 'eat', 'left': 'leave', 'sat': 'sit', 'stood': 'stand', 'bit': 'bite', 'began': 'begin', 'split': 'split', 'shot': 'shoot',
}

# verb lemma -> motion primitive. None marks a verb the director knows but never animates.
VERB_KIND: Dict[str, Optional[str]] = {
    'grow': 'grow', 'sprout': 'grow', 'bloom': 'grow', 'blossom': 'grow', 'spring': 'grow', 'swell': 'grow',
    'kick': 'kick', 'throw': 'kick', 'toss': 'kick', 'shoot': 'kick', 'strike': 'kick', 'pass': 'kick',
    'hit': 'kick', 'punt': 'kick', 'fling': 'kick', 'launch': 'rise', 'serve': 'kick', 'bat': 'kick',
    'bounce': 'bounce', 'hop': 'hop', 'jump': 'hop', 'leap': 'hop', 'skip': 'hop',
    'roll': 'roll', 'drive': 'travel', 'travel': 'travel', 'sail': 'travel', 'move': 'travel',
    'race': 'travel', 'run': 'travel', 'cross': 'travel', 'drift': 'travel', 'ride': 'travel',
    'zoom': 'travel', 'slide': 'travel', 'walk': 'travel', 'march': 'travel', 'crawl': 'travel', 'chug': 'travel',
    'fall': 'fall', 'drop': 'fall', 'tumble': 'fall', 'sink': 'fall', 'dive': 'fall', 'pour': 'fall',
    'drip': 'fall', 'rain': 'fall', 'plop': 'fall', 'splash': 'fall',
    'rise': 'rise', 'lift': 'rise', 'climb': 'rise', 'float': 'rise', 'soar': 'rise', 'ascend': 'rise',
    'fly': 'fly', 'glide': 'fly', 'swoop': 'fly',
    'flap': 'flutter', 'flutter': 'flutter', 'buzz': 'flutter',
    'spin': 'spin', 'turn': 'spin', 'whirl': 'spin', 'twirl': 'spin', 'rotate': 'spin', 'swirl': 'spin',
    'shake': 'shake', 'wobble': 'shake', 'tremble': 'shake', 'rattle': 'shake', 'shiver': 'shake',
    'rumble': 'shake', 'erupt': 'shake', 'ring': 'shake', 'quake': 'shake', 'wiggle': 'shake',
    'shine': 'shine', 'glow': 'shine', 'blink': 'shine', 'twinkle': 'shine', 'sparkle': 'shine',
    'flash': 'shine', 'light': 'shine', 'flicker': 'shine', 'beam': 'shine', 'gleam': 'shine', 'glitter': 'shine',
    'darken': 'dim', 'dim': 'dim', 'fade': 'dim', 'wane': 'dim',
    'appear': 'pop', 'arrive': 'pop', 'pop': 'pop', 'hatch': 'pop', 'emerge': 'pop', 'land': 'pop', 'burst': 'pop',
    'vanish': 'vanish', 'disappear': 'vanish', 'melt': 'vanish', 'leave': 'vanish', 'hide': 'vanish', 'escape': 'vanish',
    'open': 'unfold', 'unfold': 'unfold', 'unfurl': 'unfold', 'spread': 'unfold', 'stretch': 'unfold',
    'wave': 'wave', 'billow': 'wave', 'sway': 'wave', 'ripple': 'wave', 'flutters': 'wave',
    'swim': 'swim', 'bob': 'swim', 'paddle': 'swim',
    'orbit': 'orbit', 'circle': 'orbit', 'loop': 'orbit',
    'beat': 'pulse', 'pulse': 'pulse', 'thump': 'pulse', 'throb': 'pulse',
    'count': None, 'is': None, 'be': None, 'have': None, 'see': None, 'look': None, 'say': None,
}

# (lemma, particle) -> primitive: "went dark", "turned on", "lit up", "blew out".
PHRASAL = {
    ('go', 'dark'): 'dim', ('turn', 'dark'): 'dim', ('grow', 'dark'): 'dim', ('get', 'dark'): 'dim',
    ('go', 'out'): 'dim', ('blow', 'out'): 'dim', ('turn', 'off'): 'dim', ('go', 'dim'): 'dim',
    ('turn', 'on'): 'shine', ('light', 'up'): 'shine', ('switch', 'on'): 'shine', ('wake', 'up'): 'shine',
    ('go', 'bright'): 'shine', ('turn', 'bright'): 'shine', ('grow', 'bright'): 'shine',
    ('fly', 'away'): 'fly', ('fall', 'down'): 'fall', ('grow', 'up'): 'grow', ('come', 'out'): 'pop',
    ('pop', 'up'): 'pop', ('come', 'in'): 'pop', ('take', 'off'): 'rise', ('lift', 'off'): 'rise',
    ('blast', 'off'): 'rise', ('go', 'up'): 'rise', ('go', 'down'): 'fall', ('run', 'away'): 'vanish',
    ('go', 'away'): 'vanish', ('swim', 'away'): 'vanish', ('fly', 'off'): 'fly', ('roll', 'away'): 'roll',
}

DURATION = {
    'grow': 1500, 'kick': 950, 'bounce': 1100, 'hop': 700, 'roll': 1400, 'travel': 1800, 'fall': 1300,
    'rise': 2000, 'fly': 1900, 'spin': 1200, 'shake': 700, 'shine': 900, 'dim': 1100, 'phase': 1700,
    'pop': 380, 'vanish': 800, 'unfold': 900, 'wave': 1800, 'swim': 2000, 'flutter': 1600, 'orbit': 2400,
    'pulse': 1400,
}
# Primitives that carry the element sideways across the plate.
TRAVELLING = {'kick', 'roll', 'travel', 'fly', 'bounce'}
POP_MS = 380
SUBJECT_REACH = 4  # tokens a verb may look back for its subject / ahead for its object


def _clean(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', text.lower())


def tokens(words: Optional[Sequence[Dict[str, Any]]], narration: Optional[str]) -> List[Dict[str, Any]]:
    """Beat-local timed tokens; when no alignment exists the text still parses, untimed."""
    out: List[Dict[str, Any]] = []
    if words:
        for w in words:
            for piece in re.split(r"[\s\-]+", str(w.get('text') or '')):
                t = _clean(piece)
                if t:
                    out.append({'t': t, 'at': int(w.get('start_ms') or 0), 'end': int(w.get('end_ms') or 0), 'raw': piece.strip()})
    else:
        for piece in re.split(r"[\s\-]+", narration or ''):
            t = _clean(piece)
            if t:
                out.append({'t': t, 'at': None, 'end': None, 'raw': piece.strip()})
    return out


def lemmas(w: str) -> List[str]:
    if w in IRREGULAR:
        return [IRREGULAR[w]]
    c = [w]
    if w.endswith('ied'):
        c.append(w[:-3] + 'y')
    if w.endswith('ies'):
        c.append(w[:-3] + 'y')
    if w.endswith('ing'):
        s = w[:-3]
        c += [s, s + 'e'] + ([s[:-1]] if len(s) > 2 and s[-1] == s[-2] else [])
    if w.endswith('ed'):
        s = w[:-2]
        c += [s, w[:-1]] + ([s[:-1]] if len(s) > 2 and s[-1] == s[-2] else [])
    if w.endswith('es'):
        c.append(w[:-2])
    if w.endswith('s') and not w.endswith('ss'):
        c.append(w[:-1])
    return c


def verb_kind(toks: List[Dict[str, Any]], i: int) -> Tuple[Optional[str], Optional[str], int]:
    """(primitive, lemma, span) of a verb at token i — phrasal pairs win over the bare verb."""
    ls = lemmas(toks[i]['t'])
    if i + 1 < len(toks):
        nxt = toks[i + 1]['t']
        for l in ls:
            if (l, nxt) in PHRASAL:
                return PHRASAL[(l, nxt)], f'{l} {nxt}', 2
    for l in ls:
        if l in VERB_KIND:
            return VERB_KIND[l], l, 1
    return None, None, 1


def _number(t: str) -> Optional[int]:
    if t.isdigit():
        return int(t)
    return NUMBER_WORDS.get(t)


def _norm_concept(e: Dict[str, Any]) -> str:
    return str(e.get('concept') or '').lower().replace('_', '-')


def _refine(kind: str, concept: str, e: Dict[str, Any], zone: Dict[str, float]) -> Dict[str, Any]:
    """Primitive -> parameterised action for this element on this plate."""
    act: Dict[str, Any] = {'kind': kind}
    if kind == 'dim' and 'moon' in concept:
        act['kind'] = 'phase'
    if act['kind'] == 'grow' and 'root' in concept:
        act['anchor'] = 'top'
    if act['kind'] in TRAVELLING:
        bb = e.get('bbox') or e.get('art_bbox') or {}
        bx, bw = float(bb.get('x') or 0), float(bb.get('w') or 1)
        zx, zw = float(zone.get('x') or 0), float(zone.get('w') or 1)
        right = zx + zw - (bx + bw)
        left = bx - zx
        d = 1 if right >= left else -1
        space = max(right, left)
        act['dir'] = d
        # The travel stays inside the printed plate: never past its visible edge.
        act['dx'] = round(max(bw * 0.35, min(bw * 1.9, space)) * d, 1)
    act['dur'] = DURATION.get(act['kind'], 900)
    return act


def _reading_order(es: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key(e: Dict[str, Any]) -> Tuple[int, float]:
        b = e.get('bbox') or e.get('art_bbox') or {}
        h = float(b.get('h') or 1)
        return (int(float(b.get('y') or 0) // max(1.0, h * 0.8)), float(b.get('x') or 0))
    return sorted(es, key=key)


def direct(ents: List[Dict[str, Any]], zone: Dict[str, float], window_ms: Optional[int],
           words: Optional[Sequence[Dict[str, Any]]], narration: Optional[str],
           beat_id: str = 'beat', count_truth: bool = True) -> Dict[str, Any]:
    """Assign story actions on a printed page and return the direction record.

    Rules, in order: counted sets (>=3 of a kind) pop in reading order on their spoken
    numbers; each verb acts on the element it governs (subject before it, else the object
    after it) from the verb's spoken onset; an element named without a verb takes its
    concept's natural behaviour from the moment it is named; a line that names nothing on
    the plate lets the primary subject act. Garnish (`support_*`) never acts. Entities
    whose action was fixed upstream (`via == 'edu'`) keep it."""
    failures: List[str] = []
    events: List[Dict[str, Any]] = []
    fixed = [e for e in ents if e.get('action') and (e.get('params') or {}).get('resolution', {}).get('via') == 'edu']
    subjects = [e for e in ents if not str(e.get('id') or '').startswith('support_') and e not in fixed]
    for e in ents:
        if e not in fixed:
            e.pop('action', None)
    toks = tokens(words, narration)
    counts = Counter(_norm_concept(e) for e in subjects)
    moons = sum(1 for e in subjects if 'moon' in _norm_concept(e))
    latest = int(window_ms) - 200 if window_ms is not None else None

    def ready_of(e: Dict[str, Any]) -> int:
        return int(e.get('enter_ms') or 0) + int(e.get('enter_duration_ms') or 0)

    def place(e: Dict[str, Any], act: Dict[str, Any], at: Optional[int], tok: Optional[Dict[str, Any]], reason: str, verb: Optional[str]) -> bool:
        ready = ready_of(e)
        if act['kind'] == 'phase' and moons > 1:
            return False  # a phases row teaches the sequence — its cells stay fixed
        start = max(ready, at if at is not None else ready + 150)
        clamped = False
        if latest is not None:
            if ready > latest:
                return False
            if start > latest:
                start, clamped = latest, True
            act['dur'] = min(int(act.get('dur') or 600), max(200, int(window_ms) - start))
        act['at'] = int(start)
        if tok is not None:
            act['word'] = tok['raw']
            if tok['at'] is not None:
                act['word_ms'] = int(tok['at'])
        e['action'] = act
        events.append({'id': e['id'], 'concept': _norm_concept(e), 'kind': act['kind'], 'at': act['at'], 'dur': act['dur'],
                       'word': act.get('word'), 'word_ms': act.get('word_ms'), 'verb': verb, 'reason': reason,
                       'clamped': clamped or (act.get('word_ms') is not None and act['at'] > act['word_ms'])})
        return True

    # Mentions: token index -> entities it names.
    mentions: Dict[int, List[Dict[str, Any]]] = {}
    for i, tk in enumerate(toks):
        if len(tk['t']) < 3 or _number(tk['t']) is not None:
            continue
        hit = [e for e in subjects if _is_focus(_norm_concept(e), {tk['t']})]
        if hit:
            mentions[i] = hit

    # 1) Counted sets.
    counted = {c for c, n in counts.items() if n >= 3 and c}
    for c in sorted(counted):
        group = _reading_order([e for e in subjects if _norm_concept(e) == c])
        nums = [(i, _number(tk['t'])) for i, tk in enumerate(toks) if _number(tk['t']) is not None]
        seq = [toks[i] for i, _ in nums]
        ascending = len(nums) >= 2 and all(nums[k + 1][1] == nums[k][1] + 1 for k in range(len(nums) - 1))
        ready = max(ready_of(e) for e in group)
        if ascending:
            times = [tk['at'] for tk in seq]
        else:
            anchor_tok = seq[0] if seq else next((toks[i] for i in sorted(mentions) if any(e in group for e in mentions[i])), None)
            anchor = anchor_tok['at'] if anchor_tok and anchor_tok['at'] is not None else ready
            anchor = max(anchor, ready)
            space = 240
            if window_ms is not None:
                space = max(110, min(300, int((window_ms - POP_MS - anchor) / max(1, len(group) - 1))))
            times = [anchor + k * space for k in range(len(group))]
        prev: Optional[int] = None
        for k, e in enumerate(group):
            t = times[k] if k < len(times) and times[k] is not None else (times[-1] + 240 * (k - len(times) + 1) if times and times[-1] is not None else None)
            tok = seq[k] if ascending and k < len(seq) else (seq[0] if seq and k == 0 else None)
            if t is not None:
                t = max(t, ready)
                if prev is not None:
                    t = max(t, prev + 110)  # one object per beat of the count, never two at once
                prev = t
            place(e, {'kind': 'pop', 'dur': POP_MS, 'index': k + 1, 'of': len(group)}, t, tok, 'count', None)

    # Count truth: "three stars" must show three stars; "five more" matches the counted set.
    for i, tk in enumerate(toks if count_truth else []):
        n = _number(tk['t'])
        if n is None or n < 2:
            continue
        if i + 1 < len(toks) and _number(toks[i + 1]['t']) is not None:
            continue  # inside a counting run ("one, two, three stars") only the last number names the set
        nxt = [toks[j]['t'] for j in range(i + 1, min(len(toks), i + 3))]
        target = None
        for w in nxt:
            named = [c for c in counts if c and _is_focus(c, {w})]
            if named:
                target = named[0]
                break
        if target is None and nxt and nxt[0] == 'more' and len(counted) == 1:
            target = next(iter(counted))
        if target is not None:
            shown = counts[target]
            if shown != n and not (shown <= 1 and target.endswith('s')):
                failures.append(f'COUNT_MISMATCH:{beat_id}:{target}:said {n}, shows {shown}')

    # 2) Verbs act on the element they govern.
    acted = {e['id'] for e in ents if e.get('action')}
    i = 0
    first_free_verb: Optional[Tuple[str, str, Dict[str, Any]]] = None
    while i < len(toks):
        kind, lemma, span = verb_kind(toks, i)
        if kind is None:
            i += span
            continue
        target = None
        for j in range(i - 1, max(-1, i - 1 - SUBJECT_REACH), -1):
            cand = [e for e in mentions.get(j, []) if e['id'] not in acted and _norm_concept(e) not in counted]
            if cand:
                target = cand
                break
        if target is None:
            for j in range(i + span, min(len(toks), i + span + SUBJECT_REACH)):
                cand = [e for e in mentions.get(j, []) if e['id'] not in acted and _norm_concept(e) not in counted]
                if cand:
                    target = cand
                    break
        if target is None:
            if first_free_verb is None:
                first_free_verb = (kind, lemma, toks[i])
        else:
            e = max(target, key=lambda x: float((x.get('bbox') or {}).get('w') or 0) * float((x.get('bbox') or {}).get('h') or 0))
            if place(e, _refine(kind, _norm_concept(e), e, zone), toks[i]['at'], toks[i], 'verb', lemma):
                acted.add(e['id'])
        i += span

    # 3) Named without a verb: the concept's own behaviour, from the naming word — only
    # when no verb already gave the line its focus (a tree the bird flies from stays still).
    verb_acted = bool(acted - {e['id'] for e in fixed})
    for j in ([] if verb_acted else sorted(mentions)):
        for e in mentions[j]:
            if e['id'] in acted or _norm_concept(e) in counted:
                continue
            base = _action_for(_norm_concept(e), ready_of(e), zone, e.get('bbox') or {})
            if not base:
                continue
            act = _refine(base['kind'], _norm_concept(e), e, zone)
            if base.get('anchor'):
                act['anchor'] = base['anchor']
            if place(e, act, toks[j]['at'], toks[j], 'mention', None):
                acted.add(e['id'])

    # 4) The line names nothing on the plate but has an action verb: the primary subject
    # performs it. A line with neither leaves the page a still print, reported unresolved.
    if not acted and subjects and first_free_verb is not None:
        heroes = [e for e in subjects if e.get('size') == 'hero'] or subjects
        e = max(heroes, key=lambda x: float((x.get('bbox') or {}).get('w') or 0) * float((x.get('bbox') or {}).get('h') or 0))
        c = _norm_concept(e)
        kind, lemma, tok = first_free_verb
        place(e, _refine(kind, c, e, zone), tok['at'], tok, 'verb-primary', lemma)
    unresolved = not acted and not fixed and bool(subjects) and first_free_verb is None
    for e in fixed:
        a = e['action']
        events.append({'id': e['id'], 'concept': _norm_concept(e), 'kind': a['kind'], 'at': a['at'], 'dur': a.get('dur'),
                       'word': a.get('word'), 'word_ms': a.get('word_ms'), 'verb': None, 'reason': 'edu', 'clamped': False})
    events.sort(key=lambda x: (x['at'], x['id']))
    return {'events': events, 'failures': failures, 'unresolved': unresolved}
