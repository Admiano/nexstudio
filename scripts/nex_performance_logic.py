"""Audited, rig-free planning functions isolated from the frozen Nex performance core.

Admission scope: planning decisions, contact prerequisites and finite-input transition mathematics only. This module does not bind
MakeHuman bones, keys, seats, props or audio. It does not certify a rendered
MakeHuman performance. Physical execution, speech sampling and duration
estimation and the old attention/seating validators are intentionally excluded
after audit counterexamples. Callers must prevalidate finite, ordered timestamps,
known actor/intent IDs and master-audio bounds. Gesture classes are selection
labels; they grant no admission to an old pose or untested MakeHuman action.
"""
from __future__ import annotations
import json,hashlib,math,re,copy
POLICY_DATA = {'data/gesture_policy.json': {'minimum_gap_s': 1.25, 'repeat_cooldown_beats': 2, 'phase_fractions': {'prepare': 0.2, 'stroke': 0.22, 'hold': 0.2, 'recovery': 0.3, 'rest': 0.08}, 'classes': {'no_gesture': {'hand_state': 'relaxed', 'orientation': 'neutral', 'bilateral': False}, 'open': {'hand_state': 'open', 'orientation': 'palm-front', 'bilateral': False}, 'present': {'hand_state': 'present', 'orientation': 'palm-front', 'bilateral': False}, 'point': {'hand_state': 'point', 'orientation': 'edge/target', 'bilateral': False}, 'offer': {'hand_state': 'offer', 'orientation': 'palm-up', 'bilateral': False}, 'count': {'hand_state': 'count', 'orientation': 'palm-front', 'bilateral': False}, 'stop': {'hand_state': 'stop', 'orientation': 'palm-front', 'bilateral': False}, 'receive': {'hand_state': 'receive', 'orientation': 'palm-up', 'bilateral': False}, 'support_large': {'hand_state': 'support_large', 'orientation': 'contact', 'bilateral': True}}}, 'data/intent_policy.json': {'priority': ['question', 'disagree', 'agree', 'acknowledge', 'answer', 'doubt', 'reassure', 'warn', 'invite', 'offer', 'contrast', 'transition', 'instruction', 'demonstration', 'enumerate', 'emphasize', 'think', 'remember', 'joke', 'explain', 'evidence', 'celebrate', 'concern', 'surprise', 'inform'], 'intents': {'question': {'regex': ['\\?\\s*$', '^\\s*(why|how|what|when|where|who)\\b'], 'delivery': 'inquisitive', 'gesture_score': 0.34, 'gestures': ['open', 'present'], 'expression': 'curious', 'head': 'react', 'gaze': 'recipient', 'stillness_bias': 0.42}, 'contrast': {'regex': ['\\b(but|however|instead|rather than|on the other hand|while|yet|not .* but)\\b'], 'delivery': 'contrastive', 'gesture_score': 0.62, 'gestures': ['present', 'open'], 'expression': 'serious', 'head': 'lead', 'gaze': 'audience', 'stillness_bias': 0.24}, 'transition': {'regex': ['\\b(now|next|then|finally|meanwhile|moving on|from here|so now)\\b'], 'delivery': 'transition', 'gesture_score': 0.42, 'gestures': ['present', 'open'], 'expression': 'attentive', 'head': 'orient', 'gaze': 'audience', 'stillness_bias': 0.34}, 'enumerate': {'regex': ['\\b(first|second|third|fourth|fifth)\\b', '\\b(one|two|three|four|five)\\b.{0,25}\\b(parts|steps|things|reasons|points|ways|items)\\b', '[:;]'], 'delivery': 'structured', 'gesture_score': 0.66, 'gestures': ['count', 'present'], 'expression': 'attentive', 'head': 'lead', 'gaze': 'audience', 'stillness_bias': 0.18}, 'warn': {'regex': ['\\b(warn|warning|danger|risk|avoid|never|must not|do not|cannot)\\b'], 'delivery': 'caution', 'gesture_score': 0.54, 'gestures': ['stop', 'point'], 'expression': 'concerned', 'head': 'lead', 'gaze': 'audience', 'stillness_bias': 0.28}, 'reassure': {'regex': ['\\b(safe|okay|fine|you can|we can|no problem|rest assured|do not worry|don.t worry)\\b'], 'delivery': 'reassuring', 'gesture_score': 0.36, 'gestures': ['open', 'present'], 'expression': 'happy', 'head': 'attend', 'gaze': 'recipient', 'stillness_bias': 0.42}, 'invite': {'regex': ['\\b(join|come|try|take a look|consider|imagine|let us|let.s)\\b'], 'delivery': 'inviting', 'gesture_score': 0.56, 'gestures': ['offer', 'present'], 'expression': 'happy', 'head': 'lead', 'gaze': 'recipient', 'stillness_bias': 0.22}, 'offer': {'regex': ['\\b(offer|give|share|here is|here.s|take this)\\b'], 'delivery': 'offering', 'gesture_score': 0.7, 'gestures': ['offer', 'present'], 'expression': 'attentive', 'head': 'lead', 'gaze': 'recipient', 'stillness_bias': 0.14}, 'agree': {'regex': ['\\b(yes|exactly|correct|right|i agree|that.s true|indeed)\\b'], 'delivery': 'affirming', 'gesture_score': 0.24, 'gestures': ['no_gesture', 'open'], 'expression': 'happy', 'head': 'react', 'gaze': 'recipient', 'stillness_bias': 0.58}, 'disagree': {'regex': ['\\b(no|not really|i disagree|that.s wrong|incorrect|actually not)\\b'], 'delivery': 'corrective', 'gesture_score': 0.38, 'gestures': ['stop', 'open'], 'expression': 'serious', 'head': 'react', 'gaze': 'recipient', 'stillness_bias': 0.46}, 'celebrate': {'regex': ['\\b(great|excellent|amazing|success|won|win|celebrate|congratulations)\\b'], 'delivery': 'celebratory', 'gesture_score': 0.62, 'gestures': ['open', 'present'], 'expression': 'happy', 'head': 'react', 'gaze': 'audience', 'stillness_bias': 0.16}, 'concern': {'regex': ['\\b(problem|issue|worry|concern|failure|failed|hard|difficult|struggle)\\b'], 'delivery': 'concerned', 'gesture_score': 0.28, 'gestures': ['open', 'no_gesture'], 'expression': 'concerned', 'head': 'listen', 'gaze': 'recipient', 'stillness_bias': 0.54}, 'surprise': {'regex': ['\\b(surprising|surprised|unexpected|suddenly|wow|incredible)\\b', '!$'], 'delivery': 'surprised', 'gesture_score': 0.44, 'gestures': ['open', 'present'], 'expression': 'surprised', 'head': 'react', 'gaze': 'audience', 'stillness_bias': 0.28}, 'instruction': {'regex': ['^(please )?(press|click|tap|move|turn|open|close|pick|place|hold|keep|make|use|choose|select)\\b', '\\b(you should|you need to|you must)\\b'], 'delivery': 'instructional', 'gesture_score': 0.64, 'gestures': ['point', 'present'], 'expression': 'attentive', 'head': 'lead', 'gaze': 'target', 'stillness_bias': 0.18}, 'demonstration': {'regex': ['\\b(watch|demonstrate|here.s how|this is how|look at)\\b', '^\\s*show\\b'], 'delivery': 'demonstrative', 'gesture_score': 0.72, 'gestures': ['present', 'point'], 'expression': 'attentive', 'head': 'orient', 'gaze': 'target', 'stillness_bias': 0.12}, 'evidence': {'regex': ['\\b\\d+[,.]?\\d*\\b', '\\b(percent|million|billion|thousand|data|evidence|research|results|revenue|users|jobs)\\b'], 'delivery': 'evidence', 'gesture_score': 0.46, 'gestures': ['present', 'count'], 'expression': 'serious', 'head': 'lead', 'gaze': 'audience', 'stillness_bias': 0.36}, 'explain': {'regex': ['\\b(because|means|works|reason|therefore|so that|in other words|for example|the point is)\\b'], 'delivery': 'explanatory', 'gesture_score': 0.58, 'gestures': ['present', 'open'], 'expression': 'attentive', 'head': 'lead', 'gaze': 'audience', 'stillness_bias': 0.24}, 'inform': {'regex': ['.+'], 'delivery': 'informative', 'gesture_score': 0.22, 'gestures': ['no_gesture', 'open'], 'expression': 'attentive', 'head': 'attend', 'gaze': 'audience', 'stillness_bias': 0.62}, 'answer': {'regex': ['\\b(the answer is|the reason is|my answer is|the result is)\\b', '^\\s*(because|since)\\b'], 'delivery': 'responsive', 'gesture_score': 0.34, 'gestures': ['open', 'present'], 'expression': 'attentive', 'head': 'attend', 'gaze': 'recipient', 'stillness_bias': 0.46}, 'acknowledge': {'regex': ['\\b(got it|understood|i see|makes sense|fair enough|okay|alright|noted)\\b'], 'delivery': 'acknowledging', 'gesture_score': 0.18, 'gestures': ['no_gesture', 'open'], 'expression': 'happy', 'head': 'react', 'gaze': 'recipient', 'stillness_bias': 0.68}, 'doubt': {'regex': ['\\b(maybe|perhaps|not sure|uncertain|doubt|questionable|i wonder|does that really|is that really)\\b'], 'delivery': 'doubtful', 'gesture_score': 0.3, 'gestures': ['open', 'no_gesture'], 'expression': 'curious', 'head': 'react', 'gaze': 'recipient', 'stillness_bias': 0.52}, 'think': {'regex': ['\\b(think|thinking|consider|let me think|hmm|weigh|reflect)\\b'], 'delivery': 'thoughtful', 'gesture_score': 0.16, 'gestures': ['no_gesture', 'open'], 'expression': 'thinking', 'head': 'listen', 'gaze': 'away', 'stillness_bias': 0.74}, 'remember': {'regex': ['\\b(remember|recall|used to|back then|previously|earlier)\\b'], 'delivery': 'reflective', 'gesture_score': 0.22, 'gestures': ['no_gesture', 'open'], 'expression': 'thinking', 'head': 'react', 'gaze': 'away', 'stillness_bias': 0.66}, 'emphasize': {'regex': ['\\b(important|crucial|critical|key point|the key|especially|above all|what matters|really matters)\\b'], 'delivery': 'emphatic', 'gesture_score': 0.7, 'gestures': ['present', 'point', 'open'], 'expression': 'serious', 'head': 'lead', 'gaze': 'audience', 'stillness_bias': 0.14}, 'joke': {'regex': ['\\b(just kidding|kidding|funny|joke|laugh|haha|ha ha|plot twist)\\b'], 'delivery': 'amused', 'gesture_score': 0.3, 'gestures': ['open', 'no_gesture'], 'expression': 'happy', 'head': 'react', 'gaze': 'recipient', 'stillness_bias': 0.48}}}, 'data/personality_presets.json': {'presets': {'calm': {'gestureAmplitude': 0.82, 'gestureFrequency': 0.78, 'idleActivity': 0.72, 'headTiltTendency': 0.28, 'gazeHoldDuration': 2.2, 'reactionLatency': 0.24, 'stanceWidth': 0.96, 'movementEnergy': 0.78, 'turnSharpness': 0.86, 'armSwingScale': 0.85, 'bodyOpenness': 0.95, 'handRestOpenness': 0.95, 'nodFrequency': 2.0, 'conversationListenerActivity': 0.82, 'movementTempoBias': 0.88, 'anticipationAmplitude': 0.85, 'settleDuration': 1.25}, 'cheerful': {'gestureAmplitude': 1.15, 'gestureFrequency': 1.18, 'idleActivity': 1.1, 'headTiltTendency': 0.55, 'gazeHoldDuration': 1.3, 'reactionLatency': 0.13, 'stanceWidth': 1.0, 'movementEnergy': 1.1, 'turnSharpness': 1.05, 'armSwingScale': 1.08, 'bodyOpenness': 1.18, 'handRestOpenness': 1.18, 'nodFrequency': 6.0, 'conversationListenerActivity': 1.15, 'movementTempoBias': 1.08, 'anticipationAmplitude': 1.05, 'settleDuration': 0.92}, 'confident': {'gestureAmplitude': 1.12, 'gestureFrequency': 0.95, 'idleActivity': 0.84, 'headTiltTendency': 0.18, 'gazeHoldDuration': 2.4, 'reactionLatency': 0.1, 'stanceWidth': 1.12, 'movementEnergy': 1.08, 'turnSharpness': 1.18, 'armSwingScale': 1.05, 'bodyOpenness': 1.25, 'handRestOpenness': 1.12, 'nodFrequency': 3.0, 'conversationListenerActivity': 0.92, 'movementTempoBias': 1.04, 'anticipationAmplitude': 0.95, 'settleDuration': 1.0}, 'shy': {'gestureAmplitude': 0.72, 'gestureFrequency': 0.68, 'idleActivity': 0.62, 'headTiltTendency': 0.62, 'gazeHoldDuration': 0.85, 'reactionLatency': 0.34, 'stanceWidth': 0.86, 'movementEnergy': 0.72, 'turnSharpness': 0.82, 'armSwingScale': 0.76, 'bodyOpenness': 0.72, 'handRestOpenness': 0.78, 'nodFrequency': 2.0, 'conversationListenerActivity': 0.72, 'movementTempoBias': 0.9, 'anticipationAmplitude': 0.78, 'settleDuration': 1.3}, 'energetic': {'gestureAmplitude': 1.32, 'gestureFrequency': 1.4, 'idleActivity': 1.42, 'headTiltTendency': 0.42, 'gazeHoldDuration': 0.9, 'reactionLatency': 0.07, 'stanceWidth': 1.06, 'movementEnergy': 1.38, 'turnSharpness': 1.25, 'armSwingScale': 1.28, 'bodyOpenness': 1.2, 'handRestOpenness': 1.22, 'nodFrequency': 8.0, 'conversationListenerActivity': 1.32, 'movementTempoBias': 1.22, 'anticipationAmplitude': 1.22, 'settleDuration': 0.72}, 'serious': {'gestureAmplitude': 0.9, 'gestureFrequency': 0.72, 'idleActivity': 0.64, 'headTiltTendency': 0.08, 'gazeHoldDuration': 2.6, 'reactionLatency': 0.18, 'stanceWidth': 1.04, 'movementEnergy': 0.9, 'turnSharpness': 1.12, 'armSwingScale': 0.88, 'bodyOpenness': 0.92, 'handRestOpenness': 0.85, 'nodFrequency': 1.0, 'conversationListenerActivity': 0.76, 'movementTempoBias': 0.96, 'anticipationAmplitude': 0.92, 'settleDuration': 1.2}, 'playful': {'gestureAmplitude': 1.28, 'gestureFrequency': 1.35, 'idleActivity': 1.28, 'headTiltTendency': 0.78, 'gazeHoldDuration': 0.95, 'reactionLatency': 0.09, 'stanceWidth': 1.02, 'movementEnergy': 1.25, 'turnSharpness': 1.16, 'armSwingScale': 1.2, 'bodyOpenness': 1.24, 'handRestOpenness': 1.27, 'nodFrequency': 9.0, 'conversationListenerActivity': 1.3, 'movementTempoBias': 1.14, 'anticipationAmplitude': 1.25, 'settleDuration': 0.82}, 'authoritative': {'gestureAmplitude': 1.15, 'gestureFrequency': 0.78, 'idleActivity': 0.7, 'headTiltTendency': 0.1, 'gazeHoldDuration': 2.8, 'reactionLatency': 0.09, 'stanceWidth': 1.18, 'movementEnergy': 1.05, 'turnSharpness': 1.25, 'armSwingScale': 1.0, 'bodyOpenness': 1.3, 'handRestOpenness': 1.08, 'nodFrequency': 2.0, 'conversationListenerActivity': 0.7, 'movementTempoBias': 1.0, 'anticipationAmplitude': 1.0, 'settleDuration': 1.15}, 'warm': {'gestureAmplitude': 1.05, 'gestureFrequency': 1.05, 'idleActivity': 0.9, 'headTiltTendency': 0.48, 'gazeHoldDuration': 1.8, 'reactionLatency': 0.14, 'stanceWidth': 0.98, 'movementEnergy': 0.98, 'turnSharpness': 0.95, 'armSwingScale': 0.98, 'bodyOpenness': 1.2, 'handRestOpenness': 1.22, 'nodFrequency': 5.0, 'conversationListenerActivity': 1.28, 'movementTempoBias': 1.0, 'anticipationAmplitude': 1.05, 'settleDuration': 1.05}, 'reserved': {'gestureAmplitude': 0.76, 'gestureFrequency': 0.62, 'idleActivity': 0.56, 'headTiltTendency': 0.16, 'gazeHoldDuration': 1.7, 'reactionLatency': 0.28, 'stanceWidth': 0.9, 'movementEnergy': 0.7, 'turnSharpness': 0.88, 'armSwingScale': 0.78, 'bodyOpenness': 0.78, 'handRestOpenness': 0.76, 'nodFrequency': 1.0, 'conversationListenerActivity': 0.64, 'movementTempoBias': 0.86, 'anticipationAmplitude': 0.8, 'settleDuration': 1.35}}}}

