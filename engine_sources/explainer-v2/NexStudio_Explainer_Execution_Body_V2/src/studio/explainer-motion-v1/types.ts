import type { CompositionBundle } from "@/hyperframes/types";

export const EXPLAINER_LIBRARY_VERSION = "3.0.0-rc1" as const;
export const EXPLAINER_COMPILER_VERSION = "explainer-motion-compiler-1.0.0" as const;
export const EXPLAINER_PACKAGE_VERSION = "1.0.0" as const;
export const EXPLAINER_FRAME_RATE = 30 as const;
export const MOTION_CRAFT_ENGINE_VERSION = "explainer-motion-craft.v1" as const;

export type ProductionMode = "product-library" | "explainer-library" | "documentary-library" | "bespoke-runtime";
export type AspectRatio = "16:9" | "1:1" | "9:16";
export type MotionEnergy = "low" | "medium" | "high";
export type InformationDensity = "low" | "medium" | "high";
export type SceneApprovalState = "DRAFT" | "REVISION_REQUESTED" | "APPROVED" | "LOCKED";
export type VisualVerb =
  | "Reveal"
  | "Extract"
  | "Split"
  | "Merge"
  | "Transform"
  | "Assemble"
  | "Route"
  | "Compare"
  | "Rank"
  | "Filter"
  | "Expand"
  | "Collapse"
  | "Scan"
  | "Detect"
  | "Repair"
  | "Validate"
  | "Package"
  | "Deliver"
  | "Connect"
  | "Multiply"
  | "Convert"
  | "Grow"
  | "Unfold"
  | "Branch"
  | "Emerge"
  | "Absorb"
  | "Flow"
  | "Illuminate"
  | "Accumulate"
  | "Circulate";

export type StoryPurpose =
  | "hook"
  | "context"
  | "problem"
  | "concept"
  | "how-it-works"
  | "proof"
  | "validation"
  | "outcome"
  | "cta";

export type ExplainerIntentType =
  | "educational-process"
  | "concept-explanation"
  | "mechanism"
  | "problem-solution"
  | "comparison"
  | "historical-story"
  | "investigation"
  | "product-explainer"
  | "data-analysis"
  | "how-to"
  | "persuasion"
  | "announcement";

export type ExplainerKnowledgeMode = "user-evidence" | "verified-general-knowledge" | "research-backed" | "mixed";

export type ExplainerFact = {
  id: string;
  statement: string;
  domain: string;
  sourceMode: ExplainerKnowledgeMode;
  confidence: "high" | "medium" | "low";
  supports: string[];
};

export type ExplainerKnowledgePack = {
  version: string;
  topic: string;
  domain: string;
  mode: ExplainerKnowledgeMode;
  facts: ExplainerFact[];
  limitations: string[];
  requiresResearch: boolean;
};

export type ExplainerVisualDirection = {
  visualVerb: string;
  heroSubject: string;
  startingState: string;
  transformation: string;
  endingState: string;
  spatialRelationship: string;
  continuityObject?: string;
  energy: string;
};

