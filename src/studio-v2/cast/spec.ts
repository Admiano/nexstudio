// Cast spec model + plate-path helpers.
//
// Colour is independent from clothing style. The MakeHuman presenter source
// supports arbitrary hex garment colours; the web runtime uses a curated set
// of baked colour plates so previews remain pixel-faithful to the Blender
// authoring pipeline rather than browser-tinted approximations.

export type CastCharacter = "female" | "male";
export type FaceId = 0 | 1 | 2;

export interface CastOutfitSpec {
  kind: string;
  // Female: dress colour. Male: top colour; trousers + shoes remain authored
  // for the selected outfit. Optional for compatibility with V1 saved specs.
  color?: string | null;
  pieces?: Record<string, string>;
}

export interface CastSpec {
  character: CastCharacter;
  face: FaceId;
  skin: string;
  hair: { style: string; color: string } | null;
  lip: string | null;
  neck: string | null;
  outfit: CastOutfitSpec | null;
  watch: string | null;
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
  { key: "long", label: "Long waves", note: "slim gold hoop" },
  { key: "bob", label: "Blunt bob", note: "gold bar drop" },
  { key: "bangs", label: "Bangs", note: "pearl stud" },
  { key: "bun", label: "High bun", note: "statement hoops" },
  { key: "braid", label: "French braid", note: "teardrop" },
] as const;

export const MALE_HAIRSTYLES = [
  { key: "afro", label: "Short afro" },
  { key: "crop", label: "Short crop" },
  { key: "quiff", label: "Textured quiff" },
  { key: "braids", label: "Braids" },
  { key: "swept", label: "Side-swept" },
] as const;

export const FEM_HAIR_COLORS = [
  { key: "auburn", label: "Auburn", hex: "#9A4A2E" },
  { key: "black", label: "Black", hex: "#1C1714" },
  { key: "brown", label: "Dark brown", hex: "#3B2418" },
  { key: "blonde", label: "Blonde", hex: "#D8B77A" },
  { key: "silver", label: "Silver", hex: "#B9B8B5" },
] as const;

export const MALE_HAIR_COLORS = [
  { key: "black", label: "Black", hex: "#1C1714" },
  { key: "blonde", label: "Blonde", hex: "#C9A366" },
  { key: "brown", label: "Brown", hex: "#5A3A24" },
  { key: "dye", label: "Black & burgundy", hex: "#141212" },
  { key: "grey", label: "Grey", hex: "#8F9096" },
] as const;

export const LIPS = [
  { key: "rose", label: "Soft rose" },
  { key: "red", label: "Classic red" },
  { key: "berry", label: "Berry" },
  { key: "coral", label: "Coral" },
  { key: "nude", label: "Nude" },
] as const;

export const NECKS = [
  { key: "none", label: "None" },
  { key: "fine", label: "Fine chain" },
  { key: "pendant", label: "Pendant" },
  { key: "pearls", label: "Pearls" },
  { key: "choker", label: "Choker" },
  { key: "scarf", label: "Neckerchief" },
] as const;

export const FEM_DRESS_COLORS = [
  { key: "navy", label: "Navy", hex: "#2B3A5C" },
  { key: "burgundy", label: "Burgundy", hex: "#6B2233" },
  { key: "sage", label: "Sage", hex: "#7C8C6A" },
  { key: "emerald", label: "Emerald", hex: "#1F5C4A" },
  { key: "rose", label: "Dusty rose", hex: "#B87A7F" },
] as const;

export const FEM_DRESSES = [
  { key: "sheath", label: "Tailored sheath", note: "3/4 sleeve" },
  { key: "maxi", label: "Long-sleeve maxi", note: "full length" },
  { key: "column", label: "Column midi", note: "sleeveless" },
  { key: "cocktail", label: "Cocktail sheath", note: "knee length" },
  { key: "qipao", label: "Qipao midi", note: "mandarin collar" },
] as const;

