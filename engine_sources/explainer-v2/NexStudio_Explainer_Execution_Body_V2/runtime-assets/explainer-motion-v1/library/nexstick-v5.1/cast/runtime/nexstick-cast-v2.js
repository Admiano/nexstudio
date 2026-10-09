'use strict';
const fs=require('fs'), path=require('path');
const ROOT=path.resolve(__dirname,'../..');
if(!global.window)global.window=globalThis;
function loadGlobal(rel){require(path.join(ROOT,rel));}
if(!global.NexPerformanceUnifiedV5)loadGlobal('runtime/node-bootstrap-v5.js');
if(!global.NexStickBodyShellV1)loadGlobal('cast/phases/A/runtime/nex-stick-body-shell-v1.js');
if(!global.NexClothingLibraryV1)loadGlobal('cast/phases/B/runtime/clothing-library-v1.js');
if(!global.NexClothingSystemV1)loadGlobal('cast/phases/B/runtime/nex-clothing-system-v1.js');
const C=require(path.join(ROOT,'cast/phases/C/runtime/nexstick-morphology-v1.js'));
if(!global.NexStickCastPhaseDModifiersV1)loadGlobal('cast/phases/D/config/family-motion-modifiers-v1.js');
if(!global.NexStickCastPhaseDV2)loadGlobal('cast/phases/D/runtime/nex-proportion-performance-adapter-v2.js');
if(!global.NexPersonalityMotionSelectionV1)loadGlobal('cast/phases/E/runtime/personality-motion-selection-adapter-v1.js');
if(!global.NexStickPersonalityAdapterV2)loadGlobal('cast/phases/E/runtime/nexstick-personality-adapter-v2.js');
const F=require(path.join(ROOT,'cast/phases/F/CAST_RESOLVER_V1/index.js'));
const PRESETS=JSON.parse(fs.readFileSync(path.join(ROOT,'cast/phases/C/CAST_FAMILY_PRESETS_V1.json'),'utf8'));
const RULES=JSON.parse(fs.readFileSync(path.join(ROOT,'cast/phases/C/MORPHOLOGY_RULES_V1.json'),'utf8'));
const BRIDGE=JSON.parse(fs.readFileSync(path.join(ROOT,'cast/data/FAMILY_BRIDGE_V1.json'),'utf8'));
const ROLE_CLOTHING=JSON.parse(fs.readFileSync(path.join(ROOT,'cast/data/ROLE_CLOTHING_BRIDGE_V1.json'),'utf8'));
const morph=C.createSystem(PRESETS,RULES);
const V5=global.NexPerformanceUnifiedV5, D=global.NexStickCastPhaseDV2, DM=global.NexStickCastPhaseDModifiersV1, E=global.NexStickPersonalityAdapterV2;
const Body=global.NexStickBodyShellV1, Cloth=global.NexClothingSystemV1, ClothLib=global.NexClothingLibraryV1, NS=global.NexStickman;
const Surface=require(path.join(ROOT,'cast/runtime/nexstick-authored-surface-v1.js'));
const VERSION='2.1.0-unified-performance-v5.1';
const clone=x=>x==null?x:JSON.parse(JSON.stringify(x));
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);
function family(id){return morph.getFamily(id)}
function familyBridge(id){const b=BRIDGE.families[id];if(!b)throw new Error('No master family bridge for '+id);return b}
function performanceClassForFamily(id){return familyBridge(id).performanceClass}
function clothingFamilyForFamily(id){return familyBridge(id).clothingFamily}
function derivePerformanceMorphology(id){
 const f=family(id), m=f.morphology, targets=morph.targetSegmentLengths(id), ref=NS.corpus.segmentLengthReference;
 const segmentScales={};for(const [k,L] of Object.entries(targets))segmentScales[k]=L/ref[k];
 const desc={id, heightScale:clamp(m.overallScale,.45,1.4), armScale:clamp(m.overallScale*((m.upperArmLength+m.forearmLength)/2),.45,1.4), legScale:clamp(m.overallScale*((m.thighLength+m.shinLength)/2),.45,1.4), torsoScale:clamp(m.overallScale*m.torsoLength,.55,1.35), shoulderScale:clamp(m.overallScale*m.shoulderWidth,.65,1.4), footScale:clamp(m.overallScale*m.footScale,.6,1.35), segmentScales};
 const v=D.validateMorphology(desc);if(!v.ok)throw new Error(`Phase C -> D morphology bridge invalid for ${id}: ${JSON.stringify(v)}`);return desc;
}
function bodyProfileForFamily(id){
 const m=family(id).morphology, os=m.overallScale, thick=m.limbThickness;
 return {id:`cast_${id}_body_v1`,torso:{shoulderPadM:.020*os*m.shoulderWidth,hipPadM:.034*os*m.hipWidth,minShoulderHalfM:.160*os*m.shoulderWidth,minHipHalfM:.145*os*m.hipWidth,waistTaper:clamp(.86*(m.waistWidth/((m.shoulderWidth+m.hipWidth)/2)),.70,.98)},limbRadiusM:{upperArm:.045*os*thick,forearm:.040*os*thick,thigh:.065*os*thick,calf:.052*os*thick,neck:.043*os*m.neckLength},hand:{scale:1.34*os*m.handScale,palmExpandPx:1.5,fingerWidthM:.017*os*m.handScale},foot:{widthM:.078*os*m.footScale,toeExpandM:.018*os*m.footScale},head:{radiusXM:.100*os*m.headRatio,radiusYM:.125*os*m.headRatio},outlineM:.012*clamp(Math.pow(os,.35),.78,1.12)};
}
function clothingBodyForFamily(id){
 const f=family(id), m=f.morphology, os=m.overallScale, cf=clothingFamilyForFamily(id);
 const metrics={shoulderHalfWidth:.195*os*m.shoulderWidth,chestHalfWidth:.170*os*m.ribcageWidth,waistHalfWidth:.145*os*m.waistWidth,hipHalfWidth:.155*os*m.hipWidth,upperArmRadius:.038*os*m.limbThickness,forearmRadius:.032*os*m.limbThickness,thighRadius:.058*os*m.limbThickness,calfRadius:.046*os*m.limbThickness,footRadius:.042*os*m.footScale,torsoLengthScale:os*m.torsoLength,limbWidthScale:os*m.limbThickness,source:'phase-a-c-measured-bridge'};
 return {id:`cast_${id}_clothing_body`,family:cf,metrics,sourceFamily:id,presentation:f.presentation,lifeStage:f.lifeStage};
}
function presetById(id){return ClothLib.presets.find(p=>p.id===id)||null}
function presentationKey(id){const p=family(id).presentation;if(['man','woman','boy','girl'].includes(p))return p;return 'neutral'}
function presetCompatible(p,id){if(!p)return false;const cf=clothingFamilyForFamily(id);return p.compatibleBodyFamilies.includes('*')||p.compatibleBodyFamilies.includes(cf)}
function resolveClothingPreset({familyId,explicitPreset,roleTags=[]}={}){
 family(familyId);
 if(explicitPreset){const p=presetById(explicitPreset);if(!p)return {blocked:true,failure:'UNKNOWN_CLOTHING_PRESET',presetId:explicitPreset};if(!presetCompatible(p,familyId))return {blocked:true,failure:'CLOTHING_PRESET_INCOMPATIBLE_WITH_FAMILY',presetId:explicitPreset,familyId};return {blocked:false,presetId:p.id,source:'explicit'};}
 const pk=presentationKey(familyId);
 for(const tag of roleTags||[]){const row=ROLE_CLOTHING.tags[tag];if(!row)continue;const id=row[pk]||row.neutral;const p=presetById(id);if(p&&presetCompatible(p,familyId))return {blocked:false,presetId:id,source:'role_tag',tag};}
 const d=familyBridge(familyId).defaultClothing,p=presetById(d);if(p&&presetCompatible(p,familyId))return {blocked:false,presetId:d,source:'family_default'};
 const u=presetById('workwear_universal');return {blocked:false,presetId:u.id,source:'universal_fallback'};
}
function personalityPlanningAction(action){return ({low_pickup:'pickup',table_pickup:'pickup',high_reach:'reach',heavy_carry:'carry'}[action]||action)}
function executionAction(action){return ({present:'interact',reach:'captured_reach'}[action]||action)}
function planPersonality(req){const publicAction=req.action||'idle',planningAction=personalityPlanningAction(publicAction);const p=E.plan({...req,action:planningAction});return {...p,masterPublicAction:publicAction};}
function personalityMeta(plan,t){
 const map=E._internals.coreMap(plan,t), pr=plan.profile, sel=plan.selection.selected;
 const conversation=['conversation','talk','handoff','handoff_pair'].includes(plan.publicAction),presentation=['present','interact'].includes(plan.publicAction),target=conversation?'partner':presentation?'audience':['pickup','reach','captured_reach'].includes(plan.publicAction)?'task':'forward';
 const interval=pr.nodFrequency>0?60/pr.nodFrequency:Infinity,phase=((String(plan.seed).split('').reduce((s,c)=>s+c.charCodeAt(0),0)%1000)/1000)*Math.min(interval,4),local=Math.max(0,(+t||0)-plan.leadIn),pulse=conversation&&Number.isFinite(interval)&&local>=phase&&((local-phase)%interval)<.12;
 return {version:plan.version,preset:plan.personality,character:plan.character,seed:plan.seed,parameters:clone(pr),motionSelection:{reason:plan.selection.reason,selected:sel?{id:sel.id,source:sel.source,clip:sel.clip,performance:sel.performance||null,semantic:sel.semantic}:null,ranked:plan.selection.ranked.slice(0,5)},timing:{region:map.region,baseTime:map.baseTime,leadIn:plan.leadIn,coreDuration:plan.coreDuration,settleTail:plan.settleTail,tempo:plan.tempo,contactLocked:plan.contactLocked},gestureIntent:{amplitude:pr.gestureAmplitude,frequency:pr.gestureFrequency,anticipationAmplitude:pr.anticipationAmplitude,bodyOpenness:pr.bodyOpenness,handRestOpenness:pr.handRestOpenness,directJointWrite:false},restIntent:{stanceWidth:pr.stanceWidth,bodyOpenness:pr.bodyOpenness,handRestOpenness:pr.handRestOpenness,directJointWrite:false},attention:{target,gazeHoldSeconds:pr.gazeHoldDuration,reactionLatencySeconds:pr.reactionLatency,headTiltTendency:pr.headTiltTendency,nodFrequencyPerMinute:pr.nodFrequency,nodCue:pulse,listenerActivity:pr.conversationListenerActivity,region:map.region,directJointWrite:false},invariants:{phaseEJointWrites:false,v5PerformanceAuthority:true,contactCoreV5Authoritative:true}};
}
function safeRestHands(state,plan){if(!state||state.blocked||plan.contactLocked||!state.hands)return state;if(!['idle','conversation','talk'].includes(plan.publicAction)||plan.profile.handRestOpenness<1.10)return state;const h=clone(state.hands);for(const s of ['left','right'])if(h[s]&&['relaxed','open'].includes(h[s].pose))h[s].pose='open';return {...state,hands:h};}
function decorateState(req,familyId,f,perfClass,morphology,plan,t,state0){
 if(!state0||state0.blocked)return {...state0,masterVersion:VERSION,familyId,performanceClass:perfClass,personalityPlan:{preset:plan.personality,timing:personalityMeta(plan,Math.min(+t||0,plan.duration)).timing},inheritedFailure:true};
 let state=safeRestHands(state0,plan);state={...state,action:req.action||'idle',masterVersion:VERSION,familyId,castFamily:{id:f.id,lifeStage:f.lifeStage,presentation:f.presentation,statureClass:f.statureClass},morphology:{...C.compatibilityMetadata(f,state.pose3d),derivedPerformanceDescriptor:morphology},personality:personalityMeta(plan,Math.min(+t||0,plan.duration))};
 state.personality.timing.familyCadenceApplied=state.adaptation?.cadenceApplied??1;
 const csel=resolveClothingPreset({familyId,explicitPreset:req.clothingPreset,roleTags:req.roleTags||[]});if(csel.blocked)return {...state,blocked:true,failure:csel.failure,clothing:csel};
 const cbody=clothingBodyForFamily(familyId);let fit;try{fit=Cloth.fit({pose3d:state.pose3d,body:cbody,preset:presetById(csel.presetId),library:ClothLib,palette:req.palette});}catch(e){return {...state,blocked:true,failure:'CLOTHING_FIT_ERROR',detail:e.message,clothing:csel};}
 const cqa=Cloth.qaFit(fit),profile=bodyProfileForFamily(familyId);
 return {blocked:false,masterVersion:VERSION,state,familyId,performanceClass:perfClass,bodyProfile:profile,clothingBody:cbody,clothingPreset:csel,clothingFit:fit,clothingQA:cqa,duration:state.duration??plan.duration,time:+t||0};
}
function sample(req={},t=0){
 const familyId=req.familyId||req.family;if(!familyId)return {blocked:true,failure:'FAMILY_REQUIRED'};let f;try{f=family(familyId)}catch(e){return {blocked:true,failure:'UNKNOWN_FAMILY',familyId}};
 const perfClass=performanceClassForFamily(familyId),morphology=derivePerformanceMorphology(familyId),plan=planPersonality({...req,character:req.character||familyId}),map=E._internals.coreMap(plan,t);
 const dreq={...plan.adaptedRequest,action:executionAction(req.action||'idle')};delete dreq.familyId;delete dreq.family;delete dreq.clothingPreset;delete dreq.roleTags;
 const state0=D.sample({family:perfClass,morphology,request:dreq},map.baseTime,DM);
 return decorateState(req,familyId,f,perfClass,morphology,plan,t,state0);
}
function prepareSequenceStep(req,familyId,perfClass){
 const plan=planPersonality({...req,character:req.character||familyId}),execAction=executionAction(req.action||'idle'),mod=DM.families[perfClass]||{},coreReq={...plan.adaptedRequest,...req,action:execAction};
 for(const k of ['family','familyId','clothingPreset','roleTags','personality','character','seed','palette'])delete coreReq[k];
 const gait=['walk','run'].includes(execAction),familyCadence=gait?(mod.cadenceBias||1):1,personalityScale=plan.tempoEligible?(plan.tempo||1):1,totalScale=clamp(familyCadence*personalityScale,.55,1.65);coreReq.timeScale=totalScale;
 if(gait){const base=execAction==='walk'?1.1:2.1,worldSpeed=Number.isFinite(req.speedMps)?+req.speedMps:base*(mod.strideLengthScale||1);coreReq.worldSpeedMps=worldSpeed;coreReq.speedMps=worldSpeed/totalScale;}
 return {publicReq:clone(req),execAction,personalityPlan:plan,coreReq,totalScale,familyCadence};
}
function sequence(input={},opts={}){
 const familyId=input.familyId||input.family;if(!familyId)return {blocked:true,failure:'FAMILY_REQUIRED'};let f;try{f=family(familyId)}catch(e){return {blocked:true,failure:'UNKNOWN_FAMILY',familyId}};
 const steps=input.steps||[];if(!Array.isArray(steps)||!steps.length)return {blocked:true,failure:'SEQUENCE_STEPS_REQUIRED'};
 const perfClass=performanceClassForFamily(familyId),morphology=derivePerformanceMorphology(familyId),prepared=steps.map(r=>prepareSequenceStep(r,familyId,perfClass)),core=V5.sequence(prepared.map(x=>x.coreReq),opts);
 if(core.blocked)return {...core,masterVersion:VERSION,familyId,performanceClass:perfClass};
 function stateAt(t){const tt=clamp(+t||0,0,core.duration),raw=core.sample(tt);if(raw.blocked)return raw;const idx=raw.sequence?.index??0,meta=prepared[idx],cp=core.plans[idx],local=Math.max(0,tt-cp.start),adapted=D.adaptState({family:perfClass,morphology,request:{...meta.publicReq,action:meta.execAction}},raw,DM);if(!adapted||adapted.blocked)return adapted;const planT=meta.personalityPlan.duration>0?Math.min(meta.personalityPlan.duration,local/Math.max(1e-6,cp.duration)*meta.personalityPlan.duration):0;let state=safeRestHands(adapted,meta.personalityPlan);state={...state,action:meta.publicReq.action||'idle',masterVersion:VERSION,familyId,castFamily:{id:f.id,lifeStage:f.lifeStage,presentation:f.presentation,statureClass:f.statureClass},morphology:{...C.compatibilityMetadata(f,state.pose3d),derivedPerformanceDescriptor:morphology},personality:personalityMeta(meta.personalityPlan,planT),sequence:{...raw.sequence,publicAction:meta.publicReq.action||'idle',familyCadence:meta.familyCadence,timeScale:meta.totalScale}};return state;}
 const stateSeq={version:VERSION,duration:core.duration,plans:core.plans,blocked:false,sample:stateAt};
 stateSeq.qa=()=>V5.qa.continuity(stateSeq,{...(opts.qa||{}),segmentReference:D.targetLengths(morphology)});
 return {version:VERSION,masterVersion:VERSION,familyId,performanceClass:perfClass,morphology,prepared,core,duration:core.duration,blocked:false,state:stateAt,sample(t){const tt=clamp(+t||0,0,core.duration),st=stateAt(tt);if(!st||st.blocked)return st;const idx=st.sequence?.index??0,meta=prepared[idx];return decorateState(meta.publicReq,familyId,f,perfClass,morphology,meta.personalityPlan,tt,st);},qa:stateSeq.qa};
}
function resolveCast(input){return F.resolve(input)}
function sampleCastSpec(castSpec,request={},t=0){if(!castSpec||!castSpec.family)return {blocked:true,failure:'CAST_SPEC_WITH_FAMILY_REQUIRED'};const personality=request.personality||castSpec.personality?.selected_preset||castSpec.personality?.ranked_presets?.[0]||'calm',roleTags=request.roleTags||([castSpec.clothing?.selected_tag].filter(Boolean).concat(castSpec.clothing?.ranked_tags||[]));return sample({...request,familyId:castSpec.family,personality,roleTags},t)}
function resolveAndSample(input,request={},t=0){const r=resolveCast(input);if(r.status!=='RESOLVED')return {blocked:true,failure:'CAST_SELECTION_REQUIRED',resolution:r};const slot=r.slots?.[0],spec=slot?.final_cast_spec;if(!spec)return {blocked:true,failure:'CAST_SELECTION_REQUIRED',resolution:r};return {resolution:r,sample:sampleCastSpec(spec,request,t)};}
function projectWorld(state,g,p){return NS.project({root:state.pose3d.root,x:p},{...g.camera,root_center:g.camera.root_center}).x}
function garmentPalette(familyId,fit){const sets=[{upper:'#63799a',lower:'#363d4b',outer:'#59606e',shoe:'#282b31',accent:'#b9925c'},{upper:'#8b6f63',lower:'#42404a',outer:'#61545a',shoe:'#29272b',accent:'#b88c5a'},{upper:'#667e71',lower:'#3e4850',outer:'#53645d',shoe:'#272d30',accent:'#b79762'},{upper:'#786f91',lower:'#3c3e4d',outer:'#5a566a',shoe:'#292a31',accent:'#b99662'}];let h=0;for(const c of familyId)h=(h*31+c.charCodeAt(0))>>>0;return {...sets[h%sets.length],...(fit?.palette||{})};}
function clothingOverlay(result,g){
 const fit=result.clothingFit,state=result.state,pal=garmentPalette(result.familyId,fit),sc=g.camera.scale;let out=`<g data-layer="clothing" data-preset="${result.clothingPreset.presetId}">`;
 const esc=s=>String(s).replace(/[&<>'"]/g,'');
 for(const r of [...fit.regions].sort((a,b)=>(a.layer||0)-(b.layer||0))){
   if(r.type==='segment_envelope'){const A=projectWorld(state,g,r.a),B=projectWorld(state,g,r.b),key=r.kind==='trouser'?'lower':r.kind==='footwear'?'shoe':r.kind==='outerwear'?'outer':'upper',col=pal[key]||pal.upper;out+=`<line data-garment="${esc(r.id)}" x1="${A.x.toFixed(2)}" y1="${A.y.toFixed(2)}" x2="${B.x.toFixed(2)}" y2="${B.y.toFixed(2)}" stroke="${col}" stroke-width="${(2*r.radius*sc).toFixed(2)}" stroke-linecap="round"/>`;}
   else if(r.type==='torso_envelope'){const Cc=projectWorld(state,g,r.chest),P=projectWorld(state,g,r.pelvis),th=r.topHalfWidth*sc,wh=r.waistHalfWidth*sc,hh=r.hemHalfWidth*sc,my=(Cc.y+P.y)/2,col=r.kind==='outerwear'?pal.outer:pal.upper;out+=`<path data-garment="${esc(r.id)}" d="M ${(Cc.x-th).toFixed(1)} ${Cc.y.toFixed(1)} Q ${(Cc.x-wh).toFixed(1)} ${my.toFixed(1)} ${(P.x-hh).toFixed(1)} ${P.y.toFixed(1)} L ${(P.x+hh).toFixed(1)} ${P.y.toFixed(1)} Q ${(Cc.x+wh).toFixed(1)} ${my.toFixed(1)} ${(Cc.x+th).toFixed(1)} ${Cc.y.toFixed(1)} Z" fill="${col}" stroke="#272522" stroke-width="1.5"/>`;}
   else if(r.type==='skirt_envelope'){const T=projectWorld(state,g,r.centerTop),hw=r.hipHalfWidth*sc,bw=r.hemHalfWidth*sc,hy=g.camera.origin[1]-r.hemY*sc;out+=`<path data-garment="${esc(r.id)}" d="M ${(T.x-hw).toFixed(1)} ${T.y.toFixed(1)} L ${(T.x-bw).toFixed(1)} ${hy.toFixed(1)} L ${(T.x+bw).toFixed(1)} ${hy.toFixed(1)} L ${(T.x+hw).toFixed(1)} ${T.y.toFixed(1)} Z" fill="${pal.lower}" stroke="#272522" stroke-width="1.5"/>`;}
   else if(r.type==='waist_band'){const Cc=projectWorld(state,g,r.center);out+=`<line x1="${(Cc.x-r.halfWidth*sc).toFixed(1)}" y1="${Cc.y.toFixed(1)}" x2="${(Cc.x+r.halfWidth*sc).toFixed(1)}" y2="${Cc.y.toFixed(1)}" stroke="#272522" stroke-width="2" opacity=".45"/>`;}
   else if(r.type==='headwear'){const Cc=projectWorld(state,g,r.center),rr=r.radius*sc;out+=`<path d="M ${(Cc.x-rr).toFixed(1)} ${(Cc.y-rr*.40).toFixed(1)} Q ${Cc.x.toFixed(1)} ${(Cc.y-rr*1.03).toFixed(1)} ${(Cc.x+rr).toFixed(1)} ${(Cc.y-rr*.40).toFixed(1)}" fill="none" stroke="${pal.outer}" stroke-width="${Math.max(5,rr*.32).toFixed(1)}" stroke-linecap="round"/>`;}
   else if(r.type==='accessory'){const Cc=projectWorld(state,g,r.center);out+=`<circle cx="${(Cc.x+18).toFixed(1)}" cy="${(Cc.y+10).toFixed(1)}" r="6" fill="${pal.accent}" stroke="#272522" stroke-width="1.5"/>`;}
 }
 return out+'</g>';
}
function render(result,opts={}){return Surface.render(result,opts);}
function translatePose(p,d){const o={};for(const [k,v] of Object.entries(p))o[k]=Array.isArray(v)&&v.length===3?[v[0]+d[0],v[1]+d[1],v[2]+d[2]]:v;return o}
function wrist(pose,hand){return pose['wrist_'+(hand==='left'?'l':'r')]}
function handoffPair(spec={},t=0){
 const giverFamilyId=spec.giverFamilyId||'adult_man_average',receiverFamilyId=spec.receiverFamilyId||'adult_woman_average',gh=spec.giverHand||'right',rh=spec.receiverHand||'left';family(giverFamilyId);family(receiverFamilyId);
 if(giverFamilyId===receiverFamilyId){const pc=performanceClassForFamily(giverFamilyId),m=derivePerformanceMorphology(giverFamilyId),pair=D.handoffPair({family:pc,morphology:m,spec},t,DM);return {...pair,masterVersion:VERSION,giverFamilyId,receiverFamilyId,mixedFamily:false};}
 const core=V5.handoffPair(t,spec);if(!core||core.blocked)return {...core,masterVersion:VERSION};
 const cref=V5.handoffPair(.9,spec),now=morph.applyHandoff(core,giverFamilyId,receiverFamilyId,{giverHand:gh,receiverHand:rh}),ref=morph.applyHandoff(cref,giverFamilyId,receiverFamilyId,{giverHand:gh,receiverHand:rh});
 // First preserve the authored offer plane by aligning the reference wrists horizontally only.
 const rg0=ref.actors.giver.pose3d,rr0=ref.actors.receiver.pose3d,gw0=wrist(rg0,gh),rw0=wrist(rr0,rh),baseG=[(rw0[0]-gw0[0])/2,0,(rw0[2]-gw0[2])/2],baseR=[-baseG[0],0,-baseG[2]];
 let rg=translatePose(rg0,baseG),rr=translatePose(rr0,baseR),extra=0,extraVec=[0,0,0],target=null,reachable=false;
 const armLength=(p,side)=>{const s=side==='left'?'l':'r';return dist(p['shoulder_'+s],p['elbow_'+s])+dist(p['elbow_'+s],p['wrist_'+s])};
 const canReach=(p,side,T)=>{const s=side==='left'?'l':'r';return dist(p['shoulder_'+s],T)<=armLength(p,side)+1e-8};
 // If family heights differ, stage both whole actors a few centimetres closer until the same authored offer point is reachable.
 for(extra=0;extra<=.12+1e-9;extra+=.01){
   let g=rg,r=rr;if(extra>0){let v=[rr.pelvis[0]-rg.pelvis[0],0,rr.pelvis[2]-rg.pelvis[2]],n=Math.hypot(v[0],v[2]);if(n>1e-8){extraVec=[v[0]/n*extra,0,v[2]/n*extra];g=translatePose(rg,extraVec);r=translatePose(rr,[-extraVec[0],0,-extraVec[2]]);}}
   const G=wrist(g,gh),R=wrist(r,rh),T=[(G[0]+R[0])/2,(G[1]+R[1])/2,(G[2]+R[2])/2];
   if(canReach(g,gh,T)&&canReach(r,rh,T)){rg=g;rr=r;target=T;reachable=true;break;}
 }
 if(!reachable)return {blocked:true,failure:'MIXED_FAMILY_HANDOFF_REQUIRES_BODY_REPOSITION',masterVersion:VERSION,giverFamilyId,receiverFamilyId,requestBodyReposition:true,maxExtraPartnerStageM:.12};
 const totalG=[baseG[0]+extraVec[0],0,baseG[2]+extraVec[2]],totalR=[baseR[0]-extraVec[0],0,baseR[2]-extraVec[2]];
 let Gnow=translatePose(now.actors.giver.pose3d,totalG),Rnow=translatePose(now.actors.receiver.pose3d,totalR);
 const weights={mutual_attention:0,offer_prepare:.38,contact:.78,shared_contact:1,transfer_release:.72,withdraw_settle:.18},w=weights[now.phase]??0;
 const retarget=(pose,side,T,weight)=>{if(weight<=0)return {ok:true,pose,meters:0};const s=side==='left'?'l':'r',wk='wrist_'+s,sh='shoulder_'+s,el='elbow_'+s,goal=pose[wk].map((v,i)=>v+(T[i]-v)*weight),meters=dist(pose[wk],goal);if(meters>.28+1e-9)return {ok:false,failure:'MIXED_FAMILY_HANDOFF_RETARGET_EXCEEDS_BOUND',meters,bound:.28};const sol=global.NexStickmanUtilsV2.setChain(pose,sh,el,wk,goal);return sol.ok?{ok:true,pose:sol.pose,meters}:{ok:false,failure:'MIXED_FAMILY_HANDOFF_ARM_UNREACHABLE',detail:sol,meters};};
 const gs=retarget(Gnow,gh,target,w),rs=retarget(Rnow,rh,target,w);if(!gs.ok||!rs.ok)return {blocked:true,failure:gs.failure||rs.failure,masterVersion:VERSION,giverFamilyId,receiverFamilyId,giver:gs,receiver:rs};Gnow=gs.pose;Rnow=rs.pose;
 now.actors.giver.pose3d=Gnow;now.actors.receiver.pose3d=Rnow;
 const G=wrist(Gnow,gh),R=wrist(Rnow,rh),gap=dist(G,R),sep=dist(Gnow.pelvis,Rnow.pelvis),shared=now.phase==='shared_contact'||now.prop?.owner==='shared';
 if(shared&&gap>.035+1e-8)return {blocked:true,failure:'MIXED_FAMILY_HANDOFF_CONTACT_GAP_AFTER_RETARGET',masterVersion:VERSION,giverFamilyId,receiverFamilyId,sharedContactGap:gap,cap:.035};
 const minSep=.42*Math.min(family(giverFamilyId).morphology.overallScale,family(receiverFamilyId).morphology.overallScale);if(sep<minSep)return {blocked:true,failure:'MIXED_FAMILY_HANDOFF_SPACING_COLLAPSED',masterVersion:VERSION,pelvisSeparation:sep,minSep};
 if(now.prop){if(now.prop.owner==='shared')now.prop.position=[(G[0]+R[0])/2,(G[1]+R[1])/2,(G[2]+R[2])/2];else if(now.prop.owner==='giver')now.prop.position=G.slice();else if(now.prop.owner==='receiver')now.prop.position=R.slice();}
 return {...now,blocked:false,masterVersion:VERSION,giverFamilyId,receiverFamilyId,mixedFamily:true,mixedFamilyBridge:{v5HandoffAuthority:true,horizontalPreStaging:{giver:totalG,receiver:totalR,extraTowardPartnerM:extra},interactionTarget:target,retargetWeight:w,armRetargetMeters:{giver:gs.meters,receiver:rs.meters},sharedContactGap:gap,pelvisSeparation:sep,maxArmRetargetBoundM:.28,verticalWholeBodyShift:false,limbStretch:false,finalContactCapM:.035}};
}
function contract(){return {name:'NexStickMasterV2',version:VERSION,authoritativePerformance:'NexPerformanceUnifiedV5@5.1.0-skin-safe-angular-continuity',skinPolicy:{currentFallback:'NexStick Authored Surface V1',futureProductionAdapter:'skin-independent; ongoing realistic 3D family may bind without changing performance authority'},phases:{A:'body-shell/legacy-debug',B:'clothing semantics',C:'morphology',D:'proportion-aware state retarget V2',E:'personality V2',F:'roles'},integrationOrder:['F role semantics','C family resolution','E personality/timing intent','V5 continuous performance','D V2 post-continuity morphology retarget','skin adapter','B clothing semantic fit'],hardTruth:{v4SequencerSuperseded:true,v4RetainedOnlyAsAdmittedLegacyDonor:true,phaseEJointWrites:false,separateFamilyMotionEngines:false,persistentWorldRootAndFacing:true,postRootStrideWarp:false,underspecifiedDemographicsRemainRanked:true,mixedFamilyHandoffFailsClosedWhenContactHeightMismatchExceeds35mm:true,authoredSurface:Surface.version,realistic3DBranchNotOverwritten:true}}}
module.exports={version:VERSION,contract,familyIds:PRESETS.families.map(f=>f.id),family,resolveCast,resolveAndSample,sampleCastSpec,sample,sequence,handoffPair,render,performanceClassForFamily,derivePerformanceMorphology,bodyProfileForFamily,clothingBodyForFamily,resolveClothingPreset,morphologySystem:morph};