export type VisualEntityType = "object" | "substance" | "growth-structure" | "environment" | "energy" | "signal" | "container" | "state";
export type VisualClass = "geometric-object" | "organic-object" | "attached-surface" | "linear-path" | "organic-path" | "branching-path" | "particle" | "field" | "container" | "node" | "connector" | "icon" | "illustration" | "media" | "document" | "data-series" | "label" | "group" | "environment" | "transfer-object";
export type VisualRepresentation = "circle" | "ellipse" | "organic-blob" | "seed" | "line" | "curved-line" | "arrow" | "dotted-path" | "branch" | "stem" | "leaf" | "droplet" | "sun" | "sun-ray" | "cloud" | "soil-layer" | "ground-line" | "node" | "container" | "document" | "token" | "block" | "tool" | "label" | "particle" | "glow" | "connector";
export type VisualEntityImportance = "hero" | "hero-supporting" | "supporting" | "annotation";
export type GeometryPoint = { x: number; y: number };
export type ArtDirectedPath = {
  d: string;
  role?: string;
  continuityRole?: "existing" | "new";
  strokeWidth?: number;
  stroke?: string;
  fill?: string;
  opacity?: number;
};
export type ArtDirectedGeometryItem = {
  x: number;
  y: number;
  width?: number;
  height?: number;
  rotation?: number;
  scale?: number;
  anchor?: GeometryPoint;
  pivot?: GeometryPoint;
  label?: string;
  continuityRole?: "existing" | "new";
};
export type ArtDirectedEntityGeometry = {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  rotation?: number;
  scale?: number;
  count?: number;
  curvature?: number;
  branchCount?: number;
  strokeWidth?: number;
  stroke?: string;
  fill?: string;
  opacity?: number;
  paths?: ArtDirectedPath[];
  items?: ArtDirectedGeometryItem[];
  anchors?: Record<string, GeometryPoint>;
  showLabel?: boolean;
  visible?: boolean;
};
export type ProductionRenderBinding = {
  kind: "AUTHORED_SVG" | "CHARACTER_SKIN" | "ENVIRONMENT_SVG" | "PROP_SVG";
  assetId: string;
  sourcePath: string;
  license: "MIT" | "CC0" | "INTERNAL";
  family: string;
  normalizedStyleFamily: "nexstudio-authored-cartoon-v1";
  semanticTags: string[];
  /** Scene-scoped deterministic vector body. The semantic decision still comes from P8; this field only carries body pixels. */
  inlineSvg?: string;
  performanceAuthority?: "NEXSTICK_V5_1";
  characterSpec?: {
    familyId: "adult_man_average" | "adult_woman_average" | "boy" | "girl" | "neutral_adult" | "neutral_child";
    personality: "calm" | "cheerful" | "confident" | "shy" | "energetic" | "serious" | "playful" | "authoritative" | "warm" | "reserved";
    roleTags: string[];
    skin: "NEXSTICK_AUTHORED_SURFACE_V1";
  };
  performanceSequence?: {
    source: "NEXSTICK_V5_1";
    engineVersion: string;
    action: string;
    durationSec: number;
    frames: Array<{ t: number; dataUrl: string }>;
  };
  dataUrl?: string;
};
export type VisualEntity = {
  id: string;
  type: VisualEntityType;
  semanticType: string;
  importance: VisualEntityImportance;
  continuity?: boolean;
  visualClass?: VisualClass;
  representation?: VisualRepresentation;
  label?: string;
  capabilities?: string[];
  geometry?: ArtDirectedEntityGeometry;
  renderBinding?: ProductionRenderBinding;
};
export type VisualRelationshipKind = "enters" | "exits" | "flows-to" | "grows-from" | "branches-from" | "points-to" | "surrounds" | "transforms-into" | "feeds" | "absorbs" | "produces" | "splits-into" | "merges-into" | "travels-through" | "rotates-around" | "accumulates-in" | "reveals" | "replaces" | "attaches-to" | "detaches-from" | "orients-toward" | "validates" | "passes-to" | "routes-to" | "compares-with" | "blocks" | "unlocks";
export type VisualRelationship = {
  from: string;
  to: string;
  kind: VisualRelationshipKind;
  direction?: "up" | "down" | "left" | "right" | "inward" | "outward" | "clockwise" | "counterclockwise";
  emphasis?: "primary" | "secondary";
};
export type VisualTransformation = {
  fromState: string;
  toState: string;
  action: string;
  progress?: number;
};
export type ContinuityInstruction = {
  objectId: string;
  previousState?: string;
  state: string;
  nextState?: string;
  handoff: string;
  preserveFeatures?: string[];
};
export type SpatialGrammar = "sequential-transformation" | "sequential-growth" | "directional-split" | "branching" | "converging-inputs" | "diverging-outputs" | "linear-flow" | "network-flow" | "cycle" | "layered-cutaway" | "layer-cutaway" | "assembly" | "comparison" | "cause-and-effect" | "reveal" | "transformation" | "journey-path" | "orbit" | "accumulation" | "hero-transform" | "freeform";
export type LabelStrategy = "minimal" | "diagram-essential" | "callout" | "none";
export type ConstructionMode = "existing-component" | "primitive-composition" | "diagram" | "illustration-composition" | "media" | "hybrid";
export type VisualDominanceMode = "typography-led" | "illustration-led" | "diagram-led" | "media-led" | "data-led" | "workflow-led" | "hybrid";
export type VisualStyleProfile = {
  primaryVisualLanguage: "paper-motion" | "modern-illustration" | "photographic" | "ui-product" | "diagrammatic" | "mixed-hybrid";
  secondaryVisualLanguage: "illustrated" | "diagrammatic" | "typographic" | "photographic";
  photographyPolicy: "avoid-unless-evidence" | "preferred" | "allowed";
  depth: "flat" | "light" | "layered";
  strokeStyle: "bold-clean" | "fine-technical" | "none";
  shapeStyle: "organic-geometric" | "geometric" | "editorial";
  motionEnergy: string;
};
export type VisualMotionIntent = {
  entryState: string;
  mainAction: string;
  settledState: string;
  exitTransformation: string;
  continuityHandoff: string;
};

