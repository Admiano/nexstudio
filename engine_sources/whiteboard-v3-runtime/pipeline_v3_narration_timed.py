#!/usr/bin/env python3
"""NexMind Whiteboard V3 narration-timed renderer (reconstruction).

Reconstructs the missing last-mile V3 renderer identified in provenance as
``WHITEBOARD_ELITE_RUNTIME/vendor/pipeline_v3_narration_timed.py``
(recorded sha256 c91f2bc50cb634c993ff307ef01bb4177d9478a290bf0b4da042adee260f9c34;
standalone source was never persisted — see
``engines/whiteboard-v3-system/NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE/06_provenance/EXACT_ARTIFACT_GAP.json``).

This module is a reconstruction, not the recovered original. It reuses the
preserved execution body — ``whiteboard_compiler.compile_whiteboard_plan`` for
semantic draw plans and board zones, ``whiteboard_pil_adapter`` for frame
rasterization, and ``sound_choreographer`` for the 48 kHz pen/marker bed — and
adds the pieces the receipt proves the original had: narration-clock scene
windows, camera travel between board zones (``cluster_travel`` /
``giant_board_journey``), a pull-back board reveal, VO + SFX mixing with
ducking, MP4 encoding, QA contact sheet, metrics, and an execution receipt.

Input plan schema: ``NexMindWhiteboardV3NarrationTimedPlanV1`` — see README.md.

The preserved execution body is resolved from
``$WHITEBOARD_V3_SYSTEM_PACKAGE`` or ``<repo>/engines/whiteboard-v3-system/
NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE`` (installed by ``scripts/install-engines.py``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

SCHEMA = 'NexMindWhiteboardV3NarrationTimedPlanV1'
RECEIPT_SCHEMA = 'NexMindWhiteboardV3ReconstructedExecutionReceiptV1'
VERSION = '3.0.0-reconstruction.1'

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKAGE = (
    REPO_ROOT / 'engines' / 'whiteboard-v3-system' / 'NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE'
)
EXECUTION_SUBPATH = (
    '01_base_execution/Whiteboard_Execution_Body_V2/explainer-motion/whiteboard-v1/runtime'
)

DEFAULT_FPS = 25
LEAD_IN_SECONDS = 0.4
CLUSTER_TRANSITION_SECONDS = 0.62
GIANT_BOARD_TRAVEL_SECONDS = 0.72
REVEAL_HOLD_FRACTION = 0.25


# ---------------------------------------------------------------------------
# Preserved execution body access
# ---------------------------------------------------------------------------

def resolve_execution_package(package_root: str | None = None) -> Path:
    root = Path(package_root or os.environ.get('WHITEBOARD_V3_SYSTEM_PACKAGE') or DEFAULT_PACKAGE)
    runtime = root / EXECUTION_SUBPATH
    if not (runtime / 'whiteboard_pil_adapter.py').exists():
        raise FileNotFoundError(
            'WHITEBOARD_V3_EXECUTION_BODY_MISSING: expected preserved execution body at '
            f'{runtime}. Run `python scripts/install-engines.py` or set WHITEBOARD_V3_SYSTEM_PACKAGE.'
        )
    return runtime


def load_execution_body(package_root: str | None = None):
    runtime = resolve_execution_package(package_root)
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    import whiteboard_compiler  # noqa: E402
    import whiteboard_pil_adapter  # noqa: E402
    import sound_choreographer  # noqa: E402
    import v3_board_renderer  # noqa: E402
    return whiteboard_compiler, whiteboard_pil_adapter, sound_choreographer, v3_board_renderer


# ---------------------------------------------------------------------------
# Plan handling — narration is the clock
# ---------------------------------------------------------------------------

def _err(code: str, detail: str) -> ValueError:
    return ValueError(f'{code}: {detail}')


def load_plan(path: Path) -> dict:
    try:
        plan = json.loads(Path(path).read_text())
    except Exception as e:
        raise _err('WHITEBOARD_V3_PLAN_UNREADABLE', str(e))
    return normalize_plan(plan)


def _norm_word(w: str) -> str:
    return re.sub(r"[^a-z0-9']+", '', str(w).lower())


def load_word_timings(path: str | Path) -> list[dict]:
    """Normalize a word-timings JSON to [{'word','start','end'}].

    Accepts: a flat list of {word|text, start, end}, ElevenLabs-style
    {'characters': [...], 'character_start_times_seconds': [...]} — grouped
    into words, or whisper verbose {'segments': [{words: [...]}]}.
    """
    data = json.loads(Path(path).read_text())
    words: list[dict] = []
    if isinstance(data, list):
        for w in data:
            if isinstance(w, dict) and 'start' in w:
                words.append({'word': w.get('word', w.get('text', '')),
                              'start': float(w['start']),
                              'end': float(w.get('end', w['start']))})
    elif isinstance(data, dict) and data.get('segments'):
        for seg in data['segments']:
            for w in seg.get('words', []):
                words.append({'word': w.get('word', ''),
                              'start': float(w['start']),
                              'end': float(w['end'])})
    elif isinstance(data, dict) and data.get('characters'):
        chars = data['characters']
        starts = data['character_start_times_seconds']
        ends = data['character_end_times_seconds']
        cur, ws, we = '', None, None
        for ch, st, en in zip(chars, starts, ends):
            if ch in ' \n\t':
                if cur:
                    words.append({'word': cur, 'start': ws, 'end': we})
                    cur = ''
            else:
                cur += ch
                ws = st if ws is None else ws
                we = en
        if cur:
            words.append({'word': cur, 'start': ws, 'end': we})
    return [w for w in words if w.get('word')]


def align_beats_to_words(plan: dict, words: list[dict]) -> dict:
    """Audio-as-authority: re-time each beat's window to where its narration
    is actually spoken. Sequential matcher walks the transcript once; beats
    whose narration isn't found keep their authored timing."""
    p = normalize_plan(plan)
    # keep word objects parallel to normalized tokens — indices align
    pairs = [(w, _norm_word(w['word'])) for w in words]
    pairs = [(w, t) for w, t in pairs if t]
    if not pairs:
        return p
    toks = [t for _, t in pairs]
    ti = 0
    for b in p['beats']:
        narr = [_norm_word(x) for x in
                str(b.get('narration') or '').split()]
        narr = [x for x in narr if x]
        if not narr:
            continue
        # locate the narration's first token within a scan window
        found = None
        for j in range(ti, min(len(toks), ti + 400)):
            if toks[j] == narr[0]:
                found = j
                break
        if found is None:
            continue
        end_i = min(len(toks) - 1, found + len(narr) - 1)
        b['start_seconds'] = max(0.0, pairs[found][0]['start'] - 0.15)
        b['duration_seconds'] = max(
            0.5, pairs[end_i][0]['end'] - b['start_seconds'] + 0.35)
        ti = end_i + 1
    cursor = 0.0
    for b in p['beats']:
        b['start_seconds'] = max(b['start_seconds'], cursor)
        cursor = b['start_seconds'] + b['duration_seconds']
    p['durationSeconds'] = cursor + p['pacing']['board_reveal_seconds']
    return p


