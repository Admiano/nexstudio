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
               'agent owner', 'customer agent'),
    'agent': ('agent', 'robot', 'ai', 'bot', 'assistant', 'system'),
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
    'laptop': ('laptop', 'computer', 'workstation', 'website', 'platform',
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


def icon_for(concept: str) -> str:
    phrase = str(concept).lower().replace('-', ' ').replace('_', ' ').strip()
    words = phrase.split()
    wset = set(words)
    if any(f'{k} agent' in phrase or f'{k} rep' in phrase for k in _PERSON_AGENT_PREFIXES):
        return 'person'
    for icon, keys in _ICON_KEYWORDS.items():
        if any(' ' in k and k in phrase for k in keys):
            return icon
    if words:
        # a leading person/profession noun names the actor — it wins over an
        # object trailing the phrase ('teacher explains idea' → person)
        if words[0] in _ICON_KEYWORDS['person']:
            return 'person'
        last = words[-1]
        for icon, keys in _ICON_KEYWORDS.items():
            if last in keys:
                return icon
    for icon, keys in _ICON_KEYWORDS.items():
        if any(k in wset or (len(k) > 3 and k in phrase) for k in keys):
            return icon
    if re.search(r'\d', phrase):
        if re.search(r'\b(min|mins|minute|minutes|hour|hours|sec|seconds|day|days|am|pm)\b', phrase):
            return 'clock'
        if re.search(r'(%|\$|bp|bps|\bx\b|\bk\b)', phrase):
            return 'chart'
        return 'coin'
    return 'tile'


def _strokes_for(icon: str, pose='point', facing: int = 1, cast=None):
    if icon == 'person':
        spec = cast if isinstance(cast, dict) else (cast or pose)
        return _peeps_strokes(spec, facing)
    if icon == 'agent':
        return _robot_strokes()
    return PROPS.get(icon, PROPS['tile'])


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

def _scene_slots(labels: list[str], zone: dict, ratio: str):
    icons = [icon_for(l) for l in labels]
    x, y, w, h = zone['x'], zone['y'], zone['w'], zone['h']
    portrait = ratio == '9:16'
    cy = y + h * (0.54 if portrait else 0.56)

    people = [i for i, ic in enumerate(icons) if ic in ('person', 'agent')]
    props = [i for i, ic in enumerate(icons) if ic not in ('person', 'agent')]

    slots: list[dict | None] = [None] * len(icons)
    char_size = h * (0.66 if len(props) <= 1 else 0.58)
    prop_size = min(w, h) * (0.34 if len(props) <= 2 else 0.26)

    def _size_for(icon):
        if icon == 'person':
            return char_size
        if icon == 'agent':
            return char_size * 0.62
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


def _draw_strokes(layer, strokes, center, size, cam, colors, ratio, progress,
                  seed, zoom=1.0):
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
    y_u = origin[1] + h * 0.34
    upts = [(origin[0] + tw * t / 18, y_u + math.sin(t * 1.4) * h * 0.10)
            for t in range(19)]
    strokes.append((upts, 'ink', 1.5, False, True))
    strokes.append(([(a, b + h * 0.13) for a, b in upts], 'accent', 0.9,
                    False, True))
    return strokes


def _caption_strokes(center, size, label, zone=None, row=0):
    txt = str(label).upper()
    h = size * 0.11
    tw = text_width(txt, h)
    maxw = min(size * 1.9, (zone['w'] * 0.42 if zone else size * 1.9))
    while tw > maxw and len(txt) > 6:
        txt = txt[:-4] + '...'
        tw = text_width(txt, h)
    ox = center[0] - tw / 2
    if zone:
        ox = min(max(ox, zone['x'] + 6), zone['x'] + zone['w'] - tw - 6)
    origin = (ox, center[1] + size * (0.56 + 0.15 * row))
    strokes = text_strokes(txt, origin, h, 'ink', 0.85)
    pad = tw * 0.05
    y = origin[1] + h * 0.30
    strokes.append(([(origin[0] - pad, y), (origin[0] + tw + pad, y)],
                    'accent', 0.8, False, True))
    return strokes, ox, ox + tw


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


def _scene_groups(scene: dict, plan: dict, ratio: str):
    zone = scene['whiteboardRuntime']['boardZone']
    labels = _scene_labels(scene)
    slots = _scene_slots(labels, zone, ratio)

    order = {'headline': -1, 'ground': 0, 'icon': 0, 'bubble': 1,
             'marks': 2, 'sparkle': 2, 'caption': 3}
    groups = [('headline', _headline_strokes(scene, zone, ratio),
               (zone['x'], zone['y']), 1.0, None)]
    for s in slots:
        groups.append(('icon', _strokes_for(s['icon'], s.get('pose') or 'point',
                                            s.get('facing', 1), s.get('cast')),
                       s['center'], s['size'], s))
        if s['icon'] in ('person', 'agent'):
            gc = (s['center'][0], s['center'][1] + s['size'] * 0.52)
            groups.append(('ground', _ground_shadow_strokes(), gc, s['size'], s))
            if s['icon'] == 'person':
                groups.append(('marks', _motion_marks_strokes(), s['center'], s['size'], s))
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
    # two caption rows: neighbors whose text ranges overlap drop to row 1
    prev_edge = None
    row = 0
    for s in sorted(slots, key=lambda s: s['center'][0]):
        strokes, x0, x1 = _caption_strokes(s['center'], s['size'],
                                           s['label'], zone, row)
        if prev_edge is not None and x0 < prev_edge + 10:
            row = 1
            strokes, x0, x1 = _caption_strokes(s['center'], s['size'],
                                               s['label'], zone, row)
        else:
            row = 0
        prev_edge = x1
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
    return out


def draw_scene_layer(scene: dict, plan: dict, ratio: str, scene_time: float,
                     cam=None, seed=7, zoom=1.0):
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
                          ratio, p, seed + gi * 97, zoom)
        if p < 1 and t is not None:
            tip = t
    return layer, tip


def _scene_zoom(scene, scene_time: float, ratio: str) -> float:
    """Camera micro-zoom: slow push-in over the scene's first half, then
    settle — the subtle drift paid whiteboard tools charge for."""
    wb = scene.get('whiteboardRuntime') or {}
    dur = float(wb.get('sceneDuration') or 4.0)
    q = wbp._ease(wbp._clamp(scene_time / max(0.1, dur * 0.55)))
    return 1.0 + 0.085 * q


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
    cam = wbp._camera(scene, ratio)
    zoom = _scene_zoom(scene, scene_time, ratio)
    scenes = plan.get('sceneSpecs') or [scene]
    idx = next((i for i, s in enumerate(scenes)
                if s.get('sceneId') == scene.get('sceneId')), 0)
    wb = scene.get('whiteboardRuntime') or {}
    seed = int(wb.get('seed', 7))
    tip = None
    layers = []
    for j in range(idx):
        lyr, _ = draw_scene_layer(scenes[j], plan, ratio, 999.0, cam,
                                  seed + j, zoom)
        layers.append((lyr, 255))
    lyr, tip = draw_scene_layer(scene, plan, ratio, scene_time, cam,
                                seed + idx, zoom)
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
    if p > 0.55:
        next_time = (p - 0.55) / 0.45 * dur * 0.5
        lyr, tip = draw_scene_layer(next_scene, plan, ratio, next_time, cam,
                                    seed + idx, zoom_dip)
        layers.append((lyr, 255))
    frame = _composite_frame(plan, ratio, cam, layers, seed)
    return _overlay_hand(frame, tip, ratio, p * 30 + seed)
