#!/usr/bin/env python3
"""OpenMoji people/activity glyph pack builder.

Reads the downloaded black (line-art) OpenMoji set + data/openmoji.json,
keeps base people/activity glyphs (skin-tone variants dropped), flattens
every element (paths AND shapes AND transforms) into straight polyline
<path> elements, and writes assets/openmoji/<slug>.svg + index.json.

License: OpenMoji is CC BY-SA 4.0 (hfg-gmuend) — attribution required.
Usage:
    python3 tools/openmoji_pack.py ~/emoji/openmoji-black ~/emoji/openmoji.json
"""
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from svg_paths import parse_path_d  # noqa: E402

GROUPS = ('people-body', 'activities')
OUT = ROOT / 'assets' / 'openmoji'
STOP = {'the', 'and', 'with', 'in', 'on', 'of', 'a', 'an', 'for', 'to'}


# --- tiny affine matrix over (x,y) -------------------------------------
def _mat_mul(a, b):
    return [a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1],
            a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3],
            a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5]]


def _parse_transform(s):
    m = [1, 0, 0, 1, 0, 0]
    if not s:
        return m
    for name, args in re.findall(r'(matrix|translate|scale|rotate|skewX|skewY)\s*\(([^)]*)\)', s):
        v = [float(x) for x in re.split(r'[,\s]+', args.strip()) if x]
        if name == 'matrix' and len(v) == 6:
            t = v
        elif name == 'translate':
            t = [1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0]
        elif name == 'scale':
            t = [v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0]
        elif name == 'rotate':
            a = math.radians(v[0]); c, si = math.cos(a), math.sin(a)
            t = [c, si, -si, c, 0.0, 0.0]
            if len(v) == 3:  # rotate about (cx,cy)
                t = _mat_mul(_mat_mul([1, 0, 0, 1, v[1], v[2]], t),
                             [1, 0, 0, 1, -v[1], -v[2]])
        elif name == 'skewX':
            t = [1, 0, math.tan(math.radians(v[0])), 1, 0, 0]
        else:
            t = [1, math.tan(math.radians(v[0])), 0, 1, 0, 0]
        m = _mat_mul(m, t)
    return m


def _apply(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def _shape_d(tag, a):
    f = lambda k, d=0.0: float(a.get(k, d))
    if tag == 'line':
        return f"M{f('x1')} {f('y1')}L{f('x2')} {f('y2')}"
    if tag == 'circle':
        cx, cy, r = f('cx'), f('cy'), f('r')
        return f"M{cx - r} {cy}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0"
    if tag == 'ellipse':
        cx, cy, rx, ry = f('cx'), f('cy'), f('rx'), f('ry')
        return f"M{cx - rx} {cy}a{rx} {ry} 0 1 0 {2 * rx} 0a{rx} {ry} 0 1 0 {-2 * rx} 0"
    if tag == 'rect':
        x, y, w, h = f('x'), f('y'), f('width'), f('height')
        return f"M{x} {y}h{w}v{h}h{-w}Z"
    if tag in ('polyline', 'polygon'):
        nums = [float(n) for n in re.split(r'[,\s]+', a.get('points', '').strip()) if n]
        pts = 'L'.join(f"{nums[i]} {nums[i + 1]}" for i in range(0, len(nums) - 1, 2))
        return f"M{pts}" + ('Z' if tag == 'polygon' else '')
    return None


def flatten_svg(path):
    """Every drawable element -> [(polyline_pts, fill, closed)] with the
    element's full transform baked in."""
    root = ET.parse(str(path)).getroot()
    out = []

    def walk(el, m):
        m = _mat_mul(m, _parse_transform(el.get('transform')))
        tag = el.tag.rsplit('}', 1)[-1]
        d = el.get('d') if tag == 'path' else _shape_d(tag, el.attrib) \
            if tag in ('circle', 'ellipse', 'line', 'rect', 'polyline',
                       'polygon') else None
        if d and re.search(r'[MLHVCSQTAZmlhvcsqtaz]', d):
            for poly in parse_path_d(d):
                if len(poly) >= 2:
                    out.append(([_apply(m, x, y) for x, y in poly],
                                el.get('fill') or 'default',
                                d.rstrip().upper().endswith('Z')))
        for ch in el:
            walk(ch, m)

    walk(root, [1, 0, 0, 1, 0, 0])
    return out


def _slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def main(src_dir, index_json):
    src = Path(src_dir)
    meta = json.loads(Path(index_json).read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    idx = {}
    used = set()
    for e in meta:
        if e['group'] not in GROUPS or e.get('skintone'):
            continue
        f = src / f"{e['hexcode']}.svg"
        if not f.is_file():
            continue
        slug = _slug(e['annotation'])
        if slug in used:
            slug = f"{slug}-{e['hexcode'].lower()}"
        used.add(slug)
        els = flatten_svg(f)
        if not els:
            continue
        parts = []
        for pts, fill, closed in els:
            fill_attr = '' if fill in ('default', None) \
                else f' fill="{fill}"'
            d = 'M' + 'L'.join(f"{x:.2f} {y:.2f}" for x, y in pts) \
                + ('Z' if closed else '')
            parts.append(f'<path d="{d}"{fill_attr}/>')
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' "
               "viewBox='0 0 72 72'>" + ''.join(parts) + '</svg>')
        (OUT / f'{slug}.svg').write_text(svg)
        toks = set(_slug(e['annotation']).split('-')) - STOP
        toks |= {t for t in re.split(r'[,\s]+', ' '.join(
            e.get('tags') or [])) if t} - STOP
        toks |= set(e.get('subgroups', '').split('-')) - STOP
        toks |= set(e['group'].split('-'))
        toks.add('emoji')
        idx[slug] = {'tokens': sorted(toks), 'annotation': e['annotation'],
                     'hexcode': e['hexcode'], 'group': e['group']}
    (OUT / 'index.json').write_text(json.dumps(idx, indent=1))
    print(f'wrote {len(idx)} glyphs -> {OUT}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
