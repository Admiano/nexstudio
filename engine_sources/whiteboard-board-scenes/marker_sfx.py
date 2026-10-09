"""Felt-tip marker foley from real recordings, one event per pen-down stroke.

Every stroke the pen inks becomes one sound event timed to its exact
pen-down window. The sound is played from a grain bank cut from real
marker-on-paper recordings (assets/sfx/marker-grains-48k.wav, built by
tools/marker_grains_pack.py from CC0 / public-domain sources): long strokes
play marker-line takes, short strokes (lettering, ticks) play felt-pen
handwriting takes starting at their nib contact. Grains are chained with
equal-power crossfades, never pitch-shifted; stroke speed only scales level
and brightness. Deterministic for a given seed.
"""
from __future__ import annotations

import json
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np

RATE = 48000
_SFX = Path(__file__).resolve().parent / 'assets' / 'sfx'
_XF = int(0.015 * RATE)
_ATTACK = int(0.005 * RATE)
_RELEASE = int(0.02 * RATE)


@lru_cache(maxsize=1)
def _bank():
    with wave.open(str(_SFX / 'marker-grains-48k.wav')) as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()),
                            np.int16).astype(np.float64) / 32768
    idx = json.loads((_SFX / 'marker-grains.json').read_text())['grains']
    pools: dict[str, list[np.ndarray]] = {}
    for g in idx:
        pools.setdefault(g['pool'], []).append(pcm[g['start']:g['end']])
    return pools


def _pool(dur: float) -> list[np.ndarray]:
    pools = _bank()
    want = 'long' if dur >= 0.6 else 'short'
    return pools.get(want) or next(iter(pools.values()))


def _lowpass(x: np.ndarray, hz: float) -> np.ndarray:
    k = np.exp(-2 * np.pi * hz / RATE)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - k) * v + k * acc
        y[i] = acc
    return y


def stroke(dur: float, speed: float, rnd: np.random.Generator) -> np.ndarray:
    """dur seconds of recorded marker drag; speed in px/s."""
    n = max(1, int(dur * RATE))
    pool = _pool(dur)
    out = np.zeros(0)
    first = True
    while len(out) < n + _RELEASE:
        g = pool[int(rnd.integers(len(pool)))]
        need = n + _RELEASE - len(out) + _XF
        if first and dur < 0.6:
            off = 0
        else:
            off = int(rnd.integers(max(1, len(g) - min(len(g), need))))
        seg = g[off:off + need]
        if len(out) and len(seg) > _XF and len(out) > _XF:
            t = np.linspace(0, np.pi / 2, _XF)
            seg = seg.copy()
            seg[:_XF] = out[-_XF:] * np.cos(t) + seg[:_XF] * np.sin(t)
            out = np.concatenate([out[:-_XF], seg])
        else:
            out = np.concatenate([out, seg])
        first = False
    y = out[:n + _RELEASE].copy()
    sp = float(np.clip(speed / 1200.0, 0.0, 1.0))
    if sp < 0.6:
        w = 0.5 * (0.6 - sp) / 0.6
        y = (1 - w) * y + w * _lowpass(y, 3200.0)
    env = np.ones(len(y))
    a = min(_ATTACK, n // 2)
    env[:a] = np.linspace(0, 1, a) if a else env[:a]
    env[n:] = np.cos(np.linspace(0, np.pi / 2, len(y) - n)) ** 2
    return y * env * (0.75 + 0.25 * sp)


def _cap(path: Path) -> np.ndarray | None:
    if not path.is_file():
        return None
    with wave.open(str(path)) as w:
        if w.getframerate() != RATE or w.getsampwidth() != 2:
            return None
        return np.frombuffer(w.readframes(w.getnframes()),
                             np.int16).astype(np.float32) / 32768


def render(events: list[dict], duration: float, out_path: Path,
           cap_wav: Path | None = None, seed: int = 0) -> dict:
    """events: {'start','duration','length'(px, optional),'gain'} pen spans,
    plus {'role':'cap','start'} punctuation."""
    n = max(1, int(np.ceil(duration * RATE)))
    mix = np.zeros(n, np.float64)
    cap = _cap(cap_wav) if cap_wav else None
    for i, ev in enumerate(events):
        a = max(0, int(float(ev['start']) * RATE))
        if a >= n:
            continue
        rnd = np.random.default_rng((seed * 1_000_003 + i) & 0xFFFFFFFF)
        if ev.get('role') == 'cap':
            if cap is None:
                continue
            seg = cap[int(RATE * float(ev.get('offset', 0))):][
                :int(RATE * float(ev.get('duration', .24)))]
            y = seg * float(ev.get('gain', .3))
        else:
            d = max(0.03, float(ev['duration']))
            length = ev.get('length')
            speed = (float(length) / d) if length else 700.0
            y = stroke(d, speed, rnd) * float(ev.get('gain', 1.0))
        b = min(n, a + len(y))
        mix[a:b] += y[:b - a]
    peak = float(np.abs(mix).max()) or 1.0
    scale = min(1.0, 0.7 / peak)
    pcm = np.clip(mix * scale, -1, 1)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((pcm * 32767).astype(np.int16).tobytes())
    return {'path': str(out_path), 'eventCount': len(events),
            'peakBeforeLimit': round(peak, 6), 'limiterScale': round(scale, 6)}
