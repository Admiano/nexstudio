"""Board-sections render mode — the whiteboard-crypto form.

Evidence model (from frame analysis of the reference):
  * Fixed camera on ONE board — the viewport IS the board, always.
  * A video is a sequence of boards separated by a fast full erase.
  * Each board holds 1-4 free-form sections: a hand-lettered heading at the
    section's top, then a composition of elements (labeled people, objects,
    captions, speech bubbles) arranged in the region; dividing lines appear
    where two regions share the board.
  * Multi-accent ink: black lettering/art + accent colors on fills, marks.
  * Ending: the board wipes, "Thanks" + heart inks big, then a montage of
    mini versions of every section fills the grid.

Beats map 1:1 to sections; boards chunk sections (<=3 per board by default,
hard max 4). Sections inside a board share the beat timeline, so narration
pacing is unchanged — the wipe lives in the last WIPE_SECONDS of a board.
"""
from __future__ import annotations

import math
import re
import random

from PIL import Image, ImageDraw

import whiteboard_pil_adapter as wbp
import v3_board_renderer as v3r
from v3_board_renderer import (
    _draw_strokes, _map_scale, _palette, _group_world_bounds,
    _composite_frame, _overlay_hand, _SLICE_SPAN, _arc,
)
from v3_board_renderer import text_strokes, text_width

WIPE_SECONDS = 0.7
THANKS_SECONDS = 1.8
CELL_SECONDS = 0.42
END_HOLD = 1.4
MAX_SECTIONS_PER_BOARD = 3

# extra accent channels layered on the plan palette (reference ink colors)
_ACCENTS = {
    'a_orange': (232, 131, 58, 255),
    'a_blue': (59, 123, 212, 255),
    'a_green': (79, 157, 105, 255),
    'a_red': (208, 69, 62, 255),
    'a_yellow': (229, 184, 58, 255),
}
# stroke-color channel remap for this mode: icon detail/fill strokes take
# real accent hues instead of the neutral plan accent
_REMAP = {'accent': 'a_orange', 'accfill': 'a_blue', 'accdeep': 'a_blue'}


def _colors(plan):
    cols = dict(_palette(plan))
    acc = cols.get('accent')
    for k, v in _ACCENTS.items():
        cols[k] = v
    # plan accent (brand-authored or --accent) still wins for 'accent'
    if acc and acc[:3] not in ((51, 51, 51), (17, 17, 17)):
        cols['a_orange'] = acc
    return cols


def _remap_col(col):
    return _REMAP.get(col, col)


def _remap_strokes(strokes):
    return [tuple([s[0], _remap_col(s[1])] + list(s[2:])) for s in strokes]


def _wobble_line(p0, p1, n=30, wob=8.0, seed=3):
    rnd = random.Random(seed)
    pts = []
    for i in range(n + 1):
        q = i / n
        x = p0[0] + (p1[0] - p0[0]) * q
        y = p0[1] + (p1[1] - p0[1]) * q
        # perpendicular jitter, tapered at both ends
        f = math.sin(q * math.pi) ** 0.5
        dx = -(p1[1] - p0[1])
        dy = (p1[0] - p0[0])
        L = math.hypot(dx, dy) or 1.0
        x += rnd.uniform(-wob, wob) * f * dx / L
        y += rnd.uniform(-wob, wob) * f * dy / L
        pts.append((x, y))
    return pts


def _bubble_box(center, w, h, tail_to):
    """Rounded speech bubble (absolute strokes): box + tail to speaker."""
    x0, y0 = center[0] - w / 2, center[1] - h / 2
    x1, y1 = center[0] + w / 2, center[1] + h / 2
    r = min(h * 0.32, w * 0.14)
    seg = []
    seg += _arc(x0 + r, y0 + r, r, r, 90, 180, 8)          # TL
    seg += [(x1 - r, y0)]
    seg += _arc(x1 - r, y0 + r, r, r, 0, 90, 8)            # TR
    seg += [(x1, y1 - r)]
    seg += _arc(x1 - r, y1 - r, r, r, -90, 0, 8)           # BR
    seg += [(x0 + r, y1)]
    seg += _arc(x0 + r, y1 - r, r, r, 180, 270, 8)         # BL
    seg += [(x0, y0 + r)]
    tail = [(center[0] - w * 0.16, y1), (tail_to[0], tail_to[1]),
            (center[0] + w * 0.02, y1)]
    return [(seg, 'ink', 1.0, False, True),
            (tail, 'ink', 0.9, False, True)]


