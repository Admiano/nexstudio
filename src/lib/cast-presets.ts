// Studio cast presets — 20 ready-made modular characters (10 female + 10 male)
// anyone can present with. A preset is adopted into the user's cast on first
// use, so it stays a real StudioCastMember row (P8 cast scope, memory, drafts
// all work unchanged). The shared `preset-*` identityKey means the same preset
// is the same performer for every user.
import type { CastSpec } from "@/studio-v2/cast/spec";

export interface CastPreset {
  id: string;              // stable preset id, e.g. "aria"
  name: string;
  gender: "female" | "male";
  tagline: string;
  identityKey: string;     // preset-<id>
  spec: CastSpec;
}

const F = (id: string, name: string, tagline: string, spec: Partial<CastSpec> & Pick<CastSpec, "skin" | "face" | "hair" | "lip" | "neck" | "outfit">): CastPreset => ({
  id, name, gender: "female", tagline, identityKey: `preset-${id}`,
  spec: { character: "female", watch: null, voiceId: null, ...spec } as CastSpec,
});

const M = (id: string, name: string, tagline: string, spec: Partial<CastSpec> & Pick<CastSpec, "skin" | "face" | "hair" | "outfit" | "watch">): CastPreset => ({
  id, name, gender: "male", tagline, identityKey: `preset-${id}`,
  spec: { character: "male", lip: null, neck: null, voiceId: null, ...spec } as CastSpec,
});

export const CAST_PRESETS: readonly CastPreset[] = [
  F("aria", "Aria", "Warm and polished — the approachable host.", {
    skin: "fair", face: 0, hair: { style: "long", color: "blonde" }, lip: "rose", neck: "fine",
    outfit: { kind: "sheath", color: "navy" },
  }),
  F("maya", "Maya", "Confident and editorial — strong presence.", {
    skin: "deep", face: 1, hair: { style: "bob", color: "black" }, lip: "berry", neck: "pearls",
    outfit: { kind: "maxi", color: "emerald" },
  }),
  F("zoe", "Zoe", "Bright and quick — friendly explainer energy.", {
    skin: "tan", face: 2, hair: { style: "bangs", color: "auburn" }, lip: "coral", neck: "scarf",
    outfit: { kind: "column", color: "sage" },
  }),
  F("ivy", "Ivy", "Calm authority — composed and precise.", {
    skin: "medium", face: 0, hair: { style: "bun", color: "brown" }, lip: "nude", neck: "pendant",
    outfit: { kind: "cocktail", color: "burgundy" },
  }),
  F("sana", "Sana", "Graceful and deliberate — a teacher's cadence.", {
    skin: "brown", face: 1, hair: { style: "braid", color: "black" }, lip: "red", neck: "choker",
    outfit: { kind: "qipao", color: "rose" },
  }),
  F("ruth", "Ruth", "Seasoned and steady — silver-haired authority.", {
    skin: "light", face: 2, hair: { style: "long", color: "silver" }, lip: "rose", neck: "pearls",
    outfit: { kind: "maxi", color: "navy" },
  }),
  F("nia", "Nia", "Bold and creative — striking contrast.", {
    skin: "deep", face: 0, hair: { style: "bob", color: "blonde" }, lip: "coral", neck: "fine",
    outfit: { kind: "cocktail", color: "emerald" },
  }),
  F("elena", "Elena", "Direct and capable — business-ready.", {
    skin: "tan", face: 1, hair: { style: "bangs", color: "brown" }, lip: "berry", neck: "pendant",
    outfit: { kind: "sheath", color: "burgundy" },
  }),
  F("amara", "Amara", "Gentle and reassuring — easy to trust.", {
    skin: "brown", face: 2, hair: { style: "braid", color: "auburn" }, lip: "nude", neck: "pearls",
    outfit: { kind: "column", color: "rose" },
  }),
  F("priya", "Priya", "Sharp and articulate — crisp delivery.", {
    skin: "medium", face: 0, hair: { style: "bun", color: "black" }, lip: "red", neck: "scarf",
    outfit: { kind: "qipao", color: "sage" },
  }),
  M("marcus", "Marcus", "Steady and warm — the reliable host.", {
    skin: "tan", face: 0, hair: { style: "quiff", color: "brown" }, watch: null,
    outfit: { kind: "o3", color: "blue" },
  }),
  M("david", "David", "Classic and assured — boardroom polish.", {
    skin: "light", face: 1, hair: { style: "crop", color: "black" }, watch: "analog",
    outfit: { kind: "o1", color: "navy" },
  }),
  M("kwame", "Kwame", "Easy and open — relaxed storyteller.", {
    skin: "deep", face: 2, hair: { style: "braids", color: "black" }, watch: "digital",
    outfit: { kind: "o2", color: "ivory" },
  }),
  M("tom", "Tom", "Boyish and direct — approachable energy.", {
    skin: "fair", face: 0, hair: { style: "swept", color: "blonde" }, watch: null,
    outfit: { kind: "o4", color: "burgundy" },
  }),
  M("andre", "Andre", "Commanding and calm — strong silhouette.", {
    skin: "brown", face: 1, hair: { style: "bald", color: "black" }, watch: null,
    outfit: { kind: "o5", color: "cream" },
  }),
  M("luis", "Luis", "Casual and genuine — conversational pace.", {
    skin: "medium", face: 2, hair: { style: "crop", color: "brown" }, watch: "smart",
    outfit: { kind: "o2", color: "blue" },
  }),
  M("vikram", "Vikram", "Focused and articulate — crisp delivery.", {
    skin: "tan", face: 0, hair: { style: "quiff", color: "black" }, watch: null,
    outfit: { kind: "o3", color: "ivory" },
  }),
  M("cole", "Cole", "Silver and seasoned — elder authority.", {
    skin: "light", face: 1, hair: { style: "swept", color: "grey" }, watch: "chrono",
    outfit: { kind: "o1", color: "cream" },
  }),
  M("jin", "Jin", "Creative and modern — standout style.", {
    skin: "fair", face: 2, hair: { style: "crop", color: "dye" }, watch: null,
    outfit: { kind: "o4", color: "navy" },
  }),
  M("osei", "Osei", "Grounded and dignified — deep presence.", {
    skin: "deep", face: 0, hair: { style: "braids", color: "dye" }, watch: null,
    outfit: { kind: "o5", color: "burgundy" },
  }),
];

export function castPreset(id: string): CastPreset | undefined {
  return CAST_PRESETS.find((p) => p.id === id || p.identityKey === id);
}
