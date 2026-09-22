"""Kinetic-type renderer — the "sentence-build" caption style.

Separate video TYPE from the whiteboard board world: text is the visual.
A full sentence stays laid out on screen; words flip state as they are
spoken — dim future -> active now -> settled — with emphasis treatments
(hand-drawn accent swoosh, dark highlight box on the active key word).

Shares the pipeline contract with the board renderer: beats carry
`narration` text; word timings (whisper / ElevenLabs / flat JSON) give
each word its spoken window; frames render deterministically at (t).
No drawing assets involved — this is typesetting, not illustration.
"""

import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_FONTS = Path(__file__).resolve().parent / 'assets' / 'fonts'

_FACES = {
    # Inter (OFL) — condensed-feel grotesk, matches commercial refs
    'grotesk': (_FONTS / 'inter' / 'Inter-Regular.ttf',
                _FONTS / 'inter' / 'Inter-Bold.ttf'),
    # marker face — bridges to the whiteboard house style
    'marker': (_FONTS / 'PermanentMarker.ttf',
               _FONTS / 'PermanentMarker.ttf'),
}

# Closed-class words: never emphasized, always settle back to plain ink.
_FUNC = frozenset(
    'the a an and or but if then that this these those is are was were be '
    'been it its it\'s to of in on at for with as by from we you they he she '
    'i me my our your their his her not no do does did have has had will '
    'would can could should shall may might must so such than too very just '
    'about into over under again once only own same how when where which who '
    'whom what why all any both each few more most other some them us also '
    'even still back out up down off around through between while during '
    'before after because until although though unless since whether both '
    'there here where when why how say says said tell tells told get gets '
    'got make makes made let lets go goes went come comes came per vs ok '
    'okay yeah really thing things way ways lot lots kind kinds stuff '.split())


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']+", '', str(w).lower())


def _emphasized(word: str, sentence_first: bool) -> bool:
    """Deterministic emphasis rule — works for any domain, no keyword tables.

    Emphasized: open-class words (not function words), digits/numbers, and
    TitleCase words that aren't sentence-initial (proper nouns)."""
    tok = _norm(word)
    if not tok:
        return False
    stem = tok.split("'")[0]          # contractions inherit their stem's
    if stem != tok and stem in _FUNC:  # class — "what's"/"that's" stay flat
        return False
    if tok in _FUNC or stem in _FUNC:
        return False
    stripped = word.strip('"\'“”‘’')
    if not sentence_first and stripped[:1].isupper() and len(tok) > 1:
        return True                      # proper noun
    if any(c.isdigit() for c in stripped):
        return True                      # numbers always pop
    return len(stem) >= 4


def split_sentences(text: str) -> list[str]:
    """Split narration on ., !, ? keeping the punctuation on its sentence."""
    parts = re.findall(r'[^.!?]+[.!?]*', str(text))
    return [p.strip() for p in parts if p.strip()]


def _font(face: str, bold: bool, size: int) -> ImageFont.FreeTypeFont:
    reg, bld = _FACES.get(face, _FACES['grotesk'])
    return ImageFont.truetype(str(bld if bold else reg), size)


def _tw(word: str, size: int, face: str, bold: bool = True) -> int:
    f = _font(face, bold, size)
    b = f.getbbox(word)
    return b[2] - b[0]


