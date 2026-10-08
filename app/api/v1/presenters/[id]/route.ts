import path from "node:path";
import { existsSync, readFileSync } from "node:fs";
import { requireSession } from "@/lib/route-auth";
import { json, problem } from "@/lib/http";
import { engineJobsDir, finalizeCastScope } from "@/lib/engine-jobs";

export const runtime = "nodejs";

export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const { id } = await context.params;
  const missing = () => problem(auth.id, 404, "JOB_NOT_FOUND", "Presenter job not found", "No presenter job with that id exists.");
  if (!/^pr-[a-z0-9]{8}$/.test(id)) return missing();
  const dir = path.join(engineJobsDir("presenter"), id);
  const reqPath = path.join(dir, "request.json");
  if (!existsSync(reqPath)) return missing();
  const req = JSON.parse(readFileSync(reqPath, "utf8"));
  if (req.userId !== auth.session!.userId) return missing();
  const read = (f: string) => existsSync(path.join(dir, f)) ? JSON.parse(readFileSync(path.join(dir, f), "utf8")) : null;
  const status = read("status.json") ?? { status: "running" };
  if (status.status === "done" || status.status === "failed") void finalizeCastScope(dir, status.status);
  return json({
    jobId: id, status: status.status, outputs: status.outputs ?? {}, error: status.error, finishedAt: status.finishedAt,
    aspects: req.aspects, createdAt: req.createdAt, progress: read("progress.json"),
  }, auth.id);
}
