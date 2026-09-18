"""Whiteboard V3 board renderer — expressive pictogram scenes.

Replaces the labeled-rect generic semantic path with the reel's (and the
crypto-explainer genre's) visual language: bold expressive characters with
faces and poses, filled illustrative props, thought bubbles, sparkles and
ground swash — composed as scenes, not rows of icons. Strokes replay
progressively via the compiler's per-step ``drawPlan`` timing. Everything is
drawn in board world coordinates through the preserved adapter's camera and
rough-stroke helpers, so unmodified preserved modules keep their contract.
"""
from __future__ import annotations

import math
import re

from PIL import Image, ImageDraw

import whiteboard_pil_adapter as wbp

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
    """Fuller character: head with face + hair, accent shirt, posed limbs."""
    s = [
        (_ellipse(0, -0.34, 0.15, 0.15, 26), 'paper', 1.0, True),
        (_ellipse(0, -0.34, 0.15, 0.15, 26), 'ink', 1.2),
        (_arc(0, -0.40, 0.15, 0.12, 200, -20, 14), 'ink', 1.4),
        (_arc(0.13, -0.36, 0.05, 0.06, 200, 340, 10), 'ink', 1.2),
        (_ellipse(-0.07, -0.33, 0.018, 0.022, 8), 'ink', 0.9, True),
        (_ellipse(0.05, -0.33, 0.018, 0.022, 8), 'ink', 0.9, True),
        (_arc(-0.06, -0.40, 0.03, 0.02, 200, 340, 8), 'ink', 0.8),
        (_arc(0.04, -0.40, 0.03, 0.02, 200, 340, 8), 'ink', 0.8),
        (_arc(-0.01, -0.28, 0.06, 0.05, 20, 160, 10), 'ink', 0.9),
        (_P((-0.14, -0.14), (0.14, -0.14), (0.17, 0.12), (-0.17, 0.12), (-0.14, -0.14)), 'accfill', 1.0, True),
        (_P((-0.15, -0.18), (0.15, -0.18), (0.19, 0.16), (-0.19, 0.16), (-0.15, -0.18)), 'ink', 1.3),
        (_P((-0.05, -0.18), (0, -0.12), (0.05, -0.18)), 'ink', 0.9),
    ]
    if pose == 'point':
        s += [(_P((0.16, -0.12), (0.30, -0.16), (0.44, -0.14)), 'ink', 1.2),
              (_ellipse(0.46, -0.14, 0.035, 0.035, 8), 'ink', 1.0, True),
              (_P((-0.16, -0.12), (-0.24, 0.04), (-0.20, 0.16)), 'ink', 1.2)]
    elif pose == 'think':
        s += [(_P((0.16, -0.12), (0.24, -0.02), (0.10, -0.24)), 'ink', 1.2),
              (_ellipse(0.09, -0.26, 0.035, 0.035, 8), 'ink', 1.0, True),
              (_P((-0.16, -0.12), (-0.24, 0.04), (-0.20, 0.16)), 'ink', 1.2)]
    elif pose == 'cheer':
        s += [(_P((0.16, -0.12), (0.28, -0.28), (0.36, -0.40)), 'ink', 1.2),
              (_P((-0.16, -0.12), (-0.28, -0.28), (-0.36, -0.40)), 'ink', 1.2),
              (_ellipse(0.37, -0.42, 0.035, 0.035, 8), 'ink', 1.0, True),
              (_ellipse(-0.37, -0.42, 0.035, 0.035, 8), 'ink', 1.0, True)]
    elif pose == 'hold':
        s += [(_P((0.16, -0.12), (0.28, 0.0), (0.36, 0.08)), 'ink', 1.2),
              (_P((-0.16, -0.12), (-0.20, 0.02), (-0.10, 0.12)), 'ink', 1.2)]
    else:
        s += [(_P((0.16, -0.12), (0.22, 0.04), (0.20, 0.18)), 'ink', 1.2),
              (_P((-0.16, -0.12), (-0.22, 0.04), (-0.20, 0.18)), 'ink', 1.2)]
    s += [(_P((-0.09, 0.16), (-0.11, 0.36), (-0.13, 0.50)), 'ink', 1.2),
          (_P((0.09, 0.16), (0.11, 0.36), (0.13, 0.50)), 'ink', 1.2),
          (_P((-0.13, 0.50), (-0.22, 0.50)), 'ink', 1.3),
          (_P((0.13, 0.50), (0.22, 0.50)), 'ink', 1.3)]
    if facing < 0:
        s = [([(-x, y) for x, y in pts], c, w, *rest) for pts, c, w, *rest in s]
    return s


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
# Concept → drawing
# ---------------------------------------------------------------------------

