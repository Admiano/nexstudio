import path from "node:path";
import { existsSync, readFileSync } from "node:fs";
import { requireSession } from "@/lib/route-auth";
import { problem } from "@/lib/http";
import { engineJobsDir } from "@/lib/engine-jobs";

export const runtime = "nodejs";

export async function GET(request: Request, context: { params: Promise<{ id: string; name: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const { id, name } = await context.params;
  const dir = path.join(engineJobsDir("presenter"), id);
  const reqPath = path.join(dir, "request.json");
  if (!/^pr-[a-z0-9]{8}$/.test(id) || !existsSync(reqPath))
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Presenter job not found", "No presenter job with that id exists.");
  const req = JSON.parse(readFileSync(reqPath, "utf8"));
  if (req.userId !== auth.session!.userId)
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Presenter job not found", "No presenter job with that id exists.");
  const base = path.basename(name);
  const file = path.join(dir, "files", base);
  if (!/^[\w.-]+\.mp4$/.test(base) || !existsSync(file))
    return problem(auth.id, 404, "FILE_NOT_FOUND", "Output not found", "That output file does not exist for this job.");
  return new Response(readFileSync(file), {
    headers: { "content-type": "video/mp4", "cache-control": "private, no-store",
               "content-disposition": `inline; filename="${base}"` },
  });
}