def _heart_strokes(center, size):
    pts = []
    for i in range(41):
        a = i / 40 * 2 * math.pi
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((center[0] + x * size / 34, center[1] - y * size / 34))
    return [(pts, 'a_red', 1.6, True, True)]


def _regions(n, rect):
    """Free-form regions like the reference: halves / L-shape / quadrants."""
    x0, y0, w, h = rect
    if n <= 1:
        return [rect], []
    if n == 2:
        div = [(((x0 + w / 2), y0 + h * 0.06), ((x0 + w / 2), y0 + h * 0.94))]
        return [(x0, y0, w / 2, h), (x0 + w / 2, y0, w / 2, h)], div
    if n == 3:
        div = [((x0 + w * 0.56, y0 + h * 0.06), (x0 + w * 0.56, y0 + h * 0.94)),
               ((x0, y0 + h * 0.52), (x0 + w * 0.52, y0 + h * 0.52))]
        return [(x0, y0, w * 0.54, h * 0.5),
                (x0, y0 + h * 0.54, w * 0.54, h * 0.46),
                (x0 + w * 0.58, y0, w * 0.42, h)], div
    div = [((x0 + w / 2, y0 + h * 0.05), (x0 + w / 2, y0 + h * 0.95)),
           ((x0, y0 + h * 0.52), (x0 + w, y0 + h * 0.52))]
    return [(x0, y0, w / 2, h * 0.5),
            (x0 + w / 2, y0, w / 2, h * 0.5),
            (x0, y0 + h * 0.54, w / 2, h * 0.46),
            (x0 + w / 2, y0 + h * 0.54, w / 2, h * 0.46)], div


def _section_label(beat):
    label = str(beat.get('heroRole') or '').strip()
    if not label:
        sid = str(beat.get('beat_id') or '')
        label = sid.split('_', 1)[-1].replace('_', ' ')
    return label.title()


def _is_person_item(it):
    return any(g[4] is not None and g[4].get('icon') in ('person', 'agent')
               for g, _s, _e in it['groups'])


