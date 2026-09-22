/**
 * Sketch-film director — turns a brief into a SketchFilmSpec.
 *
 * Two input modes, same compiler:
 *
 *   1. `script` — structured beats (`FilmBeat[]`). The caller (an agent, the
 *      API route, a human) supplies the narrative content; the compiler picks
 *      the scene type that best carries each beat's content, times the film,
 *      assigns transitions/camera/furniture, and validates the result.
 *   2. `prompt` — free text. The compiler derives a script: it splits the
 *      brief into clauses, classifies each clause by content shape (claim,
 *      enumeration, figure, quotation, contrast, process), and emits beats.
 *      Product-UI scenes are only chosen when the brief actually describes a
 *      product interface — otherwise the film is built from the
 *      content-typed primitives (chapter, word-list, feature-grid, stat,
 *      quote, media-frame, split, marquee-word, …).
 *
 * Copy is deterministic by default; inject an LLM source via
 * `directToSpec(brief, { copywriter })` to rewrite any scene's fields.
 */
import type { SketchFilmSpec, SketchSceneSpec } from "./spec.js";

/* ------------------------------------------------------------------ */
/* Input types                                                        */
/* ------------------------------------------------------------------ */

export type FilmBeat = {
  /** Optional role hint: hook | interface | process | product | proof | payoff | close */
  role?: string;
  /** Pin a scene type directly (skips inference). */
  sceneType?: string;
  /** Headline / title / claim text. */
  head?: string;
  /** Secondary line under the head. */
  sub?: string;
  /** List content — strings, or {title, sub, icon} cards. */
  items?: (string | { title?: string; text?: string; sub?: string; icon?: string })[];
  /** Big figure. */
  stat?: number;
  format?: string;
  /** Unit shown after the figure ("%", "x", "k", "hrs"…). */
  suffix?: string;
  statLabel?: string;
  statSub?: string;
  /** Pull-quote. */
  quote?: string;
  by?: string;
  /** Showcase media (asset name or spec-relative path/URL) with optional caption. */
  media?: string;
  caption?: string;
  /** Product-mockup content (optional — the scene fills from the brief otherwise).
      agent-window: sidebar tasks; phone-app: card rows; storyboard: cell labels/thumbs;
      player: poster + row titles; chat-prompt: tool tags. */
  tasks?: { title?: string; sub?: string; on?: boolean }[];
  messages?: { from?: "user" | "agent"; text?: string }[];
  cards?: { title?: string; sub?: string; meta?: string; img?: string; icon?: string }[];
  cells?: string[];
  thumbs?: string[];
  poster?: string;
  tags?: string[];
  /** Contrast pair. */
  a?: { title?: string; items?: string[] };
  b?: { title?: string; items?: string[] };
  /** Single huge word. */
  word?: string;
  /** word-object-bridge params. */
  keyword?: string;
  object?: string;
  /** Generic display line (type-card). */
  text?: string;
  /** Explicit beat length override (seconds). */
  duration?: number;
  /** Scene-level extra fields passed through verbatim. */
  params?: Record<string, unknown>;
};

export type FilmBrief = {
  prompt?: string;
  /** Structured narrative — preferred when a real script exists. */
  script?: FilmBeat[];
  duration?: number;
  product?: string;
  tagline?: string;
  cta?: string;
  seed?: number;
  /** Named media assets scenes can reference ({name: spec-relative path}). */
  media?: Record<string, string>;
  /** Beat indices that get UI/product scenes even without explicit asks. */
  flavor?: "paper" | "product";
};

export type Copywriter = (
  beat: FilmBeat,
  ctx: { brief: FilmBrief; sceneType: string; index: number }
) => Partial<SketchSceneSpec> | void;

