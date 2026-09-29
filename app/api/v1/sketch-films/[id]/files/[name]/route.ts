import path from "node:path";
import { existsSync, readFileSync } from "node:fs";
import { requireSession } from "@/lib/route-auth";
import { problem } from "@/lib/http";

export const runtime = "nodejs";

const ENGINE = process.env.SKETCH_FILMS_ENGINE_DIR
  ?? path.join(process.cwd(), "engines", "explainer", "NexStudio_Explainer_Execution_Body_V2");
const JOBS = path.join(ENGINE, "out", "sketch-film-jobs");

export async function GET(request: Request, context: { params: Promise<{ id: string; name: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const { id, name } = await context.params;
  const dir = path.join(JOBS, id);
  const reqPath = path.join(dir, "request.json");
  if (!/^sf-[a-z0-9]{8}$/.test(id) || !existsSync(reqPath))
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Sketch-film job not found", "No sketch-film job with that id exists.");
  const req = JSON.parse(readFileSync(reqPath, "utf8"));
  if (req.userId !== auth.session!.userId)
    return problem(auth.id, 404, "JOB_NOT_FOUND", "Sketch-film job not found", "No sketch-film job with that id exists.");
  const file = path.join(dir, "files", path.basename(name));
  if (!/^[\w.-]+\.mp4$/.test(path.basename(name)) || !existsSync(file))
    return problem(auth.id, 404, "FILE_NOT_FOUND", "Output not found", "That output file does not exist for this job.");
  return new Response(readFileSync(file), {
    headers: { "content-type": "video/mp4", "cache-control": "private, no-store",
               "content-disposition": `inline; filename="${path.basename(name)}"` },
  });
}
