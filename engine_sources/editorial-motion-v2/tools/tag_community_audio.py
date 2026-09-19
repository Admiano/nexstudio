#!/usr/bin/env python3
"""Tag the community audio pool so the compiler can bind it semantically.

Two jobs, one manifest:

1. sfx/wooshes: the vendored CC0 organic-whoosh pack was unreachably stored —
   no semantic_tag and community-relative paths, which `_merge_community_foley`
   cannot resolve (it joins engine-root-relative paths). Give each file the
   `motion.ui.whoosh` tag, a real duration and the engine-relative path so it
   becomes selectable for WIPE_SWEEP / TRANSITION_SWEEP accents.

2. music beds: measure duration, estimate tempo by onset-envelope autocorrelation
   and attach a curated mood list, so `bind_film_music` can honour a film `mood`
   and prefer beds that cover the cut without looping.

    python3 tools/tag_community_audio.py

Requires ffmpeg/ffprobe on PATH. Idempotent.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import wave
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'assets' / 'community' / 'manifest.json'

# Curated mood per music asset id — subjective fit, bounded by FILM_MOODS in contracts.py.
MOODS: Dict[str, List[str]] = {
    'music.adding-the-sun': ['uplifting', 'bright'],
    'music.bass-meant-jazz': ['jazzy', 'calm'],
    'music.flutey-jazz': ['jazzy', 'bright'],
    'music.happy-whistling-ukulele': ['playful', 'bright'],
    'music.hopeful': ['uplifting'],
    'music.landras-dream': ['dreamy', 'calm'],
    'music.nordic-wist': ['wistful'],
    'music.study-and-relax': ['calm', 'dreamy'],
    'music.sunday-dub': ['calm', 'playful'],
    'music.ukulele-song': ['playful', 'uplifting'],
}


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), 'rb') as w:
        return w.getnframes() / w.getframerate()


def _ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)])
    return float(out.decode().strip())


def _decode_mono(path: Path, sr: int = 22050) -> np.ndarray:
    raw = subprocess.check_output(
        ['ffmpeg', '-v', 'quiet', '-i', str(path), '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
        stderr=subprocess.DEVNULL)
    return np.frombuffer(raw, dtype='<f4')


def _estimate_bpm(path: Path, sr: int = 22050) -> Optional[int]:
    """Onset-envelope autocorrelation: peak lag in the 50–200 BPM band."""
    x = _decode_mono(path, sr)
    if len(x) < sr * 10:
        return None
    hop = 512
    n = len(x) // hop
    env = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    onset = np.maximum(0.0, np.diff(env))
    onset -= onset.mean()
    lags = np.arange(int(sr / hop / 200 * 60), int(sr / hop / 50 * 60))
    corr = np.array([np.dot(onset[:-l or None], onset[l:]) if l else onset.var() * len(onset) for l in lags])
    best = lags[int(np.argmax(corr))]
    bpm = 60.0 * sr / hop / best
    while bpm < 50:
        bpm *= 2
    while bpm > 200:
        bpm /= 2
    return int(round(bpm))


def main() -> None:
    m = json.loads(MANIFEST.read_text())
    wooshes = music = 0
    for a in m['assets']:
        p = ROOT / 'assets' / 'community' / a['path']
        if 'wooshes-organic' in a['path']:
            rel = a['path'] if a['path'].startswith('assets/community/') else f'assets/community/{a["path"]}'
            a['path'] = rel
            a['semantic_tag'] = 'motion.ui.whoosh'
            a['family'] = 'motion'
            a['duration_s'] = round(_wav_duration(ROOT / rel), 3)
            wooshes += 1
        elif a.get('kind') == 'music' and p.exists():
            a['duration_s'] = round(_ffprobe_duration(p), 3)
            bpm = _estimate_bpm(p)
            if bpm:
                a['bpm'] = bpm
            if a['id'] in MOODS:
                a['moods'] = MOODS[a['id']]
            music += 1
    MANIFEST.write_text(json.dumps(m, indent=1) + '\n')
    print(f'tagged {wooshes} wooshes, enriched {music} music beds')


if __name__ == '__main__':
    main()
