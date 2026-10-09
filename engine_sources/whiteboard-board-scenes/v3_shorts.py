"""Rigged-shorts render mode — the character IS the scene.

A stage, not a board: a hand-drawn floor line, a hand-lettered caption,
and the baked line-art figure performing full-frame. Entrances and exits
play real walk-cycles while the figure travels; everything else is the
beat's clip (host gestures, motions, exercises) straight from fig_motion.

Plan contract (per beat):
    figure:  {clip|say, x (0..1 stage position, default .5),
              size (0..1 of stage height, default .85), facing (1 right /
              -1 left), enter ('left'|'right'), exit ('left'|'right'),
              enter_clip / exit_clip (default NEX_MOTION_WALK)}
    figures: [...]  same spec, for two-character beats
    caption: hand-lettered line drawn at the top during the beat
"""
from __future__ import annotations

from PIL import Image

import whiteboard_pil_adapter as wbp
from v3_board_renderer import (
    _draw_strokes, _map_scale,
    _composite_frame, _overlay_hand,
)
from v3_board_renderer import text_strokes, text_width
from v3_board_sections import _wobble_line, _colors
from tools.nexstick import fig_motion as _fm

FPS = 12
END_HOLD = 1.0
WALK_ENTER_MAX = 1.6          # cap on entrance travel time
WALK_EXIT_MAX = 1.4


def _figs_for(beat):
    specs = beat.get('figures')
    if specs:
        return [dict(s) for s in specs]
    f = beat.get('figure')
    return [dict(f)] if f else []


def _build(plan, ratio):
    """Stage layout + per-beat figure schedule; cached per plan+ratio."""
    cache = plan.setdefault('_shorts_flow', {})
    if ratio in cache:
        return cache[ratio]
    vw, vh = wbp.RATIO_SIZES[ratio]
    scale = _map_scale(ratio)
    W, H = vw / scale, vh / scale
    m = W * 0.06
    floor_y = -H / 2 + H * 0.80        # world y=+H/2 is the frame bottom
    top_y = -H / 2 + H * 0.10
    stage_h = floor_y - top_y          # figure max height in world units

    floor_st = _wobble_line((-W / 2 + m, floor_y), (W / 2 - m, floor_y),
                            n=60, wob=3.0, seed=5)
    floor_item = [('ground', [(floor_st, 'ink', 1.0, False, True)],
                   (0, 0), 1.0, None)]

    beats = plan.get('beats') or []
    secs = []
    for bi, beat in enumerate(beats):
        t0 = float(beat.get('start_seconds', 0.0))
        t1 = t0 + float(beat.get('duration_seconds', 4.0))
        dur = t1 - t0
        figs = _figs_for(beat)
        n = len(figs)
        sched = []
        for fi, spec in enumerate(figs):
            x = float(spec.get('x', 0.5 if n == 1 else
                               (0.34 + 0.32 * fi)))
            facing = int(spec.get('facing', -1))
            enter = spec.get('enter')
            exit_ = spec.get('exit')
            enter_dur = min(WALK_ENTER_MAX, dur * 0.35) if enter else 0.0
            exit_dur = min(WALK_EXIT_MAX, dur * 0.30) if exit_ else 0.0
            sched.append({
                'spec': spec, 'x': x, 'facing': facing,
                'enter': enter, 'exit': exit_,
                'enter_dur': enter_dur, 'exit_dur': exit_dur,
                'size': float(spec.get('size', 0.85)),
            })
        cap = str(beat.get('caption') or beat.get('heroRole')
                  or '').replace('_', ' ').title()
        ch_ = min(H * 0.075, stage_h * 0.13)
        cap_st = []
        if cap:
            tw_ = text_width(cap, ch_)
            if tw_ > W * 0.7:
                ch_ *= W * 0.7 / tw_
            tw_ = text_width(cap, ch_)
            cap_st = text_strokes(cap, (-tw_ / 2, -H / 2 + H * 0.045),
                                  ch_, 'ink', 1.1)
        secs.append({'bi': bi, 't0': t0, 't1': t1, 'dur': dur,
                     'sched': sched, 'cap_st': cap_st,
                     'cap_win': (0.15, 0.95)})
    flow = {'secs': secs, 'floor': floor_item, 'floor_y': floor_y,
            'stage_h': stage_h, 'W': W, 'H': H,
            'total': (beats[-1]['start_seconds']
                      + beats[-1]['duration_seconds']) if beats else 0.0}
    cache[ratio] = flow
    return flow


def ending_seconds(plan, ratio):
    return END_HOLD


