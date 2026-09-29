import type { BrandTokenSet, ComponentBinding, DirectorPlan, ExplainerRegistry, MotionEnergy, ScenePlan, StorySpec, UserAssetBinding } from "./types";
import { selectScene } from "./selector";
import { attachMotionDirection } from "./motion-direction";

// Brand tokens are an execution input. This module has no house/default Brand authority.
type AssetInput = { assetId: string; sourceId?: string; mediaType?: string };

function contentFor(scene: DirectorPlan["scenes"][number], story: StorySpec, selected: ReturnType<typeof selectScene>, brandTokens: BrandTokenSet): Record<string, unknown> {
  const beat = story.beats.find((item) => `${story.productionId}-scene-${item.order + 1}` === scene.sceneId);
  return {
    title: beat?.message ?? scene.heroSubject,
    subtitle: `${String((beat?.order ?? 0) + 1).padStart(2, "0")} · ${(beat?.narrativeRole ?? scene.storyFunction).toUpperCase()}`,
    body: beat?.narration ?? story.coreMessage,
    style: brandTokens.typographyStyle,
    energy: scene.emotionalEnergy,
    items: beat?.visualDirection ? [beat.visualDirection.heroSubject, beat.visualDirection.endingState] : [scene.heroSubject, scene.visualVerb],
    semanticMessage: beat?.semanticMessage ?? beat?.message,
    factualGoal: beat?.factualGoal,
    supportingFactIds: beat?.supportingFactIds ?? [],
    productionContent: true,
    mediaState: "VISUAL_COVERAGE_GAP",
    mediaFallback: "assets/media/semantic-explainer.svg",
    productionContentContract: {
      version: "explainer-content.v1",
      bound: true,
      demoContentAllowed: false,
      meaningfulRelation: beat?.semanticMessage ?? beat?.message ?? scene.heroSubject,
    },
    component: selected.sceneFamily.id,
  };
}

export function createScenePlans(input: {
  story: StorySpec;
  director: DirectorPlan;
  registry: ExplainerRegistry;
  motionEnergy?: MotionEnergy;
  brandTokens: BrandTokenSet;
  approvedAssets?: AssetInput[];
}): ScenePlan[] {
  const used = { families: new Set<string>(), transitions: new Set<string>() };
  const tokens = input.brandTokens;
  let cursor = 0;
  const scenes = input.director.scenes.map((directorScene, index) => {
    const beat = input.story.beats[index];
    if (!beat) throw new Error(`Missing StoryBeat for director scene ${directorScene.sceneId}`);
    const selected = selectScene(input.registry, directorScene, used, input.motionEnergy ?? "medium", input.story.aspectRatio);
    const content = contentFor(directorScene, input.story, selected, tokens);
    const componentContent = beat.componentContent && typeof beat.componentContent === "object" ? beat.componentContent : {};
    const defaultData = selected.workflow
      ? { dataVariant: "full", data: { title: beat.message, eyebrow: beat.narrativeRole ?? "PROCESS", state: "ready", nodes: [{ id: "start", label: "START", type: "first step" }, { id: "next", label: "NEXT", type: "next step" }, { id: "finish", label: "FINISH", type: "result" }], edges: [{ from: "start", to: "next" }, { from: "next", to: "finish" }] } }
      : { dataVariant: "full", data: { title: beat.message, eyebrow: beat.narrativeRole ?? "STAGE", state: "ready", format: "compact", metricKind: "ordinal", items: [{ label: beat.narrativeRole ?? "STAGE", value: 1 }] } };
    const bindingContent = (slot: string) => ({
      ...content,
      ...(slot === "data" || slot === "workflow" ? defaultData : {}),
      ...(componentContent[slot] && typeof componentContent[slot] === "object" ? componentContent[slot] as Record<string, unknown> : {}),
    });
    const bindings: ComponentBinding[] = [
      { slot: "hero", componentId: selected.sceneFamily.id, content: bindingContent("hero") },
      { slot: "typography", componentId: selected.typography.id, content: bindingContent("typography") },
      { slot: "media", componentId: selected.hero.id, content: bindingContent("media") },
      { slot: "icon", componentId: selected.support.id, content: bindingContent("icon") },
    ];
    const constructionOwnsVisual = directorScene.visualConstruction && !["existing-component", "hybrid"].includes(directorScene.visualConstruction.constructionMode);
    if (selected.data && !constructionOwnsVisual) bindings.push({ slot: selected.workflow ? "workflow" : "data", componentId: selected.data.id, content: bindingContent(selected.workflow ? "workflow" : "data") });
    const mediaContent = componentContent.media && typeof componentContent.media === "object" ? componentContent.media as Record<string, unknown> : {};
    const bindUserAsset = mediaContent.bindAsset !== false;
    const userAssetBindings: UserAssetBinding[] = bindUserAsset
      ? (input.approvedAssets ?? []).map((asset, assetIndex) => ({ slot: assetIndex === 0 ? "hero-media" : `supporting-media-${assetIndex}`, assetId: asset.assetId, sourceId: asset.sourceId, mediaType: asset.mediaType, cropMode: "cover", focalPoint: { x: 50, y: 50 } }))
      : [];
    const durationSec = beat.durationSec;
    const productionContentContract = beat.semanticMessage && directorScene.visualConcept
      ? {
        version: "explainer-content.v1",
        bound: true,
        demoContentAllowed: false,
        meaningfulRelation: beat.semanticMessage,
        contentSlots: {
          headline: { required: true, type: "short-text" },
          narration: { required: true, type: "explanatory-text" },
          visualDirection: { required: true, type: "structured-action" },
        },
      }
      : undefined;
    const scene: ScenePlan = {
      id: directorScene.sceneId,
      productionId: input.story.productionId,
      storyBeatId: beat.id,
      order: index,
      startSec: Math.round(cursor * 100) / 100,
      durationSec,
      message: beat.message,
      narration: beat.narration,
      visualVerb: directorScene.visualVerb,
      heroSubject: directorScene.heroSubject,
      sceneFamilyId: selected.sceneFamily.id,
      layoutArchetypeId: selected.sceneFamily.id,
      layoutVariantId: selected.layoutVariantId,
      typographySystemId: selected.typography.id,
      componentBindings: bindings,
      motionPrimitiveIds: [selected.motion.id],
      transitionInId: index > 0 ? selected.transition.id : undefined,
      transitionOutId: index < input.director.scenes.length - 1 ? selected.transition.id : undefined,
      userAssetBindings,
      brandTokens: tokens,
      approvalState: "DRAFT",
      revisionVersion: 1,
      validationWarnings: [],
      factualGoal: beat.factualGoal,
      semanticMessage: beat.semanticMessage,
      supportingFactIds: beat.supportingFactIds,
      narrativeRole: beat.narrativeRole,
      visualConcept: directorScene.visualConcept,
      visualDirection: directorScene.visualDirection,
      purpose: beat.narrativeRole ?? beat.purpose,
      visualConstruction: directorScene.visualConstruction,
      visualDominance: directorScene.visualDominance,
      styleProfile: directorScene.styleProfile,
      motionIntent: directorScene.motionIntent,
      continuityObjectId: directorScene.visualConstruction?.continuity?.objectId,
      continuityState: directorScene.visualConstruction?.continuity?.state,
      ...(productionContentContract ? { productionContentContract } : {}),
    };
    cursor += durationSec;
    return scene;
  });
  return attachMotionDirection(scenes);
}
