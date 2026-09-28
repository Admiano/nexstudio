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


def click(f0: float, dur_s: float, seed: int) -> np.ndarray:
    """Glossy tile click: a very short high resonance over a 2ms noise burst — the transient a lacquered
    square makes landing on a desk."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    ring = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 900.0) + 0.35 * np.sin(2 * np.pi * f0 * 2.7 * t) * np.exp(-t * 1600.0)
    burst = rng.standard_normal(len(t)) * np.exp(-t * 2500.0)
    burst = np.concatenate([[0.0], np.diff(burst)])
    return _norm(ring + 0.6 * burst)


def thock(f0: float, dur_s: float, seed: int) -> np.ndarray:
    """Soft thock: a low, damped sine knock with a felt-like noise puff — a padded chip settling."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    knock = np.sin(2 * np.pi * f0 * (1.0 - 0.25 * (1.0 - np.exp(-t * 40.0))) * t) * np.exp(-t * 60.0)
    puff = rng.standard_normal(len(t))
    puff = np.convolve(puff, np.ones(24) / 24.0, mode='same') * np.exp(-t * 180.0)
    return _norm(knock * _env_ad(len(t), 2.0, dur_s * 220.0) + 0.3 * puff)


def swish(dur_s: float, seed: int) -> np.ndarray:
    """Stroke swish: a short band-passed noise arc, brighter in the middle — a line drawn fast."""
    n = int(dur_s * SR)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    # band-pass by subtracting a wide moving average from a narrow one
    narrow = np.convolve(noise, np.ones(6) / 6.0, mode='same')
    wide = np.convolve(noise, np.ones(60) / 60.0, mode='same')
    env = np.sin(np.linspace(0, np.pi, n)) ** 2.2
    return _norm((narrow - wide) * env)


# ---------------------------------------------------------------------------
# Craft foley + ambience — the paper-film's own vocabulary. Not UI sounds:
# the sound a thing makes (rain falls, water plips, a sprout sproings, a page
# turns) and the air a scene stands in (crickets at night, birds at dawn).
# ---------------------------------------------------------------------------

def _noise(n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal(n)


def _smooth(x: np.ndarray, w: int) -> np.ndarray:
    return np.convolve(x, np.ones(w) / w, mode='same')


def _hipass(x: np.ndarray) -> np.ndarray:
    return np.concatenate([[0.0], np.diff(x)])


def paper_rustle(dur_s: float, seed: int) -> np.ndarray:
    """Paper crinkle: high-passed noise driven through a jittery amplitude gate —
    a handful of micro-folds, not one rub."""
    n = int(dur_s * SR)
    rng = np.random.default_rng(seed)
    noise = _hipass(_hipass(_noise(n, seed)))
    gate = np.zeros(n)
    for _ in range(int(dur_s * 26) + 3):
        w = int(rng.uniform(120, 700))
        c = int(rng.uniform(w, n))
        gate[c - w:c] += rng.uniform(0.3, 1.0) * np.linspace(1.0, 0.0, w)
    gate = _smooth(np.clip(gate, 0, 1.6), 180)
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.9
    return _norm(noise * gate * env)


def paper_tap(dur_s: float, seed: int) -> np.ndarray:
    """A paper card settling onto the stage: a dull slap (lowpassed noise burst)
    with a felt knock under it — matte, never plasticky."""
    t = _t(dur_s)
    slap = _smooth(_noise(len(t), seed), 60) * np.exp(-t * 300.0)
    knock = np.sin(2 * np.pi * 210.0 * t) * np.exp(-t * 120.0) * 0.5
    crinkle = _hipass(_noise(len(t), seed + 7)) * np.exp(-t * 900.0) * 0.35
    return _norm(slap * _env_ad(len(t), 0.6, dur_s * 180.0) + knock + crinkle)


def paper_page(dur_s: float, seed: int) -> np.ndarray:
    """A page being lifted across: a slow band sweep of noise with a paper flutter
    riding on it — the transition sound, not a whoosh."""
    n = int(dur_s * SR)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    w = np.linspace(26, 240, n).astype(int)  # closing filter = the page settles
    y = np.cumsum(np.concatenate([[0.0], noise]))
    lo = np.maximum(0, np.arange(n + 1) - np.concatenate([w, [w[-1]]]))
    sm = y[np.arange(n) + 1] - y[lo[:n]]
    out = sm / np.maximum(1, np.concatenate([w, [w[-1]]])[:n])
    flutter = _hipass(_noise(n, seed + 3)) * (0.35 + 0.65 * (np.sin(np.linspace(0, np.pi * 3, n)) ** 2))
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.3
    return _norm(out * env + 0.35 * flutter * env)


def paper_tear(dur_s: float, seed: int) -> np.ndarray:
    """A controlled rip: staccato noise fibres pulling apart down a closing filter."""
    n = int(dur_s * SR)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    win = np.linspace(12, 200, n).astype(int)
    y = np.cumsum(np.concatenate([[0.0], noise]))
    lo = np.maximum(0, np.arange(n + 1) - np.concatenate([win, [win[-1]]]))
    sm = (y[np.arange(n) + 1] - y[lo[:n]]) / np.maximum(1, win[:n])
    tear_gate = np.clip(0.25 + np.abs(_hipass(_smooth(_noise(n, seed + 11), 400))) * 8.0, 0, 1.4)
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.1
    return _norm(sm * tear_gate * env)


def amb_rain(dur_s: float, seed: int) -> np.ndarray:
    """Rainfall loop: soft lowpassed wash plus sparse droplet ticks — reads at -28dB."""
    n = int(dur_s * SR)
    rng = np.random.default_rng(seed)
    wash = _smooth(_noise(n, seed), 240)
    drops = np.zeros(n)
    for _ in range(int(dur_s * 34)):
        c = int(rng.uniform(0, n - 300))
        f = rng.uniform(900, 2600)
        tt = np.arange(300) / SR
        drops[c:c + 300] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 220.0) * rng.uniform(0.15, 0.5)
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.5
    return _norm((wash * 0.8 + drops * 0.4) * env)


