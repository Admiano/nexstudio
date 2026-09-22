import path from "node:path";
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync, readFileSync, copyFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { homedir } from "node:os";
import { requireSession } from "@/lib/route-auth";
import { json, problem } from "@/lib/http";

export const runtime = "nodejs";

const ENGINE = process.env.SKETCH_FILMS_ENGINE_DIR
  ?? path.join(process.cwd(), "engines", "explainer", "NexStudio_Explainer_Execution_Body_V2");
const JOBS = path.join(ENGINE, "out", "sketch-film-jobs");
const AUDIO_LIB = path.join(ENGINE, "src", "hyperframes", "sketch-films", "specs", "launch-promo", "audio");
const TSX = path.join(process.cwd(), "node_modules", ".bin", "tsx");

/**
 * GET — discovery: scene types + the brief fields this endpoint accepts.
 */
export async function GET(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  return json({
    accepts: "application/json",
    body: {
      prompt: "free-text brief — the director derives beats, scenes, copy",
      script: "FilmBeat[] — structured narrative (head/items/stat/quote/media/split/word per beat)",
      spec: "SketchFilmSpec — power path, rendered verbatim",
      duration: "seconds (default 38)",
      product: "brand name for the end-card",
      tagline: "payoff line",
      cta: "end-card button text",
      seed: "deterministic variation seed",
    },
    sceneTypes: [
      "chapter", "type-card", "hero-build", "phrase-swap", "word-list", "feature-grid",
      "process-rail", "stat", "quote", "media-frame", "split", "marquee-word",
      "word-object-bridge", "payoff-lockup", "end-card",
      "chat-prompt", "agent-window", "phone-app", "storyboard", "compose-graph",
      "render-bar", "player", "step", "logo-mark",
    ],
  }, auth.id);
}

/**
 * POST — { prompt | script | spec, duration?, product?, tagline?, cta?, seed? }
 * Compiles a spec, spawns the renderer, returns a job id to poll.
 */
export async function POST(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const id = auth.id;

  let body: Record<string, unknown>;
  try { body = await request.json(); }
  catch { return problem(id, 400, "BAD_JSON", "Invalid JSON", "Send application/json with prompt, script, or spec."); }

  const hasSpec = body.spec && typeof body.spec === "object";
  const hasScript = Array.isArray(body.script) && (body.script as unknown[]).length > 0;
  const hasPrompt = typeof body.prompt === "string" && body.prompt.trim().length > 3;
  if (!hasSpec && !hasScript && !hasPrompt)
    return problem(id, 422, "BRIEF_REQUIRED", "Nothing to film", "Send 'prompt' (free text), 'script' (FilmBeat[]), or 'spec' (SketchFilmSpec).");

  const jobId = `sf-${randomUUID().slice(0, 8)}`;
  const dir = path.join(JOBS, jobId);
  const specDir = path.join(dir, "spec");
  mkdirSync(specDir, { recursive: true });
  const nodeBin = path.join(homedir(), ".nvm", "versions", "node", "v24.19.0", "bin");

  if (hasSpec) {
    /* power path — write the supplied spec; copy the vendored audio clips it references */
    mkdirSync(path.join(specDir, "audio"), { recursive: true });
    for (const f of ["music.mp3", "swipe.mp3", "pop.mp3", "paper.mp3", "confirm.mp3"]) {
      try { copyFileSync(path.join(AUDIO_LIB, f), path.join(specDir, "audio", f)); } catch { /* proceed silent */ }
    }
    writeFileSync(path.join(specDir, "spec.json"), JSON.stringify(body.spec, null, 2));
  } else {
    /* compile the brief via the director (writes spec.json + audio into specDir) */
    const compileArgs = [path.join(ENGINE, "src", "hyperframes", "sketch-films", "direct-cli.ts")];
    if (hasScript) {
      writeFileSync(path.join(dir, "beats.json"), JSON.stringify(body.script));
      compileArgs.push("--script", path.join(dir, "beats.json"));
    } else {
      compileArgs.push(String(body.prompt));
    }
    compileArgs.push(specDir);
    for (const k of ["duration", "product", "tagline", "cta", "seed"] as const) {
      if (body[k] != null) compileArgs.push(`--${k}`, String(body[k]));
    }
    const compiled = spawn(TSX, compileArgs, { cwd: ENGINE, env: { ...process.env, PATH: `${nodeBin}:${process.env.PATH}` } });
    let compileErr = "";
    compiled.stdout?.on("data", () => {});
    compiled.stderr?.on("data", d => { compileErr += String(d); });
    const code = await new Promise<number>(res => compiled.on("exit", res));
    if (code !== 0 || !existsSync(path.join(specDir, "spec.json")))
      return problem(id, 422, "DIRECT_FAILED", "Could not compose the brief", compileErr.slice(-400) || "Director compilation failed.");
  }

  writeFileSync(path.join(dir, "request.json"), JSON.stringify({
    userId: auth.session!.userId, prompt: body.prompt ?? null,
    script: hasScript ? body.script : null, spec: hasSpec ? body.spec : null,
    createdAt: new Date().toISOString(),
  }, null, 1));
  writeFileSync(path.join(dir, "status.json"), JSON.stringify({ status: "running", startedAt: new Date().toISOString() }));

  const outDir = path.join(dir, "out");
  mkdirSync(outDir, { recursive: true });
  const film = path.join(outDir, "film.mp4");
  const child = spawn(TSX, [
    path.join(ENGINE, "src", "hyperframes", "sketch-films", "render.ts"),
    path.join(specDir, "spec.json"), film,
  ], {
    cwd: ENGINE, detached: true, stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, PATH: `${nodeBin}:${process.env.PATH}` },
  });
  child.stdout?.on("data", () => {});
  child.stderr?.on("data", () => {});
  child.on("exit", (code) => {
    try {
      const filesDir = path.join(dir, "files");
      mkdirSync(filesDir, { recursive: true });
      const outputs: Record<string, string> = {};
      if (existsSync(film)) {
        copyFileSync(film, path.join(filesDir, "film.mp4"));
        outputs.film = `/api/v1/sketch-films/${jobId}/files/film.mp4`;
      }
      writeFileSync(path.join(dir, "status.json"), JSON.stringify({
        status: code === 0 ? "done" : "failed",
        exitCode: code, outputs, finishedAt: new Date().toISOString(),
      }));
    } catch (e) {
      writeFileSync(path.join(dir, "status.json"), JSON.stringify({
        status: "failed", exitCode: code, error: String(e), finishedAt: new Date().toISOString(),
      }));
    }
  });
  child.unref();

  return json({ jobId, status: "running", statusUrl: `/api/v1/sketch-films/${jobId}` }, id, { status: 202 });
}
