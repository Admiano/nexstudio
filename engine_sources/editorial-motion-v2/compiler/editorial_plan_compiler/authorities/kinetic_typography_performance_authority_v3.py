from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
import math, json, random
from pathlib import Path
import sys

from .kinetic_typography_grammar_v2 import compile_beat as compile_v2
from .text_element_spatial_authority_v1 import SpatialAuthorityV1, SpatialRequest, ASPECTS

MOTIFS=[
    'PROMOTED_WORD_STACK',
    'SPLIT_SCALE_LOCKUP',
    'SIDE_NOTE_HERO',
    'BLACK_LABEL_PUNCH',
    'OFF_AXIS_SUPPORT',
    'FULL_FRAME_HIT',
    'COLUMN_BUILD',
    'REPLACEMENT_LOCKUP',
    'EDGE_CROP_HERO',
    'WORD_OBJECT_BRIDGE',
]

BEAT_MOTIFS={
    'HOOK':['FULL_FRAME_HIT','PROMOTED_WORD_STACK','EDGE_CROP_HERO'],
    'SETUP':['SIDE_NOTE_HERO','COLUMN_BUILD','SPLIT_SCALE_LOCKUP'],
    'CONTRAST':['REPLACEMENT_LOCKUP','SPLIT_SCALE_LOCKUP','BLACK_LABEL_PUNCH'],
    'EXPLANATION':['COLUMN_BUILD','SIDE_NOTE_HERO','OFF_AXIS_SUPPORT'],
    'PROOF':['BLACK_LABEL_PUNCH','SPLIT_SCALE_LOCKUP','COLUMN_BUILD'],
    'LIST':['COLUMN_BUILD','OFF_AXIS_SUPPORT','SIDE_NOTE_HERO'],
    'REFRAME':['REPLACEMENT_LOCKUP','PROMOTED_WORD_STACK','WORD_OBJECT_BRIDGE'],
    'EMPHASIS':['FULL_FRAME_HIT','BLACK_LABEL_PUNCH','PROMOTED_WORD_STACK'],
    'PAYOFF':['PROMOTED_WORD_STACK','FULL_FRAME_HIT','SPLIT_SCALE_LOCKUP'],
    'CTA':['BLACK_LABEL_PUNCH','FULL_FRAME_HIT','SIDE_NOTE_HERO'],
}

ASPECT_RULES={
    '9x16':{'hero_scale':1.00,'promotion_ratio':2.15,'max_primary_lines':4,'support_tilt_deg':-5.0,'edge_crop_max':0.10},
    '1x1': {'hero_scale':1.08,'promotion_ratio':2.30,'max_primary_lines':3,'support_tilt_deg':-4.0,'edge_crop_max':0.08},
    '16x9':{'hero_scale':1.00,'promotion_ratio':2.00,'max_primary_lines':3,'support_tilt_deg':-3.0,'edge_crop_max':0.07},
}

@dataclass
class TextUnit:
    text:str
    role:str='hero'                 # hero | support | label
    emphasis:float=0.5
    semantic_role:str='statement'   # setup | contrast | proof | punch | qualifier | action | evidence
    replace_group:Optional[str]=None
    can_promote:bool=True
    italic:bool=False

@dataclass
class TextBlock:
    unit_index:int
    text:str
    role:str
    style:str
    bbox:Dict[str,float]
    font_scale:float
    weight:str
    italic:bool
    alignment:str
    z:int
    emphasis:float

@dataclass
class PerformancePlan:
    beat_type:str
    aspect:str
    motif:str
    spatial_preset:str
    text_blocks:List[TextBlock]
    choreography:Dict[str,Any]
    transition_carrier:Optional[Dict[str,Any]]
    reading_order:List[int]
    focal_order:List[int]
    warnings:List[str]
    metrics:Dict[str,Any]
    pass_gate:bool

def clamp(v,a=0,b=1): return max(a,min(b,v))

def norm_bbox(rect:Dict[str,float], W:int,H:int)->Dict[str,float]:
    return {'x':rect['x']/W,'y':rect['y']/H,'w':rect['w']/W,'h':rect['h']/H}

def abs_bbox(nb:Dict[str,float],W:int,H:int)->Dict[str,float]:
    return {'x':round(nb['x']*W,1),'y':round(nb['y']*H,1),'w':round(nb['w']*W,1),'h':round(nb['h']*H,1)}

def token_count(s:str)->int:
    return len([x for x in s.replace('\n',' ').split(' ') if x.strip()])

