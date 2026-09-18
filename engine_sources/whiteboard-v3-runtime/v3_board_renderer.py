"""V3 scene renderer — pictogram vocabulary matching the reference reel.

Draws each beat the way the lost V3 lineage did: an underlined headline, a
horizontal row of hand-drawn pictograms with dashed connectors, per-icon
caption labels, and an optional annotation caption — all on the shared board
coordinate system so camera travel and board memory still apply.

Reuses the preserved adapter's ink primitives (`_line`, `_ellipse_points`,
`_font`, `_pal`, `_paper_texture`, `_map_point`, `RATIO_SIZES`) — only the
scene composition is reconstructed.
"""
from __future__ import annotations

import math
import re

import whiteboard_pil_adapter as wbp

_font = wbp._font
_line = wbp._line
_ellipse_points = wbp._ellipse_points
_rect_points = wbp._rect_points
_clamp = wbp._clamp


# ---------------------------------------------------------------------------
# Pictogram strokes
#
# Each icon is a list of strokes in unit space centered at (0,0):
#   (points, color, width_scale)   color in {'ink','accent','pale'}
# Icons render ~[-0.5, 0.5] in both axes; the caller scales to slot size.
# ---------------------------------------------------------------------------

def _P(*pts):
    return [tuple(p) for p in pts]


ICONS: dict[str, list[tuple[list, str, float]]] = {}


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


