"""Comic/storyboard render mode — panels that draw themselves.

One beat = one panel on a hand-drawn comic page. In the beat's window the
panel inks in order: wobbled border -> narration caption box -> the posed
figure (a baked sprite frame revealed top-to-bottom) -> speech bubble with
hand-lettered text. Earlier panels stay inked; the page holds at the end.

Plan contract (per beat):
    figure: {clip|say, pose (clip seconds to freeze, default 1.0),
             facing (1/-1), x (0..1 inside panel, default .5),
             size (0..1 of panel height, default .62)}
    bubble: "text"  or  {text, x, y (0..1 inside panel)}
    caption / heroRole: narration-box line at the panel's top-left
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

import whiteboard_pil_adapter as wbp
from v3_board_renderer import (
    _draw_strokes, _map_scale,
    _composite_frame, _overlay_hand,
)
from v3_board_renderer import text_strokes, text_width
from v3_board_sections import _wobble_line, _bubble_box, _colors
from tools.nexstick import fig_motion as _fm

FPS = 12
END_HOLD = 1.2
# draw-order windows inside each beat (fractions of beat duration)
W_BORDER = (0.00, 0.30)
W_CAPTION = (0.10, 0.45)
W_FIGURE = (0.25, 0.75)
W_BUBBLE = (0.55, 0.95)


def _wrap(text, max_w, h):
    """Greedy wrap into <=3 Hershey lines that fit max_w."""
    words = str(text).split()
    if not words:
        return []
    lines, cur = [], ''
    for w_ in words:
        trial = (cur + ' ' + w_).strip()
        if text_width(trial, h) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
            if len(lines) == 3:
                break
    if cur and len(lines) < 3:
        lines.append(cur)
    return lines


def _panel_border(rect, seed):
    x0, y0, x1, y1 = rect
    st = []
    for k, (p0, p1) in enumerate((
            ((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
            ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))):
        st.append((_wobble_line(p0, p1, n=24, wob=2.2, seed=seed + k),
                   'ink', 1.15, False, True))
    return st


def _build(plan, ratio):
    cache = plan.setdefault('_comic_flow', {})
    if ratio in cache:
        return cache[ratio]
    vw, vh = wbp.RATIO_SIZES[ratio]
    scale = _map_scale(ratio)
    W, H = vw / scale, vh / scale
    m = W * 0.055
    gap = W * 0.025
    beats = plan.get('beats') or []
    n = max(1, len(beats))
    aspect = vw / vh
    cols = max(1, math.ceil(math.sqrt(n * aspect)))
    rows = max(1, math.ceil(n / cols))
    pw = (W - 2 * m - (cols - 1) * gap) / cols
    ph = (H - 2 * m - (rows - 1) * gap) / rows

    panels = []
    for bi, beat in enumerate(beats):
        col, row = bi % cols, bi // cols
        rect = (-W / 2 + m + col * (pw + gap),
                -H / 2 + m + row * (ph + gap),
                -W / 2 + m + col * (pw + gap) + pw,
                -H / 2 + m + row * (ph + gap) + ph)
        t0 = float(beat.get('start_seconds', 0.0))
        t1 = t0 + float(beat.get('duration_seconds', 4.0))
        dur = t1 - t0
        fig = beat.get('figure')
        bub = beat.get('bubble')
        if isinstance(bub, str):
            bub = {'text': bub}
        cap = str(beat.get('caption') or beat.get('heroRole') or '') \
            .replace('_', ' ').title()

        # figure anchor: bottom-center of panel interior
        fx = (rect[0] + rect[2]) / 2 + pw * 0.0
        if fig is not None:
            fx = rect[0] + pw * float(fig.get('x', 0.5))
        fy = rect[3] - ph * 0.05
        fsize = ph * float((fig or {}).get('size', 0.72))
        facing = int((fig or {}).get('facing', -1))

        # bubble: upper area of the panel, tail aimed at the figure's
        # head — sized to the wrapped text, never the other way around
        bub_groups = []
        if bub:
            th_ = ph * 0.085
            lines = _wrap(bub.get('text', ''), pw * 0.52, th_)
            bw = min(pw * 0.60,
                     max((text_width(ln, th_) for ln in lines),
                         default=0.0) + th_ * 2.2)
            bh_ = th_ * 1.30 * max(1, len(lines)) + th_ * 1.1
            bcx = rect[0] + pw * float(bub.get('x', 0.74))
            bcx = max(rect[0] + bw / 2 + pw * 0.03,
                      min(bcx, rect[2] - bw / 2 - pw * 0.03))
            bcy = rect[1] + ph * float(bub.get('y', 0.30))
            tail_to = (fx + pw * 0.02, fy - fsize * 0.92)
            bub_groups = _bubble_box((bcx, bcy), bw, bh_, tail_to)
            ly = bcy - th_ * 1.30 * len(lines) / 2
            for li, ln in enumerate(lines):
                tst = text_strokes(ln, (bcx - text_width(ln, th_) / 2,
                                        ly + li * th_ * 1.30),
                                   th_, 'ink', 0.9)
                bub_groups += [(p_, c_, ws_, False, True)
                               for p_, c_, ws_, *_ in tst]

        # narration caption box — small rect + text at the panel's top-left
        cap_groups = []
        if cap:
            ch_ = ph * 0.11
            ctext = cap.upper()
            cw_ = text_width(ctext, ch_) + ch_ * 1.1
            cx0, cy0 = rect[0] + pw * 0.04, rect[1] + ph * 0.05
            box = [_wobble_line((cx0, cy0), (cx0 + cw_, cy0), n=14,
                                wob=1.2, seed=bi + 40),
                   _wobble_line((cx0, cy0 + ch_ * 1.7),
                                (cx0 + cw_, cy0 + ch_ * 1.7), n=14,
                                wob=1.2, seed=bi + 41),
                   [(cx0, cy0), (cx0, cy0 + ch_ * 1.7)],
                   [(cx0 + cw_, cy0), (cx0 + cw_, cy0 + ch_ * 1.7)]]
            cap_groups += [(s_, 'ink', 1.0, False, True) for s_ in box]
            tst = text_strokes(ctext, (cx0 + ch_ * 0.55, cy0 + ch_ * 0.30),
                               ch_, 'ink', 0.95)
            cap_groups += [(p_, c_, ws_, False, True)
                           for p_, c_, ws_, *_ in tst]

        panels.append({
            'bi': bi, 't0': t0, 't1': t1, 'dur': dur, 'rect': rect,
            'border': _panel_border(rect, bi * 7 + 3),
            'cap_groups': cap_groups,
            'bub_groups': bub_groups,
            'fig': fig, 'fx': fx, 'fy': fy, 'fsize': fsize,
            'facing': facing,
        })

    flow = {'panels': panels,
            'total': (beats[-1]['start_seconds']
                      + beats[-1]['duration_seconds']) if beats else 0.0}
    cache[ratio] = flow
    return flow


def ending_seconds(plan, ratio):
    return END_HOLD


def _fig_frame(spec, facing):
    """One posed sprite frame for the panel."""
    sp = dict(spec)
    sp.pop('pose', None)
    sp.pop('x', None)
    sp.pop('size', None)
    sp['mirror'] = (facing == 1)
    strip = _fm.get_strip(sp, 1.6, fps=FPS)
    if not strip:
        return None
    pose = float(spec.get('pose', 1.0))
    return strip[min(len(strip) - 1, max(0, int(pose * FPS)))]


def _paste_masked(frame, img, cx_px, feet_px, h_px, clip_rect, reveal):
    """Paste figure inside a panel rect, revealed top->bottom by reveal."""
    img2 = img.resize((max(1, int(img.width * h_px / img.height)),
                       max(1, int(h_px))), Image.LANCZOS)
    px = int(cx_px - img2.width / 2)
    py = int(feet_px - img2.height)
    tile = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    tile.alpha_composite(img2, (px, py))
    a = tile.getchannel('A')
    mask = Image.new('L', frame.size, 0)
    md = ImageDraw.Draw(mask)
    x0, y0, x1, y1 = clip_rect
    ry = y0 + (y1 - y0) * wbp._clamp(reveal)
    md.rectangle([x0, y0, x1, ry], fill=255)
    a = Image.composite(a, Image.new('L', frame.size, 0), mask)
    tile.putalpha(a)
    return Image.alpha_composite(frame.convert('RGBA'), tile).convert('RGB')


def render_comic_frame(plan: dict, ratio: str, t: float):
    flow = _build(plan, ratio)
    colors = _colors(plan)
    vw, vh = wbp.RATIO_SIZES[ratio]
    scale = _map_scale(ratio)
    cam = (0.0, 0.0)
    zoom = 1.0
    seed = 31
    layer = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
    tip = None

    def local_p(sec, win, default=1.0):
        if t >= sec['t1']:
            return 1.0
        lt = t - sec['t0']
        if lt < 0:
            return 0.0
        return wbp._ease(wbp._clamp(
            (lt - win[0] * sec['dur'])
            / max(0.1, (win[1] - win[0]) * sec['dur'])))

    fig_overlays = []   # (img, cx, fy, h, clip_rect_px, reveal_p)
    for sec in flow['panels']:
        if t < sec['t0']:
            continue
        g_seed = seed + sec['bi'] * 13
        p = local_p(sec, W_BORDER)
        if p > 0:
            t2 = _draw_strokes(layer, sec['border'], (0, 0), 1.0, cam,
                               colors, ratio, p, g_seed, zoom)
            if t2:
                tip = t2
        p = local_p(sec, W_CAPTION)
        if p > 0 and sec['cap_groups']:
            g = ('capbox', sec['cap_groups'], (0, 0), 1.0, None)
            t2 = _draw_strokes(layer, g[1], g[2], g[3], cam, colors,
                               ratio, p, g_seed + 1, zoom)
            if t2:
                tip = t2
        p = local_p(sec, W_BUBBLE)
        if p > 0 and sec['bub_groups']:
            g = ('bubble', sec['bub_groups'], (0, 0), 1.0, None)
            t2 = _draw_strokes(layer, g[1], g[2], g[3], cam, colors,
                               ratio, p, g_seed + 2, zoom)
            if t2:
                tip = t2
        if sec['fig'] is not None:
            p = local_p(sec, W_FIGURE, 1.0)
            if p > 0:
                img = _fig_frame(sec['fig'], sec['facing'])
                if img is not None:
                    x0, y0, x1, y1 = sec['rect']
                    cx, fy = wbp._map_point((sec['fx'], sec['fy']),
                                            cam, ratio, zoom)
                    px0, py0 = wbp._map_point((x0, y0), cam, ratio, zoom)
                    px1, py1 = wbp._map_point((x1, y1), cam, ratio, zoom)
                    h_px = sec['fsize'] * scale
                    fig_overlays.append(
                        (img, cx, fy, h_px,
                         (px0 + 3, py0 + 3, px1 - 3, py1 - 3), p))

    frame = _composite_frame(plan, ratio, cam, [(layer, 255)], seed)
    for img, cx, fy, h_px, clip, rv in fig_overlays:
        frame = _paste_masked(frame, img, cx, fy, h_px, clip, rv)
    return _overlay_hand(frame, tip, ratio, t * 8 + seed)
