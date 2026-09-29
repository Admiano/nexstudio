import type { NexArtSpecialistProposal } from "../types";
export function buildWhiteboardProposal(sceneId: string, entityIds: string[]): NexArtSpecialistProposal {
  return { role:"WHITEBOARD", sceneId, constructionThesis:"Construct one coherent authored line-art scene with semantic stroke order, pen lifts, occlusion-aware drawing and marker contact bound to the actual path geometry.", requiredEntityIds:entityIds, sourceStrategies:["COMPOSED_CANONICAL"], styleTraits:["authored-line-art","draw-order-aware","human-marker-contact"], interactionAnchors:[], unsupported:[], riskNotes:[] };
}
