"""Beat alignment: the music bed and the motion share one grid.

Two things make a cut feel scored rather than underlaid. Elements arrive in a rhythm the bed
also keeps — the landing-wave stagger is a subdivision of the bed's beat, so a row of tiles pops
in eighths or sixteenths of the bar — and the bed is *phased* so its beat ticks fall on the
film's landings. The voice is never retimed for this; only the bed's start offset and the
furniture stagger move, and both are recorded in the plan so the render is reproducible.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Fractions of a beat a landing wave may step by, nearest to the finish's authored stagger.
SUBDIVISIONS: Tuple[Tuple[str, float], ...] = (('quarter', 1.0), ('triplet', 1 / 3), ('eighth', 0.5), ('sixteenth', 0.25), ('sextuplet', 1 / 6))
STAGGER_TOLERANCE = 0.35
# A landing within this of a grid tick reads as on the beat; tighter than a frame at 30fps.
ON_GRID_MS = 30.0


def groove_stagger(stagger_ms: int, bpm: Optional[int]) -> Tuple[int, Optional[str]]:
    """Snap the finish's stagger to the beat subdivision nearest it, if one lies within tolerance."""
    if not bpm:
        return stagger_ms, None
    period = 60000.0 / bpm
    best: Optional[Tuple[float, str, float]] = None
    for name, frac in SUBDIVISIONS:
        step = period * frac
        err = abs(step - stagger_ms) / stagger_ms
        if err <= STAGGER_TOLERANCE and (best is None or err < best[0]):
            best = (err, name, step)
    if best is None:
        return stagger_ms, None
    return int(round(best[2])), best[1]


def landings(beats: List[Dict[str, Any]]) -> List[int]:
    """Film-clock moments an element or a cut lands: what a listener would expect to hear on a beat."""
    out: List[int] = []
    for b in beats:
        il = b.get('illustration')
        if il and not il.get('carried'):
            for e in il['entities']:
                if not e.get('carried') and e.get('enter_duration_ms'):
                    out.append(int(b['start_ms'] + e['enter_ms'] + e['enter_duration_ms']))
            for r in il['relations']:
                if r.get('enter_duration_ms') and not r.get('stub'):
                    out.append(int(b['start_ms'] + r['enter_ms'] + r['enter_duration_ms']))
        for key in ('media', 'data'):
            d = b.get(key)
            if d and d.get('enter_duration_ms'):
                out.append(int(b['start_ms'] + d['enter_ms'] + d['enter_duration_ms']))
        tr = b.get('transition')
        if tr and tr.get('camera') and tr['end_ms'] > tr['start_ms']:
            out.append(int(b['start_ms'] + tr['start_ms']))
    return sorted(set(out))


def fit_phase(music: Dict[str, Any], beats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Choose where inside the bed playback starts so its beat grid meets the film's landings.

    Ticks are the bed's eighth-notes (`grid_offset_ms + k * period / 2` in file time); a landing at
    film time t hears file time t + start. The start offset is searched over one beat at 1ms, keeping
    the one that puts the most landings within ON_GRID_MS of a tick (ties: least total drift), so the
    bed's own intro is never skipped by more than a beat."""
    bpm = music.get('bpm')
    if not bpm or not music.get('path'):
        return {'status': 'NO_GRID', 'start_offset_ms': 0}
    period = 60000.0 / bpm
    tick = period / 2.0
    phase0 = float(music.get('grid_offset_ms') or 0) % tick
    lands = landings(beats)
    if not lands:
        return {'status': 'NO_LANDINGS', 'bpm': bpm, 'period_ms': round(period, 2), 'start_offset_ms': 0}

    def drift(t: float, start: float) -> float:
        d = (t + start - phase0) % tick
        return min(d, tick - d)

    best_start, best_key = 0, (-1, 0.0)
    for start in range(int(period)):
        ds = [drift(t, start) for t in lands]
        hits = sum(d <= ON_GRID_MS for d in ds)
        key = (hits, -sum(ds))
        if key > best_key:
            best_key, best_start = key, start
    ds = [drift(t, best_start) for t in lands]
    on = [t for t, d in zip(lands, ds) if d <= ON_GRID_MS]
    return {
        'status': 'PHASED', 'bpm': bpm, 'period_ms': round(period, 2), 'tick_ms': round(tick, 2), 'tolerance_ms': ON_GRID_MS,
        'start_offset_ms': int(best_start), 'landings': len(lands), 'on_grid': len(on), 'on_grid_ratio': round(len(on) / len(lands), 3),
        'mean_drift_ms': round(sum(ds) / len(ds), 1),
    }
