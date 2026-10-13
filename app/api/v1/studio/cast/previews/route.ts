import {requireSession} from '@/lib/route-auth';
import {json,problem,zodProblem} from '@/lib/http';
import {castSpecSchema} from '@/lib/cast-spec-schema';
import {formalSpecAvailable} from '@/lib/cast-formal-wardrobe';
import {enqueueCastPreview} from '@/lib/cast-preview';
import {normalizeCastSpec,type CastSpec} from '@/studio-v2/cast/spec';
export const runtime='nodejs';
export async function POST(request:Request){
 const auth=await requireSession(request);if(auth.response)return auth.response;
 const body=castSpecSchema.safeParse(await request.json().catch(()=>null));if(!body.success)return zodProblem(auth.id,body.error);
 if(!formalSpecAvailable(body.data))return problem(auth.id,409,'FORMAL_ASSETS_UNVERIFIED','Formal outfit unavailable','Verified production wardrobe files are not installed yet.');
 try{const preview=enqueueCastPreview(normalizeCastSpec(body.data as CastSpec));return json(preview,auth.id,{status:preview.status==='ready'?200:202});}
 catch(e){if(e instanceof Error&&e.message==='CAST_PREVIEW_CAPACITY')return problem(auth.id,429,'CAST_PREVIEW_CAPACITY','Preview queue is busy','Try again shortly.');console.error('CAST_PREVIEW_QUEUE_FAILED',e);return problem(auth.id,503,'CAST_PREVIEW_UNAVAILABLE','Preview unavailable','Try again shortly.');}
}