ICONS = {
    # stick figure with accent shirt band (the reel's person style)
    'person': [
        (_ellipse_points(0, -0.32, 0.12, 0.12, 24), 'ink', 1.0),
        (_P((0, -0.20), (0, 0.12)), 'ink', 1.1),
        (_P((-0.15, -0.04), (0, -0.02), (0.17, -0.12)), 'ink', 1.0),
        (_P((0, 0.12), (-0.13, 0.46)), 'ink', 1.0),
        (_P((0, 0.12), (0.15, 0.46)), 'ink', 1.0),
        (_P((-0.12, 0.0), (0.12, -0.05)), 'accent', 0.8),
        (_P((-0.12, 0.04), (0.13, -0.01)), 'accent', 0.8),
    ],
    # rounded-square robot face, antenna, eyes, smile
    'agent': [
        (_rounded_rect(0, 0.02, 0.52, 0.52, 0.12), 'ink', 1.1),
        (_P((0, -0.24), (0, -0.38)), 'ink', 0.9),
        (_ellipse_points(0, -0.42, 0.035, 0.035, 14), 'ink', 0.9),
        (_ellipse_points(-0.12, -0.04, 0.045, 0.055, 14), 'accent', 0.9),
        (_ellipse_points(0.12, -0.04, 0.045, 0.055, 14), 'accent', 0.9),
        (_P((-0.13, 0.14), (-0.05, 0.20), (0.06, 0.20), (0.14, 0.13)), 'ink', 0.8),
        (_P((-0.24, -0.24), (0.24, -0.24)), 'accent', 0.5),
    ],
    # envelope
    'envelope': [
        (_rect_points(-0.34, -0.24, 0.34, 0.24), 'ink', 1.0),
        (_P((-0.34, -0.24), (0, 0.06), (0.34, -0.24)), 'ink', 1.0),
        (_P((-0.10, 0.24), (0.02, 0.12), (0.14, 0.24)), 'accent', 0.7),
    ],
    # document card with text lines
    'document': [
        (_rounded_rect(0, 0, 0.44, 0.56, 0.04), 'ink', 1.0),
        (_P((-0.14, -0.14), (0.14, -0.14)), 'pale', 0.8),
        (_P((-0.14, -0.01), (0.14, -0.01)), 'pale', 0.8),
        (_P((-0.14, 0.12), (0.05, 0.12)), 'pale', 0.8),
    ],
    # context card — document + bold title line
    'context': [
        (_rounded_rect(0, 0, 0.58, 0.42, 0.04), 'ink', 1.1),
        (_P((-0.20, -0.08), (0.20, -0.08)), 'pale', 0.8),
        (_P((-0.20, 0.03), (0.20, 0.03)), 'pale', 0.8),
        (_P((-0.20, 0.14), (0.10, 0.14)), 'pale', 0.8),
    ],
    # stacked cards (queue / routine work)
    'stack': [
        (_rect_points(-0.40, -0.10, 0.06, 0.28), 'ink', 0.9),
        (_rect_points(-0.30, -0.22, 0.16, 0.16), 'ink', 0.9),
        (_rect_points(-0.20, -0.34, 0.40, 0.04), 'ink', 0.9),
    ],
    # funnel
    'funnel': [
        (_P((-0.30, -0.34), (0.30, -0.34), (0.08, 0.02), (0.08, 0.30), (-0.08, 0.30), (-0.08, 0.02), (-0.30, -0.34)), 'ink', 1.0),
        (_P((-0.20, -0.16), (0.20, -0.16)), 'accent', 0.7),
    ],
    # wrench — open jaw arc, diagonal handle, end knob
    'tool': [
        ([(-0.10 + 0.16 * math.cos(math.radians(210 - 260 * i / 20)),
           -0.24 + 0.16 * math.sin(math.radians(210 - 260 * i / 20))) for i in range(21)], 'ink', 1.1),
        (_P((0.02, -0.12), (0.30, 0.34)), 'ink', 1.4),
        (_ellipse_points(0.32, 0.40, 0.05, 0.05, 12), 'ink', 1.0),
        (_P((-0.22, -0.36), (-0.10, -0.30)), 'accent', 0.7),
    ],
    # circled checkmark
    'check': [
        (_ellipse_points(0, 0, 0.30, 0.30, 30), 'accent', 1.0),
        (_P((-0.14, 0.0), (-0.04, 0.12), (0.16, -0.14)), 'ink', 1.1),
    ],
    # axes + rising line + callout bubble
    'chart': [
        (_P((-0.38, -0.30), (-0.38, 0.36), (0.40, 0.36)), 'ink', 1.0),
        (_P((-0.30, 0.26), (-0.10, 0.16), (0.05, -0.02), (0.24, -0.20)), 'accent', 1.2),
        (_ellipse_points(0.30, -0.30, 0.14, 0.12, 20), 'accent', 0.8),
    ],
    # clock
    'clock': [
        (_ellipse_points(0, 0, 0.28, 0.28, 28), 'ink', 1.0),
        (_P((0, 0), (0, -0.16)), 'ink', 0.9),
        (_P((0, 0), (0.12, 0.05)), 'accent', 0.9),
    ],
    # phone
    'phone': [
        (_rounded_rect(0, 0, 0.28, 0.56, 0.06), 'ink', 1.0),
        (_ellipse_points(0, 0.20, 0.03, 0.03, 10), 'accent', 0.8),
        (_P((-0.08, -0.18), (0.08, -0.18)), 'pale', 0.7),
    ],
    # question card — for uncertain/hard cases
    'question': [
        (_rounded_rect(0, 0, 0.42, 0.54, 0.05), 'ink', 1.0),
        (_P((-0.07, -0.16), (0.02, -0.20), (0.09, -0.13), (0.06, -0.03), (0.0, 0.02), (0.0, 0.08)), 'accent', 0.9),
        (_ellipse_points(0.0, 0.16, 0.02, 0.02, 8), 'accent', 0.9),
    ],
    # generic rounded tile
    'tile': [
        (_rounded_rect(0, 0, 0.5, 0.5, 0.08), 'ink', 1.0),
        (_P((-0.12, 0), (0.12, 0)), 'pale', 0.7),
    ],
}

