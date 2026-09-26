import type { CommercialExecutionTier, NexArtSpecialistProposal, ProductionArtPlan, ProductionArtSystem, ReferenceLanguageProfile, VisualConstructionPlan } from "../types";
import { composeSceneRequirements } from "./scene-composer";
import { dispatchSpecialistArtists, requiredSpecialistRoles } from "./specialist-artists";
import { resolveStyleSignature, styleGrammarBlockers } from "./style-grammar";
import { authoredBindingBlockers, bindEntityToAuthoredBody } from "./asset-body";
import { constructEnvironmentBody } from "./environment-constructor";
import { assessObjectPropCapability } from "./object-prop-constructor";

function visualMode(construction: VisualConstructionPlan, reference?: ReferenceLanguageProfile): ProductionArtPlan["visualMode"] {
  if ((reference?.authoredSceneBias ?? 0) >= .6 && construction.dominanceMode !== "media-led") return "AUTHORED_SCENE";
  if (construction.dominanceMode === "diagram-led" || construction.dominanceMode === "data-led" || construction.dominanceMode === "workflow-led") return "DIAGRAM";
  if (construction.dominanceMode === "media-led") return "MEDIA";
  if (construction.dominanceMode === "hybrid") return "HYBRID_ILLUSTRATION";
  return "AUTHORED_SCENE";
}


function productionScopedAuthoredPlan(construction: VisualConstructionPlan, referenceLanguage?: ReferenceLanguageProfile): ProductionArtPlan | undefined {
  const plate=construction.productionScopedArt;
  if(!plate)return undefined;
  if(plate.schema!=="NexStudioAuthoredScenePlateBindingV1"||plate.creativeChoiceIntroduced!==false)throw new Error(`PRODUCTION_SCOPED_ART_CONTRACT_INVALID:${construction.sceneId}`);
  if(!plate.finalPngDataUrl.startsWith("data:image/png;base64,"))throw new Error(`PRODUCTION_SCOPED_ART_PIXELS_INVALID:${construction.sceneId}`);
  const required=[construction.heroEntity.semanticType,...construction.supportingEntities.map((entity)=>entity.semanticType)].filter(Boolean).map((x)=>String(x).toLowerCase());
  const bound=new Set((plate.semanticBindings||[]).map((item)=>String(item.semantic_ref||"").trim().toLowerCase()).filter(Boolean));
  const missing=required.filter((semantic)=>!bound.has(semantic));
  if(missing.length)throw new Error(`PRODUCTION_SCOPED_ART_SEMANTICS_MISSING:${construction.sceneId}:${missing.join("|")}`);
  const embedded=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 560" preserveAspectRatio="xMidYMid meet"><image href="${plate.finalPngDataUrl}" x="0" y="0" width="900" height="560" preserveAspectRatio="xMidYMid meet"/></svg>`;
  const binding={kind:"AUTHORED_SVG" as const,assetId:`production-scoped-authored-art:${construction.sceneId}`,sourcePath:"inline:production-scoped-authored-art-v1",license:"INTERNAL" as const,family:"nexstudio-production-scoped-authored-art-v1",normalizedStyleFamily:"nexstudio-authored-cartoon-v1" as const,semanticTags:[...required,"production-scoped","p8-locked"],inlineSvg:embedded};
  const layer={id:`${construction.sceneId}:body:authored-scene`,role:"background" as const,semanticPurpose:"production-scoped-authored-scene",source:"PRODUCTION_SCOPED_AUTHORED_ART" as const,commercialTier:"PREMIUM_COMPOSED" as const,geometry:{x:450,y:280,width:900,height:560,opacity:1},renderBinding:binding};
  return {
    version:"production-art.v2",sceneId:construction.sceneId,visualMode:"AUTHORED_SCENE",requiredSystems:["SCENE_COMPOSER","STYLE_GRAMMAR","EXECUTION_FIDELITY_CHECK"],specialistRoles:[],specialistProposals:[],
    characterPerformanceRequired:false,environmentRequired:true,objectConstructionRequired:true,coherentWorldRequired:true,diagramFallbackAllowed:false,rawRigVisibleAllowed:false,textMustBeSubordinate:true,
    ...(referenceLanguage?{referenceLanguage}:{}),densityTarget:referenceLanguage?.densityTarget??"rich",minimumForegroundOccupancy:referenceLanguage?.minimumForegroundOccupancy??.34,maximumDeadWhiteRatio:referenceLanguage?.maximumDeadWhiteRatio??.38,
    styleSignature:["p8-locked","production-scoped-authored-art"],executionLayers:[layer],productionScopedAuthoredPlate:{lockedSemanticsHash:plate.lockedSemanticsHash,semanticBindings:plate.semanticBindings,stageCount:plate.stageCount},
    commercialCapability:{character:"PREMIUM_COMPOSED",environment:"PREMIUM_COMPOSED",objectProp:"PREMIUM_COMPOSED",reasons:["Production-scoped authored scene plate validated against P8 locked semantics. Pixel fidelity remains subject to the independent authored-art execution-fidelity reviewer; commercial judgment is post-render Final Producer + independent perceptual auditor."],replanRequired:false},
    sceneComposition:{foregroundRequired:true,midgroundRequired:true,backgroundRequired:true,interactionStagingRequired:false,negativeSpaceIntent:"P8_AUTHORED",estimatedForegroundOccupancy:.9,worldLayerCount:3,interactionPairCount:0,compositionBlockers:[]},
    motionAuthority:"NEXMIND_MOTION_DIRECTOR",releaseGate:"EXECUTION_FIDELITY_REQUIRED",status:"READY_FOR_RENDER",blockers:[]
  };
}

