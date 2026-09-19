"""Illustration program -> geometry and timed state changes.

P8 authors a visual argument (form, entities, relations, program). This module
solves where every entity sits inside the aspect-native visual zone, how the
relations are drawn between them, and at which millisecond every op runs —
anchored to the spoken word that carries it. Nothing here reads wording: labels
are payload, and the brand accent is only ever spent by a state-changing op.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .contracts import (
    IllustrationDirective, IllustrationEntity, IllustrationOp, STATE_CHANGE_OPS, TreatmentError,
)
from .timing import BeatClock, EXIT_MS, LEAD_IN_MS, find_landing
from .typefit import FLOOR_FRACTION, TRACKING, _face, fit_text, measure

REGISTRY_PATH = Path(__file__).resolve().parents[2] / 'assets' / 'illustration' / 'registry.json'
# Additional licence-clean catalogues materialised by tools/build_community_registry.py; each entry is
# resolved relative to its own registry root, so pack layout never reaches into this module.
EXTRA_REGISTRIES = [Path(__file__).resolve().parents[2] / 'assets' / 'community' / 'icons-registry.json']

# Drawable aspect (w/h) of each glyph inside its cell; MEDIA takes the asset's own ratio.
GLYPH_ASPECT = {'VESSEL': 0.72, 'NODE': 1.0, 'CARD': 1.28, 'LENS': 1.0, 'CHART_LINE': 1.55, 'RING': 1.0, 'PILL': 2.8,
                'PROHIBIT': 1.0, 'BRACKET': 1.7, 'BAR': 0.46, 'ICON': 1.0}
SIZE_WEIGHT = {'hero': 1.0, 'support': 0.64, 'minor': 0.42}
ARROWED = {'flows_to', 'points_at', 'transforms_into'}
LINED = ARROWED | {'connects', 'blocks'}
ENTER_STAGGER_MS = 90
ENTER_MS = 420
CARRY_REFRAME_MS = 420
LABEL_H_FRAC = 0.13
GAP_FRAC = 0.055
# Cells joined by a drawn connector leave room for the connector itself to read as a stroke, not a tick.
CONNECTOR_GAP_FRAC = 0.16


def _box(x: float, y: float, w: float, h: float) -> Dict[str, float]:
    return {'x': round(x, 1), 'y': round(y, 1), 'w': round(max(0.0, w), 1), 'h': round(max(0.0, h), 1)}


def _overlap(a: Dict[str, float], b: Dict[str, float]) -> float:
    x = max(0.0, min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']))
    y = max(0.0, min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']))
    return x * y


def _inside(a: Dict[str, float], b: Dict[str, float], tol: float = 1.0) -> bool:
    return a['x'] >= b['x'] - tol and a['y'] >= b['y'] - tol and a['x'] + a['w'] <= b['x'] + b['w'] + tol and a['y'] + a['h'] <= b['y'] + b['h'] + tol


def _fit_aspect(cell: Dict[str, float], ar: float, scale: float = 1.0) -> Dict[str, float]:
    w = cell['w'] * scale
    h = w / ar
    if h > cell['h'] * scale:
        h = cell['h'] * scale
        w = h * ar
    return _box(cell['x'] + (cell['w'] - w) / 2, cell['y'] + (cell['h'] - h) / 2, w, h)


def _centre(b: Dict[str, float]) -> Tuple[float, float]:
    return b['x'] + b['w'] / 2, b['y'] + b['h'] / 2


_NUM = re.compile(r'-?\d*\.?\d+(?:e-?\d+)?')
_ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')
_ELEMENT = re.compile(r'<(circle|ellipse|line|rect|polyline|polygon|path)\b([^>]*)>')


def svg_art_box(svg: str) -> Dict[str, float]:
    """Fraction of the viewBox the drawn geometry actually occupies (control points count, so it is never too small).

    Artwork under a transform cannot be measured cheaply, so it reports the full viewBox."""
    m = re.search(r'viewBox="([^"]+)"', svg)
    vb = [float(v) for v in _NUM.findall(m.group(1))] if m else [0.0, 0.0, 100.0, 100.0]
    full = {'x': 0.0, 'y': 0.0, 'w': 1.0, 'h': 1.0}
    if 'transform=' in svg or len(vb) != 4 or vb[2] <= 0 or vb[3] <= 0:
        return full
    xs: List[float] = []
    ys: List[float] = []
    for tag, raw in _ELEMENT.findall(svg):
        a = dict(_ATTR.findall(raw))
        try:
            if tag == 'circle':
                cx, cy, r = float(a['cx']), float(a['cy']), float(a['r'])
                xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
            elif tag == 'ellipse':
                cx, cy, rx, ry = float(a['cx']), float(a['cy']), float(a['rx']), float(a['ry'])
                xs += [cx - rx, cx + rx]; ys += [cy - ry, cy + ry]
            elif tag == 'line':
                xs += [float(a['x1']), float(a['x2'])]; ys += [float(a['y1']), float(a['y2'])]
            elif tag == 'rect':
                x, y = float(a.get('x', 0)), float(a.get('y', 0))
                xs += [x, x + float(a['width'])]; ys += [y, y + float(a['height'])]
            elif tag in ('polyline', 'polygon'):
                pts = [float(v) for v in _NUM.findall(a['points'])]
                xs += pts[0::2]; ys += pts[1::2]
            else:
                px, py = _path_points(a['d'])
                if px is None:
                    return full
                xs += px; ys += py
        except (KeyError, ValueError):
            return full
    if not xs or not ys:
        return full
    x0, x1 = max(vb[0], min(xs)), min(vb[0] + vb[2], max(xs))
    y0, y1 = max(vb[1], min(ys)), min(vb[1] + vb[3], max(ys))
    if x1 <= x0 or y1 <= y0:
        return full
    return {'x': round((x0 - vb[0]) / vb[2], 4), 'y': round((y0 - vb[1]) / vb[3], 4), 'w': round((x1 - x0) / vb[2], 4), 'h': round((y1 - y0) / vb[3], 4)}


def _path_points(d: str) -> Tuple[Optional[List[float]], Optional[List[float]]]:
    """Absolute x/y of every coordinate in a path (arcs report their endpoints only)."""
    xs: List[float] = []
    ys: List[float] = []
    cx = cy = 0.0
    sx = sy = 0.0
    for cmd, body in re.findall(r'([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)', d):
        nums = [float(v) for v in _NUM.findall(body)]
        rel = cmd.islower()
        c = cmd.upper()
        if c == 'Z':
            cx, cy = sx, sy
            continue
        if c == 'H':
            for v in nums:
                cx = cx + v if rel else v
                xs.append(cx); ys.append(cy)
            continue
        if c == 'V':
            for v in nums:
                cy = cy + v if rel else v
                xs.append(cx); ys.append(cy)
            continue
        stride = {'M': 2, 'L': 2, 'T': 2, 'S': 4, 'Q': 4, 'C': 6, 'A': 7}[c]
        if len(nums) % stride:
            return None, None
        for i in range(0, len(nums), stride):
            seg = nums[i:i + stride]
            pts = [(seg[j], seg[j + 1]) for j in range(0, len(seg) - 1, 2)] if c != 'A' else [(seg[5], seg[6])]
            for px, py in pts:
                px, py = (cx + px, cy + py) if rel else (px, py)
                xs.append(px); ys.append(py)
            cx, cy = xs[-1], ys[-1]
            if c == 'M':
                sx, sy = cx, cy
    return xs, ys


def _art_bbox(bbox: Dict[str, float], art: Dict[str, float]) -> Dict[str, float]:
    return _box(bbox['x'] + bbox['w'] * art['x'], bbox['y'] + bbox['h'] * art['y'], bbox['w'] * art['w'], bbox['h'] * art['h'])


def _viewbox_for_art(art_bbox: Dict[str, float], art: Dict[str, float]) -> Dict[str, float]:
    w, h = art_bbox['w'] / art['w'], art_bbox['h'] / art['h']
    return _box(art_bbox['x'] - w * art['x'], art_bbox['y'] - h * art['y'], w, h)


class IllustrationRegistry:
    """Catalogue of drawable line assets P8 may reference by id. Never searched by wording here.

    Loads the authored AEV1 catalogue plus any licence-clean community catalogues listed in
    EXTRA_REGISTRIES; ids are namespaced by their file path so packs can coexist without collisions."""

    def __init__(self, path: Path = REGISTRY_PATH, extra_paths: Optional[List[Path]] = None):
        self.path = path
        self.root = path.parent
        self.items: Dict[str, Dict[str, Any]] = {}
        self._roots: Dict[str, Path] = {}
        versions: List[str] = []
        for p in [path] + list(extra_paths if extra_paths is not None else EXTRA_REGISTRIES):
            if not p.exists():
                continue
            doc = json.loads(p.read_text())
            for a in doc['assets']:
                self.items[a['id']] = a
                self._roots[a['id']] = p.parent
            versions.append(str(doc.get('version') or p.name))
        self.version = '+'.join(versions) if versions else None

    def resolve(self, ref: str, beat_id: str) -> Dict[str, Any]:
        item = self.items.get(ref)
        if not item:
            raise TreatmentError('ASSET_REF_UNKNOWN', f'{ref} is not in the illustration registry', beat_id)
        p = self._roots[ref] / item['path']
        if not p.exists():
            raise TreatmentError('ASSET_FILE_MISSING', str(p), beat_id)
        return {'id': ref, 'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'license': item['license'], 'family': item['family'],
                'art_box': svg_art_box(p.read_text())}

    def art_box(self, ref: str, beat_id: str) -> Dict[str, float]:
        return self.resolve(ref, beat_id)['art_box']


class IllustrationSolver:
    def __init__(self, aspect: str, canvas: Tuple[int, int], registry: IllustrationRegistry, media_library: Dict[str, Any], media_files: Dict[str, Any], accent: Optional[str]):
        self.aspect = aspect
        self.canvas = canvas
        self.registry = registry
        self.media_library = media_library
        self.media_files = media_files
        self.accent = accent

    # ------------------------------------------------------------------ layout
    def _cells(self, zone: Dict[str, float], ents: List[IllustrationEntity], vertical: bool, gap_frac: float = GAP_FRAC) -> Dict[str, Dict[str, float]]:
        weights = [SIZE_WEIGHT[e.size] for e in ents]
        gap = (zone['h'] if vertical else zone['w']) * gap_frac
        span = (zone['h'] if vertical else zone['w']) - gap * (len(ents) - 1)
        total = sum(weights)
        cells: Dict[str, Dict[str, float]] = {}
        cur = zone['y'] if vertical else zone['x']
        for e, wgt in zip(ents, weights):
            size = span * wgt / total
            if vertical:
                cells[e.id] = _box(zone['x'], cur, zone['w'], size)
            else:
                cells[e.id] = _box(cur, zone['y'], size, zone['h'])
            cur += size + gap
        return cells

    def _entity_ar(self, e: IllustrationEntity, beat_id: str = '') -> float:
        if e.glyph == 'MEDIA':
            a = self.media_library[e.media_ref]
            return a.width / a.height
        if e.glyph == 'ICON':
            art = self.registry.art_box(e.asset_ref, beat_id)
            return art['w'] / art['h'] if art['h'] else 1.0
        return GLYPH_ASPECT[e.glyph]

    def _place(self, e: IllustrationEntity, cell: Dict[str, float], zone: Dict[str, float], vertical: bool, beat_id: str = '') -> Tuple[Dict[str, float], Optional[Dict[str, float]]]:
        """Glyph bbox and, if labelled, a label strip under it.

        For an ICON the drawn artwork (not its viewBox padding) is what fills the cell; the returned bbox is
        the viewBox the runtime maps, so the art lands exactly where the solver measured it."""
        label_h = zone['h'] * LABEL_H_FRAC if e.label and e.glyph not in ('PILL', 'CARD') else 0.0
        body = _box(cell['x'], cell['y'], cell['w'], cell['h'] - label_h)
        scale = {'hero': 0.92, 'support': 0.78, 'minor': 0.66}[e.size]
        # Weighted cells already encode size; a hero in a row keeps its full cell, supports breathe.
        if e.glyph == 'ICON':
            # The runtime renders the icon's whole viewBox (padding included), so the viewBox — not
            # just the drawn art — must fit the cell; fitting art first lets the padding spill past it.
            ab = self.registry.art_box(e.asset_ref, beat_id)
            ar = self._entity_ar(e, beat_id)
            vb_ar = ar * (ab['h'] / ab['w']) if ab['w'] else ar
            bbox = _fit_aspect(body, vb_ar, scale)
        else:
            bbox = _fit_aspect(body, self._entity_ar(e, beat_id), scale)
        if e.glyph == 'PILL' and e.label:
            # A pill is a label carrier: it widens (up to 5:1) until its label sits at the floor size on one line.
            floor = FLOOR_FRACTION['label'] * min(self.canvas)
            need = measure(e.label, _face('label', 'SemiBold'), floor, TRACKING['label']) / 0.76 * 1.06
            w = min(max(bbox['w'], need), bbox['h'] * 5.0, body['w'])
            bbox = _box(body['x'] + (body['w'] - w) / 2, bbox['y'], w, bbox['h'])
        label = None
        if label_h:
            label = _box(cell['x'], bbox['y'] + bbox['h'] + label_h * 0.12, cell['w'], label_h * 0.8)
        return bbox, label

    def layout(self, il: IllustrationDirective, zone: Dict[str, float], beat_id: str = '') -> Tuple[List[Dict[str, Any]], List[str]]:
        failures: List[str] = []
        contained = {r.target: r.source for r in il.relations if r.type == 'contains'}
        # A lens is not given a cell of its own: it sits over whatever it scans.
        scans = {r.source: r.target for r in il.relations if r.type == 'scans'}
        lenses = {e.id for e in il.entities if e.glyph == 'LENS' and il.form == 'CALLOUT_LENS'}
        # A PROHIBIT that blocks something is worn by the target, not parked beside it.
        blocks = {r.source: r.target for r in il.relations if r.type == 'blocks'}
        prohibits = {e.id for e in il.entities if e.glyph == 'PROHIBIT' and e.id in blocks}
        top = [e for e in il.entities if e.id not in contained and e.id not in lenses and e.id not in prohibits]
        vertical = self._vertical(il, zone, len(top))
        cells: Dict[str, Dict[str, float]]
        if il.form == 'RELATIONSHIP' and len(top) >= 4:
            cells = self._hub_layout(il, top, zone)
        elif il.form == 'DATA_VISUAL':
            cells = self._data_layout(top, zone, vertical)
        else:
            order = self._order(il, top)
            top_ids = {e.id for e in top}
            lined = any(r.type in LINED and r.source in top_ids and r.target in top_ids for r in il.relations)
            cells = self._cells(zone, order, vertical, CONNECTOR_GAP_FRAC if lined else GAP_FRAC)
        placed: Dict[str, Dict[str, Any]] = {}
        for e in il.entities:
            if e.id in contained or e.id in lenses or e.id in prohibits:
                continue
            bbox, label_box = self._place(e, cells[e.id], zone, vertical, beat_id)
            placed[e.id] = self._entity_plan(e, bbox, label_box, failures, beat_id)
        for e in il.entities:
            if e.id in contained:
                host = placed[contained[e.id]]['art_bbox']
                inset = _box(host['x'] + host['w'] * 0.18, host['y'] + host['h'] * 0.18, host['w'] * 0.64, host['h'] * 0.64)
                if e.glyph == 'ICON':
                    ab = self.registry.art_box(e.asset_ref, beat_id)
                    ar = self._entity_ar(e, beat_id)
                    bbox = _fit_aspect(inset, ar * (ab['h'] / ab['w']) if ab['w'] else ar)
                else:
                    bbox = _fit_aspect(inset, self._entity_ar(e, beat_id))
                if e.glyph in ('PILL', 'CARD') and e.label:
                    # A contained label carrier still earns its floor size: widen toward the host edge before breaching.
                    floor = FLOOR_FRACTION['label'] * min(self.canvas)
                    need = measure(e.label, _face('label', 'SemiBold'), floor, TRACKING['label']) / 0.76 * 1.06
                    w = min(max(bbox['w'], need), bbox['h'] * 5.0, host['w'] * 0.84)
                    bbox = _box(inset['x'] + (inset['w'] - w) / 2, bbox['y'], w, bbox['h'])
                placed[e.id] = self._entity_plan(e, bbox, None, failures, beat_id)
                placed[e.id]['inside'] = contained[e.id]
            elif e.id in lenses:
                over_id = scans.get(e.id) or next((t.id for t in top), None)
                if over_id is None:
                    failures.append(f'LENS_WITHOUT_SUBJECT:{e.id}')
                    host = dict(zone)
                else:
                    host = dict(placed[over_id]['art_bbox'])
                    # The loupe is cut for the widest subject it will travel over.
                    for op in il.program:
                        if op.op == 'TRAVEL' and op.target == e.id:
                            for oid in op.params.get('over', []):
                                if oid in placed:
                                    host['w'] = max(host['w'], placed[oid]['art_bbox']['w'])
                                    host['h'] = max(host['h'], placed[oid]['art_bbox']['h'])
                hx, hy = _centre(placed[over_id]['art_bbox']) if over_id else _centre(host)
                if host['w'] > host['h'] * 1.5:
                    # A wide subject is framed by a loupe around it, so its label stays clear.
                    pad = host['h'] * 0.22
                    bw, bh = host['w'] + pad * 2, host['h'] + pad * 2
                else:
                    bw = bh = min(max(host['w'], host['h']) * 1.18, min(zone['w'], zone['h']))
                x = min(max(hx - bw / 2, zone['x']), zone['x'] + zone['w'] - bw)
                y = min(max(hy - bh / 2, zone['y']), zone['y'] + zone['h'] - bh)
                bbox = _box(x, y, bw, bh)
                placed[e.id] = self._entity_plan(e, bbox, None, failures, beat_id)
                placed[e.id]['over'] = over_id
        for e in il.entities:
            if e.id in prohibits:
                host = placed.get(blocks[e.id], {}).get('art_bbox')
                if host is None:
                    failures.append(f'PROHIBIT_WITHOUT_TARGET:{e.id}')
                    bbox = _fit_aspect(zone, self._entity_ar(e, beat_id), 1.0)
                else:
                    hx, hy = _centre(host)
                    d = max(host['w'], host['h']) * 1.2
                    x = min(max(hx - d / 2, zone['x']), zone['x'] + zone['w'] - d)
                    y = min(max(hy - d / 2, zone['y']), zone['y'] + zone['h'] - d)
                    bbox = _box(x, y, d, d)
                placed[e.id] = self._entity_plan(e, bbox, None, failures, beat_id)
                placed[e.id]['blocks'] = blocks[e.id]
        # A below-label has one line and cannot hyphenate, so a word that outgrows its cell borrows
        # the inter-cell gaps: it widens symmetrically, capped at the midpoint to each neighbour's
        # label centre and at the zone edges.
        labelled = [p for e in il.entities if e.id in placed for p in (placed[e.id],)
                    if p['label'] and p['label']['placement'] == 'below']
        centres = sorted((_centre(cells[e.id])[0], e.id) for e in il.entities if e.id in cells and e.id in placed)
        pad = min(self.canvas) * 0.008
        for idx, (cx, eid) in enumerate(centres):
            plan = placed[eid]
            if not plan['label'] or plan['label'].get('placement') != 'below' or plan['label']['fit']['status'] == 'FIT':
                continue
            left = zone['x'] if idx == 0 else (centres[idx - 1][0] + cx) / 2
            right = zone['x'] + zone['w'] if idx == len(centres) - 1 else (cx + centres[idx + 1][0]) / 2
            lb = plan['label']['bbox']
            lb['x'], lb['w'] = left + pad, right - left - pad * 2
            plan['label']['fit'] = asdict(fit_text(plan['label']['text'], lb, 'label', 'SemiBold', self.canvas, max_lines=1))
        for plan in labelled:
            if plan['label']['fit']['status'] != 'FIT':
                failures.append(f"ENTITY_LABEL_{plan['label']['fit']['status']}:{plan['id']}")
        ents = [placed[e.id] for e in il.entities]
        for i in range(len(ents)):
            if not _inside(ents[i]['art_bbox'], zone, 2):
                failures.append(f"ENTITY_OUTSIDE_ZONE:{ents[i]['id']}")
            for j in range(i + 1, len(ents)):
                if ents[i].get('inside') == ents[j]['id'] or ents[j].get('inside') == ents[i]['id']:
                    continue
                if ents[i].get('blocks') == ents[j]['id'] or ents[j].get('blocks') == ents[i]['id']:
                    continue  # a prohibition is worn by what it blocks
                if ents[i]['glyph'] == 'LENS' or ents[j]['glyph'] == 'LENS':
                    continue  # a lens is allowed to sit over what it inspects
                if _overlap(ents[i]['art_bbox'], ents[j]['art_bbox']) > 0.5:
                    failures.append(f"ENTITY_COLLISION:{ents[i]['id']}:{ents[j]['id']}")
        return ents, failures

    def _vertical(self, il: IllustrationDirective, zone: Dict[str, float], n: int) -> bool:
        tall = zone['h'] > zone['w'] * 1.15
        wide_glyphs = [e for e in il.entities if e.glyph in ('PILL', 'CARD')]
        if n >= 2 and len(wide_glyphs) >= n and zone['w'] < zone['h'] * 2.0:
            return True  # a row of labelled pills/cards only reads when the stage is wide enough for each label
        if il.form in ('PROCESS_PIPELINE', 'COMPARISON', 'STATE_TRANSFORMATION'):
            return tall and n >= 3 or (tall and il.form == 'PROCESS_PIPELINE')
        return tall and n >= 3

    @staticmethod
    def _order(il: IllustrationDirective, top: List[IllustrationEntity]) -> List[IllustrationEntity]:
        if il.form == 'PROCESS_PIPELINE':
            # Follow flows_to chains so the rail reads in process order.
            nxt = {r.source: r.target for r in il.relations if r.type == 'flows_to'}
            heads = [e for e in top if e.id not in nxt.values()]
            seen: List[IllustrationEntity] = []
            by_id = {e.id: e for e in top}
            for h in heads:
                cur: Optional[IllustrationEntity] = h
                while cur and cur not in seen:
                    seen.append(cur)
                    cur = by_id.get(nxt.get(cur.id, ''))
            return seen + [e for e in top if e not in seen]
        if il.form == 'RELATIONSHIP':
            degree = {e.id: 0 for e in top}
            for r in il.relations:
                degree[r.source] = degree.get(r.source, 0) + 1
                degree[r.target] = degree.get(r.target, 0) + 1
            hub = max(top, key=lambda e: (degree[e.id], e.size == 'hero'))
            others = [e for e in top if e is not hub]
            mid = len(others) // 2
            return others[:mid] + [hub] + others[mid:]
        if il.form == 'COMPARISON':
            comp = next(r for r in il.relations if r.type == 'compares')
            by_id = {e.id: e for e in top}
            first = [by_id[comp.source]] if comp.source in by_id else []
            second = [by_id[comp.target]] if comp.target in by_id else []
            return first + [e for e in top if e.id not in (comp.source, comp.target)] + second
        if il.form == 'STATE_TRANSFORMATION':
            tr = next(r for r in il.relations if r.type == 'transforms_into')
            by_id = {e.id: e for e in top}
            rest = [e for e in top if e.id not in (tr.source, tr.target)]
            return [by_id[tr.source]] + rest + [by_id[tr.target]] if tr.source in by_id and tr.target in by_id else top
        return top

    def _hub_layout(self, il: IllustrationDirective, top: List[IllustrationEntity], zone: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        degree = {e.id: 0 for e in top}
        for r in il.relations:
            degree[r.source] += 1
            degree[r.target] += 1
        hub = max(top, key=lambda e: degree[e.id])
        others = [e for e in top if e is not hub]
        cx, cy = _centre(zone)
        side = min(zone['w'], zone['h'])
        hub_size = side * 0.34
        cells = {hub.id: _box(cx - hub_size / 2, cy - hub_size / 2, hub_size, hub_size)}
        r_x, r_y = zone['w'] / 2 - side * 0.14, zone['h'] / 2 - side * 0.14
        sat = side * 0.26
        for i, e in enumerate(others):
            ang = -math.pi / 2 + i * 2 * math.pi / len(others)
            x, y = cx + math.cos(ang) * r_x, cy + math.sin(ang) * r_y
            cells[e.id] = _box(x - sat / 2, y - sat / 2, sat, sat)
        return cells

    def _data_layout(self, top: List[IllustrationEntity], zone: Dict[str, float], vertical: bool) -> Dict[str, Dict[str, float]]:
        if all(e.glyph == 'BAR' for e in top):
            return self._cells(zone, top, False)
        chart = next(e for e in top if e.glyph == 'CHART_LINE')
        others = [e for e in top if e is not chart]
        if not others:
            return {chart.id: dict(zone)}
        strip = zone['h'] * 0.22
        cells = {chart.id: _box(zone['x'], zone['y'], zone['w'], zone['h'] - strip - zone['h'] * 0.04)}
        row = _box(zone['x'], zone['y'] + zone['h'] - strip, zone['w'], strip)
        cells.update(self._cells(row, others, False))
        return cells

    def _entity_plan(self, e: IllustrationEntity, bbox: Dict[str, float], label_box: Optional[Dict[str, float]], failures: List[str], beat_id: str) -> Dict[str, Any]:
        plan: Dict[str, Any] = {'id': e.id, 'kind': e.kind, 'glyph': e.glyph, 'size': e.size, 'bbox': bbox, 'art_bbox': bbox, 'params': dict(e.params), 'label': None, 'asset': None, 'media': None}
        if e.glyph == 'ICON':
            plan['asset'] = self.registry.resolve(e.asset_ref, beat_id)
            plan['art_bbox'] = _art_bbox(bbox, plan['asset']['art_box'])
        if e.glyph == 'MEDIA':
            a = self.media_library[e.media_ref]
            nm = self.media_files.get(e.media_ref)
            plan['media'] = {'asset_id': a.asset_id, 'kind': a.kind, 'path': nm.render_path if nm else a.path, 'sha256': nm.render_sha256 if nm else None,
                             'source_size': {'w': a.width, 'h': a.height}, 'rights': a.rights, 'audio': 'MUTE',
                             'trim': ({'start': float(e.params['trim'][0]), 'end': float(e.params['trim'][1])} if e.params.get('trim') else None)}
        if e.label:
            if e.glyph in ('PILL', 'CARD'):
                inner = _box(bbox['x'] + bbox['w'] * 0.12, bbox['y'] + bbox['h'] * (0.2 if e.glyph == 'PILL' else 0.58), bbox['w'] * 0.76, bbox['h'] * (0.6 if e.glyph == 'PILL' else 0.3))
                fit = fit_text(e.label, inner, 'label', 'SemiBold', self.canvas, max_lines=1)
                plan['label'] = {'text': e.label, 'bbox': inner, 'fit': asdict(fit), 'placement': 'inside'}
            elif label_box:
                fit = fit_text(e.label, label_box, 'label', 'SemiBold', self.canvas, max_lines=1)
                plan['label'] = {'text': e.label, 'bbox': label_box, 'fit': asdict(fit), 'placement': 'below'}
            # 'below' labels are checked after the gap-borrowing pass in layout(), not here.
            if plan['label'] and plan['label']['placement'] == 'inside' and plan['label']['fit']['status'] != 'FIT':
                failures.append(f"ENTITY_LABEL_{plan['label']['fit']['status']}:{e.id}")
        return plan

    # ------------------------------------------------------------------ relations
    @staticmethod
    def connectors(il: IllustrationDirective, ents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        by_id = {e['id']: e for e in ents}
        out = []
        for r in il.relations:
            a, b = by_id[r.source]['art_bbox'], by_id[r.target]['art_bbox']
            rel = {'type': r.type, 'source': r.source, 'target': r.target, 'id': f'{r.source}->{r.target}', 'path': None, 'arrow': r.type in ARROWED, 'bar': r.type == 'blocks'}
            if r.type == 'blocks' and by_id[r.source]['glyph'] == 'PROHIBIT':
                # The overlay is the statement — no line between a ban and what it bans.
                out.append(rel)
                continue
            if r.type in LINED:
                ax, ay = _centre(a)
                bx, by = _centre(b)
                if abs(bx - ax) >= abs(by - ay):
                    sgn = 1 if bx >= ax else -1
                    p0 = (a['x'] + a['w'] if sgn > 0 else a['x'], ay)
                    p1 = (b['x'] if sgn > 0 else b['x'] + b['w'], by)
                    gap = abs(p1[0] - p0[0])
                    pad = min(14.0, gap * 0.12)
                    p0 = (p0[0] + sgn * pad, p0[1])
                    p1 = (p1[0] - sgn * pad, p1[1])
                    if abs(ay - by) > 2:
                        mid = (p0[0] + p1[0]) / 2
                        rel['path'] = [p0, (mid, ay), (mid, by), p1]
                    else:
                        rel['path'] = [p0, p1]
                else:
                    sgn = 1 if by >= ay else -1
                    p0 = (ax, a['y'] + a['h'] if sgn > 0 else a['y'])
                    p1 = (bx, b['y'] if sgn > 0 else b['y'] + b['h'])
                    gap = abs(p1[1] - p0[1])
                    pad = min(14.0, gap * 0.12)
                    p0 = (p0[0], p0[1] + sgn * pad)
                    p1 = (p1[0], p1[1] - sgn * pad)
                    if abs(ax - bx) > 2:
                        mid = (p0[1] + p1[1]) / 2
                        rel['path'] = [p0, (ax, mid), (bx, mid), p1]
                    else:
                        rel['path'] = [p0, p1]
                rel['path'] = [[round(x, 1), round(y, 1)] for x, y in rel['path']]
                rel['length'] = round(sum(math.dist(rel['path'][i], rel['path'][i + 1]) for i in range(len(rel['path']) - 1)), 1)
            elif r.type == 'compares':
                # A hairline rule between the two compared bodies.
                ax, ay = _centre(a)
                bx, by = _centre(b)
                if abs(bx - ax) >= abs(by - ay):
                    x = (a['x'] + a['w'] + b['x']) / 2 if bx > ax else (b['x'] + b['w'] + a['x']) / 2
                    y0, y1 = min(a['y'], b['y']), max(a['y'] + a['h'], b['y'] + b['h'])
                    rel['path'] = [[round(x, 1), round(y0, 1)], [round(x, 1), round(y1, 1)]]
                else:
                    y = (a['y'] + a['h'] + b['y']) / 2 if by > ay else (b['y'] + b['h'] + a['y']) / 2
                    x0, x1 = min(a['x'], b['x']), max(a['x'] + a['w'], b['x'] + b['w'])
                    rel['path'] = [[round(x0, 1), round(y, 1)], [round(x1, 1), round(y, 1)]]
                rel['length'] = round(math.dist(rel['path'][0], rel['path'][1]), 1)
                rel['rule'] = True
            out.append(rel)
        return out

    # ------------------------------------------------------------------ program
    @staticmethod
    def schedule(il: IllustrationDirective, clock: BeatClock, ents: List[Dict[str, Any]], carried_ids: set, beat_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[str]]:
        failures: List[str] = []
        latest_end = clock.duration_ms - EXIT_MS - 80
        ops: List[Dict[str, Any]] = []
        cursor = 0
        for op in il.program:
            if 'word' in op.at:
                idx = find_landing(clock.words, op.at['word'], cursor)
                if idx is None:
                    raise TreatmentError('OP_ANCHOR_WORD_NOT_IN_NARRATION', f"{op.op} {op.target} @ '{op.at['word']}'", beat_id)
                start = clock.words[idx].start_ms - 60
                cursor = idx
            elif 'unit' in op.at:
                start = clock.landings_ms[op.at['unit']]
            else:
                start = LEAD_IN_MS + op.at['offset_ms']
            start = max(LEAD_IN_MS // 2, start)
            end = start + op.duration_ms
            if end > latest_end:
                end = latest_end
                start = max(LEAD_IN_MS // 2, end - op.duration_ms)
            ops.append({'op': op.op, 'target': op.target, 'start_ms': int(start), 'end_ms': int(end), 'from': op.value_from, 'to': op.value_to,
                        'params': op.params, 'state_change': op.op in STATE_CHANGE_OPS, 'anchor': op.at})
        ops.sort(key=lambda o: (o['start_ms'], o['end_ms']))
        # Entrance: every entity is on stage before its first op, in layout order, before the first landing.
        # The stage must never stand empty while voice is already running: the first furniture always enters
        # inside the lead-in, and the rest of the scene staggers after it.
        first_land = min([l for l in clock.landings_ms] or [LEAD_IN_MS + 200])
        # The first furniture lands inside ~50ms so a cut never opens on bare paper.
        base = max(LEAD_IN_MS // 5, min(first_land - 120, LEAD_IN_MS))
        enter: Dict[str, int] = {}
        for i, e in enumerate(ents):
            if e['id'] in carried_ids:
                enter[e['id']] = 0
                continue
            t = min(base + i * ENTER_STAGGER_MS, first_land - 40)
            t = max(LEAD_IN_MS // 5, t)
            first_op = min((o['start_ms'] for o in ops if o['target'] == e['id'] or o['target'].startswith(e['id'] + '->') or o['target'].endswith('->' + e['id'])), default=None)
            if first_op is not None:
                t = min(t, first_op - 160)
            enter[e['id']] = max(LEAD_IN_MS // 5, int(t))
        for o in ops:
            if o['end_ms'] - o['start_ms'] < 120:
                failures.append(f"OP_SQUEEZED:{o['op']}:{o['target']}")
        return ops, enter, failures

    # ------------------------------------------------------------------ authored-program decoration
    @staticmethod
    def _decorate(ops: List[Dict[str, Any]], ents: List[Dict[str, Any]], rels: List[Dict[str, Any]], latest_end: int,
                  il: Optional[IllustrationDirective] = None, settled: int = 0) -> List[Dict[str, Any]]:
        """Secondary grammar the authoring layer shouldn't have to spell out: a drawn connector earns a
        tracer pass, the beat's last state change earns a confirmation ring, a multi-dot node counts
        itself in. Synthesized ops are state_change ops only where they spend the accent."""
        extra: List[Dict[str, Any]] = []
        ent_ids = {e['id'] for e in ents}
        for r in rels:
            draw = next((o for o in ops if o['target'] == r['id'] and o['op'] in ('CONNECT', 'DRAW')), None)
            if draw and not any(o['op'] == 'TRACE' and o['target'] == r['id'] for o in ops):
                st = draw['end_ms'] + 140
                dur = min(560, max(240, int(r.get('length', 300) * 0.9)))
                if st + dur <= latest_end:
                    extra.append({'op': 'TRACE', 'target': r['id'], 'start_ms': st, 'end_ms': st + dur,
                                  'from': 0.0, 'to': 1.0, 'params': {}, 'state_change': True, 'anchor': {'offset_ms': st}, 'synthesized': True})
        sc = [o for o in ops if o['state_change'] and o['target'] in ent_ids]
        if sc:
            last = max(sc, key=lambda o: o['end_ms'])
            if not any(o['op'] == 'EMIT' and o['target'] == last['target'] for o in ops):
                st = last['end_ms'] + 120
                if st + 300 <= latest_end:
                    extra.append({'op': 'EMIT', 'target': last['target'], 'start_ms': st, 'end_ms': st + 420,
                                  'from': 0.0, 'to': 0.7, 'params': {}, 'state_change': True, 'anchor': {'offset_ms': st}, 'synthesized': True})
        elif ents:
            # Even a quiet scene lands one confirmation — the dominant entity emits on its settle.
            hero = max(ents, key=lambda e: e['bbox']['w'] * e['bbox']['h'])
            st = hero['enter_ms'] + hero.get('enter_duration_ms', 0) + 120
            if st + 300 <= latest_end:
                extra.append({'op': 'EMIT', 'target': hero['id'], 'start_ms': st, 'end_ms': st + 420,
                              'from': 0.0, 'to': 0.7, 'params': {}, 'state_change': True, 'anchor': {'offset_ms': st}, 'synthesized': True})
        for e in ents:
            n = int((e.get('params') or {}).get('count') or 0)
            if n > 1 and not any(o['op'] == 'COUNT' and o['target'] == e['id'] for o in ops):
                st = e['enter_ms'] + e.get('enter_duration_ms', 0) + 100
                dur = min(160 * n, 800)
                if st + dur <= latest_end:
                    extra.append({'op': 'COUNT', 'target': e['id'], 'start_ms': st, 'end_ms': st + dur,
                                  'from': 0.0, 'to': 1.0, 'params': {}, 'state_change': True, 'anchor': {'offset_ms': st}, 'synthesized': True})
        if il is not None:
            extra += IllustrationSolver._choreograph(il, ops + extra, ents, rels, settled, latest_end)
        return extra

    # ------------------------------------------------------------------ hold choreography
    @staticmethod
    def _choreograph(il: IllustrationDirective, ops: List[Dict[str, Any]], ents: List[Dict[str, Any]],
                     rels: List[Dict[str, Any]], settled: int, latest_end: int) -> List[Dict[str, Any]]:
        """Form semantics become motion inside the hold: a pipeline sweeps its accent forward in
        process order, a relationship banks on its hub, a transformation hands ink to its result,
        a data visual singles out the biggest number. The author writes the argument; the hold
        plays it. Nothing is emitted when the authored program already does the move."""
        out: List[Dict[str, Any]] = []
        span = latest_end - settled
        if span < 500:
            return out

        def put(op: str, target: str, st: int, dur: int, frm: float, to: float, params: Optional[Dict[str, Any]] = None) -> None:
            if st + dur <= latest_end:
                out.append({'op': op, 'target': target, 'start_ms': int(st), 'end_ms': int(st + dur),
                            'from': frm, 'to': to, 'params': params or {}, 'state_change': op in STATE_CHANGE_OPS,
                            'anchor': {'offset_ms': int(st)}, 'synthesized': True})

        if il.form == 'PROCESS_PIPELINE':
            # The accent rides the entrance wave: each stage lights as it lands and hands off when
            # the next lands — process order is read the moment the chain arrives.
            order = [e['id'] for e in ents if e['glyph'] != 'LENS' and not e.get('inside')]
            n = min(len(order), 6)
            if n >= 2 and not any(o['op'] == 'INK' and o['to'] for o in ops):
                for i, eid in enumerate(order[:n]):
                    e = next(x for x in ents if x['id'] == eid)
                    t = e['enter_ms'] + e['enter_duration_ms']
                    put('INK', eid, t, 140, 0.0, 1.0)
                    if i < n - 1:
                        nx = next(x for x in ents if x['id'] == order[i + 1])
                        put('INK', eid, nx['enter_ms'], 140, 1.0, 0.0)
        elif il.form == 'RELATIONSHIP':
            degree: Dict[str, int] = {}
            for r in il.relations:
                degree[r.source] = degree.get(r.source, 0) + 1
                degree[r.target] = degree.get(r.target, 0) + 1
            if degree:
                hub = max(degree, key=degree.get)
                drawn = max((o['end_ms'] for o in ops if o['op'] in ('CONNECT', 'DRAW')), default=settled)
                if not any(o['op'] == 'INK' and o['target'] == hub and o['to'] for o in ops):
                    put('INK', hub, max(settled + 120, drawn + 160), 200, 0.0, 1.0)
        elif il.form == 'STATE_TRANSFORMATION':
            tr = next((r for r in il.relations if r.type == 'transforms_into'), None)
            if tr and not any(o['op'] == 'DIM' and o['target'] == tr.source for o in ops):
                tgt_end = max((o['end_ms'] for o in ops if o['target'] == tr.target), default=settled)
                put('DIM', tr.source, tgt_end, 260, 1.0, 0.35)
        elif il.form == 'DATA_VISUAL':
            nums = [(float((e.get('params') or {}).get('count') or (e.get('params') or {}).get('value') or 0), e['id'])
                    for e in ents if e['glyph'] not in ('LENS', 'CHART_LINE') and not e.get('inside')]
            if len(nums) >= 2:
                peak = max(nums)[1]
                if not any(o['op'] == 'INK' and o['target'] == peak and o['to'] for o in ops):
                    put('INK', peak, settled + 160, 180, 0.0, 1.0)
        elif il.form == 'CALLOUT_LENS':
            # The grammar requires authored TRAVEL; what it doesn't author is the return — a loupe
            # parked away from its scans subject at the cut reads stranded, so bring it home.
            lens = next((e for e in ents if e['glyph'] == 'LENS'), None)
            home = next((r.target for r in il.relations if r.type == 'scans'), None)
            travels = [o for o in ops if o['op'] == 'TRAVEL' and o['target'] == (lens and lens['id'])]
            last_over = travels[-1]['params'].get('over', [None])[-1] if travels else None
            if lens and home and last_over and last_over != home:
                st = travels[-1]['end_ms'] + 140
                put('TRAVEL', lens['id'], max(st, settled + 80), 480, 0.0, 1.0, {'over': [home]})
        return out

    # ------------------------------------------------------------------ entry
    def compile(self, il: IllustrationDirective, zone: Dict[str, float], clock: BeatClock, beat_id: str,
                carry_source: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
        ents, failures = self.layout(il, zone, beat_id)
        rels = self.connectors(il, ents)
        carried_ids = set(il.carry_entities) if carry_source else set()
        carry_in: Dict[str, Dict[str, float]] = {}
        if carry_source:
            prev = {e['id']: e for e in carry_source['entities']}
            for cid in il.carry_entities:
                if cid not in prev:
                    failures.append(f'CARRY_ENTITY_MISSING_IN_SOURCE_PLAN:{cid}')
                    continue
                carry_in[cid] = prev[cid]['bbox']
        ops, enter, sf = self.schedule(il, clock, ents, carried_ids, beat_id)
        failures += sf
        inherited = terminal_state(carry_source) if carry_source else {}
        for e in ents:
            e['enter_ms'] = enter[e['id']]
            e['enter_duration_ms'] = 0 if e['id'] in carried_ids else ENTER_MS
            e['carried'] = e['id'] in carried_ids
            e['carry_from_bbox'] = carry_in.get(e['id'])
            e['state_in'] = inherited.get(e['id'], {}) if e['carried'] else {}
        for r in rels:
            r['enter_ms'] = max(enter[r['source']], enter[r['target']]) + 120
            r['enter_duration_ms'] = 0 if (r['source'] in carried_ids and r['target'] in carried_ids) else 360
            r['state_in'] = inherited.get(r['id'], {}) if (r['source'] in carried_ids and r['target'] in carried_ids) else {}
            connect = next((o for o in ops if o['op'] == 'CONNECT' and o['target'] == r['id']), None)
            if connect:
                r['enter_ms'], r['enter_duration_ms'] = connect['start_ms'], connect['end_ms'] - connect['start_ms']
                r['drawn_by_op'] = True
        # The authored program settles the scene; decorations then ride the hold it opened, so
        # they join the op list after `settled` is measured rather than delaying it.
        settled = max([e['enter_ms'] + e['enter_duration_ms'] for e in ents] + [r['enter_ms'] + r['enter_duration_ms'] for r in rels] + [o['end_ms'] for o in ops] + [CARRY_REFRAME_MS if carry_in else 0])
        ops += self._decorate(ops, ents, rels, clock.duration_ms - EXIT_MS - 60, il, int(settled))
        ops.sort(key=lambda o: (o['start_ms'], o['end_ms']))
        state_changes = sum(o['state_change'] for o in ops)
        plan = {
            'form': il.form, 'zone': zone, 'entities': ents, 'relations': rels, 'ops': ops, 'settled_ms': int(settled),
            'accent': self.accent, 'accent_policy': 'STATE_CHANGE_OPS_ONLY', 'state_changes': state_changes,
            'carry_from': il.carry_from, 'persist_to': il.persist_to, 'carried': False,
            'registry_version': self.registry.version,
        }
        return plan, failures


# Which continuous property each op drives, and its rest value when no op ever touches it.
OP_PROPERTY = {'DRAW': 'draw', 'FILL': 'fill', 'INK': 'ink', 'DIM': 'dim', 'GROW': 'grow', 'STRIKE': 'strike', 'SWAP': 'swap',
               'COUNT': 'count', 'EMIT': 'emit', 'CONNECT': 'connect'}
PROPERTY_REST = {'draw': 1.0, 'fill': 0.0, 'ink': 0.0, 'dim': 1.0, 'grow': 1.0, 'strike': 0.0, 'swap': 0.0, 'count': 1.0, 'emit': 0.0, 'connect': 1.0}


def terminal_state(plan: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Where every entity and relation ends up once a beat's program has fully run: inherited state, then each op's `to`.
    The runtime applies the identical rule, so a carried entity re-enters exactly as it was left."""
    state: Dict[str, Dict[str, Any]] = {}
    for e in plan['entities']:
        state[e['id']] = dict(e.get('state_in') or {})
    for r in plan['relations']:
        state[r['id']] = dict(r.get('state_in') or {})
    for o in sorted(plan['ops'], key=lambda o: (o['start_ms'], o['end_ms'])):
        s = state.setdefault(o['target'], {})
        if o['op'] == 'TRAVEL':
            s['at'] = o['params']['over'][-1]
        elif o['op'] in OP_PROPERTY:
            s[OP_PROPERTY[o['op']]] = o['to']
    return state


def carried_copy(src: Dict[str, Any]) -> Dict[str, Any]:
    """A persisted illustration re-enters a later beat already settled: same geometry, no program."""
    out = json.loads(json.dumps(src))
    end = terminal_state(src)
    for e in out['entities']:
        e['enter_ms'], e['enter_duration_ms'], e['carried'], e['carry_from_bbox'] = 0, 0, True, None
        e['state_in'] = end.get(e['id'], {})
    for r in out['relations']:
        r['enter_ms'], r['enter_duration_ms'] = 0, 0
        r.pop('drawn_by_op', None)
        r['state_in'] = end.get(r['id'], {})
    # The program has run: its end state is baked into state_in and nothing animates.
    out['ops'] = []
    out.update({'settled_ms': 0, 'carried': True, 'state_changes': 0})
    return out
