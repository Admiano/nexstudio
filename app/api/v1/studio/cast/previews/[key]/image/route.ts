import {readFile} from 'node:fs/promises';
import {requireSession} from '@/lib/route-auth';
import {problem} from '@/lib/http';
import {castPreviewImage} from '@/lib/cast-preview';
export const runtime='nodejs';
export async function GET(request:Request,context:{params:Promise<{key:string}>}){
 const auth=await requireSession(request);if(auth.response)return auth.response;
 const {key}=await context.params,p=castPreviewImage(key);if(!p)return problem(auth.id,404,'CAST_PREVIEW_NOT_FOUND','Preview not found','Select the look again.');
 return new Response(new Uint8Array(await readFile(p)),{headers:{'Content-Type':'image/png','Cache-Control':'private, max-age=31536000, immutable','X-Content-Type-Options':'nosniff'}});
}
