from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

BEAT_MAP={
    'HOOK':('DECISIVE_SLIDE','KEYWORD_HIT'),
    'SETUP':('MASK_REVEAL','FADE_SCALE_SETTLE'),
    'CONTRAST':('PHRASE_REPLACE','DECISIVE_SLIDE'),
    'EXPLANATION':('LINE_STAGGER','FADE_SCALE_SETTLE'),
    'PROOF':('MASK_REVEAL','KEYWORD_HIT'),
    'LIST':('LINE_STAGGER','MASK_REVEAL'),
    'REFRAME':('PHRASE_REPLACE','MASK_REVEAL'),
    'EMPHASIS':('KEYWORD_HIT','MASK_REVEAL'),
    'PAYOFF':('KEYWORD_HIT','HOLD_AND_WIPE'),
    'CTA':('DECISIVE_SLIDE','HOLD_AND_WIPE'),
}

@dataclass
class PhraseUnit:
    text:str
    role:str='hero'             # hero | support
    emphasis:float=0.0          # 0..1
    replace_group:Optional[str]=None
    line_index:int=0

@dataclass
class MotionEvent:
    unit_index:int
    role:str
    event:str
    start_ms:int
    end_ms:int
    strength:float
    note:str=''

@dataclass
class Choreography:
    beat_type:str
    duration_ms:int
    primary_family:str
    secondary_family:str
    events:List[MotionEvent]
    warnings:List[str]
    pass_gate:bool

def clamp(v,a,b): return max(a,min(b,v))

def choose_family(beat_type:str, energy:float=0.5):
    beat=beat_type.upper()
    p,s=BEAT_MAP.get(beat,('MASK_REVEAL','FADE_SCALE_SETTLE'))
    if energy<0.28 and p in {'DECISIVE_SLIDE','KEYWORD_HIT'}:
        p='MASK_REVEAL'
    return p,s

def _timing(duration_ms:int, hero_count:int, support_count:int, complexity:float):
    # Generic timing allocation. No subject/topic routing.
    lead=int(clamp(80+complexity*70,60,180))
    exit_ms=int(clamp(230+complexity*110,180,480))
    usable=max(420,duration_ms-lead-exit_ms-120)
    hero_reveal=int(clamp(290+complexity*180,220,620))
    support_reveal=int(clamp(230+complexity*130,180,520))
    hero_hold=int(clamp(usable*.36,520,1400))
    support_hold=int(clamp(usable*.24,360,1100))
    return lead,exit_ms,hero_reveal,support_reveal,hero_hold,support_hold