def amb_wind(dur_s: float, seed: int) -> np.ndarray:
    """Wind loop: brown noise breathing through a slow LFO — low, open air."""
    n = int(dur_s * SR)
    t = _t(dur_s)
    brown = np.cumsum(_noise(n, seed))
    brown = _smooth(brown, 400)
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.4 * t + seed) * np.sin(2 * np.pi * 0.13 * t + seed * 0.7)
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.5
    return _norm(brown * lfo * env)


def amb_water(dur_s: float, seed: int) -> np.ndarray:
    """Lapping water loop: band-limited noise swelling in slow waves plus a wandering
    low gurgle — the sea / a riverbank, not a tap."""
    n = int(dur_s * SR)
    t = _t(dur_s)
    lap = _smooth(_noise(n, seed), 300) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t + 1.0))
    gurgle_f = 300 + 140 * np.sin(2 * np.pi * 0.23 * t + seed)
    gurgle = np.sin(2 * np.pi * np.cumsum(gurgle_f) / SR) * _smooth(np.abs(_noise(n, seed + 5)), 500) * 3.0
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.5
    return _norm((lap * 0.7 + gurgle * 0.5) * env)


def amb_birds(dur_s: float, seed: int) -> np.ndarray:
    """Sparse morning birdsong: short FM chirps at random onsets over a faint air bed —
    dawn and open field, kept light enough to sit under voice."""
    n = int(dur_s * SR)
    rng = np.random.default_rng(seed)
    out = _smooth(_noise(n, seed), 800) * 0.05
    for _ in range(int(dur_s * 7) + 2):
        c = int(rng.uniform(0, n - 2200))
        f0 = rng.uniform(2400, 4200)
        chirps = rng.integers(1, 4)
        for k in range(chirps):
            cc = c + k * rng.integers(300, 700)
            if cc + 260 >= n:
                break
            tt = np.arange(260) / SR
            fm = np.sin(2 * np.pi * (f0 + rng.uniform(-400, 900) * tt / 0.005) * tt)
            out[cc:cc + 260] += fm * np.exp(-tt * 30.0) * rng.uniform(0.25, 0.6)
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.5
    return _norm(out * env)


