from __future__ import annotations
from typing import Any, Dict
import importlib, pathlib, sys

from . import editorial_scene_composition_authority_v2 as _COMP_V2

def _authentic_foundation(aspect,treatment,visual_kind):
    if _COMP_V2 is None: return None
    try:
        evidence=.90 if visual_kind in {'SCREENSHOT','DOCUMENT','CODE_WINDOW','EVIDENCE_CARD'} else 0.0
        technical=.78 if visual_kind in {'CODE_WINDOW','PROCESS_RAIL'} else .25
        obj_count=3 if visual_kind=='PROCESS_RAIL' else (1 if visual_kind!='NONE' else 0)
        req=_COMP_V2.SceneCompositionRequest(
            aspect=aspect,shot_role='TEXT_LED',text_load=.62,
            illustration_load=.62 if visual_kind!='NONE' else .12,
            character_present=visual_kind=='HUMAN',evidence_density=evidence,
            technical_density=technical,depth_need=.60,object_formality=.78,
            transition_energy=.62,object_count=obj_count,text_motif=None,object_dominance=.64)
        plan=_COMP_V2.EditorialSceneCompositionAuthorityV2().plan(req)
        from dataclasses import asdict
        return asdict(plan)
    except Exception as exc:
        return {'status':'ADAPTER_ERROR','error':type(exc).__name__+':'+str(exc)}

ASPECTS={
 '9x16':{'size':(720,1280),'safe':(52,72,616,1136),'hero_max_lines':4},
 '1x1': {'size':(1080,1080),'safe':(76,70,928,940),'hero_max_lines':3},
 '16x9':{'size':(1280,720),'safe':(72,54,1136,612),'hero_max_lines':3},
}

def _box(x,y,w,h): return {'x':int(x),'y':int(y),'w':int(w),'h':int(h)}

def _profile(text_zone, visual_zone, *, layout_family, hero_scale, evidence_scale=1.0,
             text_align='left', support_anchor='under_hero', visual_anchor='independent',
             field_use='balanced', max_lines=3):
    return {
        'text_zone':text_zone,'visual_zone':visual_zone,'layout_family':layout_family,
        'typography_hints':{
            'hero_scale':hero_scale,'text_align':text_align,'max_lines':max_lines,
            'support_anchor':support_anchor,
        },
        'visual_hints':{
            'evidence_scale':evidence_scale,'visual_anchor':visual_anchor,
            'field_use':field_use,
        }
    }

def _portrait(treatment,visual_kind):
    # Portrait remains stacked and vertical-first. V2 preserves the strengths of V1.
    m={
      'PROGRESSIVE_HERO_BUILD':_profile(_box(54,145,612,455),_box(88,690,544,370),layout_family='PORTRAIT_HERO_STACK',hero_scale=1.00,text_align='left',field_use='vertical_air',max_lines=4),
      'HERO_TO_EVIDENCE_HANDOFF':_profile(_box(54,96,612,312),_box(56,450,608,635),layout_family='PORTRAIT_CLAIM_OVER_EVIDENCE',hero_scale=.98,evidence_scale=1.03,field_use='stacked_proof',max_lines=3),
      'ANCHORED_SCREENSHOT_PROOF':_profile(_box(54,92,612,270),_box(54,402,612,676),layout_family='PORTRAIT_SCREEN_EVIDENCE',hero_scale=.98,evidence_scale=1.05,field_use='dominant_proof',max_lines=3),
      'PROCESS_RAIL':_profile(_box(54,92,612,300),_box(84,440,552,606),layout_family='PORTRAIT_PROCESS_STACK',hero_scale=.95,evidence_scale=1.02,field_use='vertical_process',max_lines=3),
      'CONTRAST_RECONFIGURATION':_profile(_box(54,126,612,420),_box(78,590,564,470),layout_family='PORTRAIT_CONTRAST_REFRAME',hero_scale=1.00,evidence_scale=1.0,field_use='stacked_reframe',max_lines=3),
      'PAYOFF_LOCKUP':_profile(_box(54,248,612,492),_box(140,820,440,250),layout_family='PORTRAIT_PAYOFF_LOCKUP',hero_scale=1.10,text_align='center',field_use='hero_dominant',max_lines=3),
      'CONTROLLED_EMPTY_SPACE':_profile(_box(54,270,612,470),_box(175,850,370,170),layout_family='PORTRAIT_QUIET_HERO',hero_scale=1.06,text_align='left',field_use='intentional_air',max_lines=4),
      'CTA_LOCKUP':_profile(_box(54,300,612,420),_box(110,810,500,250),layout_family='PORTRAIT_CTA_LOCKUP',hero_scale=1.04,text_align='center',field_use='hero_dominant',max_lines=3),
      # Product collage: centred lockup over a full-width object field; no side split.
      'COLLAGE_STAGE':_profile(_box(54,96,612,300),_box(40,440,640,720),layout_family='PORTRAIT_COLLAGE',hero_scale=1.02,evidence_scale=1.1,text_align='center',field_use='centred_collage',max_lines=3),
      'COLLAGE_LOCKUP':_profile(_box(54,300,612,520),_box(200,900,320,200),layout_family='PORTRAIT_COLLAGE_LOCKUP',hero_scale=1.12,text_align='center',field_use='hero_dominant',max_lines=4),
    }
    return m.get(treatment,m['PROGRESSIVE_HERO_BUILD'])

