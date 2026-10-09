import type { ProductionArtExecutionLayer, ProductionArtPlan, VisualConstructionPlan, VisualEntity } from "../types";

const STAGE_AREA = 900 * 560;
const PHYSICAL_RELATIONSHIPS = new Set(["passes-to", "attaches-to", "detaches-from", "enters", "exits", "travels-through", "orients-toward", "feeds", "routes-to"]);

function resolvedGeometry(construction: VisualConstructionPlan, entity: VisualEntity) {
  const state = construction.artDirection?.states?.find((candidate) => candidate.id === construction.artDirection?.activeStateId);
  return { ...(entity.geometry ?? {}), ...(state?.entities?.[entity.id] ?? {}) };
}

function entityArea(construction: VisualConstructionPlan, entity: VisualEntity): number {
  const geometry = resolvedGeometry(construction, entity);
  const scale = Math.max(.15, Number(geometry.scale ?? 1));
  if (Array.isArray(geometry.items) && geometry.items.length) {
    return geometry.items.reduce((sum, item) => sum + Math.max(20, Number(item.width ?? 80)) * Math.max(20, Number(item.height ?? 60)), 0);
  }
  const width = Number(geometry.width);
  const height = Number(geometry.height);
  if (Number.isFinite(width) && Number.isFinite(height) && width > 0 && height > 0) return width * height;
  if (entity.renderBinding?.kind === "ENVIRONMENT_SVG") return STAGE_AREA * .86;
  if (entity.renderBinding?.kind === "CHARACTER_SKIN") return 250 * 330 * scale * scale;
  if (entity.renderBinding) return 190 * 170 * scale * scale;
  if (geometry.paths?.length) return Math.min(STAGE_AREA * .18, geometry.paths.length * 105 * 95 * scale);
  return 0;
}

function executionLayerArea(layer:ProductionArtExecutionLayer){
  const width=Math.max(24,Number(layer.geometry.width??(layer.renderBinding.kind==="ENVIRONMENT_SVG"?900:190)));
  const height=Math.max(24,Number(layer.geometry.height??(layer.renderBinding.kind==="ENVIRONMENT_SVG"?560:170)));
  const scale=Math.max(.15,Number(layer.geometry.scale??1));
  return width*height*scale*scale;
}

function layerCount(construction: VisualConstructionPlan, plan:ProductionArtPlan) {
  const entities = [construction.heroEntity, ...construction.supportingEntities];
  let background = 0, middle = 0, foreground = 0;
  for (const entity of entities) {
    if (entity.type === "environment" || entity.visualClass === "environment" || entity.visualClass === "field") background += 1;
    else if (entity.importance === "annotation" || entity.type === "energy") foreground += 1;
    else middle += 1;
  }
  for(const layer of plan.executionLayers??[]){
    if(layer.role==="background")background+=1; else if(layer.role==="foreground")foreground+=1; else middle+=1;
  }
  return Number(background > 0) + Number(middle > 0) + Number(foreground > 0);
}

export function composeSceneRequirements(construction: VisualConstructionPlan, plan: ProductionArtPlan): ProductionArtPlan["sceneComposition"] {
  const authored = plan.visualMode === "AUTHORED_SCENE" || plan.visualMode === "HYBRID_ILLUSTRATION" || plan.visualMode === "WHITEBOARD_SCENE";
  const entities = [construction.heroEntity, ...construction.supportingEntities];
  // Foreground occupancy deliberately excludes full-frame environment substrates.
  // A single background illustration is not evidence of a richly authored scene.
  const foregroundEntityArea=entities.filter((entity)=>entity.type!=="environment"&&entity.visualClass!=="environment"&&entity.visualClass!=="field").reduce((sum,entity)=>sum+entityArea(construction,entity),0);
  const executionForegroundArea=(plan.executionLayers??[]).filter((layer)=>layer.role!=="background").reduce((sum,layer)=>sum+executionLayerArea(layer),0);
  const estimatedForegroundOccupancy = Math.min(.96, (foregroundEntityArea+executionForegroundArea) / STAGE_AREA * .78);
  const worldLayers = layerCount(construction,plan);
  const interactionPairCount = construction.relationships.filter((relationship) => PHYSICAL_RELATIONSHIPS.has(relationship.kind)).length;
  const interactionStagingRequired = plan.characterPerformanceRequired || interactionPairCount > 0;
  const compositionBlockers: string[] = [];

  if (authored) {
    const semanticEntityCount = entities.filter((entity) => {
      const geometry = resolvedGeometry(construction, entity);
      return entity.renderBinding || geometry.paths?.length || geometry.items?.length;
    }).length;
    const bodyLayerCount=(plan.executionLayers??[]).length;
    const meaningfulEntityCount=semanticEntityCount+bodyLayerCount;
    if (meaningfulEntityCount < 3) compositionBlockers.push(`SCENE_COMPOSER_UNDERAUTHORED:${meaningfulEntityCount}<3`);
    if (estimatedForegroundOccupancy < plan.minimumForegroundOccupancy) {
      compositionBlockers.push(`SCENE_COMPOSER_LOW_FOREGROUND_OCCUPANCY:${estimatedForegroundOccupancy.toFixed(3)}<${plan.minimumForegroundOccupancy.toFixed(3)}`);
    }
    if (plan.densityTarget === "rich" && meaningfulEntityCount < 5) compositionBlockers.push(`SCENE_COMPOSER_RICH_DENSITY_REQUIRES_5_ELEMENTS:${meaningfulEntityCount}`);
    if(plan.environmentRequired&&worldLayers<3)compositionBlockers.push(`SCENE_COMPOSER_ENVIRONMENT_REQUIRES_3_DEPTH_LAYERS:${worldLayers}`);
    if (interactionStagingRequired && interactionPairCount === 0 && plan.specialistRoles.includes("INTERACTION_POSE")) {
      compositionBlockers.push("SCENE_COMPOSER_INTERACTION_RELATIONSHIP_MISSING");
    }
    if (plan.environmentRequired && !plan.referenceLanguage?.whiteField && !entities.some((entity) => entity.type === "environment" || entity.visualClass === "environment") && !(plan.executionLayers??[]).some((layer)=>layer.role==="background"&&layer.renderBinding.kind==="ENVIRONMENT_SVG")) {
      compositionBlockers.push("SCENE_COMPOSER_ENVIRONMENT_LAYER_MISSING");
    }
  }

  return {
    foregroundRequired: authored,
    midgroundRequired: authored,
    backgroundRequired: authored && plan.environmentRequired && !Boolean(plan.referenceLanguage?.whiteField),
    interactionStagingRequired,
    negativeSpaceIntent: authored ? "Reserve negative space only where it strengthens hierarchy; do not leave unexplained dead canvas." : (construction.artDirectionPlan?.negativeSpace.intent ?? "breathing-room"),
    estimatedForegroundOccupancy: Number(estimatedForegroundOccupancy.toFixed(4)),
    worldLayerCount: worldLayers,
    interactionPairCount,
    compositionBlockers,
  };
}
