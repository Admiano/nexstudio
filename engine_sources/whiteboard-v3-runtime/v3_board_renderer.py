"""Whiteboard V3 board renderer — authored-illustration scenes.

Replaces the labeled-rect generic semantic path with the reel's (and the
crypto-explainer genre's) visual language: authored Open Peeps pose
illustrations (shipped in ``assets/open_peeps``, from the approved V3
source bundle's V15/V16 donor lineage) rendered as progressive pen strokes,
filled illustrative props, thought bubbles, motion marks, ground shadows and
sparkles — composed as scenes, not rows of icons. Strokes replay
progressively via the compiler's per-step ``drawPlan`` timing. Everything is
drawn in board world coordinates through the preserved adapter's camera and
rough-stroke helpers, so unmodified preserved modules keep their contract.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw

import whiteboard_pil_adapter as wbp
import svg_paths


# The preserved adapter's paper grain draws near-black specks: ImageDraw on
# RGBA ignores the fill alpha, so its 'subtle' dots always render full ink.
# Wrap it (runtime-only, file untouched) with a pre-blended paper tint.
def _subtle_paper_texture(im, pal, seed):
    import random
    rnd = random.Random(seed)
    d = ImageDraw.Draw(im)
    w, h = im.size
    for _ in range(max(14, int(w * h / 46000))):
        x, y = rnd.randrange(w), rnd.randrange(h)
        d.point((x, y), fill=(238, 235, 228, 255))


wbp._paper_texture = _subtle_paper_texture


# The preserved adapter's board->screen scale uses a fixed 650/760-unit
# reference, which does not match the compiler's actual zone sizes. In 9:16 the
# view overscans ~225px past each zone's top/bottom into the neighbour zone
# only 140px away, so the previous scene's captions bleed into frame; in 1:1 it
# under-covers the zone and clips captions near the edges. Refit the scale to
# the real zone dims (compiler fixes 520x900 for 9:16, 720x700 for 1:1) so the
# frame shows exactly one zone. 16:9 keeps the locked look.
_orig_map_point = wbp._map_point
_ZONE_FIT = {'9:16': (520.0, 900.0), '1:1': (720.0, 700.0)}


def _map_point_zone_fit(pt, cam, ratio, zoom=1.0):
    zwzh = _ZONE_FIT.get(ratio)
    if zwzh is None:
        return _orig_map_point(pt, cam, ratio, zoom)
    w, h = wbp.RATIO_SIZES[ratio]
    scale = min(w / zwzh[0], h / zwzh[1]) * zoom
    return w / 2 + (pt[0] - cam[0]) * scale, h / 2 + (pt[1] - cam[1]) * scale


wbp._map_point = _map_point_zone_fit

_ASSETS = Path(__file__).resolve().parent / 'assets'
_ASSET_DIR = _ASSETS / 'open_peeps'
_PEEPS_DIR = _ASSETS / 'peeps'
_HAND_PATH = _ASSETS / 'hand' / 'drawing-hand.png'
_FONT_DIR = _ASSETS / 'fonts'

# Authored Open Peeps pose library: the V15/V16 donor-lineage files shipped in
# the approved bundle plus the full composable library vendored under
# assets/peeps/. Symbolic pose names used by scene composition resolve through
# this table; a name may also be a direct file under peeps/composed|cast, or a
# dict spec {'pose','hair','face','facial_hair','accessory'} composed at
# runtime from parts — nothing is hard-coded to a fixed cast.
_POSE_FILES = {
    'point': 'composed/standing_PointingFingerWB.svg',
    'gesture': 'composed/standing_EasingWB.svg',
    'walk': 'composed/standing_WalkingWB.svg',
    'hold': 'composed/standing_WalkingFilled.svg',
    'seated': 'composed/sitting_MediumWB.svg',
    'seated_alt': 'composed/sitting_CrossedLegs.svg',
    'crouch': 'composed/sitting_OneLegUpWB.svg',
    'stand': 'composed/standing_RestingWB.svg',
    'cheer': 'composed/standing_RoboDanceWB.svg',
    'think': 'composed/standing_EasingWB.svg',
    'crossed': 'composed/standing_CrossedArmsWB.svg',
    'blazer': 'composed/standing_BlazerPantsWB.svg',
    'casual': 'composed/standing_ShirtPantsWB.svg',
    'doc': 'composed/standing_DocStethoscope.svg',
    'wheelchair': 'composed/sitting_Wheelchair.svg',
    'bike': 'composed/sitting_Bike.svg',
    'authority': 'open_peeps/malik_identity_authority.svg',
}

# Semantic pose bindings — the first table row whose keyword appears in the
# role label wins; 'person' falls through to a deterministic per-label pick so
# every cast looks like a deliberate illustrator's choice, not a default.
_POSE_BINDINGS = [
    (('walk', 'move', 'go', 'travel', 'journey', 'commute', 'arrive', 'step',
      'deliver', 'ship'), 'walk'),
    (('sit', 'desk', 'office', 'waiting', 'waiting room', 'seated', 'reading',
      'watching'), 'seated'),
    (('wheelchair', 'disabled', 'accessibility'), 'wheelchair'),
    (('cycl', 'bike', 'ride'), 'bike'),
    (('doctor', 'nurse', 'medic', 'clinic', 'health', 'patient', 'hospital',
      'pharma'), 'doc'),
    (('celebrat', 'win', 'success', 'party', 'cheer', 'excited', 'launch',
      'happy'), 'cheer'),
    (('think', 'plan', 'idea', 'question', 'decide', 'consider', 'wonder',
      'strategy', 'ponder'), 'gesture'),
    (('cross', 'skeptic', 'boss', 'manager', 'executive', 'investor',
      'suit', 'corporate', 'firm'), 'blazer'),
    (('student', 'kid', 'young', 'casual', 'teen', 'friend'), 'casual'),
    (('crouch', 'inspect', 'check', 'look closer', 'examine'), 'crouch'),
    (('point', 'show', 'present', 'explain', 'teach', 'guide', 'lead'), 'point'),
    (('authority', 'founder', 'leader', 'ceo'), 'authority'),
]

_POSE_ROTATION = ['point', 'stand', 'gesture', 'crossed', 'casual', 'blazer',
                  'walk', 'cheer', 'seated']
_FACE_ROTATION = ['Smile', 'Calm', 'Explaining', 'SmileBig', 'Serious',
                  'Awe', 'Contempt', 'Concerned']
_HAIR_ROTATION = ['Short', 'Medium', 'Bun', 'ShortWavy', 'Long', 'Pomp',
                  'MediumBangs', 'GrayShort', 'ShortCurly', 'FlatTop']

_POSE_CACHE: dict = {}


def _peep_file(name: str) -> Path:
    rel = _POSE_FILES.get(name, name)
    p = _PEEPS_DIR / rel
    if p.exists():
        return p
    p = _ASSET_DIR / rel
    if p.exists():
        return p
    return _PEEPS_DIR / 'composed' / 'standing_RestingWB.svg'


def _part_inner(subdir: str, name: str) -> str:
    p = _PEEPS_DIR / 'parts' / subdir / f'{name}.svg'
    if not p.exists():
        return ''
    s = p.read_text()
    s = s[s.index('>') + 1:]
    s = s[: s.rindex('</svg>')]
    return s


def compose_peep_svg(pose: str, hair='Short', face='Smile', facial_hair=None,
                     accessory=None) -> str:
    """Compose a full peep from vendored parts (react-peeps layout rules)."""
    pose_file = pose if '/' in pose else f'composed/standing_{pose}.svg'
    if not (_PEEPS_DIR / pose_file).exists():
        pose_file = f'composed/{pose}.svg'
    if not (_PEEPS_DIR / pose_file).exists() and pose.endswith('.svg'):
        # explicit vendored path (e.g. open_peeps/*.svg) — use verbatim
        p = _peep_file(pose)
        s = p.read_text()
        body = s[s.index('>') + 1: s.rindex('</svg>')]
        return "<svg xmlns='http://www.w3.org/2000/svg'>" + body + '</svg>'
    if not (_PEEPS_DIR / pose_file).exists():
        # a part pose name like 'WalkingWB' in pose/standing
        for sub in ('pose_standing', 'pose_sitting', 'pose_bust'):
            if (_PEEPS_DIR / 'parts' / sub / f'{pose}.svg').exists():
                body = _part_inner(sub, pose)
                break
        else:
            body = _part_inner('pose_standing', 'RestingWB')
    else:
        s = (_PEEPS_DIR / pose_file).read_text()
        body = s[s.index('>') + 1: s.rindex('</svg>')]
        # composed files already include a head group — drop it (it is the
        # last child of the pose group) so we can rebuild the requested one
        idx = body.rfind("<g transform='translate(225 0)'>")
        if idx != -1:
            body = body[:idx] + '</g>'
    head = []
    h = _part_inner('hair', hair)
    if h:
        head.append(h)
    f = _part_inner('face', face)
    if f:
        head.append("<g transform='translate(159 186)'>" + f + '</g>')
    if facial_hair:
        x = _part_inner('facial_hair', facial_hair)
        if x:
            head.append("<g transform='translate(123 338)'>" + x + '</g>')
    if accessory:
        a = _part_inner('accessories', accessory)
        if a:
            head.append("<g transform='translate(47 241)'>" + a + '</g>')
    return ("<svg xmlns='http://www.w3.org/2000/svg'>" + body +
            "<g transform='translate(225 0)'>" + ''.join(head) + '</g></svg>')


def _figure_elements(spec, facing: int):
    """Resolve a pose spec → (elements, bbox). Spec is a pose name, a file
    under assets/peeps, or a dict {'pose','hair','face','facial_hair',
    'accessory'} composed from parts."""
    key = json.dumps(spec, sort_keys=True) if isinstance(spec, dict) else str(spec)
    ck = (key, facing)
    if ck in _POSE_CACHE:
        return _POSE_CACHE[ck]
    if isinstance(spec, dict):
        svg_text = compose_peep_svg(
            spec.get('pose', 'RestingWB'), spec.get('hair', 'Short'),
            spec.get('face', 'Smile'), spec.get('facial_hair'),
            spec.get('accessory'))
        elements, view_box = svg_paths.elements_from_string(svg_text)
    else:
        elements, view_box = svg_paths.load_svg_strokes(_peep_file(spec))
    _POSE_CACHE[ck] = (elements, view_box)
    return _POSE_CACHE[ck]


def _poly_area(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def _peeps_strokes(pose, facing: int = 1):
    """Normalize an authored pose into unit-space stroke entries.

    Closed paths hatch-fill progressively then draw their outline in ink:
    light fills (skin, face whites) stay paper-toned; large dark fills
    (clothing) take the deep accent; small dark fills (hair, features) stay
    ink — matching the authored asset's tonal structure.
    """
    key = ('strokes', json.dumps(pose, sort_keys=True)
           if isinstance(pose, dict) else pose, facing)
    if key in _POSE_CACHE:
        return _POSE_CACHE[key]
    elements, view_box = _figure_elements(pose, facing)
    if view_box is None:
        # composed-at-runtime specs carry no viewBox — normalize by bbox
        xs = [pt[0] for polys, _, _ in elements for poly in polys for pt in poly]
        ys = [pt[1] for polys, _, _ in elements for poly in polys for pt in poly]
        view_box = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
    x0, y0, w, h = view_box

    def unit(poly):
        return [((x - (x0 + w / 2)) / h * facing, (y - (y0 + h / 2)) / h)
                for x, y in poly]

    strokes = []
    for polys, fill, closed in elements:
        mapped = [unit(p) for p in polys]
        if closed:
            for mp in mapped:
                area = _poly_area(mp)
                cy = sum(y for _, y in mp) / len(mp)
                if fill == '#000000':
                    # dark fills above the torso line are hair/head detail —
                    # keep them ink; body clothing takes the bold accent
                    if cy < -0.20 or area < 0.015:
                        strokes.append((mp, 'inkfill', 1.0, True))
                    else:
                        strokes.append((mp, 'accdeep', 1.0, True))
                elif fill == '#FFFFFF':
                    strokes.append((mp, 'paper', 1.0, True))
                else:
                    strokes.append((mp, 'inkfill', 1.0, True))
        for mp in mapped:
            # coarser strokes read as body contours; finer as detail
            detail = 0.20 if len(mp) < 25 else 0.30
            strokes.append((mp, 'ink', detail))
    _POSE_CACHE[key] = strokes
    return strokes

# ---------------------------------------------------------------------------
# Stroke vocabulary (unit space, ~[-0.5, 0.5] → scaled per slot)
# entry: (points, color, width_scale, fill?)
# color ∈ ink | accent | pale | accfill | paper
# ---------------------------------------------------------------------------

def _P(*pts):
    return [tuple(p) for p in pts]


def _rounded_rect(cx, cy, w, h, r, n=6):
    pts = []
    for cx2, cy2, a0, a1 in (
        (cx + w / 2 - r, cy - h / 2 + r, -90, 0),
        (cx + w / 2 - r, cy + h / 2 - r, 0, 90),
        (cx - w / 2 + r, cy + h / 2 - r, 90, 180),
        (cx - w / 2 + r, cy - h / 2 + r, 180, 270),
    ):
        for i in range(n):
            a = math.radians(a0 + (a1 - a0) * i / (n - 1))
            pts.append((cx2 + r * math.cos(a), cy2 + r * math.sin(a)))
    return pts + [pts[0]]


def _arc(cx, cy, rx, ry, a0, a1, n=20):
    return [
        (cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
         cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))))
        for i in range(n)
    ]


def _ellipse(cx, cy, rx, ry, n=26):
    return _arc(cx, cy, rx, ry, 0, 360, n)


# -- props ------------------------------------------------------------------

PROPS = {
    'envelope': [
        (_rounded_rect(0, 0, 0.72, 0.48, 0.04), 'accfill', 1.0, True),
        (_rounded_rect(0, 0, 0.72, 0.48, 0.04), 'ink', 1.2),
        (_P((-0.36, -0.24), (0, 0.10), (0.36, -0.24)), 'ink', 1.1),
        (_P((-0.16, 0.24), (-0.02, 0.10)), 'ink', 0.9),
        (_P((0.16, 0.24), (0.02, 0.10)), 'ink', 0.9),
    ],
    'document': [
        (_rounded_rect(0, 0, 0.46, 0.60, 0.03), 'paper', 1.0, True),
        (_rounded_rect(0, 0, 0.46, 0.60, 0.03), 'ink', 1.2),
        (_P((-0.14, -0.16), (0.14, -0.16)), 'ink', 1.0),
        (_P((-0.14, -0.02), (0.14, -0.02)), 'pale', 0.9),
        (_P((-0.14, 0.12), (0.14, 0.12)), 'pale', 0.9),
        (_P((-0.14, 0.26), (0.04, 0.26)), 'pale', 0.9),
        (_ellipse(0.14, 0.20, 0.06, 0.06, 14), 'accent', 1.0),
        (_P((0.11, 0.21), (0.135, 0.24), (0.18, 0.15)), 'ink', 0.8),
    ],
    'context': [
        (_rounded_rect(0, 0, 0.62, 0.46, 0.04), 'paper', 1.0, True),
        (_rounded_rect(0, 0, 0.62, 0.46, 0.04), 'ink', 1.2),
        (_P((-0.22, -0.10), (0.22, -0.10)), 'ink', 1.0),
        (_P((-0.22, 0.04), (0.22, 0.04)), 'pale', 0.9),
        (_P((-0.22, 0.18), (0.10, 0.18)), 'pale', 0.9),
        (_P((0.18, 0.10), (0.24, 0.16), (0.18, 0.22), (0.12, 0.16), (0.18, 0.10)), 'accent', 1.0),
    ],
    'stack': [
        (_rounded_rect(-0.20, 0.16, 0.42, 0.20, 0.03), 'paper', 1.0, True),
        (_rounded_rect(-0.20, 0.16, 0.42, 0.20, 0.03), 'ink', 1.0),
        (_rounded_rect(-0.08, -0.04, 0.42, 0.20, 0.03), 'paper', 1.0, True),
        (_rounded_rect(-0.08, -0.04, 0.42, 0.20, 0.03), 'ink', 1.0),
        (_rounded_rect(0.04, -0.24, 0.42, 0.20, 0.03), 'accfill', 1.0, True),
        (_rounded_rect(0.04, -0.24, 0.42, 0.20, 0.03), 'ink', 1.1),
        (_P((0.10, -0.18), (0.22, -0.18)), 'ink', 0.8),
    ],
    'funnel': [
        (_P((-0.32, -0.36), (0.32, -0.36), (0.10, 0.04), (0.10, 0.34), (-0.10, 0.34), (-0.10, 0.04), (-0.32, -0.36)), 'accfill', 1.0, True),
        (_P((-0.32, -0.36), (0.32, -0.36), (0.10, 0.04), (0.10, 0.34), (-0.10, 0.34), (-0.10, 0.04), (-0.32, -0.36)), 'ink', 1.2),
        (_P((-0.22, -0.18), (0.22, -0.18)), 'ink', 0.9),
        (_P((-0.16, -0.04), (0.16, -0.04)), 'ink', 0.8),
    ],
    'tool': [
        # wrench: open jaw, shaft, handle end
        (_arc(-0.14, -0.30, 0.15, 0.15, 250, 130, 16), 'ink', 1.3),
        (_P((-0.22, -0.20), (-0.05, -0.18), (0.02, -0.10)), 'ink', 1.3),
        (_P((-0.14, -0.17), (0.20, 0.36)), 'ink', 1.7),
        (_ellipse(0.22, 0.40, 0.05, 0.05, 12), 'ink', 1.2),
        (_P((-0.26, -0.40), (-0.16, -0.34)), 'accent', 0.8),
    ],
    'check': [
        (_ellipse(0, 0, 0.32, 0.32, 30), 'accfill', 1.0, True),
        (_ellipse(0, 0, 0.32, 0.32, 30), 'accent', 1.3),
        (_P((-0.15, 0.0), (-0.04, 0.13), (0.17, -0.15)), 'ink', 1.5),
    ],
    'chart': [
        (_P((-0.38, -0.34), (-0.38, 0.36), (0.42, 0.36)), 'ink', 1.3),
        (_P((-0.30, 0.26), (-0.30, 0.10)), 'accfill', 2.4),
        (_P((-0.12, 0.26), (-0.12, -0.02)), 'accfill', 2.4),
        (_P((0.06, 0.26), (0.06, -0.14)), 'accfill', 2.4),
        (_P((0.24, 0.26), (0.24, -0.26)), 'accfill', 2.4),
        (_P((-0.30, 0.20), (-0.10, 0.08), (0.06, -0.06), (0.30, -0.26)), 'accent', 1.4),
        (_P((0.30, -0.26), (0.20, -0.24), (0.30, -0.26), (0.28, -0.16)), 'accent', 1.3),
    ],
    'clock': [
        (_ellipse(0, 0, 0.30, 0.30, 30), 'paper', 1.0, True),
        (_ellipse(0, 0, 0.30, 0.30, 30), 'ink', 1.3),
        (_P((0, -0.24), (0, -0.20)), 'ink', 1.0),
        (_P((0, 0.20), (0, 0.24)), 'ink', 1.0),
        (_P((-0.24, 0), (-0.20, 0)), 'ink', 1.0),
        (_P((0.20, 0), (0.24, 0)), 'ink', 1.0),
        (_P((0, 0), (0, -0.16)), 'ink', 1.3),
        (_P((0, 0), (0.13, 0.06)), 'accent', 1.3),
        (_ellipse(0, 0, 0.02, 0.02, 8), 'ink', 1.0, True),
    ],
    'phone': [
        (_rounded_rect(0, 0, 0.32, 0.62, 0.06), 'paper', 1.0, True),
        (_rounded_rect(0, 0, 0.32, 0.62, 0.06), 'ink', 1.2),
        (_P((-0.08, -0.22), (0.08, -0.22)), 'pale', 0.9),
        (_P((-0.10, -0.10), (0.10, -0.10)), 'accfill', 1.8),
        (_P((-0.10, 0.00), (0.10, 0.00)), 'accfill', 1.8),
        (_ellipse(0, 0.24, 0.035, 0.035, 10), 'accent', 0.9),
    ],
    'laptop': [
        (_rounded_rect(0, -0.10, 0.52, 0.34, 0.03), 'accfill', 1.0, True),
        (_rounded_rect(0, -0.10, 0.52, 0.34, 0.03), 'ink', 1.2),
        (_P((-0.32, 0.18), (0.32, 0.18), (0.38, 0.26), (-0.38, 0.26), (-0.32, 0.18)), 'ink', 1.2),
        (_P((-0.16, -0.16), (0.10, -0.16)), 'ink', 0.8),
        (_P((-0.16, -0.06), (0.16, -0.06)), 'ink', 0.8),
        (_P((-0.16, 0.04), (0.02, 0.04)), 'ink', 0.8),
    ],
    'coin': [
        (_ellipse(0, 0, 0.30, 0.30, 30), 'accfill', 1.0, True),
        (_ellipse(0, 0, 0.30, 0.30, 30), 'accent', 1.4),
        (_ellipse(0, 0, 0.22, 0.22, 24), 'accent', 0.8),
        (_P((-0.06, -0.12), (0.08, -0.12), (0.10, -0.02), (-0.02, 0.02), (-0.04, 0.12), (-0.14, 0.12)), 'ink', 1.1),
        (_P((0.02, -0.18), (0.02, 0.18)), 'ink', 0.9),
    ],
    'coins': [
        (_ellipse(-0.14, 0.10, 0.18, 0.18, 24), 'accfill', 1.0, True),
        (_ellipse(-0.14, 0.10, 0.18, 0.18, 24), 'accent', 1.1),
        (_ellipse(0.16, -0.12, 0.22, 0.22, 26), 'accfill', 1.0, True),
        (_ellipse(0.16, -0.12, 0.22, 0.22, 26), 'accent', 1.3),
        (_P((0.10, -0.12), (0.22, -0.12)), 'ink', 1.0),
        (_P((0.16, -0.18), (0.16, -0.06)), 'ink', 1.0),
    ],
    'bank': [
        (_P((-0.36, -0.16), (0, -0.40), (0.36, -0.16), (-0.36, -0.16)), 'accfill', 1.0, True),
        (_P((-0.36, -0.16), (0, -0.40), (0.36, -0.16), (-0.36, -0.16)), 'ink', 1.2),
        (_P((-0.28, -0.16), (-0.28, 0.22)), 'ink', 1.1),
        (_P((-0.10, -0.16), (-0.10, 0.22)), 'ink', 1.1),
        (_P((0.10, -0.16), (0.10, 0.22)), 'ink', 1.1),
        (_P((0.28, -0.16), (0.28, 0.22)), 'ink', 1.1),
        (_P((-0.36, 0.22), (0.36, 0.22)), 'ink', 1.2),
        (_P((-0.40, 0.30), (0.40, 0.30)), 'ink', 1.2),
        (_ellipse(0, -0.10, 0.05, 0.05, 12), 'accent', 1.0),
    ],
    'shield': [
        (_P((0, -0.36), (0.30, -0.26), (0.30, 0.02), (0, 0.36), (-0.30, 0.02), (-0.30, -0.26), (0, -0.36)), 'accfill', 1.0, True),
        (_P((0, -0.36), (0.30, -0.26), (0.30, 0.02), (0, 0.36), (-0.30, 0.02), (-0.30, -0.26), (0, -0.36)), 'ink', 1.2),
        (_P((-0.12, -0.02), (-0.02, 0.10), (0.15, -0.12)), 'accent', 1.4),
    ],
    'gear': [
        (_ellipse(0, 0, 0.16, 0.16, 20), 'paper', 1.0, True),
        (_ellipse(0, 0, 0.16, 0.16, 20), 'ink', 1.1),
        (_ellipse(0, 0, 0.07, 0.07, 14), 'accent', 1.0),
    ] + [
        (_P((0.26 * math.cos(math.radians(t * 45)), 0.26 * math.sin(math.radians(t * 45))),
            (0.16 * math.cos(math.radians(t * 45)), 0.16 * math.sin(math.radians(t * 45)))),
         'ink', 1.0)
        for t in range(8)
    ] + [
        (_ellipse(0.22 * math.cos(math.radians(t * 45 + 22)),
                  0.22 * math.sin(math.radians(t * 45 + 22)), 0.045, 0.045, 8), 'ink', 1.0)
        for t in range(8)
    ],
    'lightbulb': [
        (_arc(0, -0.08, 0.20, 0.20, -50, 230, 24), 'accfill', 1.0, True),
        (_arc(0, -0.08, 0.20, 0.20, -50, 230, 24), 'ink', 1.2),
        (_P((-0.10, 0.14), (0.10, 0.14), (0.08, 0.24), (-0.08, 0.24), (-0.10, 0.14)), 'ink', 1.0),
        (_P((-0.06, 0.30), (0.06, 0.30)), 'ink', 1.0),
        (_P((-0.26, -0.28), (-0.32, -0.34)), 'accent', 0.9),
        (_P((0.26, -0.28), (0.32, -0.34)), 'accent', 0.9),
        (_P((0, -0.36), (0, -0.44)), 'accent', 0.9),
    ],
    'rocket': [
        (_arc(0, -0.10, 0.14, 0.30, 160, 20, 18) + _arc(0, -0.10, 0.14, 0.30, 20, 160, 18), 'accfill', 1.0, True),
        (_arc(0, -0.10, 0.14, 0.30, 160, 20, 18) + _arc(0, -0.10, 0.14, 0.30, 20, 160, 18), 'ink', 1.2),
        (_ellipse(0, -0.14, 0.07, 0.07, 14), 'accent', 1.0),
        (_P((-0.14, 0.10), (-0.24, 0.26), (-0.10, 0.20)), 'ink', 1.1),
        (_P((0.14, 0.10), (0.24, 0.26), (0.10, 0.20)), 'ink', 1.1),
        (_P((-0.06, 0.24), (0, 0.42), (0.06, 0.24)), 'accent', 1.2),
    ],
    'network': [
        (_P((-0.26, 0.14), (0, -0.20), (0.28, 0.10)), 'pale', 1.0),
        (_P((-0.26, 0.14), (0.16, 0.32)), 'pale', 1.0),
        (_P((0, -0.20), (0.16, 0.32)), 'pale', 1.0),
        (_ellipse(-0.26, 0.14, 0.10, 0.10, 14), 'accfill', 1.0, True),
        (_ellipse(-0.26, 0.14, 0.10, 0.10, 14), 'ink', 1.1),
        (_ellipse(0, -0.20, 0.12, 0.12, 14), 'accfill', 1.0, True),
        (_ellipse(0, -0.20, 0.12, 0.12, 14), 'accent', 1.2),
        (_ellipse(0.28, 0.10, 0.10, 0.10, 14), 'accfill', 1.0, True),
        (_ellipse(0.28, 0.10, 0.10, 0.10, 14), 'ink', 1.1),
        (_ellipse(0.16, 0.32, 0.10, 0.10, 14), 'accfill', 1.0, True),
        (_ellipse(0.16, 0.32, 0.10, 0.10, 14), 'ink', 1.1),
    ],
    'target': [
        (_ellipse(0, 0, 0.30, 0.30, 28), 'ink', 1.1),
        (_ellipse(0, 0, 0.20, 0.20, 22), 'accent', 1.0),
        (_ellipse(0, 0, 0.10, 0.10, 16), 'accfill', 1.0, True),
        (_ellipse(0, 0, 0.10, 0.10, 16), 'ink', 1.0),
        (_P((0.10, -0.10), (0.30, -0.32)), 'ink', 1.1),
        (_P((0.30, -0.32), (0.24, -0.30), (0.30, -0.32), (0.28, -0.24)), 'accent', 1.0),
    ],
    'question': [
        (_rounded_rect(0, 0, 0.44, 0.56, 0.05), 'paper', 1.0, True),
        (_rounded_rect(0, 0, 0.44, 0.56, 0.05), 'ink', 1.2),
        (_P((-0.08, -0.18), (0.02, -0.22), (0.10, -0.14), (0.06, -0.04), (0.0, 0.02), (0.0, 0.08)), 'accent', 1.2),
        (_ellipse(0.0, 0.18, 0.025, 0.025, 8), 'accent', 1.0, True),
    ],
    'tile': [
        (_rounded_rect(0, 0, 0.52, 0.52, 0.08), 'accfill', 1.0, True),
        (_rounded_rect(0, 0, 0.52, 0.52, 0.08), 'ink', 1.2),
        (_P((-0.12, 0), (0.12, 0)), 'accent', 1.0),
        (_P((0, -0.12), (0, 0.12)), 'accent', 1.0),
    ],
}


def _robot_strokes():
    return [
        (_rounded_rect(0, -0.02, 0.50, 0.52, 0.12), 'accfill', 1.0, True),
        (_rounded_rect(0, -0.02, 0.50, 0.52, 0.12), 'ink', 1.3),
        (_P((0, -0.28), (0, -0.40)), 'ink', 1.0),
        (_ellipse(0, -0.44, 0.04, 0.04, 12), 'accent', 1.0, True),
        (_rounded_rect(-0.13, -0.10, 0.10, 0.12, 0.04), 'paper', 0.9, True),
        (_rounded_rect(-0.13, -0.10, 0.10, 0.12, 0.04), 'ink', 0.9),
        (_rounded_rect(0.13, -0.10, 0.10, 0.12, 0.04), 'paper', 0.9, True),
        (_rounded_rect(0.13, -0.10, 0.10, 0.12, 0.04), 'ink', 0.9),
        (_ellipse(-0.13, -0.10, 0.03, 0.04, 10), 'accent', 0.9, True),
        (_ellipse(0.13, -0.10, 0.03, 0.04, 10), 'accent', 0.9, True),
        (_arc(0, 0.08, 0.12, 0.10, 20, 160, 12), 'ink', 1.0),
        (_P((-0.25, -0.02), (-0.34, -0.02)), 'ink', 1.0),
        (_P((0.25, -0.02), (0.34, -0.02)), 'ink', 1.0),
        (_ellipse(-0.36, -0.02, 0.05, 0.08, 10), 'ink', 0.9),
        (_ellipse(0.36, -0.02, 0.05, 0.08, 10), 'ink', 0.9),
        (_P((-0.20, 0.22), (-0.20, 0.30)), 'ink', 1.0),
        (_P((0.20, 0.22), (0.20, 0.30)), 'ink', 1.0),
    ]


def _character_strokes(pose='point', facing=1):
    """Authored Open Peeps pose — real illustrated figure, not a stick figure."""
    return _peeps_strokes(pose, facing)


def _bubble_strokes():
    cloud = []
    for cx, cy, r in ((-0.20, 0.02, 0.13), (-0.05, -0.10, 0.15), (0.12, -0.06, 0.13),
                      (0.20, 0.08, 0.11), (0.0, 0.12, 0.14)):
        cloud += _arc(cx, cy, r, r, -30, 210, 10)
    return [
        (cloud, 'ink', 1.0),
        (_ellipse(0.30, 0.24, 0.030, 0.030, 8), 'ink', 0.9),
        (_ellipse(0.38, 0.34, 0.020, 0.020, 8), 'ink', 0.9),
    ]


def _ground_shadow_strokes():
    """Loose grounding shadow under a figure's feet — whiteboard convention."""
    s = _arc(0, 0, 0.34, 0.045, 0, 360, 30)
    return [
        ([p for p in s if p[1] > -0.002] + [(s[-1][0], 0.0), (s[0][0], 0.0)], 'pale', 1.0, True),
        (_arc(0, 0, 0.34, 0.045, 10, 170, 18), 'ink', 0.7),
    ]


