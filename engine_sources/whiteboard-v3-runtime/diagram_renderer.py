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
        'hero-c': (0.0, hy + s * 0.55),
        'hero-bl': (-s * 0.52, hy + s * 0.38),
        'hero-br': (s * 0.52, hy + s * 0.38),
        'bottom': (0.0, z['h'] * 0.44),
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


def _text_block(lines, cx: float, cy: float, gap: float = 8.0,
                max_w=None) -> list:
    """Stacked text lines centered exactly on (cx, cy) on BOTH axes —
    the union ink bounds of all lines are recentered, so container text
    can never sit off-middle regardless of line count or glyph skew."""
    groups = []
    y = 0.0
    for txt, h, color, ws, bold in lines:
        st, _o, _t, _h = _lettered(txt, 0.0, y, h, color, ws=ws,
                                   bold=bold, max_w=max_w)
        groups.append(st)
        y += _h + gap
    xs = [p[0] for g in groups for s in g for p in s[0]]
    ys = [p[1] for g in groups for s in g for p in s[0]]
    dx = cx - (min(xs) + max(xs)) / 2
    dy = cy - (min(ys) + max(ys)) / 2
    return [([(px + dx, py + dy) for px, py in s[0]], *s[1:])
            for g in groups for s in g]


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
    when it annotates the hero from outside its bounds.
    Sub-lines stay in ink (not 'secondary'): pale thin strokes at small
    sizes read as out-of-focus rather than deliberately muted."""
    h_l, h_s = 18.5, 13.0
    tw = v3.text_width(str(label).upper(), h_l)
    sw = v3.text_width(str(sub), h_s) if sub else 0.0
    w_b = max(140.0, max(tw, sw) + 56)
    h_b = 78.0 if sub else 52.0
    strokes = []
    if pin_to is not None:
        # short pointer from the box edge toward the hero's edge
        dx, dy = pin_to[0] - cx, pin_to[1] - cy
        d = math.hypot(dx, dy) or 1.0
        x0 = cx + dx / d * w_b * 0.5
        y0 = cy + dy / d * h_b * 0.5
        # 'pin'-tagged strokes reach INTO the hero by design — excluded
        # from the chip's collision bounds or the resolver would push the
        # box away from its own pointer forever
        strokes += [s + ('pin',) for s in _arrow(
            x0, y0, cx + dx / d * (d * 0.55), cy + dy / d * (d * 0.55),
            'accent')]
    strokes.append((v3._rounded_rect(cx, cy, w_b, h_b, min(w_b * 0.12, 18)),
                    'accent' if accent else 'ink', 1.0, False, True))
    lines = [(str(label).upper(), h_l, 'ink', 1.35, True)]
    if sub:
        lines.append((str(sub), h_s, 'ink', 0.95, False))
    strokes += _text_block(lines, cx, cy, gap=9.0, max_w=w_b - 24)
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


def _edge_pt(b, toward) -> tuple:
    """Point where a rect's border exits toward `toward` — parametric
    exit of the center→target ray on the bounds rect."""
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    t = min(
        ((b[2] - cx) / dx if dx > 0 else (cx - b[0]) / -dx if dx < 0
         else float('inf')),
        ((b[3] - cy) / dy if dy > 0 else (cy - b[1]) / -dy if dy < 0
         else float('inf')))
    return cx + dx * t, cy + dy * t


def _conn_pt(atlas, ref, id_map, elements, other_ref, margin=0.0) -> tuple:
    """Arrow endpoint: element id → its bounds edge toward the other end;
    slot/region name → its atlas point. `margin` pulls the endpoint back
    along the ray so arrowheads sit off the target's ink."""
    idx = id_map.get(str(ref)) if ref is not None else None
    if idx is None:
        return _slot_point(atlas, ref or 'hero')
    e = elements[idx]
    b = _elem_bounds(e)
    if b is None:
        return _slot_point(atlas, e.get('slot') or 'hero')
    toward = _conn_pt(atlas, other_ref, id_map, elements, None) \
        if other_ref is not None else atlas['hero_c']
    px, py = _edge_pt(b, toward)
    if margin:
        dx, dy = px - (b[0] + b[2]) / 2, py - (b[1] + b[3]) / 2
        d = math.hypot(dx, dy) or 1.0
        px -= dx / d * margin
        py -= dy / d * margin
    return px, py


