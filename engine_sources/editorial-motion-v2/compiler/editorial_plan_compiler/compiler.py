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
from .media import NormalisedMedia, normalise_media
from .sound import SoundLibrary, bind_beat_sound, library_root
from .timing import BeatClock, LEAD_IN_MS, MIN_HOLD_MS, beat_clock, retime_choreography
from .typefit import fit_text
from .voice import VoiceSegment, resolve_voice

COMPILER_VERSION = 'EDITORIAL_PLAN_COMPILER_V2.0'
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
SHOT_ROLE = {'TEXT': 'TEXT_LED', 'EVIDENCE': 'HYBRID', 'FIGURE': 'CHARACTER_EMPHASIS', 'DATA': 'HYBRID', 'QUIET': 'TEXT_LED'}
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

    # ------------------------------------------------------------------ helpers
    def _visual_kind(self, b: BeatTreatment) -> str:
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
        for blk in perf['text_blocks']:
            bbox = _remap(blk['bbox'], ktp_zone, native_zone)
            # Edge-crop heroes may reach the safe edge but never leave the safe frame.
            bbox['x'] = max(self.safe['x'], bbox['x'])
            bbox['w'] = min(bbox['w'], self.safe['x'] + self.safe['w'] - bbox['x'])
            max_lines = self.hero_max_lines if blk['role'] == 'hero' else MAX_LINES[blk['role']]
            fit = fit_text(blk['text'], bbox, blk['role'], blk['weight'], (self.W, self.H), max_lines=max_lines)
            blocks.append({**blk, 'bbox': bbox, 'fit': asdict(fit)})
        hero_px = max((bl['fit']['font_px'] for bl in blocks if bl['role'] == 'hero'), default=0.0)
        for bl in blocks:
            f = bl['fit']
            if bl['role'] == 'support' and hero_px and f['font_px'] > hero_px / HERO_SUPPORT_MIN_RATIO:
                refit = fit_text(bl['text'], {**bl['bbox'], 'h': hero_px / HERO_SUPPORT_MIN_RATIO * f['line_height'] * len(f['lines'])}, 'support', bl['weight'], (self.W, self.H), max_lines=MAX_LINES['support'])
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
        events = retime_choreography(perf['choreography']['base']['events'], clock.landings_ms, clock.duration_ms)
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
        typ = {
            'motif': perf['motif'], 'spatial_preset': perf['spatial_preset'], 'blocks': blocks, 'events': events, 'performance_events': perf_events,
            'transition_carrier': perf['transition_carrier'], 'reading_order': perf['reading_order'], 'focal_order': perf['focal_order'], 'metrics': perf['metrics'],
        }
        return typ, failures, warnings

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
            }
            self.carried_media = media if b.media.persist_to and b.media.persist_to != b.beat_id else None
            return media
        carried = dict(self.carried_media)
        asset = self.film.media_library[carried['asset_id']]
        bbox = _contain(zone, asset.width / asset.height, min(1.0, comp['visual_hints']['evidence_scale']))
        carried.update({'bbox': bbox, 'zone': zone, 'enter_ms': 0, 'enter_duration_ms': 0, 'carried_from': carried.get('carried_from') or self.carried_media['asset_id'],
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
        return {'kind': d.kind, 'zone': zone, 'blocks': blocks, 'enter_ms': int(enter), 'enter_duration_ms': 340, 'stagger_ms': stagger, 'style': 'COUNT_IN' if d.kind == 'STAT' else 'SETTLE'}

    # ------------------------------------------------------------------ beat
    def compile(self, b: BeatTreatment, clock: BeatClock, beat_offset_ms: int) -> Dict[str, Any]:
        failures: List[str] = []
        warnings: List[str] = []
        comp = native.compose(self.aspect, NATIVE_TREATMENT[b.pattern], self._visual_kind(b))
        object_present = bool(b.media or b.figure or b.data or self.carried_media)
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
            illustration_motion_count=1 if (b.media or b.data or self.carried_media) else 0, character_present=b.figure is not None,
            transition_mode='TEXT_CARRIER' if (typ['transition_carrier'] and not b.media) else 'OBJECT_OR_TEXT_CARRIER',
            beat_energy=b.energy, audio_accent_times=[l for l in clock.landings_ms if 0 < l < clock.duration_ms]))
        ensemble = asdict(ensemble_plan)
        warnings += ensemble['warnings']

        media = self._media(b, comp, clock, typ)
        figure = self._figure(b, comp, clock, ensemble)
        data = self._data(b, comp, clock)

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
            transition = {'mode': 'EVIDENCE_PERSISTENCE', 'owner': 'MEDIA', 'start_ms': clock.duration_ms - 320, 'end_ms': clock.duration_ms}
        elif typ['transition_carrier']:
            transition = {**typ['transition_carrier'], 'owner': 'TEXT'}
        else:
            transition = {'mode': 'SETTLE_CUT', 'owner': 'NONE', 'start_ms': clock.duration_ms - 200, 'end_ms': clock.duration_ms}

        # The settled hold is the window in which every authored element has finished arriving and nothing has
        # started leaving; typography, ensemble and object channels are reconciled to that single window.
        settled = [e['end_ms'] for e in typ['events'] + typ['performance_events'] if e['unit_index'] != -1]
        if media:
            settled.append(media['enter_ms'] + media['enter_duration_ms'])
        if figure:
            settled.append(figure['enter_ms'] + figure['enter_duration_ms'])
        if data:
            settled.append(data['enter_ms'] + data['enter_duration_ms'] + data['stagger_ms'] * max(0, len(data['blocks']) - 1))
        leaving = [transition['start_ms']]
        leaving += [e['start_ms'] for e in typ['events'] if e['event'] == 'EXIT']
        hold_start, hold_end = int(max(settled)), int(min(leaving))
        ensemble['hold_window'] = {'start_ms': hold_start, 'end_ms': hold_end}
        hold = next((e for e in typ['events'] if e['event'] == 'HOLD'), None)
        if hold:
            hold['start_ms'], hold['end_ms'] = hold_start, hold_end
        if hold_end - hold_start < MIN_HOLD_MS:
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
        if transition['mode'] in ('TEXT_MASK_WIPE', 'LABEL_EXPAND_WIPE'):
            candidates.append({'event': 'TRANSITION_CARRIER', 'at_ms': transition['start_ms'], 'strength': 0.6})
        sound = bind_beat_sound(self.lib, self.film.film_id, b.beat_id, beat_offset_ms, b.dominant_layer, b.energy, candidates)
        if self.lib is None and candidates and b.dominant_layer != 'QUIET':
            warnings.append('SOUND_LIBRARY_MISSING')

        bg = (comp.get('authentic_v2_plan') or {}).get('background_template') or 'SOFT_FIELD'
        render_bg = 'SPOTLIGHT_STAGE' if figure else ('CARD_STAGE' if (media or data) else 'SOFT_FIELD')
        return {
            'beat_id': b.beat_id, 'beat_type': b.beat_type, 'pattern': b.pattern, 'dominant_layer': b.dominant_layer, 'shot_role': shot_role,
            'start_ms': beat_offset_ms, 'duration_ms': clock.duration_ms, 'energy': b.energy,
            'narration': b.narration, 'words': [{'text': w.text, 'start_ms': w.start_ms, 'end_ms': w.end_ms} for w in clock.words],
            'landings': [{'unit_index': i, 'at_ms': l, 'source': s} for i, (l, s) in enumerate(zip(clock.landings_ms, clock.landing_source))],
            'composition': {
                'layout_family': comp['layout_family'], 'treatment': comp['treatment'], 'text_zone': comp['text_zone'], 'visual_zone': comp['visual_zone'],
                'safe_area': self.safe, 'background': {'template': bg, 'render': render_bg, 'stage': (media or figure or data or {}).get('zone')},
                'native_profile': comp['native_profile'], 'derived_by_scaling': comp['derived_by_scaling'], 'authority': comp['authority_version'],
            },
            'typography': typ, 'ensemble': {'events': ensemble['events'], 'dominant_sequence': ensemble['dominant_sequence'], 'hold_window': ensemble['hold_window'], 'transition_window': ensemble['transition_window']},
            'media': media, 'figure': figure, 'data': data, 'transition': transition, 'sound': sound,
            'gate': {'status': 'FAIL' if failures else 'PASS', 'failures': failures, 'warnings': sorted(set(warnings))},
        }


