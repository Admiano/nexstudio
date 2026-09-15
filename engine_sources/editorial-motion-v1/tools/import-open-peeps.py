"""Export the Open Peeps library from a .sketch document into SVG parts.

Sketch stores geometry as normalised curve points inside nested layer frames.
This walks the tree, resolves frames into absolute coordinates, turns curve
points into cubic beziers, and flattens each shapeGroup into a single path so a
boolean subtraction reads as an even-odd hole rather than a separate shape.

The `a person/*` symbols carry the library's own slot geometry, so the part
placement used by the composer is read out of the source rather than guessed.

Usage: python3 tools/import-open-peeps.py <unzipped-sketch-dir> <assets-dir>
"""
import json
import math
import os
import re
import sys
from collections import defaultdict

PT = re.compile(r'\{\s*([-\d.e]+)\s*,\s*([-\d.e]+)\s*\}')


def pt(value):
    m = PT.match(value)
    return float(m.group(1)), float(m.group(2))


def rnd(v):
    return round(v, 2)


def color(c):
    if not c:
        return None
    r, g, b = (int(round(c[k] * 255)) for k in ('red', 'green', 'blue'))
    a = c.get('alpha', 1)
    hexc = f'#{r:02x}{g:02x}{b:02x}'
    return hexc if a >= 0.999 else (hexc, round(a, 3))


def fill_of(layer):
    style = layer.get('style') or {}
    for f in style.get('fills') or []:
        if f.get('isEnabled') and f.get('fillType', 0) == 0:
            return color(f.get('color'))
    return None


def border_of(layer):
    style = layer.get('style') or {}
    for b in style.get('borders') or []:
        if b.get('isEnabled'):
            return color(b.get('color')), b.get('thickness', 1)
    return None, 0


def opacity_of(layer):
    ctx = ((layer.get('style') or {}).get('contextSettings') or {})
    return ctx.get('opacity', 1)


def path_points(layer, ox, oy, sx, sy):
    """Curve points -> absolute cubic path data."""
    frame = layer['frame']
    w, h = frame['width'] * sx, frame['height'] * sy
    x0, y0 = ox + frame['x'] * sx, oy + frame['y'] * sy
    if layer.get('isFlippedHorizontal') or layer.get('isFlippedVertical'):
        fx = -1 if layer.get('isFlippedHorizontal') else 1
        fy = -1 if layer.get('isFlippedVertical') else 1
    else:
        fx = fy = 1

    def abs_pt(raw):
        px, py = pt(raw)
        if fx < 0:
            px = 1 - px
        if fy < 0:
            py = 1 - py
        return x0 + px * w, y0 + py * h

    pts = layer.get('points') or []
    if not pts:
        return ''
    closed = layer.get('isClosed', True)
    d = []
    start = abs_pt(pts[0]['point'])
    d.append(f'M {rnd(start[0])} {rnd(start[1])}')
    count = len(pts)
    last = count if closed else count - 1
    for i in range(last):
        a = pts[i]
        b = pts[(i + 1) % count]
        p1 = abs_pt(a['curveFrom']) if a.get('hasCurveFrom') else abs_pt(a['point'])
        p2 = abs_pt(b['curveTo']) if b.get('hasCurveTo') else abs_pt(b['point'])
        p3 = abs_pt(b['point'])
        d.append(f'C {rnd(p1[0])} {rnd(p1[1])} {rnd(p2[0])} {rnd(p2[1])} {rnd(p3[0])} {rnd(p3[1])}')
    if closed:
        d.append('Z')
    return ' '.join(d)


def oval_path(layer, ox, oy, sx, sy):
    f = layer['frame']
    x, y = ox + f['x'] * sx, oy + f['y'] * sy
    w, h = f['width'] * sx, f['height'] * sy
    rx, ry = w / 2, h / 2
    cx, cy = x + rx, y + ry
    return (f'M {rnd(cx - rx)} {rnd(cy)} a {rnd(rx)} {rnd(ry)} 0 1 0 {rnd(rx * 2)} 0 '
            f'a {rnd(rx)} {rnd(ry)} 0 1 0 {rnd(-rx * 2)} 0 Z')


