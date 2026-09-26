import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, join, relative, resolve } from "node:path";
import { EXPLAINER_LIBRARY_VERSION, type ExplainerRegistry, type RegistryEntry, type RegistryReconciliation, type ResolvedRegistryEntry } from "./types";

export const EXPLAINER_LIBRARY_ROOT = resolve(process.cwd(), "runtime-assets", "explainer-motion-v1", "library");

type RegistryFile = {
  release?: string;
  totalEntries?: number;
  entries?: RegistryEntry[];
};

function inside(root: string, candidate: string) {
  const rel = relative(root, candidate);
  return rel === "" || (!rel.startsWith("..") && !isAbsolute(rel));
}

function mappedPath(root: string, value: string | undefined) {
  if (!value) return undefined;
  const candidate = resolve(root, value);
  return inside(root, candidate) && existsSync(candidate) ? candidate : undefined;
}

function manifestId(path: string): string | undefined {
  try {
    const parsed = JSON.parse(readFileSync(path, "utf8")) as { id?: unknown };
    return typeof parsed.id === "string" ? parsed.id : undefined;
  } catch {
    return undefined;
  }
}

function reconciliationFor(root: string, source: RegistryFile): { reconciliation: RegistryReconciliation; entries: ResolvedRegistryEntry[] } {
  const rawEntries = Array.isArray(source.entries) ? source.entries : [];
  const seen = new Set<string>();
  const duplicateIds: string[] = [];
  const missingManifestMappings: string[] = [];
  const missingSourceMappings: string[] = [];
  const missingPreviewMappings: string[] = [];
  const unsupportedAspectRatioEntries: string[] = [];
  const entries: ResolvedRegistryEntry[] = [];
  const categoryCounts: Record<string, number> = {};
  const supported = new Set(["16:9", "1:1", "9:16"]);

  for (const entry of rawEntries) {
    if (seen.has(entry.id)) duplicateIds.push(entry.id);
    seen.add(entry.id);
    categoryCounts[entry.category] = (categoryCounts[entry.category] ?? 0) + 1;
    // Audio entries are not visual compositions and legitimately omit aspect
    // ratios. Visual entries must declare at least one supported ratio.
    if (entry.category !== "audio" && (!entry.aspectRatios?.length || entry.aspectRatios.some((ratio) => !supported.has(ratio)))) unsupportedAspectRatioEntries.push(entry.id);
    const absoluteManifestPath = mappedPath(root, entry.manifestPath);
    const absoluteSourcePath = mappedPath(root, entry.sourcePath);
    const absolutePreviewPath = mappedPath(root, entry.previewPath);
    const absoluteRegistryPath = mappedPath(root, entry.registryPath);
    if (!absoluteManifestPath || manifestId(absoluteManifestPath) !== entry.id) missingManifestMappings.push(entry.id);
    if (!absoluteSourcePath) missingSourceMappings.push(entry.id);
    if (!absolutePreviewPath) missingPreviewMappings.push(entry.id);
    if (absoluteManifestPath && absoluteSourcePath && absolutePreviewPath && absoluteRegistryPath) {
      entries.push({ ...entry, absoluteManifestPath, absoluteSourcePath, absoluteRegistryPath, absolutePreviewPath });
    }
  }

  return {
    entries,
    reconciliation: {
      release: typeof source.release === "string" ? source.release : "",
      totalEntries: rawEntries.length,
      duplicateIds: [...new Set(duplicateIds)],
      missingManifestMappings: [...new Set(missingManifestMappings)],
      missingSourceMappings: [...new Set(missingSourceMappings)],
      missingPreviewMappings: [...new Set(missingPreviewMappings)],
      unsupportedAspectRatioEntries: [...new Set(unsupportedAspectRatioEntries)],
      categoryCounts,
    },
  };
}

export function assertNoDuplicateRegistryIds(entries: Array<Pick<RegistryEntry, "id">>) {
  const seen = new Set<string>();
  const duplicates = [...new Set(entries.map((entry) => entry.id).filter((id) => seen.has(id) || (seen.add(id), false)))];
  if (duplicates.length) throw new Error(`EXPLAINER_REGISTRY_DUPLICATE_IDS: ${duplicates.join(", ")}`);
  return true;
}

export function assertMappedRegistryEntry(entry: Pick<RegistryEntry, "id" | "manifestPath" | "sourcePath" | "previewPath">, root: string) {
  if (!mappedPath(root, entry.manifestPath) || !mappedPath(root, entry.sourcePath) || !mappedPath(root, entry.previewPath)) throw new Error(`EXPLAINER_REGISTRY_MAPPING_MISSING: ${entry.id}`);
  return true;
}

export function loadExplainerRegistry(options: { root?: string; strict?: boolean } = {}): ExplainerRegistry {
  const root = resolve(options.root ?? EXPLAINER_LIBRARY_ROOT);
  const registryPath = join(root, "manifests", "master-agent-registry.json");
  if (!existsSync(registryPath)) throw new Error("EXPLAINER_REGISTRY_MISSING");
  const source = JSON.parse(readFileSync(registryPath, "utf8")) as RegistryFile;
  const { entries, reconciliation } = reconciliationFor(root, source);
  assertNoDuplicateRegistryIds(source.entries ?? []);
  const expected = source.totalEntries ?? entries.length;
  const failures = [
    reconciliation.release !== EXPLAINER_LIBRARY_VERSION ? `release=${reconciliation.release}` : "",
    reconciliation.totalEntries !== expected ? `total=${reconciliation.totalEntries}/${expected}` : "",
    reconciliation.duplicateIds.length ? `duplicateIds=${reconciliation.duplicateIds.length}` : "",
    reconciliation.missingManifestMappings.length ? `missingManifests=${reconciliation.missingManifestMappings.length}` : "",
    reconciliation.missingSourceMappings.length ? `missingSources=${reconciliation.missingSourceMappings.length}` : "",
    reconciliation.missingPreviewMappings.length ? `missingPreviews=${reconciliation.missingPreviewMappings.length}` : "",
    reconciliation.unsupportedAspectRatioEntries.length ? `unsupportedAspectRatios=${reconciliation.unsupportedAspectRatioEntries.length}` : "",
  ].filter(Boolean);
  if ((options.strict ?? true) && failures.length) throw new Error(`EXPLAINER_REGISTRY_INVALID: ${failures.join(", ")}`);

  const byId = new Map(entries.map((entry) => [entry.id, entry]));
  const byCategory = new Map<string, ResolvedRegistryEntry[]>();
  for (const entry of entries) byCategory.set(entry.category, [...(byCategory.get(entry.category) ?? []), entry]);
  for (const values of byCategory.values()) values.sort((left, right) => (left.order ?? 0) - (right.order ?? 0) || left.id.localeCompare(right.id));
  return {
    release: EXPLAINER_LIBRARY_VERSION,
    entries,
    byId,
    byCategory,
    reconciliation,
    resolve(id: string) {
      const entry = byId.get(id);
      if (!entry) throw new Error(`EXPLAINER_COMPONENT_ID_NOT_FOUND: ${id}`);
      return entry;
    },
    has: (id: string) => byId.has(id),
  };
}

export function registryCounts(registry: ExplainerRegistry) {
  return Object.fromEntries([...registry.byCategory.entries()].map(([category, entries]) => [category, entries.length] as const).sort(([left], [right]) => left.localeCompare(right)));
}
