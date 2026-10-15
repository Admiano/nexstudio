import {createHash} from 'node:crypto';
import {existsSync,readFileSync} from 'node:fs';
import path from 'node:path';
import {CAST_SOURCE_VERSION,FEMALE_FORMAL_OUTFITS,MALE_FORMAL_OUTFITS,isFormalOutfit,type CastSpec} from '@/studio-v2/cast/spec';

// Fail closed until exact live VM parity and art/motion/collision approval are recorded.
const LOOKS=[...FEMALE_FORMAL_OUTFITS.map(x=>['female',x.key] as const),...MALE_FORMAL_OUTFITS.map(x=>['male',x.key] as const)];
type Certified={rigAndMotion?:boolean;independentSuitAndTie?:boolean;visualApproved?:boolean;collisionCertified?:boolean};
type Manifest={castSourceVersion?:string;liveVmParityCertified?:boolean;collisionCertified?:boolean;files?:Record<string,string>;certified?:Record<string,Certified>};
export function availableFormalWardrobe():string[]{
 if(process.env.SCENEBAM_FORMAL_WARDROBE_ENABLED!=='1')return [];
 const root=process.env.CAST_PROJECT_ROOT??process.cwd(),manifestPath=path.join(root,'config/scenebam-formal-assets.json');
 if(!existsSync(manifestPath))return [];
 let manifest:Manifest;
 try{manifest=JSON.parse(readFileSync(manifestPath,'utf8')) as Manifest;}catch{return [];}
 if(manifest.castSourceVersion!==CAST_SOURCE_VERSION||manifest.liveVmParityCertified!==true||manifest.collisionCertified!==true)return [];
 const assets=process.env.CAST_FORMAL_ASSETS_DIR??path.join(root,'engine_sources/makehuman-lineart/assets/cast-formals');
 return LOOKS.flatMap(([character,kind])=>{
   const id=character+'-'+kind.replace(/^formal-/,''),proof=manifest.certified?.[id],sha=manifest.files?.[id];
   if(!proof?.rigAndMotion||!proof.independentSuitAndTie||!proof.visualApproved||!proof.collisionCertified||!sha||!/^[a-f0-9]{64}$/i.test(sha))return [];
   const file=path.join(assets,id+'.blend');if(!existsSync(file))return [];
   try{if(createHash('sha256').update(readFileSync(file)).digest('hex')!==sha.toLowerCase())return [];}catch{return [];}
   return [character+':'+kind];
 });
}
export function formalSpecAvailable(spec:Pick<CastSpec,'character'|'outfit'>|null|undefined):boolean{
 return !isFormalOutfit(spec?.outfit?.kind)||availableFormalWardrobe().includes(spec!.character+':'+spec!.outfit!.kind);
}
