import assert from 'node:assert/strict';import {mkdtempSync,rmSync,readFileSync,writeFileSync,mkdirSync} from 'node:fs';import os from 'node:os';import path from 'node:path';
import {DEFAULT_SPEC} from '../src/studio-v2/cast/spec';import {castPreviewKey,castPreviewStatus,castPreviewImage,enqueueCastPreview} from '../src/lib/cast-preview';import {castRenderConfig} from '../src/studio-v2/cast/render-config';import {castSpecSchema} from '../src/lib/cast-spec-schema';
import {requireTrustedOrigin} from '../src/lib/route-auth';
const dir=mkdtempSync(path.join(os.tmpdir(),'cast-queue-'));process.env.CAST_PREVIEW_CACHE_DIR=dir;process.env.CAST_PREVIEW_EXTERNAL_WORKER='1';
try{
 const forwarded=new Request('https://0.0.0.0:3000/api/v1/studio/cast/previews',{method:'POST',headers:{origin:'http://localhost',cookie:'studio_session=probe'}});
 assert.equal(requireTrustedOrigin(forwarded,'preview-origin'),null);
 const spec={...DEFAULT_SPEC.female,skin:'#CA9864'},a=enqueueCastPreview(spec),b=enqueueCastPreview({...spec,voiceId:'emma'});assert.equal(a.key,b.key);assert.equal(a.status,'queued');
 const job=path.join(dir,a.key);assert.deepEqual(JSON.parse(readFileSync(path.join(job,'request.json'),'utf8')).config,castRenderConfig(spec));
 assert.equal(castPreviewImage('../../etc/passwd'),null);assert.equal(castPreviewStatus('invalid'),null);
 writeFileSync(path.join(job,'status.json'),JSON.stringify({status:'rendering'}));assert.equal(castPreviewStatus(a.key)?.status,'rendering');
 writeFileSync(path.join(job,'status.json'),JSON.stringify({status:'failed'}));assert.equal(enqueueCastPreview(spec).status,'queued');
 writeFileSync(path.join(job,'preview.png'),'completed-test-image');assert.equal(castPreviewStatus(a.key)?.status,'ready');assert.equal(enqueueCastPreview(spec).status,'ready');
 assert.ok(!castSpecSchema.safeParse({...spec,hair:{style:'../../bad',color:'black'}}).success);assert.ok(!castSpecSchema.safeParse({...DEFAULT_SPEC.male,outfit:{kind:'o3',pieces:{unknown:'x'}}}).success);assert.ok(castSpecSchema.safeParse({...spec,hair:{style:'bun',color:'#445566'}}).success);
 for(let i=0;i<64;i++){const config=castRenderConfig({...spec,skin:'#'+i.toString(16).padStart(6,'0')}),key=castPreviewKey(config),p=path.join(dir,key);mkdirSync(p,{recursive:true});writeFileSync(path.join(p,'request.json'),'{}');}
 assert.throws(()=>enqueueCastPreview({...spec,skin:'#CC9988'}),/CAST_PREVIEW_CAPACITY/);console.log('PASS queue deduplication, retries, cache, capacity, schema and traversal rejection');
}finally{rmSync(dir,{recursive:true,force:true});}
