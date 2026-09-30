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

# The proto cast (RGS pack + vault-drawn exercises) is the whiteboard
# character — say-resolved clips prefer it wherever its set covers the
# motion. Vault clip name -> baked PROTO_* dir.
_PROTO_ALIASES = {
    'NEX_MOTION_WALK': 'PROTO_WALK', 'CMU_WALK': 'PROTO_WALK',
    'NEX_MOTION_RUN': 'PROTO_RUN', 'CMU_RUN': 'PROTO_RUN',
    'NEX_MOTION_JUMP': 'PROTO_JUMP', 'CMU_JUMP': 'PROTO_JUMP',
    'NEX_MOTION_IDLE': 'PROTO_IDLE', 'NEX_MOTION_LIVING_IDLE': 'PROTO_IDLE',
    'NEX_MOTION_SIT': 'PROTO_IDLE',
    'NEX_MECHANIC_PUSHUP_CYCLE': 'PROTO_EX_PUSH_UP',
    'NEX_ACTPRIM_PUSHUP_CYCLE_V1': 'PROTO_EX_PUSH_UP',
    'NEX_MECHANIC_PLANK_DYNAMIC': 'PROTO_EX_PLANK',
    'NEX_ACTPRIM_PLANK_DYNAMIC_V1': 'PROTO_EX_PLANK',
    'NEX_MECHANIC_BURPEE_CYCLE': 'PROTO_EX_BURPEE',
    'NEX_ACTPRIM_BURPEE_CYCLE_V1_SUPPORT_DEPENDENT': 'PROTO_EX_BURPEE',
    'NEX_MECHANIC_LUNGE': 'PROTO_EX_LUNGE',
    'NEX_ACTPRIM_LUNGE_V1': 'PROTO_EX_LUNGE',
    'NEX_MECHANIC_PARTIAL_SQUAT': 'PROTO_EX_SQUAT',
    'NEX_ACTPRIM_PARTIAL_SQUAT_V1': 'PROTO_EX_SQUAT',
    'NEX_ACTPRIM_SINGLE_LEG_SQUAT_V1': 'PROTO_EX_SQUAT',
    'NEX_MECHANIC_HIP_HINGE': 'PROTO_EX_DEADLIFT',
    'NEX_ACTPRIM_HIP_HINGE_V1': 'PROTO_EX_DEADLIFT',
    'NEX_MECHANIC_BALLISTIC_HINGE': 'PROTO_EX_KETTLEBELL_SWING',
    'NEX_MECHANIC_CRAWL_CYCLE_BEAR': 'PROTO_EX_BEAR_CRAWL',
    'NEX_ACTPRIM_CRAWL_CYCLE_V1_BEAR': 'PROTO_EX_BEAR_CRAWL',
    'NEX_MECHANIC_CRAWL_CYCLE_INCHWORM': 'PROTO_EX_MOUNTAIN_CLIMBER',
    'NEX_ACTPRIM_INCHWORM_CYCLE_V1': 'PROTO_EX_MOUNTAIN_CLIMBER',
    'NEX_MECHANIC_JUMPING_JACK_CYCLE': 'PROTO_EX_JUMPING_JACK',
    'NEX_ACTPRIM_JUMPING_JACK_CYCLE_V1': 'PROTO_EX_JUMPING_JACK',
    'NEX_MECHANIC_DIP_CYCLE': 'PROTO_EX_DIP',
    'NEX_ACTPRIM_DIP_CYCLE_V1_SUPPORT_DEPENDENT': 'PROTO_EX_DIP',
    'NEX_MECHANIC_CURL_BILATERAL': 'PROTO_EX_BICEP_CURL',
    'NEX_ACTPRIM_CURL_BILATERAL_V1': 'PROTO_EX_BICEP_CURL',
    'NEX_MECHANIC_VERTICAL_PRESS': 'PROTO_EX_OVERHEAD_PRESS',
    'NEX_MECHANIC_OVERHEAD_REACH_BILATERAL': 'PROTO_EX_OVERHEAD_PRESS',
    'NEX_MECHANIC_VERTICAL_PULL': 'PROTO_EX_PULL_UP',
    'NEX_MECHANIC_ROW_PULL_RIGHT': 'PROTO_EX_PULL_UP',
    'NEX_MECHANIC_CONTRALATERAL_CORE_CYCLE_BIRD_DOG': 'PROTO_EX_BIRD_DOG',
    'NEX_MECHANIC_CONTRALATERAL_CORE_CYCLE_BRIDGE_MARCH':
        'PROTO_EX_GLUTE_BRIDGE',
    'NEX_MECHANIC_CORE_FLEXEXTEND': 'PROTO_EX_SIT_UP',
    'NEX_MECHANIC_BACK_EXTENSION': 'PROTO_EX_GLUTE_BRIDGE',
    'NEX_MECHANIC_KNEE_FLEXEXTEND': 'PROTO_EX_SQUAT',
}


def _proto_alias(clip: str) -> str:
    """Map a resolved vault clip to its proto-cast baked dir when one
    exists — verbatim PROTO_* names pass through untouched."""
    if clip.startswith('PROTO_'):
        return clip
    cand = _PROTO_ALIASES.get(clip)
    if cand and (BAKED_ROOT / cand / 'meta.json').exists():
        return cand
    if clip.startswith('EX_'):
        cand = f'PROTO_{clip}'
        if (BAKED_ROOT / cand / 'meta.json').exists():
            return cand
    return clip


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
    resolved = out.stdout.strip() or None
    return _proto_alias(resolved) if resolved else None


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