_ICON_KEYWORDS = {
    # people outrank 'agent' so 'human agent' renders as a person, not the robot
    'person': ('person', 'customer', 'user', 'human', 'operator', 'worker', 'courier',
               'staff', 'client', 'buyer', 'seller', 'employee', 'man', 'woman',
               'child', 'team', 'audience'),
    'agent': ('agent', 'robot', 'ai', 'bot', 'assistant', 'automation', 'system'),
    'envelope': ('inbox', 'request', 'mail', 'email', 'message', 'letter', 'send',
                 'ticket', 'notification'),
    'document': ('document', 'report', 'file', 'form', 'contract', 'invoice',
                 'proposal', 'brief', 'order', 'application', 'paper', 'memory',
                 'card', 'record', 'history', 'log'),
    'context': ('context', 'details', 'attached', 'attachment', 'summary'),
    'stack': ('queue', 'routine', 'stack', 'backlog', 'cases', 'tickets', 'batch',
              'list', 'inbox pile'),
    'funnel': ('funnel', 'filter', 'automate', 'triage', 'sort', 'screen', 'pipeline'),
    'tool': ('tool', 'wrench', 'settings', 'gear', 'fix', 'repair', 'utility'),
    'check': ('check', 'validate', 'done', 'verified', 'approve', 'success', 'complete'),
    'chart': ('chart', 'result', 'metric', 'growth', 'graph', 'measure', 'data',
              'response time', 'kpi', 'trend', 'performance'),
    'clock': ('time', 'clock', 'minute', 'hour', 'duration', 'wait', 'sla'),
    'phone': ('phone', 'smartphone', 'mobile', 'call'),
    'question': ('hard cases', 'uncertain', 'unknown', 'question', 'exception',
                 'edge case', 'risk'),
}


_PERSON_AGENT_PREFIXES = ('human', 'support', 'customer', 'live', 'service', 'real')


def icon_for(concept: str) -> str:
    phrase = str(concept).lower().replace('-', ' ').replace('_', ' ').strip()
    words = phrase.split()
    wset = set(words)
    # 'human agent' reads as a person; bare 'agent'/'AI agent' reads as the robot
    if any(f'{k} agent' in phrase or f'{k} rep' in phrase for k in _PERSON_AGENT_PREFIXES):
        return 'person'
    # multi-word keys are the most specific signal
    for icon, keys in _ICON_KEYWORDS.items():
        if any(' ' in k and k in phrase for k in keys):
            return icon
    # the last word is the noun — 'customer request' is a request, not a person
    if words:
        last = words[-1]
        for icon, keys in _ICON_KEYWORDS.items():
            if last in keys:
                return icon
    for icon, keys in _ICON_KEYWORDS.items():
        if any(k in wset or (len(k) > 3 and k in phrase) for k in keys):
            return icon
    if re.search(r'\d', phrase):
        # '12 min' reads as a clock; '12 %' reads as data
        if re.search(r'\b(min|mins|minute|minutes|hour|hours|sec|seconds|day|days|am|pm)\b', phrase):
            return 'clock'
        return 'chart'
    return 'tile'


# ---------------------------------------------------------------------------
# Scene composition
# ---------------------------------------------------------------------------

def _slot_centers(n: int, zone: dict, ratio: str):
    x, y, w, h = zone['x'], zone['y'], zone['w'], zone['h']
    portrait = ratio == '9:16'
    cy = y + h * (0.50 if portrait else 0.52)
    if portrait and n > 2:
        # two columns in portrait
        rows = math.ceil(n / 2)
        out = []
        for i in range(n):
            col, row = i % 2, i // 2
            out.append((x + w * (0.30 if col == 0 else 0.70),
                        y + h * 0.38 + row * (h * 0.62 / max(1, rows))))
        return out
    margin = w * 0.10
    if n == 1:
        return [(x + w * 0.5, cy)]
    return [
        (x + margin + (w - 2 * margin) * (i / (n - 1)), cy)
        for i in range(n)
    ]


def _dashes(a, b, n=3):
    """Short dashed connector between two points, like the reel's '- - -'."""
    out = []
    for i in range(n):
        t0 = 0.18 + 0.72 * i / n
        t1 = t0 + 0.72 / n * 0.55
        out.append([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                    (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)])
    return out