def normalize_plan(plan: dict) -> dict:
    if not isinstance(plan, dict):
        raise _err('WHITEBOARD_V3_PLAN_INVALID', 'plan must be a JSON object')
    beats = plan.get('beats')
    if not isinstance(beats, list) or not beats:
        raise _err('WHITEBOARD_V3_BEATS_REQUIRED', 'plan.beats must be a non-empty list')
    p = json.loads(json.dumps(plan))
    p['schema'] = SCHEMA
    p['executionMode'] = 'WHITEBOARD_SEMANTIC_GRAPH'
    cursor = 0.0
    norm_beats: list[dict] = []
    for i, raw in enumerate(beats):
        if not isinstance(raw, dict):
            raise _err('WHITEBOARD_V3_BEAT_INVALID', f'beats[{i}] must be an object')
        b = dict(raw)
        scene = dict(b.get('scene') or {})
        scene.setdefault('sceneId', b.get('beat_id') or f'beat-{i+1:02d}')
        scene['executionMode'] = 'WHITEBOARD_SEMANTIC_GRAPH'
        dur = b.get('duration_seconds', b.get('scene_duration_seconds'))
        if dur is None:
            dur = scene.get('timingOverrideSeconds') or 4.0
        dur = max(0.5, float(dur))
        b['duration_seconds'] = dur
        start = b.get('start_seconds')
        b['start_seconds'] = float(start) if start is not None else cursor
        cursor = b['start_seconds'] + dur
        scene['timingOverrideSeconds'] = dur
        b['scene'] = scene
        norm_beats.append(b)
    p['beats'] = norm_beats
    p['sceneSpecs'] = [b['scene'] for b in norm_beats]
    pacing = p.get('pacing') or {}
    variant = str(p.get('camera_variant') or 'cluster_travel')
    p['camera_variant'] = variant
    trans_default = GIANT_BOARD_TRAVEL_SECONDS if variant == 'giant_board_journey' else CLUSTER_TRANSITION_SECONDS
    p['pacing'] = {
        'lead_in_seconds': float(pacing.get('lead_in_seconds', LEAD_IN_SECONDS)),
        'transition_seconds': float(pacing.get('transition_seconds', trans_default)),
        'board_reveal_seconds': float(
            pacing.get('board_reveal_seconds', GIANT_BOARD_TRAVEL_SECONDS)
        ),
    }
    p['durationSeconds'] = cursor + p['pacing']['board_reveal_seconds']
    # Warm paper + blue accent — the reel's house palette; overridable per plan.
    if not p.get('brandExecution'):
        p['brandExecution'] = {
            'brandAuthority': {
                'background': '#F5F0E4', 'ink': '#1A1A17',
                'accent': '#0052FF', 'secondary': '#8B8577',
            }
        }
    return p


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _board_canvas(wbp, v3r, plan: dict, ratio: str, scenes: list[dict]):
    """Composite every fully-drawn scene into a grid mosaic with breathing
    space — N scenes lay out ceil(sqrt(N)) columns by however many rows
    (4 → 2×2, 10 → 4×3), each tile a full rendered scene frame."""
    import math
    from PIL import Image
    size = wbp.RATIO_SIZES[ratio]
    view_w, view_h = size
    pal = plan.get('_pal') or wbp._pal(plan)
    n = max(1, len(scenes))
    cols = max(1, math.ceil(math.sqrt(n)))
    rows = math.ceil(n / cols)
    gap = int(view_h * 0.06)
    cw = cols * view_w + (cols + 1) * gap
    ch = rows * view_h + (rows + 1) * gap
    canvas = Image.new('RGB', (cw, ch), tuple(pal['bgc'][:3]))
    centers = []
    for i, scene in enumerate(scenes):
        tile = v3r.render_scene_frame(scene, plan, ratio, scene_time=999.0)
        cx = gap + (i % cols) * (view_w + gap) + view_w // 2
        cy = gap + (i // cols) * (view_h + gap) + view_h // 2
        canvas.paste(tile, (cx - view_w // 2, cy - view_h // 2))
        centers.append((cx, cy))
    # pad to the output aspect so the pull-back lands with even paper margins
    need_w = int(canvas.height * view_w / view_h)
    need_h = int(canvas.width * view_h / view_w)
    pw, ph = max(canvas.width, need_w), max(canvas.height, need_h)
    if (pw, ph) != canvas.size:
        padded = Image.new('RGB', (pw, ph), tuple(pal['bgc'][:3]))
        ox, oy = (pw - canvas.width) // 2, (ph - canvas.height) // 2
        padded.paste(canvas, (ox, oy))
        canvas = padded
    else:
        ox = oy = 0
    lx, ly = centers[-1]
    start_view = (lx + ox - view_w // 2, ly + oy - view_h // 2,
                  lx + ox + view_w // 2, ly + oy + view_h // 2)
    end_view = (0, 0, canvas.width, canvas.height)
    return canvas, start_view, end_view


def _reveal_frame(canvas, start_view, end_view, p: float, size):
    q = p * p * (3 - 2 * p)
    box = tuple(
        int(a + (b - a) * q) for a, b in zip(start_view, end_view)
    )
    box = (
        max(0, box[0]), max(0, box[1]),
        min(canvas.width, max(box[0] + 8, box[2])),
        min(canvas.height, max(box[1] + 8, box[3])),
    )
    return canvas.crop(box).resize(size)


def render_frames(wbp, v3r, plan: dict, ratio: str, fps: int) -> Iterator[tuple[float, Any]]:
    """Yield (t_seconds, PIL RGB frame) across the narration-timed timeline."""
    beats = plan['beats']
    scenes = plan['sceneSpecs']
    pacing = plan['pacing']
    trans = pacing['transition_seconds']
    reveal = pacing['board_reveal_seconds']
    step = 1.0 / fps
    total = beats[-1]['start_seconds'] + beats[-1]['duration_seconds']

    t = 0.0
    while t < total - 1e-9:
        # Current beat = last beat whose window has opened; a completed beat holds.
        idx = 0
        for i, b in enumerate(beats):
            if b['start_seconds'] <= t:
                idx = i
            else:
                break
        beat, scene = beats[idx], scenes[idx]
        local = t - beat['start_seconds']
        if idx > 0 and local < trans:
            frame = v3r.render_transition_frame(scenes[idx - 1], scene, plan, ratio, local / trans)
        else:
            frame = v3r.render_scene_frame(scene, plan, ratio, scene_time=local)
        yield t, frame
        t += step

    if reveal > 0:
        canvas, start_view, end_view = _board_canvas(wbp, v3r, plan, ratio, scenes)
        n = max(1, int(round(reveal * fps)))
        hold_from = 1.0 - REVEAL_HOLD_FRACTION
        for i in range(n):
            p = min(1.0, (i / max(1, n - 1)) / hold_from)
            yield total + i * step, _reveal_frame(canvas, start_view, end_view, p, wbp.RATIO_SIZES[ratio])


# ---------------------------------------------------------------------------
# Audio + encode
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def build_sfx(snd, plan: dict, duration: float, out_path: Path) -> Path:
    # sound_choreographer reads plan['sceneSpecs'][*]['whiteboardRuntime']['drawPlan']
    # Runtime wrap (preserved module untouched): point its audio dir at our
    # denser synthesized marker bed — the packaged bed was ~16x too quiet.
    sfx_dir = Path(__file__).parent / 'assets' / 'sfx'
    marker_bed = sfx_dir / 'marker-real-bed-48k.wav'
    if not marker_bed.is_file():
        marker_bed = sfx_dir / 'marker-scratch-bed-48k.wav'
    if marker_bed.is_file():
        snd.AUDIO = sfx_dir
        snd.ROLE_FILE['marker.short'] = marker_bed.name
        snd.ROLE_FILE['marker.swipe'] = marker_bed.name
        snd.ROLE_GAIN['marker.short'] = 0.30
        snd.ROLE_GAIN['marker.swipe'] = 0.38

    # Emit one scratch event per polyline pen-down interval (written into the
    # drawPlan by the renderer) — the sound plays only while the pen inks,
    # never during lifts or travel between strokes.
    def pen_events(pl):
        import random as _rnd
        out = []
        base = 0.0
        beats = pl.get('beats') or []
        scenes = pl.get('sceneSpecs') or []
        for si, s in enumerate(scenes):
            wb = s.get('whiteboardRuntime') or {}
            dur = float(wb.get('sceneDuration') or 1)
            # The video places each scene at its word-aligned beat start —
            # narration pauses create gaps, so a cumulative-duration clock
            # would schedule scratches early (before the ink appears).
            bstart = (float(beats[si]['start_seconds'])
                      if si < len(beats) else base)
            for i, st in enumerate(wb.get('drawPlan') or []):
                role = st.get('soundRole')
                if not role:
                    continue
                rnd = _rnd.Random(snd._seed(wb.get('seed'), st.get('id'), role))
                spans = st.get('pen') or [[st.get('start', 0), st.get('end', 0)]]
                for ps, pe in spans:
                    out.append({
                        'role': role,
                        'file': snd.ROLE_FILE.get(role, snd.ROLE_FILE['marker.short']),
                        'start': bstart + float(ps),
                        'duration': max(.05, float(pe) - float(ps)),
                        'offset': rnd.random() * 4.8,
                        'gain': snd.ROLE_GAIN.get(role, .12),
                        'seed': snd._seed(si, i, role)})
            base = bstart + dur
        if scenes:
            out.append({'role': 'cap', 'file': snd.ROLE_FILE['cap'],
                        'start': .04, 'duration': .23, 'offset': .15,
                        'gain': snd.ROLE_GAIN['cap'],
                        'seed': snd._seed('cap', 'open')})
            out.append({'role': 'cap', 'file': snd.ROLE_FILE['cap'],
                        'start': max(.05, base - .28), 'duration': .24,
                        'offset': 1.28, 'gain': snd.ROLE_GAIN['cap'] * .8,
                        'seed': snd._seed('cap', 'close')})
        return sorted(out, key=lambda x: (x['start'], x['role']))
    snd.events = pen_events
    return Path(snd.render(plan, duration, out_path)['path'])


def build_music(duration: float, out_path: Path, rate: int = 48000) -> Path:
    """Generated ambient pad bed — deterministic, license-clean (no sampled
    audio): soft triangle chord progression under everything, mastered quiet.
    Not a music library — a warm neutral bed until a licensed track drops in."""
    import wave
    from array import array
    import numpy as np
    n = int(duration * rate)
    t = np.arange(n) / rate
    # Cmaj7 -> Am7 -> Fmaj7 -> G add6, 2.6 s bars — calm, unobtrusive
    bars = [(261.6, 329.6, 392.0, 493.9), (220.0, 261.6, 329.6, 392.0),
            (174.6, 220.0, 261.6, 329.6), (196.0, 246.9, 293.7, 392.0)]
    bar = 2.6
    mix = np.zeros(n)
    for bi, start_s in enumerate(np.arange(0, duration + bar, bar)):
        chord = bars[bi % len(bars)]
        i0 = int(start_s * rate)
        seg_n = min(n - i0, int((bar + 0.6) * rate))
        if seg_n <= 0:
            break
        tt = np.arange(seg_n) / rate
        env = np.minimum(1.0, tt / 0.8) * np.minimum(
            1.0, (bar + 0.6 - tt) / 0.9)  # soft attack, gentle release
        for f in chord:
            mix[i0:i0 + seg_n] += 0.045 * env * np.sin(
                2 * np.pi * f * tt + 0.15 * np.sin(2 * np.pi * 0.5 * tt))
        mix[i0:i0 + seg_n] += 0.05 * env * np.sin(
            2 * np.pi * chord[0] / 2 * tt)  # sub root
    # slow shimmer + edge fades
    mix *= 1.0 + 0.10 * np.sin(2 * np.pi * 0.31 * t)
    fade_in = np.minimum(1.0, t / 1.4)
    fade_out = np.minimum(1.0, (duration - t) / 2.2)
    mix *= fade_in * fade_out
    peak = max(1e-9, np.abs(mix).max())
    mix = mix / peak * 0.5
    pcm = array('h', np.clip(mix * 32767, -32767, 32767).astype(np.int16))
    with wave.open(str(out_path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return out_path


def encode_mp4(
    frames_dir: Path,
    fps: int,
    size: tuple[int, int],
    sfx_wav: Path | None,
    voiceover: Path | None,
    duration: float,
    out_path: Path,
    ffmpeg: str = 'ffmpeg',
    music_wav: Path | None = None,
) -> Path:
    cmd = [
        ffmpeg, '-y', '-loglevel', 'error',
        '-framerate', str(fps), '-i', str(frames_dir / 'f%05d.png'),
    ]
    filters = []
    ins = []  # ordered audio inputs after video
    if sfx_wav:
        ins.append(sfx_wav)
    if music_wav:
        ins.append(music_wav)
    if voiceover:
        ins.append(voiceover)
    for p in ins:
        cmd += ['-i', str(p)]
    idx = {p: i + 1 for i, p in enumerate(ins)}
    for p in ins:
        # VO splits into sidechain key + mix only when another bed exists to duck
        tail = (',asplit=2[vo_sc][vo_mix]'
                if p is voiceover and len(ins) > 1
                else '[vo_mix]' if p is voiceover else f'[n{idx[p]}]')
        filters.append(
            f'[{idx[p]}:a]aformat=sample_fmts=fltp:channel_layouts=mono,'
            f'aresample=48000{tail}')
    beds = [f'[n{idx[p]}]' for p in ins if p != voiceover]
    if len(ins) >= 2 and voiceover:
        # VO is the timing/intelligibility authority; SFX + music bed duck
        # under it (6 dB-class duck, ~120 ms attack, ~280 ms release,
        # mastered to -16 LUFS / -1.5 dBTP).
        if len(beds) > 1:
            filters.append(
                ''.join(beds) +
                f'amix=inputs={len(beds)}:normalize=0,'
                'aformat=sample_fmts=fltp:channel_layouts=mono[bed]')
        else:
            filters.append(
                f'{beds[0]}aformat=sample_fmts=fltp:channel_layouts=mono[bed]')
        bed_src = '[bed]'
        filters.append(
            f'{bed_src}[vo_sc]sidechaincompress='
            'threshold=0.02:ratio=8:attack=120:release=280[ducked];'
            f'[ducked][vo_mix]amix=inputs=2:normalize=0[m];'
            f'[m]loudnorm=I=-16:TP=-1.5:LRA=7,atrim=0:{duration:.3f}[a]'
        )
    elif ins:
        if len(beds) > 1:
            filters.append(
                ''.join(beds) +
                f'amix=inputs={len(beds)}:normalize=0[m];'
                f'[m]loudnorm=I=-16:TP=-1.5:LRA=7,atrim=0:{duration:.3f}[a]')
        elif voiceover and not beds:
            # voiceover is the only input — master it straight to spec
            filters.append(
                f'[vo_mix]loudnorm=I=-16:TP=-1.5:LRA=7,atrim=0:{duration:.3f}[a]')
        else:
            filters.append(
                f'{beds[0]}loudnorm=I=-16:TP=-1.5:LRA=7,atrim=0:{duration:.3f}[a]')
    if filters:
        cmd += ['-filter_complex', ';'.join(filters), '-map', '0:v', '-map', '[a]',
                '-c:a', 'aac', '-b:a', '160k']
    else:
        cmd += ['-map', '0:v']
    cmd += [
        '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart', '-shortest', str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f'FFMPEG_ENCODE_FAILED: {proc.stderr[-2000:]}')
    return out_path


# ---------------------------------------------------------------------------
# QA artifacts
# ---------------------------------------------------------------------------

def contact_sheet(frames_dir: Path, times: list[float], fps: int, out_path: Path, cols: int = 2):
    from PIL import Image
    frames = sorted(frames_dir.glob('f*.png'))
    picked = [frames[min(len(frames) - 1, int(round(t * fps)))] for t in times]
    thumbs = []
    for p in picked:
        im = Image.open(p).convert('RGB')
        im.thumbnail((640, 640))
        thumbs.append((p, im))
    w = max(im.width for _, im in thumbs)
    h = max(im.height for _, im in thumbs) + 22
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new('RGB', (cols * w, rows * h), (18, 18, 16))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, (p, im) in enumerate(thumbs):
        x = (i % cols) * w
        y = (i // cols) * h
        sheet.paste(im, (x, y + 22))
        d.text((x + 6, y + 5), f'{times[i]:.1f}s', fill=(220, 220, 210))
    sheet.save(out_path, quality=88)
    return out_path


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def render_production(
    plan: dict,
    out_dir: Path,
    ratio: str = '16:9',
    fps: int = DEFAULT_FPS,
    voiceover: Path | None = None,
    keep_frames: bool = False,
    package_root: str | None = None,
) -> dict:
    wbc, wbp, snd, v3r = load_execution_body(package_root)
    ratio = ratio or (plan.get('output_ratios') or ['16:9'])[0]
    if ratio not in wbp.RATIO_SIZES:
        raise _err('WHITEBOARD_V3_RATIO_UNSUPPORTED', ratio)

    compiled = wbc.compile_whiteboard_plan(plan, {'ratio': ratio})
    compiled['_pal'] = wbp._pal(compiled)
    plan.update(compiled)
    beats = plan['beats']
    duration = beats[-1]['start_seconds'] + beats[-1]['duration_seconds'] + plan['pacing']['board_reveal_seconds']

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = str(plan.get('production_id') or 'whiteboard-v3')
    frames_dir = Path(tempfile.mkdtemp(prefix='wbv3-frames-'))
    frame_count = 0
    try:
        for t, frame in render_frames(wbp, v3r, plan, ratio, fps):
            frame.save(frames_dir / f'f{frame_count:05d}.png')
            frame_count += 1

        sfx_wav = None
        ffmpeg = shutil.which('ffmpeg')
        mp4 = out_dir / f'{name}.mp4'
        if ffmpeg:
            sfx_wav = build_sfx(snd, plan, duration, out_dir / f'{name}.sfx.wav')
            vo = None
            vo_spec = plan.get('voiceover') or {}
            vo_path = Path(vo_spec.get('path')) if vo_spec.get('path') else voiceover
            if vo_path and Path(vo_path).exists():
                vo = Path(vo_path)
            encode_mp4(frames_dir, fps, wbp.RATIO_SIZES[ratio], sfx_wav, vo,
                       duration, mp4, ffmpeg)

        times = [b['start_seconds'] + b['duration_seconds'] * 0.5 for b in beats]
        times.append(duration - plan['pacing']['board_reveal_seconds'] * 0.2)
        qa = contact_sheet(frames_dir, times, fps, out_dir / f'{name}_QA.jpg')
    finally:
        if not keep_frames:
            shutil.rmtree(frames_dir, ignore_errors=True)

    metrics = {
        'schema': 'NexMindWhiteboardV3MetricsV1',
        'production_id': name,
        'camera_variant': plan['camera_variant'],
        'ratio': ratio,
        'fps': fps,
        'duration_seconds': round(duration, 3),
        'frame_count': frame_count,
        'scene_count': len(beats),
        'stroke_count': sum(
            len(s.get('whiteboardRuntime', {}).get('drawPlan', [])) for s in plan['sceneSpecs']
        ),
        'board_world': plan.get('whiteboardBoardWorld'),
    }
    (out_dir / f'{name}_METRICS.json').write_text(json.dumps(metrics, indent=2) + '\n')

    receipt = {
        'schema': RECEIPT_SCHEMA,
        'renderer': {
            'path': 'engine_sources/whiteboard-v3-runtime/pipeline_v3_narration_timed.py',
            'version': VERSION,
            'reconstruction': True,
            'recorded_original_sha256': 'c91f2bc50cb634c993ff307ef01bb4177d9478a290bf0b4da042adee260f9c34',
        },
        'production_id': name,
        'camera_variant': plan['camera_variant'],
        'ratio': ratio,
        'duration_seconds': round(duration, 3),
        'outputs': {
            f.stem: {'path': str(f), 'sha256': _sha256(f)}
            for f in out_dir.glob(f'{name}*') if f.is_file()
        },
    }
    receipt_path = out_dir / f'{name}_EXECUTION_RECEIPT.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='NexMind Whiteboard V3 narration-timed renderer (reconstruction)')
    ap.add_argument('plan', help='Narration-timed plan JSON (NexMindWhiteboardV3NarrationTimedPlanV1)')
    ap.add_argument('--out-dir', default='out')
    ap.add_argument('--ratio', default=None, choices=['16:9', '1:1', '9:16'])
    ap.add_argument('--variant', default=None, choices=['cluster_travel', 'giant_board_journey'])
    ap.add_argument('--fps', type=int, default=DEFAULT_FPS)
    ap.add_argument('--voiceover', default=None, help='Optional VO audio file to mix under the pen bed')
    ap.add_argument('--word-timings', default=None,
                    help='Word-level timing JSON (ElevenLabs /with-timestamps, '
                         'whisper verbose_json, or flat [{word,start,end}]). '
                         'When given, each beat window is re-aligned to where '
                         'its narration is actually spoken — audio is the clock.')
    ap.add_argument('--accent', default=None,
                    help='Brand accent hex (e.g. #E11D48) — overrides the '
                         'plan brandAuthority.accent; drives swooshes, '
                         'accent fills and callout marks')
    ap.add_argument('--keep-frames', action='store_true')
    ap.add_argument('--package-root', default=None, help='Override path to NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE')
    a = ap.parse_args(argv)

    plan = load_plan(Path(a.plan))
    if a.variant:
        plan['camera_variant'] = a.variant
    if a.accent:
        plan.setdefault('brandExecution', {}).setdefault(
            'brandAuthority', {})['accent'] = a.accent
    if a.word_timings:
        plan = align_beats_to_words(plan, load_word_timings(a.word_timings))
    receipt = render_production(
        plan,
        Path(a.out_dir),
        ratio=a.ratio or '16:9',
        fps=a.fps,
        voiceover=Path(a.voiceover) if a.voiceover else None,
        keep_frames=a.keep_frames,
        package_root=a.package_root,
    )
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