_ICON_KEYWORDS = {
    'person': ('person', 'customer', 'user', 'human', 'operator', 'worker', 'courier',
               'staff', 'client', 'buyer', 'seller', 'employee', 'man', 'woman',
               'child', 'team', 'audience', 'investor', 'trader', 'founder',
               'developer', 'miner', 'holder', 'member'),
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
             'headquarters', 'organization', 'vault', 'custodian'),
    'shield': ('shield', 'security', 'protection', 'privacy', 'insurance',
               'compliance', 'audit', 'trust', 'safety', 'secure'),
    'gear': ('automation', 'process', 'workflow', 'engine', 'mechanism', 'machine',
             'protocol', 'algorithm', 'mining', 'gear'),
    'lightbulb': ('idea', 'insight', 'learn', 'knowledge', 'solution', 'innovation',
                  'discovery', 'strategy', 'tip', 'answer'),
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


def _strokes_for(icon: str, pose='point'):
    if icon == 'person':
        return _character_strokes(pose)
    if icon == 'agent':
        return _robot_strokes()
    return PROPS.get(icon, PROPS['tile'])


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
        slots[pi] = dict(center=(cx_p, cy - char_size * 0.02), size=_size_for(icons[pi]),
                         icon=icons[pi], label=labels[pi],
                         pose='point' if icons[pi] == 'person' else None, bubble=False)
        area_x0 = x + (0 if portrait else w * 0.42)
        rest = props + people[1:]
        n = len(rest)
        if portrait and n > 2:
            for k, i in enumerate(rest):
                col, row = k % 2, k // 2
                slots[i] = dict(
                    center=(x + w * (0.30 + 0.40 * col), y + h * (0.40 + 0.36 * row)),
                    size=_size_for(icons[i]) * 0.9, icon=icons[i], label=labels[i],
                    pose='stand' if icons[i] == 'person' else None, bubble=False)
        else:
            aw = x + w - area_x0
            step = aw / max(1, n)
            for k, i in enumerate(rest):
                slots[i] = dict(
                    center=(area_x0 + step * (k + 0.5), cy),
                    size=_size_for(icons[i]), icon=icons[i], label=labels[i],
                    pose=('cheer' if len(rest) > 1 else 'stand') if icons[i] == 'person' else None,
                    bubble=False)
    elif people:
        n = len(people)
        step = w / (n + 1)
        for k, i in enumerate(people):
            slots[i] = dict(center=(x + step * (k + 1), cy - char_size * 0.02),
                            size=_size_for(icons[i]), icon=icons[i], label=labels[i],
                            pose='stand' if n > 1 else 'point', bubble=False)
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
                    pose=None, bubble=False)
        else:
            margin = w * (0.10 if n > 3 else 0.18)
            step = (w - 2 * margin) / max(1, n - 1) if n > 1 else 0
            size = prop_size * (1.25 if n <= 2 else 1.0)
            for k, i in enumerate(props):
                jitter = (0.03 * h) * (1 if k % 2 else -1) if n > 2 else 0
                slots[i] = dict(center=(x + margin + step * k, cy + jitter),
                                size=size, icon=icons[i], label=labels[i],
                                pose=None, bubble=False)

    if people:
        for s in slots:
            if s is None or s['icon'] in ('person', 'agent'):
                continue
            low = s['label'].lower()
            if any(k in low for k in ('want', 'need', 'idea', 'dream', 'goal',
                                      'question', 'why', 'wish', 'hope', 'think')):
                s['bubble'] = True
                s['pose'] = 'think'
                break
        if people and slots[people[0]] is not None:
            for i in people:
                if any(s is not None and s.get('bubble') for s in slots):
                    slots[people[0]]['pose'] = 'think'
    return [s for s in slots if s is not None]


