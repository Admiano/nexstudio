import path from "node:path";
import { readFileSync } from "node:fs";
import { engineDir } from "./engine-paths";

type Style = {
  id: string;
  name: string;
  tagline?: string;
  preview?: string | null;
  poster?: string | null;
  variants?: Array<{ id: string; name: string; tagline?: string }>;
};

export function explainerStyles(
  directory = engineDir("explainer"),
  registryPath = path.join(process.cwd(), "services", "studio-family-engines", "site-dispatch.json"),
) {
  const registry = JSON.parse(readFileSync(registryPath, "utf8"));
  const subtypes = registry.families?.explainer?.subtypes ?? {};
  const doc = JSON.parse(readFileSync(path.join(directory, "styles.json"), "utf8")) as { styles?: Style[] };
  return (doc.styles ?? [])
    .filter((s) => subtypes[s.id]?.status === "CERTIFIED_FOR_DISPATCH")
    .map((s) => ({
      id: s.id, name: s.name, tagline: s.tagline,
      preview: s.preview ?? null, poster: s.poster ?? null,
      variants: (s.variants ?? []).map((v) => ({
        id: `${s.id}.${v.id}`, name: `${s.name} · ${v.name}`, tagline: v.tagline,
      })),
    }));
}
