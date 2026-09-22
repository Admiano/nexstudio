"""Diagram type — a cumulative annotated-canvas explainer.

Grammar (reference: "How does a computer work?"): one persistent board —
hand-lettered headline + accent underline on top, a hero illustration at
center, then each beat *adds* elements (numbered stage labels, icons,
callout chips, connector arrows) that draw on stroke-by-stroke. Elements
from earlier beats stay on the board muted while the active beat draws in
full ink/accent. An optional summary strip closes the piece.

Beats carry a `diagram` spec:

    beats: [{
      "narration": "...",
      "diagram": {
        "stage": "INPUT",                  # stage label ("1." auto-numbered)
        "region": "left",                  # column the beat owns
        "elements": [
          {"icon": "keyboard", "at": "left"},
          {"chip": "CPU", "sub": "thinks", "at": "hero-tl"},
          {"arrow": {"from": "left", "to": "hero"}},
          {"callout": "screen · sound · files", "at": "right"}
        ]
      }
    }]

Plan-level `diagram`: {"title": ..., "hero": "laptop", "summary": "..."}.
Art resolves through the same asset registry as the board — assets first,
the artist slot is open: anything unresolved falls back to a lettered card.
"""

from __future__ import annotations

import math

from PIL import Image

def _boot():
    # v3_board_renderer imports the preserved execution body
    # (whiteboard_pil_adapter), which only resolves after
    # load_execution_body() has put the package dir on sys.path — so the
    # import is deferred to the first public call.
    global v3, wbp
    if 'v3' not in globals():
        import v3_board_renderer as _v3
        v3 = _v3
        wbp = _v3.wbp


# ---------------------------------------------------------------------------
# Layout — a fixed slot atlas on one board, sized to the frame's zone
# ---------------------------------------------------------------------------

def _zone(ratio: str) -> dict:
    """Content bounds in board units for this ratio's fitted view."""
    scale = v3._map_scale(ratio)
    w, h = wbp.RATIO_SIZES[ratio]
    return {'w': w / scale, 'h': h / scale}


def _atlas(ratio: str, hero_size: float) -> dict:
    """Named slots -> board-space center for element placement."""
    z = _zone(ratio)
    lx, rx = -z['w'] * 0.36, z['w'] * 0.36
    hy = z['h'] * 0.02  # hero center y
    s = hero_size
    return {
        'zone': z, 'hero_c': (0.0, hy), 'hero_s': s,
        'left': lx, 'right': rx,
        # hero-* chips are satellite callouts AROUND the hero (the reference
        # laptop screen is hand-composed; our icon art is too small to hold
        # boxes inside it) — each gets a pin arrow back into the hero.
        'hero-tl': (-s * 0.52, hy - s * 0.50),
        'hero-tr': (s * 0.52, hy - s * 0.50),
        'hero-c': (0.0, hy + s * 0.58),
        'hero-bl': (-s * 0.52, hy + s * 0.38),
        'hero-br': (s * 0.52, hy + s * 0.38),
        'bottom': (0.0, z['h'] * 0.40),
        'headline_y': -z['h'] * 0.44,
    }


def _column_slot(atlas: dict, side: str, i: int, n: int) -> tuple[float, float]:
    """Nth element slot inside the left/right column (evenly stacked)."""
    z = atlas['zone']
    x = atlas[side]
    if n <= 1:
        return x, -z['h'] * 0.02
    y0, y1 = -z['h'] * 0.17, z['h'] * 0.17
    return x, y0 + (y1 - y0) * i / (n - 1)


# ---------------------------------------------------------------------------
# Element builders -> stroke groups [(pts, color, wscale, fill?, absolute?)]
# ---------------------------------------------------------------------------