# ---------------------------------------------------------------------------
# Drawing — adapter helpers do camera mapping, rough strokes, progressive ink
# ---------------------------------------------------------------------------

def _palette(plan):
    pal = wbp._pal(plan)
    accf = wbp._mix(pal['bgc'], pal['accentc'], 0.20)
    return {'ink': pal['inkc'], 'accent': pal['accentc'],
            'pale': (pal['secondaryc'][0], pal['secondaryc'][1], pal['secondaryc'][2], 190),
            'accfill': accf, 'paper': pal['bgc'], 'bg': pal['bg']}


def _draw_strokes(layer, strokes, center, size, cam, colors, ratio, progress, seed):
    n = len(strokes)
    if n == 0:
        return
    scale = (min(*wbp.RATIO_SIZES[ratio]) / (650 if ratio != '9:16' else 760))
    lw = max(2.0, size * scale * 0.028)
    d = ImageDraw.Draw(layer, 'RGBA')
    for j, st in enumerate(strokes):
        pts, col, wscale = st[0], st[1], st[2]
        fill = st[3] if len(st) > 3 else False
        p = wbp._clamp(progress * n - j)
        if p <= 0:
            break
        pts_b = [(center[0] + px * size, center[1] + py * size) for px, py in pts]
        pts_s = [wbp._map_point(q, cam, ratio) for q in pts_b]
        if fill:
            if p >= 0.9:
                d.polygon([(int(a), int(b)) for a, b in pts_s], fill=colors[col])
            continue
        wbp._line(layer, pts_s, colors[col], lw * wscale, seed + j * 13, .26, p)


