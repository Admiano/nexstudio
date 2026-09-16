"""One continuous voice track is the clock for the whole film.

The MASTER voice source takes a single audio file plus one word (or
ElevenLabs character) alignment for the entire script. Each authored beat's
narration is located inside that word stream; beat boundaries are then placed
inside the speaker's own pauses. The audio is never cut, stretched or
re-spaced: beats live where the speech lives, and a beat whose window cannot
carry its choreography is reported through the gate instead of padded.
"""
from __future__ import annotations

import difflib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .contracts import BeatTreatment, TreatmentError
from .timing import LEAD_IN_MS, Word, normalise, words_from_alignment

MATCH_FLOOR = 0.82        # sequence ratio below which a beat's narration is not in the audio
OUTGOING_SHARE = 0.65     # share of a boundary pause given to the outgoing beat's hold


@dataclass
class BeatWindow:
    beat_id: str
    start_ms: int                 # cut in (film time)
    end_ms: int                   # cut out (film time)
    speech_start_ms: int          # first word (film time); -1 when silent
    speech_end_ms: int            # last word end (film time); -1 when silent
    pause_before_ms: int
    pause_after_ms: int
    words: List[Word]             # film time
    match_ratio: float

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def local_words(self) -> List[Word]:
        return [Word(w.text, w.start_ms - self.start_ms, w.end_ms - self.start_ms) for w in self.words]


@dataclass
class MasterTimeline:
    audio_path: str
    audio_ms: int
    head_pad_ms: int
    tail_silence_ms: int
    film_ms: int
    words: List[Word]
    windows: List[BeatWindow]
    tempo: Dict[str, float]


def load_master_words(alignment: Dict[str, Any]) -> List[Word]:
    """Accept the ElevenLabs character shape or a plain ``{"words": [{text,start_ms,end_ms}]}`` word list."""
    if 'characters' in alignment:
        return words_from_alignment(alignment)
    words = alignment.get('words')
    if not isinstance(words, list) or not words:
        raise TreatmentError('MASTER_ALIGNMENT_SHAPE', 'master alignment needs characters[] or words[]')
    out = [Word(str(w['text']), int(w['start_ms']), int(w['end_ms'])) for w in words]
    out = [w for w in out if normalise(w.text)]
    for a, b in zip(out, out[1:]):
        if b.start_ms < a.start_ms:
            raise TreatmentError('MASTER_ALIGNMENT_NOT_MONOTONIC', f'{a.text!r} -> {b.text!r}')
    return out


def audio_duration_ms(path: Path) -> int:
    if not shutil.which('ffprobe'):
        raise TreatmentError('FFPROBE_MISSING', 'ffprobe is required to read the master audio duration')
    cp = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
                        capture_output=True, text=True)
    if cp.returncode != 0 or not cp.stdout.strip():
        raise TreatmentError('MASTER_AUDIO_UNREADABLE', str(path))
    return int(round(float(cp.stdout.strip()) * 1000))