def _lettered(text: str, cx: float, top: float, h: float,
              color='ink', ws=1.35, bold=True, max_w=None):
    if max_w:
        while v3.text_width(text, h) > max_w and h > 5:
            h *= 0.92
    tw = v3.text_width(text, h)
    origin = (cx - tw / 2, top)
    strokes = v3.text_strokes(text, origin, h, color, ws)
    if bold:
        strokes += [([(px + h * 0.045, py + h * 0.02)
                      for px, py in s[0]], s[1], s[2], s[3], s[4])
                    for s in strokes]
    return strokes, origin, tw, h


def _headline(text: str, atlas: dict) -> list:
    z = atlas['zone']
    h = min(z['h'] * 0.055, 34.0)
    strokes, origin, tw, h = _lettered(text.upper()[:46], 0,
                                       atlas['headline_y'], h, 'ink',
                                       max_w=z['w'] * 0.9)
    y_u = origin[1] + v3._text_bottom('Ag', h) + h * 0.55
    upts = [(origin[0] + tw * t / 24,
             y_u + math.sin(t * 0.7) * h * 0.14) for t in range(25)]
    strokes.append((upts, 'ink', 1.4, False, True))
    strokes.append(([(a, b + h * 0.14) for a, b in upts],
                    'accent', 0.85, False, True))
    return strokes


def _chip(label: str, sub: str | None, cx: float, cy: float,
          accent=False, pin_to: tuple | None = None) -> list:
    """Rounded box sized to its label + optional sub-line + a pin arrow
    when it annotates the hero from outside its bounds."""
    h_l, h_s = 15.0, 10.0
    tw = v3.text_width(str(label).upper(), h_l)
    sw = v3.text_width(str(sub), h_s) if sub else 0.0
    w_b = max(120.0, max(tw, sw) + 44)
    h_b = 60.0 if sub else 44.0
    strokes = []
    if pin_to is not None:
        # short pointer from the box edge toward the hero's edge
        dx, dy = pin_to[0] - cx, pin_to[1] - cy
        d = math.hypot(dx, dy) or 1.0
        x0 = cx + dx / d * w_b * 0.42
        y0 = cy + dy / d * h_b * 0.55
        strokes += _arrow(x0, y0, cx + dx / d * (d * 0.55),
                          cy + dy / d * (d * 0.55), 'accent')
    strokes.append((v3._rounded_rect(cx, cy, w_b, h_b, min(w_b * 0.12, 18)),
                    'accent' if accent else 'ink', 1.0, False, True))
    st, _o, _t, _h = _lettered(str(label).upper(), cx,
                               cy - h_b * 0.40, h_l, 'ink', max_w=w_b - 20)
    strokes += st
    if sub:
        st, _o, _t, _h = _lettered(str(sub), cx, cy + h_b * 0.08,
                                   h_s, 'secondary', ws=1.0, bold=False,
                                   max_w=w_b - 16)
        strokes += st
    return strokes


def _arrow(x0, y0, x1, y1, color='accent') -> list:
    ang = math.atan2(y1 - y0, x1 - x0)
    strokes = [[[(x0, y0), (x1, y1)], color, 1.0, False, True]]
    for da in (2.6, -2.6):
        strokes.append([[(x1, y1),
                         (x1 + math.cos(ang + da) * 14,
                          y1 + math.sin(ang + da) * 14)],
                        color, 1.0, False, True])
    return [tuple(s) for s in strokes]


def _icon_group(concept: str, used: dict) -> list:
    ic = v3.icon_for(concept, used)
    st = v3._strokes_for(ic)
    if ic == 'card':
        # lettered fallback card is built by the caller with the label
        return []
    return st or []


# ---------------------------------------------------------------------------
# Schedule — flatten the plan into draw-ordered elements with beat windows
# ---------------------------------------------------------------------------

def _ink_len(strokes, size) -> float:
    total = 0.0
    for st in strokes:
        pts = st[0]
        scale = 1.0 if (len(st) > 4 and st[4]) else size
        for a, b in zip(pts, pts[1:]):
            total += math.hypot(b[0] - a[0], b[1] - a[1]) * scale
    return max(1.0, total)


