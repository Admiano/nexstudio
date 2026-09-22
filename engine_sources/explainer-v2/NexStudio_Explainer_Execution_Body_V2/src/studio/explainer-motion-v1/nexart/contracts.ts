import type { ReferenceLanguageProfile } from "../types";

export type ReferenceFrameEvidence = {
  sourceId: string;
  mimeType: "image/jpeg" | "image/png";
  dataUrl: string;
  sampleTimeSec: number;
  sha256: string;
};

export type ReferenceLanguageEvidence = {
  profile: ReferenceLanguageProfile;
  frames: ReferenceFrameEvidence[];
};

export type ReferenceSourceAsset = {
  assetId: string;
  mimeType: string;
  bytes: Uint8Array;
  name?: string;
};

export const AUTHORED_SCENE_MODES = new Set(["AUTHORED_SCENE", "WHITEBOARD_SCENE", "HYBRID_ILLUSTRATION"]);
