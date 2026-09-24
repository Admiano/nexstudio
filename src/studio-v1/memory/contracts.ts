export const STUDIO_MEMORY_SCOPES = ["ACCOUNT", "BRAND", "CAST", "SERIES", "PRODUCTION"] as const;
export type StudioMemoryScopeName = (typeof STUDIO_MEMORY_SCOPES)[number];

export const STUDIO_MEMORY_WRITE_MODES = [
  "THIS_PRODUCTION_ONLY",
  "REMEMBER_FOR_BRAND",
  "REMEMBER_FOR_SERIES",
  "UPDATE_CHARACTER_GOING_FORWARD",
  "UPDATE_FROM_FUTURE_EPISODE",
] as const;
export type StudioMemoryWriteModeName = (typeof STUDIO_MEMORY_WRITE_MODES)[number];

export type StudioMemoryProvenance = {
  source: "CUSTOMER" | "PRODUCTION" | "IMPORT" | "SYSTEM_INFERENCE";
  sourceProductionId?: string | null;
  sourceProductionVersionId?: string | null;
  sourceArtifactIds?: string[];
  sourceReferences?: Array<{ kind: string; reference: string; hash?: string }>;
  customerConfirmed?: boolean;
  recordedAt: string;
  note?: string;
};

export type EffectiveStudioMemory = {
  itemId: string;
  scope: StudioMemoryScopeName;
  scopeRefId: string;
  key: string;
  category: string;
  versionId: string;
  versionNumber: number;
  effectiveState: "ACTIVE" | "INACTIVE" | "DELETED";
  content: Record<string, unknown>;
  contentHash: string;
  provenance: StudioMemoryProvenance | Record<string, unknown>;
  effectiveFrom: string;
  effectiveUntil: string | null;
  effectiveFromEpisodeOrdinal: number | null;
  effectiveUntilEpisodeOrdinal: number | null;
};

export type StudioProductionMemoryPacket = {
  schema: "StudioProductionMemoryPacketV1";
  productionId: string;
  projectVersion: number;
  ownerUserId: string;
  episodeOrdinal: number | null;
  selected: {
    brandId: string | null;
    seriesId: string | null;
    castMemberIds: string[];
  };
  accountMemory: EffectiveStudioMemory[];
  brandAuthority: {
    brandId: string | null;
    memories: EffectiveStudioMemory[];
    enforcement: "BINDING_UNLESS_EXPLICIT_PRODUCTION_EXCEPTION";
  };
  castAuthority: Array<{
    castMemberId: string;
    identityKey: string;
    name: string;
    memories: EffectiveStudioMemory[];
  }>;
  seriesMemory: {
    seriesId: string | null;
    memories: EffectiveStudioMemory[];
    previousEpisodeSignatures: SeriesPlanSignature[];
    antiRepetitionWindow: number;
  };
  productionMemory: EffectiveStudioMemory[];
  precedence: ["ACCOUNT", "BRAND", "SERIES", "CAST", "PRODUCTION"];
  laws: {
    completedProductionsNeverRetroactivelyChange: true;
    memorySnapshotIsImmutableProductionInput: true;
    seriesIsNotProductionFamily: true;
    castLivesUnderAssetsAndCreativeMemory: true;
  };
};

export type SeriesPlanSignature = {
  productionId?: string;
  episodeOrdinal?: number;
  environments?: string[];
  silhouettes?: string[];
  transitions?: string[];
  cameras?: string[];
  actorPositions?: string[];
  headlineStructures?: string[];
  cardGrid?: boolean;
  floatingObjects?: boolean;
  visualMetaphors?: string[];
  motifs?: string[];
};