/* ------------------------------------------------------------------ */
/* Deterministic rng                                                  */
/* ------------------------------------------------------------------ */
const mulberry32 = (a: number) => () => {
  a |= 0; a = (a + 0x6d2b79f5) | 0;
  let t = Math.imul(a ^ (a >>> 15), 1 | a);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const pick = <T,>(rng: () => number, items: T[], exclude: (t: T) => boolean = () => false): T => {
  const ok = items.filter(t => !exclude(t));
  const pool = ok.length ? ok : items;
  return pool[Math.floor(rng() * pool.length)];
};

/* ------------------------------------------------------------------ */
/* Prompt → script (clause classification)                            */
/* ------------------------------------------------------------------ */

const STOP = new Set(("the a an and or of for to in on with by is are was be will that this it its as at from into your our my me we you their them can " +
  "make makes made get gets let lets want needs need like video film clip short promo about around something some any each every very just").split(" "));

export function keywordsOf(text: string): string[] {
  const freq = new Map<string, number>();
  for (const raw of text.toLowerCase().replace(/[^a-z0-9'\-\s]/g, " ").split(/\s+/)) {
    if (!raw || raw.length < 3 || STOP.has(raw)) continue;
    freq.set(raw, (freq.get(raw) ?? 0) + 1);
  }
  return [...freq.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(([w]) => w);
}

const has = (text: string, ...words: string[]) => {
  const p = text.toLowerCase();
  return words.some(w => p.includes(w));
};

/** Ordered-action verbs → process steps. */
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

/** Clause → content shape. Order matters: first match wins. */
function classifyClause(clause: string): FilmBeat | null {
  const c = clause.trim();
  if (!c || c.length < 4) return null;
  /* quoted → pull-quote */
  const qm = c.match(/["“](.+?)["”]/);
  if (qm) return { quote: qm[1] };
  /* enumeration "a, b, c" or "a / b / c" → list (checked before figures so a
     list containing a number stays a list) */
  const parts = c.split(/,|;| \/ |·| and /).map(s => s.trim()).filter(s => s.length >= 3 && s.length <= 60);
  if (parts.length >= 3) return { items: parts.slice(0, 6) };
  /* contrast "x vs y" / "instead of" */
  const vs = c.match(/(.+?)\s+(?:vs\.?|versus|instead of|rather than|not)\s+(.+)/i);
  if (vs) return { a: { title: "OLD" }, b: { title: "NEW" }, head: c, role: "proof" };
  /* figure → stat */
  const nm = c.match(/(\d[\d,.]*)\s*([kKmMx%]|\$\s*|\+\s*|percent|per cent)?/);
  if (nm && /\d/.test(c) && (has(c, "%", "$", "x ", "k ", "times", "faster", "cheaper", "users", "customers", "minutes", "seconds", "hours", "days", "weeks", "of ") || Number(nm[1].replace(/,/g, "")) >= 100))
    return {
      stat: Number(nm[1].replace(/,/g, "")),
      suffix: nm[2]?.includes("%") || c.includes("%") ? "%" : nm[2]?.includes("$") ? "$" : nm[2]?.trim() === "+" ? "+" : nm[2]?.toLowerCase() === "x" ? "×" : nm[2]?.toLowerCase() === "k" ? "k" : "",
      statLabel: c.replace(/["'“”]/g, "").replace(/\d[\d,.]*\s*[%kKx$+]*\s*/, "").trim().slice(0, 60),
    };
  /* explicit process language → rail (needs a real sequence signal, not a
     lone "finally") */
  const seqCount = ["first", "then", "next", "finally", "step"].filter(w => has(c, w)).length;
  if (has(c, "how it works", "works like", "the process", "step by step") || seqCount >= 2) {
    const sw = stepWords(c);
    return { items: sw.length >= 2 ? sw : ["FIRST", "THEN", "FINALLY"], role: "process" };
  }
  /* product interface asks */
  if (has(c, "prompt box", "chat", "text input", "type a")) return { role: "interface", sceneType: "chat-prompt", head: c };
  if (has(c, "mobile app", "phone", "ios", "android")) return { role: "product", sceneType: "phone-app", head: c };
  if (has(c, "dashboard", "editor", "console", "desk")) return { role: "product", sceneType: "agent-window", head: c };
  /* default: claim → headline beat — strip leading discourse markers */
  const head = c.replace(/^(finally|so|and|but|well|now|then),?\s+/i, "");
  return { head: head.length > 90 ? head.slice(0, 87) + "…" : head };
}

function promptToScript(brief: FilmBrief): FilmBeat[] {
  const p = (brief.prompt || "").trim();
  if (!p) return [];
  /* split into clauses on ., —, newlines; keep order */
  const clauses = p.split(/[.\n\r—]+/).map(s => s.trim()).filter(Boolean);
  const beats: FilmBeat[] = [];
  /* headline hook from the first substantive clause */
  const first = clauses[0];
  if (first) beats.push({ role: "hook", head: first.length > 80 ? keywordsOf(first).slice(0, 5).join(" ") : first });
  for (const c of clauses.slice(1)) {
    const b = classifyClause(c);
    if (b) beats.push(b);
  }
  /* process detection across the whole prompt (ordered verbs) — only when
     no beat already carries a list */
  const steps = stepWords(p);
  if (steps.length >= 2 && !beats.some(b => b.items?.length))
    beats.push({ role: "process", items: steps.slice(0, 4) });
  return beats;
}

/* ------------------------------------------------------------------ */
/* Beat → scene type                                                  */
/* ------------------------------------------------------------------ */

function inferSceneType(beat: FilmBeat, ctx: { index: number; total: number; used: Set<string>; prompt: string; rng: () => number }): SketchSceneSpec["type"] {
  if (beat.sceneType) return beat.sceneType as SketchSceneSpec["type"];
  const { used, rng } = ctx;
  const fresh = <T extends string>(cands: T[]) => pick(rng, cands, t => used.has(t));

  /* structured content wins over role hints */
  if (beat.a && beat.b) return "split";
  if (beat.stat != null) return "stat";
  if (beat.quote) return "quote";
  if (beat.media) return "media-frame";
  if (beat.word) return "marquee-word";
  if (beat.keyword) return "word-object-bridge";
  if (beat.items?.length) {
    const hasTitles = beat.items.some(i => typeof i === "object" && (i.title || i.sub));
    const stepish = beat.items.every(i => typeof i === "string" && /^[A-Z]{2,12}$/.test(i));
    /* items are verb-first phrases ("roast to order", "ship within 48h") → a
       moving rail reads better than a static list */
    const ACTION = /^(plan|design|draw|build|make|roast|grind|brew|ship|pack|send|pick|grow|cut|mix|write|record|edit|test|check|render|export|publish|launch|collect|choose|set|open|place|scan|tap|swipe|track|measure|weigh|clean|fill)\b/i;
    const actionish = beat.items.length >= 3 && beat.items.every(i => typeof i === "string" && ACTION.test(i));
    if (beat.role === "process" || stepish || actionish) return "process-rail";
    if (hasTitles && beat.items.length >= 3) return "feature-grid";
    return "word-list";
  }
  /* role-driven picks */
  switch (beat.role) {
    case "interface": return fresh(["chat-prompt", "agent-window"]);
    case "product": return fresh(["phone-app", "agent-window", "media-frame"]);
    case "process": return "process-rail";
    case "proof": return fresh(["storyboard", "compose-graph", "render-bar", "word-list"]);
    case "payoff": return fresh(["payoff-lockup", "type-card"]);
    case "close": return "end-card";
  }
  /* head/text fallback by position — the beat just before the close is the
     payoff; a short head can go huge */
  const isFirst = ctx.index === 0, isLast = ctx.index === ctx.total - 1;
  const beforeClose = ctx.index === ctx.total - 2;
  const head = beat.head || beat.text || "";
  if (isFirst && head) return fresh(["hero-build", "chapter", "type-card"]);
  if (isLast || beforeClose) return "payoff-lockup";
  if (head && head.split(/\s+/).length <= 2 && head.length <= 12) return "marquee-word";
  return fresh(["type-card", "chapter", "word-list"]);
}

/* ------------------------------------------------------------------ */
/* Beat → scene params                                                */
/* ------------------------------------------------------------------ */

const short = (s: string, n: number) => (s.length <= n ? s : s.slice(0, n - 1).replace(/\s+\S*$/, "") + "…");
const UPPER = (s: string) => s.toUpperCase();

function beatParams(beat: FilmBeat, type: SketchSceneSpec["type"], brief: FilmBrief, rng: () => number): Partial<SketchSceneSpec> {
  const product = brief.product || "NEX STUDIO";
  const kw = keywordsOf(brief.prompt || beat.head || "");
  const base: Record<string, unknown> = { ...(beat.params || {}) };
  const roleKick: Record<string, string> = {
    hook: "THE PITCH", interface: "HOW YOU TALK", process: "HOW IT MOVES",
    product: "WHAT YOU GET", proof: "UNDER THE HOOD", payoff: "THE POINT", close: "",
  };
  if (beat.role && roleKick[beat.role]) base.kicker = roleKick[beat.role];

  switch (type) {
    case "chapter": return { ...base, text: beat.head || beat.text || "", sub: beat.sub };
    case "type-card": return { ...base, text: beat.text || beat.head || "" };
    case "hero-build": {
      const words = (beat.head || "the whole idea drawn.").split(/\s+/).filter(Boolean);
      const lines = words.length > 5
        ? [words.slice(0, 2).join(" "), words.slice(2, 4).join(" "), words.slice(4).join(" ") || "drawn."]
        : [beat.head || ""];
      return { ...base, lines };
    }
    case "phrase-swap": return { ...base, lead: beat.head || "not this —", swapFrom: (beat.a?.title || "before.").toLowerCase(), swapTo: (beat.b?.title || "this.").toLowerCase() };
    case "word-list": return { ...base, title: beat.head, items: beat.items };
    case "feature-grid": return { ...base, title: beat.head, items: beat.items };
    case "process-rail": return {
      ...base, title: beat.head || "how it moves",
      steps: (beat.items || []).map(i => {
        const s = typeof i === "string" ? i : i.title || i.text || "";
        return UPPER(s.length > 10 ? s.split(/\s+/)[0] : s);
      }),
      payoff: beat.sub || "every beat drawn before it moves.",
    };
    case "stat": return { ...base, value: beat.stat, format: beat.format, suffix: beat.suffix, label: beat.statLabel || beat.head || "", sub: beat.statSub || beat.sub };
    case "quote": return { ...base, text: beat.quote, by: beat.by };
    case "media-frame": return { ...base, media: beat.media, caption: beat.caption || beat.head };
    case "split": return { ...base, a: beat.a, b: beat.b };
    case "marquee-word": {
      const raw = beat.word || beat.head || "FILM";
      const word = raw.length <= 14 ? raw : (keywordsOf(raw)[0] || "FILM");
      return { ...base, word: UPPER(word), fillMint: true };
    }
    case "word-object-bridge": return { ...base, keyword: beat.keyword || kw[0] || "idea", before: "the", after: beat.sub || "does the work.", object: beat.object || "card" };
    /* product-UI scenes */
    case "chat-prompt": return { ...base, kicker: (base.kicker as string) || "BRIEF → FILM", mention: "Studio", text: short(brief.prompt || beat.head || "", 52), mode: "Auto", cursor: true, index: false, ...(beat.tags ? { tags: beat.tags } : {}) };
    case "agent-window": return {
      ...base, kicker: (base.kicker as string) || "THE DESK",
      prompt: short(brief.prompt || beat.head || "", 68),
      status: "Agent — planning the build…",
      ...(beat.tasks ? { tasks: beat.tasks } : {}),
      ...(beat.messages ? { messages: beat.messages } : {}),
      checks: beat.items?.map(i => typeof i === "string" ? i : i.title || "") || ["scaffold the storyboard", "bind the sketch style kit", "compose 1:1 frames", "master music + accents"],
    };
    case "phone-app": return {
      ...base, kicker: (base.kicker as string) || "YOUR FILM — READY",
      caption: beat.head || "the output, as it lands",
      appTitle: product.toLowerCase(),
      cards: beat.cards || (beat.items || [{ title: "beats" }, { title: "style" }, { title: "audio" }, { title: "export" }]).map(i => typeof i === "string" ? { title: i } : i),
    };
    case "storyboard": return {
      ...base, kicker: (base.kicker as string) || "THE BOARD", kickerR: "INK ONLY",
      foot: "EVERY BEAT, DRAWN BEFORE IT MOVES",
      cells: beat.cells || 6,
      ...(beat.thumbs ? { thumbs: beat.thumbs } : {}),
    };
    case "compose-graph": return { ...base, kicker: (base.kicker as string) || "/ PIPELINE", kickerR: "COMPOSE", title: "COMPOSE" };
    case "render-bar": return { ...base, kicker: (base.kicker as string) || "RENDER", file: `${product.toLowerCase().replace(/\s+/g, "-")}.mp4` };
    case "payoff-lockup": return { ...base, text: beat.head || brief.tagline || "briefs in. films out.", sub: beat.sub || brief.tagline || "", index: false };
    case "end-card": {
      const [a, ...rest] = product.split(" ");
      return { ...base, brandA: a || "NEX", brandB: rest.join(" ") || "STUDIO", sub: brief.tagline || "briefs in. films out.", pill: brief.cta || "Start a film", index: false };
    }
    default: return { ...base, text: beat.head || beat.text || "" };
  }
}
const beatIndex = (_b: FilmBeat) => 0; // marker numbering handled by caller

/* ------------------------------------------------------------------ */
/* Pacing, transitions, camera, SFX                                   */
/* ------------------------------------------------------------------ */

const ROLE_WEIGHT: Record<string, number> = {
  hook: 0.11, interface: 0.14, process: 0.18, product: 0.14, proof: 0.12, payoff: 0.11, close: 0.08,
};
const beatWeight = (beat: FilmBeat, type: string): number => {
  if (beat.duration) return beat.duration;
  let w = ROLE_WEIGHT[beat.role || ""] ?? 0.10;
  if (type === "feature-grid" || type === "word-list") w = Math.max(w, 0.12);
  if (type === "split" || type === "process-rail") w = Math.max(w, 0.13);
  if (type === "marquee-word") w = Math.min(w, 0.08);
  if (type === "quote" || type === "stat") w = Math.max(w, 0.09);
  return w;
};

const TRANSITION_POOL: NonNullable<SketchSceneSpec["transition"]>[] =
  ["fade", "wipe", "torn", "push", "page", "shuffle", "tape", "paper", "crumple", "rise"];

function transitionFor(beat: FilmBeat, type: string, prev: { beat: FilmBeat; type: string } | undefined, rng: () => number): SketchSceneSpec["transition"] {
  if (!prev) return "cut";
  if (prev.type === "step" && type === "step") return "cut";
  if (type === "end-card") return pick(rng, ["torn", "cut"], () => false);
  if (type === "payoff-lockup" || type === "end-card") return "page";
  if (type === "storyboard" || type === "compose-graph" || type === "feature-grid") return "push";
  if (type === "chapter") return pick(rng, ["paper", "page", "fade"], () => false);
  if (type === "marquee-word") return pick(rng, ["paper", "rise"], () => false);
  return pick(rng, TRANSITION_POOL, () => false);
}

function cameraFor(type: string, i: number, isLast: boolean): SketchSceneSpec["camera"] | undefined {
  if (type === "end-card" || type === "payoff-lockup") return { push: 0.05 };
  if (type === "process-rail") return { pan: [0.03, 0] };
  if (type === "media-frame") return { push: 0.05 };
  if (i % 3 === 2) return { push: 0.06 };
  return undefined;
}

/* ------------------------------------------------------------------ */
/* Compiler                                                           */
/* ------------------------------------------------------------------ */

export function directToSpec(brief: FilmBrief, opts: { copywriter?: Copywriter } = {}): SketchFilmSpec {
  const rng = mulberry32(brief.seed ?? 97);
  const dur = brief.duration ?? 38;

  /* 1) script: explicit beats or derived from the prompt */
  let beats = brief.script?.length ? [...brief.script] : promptToScript(brief);
  /* bookends: hook if missing, close always */
  if (beats.length && beats[0].role !== "hook" && !beats[0].head && !beats[0].text) {
    const kw = keywordsOf(brief.prompt || "");
    beats.unshift({ role: "hook", head: `one ${kw[0] || "brief"} in. one film out.` });
  }
  if (!beats.length || beats[beats.length - 1].sceneType !== "end-card" && beats[beats.length - 1].role !== "close") {
    beats.push({ role: "close", sceneType: "end-card" });
  }
  if (beats.length > 12) beats = [...beats.slice(0, 11), beats[beats.length - 1]];

  /* 2) scene selection with dedupe — a type repeats only if the narrative
        carries multiple beats that genuinely need it (e.g. several lists) */
  const used = new Set<string>();
  const typed = beats.map((b, i) => {
    let type = inferSceneType(b, { index: i, total: beats.length, used, prompt: brief.prompt || "", rng });
    /* soft dedupe: if the same type was already used and this beat has a
       near-equivalent alternative, vary it */
    if (used.has(type) && !b.sceneType) {
      const alts: Record<string, SketchSceneSpec["type"][]> = {
        "type-card": ["chapter", "hero-build", "marquee-word"],
        "chapter": ["type-card", "marquee-word"],
        "word-list": ["feature-grid", "process-rail"],
        "feature-grid": ["word-list", "compose-graph"],
        "hero-build": ["type-card", "chapter"],
        "stat": ["marquee-word", "type-card", "chapter"],
      };
      for (const alt of alts[type] || []) if (!used.has(alt)) { type = alt; break; }
    }
    used.add(type);
    return { beat: b, type };
  });

  /* 2b) pinned beats are sacred: if an *inferred* beat collides with a pinned
        neighbor, re-type the inferred one */
  for (let i = 1; i < typed.length; i++) {
    if (typed[i].type !== typed[i - 1].type) continue;
    const movable = !typed[i].beat.sceneType ? i : !typed[i - 1].beat.sceneType ? i - 1 : -1;
    if (movable < 0) continue; // both pinned — caller's choice, validator will flag
    const family: Record<string, SketchSceneSpec["type"][]> = {
      "chapter": ["type-card", "hero-build", "marquee-word"],
      "type-card": ["chapter", "marquee-word"],
      "word-list": ["feature-grid"],
      "feature-grid": ["word-list"],
      "stat": ["marquee-word", "type-card"],
      "quote": ["type-card"],
      "hero-build": ["type-card", "chapter"],
      "marquee-word": ["type-card"],
      "payoff-lockup": ["type-card"],
    };
    const cur = typed[movable].type;
    for (const alt of family[cur] || []) {
      if (!used.has(alt) && typed[movable - 1]?.type !== alt && typed[movable + 1]?.type !== alt) {
        used.delete(cur); used.add(alt); typed[movable].type = alt; break;
      }
    }
  }

  /* 3) timing: weights → seconds, snap to 0.1s, last beat absorbs remainder */
  const wsum = typed.reduce((s, t) => s + beatWeight(t.beat, t.type), 0);
  let t = 0;
  const scenes: SketchSceneSpec[] = [];
  typed.forEach((tb, i) => {
    const raw = (beatWeight(tb.beat, tb.type) / wsum) * dur;
    const d = i === typed.length - 1 ? dur - t : Math.max(2.0, Math.round(raw * 10) / 10);
    const prev = typed[i - 1];
    const scene: SketchSceneSpec = {
      id: `beat-${String(i + 1).padStart(2, "0")}-${tb.type}`,
      type: tb.type,
      start: Math.round(t * 10) / 10,
      duration: Math.round(d * 10) / 10,
      transition: transitionFor(tb.beat, tb.type, prev, rng),
    };
    const cam = cameraFor(tb.type, i, i === typed.length - 1);
    if (cam) scene.camera = cam;
    Object.assign(scene, beatParams(tb.beat, tb.type, brief, rng));
    if (tb.type === "chapter" && !scene.marker) scene.marker = `0${i + 1}`;
    const over = opts.copywriter?.(tb.beat, { brief, sceneType: tb.type, index: i });
    if (over) Object.assign(scene, over);
    scenes.push(scene);
    t += d;
  });

  /* 3b) product-mockup enrichment: a scene that asked for a UI mockup shows the
        film's own content — sidebar tasks and board cells name the real beats,
        phone cards carry the brief's items, prompt text echoes the brief */
  const headOf = (i: number): string =>
    typed[i]?.beat.head || typed[i]?.beat.text || typed[i]?.type.replace(/-/g, " ") || "beat";
  scenes.forEach((scene, i) => {
    if (scene.type === "agent-window" && !scene.tasks) {
      const tasks = typed
        .map((t, ti) => ({ t, ti }))
        .filter(({ ti }) => ti !== i)
        .slice(0, 2)
        .map(({ t, ti }) => ({ title: short(headOf(ti), 20), sub: ti < i ? "done" : "idle", on: false }));
      scene.tasks = [{ title: short(headOf(i), 20), sub: "now", on: true }, ...tasks];
      if (!scene.messages && brief.prompt) {
        scene.messages = [
          { from: "user", text: short(brief.prompt, 60) },
          { from: "agent", text: `on it — ${short(headOf(Math.min(i + 1, typed.length - 1)), 40)}` },
        ];
      }
    }
    if (scene.type === "storyboard" && !Array.isArray(scene.cells)) {
      scene.cells = typed.slice(0, 6).map((t, ti) =>
        UPPER((keywordsOf(headOf(ti))[0] || t.type.replace(/-/g, " ").slice(0, 9)).slice(0, 9)));
    }
    if (scene.type === "chat-prompt" && !scene.tags) {
      const tags = keywordsOf(brief.prompt || "").filter(k => k.length > 3).slice(0, 3);
      if (tags.length) scene.tags = tags;
    }
  });

  /* 4) SFX cues: swipe on real transitions, pops on entrances, paper on
        first + board-like scenes, confirm on close */
  const swipes: number[] = [], pops: number[] = [], papers: number[] = [0.05];
  scenes.forEach((s, i) => {
    if (s.transition && s.transition !== "cut" && i > 0) swipes.push(round1(s.start));
    const n = ["storyboard", "feature-grid", "word-list"].includes(s.type) ? 5 : 3;
    for (let k = 0; k < n; k++) pops.push(round1(s.start + 0.55 + k * 0.26));
    if (s.type === "storyboard" || s.type === "media-frame") papers.push(round1(s.start));
    if (s.type === "end-card") pops.push(round1(s.start + 1.4));
  });
  const last = scenes[scenes.length - 1];

  const spec: SketchFilmSpec = {
    productionId: `sketch-film-${slugify(brief.prompt || "scripted").slice(0, 40) || "film"}`,
    width: 720, height: 720, fps: 30,
    durationSeconds: Math.round(dur * 10) / 10,
    music: { path: "audio/music.mp3", volume: 0.16 },
    sfx: [
      { path: "audio/swipe.mp3", atSec: dedupe(swipes), volume: 0.32 },
      { path: "audio/pop.mp3", atSec: dedupe(pops), volume: 0.30 },
      { path: "audio/paper.mp3", atSec: dedupe(papers), volume: 0.36 },
      { path: "audio/confirm.mp3", atSec: last ? [round1(last.start + Math.min(1.6, last.duration - 0.8))] : [], volume: 0.42 },
    ],
    ...(brief.media ? { assets: brief.media } : {}),
    scenes,
  };
  validateSpec(spec);
  return spec;
}

const round1 = (n: number) => Math.round(n * 10) / 10;
const dedupe = (xs: number[]) => [...new Set(xs.map(round1))].sort((a, b) => a - b).filter(x => x >= 0);
const slugify = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

/* ------------------------------------------------------------------ */
/* Validation                                                         */
/* ------------------------------------------------------------------ */

const REQUIRED_PARAMS: Partial<Record<SketchSceneSpec["type"], string[]>> = {
  "type-card": ["text"], "chapter": ["text"], "hero-build": ["lines"],
  "word-list": ["items"], "feature-grid": ["items"], "process-rail": ["steps"],
  "stat": ["value"], "quote": ["text"], "marquee-word": ["word"],
  "split": ["a", "b"], "word-object-bridge": ["keyword"], "end-card": ["brandA"],
};

export function validateSpec(spec: SketchFilmSpec): void {
  const VALID = new Set([
    "type-card", "chat-prompt", "agent-window", "step", "phone-app", "storyboard",
    "compose-graph", "render-bar", "player", "logo-mark", "end-card",
    "hero-build", "phrase-swap", "process-rail", "payoff-lockup", "word-object-bridge",
    "chapter", "word-list", "feature-grid", "stat", "quote", "media-frame", "split", "marquee-word",
  ]);
  if (!spec.scenes.length) throw new Error("spec.scenes empty");
  let t = 0;
  for (const [i, s] of spec.scenes.entries()) {
    if (!VALID.has(s.type)) throw new Error(`unknown scene type ${s.type}`);
    if (Math.abs(s.start - t) > 0.05) throw new Error(`scene ${i} (${s.id}) starts at ${s.start}, expected ${t} — scenes must tile the timeline`);
    if (s.duration < 1.2) throw new Error(`scene ${s.id} too short (${s.duration}s)`);
    const text = String((s as Record<string, unknown>).text ?? "");
    if (text.length > 120) throw new Error(`scene ${s.id} text too long (${text.length} chars)`);
    for (const k of REQUIRED_PARAMS[s.type] || []) {
      const v = (s as Record<string, unknown>)[k];
      if (v == null || (Array.isArray(v) && !v.length) || v === "")
        throw new Error(`scene ${s.id} (${s.type}) missing required param '${k}'`);
    }
    t = s.start + s.duration;
  }
  if (Math.abs(t - spec.durationSeconds) > 0.2) throw new Error(`scenes end at ${t}s but durationSeconds=${spec.durationSeconds}`);
  const adj = spec.scenes.filter((s, i) => i > 0 && s.type === spec.scenes[i - 1].type);
  if (adj.length) throw new Error(`adjacent duplicate scene types: ${adj.map(s => s.type).join(",")}`);
}
