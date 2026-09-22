import type {
  ArtCompositionArchetype,
  ArtDirectedEntityGeometry,
  ArtDirectionEntityParameter,
  ArtDirectionPlan,
  ArtPlacementIntent,
  NormalizedArtRegion,
  ResolvedArtState,
  VisualConstructionPlan,
  VisualEntity,
} from "./types";

export const ART_DIRECTION_RESOLVER_VERSION = "art-direction-resolver.v1";
export const DEFAULT_ART_VIEWPORT = { width: 900, height: 560 } as const;

type ArchetypeProfile = {
  heroRegion: NormalizedArtRegion;
  titleRegion: NormalizedArtRegion;
  focalRegion: NormalizedArtRegion;
  occupancy: [number, number];
  environmentSplit: number;
};

/** Calibrated composition families, expressed in normalized space. */
export const artDirectionArchetypeProfiles: Record<ArtCompositionArchetype, ArchetypeProfile> = {
  "hero-centered": { heroRegion: { x: .2, y: .13, width: .6, height: .72 }, titleRegion: { x: .08, y: .06, width: .42, height: .2 }, focalRegion: { x: .18, y: .1, width: .64, height: .78 }, occupancy: [.46, .66], environmentSplit: .68 },
  "hero-with-negative-space": { heroRegion: { x: .48, y: .14, width: .43, height: .72 }, titleRegion: { x: .07, y: .15, width: .36, height: .42 }, focalRegion: { x: .42, y: .09, width: .53, height: .8 }, occupancy: [.48, .65], environmentSplit: .7 },
  "vertical-growth": { heroRegion: { x: .27, y: .08, width: .46, height: .82 }, titleRegion: { x: .06, y: .08, width: .3, height: .2 }, focalRegion: { x: .22, y: .04, width: .56, height: .9 }, occupancy: [.5, .7], environmentSplit: .69 },
  "horizontal-journey": { heroRegion: { x: .06, y: .27, width: .22, height: .48 }, titleRegion: { x: .06, y: .06, width: .48, height: .16 }, focalRegion: { x: .04, y: .18, width: .92, height: .66 }, occupancy: [.42, .58], environmentSplit: .74 },
  cutaway: { heroRegion: { x: .28, y: .08, width: .44, height: .84 }, titleRegion: { x: .06, y: .06, width: .3, height: .17 }, focalRegion: { x: .2, y: .03, width: .6, height: .94 }, occupancy: [.52, .7], environmentSplit: .57 },
  "converging-inputs": { heroRegion: { x: .34, y: .2, width: .34, height: .58 }, titleRegion: { x: .06, y: .05, width: .42, height: .15 }, focalRegion: { x: .23, y: .1, width: .56, height: .79 }, occupancy: [.44, .6], environmentSplit: .73 },
  "branching-system": { heroRegion: { x: .36, y: .28, width: .28, height: .44 }, titleRegion: { x: .06, y: .05, width: .44, height: .16 }, focalRegion: { x: .12, y: .12, width: .76, height: .76 }, occupancy: [.46, .64], environmentSplit: .74 },
  "central-transformation": { heroRegion: { x: .26, y: .15, width: .48, height: .66 }, titleRegion: { x: .08, y: .06, width: .4, height: .16 }, focalRegion: { x: .18, y: .09, width: .64, height: .8 }, occupancy: [.5, .68], environmentSplit: .71 },
  "before-after": { heroRegion: { x: .08, y: .2, width: .36, height: .62 }, titleRegion: { x: .08, y: .05, width: .5, height: .16 }, focalRegion: { x: .05, y: .14, width: .9, height: .72 }, occupancy: [.42, .58], environmentSplit: .72 },
  comparison: { heroRegion: { x: .08, y: .2, width: .34, height: .62 }, titleRegion: { x: .08, y: .05, width: .5, height: .16 }, focalRegion: { x: .05, y: .14, width: .9, height: .72 }, occupancy: [.4, .56], environmentSplit: .72 },
  "macro-detail": { heroRegion: { x: .15, y: .1, width: .7, height: .78 }, titleRegion: { x: .06, y: .06, width: .32, height: .16 }, focalRegion: { x: .1, y: .05, width: .8, height: .88 }, occupancy: [.62, .78], environmentSplit: .72 },
  "wide-reveal": { heroRegion: { x: .18, y: .07, width: .64, height: .86 }, titleRegion: { x: .06, y: .06, width: .36, height: .15 }, focalRegion: { x: .1, y: .03, width: .8, height: .93 }, occupancy: [.48, .64], environmentSplit: .65 },
  "layered-environment": { heroRegion: { x: .24, y: .14, width: .52, height: .68 }, titleRegion: { x: .06, y: .05, width: .38, height: .17 }, focalRegion: { x: .16, y: .08, width: .68, height: .84 }, occupancy: [.46, .64], environmentSplit: .62 },
};