def _fig_strip(spec, seconds, facing):
    """Strip for a spec honoring facing (our sprites default face-left)."""
    sp = dict(spec)
    sp['mirror'] = (facing == 1)
    return _fm.get_strip(sp, seconds, fps=FPS)


def _paste_fig(frame, img, cx_px, feet_px, h_px):
    img2 = img.resize((max(1, int(img.width * h_px / img.height)),
                       max(1, int(h_px))), Image.LANCZOS)
    tile = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    tile.alpha_composite(img2, (int(cx_px - img2.width / 2),
                                int(feet_px - img2.height)))
    return Image.alpha_composite(frame.convert('RGBA'), tile).convert('RGB')


def render_short_frame(plan: dict, ratio: str, t: float):
    flow = _build(plan, ratio)
    colors = _colors(plan)
    vw, vh = wbp.RATIO_SIZES[ratio]
    scale = _map_scale(ratio)
    W = flow['W']
    cam = (0.0, 0.0)
    zoom = 1.0
    seed = 23
    layer = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
    tip = None

    # floor inks once, during the first half-second
    p_floor = wbp._ease(wbp._clamp(t / 0.5))
    if p_floor > 0:
        t2 = _draw_strokes(layer, flow['floor'][0][1], (0, 0), 1.0,
                           cam, colors, ratio, p_floor, seed, zoom)
        if t2:
            tip = t2

    sec = next((s for s in reversed(flow['secs']) if s['t0'] <= t),
               flow['secs'][-1] if flow['secs'] else None)
    if sec is not None:
        local = t - sec['t0']
        cs, ce = sec['cap_win']
        p_cap = wbp._ease(wbp._clamp(
            (local - cs) / max(0.1, ce - cs)))
        if p_cap > 0 and sec['cap_st']:
            g = ('plabel', [(p_, c_, ws_, False, True)
                            for p_, c_, ws_, *_ in sec['cap_st']],
                 (0, 0), 1.0, None)
            t2 = _draw_strokes(layer, g[1], g[2], g[3], cam, colors,
                               ratio, p_cap, seed + 3, zoom)
            if t2:
                tip = t2
        frame = _composite_frame(plan, ratio, cam, [(layer, 255)], seed)
        floor_y = flow['floor_y']
        stage_h = flow['stage_h']
        for sch in sec['sched']:
            spec = sch['spec']
            dur = sec['dur']
            x = sch['x']
            enter, exit_ = sch['enter'], sch['exit']
            e_dur, x_dur = sch['enter_dur'], sch['exit_dur']
            # choose strip + x(t): entrance walk, beat clip, or exit walk
            if enter and local < e_dur:
                p = wbp._ease(wbp._clamp(local / e_dur))
                edge = -0.14 if enter == 'left' else 1.14
                xw = edge + (x - edge) * p
                walk_clip = spec.get('enter_clip') or 'NEX_MOTION_WALK'
                fdir = 1 if enter == 'left' else -1
                strip = _fig_strip({'clip': walk_clip,
                                    't': spec.get('t')}, e_dur, fdir)
                idx = int(local * FPS)
            elif exit_ and local > dur - x_dur:
                q = wbp._ease(wbp._clamp(
                    (local - (dur - x_dur)) / max(0.1, x_dur)))
                edge = -0.14 if exit_ == 'left' else 1.14
                xw = x + (edge - x) * q
                walk_clip = spec.get('exit_clip') or 'NEX_MOTION_WALK'
                fdir = 1 if exit_ == 'right' else -1
                strip = _fig_strip({'clip': walk_clip,
                                    't': spec.get('t')}, x_dur, fdir)
                idx = int((local - (dur - x_dur)) * FPS)
            else:
                clip_t = local - e_dur
                strip = _fig_strip(spec, max(dur - e_dur - x_dur, 0.5),
                                   sch['facing'])
                idx = int(clip_t * FPS)
                xw = x
            if not strip:
                continue
            img = strip[min(len(strip) - 1, max(0, idx))]
            h_px = sch['size'] * stage_h * scale * \
                float(spec.get('scale', 1.0))
            cx, fy = wbp._map_point(
                ((xw - 0.5) * (W - 2 * (W * 0.06)), floor_y),
                cam, ratio, zoom)
            frame = _paste_fig(frame, img, cx, fy, h_px)
        return _overlay_hand(frame, tip, ratio, t * 8 + seed)

    frame = _composite_frame(plan, ratio, cam, [(layer, 255)], seed)
    return _overlay_hand(frame, tip, ratio, t * 8 + seed)
