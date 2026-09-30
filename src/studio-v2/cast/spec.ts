// Cast spec model + plate-path helpers.
// Plates are 720x1080 alpha renders baked from the presenters_v1 scenes
// (scripts/castbake.py), composited in the browser in this draw order:
//   body -> lips -> shoes -> bottom -> outfit/top -> neck -> watch -> hair
// The hair plate carries its matched earring (female) baked in.

export type CastCharacter = "female" | "male";
export type FaceId = 0 | 1 | 2;

export interface CastSpec {
  character: CastCharacter;
  face: FaceId;
  skin: string;                                     // preset key
  hair: { style: string; color: string } | null;    // color: preset key or #hex
  lip: string | null;                               // female only
  neck: string | null;                              // female only
  outfit: { kind: string; color?: string | null; pieces?: Record<string, string> } | null;
  watch: string | null;                             // male only
  voiceId: string | null;
}

export interface CastMember {
  id: string;
  name: string;
  brandId: string | null;
  spec: CastSpec | null;
  createdAt: string;
  updatedAt: string;
}

export const SKINS = [
  { key: "fair", label: "Fair", hex: "#F7E1D3" },
  { key: "light", label: "Light", hex: "#F1D7C8" },
  { key: "medium", label: "Medium", hex: "#E0B48F" },
  { key: "tan", label: "Tan", hex: "#C99A6E" },
  { key: "brown", label: "Brown", hex: "#9E6B4A" },
  { key: "deep", label: "Deep", hex: "#6A4431" },
] as const;

export const FACES = [
  { id: 0, label: "Natural" },
  { id: 1, label: "Defined" },
  { id: 2, label: "Soft" },
] as const;

export const FEM_HAIRSTYLES = [
  { key: "long", label: "Long waves", note: "gold hoop" },
  { key: "afro", label: "Afro", note: "gold stud" },
  { key: "bun", label: "Bun", note: "statement hoops" },
  { key: "braid", label: "Braid", note: "teardrop" },
  { key: "swept", label: "Side-swept", note: "pearl stud" },
] as const;

export const MALE_HAIRSTYLES = [
  { key: "quiff", label: "Quiff" },
  { key: "afro", label: "Afro" },
] as const;

export const HAIR_COLORS = [
  { key: "auburn", label: "Auburn", hex: "#9A4A2E" },
  { key: "raven", label: "Raven", hex: "#1C1714" },
  { key: "brownd", label: "Dark brown", hex: "#3B2418" },
  { key: "blonde", label: "Blonde", hex: "#D8B77A" },
  { key: "silver", label: "Silver", hex: "#B9B8B5" },
] as const;

export const LIPS = [
  { key: "rose", label: "Soft rose" },
  { key: "crimson", label: "Crimson" },
  { key: "plum", label: "Plum" },
  { key: "coral", label: "Coral" },
] as const;

export const NECKS = [
  { key: "none", label: "None" },
  { key: "fine", label: "Fine chain" },
  { key: "pendant", label: "Pendant" },
  { key: "pearls", label: "Pearls" },
  { key: "choker", label: "Choker" },
  { key: "scarf", label: "Scarf" },
] as const;

export const FEM_OUTFITS = [
  { key: "sheath", label: "Navy sheath" },
  { key: "dress01", label: "Teal dress" },
  { key: "suit", label: "Elegant suit" },
] as const;

export const MALE_PIECES = [
  { key: "top", label: "Shirt" },
  { key: "bottom", label: "Trousers" },
  { key: "shoes", label: "Shoes" },
] as const;

export const WATCHES = [
  { key: "none", label: "None" },
  { key: "dress", label: "Dress" },
  { key: "analog", label: "Analog" },
  { key: "chrono", label: "Chrono" },
  { key: "smart", label: "Smart" },
  { key: "digital", label: "Digital" },
] as const;

export const VOICES = [
  { id: "emma", label: "Emma", tag: "US" },
  { id: "ava", label: "Ava", tag: "US" },
  { id: "andrew", label: "Andrew", tag: "US" },
  { id: "brian", label: "Brian", tag: "US" },
  { id: "sonia", label: "Sonia", tag: "UK" },
  { id: "natasha", label: "Natasha", tag: "AU" },
] as const;

export const DEFAULT_SPEC: Record<CastCharacter, CastSpec> = {
  female: { character: "female", face: 0, skin: "light", hair: { style: "long", color: "auburn" }, lip: "rose", neck: "fine", outfit: { kind: "sheath", color: null }, watch: null, voiceId: null },
  male: { character: "male", face: 0, skin: "tan", hair: { style: "quiff", color: "brownd" }, lip: null, neck: null, outfit: { kind: "casual", pieces: { top: "#A9C4DE", bottom: "#B59A6E", shoes: "#4A2E1E" } }, watch: "dress", voiceId: null },
};

const P = "/cast";
const prefix = (c: CastCharacter) => (c === "female" ? "fem" : "male");
const isHex = (v: string | null | undefined) => !!v && v.startsWith("#");
const presetKeys = (set: readonly { key: string }[]) => new Set(set.map((s) => s.key));

const HC_KEYS = presetKeys(HAIR_COLORS);
const SKIN_KEYS = presetKeys(SKINS);
const LIP_KEYS = presetKeys(LIPS);

export interface CastLayer {
  src: string;          // plate png
  tint?: string;        // multiply hex (uses the matching *_tint plate)
}

export function specLayers(spec: CastSpec): CastLayer[] {
  const p = prefix(spec.character);
  const layers: CastLayer[] = [];

  // body (baked per face x skin preset)
  const skin = SKIN_KEYS.has(spec.skin) ? spec.skin : "light";
  layers.push({ src: `${P}/${p}_body_f${spec.face}_${skin}.png` });

  // lipstick: PIL-extracted alpha patch, female only; drawn for every colour
  // (the scene's default lip is none of these)
  if (spec.character === "female" && spec.lip && LIP_KEYS.has(spec.lip)) {
    layers.push({ src: `${P}/fem_lip_f${spec.face}_${spec.lip}.png` });
  }

  if (spec.character === "male") {
    // shoes -> trousers -> shirt so cuffs sit right
    const pieces = spec.outfit?.pieces ?? {};
    for (const part of ["shoes", "bottom", "top"] as const) {
      const hex = pieces[part];
      layers.push(isHex(hex) ? { src: `${P}/male_${part}_tint.png`, tint: hex! } : { src: `${P}/male_${part}.png` });
    }
  } else if (spec.outfit?.kind) {
    layers.push(isHex(spec.outfit.color)
      ? { src: `${P}/fem_outfit_${spec.outfit.kind}_tint.png`, tint: spec.outfit.color! }
      : { src: `${P}/fem_outfit_${spec.outfit.kind}.png` });
  }

  if (spec.character === "female" && spec.neck && spec.neck !== "none") {
    layers.push({ src: `${P}/fem_neck_${spec.neck}.png` });
  }
  if (spec.character === "male" && spec.watch && spec.watch !== "none") {
    layers.push({ src: `${P}/male_watch_${spec.watch}.png` });
  }

  if (spec.hair) {
    layers.push(HC_KEYS.has(spec.hair.color)
      ? { src: `${P}/${p}_hair_${spec.hair.style}_${spec.hair.color}.png` }
      : { src: `${P}/${p}_hair_${spec.hair.style}_tint.png`, tint: spec.hair.color });
    // her earring pairs with the hairstyle - separate plate so custom tinting
    // never recolours the gold
    if (spec.character === "female") {
      layers.push({ src: `${P}/fem_earring_${spec.hair.style}.png` });
    }
  }
  return layers;
}
