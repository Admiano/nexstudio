import type { CommercialExecutionTier, NexArtSpecialistProposal, VisualConstructionPlan } from "../types";
import { authoredAssetRegistry, scoreAuthoredAsset } from "./asset-body";

export type ObjectPropCapabilityResult = { tier: CommercialExecutionTier; blockers:string[]; reasons:string[] };

function constructedGeometry(construction:VisualConstructionPlan, entityId:string) {
  const entity=[construction.heroEntity,...construction.supportingEntities].find((candidate)=>candidate.id===entityId);
  const state=construction.artDirection?.states?.find((candidate)=>candidate.id===construction.artDirection?.activeStateId);
  const geometry={...(entity?.geometry??{}),...(state?.entities?.[entityId]??{})};
  return { pathCount:geometry.paths?.length??0, itemCount:geometry.items?.length??0 };
}

export function assessObjectPropCapability(construction:VisualConstructionPlan):ObjectPropCapabilityResult {
  const objects=[construction.heroEntity,...construction.supportingEntities].filter((entity)=>entity.importance!=="annotation"&&(entity.type==="object"||entity.type==="container"||entity.visualClass==="transfer-object"||entity.visualClass==="document"||entity.visualClass==="attached-surface"));
  if(!objects.length)return {tier:"PREMIUM_NATIVE",blockers:[],reasons:["No literal object/prop construction demanded by this scene."]};
  const blockers:string[]=[]; const reasons:string[]=[];
  for(const entity of objects){
    const semantic=`${entity.semanticType} ${entity.label??""}`;
    if(entity.renderBinding){
      const asset=authoredAssetRegistry.find((candidate)=>candidate.assetId===entity.renderBinding?.assetId);
      const score=asset?scoreAuthoredAsset(asset,semantic):0;
      const floor=entity.importance==="hero"?6:3;
      if(score<floor)blockers.push(`PREMIUM_PROP_SEMANTIC_MATCH_INSUFFICIENT:${entity.id}:${score}<${floor}`);
      else reasons.push(`${entity.id}: authored asset match ${score}.`);
      continue;
    }
    const geometry=constructedGeometry(construction,entity.id);
    const authoredEnough=geometry.pathCount>=2||geometry.itemCount>=3;
    if(!authoredEnough)blockers.push(`PREMIUM_PROP_CONSTRUCTION_UNAVAILABLE:${entity.id}`);
    else reasons.push(`${entity.id}: multi-part constructed geometry.`);
  }
  return {tier:blockers.length?"UNAVAILABLE":"PREMIUM_COMPOSED",blockers,reasons};
}

export function buildObjectPropProposal(sceneId: string, entityIds: string[]): NexArtSpecialistProposal {
  return { role:"OBJECT_PROP", sceneId, constructionThesis:"Construct literal recognizable props with contact/affordance zones and inherit the scene style; generic icons may support but never replace required physical hero objects.", requiredEntityIds:entityIds, sourceStrategies:["COMPOSED_CANONICAL","APPROVED_ASSET"], styleTraits:["literal-recognizable-form","contact-aware","style-inherited"], interactionAnchors:[], unsupported:[], riskNotes:[] };
}
