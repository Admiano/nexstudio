#!/usr/bin/env python3
"""Procedural SFX synthesiser — NexStudio-authored accents, zero rights questions.

What the sound library and the community pool do not cover is the tight, clean
transient vocabulary the benchmark reels use: element-landing pops, tick clicks,
transition whooshes, counter risers and confirm shimmers. Rather than shopping
for licensed one-shots, we synthesise them parametrically — every file is pure
math, generated deterministically, and owned outright.

    python3 tools/synth_sfx.py

Writes WAVs into assets/community/synth/ and registers each in the community
manifest (id synth.<family>.<n>) with license NexStudio-Authored-1.0, sha256
provenance and the semantic tag the compiler binds against. Re-running is
idempotent: same parameters, same bytes.
"""
from __future__ import annotations

import hashlib
import json
import math
import wave
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'assets' / 'community' / 'synth'
MANIFEST = ROOT / 'assets' / 'community' / 'manifest.json'
SR = 48000
LICENSE = 'NexStudio-Authored-1.0'


def _t(dur_s: float) -> np.ndarray:
    return np.arange(int(dur_s * SR)) / SR


def _env_ad(n: int, attack_ms: float, tau_ms: float) -> np.ndarray:
    """Attack in attack_ms, then exponential decay with time constant tau_ms."""
    t = np.arange(n) * 1000.0 / SR
    att = np.minimum(1.0, t / max(attack_ms, 0.1))
    return att * np.exp(-t / max(tau_ms, 0.1))


def _norm(x: np.ndarray, peak: float = 0.92) -> np.ndarray:
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def _wav(path: Path, x: np.ndarray) -> None:
    pcm = np.clip(x, -1.0, 1.0)
    pcm = (pcm * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def pop(f0: float, dur_s: float, seed: int) -> np.ndarray:
    """Percussive plop: a sine chirp falling ~an octave under a fast envelope, plus a 4ms click."""
    t = _t(dur_s)
    phase = 2 * np.pi * f0 * (1.0 - np.exp(-t * 9.0)) * t + 2 * np.pi * (f0 * 0.36) * t
    tone = np.sin(phase)
    click = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t * 400.0)
    return _norm(tone * _env_ad(len(t), 3.0, dur_s * 260.0) + 0.22 * click)


def tick(f0: float, dur_s: float, seed: int) -> np.ndarray:
    """Dry mechanical click: a short sine pip plus a band-limited noise snap."""
    t = _t(dur_s)
    tone = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 260.0)
    noise = np.random.default_rng(seed).standard_normal(len(t))
    # one-pole high-ish pass: difference the noise so it reads as a snap, not hiss
    noise = np.concatenate([[0.0], np.diff(noise)]) * np.exp(-t * 520.0)
    return _norm(tone + 0.5 * noise)


def whoosh(dur_s: float, upward: bool, seed: int) -> np.ndarray:
    """Filtered noise sweep: a one-pole low-pass whose cutoff sweeps across the band."""
    n = int(dur_s * SR)
    noise = np.random.default_rng(seed).standard_normal(n)
    # moving-average low-pass with a sweeping window: window grows -> cutoff falls.
    # 'upward' opens the filter (window shrinks); 'downward' closes it.
    win0, win1 = (220, 4) if upward else (4, 220)
    w = np.linspace(win0, win1, n).astype(int)
    y = np.cumsum(np.concatenate([[0.0], noise]))
    lo = np.maximum(0, np.arange(n + 1) - np.concatenate([w, [w[-1]]]))
    sm = y[np.arange(n) + 1] - y[lo[:n]]
    out = sm / np.maximum(1, np.concatenate([w, [w[-1]]])[:n])
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.6
    return _norm(out * env)