def amb_crickets(dur_s: float, seed: int) -> np.ndarray:
    """Night crickets loop: two detuned pulse trains at cricket rate over a low dark bed."""
    n = int(dur_s * SR)
    t = _t(dur_s)
    bed = _smooth(_noise(n, seed), 900) * 0.08
    out = np.copy(bed)
    for f0, rate, ph in ((4300.0, 13.0, 0.0), (4700.0, 11.0, 0.6)):
        pulses = np.maximum(0.0, np.sin(2 * np.pi * rate * t + ph)) ** 8
        out += np.sin(2 * np.pi * f0 * t) * pulses * 0.3
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.5
    return _norm(out * env)


def amb_fire(dur_s: float, seed: int) -> np.ndarray:
    """Fire crackle loop: a low hiss bed with random pops of varying size."""
    n = int(dur_s * SR)
    rng = np.random.default_rng(seed)
    hiss = _smooth(_noise(n, seed), 120) * 0.3
    pops = np.zeros(n)
    for _ in range(int(dur_s * 22)):
        c = int(rng.uniform(0, n - 600))
        w = int(rng.uniform(80, 500))
        pops[c:c + w] += _noise(w, seed + c) * np.exp(-np.arange(w) / (w * 0.3)) * rng.uniform(0.2, 1.0)
    env = np.sin(np.linspace(0, np.pi, n)) ** 0.5
    return _norm((hiss + pops * 0.7) * env)


def foley_drop(dur_s: float, seed: int) -> np.ndarray:
    """Water plip: a rising sine chirp into a tiny noise splash."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    chirp = np.sin(2 * np.pi * (700 + 900 * t / dur_s) * t) * np.exp(-t * 25.0)
    splash = _hipass(rng.standard_normal(len(t))) * np.exp(-t * 160.0) * 0.4
    return _norm(chirp * _env_ad(len(t), 4.0, dur_s * 200.0) + splash * (t > dur_s * 0.55))


def foley_grow(dur_s: float, seed: int) -> np.ndarray:
    """Growth sproing: a cartoon spring — pitch dips then rebounds up, ring decaying —
    plus a soft soil pop at the start."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    f = 320.0 + 240.0 * np.tanh((t / dur_s - 0.28) * 6.0)
    spring = np.sin(2 * np.pi * np.cumsum(f) / SR)
    wobble = 1.0 + 0.25 * np.sin(2 * np.pi * 22.0 * t) * np.exp(-t * 8.0)
    pop_ = np.sin(2 * np.pi * 180.0 * t) * np.exp(-t * 200.0) * 0.6
    return _norm(spring * wobble * np.exp(-t * 7.0) * _env_ad(len(t), 6.0, dur_s * 500.0) + pop_)


def foley_sparkle(dur_s: float, seed: int) -> np.ndarray:
    """Celestial sparkle: a tiny high bell arpeggio, staggered — moon, stars, magic."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    out = np.zeros(len(t))
    notes = rng.choice([1568.0, 1760.0, 2093.0, 2349.0, 2637.0], size=4, replace=False)
    for i, f0 in enumerate(notes):
        lag = i * 0.07 + rng.uniform(0, 0.02)
        tt = np.maximum(0.0, t - lag)
        out += np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 14.0) * (t >= lag) * (0.5 - i * 0.09)
        out += np.sin(2 * np.pi * f0 * 2.01 * tt) * np.exp(-tt * 30.0) * (t >= lag) * 0.1
    return _norm(out)


def foley_chime(dur_s: float, seed: int) -> np.ndarray:
    """Warm chime: two mallet partials — daylight, arrival, gentle reveal."""
    t = _t(dur_s)
    out = np.sin(2 * np.pi * 660.0 * t) * np.exp(-t * 9.0)
    out += 0.5 * np.sin(2 * np.pi * 990.0 * t) * np.exp(-t * 14.0)
    out += 0.18 * np.sin(2 * np.pi * 1320.0 * t) * np.exp(-t * 22.0)
    return _norm(out * _env_ad(len(t), 3.0, dur_s * 300.0))


def foley_engine(dur_s: float, seed: int) -> np.ndarray:
    """Vehicle hum: a low two-tone drone with a slow judder plus tyre-noise wash —
    driving, machinery, things that run."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    judder = 1.0 + 0.3 * np.sin(2 * np.pi * 7.0 * t)
    hum = (np.sin(2 * np.pi * 82.0 * t) + 0.5 * np.sin(2 * np.pi * 123.0 * t)) * judder
    road = _smooth(rng.standard_normal(len(t)), 90) * 0.5
    env = np.sin(np.linspace(0, np.pi, len(t))) ** 1.2
    return _norm((hum * 0.7 + road) * env)


