import { EXPLAINER_FRAME_RATE, MOTION_CRAFT_ENGINE_VERSION, type CameraPerformance, type ContinuityBridge, type MotionPerformance, type MotionPerformancePlan, type MotionPerformanceVariant, type ScenePlan, type SemanticMotionAction, type TransitionPerformance, type VisualEntity } from "./types";

export const motionPerformanceRegistry: Array<{
  action: SemanticMotionAction["action"];
  variants: MotionPerformanceVariant[];
  supportedVisualClasses: string[];
  preferredEasing: SemanticMotionAction["easingProfile"];
  continuitySupport: "none" | "preserve" | "transform";
  minimumDurationFrames: number;
}> = [
  { action: "grow", variants: ["organic-path-grow", "continuity-transform", "positive-growth-delta", "scale-settle"], supportedVisualClasses: ["organic-object", "organic-path", "branching-path", "group"], preferredEasing: "organic-controlled", continuitySupport: "transform", minimumDurationFrames: 12 },
  { action: "extend", variants: ["organic-path-grow", "continuity-transform", "linear-extension"], supportedVisualClasses: ["organic-path", "branching-path", "linear-path"], preferredEasing: "organic-controlled", continuitySupport: "preserve", minimumDurationFrames: 18 },
  { action: "branch", variants: ["staggered-branch", "attached-unfold", "organic-path-grow"], supportedVisualClasses: ["branching-path", "organic-path", "group"], preferredEasing: "organic-controlled", continuitySupport: "preserve", minimumDurationFrames: 16 },
  { action: "flow", variants: ["flow-to", "anchor-flow"], supportedVisualClasses: ["particle", "field", "transfer-object", "organic-object", "group"], preferredEasing: "precise", continuitySupport: "none", minimumDurationFrames: 18 },
  { action: "travel", variants: ["anchor-flow", "precise-transfer"], supportedVisualClasses: ["particle", "node", "transfer-object", "linear-path", "organic-path"], preferredEasing: "technical", continuitySupport: "none", minimumDurationFrames: 18 },
  { action: "absorb", variants: ["receiver-absorb"], supportedVisualClasses: ["organic-object", "container", "node", "group"], preferredEasing: "organic-controlled", continuitySupport: "transform", minimumDurationFrames: 16 },
  { action: "unfold", variants: ["attached-unfold", "pivot-unfold"], supportedVisualClasses: ["attached-surface", "organic-object", "organic-path", "group", "document"], preferredEasing: "organic-controlled", continuitySupport: "preserve", minimumDurationFrames: 18 },
  { action: "orient-toward", variants: ["target-orient"], supportedVisualClasses: ["organic-object", "organic-path", "arrow", "icon"], preferredEasing: "calm", continuitySupport: "preserve", minimumDurationFrames: 18 },
  { action: "open", variants: ["causal-reveal"], supportedVisualClasses: ["organic-object", "container", "document", "group"], preferredEasing: "organic-controlled", continuitySupport: "transform", minimumDurationFrames: 12 },
  { action: "reveal", variants: ["causal-reveal"], supportedVisualClasses: ["group", "illustration", "media", "object"], preferredEasing: "educational", continuitySupport: "preserve", minimumDurationFrames: 12 },
  { action: "pulse", variants: ["pulse-response"], supportedVisualClasses: ["organic-object", "node", "field", "group"], preferredEasing: "organic-controlled", continuitySupport: "preserve", minimumDurationFrames: 12 },
  { action: "transfer", variants: ["precise-transfer", "anchor-flow"], supportedVisualClasses: ["particle", "node", "transfer-object", "group"], preferredEasing: "precise", continuitySupport: "none", minimumDurationFrames: 18 },
  { action: "assemble", variants: ["cause-and-effect-performance", "assemble-highlight", "scale-settle"], supportedVisualClasses: ["group", "node", "data-series", "organic-object"], preferredEasing: "educational", continuitySupport: "transform", minimumDurationFrames: 14 },
  { action: "transform", variants: ["scale-settle", "causal-reveal"], supportedVisualClasses: ["group", "organic-object", "node", "document"], preferredEasing: "organic-controlled", continuitySupport: "transform", minimumDurationFrames: 16 },
  { action: "merge", variants: ["anchor-flow", "assemble-highlight"], supportedVisualClasses: ["group", "node", "particle", "transfer-object"], preferredEasing: "precise", continuitySupport: "transform", minimumDurationFrames: 14 },
  { action: "split", variants: ["staggered-branch", "linear-extension"], supportedVisualClasses: ["group", "node", "branching-path", "organic-path"], preferredEasing: "precise", continuitySupport: "transform", minimumDurationFrames: 14 },
  { action: "connect", variants: ["linear-extension", "precise-transfer"], supportedVisualClasses: ["connector", "linear-path", "organic-path", "group"], preferredEasing: "precise", continuitySupport: "preserve", minimumDurationFrames: 10 },
  { action: "highlight", variants: ["assemble-highlight", "pulse-response"], supportedVisualClasses: ["group", "node", "label", "data-series"], preferredEasing: "precise", continuitySupport: "preserve", minimumDurationFrames: 10 },
  { action: "validate", variants: ["assemble-highlight"], supportedVisualClasses: ["node", "group", "data-series"], preferredEasing: "technical", continuitySupport: "preserve", minimumDurationFrames: 12 },
];

