from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Dict,List,Optional,Any,Tuple
from pathlib import Path
import sys,json,math

from .text_element_spatial_authority_v1 import SpatialAuthorityV1,SpatialRequest,ASPECTS
from .editorial_background_system_v1 import EditorialBackgroundSystemV1,BackgroundRequest

COMPOSITIONS={
 'FLOATING_PANEL','DOCUMENT_HERO','PRODUCT_PLINTH','OFFSET_GRID_STAGE','RAIL_FRAME',
 'SPLIT_STAGE','EDGE_CROP_OBJECT','STACKED_CARDS','LAYERED_EDITORIAL','OPEN_FIELD'
}

@dataclass
class SceneCompositionRequest:
    aspect:str
    shot_role:str
    text_load:float=.5
    illustration_load:float=.5
    character_present:bool=False
    evidence_density:float=.0
    technical_density:float=.0
    depth_need:float=.5
    object_formality:float=.5
    transition_energy:float=.5
    object_count:int=1
    text_motif:Optional[str]=None
    object_dominance:float=.6
    crop_tolerance:float=.0

@dataclass
class Layer:
    id:str
    role:str
    bbox:Dict[str,float]
    z:int
    rotation_deg:float=0
    shadow:Optional[Dict[str,float]]=None
    crop:Optional[Dict[str,float]]=None
    note:str=''

@dataclass
class SceneCompositionPlan:
    aspect:str
    composition:str
    background_template:str
    text_zone:Dict
    illustration_zone:Dict
    character_zone:Optional[Dict]
    layers:List[Layer]
    depth_order:List[str]
    reading_path:List[str]
    transition_anchor:str
    status:str
    warnings:List[str]
    metrics:Dict[str,Any]