def foley_heart(dur_s: float, seed: int) -> np.ndarray:
    """Heartbeat: two soft low thumps, lub-dub — warmth, life, courage beats."""
    t = _t(dur_s)
    lub = np.sin(2 * np.pi * 60.0 * t) * np.exp(-t * 40.0)
    tt = np.maximum(0.0, t - dur_s * 0.42)
    dub = np.sin(2 * np.pi * 52.0 * tt) * np.exp(-tt * 45.0) * (t >= dur_s * 0.42) * 0.8
    return _norm((lub + dub) * _env_ad(len(t), 4.0, dur_s * 400.0))


def foley_alarm(dur_s: float, seed: int) -> np.ndarray:
    """Little bell alarm: three bright metal tings — waking, attention, o'clock."""
    t = _t(dur_s)
    out = np.zeros(len(t))
    for i in range(3):
        lag = i * dur_s * 0.26
        tt = np.maximum(0.0, t - lag)
        ring = np.sin(2 * np.pi * 2100.0 * tt) + 0.4 * np.sin(2 * np.pi * 3310.0 * tt)
        out += ring * np.exp(-tt * 26.0) * (t >= lag)
    return _norm(out)


def foley_step(dur_s: float, seed: int) -> np.ndarray:
    """A soft paper step: felt thud plus a short rustle — the puppet's footfall."""
    t = _t(dur_s)
    thud = np.sin(2 * np.pi * 140.0 * t) * np.exp(-t * 90.0) * 0.7
    rustle = _hipass(_noise(len(t), seed)) * np.exp(-t * 160.0) * 0.45
    return _norm(thud + rustle)


def foley_kick(dur_s: float, seed: int) -> np.ndarray:
    """Boot on ball: a punchy low thump with a leather slap on top."""
    t = _t(dur_s)
    f = 110.0 + 90.0 * np.exp(-t * 60.0)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28.0)
    slap = _hipass(_noise(len(t), seed)) * np.exp(-t * 260.0) * 0.9
    return _norm(thump + slap)


def foley_bounce(dur_s: float, seed: int) -> np.ndarray:
    """A ball bouncing to rest: three rubbery thumps, each closer and softer."""
    t = _t(dur_s)
    out = np.zeros(len(t))
    lag, gap, amp = 0.0, dur_s * 0.42, 1.0
    for _ in range(4):
        tt = np.maximum(0.0, t - lag)
        f = 150.0 + 120.0 * np.exp(-tt * 70.0)
        out += np.sin(2 * np.pi * np.cumsum(f * (t >= lag)) / SR) * np.exp(-tt * 38.0) * (t >= lag) * amp
        lag += gap
        gap *= 0.55
        amp *= 0.6
    return _norm(out)


def foley_hop(dur_s: float, seed: int) -> np.ndarray:
    """Cartoon hop: a quick upward boing with a soft landing pat."""
    t = _t(dur_s)
    f = 260.0 + 520.0 * (t / dur_s)
    boing = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.minimum(1.0, t / (dur_s * 0.7))) ** 1.5
    pat = np.sin(2 * np.pi * 120.0 * t) * np.exp(-np.maximum(0.0, t - dur_s * 0.75) * 60.0) * (t >= dur_s * 0.75)
    return _norm(boing * 0.8 + pat * 0.6)


def foley_roll(dur_s: float, seed: int) -> np.ndarray:
    """Rolling: a low grainy rumble that swells and fades."""
    t = _t(dur_s)
    grit = _smooth(_noise(len(t), seed), 40) * (1.0 + 0.4 * np.sin(2 * np.pi * 9.0 * t))
    hum = np.sin(2 * np.pi * 70.0 * t) * 0.4
    return _norm((grit + hum) * np.sin(np.linspace(0, np.pi, len(t))) ** 0.8)


