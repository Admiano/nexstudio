from __future__ import annotations
from typing import Dict, Any, List
from .scene_intelligence_schema import *

class SemanticBeatError(ValueError): pass

def _f(v, lo=0.0, hi=1.0):
    try: return max(lo,min(hi,float(v)))
    except Exception: return 0.0

def normalize_beat(raw: Dict[str,Any]) -> SemanticBeat:
    '''
    Production seam: accepts semantic analysis from NexMind upstream.
    Subject/content labels are retained as payload only. Representation/layout code
    consumes entity kinds, relations and continuous abstract features.
    '''
    if not isinstance(raw,dict): raise SemanticBeatError('BEAT_MUST_BE_OBJECT')
    beat_id=str(raw.get('beat_id') or '').strip()
    if not beat_id: raise SemanticBeatError('BEAT_ID_REQUIRED')
    ents=[]
    for e in raw.get('entities') or []:
        if not e.get('id') or not e.get('kind'): raise SemanticBeatError('ENTITY_ID_KIND_REQUIRED')
        ents.append(SemanticEntity(
            id=str(e['id']), kind=e['kind'], label=str(e.get('label') or ''),
            importance=_f(e.get('importance',.5)), agency=_f(e.get('agency',0)),
            mobility=_f(e.get('mobility',0)), physicality=_f(e.get('physicality',.5))))
    if not ents: raise SemanticBeatError('ENTITIES_REQUIRED')
    ids={e.id for e in ents}
    rels=[]
    for r in raw.get('relations') or []:
        typ=str(r.get('type') or '')
        if typ not in ALLOWED_RELATIONS: raise SemanticBeatError(f'UNSUPPORTED_RELATION:{typ}')
        if r.get('source') not in ids or r.get('target') not in ids:
            raise SemanticBeatError('RELATION_ENDPOINT_MISSING')
        rels.append(SemanticRelation(typ,str(r['source']),str(r['target']),_f(r.get('strength',1)),_f(r.get('directionality',1))))
    f=raw.get('features') or {}
    features=BeatFeatures(
        human_agency=_f(f.get('human_agency',0)), emotional_intensity=_f(f.get('emotional_intensity',0)),
        emotional_valence=max(-1,min(1,float(f.get('emotional_valence',0) or 0))),
        relational_density=_f(f.get('relational_density', min(1,len(rels)/max(1,len(ents))))),
        transformation_degree=_f(f.get('transformation_degree',0)), comparison_degree=_f(f.get('comparison_degree',0)),
        spatiality=_f(f.get('spatiality',0)), physicality=_f(f.get('physicality',0)),
        evidence_density=_f(f.get('evidence_density',0)), uncertainty=_f(f.get('uncertainty',0)),
        sociality=_f(f.get('sociality',0)), causality=_f(f.get('causality',0)),
        continuity_required=_f(f.get('continuity_required',0)))
    return SemanticBeat(beat_id, str(raw.get('text') or ''), ents, rels, features,
                        raw.get('protagonist_id'), raw.get('explicit_representation'))