def load_json(rel):
    if rel not in POLICY_DATA: raise KeyError(rel)
    return copy.deepcopy(POLICY_DATA[rel])

def clamp(x,a=0.0,b=1.0):
    try:x=float(x)
    except:return a
    return max(a,min(b,x))

def stable_unit(text:str)->float:
    h=hashlib.sha256(text.encode('utf-8')).digest()
    return int.from_bytes(h[:8],'big')/(2**64-1)

def stable_choice(items,key):
    if not items:return None
    u=stable_unit(key)
    return items[min(len(items)-1,int(u*len(items)))]

def deep(obj): return copy.deepcopy(obj)

def canonical(s):
    return re.sub(r'_+','_',re.sub(r'[^a-z0-9_]+','_',str(s or '').strip().lower().replace('-','_').replace(' ','_'))).strip('_')

PRE=load_json('data/personality_presets.json')['presets']

def get(name='calm'):return PRE.get(name,PRE['calm'])

def personality_sem(name='calm'):
    p=get(name)
    return {
      'gesture_budget_scale':clamp(p['gestureFrequency']/1.0,0.35,1.6),
      'gesture_amplitude_scale':clamp(p['gestureAmplitude']/1.0,0.45,1.45),
      'reaction_latency_s':max(.04,float(p['reactionLatency'])),
      'attention_hold_s':max(.45,float(p['gazeHoldDuration'])),
      'head_tilt_tendency':clamp(p['headTiltTendency'],0,1),
      'energy':clamp(p['movementEnergy']/1.35),
      'openness':clamp(p['bodyOpenness']/1.35),
      'listener_activity':clamp(p['conversationListenerActivity']/1.35),
      'tempo_scale':clamp(p['movementTempoBias'],.65,1.35),
      'settle_s':max(.3,float(p['settleDuration'])),
      'idle_activity':clamp(p['idleActivity']/1.45)
    }

