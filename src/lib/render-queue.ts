import path from "node:path";
import { homedir } from "node:os";
import { spawn } from "node:child_process";
import { appendFileSync } from "node:fs";

// Render jobs drain from a Postgres queue (pg-boss) instead of the route
// spawning a detached child. One box can host any number of workers; the
// queue survives process restarts and gives retries/backoff for free.
// Set RENDER_QUEUE=off to keep the legacy in-process spawn behaviour.

export const RENDER_QUEUE = "site-render";
export type RenderJobPayload = { jobId: string; dir: string; family: string };

const queueEnabled = () => process.env.RENDER_QUEUE !== "off" && Boolean(process.env.DATABASE_URL);

let bossPromise: Promise<import("pg-boss").PgBoss> | null = null;
async function getBoss() {
  if (!bossPromise) {
    bossPromise = (async () => {
      const { PgBoss } = await import("pg-boss");
      const boss = new PgBoss({
        connectionString: process.env.DATABASE_URL!,
        schema: "render_queue",
        supervise: false,
        migrate: true,
      });
      boss.on("error", (e: Error) => console.error("[render-queue]", e));
      await boss.start();
      await boss.createQueue(RENDER_QUEUE);
      return boss;
    })();
  }
  return bossPromise;
}

// Same env the engines see regardless of who spawns the runner.
export function renderEnv(): NodeJS.ProcessEnv {
  const nodeBin = path.join(homedir(), ".nvm", "versions", "node", "v24.19.0", "bin");
  const whisperPy = process.env.NEXSTUDIO_WHISPER_PYTHON
    ?? path.join(homedir(), "tools", "whisper", "bin", "python3");
  return {
    ...process.env,
    PATH: `${nodeBin}:${process.env.PATH}`,
    WHISPER_PYTHON: whisperPy,
    NEXSTUDIO_SCENE_LLM: process.env.NEXSTUDIO_SCENE_LLM ?? "off",
  };
}

export function runRenderJob(payload: RenderJobPayload): Promise<number> {
  const runner = path.join(process.cwd(), "services", "studio-family-engines", "site_job_runner.py");
  return new Promise((resolve) => {
    const child = spawn(process.env.PYTHON_BIN ?? "python3", [runner, payload.dir], {
      cwd: process.cwd(), stdio: ["ignore", "pipe", "pipe"], env: renderEnv(),
    });
    const log = path.join(payload.dir, "worker.log");
    child.stdout.on("data", (d) => appendFileSync(log, d));
    child.stderr.on("data", (d) => appendFileSync(log, d));
    child.on("error", () => resolve(127));
    child.on("close", (code) => resolve(code ?? 1));
  });
}

// Called by API routes after the job dir + request files are written.
// Enqueues to Postgres when enabled; falls back to the legacy detached
// spawn so a standalone dev box with the queue off behaves exactly as before.
export async function submitRenderJob(payload: RenderJobPayload): Promise<void> {
  if (!queueEnabled()) return legacySpawn(payload);
  try {
    const boss = await getBoss();
    await boss.send(RENDER_QUEUE, payload, {
      singletonKey: payload.jobId, // never run the same job twice
      retryLimit: 0,               // engines write their own terminal status; retries would double-render
      expireInSeconds: 60 * 60 * 4,
    });
  } catch (e) {
    console.error("[render-queue] enqueue failed, falling back to spawn", e);
    legacySpawn(payload);
  }
}

function legacySpawn(payload: RenderJobPayload) {
  const runner = path.join(process.cwd(), "services", "studio-family-engines", "site_job_runner.py");
  const child = spawn(process.env.PYTHON_BIN ?? "python3", [runner, payload.dir], {
    cwd: process.cwd(), detached: true, stdio: "ignore", env: renderEnv(),
  });
  child.unref();
}

// Capacity gate under queueing: with the queue on, "in-flight" means queued
// OR rendering — a bigger pool than the old concurrency cap. With it off the
// legacy concurrent-render limit applies. runningEngineJobs() counts both
// either way (status.json stays "running" from submit to terminal).
export function renderInFlightLimit(): number {
  if (queueEnabled()) {
    const cap = parseInt(process.env.STUDIO_MAX_QUEUED_RENDERS ?? "25", 10);
    return Number.isFinite(cap) && cap > 0 ? cap : 25;
  }
  const cap = parseInt(process.env.STUDIO_MAX_CONCURRENT_RENDERS ?? "4", 10);
  return Number.isFinite(cap) && cap > 0 ? cap : 4;
}

// Rough queue depth for the capacity gate: counts queued+active rows in the
// boss schema. Returns null when the queue is off or unreadable so callers
// can fall back to the filesystem-based running-job count.
export async function renderQueueDepth(): Promise<number | null> {
  if (!queueEnabled()) return null;
  try {
    const boss = await getBoss();
    const stats = await boss.getQueueStats(RENDER_QUEUE);
    const q = stats[0];
    return q ? q.queuedCount + q.activeCount + q.deferredCount : 0;
  } catch { return null; }
}