def locate(narration: str, keys: List[str], cursor: int) -> Tuple[int, int, float]:
    """Best contiguous window of master tokens for this narration, at or after ``cursor``.

    Returns (start_index, end_index_exclusive, ratio). Windows are tried at the
    narration's token count ±25% so dropped or merged tokens still match.
    """
    tokens = [normalise(t) for t in narration.split()]
    tokens = [t for t in tokens if t]
    n = len(tokens)
    if n == 0:
        return cursor, cursor, 1.0
    best = (cursor, cursor, 0.0)
    slack = max(1, n // 4)
    for length in range(max(1, n - slack), n + slack + 1):
        for i in range(cursor, len(keys) - length + 1):
            ratio = difflib.SequenceMatcher(None, tokens, keys[i:i + length], autojunk=False).ratio()
            if ratio > best[2] + 1e-9:
                best = (i, i + length, ratio)
            if ratio >= 0.999:
                break
        if best[2] >= 0.999:
            break
    return best


def resolve_master(beats: List[BeatTreatment], voice_cfg: Dict[str, Any], base_dir: Path) -> MasterTimeline:
    audio = (base_dir / str(voice_cfg.get('audio_path') or '')).resolve()
    al_path = (base_dir / str(voice_cfg.get('alignment_path') or '')).resolve()
    if not voice_cfg.get('audio_path') or not audio.exists():
        raise TreatmentError('MASTER_AUDIO_MISSING', str(audio))
    if not voice_cfg.get('alignment_path') or not al_path.exists():
        raise TreatmentError('MASTER_ALIGNMENT_MISSING', str(al_path))
    head_pad = int(voice_cfg.get('head_pad_ms') or 0)
    if head_pad < 0:
        raise TreatmentError('MASTER_HEAD_PAD_NEGATIVE', str(head_pad))
    audio_ms = audio_duration_ms(audio)
    raw = json.loads(al_path.read_text())
    words = [Word(w.text, w.start_ms + head_pad, w.end_ms + head_pad) for w in load_master_words(raw.get('alignment', raw))]
    keys = [w.key for w in words]

    spoken = [b for b in beats if b.narration]
    silent_tail = [b for b in beats if not b.narration]
    for b in beats[:len(beats) - len(silent_tail)]:
        if not b.narration:
            raise TreatmentError('MASTER_SILENT_BEAT_MUST_BE_LAST', 'a beat without narration can only close a MASTER film', b.beat_id)

    spans: List[Tuple[int, int, float]] = []
    cursor = 0
    for b in spoken:
        s, e, ratio = locate(b.narration, keys, cursor)
        if ratio < MATCH_FLOOR or e <= s:
            raise TreatmentError('MASTER_NARRATION_NOT_FOUND', f'ratio {ratio:.2f} for narration {b.narration!r}', b.beat_id)
        spans.append((s, e, ratio))
        cursor = e
    if spans and spans[-1][1] < len(words):
        unclaimed = ' '.join(w.text for w in words[spans[-1][1]:])
        raise TreatmentError('MASTER_AUDIO_UNCLAIMED_WORDS', f'no beat narrates the tail: {unclaimed!r}')
    if spans and spans[0][0] > 0:
        unclaimed = ' '.join(w.text for w in words[:spans[0][0]])
        raise TreatmentError('MASTER_AUDIO_UNCLAIMED_WORDS', f'no beat narrates the head: {unclaimed!r}')

    windows: List[BeatWindow] = []
    for k, (b, (s, e, ratio)) in enumerate(zip(spoken, spans)):
        ws = words[s:e]
        speech_start, speech_end = ws[0].start_ms, ws[-1].end_ms
        prev_end = words[spans[k - 1][1] - 1].end_ms if k > 0 else 0
        next_start = words[spans[k + 1][0]].start_ms if k + 1 < len(spans) else None
        pause_before = speech_start - prev_end
        pause_after = (next_start - speech_end) if next_start is not None else (head_pad + audio_ms - speech_end)
        windows.append(BeatWindow(b.beat_id, 0, 0, speech_start, speech_end, pause_before, pause_after, ws, round(ratio, 3)))

    # Cuts live inside the speaker's pauses: the outgoing beat keeps most of the pause as its hold,
    # the incoming beat gets a lead-in no longer than the stage-settle budget.
    for k, w in enumerate(windows):
        if k == 0:
            w.start_ms = 0
        else:
            prev = windows[k - 1]
            pause = w.speech_start_ms - prev.speech_end_ms
            lead = min(LEAD_IN_MS, int(pause * (1 - OUTGOING_SHARE)))
            cut = w.speech_start_ms - lead
            prev.end_ms = cut
            w.start_ms = cut
    film_ms = head_pad + audio_ms
    if windows:
        windows[-1].end_ms = film_ms
    tail = 0
    for b in silent_tail:
        d = max(0, b.min_duration_ms)
        windows.append(BeatWindow(b.beat_id, film_ms + tail, film_ms + tail + d, -1, -1, 0, 0, [], 1.0))
        tail += d

    gaps = [b.start_ms - a.end_ms for a, b in zip(words, words[1:])]
    spoken_ms = max(1, words[-1].end_ms - words[0].start_ms) if words else 1
    tempo = {
        'words_per_second': round(len(words) * 1000 / spoken_ms, 3),
        'median_word_gap_ms': float(sorted(gaps)[len(gaps) // 2]) if gaps else 0.0,
        'p90_pause_ms': float(sorted(gaps)[int(len(gaps) * 0.9)]) if gaps else 0.0,
        'spoken_ms': spoken_ms,
    }
    return MasterTimeline(str(audio), audio_ms, head_pad, tail, film_ms + tail, words, windows, tempo)


def extend_tail(tl: MasterTimeline, extra_ms: int) -> None:
    """Give the last spoken beat a readable close by appending silence (the audio itself is untouched)."""
    if extra_ms <= 0:
        return
    last_spoken: Optional[BeatWindow] = next((w for w in reversed(tl.windows) if w.speech_start_ms >= 0), None)
    if last_spoken is None:
        return
    last_spoken.end_ms += extra_ms
    after = False
    for w in tl.windows:
        if after:
            w.start_ms += extra_ms
            w.end_ms += extra_ms
        if w is last_spoken:
            after = True
    tl.tail_silence_ms += extra_ms
    tl.film_ms += extra_ms
