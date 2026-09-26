"""Render world-atlas topojson into paper-dialect SVG map plates.

Emits one world map plus continent crops (same plate, tighter viewBox — the
way a picture book zooms a map). Output is a `maps` bank dir harvestable by
bank_index.py sidecar-JSON readers.
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path('/home/ubuntu/banks/world-atlas')
OUT = Path('/home/ubuntu/banks/maps')


def project(lon: float, lat: float) -> tuple:
    return (lon + 180.0) / 360.0 * 960.0, (84.0 - lat) / 168.0 * 600.0


def decode_arcs(topo: dict) -> list:
    tr = topo.get('transform') or {'scale': [1, 1], 'translate': [0, 0]}
    out = []
    for arc in topo['arcs']:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * tr['scale'][0] + tr['translate'][0], y * tr['scale'][1] + tr['translate'][1]))
        out.append(pts)
    return out


def geom_paths(geom: dict, arcs: list) -> str:
    def arc_path(idx: int) -> str:
        pts = list(reversed(arcs[~idx])) if idx < 0 else arcs[idx]
        return 'M' + 'L'.join(f'{p[0]:.1f},{p[1]:.1f}' for p in (project(lon, lat) for lon, lat in pts)) + 'Z'
    t = geom['type']
    if t == 'Polygon':
        return ''.join(''.join(arc_path(a) for a in ring) for ring in geom['arcs'])
    if t == 'MultiPolygon':
        return ''.join(''.join(arc_path(a) for a in ring) for poly in geom['arcs'] for ring in poly)
    return ''


def topo_paths(topo: dict, obj: str) -> str:
    arcs = decode_arcs(topo)
    return ''.join(geom_paths(g, arcs) for g in topo['objects'][obj]['geometries'])


# (name, viewBox x y w h) — equirectangular continent windows
CROPS = {
    'world': (0, 0, 960, 600),
    'africa': (400, 175, 320, 330),
    'europe': (435, 0, 235, 175),
    'asia': (560, 0, 400, 300),
    'north-america': (20, 15, 390, 290),
    'south-america': (210, 290, 200, 300),
    'oceania': (760, 330, 200, 260),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    countries = json.loads((SRC / 'countries-110m.json').read_text())
    land = json.loads((SRC / 'land-110m.json').read_text())
    land_d = topo_paths(land, 'land')
    border_d = topo_paths(countries, 'countries')
    for name, (vx, vy, vw, vh) in CROPS.items():
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx} {vy} {vw} {vh}">'
            f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="#e8dcc0"/>'
            f'<path d="{land_d}" fill="#c4a35a" stroke="#6b5335" stroke-width="0.8" fill-rule="evenodd"/>'
            f'<path d="{border_d}" fill="none" stroke="#8a6f45" stroke-width="0.45" fill-rule="evenodd"/>'
            f'</svg>'
        )
        (OUT / f'{name}.svg').write_text(svg)
        title = {'world': 'Map of the world', 'north-america': 'Map of North America',
                 'south-america': 'Map of South America'}.get(name, f'Map of {name.title()}')
        meta = {'id': f'maps:{name}', 'lane': 'maps', 'title': title,
                'creator': 'Natural Earth', 'license': 'PD',
                'desc': f'{title} world atlas earth continents countries geography land sea globe ' + ' '.join(name.split('-')),
                'file': f'{name}.svg', 'w': 960, 'h': 600}
        (OUT / f'{name}.json').write_text(json.dumps(meta))
    print('maps:', len(CROPS))


if __name__ == '__main__':
    main()
