"""Editorial treatment contract: what NexMind P8 hands the compiler.

P8 owns every creative decision expressed here. The compiler validates the
decision, refuses anything outside the bounded vocabulary, and turns it into
geometry and timing. Nothing in this module reads the wording of the script to
route layout, motif, figure or sound; wording is payload.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

AUTHORITIES = Path(__file__).resolve().parent / 'authorities'
GRAMMAR = json.loads((AUTHORITIES / 'REFERENCE_EDITORIAL_MOTION_GRAMMAR_V1.json').read_text())

SCHEMA = 'NexStudioEditorialTreatmentV2'
ASPECTS = ('9x16', '1x1', '16x9')
BEAT_TYPES = ('HOOK', 'SETUP', 'CONTRAST', 'EXPLANATION', 'PROOF', 'LIST', 'REFRAME', 'EMPHASIS', 'PAYOFF', 'CTA')
PATTERNS = tuple(p['id'] for p in GRAMMAR['patterns'])
PATTERN_LAYER = {p['id']: p['dominant_layer'] for p in GRAMMAR['patterns']}
DOMINANT_LAYERS = ('TEXT', 'EVIDENCE', 'FIGURE', 'DATA', 'QUIET')
UNIT_ROLES = ('hero', 'support', 'label')
SEMANTIC_ROLES = ('statement', 'setup', 'contrast', 'proof', 'punch', 'qualifier', 'action', 'evidence')
MEDIA_KINDS = ('IMAGE', 'SCREENSHOT', 'DOCUMENT', 'VIDEO')
MEDIA_ROLES = ('EVIDENCE', 'PROOF', 'CONTEXT')
FIGURE_POSTURES = ('standing', 'sitting')
FIGURE_FACINGS = ('TOWARD_TEXT', 'TOWARD_EVIDENCE', 'CAMERA', 'AWAY')
FINISHES = ('EDITORIAL_FLAT', 'PAPER')
DATA_KINDS = ('STAT', 'COMPARISON', 'SEQUENCE')


class TreatmentError(ValueError):
    """The treatment is outside the bounded vocabulary. Compiler fails closed."""

    def __init__(self, code: str, detail: str, beat_id: str = ''):
        super().__init__(f'{code}: {detail}' + (f' (beat {beat_id})' if beat_id else ''))
        self.code = code
        self.detail = detail
        self.beat_id = beat_id


def _need(cond: bool, code: str, detail: str, beat_id: str = '') -> None:
    if not cond:
        raise TreatmentError(code, detail, beat_id)


def _unit(v: Any) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class DisplayUnit:
    text: str
    role: str = 'hero'
    emphasis: float = 0.5
    semantic_role: str = 'statement'
    replace_group: Optional[str] = None
    can_promote: bool = True
    italic: bool = False
    anchor_word: Optional[str] = None  # narration word the unit lands on; defaults to its own first word

    @classmethod
    def parse(cls, d: Dict[str, Any], beat_id: str) -> 'DisplayUnit':
        text = ' '.join(str(d.get('text') or '').split())
        _need(bool(text), 'DISPLAY_UNIT_EMPTY', 'display unit has no authored text', beat_id)
        role = str(d.get('role') or 'hero')
        _need(role in UNIT_ROLES, 'DISPLAY_UNIT_ROLE_UNKNOWN', role, beat_id)
        sem = str(d.get('semantic_role') or 'statement')
        _need(sem in SEMANTIC_ROLES, 'DISPLAY_UNIT_SEMANTIC_ROLE_UNKNOWN', sem, beat_id)
        return cls(
            text=text,
            role=role,
            emphasis=_unit(d.get('emphasis', 0.5)),
            semantic_role=sem,
            replace_group=(str(d['replace_group']) if d.get('replace_group') else None),
            can_promote=bool(d.get('can_promote', True)),
            italic=bool(d.get('italic', False)),
            anchor_word=(str(d['anchor_word']).strip() or None) if d.get('anchor_word') else None,
        )

    def ktp_unit(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'role': self.role,
            'emphasis': self.emphasis,
            'semantic_role': self.semantic_role,
            'replace_group': self.replace_group,
            'can_promote': self.can_promote,
            'italic': self.italic,
        }


@dataclass
class FigureDirective:
    """A still Open Peeps figure appears only when the beat is about a person's state."""

    valence: float  # -1 .. 1
    arousal: float  # 0 .. 1
    posture: str = 'standing'
    energy: float = 0.5
    formality: float = 0.5
    facing: str = 'TOWARD_TEXT'
    justification: str = ''

    @classmethod
    def parse(cls, d: Dict[str, Any], beat_id: str) -> 'FigureDirective':
        posture = str(d.get('posture') or 'standing')
        _need(posture in FIGURE_POSTURES, 'FIGURE_POSTURE_UNKNOWN', posture, beat_id)
        facing = str(d.get('facing') or 'TOWARD_TEXT')
        _need(facing in FIGURE_FACINGS, 'FIGURE_FACING_UNKNOWN', facing, beat_id)
        just = ' '.join(str(d.get('justification') or '').split())
        _need(bool(just), 'FIGURE_UNJUSTIFIED', 'figure directive must state the human state it embodies', beat_id)
        return cls(
            valence=max(-1.0, min(1.0, float(d.get('valence', 0)))),
            arousal=_unit(d.get('arousal', 0.5)),
            posture=posture,
            energy=_unit(d.get('energy', 0.5)),
            formality=_unit(d.get('formality', 0.5)),
            facing=facing,
            justification=just,
        )