def _ping_strokes():
    """Notification ping arcs — signals a message/request arriving."""
    return [
        (_arc(0.30, -0.26, 0.10, 0.10, -70, 30, 10), 'accent', 1.0),
        (_arc(0.30, -0.26, 0.18, 0.18, -70, 30, 12), 'accent', 0.9),
        (_ellipse(0.30, -0.26, 0.030, 0.030, 10), 'accent', 1.0, True),
    ]


def _motion_marks_strokes():
    """Action dashes radiating near a figure's gesturing hand."""
    return [
        (_P((0.52, -0.30), (0.60, -0.36)), 'accent', 0.9),
        (_P((0.55, -0.20), (0.65, -0.22)), 'accent', 0.9),
        (_P((0.52, -0.10), (0.60, -0.06)), 'accent', 0.9),
    ]


def _sparkle_strokes():
    return [
        (_P((-0.40, -0.30), (-0.40, -0.18)), 'accent', 0.9),
        (_P((-0.46, -0.24), (-0.34, -0.24)), 'accent', 0.9),
        (_P((0.38, 0.30), (0.38, 0.42)), 'accent', 0.9),
        (_P((0.32, 0.36), (0.44, 0.36)), 'accent', 0.9),
        (_P((0.42, -0.38), (0.48, -0.32)), 'accent', 0.9),
        (_P((0.48, -0.38), (0.42, -0.32)), 'accent', 0.9),
    ]


