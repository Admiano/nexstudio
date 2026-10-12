"""Show grammar: the numbered-section show (today's grammar: NEWSREEL, the sectioned
data-news reel). The treatment authors `show` once — format, masthead subject, and the
shade family — and names each beat's `section`. This module resolves that into what the
compiler needs per aspect: section order, the per-beat field shade cycling through the
family, the persistent chrome band geometry, and the inner content zone the show owns.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .authorities import native_three_aspect_composition_authority_v2 as native
from .contracts import FilmTreatment

# The two persistent bands, as fractions of canvas height. The header carries the
# `NN SECTION` slug left and the subject right, split by a hairline; the footer carries
# the giant outlined section word. Content zones are remapped into the inner band
# between them, so nothing authored ever fights the chrome.
BANDS = {
    '9x16': {'header_top': 0.052, 'header_h': 0.058, 'footer_top': 0.862, 'footer_h': 0.115},
    '1x1': {'header_top': 0.052, 'header_h': 0.062, 'footer_top': 0.856, 'footer_h': 0.115},
    '16x9': {'header_top': 0.046, 'header_h': 0.082, 'footer_top': 0.812, 'footer_h': 0.148},
}


def _fr(v: float) -> float:
    return round(v, 4)


def resolve(film: FilmTreatment) -> Optional[Dict[str, Any]]:
    """Fold the authored show into per-beat assignments. Mutates the treatment beats'
    `cut` — a show plays every change of set as a hard cut — and returns the film-level
    resolved show for the plan, or None when the film is not a show."""
    show = film.show
    if not show:
        return None
    names = []
    for b in film.beats:
        if b.section and b.section not in names:
            names.append(b.section)
    idx_of = {n: i for i, n in enumerate(names)}
    shades = show['shades']
    beats: Dict[str, Dict[str, Any]] = {}
    prev_bg = None
    for i, b in enumerate(film.beats):
        b.cut = 'hard'  # the show's only transition is the hard cut
        shade = shades[i % len(shades)]
        if shade['bg'] == prev_bg and len(shades) > 1:
            shade = shades[(i + 1) % len(shades)]
        prev_bg = shade['bg']
        beats[b.beat_id] = {'idx': idx_of[b.section], 'name': b.section, 'shade': shade}
    return {'format': show['format'], 'subject': show['subject'], 'sections': names,
            'shades': shades, 'beats': beats}


def bands(aspect: str) -> Dict[str, Dict[str, float]]:
    """Chrome band boxes (canvas pixels) for one aspect."""
    W, H = native.ASPECTS[aspect]['size']
    spec = BANDS[aspect]
    header = {'x': _fr(W * 0.052), 'y': _fr(H * spec['header_top']),
              'w': _fr(W * (1 - 2 * 0.052)), 'h': _fr(H * spec['header_h'])}
    footer = {'x': _fr(W * 0.045), 'y': _fr(H * spec['footer_top']),
              'w': _fr(W * (1 - 2 * 0.045)), 'h': _fr(H * spec['footer_h'])}
    inner = {'x': header['x'], 'y': _fr(H * (spec['header_top'] + spec['header_h']) + H * 0.016),
             'w': header['w'], 'h': _fr(H * spec['footer_top'] - H * (spec['header_top'] + spec['header_h']) - H * 0.03)}
    return {'header': header, 'footer': footer, 'inner': inner}


def remap_zone(zone: Dict[str, float], safe: Dict[str, float], inner: Dict[str, float]) -> Dict[str, float]:
    """A zone authored inside the safe frame is compressed into the show's inner band,
    preserving its relative shape and position. The result is clamped inside the band:
    the show's chrome owns everything outside it."""
    fx = (zone['x'] - safe['x']) / max(1.0, safe['w'])
    fy = (zone['y'] - safe['y']) / max(1.0, safe['h'])
    x = inner['x'] + fx * inner['w']
    y = inner['y'] + fy * inner['h']
    x2 = x + zone['w'] / max(1.0, safe['w']) * inner['w']
    y2 = y + zone['h'] / max(1.0, safe['h']) * inner['h']
    x = min(max(x, inner['x']), inner['x'] + inner['w'])
    y = min(max(y, inner['y']), inner['y'] + inner['h'])
    x2 = min(max(x2, x), inner['x'] + inner['w'])
    y2 = min(max(y2, y), inner['y'] + inner['h'])
    return {'x': _fr(x), 'y': _fr(y), 'w': _fr(x2 - x), 'h': _fr(y2 - y)}
