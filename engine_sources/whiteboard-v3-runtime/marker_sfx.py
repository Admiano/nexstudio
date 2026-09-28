"""Felt-tip marker foley, synthesized per pen-down stroke.

Every stroke the pen inks becomes one sound event timed to its exact
pen-down window. The timbre models a felt nib dragging over paper: broadband
pink-tilted friction noise with smooth shelves and no spectral peak (so no
pitch or whistle), irregular Poisson micro-catches for the paper tooth, slow
hand-pressure drift, a soft touch-down and a quick release on lift. Stroke
speed drives loudness, brightness and grit density.
Deterministic (seeded) and license-clean: no sampled audio.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

RATE = 48000


def _shaped_noise(n: int, lp_hz: float, rnd: np.random.Generator,
                  hp_hz: float = 220.0) -> np.ndarray:
    """Broadband friction noise with no spectral peak: a gentle pink tilt
    (-3 dB/oct) between smooth shelves, so nothing in it reads as a pitch."""
    m = 1 << max(8, int(np.ceil(np.log2(n + 1))))
    spec = np.fft.rfft(rnd.standard_normal(m))
    f = np.maximum(np.fft.rfftfreq(m, 1 / RATE), 1.0)
    tilt = (1000.0 / f) ** 0.5
    hp = 1 / np.sqrt(1 + (hp_hz / f) ** 4)
    lp = 1 / np.sqrt(1 + (f / lp_hz) ** 4)
    x = np.fft.irfft(spec * tilt * hp * lp, m)[:n]
    return x / max(1e-9, np.sqrt((x ** 2).mean()))


def _drift(n: int, rnd: np.random.Generator, hz: float) -> np.ndarray:
    """Smooth random level drift below ~hz — hand pressure, not a buzz."""
    k = max(2, int(n / RATE * hz) + 2)
    pts = np.cumsum(rnd.standard_normal(k)) * 0.35
    pts -= pts.mean()
    x = np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)
    return np.clip(x, -0.9, 0.9)


def _tooth(n: int, rate_hz: float, rnd: np.random.Generator) -> np.ndarray:
    """Paper tooth: irregular (Poisson) micro-catches of the felt fibres,
    each a ~1 ms decaying noise tick. Aperiodic, so no pitch forms."""
    out = np.zeros(n)
    k = rnd.poisson(max(0.0, rate_hz) * n / RATE)
    if k == 0:
        return out
    w = int(RATE * 0.0012)
    env = np.exp(-np.arange(w) / (w / 4))
    for p in rnd.integers(0, max(1, n - w), k):
        out[p:p + w] += env * rnd.standard_normal(w) * rnd.uniform(0.3, 1.0)
    return out


def stroke(dur: float, speed: float, rnd: np.random.Generator) -> np.ndarray:
    """One pen-down interval. speed in board px/s (≈ 0-3000)."""
    n = max(int(RATE * 0.03), int(RATE * dur))
    s = float(np.clip(speed / 900.0, 0.15, 2.2))
    # faster drag = brighter and denser fibre catches, never a moving tone
    lp_hz = 2600 + 1800 * min(s, 1.6) + rnd.uniform(-200, 200)
    body = _shaped_noise(n, lp_hz, rnd)
    grit = _tooth(n, 260 + 520 * min(s, 1.6), rnd)
    g_rms = np.sqrt((grit ** 2).mean())
    if g_rms > 0:
        grit = np.convolve(grit, [0.5, 0.35, 0.15], 'same') / g_rms
    x = body + 0.35 * grit
    t = np.arange(n) / RATE
    att = np.minimum(1, t / 0.008) ** 1.5
    rel = np.minimum(1, (n / RATE - t) / 0.025)
    # pressure: nib bites on contact, eases mid-stroke, wanders with the hand
    press = (0.85 + 0.15 * np.exp(-t / 0.06)) * (1 + 0.25 * _drift(n, rnd, 6))
    level = 0.5 * s ** 0.5
    y = x * press * att * rel * level
    tap = int(RATE * 0.005)
    if n > tap:
        y[:tap] += 0.35 * level * np.hanning(tap * 2)[:tap] * _shaped_noise(
            tap, 1500, rnd, hp_hz=120)
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
