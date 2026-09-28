"""Storyboard cast: the proto whiteboard character as vector still poses.

Same figure as the RGS proto pack (tools/nexstick/baked/PROTO_*): circle
head, pear torso, stick limbs, oval hands, triangle shoes — drawn front-on
so both arms and a face read. Each still is a pose + a face + optional
expression marks, chosen from the emotion the scene context asks for.

Unit space: figure height H=260, feet at y=0, up is negative y.
Strokes: (points, color, width_scale, fill) — fill False | 'solid'.
"""
from __future__ import annotations

import math
import re

H = 260.0
HEAD_R = 0.155
HEAD_CY = -0.862
SH_Y = -0.700
HIP_Y = -0.420

# proto pack tones: light body, darker far-side hand/shoe
FILL = '#D9D4C7'
SHADE = '#8B8577'
# shirt tones — paper-pastel washes that give each cast member a color
SHIRTS = ('#8FB3E3', '#95C9A2', '#F2B27A', '#BCA8E0', '#E79A92', '#E9CB7A')


def shirt_for(key) -> str:
    """Stable shirt tone for a cast member (same name, same shirt)."""
    k = str(key or '').lower().strip()
    return SHIRTS[sum(ord(c) * (i + 1) for i, c in enumerate(k)) % len(SHIRTS)]

# arm = (elbow, hand) per side, leg = (knee, foot); x > 0 is screen right.
# All in figure heights. Only still poses — no motion is authored here.
_IDLE_ARM = ((0.15, -0.56), (0.19, -0.41))
_IDLE_LEG = ((0.055, -0.20), (0.085, 0.0))
POSES = {
    'idle':      {'r': _IDLE_ARM, 'l': _IDLE_ARM},
    'think':     {'r': ((0.15, -0.50), (0.045, -0.705)),
                  'l': _IDLE_ARM},
    'panic':     {'r': ((0.23, -0.86), (0.095, -0.945)),
                  'l': ((0.23, -0.86), (0.095, -0.945)),
                  'leg': ((0.035, -0.20), (0.11, 0.0))},
    'cheer':     {'r': ((0.19, -0.87), (0.25, -1.01)),
                  'l': ((0.19, -0.87), (0.25, -1.01)),
                  'leg': ((0.07, -0.20), (0.13, 0.0))},
    'crossed':   {'r': ((0.14, -0.55), (-0.075, -0.60)),
                  'l': ((0.14, -0.55), (-0.075, -0.60))},
    'slump':     {'r': ((0.105, -0.50), (0.11, -0.33)),
                  'l': ((0.105, -0.50), (0.11, -0.33)),
                  'head': (0.02, 0.035), 'sh': 0.02},
    'shrug':     {'r': ((0.22, -0.60), (0.29, -0.74)),
                  'l': ((0.22, -0.60), (0.29, -0.74)), 'sh': -0.015},
    'point':     {'r': ((0.21, -0.69), (0.37, -0.72)), 'l': _IDLE_ARM},
    'fist':      {'r': ((0.18, -0.87), (0.19, -1.01)), 'l': _IDLE_ARM},
    'wave':      {'r': ((0.22, -0.74), (0.26, -0.93)), 'l': _IDLE_ARM},
    'hands-hips': {'r': ((0.20, -0.56), (0.10, -0.44)),
                   'l': ((0.20, -0.56), (0.10, -0.44))},
    'hold':      {'r': ((0.20, -0.53), (0.31, -0.60)), 'l': _IDLE_ARM},
    'offer':     {'r': ((0.21, -0.56), (0.34, -0.66)),
                  'l': ((0.21, -0.56), (0.34, -0.66))},
    'reach':     {'r': ((0.25, -0.64), (0.44, -0.63)), 'l': _IDLE_ARM},
    'lift':      {'r': ((0.22, -0.74), (0.33, -0.90)), 'l': _IDLE_ARM},
}

# interaction verbs -> still pose (the emotion keeps its face and marks)
ACTIONS = {'hold': 'hold', 'carry': 'hold', 'point': 'point',
           'show': 'point', 'offer': 'offer', 'give': 'offer',
           'reach': 'reach', 'lift': 'lift', 'wave': 'wave'}