def _icon_group(concept: str, used: dict, cast=None, facing: int = 1,
                force=None) -> list:
    ic = force or v3.icon_for(concept, used)
    if ic == 'card':
        # lettered fallback card is built by the caller with the label
        return []
    if ic == 'person':
        spec = cast if isinstance(cast, dict) \
            else v3._cast_spec_for(concept, 'point')
        return v3._strokes_for(ic, cast=spec, facing=facing) or []
    st = v3._strokes_for(ic)
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

    # headline + hero draw during beat 0 — except in 'flow' layout,
    # which has no hero: beats are stage cells chained left to right
    flow = str(dg.get('layout') or '') == 'flow'
    title = str(dg.get('title') or '').strip()
    if title:
        add(0, 'headline', _headline(title, atlas), size=1.0,
            role='marker.swipe')
    hero = str(dg.get('hero') or '').strip()
    hero_strokes: list = []
    if hero and not flow:
        hero_strokes = _icon_group(hero, used)
        add(0, 'hero', hero_strokes, center=atlas['hero_c'],
            size=atlas['hero_s'], role='marker.swipe')

    cells: list[tuple[float, float, float, float]] = []
    if flow and beats:
        span = z['w'] * 0.86
        cw = span / len(beats)
        cells = [(-span / 2 + cw * (i + 0.5), z['h'] * 0.06,
                  cw - 34, z['h'] * 0.50) for i in range(len(beats))]

    # per-beat elements
    id_map: dict = {}  # element id -> elements[] index for arrow endpoints
    if hero_strokes:
        id_map['hero'] = next(i for i, e in enumerate(elements)
                              if e['kind'] == 'hero')
    col_counts = {'left': 0, 'right': 0}
    col_total = {'left': 0, 'right': 0}
    for b in beats:
        spec = b.get('diagram') or {}
        for el in spec.get('elements') or []:
            at = el.get('at', spec.get('region', 'hero-c'))
            if at in col_total:
                col_total[at] += 1
    cell_total_cells: dict = {}
    for bi, b in enumerate(beats):
        spec = b.get('diagram') or {}
        cell_total_cells[bi] = sum(
            1 for el in (spec.get('elements') or [])
            if str(el.get('at', spec.get('region', 'cell'))) == 'cell')
    for bi, b in enumerate(beats):
        spec = b.get('diagram') or {}
        region = spec.get('region') or (
            'cell' if flow else
            'left' if bi == 0 else
            ('right' if bi == len(beats) - 1 else 'hero'))
        if flow and region == 'cell':
            # stage cell: frame box + connector arrow from the previous
            # cell's right edge — process content reads as a chain
            cx0, cy0, wc, hc = cells[bi]
            add(bi, 'cellbox', [(v3._rounded_rect(cx0, cy0, wc, hc, 16),
                                 'ink', 1.0, False, True)],
                center=(0, 0), size=1.0, role='marker.swipe')
            elements[-1]['slot'] = f'cellbox{bi}'
            if bi > 0:
                px0 = cells[bi - 1][0] + cells[bi - 1][2] / 2 + 6
                px1 = cx0 - wc / 2 - 6
                add(bi, 'arrow',
                    _arrow(px0, cy0, px1, cy0, 'accent'),
                    center=(0, 0), size=1.0, role='marker.short')
        stage = str(spec.get('stage') or '').strip()
        if stage:
            lbl = f'{bi + 1}. {stage.upper()}'[:32]
            if region == 'cell':
                sx = cells[bi][0]
                sy = cells[bi][1] - cells[bi][3] / 2 - 34
            elif region in ('left', 'right'):
                sx = atlas[region]
                sy = -z['h'] * 0.30
            else:
                # hero beats: label floats above the satellite chips
                sx, sy = 0.0, atlas['hero_c'][1] - atlas['hero_s'] * 0.74
            st, _o, _t, _h = _lettered(lbl, sx, sy, 20, 'ink',
                                       max_w=z['w'] * 0.4)
            add(bi, 'stage', st, size=1.0, role='marker.short')
            elements[-1]['slot'] = (f'cell{bi}' if region == 'cell'
                                    else region if region in ('left', 'right')
                                    else 'hero')
        for el in spec.get('elements') or []:
            at = str(el.get('at', region))
            el_id = el.get('id')
            in_cell = flow and at == 'cell'
            if in_cell:
                # stack inside this beat's stage cell — icon size shrinks
                # with item count so icon+caption stacks stay inside the box
                cx0, cy0, wc, hc = cells[bi]
                idx = col_counts.get(f'cell{bi}', 0)
                col_counts[f'cell{bi}'] = idx + 1
                n = cell_total_cells.get(bi, 1)
                cx = cx0
                span = hc * 0.56
                cy = (cy0 - span / 2 if n == 1 else
                      cy0 - span / 2 + span * idx / (n - 1))
                icon_size = min(140.0, wc * 0.46,
                                hc * 0.28 if n <= 2 else hc * 0.185)
            elif at in ('left', 'right'):
                cx, cy = _column_slot(atlas, at, col_counts.get(at, 0),
                                      col_total.get(at, 1))
                col_counts[at] = col_counts.get(at, 0) + 1
                icon_size = 140.0
            else:
                cx, cy = atlas.get(at, atlas['hero-c'])
                icon_size = 140.0
            pin = (atlas['hero_c'] if at.startswith('hero') else None)
            concept = el.get('icon') or el.get('part')
            person_spec = el.get('person')
            if person_spec is not None:
                # explicit character element: {"person": "<role>"} or a
                # cast spec dict — a string seeds a deterministic variant
                concept = (str(person_spec) if isinstance(person_spec, str)
                           else str(el.get('label') or 'person'))
                cast = (person_spec if isinstance(person_spec, dict)
                        else v3._cast_spec_for(concept, 'point'))
            else:
                cast = None
            if concept:
                # face characters toward the stage centre so left/right
                # satellites look into the composition, not off-canvas
                facing = -1 if cx > atlas['hero_c'][0] else 1
                st = _icon_group(str(concept), used, cast=cast,
                                 facing=facing,
                                 force='person' if person_spec is not None
                                 else None)
                if st and (person_spec is not None
                           or v3.icon_for(str(concept), used) == 'person'):
                    # figures are taller than props — keep them readable
                    icon_size *= 1.3
                label = str(el.get('label') or concept)
                if st:
                    # satellite/cell icons draw a touch heavier than the
                    # library default so small art doesn't read spindly
                    strokes = [
                        (s[0], s[1], min(1.0, (s[2] or 1.0) * 1.45),
                         *s[3:]) if len(s) >= 3 else s
                        for s in st]
                    if pin is not None:
                        hero_b = _elem_bounds(
                            {'strokes': hero_strokes, 'center': atlas['hero_c'],
                             'size': atlas['hero_s']}) or (0, 0, 0, 0)
                        ib = _elem_bounds(
                            {'strokes': strokes, 'center': (cx, cy),
                             'size': icon_size}) or (
                                cx - 70, cy - 70, cx + 70, cy + 70)
                        px0, py0 = _edge_pt(ib, atlas['hero_c'])
                        px1, py1 = _edge_pt(hero_b, (cx, cy))
                        strokes += [s + ('pin',) for s in _arrow(
                            px0, py0, px1, py1, 'accent')]
                    add(bi, 'icon', strokes, center=(cx, cy),
                        size=icon_size, role='marker.swipe')
                    if el.get('label') or el.get('sub'):
                        small = in_cell and cell_total_cells.get(bi, 1) > 2
                        lines = [(str(el.get('label') or concept).upper(),
                                  12 if small else 13.5, 'ink',
                                  1.25, True)]
                        if el.get('sub'):
                            lines.append((str(el['sub']),
                                          10 if small else 11, 'ink',
                                          0.9, False))
                        # caption hugs the element's real ink bottom —
                        # figures aren't vertically centered like icons
                        b = _elem_bounds(
                            {'strokes': strokes, 'center': (cx, cy),
                             'size': icon_size})
                        cap_y = (b[3] + 16) if b else \
                            cy + icon_size * 0.5 + 16
                        strokes = _text_block(
                            lines, cx, cap_y,
                            gap=6, max_w=(wc - 40) if in_cell else 210)
                        elements[-1]['strokes'] += strokes
                else:
                    add(bi, 'chip',
                        _chip(label, el.get('sub'), cx, cy, pin_to=pin),
                        center=(0, 0), size=1.0, role='marker.short')
                elements[-1]['slot'] = f'cell{bi}' if in_cell else at
            elif 'chip' in el:
                add(bi, 'chip',
                    _chip(el['chip'], el.get('sub'), cx, cy, pin_to=pin),
                    center=(0, 0), size=1.0, role='marker.short')
                elements[-1]['slot'] = f'cell{bi}' if in_cell else at
            elif 'callout' in el:
                add(bi, 'callout',
                    _chip(el['callout'], el.get('sub'), cx, cy, accent=True),
                    center=(0, 0), size=1.0, role='marker.swipe')
                elements[-1]['slot'] = f'cell{bi}' if in_cell else at
            elif 'arrow' in el:
                a = el['arrow'] if isinstance(el['arrow'], dict) else {}
                p0 = _conn_pt(atlas, a.get('from'), id_map, elements,
                              a.get('to'))
                p1 = _conn_pt(atlas, a.get('to'), id_map, elements,
                              a.get('from'), margin=16)
                add(bi, 'arrow', _arrow(p0[0], p0[1], p1[0], p1[1],
                                        a.get('color', 'accent')),
                    center=(0, 0), size=1.0, role='marker.short')
            if el_id:
                id_map[el_id] = len(elements) - 1

    atlas['cells'] = cells
    # summary strip draws inside the last beat's window
    summary = str(dg.get('summary') or '').strip()
    if summary and beats:
        bx, by = atlas['bottom']
        txt = summary.upper()[:60]
        tw = v3.text_width(txt, 17)
        w_b = min(z['w'] * 0.92, tw + 72)
        strokes = [(v3._rounded_rect(bx, by, w_b, 60, 16),
                    'ink', 1.0, False, True)]
        strokes += _text_block([(txt, 18, 'ink', 1.35, True)],
                               bx, by, max_w=w_b - 24)
        add(len(beats) - 1, 'summary', strokes, center=(0, 0), size=1.0,
            role='marker.swipe')

    _resolve_collisions(elements, atlas)

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


