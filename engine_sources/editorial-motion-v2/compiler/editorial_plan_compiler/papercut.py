"""Papercut — an imported image re-printed in the film's own ink.

A bank painting or photograph pasted raw into a paperbook reads as collage debris.
This pass prints it the way a screen-printer would: quantize to a handful of tones,
then remap every tone to the nearest colour on a ramp built from the film's brand
(paper → ink steps plus the accent), so every imported plate is painted in the
film's own pigments. Deterministic: same source + brand → identical output.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageFilter


def _hex_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tonal_ramp(paper: str, ink: str, accent: str) -> List[Tuple[int, int, int]]:
    """The film's printable inks: a stepped ramp paper→ink plus the accent pair."""
    p, k, a = _hex_rgb(paper), _hex_rgb(ink), _hex_rgb(accent)
    return [
        p,
        _mix(p, k, 0.18),
        _mix(p, k, 0.38),
        _mix(p, k, 0.60),
        _mix(p, k, 0.82),
        k,
        _mix(a, p, 0.30),          # accent tint
        _mix(a, k, 0.18),          # accent shade
    ]


def _lum(c: Tuple[int, int, int]) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _dist(c: Tuple[int, int, int], t: Tuple[int, int, int]) -> float:
    # Luminance-weighted RGB distance: screen printing keeps tonal steps honest —
    # a mid sky maps to a mid ink, not the nearest hue.
    dl = (_lum(c) - _lum(t)) * 1.6
    dr, dg, db = c[0] - t[0], c[1] - t[1], c[2] - t[2]
    return dl * dl + dr * dr + dg * dg + db * db


def papercut_image(src: str, dest: str, ramp: List[Tuple[int, int, int]],
                   n_colors: int = 6, max_w: int = 900) -> dict:
    """Posterize `src` into `dest`, palette-locked to `ramp`. Returns the record."""
    im = Image.open(src).convert('RGB')
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    q = im.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
    src_pal = q.getpalette()[: n_colors * 3]
    clusters = [tuple(src_pal[i * 3: i * 3 + 3]) for i in range(n_colors)]
    remap = [min(ramp, key=lambda t, c=c: _dist(c, t)) for c in clusters]
    # Rebuild in RGB so every output pixel is literally a film ink.
    flat = q.convert('RGB')
    px = flat.load()
    lut = {}
    out = Image.new('RGB', flat.size)
    op = out.load()
    for y in range(flat.size[1]):
        for x in range(flat.size[0]):
            c = px[x, y]
            m = lut.get(c)
            if m is None:
                # find which cluster this quantized colour is (index match is exact)
                try:
                    idx = clusters.index(c)
                except ValueError:
                    idx = min(range(len(clusters)), key=lambda i, cc=c: _dist(cc, clusters[i]))
                m = remap[idx]
                lut[c] = m
            op[x, y] = m
    # Riso misregistration (sefatlmn/halftone): the accent plate never lands exactly
    # on the ink pass — accent pixels get re-stamped a couple px down-right in a
    # paler tint, visible only where they spill onto paper.
    acc_mask = Image.new('L', out.size, 0)
    paper_mask = Image.new('L', out.size, 0)
    am, pm = acc_mask.load(), paper_mask.load()
    acc_cols = (ramp[6], ramp[7])
    for y in range(out.size[1]):
        for x in range(out.size[0]):
            c = op[x, y]
            if c in acc_cols:
                am[x, y] = 255
            elif c == ramp[0]:
                pm[x, y] = 255
    ghost = Image.new('RGB', out.size, ramp[0])
    ghost.paste(_mix(ramp[6], ramp[0], 0.4), (2, 2), acc_mask)
    out = Image.composite(ghost, out, paper_mask)
    # Close the pinholes: a 3px median keeps the poster flats clean without melting detail.
    out = out.filter(ImageFilter.MedianFilter(3))
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, optimize=True)
    h = hashlib.sha256(Path(dest).read_bytes()).hexdigest()
    return {'path': dest, 'sha256': h, 'size': {'w': out.width, 'h': out.height}}