# ---------------------------------------------------------------------------
# Elite drawing machinery — taper, hatching, hand, lettering
# ---------------------------------------------------------------------------

def _taper_profile(i: int, n: int) -> float:
    """Marker-tip width profile: ramps in fast, rides full, eases to a taper."""
    if n < 4:
        return 1.0
    t = i / (n - 1)
    ramp_in = min(1.0, t / 0.10)
    ramp_out = min(1.0, (1 - t) / 0.22)
    return max(0.28, min(ramp_in, ramp_out))


def _taper_line(layer, pts, color, width, seed, rough=.3, p=1.0):
    """Progressive tapered stroke: variable-width ribbon along the polyline.

    Returns the screen-space pen tip (for the drawing hand) when the stroke
    is mid-draw, else the final point.
    """
    pts = wbp._partial(pts, p)
    if len(pts) < 2:
        return pts[-1] if pts else None
    rpts = wbp._rough_points(pts, seed, max(.25, width * rough * .46))
    n = len(rpts)
    # ribbon edges offset along the local normal, width tapered by arc position
    left, right = [], []
    for i, (x, y) in enumerate(rpts):
        a = rpts[i - 1] if i else rpts[0]
        b = rpts[i + 1] if i < n - 1 else rpts[-1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        hw = width * _taper_profile(i, n) / 2
        left.append((x - dy / ln * hw, y + dx / ln * hw))
        right.append((x + dy / ln * hw, y - dx / ln * hw))
    d = ImageDraw.Draw(layer, 'RGBA')
    d.polygon(left + right[::-1], fill=color)
    rr = width * _taper_profile(n - 1, n) / 2
    x, y = rpts[-1]
    d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=color)
    return rpts[-1]


def _hatch_segments(poly, spacing=0.07, angle_deg=45.0):
    """Diagonal hatch segments clipped to a closed unit-space polygon.

    Scribble-fill the region like a marker shading pass: even-odd interior
    segments of parallel lines through the polygon bbox.
    """
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if x1 - x0 < 1e-4 or y1 - y0 < 1e-4:
        return []
    a = math.radians(angle_deg)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx  # hatch normal sweeps the bbox diagonal
    c0, c1 = x0 * nx + y0 * ny, x1 * nx + y1 * ny
    d0, d1 = x0 * dx + y0 * dy, x1 * dx + y1 * dy
    lo, hi = min(c0, c1, x1 * nx + y0 * ny, x0 * nx + y1 * ny), \
        max(c0, c1, x1 * nx + y0 * ny, x0 * nx + y1 * ny)
    # signed crossings along each hatch line
    def crossings(t):
        ox, oy = nx * t, ny * t  # point on the hatch line at normal dist t
        out = []
        for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
            sa = (ax - ox) * nx + (ay - oy) * ny
            sb = (bx - ox) * nx + (by - oy) * ny
            if (sa < 0) == (sb < 0) or abs(sb - sa) < 1e-9:
                continue
            f = -sa / (sb - sa)
            out.append((ax + (bx - ax) * f - ox) * dx
                       + (ay + (by - ay) * f - oy) * dy)
        out.sort()
        return [(out[i], out[i + 1]) for i in range(0, len(out) - 1, 2)]
    segs = []
    t = lo + spacing / 2
    while t < hi:
        for u0, u1 in crossings(t):
            if u1 - u0 > spacing * 0.4:
                segs.append([(nx * t + dx * u0, ny * t + dy * u0),
                             (nx * t + dx * u1, ny * t + dy * u1)])
        t += spacing
    return segs


# -- hand-lettered strokes (Hershey single-stroke data, public domain) -------

_HERSHEY = None


def _hershey():
    global _HERSHEY
    if _HERSHEY is None:
        f = _FONT_DIR / 'hershey_lite.json'
        _HERSHEY = json.loads(f.read_text()) if f.exists() else {}
    return _HERSHEY


def text_strokes(text: str, origin, height: float, color='ink', wscale=1.0):
    """Hand-lettered text as progressive pen strokes (board coordinates).

    Each glyph's single-stroke polylines map onto the baseline at `origin`;
    glyphs advance by their authored bearings. Returns stroke entries in
    absolute board space (drawn without the unit-space slot transform).
    """
    glyphs = _hershey()
    if not glyphs:
        return []
    scale = height / 1.0
    strokes = []
    x = origin[0]
    for ch in text:
        g = glyphs.get(str(ord(ch)))
        if g is None:
            x += height * 0.34
            continue
        bb = g['bounding_box']
        lx, rx = bb[0][0], bb[1][0]
        for line in g['strokes']:
            pts = [(x + (px - lx) * scale,
                    origin[1] + py * scale) for px, py in line]
            if len(pts) >= 2:
                strokes.append((pts, color, wscale, False, True))
        x += (rx - lx) * scale + height * 0.10
    return strokes


def _text_bottom(text: str, height: float) -> float:
    """Distance from origin to the lowest ink point (clears descenders)."""
    glyphs = _hershey()
    m = 0.0
    for ch in text:
        g = glyphs.get(str(ord(ch)))
        if g:
            m = max(m, g['bounding_box'][1][1])
    return m * height


def text_width(text: str, height: float) -> float:
    glyphs = _hershey()
    x = 0.0
    for ch in text:
        g = glyphs.get(str(ord(ch)))
        x += ((g['bounding_box'][1][0] - g['bounding_box'][0][0]) * height
              + height * 0.10) if g else height * 0.34
    return x


# -- drawing hand ------------------------------------------------------------

_HAND_IMG = None
_HAND_NIB = (105, 70)  # marker tip inside the sprite (px, source image space)


def _hand():
    global _HAND_IMG
    if _HAND_IMG is None and _HAND_PATH.exists():
        _HAND_IMG = Image.open(_HAND_PATH).convert('RGBA')
    return _HAND_IMG


