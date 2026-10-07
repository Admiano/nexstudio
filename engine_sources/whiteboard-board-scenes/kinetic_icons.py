"""Sparse word icons for kinetic type: the drawing takes its word's
place inside the line.

An icon joins a sentence only when its key word names a concrete,
picturable thing (object, animal, food, plant, vehicle, body of nature)
used as a noun, and the library holds a drawing that unmistakably is
that thing. Abstract words, people and verbs stay text only. A script
gets at most one icon per sentence, on roughly one sentence in three,
never in back-to-back sentences and never the same drawing twice.
"""
from __future__ import annotations

import math
import re

from PIL import Image, ImageDraw

_CONCRETE_LEX = frozenset({
    'noun.artifact', 'noun.animal', 'noun.food', 'noun.plant',
    'noun.object'})
_DETERMINERS = frozenset(
    'a an the my his her their our your its this that these those some '
    'every each one two three four five six seven eight nine ten no any '
    'another whose'.split())
MAX_RANK = 10
MIN_SIM = 0.30
SENTENCES_PER_ICON = 3

_v3 = None


def _r():
    global _v3
    if _v3 is None:
        import v3_board_renderer
        _v3 = v3_board_renderer
    return _v3


def _tok(w: str) -> str:
    return re.sub(r"[^a-z0-9'-]+", '', str(w).lower()).strip("'-")


def _senses(phrase: str):
    """Noun senses of the phrase's lemma ('shoes' -> shoe, not the
    'in someone's shoes' plural sense)."""
    wn = _r()._WN
    if wn is None:
        return []
    key = phrase.strip().replace(' ', '_').replace('-', '_').lower()
    for lem in (_r()._singular(key), wn.morphy(key, wn.NOUN), key):
        if lem and wn.synsets(lem, pos=wn.NOUN):
            return wn.synsets(lem, pos=wn.NOUN)
    return []


def _is_concrete_sense(ss) -> bool:
    lex = ss.lexname()
    if lex not in _CONCRETE_LEX:
        return False
    if lex == 'noun.object':
        return any(h.name().startswith(
            ('natural_object', 'land.', 'body_of_water'))
            for path in ss.hypernym_paths() for h in path)
    return True


def concrete_noun(phrase: str) -> bool:
    """One of the phrase's two leading noun senses is a concrete thing
    ('football' the ball, 'whistle' the instrument). People are never
    icons — the cast draws them."""
    ns = _senses(phrase)
    if not ns or ns[0].lexname() == 'noun.person':
        return False
    return any(_is_concrete_sense(x) for x in ns[:2])


def script_concreteness(sents: list[dict]) -> float:
    """Share of the script's nouns (words in a noun slot) that name a
    physical thing. Abstract scripts (habits, trust, strategy) stay text
    only."""
    nouns = conc = 0
    for s in sents:
        words = [w['word'] for w in s['words']]
        for i, w in enumerate(words):
            t = _tok(w)
            if len(t) < 3 or not t.isalpha() or not _noun_slot(words, i):
                continue
            nxt = _tok(words[i + 1]) if i + 1 < len(words) else ''
            if nxt and _senses(nxt) and _r()._WN.synsets(
                    t, pos=_r()._WN.ADJ):
                continue  # modifier ('whole town', 'final whistle')
            ns = _senses(t)
            if not ns or ns[0].lexname() == 'noun.person':
                continue
            nouns += 1
            conc += concrete_noun(t)
    return conc / nouns if nouns else 0.0


MIN_SCRIPT_CONCRETENESS = 0.25
_PREPOSITIONS = frozenset(
    'of for with from into onto in on at by under over behind beside '
    'near past through across inside outside toward towards'.split())


def _noun_slot(words: list[str], i: int) -> bool:
    """The word is used as a noun: it follows a determiner, number,
    possessive or adjective (directly or through one modifier)."""
    wn = _r()._WN
    for back in (1, 2):
        j = i - back
        if j < 0:
            return False
        prev = _tok(words[j])
        if prev in _DETERMINERS or prev.endswith("'s") or prev.isdigit() \
                or (back == 1 and prev in _PREPOSITIONS):
            return True
        if wn is None:
            return False
        if back == 1 and wn.synsets(prev, pos=wn.VERB):
            return True  # verb's object ('recognize images')
        adj = wn.synsets(prev, pos=wn.ADJ)
        noun = wn.synsets(prev, pos=wn.NOUN)
        if not (adj or noun):
            return False
        if back == 2:
            return False
    return False


def _art(phrase: str, used):
    v3 = _r()
    ic = v3.icon_for(phrase, used)
    if not (isinstance(ic, tuple) and len(ic) == 3
            and ic[0] in ('icon', 'illust') and isinstance(ic[2], str)):
        return None, None
    if ic[1] in ('animicon', 'notomoji') or not v3.art_related(phrase, ic):
        return None, None
    import art_clip
    key = (ic[1], ic[2])
    rank = art_clip.rank(phrase, key) if art_clip.available() else None
    sim = art_clip.score(phrase, key) if art_clip.available() else None
    if rank is None or sim is None or rank > MAX_RANK or sim < MIN_SIM:
        return None, None
    strokes = v3._strokes_for(ic)
    if not strokes:
        return None, None
    return ic, {'rank': rank, 'sim': round(float(sim), 4),
                'strokes': strokes}


