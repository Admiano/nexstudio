from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import json, math, random, sys
try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:  # raster preview is optional
    np = None
    Image = ImageDraw = ImageFilter = None

from .text_element_spatial_authority_v1 import SpatialAuthorityV1, SpatialRequest, ASPECTS

# Monochrome editorial system: white, black, and neutral greys only.
BG_WHITE=(248,248,247,255)
PURE_WHITE=(255,255,255,255)
INK=(14,14,14,255)
GREY_1=(242,242,241,255)
GREY_2=(232,232,231,255)
GREY_3=(214,214,213,255)

TEMPLATES={
    'SOFT_FIELD','CARD_STAGE','DOCUMENT_STAGE','PRODUCT_STAGE',
    'GRID_FIELD','SPOTLIGHT_STAGE','LAYERED_PLANE'
}

@dataclass
class BackgroundRequest:
    aspect:str
    shot_role:str
    text_load:float=.5
    illustration_load:float=.5
    character_present:bool=False
    text_dominance:float=.5
    illustration_dominance:float=.5
    evidence_density:float=.0
    technical_density:float=.0
    depth_need:float=.5
    object_formality:float=.5
    transition_energy:float=.5
    focal_emphasis:float=.7
    preferred_template:Optional[str]=None

@dataclass
class BackgroundPlan:
    aspect:str
    shot_role:str
    template:str
    canvas:Tuple[int,int]
    monochrome:bool
    stage_zone:Dict
    depth_layers:List[Dict]
    shadow_rule:Dict
    grid_rule:Dict
    texture_rule:Dict
    mapping_reason:List[str]
    status:str
    warnings:List[str]

def _rect(d):
    return (float(d['x']),float(d['y']),float(d['x']+d['w']),float(d['y']+d['h']))

def _clamp(v,a=0,b=1): return max(a,min(b,v))

def _box_from_zone(zone,pad=0):
    return (int(zone['x']+pad),int(zone['y']+pad),int(zone['x']+zone['w']-pad),int(zone['y']+zone['h']-pad))

