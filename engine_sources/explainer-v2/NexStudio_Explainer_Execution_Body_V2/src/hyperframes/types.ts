export type AspectRatio = "16:9" | "9:16" | "1:1";
export type RenderQuality = "draft" | "standard" | "high";

export type CompositionBeatOverride = {
  /**
   * Complete, validated HyperFrames sub-composition document authored by the
   * composition agent. Legacy markup remains supported for deterministic
   * migrations, but new model output always supplies html.
   */
  html?: string;
  markup?: string;
  css: string;
  js: string;
  /**
   * Optional controlled bundle namespace for reusable library assets. Model
   * authored bespoke scenes retain the legacy assets/kimi/<beat> namespace.
   */
  assetNamespace?: `assets/${string}`;
  libraryScene?: {
    family: string;
    sceneId: string;
    version: string;
  };
  /** Frozen canonical-library media required by this scene. */
  files?: Record<string, Uint8Array>;
};

export type CompositionInput = {
  productionId: string;
  title: string;
  message: string;
  callToAction: string;
  accent?: string;
  aspectRatio: AspectRatio;
  /** Product Launch Standard must fail on an unresolved selected asset rather than substitute another source. */
  strictAssetBinding?: boolean;
  durationSeconds?: number;
  messageClaimIds?: string[];
  callToActionClaimIds?: string[];
  storyboard?: import("@/domain/studio-pipeline").FirstSliceStoryboard;
  storyboardValidation?: { minBeats?: number; maxBeats?: number };
  media?: {
    narration?: { bytes: Uint8Array; mimeType: string; durationSec: number };
    narrationClips?: Array<{ id: string; sceneId: string; bytes: Uint8Array; mimeType: string; durationSec: number; startSec: number }>;
    music?: { bytes: Uint8Array; mimeType: string; durationSec: number; volume: number; duckUnderNarration?: boolean };
    soundEffect?: { bytes: Uint8Array; mimeType: string; durationSec: number; volume: number; cueTimesSec: number[] };
    captions?: { text: string; startSec: number; endSec: number }[];
  };
  assets?: {
    sourceId: string;
    name: string;
    mimeType: string;
    contentHash: string;
    bytes: Uint8Array;
  }[];
  beatOverrides?: Record<string, CompositionBeatOverride>;
};

export type CompositionBundle = {
  entry: "index.html";
  hyperframesVersion: string;
  width: number;
  height: number;
  durationSeconds: number;
  files: Record<string, string | Uint8Array>;
  manifest: {
    productionId: string;
    templateVersion?: string;
    compositionHash: string;
    sourceHash: string;
    createdAt: string;
    assets: { path: string; sha256: string }[];
    beatCount: number;
    beatTimings: { beatId: string; startSec: number; endSec: number }[];
    beatFiles?: Record<string, string>;
    audioTracks: {
      id: string;
      path: string;
      sha256: string;
      durationSec: number;
      startSec?: number;
      volume?: number;
      cueTimesSec?: number[];
      duckUnderNarration?: boolean;
    }[];
    sceneLibrary?: {
      family: string;
      sceneId: string;
      version: string;
      beatId: string;
    }[];
  };
};

export type CloudRenderRequest = {
  assetId: string;
  composition?: string;
  fps?: number;
  quality?: RenderQuality;
  format?: "mp4" | "webm" | "mov";
  resolution?: "1080p" | "4k";
  aspectRatio?: AspectRatio;
  variables?: Record<string, unknown>;
  callbackUrl?: string;
  callbackId?: string;
  title?: string;
  idempotencyKey: string;
};

export type CloudRenderResult = {
  renderId: string;
  status: "queued" | "rendering" | "completed" | "failed";
  assetId?: string;
  videoUrl?: string;
  thumbnailUrl?: string;
  error?: string;
  raw: Record<string, unknown>;
};
