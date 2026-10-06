import {readFile} from 'node:fs/promises';
import {requireSession} from '@/lib/route-auth';
import {problem} from '@/lib/http';
import {castLive3dAsset} from '@/lib/cast-live3d';
export const runtime='nodejs';
export async function GET(request:Request,context:{params:Promise<{path:string[]}>}){
 const auth=await requireSession(request);if(auth.response)return auth.response;
 const asset=castLive3dAsset((await context.params).path);if(!asset)return problem(auth.id,404,'CAST_LIVE3D_NOT_FOUND','Presenter part not found','Reload the creator.');
 return new Response(new Uint8Array(await readFile(asset.file)),{headers:{'Content-Type':asset.type,'Cache-Control':asset.manifest?'private, no-cache':'private, max-age=31536000, immutable','X-Content-Type-Options':'nosniff'}});
}