const maturityScale: Record<NonNullable<ArtDirectionEntityParameter["maturity"]>, number> = { nascent: .52, early: .68, developing: .84, established: 1, developed: 1.14 };
const explicitScale: Record<NonNullable<ArtDirectionEntityParameter["scaleIntent"]>, number> = { tiny: .42, small: .62, medium: .82, large: 1.05, heroic: 1.22 };
const branchCounts: Record<NonNullable<ArtDirectionEntityParameter["branchingComplexity"]>, number> = { none: 0, low: 2, moderate: 3, high: 5 };

const round = (value: number) => Math.round(value * 100) / 100;
const pointIn = (region: NormalizedArtRegion, width: number, height: number) => ({ x: round((region.x + region.width / 2) * width), y: round((region.y + region.height / 2) * height) });
const hash = (value: string) => [...value].reduce((result, character) => ((result * 31) + character.charCodeAt(0)) >>> 0, 2166136261);
const signedVariation = (value: string, magnitude: number) => (((hash(value) % 2001) / 1000) - 1) * magnitude;

function regionForPlacement(intent: ArtPlacementIntent, profile: ArchetypeProfile): NormalizedArtRegion {
  const regions: Partial<Record<ArtPlacementIntent, NormalizedArtRegion>> = {
    center: profile.heroRegion, "upper-left": { x: .08, y: .12, width: .28, height: .3 }, "upper-center": { x: .36, y: .1, width: .28, height: .3 }, "upper-right": { x: .66, y: .12, width: .26, height: .3 },
    "middle-left": { x: .06, y: .33, width: .28, height: .34 }, "middle-right": { x: .66, y: .33, width: .28, height: .34 }, "lower-left": { x: .08, y: .62, width: .28, height: .27 }, "lower-center": { x: .36, y: .62, width: .28, height: .27 }, "lower-right": { x: .66, y: .62, width: .26, height: .27 },
    "environment-layer": { x: .02, y: profile.environmentSplit, width: .96, height: 1 - profile.environmentSplit },
  };
  return regions[intent] ?? profile.heroRegion;
}

