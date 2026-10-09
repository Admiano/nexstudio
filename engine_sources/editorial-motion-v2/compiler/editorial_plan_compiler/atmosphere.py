"""Designed background: the field is a lit surface, not a flat fill.

Everything here is derived from the brand palette (ink / paper / accent) so a film's
atmosphere follows its colours — a dark paper yields the dark variant of the same
grammar, a warm paper a warm bloom — with nothing keyed to a fixture or a domain.

Film level (`film_atmosphere`): theme polarity, contrast law, vignette and grain
strengths, the bloom tint, the housing surfaces every chassis draws with, and the tints
the far-plane depth shapes are cut from.

Beat level (`beat_atmosphere`): a bloom that sits behind the beat's hero and travels
there from wherever the previous beat's bloom was, plus a few large, defocused shapes on
a far parallax plane, placed by hash away from the content so they read as room, not as
diagram parts. Every value is deterministic in (film_id, beat_id).
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Polarity: paper darker than this relative luminance is the dark variant.
DARK_THEME_MAX_LUMINANCE = 0.25
# Ink must sit at least this far from paper (WCAG contrast ratio) or the brand fails the gate.
MIN_INK_CONTRAST = 7.0

VIGNETTE = {'light': 0.10, 'dark': 0.42}      # edge darkening opacity
GRAIN = {'light': 0.045, 'dark': 0.075}       # multiply-grain opacity (dark fields hide grain; push harder)
BLOOM_OPACITY = {'light': 0.15, 'dark': 0.19}       # peak; the light reads as ambient, never a spot
DEPTH_OPACITY = {'light': 0.14, 'dark': 0.22}
DEPTH_COUNT = (2, 3)                          # far-plane shapes per beat, min..max
DEPTH_PLANE = (0.35, 0.6)                     # parallax factor range: 0 = fixed to the frame, 1 = with content
DEPTH_MAX_OVERLAP = 0.18                      # fraction of a shape allowed to sit under content
DEPTH_BLUR_FRAC = 0.028                       # blur radius as a fraction of the canvas short side
BLOOM_TRAVEL_MS = 640
BLOOM_RADIUS = (1.45, 0.44, 1.9, 0.38)            # x: max(hero.w×, W×); y: max(hero.h×, H×)


def _rgb(hex_colour: str) -> Tuple[int, int, int]:
    h = hex_colour.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(rgb: Sequence[float]) -> str:
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def mix(a: str, b: str, t: float) -> str:
    ra, rb = _rgb(a), _rgb(b)
    return _hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def hrot(hex_colour: str, degrees: float, sat_mul: float = 1.0, val_add: float = 0.0) -> str:
    """Rotate a colour's hue (and optionally scale saturation / shift value) so a film's
    palette can grow true hue families — green hills, blue water, warm light — that stay
    harmonious with the brand inks they were derived from."""
    import colorsys
    r, g, b = _rgb(hex_colour)
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h = (h + degrees / 360.0) % 1.0
    s = max(0.0, min(1.0, s * sat_mul))
    v = max(0.0, min(1.0, v + val_add))
    rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
    return _hex((rr * 255, gg * 255, bb * 255))


def luminance(hex_colour: str) -> float:
    def lin(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(hex_colour)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _warm_shift(hex_colour: str, amount: float) -> str:
    """Nudge a colour toward warm (more red, less blue) — the bloom tint for a brand with no accent."""
    r, g, b = _rgb(hex_colour)
    return _hex([r + 255 * amount * 0.35, g + 255 * amount * 0.12, b - 255 * amount * 0.3])


def film_atmosphere(brand: Dict[str, Any]) -> Dict[str, Any]:
    paper, ink, accent = brand['paper'], brand['ink'], brand.get('accent')
    theme = 'dark' if luminance(paper) <= DARK_THEME_MAX_LUMINANCE else 'light'
    bloom = mix(accent, paper, 0.35) if accent else _warm_shift(paper, 0.18)
    if theme == 'light':
        housing = {'light': mix(paper, '#ffffff', 0.9), 'dark': mix(ink, paper, 0.05)}
        shadow_rgb = [int(c * 0.7) for c in _rgb(mix(ink, '#3a2a18', 0.5))]
    else:
        housing = {'light': mix(paper, '#ffffff', 0.09), 'dark': mix(ink, paper, 0.06)}
        shadow_rgb = [0, 0, 0]
    return {
        'theme': theme,
        'field': paper,
        'vignette': '#000000' if theme == 'dark' else mix(ink, paper, 0.1),
        'vignette_opacity': VIGNETTE[theme],
        'grain_opacity': GRAIN[theme],
        'bloom': bloom,
        'bloom_opacity': BLOOM_OPACITY[theme],
        'housing': housing,
        'shadow_rgb': shadow_rgb,
        'depth_tints': [mix(paper, accent or ink, 0.22 if theme == 'light' else 0.30), mix(paper, ink, 0.10 if theme == 'light' else 0.16)],
        'depth_opacity': DEPTH_OPACITY[theme],
        'ink_contrast': round(contrast(ink, paper), 2),
    }


def brand_failures(atmo: Dict[str, Any]) -> List[str]:
    fails: List[str] = []
    if atmo['ink_contrast'] < MIN_INK_CONTRAST:
        fails.append(f"BRAND_CONTRAST:{atmo['ink_contrast']}<{MIN_INK_CONTRAST}")
    return fails


def _h(*parts: Any) -> int:
    return int(hashlib.sha256('|'.join(str(p) for p in parts).encode()).hexdigest()[:16], 16)


def _unit(seed: int, k: int) -> float:
    return ((seed >> (k * 7)) & 0x7F) / 127.0


def _overlap_frac(a: Dict[str, float], b: Dict[str, float]) -> float:
    x = max(0.0, min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']))
    y = max(0.0, min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']))
    return (x * y) / max(1.0, a['w'] * a['h'])


def _centre(b: Dict[str, float]) -> Tuple[float, float]:
    return b['x'] + b['w'] / 2, b['y'] + b['h'] / 2


def hero_box(beat: Dict[str, Any], safe: Dict[str, float]) -> Dict[str, float]:
    """Where the light belongs: the largest drawn entity, else the media/data zone, else the hero copy."""
    ill = beat.get('illustration')
    if ill and ill.get('entities'):
        return dict(max((e['bbox'] for e in ill['entities']), key=lambda b: b['w'] * b['h']))
    for key in ('media', 'data', 'figure'):
        z = (beat.get(key) or {}).get('zone')
        if z:
            return dict(z)
    heroes = [t['bbox'] for t in beat['typography']['blocks'] if t['role'] == 'hero']
    if heroes:
        return dict(heroes[0])
    return dict(safe)


def content_boxes(beat: Dict[str, Any]) -> List[Dict[str, float]]:
    boxes = [t['bbox'] for t in beat['typography']['blocks']]
    ill = beat.get('illustration')
    if ill:
        boxes += [e['bbox'] for e in ill.get('entities', [])]
    for key in ('media', 'data', 'figure'):
        z = (beat.get(key) or {}).get('zone')
        if z:
            boxes.append(z)
    return boxes


def beat_atmosphere(film_id: str, beat: Dict[str, Any], canvas: Tuple[int, int], safe: Dict[str, float],
                    prev_bloom: Optional[Dict[str, float]], atmo: Dict[str, Any]) -> List[Dict[str, Any]]:
    W, H = canvas
    short = min(W, H)
    hero = hero_box(beat, safe)
    hx, hy = _centre(hero)
    # The bloom is a wide ellipse behind the hero, slightly above its centre so the light falls down onto it.
    bloom_at = {'x': round(hx, 1), 'y': round(hy - hero['h'] * 0.12, 1)}
    layers: List[Dict[str, Any]] = [{
        'kind': 'bloom',
        'at': bloom_at,
        'from': dict(prev_bloom) if prev_bloom else dict(bloom_at),
        'travel_ms': BLOOM_TRAVEL_MS,
        'radius': {'x': round(max(hero['w'] * BLOOM_RADIUS[0], W * BLOOM_RADIUS[1]), 1),
                   'y': round(max(hero['h'] * BLOOM_RADIUS[2], H * BLOOM_RADIUS[3]), 1)},
        'opacity': 1.0,
    }]
    # Far-plane shapes: large, defocused, out of the content's way. Placed by hash, rejected if they
    # sit under content, so a busy beat gets fewer shapes and a quiet one gets its room.
    seed = _h(film_id, beat['beat_id'], 'depth')
    want = DEPTH_COUNT[0] + (seed % (DEPTH_COUNT[1] - DEPTH_COUNT[0] + 1))
    boxes = content_boxes(beat)
    placed: List[Dict[str, float]] = []
    attempts = 0
    while len(placed) < want and attempts < 24:
        s = _h(seed, attempts)
        attempts += 1
        size = short * (0.16 + 0.22 * _unit(s, 0))
        box = {'x': -size * 0.35 + (W - size * 0.3) * _unit(s, 1), 'y': -size * 0.35 + (H - size * 0.3) * _unit(s, 2), 'w': size, 'h': size}
        if any(_overlap_frac(box, c) > DEPTH_MAX_OVERLAP for c in boxes + placed):
            continue
        placed.append(box)
        layers.append({
            'kind': 'depth',
            'shape': 'disc' if _unit(s, 3) < 0.5 else 'tile',
            'bbox': {k: round(v, 1) for k, v in box.items()},
            'tint': int(_unit(s, 4) < 0.5),
            'plane': round(DEPTH_PLANE[0] + (DEPTH_PLANE[1] - DEPTH_PLANE[0]) * _unit(s, 5), 3),
            'blur_px': round(short * DEPTH_BLUR_FRAC * (0.8 + 0.5 * _unit(s, 6)), 1),
            'rotation_deg': round(-14 + 28 * _unit(s, 7), 1),
            'opacity': atmo['depth_opacity'],
        })
    return layers
