"""Treatment -> EditorialPlan compiler.

Input: a ``NexStudioEditorialTreatmentV2`` document authored by NexMind P8.
Output: one ``NexStudioEditorialPlanV2`` per requested aspect, fully resolved
to pixels and milliseconds, plus a film-level gate report. The renderer
executes a plan verbatim; if the compiler cannot satisfy the treatment inside
the bounded vocabulary it fails with a coded reason for P8 to replan.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, replace
from pathlib import Path

from PIL import Image
from typing import Any, Dict, List, Optional, Tuple

from .authorities import editorial_motion_ensemble_director_v1 as ens
from .authorities import kinetic_typography_performance_authority_v3 as ktp
from .authorities import native_three_aspect_composition_authority_v2 as native
from .chassis import chassis_aspect, housing
from .contracts import MOTION_PROFILES, WORD_GLYPHS, BeatTreatment, FigureDirective, FilmTreatment, TreatmentError
from .atmosphere import beat_atmosphere, brand_failures, film_atmosphere, hrot, mix
from .figures import resolve_figure, resolve_state_parts, FigurePartError, INDEX as PEEPS_INDEX
from .groove import fit_phase, groove_stagger
from .illustration import IllustrationRegistry, IllustrationSolver, carried_copy, _fit_aspect
from .bankart import BankArt
from .papercut import papercut_image, papercut_coverage, tonal_ramp
from .evidence import PhotoEvidence
from .lexicon import AssetFinder, NounLexicon, Resolution
from .media import NormalisedMedia, normalise_media
from .motion import camera_move, transition_window_ms
from .sound import MIX, SoundLibrary, bind_beat_ambience, bind_beat_sound, bind_film_music, community_surface, library_root
from .master_timeline import MasterTimeline, extend_tail, resolve_master
from .timing import BeatClock, CASCADE_SETTLE_MS, EXIT_MS, LAND_SETTLE_MS, LEAD_IN_MS, MIN_HOLD_MS, beat_clock, find_landing, normalise, readable_close_floor, retime_choreography, window_clock
from .typefit import fit_text
from .voice import VoiceSegment, resolve_voice


def _cascade_settle_ms(finish: str) -> int:
    """Word-cascade settle budget — must equal the runtime's per-profile landing
    duration ('rise' lands a word in 300ms, 'tonal' in 260)."""
    return 300 if MOTION_PROFILES[finish]['word_landing'] == 'rise' else CASCADE_SETTLE_MS


COMPILER_VERSION = 'EDITORIAL_PLAN_COMPILER_V3.0'
PLAN_SCHEMA = 'NexStudioEditorialPlanV2'
FONTS = Path(__file__).resolve().parents[2] / 'assets' / 'fonts'

# Grammar pattern -> native composition treatment authored per aspect.
NATIVE_TREATMENT = {
    'PROGRESSIVE_HERO_BUILD': 'PROGRESSIVE_HERO_BUILD',
    'PHRASE_REPLACEMENT': 'PROGRESSIVE_HERO_BUILD',
    'HERO_SCALE_PROMOTION': 'PROGRESSIVE_HERO_BUILD',
    'HERO_TO_EVIDENCE_HANDOFF': 'HERO_TO_EVIDENCE_HANDOFF',
    'EVIDENCE_PERSISTENCE_CARRIER': 'HERO_TO_EVIDENCE_HANDOFF',
    'ANCHORED_SCREENSHOT_PROOF': 'ANCHORED_SCREENSHOT_PROOF',
    'SEQUENTIAL_SUPPORT_LIST': 'PROCESS_RAIL',
    'QUIET_SUPPORT_AFTER_HERO': 'CONTROLLED_EMPTY_SPACE',
    'CONTRAST_RECONFIGURATION': 'CONTRAST_RECONFIGURATION',
    'PROCESS_RAIL': 'PROCESS_RAIL',
    'WORD_OBJECT_BRIDGE': 'HERO_TO_EVIDENCE_HANDOFF',
    'OBJECT_LED_TRANSITION': 'HERO_TO_EVIDENCE_HANDOFF',
    'PAYOFF_LOCKUP': 'PAYOFF_LOCKUP',
    'CTA_LOCKUP': 'CTA_LOCKUP',
    'CONTROLLED_EMPTY_SPACE': 'CONTROLLED_EMPTY_SPACE',
}
SHOT_ROLE = {'TEXT': 'TEXT_LED', 'ILLUSTRATION': 'HYBRID', 'HYBRID': 'HYBRID', 'EVIDENCE': 'HYBRID', 'FIGURE': 'CHARACTER_EMPHASIS', 'DATA': 'HYBRID', 'QUIET': 'TEXT_LED'}
# Native treatments whose visual field is too small to stage a visual argument; an illustration-led beat is
# re-composed on the aspect's evidence or process field instead (still authored natively per aspect).
SMALL_FIELD_TREATMENTS = {'PROGRESSIVE_HERO_BUILD', 'CONTROLLED_EMPTY_SPACE', 'PAYOFF_LOCKUP', 'CTA_LOCKUP'}
PROCESS_FORMS = {'PROCESS_PIPELINE', 'CALLOUT_LENS'}
WORD_CASCADE_MIN_STEP_MS = 70
# Delivery sizes; authority canvases are the native authoring spaces they scale from uniformly.
OUTPUT = {'9x16': (1080, 1920), '1x1': (1080, 1080), '16x9': (1920, 1080)}
BACKGROUND_RENDER = {'SOFT_FIELD': 'SOFT_FIELD', 'GRID_FIELD': 'GRID_FIELD', 'SPOTLIGHT_STAGE': 'SPOTLIGHT_STAGE', 'CARD_STAGE': 'CARD_STAGE',
                     'DOCUMENT_STAGE': 'CARD_STAGE', 'PRODUCT_STAGE': 'CARD_STAGE', 'LAYERED_PLANE': 'CARD_STAGE'}
MAX_LINES = {'support': 2, 'label': 1}
HERO_SUPPORT_MIN_RATIO = 1.65
DESCENDER_EM = 0.24       # how far a line's descenders hang below its line box (Black sans)
# Ladder rungs a photograph of the concept outranks: anything that stops naming the thing itself.
PHOTO_BELOW = ('hypernym', 'composite', 'typographic')


def _sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _box(x: float, y: float, w: float, h: float) -> Dict[str, float]:
    return {'x': round(x, 1), 'y': round(y, 1), 'w': round(max(0.0, w), 1), 'h': round(max(0.0, h), 1)}


def _inside(a: Dict[str, float], b: Dict[str, float], tol: float = 1.0) -> bool:
    return a['x'] >= b['x'] - tol and a['y'] >= b['y'] - tol and a['x'] + a['w'] <= b['x'] + b['w'] + tol and a['y'] + a['h'] <= b['y'] + b['h'] + tol


def _background_layers(render_bg: str, authored: str, stage: Dict[str, float], safe: Dict[str, float], canvas: Tuple[int, int], beat_index: int = 0,
                       finish: str = 'EDITORIAL_FLAT') -> List[Dict[str, Any]]:
    """Structural stage furniture under the content, derived from the authored background template.

    The runtime renders these verbatim; `kind` selects the draw recipe and all geometry is absolute
    canvas coordinates so the layers land exactly under the zones they dress."""
    W, H = canvas
    st = dict(stage)
    layers: List[Dict[str, Any]] = []
    if finish == 'PRODUCT_COLLAGE':
        # Free canvas: no lifted panel, no rules. Objects float on the field; the light (bloom behind the
        # hero) and the far-plane depth shapes are added by `atmosphere.beat_atmosphere` once the beat is placed.
        return layers
    has_panel = authored in {'CARD_STAGE', 'DOCUMENT_STAGE', 'PRODUCT_STAGE', 'LAYERED_PLANE'} or render_bg in {'CARD_STAGE', 'SPOTLIGHT_STAGE'}
    if has_panel:
        layers.append({'kind': 'panel', 'bbox': _box(st['x'], st['y'], st['w'], st['h']), 'fill': 'paper_lift', 'radius_frac': 0.032,
                       'shadow': {'opacity': 0.13, 'blur_frac': 0.022, 'dy_frac': 0.013}, 'opacity': 1.0})
        layers.append({'kind': 'hairline', 'bbox': _box(st['x'] + st['w'] * 0.045, st['y'] + st['h'] * 0.045, st['w'] * 0.91, st['h'] * 0.91), 'opacity': 0.10})
    if authored == 'LAYERED_PLANE':
        layers.append({'kind': 'plane', 'bbox': _box(st['x'] + st['w'] * 0.06, st['y'] + st['h'] * 0.05, st['w'] * 0.88, st['h'] * 0.9), 'rotation_deg': -1.1, 'opacity': 0.45})
        layers.append({'kind': 'plane', 'bbox': _box(st['x'] + st['w'] * 0.11, st['y'] + st['h'] * 0.09, st['w'] * 0.78, st['h'] * 0.82), 'rotation_deg': 1.3, 'opacity': 0.3})
    if authored == 'GRID_FIELD':
        layers.append({'kind': 'dotgrid', 'bbox': _box(st['x'], st['y'], st['w'], st['h']), 'opacity': 0.5, 'spacing_frac': 0.055, 'radius_frac': 0.0022})
    elif render_bg == 'STAGE_FIELD' and not has_panel:
        # Bare field: a sparse texture inside the safe frame keeps the cut from reading empty.
        # Texture cycles per beat so successive bare-field cuts feel deliberately re-dressed.
        v = beat_index % 4
        if v == 1:
            layers.append({'kind': 'ruled', 'bbox': dict(safe), 'opacity': 0.5, 'spacing_frac': 0.075})
        elif v == 2:
            layers.append({'kind': 'wash', 'bbox': _box(st['x'], st['y'], st['w'], st['h']), 'align': 'left' if beat_index % 2 else 'right'})
        elif v == 3:
            # A tonal wash, never a free-floating arc: an unexplained curve on the field is a stray mark.
            layers.append({'kind': 'wash', 'bbox': _box(st['x'], st['y'], st['w'], st['h']), 'align': 'right' if beat_index % 2 else 'left'})
        else:
            layers.append({'kind': 'dotgrid', 'bbox': dict(safe), 'opacity': 0.32, 'spacing_frac': 0.08, 'radius_frac': 0.0018})
    if render_bg == 'SPOTLIGHT_STAGE':
        layers.append({'kind': 'spotlight', 'bbox': _box(st['x'], st['y'] + st['h'] * 0.05, st['w'], st['h']), 'radius_frac': 0.9, 'opacity': 0.5})
    if not layers:
        # SOFT_FIELD text beats still get a faint field texture so a quiet cut never reads as dead paper.
        v = beat_index % 3
        if v == 1:
            layers.append({'kind': 'ruled', 'bbox': dict(safe), 'opacity': 0.3, 'spacing_frac': 0.095})
        elif v == 2:
            layers.append({'kind': 'wash', 'bbox': dict(safe), 'align': 'center'})
        else:
            layers.append({'kind': 'dotgrid', 'bbox': dict(safe), 'opacity': 0.18, 'spacing_frac': 0.095, 'radius_frac': 0.0016})
    return layers


def _overlap(a: Dict[str, float], b: Dict[str, float]) -> float:
    x = max(0.0, min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']))
    y = max(0.0, min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']))
    return x * y


def _contain(zone: Dict[str, float], aspect_ratio: float, scale: float = 1.0, anchor: str = 'center') -> Dict[str, float]:
    w = zone['w'] * scale
    h = w / aspect_ratio
    if h > zone['h'] * scale:
        h = zone['h'] * scale
        w = h * aspect_ratio
    x = zone['x'] + (zone['w'] - w) / 2
    y = zone['y'] + (zone['h'] - h) / 2
    if anchor == 'bottom':
        y = zone['y'] + zone['h'] - h
    elif anchor == 'top':
        y = zone['y']
    return _box(x, y, w, h)


def _carve(text: Dict[str, float], visual: Dict[str, float], gap: float = 40.0) -> Dict[str, float]:
    """Shrink the text zone so it never shares pixels with an occupied visual zone."""
    if _overlap(text, visual) <= 0:
        return text
    tcx, vcx = text['x'] + text['w'] / 2, visual['x'] + visual['w'] / 2
    tcy, vcy = text['y'] + text['h'] / 2, visual['y'] + visual['h'] / 2
    horizontal = abs(vcx - tcx) / max(1.0, text['w']) >= abs(vcy - tcy) / max(1.0, text['h'])
    if horizontal and vcx >= tcx:
        return _box(text['x'], text['y'], visual['x'] - gap - text['x'], text['h'])
    if horizontal:
        nx = visual['x'] + visual['w'] + gap
        return _box(nx, text['y'], text['x'] + text['w'] - nx, text['h'])
    if vcy >= tcy:
        return _box(text['x'], text['y'], text['w'], visual['y'] - gap - text['y'])
    ny = visual['y'] + visual['h'] + gap
    return _box(text['x'], ny, text['w'], text['y'] + text['h'] - ny)


def _remap(bbox: Dict[str, float], src: Dict[str, float], dst: Dict[str, float]) -> Dict[str, float]:
    sx = dst['w'] / max(1.0, src['w'])
    sy = dst['h'] / max(1.0, src['h'])
    return _box(dst['x'] + (bbox['x'] - src['x']) * sx, dst['y'] + (bbox['y'] - src['y']) * sy, bbox['w'] * sx, bbox['h'] * sy)


# The paperbook plate crops the whole canvas to cover its slot; only the centered
# crop of the canvas is actually printed on the page. Mirrors paperbookRects +
# the per-layout slotRects in the runtime, in canvas coordinates.
def _pb_slot_crop(layout: str, W: int, H: int) -> Dict[str, float]:
    pw, ph = W * 0.38, H * 0.80
    pad = pw * 0.082
    slots = {
        'full': (pw - pad, ph * 0.86),
        'vignette': (pw, ph * 0.92),
        'portrait': (pw - pad * 0.8, ph * 0.58),
        'spot': (pw * 0.60, ph * 0.44),
        'diagonal': (pw - pad * 0.8, ph * 0.78),
        'zipped': (pw - pad * 0.8, ph * 0.505),
        'scissor': (pw - pad * 0.8, ph * 0.505),
        'series': (pw - pad, ph * 0.44),
        'half': (pw - pad * 2.15, ph * 0.46),
    }
    sw, sh = slots.get(layout, slots['half'])
    k = max(sw / W, sh / H)
    vw, vh = sw / k, sh / k
    return _box((W - vw) / 2, (H - vh) / 2, vw, vh)


def _compose_paperbook_plate(btr: 'BeatTreatment', illustration: Optional[Dict[str, Any]],
                             figure: Optional[Dict[str, Any]], W: int, H: int, dur_ms: float) -> None:
    """Recompose the beat's entities as a page illustration: bank art gets plate-scale
    mounting, marks spread into a scene, the figure stands at picture-book size —
    all inside the slot's visible canvas crop, not the word-tile zone."""
    pg = getattr(btr, 'page', None) or {}
    # A character alone on a spread stands on the paper itself (the picture-book
    # portrait page): when the script gives a figure and nothing else to draw,
    # the page becomes a paper field — wavy ink rows, a pale halo, the performer
    # at standing height — not a framed plate.
    _empty_il = not ((illustration or {}).get('entities'))
    if figure and _empty_il and (pg.get('layout') or 'half') in ('half', 'spot'):
        pg['layout'] = 'portrait'
        if getattr(btr, 'page', None) is None:
            btr.page = pg
        scene0 = getattr(btr, 'scene', None) or {}
        if str(scene0.get('setting') or '') in ('', 'abstract'):
            scene0['setting'] = 'paper'
        scene0.setdefault('mood', 'day')
        scene0.setdefault('elements', [])
        btr.scene = scene0
    vis = _pb_slot_crop(pg.get('layout') or 'half', W, H)
    # Content never prints closer than the safe frame: the slot may bleed to the
    # page edge, but figures and marks must stay inside the 24px frame.
    _fr = _box(24.0, 24.0, W - 48.0, H - 48.0)
    _ix = max(vis['x'], _fr['x']); _iy = max(vis['y'], _fr['y'])
    vis = _box(_ix, _iy, max(1.0, min(vis['x'] + vis['w'], _fr['x'] + _fr['w']) - _ix),
               max(1.0, min(vis['y'] + vis['h'], _fr['y'] + _fr['h']) - _iy))
    vx, vy = vis['x'] + vis['w'] * 0.045, vis['y'] + vis['h'] * 0.06
    vw, vh = vis['w'] * 0.91, vis['h'] * 0.88
    ents = (illustration or {}).get('entities') or []
    photos = [e for e in ents if e.get('photo') and e.get('art_bbox')]
    marks = [e for e in ents if e.get('art_bbox') and e not in photos]

    # Authored density: a picture-book plate needs ~3 subjects to read as a scene, not
    # a spot check. When the script supplies too few, the compiler restocks it from the
    # scene's own vocabulary — night grows stars, soil grows flowers — seeded per beat so
    # the same page always grows the same life. Supports are marks, never photos.
    scene = getattr(btr, 'scene', None) or {}
    setting = str(scene.get('setting') or 'outdoor')
    _SUPPORT_POOLS = {
        'space':      ['star', 'stars', 'moon-crescent', 'star', 'earth'],
        'underwater': ['fish', 'wave', 'drop', 'fish'],
        'indoor':     ['window', 'book', 'plant', 'cup', 'candle'],
        'urban':      ['cloud', 'bird', 'star', 'kite'],
        'ground':     ['mushroom', 'flower', 'leaf', 'butterfly'],
        'abstract':   ['star', 'leaf', 'drop', 'heart'],
        'outdoor':    ['butterfly', 'flower', 'bird', 'cloud', 'leaf', 'mushroom'],
    }
    pool = list(_SUPPORT_POOLS.get(setting, _SUPPORT_POOLS['outdoor']))
    mood = str(scene.get('mood') or '')
    if mood in ('night', 'dusk', 'dawn') and setting not in ('ground', 'indoor', 'underwater'):
        pool = [c for c in ('star', 'stars', 'moon-crescent') if c not in {e.get('concept') for e in ents}] + pool
    present = {e.get('concept') for e in ents}
    subjects = len(photos) + len(marks) + (1 if figure else 0)
    if not photos and subjects < 3:
        rng = random.Random(f"{getattr(btr, 'beat_id', 'beat')}:support")
        if illustration is None:
            # Figure walks into an otherwise empty plate: the spread still needs a scene,
            # so the composer fabricates the minimal illustration the runtime can mount.
            zx, zy = max(vis['x'], 24.0), max(vis['y'], 24.0)
            zf = _box(zx, zy, max(1.0, min(vis['x'] + vis['w'], W - 24.0) - zx), max(1.0, min(vis['y'] + vis['h'], H - 24.0) - zy))
            illustration = {'form': 'SCENE', 'zone': zf, 'entities': [], 'relations': [],
                            'ops': [], 'marks': [], 'settled_ms': 0, 'accent': None,
                            'accent_policy': 'STATE_CHANGE_OPS_ONLY', 'state_changes': 0,
                            'carry_from': None, 'persist_to': None, 'carried': False,
                            'registry_version': 'supports'}
            ents = illustration['entities']
        wanted = min(2, 3 - subjects)
        added = 0
        for concept in pool:
            if added >= wanted:
                break
            if concept in present:
                continue
            size = 110 + rng.random() * 60
            e = {'id': f"support_{concept}_{added}", 'concept': concept, 'kind': 'object',
                 'glyph': 'ICON', 'size': 'support', 'label': None, 'media': None, 'photo': None,
                 'asset': None, 'carried': False, 'carry_from_bbox': None, 'state_in': {},
                 'enter_ms': int(60 + rng.random() * 120), 'enter_duration_ms': 420,
                 'bbox': _box(0, 0, size, size), 'art_bbox': _box(0, 0, size, size),
                 'params': {'resolution': {'via': 'support', 'concept': concept}}}
            illustration['entities'].append(e)
            marks.append(e)
            present.add(concept)
            added += 1

    def put(e: Dict[str, Any], box: Dict[str, float]) -> None:
        e['art_bbox'] = dict(box)
        if e.get('bbox'):
            e['bbox'] = dict(box)
        if e.get('label') and e['label'].get('bbox'):
            lb = e['label']['bbox']
            e['label']['bbox'] = _box(box['x'], box['y'] + box['h'] + lb['h'] * 0.15, box['w'], lb['h'])

    # Bank art is the plate's artwork, not a chip: single piece hangs centered like a
    # mounted plate; a series lands as a gallery (row, hero + stack, or a grid).
    n = len(photos)
    if n == 1:
        cells = [_box(vx + vw * 0.10, vy + vh * 0.06, vw * 0.80, vh * 0.86)]
    elif n == 2:
        g = vw * 0.06
        cw = (vw - g) / 2
        cells = [_box(vx + i * (cw + g), vy + vh * 0.14, cw, vh * 0.72) for i in range(2)]
    elif n == 3:
        g = vw * 0.05
        cw = (vw - 2 * g) / 3
        cells = [_box(vx + i * (cw + g), vy + vh * 0.20, cw, vh * 0.62) for i in range(3)]
    else:
        g = vw * 0.05
        cw, ch = (vw - g) / 2, (vh * 0.94 - g) / 2
        cells = [_box(vx + (i % 2) * (cw + g), vy + (i // 2) * (ch + g), cw, ch) for i in range(min(n, 4))]
    for e, cell in zip(photos, cells):
        sz = (e.get('photo') or {}).get('source_size') or {}
        ab = e['art_bbox']
        ar = (sz['w'] / sz['h']) if sz.get('w') and sz.get('h') else (ab['w'] / ab['h'] if ab['h'] else 1.0)
        put(e, _fit_aspect(cell, ar))

    # The performer is a storybook character: stands at least ~40% of plate height,
    # feet near the plate floor, shifted to whichever flank the artwork leaves open.
    # On portrait pages the figure is the page — nearer three-quarters of its field.
    if figure and figure.get('bbox'):
        fb = dict(figure['bbox'])
        fig_frac = 0.78 if (pg.get('layout') == 'portrait') else 0.40
        # Scale toward the target share of the visible field — down as well as up —
        # and never wider than the field itself.
        f = (vh * fig_frac) / max(1.0, fb['h'])
        f = min(f, (vw * 0.92) / max(1.0, fb['w']))
        f = max(0.05, f)
        nw, nh = fb['w'] * f, fb['h'] * f
        bottom = min(fb['y'] + fb['h'], vy + vh)
        cx = fb['x'] + fb['w'] / 2
        candidates = [cx - nw / 2] + [vx + vw * p - nw / 2 for p in (0.14, 0.86, 0.32, 0.68, 0.50)]
        trial = None
        for cand in candidates:
            cand = min(max(cand, vx), vx + vw - nw)
            trial = _box(cand, bottom - nh, nw, nh)
            if all(_overlap(trial, e['art_bbox']) <= 0 for e in photos):
                break
        figure['bbox'] = trial
        fb = trial

    # Marks compose the scene itself when there is no bank art: the biggest subject
    # anchors center-low, satellites spread across thirds like a staged diorama. With
    # artwork mounted they stay as small accents clamped inside the crop.
    if marks and not photos and pg.get('layout') == 'series':
        # The picture-book sequence page: one framed panel per subject across the
        # plate — phases of a moon, steps of a process — gutters between, prose below.
        order = sorted(marks, key=lambda e: -e['art_bbox']['w'] * e['art_bbox']['h'])
        n_cells = max(2, min(5, len(order)))
        cw = vw / n_cells
        for i, e in enumerate(order):
            cell_no = min(i, n_cells - 1)
            share = 1.0 if i < n_cells else 0.6
            offx = 0.0 if i < n_cells else cw * 0.34
            offy = 0.0 if i < n_cells else vh * 0.30
            ab = e['art_bbox']
            ar = ab['w'] / ab['h'] if ab['h'] else 1.0
            cell = _box(vx + cell_no * cw + cw * 0.07 + offx, vy + vh * 0.10 + offy,
                        cw * 0.86 * share, vh * 0.72 * share)
            put(e, _fit_aspect(cell, ar))
    elif marks and not photos:
        order = sorted(marks, key=lambda e: -e['art_bbox']['w'] * e['art_bbox']['h'])
        # Focal hierarchy: the largest subject is the hero — dominant, biased to a
        # lower-left/thirds anchor; satellites recede around it on a spiral of thirds.
        anchors = [(0.46, 0.58, 0.64), (0.22, 0.36, 0.30), (0.78, 0.33, 0.28),
                   (0.16, 0.72, 0.22), (0.84, 0.70, 0.20), (0.52, 0.18, 0.18)]
        for i, e in enumerate(order):
            ax, ay, hf = anchors[i % len(anchors)]
            ab = e['art_bbox']
            # Synthesised supports are garnish, not the subject — they stay small
            # so an authored hero never loses the plate to a decoration.
            if (e.get('params') or {}).get('resolution', {}).get('via') == 'support':
                hf = min(hf, 0.36)
            s = min(3.2, (vh * hf) / max(1.0, ab['h']))
            nw2, nh2 = ab['w'] * s, ab['h'] * s
            box = _box(vx + ax * vw - nw2 / 2, vy + ay * vh - nh2 / 2, nw2, nh2)
            for _ in range(4):
                if figure and _overlap(box, figure['bbox']) > 0:
                    box['x'] += vw * 0.20
                    if box['x'] + box['w'] > vx + vw:
                        box['x'] = vx
                else:
                    break
            box['x'] = min(max(box['x'], vx), vx + vw - box['w'])
            box['y'] = min(max(box['y'], vy), vy + vh - box['h'])
            put(e, box)
    elif marks:
        # Photographic plate: art marks step back to small accents strung across
        # the frame's lower band, kept off the figure.
        acc = sorted(marks, key=lambda e: -e['art_bbox']['w'] * e['art_bbox']['h'])
        n_acc = len(acc)
        for i, e in enumerate(acc):
            ab = e['art_bbox']
            s = min(1.4, (vh * 0.24) / max(1.0, ab['h']))
            box = _box(0, 0, ab['w'] * s, ab['h'] * s)
            t = (i + 1) / (n_acc + 1)
            box['x'] = vx + vw * t - box['w'] / 2
            box['y'] = vy + vh * 0.72 - box['h'] / 2
            for _ in range(4):
                if figure and _overlap(box, figure['bbox']) > 0:
                    box['y'] = vy + vh * 0.08 if box['y'] > vy + vh * 0.4 else vy + vh - box['h'] - vh * 0.04
                    box['x'] += vw * 0.18
                    box['x'] = min(max(box['x'], vx), vx + vw - box['w'])
                else:
                    break
            put(e, box)

    # Last resort de-overlap: a mark still touching the performer after the anchors
    # (narrow aspects crowd the crop) is walked to a free top-edge slot, shrinking as
    # it goes; a support that cannot clear is simply dropped — it was a garnish.
    if figure:
        fb = figure['bbox']
        for e in list(marks):
            b2 = e['art_bbox']
            if _overlap(b2, fb) <= 0:
                continue
            placed = False
            for sc2 in (1.0, 0.7, 0.5):
                w2, h2 = b2['w'] * sc2, b2['h'] * sc2
                for px in (0.06, 0.94, 0.25, 0.75, 0.5):
                    cand = _box(vx + px * vw - w2 / 2, vy + vh * 0.02, w2, h2)
                    if cand['x'] < vx - 1 or cand['x'] + cand['w'] > vx + vw + 1:
                        continue
                    if _overlap(cand, fb) <= 0 and all(_overlap(cand, m['art_bbox']) <= 0 for m in marks if m is not e):
                        put(e, cand)
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                for lst in (ents, marks):
                    if e in lst:
                        lst.remove(e)
                illustration['entities'] = [x for x in illustration['entities'] if x is not e]

    # A plate is a settled illustration: every element has arrived by the page's
    # first half — no subject may pop in during the last third of the read.
    for e in ents:
        if e.get('enter_ms', 0) > dur_ms * 0.62:
            e['enter_ms'] = int(dur_ms * 0.62)
    return illustration


def _fonts() -> Dict[str, Any]:
    files = {'display': 'InterVariable.woff2', 'display_italic': 'InterVariable-Italic.woff2', 'data': 'JetBrainsMono-SemiBold.ttf'}
    return {k: {'file': f, 'sha256': _sha_file(FONTS / f)} for k, f in files.items()} | {
        'licenses': ['INTER-LICENSE-OFL.txt', 'JETBRAINS-MONO-LICENSE-APACHE2.txt'], 'families': {'display': 'Inter Display', 'text': 'Inter', 'data': 'JetBrains Mono'}}


class BeatCompiler:
    def __init__(self, film: FilmTreatment, aspect: str, lib: Optional[SoundLibrary], media: Optional[Dict[str, NormalisedMedia]] = None,
                 stagger_ms: Optional[int] = None):
        self.film = film
        self.aspect = aspect
        self.lib = lib
        self.media_files: Dict[str, NormalisedMedia] = media or {}
        self.W, self.H = native.ASPECTS[aspect]['size']
        sx, sy, sx2, sy2 = native.ASPECTS[aspect]['safe']
        self.safe = _box(sx, sy, sx2 - sx, sy2 - sy)
        # Evidence and figures may use the field beyond the caption-safe text frame, but never clip the canvas.
        self.frame = _box(24, 24, self.W - 48, self.H - 48)
        self.hero_max_lines = native.ASPECTS[aspect]['hero_max_lines']
        self.prev_motif: Optional[str] = None
        self.carried_media: Optional[Dict[str, Any]] = None  # media persisting from an earlier beat
        self.carried_illustration: Optional[Dict[str, Any]] = None  # illustration persisting from an earlier beat
        self.illustrations: Dict[str, Dict[str, Any]] = {}  # beat_id -> compiled illustration (carry-over source)
        self.solver = IllustrationSolver(aspect, (self.W, self.H), IllustrationRegistry(), film.media_library, self.media_files, film.brand.accent,
                                         collage=film.brand.finish == 'PRODUCT_COLLAGE',
                                         stagger_ms=stagger_ms or MOTION_PROFILES[film.brand.finish]['stagger_ms'], motion=MOTION_PROFILES[film.brand.finish])

    # ------------------------------------------------------------------ helpers
    def _native_treatment(self, b: BeatTreatment) -> str:
        t = NATIVE_TREATMENT[b.pattern]
        il = b.illustration
        if self.film.brand.finish == 'PRODUCT_COLLAGE':
            has_visual = bool(il or b.media or b.data or b.figure or self.carried_illustration or self.carried_media)
            return 'COLLAGE_STAGE' if has_visual else 'COLLAGE_LOCKUP'
        if il is None and not self.carried_illustration:
            return t
        if il is not None and il.form in PROCESS_FORMS:
            return 'PROCESS_RAIL'
        if t in SMALL_FIELD_TREATMENTS or self.carried_illustration:
            return 'HERO_TO_EVIDENCE_HANDOFF' if b.dominant_layer in ('ILLUSTRATION', 'HYBRID') or self.carried_illustration else t
        return t

    @staticmethod
    def _text_share(b: BeatTreatment) -> float:
        """How much of the stacked stage the copy needs: grows with hero count and word load, shrinks for illustration-led beats."""
        heroes = sum(u.role == 'hero' for u in b.units)
        words = sum(len(u.text.split()) for u in b.units)
        share = 0.34 + 0.09 * max(0, heroes - 1) + 0.012 * max(0, words - 4)
        if b.dominant_layer == 'ILLUSTRATION':
            share -= 0.04
        return max(0.28, min(0.5, share))

    def _visual_kind(self, b: BeatTreatment) -> str:
        if b.illustration:
            return 'PROCESS_RAIL' if b.illustration.form in PROCESS_FORMS else 'EVIDENCE_CARD'
        if b.media:
            kind = self.film.media_library[b.media.asset_id].kind
            return {'SCREENSHOT': 'SCREENSHOT', 'DOCUMENT': 'DOCUMENT', 'IMAGE': 'EVIDENCE_CARD', 'VIDEO': 'EVIDENCE_CARD'}[kind]
        if b.figure:
            return 'HUMAN'
        if b.data:
            return 'EVIDENCE_CARD' if b.data.kind != 'SEQUENCE' else 'PROCESS_RAIL'
        return 'NONE'

    def _typography(self, b: BeatTreatment, clock: BeatClock, comp: Dict[str, Any], object_present: bool, shot_role: str) -> Tuple[Dict[str, Any], List[str], List[str]]:
        failures: List[str] = []
        warnings: List[str] = []
        units = [u.ktp_unit() for u in b.units]
        if not units:
            return {'motif': None, 'blocks': [], 'events': [], 'performance_events': [], 'transition_carrier': None, 'reading_order': [], 'focal_order': []}, failures, warnings
        perf = ktp.compile_performance(b.beat_type, self.aspect, clock.duration_ms, units, shot_role=shot_role, object_present=object_present,
                                       prev_motif=self.prev_motif, energy=b.energy, complexity=b.complexity)
        self.prev_motif = perf['motif']
        text_load = ktp.clamp(sum(ktp.token_count(u['text']) for u in units) / 28, .15, 1)
        ktp_zone = ktp._zones(self.aspect, shot_role, object_present, text_load).text_zone
        native_zone = comp['text_zone']
        blocks: List[Dict[str, Any]] = []
        grown: List[int] = []
        for blk in perf['text_blocks']:
            bbox = _remap(blk['bbox'], ktp_zone, native_zone)
            # Edge-crop heroes may reach the safe edge but never leave the safe frame.
            bbox['x'] = max(self.safe['x'], bbox['x'])
            bbox['w'] = min(bbox['w'], self.safe['x'] + self.safe['w'] - bbox['x'])
            max_lines = self.hero_max_lines if blk['role'] == 'hero' else MAX_LINES[blk['role']]
            stress = b.units[blk['unit_index']].stress
            fit = fit_text(blk['text'], bbox, blk['role'], blk['weight'], (self.W, self.H), max_lines=max_lines, stress=stress)
            if fit.status == 'FLOOR_BREACH':
                # The authority's proportional box is a starting point; the legibility floor is the law. Grow the
                # box to the floor requirement inside the text zone and let the collision gate judge the result.
                bbox = _grow(bbox, fit.width_px * 1.04, fit.height_px * 1.06, native_zone, self.safe)
                fit = fit_text(blk['text'], bbox, blk['role'], blk['weight'], (self.W, self.H), max_lines=max_lines, stress=stress)
                grown.append(len(blocks))
            blocks.append({**blk, 'bbox': bbox, 'fit': asdict(fit)})
        def _others(k: int) -> List[Dict[str, float]]:
            rg = b.units[blocks[k]['unit_index']].replace_group
            return [bl['bbox'] for j, bl in enumerate(blocks) if j != k and not (rg and b.units[bl['unit_index']].replace_group == rg)]
        for gi in grown:
            blocks[gi]['bbox'] = _nudge_clear(blocks[gi]['bbox'], _others(gi), native_zone)
            # If the grown block has nowhere to go, the neighbour it hits may have the slack instead.
            for j, bl in enumerate(blocks):
                if j != gi and _overlap(bl['bbox'], blocks[gi]['bbox']) > 0:
                    blocks[j]['bbox'] = _nudge_clear(bl['bbox'], _others(j), native_zone)
        self._stack_in_narration_order(b, blocks)
        if comp.get('typography_hints', {}).get('text_align') == 'center':
            # Centred lockup: every block sits on the zone's vertical axis and sets its lines centred.
            lo = max(native_zone['x'], self.safe['x'])
            hi = min(native_zone['x'] + native_zone['w'], self.safe['x'] + self.safe['w'])
            for bl in blocks:
                bl['alignment'] = 'center'
                w = min(bl['bbox']['w'], hi - lo)
                bl['bbox'] = _box((lo + hi - w) / 2, bl['bbox']['y'], w, bl['bbox']['h'])
        hero_px = max((bl['fit']['font_px'] for bl in blocks if bl['role'] == 'hero'), default=0.0)
        for bl in blocks:
            f = bl['fit']
            if bl['role'] == 'support' and hero_px and f['font_px'] > hero_px / HERO_SUPPORT_MIN_RATIO:
                refit = fit_text(bl['text'], {**bl['bbox'], 'h': hero_px / HERO_SUPPORT_MIN_RATIO * f['line_height'] * len(f['lines'])}, 'support', bl['weight'], (self.W, self.H), max_lines=MAX_LINES['support'], stress=b.units[bl['unit_index']].stress)
                bl['fit'] = asdict(refit)
                f = bl['fit']
            if f['status'] == 'WORD_TOO_WIDE':
                failures.append(f"TYPE_WORD_TOO_WIDE:{bl['unit_index']}")
            elif f['status'] == 'FLOOR_BREACH':
                failures.append(f"TYPE_FLOOR_BREACH:{bl['unit_index']}")
            if not _inside(bl['bbox'], self.safe):
                failures.append(f"TEXT_OUTSIDE_SAFE:{bl['unit_index']}")
        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                ui, uj = b.units[blocks[i]['unit_index']], b.units[blocks[j]['unit_index']]
                if ui.replace_group and ui.replace_group == uj.replace_group:
                    continue
                if _overlap(blocks[i]['bbox'], blocks[j]['bbox']) > 0:
                    failures.append(f"TEXT_COLLISION:{blocks[i]['unit_index']}:{blocks[j]['unit_index']}")
        events = retime_choreography(perf['choreography']['base']['events'], clock.landings_ms, clock.duration_ms, clock.exit_ms)
        events = self._resolve_replacements(b, blocks, events, clock)
        events = self._reveal_orphans(b, blocks, events, clock)
        # Performance events follow their unit's retimed reveal.
        reveal_start = {e['unit_index']: e['start_ms'] for e in reversed(events) if e['unit_index'] >= 0}
        perf_events = []
        for pe in perf['choreography']['performance_events']:
            shift = 0
            if pe['unit_index'] >= 0 and pe['unit_index'] in reveal_start:
                base = next((e for e in perf['choreography']['base']['events'] if e['unit_index'] == pe['unit_index']), None)
                shift = reveal_start[pe['unit_index']] - (base['start_ms'] if base else pe['start_ms'])
            perf_events.append({**pe, 'start_ms': max(0, pe['start_ms'] + shift), 'end_ms': min(clock.duration_ms, pe['end_ms'] + shift)})
        warnings += [w for w in perf['warnings'] if not w.startswith('TEXT_BLOCK_COLLISION')]
        if not perf['pass_gate'] and not failures:
            failures.append('TYPOGRAPHY_AUTHORITY_GATE_FAIL')
        self._word_cascade(b, blocks, events, clock)
        typ = {
            'motif': perf['motif'], 'spatial_preset': perf['spatial_preset'], 'blocks': blocks, 'events': events, 'performance_events': perf_events,
            'reveal_mode': self.film.typography.reveal, 'tonal_ink': self.film.typography.tonal_ink,
            'transition_carrier': perf['transition_carrier'], 'reading_order': perf['reading_order'], 'focal_order': perf['focal_order'], 'metrics': perf['metrics'],
        }
        return typ, failures, warnings

    @staticmethod
    def _stack_in_narration_order(b: BeatTreatment, blocks: List[Dict[str, Any]]) -> None:
        """Blocks that share a column read top-down in the order the voice says them.

        The authority sizes the hero and its supports; it does not know which unit is spoken
        first. The vertical slots it chose are kept (top edge and gaps) and refilled by unit
        order, so a lead-in never sits under the phrase it introduces. Replace-group stages
        share one slot and are left alone."""
        idx = [k for k, bl in enumerate(blocks) if not b.units[bl['unit_index']].replace_group]
        if len(idx) < 2:
            return
        def _same_column(a: Dict[str, float], c: Dict[str, float]) -> bool:
            return min(a['x'] + a['w'], c['x'] + c['w']) - max(a['x'], c['x']) > min(a['w'], c['w']) * 0.5
        if not all(_same_column(blocks[i]['bbox'], blocks[j]['bbox']) for i in idx for j in idx if i < j):
            return
        by_y = sorted(idx, key=lambda k: blocks[k]['bbox']['y'])
        by_unit = sorted(idx, key=lambda k: blocks[k]['unit_index'])
        if by_y == by_unit:
            return
        gaps = sorted((blocks[by_y[i + 1]]['bbox']['y'] - (blocks[by_y[i]]['bbox']['y'] + blocks[by_y[i]]['bbox']['h']) for i in range(len(by_y) - 1)), reverse=True)
        # The widest gap the authority drew goes under the hero, whose descenders reach below
        # its box; the next to the pair above it; the tight ones stay between supports.
        pairs = list(range(len(by_unit) - 1))
        def need(i: int) -> int:
            upper, lower = blocks[by_unit[i]]['role'], blocks[by_unit[i + 1]]['role']
            return 0 if upper == 'hero' else 1 if lower == 'hero' else 2
        order = sorted(pairs, key=lambda i: (need(i), i))
        gap_at = {i: gaps[n] for n, i in enumerate(order)}
        y = blocks[by_y[0]]['bbox']['y']
        for i, k in enumerate(by_unit):
            blocks[k]['bbox'] = {**blocks[k]['bbox'], 'y': round(y, 1)}
            # A block's box ends at its last baseline's line box; the descenders hang below it.
            y += blocks[k]['bbox']['h'] + max(gap_at.get(i, 0.0), DESCENDER_EM * blocks[k]['fit']['font_px'] if i < len(by_unit) - 1 else 0.0)

    def _word_cascade(self, b: BeatTreatment, blocks: List[Dict[str, Any]], events: List[Dict[str, Any]], clock: BeatClock) -> None:
        """Per-word landing times for every block: a word arrives when the voice says it.

        Words are matched sequentially from the unit's landing word; words the voice does not
        say (display copy is authored, not transcribed) are spread evenly across the gap to the
        next spoken word. Stressed words are flagged for full-ink weight; the rest read tonal
        until the unit is complete."""
        reveal_start = {e['unit_index']: e['start_ms'] for e in reversed(events) if e['unit_index'] >= 0 and e['event'] not in ('HOLD', 'EXIT')}
        for bl in blocks:
            i = bl['unit_index']
            unit = b.units[i]
            mode = unit.reveal or self.film.typography.reveal
            bl['reveal'] = mode
            stress = {normalise(w) for w in unit.stress}
            muted = {normalise(w) for w in unit.mute}
            tokens = [t for line in bl['fit']['lines'] for t in line.split()]
            line_of = [li for li, line in enumerate(bl['fit']['lines']) for _ in line.split()]
            start = reveal_start.get(i, clock.landings_ms[i])
            times: List[Optional[int]] = [None] * len(tokens)
            if clock.landing_source[i] == 'WORD' and clock.words:
                cursor = max(0, find_landing(clock.words, unit.anchor_word or tokens[0], 0) or 0)
                for k, tok in enumerate(tokens):
                    idx = find_landing(clock.words, tok, cursor)
                    if idx is not None and idx >= cursor and (idx - cursor) <= 3:
                        times[k] = clock.words[idx].start_ms
                        cursor = idx + 1
            # Fill unmatched words evenly between their spoken neighbours.
            if times and times[0] is None:
                times[0] = start
            k = 0
            while k < len(times):
                if times[k] is not None:
                    k += 1
                    continue
                j = k
                while j < len(times) and times[j] is None:
                    j += 1
                lo = times[k - 1]
                hi = times[j] if j < len(times) else lo + WORD_CASCADE_MIN_STEP_MS * (j - k + 1) * 1.6
                n = j - k + 1
                for m in range(k, j):
                    times[m] = int(lo + (hi - lo) * (m - k + 1) / n)
                k = j
            # Monotonic, never before the unit reveal, never past the settle window.
            words = []
            prev = start - WORD_CASCADE_MIN_STEP_MS
            for k, tok in enumerate(tokens):
                t = max(int(times[k]), prev + WORD_CASCADE_MIN_STEP_MS, start)
                prev = t
                w = {'text': tok, 'line': line_of[k], 'start_ms': t, 'stress': normalise(tok) in stress}
                if normalise(tok) in muted:
                    w['tone'] = 'mute'
                words.append(w)
            if words:
                last = words[-1]['start_ms']
                settle = _cascade_settle_ms(self.film.brand.finish)
                bl['cascade_end_ms'] = last + settle
                limit = bl['exit_ms'] - 360 if bl.get('exit_ms') else clock.duration_ms - (clock.exit_ms + 40 if clock.fixed_window else 760)
                if last > limit:
                    # Compress the cascade so the phrase finishes reading before it leaves or the beat ends.
                    span = max(1, last - start)
                    room = max(WORD_CASCADE_MIN_STEP_MS * len(words), limit - start)
                    for w in words:
                        w['start_ms'] = int(start + (w['start_ms'] - start) * room / span)
                    bl['cascade_end_ms'] = words[-1]['start_ms'] + settle
                    bl['cascade_compression'] = round(room / span, 3)
            bl['words'] = words
            bl['has_stress'] = any(w['stress'] for w in words)

    @staticmethod
    def _resolve_replacements(b: BeatTreatment, blocks: List[Dict[str, Any]], events: List[Dict[str, Any]], clock: BeatClock) -> List[Dict[str, Any]]:
        """Stage B of a replace group only exists through PHRASE_REPLACE; stage A leaves as B arrives."""
        groups: Dict[str, List[int]] = {}
        for i, u in enumerate(b.units):
            if u.replace_group and u.role == 'hero':
                groups.setdefault(u.replace_group, []).append(i)
        stage_b = {ixs[1] for ixs in groups.values() if len(ixs) >= 2}
        out = list(events)
        for e in out:
            if e['event'] == 'PHRASE_REPLACE' and e['unit_index'] not in stage_b:
                e['event'] = 'MASK_REVEAL'  # a replacement needs a partner; alone it is just a reveal
        for ixs in groups.values():
            if len(ixs) < 2:
                continue
            a, bb = ixs[0], ixs[1]
            rep = next((e for e in out if e['event'] == 'PHRASE_REPLACE' and e['unit_index'] == bb), None)
            out = [e for e in out if not (e['unit_index'] == bb and e['event'] != 'PHRASE_REPLACE')]
            if rep is None:
                a_end = max((e['end_ms'] for e in out if e['unit_index'] == a), default=LEAD_IN_MS)
                rep = {'unit_index': bb, 'role': 'hero', 'event': 'PHRASE_REPLACE', 'start_ms': a_end + 420, 'end_ms': a_end + 750, 'strength': 0.94, 'note': 'replace_group'}
                out.append(rep)
            land = clock.landings_ms[bb]
            if clock.landing_source[bb] == 'WORD':
                a_end = max((e['end_ms'] for e in out if e['unit_index'] == a), default=LEAD_IN_MS)
                dur = rep['end_ms'] - rep['start_ms']
                rep['end_ms'] = max(a_end + 360 + dur, min(land, clock.duration_ms - 700))
                rep['start_ms'] = rep['end_ms'] - dur
            for bl in blocks:
                if bl['unit_index'] == a:
                    bl['replace_partner'] = bb
                    bl['exit_ms'] = rep['start_ms']
                if bl['unit_index'] == bb:
                    bl['replace_partner'] = a
        hold = next((e for e in out if e['event'] == 'HOLD'), None)
        latest = max((e['end_ms'] for e in out if e['event'] not in ('HOLD', 'EXIT')), default=0)
        if hold and hold['start_ms'] < latest:
            hold['start_ms'] = min(latest, hold['end_ms'])
        out.sort(key=lambda e: (e['start_ms'], e['end_ms'], e['unit_index']))
        return out

    @staticmethod
    def _reveal_orphans(b: BeatTreatment, blocks: List[Dict[str, Any]], events: List[Dict[str, Any]], clock: BeatClock) -> List[Dict[str, Any]]:
        """Units the grammar gives no choreography (labels) still land on their word."""
        revealed = {e['unit_index'] for e in events if e['unit_index'] >= 0}
        out = list(events)
        for bl in blocks:
            i = bl['unit_index']
            if i in revealed:
                continue
            land = min(clock.landings_ms[i], clock.duration_ms - 800)
            out.append({'unit_index': i, 'role': bl['role'], 'event': 'FADE_SCALE_SETTLE', 'start_ms': max(0, land - 240), 'end_ms': land, 'strength': 0.5, 'note': 'orphan_reveal'})
        out.sort(key=lambda e: (e['start_ms'], e['end_ms'], e['unit_index']))
        return out

    def _media(self, b: BeatTreatment, comp: Dict[str, Any], clock: BeatClock, typ: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not b.media and not self.carried_media:
            return None
        zone = comp['visual_zone']
        if b.media and self.carried_media and b.media.asset_id == self.carried_media['asset_id']:
            self.carried_media['persist_to'] = b.media.persist_to or b.beat_id
            b = replace(b, media=None)
        if b.media:
            asset = self.film.media_library[b.media.asset_id]
            house = housing(asset.kind, asset.width, asset.height, asset.asset_id, MOTION_PROFILES[self.film.brand.finish])
            ar = chassis_aspect(house['chassis'], asset.width / asset.height)
            bbox = _contain(zone, ar, min(1.0, comp['visual_hints']['evidence_scale']))
            proof_units = [i for i, u in enumerate(b.units) if u.semantic_role in ('proof', 'evidence')]
            hero_land = max((clock.landings_ms[i] for i, u in enumerate(b.units) if u.role == 'hero'), default=LEAD_IN_MS)
            enter = clock.landings_ms[proof_units[0]] if proof_units else hero_land + 180
            enter = min(enter, clock.duration_ms - 900)
            nm = self.media_files.get(asset.asset_id)
            media = {
                'asset_id': asset.asset_id, 'kind': asset.kind,
                'path': nm.render_path if nm else asset.path, 'sha256': nm.render_sha256 if nm else (_sha_file(Path(asset.path)) if Path(asset.path).exists() else None),
                'original_path': asset.path, 'original_sha256': nm.original_sha256 if nm else None, 'render_codec': nm.render_codec if nm else None,
                'role': b.media.role, 'bbox': bbox, 'zone': zone, 'focus': b.media.focus, 'trim': b.media.trim, 'audio': 'MUTE',
                'enter_ms': int(enter), 'enter_duration_ms': 360, 'carried_from': None, 'persist_to': b.media.persist_to, 'frame': 'EVIDENCE_PANEL',
                'source_size': {'w': asset.width, 'h': asset.height}, 'rights': asset.rights,
                **house,
                # A housing is the object's own body: it lands with its content, never as an empty
                # card waiting for the exhibit.
                'chrome_ms': None,
            }
            self.carried_media = media if b.media.persist_to and b.media.persist_to != b.beat_id else None
            return media
        carried = dict(self.carried_media)
        asset = self.film.media_library[carried['asset_id']]
        bbox = _contain(zone, chassis_aspect(carried['chassis'], asset.width / asset.height), min(1.0, comp['visual_hints']['evidence_scale']))
        carried.update({'bbox': bbox, 'zone': zone, 'enter_ms': 0, 'enter_duration_ms': 0, 'chrome_ms': None, 'carried_from': carried.get('carried_from') or self.carried_media['asset_id'],
                        'reframe': {'from': self.carried_media['bbox'], 'start_ms': 0, 'end_ms': 420} if self.carried_media['bbox'] != bbox else None})
        if carried['persist_to'] == b.beat_id:
            self.carried_media = None
        else:
            self.carried_media = carried
        return carried

    def _figure(self, b: BeatTreatment, comp: Dict[str, Any], clock: BeatClock, ensemble: Dict[str, Any], failures: List[str]) -> Optional[Dict[str, Any]]:
        if not b.figure:
            return None
        zone = comp['visual_zone']
        text_cx = comp['text_zone']['x'] + comp['text_zone']['w'] / 2
        zone_cx = zone['x'] + zone['w'] / 2
        # Library artwork faces the viewer's left; mirror when the copy sits to the figure's right.
        facing_left = not (b.figure.facing == 'TOWARD_TEXT' and text_cx > zone_cx + 40)
        if b.figure.facing == 'AWAY':
            facing_left = text_cx > zone_cx
        d = b.figure
        try:
            fig = resolve_figure(d, b.beat_id, self.film.film_id, self.film.brand, facing_left=facing_left,
                                 cast_member=self.film.cast.get(d.character) if d.character else None,
                                 character=d.character)
        except FigurePartError as e:
            failures.append(str(e))
            fig = resolve_figure(FigureDirective(valence=d.valence, arousal=d.arousal, posture=d.posture, energy=d.energy,
                                                 formality=d.formality, facing=d.facing, justification=d.justification),
                                 b.beat_id, self.film.film_id, self.film.brand, facing_left=facing_left)
        bbox = _contain(zone, fig['composition']['aspect'], 1.0, anchor='bottom')
        if getattr(self.film.world, 'book', None) == 'paperbook':
            # The paperbook's plate crops to a wide band of the canvas: the performer must
            # stand at picture-book scale inside it, not caption scale. Grows toward the
            # zone's floor so the ground line stays put, capped at what the safe frame fits.
            cx = bbox['x'] + bbox['w'] / 2
            bottom = bbox['y'] + bbox['h']
            k = min(2.6, (bottom - self.safe['y']) / bbox['h'],
                    (self.safe['w'] - 8) / bbox['w'],
                    2 * (cx - self.safe['x']) / bbox['w'],
                    2 * (self.safe['x'] + self.safe['w'] - cx) / bbox['w'])
            bbox = _box(cx - bbox['w'] * k / 2, bottom - bbox['h'] * k, bbox['w'] * k, bbox['h'] * k)
        ev = next((e for e in ensemble['events'] if e['channel'] == 'CHARACTER'), None)
        enter = ev['start_ms'] if ev else min(clock.duration_ms - 900, max(clock.landings_ms or [LEAD_IN_MS]) + 200)
        # A performer is part of the stage, not a payload: when the character event sits late the figure
        # still arrives inside the lead-in rather than leaving the stage empty.
        enter = max(LEAD_IN_MS // 4 + 20, min(int(enter), LEAD_IN_MS + 220))
        fig.update({'bbox': bbox, 'zone': zone, 'enter_ms': int(enter), 'enter_duration_ms': 300, 'entrance': 'SETTLE_RISE', 'ground_line': round(bbox['y'] + bbox['h'], 1)})
        if d.track:
            dur_in = int(min(750, max(420, clock.duration_ms * 0.12)))
            dur_out = int(min(560, max(360, clock.duration_ms * 0.1)))
            fig['track'] = {'enter': d.track['enter'], 'exit': d.track['exit'],
                            'enter_ms': int(enter), 'enter_duration_ms': dur_in,
                            'exit_start_ms': int(clock.duration_ms - dur_out - 60), 'exit_duration_ms': dur_out}
        if d.prop:
            hand = d.prop['hand']
            side = ('right', 'left')[hand == 'left' or (hand == 'auto' and fig['mirror'])]
            # Anchor sits on the paper figure's carry hand (its arm angles inward ~30°):
            # a fraction of the figure's 100x140 sheet, where the prop is centred.
            fig['prop'] = {'hand': side, 'anchor': {'x': 0.22 if side == 'left' else 0.78, 'y': 0.66},
                           'concept': d.prop['concept'], 'via': d.prop.get('via'),
                           'asset': d.prop.get('asset'), 'photo': d.prop.get('photo'), 'word': d.prop.get('word')}
        if d.motion:
            fig['motion'] = d.motion
        if d.states:
            try:
                states = []
                for st in d.states:
                    at = st.get('at') or {}
                    if 'word' in at:
                        hit = find_landing(list(clock.words), str(at['word']))
                        hit_w = clock.words[hit] if hit is not None else None
                        at_ms = int(hit_w.start_ms) if hit_w else int(clock.duration_ms * 0.5)
                    else:
                        at_ms = int(at.get('offset_ms') or 0)
                    at_ms = max(int(enter) + 120, min(at_ms, clock.duration_ms - 350))
                    swaps = resolve_state_parts(st, PEEPS_INDEX['compositions'][fig['posture']], fig['posture'], b.beat_id)
                    if swaps:
                        states.append({'at_ms': at_ms, 'swaps': swaps})
                if states:
                    fig['states'] = sorted(states, key=lambda s: s['at_ms'])
            except FigurePartError as e:
                failures.append(str(e))
        return fig

    def _data(self, b: BeatTreatment, comp: Dict[str, Any], clock: BeatClock) -> Optional[Dict[str, Any]]:
        if not b.data:
            return None
        zone = comp['visual_zone']
        d = b.data
        canvas = (self.W, self.H)
        if d.kind == 'STAT':
            vbox = _box(zone['x'], zone['y'], zone['w'], zone['h'] * 0.62)
            lbox = _box(zone['x'], zone['y'] + zone['h'] * 0.68, zone['w'], zone['h'] * 0.22)
            blocks = [{'role': 'value', 'text': d.value, 'bbox': vbox, 'fit': asdict(fit_text(d.value, vbox, 'data', 'SemiBold', canvas, 1, mono=True))}]
            if d.label:
                blocks.append({'role': 'label', 'text': d.label, 'bbox': lbox, 'fit': asdict(fit_text(d.label, lbox, 'support', 'SemiBold', canvas, 2))})
        elif d.kind == 'COMPARISON':
            half = zone['w'] / 2 - 12
            blocks = []
            for i, (val, lab) in enumerate(((d.value, d.label), (d.secondary or '', ''))):
                if not val:
                    continue
                vbox = _box(zone['x'] + i * (half + 24), zone['y'], half, zone['h'] * 0.58)
                blocks.append({'role': 'value', 'side': i, 'text': val, 'bbox': vbox, 'fit': asdict(fit_text(val, vbox, 'data', 'SemiBold', canvas, 1, mono=True))})
            if d.label:
                lbox = _box(zone['x'], zone['y'] + zone['h'] * 0.7, zone['w'], zone['h'] * 0.2)
                blocks.append({'role': 'label', 'text': d.label, 'bbox': lbox, 'fit': asdict(fit_text(d.label, lbox, 'support', 'SemiBold', canvas, 2))})
        else:  # SEQUENCE: steps separated by ' | '
            steps = [s.strip() for s in d.value.split('|') if s.strip()][:5]
            blocks = []
            step_h = zone['h'] / max(1, len(steps))
            for i, s in enumerate(steps):
                sbox = _box(zone['x'] + 56, zone['y'] + i * step_h + step_h * 0.18, zone['w'] - 56, step_h * 0.64)
                blocks.append({'role': 'step', 'index': i, 'text': s, 'bbox': sbox, 'fit': asdict(fit_text(s, sbox, 'support', 'SemiBold', canvas, 2)),
                               'marker': _box(zone['x'], zone['y'] + i * step_h + step_h * 0.18, 40, 40)})
        hero_land = max((clock.landings_ms[i] for i, u in enumerate(b.units) if u.role == 'hero'), default=LEAD_IN_MS)
        enter = min(hero_land + 160, clock.duration_ms - 900)
        stagger = 160 if d.kind == 'SEQUENCE' else 0
        return {'kind': d.kind, 'zone': zone, 'blocks': blocks, 'enter_ms': int(enter), 'enter_duration_ms': 340, 'stagger_ms': stagger, 'style': 'COUNT_IN' if d.kind == 'STAT' else 'SETTLE',
                # A hairline table rail enters inside the lead-in when the figures themselves land late.
                'chrome_ms': LEAD_IN_MS // 4 + 40 if enter > LEAD_IN_MS + 340 else None}

    # ------------------------------------------------------------------ beat
    def _illustration(self, b: BeatTreatment, comp: Dict[str, Any], clock: BeatClock) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        il = b.illustration
        if il is None:
            if self.carried_illustration:
                plan = carried_copy(self.carried_illustration)
                if self.carried_illustration.get('persist_to') == b.beat_id:
                    self.carried_illustration = None
                return plan, []
            return None, []
        src = self.illustrations.get(il.carry_from) if il.carry_from else None
        plan, failures = self.solver.compile(il, comp['visual_zone'], clock, b.beat_id, src)
        self.illustrations[b.beat_id] = plan
        self.carried_illustration = plan if il.persist_to else None
        return plan, failures

    def compile(self, b: BeatTreatment, clock: BeatClock, beat_offset_ms: int, beat_index: int = 0) -> Dict[str, Any]:
        failures: List[str] = []
        warnings: List[str] = []
        comp = native.compose(self.aspect, self._native_treatment(b), self._visual_kind(b))
        if b.illustration is not None and not (b.illustration.carry_from and b.illustration.carry_from in self.illustrations):
            _rebalance(comp, self._text_share(b))
        if self.carried_illustration and b.illustration is None:
            comp['visual_zone'] = dict(self.carried_illustration['zone'])  # persisted argument keeps its stage
        elif b.illustration is not None and b.illustration.carry_from and b.illustration.carry_from in self.illustrations:
            comp['visual_zone'] = dict(self.illustrations[b.illustration.carry_from]['zone'])
        object_present = bool(b.media or b.figure or b.data or b.illustration or self.carried_media or self.carried_illustration)
        if object_present:
            comp['text_zone'] = _carve(comp['text_zone'], comp['visual_zone'])
            if comp['text_zone']['w'] < 200 or comp['text_zone']['h'] < 90:
                failures.append('TEXT_ZONE_TOO_SMALL_AFTER_CARVE')
        shot_role = 'PAYOFF' if b.beat_type in ('PAYOFF', 'CTA') else SHOT_ROLE[b.dominant_layer]
        typ, tf, tw = self._typography(b, clock, comp, object_present, shot_role)
        failures += tf
        warnings += tw

        ensemble_plan = ens.EditorialMotionEnsembleDirectorV1().plan(ens.EnsembleRequest(
            duration_ms=clock.duration_ms, shot_role=shot_role,
            hero_motion_count=sum(u.role == 'hero' for u in b.units), support_motion_count=sum(u.role != 'hero' for u in b.units),
            illustration_motion_count=(len(b.illustration.program) if b.illustration else 0) + (1 if (b.media or b.data or self.carried_media) else 0),
            character_present=b.figure is not None,
            transition_mode='TEXT_CARRIER' if (typ['transition_carrier'] and not b.media and not b.illustration) else 'OBJECT_OR_TEXT_CARRIER',
            beat_energy=b.energy, audio_accent_times=[l for l in clock.landings_ms if 0 < l < clock.duration_ms]))
        ensemble = asdict(ensemble_plan)
        warnings += ensemble['warnings']

        media = self._media(b, comp, clock, typ)
        figure = self._figure(b, comp, clock, ensemble, failures)
        data = self._data(b, comp, clock)
        illustration, ilf = self._illustration(b, comp, clock)
        failures += ilf
        if getattr(self.film.world, 'book', None) == 'paperbook':
            illustration = _compose_paperbook_plate(b, illustration, figure, self.W, self.H, clock.duration_ms)
        if illustration:
            if not _inside(illustration['zone'], self.frame, 2):
                failures.append('ILLUSTRATION_OUTSIDE_FRAME')
            for ent in illustration['entities']:
                boxes = [ent['art_bbox']] + ([ent['label']['bbox']] if ent.get('label') else [])
                for bx in boxes:
                    # The paperbook page prints its own words; in-canvas text blocks are
                    # never painted there, so entities cannot collide with them.
                    if getattr(self.film.world, 'book', None) == 'paperbook':
                        break
                    for bl in typ['blocks']:
                        if _overlap(bx, bl['bbox']) > 0:
                            failures.append(f"ILLUSTRATION_COLLIDES_TEXT:{ent['id']}:{bl['unit_index']}")
            if figure and any(_overlap(figure['bbox'], e['art_bbox']) > 0 for e in illustration['entities']):
                failures.append('FIGURE_COLLIDES_ILLUSTRATION')
            if not illustration['carried'] and illustration['state_changes'] == 0 and b.dominant_layer in ('ILLUSTRATION', 'HYBRID'):
                warnings.append('ILLUSTRATION_WITHOUT_STATE_CHANGE')
            for rel in illustration['relations']:
                if rel.get('stub'):
                    warnings.append(f"CONNECTOR_STUB_ADJACENT:{rel['id']}")

        # Ownership: nothing visual may sit on text, and every element stays in the safe frame.
        for name, el in (('MEDIA', media), ('FIGURE', figure)):
            if el:
                if not _inside(el['bbox'], self.frame, 2):
                    failures.append(f'{name}_OUTSIDE_FRAME')
                # The paperbook demotes all in-canvas text (page faces carry prose
                # outside the scene), so nothing visual can collide with it there.
                if getattr(self.film.world, 'book', None) != 'paperbook':
                    for bl in typ['blocks']:
                        if _overlap(el['bbox'], bl['bbox']) > 0:
                            failures.append(f"{name}_COLLIDES_TEXT:{bl['unit_index']}")
        if data:
            for db in data['blocks']:
                if db['fit']['status'] != 'FIT':
                    failures.append(f"DATA_{db['fit']['status']}")
                for bl in typ['blocks']:
                    if _overlap(db['bbox'], bl['bbox']) > 0:
                        failures.append(f"DATA_COLLIDES_TEXT:{bl['unit_index']}")
        # Transition: media persisting into the next beat carries the cut; otherwise the type carrier or a plain settle-cut.
        # The camera move on top of it is one grammar for the film, picked from the energy either side of the cut.
        next_beat = self.film.beats[beat_index + 1] if beat_index + 1 < len(self.film.beats) else None
        if media and media.get('persist_to') and media['persist_to'] != b.beat_id:
            transition = {'mode': 'EVIDENCE_PERSISTENCE', 'owner': 'MEDIA', 'start_ms': clock.duration_ms - clock.exit_ms, 'end_ms': clock.duration_ms}
        elif illustration and illustration.get('persist_to') and illustration['persist_to'] != b.beat_id:
            transition = {'mode': 'ILLUSTRATION_PERSISTENCE', 'owner': 'ILLUSTRATION', 'start_ms': clock.duration_ms - clock.exit_ms, 'end_ms': clock.duration_ms}
        elif typ['transition_carrier']:
            transition = {**typ['transition_carrier'], 'owner': 'TEXT'}
            if clock.fixed_window:
                transition['start_ms'] = max(transition['start_ms'], clock.duration_ms - clock.exit_ms)
        else:
            transition = {'mode': 'SETTLE_CUT', 'owner': 'NONE', 'start_ms': clock.duration_ms - transition_window_ms(b, next_beat, clock.exit_ms), 'end_ms': clock.duration_ms}
        camera = camera_move(b, next_beat, transition['mode'], beat_index, MOTION_PROFILES[self.film.brand.finish]['transition'] == 'scale_through')
        if camera is not None:
            transition['camera'] = camera
            if camera['move'] == 'cut':
                transition['start_ms'] = transition['end_ms']

        # The settled hold is the window in which every authored element has finished arriving and nothing has
        # started leaving; typography, ensemble and object channels are reconciled to that single window.
        settled = [e['end_ms'] for e in typ['events'] + typ['performance_events'] if e['unit_index'] != -1]
        if media:
            settled.append(media['enter_ms'] + media['enter_duration_ms'])
        if figure:
            settled.append(figure['enter_ms'] + figure['enter_duration_ms'])
        if data:
            settled.append(data['enter_ms'] + data['enter_duration_ms'] + data['stagger_ms'] * max(0, len(data['blocks']) - 1))
        if illustration:
            settled.append(illustration['settled_ms'])
        settled += [bl['cascade_end_ms'] for bl in typ['blocks'] if bl.get('cascade_end_ms') and not bl.get('exit_ms')]
        leaving = [transition['start_ms']]
        leaving += [e['start_ms'] for e in typ['events'] if e['event'] == 'EXIT']
        hold_start, hold_end = int(max(settled)), int(min(leaving))
        ensemble['hold_window'] = {'start_ms': hold_start, 'end_ms': hold_end}
        hold = next((e for e in typ['events'] if e['event'] == 'HOLD'), None)
        if hold:
            hold['start_ms'], hold['end_ms'] = hold_start, hold_end
        if clock.fixed_window:
            # Speech sets the window. Copy cascades with the spoken words, so the viewer reads the phrase as it is
            # said; what must survive is the hero in its settled state and every visual state change, legible for
            # a floor that scales with the beat, and no cascade still landing while the beat leaves.
            hero_units = {i for i, u in enumerate(b.units) if u.role == 'hero'}
            core = [e['end_ms'] for e in typ['events'] if e['unit_index'] in hero_units and e['event'] not in ('HOLD', 'EXIT')]
            core += [bl['cascade_end_ms'] for bl in typ['blocks'] if bl['unit_index'] in hero_units and bl.get('cascade_end_ms')]
            if illustration:
                # Decorations ride the hold; only authored state changes claim reading time.
                core += [o['end_ms'] for o in illustration.get('ops', []) if o.get('state_change') and not o.get('synthesized')]
            for el in (media, figure):
                if el:
                    core.append(el['enter_ms'] + el['enter_duration_ms'])
            legible = hold_end - (max(core) if core else hold_start)
            floor = readable_close_floor(clock.pause_after_ms) if clock.pause_after_ms >= 0 else MIN_HOLD_MS
            if legible < floor:
                (warnings if legible >= floor * 0.6 else failures).append(f'LEGIBLE_HOLD_{legible}MS_UNDER_{floor}MS')
            overrun = max((bl['cascade_end_ms'] - hold_end for bl in typ['blocks'] if bl.get('cascade_end_ms')), default=0)
            if overrun > 1000 // self.film.fps:
                failures.append(f'CASCADE_OVERRUNS_EXIT:{overrun}ms')
            for bl in typ['blocks']:
                if bl.get('cascade_compression', 1.0) < 0.8:
                    warnings.append(f"CASCADE_COMPRESSED:{bl['unit_index']}:{bl['cascade_compression']}")
            # Under MASTER the speaker's pause is the settled-hold budget: warn only when the
            # window couldn't afford even the pause-scaled readable close. The flat MIN_HOLD
            # floor stays on free-running beats (HOLD_TOO_SHORT below).
            settled_floor = readable_close_floor(clock.pause_after_ms)
            if hold_end - hold_start < settled_floor:
                warnings.append(f"SETTLED_HOLD:{hold_end - hold_start}ms")
        elif hold_end - hold_start < MIN_HOLD_MS:
            failures.append(f"HOLD_TOO_SHORT:{hold_end - hold_start}ms")
        if b.dominant_layer == 'FIGURE' and not figure:
            failures.append('FIGURE_UNRESOLVED')

        candidates = [{'event': pe['event'], 'at_ms': pe['end_ms'] if pe['event'] != 'SPATIAL_RECONFIGURE' else pe['start_ms'], 'strength': pe['strength']}
                      for pe in typ['performance_events'] if pe['event'] != 'SUPPORT_ITALIC_DRIFT']
        for e in typ['events']:
            if e['event'] == 'KEYWORD_HIT':
                candidates.append({'event': 'KEYWORD_HIT', 'at_ms': e['end_ms'], 'strength': e['strength']})
        if media and media['enter_duration_ms']:
            candidates.append({'event': 'EVIDENCE_LAND', 'at_ms': media['enter_ms'] + media['enter_duration_ms'], 'strength': 0.86, 'glyph': 'MEDIA'})
        if media and media.get('reframe'):
            candidates.append({'event': 'SPATIAL_RECONFIGURE', 'at_ms': 0, 'strength': 0.7})
        if data:
            candidates.append({'event': 'DATA_LAND', 'at_ms': data['enter_ms'] + data['enter_duration_ms'], 'strength': 0.8, 'glyph': 'COUNTER'})
        if illustration and not illustration['carried']:
            # Furniture lands audibly: a pop on each element's arrival. Under the collage's 'pop'
            # entrance the landing wave is the film's signature sound — it wins any window it
            # shares with a text hit (they are one fused moment, so it plays with pop texture),
            # and the 220ms-gap law takes every ~3rd landing of an 80ms-staggered wave.
            # Elsewhere it stays a subordinate furniture click. The accent caps decide the rest.
            pop_entrance = MOTION_PROFILES[self.film.brand.finish]['entrance'] == 'pop'
            for e in illustration['entities']:
                if not e.get('carried') and e.get('enter_duration_ms'):
                    candidates.append({'event': 'ELEMENT_LAND', 'at_ms': e['enter_ms'] + e['enter_duration_ms'], 'strength': 0.99 if pop_entrance else 0.34, 'glyph': e['glyph'], 'concept': e.get('concept')})
            for r in illustration['relations']:
                if not r.get('drawn_by_op') and r.get('enter_duration_ms'):
                    candidates.append({'event': 'ELEMENT_LAND', 'at_ms': r['enter_ms'] + r['enter_duration_ms'], 'strength': 0.3, 'glyph': 'CONNECTOR'})
            glyph_of = {e['id']: e['glyph'] for e in illustration['entities']}
            for o in illustration['ops']:
                if o['state_change'] and o['op'] != 'INK':
                    candidates.append({'event': 'KEYWORD_HIT' if o['op'] == 'STRIKE' else 'EVIDENCE_LAND', 'at_ms': o['end_ms'], 'strength': 0.7, 'glyph': glyph_of.get(o['target'])})
                if o['op'] == 'INK':
                    candidates.append({'event': 'INK_WRITE', 'at_ms': o['start_ms'], 'strength': 0.72})
                if o['op'] in ('DRAW', 'CONNECT', 'TRACE'):
                    if (o.get('params') or {}).get('wipe'):
                        # A wiped stroke sweeps the stage — a whoosh at mid-sweep, not the line-draw
                        # scratch. It is the beat's authored event, so it outranks carriers.
                        candidates.append({'event': 'WIPE_SWEEP', 'at_ms': o['start_ms'] + (o['end_ms'] - o['start_ms']) // 3, 'strength': 0.62})
                    else:
                        candidates.append({'event': 'LINE_DRAW', 'at_ms': o['end_ms'], 'strength': 0.5})
                if o['op'] == 'EMIT':
                    candidates.append({'event': 'EMIT_CONFIRM', 'at_ms': o['end_ms'], 'strength': 0.75, 'glyph': glyph_of.get(o['target'])})
                if o['op'] == 'COUNT':
                    candidates.append({'event': 'COUNT_TICK', 'at_ms': o['end_ms'], 'strength': 0.5, 'glyph': glyph_of.get(o['target'])})
                    candidates.append({'event': 'COUNT_RISE', 'at_ms': o['start_ms'], 'strength': 0.38})
                if o['op'] == 'TRAVEL':
                    candidates.append({'event': 'LOUPE_TRAVEL', 'at_ms': o['end_ms'], 'strength': 0.55})
        if transition['mode'] in ('TEXT_MASK_WIPE', 'LABEL_EXPAND_WIPE'):
            candidates.append({'event': 'TRANSITION_CARRIER', 'at_ms': transition['start_ms'], 'strength': 0.6})
        if figure and figure.get('track') and figure['track'].get('enter', 'none') != 'none':
            # The puppet walks in on paper: a soft footfall as the stride settles.
            tr = figure['track']
            for step in (0.38, 0.78):
                candidates.append({'event': 'FIGURE_STEP', 'at_ms': int(tr['enter_ms'] + tr['enter_duration_ms'] * step), 'strength': 0.4})
        # Camera moves are cuts with motion: a push, pull or drift takes a full whoosh; a dissolve
        # stays a subordinate fabric sound; a hard cut is silent.
        if transition.get('camera') and transition['end_ms'] > transition['start_ms']:
            sweep = {'push_through': 0.78, 'pull_back': 0.7, 'drift': 0.74, 'page': 0.86, 'dissolve': 0.32}.get(transition['camera']['move'])
            if sweep:
                candidates.append({'event': 'TRANSITION_SWEEP', 'at_ms': transition['start_ms'], 'strength': sweep})
        sound = bind_beat_sound(self.lib, self.film.film_id, b.beat_id, beat_offset_ms, b.dominant_layer, b.energy, candidates)
        if b.dominant_layer != 'QUIET':
            amb_concepts = [e.get('concept') for e in (illustration or {}).get('entities', [])] + [m.get('concept') for m in (illustration or {}).get('marks', [])] + [p.get('concept') for p in (b.backdrop or [])]
            amb_tones = [p.get('tone') for p in (b.backdrop or [])]
            amb = bind_beat_ambience(self.lib, self.film.film_id, b.beat_id, [c for c in amb_concepts if c], [t for t in amb_tones if t], int(clock.duration_ms))
            if amb:
                amb['at_ms'] = int(beat_offset_ms)
                amb['dur_ms'] = int(clock.duration_ms)
                sound['ambience'] = amb
        if self.lib is None and candidates and b.dominant_layer != 'QUIET':
            warnings.append('SOUND_LIBRARY_MISSING')

        bg = (comp.get('authentic_v2_plan') or {}).get('background_template') or 'SOFT_FIELD'
        render_bg = 'SPOTLIGHT_STAGE' if figure else ('CARD_STAGE' if (media or data) else ('STAGE_FIELD' if illustration else 'SOFT_FIELD'))
        stage_zone = (media or figure or data or illustration or {}).get('zone') or self.safe
        # Every beat must carry visible content inside its lead-in window: stage, chrome or first words.
        firsts = [w['start_ms'] for w in [{'text': w.text, 'start_ms': w.start_ms, 'end_ms': w.end_ms} for w in clock.words]]
        firsts += [e['start_ms'] for e in typ['events'] if e['unit_index'] >= 0]
        if illustration:
            firsts += [e['enter_ms'] for e in illustration['entities']] + [r['enter_ms'] for r in illustration['relations']]
        if media:
            firsts += [media['chrome_ms'] or media['enter_ms']]
        if data:
            firsts += [data['chrome_ms'] or data['enter_ms']]
        if figure:
            firsts += [figure['enter_ms']]
        if firsts and min(firsts) > LEAD_IN_MS + 420:
            warnings.append(f'EMPTY_LEAD:{min(firsts)}ms')
        return {
            'beat_id': b.beat_id, 'beat_type': b.beat_type, 'pattern': b.pattern, 'dominant_layer': b.dominant_layer, 'shot_role': shot_role,
            'start_ms': beat_offset_ms, 'duration_ms': clock.duration_ms, 'energy': b.energy,
            'narration': b.narration, 'words': [{'text': w.text, 'start_ms': w.start_ms, 'end_ms': w.end_ms} for w in clock.words],
            'landings': [{'unit_index': i, 'at_ms': l, 'source': s} for i, (l, s) in enumerate(zip(clock.landings_ms, clock.landing_source))],
            'composition': {
                'layout_family': comp['layout_family'], 'treatment': comp['treatment'], 'text_zone': comp['text_zone'], 'visual_zone': comp['visual_zone'],
                'safe_area': self.safe, 'background': {'template': bg, 'render': render_bg, 'stage': stage_zone,
                                                       'layers': _background_layers(render_bg, bg, stage_zone, self.safe, (self.W, self.H), beat_index, self.film.brand.finish),
                                                       'finish': self.film.brand.finish},
                'native_profile': comp['native_profile'], 'derived_by_scaling': comp['derived_by_scaling'], 'authority': comp['authority_version'],
            },
            'typography': typ, 'ensemble': {'events': ensemble['events'], 'dominant_sequence': ensemble['dominant_sequence'], 'hold_window': ensemble['hold_window'], 'transition_window': ensemble['transition_window']},
            'media': media, 'figure': figure, 'data': data, 'illustration': illustration, 'transition': transition, 'sound': sound, 'page': b.page,
            'gate': {'status': 'FAIL' if failures else 'PASS', 'failures': failures, 'warnings': sorted(set(warnings))},
        }


def _film_pack(film: FilmTreatment, registry: IllustrationRegistry) -> Optional[str]:
    """The colour pack the film's authored native marks come from (most used wins), if any."""
    tally: Dict[str, int] = {}
    for b in film.beats:
        for e in (b.illustration.entities if b.illustration else []):
            item = registry.items.get(e.asset_ref or '')
            if item and item.get('colour') == 'native' and item.get('family') != 'brand':
                pack = AssetFinder.pack_of(e.asset_ref)
                tally[pack] = tally.get(pack, 0) + 1
    return max(sorted(tally), key=lambda k: tally[k]) if tally else None


def settle_descriptors(plans: Dict[str, Any]) -> None:
    """A tile drawn by a mark or photograph over the concept's own name owes that name the label
    floor. The solver records per aspect whether the well leaves room for it; a name that is short
    of the floor in any aspect is settled once for all of them, so the film keeps one answer: a
    photograph fills the well alone (it *is* the concept), while an ancestor's mark gives way to
    the name set as the mark (a mark the viewer cannot read back is worth less than the word).
    The recorded resolution follows, so the audit says what is drawn."""
    short = set()
    for plan in plans.values():
        for bt in plan['beats']:
            for e in ((bt.get('illustration') or {}).get('entities') or []):
                if e['params'].get('descriptor_fit') is False:
                    short.add((bt['beat_id'], e['id']))
    for plan in plans.values():
        for bt in plan['beats']:
            for e in ((bt.get('illustration') or {}).get('entities') or []):
                if 'descriptor_fit' not in e['params']:
                    continue
                e['params'].pop('descriptor_fit')
                if (bt['beat_id'], e['id']) not in short:
                    continue
                res = dict(e['params'].get('resolution') or {})
                if e.get('photo'):
                    e['params'].pop('word', None)
                    e['params'].pop('word_kind', None)
                    e['params']['descriptor'] = 'photo_fills'
                    res['word'] = None
                else:
                    e['asset'] = None
                    e['params']['descriptor'] = 'word_alone'
                    res.update(via='typographic', asset_ref=None, path=[])
                e['params']['resolution'] = res


# Scene engine: elements that are drawn as paper primitives in the runtime rather than
# resolved through the art ladder. Anything not named here resolves as a concept mark.
SCENE_PROP_SHAPES = {
    'arch', 'beam', 'bed', 'boat', 'bookshelf', 'building', 'car', 'chair', 'cliff', 'cloud',
    'comet', 'coral', 'crate', 'curtain', 'door', 'fence', 'frame', 'hill', 'house', 'hut',
    'kelp', 'lamp', 'log', 'moon', 'mountain', 'pebble', 'pillar', 'planet', 'poster', 'pot',
    'ring', 'rock', 'rug', 'sandcastle', 'shaft', 'shelf', 'sign', 'skyline', 'sofa', 'star',
    'stone', 'stool', 'streetlamp', 'sun', 'table', 'tent', 'tower', 'vase', 'wave', 'window',
}
# Where an element sits by default, as (width, height) fractions of the canvas short edge.
_SCENE_ELEMENT_SIZE = {
    'window': (0.30, 0.40), 'door': (0.24, 0.5), 'table': (0.42, 0.30), 'chair': (0.24, 0.3),
    'stool': (0.2, 0.24), 'shelf': (0.4, 0.1), 'bookshelf': (0.34, 0.55), 'lamp': (0.12, 0.5),
    'rug': (0.5, 0.16), 'bed': (0.55, 0.3), 'sofa': (0.5, 0.3), 'poster': (0.24, 0.3),
    'frame': (0.2, 0.24), 'pot': (0.16, 0.2), 'vase': (0.12, 0.2), 'curtain': (0.16, 0.55),
    'pillar': (0.1, 0.65), 'fence': (0.5, 0.14), 'house': (0.4, 0.36), 'hut': (0.32, 0.3),
    'tent': (0.36, 0.3), 'mountain': (0.6, 0.4), 'hill': (0.55, 0.2), 'cliff': (0.4, 0.5),
    'log': (0.3, 0.1), 'cloud': (0.4, 0.14), 'star': (0.12, 0.12), 'planet': (0.4, 0.4),
    'moon': (0.2, 0.2), 'comet': (0.4, 0.1), 'ring': (0.5, 0.16), 'kelp': (0.12, 0.5),
    'coral': (0.24, 0.26), 'rock': (0.22, 0.14), 'stone': (0.16, 0.1), 'pebble': (0.1, 0.07),
    'sandcastle': (0.3, 0.28), 'building': (0.24, 0.6), 'tower': (0.18, 0.7), 'sign': (0.2, 0.3),
    'streetlamp': (0.1, 0.55), 'car': (0.34, 0.16), 'boat': (0.32, 0.16), 'shaft': (0.24, 0.7),
    'wave': (0.4, 0.12), 'sun': (0.24, 0.24), 'arch': (0.3, 0.5), 'beam': (0.5, 0.06),
    'crate': (0.2, 0.2), 'barrel': (0.18, 0.24), 'skyline': (1.0, 0.35),
}


def _scene_layers(film_id: str, btr: BeatTreatment, canvas: Tuple[int, int], brand: Brand,
                  sky_concepts: Optional[set] = None) -> List[Dict[str, Any]]:
    """The environment engine: the treatment declares a setting and mood, and this composes
    that world out of paper pieces — outdoor skies and grounds, interior walls and furniture,
    starfields, underwater depth, urban skylines, underground soil — all in the film's palette.
    Elements are paper primitives (windows, tables, kelp) or resolved art marks placed on the
    scene's ground line. Under paperbook they land as flat matte pieces with fibre speckle."""
    if not btr.scene:
        return []
    sky_concepts = sky_concepts or set()
    W, H = canvas
    short = min(W, H)
    overhang = W * 0.10
    sc = btr.scene
    setting, mood = sc['setting'], sc.get('mood') or 'day'
    resolved = sc.get('resolved') or {}
    ink, paper, accent = brand.ink, brand.paper, brand.accent or brand.ink
    seed0 = int(hashlib.sha256(f'{film_id}:scene:{btr.beat_id}'.encode()).hexdigest()[:12], 16)
    out: List[Dict[str, Any]] = []

    def band(top: float, height: float, tone: str, plane: float, ragged: bool = True, i: int = 0) -> Dict[str, Any]:
        y = H * top - short * 0.015
        h = H * height + short * 0.03
        return {'kind': 'band',
                'bbox': {'x': round(-overhang, 1), 'y': round(y, 1), 'w': round(W + 2 * overhang, 1), 'h': round(h, 1)},
                'tone': tone, 'plane': plane, 'ragged': ragged, 'seed': seed0 ^ (i * 0x7ab1)}

    # One light source per spread: the sky body's side (suns sit right of the plate,
    # dawn's sun is low-left, storm light is a top-down wash). Every lit piece carries
    # the direction so the runtime can paint a rim where the world catches it and drop
    # the contact shadow on the dark side.
    light_dx = {'day': 1.0, 'golden': 1.0, 'dawn': -1.0, 'dusk': 1.0,
                'night': 1.0, 'storm': 0.0}.get(mood, float((seed0 & 1) * 2 - 1))
    _LIT_SKIP = {'sun', 'moon', 'cloud', 'comet', 'beam', 'star'}
    _CONTACT = {'bush', 'tuft', 'stone', 'mushroom', 'flower', 'streetlamp', 'kelp'}

    def piece(shape: str, x: float, y: float, w: float, h: float, tone: str,
              plane: float = 0.5, i: int = 0, **kw) -> Dict[str, Any]:
        spec = {'kind': 'piece', 'shape': shape,
                'bbox': {'x': round(x, 1), 'y': round(y, 1), 'w': round(w, 1), 'h': round(h, 1)},
                'tone': tone, 'plane': plane, 'seed': seed0 ^ (i * 0x51ab)}
        if shape not in _LIT_SKIP:
            spec['lit_dx'] = light_dx
        if shape in _CONTACT:
            spec['contact'] = True
        spec.update(kw)
        return spec

    # Mood drives the palette: the same outdoor recipe reads noon or midnight from it.
    if mood == 'night':
        sky, mid, gnd, glow = mix(ink, paper, 0.10), mix(ink, paper, 0.20), mix(ink, paper, 0.30), mix(paper, '#ffe9a8', 0.5)
    elif mood == 'dusk':
        sky, mid, gnd, glow = mix(accent, ink, 0.42), mix(ink, accent, 0.28), mix(ink, paper, 0.36), mix(accent, '#ffffff', 0.35)
    elif mood == 'dawn':
        sky, mid, gnd, glow = mix(accent, paper, 0.55), mix(paper, accent, 0.20), mix(ink, paper, 0.18), mix(accent, '#ffffff', 0.5)
    elif mood == 'storm':
        sky, mid, gnd, glow = mix(ink, paper, 0.28), mix(ink, paper, 0.40), mix(ink, paper, 0.48), mix(paper, ink, 0.2)
    elif mood == 'golden':
        sky, mid, gnd, glow = mix(accent, '#ffffff', 0.42), mix(paper, accent, 0.26), mix(ink, accent, 0.28), mix(accent, '#ffffff', 0.55)
    else:  # day
        sky, mid, gnd, glow = mix(paper, accent, 0.16), mix(paper, ink, 0.10), mix(ink, paper, 0.24), mix(accent, '#ffffff', 0.45)

    # Harmony expansion (jacoblockett pattern): a scene is not two inks — hills run
    # green, water runs blue, evening burns warm. Each family is a hue rotation of
    # the film's anchors so the film keeps its identity but the world gains colour.
    seed_h = (seed0 % 97) / 97.0  # per-beat drift keeps sibling spreads related, not identical
    flora = hrot(accent, 112, 1.55, -0.10)                 # hills/ground → green family
    flora = mix(flora, ink, 0.30)
    flora_deep = hrot(accent, 105, 1.5, -0.18)             # near ground → deeper green
    flora_deep = mix(flora_deep, ink, 0.45)
    water = hrot(ink, 12, 1.4)                             # sea/river → deeper blue
    warmth = hrot(accent, -30, 1.35)                       # sunlight/fire → warm family

    def stars(bbox: Dict[str, float], i: int, density: int = 90, plane: float = 0.08) -> Dict[str, Any]:
        return {'kind': 'stars', 'bbox': bbox, 'count': density, 'seed': seed0 ^ (i * 0x33), 'plane': plane}

    def shaft(bbox: Dict[str, float], i: int, tilt: float = 14.0, plane: float = 0.3) -> Dict[str, Any]:
        return {'kind': 'shaft', 'bbox': bbox, 'tone': mix(paper, glow, 0.5), 'tilt_deg': tilt, 'seed': seed0 ^ (i * 0x21), 'plane': plane}

    # Living layers: weather and wildlife that move while the page is read —
    # rain that falls, birds that cross, fireflies that wander. The runtime
    # animates their children per frame; the compiler only casts the world.
    def rain(i: int) -> Dict[str, Any]:
        return {'kind': 'rain', 'bbox': {'x': round(-overhang, 1), 'y': 0,
                                         'w': round(W + 2 * overhang, 1), 'h': round(H, 1)},
                'count': 110, 'seed': seed0 ^ (i * 0x1f), 'plane': 0.7,
                'tone': mix(paper, '#ffffff', 0.55)}

    def birds(i: int, n: int = 3) -> Dict[str, Any]:
        return {'kind': 'birds', 'bbox': {'x': round(-overhang, 1), 'y': round(H * 0.10, 1),
                                          'w': round(W + 2 * overhang, 1), 'h': round(H * 0.35, 1)},
                'count': n, 'seed': seed0 ^ (i * 0x45), 'plane': 0.2, 'tone': mix(ink, paper, 0.18)}

    def fireflies(i: int, n: int = 9) -> Dict[str, Any]:
        return {'kind': 'fireflies', 'bbox': {'x': 0, 'y': round(H * 0.30, 1),
                                              'w': round(W, 1), 'h': round(H * 0.6, 1)},
                'count': n, 'seed': seed0 ^ (i * 0x5b), 'plane': 0.55, 'tone': glow}

    def celestial(i: int) -> None:
        """Sun or moon placed by mood — a flat paper disc, never a glow."""
        if mood in ('day', 'golden'):
            out.append(piece('sun', W * 0.72, H * 0.06, short * 0.17, short * 0.17, glow, 0.1, i))
        elif mood == 'dawn':
            out.append(piece('sun', W * 0.30, H * 0.30, short * 0.2, short * 0.2, glow, 0.1, i))
        elif mood == 'dusk':
            out.append(piece('sun', W * 0.62, H * 0.42, short * 0.16, short * 0.16, mix(accent, ink, 0.1), 0.1, i))
        elif mood == 'night':
            out.append(piece('moon', W * 0.70, H * 0.05, short * 0.14, short * 0.14, mix(paper, '#f5edd8', 0.5), 0.1, i))

    def clouds(i: int, n: int = 2) -> None:
        for k in range(n):
            sx = ((seed0 >> (k * 5)) & 0x3F) / 63.0
            out.append(piece('cloud', W * (0.08 + 0.62 * sx), H * (0.05 + 0.13 * k), W * 0.18, H * 0.13,
                             mix(paper, '#ffffff', 0.65 if mood != 'storm' else 0.15), 0.16, i + k))

    def elements_on(ground_top: float, plane: float = 0.6) -> None:
        """Scene elements land on the ground line, seeded across the width; prop shapes draw
        as paper primitives, everything else as a resolved art mark standing in the world."""
        for k, name in enumerate(sc['elements'][:8]):
            key = name.lower().strip()
            sx = ((seed0 >> (k * 7)) & 0x7F) / 127.0
            x = W * (0.08 + 0.62 * sx)
            w_frac, h_frac = _SCENE_ELEMENT_SIZE.get(key, (0.24, 0.3))
            if key in SCENE_PROP_SHAPES:
                out.append(piece(key, x, ground_top - H * h_frac * 0.6, W * w_frac, H * h_frac,
                                 mix(ink, paper, 0.30 + 0.1 * (k % 3)), plane, 40 + k))
            else:
                asset = resolved.get(name)
                mh = short * 0.16
                art = (asset or {}).get('art_box') or {'w': 1, 'h': 1}
                mw = mh * max(0.25, art['w'] / max(1, art['h']))
                out.append({'kind': 'piece', 'shape': 'art', 'concept': name, 'asset': asset,
                            'bbox': {'x': round(x, 1), 'y': round(ground_top - mh, 1), 'w': round(mw, 1), 'h': round(mh, 1)},
                            'tone': '', 'plane': plane, 'seed': seed0 ^ (k * 0x99),
                            'lit_dx': light_dx, 'contact': True})

    if setting == 'paper':
        # Standing-on-the-page: no painted ground, no sky — the page itself is the
        # world (its own wavy ink field shows through the slot's transparent
        # viewport). All a paper page carries is a pale halo behind the subject
        # and the odd faint wash drifting by; elements float on the stock.
        out.append(piece('disc', W * (0.56 + 0.10 * ((seed0 >> 3) & 1)), H * 0.07,
                         short * 0.30, short * 0.30, mix(paper, glow, 0.40), 0.08, 1))
        out.append(piece('disc', W * 0.10, H * 0.52, short * 0.22, short * 0.22,
                         mix(paper, accent, 0.10), 0.06, 2))
        elements_on(H * 0.86, 0.6)
    elif setting == 'outdoor':
        out.append(band(-0.02, 0.62, sky, 0.10, False, 1))
        celestial(2)
        if mood != 'night':
            clouds(4, 3 if mood != 'storm' else 4)
            # A second, farther cloud layer so the sky has depth, not one stripe of weather.
            for k in range(2):
                sx = ((seed0 >> (k * 9 + 3)) & 0x3F) / 63.0
                out.append(piece('cloud', W * (0.15 + 0.55 * sx), H * (0.24 + 0.07 * k), W * 0.10, H * 0.07,
                                 mix(paper, sky, 0.45), 0.18, 30 + k))
        else:
            out.append(stars({'x': 0, 'y': 0, 'w': W, 'h': H * 0.5}, 8))
            out.append(stars({'x': 0, 'y': 0, 'w': W, 'h': H * 0.30}, 9, 60, 0.05))
        if mood == 'storm':
            out.append(rain(45))
        elif mood in ('day', 'golden'):
            out.append(birds(46))
        else:
            out.append(fireflies(47))
        out.append(band(0.52, 0.24, mid, 0.30, True, 6))
        # Far hills sit between the mid band and the ground — the middle distance
        # every landscape needs. Lit moods green them; night/storm stay ink-dark.
        veg = mood in ('day', 'dawn', 'dusk', 'golden')
        for k in range(2):
            sx = ((seed0 >> (k * 11 + 5)) & 0x7F) / 127.0
            ht = mix(flora if veg else mid, gnd, 0.35 + 0.2 * k)
            out.append(piece('hill', W * (-0.06 + 0.55 * sx), H * (0.44 + 0.05 * k), W * (0.42 + 0.1 * k), H * 0.22,
                             ht, 0.38 + k * 0.06, 32 + k))
        out.append(band(0.66, 0.38, mix(flora_deep, gnd, 0.45) if veg else gnd, 0.55, True, 7))
        elements_on(H * 0.80)
        # Ground scatter: tufts and stones at the feet of the world, near plane.
        for k in range(6):
            sx = ((seed0 >> (k * 6 + 9)) & 0x7F) / 127.0
            sy = ((seed0 >> (k * 4 + 2)) & 0xF) / 15.0
            shape = ('tuft', 'stone', 'tuft', 'bush', 'tuft', 'stone')[k % 6] if mood != 'night' else ('tuft', 'stone')[k % 2]
            sw = W * (0.05 + 0.05 * ((seed0 >> (k * 3)) & 3) / 3.0)
            fl_t = mix(flora, gnd, 0.3 + 0.1 * (k % 2)) if veg and shape in ('tuft', 'bush') else mix(ink, paper, 0.30 + 0.08 * (k % 3))
            out.append(piece(shape, W * (0.03 + 0.9 * sx), H * (0.74 + 0.20 * sy) - short * 0.05,
                             sw, short * (0.06 + 0.03 * (k % 3)), fl_t, 0.62 + 0.05 * (k % 2), 34 + k))
        # Foreground fringe: bushes nearer than the subject, cropped by the page's lower
        # edge — the depth cue a still camera needs. Darker than the ground plane.
        for k in range(2):
            sx = ((seed0 >> (k * 13 + 21)) & 0x7F) / 127.0
            fg_t = mix(flora_deep, ink, 0.42) if veg else mix(ink, paper, 0.20)
            out.append(piece('bush', W * (-0.04 + 0.72 * sx), H * 0.91,
                             W * (0.30 + 0.14 * k), short * 0.17, fg_t, 0.92, 60 + k))
    elif setting == 'indoor':
        wall = mix(paper, ink, 0.07 if mood != 'night' else 0.3)
        out.append(band(-0.02, 0.72, wall, 0.12, False, 1))
        out.append(band(0.70, 0.34, mix(ink, paper, 0.22), 0.5, False, 2))
        out.append(piece('beam', -overhang, H * 0.685, W + 2 * overhang, H * 0.02, mix(ink, wall, 0.35), 0.4, 3))
        # Rooms read by their furnishing: a window or picture on the wall, a rug underfoot.
        out.append(piece('window', W * 0.08, H * 0.14, W * 0.16, H * 0.30, mix(ink, wall, 0.5), 0.2, 30))
        out.append(piece('frame', W * (0.58 + 0.1 * ((seed0 >> 4) & 3) / 3.0), H * 0.16, W * 0.11, H * 0.17, mix(ink, wall, 0.4), 0.2, 31))
        out.append(piece('rug', W * 0.30, H * 0.80, W * 0.4, H * 0.14, mix(accent, ink, 0.4), 0.52, 32))
        elements_on(H * 0.70)
    elif setting == 'space':
        out.append(band(-0.02, 1.04, mix(ink, paper, 0.05), 0.05, False, 1))
        out.append(stars({'x': 0, 'y': 0, 'w': W, 'h': H}, 2, 260))
        out.append(stars({'x': 0, 'y': 0, 'w': W, 'h': H * 0.55}, 12, 120, 0.05))
        # The great circle is an orbit path, not a ring around a body: skipped when a
        # celestial subject is on the plate, else the sun reads as Saturn.
        sky_bodies = {'sun', 'moon', 'planet', 'star', 'moon-full', 'moon-crescent', 'comet'}
        if not (sky_concepts & sky_bodies):
            out.append({'kind': 'arc', 'bbox': {'x': -W * 0.1, 'y': H * 0.1, 'w': W * 1.2, 'h': H * 0.9}, 'corner': 1, 'plane': 0.1})
        out.append(piece('planet', W * 0.55, H * 0.30, short * 0.36, short * 0.36, accent, 0.18, 3))
        out.append(piece('moon', W * 0.12, H * 0.14, short * 0.1, short * 0.1, mix(paper, '#f5edd8', 0.4), 0.14, 4))
        out.append(piece('comet', W * 0.05, H * 0.08, W * 0.22, short * 0.04, mix(paper, accent, 0.5), 0.12, 5))
        # Asteroid drift and a farther planet — the void needs bodies at depth.
        for k in range(3):
            sx = ((seed0 >> (k * 8 + 1)) & 0x7F) / 127.0
            sy = ((seed0 >> (k * 5 + 7)) & 0x3F) / 63.0
            out.append(piece('rock', W * (0.10 + 0.8 * sx), H * (0.35 + 0.5 * sy),
                             short * (0.03 + 0.04 * (k % 2)), short * 0.045, mix(ink, paper, 0.35), 0.32, 30 + k))
        out.append(piece('planet', W * (0.02 + 0.2 * ((seed0 >> 9) & 3) / 3.0), H * 0.62, short * 0.10, short * 0.10,
                         mix(accent, ink, 0.35), 0.30, 34))
        elements_on(H * 0.95)
    elif setting == 'underwater':
        # Water runs blue even when the accent doesn't: rotate the deeps into the
        # water family, then deepen with plane as before.
        w = water if mood in ('day', 'dawn', 'golden') else mix(ink, accent, 0.4)
        deep1, deep2, deep3 = mix(w, ink, 0.35), mix(w, ink, 0.5), mix(w, ink, 0.62)
        out.append(band(-0.02, 0.42, deep1, 0.08, False, 1))
        out.append(band(0.30, 0.45, deep2, 0.2, False, 2))
        out.append(shaft({'x': W * 0.18, 'y': 0, 'w': W * 0.16, 'h': H * 0.85}, 3, 12.0))
        out.append(shaft({'x': W * 0.55, 'y': 0, 'w': W * 0.10, 'h': H * 0.7}, 4, -9.0))
        out.append(band(0.60, 0.45, deep3, 0.4, True, 5))
        out.append(band(0.80, 0.24, mix(ink, paper, 0.28), 0.55, True, 6))
        # Rising bubbles and kelp on the bed — water reads by what drifts through it.
        for k in range(4):
            sx = ((seed0 >> (k * 7 + 3)) & 0x7F) / 127.0
            sy = ((seed0 >> (k * 4 + 6)) & 0x3F) / 63.0
            out.append(piece('bubble', W * (0.10 + 0.75 * sx), H * (0.18 + 0.5 * sy),
                             short * (0.04 + 0.02 * (k % 2)), short * 0.05, mix(paper, accent, 0.4), 0.45, 30 + k))
        for k in range(3):
            sx = ((seed0 >> (k * 9 + 11)) & 0x7F) / 127.0
            out.append(piece('kelp', W * (0.05 + 0.85 * sx), H * 0.86 - short * 0.16,
                             W * 0.08, short * 0.17, mix(ink, accent, 0.55), 0.6, 36 + k))
        elements_on(H * 0.88)
    elif setting == 'urban':
        out.append(band(-0.02, 0.55, sky, 0.10, False, 1))
        if mood == 'night':
            out.append(stars({'x': 0, 'y': 0, 'w': W, 'h': H * 0.4}, 8, 70))
        celestial(3)
        out.append({'kind': 'windows', 'bbox': {'x': -overhang, 'y': H * 0.28, 'w': W + 2 * overhang, 'h': H * 0.30},
                    'tone': mix(ink, paper, 0.45), 'lit': glow, 'seed': seed0 ^ 0x77, 'plane': 0.22, 'rows': 4, 'silhouette': True,
                    'lit_dx': light_dx})
        out.append({'kind': 'windows', 'bbox': {'x': -overhang, 'y': H * 0.44, 'w': W + 2 * overhang, 'h': H * 0.30},
                    'tone': mix(ink, paper, 0.30), 'lit': glow, 'seed': seed0 ^ 0x78, 'plane': 0.42, 'rows': 5, 'silhouette': True,
                    'lit_dx': light_dx})
        out.append(band(0.72, 0.32, mix(ink, paper, 0.16), 0.55, False, 6))
        # Street furniture in the near plane — the street level the eye lands on.
        for k in range(2):
            sx = ((seed0 >> (k * 10 + 4)) & 0x7F) / 127.0
            out.append(piece('streetlamp', W * (0.10 + 0.72 * sx), H * 0.72 - short * 0.30,
                             W * 0.07, short * 0.31, mix(ink, paper, 0.18), 0.7, 30 + k))
        elements_on(H * 0.84)
    elif setting == 'ground':
        out.append(band(-0.02, 0.14, sky, 0.08, False, 1))
        out.append(band(0.10, 0.40, mix(ink, accent, 0.55), 0.3, True, 2))
        out.append(band(0.46, 0.34, mix(ink, accent, 0.68), 0.45, True, 3))
        out.append(band(0.76, 0.28, mix(ink, paper, 0.5), 0.58, True, 4))
        if mood in ('dusk', 'night'):
            out.append(fireflies(48, 7))
        if mood == 'storm':
            out.append(rain(49))
        for k in range(7):
            sx = ((seed0 >> (k * 6)) & 0x7F) / 127.0
            out.append(piece('stone', W * (0.04 + 0.86 * sx), H * (0.25 + 0.58 * ((seed0 >> k) & 7) / 8.0),
                             W * (0.05 + 0.05 * ((seed0 >> (k * 3)) & 3) / 3.0), short * 0.05, mix(paper, ink, 0.3), 0.5, 10 + k))
        elements_on(H * 0.55)
    else:  # abstract — a colour field with authored geometry, never a pattern tile
        out.append(band(-0.02, 1.04, mix(paper, accent, 0.10), 0.08, False, 1))
        out.append({'kind': 'arc', 'bbox': {'x': -W * 0.05, 'y': -H * 0.1, 'w': W * 1.1, 'h': H * 1.1}, 'corner': (seed0 & 3), 'plane': 0.12})
        for k, sh in enumerate(('planet', 'beam', 'cloud')):
            out.append(piece(sh, W * (0.15 + 0.3 * k), H * (0.2 + 0.22 * k), short * 0.2, short * 0.12,
                             mix(accent, ink, 0.15 * k), 0.3, 5 + k))
        elements_on(H * 0.85)
    return out


def _backdrop_layers(film_id: str, btr: BeatTreatment, canvas: Tuple[int, int], brand: Brand) -> List[Dict[str, Any]]:
    """Diorama planes a treatment authored for this beat, cut in the film's palette and laid at
    their parallax depth. `auto` tones deepen as the plane nears the content; a concept that
    resolved to a mark perches on its band's torn edge like a pinned cut-out."""
    if not btr.backdrop:
        return []
    W, H = canvas
    short = min(W, H)
    overhang = W * 0.10  # parallax travel must never reveal a band's edge
    out: List[Dict[str, Any]] = []
    for i, p in enumerate(btr.backdrop):
        tone, depth = p['tone'], p['depth']
        if tone == 'auto':
            hex_tone = mix(brand.paper, brand.ink, 0.06 + 0.20 * depth)
        elif tone == 'accent':
            hex_tone = brand.accent or brand.ink
        elif tone == 'ink':
            hex_tone = brand.ink
        elif tone == 'paper':
            hex_tone = brand.paper
        else:
            hex_tone = tone
        band = p['band']
        y = H * band['top'] - short * 0.015
        h = H * band['height'] + short * 0.03
        seed = int(hashlib.sha256(f'{film_id}:band:{btr.beat_id}:{i}'.encode()).hexdigest()[:12], 16)
        layer: Dict[str, Any] = {'kind': 'band',
                                 'bbox': {'x': round(-overhang, 1), 'y': round(y, 1),
                                          'w': round(W + 2 * overhang, 1), 'h': round(h, 1)},
                                 'tone': hex_tone, 'plane': depth, 'ragged': bool(p.get('ragged')), 'seed': seed}
        asset = p.get('asset')
        if asset:
            mh = short * (0.09 + 0.13 * depth)
            art = asset.get('art_box') or {'w': 1, 'h': 1}
            mw = mh * max(0.25, art['w'] / max(1, art['h']))
            xf = 0.18 + 0.55 * (((seed >> 6) & 0x7F) / 127.0)
            layer['mark'] = {'path': asset['path'], 'sha256': asset.get('sha256'), 'concept': p.get('concept'),
                             'bbox': {'x': round(-overhang + (W + 2 * overhang) * xf, 1),
                                      'y': round(y - mh * 0.82, 1), 'w': round(mw, 1), 'h': round(mh, 1)}}
        out.append(layer)
    return out


def _resolve_concepts(film: FilmTreatment, registry: IllustrationRegistry, work_dir: Optional[Path] = None) -> List[str]:
    """Turn every entity `concept` into an asset_ref and/or a typeset word before any aspect is
    solved, so all aspects draw the same answer. The ladder is pinned to the film's colour pack:
    authored marks set it, otherwise the first pass's most common pack does. Returns film-level
    warnings (a photo catalogue that would not answer, so a lower rung stood in)."""
    todo = [(b, e) for b in film.beats if b.illustration for e in b.illustration.entities if e.concept and not e.asset_ref]
    prop_todo = [b for b in film.beats if b.figure and b.figure.prop]
    backdrop_todo = [(b, p) for b in film.beats if b.backdrop for p in b.backdrop if p.get('concept')]
    scene_todo = [(b, e) for b in film.beats if b.scene for e in b.scene['elements'] if e.lower().strip() not in SCENE_PROP_SHAPES]
    motif = film.world.motif if film.world and film.world.motif else None
    if not todo and not prop_todo and not motif and not backdrop_todo and not scene_todo:
        return []
    finder = AssetFinder(registry.items, NounLexicon(), registry.quarantined)
    pack = _film_pack(film, registry)
    if pack is None:
        tally: Dict[str, int] = {}
        for _b, e in todo:
            r = finder.resolve(e.concept, None, e.glyph in WORD_GLYPHS)
            item = registry.items.get(r.asset_ref or '')
            if item and item.get('colour') == 'native' and item.get('family') != 'brand':
                p = AssetFinder.pack_of(r.asset_ref)
                tally[p] = tally.get(p, 0) + 1
        pack = max(sorted(tally), key=lambda k: tally[k]) if tally else None
    # With a colour pack in play a flat mono icon among colour art is the mix the film forbids,
    # so the ladder only offers native marks and otherwise typesets.
    native_only = pack is not None
    evidence = PhotoEvidence(lexicon=finder.lexicon)
    # Paperbook paints its concepts: a real picture-book plate from the open-licensed
    # bank outranks a photograph; other dialects keep photo evidence first.
    bankart = BankArt() if film.world and film.world.book == 'paperbook' else None
    for b, e in todo:
        named = e.glyph == 'CHIP' and e.label is not None
        r = finder.resolve(e.concept, pack, e.glyph in WORD_GLYPHS, native_only, named)
        if r.via in PHOTO_BELOW and e.glyph in WORD_GLYPHS:
            # No mark names the concept itself: a rights-clean photograph of it, set in the housing's
            # well, beats an ancestor's mark or the bare word. The name still rides with it unless
            # the housing already carries it.
            rec = evidence.find(e.concept)
            if bankart is not None:
                brec = bankart.find(e.concept)
                if brec is not None:
                    word = None if (named or e.glyph == 'BADGE') else e.concept
                    r = Resolution(e.concept, 'bank', asset_ref=None, word=word, path=[e.concept, brec['desc']])
                    plan = bankart.as_plan(brec)
                    if work_dir is not None:
                        # Papercut-ify (onionsvg/cutter principle): the imported plate is
                        # re-printed in the film's own inks — quantized then remapped to the
                        # brand ramp — so it reads as page illustration, not pasted photo.
                        ramp = tonal_ramp(film.brand.paper, film.brand.ink, film.brand.accent or '#b8263b')
                        dest = work_dir / 'papercut' / f"{brec['id'].replace('/', '_').replace(':', '_')}.png"
                        if not dest.exists():
                            papercut_image(plan['path'], str(dest), ramp)
                        with Image.open(dest) as dim:
                            drec = {'path': str(dest), 'sha256': _sha_file(dest), 'source_size': {'w': dim.width, 'h': dim.height}}
                        # Coverage gate: a print that is almost all paper mounts as a blank
                        # card — drop it and let the concept ladder keep climbing.
                        inked = papercut_coverage(str(dest), ramp[0])
                        if inked < 0.10:
                            brec = None
                            r = replace(r, via='typographic', asset_ref=None, word=None)
                            e.params.pop('photo', None)
                            rec = None
                        else:
                            plan.update(drec)
                            plan['papercut_of'] = brec['id']
                            plan['ink_coverage'] = inked
                    if brec is not None:
                        e.params['photo'] = plan
                        rec = None
            if rec is not None:
                word = None if (named or e.glyph == 'BADGE') else e.concept
                r = Resolution(e.concept, 'photo', asset_ref=None, word=word, path=[e.concept, rec.title])
                e.params['photo'] = evidence.as_plan(rec)
        if e.glyph == 'CHIP' and not named and r.via in ('composite', 'photo', 'bank'):
            # A chip's peg holds the mark or photograph and its inside label the name: an unlabelled
            # chip drawn by an ancestor or a photograph takes its concept as that label, so the
            # descriptor is typeset through the label fit rather than squeezed into the peg.
            e.label = e.concept
            r = replace(r, via='hypernym' if r.via == 'composite' else r.via, word=None)
        if r.via == 'composite' and e.glyph == 'BADGE':
            # A disc is too small for a mark and a word: it takes its own name (or monogram)
            # rather than an ancestor's mark the viewer cannot read back to the concept.
            r = replace(r, via='typographic', asset_ref=None, path=[])
        if r.via == 'unresolved':
            # Only a bare ICON can end here (every housing typesets). Nothing stands in for it.
            raise TreatmentError('CONCEPT_UNRESOLVED', f'{e.id}: no mark in the registry draws {e.concept!r} and {e.glyph} cannot typeset it', b.beat_id)
        e.asset_ref = r.asset_ref
        if r.word:
            # A concept id is an index, not a word — the page never typesets an underscore.
            e.params['word'] = r.word.replace('_', ' ')
            e.params['word_kind'] = 'numeric' if r.via == 'numeric' else 'name'
        e.params['resolution'] = r.as_dict()
    for b in prop_todo:
        # A performer's prop rides the same ladder: named mark, otherwise a photo, else a typeset tag.
        p = b.figure.prop
        r = finder.resolve(p['concept'], pack, True, native_only)
        p['via'] = r.via
        if r.via in PHOTO_BELOW:
            rec = evidence.find(p['concept'])
            if rec is not None:
                p['photo'] = evidence.as_plan(rec)
                r = replace(r, via='photo', asset_ref=None, path=[p['concept'], rec.title])
                p['via'] = r.via
        p['asset_ref'] = r.asset_ref
        p['asset'] = registry.resolve(r.asset_ref, b.beat_id) if r.asset_ref else None
        p['word'] = (r.word if r.word else (None if r.asset_ref or p.get('photo') else p['concept']))
        if p['word']:
            p['word'] = p['word'].replace('_', ' ')
        p['resolution'] = r.as_dict()
    for b, p in backdrop_todo:
        # A backdrop silhouette mark wants vector art: the ladder ends at asset_ref — a photo or
        # typeset tag would break the paper plane, so the plane still paints and drops the mark.
        r = finder.resolve(p['concept'], pack, True, native_only)
        p['via'] = r.via
        p['asset_ref'] = r.asset_ref
        p['asset'] = registry.resolve(r.asset_ref, b.beat_id) if r.asset_ref else None
        p['resolution'] = r.as_dict()
    for b, e in scene_todo:
        # A scene element that is not a paper primitive resolves the same way — it stands in
        # the world as its own art mark (a tree, a fish, a telescope on the ground line).
        r = finder.resolve(e, pack, True, native_only)
        if r.asset_ref:
            b.scene.setdefault('resolved', {})[e] = registry.resolve(r.asset_ref, b.beat_id)
    if motif:
        # The film's signature mark rides the same ladder once — every aspect and every beat
        # stamps the same answer.
        r = finder.resolve(motif['concept'], pack, True, native_only)
        motif['via'] = r.via
        if r.via in PHOTO_BELOW:
            rec = evidence.find(motif['concept'])
            if rec is not None:
                motif['photo'] = evidence.as_plan(rec)
                r = replace(r, via='photo', asset_ref=None, path=[motif['concept'], rec.title])
                motif['via'] = r.via
        motif['asset_ref'] = r.asset_ref
        motif['asset'] = registry.resolve(r.asset_ref, '') if r.asset_ref else None
        motif['word'] = r.word if r.word else (None if r.asset_ref or motif.get('photo') else motif['concept'])
        motif['resolution'] = r.as_dict()
    return [f'EVIDENCE_UNAVAILABLE:{u}' for u in evidence.unavailable]


def _asset_pack_mix(film: FilmTreatment, registry: IllustrationRegistry) -> List[str]:
    """One colour pack per film. Native-colour art from different packs (3D emoji next to flat
    icons) reads as assembled, not designed; brand marks are exempt since each is its own mark."""
    by_pack: Dict[str, List[str]] = {}
    for b in film.beats:
        if not b.illustration:
            continue
        for e in b.illustration.entities:
            item = registry.items.get(e.asset_ref or '')
            if not item or item.get('colour') != 'native' or item.get('family') == 'brand':
                continue
            by_pack.setdefault('.'.join(e.asset_ref.split('.')[:2]), []).append(f'{b.beat_id}:{e.asset_ref}')
    if len(by_pack) <= 1:
        return []
    packs = sorted(by_pack, key=lambda k: (-len(by_pack[k]), k))
    strays = [ref for k in packs[1:] for ref in by_pack[k]]
    return [f'ASSET_PACK_MIX:{packs[0]}!={ref}' for ref in strays]


def _captions(beats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    caps = []
    for bt in beats:
        for w in bt['words']:
            caps.append({'beat_id': bt['beat_id'], 'text': w['text'], 'start_ms': bt['start_ms'] + w['start_ms'], 'end_ms': bt['start_ms'] + w['end_ms']})
    return caps


def _grow(bbox: Dict[str, float], need_w: float, need_h: float, zone: Dict[str, float], safe: Dict[str, float]) -> Dict[str, float]:
    """Enlarge a box about its centre to at least need_w x need_h, staying inside the text zone and safe frame."""
    lim_x = max(zone['x'], safe['x'])
    lim_r = min(zone['x'] + zone['w'], safe['x'] + safe['w'])
    lim_y = max(zone['y'], safe['y'])
    lim_b = min(zone['y'] + zone['h'], safe['y'] + safe['h'])
    w = min(max(bbox['w'], need_w), lim_r - lim_x)
    h = min(max(bbox['h'], need_h), lim_b - lim_y)
    cx, cy = bbox['x'] + bbox['w'] / 2, bbox['y'] + bbox['h'] / 2
    x = min(max(cx - w / 2, lim_x), lim_r - w)
    y = min(max(cy - h / 2, lim_y), lim_b - h)
    return {'x': round(x, 1), 'y': round(y, 1), 'w': round(w, 1), 'h': round(h, 1)}


def _nudge_clear(bbox: Dict[str, float], others: List[Dict[str, float]], zone: Dict[str, float]) -> Dict[str, float]:
    """Slide a box vertically inside the zone to the nearest position clear of every other box; unchanged if none exists."""
    if not any(_overlap(bbox, o) > 0 for o in others):
        return bbox
    lo, hi = zone['y'], zone['y'] + zone['h'] - bbox['h']
    candidates: List[float] = []
    for o in others:
        candidates += [o['y'] - bbox['h'] - 6, o['y'] + o['h'] + 6]
    best = None
    for y in sorted(c for c in candidates if lo - 0.5 <= c <= hi + 0.5):
        trial = {**bbox, 'y': round(y, 1)}
        if not any(_overlap(trial, o) > 0 for o in others):
            if best is None or abs(y - bbox['y']) < abs(best['y'] - bbox['y']):
                best = trial
    return best or bbox


def _rebalance(comp: Dict[str, Any], text_share: float) -> None:
    """Re-split a stacked (text over visual) or side-by-side (text beside visual) stage so the copy gets `text_share` of the axis."""
    t, v = comp['text_zone'], comp['visual_zone']
    gap_y = v['y'] - (t['y'] + t['h'])
    gap_x = v['x'] - (t['x'] + t['w'])
    if gap_y >= 0 and _overlap({**t, 'y': 0, 'h': 1}, {**v, 'y': 0, 'h': 1}) > 0:
        top, bottom = t['y'], v['y'] + v['h']
        span = bottom - top - gap_y
        th = round(span * text_share, 1)
        t['h'] = th
        v['y'] = round(top + th + gap_y, 1)
        v['h'] = round(bottom - v['y'], 1)
    elif gap_x >= 0 and _overlap({**t, 'x': 0, 'w': 1}, {**v, 'x': 0, 'w': 1}) > 0:
        left, right = t['x'], v['x'] + v['w']
        span = right - left - gap_x
        tw = round(span * max(text_share, 0.4), 1)
        t['w'] = tw
        v['x'] = round(left + tw + gap_x, 1)
        v['w'] = round(right - v['x'], 1)


def _extend_for_program(clock: BeatClock, b: BeatTreatment) -> BeatClock:
    """An illustration op that lands on a late word must still finish, settle and be read before the cut.

    A MASTER window cannot grow: the deficit is folded into ``budget_met`` and gated there."""
    if not b.illustration:
        return clock
    cursor = 0
    latest = 0
    for op in b.illustration.program:
        if 'word' in op.at:
            idx = find_landing(clock.words, op.at['word'], cursor)
            if idx is None:
                continue
            start = clock.words[idx].start_ms - 60
            cursor = idx
        elif 'unit' in op.at:
            start = clock.landings_ms[op.at['unit']]
        else:
            start = LEAD_IN_MS + op.at['offset_ms']
        latest = max(latest, start + op.duration_ms)
    needed = latest + MIN_HOLD_MS + EXIT_MS + 80
    if needed <= clock.duration_ms:
        return clock
    if clock.fixed_window:
        met = max(0.0, (clock.duration_ms - latest) / (MIN_HOLD_MS + EXIT_MS + 80))
        return replace(clock, budget_met=round(min(clock.budget_met, met), 3))
    return replace(clock, duration_ms=int(needed))


def _master_clocks(film: FilmTreatment, base_dir: Path) -> Tuple[MasterTimeline, List[BeatClock], List[int], List[VoiceSegment]]:
    """Beats take their windows from the continuous speech timeline; the last spoken beat gets a silent readable close."""
    tl = resolve_master(film.beats, film.voice, base_dir)
    by_id = {w.beat_id: w for w in tl.windows}
    clocks: List[BeatClock] = []
    for b in film.beats:
        w = by_id[b.beat_id]
        clocks.append(_extend_for_program(window_clock(b.beat_id, [u.text for u in b.units], [u.anchor_word for u in b.units], w.local_words(), w.duration_ms, 'MASTER', w.pause_after_ms), b))
    last = next((i for i in range(len(film.beats) - 1, -1, -1) if by_id[film.beats[i].beat_id].speech_start_ms >= 0), None)
    if last is not None and clocks[last].budget_met < 1.0:
        c = clocks[last]
        need = max((max(c.landings_ms) + LAND_SETTLE_MS) if c.landings_ms else 0, (c.words[-1].start_ms + _cascade_settle_ms(film.brand.finish)) if c.words else 0) + MIN_HOLD_MS + EXIT_MS
        extend_tail(tl, need - c.duration_ms)
        w = by_id[film.beats[last].beat_id]
        clocks[last] = _extend_for_program(window_clock(c.beat_id, [u.text for u in film.beats[last].units], [u.anchor_word for u in film.beats[last].units], w.local_words(), w.duration_ms, 'MASTER', w.pause_after_ms), film.beats[last])
    offsets = [by_id[b.beat_id].start_ms for b in film.beats]
    seg = VoiceSegment('MASTER', 'MASTER', None, tl.audio_path, hashlib.sha256(Path(tl.audio_path).read_bytes()).hexdigest(), tl.audio_ms,
                       {'alignment_path': str((base_dir / film.voice['alignment_path']).resolve()), 'head_pad_ms': tl.head_pad_ms, 'tail_silence_ms': tl.tail_silence_ms,
                        'tempo': tl.tempo, 'windows': [{'beat_id': w.beat_id, 'start_ms': w.start_ms, 'end_ms': w.end_ms, 'speech_start_ms': w.speech_start_ms,
                                                         'speech_end_ms': w.speech_end_ms, 'pause_before_ms': w.pause_before_ms, 'pause_after_ms': w.pause_after_ms,
                                                         'match_ratio': w.match_ratio} for w in tl.windows]})
    return tl, clocks, offsets, [seg]


def compile_film(treatment: Dict[str, Any], work_dir: Path, base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Compile every requested aspect. Returns {'plans': {aspect: plan}, 'gate': {...}, 'voice': [...]}."""
    film = FilmTreatment.parse(treatment)
    base_dir = base_dir or work_dir
    work_dir.mkdir(parents=True, exist_ok=True)
    for m in film.media_library.values():
        p = Path(m.path)
        m.path = str(p if p.is_absolute() else (base_dir / p).resolve())
        if not Path(m.path).exists():
            raise TreatmentError('MEDIA_ASSET_FILE_MISSING', m.path)
    normalised = {m.asset_id: normalise_media(m, work_dir) for m in film.media_library.values()}
    treatment_sha = hashlib.sha256(json.dumps(treatment, sort_keys=True).encode()).hexdigest()
    voice_source = str(film.voice.get('source') or 'FIXTURE').upper()
    timeline: Optional[MasterTimeline] = None
    if voice_source == 'MASTER':
        timeline, clocks, offsets, segments = _master_clocks(film, base_dir)
        total_ms = timeline.film_ms
        segment_starts = [timeline.head_pad_ms]
    else:
        segments = resolve_voice(film.beats, film.voice, work_dir, base_dir, film.film_id)
        seg_by_id: Dict[str, VoiceSegment] = {s.beat_id: s for s in segments}
        clocks = []
        for b in film.beats:
            seg = seg_by_id[b.beat_id]
            clock = beat_clock(b.beat_id, [u.text for u in b.units], [u.anchor_word for u in b.units], seg.alignment, seg.source, b.min_duration_ms, b.energy)
            clocks.append(_extend_for_program(clock, b))
        offsets = []
        t = 0
        for c in clocks:
            offsets.append(t)
            t += c.duration_ms
        total_ms = t
        segment_starts = [o + LEAD_IN_MS for o in offsets]

    root = library_root()
    lib = SoundLibrary(root) if root else None
    plans: Dict[str, Any] = {}
    registry = IllustrationRegistry()
    film_warnings: List[str] = _resolve_concepts(film, registry, work_dir)
    film_failures: List[str] = _asset_pack_mix(film, registry)
    atmosphere = film_atmosphere(asdict(film.brand))
    film_failures += brand_failures(atmosphere)
    # The bed is chosen before any beat is laid out: its tempo sets the landing-wave stagger, and once
    # the beats exist its playback phase is fitted to their landings. Every aspect shares the one bed.
    spoken = [b for b in film.beats if b.dominant_layer != 'QUIET'] or film.beats
    music = bind_film_music(film.film_id, film.mood, total_ms, sum(b.energy for b in spoken) / len(spoken))
    profile = MOTION_PROFILES[film.brand.finish]
    stagger_ms, subdivision = groove_stagger(profile['stagger_ms'], music.get('bpm'))
    for aspect in film.aspects:
        bc = BeatCompiler(film, aspect, lib, normalised, stagger_ms=stagger_ms)
        beats = [bc.compile(b, c, o, i) for i, (b, c, o) in enumerate(zip(film.beats, clocks, offsets))]
        W, H = native.ASPECTS[aspect]['size']
        # The field is dressed once the content is placed: the bloom follows each beat's hero from the
        # previous beat's light, the far-plane shapes take whatever room the content leaves.
        prev_bloom = None
        for bt, btr in zip(beats, film.beats):
            backdrop = _backdrop_layers(film.film_id, btr, (W, H), film.brand)
            sky_concepts = {e.get('concept') for e in ((bt.get('illustration') or {}).get('entities') or []) if e.get('concept')}
            scene = _scene_layers(film.film_id, btr, (W, H), film.brand, sky_concepts)
            atmo_layers = beat_atmosphere(film.film_id, bt, (W, H), bc.safe, prev_bloom, atmosphere)
            prev_bloom = next(L['at'] for L in atmo_layers if L['kind'] == 'bloom')
            # Painter's order inside the bg layer: stage furniture, then the authored world
            # (scene environment and/or diorama planes), then the hero's light over it.
            bt['composition']['background']['layers'] += backdrop + scene + atmo_layers
        phase = fit_phase(music, beats)
        aspect_music = {**music, 'start_offset_ms': phase['start_offset_ms'],
                        'groove': {**phase, 'stagger_ms': stagger_ms, 'stagger_subdivision': subdivision, 'authored_stagger_ms': profile['stagger_ms']}}
        if bc.carried_media:
            film_failures.append(f'{aspect}:MEDIA_PERSISTENCE_UNTERMINATED')
        if bc.carried_illustration:
            film_failures.append(f'{aspect}:ILLUSTRATION_PERSISTENCE_UNTERMINATED')
        motifs = [bt['typography']['motif'] for bt in beats if bt['typography']['motif']]
        if len(motifs) >= 4 and len(set(motifs)) < 2:
            film_warnings.append(f'{aspect}:MOTIF_MONOTONY')
        fails = [f"{bt['beat_id']}:{f}" for bt in beats for f in bt['gate']['failures']]
        film_failures += [f'{aspect}:{f}' for f in fails]
        film_warnings += [f"{aspect}:{bt['beat_id']}:{w}" for bt in beats for w in bt['gate']['warnings']]
        ow, oh = OUTPUT[aspect]
        plans[aspect] = {
            'schema': PLAN_SCHEMA, 'compiler': COMPILER_VERSION, 'film_id': film.film_id, 'aspect': aspect, 'fps': film.fps,
            'canvas': {'w': W, 'h': H}, 'output': {'w': ow, 'h': oh, 'scale': round(ow / W, 4)},
            'brand': asdict(film.brand), 'motion': {**profile, 'stagger_ms': stagger_ms}, 'typography': asdict(film.typography), 'fonts': _fonts(), 'duration_ms': total_ms,
            'illustration_registry': {'path': str(bc.solver.registry.path), 'version': bc.solver.registry.version},
            'voice': {'source': voice_source, 'segments': [
                {'beat_id': s.beat_id, 'source': s.source, 'audio_path': s.audio_path, 'sha256': s.audio_sha256, 'start_ms': o, 'duration_ms': s.duration_ms, 'evidence': s.evidence}
                for s, o in zip(segments, segment_starts)]},
            'timeline': None if timeline is None else {'source': 'MASTER', 'audio_ms': timeline.audio_ms, 'head_pad_ms': timeline.head_pad_ms, 'tail_silence_ms': timeline.tail_silence_ms,
                                                       'tempo': timeline.tempo, 'beats': [{'beat_id': w.beat_id, 'start_ms': w.start_ms, 'end_ms': w.end_ms, 'speech_start_ms': w.speech_start_ms,
                                                                                          'speech_end_ms': w.speech_end_ms, 'budget_met': c.budget_met} for w, c in zip(timeline.windows, clocks)]},
            'music': aspect_music, 'mix': MIX, 'atmosphere': atmosphere,
            'surfaces': {'grain': community_surface('surface', (film.world.grain if film.world else None) or 'grain-fine'),
                         'paper': community_surface('texture', 'paper006-color')},
            'book': (film.world.book if film.world else False),
            'motif': ({'corner': film.world.motif['corner'], 'concept': film.world.motif['concept'], 'via': film.world.motif.get('via'),
                       'asset': film.world.motif.get('asset'), 'photo': film.world.motif.get('photo'), 'word': film.world.motif.get('word')}
                      if film.world and film.world.motif else None),
            'beats': beats, 'captions': _captions(beats),
            'captions_policy': 'kinetic' if film.brand.finish == 'PRODUCT_COLLAGE' else 'burned',
            'gate': {'status': 'FAIL' if fails else 'PASS', 'failures': fails},
            'provenance': {
                'treatment_sha256': treatment_sha, 'creative_authority': 'NEXMIND_P8', 'compiler_role': 'DETERMINISTIC_PLAN_COMPILER', 'renderer_role': 'EXECUTION_ONLY',
                'voice_timing': voice_source, 'commercial_certification': False if voice_source == 'FIXTURE' else None,
                'authorities': json.loads((Path(__file__).parent / 'authorities' / 'AUTHORITY_PROVENANCE.json').read_text())['files'],
                'sound_library': {'root': str(root) if root else None, 'version': lib.version if lib else None},
                'media_assets': [{'asset_id': m.asset_id, 'kind': m.kind, 'rights': m.rights, 'original_path': nm.original_path, 'original_sha256': nm.original_sha256,
                                  'render_path': nm.render_path, 'render_sha256': nm.render_sha256, 'render_codec': nm.render_codec, 'normalised': nm.normalised}
                                 for m in film.media_library.values() for nm in [normalised[m.asset_id]]],
            },
        }
    settle_descriptors(plans)
    gate = {'status': 'FAIL' if film_failures else 'PASS', 'failures': film_failures, 'warnings': sorted(set(film_warnings)), 'duration_ms': total_ms,
            'aspects': list(plans), 'voice_source': voice_source, 'beats': len(film.beats)}
    return {'plans': plans, 'gate': gate, 'voice': [asdict(s) for s in segments]}


def write_outputs(result: Dict[str, Any], out_dir: Path) -> Dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for aspect, plan in result['plans'].items():
        p = out_dir / f'plan_{aspect}.json'
        p.write_text(json.dumps(plan, indent=1))
        written[aspect] = str(p)
    g = out_dir / 'gate_report.json'
    g.write_text(json.dumps(result['gate'], indent=1))
    written['gate'] = str(g)
    return written