const round = (value: number) => Math.max(0, Math.round(value));
const entityList = (scene: ScenePlan) => [scene.visualConstruction?.heroEntity, ...(scene.visualConstruction?.supportingEntities ?? [])].filter((entity): entity is VisualEntity => Boolean(entity));
const actionRegistryEntry = (action: SemanticMotionAction["action"]) => motionPerformanceRegistry.find((entry) => entry.action === action);

function chooseVariant(action: SemanticMotionAction, actor: VisualEntity | undefined): MotionPerformanceVariant {
  const entry = actionRegistryEntry(action.action);
  if (!entry) return "causal-reveal";
  const visualClass = actor?.visualClass ?? "group";
  if (actor?.continuity && (action.action === "extend" || action.action === "grow") && actor.visualClass !== "group") return "continuity-transform";
  if (action.action === "grow" && (actor?.continuity || action.startState === "established" || action.startState === "partly-established")) return "positive-growth-delta";
  if (action.action === "extend" && (actor?.representation === "branch" || actor?.representation === "stem" || visualClass === "organic-path" || visualClass === "branching-path")) return "organic-path-grow";
  if (action.action === "branch" && (actor?.representation === "branch" || visualClass === "branching-path")) return "staggered-branch";
  // Keep the established implementation variants as the concrete runtime
  // contract.  The more descriptive V4 capabilities are published through
  // `mechanism` below, so existing consumers do not have to migrate merely
  // because the semantic contract became richer.
  if (action.action === "unfold") return "attached-unfold";
  if (action.action === "flow") return "anchor-flow";
  if (action.action === "travel") return "anchor-flow";
  if (action.action === "assemble") return "assemble-highlight";
  return entry.variants.find((variant) => variant === "organic-path-grow" && ["organic-path", "branching-path"].includes(visualClass)) ?? entry.variants[0]!;
}

function mechanismFor(action: SemanticMotionAction, variant: MotionPerformanceVariant): MotionPerformanceVariant {
  if (action.action === "flow") return "flow-to";
  if (action.action === "unfold") return "attached-unfold";
  if (action.action === "assemble") return "cause-and-effect-performance";
  return variant;
}

function anchorFor(action: SemanticMotionAction, source: boolean): MotionPerformance["sourceAnchor"] {
  if (["flow", "travel", "transfer"].includes(action.action)) return source ? "entry" : "attachment";
  if (["extend", "grow", "branch"].includes(action.action)) return action.direction === "up" ? "growth-origin" : "branch-origin";
  if (action.action === "unfold") return "attachment";
  if (["absorb", "connect", "merge"].includes(action.action)) return source ? "exit" : "attachment";
  return source ? "center" : "focus";
}