def _bundle_scene_groups(scene, plan, ratio):
    """_scene_groups minus the zone headline, merged into element bundles
    (icon+caption, person+prop cluster) — same model the journey uses."""
    groups = v3r._scene_groups(scene, plan, ratio)
    merged = []          # list of items {groups:[(g,s,e)], label}
    person_key = None
    for g, s, e in groups:
        if g[0] in ('headline',):
            continue
        slot = g[4]
        key = (id(slot) if slot is not None else ('free', len(merged)))
        placed = None
        if slot is not None:
            placed = next((it for it in merged if it['key'] == key), None)
        if placed is None:
            # relation arrows/solo marks attach to the previous element
            if g[0] == 'arrow' and merged:
                merged[-1]['groups'].append((g, s, e))
                continue
            placed = {'key': key, 'groups': [], 'label':
                      (slot or {}).get('label', '') if slot else ''}
            merged.append(placed)
        placed['groups'].append((g, s, e))
    # merge prop cluster into person cluster (interaction composition)
    pk = None
    for i, it in enumerate(merged):
        if _is_person_item(it):
            pk = i
            break
    if pk is not None and len(merged) > 1:
        qk = next((i for i, it in enumerate(merged) if i != pk), None)
        if qk is not None:
            for g, s, e in merged[qk]['groups']:
                if g[0] == 'caption':
                    pc = next((g3 for g3 in merged[pk]['groups']
                               if g3[0][0] == 'caption'), None)
                    drop = g[2][1] * 0.6 + g[3] * 0.4
                    if pc is not None:
                        pmax = max(p_[1] for st in pc[0][1]
                                   for p_ in st[0] if len(p_) > 1)
                        cmin = min(p_[1] for st in g[1]
                                   for p_ in st[0] if len(p_) > 1)
                        drop = pmax - cmin + 10.0
                    st2 = [([(p_[0], p_[1] + drop) for p_ in st[0]
                             if len(p_) > 1],) + tuple(st[1:])
                           for st in g[1]]
                    merged[pk]['groups'].append(
                        ((g[0], st2, g[2], g[3], g[4]), s, e))
                else:
                    merged[pk]['groups'].append((g, s, e))
            merged.pop(qk)
    # long captions -> speech bubble wrapping the text
    for it in merged:
        for gi, (g, s, e) in enumerate(it['groups']):
            if g[0] == 'caption' and len(str(it['label']).split()) >= 5:
                bb = _group_world_bounds(g)
                cw_, ch_ = bb[2] - bb[0], bb[3] - bb[1]
                bc = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
                art = next((gb for gb in it['groups'] if gb[0][0] == 'icon'),
                           None)
                tail = (bc[0], bc[1] + ch_ * 2.2)
                if art is not None:
                    ab = _group_world_bounds(art[0])
                    tail = (bc[0] + (ab[0] - bc[0]) * 0.15, ab[1])
                pad = ch_ * 0.9
                bstr = _bubble_box(bc, cw_ + pad * 2, ch_ + pad * 1.6, tail)
                it['groups'][gi] = (
                    ('caption', bstr + list(g[1]), g[2], g[3], g[4]), s, e)
    return merged