def _promote_index(units:List[TextUnit])->Optional[int]:
    candidates=[]
    for i,u in enumerate(units):
        if u.role!='hero' or not u.can_promote: continue
        words=token_count(u.text)
        # Promotion is strongest for short semantic punch units; never topic-specific.
        compact=max(0,1-(max(1,words)-1)/7)
        score=.62*u.emphasis+.25*compact+.13*(1 if u.semantic_role in {'punch','contrast','action'} else 0)
        candidates.append((score,i))
    return max(candidates)[1] if candidates else None

def _semantic_lines(text:str,max_lines:int)->List[str]:
    # This consumes an already-resolved phrase. Breaks at punctuation/semantic boundaries first,
    # then balances words. It never changes the actual wording.
    raw=text.strip()
    if '\n' in raw:
        return [x.strip() for x in raw.split('\n') if x.strip()][:max_lines]
    parts=[]
    buf=''
    for tok in raw.split():
        add=(' '+tok if buf else tok)
        buf+=add
        if tok.endswith((',', ';', ':', '—')):
            parts.append(buf.strip()); buf=''
    if buf: parts.append(buf.strip())
    if len(parts)>1 and len(parts)<=max_lines:
        return parts
    words=raw.split()
    if len(words)<=4 or max_lines<=1: return [raw]
    line_count=min(max_lines, max(1, round(len(words)/4.5)))
    if line_count<=1:return [raw]
    target=len(words)/line_count
    lines=[]; start=0
    for li in range(line_count):
        remain=len(words)-start; left=line_count-li
        take=max(1, round(remain/left))
        lines.append(' '.join(words[start:start+take])); start+=take
    return lines

def choose_motif(beat_type:str,units:List[TextUnit],aspect:str,object_present:bool=False,prev_motif:Optional[str]=None)->str:
    beat=beat_type.upper(); choices=list(BEAT_MOTIFS.get(beat,['PROMOTED_WORD_STACK']))
    promoted=_promote_index(units)
    replace=any(u.replace_group for u in units)
    support=sum(u.role=='support' for u in units)
    if object_present and beat in {'REFRAME','EXPLANATION','PROOF'} and not replace:
        choices.insert(0,'WORD_OBJECT_BRIDGE')
    if replace and 'REPLACEMENT_LOCKUP' in choices:
        choices.insert(0,'REPLACEMENT_LOCKUP')
    if not replace:
        choices=[c for c in choices if c!='REPLACEMENT_LOCKUP'] or ['SPLIT_SCALE_LOCKUP']
    if promoted is None: choices=[m for m in choices if m not in {'PROMOTED_WORD_STACK','EDGE_CROP_HERO'}] or choices
    if support>=2 and 'COLUMN_BUILD' in choices: choices.insert(0,'COLUMN_BUILD')
    # Sequence diversity gate: do not repeat the same motif back-to-back if another is viable.
    if prev_motif and len(choices)>1:
        choices=[m for m in choices if m!=prev_motif]+([prev_motif] if prev_motif in choices else [])
    return choices[0]

def _zones(aspect:str,shot_role:str='TEXT_LED',object_present:bool=True,text_load=.55):
    spatial=SpatialAuthorityV1().plan(SpatialRequest(
        aspect=aspect, shot_role=shot_role,
        text_load=text_load, illustration_load=.55 if object_present else .20,
        character_present=False, text_dominance=.78 if shot_role=='TEXT_LED' else .58,
        illustration_dominance=.42 if shot_role=='TEXT_LED' else .62
    ))
    return spatial