def _draw_icon(layer, icon, cx, cy, s, progress, seed, pal, opacity=255):
    """Draw a pictogram at (cx, cy), size s board px, stroke-by-stroke."""
    strokes = ICONS.get(icon, ICONS['tile'])
    ink = (pal['inkc'][0], pal['inkc'][1], pal['inkc'][2], int(opacity))
    acc = (pal['accentc'][0], pal['accentc'][1], pal['accentc'][2], int(opacity))
    pale = (pal['secondaryc'][0], pal['secondaryc'][1], pal['secondaryc'][2], int(opacity))
    colors = {'ink': ink, 'accent': acc, 'pale': pale}
    width = pal['stroke']
    n = len(strokes)
    for j, (pts, cname, wscale) in enumerate(strokes):
        p = _clamp(progress * n - j)
        if p <= 0:
            break
        mapped = [(cx + px * s, cy + py * s) for px, py in pts]
        _line(layer, mapped, colors[cname], max(2, int(width * wscale)), seed + j * 131, pal['rough'], p)


def _caption(layer, xy, text, pal, size=13, alpha=235):
    from PIL import ImageDraw
    d = ImageDraw.Draw(layer, 'RGBA')
    f = _font(size, True)
    label = re.sub(r'\s+', ' ', str(text).upper()).strip()
    bb = d.textbbox((0, 0), label, font=f)
    d.text((xy[0] - (bb[2] - bb[0]) / 2, xy[1]), label, font=f,
           fill=(pal['inkc'][0], pal['inkc'][1], pal['inkc'][2], alpha))


def _headline(layer, plan, scene, pal):
    """Underlined bold headline, top-left of the view — the reel's masthead."""
    from PIL import ImageDraw
    primary = str((scene.get('screenCopy') or {}).get('primary') or '').strip()
    if not primary:
        return
    d = ImageDraw.Draw(layer, 'RGBA')
    w, h = layer.size
    f = _font(int(w * 0.030), True)
    text = primary.upper()
    bb = d.textbbox((0, 0), text, font=f)
    tw = bb[2] - bb[0]
    x, y = int(w * 0.10), int(h * 0.075)
    ink = pal['inkc']
    d.text((x, y), text, font=f, fill=ink)
    # hand-drawn underline
    uy = y + (bb[3] - bb[1]) + int(h * 0.008)
    _line(layer, [(x, uy), (x + tw, uy)], ink, max(2, int(w * 0.0022)), 4242, 0.35)