def rect_path(layer, ox, oy, sx, sy):
    f = layer['frame']
    x, y = ox + f['x'] * sx, oy + f['y'] * sy
    w, h = f['width'] * sx, f['height'] * sy
    return f'M {rnd(x)} {rnd(y)} H {rnd(x + w)} V {rnd(y + h)} H {rnd(x)} Z'


def geometry(layer, ox, oy, sx, sy):
    cls = layer.get('_class')
    if cls in ('shapePath', 'polygon', 'star', 'triangle'):
        return path_points(layer, ox, oy, sx, sy)
    if cls == 'oval':
        return oval_path(layer, ox, oy, sx, sy)
    if cls == 'rectangle':
        return rect_path(layer, ox, oy, sx, sy)
    return ''


class Exporter:
    def __init__(self, masters):
        self.masters = masters

    def emit(self, layer, ox, oy, sx, sy, out, depth=0):
        if not layer.get('isVisible', True) or depth > 12:
            return
        cls = layer.get('_class')
        frame = layer.get('frame') or {'x': 0, 'y': 0, 'width': 0, 'height': 0}

        if cls in ('shapeGroup', 'group'):
            gx, gy = ox + frame['x'] * sx, oy + frame['y'] * sy
            children = layer.get('layers') or []
            if cls == 'shapeGroup':
                visible = [c for c in children if c.get('isVisible', True)]
                subpaths = [s for s in (geometry(c, gx, gy, sx, sy) for c in visible) if s]
                nested = [c for c in visible if c.get('_class') in ('shapeGroup', 'group')]
                fill = fill_of(layer) or next((fill_of(c) for c in visible if fill_of(c)), None)
                stroke, thickness = border_of(layer)
                if stroke is None:
                    stroke, thickness = border_of(visible[0]) if visible else (None, 0)
                if subpaths:
                    out.append(self.path_el(' '.join(subpaths), fill, stroke, thickness * sx, opacity_of(layer)))
                for c in nested:
                    if not (c.get('style') or {}).get('fills'):
                        c = dict(c, style={**(c.get('style') or {}), 'fills': (layer.get('style') or {}).get('fills')})
                    self.emit(c, gx, gy, sx, sy, out, depth + 1)
                return
            for c in children:
                self.emit(c, gx, gy, sx, sy, out, depth + 1)
            return

        if cls == 'symbolInstance':
            master = self.masters.get(layer.get('symbolID'))
            if not master:
                return
            mf = master['frame']
            ix, iy = ox + frame['x'] * sx, oy + frame['y'] * sy
            nsx = sx * (frame['width'] / mf['width'] if mf['width'] else 1)
            nsy = sy * (frame['height'] / mf['height'] if mf['height'] else 1)
            for c in master.get('layers') or []:
                self.emit(c, ix - mf['x'] * 0, iy - mf['y'] * 0, nsx, nsy, out, depth + 1)
            return

        d = geometry(layer, ox, oy, sx, sy)
        if not d:
            return
        stroke, thickness = border_of(layer)
        out.append(self.path_el(d, fill_of(layer), stroke, thickness * sx, opacity_of(layer)))

    @staticmethod
    def path_el(d, fill, stroke, thickness, opacity):
        attrs = [f'd="{d}"']
        fill_op = None
        if isinstance(fill, tuple):
            fill, fill_op = fill
        attrs.append(f'fill="{fill}"' if fill else 'fill="none"')
        if fill:
            attrs.append('fill-rule="evenodd"')
        if fill_op is not None:
            attrs.append(f'fill-opacity="{fill_op}"')
        if isinstance(stroke, tuple):
            stroke = stroke[0]
        if stroke and thickness:
            attrs.append(f'stroke="{stroke}" stroke-width="{rnd(thickness)}" stroke-linejoin="round" stroke-linecap="round"')
        if opacity is not None and opacity < 0.999:
            attrs.append(f'opacity="{round(opacity, 3)}"')
        return f'<path {" ".join(attrs)}/>'

    def svg(self, master):
        f = master['frame']
        out = []
        for layer in master.get('layers') or []:
            self.emit(layer, 0, 0, 1, 1, out)
        body = ''.join(out)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {rnd(f["width"])} {rnd(f["height"])}" '
                f'width="{rnd(f["width"])}" height="{rnd(f["height"])}">{body}</svg>')


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