def foley_fall(dur_s: float, seed: int) -> np.ndarray:
    """Falling: a descending slide whistle that ends in a soft thud."""
    t = _t(dur_s)
    f = 1300.0 * np.exp(-t / dur_s * 1.6)
    slide = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t < dur_s * 0.8) * 0.55
    tt = np.maximum(0.0, t - dur_s * 0.8)
    thud = np.sin(2 * np.pi * 90.0 * tt) * np.exp(-tt * 40.0) * (t >= dur_s * 0.8)
    return _norm(slide + thud)


def foley_rise(dur_s: float, seed: int) -> np.ndarray:
    """Lifting off: a rising tone under an opening air sweep."""
    t = _t(dur_s)
    f = 220.0 * np.exp(t / dur_s * 1.8)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
    air = whoosh(dur_s, True, seed)[: len(t)]
    return _norm((tone + air) * np.sin(np.linspace(0, np.pi, len(t))))


def foley_flap(dur_s: float, seed: int) -> np.ndarray:
    """Wings: soft feathery noise bursts at a flapping rate."""
    t = _t(dur_s)
    rate = 7.5
    gate = np.maximum(0.0, np.sin(2 * np.pi * rate * t)) ** 3
    air = _smooth(_noise(len(t), seed), 12)
    return _norm(air * gate * np.sin(np.linspace(0, np.pi, len(t))) ** 0.5)


def foley_spin(dur_s: float, seed: int) -> np.ndarray:
    """Spinning: a whirr whose pitch wobbles with the turn."""
    t = _t(dur_s)
    f = 420.0 + 160.0 * np.sin(2 * np.pi * 5.0 * t)
    whirr = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + _smooth(_noise(len(t), seed), 6) * 0.4
    return _norm(whirr * np.sin(np.linspace(0, np.pi, len(t))) ** 1.2)


def foley_shake(dur_s: float, seed: int) -> np.ndarray:
    """Shaking: a quick run of dry rattles."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    out = np.zeros(len(t))
    for i in range(7):
        lag = i * dur_s / 7 + rng.uniform(0, 0.01)
        tt = np.maximum(0.0, t - lag)
        out += _hipass(_noise(len(t), seed + i)) * np.exp(-tt * 110.0) * (t >= lag) * (0.6 + 0.4 * rng.random())
    return _norm(out)


def foley_dim(dur_s: float, seed: int) -> np.ndarray:
    """Going dark: a soft falling bell that closes to silence."""
    t = _t(dur_s)
    f = 880.0 * np.exp(-t / dur_s * 0.9)
    bell = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return _norm(bell * np.exp(-t * 3.5) * _env_ad(len(t), 20.0, dur_s * 600.0))


def foley_crack(dur_s: float, seed: int) -> np.ndarray:
    """A shell giving way: three brittle ticks tightening into one crisp snap."""
    t = _t(dur_s)
    out = np.zeros(len(t))
    n = _hipass(_noise(len(t), seed))
    for k, (at, amp) in enumerate(((0.0, 0.45), (0.07, 0.6), (0.13, 1.0))):
        m = t >= at
        out[m] += n[m] * np.exp(-(t[m] - at) * (380.0 - k * 60.0)) * amp
    return _norm(out)


def foley_pour(dur_s: float, seed: int) -> np.ndarray:
    """Liquid filling a vessel: a burbling stream whose pitch climbs as it fills."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    out = _hipass(_noise(len(t), seed)) * 0.18
    for _ in range(int(dur_s * 28)):
        at = rng.uniform(0.0, dur_s * 0.95)
        f0 = 380.0 + 900.0 * (at / dur_s) + rng.uniform(-60.0, 60.0)
        m = t >= at
        tt = t[m] - at
        out[m] += np.sin(2 * np.pi * (f0 * tt + 1800.0 * tt * tt)) * np.exp(-tt * 70.0) * 0.5
    return _norm(out * _env_ad(len(t), 40.0, dur_s * 1400.0))