POL=load_json('data/intent_policy.json')

def infer_intent(text):
    t=(text or '').strip()
    for name in POL['priority']:
        spec=POL['intents'][name]
        for pat in spec['regex']:
            if re.search(pat,t,re.I):return name
    return 'inform'

def intent_family(intent):
    k=str(intent or '').strip().lower().replace('_','-')
    if k in POL['intents']:return k
    rules=[('question','question'),('answer','answer'),('acknowledg','acknowledge'),('doubt','doubt'),('uncertain','doubt'),('think','think'),('remember','remember'),('recall','remember'),('emphas','emphasize'),('important','emphasize'),('joke','joke'),('amuse','joke'),('contrast','contrast'),('transition','transition'),('evidence','evidence'),('metric','evidence'),('explain','explain'),('infrastructure','explain'),('integration','explain'),('enumerat','enumerate'),('warn','warn'),('caution','warn'),('reassur','reassure'),('offer','offer'),('invite','invite'),('agree','agree'),('disagree','disagree'),('celebrat','celebrate'),('concern','concern'),('surpris','surprise'),('instruction','instruction'),('demonstrat','demonstration')]
    for token,fam in rules:
        if token in k:return fam
    return 'inform'

def intent_spec(intent):return POL['intents'].get(intent_family(intent),POL['intents']['inform'])

GP=load_json('data/gesture_policy.json')

_PRIORITY_BONUS={
    'emphasize':.22,'demonstration':.20,'instruction':.18,'enumerate':.17,'offer':.16,
    'contrast':.14,'explain':.14,'transition':.10,'question':.09,'warn':.12,
    'agree':.08,'disagree':.11,'evidence':.08,'inform':0.0
}

