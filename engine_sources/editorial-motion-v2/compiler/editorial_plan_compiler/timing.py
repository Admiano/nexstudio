"""Voice is the clock.

Character alignment (ElevenLabs ``with-timestamps`` shape, or the fixture
synthesiser that mimics it) becomes word timings; word timings decide when each
authored display unit lands and how long each beat runs. Typography choreography
compiled for a beat is then re-timed so a unit's settle coincides with the word
that carries it.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

LEAD_IN_MS = 220          # stage settles before the first word
TAIL_HOLD_MS = 620        # settled read after the last word
LAND_BEFORE_WORD_MS = 90  # text lands a breath before the word is spoken
MIN_BEAT_MS = 1400
EXIT_MS = 320
MIN_EXIT_MS = 120
MIN_HOLD_MS = 480         # shortest readable settled state
LAND_SETTLE_MS = 640      # reveal + emphasis after the last landing before the state counts as settled
CASCADE_SETTLE_MS = 260   # a cascaded word is readable this long after it lands

_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’%.,:-]*[A-Za-z0-9%]|[A-Za-z0-9]")


@dataclass
class Word:
    text: str
    start_ms: int
    end_ms: int

    @property
    def key(self) -> str:
        return normalise(self.text)


def normalise(token: str) -> str:
    return re.sub(r"[^a-z0-9%]", '', token.lower().replace('’', "'"))


def words_from_alignment(alignment: Dict[str, Any]) -> List[Word]:
    """Group ElevenLabs character alignment into words."""
    chars: Sequence[str] = alignment.get('characters') or []
    starts: Sequence[float] = alignment.get('character_start_times_seconds') or []
    ends: Sequence[float] = alignment.get('character_end_times_seconds') or []
    if not (len(chars) == len(starts) == len(ends)):
        raise ValueError('ALIGNMENT_ARRAYS_MISMATCH')
    words: List[Word] = []
    buf: List[str] = []
    w_start = 0.0
    w_end = 0.0
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if buf:
                words.append(Word(''.join(buf), int(round(w_start * 1000)), int(round(w_end * 1000))))
                buf = []
            continue
        if not buf:
            w_start = float(s)
        buf.append(ch)
        w_end = float(e)
    if buf:
        words.append(Word(''.join(buf), int(round(w_start * 1000)), int(round(w_end * 1000))))
    return [w for w in words if normalise(w.text)]


def synthesise_alignment(text: str, seed: str, words_per_second: float = 2.6) -> Dict[str, Any]:
    """Deterministic FIXTURE alignment in the ElevenLabs shape. Not a voice.

    Word length drives duration, punctuation adds pauses, and a seeded ±8%
    jitter keeps the cadence from being metronomic. Used only when no TTS route
    is configured; provenance records it as FIXTURE_TIMING.
    """
    chars: List[str] = []
    starts: List[float] = []
    ends: List[float] = []
    t = 0.0
    base = 1.0 / max(1.2, words_per_second)
    for i, tok in enumerate(text.split()):
        core = re.sub(r'[^A-Za-z0-9]', '', tok)
        jitter = (int(hashlib.sha256(f'{seed}:{i}'.encode()).hexdigest()[:4], 16) % 17 - 8) / 100.0
        dur = base * (0.42 + 0.085 * max(2, len(core))) * (1 + jitter)
        dur = max(0.14, min(0.95, dur))
        per_char = dur / max(1, len(tok))
        for ch in tok:
            chars.append(ch)
            starts.append(round(t, 4))
            t += per_char
            ends.append(round(t, 4))
        pause = 0.07
        if tok.endswith(('.', '!', '?')):
            pause = 0.34
        elif tok.endswith((',', ';', ':', '—')):
            pause = 0.19
        chars.append(' ')
        starts.append(round(t, 4))
        t += pause
        ends.append(round(t, 4))
    if chars and chars[-1] == ' ':
        chars.pop(); starts.pop(); ends.pop()
    return {
        'characters': chars,
        'character_start_times_seconds': starts,
        'character_end_times_seconds': ends,
        'fixture': True,
    }


def find_landing(words: List[Word], anchor: str, search_from: int = 0) -> Optional[int]:
    """Index of the first word at/after ``search_from`` matching the anchor token."""
    key = normalise(anchor)
    if not key:
        return None
    for i in range(search_from, len(words)):
        if words[i].key == key or (len(key) >= 5 and words[i].key.startswith(key)):
            return i
    for i in range(0, search_from):
        if words[i].key == key:
            return i
    return None


def unit_anchor(unit_text: str, anchor_word: Optional[str]) -> str:
    if anchor_word:
        return anchor_word
    m = _WORD.search(unit_text)
    return m.group(0) if m else unit_text


@dataclass
class BeatClock:
    beat_id: str
    duration_ms: int
    voice_offset_ms: int           # where the VO starts inside the beat
    voice_duration_ms: int
    words: List[Word]              # timings relative to beat start
    landings_ms: List[int]         # one per display unit
    landing_source: List[str]      # WORD | PROPORTIONAL
    source: str                    # ELEVENLABS | FIXTURE | NONE
    fixed_window: bool = False     # MASTER: duration is set by the speech timeline and cannot grow
    budget_met: float = 1.0        # share of the readable settle/hold/exit budget the window affords
    exit_ms: int = EXIT_MS         # handoff length; under MASTER it is sized from the speaker's own pause
    pause_after_ms: int = -1       # MASTER: silence the speaker left after this beat's last word (-1: not a speech window)


def exit_for_pause(pause_ms: int) -> int:
    """The outgoing beat leaves inside the pause the speaker actually left, never longer than the
    authored exit — the exit takes at most a third of the pause so two-thirds stay readable."""
    return max(MIN_EXIT_MS, min(EXIT_MS, int(pause_ms * 0.34)))


def readable_close_floor(pause_ms: int) -> int:
    """How long a settled state must stay legible after its last word: the speaker's pause is the budget."""
    return min(MIN_HOLD_MS, max(100, int(pause_ms * 0.35)))