def _overlay_hand(frame: Image.Image, tip, ratio: str, wobble: float = 0.0):
    """Composite the marker hand so the nib sits on the live pen tip."""
    hand = _hand()
    if hand is None or tip is None:
        return frame
    w, h = wbp.RATIO_SIZES[ratio]
    scale = (h * 0.24) / hand.height
    hw, hh = int(hand.width * scale), int(hand.height * scale)
    img = hand.resize((hw, hh), Image.LANCZOS)
    nx, ny = _HAND_NIB[0] * scale, _HAND_NIB[1] * scale
    # wobble: the hand breathes with the stroke, ±1.5px
    dx = tip[0] - nx + math.sin(wobble) * 1.5
    dy = tip[1] - ny + math.cos(wobble * 1.3) * 1.2
    frame.paste(img, (int(dx), int(dy)), img)
    return frame


# ---------------------------------------------------------------------------
# Concept → drawing
# ---------------------------------------------------------------------------

_ICON_KEYWORDS = {
    'person': ('person', 'people', 'customer', 'user', 'human', 'operator',
               'worker', 'courier', 'staff', 'client', 'buyer', 'seller',
               'employee', 'man', 'woman', 'child', 'kid', 'team', 'audience',
               'investor', 'trader', 'founder', 'developer', 'miner', 'holder',
               'member', 'doctor', 'nurse', 'patient', 'teacher', 'student',
               'executive', 'manager', 'boss', 'ceo', 'farmer', 'artist',
               'musician', 'athlete', 'engineer', 'lawyer', 'accountant',
               'designer', 'writer', 'analyst', 'consultant', 'driver',
               'chef', 'scientist', 'professor', 'builder', 'contractor',
               'veterinarian', 'vet', 'firefighter', 'logger', 'lumberjack',
               'plumber', 'electrician', 'mechanic', 'pilot', 'soldier',
               'sailor', 'fisherman', 'photographer', 'waiter', 'barber',
               'coach', 'referee', 'guard', 'officer', 'police', 'detective',
               'janitor', 'cleaner', 'baker', 'butcher', 'cashier', 'welder',
               'carpenter', 'mason', 'roofer', 'painter', 'technician',
               'programmer', 'marketer', 'salesman', 'broker', 'advisor',
               'therapist', 'surgeon', 'pharmacist', 'radiologist', 'dentist',
               'dentist', 'ranger', 'forester', 'biologist', 'operator',
               'inspector', 'supervisor', 'dispatcher', 'conductor',
               'attorney', 'judge', 'reporter', 'editor', 'author',
               'barista', 'server', 'bartender', 'host', 'guide',
               'beekeeper', 'commuter', 'passenger', 'rider', 'tourist',
               'traveler', 'hiker', 'camper', 'gardener', 'rancher',
               'herder', 'shepherd', 'fisher', 'hunter', 'swimmer',
               'runner', 'cyclist', 'dancer', 'singer', 'actor',
               'shopper', 'vendor', 'merchant', 'consumer', 'guest',
               'resident', 'visitor', 'pedestrian', 'jogger', 'clerk',
               'agent owner', 'customer agent'),
    'agent': ('agent', 'robot', 'ai', 'bot', 'assistant', 'android',
              'chatbot', 'automation bot'),
    'envelope': ('request', 'mail', 'email', 'message', 'letter', 'send', 'ticket',
                 'notification', 'inbox', 'invite'),
    'document': ('document', 'report', 'file', 'form', 'contract', 'invoice',
                 'proposal', 'brief', 'order', 'application', 'paper', 'memory',
                 'card', 'record', 'history', 'log', 'receipt', 'whitepaper',
                 'ledger', 'statement', 'guide', 'manual'),
    'context': ('context', 'details', 'attached', 'attachment', 'summary', 'profile',
                'account', 'dashboard', 'portfolio'),
    'stack': ('queue', 'routine', 'stack', 'backlog', 'cases', 'tickets', 'batch',
              'list', 'docs', 'papers', 'blocks'),
    'funnel': ('funnel', 'filter', 'triage', 'sort', 'screen', 'pipeline'),
    'tool': ('tool', 'wrench', 'settings', 'fix', 'repair', 'utility', 'configure'),
    'check': ('check', 'validate', 'done', 'verified', 'approve', 'success',
              'complete', 'confirm', 'correct'),
    'chart': ('chart', 'result', 'metric', 'growth', 'graph', 'measure', 'data',
              'response time', 'kpi', 'trend', 'performance', 'revenue', 'price',
              'market', 'profit', 'roi', 'analytics', 'stats'),
    'clock': ('time', 'clock', 'wait', 'sla', 'deadline', 'schedule', 'calendar',
              'delay', 'duration'),
    'phone': ('phone', 'smartphone', 'mobile', 'call', 'app', 'sms'),
    'laptop': ('laptop', 'computer', 'workstation', 'website',
               'software', 'browser'),
    'coin': ('coin', 'money', 'payment', 'cash', 'token', 'crypto', 'bitcoin',
             'currency', 'dollar', 'fund', 'fee', 'cost', 'pay', 'salary',
             'reward', 'stake', 'deposit'),
    'coins': ('savings', 'wealth', 'funds', 'capital', 'treasury', 'earnings',
              'balance', 'wallet', 'pool', 'liquidity'),
    'bank': ('bank', 'institution', 'government', 'exchange', 'company', 'office',
             'headquarters', 'organization', 'vault', 'custodian', 'hospital',
             'pharmacy', 'clinic', 'school', 'university', 'store', 'shop'),
    'shield': ('shield', 'security', 'protection', 'privacy', 'insurance',
               'compliance', 'audit', 'trust', 'safety', 'secure'),
    'gear': ('automation', 'process', 'workflow', 'engine', 'mechanism', 'machine',
             'protocol', 'algorithm', 'mining', 'gear'),
    'lightbulb': ('idea', 'insight', 'learn', 'knowledge', 'solution', 'innovation',
                  'discovery', 'strategy', 'tip', 'answer', 'lightbulb'),
    'rocket': ('launch', 'fast', 'speed', 'scale', 'boost', 'start', 'deploy',
               'release', 'moon'),
    'network': ('network', 'blockchain', 'chain', 'nodes', 'distributed',
                'community', 'ecosystem', 'connection', 'peer', 'web3', 'defi',
                'internet', 'cloud'),
    'target': ('target', 'goal', 'objective', 'aim', 'focus', 'accuracy',
               'precision', 'hit'),
    'question': ('hard cases', 'uncertain', 'unknown', 'question', 'exception',
                 'edge case', 'risk', 'problem', 'issue', 'challenge', 'why',
                 'mystery'),
}

_PERSON_AGENT_PREFIXES = ('human', 'support', 'customer', 'live', 'service', 'real')

# Verb/difference vocabulary — pinned Tabler icons for action and contrast
# words, so 'response time drops' draws a falling trend rather than whatever
# the object keyword would have matched. Curated beats fuzzy here.
_VERB_TABLE = {
    'drop': 'trending-down', 'drops': 'trending-down', 'fall': 'trending-down',
    'falls': 'trending-down', 'crash': 'trending-down', 'decline': 'trending-down',
    'decrease': 'trending-down', 'lower': 'trending-down', 'sink': 'trending-down',
    'cheaper': 'discount', 'cut': 'discount', 'discount': 'discount',
    'rise': 'trending-up', 'rises': 'trending-up', 'grow': 'trending-up',
    'grows': 'trending-up', 'growth': 'trending-up', 'increase': 'trending-up',
    'higher': 'trending-up', 'climb': 'trending-up', 'surge': 'trending-up',
    'boost': 'rocket', 'accelerate': 'rocket',
    'faster': 'bolt', 'instant': 'bolt', 'quick': 'bolt', 'instantly': 'bolt',
    'vs': 'scale', 'versus': 'scale', 'compare': 'scale', 'compared': 'scale',
    'tradeoff': 'scale', 'balance': 'scale',
    'difference': 'arrows-diff', 'gap': 'arrows-diff',
    'instead': 'switch-3', 'rather': 'switch-3',
    'replace': 'replace', 'replaces': 'replace', 'swap': 'exchange',
    'exchange': 'exchange', 'switch': 'switch-3', 'migrate': 'arrows-left-right',
    'transfer': 'arrows-left-right',
    'benefit': 'award', 'benefits': 'award', 'advantage': 'award',
    'gain': 'stars', 'value': 'stars', 'quality': 'stars',
    'ownership': 'certificate', 'owner': 'id', 'equity': 'percentage',
    'stake': 'percentage', 'share': 'percentage',
    'dividend': 'pig-money', 'dividends': 'pig-money', 'yield': 'pig-money',
    'payout': 'gift', 'reward': 'gift',
    'transparent': 'eye', 'transparency': 'eye-check', 'visible': 'eye',
    'programmable': 'settings-automation', 'automated': 'settings-automation',
    'automatic': 'settings-automation',
    'save': 'pig-money', 'saves': 'pig-money', 'saving': 'pig-money',
    'earn': 'coin', 'earns': 'coin', 'earnings': 'coin',
    'cost': 'receipt-2', 'costs': 'receipt-2', 'fee': 'receipt-2',
    'fees': 'receipt-2', 'price': 'receipt-2',
}


def _verb_icon(concept: str):
    """Pinned tabler icon for a phrase carrying an action/contrast word.
    Runs after actor detection so 'driver earns more' keeps its person."""
    words = [w for w in re.findall(r"[a-z]+", str(concept).lower())]
    for w in words:
        if w in _VERB_TABLE and _VERB_TABLE[w] in _tabler()[0]:
            return ('tabler', _VERB_TABLE[w])
    return None

# ---------------------------------------------------------------------------
# Tabler vocabulary — 4,964 stroke-style icons (MIT) searched by name/tags,
# so any domain (animals, transport, forestry, health) resolves to a real
# drawing instead of a placeholder tile.
# ---------------------------------------------------------------------------
_TABLER_NODES_PATH = _ASSETS / 'icons' / 'tabler' / 'tabler-nodes-outline.json'
_TABLER_META_PATH = _ASSETS / 'icons' / 'tabler' / 'icons.json'
_TABLER = None

# UI-furniture glyphs (menus, layout grids, control decorations) must never
# serve as the drawing for a real-world concept.
_TABLER_JUNK_PREFIXES = (
    'menu', 'layout-', 'grid-', 'table-', 'row-', 'column-', 'sort-',
    'math-', 'square-', 'letter-', 'spacing-', 'text-', 'align-',
    'bracket', 'header', 'separator', 'section', 'breadcrumb', 'navbar',
    'whitespace', 'marquee', 'article', 'typography', 'input-', 'forms',
    'list-', 'box-model', 'clipboard-', 'copyleft', 'copyright',
    'help', 'info-', 'file-', 'folder', 'device-', 'app-window',
)


def _tabler():
    global _TABLER
    if _TABLER is None:
        nodes = json.loads(_TABLER_NODES_PATH.read_text())
        meta = json.loads(_TABLER_META_PATH.read_text())
        index = {}
        for name, m in meta.items():
            toks = set(name.split('-'))
            toks |= {str(t).lower() for t in (m.get('tags') or [])}
            if m.get('category'):
                toks.add(str(m['category']).lower())
            index[name] = toks
        _TABLER = (nodes, index)
    return _TABLER


def _tabler_lookup(concept: str):
    hit = _icon_lookup(concept)
    return hit[2] if hit and hit[1] == 'tabler' else None


_ICON_INDEX = None
_SYN = None


def _synonyms():
    """Vendored WordNet-derived lemma relations (assets/semantic/synonyms.json) —
    deterministic, no runtime dependency."""
    global _SYN
    if _SYN is None:
        p = _ASSETS / 'semantic' / 'synonyms.json'
        _SYN = json.loads(p.read_text()) if p.is_file() else {}
    return _SYN


def _expanded(words):
    """(direct tokens incl. singulars, synonym-expanded tokens)."""
    syn = _synonyms()
    direct = set(words) | {_singular(w) for w in words}
    expanded = set(direct)
    for w in direct:
        expanded |= set(syn.get(w, ())[:6])
    return direct, expanded


def _icon_index():
    """Merged icon index across tabler / phosphor / fluent: {(dir, slug): toks}."""
    global _ICON_INDEX
    if _ICON_INDEX is None:
        idx = {}
        _nodes, tix = _tabler()
        for name, toks in tix.items():
            idx[('tabler', name)] = set(toks)
        for f in (_ASSETS / 'phosphor').glob('*.svg'):
            idx[('phosphor', f.stem)] = set(f.stem.split('-'))
        fx = _ASSETS / 'fluent' / 'index.json'
        if fx.is_file():
            for slug, m in json.loads(fx.read_text()).items():
                toks = set(slug.split('-')) | set(m.get('keywords', ()))
                toks |= set(str(m.get('group', '')).lower().replace('&', ' ').split())
                idx[('fluent', slug)] = {t for t in toks if len(t) > 1}
        _ICON_INDEX = idx
    return _ICON_INDEX


