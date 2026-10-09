from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import List,Dict,Any,Optional
import json,math

CHANNELS={'BACKGROUND','HERO_TEXT','SUPPORT_TEXT','ILLUSTRATION','CHARACTER','TRANSITION'}

@dataclass
class EnsembleRequest:
    duration_ms:int
    shot_role:str
    hero_motion_count:int=1
    support_motion_count:int=1
    illustration_motion_count:int=1
    character_present:bool=False
    background_stage_motion:bool=True
    transition_mode:str='OBJECT_OR_TEXT_CARRIER'
    beat_energy:float=.55
    audio_accent_times:Optional[List[int]]=None
    preferred_primary:str='AUTO'

@dataclass
class EnsembleEvent:
    channel:str
    event:str
    start_ms:int
    end_ms:int
    strength:float
    dominant:bool
    note:str=''

@dataclass
class EnsemblePlan:
    duration_ms:int
    shot_role:str
    events:List[EnsembleEvent]
    dominant_sequence:List[str]
    hold_window:Dict[str,int]
    transition_window:Dict[str,int]
    warnings:List[str]
    pass_gate:bool

def clamp(v,a,b):return max(a,min(b,v))

def overlaps(a:EnsembleEvent,b:EnsembleEvent):return max(0,min(a.end_ms,b.end_ms)-max(a.start_ms,b.start_ms))

