"""Editorial treatment contract: what NexMind P8 hands the compiler.

P8 owns every creative decision expressed here. The compiler validates the
decision, refuses anything outside the bounded vocabulary, and turns it into
geometry and timing. Nothing in this module reads the wording of the script to
route layout, motif, figure or sound; wording is payload.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .chassis import CHASSIS

AUTHORITIES = Path(__file__).resolve().parent / 'authorities'
GRAMMAR = json.loads((AUTHORITIES / 'REFERENCE_EDITORIAL_MOTION_GRAMMAR_V1.json').read_text())

SCHEMA = 'NexStudioEditorialTreatmentV2'
ASPECTS = ('9x16', '1x1', '16x9')
BEAT_TYPES = ('HOOK', 'SETUP', 'CONTRAST', 'EXPLANATION', 'PROOF', 'LIST', 'REFRAME', 'EMPHASIS', 'PAYOFF', 'CTA')
PATTERNS = tuple(p['id'] for p in GRAMMAR['patterns'])
PATTERN_LAYER = {p['id']: p['dominant_layer'] for p in GRAMMAR['patterns']}
DOMINANT_LAYERS = ('TEXT', 'ILLUSTRATION', 'HYBRID', 'EVIDENCE', 'FIGURE', 'DATA', 'QUIET')
REVEAL_MODES = ('WORD_CASCADE', 'BLOCK')
# Illustration program: a per-beat visual argument. Forms are topologies, glyphs are drawable
# primitives, ops are timed state changes. None of these names is derived from wording.
ILLUSTRATION_FORMS = ('OBJECT_STAGE', 'PROCESS_PIPELINE', 'RELATIONSHIP', 'STATE_TRANSFORMATION', 'COMPARISON', 'DATA_VISUAL', 'CALLOUT_LENS', 'SIGNAL')
GLYPHS = ('VESSEL', 'NODE', 'CARD', 'LENS', 'CHART_LINE', 'RING', 'PILL', 'PROHIBIT', 'BRACKET', 'BAR', 'ICON', 'MEDIA',
          'ARROW', 'MARK_CIRCLE', 'UNDERLINE', 'BURST', 'CALLOUT', 'STICKY', 'DONUT', 'FRAME', 'TILE', 'CHIP', 'BADGE', 'COUNTER')
# Housings whose only job is to carry a mark; staged without one they read as generated filler.
CARRIER_GLYPHS = ('TILE', 'BADGE', 'CHIP')
# Housings whose label is set inside the body, so a word alone is content.
INSIDE_LABEL_GLYPHS = ('CHIP',)
# Glyphs a `concept` can resolve onto; the housed ones can fall back to a typeset word, a bare
# ICON cannot and must land on a mark.
CONCEPT_GLYPHS = ('ICON', 'TILE', 'BADGE', 'CHIP')
WORD_GLYPHS = ('TILE', 'BADGE', 'CHIP')
ENTITY_KINDS = ('object', 'system', 'state', 'group', 'evidence', 'signal', 'agent')
ENTITY_SIZES = ('hero', 'support', 'minor')
RELATION_TYPES = ('flows_to', 'connects', 'points_at', 'blocks', 'contains', 'compares', 'transforms_into', 'emits_to', 'scans', 'marks')
# Connector dress: default (hand-stroke + arrowhead) vs the product-diagram look — a hairline with
# dot endpoints, optionally dashed straight ('dash') or bowed ('arc').
RELATION_STYLES = ('link', 'dash', 'arc')
OPS = ('FILL', 'DRAW', 'CONNECT', 'EMIT', 'TRAVEL', 'GROW', 'SWAP', 'STRIKE', 'COUNT', 'INK', 'DIM', 'TRACE', 'SETTLE')
OP_DEFAULT_MS = {'FILL': 900, 'DRAW': 520, 'CONNECT': 480, 'EMIT': 1100, 'TRAVEL': 700, 'GROW': 460, 'SWAP': 420, 'STRIKE': 380,
                 'COUNT': 620, 'INK': 320, 'DIM': 320, 'TRACE': 900, 'SETTLE': 360}
# Ops whose visible result is a changed state: the only place the brand accent may appear.
STATE_CHANGE_OPS = ('FILL', 'INK', 'SWAP', 'STRIKE', 'EMIT', 'TRACE')
FORM_MIN_ENTITIES = {'OBJECT_STAGE': 1, 'PROCESS_PIPELINE': 2, 'RELATIONSHIP': 2, 'STATE_TRANSFORMATION': 2, 'COMPARISON': 2,
                     'DATA_VISUAL': 1, 'CALLOUT_LENS': 2, 'SIGNAL': 1}
UNIT_ROLES = ('hero', 'support', 'label')
SEMANTIC_ROLES = ('statement', 'setup', 'contrast', 'proof', 'punch', 'qualifier', 'action', 'evidence')
MEDIA_KINDS = ('IMAGE', 'SCREENSHOT', 'DOCUMENT', 'VIDEO')
MEDIA_ROLES = ('EVIDENCE', 'PROOF', 'CONTEXT')
FIGURE_POSTURES = ('standing', 'sitting')
FIGURE_TRACK_SIDES = ('left', 'right', 'none')
FIGURE_HANDS = ('left', 'right', 'auto')
CAST_MEMBER_CAP = 6
# The world bible: film-level look authored per script, not per style preset.
WORLD_GRAINS = ('grain-fine', 'dots-24', 'grid-24', 'graph-paper', 'hatch-45')
WORLD_CORNERS = ('top-left', 'top-right', 'bottom-left', 'bottom-right')
# Diorama backdrops: stacked paper planes per beat. tone resolves 'auto' by depth (far = pale,
# near = dark), or an authored ink|paper|accent|#hex; band is the plane's vertical slice of the
# stage; depth is its parallax factor — 0 frame-fixed (sky) .. 1 with the content (ground).
BACKDROP_TONES = ('ink', 'paper', 'accent', 'auto')
BACKDROP_PLANE_CAP = 4
HEX_COLOUR_RE = re.compile(r'^#[0-9a-fA-F]{3,8}$')
FIGURE_FACINGS = ('TOWARD_TEXT', 'TOWARD_EVIDENCE', 'CAMERA', 'AWAY')
FINISHES = ('EDITORIAL_FLAT', 'PAPER', 'PRODUCT_COLLAGE')
# Film-level musical intent; the compiler binds a mood-matched CC0 bed of covering duration.
FILM_MOODS = ('bright', 'calm', 'dreamy', 'driving', 'elegant', 'focused', 'jazzy', 'playful', 'quirky', 'tense', 'uplifting', 'warm', 'wistful')
# Motion profile per finish: how elements enter, how far the camera drifts per beat, how cuts dissolve.
#   spring        damping preset every arrival is solved with ('snap' overshoots, 'settle' barely, 'float' never)
#   breathe       idle scale amplitude of a held element (fraction), phase-offset per element
#   label_lag_ms  a label trails its body's arrival by this much — secondary motion
#   motion_blur   gain on the per-frame travel that becomes directional blur (0 disables)
SPRING_PRESETS = ('snap', 'settle', 'float')
MOTION_PROFILES = {
    'EDITORIAL_FLAT': {'entrance': 'settle', 'stagger_ms': 90, 'camera_push': 0.012, 'camera_pan_frac': 0.004, 'transition': 'blur_dissolve', 'blur_px': 6, 'word_landing': 'tonal',
                       'spring': 'settle', 'breathe': 0.006, 'label_lag_ms': 40, 'motion_blur': 0.8, 'media_tilt': 0.0},
    'PAPER': {'entrance': 'settle', 'stagger_ms': 90, 'camera_push': 0.01, 'camera_pan_frac': 0.003, 'transition': 'blur_dissolve', 'blur_px': 5, 'word_landing': 'tonal',
              'spring': 'settle', 'breathe': 0.005, 'label_lag_ms': 40, 'motion_blur': 0.6, 'media_tilt': 0.0},
    'PRODUCT_COLLAGE': {'entrance': 'pop', 'stagger_ms': 80, 'camera_push': 0.03, 'camera_pan_frac': 0.008, 'transition': 'scale_through', 'blur_px': 10, 'word_landing': 'rise',
                        'spring': 'snap', 'breathe': 0.012, 'label_lag_ms': 60, 'motion_blur': 1.0, 'media_tilt': 1.0},
}
# How the film's camera carries one beat into the next; the compiler picks from beat energy,
# a hard cut only when the treatment asks for one (beat.cut = 'hard').
CAMERA_MOVES = ('push_through', 'pull_back', 'drift', 'dissolve', 'cut')
CUT_MODES = ('hard',)
DATA_KINDS = ('STAT', 'COMPARISON', 'SEQUENCE')
# Entity labels are nouns, not captions: no leading article, at most three words, and never a
# restatement of a display unit already set in type on the same beat.
LABEL_MAX_WORDS = 3
LABEL_ARTICLES = ('the', 'a', 'an')


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


def _norm_words(text: str) -> List[str]:
    return [w for w in re.sub(r"[^a-z0-9%]+", ' ', text.lower().replace('\u2019', "'")).split() if w]


def check_labels(units: List['DisplayUnit'], illus: 'IllustrationDirective', beat_id: str) -> None:
    unit_words = [_norm_words(u.text) for u in units]
    for e in illus.entities:
        if not e.label:
            continue
        words = _norm_words(e.label)
        if not words:
            continue
        _need(words[0] not in LABEL_ARTICLES, 'ENTITY_LABEL_ARTICLE', f'{e.id}: label "{e.label}" opens with an article', beat_id)
        _need(len(words) <= LABEL_MAX_WORDS, 'ENTITY_LABEL_LONG', f'{e.id}: label "{e.label}" runs past {LABEL_MAX_WORDS} words', beat_id)
        for uw in unit_words:
            echo = words == uw or (len(words) >= 2 and any(uw[i:i + len(words)] == words for i in range(len(uw) - len(words) + 1)))
            _need(not echo, 'ENTITY_LABEL_ECHO', f'{e.id}: label "{e.label}" restates a display unit', beat_id)


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
    stress: List[str] = field(default_factory=list)  # words set in full ink weight; the rest of the unit reads tonal
    mute: List[str] = field(default_factory=list)    # words set in grey — the benchmark's mixed-tone type
    reveal: Optional[str] = None  # WORD_CASCADE | BLOCK; None inherits the film typography mode

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
            stress=cls._parse_word_list(d.get('stress'), text, 'STRESS', beat_id),
            mute=cls._parse_word_list(d.get('mute'), text, 'MUTE', beat_id),
            reveal=cls._parse_reveal(d.get('reveal'), beat_id),
        )

    @staticmethod
    def _parse_word_list(raw: Any, text: str, field_name: str, beat_id: str) -> List[str]:
        if not raw:
            return []
        code = f'DISPLAY_UNIT_{field_name}'
        _need(isinstance(raw, list), f'{code}_INVALID', f'{field_name.lower()} must be a list of words from the unit text', beat_id)
        words = {_norm(w) for w in text.split()}
        out = []
        for w in raw:
            s = str(w).strip()
            _need(_norm(s) in words, f'{code}_NOT_IN_TEXT', s, beat_id)
            out.append(s)
        return out

    @staticmethod
    def _parse_reveal(raw: Any, beat_id: str) -> Optional[str]:
        if raw is None:
            return None
        r = str(raw).upper()
        _need(r in REVEAL_MODES, 'DISPLAY_UNIT_REVEAL_UNKNOWN', r, beat_id)
        return r

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


def _norm(token: str) -> str:
    return ''.join(ch for ch in token.lower().replace('\u2019', "'") if ch.isalnum() or ch in "'%")


@dataclass
class IllustrationEntity:
    id: str
    kind: str
    glyph: str
    size: str = 'support'
    label: Optional[str] = None       # payload, drawn as a label; never routes
    asset_ref: Optional[str] = None   # ICON: illustration registry id
    media_ref: Optional[str] = None   # MEDIA: media_library asset_id
    params: Dict[str, Any] = field(default_factory=dict)
    concept: Optional[str] = None     # what the mark stands for; resolved to an asset or a typeset word by the compiler

    @classmethod
    def parse(cls, d: Dict[str, Any], beat_id: str) -> 'IllustrationEntity':
        eid = str(d.get('id') or '').strip()
        _need(bool(eid), 'ENTITY_ID_MISSING', 'illustration entity needs an id', beat_id)
        kind = str(d.get('kind') or '')
        _need(kind in ENTITY_KINDS, 'ENTITY_KIND_UNKNOWN', f'{eid}:{kind}', beat_id)
        glyph = str(d.get('glyph') or '').upper()
        _need(glyph in GLYPHS, 'ENTITY_GLYPH_UNKNOWN', f'{eid}:{glyph}', beat_id)
        size = str(d.get('size') or 'support')
        _need(size in ENTITY_SIZES, 'ENTITY_SIZE_UNKNOWN', f'{eid}:{size}', beat_id)
        label = ' '.join(str(d.get('label') or '').split()) or None
        asset_ref = (str(d.get('asset_ref') or '').strip() or None)
        media_ref = (str(d.get('media_ref') or '').strip() or None)
        concept = ' '.join(str(d.get('concept') or '').split()) or None
        if concept is not None:
            _need(glyph in CONCEPT_GLYPHS, 'CONCEPT_ON_UNHOUSED_GLYPH', f'{eid}: concept resolves onto {"/".join(CONCEPT_GLYPHS)} only', beat_id)
            _need(len(concept) <= 40, 'CONCEPT_TOO_LONG', f'{eid}: {concept!r}', beat_id)
        if glyph == 'ICON':
            _need(asset_ref is not None or concept is not None, 'ICON_WITHOUT_ASSET_REF', eid, beat_id)
        if glyph in CARRIER_GLYPHS:
            # A housing is never staged empty: the tile / disc / row exists to carry a mark or a word.
            carries = asset_ref is not None or concept is not None or (label is not None and glyph in INSIDE_LABEL_GLYPHS)
            _need(carries, 'CHASSIS_EMPTY', f'{eid}: {glyph} carries nothing (no asset_ref, no concept, no inside label)', beat_id)
        if glyph == 'MEDIA':
            _need(media_ref is not None, 'MEDIA_GLYPH_WITHOUT_MEDIA_REF', eid, beat_id)
        params = dict(d.get('params') or {})
        if 'chassis' in params:
            _need(glyph == 'MEDIA', 'CHASSIS_ON_NON_MEDIA', f'{eid}: chassis wraps MEDIA only', beat_id)
            _need(str(params['chassis']) in CHASSIS, 'CHASSIS_UNKNOWN', f"{eid}:{params['chassis']}", beat_id)
        if glyph == 'CHART_LINE':
            pts = params.get('points')
            _need(isinstance(pts, list) and len(pts) >= 2, 'CHART_POINTS_MISSING', f'{eid}: CHART_LINE needs >=2 points in 0..1', beat_id)
            params['points'] = [_unit(p) for p in pts]
        if 'level' in params:
            params['level'] = _unit(params['level'])
        if 'count' in params:
            # NODE clusters spend count as drawn parts; readout glyphs (BAR, DONUT) carry the datum.
            params['count'] = max(1, min(12, int(params['count']))) if glyph == 'NODE' else max(1, int(params['count']))
        if 'lines' in params:
            params['lines'] = max(0, min(4, int(params['lines'])))
        if glyph == 'COUNTER':
            _need('count' in params, 'COUNTER_WITHOUT_COUNT', f'{eid}: COUNTER needs params.count', beat_id)
            for k in ('prefix', 'suffix', 'caption'):
                if k in params:
                    params[k] = str(params[k])[:24]
        if 'tone' in params:
            _need(str(params['tone']) in ('light', 'dark'), 'TONE_UNKNOWN', f"{eid}:{params['tone']}", beat_id)
        return cls(eid, kind, glyph, size, label, asset_ref, media_ref, params, concept)


@dataclass
class IllustrationRelation:
    type: str
    source: str
    target: str
    style: Optional[str] = None        # None = drawn stroke; 'link'|'dash'|'arc' = hairline + dot ends

    @classmethod
    def parse(cls, d: Dict[str, Any], ids: set, beat_id: str) -> 'IllustrationRelation':
        t = str(d.get('type') or '')
        _need(t in RELATION_TYPES, 'RELATION_TYPE_UNKNOWN', t, beat_id)
        s, tg = str(d.get('source') or ''), str(d.get('target') or '')
        _need(s in ids and tg in ids, 'RELATION_ENDPOINT_UNKNOWN', f'{s}->{tg}', beat_id)
        _need(s != tg, 'RELATION_SELF_LOOP', s, beat_id)
        style = d.get('style')
        if style is not None:
            style = str(style).lower()
            _need(style in RELATION_STYLES, 'RELATION_STYLE_UNKNOWN', str(style), beat_id)
        return cls(t, s, tg, style)


@dataclass
class IllustrationOp:
    op: str
    target: str
    at: Dict[str, Any]              # {'word': str} | {'unit': int} | {'offset_ms': int}
    duration_ms: int
    value_from: float = 0.0
    value_to: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def parse(cls, d: Dict[str, Any], ids: set, relations: List['IllustrationRelation'], n_units: int, beat_id: str) -> 'IllustrationOp':
        op = str(d.get('op') or '').upper()
        _need(op in OPS, 'OP_UNKNOWN', op, beat_id)
        target = str(d.get('target') or '')
        if op == 'CONNECT' or '->' in target:
            # target is 'source->target' naming an authored relation
            _need('->' in target, 'CONNECT_TARGET_NOT_A_RELATION', target, beat_id)
            _need(op in ('CONNECT', 'STRIKE', 'INK', 'DIM', 'TRACE', 'SETTLE'), 'OP_NOT_APPLICABLE_TO_RELATION', f'{op}:{target}', beat_id)
            s, t = [x.strip() for x in target.split('->', 1)]
            _need(any(r.source == s and r.target == t for r in relations), 'CONNECT_RELATION_UNKNOWN', target, beat_id)
            target = f'{s}->{t}'
        else:
            _need(target in ids, 'OP_TARGET_UNKNOWN', f'{op}:{target}', beat_id)
        at = dict(d.get('at') or {})
        keys = [k for k in ('word', 'unit', 'offset_ms') if k in at]
        _need(len(keys) == 1, 'OP_ANCHOR_INVALID', 'op.at needs exactly one of word | unit | offset_ms', beat_id)
        if 'unit' in at:
            _need(0 <= int(at['unit']) < n_units, 'OP_ANCHOR_UNIT_OUT_OF_RANGE', str(at['unit']), beat_id)
            at = {'unit': int(at['unit'])}
        elif 'word' in at:
            _need(bool(str(at['word']).strip()), 'OP_ANCHOR_WORD_EMPTY', op, beat_id)
            at = {'word': str(at['word']).strip()}
        else:
            at = {'offset_ms': max(0, int(at['offset_ms']))}
        dur = int(d.get('duration_ms') or OP_DEFAULT_MS[op])
        _need(120 <= dur <= 4000, 'OP_DURATION_OUT_OF_RANGE', f'{op}:{dur}', beat_id)
        params = dict(d.get('params') or {})
        if params.get('wipe'):
            _need(op in ('DRAW', 'CONNECT'), 'WIPE_ON_NON_STROKE_OP', f'{op}:{target}', beat_id)
        if op == 'TRAVEL':
            over = params.get('over')
            _need(isinstance(over, list) and len(over) >= 1 and all(o in ids for o in over), 'TRAVEL_OVER_INVALID', 'TRAVEL needs params.over: [entity ids]', beat_id)
        if op == 'COUNT':
            params['count'] = max(1, min(12, int(params.get('count') or 3)))
        return cls(op, target, at, dur, float(d.get('from', 0.0)), float(d.get('to', 1.0)), params)


@dataclass
class IllustrationDirective:
    """A visual argument: entities in a topology, relations between them, and timed state changes."""

    form: str
    entities: List[IllustrationEntity]
    relations: List[IllustrationRelation]
    program: List[IllustrationOp]
    carry_from: Optional[str] = None            # beat_id whose entities (below) persist into this beat
    carry_entities: List[str] = field(default_factory=list)
    persist_to: Optional[str] = None            # beat_id through which this illustration stays on stage

    @classmethod
    def parse(cls, d: Dict[str, Any], n_units: int, beat_id: str) -> 'IllustrationDirective':
        form = str(d.get('form') or '').upper()
        _need(form in ILLUSTRATION_FORMS, 'ILLUSTRATION_FORM_UNKNOWN', form, beat_id)
        ents = [IllustrationEntity.parse(e, beat_id) for e in (d.get('entities') or [])]
        ids = [e.id for e in ents]
        _need(len(ids) == len(set(ids)), 'ENTITY_ID_DUPLICATE', 'entity ids must be unique inside a beat', beat_id)
        _need(len(ents) >= FORM_MIN_ENTITIES[form], 'ILLUSTRATION_TOO_FEW_ENTITIES', f'{form} needs >= {FORM_MIN_ENTITIES[form]} entities', beat_id)
        _need(len(ents) <= 7, 'ILLUSTRATION_TOO_MANY_ENTITIES', 'more than seven entities in one beat', beat_id)
        idset = set(ids)
        rels = [IllustrationRelation.parse(r, idset, beat_id) for r in (d.get('relations') or [])]
        ops = [IllustrationOp.parse(o, idset, rels, n_units, beat_id) for o in (d.get('program') or [])]
        _need(bool(ops), 'ILLUSTRATION_WITHOUT_PROGRAM', 'an illustration must change state at least once while the beat speaks', beat_id)
        _need(len(ops) <= 10, 'ILLUSTRATION_PROGRAM_TOO_LONG', 'more than ten ops in one beat', beat_id)
        if form == 'DATA_VISUAL':
            _need(any(e.glyph in ('CHART_LINE', 'BAR') for e in ents), 'DATA_VISUAL_WITHOUT_CHART', 'DATA_VISUAL needs a CHART_LINE or BAR entity', beat_id)
        if form == 'CALLOUT_LENS':
            _need(any(e.glyph == 'LENS' for e in ents), 'CALLOUT_LENS_WITHOUT_LENS', 'CALLOUT_LENS needs a LENS entity', beat_id)
            _need(any(o.op == 'TRAVEL' for o in ops), 'CALLOUT_LENS_WITHOUT_TRAVEL', 'the lens must TRAVEL', beat_id)
        if form == 'SIGNAL':
            _need(any(e.glyph == 'RING' for e in ents), 'SIGNAL_WITHOUT_RING', 'SIGNAL needs a RING entity', beat_id)
        if form in ('PROCESS_PIPELINE', 'RELATIONSHIP'):
            _need(bool(rels), 'FORM_WITHOUT_RELATIONS', f'{form} needs at least one relation', beat_id)
        if form == 'STATE_TRANSFORMATION':
            _need(any(r.type == 'transforms_into' for r in rels), 'STATE_TRANSFORMATION_WITHOUT_TRANSFORM', 'needs a transforms_into relation', beat_id)
        if form == 'COMPARISON':
            _need(any(r.type == 'compares' for r in rels), 'COMPARISON_WITHOUT_COMPARES', 'needs a compares relation', beat_id)
        heroes = [e for e in ents if e.size == 'hero']
        _need(len(heroes) <= 2, 'ILLUSTRATION_TOO_MANY_HEROES', 'at most two hero entities', beat_id)
        carry = d.get('carry') or {}
        carry_from = (str(carry.get('from_beat') or '').strip() or None)
        carry_entities = [str(x) for x in (carry.get('entities') or [])]
        if carry_entities:
            _need(carry_from is not None, 'CARRY_WITHOUT_SOURCE_BEAT', 'carry.entities needs carry.from_beat', beat_id)
            for ce in carry_entities:
                _need(ce in idset, 'CARRY_ENTITY_NOT_DECLARED', f'{ce} must be declared in this beat too', beat_id)
        return cls(form, ents, rels, ops, carry_from, carry_entities, (str(d['persist_to']) if d.get('persist_to') else None))


@dataclass
class FigureDirective:
    """A still Open Peeps figure appears only when the beat is about a person's state.

    `character` names a film-cast member so the figure keeps one identity across beats; `track`
    slides it on/off the stage (walks between scenes); `prop` pins a concept to a hand anchor;
    `states` morph pose/face parts mid-beat so the performer can react inside its beat."""

    valence: float  # -1 .. 1
    arousal: float  # 0 .. 1
    posture: str = 'standing'
    energy: float = 0.5
    formality: float = 0.5
    facing: str = 'TOWARD_TEXT'
    justification: str = ''
    character: Optional[str] = None
    track: Optional[Dict[str, str]] = None
    prop: Optional[Dict[str, Any]] = None
    states: Optional[List[Dict[str, Any]]] = None
    pose: Optional[str] = None
    face: Optional[str] = None

    @classmethod
    def parse(cls, d: Dict[str, Any], beat_id: str) -> 'FigureDirective':
        posture = str(d.get('posture') or 'standing')
        _need(posture in FIGURE_POSTURES, 'FIGURE_POSTURE_UNKNOWN', posture, beat_id)
        facing = str(d.get('facing') or 'TOWARD_TEXT')
        _need(facing in FIGURE_FACINGS, 'FIGURE_FACING_UNKNOWN', facing, beat_id)
        just = ' '.join(str(d.get('justification') or '').split())
        _need(bool(just), 'FIGURE_UNJUSTIFIED', 'figure directive must state the human state it embodies', beat_id)
        character = (str(d.get('character') or '').strip() or None)
        _need(character is None or len(character) <= 32, 'FIGURE_CHARACTER_INVALID', character or '', beat_id)
        track = d.get('track')
        if track is not None:
            _need(isinstance(track, dict), 'FIGURE_TRACK_INVALID', 'track must be an object', beat_id)
            for k in ('enter', 'exit'):
                side = str(track.get(k) or 'none')
                _need(side in FIGURE_TRACK_SIDES, 'FIGURE_TRACK_SIDE_UNKNOWN', side, beat_id)
                track[k] = side
        prop = d.get('prop')
        if prop is not None:
            _need(isinstance(prop, dict), 'FIGURE_PROP_INVALID', 'prop must be an object', beat_id)
            concept = ' '.join(str(prop.get('concept') or '').split())
            _need(0 < len(concept) <= 40, 'FIGURE_PROP_CONCEPT', concept, beat_id)
            hand = str(prop.get('hand') or 'auto')
            _need(hand in FIGURE_HANDS, 'FIGURE_HAND_UNKNOWN', hand, beat_id)
            prop = {**prop, 'concept': concept, 'hand': hand}
        states = d.get('states')
        if states is not None:
            _need(isinstance(states, list) and 1 <= len(states) <= 3, 'FIGURE_STATES_CAP', 'at most 3 states', beat_id)
            for st in states:
                _need(isinstance(st, dict) and any(st.get(k) for k in ('pose', 'face', 'head')), 'FIGURE_STATE_INVALID', 'a state needs a pose, face or head part to swap', beat_id)
                at = st.get('at') or {}
                _need(sum(1 for k in ('word', 'offset_ms') if k in at) == 1, 'FIGURE_STATE_AT', 'state needs exactly one of word/offset_ms', beat_id)
        return cls(
            valence=max(-1.0, min(1.0, float(d.get('valence', 0)))),
            arousal=_unit(d.get('arousal', 0.5)),
            posture=posture,
            energy=_unit(d.get('energy', 0.5)),
            formality=_unit(d.get('formality', 0.5)),
            facing=facing,
            justification=just,
            character=character,
            track={k: str(v) for k, v in track.items()} if isinstance(track, dict) else None,
            prop=prop,
            states=states,
            pose=(str(d.get('pose') or '').strip() or None),
            face=(str(d.get('face') or '').strip() or None),
        )


@dataclass
class CastMember:
    """A named performer identity held consistent across the film. Optional part pins fix the
    composition/parts; otherwise the member's seed keeps the same picks on every beat it plays."""

    posture: str = 'standing'
    head: Optional[str] = None
    face: Optional[str] = None
    skin: Optional[str] = None
    garment: Optional[str] = None

    @classmethod
    def parse(cls, member_id: str, d: Dict[str, Any]) -> 'CastMember':
        posture = str(d.get('posture') or 'standing')
        _need(posture in FIGURE_POSTURES, 'CAST_POSTURE_UNKNOWN', posture, member_id)
        return cls(posture=posture,
                   head=(str(d.get('head') or '').strip() or None),
                   face=(str(d.get('face') or '').strip() or None),
                   skin=(str(d.get('skin') or '').strip() or None),
                   garment=(str(d.get('garment') or '').strip() or None))


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
    illustration: Optional[IllustrationDirective] = None
    energy: float = 0.55
    complexity: float = 0.45
    features: Dict[str, float] = field(default_factory=dict)
    min_duration_ms: int = 0
    cut: Optional[str] = None  # authored hard cut out of this beat; every other cut is a camera move
    backdrop: Optional[List[Dict[str, Any]]] = None

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
        illus = IllustrationDirective.parse(d['illustration'], len(units), bid) if d.get('illustration') else None

        if layer == 'QUIET':
            _need(len(units) <= 1 and not figure and not media and not illus, 'QUIET_BEAT_OVERLOADED', 'QUIET carries at most one unit and no figure/media/illustration', bid)
        else:
            _need(bool(units) or media or data or illus, 'BEAT_HAS_NOTHING_TO_SHOW', 'beat has no display units, media, data or illustration', bid)
        if layer == 'ILLUSTRATION':
            _need(illus is not None, 'ILLUSTRATION_LAYER_WITHOUT_ILLUSTRATION', 'ILLUSTRATION dominant layer requires an illustration directive', bid)
        if layer == 'HYBRID':
            _need(illus is not None and bool(units), 'HYBRID_LAYER_INCOMPLETE', 'HYBRID needs display units and an illustration', bid)
        if illus is not None:
            _need(media is None and data is None, 'ILLUSTRATION_WITH_MEDIA_OR_DATA', 'media and data belong inside the illustration as MEDIA/CHART entities', bid)
            check_labels(units, illus, bid)
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
        cut = str(d['cut']) if d.get('cut') else None
        if cut is not None:
            _need(cut in CUT_MODES, 'CUT_MODE_UNKNOWN', cut, bid)
        backdrop = None
        rb = d.get('backdrop')
        if rb is not None:
            _need(isinstance(rb, list) and 1 <= len(rb) <= BACKDROP_PLANE_CAP, 'BACKDROP_PLANE_CAP', f'at most {BACKDROP_PLANE_CAP} planes', bid)
            backdrop = []
            for p in rb:
                _need(isinstance(p, dict), 'BACKDROP_PLANE_INVALID', 'a plane must be an object', bid)
                tone = str(p.get('tone') or 'auto')
                _need(tone in BACKDROP_TONES or bool(HEX_COLOUR_RE.match(tone)), 'BACKDROP_TONE_UNKNOWN', tone, bid)
                band = p.get('band') or {}
                top = _unit(band.get('top', 0.5))
                height = float(band.get('height') or 0.2)
                _need(0.05 <= height <= 0.7 and top + height <= 1.05, 'BACKDROP_BAND_INVALID', f'top {top} height {height}', bid)
                depth = _unit(p.get('depth', 0.4))
                concept = ' '.join(str(p.get('concept') or '').split())
                _need(len(concept) <= 40, 'BACKDROP_CONCEPT_LONG', concept, bid)
                backdrop.append({'tone': tone, 'band': {'top': top, 'height': height}, 'depth': depth,
                                 'ragged': bool(p.get('ragged')), 'concept': concept or None})
            backdrop.sort(key=lambda p: p['depth'])
        return cls(bid, bt, pattern, layer, narration, units, figure, media, data, illus,
                   _unit(d.get('energy', 0.55)), _unit(d.get('complexity', 0.45)), feats, int(d.get('min_duration_ms') or 0), cut, backdrop)

    @property
    def has_visual(self) -> bool:
        return bool(self.illustration or self.media or self.figure or self.data)


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
    accent: Optional[str] = None  # one brand colour, spent only on state changes
    finish: str = 'EDITORIAL_FLAT'


