"""Motion-figure strip renderer for whiteboard scenes.

Runs the skin_rig CLI once per scene ``figureMotion`` spec and caches RGBA
PNG frames; ``v3_board_renderer`` composites them over the drawn board at the
character's slot. Deterministic: identical (clip, spec, duration) reuses the
cached strip. Figures bottom-align onto a fixed canvas so foot contact never
jumps.

Spec fields: ``clip`` (vault clip name) or ``say`` (narration resolved through
clip_select), optional ``visemes`` (rhubarb cues json), ``visemeOffset``
(seconds — narration absolute time -> clip-local), ``t`` (clip start offset),
``mirror``, ``scale``.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKIN_RIG = HERE / 'skin_rig.cjs'
NODE = shutil.which('node') or '/home/ubuntu/.nvm/versions/node/v24.19.0/bin/node'
_STRIP_ROOT = Path(tempfile.gettempdir()) / 'nexstick_fig_strips'
_CANVAS = (300, 400)  # strip tile; content bottom-aligns, headroom for reach

_STRIPS: dict = {}


def resolve_clip(spec: dict) -> str | None:
    """'clip' verbatim, else 'say' text through the clip_select table."""
    clip = spec.get('clip')
    if clip:
        return str(clip)
    say = spec.get('say') or spec.get('text')
    if not say:
        return None
    out = subprocess.run(
        [NODE, '-e',
         "const cs=require('./clip_select.cjs');"
         "const sm=require('./cmu_sampler.cjs');"
         "console.log(cs.selectClip(process.argv[1],sm.vault().clips)||'')",
         str(say)],
        cwd=str(HERE), capture_output=True, text=True, timeout=60)
    return out.stdout.strip() or None


def _rasterize(svg_dir: Path):
    """Every gNNN.svg -> RGBA tile on a fixed canvas, feet pinned to the
    bottom edge so the figure never slides vertically between frames."""
    import cairosvg
    from PIL import Image
    frames = []
    for f in sorted(svg_dir.glob('g*.svg')):
        png = svg_dir / (f.stem + '.png')
        cairosvg.svg2png(url=str(f), write_to=str(png),
                         output_width=_CANVAS[0])
        img = Image.open(png).convert('RGBA')
        if img.height > _CANVAS[1]:
            w = int(img.width * _CANVAS[1] / img.height)
            img = img.resize((w, _CANVAS[1]), Image.LANCZOS)
        tile = Image.new('RGBA', _CANVAS, (0, 0, 0, 0))
        tile.alpha_composite(img, (( _CANVAS[0] - img.width) // 2,
                                   _CANVAS[1] - img.height))
        frames.append(tile)
    return frames


def get_strip(spec: dict, seconds: float, fps: int = 12):
    """(spec, duration) -> list of RGBA frames covering the beat. Cached."""
    clip = resolve_clip(spec)
    if not clip:
        return []
    key = (clip, round(float(seconds), 2), fps,
           json.dumps(spec, sort_keys=True))
    if key in _STRIPS:
        return _STRIPS[key]
    n = max(2, int(math.ceil(seconds * fps)))
    tag = re.sub(r'[^A-Za-z0-9_]+', '_', clip)
    out = _STRIP_ROOT / f"{tag}_{hashlib.sha1(repr(key).encode()).hexdigest()[:8]}"
    if not (out / 'g000.svg').exists():
        out.mkdir(parents=True, exist_ok=True)
        req = {'cmuClip': clip}
        if spec.get('style'):
            req['style'] = spec['style']
        if spec.get('visemes'):
            req['visemes'] = str(spec['visemes'])
        if spec.get('visemeOffset') is not None:
            req['visOffset'] = float(spec['visemeOffset'])
        if spec.get('t'):
            req['t'] = float(spec['t'])
        if spec.get('mirror'):
            req['mirror'] = True
        r = subprocess.run(
            [NODE, str(SKIN_RIG), json.dumps(req), str(out), str(n), str(fps)],
            capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            _STRIPS[key] = []
            return []
    _STRIPS[key] = _rasterize(out)
    return _STRIPS[key]