# emotion -> (pose, face, marks)
EMOTIONS = {
    'neutral':   ('idle', 'neutral', ()),
    'happy':     ('wave', 'smile', ()),
    'think':     ('think', 'think', ('bubble',)),
    'alert':     ('point', 'alert', ('exclaim',)),
    'excited':   ('cheer', 'grin', ('burst',)),
    'greedy':    ('cheer', 'grin', ('burst',)),
    'panic':     ('panic', 'scared', ('sweat', 'shake')),
    'afraid':    ('panic', 'scared', ('sweat',)),
    'calm':      ('crossed', 'serene', ()),
    'confident': ('hands-hips', 'smirk', ()),
    'sad':       ('slump', 'sad', ('drop',)),
    'defeated':  ('slump', 'sad', ('gloom',)),
    'confused':  ('shrug', 'confused', ('question',)),
    'angry':     ('fist', 'angry', ('steam',)),
    'proud':     ('fist', 'smile', ('burst',)),
    'explain':   ('point', 'smile', ()),
    'content':   ('idle', 'smile', ()),
}

# context words -> emotion, first match wins (annotation, cue, label order)
_LEXICON = [
    ('panic', r'panic|crash|dump|scared|terrif|capitulat|sell[- ]?off|'
              r'liquidat|meltdown|freak'),
    ('afraid', r'fear|worr|anxi|nervous|risk|danger|threat|stress|'
               r'frustrat|stuck|overwhelm'),
    ('excited', r'fomo|hype|\bmoon|pump|euphor|excit|\brush|chase|\bape'),
    ('greedy', r'greed|get rich|all in|lambo'),
    ('calm', r'calm|rational|patien|disciplin|steady|zen|relax|stay'),
    ('think', r'think|\bread\b|\breads\b|analy|research|\bstud|consider|interpret|'
              r'wonder|\bplan|learn|figure out'),
    ('confident', r'confiden|\bsure\b|\bwin|expert|\bpro\b|smart|better'),
    ('alert', r'\bsee|spot|notice|early|earlier|first|discover|\bfind|'
              r'aware|signal'),
    ('defeated', r'defeat|give up|quit|burn ?out|wreck|rekt|exhaust|tired'),
    ('sad', r'\bsad|\blose|\blost|\bloss|\bmiss|regret|broke|bag ?holder'),
    ('confused', r'confus|unsure|\bwhy\b|doubt|\?'),
    ('angry', r'angry|\bmad\b|furious|rage|scam|cheat|unfair'),
    ('proud', r'proud|success|achiev|made it|profit|\bgain'),
    ('happy', r'happy|glad|thank|welcome|hello|love|enjoy'),
    ('explain', r'explain|show|present|teach|guide|point'),
]


def emotion_for(role) -> str:
    """Pick the still's emotion: explicit role['emotion'] wins, then a
    legacy role['expression'] hint, then the role's own words."""
    em = str(role.get('emotion') or '').lower().strip()
    if em in EMOTIONS:
        return em
    for k in ('annotate', 'cue', 'label', 'narration'):
        text = str(role.get(k) or '').lower()
        for emo, pat in _LEXICON:
            if text and re.search(pat, text):
                return emo
    ex = str(role.get('expression') or '').lower()
    dflt = 'content' if role.get('narration') else 'neutral'
    return {'thinking': 'think', 'exclaim': 'alert'}.get(ex, dflt)


def _circle(cx, cy, rx, ry=None, n=26, a0=0.0, a1=2 * math.pi):
    ry = rx if ry is None else ry
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * rx,
             cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]


def _p(x, y):
    return (x * H, y * H)


