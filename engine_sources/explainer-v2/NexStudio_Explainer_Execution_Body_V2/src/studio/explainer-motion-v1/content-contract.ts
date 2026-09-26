import type { ComponentBinding, ScenePlan } from "./types";

export const DEMO_CONTENT_REGISTRY = [
  "RC1 RUNTIME PROOF", "COMPILER PROOF", "PROOF SIGNAL", "+48% FASTER", "UNTITLED", "READY", "SOURCE", "REVIEW", "RESULT",
] as const;

const STRUCTURAL_FILLER_PATTERNS = [
  /^\s*(?:here is|this is how|what you need to know)\b/i,
  /^\s*the problem is\b/i,
  /^\s*the outcome is\b/i,
  /,\s*explained\.?\s*$/i,
];

export const componentContentSlots: Record<string, Record<string, { required: boolean; type: string; demoOnly?: boolean }>> = {
  "data.data-callout.paper-01": {
    eyebrow: { required: false, type: "short-text" }, value: { required: true, type: "number-or-short-text" }, label: { required: true, type: "short-text" }, comparison: { required: false, type: "short-text" },
  },
  "data.timeline.paper-01": {
    title: { required: true, type: "short-text" }, items: { required: true, type: "ordered-labels" },
  },
  "workflow.linear-process.paper-01": {
    title: { required: true, type: "short-text" }, nodes: { required: true, type: "ordered-nodes" }, edges: { required: true, type: "connectors" },
  },
  "media.paper-framed-photograph.paper-01": {
    media: { required: false, type: "approved-asset-or-semantic-construction" }, caption: { required: false, type: "short-text" },
  },
};

function normalise(value: string) { return value.toLocaleUpperCase().replace(/\s+/g, " ").trim(); }

const NON_VIEWER_KEYS = new Set(["state", "productionContent", "mediaState", "metricKind", "dataVariant", "variant", "format", "type", "bindAsset", "demoContentAllowed", "bound", "version"]);

function flattenStrings(value: unknown, key?: string): string[] {
  if (key && NON_VIEWER_KEYS.has(key)) return [];
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap((item) => flattenStrings(item));
  if (value && typeof value === "object") return Object.entries(value as Record<string, unknown>).flatMap(([childKey, child]) => flattenStrings(child, childKey));
  return [];
}

function isNumericClaim(binding: ComponentBinding) {
  const data = binding.content.data;
  return Boolean(data && typeof data === "object" && !Array.isArray(data) && (data as Record<string, unknown>).metricKind === "metric");
}

export type ProductionContentValidation = {
  valid: boolean;
  errors: string[];
  warnings: string[];
  scenes: Array<{ sceneId: string; bound: boolean; demoStrings: string[]; fillerStrings: string[]; metricClaimMissingFact: boolean; mediaLegitimate: boolean; relevant: boolean; narrationRedundant: boolean; narrationSimilarity: number; constructionMode?: string; genericModuleOveruse?: boolean }>;
};

const COPY_STOP_WORDS = new Set(["A", "AN", "THE", "IS", "ARE", "TO", "OF", "AND", "IN", "FOR", "ON", "WITH", "FROM"]);
function copyTokens(value: string) {
  return new Set(normalise(value).replace(/[^A-Z0-9 ]+/g, " ").split(/\s+/).filter((token) => token.length > 1 && !COPY_STOP_WORDS.has(token)));
}
function copySimilarity(a: string, b: string) {
  const left = copyTokens(a), right = copyTokens(b);
  if (!left.size || !right.size) return 0;
  const intersection = [...left].filter((token) => right.has(token)).length;
  return intersection / new Set([...left, ...right]).size;
}
function narrationRedundancy(message: string, narration: string) {
  const headline = normalise(message), spoken = normalise(narration);
  if (!headline || !spoken) return { redundant: false, similarity: 0 };
  const firstSentence = spoken.split(/[.!?](?:\s|$)/, 1)[0] ?? spoken;
  const headlineRepeatedAtStart = firstSentence.startsWith(headline);
  const similarity = copySimilarity(headline, spoken);
  return { redundant: headline === spoken || similarity >= 0.78 || headlineRepeatedAtStart, similarity: Number(similarity.toFixed(3)) };
}