def _land_before(words: List[Word], idx: int) -> int:
    """Land a breath before the word, never more than 40% of the gap to the previous word."""
    if idx == 0:
        return LAND_BEFORE_WORD_MS
    gap = max(0, words[idx].start_ms - words[idx - 1].end_ms) + 40
    return min(LAND_BEFORE_WORD_MS, int(gap * 0.4))


def window_clock(beat_id: str, unit_texts: List[str], anchors: List[Optional[str]], words: List[Word],
                 window_ms: int, source: str, pause_after_ms: int = EXIT_MS * 2) -> BeatClock:
    """Beat clock for a MASTER window: words are already placed inside the beat, the window is fixed.

    Landings follow the spoken anchors exactly as in ``beat_clock``; nothing is padded. The
    readable close after the last landing is measured against the window and reported as
    ``budget_met`` so the gate, not the clock, decides what a short window means.
    """
    voice_ms = max((w.end_ms for w in words), default=0)
    first = words[0].start_ms if words else LEAD_IN_MS
    landings: List[int] = []
    sources: List[str] = []
    cursor = 0
    for text, anchor in zip(unit_texts, anchors):
        idx = find_landing(words, unit_anchor(text, anchor), cursor) if words else None
        if idx is None:
            landings.append(-1)
            sources.append('PROPORTIONAL')
            continue
        landings.append(max(min(first, LEAD_IN_MS // 2), words[idx].start_ms - _land_before(words, idx)))
        sources.append('WORD')
        cursor = idx + 1
    missing = [i for i, v in enumerate(landings) if v < 0]
    if missing:
        span_start = first
        span_end = voice_ms if voice_ms else max(first, window_ms - EXIT_MS - MIN_HOLD_MS)
        for n, i in enumerate(missing):
            frac = (n + 1) / (len(missing) + 1)
            landings[i] = int(span_start + (span_end - span_start) * frac)
    for i in range(1, len(landings)):
        landings[i] = max(landings[i], landings[i - 1] + 60)
    exit_ms = exit_for_pause(pause_after_ms)
    close = LAND_SETTLE_MS + MIN_HOLD_MS + exit_ms
    budget = max(0.0, min(1.0, (window_ms - max(landings)) / close)) if landings else 1.0
    return BeatClock(beat_id, window_ms, first, voice_ms, list(words), landings, sources, source, True, round(budget, 3), exit_ms, pause_after_ms)


def beat_clock(beat_id: str, unit_texts: List[str], anchors: List[Optional[str]], alignment: Optional[Dict[str, Any]],
               source: str, min_duration_ms: int = 0, energy: float = 0.55) -> BeatClock:
    words = words_from_alignment(alignment) if alignment else []
    voice_ms = max((w.end_ms for w in words), default=0)
    tail = int(TAIL_HOLD_MS + (1 - energy) * 260)
    duration = max(MIN_BEAT_MS, min_duration_ms, LEAD_IN_MS + voice_ms + tail)
    shifted = [Word(w.text, w.start_ms + LEAD_IN_MS, w.end_ms + LEAD_IN_MS) for w in words]

    landings: List[int] = []
    sources: List[str] = []
    cursor = 0
    for text, anchor in zip(unit_texts, anchors):
        idx = find_landing(shifted, unit_anchor(text, anchor), cursor) if shifted else None
        if idx is None:
            landings.append(-1)
            sources.append('PROPORTIONAL')
            continue
        landings.append(max(LEAD_IN_MS, shifted[idx].start_ms - LAND_BEFORE_WORD_MS))
        sources.append('WORD')
        cursor = idx + 1
    # Units without a spoken anchor land at even fractions of the voiced span, in reading order.
    missing = [i for i, v in enumerate(landings) if v < 0]
    if missing:
        span_start = LEAD_IN_MS
        span_end = LEAD_IN_MS + voice_ms if voice_ms else duration - tail
        for n, i in enumerate(missing):
            frac = (n + 1) / (len(missing) + 1)
            landings[i] = int(span_start + (span_end - span_start) * frac)
    # Keep authored order monotonic so a later unit never lands before an earlier one.
    for i in range(1, len(landings)):
        landings[i] = max(landings[i], landings[i - 1] + 140)
    # The beat lasts at least until the last unit has settled, been read and left.
    if landings:
        duration = max(duration, max(landings) + LAND_SETTLE_MS + MIN_HOLD_MS + EXIT_MS + 60)
    # Word cascades land copy on the spoken word, so the last spoken word also needs its settled read.
    if shifted and unit_texts:
        duration = max(duration, shifted[-1].start_ms + CASCADE_SETTLE_MS + MIN_HOLD_MS + EXIT_MS + 120)
    return BeatClock(beat_id, duration, LEAD_IN_MS, voice_ms, shifted, landings, sources, source)


def retime_choreography(events: List[Dict[str, Any]], landings_ms: List[int], duration_ms: int, exit_ms: int = EXIT_MS) -> List[Dict[str, Any]]:
    """Shift each unit's first reveal so its settle meets the word landing.

    Event durations are preserved; only start times move. HOLD/EXIT globals
    are recomputed from the last settled event so the beat always ends in a
    read state followed by one exit window.
    """
    out: List[Dict[str, Any]] = []
    first_seen: Dict[int, int] = {}
    shift_by_unit: Dict[int, int] = {}
    last_end = 0
    exit_start = duration_ms - exit_ms
    for ev in sorted(events, key=lambda e: (e['start_ms'], e['end_ms'])):
        ui = ev.get('unit_index', -1)
        if ev['event'] in ('HOLD', 'EXIT'):
            continue
        length = ev['end_ms'] - ev['start_ms']
        if ui is not None and ui >= 0 and ui < len(landings_ms):
            if ui not in first_seen:
                # settle point (event end) should meet the landing
                target_start = landings_ms[ui] - length
                shift_by_unit[ui] = target_start - ev['start_ms']
                first_seen[ui] = target_start
            start = ev['start_ms'] + shift_by_unit[ui]
        else:
            start = ev['start_ms']
        start = max(LEAD_IN_MS // 2, start)
        end = start + length
        if end > exit_start - 40:
            end = exit_start - 40
            start = max(LEAD_IN_MS // 2, end - length)
        out.append({**ev, 'start_ms': int(start), 'end_ms': int(end)})
        last_end = max(last_end, int(end))
    hold_start = last_end
    hold_end = max(hold_start, exit_start)
    out.append({'unit_index': -1, 'role': 'global', 'event': 'HOLD', 'start_ms': hold_start, 'end_ms': hold_end, 'strength': 0.0, 'note': 'readable_settled_state'})
    out.append({'unit_index': -1, 'role': 'global', 'event': 'EXIT', 'start_ms': exit_start, 'end_ms': duration_ms, 'strength': 0.72, 'note': 'beat_handoff'})
    out.sort(key=lambda e: (e['start_ms'], e['end_ms'], e.get('unit_index', -1)))
    return out
