import { compileExplainerVideoSpec } from "./compiler";
import { hashVideoSpec } from "./schemas";
import type { BrandTokenSet, CompilerOptions, DirectorPlan, ExplainerComposition, ExplainerRegistry, FrozenVideoSpec, ScenePlan, StorySpec, VideoSpec } from "./types";
import { buildContinuityRegistry, createMotionDirectionPlans } from "./motion-direction";

export function renderExplainerPreview(spec: FrozenVideoSpec, registry: ExplainerRegistry): ExplainerComposition {
  // Preview and production deliberately share the exact VideoSpec and compiler.
  // Only resolution/quality changes here.
  return compileExplainerVideoSpec(spec, registry, { quality: "draft", buildTimestamp: spec.frozenAt });
}

export function renderExplainerStoryboardPreview(input: { story: StorySpec; director: DirectorPlan; scenes: ScenePlan[]; registry: ExplainerRegistry; brandTokens: BrandTokenSet; frozenAt: string; mediaAssets?: CompilerOptions["mediaAssets"] }): ExplainerComposition {
  const draft: VideoSpec = {
    id: `${input.story.productionId}:storyboard-preview`, productionId: input.story.productionId, storySpecId: input.story.id, directorPlan: input.director, scenes: input.scenes, durationSec: input.story.durationSec, aspectRatio: input.story.aspectRatio, brandTokens: input.brandTokens,
    voiceTiming: input.story.beats.map((beat, index) => ({ sceneId: input.scenes[index].id, startSec: input.scenes[index].startSec, durationSec: beat.durationSec, text: beat.narration, status: "placeholder" as const })), soundSchedule: [], outputFormats: ["draft"], validationVersion: "explainer-validation.v1", libraryVersion: input.registry.release, compilerVersion: "explainer-motion-compiler-1.0.0", frozenAt: input.frozenAt, contentHash: "",
    motionDirectionPlans: createMotionDirectionPlans(input.scenes), continuityRegistry: buildContinuityRegistry(input.scenes),
  };
  const previewSpec = { ...draft, contentHash: hashVideoSpec(draft) } as FrozenVideoSpec;
  return compileExplainerVideoSpec(previewSpec, input.registry, { quality: "draft", buildTimestamp: input.frozenAt, mediaAssets: input.mediaAssets });
}
