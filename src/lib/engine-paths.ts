import path from "node:path";

export type EngineKind = "whiteboard" | "explainer" | "presenter";

export function engineDir(kind: EngineKind): string {
  const settings = {
    whiteboard: ["WHITEBOARD_V3_RUNTIME_DIR", "whiteboard-v3-runtime"],
    explainer: ["EXPLAINER_ENGINE_DIR", "explainer-locks"],
    presenter: ["PRESENTER_ENGINE_DIR", "makehuman-lineart"],
  } as const;
  const [variable, fallback] = settings[kind];
  const configured = process.env[variable]?.trim();
  return path.resolve(configured || path.join(process.cwd(), "engine_sources", fallback));
}

export function engineJobsDir(kind: EngineKind): string {
  return path.join(engineDir(kind), "out", `${kind}-jobs`);
}