function bridgeFor(scene: ScenePlan, frameRate: number): ContinuityBridge[] {
  const direction = scene.motionDirection?.transitionOut;
  const continuity = scene.visualConstruction?.continuity;
  if (!direction || !continuity) return [];
  const destination = scene.visualConstruction?.continuity?.nextState ?? direction.toState ?? continuity.state;
  const strategy: ContinuityBridge["strategy"] = direction.family === "camera-follow" ? "camera-follow" : direction.family === "path-continuation" ? "path-continue" : direction.family === "object-transformation" ? "transform" : direction.family === "focus-transfer" ? "reframe" : "preserve";
  return [{ continuityId: continuity.objectId, fromSceneId: scene.id, toSceneId: "next-scene", sourceState: direction.fromState ?? continuity.state, destinationState: destination, strategy, bridgeDurationFrames: round((direction.durationSec || .6) * frameRate) }];
}

function cameraFor(scene: ScenePlan, frameRate: number, durationFrames: number): CameraPerformance {
  const source = scene.motionDirection?.cameraPlan;
  const startFrame = round((source?.startSec ?? 0) * frameRate);
  const cameraDuration = round((source?.durationSec ?? scene.durationSec) * frameRate);
  const action = source?.action ?? "hold";
  const scaleFrom = source?.scaleFrom ?? 1;
  const scaleTo = source?.scaleTo ?? 1;
  const translateXPercent = source?.translateXPercent ?? 0;
  const translateYPercent = source?.translateYPercent ?? 0;
  const cameraTravelDistance = Math.sqrt(Math.pow(scaleTo - scaleFrom, 2) + Math.pow(translateXPercent / 100, 2) + Math.pow(translateYPercent / 100, 2));
  const cameraActionExpected = scene.visualConstruction?.artDirection?.cameraActionExpected ?? action !== "hold";
  return {
    action,
    target: source?.target ?? scene.visualConstruction?.heroEntity.id ?? "hero",
    reason: source?.reason ?? "Hold a stable explanatory frame.",
    startFrame: Math.min(startFrame, durationFrames),
    endFrame: Math.min(durationFrames, startFrame + cameraDuration),
    durationFrames: Math.max(1, Math.min(durationFrames, cameraDuration)),
    easingProfile: action === "follow-object" || action === "macro-focus" ? "calm" : "precise",
    scaleFrom,
    scaleTo,
    translateXPercent,
    translateYPercent,
    safeFocalRegion: { xMin: .2, xMax: .8, yMin: .16, yMax: .84 },
    cameraContinuity: true,
    cameraActionExpected,
    cameraActionExecuted: !cameraActionExpected || cameraTravelDistance > .0005,
    cameraTravelDistance,
    cameraTargetTrackingError: action === "follow-object" ? 0 : 0,
  };
}

