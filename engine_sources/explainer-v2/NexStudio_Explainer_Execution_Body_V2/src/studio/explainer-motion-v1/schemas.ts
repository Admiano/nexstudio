import { createHash } from "node:crypto";
import { z } from "zod";
import type { ScenePlan, VideoSpec } from "./types";

export const aspectRatioSchema = z.enum(["16:9", "1:1", "9:16"]);
export const visualVerbSchema = z.enum([
  "Reveal", "Extract", "Split", "Merge", "Transform", "Assemble", "Route", "Compare", "Rank", "Filter",
  "Expand", "Collapse", "Scan", "Detect", "Repair", "Validate", "Package", "Deliver", "Connect", "Multiply", "Convert",
  "Grow", "Unfold", "Branch", "Emerge", "Absorb", "Flow", "Illuminate", "Accumulate", "Circulate",
]);
export const storyPurposeSchema = z.enum(["hook", "context", "problem", "concept", "how-it-works", "proof", "validation", "outcome", "cta"]);

export const storySpecSchema = z.object({
  id: z.string().min(1),
  productionId: z.string().min(1),
  title: z.string().min(1),
  durationSec: z.number().positive(),
  sceneCount: z.number().int().min(5).max(6),
  audience: z.string(),
  goal: z.string(),
  coreMessage: z.string(),
  tone: z.string(),
  aspectRatio: aspectRatioSchema,
  beats: z.array(z.object({
    id: z.string().min(1),
    order: z.number().int().nonnegative(),
    purpose: storyPurposeSchema,
    message: z.string().min(1),
    narration: z.string().min(1),
    durationSec: z.number().positive(),
  })).min(5).max(6),
  version: z.string().min(1),
  rawRequest: z.string().optional(),
  intent: z.object({
    topic: z.string().min(1),
    intentType: z.string().min(1),
    knowledgeDomain: z.string().min(1),
    requiresProblem: z.boolean(),
    requiresChronology: z.boolean(),
    requiresMechanism: z.boolean(),
    requiresComparison: z.boolean(),
    requiresProductProof: z.boolean(),
    requiresCTA: z.boolean(),
  }).optional(),
  grammar: z.string().optional(),
  knowledgePack: z.object({
    version: z.string(), topic: z.string(), domain: z.string(), mode: z.string(),
    facts: z.array(z.object({ id: z.string(), statement: z.string(), domain: z.string(), sourceMode: z.string(), confidence: z.string(), supports: z.array(z.string()) })),
    limitations: z.array(z.string()), requiresResearch: z.boolean(),
  }).optional(),
}).superRefine((value, ctx) => {
  if (value.beats.length !== value.sceneCount) ctx.addIssue({ code: "custom", path: ["sceneCount"], message: "sceneCount must match beats.length" });
  const total = value.beats.reduce((sum, beat) => sum + beat.durationSec, 0);
  if (Math.abs(total - value.durationSec) > 0.02) ctx.addIssue({ code: "custom", path: ["durationSec"], message: "Beat durations must equal durationSec" });
});

export const directorPlanSchema = z.object({
  storySpecId: z.string().min(1),
  productionId: z.string().min(1),
  scenes: z.array(z.object({
    sceneId: z.string().min(1),
    storyFunction: z.string().min(1),
    visualVerb: visualVerbSchema,
    heroSubject: z.string().min(1),
    supportingSubjects: z.array(z.string()),
    layoutIntent: z.string().min(1),
    informationDensity: z.enum(["low", "medium", "high"]),
    cameraIntent: z.string().min(1),
    transitionIntent: z.string().min(1),
    copyBudget: z.number().int().positive(),
    emotionalEnergy: z.string().min(1),
  continuityKey: z.string().min(1),
  visualConcept: z.string().optional(),
  visualDirection: z.record(z.string(), z.unknown()).optional(),
  continuityObject: z.string().optional(),
  componentHints: z.record(z.string(), z.string()).optional(),
  visualConstruction: z.record(z.string(), z.unknown()).optional(),
  visualDominance: z.string().optional(),
  styleProfile: z.record(z.string(), z.unknown()).optional(),
  motionIntent: z.record(z.string(), z.unknown()).optional(),
  })).min(5).max(6),
  version: z.string().min(1),
});