function basePositions(construction: VisualConstructionPlan, plan: ArtDirectionPlan, profile: ArchetypeProfile, width: number, height: number) {
  const all = [construction.heroEntity, ...construction.supportingEntities];
  const positions = new Map<string, { x: number; y: number }>();
  positions.set(plan.hero.entityId, pointIn(regionForPlacement(plan.hero.placementIntent, profile), width, height));
  const roles = plan.supportingRoles.filter((role) => role.role !== "environment" && role.role !== "attached-child");
  roles.forEach((role, index) => {
    let x = width * (.18 + ((index % 4) * .21));
    let y = height * (.25 + (Math.floor(index / 4) * .42));
    if (plan.compositionArchetype === "horizontal-journey") { x = width * (.12 + ((index + 1) / Math.max(2, roles.length + 1)) * .76); y = height * .52; }
    if (plan.compositionArchetype === "converging-inputs") { const side = index % 2 ? 1 : -1; x = width * (.5 + side * .34); y = height * (.23 + Math.floor(index / 2) * .24); }
    if (plan.compositionArchetype === "branching-system") { const angle = -Math.PI * .86 + (index / Math.max(1, roles.length - 1)) * Math.PI * .72; x = width * .5 + Math.cos(angle) * width * .34; y = height * .55 + Math.sin(angle) * height * .32; }
    if (plan.compositionArchetype === "comparison" || plan.compositionArchetype === "before-after") { x = width * .72; y = height * .52; }
    positions.set(role.entityId, { x: round(x), y: round(y) });
  });
  for (const role of plan.supportingRoles.filter((candidate) => candidate.role === "environment")) positions.set(role.entityId, { x: width / 2, y: round(height * profile.environmentSplit) });
  for (const entity of all) if (!positions.has(entity.id)) positions.set(entity.id, pointIn(regionForPlacement(plan.supportingRoles.find((role) => role.entityId === entity.id)?.placementIntent ?? "around-hero", profile), width, height));
  const hasEnvironment = all.some((entity) => entity.type === "environment");
  const structural = all.filter((entity) => entity.visualClass === "organic-path" || entity.visualClass === "branching-path" || entity.visualClass === "group" || entity.representation === "stem" || entity.representation === "branch");
  if (hasEnvironment && structural.length && ["cutaway", "vertical-growth", "wide-reveal", "converging-inputs"].includes(plan.compositionArchetype)) {
    const base = { x: positions.get(plan.hero.entityId)?.x ?? width / 2, y: round(height * profile.environmentSplit) };
    for (const entity of structural) positions.set(entity.id, base);
    for (const relation of construction.relationships.filter((candidate) => candidate.kind === "grows-from")) {
      const target = all.find((entity) => entity.id === relation.to);
      if (target && target.visualClass === "organic-object") positions.set(target.id, base);
    }
  }
  for (const relation of construction.relationships.filter((candidate) => candidate.kind === "attaches-to")) {
    const source = all.find((entity) => entity.id === relation.from), target = all.find((entity) => entity.id === relation.to);
    if (source && target?.type === "environment") positions.set(source.id, { x: positions.get(source.id)?.x ?? width / 2, y: round(height * profile.environmentSplit - 34) });
  }
  for (const entity of all.filter((candidate) => candidate.type === "energy" || candidate.visualClass === "field")) positions.set(entity.id, { x: round(width * .82), y: round(height * .18) });
  for (const relation of construction.relationships.filter((candidate) => ["flows-to", "feeds", "passes-to", "routes-to"].includes(candidate.kind))) {
    const source = all.find((entity) => entity.id === relation.from);
    const target = positions.get(relation.to);
    if (!source || !target || source.type === "energy") continue;
    if (relation.direction === "down") positions.set(source.id, { x: target.x, y: round(height * .24) });
    else if (relation.direction === "up") positions.set(source.id, { x: round(width * .18), y: round(height * .78) });
  }
  return positions;
}

function organicPath(entity: VisualEntity, origin: { x: number; y: number }, parameter: ArtDirectionEntityParameter | undefined, scale: number) {
  const orientation = parameter?.orientation ?? "up";
  const formLengthFactor = parameter?.form === "compact" ? .84 : parameter?.form === "expanded" ? .94 : 1;
  const length = 190 * scale * formLengthFactor;
  const sideways = signedVariation(entity.id, 16) * scale;
  const end = orientation === "down" ? { x: origin.x + sideways, y: origin.y + length } : orientation === "left" ? { x: origin.x - length, y: origin.y + sideways } : orientation === "right" ? { x: origin.x + length, y: origin.y + sideways } : { x: origin.x + sideways, y: origin.y - length };
  const horizontal = orientation === "left" || orientation === "right";
  const c1 = horizontal ? { x: origin.x + (end.x - origin.x) * .34, y: origin.y - 12 * scale } : { x: origin.x + 8 * scale, y: origin.y + (end.y - origin.y) * .34 };
  const c2 = horizontal ? { x: origin.x + (end.x - origin.x) * .7, y: end.y + 12 * scale } : { x: end.x - 8 * scale, y: origin.y + (end.y - origin.y) * .72 };
  return { d: `M${round(origin.x)} ${round(origin.y)} C${round(c1.x)} ${round(c1.y)} ${round(c2.x)} ${round(c2.y)} ${round(end.x)} ${round(end.y)}`, role: "primary-path", strokeWidth: round(Math.max(7, 11 * scale)) };
}

