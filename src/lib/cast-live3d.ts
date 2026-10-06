import path from 'node:path';
import {existsSync} from 'node:fs';
const castProjectRoot=()=>process.env.CAST_PROJECT_ROOT??process.cwd();
export const castLive3dDir=()=>process.env.CAST_LIVE3D_DIR??path.join(castProjectRoot(),'engine_sources/makehuman-lineart/out/cast-live3d/parts');
const ASSET=/^(?:manifest\.json|(?:body|hair|garment|neck|earring|watch)\/[a-z0-9-]+\.(?:glb|lines\.bin|hair\.bin))$/;
export function castLive3dAsset(parts:string[]){
 const rel=parts.join('/');if(!ASSET.test(rel))return null;
 const file=path.join(castLive3dDir(),rel);return existsSync(file)?{file,type:rel.endsWith('.json')?'application/json':rel.endsWith('.glb')?'model/gltf-binary':'application/octet-stream',manifest:rel==='manifest.json'}:null;
}
