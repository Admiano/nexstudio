import type { NexArtSpecialistProposal, ProductionArtExecutionLayer, ReferenceLanguageProfile, VisualConstructionPlan } from "../types";

export type EnvironmentConstructionResult = {
  strategy: "INTENTIONAL_WHITE_FIELD" | "EXPLICIT_AUTHORED_WORLD" | "UNAVAILABLE";
  layers: ProductionArtExecutionLayer[];
  contextualPropCount: number;
  depthLayerCount: number;
  semanticBasis: string;
  blockers: string[];
};

/** Execution-only environment binding. This body never invents a world category from prose. */
export function constructEnvironmentBody(construction: VisualConstructionPlan, reference?: ReferenceLanguageProfile): EnvironmentConstructionResult {
  if(reference?.whiteField) return {strategy:"INTENTIONAL_WHITE_FIELD",layers:[],contextualPropCount:0,depthLayerCount:2,semanticBasis:"p8-explicit-white-field",blockers:[]};
  const entities=[construction.heroEntity,...construction.supportingEntities];
  const explicit=entities.find((e)=>e.type==="environment"||e.visualClass==="environment");
  if(explicit?.renderBinding?.kind==="ENVIRONMENT_SVG"){
    return {strategy:"EXPLICIT_AUTHORED_WORLD",layers:[{id:`${construction.sceneId}:body:environment`,role:"background",semanticPurpose:explicit.semanticType,source:"APPROVED_ASSET",commercialTier:"PREMIUM_COMPOSED",geometry:{x:450,y:280,width:900,height:560,opacity:1},renderBinding:explicit.renderBinding}],contextualPropCount:0,depthLayerCount:3,semanticBasis:`explicit:${explicit.id}:${explicit.semanticType}`,blockers:[]};
  }
  return {strategy:"UNAVAILABLE",layers:[],contextualPropCount:0,depthLayerCount:0,semanticBasis:"no-explicit-authored-environment",blockers:[`PRODUCTION_SCOPED_AUTHORED_ENVIRONMENT_REQUIRED:${construction.sceneId}`]};
}

export function buildEnvironmentProposal(sceneId:string,entityIds:string[]):NexArtSpecialistProposal{
  return {role:"ENVIRONMENT_SCENE",sceneId,constructionThesis:"Execute the P8-authored environment/world exactly. If no production-scoped authored world or explicit approved environment binding exists, fail/replan rather than infer an archetype from prose.",requiredEntityIds:entityIds,sourceStrategies:["PRODUCTION_SCOPED_AUTHORED_ART","APPROVED_ASSET"],styleTraits:["p8-authored","world-specific","no-house-archetype"],interactionAnchors:[],unsupported:[],riskNotes:[]};
}
