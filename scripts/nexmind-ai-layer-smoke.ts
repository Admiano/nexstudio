import "dotenv/config";
import { callNexMindDetailed, parseProviderJson } from "../src/lib/nexmind";
import { nexMindRoleRouting } from "../src/lib/nexmind-routing";

// Smoke test for the standalone AI API layer (the same transport used by
// studio_plan_preview). Resolves the configured route from env, makes one real
// provider call, and verifies a parseable JSON answer comes back.
async function main() {
  const routing = nexMindRoleRouting("studio_plan_preview");
  console.log(`route: ${routing.provider}/${routing.model} @ ${routing.baseUrl} mode=${routing.apiMode} keyEnv=${routing.apiKeyEnv} source=${routing.source}`);

  const schema = {
    type: "object",
    additionalProperties: false,
    required: ["probe", "ok"],
    properties: {
      probe: { type: "string" },
      ok: { type: "boolean" },
    },
  };

  const result = await callNexMindDetailed(
    [
      { role: "system", content: "You are a connectivity probe. Reply with one JSON object only." },
      { role: "user", content: 'Return {"probe":"nexmind-ai-layer","ok":true} exactly.' },
    ],
    {
      model: routing.model,
      apiUrl: routing.baseUrl,
      apiKey: process.env[routing.apiKeyEnv]?.trim(),
      apiMode: routing.apiMode,
      maxTokens: 200,
      timeoutMs: 30_000,
      retries: 0,
      requestIdempotencyKey: "nexmind-ai-layer-smoke",
      jsonSchema: { name: "ai_layer_smoke", schema },
    },
  );

  console.log(`providerRequestId: ${result.providerRequestId ?? "none"}`);
  console.log(`usage: ${JSON.stringify(result.usage)}`);
  const parsed = parseProviderJson(result.content) as { probe?: string; ok?: boolean };
  if (parsed.probe !== "nexmind-ai-layer" || parsed.ok !== true) {
    throw new Error(`SMOKE_UNEXPECTED_OUTPUT:${result.content.slice(0, 300)}`);
  }
  console.log("AI_LAYER_SMOKE_PASS");
}

main().catch((error) => {
  console.error(`AI_LAYER_SMOKE_FAIL: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
});