def _elem_bounds(e):
    xs, ys = [], []
    for st in e['strokes']:
        if len(st) > 5 and st[5] == 'pin':
            continue
        absolute = len(st) > 4 and st[4]
        for px, py in st[0]:
            xs.append(px if absolute else e['center'][0] + px * e['size'])
            ys.append(py if absolute else e['center'][1] + py * e['size'])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _shift_elem(e, dx, dy):
    """Move an element: absolute-stroke pts translate directly; relative
    (icon/hero) strokes move via their center."""
    moved_rel = False
    new = []
    for st in e['strokes']:
        absolute = len(st) > 4 and st[4]
        if absolute:
            new.append(([(px + dx, py + dy) for px, py in st[0]],) + st[1:])
        else:
            new.append(st)
            moved_rel = True
    e['strokes'] = new
    if moved_rel:
        e['center'] = (e['center'][0] + dx, e['center'][1] + dy)


def _overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def _bounds_in_band(e, y0: float, y1: float):
    """Ink bounds of element restricted to strokes inside [y0, y1] — a
    tall hero's full bbox overstates what a top satellite must avoid
    (up there only its antenna has ink, not its whole width)."""
    xs, ys = [], []
    for st in e['strokes']:
        if len(st) > 5 and st[5] == 'pin':
            continue
        absolute = len(st) > 4 and st[4]
        for px, py in st[0]:
            yy = py if absolute else e['center'][1] + py * e['size']
            if y0 <= yy <= y1:
                xs.append(px if absolute else e['center'][0] + px * e['size'])
                ys.append(yy)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _resolve_collisions(elements: list[dict], atlas: dict) -> None:
    """Measured-bounds layout repair. Nominal slots can place ink on top
    of other ink (icons touching, chips on the hero's edge, stage labels
    on callout boxes) — resolve with real bounds: re-stack each column
    with a minimum gap, push hero-satellite chips radially off the hero,
    and float stage labels just above their region's topmost ink."""
    z = atlas['zone']
    margin = 24.0
    hero_e = next((e for e in elements if e['kind'] == 'hero'), None)
    head_b = next((_elem_bounds(e) for e in elements
                   if e['kind'] == 'headline'), None)
    summ_b = next((_elem_bounds(e) for e in elements
                   if e['kind'] == 'summary'), None)

    def _inflate(b):
        return (b[0] - margin * 0.5, b[1] - margin * 0.5,
                b[2] + margin * 0.5, b[3] + margin * 0.5)

    for e in elements:
        if (e.get('slot') or '').startswith('hero'):
            for _ in range(26):
                b = _elem_bounds(e)
                if not b:
                    break
                forbids = []
                if hero_e:
                    hb = _bounds_in_band(hero_e, b[1] - margin,
                                         b[3] + margin)
                    if hb:
                        forbids.append(_inflate(hb))
                if head_b:
                    forbids.append(_inflate(head_b))
                if summ_b:
                    forbids.append(_inflate(summ_b))
                # accent callout boxes are equally forbidden — satellite
                # captions/art must never bleed into them
                for co in elements:
                    if co['kind'] == 'callout':
                        cob = _elem_bounds(co)
                        if cob:
                            forbids.append(_inflate(cob))
                bad = [f for f in forbids if _overlaps(b, f)]
                if not bad:
                    break
                cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                dx = dy = 0.0
                for f in bad:
                    ddx = cx - (f[0] + f[2]) / 2
                    ddy = cy - (f[1] + f[3]) / 2
                    dd = math.hypot(ddx, ddy) or 1.0
                    dx += ddx / dd
                    dy += ddy / dd
                d = math.hypot(dx, dy) or 1.0
                _shift_elem(e, dx / d * 12.0, dy / d * 12.0)
    for col in ('left', 'right'):
        items = [e for e in elements if e.get('slot') == col]
        items.sort(key=lambda e: (_elem_bounds(e) or (0, 0, 0, 0))[1])
        cursor = -z['h'] * 0.20
        for e in items:
            b = _elem_bounds(e)
            if not b:
                continue
            _shift_elem(e, 0.0, cursor - b[1])
            cursor = _elem_bounds(e)[3] + margin
        for e in elements:
            if e['kind'] == 'stage' and e.get('slot') == col:
                b = _elem_bounds(e)
                top = min((_elem_bounds(x)[1] for x in items
                           if _elem_bounds(x)), default=b[1])
                _shift_elem(e, 0.0, top - margin * 0.6 - b[3])
                # never float into the headline zone — drop the column
                # stack down by the deficit instead
                head = next((f for f in forbids), None)
                hb = next((_elem_bounds(x) for x in elements
                           if x['kind'] == 'headline'), None)
                b = _elem_bounds(e)
                if hb and b and b[1] < hb[3] + margin * 0.4:
                    deficit = hb[3] + margin * 0.4 - b[1]
                    _shift_elem(e, 0.0, deficit)
                    for x in items:
                        _shift_elem(x, 0.0, deficit)
    # flow layout: restack each stage cell's contents inside its box and
    # float the stage label just above the box top
    for i, (cx0, cy0, wc, hc) in enumerate(atlas.get('cells') or []):
        items = [e for e in elements if e.get('slot') == f'cell{i}'
                 and e['kind'] != 'stage']
        items.sort(key=lambda e: (_elem_bounds(e) or (0, 0, 0, 0))[1])
        cursor = cy0 - hc / 2 + hc * 0.11
        for e in items:
            b = _elem_bounds(e)
            if not b:
                continue
            _shift_elem(e, 0.0, cursor - b[1])
            cursor = _elem_bounds(e)[3] + margin * 0.6
        for e in elements:
            if e['kind'] == 'stage' and e.get('slot') == f'cell{i}':
                b = _elem_bounds(e)
                _shift_elem(e, 0.0, cy0 - hc / 2 - margin * 0.5 - b[3])
    for e in elements:
        if e['kind'] == 'stage' and e.get('slot') == 'hero':
            b = _elem_bounds(e)
            tops = [_elem_bounds(x)[1] for x in elements
                    if (x.get('slot') or '').startswith('hero')
                    and _elem_bounds(x)]
            if tops and b:
                _shift_elem(e, 0.0, min(tops) - margin * 0.6 - b[3])
                # never into the headline zone either
                b = _elem_bounds(e)
                if head_b and b[1] < head_b[3] + margin * 0.4:
                    _shift_elem(e, 0.0, head_b[3] + margin * 0.4 - b[1])


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
# Frame render — cumulative layer; every drawn element keeps full ink
# ---------------------------------------------------------------------------