def _face(kind, hx, hy, r):
    """Face strokes on the head circle (unit px)."""
    st = []
    ex, ey = r * 0.36, hy - r * 0.02
    my = hy + r * 0.46

    def dot(x, y, rr=r * 0.10):
        st.append((_circle(x, y, rr, n=10), 'ink', 0.8, 'solid'))

    def line(pts, w=0.75):
        st.append((pts, 'ink', w * 1.35, False))

    def arc(cx, cy, rx, ry, a0, a1, w=0.75):
        line(_circle(cx, cy, rx, ry, 12, a0, a1), w)

    if kind in ('neutral', 'think', 'smile', 'smirk', 'sad', 'angry',
                'confused'):
        dx = r * 0.10 if kind == 'think' else 0.0
        dy = -r * 0.10 if kind == 'think' else (r * 0.05 if kind == 'sad'
                                                 else 0.0)
        dot(hx - ex + dx, ey + dy)
        dot(hx + ex + dx, ey + dy)
    elif kind in ('alert', 'scared', 'grin'):
        for s in (-1, 1):
            line(_circle(hx + s * ex, ey, r * 0.19, r * 0.22, 14), 0.6)
            dot(hx + s * ex + r * (0.04 if kind == 'alert' else 0.0),
                ey + r * 0.03, r * 0.075)
    elif kind == 'serene':
        for s in (-1, 1):
            arc(hx + s * ex, ey + r * 0.05, r * 0.14, r * 0.10,
                math.pi, 2 * math.pi)
    # brows
    by = hy - r * 0.34
    bw = r * 0.18
    if kind in ('scared', 'sad'):
        for s in (-1, 1):
            line([(hx + s * (ex + bw), by + r * 0.05),
                  (hx + s * (ex - bw), by - r * 0.10)])
    elif kind == 'angry':
        for s in (-1, 1):
            line([(hx + s * (ex + bw), by - r * 0.08),
                  (hx + s * (ex - bw), by + r * 0.09)], 0.9)
    elif kind in ('alert', 'grin'):
        for s in (-1, 1):
            arc(hx + s * ex, by - r * 0.08, bw, r * 0.07, math.pi,
                2 * math.pi)
    elif kind in ('think', 'confused'):
        line([(hx - ex - bw, by + r * 0.02), (hx - ex + bw, by + r * 0.02)])
        arc(hx + ex, by - r * 0.06, bw, r * 0.09, math.pi, 2 * math.pi)
    elif kind == 'smirk':
        for s in (-1, 1):
            line([(hx + s * (ex + bw), by + r * 0.03),
                  (hx + s * (ex - bw), by + r * 0.06)])
    # mouth
    if kind in ('smile', 'serene'):
        arc(hx, my - r * 0.10, r * 0.26, r * 0.16, 0.15 * math.pi,
            0.85 * math.pi)
    elif kind == 'grin':
        pts = _circle(hx, my - r * 0.10, r * 0.30, r * 0.24, 14, 0.0, math.pi)
        st.append((pts + [pts[0]], 'ink', 0.7, 'solid'))
    elif kind == 'smirk':
        line([(hx - r * 0.18, my), (hx + r * 0.10, my - r * 0.02),
              (hx + r * 0.24, my - r * 0.10)])
    elif kind == 'scared':
        st.append((_circle(hx, my, r * 0.12, r * 0.16, 12), 'ink', 0.7,
                   'solid'))
    elif kind == 'alert':
        line(_circle(hx, my, r * 0.09, r * 0.11, 10), 0.7)
    elif kind in ('sad', 'angry'):
        arc(hx, my + r * 0.10, r * 0.22, r * 0.13, 1.15 * math.pi,
            1.85 * math.pi)
    elif kind == 'confused':
        line([(hx - r * 0.20, my), (hx - r * 0.07, my - r * 0.06),
              (hx + r * 0.06, my + r * 0.03), (hx + r * 0.20, my - r * 0.03)])
    elif kind == 'think':
        line([(hx - r * 0.02, my), (hx + r * 0.20, my - r * 0.02)])
    else:
        line([(hx - r * 0.15, my), (hx + r * 0.15, my)])
    return st


