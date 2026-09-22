import type { ExplainerRegistry, ScenePlan, StorySpec } from "./types";
import { hashApprovedScene, scenePlanSchema, videoSpecSchema } from "./schemas";

export type SceneValidationReport = { ok: boolean; errors: string[]; warnings: string[]; hash: string };

function exactIds(scene: ScenePlan) {
  return [scene.sceneFamilyId, scene.layoutArchetypeId, scene.typographySystemId, ...scene.componentBindings.map((binding) => binding.componentId), ...scene.motionPrimitiveIds, scene.transitionInId, scene.transitionOutId, scene.cameraPresetId].filter((id): id is string => Boolean(id));
}

export function validateScenePlan(scene: ScenePlan, registry: ExplainerRegistry, story?: StorySpec): SceneValidationReport {
  const errors: string[] = [];
  const warnings = [...scene.validationWarnings];
  const parsed = scenePlanSchema.safeParse(scene);
  if (!parsed.success) errors.push(...parsed.error.issues.map((issue) => `${issue.path.join(".")}: ${issue.message}`));
  for (const id of exactIds(scene)) if (!registry.has(id)) errors.push(`Unknown RC1 component ID: ${id}`);
  if (scene.layoutArchetypeId && registry.has(scene.layoutArchetypeId) && registry.resolve(scene.layoutArchetypeId).category !== "scene-family") errors.push(`Layout archetype must resolve to a scene-family layout: ${scene.layoutArchetypeId}`);
  if (scene.order < 0 || scene.startSec < 0 || scene.durationSec <= 0) errors.push(`Invalid timing for ${scene.id}`);
  if (story && scene.productionId !== story.productionId) errors.push(`Scene ${scene.id} belongs to a different production.`);
  if (scene.approvalState === "APPROVED" && scene.approvedHash && scene.approvedHash !== hashApprovedScene(scene)) errors.push(`Approved hash mismatch for ${scene.id}`);
  return { ok: errors.length === 0, errors, warnings, hash: hashApprovedScene(scene) };
}

export function validateScenePlans(scenes: ScenePlan[], registry: ExplainerRegistry, story?: StorySpec): SceneValidationReport[] {
  const reports = scenes.map((scene) => validateScenePlan(scene, registry, story));
  const ordered = [...scenes].sort((a, b) => a.order - b.order);
  for (let index = 1; index < ordered.length; index += 1) {
    const previous = ordered[index - 1];
    const current = ordered[index];
    if (Math.abs(current.startSec - (previous.startSec + previous.durationSec)) > 0.02) reports[index].errors.push(`Scene timing is not contiguous after ${previous.id}.`);
  }
  return reports;
}

export function assertScenePlansValid(scenes: ScenePlan[], registry: ExplainerRegistry, story?: StorySpec) {
  const reports = validateScenePlans(scenes, registry, story);
  const errors = reports.flatMap((report) => report.errors);
  if (errors.length) throw new Error(`SCENE_PLAN_INVALID: ${errors.join(" ")}`);
  return reports;
}

export function canBuildApprovedScenes(scenes: ScenePlan[], expectedSceneCount: number) {
  return scenes.length === expectedSceneCount && scenes.every((scene) => scene.approvalState === "APPROVED" || scene.approvalState === "LOCKED");
}

export function assertVideoSpecValid(spec: unknown, registry: ExplainerRegistry) {
  const parsed = videoSpecSchema.safeParse(spec);
  if (!parsed.success) throw new Error(`VIDEOSPEC_INVALID: ${parsed.error.issues.map((issue) => `${issue.path.join(".")}: ${issue.message}`).join(" ")}`);
  assertScenePlansValid(parsed.data.scenes as unknown as ScenePlan[], registry);
  if (!parsed.data.scenes.every((scene) => scene.approvalState === "APPROVED" || scene.approvalState === "LOCKED")) throw new Error("VIDEOSPEC_INVALID: every scene must be approved before freezing.");
  return parsed.data;
}