export type ArtCompositionArchetype = "hero-centered" | "hero-with-negative-space" | "vertical-growth" | "horizontal-journey" | "cutaway" | "converging-inputs" | "branching-system" | "central-transformation" | "before-after" | "comparison" | "macro-detail" | "wide-reveal" | "layered-environment";
export type ArtPlacementIntent = "center" | "upper-left" | "upper-center" | "upper-right" | "middle-left" | "middle-right" | "lower-left" | "lower-center" | "lower-right" | "around-hero" | "along-path" | "attached-to-parent" | "environment-layer";
export type ArtRegionIntent = "full-frame" | "upper-band" | "lower-band" | "left-third" | "center-third" | "right-third" | "upper-left" | "upper-right" | "lower-left" | "lower-right" | "hero-adjacent" | "below-ground" | "above-ground";
export type ArtFormIntent = "upright" | "balanced" | "leaning" | "compact" | "expanded" | "symmetrical" | "asymmetric" | "radial" | "branching" | "layered";
export type ArtDirectionEntityParameter = {
  entityId: string;
  maturity?: "nascent" | "early" | "developing" | "established" | "developed";
  scaleIntent?: "tiny" | "small" | "medium" | "large" | "heroic";
  orientation?: "up" | "down" | "left" | "right" | "inward" | "outward" | "radial";
  form?: ArtFormIntent;
  branchingComplexity?: "none" | "low" | "moderate" | "high";
  curvature?: "straight" | "gentle" | "organic" | "pronounced";
  density?: "sparse" | "moderate" | "dense";
  count?: number;
  visibility?: "hidden" | "suggested" | "clear" | "heroic";
  state?: string;
};
export type ArtDirectionPlan = {
  id: string;
  sceneId: string;
  version: string;
  visualDominance: VisualDominanceMode;
  compositionArchetype: ArtCompositionArchetype;
  hero: { entityId: string; prominence: number; placementIntent: ArtPlacementIntent; silhouetteIntent?: ArtFormIntent };
  supportingRoles: Array<{ entityId: string; role: "context" | "counterweight" | "input" | "output" | "attached-child" | "environment" | "annotation" | "continuity-support"; placementIntent: ArtPlacementIntent; relativeTo?: string; emphasis: "primary" | "secondary" | "quiet" }>;
  balance: { horizontal: "centered" | "left-weighted" | "right-weighted" | "distributed"; vertical: "centered" | "top-weighted" | "bottom-weighted" | "split"; asymmetry: "none" | "restrained" | "expressive" };
  negativeSpace: { intent: "minimal" | "title-space" | "process-lanes" | "breathing-room" | "comparison-gap"; preferredRegion?: ArtRegionIntent };
  environment: { visibility: "hidden" | "suggested" | "clear" | "cutaway"; relevantRegions: ArtRegionIntent[]; splitIntent?: "shallow" | "balanced" | "deep" };
  framing: { shotSize: "macro" | "close" | "medium" | "wide"; focalEntity: string; cropPolicy: "contain-complete-subject" | "allow-context-crop" | "protect-attachments" | "protect-environment-split" };
  typography: { treatment: VisualTitleTreatment; prominence: "primary" | "secondary" | "quiet"; preferredRegion?: ArtRegionIntent };
  continuityTransform: { preserveIdentity: boolean; allowGrowth: boolean; allowReorientation: boolean; allowMorph: boolean };
  aestheticConstraints: ArtFormIntent[];
  stateParameters: ArtDirectionEntityParameter[];
  qualityIntent: { silhouette: "clean" | "distinct" | "expressive"; readability: "immediate" | "guided" | "detailed"; density: "sparse" | "balanced" | "rich" };
  rationale: string;
};

/** Resolved art state is deterministic geometry produced from ArtDirectionPlan.
 * NexMind never authors these viewport coordinates in the normal pipeline. */
export type ArtDirectionQuality = {
  heroScale: number;
  visualBalance: string;
  silhouetteQuality: string;
  negativeSpaceIntent: string;
  subjectReadability: string;
  attachmentQuality: string;
};
export type VisualGeometryState = {
  id: string;
  label?: string;
  entities: Record<string, ArtDirectedEntityGeometry>;
  quality: ArtDirectionQuality;
  metrics?: Record<string, number>;
  resultPersistenceFrames?: number;
};
export type NormalizedArtRegion = { x: number; y: number; width: number; height: number };
export type ResolvedArtState = VisualGeometryState & {
  sceneId: string;
  planId: string;
  compositionArchetype: ArtCompositionArchetype;
  viewport: { width: number; height: number; aspectRatio: string };
  regions: Record<string, NormalizedArtRegion>;
};
export type ContinuityTransformInstruction = {
  fromStateId: string;
  toStateId: string;
  anchorCorrespondence: Array<{ fromEntityId: string; toEntityId: string; fromAnchor?: string; toAnchor?: string }>;
  durationFrames: number;
  easingProfile: SemanticMotionAction["easingProfile"];
};
export type VisualTitleTreatment = "integrated-headline" | "anchored-label" | "temporary-overlay";
export type VisualSurfaceDirection = {
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  radius?: number;
  opacity?: number;
};
export type VisualArtDirection = {
  planId?: string;
  resolvedBy?: string;
  activeStateId: string;
  states: ResolvedArtState[];
  continuityTransform?: ContinuityTransformInstruction;
  titleTreatment: VisualTitleTreatment;
  typographyProminence?: ArtDirectionPlan["typography"]["prominence"];
  typographyRegion?: NormalizedArtRegion;
  cameraCrop?: { focalEntity: string; safeRegion: NormalizedArtRegion; shotSize: ArtDirectionPlan["framing"]["shotSize"]; cropPolicy: ArtDirectionPlan["framing"]["cropPolicy"] };
  surface?: VisualSurfaceDirection;
  resultPersistenceFrames: number;
  cameraActionExpected?: boolean;
  cameraTargetTrackingErrorMax?: number;
};