@dataclass
class MediaDirective:
    asset_id: str
    role: str = 'EVIDENCE'
    focus: Optional[Dict[str, float]] = None  # normalised region of interest inside the asset
    persist_to: Optional[str] = None  # beat_id through which the media stays on stage
    trim: Optional[Dict[str, float]] = None  # {'start': s, 'end': s} for video

    @classmethod
    def parse(cls, d: Dict[str, Any], beat_id: str) -> 'MediaDirective':
        aid = str(d.get('asset_id') or '').strip()
        _need(bool(aid), 'MEDIA_ASSET_ID_MISSING', 'media directive without asset_id', beat_id)
        role = str(d.get('role') or 'EVIDENCE')
        _need(role in MEDIA_ROLES, 'MEDIA_ROLE_UNKNOWN', role, beat_id)
        focus = d.get('focus')
        if focus is not None:
            _need(all(k in focus for k in ('x', 'y', 'w', 'h')), 'MEDIA_FOCUS_INVALID', 'focus needs x,y,w,h', beat_id)
            focus = {k: _unit(focus[k]) for k in ('x', 'y', 'w', 'h')}
        trim = d.get('trim')
        if trim is not None:
            _need(float(trim.get('end', 0)) > float(trim.get('start', 0)), 'MEDIA_TRIM_INVALID', 'trim end must follow start', beat_id)
            trim = {'start': float(trim['start']), 'end': float(trim['end'])}
        return cls(aid, role, focus, (str(d['persist_to']) if d.get('persist_to') else None), trim)


@dataclass
class DataDirective:
    kind: str
    value: str
    label: str = ''
    secondary: Optional[str] = None

    @classmethod
    def parse(cls, d: Dict[str, Any], beat_id: str) -> 'DataDirective':
        kind = str(d.get('kind') or '')
        _need(kind in DATA_KINDS, 'DATA_KIND_UNKNOWN', kind, beat_id)
        value = ' '.join(str(d.get('value') or '').split())
        _need(bool(value), 'DATA_VALUE_MISSING', 'data directive has no value', beat_id)
        return cls(kind, value, ' '.join(str(d.get('label') or '').split()), (str(d['secondary']) if d.get('secondary') else None))


@dataclass
class BeatTreatment:
    beat_id: str
    beat_type: str
    pattern: str
    dominant_layer: str
    narration: str
    units: List[DisplayUnit]
    figure: Optional[FigureDirective] = None
    media: Optional[MediaDirective] = None
    data: Optional[DataDirective] = None
    energy: float = 0.55
    complexity: float = 0.45
    features: Dict[str, float] = field(default_factory=dict)
    min_duration_ms: int = 0

    @classmethod
    def parse(cls, d: Dict[str, Any]) -> 'BeatTreatment':
        bid = str(d.get('beat_id') or '').strip()
        _need(bool(bid), 'BEAT_ID_MISSING', 'every beat needs a stable beat_id')
        bt = str(d.get('beat_type') or '').upper()
        _need(bt in BEAT_TYPES, 'BEAT_TYPE_UNKNOWN', bt, bid)
        pattern = str(d.get('pattern') or '')
        _need(pattern in PATTERNS, 'PATTERN_UNKNOWN', pattern, bid)
        layer = str(d.get('dominant_layer') or PATTERN_LAYER[pattern])
        _need(layer in DOMINANT_LAYERS, 'DOMINANT_LAYER_UNKNOWN', layer, bid)
        narration = ' '.join(str(d.get('narration') or '').split())
        units = [DisplayUnit.parse(u, bid) for u in (d.get('display_units') or [])]
        figure = FigureDirective.parse(d['figure'], bid) if d.get('figure') else None
        media = MediaDirective.parse(d['media'], bid) if d.get('media') else None
        data = DataDirective.parse(d['data'], bid) if d.get('data') else None

        if layer == 'QUIET':
            _need(len(units) <= 1 and not figure and not media, 'QUIET_BEAT_OVERLOADED', 'QUIET carries at most one unit and no figure/media', bid)
        else:
            _need(bool(units) or media or data, 'BEAT_HAS_NOTHING_TO_SHOW', 'beat has no display units, media or data', bid)
        if layer == 'FIGURE':
            _need(figure is not None, 'FIGURE_LAYER_WITHOUT_FIGURE', 'FIGURE dominant layer requires a figure directive', bid)
        if layer == 'EVIDENCE':
            _need(media is not None, 'EVIDENCE_LAYER_WITHOUT_MEDIA', 'EVIDENCE dominant layer requires a media directive', bid)
        if layer == 'DATA':
            _need(data is not None, 'DATA_LAYER_WITHOUT_DATA', 'DATA dominant layer requires a data directive', bid)
        _need(sum(u.role == 'hero' for u in units) <= 3, 'TOO_MANY_HERO_UNITS', 'more than three hero units in one beat', bid)
        _need(len(units) <= 5, 'TOO_MANY_DISPLAY_UNITS', 'more than five display units in one beat', bid)
        _need(not (figure and media and layer == 'TEXT'), 'TEXT_BEAT_WITH_FIGURE_AND_MEDIA', 'a text-led beat may carry a figure or media, not both', bid)
        feats = {k: _unit(v) for k, v in (d.get('features') or {}).items()}
        return cls(bid, bt, pattern, layer, narration, units, figure, media, data,
                   _unit(d.get('energy', 0.55)), _unit(d.get('complexity', 0.45)), feats, int(d.get('min_duration_ms') or 0))


