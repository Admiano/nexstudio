/**
 * Sketch-film director — turns a free-text brief into a SketchFilmSpec.
 *
 * This is the layer that keeps sketch-films from being a fixed template:
 * the brief drives beat selection (which scene types appear and in which
 * order), copy (kickers, display words, captions), transitions and camera
 * moves. The scene library only provides the palette; the director composes.
 *
 * Copy generation is deterministic by default; pass a `copywriter` to inject
 * an LLM (or any) copy source per beat. `validateSpec` guards the output.
 */
import type { SketchFilmSpec, SketchSceneSpec } from "./spec.js";

export type FilmBrief = {
  /** The user prompt — one paragraph is plenty. */
  prompt: string;
  /** Target film length in seconds (default 38). */
  duration?: number;
  /** Product/brand name for the close lockup (e.g. "NEX STUDIO"). */
  product?: string;
  /** Payoff line; falls back to a claim derived from the brief. */
  tagline?: string;
  /** CTA pill text on the close. */
  cta?: string;
  /** Deterministic seed for shuffled picks. */
  seed?: number;
};

export type BeatRole =
  | "hook"
  | "interface"
  | "process"
  | "product"
  | "proof"
  | "payoff"
  | "close";

export type Copywriter = (
  role: BeatRole,
  ctx: { brief: FilmBrief; stepWords: string[]; sceneType: string }
) => Partial<SketchSceneSpec>;