export const MALE_TOP_COLORS = [
  { key: "navy", label: "Navy", hex: "#2E3A55" },
  { key: "ivory", label: "Ivory", hex: "#EDEBE6" },
  { key: "blue", label: "Light blue", hex: "#A9C4DE" },
  { key: "burgundy", label: "Burgundy", hex: "#6B2E2E" },
  { key: "cream", label: "Cream", hex: "#D8CFBE" },
] as const;

export const MALE_OUTFITS = [
  { key: "o1", label: "Polo", note: "charcoal trousers · brown Oxfords" },
  { key: "o2", label: "Tee", note: "straight jeans · white sneakers" },
  { key: "o3", label: "Button-down", note: "tan trousers · monk straps" },
  { key: "o4", label: "Knit", note: "classic jeans · sneakers" },
  { key: "o5", label: "Fisherman", note: "wool trousers · Oxfords" },
] as const;

export const WATCHES = [
  { key: "none", label: "None" },
  { key: "analog", label: "Analog" },
  { key: "digital", label: "Digital" },
  { key: "smart", label: "Smart" },
  { key: "chrono", label: "Chronograph" },
  { key: "dress", label: "Dress" },
] as const;

export const VOICES = [
  { id: "emma", label: "Emma", tag: "US" },
  { id: "ava", label: "Ava", tag: "US" },
  { id: "andrew", label: "Andrew", tag: "US" },
  { id: "brian", label: "Brian", tag: "US" },
  { id: "sonia", label: "Sonia", tag: "UK" },
  { id: "natasha", label: "Natasha", tag: "AU" },
] as const;

export const FEM_DRESS_DEFAULT_COLOR: Record<string, string> = {
  sheath: "navy",
  maxi: "burgundy",
  column: "sage",
  cocktail: "emerald",
  qipao: "rose",
};

export const MALE_TOP_DEFAULT_COLOR: Record<string, string> = {
  o1: "navy",
  o2: "ivory",
  o3: "blue",
  o4: "burgundy",
  o5: "cream",
};

export const DEFAULT_SPEC: Record<CastCharacter, CastSpec> = {
  female: {
    character: "female", face: 0, skin: "light",
    hair: { style: "long", color: "auburn" }, lip: "rose", neck: "fine",
    outfit: { kind: "sheath", color: "navy" }, watch: null, voiceId: null,
  },
  male: {
    character: "male", face: 0, skin: "tan",
    hair: { style: "quiff", color: "brown" }, lip: null, neck: null,
    outfit: { kind: "o3", color: "blue" }, watch: "dress", voiceId: null,
  },
};

const presetKeys = (set: readonly { key: string }[]) => new Set(set.map((s) => s.key));
const SKIN_KEYS = presetKeys(SKINS);
const LIP_KEYS = presetKeys(LIPS);
const FEM_HC_KEYS = presetKeys(FEM_HAIR_COLORS);
const MALE_HC_KEYS = presetKeys(MALE_HAIR_COLORS);
const FEM_STYLE_KEYS = presetKeys(FEM_HAIRSTYLES);
const MALE_STYLE_KEYS = presetKeys(MALE_HAIRSTYLES);
const FEM_DRESS_KEYS = presetKeys(FEM_DRESSES);
const MALE_OUTFIT_KEYS = presetKeys(MALE_OUTFITS);
const FEM_DRESS_COLOR_KEYS = presetKeys(FEM_DRESS_COLORS);
const MALE_TOP_COLOR_KEYS = presetKeys(MALE_TOP_COLORS);
const NECK_KEYS = presetKeys(NECKS);
const WATCH_KEYS = presetKeys(WATCHES);