def _build(plan, ratio):
    """Precompute boards/sections/items/timing; cached per plan+ratio."""
    cache = plan.setdefault('_bs_flow', {})
    if ratio in cache:
        return cache[ratio]
    beats = plan['beats']
    scenes = plan['sceneSpecs']
    vw, vh = wbp.RATIO_SIZES[ratio]
    scale = _map_scale(ratio)
    W, H = vw / scale, vh / scale
    m = 0.045 * W
    board_rect = (-W / 2 + m, -H / 2 + m * 1.4, W - 2 * m, H - 2 * m * 1.6)

    sections = []
    for bi, (beat, scene) in enumerate(zip(beats, scenes)):
        merged = _bundle_scene_groups(scene, plan, ratio)
        for it in merged:
            b = None
            for g, _s, _e in it['groups']:
                gb = _group_world_bounds(g)
                b = gb if b is None else (min(b[0], gb[0]), min(b[1], gb[1]),
                                          max(b[2], gb[2]), max(b[3], gb[3]))
            it['bounds'] = b
        sections.append({'beat': beat, 'bi': bi, 'items': merged,
                         'label': _section_label(beat)})

    # chunk into boards
    boards = []
    cur = []
    for sec in sections:
        cur.append(sec)
        if len(cur) >= MAX_SECTIONS_PER_BOARD:
            boards.append(cur)
            cur = []
    if cur:
        boards.append(cur)

    out_sections = []
    for board in boards:
        regs, divs = _regions(len(board), board_rect)
        t0 = board[0]['beat']['start_seconds']
        t1 = (board[-1]['beat']['start_seconds']
              + board[-1]['beat']['duration_seconds'])
        # dividers ink fast at the board's opening
        div_items = []
        for k, (p0, p1) in enumerate(divs):
            st = [( _wobble_line(p0, p1, seed=11 + k), 'ink', 0.55,
                    False, True)]
            g = ('divider', st, (0, 0), 1.0, None)
            div_items.append({'groups': [(g, t0 + 0.05,
                                          t0 + 0.05 + min(0.55, t1 - t0))],
                              'bounds': _group_world_bounds(g)})
        for si, sec in enumerate(board):
            rx, ry, rw, rh = regs[si]
            heading_h = rh * 0.11
            label = sec['label']
            hgt = heading_h * 0.62
            maxw = rw * 0.72
            tw = text_width(label, hgt)
            if tw > maxw:
                hgt *= maxw / tw
            hst = text_strokes(label, (rx + rw * 0.04, ry + rh * 0.04),
                               hgt, 'ink', 1.0)
            items = []
            if hst:
                g = ('plabel', [(p, c, ws, False, True)
                                for p, c, ws, *_ in hst], (0, 0), 1.0, None)
                items.append({'groups': [(g, 0.0, 1.0)], 'wgt': 0.55,
                              'kind': 'plabel'})
            cx0, cy0 = rx + rw * 0.05, ry + rh * 0.04 + heading_h
            cw, ch = rw * 0.9, rh - heading_h - rh * 0.08
            elems = sec['items']
            k = len(elems)
            if k:
                rws = 1 if k <= 3 else 2
                ncol = math.ceil(k / rws)
                for j, it in enumerate(elems):
                    r_ = j % rws
                    c_ = j // rws
                    fx = (c_ + 0.5) / ncol
                    fy = (r_ + 0.62) / (rws + 0.25)
                    sw = cw / ncol * 0.92
                    sh = ch / (rws + 0.25)
                    b = it['bounds']
                    w = max(30.0, b[2] - b[0])
                    h = max(30.0, b[3] - b[1])
                    bo2 = min(2.6, (sw * 0.97) / w, (sh * 0.97) / h)
                    bcx, bcy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                    sx, sy = cx0 + cw * fx, cy0 + ch * fy
                    moved = []
                    for g, s, e in it['groups']:
                        kind, strokes, center, size, slot = g
                        st2 = []
                        for st in strokes:
                            if len(st) > 4 and st[4]:
                                st2.append((
                                    [(sx + (px_ - bcx) * bo2,
                                      sy + (py_ - bcy) * bo2)
                                     for px_, py_ in st[0]],) + tuple(st[1:]))
                            else:
                                st2.append(st)
                        moved.append(((kind, _remap_strokes(st2),
                                       (sx + (center[0] - bcx) * bo2,
                                        sy + (center[1] - bcy) * bo2),
                                       size * bo2, slot), s, e))
                    it['groups'] = moved
                    it['w'], it['h'] = w * bo2, h * bo2
                    it['bounds2'] = (sx - it['w'] / 2, sy - it['h'] / 2,
                                     sx + it['w'] / 2, sy + it['h'] / 2)
                    items.append({'groups': moved, 'wgt': 1.0,
                                  'kind': 'elem',
                                  'bounds2': it['bounds2']})
            # weighted slices across the beat
            dur = float(sec['beat'].get('duration_seconds', 3.0))
            b0 = sec['beat']['start_seconds']
            twt = sum(it['wgt'] for it in items)
            unit = dur / max(1e-6, twt)
            acc = b0
            for it in items:
                wd = it['wgt'] * unit
                it['groups'] = [
                    (g, acc + _SLICE_SPAN.get(g[0], (0.0, 1.0))[0] * wd,
                     acc + _SLICE_SPAN.get(g[0], (0.0, 1.0))[1] * wd)
                    for g, _s, _e in it['groups']]
                acc += wd
            sec['items2'] = items
            sec['region'] = (rx, ry, rw, rh)
            out_sections.append(sec)
        board[0]['_board_divs'] = div_items
        board[0]['_board_t'] = (t0, t1)

    # montage mini-cards: every section's art scaled into a grid cell
    nsec = len(out_sections)
    ncell = min(nsec, 14)
    cols = max(1, math.ceil(math.sqrt(ncell * (vw / vh))))
    rows = max(1, math.ceil(ncell / cols))
    gx0, gy0 = -W / 2 + m * 0.6, -H / 2 + m
    gw, gh = W - 2 * m * 0.6, H * 0.72
    cell_w, cell_h = gw / cols, gh / rows
    montage = []
    for si, sec in enumerate(out_sections[:ncell]):
        col, row = si % cols, si // cols
        ccx = gx0 + cell_w * (col + 0.5)
        ccy = gy0 + cell_h * (row + 0.42)
        # union of element bounds
        u = None
        for it in sec['items2']:
            if it['kind'] != 'elem':
                continue
            b = it['bounds2']
            u = b if u is None else (min(u[0], b[0]), min(u[1], b[1]),
                                     max(u[2], b[2]), max(u[3], b[3]))
        if u is None:
            continue
        uw, uh = max(30.0, u[2] - u[0]), max(30.0, u[3] - u[1])
        k = min(cell_w * 0.86 / uw, cell_h * 0.62 / uh)
        ucx, ucy = (u[0] + u[2]) / 2, (u[1] + u[3]) / 2
        mini = []
        for it in sec['items2']:
            if it['kind'] != 'elem':
                continue
            for g, s, e in it['groups']:
                kind, strokes, center, size, slot = g
                st2 = []
                for st in strokes:
                    if len(st) > 4 and st[4]:
                        st2.append((
                            [(ccx + (px_ - ucx) * k, ccy + (py_ - ucy) * k)
                             for px_, py_ in st[0]],) + tuple(st[1:]))
                    else:
                        st2.append(st)
                mini.append(((kind, st2,
                             (ccx + (center[0] - ucx) * k,
                              ccy + (center[1] - ucy) * k),
                             size * k, slot)))
        lbl = sec['label']
        lh = cell_h * 0.16
        lw_ = text_width(lbl, lh)
        if lw_ > cell_w * 0.9:
            lh *= cell_w * 0.9 / lw_
        lst = text_strokes(lbl, (ccx - text_width(lbl, lh) / 2,
                                 gy0 + cell_h * row + cell_h * 0.08),
                           lh, 'ink', 0.9)
        montage.append({'groups': mini, 'label_st': lst,
                        'c': (ccx, gy0 + cell_h * row + cell_h * 0.08)})

    total_beats_end = beats[-1]['start_seconds'] + beats[-1]['duration_seconds']
    # thanks block drawn on the wiped board — lower-right area kept free
    # by the montage grid (grid fills the top rows)
    th_h = H * 0.14
    th_w = text_width('Thanks', th_h)
    if th_w > W * 0.30:
        th_h *= W * 0.30 / th_w
        th_w = text_width('Thanks', th_h)
    th_cx = W * 0.16
    th_cy = H * 0.30
    th = text_strokes('Thanks', (th_cx - th_w / 2, th_cy - th_h / 2),
                      th_h, 'ink', 1.3)
    hx = min(th_cx + th_w / 2 + th_h * 0.62, W / 2 - th_h * 0.55)
    heart = _heart_strokes((hx, th_cy + th_h * 0.02), th_h * 0.8)
    ending = {
        'wipe_t0': total_beats_end,
        'thanks_t0': total_beats_end + WIPE_SECONDS,
        'montage_t0': total_beats_end + WIPE_SECONDS + THANKS_SECONDS,
        'thanks': [('thanks', th, (0, 0), 1.0, None),
                   ('heart', heart, (0, 0), 1.0, None)],
        'montage': montage,
        'dur': WIPE_SECONDS + THANKS_SECONDS + CELL_SECONDS * len(montage)
               + END_HOLD,
    }
    flow = {'boards': boards, 'sections': out_sections,
            'ending': ending, 'board_rect': board_rect,
            'total_beats_end': total_beats_end}
    cache[ratio] = flow
    return flow


