"""Felt-tip marker foley, synthesized per pen-down stroke.

Every stroke the pen inks becomes one sound event timed to its exact
pen-down window. The timbre models a felt nib dragging over paper: broadband
friction noise shaped to a soft 1-4 kHz body (no tonal squeal, steep roll-off
above ~6 kHz), grain from nib fibres (slow random amplitude flutter), a soft
touch-down at pen contact, and a quick release on lift. Stroke speed drives
loudness and brightness, so long sweeps hiss and letters tick.
Deterministic (seeded) and license-clean: no sampled audio.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

RATE = 48000


def _shaped_noise(n: int, fc: float, rnd: np.random.Generator) -> np.ndarray:
    m = 1 << max(8, int(np.ceil(np.log2(n + 1))))
    spec = np.fft.rfft(rnd.standard_normal(m))
    f = np.fft.rfftfreq(m, 1 / RATE)
    body = np.exp(-0.5 * (np.log(np.maximum(f, 1) / fc) / 0.55) ** 2)
    low = 0.22 * np.exp(-0.5 * (np.log(np.maximum(f, 1) / 420) / 0.5) ** 2)
    hp = 1 / (1 + (160 / np.maximum(f, 1)) ** 4)
    lp = 1 / (1 + (f / 6000) ** 6)
    x = np.fft.irfft(spec * (body + low) * hp * lp, m)[:n]
    return x / max(1e-9, np.sqrt((x ** 2).mean()))


def _flutter(n: int, rnd: np.random.Generator, hz: float = 28.0) -> np.ndarray:
    k = max(2, int(n / RATE * hz) + 2)
    pts = rnd.standard_normal(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)


def stroke(dur: float, speed: float, rnd: np.random.Generator) -> np.ndarray:
    """One pen-down interval. speed in board px/s (≈ 0-3000)."""
    n = max(int(RATE * 0.03), int(RATE * dur))
    s = float(np.clip(speed / 900.0, 0.15, 2.2))
    fc = 1500 + 900 * min(s, 1.6)
    x = _shaped_noise(n, fc, rnd)
    grain = 1 + 0.32 * _flutter(n, rnd) + 0.12 * _flutter(n, rnd, 90)
    t = np.arange(n) / RATE
    att = np.minimum(1, t / 0.006)
    rel = np.minimum(1, (n / RATE - t) / 0.022)
    # pressure: nib bites on contact, eases mid-stroke, lightens on lift
    press = 0.82 + 0.18 * np.exp(-t / 0.05)
    level = 0.55 * s ** 0.55
    y = x * np.clip(grain, 0.2, None) * att * rel * press * level
    tap = int(RATE * 0.004)
    if n > tap:
        y[:tap] += 0.5 * level * np.hanning(tap * 2)[:tap] * _shaped_noise(
            tap, 700, rnd)
    return y


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