class EditorialBackgroundSystemV1:
    def __init__(self):
        self.spatial=SpatialAuthorityV1()
        self.shadow={
            'max_opacity':.18,
            'default_opacity':.13,
            'blur_fraction_min':.012,
            'blur_fraction_max':.028,
            'offset_fraction':.010,
            'rule':'soft neutral shadow only; never compete with content'
        }
        self.grid={
            'max_opacity':.10,
            'default_opacity':.055,
            'spacing_fraction':.055,
            'dot_radius_fraction':.0022,
            'rule':'grid is contextual stage texture, never a foreground object'
        }
        self.texture={
            'noise_opacity_max':.025,
            'default_noise_opacity':.012,
            'rule':'subtle luminance texture only; monochrome; imperceptible at reading distance'
        }

    def plan(self, req:BackgroundRequest)->BackgroundPlan:
        assert req.aspect in ASPECTS
        assert req.preferred_template in TEMPLATES or req.preferred_template is None
        sreq=SpatialRequest(
            aspect=req.aspect, shot_role=req.shot_role,
            text_load=req.text_load, illustration_load=req.illustration_load,
            character_present=req.character_present,
            text_dominance=req.text_dominance,
            illustration_dominance=req.illustration_dominance,
            focal_emphasis=req.focal_emphasis
        )
        sp=self.spatial.plan(sreq)
        template,reasons=self._map_template(req,sp)
        stage_zone=self._stage_zone(template,sp)
        warnings=[]
        if template in {'CARD_STAGE','DOCUMENT_STAGE','PRODUCT_STAGE','LAYERED_PLANE'} and stage_zone['w']<80:
            warnings.append('STAGE_ZONE_TOO_NARROW')
        if sp.status!='PASS': warnings.append('UPSTREAM_SPATIAL_PLAN_FAIL')
        status='PASS' if not warnings else 'FAIL'
        layers=self._depth_layers(template,stage_zone,req)
        return BackgroundPlan(
            aspect=req.aspect, shot_role=req.shot_role, template=template,
            canvas=ASPECTS[req.aspect], monochrome=True,
            stage_zone=stage_zone, depth_layers=layers,
            shadow_rule=self.shadow, grid_rule=self.grid, texture_rule=self.texture,
            mapping_reason=reasons, status=status, warnings=warnings
        )

    def _map_template(self,req,sp):
        if req.preferred_template:
            return req.preferred_template,['explicit_preference']
        r=req.shot_role
        reasons=[f'shot_role:{r}']
        # Structural routing only — no topic nouns.
        if r=='TEXT_LED':
            if req.evidence_density>.58 or req.technical_density>.68:
                reasons.append('supporting_evidence_or_technical_context')
                return 'DOCUMENT_STAGE',reasons
            if req.focal_emphasis>.80:
                reasons.append('high_focal_emphasis')
                return 'SPOTLIGHT_STAGE',reasons
            return 'SOFT_FIELD',reasons
        if r=='ILLUSTRATION_LED':
            if req.object_formality>.66:
                reasons.append('formal_object_presentation')
                return 'PRODUCT_STAGE',reasons
            if req.technical_density>.58 or req.evidence_density>.58:
                reasons.append('structured_information')
                return 'GRID_FIELD',reasons
            return 'CARD_STAGE',reasons
        if r=='CHARACTER_EMPHASIS':
            if req.depth_need>.62:
                reasons.append('character_depth_separation')
                return 'LAYERED_PLANE',reasons
            return 'SPOTLIGHT_STAGE',reasons
        if r=='PAYOFF':
            if req.transition_energy>.70:
                reasons.append('payoff_transition_energy')
                return 'LAYERED_PLANE',reasons
            return 'SOFT_FIELD',reasons
        # HYBRID and fallback
        if req.evidence_density>.60:
            reasons.append('evidence_requires_surface')
            return 'DOCUMENT_STAGE',reasons
        if req.depth_need>.58:
            reasons.append('multi_element_depth_need')
            return 'LAYERED_PLANE',reasons
        return 'CARD_STAGE',reasons

    def _stage_zone(self,template,sp):
        W,H=ASPECTS[sp.aspect]
        iz=sp.illustration_zone.copy()
        tz=sp.text_zone.copy()
        cz=sp.character_zone
        if template in {'CARD_STAGE','DOCUMENT_STAGE','PRODUCT_STAGE'}:
            # stage belongs to illustration territory. If character emphasis, unite illustration + character without entering text.
            if cz:
                x=min(iz['x'],cz['x']); y=min(iz['y'],cz['y'])
                x2=max(iz['x']+iz['w'],cz['x']+cz['w']); y2=max(iz['y']+iz['h'],cz['y']+cz['h'])
                return {'x':round(x,1),'y':round(y,1),'w':round(x2-x,1),'h':round(y2-y,1)}
            return iz
        if template=='LAYERED_PLANE':
            # broad stage may sit behind illustration + character, but not hero text.
            zones=[iz]+([cz] if cz else [])
            x=min(z['x'] for z in zones); y=min(z['y'] for z in zones)
            x2=max(z['x']+z['w'] for z in zones); y2=max(z['y']+z['h'] for z in zones)
            return {'x':round(x,1),'y':round(y,1),'w':round(x2-x,1),'h':round(y2-y,1)}
        # texture-only stages can span the safe frame because they are background, not objects.
        return sp.safe_frame.copy()

    def _depth_layers(self,template,zone,req):
        layers=[{'z':0,'kind':'base_field','opacity':1.0}]
        if template in {'CARD_STAGE','DOCUMENT_STAGE','PRODUCT_STAGE'}:
            layers += [
                {'z':1,'kind':'soft_shadow','opacity':self.shadow['default_opacity']},
                {'z':2,'kind':template.lower(),'opacity':1.0}
            ]
        elif template=='LAYERED_PLANE':
            layers += [
                {'z':1,'kind':'rear_plane','opacity':.55},
                {'z':2,'kind':'mid_plane_shadow','opacity':self.shadow['default_opacity']},
                {'z':3,'kind':'mid_plane','opacity':.95}
            ]
        elif template=='GRID_FIELD':
            layers += [{'z':1,'kind':'subtle_grid','opacity':self.grid['default_opacity']}]
        elif template=='SPOTLIGHT_STAGE':
            layers += [{'z':1,'kind':'soft_spotlight','opacity':.10}]
        elif template=='SOFT_FIELD':
            layers += [{'z':1,'kind':'soft_luminance_gradient','opacity':.08}]
        return layers

    def render(self,req:BackgroundRequest)->Tuple[Image.Image,BackgroundPlan]:
        plan=self.plan(req)
        W,H=plan.canvas
        base=Image.new('RGBA',(W,H),BG_WHITE)
        t=plan.template
        if t=='SOFT_FIELD': self._render_soft_field(base,plan)
        elif t=='CARD_STAGE': self._render_card(base,plan)
        elif t=='DOCUMENT_STAGE': self._render_document(base,plan)
        elif t=='PRODUCT_STAGE': self._render_product(base,plan)
        elif t=='GRID_FIELD': self._render_grid(base,plan)
        elif t=='SPOTLIGHT_STAGE': self._render_spotlight(base,plan)
        elif t=='LAYERED_PLANE': self._render_layered(base,plan)
        self._apply_texture(base,plan)
        return base,plan

    def _shadowed_panel(self,base,box,radius,fill=PURE_WHITE,shadow_opacity=.13,offset=None,blur=None):
        W,H=base.size; minD=min(W,H)
        if offset is None: offset=max(6,int(minD*self.shadow['offset_fraction']))
        if blur is None: blur=max(10,int(minD*.020))
        x0,y0,x1,y1=box
        shadow=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(shadow)
        sd.rounded_rectangle((x0+offset,y0+offset,x1+offset,y1+offset),radius=radius,fill=(0,0,0,int(255*shadow_opacity)))
        shadow=shadow.filter(ImageFilter.GaussianBlur(blur))
        base.alpha_composite(shadow)
        dr=ImageDraw.Draw(base)
        dr.rounded_rectangle(box,radius=radius,fill=fill,outline=(220,220,219,255),width=max(1,int(minD*.002)))

    def _render_soft_field(self,base,plan):
        W,H=base.size
        # soft vertical luminance gradient; no object-like geometry.
        arr=np.zeros((H,W,4),dtype=np.uint8)
        yy=np.linspace(-1,1,H)[:,None]
        val=(246+7*np.exp(-(yy/0.65)**2)).astype(np.uint8)
        arr[:,:,0]=val;arr[:,:,1]=val;arr[:,:,2]=val;arr[:,:,3]=255
        im=Image.fromarray(arr,'RGBA')
        base.alpha_composite(im)

    def _render_card(self,base,plan):
        z=plan.stage_zone; pad=max(10,int(min(base.size)*.018)); box=_box_from_zone(z,pad)
        self._shadowed_panel(base,box,radius=max(16,int(min(base.size)*.025)))

    def _render_document(self,base,plan):
        z=plan.stage_zone; pad=max(12,int(min(base.size)*.025)); box=list(_box_from_zone(z,pad))
        # Slight top-left reveal. Document remains in illustration zone.
        self._shadowed_panel(base,tuple(box),radius=max(8,int(min(base.size)*.012)),fill=(253,253,252,255),shadow_opacity=.15)
        dr=ImageDraw.Draw(base); x0,y0,x1,y1=box
        line=(208,208,207,255); w=max(1,int(min(base.size)*.002))
        # faint document rules; never invade text zone because stage itself is in illustration zone
        for i in range(4):
            yy=y0+(y1-y0)*(.18+.13*i)
            dr.line((x0+(x1-x0)*.12,yy,x0+(x1-x0)*(.78-.05*(i%2)),yy),fill=line,width=w)
        dr.rectangle((x0+(x1-x0)*.12,y0+(y1-y0)*.10,x0+(x1-x0)*.38,y0+(y1-y0)*.135),fill=(188,188,187,255))

    def _render_product(self,base,plan):
        z=plan.stage_zone; pad=max(10,int(min(base.size)*.022)); box=_box_from_zone(z,pad)
        self._shadowed_panel(base,box,radius=max(18,int(min(base.size)*.028)),fill=(252,252,251,255),shadow_opacity=.16)
        dr=ImageDraw.Draw(base); x0,y0,x1,y1=box
        # subtle pedestal line gives object a stage without becoming foreground clutter
        y=y0+(y1-y0)*.82
        dr.line((x0+(x1-x0)*.16,y,x0+(x1-x0)*.84,y),fill=(214,214,213,255),width=max(2,int(min(base.size)*.003)))

    def _render_grid(self,base,plan):
        W,H=base.size; z=plan.stage_zone
        spacing=max(28,int(min(W,H)*self.grid['spacing_fraction']))
        r=max(1,int(min(W,H)*self.grid['dot_radius_fraction']))
        layer=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
        x0,y0,x1,y1=_box_from_zone(z,0)
        c=(80,80,80,int(255*self.grid['default_opacity']))
        for x in range(int(x0),int(x1)+1,spacing):
            for y in range(int(y0),int(y1)+1,spacing):
                d.ellipse((x-r,y-r,x+r,y+r),fill=c)
        base.alpha_composite(layer)

    def _render_spotlight(self,base,plan):
        W,H=base.size; z=plan.stage_zone
        cx=z['x']+z['w']*.5; cy=z['y']+z['h']*.5
        yy,xx=np.mgrid[0:H,0:W]
        sx=max(1,z['w']*.62); sy=max(1,z['h']*.62)
        dist=((xx-cx)/sx)**2+((yy-cy)/sy)**2
        alpha=np.clip(np.exp(-dist*2.2)*22,0,22).astype(np.uint8)
        layer=np.zeros((H,W,4),dtype=np.uint8)
        layer[:,:,:3]=255;layer[:,:,3]=alpha
        base.alpha_composite(Image.fromarray(layer,'RGBA'))

    def _render_layered(self,base,plan):
        z=plan.stage_zone; W,H=base.size; minD=min(W,H)
        x0,y0,x1,y1=_box_from_zone(z,max(8,int(minD*.015)))
        dx=max(10,int(minD*.018)); dy=max(10,int(minD*.014))
        rear=(x0+dx,y0-dy,x1+dx,y1-dy)
        dr=ImageDraw.Draw(base)
        dr.rounded_rectangle(rear,radius=max(14,int(minD*.022)),fill=GREY_2,outline=GREY_3,width=max(1,int(minD*.002)))
        self._shadowed_panel(base,(x0,y0,x1,y1),radius=max(16,int(minD*.026)),fill=(253,253,252,255),shadow_opacity=.14)

    def _apply_texture(self,base,plan):
        W,H=base.size
        # deterministic, extremely subtle neutral texture.
        rng=np.random.default_rng(417)
        noise=rng.normal(0,1.25,(H,W,1))
        arr=np.array(base).astype(np.float32)
        arr[:,:,:3]=np.clip(arr[:,:,:3]+noise,0,255)
        base.paste(Image.fromarray(arr.astype(np.uint8),'RGBA'))

def request_from_dict(d): return BackgroundRequest(**d)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--aspect',default='1x1'); p.add_argument('--role',default='HYBRID'); p.add_argument('--template',default=None); p.add_argument('--out',default='.')
    args=p.parse_args()
    req=BackgroundRequest(aspect=args.aspect,shot_role=args.role,preferred_template=args.template)
    img,plan=EditorialBackgroundSystemV1().render(req)
    out=Path(args.out)/f'preview_{args.aspect}_{plan.template}.png'
    img.convert('RGB').save(out)
    print(json.dumps(asdict(plan),indent=2)); print(out)
