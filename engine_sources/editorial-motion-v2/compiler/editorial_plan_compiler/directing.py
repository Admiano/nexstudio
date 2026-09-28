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
    'froze': 'freeze', 'frozen': 'freeze', 'drank': 'drink', 'drunk': 'drink', 'broken': 'break', 'shattered': 'shatter',
    'lighted': 'light', 'filled': 'fill', 'cracked': 'crack', 'spilt': 'spill', 'burnt': 'burn', 'withered': 'wither',
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
    'appear': 'pop', 'arrive': 'pop', 'pop': 'pop', 'hatch': 'hatch', 'emerge': 'pop', 'land': 'pop', 'burst': 'pop',
    'vanish': 'vanish', 'disappear': 'vanish', 'melt': 'melt', 'leave': 'vanish', 'hide': 'vanish', 'escape': 'vanish',
    'open': 'unfold', 'unfold': 'unfold', 'unfurl': 'unfold', 'spread': 'unfold', 'stretch': 'unfold',
    'wave': 'wave', 'billow': 'wave', 'sway': 'wave', 'ripple': 'wave', 'flutters': 'wave',
    'swim': 'swim', 'bob': 'swim', 'paddle': 'swim',
    'orbit': 'orbit', 'circle': 'orbit', 'loop': 'orbit',
    'beat': 'pulse', 'pulse': 'pulse', 'thump': 'pulse', 'throb': 'pulse',
    'crack': 'crack', 'break': 'crack', 'smash': 'crack', 'shatter': 'crack', 'split': 'crack',
    'fill': 'fill', 'empty': 'empty', 'drink': 'empty', 'spill': 'empty', 'drain': 'empty',
    'ignite': 'light', 'kindle': 'light', 'extinguish': 'out', 'snuff': 'out',
    'wilt': 'wilt', 'droop': 'wilt', 'wither': 'wilt', 'freeze': 'freeze', 'frost': 'freeze',
    'close': 'close', 'shut': 'close', 'slam': 'close',
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
    ('blow', 'on'): 'shake', ('break', 'open'): 'crack', ('crack', 'open'): 'crack', ('fill', 'up'): 'fill',
    ('swing', 'open'): 'unfold', ('fly', 'open'): 'unfold', ('slam', 'shut'): 'close', ('swing', 'shut'): 'close',
    ('go', 'away'): 'vanish', ('swim', 'away'): 'vanish', ('fly', 'off'): 'fly', ('roll', 'away'): 'roll',
}

# "blew the candle out": a particle closing the clause completes the verb it follows.
SPLIT_PARTICLES = frozenset(('out', 'off', 'up', 'open', 'shut', 'away', 'down'))
SPLIT_REACH = 5

DURATION = {
    'grow': 1500, 'kick': 950, 'bounce': 1100, 'hop': 700, 'roll': 1400, 'travel': 1800, 'fall': 1300,
    'rise': 2000, 'fly': 1900, 'spin': 1200, 'shake': 700, 'shine': 900, 'dim': 1100, 'phase': 1700,
    'pop': 380, 'vanish': 800, 'unfold': 900, 'wave': 1800, 'swim': 2000, 'flutter': 1600, 'orbit': 2400,
    'pulse': 1400, 'hatch': 1700, 'crack': 900, 'fill': 1600, 'empty': 1400, 'light': 900, 'out': 1000,
    'melt': 1900, 'wilt': 1500, 'freeze': 1300, 'swing': 1000, 'close': 900,
}
# Object state vocabulary: the verb's primitive becomes the state change the object itself
# undergoes — a candle that "went out" loses its flame, it does not fade; a door "opened"
# swings on its hinge; ice that "melted" slumps into a puddle.
FLAME = ('candle', 'lantern', 'lamp', 'torch', 'campfire', 'fire', 'match', 'fireplace', 'bonfire', 'oil-lamp', 'diya')
CONTAINER = ('cup', 'glass', 'mug', 'jug', 'bucket', 'bowl', 'jar', 'pot', 'bottle', 'vase', 'teapot', 'pitcher',
             'bathtub', 'tub', 'kettle', 'beaker', 'watering-can', 'pail', 'tank', 'pool', 'pond', 'well')
