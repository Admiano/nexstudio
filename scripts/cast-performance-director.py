"""Continuous-master director for the native illustrated cast. No estimated timings."""
import copy,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import nex_performance_logic as logic
from nex_performance_guards import pg_actor_errors,pg_number,pg_segments,pg_window,pg_sample_viseme
VERSION='cast-native-performance-v19'
SUPPORTED_MODES={'direct_presenter','conversational','partner_oriented'}
# Native variants are deliberately separate from the rejected source rig handbank.
NATIVE_CLASSES={'present':'low_offer','open':'low_offer','emphasis':'micro_beat','point':'point','count':'precision','contrast':'contrast','small':'micro_beat','explain':'low_offer','precision':'precision','stop':'micro_beat','offer':'low_offer'}

def compile_scene(request):
    r=copy.deepcopy(request);master=r.get('masterAudio') or {};duration=pg_number(master.get('duration'),'master.duration',positive=True)
    if not master.get('path') or not master.get('sha256'):raise ValueError('MASTER_AUDIO_REFERENCE_AND_HASH_REQUIRED')
    actors=r.get('actors') or []
    for name,position in (r.get('targets') or {}).items():
        if not isinstance(position,(list,tuple)) or len(position)!=3:raise ValueError('TARGET_REQUIRES_WORLD_XYZ:'+name)
        for coordinate in position:pg_number(coordinate,'target.'+name)
    if not actors:raise ValueError('ACTORS_REQUIRED')
    ids=[a.get('actor_id') for a in actors]
    if any(not isinstance(aid,str) or not aid for aid in ids) or len(ids)!=len(set(ids)):raise ValueError('ACTOR_IDS_INVALID')
    turns=r.get('turns') or [{'actor_id':a['actor_id'],'start':b['start'],'end':b['end'],'semantic_intent':b['semantic_intent']} for a in actors for b in a.get('script_beats',[])]
    turns=sorted(turns,key=lambda t:(t['start'],t['end']))
    pg_segments(turns,duration,'turns')
    for t in turns:
        if t['actor_id'] not in ids or (t.get('recipient_id') and t['recipient_id'] not in ids):raise ValueError('UNKNOWN_TURN_ACTOR')
    for cue in r.get('floor_cues',[]):
        pg_window(cue['time'],cue['time']+cue.get('duration',.32),duration,'floor_cue')
        if cue.get('actor_id') not in ids:raise ValueError('UNKNOWN_FLOOR_CUE_ACTOR')
    floor=logic.floor_from_turns(turns,actors,r.get('seed','cast-v19'),r.get('floor_cues'))
    reflective=logic.reflective_response_events(turns,r.get('seed','cast-v19'));social=logic.social_nuance_events(turns,r.get('seed','cast-v19'))
    compiled=[]
    for a in actors:
        aid=a['actor_id'];mode=a.get('camera_relationship','direct_presenter')
        if a.get('character') not in ('male','female'):raise ValueError('NATIVE_CHARACTER_REQUIRED')
        if mode not in SUPPORTED_MODES:raise ValueError('CAMERA_RELATIONSHIP_NOT_ADMITTED')
        if a.get('posture','standing') not in ('standing','seated'):raise ValueError('POSTURE_NOT_ADMITTED')
        a.setdefault('speech',{});a['speech'].update(duration=duration,timing_authority='MASTER_AUDIO')
        errors=pg_actor_errors(a)
        if errors:raise ValueError(json.dumps(errors))
        beats=[]
        for i,b in enumerate(a.get('script_beats') or []):
            intent=logic.intent_family(b.get('semantic_intent','inform'))
            if intent not in logic.POL['intents']:raise ValueError('SEMANTIC_INTENT_NOT_ADMITTED:'+intent)
            beats.append(dict(b,beat_id=f'{aid}:{i}',semantic_intent=intent,emphasis_anchors=b.get('emphasis_anchors',[]),pause_state=b.get('pause_state','speech')))
        logic.apply_narrative_roles(beats,a,r.get('seed','cast-v19'))
        selected=logic.choose_gestures(beats,a.get('personality','calm'),r.get('seed','cast-v19')+'|'+aid,'strict_right','professional_restrained')
        gestures=[]
        for b,g in zip(beats,selected):
            b['gesture']=g
            if g['suppress']:continue
            native=NATIVE_CLASSES.get(g['class'])
            if native=='point' and b['semantic_intent']!='point':native='micro_beat'
            if b['semantic_intent']=='point':raise ValueError('PHYSICAL_SCREEN_POINT_REQUIRES_ADMISSION')
            if native is None:raise ValueError('NATIVE_GESTURE_CLASS_NOT_ADMITTED:'+str(g['class']))
            if native not in ('micro_beat','low_offer'):raise ValueError('NATIVE_VARIANT_REQUIRES_RENDER_ADMISSION:'+native)
            stroke=g['stroke_time'];start=max(b['start'],stroke-g['prepare_s']);end=min(b['end'],stroke+g['hold_s']+g['recovery_s'])
            # Fit to the available spoken interval. The master is never extended.
            if end-start<.22:continue
            gestures.append({'start':start,'stroke':stroke,'holdEnd':min(stroke+g['hold_s'],end-(end-start)*.2),'end':end,'variant':native,'side':g['dominant_manipulator'],'strength':min(.70,g['amplitude']),'secondary_policy':g['secondary_policy']})
        own=logic._merge_windows([[t['start'],t['end']] for t in turns if t['actor_id']==aid])
        cuts=[]
        for e in floor:
            if e['intent']=='SOFT_INTERRUPT' and e['parameters'].get('from_speaker')==aid:
                at=e['parameters']['takeover_time'];cuts.extend([[at,b] for x,b in own if x<at<b])
        effective=logic._subtract_windows(own,cuts)
        rest=logic._subtract_windows([[0,duration]],effective)
        events=[e for e in reflective+social+floor if e['parameters'].get('actor_id')==aid]
        events+=logic.listener_life_events_for_actor(aid,turns,a,r.get('seed','cast-v19')+'|'+aid)
        speech=copy.deepcopy(a['speech'].get('viseme_segments') or [])
        # Speaking actors require real aligned phonemes; no word-based mouth estimates.
        if own and not speech:raise ValueError('ALIGNED_PHONEMES_REQUIRED:'+aid)
        if own:
            words=a['speech'].get('word_segments') or []
            if not words:raise ValueError('NATIVE_WORD_ALIGNMENT_REQUIRED:'+aid)
            coverage=logic._merge_windows([[e['start'],e['end']] for e in speech]+a['speech'].get('silence_windows',[]))
            for word in words:
                gaps=logic._subtract_windows([[word['start'],word['end']]],coverage)
                if sum(b-x for x,b in gaps)>.001:raise ValueError('INCOMPLETE_NATIVE_PHONEME_COVERAGE:'+aid)
        for e in speech:pg_sample_viseme([e],e['start'],True)
        for x,b in rest:speech.append({'start':x,'end':b,'viseme':'REST','hard_override':True,'reason':'NON_SPEAKER'})
        for x,b in a['speech'].get('silence_windows',[]):speech.append({'start':x,'end':b,'viseme':'REST','hard_override':True,'reason':'WAVEFORM_SILENCE'})
        speech.sort(key=lambda e:(e['start'],not e.get('hard_override',False)))
        compiled.append({'actor_id':aid,'character':a['character'],'personality':a.get('personality','calm'),'camera_relationship':mode,'posture':a.get('posture','standing'),'duration':duration,'beats':beats,'gestures':gestures,'attention':logic.plan_attention(beats,a.get('personality','calm'),mode,aid,r.get('seed','cast-v19')),'social':sorted(events,key=lambda e:(e['start'],e['end'])),'narrative':logic.narrative_events(beats,a),'speech':speech,'speaker_active_windows':effective,'speaker_rest_windows':rest,'recipient_id':a.get('recipient_id'),'staging':a.get('staging',{}),'targets':r.get('targets',{}),'handAdmission':['right']})
    return {'version':VERSION,'duration':duration,'masterAudio':master,'actors':compiled,'floor':floor,'physicalAdmission':'native variants require per-character validation','sourceAudioRetimed':False}

if __name__=='__main__':
    source,destination=map(Path,sys.argv[1:3]);destination.write_text(json.dumps(compile_scene(json.loads(source.read_text())),indent=2))