def _target_budget(beats,ps,performance_style):
    speech=[b for b in beats if b.get('pause_state') not in ('pause','silence') and (b.get('text') or '').strip()]
    if not speech:return 0
    span=max(0.0,max(b['end'] for b in speech)-min(b['start'] for b in speech))
    density=ps['gesture_budget_scale']
    restrained='restrained' in (performance_style or '').lower()
    # Professional restrained delivery targets roughly one meaningful gesture every 10-14 seconds,
    # then personality scales the budget. This is a global semantic budget, not fixed beat timing.
    interval=10.8 if restrained else 8.2
    target=round((span/max(1.0,interval))*density)
    # A longer presenter should never accidentally become a mouth-only mannequin, but stillness remains dominant.
    floor=1 if span>=5 else 0
    if restrained and span>=24:floor=2
    if restrained and span>=40:floor=3
    ceiling=max(1,int(len(speech)*(.38 if restrained else .52)+.5))
    return int(max(floor,min(ceiling,target)))

def choose_gestures(beats,personality='calm',seed='0',preferred='right',performance_style='professional_restrained'):
    ps=personality_sem(personality);density=ps['gesture_budget_scale']
    if 'restrained' in (performance_style or '').lower():density*=.78
    target=_target_budget(beats,ps,performance_style)
    candidates=[]
    # Build an eligible semantic candidate per beat. NO_GESTURE is expressed by not selecting the beat.
    for i,b in enumerate(beats):
        spec=intent_spec(b['semantic_intent']);dur=b['end']-b['start'];key=f'{seed}|{b["beat_id"]}|{b["text"]}'
        deliberate=b.get('pause_state') in ('pause','silence') or b['text'].strip().lower() in {'or…','or...','or'}
        actual=[x for x in spec.get('gestures',[]) if x!='no_gesture']
        if deliberate or not actual or dur<.55:continue
        cls=stable_choice(actual,key+'|class')
        base=spec['gesture_score']*density*(1-spec.get('stillness_bias',0)*.45)
        base*=float(b.get('narrative_gesture_bias',1.0))
        # Semantic strength + emphasis + a small deterministic jitter. The jitter may vary optional behavior,
        # but cannot override a deliberate pause or create unlimited gestures.
        score=base+_PRIORITY_BONUS.get(b['semantic_intent'],.04)+float(b.get('narrative_priority_bonus',0.0))
        if b.get('emphasis_anchors'):score+=.055
        score+=.07*(stable_unit(key+'|rank')-.5)
        stroke=(b.get('emphasis_anchors') or [b['start']+dur*(.48+.12*(stable_unit(key+'|stroke')-.5))])[0]
        if b.get('narrative_role')=='REVEAL': stroke=b['start']+dur*(.60+.08*(stable_unit(key+'|reveal_stroke')-.5))
        candidates.append({'index':i,'score':score,'class':cls,'stroke':stroke,'key':key,'spec':spec,'dur':dur})
    # Highest semantic value wins, subject to a real time-separation constraint.
    selected=[]
    for c in sorted(candidates,key=lambda x:(-x['score'],x['stroke'],x['index'])):
        if len(selected)>=target:break
        if any(abs(c['stroke']-s['stroke'])<GP['minimum_gap_s'] for s in selected):continue
        selected.append(c)
    selected={c['index']:c for c in selected}
    out=[];history=[]
    for i,b in enumerate(beats):
        c=selected.get(i)
        if c is None:
            out.append({'suppress':True,'class':None,'dominant_manipulator':'none','secondary_policy':'rest','amplitude':0.0,'prepare_s':0.0,'stroke_time':None,'hold_s':0.0,'recovery_s':0.0,'semantic_hand_intent':'relaxed','orientation_intent':'neutral','target':None,'reason':'NO_GESTURE: global semantic budget/stillness/spacing'})
            history.append('no_gesture');continue
        cls=c['class'];meta=GP['classes'].get(cls,GP['classes']['open']);key=c['key'];dur=c['dur'];stroke=c['stroke']
        # Repetition control: choose a semantically legal alternate if the immediately recent visible gesture repeats.
        visible_recent=[(x[0] if isinstance(x,tuple) else x) for x in history if x!='no_gesture'][-GP['repeat_cooldown_beats']:]
        if cls in visible_recent:
            alts=[x for x in c['spec'].get('gestures',[]) if x!='no_gesture' and x not in visible_recent]
            if alts:cls=stable_choice(alts,key+'|alt');meta=GP['classes'].get(cls,GP['classes']['open'])
        amp=clamp(.48*ps['gesture_amplitude_scale']*(.85+.3*stable_unit(key+'|amp')),.18,.88)
        prepare=min(.55,max(.16,dur*.18));hold=min(.45,max(.08,dur*.12));recovery=min(.72,max(.22,dur*.22))
        # preferred_manipulator is a bias, not a robotic permanent-side lock.
        # Explicit strict_* values remain fixed; ordinary left/right preference allows sparse off-hand use.
        recent_hands=[x for x in history if isinstance(x,tuple)]
        if preferred in ('strict_left','strict_right'):
            dominant=preferred.replace('strict_','')
        elif preferred in ('left','right'):
            other='left' if preferred=='right' else 'right'
            u=stable_unit(key+'|hand_variation')
            # Roughly 24% off-hand baseline; after two visible same-hand gestures, raise the chance
            # so a long conversation does not look like a one-arm puppet.
            same_run=len(recent_hands)>=2 and recent_hands[-1][1]==preferred and recent_hands[-2][1]==preferred
            dominant=other if u < (.48 if same_run else .24) else preferred
        else:
            dominant='right' if stable_unit(key+'|hand')>.35 else 'left'
        secondary='compound' if meta.get('bilateral') else 'rest'
        out.append({'suppress':False,'class':cls,'dominant_manipulator':dominant,'secondary_policy':secondary,'amplitude':round(amp,4),'prepare_s':round(prepare,4),'stroke_time':round(stroke,4),'hold_s':round(hold,4),'recovery_s':round(recovery,4),'semantic_hand_intent':meta.get('hand_state'),'orientation_intent':meta.get('orientation'),'target':None,'reason':f'global_semantic_budget; semantic_intent={b["semantic_intent"]}; rank={c["score"]:.4f}; preferred_hand={preferred}; executed_hand={dominant}'})
        history.append((cls,dominant))
    return out