HINGED = ('door', 'gate', 'window', 'cupboard', 'fridge', 'wardrobe', 'closet', 'shutter', 'locker', 'cabinet')
MELTS = ('ice', 'snowman', 'snow', 'ice-cream', 'icecream', 'ice-cube', 'icicle', 'popsicle', 'butter', 'chocolate', 'glacier', 'candle')
WILTS = ('flower', 'rose', 'tulip', 'sunflower', 'daisy', 'plant', 'bloom', 'blossom', 'lily', 'bouquet', 'leaf')
LIQUIDS = {'milk': '#f3efe4', 'juice': '#f0a53a', 'orange': '#f0a53a', 'lemonade': '#f1df78', 'tea': '#9a6232',
           'coffee': '#6b4226', 'cocoa': '#6b4226', 'chocolate': '#6b4226', 'soup': '#d98a3d', 'honey': '#e3a92c',
           'paint': '#c9453a', 'wine': '#7e2433', 'lava': '#e0582a', 'oil': '#d8b94a', 'water': '#6fa8c9', 'rain': '#6fa8c9'}
SHELLED = ('egg', 'nut', 'coconut', 'shell', 'pinata', 'seed-pod')
HATCHLING = ('chick', 'duckling', 'baby-bird', 'hatchling', 'dragon', 'dinosaur', 'turtle', 'baby-chick', 'hatching-chick', 'bird', 'snake', 'crocodile')


SUBJECT_DETERMINERS = frozenset(('the', 'a', 'an', 'his', 'her', 'their', 'my', 'our', 'its'))


def _is(concept: str, family: Sequence[str]) -> bool:
    parts = set(concept.replace('_', '-').split('-')) | {concept}
    return any(f in parts or concept == f or concept.endswith('-' + f) for f in family)


def state_kind(kind: str, lemma: Optional[str], concept: str) -> str:
    """Primitive (from the verb) + the element's concept -> the state change it performs."""
    if _is(concept, FLAME):
        if kind in ('dim', 'vanish', 'out'):
            return 'out'
        if kind in ('shine', 'light') or lemma in ('light', 'ignite', 'kindle'):
            return 'light'
        if kind == 'melt':
            return 'melt'
    if _is(concept, CONTAINER):
        if kind in ('fill',) or lemma in ('pour', 'fill'):
            return 'fill'
        if kind in ('empty',) or lemma in ('drink', 'spill', 'empty', 'drain'):
            return 'empty'
    if _is(concept, HINGED):
        if kind == 'unfold':
            return 'swing'
        if kind == 'close':
            return 'close'
    if kind == 'melt':
        return 'melt' if _is(concept, MELTS) else 'vanish'
    if kind == 'wilt' and not _is(concept, WILTS):
        return 'fall'
    if kind == 'hatch' and not _is(concept, SHELLED):
        return 'pop'
    if kind in ('fill', 'empty') and not _is(concept, CONTAINER):
        return 'pop' if kind == 'fill' else 'vanish'
    if kind in ('light',):
        return 'shine'
    if kind in ('out',):
        return 'dim'
    if kind in ('close',):
        return 'shake'
    return kind
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
    for j in range(i + 2, min(len(toks), i + 1 + SPLIT_REACH)):
        if _clause_end(toks[j - 1]):
            break
        if toks[j]['t'] in SPLIT_PARTICLES and (j + 1 == len(toks) or _clause_end(toks[j])):
            for l in ls:
                if (l, toks[j]['t']) in PHRASAL:
                    return PHRASAL[(l, toks[j]['t'])], f"{l} {toks[j]['t']}", 1
    for l in ls:
        if l in VERB_KIND:
            return VERB_KIND[l], l, 1
    return None, None, 1


def _clause_end(tok: Dict[str, Any]) -> bool:
    return bool(re.search(r'[.,;:!?]$', str(tok.get('raw') or '')))


def _number(t: str) -> Optional[int]:
    if t.isdigit():
        return int(t)
    return NUMBER_WORDS.get(t)


def _norm_concept(e: Dict[str, Any]) -> str:
    return str(e.get('concept') or '').lower().replace('_', '-')


