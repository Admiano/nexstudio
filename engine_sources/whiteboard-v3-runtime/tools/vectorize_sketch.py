#!/usr/bin/env python3
"""Vectorize a raster sketch into a stroke-only SVG for assets/custom/.

Bespoke illustration pipeline:
  1. Produce line art (commissioned, hand-drawn, or AI-generated) —
     black marker lines on white, no fills, no shading.
  2. python3 tools/vectorize_sketch.py art.png --name my-concept
  3. The SVG lands in assets/custom/my-concept.svg and any scene label
     'my concept' (or ending in 'concept' via last-word match) draws it.

Requires: vtracer (pip install vtracer), Pillow.
"""
import argparse
import sys
from pathlib import Path

import vtracer
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
CUSTOM = ROOT / 'assets' / 'custom'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image', help='raster line art (png/jpg/webp)')
    ap.add_argument('--name', default=None,
                    help='slug for the scene label (default: filename)')
    ap.add_argument('--out', default=None,
                    help='output svg path (default: assets/custom/<name>.svg)')
    a = ap.parse_args()

    src = Path(a.image)
    if not src.is_file():
        print(f'no such image: {src}', file=sys.stderr)
        return 2
    name = a.name or src.stem
    name = ''.join(c if c.isalnum() else '-' for c in name.lower()).strip('-')
    out = Path(a.out) if a.out else CUSTOM / f'{name}.svg'
    out.parent.mkdir(parents=True, exist_ok=True)

    # normalize: grayscale, autocontrast, white background
    im = ImageOps.autocontrast(Image.open(src).convert('L')).convert('RGB')
    tmp = out.with_suffix('.png')
    im.save(tmp)
    vtracer.convert_image_to_svg_py(
        str(tmp), str(out),
        colormode='binary',        # line art: two colors, no fills wanted
        mode='polygon',            # outline polys -> strokes
        filter_speckle=8,          # drop dust
        color_precision=1,
        corner_threshold=40,
        length_threshold=4.0,
        splice_threshold=45,
        path_precision=3,
    )
    tmp.unlink(missing_ok=True)
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