def _square(treatment,visual_kind):
    # Square uses a broad upper text field and a lower/offset support field. Not a portrait crop.
    m={
      'PROGRESSIVE_HERO_BUILD':_profile(_box(90,150,900,500),_box(660,610,330,310),layout_family='SQUARE_HERO_FIELD',hero_scale=1.05,text_align='left',field_use='broad_center',max_lines=3),
      'HERO_TO_EVIDENCE_HANDOFF':_profile(_box(84,80,790,300),_box(260,390,746,540),layout_family='SQUARE_OFFSET_EVIDENCE',hero_scale=1.00,evidence_scale=1.06,field_use='diagonal_proof',max_lines=3),
      'ANCHORED_SCREENSHOT_PROOF':_profile(_box(82,78,740,290),_box(300,365,700,555),layout_family='SQUARE_PROOF_STAGE',hero_scale=1.00,evidence_scale=1.08,field_use='dominant_proof',max_lines=3),
      'PROCESS_RAIL':_profile(_box(84,82,790,290),_box(120,395,840,470),layout_family='SQUARE_PROCESS_FIELD',hero_scale=.98,evidence_scale=1.04,field_use='wide_process',max_lines=3),
      'CONTRAST_RECONFIGURATION':_profile(_box(88,115,904,360),_box(120,475,840,430),layout_family='SQUARE_CONTRAST_FIELD',hero_scale=1.05,evidence_scale=1.02,field_use='split_reframe',max_lines=3),
      'PAYOFF_LOCKUP':_profile(_box(105,230,870,470),_box(655,720,260,170),layout_family='SQUARE_PAYOFF_LOCKUP',hero_scale=1.12,text_align='center',field_use='hero_dominant',max_lines=3),
      'CONTROLLED_EMPTY_SPACE':_profile(_box(110,250,860,430),_box(690,735,190,150),layout_family='SQUARE_QUIET_HERO',hero_scale=1.08,text_align='left',field_use='intentional_air',max_lines=3),
      'CTA_LOCKUP':_profile(_box(115,255,850,420),_box(660,705,240,175),layout_family='SQUARE_CTA_LOCKUP',hero_scale=1.07,text_align='center',field_use='hero_dominant',max_lines=3),
      'COLLAGE_STAGE':_profile(_box(84,80,912,260),_box(70,380,940,600),layout_family='SQUARE_COLLAGE',hero_scale=1.02,evidence_scale=1.1,text_align='center',field_use='centred_collage',max_lines=3),
      'COLLAGE_LOCKUP':_profile(_box(100,300,880,440),_box(760,760,220,160),layout_family='SQUARE_COLLAGE_LOCKUP',hero_scale=1.14,text_align='center',field_use='hero_dominant',max_lines=3),
    }
    return m.get(treatment,m['PROGRESSIVE_HERO_BUILD'])

