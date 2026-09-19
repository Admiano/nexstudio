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
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .authorities import editorial_motion_ensemble_director_v1 as ens
from .authorities import kinetic_typography_performance_authority_v3 as ktp
from .authorities import native_three_aspect_composition_authority_v2 as native
from .contracts import BeatTreatment, FilmTreatment, TreatmentError
from .figures import resolve_figure
from .illustration import IllustrationRegistry, IllustrationSolver, carried_copy
from .media import NormalisedMedia, normalise_media
from .sound import SoundLibrary, bind_beat_sound, bind_film_music, community_surface, library_root
from .master_timeline import MasterTimeline, extend_tail, resolve_master
from .timing import BeatClock, CASCADE_SETTLE_MS, EXIT_MS, LAND_SETTLE_MS, LEAD_IN_MS, MIN_HOLD_MS, beat_clock, find_landing, normalise, readable_close_floor, retime_choreography, window_clock
from .typefit import fit_text
from .voice import VoiceSegment, resolve_voice

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


def _sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _box(x: float, y: float, w: float, h: float) -> Dict[str, float]:
    return {'x': round(x, 1), 'y': round(y, 1), 'w': round(max(0.0, w), 1), 'h': round(max(0.0, h), 1)}


def _inside(a: Dict[str, float], b: Dict[str, float], tol: float = 1.0) -> bool:
    return a['x'] >= b['x'] - tol and a['y'] >= b['y'] - tol and a['x'] + a['w'] <= b['x'] + b['w'] + tol and a['y'] + a['h'] <= b['y'] + b['h'] + tol


def _background_layers(render_bg: str, authored: str, stage: Dict[str, float], safe: Dict[str, float], canvas: Tuple[int, int], beat_index: int = 0) -> List[Dict[str, Any]]:
    """Structural stage furniture under the content, derived from the authored background template.

    The runtime renders these verbatim; `kind` selects the draw recipe and all geometry is absolute
    canvas coordinates so the layers land exactly under the zones they dress."""
    W, H = canvas
    st = dict(stage)
    layers: List[Dict[str, Any]] = []
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
            layers.append({'kind': 'arc', 'bbox': dict(safe), 'opacity': 1.0, 'corner': beat_index % 4})
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


def _fonts() -> Dict[str, Any]:
    files = {'display': 'InterVariable.woff2', 'display_italic': 'InterVariable-Italic.woff2', 'data': 'JetBrainsMono-SemiBold.ttf'}
    return {k: {'file': f, 'sha256': _sha_file(FONTS / f)} for k, f in files.items()} | {
        'licenses': ['INTER-LICENSE-OFL.txt', 'JETBRAINS-MONO-LICENSE-APACHE2.txt'], 'families': {'display': 'Inter Display', 'text': 'Inter', 'data': 'JetBrains Mono'}}


