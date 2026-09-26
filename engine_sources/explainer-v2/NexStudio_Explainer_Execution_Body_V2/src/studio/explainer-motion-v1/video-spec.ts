import { deepFreeze } from "./video-spec-freeze";
import { assertScenePlansValid, canBuildApprovedScenes } from "./scene-validator";
import { hashVideoSpec } from "./schemas";
import type { DirectorPlan, ExplainerRegistry, FrozenVideoSpec, ScenePlan, StorySpec, VideoSpec } from "./types";
import { buildContinuityRegistry, createMotionDirectionPlans } from "./motion-direction";

export function freezeVideoSpec(input: {
  id: string;
  story: StorySpec;
  director: DirectorPlan;
  scenes: ScenePlan[];
  registry: ExplainerRegistry;
  brandTokens: VideoSpec["brandTokens"];
  voiceTiming?: VideoSpec["voiceTiming"];
  soundSchedule?: VideoSpec["soundSchedule"];
  frozenAt: string;
}): FrozenVideoSpec {
  if (!canBuildApprovedScenes(input.scenes, input.story.sceneCount)) throw new Error("EXPLAINER_APPROVAL_GATE_FAILED: every required scene must be approved before production.");
  for (const scene of input.scenes) {
    const art = scene.visualConstruction?.productionArt;
    if (!art) throw new Error(`PRODUCTION_ART_PLAN_MISSING:${scene.id}`);
    if (art.status !== "READY_FOR_RENDER" || art.blockers.length) throw new Error(`PRODUCTION_ART_BLOCKED:${scene.id}:${art.blockers.join("|") || "not-ready"}`);
    if (art.releaseGate !== "EXECUTION_FIDELITY_REQUIRED") throw new Error(`PRODUCTION_ART_RELEASE_GATE_MISSING:${scene.id}`);
    if (art.rawRigVisibleAllowed !== false) throw new Error(`RAW_RIG_EXPOSURE_FORBIDDEN:${scene.id}`);
  }
  assertScenePlansValid(input.scenes, input.registry, input.story);
  const scenes = input.scenes.map((scene) => ({ ...scene, approvalState: scene.approvalState === "LOCKED" ? "LOCKED" as const : "APPROVED" as const }));
  const base: VideoSpec = {
    id: input.id, productionId: input.story.productionId, storySpecId: input.story.id, directorPlan: input.director, scenes, durationSec: input.story.durationSec,
    aspectRatio: input.story.aspectRatio, brandTokens: input.brandTokens, voiceTiming: input.voiceTiming ?? input.story.beats.map((beat, index) => ({ sceneId: scenes[index].id, startSec: scenes[index].startSec, durationSec: beat.durationSec, text: beat.narration, status: "placeholder" as const })),
    soundSchedule: input.soundSchedule ?? [], outputFormats: ["draft", "standard", "high"], validationVersion: "explainer-validation.v1", libraryVersion: input.registry.release, compilerVersion: "explainer-motion-compiler-1.0.0", frozenAt: input.frozenAt, contentHash: "",
    motionDirectionPlans: createMotionDirectionPlans(scenes), continuityRegistry: buildContinuityRegistry(scenes),
  };
  const spec = { ...base, contentHash: hashVideoSpec(base) };
  return deepFreeze(spec);
}

export function assertFrozenVideoSpecUnchanged(spec: FrozenVideoSpec) {
  const expected = hashVideoSpec(spec);
  if (expected !== spec.contentHash) throw new Error("VIDEOSPEC_MUTATION_DETECTED");
  return true;
}
