"""Minimal SVG path -> polyline sampling for authored illustration assets.

Supports absolute and relative M/L/H/V/C/S/Q/Z commands (the Open Peeps
lineage uses only absolute M/C/L/Z; relative + smooth forms are covered for
robustness). Arc segments are approximated by a straight segment to the arc
end point — sufficient for authored outline assets.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

_TOK = re.compile(r"[MLHVCSQTAZmlhvcsqtaz]|-?\d*\.?\d+(?:e[+-]?\d+)?")

CUBIC_SAMPLES = 14
QUAD_SAMPLES = 10


def _cubic(p0, c1, c2, p1, n=CUBIC_SAMPLES):
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        out.append(
            (
                mt * mt * mt * p0[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t * t * t * p1[0],
                mt * mt * mt * p0[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t * t * t * p1[1],
            )
        )
    return out


def _quad(p0, c, p1, n=QUAD_SAMPLES):
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        out.append(
            (
                mt * mt * p0[0] + 2 * mt * t * c[0] + t * t * p1[0],
                mt * mt * p0[1] + 2 * mt * t * c[1] + t * t * p1[1],
            )
        )
    return out


def parse_path_d(d: str):
    """Return list of polylines (each a list of (x, y) points)."""
    toks = _TOK.findall(d)
    polys = []
    cur = []
    pos = (0.0, 0.0)
    start = (0.0, 0.0)
    prev_ctrl = None
    i = 0
    cmd = None

    def is_cmd(t):
        return len(t) == 1 and t.isalpha()

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        if is_cmd(toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur and cur[-1] != start:
                    cur.append(start)
                if cur:
                    polys.append(cur)
                cur = []
                pos = start
                prev_ctrl = None
                continue
        if cmd is None:
            break
        rel = cmd.islower()
        c = cmd.upper()

        def pt():
            x, y = num(), num()
            if rel:
                return (pos[0] + x, pos[1] + y)
            return (x, y)

        try:
            if c == "M":
                p = pt()
                if cur:
                    polys.append(cur)
                cur = [p]
                pos = start = p
                cmd = "l" if rel else "L"
            elif c == "L":
                while i < len(toks) and not is_cmd(toks[i]):
                    p = pt()
                    cur.append(p)
                    pos = p
                prev_ctrl = None
            elif c == "H":
                while i < len(toks) and not is_cmd(toks[i]):
                    x = num()
                    x = pos[0] + x if rel else x
                    pos = (x, pos[1])
                    cur.append(pos)
                prev_ctrl = None
            elif c == "V":
                while i < len(toks) and not is_cmd(toks[i]):
                    y = num()
                    y = pos[1] + y if rel else y
                    pos = (pos[0], y)
                    cur.append(pos)
                prev_ctrl = None
            elif c == "C":
                while i < len(toks) and not is_cmd(toks[i]):
                    c1 = pt()
                    c2 = pt()
                    p = pt()
                    cur.extend(_cubic(pos, c1, c2, p))
                    pos = p
                    prev_ctrl = c2
            elif c == "S":
                while i < len(toks) and not is_cmd(toks[i]):
                    c1 = (2 * pos[0] - prev_ctrl[0], 2 * pos[1] - prev_ctrl[1]) if prev_ctrl else pos
                    c2 = pt()
                    p = pt()
                    cur.extend(_cubic(pos, c1, c2, p))
                    pos = p
                    prev_ctrl = c2
            elif c == "Q":
                while i < len(toks) and not is_cmd(toks[i]):
                    c1 = pt()
                    p = pt()
                    cur.extend(_quad(pos, c1, p))
                    pos = p
                    prev_ctrl = c1
            elif c == "T":
                while i < len(toks) and not is_cmd(toks[i]):
                    c1 = (2 * pos[0] - prev_ctrl[0], 2 * pos[1] - prev_ctrl[1]) if prev_ctrl else pos
                    p = pt()
                    cur.extend(_quad(pos, c1, p))
                    pos = p
                    prev_ctrl = c1
            elif c == "A":
                while i < len(toks) and not is_cmd(toks[i]):
                    num(); num(); num(); num(); num()
                    p = pt()
                    cur.append(p)
                    pos = p
                prev_ctrl = None
            else:
                break
        except (IndexError, ValueError):
            break
    if cur:
        polys.append(cur)
    return polys


def load_svg_strokes(path):
    """Load an SVG file; return (polylines_per_element, viewBox, fills).

    Each element is (polylines, fill, closed) where fill is the element's
    fill attribute (or 'default') and closed marks Z-terminated outlines.
    """
    tree = ET.parse(str(path))
    root = tree.getroot()
    vb = root.get("viewBox")
    view_box = tuple(float(v) for v in vb.split()) if vb else (0.0, 0.0, float(root.get("width", 100)), float(root.get("height", 100)))
    out = []
    _TR = re.compile(r"translate\(\s*(-?\d*\.?\d+(?:e[+-]?\d+)?)[ ,]+(-?\d*\.?\d+(?:e[+-]?\d+)?)\s*\)")

    def walk(el, tx, ty):
        m = _TR.search(el.get("transform") or "")
        if m:
            tx += float(m.group(1))
            ty += float(m.group(2))
        if el.tag.rsplit("}", 1)[-1] == "path":
            d = el.get("d")
            if d and re.search(r"[MLHVCSQTAZmlhvcsqtaz]", d):
                polys = [
                    [(x + tx, y + ty) for x, y in poly]
                    for poly in parse_path_d(d)
                    if len(poly) >= 2
                ]
                if polys:
                    out.append((polys, el.get("fill") or "default", d.rstrip().upper().endswith("Z")))
        for child in el:
            walk(child, tx, ty)

    walk(root, 0.0, 0.0)
    return out, view_box


def rescale(strokes, view_box, center, size):
    """Map SVG-space polylines onto board space centered at `center` with
    bounding-box height `size` (aspect preserved). Returns same structure."""
    x0, y0, w, h = view_box
    scale = size / h if h else 1.0
    out = []
    for polys, fill, closed in strokes:
        mapped = [
            [((x - (x0 + w / 2)) * scale + center[0], (y - (y0 + h / 2)) * scale + center[1]) for x, y in poly]
            for poly in polys
        ]
        out.append((mapped, fill, closed))
    return out
