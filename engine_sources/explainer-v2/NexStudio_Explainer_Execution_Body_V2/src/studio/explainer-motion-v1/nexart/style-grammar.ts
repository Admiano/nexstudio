import type { ReferenceLanguageProfile, VisualConstructionPlan } from "../types";

export const AUTHORED_STYLE_FAMILY = "nexstudio-authored-cartoon-v1" as const;

export function resolveStyleSignature(construction: VisualConstructionPlan, reference?: ReferenceLanguageProfile) {
  const signature: string[] = [
    AUTHORED_STYLE_FAMILY,
    construction.styleProfile.primaryVisualLanguage,
    construction.styleProfile.secondaryVisualLanguage,
    construction.styleProfile.strokeStyle,
    construction.styleProfile.depth,
    construction.styleProfile.shapeStyle,
  ];
  if (reference?.whiteField) signature.push("active-white-field");
  if (reference?.densityTarget === "rich") signature.push("authored-rich-density");
  if ((reference?.authoredSceneBias ?? 0) >= .6) signature.push("cartoon-scene-over-presentation-layout");
  return [...new Set(signature)];
}

/**
 * Shared Style Grammar is a production gate, not metadata. Third-party donor
 * identity is retained for provenance, but every authored binding must declare
 * the same normalized NexStudio style family before it can reach rendering.
 * Procedural paths/items are produced by the canonical runtime and therefore
 * already belong to that family.
 */
export function styleGrammarBlockers(construction: VisualConstructionPlan, authored: boolean): string[] {
  if (!authored) return [];
  const blockers: string[] = [];
  const entities = [construction.heroEntity, ...construction.supportingEntities];
  const bound = entities.filter((entity) => entity.renderBinding);
  for (const entity of bound) {
    const binding = entity.renderBinding!;
    if (binding.normalizedStyleFamily !== AUTHORED_STYLE_FAMILY) {
      blockers.push(`STYLE_FAMILY_NOT_NORMALIZED:${entity.id}:${binding.family}`);
    }
    if (binding.kind === "CHARACTER_SKIN" && binding.performanceAuthority !== "NEXSTICK_V5_1") {
      blockers.push(`CHARACTER_STYLE_MOTION_AUTHORITY_MISSING:${entity.id}`);
    }
  }
  const normalizedFamilies = new Set(bound.map((entity) => entity.renderBinding!.normalizedStyleFamily));
  if (normalizedFamilies.size > 1) blockers.push(`STYLE_COLLAGE_MULTIPLE_NORMALIZED_FAMILIES:${[...normalizedFamilies].join(",")}`);
  return blockers;
}
