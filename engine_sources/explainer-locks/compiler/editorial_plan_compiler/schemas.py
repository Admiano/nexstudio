"""JSON Schema documents for the contracts that cross the P8 -> compiler -> runtime boundary.

The vocabularies are read from ``contracts`` so a schema can never drift from
what the parser accepts. ``python3 -m editorial_plan_compiler.schemas <dir>``
writes them to disk; the runtime and P8 integration validate against the files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from . import contracts as c

DRAFT = 'https://json-schema.org/draft/2020-12/schema'
PLAN_SCHEMA_ID = 'NexStudioEditorialPlanV2'


def _obj(props: Dict[str, Any], required: List[str], **extra: Any) -> Dict[str, Any]:
    return {'type': 'object', 'properties': props, 'required': required, **extra}


def _enum(values) -> Dict[str, Any]:
    return {'type': 'string', 'enum': list(values)}


def _unit(lo: float = 0.0, hi: float = 1.0) -> Dict[str, Any]:
    return {'type': 'number', 'minimum': lo, 'maximum': hi}


def _str(min_len: int = 1) -> Dict[str, Any]:
    return {'type': 'string', 'minLength': min_len}


NULLABLE_STR = {'type': ['string', 'null']}
NULLABLE_OBJ = {'type': ['object', 'null']}
BOX = _obj({k: {'type': 'number'} for k in ('x', 'y', 'w', 'h')}, ['x', 'y', 'w', 'h'])
MS = {'type': 'integer', 'minimum': 0}
SHA = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}


def treatment_schema() -> Dict[str, Any]:
    """What P8 authors. Wording is payload; every routing decision is an explicit field."""
    unit = _obj({
        'text': _str(),
        'role': _enum(c.UNIT_ROLES),
        'emphasis': _unit(),
        'semantic_role': _enum(c.SEMANTIC_ROLES),
        'replace_group': NULLABLE_STR,
        'can_promote': {'type': 'boolean'},
        'italic': {'type': 'boolean'},
        'anchor_word': NULLABLE_STR,
        'stress': {'type': 'array', 'items': _str()},
        'mute': {'type': 'array', 'items': _str()},
        'reveal': {'anyOf': [_enum(c.REVEAL_MODES), {'type': 'null'}]},
    }, ['text'], additionalProperties=False)
    entity = _obj({
        'id': _str(), 'kind': _enum(c.ENTITY_KINDS), 'glyph': _enum(c.GLYPHS), 'size': _enum(c.ENTITY_SIZES),
        'label': NULLABLE_STR, 'asset_ref': NULLABLE_STR, 'media_ref': NULLABLE_STR,
        'params': {'type': 'object'},
    }, ['id', 'kind', 'glyph'], additionalProperties=False)
    relation = _obj({'type': _enum(c.RELATION_TYPES), 'source': _str(), 'target': _str(), 'style': _enum(c.RELATION_STYLES)}, ['type', 'source', 'target'], additionalProperties=False)
    anchor = {'oneOf': [_obj({'word': _str()}, ['word'], additionalProperties=False), _obj({'unit': {'type': 'integer', 'minimum': 0}}, ['unit'], additionalProperties=False),
                        _obj({'offset_ms': MS}, ['offset_ms'], additionalProperties=False)]}
    op = _obj({
        'op': _enum(c.OPS), 'target': _str(), 'at': anchor, 'duration_ms': {'type': 'integer', 'minimum': 120, 'maximum': 4000},
        'from': {'type': 'number'}, 'to': {'type': 'number'}, 'params': {'type': 'object'},
    }, ['op', 'target', 'at'], additionalProperties=False)
    illustration = _obj({
        'form': _enum(c.ILLUSTRATION_FORMS),
        'entities': {'type': 'array', 'items': entity, 'minItems': 1, 'maxItems': 7},
        'relations': {'type': 'array', 'items': relation},
        'program': {'type': 'array', 'items': op, 'minItems': 1, 'maxItems': 10},
        'carry': _obj({'from_beat': _str(), 'entities': {'type': 'array', 'items': _str()}}, ['from_beat'], additionalProperties=False),
        'persist_to': NULLABLE_STR,
    }, ['form', 'entities', 'program'], additionalProperties=False)
    figure = _obj({
        'valence': _unit(-1.0, 1.0),
        'arousal': _unit(),
        'posture': _enum(c.FIGURE_POSTURES),
        'energy': _unit(),
        'formality': _unit(),
        'facing': _enum(c.FIGURE_FACINGS),
        'justification': _str(),
    }, ['valence', 'arousal', 'justification'], additionalProperties=False)
    media = _obj({
        'asset_id': _str(),
        'role': _enum(c.MEDIA_ROLES),
        'focus': {**BOX, 'properties': {k: _unit() for k in ('x', 'y', 'w', 'h')}},
        'persist_to': NULLABLE_STR,
        'trim': _obj({'start': {'type': 'number', 'minimum': 0}, 'end': {'type': 'number', 'exclusiveMinimum': 0}}, ['start', 'end']),
    }, ['asset_id'], additionalProperties=False)
    data = _obj({
        'kind': _enum(c.DATA_KINDS),
        'value': _str(),
        'label': {'type': 'string'},
        'secondary': NULLABLE_STR,
    }, ['kind', 'value'], additionalProperties=False)
    beat = _obj({
        'beat_id': _str(),
        'beat_type': _enum(c.BEAT_TYPES),
        'pattern': _enum(c.PATTERNS),
        'dominant_layer': _enum(c.DOMINANT_LAYERS),
        'narration': {'type': 'string'},
        'display_units': {'type': 'array', 'items': unit, 'maxItems': 5},
        'figure': {'anyOf': [figure, {'type': 'null'}]},
        'media': {'anyOf': [media, {'type': 'null'}]},
        'data': {'anyOf': [data, {'type': 'null'}]},
        'illustration': {'anyOf': [illustration, {'type': 'null'}]},
        'energy': _unit(),
        'complexity': _unit(),
        'features': {'type': 'object', 'additionalProperties': _unit()},
        'min_duration_ms': MS,
        'cut': _enum(c.CUT_MODES),
    }, ['beat_id', 'beat_type', 'pattern'], additionalProperties=False)
    asset = _obj({
        'asset_id': _str(),
        'kind': _enum(c.MEDIA_KINDS),
        'path': _str(),
        'width': {'type': 'integer', 'minimum': 1},
        'height': {'type': 'integer', 'minimum': 1},
        'duration_s': {'type': 'number', 'minimum': 0},
        'rights': _str(),
    }, ['asset_id', 'kind', 'path', 'width', 'height'], additionalProperties=False)
    voice = _obj({
        'source': _enum(('RECORDED', 'ROUTE', 'FIXTURE', 'MASTER')),
        'route_id': {'type': 'string'},
        'alignments': {'type': 'object', 'additionalProperties': alignment_schema(nested=True)},
        'words_per_minute': {'type': 'number', 'exclusiveMinimum': 0},
        'audio_path': _str(),
        'alignment_path': _str(),
        'head_pad_ms': MS,
    }, [])
    return {
        '$schema': DRAFT,
        '$id': f'https://nexstudio.dev/schema/{c.SCHEMA}.json',
        'title': c.SCHEMA,
        'description': 'Per-beat editorial treatment decision authored by NexMind P8. The compiler fails closed on anything outside these vocabularies.',
        **_obj({
            'schema': {'const': c.SCHEMA},
            'film_id': _str(),
            'aspects': {'type': 'array', 'items': _enum(c.ASPECTS), 'uniqueItems': True, 'minItems': 1},
            'fps': _enum_int((24, 25, 30, 60)),
            'beats': {'type': 'array', 'items': beat, 'minItems': 1},
            'media_library': {'type': 'array', 'items': asset},
            'brand': _obj({'ink': _str(), 'paper': _str(), 'accent': NULLABLE_STR, 'finish': _enum(c.FINISHES)}, []),
            'typography': _obj({'reveal': _enum(c.REVEAL_MODES), 'tonal_ink': _unit(), 'min_visual_share': _unit()}, []),
            'voice': voice,
            'mood': _enum(c.FILM_MOODS),
            'note': {'type': 'string'},
        }, ['schema', 'film_id', 'beats']),
    }


def _enum_int(values) -> Dict[str, Any]:
    return {'type': 'integer', 'enum': list(values)}


def alignment_schema(nested: bool = False) -> Dict[str, Any]:
    """Character alignment as returned by ElevenLabs /with-timestamps, and the word timings derived from it."""
    times = {'type': 'array', 'items': {'type': 'number', 'minimum': 0}}
    body = _obj({
        'characters': {'type': 'array', 'items': {'type': 'string', 'maxLength': 1}},
        'character_start_times_seconds': times,
        'character_end_times_seconds': times,
    }, ['characters', 'character_start_times_seconds', 'character_end_times_seconds'])
    if nested:
        return body
    return {'$schema': DRAFT, '$id': 'https://nexstudio.dev/schema/NexStudioVoiceAlignmentV1.json', 'title': 'NexStudioVoiceAlignmentV1', **body}


def semantic_beat_schema() -> Dict[str, Any]:
    """Scene Intelligence output: continuous features + typed entities/relations. Labels never route."""
    features = ('human_agency', 'emotional_intensity', 'emotional_valence', 'relational_density', 'transformation_degree',
                'comparison_degree', 'spatiality', 'physicality', 'evidence_density', 'uncertainty', 'sociality', 'causality',
                'continuity_required')
    entity = _obj({'id': _str(), 'text': _str(), 'type': _str(), 'salience': _unit()}, ['id', 'text', 'type'])
    relation = _obj({'source': _str(), 'target': _str(), 'type': _str(), 'weight': _unit()}, ['source', 'target', 'type'])
    return {
        '$schema': DRAFT, '$id': 'https://nexstudio.dev/schema/NexStudioSemanticBeatV1.json', 'title': 'NexStudioSemanticBeatV1',
        **_obj({
            'beat_id': _str(),
            'text': _str(),
            'entities': {'type': 'array', 'items': entity},
            'relations': {'type': 'array', 'items': relation},
            'features': _obj({f: _unit(-1.0 if f == 'emotional_valence' else 0.0, 1.0) for f in features}, list(features)),
            'protagonist_id': NULLABLE_STR,
        }, ['beat_id', 'text', 'features']),
    }


def sound_events_schema() -> Dict[str, Any]:
    accent = _obj({
        'event': _str(), 'beat_at_ms': MS, 'film_at_ms': MS, 'asset_id': _str(), 'semantic_tag': _str(),
        'path': _str(), 'sha256': SHA, 'license': _str(), 'duration_s': {'type': 'number', 'minimum': 0}, 'gain_db': {'type': 'number'},
    }, ['event', 'beat_at_ms', 'film_at_ms', 'asset_id', 'path', 'sha256', 'license'])
    return {
        '$schema': DRAFT, '$id': 'https://nexstudio.dev/schema/NexStudioSoundEventsV2.json', 'title': 'NexStudioSoundEventsV2',
        'description': 'Semantic accents bound to visible events. Silence is a valid, recorded outcome.',
        **_obj({'accents': {'type': 'array', 'items': accent, 'maxItems': 3}, 'silenced': {'type': 'array', 'items': {'type': 'string'}},
                'reason': NULLABLE_STR}, ['accents', 'silenced']),
    }


def media_provenance_schema() -> Dict[str, Any]:
    return {
        '$schema': DRAFT, '$id': 'https://nexstudio.dev/schema/NexStudioMediaProvenanceV1.json', 'title': 'NexStudioMediaProvenanceV1',
        'description': 'Customer media as ingested: the original upload and the render-normalised copy are both hashed.',
        **_obj({
            'asset_id': _str(), 'kind': _enum(c.MEDIA_KINDS), 'rights': _str(),
            'original_path': _str(), 'original_sha256': SHA,
            'render_path': _str(), 'render_sha256': SHA, 'render_codec': _str(), 'normalised': {'type': 'boolean'},
        }, ['asset_id', 'kind', 'rights', 'original_path', 'original_sha256', 'render_path', 'render_sha256', 'render_codec', 'normalised']),
    }


def native_aspect_schema() -> Dict[str, Any]:
    return {
        '$schema': DRAFT, '$id': 'https://nexstudio.dev/schema/NexStudioNativeAspectCompositionV2.json', 'title': 'NexStudioNativeAspectCompositionV2',
        'description': 'Composition authored independently for one aspect. A plan that reports derived_by_scaling=true is rejected.',
        **_obj({
            'layout_family': _str(), 'treatment': _str(), 'text_zone': BOX, 'visual_zone': BOX, 'safe_area': BOX,
            'background': {'type': 'object'},
            'native_profile': {'const': True}, 'derived_by_scaling': {'const': False},
            'authority': {'const': 'NATIVE_THREE_ASPECT_COMPOSITION_AUTHORITY_V2'},
        }, ['layout_family', 'treatment', 'text_zone', 'visual_zone', 'safe_area', 'native_profile', 'derived_by_scaling', 'authority']),
    }


def plan_schema() -> Dict[str, Any]:
    """What the execution-only runtime consumes. Every field is geometry, timing or provenance; no prose to interpret."""
    event = _obj({'event': _str(), 'unit_index': {'type': 'integer', 'minimum': -1}, 'start_ms': MS, 'end_ms': MS}, ['event', 'unit_index', 'start_ms', 'end_ms'])
    fit = _obj({'font_px': {'type': 'number', 'exclusiveMinimum': 0}, 'line_height': {'type': 'number'}, 'lines': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1},
                'status': {'const': 'FIT'}}, ['font_px', 'lines', 'status'])
    cascade_word = _obj({'text': _str(), 'line': {'type': 'integer', 'minimum': 0}, 'start_ms': MS, 'stress': {'type': 'boolean'}, 'tone': _enum(('mute',))}, ['text', 'line', 'start_ms', 'stress'])
    block = _obj({'unit_index': {'type': 'integer', 'minimum': 0}, 'role': _enum(c.UNIT_ROLES), 'text': _str(), 'weight': _str(), 'style': _str(), 'bbox': BOX, 'fit': fit,
                  'reveal': _enum(c.REVEAL_MODES), 'words': {'type': 'array', 'items': cascade_word, 'minItems': 1}, 'cascade_end_ms': MS},
                 ['unit_index', 'role', 'text', 'bbox', 'fit', 'reveal', 'words'])
    typography = _obj({'motif': NULLABLE_STR, 'blocks': {'type': 'array', 'items': block}, 'events': {'type': 'array', 'items': event},
                       'performance_events': {'type': 'array', 'items': event}, 'transition_carrier': {}, 'reading_order': {'type': 'array'}, 'focal_order': {'type': 'array'},
                       'reveal_mode': _enum(c.REVEAL_MODES), 'tonal_ink': _unit()},
                      ['blocks', 'events', 'performance_events'])
    label = _obj({'text': _str(), 'bbox': BOX, 'fit': fit, 'placement': _enum(('inside', 'below'))}, ['text', 'bbox', 'fit', 'placement'])
    asset = _obj({'id': _str(), 'path': _str(), 'sha256': SHA, 'license': _str(), 'family': _str(), 'art_box': {'type': 'object'},
                  'colour': _enum(('mono', 'native', 'brand')), 'brand_hex': _str()}, ['id', 'path', 'sha256', 'license'])
    ent_media = _obj({'asset_id': _str(), 'kind': _enum(c.MEDIA_KINDS), 'path': _str(), 'sha256': {'anyOf': [SHA, {'type': 'null'}]}, 'source_size': {'type': 'object'},
                      'rights': _str(), 'audio': {'const': 'MUTE'}, 'trim': {}, 'chassis': _enum(c.CHASSIS), 'tilt': {'type': 'number'}},
                     ['asset_id', 'kind', 'path', 'rights', 'audio', 'chassis', 'tilt'])
    ent_photo = _obj({'path': _str(), 'sha256': SHA, 'source_size': {'type': 'object'}, 'rights': _str(), 'license': _enum(('CC0 1.0', 'Public Domain')),
                      'license_url': _str(), 'source': _str(), 'source_id': _str(), 'landing_url': _str(), 'title': _str(), 'creator': _str()},
                     ['path', 'sha256', 'source_size', 'rights', 'license', 'source', 'landing_url'])
    state_in = _obj({k: {'type': 'number'} for k in ('draw', 'fill', 'ink', 'dim', 'grow', 'strike', 'swap', 'count', 'emit', 'connect')} | {'at': _str()}, [], additionalProperties=False)
    entity = _obj({
        'id': _str(), 'kind': _enum(c.ENTITY_KINDS), 'glyph': _enum(c.GLYPHS), 'size': _enum(c.ENTITY_SIZES), 'bbox': BOX, 'params': {'type': 'object'},
        'label': {'anyOf': [label, {'type': 'null'}]}, 'asset': {'anyOf': [asset, {'type': 'null'}]}, 'media': {'anyOf': [ent_media, {'type': 'null'}]},
        'photo': {'anyOf': [ent_photo, {'type': 'null'}]},
        'inside': _str(), 'over': _str(), 'enter_ms': MS, 'enter_duration_ms': MS, 'carried': {'type': 'boolean'}, 'carry_from_bbox': {'anyOf': [BOX, {'type': 'null'}]},
        'state_in': state_in,
    }, ['id', 'kind', 'glyph', 'size', 'bbox', 'params', 'enter_ms', 'enter_duration_ms', 'carried', 'state_in'])
    point = {'type': 'array', 'items': {'type': 'number'}, 'minItems': 2, 'maxItems': 2}
    relation = _obj({
        'id': _str(), 'type': _enum(c.RELATION_TYPES), 'source': _str(), 'target': _str(), 'path': {'anyOf': [{'type': 'array', 'items': point, 'minItems': 2}, {'type': 'null'}]},
        'length': {'type': 'number'}, 'arrow': {'type': 'boolean'}, 'bar': {'type': 'boolean'}, 'rule': {'type': 'boolean'},
        'style': NULLABLE_STR, 'dots': {'type': 'boolean'}, 'dashed': {'type': 'boolean'}, 'thin': {'type': 'boolean'},
        'enter_ms': MS, 'enter_duration_ms': MS, 'drawn_by_op': {'type': 'boolean'}, 'state_in': state_in,
    }, ['id', 'type', 'source', 'target', 'path', 'arrow', 'enter_ms', 'enter_duration_ms', 'state_in'])
    op = _obj({'op': _enum(c.OPS), 'target': _str(), 'start_ms': MS, 'end_ms': MS, 'from': {'type': 'number'}, 'to': {'type': 'number'}, 'params': {'type': 'object'},
               'state_change': {'type': 'boolean'}, 'anchor': {'type': 'object'}}, ['op', 'target', 'start_ms', 'end_ms', 'from', 'to', 'state_change'])
    illustration = _obj({
        'form': _enum(c.ILLUSTRATION_FORMS), 'zone': BOX, 'entities': {'type': 'array', 'items': entity, 'minItems': 1}, 'relations': {'type': 'array', 'items': relation},
        'ops': {'type': 'array', 'items': op}, 'settled_ms': MS, 'accent': NULLABLE_STR, 'accent_policy': {'const': 'STATE_CHANGE_OPS_ONLY'}, 'state_changes': {'type': 'integer'},
        'carry_from': NULLABLE_STR, 'persist_to': NULLABLE_STR, 'carried': {'type': 'boolean'}, 'registry_version': NULLABLE_STR,
    }, ['form', 'zone', 'entities', 'relations', 'ops', 'settled_ms', 'accent_policy', 'carried'])
    window = _obj({'start_ms': MS, 'end_ms': MS}, ['start_ms', 'end_ms'])
    ensemble = _obj({'events': {'type': 'array'}, 'hold_window': window, 'transition_window': window}, ['hold_window'])
    part = _obj({'slot': _str(), 'part_id': _str(), 'file': _str(), 'sha256': SHA, 'frame': BOX}, ['slot', 'part_id', 'file', 'sha256', 'frame'])
    figure = _obj({'library': {'const': 'OPEN_PEEPS'}, 'still': {'const': True}, 'framing': {'const': 'FULL_BODY'}, 'posture': _enum(c.FIGURE_POSTURES),
                   'parts': {'type': 'array', 'items': part, 'minItems': 1}, 'palette': {'type': 'object'}, 'mirror': {'type': 'boolean'},
                   'facing': _enum(c.FIGURE_FACINGS), 'emotion': {'type': 'object'}, 'pose': {'type': 'object'}, 'justification': _str(),
                   'bbox': BOX, 'zone': BOX, 'enter_ms': MS, 'enter_duration_ms': MS, 'entrance': _str(), 'ground_line': {'type': 'number'}},
                  ['library', 'still', 'framing', 'parts', 'facing', 'justification', 'bbox', 'enter_ms', 'enter_duration_ms'])
    media = _obj({
        'asset_id': _str(), 'kind': _enum(c.MEDIA_KINDS), 'rights': _str(), 'path': _str(), 'sha256': SHA,
        'original_path': _str(), 'original_sha256': SHA, 'render_codec': _str(), 'source_size': _obj({'w': {'type': 'integer'}, 'h': {'type': 'integer'}}, ['w', 'h']),
        'role': _enum(c.MEDIA_ROLES), 'bbox': BOX, 'zone': BOX, 'focus': {'anyOf': [BOX, {'type': 'null'}]},
        'trim': {'anyOf': [_obj({'start': {'type': 'number'}, 'end': {'type': 'number'}}, ['start', 'end']), {'type': 'null'}]},
        'audio': {'const': 'MUTE'}, 'enter_ms': MS, 'enter_duration_ms': MS, 'carried_from': NULLABLE_STR, 'persist_to': NULLABLE_STR, 'frame': _str(),
        'chassis': _enum(c.CHASSIS), 'tilt': {'type': 'number'},
    }, ['asset_id', 'kind', 'rights', 'path', 'sha256', 'original_path', 'original_sha256', 'role', 'bbox', 'audio', 'enter_ms', 'enter_duration_ms', 'frame', 'chassis', 'tilt'])
    data = _obj({'kind': _enum(c.DATA_KINDS), 'zone': BOX, 'blocks': {'type': 'array'}, 'enter_ms': MS, 'enter_duration_ms': MS, 'stagger_ms': MS, 'style': _str()},
                ['kind', 'zone', 'blocks', 'enter_ms', 'enter_duration_ms', 'stagger_ms'])
    camera = _obj({'move': _enum(c.CAMERA_MOVES), 'dir': {'type': 'integer', 'enum': [-1, 0, 1]}, 'blur': _unit()}, ['move', 'dir', 'blur'], additionalProperties=False)
    transition = _obj({'mode': _str(), 'owner': _str(), 'start_ms': MS, 'end_ms': MS, 'camera': camera}, ['mode', 'owner', 'start_ms', 'end_ms'])
    word = _obj({'text': _str(), 'start_ms': MS, 'end_ms': MS}, ['text', 'start_ms', 'end_ms'])
    gate = _obj({'status': _enum(('PASS', 'FAIL')), 'failures': {'type': 'array', 'items': {'type': 'string'}}}, ['status', 'failures'])
    beat = _obj({
        'beat_id': _str(), 'beat_type': _enum(c.BEAT_TYPES), 'pattern': _enum(c.PATTERNS), 'dominant_layer': _enum(c.DOMINANT_LAYERS), 'shot_role': _str(),
        'start_ms': MS, 'duration_ms': {'type': 'integer', 'exclusiveMinimum': 0}, 'narration': {'type': 'string'},
        'words': {'type': 'array', 'items': word}, 'landings': {'type': 'array'},
        'composition': _strip(native_aspect_schema()), 'typography': typography, 'ensemble': ensemble,
        'media': {'anyOf': [media, {'type': 'null'}]}, 'figure': {'anyOf': [figure, {'type': 'null'}]}, 'data': {'anyOf': [data, {'type': 'null'}]},
        'illustration': {'anyOf': [illustration, {'type': 'null'}]},
        'transition': transition, 'sound': _strip(sound_events_schema()), 'gate': gate,
    }, ['beat_id', 'beat_type', 'pattern', 'dominant_layer', 'start_ms', 'duration_ms', 'composition', 'typography', 'ensemble', 'illustration', 'transition', 'sound', 'gate'])
    segment = _obj({'beat_id': _str(), 'source': _enum(('RECORDED', 'ROUTE', 'FIXTURE', 'MASTER')), 'audio_path': _str(), 'sha256': SHA, 'start_ms': MS, 'duration_ms': MS,
                    'evidence': {'type': 'object'}}, ['beat_id', 'source', 'audio_path', 'sha256', 'start_ms', 'duration_ms'])
    caption = _obj({'beat_id': _str(), 'text': _str(), 'start_ms': MS, 'end_ms': MS}, ['beat_id', 'text', 'start_ms', 'end_ms'])
    provenance = _obj({
        'treatment_sha256': SHA, 'creative_authority': {'const': 'NEXMIND_P8'}, 'compiler_role': {'const': 'DETERMINISTIC_PLAN_COMPILER'},
        'renderer_role': {'const': 'EXECUTION_ONLY'}, 'voice_timing': _enum(('RECORDED', 'ROUTE', 'FIXTURE', 'MASTER')), 'commercial_certification': {'const': False},
        'authorities': {'type': 'array', 'items': _obj({'file': _str(), 'bundle_path': _str(), 'source_sha256': SHA, 'vendored_sha256': SHA, 'modified': {'type': 'boolean'}},
                                                       ['file', 'source_sha256', 'vendored_sha256', 'modified'])},
        'sound_library': {'type': 'object'}, 'media_assets': {'type': 'array', 'items': _strip(media_provenance_schema())},
    }, ['treatment_sha256', 'creative_authority', 'compiler_role', 'renderer_role', 'voice_timing', 'commercial_certification', 'authorities'])
    return {
        '$schema': DRAFT, '$id': f'https://nexstudio.dev/schema/{PLAN_SCHEMA_ID}.json', 'title': PLAN_SCHEMA_ID,
        'description': 'Compiled, gate-checked editorial plan for one native aspect. Consumed verbatim by the execution-only runtime.',
        **_obj({
            'schema': {'const': PLAN_SCHEMA_ID}, 'compiler': _str(), 'film_id': _str(), 'aspect': _enum(c.ASPECTS), 'fps': _enum_int((24, 25, 30, 60)),
            'canvas': _obj({'w': {'type': 'integer'}, 'h': {'type': 'integer'}}, ['w', 'h']),
            'output': _obj({'w': {'type': 'integer'}, 'h': {'type': 'integer'}, 'scale': {'type': 'number'}}, ['w', 'h', 'scale']),
            'brand': _obj({'ink': _str(), 'paper': _str(), 'accent': NULLABLE_STR, 'finish': _enum(c.FINISHES)}, ['ink', 'paper', 'finish']),
            'motion': _obj({'entrance': _enum(('settle', 'pop')), 'stagger_ms': MS, 'camera_push': {'type': 'number'}, 'camera_pan_frac': {'type': 'number'},
                            'transition': _enum(('blur_dissolve', 'scale_through')), 'blur_px': {'type': 'number'}, 'word_landing': _enum(('tonal', 'rise')),
                            'spring': _enum(c.SPRING_PRESETS), 'breathe': _unit(), 'label_lag_ms': MS, 'motion_blur': {'type': 'number', 'minimum': 0},
                            'media_tilt': {'type': 'number', 'minimum': 0}},
                           ['entrance', 'stagger_ms', 'camera_push', 'transition', 'word_landing', 'spring', 'breathe', 'label_lag_ms', 'motion_blur', 'media_tilt']),
            'typography': _obj({'reveal': _enum(c.REVEAL_MODES), 'tonal_ink': _unit(), 'min_visual_share': _unit()}, ['reveal', 'tonal_ink']),
            'illustration_registry': _obj({'path': _str(), 'version': NULLABLE_STR}, ['path']),
            'fonts': {'type': 'object'}, 'duration_ms': {'type': 'integer', 'exclusiveMinimum': 0},
            'voice': _obj({'source': _enum(('RECORDED', 'ROUTE', 'FIXTURE', 'MASTER')), 'segments': {'type': 'array', 'items': segment},
                           'timeline': {'type': ['object', 'null']}}, ['source', 'segments']),
            'music': _obj({'slot': _str(), 'status': _str(), 'duck_under_voice_db': {'type': 'number'}, 'path': NULLABLE_STR,
                           'sha256': NULLABLE_STR, 'license': NULLABLE_STR, 'gain_db': {'type': 'number'},
                           'asset_id': NULLABLE_STR, 'moods': {'anyOf': [{'type': 'array', 'items': _str()}, {'type': 'null'}]},
                           'bpm': {'anyOf': [{'type': 'number'}, {'type': 'null'}]}, 'mood_request': NULLABLE_STR,
                           'loop': {'type': 'boolean'}, 'fade_in_ms': MS, 'fade_out_ms': MS}, ['slot', 'status', 'path']),
            'surfaces': _obj({'grain': NULLABLE_OBJ, 'paper': NULLABLE_OBJ}, []),
            'beats': {'type': 'array', 'items': beat, 'minItems': 1},
            'captions': {'type': 'array', 'items': caption},
            'captions_policy': _enum(('burned', 'kinetic')),
            'gate': gate, 'provenance': provenance,
        }, ['schema', 'compiler', 'film_id', 'aspect', 'fps', 'canvas', 'output', 'brand', 'typography', 'fonts', 'duration_ms', 'voice', 'music', 'beats', 'captions', 'gate', 'provenance']),
    }


def _strip(schema: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in schema.items() if k not in ('$schema', '$id', 'title', 'description')}


ALL = {
    'NexStudioEditorialTreatmentV2.schema.json': treatment_schema,
    'NexStudioSemanticBeatV1.schema.json': semantic_beat_schema,
    'NexStudioEditorialPlanV2.schema.json': plan_schema,
    'NexStudioVoiceAlignmentV1.schema.json': alignment_schema,
    'NexStudioSoundEventsV2.schema.json': sound_events_schema,
    'NexStudioMediaProvenanceV1.schema.json': media_provenance_schema,
    'NexStudioNativeAspectCompositionV2.schema.json': native_aspect_schema,
}


def write_all(out_dir: Path) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, fn in ALL.items():
        p = out_dir / name
        p.write_text(json.dumps(fn(), indent=2) + '\n')
        written.append(p)
    return written


if __name__ == '__main__':
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'schema'
    for p in write_all(target):
        print(p)