def _overlap(a,b):
    x=max(0,min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x']))
    y=max(0,min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y']))
    return x*y

def _inside(a,b,tol=1):
    return a['x']>=b['x']-tol and a['y']>=b['y']-tol and a['x']+a['w']<=b['x']+b['w']+tol and a['y']+a['h']<=b['y']+b['h']+tol

def _box(x,y,w,h):return {'x':round(x,1),'y':round(y,1),'w':round(max(0,w),1),'h':round(max(0,h),1)}

class EditorialSceneCompositionAuthorityV2:
    def __init__(self):
        self.spatial=SpatialAuthorityV1(); self.background=EditorialBackgroundSystemV1()
        self.outer_crop_max={'9x16':.08,'1x1':.07,'16x9':.06}

    def plan(self,req:SceneCompositionRequest)->SceneCompositionPlan:
        W,H=ASPECTS[req.aspect]
        sp=self.spatial.plan(SpatialRequest(
            aspect=req.aspect,shot_role=req.shot_role,text_load=req.text_load,
            illustration_load=req.illustration_load,character_present=req.character_present,
            text_dominance=.72 if req.shot_role=='TEXT_LED' else .52,
            illustration_dominance=req.object_dominance
        ))
        comp=self._choose(req,sp)
        bg_req=BackgroundRequest(
            aspect=req.aspect,shot_role=req.shot_role,text_load=req.text_load,
            illustration_load=req.illustration_load,character_present=req.character_present,
            text_dominance=.72 if req.shot_role=='TEXT_LED' else .52,
            illustration_dominance=req.object_dominance,evidence_density=req.evidence_density,
            technical_density=req.technical_density,depth_need=req.depth_need,
            object_formality=req.object_formality,transition_energy=req.transition_energy,
            preferred_template=self._background_for(comp,req)
        )
        bg=self.background.plan(bg_req)
        layers=self._layers(comp,req,sp)
        warnings=self._validate(req,sp,layers)
        if sp.status!='PASS':warnings.append('UPSTREAM_SPATIAL_FAIL')
        if bg.status!='PASS':warnings.append('UPSTREAM_BACKGROUND_FAIL')
        status='PASS' if not warnings else 'FAIL'
        metrics={
          'layer_count':len(layers),
          'max_depth':max([l.z for l in layers],default=0),
          'text_overlap_px2':round(sum(_overlap(l.bbox,sp.text_zone) for l in layers if l.role in {'object','panel','document','card','product'}),1),
          'illustration_occupancy':round(sum(l.bbox['w']*l.bbox['h'] for l in layers if l.role in {'object','panel','document','card','product'})/(W*H),3),
          'outer_crop_limit':self.outer_crop_max[req.aspect],
        }
        reading=['hero_text']+(['character'] if req.character_present else [])+['primary_object','support_surface']
        transition_anchor=self._transition_anchor(comp,req)
        return SceneCompositionPlan(req.aspect,comp,bg.template,sp.text_zone,sp.illustration_zone,sp.character_zone,
                                    layers,[l.id for l in sorted(layers,key=lambda x:x.z)],reading,transition_anchor,status,list(dict.fromkeys(warnings)),metrics)

    def _choose(self,req,sp):
        # Structural routing only. No topic words.
        if req.evidence_density>.62:
            return 'DOCUMENT_HERO' if req.object_count<=1 else 'STACKED_CARDS'
        if req.technical_density>.62:
            return 'OFFSET_GRID_STAGE'
        if req.character_present:
            return 'LAYERED_EDITORIAL' if req.depth_need>.55 else 'SPLIT_STAGE'
        if req.object_count>=3:
            return 'STACKED_CARDS'
        if req.object_formality>.72:
            return 'PRODUCT_PLINTH'
        if req.transition_energy>.74 and req.crop_tolerance>.35:
            return 'EDGE_CROP_OBJECT'
        if req.text_motif in {'WORD_OBJECT_BRIDGE','SPLIT_SCALE_LOCKUP'}:
            return 'RAIL_FRAME'
        if req.depth_need>.62:
            return 'LAYERED_EDITORIAL'
        if req.shot_role=='TEXT_LED' and req.illustration_load<.34:
            return 'OPEN_FIELD'
        return 'FLOATING_PANEL'

    def _background_for(self,comp,req):
        return {
          'DOCUMENT_HERO':'DOCUMENT_STAGE','STACKED_CARDS':'LAYERED_PLANE','OFFSET_GRID_STAGE':'GRID_FIELD',
          'LAYERED_EDITORIAL':'LAYERED_PLANE','SPLIT_STAGE':'SPOTLIGHT_STAGE','PRODUCT_PLINTH':'PRODUCT_STAGE',
          'EDGE_CROP_OBJECT':'SOFT_FIELD','RAIL_FRAME':'SOFT_FIELD','OPEN_FIELD':'SOFT_FIELD','FLOATING_PANEL':'CARD_STAGE'
        }[comp]

    def _layers(self,comp,req,sp):
        W,H=ASPECTS[req.aspect]; iz=sp.illustration_zone; cz=sp.character_zone
        x,y,w,h=iz['x'],iz['y'],iz['w'],iz['h']; L=[]
        shadow={'opacity':.13,'blur_fraction':.02,'offset_fraction':.01}
        def add(id,role,b,z,rot=0,sh=None,crop=None,note=''):
            L.append(Layer(id,role,b,z,rot,sh,crop,note))
        if comp=='OPEN_FIELD':
            add('object','object',_box(x+w*.14,y+h*.12,w*.72,h*.72),2,0,None,None,'single isolated object with deliberate air')
        elif comp=='FLOATING_PANEL':
            add('panel','panel',_box(x+w*.05,y+h*.05,w*.90,h*.88),1,-1.0,shadow)
            add('object','object',_box(x+w*.18,y+h*.16,w*.64,h*.58),3,0,None)
        elif comp=='DOCUMENT_HERO':
            rot=-2.0 if req.aspect!='16x9' else -1.2
            add('document_shadow','support',_box(x+w*.09,y+h*.09,w*.80,h*.80),1,rot,shadow)
            add('document','document',_box(x+w*.08,y+h*.05,w*.82,h*.82),2,rot,shadow)
            add('evidence_detail','object',_box(x+w*.14,y+h*.15,w*.70,h*.56),3,0,None)
        elif comp=='PRODUCT_PLINTH':
            add('product_panel','panel',_box(x+w*.06,y+h*.04,w*.88,h*.86),1,0,shadow)
            add('product','product',_box(x+w*.20,y+h*.12,w*.60,h*.55),3,-1.2,None)
            add('plinth','support',_box(x+w*.15,y+h*.73,w*.70,h*.035),2,0,None)
        elif comp=='OFFSET_GRID_STAGE':
            add('grid_surface','support',_box(x,y,w,h),0,0,None)
            add('technical_panel','panel',_box(x+w*.10,y+h*.08,w*.82,h*.78),2,1.1,shadow)
            add('object','object',_box(x+w*.20,y+h*.18,w*.62,h*.52),3,0,None)
        elif comp=='RAIL_FRAME':
            if req.aspect=='9x16':
                add('rail_top','support',_box(x,y,w,h*.10),1,0,shadow)
                add('rail_bottom','support',_box(x,y+h*.86,w,h*.10),1,0,shadow)
                add('object','object',_box(x+w*.10,y+h*.18,w*.80,h*.58),3,0,None)
            else:
                add('rail_left','support',_box(x,y,w*.10,h),1,0,shadow)
                add('rail_right','support',_box(x+w*.88,y,w*.10,h),1,0,shadow)
                add('object','object',_box(x+w*.18,y+h*.10,w*.64,h*.78),3,0,None)
        elif comp=='SPLIT_STAGE':
            if cz:
                add('character_stage','support',_box(cz['x'],cz['y'],cz['w'],cz['h']),1,0,None)
            add('object_panel','panel',_box(x+w*.06,y+h*.08,w*.88,h*.80),1,0,shadow)
            add('object','object',_box(x+w*.18,y+h*.19,w*.64,h*.54),3,0,None)
        elif comp=='EDGE_CROP_OBJECT':
            crop=min(self.outer_crop_max[req.aspect],max(0,req.crop_tolerance*self.outer_crop_max[req.aspect]))
            # Cropping occurs only toward outer canvas edge chosen by illustration zone position.
            left_side=(x+w/2)<W/2
            bx=x-w*crop if left_side else x+w*.12
            bw=w*(.96+crop) if left_side else w*(.96+crop)
            add('object','object',_box(bx,y+h*.06,bw,h*.88),3, -1.3 if left_side else 1.3,None,{'outer_fraction':round(crop,3),'edge':'left' if left_side else 'right'})
        elif comp=='STACKED_CARDS':
            count=min(3,max(2,req.object_count))
            for i in range(count):
                off=i*min(w,h)*.025
                add(f'card_{i}','card',_box(x+w*.10+off,y+h*.10+off,w*.72,h*.66),1+i,(-2+i*1.5),shadow)
            add('active_object','object',_box(x+w*.16,y+h*.19,w*.64,h*.52),5,0,None)
        elif comp=='LAYERED_EDITORIAL':
            add('rear_plane','support',_box(x+w*.12,y+h*.02,w*.76,h*.82),1,1.1,None)
            add('mid_panel','panel',_box(x+w*.06,y+h*.08,w*.82,h*.78),2,-.8,shadow)
            add('object','object',_box(x+w*.17,y+h*.17,w*.64,h*.56),4,0,None)
            if cz:add('character_stage','support',_box(cz['x'],cz['y'],cz['w'],cz['h']),3,0,None)
        return L

    def _validate(self,req,sp,layers):
        warnings=[]; W,H=ASPECTS[req.aspect]
        # Text territory is sacred for all foreground object-bearing layers.
        for l in layers:
            if l.role in {'object','panel','document','card','product'} and _overlap(l.bbox,sp.text_zone)>0:
                warnings.append('FOREGROUND_INTRUDES_TEXT_ZONE:'+l.id)
            # outer crop is allowed only for explicitly cropped object
            canvas={'x':0,'y':0,'w':W,'h':H}
            if not _inside(l.bbox,canvas) and not l.crop:
                warnings.append('UNOWNED_OUTER_CROP:'+l.id)
            if l.crop and l.crop.get('outer_fraction',0)>self.outer_crop_max[req.aspect]+1e-6:
                warnings.append('OUTER_CROP_TOO_LARGE:'+l.id)
        # Depth hierarchy: no more than 5 foreground layers.
        foreground=[l for l in layers if l.z>=1]
        if len(foreground)>5:warnings.append('TOO_MANY_DEPTH_LAYERS')
        # Primary object must be materially visible.
        objs=[l for l in layers if l.role in {'object','product'}]
        if not objs:warnings.append('NO_PRIMARY_OBJECT')
        else:
            maxfrac=max(l.bbox['w']*l.bbox['h']/(W*H) for l in objs)
            if maxfrac<.07:warnings.append('PRIMARY_OBJECT_TOO_SMALL')
        return warnings

    def _transition_anchor(self,comp,req):
        return {
          'DOCUMENT_HERO':'document','STACKED_CARDS':'active_object','OFFSET_GRID_STAGE':'technical_panel',
          'LAYERED_EDITORIAL':'object','SPLIT_STAGE':'object','PRODUCT_PLINTH':'product',
          'EDGE_CROP_OBJECT':'object','RAIL_FRAME':'object','OPEN_FIELD':'object','FLOATING_PANEL':'panel'
        }[comp]

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--aspect',default='1x1');p.add_argument('--role',default='HYBRID');args=p.parse_args()
    req=SceneCompositionRequest(aspect=args.aspect,shot_role=args.role)
    print(json.dumps(asdict(EditorialSceneCompositionAuthorityV2().plan(req)),indent=2))
