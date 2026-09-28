#!/usr/bin/env python3
"""Still-page certification for paperbook films.

A printed page may change during its hold only where the story acts: the focus actors'
swept boxes (from tools/focus_probe.cjs), the performer, and timed maths print (an
equation inked on its word). Everything else — sky, ground, frames, prose — must stay
pixel-still. Alongside the pixel gate it checks that every focus action starts on its
spoken word and that every action carries its sound on the same onset.

  python3 tools/stillness_gate.py --plan plan_16x9.json --focus focus.json \
      --frames frames_16x9 [--out stillness.json]
"""
import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

DIFF_LEVEL = 28          # per-channel delta that counts as a real change (above JPEG noise)
STRAY_MAX = 0.0006       # changed share of the frame allowed outside the focus boxes
PAD_PX = 14              # focus boxes grow by this much (anti-aliased edges, contact pools)
WORD_SYNC_MS = 90        # action onset vs its spoken word
SFX_SYNC_MS = 45         # accent onset vs its action onset
DENSE_RUN_MS = 200        # actions closer than this share one accent
SETTLE_MS = 160          # after the page lands
PRE_TURN_MS = 60         # before the leaf lifts


def _frame(frames: str, i: int) -> Optional[np.ndarray]:
    for ext in ('jpg', 'png'):
        p = os.path.join(frames, f'f{i:05d}.{ext}')
        if os.path.exists(p):
            return np.asarray(Image.open(p).convert('RGB'), dtype=np.int16)
    return None


def _mask(shape: Tuple[int, int], boxes: List[List[float]]) -> np.ndarray:
    m = np.zeros(shape, dtype=bool)
    h, w = shape
    for b in boxes:
        x0, y0 = max(0, int(b[0] - PAD_PX)), max(0, int(b[1] - PAD_PX))
        x1, y1 = min(w, int(b[2] + PAD_PX) + 1), min(h, int(b[3] + PAD_PX) + 1)
        if x1 > x0 and y1 > y0:
            m[y0:y1, x0:x1] = True
    return m


def _stray_box(stray: np.ndarray) -> Optional[List[int]]:
    ys, xs = np.nonzero(stray)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def certify(plan: Dict[str, Any], focus: Dict[str, Any], frames: str, fps: int) -> Dict[str, Any]:
    fb = {b['beat_id']: b for b in focus['beats']}
    pages, failures = [], []
    for b in plan['beats']:
        bid = b['beat_id']
        tr = b.get('transition') or {}
        t0 = b['start_ms'] + SETTLE_MS
        t1 = b['start_ms'] + (tr.get('start_ms') if tr else b['duration_ms']) - PRE_TURN_MS
        rec = fb.get(bid) or {'focus': [], 'figure': None, 'edu': []}
        boxes = [f['box'] for f in rec['focus'] if f.get('box')] + ([rec['figure']] if rec.get('figure') else []) + list(rec.get('edu') or [])
        f0, f1 = int(np.ceil(t0 * fps / 1000)), int(t1 * fps / 1000)
        ref = _frame(frames, f0)
        page = {'beat_id': bid, 'hold_ms': [t0, t1], 'frames': [f0, f1], 'focus': [f['id'] for f in rec['focus']],
                'worst_stray': 0.0, 'worst_frame': None, 'stray_box': None, 'focus_changed': 0.0}
        if ref is None:
            failures.append(f'{bid}:FRAMES_MISSING')
            pages.append(page)
            continue
        allow = _mask(ref.shape[:2], boxes)
        for i in range(f0 + 1, f1 + 1):
            fr = _frame(frames, i)
            if fr is None:
                continue
            changed = np.abs(fr - ref).max(axis=2) > DIFF_LEVEL
            stray = changed & ~allow
            share = float(stray.mean())
            page['focus_changed'] = max(page['focus_changed'], float((changed & allow).mean()))
            if share > page['worst_stray']:
                page['worst_stray'], page['worst_frame'], page['stray_box'] = share, i, _stray_box(stray)
        if page['worst_stray'] > STRAY_MAX:
            failures.append(f"{bid}:PAGE_NOT_STILL:{page['worst_stray'] * 100:.3f}% changed outside focus at f{page['worst_frame']} box {page['stray_box']}")
        if rec['focus'] and page['focus_changed'] == 0.0:
            failures.append(f'{bid}:FOCUS_NEVER_MOVED')
        pages.append(page)
    return {'pages': pages, 'failures': failures}