/* ---------------- deterministic rng ---------------- */
const mulberry32 = (a: number) => () => {
  a |= 0; a = (a + 0x6d2b79f5) | 0;
  let t = Math.imul(a ^ (a >>> 15), 1 | a);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

/* ---------------- brief analysis ---------------- */
const STOP = new Set(("the a an and or of for to in on with by is are was be will that this it its as at from into your our my me we you their them can " +
  "make makes made get gets let lets want needs need like video film clip short promo about around something some any each every").split(" "));

function keywordsOf(text: string): string[] {
  const freq = new Map<string, number>();
  for (const raw of text.toLowerCase().replace(/[^a-z0-9'\-\s]/g, " ").split(/\s+/)) {
    if (!raw || raw.length < 3 || STOP.has(raw)) continue;
    freq.set(raw, (freq.get(raw) ?? 0) + 1);
  }
  return [...freq.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(([w]) => w);
}

const has = (prompt: string, ...words: string[]) => {
  const p = prompt.toLowerCase();
  return words.some(w => p.includes(w));
};

/** Pull imperative-ish verbs out of the brief to serve as numbered steps. */
function stepWords(prompt: string): string[] {
  const VERBS: [RegExp, string][] = [
    [/\b(scri|writ|prompt|brief)/i, "SCRIPT"],
    [/\b(plan|plans|planned|planning|storyboard|board|outline|map)\b/i, "PLAN"],
    [/\b(draw|drawn|sketch|design|style|styled|art)\b/i, "DRAW"],
    [/\b(build|builds|compose|composes|assembl|animat)\w*/i, "BUILD"],
    [/\b(voice|music|audio|sound|sfx|score|scores)\b/i, "SCORE"],
    [/\b(test|tests|check|checks|verif|qa|review)\w*/i, "TEST"],
    [/\b(render|renders|export|exports|master|ship|ships|deliver|publish)\w*/i, "RENDER"],
    [/\b(launch|launching|release|share|post)\w*/i, "SHIP"],
  ];
  const out: string[] = [];
  for (const [re, word] of VERBS) if (re.test(prompt) && !out.includes(word)) out.push(word);
  return out;
}

/* ---------------- scene selection ---------------- */
type Beat = { role: BeatRole; type: SketchSceneSpec["type"]; weight: number };

function pick<T>(rng: () => number, items: T[], exclude: (t: T) => boolean): T {
  const ok = items.filter(t => !exclude(t));
  const pool = ok.length ? ok : items;
  return pool[Math.floor(rng() * pool.length)];
}

function beatsFor(brief: FilmBrief, rng: () => number): Beat[] {
  const p = brief.prompt.toLowerCase();
  const beats: Beat[] = [];
  const steps = stepWords(p);
  const used = new Set<SketchSceneSpec["type"]>();
  const take = (role: BeatRole, type: SketchSceneSpec["type"], weight: number) => {
    beats.push({ role, type, weight }); used.add(type);
  };
  const fresh = <T extends SketchSceneSpec["type"]>(cands: T[]): T =>
    pick(rng, cands, t => used.has(t));

  /* hook */
  if (has(p, "not a", "instead of", "rather than")) take("hook", "phrase-swap", 0.12);
  else if (has(p, "manifesto", "statement", "philosophy")) take("hook", "hero-build", 0.13);
  else take("hook", fresh(["type-card", "hero-build", "phrase-swap"]), 0.11);

  /* interface — how the user speaks to the product */
  if (has(p, "prompt", "chat", "brief", "text", "type", "describe")) take("interface", "chat-prompt", 0.13);
  else if (has(p, "app", "mobile", "phone")) take("interface", "phone-app", 0.14);
  else take("interface", "agent-window", 0.14);

  /* process — 1 explicit step scene per detected verb, or a rail */
  if (steps.length >= 3) take("process", "process-rail", 0.16);
  for (const w of steps.slice(0, 3)) {
    take("process", "step", steps.length >= 3 ? 0 : 0.10); // step beats get durations from steps.length split below
  }
  /* if no verbs detected, use a rail of the generic pipeline */
  if (!steps.length) take("process", "process-rail", 0.16);
  /* if step beats got zero weight (rail path), drop them */
  for (let i = beats.length - 1; i >= 0; i--) if (beats[i].type === "step" && beats[i].weight === 0) beats.splice(i, 1);

  /* product — what the user gets (never the same scene type twice) */
  const productPref: SketchSceneSpec["type"] = has(p, "app", "mobile", "phone") ? "phone-app"
    : has(p, "dashboard", "tool", "editor", "studio", "agent") ? "agent-window" : "phone-app";
  const productAlt = productPref === "phone-app" ? "agent-window" : "phone-app";
  take("product", used.has(productPref) ? productAlt : productPref, 0.13);

  /* proof — show the machinery once */
  const proofCand: SketchSceneSpec["type"][] = ["storyboard", "compose-graph", "render-bar", "word-object-bridge"];
  if (has(p, "storyboard", "frames", "beats", "scenes")) take("proof", "storyboard", 0.13);
  else if (has(p, "pipeline", "compose", "graph", "architecture")) take("proof", "compose-graph", 0.13);
  else if (has(p, "progress", "render", "export")) take("proof", "render-bar", 0.12);
  else take("proof", fresh(proofCand), 0.11);

  /* payoff + close */
  take("payoff", fresh(["payoff-lockup", "type-card", "hero-build"]), 0.10);
  take("close", "end-card", 0.08);

  return beats;
}

/* ---------------- copy (deterministic default) ---------------- */
const UPPER = (s: string) => s.toUpperCase();
const verbs = (kw: string[]) => kw.filter(k => /(draw|build|test|render|ship|make|turn|launch|publish|compose|plan)/.test(k));

function defaultCopy(role: BeatRole, ctx: { brief: FilmBrief; stepWords: string[]; sceneType: string; stepIdx?: number }): Partial<SketchSceneSpec> {
  const { brief, stepWords: steps, sceneType } = ctx;
  const product = brief.product || "NEX STUDIO";
  const kw = keywordsOf(brief.prompt);
  switch (role) {
    case "hook":
      if (sceneType === "phrase-swap") return { lead: "not another generator —", swapFrom: "rendered.", swapTo: "directed.", kicker: "THE PITCH" };
      if (sceneType === "hero-build") return { lines: [`${kw[0] || "the brief"} in —`, "every beat drawn —", "a film out."], kicker: "THE PITCH" };
      return { text: `one ${kw[0] || "brief"} in. one film out.`, kicker: "THE PITCH", index: false };
    case "interface":
      if (sceneType === "chat-prompt") return { kicker: "BRIEF → FILM", mention: "Studio", text: short(brief.prompt, 56), mode: "Auto", cursor: true, index: false };
      if (sceneType === "phone-app") return { kicker: "IN THE POCKET", caption: "your film, where you are", appTitle: product.toLowerCase(), cards: [{ title: "beats" }, { title: "style" }, { title: "audio" }, { title: "export" }] };
      return { kicker: "SOLO DESK", prompt: short(brief.prompt, 68), status: "Agent — planning the build…", checks: ["scaffold the storyboard", "bind the sketch style kit", "compose 1:1 frames", "master music + accents"] };
    case "process":
      if (sceneType === "process-rail") return { title: "how it moves", steps: steps.length ? steps.slice(0, 4) : ["SCRIPT", "DRAW", "SCORE", "RENDER"], payoff: "every beat drawn before it moves." };
      return { kicker: `/ STEP 0${(ctx.stepIdx ?? 0) + 1}`, kickerR: `STEP 0${(ctx.stepIdx ?? 0) + 1}`, word: steps[ctx.stepIdx ?? 0] || "BUILD", variant: stepVariant(steps[ctx.stepIdx ?? 0] || "BUILD") };
    case "product":
      if (sceneType === "phone-app") return { kicker: "YOUR FILM — READY", kickerR: "DEMO", caption: "the output, as it lands", appTitle: product.toLowerCase(), hero: "SCENE 01 — PROMPT", cards: [{ title: "beats" }, { title: "style" }, { title: "audio" }, { title: "export" }] };
      return { kicker: "THE DESK", prompt: short(brief.prompt, 68), checks: ["scaffold the storyboard", "bind the sketch style kit", "compose 1:1 frames", "master music + accents"] };
    case "proof":
      if (sceneType === "storyboard") return { kicker: "THE BOARD", kickerR: "INK ONLY", foot: "EVERY BEAT, DRAWN BEFORE IT MOVES", cells: 6 };
      if (sceneType === "compose-graph") return { kicker: "/ PIPELINE", kickerR: "COMPOSE", title: "COMPOSE" };
      if (sceneType === "render-bar") return { kicker: "RENDER", file: `${product.toLowerCase().replace(/\s+/g, "-")}.mp4` };
      return { keyword: kw[0] || "film", before: "the", after: "does the work.", object: "card" };
    case "payoff":
      if (sceneType === "payoff-lockup") return { text: brief.tagline || "briefs in. films out.", sub: `MUSIC + ACCENTS · ${(brief.duration ?? 38).toFixed(0)}S`, index: false };
      return { text: brief.tagline || "now it draws the launch video too.", index: false };
    case "close":
      return { brandA: product.split(" ")[0] || "NEX", brandB: product.split(" ").slice(1).join(" ") || "STUDIO", sub: brief.tagline || "briefs in. films out.", pill: brief.cta || "Start a film", index: false };
  }
}

const stepVariant = (word: string): "build" | "test" | "render" =>
  /TEST|CHECK|VERIF|QA|REVIEW/.test(word) ? "test" : /RENDER|SHIP|EXPORT|MASTER|DELIVER|LAUNCH|RELEASE|SHARE|POST/.test(word) ? "render" : "build";

const short = (s: string, n: number) => (s.length <= n ? s : s.slice(0, n - 1).replace(/\s+\S*$/, "") + "…");

/* ---------------- transitions + camera ---------------- */
const TRANSITION_POOL: NonNullable<SketchSceneSpec["transition"]>[] =
  ["fade", "wipe", "torn", "push", "page", "shuffle", "tape", "paper", "crumple", "rise"];

function transitionFor(beat: Beat, prev: Beat | undefined, rng: () => number): SketchSceneSpec["transition"] {
  if (!prev) return "cut";
  if (beat.role === "process" && prev.role === "process") return "cut";      // numbered steps snap
  if (beat.role === "close") return pick(rng, ["torn", "cut"], () => false);
  if (beat.role === "payoff") return pick(rng, ["page", "fade"], () => false);
  if (beat.type === "storyboard" || beat.type === "compose-graph") return "push";
  return pick(rng, TRANSITION_POOL, () => false);
}

function cameraFor(beat: Beat, i: number): SketchSceneSpec["camera"] | undefined {
  if (beat.role === "close" || beat.role === "payoff") return { push: 0.05 };
  if (i % 3 === 2) return { push: 0.06 };
  if (beat.type === "process-rail") return { pan: [0.03, 0] };
  return undefined;
}

/* ---------------- spec assembly + validation ---------------- */
export function directToSpec(brief: FilmBrief, opts: { copywriter?: Copywriter } = {}): SketchFilmSpec {
  const rng = mulberry32(brief.seed ?? 97);
  const dur = brief.duration ?? 38;
  const beats = beatsFor(brief, rng);
  const steps = stepWords(brief.prompt);

  /* weight → seconds, then snap to 0.1s and re-extend the last beat */
  const wsum = beats.reduce((s, b) => s + b.weight, 0);
  let t = 0;
  const scenes: SketchSceneSpec[] = [];
  let stepIdx = 0;
  beats.forEach((b, i) => {
    const raw = (b.weight / wsum) * dur;
    const d = i === beats.length - 1 ? dur - t : Math.max(2.2, Math.round(raw * 10) / 10);
    const scene: SketchSceneSpec = {
      id: `beat-${String(i + 1).padStart(2, "0")}-${b.type}`,
      type: b.type,
      start: Math.round(t * 10) / 10,
      duration: Math.round(d * 10) / 10,
    };
    const prev = beats[i - 1];
    scene.transition = transitionFor(b, prev, rng);
    const cam = cameraFor(b, i);
    if (cam) scene.camera = cam;
    const ctx = { brief, stepWords: steps, sceneType: b.type, stepIdx: b.type === "step" ? stepIdx++ : undefined };
    Object.assign(scene, defaultCopy(b.role, ctx));
    const over = opts.copywriter?.(b.role, ctx);
    if (over) Object.assign(scene, over);
    scenes.push(scene);
    t += d;
  });

  /* SFX: swipe on every real transition, pops inside entrances, paper on
     first + storyboard, confirm on close */
  const swipes: number[] = [], pops: number[] = [], papers: number[] = [0.05];
  scenes.forEach((s, i) => {
    if (s.transition && s.transition !== "cut" && i > 0) swipes.push(round1(s.start));
    const n = s.type === "storyboard" ? 6 : s.type === "agent-window" ? 5 : 3;
    for (let k = 0; k < n; k++) pops.push(round1(s.start + 0.55 + k * (s.type === "storyboard" ? 0.16 : 0.26)));
    if (s.type === "storyboard") papers.push(round1(s.start));
    if (s.type === "end-card") pops.push(round1(s.start + 1.4));
  });
  const last = scenes[scenes.length - 1];

  const spec: SketchFilmSpec = {
    productionId: `sketch-film-${slugify(brief.prompt).slice(0, 40) || "film"}`,
    width: 720, height: 720, fps: 30,
    durationSeconds: Math.round(dur * 10) / 10,
    music: { path: "audio/music.mp3", volume: 0.16 },
    sfx: [
      { path: "audio/swipe.mp3", atSec: dedupe(swipes), volume: 0.32 },
      { path: "audio/pop.mp3", atSec: dedupe(pops), volume: 0.30 },
      { path: "audio/paper.mp3", atSec: dedupe(papers), volume: 0.36 },
      { path: "audio/confirm.mp3", atSec: last ? [round1(last.start + Math.min(1.6, last.duration - 0.8))] : [], volume: 0.42 },
    ],
    scenes,
  };
  validateSpec(spec);
  return spec;
}

const round1 = (n: number) => Math.round(n * 10) / 10;
const dedupe = (xs: number[]) => [...new Set(xs.map(round1))].sort((a, b) => a - b).filter(x => x >= 0);
const slugify = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

/** Guardrail: the contract every emitted spec must satisfy. */
export function validateSpec(spec: SketchFilmSpec): void {
  const VALID = new Set([
    "type-card", "chat-prompt", "agent-window", "step", "phone-app", "storyboard",
    "compose-graph", "render-bar", "player", "logo-mark", "end-card",
    "hero-build", "phrase-swap", "process-rail", "payoff-lockup", "word-object-bridge",
  ]);
  if (!spec.scenes.length) throw new Error("spec.scenes empty");
  let t = 0;
  for (const [i, s] of spec.scenes.entries()) {
    if (!VALID.has(s.type)) throw new Error(`unknown scene type ${s.type}`);
    if (Math.abs(s.start - t) > 0.05) throw new Error(`scene ${i} (${s.id}) starts at ${s.start}, expected ${t} — scenes must tile the timeline`);
    if (s.duration < 1.2) throw new Error(`scene ${s.id} too short (${s.duration}s)`);
    const text = String((s as Record<string, unknown>).text ?? "");
    if (text.length > 120) throw new Error(`scene ${s.id} text too long (${text.length} chars)`);
    t = s.start + s.duration;
  }
  if (Math.abs(t - spec.durationSeconds) > 0.2) throw new Error(`scenes end at ${t}s but durationSeconds=${spec.durationSeconds}`);
  const adj = spec.scenes.filter((s, i) => i > 0 && s.type === spec.scenes[i - 1].type);
  if (adj.length) throw new Error(`adjacent duplicate scene types: ${adj.map(s => s.type).join(",")}`);
}