const visualConstructionSchema = z.object({
  sceneId: z.string().min(1), semanticGoal: z.string().min(1),
  heroEntity: z.object({ id: z.string().min(1), type: z.string().min(1), semanticType: z.string().min(1), importance: z.string().min(1), continuity: z.boolean().optional(), visualClass: z.string().optional(), representation: z.string().optional(), label: z.string().optional(), capabilities: z.array(z.string()).optional(), geometry: z.record(z.string(), z.unknown()).optional() }),
  supportingEntities: z.array(z.object({ id: z.string().min(1), type: z.string().min(1), semanticType: z.string().min(1), importance: z.string().min(1), continuity: z.boolean().optional(), visualClass: z.string().optional(), representation: z.string().optional(), label: z.string().optional(), capabilities: z.array(z.string()).optional(), geometry: z.record(z.string(), z.unknown()).optional() })),
  relationships: z.array(z.object({ from: z.string(), to: z.string(), kind: z.string(), direction: z.string().optional(), emphasis: z.string().optional() })),
  transformation: z.object({ fromState: z.string(), toState: z.string(), action: z.string(), progress: z.number().optional() }).optional(),
  continuity: z.object({ objectId: z.string(), previousState: z.string().optional(), state: z.string(), nextState: z.string().optional(), handoff: z.string(), preserveFeatures: z.array(z.string()).optional() }).optional(),
  spatialGrammar: z.string(), labelStrategy: z.string(), constructionMode: z.string(), requiredCapabilities: z.array(z.string()), optionalCapabilities: z.array(z.string()),
  dominanceMode: z.string(), styleProfile: z.record(z.string(), z.unknown()), motionIntent: z.object({ entryState: z.string(), mainAction: z.string(), settledState: z.string(), exitTransformation: z.string(), continuityHandoff: z.string() }),
  artDirection: z.object({
    planId: z.string().optional(), resolvedBy: z.string().optional(),
    activeStateId: z.string(),
    states: z.array(z.object({ id: z.string(), label: z.string().optional(), sceneId: z.string().optional(), planId: z.string().optional(), compositionArchetype: z.string().optional(), viewport: z.object({ width: z.number(), height: z.number(), aspectRatio: z.string() }).optional(), regions: z.record(z.string(), z.object({ x: z.number(), y: z.number(), width: z.number(), height: z.number() })).optional(), entities: z.record(z.string(), z.unknown()), quality: z.object({ heroScale: z.number(), visualBalance: z.string(), silhouetteQuality: z.string(), negativeSpaceIntent: z.string(), subjectReadability: z.string(), attachmentQuality: z.string() }), metrics: z.record(z.string(), z.number()).optional(), resultPersistenceFrames: z.number().int().nonnegative().optional() })),
    continuityTransform: z.object({ fromStateId: z.string(), toStateId: z.string(), anchorCorrespondence: z.array(z.object({ fromEntityId: z.string(), toEntityId: z.string(), fromAnchor: z.string().optional(), toAnchor: z.string().optional() })), durationFrames: z.number().int().positive(), easingProfile: z.string() }).optional(),
    titleTreatment: z.enum(["integrated-headline", "anchored-label", "temporary-overlay"]),
    typographyProminence: z.enum(["primary", "secondary", "quiet"]).optional(),
    typographyRegion: z.object({ x: z.number(), y: z.number(), width: z.number(), height: z.number() }).optional(),
    cameraCrop: z.object({ focalEntity: z.string(), safeRegion: z.object({ x: z.number(), y: z.number(), width: z.number(), height: z.number() }), shotSize: z.string(), cropPolicy: z.string() }).optional(),
    surface: z.object({ fill: z.string().optional(), stroke: z.string().optional(), strokeWidth: z.number().optional(), radius: z.number().optional(), opacity: z.number().optional() }).optional(),
    resultPersistenceFrames: z.number().int().nonnegative(), cameraActionExpected: z.boolean().optional(), cameraTargetTrackingErrorMax: z.number().nonnegative().optional(),
  }).optional(),
  artDirectionPlan: z.record(z.string(), z.unknown()).optional(),
  constructionId: z.string().optional(), visualCoverage: z.string().optional(), directorContractVersion: z.string().optional(), visualGrammarVersion: z.string().optional(), coverageDecision: z.string().optional(), assetRequirement: z.record(z.string(), z.unknown()).optional(),
});