export type SemanticMotionActionName =
  | "enter" | "exit" | "reveal" | "grow" | "shrink" | "extend" | "retract"
  | "branch" | "split" | "merge" | "absorb" | "flow" | "travel" | "fall" | "rise"
  | "rotate" | "orient-toward" | "open" | "close" | "unfold" | "pulse" | "accumulate"
  | "transform" | "connect" | "disconnect" | "highlight" | "scan" | "transfer"
  | "assemble" | "disperse" | "replace" | "validate";

export type MotionState = {
  id: string;
  description: string;
  visibleEntities: string[];
  continuityState?: string;
};

export type SemanticMotionAction = {
  id: string;
  action: SemanticMotionActionName;
  actor: string;
  target?: string;
  source?: string;
  relationship?: VisualRelationshipKind | "causes" | "responds-to";
  direction?: "up" | "down" | "left" | "right" | "inward" | "outward" | "clockwise" | "counterclockwise";
  startState: string;
  endState: string;
  startSec: number;
  durationSec: number;
  priority: "primary" | "secondary" | "ambient";
  chainAfter?: string;
  easingProfile: "precise" | "educational" | "playful" | "energetic" | "technical" | "calm" | "organic-controlled";
};

export type CameraDirection = {
  action: "hold" | "gentle-push" | "pull-back" | "follow-object" | "pan-along-path" | "reframe" | "macro-focus" | "ecosystem-reveal" | "focus-transfer" | "depth-parallax";
  target: string;
  reason: string;
  startSec: number;
  durationSec: number;
  scaleFrom?: number;
  scaleTo?: number;
  translateXPercent?: number;
  translateYPercent?: number;
};

export type SemanticTransitionFamily = "object-continuation" | "object-transformation" | "camera-follow" | "path-continuation" | "shape-match" | "focus-transfer" | "environmental-reveal" | "typography-to-visual";
export type TransitionDirection = {
  family: SemanticTransitionFamily;
  continuityObjectId?: string;
  fromState?: string;
  toState?: string;
  durationSec: number;
  reason: string;
};

export type ReducedMotionDirection = {
  strategy: "settled-state-cuts" | "short-opacity-reveal" | "essential-path-only";
  preserveActions: string[];
  suppressActions: string[];
};

export type MotionDirectionPlan = {
  sceneId: string;
  entryState: MotionState;
  actions: SemanticMotionAction[];
  cameraPlan: CameraDirection;
  transitionIn?: TransitionDirection;
  transitionOut?: TransitionDirection;
  continuityObject?: { id: string; incomingState: string; outgoingState: string };
  settledStoryboardState: number;
  emotionalEnergy: string;
  motionDensity: "minimal" | "moderate" | "active";
  reducedMotionPlan: ReducedMotionDirection;
};

export type MotionPerformanceVariant =
  | "organic-path-grow"
  | "linear-extension"
  | "staggered-branch"
  | "anchor-flow"
  | "receiver-absorb"
  | "pivot-unfold"
  | "target-orient"
  | "causal-reveal"
  | "scale-settle"
  | "pulse-response"
  | "precise-transfer"
  | "assemble-highlight"
  | "continuity-transform"
  | "attached-unfold"
  | "flow-to"
  | "positive-growth-delta"
  | "cause-and-effect-performance"
  | "target-follow-camera"
  | "converging-inputs";

export type MotionAnchorName = "center" | "top" | "bottom" | "left" | "right" | "entry" | "exit" | "growth-origin" | "branch-origin" | "attachment" | "focus";

