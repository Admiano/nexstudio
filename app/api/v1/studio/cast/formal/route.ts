import {requireSession} from '@/lib/route-auth';
import {json} from '@/lib/http';
import {availableFormalWardrobe} from '@/lib/cast-formal-wardrobe';
export const runtime='nodejs';
export async function GET(request:Request){
 const auth=await requireSession(request);if(auth.response)return auth.response;
 return json({available:availableFormalWardrobe()},auth.id,{headers:{'Cache-Control':'private, no-store'}});
}