def _captions(beats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    caps = []
    for bt in beats:
        for w in bt['words']:
            caps.append({'beat_id': bt['beat_id'], 'text': w['text'], 'start_ms': bt['start_ms'] + w['start_ms'], 'end_ms': bt['start_ms'] + w['end_ms']})
    return caps


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
    segments = resolve_voice(film.beats, film.voice, work_dir, base_dir, film.film_id)
    seg_by_id: Dict[str, VoiceSegment] = {s.beat_id: s for s in segments}
    clocks: List[BeatClock] = []
    for b in film.beats:
        seg = seg_by_id[b.beat_id]
        clocks.append(beat_clock(b.beat_id, [u.text for u in b.units], [u.anchor_word for u in b.units], seg.alignment, seg.source, b.min_duration_ms, b.energy))
    offsets: List[int] = []
    t = 0
    for c in clocks:
        offsets.append(t)
        t += c.duration_ms
    total_ms = t

    root = library_root()
    lib = SoundLibrary(root) if root else None
    voice_source = str(film.voice.get('source') or 'FIXTURE').upper()
    plans: Dict[str, Any] = {}
    film_failures: List[str] = []
    film_warnings: List[str] = []
    for aspect in film.aspects:
        bc = BeatCompiler(film, aspect, lib, normalised)
        beats = [bc.compile(b, c, o) for b, c, o in zip(film.beats, clocks, offsets)]
        if bc.carried_media:
            film_failures.append(f'{aspect}:MEDIA_PERSISTENCE_UNTERMINATED')
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
            'brand': asdict(film.brand), 'fonts': _fonts(), 'duration_ms': total_ms,
            'voice': {'source': voice_source, 'segments': [
                {'beat_id': s.beat_id, 'source': s.source, 'audio_path': s.audio_path, 'sha256': s.audio_sha256, 'start_ms': o + LEAD_IN_MS, 'duration_ms': s.duration_ms, 'evidence': s.evidence}
                for s, o in zip(segments, offsets)]},
            'music': {'slot': 'BACKGROUND_MUSIC', 'status': 'SILENT_UNTIL_RIGHTS_CLEAN_SOURCE_SELECTED', 'duck_under_voice_db': -14, 'path': None},
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