export type MotionPerformance = {
  id: string;
  actionId: string;
  action: SemanticMotionActionName;
  actor: string;
  target?: string;
  variant: MotionPerformanceVariant;
  startFrame: number;
  endFrame: number;
  durationFrames: number;
  easingProfile: SemanticMotionAction["easingProfile"];
  sourceAnchor?: MotionAnchorName;
  targetAnchor?: MotionAnchorName;
  prerequisiteIds: string[];
  affectedEntities: string[];
  quality: {
    continuitySupport: "none" | "preserve" | "transform";
    cameraCompatible: boolean;
    reducedMotion: "settled-state" | "essential-path" | "short-reveal";
    resultPersistenceFrames: number;
  };
  mechanism?: MotionPerformanceVariant;
};

export type ContinuityBridge = {
  continuityId: string;
  fromSceneId: string;
  toSceneId: string;
  sourceState: string;
  destinationState: string;
  strategy: "preserve" | "transform" | "camera-follow" | "scale-match" | "path-continue" | "reframe";
  bridgeDurationFrames: number;
};

export type CameraPerformance = {
  action: CameraDirection["action"];
  target: string;
  reason: string;
  startFrame: number;
  endFrame: number;
  durationFrames: number;
  easingProfile: SemanticMotionAction["easingProfile"];
  scaleFrom: number;
  scaleTo: number;
  translateXPercent: number;
  translateYPercent: number;
  safeFocalRegion: { xMin: number; xMax: number; yMin: number; yMax: number };
  cameraContinuity: boolean;
  cameraActionExpected: boolean;
  cameraActionExecuted: boolean;
  cameraTravelDistance: number;
  cameraTargetTrackingError: number;
};

export type TransitionPerformance = {
  family: SemanticTransitionFamily;
  durationFrames: number;
  easingProfile: SemanticMotionAction["easingProfile"];
  continuityDriven: boolean;
  reason: string;
};

export type MotionPerformancePlan = {
  version: typeof MOTION_CRAFT_ENGINE_VERSION;
  sceneId: string;
  frameRate: number;
  durationFrames: number;
  performances: MotionPerformance[];
  continuityBridges: ContinuityBridge[];
  cameraPerformance: CameraPerformance;
  transitionPerformance?: TransitionPerformance;
  typographyPerformances: Array<{ role: "headline" | "label" | "body"; mode: "quiet-reveal" | "emphasis" | "recede"; startFrame: number; endFrame: number }>;
  eventGraph: Array<{ id: string; prerequisiteIds: string[]; startFrame: number; endFrame: number; affectedEntities: string[] }>;
  reducedMotion: { strategy: ReducedMotionDirection["strategy"]; preservePerformanceIds: string[] };
  creativeMechanisms: MotionPerformanceVariant[];
  resultPersistenceFrames: number;
};

export type ContinuityObjectState = {
  continuityId: string;
  sceneId: string;
  stateId: string;
  geometryState: Record<string, unknown>;
  transformState: Record<string, unknown>;
  visualState: Record<string, unknown>;
  anchors?: Record<string, { x: number; y: number }>;
  geometrySnapshot?: Record<string, unknown>;
};