def _landscape(treatment,visual_kind):
    # Landscape V2 is an independently authored horizontal field.
    # It deliberately uses wider/larger evidence surfaces and asymmetrical editorial staging.
    m={
      'PROGRESSIVE_HERO_BUILD':_profile(_box(82,88,1030,510),_box(930,120,250,430),layout_family='LANDSCAPE_HERO_BILLBOARD',hero_scale=1.22,text_align='left',field_use='wide_hero',max_lines=3),
      'HERO_TO_EVIDENCE_HANDOFF':_profile(_box(78,76,470,548),_box(575,70,625,570),layout_family='LANDSCAPE_EDITORIAL_SPLIT',hero_scale=1.20,evidence_scale=1.20,field_use='asymmetric_48_52',max_lines=3),
      'ANCHORED_SCREENSHOT_PROOF':_profile(_box(78,74,430,540),_box(535,62,670,586),layout_family='LANDSCAPE_PROOF_DOMINANT',hero_scale=1.18,evidence_scale=1.24,field_use='proof_dominant_40_60',max_lines=3),
      'PROCESS_RAIL':_profile(_box(78,80,430,530),_box(530,96,675,500),layout_family='LANDSCAPE_PROCESS_STAGE',hero_scale=1.16,evidence_scale=1.18,field_use='horizontal_process',max_lines=3),
      'CONTRAST_RECONFIGURATION':_profile(_box(78,76,500,550),_box(615,84,590,520),layout_family='LANDSCAPE_CONTRAST_SPLIT',hero_scale=1.20,evidence_scale=1.16,field_use='asymmetric_reframe',max_lines=3),
      'PAYOFF_LOCKUP':_profile(_box(92,120,1096,465),_box(930,520,240,92),layout_family='LANDSCAPE_PAYOFF_BILLBOARD',hero_scale=1.30,text_align='center',field_use='full_width_payoff',max_lines=2),
      'CONTROLLED_EMPTY_SPACE':_profile(_box(105,120,1060,450),_box(1000,520,150,80),layout_family='LANDSCAPE_QUIET_BILLBOARD',hero_scale=1.24,text_align='left',field_use='intentional_horizontal_air',max_lines=3),
      'CTA_LOCKUP':_profile(_box(110,128,1020,430),_box(980,490,170,100),layout_family='LANDSCAPE_CTA_BILLBOARD',hero_scale=1.22,text_align='center',field_use='full_width_cta',max_lines=2),
      'COLLAGE_STAGE':_profile(_box(110,62,988,200),_box(80,290,1120,376),layout_family='LANDSCAPE_COLLAGE',hero_scale=1.12,evidence_scale=1.15,text_align='center',field_use='centred_collage',max_lines=2),
      'COLLAGE_LOCKUP':_profile(_box(100,140,1008,420),_box(960,520,160,80),layout_family='LANDSCAPE_COLLAGE_LOCKUP',hero_scale=1.3,text_align='center',field_use='full_width_lockup',max_lines=3),
    }
    return m.get(treatment,m['PROGRESSIVE_HERO_BUILD'])

def compose(aspect:str,treatment:str,visual_kind:str)->Dict[str,Any]:
    a=ASPECTS[aspect]; W,H=a['size']
    p=_portrait(treatment,visual_kind) if aspect=='9x16' else (_square(treatment,visual_kind) if aspect=='1x1' else _landscape(treatment,visual_kind))
    # Typography-only beats keep treatment-specific visual staging metadata even when no donor visual is selected.
    # This matters for contrast/process-like programmatic editorial elements generated by the renderer itself.
    return {
        'aspect':aspect,'size':[W,H],'safe_area':list(a['safe']),'hero_max_lines':a['hero_max_lines'],
        'treatment':treatment,'text_zone':p['text_zone'],'visual_zone':p['visual_zone'],'visual_kind':visual_kind,
        'layout_family':p['layout_family'],'typography_hints':p['typography_hints'],'visual_hints':p['visual_hints'],
        'native_profile':True,'derived_by_scaling':False,'authority_version':'NATIVE_THREE_ASPECT_COMPOSITION_AUTHORITY_V2',
        'source_foundation':'EDITORIAL_SCENE_COMPOSITION_AUTHORITY_V2 + independently authored native aspect successor profiles V2',
        'authentic_v2_plan':_authentic_foundation(aspect,treatment,visual_kind),
    }
