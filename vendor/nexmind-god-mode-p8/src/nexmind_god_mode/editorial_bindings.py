"""P8-owned semantic Editorial bindings. No prose inference or renderer geometry."""
from copy import deepcopy
from .contracts import ContractViolation, require_exact_keys

VISUAL_KINDS = {'TEXT', 'BACKGROUND', 'VACANCY', 'ASSET'}
KINDS = VISUAL_KINDS | {'NARRATION', 'SILENCE', 'SOUND_EVENT', 'CAMERA'}
PLACEMENTS = {'FULL_CANVAS', 'MAIN', 'UPPER', 'LOWER', 'LEADING', 'TRAILING'}
TOKENS = {
    'placement': PLACEMENTS, 'scale': {'HERO', 'BODY', 'CAPTION'},
    'tone': {'BACKGROUND', 'INK', 'SURFACE', 'PRIMARY', 'ACCENT', 'SECONDARY'},
    'font': {'DIDONE', 'SANS', 'MONO'}, 'weight': {'REGULAR', 'BOLD'},
    'align': {'LEADING', 'CENTER', 'TRAILING'}, 'emphasis': {'NORMAL', 'MUTED', 'HIDDEN'},
    'source': {'CATALOG', 'CUSTOMER_MEDIA'},
}

BINDING_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['role', 'kind', 'semantic_ref'],
    'properties': {
        'role': {'type': 'string', 'minLength': 1},
        'kind': {'type': 'string', 'enum': sorted(KINDS)},
        'semantic_ref': {'type': 'string', 'minLength': 1},
        'text': {'type': 'string'}, 'asset_id': {'type': 'string', 'minLength': 1},
        **{key: {'type': 'string', 'enum': sorted(values)} for key, values in TOKENS.items()},
    },
}


def validate_binding(binding, *, hero=False):
    if not isinstance(binding, dict): raise ContractViolation('Editorial binding must be an object')
    require_exact_keys(binding, {'role', 'kind', 'semantic_ref'},
                       set(TOKENS) | {'text', 'asset_id'}, label='Editorial binding')
    for key in ('role', 'semantic_ref'):
        if not isinstance(binding[key], str) or not binding[key].strip():
            raise ContractViolation('Editorial binding requires ' + key)
    kind = binding['kind']
    if not isinstance(kind, str) or kind not in KINDS or (hero and kind not in VISUAL_KINDS - {'BACKGROUND', 'VACANCY'}):
        raise ContractViolation('Editorial binding kind is invalid')
    required = {'placement'} if kind in VISUAL_KINDS else set()
    if kind == 'TEXT': required |= {'text', 'scale', 'tone', 'font', 'weight', 'align', 'emphasis'}
    if kind == 'BACKGROUND': required |= {'tone'}
    if kind == 'ASSET': required |= {'asset_id', 'source', 'emphasis'}
    allowed = {'role', 'kind', 'semantic_ref'} | required
    if set(binding) != allowed: raise ContractViolation('Editorial ' + kind + ' binding fields: ' + str(sorted(required)))
    for key in required & TOKENS.keys():
        if not isinstance(binding[key], str) or binding[key] not in TOKENS[key]:
            raise ContractViolation('Editorial binding invalid ' + key)
    if kind == 'TEXT' and (not isinstance(binding['text'], str) or not binding['text'].strip()):
        raise ContractViolation('Editorial TEXT requires exact audience text')
    if kind == 'ASSET' and (not isinstance(binding['asset_id'], str) or not binding['asset_id'].strip()):
        raise ContractViolation('Editorial ASSET requires exact asset_id')
    if (kind == 'BACKGROUND') != (binding.get('placement') == 'FULL_CANVAS'):
        raise ContractViolation('FULL_CANVAS is reserved for BACKGROUND')
    return deepcopy(binding)


