// Deterministic brief → narration fallback for environments with no NexMind provider key.
// Shapes the user's brief into per-beat spoken lines — it never invents content.

const IMPERATIVE_PREFIXES = [
  /^(please\s+)?(create|make|produce|generate|write|craft|tell|give|build|show|explain|do|prepare|describe|narrate|voice)\b[^,.!?;]*?(about|a|an|the|how|why|of|on)\s+/i,
  /^(i\s+want|i\s+need|i['’]?d\s+like|can\s+you|could\s+you|we\s+want|we\s+need)\b[^,.!?;]*?(a|an|the|to)\s+/i,
];

const FILLER = [
  /^(so\s+|ok(?:ay)?\s+|well\s+|basically\s+)+/i,
  /\s+(please|kindly)\.?$/i,
];

function normalizeSentence(raw: string): string {
  let s = raw.trim();
  for (const re of IMPERATIVE_PREFIXES) s = s.replace(re, "");
  for (const re of FILLER) s = s.replace(re, "");
  s = s.replace(/\s+/g, " ").trim().replace(/^[.\s,;:!?-]+/, "");
  if (!s) return "";
  s = s.charAt(0).toUpperCase() + s.slice(1);
  if (!/[.!?…]$/.test(s)) s += ".";
  return s;
}

function sentencesOf(brief: string): string[] {
  // Split on sentence boundaries; on semicolons/coordinating commas when too few.
  let parts = brief.split(/(?<=[.!?…])\s+/).map((p) => p.trim()).filter(Boolean);
  if (parts.length < 3) {
    parts = parts.flatMap((p) => p.split(/;\s+|,\s+(?=(?:and|but|while|then|as|when|so|which|who|that)\b)/i));
  }
  return parts.map(normalizeSentence).filter(Boolean);
}

export interface LocalScriptResult { lines: string[]; title: string }

export function writeLocalScript(brief: string, duration: number, beats?: { purposeTitle: string; description: string }[]): LocalScriptResult {
  const core = sentencesOf(brief);
  const target = Math.max(4, Math.min(beats?.length ?? 6, 12, Math.round(duration / 7)));

  // Fewer sentences than beats → each sentence is its own board, no repetition.
  if (core.length <= target) {
    const title = (core[0] ?? brief).replace(/[.!?…]+$/, "").split(/\s+/).slice(0, 8).join(" ") || "Untitled";
    return { lines: core, title };
  }
  // More sentences than beats → merge evenly into ≤target segments.
  const lines: string[] = [];
  const copy = [...core];
  while (lines.length < target && copy.length) {
    const take = Math.max(1, Math.ceil(copy.length / (target - lines.length)));
    const seg = copy.splice(0, take).join(" ");
    lines.push(seg.length > 220 ? seg.slice(0, 217).trimEnd() + "…" : seg);
  }
  const title = (core[0] ?? brief)
    .replace(/[.!?…]+$/, "")
    .split(/\s+/).slice(0, 8).join(" ") || "Untitled";
  return { lines, title };
}