function branchingPaths(entity: VisualEntity, origin: { x: number; y: number }, parameter: ArtDirectionEntityParameter | undefined, scale: number) {
  const orientation = parameter?.orientation ?? "down";
  const sign = orientation === "up" ? -1 : 1;
  const length = 185 * scale;
  const count = branchCounts[parameter?.branchingComplexity ?? "low"];
  const endY = origin.y + sign * length;
  const paths = [{ d: `M${round(origin.x)} ${round(origin.y)} C${round(origin.x - 4 * scale)} ${round(origin.y + sign * length * .36)} ${round(origin.x + 9 * scale)} ${round(origin.y + sign * length * .68)} ${round(origin.x + signedVariation(entity.id, 10) * scale)} ${round(endY)}`, role: "primary-branch", strokeWidth: round(Math.max(7, 11 * scale)) }];
  for (let index = 0; index < count; index += 1) {
    const side = index % 2 ? 1 : -1;
    const t = .3 + index * (.48 / Math.max(1, count));
    const startY = origin.y + sign * length * t;
    const reach = (48 + index * 9) * scale;
    paths.push({ d: `M${round(origin.x)} ${round(startY)} C${round(origin.x + side * reach * .28)} ${round(startY + sign * 10 * scale)} ${round(origin.x + side * reach * .68)} ${round(startY + sign * 29 * scale)} ${round(origin.x + side * reach)} ${round(startY + sign * 48 * scale)}`, role: "secondary-branch", strokeWidth: round(Math.max(3.5, (7 - index * .7) * scale)) });
  }
  return paths;
}

function geometryFor(
  entity: VisualEntity,
  position: { x: number; y: number },
  parameter: ArtDirectionEntityParameter | undefined,
  plan: ArtDirectionPlan,
  hero: boolean,
  viewport = DEFAULT_ART_VIEWPORT,
  inheritedCompositeScale = 1,
): ArtDirectedEntityGeometry {
  const profile = artDirectionArchetypeProfiles[plan.compositionArchetype];
  const developsGeometry = entity.visualClass === "organic-path" || entity.visualClass === "branching-path" || entity.visualClass === "attached-surface" || entity.visualClass === "group" || entity.type === "growth-structure";
  const maturity = developsGeometry ? maturityScale[parameter?.maturity ?? "established"] : 1;
  const scaleIntent = explicitScale[parameter?.scaleIntent ?? (hero ? "heroic" : "medium")];
  const occupancyTarget = profile.occupancy[0] + (profile.occupancy[1] - profile.occupancy[0]) * plan.hero.prominence;
  // Composite/group heroes carry art-directed prominence into their structural
  // descendants. Without this, a large semantic hero could resolve to a large
  // invisible group anchor while its stem/branches/attached surfaces remained
  // at generic support scale, making the actual visible subject inexplicably
  // small. The multiplier is bounded and relationship-driven, not topic-driven.
  const scale = round(Math.max(.42, Math.min(1.65, maturity * scaleIntent * (hero ? .68 + occupancyTarget * .56 : .9) * inheritedCompositeScale)));
  const geometry: ArtDirectedEntityGeometry = { x: position.x, y: position.y, scale, visible: parameter?.visibility !== "hidden", showLabel: entity.importance === "annotation" };
  if (entity.representation === "seed" || entity.representation === "ellipse" || entity.representation === "organic-blob") { geometry.width = round(112 * scale); geometry.height = round(74 * scale); geometry.rotation = round(signedVariation(entity.id, 7)); }
  if (entity.visualClass === "organic-path" || entity.representation === "stem") {
    geometry.paths = [organicPath(entity, position, parameter, scale)];
    geometry.strokeWidth = round(Math.max(7, 11 * scale));
    const orientation = parameter?.orientation ?? "up";
    const signX = orientation === "right" ? 1 : orientation === "left" ? -1 : 0;
    const signY = orientation === "down" ? 1 : orientation === "up" ? -1 : 0;
    const length = 190 * scale;
    const along = (fraction: number) => ({
      x: round(position.x + signX * length * fraction),
      y: round(position.y + signY * length * fraction),
    });
    geometry.anchors = {
      growthOrigin: { ...position },
      bottom: { ...position },
      top: along(.98),
      attachment: along(.56),
      "attachment-1": along(.38),
      "attachment-2": along(.52),
      "attachment-3": along(.66),
      "attachment-4": along(.79),
      "attachment-5": along(.9),
    };
  }
  if (entity.visualClass === "branching-path" || entity.representation === "branch") { const availableScale = parameter?.orientation === "down" && ["cutaway", "wide-reveal", "layered-environment", "converging-inputs"].includes(plan.compositionArchetype) ? (viewport.height * (1 - profile.environmentSplit) * .88) / 185 : scale; const pathScale = Math.min(scale, availableScale); geometry.scale = round(pathScale); geometry.paths = branchingPaths(entity, position, parameter, pathScale); geometry.branchCount = branchCounts[parameter?.branchingComplexity ?? "low"]; geometry.strokeWidth = round(Math.max(7, 11 * pathScale)); geometry.anchors = { growthOrigin: { ...position }, attachment: { ...position } }; }
  if (entity.type === "environment") { geometry.y = round(position.y); geometry.height = round(viewport.height * (1 - profile.environmentSplit)); geometry.width = viewport.width; geometry.scale = 1; }
  if (entity.visualClass === "particle") geometry.width = round(44 * scale);
  return geometry;
}