class BeatCompiler:
    def __init__(self, film: FilmTreatment, aspect: str, lib: Optional[SoundLibrary], media: Optional[Dict[str, NormalisedMedia]] = None):
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
        self.solver = IllustrationSolver(aspect, (self.W, self.H), IllustrationRegistry(), film.media_library, self.media_files, film.brand.accent)

    # ------------------------------------------------------------------ helpers
    def _native_treatment(self, b: BeatTreatment) -> str:
        t = NATIVE_TREATMENT[b.pattern]
        il = b.illustration
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
        gaps = [blocks[by_y[i + 1]]['bbox']['y'] - (blocks[by_y[i]]['bbox']['y'] + blocks[by_y[i]]['bbox']['h']) for i in range(len(by_y) - 1)]
        y = blocks[by_y[0]]['bbox']['y']
        for i, k in enumerate(by_unit):
            blocks[k]['bbox'] = {**blocks[k]['bbox'], 'y': round(y, 1)}
            y += blocks[k]['bbox']['h'] + (gaps[i] if i < len(gaps) else 0.0)

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
                bl['cascade_end_ms'] = last + CASCADE_SETTLE_MS
                limit = bl['exit_ms'] - 360 if bl.get('exit_ms') else clock.duration_ms - (clock.exit_ms + 40 if clock.fixed_window else 760)
                if last > limit:
                    # Compress the cascade so the phrase finishes reading before it leaves or the beat ends.
                    span = max(1, last - start)
                    room = max(WORD_CASCADE_MIN_STEP_MS * len(words), limit - start)
                    for w in words:
                        w['start_ms'] = int(start + (w['start_ms'] - start) * room / span)
                    bl['cascade_end_ms'] = words[-1]['start_ms'] + CASCADE_SETTLE_MS
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
            ar = asset.width / asset.height
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
                # The empty evidence card is set-dressing: it enters inside the lead-in when the
                # exhibit itself lands late, so a cut never opens on bare paper.
                'chrome_ms': LEAD_IN_MS // 4 if enter > LEAD_IN_MS + 320 else None,
            }
            self.carried_media = media if b.media.persist_to and b.media.persist_to != b.beat_id else None
            return media
        carried = dict(self.carried_media)
        asset = self.film.media_library[carried['asset_id']]
        bbox = _contain(zone, asset.width / asset.height, min(1.0, comp['visual_hints']['evidence_scale']))
        carried.update({'bbox': bbox, 'zone': zone, 'enter_ms': 0, 'enter_duration_ms': 0, 'chrome_ms': None, 'carried_from': carried.get('carried_from') or self.carried_media['asset_id'],
                        'reframe': {'from': self.carried_media['bbox'], 'start_ms': 0, 'end_ms': 420} if self.carried_media['bbox'] != bbox else None})
        if carried['persist_to'] == b.beat_id:
            self.carried_media = None
        else:
            self.carried_media = carried
        return carried

    def _figure(self, b: BeatTreatment, comp: Dict[str, Any], clock: BeatClock, ensemble: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not b.figure:
            return None
        zone = comp['visual_zone']
        text_cx = comp['text_zone']['x'] + comp['text_zone']['w'] / 2
        zone_cx = zone['x'] + zone['w'] / 2
        # Library artwork faces the viewer's left; mirror when the copy sits to the figure's right.
        facing_left = not (b.figure.facing == 'TOWARD_TEXT' and text_cx > zone_cx + 40)
        if b.figure.facing == 'AWAY':
            facing_left = text_cx > zone_cx
        fig = resolve_figure(b.figure, b.beat_id, self.film.film_id, self.film.brand, facing_left=facing_left)
        bbox = _contain(zone, fig['composition']['aspect'], 1.0, anchor='bottom')
        ev = next((e for e in ensemble['events'] if e['channel'] == 'CHARACTER'), None)
        enter = ev['start_ms'] if ev else min(clock.duration_ms - 900, max(clock.landings_ms or [LEAD_IN_MS]) + 200)
        # A performer is part of the stage, not a payload: when the character event sits late the figure
        # still arrives inside the lead-in rather than leaving the stage empty.
        enter = max(LEAD_IN_MS // 4 + 20, min(int(enter), LEAD_IN_MS + 220))
        fig.update({'bbox': bbox, 'zone': zone, 'enter_ms': int(enter), 'enter_duration_ms': 300, 'entrance': 'SETTLE_RISE', 'ground_line': round(bbox['y'] + bbox['h'], 1)})
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
        figure = self._figure(b, comp, clock, ensemble)
        data = self._data(b, comp, clock)
        illustration, ilf = self._illustration(b, comp, clock)
        failures += ilf
        if illustration:
            if not _inside(illustration['zone'], self.frame, 2):
                failures.append('ILLUSTRATION_OUTSIDE_FRAME')
            for ent in illustration['entities']:
                boxes = [ent['art_bbox']] + ([ent['label']['bbox']] if ent.get('label') else [])
                for bx in boxes:
                    for bl in typ['blocks']:
                        if _overlap(bx, bl['bbox']) > 0:
                            failures.append(f"ILLUSTRATION_COLLIDES_TEXT:{ent['id']}:{bl['unit_index']}")
            if figure and any(_overlap(figure['bbox'], e['art_bbox']) > 0 for e in illustration['entities']):
                failures.append('FIGURE_COLLIDES_ILLUSTRATION')
            if not illustration['carried'] and illustration['state_changes'] == 0 and b.dominant_layer in ('ILLUSTRATION', 'HYBRID'):
                warnings.append('ILLUSTRATION_WITHOUT_STATE_CHANGE')

        # Ownership: nothing visual may sit on text, and every element stays in the safe frame.
        for name, el in (('MEDIA', media), ('FIGURE', figure)):
            if el:
                if not _inside(el['bbox'], self.frame, 2):
                    failures.append(f'{name}_OUTSIDE_FRAME')
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
        if media and media.get('persist_to') and media['persist_to'] != b.beat_id:
            transition = {'mode': 'EVIDENCE_PERSISTENCE', 'owner': 'MEDIA', 'start_ms': clock.duration_ms - clock.exit_ms, 'end_ms': clock.duration_ms}
        elif illustration and illustration.get('persist_to') and illustration['persist_to'] != b.beat_id:
            transition = {'mode': 'ILLUSTRATION_PERSISTENCE', 'owner': 'ILLUSTRATION', 'start_ms': clock.duration_ms - clock.exit_ms, 'end_ms': clock.duration_ms}
        elif typ['transition_carrier']:
            transition = {**typ['transition_carrier'], 'owner': 'TEXT'}
            if clock.fixed_window:
                transition['start_ms'] = max(transition['start_ms'], clock.duration_ms - clock.exit_ms)
        else:
            transition = {'mode': 'SETTLE_CUT', 'owner': 'NONE', 'start_ms': clock.duration_ms - min(200, clock.exit_ms), 'end_ms': clock.duration_ms}

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
            candidates.append({'event': 'EVIDENCE_LAND', 'at_ms': media['enter_ms'] + media['enter_duration_ms'], 'strength': 0.86})
        if media and media.get('reframe'):
            candidates.append({'event': 'SPATIAL_RECONFIGURE', 'at_ms': 0, 'strength': 0.7})
        if data:
            candidates.append({'event': 'DATA_LAND', 'at_ms': data['enter_ms'] + data['enter_duration_ms'], 'strength': 0.8})
        if illustration and not illustration['carried']:
            for o in illustration['ops']:
                if o['state_change'] and o['op'] != 'INK':
                    candidates.append({'event': 'KEYWORD_HIT' if o['op'] == 'STRIKE' else 'EVIDENCE_LAND', 'at_ms': o['end_ms'], 'strength': 0.7})
                if o['op'] == 'INK':
                    candidates.append({'event': 'INK_WRITE', 'at_ms': o['start_ms'], 'strength': 0.72})
                if o['op'] in ('DRAW', 'CONNECT', 'TRACE'):
                    candidates.append({'event': 'LINE_DRAW', 'at_ms': o['end_ms'], 'strength': 0.5})
                if o['op'] == 'EMIT':
                    candidates.append({'event': 'EMIT_CONFIRM', 'at_ms': o['end_ms'], 'strength': 0.75})
                if o['op'] == 'COUNT':
                    candidates.append({'event': 'COUNT_TICK', 'at_ms': o['end_ms'], 'strength': 0.5})
                if o['op'] == 'TRAVEL':
                    candidates.append({'event': 'LOUPE_TRAVEL', 'at_ms': o['end_ms'], 'strength': 0.55})
        if transition['mode'] in ('TEXT_MASK_WIPE', 'LABEL_EXPAND_WIPE'):
            candidates.append({'event': 'TRANSITION_CARRIER', 'at_ms': transition['start_ms'], 'strength': 0.6})
        sound = bind_beat_sound(self.lib, self.film.film_id, b.beat_id, beat_offset_ms, b.dominant_layer, b.energy, candidates)
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
                                                       'layers': _background_layers(render_bg, bg, stage_zone, self.safe, (self.W, self.H), beat_index),
                                                       'finish': self.film.brand.finish},
                'native_profile': comp['native_profile'], 'derived_by_scaling': comp['derived_by_scaling'], 'authority': comp['authority_version'],
            },
            'typography': typ, 'ensemble': {'events': ensemble['events'], 'dominant_sequence': ensemble['dominant_sequence'], 'hold_window': ensemble['hold_window'], 'transition_window': ensemble['transition_window']},
            'media': media, 'figure': figure, 'data': data, 'illustration': illustration, 'transition': transition, 'sound': sound,
            'gate': {'status': 'FAIL' if failures else 'PASS', 'failures': failures, 'warnings': sorted(set(warnings))},
        }


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
        need = max((max(c.landings_ms) + LAND_SETTLE_MS) if c.landings_ms else 0, (c.words[-1].start_ms + CASCADE_SETTLE_MS) if c.words else 0) + MIN_HOLD_MS + EXIT_MS
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
    film_failures: List[str] = []
    film_warnings: List[str] = []
    for aspect in film.aspects:
        bc = BeatCompiler(film, aspect, lib, normalised)
        beats = [bc.compile(b, c, o, i) for i, (b, c, o) in enumerate(zip(film.beats, clocks, offsets))]
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
        W, H = native.ASPECTS[aspect]['size']
        ow, oh = OUTPUT[aspect]
        plans[aspect] = {
            'schema': PLAN_SCHEMA, 'compiler': COMPILER_VERSION, 'film_id': film.film_id, 'aspect': aspect, 'fps': film.fps,
            'canvas': {'w': W, 'h': H}, 'output': {'w': ow, 'h': oh, 'scale': round(ow / W, 4)},
            'brand': asdict(film.brand), 'typography': asdict(film.typography), 'fonts': _fonts(), 'duration_ms': total_ms,
            'illustration_registry': {'path': str(bc.solver.registry.path), 'version': bc.solver.registry.version},
            'voice': {'source': voice_source, 'segments': [
                {'beat_id': s.beat_id, 'source': s.source, 'audio_path': s.audio_path, 'sha256': s.audio_sha256, 'start_ms': o, 'duration_ms': s.duration_ms, 'evidence': s.evidence}
                for s, o in zip(segments, segment_starts)]},
            'timeline': None if timeline is None else {'source': 'MASTER', 'audio_ms': timeline.audio_ms, 'head_pad_ms': timeline.head_pad_ms, 'tail_silence_ms': timeline.tail_silence_ms,
                                                       'tempo': timeline.tempo, 'beats': [{'beat_id': w.beat_id, 'start_ms': w.start_ms, 'end_ms': w.end_ms, 'speech_start_ms': w.speech_start_ms,
                                                                                          'speech_end_ms': w.speech_end_ms, 'budget_met': c.budget_met} for w, c in zip(timeline.windows, clocks)]},
            'music': bind_film_music(film.film_id),
            'surfaces': {'grain': community_surface('surface', 'grain-fine'), 'paper': community_surface('texture', 'paper006-color')},
            'beats': beats, 'captions': _captions(beats),
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