def compile_beat(beat_type:str, duration_ms:int, units:List[Dict[str,Any]], energy:float=0.5, complexity:float=0.4)->Dict[str,Any]:
    duration_ms=max(650,int(duration_ms))
    parsed=[PhraseUnit(**u) for u in units]
    hero_ix=[i for i,u in enumerate(parsed) if u.role=='hero']
    support_ix=[i for i,u in enumerate(parsed) if u.role=='support']
    primary,secondary=choose_family(beat_type,energy)
    lead,exit_ms,hero_rev,supp_rev,hero_hold,supp_hold=_timing(duration_ms,len(hero_ix),len(support_ix),complexity)
    events=[]; warnings=[]

    cursor=lead
    # Hero choreography first.
    if hero_ix:
        for n,i in enumerate(hero_ix):
            u=parsed[i]
            fam=primary if n==0 else secondary
            rev=hero_rev if fam!='KEYWORD_HIT' else int(hero_rev*.82)
            start=cursor
            end=min(duration_ms-exit_ms-120,start+rev)
            events.append(MotionEvent(i,'hero',fam,start,end,0.88+0.12*u.emphasis,'hero_reveal'))
            cursor=end
            # high-emphasis phrase gets a dedicated hit after settle
            if u.emphasis>=0.72 and fam!='KEYWORD_HIT':
                hs=cursor+60; he=min(duration_ms-exit_ms-120,hs+170)
                if he>hs:
                    events.append(MotionEvent(i,'hero','KEYWORD_HIT',hs,he,clamp(.82+.18*u.emphasis,0,1),'semantic_emphasis'))
                    cursor=he
        hero_settle=cursor
    else:
        hero_settle=lead

    # Support waits for hero readability except list/proof style where sequence is intentional.
    support_cursor=hero_settle + (100 if beat_type.upper() in {'LIST','EXPLANATION','PROOF'} else 140)
    for n,i in enumerate(support_ix):
        u=parsed[i]
        fam='LINE_STAGGER' if beat_type.upper() in {'LIST','EXPLANATION'} else 'FADE_SCALE_SETTLE'
        start=support_cursor
        end=min(duration_ms-exit_ms-120,start+supp_rev)
        if end<=start:
            warnings.append('SUPPORT_TIMING_COMPRESSED')
            break
        events.append(MotionEvent(i,'support',fam,start,end,0.45+0.18*u.emphasis,'support_reveal'))
        support_cursor=end+80

    # Replace groups are allowed for hero only; replacement occurs after initial readable hold.
    groups={}
    for i,u in enumerate(parsed):
        if u.replace_group:
            groups.setdefault(u.replace_group,[]).append(i)
    for g,ixs in groups.items():
        hero_group=[i for i in ixs if parsed[i].role=='hero']
        if len(hero_group)>=2:
            first,second=hero_group[0],hero_group[1]
            prior=[e for e in events if e.unit_index==first and e.role=='hero']
            if prior:
                rs=max(e.end_ms for e in prior)+max(360,int(hero_hold*.52))
                re=min(duration_ms-exit_ms-120,rs+330)
                if re>rs:
                    events.append(MotionEvent(second,'hero','PHRASE_REPLACE',rs,re,0.94,'replace_group:'+g))

    # Hold window and exit. Ensures final state settles before spoken phrase end where possible.
    latest=max([e.end_ms for e in events],default=lead)
    hold_start=latest
    hold_end=min(duration_ms-exit_ms, max(hold_start+520, duration_ms-exit_ms-80))
    if hold_end>hold_start:
        events.append(MotionEvent(-1,'global','HOLD',hold_start,hold_end,0.0,'readable_settled_state'))
    exs=max(hold_end,duration_ms-exit_ms)
    events.append(MotionEvent(-1,'global','EXIT',exs,duration_ms,0.72,'beat_handoff'))

    # QA
    events.sort(key=lambda e:(e.start_ms,e.end_ms,e.unit_index))
    # Hero/support overlap gate: support cannot start before first hero settles except comparison/list semantics.
    if hero_ix and support_ix and beat_type.upper() not in {'LIST','EXPLANATION'}:
        hero_events=[e for e in events if e.role=='hero' and e.event not in {'PHRASE_REPLACE'}]
        support_events=[e for e in events if e.role=='support']
        if hero_events and support_events:
            hero_end=max(e.end_ms for e in hero_events)
            supp_start=min(e.start_ms for e in support_events)
            if supp_start < hero_end:
                warnings.append('SUPPORT_COMPETES_WITH_HERO')
        elif hero_ix and not hero_events:
            warnings.append('HERO_TIMING_COMPRESSED')
    # Dominant-motion gate: no two HIGH-strength reveal events begin within 90ms.
    highs=[e for e in events if e.strength>=.82 and e.event not in {'HOLD','EXIT'}]
    for a,b in zip(highs,highs[1:]):
        if abs(a.start_ms-b.start_ms)<90 and a.unit_index!=b.unit_index:
            warnings.append('COMPETING_HIGH_STRENGTH_TEXT_MOTION')
    if duration_ms-latest<120:
        warnings.append('NO_AUDIO_END_GUARD')
    pass_gate=not any(w in warnings for w in ['SUPPORT_COMPETES_WITH_HERO','COMPETING_HIGH_STRENGTH_TEXT_MOTION','NO_AUDIO_END_GUARD'])
    return asdict(Choreography(beat_type.upper(),duration_ms,primary,secondary,events,warnings,pass_gate))