def typeset(sentence: dict, size: int, face: str, frame_w: int,
            margin: int = 64, gap_ratio: float = 0.22,
            frame_h: int | None = None):
    """Sentence -> wrapped lines of word slots at final (bold) widths.

    `sentence` is {'words': [{'word','start','end','emph'}...]}.
    Returns {'lines': [[slot...]], 'lh': line_height, 'block_h': int,
             'size': size} — slots carry x within the centered line and the
    word's timing/emph state inputs.
    """
    gap = max(10, int(size * gap_ratio))
    words = sentence['words']
    # per-sentence emphasis cap — content-dense narration would otherwise
    # accent nearly every word. Keep the strongest candidates: digits >
    # proper nouns > longest open-class words; ties go to the earlier word.
    cap = max(2, math.ceil(len(words) * 0.35))
    cands = []
    for i, w in enumerate(words):
        e = w.get('emph')
        if e is None:
            e = _emphasized(w['word'], sentence_first=(i == 0))
        if e:
            tok = _norm(w['word'])
            raw = w['word'].strip('"\'“”‘’')
            sc = (100 if any(c.isdigit() for c in raw) else 0) \
                + (50 if raw[:1].isupper() else 0) + len(tok)
            cands.append((sc, -i, i))
    keep = {i for _sc, _ni, i in sorted(cands, reverse=True)[:cap]}

    def lay(sz):
        items = []
        for i, w in enumerate(words):
            emph = w.get('emph')
            if emph is None:
                emph = _emphasized(w['word'], sentence_first=(i == 0)) \
                    and i in keep
            items.append({'w': w, 'emph': emph,
                          'tw': _tw(w['word'], sz, face, True)})
        lines, cur_w = [[]], 0
        for it in items:
            need = it['tw'] + (gap if lines[-1] else 0)
            if cur_w + need > frame_w - 2 * margin and lines[-1]:
                lines.append([it]); cur_w = it['tw']
            else:
                lines[-1].append(it); cur_w += need
        widest = max(sum(i['tw'] for i in l) + gap * (len(l) - 1)
                     for l in lines)
        return lines, widest

    size = int(size)
    vmargin = max(48, int(frame_h * 0.08)) if frame_h else 0
    while True:
        lines, widest = lay(size)
        lh = int(size * 1.42)
        fits_w = widest <= frame_w - 2 * margin
        fits_h = frame_h is None or lh * len(lines) <= frame_h - 2 * vmargin
        if (fits_w and fits_h) or size <= 18:
            break
        size = int(size * 0.90)
    return {'lines': lines, 'size': size, 'lh': lh,
            'block_h': lh * len(lines), 'gap': gap}


def attach_word_times(sentence_words: list[str], word_times: list[dict],
                      start: float, end: float) -> list[dict]:
    """Give each sentence word a spoken window. `word_times` (absolute,
    sequential) wins; missing entries distribute evenly across
    [start, end] so fixtures/tests need no audio."""
    out = []
    for i, w in enumerate(sentence_words):
        wt = word_times[i] if i < len(word_times) else None
        if wt:
            out.append({'word': w, 'start': float(wt['start']),
                        'end': float(wt['end'])})
        else:
            n = max(1, len(sentence_words))
            span = (end - start) / n
            out.append({'word': w,
                        'start': start + i * span,
                        'end': start + (i + 1) * span})
    return out


def sentence_words(plan: dict, word_times: list[dict] | None):
    """Plan beats -> kinetic sentence list.

    Each beat's `narration` splits into sentences; sentences tile the beat
    window proportionally by word count (or by actual word timings when
    the beat was audio-aligned). Returns [{'text', 'words':[...],
    'start', 'end'}] in absolute timeline seconds.
    """
    beats = plan.get('beats') or []
    wt_i = 0
    sents: list[dict] = []
    for b in beats:
        text = str(b.get('narration') or b.get('text') or '').strip()
        if not text:
            continue
        bs = float(b.get('start_seconds', 0.0))
        be = bs + float(b.get('duration_seconds', 1.0))
        parts = split_sentences(text)
        n_words_beat = sum(len(p.split()) for p in parts)
        cursor = bs
        for p in parts:
            ws = p.split()
            # locate this sentence's words in the timing stream
            found = None
            if word_times:
                first_tok = _norm(ws[0])
                for j in range(wt_i, min(len(word_times), wt_i + 200)):
                    if _norm(word_times[j]['word']) == first_tok:
                        found = j
                        break
            if found is not None:
                end_i = min(len(word_times) - 1, found + len(ws) - 1)
                ss = float(word_times[found]['start'])
                se = float(word_times[end_i]['end'])
                sub = word_times[found:end_i + 1]
                wt_i = end_i + 1
            else:
                share = (be - bs) * (len(ws) / max(1, n_words_beat))
                ss, se = cursor, cursor + share
                sub = []
                cursor = se
            words = attach_word_times(ws, sub, ss, se)
            sents.append({'text': p, 'words': words,
                          'start': words[0]['start'], 'end': words[-1]['end']})
    return sents