def plan_attention(beats,personality='calm',camera_relationship='direct_presenter',actor_id='actor',seed='0'):
    ps=personality_sem(personality);events=[]
    prev_end=None
    for i,b in enumerate(beats):
        # Use real semantic/speech gaps as the safest place for sparse gaze release.
        # This is deterministic, personality-bounded, and not tied to any benchmark transcript.
        if prev_end is not None:
            gap=max(0.0,float(b['start'])-float(prev_end))
            if gap>=.55 and b['semantic_intent'] not in ('question','warn') and stable_unit(f'{seed}|{actor_id}|{i}|interbeat_gaze_break')<.48:
                rel_start=float(prev_end)+min(.12,gap*.18)
                rel_end=min(float(b['start'])-.12,rel_start+min(.38,gap*.42))
                if rel_end>rel_start+.06:
                    events.append({'start':round(rel_start,4),'end':round(rel_end,4),'intent':'RELEASE','parameters':{'target':{'type':'away','id':None},'focus':.30,'reason':'semantic_silence_gaze_break'}})
                    if float(b['start'])-rel_end>.08:
                        events.append({'start':round(rel_end,4),'end':round(float(b['start']),4),'intent':'REORIENT','parameters':{'target':{'type':'camera' if camera_relationship=='direct_presenter' else 'person' if camera_relationship in ('conversational','partner_oriented') else 'forward','id':b.get('recipient_id')},'eyes_lead':True,'reason':'return_before_next_beat'}})
        spec=intent_spec(b['semantic_intent']);intent_target=spec.get('gaze','audience')
        if camera_relationship=='direct_presenter':base='camera'
        elif camera_relationship in ('conversational','partner_oriented'):base='person'
        else:base='forward'
        target=base
        if intent_target=='target':target='object'
        elif intent_target=='recipient':target='person'
        a,bend=b['start'],b['end'];dur=bend-a
        latency=min(ps['reaction_latency_s'],dur*.2)
        orient_end=min(bend,a+max(.12,latency+.16))
        hold_end=min(bend,max(orient_end,bend-min(.28,dur*.12)))
        events.append({'start':round(a,4),'end':round(orient_end,4),'intent':'ORIENT','parameters':{'target':{'type':target,'id':b.get('recipient_id')},'eyes_lead':True,'head_follow':True,'body_follow_strength':round(.12+.18*ps['openness'],3)}})
        # sparse deterministic gaze break only on longer low-criticality beats
        break_allowed=dur>3.2 and b['semantic_intent'] not in ('question','warn') and stable_unit(f'{seed}|{actor_id}|{i}|gaze_break')<.42
        if break_allowed:
            bs=a+dur*.63;be=min(bend,bs+min(.38,dur*.10))
            events.append({'start':round(orient_end,4),'end':round(bs,4),'intent':'SUSTAIN','parameters':{'target':{'type':target,'id':b.get('recipient_id')},'focus':round(.70+.18*ps['energy'],3)}})
            events.append({'start':round(bs,4),'end':round(be,4),'intent':'RELEASE','parameters':{'target':{'type':'away','id':None},'focus':.35}})
            events.append({'start':round(be,4),'end':round(bend,4),'intent':'REORIENT','parameters':{'target':{'type':target,'id':b.get('recipient_id')},'eyes_lead':True}})
        else:
            events.append({'start':round(orient_end,4),'end':round(bend,4),'intent':'SUSTAIN','parameters':{'target':{'type':target,'id':b.get('recipient_id')},'focus':round(.72+.16*ps['energy'],3)}})
        prev_end=bend
    return sorted(events,key=lambda e:(e['start'],e['end'],e['intent']))

DOCUMENTARY_HUMAN_TIMING_PRIOR={
    'evidence_source':'Rokoko NatureDocumentary_GoneWrong_hik.fbx via recovered local motion vault',
    'duration_s':53.133333,
    'fps':30.0,
    'quiet_hold_median_s':0.9333,
    'quiet_hold_max_s':1.9667,
    'active_burst_median_s':0.6833,
    'upper_body_energy_quantiles':{'q20':0.209798,'q40':0.424345,'q60':0.674510,'q80':1.084597,'q90':1.924707},
    'use':'timing_prior_only',
    'raw_mocap_replay':False,
    'character_joint_authority':False,
}

NARRATIVE_ROLE_POLICY={
    'SETUP':        {'gesture_bias':.72,'priority_bonus':0.00,'attention':'engage','energy':.42,'stillness':.42},
    'RECALL':       {'gesture_bias':.24,'priority_bonus':-.04,'attention':'release','energy':.32,'stillness':.76},
    'DEVELOPMENT':  {'gesture_bias':.88,'priority_bonus':0.00,'attention':'sustain','energy':.55,'stillness':.35},
    'CONTRAST':     {'gesture_bias':1.04,'priority_bonus':.07,'attention':'reengage','energy':.62,'stillness':.24},
    'ANTICIPATION': {'gesture_bias':0.00,'priority_bonus':-.30,'attention':'hold','energy':.36,'stillness':.92},
    'REVEAL':       {'gesture_bias':1.22,'priority_bonus':.18,'attention':'reengage','energy':.78,'stillness':.18},
    'REFLECTION':   {'gesture_bias':.28,'priority_bonus':-.05,'attention':'release','energy':.30,'stillness':.80},
    'RESOLUTION':   {'gesture_bias':.48,'priority_bonus':-.01,'attention':'settle','energy':.40,'stillness':.58},
}

def _turn_intent(t):
    return intent_family(t.get('semantic_intent') or infer_intent(t.get('text','')))

def _actor_map(actors):
    return {a.get('actor_id'):a for a in (actors or []) if a.get('actor_id')}

def _subtract_windows(base,cuts):
    """Return merged base windows minus merged cuts. Used so explicit overlap is not silenced."""
    base=_merge_windows(base);cuts=_merge_windows(cuts);out=[]
    for a,b in base:
        cur=a
        for c,d in cuts:
            if d<=cur or c>=b:continue
            if c>cur:out.append([cur,min(c,b)])
            cur=max(cur,d)
            if cur>=b:break
        if cur<b:out.append([cur,b])
    return _merge_windows(out)

def _explicit_floor_cue_events(cues,turns):
    events=[]
    active=lambda t: next((x for x in turns if float(x['start'])<=t<float(x['end'])),None)
    for i,c in enumerate(cues or []):
        typ=str(c.get('type','')).lower();actor=c.get('actor_id');t=float(c.get('time',0));dur=float(c.get('duration',.32));cur=active(t);target=c.get('target_speaker') or (cur or {}).get('actor_id')
        base={'actor_id':actor,'to_speaker':target,'explicit_cue':True,'cue_index':i}
        if typ in ('bid','floor_bid'):
            events.append({'start':t,'end':t+dur,'intent':'FLOOR_BID','parameters':dict(base,quiet=True)})
        elif typ in ('bid_withdrawn','withdraw'):
            events.append({'start':t,'end':t+dur*.55,'intent':'FLOOR_BID','parameters':dict(base,quiet=True)})
            events.append({'start':t+dur*.55,'end':t+dur,'intent':'BID_WITHDRAWN','parameters':dict(base,settle='living_rest')})
        elif typ in ('backchannel','acknowledge'):
            events.append({'start':t,'end':t+dur,'intent':'BACKCHANNEL','parameters':dict(base,quiet=True,reaction=c.get('reaction','acknowledge'))})
        elif typ in ('soft_interrupt','interrupt'):
            events.append({'start':max(0,t-.18),'end':t,'intent':'FLOOR_BID','parameters':dict(base,quiet=True)})
            events.append({'start':t,'end':t+max(.18,dur),'intent':'SOFT_INTERRUPT','parameters':dict(base,from_speaker=target,to_speaker=actor,takeover_time=t,speech_overlap_policy='yield')})
        elif typ in ('cooperative_overlap','overlap'):
            events.append({'start':t,'end':t+max(.18,dur),'intent':'COOPERATIVE_OVERLAP','parameters':dict(base,from_speaker=target,to_speaker=actor,speech_overlap_policy='allow')})
    return events