@dataclass
class MediaAsset:
    asset_id: str
    kind: str
    path: str
    width: int
    height: int
    duration_s: float = 0.0
    rights: str = 'CUSTOMER_SUPPLIED'

    @classmethod
    def parse(cls, d: Dict[str, Any]) -> 'MediaAsset':
        aid = str(d.get('asset_id') or '').strip()
        _need(bool(aid), 'MEDIA_LIBRARY_ASSET_ID_MISSING', 'library asset without id')
        kind = str(d.get('kind') or '')
        _need(kind in MEDIA_KINDS, 'MEDIA_LIBRARY_KIND_UNKNOWN', kind)
        _need(int(d.get('width') or 0) > 0 and int(d.get('height') or 0) > 0, 'MEDIA_LIBRARY_DIMENSIONS_MISSING', aid)
        return cls(aid, kind, str(d.get('path') or ''), int(d['width']), int(d['height']), float(d.get('duration_s') or 0), str(d.get('rights') or 'CUSTOMER_SUPPLIED'))


@dataclass
class Brand:
    ink: str = '#0e0e0e'
    paper: str = '#f7f7f5'
    accent: Optional[str] = None
    finish: str = 'EDITORIAL_FLAT'


@dataclass
class FilmTreatment:
    film_id: str
    beats: List[BeatTreatment]
    aspects: List[str]
    media_library: Dict[str, MediaAsset]
    brand: Brand
    voice: Dict[str, Any]
    fps: int = 30

    @classmethod
    def parse(cls, d: Dict[str, Any]) -> 'FilmTreatment':
        _need(d.get('schema') == SCHEMA, 'TREATMENT_SCHEMA_MISMATCH', f'expected {SCHEMA}, got {d.get("schema")}')
        fid = str(d.get('film_id') or '').strip()
        _need(bool(fid), 'FILM_ID_MISSING', 'film_id required')
        beats = [BeatTreatment.parse(b) for b in (d.get('beats') or [])]
        _need(bool(beats), 'FILM_HAS_NO_BEATS', 'at least one beat required')
        ids = [b.beat_id for b in beats]
        _need(len(ids) == len(set(ids)), 'BEAT_ID_DUPLICATE', 'beat ids must be unique')
        aspects = [str(a) for a in (d.get('aspects') or list(ASPECTS))]
        for a in aspects:
            _need(a in ASPECTS, 'ASPECT_UNKNOWN', a)
        library = {m.asset_id: m for m in (MediaAsset.parse(x) for x in (d.get('media_library') or []))}
        for b in beats:
            if b.media:
                _need(b.media.asset_id in library, 'MEDIA_ASSET_NOT_IN_LIBRARY', b.media.asset_id, b.beat_id)
                if b.media.persist_to:
                    _need(b.media.persist_to in ids, 'MEDIA_PERSIST_TARGET_UNKNOWN', b.media.persist_to, b.beat_id)
                    _need(ids.index(b.media.persist_to) >= ids.index(b.beat_id), 'MEDIA_PERSIST_TARGET_BEHIND', b.media.persist_to, b.beat_id)
                if b.media.trim:
                    _need(library[b.media.asset_id].kind == 'VIDEO', 'MEDIA_TRIM_ON_STILL', b.media.asset_id, b.beat_id)
        brand_d = d.get('brand') or {}
        finish = str(brand_d.get('finish') or 'EDITORIAL_FLAT')
        _need(finish in FINISHES, 'FINISH_UNKNOWN', finish)
        brand = Brand(str(brand_d.get('ink') or '#0e0e0e'), str(brand_d.get('paper') or '#f7f7f5'), brand_d.get('accent'), finish)
        voice = dict(d.get('voice') or {})
        fps = int(d.get('fps') or 30)
        _need(fps in (24, 25, 30, 60), 'FPS_UNSUPPORTED', str(fps))
        return cls(fid, beats, aspects, library, brand, voice, fps)