def _ease_out(p: float) -> float:
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def _swoosh(d: ImageDraw.ImageDraw, x0, x1, y, color, prog: float,
            lw: int = 4):
    """Hand-drawn accent underline — a smooth marker swipe that dips below
    the line with a tapered brush (thin ends, fat belly), drawn in
    left-to-right over the first ~0.28 s after the word is spoken."""
    n = 28
    upto = max(2, int(round(n * min(1.0, prog))))
    top, bot = [], []
    for i in range(upto):
        q = i / (n - 1)
        dip = math.sin(math.pi * q) * lw * 1.35          # bows below the line
        wob = math.sin(q * 9.2 + 0.7) * lw * 0.22        # faint hand wobble
        th = lw * (0.45 + 0.55 * math.sin(math.pi * q))  # tapered ends
        cx = x0 + (x1 - x0) * q
        cy = y + dip + wob + q * lw * 0.30
        top.append((cx, cy - th / 2))
        bot.append((cx, cy + th / 2))
    if len(top) >= 2:
        d.polygon(top + bot[::-1], fill=color)


def render_sentence(draw: ImageDraw.ImageDraw, spec: dict, t: float,
                    frame_w: int, frame_h: int, pal: dict,
                    alpha: float = 1.0, y_shift: float = 0.0,
                    face: str = 'grotesk'):
    """Draw one typeset sentence at absolute time t onto `draw`.

    Word states: future (dim regular), active (bold; key words get the
    highlight box + white text), settled (ink; key words accent + swoosh).
    `alpha`/`y_shift` drive the sentence-entry transition.
    """
    size = spec['size']; lh = spec['lh']; gap = spec['gap']
    ink = pal.get('ink', (28, 28, 26))
    dim = pal.get('dim', (203, 199, 190))
    acc = pal.get('accent', (0, 82, 255))
    boxc = pal.get('box', (24, 24, 26))
    a = max(0.0, min(1.0, alpha))
    bg = pal.get('paper', (252, 252, 250))
    fade = lambda c: tuple(int(ch * a) + int(bg[j] * (1 - a))
                           for j, ch in enumerate(c))
    y = frame_h * 0.46 - spec['block_h'] / 2 + y_shift
    for line in spec['lines']:
        total = sum(it['tw'] for it in line) + gap * (len(line) - 1)
        x = (frame_w - total) / 2
        for it in line:
            w = it['w']
            tw = it['tw']
            age = t - w['start']
            span = max(0.05, w['end'] - w['start'])
            hold = w['end'] + min(0.12, span * 0.4)
            emph = it['emph']
            if age < -0.02:
                col, bold = dim, emph
            elif t < hold:
                bold = True
                g = _ease_out(min(1.0, max(0.0, age) / 0.14))
                if emph:
                    # the highlight box grows in from the left while the
                    # word's color eases ink -> white
                    pad = max(8, int(size * 0.16))
                    dcol = fade(boxc)
                    draw.rounded_rectangle(
                        [x - pad, y - size * 0.06,
                         x + tw * g + pad, y + size * 1.14],
                        radius=size * 0.18, fill=dcol)
                    col = _lerp(ink, (255, 255, 255), g)
                else:
                    col = _lerp(dim, ink, g)
            else:
                st = _ease_out(min(1.0, (t - hold) / 0.14))
                col = _lerp(ink, acc, st) if emph else ink
                bold = emph
            pop = 1.0
            if 0 <= age < 0.16:
                pop = 1.0 + 0.12 * (1 - _ease_out(age / 0.16))
            sz = max(8, int(size * pop))
            f = _font(face, bold, sz)
            tw_s = _tw(w['word'], sz, face, bold)
            # the active-word pop widens past its slot — clamp so the
            # popped word can never cross the frame edge
            cx = x + tw / 2
            max_tw = 2 * min(cx - 8, frame_w - 8 - cx)
            if tw_s > max_tw:
                sz = max(8, int(sz * max_tw / tw_s))
                f = _font(face, bold, sz)
                tw_s = _tw(w['word'], sz, face, bold)
            ccol = fade(col) if a < 1 else col
            draw.text((x + (tw - tw_s) / 2, y + (size - sz) * 0.55),
                      w['word'], font=f, fill=ccol)
            if emph and age > 0.25:
                _swoosh(draw, x - size * 0.06, x + tw + size * 0.06,
                        y + size * 1.22,
                        acc if a >= 1 else fade(acc),
                        prog=min(1.0, (age - 0.25) / 0.28),
                        lw=max(3, size // 16))
            x += tw + gap
        y += lh


def _lerp(c1, c2, u):
    u = max(0.0, min(1.0, u))
    return tuple(int(a + (b - a) * u) for a, b in zip(c1, c2))


_THEMES = {
    'light': {'paper': (252, 252, 250), 'ink': (22, 22, 20),
              'dim': (172, 168, 158), 'box': (22, 22, 24)},
    'dark': {'paper': (18, 18, 16), 'ink': (245, 242, 235),
             'dim': (128, 124, 113), 'box': None},  # box <- accent
}


def palette(plan: dict, theme: str = 'light') -> dict:
    ba = (plan.get('brandExecution') or {}).get('brandAuthority') or {}
    def hx(k, d):
        v = str(ba.get(k, d)).lstrip('#')
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    t = _THEMES[theme]
    accent = hx('accent', '#0052FF')
    pal = dict(t)
    if theme == 'dark':
        # accent text lightened for dark-bg legibility; the highlight box
        # uses the raw brand accent so it reads as the same brand
        pal['accent'] = tuple(int(c + (255 - c) * 0.38) for c in accent)
        pal['box'] = accent
    else:
        pal['accent'] = accent
    return pal


_TRANS_S = 0.34


def render_kinetic_frame(sents: list[dict], specs: list[dict], t: float,
                         size: tuple[int, int], plan: dict,
                         face: str = 'grotesk', theme: str = 'light',
                         watermark: str | None = None):
    """Full frame at absolute t: active sentence centered; when a new
    sentence just became active, the previous one slides up & fades while
    the new one rises into place."""
    W, H = size
    pal = palette(plan, theme)
    img = Image.new('RGB', (W, H), pal['paper'])
    d = ImageDraw.Draw(img)
    if not sents:
        return img
    i = 0
    for k, s in enumerate(sents):
        if s['start'] <= t + 0.04:
            i = k
        else:
            break
    age = t - sents[i]['start']
    if i > 0 and age < _TRANS_S:
        q = _ease_out(age / _TRANS_S)
        # previous sentence exits fully upward; the new one rises in — a
        # small shift would leave two tall blocks overlapping mid-frame
        render_sentence(d, specs[i - 1], t, W, H, pal,
                        alpha=1.0 - q, y_shift=-(H * 0.55) * q, face=face)
        # cap the entry rise so a tall block's bottom never dips below
        # the frame — no word is ever partially out of frame
        enter = min(H * 0.30,
                    max(0.0, H * 0.54 - specs[i]['block_h'] / 2 - 8))
        render_sentence(d, specs[i], t, W, H, pal,
                        alpha=q, y_shift=enter * (1 - q), face=face)
    else:
        render_sentence(d, specs[i], t, W, H, pal, face=face)
    wm = watermark if watermark is not None else plan.get('watermark')
    if wm:
        ws = max(11, int(H * 0.022))
        wf = _font(face, False, ws)
        wb = wf.getbbox(wm)
        d.text(((W - (wb[2] - wb[0])) / 2, H * 0.955 - wb[1]),
               wm, font=wf, fill=pal['dim'])
    return img


def base_size(ratio_w: int, ratio_h: int) -> int:
    """Nominal type size per frame — 9:16 text carries the whole frame."""
    return max(40, int(min(ratio_w, ratio_h) * 0.115))