class EditorialMotionEnsembleDirectorV1:
    def plan(self,req:EnsembleRequest)->EnsemblePlan:
        D=max(1600,int(req.duration_ms));warnings=[];events=[]
        # Beat windows: intro 0-15%, build to 62%, hold to 86%, transition last 14%.
        intro_end=int(D*.16); build_end=int(D*.63); hold_start=int(D*.68); trans_start=int(D*.86)
        gap=max(55,int(D*.025))

        def add(ch,ev,s,e,strength,dom,note=''):
            s=max(0,int(s));e=min(D,max(s+1,int(e)));events.append(EnsembleEvent(ch,ev,s,e,round(strength,3),dom,note))

        # Background stage settles before hero action, and is deliberately low-strength.
        if req.background_stage_motion:
            add('BACKGROUND','STAGE_SETTLE',0,min(intro_end,int(D*.11)),.26,False,'depth establishes without becoming focal')

        role=req.shot_role.upper()
        cursor=max(40,int(D*.06))
        # Primary attention sequence is role-aware, but generic.
        if role=='ILLUSTRATION_LED':
            order=['ILLUSTRATION','HERO_TEXT','SUPPORT_TEXT']
        elif role=='CHARACTER_EMPHASIS':
            order=['HERO_TEXT','CHARACTER','ILLUSTRATION','SUPPORT_TEXT']
        elif role=='PAYOFF':
            order=['HERO_TEXT','ILLUSTRATION']+(['CHARACTER'] if req.character_present else [])
        else:
            order=['HERO_TEXT','ILLUSTRATION','SUPPORT_TEXT']+(['CHARACTER'] if req.character_present else [])

        # Explicit user/semantic override only by channel, not topic.
        if req.preferred_primary in CHANNELS and req.preferred_primary in order:
            order=[req.preferred_primary]+[x for x in order if x!=req.preferred_primary]

        durations={
          'HERO_TEXT':clamp(int(D*.15),260,620),
          'ILLUSTRATION':clamp(int(D*.17),300,720),
          'CHARACTER':clamp(int(D*.15),280,650),
          'SUPPORT_TEXT':clamp(int(D*.12),220,500)
        }
        strengths={'HERO_TEXT':.94,'ILLUSTRATION':.88,'CHARACTER':.92,'SUPPORT_TEXT':.46}
        names={'HERO_TEXT':'HERO_PERFORMANCE','ILLUSTRATION':'ILLUSTRATION_ACTION','CHARACTER':'CHARACTER_EMPHASIS','SUPPORT_TEXT':'SUPPORT_REVEAL'}

        dominant_sequence=[]
        for ch in order:
            if ch=='CHARACTER' and not req.character_present:continue
            if ch=='SUPPORT_TEXT' and req.support_motion_count<=0:continue
            if ch=='ILLUSTRATION' and req.illustration_motion_count<=0:continue
            if ch=='HERO_TEXT' and req.hero_motion_count<=0:continue
            dur=durations[ch]
            if cursor+dur>build_end:
                dur=max(160,build_end-cursor)
            if dur<=140:break
            dom=ch!='SUPPORT_TEXT'
            add(ch,names[ch],cursor,cursor+dur,strengths[ch],dom,'attention baton')
            if dom:dominant_sequence.append(ch)
            cursor+=dur+gap

        # Extra support/object motions are subordinate and serialize after corresponding hero motion.
        if req.illustration_motion_count>1 and cursor<hold_start-180:
            for i in range(req.illustration_motion_count-1):
                dur=min(260,max(140,int(D*.075)))
                if cursor+dur>=hold_start:break
                add('ILLUSTRATION',f'SECONDARY_OBJECT_MOTION_{i+1}',cursor,cursor+dur,.38,False,'supporting scene-native motion')
                cursor+=dur+gap
        if req.support_motion_count>1 and cursor<hold_start-160:
            for i in range(req.support_motion_count-1):
                dur=min(230,max(120,int(D*.065)))
                if cursor+dur>=hold_start:break
                add('SUPPORT_TEXT',f'SUPPORT_LINE_{i+2}',cursor,cursor+dur,.34,False,'subordinate support')
                cursor+=dur+gap

        # Audio accents can nudge, never create a second simultaneous dominant action.
        accents=sorted([a for a in (req.audio_accent_times or []) if 0<a<trans_start])
        for a in accents[:3]:
            # only add a low-strength micro-emphasis if no dominant event already covers accent
            if not any(e.dominant and e.start_ms<=a<=e.end_ms for e in events):
                add('HERO_TEXT','AUDIO_ACCENT_SETTLE',a,min(a+120,trans_start),.32,False,'audio-aligned micro emphasis')

        # Settled hold: no high-strength motion.
        actual_hold_start=max(cursor,hold_start)
        if actual_hold_start>=trans_start-100:
            actual_hold_start=max(0,trans_start-max(260,int(D*.10)))
        add('BACKGROUND','SETTLED_HOLD',actual_hold_start,trans_start,.0,False,'read/absorb state')

        # One transition carrier owns the ending.
        carrier='HERO_TEXT' if req.transition_mode.startswith('TEXT') else ('ILLUSTRATION' if req.transition_mode.startswith('OBJECT') else 'TRANSITION')
        add(carrier,'TRANSITION_CARRIER',trans_start,D,.84,True,req.transition_mode)
        dominant_sequence.append(carrier)

        # QA: high-strength dominant events may not overlap.
        doms=[e for e in events if e.dominant and e.strength>=.80]
        for i,a in enumerate(doms):
            for b in doms[i+1:]:
                ov=overlaps(a,b)
                if ov>20:warnings.append(f'DOMINANT_MOTION_COLLISION:{a.channel}:{b.channel}:{ov}ms')
        # Support should not exceed dominant strength.
        if any(e.strength>=.70 and not e.dominant for e in events):warnings.append('SUPPORT_MOTION_TOO_STRONG')
        # Hold needs minimum read time.
        hold_len=trans_start-actual_hold_start
        if hold_len<220:warnings.append('SETTLED_HOLD_TOO_SHORT')
        # Character cannot exist as idle decorative channel; when present it must receive emphasis event.
        if req.character_present and not any(e.channel=='CHARACTER' for e in events):warnings.append('CHARACTER_PRESENT_WITHOUT_PERFORMANCE')
        events.sort(key=lambda e:(e.start_ms,e.end_ms))
        pass_gate=not warnings
        return EnsemblePlan(D,role,events,dominant_sequence,{'start_ms':actual_hold_start,'end_ms':trans_start},{'start_ms':trans_start,'end_ms':D},warnings,pass_gate)

if __name__=='__main__':
    req=EnsembleRequest(duration_ms=3800,shot_role='HYBRID',character_present=False,illustration_motion_count=2)
    print(json.dumps(asdict(EditorialMotionEnsembleDirectorV1().plan(req)),indent=2))
