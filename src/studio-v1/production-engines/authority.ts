import type { StudioProductionFamily } from "@/generated/prisma/client";

export type StudioEngineAuthorityStatus =
  | "ENGINEERING_COMPLETE_CREATIVE_REVIEW_PENDING"
  | "TECHNICAL_PASS_CREATIVE_REVIEW_PENDING"
  | "MACHINE_CERTIFIED_NO_SHIP"
  | "INTERNAL_PERFORMANCE_MASTER"
  | "PUBLIC_PRODUCTION_APPROVED";

export type StudioFamilyEngineAuthority = {
  family: StudioProductionFamily;
  authorityId: string;
  sourceLabel: string;
  sourceArchiveSha256: string;
  capabilityManifestSha256?: string;
  technicalStatus: StudioEngineAuthorityStatus;
  executionBody: string;
  truthBoundary: string;
  eligibleForInternalReviewEvidence: boolean;
  eligibleForPublicProduction: boolean;
  dispatchAdapterStatus: "ADAPTER_PENDING" | "READY";
};

/**
 * Current execution-body truth for Standalone Studio V1.
 *
 * Only the two production-approved families carry authorities: Explainer and
 * Whiteboard. Families without an authority entry are retired offerings — the
 * lookup helpers fail closed on them.
 */
const AUTHORITIES: Readonly<Partial<Record<StudioProductionFamily, StudioFamilyEngineAuthority>>> = {
  EXPLAINER: {
    family: "EXPLAINER",
    authorityId: "EXPLAINER_EXECUTION_BODY_V2_P8_UNIFIED",
    sourceLabel: "NexStudio_Explainer_Execution_Body_V2.zip",
    sourceArchiveSha256: "b2782b1557515d43db78a2c1507aeebb1cae99458104c450ed63ef752a675f1b",
    capabilityManifestSha256: "dbfd89654e869ad9a33917e668acca367bed34be8057c5526b710c179ebaf404",
    technicalStatus: "PUBLIC_PRODUCTION_APPROVED",
    executionBody: "engine_sources/editorial-motion-v2 render pipeline (tools/make_reel.py): script or uploaded voice -> Microsoft neural voice -> style treatment -> per-aspect web mp4s",
    truthBoundary: "The explainer route renders through the checked-in editorial-motion-v2 pipeline across its six approved styles and emits 16:9, 9:16 and 1:1 outputs per job.",
    eligibleForInternalReviewEvidence: true,
    eligibleForPublicProduction: true,
    dispatchAdapterStatus: "READY",
  },
  WHITEBOARD: {
    family: "WHITEBOARD",
    authorityId: "WHITEBOARD_V3_RUNTIME_APPROVED",
    sourceLabel: "engine_sources/whiteboard-v3-runtime",
    sourceArchiveSha256: "",
    technicalStatus: "PUBLIC_PRODUCTION_APPROVED",
    executionBody: "Whiteboard v3 runtime: pipeline_kinetic_timed.py (text-driven, light/dark theme, accent highlight) and pipeline_v3_narration_timed.py (hand-drawn giant-board journey), Microsoft neural voice via edge-tts",
    truthBoundary: "The two approved whiteboard productions are the kinetic text-driven render and the hand-drawn board render, both voiced by the Microsoft neural voices. Older whiteboard execution bodies remain installed for internal lineage only.",
    eligibleForInternalReviewEvidence: true,
    eligibleForPublicProduction: true,
    dispatchAdapterStatus: "READY",
  },
};

export function familyEngineAuthority(family: StudioProductionFamily): StudioFamilyEngineAuthority {
  const authority = AUTHORITIES[family];
  if (!authority) throw new Error(`FAMILY_OFFERING_RETIRED:${family}`);
  return authority;
}

export function assertInternalReviewEvidenceEligible(family: StudioProductionFamily) {
  const authority = familyEngineAuthority(family);
  if (!authority.eligibleForInternalReviewEvidence) throw new Error(`FAMILY_INTERNAL_REVIEW_EVIDENCE_BLOCKED:${family}`);
  return authority;
}

export function assertPublicProductionEligible(family: StudioProductionFamily) {
  const authority = familyEngineAuthority(family);
  if (!authority.eligibleForPublicProduction || authority.dispatchAdapterStatus !== "READY") {
    throw new Error(`FAMILY_PUBLIC_PRODUCTION_NOT_CERTIFIED:${family}`);
  }
  return authority;
}
