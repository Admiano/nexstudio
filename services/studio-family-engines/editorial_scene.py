"""Bind typed P8 Art to native elements, exact assets and directed departments."""
from copy import deepcopy
from pathlib import Path
import math
import sys
from canonical import stable
from contracts import AdapterReplan, creative_replan_request, require_review_board

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'vendor/nexmind-god-mode-p8/src'))
from nexmind_god_mode.editorial_bindings import validate_beat_bindings, VISUAL_KINDS
from nexmind_god_mode.contracts import ContractViolation

# Named native slots are execution tokens, selected explicitly by Art. They are
# not selected from story/Art prose by this compiler.
SLOTS = {
    'FULL_CANVAS': [0,0,1,1], 'MAIN': [.12,.32,.76,.36],
    'UPPER': [.12,.08,.76,.22], 'LOWER': [.12,.72,.76,.20],
    'LEADING': [.08,.32,.38,.36], 'TRAILING': [.54,.32,.38,.36],
}
SIZES = {'HERO': .075, 'BODY': .045, 'CAPTION': .025}
ALPHAS = {'NORMAL': 1, 'MUTED': .35, 'HIDDEN': 0}


def fail(code, detail, owner='ART_DIRECTION'):
    downstream={'ART_DIRECTION':['art_direction','storyboard','cinematography','editorial_rhythm','motion_performance','sound_direction'],
                'CINEMATOGRAPHY':['cinematography','editorial_rhythm','motion_performance','sound_direction'],
                'EDITORIAL_RHYTHM':['editorial_rhythm','motion_performance','sound_direction'],
                'MOTION_PERFORMANCE':['motion_performance','sound_direction'], 'SOUND_DIRECTION':['sound_direction']}
    raise AdapterReplan(code,detail,creative_replan_request(
        escalation_scope=owner+'_STRATEGY',invalidate_slots=downstream[owner],issue=detail,
        revision_plan='Repair the typed binding at its owning department; preserve exact approved audience copy and all unaffected decisions.',
        quality_reason=code,constraints=['No role-name inference, invented copy, omitted support or icon substitution.']))


def seconds(value):
    if not isinstance(value,dict): fail('EDITORIAL_TIMELINE_BINDING_INVALID','Canonical rational timing required.','EDITORIAL_RHYTHM')
    v=value.get('value');r=value.get('rate')
    if isinstance(v,bool) or isinstance(r,bool) or not isinstance(v,(int,float)) or not isinstance(r,(int,float)) or not math.isfinite(v) or not math.isfinite(r) or r<=0:
        fail('EDITORIAL_TIMELINE_BINDING_INVALID','Finite canonical frame/rate required.','EDITORIAL_RHYTHM')
    return v/r