def foley_ignite(dur_s: float, seed: int) -> np.ndarray:
    """A match catching: a scratch, then the soft breath of a flame taking hold."""
    t = _t(dur_s)
    n = _noise(len(t), seed)
    scratch = _hipass(n) * np.exp(-t * 30.0) * (t < 0.12)
    whoomp = n * np.exp(-np.maximum(0.0, t - 0.08) * 7.0) * (t >= 0.08) * 0.35
    return _norm(scratch + np.convolve(whoomp, np.ones(24) / 24, mode='same'))


def foley_puff(dur_s: float, seed: int) -> np.ndarray:
    """Blowing a flame out: a short breathy puff that dies to nothing."""
    t = _t(dur_s)
    n = np.convolve(_noise(len(t), seed), np.ones(18) / 18, mode='same')
    return _norm(n * _env_ad(len(t), 25.0, 110.0))


def foley_drip(dur_s: float, seed: int) -> np.ndarray:
    """Melting: slow, spaced drips, each a small falling plink."""
    t = _t(dur_s)
    out = np.zeros(len(t))
    for k, at in enumerate((0.0, dur_s * 0.33, dur_s * 0.62)):
        m = t >= at
        tt = t[m] - at
        f = 1500.0 - 500.0 * np.minimum(1.0, tt * 30.0) - k * 120.0
        out[m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40.0) * (1.0 - k * 0.2)
    return _norm(out)


def foley_frost(dur_s: float, seed: int) -> np.ndarray:
    """Freezing: a glassy crystalline shimmer that creeps in and holds."""
    t = _t(dur_s)
    rng = np.random.default_rng(seed)
    out = np.zeros(len(t))
    for _ in range(14):
        f = rng.uniform(3200.0, 6400.0)
        at = rng.uniform(0.0, dur_s * 0.7)
        m = t >= at
        out[m] += np.sin(2 * np.pi * f * (t[m] - at)) * np.exp(-(t[m] - at) * 12.0) * 0.3
    return _norm(out * np.minimum(1.0, t / (dur_s * 0.4)))


def foley_creak(dur_s: float, seed: int) -> np.ndarray:
    """A door on its hinge: a slow rasping creak that bends in pitch."""
    t = _t(dur_s)
    f = 170.0 + 90.0 * np.sin(np.pi * t / dur_s)
    ph = 2 * np.pi * np.cumsum(f) / SR
    rasp = np.sign(np.sin(ph)) * 0.4 + np.sin(ph * 3.0) * 0.3
    grain = 1.0 + 0.5 * np.sin(2 * np.pi * 34.0 * t)
    return _norm(rasp * grain * _env_ad(len(t), 60.0, dur_s * 900.0) * 0.8)


def foley_thud(dur_s: float, seed: int) -> np.ndarray:
    """A door shutting: a dull wooden thud with a latch click."""
    t = _t(dur_s)
    f = 85.0 + 60.0 * np.exp(-t * 40.0)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22.0)
    latch = _hipass(_noise(len(t), seed)) * np.exp(-np.maximum(0.0, t - 0.05) * 300.0) * (t >= 0.05) * 0.5
    return _norm(body + latch)


def foley_vanish(dur_s: float, seed: int) -> np.ndarray:
    """Leaving: a quick up-swish that thins out into air."""
    t = _t(dur_s)
    air = whoosh(dur_s, True, seed)[: len(t)]
    glint = np.sin(2 * np.pi * 2400.0 * t) * np.exp(-np.maximum(0.0, t - dur_s * 0.5) * 20.0) * (t >= dur_s * 0.5) * 0.25
    return _norm(air * np.exp(-t * 2.0) + glint)


def foley_flag(dur_s: float, seed: int) -> np.ndarray:
    """Cloth in wind: low flutter noise with irregular snaps."""
    t = _t(dur_s)
    cloth = _smooth(_noise(len(t), seed), 30) * (0.6 + 0.4 * np.sin(2 * np.pi * 3.3 * t) ** 2)
    snap = _hipass(_noise(len(t), seed + 1)) * (np.sin(2 * np.pi * 2.1 * t) > 0.97) * 0.8
    return _norm((cloth + snap) * np.sin(np.linspace(0, np.pi, len(t))) ** 0.6)