function characterCommercialTier(construction:VisualConstructionPlan, characterRequired:boolean):{tier:CommercialExecutionTier;reasons:string[];blockers:string[]} {
  if(!characterRequired)return {tier:"PREMIUM_NATIVE",reasons:["No character performance required by the committed scene."],blockers:[]};
  const characters=[construction.heroEntity,...construction.supportingEntities].filter((entity)=>entity.renderBinding?.kind==="CHARACTER_SKIN");
  const premium=characters.length>0&&characters.every((entity)=>entity.renderBinding?.family==="nexstudio-rive-premium-v1");
  if(premium)return {tier:"PREMIUM_NATIVE",reasons:["Approved animation-native premium character master bound."],blockers:[]};
  return {tier:"UNAVAILABLE",reasons:["Current NexStick authored-surface character body remains performance-support infrastructure, not the approved premium animation-native character master."],blockers:["PREMIUM_CHARACTER_MASTER_UNAVAILABLE"]};
}

export function buildProductionArtPlan(input: { construction: VisualConstructionPlan; referenceLanguage?: ReferenceLanguageProfile; approvedAssets?: boolean; whiteboard?: boolean; specialistProposals?: readonly NexArtSpecialistProposal[] }): ProductionArtPlan {
  const { construction, referenceLanguage } = input;
  const productionScoped=productionScopedAuthoredPlan(construction,referenceLanguage);
  if(productionScoped)return productionScoped;
  const mode = input.whiteboard ? "WHITEBOARD_SCENE" : visualMode(construction, referenceLanguage);
  const specialistRoles = requiredSpecialistRoles(construction, { whiteboard: input.whiteboard, approvedAssets: input.approvedAssets });
  const specialistProposals: NexArtSpecialistProposal[] = input.specialistProposals ? [...input.specialistProposals] : dispatchSpecialistArtists(construction, specialistRoles);
  const proposalRoles = new Set(specialistProposals.map((proposal) => proposal.role));
  for (const role of specialistRoles) if (!proposalRoles.has(role)) throw new Error(`NEXART_SPECIALIST_PROPOSAL_MISSING:${construction.sceneId}:${role}`);
  const requiredSystems = new Set<ProductionArtSystem>(["SCENE_COMPOSER","STYLE_GRAMMAR","EXECUTION_FIDELITY_CHECK"]);
  if (specialistRoles.includes("CHARACTER")) requiredSystems.add("CHARACTER_SKIN");
  if (specialistRoles.includes("WHITEBOARD")) requiredSystems.add("WHITEBOARD_DRAWING");
  if (specialistRoles.includes("ENVIRONMENT_SCENE")) requiredSystems.add("ENVIRONMENT_CONSTRUCTOR");
  if (specialistRoles.includes("OBJECT_PROP")) requiredSystems.add("OBJECT_PROP_CONSTRUCTOR");
  const authored = mode === "AUTHORED_SCENE" || mode === "HYBRID_ILLUSTRATION" || mode === "WHITEBOARD_SCENE";
  const blockers: string[] = [];
  if (construction.visualCoverage === "VISUAL_COVERAGE_GAP") blockers.push("VISUAL_COVERAGE_GAP");
  blockers.push(...authoredBindingBlockers(construction, authored));
  blockers.push(...styleGrammarBlockers(construction, authored));
  for (const proposal of specialistProposals) for (const reason of proposal.unsupported) blockers.push(`${proposal.role}:${reason}`);
  if (authored && specialistRoles.includes("DIAGRAM") && !specialistRoles.some((role) => role === "ENVIRONMENT_SCENE" || role === "CHARACTER" || role === "OBJECT_PROP")) blockers.push("AUTHORED_SCENE_CANNOT_RESOLVE_TO_DIAGRAM_ONLY");

  const environmentRequired=authored&&!Boolean(referenceLanguage?.whiteField);
  const environment=environmentRequired?constructEnvironmentBody(construction,referenceLanguage):{strategy:"INTENTIONAL_WHITE_FIELD" as const,layers:[],contextualPropCount:0,depthLayerCount:2,semanticBasis:"not-required",blockers:[]};
  const objectProp=assessObjectPropCapability(construction);
  const character=characterCommercialTier(construction,specialistRoles.includes("CHARACTER")||specialistRoles.includes("INTERACTION_POSE"));
  if(environmentRequired)blockers.push(...environment.blockers);
  if(authored||specialistRoles.includes("OBJECT_PROP"))blockers.push(...objectProp.blockers);
  blockers.push(...character.blockers);
  const commercialCapability={
    character:character.tier,
    environment:(environmentRequired?(environment.blockers.length?"UNAVAILABLE":"PREMIUM_COMPOSED"):"PREMIUM_NATIVE") as CommercialExecutionTier,
    objectProp:objectProp.tier,
    reasons:[...character.reasons,`Environment strategy: ${environment.strategy}; contextual props: ${environment.contextualPropCount}; depth layers: ${environment.depthLayerCount}.`,...objectProp.reasons],
    replanRequired:false,
  };
  commercialCapability.replanRequired=blockers.some((reason)=>reason.startsWith("PREMIUM_"));
  const plan: ProductionArtPlan = {
    version:"production-art.v2", sceneId:construction.sceneId, visualMode:mode,
    requiredSystems:[...requiredSystems], specialistRoles, specialistProposals,
    characterPerformanceRequired:specialistRoles.includes("CHARACTER") || specialistRoles.includes("INTERACTION_POSE"),
    environmentRequired,
    objectConstructionRequired:authored || specialistRoles.includes("OBJECT_PROP"),
    coherentWorldRequired:authored,
    diagramFallbackAllowed:mode === "DIAGRAM",
    rawRigVisibleAllowed:false,
    textMustBeSubordinate:authored,
    ...(referenceLanguage ? { referenceLanguage } : {}),
    densityTarget: referenceLanguage?.densityTarget ?? (construction.artDirectionPlan?.qualityIntent.density === "rich" ? "rich" : construction.artDirectionPlan?.qualityIntent.density === "sparse" ? "sparse" : "balanced"),
    minimumForegroundOccupancy: referenceLanguage?.minimumForegroundOccupancy ?? (authored ? (construction.artDirectionPlan?.qualityIntent.density === "rich" ? .32 : construction.artDirectionPlan?.qualityIntent.density === "sparse" ? .18 : .24) : .1),
    maximumDeadWhiteRatio: referenceLanguage?.maximumDeadWhiteRatio ?? (authored ? (construction.artDirectionPlan?.qualityIntent.density === "rich" ? .40 : .52) : .72),
    styleSignature:resolveStyleSignature(construction,referenceLanguage),
    executionLayers:environment.layers,
    commercialCapability,
    sceneComposition: { foregroundRequired:false, midgroundRequired:false, backgroundRequired:false, interactionStagingRequired:false, negativeSpaceIntent:"", estimatedForegroundOccupancy:0, worldLayerCount:0, interactionPairCount:0, compositionBlockers:[] },
    motionAuthority:"NEXMIND_MOTION_DIRECTOR",
    ...(specialistRoles.includes("CHARACTER") || specialistRoles.includes("INTERACTION_POSE") ? { characterMotionAuthority:"NEXSTICK_V5_1" as const } : {}),
    releaseGate:"EXECUTION_FIDELITY_REQUIRED",
    status:blockers.length ? "BLOCKED" : "READY_FOR_RENDER",
    blockers,
  };
  plan.sceneComposition = composeSceneRequirements(construction, plan);
  plan.blockers.push(...plan.sceneComposition.compositionBlockers);
  plan.blockers = [...new Set(plan.blockers)];
  plan.status = plan.blockers.length ? "BLOCKED" : "READY_FOR_RENDER";
  return plan;
}

