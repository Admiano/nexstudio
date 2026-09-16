from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal

Representation = Literal[
    'character_led','character_object','object_led','relationship_led',
    'spatial_contrast','state_transformation','typography_led','data_in_context'
]

ALLOWED_RELATIONS = {
    'looks_at','gestures_to','holds','acts_on','moves_toward','moves_away_from',
    'blocks','contains','supports','rests_on','surrounds','reveals','transforms',
    'produces','receives','hands_to','compares','connects_to','depends_on',
    'causes','resolves_to','before','after','part_of','inside','behind','in_front_of'
}

@dataclass
class SemanticEntity:
    id: str
    kind: Literal['person','object','place','system','state','result','evidence','text']
    label: str = ''            # payload only; never a representation/layout routing feature
    importance: float = 0.5
    agency: float = 0.0
    mobility: float = 0.0
    physicality: float = 0.5

@dataclass
class SemanticRelation:
    type: str
    source: str
    target: str
    strength: float = 1.0
    directionality: float = 1.0

@dataclass
class BeatFeatures:
    human_agency: float = 0.0
    emotional_intensity: float = 0.0
    emotional_valence: float = 0.0      # -1..1
    relational_density: float = 0.0
    transformation_degree: float = 0.0
    comparison_degree: float = 0.0
    spatiality: float = 0.0
    physicality: float = 0.0
    evidence_density: float = 0.0
    uncertainty: float = 0.0
    sociality: float = 0.0
    causality: float = 0.0
    continuity_required: float = 0.0

@dataclass
class SemanticBeat:
    beat_id: str
    text: str
    entities: List[SemanticEntity]
    relations: List[SemanticRelation]
    features: BeatFeatures
    protagonist_id: str | None = None
    explicit_representation: str | None = None

@dataclass
class RepresentationDecision:
    selected: Representation
    scores: Dict[str,float]
    reasons: List[str]
    fallback_order: List[str]

@dataclass
class SceneNode:
    id: str
    kind: str
    semantic_id: str
    hierarchy: Literal['hero','support','micro']
    x: float
    y: float
    w: float
    h: float
    facing: Literal['left','right','front','neutral'] = 'neutral'
    layer: Literal['foreground','midground','background'] = 'midground'
    allow_overlap_with: List[str] = field(default_factory=list)

@dataclass
class SceneConstraint:
    type: str
    source: str
    target: str | None = None
    params: Dict[str,Any] = field(default_factory=dict)

@dataclass
class ScenePlan:
    beat_id: str
    aspect: str
    representation: Representation
    nodes: List[SceneNode]
    constraints: List[SceneConstraint]
    motion_intent: Dict[str,Any]
    composition_metrics: Dict[str,float]
    payload_labels: Dict[str,str]

@dataclass
class QAResult:
    status: Literal['PASS','REPLAN','FAIL']
    score: float
    failures: List[Dict[str,Any]]
    warnings: List[Dict[str,Any]]
    metrics: Dict[str,float]

def clamp01(x: float) -> float:
    return max(0.0,min(1.0,float(x)))

def serial(obj: Any) -> Any:
    if hasattr(obj,'__dataclass_fields__'):
        return {k:serial(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [serial(x) for x in obj]
    if isinstance(obj,dict): return {k:serial(v) for k,v in obj.items()}
    return obj
