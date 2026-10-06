import {castRenderConfig} from './render-config';
import {FEM_HAIR_COLORS,MALE_HAIR_COLORS,maleWatchAvailable,normalizeCastSpec,type CastSpec} from './spec';

export type LivePartGroup='body'|'hair'|'garment'|'neck'|'earring'|'watch';
export type LivePart={glb:string;lines?:string;hair?:string;skin?:string;lip?:string;hairHex?:string;tint?:Record<string,string>;ink?:Record<string,number>};
export type LiveManifest={version:string;parts:Partial<Record<LivePartGroup,Record<string,LivePart>>>;hairShade?:Partial<Record<'f'|'m',Record<string,number[]>>>;outline?:{width:number;colour:number}|null};
export type LiveSelection=Partial<Record<LivePartGroup,{key:string;part:LivePart}>>;

export function livePartKeys(raw:CastSpec):Partial<Record<LivePartGroup,string>>{
 const s=normalizeCastSpec(raw),c=s.character==='female'?'f':'m',o=s.outfit!.kind;
 const keys:Partial<Record<LivePartGroup,string>>={body:`${c}-face${s.face}-${o}`,garment:`${c}-${o}`};
 if(s.hair!.style!=='bald')keys.hair=`${c}-${s.hair!.style}`;
 if(c==='f'){if(s.neck&&s.neck!=='none')keys.neck=`f-${s.neck}`;keys.earring=`f-${s.hair!.style}`;}
 else if(s.watch&&s.watch!=='none'&&maleWatchAvailable(o))keys.watch=`m-${s.watch}-${o}`;
 return keys;
}

export function selectLiveParts(spec:CastSpec,manifest:LiveManifest):{selection:LiveSelection;missing:LivePartGroup[]}{
 const s=normalizeCastSpec(spec),c=s.character==='female'?'f':'m',selection:LiveSelection={},missing:LivePartGroup[]=[];
 for(const [group,wanted] of Object.entries(livePartKeys(s)) as [LivePartGroup,string][]){
  const set=manifest.parts[group]??{};
  let key:string|undefined=set[wanted]?wanted:undefined;
  if(!key&&group==='watch')key=Object.keys(set).sort().find(k=>k.startsWith(`m-${s.watch}-`));
  if(key&&group==='garment'){const want=Object.keys(liveColours(s).garments).sort().join(),have=Object.keys(set[key].tint??{}).sort().join();if(want!==have)key=undefined;}
  if(key)selection[group]={key,part:set[key]};
  else if(group!=='earring')missing.push(group);
 }
 return {selection,missing};
}

const catalogHex=(raw:CastSpec)=>{const s=normalizeCastSpec(raw);return ((s.character==='female'?FEM_HAIR_COLORS:MALE_HAIR_COLORS) as readonly {key:string;hex:string}[]).find(c=>c.key===s.hair!.color)?.hex.replace('#','')??'';};
export function liveColours(raw:CastSpec){
 const env=castRenderConfig(raw).env,garments:Record<string,string>={};
 for(const item of (env.CAST_GARMENTS??'').split(',')){const [asset,hex]=item.split('=');if(asset&&hex)garments[asset]=hex.toUpperCase();}
 if(env.CAST_DRESS&&env.CAST_DRESS_HEX)garments[env.CAST_DRESS]=env.CAST_DRESS_HEX.toUpperCase();
 return {skin:(env.CAST_SKIN_HEX??'').toUpperCase(),lip:env.CAST_CHARACTER==='female'?(env.CAST_LIP_HEX||'A86F66').toUpperCase():'',hair:(env.CAST_HAIR_HEX||catalogHex(raw)).toUpperCase(),garments};
}

const linear=(hex:string)=>[0,2,4].map(i=>{const v=parseInt(hex.slice(i,i+2),16)/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});
export const tintRatio=(target:string,base:string)=>{const t=linear(target),b=linear(base);return t.map((v,i)=>v/Math.max(b[i],1e-4)) as [number,number,number];};
export const luminance=(r:number,g:number,b:number)=>.2126*r+.7152*g+.0722*b;
export function hairTint(target:string,base:string){const t=linear(target),b=linear(base);return {colour:t as [number,number,number],scale:1/Math.max(luminance(b[0],b[1],b[2]),1e-4)};}
export function hairShadeRatio(manifest:LiveManifest,character:'f'|'m',target:string,base:string){const set=manifest.hairShade?.[character],t=set?.[target.toUpperCase()],b=set?.[base.toUpperCase()];return t&&b?t.map((v,k)=>v/Math.max(b[k],1e-5)) as [number,number,number]:null;}
