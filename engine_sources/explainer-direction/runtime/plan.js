/* Independent execution boundary. The capture tool additionally calls frozen Python validate_plan. */
(function (root) {
  'use strict';
  const ASPECTS = {'16:9': [1920,1080], '9:16': [1080,1920], '1:1': [1080,1080]};
  const COMMON = ['opacity','reveal','scale','rotation','highlight','x','y'];
  const KINDS = {text:['text'],number:['value'],shape:['draw','fill','variant'],bar:['value','fill'],axis:['draw'],connector:['draw'],selector:['selection'],particles:['flow','fill'],panel:['fill'],image:[],group:[]};
  const VERBS = {reveal:['opacity','reveal'],hide:['opacity','reveal'],draw:['draw'],fill:['fill'],grow:['fill','value','scale'],update:[...COMMON,'text','value','draw','fill','variant','selection','flow'],select:['selection','highlight'],highlight:['highlight','opacity'],connect:['draw','opacity'],move:['x','y'],rotate:['rotation'],reframe:['x','y','scale','rotation'],morph:['variant','fill','scale'],settle:['x','y','scale','rotation','opacity','highlight'],hold:[]};
  const EASINGS = ['linear','ease_in','ease_out','ease_in_out','step'];
  const SPATIAL = {above:['y',false],below:['y',true],left_of:['x',false],right_of:['x',true]};
  const ROLES = ['background','surface','text','muted','primary','secondary','accent','positive','negative'];
  const LICENSES = ['CC0-1.0','CC-BY-4.0','CC-BY-SA-4.0','MIT','Apache-2.0','OFL-1.1','public-domain','owned','permission'];
  const UNITS = {'1':['ratio',1,0],'%':['ratio',.01,0],count:['count',1,0],ms:['time',.001,0],s:['time',1,0],min:['time',60,0],h:['time',3600,0],mm:['length',.001,0],cm:['length',.01,0],m:['length',1,0],km:['length',1000,0],g:['mass',.001,0],kg:['mass',1,0],K:['temperature',1,0],degC:['temperature',1,273.15],USD:['currency:USD',1,0],EUR:['currency:EUR',1,0],J:['energy',1,0],kJ:['energy',1000,0],W:['power',1,0],kW:['power',1000,0],Pa:['pressure',1,0],kPa:['pressure',1000,0],mL:['volume',.001,0],L:['volume',1,0],'m/s':['speed',1,0],'km/h':['speed',1/3.6,0],byte:['data',1,0],KB:['data',1000,0],MB:['data',1e6,0],GB:['data',1e9,0],Hz:['frequency',1,0],kHz:['frequency',1000,0]};
  class PlanError extends Error { constructor(message, path='$') { super(`${path}: ${message}`); this.name='PlanError'; this.path=path; } }
  const fail = (s,p) => {throw new PlanError(s,p);};
  const assert = (ok,s,p) => {if (!ok) fail(s,p);};
  const equal = (a,b) => { if (a === b) return true; if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return false; const ka=Object.keys(a).sort(),kb=Object.keys(b).sort(); return equalKeys(ka,kb) && ka.every(k=>equal(a[k],b[k])); };
  const equalKeys = (a,b) => a.length===b.length && a.every((v,i)=>v===b[i]);
  const finite = v => typeof v==='number' && Number.isFinite(v) && Math.abs(v)<=Number.MAX_SAFE_INTEGER;
  function obj(v, required, optional=[], path='$') { assert(v && typeof v==='object' && !Array.isArray(v),'expected object',path); assert(required.every(k=>Object.hasOwn(v,k)),'missing required fields',path); assert(Object.keys(v).every(k=>required.includes(k)||optional.includes(k)),'unknown fields',path); }
  function list(v,p,nonempty=false) {assert(Array.isArray(v) && (!nonempty || v.length),'expected array',p);}
  function str(v,p) {assert(typeof v==='string' && v.trim().length>0 && v.length<=12000,'expected nonempty text',p);}
  function id(v,p) {assert(typeof v==='string' && /^[A-Za-z][A-Za-z0-9_.:-]{0,95}$/.test(v),'invalid stable id',p);}
  function ids(v,p) {list(v,p); v.forEach(x=>id(x,p));assert(new Set(v).size===v.length,'duplicate ids',p);}
  function one(v,choices,p) {assert(choices.includes(v),`unsupported ${String(v)}`,p);}
  function num(v,min,max,p) {assert(finite(v) && v>=min && v<=max,'number outside admitted range',p);}
  function localAsset(v,ext,p) {str(v,p);assert(v===v.trim() && !/[\\%?#\x00-\x1f\x7f]/u.test(v) && !/^[a-z][a-z0-9+.-]*:/i.test(v) && !v.startsWith('//') && !v.split('/').includes('..') && ext.test(v),'only local declared assets permitted',p);}
  function source(s,p) {obj(s,['id','uri','locator','license','commercial_use'],[],p);id(s.id,p);str(s.uri,p);str(s.locator,p);one(s.license,LICENSES,p);assert(s.commercial_use===true,'commercial use must be declared',p);if(s.license==='permission') assert(!/^(unknown|none|n\/a)$/i.test(s.locator.trim()),'permission needs actual locator',p);}
  function acyclic(graph,p) {const active=new Set(),done=new Set();function visit(k){assert(!active.has(k),'cyclic dependency',p);if(done.has(k))return;active.add(k);for(const d of graph[k]||[]) {assert(Object.hasOwn(graph,d),'missing graph reference',p);visit(d);}active.delete(k);done.add(k);}Object.keys(graph).forEach(visit);}
  function index(v,p) {list(v,p);const out=Object.create(null);for(const x of v){id(x.id,p);assert(!Object.hasOwn(out,x.id),'duplicate id',p);Object.defineProperty(out,x.id,{value:x,enumerable:true});}return out;}
  function refs(v,map,p) {ids(v,p);v.forEach(k=>assert(Object.hasOwn(map,k),'unknown reference '+k,p));}
  function meaningBindings(graph,scene,evidence,p) {
    obj(graph,['entities','facts','quantities'],[],p+'.meaning_graph');
    list(graph.entities,p,true);list(graph.facts,p,true);
    const entities=index(graph.entities,p),facts=index(graph.facts,p),actors=index(scene.actors,p);
    const physical=['system','place','device','organism'],carriers=['material','energy','signal'];
    const entityClaims=Object.fromEntries(graph.entities.map(e=>[e.id,new Set(e.evidence_ids)]));
    for(const e of graph.entities) {
      obj(e,['id','kind','label','evidence_ids'],[],p);one(e.kind,[...physical,...carriers,'process','concept'],p);str(e.label,p);
      refs(e.evidence_ids,evidence,p);assert(e.evidence_ids.length,'entity needs provenance',p);
    }
    for(const f of graph.facts) {
      obj(f,['id','kind','from','to','evidence_ids'],['carrier','via','process'],p);
      one(f.kind,[...Object.keys(SPATIAL),'flows_to','causes','contains','connected_to','produces','stores','powers','aligns_with'],p);
      refs([f.from,f.to],entities,p);refs(f.evidence_ids,evidence,p);assert(f.from!==f.to&&f.evidence_ids.length,'fact needs distinct endpoints and provenance',p);
      if(SPATIAL[f.kind]||f.kind==='flows_to')assert([f.from,f.to].every(e=>physical.includes(entities[e].kind)),'physical fact needs physical endpoints',p);
      if(f.kind==='flows_to') {
        assert(carriers.includes(entities[f.carrier]?.kind)&&![f.from,f.to].includes(f.carrier),'flow needs a separate admitted carrier',p);
        if(f.via!==undefined)assert(physical.includes(entities[f.via]?.kind)&&![f.from,f.to].includes(f.via),'flow intermediate must be physical and distinct',p);
        if(f.process!==undefined)assert(entities[f.process]?.kind==='process','transport activity needs admitted process',p);
      } else assert(f.carrier===undefined&&f.via===undefined&&f.process===undefined,'only flows_to admits carrier/via/process',p);
      if(f.kind==='causes')assert(['process','concept'].includes(entities[f.to].kind),'causation needs process/outcome, not carrier creation',p);
      if(f.kind==='produces')assert([...physical,'process'].includes(entities[f.from].kind),'producer must be physical or a process',p);
      if(['contains','connected_to','stores'].includes(f.kind))assert(physical.includes(entities[f.from].kind),'contain/connect/store must start physical',p);
      if(f.kind==='connected_to')assert(physical.includes(entities[f.to].kind),'connected endpoint must be physical',p);
      if(f.kind==='stores')assert(carriers.includes(entities[f.to].kind),'stored entity must be carrier',p);
      if(f.kind==='powers')assert(entities[f.from].kind==='energy'&&[...physical,'process'].includes(entities[f.to].kind),'energy powers physical device/system or process',p);
      if(f.kind==='aligns_with')assert(physical.includes(entities[f.from].kind)&&[...physical,...carriers,'concept'].includes(entities[f.to].kind),'orientation needs physical subject and physical entity, field/carrier or direction',p);
      for(const key of ['from','to','carrier','via','process'])if(f[key]!==undefined)for(const claim of f.evidence_ids)entityClaims[f[key]].add(claim);
    }
    const quantities=Object.create(null);
    list(graph.quantities,p);
    for(const q of graph.quantities) {
      obj(q,['claim_id','subject'],[],p);refs([q.subject],entities,p);refs([q.claim_id],evidence,p);
      assert(evidence[q.claim_id].quantity&&entities[q.subject].evidence_ids.includes(q.claim_id)&&!Object.hasOwn(quantities,q.claim_id),'invalid quantity subject',p);
      quantities[q.claim_id]=q.subject;
    }
    const physicalActors=Object.create(null);
    for(const a of scene.actors) {
      obj(a.meaning_binding,[],['entity','fact'],p);
      const keys=Object.keys(a.meaning_binding);assert(keys.length===1,'actor needs exactly one meaning binding',p);
      const key=keys[0],value=a.meaning_binding[key],record=(key==='entity'?entities:facts)[value];
      assert(record&&a.evidence_ids.length&&a.evidence_ids.every(e=>key==='entity'?entityClaims[value].has(e):record.evidence_ids.includes(e)),'actor claims differ from bound meaning',p);
      if(['shape','image','group'].includes(a.kind)&&key==='entity')(physicalActors[value]||=[]).push(a.id);
      if(['number','bar','axis'].includes(a.kind))assert((a.kind==='axis'?a.evidence_ids:[a.value_binding]).some(e=>quantities[e]===a.meaning_binding.entity),'measured actor depicts the wrong entity',p);
      if(a.kind==='connector')assert(key==='fact'&&['flows_to','causes','connected_to','produces','stores','powers'].includes(record.kind),'connector needs a link/process fact',p);
    }
    for(const a of scene.actors) {
      if(a.kind==='connector') {
        const fact=facts[a.meaning_binding.fact],left=actors[a.payload.from].meaning_binding.entity,right=actors[a.payload.to].meaning_binding.entity;
        if(fact.kind==='flows_to') {
          const route=[fact.from,...(fact.via?[fact.via]:[]),fact.to];
          assert(route.slice(1).some((target,i)=>(left===route[i]&&right===target)||(right===route[i]&&left===target)),'route does not connect adjacent physical entities',p);
        } else assert(left&&right&&left!==right&&[fact.from,fact.to].includes(left)&&[fact.from,fact.to].includes(right),'link endpoints contradict the fact',p);
      }
      if(a.kind==='particles'&&a.payload.path) {
        const route=actors[a.payload.path.connector],fact=facts[route.meaning_binding.fact];
        assert(fact?.kind==='flows_to'&&a.meaning_binding.entity===fact.carrier,'particle depicts the wrong carrier',p);
        const itinerary=[fact.from,...(fact.via?[fact.via]:[]),fact.to],left=actors[route.payload.from].meaning_binding.entity,right=actors[route.payload.to].meaning_binding.entity;
        const forward=itinerary.slice(1).some((target,i)=>left===itinerary[i]&&right===target);
        assert(a.payload.path.direction===(forward?'forward':'reverse'),'particle flow contradicts the process direction',p);
      }
    }
    for(const r of scene.relations)if(SPATIAL[r.kind]||r.kind==='flows_to'||r.kind==='aligns_with') {
      const left=actors[r.from].meaning_binding.entity,right=actors[r.to].meaning_binding.entity;
      assert(graph.facts.some(f=>f.kind===r.kind&&f.from===left&&f.to===right&&r.evidence_ids.every(e=>f.evidence_ids.includes(e))),'relation lacks an exact meaning fact',p);
    }
    for(const f of graph.facts)if(SPATIAL[f.kind]&&physicalActors[f.from]&&physicalActors[f.to])
      assert(scene.relations.some(r=>r.kind===f.kind&&physicalActors[f.from].includes(r.from)&&physicalActors[f.to].includes(r.to)),'physical entities lost a required spatial fact',p);
  }
  function stateValue(prop,v,actor,p) {if(['text'].includes(prop)) str(v,p);else if(prop==='variant')one(v,['circle','rect','diamond','hexagon'],p);else if(prop==='selection'){num(v,0,actor.payload.options.length-1,p);assert(Number.isInteger(v),'selection must be integral',p);}else if(prop==='value') {num(v,-Number.MAX_SAFE_INTEGER,Number.MAX_SAFE_INTEGER,p);if(actor.kind==='bar')num(v,...actor.payload.domain,p);}else if(prop==='scale')num(v,.05,8,p);else if(prop==='rotation')num(v,-3600,3600,p);else if(prop==='x'||prop==='y')num(v,-Number.MAX_SAFE_INTEGER,Number.MAX_SAFE_INTEGER,p);else num(v,0,1,p);}
  function quantity(v,unit,e) {const a=UNITS[e.quantity?.unit],b=UNITS[unit];if(!a||!b||a[0]!==b[0])return false;if(e.quantity.unit===unit)return v===e.quantity.value;return Math.abs(v-((e.quantity.value*a[1]+a[2]-b[2])/b[1]))<=1e-9;}
  function literal(v) {
    const match=String(v).match(/^([+-]?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/);
    if(!match)return null;
    let digits=(match[2]+(match[3]||'')).replace(/^0+/,''),exponent=Number(match[4]||0)-(match[3]||'').length;
    if(!digits)return '0';
    while(digits.endsWith('0')){digits=digits.slice(0,-1);exponent++;}
    return (match[1]==='-'?'-':'')+digits+'e'+exponent;
  }
  function textBinding(text,a,ev,claims,p) {
    const bound=a.evidence_ids.filter(k=>claims.includes(k));
    assert(a.payload.purpose==='label'||bound.length,'fact-bearing text needs evidence',p);
    const clean=text.replaceAll(',','').replaceAll('\u2212','-');
    const pattern='(?<![\\w.])[-+]?\\d+(?:\\.\\d+)?(?:[eE][-+]?\\d+)?';
    const numbers=[...clean.matchAll(new RegExp(pattern+'(?!\\d|\\.\\d)','g'))].map(m=>m[0]);
    const aliases={'°C':'degC','°F':'degF','$':'USD','€':'EUR'};
    const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    const units=Object.keys({...UNITS,...aliases}).filter(x=>x!=='1').sort((a,b)=>b.length-a.length).map(escape).join('|');
    const labelled=[...clean.matchAll(new RegExp('('+pattern+')\\s*('+units+')(?!\\w)','g'))].map(m=>[m[1],aliases[m[2]]||m[2]]);
    labelled.push(...[...clean.matchAll(new RegExp('([$€])\\s*('+pattern+')(?!\\d|\\.\\d)','g'))].map(m=>[m[2],aliases[m[1]]]));
    if(a.payload.numeric_role==='ordinal'){assert(a.payload.purpose==='label'&&!labelled.length&&numbers.every(n=>/^\+?\d+$/.test(n)&&Number(n)>0),'ordinal is not a measured claim',p);return;}
    const quantities=bound.map(k=>ev[k].quantity).filter(Boolean);
    numbers.forEach(n=>assert(quantities.some(q=>literal(n)===literal(q.value)),'unbound numeric text',p));
    labelled.forEach(([n,u])=>assert(quantities.some(q=>q.unit===u&&literal(n)===literal(q.value)),'numeric text unit mismatch',p));
  }
  function payload(a,p) {
    const x=a.payload;
    const keys={text:[['text','purpose'],['max_lines','numeric_role']],number:[['unit','dimension'],['decimals']],shape:[['shape'],['aspect_ratio']],bar:[['domain','unit','dimension','orientation'],[]],axis:[['domain','unit','dimension','orientation'],['ticks']],connector:[['from','to','arrow'],['routing']],selector:[['options'],[]],particles:[['count','arrangement','illustrative'],['path']],panel:[[],[]],image:[['src','mime','fit','source'],[]],group:[['children'],[]]}[a.kind];
    obj(x,...keys,p);
    if(['number','bar','axis'].includes(a.kind)){one(x.unit,Object.keys(UNITS),p);assert(x.dimension===UNITS[x.unit][0],'incompatible dimension/unit',p);}
    if(['bar','axis'].includes(a.kind)){list(x.domain,p);assert(x.domain.length===2 && x.domain.every(finite)&&x.domain[1]>x.domain[0],'invalid domain',p);one(x.orientation,['horizontal','vertical'],p);}
    if(a.kind==='number'&&x.decimals!==undefined){num(x.decimals,0,6,p);assert(Number.isInteger(x.decimals),'decimals integral',p);}
    if(a.kind==='text'){str(x.text,p);one(x.purpose,['label','headline','annotation','conclusion','caption'],p);if(x.max_lines!==undefined){num(x.max_lines,1,8,p);assert(Number.isInteger(x.max_lines),'line count integral',p);}if(x.numeric_role!==undefined)one(x.numeric_role,['quantity','ordinal'],p);}
    if(a.kind==='shape'){one(x.shape,['circle','rect','diamond','hexagon'],p);if(x.aspect_ratio!==undefined)num(x.aspect_ratio,.1,10,p);}
    if(a.kind==='selector'){list(x.options,p,true);assert(x.options.length<=64&&new Set(x.options).size===x.options.length,'invalid options',p);x.options.forEach(v=>str(v,p));}
    if(a.kind==='axis'&&x.ticks!==undefined){num(x.ticks,2,12,p);assert(Number.isInteger(x.ticks),'ticks integral',p);}
    if(a.kind==='connector'){id(x.from,p);id(x.to,p);assert(x.from!==x.to && typeof x.arrow==='boolean','invalid connector',p);if(x.routing!==undefined)one(x.routing,['direct','elbow'],p);}
    if(a.kind==='particles'){num(x.count,1,64,p);assert(Number.isInteger(x.count)&&x.illustrative===true,'particles must be illustrative',p);one(x.arrangement,['grid','stream','radial'],p);}
    if(a.kind==='particles'&&x.path!==undefined){obj(x.path,['connector','direction'],[],p);id(x.path.connector,p);one(x.path.direction,['forward','reverse'],p);assert(x.arrangement==='stream','path-bound particles must use stream arrangement',p);}
    if(a.kind==='image'){localAsset(x.src,/\.(png|jpe?g|webp)$/i,p);one(x.mime,['image/png','image/jpeg','image/webp'],p);assert(({png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg',webp:'image/webp'})[x.src.split('.').at(-1).toLowerCase()]===x.mime,'mime mismatch',p);one(x.fit,['contain','cover'],p);source(x.source,p);}
    if(a.kind==='group')ids(x.children,p);
  }
  function validatePlan(input) {
    // Round-trip only after rejecting non-JSON values (including nonfinite numbers).
    function safe(v,p,depth=0){assert(depth<=50,'JSON nesting limit',p);if(typeof v==='string'){assert(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(v),'invalid Unicode scalar',p);return;}if(typeof v==='number'){assert(finite(v),'nonfinite/unsafe number',p);return;}if(v===null||typeof v==='boolean')return;assert(v&&typeof v==='object'&&(Array.isArray(v)||Object.getPrototypeOf(v)===Object.prototype),'non-JSON value',p);Object.entries(v).forEach(([k,x])=>safe(x,`${p}.${k}`,depth+1));}
    safe(input,'$');const plan=JSON.parse(JSON.stringify(input));
    obj(plan,['schema','film_id','title','aspect','canvas','output','duration_ms','style','evidence','scenes','provenance','direction'],['meaning_graph']);
    assert(plan.schema==='explainer-direction.plan/v1','unsupported schema');id(plan.film_id,'$.film_id');str(plan.title,'$.title');one(plan.aspect,Object.keys(ASPECTS),'$.aspect');obj(plan.canvas,['width','height']);assert(equal([plan.canvas.width,plan.canvas.height],ASPECTS[plan.aspect]),'native canvas mismatch');obj(plan.output,['fps','format','background']);num(plan.output.fps,1,60,'$.output.fps');assert(Number.isInteger(plan.output.fps)&&plan.output.format==='mp4'&&/^#[\da-f]{6}$/i.test(plan.output.background),'invalid output');num(plan.duration_ms,1,Number.MAX_SAFE_INTEGER,'$.duration_ms');
    const st=plan.style;obj(st,['family','palette','typography','strokes','materials','motion']);one(st.family,['neon','candy','forest','ocean','ember'],'$.style');obj(st.palette,ROLES);ROLES.forEach(r=>assert(/^#[\da-f]{6}$/i.test(st.palette[r]),'invalid palette'));obj(st.typography,['font_family','font_url','font_license','headline_size','body_size','label_size']);str(st.typography.font_family,'$.style');localAsset(st.typography.font_url,/\.(woff2?|ttf|otf)$/i,'$.style.font_url');one(st.typography.font_license,['OFL-1.1','Apache-2.0'],'$.style');num(st.typography.headline_size,28,120,'$.style');num(st.typography.body_size,20,72,'$.style');num(st.typography.label_size,16,64,'$.style');obj(st.strokes,['width','corner_radius']);num(st.strokes.width,.5,12,'$.style');num(st.strokes.corner_radius,0,40,'$.style');obj(st.materials,['surface']);one(st.materials.surface,['flat','outlined'],'$.style');obj(st.motion,['character','easing']);one(st.motion.character,['precise','calm','energetic'],'$.style');one(st.motion.easing,EASINGS,'$.style');
    const prov=plan.provenance;obj(prov,['mode','creative_authority','status','direction_id','source'],['model','p8','test_fixture']);source(prov.source,'$.provenance');id(prov.direction_id,'$.provenance');assert(prov.creative_authority==='P8','P8 required');one(prov.mode,['development','p8_bound'],'$.provenance');assert(prov.status===(prov.mode==='development'?'DEVELOPMENT_PREFLIGHT':'P8_SEMANTIC_BOUND'),'authority mode mismatch');if(prov.test_fixture!==undefined)assert(typeof prov.test_fixture==='boolean','fixture flag boolean');if(prov.mode==='development')assert(!prov.p8,'development cannot claim P8 hashes');else{obj(prov.p8,['state_hash','board_hash']);assert(!prov.test_fixture&&Object.values(prov.p8).every(x=>/^[a-f0-9]{64}$/.test(x)),'invalid P8 provenance');}if(prov.model){obj(prov.model,['provider','model'],['request_id']);Object.values(prov.model).forEach(x=>str(x,'$.provenance.model'));}
    obj(plan.direction,['authority','status','score_sha256','timing']);assert(plan.direction.authority==='P8'&&plan.direction.status===prov.status&&/^[a-f0-9]{64}$/.test(plan.direction.score_sha256),'invalid direction');one(plan.direction.timing,['provisional','authored','aligned'],'$.direction');
    list(plan.evidence,'$.evidence',true);const ev=index(plan.evidence,'$.evidence'),sources=Object.create(null);
    function register(s){source(s,'$.source');if(Object.hasOwn(sources,s.id))assert(equal(s,sources[s.id]),'source identity provenance changed');else sources[s.id]=s;}
    register(prov.source);
    for(const e of plan.evidence){obj(e,['id','claim','status','source'],['quantity','comparison']);str(e.claim,'$.evidence');one(e.status,['supported','uncertain','illustrative'],'$.evidence');register(e.source);if(e.quantity){obj(e.quantity,['value','unit','dimension']);assert(finite(e.quantity.value)&&UNITS[e.quantity.unit]?.[0]===e.quantity.dimension,'invalid quantity');if(e.quantity.dimension==='count')assert(Number.isInteger(e.quantity.value)&&e.quantity.value>=0,'invalid count');}if(e.comparison){obj(e.comparison,['group','conditions']);id(e.comparison.group,'$.comparison');assert(e.comparison.conditions&&typeof e.comparison.conditions==='object'&&!Array.isArray(e.comparison.conditions)&&Object.keys(e.comparison.conditions).length,'comparison context required');}}
    list(plan.scenes,'$.scenes',true);index(plan.scenes,'$.scenes');let end=0;const history=Object.create(null),allEvents=new Set();
    for(const scene of plan.scenes){const p=`$.scenes.${scene.id}`;obj(scene,['id','section_id','intent','claim_ids','narration','start_ms','end_ms','actors','relations','events','tracks','transition','composition','constraints'],['motif'],p);id(scene.section_id,p);str(scene.intent,p);str(scene.narration,p);assert(finite(scene.start_ms)&&finite(scene.end_ms),'invalid scene interval',p);refs(scene.claim_ids,ev,p);textBinding(scene.narration,{evidence_ids:scene.claim_ids,payload:{purpose:'caption'}},ev,scene.claim_ids,p);assert(scene.start_ms===end&&scene.end_ms>scene.start_ms,'noncontiguous scenes',p);end=scene.end_ms;list(scene.actors,p,true);const actors=index(scene.actors,p),events=index(scene.events,p),parents=Object.create(null),groupGraph=Object.create(null),layoutGraph=Object.create(null);
      obj(scene.composition,['flow','density'],['focus']);one(scene.composition.flow,['auto','row','column','radial','stack','plot'],p);one(scene.composition.density,['open','balanced','dense'],p);if(scene.composition.focus)refs([scene.composition.focus],actors,p);list(scene.constraints,p);scene.constraints.forEach(x=>str(x,p));if(scene.motif!==undefined)str(scene.motif,p);
      for(const a of scene.actors){obj(a,['id','identity','kind','role','label','meaning','evidence_ids','geometry','payload','initial','retained','layout'],['value_binding','meaning_binding'],p);assert(a.id===a.identity,'unstable identity',p);one(a.kind,Object.keys(KINDS),p);one(a.role,ROLES,p);str(a.label,p);str(a.meaning,p);refs(a.evidence_ids,ev,p);assert(a.evidence_ids.every(e=>scene.claim_ids.includes(e)),'actor claim outside scene',p);payload(a,p);textBinding(a.label,{evidence_ids:a.evidence_ids,payload:{purpose:'label',...(a.payload.numeric_role==='ordinal'?{numeric_role:'ordinal'}:{})}},ev,scene.claim_ids,p);if(a.kind==='text'){textBinding(a.payload.text,a,ev,scene.claim_ids,p);textBinding(a.initial.text,a,ev,scene.claim_ids,p);}if(a.kind==='selector')a.payload.options.forEach(t=>textBinding(t,{evidence_ids:a.evidence_ids,payload:{purpose:'label'}},ev,scene.claim_ids,p));if(['number','bar','axis'].includes(a.kind))assert(a.evidence_ids.length&&a.evidence_ids.every(k=>ev[k].quantity?.dimension===a.payload.dimension),'typed data evidence required',p);if(a.kind==='image')register(a.payload.source);
        const g=a.geometry;obj(g,['x','y','width','height'],['points','font_size','line_height','lines','anchors'],p);['x','y','width','height'].forEach(k=>num(g[k],k==='width'||k==='height'?0:-Number.MAX_SAFE_INTEGER,Number.MAX_SAFE_INTEGER,p));if(g.points){list(g.points,p,true);assert(g.points.length>=2,'insufficient points',p);g.points.forEach(x=>{obj(x,['x','y']);assert(finite(x.x)&&finite(x.y),'invalid point',p);});}if(['axis','connector'].includes(a.kind))assert(g.points,'line points required',p);if(['text','number'].includes(a.kind)){assert(g.font_size>0&&g.line_height>0&&Array.isArray(g.lines),'fitted text geometry required',p);}for(const k of ['font_size','line_height'])if(g[k]!==undefined)num(g[k],Number.MIN_VALUE,Number.MAX_SAFE_INTEGER,p);if(g.lines){list(g.lines,p);g.lines.forEach(x=>str(x,p));}if(g.anchors){obj(g.anchors,['home','focus','context','start','end']);for(const x of Object.values(g.anchors)){obj(x,['x','y']);assert(finite(x.x)&&finite(x.y),'invalid anchor',p);}}
        const required=['opacity','x','y',...({text:['text'],number:['value'],bar:['value'],selector:['selection'],shape:['variant']}[a.kind]||[])];obj(a.initial,required,[...COMMON,...KINDS[a.kind]],p);Object.entries(a.initial).forEach(([k,v])=>stateValue(k,v,a,p));obj(a.layout,['anchor'],['rank','relative_to','arrangement'],p);one(a.layout.anchor,['primary','secondary','context','caption','background','start','end','center'],p);if(a.layout.rank!==undefined){num(a.layout.rank,0,100,p);assert(Number.isInteger(a.layout.rank),'rank integral',p);}if(a.layout.arrangement!==undefined)one(a.layout.arrangement,['auto','row','column','radial','stack','plot'],p);layoutGraph[a.id]=a.layout.relative_to?[a.layout.relative_to]:[];
        if(a.kind==='connector'){refs([a.payload.from,a.payload.to],actors,p);assert(a.id!==a.payload.from&&a.id!==a.payload.to,'connector cannot connect itself',p);}groupGraph[a.id]=a.kind==='group'?a.payload.children:[];refs(groupGraph[a.id],actors,p);for(const c of groupGraph[a.id]){assert(!parents[c],'multiple group parents',p);parents[c]=a.id;}
        if(['number','bar'].includes(a.kind)){assert(a.evidence_ids.includes(a.value_binding)&&ev[a.value_binding]?.quantity&&quantity(a.initial.value,a.payload.unit,ev[a.value_binding]),'unbound value',p);if(ev[a.value_binding]?.status==='illustrative')assert(/illustrative/i.test(a.meaning),'illustrative value needs declaration',p);}else assert(a.value_binding===undefined,'unexpected numeric binding',p);
        const old=history[a.id];assert(a.retained===Boolean(old),'invalid retained flag',p);if(old){for(const k of ['id','kind','role','label','meaning','evidence_ids','payload','meaning_binding'])assert(equal(a[k],old.actor[k]),'retained identity changed',p);assert(equal(Object.fromEntries(Object.entries(a.initial).filter(([k])=>k!=='x'&&k!=='y')),old.state),'retained terminal state discontinuity',p);}else if(a.kind==='shape')assert(a.initial.variant===a.payload.shape,'initial variant mismatch',p);
      }
      acyclic(groupGraph,p);acyclic(layoutGraph,p);
      for(const a of scene.actors)if(a.kind==='particles'&&a.payload.path){
        const binding=a.payload.path;refs([binding.connector],actors,p);
        const route=actors[binding.connector];assert(route.kind==='connector'&&a.id!==route.payload.from&&a.id!==route.payload.to,'path-bound particles need a distinct connector, not their own endpoint',p);
        assert(Object.hasOwn(a.initial,'flow')&&a.initial.x===a.geometry.x&&a.initial.y===a.geometry.y&&(a.initial.scale??1)===1&&(a.initial.rotation??0)===0,'path-bound particles need home/unit scale/zero rotation and initialized flow',p);
        assert(!scene.tracks.some(t=>t.actor_id===a.id&&['x','y','scale','rotation'].includes(t.property)),'path-bound particle transforms are driven by endpoints or groups',p);
        assert(!scene.tracks.some(t=>t.actor_id===a.id&&t.property==='flow'&&t.to<=t.from),'path-bound flow must advance in its declared process direction',p);
      }
      list(scene.relations,p);index(scene.relations,p);for(const r of scene.relations){obj(r,['id','kind','from','to','evidence_ids']);one(r.kind,['comparison','causes','contains','sequence','connected_to','labels','supports','flows_to','produces','stores','powers','aligns_with',...Object.keys(SPATIAL)],p);refs([r.from,r.to],actors,p);refs(r.evidence_ids,ev,p);assert(r.evidence_ids.every(e=>scene.claim_ids.includes(e)),'relation claim outside scene',p);if(r.kind==='comparison'){const a=actors[r.from],b=actors[r.to];assert(['number','bar'].includes(a.kind)&&['number','bar'].includes(b.kind)&&a.payload.dimension===b.payload.dimension,'incompatible comparison',p);const claims=[...a.evidence_ids,...b.evidence_ids].map(e=>ev[e]);assert(claims.every(e=>e.quantity&&e.comparison&&equal(e.comparison,claims[0].comparison)&&(e.status==='illustrative')===(claims[0].status==='illustrative')),'incompatible comparison context',p);}}
      if(plan.meaning_graph!==undefined)meaningBindings(plan.meaning_graph,scene,ev,p);
      const spatialMembers=new Set(),physicalGraphs={x:Object.create(null),y:Object.create(null)},scopes={...parents};
      for(const r of scene.relations)if(r.kind==='contains'&&!scopes[r.to])scopes[r.to]=r.from;
      for(const r of scene.relations)if(SPATIAL[r.kind]){
        const [axis,reverse]=SPATIAL[r.kind],[first,second]=reverse?[r.to,r.from]:[r.from,r.to],a=actors[first],b=actors[second],extent=axis==='x'?'width':'height';
        assert(scopes[first]===scopes[second]&&r.evidence_ids.length>0,'physical ordering needs a shared layout scope and evidence',p);
        assert(a.initial[axis]+a.geometry[extent]/2<b.initial[axis]+b.geometry[extent]/2,'compiled layout reverses physical ordering',p);
        (physicalGraphs[axis][first]||=[]);(physicalGraphs[axis][second]||=[]).push(first);spatialMembers.add(first);spatialMembers.add(second);
      }
      for(const g of Object.values(physicalGraphs))acyclic(g,p);
      const orderedGroups=new Set();
      for(const aid of spatialMembers)for(let parent=parents[aid];parent;parent=parents[parent])orderedGroups.add(parent);
      for(const aid of orderedGroups)assert((actors[aid].initial.rotation??0)===0&&!scene.tracks.some(t=>t.actor_id===aid&&t.property==='rotation'&&(t.from!==0||t.to!==0)),'rotation of a physical ordering group is unsupported',p);
      for(const a of scene.actors)if(a.kind==='connector')assert((a.initial.rotation??0)===0&&!scene.tracks.some(t=>t.actor_id===a.id&&t.property==='rotation'),'attached connector rotation is driven by endpoints or groups',p);
      for(const aid of spatialMembers)assert(actors[aid].kind!=='connector'&&actors[aid].layout.anchor!=='background','physical ordering requires content entities',p);
      for(const t of scene.tracks)assert(!spatialMembers.has(t.actor_id)||!['x','y'].includes(t.property),'move a shared physical group, not constrained endpoints',p);
      for(const a of scene.actors)if(a.payload.numeric_role==='ordinal')assert(scene.relations.some(r=>r.kind==='sequence'&&(r.from===a.id||r.to===a.id)),'ordinal requires sequence relation',p);
      const graph=Object.create(null),writes=Object.create(null),byEvent=Object.create(null);for(const e of scene.events){obj(e,['id','verb','targets','start_ms','end_ms','dependencies','claim_ids','rationale']);assert(!allEvents.has(e.id),'event ids must be film unique',p);allEvents.add(e.id);one(e.verb,Object.keys(VERBS),p);refs(e.targets,actors,p);refs(e.dependencies,events,p);refs(e.claim_ids,ev,p);assert(e.claim_ids.every(x=>scene.claim_ids.includes(x)),'event claim outside scene',p);str(e.rationale,p);assert(scene.start_ms<=e.start_ms&&e.start_ms<=e.end_ms&&e.end_ms<=scene.end_ms,'event outside scene',p);assert(e.verb==='hold'?e.end_ms>e.start_ms:e.targets.length>0,'invalid semantic event',p);assert(e.dependencies.every(d=>events[d].end_ms<=e.start_ms),'dependency incomplete',p);graph[e.id]=e.dependencies;byEvent[e.id]=[];}acyclic(graph,p);
      list(scene.tracks,p);for(const t of scene.tracks){obj(t,['event_id','actor_id','property','from','to','start_ms','end_ms','easing','verb','rationale','claim_ids'],[],p);const a=actors[t.actor_id],e=events[t.event_id];assert(a&&e,'unknown track reference',p);assert(a.kind!=='connector'||!['x','y','scale'].includes(t.property),'attached connector transforms are driven by endpoints or groups',p);assert(Object.hasOwn(a.initial,t.property)&&VERBS[e.verb].includes(t.property),'unsupported property or absent initial',p);stateValue(t.property,t.from,a,p);stateValue(t.property,t.to,a,p);one(t.easing,EASINGS,p);assert(t.start_ms===e.start_ms&&t.end_ms===e.end_ms&&t.verb===e.verb&&t.rationale===e.rationale&&equal(t.claim_ids,e.claim_ids)&&e.targets.includes(a.id),'unlinked semantic track',p);if(['text','variant','selection'].includes(t.property))assert(t.easing==='step','discrete tracks must step',p);if(t.property==='value')assert(t.claim_ids.some(k=>a.evidence_ids.includes(k)&&ev[k]?.quantity&&quantity(t.to,a.payload.unit,ev[k])),'unbound numeric target',p);if(t.property==='text')textBinding(t.to,a,ev,t.claim_ids,p);if(t.property==='selection')textBinding(a.payload.options[t.to],{evidence_ids:a.evidence_ids,payload:{purpose:'label'}},ev,t.claim_ids,p);const key=a.id+'|'+t.property;(writes[key]||= []).push(t);byEvent[e.id].push(t);}
      const terminals={};for(const a of scene.actors)terminals[a.id]={...a.initial};for(const ts of Object.values(writes)){ts.sort((a,b)=>a.start_ms-b.start_ms||a.end_ms-b.end_ms);let lastEnd=-1,lastStart=-1,current=actors[ts[0].actor_id].initial[ts[0].property];for(const t of ts){assert(t.start_ms>=lastEnd&&t.start_ms!==lastStart&&equal(t.from,current),'overlap or noncontinuous track',p);current=t.to;lastEnd=t.end_ms;lastStart=t.start_ms;}terminals[ts[0].actor_id][ts[0].property]=current;}
      for(const e of scene.events){assert(e.verb==='hold'?byEvent[e.id].length===0:equalKeys([...new Set(byEvent[e.id].map(t=>t.actor_id))].sort(),[...e.targets].sort()),'event lost linked targets',p);for(const target of e.targets){const xy=byEvent[e.id].filter(t=>t.actor_id===target&&['x','y'].includes(t.property));assert(xy.length===0||(xy.length===2&&new Set(xy.map(t=>t.property)).size===2),'position must lower into both x/y',p);if(xy.length)assert(xy[0].easing===xy[1].easing,'paired position tracks must share easing',p);}}
      for(const a of scene.actors)history[a.id]={actor:a,state:Object.fromEntries(Object.entries(terminals[a.id]).filter(([k])=>k!=='x'&&k!=='y'))};
      const tr=scene.transition;obj(tr,['kind','start_ms','end_ms'],['direction']);one(tr.kind,['cut','fade','wipe','hold'],p);assert(tr.end_ms===scene.end_ms&&tr.start_ms>=scene.start_ms&&tr.start_ms<=tr.end_ms,'invalid outgoing transition',p);if(['cut','hold'].includes(tr.kind))assert(tr.start_ms===tr.end_ms&&tr.direction===undefined,'invalid cut/hold',p);else assert(tr.start_ms<tr.end_ms,'empty transition',p);if(tr.kind==='wipe')one(tr.direction,['left','right','up','down'],p);else assert(tr.direction===undefined,'unexpected transition direction',p);
    }
    assert(end===plan.duration_ms,'film duration mismatch');return plan;
  }
  const api={validatePlan,PlanError,ASPECTS,KINDS,VERBS,EASINGS,UNITS};
  root.ExplainerDirectionPlan=api;if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window==='object'?window:globalThis);