def floor_from_turns(turns,actors,seed='0',floor_cues=None):
    ts=sorted(turns,key=lambda x:(float(x['start']),float(x['end']),x.get('actor_id','')));events=[];ids=[a['actor_id'] for a in actors];amap=_actor_map(actors);last_backchannel={x:-999.0 for x in ids}
    for i,t in enumerate(ts):
        a=float(t['start']);e=float(t['end']);sp=t['actor_id'];rec=t.get('recipient_id');dur=e-a
        events.append({'start':a,'end':e,'intent':'SPEAKER_FLOOR','parameters':{'speaker':sp,'recipient':rec,'secondary_listeners':[x for x in ids if x not in (sp,rec)]}})
        # Sparse listener backchannels on sufficiently long turns. They are reactions, never floor acquisition.
        for lid in ids:
            if lid==sp:continue
            p=amap.get(lid,{'personality':'calm'});ps=personality_sem(p.get('personality','calm'));u=stable_unit(f'{seed}|{i}|{lid}|backchannel')
            if dur>=2.2 and u < .16+.24*ps['listener_activity']:
                bt=a+dur*(.62+.18*(stable_unit(f'{seed}|{i}|{lid}|backchannel_t')-.5));bd=min(.42,max(.16,ps['reaction_latency_s']+.12))
                # Backchannels are human only when sparse; never stack them at clause boundaries.
                if bt-last_backchannel.get(lid,-999.0)>=3.8:
                    events.append({'start':round(max(a,bt-bd*.4),4),'end':round(min(e,bt+bd*.6),4),'intent':'BACKCHANNEL','parameters':{'actor_id':lid,'to_speaker':sp,'reaction':'acknowledge' if u<.33 else 'interest','quiet':True,'takes_floor':False}})
                    last_backchannel[lid]=bt
        # Anticipatory pre-turn and automatic interpretation of real overlap in supplied dialogue timing.
        nxt=ts[i+1] if i+1<len(ts) else None
        if nxt and nxt.get('actor_id')!=sp:
            ns=nxt['actor_id'];na=float(nxt['start']);ne=float(nxt['end']);gap=na-e;overlap=e-na;np=amap.get(ns,{'personality':'calm'});nps=personality_sem(np.get('personality','calm'));prep=clamp(.24+.24*nps['listener_activity'],.18,.52)
            pre_a=max(a,na-prep);pre_b=min(na,e if overlap>0 else na)
            if pre_b>pre_a+.05:
                events.append({'start':round(pre_a,4),'end':round(pre_b,4),'intent':'PRE_TURN','parameters':{'actor_id':ns,'to_speaker':sp,'quiet':True,'mouth':'REST','posture_preparation':True,'eyes_lead':True}})
            if overlap>.04:
                cue=str(nxt.get('floor_cue') or '').lower();ni=_turn_intent(nxt)
                if cue in ('cooperative_overlap','overlap') or ni in ('agree','acknowledge','joke') and overlap<=.65:
                    kind='COOPERATIVE_OVERLAP';policy='allow'
                else:
                    kind='SOFT_INTERRUPT' if cue in ('soft_interrupt','interrupt') or overlap>.38 else 'BID_ACCEPTED';policy='yield' if kind=='SOFT_INTERRUPT' else 'allow'
                events.append({'start':round(na,4),'end':round(min(e,na+min(.55,max(.18,overlap))),4),'intent':kind,'parameters':{'actor_id':ns,'from_speaker':sp,'to_speaker':ns,'takeover_time':na,'speech_overlap_policy':policy,'inferred_from_timing':True}})
            elif gap<=1.25:
                events.append({'start':round(max(a,na-prep),4),'end':round(na,4),'intent':'TURN_READY','parameters':{'actor_id':ns,'from_speaker':sp,'quiet':True,'gap_s':round(gap,4)}})
        # Optional sparse aborted floor bid for engaged listeners in long answers. Deterministic and off by default.
        if dur>=7.5:
            for lid in ids:
                if lid==sp:continue
                la=amap.get(lid,{})
                if not la.get('allow_floor_bids'):continue
                ps=personality_sem(la.get('personality','calm'));u=stable_unit(f'{seed}|{i}|{lid}|autobid')
                if u<.14+.18*ps['listener_activity']:
                    bt=a+dur*(.56+.10*(stable_unit(f'{seed}|{i}|{lid}|autobid_t')-.5));bd=.34
                    events.append({'start':round(bt,4),'end':round(bt+bd*.5,4),'intent':'FLOOR_BID','parameters':{'actor_id':lid,'to_speaker':sp,'quiet':True,'takes_floor':False,'automatic':True}})
                    events.append({'start':round(bt+bd*.5,4),'end':round(bt+bd,4),'intent':'BID_WITHDRAWN','parameters':{'actor_id':lid,'to_speaker':sp,'settle':'living_rest','automatic':True}})
    events.extend(_explicit_floor_cue_events(floor_cues,ts))
    return sorted(events,key=lambda x:(x['start'],x['end'],x['intent']))

def reflective_response_events(turns,seed='0'):
    ts=sorted(turns,key=lambda x:(float(x['start']),float(x['end'])));ev=[]
    for i in range(1,len(ts)):
        prev,cur=ts[i-1],ts[i]
        if prev.get('actor_id')==cur.get('actor_id'):continue
        gap=float(cur['start'])-float(prev['end']);reflective=(_turn_intent(prev)=='question' and gap>=.24) or str(cur.get('response_mode') or '').lower() in ('reflective','think_first')
        if not reflective or gap<.18:continue
        a=float(prev['end']);b=float(cur['start']);aid=cur['actor_id'];span=b-a
        # Humanistic order: receive -> quiet thought -> resolve -> eyes reacquire. No hand gesture implied.
        r0=min(b,a+min(.16,span*.16));r1=a+span*.58;r2=a+span*.80
        if r0>a+.02:ev.append({'start':round(a,4),'end':round(r0,4),'intent':'RECEIVE_QUESTION','parameters':{'actor_id':aid,'from_speaker':prev['actor_id'],'gesture_policy':'none','mouth':'REST'}})
        if r1>r0+.03:ev.append({'start':round(r0,4),'end':round(r1,4),'intent':'THINK_BEFORE_ANSWER','parameters':{'actor_id':aid,'attention':'away','expression':'thinking','gesture_policy':'none','stillness':.88}})
        if r2>r1+.03:ev.append({'start':round(r1,4),'end':round(r2,4),'intent':'RESOLVE_THOUGHT','parameters':{'actor_id':aid,'attention':'soft_return','expression':'attentive','gesture_policy':'none'}})
        if b>r2+.02:ev.append({'start':round(r2,4),'end':round(b,4),'intent':'REORIENT_TO_SPEAKER','parameters':{'actor_id':aid,'target':prev['actor_id'],'eyes_lead':True,'posture_preparation':True,'mouth':'REST'}})
    return ev