export type MotionCapabilityMetadata = {
  entityType: VisualEntityType | "typography" | "media" | "data" | "workflow" | "path";
  capabilities: Array<"growable" | "path-drawable" | "rotatable" | "orientable" | "flow-target" | "flow-source" | "branchable" | "transformable" | "continuity-capable">;
};
export type NexArtSpecialistRole = "CHARACTER" | "WHITEBOARD" | "OBJECT_PROP" | "ENVIRONMENT_SCENE" | "DIAGRAM" | "INTERACTION_POSE" | "ASSET_ASSIMILATION";
export type ProductionArtSystem = "CHARACTER_SKIN" | "WHITEBOARD_DRAWING" | "ENVIRONMENT_CONSTRUCTOR" | "OBJECT_PROP_CONSTRUCTOR" | "SCENE_COMPOSER" | "STYLE_GRAMMAR" | "EXECUTION_FIDELITY_CHECK";
export type CommercialExecutionTier = "PREMIUM_NATIVE" | "PREMIUM_COMPOSED" | "SUPPORT_ONLY" | "UNAVAILABLE";
export type ProductionArtExecutionLayer = {
  id: string;
  role: "background" | "midground" | "foreground";
  semanticPurpose: string;
  source: "EXECUTION_BODY_CONSTRUCTOR" | "PRODUCTION_SCOPED_AUTHORED_ART";
  commercialTier: "PREMIUM_COMPOSED" | "SUPPORT_ONLY";
  geometry: ArtDirectedEntityGeometry;
  renderBinding: ProductionRenderBinding;
};
export type ProductionArtCommercialCapability = {
  character: CommercialExecutionTier;
  environment: CommercialExecutionTier;
  objectProp: CommercialExecutionTier;
  reasons: string[];
  replanRequired: boolean;
};
export type ReferenceLanguageProfile = {
  version: "reference-language.v1";
  sourceIds: string[];
  sourceKinds: string[];
  frameCount: number;
  durationSec?: number;
  meanNonWhiteOccupancy: number;
  meanEdgeDensity: number;
  meanLumaStd: number;
  meanFrameDelta: number;
  whiteField: boolean;
  authoredSceneBias: number;
  densityTarget: "sparse" | "balanced" | "rich";
  textDominanceMax: number;
  minimumForegroundOccupancy: number;
  maximumDeadWhiteRatio: number;
  notes: string[];
};
export type NexArtSpecialistProposal = {
  role: NexArtSpecialistRole;
  sceneId: string;
  constructionThesis: string;
  requiredEntityIds: string[];
  sourceStrategies: Array<"APPROVED_ASSET" | "USER_ASSET" | "COMPOSED_CANONICAL" | "PROCEDURAL_DIAGRAM" | "NEXSTICK_SKIN" | "VECTOR_TRACE">;
  styleTraits: string[];
  interactionAnchors: Array<{ actor: string; anchor: string; target: string; ownershipRule: string }>;
  unsupported: string[];
  riskNotes: string[];
};
export type ProductionArtPlan = {
  version: "production-art.v2";
  sceneId: string;
  visualMode: "AUTHORED_SCENE" | "WHITEBOARD_SCENE" | "DIAGRAM" | "MEDIA" | "HYBRID_ILLUSTRATION";
  requiredSystems: ProductionArtSystem[];
  specialistRoles: NexArtSpecialistRole[];
  specialistProposals: NexArtSpecialistProposal[];
  characterPerformanceRequired: boolean;
  environmentRequired: boolean;
  objectConstructionRequired: boolean;
  coherentWorldRequired: boolean;
  diagramFallbackAllowed: boolean;
  rawRigVisibleAllowed: false;
  textMustBeSubordinate: boolean;
  referenceLanguage?: ReferenceLanguageProfile;
  densityTarget: "sparse" | "balanced" | "rich";
  minimumForegroundOccupancy: number;
  maximumDeadWhiteRatio: number;
  styleSignature: string[];
  executionLayers: ProductionArtExecutionLayer[];
  productionScopedAuthoredPlate?: { lockedSemanticsHash: string; semanticBindings: Array<{ semantic_ref: string; role?: string }>; stageCount: number; };
  commercialCapability: ProductionArtCommercialCapability;
  sceneComposition: {
    foregroundRequired: boolean;
    midgroundRequired: boolean;
    backgroundRequired: boolean;
    interactionStagingRequired: boolean;
    negativeSpaceIntent: string;
    estimatedForegroundOccupancy: number;
    worldLayerCount: number;
    interactionPairCount: number;
    compositionBlockers: string[];
  };
  motionAuthority: "NEXMIND_MOTION_DIRECTOR";
  characterMotionAuthority?: "NEXSTICK_V5_1";
  releaseGate: "EXECUTION_FIDELITY_REQUIRED";
  status: "READY_FOR_RENDER" | "BLOCKED";
  blockers: string[];
};

export type VisualConstructionPlan = {
  sceneId: string;
  semanticGoal: string;
  heroEntity: VisualEntity;
  supportingEntities: VisualEntity[];
  relationships: VisualRelationship[];
  transformation?: VisualTransformation;
  continuity?: ContinuityInstruction;
  spatialGrammar: SpatialGrammar;
  labelStrategy: LabelStrategy;
  constructionMode: ConstructionMode;
  requiredCapabilities: string[];
  optionalCapabilities: string[];
  dominanceMode: VisualDominanceMode;
  styleProfile: VisualStyleProfile;
  motionIntent: VisualMotionIntent;
  artDirectionPlan?: ArtDirectionPlan;
  artDirection?: VisualArtDirection;
  constructionId?: string;
  visualCoverage?: "covered" | "VISUAL_COVERAGE_GAP";
  directorContractVersion?: string;
  visualGrammarVersion?: string;
  coverageDecision?: "reuse-component" | "primitive-construction" | "semantic-diagram" | "production-scoped-asset" | "user-media" | "VISUAL_COVERAGE_GAP";
  assetRequirement?: { type: "illustration" | "media"; subject: string; view: string; style: string; background: string; purpose: string; sceneId: string };
  productionScopedArt?: {
    schema: "NexStudioAuthoredScenePlateBindingV1";
    lockedSemanticsHash: string;
    semanticBindings: Array<{ semantic_ref: string; role?: string }>;
    finalPngDataUrl: string;
    stageCount: number;
    creativeChoiceIntroduced: false;
  };
  /** Exact P8 execution commitments. These are execution inputs, not creative hints. */
  p8MotionActions?: Array<Record<string, unknown>>;
  p8CameraAtom?: Record<string, unknown>;
  p8BrandExecutionHash?: string;
  productionArt?: ProductionArtPlan;
};