def _icon_lookup(concept: str, exclude=None):
    """Best icon for a free-text concept across all vendored icon sets,
    or None when nothing fits. Returns ('icon', dir, slug)."""
    words = [w for w in re.findall(r"[a-z0-9]+", str(concept).lower())
             if len(w) > 2]
    if not words:
        return None
    index = _icon_index()
    dashed = '-'.join(words)
    if (('tabler', dashed) in index
            and not (exclude and ('icon', 'tabler', dashed) in exclude)):
        return ('icon', 'tabler', dashed)
    direct, expanded = _expanded(words)
    best, best_score = None, 0.0
    for (d, name), toks in index.items():
        if exclude and ('icon', d, name) in exclude:
            continue
        if d == 'tabler' and (
                name.endswith('-off') or name in ('old', 'new', 'current')
                or name.startswith(('brand-', 'steam', 'tiktok', 'meta'))
                or (name.startswith(_TABLER_JUNK_PREFIXES)
                    and name != 'list-check')):
            continue
        name_parts = set(name.split('-'))
        score = 0.0
        for w in direct & toks:
            score += (5 if w in name_parts else 3) + 0.15 * len(w)
        syn_hits = (expanded & toks) - direct
        score += 1.8 * len(syn_hits)          # meaning-level matches, half weight
        score += len(direct & name_parts)     # prefer covering more of the phrase
        score += 1.5 * len(direct & toks) / len(direct)
        if d == 'tabler':
            score += 0.15                     # cleanest stroke style wins ties
        score -= len(name) * 0.04
        if score > best_score:
            best, best_score = ('icon', d, name), score
    return best if best_score >= 3.5 else None


def _shift_strokes(strokes, scale, dx, dy, color=None):
    out = []
    for st in strokes:
        pts = [(x * scale + dx, y * scale + dy) for x, y in st[0]]
        out.append(tuple([pts, color or st[1]] + list(st[2:])))
    return out


def _shape_to_d(tag: str, a: dict) -> str:
    if tag == 'line':
        return f"M{a.get('x1',0)} {a.get('y1',0)}L{a.get('x2',0)} {a.get('y2',0)}"
    if tag == 'circle':
        cx, cy, r = (float(a.get(k, 0)) for k in ('cx', 'cy', 'r'))
        return (f"M{cx - r} {cy}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 "
                f"{-2 * r} 0")
    if tag in ('rect',):
        x, y = float(a.get('x', 0)), float(a.get('y', 0))
        w, h = float(a.get('width', 0)), float(a.get('height', 0))
        rx = float(a.get('rx', 0))
        if rx:
            return (f"M{x + rx} {y}h{w - 2 * rx}a{rx} {rx} 0 0 1 {rx} {rx}"
                    f"v{h - 2 * rx}a{rx} {rx} 0 0 1 {-rx} {rx}h{-w + 2 * rx}"
                    f"a{rx} {rx} 0 0 1 {-rx} {-rx}v{-h + 2 * rx}"
                    f"a{rx} {rx} 0 0 1 {rx} {-rx}")
        return f"M{x} {y}h{w}v{h}h{-w}Z"
    if tag in ('polyline', 'polygon'):
        seq = str(a.get('points', '')).replace(',', ' ').split()
        d = 'M' + ' L'.join(f"{seq[i]} {seq[i + 1]}"
                            for i in range(0, len(seq) - 1, 2))
        return d + ('Z' if tag == 'polygon' else '')
    if tag == 'ellipse':
        cx, cy, rx, ry = (float(a.get(k, 0)) for k in ('cx', 'cy', 'rx', 'ry'))
        return (f"M{cx - rx} {cy}a{rx} {ry} 0 1 0 {2 * rx} 0a{rx} {ry} 0 1 0 "
                f"{-2 * rx} 0")
    return ''


_TABLER_STROKE_CACHE: dict = {}


def _tabler_strokes(name: str):
    """Unit-space strokes for a tabler icon; decorative sub-paths get accent."""
    if name in _TABLER_STROKE_CACHE:
        return _TABLER_STROKE_CACHE[name]
    nodes, _ = _tabler()
    ds: list[str] = []

    def collect(el):
        if isinstance(el, list) and el:
            if el[0] == 'path':
                ds.append(el[1].get('d', ''))
            elif el[0] in ('circle', 'rect', 'line', 'polyline', 'polygon',
                           'ellipse'):
                ds.append(_shape_to_d(el[0], el[1]))
            else:
                for ch in el:
                    collect(ch)

    collect(nodes.get(name) or [])
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
           + ''.join(f"<path d='{d}'/>" for d in ds if d) + '</svg>')
    elements, _vb = svg_paths.elements_from_string(svg)
    strokes = []
    for polys, _fill, _closed in elements:
        for poly in polys:
            if len(poly) < 2:
                continue
            strokes.append(([(x / 24.0 - 0.5, y / 24.0 - 0.5) for x, y in poly],
                            'ink', 0.95, False))
    # accent the small decorative details (eyes, ticks, dots) — never big shapes
    if len(strokes) > 3:
        for i, (poly, _c, w, _f) in enumerate(strokes):
            bw = max(p[0] for p in poly) - min(p[0] for p in poly)
            bh = max(p[1] for p in poly) - min(p[1] for p in poly)
            if bw < 0.16 and bh < 0.16:
                strokes[i] = (poly, 'accent', w * 1.15, False)
    _TABLER_STROKE_CACHE[name] = strokes
    return strokes


_STAT_RE = re.compile(r"^[\$£€]?\s*\d[\d,\.]*\s*(%|[kmbx×+]|[a-z]{1,7})?\.?$",
                      re.I)
_CUSTOM_DIR = _ASSETS / 'custom'
# License-clean illustration collections (all stroke-friendly vector art):
#   custom/   bespoke commissioned or generated sketches (vtracer output)
#   ctrlv/    1019 CC0 vignette illustrations, tag-indexed
#   flowbite/ 54 MIT scene illustrations (light/outline set)
#   doodles/  31 CC0 sketchy figure illustrations (Open Doodles)
_ILLUST_DIRS = ('custom', 'ctrlv', 'flowbite', 'doodles')


def _slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def _dir_strokes(dir_name: str, slug: str):
    """Unit-space strokes for an SVG in assets/<dir_name>/<slug>.svg.
    Ink-filled elements hatch; paper/secondary fills draw as outlines only
    so the art reads on the board's paper."""
    path = _ASSETS / dir_name / f'{slug}.svg'
    if not path.is_file():
        return None
    elements, vb = svg_paths.elements_from_string(path.read_text())
    polys = [p for ps, _f, _c in elements for p in ps if len(p) >= 2]
    if not polys:
        return None
    xs = [p[0] for pl in polys for p in pl]
    ys = [p[1] for pl in polys for p in pl]
    # normalize by drawn geometry, not viewBox — library art carries big
    # empty margins that would shrink the drawing inside its slot
    vbw = max(xs) - min(xs) or 1
    vbh = max(ys) - min(ys) or 1
    x0 = min(xs)
    y0 = min(ys)
    side = max(vbw, vbh, 1)  # normalize by the long edge, keep aspect
    ox = (side - vbw) / 2
    oy = (side - vbh) / 2
    # promote one mid-size closed ink fill to accent — the signature blue
    # pop inside a vignette (giant background fills are skipped)
    accent_el = -1
    if dir_name != 'custom':
        filled = [(i, (max(p[0] for p in pls[0])
                       - min(p[0] for p in pls[0]))
                  * (max(p[1] for p in pls[0]) - min(p[1] for p in pls[0])))
                  for i, (pls, f, c) in enumerate(elements)
                  if c and str(f).startswith('#')
                  and f not in ('#F5F0E4', '#FFFFFF', '#fff', 'white')]
        if filled:
            biggest = max(filled, key=lambda t: t[1])
            total_area = vbw * vbh or 1
            if biggest[1] <= total_area * 0.40:
                accent_el = biggest[0]
    strokes = []
    # library vignettes draw at a lighter pen weight than bespoke art —
    # dense multi-path art at full width reads as a blob beside the icon set
    weight = 0.95 if dir_name == 'custom' else 0.5
    hatch_ok = dir_name == 'custom'
    for ei, (polys_el, fill, closed) in enumerate(elements):
        if fill in ('#F5F0E4', '#FFFFFF', '#fff', 'white'):
            color, hatch = 'ink', False
        elif ei == accent_el:
            color, hatch = 'accent', True
        elif str(fill).startswith('#') and fill.lower() not in (
                'none', 'default'):
            color, hatch = 'ink', closed and hatch_ok
        else:
            color, hatch = 'ink', False
        for poly in polys_el:
            if len(poly) < 2:
                continue
            strokes.append(([( (x - x0 + ox) / side - 0.5,
                              (y - y0 + oy) / side - 0.5) for x, y in poly],
                            color, weight, hatch))
    return strokes or None


def _custom_strokes(slug: str):
    """Unit-space strokes for a bespoke SVG in assets/custom/<slug>.svg.
    These are commissioned/generated illustrations — they win over every
    generic vocabulary path."""
    return _dir_strokes('custom', slug)


_CTRLV_INDEX: dict = None


def _ctrlv_index():
    global _CTRLV_INDEX
    if _CTRLV_INDEX is None:
        path = _ASSETS / 'ctrlv' / 'index.json'
        _CTRLV_INDEX = json.loads(path.read_text()) if path.is_file() else {}
    return _CTRLV_INDEX


_ILLUST_DIRS_ = {'ctrlv', 'flowbite', 'doodles'}


def _illust_ink(dir_name: str, slug: str) -> float:
    """Normalized total stroke length — tiny/sparse art reads as fragments
    at icon scale, so weak geometry must lose to the icon vocabularies."""
    try:
        elements, _vb = svg_paths.elements_from_string(
            (_ASSETS / dir_name / f'{slug}.svg').read_text())
    except Exception:
        return 0.0
    pts = [pt for polys, _f, _c in elements for pl in polys for pt in pl]
    if len(pts) < 6:
        return 0.0
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    side = max(max(xs) - min(xs), max(ys) - min(ys), 1)
    total = 0.0
    for polys, _f, _c in elements:
        for pl in polys:
            total += sum(math.hypot(b[0] - a[0], b[1] - a[1])
                        for a, b in zip(pl, pl[1:]))
    return total / side


def _illust_lookup(concept: str, exclude=None):
    """(dir, slug) for the best matching vignette illustration, or None.
    Scene-level art beats a flat icon only when the match is strong — the
    label's main noun must land in the art's slug/title/tags — and the art
    must carry enough ink to read at icon scale."""
    words = [w for w in re.findall(r"[a-z0-9]+", str(concept).lower())
             if len(w) > 2]
    if not words:
        return None
    wset = set(words) | {_singular(w) for w in words}
    main = {_singular(words[-1]), words[-1]} | {w for w in wset if len(w) >= 5}
    best, best_score = None, 0.0
    candidates = []
    for slug, meta in _ctrlv_index().items():
        slug_parts = set(slug.split('-'))
        toks = slug_parts | set(meta.get('tags') or [])
        toks |= set(re.findall(r'[a-z0-9]+', (meta.get('title') or '').lower()))
        candidates.append(('ctrlv', slug, slug_parts, toks))
    for d in ('flowbite', 'doodles'):
        ddir = _ASSETS / d
        if not ddir.is_dir():
            continue
        for f in ddir.glob('*.svg'):
            slug_parts = set(f.stem.split('-'))
            candidates.append((d, f.stem, slug_parts, slug_parts))
    for d, slug, slug_parts, toks in candidates:
        if exclude and ('illust', d, slug) in exclude:
            continue
        # a meaningful word must anchor the match — fuzzy tag overlap alone
        # ('gate open' -> 'open-notes') pulls wrong art
        if not (main & slug_parts) and not (main & toks and len(wset & toks) >= 2):
            continue
        score = 0.0
        for w in wset & toks:
            score += (5 if w in slug_parts else 3) + 0.15 * len(w)
        score += len(wset & slug_parts)
        score += 1.5 * len(wset & toks) / len(wset)
        score -= len(slug) * 0.04
        if score > best_score:
            best, best_score = (d, slug), score
    if best and best_score >= 6.5:
        strokes = _dir_strokes(*best)
        # sparse art reads as fragments at icon scale — require real geometry
        try:
            n_el = len(svg_paths.elements_from_string(
                (_ASSETS / best[0] / f'{best[1]}.svg').read_text())[0])
        except Exception:
            n_el = 0
        if strokes and n_el >= 4 and _illust_ink(*best) >= 2.6:
            return ('illust',) + best
    return None


def _singular(w: str) -> str:
    if w.endswith('ies') and len(w) > 4:
        return w[:-3] + 'y'
    if w.endswith('es') and len(w) > 4:
        return w[:-2]
    if w.endswith('s') and not w.endswith('ss') and len(w) > 3:
        return w[:-1]
    return w
_STRIKE_TOKENS = {'old', 'manual', 'before', 'outdated', 'legacy', 'broken',
                  'without', 'no', 'boring', 'slow', 'bad'}
_EMPHASIS_TOKENS = {'important', 'critical', 'key', 'warning', 'urgent',
                    'must', 'never', 'always', 'alert', 'vital', 'best'}


def _asset_key(icon):
    """Identity of the drawn asset for dedup — tuple art is keyed by its
    file identity; plain props are generic enough to never collide."""
    if isinstance(icon, tuple):
        if icon[0] == 'overlay':
            return ('overlay', _asset_key(icon[1]), _asset_key(icon[2]))
        return tuple(icon[:3])
    return (icon,)


