import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import { PgBoss } from "pg-boss";
import { config } from "dotenv";
import { renderWorkerOptions } from "../src/lib/render-parallelism";

test("automatic render concurrency follows CPU availability and overrides are uncapped", () => {
  assert.equal(renderWorkerOptions("auto", 12).localConcurrency, 12);
  assert.equal(renderWorkerOptions("", 12).localConcurrency, 12);
  assert.equal(renderWorkerOptions("64", 2).localConcurrency, 64);
  for (const value of ["0", "-1", "1.5", "bad"]) {
    assert.throws(() => renderWorkerOptions(value, 2), /positive integer/);
  }
});

test("pg-boss starts two jobs before either finishes", {
  skip: process.env.RUN_RENDER_QUEUE_INTEGRATION !== "1", timeout: 60000,
}, async () => {
  config({ path: [".env.local", ".env"], quiet: true });
  assert(process.env.DATABASE_URL, "DATABASE_URL required for queue integration test");
  const boss = new PgBoss({ connectionString: process.env.DATABASE_URL, schema: "render_queue", supervise: false });
  boss.on("error", error => { throw error; });
  const queue = `parallelism-check-${randomUUID()}`;
  let started = 0;
  let finished = 0;
  let release!: () => void;
  let bothStarted!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  const overlap = new Promise<void>(resolve => { bothStarted = resolve; });
  let timeout: ReturnType<typeof setTimeout> | undefined;
  try {
    await boss.start();
    await boss.createQueue(queue);
    await boss.send(queue, { check: 1 });
    await boss.send(queue, { check: 2 });
    await boss.work(queue, renderWorkerOptions("2"), async jobs => {
      assert.equal(jobs.length, 1);
      started++;
      if (started === 2) bothStarted();
      await gate;
      finished++;
    });
    await Promise.race([overlap, new Promise<never>((_, reject) => {
      timeout = setTimeout(() => reject(new Error(`Expected overlap; started=${started}, finished=${finished}`)), 15000);
    })]);
    assert.equal(started, 2);
    assert.equal(finished, 0, "both handlers must start while the first remains blocked");
  } finally {
    if (timeout) clearTimeout(timeout);
    release();
    await boss.offWork(queue);
    try { await boss.deleteQueue(queue); }
    finally { await boss.stop(); }
  }
});