# The counting scale: C major from C5 upward — each count rings one step higher.
COUNT_SCALE = [523.25, 587.33, 659.25, 698.46, 783.99, 880.0, 987.77, 1046.5, 1174.66, 1318.51]


def count_note(k: int, dur_s: float = 0.32) -> np.ndarray:
    """Marimba-like count note k (1..10): wooden strike + two partials."""
    f0 = COUNT_SCALE[max(0, min(len(COUNT_SCALE) - 1, k - 1))]
    t = _t(dur_s)
    body = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 11.0)
    body += 0.35 * np.sin(2 * np.pi * f0 * 3.9 * t) * np.exp(-t * 40.0)
    body += 0.12 * np.sin(2 * np.pi * f0 * 9.2 * t) * np.exp(-t * 90.0)
    return _norm(body * _env_ad(len(t), 1.5, dur_s * 800.0))



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
    ('click-01', 'synth.click', lambda: click(3200.0, 0.045, 151)),
    ('click-02', 'synth.click', lambda: click(3900.0, 0.04, 152)),
    ('click-03', 'synth.click', lambda: click(2700.0, 0.05, 153)),
    ('thock-01', 'synth.thock', lambda: thock(190.0, 0.14, 161)),
    ('thock-02', 'synth.thock', lambda: thock(230.0, 0.12, 162)),
    ('thock-03', 'synth.thock', lambda: thock(160.0, 0.16, 163)),
    ('swish-01', 'synth.swish', lambda: swish(0.2, 171)),
    ('swish-02', 'synth.swish', lambda: swish(0.26, 172)),
    ('swish-03', 'synth.swish', lambda: swish(0.17, 173)),
    # --- the paper film's own fabric
    ('paper-rustle-01', 'craft.paper.rustle', lambda: paper_rustle(0.5, 201)),
    ('paper-rustle-02', 'craft.paper.rustle', lambda: paper_rustle(0.38, 202)),
    ('paper-rustle-03', 'craft.paper.rustle', lambda: paper_rustle(0.62, 203)),
    ('paper-tap-01', 'craft.paper.tap', lambda: paper_tap(0.16, 211)),
    ('paper-tap-02', 'craft.paper.tap', lambda: paper_tap(0.13, 212)),
    ('paper-tap-03', 'craft.paper.tap', lambda: paper_tap(0.19, 213)),
    ('paper-page-01', 'craft.paper.page', lambda: paper_page(0.5, 221)),
    ('paper-page-02', 'craft.paper.page', lambda: paper_page(0.4, 222)),
    ('paper-page-03', 'craft.paper.page', lambda: paper_page(0.58, 223)),
    ('paper-tear-01', 'craft.paper.tear', lambda: paper_tear(0.42, 231)),
    ('paper-tear-02', 'craft.paper.tear', lambda: paper_tear(0.3, 232)),
    ('paper-step-01', 'craft.paper.step', lambda: foley_step(0.18, 241)),
    ('paper-step-02', 'craft.paper.step', lambda: foley_step(0.15, 242)),
    ('paper-step-03', 'craft.paper.step', lambda: foley_step(0.21, 243)),
    # --- ambience loops (bed under a beat, mixed quiet)
    ('amb-rain-01', 'amb.rain', lambda: amb_rain(2.6, 251)),
    ('amb-rain-02', 'amb.rain', lambda: amb_rain(3.1, 252)),
    ('amb-wind-01', 'amb.wind', lambda: amb_wind(3.2, 261)),
    ('amb-wind-02', 'amb.wind', lambda: amb_wind(2.7, 262)),
    ('amb-water-01', 'amb.water', lambda: amb_water(3.0, 271)),
    ('amb-water-02', 'amb.water', lambda: amb_water(2.5, 272)),
    ('amb-birds-01', 'amb.birds', lambda: amb_birds(2.8, 281)),
    ('amb-birds-02', 'amb.birds', lambda: amb_birds(3.4, 282)),
    ('amb-crickets-01', 'amb.crickets', lambda: amb_crickets(3.0, 291)),
    ('amb-crickets-02', 'amb.crickets', lambda: amb_crickets(2.6, 292)),
    ('amb-fire-01', 'amb.fire', lambda: amb_fire(2.8, 295)),
    # --- foley hits: the sound the shown thing makes
    ('foley-drop-01', 'foley.water.drop', lambda: foley_drop(0.5, 301)),
    ('foley-drop-02', 'foley.water.drop', lambda: foley_drop(0.42, 302)),
    ('foley-grow-01', 'foley.grow', lambda: foley_grow(0.6, 311)),
    ('foley-grow-02', 'foley.grow', lambda: foley_grow(0.48, 312)),
    ('foley-sparkle-01', 'foley.sparkle', lambda: foley_sparkle(0.8, 321)),
    ('foley-sparkle-02', 'foley.sparkle', lambda: foley_sparkle(0.66, 322)),
    ('foley-chime-01', 'foley.chime', lambda: foley_chime(0.9, 331)),
    ('foley-chime-02', 'foley.chime', lambda: foley_chime(0.7, 332)),
    ('foley-engine-01', 'foley.engine', lambda: foley_engine(1.0, 341)),
    ('foley-engine-02', 'foley.engine', lambda: foley_engine(0.8, 342)),
    ('foley-heart-01', 'foley.heart', lambda: foley_heart(0.9, 351)),
    ('foley-heart-02', 'foley.heart', lambda: foley_heart(0.74, 352)),
    ('foley-alarm-01', 'foley.alarm', lambda: foley_alarm(0.9, 361)),
    ('foley-alarm-02', 'foley.alarm', lambda: foley_alarm(0.72, 362)),
    # --- story-action foley: the sound of the verb
    ('foley-kick-01', 'foley.kick', lambda: foley_kick(0.3, 401)),
    ('foley-kick-02', 'foley.kick', lambda: foley_kick(0.26, 402)),
    ('foley-bounce-01', 'foley.bounce', lambda: foley_bounce(0.9, 411)),
    ('foley-hop-01', 'foley.hop', lambda: foley_hop(0.36, 421)),
    ('foley-hop-02', 'foley.hop', lambda: foley_hop(0.3, 422)),
    ('foley-roll-01', 'foley.roll', lambda: foley_roll(1.1, 431)),
    ('foley-fall-01', 'foley.fall', lambda: foley_fall(0.9, 441)),
    ('foley-fall-02', 'foley.fall', lambda: foley_fall(0.75, 442)),
    ('foley-rise-01', 'foley.rise', lambda: foley_rise(1.1, 451)),
    ('foley-flap-01', 'foley.flap', lambda: foley_flap(0.8, 461)),
    ('foley-flap-02', 'foley.flap', lambda: foley_flap(0.65, 462)),
    ('foley-spin-01', 'foley.spin', lambda: foley_spin(0.8, 471)),
    ('foley-shake-01', 'foley.shake', lambda: foley_shake(0.5, 481)),
    ('foley-dim-01', 'foley.dim', lambda: foley_dim(1.0, 491)),
    ('foley-vanish-01', 'foley.vanish', lambda: foley_vanish(0.6, 501)),
    ('foley-flag-01', 'foley.flag', lambda: foley_flag(1.0, 511)),
    # --- object state changes
    ('foley-crack-01', 'foley.crack', lambda: foley_crack(0.4, 521)),
    ('foley-pour-01', 'foley.pour', lambda: foley_pour(1.4, 531)),
    ('foley-ignite-01', 'foley.ignite', lambda: foley_ignite(0.7, 541)),
    ('foley-puff-01', 'foley.puff', lambda: foley_puff(0.45, 551)),
    ('foley-drip-01', 'foley.drip', lambda: foley_drip(1.2, 561)),
    ('foley-frost-01', 'foley.frost', lambda: foley_frost(1.1, 571)),
    ('foley-creak-01', 'foley.creak', lambda: foley_creak(0.9, 581)),
    ('foley-thud-01', 'foley.thud', lambda: foley_thud(0.35, 591)),
] + [(f'count-{k:02d}', f'synth.count.{k:02d}', (lambda k=k: count_note(k))) for k in range(1, 11)]


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
            'family': tag.split('.')[0],
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
