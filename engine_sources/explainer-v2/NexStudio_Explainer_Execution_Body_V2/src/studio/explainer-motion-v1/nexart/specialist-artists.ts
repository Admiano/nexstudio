import type { NexArtSpecialistProposal, NexArtSpecialistRole, ReferenceLanguageProfile, VisualConstructionPlan } from "../types";
import { buildCharacterSkinProposal } from "./character-skin";
import { buildEnvironmentProposal } from "./environment-constructor";
import { buildObjectPropProposal } from "./object-prop-constructor";
import { buildWhiteboardProposal } from "./whiteboard-drawing";

const HUMAN_ROLE = /(?:person|people|human|worker|staff|team|volunteer|customer|parent|child|student|teacher|doctor|nurse|manager|operator|creator|driver|courier|presenter|character|woman|man|girl|boy|adult)/i;
const physicalRelationship = new Set(["passes-to","attaches-to","detaches-from","enters","exits","travels-through","orients-toward"]);

export function requiredSpecialistRoles(construction: VisualConstructionPlan, options?: { whiteboard?: boolean; approvedAssets?: boolean }): NexArtSpecialistRole[] {
  const entities = [construction.heroEntity, ...construction.supportingEntities];
  const roles = new Set<NexArtSpecialistRole>();
  const authored = construction.dominanceMode === "illustration-led" || construction.dominanceMode === "hybrid";
  const hasCharacter = entities.some((entity) => entity.visualClass === "illustration" && HUMAN_ROLE.test(`${entity.semanticType} ${entity.label ?? ""}`));
  if (hasCharacter) roles.add("CHARACTER");
  if (options?.whiteboard) roles.add("WHITEBOARD");
  if (authored || entities.some((entity) => entity.type === "environment" || entity.visualClass === "environment")) roles.add("ENVIRONMENT_SCENE");
  if (authored || entities.some((entity) => entity.type === "object" || entity.visualClass === "transfer-object" || entity.importance === "hero")) roles.add("OBJECT_PROP");
  if (construction.dominanceMode === "diagram-led" || construction.dominanceMode === "data-led" || construction.dominanceMode === "workflow-led") roles.add("DIAGRAM");
  if (construction.relationships.some((relationship) => physicalRelationship.has(relationship.kind))) roles.add("INTERACTION_POSE");
  if (options?.approvedAssets || construction.coverageDecision === "user-media") roles.add("ASSET_ASSIMILATION");
  return [...roles];
}

export function dispatchSpecialistArtists(construction: VisualConstructionPlan, roles: readonly NexArtSpecialistRole[]): NexArtSpecialistProposal[] {
  const entities = [construction.heroEntity, ...construction.supportingEntities];
  const allIds = entities.map((entity) => entity.id);
  const humanIds = entities.filter((entity) => entity.visualClass === "illustration" && HUMAN_ROLE.test(`${entity.semanticType} ${entity.label ?? ""}`)).map((entity) => entity.id);
  const environmentIds = entities.filter((entity) => entity.type === "environment" || entity.visualClass === "environment").map((entity) => entity.id);
  const objectIds = entities.filter((entity) => entity.type === "object" || entity.visualClass === "transfer-object" || entity.importance === "hero").map((entity) => entity.id);
  return roles.map((role): NexArtSpecialistProposal => {
    if (role === "CHARACTER") return buildCharacterSkinProposal(construction.sceneId, construction, humanIds.length ? humanIds : [construction.heroEntity.id]);
    if (role === "WHITEBOARD") return buildWhiteboardProposal(construction.sceneId, allIds);
    if (role === "ENVIRONMENT_SCENE") return buildEnvironmentProposal(construction.sceneId, environmentIds.length ? environmentIds : allIds);
    if (role === "OBJECT_PROP") return buildObjectPropProposal(construction.sceneId, objectIds.length ? objectIds : [construction.heroEntity.id]);
    if (role === "DIAGRAM") return { role, sceneId:construction.sceneId, constructionThesis:"Use semantic diagram grammar only when abstraction is the approved visual thesis; diagram primitives may not masquerade as an authored physical scene.", requiredEntityIds:allIds, sourceStrategies:["PROCEDURAL_DIAGRAM"], styleTraits:["semantic-structure","minimal-connectors"], interactionAnchors:[], unsupported:[], riskNotes:[] };
    if (role === "INTERACTION_POSE") return { role, sceneId:construction.sceneId, constructionThesis:"Stage explicit contact, gaze, grip, seat and ownership relationships before motion; preserve physical cause and effect.", requiredEntityIds:allIds, sourceStrategies:["NEXSTICK_SKIN","COMPOSED_CANONICAL"], styleTraits:["contact-aware","causal-performance"], interactionAnchors:construction.relationships.filter((relationship)=>physicalRelationship.has(relationship.kind)).map((relationship)=>({actor:relationship.from,anchor:"SEMANTIC_CONTACT",target:relationship.to,ownershipRule:`${relationship.kind}: preserve ownership through contact`})), unsupported:[], riskNotes:[] };
    return { role, sceneId:construction.sceneId, constructionThesis:"Assimilate approved user/source assets without changing source identity; preserve provenance and visual semantics.", requiredEntityIds:allIds, sourceStrategies:["USER_ASSET","VECTOR_TRACE"], styleTraits:["identity-preserving","provenance-bound"], interactionAnchors:[], unsupported:[], riskNotes:[] };
  });
}