const motionDirectionSchema = z.object({
  sceneId: z.string().min(1),
  entryState: z.object({ id: z.string(), description: z.string(), visibleEntities: z.array(z.string()), continuityState: z.string().optional() }),
  actions: z.array(z.object({
    id: z.string(), action: z.string(), actor: z.string(), target: z.string().optional(), source: z.string().optional(), relationship: z.string().optional(), direction: z.string().optional(),
    startState: z.string(), endState: z.string(), startSec: z.number().nonnegative(), durationSec: z.number().positive(), priority: z.enum(["primary", "secondary", "ambient"]), chainAfter: z.string().optional(), easingProfile: z.string(),
  })),
  cameraPlan: z.object({ action: z.string(), target: z.string(), reason: z.string(), startSec: z.number().nonnegative(), durationSec: z.number().nonnegative(), scaleFrom: z.number().optional(), scaleTo: z.number().optional(), translateXPercent: z.number().optional(), translateYPercent: z.number().optional() }),
  transitionIn: z.record(z.string(), z.unknown()).optional(), transitionOut: z.record(z.string(), z.unknown()).optional(),
  continuityObject: z.object({ id: z.string(), incomingState: z.string(), outgoingState: z.string() }).optional(),
  settledStoryboardState: z.number().nonnegative(), emotionalEnergy: z.string(), motionDensity: z.enum(["minimal", "moderate", "active"]),
  reducedMotionPlan: z.object({ strategy: z.enum(["settled-state-cuts", "short-opacity-reveal", "essential-path-only"]), preserveActions: z.array(z.string()), suppressActions: z.array(z.string()) }),
});

const brandTokenSchema = z.object({
  paperBg: z.string().min(1), paperSurface: z.string().min(1), ink: z.string().min(1), inkMuted: z.string().min(1),
  primary: z.string().min(1), secondary: z.string().min(1), accent: z.string().min(1), highlight: z.string().min(1), typographyStyle: z.string().min(1),
});

const componentBindingSchema = z.object({
  slot: z.enum(["hero", "supporting", "typography", "data", "workflow", "icon", "media"]),
  componentId: z.string().min(1),
  content: z.record(z.string(), z.unknown()),
});

const userAssetBindingSchema = z.object({
  slot: z.string().min(1), assetId: z.string().min(1), sourceId: z.string().optional(), mediaType: z.string().optional(),
  cropMode: z.enum(["cover", "contain", "fill"]).optional(), focalPoint: z.object({ x: z.number().min(0).max(100), y: z.number().min(0).max(100) }).optional(),
});