function attachChildren(construction: VisualConstructionPlan, plan: ArtDirectionPlan, geometries: Record<string, ArtDirectedEntityGeometry>, viewport = DEFAULT_ART_VIEWPORT) {
  const all = [construction.heroEntity, ...construction.supportingEntities];
  const attachments = construction.relationships.filter((relation) => ["grows-from", "branches-from", "attaches-to"].includes(relation.kind));
  for (let pass = 0; pass < 3; pass += 1) for (const relation of attachments) {
    const child = all.find((entity) => entity.id === relation.from);
    const parent = all.find((entity) => entity.id === relation.to);
    if (!child || !parent) continue;
    const parentGeometry = geometries[parent.id];
    let childGeometry = geometries[child.id];
    const parameter = plan.stateParameters.find((candidate) => candidate.entityId === child.id);
    const origin = { x: Number(parentGeometry.x ?? 450), y: Number(parentGeometry.y ?? 360) };
    if (child.visualClass === "organic-path" || child.visualClass === "branching-path" || child.visualClass === "group" || child.representation === "stem" || child.representation === "branch") {
      const compositeScale = parent.visualClass === "group"
        ? Math.max(.9, Math.min(1.45, Math.max(Number(parentGeometry.scale ?? 1), 1.12 + plan.hero.prominence * .32)))
        : 1;
      childGeometry = geometryFor(child, origin, parameter, plan, child.id === plan.hero.entityId, viewport, compositeScale);
      geometries[child.id] = childGeometry;
      continue;
    }
    const childRole = plan.supportingRoles.find((candidate) => candidate.entityId === child.id);
    if (!(child.visualClass === "attached-surface" || childRole?.role === "attached-child")) continue;
    const count = Math.max(1, Math.min(8, parameter?.count ?? 2));
    const originX = Number(parentGeometry.x ?? 450);
    const originY = Number(parentGeometry.y ?? 360);
    const parentScale = Number(parentGeometry.scale ?? 1);
    const parentAnchors = parentGeometry.anchors ?? {};
    const parentParameter = plan.stateParameters.find((candidate) => candidate.entityId === parent.id);
    const spreadFactor = parentParameter?.form === "expanded" ? 1.18 : parentParameter?.form === "compact" ? .9 : 1;
    const surfaceScale = Math.max(.72, Math.min(1.48, Math.max(parentScale, Number(childGeometry.scale ?? 1)) * (parentParameter?.form === "expanded" ? 1.08 : 1)));
    childGeometry.items = Array.from({ length: count }, (_, index) => {
      const side = index % 2 ? 1 : -1;
      // Attached surfaces should occupy distinct parent anchors rather than
      // stacking opposing pairs on exactly the same joint. This generic
      // stagger produces a readable silhouette for leaves, document tabs,
      // hinged panels and other attached surfaces while keeping every child
      // physically born at a real attachment point.
      const slotIndex = Math.min(5, Math.max(1, 1 + index));
      const tier = Math.floor(index / 2);
      const preferred = parentAnchors[`attachment-${slotIndex}`] ?? parentAnchors.attachment;
      const anchor = preferred
        ? { x: round(preferred.x + signedVariation(`${child.id}:${index}:x`, 1.5)), y: round(preferred.y + signedVariation(`${child.id}:${index}:y`, 1.2)) }
        : { x: round(originX + signedVariation(`${child.id}:${index}`, 2.5)), y: round(originY - parentScale * (64 + index * 34)) };
      const sizeVariation = 1 + signedVariation(`${child.id}:${index}:size`, .055);
      const progressiveScale = Math.max(.76, 1 - index * .055);
      const surfaceWidth = Math.max(68, (child.id === plan.hero.entityId ? 150 : 122) * surfaceScale * progressiveScale * sizeVariation);
      const reach = surfaceWidth * (.39 + signedVariation(`${child.id}:${index}:reach`, .015)) * spreadFactor;
      const centerX = anchor.x + side * reach;
      const centerY = anchor.y + signedVariation(`${child.id}:${index}:lift`, 3.6) - tier * 1.5 * parentScale;
      const rotation = side * (18 + Math.min(10, index * 2.2)) + signedVariation(`${child.id}:${index}:rotation`, 3.2);
      return { x: round(centerX), y: round(centerY), width: round(surfaceWidth), height: round(surfaceWidth * (.32 + signedVariation(`${child.id}:${index}:shape`, .018))), rotation: round(rotation), anchor, pivot: anchor };
    });
    childGeometry.count = count;
    childGeometry.x = Number(parentAnchors.attachment?.x ?? originX);
    childGeometry.y = Number(parentAnchors.attachment?.y ?? round(originY - 72 * parentScale));
    childGeometry.anchors = { attachment: { x: childGeometry.x, y: childGeometry.y } };
  }
}