def bind_editorial_scene(board, palette, asset_resolver, camera_resolver):
    beats=require_review_board(board)
    if not any('hero_binding' in b or 'support_bindings' in b for b in beats): return None
    authored=(board.get('authored_art') or {}).get('beat_bindings')
    if not isinstance(authored,list) or len(authored)!=len(beats) or {a.get('beat_id') for a in authored if isinstance(a,dict)}!={b['beat_id'] for b in beats}:
        fail('EDITORIAL_ART_PROVENANCE_MISSING','Typed beat bindings must retain the accepted source Art.')
    sources={a['beat_id']:a for a in authored}
    scenes=[];assets=[];cursor=0.;previous={};all_actions=set();sound_sync={}
    for beat in beats:
        bid=beat['beat_id']
        try: validate_beat_bindings(beat,required=True)
        except ContractViolation as exc: fail('EDITORIAL_TYPED_ART_BINDING_INVALID',bid+':'+str(exc))
        source=sources[bid]
        if any(beat[key]!=source.get(key) for key in ('display_copy','hero_binding','support_bindings')) or beat.get('supporting_assets')!=source.get('supporting_roles'):
            fail('EDITORIAL_ART_PROVENANCE_CHANGED',bid+': Typed execution differs from accepted Art.')
        edit=beat.get('editorial') or {};start=seconds(edit.get('start'));duration=seconds(edit.get('duration'))
        if duration<=0 or abs(start-cursor)>.001 or edit.get('overlap_to_next_frames',0) or edit.get('transition','CUT') not in {'CUT','MATCH_CUT','CARRY','HOLD_THROUGH'}:
            fail('EDITORIAL_TIMELINE_BINDING_UNSUPPORTED',bid+': contiguous native timing without unbound overlaps/dissolves required.','EDITORIAL_RHYTHM')
        raw=[beat['hero_binding'],*beat['support_bindings']];nodes=[];nonvisual=[]
        for binding in raw:
            kind=binding['kind'];ref=binding['semantic_ref']
            if kind not in VISUAL_KINDS:
                events=beat.get('sound_events') or []
                if kind=='NARRATION' and beat.get('narration_mode')!='VOICEOVER':
                    fail('EDITORIAL_NARRATION_BINDING_UNRESOLVED',bid+': Art NARRATION contradicts the accepted Story.')
                if kind=='SILENCE' and beat.get('narration_mode','SILENT')!='SILENT':
                    fail('EDITORIAL_SILENCE_BINDING_UNRESOLVED',bid+': Art SILENCE contradicts the accepted Story voiceover.')
                if kind=='SILENCE' and any(e.get('kind') not in {'SILENCE','NARRATION_ACCENT'} for e in events):
                    fail('EDITORIAL_SILENCE_BINDING_UNRESOLVED',bid+':'+binding['role'],'SOUND_DIRECTION')
                if kind=='SOUND_EVENT' and not any(e.get('semantic_tag')==ref and e.get('kind') not in {'SILENCE','NARRATION_ACCENT'} and e.get('intensity')!='NONE' and not e.get('optional') for e in events):
                    fail('EDITORIAL_SOUND_BINDING_UNRESOLVED',bid+':'+ref,'SOUND_DIRECTION')
                if kind=='CAMERA' and (beat.get('camera') or {}).get('camera_atom',{}).get('atom')!=ref:
                    fail('EDITORIAL_CAMERA_BINDING_UNRESOLVED',bid+':'+ref,'CINEMATOGRAPHY')
                nonvisual.append(deepcopy(binding));continue
            node={'id':ref,'kind':kind,'role':binding['role'],'rect':deepcopy(SLOTS[binding['placement']]),
                  'opacity':ALPHAS[binding['emphasis']] if 'emphasis' in binding else 1,'sourceBinding':deepcopy(binding)}
            if kind in {'TEXT','BACKGROUND'}: node['color']=palette[binding['tone'].lower()]
            if kind=='TEXT':
                node.update({'text':binding['text'],'font':binding['font'].lower(),'fontSize':SIZES[binding['scale']],
                             'weight':700 if binding['weight']=='BOLD' else 400,'align':{'LEADING':'left','CENTER':'center','TRAILING':'right'}[binding['align']]})
            if kind=='ASSET':
                asset=asset_resolver(binding,binding is raw[0])
                if not asset: fail('EDITORIAL_EXACT_ASSET_BINDING_UNAVAILABLE',bid+':'+binding['asset_id'])
                node['assetBinding']=deepcopy(asset)
                if asset not in assets: assets.append(deepcopy(asset))
            nodes.append(node)
        refs={n['id']:n for n in nodes};aliases={}
        for vacancy in (n for n in nodes if n['kind']=='VACANCY'):
            x,y,w,h=vacancy['rect']
            for n in nodes:
                if n['kind'] in {'BACKGROUND','VACANCY'} or n['opacity']<=.01: continue
                xx,yy,ww,hh=n['rect']
                if min(x+w,xx+ww)>max(x,xx) and min(y+h,yy+hh)>max(y,yy):
                    fail('EDITORIAL_AUTHORED_VACANCY_OCCLUDED',bid+':'+vacancy['id'])
        for n in nodes:
            for label in {n['id'],n['role']}:
                aliases.setdefault(label,set()).add(n['id'])
        def target(label,owner):
            matches=aliases.get(label,set())
            if len(matches)!=1: fail('EDITORIAL_SEMANTIC_TARGET_UNBOUND',bid+':'+str(label),owner)
            return next(iter(matches))
        camera=(beat.get('camera') or {}).get('camera_atom') or {}
        camera_ref=target(camera.get('target'),'CINEMATOGRAPHY')
        camera_binding=camera_resolver(beat,camera_ref)
        actions=beat.get('motion_actions') or []
        if not actions: fail('EDITORIAL_MOTION_BINDING_MISSING',bid,'MOTION_PERFORMANCE')
        rate=edit['duration']['rate'];af=edit.get('action_frame');sf=edit.get('settle_frame')
        if any(isinstance(f,bool) or not isinstance(f,int) for f in (af,sf)) or not 0<=af<=sf<edit['duration']['value']:
            fail('EDITORIAL_ACTION_WINDOW_INVALID',bid,'EDITORIAL_RHYTHM')
        directed=[];changing=set()
        for index,action in enumerate(actions):
            ident=action.get('action_id');verb=(action.get('execution') or {}).get('resolved_verb') or action.get('requested_verb')
            if not isinstance(ident,str) or not ident or ident in all_actions: fail('EDITORIAL_ACTION_ID_INVALID',bid,'MOTION_PERFORMANCE')
            if action.get('performer_class')!='SCENE_GRAPH' or verb not in {'TYPE_REVEAL','REVEAL','HIGHLIGHT','DE_EMPHASIZE','SETTLE','STATE_CHANGE','REFRAME_CONTENT'}:
                fail('EDITORIAL_MOTION_BINDING_UNSUPPORTED',bid+':'+str(verb),'MOTION_PERFORMANCE')
            if len(actions)>1 and action.get('overlap_policy') not in {'SERIAL_REQUIRED','HOLD'}:
                fail('EDITORIAL_ACTION_OVERLAP_UNBOUND',bid+':'+ident,'MOTION_PERFORMANCE')
            actor=target(action.get('actor'),'MOTION_PERFORMANCE')
            ref=actor if action.get('target') in {None,'','NONE'} else target(action['target'],'MOTION_PERFORMANCE')
            node=refs[ref];before=deepcopy(previous.get(ref));after=deepcopy(node)
            if node['kind'] in {'BACKGROUND','VACANCY'} and verb!='SETTLE':
                fail('EDITORIAL_PRIMITIVE_ACTION_UNSUPPORTED',bid+':'+ref+':'+verb,'MOTION_PERFORMANCE')
            if verb=='TYPE_REVEAL' and node['kind']!='TEXT': fail('EDITORIAL_TYPE_TARGET_INVALID',bid+':'+ref,'MOTION_PERFORMANCE')
            if verb=='TYPE_REVEAL' and before and not node['text'].startswith(before.get('text','')):
                fail('EDITORIAL_AUTHORED_TRANSITION_MISSING',bid+': TYPE_REVEAL requires an exact prior literal prefix.')
            if verb!='SETTLE':
                if ref in changing: fail('EDITORIAL_INTERMEDIATE_STATE_UNBOUND',bid+':'+ref,'MOTION_PERFORMANCE')
                changing.add(ref)
            if verb in {'STATE_CHANGE','REFRAME_CONTENT','HIGHLIGHT','DE_EMPHASIZE'}:
                differences={k for k in ('text','rect','opacity','color','fontSize','font','weight','align','assetBinding') if (before or {}).get(k)!=node.get(k)}
                required={'REFRAME_CONTENT':{'rect'},'HIGHLIGHT':{'color','opacity','fontSize','weight'},'DE_EMPHASIZE':{'color','opacity','fontSize','weight'}}.get(verb,differences)
                if before is None or before['kind']!=node['kind'] or not differences & required:
                    fail('EDITORIAL_AUTHORED_TRANSITION_MISSING',bid+':'+ref+':'+verb,'ART_DIRECTION')
                allowed={'REFRAME_CONTENT':{'rect','fontSize','align'},'HIGHLIGHT':required,'DE_EMPHASIZE':required}.get(verb,differences)
                if not differences<=allowed: fail('EDITORIAL_AUTHORED_TRANSITION_UNSUPPORTED',bid+':'+ref+':'+verb)
            if verb!='SETTLE' and sf<=af: fail('EDITORIAL_ACTION_WINDOW_EMPTY',bid,'EDITORIAL_RHYTHM')
            begin=start+(af+(sf-af)*index/len(actions))/rate;end=start+(af+(sf-af)*(index+1)/len(actions))/rate
            directed.append({'actionId':ident,'verb':verb,'nodeId':ref,'start':begin,'end':end,'before':before,'after':after})
            previous[ref]=after;all_actions.add(ident)
        scenes.append({'beatId':bid,'start':start,'end':start+duration,'nodes':nodes,'actions':directed,'camera':camera_binding,
                       'nonvisualBindings':nonvisual,'adapterTrace':{'sourceBeatId':bid,'creativeChoiceIntroduced':False,
                            'copyAuthority':'P8_ART_LITERAL','sourceBindingsHash':stable(raw)}})
        # Named native motion cues resolve to the same directed visual timeline.
        for event in beat.get('sound_events') or []:
            if event.get('kind') in {'SILENCE','NARRATION_ACCENT'}:continue
            match=next((a for a in directed if event.get('sync_target')==a['actionId']),None)
            from sound_mix import _sync_time
            at=min(start+duration-1e-6,match['end']) if match else _sync_time(beat,start,duration,event.get('sync_target'))
            if at is not None:
                resolved={'syncTarget':event['sync_target'],'sourceBeatId':bid,'at':at}
                index=len(scenes)
                next_silent=index<len(beats) and any(b['kind']=='SILENCE' for b in beats[index].get('support_bindings',[]))
                if event.get('silence_after') or next_silent:resolved['end']=start+duration
                sound_sync[event['event_id']]=resolved
        previous=deepcopy(refs);cursor=start+duration
    spec={'schema':'StudioP8EditorialSceneV1','scenes':scenes,'duration':cursor,'assets':assets,'soundSync':sound_sync,
          'sourceBoardHash':stable(board),'sourceArtHash':stable(board.get('authored_art') or {}),'copyAuthority':'P8_ART_LITERAL'}
    spec['renderBindingHash']=stable(spec)
    return spec