def candidates(words: list[str]) -> list[dict]:
    """Concrete noun phrases in one sentence: [{'i', 'phrase'}], where i
    is the head word index (the word the icon rides on)."""
    out = []
    for i, w in enumerate(words):
        t = _tok(w)
        if len(t) < 3 or not t.isalpha():
            continue
        if i + 1 < len(words) and concrete_noun(
                f'{t} {_tok(words[i + 1])}'):
            continue  # head of a compound sits on the next word
        if i > 0 and concrete_noun(f'{_tok(words[i - 1])} {t}') \
                and _noun_slot(words, i - 1):
            out.append({'i': i, 'phrase': f'{_tok(words[i - 1])} {t}'})
            continue
        if concrete_noun(t) and _noun_slot(words, i):
            out.append({'i': i, 'phrase': t})
    return out


def select(sents: list[dict]) -> dict[int, dict]:
    """Pick the sparse icon set for a whole script: {sentence index:
    {'word', 'phrase', 'icon', 'strokes', 'rank', 'sim'}}."""
    used: dict = {}
    has_concrete = any(
        candidates([w['word'] for w in s['words']]) for s in sents)
    if not has_concrete and script_concreteness(sents) < MIN_SCRIPT_CONCRETENESS:
        return {}
    best: list[tuple[float, int, dict]] = []
    for si, s in enumerate(sents):
        words = [w['word'] for w in s['words']]
        top = None
        for c in candidates(words):
            ic, info = _art(c['phrase'], used)
            if ic is None:
                continue
            row = {'word': c['i'], 'phrase': c['phrase'], 'icon': ic,
                   **info}
            if top is None or row['sim'] > top['sim']:
                top = row
        if top:
            best.append((top['sim'], si, top))
    budget = max(1, math.ceil(len(sents) / SENTENCES_PER_ICON)) \
        if sents else 0
    picked: dict[int, dict] = {}
    seen: set = set()
    for _sim, si, row in sorted(best, key=lambda r: (-r[0], r[1])):
        if len(picked) >= budget:
            break
        key = (row['icon'][1], row['icon'][2])
        if key in seen or (si - 1) in picked or (si + 1) in picked:
            continue
        picked[si] = row
        seen.add(key)
    return dict(sorted(picked.items()))


def apply(sents: list[dict], picks: dict[int, dict]) -> None:
    """The drawing replaces its word in the sentence."""
    for si, row in picks.items():
        sents[si]['icon'] = row


def qa(sents: list[dict], picks: dict[int, dict]) -> list[dict]:
    issues = []
    budget = max(1, math.ceil(len(sents) / SENTENCES_PER_ICON))
    if len(picks) > budget:
        issues.append({'severity': 'fail', 'check': 'icon-budget',
                       'detail': f'{len(picks)} icons > {budget}'})
    keys = [(r['icon'][1], r['icon'][2]) for r in picks.values()]
    if len(keys) != len(set(keys)):
        issues.append({'severity': 'fail', 'check': 'icon-repeat',
                       'detail': 'same drawing used twice'})
    for si, r in picks.items():
        if si + 1 in picks:
            issues.append({'severity': 'fail', 'check': 'icon-adjacent',
                           'beat': si, 'detail': 'icons in back-to-back '
                           'sentences'})
        if not concrete_noun(r['phrase']):
            issues.append({'severity': 'fail', 'check': 'icon-abstract',
                           'beat': si, 'detail': r['phrase']})
        if r['rank'] > MAX_RANK or r['sim'] < MIN_SIM:
            issues.append({'severity': 'fail', 'check': 'icon-match',
                           'beat': si,
                           'detail': f"{r['phrase']} -> {r['icon'][2]}"})
        w = sents[si]['words'][r['word']]
        if not _tok(w['word']) or _tok(w['word']) not in r['phrase']:
            issues.append({'severity': 'fail', 'check': 'icon-timing',
                           'beat': si, 'detail': 'icon not on its word'})
    return issues


DRAW_S = 0.45


def draw_icon(img: Image.Image, strokes, center, size: float, t0: float,
              t: float, ink, accent, paper) -> None:
    """Draw a library stroke group in the kinetic palette: outlines in
    ink, filled regions as a soft accent tint, drawn on from t0."""
    v3 = _r()
    p = max(0.0, min(1.0, (t - t0) / DRAW_S))
    if p <= 0:
        return
    tint = tuple(int(a * 0.30 + b * 0.70) for a, b in zip(accent, paper))
    ss = 3
    W = H = int(size * 1.15 * ss)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    n = len(strokes)
    lw = max(2, int(size * 0.045 * ss))
    for fills in (True, False):
        for j, st in enumerate(strokes):
            q = max(0.0, min(1.0, p * n - j))
            if q <= 0:
                break
            pts = [(W / 2 + x * size * ss, H / 2 + y * size * ss)
                   for x, y in st[0]]
            fill = bool(st[3]) if len(st) > 3 else False
            if fill != fills or len(pts) < 2:
                continue
            col = st[1]
            if fill:
                if q >= 1 and len(pts) >= 3:
                    tone = v3.SVG_TONES.get(col)
                    c = tint if tone is None or col == 'ink' else tuple(
                        int(a * 0.55 + b * 0.45)
                        for a, b in zip(tone, paper))
                    d.polygon(pts, fill=c + (255,))
                continue
            k = max(2, int(round(len(pts) * q)))
            c = accent if col == 'accent' else ink
            d.line(pts[:k], fill=tuple(c) + (255,), width=lw,
                   joint='curve')
    lay = lay.resize((W // ss, H // ss), Image.LANCZOS)
    img.paste(lay, (int(center[0] - lay.width / 2),
                    int(center[1] - lay.height / 2)), lay)