export type ExplainerComponentHints = {
  sceneFamily?: string;
  typography?: string;
  media?: string;
  data?: string;
  workflow?: string;
  icon?: string;
};

export type StoryBeat = {
  id: string;
  order: number;
  purpose: StoryPurpose;
  message: string;
  narration: string;
  durationSec: number;
  factualGoal?: string;
  semanticMessage?: string;
  supportingFactIds?: string[];
  narrativeRole?: string;
  visualDirection?: ExplainerVisualDirection;
  visualVerb?: VisualVerb;
  componentHints?: ExplainerComponentHints;
  componentContent?: Record<string, unknown>;
};

export type StorySpec = {
  id: string;
  productionId: string;
  title: string;
  durationSec: number;
  sceneCount: number;
  audience: string;
  goal: string;
  coreMessage: string;
  tone: string;
  aspectRatio: AspectRatio;
  beats: StoryBeat[];
  version: string;
  rawRequest?: string;
  intent?: {
    topic: string;
    intentType: ExplainerIntentType;
    knowledgeDomain: string;
    requiresProblem: boolean;
    requiresChronology: boolean;
    requiresMechanism: boolean;
    requiresComparison: boolean;
    requiresProductProof: boolean;
    requiresCTA: boolean;
  };
  grammar?: string;
  knowledgePack?: ExplainerKnowledgePack;
};

export type DirectorScenePlan = {
  sceneId: string;
  storyFunction: string;
  visualVerb: VisualVerb;
  heroSubject: string;
  supportingSubjects: string[];
  layoutIntent: string;
  informationDensity: InformationDensity;
  cameraIntent: string;
  transitionIntent: string;
  copyBudget: number;
  emotionalEnergy: string;
  continuityKey: string;
  visualConcept?: string;
  visualDirection?: ExplainerVisualDirection;
  continuityObject?: string;
  componentHints?: ExplainerComponentHints;
  visualConstruction?: VisualConstructionPlan;
  visualDominance?: VisualDominanceMode;
  styleProfile?: VisualStyleProfile;
  motionIntent?: VisualMotionIntent;
};

export type DirectorPlan = {
  storySpecId: string;
  productionId: string;
  scenes: DirectorScenePlan[];
  version: string;
};

export type ComponentBinding = {
  slot: "hero" | "supporting" | "typography" | "data" | "workflow" | "icon" | "media";
  componentId: string;
  content: Record<string, unknown>;
};

/** Browser-measured geometry for a mounted component. Slot allocation is deliberately
 * kept separate from the component's meaningful pixels and text. */
export type RenderedRect = {
  x: number;
  y: number;
  width: number;
  height: number;
  right?: number;
  bottom?: number;
};

export type RenderedComponentMetrics = {
  componentId?: string;
  slot: string;
  slotBounds: RenderedRect;
  rootBounds: RenderedRect;
  meaningfulBounds: RenderedRect | null;
  textBounds: RenderedRect[];
  scale: number;
  effectiveScaleX: number;
  effectiveScaleY: number;
};

export type RenderedTypographyMetrics = {
  text: string;
  renderedLines: string[];
  wordIntegrity: boolean;
  overflow: boolean;
  minimumFontSizePass: boolean;
  readable: boolean;
};

export type UserAssetBinding = {
  slot: string;
  assetId: string;
  sourceId?: string;
  mediaType?: string;
  cropMode?: "cover" | "contain" | "fill";
  focalPoint?: { x: number; y: number };
};

export type BrandTokenSet = {
  paperBg: string;
  paperSurface: string;
  ink: string;
  inkMuted: string;
  primary: string;
  secondary: string;
  accent: string;
  highlight: string;
  typographyStyle: string;
};

export type ScenePlan = {
  id: string;
  productionId: string;
  storyBeatId: string;
  order: number;
  startSec: number;
  durationSec: number;
  message: string;
  narration: string;
  visualVerb: VisualVerb;
  heroSubject: string;
  sceneFamilyId: string;
  layoutArchetypeId: string;
  layoutVariantId: string;
  typographySystemId: string;
  componentBindings: ComponentBinding[];
  motionPrimitiveIds: string[];
  transitionInId?: string;
  transitionOutId?: string;
  cameraPresetId?: string;
  userAssetBindings: UserAssetBinding[];
  brandTokens: BrandTokenSet;
  approvalState: SceneApprovalState;
  revisionVersion: number;
  approvedHash?: string;
  approvedAt?: string;
  approvedBy?: string;
  validationWarnings: string[];
  factualGoal?: string;
  semanticMessage?: string;
  supportingFactIds?: string[];
  narrativeRole?: string;
  visualConcept?: string;
  visualDirection?: ExplainerVisualDirection;
  purpose?: string;
  productionContentContract?: {
    version: string;
    bound: boolean;
    demoContentAllowed: boolean;
    meaningfulRelation: string;
    contentSlots?: Record<string, { required: boolean; type?: string; demoOnly?: boolean }>;
  };
  visualConstruction?: VisualConstructionPlan;
  visualDominance?: VisualDominanceMode;
  styleProfile?: VisualStyleProfile;
  motionIntent?: VisualMotionIntent;
  continuityObjectId?: string;
  continuityState?: string;
  motionDirection?: MotionDirectionPlan;
};

