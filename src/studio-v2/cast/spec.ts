// Cast spec model + plate-path helpers.
// Plates are 720x1080 alpha renders baked from the presenters_v1 scenes by
// scripts/castbake3.py through the canonical preset pipeline (presets.sh):
// every look is built exactly as authored, then each component renders with
// all other objects on holdout - so a plate carries precisely the pixels
// that component covers in the real frame, down to cuff and hair occlusion.
//
// Composited in the browser in this draw order:
//   body -> lip -> watch -> outfit -> neck -> earring -> hair -> hands
// The watch sits under the outfit so long sleeves cover the strap the way the
// authored looks do; the earring sits under hair for the same reason; hands
// draw last because the talking-frame pose rests them in front of everything.

export type CastCharacter = "female" | "male";
export type FaceId = 0 | 1 | 2;

export interface CastSpec {
  character: CastCharacter;
  face: FaceId;
  skin: string;                                  // preset key
  hair: { style: string; color: string } | null; // style + preset colour key
  lip: string | null;                            // female only
  neck: string | null;                           // female only, "none" ok
  outfit: { kind: string } | null;               // female: dress key; male: look key
  watch: string | null;                          // male only, "none" ok
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

// Every hairstyle carries its own earring (authored pairing, no picker).
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

// Fixed colourways - each dress ships exactly the colour it was authored in.
export const FEM_DRESSES = [
  { key: "sheath", label: "Navy sheath", hex: "#2B3A5C", note: "tailored 3/4 sleeve" },
  { key: "maxi", label: "Burgundy maxi", hex: "#6B2233", note: "long sleeve" },
  { key: "column", label: "Sage column", hex: "#7C8C6A", note: "sleeveless midi" },
  { key: "cocktail", label: "Emerald sheath", hex: "#1F5C4A", note: "knee length" },
  { key: "qipao", label: "Dusty rose qipao", hex: "#B87A7F", note: "mandarin collar" },
] as const;

// Fixed ensembles - top, trousers and shoes are one authored set.
export const MALE_OUTFITS = [
  { key: "o1", label: "Navy polo", note: "charcoal trousers · brown Oxfords" },
  { key: "o2", label: "White tee", note: "straight jeans · white sneakers" },
  { key: "o3", label: "Blue shirt", note: "tan trousers · monk straps" },
  { key: "o4", label: "Burgundy knit", note: "classic jeans · sneakers" },
  { key: "o5", label: "Cream fisherman", note: "wool trousers · Oxfords" },
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

export const DEFAULT_SPEC: Record<CastCharacter, CastSpec> = {
  female: { character: "female", face: 0, skin: "light", hair: { style: "long", color: "auburn" }, lip: "rose", neck: "fine", outfit: { kind: "sheath" }, watch: null, voiceId: null },
  male: { character: "male", face: 0, skin: "tan", hair: { style: "quiff", color: "brown" }, lip: null, neck: null, outfit: { kind: "o3" }, watch: "dress", voiceId: null },
};

// Bump when the plate set is re-baked so cached copies refresh.
const PLATE_V = "v8";
const P = "/cast";
const plate = (name: string) => `${P}/${name}.png?v=${PLATE_V}`;
const prefix = (c: CastCharacter) => (c === "female" ? "fem" : "male");
const presetKeys = (set: readonly { key: string }[]) => new Set(set.map((s) => s.key));

const SKIN_KEYS = presetKeys(SKINS);
const LIP_KEYS = presetKeys(LIPS);
const FEM_HC_KEYS = presetKeys(FEM_HAIR_COLORS);
const MALE_HC_KEYS = presetKeys(MALE_HAIR_COLORS);
const FEM_STYLE_KEYS = presetKeys(FEM_HAIRSTYLES);
const MALE_STYLE_KEYS = presetKeys(MALE_HAIRSTYLES);
const FEM_DRESS_KEYS = presetKeys(FEM_DRESSES);
const MALE_OUTFIT_KEYS = presetKeys(MALE_OUTFITS);

export interface CastLayer {
  src: string;
}

export function specLayers(spec: CastSpec): CastLayer[] {
  const p = prefix(spec.character);
  const layers: CastLayer[] = [];

  const skin = SKIN_KEYS.has(spec.skin) ? spec.skin : "light";
  layers.push({ src: plate(`${p}_body_f${spec.face}_${skin}`) });

  // the shipped default lip is soft rose - the body plate already carries it,
  // so only the four other authored shades need their patch layer
  if (spec.character === "female" && spec.lip && spec.lip !== "rose" && LIP_KEYS.has(spec.lip)) {
    layers.push({ src: plate(`fem_lip_f${spec.face}_${spec.lip}`) });
  }

  const maleLook = spec.character === "male"
    ? (MALE_OUTFIT_KEYS.has(spec.outfit?.kind ?? "") ? spec.outfit!.kind : "o3")
    : null;

  // watch before the outfit: sleeves cover the strap exactly like the looks do.
  // one plate set per outfit because the strap seats differently per sleeve
  if (maleLook && spec.watch && spec.watch !== "none") {
    layers.push({ src: plate(`male_watch_${maleLook}_${spec.watch}`) });
  }

  if (spec.character === "female") {
    const kind = spec.outfit?.kind;
    layers.push({ src: plate(`fem_outfit_${FEM_DRESS_KEYS.has(kind ?? "") ? kind : "sheath"}`) });
  } else {
    layers.push({ src: plate(`male_outfit_${maleLook}`) });
  }

  if (spec.character === "female" && spec.neck && spec.neck !== "none") {
    layers.push({ src: plate(`fem_neck_${spec.neck}`) });
  }

  // her earring is authored per hairstyle - under hair like the real frame
  const styles = spec.character === "female" ? FEM_STYLE_KEYS : MALE_STYLE_KEYS;
  const colors = spec.character === "female" ? FEM_HC_KEYS : MALE_HC_KEYS;
  const style = styles.has(spec.hair?.style ?? "")
    ? spec.hair!.style
    : DEFAULT_SPEC[spec.character].hair!.style;
  if (spec.character === "female") {
    layers.push({ src: plate(`fem_earring_${style}`) });
  }

  const color = colors.has(spec.hair?.color ?? "")
    ? spec.hair!.color
    : DEFAULT_SPEC[spec.character].hair!.color;
  if (spec.hair) {
    layers.push({ src: plate(`${p}_hair_${style}_${color}`) });
  }

  // hands rest in front of the torso at the talking frame - always last.
  // per outfit: each garment hides a different wrist/hand band
  const okind = spec.character === "female"
    ? (FEM_DRESS_KEYS.has(spec.outfit?.kind ?? "") ? spec.outfit!.kind : "sheath")
    : maleLook;
  layers.push({ src: plate(`${p}_hands_${okind}_${skin}`) });
  return layers;
}
