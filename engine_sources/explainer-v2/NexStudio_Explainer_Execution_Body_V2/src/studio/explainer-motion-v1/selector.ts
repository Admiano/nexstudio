import type { AspectRatio, DirectorScenePlan, ExplainerRegistry, MotionEnergy, ResolvedRegistryEntry, StoryPurpose, VisualVerb } from "./types";
import { entriesFor, findComponent } from "./registry-index";

export class ExplainerSelectionError extends Error {
  readonly code = "SCENE_SELECTION_FAILED" as const;
  constructor(message: string, readonly details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ExplainerSelectionError";
  }
}

type Selection = {
  sceneFamily: ResolvedRegistryEntry;
  typography: ResolvedRegistryEntry;
  hero: ResolvedRegistryEntry;
  support: ResolvedRegistryEntry;
  data?: ResolvedRegistryEntry;
  workflow?: ResolvedRegistryEntry;
  motion: ResolvedRegistryEntry;
  transition: ResolvedRegistryEntry;
  layoutVariantId: string;
};

const familyIntents: Record<StoryPurpose, string[]> = {
  hook: ["capture_attention", "ask_question", "state_bold_claim"],
  context: ["open_chapter", "set_context", "show_timeline", "show_document"],
  problem: ["frame_problem", "compare_options", "detect_issue"],
  concept: ["define_concept", "present_solution", "introduce_feature"],
  "how-it-works": ["explain_process", "explain_system", "explain_agent_workflow", "teach_step"],
  proof: ["show_statistic", "visualise_metric", "compare_options", "show_before_after"],
  validation: ["validate_result", "show_source", "show_document", "show_statistic"],
  outcome: ["present_solution", "show_result", "show_before_after", "close_story"],
  cta: ["call_to_action", "close_story", "present_solution"],
};

const hintedFamilyIntents: Record<string, string[]> = {
  "starting-condition": ["open_chapter", "show_timeline", "compose_story_scene"],
  "stage": ["teach_step", "show_timeline", "compose_story_scene"],
  "mechanism": ["explain_process", "explain_system", "compose_story_scene"],
  "recap": ["summarise_story", "close_story", "compose_story_scene"],
  "definition": ["define_concept", "compose_story_scene"],
  "relationship": ["explain_process", "explain_system", "compose_story_scene"],
  "example": ["show_evidence", "compose_story_scene"],
};

const preferredMotionNames: Record<VisualVerb, string[]> = {
  Reveal: ["ink-reveal", "peel-reveal", "paper-slide"], Extract: ["peel-reveal", "draw-on", "paper-slide"], Split: ["open-and-close", "paper-slide", "cut-paper-pop"], Merge: ["connect", "paper-slide", "unfold"], Transform: ["unfold", "open-and-close", "ink-reveal"], Assemble: ["connect", "drop-and-settle", "paper-slide"], Route: ["connect", "node-sequence", "paper-slide"], Compare: ["open-and-close", "numeric-count", "paper-slide"], Rank: ["numeric-count", "tick-confirm", "paper-slide"], Filter: ["marker-highlight", "open-and-close", "paper-slide"], Expand: ["scale-bounce", "unfold", "paper-slide"], Collapse: ["open-and-close", "paper-slide"], Scan: ["draw-on", "marker-highlight", "paper-slide"], Detect: ["marker-highlight", "pulse", "paper-slide"], Repair: ["tick-confirm", "connect", "paper-slide"], Validate: ["tick-confirm", "numeric-count", "paper-slide"], Package: ["drop-and-settle", "unfold", "paper-slide"], Deliver: ["stamp-impact", "scale-bounce", "paper-slide"], Connect: ["connect", "node-sequence", "paper-slide"], Multiply: ["numeric-count", "scale-bounce", "paper-slide"], Convert: ["unfold", "open-and-close", "paper-slide"],
  Grow: ["scale-bounce", "unfold", "draw-on"], Unfold: ["unfold", "open-and-close", "draw-on"], Branch: ["connect", "node-sequence", "draw-on"], Emerge: ["unfold", "ink-reveal", "draw-on"], Absorb: ["draw-on", "pulse", "connect"], Flow: ["connect", "node-sequence", "paper-slide"], Illuminate: ["pulse", "ink-reveal", "scale-bounce"], Accumulate: ["numeric-count", "scale-bounce", "connect"], Circulate: ["connect", "node-sequence", "paper-slide"],
};