def _icon_for(concept: str, exclude=None):
    phrase = str(concept).lower().replace('-', ' ').replace('_', ' ').strip()
    words = phrase.split()
    wset = set(words)
    if any(f'{k} agent' in phrase or f'{k} rep' in phrase for k in _PERSON_AGENT_PREFIXES):
        return 'person'
    # bespoke commissioned/generated art for this exact label wins outright
    if (_CUSTOM_DIR / f'{_slug(phrase)}.svg').is_file():
        return ('custom', _slug(phrase))
    # action-word figure art (running, sitting, reading...) beats a static pose
    for w in words:
        if (_ASSETS / 'doodles' / f'{w}.svg').is_file() and w in (
                'running', 'sprinting', 'sitting', 'reading', 'meditating',
                'dancing', 'jumping', 'strolling', 'unboxing', 'petting',
                'selfie', 'ballet', 'swinging', 'laying', 'groovy', 'rolling',
                'chilling', 'moshing', 'zombieing', 'sleek', 'clumsy', 'float',
                'loving'):
            return ('illust', 'doodles', w)
    for icon, keys in _ICON_KEYWORDS.items():
        if any(' ' in k and k in phrase for k in keys):
            return icon
    if words:
        # a leading person/profession noun names the actor — it wins over an
        # object trailing the phrase ('teacher explains idea' → person)
        if words[0] in _ICON_KEYWORDS['person']:
            return 'person'
        # action/contrast words pin to their own icons before any fuzzy match;
        # 'wages rise' -> wage icon + rise badge beats a bare trend arrow
        vi = _verb_icon(phrase)
        if vi:
            rest = ' '.join(w for w in words if w not in _VERB_TABLE)
            base = _icon_lookup(rest, exclude) if rest else None
            if base and 0 < len(rest.split()) <= 3:
                return ('overlay', base, vi)
            return vi
        # a strong scene-vignette match beats the flat icon vocabulary
        il = _illust_lookup(phrase, exclude)
        if il:
            return il
        last = words[-1]
        for icon, keys in _ICON_KEYWORDS.items():
            if last in keys:
                return icon
    for icon, keys in _ICON_KEYWORDS.items():
        if any(k in wset or (len(k) >= 6 and k in phrase) for k in keys):
            return icon
    if _STAT_RE.match(phrase):
        return 'stat'
    if re.search(r'\d', phrase):
        # the icon vocabulary may still know the non-numeric words
        rest = ' '.join(w for w in words if not re.search(r'\d', w))
        if rest and rest not in ('min', 'minute', 'hour', 'day'):
            hit = _icon_lookup(rest, exclude)
            if hit:
                return hit
        if re.search(r'\b(min|mins|minute|minutes|hour|hours|sec|seconds|day|days|am|pm)\b', phrase):
            return 'clock'
        if re.search(r'(%|\$|bp|bps|\bx\b|\bk\b)', phrase):
            return 'chart'
        return 'coin'
    # last-word bespoke art ('giant octopus' -> octopus.svg)
    if words and (_CUSTOM_DIR / f'{_slug(words[-1])}.svg').is_file():
        return ('custom', _slug(words[-1]))
    hit = _icon_lookup(phrase, exclude)
    if hit:
        return hit
    return 'card'


def icon_for(concept: str, used=None):
    """Resolve a label to art, honouring a per-reel asset registry.

    `used` maps asset key -> normalized label. An identical label reuses
    its asset (continuity); a different label may not clone art that a
    different label already claimed — it takes the next-best distinct
    asset instead ('square window' vs 'window pane' must differ)."""
    if used is None:
        return _icon_for(concept)
    label = ' '.join(str(concept).lower().replace('-', ' ').split())
    reg = used.setdefault('_reg', {})
    assets = reg.setdefault('assets', {})
    nouns = reg.setdefault('nouns', {})
    excl = {k for k, v in assets.items() if v != label}
    words = [w for w in label.split() if len(w) > 2]
    head = _singular(words[-1]) if words else None
    icon = None
    # When this reel already depicted this head noun under a different
    # label, let the modifiers steer: 'window frame' after 'square window'
    # should draw a frame, not a second window.
    if head and head in nouns and nouns[head] != label and len(words) > 1:
        rest = ' '.join(words[:-1])
        icon = (_illust_lookup(rest, excl) or _icon_lookup(rest, excl))
    if icon is None:
        icon = _icon_for(concept, excl)
    key = ('card', label) if icon == 'card' else _asset_key(icon)
    assets.setdefault(key, label)
    if head and isinstance(icon, tuple):
        nouns.setdefault(head, label)
    return icon


def _strokes_for(icon, pose='point', facing: int = 1, cast=None):
    if isinstance(icon, tuple) and icon[0] == 'overlay':
        base = _strokes_for(icon[1]) or []
        verb = _strokes_for(icon[2]) or []
        return base + _shift_strokes(verb, 0.40, 0.56, 0.56, color='accent')
    if isinstance(icon, tuple) and icon[0] == 'icon':
        if icon[1] == 'tabler':
            return _tabler_strokes(icon[2])
        st = _dir_strokes(icon[1], icon[2])
        if st:
            return st
        return PROPS['tile']
    if isinstance(icon, tuple) and icon[0] == 'tabler':
        return _tabler_strokes(icon[1])
    if isinstance(icon, tuple) and icon[0] == 'custom':
        custom = _custom_strokes(icon[1])
        if custom:
            return custom
    if isinstance(icon, tuple) and icon[0] == 'illust':
        ill = _dir_strokes(icon[1], icon[2])
        if ill:
            return ill
    if icon == 'person':
        spec = cast if isinstance(cast, dict) else (cast or pose)
        return _peeps_strokes(spec, facing)
    if icon == 'agent':
        return _robot_strokes()
    if icon == 'card':
        return [(_rounded_rect(0, 0, 1.0, 0.68, 0.08), 'ink', 1.0)]
    return PROPS.get(icon, PROPS['tile'])


def _card_text_strokes(center, size, label, zone):
    """The fallback card lettered with its label — never a blank box."""
    txt = str(label).upper()
    h = size * 0.19
    maxw = size * 0.72
    words = txt.split()
    lines = None
    if len(words) > 1 and text_width(txt, h) > maxw:
        # two-line wrap at the most balanced word boundary
        best = min(range(1, len(words)),
                   key=lambda i: max(text_width(' '.join(words[:i]), h),
                                     text_width(' '.join(words[i:]), h)))
        lines = [' '.join(words[:best]), ' '.join(words[best:])]
        tw = max(text_width(l, h) for l in lines)
        if tw > maxw:
            h *= maxw / tw
    if lines is None:
        tw = text_width(txt, h)
        if len(words) <= 1 and tw > maxw:  # one long word: shrink, not chop
            h *= maxw / tw
            tw = text_width(txt, h)
        while tw > maxw and ' ' in txt[:-2]:
            txt = txt.rsplit(' ', 1)[0] + '…'
            tw = text_width(txt, h)
        while tw > maxw and len(txt) > 4:
            txt = txt[:-2] + '…'
            tw = text_width(txt, h)
        lines = [txt]
    strokes = []
    oy = center[1] + h * (0.07 if len(lines) == 1 else -0.72)
    for li, ln in enumerate(lines):
        lw = text_width(ln, h)
        strokes += text_strokes(ln, (center[0] - lw / 2, oy + li * h * 1.45),
                                h, 'ink', 0.95)
    return strokes


def _stat_strokes(center, size, label):
    """A number written large — the crypto-explainer stat callout."""
    txt = str(label).strip().upper()
    h = size * 0.52
    tw = text_width(txt, h)
    maxw = size * 1.5
    if tw > maxw:
        h *= maxw / tw
        tw = text_width(txt, h)
    origin = (center[0] - tw / 2, center[1] + h * 0.15)
    strokes = text_strokes(txt, origin, h, 'ink', 1.5)
    strokes += [([(px + h * 0.04, py + h * 0.02) for px, py in s[0]],
                 s[1], s[2], s[3], s[4]) for s in list(strokes)]
    y = origin[1] + _text_bottom(txt, h) + h * 0.16
    strokes.append(([(origin[0] - tw * 0.06, y), (origin[0] + tw * 1.06, y)],
                    'accent', 1.2, False, True))
    return strokes


def _arrow_strokes(p0, p1):
    """Curved accent arrow — the drawn verb between actor and object."""
    mx = (p0[0] + p1[0]) / 2
    cy = min(p0[1], p1[1]) - abs(p1[0] - p0[0]) * 0.14
    pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * mx + t * t * p1[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t * t * p1[1])
           for t in (i / 18 for i in range(19))]
    ex, ey = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
    m = math.hypot(ex, ey) or 1
    ux, uy = ex / m, ey / m
    px, py = -uy, ux
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * 0.16
    tip = p1
    base = (p1[0] - ux * L, p1[1] - uy * L)
    head = [[(base[0] + px * L * 0.45, base[1] + py * L * 0.45), tip,
             (base[0] - px * L * 0.45, base[1] - py * L * 0.45)]]
    return [(pts, 'accent', 1.0, False, True),
            (head[0], 'accent', 1.0, False, True)]


def _strike_strokes(size):
    """Cross-out X over a slot — the 'not this' transform."""
    return [([(-0.52, -0.42), (0.52, 0.42)], 'accent', 1.5, False),
            ([(0.52, -0.42), (-0.52, 0.42)], 'accent', 1.5, False)]


def _emphasis_strokes(size):
    """Loose circle around a slot — drawn emphasis on the key item."""
    pts = [(0.62 * math.cos(a), 0.52 * math.sin(a))
           for a in [i * math.pi / 10 + 0.2 for i in range(22)]]
    return [(pts, 'accent', 1.3, False)]


def _pose_for_label(label: str) -> str:
    low = str(label).lower()
    for keys, pose in _POSE_BINDINGS:
        if any(k in low for k in keys):
            return pose
    h = _stable_hash(str(label).strip().lower())
    return _POSE_ROTATION[h % len(_POSE_ROTATION)]


