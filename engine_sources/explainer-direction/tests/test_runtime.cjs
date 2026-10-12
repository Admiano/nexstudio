'use strict';
// Test-only execution evidence, not live inference, TTS alignment, commercial proof or P8 lock.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const ENGINE=path.resolve(__dirname,'..'),REPO=path.resolve(ENGINE,'../..');
require('../runtime/plan.js');
const {validatePlan,KINDS}=globalThis.ExplainerDirectionPlan;
const {render,createServer,resolveAssets,validateWithPython,args}=require('../tools/render.cjs');
const {chromium}=require(path.join(REPO,'engine_sources/explainer-locks/node_modules/playwright-core'));
const OUTPUT='/home/ubuntu/vid_study/explainer_direction';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const copy=v=>JSON.parse(JSON.stringify(v));
const SOURCE={id:'runtime_fixture_art',uri:'test-fixture://runtime',locator:'Test-only generated raster and declared sound, never production evidence',license:'owned',commercial_use:true};
const BASE=spawnSync('/usr/bin/python3',['-c','import json; from test_contracts import fixture_plan; print(json.dumps({t:fixture_plan(t) for t in ("water","energy","travel")}))'],{encoding:'utf8',env:{...process.env,PYTHONPATH:ENGINE+path.delimiter+path.join(ENGINE,'tests'),PYTHONDONTWRITEBYTECODE:'1'}});
if(BASE.status!==0)throw new Error(BASE.stderr);const baselines=JSON.parse(BASE.stdout);
const MEANING=spawnSync('/home/ubuntu/.pyenv/versions/3.12.13/bin/python',['-c','import json; from test_meaning import meaning_score; from explainer_direction.compiler import compile_score; print(json.dumps(compile_score(meaning_score(),"16:9")))'],{encoding:'utf8',env:{...process.env,PYTHONPATH:ENGINE+path.delimiter+path.join(ENGINE,'tests'),PYTHONDONTWRITEBYTECODE:'1'}});
if(MEANING.status!==0)throw new Error(MEANING.stderr);
test('runtime boundary rejects mutated semantic bindings and backward material motion',()=>{
  const base=JSON.parse(MEANING.stdout);
  assert.doesNotThrow(()=>validatePlan(base));
  const badEntity=copy(base);badEntity.scenes[0].actors.find(a=>a.id==='upper_actor').meaning_binding={entity:'water'};
  assert.throws(()=>validatePlan(badEntity),/meaning|spatial/i);
  const badQuantity=copy(base);badQuantity.meaning_graph.quantities[0].subject='water';
  assert.throws(()=>validatePlan(badQuantity),/quantity|meaning|measured/i);
  const badCarrier=copy(base);badCarrier.scenes[0].actors.find(a=>a.id==='material').meaning_binding={entity:'upper'};
  assert.throws(()=>validatePlan(badCarrier),/meaning|carrier/i);
  const badDirection=copy(base);badDirection.scenes[0].actors.find(a=>a.id==='material').payload.path.direction='reverse';
  assert.throws(()=>validatePlan(badDirection),/flow|direction/i);
  const wrongFact=copy(base);wrongFact.meaning_graph.facts.find(f=>f.id==='charging').carrier='upper';
  assert.throws(()=>validatePlan(wrongFact),/carrier|flow/i);
  for(const [kind,from,to] of [['causes','system','water'],['produces','water','system']]){
    const p=copy(base);
    p.meaning_graph.facts.push({id:'invalid_causal_edge',kind,from,to,evidence_ids:['transfer']});
    assert.throws(()=>validatePlan(p),/causation|producer/i);
  }
  const reverseMotion=copy(base),s=reverseMotion.scenes[0],material=s.actors.find(a=>a.id==='material');
  material.initial.flow=.8;
  s.events=[{id:'reverse',verb:'update',targets:['material'],start_ms:s.start_ms+100,end_ms:s.start_ms+200,dependencies:[],claim_ids:['transfer'],rationale:'Wrong direction'}];
  s.tracks=[{actor_id:'material',property:'flow',from:.8,to:.2,start_ms:s.start_ms+100,end_ms:s.start_ms+200,easing:'linear',verb:'update',event_id:'reverse',claim_ids:['transfer'],rationale:'Wrong direction'}];
  assert.throws(()=>validatePlan(reverseMotion),/advance|direction/i);
});
test('qualitative orientation needs an exact scene-to-meaning binding',()=>{
  const plan=JSON.parse(MEANING.stdout),scene=plan.scenes[0];
  plan.meaning_graph.facts.push({id:'illustrative_orientation',kind:'aligns_with',from:'upper',to:'water',evidence_ids:['transfer']});
  scene.relations.push({id:'illustrative_orientation',kind:'aligns_with',from:'upper_actor',to:'material',evidence_ids:['transfer']});
  validatePlan(plan);
  const wrongEndpoint=copy(plan);wrongEndpoint.scenes[0].relations.at(-1).to='lower_actor';
  assert.throws(()=>validatePlan(wrongEndpoint),/exact meaning fact/);
  const wrongSubject=copy(plan);wrongSubject.meaning_graph.facts.at(-1).from='water';wrongSubject.meaning_graph.facts.at(-1).to='upper';
  assert.throws(()=>validatePlan(wrongSubject),/orientation needs physical subject/);
});
function fixturePlan(topic='water',aspect='16:9'){
  const plan=copy(baselines[topic]),[width,height]={'16:9':[1920,1080],'9:16':[1080,1920],'1:1':[1080,1080]}[aspect];
  plan.aspect=aspect;plan.canvas={width,height};plan.output.fps=3;plan.title=`Runtime ${topic} primitive test`;const s=plan.scenes[0];
  function box(x,y,w,h){return {x,y,width:w,height:h};}
  const original=s.actors;
  original[0].geometry={...box(64,220,width*.40,190),font_size:72,line_height:86,lines:['Readout']};
  original[1].geometry=box(width*.53,220,width*.40,190);original[1].payload.orientation=aspect==='9:16'?'vertical':'horizontal';
  original[2].geometry=box(64,450,width-128,100);
  function actor(id,kind,geometry,payload,initial,role='primary'){
    return {id,identity:id,kind,role,label:{text:'Channel state',shape:'Reservoir',particles:'Illustrative transport',axis:'Volume domain',connector:'Flow path',panel:'Context field',image:'Test raster',group:'Transport construction'}[kind]||id,meaning:'Illustrative runtime test actor, not a production claim',evidence_ids:['before','after'],geometry,payload,initial:{opacity:1,x:geometry.x,y:geometry.y,...initial},retained:false,layout:{anchor:kind==='panel'?'background':'context'}};
  }
  const shape=actor('reservoir','shape',box(90,620,180,180),{shape:'circle'},{variant:'circle',draw:0,fill:.25});
  const particles=actor('transport','particles',box(width*.42,620,width*.36,180),{count:24,arrangement:'stream',illustrative:true},{flow:0,fill:.25});
  const linkBox=box(90,610,width*.7,220);linkBox.points=[{x:90,y:100},{x:width*.42+width*.18-90,y:100}];
  const connector=actor('flow_path','connector',linkBox,{from:'reservoir',to:'transport',arrow:true,routing:'direct'},{draw:0});
  const axisBox=box(90,height-210,width*.43,110);axisBox.points=[{x:10,y:30},{x:axisBox.width-10,y:30}];
  const quantity=plan.evidence[0].quantity;
  const axis=actor('domain','axis',axisBox,{domain:original[1].payload.domain,unit:quantity.unit,dimension:quantity.dimension,orientation:'horizontal',ticks:5},{draw:0},'muted');
  const group=actor('construction','group',box(64,600,width-128,240),{children:['reservoir','transport','flow_path']},{},'primary');
  const panel=actor('context_field','panel',box(0,0,width,height),{},{opacity:.25,fill:.1},'surface');
  const heading=actor('integrated_text','text',{...box(64,65,width-128,125),font_size:52,line_height:62,lines:['An open channel changes the flow']},{text:'An open channel changes the flow',purpose:'headline',max_lines:2},{text:'An open channel changes the flow'},'text');
  const image=actor('raster','image',box(width-220,height-210,128,128),{src:'/test-assets/pixel.png',mime:'image/png',fit:'contain',source:SOURCE},{},'accent');
  s.actors=[panel,heading,...original,group,shape,particles,connector,axis,image];
  for(const a of s.actors){Object.assign(a.initial,{x:a.geometry.x,y:a.geometry.y,reveal:1,scale:1,highlight:a.initial.highlight??0});}
  const linked=s.events.find(e=>e.verb==='update');linked.targets=s.actors.map(a=>a.id);
  for(const a of s.actors){const changes={opacity:a.kind==='panel'?.6:.9,reveal:.95,scale:a.kind==='group'?1.02:1,highlight:1,x:a.initial.x+(a.kind==='panel'?12:a.kind==='shape'?30:0),y:a.initial.y+(a.kind==='panel'?4:a.kind==='shape'?15:0)};
    if(a.kind==='connector'){delete changes.x;delete changes.y;delete changes.scale;}
    if(a.kind==='text')changes.text='The second channel is open';
    if(['number','bar'].includes(a.kind))changes.value=plan.evidence[1].quantity.value;
    if(a.kind==='shape')Object.assign(changes,{variant:'hexagon',draw:1,fill:1});
    if(['axis','connector'].includes(a.kind))changes.draw=1;
    if(['bar','panel','particles'].includes(a.kind))changes.fill=1;
    if(a.kind==='particles')changes.flow=.75;
    if(a.kind==='selector')changes.selection=1;
    for(const [property,to] of Object.entries(changes)){
      const old=s.tracks.find(t=>t.event_id===linked.id&&t.actor_id===a.id&&t.property===property);
      const track={event_id:linked.id,actor_id:a.id,property,from:a.initial[property],to,start_ms:linked.start_ms,end_ms:linked.end_ms,easing:['text','variant','selection'].includes(property)?'step':'ease_in_out',verb:'update',rationale:linked.rationale,claim_ids:linked.claim_ids};
      if(old)Object.assign(old,track);else s.tracks.push(track);
    }
  }
  s.transition={kind:'wipe',direction:'right',start_ms:5000,end_ms:6000};
  const second=copy(s);second.id='terminal_hold';second.start_ms=6000;second.end_ms=9000;second.events=[{id:'terminal_hold_event',verb:'hold',targets:[],start_ms:6000,end_ms:9000,dependencies:[],claim_ids:['after'],rationale:'Inspect terminal linked state, without perpetual motion'}];second.tracks=[];second.transition={kind:'hold',start_ms:9000,end_ms:9000};
  for(const a of second.actors){a.retained=true;for(const track of s.tracks.filter(t=>t.actor_id===a.id))a.initial[track.property]=track.to;if(['number','bar'].includes(a.kind))a.value_binding='after';}
  plan.scenes.push(second);plan.duration_ms=9000;return validateWithPython(plan);
}
let browser,temp;
test.before(async()=>{
  assert(fs.statSync(OUTPUT).isDirectory());temp=fs.mkdtempSync(path.join(OUTPUT,'runtime-tests-'));
  fs.mkdirSync(path.join(temp,'test-assets'));
  // Actual decodable test raster: no artwork synthesis is used in live mode.
  fs.writeFileSync(path.join(temp,'test-assets/pixel.png'),Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==','base64'));
  browser=await chromium.launch({executablePath:'/home/ubuntu/.local/bin/google-chrome',headless:true,ignoreDefaultArgs:['--headless=old'],args:['--headless=new','--no-sandbox','--disable-dev-shm-usage','--force-color-profile=srgb']});
});
test.after(async()=>{if(browser)await browser.close();console.log('Runtime test artifacts: '+temp);});
async function pageFor(plan,body){const assets=await resolveAssets(plan,{assetRoot:temp});const local=await createServer(plan,assets),context=await browser.newContext({viewport:plan.canvas,deviceScaleFactor:1});try{const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(local.origin,{waitUntil:'load'});await page.evaluate(()=>start());await body(page);assert.deepEqual(errors,[]);assert.deepEqual(local.errors,[]);}finally{await context.close();await new Promise(resolve=>local.server.close(resolve));}}
test('strict execution boundary rejects unsupported and unbound plans',()=>{
  const plan=fixturePlan();assert.deepEqual(validatePlan(plan),plan);
  const mutations=[p=>p.scenes[0].actors[0].kind='unsupported',p=>p.scenes[0].actors[0].initial.unknown=.5,p=>p.scenes[0].tracks[0].easing='bounce',p=>p.scenes[0].events[0].dependencies=['missing'],p=>p.scenes[0].actors.find(a=>a.kind==='image').payload.src='https://bad.example/art.png',p=>p.scenes[0].tracks.find(t=>t.property==='value').to=41,p=>p.scenes[0].actors.find(a=>a.kind==='text').initial.text='Invented 41 L',p=>p.scenes[0].actors.find(a=>a.kind==='image').payload.source.commercial_use=false,p=>p.scenes[0].actors.find(a=>a.kind==='group').payload.children.push('construction'),p=>p.scenes[1].actors.find(a=>a.kind==='shape').initial.fill=0,p=>p.scenes[0].tracks[0].from=.123,p=>p.scenes[0].tracks[0].property='position',p=>p.direction.status='CREATIVE_LOCKED'];
  mutations.forEach(fn=>{const p=copy(plan);fn(p);assert.throws(()=>validatePlan(p));});
  assert.throws(()=>args(['--workers','5','--unsupported','x']));
});
test('native physical relationships remain independent from process order at execution',()=>{
  for(const aspect of ['16:9','9:16','1:1']){
    const p=fixturePlan('water',aspect),s=p.scenes[0],members=new Set(['reservoir','transport']);
    s.tracks=s.tracks.filter(t=>!(members.has(t.actor_id)&&['x','y'].includes(t.property)));
    s.relations.push({id:'physical_left',kind:'left_of',from:'reservoir',to:'transport',evidence_ids:['before']});
    validatePlan(p);
    const flipped=copy(p);flipped.scenes[0].relations.at(-1).kind='right_of';
    assert.throws(()=>validatePlan(flipped),/physical ordering/);
    const moved=copy(p),a=moved.scenes[0].actors.find(x=>x.id==='reservoir'),e=moved.scenes[0].events.find(x=>x.verb==='update');
    for(const axis of ['x','y'])moved.scenes[0].tracks.push({event_id:e.id,actor_id:a.id,property:axis,from:a.initial[axis],to:a.initial[axis]+10,start_ms:e.start_ms,end_ms:e.end_ms,easing:'linear',verb:e.verb,rationale:e.rationale,claim_ids:e.claim_ids});
    assert.throws(()=>validatePlan(moved),/shared physical group/);
  }
});
test('path-bound transport follows native moving routes in both directions without double group transforms',async()=>{
  const result=spawnSync('/usr/bin/python3',['-c','import json; from test_compiler import material_score; from explainer_direction.compiler import compile_score; print(json.dumps({a:compile_score(material_score(grouped=True),a) for a in ("16:9","9:16","1:1")}))'],{encoding:'utf8',env:{...process.env,PYTHONPATH:ENGINE+path.delimiter+path.join(ENGINE,'tests'),PYTHONDONTWRITEBYTECODE:'1'}});
  assert.equal(result.status,0,result.stderr);
  const native=JSON.parse(result.stdout);
  for(const aspect of ['16:9','9:16','1:1'])for(const direction of ['forward','reverse'])for(const shared of [true,false]){
    const plan=copy(native[aspect]),s=plan.scenes[0],material=s.actors.find(a=>a.id==='material');
    material.payload.path.direction=direction;
    material.role='accent';
    if(!shared)s.actors.find(a=>a.id==='construct').payload.children=s.actors.find(a=>a.id==='construct').payload.children.filter(id=>id!=='material');
    validateWithPython(plan);validatePlan(plan);
    await pageFor(plan,async page=>{
      const first=await page.screenshot();
      const reference=await page.evaluate(()=>{
        const route=document.querySelector('[data-actor="target"] path'),target=document.querySelector('[data-actor="a"] path');
        const world=new DOMPoint(route.getPointAtLength(0).x,route.getPointAtLength(0).y).matrixTransform(route.getCTM());
        const local=world.matrixTransform(target.getCTM().inverse());return {x:local.x,y:local.y};
      });
      for(const ms of [225,350,600]){
        await page.evaluate(ms=>film.seek(ms),ms);
        const errors=await page.evaluate(({direction,reference})=>{
          const route=document.querySelector('[data-actor="target"] path'),particles=[...document.querySelectorAll('[data-actor="material"] circle')],state=film.inspect().scenes[0].states.material,total=route.getTotalLength();
          const deviation=particles.map((dot,i)=>{
            const phase=((i+.5)/particles.length+state.flow)%1,p=route.getPointAtLength(total*(direction==='reverse'?1-phase:phase));
            const expected=new DOMPoint(p.x,p.y).matrixTransform(route.getCTM()),actual=new DOMPoint(+dot.getAttribute('cx'),+dot.getAttribute('cy')).matrixTransform(dot.getCTM());
            return Math.hypot(expected.x-actual.x,expected.y-actual.y);
          });
          const target=document.querySelector('[data-actor="a"] path'),expected=new DOMPoint(reference.x,reference.y).matrixTransform(target.getCTM()),p=route.getPointAtLength(0),actual=new DOMPoint(p.x,p.y).matrixTransform(route.getCTM());
          const markers=particles.map(dot=>{const p=new DOMPoint(+dot.getAttribute('cx'),+dot.getAttribute('cy')).matrixTransform(dot.getCTM());return [p.x,p.y];});
          return {particles:Math.max(...deviation),attachment:Math.hypot(expected.x-actual.x,expected.y-actual.y),markers};
        },{direction,reference});
        assert(errors.particles<.05,`${aspect}/${direction}: route deviation ${errors.particles}`);
        assert(errors.attachment<.05,`${aspect}: detached endpoint ${errors.attachment}`);
        const pixels=spawnSync('/usr/bin/python3',['-c','import io,json,sys; from PIL import Image; im=Image.open(io.BytesIO(sys.stdin.buffer.read())).convert("RGB"); want=tuple(int(sys.argv[1][i:i+2],16) for i in (1,3,5)); points=json.loads(sys.argv[2]); found=[[im.getpixel((round(x)+dx,round(y)+dy)) for dx in range(-3,4) for dy in range(-3,4)] for x,y in points]; assert all(any(all(abs(a-b)<=12 for a,b in zip(p,want)) for p in samples) for samples in found),(want,points)',plan.style.palette.accent,JSON.stringify(errors.markers)],{input:await page.screenshot()});
        if(pixels.status!==0)fs.writeFileSync(path.join(temp,'material-visibility-failure.png'),await page.screenshot());
        assert.equal(pixels.status,0,`${aspect}/${direction}/${shared}@${ms}: ${String(pixels.stderr)}`);
      }
      assert.notEqual(hash(first),hash(await page.screenshot()));
      await page.evaluate(()=>film.seek(0));assert.equal(hash(first),hash(await page.screenshot()));
    });
    for(const mutation of [
      p=>p.scenes[0].actors.find(a=>a.id==='material').payload.path.connector='missing',
      p=>p.scenes[0].actors.find(a=>a.id==='material').payload.path.connector='a',
      p=>p.scenes[0].actors.find(a=>a.id==='material').payload.path.direction='sideways',
      p=>p.scenes[0].actors.find(a=>a.id==='material').payload.arrangement='radial',
      p=>p.scenes[0].actors.find(a=>a.id==='material').initial.x+=5,
      p=>delete p.scenes[0].actors.find(a=>a.id==='material').initial.flow,
      p=>p.scenes[0].tracks.find(t=>t.actor_id==='material').property='scale',
    ]){const broken=copy(plan);mutation(broken);assert.throws(()=>validatePlan(broken));}
  }
});
test('all primitive properties are visible and deterministic on every native aspect and topic',async()=>{
  const reports=[];
  for(const aspect of ['16:9','9:16','1:1'])for(const topic of ['water','energy','travel']){
    const plan=fixturePlan(topic,aspect);
    await pageFor(plan,async page=>{
      assert.deepEqual(await page.evaluate(()=>[...new Set([...document.querySelectorAll('[data-kind]')].map(n=>n.dataset.kind))].sort()),Object.keys(KINDS).sort());
      const initial=await page.screenshot();const startState=await page.evaluate(()=>film.inspect());
      const middle=await page.evaluate(()=>film.seek(2550));const state=middle.scenes[0].states;
      assert.equal(state.readout.value,(plan.evidence[0].quantity.value+plan.evidence[1].quantity.value)/2);assert.equal(state.stage.selection,0);assert.equal(state.reservoir.variant,'circle');assert.equal(state.flow_path.draw,.5);assert.equal(state.transport.flow,.375);
      const magnitude=await page.evaluate(()=>{const rects=document.querySelectorAll('[data-scene="change"] [data-actor="meter"] rect');return [...rects].map(n=>({width:+n.getAttribute('width'),height:+n.getAttribute('height')}));});
      const dimension=aspect==='9:16'?'height':'width';assert(Math.abs(magnitude[1][dimension]/magnitude[0][dimension]-.75)<1e-9);
      const end=await page.evaluate(()=>film.seek(3000));
      for(const track of plan.scenes[0].tracks)assert.equal(end.scenes[0].states[track.actor_id][track.property],track.to);
      const changed=await page.screenshot();assert.notEqual(hash(initial),hash(changed));
      const dom=await page.evaluate(()=>({value:document.querySelector('[data-actor="readout"] text').textContent,selector:[...document.querySelectorAll('[data-scene="change"] [data-actor="stage"] text')].map(n=>[n.textContent,n.getAttribute('fill')]),mask:document.querySelector('[data-actor="context_field"] [clip-path]').getAttribute('clip-path'),bar:[...document.querySelectorAll('[data-scene="change"] [data-actor="meter"] rect')].map(n=>({width:n.getAttribute('width'),height:n.getAttribute('height')})),trace:document.querySelector('[data-actor="flow_path"] path').getAttribute('stroke-dasharray')}));
      assert(dom.value.includes(String(plan.evidence[1].quantity.value)));assert.equal(dom.trace,'1 1');assert.equal(dom.selector[1][1].toLowerCase(),plan.style.palette.accent.toLowerCase());
      const wipe=await page.evaluate(()=>film.seek(5500));assert.deepEqual(wipe.active_scenes,['change','terminal_hold']);const masks=await page.evaluate(()=>[...document.querySelectorAll('clipPath[id*="-scene-"] rect')].map(n=>Number(n.getAttribute('width'))));assert.deepEqual(masks,[plan.canvas.width/2,plan.canvas.width/2]);
      await page.evaluate(()=>film.seek(8500));const back=await page.evaluate(()=>film.seek(0));assert.deepEqual(back.scenes,startState.scenes);const backwards=await page.screenshot();assert.equal(hash(initial),hash(backwards));
      fs.writeFileSync(path.join(temp,`${topic}-${aspect.replace(':','x')}-before.png`),initial);fs.writeFileSync(path.join(temp,`${topic}-${aspect.replace(':','x')}-after.png`),changed);
      reports.push({aspect,topic,initial_sha256:hash(initial),changed_sha256:hash(changed),backward_equal:true});
    });
  }
  fs.writeFileSync(path.join(temp,'browser-report.json'),JSON.stringify(reports,null,2));
});
test('easing, zero-duration steps, group coordinates, and all transition directions',async()=>{
  for(const easing of ['linear','ease_in','ease_out','ease_in_out','step']){
    const plan=fixturePlan();const tracks=plan.scenes[0].tracks.filter(t=>!['text','variant','selection'].includes(t.property));tracks.forEach(t=>t.easing=easing);
    await pageFor(plan,async page=>{const s=await page.evaluate(()=>film.seek(2325));const expected={linear:.25,ease_in:.0625,ease_out:.4375,ease_in_out:.125,step:0}[easing];assert.equal(s.scenes[0].states.flow_path.draw,expected);const coords=await page.evaluate(()=>{const n=document.querySelector('[data-actor="reservoir"]');const m=n.getCTM();return [m.e,m.f];});assert(Math.abs(coords[0]-30*expected*(1+.02*expected)+19.2*expected)<1e-4);assert(Math.abs(coords[1]-15*expected*(1+.02*expected)+14.4*expected)<1e-4);});
  }
  for(const direction of ['left','right','up','down']){
    const plan=fixturePlan();plan.scenes[0].transition.direction=direction;
    await pageFor(plan,async page=>{await page.evaluate(()=>film.seek(5500));const masks=await page.evaluate(()=>[...document.querySelectorAll('clipPath[id*="-scene-"] rect')].map(n=>({x:+n.getAttribute('x'),y:+n.getAttribute('y'),width:+n.getAttribute('width'),height:+n.getAttribute('height')})));if(['left','right'].includes(direction))assert(masks.every(n=>n.width===plan.canvas.width/2));else assert(masks.every(n=>n.height===plan.canvas.height/2));});
  }
  const fade=fixturePlan();fade.scenes[0].transition={kind:'fade',start_ms:5000,end_ms:6000};await pageFor(fade,async page=>{await page.evaluate(()=>film.seek(5500));assert.deepEqual(await page.evaluate(()=>[...document.querySelectorAll('[data-scene]')].map(n=>Number(n.getAttribute('opacity')))),[.5,.5]);});
  const instant=fixturePlan();const event=instant.scenes[0].events[0];event.end_ms=event.start_ms;instant.scenes[0].tracks.filter(t=>t.event_id===event.id).forEach(t=>t.end_ms=t.start_ms);await pageFor(instant,async page=>{assert.equal((await page.evaluate(()=>film.seek(2100))).scenes[0].states.stage.selection,1);});
});
test('missing declared media and unfittable text reject ready without fallback',async()=>{
  const plan=fixturePlan(),assets=await resolveAssets(plan,{assetRoot:temp});assets.delete('/test-assets/pixel.png');const local=await createServer(plan,assets),context=await browser.newContext({viewport:plan.canvas});try{const page=await context.newPage();await page.goto(local.origin);await assert.rejects(page.evaluate(()=>start()),/raster image/);assert.equal(await page.locator('svg').count(),0);}finally{await context.close();await new Promise(resolve=>local.server.close(resolve));}
  const bad=fixturePlan();bad.scenes.forEach(s=>{const a=s.actors.find(a=>a.kind==='text');a.geometry.width=10;a.geometry.height=10;});const goodAssets=await resolveAssets(bad,{assetRoot:temp}),server=await createServer(bad,goodAssets),ctx=await browser.newContext({viewport:bad.canvas});try{const page=await ctx.newPage();await page.goto(server.origin);await assert.rejects(page.evaluate(()=>start()),/does not fit/);}finally{await ctx.close();await new Promise(resolve=>server.server.close(resolve));}
});
test('actual PNG and H264 captures on all native aspects have verified hashes',async()=>{
  for(const aspect of ['16:9','9:16','1:1']){
    const plan=fixturePlan('energy',aspect),planFile=path.join(temp,`plan-${aspect.replace(':','x')}.json`);fs.writeFileSync(planFile,JSON.stringify(plan));const out=path.join(temp,`capture-${aspect.replace(':','x')}`);const manifest=await render({plan:planFile,out,assetRoot:temp,workers:2});
    assert.equal(manifest.status,'RENDERED_DEVELOPMENT_PREFLIGHT');assert.equal(manifest.frame_count,27);assert.equal(manifest.frames.length,27);assert.notEqual(manifest.frames[0].sha256,manifest.frames[9].sha256);assert.equal(hash(fs.readFileSync(path.join(out,'film.mp4'))),manifest.movie.sha256);manifest.frames.forEach(frame=>assert.equal(hash(fs.readFileSync(path.join(out,frame.file))),frame.sha256));const video=manifest.movie.probe.streams.find(s=>s.codec_type==='video');assert.equal(video.width,plan.canvas.width);assert.equal(video.height,plan.canvas.height);assert.equal(Number(video.nb_frames),27);assert(!manifest.movie.probe.streams.some(s=>s.codec_type==='audio'));
  }
  const broken=fixturePlan(),file=path.join(temp,'broken.json');broken.scenes[0].actors[0].kind='unknown';fs.writeFileSync(file,JSON.stringify(broken));const failed=path.join(temp,'failed');await assert.rejects(render({plan:file,out:failed,assetRoot:temp}),/rejected/);assert.equal(JSON.parse(fs.readFileSync(path.join(failed,'render-manifest.json'))).status,'FAILED');assert(!fs.existsSync(path.join(failed,'film.mp4')));
});
test('declared sound mixing encodes an audible scheduled track and rejects undeclared voices',async()=>{
  const sound=path.join(temp,'test-sound.wav');
  const generated=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=660:duration=0.5','-c:a','pcm_s16le',sound]);
  assert.equal(generated.status,0,String(generated.stderr));
  const planFile=path.join(temp,'sound-plan.json');fs.writeFileSync(planFile,JSON.stringify(fixturePlan()));
  const audioFile=path.join(temp,'sound-input.json');fs.writeFileSync(audioFile,JSON.stringify({tracks:[{path:sound,role:'sound',source:SOURCE,start_ms:2400,gain:.5}]}));
  const manifest=await render({plan:planFile,out:path.join(temp,'sound-capture'),assetRoot:temp,audio:audioFile});
  assert(manifest.movie.probe.streams.some(s=>s.codec_type==='audio'));
  assert.equal(manifest.audio[0].sha256,hash(fs.readFileSync(sound)));
  const decoded=spawnSync('ffmpeg',['-v','error','-i',path.join(temp,'sound-capture/film.mp4'),'-vn','-ac','1','-ar','8000','-f','f32le','pipe:1'],{maxBuffer:5e6});assert.equal(decoded.status,0,String(decoded.stderr));
  function rms(start,end){let sum=0,count=0;for(let i=Math.floor(start*8000);i<Math.floor(end*8000);i++){const n=decoded.stdout.readFloatLE(i*4);sum+=n*n;count++;}return Math.sqrt(sum/count);}
  assert(rms(2.5,2.8)>.02);assert(rms(.5,1)<.001);assert(rms(4,4.5)<.001);
  await assert.rejects(render({plan:planFile,out:path.join(temp,'undeclared-voice'),assetRoot:temp,voice:sound}),/voice-meta/);
  const metadata=path.join(temp,'voice-bad-hash.json');fs.writeFileSync(metadata,JSON.stringify({source:SOURCE,provider:'test-only-rejection',route:'NOT_TTS',audio_sha256:'0'.repeat(64)}));
  await assert.rejects(render({plan:planFile,out:path.join(temp,'voice-hash-mismatch'),assetRoot:temp,voice:sound,voiceMeta:metadata}),/does not match/);
});
test('compiled peer plans render without a private adapter on all native aspects',async()=>{
  const compiled=spawnSync('/usr/bin/python3',['-c','import json; from explainer_direction.contracts import sample_score,ASPECTS; from explainer_direction.compiler import compile_score; print(json.dumps([compile_score(sample_score(t),a) for t in ("water","energy","travel") for a in ASPECTS]))'],{encoding:'utf8',env:{...process.env,PYTHONPATH:ENGINE,PYTHONDONTWRITEBYTECODE:'1'},maxBuffer:4e6});
  assert.equal(compiled.status,0,compiled.stderr);
  for(const plan of JSON.parse(compiled.stdout))await pageFor(plan,async page=>{
    const initial=await page.screenshot();const end=await page.evaluate(()=>film.seek(3000));
    assert.equal(end.scenes[0].states.readout.value,plan.evidence[1].quantity.value);
    assert.notEqual(hash(await page.screenshot()),hash(initial));
    await page.evaluate(()=>film.seek(0));assert.equal(hash(await page.screenshot()),hash(initial));
  });
});
test('primitive variants, inherited group emphasis, connector attachment, and Unicode local assets',async()=>{
  const unicode='test-assets/transport é.png';fs.copyFileSync(path.join(temp,'test-assets/pixel.png'),path.join(temp,unicode));
  for(const [shape,arrangement] of [['rect','grid'],['diamond','radial'],['hexagon','stream']]){
    const plan=fixturePlan();plan.style.materials.surface='outlined';
    for(const scene of plan.scenes){scene.actors.find(a=>a.kind==='particles').payload.arrangement=arrangement;scene.actors.find(a=>a.kind==='shape').payload.shape=shape;scene.actors.find(a=>a.kind==='image').payload.src='/'+unicode;scene.actors.find(a=>a.kind==='image').payload.fit='cover';scene.actors.find(a=>a.kind==='connector').payload.routing='elbow';}
    plan.scenes[0].actors.find(a=>a.kind==='shape').initial.variant=shape;
    plan.scenes[0].tracks.find(t=>t.property==='variant').from=shape;
    // Isolate group highlight: descendant's own highlight stays at zero.
    const highlight=plan.scenes[0].tracks.find(t=>t.actor_id==='reservoir'&&t.property==='highlight');highlight.to=0;plan.scenes[1].actors.find(a=>a.id==='reservoir').initial.highlight=0;
    await pageFor(plan,async page=>{
      await page.evaluate(()=>film.seek(3000));
      const result=await page.evaluate(()=>{
        const shape=document.querySelector('[data-scene="change"] [data-actor="reservoir"] path');
        const connector=document.querySelector('[data-scene="change"] [data-actor="flow_path"] path');
        const m=connector.getCTM(),p=connector.getPointAtLength(0);const point=new DOMPoint(p.x,p.y).matrixTransform(m);
        const g=document.querySelector('[data-scene="change"] [data-actor="reservoir"] g g').getCTM();
        const center=new DOMPoint(90,90).matrixTransform(g);
        return {color:shape.getAttribute('fill'),point:[point.x,point.y],center:[center.x,center.y]};
      });
      assert.equal(result.color,plan.style.palette.accent.toLowerCase());
      assert(Math.abs(result.point[0]-result.center[0])<.001);assert(Math.abs(result.point[1]-result.center[1])<.001);
      await page.evaluate(()=>{film.destroy();film.destroy();});assert.equal(await page.locator('svg').count(),0);await assert.rejects(page.evaluate(()=>film.seek(0)),/destroyed/);
    });
  }
});
test('rotation composes with nested motion and keeps material attached in all native aspects',async()=>{
  for(const aspect of ['16:9','9:16','1:1']){
    const plan=fixturePlan('water',aspect),scene=plan.scenes[0],next=plan.scenes[1],event=scene.events.find(e=>e.verb==='update');
    const group=scene.actors.find(a=>a.id==='construction'),endpoint=scene.actors.find(a=>a.id==='reservoir');
    for(const [a,initial,to] of [[group,0,35],[endpoint,-20,70]]){
      a.initial.rotation=initial;
      scene.tracks.push({event_id:event.id,actor_id:a.id,property:'rotation',from:initial,to,start_ms:event.start_ms,end_ms:event.end_ms,easing:'ease_in_out',verb:'update',rationale:event.rationale,claim_ids:event.claim_ids});
      next.actors.find(b=>b.id===a.id).initial.rotation=to;
    }
    const material=copy(scene.actors.find(a=>a.id==='transport'));
    material.id=material.identity='path_material';material.payload.path={connector:'flow_path',direction:'forward'};
    Object.assign(material.initial,{opacity:1,reveal:1,scale:1,highlight:0,flow:.02});
    scene.actors.push(material);group.payload.children.push(material.id);event.targets.push(material.id);
    scene.tracks.push({event_id:event.id,actor_id:material.id,property:'flow',from:.02,to:.8,start_ms:event.start_ms,end_ms:event.end_ms,easing:'ease_in_out',verb:'update',rationale:event.rationale,claim_ids:event.claim_ids});
    const retained=copy(material);retained.retained=true;retained.initial.flow=.8;next.actors.push(retained);next.actors.find(a=>a.id===group.id).payload.children.push(material.id);
    validateWithPython(plan);validatePlan(plan);
    await pageFor(plan,async page=>{
      const before=await page.screenshot();
      for(const time of [0,2500,3000]){
        const state=await page.evaluate(t=>film.seek(t),time);
        const points=await page.evaluate(()=>{
          const route=document.querySelector('[data-scene="change"] [data-actor="flow_path"] path'),matrix=route.getCTM(),first=route.getPointAtLength(0),last=route.getPointAtLength(route.getTotalLength());
          const from=first.matrixTransform(matrix),to=last.matrixTransform(matrix);
          const shape=document.querySelector('[data-scene="change"] [data-actor="reservoir"] path');
          const center=new DOMPoint(90,90).matrixTransform(shape.getCTM());
          const dots=[...document.querySelectorAll('[data-scene="change"] [data-actor="path_material"] circle')].map(dot=>new DOMPoint(+dot.getAttribute('cx'),+dot.getAttribute('cy')).matrixTransform(dot.getCTM()));
          return {from:[from.x,from.y],to:[to.x,to.y],center:[center.x,center.y],dots:dots.map(p=>[p.x,p.y])};
        });
        assert(Math.hypot(points.from[0]-points.center[0],points.from[1]-points.center[1])<.001);
        const [ax,ay]=points.from,[bx,by]=points.to,dx=bx-ax,dy=by-ay,length=Math.hypot(dx,dy);
        for(const [x,y] of points.dots)assert(Math.abs(dx*(ay-y)-(ax-x)*dy)/length<.001);
        if(time===3000)assert.equal(state.scenes[0].states.reservoir.rotation,70);
      }
      assert.notEqual(hash(await page.screenshot()),hash(before));
      await page.evaluate(()=>film.seek(0));assert.equal(hash(await page.screenshot()),hash(before));
    });
    const detached=copy(plan);detached.scenes[0].actors.find(a=>a.id==='flow_path').initial.rotation=15;
    assert.throws(()=>validatePlan(detached),/connector rotation/);
    const badMaterial=copy(plan);badMaterial.scenes[0].actors.find(a=>a.id==='path_material').initial.rotation=15;
    assert.throws(()=>validatePlan(badMaterial),/zero rotation/);
  }
});
test('SVG disguised as a local PNG fails the browser asset boundary',async()=>{
  const plan=fixturePlan(),assets=await resolveAssets(plan,{assetRoot:temp});
  assets.get('/test-assets/pixel.png').bytes=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>');
  const local=await createServer(plan,assets),context=await browser.newContext({viewport:plan.canvas});
  try{const page=await context.newPage();await page.goto(local.origin);await assert.rejects(page.evaluate(()=>start()),/no SVG fallback/);assert.equal(await page.locator('svg').count(),0);}finally{await context.close();await new Promise(resolve=>local.server.close(resolve));}
});
module.exports={fixturePlan};
