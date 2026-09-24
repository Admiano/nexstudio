import type {
  CapabilityContract,
  FamilyId,
  InputRequirement,
  ProductionFamily,
  ProductionRegistry,
  ProductionVideoType,
} from "./types";
import { getSubtypeCertificationGate } from "../certification/certification-gate";

const topic: InputRequirement = {
  id: "topic",
  label: "What should the video explain or show?",
  kind: "text",
};

const audience: InputRequirement = {
  id: "audience",
  label: "Who is it for?",
  kind: "text",
};

const references: InputRequirement = {
  id: "references",
  label: "References or source material",
  kind: "file",
  description: "Optional files, links, scripts, screenshots or source material.",
};

const tone: InputRequirement = {
  id: "tone",
  label: "Tone or feel",
  kind: "text",
};

const data: InputRequirement = {
  id: "data",
  label: "Data or facts to use",
  kind: "file",
};

function contract(family: FamilyId, videoTypeId: string, capabilities: readonly string[]): CapabilityContract {
  const certification = getSubtypeCertificationGate(family, videoTypeId);
  return {
    contractId: `studio.v1.${family}.${videoTypeId}`,
    requiredCapabilities: capabilities,
    verification: certification.verification,
  };
}

function type(
  family: FamilyId,
  id: string,
  name: string,
  shortDescription: string,
  capabilities: readonly string[],
  requiredInputs: readonly InputRequirement[] = [topic],
  optionalInputs: readonly InputRequirement[] = [audience, tone, references],
): ProductionVideoType {
  const certification = getSubtypeCertificationGate(family, id);
  return {
    id,
    family,
    name,
    shortDescription,
    previewVideo: certification.previewVideo,
    posterFrame: certification.posterFrame,
    supportedDurations: [15, 30, 45, 60],
    supportedAspectRatios: ["16:9", "9:16", "1:1"],
    requiredInputs,
    optionalInputs,
    capabilityContract: contract(family, id, capabilities),
    // Certification evidence owns the publishing switch. A gallery edit alone cannot enable a subtype.
    publicEnabled: certification.publicEnabled,
  };
}

export const PRODUCTION_FAMILIES: readonly ProductionFamily[] = [
  {
    id: "explainer",
    name: "Explainer",
    shortDescription: "Make a product, process, system or idea easy to understand.",
    publicEnabled: true,
    previewVideo: null,
    posterFrame: null,
  },
  {
    id: "whiteboard",
    name: "Whiteboard",
    shortDescription: "Build the explanation as the viewer watches it unfold.",
    publicEnabled: true,
    previewVideo: null,
    posterFrame: null,
  },
] as const;

export const PRODUCTION_VIDEO_TYPES: readonly ProductionVideoType[] = [
  // WHITEBOARD — the two approved pipelines
  type("whiteboard", "kinetic-text", "Text-Driven Whiteboard", "Your script builds on the board line by line, with a highlight color and a light or dark board.", ["kinetic-typography", "narration", "progressive-reveal"]),
  type("whiteboard", "hand-drawn-board", "Hand-Drawn Whiteboard", "A hand draws boxes, characters and scenes on a giant board while the narration walks through.", ["whiteboard-drawing", "character-performance", "narration"]),

  // EXPLAINER — the six approved styles
  type("explainer", "tiles", "Tiles", "Colour icons in tiles — the default explainer collage look.", ["explanation", "styled-collage", "narrative-structure"]),
  type("explainer", "photo-story", "Photo Story", "Real photos in tiles — evidence-led, documentary feel.", ["explanation", "photo-collage", "narrative-structure"]),
  type("explainer", "sketch", "Sketch", "Black wireframe icons in tiles — clean, technical, brand-safe.", ["explanation", "wireframe-icons", "narrative-structure"]),
  type("explainer", "emoji", "Emoji", "Emoji tiles — playful, casual, social-native.", ["explanation", "emoji-tiles", "narrative-structure"]),
  type("explainer", "ink-paper", "Ink & Paper", "Ink illustrations on textured paper — editorial, crafted.", ["explanation", "ink-illustration", "narrative-structure"]),
  type("explainer", "poster", "Poster", "Bold poster compositions — loud, graphic, designed.", ["explanation", "poster-composition", "narrative-structure"]),
] as const;

export const PRODUCTION_REGISTRY: ProductionRegistry = {
  families: PRODUCTION_FAMILIES,
  videoTypes: PRODUCTION_VIDEO_TYPES,
};