export type VoiceTiming = {
  sceneId: string;
  startSec: number;
  durationSec: number;
  text: string;
  status: "placeholder" | "measured";
};

export type SoundScheduleItem = {
  sceneId: string;
  soundId: string;
  action: string;
  startSec: number;
  volume: number;
  sourceFilename: string;
  sourceHash: string;
};

export type VideoSpec = {
  id: string;
  productionId: string;
  storySpecId: string;
  directorPlan: DirectorPlan;
  scenes: ScenePlan[];
  durationSec: number;
  aspectRatio: AspectRatio;
  brandTokens: BrandTokenSet;
  voiceTiming: VoiceTiming[];
  soundSchedule: SoundScheduleItem[];
  outputFormats: Array<"draft" | "standard" | "high">;
  validationVersion: string;
  libraryVersion: string;
  compilerVersion: string;
  frozenAt: string;
  contentHash: string;
  frameRate?: number;
  motionCraftVersion?: typeof MOTION_CRAFT_ENGINE_VERSION;
  motionDirectionPlans?: MotionDirectionPlan[];
  continuityRegistry?: ContinuityObjectState[];
};

export type FrozenVideoSpec = Readonly<VideoSpec>;

export type RegistryEntry = {
  id: string;
  name?: string;
  version: string;
  category: string;
  subtype?: string;
  slug?: string;
  order?: number;
  intents?: string[];
  keywords?: string[];
  paperStyles?: string[];
  aspectRatios?: AspectRatio[];
  slots?: Record<string, unknown>;
  duration?: { minimum?: number; recommended?: number; maximum?: number };
  motionEnergy?: MotionEnergy[];
  compatibleMotions?: string[];
  compatibleTransitions?: string[];
  defaultMotion?: string;
  soundTags?: string[];
  themeTokens?: string[];
  accessibilityLabel?: string;
  manifestPath: string;
  sourcePath: string;
  registryPath: string;
  previewPath: string;
  availability?: {
    manifest?: boolean;
    source?: boolean;
    preview?: boolean;
    reusable?: boolean;
    editoriallyApproved?: boolean;
  };
  approvedComponents?: Record<string, string>;
  layoutVariants?: Array<{ id: string; name?: string; layout?: string }>;
  [key: string]: unknown;
};

export type ResolvedRegistryEntry = RegistryEntry & {
  absoluteManifestPath: string;
  absoluteSourcePath: string;
  absoluteRegistryPath: string;
  absolutePreviewPath: string;
};

export type RegistryReconciliation = {
  release: string;
  totalEntries: number;
  duplicateIds: string[];
  missingManifestMappings: string[];
  missingSourceMappings: string[];
  missingPreviewMappings: string[];
  unsupportedAspectRatioEntries: string[];
  categoryCounts: Record<string, number>;
};

export type ExplainerRegistry = {
  release: typeof EXPLAINER_LIBRARY_VERSION;
  entries: ResolvedRegistryEntry[];
  byId: ReadonlyMap<string, ResolvedRegistryEntry>;
  byCategory: ReadonlyMap<string, ResolvedRegistryEntry[]>;
  reconciliation: RegistryReconciliation;
  resolve(id: string): ResolvedRegistryEntry;
  has(id: string): boolean;
};

export type CompilerOptions = {
  quality?: "draft" | "standard" | "high";
  buildTimestamp?: string;
  includeAudio?: boolean;
  mediaAssets?: Array<{
    assetId: string;
    name?: string;
    mimeType: string;
    contentHash: string;
    bytes: Uint8Array;
  }>;
};

export type ExplainerComposition = {
  bundle: CompositionBundle;
  scenePlans: ScenePlan[];
  previewHtml: string;
  compositionHash: string;
  sourceHash: string;
};

export type PlanningFailureCode =
  | "DIRECTOR_PLAN_FAILED"
  | "SCENE_SELECTION_FAILED"
  | "MEDIA_BINDING_FAILED"
  | "SCENE_COMPILATION_FAILED"
  | "EXPLAINER_APPROVAL_GATE_FAILED"
  | "VIDEOSPEC_FREEZE_FAILED"
  | "EXPLAINER_LIBRARY_QA_FAILED";