const preferredTransitions: Record<VisualVerb, string[]> = {
  Reveal: ["paper-wipe", "torn-paper-reveal", "page-turn"], Extract: ["tape-peel", "paper-wipe", "page-turn"], Split: ["collage-push", "card-stack-shuffle", "paper-wipe"], Merge: ["collage-push", "card-stack-shuffle", "page-turn"], Transform: ["torn-paper-reveal", "paper-wipe", "page-turn"], Assemble: ["card-stack-shuffle", "collage-push", "paper-wipe"], Route: ["collage-push", "paper-wipe", "page-turn"], Compare: ["card-stack-shuffle", "collage-push", "paper-wipe"], Rank: ["card-stack-shuffle", "paper-wipe", "page-turn"], Filter: ["tape-peel", "torn-paper-reveal", "paper-wipe"], Expand: ["torn-paper-reveal", "paper-wipe", "page-turn"], Collapse: ["tape-peel", "paper-wipe", "page-turn"], Scan: ["paper-wipe", "torn-paper-reveal", "page-turn"], Detect: ["tape-peel", "paper-wipe", "page-turn"], Repair: ["card-stack-shuffle", "paper-wipe", "page-turn"], Validate: ["page-turn", "paper-wipe", "torn-paper-reveal"], Package: ["card-stack-shuffle", "collage-push", "page-turn"], Deliver: ["page-turn", "paper-wipe", "collage-push"], Connect: ["collage-push", "paper-wipe", "page-turn"], Multiply: ["card-stack-shuffle", "collage-push", "paper-wipe"], Convert: ["torn-paper-reveal", "paper-wipe", "page-turn"],
  Grow: ["torn-paper-reveal", "paper-wipe", "page-turn"], Unfold: ["torn-paper-reveal", "paper-wipe", "page-turn"], Branch: ["collage-push", "paper-wipe", "page-turn"], Emerge: ["ink-reveal", "paper-wipe", "page-turn"], Absorb: ["tape-peel", "paper-wipe", "page-turn"], Flow: ["collage-push", "paper-wipe", "page-turn"], Illuminate: ["ink-reveal", "paper-wipe", "page-turn"], Accumulate: ["card-stack-shuffle", "paper-wipe", "page-turn"], Circulate: ["collage-push", "paper-wipe", "page-turn"],
};

function normalized(value: string) { return value.toLowerCase().replace(/[^a-z0-9]+/g, "-"); }

function scoreEntry(entry: ResolvedRegistryEntry, intents: string[], subject: string, used: Set<string>) {
  const haystack = [...(entry.intents ?? []), ...(entry.keywords ?? []), entry.slug ?? "", entry.name ?? ""].join(" ").toLowerCase();
  const intentScore = intents.reduce((score, intent) => score + (entry.intents?.includes(intent) ? 100 : 0), 0);
  const words = subject.toLowerCase().split(/\W+/).filter((word) => word.length > 3);
  const subjectScore = words.reduce((score, word) => score + (haystack.includes(word) ? 4 : 0), 0);
  return intentScore + subjectScore - (used.has(entry.id) ? 25 : 0);
}