def _refine(kind: str, concept: str, e: Dict[str, Any], zone: Dict[str, float], lemma: Optional[str] = None) -> Dict[str, Any]:
    """Primitive -> parameterised action for this element on this plate."""
    act: Dict[str, Any] = {'kind': state_kind(kind, lemma, concept)}
    if act['kind'] == 'dim' and 'moon' in concept:
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
            act['dur'] = min(int(act.get('dur') or 600), max(200, (window_ms if window_ms is not None else latest) - start))
        act['at'] = int(start)
        if act['kind'] in ('fill', 'empty', 'melt') and 'liquid' not in act:
            named = [LIQUIDS[t['t']] for t in toks if t['t'] in LIQUIDS]
            if named:
                act['liquid'] = named[0]
            elif act['kind'] == 'melt' and 'chocolate' in _norm_concept(e):
                act['liquid'] = LIQUIDS['chocolate']
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
        nums = [(i, n) for i, tk in enumerate(toks) if (n := _number(tk['t'])) is not None]
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
    first_free_verb: Optional[Tuple[str, Optional[str], Dict[str, Any]]] = None
    while i < len(toks):
        kind, lemma, span = verb_kind(toks, i)
        if kind is not None and i > 0 and toks[i - 1]['t'] in SUBJECT_DETERMINERS:
            kind = None  # "the rain", "a light": a determiner makes the word a noun
        if kind is None:
            i += span
            continue
        hits = None
        offpage = False
        for j in range(i - 1, max(-1, i - 1 - SUBJECT_REACH), -1):
            if _clause_end(toks[j]):
                break
            cand = [e for e in mentions.get(j, []) if e['id'] not in acted and _norm_concept(e) not in counted]
            if cand:
                hits = cand
                break
            if not mentions.get(j) and j > 0 and toks[j - 1]['t'] in SUBJECT_DETERMINERS:
                # "the rain fell": the verb's own subject is named and is not on the plate.
                offpage = True
                break
        if hits is None and not offpage:
            for j in range(i + span, min(len(toks), i + span + SUBJECT_REACH)):
                if j > i + span and _clause_end(toks[j - 1]):
                    break
                cand = [e for e in mentions.get(j, []) if e['id'] not in acted and _norm_concept(e) not in counted]
                if cand:
                    hits = cand
                    break
        if kind in ('hatch', 'crack'):
            # "The chick hatched" breaks the egg, not the chick: the shell is what changes state.
            shells = [e for e in subjects if e['id'] not in acted and _is(_norm_concept(e), SHELLED)]
            if shells and (hits is None or not any(_is(_norm_concept(x), SHELLED) for x in hits)):
                hits = shells
        if hits is None:
            if first_free_verb is None:
                first_free_verb = (kind, lemma, toks[i])
        else:
            e = max(hits, key=lambda x: float((x.get('bbox') or {}).get('w') or 0) * float((x.get('bbox') or {}).get('h') or 0))
            if place(e, _refine(kind, _norm_concept(e), e, zone, lemma), toks[i]['at'], toks[i], 'verb', lemma):
                acted.add(e['id'])
                if e['action']['kind'] == 'hatch':
                    # What was inside comes out as the shell parts.
                    out_at = int(e['action']['at'] + e['action']['dur'] * 0.55)
                    for h in subjects:
                        if h['id'] not in acted and _is(_norm_concept(h), HATCHLING):
                            if place(h, {'kind': 'pop', 'dur': POP_MS * 2}, out_at, None, 'state-follow', lemma):
                                acted.add(h['id'])
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
        place(e, _refine(kind, c, e, zone, lemma), tok['at'], tok, 'verb-primary', lemma)
    unresolved = not acted and not fixed and bool(subjects) and first_free_verb is None
    for e in fixed:
        a = e['action']
        events.append({'id': e['id'], 'concept': _norm_concept(e), 'kind': a['kind'], 'at': a['at'], 'dur': a.get('dur'),
                       'word': a.get('word'), 'word_ms': a.get('word_ms'), 'verb': None, 'reason': 'edu', 'clamped': False})
    events.sort(key=lambda x: (x['at'], x['id']))
    return {'events': events, 'failures': failures, 'unresolved': unresolved}
