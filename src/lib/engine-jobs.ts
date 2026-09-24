import path from "node:path";
import { existsSync, readFileSync } from "node:fs";
import { getPrisma } from "@/lib/db";

export type EngineKind = "whiteboard" | "explainer";

function engineDir(kind: EngineKind): string {
  return kind === "whiteboard"
    ? (process.env.WHITEBOARD_V3_RUNTIME_DIR ?? path.join(process.cwd(), "engine_sources", "whiteboard-v3-runtime"))
    : (process.env.EXPLAINER_ENGINE_DIR ?? path.join(process.cwd(), "engine_sources", "editorial-motion-v2"));
}

export function engineJobsDir(kind: EngineKind): string {
  return path.join(engineDir(kind), "out", `${kind === "whiteboard" ? "whiteboard" : "explainer"}-jobs`);
}

export interface EngineJobRead {
  status: "running" | "done" | "failed" | "unknown";
  phase?: string;
  outputs?: Record<string, string>;
  failureCode?: string;
  script?: string;
  title?: string;
}

export function readEngineJob(kind: EngineKind, jobId: string): EngineJobRead {
  try {
    const dir = path.join(engineJobsDir(kind), jobId);
    const statusRaw = existsSync(path.join(dir, "status.json"))
      ? JSON.parse(readFileSync(path.join(dir, "status.json"), "utf8")) : {};
    const progressRaw = existsSync(path.join(dir, "progress.json"))
      ? JSON.parse(readFileSync(path.join(dir, "progress.json"), "utf8")) : {};
    const requestRaw = existsSync(path.join(dir, "request.json"))
      ? JSON.parse(readFileSync(path.join(dir, "request.json"), "utf8")) : {};
    const status = typeof statusRaw.status === "string" ? statusRaw.status : "unknown";
    return {
      status: status === "done" || status === "failed" || status === "running" ? status : "unknown",
      phase: typeof progressRaw.phase === "string" ? progressRaw.phase : (typeof progressRaw.step === "string" ? progressRaw.step : undefined),
      outputs: statusRaw.outputs && typeof statusRaw.outputs === "object" ? statusRaw.outputs as Record<string, string> : undefined,
      failureCode: typeof statusRaw.error === "string" ? statusRaw.error : (typeof statusRaw.failureCode === "string" ? statusRaw.failureCode : undefined),
      script: typeof requestRaw.script === "string" ? requestRaw.script : undefined,
      title: typeof requestRaw.title === "string" ? requestRaw.title : undefined,
    };
  } catch {
    return { status: "unknown" };
  }
}

export async function createEngineDraft(input: {
  ownerUserId: string;
  kind: EngineKind;
  jobId: string;
  videoType: string;
  script: string;
  title?: string | null;
  duration?: number | null;
  voice?: string | null;
}): Promise<void> {
  const prisma = getPrisma();
  if (!prisma) return;
  const firstLine = input.script.split("\n").map((l) => l.trim()).filter(Boolean)[0] ?? "";
  const title = (input.title ?? "").trim() || (firstLine ? firstLine.split(/\s+/).slice(0, 8).join(" ") : "Untitled production");
  await prisma.draft.create({
    data: {
      ownerUserId: input.ownerUserId,
      kind: "VIDEO",
      family: input.kind === "whiteboard" ? "WHITEBOARD" : "EXPLAINER",
      videoType: input.videoType,
      title,
      prompt: input.script || "[uploaded voiceover]",
      duration: input.duration ?? null,
      voicePreference: input.voice ?? null,
      payload: { engine: { kind: input.kind, jobId: input.jobId } },
      studioState: "PRODUCTION",
    },
  });
}