export function validateProductionContent(scenes: ScenePlan[]): ProductionContentValidation {
  const errors: string[] = [];
  const warnings: string[] = [];
  const sceneReports = scenes.map((scene) => {
    const contract = scene.productionContentContract;
    const bindings = scene.componentBindings;
    const allStrings = flattenStrings(bindings);
    const canonicalStoryText = normalise([
      scene.message,
      scene.narration,
      scene.semanticMessage,
      scene.factualGoal,
      scene.visualConcept,
      scene.visualDirection,
    ].filter((value): value is string => typeof value === "string").join(" "));
    const demoStrings = [...new Set(allStrings.flatMap((value) => {
      const upper = normalise(value);
      return DEMO_CONTENT_REGISTRY.filter((demo) => {
        if (!upper.includes(demo)) return false;
        // Short registry tokens can also be legitimate story vocabulary (for
        // example an AI-agent film explicitly producing a result). They are
        // allowed only when the canonical scene contract grounds that exact
        // token; unbound component defaults remain failures.
        const grounded = canonicalStoryText.includes(demo);
        return !grounded;
      });
    }))];
    const fillerStrings = [...new Set(allStrings.filter((value) => STRUCTURAL_FILLER_PATTERNS.some((pattern) => pattern.test(value))))];
    const bound = contract?.bound === true && bindings.every((binding) => binding.content.productionContent === true);
    const metricClaimMissingFact = bindings.some(isNumericClaim) && !(scene.supportingFactIds?.length);
    const mediaBinding = bindings.find((binding) => binding.slot === "media");
    const mediaLegitimate = Boolean(scene.visualConstruction || (mediaBinding && (mediaBinding.content.mediaState === "bound-user-asset" || mediaBinding.content.mediaState === "semantic-construction" || mediaBinding.content.mediaState === "VISUAL_COVERAGE_GAP" || mediaBinding.content.mediaFallback)));
    const relevant = Boolean(contract?.meaningfulRelation && scene.visualConcept && scene.semanticMessage);
    const narrationCheck = narrationRedundancy(scene.message, scene.narration);
    if (!bound) errors.push(`${scene.id}: production-content contract is not fully bound.`);
    if (demoStrings.length && !contract?.demoContentAllowed) errors.push(`${scene.id}: demo-content leakage: ${demoStrings.join(", ")}`);
    if (fillerStrings.length) errors.push(`${scene.id}: structural filler is being used as substantive content: ${fillerStrings.join(" | ")}`);
    if (metricClaimMissingFact) errors.push(`${scene.id}: numeric metric has no supporting KnowledgePack fact or user evidence.`);
    if (!mediaLegitimate) errors.push(`${scene.id}: media has no approved asset, semantic construction, or explicit coverage-gap state.`);
    if (!relevant) errors.push(`${scene.id}: component bindings are missing a meaningful semantic relation or concrete visual direction.`);
    if (narrationCheck.redundant) errors.push(`${scene.id}: narration repeats the visible message instead of adding explanation.`);
    if (bindings.some((binding) => binding.content.demoOnly === true)) errors.push(`${scene.id}: demo-only content was bound into production.`);
    const genericModuleOveruse = Boolean(scene.visualConstruction && bindings.some((binding) => binding.slot === "data" || binding.slot === "workflow") && scene.visualConstruction.dominanceMode !== "data-led" && scene.visualConstruction.dominanceMode !== "workflow-led");
    if (genericModuleOveruse) warnings.push(`${scene.id}: selected data/workflow bindings are hidden behind a semantic construction.`);
    return { sceneId: scene.id, bound, demoStrings, fillerStrings, metricClaimMissingFact, mediaLegitimate, relevant, narrationRedundant: narrationCheck.redundant, narrationSimilarity: narrationCheck.similarity, constructionMode: scene.visualConstruction?.constructionMode, genericModuleOveruse };
  });
  if (scenes.length > 1 && new Set(scenes.map((scene) => scene.semanticMessage)).size < Math.max(3, Math.floor(scenes.length / 2))) warnings.push("Narrative progression may be repetitive; inspect semantic messages.");
  return { valid: errors.length === 0, errors, warnings, scenes: sceneReports };
}

export function assertProductionContentValid(scenes: ScenePlan[]) {
  const report = validateProductionContent(scenes);
  if (!report.valid) throw new Error(`EXPLAINER_PRODUCTION_CONTENT_INVALID: ${report.errors.join(" ")}`);
  return report;
}
