import {writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {DEFAULT_SPEC,FEM_HAIR_COLORS,MALE_HAIR_COLORS,WATCHES,type CastSpec,type FaceId} from '../src/studio-v2/cast/spec';
import {castRenderConfig} from '../src/studio-v2/cast/render-config';
const F=DEFAULT_SPEC.female,M=DEFAULT_SPEC.male;
const f=(face:FaceId,style:string,kind:string,neck:string):CastSpec=>({...F,face,hair:{...F.hair!,style},outfit:{...F.outfit!,kind,color:({sheath:'navy',maxi:'burgundy',column:'sage',cocktail:'emerald',qipao:'rose'} as Record<string,string>)[kind]},neck});
const m=(face:FaceId,style:string,kind:string,watch:string|null):CastSpec=>({...M,face,hair:{...M.hair!,style},outfit:{...M.outfit!,kind,color:({o1:'navy',o2:'ivory',o3:'blue',o4:'burgundy',o5:'cream'} as Record<string,string>)[kind]},watch});
const specs:Record<string,CastSpec>={
 m0:m(0,'quiff','o3',null),m1:m(1,'crop','o1','analog'),m2:m(2,'braids','o2','digital'),m3:m(0,'swept','o4',null),m4:m(1,'bald','o5',null),
 m5:m(2,'quiff','o1','smart'),m6:m(0,'crop','o2','chrono'),m7:m(1,'swept','o1','dress'),
 f0:f(0,'long','sheath','fine'),f1:f(1,'bob','maxi','pendant'),f2:f(2,'bangs','column','pearls'),f3:f(0,'bun','cocktail','choker'),f4:f(1,'braid','qipao','scarf'),f5:f(2,'long','sheath','none'),
};
const planned=new Set(Object.values(specs).map(s=>`${s.character}-${s.face}-${s.outfit!.kind}`));
for(const face of [0,1,2] as FaceId[]){
 for(const kind of ['sheath','maxi','column','cocktail','qipao'])if(!planned.has(`female-${face}-${kind}`))specs[`b_f_${face}_${kind}`]=f(face,'bob',kind,'none');
 for(const kind of ['o1','o2','o3','o4','o5'])if(!planned.has(`male-${face}-${kind}`))specs[`b_m_${face}_${kind}`]=m(face,'quiff',kind,null);
}
const watches=new Set(Object.values(specs).map(s=>`${s.watch}-${s.outfit!.kind}`));
for(const w of WATCHES)for(const kind of ['o1','o2'])if(w.key!=='none'&&!watches.has(`${w.key}-${kind}`))specs[`w_m_${w.key}_${kind}`]=m(0,'quiff',kind,w.key);
for(const c of FEM_HAIR_COLORS)specs[`c_f_${c.key}`]={...f(1,'bob','maxi','pendant'),hair:{style:'bob',color:c.key}};
for(const c of MALE_HAIR_COLORS)specs[`c_m_${c.key}`]={...m(0,'quiff','o3',null),hair:{style:'quiff',color:c.key}};
for(const [id,spec] of Object.entries(specs)){
 const config=castRenderConfig(spec),key=createHash('sha256').update(JSON.stringify(config)).digest('hex'),dir=path.join(process.env.CAST_LIVE3D_OUT??path.join(process.cwd(),'engine_sources/makehuman-lineart/out/cast-live3d'),'jobs',id);
 mkdirSync(dir,{recursive:true});writeFileSync(`${dir}/request.json`,JSON.stringify({key,config}));writeFileSync(`${dir}/spec.json`,JSON.stringify(spec));
 console.log(id,key.slice(0,8),spec.face,spec.hair!.style,spec.outfit!.kind,spec.neck??spec.watch);
}