def _active_beat(beats: list[dict], t: float) -> int:
    idx = 0
    for i, b in enumerate(beats):
        if float(b.get('start_seconds') or 0) <= t:
            idx = i
    return idx


# structural ink survives an 'erase' transition — the wipe clears a beat's
# content (icons, chips, callouts, its stage label), never the furniture
_STRUCTURAL = {'headline', 'summary', 'cellbox', 'arrow'}


def draw_diagram_layer(plan: dict, elements: list[dict], atlas: dict,
                       ratio: str, t: float, draw=True, wipe=None):
    """Returns (layer, pen_tip_px).

    wipe=(beat_idx, fade): an 'erase' transition in progress — elements
    owned by beats before beat_idx whose kind isn't structural composite
    at fade alpha, like a hand clearing the canvas for the new beat."""
    _boot()
    w, h = wbp.RATIO_SIZES[ratio]
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    old_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0)) if wipe else None
    cutoff, fade = wipe if wipe else (-1, 1.0)
    cam = (0.0, 0.0)
    colors = v3._palette(plan)
    colors.setdefault('secondary', (139, 133, 119, 255))
    beats = plan.get('beats') or []
    tip = None
    for ei, e in enumerate(elements):
        b = beats[e['beat']] if e['beat'] < len(beats) else {}
        bt = t - float(b.get('start_seconds') or 0)
        span = max(0.05, e['end'] - e['start'])
        p = wbp._ease(wbp._clamp((bt - e['start']) / span))
        if p <= 0:
            continue
        target = (old_layer
                  if old_layer is not None and e['beat'] < cutoff
                  and e['kind'] not in _STRUCTURAL
                  else layer)
        tip_i = _draw_group(target, e['strokes'], e['center'], e['size'],
                            cam, colors, ratio, p, 31 + ei * 97, draw)
        if p < 1 and tip_i is not None:
            tip = tip_i
    if old_layer is not None:
        a = old_layer.getchannel('A').point(lambda v: int(v * fade))
        old_layer.putalpha(a)
        layer.alpha_composite(old_layer)
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


