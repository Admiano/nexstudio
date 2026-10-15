import { CAST_SOURCE_VERSION, FEM_DRESS_COLORS, FEM_HAIR_COLORS, LIPS, MALE_BOTTOMS, MALE_HAIR_COLORS, MALE_SHOES, MALE_TOP_COLORS, SKINS, FORMAL_SUIT_COLORS,FORMAL_TIE_COLORS,FORMAL_DEFAULT_TIE,isFormalOutfit,formalOutfitId,malePieces, normalizeCastSpec, type CastSpec } from './spec';
export const CAST_RENDER_VERSION = 'approved-v3-v6-native-formals-v22-upper-thigh';
export const CAST_PREVIEW_FRAME = 27;
const DRESSES: Record<string,string> = {sheath:'mindfront_f_dress_11',maxi:'mindfront_f_dress_09',column:'mindfront_f_dress_07',cocktail:'punkduck_black_cocktail_dress',qipao:'punkduck_middle_length_qipao'};
const TOPS: Record<string,string> = {o1:'namuhekam_male_polo_shirt',o2:'toigo_basic_tucked_t-shirt',o3:'elvs_male_shirt_untucked_bd1',o4:'mindfront_knitted_sweater_01',o5:'toigo_fisherman_sweater'};
const HAIR: Record<string,string> = {bald:'elvs_maxwell_hair',afro:'afro01',crop:'short01',quiff:'elvs_maxwell_hair',braids:'elvs_braided_rows',swept:'elvs_grump_hair'};
const hex = (v:string,set:readonly {key:string;hex:string}[]) => (set.find(x=>x.key===v)?.hex??v).replace(/^#/,'').toUpperCase();
const formalColour = (v:string,set:readonly {key:string;hex:string}[]) => v==='original'?'ORIGINAL':hex(v,set);
export function castRenderConfig(raw:CastSpec,frame=CAST_PREVIEW_FRAME){
 const s=normalizeCastSpec(raw),f=s.character==='female',p=malePieces(s),formal=isFormalOutfit(s.outfit?.kind),baseKind=formal?(f?'sheath':'o3'):s.outfit!.kind;
 const env:Record<string,string>={
  CAST_CHARACTER:s.character,CAST_FACE:String(s.face),CAST_HAIR_STYLE:s.hair!.style,
  CAST_HAIR_HEX:f&&s.hair!.color==='auburn'?'':hex(s.hair!.color,f?FEM_HAIR_COLORS:MALE_HAIR_COLORS),
  CAST_SKIN_HEX:hex(s.skin,SKINS),CAST_LIP_HEX:f?(s.lip==='rose'?'':hex(s.lip!,LIPS)):'',
  CAST_NECK:formal?'none':s.neck??'none',CAST_WATCH:formal?'none':s.watch??'none',CAST_DRESS:f?DRESSES[baseKind]:'',CAST_DRESS_HEX:f?hex(formal?'navy':s.outfit!.color!,FEM_DRESS_COLORS):'',
  CAST_MALE_LOOK:f?'':baseKind.toUpperCase(),CAST_MALE_HAIR:f?'':HAIR[s.hair!.style],CAST_HAIR_DYE:!f&&s.hair!.color==='dye'?'8A1F3C':'',
  CAST_GARMENTS:f?'':[`${TOPS[baseKind]}=${hex(formal?'blue':s.outfit!.color!,MALE_TOP_COLORS)}`,`${MALE_BOTTOMS.find(b=>b.key===p.bottom)!.asset}=${hex(p.bottomColor,[])}`,`${MALE_SHOES.find(b=>b.key===p.shoes)!.asset}=${hex(p.shoesColor,[])}`].join(','),
  CAST_FORMAL_ID:formal?formalOutfitId(s.character,s.outfit!.kind):'',
  CAST_FORMAL_SUIT_HEX:formal?formalColour(s.outfit!.color!,FORMAL_SUIT_COLORS):'',
  CAST_FORMAL_TIE_HEX:formal?formalColour(s.outfit?.pieces?.tieColor??FORMAL_DEFAULT_TIE,FORMAL_TIE_COLORS):'',
 };
 const coverageProfile=!f&&['o3','o4','o5'].includes(baseKind)?{garmentCoverageProfile:'intact-wrists-v1'}:{};
 return {sourceVersion:CAST_SOURCE_VERSION,renderVersion:CAST_RENDER_VERSION,oralProfile:'anatomical-mouth-v13',...coverageProfile,frame,framing:'upper-thigh',resolutionPercentage:50,env};
}
export type CastRenderConfig=ReturnType<typeof castRenderConfig>;