def _layout_blocks(motif:str,aspect:str,units:List[TextUnit],text_zone:Dict[str,float],illustration_zone:Dict[str,float],promote:Optional[int])->Tuple[List[TextBlock],List[str]]:
    W,H=ASPECTS[aspect]; ar=ASPECT_RULES[aspect]; warnings=[]
    tz=norm_bbox(text_zone,W,H); iz=norm_bbox(illustration_zone,W,H)
    blocks=[]
    hero=[(i,u) for i,u in enumerate(units) if u.role=='hero']
    support=[(i,u) for i,u in enumerate(units) if u.role=='support']
    labels=[(i,u) for i,u in enumerate(units) if u.role=='label']

    def add(i,u,x,y,w,h,scale,weight='Black',italic=None,align='left',style='hero',z=20):
        blocks.append(TextBlock(i,u.text,u.role,style,abs_bbox({'x':x,'y':y,'w':w,'h':h},W,H),round(scale,3),weight,u.italic if italic is None else italic,align,z,u.emphasis))

    tx,ty,tw,th=tz['x'],tz['y'],tz['w'],tz['h']
    # Ensure blocks remain spatially owned by text zone except intentional edge-crop hero,
    # which may crop only against the safe frame edge, never into illustration territory.
    if motif=='PROMOTED_WORD_STACK':
        if hero:
            promote=promote if promote is not None else hero[-1][0]
            regular=[(i,u) for i,u in hero if i!=promote]
            py=ty
            if regular:
                for n,(i,u) in enumerate(regular):
                    h=min(th*.19, .095); add(i,u,tx,py,tw,h,.72*ar['hero_scale'],'SemiBold',False,'left','setup',20); py+=h+.012
            pu=units[promote]; ph=min(max(.115,th*.34),.22)
            add(promote,pu,tx,py,tw,ph,1.0*ar['promotion_ratio']*ar['hero_scale'],'Black',False,'left','promoted_word',30)
            sy=py+ph+.018
            for i,u in support[:2]:
                add(i,u,tx+.02,sy,tw*.86,min(.07,th*.16),.54,'SemiBold',True,'left','support_italic',15); sy+=.075
    elif motif=='SPLIT_SCALE_LOCKUP':
        if hero:
            i0,u0=hero[0]; add(i0,u0,tx,ty+th*.02,tw*.58,th*.23,.78,'SemiBold',False,'left','setup',20)
            if len(hero)>1:
                i1,u1=hero[1]; add(i1,u1,tx+tw*.38,ty+th*.31,tw*.62,th*.37,1.65,'Black',False,'right','large_counterweight',30)
            elif promote is not None:
                pu=units[promote]; add(promote,pu,tx+tw*.32,ty+th*.30,tw*.68,th*.40,1.55,'Black',False,'right','large_counterweight',30)
            sy=ty+th*.76
            for i,u in support[:2]:
                add(i,u,tx,sy,tw*.72,th*.13,.50,'SemiBold',True,'left','support_italic',15); sy+=th*.15
    elif motif=='SIDE_NOTE_HERO':
        if hero:
            i,u=hero[0]; add(i,u,tx+tw*.14,ty+th*.24,tw*.78,th*.44,1.20,'Black',False,'left','hero',30)
        sy=ty+th*.02
        for i,u in support[:2]:
            add(i,u,tx,sy,tw*.36,th*.10,.46,'SemiBold',True,'left','side_note',15); sy+=th*.115
    elif motif=='BLACK_LABEL_PUNCH':
        if labels:
            i,u=labels[0]; add(i,u,tx,ty,tw*.34,th*.13,.48,'Black',False,'center','black_label',35)
        if hero:
            i,u=hero[0]; add(i,u,tx,ty+th*.22,tw,th*.48,1.45,'Black',False,'left','punch',30)
        sy=ty+th*.76
        for i,u in support[:2]:
            add(i,u,tx+.03,sy,tw*.82,th*.12,.48,'SemiBold',False,'left','support',15); sy+=th*.13
    elif motif=='OFF_AXIS_SUPPORT':
        if hero:
            i,u=hero[0]; add(i,u,tx,ty+th*.14,tw*.86,th*.42,1.18,'Black',False,'left','hero',30)
        sy=ty+th*.61
        for n,(i,u) in enumerate(support[:3]):
            off=.06*n
            add(i,u,tx+.05+off,sy,tw*.68,th*.11,.48,'SemiBold',True,'left','off_axis_support',15+n); sy+=th*.12
    elif motif=='FULL_FRAME_HIT':
        if hero:
            target=promote if promote is not None else hero[-1][0]; u=units[target]
            add(target,u,tx,ty+th*.22,tw,th*.54,2.15*ar['hero_scale'],'Black',False,'center','full_frame_hit',40)
            for i,u2 in [x for x in hero if x[0]!=target][:1]:
                add(i,u2,tx+tw*.14,ty,tw*.72,th*.12,.60,'SemiBold',False,'center','setup',20)
        for i,u in support[:1]:
            add(i,u,tx+tw*.20,ty+th*.82,tw*.60,th*.10,.44,'SemiBold',True,'center','support_italic',15)
    elif motif=='COLUMN_BUILD':
        y=ty
        entries=hero+support
        for n,(i,u) in enumerate(entries[:5]):
            ishero=u.role=='hero'; hh=th*(.22 if ishero else .13); scale=.92 if ishero else .48
            add(i,u,tx,y,tw,hh,scale,'Black' if ishero else 'SemiBold',u.role=='support','left','column_line',30 if ishero else 15); y+=hh+.015
    elif motif=='REPLACEMENT_LOCKUP':
        if hero:
            i,u=hero[0]; add(i,u,tx,ty+th*.15,tw,th*.48,1.45,'Black',False,'left','replace_stage_a',30)
        if len(hero)>1:
            i,u=hero[1]; add(i,u,tx,ty+th*.15,tw,th*.48,1.55,'Black',False,'left','replace_stage_b',31)
        for i,u in support[:1]:
            add(i,u,tx,ty+th*.73,tw*.78,th*.12,.48,'SemiBold',True,'left','support_italic',15)
    elif motif=='EDGE_CROP_HERO':
        if hero:
            target=promote if promote is not None else hero[-1][0];u=units[target]
            crop=ar['edge_crop_max']
            # Crops only into outer safe edge; never across the illustration zone boundary.
            add(target,u,max(0,tx-crop*tw),ty+th*.18,tw*(1+crop),th*.52,2.00,'Black',False,'left','edge_crop_hero',40)
            for i,u2 in [x for x in hero if x[0]!=target][:1]:
                add(i,u2,tx+tw*.12,ty,tw*.72,th*.15,.55,'SemiBold',False,'left','setup',20)
    elif motif=='WORD_OBJECT_BRIDGE':
        if hero:
            i,u=hero[0]; add(i,u,tx,ty+th*.12,tw*.92,th*.36,1.12,'Black',False,'left','hero',30)
            # bridge word sits at text-zone edge, aligned toward illustration but not crossing it.
            if promote is not None and promote!=i:
                pu=units[promote]; add(promote,pu,tx+tw*.45,ty+th*.52,tw*.52,th*.23,1.42,'Black',False,'right','bridge_word',35)
        for i,u in support[:1]:
            add(i,u,tx,ty+th*.80,tw*.58,th*.10,.44,'SemiBold',True,'left','support_italic',15)
    else:
        warnings.append('UNKNOWN_MOTIF')

    # Internal text collision check.
    for a in range(len(blocks)):
        A=blocks[a].bbox
        for b in range(a+1,len(blocks)):
            B=blocks[b].bbox
            # Replacement group blocks are allowed to occupy same slot because they are temporal alternatives.
            if blocks[a].style.startswith('replace_stage') and blocks[b].style.startswith('replace_stage'): continue
            x=max(0,min(A['x']+A['w'],B['x']+B['w'])-max(A['x'],B['x']))
            y=max(0,min(A['y']+A['h'],B['y']+B['h'])-max(A['y'],B['y']))
            if x*y>0: warnings.append(f'TEXT_BLOCK_COLLISION:{a}:{b}')
    return blocks,warnings