@dataclass
class TypographyMode:
    reveal: str = 'WORD_CASCADE'
    tonal_ink: float = 0.42   # opacity of non-stressed words while a unit is still being spoken
    min_visual_share: float = 0.6  # fraction of non-QUIET beats that must carry a visual argument


@dataclass
class World:
    """The film's visual bible: a grain/overlay pick and a recurring motif emblem stamped in a
    corner of every beat (the thread the viewer follows between scenes). Authored per film."""

    grain: Optional[str] = None
    motif: Optional[Dict[str, Any]] = None  # {concept, corner} -> resolved to a mark in _resolve_concepts


@dataclass
class FilmTreatment:
    film_id: str
    beats: List[BeatTreatment]
    aspects: List[str]
    media_library: Dict[str, MediaAsset]
    brand: Brand
    voice: Dict[str, Any]
    fps: int = 30
    typography: TypographyMode = field(default_factory=TypographyMode)
    mood: Optional[str] = None
    cast: Dict[str, CastMember] = field(default_factory=dict)
    world: Optional[World] = None

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
        cast_d = d.get('cast') or {}
        _need(isinstance(cast_d, dict) and len(cast_d) <= CAST_MEMBER_CAP, 'CAST_MEMBER_CAP', f'at most {CAST_MEMBER_CAP} cast members')
        cast: Dict[str, CastMember] = {}
        for cid, m in cast_d.items():
            mid = str(cid).strip()
            _need(bool(mid) and len(mid) <= 32, 'CAST_MEMBER_ID_INVALID', str(cid))
            _need(isinstance(m, dict), 'CAST_MEMBER_INVALID', str(cid))
            cast[mid] = CastMember.parse(mid, m)
        world = None
        world_d = d.get('world')
        if isinstance(world_d, dict):
            grain = str(world_d.get('grain') or '').strip() or None
            _need(grain is None or grain in WORLD_GRAINS, 'WORLD_GRAIN_UNKNOWN', grain or '')
            motif = world_d.get('motif')
            if motif is not None:
                _need(isinstance(motif, dict), 'WORLD_MOTIF_INVALID', 'motif must be an object')
                concept = ' '.join(str(motif.get('concept') or '').split())
                _need(0 < len(concept) <= 40, 'WORLD_MOTIF_CONCEPT', concept)
                corner = str(motif.get('corner') or 'bottom-right')
                _need(corner in WORLD_CORNERS, 'WORLD_CORNER_UNKNOWN', corner)
                motif = {**motif, 'concept': concept, 'corner': corner}
            world = World(grain, motif)
        by_id = {b.beat_id: b for b in beats}
        for b in beats:
            il = b.illustration
            if il:
                for e in il.entities:
                    if e.glyph == 'MEDIA':
                        _need(e.media_ref in library, 'MEDIA_ASSET_NOT_IN_LIBRARY', e.media_ref, b.beat_id)
                if il.carry_from:
                    _need(il.carry_from in ids and ids.index(il.carry_from) < ids.index(b.beat_id), 'CARRY_SOURCE_NOT_EARLIER', il.carry_from, b.beat_id)
                    src = by_id[il.carry_from].illustration
                    _need(src is not None, 'CARRY_SOURCE_HAS_NO_ILLUSTRATION', il.carry_from, b.beat_id)
                    src_ids = {e.id for e in src.entities}
                    for ce in il.carry_entities:
                        _need(ce in src_ids, 'CARRY_ENTITY_NOT_IN_SOURCE', f'{ce} not in {il.carry_from}', b.beat_id)
                if il.persist_to:
                    _need(il.persist_to in ids and ids.index(il.persist_to) > ids.index(b.beat_id), 'ILLUSTRATION_PERSIST_TARGET_INVALID', il.persist_to, b.beat_id)
            if b.figure and b.figure.character:
                _need(b.figure.character in cast, 'PERFORMER_CHARACTER_UNKNOWN', b.figure.character, b.beat_id)
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
        ty = d.get('typography') or {}
        reveal = str(ty.get('reveal') or 'WORD_CASCADE').upper()
        _need(reveal in REVEAL_MODES, 'TYPOGRAPHY_REVEAL_UNKNOWN', reveal)
        typo = TypographyMode(reveal, _unit(ty.get('tonal_ink', 0.42)), _unit(ty.get('min_visual_share', 0.6)))
        mood = (str(d.get('mood') or '').strip().lower() or None)
        if mood is not None:
            _need(mood in FILM_MOODS, 'FILM_MOOD_UNKNOWN', mood)
        spoken = [b for b in beats if b.dominant_layer != 'QUIET']
        if spoken:
            share = sum(b.has_visual for b in spoken) / len(spoken)
            _need(share + 1e-9 >= typo.min_visual_share, 'FILM_VISUAL_DENSITY_LOW',
                  f'{share:.2f} of beats carry a visual argument; the film demands {typo.min_visual_share:.2f}. Text-only is not editorial.')
        return cls(fid, beats, aspects, library, brand, voice, fps, typo, mood, cast, world)
