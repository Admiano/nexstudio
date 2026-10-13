import assert from "node:assert/strict";
import { test } from "node:test";
import { callNexMindDetailed } from "../src/lib/nexmind";

test("Enclave transport can omit unsupported idempotency headers", async () => {
  const originalFetch = globalThis.fetch;
  const originalFlag = process.env.NEXMIND_SEND_IDEMPOTENCY_KEY;
  process.env.NEXMIND_SEND_IDEMPOTENCY_KEY = "false";
  globalThis.fetch = async (_url, init) => {
    const headers = new Headers(init?.headers);
    assert.equal(headers.has("Idempotency-Key"), false);
    const body = JSON.parse(String(init?.body));
    assert.equal(body.model, "configured-model");
    return Response.json({ id: "provider-request", choices: [{ message: { content: '{"ok":true}' } }] });
  };
  try {
    const result = await callNexMindDetailed([{ role: "user", content: "probe" }], {
      model: "configured-model", apiUrl: "https://gateway.invalid/v1", apiKey: "synthetic",
      requestIdempotencyKey: "local-audit-key",
    });
    assert.equal(result.providerRequestId, "provider-request");
    assert.equal(result.content, '{"ok":true}');
  } finally {
    globalThis.fetch = originalFetch;
    if (originalFlag === undefined) delete process.env.NEXMIND_SEND_IDEMPOTENCY_KEY;
    else process.env.NEXMIND_SEND_IDEMPOTENCY_KEY = originalFlag;
  }
});

test("default transport preserves configured idempotency headers", async () => {
  const originalFetch = globalThis.fetch;
  const originalFlag = process.env.NEXMIND_SEND_IDEMPOTENCY_KEY;
  delete process.env.NEXMIND_SEND_IDEMPOTENCY_KEY;
  globalThis.fetch = async (_url, init) => {
    assert.equal(new Headers(init?.headers).get("Idempotency-Key"), "request-key");
    return Response.json({ choices: [{ message: { content: "ok" } }] });
  };
  try {
    await callNexMindDetailed([{ role: "user", content: "probe" }], {
      model: "configured-model", apiUrl: "https://gateway.invalid/v1", apiKey: "synthetic",
      requestIdempotencyKey: "request-key",
    });
  } finally {
    globalThis.fetch = originalFetch;
    if (originalFlag === undefined) delete process.env.NEXMIND_SEND_IDEMPOTENCY_KEY;
    else process.env.NEXMIND_SEND_IDEMPOTENCY_KEY = originalFlag;
  }
});
