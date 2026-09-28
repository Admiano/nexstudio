"""Teaching plates that are correct by construction.

A maths page is not a scatter of pretty objects: the quantity is built from the numbers
(five-frames and ten-frames for counting, two groups joining for addition, items leaving
for subtraction, equal rows for multiplication, dealing into equal groups for division,
equal parts of a whole for fractions, hops along a number line). The printed structure
(frames, plates, bars, ticks) is still; the objects act on the spoken numbers — one
object per number word — and the written sentence ("3 + 2 = 5") prints once the
answer is said. Every layout checks itself: shown quantity == stated quantity.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .directing import POP_MS, _number, tokens

# Transcribers hear a spoken answer as its homophone: "leaves for", "makes to".
ANSWER_HOMOPHONES = {'for': 4, 'fore': 4, 'to': 2, 'too': 2, 'won': 1, 'ate': 8}
ANSWER_WORDS = {'make', 'makes', 'equals', 'equal', 'is', 'are', 'altogether', 'total', 'left', 'each', 'gives', 'get', 'leaves'}
TAKE_WORDS = {'away', 'minus', 'flew', 'fly', 'ate', 'eat', 'eaten', 'left', 'leave', 'gone', 'popped', 'ran', 'swam', 'hopped', 'rolled', 'took', 'take'}
MINUS = '\u2212'
TIMES = '\u00d7'
DIVIDE = '\u00f7'


def _box(x: float, y: float, w: float, h: float) -> Dict[str, float]:
    return {'x': round(x, 2), 'y': round(y, 2), 'w': round(max(1.0, w), 2), 'h': round(max(1.0, h), 2)}


def result_of(edu: Dict[str, Any]) -> Optional[int]:
    k, a, b = edu['kind'], int(edu.get('a') or 0), int(edu.get('b') or 0)
    return {'count': a, 'add': a + b, 'subtract': a - b, 'multiply': a * b,
            'share': a // b if b else None, 'compare': None, 'fraction': None, 'numberline': a + b}.get(k)


def _ent(i: int, concept: str, box: Dict[str, float], action: Optional[Dict[str, Any]], enter_ms: int = 0) -> Dict[str, Any]:
    e = {'id': f'edu_{i}', 'concept': concept, 'kind': 'object', 'glyph': 'ICON', 'size': 'support', 'label': None,
         'media': None, 'photo': None, 'asset': None, 'carried': False, 'carry_from_bbox': None, 'state_in': {},
         'enter_ms': enter_ms, 'enter_duration_ms': 0 if action and action['kind'] == 'pop' else 360,
         'bbox': dict(box), 'art_bbox': dict(box), 'params': {'resolution': {'via': 'edu', 'concept': concept}}}
    if action:
        e['action'] = action
    return e


def _pop(at: int, k: int, n: int, tok: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    a = {'kind': 'pop', 'at': int(at), 'dur': POP_MS, 'index': k, 'of': n}
    if tok is not None:
        a['word'] = tok['raw']
        if tok['at'] is not None:
            a['word_ms'] = int(tok['at'])
    return a


class _Clock:
    """Spoken-number timing: the k-th object lands on the k-th spoken counting number."""

    def __init__(self, words: Optional[Sequence[Dict[str, Any]]], narration: Optional[str], window_ms: int, start_ms: int):
        self.toks = tokens(words, narration)
        self.window = int(window_ms)
        self.start = int(start_ms)
        self.nums = [(i, v) for i, v in ((i, self._value(i)) for i in range(len(self.toks))) if v is not None]

    def _value(self, i: int) -> Optional[int]:
        t = self.toks[i]['t']
        n = _number(t)
        if n is None and i > 0 and self.toks[i - 1]['t'] in ANSWER_WORDS and i == len(self.toks) - 1:
            return ANSWER_HOMOPHONES.get(t)
        return n

    def at_word(self, pred, after: int = 0) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        for t in self.toks:
            if t['at'] is not None and t['at'] >= after and pred(t['t']):
                return t['at'], t
        return None, None

    def sequence(self, n: int, first: int = 1, after: int = 0) -> List[Tuple[int, Optional[Dict[str, Any]]]]:
        """n landing times. Uses a spoken ascending run first..first+n-1 when present."""
        run: List[Dict[str, Any]] = []
        want = first
        for i, v in self.nums:
            t = self.toks[i]
            if v == want and (t['at'] is None or t['at'] >= after):
                run.append(t)
                want += 1
                if len(run) == n:
                    break
        if len(run) == n and all(t['at'] is not None for t in run):
            return [(max(self.start, t['at']), t) for t in run]
        anchor = max(self.start, after)
        space = max(110, min(320, int((self.window - 700 - anchor) / max(1, n))))
        return [(anchor + k * space, None) for k in range(n)]

    def answer(self, value: Optional[int], after: int) -> Tuple[int, Optional[Dict[str, Any]]]:
        """The written answer prints when the answer is spoken, else once the objects settle."""
        if value is not None:
            for i, v in reversed(self.nums):
                t = self.toks[i]
                if v == value and t['at'] is not None and t['at'] >= after:
                    return max(after, t['at']), t
        at, t = self.at_word(lambda w: w in ANSWER_WORDS, after)
        return (min(self.window - 300, max(after, at if at is not None else after + 220)), t)


def _cells(area: Dict[str, float], n: int, cols: int, rows: int, pad: float = 0.08) -> Tuple[List[Dict[str, float]], float]:
    s = min(area['w'] / cols, area['h'] / rows)
    ox = area['x'] + (area['w'] - s * cols) / 2
    oy = area['y'] + (area['h'] - s * rows) / 2
    out = []
    for k in range(n):
        r, c = divmod(k, cols)
        out.append(_box(ox + c * s, oy + r * s, s, s))
    return out, s


def _inset(b: Dict[str, float], f: float) -> Dict[str, float]:
    return _box(b['x'] + b['w'] * f, b['y'] + b['h'] * f, b['w'] * (1 - 2 * f), b['h'] * (1 - 2 * f))


def build(edu: Dict[str, Any], area: Dict[str, float], words: Optional[Sequence[Dict[str, Any]]],
          narration: Optional[str], window_ms: int, beat_id: str = 'beat') -> Dict[str, Any]:
    """Entities + printed overlay for one teaching page, and its own truth check."""
    k = edu['kind']
    obj = str(edu.get('object') or 'apple')
    a, b = int(edu.get('a') or 0), int(edu.get('b') or 0)
    clock = _Clock(words, narration, window_ms, 260)
    ents: List[Dict[str, Any]] = []
    frames: List[Dict[str, Any]] = []
    texts: List[Dict[str, Any]] = []
    x, y, w, h = area['x'], area['y'], area['w'], area['h']
    eq_h = h * 0.22
    top = _box(x, y, w, h - eq_h)
    fs = eq_h * 0.62
    eq_y = y + h - eq_h * 0.45
    res = result_of(edu)
    last = 0

    def frame(bx: Dict[str, float], rx: float = 0.12, fill: bool = False, at: Optional[int] = None) -> None:
        frames.append({'x': bx['x'], 'y': bx['y'], 'w': bx['w'], 'h': bx['h'], 'rx': round(min(bx['w'], bx['h']) * rx, 2), 'fill': fill, 'at': at})

    def text(s: str, cx: float, cy: float, size: float, at: Optional[int], tok: Optional[Dict[str, Any]] = None) -> None:
        t = {'text': s, 'x': round(cx, 2), 'y': round(cy, 2), 'size': round(size, 2), 'at': at}
        if tok is not None and tok.get('at') is not None:
            t['word_ms'] = int(tok['at'])
        texts.append(t)

    if k == 'count':
        cols = 5
        rows = max(1, math.ceil(a / cols)) if a > 5 else 1
        rows = 2 if a > 5 and a <= 10 else rows
        cells, s = _cells(top, cols * rows, cols, rows)
        for c in cells:
            frame(c, 0.06)
        for i, (t, tok) in enumerate(clock.sequence(a)):
            ents.append(_ent(i, obj, _inset(cells[i], 0.14), _pop(t, i + 1, a, tok)))
            last = t
        at, tok = clock.answer(a, last + POP_MS)
        text(str(a), x + w / 2, eq_y, fs * 1.2, at, tok)
    elif k == 'add':
        gw = w * 0.40
        ga, gb = _box(x, top['y'], gw, top['h']), _box(x + w - gw, top['y'], gw, top['h'])
        seq_a = clock.sequence(a)
        seq_start_b = seq_a[-1][0] + POP_MS if seq_a else 260
        plus_at, plus_tok = clock.at_word(lambda t: t in ('plus', 'and', 'add', 'more', 'join', 'joined'), seq_start_b - POP_MS)
        seq_b = clock.sequence(b, first=1, after=plus_at or seq_start_b) if b else []
        i = 0
        for grp, seq, n in ((ga, seq_a, a), (gb, seq_b, b)):
            cols = min(5, max(1, n)) if n <= 5 else math.ceil(n / 2)
            rows = 1 if n <= 5 else 2
            cells, _ = _cells(_inset(grp, 0.05), n, cols, rows)
            frame(_inset(grp, 0.02), 0.08)
            for j, (t, tok) in enumerate(seq):
                ents.append(_ent(i, obj, _inset(cells[j], 0.12), _pop(t, j + 1, n, tok)))
                i += 1
                last = max(last, t)
        text('+', x + w / 2, top['y'] + top['h'] / 2, fs * 1.3, plus_at if plus_at is not None else seq_start_b, plus_tok)
        at, tok = clock.answer(res, last + POP_MS)
        text(f'{a} + {b} = {res}', x + w / 2, eq_y, fs, at, tok)
    elif k == 'subtract':
        cols = min(5, max(1, a)) if a <= 5 else math.ceil(a / 2)
        rows = 1 if a <= 5 else 2
        cells, _ = _cells(top, a, cols, rows)
        for c in cells:
            frame(c, 0.06)
        go_at, go_tok = clock.at_word(lambda t: t in TAKE_WORDS, 400)
        go_at = go_at if go_at is not None else int(window_ms * 0.35)
        for i in range(a):
            act = None
            if i >= a - b:
                j = i - (a - b)
                act = {'kind': 'vanish', 'at': int(go_at + j * 160), 'dur': 800, 'dir': 1}
                if j == 0 and go_tok is not None and go_tok['at'] is not None:
                    act['word'], act['word_ms'] = go_tok['raw'], int(go_tok['at'])
                last = max(last, act['at'] + 800)
            ents.append(_ent(i, obj, _inset(cells[i], 0.12), act, enter_ms=60))
        at, tok = clock.answer(res, last)
        text(f'{a} {MINUS} {b} = {res}', x + w / 2, eq_y, fs, at, tok)
    elif k == 'multiply':
        cells, s = _cells(top, a * b, b, a)
        seq = clock.sequence(a)
        i = 0
        for r in range(a):
            row = cells[r * b:(r + 1) * b]
            frame(_box(row[0]['x'], row[0]['y'], s * b, s), 0.2)
            t, tok = seq[r]
            for c, cell in enumerate(row):
                ents.append(_ent(i, obj, _inset(cell, 0.14), _pop(t + c * 70, i + 1, a * b, tok if c == 0 else None)))
                i += 1
                last = max(last, t + c * 70)
        at, tok = clock.answer(res, last + POP_MS)
        text(f'{a} {TIMES} {b} = {res}', x + w / 2, eq_y, fs, at, tok)
    elif k == 'share':
        each = a // b
        gw = w / b
        groups = [_inset(_box(x + g * gw, top['y'], gw, top['h']), 0.06) for g in range(b)]
        for g in groups:
            frame(g, 0.5)
        per = [_cells(_inset(g, 0.18), each, min(each, 3), math.ceil(each / 3))[0] for g in groups]
        seq = clock.sequence(a)
        for i, (t, tok) in enumerate(seq):
            g, slot = i % b, i // b
            ents.append(_ent(i, obj, _inset(per[g][slot], 0.08), _pop(t, i + 1, a, tok)))
            last = t
        at, tok = clock.answer(res, last + POP_MS)
        text(f'{a} {DIVIDE} {b} = {res}', x + w / 2, eq_y, fs, at, tok)
    elif k == 'compare':
        n = max(a, b, 1)
        cw = w * 0.30
        s = min(cw, top['h'] / n)
        i = 0
        stacks = ((x + w * 0.12, a), (x + w * 0.88 - s, b))
        last_a = 0
        for si, (sx, cnt) in enumerate(stacks):
            seq = clock.sequence(cnt, after=last_a + POP_MS if si else 0)
            for j in range(cnt):
                cell = _box(sx, top['y'] + top['h'] - (j + 1) * s, s, s)
                frame(cell, 0.06)
                t, tok = seq[j]
                ents.append(_ent(i, obj, _inset(cell, 0.12), _pop(t, j + 1, cnt, tok)))
                i += 1
                last = max(last, t)
            if si == 0:
                last_a = last
            text(str(cnt), sx + s / 2, eq_y, fs, None)
        sym = '>' if a > b else '<' if a < b else '='
        at, tok = clock.at_word(lambda t: t in ('more', 'fewer', 'less', 'than', 'same', 'bigger', 'smaller'), last + POP_MS)
        text(sym, x + w / 2, top['y'] + top['h'] / 2, fs * 1.6, at if at is not None else last + POP_MS + 200, tok)
    elif k == 'fraction':
        bar = _box(x + w * 0.06, top['y'] + top['h'] * 0.3, w * 0.88, top['h'] * 0.4)
        pw = bar['w'] / b
        seq = clock.sequence(a)
        for p in range(b):
            cell = _box(bar['x'] + p * pw, bar['y'], pw, bar['h'])
            frame(cell, 0.04)
            if p < a:
                t, tok = seq[p]
                frame(_inset(cell, 0.08), 0.04, fill=True, at=int(t))
                last = t
        at, tok = clock.answer(None, last + POP_MS)
        text(f'{a}/{b}', x + w / 2, eq_y, fs, at, tok)
    elif k == 'numberline':
        hi = max(10, a + b)
        ly = top['y'] + top['h'] * 0.72
        step = w * 0.92 / hi
        x0 = x + w * 0.04
        frames.append({'x': round(x0, 2), 'y': round(ly, 2), 'w': round(step * hi, 2), 'h': 3.0, 'rx': 1.5, 'fill': True, 'at': None, 'ink': True})
        for v in range(hi + 1):
            frames.append({'x': round(x0 + v * step - 1.5, 2), 'y': round(ly - 9, 2), 'w': 3.0, 'h': 18.0, 'rx': 1.5, 'fill': True, 'at': None, 'ink': True})
            text(str(v), x0 + v * step, ly + top['h'] * 0.16, fs * 0.45, None)
        s = min(step * 0.9, top['h'] * 0.3)
        ents.append(_ent(0, obj, _box(x0 + a * step - s / 2, ly - s - 12, s, s), None, enter_ms=60))
        seq = clock.sequence(b, first=a + 1)
        for j, (t, tok) in enumerate(seq):
            ents.append(_ent(j + 1, obj, _box(x0 + (a + j + 1) * step - s / 2, ly - s - 12, s, s), _pop(t, j + 1, b, tok)))
            last = t
        at, tok = clock.answer(res, last + POP_MS)
        text(f'{a} + {b} = {res}', x + w / 2, eq_y, fs, at, tok)

    # Truth: what the page shows is what the numbers say, and what the voice claims.
    failures: List[str] = []
    shown = sum(1 for e in ents if not (e.get('action') or {}).get('kind') == 'vanish')
    expect = {'count': a, 'add': a + b, 'subtract': a - b, 'multiply': a * b, 'share': a, 'compare': a + b,
              'fraction': None, 'numberline': b + 1}.get(k)
    if expect is not None and shown != expect:
        failures.append(f'EDU_SHOWN_MISMATCH:{beat_id}:{k}:shows {shown}, expected {expect}')
    if k == 'fraction' and sum(1 for f in frames if f['fill'] and f['at'] is not None) != a:
        failures.append(f'EDU_SHOWN_MISMATCH:{beat_id}:fraction')
    spoken = [v for _, v in clock.nums]
    if res is not None and k != 'count' and spoken and spoken[-1] != res and res in range(0, 101) and \
            any(t['t'] in ANSWER_WORDS for t in clock.toks):
        failures.append(f'EDU_SPOKEN_ANSWER_MISMATCH:{beat_id}:said {spoken[-1]}, is {res}')
    for e in ents:
        e['bbox'] = dict(e['art_bbox'])
    return {'entities': ents, 'overlay': {'kind': k, 'frames': frames, 'texts': texts}, 'failures': failures}