def compile_performance(beat_type:str,aspect:str,duration_ms:int,units:List[Dict[str,Any]],
                        shot_role:str='TEXT_LED',object_present:bool=True,prev_motif:Optional[str]=None,
                        energy:float=.55,complexity:float=.45)->Dict[str,Any]:
    parsed=[TextUnit(**u) for u in units]
    promote=_promote_index(parsed)
    motif=choose_motif(beat_type,parsed,aspect,object_present,prev_motif)
    text_load=clamp(sum(token_count(u.text) for u in parsed)/28,.15,1)
    spatial=_zones(aspect,shot_role,object_present,text_load)
    blocks,warnings=_layout_blocks(motif,aspect,parsed,spatial.text_zone,spatial.illustration_zone,promote)

    # V2 remains timing substrate, but V3 injects performance events.
    v2_units=[]
    for u in parsed:
        role='support' if u.role in {'support','label'} else 'hero'
        v2_units.append({'text':u.text,'role':role,'emphasis':u.emphasis,'replace_group':u.replace_group})
    choreo=compile_v2(beat_type,duration_ms,v2_units,energy=energy,complexity=complexity)
    events=list(choreo['events'])

    # Performance events: reconfiguration, label punch, support tilt, and transition carrier.
    perf=[]
    if motif in {'SPLIT_SCALE_LOCKUP','PROMOTED_WORD_STACK','FULL_FRAME_HIT','EDGE_CROP_HERO'} and promote is not None:
        hero_events=[e for e in events if e['unit_index']==promote and e['role']=='hero']
        start=min([e['start_ms'] for e in hero_events],default=max(80,int(duration_ms*.14)))
        perf.append({'unit_index':promote,'event':'WORD_PROMOTION','start_ms':start,'end_ms':min(duration_ms-300,start+260),'strength':.96})
    if motif=='REPLACEMENT_LOCKUP':
        perf.append({'unit_index':-1,'event':'SPATIAL_RECONFIGURE','start_ms':int(duration_ms*.46),'end_ms':int(duration_ms*.62),'strength':.92})
    if motif=='BLACK_LABEL_PUNCH':
        perf.append({'unit_index':next((i for i,u in enumerate(parsed) if u.role=='label'),-1),'event':'LABEL_INVERT','start_ms':120,'end_ms':330,'strength':.88})
    if any(b.italic for b in blocks):
        first=min([e['start_ms'] for e in events if e['role']=='support'],default=int(duration_ms*.48))
        perf.append({'unit_index':-1,'event':'SUPPORT_ITALIC_DRIFT','start_ms':first,'end_ms':min(duration_ms-250,first+280),'strength':.38,'tilt_deg':ASPECT_RULES[aspect]['support_tilt_deg']})

    # Text-as-transition: high-emphasis promoted word or label may become wipe/mask carrier.
    carrier=None
    if beat_type.upper() in {'HOOK','REFRAME','PAYOFF','CTA','EMPHASIS'}:
        ci=promote if promote is not None else next((i for i,u in enumerate(parsed) if u.role=='hero'),None)
        if ci is not None:
            carrier={'unit_index':ci,'mode':'TEXT_MASK_WIPE' if motif!='BLACK_LABEL_PUNCH' else 'LABEL_EXPAND_WIPE',
                     'start_ms':max(0,duration_ms-360),'end_ms':duration_ms,'direction':'FORWARD_READING'}

    all_events=events+perf
    # QA metrics
    hero_scales=[b.font_scale for b in blocks if b.role=='hero']
    support_scales=[b.font_scale for b in blocks if b.role=='support']
    ratio=(max(hero_scales)/(max(support_scales) or 1)) if support_scales else (max(hero_scales) if hero_scales else 0)
    if support_scales and ratio<1.65: warnings.append('HERO_SUPPORT_SCALE_CONTRAST_WEAK')
    if motif=='FULL_FRAME_HIT' and not any(b.font_scale>=1.8 for b in blocks): warnings.append('FULL_FRAME_HIT_NOT_LARGE_ENOUGH')
    if spatial.status!='PASS': warnings.append('SPATIAL_AUTHORITY_FAIL')
    if any(x.startswith('TEXT_BLOCK_COLLISION') for x in warnings): pass_gate=False
    else: pass_gate=choreo['pass_gate'] and spatial.status=='PASS' and 'HERO_SUPPORT_SCALE_CONTRAST_WEAK' not in warnings

    reading=sorted(range(len(blocks)), key=lambda i:(blocks[i].z,blocks[i].bbox['y']))
    focal=sorted(range(len(blocks)), key=lambda i:(blocks[i].emphasis,blocks[i].font_scale,blocks[i].z), reverse=True)
    metrics={
        'hero_support_scale_ratio':round(ratio,3),
        'block_count':len(blocks),
        'promoted_unit_index':promote,
        'motif_diversity_class':motif,
        'spatial_score':spatial.metrics.get('score'),
        'text_zone_fraction':spatial.metrics.get('text_fraction'),
        'event_count':len(all_events),
    }
    plan=PerformancePlan(beat_type.upper(),aspect,motif,spatial.preset,blocks,
                         {'base':choreo,'performance_events':perf,'all_events':all_events},
                         carrier,reading,focal,list(dict.fromkeys(warnings+choreo['warnings'])),metrics,pass_gate)
    return asdict(plan)

def compile_story(beats:List[Dict[str,Any]],aspect:str)->List[Dict[str,Any]]:
    out=[]; prev=None
    for b in beats:
        p=compile_performance(b['beat_type'],aspect,b['duration_ms'],b['units'],
                              shot_role=b.get('shot_role','TEXT_LED'),object_present=b.get('object_present',True),
                              prev_motif=prev,energy=b.get('energy',.55),complexity=b.get('complexity',.45))
        out.append(p); prev=p['motif']
    # Story-level anti-repetition QA.
    for i in range(1,len(out)):
        if out[i]['motif']==out[i-1]['motif']:
            out[i]['warnings'].append('CONSECUTIVE_MOTIF_REPEAT')
            out[i]['pass_gate']=False
    return out

if __name__=='__main__':
    sample=[
        {'text':'THE EASIEST WAY','role':'hero','emphasis':.55,'semantic_role':'setup'},
        {'text':'TO SELL','role':'hero','emphasis':1.0,'semantic_role':'punch'},
        {'text':'is not to convince harder','role':'support','emphasis':.35,'semantic_role':'qualifier','italic':True},
    ]
    print(json.dumps(compile_performance('HOOK','1x1',2800,sample),indent=2))