def _headline(scene, layer, plan, zone, cam, ratio):
    primary = str((scene.get('screenCopy') or {}).get('primary') or '').strip()
    if not primary:
        return
    colors = _palette(plan)
    d = ImageDraw.Draw(layer, 'RGBA')
    fnt = wbp._font(max(16, wbp.RATIO_SIZES[ratio][0] // 34), b=True)
    txt = primary.upper()
    hx, hy = wbp._map_point((zone['x'] + 26, zone['y'] + 8), cam, ratio)
    d.text((hx, hy), txt, font=fnt, fill=colors['ink'])
    tw = d.textlength(txt, font=fnt)
    ws = max(2.0, fnt.size * 0.09)
    y_u = hy + fnt.size * 1.10
    pts = [(hx + tw * t / 18, y_u + math.sin(t * 1.4) * ws * 0.8) for t in range(19)]
    wbp._line(layer, pts, colors['ink'], ws, 917, .22, 1.0)
    wbp._line(layer, [(a, b + ws * 1.6) for a, b in pts], colors['accent'], ws * 0.55, 733, .22, 1.0)


def _caption(layer, center, size, label, cam, colors, ratio):
    d = ImageDraw.Draw(layer, 'RGBA')
    fnt = wbp._font(max(11, wbp.RATIO_SIZES[ratio][0] // 70), b=True)
    txt = str(label).upper()
    cx, cy = wbp._map_point(center, cam, ratio)
    scale = (min(*wbp.RATIO_SIZES[ratio]) / (650 if ratio != '9:16' else 760))
    y = cy + size * scale * 0.58 + fnt.size * 0.3
    tw = d.textlength(txt, font=fnt)
    maxw = wbp.RATIO_SIZES[ratio][0] * 0.30
    if tw > maxw:
        txt = txt[: int(len(txt) * maxw / tw) - 1] + '…'
        tw = d.textlength(txt, font=fnt)
    d.text((cx - tw / 2, y), txt, font=fnt, fill=colors['ink'])
    pad = tw * 0.05
    wbp._line(layer, [(cx - tw / 2 - pad, y + fnt.size * 1.15), (cx + tw / 2 + pad, y + fnt.size * 1.15)],
              colors['accent'], max(1.4, fnt.size * 0.07), 311, .2, 1.0)


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

    order = {'icon': 0, 'bubble': 1, 'sparkle': 2, 'caption': 3}
    groups = []
    for s in slots:
        groups.append(('icon', _strokes_for(s['icon'], s.get('pose') or 'point'),
                       s['center'], s['size'], s))
        if s.get('bubble'):
            bc = (s['center'][0] + s['size'] * 0.55, s['center'][1] - s['size'] * 0.62)
            groups.append(('bubble', _bubble_strokes(), bc, s['size'] * 0.62, s))
        if s['icon'] in ('check', 'coin', 'coins', 'rocket', 'lightbulb', 'chart', 'target'):
            groups.append(('sparkle', _sparkle_strokes(), s['center'], s['size'], s))
    for s in slots:
        groups.append(('caption', None, s['center'], s['size'], s))
    groups.sort(key=lambda g: order[g[0]])

    dp = scene['whiteboardRuntime'].get('drawPlan') or []
    n_draw = max(1, sum(1 for g in groups if g[0] != 'caption'))
    out = []
    for gi, g in enumerate(groups):
        j = min(gi, len(dp) - 1)
        st = dp[j] if dp else {}
        start = float(st.get('start', gi / n_draw))
        end = float(st.get('end', (gi + 1) / n_draw))
        out.append((g, start, max(end, start + 0.02)))
    return out


def draw_scene_layer(scene: dict, plan: dict, ratio: str, scene_time: float,
                     cam=None, seed=7) -> Image.Image:
    layer = Image.new('RGBA', wbp.RATIO_SIZES[ratio], (0, 0, 0, 0))
    cam = cam or wbp._camera(scene, ratio)
    zone = scene['whiteboardRuntime']['boardZone']
    colors = _palette(plan)
    for gi, ((kind, strokes, center, size, slot), start, end) in enumerate(
            _scene_groups(scene, plan, ratio)):
        if kind == 'caption':
            if scene_time >= end:
                _caption(layer, center, size, slot['label'], cam, colors, ratio)
            continue
        p = wbp._ease(wbp._clamp((scene_time - start) / max(0.05, end - start)))
        if p <= 0:
            continue
        _draw_strokes(layer, strokes, center, size, cam, colors, ratio, p,
                      seed + gi * 97)
    _headline(scene, layer, plan, zone, cam, ratio)
    return layer


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
    scenes = plan.get('sceneSpecs') or [scene]
    idx = next((i for i, s in enumerate(scenes)
                if s.get('sceneId') == scene.get('sceneId')), 0)
    wb = scene.get('whiteboardRuntime') or {}
    seed = int(wb.get('seed', 7))
    layers = [(draw_scene_layer(scenes[j], plan, ratio, 999.0, cam, seed + j), 255)
              for j in range(idx)]
    layers.append((draw_scene_layer(scene, plan, ratio, scene_time, cam, seed + idx), 255))
    return _composite_frame(plan, ratio, cam, layers, seed)


def render_transition_frame(prev_scene, next_scene, plan, ratio, p: float):
    """Camera slide between zones; previous scenes stay on the board."""
    c0 = wbp._camera(prev_scene, ratio)
    c1 = wbp._camera(next_scene, ratio)
    q = wbp._ease(wbp._clamp(p))
    cam = (c0[0] + (c1[0] - c0[0]) * q, c0[1] + (c1[1] - c0[1]) * q)
    scenes = plan.get('sceneSpecs') or [next_scene]
    idx = next((i for i, s in enumerate(scenes)
                if s.get('sceneId') == next_scene.get('sceneId')), len(scenes) - 1)
    wb = next_scene.get('whiteboardRuntime') or {}
    seed = int(wb.get('seed', 9))
    layers = [(draw_scene_layer(scenes[j], plan, ratio, 999.0, cam, seed + j), 255)
              for j in range(idx)]
    if p > 0.55:
        dur = float(wb.get('sceneDuration') or 4.0)
        layers.append((draw_scene_layer(next_scene, plan, ratio,
                                        (p - 0.55) / 0.45 * dur * 0.5, cam, seed + idx), 255))
    return _composite_frame(plan, ratio, cam, layers, seed)
