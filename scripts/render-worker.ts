// Render worker: drains the site-render pg-boss queue and runs
// site_job_runner.py per job. Run alongside the web app:
//   npm run worker:renders
// Concurrency follows available CPUs by default; a positive override is uncapped.
import { PgBoss, type Job } from "pg-boss";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { RENDER_QUEUE, runRenderJob, type RenderJobPayload } from "../src/lib/render-queue";
import { uploadJobOutputs } from "../src/lib/storage";
import { renderWorkerOptions } from "../src/lib/render-parallelism";

async function main() {
  if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL required");
  const boss = new PgBoss({
    connectionString: process.env.DATABASE_URL,
    schema: "render_queue",
    supervise: false,
  });
  boss.on("error", (e: Error) => console.error("[render-worker]", e));
  await boss.start();
  await boss.createQueue(RENDER_QUEUE);
  const options = renderWorkerOptions();
  await boss.work(RENDER_QUEUE, options, async (jobs: Job<RenderJobPayload>[]) => {
    const payload = jobs[0].data;
    console.log(`[render-worker] start ${payload.family}/${payload.jobId}`);
    const code = await runRenderJob(payload);
    console.log(`[render-worker] exit ${payload.jobId} code=${code}`);
    try {
      const statusPath = path.join(payload.dir, "status.json");
      const status = existsSync(statusPath) ? JSON.parse(readFileSync(statusPath, "utf8")).status : null;
      if (status === "done") {
        const uploaded = await uploadJobOutputs(payload.dir, payload.family, payload.jobId);
        if (uploaded?.length) console.log(`[render-worker] uploaded ${uploaded.length} output(s) for ${payload.jobId}`);
      }
    } catch (e) {
      console.error(`[render-worker] storage upload failed for ${payload.jobId}`, e);
    }
    // The runner always writes a terminal status.json; a nonzero exit is still
    // "complete" for queue purposes — the job itself reports the failure.
  });
  console.log(`[render-worker] listening on ${RENDER_QUEUE} (concurrency=${options.localConcurrency})`);
}

main().catch((e) => { console.error(e); process.exit(1); });
