import type { SeriesPlanSignature } from "./contracts";

const dimensions = [
  "environments", "silhouettes", "transitions", "cameras", "actorPositions",
  "headlineStructures", "visualMetaphors", "motifs",
] as const;

type Dimension = (typeof dimensions)[number];

function normalized(values: unknown): string[] {
  if (!Array.isArray(values)) return [];
  return [...new Set(values.map(String).map((v) => v.trim().toLowerCase()).filter(Boolean))].sort();
}

export function evaluateSeriesAntiRepetition(input: {
  candidate: SeriesPlanSignature;
  history: SeriesPlanSignature[];
  historyWindow?: number;
  continuityReasons?: Partial<Record<Dimension | "cardGrid" | "floatingObjects", string>>;
}) {
  const window = Math.max(1, Math.min(12, input.historyWindow ?? 2));
  const recent = input.history.slice(-window);
  const collisions: Array<{ dimension: string; repeated: string[]; continuityReason: string | null; blocked: boolean }> = [];

  for (const dimension of dimensions) {
    const candidateValues = normalized(input.candidate[dimension]);
    if (!candidateValues.length) continue;
    const historical = new Set(recent.flatMap((signature) => normalized(signature[dimension])));
    const repeated = candidateValues.filter((value) => historical.has(value));
    if (!repeated.length) continue;
    const continuityReason = input.continuityReasons?.[dimension]?.trim() || null;
    collisions.push({ dimension, repeated, continuityReason, blocked: !continuityReason });
  }
  for (const dimension of ["cardGrid", "floatingObjects"] as const) {
    if (input.candidate[dimension] !== true) continue;
    if (!recent.some((signature) => signature[dimension] === true)) continue;
    const continuityReason = input.continuityReasons?.[dimension]?.trim() || null;
    collisions.push({ dimension, repeated: ["true"], continuityReason, blocked: !continuityReason });
  }

  return {
    historyWindow: window,
    historyCount: recent.length,
    collisions,
    blockedDimensions: collisions.filter((collision) => collision.blocked).map((collision) => collision.dimension),
    passes: collisions.every((collision) => !collision.blocked),
    law: "REPETITION_REQUIRES_CONTINUITY_REASON_OR_RANKED_ALTERNATIVE",
  } as const;
}