def ending_seconds(plan, ratio):
    return _build(plan, ratio)['ending']['dur']


def render_board_frame(plan: dict, ratio: str, t: float):
    """Fixed-camera frame: boards draw in place, wipe between boards,
    ending = wipe -> Thanks+heart -> montage grid -> hold."""
    flow = _build(plan, ratio)
    colors = _colors(plan)
    vw, vh = wbp.RATIO_SIZES[ratio]
    cam = (0.0, 0.0)
    zoom = 1.0
    scale = _map_scale(ratio)
    seed = 11
    layer = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
    tip = None
    t_end = flow['total_beats_end']

    def progress_draw(groups, base_seed):
        nonlocal tip
        for g, s, e in groups:
            p = wbp._ease(wbp._clamp((t - s) / max(0.05, e - s)))
            if p <= 0:
                continue
            t2 = _draw_strokes(layer, g[1], g[2], g[3], cam, colors,
                               ratio, p, base_seed, zoom)
            if t2:
                tip = t2
        return

    if t < t_end:
        # find active board
        board = None
        for bd in flow['boards']:
            bt0, bt1 = bd[0]['_board_t']
            if bt0 <= t < bt1 + 1e-9:
                board = bd
        last_board = flow['boards'][-1]
        # draw all sections of the active board (its full window)
        if board is not None:
            bt0, bt1 = board[0]['_board_t']
            for it in board[0].get('_board_divs', []):
                progress_draw(it['groups'], seed + 5)
            for sec in board:
                for it in sec['items2']:
                    progress_draw(it['groups'], seed + sec['bi'] * 7)
            # wipe during the tail of a non-last board
            if board is not last_board:
                w0 = bt1 - WIPE_SECONDS
                if t >= w0:
                    p = wbp._clamp((t - w0) / WIPE_SECONDS)
                    from PIL import ImageDraw
                    d = ImageDraw.Draw(layer)
                    pal = wbp._pal(plan)
                    d.rectangle([-8, -8, vw * p + 26, vh + 8],
                                fill=pal['bgc'])
        frame = _composite_frame(plan, ratio, cam, [(layer, 255)], seed)
        return _overlay_hand(frame, tip, ratio, t * 8 + seed)

    # -------- ending --------
    ending = flow['ending']
    rel = t - t_end
    pal = wbp._pal(plan)
    # wipe of the final board
    if rel < WIPE_SECONDS:
        p = wbp._clamp(rel / WIPE_SECONDS)
        from PIL import ImageDraw
        d = ImageDraw.Draw(layer)
        # draw remaining final-board ink then cover progressively
        for it in flow['boards'][-1][0].get('_board_divs', []):
            progress_draw(it['groups'], seed + 5)
        for sec in flow['boards'][-1]:
            for it in sec['items2']:
                for g, s, e in it['groups']:
                    _draw_strokes(layer, g[1], g[2], g[3], cam, colors,
                                  ratio, 1.0, seed + sec['bi'] * 7, zoom)
        d.rectangle([-8, -8, vw * p + 26, vh + 8], fill=pal['bgc'])
    else:
        # thanks
        tt = rel - WIPE_SECONDS
        for gi, g in enumerate(ending['thanks']):
            p = wbp._ease(wbp._clamp(
                (tt - gi * 0.9) / max(0.2, THANKS_SECONDS - 0.9)))
            if p > 0:
                t2 = _draw_strokes(layer, g[1], g[2], g[3], cam, colors,
                                   ratio, p, seed + 40 + gi, zoom)
                if t2:
                    tip = t2
        mt = tt - THANKS_SECONDS
        if mt > 0:
            for ci, cell in enumerate(ending['montage']):
                cs = ci * CELL_SECONDS
                p = wbp._ease(wbp._clamp((mt - cs) / CELL_SECONDS))
                if p <= 0:
                    continue
                for g in cell['groups']:
                    t2 = _draw_strokes(layer, g[1], g[2], g[3], cam,
                                       colors, ratio, p,
                                       seed + 80 + ci, zoom)
                    if t2:
                        tip = t2
                lg = ('plabel', [(p_, c_, ws_, False, True)
                                 for p_, c_, ws_, *_ in cell['label_st']],
                      (0, 0), 1.0, None)
                t2 = _draw_strokes(layer, lg[1], lg[2], lg[3], cam,
                                   colors, ratio, min(1.0, p * 1.6),
                                   seed + 99 + ci, zoom)
                if t2:
                    tip = t2
    frame = _composite_frame(plan, ratio, cam, [(layer, 255)], seed)
    return _overlay_hand(frame, tip, ratio, t * 8 + seed)