def social_nuance_events(turns,seed='0'):
    ev=[]
    for i,t in enumerate(turns):
        intent=_turn_intent(t);a=float(t['start']);b=float(t['end']);dur=max(.01,b-a);aid=t['actor_id'];target=t.get('recipient_id')
        if intent in ('disagree','doubt'):
            p1=a+dur*.18;p2=a+dur*.38;p3=a+dur*.62
            ev += [
                {'start':round(a,4),'end':round(p1,4),'intent':'SOCIAL_ACKNOWLEDGE','parameters':{'actor_id':aid,'target':target,'head_led':True,'gesture_policy':'none','tone':'polite'}},
                {'start':round(p1,4),'end':round(p2,4),'intent':'SOCIAL_DOUBT','parameters':{'actor_id':aid,'target':target,'gaze':'hold_then_release','expression':'thinking','gesture_policy':'none'}},
                {'start':round(p2,4),'end':round(p3,4),'intent':'SOCIAL_DISAGREE','parameters':{'actor_id':aid,'target':target,'head_led':True,'chest_restrained':True,'arm_policy':'quiet'}},
                {'start':round(p3,4),'end':round(b,4),'intent':'SOCIAL_CLARIFY','parameters':{'actor_id':aid,'target':target,'gesture_policy':'optional_one_hand_open','amplitude_ceiling':.42,'soften_on_exit':True}},
            ]
        elif intent=='agree':
            ev.append({'start':round(a,4),'end':round(min(b,a+min(.7,dur*.42)),4),'intent':'SOCIAL_AGREE','parameters':{'actor_id':aid,'target':target,'head_led':True,'arm_policy':'none_unless_emphasis','quiet':True}})
        elif intent=='reassure':
            ev.append({'start':round(a,4),'end':round(b,4),'intent':'SOCIAL_REASSURE','parameters':{'actor_id':aid,'target':target,'gaze':'steady_soft','expression':'attentive_to_pleased','gesture_policy':'sparse_open','amplitude_ceiling':.38}})
    return ev

def _listening_spans(turns,listener_id,max_same_speaker_gap=.42):
    """Merge contiguous semantic beats from the same speaker so listener state persists across clauses."""
    xs=sorted([t for t in turns if t.get('actor_id')!=listener_id],key=lambda x:(float(x['start']),float(x['end'])))
    out=[]
    for t in xs:
        a=float(t['start']);b=float(t['end']);sp=t.get('actor_id')
        if out and out[-1]['speaker']==sp and a-out[-1]['end']<=max_same_speaker_gap:
            out[-1]['end']=max(out[-1]['end'],b);out[-1]['turns'].append(t)
        else:
            out.append({'speaker':sp,'start':a,'end':b,'turns':[t]})
    return out