def riser(f0: float, f1: float, dur_s: float, seed: int) -> np.ndarray:
    """Pitch swell: a sine gliding upward plus a fifth above it, crescendo into the cut."""
    t = _t(dur_s)
    sweep = np.sin(2 * np.pi * (f0 + (f1 - f0) * (t / dur_s) ** 1.4) * t)
    fifth = np.sin(2 * np.pi * (f0 * 1.5 + (f1 * 1.5 - f0 * 1.5) * (t / dur_s) ** 1.4) * t) * 0.4
    noise = np.random.default_rng(seed).standard_normal(len(t)) * 0.12
    env = (t / dur_s) ** 1.5 * np.exp(-np.maximum(0, t - dur_s * 0.9) * 40.0)
    return _norm((sweep + fifth + noise) * env)


def shimmer(base: float, dur_s: float, seed: int) -> np.ndarray:
    """Glassy confirm: a few detuned high partials cascading in, each decaying quickly."""
    t = _t(dur_s)
    out = np.zeros(len(t))
    for i, (mult, lag, tau) in enumerate(((1.0, 0.0, 55.0), (1.49, 0.05, 42.0), (2.24, 0.1, 34.0), (3.36, 0.16, 26.0))):
        tt = np.maximum(0.0, t - lag)
        out += np.sin(2 * np.pi * base * mult * tt) * np.exp(-tt * 1000.0 / tau) * (t >= lag) / (i + 1)
    return _norm(out)


# (file slug, semantic tag, synth recipe) — params are the contract: same table, same bytes.
SPEC: List[Tuple[str, str, Callable[[], np.ndarray]]] = [
    ('pop-01', 'synth.pop', lambda: pop(520.0, 0.11, 101)),
    ('pop-02', 'synth.pop', lambda: pop(640.0, 0.09, 102)),
    ('pop-03', 'synth.pop', lambda: pop(430.0, 0.13, 103)),
    ('pop-04', 'synth.pop', lambda: pop(760.0, 0.08, 104)),
    ('tick-01', 'synth.tick', lambda: tick(1900.0, 0.05, 111)),
    ('tick-02', 'synth.tick', lambda: tick(2400.0, 0.04, 112)),
    ('tick-03', 'synth.tick', lambda: tick(1500.0, 0.06, 113)),
    ('whoosh-01', 'synth.whoosh', lambda: whoosh(0.42, True, 121)),
    ('whoosh-02', 'synth.whoosh', lambda: whoosh(0.55, True, 122)),
    ('whoosh-03', 'synth.whoosh', lambda: whoosh(0.34, False, 123)),
    ('whoosh-04', 'synth.whoosh', lambda: whoosh(0.62, False, 124)),
    ('riser-01', 'synth.riser', lambda: riser(240.0, 1500.0, 0.7, 131)),
    ('riser-02', 'synth.riser', lambda: riser(320.0, 1900.0, 0.55, 132)),
    ('riser-03', 'synth.riser', lambda: riser(180.0, 1100.0, 0.85, 133)),
    ('shimmer-01', 'synth.shimmer', lambda: shimmer(1560.0, 0.55, 141)),
    ('shimmer-02', 'synth.shimmer', lambda: shimmer(1980.0, 0.45, 142)),
    ('shimmer-03', 'synth.shimmer', lambda: shimmer(1240.0, 0.7, 143)),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    manifest['assets'] = [a for a in manifest['assets'] if not str(a.get('id', '')).startswith('synth.')]
    for slug, tag, make in SPEC:
        path = OUT_DIR / f'{slug}.wav'
        _wav(path, make())
        data = path.read_bytes()
        manifest['assets'].append({
            'id': f'synth.{tag.split(".")[1]}.{slug.rsplit("-", 1)[1]}',
            'kind': 'sfx',
            'semantic_tag': tag,
            'family': 'synth',
            'path': f'assets/community/synth/{slug}.wav',
            'duration_s': round((len(data) - 44) / 2 / SR, 3),
            'license': LICENSE,
            'source': {'pack': 'NexStudio procedural SFX', 'url': 'tools/synth_sfx.py'},
            'sha256': hashlib.sha256(data).hexdigest(),
        })
    manifest['count'] = len(manifest['assets'])
    MANIFEST.write_text(json.dumps(manifest, indent=1) + '\n')
    print(f'{len(SPEC)} synth accents -> {OUT_DIR}')


if __name__ == '__main__':
    main()
