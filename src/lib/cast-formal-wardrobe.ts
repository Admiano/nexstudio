// Only advertise real SceneBam formal wardrobe files verified against the live cast.
// Missing, stale or unverified outfits remain disabled in the Cast builder.
import {createHash} from 'node:crypto';
import {existsSync,readFileSync} from 'node:fs';
import path from 'node:path';
import {CAST_SOURCE_VERSION,FEM_FORMAL_OUTFITS,MALE_FORMAL_OUTFITS,isFormalOutfit,type CastSpec} from '@/studio-v2/cast/spec';

export const FORMAL_VARIANTS=[...FEM_FORMAL_OUTFITS.map(x=>'female:'+x.key),...MALE_FORMAL_OUTFITS.map(x=>'male:'+x.key)];
export function formalWardrobeRoot(){return process.env.SCENEBAM_FORMAL_ASSET_ROOT??path.join(process.env.CAST_PROJECT_ROOT??process.cwd(),'engine_sources/makehuman-lineart/out/scenebam-formal');}
export const formalSceneName=(gender:'female'|'male',kind:string)=>gender+'-'+kind.replace(/^formal-/,'')+'.blend';
export function availableFormalWardrobe():string[]{
  const root=formalWardrobeRoot(),manifestPath=path.join(root,'manifest.json');
  if(!existsSync(manifestPath))return [];
  let manifest:{castSourceVersion?:string;liveVmHashMatched?:boolean;validated?:Record<string,{sha256?:string;independentSuitAndTie?:boolean;rigAndMotion?:boolean}>};
  try{manifest=JSON.parse(readFileSync(manifestPath,'utf8'));}catch{return [];}
  if(manifest.castSourceVersion!==CAST_SOURCE_VERSION||manifest.liveVmHashMatched!==true)return [];
  return FORMAL_VARIANTS.filter(key=>{
    const record=manifest.validated?.[key];
    if(!record||!record.independentSuitAndTie||!record.rigAndMotion||!record.sha256||!/^[0-9a-f]{64}$/i.test(record.sha256))return false;
    const [gender,kind]=key.split(':') as ['female'|'male',string];
    const file=path.join(root,formalSceneName(gender,kind));
    if(!existsSync(file))return false;
    try{return createHash('sha256').update(readFileSync(file)).digest('hex')===record.sha256.toLowerCase();}catch{return false;}
  });
}
export function formalSpecAvailable(spec:Pick<CastSpec,'character'|'outfit'>):boolean{
 return !isFormalOutfit(spec.outfit?.kind)||availableFormalWardrobe().includes(spec.character+':'+spec.outfit?.kind);
}