def build_elements(plan: dict, ratio: str) -> tuple[list[dict], dict]:
    """All drawable elements in draw order + per-beat drawPlan specs.

    Element: {'kind', 'strokes', 'center', 'size', 'beat', 'start', 'end'}
    — start/end are seconds relative to the owning beat's start.
    """
    _boot()
    dg = plan.get('diagram') or {}
    z = _zone(ratio)
    hero_size = min(z['w'] * 0.34, z['h'] * 0.44)
    atlas = _atlas(ratio, hero_size)
    used: dict = {}
    beats = plan.get('beats') or []

    elements: list[dict] = []
    plans: list[list[dict]] = [[] for _ in beats]

    def add(bi: int, kind: str, strokes, center=(0.0, 0.0), size=1.0,
            role='marker.swipe'):
        elements.append({'kind': kind, 'strokes': strokes, 'center': center,
                         'size': size, 'beat': bi})
        plans[bi].append({'role': role})

    # headline + hero draw during beat 0
    title = str(dg.get('title') or '').strip()
    if title:
        add(0, 'headline', _headline(title, atlas), size=1.0,
            role='marker.swipe')
    hero = str(dg.get('hero') or '').strip()
    if hero:
        add(0, 'hero', _icon_group(hero, used), center=atlas['hero_c'],
            size=atlas['hero_s'], role='marker.swipe')

    # per-beat elements
    col_counts = {'left': 0, 'right': 0}
    col_total = {'left': 0, 'right': 0}
    for b in beats:
        spec = b.get('diagram') or {}
        for el in spec.get('elements') or []:
            at = el.get('at', spec.get('region', 'hero-c'))
            if at in col_total:
                col_total[at] += 1
    for bi, b in enumerate(beats):
        spec = b.get('diagram') or {}
        region = spec.get('region') or (
            'left' if bi == 0 else
            ('right' if bi == len(beats) - 1 else 'hero'))
        stage = str(spec.get('stage') or '').strip()
        if stage:
            lbl = f'{bi + 1}. {stage.upper()}'[:32]
            if region in ('left', 'right'):
                sx = atlas[region]
                sy = -z['h'] * 0.30
            else:
                # hero beats: label floats above the satellite chips
                sx, sy = 0.0, atlas['hero_c'][1] - atlas['hero_s'] * 0.74
            st, _o, _t, _h = _lettered(lbl, sx, sy, 18, 'ink',
                                       max_w=z['w'] * 0.4)
            add(bi, 'stage', st, size=1.0, role='marker.short')
        for el in spec.get('elements') or []:
            at = str(el.get('at', region))
            if 'icon' in el:
                cx, cy = _column_slot(atlas, at, col_counts.get(at, 0),
                                      col_total.get(at, 1)) \
                    if at in ('left', 'right') else atlas.get(
                        at, atlas['hero_c'])
                if at in ('left', 'right'):
                    col_counts[at] = col_counts.get(at, 0) + 1
                st = _icon_group(str(el['icon']), used)
                if st:
                    add(bi, 'icon', st, center=(cx, cy), size=140.0,
                        role='marker.swipe')
                else:
                    add(bi, 'icon', _chip(el['icon'], None, cx, cy),
                        center=(0, 0), size=1.0, role='marker.swipe')
                if el.get('sub'):
                    st2, _o, _t, _h = _lettered(
                        str(el['sub']), cx, cy + 62, 13, 'secondary',
                        ws=1.0, bold=False, max_w=200)
                    add(bi, 'caption', st2, center=(0, 0), size=1.0,
                        role='marker.short')
            elif 'chip' in el:
                cx, cy = atlas.get(at, atlas['hero-c'])
                pin = atlas['hero_c'] if at.startswith('hero') else None
                add(bi, 'chip',
                    _chip(el['chip'], el.get('sub'), cx, cy, pin_to=pin),
                    center=(0, 0), size=1.0, role='marker.short')
            elif 'callout' in el:
                cx, cy = _column_slot(atlas, at, col_counts.get(at, 0),
                                      col_total.get(at, 1)) \
                    if at in ('left', 'right') else atlas.get(
                        at, atlas['hero_c'])
                if at in ('left', 'right'):
                    col_counts[at] = col_counts.get(at, 0) + 1
                add(bi, 'callout',
                    _chip(el['callout'], el.get('sub'), cx, cy, accent=True),
                    center=(0, 0), size=1.0, role='marker.swipe')
            elif 'arrow' in el:
                a = el['arrow'] if isinstance(el['arrow'], dict) else {}
                p0 = _slot_point(atlas, a.get('from', 'left'))
                p1 = _slot_point(atlas, a.get('to', 'hero'))
                add(bi, 'arrow', _arrow(p0[0], p0[1], p1[0], p1[1],
                                        a.get('color', 'accent')),
                    center=(0, 0), size=1.0, role='marker.short')

    # summary strip draws inside the last beat's window
    summary = str(dg.get('summary') or '').strip()
    if summary and beats:
        bx, by = atlas['bottom']
        txt = summary.upper()[:60]
        tw = v3.text_width(txt, 17)
        w_b = min(z['w'] * 0.92, tw + 60)
        strokes = [(v3._rounded_rect(bx, by, w_b, 56, 16),
                    'ink', 1.0, False, True)]
        st, _o, _t, _h = _lettered(txt, bx, by - 17, 17, 'ink',
                                   max_w=w_b - 24)
        strokes += st
        add(len(beats) - 1, 'summary', strokes, center=(0, 0), size=1.0,
            role='marker.swipe')

    # assign beat-relative windows weighted by ink length
    for bi, b in enumerate(beats):
        els = [e for e in elements if e['beat'] == bi]
        if not els:
            continue
        dur = float(b.get('duration_seconds') or 4.0)
        gap = 0.05
        lens = [_ink_len(e['strokes'], e['size']) for e in els]
        total = sum(lens)
        cur = 0.0
        for e, ln in zip(els, lens):
            seg = max(0.3, (dur - gap * (len(els) - 1)) * ln / total)
            e['start'], e['end'] = cur, min(dur, cur + seg)
            cur += seg + gap
        # shrink if the sum overruns the beat window
        if cur - gap > dur:
            k = dur / (cur - gap)
            for e in els:
                e['start'] *= k
                e['end'] *= k
        # drawPlan entries mirror the windows for the sound layer
        for e, spec in zip(els, plans[bi]):
            spec.update({'id': f'b{bi}-{e["kind"]}',
                         'start': e['start'], 'end': e['end']})
            n = len(e['strokes'])
            pen = []
            for jj, stt in enumerate(e['strokes']):
                a_, b_ = jj / n, (jj + 1) / n
                if len(stt) > 3 and stt[3]:
                    a_ += 0.38 / n
                pen.append([e['start'] + (e['end'] - e['start'])
                            * v3._ease_inv(a_),
                            e['start'] + (e['end'] - e['start'])
                            * v3._ease_inv(b_)])
            spec['pen'] = sorted(pen)
            spec['soundRole'] = spec.pop('role')
    return elements, {'atlas': atlas, 'plans': plans}