function qualityFor(plan: ArtDirectionPlan, construction: VisualConstructionPlan, geometries: Record<string, ArtDirectedEntityGeometry>) {
  const hero = geometries[plan.hero.entityId];
  const attachments = plan.supportingRoles.filter((role) => role.role === "attached-child");
  const attachmentIntegrity = attachments.every((role) => (geometries[role.entityId]?.items ?? []).every((item) => Boolean(item.anchor)));
  return {
    quality: {
      heroScale: Number(hero?.scale ?? 1),
      visualBalance: `${plan.balance.horizontal}/${plan.balance.vertical}/${plan.balance.asymmetry}`,
      silhouetteQuality: plan.qualityIntent.silhouette,
      negativeSpaceIntent: `${plan.negativeSpace.intent}${plan.negativeSpace.preferredRegion ? `:${plan.negativeSpace.preferredRegion}` : ""}`,
      subjectReadability: plan.qualityIntent.readability,
      attachmentQuality: attachments.length ? (attachmentIntegrity ? "touching-anchor" : "invalid") : "not-applicable",
    },
    metrics: { heroProminence: plan.hero.prominence, meaningfulOccupancyTarget: plan.hero.prominence, attachmentIntegrity: attachmentIntegrity ? 1 : 0, archetypeVariety: 1, progressionIntent: plan.continuityTransform.allowGrowth ? 1 : 0 },
  };
}

export function resolveArtDirectionPlan(construction: VisualConstructionPlan, plan: ArtDirectionPlan, viewport = DEFAULT_ART_VIEWPORT): ResolvedArtState {
  if (construction.sceneId !== plan.sceneId) throw new Error(`ART_DIRECTION_SCENE_MISMATCH: ${construction.sceneId} != ${plan.sceneId}`);
  const ids = new Set([construction.heroEntity.id, ...construction.supportingEntities.map((entity) => entity.id)]);
  if (!ids.has(plan.hero.entityId)) throw new Error(`ART_DIRECTION_UNKNOWN_HERO: ${plan.hero.entityId}`);
  const profile = artDirectionArchetypeProfiles[plan.compositionArchetype];
  const positions = basePositions(construction, plan, profile, viewport.width, viewport.height);
  const entities = Object.fromEntries([construction.heroEntity, ...construction.supportingEntities].map((entity) => [entity.id, geometryFor(entity, positions.get(entity.id)!, plan.stateParameters.find((parameter) => parameter.entityId === entity.id), plan, entity.id === plan.hero.entityId, viewport)]));

  // A small junction/source object can remain the semantic hero while multiple
  // visible structures grow from it. In growth/cutaway compositions the
  // settled silhouette should be owned by the complete connected structure,
  // not by an oversized junction. Cap only the junction's *visual* scale while
  // preserving identity and letting its structural descendants carry the hero
  // prominence. This is topology- and archetype-driven, never topic-driven.
  const heroEntity = construction.heroEntity;
  const structuralChildren = construction.relationships.filter((relation) => relation.to === heroEntity.id && ["grows-from", "branches-from", "attaches-to"].includes(relation.kind));
  const junctionLikeHero = heroEntity.visualClass === "organic-object" && structuralChildren.length >= 2 && ["cutaway", "vertical-growth", "wide-reveal"].includes(plan.compositionArchetype);
  if (junctionLikeHero) {
    const heroGeometry = entities[heroEntity.id];
    const currentScale = Number(heroGeometry?.scale ?? 1);
    const targetScale = round(Math.min(currentScale, .82));
    if (heroGeometry && targetScale < currentScale) {
      const ratio = targetScale / currentScale;
      heroGeometry.scale = targetScale;
      if (heroGeometry.width) heroGeometry.width = round(heroGeometry.width * ratio);
      if (heroGeometry.height) heroGeometry.height = round(heroGeometry.height * ratio);
    }
  }

  attachChildren(construction, plan, entities, viewport);
  const quality = qualityFor(plan, construction, entities);
  return {
    id: `${plan.sceneId}:resolved-key-state`, label: plan.compositionArchetype, sceneId: plan.sceneId, planId: plan.id, compositionArchetype: plan.compositionArchetype,
    viewport: { width: viewport.width, height: viewport.height, aspectRatio: `${viewport.width}:${viewport.height}` },
    regions: { hero: profile.heroRegion, typography: profile.titleRegion, focal: profile.focalRegion, environmentAbove: { x: 0, y: 0, width: 1, height: profile.environmentSplit }, environmentBelow: { x: 0, y: profile.environmentSplit, width: 1, height: 1 - profile.environmentSplit } },
    entities, quality: quality.quality, metrics: quality.metrics, resultPersistenceFrames: 24,
  };
}