def _scene_groups(scene, plan, ratio):
    """Ordered drawable groups: icon, connector, icon, ..., caption."""
    zone = scene['whiteboardRuntime']['boardZone']
    hero = str(scene.get('heroRole') or '').strip()
    supports = [str(v).strip() for v in (scene.get('supportingRoles') or []) if str(v).strip()]
    labels = ([hero] if hero else []) + supports
    centers = _slot_centers(len(labels), zone, ratio)

    icon_size = min(zone['w'], zone['h']) * (0.20 if len(labels) <= 4 else 0.16)

    groups = []  # each: ('icon'|'dash'|'caption', payload)
    for i, (label, c) in enumerate(zip(labels, centers)):
        if i > 0:
            groups.append(('dash', (centers[i - 1], c)))
        groups.append(('icon', (icon_for(label), c, label)))
    secondary = str((scene.get('screenCopy') or {}).get('secondary') or '').strip()
    if secondary:
        mid = centers[len(centers) // 2]
        groups.append(('caption', (secondary, (mid[0], mid[1] + icon_size * 0.95))))
    return groups, icon_size


def draw_scene_layer(layer, scene, plan, ratio, cam, scene_time, opacity=255):
    """Draw one scene into `layer` (RGBA, view size) at board camera `cam`."""
    wb = scene.get('whiteboardRuntime') or {}
    pal = wbp._pal(plan)
    size = layer.size
    zoom = 1.0 if ratio != '9:16' else 0.86
    scale = min(size) / (650 if ratio != '9:16' else 760) * zoom

    def mp(pt):
        return size[0] / 2 + (pt[0] - cam[0]) * scale, size[1] / 2 + (pt[1] - cam[1]) * scale

    groups, icon_size = _scene_groups(scene, plan, ratio)
    drawplan = wb.get('drawPlan') or []
    seed = int(wb.get('seed', 1))
    acc = (pal['accentc'][0], pal['accentc'][1], pal['accentc'][2], int(opacity * 0.95))
    ink = pal['inkc']

    for i, (kind, payload) in enumerate(groups):
        item = drawplan[i] if i < len(drawplan) else None
        if item:
            p = wbp._ease(_clamp(
                (scene_time - float(item.get('start', i * 0.3)))
                / max(0.001, float(item.get('end', i * 0.3 + 0.6)) - float(item.get('start', i * 0.3)))))
        else:
            p = _clamp((scene_time - i * 0.3) / 0.6)
        if p <= 0:
            continue
        if kind == 'icon':
            icon, c, label = payload
            sc = mp(c)
            _draw_icon(layer, icon, sc[0], sc[1], icon_size * scale, p, seed + i * 977, pal, opacity)
            if p > 0.55:
                q = _clamp((p - 0.55) / 0.45)
                _caption(layer, (sc[0], sc[1] + icon_size * scale * 0.62), label, pal,
                         size=13, alpha=int(opacity * q))
        elif kind == 'dash':
            a, b = payload
            for j, seg in enumerate(_dashes(a, b)):
                _line(layer, [mp(seg[0]), mp(seg[1])], acc, max(2, pal['stroke'] - 1),
                      seed + i * 53 + j, 0.15, _clamp(p * 3 - j * 0.4))
        elif kind == 'caption':
            text, c = payload
            sc = mp(c)
            if p > 0.2:
                _caption(layer, sc, text, pal, size=12, alpha=int(opacity * 0.8 * p))


def render_scene_frame(scene, plan, ratio='16:9', scene_time=None):
    """Public frame renderer matching the reel's composition."""
    from PIL import Image
    size = wbp.RATIO_SIZES[ratio]
    pal = wbp._pal(plan)
    im = Image.new('RGBA', size, pal['bgc'])
    wbp._paper_texture(im, pal, int((scene.get('whiteboardRuntime') or {}).get('seed', 7)))
    scenes = plan.get('sceneSpecs') or [scene]
    idx = next((i for i, s in enumerate(scenes) if s.get('sceneId') == scene.get('sceneId')), 0)
    wb = scene.get('whiteboardRuntime') or {}
    dur = float(wb.get('sceneDuration') or 1.0)
    st = _clamp(scene_time if scene_time is not None else 0.9 * dur, 0, max(dur * 2, dur))
    cam = wbp._camera(scene, ratio)
    # Nearby completed zones persist on the same board as faint memory.
    for j in range(max(0, idx - 2), idx):
        memory = Image.new('RGBA', size, (0, 0, 0, 0))
        draw_scene_layer(memory, scenes[j], plan, ratio, cam, 999.0,
                         opacity=42 if j < idx - 1 else 70)
        im.alpha_composite(memory)
    active = Image.new('RGBA', size, (0, 0, 0, 0))
    draw_scene_layer(active, scene, plan, ratio, cam, st, 255)
    im.alpha_composite(active)
    _headline(im, plan, scene, pal)
    return im.convert('RGB')


def render_transition_frame(prev_scene, scene, plan, ratio, progress):
    """Camera travel between board zones; outgoing marks persist, incoming builds."""
    from PIL import Image
    p = wbp._ease(progress)
    a = wbp._camera(prev_scene, ratio)
    b = wbp._camera(scene, ratio)
    cam = (a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p)
    size = wbp.RATIO_SIZES[ratio]
    pal = wbp._pal(plan)
    im = Image.new('RGBA', size, pal['bgc'])
    wbp._paper_texture(im, pal, int((scene.get('whiteboardRuntime') or {}).get('seed', 9)))
    out_l = Image.new('RGBA', size, (0, 0, 0, 0))
    draw_scene_layer(out_l, prev_scene, plan, ratio, cam, 999.0,
                     opacity=int(255 * (1 - 0.25 * p)))
    im.alpha_composite(out_l)
    incoming = max(0.0, (p - 0.42) / 0.58) * float(
        (scene.get('whiteboardRuntime') or {}).get('sceneDuration') or 1.0) * 0.20
    in_l = Image.new('RGBA', size, (0, 0, 0, 0))
    draw_scene_layer(in_l, scene, plan, ratio, cam, incoming, int(120 + 135 * p))
    im.alpha_composite(in_l)
    if p > 0.55:
        _headline(im, plan, scene, pal)
    return im.convert('RGB')