def listener_life_events_for_actor(actor_id,turns,actor,seed='0'):
    ev=[];own=[[float(t['start']),float(t['end'])] for t in turns if t.get('actor_id')==actor_id];ps=personality_sem((actor or {}).get('personality','calm'));variant=0
    spans=_listening_spans(turns,actor_id)
    for i,span in enumerate(spans):
        windows=_subtract_windows([[span['start'],span['end']]],own)
        for a,b in windows:
            t={'actor_id':span['speaker']}
            dur=b-a
            if dur<.12:continue
            token=f'{actor_id}|{i}|{variant}';variant+=1;settle=min(.34,max(.14,dur*.08))
            ev.append({'start':round(a,4),'end':round(min(b,a+settle),4),'intent':'LISTENER_SETTLE','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'landing_variant':int(stable_unit(token+'|landing')*5),'gesture_policy':'none'}})
            sustain_a=min(b,a+settle);sustain_b=b
            # one context-driven gaze release on longer listening windows, not periodic life noise
            if dur>=4.0 and stable_unit(token+'|release')<.66:
                rt=a+dur*(.42+.18*(stable_unit(token+'|release_t')-.5));rd=min(.42,max(.22,dur*.05));
                if rt>sustain_a+.15:
                    ev.append({'start':round(sustain_a,4),'end':round(rt,4),'intent':'LISTENER_SUSTAIN','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'attention':'speaker','stillness':.78}})
                    ev.append({'start':round(rt,4),'end':round(min(b,rt+rd),4),'intent':'LISTENER_GAZE_RELEASE','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'attention':'away','gesture_policy':'none'}})
                    re=min(b,rt+rd+.28)
                    if re>rt+rd+.04:ev.append({'start':round(rt+rd,4),'end':round(re,4),'intent':'LISTENER_REENGAGE','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'eyes_lead':True}})
                    sustain_a=re
            if dur>=6.0 and stable_unit(token+'|consider')<.72:
                ct=a+dur*(.68+.12*(stable_unit(token+'|consider_t')-.5));ce=min(b,ct+min(.58,max(.28,ps['reaction_latency_s']+.22)))
                if ct>sustain_a+.12:
                    ev.append({'start':round(sustain_a,4),'end':round(ct,4),'intent':'LISTENER_SUSTAIN','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'attention':'speaker','stillness':.82}})
                if ce>ct+.04:ev.append({'start':round(ct,4),'end':round(ce,4),'intent':'LISTENER_CONSIDER','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'expression':'thinking','head':'small_angle','gesture_policy':'none'}})
                sustain_a=ce
            # Contextual reaction is driven by what the speaker just said, not periodic listener noise.
            # Surprise/reveal-like speaker beats can earn one restrained reaction before the listener's next turn.
            for sturn in span.get('turns',[]):
                si=canonical(sturn.get('semantic_intent',''))
                sa=max(a,float(sturn.get('start',a))); sb=min(b,float(sturn.get('end',b)))
                if sb-sa<.35: continue
                if si in ('surprise','reveal'):
                    rs=sa+(sb-sa)*(.62+.08*(stable_unit(token+'|surprise_reaction')-.5)); re=min(sb,b,rs+.55)
                    if re>rs+.12:
                        ev.append({'start':round(rs,4),'end':round(re,4),'intent':'LISTENER_REACTION','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'reaction':'surprised','quiet':True,'takes_floor':False,'source_semantic':si}})
                elif si in ('emphasize','important_point') and stable_unit(token+'|emphasis_ack')<.72:
                    rs=sa+(sb-sa)*.72; re=min(sb,b,rs+.34)
                    if re>rs+.10:
                        ev.append({'start':round(rs,4),'end':round(re,4),'intent':'LISTENER_REACTION','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'reaction':'acknowledge','quiet':True,'takes_floor':False,'source_semantic':si}})
            if b>sustain_a+.04:ev.append({'start':round(sustain_a,4),'end':round(b,4),'intent':'LISTENER_SUSTAIN','parameters':{'actor_id':actor_id,'speaker':t['actor_id'],'state_token':token,'attention':'speaker','stillness':.84,'rest_destination':'continue_living_state_not_reset'}})
    return sorted(ev,key=lambda x:(x['start'],x['end'],x['intent']))

def _narrative_candidate(actor,beats):
    mode=str(actor.get('performance_mode') or actor.get('performance_style') or '').lower()
    if any(x in mode for x in ('story','narrative','documentary','memory')):return True
    text=' '.join((b.get('text') or '') for b in beats).lower();markers=sum(text.count(x) for x in ('remember','back then','once ','then ','suddenly','but ','however','finally','eventually','until ','turned out','the moment'))
    return len(beats)>=4 and markers>=2

def apply_narrative_roles(beats,actor,seed='0'):
    for b in beats:
        b['narrative_role']=None;b['narrative_gesture_bias']=1.0;b['narrative_priority_bonus']=0.0;b['narrative_timing_prior']=None
    if not _narrative_candidate(actor,beats):return False
    n=len(beats);reveal=None
    # Prefer a semantically meaningful late reveal rather than imposing one on every script.
    for i,b in enumerate(beats):
        if i>=max(1,int(n*.35)) and b['semantic_intent'] in ('surprise','emphasize'):
            reveal=i;break
        tx=(b.get('text') or '').lower()
        if i>=max(1,int(n*.45)) and any(m in tx for m in ('suddenly','turned out','the truth','finally','that was when')):
            reveal=i;break
    for i,b in enumerate(beats):
        intent=b['semantic_intent'];role='DEVELOPMENT'
        if i==0:role='SETUP'
        if intent in ('remember','think'):role='RECALL'
        elif intent=='contrast':role='CONTRAST'
        if reveal is not None and i==reveal:role='REVEAL'
        elif reveal is not None and i==reveal-1 and role=='DEVELOPMENT':role='ANTICIPATION'
        elif reveal is not None and i>reveal and i<n-1:role='REFLECTION'
        if i==n-1 and role not in ('REVEAL','RECALL'):role='RESOLUTION'
        pol=NARRATIVE_ROLE_POLICY[role];b['narrative_role']=role;b['narrative_gesture_bias']=pol['gesture_bias'];b['narrative_priority_bonus']=pol['priority_bonus'];b['narrative_timing_prior']='captured_documentary_human_timing_v1';b['narrative_state']={'attention':pol['attention'],'energy':pol['energy'],'stillness':pol['stillness'],'raw_mocap_replay':False}
        if role=='ANTICIPATION':b['emphasis_anchors']=[]
    return True

def narrative_events(beats,actor,seed='0'):
    if not any(b.get('narrative_role') for b in beats):return []
    ev=[]
    for b in beats:
        role=b.get('narrative_role')
        if not role:continue
        pol=NARRATIVE_ROLE_POLICY[role]
        ev.append({'start':b['start'],'end':b['end'],'intent':'NARRATIVE_'+role,'parameters':{'role':role,'attention':pol['attention'],'energy':pol['energy'],'stillness':pol['stillness'],'timing_prior':'captured_documentary_human_timing_v1','source_evidence':DOCUMENTARY_HUMAN_TIMING_PRIOR['evidence_source'],'raw_mocap_replay':False}})
        if role=='REVEAL':
            dur=b['end']-b['start'];hold=min(DOCUMENTARY_HUMAN_TIMING_PRIOR['quiet_hold_median_s'],max(.18,dur*.18));a=max(b['start'],b['start']+dur*.16-hold*.5)
            if a+hold<b['end']:ev.append({'start':round(a,4),'end':round(a+hold,4),'intent':'PRE_REVEAL_STILLNESS','parameters':{'gesture_policy':'none','attention':'hold','reason':'narrative_contrast_before_reveal','raw_mocap_replay':False}})
    return sorted(ev,key=lambda x:(x['start'],x['end'],x['intent']))

def _merge_windows(windows):
    xs=sorted((float(a),float(b)) for a,b in windows if float(b)>float(a))
    out=[]
    for a,b in xs:
        if not out or a>out[-1][1]+1e-6:out.append([a,b])
        else:out[-1][1]=max(out[-1][1],b)
    return out




INTERACTION_CONTRACT_DATA = json.loads('{"interaction":{"actions":["open","close","pour","carry","give","receive","sit","type","write","drink","push","pull","insert","remove","place","pickup","press","point","read"],"state_machine":["approach","precontact","contact_validate","shared_load","owned_or_actuated","release","settle"],"rules":["contact_before_ownership_change","release_after_destination_support","no_prop_teleport","reach_feasibility_before_contact","restage_or_fail_if_unreachable","held_object_spatial_continuity","world_plan_required_for_world_contact"]}}')


def minimum_jerk_blend(u):
    u=clamp(float(u),0.0,1.0)
    return 10*u**3 - 15*u**4 + 6*u**5

def minimum_jerk_bridge(start,end,u):
    if len(start)!=len(end): return {'status':'FAIL_CLOSED','failure':{'code':'BRIDGE_DIMENSION_MISMATCH'}}
    w=minimum_jerk_blend(u)
    return {'status':'PASS','value':[float(a)+(float(b)-float(a))*w for a,b in zip(start,end)],'weight':w}

def project_segment_length(parent, child, required_length):
    if len(parent)!=3 or len(child)!=3 or float(required_length)<=0:return {'status':'FAIL_CLOSED','failure':{'code':'INVALID_SEGMENT_INPUT'}}
    d=[float(child[i])-float(parent[i]) for i in range(3)]; n=sum(x*x for x in d)**0.5
    if n<1e-10:return {'status':'FAIL_CLOSED','failure':{'code':'DEGENERATE_SEGMENT'}}
    L=float(required_length); out=[float(parent[i])+d[i]*L/n for i in range(3)]
    return {'status':'PASS','child':out,'length':L,'anatomy_mutation':False}

def interaction_ownership_plan(action, *, contact_confirmed=False, destination_supported=False, world_plan=None):
    supported=set(INTERACTION_CONTRACT_DATA['interaction']['actions'])
    if action not in supported:return {'status':'FAIL_CLOSED','failure':{'code':'UNSUPPORTED_INTERACTION','action':action}}
    if action in {'pickup','place','give','receive','insert','remove','press','push','pull','open','close','pour','drink'} and not world_plan:
        return {'status':'FAIL_CLOSED','failure':{'code':'WORLD_PLAN_REQUIRED'}}
    if action in {'pickup','give','receive','insert','remove','press','push','pull','open','close','pour','drink'} and not contact_confirmed:
        return {'status':'FAIL_CLOSED','failure':{'code':'CONTACT_NOT_CONFIRMED'}}
    if action in {'place','give','insert'} and not destination_supported:
        return {'status':'FAIL_CLOSED','failure':{'code':'DESTINATION_SUPPORT_NOT_CONFIRMED'}}
    states=['approach','precontact','contact_validate']
    if contact_confirmed:states+=['shared_load','owned_or_actuated']
    if destination_supported:states+=['release']
    states+=['settle']
    return {'status':'PASS','states':states,'ownership_change_after_contact':True,'teleport':False}