PART_GROUPS = ('pose', 'body', 'head', 'face', 'facial-hair', 'accessories', 'mask')
SLOTS = {'BODY': 'body', 'HEAD': 'head', 'FACE': 'face', 'FACIAL HAIR': 'facial-hair',
         'MASK': 'mask', 'ACCESORIES': 'accessories'}


def read_compositions(page_layers, masters):
    """Slot rectangles for each `a person/*` arrangement, in symbol coordinates."""
    out = {}
    for master in page_layers:
        name = master.get('name') or ''
        if not name.startswith('a person/'):
            continue
        f = master['frame']
        slots = {}

        def walk(layer, ox, oy):
            fr = layer.get('frame') or {}
            x, y = ox + fr.get('x', 0), oy + fr.get('y', 0)
            if layer.get('_class') == 'symbolInstance':
                slot = SLOTS.get((layer.get('name') or '').upper())
                ref = masters.get(layer.get('symbolID'))
                if slot and ref:
                    slots[slot] = {'x': rnd(x), 'y': rnd(y),
                                   'width': rnd(fr.get('width', 0)), 'height': rnd(fr.get('height', 0)),
                                   'default': ref.get('name')}
                return
            for c in layer.get('layers') or []:
                walk(c, x, y)

        for c in master.get('layers') or []:
            walk(c, 0, 0)
        if slots:
            key = slug(name.split('/', 1)[1])
            out[key] = {'id': key, 'width': rnd(f['width']), 'height': rnd(f['height']), 'slots': slots}
    return out


def main(src, dest):
    masters = {}
    page_layers = []
    for page in sorted(os.listdir(os.path.join(src, 'pages'))):
        doc = json.load(open(os.path.join(src, 'pages', page)))
        for layer in doc.get('layers') or []:
            if layer.get('_class') == 'symbolMaster':
                masters[layer['symbolID']] = layer
                page_layers.append(layer)

    exporter = Exporter(masters)
    index = defaultdict(list)
    seen = set()
    for master in page_layers:
        name = master.get('name') or ''
        parts = name.split('/')
        if len(parts) < 2 or parts[0] not in PART_GROUPS:
            continue
        group = parts[0]
        sub = parts[1] if group == 'pose' and len(parts) > 2 else None
        label = parts[-1]
        if label.strip().lstrip('*').strip().lower() in ('none', 'no-mask', ''):
            continue
        key = slug('-'.join(parts[1:]))
        if (group, key) in seen:
            continue
        seen.add((group, key))
        svg = exporter.svg(master)
        folder = os.path.join(dest, group)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, f'{key}.svg'), 'w') as fh:
            fh.write(svg)
        f = master['frame']
        index[group].append({
            'id': key,
            'name': label,
            'group': group,
            'variant': sub,
            'file': f'{group}/{key}.svg',
            'width': rnd(f['width']),
            'height': rnd(f['height'])
        })

    payload = {
        'source': 'Open Peeps by Pablo Stanley (CC0)',
        'parts': {k: sorted(v, key=lambda p: p['id']) for k, v in sorted(index.items())},
        'compositions': read_compositions(page_layers, masters)
    }
    with open(os.path.join(dest, 'parts-index.json'), 'w') as fh:
        json.dump(payload, fh, indent=1)
    for k, v in payload['parts'].items():
        print(f'{k}: {len(v)}')
    print('compositions:', ', '.join(payload['compositions']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
