import {ENVIRONMENTS} from "@/studio-v2/cast/environments";
import {z} from 'zod';
import {FEM_DRESSES,FEM_DRESS_COLORS,FEM_HAIR_COLORS,FEM_HAIRSTYLES,LIPS,MALE_BOTTOMS,MALE_HAIR_COLORS,MALE_HAIRSTYLES,MALE_OUTFITS,MALE_SHOES,MALE_TOP_COLORS,NECKS,SKINS,WATCHES,isHexColour} from '@/studio-v2/cast/spec';
export const castSpecSchema=z.object({
 character:z.enum(['female','male']),face:z.number().int().min(0).max(2).default(0),skin:z.string().trim().max(24).default('light'),
 hair:z.object({style:z.string().trim().max(40),color:z.string().trim().max(24)}).nullable().default(null),lip:z.string().trim().max(24).nullable().default(null),neck:z.string().trim().max(24).nullable().default(null),
 outfit:z.object({kind:z.string().trim().max(40),color:z.string().trim().max(24).nullable().optional(),pieces:z.object({bottom:z.string().max(40).optional(),shoes:z.string().max(40).optional(),bottomColor:z.string().max(24).optional(),shoesColor:z.string().max(24).optional()}).strict().optional()}).nullable().default(null),
 environment:z.enum(ENVIRONMENTS.map(e=>e.key)).nullable().optional(),environmentFormat:z.enum(['landscape','square','portrait']).optional(),
 watch:z.string().trim().max(24).nullable().default(null),voiceId:z.string().trim().max(120).nullable().default(null),sourceVersion:z.string().max(64).optional(),
}).superRefine((s,ctx)=>{
 const f=s.character==='female';
 const choice=(v:string|null|undefined,items:readonly {key:string}[],path:string[],colour=false)=>{if(v!=null&&!items.some(x=>x.key===v)&&!(colour&&isHexColour(v)))ctx.addIssue({code:'custom',message:'Choose an available option or a six-digit colour.',path});};
 choice(s.skin,SKINS,['skin'],true);choice(s.hair?.style,f?FEM_HAIRSTYLES:MALE_HAIRSTYLES,['hair','style']);choice(s.hair?.color,f?FEM_HAIR_COLORS:MALE_HAIR_COLORS,['hair','color'],true);
 choice(s.outfit?.kind,f?FEM_DRESSES:MALE_OUTFITS,['outfit','kind']);choice(s.outfit?.color,f?FEM_DRESS_COLORS:MALE_TOP_COLORS,['outfit','color'],true);
 choice(s.lip,LIPS,['lip'],true);choice(s.neck,NECKS,['neck']);choice(s.watch,WATCHES,['watch']);choice(s.outfit?.pieces?.bottom,MALE_BOTTOMS,['outfit','pieces','bottom']);choice(s.outfit?.pieces?.shoes,MALE_SHOES,['outfit','pieces','shoes']);
 for(const k of ['bottomColor','shoesColor'] as const)choice(s.outfit?.pieces?.[k],[],['outfit','pieces',k],true);
});
