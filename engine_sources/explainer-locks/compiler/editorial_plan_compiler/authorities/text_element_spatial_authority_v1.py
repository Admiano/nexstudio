from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import math, json

ASPECTS={
    '9x16':(720,1280),
    '1x1':(1080,1080),
    '16x9':(1280,720),
}

# Domain-agnostic shot roles. No subject/topic words are used for layout routing.
SHOT_ROLES={'TEXT_LED','ILLUSTRATION_LED','HYBRID','CHARACTER_EMPHASIS','PAYOFF'}

@dataclass(frozen=True)
class Rect:
    x: float; y: float; w: float; h: float
    @property
    def x2(self): return self.x+self.w
    @property
    def y2(self): return self.y+self.h
    @property
    def cx(self): return self.x+self.w/2
    @property
    def cy(self): return self.y+self.h/2
    def area(self): return max(0,self.w)*max(0,self.h)
    def inset(self,p): return Rect(self.x+p,self.y+p,max(0,self.w-2*p),max(0,self.h-2*p))
    def expand(self,p): return Rect(self.x-p,self.y-p,self.w+2*p,self.h+2*p)

@dataclass
class SpatialRequest:
    aspect: str
    shot_role: str
    text_load: float = .5              # 0..1 expected copy density
    illustration_load: float = .5      # 0..1 expected visual density
    character_present: bool = False
    text_dominance: float = .5         # 0..1
    illustration_dominance: float = .5 # 0..1
    reading_direction: str = 'LTR'
    focal_emphasis: float = .7

@dataclass
class SpatialPlan:
    aspect: str
    shot_role: str
    safe_frame: Dict
    text_zone: Dict
    illustration_zone: Dict
    character_zone: Optional[Dict]
    reading_path: List[str]
    focal_order: List[str]
    min_gap_px: int
    status: str
    warnings: List[str]
    preset: str
    metrics: Dict

def overlap(a:Rect,b:Rect)->float:
    x=max(0,min(a.x2,b.x2)-max(a.x,b.x)); y=max(0,min(a.y2,b.y2)-max(a.y,b.y))
    return x*y

def gap(a:Rect,b:Rect)->float:
    dx=max(0,max(a.x,b.x)-min(a.x2,b.x2)); dy=max(0,max(a.y,b.y)-min(a.y2,b.y2))
    return math.hypot(dx,dy)

def rect_to_dict(r:Rect): return {'x':round(r.x,1),'y':round(r.y,1),'w':round(r.w,1),'h':round(r.h,1)}