export function resolveMotionPerformancePlan(scene: ScenePlan, frameRate: number = EXPLAINER_FRAME_RATE): MotionPerformancePlan {
  const direction = scene.motionDirection;
  const entities = entityList(scene);
  const byId = new Map(entities.map((entity) => [entity.id, entity]));
  const durationFrames = round(scene.durationSec * frameRate);
  const completed = new Map<string, number>();
  const performanceIdByAction = new Map<string, string>();
  const performances: MotionPerformance[] = [];
  for (const action of direction?.actions ?? []) {
    const actor = byId.get(action.actor);
    const variant = chooseVariant(action, actor);
    const mechanism = mechanismFor(action, variant);
    const baseStart = round(action.startSec * frameRate);
    const entry = actionRegistryEntry(action.action);
    const requestedDuration = Math.max(entry?.minimumDurationFrames ?? 1, round(action.durationSec * frameRate));
    const prerequisiteIds = action.chainAfter ? [performanceIdByAction.get(action.chainAfter) ?? action.chainAfter] : [];
    const prerequisiteEnd = action.chainAfter ? (completed.get(action.chainAfter) ?? 0) : 0;
    const startFrame = Math.min(Math.max(baseStart, prerequisiteEnd + Math.max(1, round(frameRate * .035))), Math.max(0, durationFrames - 1));
    const endFrame = Math.min(durationFrames, Math.max(startFrame + 1, startFrame + requestedDuration));
    const performance: MotionPerformance = {
      id: `${scene.id}:performance:${action.id.split(":").at(-1) ?? action.id}`,
      actionId: action.id,
      action: action.action,
      actor: action.actor,
      target: action.target,
      variant,
      startFrame,
      endFrame,
      durationFrames: endFrame - startFrame,
      easingProfile: action.easingProfile || entry?.preferredEasing || "educational",
      sourceAnchor: anchorFor(action, true),
      targetAnchor: action.target ? anchorFor(action, false) : undefined,
      prerequisiteIds,
      affectedEntities: [...new Set([action.actor, action.target].filter((value): value is string => Boolean(value)))],
     quality: {
        continuitySupport: entry?.continuitySupport ?? "none",
        cameraCompatible: !["anchor-flow", "precise-transfer"].includes(variant),
        reducedMotion: variant === "organic-path-grow" || variant === "staggered-branch" ? "essential-path" : variant === "causal-reveal" ? "short-reveal" : "settled-state",
        resultPersistenceFrames: ["grow", "extend", "branch", "unfold", "assemble", "absorb", "transfer"].includes(action.action) ? Math.max(0, durationFrames - endFrame) : 0,
      },
      mechanism,
    };
    performances.push(performance);
    completed.set(action.id, endFrame);
    performanceIdByAction.set(action.id, performance.id);
  }
  const cameraPerformance = cameraFor(scene, frameRate, durationFrames);
  const transitionDirection = direction?.transitionOut;
  const transitionPerformance: TransitionPerformance | undefined = transitionDirection ? {
    family: transitionDirection.family,
    durationFrames: Math.max(1, round(transitionDirection.durationSec * frameRate)),
    easingProfile: transitionDirection.family === "camera-follow" ? "calm" : "precise",
    continuityDriven: ["object-continuation", "object-transformation", "camera-follow", "path-continuation", "shape-match"].includes(transitionDirection.family),
    reason: transitionDirection.reason,
  } : undefined;
  const typographyPerformances = scene.visualDominance === "typography-led"
    ? [{ role: "headline" as const, mode: "quiet-reveal" as const, startFrame: Math.max(1, round(frameRate * .12)), endFrame: Math.max(2, round(frameRate * .72)) }]
    : [{ role: "headline" as const, mode: "recede" as const, startFrame: Math.max(1, round(frameRate * .1)), endFrame: Math.max(2, round(frameRate * .55)) }];
  return {
    version: MOTION_CRAFT_ENGINE_VERSION,
    sceneId: scene.id,
    frameRate,
    durationFrames,
    performances,
    continuityBridges: bridgeFor(scene, frameRate),
    cameraPerformance,
    transitionPerformance,
    typographyPerformances,
    eventGraph: performances.map((performance) => ({ id: performance.id, prerequisiteIds: performance.prerequisiteIds, startFrame: performance.startFrame, endFrame: performance.endFrame, affectedEntities: performance.affectedEntities })),
     reducedMotion: { strategy: direction?.reducedMotionPlan.strategy ?? "settled-state-cuts", preservePerformanceIds: performances.filter((performance) => performance.quality.reducedMotion !== "settled-state").map((performance) => performance.id) },
     creativeMechanisms: [...new Set([
       ...performances.map((performance) => performance.mechanism ?? performance.variant),
       ...(scene.visualConstruction?.spatialGrammar === "converging-inputs" ? ["converging-inputs" as MotionPerformanceVariant] : []),
       ...(scene.visualConstruction?.spatialGrammar === "cause-and-effect" ? ["cause-and-effect-performance" as MotionPerformanceVariant] : []),
       ...(cameraPerformance.action === "follow-object" ? ["target-follow-camera" as MotionPerformanceVariant] : []),
     ])],
     resultPersistenceFrames: Math.max(scene.visualConstruction?.artDirection?.resultPersistenceFrames ?? 0, ...performances.map((performance) => performance.quality.resultPersistenceFrames)),
   };
}

export function resolveMotionPerformancePlans(scenes: ScenePlan[], frameRate: number = EXPLAINER_FRAME_RATE) {
  return scenes.map((scene) => resolveMotionPerformancePlan(scene, frameRate));
}

export function motionPerformanceToFrameMap(plan: MotionPerformancePlan) {
  return plan.performances.map((performance) => ({ id: performance.id, actionId: performance.actionId, actor: performance.actor, target: performance.target, variant: performance.variant, mechanism: performance.mechanism, startFrame: performance.startFrame, endFrame: performance.endFrame, durationFrames: performance.durationFrames, resultPersistenceFrames: performance.quality.resultPersistenceFrames, prerequisiteIds: performance.prerequisiteIds }));
}