function chooseFamily(registry: ExplainerRegistry, scene: DirectorScenePlan, used: Set<string>, aspectRatio: AspectRatio) {
  const candidates = entriesFor(registry, "scene-family").filter((entry) => entry.aspectRatios?.includes(aspectRatio) !== false);
  const intents = hintedFamilyIntents[scene.storyFunction] ?? familyIntents[scene.storyFunction as StoryPurpose] ?? ["compose_story_scene"];
  const ranked = candidates.map((entry) => ({ entry, score: scoreEntry(entry, intents, scene.heroSubject, used) })).sort((a, b) => b.score - a.score || (a.entry.order ?? 0) - (b.entry.order ?? 0) || a.entry.id.localeCompare(b.entry.id));
  const selected = ranked[0]?.entry;
  if (!selected) throw new ExplainerSelectionError(`No scene family can satisfy ${scene.storyFunction}.`, { sceneId: scene.sceneId, intents });
  return selected;
}

function chooseReference(registry: ExplainerRegistry, reference: string | undefined, categories: string[], scene: DirectorScenePlan, required: string, aspectRatio: AspectRatio) {
  const exact = reference ? findComponent(registry, reference, categories) : undefined;
  if (exact) return exact;
  const candidates = categories.flatMap((category) => entriesFor(registry, category)).filter((entry) => entry.aspectRatios?.includes(aspectRatio) !== false);
  const selected = candidates.map((entry) => ({ entry, score: scoreEntry(entry, [required], scene.heroSubject, new Set()) })).sort((a, b) => b.score - a.score || (a.entry.order ?? 0) - (b.entry.order ?? 0) || a.entry.id.localeCompare(b.entry.id))[0]?.entry;
  if (!selected) throw new ExplainerSelectionError(`No ${required} component is available for ${scene.sceneId}.`, { categories, reference });
  return selected;
}

function chooseMotion(registry: ExplainerRegistry, scene: DirectorScenePlan, selected: ResolvedRegistryEntry[], energy: MotionEnergy) {
  const motions = entriesFor(registry, "motion").filter((entry) => entry.id.startsWith("motion."));
  const preferred = preferredMotionNames[scene.visualVerb];
  const compatible = new Set(selected.flatMap((entry) => entry.compatibleMotions ?? []));
  const ranked = motions.map((entry) => {
    const name = normalized(entry.id.split(".").slice(2).join("-"));
    const preference = preferred.findIndex((candidate) => normalized(candidate) === name);
    const energyScore = entry.motionEnergy?.includes(energy) ? 5 : 0;
    const compatibilityScore = compatible.size && [...compatible].some((candidate) => normalized(candidate) === name) ? 12 : 0;
    const entranceScore = entry.id.includes("entrance") ? 8 : 0;
    return { entry, score: preference < 0 ? 0 : 80 - preference * 10 + energyScore + compatibilityScore + entranceScore };
  }).sort((a, b) => b.score - a.score || (a.entry.order ?? 0) - (b.entry.order ?? 0) || a.entry.id.localeCompare(b.entry.id));
  const selectedMotion = ranked[0]?.entry;
  if (!selectedMotion) throw new ExplainerSelectionError(`No motion primitive is available for ${scene.sceneId}.`, { visualVerb: scene.visualVerb });
  return selectedMotion;
}

function chooseTransition(registry: ExplainerRegistry, scene: DirectorScenePlan, family: ResolvedRegistryEntry, used: Set<string>) {
  const allowed = new Set((family.compatibleTransitions ?? []).map((value) => normalized(value)));
  const candidates = entriesFor(registry, "motion").filter((entry) => entry.id.includes(".transition.") && (allowed.size === 0 || allowed.has(normalized(entry.id.split(".").slice(2).join("-")))));
  const preferred = preferredTransitions[scene.visualVerb];
  const ranked = candidates.map((entry) => {
    const name = normalized(entry.id.split(".").slice(2).join("-"));
    const preference = preferred.findIndex((candidate) => normalized(candidate) === name);
    return { entry, score: (preference < 0 ? 0 : 80 - preference * 10) - (used.has(entry.id) ? 15 : 0) };
  }).sort((a, b) => b.score - a.score || (a.entry.order ?? 0) - (b.entry.order ?? 0) || a.entry.id.localeCompare(b.entry.id));
  const selected = ranked[0]?.entry;
  if (!selected) throw new ExplainerSelectionError(`No transition is compatible with ${family.id}.`, { sceneId: scene.sceneId, familyId: family.id });
  return selected;
}

