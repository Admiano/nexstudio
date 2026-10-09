// One-off: create Draft rows for engine jobs that predate jobs→Work linkage.
import path from "node:path";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { getPrisma } from "../src/lib/db";

const JOBS: Array<{ kind: "whiteboard" | "explainer"; dir: string }> = [
  { kind: "whiteboard", dir: "engine_sources/whiteboard-v3-runtime/out/whiteboard-jobs" },
  { kind: "explainer", dir: "engine_sources/editorial-motion-v2/out/explainer-jobs" },
];

async function main() {
  const prisma = getPrisma();
  if (!prisma) throw new Error("no prisma");
  let created = 0;
  for (const { kind, dir } of JOBS) {
    const root = path.join(process.cwd(), dir);
    if (!existsSync(root)) continue;
    for (const jobId of readdirSync(root)) {
      const jd = path.join(root, jobId);
      const reqPath = path.join(jd, "request.json");
      if (!existsSync(reqPath)) continue;
      const req = JSON.parse(readFileSync(reqPath, "utf8")) as { userId?: string; script?: string | null; style?: string; type?: string; createdAt?: string };
      if (!req.userId) continue;
      const existing = await prisma.draft.findFirst({ where: { ownerUserId: req.userId, payload: { path: ["engine", "jobId"], equals: jobId } } });
      if (existing) continue;
      const script = req.script ?? "";
      const firstLine = script.split("\n").map((l) => l.trim()).filter(Boolean)[0] ?? "";
      const statusPath = path.join(jd, "status.json");
      const status = existsSync(statusPath) ? (JSON.parse(readFileSync(statusPath, "utf8")) as { status?: string }).status : "unknown";
      await prisma.draft.create({
        data: {
          ownerUserId: req.userId,
          kind: "VIDEO",
          family: kind === "whiteboard" ? "WHITEBOARD" : "EXPLAINER",
          videoType: req.type ?? req.style ?? jobId,
          title: firstLine ? firstLine.split(/\s+/).slice(0, 8).join(" ") : "Untitled production",
          prompt: script || "[uploaded voiceover]",
          payload: { engine: { kind, jobId } },
          studioState: status === "done" ? "COMPLETE" : status === "failed" ? "PRODUCTION_FAILED" : "PRODUCTION",
          createdAt: req.createdAt ? new Date(req.createdAt) : new Date(),
        },
      });
      created++;
      console.log(`drafted ${jobId} (${kind}, ${status})`);
    }
  }
  console.log(`done — ${created} drafts created`);
}

main().finally(() => process.exit(0));
