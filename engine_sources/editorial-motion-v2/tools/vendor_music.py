#!/usr/bin/env python3
"""Vendor the CC0 music library and measure what the compiler needs to place a bed under a film.

Source: the FreePD corpus (Kevin MacLeod et al., released CC0 / public domain) as mirrored by
SoundSafari/CC0-1.0-Music — freepd.com itself has closed, so the mirror is the surviving copy.

    git clone --depth 1 --filter=blob:none --no-checkout https://github.com/SoundSafari/CC0-1.0-Music ~/cc0music
    (cd ~/cc0music && git checkout HEAD -- freepd.com)
    python3 tools/vendor_music.py ~/cc0music/freepd.com

For every bed in BEDS the tool

  * transcodes an excerpt (EXCERPT_S, stereo 44.1k 96k MP3 — the bed sits 19dB under the voice) into assets/community/music/freepd/ so a
    100-bed library stays a few hundred MB, not gigabytes;
  * measures tempo (onset autocorrelation with octave folding into the 64–160 BPM band the
    motion grammar can follow), the beat-grid phase inside the file, integrated loudness
    (EBU R128), spectral brightness and onset density;
  * derives an `energy` in 0..1 from loudness + onset density so a bed can be matched to a
    film's spoken energy, not just its mood word;
  * writes the manifest entry with sha256 provenance and the curated mood list.

Moods are curated per title (the one subjective field); everything else is measured. Idempotent.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'assets' / 'community' / 'music' / 'freepd'
MANIFEST = ROOT / 'assets' / 'community' / 'manifest.json'
LICENSE_TXT = OUT_DIR / 'LICENSE.txt'
SOURCE = {'pack': 'FreePD corpus via SoundSafari/CC0-1.0-Music', 'url': 'https://github.com/SoundSafari/CC0-1.0-Music/tree/main/freepd.com'}
EXCERPT_S = 120.0
FADE_S = 2.5
SR = 22050
HOP = 512
BPM_LO, BPM_HI = 64, 160

# title -> moods. Bounded by FILM_MOODS in contracts.py; the compiler rejects a film mood outside it.
BEDS: Dict[str, List[str]] = {
    # existing ten
    'Adding the Sun': ['uplifting', 'bright'],
    'Bass Meant Jazz': ['jazzy', 'calm'],
    'Flutey Jazz': ['jazzy', 'bright'],
    'Happy Whistling Ukulele': ['playful', 'bright'],
    'Hopeful': ['uplifting'],
    "Landra's Dream": ['dreamy', 'calm'],
    'Nordic Wist': ['wistful'],
    'Study and Relax': ['calm', 'dreamy'],
    'Sunday Dub': ['calm', 'playful'],
    'Ukulele Song': ['playful', 'uplifting'],
    # bright / uplifting / corporate
    'And Here We Go': ['uplifting', 'driving'],
    'And Just Like That': ['uplifting', 'bright'],
    'Celebration': ['uplifting', 'bright'],
    'City Sunshine': ['bright', 'playful'],
    'Connecting Rainbows': ['uplifting', 'warm'],
    'Elevate Inspirate': ['uplifting', 'focused'],
    'Energizing': ['driving', 'bright'],
    'Finally See The Light': ['uplifting', 'warm'],
    'Fireworks': ['uplifting', 'driving'],
    'Funshine': ['playful', 'bright'],
    'Going Bananas': ['playful', 'quirky'],
    'Gotta Keep On Movin': ['driving', 'playful'],
    'Groovin': ['playful', 'jazzy'],
    'Hear What They Say': ['focused', 'uplifting'],
    'Hippety Hop': ['playful', 'quirky'],
    'Horizon Flare': ['uplifting', 'driving'],
    'Inspiration': ['uplifting', 'warm'],
    'Inventing Flight': ['uplifting', 'focused'],
    'Journey of Hope': ['uplifting', 'warm'],
    'Lucky Break': ['playful', 'bright'],
    'New Hero in Town': ['uplifting', 'driving'],
    'One Step Closer': ['focused', 'uplifting'],
    'Pump up your Graduation': ['uplifting', 'bright'],
    'Shining Stars': ['dreamy', 'uplifting'],
    'Slice of Life': ['warm', 'playful'],
    'Spring Chicken': ['playful', 'quirky'],
    'Take the Ride': ['driving', 'bright'],
    'Wisdom in the Sun': ['warm', 'calm'],
    # calm / dreamy / focused
    'Ambient Bongos': ['calm', 'focused'],
    'Aquarium': ['dreamy', 'calm'],
    'Be Chillin': ['calm', 'playful'],
    'Coy Koi': ['calm', 'dreamy'],
    'Deep Tones': ['calm', 'focused'],
    'Icicles Melting': ['dreamy', 'calm'],
    'Infinite Peace': ['calm', 'dreamy'],
    'Infinite Wonder': ['dreamy', 'uplifting'],
    'Kalimba Relaxation Music': ['calm', 'warm'],
    'Lovely Piano Song': ['calm', 'warm'],
    'Magic in the Garden': ['dreamy', 'playful'],
    'Meditating Beat': ['calm', 'focused'],
    'Midnight in the Green House': ['dreamy', 'calm'],
    'Nostalgic Piano': ['wistful', 'calm'],
    'Painting Room': ['calm', 'focused'],
    'Piano Magic Motive': ['dreamy', 'elegant'],
    'Pond': ['calm', 'dreamy'],
    'Relaxing Ballad': ['calm', 'warm'],
    'River Meditation': ['calm', 'dreamy'],
    'Romantic Inspiration': ['warm', 'elegant'],
    'Screen Saver': ['calm', 'focused'],
    'Space Ambience': ['dreamy', 'calm'],
    'Think About It': ['focused', 'calm'],
    'Travelers Notebook': ['wistful', 'warm'],
    'Trip Up North': ['wistful', 'calm'],
    # jazzy / elegant
    'A Waltz For Naseem': ['elegant', 'wistful'],
    'BeBop for Joey': ['jazzy', 'playful'],
    'Compy Jazz': ['jazzy', 'focused'],
    'Downtown Boogie': ['jazzy', 'driving'],
    'Fancy Family': ['elegant', 'playful'],
    'Martini Sunset': ['jazzy', 'elegant'],
    'Night in Venice': ['elegant', 'warm'],
    'Pina Colada': ['playful', 'warm'],
    'Still Pickin': ['playful', 'warm'],
    'Take the Sting Out - Jazz Fi': ['jazzy', 'calm'],
    'The Celebrated Minuet for Piano': ['elegant', 'calm'],
    # driving / electronic / focused
    'Backbeat': ['driving', 'focused'],
    'Beat One': ['driving', 'focused'],
    'Beat Thee': ['driving', 'focused'],
    'Bit Bit Loop': ['playful', 'driving'],
    'Blippy Trance': ['driving', 'bright'],
    'Circuit': ['driving', 'focused'],
    'City Run': ['driving', 'uplifting'],
    'Drop Point': ['driving', 'tense'],
    'Funkeriffic': ['playful', 'driving'],
    'Funky Energy Loop': ['driving', 'playful'],
    'Limit 70': ['driving', 'focused'],
    'Motions': ['focused', 'driving'],
    'Rush': ['driving', 'tense'],
    'Shenzhen Nightlife': ['driving', 'bright'],
    'Uberpunch': ['driving', 'tense'],
    # quirky / playful
    'Busybody': ['quirky', 'playful'],
    'Comic Game Loop - Mischief': ['quirky', 'playful'],
    'Fake It Til You Fake It': ['quirky', 'playful'],
    'Foam Rubber': ['quirky', 'playful'],
    'Hold on a Sec': ['quirky', 'focused'],
    'Llama in Pajama': ['quirky', 'playful'],
    'Lurking Sloth': ['quirky', 'calm'],
    'Managing Mischief': ['quirky', 'playful'],
    'My Giant Bunny Friend': ['quirky', 'warm'],
    'Patience Party': ['quirky', 'playful'],
    'Pickled Pink': ['quirky', 'playful'],
    'Silly Boy': ['quirky', 'playful'],
    'Wakka Wakka': ['quirky', 'playful'],
    # tense / focused underscores
    'Asking Questions': ['tense', 'focused'],
    'Driving Concern': ['tense', 'driving'],
    'Hidden Truth': ['tense', 'focused'],
    'Mysterious Lights': ['tense', 'dreamy'],
    'Parhelion': ['focused', 'dreamy'],
    'Stereotype News': ['focused', 'driving'],
}


def slug(title: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')


def _run(args: List[str]) -> bytes:
    return subprocess.check_output(args, stderr=subprocess.DEVNULL)


def _duration(path: Path) -> float:
    return float(_run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)]).decode().strip())


def _mono(path: Path) -> np.ndarray:
    raw = _run(['ffmpeg', '-v', 'quiet', '-i', str(path), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'])
    return np.frombuffer(raw, dtype='<f4')


def _lufs(path: Path) -> Tuple[float, float]:
    """Integrated loudness (LUFS) and true peak (dBTP) via EBU R128."""
    out = subprocess.run(['ffmpeg', '-nostats', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    i = re.findall(r'I:\s+(-?[\d.]+) LUFS', out)
    tp = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', out)
    return float(i[-1]), float(tp[-1])


def _onsets(x: np.ndarray) -> np.ndarray:
    n = len(x) // HOP
    frames = x[: n * HOP].reshape(n, HOP)
    spec = np.abs(np.fft.rfft(frames * np.hanning(HOP), axis=1))
    # spectral flux: positive change of the log-magnitude spectrum frame to frame
    logm = np.log1p(spec * 50.0)
    flux = np.maximum(0.0, np.diff(logm, axis=0)).sum(axis=1)
    flux = np.concatenate([[0.0], flux])
    return flux - flux.mean()


def _brightness(x: np.ndarray) -> float:
    n = len(x) // HOP
    frames = x[: n * HOP].reshape(n, HOP)
    spec = np.abs(np.fft.rfft(frames * np.hanning(HOP), axis=1))
    freqs = np.fft.rfftfreq(HOP, 1.0 / SR)
    power = spec.sum(axis=1)
    keep = power > power.max() * 0.02
    cent = (spec[keep] * freqs).sum(axis=1) / np.maximum(power[keep], 1e-9)
    return float(np.median(cent))


def _tempo(onset: np.ndarray) -> Tuple[int, float]:
    """Tempo in BPM and the beat-grid phase (ms into the file) it locks to.

    Autocorrelation of the onset curve, summed with its half-period harmonic so a tune with
    strong off-beats does not read at double tempo, then folded into [BPM_LO, BPM_HI]."""
    fps = SR / HOP
    lags = np.arange(int(fps * 60 / 220), int(fps * 60 / 40))
    ac = np.array([np.dot(onset[:-lag], onset[lag:]) / (len(onset) - lag) for lag in lags])
    score = ac.copy()
    for i, lag in enumerate(lags):
        half = lag // 2
        j = np.searchsorted(lags, half)
        if 0 <= j < len(lags) and lags[j] == half:
            score[i] += 0.5 * ac[j]
    bpm = 60.0 * fps / lags[int(np.argmax(score))]
    while bpm < BPM_LO:
        bpm *= 2
    while bpm > BPM_HI:
        bpm /= 2
    period = 60.0 * fps / bpm
    # grid phase: the offset whose comb of ticks collects the most onset energy
    idx = np.arange(0, len(onset) - period, period)
    best_phase, best = 0, -np.inf
    for ph in np.linspace(0, period, 24, endpoint=False):
        s = onset[(idx + ph).astype(int)].sum()
        if s > best:
            best, best_phase = s, ph
    return int(round(bpm)), float(best_phase * 1000.0 / fps)


def _energy(lufs: float, density: float) -> float:
    """0..1: loudness across the -30..-10 LUFS span, blended with onset density (events/s)."""
    loud = min(1.0, max(0.0, (lufs + 30.0) / 20.0))
    dens = min(1.0, max(0.0, density / 6.0))
    return round(0.6 * loud + 0.4 * dens, 3)


def transcode(src: Path, dst: Path) -> None:
    dur = min(_duration(src), EXCERPT_S)
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', str(src), '-t', f'{dur:.3f}', '-ac', '2', '-ar', '44100',
                           '-af', f'afade=t=out:st={max(0.0, dur - FADE_S):.3f}:d={FADE_S}', '-c:a', 'libmp3lame', '-b:a', '96k', str(dst)])


def measure(path: Path) -> Dict[str, object]:
    x = _mono(path)
    onset = _onsets(x)
    bpm, phase_ms = _tempo(onset)
    lufs, tp = _lufs(path)
    thr = onset.mean() + 2.0 * onset.std()
    peaks = np.flatnonzero((onset[1:-1] > thr) & (onset[1:-1] >= onset[:-2]) & (onset[1:-1] >= onset[2:]))
    density = len(peaks) / (len(x) / SR)
    return {
        'duration_s': round(len(x) / SR, 3), 'bpm': bpm, 'grid_offset_ms': int(round(phase_ms)),
        'lufs': round(lufs, 1), 'true_peak_dbtp': round(tp, 1), 'brightness_hz': int(round(_brightness(x))),
        'onsets_per_s': round(density, 2), 'energy': _energy(lufs, density),
    }


def main(src_dir: Path) -> None:
    manifest = json.loads(MANIFEST.read_text())
    keep = [a for a in manifest['assets'] if a.get('kind') != 'music']
    entries = []
    missing = []
    for title, moods in BEDS.items():
        src = src_dir / f'{title}.mp3'
        if not src.exists():
            missing.append(title)
            continue
        dst = OUT_DIR / f'{slug(title)}.mp3'
        if not dst.exists():
            transcode(src, dst)
        data = dst.read_bytes()
        m = measure(dst)
        entries.append({
            'id': f'music.{slug(title)}', 'kind': 'music', 'title': title, 'path': f'music/freepd/{dst.name}',
            'sha256': hashlib.sha256(data).hexdigest(), 'license': 'CC0-1.0', 'source': SOURCE,
            'excerpt': {'seconds': EXCERPT_S, 'fade_out_s': FADE_S}, **m, 'moods': moods,
        })
        print(f"{title:36s} {m['bpm']:4d}bpm  phase {m['grid_offset_ms']:4d}ms  {m['lufs']:6.1f} LUFS  energy {m['energy']:.2f}  {'/'.join(moods)}")
    wanted = {f'music/freepd/{slug(t)}.mp3' for t in BEDS}
    for old in OUT_DIR.glob('*.mp3'):
        if f'music/freepd/{old.name}' not in wanted:
            old.unlink()
    entries.sort(key=lambda e: e['id'])
    manifest['assets'] = keep + entries
    manifest['count'] = len(manifest['assets'])
    MANIFEST.write_text(json.dumps(manifest, indent=1) + '\n')
    LICENSE_TXT.write_text(
        'FreePD corpus — Creative Commons Zero (CC0 1.0) / public domain.\n'
        'Tracks by Kevin MacLeod and other FreePD contributors, mirrored at\n'
        f"{SOURCE['url']} after freepd.com closed.\n"
        f'Vendored as {EXCERPT_S:.0f}s excerpts (see manifest.json `excerpt`). No attribution required.\n')
    print(f'{len(entries)} beds vendored; {len(missing)} titles missing from source: {missing}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).expanduser())
