import { availableParallelism } from "node:os";

/** Auto follows CPU availability; an explicit positive override has no maximum. */
export function renderWorkerOptions(value = process.env.RENDER_WORKER_CONCURRENCY, cores = availableParallelism()) {
  const setting = value?.trim().toLowerCase();
  const concurrency = !setting || setting === "auto" ? cores : Number(setting);
  if (!Number.isSafeInteger(concurrency) || concurrency < 1) {
    throw new Error("RENDER_WORKER_CONCURRENCY must be auto or a positive integer");
  }
  return { batchSize: 1, pollingIntervalSeconds: 2, localConcurrency: concurrency };
}