def _slot_point(atlas: dict, name: str) -> tuple[float, float]:
    z = atlas['zone']
    if name in ('hero', 'hero-c'):
        return atlas['hero_c']
    if name in atlas and isinstance(atlas[name], tuple):
        return atlas[name]
    if name == 'left':
        return atlas['left'] + 90, -z['h'] * 0.02
    if name == 'right':
        return atlas['right'] - 90, -z['h'] * 0.02
    return atlas.get(name, atlas['hero_c'])


# ---------------------------------------------------------------------------
# Frame render — cumulative layer; elements of past beats draw muted
# ---------------------------------------------------------------------------

_MUTED = {'ink': 'pale', 'accent': 'pale', 'accdeep': 'pale',
          'inkfill': 'pale', 'accfill': 'paper'}


def _active_beat(beats: list[dict], t: float) -> int:
    idx = 0
    for i, b in enumerate(beats):
        if float(b.get('start_seconds') or 0) <= t:
            idx = i
    return idx


def draw_diagram_layer(plan: dict, elements: list[dict], atlas: dict,
                       ratio: str, t: float, draw=True):
    """Returns (layer, pen_tip_px)."""
    _boot()
    w, h = wbp.RATIO_SIZES[ratio]
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    cam = (0.0, 0.0)
    colors = v3._palette(plan)
    colors.setdefault('secondary', (139, 133, 119, 255))
    muted = dict(colors)
    for k, m in _MUTED.items():
        muted[k] = colors[m]
    beats = plan.get('beats') or []
    active = _active_beat(beats, t)
    tip = None
    for ei, e in enumerate(elements):
        b = beats[e['beat']] if e['beat'] < len(beats) else {}
        bt = t - float(b.get('start_seconds') or 0)
        span = max(0.05, e['end'] - e['start'])
        p = wbp._ease(wbp._clamp((bt - e['start']) / span))
        if p <= 0:
            continue
        # headline, hero and the summary strip are persistent — never muted
        persistent = e['kind'] in ('headline', 'hero', 'summary')
        cols = colors if (persistent or e['beat'] >= active) else muted
        tip_i = _draw_group(layer, e['strokes'], e['center'], e['size'],
                            cam, cols, ratio, p, 31 + ei * 97, draw)
        if p < 1 and tip_i is not None:
            tip = tip_i
    return layer, tip


