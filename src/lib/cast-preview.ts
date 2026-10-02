import path from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
import {spawn} from 'node:child_process';
import {existsSync,mkdirSync,readFileSync,readdirSync,renameSync,writeFileSync} from 'node:fs';
import {castRenderConfig,type CastRenderConfig} from '@/studio-v2/cast/render-config';
import type {CastSpec} from '@/studio-v2/cast/spec';
// Next's standalone server changes cwd; keep the worker and its source anchored.
const castProjectRoot=()=>process.env.CAST_PROJECT_ROOT??process.cwd();
export const castPreviewDir=()=>process.env.CAST_PREVIEW_CACHE_DIR??path.join(castProjectRoot(),'engine_sources/makehuman-lineart/out/cast-previews');
export const isPreviewKey=(key:string)=>/^[a-f0-9]{64}$/.test(key);
export const castPreviewKey=(config:CastRenderConfig)=>createHash('sha256').update(JSON.stringify(config)).digest('hex');
export type CastPreviewStatus={key:string;status:'queued'|'rendering'|'ready'|'failed';imageUrl?:string;message?:string};
export function castPreviewImage(key:string){
 if(!isPreviewKey(key))return null;
 for(const p of [path.join(castPreviewDir(),key,'preview.png'),path.join(castProjectRoot(),'public/cast/assembled',`${key}.png`)])if(existsSync(p))return p;
 return null;
}
export function castPreviewStatus(key:string):CastPreviewStatus|null{
 if(!isPreviewKey(key))return null;
 if(castPreviewImage(key))return {key,status:'ready',imageUrl:`/api/v1/studio/cast/previews/${key}/image`};
 const dir=path.join(castPreviewDir(),key);if(!existsSync(path.join(dir,'request.json')))return null;
 try{const s=JSON.parse(readFileSync(path.join(dir,'status.json'),'utf8'));if(s.status==='failed')return {key,status:'failed',message:'Preview could not be rendered. Try again.'};if(s.status==='rendering')return {key,status:'rendering'};}catch{}
 return {key,status:'queued'};
}
function atomicStatus(dir:string,data:unknown){const tmp=path.join(dir,`status-${randomUUID()}.tmp`);writeFileSync(tmp,JSON.stringify(data));renameSync(tmp,path.join(dir,'status.json'));}
let lastWorkerStart=0;
export function startCastPreviewWorker(){
 if(process.env.CAST_PREVIEW_EXTERNAL_WORKER==='1'||Date.now()-lastWorkerStart<5000)return;
 lastWorkerStart=Date.now();
 const root=castProjectRoot();
 const worker=spawn(process.env.PYTHON_BIN??'python3',[path.join(root,'scripts/cast-preview-worker.py'),'--drain'],{cwd:root,detached:true,stdio:'ignore',env:process.env});
 const failed=()=>{lastWorkerStart=0;try{for(const d of readdirSync(castPreviewDir(),{withFileTypes:true}))if(d.isDirectory()&&isPreviewKey(d.name)&&castPreviewStatus(d.name)?.status==='queued')atomicStatus(path.join(castPreviewDir(),d.name),{status:'failed',error:'CAST_PREVIEW_WORKER_START_FAILED'});}catch(e){console.error('CAST_PREVIEW_WORKER_STATUS_FAILED',e);}};
 worker.on('error',e=>{console.error('CAST_PREVIEW_WORKER_START_FAILED',e.message);failed();});worker.on('exit',code=>{if(code&&code!==0)failed();});worker.unref();
}
export function enqueueCastPreview(spec:CastSpec):CastPreviewStatus{
 const config=castRenderConfig(spec),key=castPreviewKey(config),old=castPreviewStatus(key);
 if(old&&old.status!=='failed'){if(old.status!=='ready')startCastPreviewWorker();return old;}
 const root=castPreviewDir();mkdirSync(root,{recursive:true});
 const pending=readdirSync(root,{withFileTypes:true}).filter(d=>d.isDirectory()&&isPreviewKey(d.name)&&['queued','rendering'].includes(castPreviewStatus(d.name)?.status??'')).length;
 if(pending>=64)throw new Error('CAST_PREVIEW_CAPACITY');
 const dir=path.join(root,key);mkdirSync(dir,{recursive:true});const tmp=path.join(dir,`request-${randomUUID()}.tmp`);writeFileSync(tmp,JSON.stringify({key,config,createdAt:new Date().toISOString()}));renameSync(tmp,path.join(dir,'request.json'));atomicStatus(dir,{status:'queued',updatedAt:new Date().toISOString()});startCastPreviewWorker();return {key,status:'queued'};
}