export function resolveArtDirectionSequence(constructions: VisualConstructionPlan[], plans: readonly ArtDirectionPlan[], viewport = DEFAULT_ART_VIEWPORT): VisualConstructionPlan[] {
  let previousState: ResolvedArtState | undefined;
  let previousConstruction: VisualConstructionPlan | undefined;
  return constructions.map((construction) => {
    const plan = plans.find((candidate) => candidate.sceneId === construction.sceneId);
    if (!plan) throw new Error(`ART_DIRECTION_PLAN_MISSING: ${construction.sceneId}`);
    const state = resolveArtDirectionPlan(construction, plan, viewport);
    if (plan.continuityTransform.preserveIdentity) {
      for (const [entityId, geometry] of Object.entries(state.entities)) {
        const previousGeometry = previousState?.entities[entityId];
        if (geometry.items?.length) {
          const priorCount = previousGeometry?.items?.length ?? 0;
          geometry.items = geometry.items.map((item, index) => ({ ...item, continuityRole: index < priorCount ? "existing" : "new" }));
        }
        if (geometry.paths?.length) {
          const priorCount = previousGeometry?.paths?.length ?? 0;
          geometry.paths = geometry.paths.map((path, index) => ({ ...path, continuityRole: index < priorCount ? "existing" : "new" }));
        }
      }
    }
    const profile = artDirectionArchetypeProfiles[plan.compositionArchetype];
    const correspondence = previousState && previousConstruction ? [{ fromEntityId: previousConstruction.heroEntity.id, toEntityId: construction.heroEntity.id, fromAnchor: "center", toAnchor: "center" }] : [];
    const resolved: VisualConstructionPlan = {
      ...construction,
      artDirectionPlan: plan,
      artDirection: {
        planId: plan.id,
        resolvedBy: ART_DIRECTION_RESOLVER_VERSION,
        activeStateId: state.id,
        states: [state],
        titleTreatment: plan.typography.treatment,
        typographyProminence: plan.typography.prominence,
        typographyRegion: profile.titleRegion,
        cameraCrop: { focalEntity: plan.framing.focalEntity, safeRegion: profile.focalRegion, shotSize: plan.framing.shotSize, cropPolicy: plan.framing.cropPolicy },
        continuityTransform: previousState && plan.continuityTransform.preserveIdentity ? { fromStateId: previousState.id, toStateId: state.id, anchorCorrespondence: correspondence, durationFrames: 24, easingProfile: "organic-controlled" } : undefined,
        resultPersistenceFrames: 24,
        cameraActionExpected: plan.framing.shotSize !== "medium" || plan.compositionArchetype === "vertical-growth" || plan.compositionArchetype === "wide-reveal",
        cameraTargetTrackingErrorMax: .12,
        surface: { fill: "#fffdf7", stroke: "#121212", strokeWidth: 0, radius: 0, opacity: 1 },
      },
    };
    previousState = state;
    previousConstruction = construction;
    return resolved;
  });
}
