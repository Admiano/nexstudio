import path from "node:path";
import { existsSync, readFileSync } from "node:fs";
import { requireSession } from "@/lib/route-auth";
import { problem } from "@/lib/http";
import { resolveOutputFile } from "@/lib/storage";

export const runtime = "nodejs";

const ENGINE = process.env.EXPLAINER_ENGINE_DIR
  ?? path.join(process.cwd(), "engine_sources", "explainer-locks");
const JOBS = path.join(ENGINE, "out", "explainer-jobs");

export async function GET(request: Request, context: { params: Promise<{ id: string; name: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const { id, name } = await context.params;
  const dir = path.join(JOBS, id);
  const reqPath = path.join(dir, "request.json");
  if (!/^xr-[a-z0-9]{8}$/.test(id) || !existsSync(reqPath))
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Explainer job not found", "No explainer job with that id exists.");
  const req = JSON.parse(readFileSync(reqPath, "utf8"));
  if (req.userId !== auth.session!.userId)
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Explainer job not found", "No explainer job with that id exists.");
  const resolved = await resolveOutputFile(dir, "explainer", id, name);
  if (!resolved)
    return problem(auth.id, 404, "FILE_NOT_FOUND", "Output not found", "That output file does not exist for this job.");
  if (resolved.kind === "redirect")
    return Response.redirect(resolved.url, 302);
  return new Response(readFileSync(resolved.filePath), {
    headers: { "content-type": "video/mp4", "cache-control": "private, no-store",
               "content-disposition": `inline; filename="${path.basename(name)}"` },
  });
}
