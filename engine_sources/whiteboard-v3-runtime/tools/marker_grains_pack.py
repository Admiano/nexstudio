"""Build the marker foley grain bank from real CC0 / public-domain recordings.

Sources (Wikimedia Commons, downloaded once, not vendored):
  377124_tubbsmedia_marker-lines.wav  — TubbsMedia, CC0 (permanent marker lines)
  Writing_with_feltpen.ogg            — stephan, public domain (felt pen writing)

Each recording is high-passed (handling rumble), gated into its pen-down runs
and loudness-normalized per run. Long runs (marker lines) and short runs
(felt-pen lettering) become two pools in one 16-bit mono 48 kHz WAV plus a
JSON index. Usage:
  python3 tools/marker_grains_pack.py lines.wav feltpen.ogg assets/sfx
"""
from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

RATE = 48000
HOP = 480


def _load(path: str) -> np.ndarray:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1',
                          '-ar', str(RATE), '-f', 'f32le', '-'],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def _filter(a: np.ndarray, hp: float, shelf_hz: float, shelf_db: float):
    S = np.fft.rfft(a)
    f = np.maximum(np.fft.rfftfreq(len(a), 1 / RATE), 1.0)
    S *= 1 / np.sqrt(1 + (hp / f) ** 8)
    g = 10 ** (shelf_db / 20)
    S *= 1 + (g - 1) / (1 + (shelf_hz / f) ** 2)
    return np.fft.irfft(S, len(a))


def _detone(segs: list, limit_db: float = 2.0) -> list:
    """Static EQ that pulls every narrow spectral bump (desk/body resonance,
    hum) down to the local median, so no grain carries a pitch."""
    x = np.concatenate(segs)
    N = 8192
    win = np.hanning(N)
    P = np.mean([np.abs(np.fft.rfft(x[i:i + N] * win)) ** 2
                 for i in range(0, len(x) - N, N // 2)], 0)
    L = 10 * np.log10(P + 1e-20)
    k = 61
    pad = np.pad(L, k // 2, mode='edge')
    base = np.array([np.median(pad[i:i + k]) for i in range(len(L))])
    excess = np.maximum(0.0, L - base - limit_db)
    gain = 10 ** (-excess / 20)
    fN = np.fft.rfftfreq(N, 1 / RATE)
    out = []
    for seg in segs:
        f = np.fft.rfftfreq(len(seg), 1 / RATE)
        out.append(np.fft.irfft(np.fft.rfft(seg) * np.interp(f, fN, gain),
                                len(seg)))
    return out


def _runs(a: np.ndarray, rise_db: float, min_s: float, pad_s: float):
    e = 20 * np.log10(np.array([np.sqrt((a[i:i + HOP] ** 2).mean())
                                for i in range(0, len(a) - HOP, HOP)]) + 1e-9)
    act = e > np.percentile(e, 10) + rise_db
    out, s = [], None
    for i, v in enumerate(list(act) + [False]):
        if v and s is None:
            s = i
        elif not v and s is not None:
            if (i - s) * HOP / RATE >= min_s:
                pad = int(pad_s * RATE)
                out.append((max(0, s * HOP - pad),
                            min(len(a), i * HOP + pad)))
            s = None
    return out


def main(lines: str, felt: str, out_dir: str) -> None:
    pools = {
        # permanent marker on paper: bright — soften the top so it reads
        # felt-on-paper rather than whiteboard squeak
        'long': (_filter(_load(lines), 400, 5000, -14.0), 20, 0.5, 0.02),
        'short': (_filter(_load(felt), 300, 9000, 0.0), 12, 0.04, 0.012),
    }
    bank, index, cur = [], [], 0
    for pool, (a, rise, mn, pad) in pools.items():
        segs = _detone([a[s:e] for s, e in _runs(a, rise, mn, pad)])
        segs = _detone(segs)
        for seg in segs:
            core = seg[int(len(seg) * .1):int(len(seg) * .9)] if len(seg) > 40 else seg
            seg = seg * (0.1 / max(1e-6, np.sqrt((core ** 2).mean())))
            bank.append(seg)
            index.append({'pool': pool, 'start': cur, 'end': cur + len(seg)})
            cur += len(seg)
    pcm = np.clip(np.concatenate(bank), -1, 1)
    out = Path(out_dir)
    with wave.open(str(out / 'marker-grains-48k.wav'), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((pcm * 32767).astype(np.int16).tobytes())
    (out / 'marker-grains.json').write_text(json.dumps(
        {'rate': RATE, 'grains': index}, indent=0))
    print({p: sum(1 for g in index if g['pool'] == p) for p in pools},
          round(cur / RATE, 2), 's')


if __name__ == '__main__':
    main(*sys.argv[1:4])