def _draw_group(layer, strokes, center, size, cam, colors, ratio, progress,
                seed, draw=True):
    n = len(strokes)
    if n == 0:
        return None
    scale = v3._map_scale(ratio)
    lw = max(2.0, size * scale * 0.028)
    tip = None
    for j, st in enumerate(strokes):
        pts, col, wscale = st[0], st[1], st[2]
        fill = st[3] if len(st) > 3 else False
        absolute = st[4] if len(st) > 4 else False
        p = wbp._clamp(progress * n - j)
        if p <= 0:
            break
        pts_b = pts if absolute else [(center[0] + px * size,
                                       center[1] + py * size)
                                      for px, py in pts]
        pts_s = [wbp._map_point(q, cam, ratio) for q in pts_b]
        if not draw:
            if 0 < p < 1:
                tip = v3._stroke_tip(pts_s, p)
            continue
        if fill:
            hp = wbp._clamp((p - 0.38) / 0.62)
            if hp <= 0:
                continue
            segs = v3._hatch_for(pts, size)
            hcol = colors[v3._HATCH_COLOR.get(col, col)]
            hcol = (hcol[0], hcol[1], hcol[2], min(215, hcol[3]))
            hw = max(1.4, lw * 0.42)
            m = len(segs)
            for k, seg in enumerate(segs):
                sp = wbp._clamp(hp * m - k)
                if sp <= 0:
                    break
                seg_b = [(center[0] + px * size, center[1] + py * size)
                         for px, py in seg]
                seg_s = [wbp._map_point(q, cam, ratio) for q in seg_b]
                t2 = v3._taper_line(layer, seg_s, hcol, hw,
                                    seed + j * 131 + k * 7, .18, sp)
                if 0 < sp < 1:
                    tip = t2
            continue
        t2 = v3._taper_line(layer, pts_s, colors[col], lw * wscale,
                            seed + j * 13, .26, p)
        if 0 < p < 1:
            tip = t2
    return tip


def render_diagram_frame(plan: dict, elements: list[dict], atlas: dict,
                         ratio: str, t: float) -> Image.Image:
    layer, tip = draw_diagram_layer(plan, elements, atlas, ratio, t)
    if tip is None and t > 0.05:
        # lagging sample — hand trails the stroke, never teleports
        _, tip = draw_diagram_layer(plan, elements, atlas, ratio, t - 0.14,
                                    draw=False)
    frame = v3._composite_frame(plan, ratio, (0.0, 0.0), [(layer, 255)], 7)
    return v3._overlay_hand(frame, tip, ratio, t * 8 + 7)