class SpatialAuthorityV1:
    def __init__(self):
        self.safe_margin_fraction={'9x16':.07,'1x1':.07,'16x9':.06}
        self.min_gap_fraction={'9x16':.040,'1x1':.035,'16x9':.030}
        self.max_text_fraction={'9x16':.42,'1x1':.40,'16x9':.46}
        self.max_illustration_fraction={'9x16':.56,'1x1':.58,'16x9':.58}

    def plan(self,req:SpatialRequest)->SpatialPlan:
        assert req.aspect in ASPECTS
        assert req.shot_role in SHOT_ROLES
        W,H=ASPECTS[req.aspect]
        margin=round(min(W,H)*self.safe_margin_fraction[req.aspect])
        safe=Rect(margin,margin,W-2*margin,H-2*margin)
        min_gap=max(24,round(min(W,H)*self.min_gap_fraction[req.aspect]))

        # Preset ordering is semantic-role driven, never topic driven.
        presets=self._preset_order(req)
        attempts=[]
        for preset in presets:
            text,illus,char=self._make_zones(req,safe,min_gap,preset)
            result=self._validate(req,safe,text,illus,char,min_gap)
            attempts.append((preset,text,illus,char,result))
            if result['status']=='PASS':
                return self._final(req,safe,text,illus,char,min_gap,preset,result)

        # Fail closed with the best deterministic restage, but mark FAIL.
        best=max(attempts,key=lambda x:x[4]['score'])
        preset,text,illus,char,result=best
        return self._final(req,safe,text,illus,char,min_gap,preset,result)

    def _preset_order(self,req):
        role=req.shot_role
        if role=='TEXT_LED':
            return ['STACK_TEXT_TOP','TEXT_LEFT_VISUAL_RIGHT','TEXT_CENTER_VISUAL_BOTTOM','TEXT_TOP_VISUAL_BOTTOM']
        if role=='ILLUSTRATION_LED':
            return ['VISUAL_CENTER_TEXT_BOTTOM','TEXT_TOP_VISUAL_BOTTOM','VISUAL_LEFT_TEXT_RIGHT','TEXT_LEFT_VISUAL_RIGHT']
        if role=='CHARACTER_EMPHASIS':
            return ['CHAR_LEFT_TEXT_RIGHT','CHAR_RIGHT_TEXT_LEFT','CHAR_BOTTOM_TEXT_TOP']
        if role=='PAYOFF':
            return ['TEXT_CENTER_VISUAL_BOTTOM','VISUAL_CENTER_TEXT_TOP','TEXT_TOP_VISUAL_BOTTOM']
        return ['TEXT_LEFT_VISUAL_RIGHT','TEXT_TOP_VISUAL_BOTTOM','VISUAL_LEFT_TEXT_RIGHT','VISUAL_CENTER_TEXT_BOTTOM']

    def _make_zones(self,req,safe,g,preset):
        x,y,w,h=safe.x,safe.y,safe.w,safe.h
        # ratios adapt to content load and dominance, not subject.
        td=max(.22,min(.60,.30+.22*req.text_dominance+.10*req.text_load))
        idom=max(.28,min(.66,.34+.22*req.illustration_dominance+.10*req.illustration_load))
        char=None

        if preset=='TEXT_LEFT_VISUAL_RIGHT':
            tw=w*max(.32,min(.48,td)); iw=w-tw-g
            text=Rect(x,y,tw,h)
            illus=Rect(x+tw+g,y,iw,h)
        elif preset=='VISUAL_LEFT_TEXT_RIGHT':
            tw=w*max(.32,min(.48,td)); iw=w-tw-g
            illus=Rect(x,y,iw,h)
            text=Rect(x+iw+g,y,tw,h)
        elif preset=='TEXT_TOP_VISUAL_BOTTOM':
            th=h*max(.22,min(.40,td)); ih=h-th-g
            text=Rect(x,y,w,th)
            illus=Rect(x,y+th+g,w,ih)
        elif preset=='VISUAL_CENTER_TEXT_BOTTOM':
            th=h*max(.18,min(.28,.18+.10*req.text_load)); ih=h-th-g
            illus=Rect(x,y,w,ih)
            text=Rect(x,y+ih+g,w,th)
        elif preset=='VISUAL_CENTER_TEXT_TOP':
            th=h*max(.18,min(.30,.18+.12*req.text_load)); ih=h-th-g
            text=Rect(x,y,w,th)
            illus=Rect(x,y+th+g,w,ih)
        elif preset=='TEXT_CENTER_VISUAL_BOTTOM':
            th=h*max(.24,min(.38,.25+.12*req.text_load)); ih=h-th-g
            text=Rect(x,y,w,th)
            illus=Rect(x,y+th+g,w,ih)
        elif preset=='STACK_TEXT_TOP':
            # leaves deliberate breathing room before a smaller support illustration.
            th=h*max(.32,min(.48,.34+.14*req.text_load));
            text=Rect(x,y,w,th)
            illus=Rect(x+w*.12,y+th+g,w*.76,h-th-g)
        elif preset=='CHAR_LEFT_TEXT_RIGHT':
            cw=w*.38; tw=w-cw-g
            char=Rect(x,y+h*.08,cw,h*.84)
            text=Rect(x+cw+g,y,tw,h*.44)
            illus=Rect(x+cw+g,y+h*.48,tw,h*.52)
        elif preset=='CHAR_RIGHT_TEXT_LEFT':
            cw=w*.38; tw=w-cw-g
            text=Rect(x,y,tw,h*.44)
            illus=Rect(x,y+h*.48,tw,h*.52)
            char=Rect(x+tw+g,y+h*.08,cw,h*.84)
        elif preset=='CHAR_BOTTOM_TEXT_TOP':
            th=h*.28; ch=h*.48; ih=h-th-ch-2*g
            text=Rect(x,y,w,th)
            illus=Rect(x,y+th+g,w,ih)
            char=Rect(x+w*.18,y+th+g+ih+g,w*.64,ch)
        else:
            text=Rect(x,y,w*.42,h)
            illus=Rect(x+w*.42+g,y,w*.58-g,h)

        # If no explicit character zone but character is present, carve from illustration.
        if req.character_present and char is None:
            if illus.w>=illus.h:
                cw=illus.w*.38
                char=Rect(illus.x,illus.y+illus.h*.08,cw,illus.h*.84)
                illus=Rect(illus.x+cw+g,illus.y,max(0,illus.w-cw-g),illus.h)
            else:
                ch=illus.h*.40
                char=Rect(illus.x+illus.w*.08,illus.y,illus.w*.84,ch)
                illus=Rect(illus.x,illus.y+ch+g,illus.w,max(0,illus.h-ch-g))
        return text,illus,char

    def _validate(self,req,safe,text,illus,char,min_gap):
        warnings=[]; score=1.0
        zones=[('text',text),('illustration',illus)]+([('character',char)] if char else [])
        # Bounds
        for name,r in zones:
            if r.x<safe.x-1 or r.y<safe.y-1 or r.x2>safe.x2+1 or r.y2>safe.y2+1:
                score-=.5; warnings.append(f'{name.upper()}_OUTSIDE_SAFE_FRAME')
            if r.w<=0 or r.h<=0:
                score-=.8; warnings.append(f'{name.upper()}_EMPTY')
        # Collision and spacing: expanded boxes may not overlap.
        pairs=[('text',text,'illustration',illus)]
        if char:
            pairs += [('text',text,'character',char),('illustration',illus,'character',char)]
        for na,a,nb,b in pairs:
            ov=overlap(a,b)
            gp=gap(a,b)
            if ov>0:
                score-=.7; warnings.append(f'COLLISION:{na}:{nb}:{ov:.0f}px2')
            elif gp < min_gap*.92:
                score-=.22; warnings.append(f'GAP_TOO_TIGHT:{na}:{nb}:{gp:.1f}px')
        # Occupancy / hierarchy
        safe_area=safe.area()
        tf=text.area()/safe_area; inf=illus.area()/safe_area
        if req.shot_role=='TEXT_LED' and tf<=inf*.60:
            score-=.18; warnings.append('TEXT_LED_HIERARCHY_WEAK')
        if req.shot_role=='ILLUSTRATION_LED' and inf<=tf*.95:
            score-=.18; warnings.append('ILLUSTRATION_LED_HIERARCHY_WEAK')
        if req.shot_role=='CHARACTER_EMPHASIS' and char and char.area()/safe_area<.22:
            score-=.18; warnings.append('CHARACTER_EMPHASIS_TOO_SMALL')
        # Reading path should not jump backwards spatially in LTR side-by-side layouts.
        if req.reading_direction=='LTR' and text.cx>illus.cx and req.shot_role in {'TEXT_LED','HYBRID'}:
            score-=.10; warnings.append('LTR_READING_PATH_REVERSED')
        status='PASS' if score>=.72 and not any(x.startswith('COLLISION') or 'OUTSIDE_SAFE' in x or x.endswith('_EMPTY') for x in warnings) else 'FAIL'
        return {'status':status,'score':round(score,3),'warnings':warnings,
                'text_fraction':round(tf,3),'illustration_fraction':round(inf,3)}

    def _final(self,req,safe,text,illus,char,min_gap,preset,result):
        # Reading/focal orders are declarative and usable downstream by motion authority.
        if req.shot_role=='TEXT_LED':
            reading=['hero_text','support_text','illustration']
            focal=['text','illustration']
        elif req.shot_role=='ILLUSTRATION_LED':
            reading=['illustration','hero_text','support_text']
            focal=['illustration','text']
        elif req.shot_role=='CHARACTER_EMPHASIS':
            reading=['character','hero_text','illustration']
            focal=['character','text','illustration']
        elif req.shot_role=='PAYOFF':
            reading=['hero_text','illustration','hold']
            focal=['text','illustration']
        else:
            reading=['hero_text','illustration','support_text']
            focal=['text','illustration'] if req.text_dominance>=req.illustration_dominance else ['illustration','text']
        return SpatialPlan(req.aspect,req.shot_role,rect_to_dict(safe),rect_to_dict(text),rect_to_dict(illus),
                           rect_to_dict(char) if char else None,reading,focal,min_gap,result['status'],result['warnings'],preset,
                           {'score':result['score'],'text_fraction':result['text_fraction'],'illustration_fraction':result['illustration_fraction']})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--aspect',default='1x1');p.add_argument('--role',default='HYBRID')
    args=p.parse_args()
    req=SpatialRequest(aspect=args.aspect,shot_role=args.role)
    print(json.dumps(asdict(SpatialAuthorityV1().plan(req)),indent=2))
