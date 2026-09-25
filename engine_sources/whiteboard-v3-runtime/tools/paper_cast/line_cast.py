"""Paper-cast figure -> continuous-silhouette line art.

The paper-cast renderer draws a figure as overlapping filled masses — the
colors merge on paper into ONE body. Stroking each part's outline shows every
seam (the 'jointed' look). This converts the figure the way the eye reads it:
rasterize the filled masses into one mask, trace the union silhouette, then
keep the interior detail strokes (face, garment folds, trims) on top.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import svg_paths  # noqa: E402

_DETAIL_CLASSES = {'pb-face', 'pb-fold', 'pb-trim', 'pb-seam', 'pb-detail'}
_SKIP_CLASSES = {'pb-shadow', 'pb-rim'}
_FILL_CLASSES = {'pb-hair', 'pb-foot'}        # solid-ink regions
_HATCH_CLASSES = {'pb-top', 'pb-sleeve'}      # garment shading strokes
_SCALE = 4  # raster oversampling


def _shape_polys(el):
    """(polys, fill_default) for path/circle/ellipse/rect elements."""
    tag = el.tag.rsplit('}', 1)[-1]
    if tag == 'path':
        d = el.get('d') or ''
        return [p for p in svg_paths.parse_path_d(d) if len(p) >= 2]
    if tag == 'circle':
        cx, cy, r = (float(el.get(k) or 0) for k in ('cx', 'cy', 'r'))
        return [[(cx + r * np.cos(a), cy + r * np.sin(a))
                 for a in np.linspace(0, 2 * np.pi, 24)]]
    if tag == 'ellipse':
        cx, cy = float(el.get('cx') or 0), float(el.get('cy') or 0)
        rx, ry = float(el.get('rx') or 0), float(el.get('ry') or 0)
        return [[(cx + rx * np.cos(a), cy + ry * np.sin(a))
                 for a in np.linspace(0, 2 * np.pi, 28)]]
    if tag == 'rect':
        x, y = float(el.get('x') or 0), float(el.get('y') or 0)
        w, h = float(el.get('width') or 0), float(el.get('height') or 0)
        return [[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]]
    return []


def _collect(el, cls, out):
    cls = el.get('class') or cls
    if el.tag.rsplit('}', 1)[-1] == 'g':
        cls = el.get('class') or cls
    tag = el.tag.rsplit('}', 1)[-1]
    if tag in ('path', 'circle', 'ellipse', 'rect', 'polygon', 'polyline'):
        out.setdefault(cls, []).extend(_shape_polys(el))
    for c in el:
        _collect(c, cls, out)


def _rdp(pts, eps):
    if len(pts) < 3:
        return pts
    if np.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < eps:
        # closed loop: split at the point farthest from the start, rdp each arc
        d = [np.hypot(p[0] - pts[0][0], p[1] - pts[0][1]) for p in pts]
        i = int(np.argmax(d))
        if i < 2 or i > len(pts) - 3:
            return pts
        return _rdp(pts[:i + 1], eps)[:-1] + _rdp(pts[i:], eps)
    a, b = np.asarray(pts[0]), np.asarray(pts[-1])
    ab = b - a
    n = np.hypot(*ab) or 1e-9
    d = [abs(np.cross(ab / n, np.asarray(p) - a)) for p in pts]
    i = int(np.argmax(d))
    if d[i] <= eps:
        return [pts[0], pts[-1]]
    return _rdp(pts[:i + 1], eps)[:-1] + _rdp(pts[i:], eps)


def figure_strokes(svg_path, height=260.0):
    """-> [(polyline, is_detail)] in a unit space `height` tall, feet at 0."""
    root = ET.parse(svg_path).getroot()
    vb = root.get('viewBox')
    vx, vy, vw, vh = (float(v) for v in vb.split())
    grouped = {}
    _collect(root, '', grouped)

    W, H = int(vw * _SCALE) + 8, int(vh * _SCALE) + 8
    ox, oy = -vx * _SCALE + 4, -vy * _SCALE + 4
    mask = Image.new('L', (W, H), 0)
    md = ImageDraw.Draw(mask)
    details = []
    for cls, polys in grouped.items():
        key = next((c for c in cls.split() if c in _SKIP_CLASSES), None)
        if key or any(c in _SKIP_CLASSES for c in cls.split()):
            continue
        # degenerate geometry guard: a detail poly spanning nearly the whole
        # figure is a renderer artifact (e.g. pb-fold's ~2m ellipse under
        # stride poses) — drop it, never let it ink.
        polys = [p for p in polys
                 if not ((max(x for x, _ in p) - min(x for x, _ in p) > vw * 0.85)
                         or (max(y for _, y in p) - min(y for _, y in p) > vh * 0.85))]
        is_detail = any(c in _DETAIL_CLASSES for c in cls.split())
        is_fill = any(c in _FILL_CLASSES for c in cls.split())
        is_hatch = any(c in _HATCH_CLASSES for c in cls.split())
        for p in polys:
            sp = [(x * _SCALE + ox, y * _SCALE + oy) for x, y in p]
            if is_detail:
                details.append(sp)
            else:
                md.polygon(sp, fill=255)
            if is_fill:
                details.append(('fill', sp))
            elif is_hatch:
                details.append(('hatch', sp))
    # union silhouette contours
    arr = np.asarray(mask)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig = plt.figure()
    cs = plt.contour(arr, levels=[127])
    import os
    if os.environ.get('LINE_CAST_DEBUG'):
        print('DBG mask>', (arr > 127).sum(), 'levels', len(cs.allsegs),
              'segs0', [s.shape for s in cs.allsegs[0]][:5])
    segs = [seg.copy() for seg in cs.allsegs[0]]
    fig.clf(); plt.close(fig)
    contours = []
    for seg in segs:
        if len(seg) >= 8:
            xs_, ys_ = seg[:, 0], seg[:, 1]
            area = abs(np.dot(xs_, np.roll(ys_, -1))
                       - np.dot(ys_, np.roll(xs_, -1))) * 0.5
            if area > (H * W) * 0.0005:
                contours.append(seg)
    strokes = []
    k = height / vh / _SCALE
    for c in contours:
        simp = _rdp([tuple(p) for p in c], 1.2)
        if len(simp) >= 3:
            strokes.append(([(float((x - ox) * k), float((y - oy) * k))
                             for x, y in simp], False))
    for d in details:
        if isinstance(d, tuple) and d[0] in ('fill', 'hatch'):
            kind, sp = d
            if kind == 'fill':
                strokes.append(([(float((x - ox) * k), float((y - oy) * k))
                                 for x, y in sp], 'fill'))
                continue
            # hatch: diagonal strokes clipped inside the polygon
            xs = [p[0] for p in sp]; ys = [p[1] for p in sp]
            try:
                from matplotlib.path import Path as _MPath
                clip = _MPath(sp)
                x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
                diag = max(x1 - x0, y1 - y0)
                step = max(6.0, diag / 6)
                off = -diag
                while off < diag:
                    seg = []
                    for i in range(25):
                        t = i / 24
                        px = x0 + (x1 - x0) * t
                        py = y0 + (y1 - y0) * t + off   # slope +1 diagonal
                        if clip.contains_point((px, py)):
                            seg.append((px, py))
                        elif len(seg) > 1:
                            strokes.append(([(float((x - ox) * k), float((y - oy) * k))
                                             for x, y in seg], True))
                            seg = []
                        else:
                            seg = []
                    if len(seg) > 1:
                        strokes.append(([(float((x - ox) * k), float((y - oy) * k))
                                         for x, y in seg], True))
                    off += step
            except Exception:
                pass
            continue
        simp = _rdp([tuple(p) for p in d], 0.8)
        if len(simp) >= 2:
            strokes.append(([(float((x - ox) * k), float((y - oy) * k))
                             for x, y in simp], True))
    # recentre: x centred on silhouette bbox, feet at y=0
    xs = [q[0] for s, _ in strokes for q in s]
    ys = [q[1] for s, _ in strokes for q in s]
    if not xs:
        return []
    cx, y0 = (min(xs) + max(xs)) / 2, max(ys)
    return [([(px - cx, py - y0) for px, py in s], det)
            for s, det in strokes]


if __name__ == '__main__':
    import glob, os
    for f in sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else
                              '../assets/paper_cast/*.svg')):
        st = figure_strokes(f)
        print(os.path.basename(f), len(st), 'strokes')