def _beat_at(plan: dict, t: float) -> int:
    idx = 0
    for i, b in enumerate(plan.get('beats') or []):
        if float(b.get('start_seconds') or 0) <= t:
            idx = i
    return idx


def _transition(plan: dict, beat_idx: int) -> tuple[str, float]:
    """('erase'|'zoom'|'', duration) for the beat entering at beat_idx —
    set as beat.diagram.transition / .transition_seconds."""
    dg = ((plan.get('beats') or [{}])[beat_idx].get('diagram') or {})
    tr = str(dg.get('transition') or '')
    dur = float(dg.get('transition_seconds') or 0.7)
    return tr, max(0.2, dur)


def render_diagram_frame(plan: dict, elements: list[dict], atlas: dict,
                         ratio: str, t: float) -> Image.Image:
    bi = _beat_at(plan, t)
    tr, td = _transition(plan, bi)
    bt = t - float((plan['beats'][bi]).get('start_seconds') or 0)
    tp = wbp._ease(wbp._clamp(bt / td)) if tr else 1.0

    wipe = (bi, tp) if tr == 'erase' and tp < 1 else None
    layer, tip = draw_diagram_layer(plan, elements, atlas, ratio, t,
                                    wipe=wipe)
    if tip is None and t > 0.05:
        # lagging sample — hand trails the stroke, never teleports
        _, tip = draw_diagram_layer(plan, elements, atlas, ratio, t - 0.14,
                                    draw=False, wipe=wipe)
    frame = v3._composite_frame(plan, ratio, (0.0, 0.0), [(layer, 255)], 7)

    if tr == 'zoom' and tp < 1:
        # settle-push into the incoming beat's centroid — a between-beat
        # transition, eased open over the beat's first transition_seconds
        pts = [e['center'] for e in elements
               if e['beat'] == bi and e['kind'] not in
               ('headline', 'cellbox', 'stage', 'summary')]
        if pts:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
        else:
            cx, cy = 0.0, 0.0
        sx, sy = wbp._map_point((cx, cy), (0.0, 0.0), ratio)
        fw, fh = frame.size
        mag = 1.0 + 0.10 * (1 - tp)
        cw, ch = fw / mag, fh / mag
        x0 = wbp._clamp(sx - cw / 2, 0, fw - cw)
        y0 = wbp._clamp(sy - ch / 2, 0, fh - ch)
        box = (int(x0), int(y0), int(x0 + cw), int(y0 + ch))
        frame = frame.crop(box).resize((fw, fh))
        if tip is not None:
            tip = ((tip[0] - x0) * mag, (tip[1] - y0) * mag)

    return v3._overlay_hand(frame, tip, ratio, t * 8 + 7)