def word_sync(plan: Dict[str, Any]) -> Dict[str, Any]:
    rows, failures = [], []
    for b in plan['beats']:
        il = b.get('illustration') or {}
        evs = list((il.get('direction') or {}).get('events') or [])
        seen = {ev['id'] for ev in evs}
        evs += [dict(e['action'], id=e['id']) for e in il.get('entities') or []
                if e['id'] not in seen and (e.get('action') or {}).get('word_ms') is not None]
        for ev in evs:
            if ev.get('word_ms') is None:
                continue
            d = int(ev['at']) - int(ev['word_ms'])
            ok = ev.get('clamped') or abs(d) <= WORD_SYNC_MS or ev.get('reason') == 'count'
            rows.append({'beat_id': b['beat_id'], 'id': ev['id'], 'kind': ev['kind'], 'word': ev.get('word'), 'delta_ms': d})
            if not ok:
                failures.append(f"{b['beat_id']}:{ev['id']}:WORD_SYNC:{ev['kind']} {d:+d}ms from '{ev.get('word')}'")
    return {'rows': rows, 'failures': failures}


def sound_sync(plan: Dict[str, Any]) -> Dict[str, Any]:
    rows, failures = [], []
    for b in plan['beats']:
        accents = (b.get('sound') or {}).get('accents') or []
        acts = sorted(((int(e['action']['at']), e) for e in (b.get('illustration') or {}).get('entities') or []
                       if (e.get('action') or {}).get('at') is not None), key=lambda x: x[0])
        prev_at, prev_ok = None, False
        for at, e in acts:
            a = e['action']
            # A tight run (a row of an array landing together) reads as one sound: the
            # run's first accent covers the rest.
            if prev_ok and prev_at is not None and at - prev_at < DENSE_RUN_MS:
                prev_at = at
                continue
            hit = [x for x in accents if x.get('target') == e['id'] and abs(int(x['beat_at_ms']) - at) <= SFX_SYNC_MS]
            near = [x for x in accents if abs(int(x['beat_at_ms']) - at) <= SFX_SYNC_MS]
            rows.append({'beat_id': b['beat_id'], 'id': e['id'], 'kind': a['kind'], 'at': at,
                         'sound': (hit or near or [{}])[0].get('asset_id')})
            prev_at, prev_ok = at, bool(hit or near)
            if not (hit or near):
                failures.append(f"{b['beat_id']}:{e['id']}:SFX_MISSING:{a['kind']} at {at}ms")
    return {'rows': rows, 'failures': failures}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True)
    ap.add_argument('--focus', required=True)
    ap.add_argument('--frames', required=True)
    ap.add_argument('--fps', type=int, help='capture fps (default: the render manifest beside the frames, else the plan)')
    ap.add_argument('--out')
    args = ap.parse_args()
    plan = json.load(open(args.plan))
    focus = json.load(open(args.focus))
    fps = args.fps
    if not fps:
        man = os.path.join(os.path.dirname(os.path.abspath(args.frames)), f"render_{plan.get('aspect', '16x9')}.json")
        fps = json.load(open(man))['fps'] if os.path.exists(man) else plan['fps']
    still, words, sound = certify(plan, focus, args.frames, fps), word_sync(plan), sound_sync(plan)
    fails = still['failures'] + words['failures'] + sound['failures']
    report = {'gate': 'FAIL' if fails else 'PASS', 'failures': fails, 'stillness': still, 'word_sync': words, 'sound_sync': sound}
    if args.out:
        json.dump(report, open(args.out, 'w'), indent=1)
    for p in still['pages']:
        print(f"{p['beat_id']}: focus={len(p['focus'])} stray={p['worst_stray'] * 100:.4f}% focus_changed={p['focus_changed'] * 100:.2f}%")
    print(json.dumps({'gate': report['gate'], 'failures': fails}, indent=1))
    return 0 if not fails else 3


if __name__ == '__main__':
    sys.exit(main())
