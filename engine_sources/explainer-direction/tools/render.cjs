#!/usr/bin/env node
'use strict';
// Local development capture only. No provider fallback, CDP attachment or service restart.
const fs=require('node:fs'),fsp=require('node:fs/promises'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {spawn,spawnSync}=require('node:child_process');
const ENGINE=path.resolve(__dirname,'..'),REPO=path.resolve(ENGINE,'../..');
require('../runtime/plan.js');
const {validatePlan}=globalThis.ExplainerDirectionPlan;
const NODE='/home/ubuntu/.nvm/versions/node/v24.19.0/bin/node';
const CHROME='/home/ubuntu/.local/bin/google-chrome';
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const json=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const within=(file,root)=>file===root||file.startsWith(root+path.sep);
function run(executable,args,options={}) {
  return new Promise((resolve,reject)=>{const child=spawn(executable,args,{...options,stdio:['ignore','pipe','pipe']});let out='',err='';child.stdout.on('data',s=>{out+=s;});child.stderr.on('data',s=>{err=(err+s).slice(-24000);});child.on('error',reject);child.on('exit',code=>code===0?resolve({stdout:out,stderr:err}):reject(new Error(`${executable} exited ${code}: ${err}`)));});
}
function validateWithPython(plan){
  const script='import json,sys; from explainer_direction.contracts import validate_plan; validate_plan(json.load(sys.stdin))';
  const checked=spawnSync('/usr/bin/python3',['-c',script],{input:JSON.stringify(plan),encoding:'utf8',env:{...process.env,PYTHONPATH:ENGINE,PYTHONDONTWRITEBYTECODE:'1'},maxBuffer:4e6});
  if(checked.status!==0)throw new Error(`Frozen validate_plan rejected input: ${checked.stderr||checked.error}`);
  return validatePlan(plan);
}
async function probe(file){return JSON.parse((await run('ffprobe',['-v','error','-show_format','-show_streams','-of','json',file])).stdout);}
function declaredSource(s) {
  const licenses=['CC0-1.0','CC-BY-4.0','CC-BY-SA-4.0','MIT','Apache-2.0','OFL-1.1','public-domain','owned','permission'];
  if(!s||Object.keys(s).sort().join(',')!=='commercial_use,id,license,locator,uri'||!licenses.includes(s.license)||s.commercial_use!==true||['id','uri','locator'].some(k=>typeof s[k]!=='string'||!s[k].trim()))throw new Error('Audio source requires exact commercial-use-safe source declaration');
  if(s.license==='permission'&&/^(unknown|none|n\/a)$/i.test(s.locator.trim()))throw new Error('Audio permission locator is missing');
}
async function audioInputs(options,plan,out){
  const result=[];
  if(options.voice){
    if(!options.voiceMeta)throw new Error('--voice requires --voice-meta FILE; undeclared/fixture voices are never silently production proof');
    const meta=json(options.voiceMeta);declaredSource(meta.source);
    if(typeof meta.provider!=='string'||!meta.provider.trim()||typeof meta.route!=='string'||!meta.route.trim()||!/^[a-f0-9]{64}$/.test(meta.audio_sha256))throw new Error('Voice metadata requires provider, route and exact audio_sha256');
    result.push({path:path.resolve(options.voice),role:'voice',start_ms:0,gain:1,source:meta.source,metadata:meta});
  }else if(options.voiceMeta)throw new Error('--voice-meta requires --voice');
  if(options.audio){
    const declared=json(options.audio);
    if(!declared||Object.keys(declared).join(',')!=='tracks'||!Array.isArray(declared.tracks))throw new Error('--audio FILE must contain {tracks:[...]}');
    const base=path.dirname(path.resolve(options.audio));
    for(const track of declared.tracks){
      if(!track||Object.keys(track).sort().join(',')!=='gain,path,role,source,start_ms'||!['sound','music'].includes(track.role)||typeof track.path!=='string'||!Number.isFinite(track.start_ms)||track.start_ms<0||!Number.isFinite(track.gain)||track.gain<0||track.gain>2)throw new Error('Declared audio tracks require path, sound/music role, source, start_ms>=0, gain 0..2');
      declaredSource(track.source);result.push({...track,path:path.resolve(base,track.path)});
    }
  }
  const sources=new Map([plan.provenance.source,...plan.evidence.map(e=>e.source),...plan.scenes.flatMap(s=>s.actors.filter(a=>a.kind==='image').map(a=>a.payload.source))].map(s=>[s.id,s]));
  const ordered=s=>JSON.stringify(Object.fromEntries(Object.entries(s).sort(([a],[b])=>a.localeCompare(b))));
  if(result.length)fs.mkdirSync(path.join(out,'audio'));
  for(const [index,input] of result.entries()){
    const bytes=fs.readFileSync(input.path),hash=sha(bytes);
    if(input.metadata&&input.metadata.audio_sha256!==hash)throw new Error('Voice audio_sha256 does not match supplied bytes');
    if(input.metadata?.alignment_audio_sha256&&input.metadata.alignment_audio_sha256!==hash)throw new Error('Voice/alignment byte identity mismatch');
    const old=sources.get(input.source.id);if(old&&ordered(old)!==ordered(input.source))throw new Error('Conflicting audio provenance for stable source id');sources.set(input.source.id,input.source);
    // ffprobe and ffmpeg consume the same immutable byte snapshot that was hashed.
    input.source_path=input.path;input.path=path.join(out,'audio',String(index).padStart(3,'0')+path.extname(input.path));
    fs.writeFileSync(input.path,bytes);
    const media=await probe(input.path),streams=media.streams.filter(s=>s.codec_type==='audio');
    if(!streams.length)throw new Error(`No audio stream: ${input.source_path}`);
    const duration=Number(media.format.duration)*1000;
    if(!Number.isFinite(duration)||duration<=0||input.start_ms+duration>plan.duration_ms+60)throw new Error(`Audio must fit the declared film interval, no implicit truncation/loop: ${input.source_path}`);
    input.sha256=hash;input.duration_ms=duration;input.stream=streams[0];
  }
  return result;
}
async function resolveAssets(plan,options){
  const roots=[fs.realpathSync(REPO),...(options.assetRoot?[fs.realpathSync(options.assetRoot)]:[])];
  const requested=[{url:plan.style.typography.font_url,kind:'font',license:plan.style.typography.font_license},...plan.scenes.flatMap(s=>s.actors.filter(a=>a.kind==='image').map(a=>({url:a.payload.src,kind:'image',source:a.payload.source})))];
  const assets=new Map();
  for(const request of requested){const raw='/'+request.url.replace(/^\/+/,''),url=new URL(raw,'http://asset.local/').pathname,rel=path.posix.normalize(raw).slice(1);if(assets.has(url))continue;let file=null;
    for(const root of roots){const candidate=path.resolve(root,rel);if(!within(candidate,root))throw new Error('Asset escaped declared root');if(fs.existsSync(candidate)){const real=fs.realpathSync(candidate);if(!within(real,root))throw new Error('Asset symlink escaped declared root');if(!fs.statSync(real).isFile())throw new Error('Asset is not a regular file');file=real;break;}}
    if(!file)throw new Error(`Declared local asset not found: ${url}`);
    const bytes=await fsp.readFile(file);
    if(request.kind==='image'){
      const prefix=(values,offset=0)=>values.every((n,i)=>bytes[offset+i]===n),extension=path.extname(file).toLowerCase();
      const raster=extension==='.png'?prefix([137,80,78,71,13,10,26,10]):['.jpg','.jpeg'].includes(extension)?prefix([255,216,255]):prefix([82,73,70,70])&&prefix([87,69,66,80],8);
      if(!raster)throw new Error(`Declared image is not admitted raster bytes: ${url}`);
    }
    assets.set(url,{...request,url,file,bytes,sha256:sha(bytes)});
  }
  return assets;
}
function contentType(file){const ext=path.extname(file).toLowerCase();return {'.js':'application/javascript','.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf','.otf':'font/otf','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}[ext]||'application/octet-stream';}
async function createServer(plan,assets){
  const runtime=new Map(['/runtime/plan.js','/runtime/film.js'].map(url=>[url,fs.readFileSync(path.join(ENGINE,url))]));
  const page='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>html,body,#mount{margin:0;width:100%;height:100%;overflow:hidden;background:'+plan.output.background+'}</style></head><body><div id="mount"></div><script src="/runtime/plan.js"></script><script src="/runtime/film.js"></script><script>window.start=async()=>{const p=await (await fetch("/plan.json")).json();window.film=ExplainerDirection.createFilm(p,document.getElementById("mount"));await film.ready;return film.inspect();};</script></body></html>';
  const errors=[];
  const server=http.createServer((req,res)=>{try{const url=req.url;if(url==='/'||url==='/index.html'){res.writeHead(200,{'Content-Type':'text/html','Cache-Control':'no-store'});return res.end(page);}if(url==='/plan.json'){res.writeHead(200,{'Content-Type':'application/json'});return res.end(JSON.stringify(plan));}if(runtime.has(url)){res.writeHead(200,{'Content-Type':'application/javascript'});return res.end(runtime.get(url));}if(assets.has(url)){const asset=assets.get(url);res.writeHead(200,{'Content-Type':contentType(asset.file),'Cache-Control':'public,max-age=31536000,immutable'});return res.end(asset.bytes);}if(url==='/favicon.ico'){res.writeHead(204);return res.end();}errors.push(`Undeclared asset request ${url}`);res.writeHead(404);res.end('Undeclared asset');}catch(e){errors.push(e.message);res.writeHead(500);res.end('Asset error');}});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));return {server,origin:`http://127.0.0.1:${server.address().port}`,errors,runtime};
}
async function render(options){
  if(!options.plan||!options.out)throw new Error('Required: --plan FILE --out DIR');
  const out=path.resolve(options.out),parent=fs.realpathSync(path.dirname(out));
  if(within(out,REPO)||within(parent,fs.realpathSync(REPO)))throw new Error('Render output must be outside git');
  if(fs.existsSync(out))throw new Error('Output directory already exists; use a fresh directory to prevent stale frames/artifacts');
  fs.mkdirSync(out);const manifest={schema:'explainer-direction.render/v1',status:'RUNNING',authority:'P8',certification:'DEVELOPMENT_RENDER_EVIDENCE_ONLY',output_directory:out,errors:[],commands:[],frames:[],audio:[]};
  let server,browser;
  try{
    const original=fs.readFileSync(path.resolve(options.plan));const plan=validateWithPython(JSON.parse(original));
    const workers=options.workers===undefined?2:Number(options.workers);if(!Number.isInteger(workers)||workers<2||workers>4)throw new Error('--workers must be 2..4');
    manifest.plan={input:path.resolve(options.plan),input_sha256:sha(original),validated_sha256:sha(JSON.stringify(plan)),film_id:plan.film_id,direction:plan.direction,provenance:plan.provenance};manifest.canvas=plan.canvas;manifest.aspect=plan.aspect;manifest.fps=plan.output.fps;manifest.duration_ms=plan.duration_ms;manifest.workers=workers;
    fs.writeFileSync(path.join(out,'plan.json'),JSON.stringify(plan,null,2));
    const assets=await resolveAssets(plan,options),audio=await audioInputs(options,plan,out);manifest.assets=[...assets.values()].map(({bytes,...x})=>x);manifest.audio=audio;
    const local=await createServer(plan,assets);server=local.server;manifest.runtime=[...local.runtime].map(([url,bytes])=>({url,sha256:sha(bytes)}));
    const {chromium}=require(path.join(REPO,'engine_sources/explainer-locks/node_modules/playwright-core'));
    browser=await chromium.launch({executablePath:options.chrome||CHROME,headless:true,ignoreDefaultArgs:['--headless=old'],args:['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-background-networking','--force-color-profile=srgb']});
    manifest.browser={version:browser.version(),executable:options.chrome||CHROME,isolated_profile:true,desktop_cdp:false};
    const frameDir=path.join(out,'frames');fs.mkdirSync(frameDir);const count=Math.ceil(plan.duration_ms*plan.output.fps/1000);manifest.frame_count=count;
    let next=0;
    const jobs=Array.from({length:Math.min(workers,count)},async()=>{
      const context=await browser.newContext({viewport:plan.canvas,deviceScaleFactor:1,reducedMotion:'reduce'});
      await context.route('**/*',route=>route.request().url().startsWith(local.origin+'/')?route.continue():route.abort());
      const page=await context.newPage();const pageErrors=[];page.on('pageerror',e=>pageErrors.push(e.message));
      try{await page.goto(local.origin,{waitUntil:'load'});const inspection=await page.evaluate(()=>window.start());if(!manifest.initial_inspection)manifest.initial_inspection=inspection;
        for(;;){const index=next++;if(index>=count)break;const ms=index*1000/plan.output.fps;await page.evaluate(t=>{window.film.seek(t);},ms);const buffer=await page.screenshot({type:'png',animations:'disabled',caret:'hide',timeout:60000});const name=`${String(index).padStart(6,'0')}.png`;await fsp.writeFile(path.join(frameDir,name),buffer);manifest.frames[index]={index,time_ms:ms,file:'frames/'+name,sha256:sha(buffer)};if(pageErrors.length)throw new Error(pageErrors.join('\n'));}
      }finally{await context.close();}
    });
    const completed=await Promise.allSettled(jobs);const failure=completed.find(x=>x.status==='rejected');if(failure)throw failure.reason;if(local.errors.length)throw new Error(local.errors.join('\n'));
    await browser.close();browser=null;await new Promise(resolve=>server.close(resolve));server=null;
    const film=path.join(out,'film.mp4'),args=['-hide_banner','-loglevel','error','-y','-framerate',String(plan.output.fps),'-i',path.join(frameDir,'%06d.png')];
    audio.forEach(x=>args.push('-i',x.path));
    if(audio.length){const filters=audio.map((x,i)=>`[${i+1}:a:0]aresample=48000,volume=${x.gain},adelay=${x.start_ms}:all=1,apad[a${i}]`);filters.push(audio.map((x,i)=>`[a${i}]`).join('')+`amix=inputs=${audio.length}:normalize=0:duration=longest,atrim=duration=${plan.duration_ms/1000}[mixed]`);args.push('-filter_complex',filters.join(';'),'-map','0:v:0','-map','[mixed]','-c:a','aac','-b:a','192k');}else args.push('-an');
    args.push('-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-t',String(plan.duration_ms/1000),'-movflags','+faststart',film);
    manifest.commands.push({executable:'ffmpeg',args});await run('ffmpeg',args);const media=await probe(film),video=media.streams.find(s=>s.codec_type==='video');if(!video||video.width!==plan.canvas.width||video.height!==plan.canvas.height)throw new Error('Encoded canvas does not match native plan');if(audio.length&&!media.streams.some(s=>s.codec_type==='audio'))throw new Error('Encoded film lost declared audio');
    manifest.silent=audio.length===0;
    manifest.movie={file:'film.mp4',sha256:sha(await fsp.readFile(film)),probe:media};manifest.status='RENDERED_DEVELOPMENT_PREFLIGHT';
    fs.writeFileSync(path.join(out,'render-manifest.json'),JSON.stringify(manifest,null,2));return manifest;
  }catch(e){manifest.status='FAILED';manifest.errors.push({name:e.name,message:e.message,stack:e.stack});fs.writeFileSync(path.join(out,'errors.json'),JSON.stringify(manifest.errors,null,2));fs.writeFileSync(path.join(out,'render-manifest.json'),JSON.stringify(manifest,null,2));throw e;
  }finally{if(browser)await browser.close().catch(()=>{});if(server)await new Promise(resolve=>server.close(resolve));}
}
function args(argv){const result={};const flags={'--plan':'plan','--out':'out','--voice':'voice','--voice-meta':'voiceMeta','--audio':'audio','--asset-root':'assetRoot','--workers':'workers','--chrome':'chrome'};for(let i=0;i<argv.length;i++){const key=flags[argv[i]];if(!key||!argv[i+1]||argv[i+1].startsWith('--')||result[key]!==undefined)throw new Error(`Unknown/duplicate/incomplete argument: ${argv[i]}`);result[key]=argv[++i];}return result;}
if(require.main===module){if(process.argv.includes('--help'))console.log(`Use ${NODE} tools/render.cjs --plan FILE --out NEW_EXTERNAL_DIR [--workers 2..4] [--asset-root DIR] [--voice FILE --voice-meta JSON] [--audio JSON]. Voice metadata: {source,provider,route,audio_sha256,alignment_audio_sha256?}. Audio: {tracks:[{path,role:"sound"|"music",source,start_ms,gain}]}. No implicit downloads, looping, truncation, live inference or creative approval.`);else Promise.resolve().then(()=>render(args(process.argv.slice(2)))).then(m=>console.log(JSON.stringify({status:m.status,manifest:path.join(m.output_directory,'render-manifest.json'),movie:m.movie}))).catch(e=>{console.error(e.stack);process.exitCode=1;});}
module.exports={render,createServer,resolveAssets,validateWithPython,args};