def _marks(kinds, hx, hy, r, top_y):
    """Expression marks around the head, in unit px."""
    st = []
    ink = 'ink'
    for m in kinds:
        if m == 'bubble':
            bx, by = hx + r * 1.55, hy - r * 1.55
            st.append((_circle(bx, by, r * 0.80, r * 0.58, 22), ink, 0.7,
                       False))
            for dx, dy, rr in ((0.62, -0.42, 0.12), (0.88, -0.78, 0.18)):
                st.append((_circle(hx + r * dx, hy + r * dy, r * rr, n=10),
                           ink, 0.6, False))
        elif m == 'exclaim':
            for i, (dx, ang) in enumerate(((1.15, -0.30), (1.55, 0.0))):
                x0, y0 = hx + r * dx, hy - r * 1.25
                ln = r * (0.62 if i == 0 else 0.72)
                x1 = x0 + math.sin(ang) * ln
                y1 = y0 + math.cos(ang) * ln
                st.append(([(x0, y0), (x1, y1)], ink, 1.05, False))
                st.append((_circle(x1 + math.sin(ang) * r * 0.26,
                                   y1 + r * 0.26, r * 0.07, n=8),
                           ink, 0.8, 'solid'))
        elif m == 'burst':
            for a in (-2.6, -2.1, -1.57, -1.05, -0.55):
                c, s = math.cos(a), math.sin(a)
                st.append(([(hx + c * r * 1.35, top_y * 0 + hy + s * r * 1.35),
                            (hx + c * r * 1.75, hy + s * r * 1.75)],
                           ink, 0.8, False))
        elif m in ('sweat', 'drop'):
            sx = hx + r * (1.45 if m == 'sweat' else 0.55)
            sy = hy - r * (0.35 if m == 'sweat' else -0.15)
            drop = [(sx, sy - r * 0.30)]
            drop += _circle(sx, sy, r * 0.14, r * 0.15, 10,
                            -0.1 * math.pi, 1.1 * math.pi)
            drop.append(drop[0])
            st.append((drop, 'a_blue', 0.6, 'solid'))
            st.append((drop, ink, 0.55, False))
            if m == 'sweat':
                sx2 = hx - r * 1.45
                d2 = [(sx2, sy - r * 0.10)] + _circle(
                    sx2, sy + r * 0.18, r * 0.11, r * 0.12, 10,
                    -0.1 * math.pi, 1.1 * math.pi)
                d2.append(d2[0])
                st.append((d2, 'a_blue', 0.6, 'solid'))
                st.append((d2, ink, 0.55, False))
        elif m == 'shake':
            for s in (-1, 1):
                for k in (0, 1):
                    x = hx + s * r * (1.45 + k * 0.28)
                    st.append(([(x, hy - r * 0.35), (x + s * r * 0.06, hy),
                                (x, hy + r * 0.35)], ink, 0.6, False))
        elif m == 'question':
            qx, qy = hx + r * 1.35, hy - r * 1.35
            q = _circle(qx, qy, r * 0.30, r * 0.30, 12, -math.pi, 0.45 * math.pi)
            q += [(qx, qy + r * 0.52)]
            st.append((q, ink, 1.0, False))
            st.append((_circle(qx, qy + r * 0.82, r * 0.07, n=8), ink, 0.8,
                       'solid'))
        elif m == 'gloom':
            for dx in (-0.55, 0.0, 0.55):
                x = hx + r * dx
                st.append(([(x, hy - r * 1.30), (x + r * 0.05, hy - r * 1.62)],
                           'pale', 0.7, False))
        elif m == 'steam':
            for s in (-1, 1):
                x = hx + s * r * 1.05
                st.append(([(x, hy - r * 0.85), (x + s * r * 0.15, hy - r * 1.1),
                            (x, hy - r * 1.35), (x + s * r * 0.15, hy - r * 1.6)],
                           ink, 0.7, False))
    return st


def hand_uv(emotion='neutral', flip=False, action=''):
    """Right (leading) hand position as a fraction (u, v) of the figure's
    ink bounds — where a held prop is anchored."""
    body, _m, _hb = figure(emotion, flip, action)
    pose_n = ACTIONS.get(action) or EMOTIONS.get(
        emotion, EMOTIONS['neutral'])[0]
    pz = POSES[pose_n]
    sgn = -1 if flip else 1
    hx, hy = _p(sgn * pz['r'][1][0], pz['r'][1][1] + pz.get('sh', 0.0))
    xs = [q[0] for st in body for q in st[0]]
    ys = [q[1] for st in body for q in st[0]]
    return ((hx - min(xs)) / max(1e-6, max(xs) - min(xs)),
            (hy - min(ys)) / max(1e-6, max(ys) - min(ys)))


