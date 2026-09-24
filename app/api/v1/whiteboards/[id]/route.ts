import path from "node:path";
import { existsSync, readFileSync } from "node:fs";
import { requireSession } from "@/lib/route-auth";
import { json, problem } from "@/lib/http";
import { friendlyEngineError } from "@/lib/engine-jobs";

export const runtime = "nodejs";

const ENGINE = process.env.WHITEBOARD_V3_RUNTIME_DIR
  ?? path.join(process.cwd(), "engine_sources", "whiteboard-v3-runtime");
const JOBS = path.join(ENGINE, "out", "whiteboard-jobs");

export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const { id } = await context.params;
  if (!/^wb-[a-z0-9]{8}$/.test(id))
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Whiteboard job not found", "No whiteboard job with that id exists.");
  const dir = path.join(JOBS, id);
  const reqPath = path.join(dir, "request.json");
  if (!existsSync(reqPath))
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Whiteboard job not found", "No whiteboard job with that id exists.");
  const req = JSON.parse(readFileSync(reqPath, "utf8"));
  if (req.userId !== auth.session!.userId)
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Whiteboard job not found", "No whiteboard job with that id exists.");
  const statusPath = path.join(dir, "status.json");
  const status = existsSync(statusPath) ? JSON.parse(readFileSync(statusPath, "utf8")) : { status: "running" };
  const progressPath = path.join(dir, "progress.json");
  const progress = existsSync(progressPath) ? JSON.parse(readFileSync(progressPath, "utf8")) : null;
  return json({
    jobId: id, type: req.type, voice: req.voice, theme: req.theme, accent: req.accent,
    aspects: req.aspects, createdAt: req.createdAt, progress, ...status,
    ...(status.status === "failed" && !status.error ? { error: friendlyEngineError(dir) } : {}),
  }, auth.id);
}
