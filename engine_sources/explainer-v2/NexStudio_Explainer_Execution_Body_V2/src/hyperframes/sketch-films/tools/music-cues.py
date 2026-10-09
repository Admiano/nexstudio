#!/usr/bin/env python3
"""Measure a music track's beat grid for beat-synced sketch-films.

Decodes with ffmpeg, builds a spectral-flux onset envelope with numpy,
estimates tempo by autocorrelation, then lays a beat grid and marks
'strong' cues (downbeats + loud onsets). Output feeds the director via
`--cues cues.json` — scene boundaries and SFX accents snap onto the grid.

    python3 music-cues.py <audio> <out.json>

Deps: python3 + numpy + ffmpeg on PATH. No librosa.
"""
import json
import math
import subprocess
import sys

import numpy as np

SR = 22050
HOP = 512
WIN = 1024


def decode(path: str) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32)


def onset_env(y: np.ndarray) -> np.ndarray:
    n = 1 + (len(y) - WIN) // HOP
    if n < 4:
        return np.zeros(4)
    frames = np.lib.stride_tricks.as_strided(
        y, shape=(n, WIN), strides=(y.strides[0] * HOP, y.strides[0])
    )
    spec = np.abs(np.fft.rfft(frames * np.hanning(WIN), axis=1))
    spec = np.log1p(1000 * spec)
    flux = np.maximum(0.0, np.diff(spec, axis=0)).sum(axis=1)
    flux = np.concatenate([[0.0], flux])
    # smooth + normalize
    k = np.hanning(5); k /= k.sum()
    flux = np.convolve(flux, k, mode="same")
    m = flux.max()
    return flux / m if m > 0 else flux


def tempo_of(env: np.ndarray, fps: float) -> float:
    env = env - env.mean()
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 55)  # 55..180 BPM
    if hi >= len(ac):
        return 120.0
    lag = lo + int(np.argmax(ac[lo:hi]))
    return 60.0 * fps / lag


def main() -> int:
    src, out = sys.argv[1], sys.argv[2]
    y = decode(src)
    dur = len(y) / SR
    env = onset_env(y)
    fps = SR / HOP
    bpm = tempo_of(env, fps)
    period = 60.0 / bpm
    # phase: strongest onset in the first 4s anchors beat 0
    early = env[: int(min(4.0, dur) * fps)]
    t0 = (int(np.argmax(early)) / fps) if early.size else 0.0
    beats = []
    t = t0
    while t < dur:
        if t >= 0:
            beats.append(round(t, 3))
        t += period
    # strong cues: onset peaks above 1.6x median, snapped to the grid
    med = np.median(env) or 1e-6
    peaks = []
    for i in range(1, len(env) - 1):
        if env[i] > 1.6 * med and env[i] >= env[i - 1] and env[i] >= env[i + 1]:
            tt = i / fps
            if not peaks or tt - peaks[-1] > period * 0.45:
                peaks.append(round(tt, 3))
    strong = []
    for p in peaks:
        g = min(beats, key=lambda b: abs(b - p), default=None)
        if g is not None and abs(g - p) < period * 0.3:
            strong.append(g)
        else:
            strong.append(p)
    strong = sorted(set(round(s, 3) for s in strong))
    with open(out, "w") as f:
        json.dump({
            "duration": round(dur, 3), "bpm": round(bpm, 1),
            "beatPeriod": round(period, 4), "beats": beats, "strong": strong,
        }, f, indent=1)
    print(f"{src}: {dur:.1f}s bpm={bpm:.1f} beats={len(beats)} strong={len(strong)}")
    return 0


if __name__ == "__main__":
    sys.exit(main() if len(sys.argv) == 3 else 2)
