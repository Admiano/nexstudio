import {ENVIRONMENTS,type EnvironmentId,type EnvironmentFormat} from "./environments";
// Saved selections for the authoritative modular presenter assembler.
export const CAST_SOURCE_VERSION = "bf88447b8f898bea078c44b9202cfe2b7ff13be5";

export type CastCharacter = "female" | "male";
export type FaceId = 0 | 1 | 2;

export interface CastOutfitSpec {
  kind: string;
  // Female dress or male top colour. Older specs use the authored trouser/shoe
  // defaults; newer specs can choose and colour each piece independently.
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
  environment?: EnvironmentId | null;
  environmentFormat?: EnvironmentFormat;
  sourceVersion?: string;
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
  { key: "long", label: "Long straight", note: "slim gold hoop" },
  { key: "bob", label: "Blunt bob", note: "gold bar drop" },
  { key: "bangs", label: "Bangs", note: "pearl stud" },
  { key: "bun", label: "Sleek bun", note: "statement hoops" },
  { key: "braid", label: "Side braid", note: "teardrop" },
] as const;

export const MALE_HAIRSTYLES = [
  { key: "bald", label: "Bald" },
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
  { key: "rose", label: "Soft rose", hex: "#A86F66" },
  { key: "red", label: "Classic red", hex: "#B3202A" },
  { key: "berry", label: "Berry", hex: "#8A2A4E" },
  { key: "coral", label: "Coral", hex: "#E0664F" },
  { key: "nude", label: "Nude", hex: "#B8826F" },
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
  { key: "maxi", label: "Long-sleeve maxi", note: "full length, covered neckline" },
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
export const maleWatchAvailable = (top: string) => top === "o1" || top === "o2";

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
    outfit: { kind: "o3", color: "blue" }, watch: null, voiceId: null,
  },
};

export const MALE_BOTTOMS = [
 {key:"trousers",label:"Tailored trousers",asset:"mindfront_male_trousers_1",hex:"#3A3A40"},
 {key:"straight-jeans",label:"Straight jeans",asset:"elvs_jeans_straight_leg",hex:"#2E3A55"},
 {key:"chinos",label:"Chinos",asset:"mindfront_male_trousers_2",hex:"#B59A6E"},
 {key:"classic-jeans",label:"Classic jeans",asset:"punkduck_male_classic_jeans",hex:"#3A4660"},
 {key:"wool-trousers",label:"Wool trousers",asset:"toigo_wool_pants",hex:"#3A3A40"},
] as const;
export const MALE_SHOES = [
 {key:"oxfords",label:"Oxfords",asset:"mindfront_shoes_oxford_male",hex:"#3A2A20"},
 {key:"sneakers",label:"Comfort sneakers",asset:"punkduck_comfortable_sneakers",hex:"#ECEAE4"},
 {key:"monk-straps",label:"Monk straps",asset:"mindfront_shoes_monk_strap_male",hex:"#4A2E1E"},
 {key:"classic-sneakers",label:"Classic sneakers",asset:"culturalibre_sneakers",hex:"#E8E6E0"},
] as const;
export const MALE_OUTFIT_PIECES:Record<string,{bottom:string;shoes:string}> = {
 o1:{bottom:"trousers",shoes:"oxfords"},o2:{bottom:"straight-jeans",shoes:"sneakers"},o3:{bottom:"chinos",shoes:"monk-straps"},o4:{bottom:"classic-jeans",shoes:"classic-sneakers"},o5:{bottom:"wool-trousers",shoes:"oxfords"},
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

export const isHexColour = (v:unknown):v is string => typeof v==="string" && /^#?[0-9a-f]{6}$/i.test(v);
export function normalizeColour(v:string|null|undefined,keys:Set<string>,fallback:string):string {
 if(v&&keys.has(v))return v;
 return isHexColour(v)?"#"+v.replace(/^#/,"").toUpperCase():fallback;
}
export function malePieces(s:CastSpec){
 const d=MALE_OUTFIT_PIECES[s.outfit?.kind??"o3"]??MALE_OUTFIT_PIECES.o3,p=s.outfit?.pieces;
 const b=MALE_BOTTOMS.find(x=>x.key===p?.bottom)??MALE_BOTTOMS.find(x=>x.key===d.bottom)!;
 const h=MALE_SHOES.find(x=>x.key===p?.shoes)??MALE_SHOES.find(x=>x.key===d.shoes)!;
 return {bottom:b.key,shoes:h.key,bottomColor:isHexColour(p?.bottomColor)?"#"+p.bottomColor.replace(/^#/,"").toUpperCase():b.hex,shoesColor:isHexColour(p?.shoesColor)?"#"+p.shoesColor.replace(/^#/,"").toUpperCase():h.hex};
}
export function normalizeCastSpec(input:CastSpec|null|undefined,hint?:CastCharacter):CastSpec{
 const character:CastCharacter=input?.character==="male"?"male":input?.character==="female"?"female":hint??"female",d=DEFAULT_SPEC[character];
 const face:FaceId=input?.face===1||input?.face===2?input.face:0;
 const styles=character==="female"?FEM_STYLE_KEYS:MALE_STYLE_KEYS,colors=character==="female"?FEM_HC_KEYS:MALE_HC_KEYS;
 const hairStyle=input?.hair?.style&&styles.has(input.hair.style)?input.hair.style:d.hair!.style;
 const kinds=character==="female"?FEM_DRESS_KEYS:MALE_OUTFIT_KEYS;
 const kind=input?.outfit?.kind&&kinds.has(input.outfit.kind)?input.outfit.kind:d.outfit!.kind;
 const defaults=character==="female"?FEM_DRESS_DEFAULT_COLOR:MALE_TOP_DEFAULT_COLOR;
 return {environment:ENVIRONMENTS.some(e=>e.key===input?.environment)?input!.environment:null,environmentFormat:input?.environmentFormat==='landscape'||input?.environmentFormat==='portrait'?input.environmentFormat:'square',character,face,skin:normalizeColour(input?.skin,SKIN_KEYS,d.skin),hair:{style:hairStyle,color:normalizeColour(input?.hair?.color,colors,d.hair!.color)},
 lip:character==="female"?normalizeColour(input?.lip,LIP_KEYS,d.lip!):null,
 neck:character==="female"?(input?.neck===null||input?.neck==="none"?null:input?.neck&&NECK_KEYS.has(input.neck)?input.neck:d.neck):null,
 outfit:{kind,color:normalizeColour(input?.outfit?.color,character==="female"?FEM_DRESS_COLOR_KEYS:MALE_TOP_COLOR_KEYS,defaults[kind]),...(character==="male"&&input?.outfit?.pieces?{pieces:malePieces({...d,outfit:{kind,pieces:input.outfit.pieces}})}:{})},
 watch:character==="male"&&maleWatchAvailable(kind)?(input?.watch===null||input?.watch==="none"?null:input?.watch&&WATCH_KEYS.has(input.watch)?input.watch:d.watch):null,
 voiceId:input?.voiceId??d.voiceId,sourceVersion:CAST_SOURCE_VERSION};
}