export function normalizeCastSpec(input: CastSpec | null | undefined, hint?: CastCharacter): CastSpec {
  const character: CastCharacter = input?.character === "male" ? "male" : input?.character === "female" ? "female" : (hint ?? "female");
  const d = DEFAULT_SPEC[character];
  const face: FaceId = input?.face === 1 || input?.face === 2 ? input.face : 0;
  const skin = input?.skin && SKIN_KEYS.has(input.skin) ? input.skin : d.skin;

  const styles = character === "female" ? FEM_STYLE_KEYS : MALE_STYLE_KEYS;
  const colors = character === "female" ? FEM_HC_KEYS : MALE_HC_KEYS;
  const hairStyle = input?.hair?.style && styles.has(input.hair.style) ? input.hair.style : d.hair!.style;
  const hairColor = input?.hair?.color && colors.has(input.hair.color) ? input.hair.color : d.hair!.color;

  const kindSet = character === "female" ? FEM_DRESS_KEYS : MALE_OUTFIT_KEYS;
  const kind = input?.outfit?.kind && kindSet.has(input.outfit.kind) ? input.outfit.kind : d.outfit!.kind;
  const defaultColour = character === "female" ? FEM_DRESS_DEFAULT_COLOR[kind] : MALE_TOP_DEFAULT_COLOR[kind];
  const colourSet = character === "female" ? FEM_DRESS_COLOR_KEYS : MALE_TOP_COLOR_KEYS;
  const outfitColor = input?.outfit?.color && colourSet.has(input.outfit.color)
    ? input.outfit.color
    : defaultColour;

  return {
    character,
    face,
    skin,
    hair: { style: hairStyle, color: hairColor },
    lip: character === "female" && input?.lip && LIP_KEYS.has(input.lip) ? input.lip : (character === "female" ? d.lip : null),
    neck: character === "female"
      ? (input?.neck === null ? null : input?.neck && NECK_KEYS.has(input.neck) && input.neck !== "none" ? input.neck : d.neck)
      : null,
    outfit: { kind, color: outfitColor, pieces: input?.outfit?.pieces },
    watch: character === "male"
      ? (input?.watch === null ? null : input?.watch && WATCH_KEYS.has(input.watch) && input.watch !== "none" ? input.watch : d.watch)
      : null,
    voiceId: input?.voiceId ?? d.voiceId,
  };
}

const PLATE_V = "v9";
const P = "/cast";
const plate = (name: string) => `${P}/${name}.png?v=${PLATE_V}`;
const prefix = (c: CastCharacter) => (c === "female" ? "fem" : "male");

export interface CastLayer {
  src: string;
  fallbackSrc?: string;
}

export function specLayers(raw: CastSpec): CastLayer[] {
  const spec = normalizeCastSpec(raw, raw.character);
  const p = prefix(spec.character);
  const layers: CastLayer[] = [];
  const skin = spec.skin;
  layers.push({ src: plate(`${p}_body_f${spec.face}_${skin}`) });

  if (spec.character === "female" && spec.lip && spec.lip !== "rose") {
    layers.push({ src: plate(`fem_lip_f${spec.face}_${spec.lip}`) });
  }

  const maleLook = spec.character === "male" ? spec.outfit!.kind : null;
  if (maleLook && spec.watch && spec.watch !== "none") {
    layers.push({ src: plate(`male_watch_${maleLook}_${spec.watch}`) });
  }

  if (spec.character === "female") {
    const kind = spec.outfit!.kind;
    const color = spec.outfit!.color!;
    layers.push({
      src: plate(`fem_outfit_${kind}_${color}`),
      fallbackSrc: plate(`fem_outfit_${kind}`),
    });
  } else {
    const color = spec.outfit!.color!;
    layers.push({
      src: plate(`male_outfit_${maleLook}_${color}`),
      fallbackSrc: plate(`male_outfit_${maleLook}`),
    });
  }

  if (spec.character === "female" && spec.neck) {
    layers.push({ src: plate(`fem_neck_${spec.neck}`) });
  }

  const style = spec.hair!.style;
  if (spec.character === "female") {
    layers.push({ src: plate(`fem_earring_${style}`) });
  }
  layers.push({ src: plate(`${p}_hair_${style}_${spec.hair!.color}`) });
  layers.push({ src: plate(`${p}_hands_${spec.outfit!.kind}_${skin}`) });
  return layers;
}