def _cast_spec_for(label: str, pose_name: str):
    """Deterministic per-label cast variant — a different face/hair per role so
    a series reads as a designed cast, not repeats of one figure."""
    low = str(label).strip().lower()
    h = _stable_hash(low)
    # resolve the file pose name for composed parts
    file = _POSE_FILES.get(pose_name, pose_name)
    base = file.rsplit('/', 1)[-1].replace('.svg', '')
    for pre in ('standing_', 'sitting_'):
        if base.startswith(pre):
            base = base[len(pre):]
    if base.startswith(('standing', 'sitting')):
        return {'pose': file}
    return {'pose': base,
            'hair': _HAIR_ROTATION[h % len(_HAIR_ROTATION)],
            'face': _FACE_ROTATION[(h // 7) % len(_FACE_ROTATION)]}


def _stable_hash(s: str) -> int:
    return int.from_bytes(hashlib.sha1(s.encode()).digest()[:4], 'big')


# ---------------------------------------------------------------------------
# Scene composition — character anchors left, props compose right; no connectors
# ---------------------------------------------------------------------------

def _scene_slots(labels: list[str], zone: dict, ratio: str, used=None):
    icons = [icon_for(l, used) for l in labels]
    x, y, w, h = zone['x'], zone['y'], zone['w'], zone['h']
    portrait = ratio == '9:16'
    cy = y + h * (0.54 if portrait else 0.56)

    people = [i for i, ic in enumerate(icons) if ic in ('person', 'agent')]
    props = [i for i, ic in enumerate(icons) if ic not in ('person', 'agent')]

    slots: list[dict | None] = [None] * len(icons)
    prop_size = min(w, h) * (0.34 if len(props) <= 2 else 0.26)
    char_size = prop_size * (1.35 if len(props) <= 1 else 1.2)

    def _size_for(icon):
        if icon == 'person':
            return char_size
        if icon == 'agent':
            return char_size * 0.72
        return prop_size

    if people and props:
        pi = people[0]
        cx_p = x + w * (0.30 if portrait else 0.22)
        pose = _pose_for_label(labels[pi]) if icons[pi] == 'person' else None
        slots[pi] = dict(center=(cx_p, cy - char_size * 0.02), size=_size_for(icons[pi]),
                         icon=icons[pi], label=labels[pi], pose=pose,
                         facing=1,
                         cast=_cast_spec_for(labels[pi], pose) if pose else None,
                         bubble=False)
        area_x0 = x + (0 if portrait else w * 0.42)
        rest = props + people[1:]
        n = len(rest)
        if portrait and n > 2:
            for k, i in enumerate(rest):
                col, row = k % 2, k // 2
                pose = _pose_for_label(labels[i]) if icons[i] == 'person' else None
                slots[i] = dict(
                    center=(x + w * (0.30 + 0.40 * col), y + h * (0.40 + 0.36 * row)),
                    size=_size_for(icons[i]) * 0.9, icon=icons[i], label=labels[i],
                    pose=pose, facing=-1 if col else 1,
                    cast=_cast_spec_for(labels[i], pose) if pose else None,
                    bubble=False)
        else:
            aw = x + w - area_x0
            step = aw / max(1, n)
            for k, i in enumerate(rest):
                pose = _pose_for_label(labels[i]) if icons[i] == 'person' else None
                slots[i] = dict(
                    center=(area_x0 + step * (k + 0.5), cy),
                    size=_size_for(icons[i]), icon=icons[i], label=labels[i],
                    pose=pose, facing=1,
                    cast=_cast_spec_for(labels[i], pose) if pose else None,
                    bubble=False)
    elif people:
        n = len(people)
        step = w / (n + 1)
        for k, i in enumerate(people):
            pose = _pose_for_label(labels[i]) if icons[i] == 'person' else None
            slots[i] = dict(center=(x + step * (k + 1), cy - char_size * 0.02),
                            size=_size_for(icons[i]), icon=icons[i], label=labels[i],
                            pose=pose, facing=1 if k % 2 == 0 else -1,
                            cast=_cast_spec_for(labels[i], pose) if pose else None,
                            bubble=False)
    else:
        n = len(props)
        if portrait and n > 2:
            cols = 2 if n > 3 else 1
            rows = math.ceil(n / cols)
            for k, i in enumerate(props):
                col, row = k % cols, k // cols
                slots[i] = dict(
                    center=(x + w * (0.30 + (0.40 if cols > 1 else 0.20) * col),
                            y + h * (0.34 + (0.62 / max(1, rows - 1) if rows > 1 else 0.0) * row)),
                    size=prop_size * 0.95, icon=icons[i], label=labels[i],
                    pose=None, facing=1, cast=None, bubble=False)
        else:
            margin = w * (0.10 if n > 3 else 0.18)
            step = (w - 2 * margin) / max(1, n - 1) if n > 1 else 0
            size = prop_size * (1.25 if n <= 2 else 1.0)
            for k, i in enumerate(props):
                jitter = (0.03 * h) * (1 if k % 2 else -1) if n > 2 else 0
                slots[i] = dict(center=(x + margin + step * k, cy + jitter),
                                size=size, icon=icons[i], label=labels[i],
                                pose=None, facing=1, cast=None, bubble=False)

    # actors face the scene center — dialogue reads correctly at any layout
    zcx = x + w / 2
    for s in slots:
        if s and s['icon'] in ('person', 'agent'):
            s['facing'] = 1 if s['center'][0] <= zcx else -1

    # vignette pairing: with an actor present, pull the first small prop into
    # reach so the two draw as an interaction, not a row of items
    ppl = [s for s in slots if s and s['icon'] in ('person', 'agent')]
    sm_props = [s for s in slots if s and s['icon'] not in ('person', 'agent')
                and not (isinstance(s['icon'], tuple)
                         and s['icon'][0] == 'illust')]
    if ppl and sm_props and not portrait:
        p, q = ppl[0], sm_props[0]
        reach_x = p['center'][0] + p['facing'] * (p['size'] * 0.58
                                                + q['size'] * 0.40)
        reach_x = min(max(reach_x, x + q['size'] * 0.55),
                      x + w - q['size'] * 0.55)
        # only pull if it doesn't collide with any other element
        ok = all(s is q or s is p
                 or abs(s['center'][0] - reach_x)
                 > (s['size'] + q['size']) * 0.46
                 for s in slots if s)
        if ok and abs(reach_x - q['center'][0]) > q['size'] * 0.2:
            q['center'] = (reach_x, p['center'][1] + p['size'] * 0.10)

    if people:
        for s in slots:
            if s is None or s['icon'] == 'agent':
                continue
            low = s['label'].lower()
            if any(k in low for k in ('want', 'need', 'idea', 'dream', 'goal',
                                      'question', 'why', 'wish', 'hope', 'think')):
                s['bubble'] = True
                if s['icon'] == 'person':
                    s['pose'] = 'gesture'
                    s['cast'] = _cast_spec_for(s['label'], 'gesture')
                break
        # if the bubble landed on a prop, the hero reacts to it
        if slots[people[0]] is not None and any(
                s is not None and s.get('bubble') and s['icon'] not in ('person', 'agent')
                for s in slots):
            slots[people[0]]['pose'] = 'gesture'
            slots[people[0]]['cast'] = _cast_spec_for(
                slots[people[0]]['label'], 'gesture')
    return [s for s in slots if s is not None]


# ---------------------------------------------------------------------------
# Drawing — adapter helpers do camera mapping, rough strokes, progressive ink
# ---------------------------------------------------------------------------

def _palette(plan):
    pal = wbp._pal(plan)
    accf = wbp._mix(pal['bgc'], pal['accentc'], 0.20)
    accdeep = wbp._mix(pal['bgc'], pal['accentc'], 0.72)
    inkfill = wbp._mix(pal['bgc'], pal['inkc'], 0.88)
    return {'ink': pal['inkc'], 'accent': pal['accentc'],
            'pale': (pal['secondaryc'][0], pal['secondaryc'][1], pal['secondaryc'][2], 190),
            'accfill': accf, 'accdeep': accdeep, 'inkfill': inkfill,
            'paper': pal['bgc'], 'bg': pal['bg']}


_HATCH_CACHE: dict = {}


def _hatch_for(poly, size, spacing=0.075):
    """Hatch segments for a closed unit-space polygon, memoized by content."""
    key = tuple(round(v, 4) for pt in poly for v in pt)
    segs = _HATCH_CACHE.get(key)
    if segs is None:
        segs = _hatch_segments(poly, spacing)
        if len(_HATCH_CACHE) > 4000:
            _HATCH_CACHE.clear()
        _HATCH_CACHE[key] = segs
    return segs


_HATCH_COLOR = {'paper': 'pale', 'accfill': 'accdeep', 'accdeep': 'accdeep',
                'inkfill': 'ink'}


def _stroke_tip(pts_s, p):
    """Analytic pen tip for a partially drawn stroke (no rasterizing)."""
    if not pts_s:
        return None
    return wbp._partial(pts_s, p)[-1]


def _draw_strokes(layer, strokes, center, size, cam, colors, ratio, progress,
                  seed, zoom=1.0, draw=True):
    """Draw a stroke group; returns the screen-space pen tip while drawing.

    Outlines draw first with tapered marker strokes; filled regions then
    scribble-hatch in (authentic marker shading, no pop-in polygon). Absolute
    entries (hand lettering) skip the unit-space slot transform.
    """
    n = len(strokes)
    if n == 0:
        return None
    scale = (min(*wbp.RATIO_SIZES[ratio]) / (650 if ratio != '9:16' else 760))
    lw = max(2.0, size * scale * 0.028)
    tip = None
    for j, st in enumerate(strokes):
        pts, col, wscale = st[0], st[1], st[2]
        fill = st[3] if len(st) > 3 else False
        absolute = st[4] if len(st) > 4 else False
        p = wbp._clamp(progress * n - j)
        if p <= 0:
            break
        if absolute:
            pts_b = pts
        else:
            pts_b = [(center[0] + px * size, center[1] + py * size)
                     for px, py in pts]
        pts_s = [wbp._map_point(q, cam, ratio, zoom) for q in pts_b]
        if not draw:
            if 0 < p < 1:
                tip = _stroke_tip(pts_s, p)
            continue
        if fill:
            # marker shading pass: hatches sweep in over the last 60% of the
            # element window, following the outline
            hp = wbp._clamp((p - 0.38) / 0.62)
            if hp <= 0:
                continue
            segs = _hatch_for(pts, size)
            hcol = colors[_HATCH_COLOR.get(col, col)]
            hcol = (hcol[0], hcol[1], hcol[2], min(215, hcol[3]))
            hw = max(1.4, lw * 0.42)
            m = len(segs)
            for k, seg in enumerate(segs):
                sp = wbp._clamp(hp * m - k)
                if sp <= 0:
                    break
                seg_b = [(center[0] + px * size, center[1] + py * size)
                         for px, py in seg]
                seg_s = [wbp._map_point(q, cam, ratio, zoom) for q in seg_b]
                t = _taper_line(layer, seg_s, hcol, hw, seed + j * 131 + k * 7,
                                .18, sp)
                if 0 < sp < 1:
                    tip = t
            if hp < 1 and not tip:
                tip = None
            continue
        t = _taper_line(layer, pts_s, colors[col], lw * wscale, seed + j * 13,
                        .26, p)
        if 0 < p < 1:
            tip = t
    return tip


def _headline_strokes(scene, zone, ratio):
    """Hand-lettered headline strokes in board space + accent underline."""
    primary = str((scene.get('screenCopy') or {}).get('primary') or '').strip()
    if not primary:
        return []
    h = zone['h'] * 0.075
    txt = primary.upper()[:46]
    while text_width(txt, h) > zone['w'] * 0.9 and h > zone['h'] * 0.03:
        h *= 0.9
    origin = (zone['x'] + zone['w'] * 0.05, zone['y'] + h * 1.5)
    strokes = text_strokes(txt, origin, h, 'ink', 1.35)
    # double-pass offset for marker boldness
    strokes += [( [(px + h * 0.045, py + h * 0.02) for px, py in s[0]],
                  s[1], s[2], s[3], s[4]) for s in list(strokes)]
    tw = text_width(txt, h)
    y_u = origin[1] + _text_bottom(txt, h) + h * 0.16
    upts = [(origin[0] + tw * t / 18, y_u + math.sin(t * 1.4) * h * 0.10)
            for t in range(19)]
    strokes.append((upts, 'ink', 1.5, False, True))
    strokes.append(([(a, b + h * 0.14) for a, b in upts], 'accent', 0.9,
                    False, True))
    return strokes


def _shift_strokes(strokes, dx, dy):
    return [([(px + dx, py + dy) for px, py in s[0]], *s[1:])
            for s in strokes]


def _caption_strokes(center, size, label, zone=None, row=0):
    txt = str(label).upper()
    h = size * 0.11
    maxw = min(size * 1.9, (zone['w'] * 0.42 if zone else size * 1.9))
    words = txt.split()
    lines = [txt]
    if len(words) > 1 and text_width(txt, h) > maxw:
        # two-line wrap at the most balanced boundary, then shrink to fit
        best = min(range(1, len(words)),
                   key=lambda i: max(text_width(' '.join(words[:i]), h),
                                     text_width(' '.join(words[i:]), h)))
        lines = [' '.join(words[:best]), ' '.join(words[best:])]
    tw = max(text_width(l, h) for l in lines)
    if tw > maxw:
        h = max(size * 0.060, h * maxw / tw)
        tw = max(text_width(l, h) for l in lines)
    oy = center[1] + size * (0.56 + 0.30 * row)
    strokes = []
    for li, ln in enumerate(lines):
        lw = text_width(ln, h)
        ox = center[0] - lw / 2
        if zone:
            ox = min(max(ox, zone['x'] + 6), zone['x'] + zone['w'] - lw - 6)
        strokes += text_strokes(ln, (ox, oy + li * h * 1.45), h, 'ink', 0.85)
    y = oy + (len(lines) - 1) * h * 1.45 + _text_bottom(lines[-1], h) + h * 0.16
    ox0 = min(center[0] - text_width(l, h) / 2 for l in lines)
    if zone:
        ox0 = max(ox0, zone['x'] + 6)
    strokes.append(([(ox0 - tw * 0.03, y), (ox0 + tw * 1.03, y)],
                    'accent', 0.8, False, True))
    return strokes, ox0, ox0 + tw


def _scene_labels(scene: dict) -> list[str]:
    labs: list[str] = []
    hero = scene.get('heroRole')
    if hero:
        labs.append(str(hero))
    labs += [str(r) for r in (scene.get('supportingRoles') or []) if str(r).strip()]
    if not labs:
        for v in (scene.get('semanticBeats') or scene.get('visualAnchors') or
                  scene.get('visuals') or []):
            l = (v.get('label') or v.get('concept')) if isinstance(v, dict) else v
            if str(l or '').strip():
                labs.append(str(l))
    return labs or [scene.get('sceneId', 'scene')]


def _group_len(g) -> float:
    """Ink length of a group's strokes in board space (unit strokes scaled
    by slot size; absolute entries are already board coordinates)."""
    _kind, strokes, _c, size, _s = g
    total = 0.0
    for st in strokes:
        pts = st[0]
        absolute = st[4] if len(st) > 4 else False
        scale = 1.0 if absolute else size
        for a, b in zip(pts, pts[1:]):
            total += math.hypot(b[0] - a[0], b[1] - a[1]) * scale
    return total


def _ease_inv(p: float) -> float:
    """Inverse of wbp._ease via bisection (monotone on [0,1])."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if wbp._ease(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _scene_groups(scene: dict, plan: dict, ratio: str):
    zone = scene['whiteboardRuntime']['boardZone']
    labels = _scene_labels(scene)
    slots = _scene_slots(labels, zone, ratio,
                         plan.setdefault('_icon_used', {}))

    order = {'headline': -1, 'ground': 0, 'icon': 0, 'arrow': 0.5,
             'bubble': 1, 'marks': 2, 'sparkle': 2, 'strike': 2.5,
             'emphasis': 2.6, 'caption': 3}
    groups = [('headline', _headline_strokes(scene, zone, ratio),
               (zone['x'], zone['y']), 1.0, None)]
    mark_groups = []
    for s in slots:
        if s['icon'] == 'stat':
            groups.append(('icon', _stat_strokes(s['center'], s['size'],
                                                 s['label']),
                           s['center'], s['size'], s))
            s['no_caption'] = True
        else:
            groups.append(('icon', _strokes_for(
                s['icon'], s.get('pose') or 'point', s.get('facing', 1),
                s.get('cast')), s['center'], s['size'], s))
        if s['icon'] == 'card':
            groups.append(('icon', _card_text_strokes(s['center'], s['size'],
                                                      s['label'], zone),
                           s['center'], s['size'], s))
            s['no_caption'] = True
        if s['icon'] in ('person', 'agent'):
            gc = (s['center'][0], s['center'][1] + s['size'] * 0.52)
            groups.append(('ground', _ground_shadow_strokes(), gc, s['size'], s))
            if s['icon'] == 'person':
                mark_groups.append(('marks', _motion_marks_strokes(),
                                    s['center'], s['size'], s))
        low_lbl = str(s['label']).lower()
        ltoks = set(re.findall(r"[a-z']+", low_lbl))
        if ltoks & _STRIKE_TOKENS or low_lbl.startswith(('no ', 'not ')):
            groups.append(('strike', _strike_strokes(s['size']),
                           s['center'], s['size'], s))
        if ltoks & _EMPHASIS_TOKENS or '!' in str(s['label']):
            groups.append(('emphasis', _emphasis_strokes(s['size']),
                           s['center'], s['size'], s))
        if s.get('bubble'):
            bx = min(s['center'][0] + s['size'] * 0.55 * s.get('facing', 1),
                     zone['x'] + zone['w'] - s['size'] * 0.35)
            bx = max(bx, zone['x'] + s['size'] * 0.35)
            bc = (bx, s['center'][1] - s['size'] * 0.62)
            groups.append(('bubble', _bubble_strokes(), bc, s['size'] * 0.62, s))
        if s['icon'] in ('envelope', 'phone', 'question'):
            groups.append(('sparkle', _ping_strokes(), s['center'], s['size'], s))
        if s['icon'] in ('check', 'coin', 'coins', 'rocket', 'lightbulb', 'chart', 'target'):
            groups.append(('sparkle', _sparkle_strokes(), s['center'], s['size'], s))
    # verb arrow — the drawn relationship from actor to first object
    arrow_drawn = False
    person_slots = [s for s in slots if s['icon'] == 'person']
    prop_slots = [s for s in slots if s['icon'] not in ('person', 'agent')]
    if person_slots and prop_slots:
        p, q = person_slots[0], prop_slots[0]
        p0 = (p['center'][0] + p['size'] * 0.40 * p.get('facing', 1),
              p['center'][1] - p['size'] * 0.08)
        p1 = (q['center'][0] - q['size'] * 0.55 * p.get('facing', 1),
              q['center'][1] - q['size'] * 0.08)
        if abs(p1[0] - p0[0]) > p['size'] * 0.15:
            mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            groups.append(('arrow', _arrow_strokes(p0, p1), mid, 1.0, None))
            arrow_drawn = True
    # motion marks only when the arrow didn't already carry the action
    if not arrow_drawn:
        groups += mark_groups

    # two caption rows with per-row edges: a caption drops to row 1 when it
    # collides on row 0, or stays on row 0 if row 1 already has a neighbor
    row_edges = [None, None]
    for s in sorted(slots, key=lambda s: s['center'][0]):
        if s.get('no_caption'):
            row_edges = [None, None]
            continue
        dy = 0.66 if s['icon'] in ('person', 'agent') else 0.56

        def cap(r):
            st, a, b = _caption_strokes(s['center'], s['size'],
                                        s['label'], zone, r)
            if s['icon'] in ('person', 'agent'):
                st = _shift_strokes(st, 0, s['size'] * (dy - 0.56))
            return st, a, b

        strokes, x0, x1 = cap(0)
        row = 0
        if row_edges[0] is not None and x0 < row_edges[0] + 10:
            row = 1
            strokes, x0, x1 = cap(1)
            if (row_edges[1] is not None and x0 < row_edges[1] + 10
                    and (row_edges[0] is None
                         or x0 - row_edges[0] > row_edges[1] - x0)):
                row = 0
                strokes, x0, x1 = cap(0)
        row_edges[row] = x1
        groups.append(('caption', strokes, s['center'], s['size'], s))
    groups.sort(key=lambda g: order[g[0]])

    dp = scene['whiteboardRuntime'].get('drawPlan') or []
    out = []
    for gi, g in enumerate(groups):
        j = min(gi, len(dp) - 1)
        st = dp[j] if dp else {}
        start = float(st.get('start', gi / max(1, len(groups))))
        end = float(st.get('end', (gi + 1) / max(1, len(groups))))
        out.append((g, start, max(end, start + 0.02)))
    # Re-weight windows by real ink length so the pen draws at roughly
    # constant physical speed — dense groups take longer, thin ones fly.
    w0 = out[0][1]
    w1 = out[-1][2]
    if w1 > w0 and len(out) > 1:
        lens = [max(1.0, _group_len(g)) for g, _s, _e in out]
        total = sum(lens)
        cur = w0
        weighted = []
        for i, (g, _s, _e) in enumerate(out):
            seg = (w1 - w0) * lens[i] / total
            weighted.append((g, cur, cur + max(seg, 0.02)))
            cur += seg + 0.03
        # keep the last end inside the original window
        overflow = cur - 0.03 - w1
        if overflow > 0:
            shrink = (w1 - w0) / (cur - 0.03 - w0)
            weighted = [(g, w0 + (s - w0) * shrink, w0 + (e - w0) * shrink)
                        for g, s, e in weighted]
        out = weighted
    # Sync the compiled drawPlan to the windows the pen actually uses — the
    # sound layer schedules scratches from the same entries, so a stale
    # window here reads as SFX running ahead of (or behind) the hand.
    # Idempotent: re-entry re-weights identical lengths to identical times.
    if dp:
        spans: dict = {}
        pens: dict = {}
        for gi, (g, s_, e_) in enumerate(out):
            j = min(gi, len(dp) - 1)
            a, b = spans.get(j, (s_, e_))
            spans[j] = (min(a, s_), max(b, e_))
            # per-polyline pen-down intervals — the sound layer scratches
            # only while the pen is inking, never during lifts/travel.
            # Strokes draw at EQUAL shares of the eased group window
            # (p = ease((t-s)/(e-s))*n - j), so invert the ease to land
            # each interval exactly on its stroke's real time span.
            n = len(g[1])
            pen = []
            for jj, stt in enumerate(g[1]):
                a, b = jj / n, (jj + 1) / n
                if len(stt) > 3 and stt[3]:  # hatch fills skip p<0.38
                    a += 0.38 / n
                pen.append([s_ + (e_ - s_) * _ease_inv(a),
                            s_ + (e_ - s_) * _ease_inv(b)])
            pens.setdefault(j, []).extend(pen)
        for j, st in enumerate(dp):
            if j in spans:
                st['start'], st['end'] = spans[j]
                st['pen'] = sorted(pens[j])
            else:
                st['soundRole'] = None  # no drawn group left for this step
    return out


def draw_scene_layer(scene: dict, plan: dict, ratio: str, scene_time: float,
                     cam=None, seed=7, zoom=1.0, draw=True):
    """Returns (layer, pen_tip_screen_or_None) — the tip feeds the hand."""
    layer = Image.new('RGBA', wbp.RATIO_SIZES[ratio], (0, 0, 0, 0))
    cam = cam or wbp._camera(scene, ratio)
    colors = _palette(plan)
    tip = None
    for gi, ((kind, strokes, center, size, slot), start, end) in enumerate(
            _scene_groups(scene, plan, ratio)):
        p = wbp._ease(wbp._clamp((scene_time - start) / max(0.05, end - start)))
        if p <= 0:
            continue
        t = _draw_strokes(layer, strokes or [], center, size, cam, colors,
                          ratio, p, seed + gi * 97, zoom, draw)
        if p < 1 and t is not None:
            tip = t
    return layer, tip


def _tip_at(scene, plan, ratio, t, cam, seed, zoom):
    """Pen tip at a time — cheap analytic pass used for hand travel smoothing."""
    _, tip = draw_scene_layer(scene, plan, ratio, t, cam, seed, zoom,
                              draw=False)
    return tip


def _smooth_tip(scene, plan, ratio, scene_time, cam, seed, zoom):
    """Hand position with travel lag and exit slide — the hand never
    teleports between elements."""
    tip = _tip_at(scene, plan, ratio, scene_time, cam, seed, zoom)
    if tip is not None:
        back = _tip_at(scene, plan, ratio, scene_time - 0.14, cam, seed, zoom)
        if back is not None:
            tip = (back[0] + (tip[0] - back[0]) * 0.72,
                   back[1] + (tip[1] - back[1]) * 0.72)
        return tip
    # exited — find when ink last moved and slide the hand off
    last = None
    for back_dt in (0.08, 0.2, 0.35, 0.55):
        b = _tip_at(scene, plan, ratio, scene_time - back_dt, cam, seed, zoom)
        if b is not None:
            last = (b, back_dt)
            break
    if last is None:
        return None
    (bx, by), dt = last
    return (bx, by + dt * 90 + 14)


def _scene_cam_zoom(scene, plan, ratio, scene_time: float):
    """Fixed frame per zone — this whiteboard style never zooms mid-scene.
    Only the inter-scene transition travels the board."""
    return wbp._camera(scene, ratio), 1.0


def _alpha_scale(layer: Image.Image, alpha: int) -> Image.Image:
    if alpha >= 255:
        return layer
    r, g, b, a = layer.split()
    a = a.point(lambda v: v * alpha // 255)
    out = Image.merge('RGBA', (r, g, b, a))
    return out


def _composite_frame(plan: dict, ratio: str, cam, layers: list[tuple[Image.Image, int]], seed=7):
    pal = wbp._pal(plan)
    base = Image.new('RGBA', wbp.RATIO_SIZES[ratio], pal['bgc'])
    wbp._paper_texture(base, pal, seed)
    for layer, alpha in layers:
        base.alpha_composite(_alpha_scale(layer, alpha))
    return base.convert('RGB')


def render_scene_frame(scene: dict, plan: dict, ratio: str, scene_time: float) -> Image.Image:
    cam, zoom = _scene_cam_zoom(scene, plan, ratio, scene_time)
    scenes = plan.get('sceneSpecs') or [scene]
    idx = next((i for i, s in enumerate(scenes)
                if s.get('sceneId') == scene.get('sceneId')), 0)
    wb = scene.get('whiteboardRuntime') or {}
    seed = int(wb.get('seed', 7))
    layers = []
    for j in range(idx):
        lyr, _ = draw_scene_layer(scenes[j], plan, ratio, 999.0, cam,
                                  seed + j, zoom)
        layers.append((lyr, 255))
    lyr, tip = draw_scene_layer(scene, plan, ratio, scene_time, cam,
                                seed + idx, zoom)
    if tip is not None:
        # smooth with a lagging sample — hand sweeps, never teleports
        tip = _smooth_tip(scene, plan, ratio, scene_time, cam, seed + idx,
                          zoom)
    elif scene_time > 0.05:
        tip = _smooth_tip(scene, plan, ratio, scene_time, cam, seed + idx,
                          zoom)
    layers.append((lyr, 255))
    frame = _composite_frame(plan, ratio, cam, layers, seed)
    return _overlay_hand(frame, tip, ratio, scene_time * 8 + seed)


def render_transition_frame(prev_scene, next_scene, plan, ratio, p: float):
    """Camera slide between zones; previous scenes stay on the board. Zoom
    relaxes mid-move (pull back to travel, push in to arrive)."""
    c0 = wbp._camera(prev_scene, ratio)
    c1 = wbp._camera(next_scene, ratio)
    q = wbp._ease(wbp._clamp(p))
    cam = (c0[0] + (c1[0] - c0[0]) * q, c0[1] + (c1[1] - c0[1]) * q)
    scenes = plan.get('sceneSpecs') or [next_scene]
    idx = next((i for i, s in enumerate(scenes)
                if s.get('sceneId') == next_scene.get('sceneId')), len(scenes) - 1)
    wb = next_scene.get('whiteboardRuntime') or {}
    seed = int(wb.get('seed', 9))
    dur = float(wb.get('sceneDuration') or 4.0)
    next_time = 0.0
    tip = None
    layers = []
    zoom_dip = 1.0 - 0.05 * math.sin(math.pi * q)
    for j in range(idx):
        lyr, _ = draw_scene_layer(scenes[j], plan, ratio, 999.0, cam, seed + j,
                                  zoom_dip)
        layers.append((lyr, 255))
    trans = float((plan.get('pacing') or {}).get('transition_seconds', 0.62))
    if p > 0.55:
        # draw only the first `trans` seconds so ink is continuous at handoff
        next_time = (p - 0.55) / 0.45 * trans
        lyr, tip = draw_scene_layer(next_scene, plan, ratio, next_time, cam,
                                    seed + idx, zoom_dip)
        layers.append((lyr, 255))
    frame = _composite_frame(plan, ratio, cam, layers, seed)
    return _overlay_hand(frame, tip, ratio, p * 30 + seed)