def validate_beat_bindings(beat, *, required=False):
    fields = {'display_copy', 'hero_binding', 'support_bindings'}
    present = fields & beat.keys()
    if not present and not required: return
    if present != fields: raise ContractViolation('Editorial beat requires display_copy, hero_binding and support_bindings')
    hero = validate_binding(beat['hero_binding'], hero=True)
    copy = beat['display_copy']
    if not isinstance(copy, str) or copy != (hero['text'] if hero['kind'] == 'TEXT' else ''):
        raise ContractViolation('display_copy must equal exact hero TEXT; ASSET heroes use explicit TEXT supports')
    roles = beat.get('supporting_roles', beat.get('supporting_assets', []))
    if not isinstance(roles, list) or not all(isinstance(role, str) and role.strip() for role in roles) or len(set(roles)) != len(roles):
        raise ContractViolation('Editorial supporting roles must be unique nonempty labels')
    bindings = beat['support_bindings']
    if not isinstance(bindings, list): raise ContractViolation('Editorial support_bindings must be an array')
    labels = []; visual_refs = {hero['semantic_ref']}; backgrounds = 0
    for raw in bindings:
        binding = validate_binding(raw); labels.append(binding['role'])
        if binding['kind'] in VISUAL_KINDS:
            if binding['semantic_ref'] in visual_refs: raise ContractViolation('Duplicate Editorial visual semantic_ref')
            visual_refs.add(binding['semantic_ref'])
        backgrounds += binding['kind'] == 'BACKGROUND'
    if len(set(labels)) != len(labels) or set(labels) != set(roles):
        raise ContractViolation('Every authored supporting role requires exactly one typed binding')
    if backgrounds != 1: raise ContractViolation('Editorial scene requires exactly one authored BACKGROUND binding')
    kinds={b['kind'] for b in bindings}
    if 'SILENCE' in kinds and kinds & {'NARRATION','SOUND_EVENT'}:
        raise ContractViolation('Art cannot require whole-beat SILENCE and audible supports together')
    camera_atoms={b['semantic_ref'] for b in bindings if b['kind']=='CAMERA'}
    if len(camera_atoms)>1: raise ContractViolation('Art cannot require conflicting camera atoms in one beat')


def validate_story_audio_bindings(art, story):
    modes={b['beat_id']:b.get('narration_mode','SILENT') for b in story['beats']}
    for beat in art['beat_art']:
        for binding in beat.get('support_bindings',[]):
            if binding['kind']=='NARRATION' and modes[beat['beat_id']]!='VOICEOVER':
                raise ContractViolation('Art NARRATION binding contradicts the accepted silent Story beat')
            if binding['kind']=='SILENCE' and modes[beat['beat_id']]=='VOICEOVER':
                raise ContractViolation('Art SILENCE binding contradicts the accepted Story voiceover')


def capability_view():
    return {
        'schema': 'P8EditorialBindingsV1', 'binding_schema': deepcopy(BINDING_SCHEMA),
        'laws': [
            'Every beat authors display_copy, hero_binding and support_bindings. These are Art-owned decisions.',
            'display_copy is the exact hero TEXT, including whitespace and punctuation; ASSET heroes use empty display_copy and explicit TEXT supports.',
            'Every supporting_roles label binds exactly once. No interpretation of role names into asset kinds.',
            'TEXT needs text, placement, scale, tone, font, weight, align and emphasis. BACKGROUND needs FULL_CANVAS placement and tone. VACANCY needs placement and intentionally draws no pixels.',
            'ASSET needs placement, asset_id, source and emphasis; use an exact admitted inventory ID, never an unrelated icon.',
            'NARRATION, SILENCE, SOUND_EVENT and CAMERA are nonvisual bindings with only role, kind and semantic_ref.',
            'NARRATION binds Story VOICEOVER. SILENCE binds a silent beat without audible events. SOUND_EVENT semantic_ref is the exact future Sound semantic_tag. CAMERA semantic_ref is the exact camera atom.',
            'Motion actor/target must use the exact visual semantic_ref. Camera framing prose and Story purpose/reveal are never audience copy.',
            'Native slots and font/scale/palette tokens are executable bindings, not restrictions on creative representation or thesis.',
            'Typed visual bindings are the executable realization of Art composition and every settled state. Prose-only promises are not rendered. This native port is flat 2D; no arbitrary geometry, texture generation, focus/depth planes or 3D camera are bound.',
        ],
        'native_motion': ['TYPE_REVEAL', 'REVEAL', 'HIGHLIGHT', 'DE_EMPHASIZE', 'SETTLE', 'STATE_CHANGE', 'REFRAME_CONTENT'],
        'motion_law': 'Serial scene-graph actions execute inside the canonical action_frame to settle_frame window. State/reframe/emphasis changes require distinct P8-authored prior and settled states for the same semantic_ref. SETTLE preserves the settled state.',
        'native_camera': ['HOLD', 'PUSH_IN', 'PULL_BACK', 'REFRAME', 'PAN', 'TILT', 'TRACK', 'FOLLOW'],
        'type_scale_law': 'HERO/BODY/CAPTION are 7.5/4.5/2.5 percent of the shorter canvas edge; every slot retains all exact copy or fails actual-frame clipping checks.',
        'timeline_law': 'Contiguous beats; CUT/MATCH_CUT/CARRY/HOLD_THROUGH; no unbound cross-beat overlaps or dissolves.',
    }