export function attachProductionArtPlans(constructions: readonly VisualConstructionPlan[], input?: { referenceLanguage?: ReferenceLanguageProfile; approvedAssets?: boolean; whiteboard?: boolean; specialistProposals?: readonly NexArtSpecialistProposal[] }): VisualConstructionPlan[] {
  return constructions.map((construction) => {
    const provisionalMode = input?.whiteboard ? "WHITEBOARD_SCENE" : visualMode(construction, input?.referenceLanguage);
    const authored = provisionalMode === "AUTHORED_SCENE" || provisionalMode === "HYBRID_ILLUSTRATION" || provisionalMode === "WHITEBOARD_SCENE";
    const bound: VisualConstructionPlan = {
      ...construction,
      heroEntity: bindEntityToAuthoredBody(construction.heroEntity, { sceneId:construction.sceneId, referenceLanguage:input?.referenceLanguage, authored }),
      supportingEntities: construction.supportingEntities.map((entity) => bindEntityToAuthoredBody(entity, { sceneId:construction.sceneId, referenceLanguage:input?.referenceLanguage, authored })),
    };
    const proposals = input?.specialistProposals?.filter((proposal) => proposal.sceneId === construction.sceneId);
    return { ...bound, productionArt: buildProductionArtPlan({ construction:bound, referenceLanguage:input?.referenceLanguage, approvedAssets:input?.approvedAssets, whiteboard:input?.whiteboard, specialistProposals:proposals?.length ? proposals : undefined }) };
  });
}