function technicalFirst(registry: ExplainerRegistry, categories: string[], aspectRatio: AspectRatio, label: string): ResolvedRegistryEntry {
  const candidates=categories.flatMap((category)=>entriesFor(registry,category)).filter((entry)=>entry.aspectRatios?.includes(aspectRatio)!==false).sort((a,b)=>(a.order??0)-(b.order??0)||a.id.localeCompare(b.id));
  const selected=candidates[0];
  if(!selected) throw new ExplainerSelectionError(`No technical ${label} component is installed.`,{categories,aspectRatio});
  return selected;
}
function selectAuthoredExecutionShell(registry: ExplainerRegistry, aspectRatio: AspectRatio): Selection {
  // Production-scoped authored art owns the scene pixels. These components are a
  // deterministic transport/render shell only and are never selected from story prose.
  const sceneFamily=technicalFirst(registry,["scene-family"],aspectRatio,"scene-family");
  const typography=technicalFirst(registry,["typography"],aspectRatio,"typography");
  const hero=technicalFirst(registry,["media-container","documentary-module","creator-module"],aspectRatio,"media");
  const support=technicalFirst(registry,["icon"],aspectRatio,"support");
  const motion=technicalFirst(registry,["motion"],aspectRatio,"motion");
  const transition=entriesFor(registry,"motion").filter((entry)=>entry.id.includes(".transition.")&&entry.aspectRatios?.includes(aspectRatio)!==false).sort((a,b)=>(a.order??0)-(b.order??0)||a.id.localeCompare(b.id))[0]??motion;
  return {sceneFamily,typography,hero,support,motion,transition,layoutVariantId:sceneFamily.layoutVariants?.[0]?.id??"A"};
}

export function selectScene(registry: ExplainerRegistry, scene: DirectorScenePlan, used: { families: Set<string>; transitions: Set<string> }, energy: MotionEnergy, aspectRatio: AspectRatio = "16:9"): Selection {
  if(scene.visualConstruction?.productionScopedArt) return selectAuthoredExecutionShell(registry,aspectRatio);
  const hints = scene.componentHints ?? {};
  const hinted = hints.sceneFamily ? findComponent(registry, hints.sceneFamily, ["scene-family"]) : undefined;
  const family = hinted ?? chooseFamily(registry, scene, used.families, aspectRatio);
  const approved = family.approvedComponents ?? {};
  const typography = chooseReference(registry, hints.typography ?? approved.typography, ["typography"], scene, "typography", aspectRatio);
  const hero = chooseReference(registry, hints.media ?? approved.media, ["media-container", "documentary-module", "creator-module"], scene, "hero", aspectRatio);
  const support = chooseReference(registry, hints.icon ?? approved.icon, ["icon"], scene, "supporting", aspectRatio);
  const dataReference = hints.data ?? hints.workflow ?? approved.data;
  const wantsWorkflow = Boolean(hints.workflow) || Boolean(hints.data?.startsWith("workflow.")) || scene.visualVerb === "Route" || /process|workflow|system|agent|flow/i.test(`${scene.layoutIntent} ${scene.heroSubject}`);
  const data = dataReference ? chooseReference(registry, dataReference, wantsWorkflow ? ["workflow-diagram", "data-visualisation"] : ["data-visualisation", "workflow-diagram"], scene, "data", aspectRatio) : undefined;
  const workflow = wantsWorkflow ? (data?.category === "workflow-diagram" ? data : undefined) : undefined;
  const motion = chooseMotion(registry, scene, [family, typography, hero, support, ...(data ? [data] : [])], energy);
  const transition = chooseTransition(registry, scene, family, used.transitions);
  const layoutVariantId = family.layoutVariants?.[0]?.id ?? "A";
  used.families.add(family.id); used.transitions.add(transition.id);
  return { sceneFamily: family, typography, hero, support, data, workflow, motion, transition, layoutVariantId };
}
