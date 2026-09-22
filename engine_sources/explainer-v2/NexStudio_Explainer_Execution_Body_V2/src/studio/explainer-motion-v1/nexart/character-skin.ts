import type { NexArtSpecialistProposal, VisualConstructionPlan } from "../types";

export function buildCharacterSkinProposal(sceneId: string, construction: VisualConstructionPlan, entityIds: string[]): NexArtSpecialistProposal {
  return {
    role: "CHARACTER", sceneId,
    constructionThesis: "Bind authored illustrated character layers to NexStick V5.1 semantic performance; preserve expressive silhouette, face/hands and contacts while keeping the raw rig invisible.",
    requiredEntityIds: entityIds,
    sourceStrategies: ["COMPOSED_CANONICAL", "NEXSTICK_SKIN"],
    styleTraits: ["authored-illustrated-body", "expressive-silhouette", "face-and-hands-semantic", "single-illustrator-language"],
    interactionAnchors: [], unsupported: [],
    riskNotes: construction.dominanceMode === "diagram-led" ? ["Character use is supporting only; do not let a diagram layout become the visual world."] : [],
  };
}