BAKED_ROOT = HERE / 'baked'


def _baked_strip(clip: str, spec: dict, seconds: float, fps: int):
    """Pre-baked line-art sprite frames (meshrig/mh_bake.py output) -> RGBA
    tiles. Loops or trims to the requested duration; mirrors on request."""
    from PIL import Image
    variant = spec.get('variant')
    d = (BAKED_ROOT / f'{clip}@{variant}' if variant
         else BAKED_ROOT / clip)
    meta_p = d / 'meta.json'
    if not meta_p.exists() and variant:
        d = BAKED_ROOT / clip          # unbaked variant falls back to base
        meta_p = d / 'meta.json'
    if not meta_p.exists():
        return None
    meta = json.loads(meta_p.read_text())
    src_fps = float(meta.get('fps') or meta.get('sourceFps') or 24)
    frames = sorted(d.glob('f*.png'))
    if not frames:
        return None
    t0 = float(spec.get('t', 0.0))
    n = max(2, int(math.ceil(seconds * fps)))
    step = src_fps / fps
    imgs = []
    src_idx = []
    for i in range(n):
        fi = int(t0 * src_fps + i * step) % len(frames)
        img = Image.open(frames[fi]).convert('RGBA')
        if spec.get('mirror'):
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        imgs.append(img)
        src_idx.append(fi)
    # trim the union transparent margin so callers can bottom-anchor on the
    # figure's lowest real pixel (a plank pose sits above its frame floor)
    box = None
    for img in imgs:
        b = img.getchannel('A').getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]),
                                     max(box[2], b[2]), max(box[3], b[3]))
    if box and (box[0] > 0 or box[1] > 0
                or box[2] < imgs[0].width or box[3] < imgs[0].height):
        pad = max(2, int(imgs[0].width * 0.02))
        box = (max(0, box[0] - pad), max(0, box[1] - pad),
               min(imgs[0].width, box[2] + pad),
               min(imgs[0].height, box[3] + pad))
        imgs = [img.crop(box) for img in imgs]
    if spec.get('visemes') and meta.get('heads'):
        _stamp_mouths(imgs, src_idx, meta['heads'], box or
                      (0, 0, 0, 0), spec, fps)
    return imgs


_MOUTH = None
_VISEMES: dict = {}


def _mouth_shapes():
    global _MOUTH
    if _MOUTH is None:
        p = HERE / 'compiled' / 'mouth_shapes.json'
        _MOUTH = json.loads(p.read_text()) if p.is_file() else {}
    return _MOUTH


def _viseme_at(path: str, t: float) -> str:
    if path not in _VISEMES:
        try:
            vc = json.loads(Path(path).read_text())
            _VISEMES[path] = vc.get('cues') or vc
        except Exception:
            _VISEMES[path] = []
    for c in _VISEMES[path]:
        if c['start'] <= t <= c['end']:
            return c['viseme']
    return 'rest'


def _stamp_mouths(imgs, src_idx, heads, box, spec, fps):
    """Draw the rig's real viseme mouth onto each baked frame at the jaw
    anchor stored in meta['heads']; hidden when the head turns away."""
    from PIL import ImageDraw
    m = _mouth_shapes()
    if not m.get('shapes'):
        return
    vo = float(spec.get('visemeOffset') or 0.0)
    mirror = bool(spec.get('mirror'))
    for i, img in enumerate(imgs):
        h = heads.get(str(src_idx[i]))
        if not h:
            continue
        jx, jy, s_px, fdir, wide = h
        if wide < 0.35:
            continue
        jx -= box[0]; jy -= box[1]
        if mirror:
            jx = img.width - jx
            fdir = -fdir
        name = _viseme_at(spec['visemes'], i / fps + vo).upper()
        loop = m['shapes'].get(name) or m['shapes']['REST']
        ax, ay = m['anchor'][0], m['anchor'][1]
        k = s_px * 0.9                    # rig mouth ~its native meter size
        mx = jx + fdir * s_px * 0.015     # lips sit just fwd/up of the jaw
        my = jy - s_px * 0.035
        pts = [(mx + (p[0] - ax) * k * fdir, my - (p[1] - ay) * k)
               for p in loop]
        d = ImageDraw.Draw(img)
        d.line(pts + [pts[0]], fill=(40, 40, 40, 255),
               width=max(1, int(s_px * 0.008)))


def get_strip(spec: dict, seconds: float, fps: int = 12):
    """(spec, duration) -> list of RGBA frames covering the beat. Cached."""
    clip = resolve_clip(spec)
    if not clip:
        return []
    key = (clip, round(float(seconds), 2), fps,
           json.dumps(spec, sort_keys=True))
    if key in _STRIPS:
        return _STRIPS[key]
    baked = _baked_strip(clip, spec, seconds, fps)
    if baked is not None:
        imgs = baked
    else:
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
        imgs = _rasterize(out)
    # 'still'/'pose': freeze the strip on one frame — the whiteboard-crypto
    # idiom keeps figures posed rather than animating in place
    if imgs and (spec.get('still') or spec.get('pose') is not None):
        i = min(len(imgs) - 1,
                max(0, int(round(float(spec.get('pose', 0.5))
                                 * (len(imgs) - 1)))))
        imgs = [imgs[i]] * len(imgs)
    _STRIPS[key] = imgs
    return imgs
