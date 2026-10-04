"""Strict boundaries for continuous-master performance plans; no duration estimates."""
import math,re

def pg_number(value,label,positive=False):
    if isinstance(value,bool):raise ValueError(label+': BOOLEAN_NOT_NUMBER')
    try:n=float(value)
    except (ValueError,TypeError,OverflowError):raise ValueError(label+': NUMBER_REQUIRED')
    if not math.isfinite(n) or (positive and n<=0):raise ValueError(label+': FINITE_POSITIVE_REQUIRED' if positive else label+': FINITE_REQUIRED')
    return n

def pg_words(text):return re.findall(r"[\w]+(?:['’][\w]+)*",text or '',flags=re.UNICODE)

def pg_window(start,end,duration,label):
    a=pg_number(start,label+'.start');b=pg_number(end,label+'.end')
    if not 0<=a<b<=duration+1e-7:raise ValueError(label+': OUTSIDE_MASTER_OR_NONPOSITIVE')
    return a,b

def pg_segments(segments,duration,label):
    last=-1
    for i,s in enumerate(segments or []):
        a,b=pg_window(s['start'],s['end'],duration,f'{label}[{i}]')
        if a<last:raise ValueError(label+': NOT_ORDERED')
        last=a

def pg_actor_errors(actor):
    try:
        sp=actor.get('speech') or {};master=sp.get('timing_authority')=='MASTER_AUDIO'
        if not master:return []
        duration=pg_number(sp.get('duration'),'master.duration',positive=True)
        script=actor.get('script') or sp.get('text') or '';tokens=pg_words(script)
        beats=actor.get('script_beats') or []
        ws=sp.get('word_segments') or []
        if tokens and not beats and not ws:raise ValueError('MASTER_ALIGNMENT_REQUIRED')
        if beats:
            pg_segments(beats,duration,'beats')
            if [x.lower() for b in beats for x in pg_words(b.get('text',''))]!=[x.lower() for x in tokens]:raise ValueError('BEAT_TEXT_COVERAGE_MISMATCH')
        if ws:
            pg_segments(ws,duration,'words')
            supplied=[x.lower() for w in ws for x in pg_words(w.get('word',w.get('text',''))) ]
            if supplied!=[x.lower() for x in tokens]:raise ValueError('INCOMPLETE_OR_MISMATCHED_WORD_ALIGNMENT')
        for name in ('phone_segments','viseme_segments'):
            pg_segments(sp.get(name) or [],duration,name)
        for name in ('silence_windows','speaker_rest_windows'):
            for i,w in enumerate(sp.get(name) or []):pg_window(w[0],w[1],duration,f'{name}[{i}]')
        for i,a in enumerate(actor.get('high_level_actions') or []):
            start=pg_number(a.get('start',duration),f'actions[{i}].start')
            end=a.get('end',start+pg_number(a.get('duration',2),f'actions[{i}].duration',positive=True))
            pg_window(start,end,duration,f'actions[{i}]')
        return []
    except (ValueError,TypeError,KeyError,IndexError) as ex:return [{'code':'MASTER_TIMING_INVALID','detail':str(ex)}]

def pg_failure(actor,errors):
    return {'schema':'NexPerformancePlan','status':'FAIL_CLOSED','actor_id':actor.get('actor_id','actor'),'duration':0,'beats':[],'tracks':{'body':[],'speech':{'segments':[]},'social':{'events':[]}},'failure':{'code':'MASTER_TIMING_INVALID','details':errors}}

def pg_attention(event,limits):
    vals=(event or {}).get('controls',event or {})
    aliases={'eyesYaw':'eyes_yaw','eyesPitch':'eyes_pitch','headYaw':'head_yaw','headPitch':'head_pitch','neckYaw':'neck_yaw','neckPitch':'neck_pitch','chestYaw':'chest_yaw','chestPitch':'chest_pitch','headRoll':'head_roll'}
    failures=[]
    for k,v in vals.items():
        kk=aliases.get(k,k)
        if kk not in limits:failures.append({'control':k,'reason':'CONTROL_NOT_ALLOWED'});continue
        try:
            n=pg_number(v,k)
            if abs(n)>pg_number(limits[kk],kk,positive=True):failures.append({'control':k,'reason':'LIMIT_EXCEEDED'})
        except ValueError as ex:failures.append({'control':k,'reason':str(ex)})
    return {'status':'FAIL_CLOSED' if failures else 'PASS','failures':failures,'lower_body_root_unchanged':not failures}

def pg_seat_errors(character,chair):
    try:
        native=(character or {}).get('native_sit') or {}
        for name in ('shoe_min_z','seat_contact_z','posterior_y','knee_y','back_surface_y','hip_width'):pg_number(native[name],'native.'+name,positive=name=='hip_width')
        for name in ('floor_height','seat_surface_height','seat_front_y','seat_rear_y','back_contact_y','usable_seat_width'):pg_number(chair[name],'chair.'+name,positive=name=='usable_seat_width')
        for name,default in [('contact_tolerance',.012),('back_contact_tolerance',.025),('lateral_clearance',.04)]:pg_number(chair.get(name,default),name,positive=True)
        if pg_number(chair.get('forward_y_sign',-1),'forward_y_sign') not in (-1,1):raise ValueError('FORWARD_SIGN_MUST_BE_UNIT')
        return []
    except (ValueError,TypeError,KeyError) as ex:return [{'code':'SEATED_FINITE_GEOMETRY_REQUIRED','detail':str(ex)}]

def pg_sample_viseme(events,t,speaker_owned=True):
    t=pg_number(t,'sample.time')
    if not speaker_owned:return {'viseme':'REST','intensity':0.0,'speaker_owned':False}
    active=[]
    for ev in events or []:
        a=pg_number(ev.get('start',ev.get('start_seconds',0)),'event.start');b=pg_number(ev.get('end',ev.get('end_seconds',a)),'event.end')
        if b<=a:raise ValueError('INVALID_VISEME_WINDOW')
        if a<=t<b:active.append(ev)
    if any(e.get('hard_override') for e in active):return {'viseme':'REST','intensity':0.0,'speaker_owned':speaker_owned}
    if not active:return {'viseme':'REST','intensity':0.0,'speaker_owned':speaker_owned}
    ev=max(enumerate(active),key=lambda p:(pg_number(p[1].get('start',p[1].get('start_seconds',0)),'start'),p[0]))[1]
    v=str(ev.get('viseme',ev.get('intent','REST'))).upper()
    if v not in ('REST','MBP','AH','EE','OH','FV','RELAX'):raise ValueError('UNKNOWN_VISEME:'+v)
    intensity=pg_number(ev.get('intensity',1),'viseme.intensity')
    if not 0<=intensity<=1:raise ValueError('VISEME_INTENSITY_OUT_OF_RANGE')
    return {'viseme':v,'intensity':0.0 if v=='REST' else intensity,'speaker_owned':speaker_owned}