export const scenePlanSchema = z.object({
  id: z.string().min(1), productionId: z.string().min(1), storyBeatId: z.string().min(1), order: z.number().int().nonnegative(),
  startSec: z.number().nonnegative(), durationSec: z.number().positive(), message: z.string().min(1), narration: z.string().min(1),
  visualVerb: visualVerbSchema, heroSubject: z.string().min(1), sceneFamilyId: z.string().min(1), layoutArchetypeId: z.string().min(1),
  layoutVariantId: z.string().min(1), typographySystemId: z.string().min(1), componentBindings: z.array(componentBindingSchema).min(1),
  motionPrimitiveIds: z.array(z.string().min(1)).min(1), transitionInId: z.string().optional(), transitionOutId: z.string().optional(),
  cameraPresetId: z.string().optional(), userAssetBindings: z.array(userAssetBindingSchema), brandTokens: brandTokenSchema,
  approvalState: z.enum(["DRAFT", "REVISION_REQUESTED", "APPROVED", "LOCKED"]), revisionVersion: z.number().int().positive(),
  approvedHash: z.string().optional(), approvedAt: z.string().optional(), approvedBy: z.string().optional(), validationWarnings: z.array(z.string()),
  factualGoal: z.string().optional(), semanticMessage: z.string().optional(), supportingFactIds: z.array(z.string()).optional(), narrativeRole: z.string().optional(),
  visualConcept: z.string().optional(), visualDirection: z.record(z.string(), z.unknown()).optional(), purpose: z.string().optional(),
  productionContentContract: z.object({ version: z.string(), bound: z.boolean(), demoContentAllowed: z.boolean(), meaningfulRelation: z.string(), contentSlots: z.record(z.string(), z.object({ required: z.boolean(), type: z.string().optional(), demoOnly: z.boolean().optional() })).optional() }).optional(),
  visualConstruction: visualConstructionSchema.optional(), visualDominance: z.string().optional(), styleProfile: z.record(z.string(), z.unknown()).optional(), motionIntent: z.record(z.string(), z.unknown()).optional(), continuityObjectId: z.string().optional(), continuityState: z.string().optional(), motionDirection: motionDirectionSchema.optional(),
});

export const videoSpecSchema = z.object({
  id: z.string().min(1), productionId: z.string().min(1), storySpecId: z.string().min(1), directorPlan: directorPlanSchema,
  scenes: z.array(scenePlanSchema).min(5).max(6), durationSec: z.number().positive(), aspectRatio: aspectRatioSchema, brandTokens: brandTokenSchema,
  voiceTiming: z.array(z.object({ sceneId: z.string(), startSec: z.number().nonnegative(), durationSec: z.number().positive(), text: z.string(), status: z.enum(["placeholder", "measured"]) })),
  soundSchedule: z.array(z.object({ sceneId: z.string(), soundId: z.string(), action: z.string(), startSec: z.number().nonnegative(), volume: z.number().min(0).max(1), sourceFilename: z.string(), sourceHash: z.string() })),
  outputFormats: z.array(z.enum(["draft", "standard", "high"])), validationVersion: z.string(), libraryVersion: z.string(), compilerVersion: z.string(), frozenAt: z.string(), contentHash: z.string(),
  motionDirectionPlans: z.array(motionDirectionSchema).optional(), continuityRegistry: z.array(z.record(z.string(), z.unknown())).optional(),
});

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => [key, stableValue(item)]));
  return value;
}

export function stableJson(value: unknown): string {
  return JSON.stringify(stableValue(value));
}

export function hashJson(value: unknown): string {
  return createHash("sha256").update(stableJson(value)).digest("hex");
}

export function approvedScenePayload(scene: ScenePlan): Omit<ScenePlan, "approvalState" | "approvedHash" | "approvedAt" | "approvedBy"> {
  const { approvalState: _approvalState, approvedHash: _approvedHash, approvedAt: _approvedAt, approvedBy: _approvedBy, ...payload } = scene;
  return payload;
}

export function hashApprovedScene(scene: ScenePlan): string {
  return hashJson(approvedScenePayload(scene));
}

export function videoSpecPayload(spec: VideoSpec): Omit<VideoSpec, "contentHash"> {
  const { contentHash: _contentHash, ...payload } = spec;
  return payload;
}

export function hashVideoSpec(spec: VideoSpec): string {
  return hashJson(videoSpecPayload(spec));
}