def figure(emotion='neutral', flip=False, action='', shirt=None):
    """-> (body_strokes, mark_strokes, head_box) in unit px (feet at 0).
    `action` (hold/point/offer/reach...) swaps the arm pose only."""
    pose_n, face_n, mark_n = EMOTIONS.get(emotion, EMOTIONS['neutral'])
    pose_n = ACTIONS.get(str(action or '').lower(), pose_n)
    pz = POSES[pose_n]
    hdx, hdy = pz.get('head', (0.0, 0.0))
    shd = pz.get('sh', 0.0)
    sh_y = SH_Y + shd
    hx, hy = _p(hdx, HEAD_CY + hdy)
    r = HEAD_R * H
    body = []
    fill, ink = FILL, 'ink'
    # head first — the artist inks the face before the body
    head = _circle(hx, hy, r, n=30)
    body.append((head, fill, 0.95, 'solid'))
    body += _face(face_n, hx, hy, r)
    # pear torso
    tw, bw = 0.125, 0.062
    ty, byy = sh_y + 0.005, HIP_Y + 0.012
    # simpler robust outline: left edge down, bottom curve, right edge up,
    # shoulder arc across
    left = [_p(-tw + (tw - bw) * (i / 8) ** 1.25, ty + (byy - ty) * i / 8)
            for i in range(9)]
    bottom = [(math.cos(a) * bw * H, byy * H + math.sin(a) * bw * H * 0.7)
              for a in [math.pi - math.pi * k / 10 for k in range(11)]]
    rgt = [(-x, y) for x, y in reversed(left)]
    shoulder = [(math.cos(a) * tw * H, ty * H - math.sin(a) * tw * H * 0.28)
                for a in [math.pi * k / 10 for k in range(11)]]
    torso_poly = left + bottom[1:] + rgt[1:] + shoulder[1:]
    torso_poly.append(torso_poly[0])
    body.append((torso_poly, shirt or fill, 1.0, 'solid'))
    # legs
    legs = pz.get('leg', _IDLE_LEG)
    for s in (-1, 1):
        hip = _p(s * 0.045, HIP_Y + 0.03)
        kn = _p(s * legs[0][0], legs[0][1])
        ft = _p(s * legs[1][0], legs[1][1])
        body.append(([hip, kn, ft], ink, 0.85, False))
        shoe = [(ft[0] - s * 0.012 * H, ft[1] - 0.048 * H),
                (ft[0] + s * 0.05 * H, ft[1]),
                (ft[0] - s * 0.03 * H, ft[1]),
                (ft[0] - s * 0.012 * H, ft[1] - 0.048 * H)]
        body.append((shoe, SHADE if s < 0 else fill, 0.8, 'solid'))
    # arms
    sgn = -1 if flip else 1
    for side, s in (('l', -1), ('r', 1)):
        el, hd = pz[side]
        s2 = s * sgn
        shp = _p(s2 * (tw - 0.012), sh_y + 0.006)
        elp = _p(s2 * el[0], el[1] + shd)
        hdp = _p(s2 * hd[0], hd[1] + shd)
        body.append(([shp, elp, hdp], ink, 0.85, False))
        body.append((_circle(hdp[0], hdp[1], 0.028 * H, 0.034 * H, 12),
                     SHADE if s2 < 0 else fill, 0.8, 'solid'))
    inked = []
    for st in body:
        inked.append(st)
        if st[3] == 'solid' and st[1] != 'ink':
            inked.append((st[0], 'ink', 0.62, False))
    body = inked
    top_y = min(q[1] for st in body for q in st[0])
    marks = _marks(mark_n, hx, hy, r, top_y)
    if flip:
        marks = [([(2 * hx - x, y) for x, y in pts], c, w, f)
                 for pts, c, w, f in marks]
    return body, marks, (hx - r, hy - r, hx + r, hy + r)
