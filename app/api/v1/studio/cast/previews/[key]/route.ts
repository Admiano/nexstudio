import {requireSession} from '@/lib/route-auth';
import {json,problem} from '@/lib/http';
import {castPreviewStatus,startCastPreviewWorker} from '@/lib/cast-preview';
export const runtime='nodejs';
export async function GET(request:Request,context:{params:Promise<{key:string}>}){
 const auth=await requireSession(request);if(auth.response)return auth.response;
 const {key}=await context.params,preview=castPreviewStatus(key);if(preview&&['queued','rendering'].includes(preview.status))startCastPreviewWorker();
 return preview?json(preview,auth.id):problem(auth.id,404,'CAST_PREVIEW_NOT_FOUND','Preview not found','Select the look again.');
}