def visual_refs(beat):
    return {binding['semantic_ref'] for binding in [beat['hero_binding'],*beat['support_bindings']]
            if binding['kind'] in VISUAL_KINDS}


def validate_camera_targets(art, candidates):
    typed={b['beat_id']:b for b in art.get('beat_art',[]) if 'hero_binding' in b}
    for candidate in candidates:
        for shot in candidate['shots']:
            beat=typed.get(shot['beat_id'])
            if beat is None: continue
            atom=shot['camera_atom']
            if atom['target'] not in visual_refs(beat): raise ContractViolation('Editorial camera requires an exact bound visual semantic_ref')
            if atom['atom'] not in capability_view()['native_camera']: raise ContractViolation('Editorial camera atom is not bound by the native body')
            for binding in beat['support_bindings']:
                if binding['kind']=='CAMERA' and atom['atom']!=binding['semantic_ref']:
                    raise ContractViolation('Cinematography must fulfill the Art CAMERA binding: '+binding['semantic_ref'])


def validate_motion_targets(board, candidates):
    typed={b['beat_id']:b for b in board.get('beats',[]) if 'hero_binding' in b}
    for candidate in candidates:
        changing={}
        for action in candidate['actions']:
            beat=typed.get(action['beat_id'])
            if beat is None: continue
            refs=visual_refs(beat)
            if action['actor'] not in refs or (action['target'] not in {'','NONE'} and action['target'] not in refs):
                raise ContractViolation('Editorial Motion actor/target requires an exact bound visual semantic_ref')
            verb=(action.get('execution') or {}).get('resolved_verb') or action['requested_verb']
            if action['performer_class']!='SCENE_GRAPH' or verb not in capability_view()['native_motion']:
                raise ContractViolation('Editorial Motion primitive is not bound by the native body')
            if verb!='SETTLE':
                ref=action['target'] if action['target'] not in {'','NONE'} else action['actor']
                pair=(action['beat_id'],ref)
                if pair in changing: raise ContractViolation('Editorial intermediate visual state is not authored for multiple changing actions')
                changing[pair]=action['action_id']
        for bid in typed:
            actions=[a for a in candidate['actions'] if a['beat_id']==bid]
            if len(actions)>1 and any(a['overlap_policy'] not in {'SERIAL_REQUIRED','HOLD'} for a in actions):
                raise ContractViolation('Editorial native body requires explicitly serial actions')


def validate_sound_obligations(board, candidates):
    for candidate in candidates:
        for beat in board.get('beats',[]):
            events=[e for e in candidate['events'] if e['beat_id']==beat['beat_id']]
            for binding in beat.get('support_bindings',[]):
                kind=binding['kind'];ref=binding['semantic_ref']
                if kind=='SOUND_EVENT' and not any(e['semantic_tag']==ref and e['kind'] not in {'SILENCE','NARRATION_ACCENT'} and e.get('intensity')!='NONE' and not e['optional'] for e in events):
                    raise ContractViolation('Sound must fulfill the exact required Art semantic_tag: '+ref)
                if kind=='SILENCE' and (beat.get('narration_mode','SILENT')!='SILENT' or any(e['kind'] not in {'SILENCE','NARRATION_ACCENT'} for e in events)):
                    raise ContractViolation('Sound must preserve the Art SILENCE binding')
