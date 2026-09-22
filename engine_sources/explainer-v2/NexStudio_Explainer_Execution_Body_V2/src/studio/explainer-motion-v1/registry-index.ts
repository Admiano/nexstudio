import type { ExplainerRegistry, ResolvedRegistryEntry } from "./types";

export function entriesFor(registry: ExplainerRegistry, category: string): ResolvedRegistryEntry[] {
  return [...(registry.byCategory.get(category) ?? [])];
}

export function entryBySlug(registry: ExplainerRegistry, category: string, slug: string): ResolvedRegistryEntry | undefined {
  const normalized = slug.toLowerCase().replace(/\s+/g, "-");
  return entriesFor(registry, category).find((entry) => entry.slug === normalized || entry.id.includes(`.${normalized}.`));
}

export function findComponent(registry: ExplainerRegistry, reference: string, categories: string[] = []): ResolvedRegistryEntry | undefined {
  if (registry.has(reference)) return registry.resolve(reference);
  const normalized = reference.toLowerCase().replace(/\s+/g, "-");
  const candidates = (categories.length ? categories.flatMap((category) => entriesFor(registry, category)) : registry.entries)
    .filter((entry) => entry.slug === normalized || entry.id.includes(`.${normalized}.`) || entry.name?.toLowerCase() === reference.toLowerCase());
  return candidates.sort((left, right) => (left.order ?? 0) - (right.order ?? 0) || left.id.localeCompare(right.id))[0];
}

export function assertRegistryIds(registry: ExplainerRegistry, ids: string[]) {
  const missing = [...new Set(ids.filter((id) => !registry.has(id)))];
  if (missing.length) throw new Error(`EXPLAINER_COMPONENT_ID_NOT_FOUND: ${missing.join(", ")}`);
}
