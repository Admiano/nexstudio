(function(root,factory){
  if(typeof module==='object'&&module.exports) module.exports=factory();
  else root.NexStickMorphologyV1=factory();
})(typeof globalThis!=='undefined'?globalThis:this,function(){'use strict';
const VERSION='1.0.0';
const JOINTS=['root','pelvis','spine','chest','neck','head','clavicle_l','shoulder_l','elbow_l','wrist_l','clavicle_r','shoulder_r','elbow_r','wrist_r','hip_l','knee_l','ankle_l','toe_l','hip_r','knee_r','ankle_r','toe_r'];
const PARENT={pelvis:'root',spine:'pelvis',chest:'spine',neck:'chest',head:'neck',clavicle_l:'chest',shoulder_l:'clavicle_l',elbow_l:'shoulder_l',wrist_l:'elbow_l',clavicle_r:'chest',shoulder_r:'clavicle_r',elbow_r:'shoulder_r',wrist_r:'elbow_r',hip_l:'pelvis',knee_l:'hip_l',ankle_l:'knee_l',toe_l:'ankle_l',hip_r:'pelvis',knee_r:'hip_r',ankle_r:'knee_r',toe_r:'ankle_r'};
const ORDER=JOINTS.slice(1);
const REFERENCE_SEGMENTS={
 'root->pelvis':0.9180679871,
 'pelvis->spine':0.1381762538541211,'spine->chest':0.2645162187488291,'chest->neck':0.17289080016314343,'neck->head':0.08258678917291558,
 'chest->clavicle_l':0.16325663863030912,'clavicle_l->shoulder_l':0.2212922436092181,'shoulder_l->elbow_l':0.27444022011501423,'elbow_l->wrist_l':0.2726405183311208,
 'chest->clavicle_r':0.16325663863030912,'clavicle_r->shoulder_r':0.22129225104337333,'shoulder_r->elbow_r':0.2744402520673814,'elbow_r->wrist_r':0.2726405201480153,
 'pelvis->hip_l':0.10397311352472906,'hip_l->knee_l':0.40030978545232543,'knee_l->ankle_l':0.429479860960582,'ankle_l->toe_l':0.17330115069175117,
 'pelvis->hip_r':0.10397311352472906,'hip_r->knee_r':0.4003097258476787,'knee_r->ankle_r':0.42947980135594216,'ankle_r->toe_r':0.17330116559372402
};
const vadd=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], vsub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], vmul=(a,s)=>[a[0]*s,a[1]*s,a[2]*s], vlen=a=>Math.hypot(a[0],a[1],a[2]);
const finiteVec=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
function unit(v,fallback=[0,1,0]){const n=vlen(v);return n>1e-9?vmul(v,1/n):fallback.slice()}
function distance(a,b){return vlen(vsub(a,b))}
function clonePose(p){const o={};for(const j of JOINTS)o[j]=p[j].slice();return o}
function familyIndex(presets){const m=new Map();for(const f of presets?.families||[])m.set(f.id,f);return m}
function validateFamily(f){
 const problems=[];if(!f||typeof f!=='object')return {pass:false,problems:['missing-family']};
 if(!f.id)problems.push('missing-id');const m=f.morphology||{};for(const k of ['overallScale','headRatio','neckLength','shoulderWidth','ribcageWidth','waistWidth','hipWidth','upperArmLength','forearmLength','handScale','thighLength','shinLength','footScale','torsoLength','limbThickness'])if(!Number.isFinite(m[k])||m[k]<=0)problems.push('bad-'+k);
 if(f.lifeStage==='adult'&&f.statureClass==='diminutive'&&m.headRatio>1.08)problems.push('diminutive-adult-childlike-head-ratio');
 if(f.lifeStage==='child'&&m.headRatio<1.12)problems.push('child-head-ratio-too-adult');
 return {pass:problems.length===0,problems};
}
function validatePose(p){const problems=[];for(const j of JOINTS)if(!finiteVec(p?.[j]))problems.push('missing-or-nonfinite-'+j);return {pass:problems.length===0,problems}}
function segmentMultiplier(f,parent,child){const m=f.morphology,base=m.overallScale,k=parent+'->'+child;
 if(k==='root->pelvis')return base*((m.thighLength+m.shinLength)/2);
 if(k==='pelvis->spine'||k==='spine->chest')return base*m.torsoLength;
 if(k==='chest->neck')return base*m.neckLength;
 if(k==='neck->head')return base*m.headRatio;
 if(parent==='chest'&&child.startsWith('clavicle_'))return base*m.shoulderWidth;
 if(parent.startsWith('clavicle_')&&child.startsWith('shoulder_'))return base*m.shoulderWidth;
 if(parent.startsWith('shoulder_')&&child.startsWith('elbow_'))return base*m.upperArmLength;
 if(parent.startsWith('elbow_')&&child.startsWith('wrist_'))return base*m.forearmLength;
 if(parent==='pelvis'&&child.startsWith('hip_'))return base*m.hipWidth;
 if(parent.startsWith('hip_')&&child.startsWith('knee_'))return base*m.thighLength;
 if(parent.startsWith('knee_')&&child.startsWith('ankle_'))return base*m.shinLength;
 if(parent.startsWith('ankle_')&&child.startsWith('toe_'))return base*m.footScale;
 return base;
}
function targetSegmentLengths(f){const o={};for(const c of ORDER){const p=PARENT[c],k=p+'->'+c;o[k]=REFERENCE_SEGMENTS[k]*segmentMultiplier(f,p,c)}return o}
function floorY(p){return Math.min(p.toe_l[1],p.toe_r[1],p.ankle_l[1],p.ankle_r[1])}
function translateY(p,dy){for(const j of JOINTS)p[j]=[p[j][0],p[j][1]+dy,p[j][2]];return p}
function inferAnchor(action,opts={}){if(opts.anchorMode)return opts.anchorMode;if(['sit','sit_idle','sit_talk'].includes(action))return 'seat';return 'floor'}
function morphPose(source,family,opts={}){
 const pv=validatePose(source),fv=validateFamily(family);if(!pv.pass||!fv.pass)throw new Error('Invalid morphology input: '+pv.problems.concat(fv.problems).join(','));
 const out={root:source.root.slice()},targets=targetSegmentLengths(family);
 for(const child of ORDER){const parent=PARENT[child],k=parent+'->'+child,dir=unit(vsub(source[child],source[parent]));out[child]=vadd(out[parent],vmul(dir,targets[k]));}
 const anchor=inferAnchor(opts.action||'',opts),srcFloor=floorY(source),rawFloor=floorY(out);let dy=0;
 if(anchor==='floor')dy=srcFloor-rawFloor;
 else if(anchor==='seat'){
   const preservePelvis=source.pelvis[1]-out.pelvis[1];
   const preventPenetration=srcFloor-rawFloor;
   dy=Math.max(preservePelvis,preventPenetration);
 }
 if(Math.abs(dy)>1e-12)translateY(out,dy);
 return {pose3d:out,meta:{familyId:family.id,anchorMode:anchor,verticalAnchorShift:dy,sourceFloorY:srcFloor,morphedFloorY:floorY(out),targetSegmentLengths:targets}};
}
function segmentLengths(p){const out={};for(const child of ORDER){const parent=PARENT[child],k=parent+'->'+child;out[k]=distance(p[parent],p[child])}return out}
function maxTargetSegmentError(p,family){const got=segmentLengths(p),tar=targetSegmentLengths(family);let worst=0,worstSegment=null;for(const k of Object.keys(tar)){const e=Math.abs(got[k]-tar[k]);if(e>worst){worst=e;worstSegment=k}}return {worst,worstSegment,measured:got,target:tar}}
function visualMetrics(p,f){
 const m=f.morphology,b=m.bodyVolumeProfile||{chest:1,waist:1,pelvis:1,limbs:1};
 const skeletalShoulderWidth=distance(p.shoulder_l,p.shoulder_r),skeletalHipJointWidth=distance(p.hip_l,p.hip_r),feet=Math.min(p.toe_l[1],p.toe_r[1],p.ankle_l[1],p.ankle_r[1]);
 const shoulderWidth=.42*m.overallScale*m.shoulderWidth*b.chest,hipWidth=.36*m.overallScale*m.hipWidth*b.pelvis;
 const headRadius=.115*m.overallScale*m.headRatio,top=p.head[1]+headRadius,visualHeight=Math.max(.001,top-feet),poseHeadToHeight=(headRadius*2)/visualHeight;
 const ts=targetSegmentLengths(f),structuralHeight=ts['root->pelvis']+ts['pelvis->spine']+ts['spine->chest']+ts['chest->neck']+ts['neck->head']+headRadius,headToHeight=(headRadius*2)/Math.max(.001,structuralHeight);
 const limbRadius=Math.max(.012,.026*m.overallScale*m.limbThickness*b.limbs),handRadius=Math.max(.014,.035*m.overallScale*m.handScale),footThickness=Math.max(.014,.035*m.overallScale*m.limbThickness*b.limbs);
 return {skeletalShoulderWidth,skeletalHipJointWidth,shoulderWidth,hipWidth,shoulderToHipWidthRatio:shoulderWidth/Math.max(.001,hipWidth),headRadius,visualHeight,poseHeadToHeight,structuralHeight,headToHeight,limbRadius,handRadius,footThickness,torsoProfile:{chest:b.chest,waist:b.waist,pelvis:b.pelvis},lifeStage:f.lifeStage};
}
function approximateCOM(p,f){
 const w={pelvis:.22,spine:.10,chest:.20,head:.08,knee_l:.08,knee_r:.08,ankle_l:.04,ankle_r:.04,elbow_l:.04,elbow_r:.04,wrist_l:.025,wrist_r:.025,hip_l:.03,hip_r:.03};let sum=0,o=[0,0,0];
 for(const [j,a] of Object.entries(w)){sum+=a;o=vadd(o,vmul(p[j],a))}o=vmul(o,1/sum);o[2]+=(f.morphology.centerOfMassApprox?.anteriorOffset||0)*f.morphology.overallScale;return o;
}
function inferActiveHand(state,preferred){if(preferred==='left'||preferred==='right')return preferred;const L=state?.hands?.left?.pose,R=state?.hands?.right?.pose;if(L&&L!=='relaxed'&&(!R||R==='relaxed'))return 'left';return 'right'}
function scaledOffset(v,f){return vmul(v,f.morphology.overallScale*f.morphology.handScale)}
function attachmentPreserve(state,morphed,f,opts={}){
 const prop=state?.prop;if(!prop)return {prop:null,attachment:null};const p={...prop,position:Array.isArray(prop.position)?prop.position.slice():prop.position};let meta=null;
 if(prop.support==='both-hands'||prop.dualHands){p.position=vmul(vadd(morphed.wrist_l,morphed.wrist_r),.5);meta={mode:'morphed-bimanual-midpoint',endpointError:0};}
 else if(prop.owner==='actor'&&String(prop.support||'').includes('hand')){const side=inferActiveHand(state,opts.activeHand),wk='wrist_'+(side==='left'?'l':'r'),srcW=state.pose3d[wk],off=Array.isArray(prop.handOffset)?prop.handOffset:vsub(prop.position,srcW),mo=scaledOffset(off,f);p.position=vadd(morphed[wk],mo);meta={mode:'morphed-single-hand',side,scaledOffset:mo,endpointError:0};}
 return {prop:p,attachment:meta};
}
function worldContactHint(state,morphed,f,opts={}){
 let target=null,side=inferActiveHand(state,opts.activeHand),reason=null;
 if(state?.bodyStage?.target&&finiteVec(state.bodyStage.target)){target=state.bodyStage.target.slice();reason='bodyStage.target'}
 else if(state?.contact?.target&&finiteVec(state.contact.target)){target=state.contact.target.slice();reason='contact.target'}
 else if(state?.prop&&state.prop.owner==='world'&&finiteVec(state.prop.position)&&['pickup','place'].includes(state.action)){const off=Array.isArray(state.prop.handOffset)?state.prop.handOffset:[0,0,0];target=vsub(state.prop.position,off);reason='world-prop-wrist-target'}
 if(!target)return null;const wk='wrist_'+(side==='left'?'l':'r'),delta=vsub(target,morphed[wk]);return {requiresPhaseD:true,side,target,source:reason,delta,meters:vlen(delta),reachScale:f.morphology.overallScale*((f.morphology.upperArmLength+f.morphology.forearmLength)/2)};
}
function compatibilityMetadata(f,p){const m=f.morphology,vm=p?visualMetrics(p,f):null;return {familyId:f.id,canonicalSkeleton:'NexStick-22',canonicalMotionSystem:'NexPerformance V4 canonical',morphologyOnly:true,phaseD:{worldLockedContactRetargetRequired:true,reachScale:m.overallScale*((m.upperArmLength+m.forearmLength)/2),strideScale:m.overallScale*((m.thighLength+m.shinLength)/2),seatFitClass:f.compatibility.seatFitClass,reachClass:f.compatibility.reachClass,centerOfMassApprox:m.centerOfMassApprox},visual:vm};}
function applyState(state,family,opts={}){
 if(!state||state.blocked||!state.pose3d)return {...state,morphology:{familyId:family?.id||null,skipped:true,reason:state?.blocked?'source-blocked':'missing-pose'}};
 const r=morphPose(state.pose3d,family,{...opts,action:state.action}),out={...state,pose3d:r.pose3d};const att=attachmentPreserve(state,r.pose3d,family,opts);if(att.prop)out.prop=att.prop;
 const hint=worldContactHint(state,r.pose3d,family,opts),metrics=visualMetrics(r.pose3d,family),com=approximateCOM(r.pose3d,family);
 out.morphology={version:VERSION,familyId:family.id,sourceEngine:state.engine||null,sourceAction:state.action||null,anchor:r.meta,visual:metrics,centerOfMassApproxWorld:com,attachment:att.attachment,phaseDContactHint:hint,compatibility:compatibilityMetadata(family,r.pose3d)};return out;
}
function applyHandoff(state,giverFamily,receiverFamily,opts={}){
 if(!state||state.blocked||!state.actors)return {...state,morphology:{skipped:true,reason:state?.blocked?'source-blocked':'missing-actors'}};
 const g=morphPose(state.actors.giver.pose3d,giverFamily,{action:'handoff_pair',anchorMode:'floor'}),r=morphPose(state.actors.receiver.pose3d,receiverFamily,{action:'handoff_pair',anchorMode:'floor'});
 const out={...state,actors:{...state.actors,giver:{...state.actors.giver,pose3d:g.pose3d},receiver:{...state.actors.receiver,pose3d:r.pose3d}}};
 const gs=opts.giverHand||'right',rs=opts.receiverHand||'left',gw=g.pose3d['wrist_'+(gs==='left'?'l':'r')],rw=r.pose3d['wrist_'+(rs==='left'?'l':'r')];
 if(state.prop){out.prop={...state.prop};if(state.prop.owner==='shared'||state.prop.support==='shared-hands')out.prop.position=vmul(vadd(gw,rw),.5);else if(state.prop.owner==='receiver')out.prop.position=rw.slice();else out.prop.position=gw.slice();}
 out.pelvisSeparation=distance(g.pose3d.pelvis,r.pose3d.pelvis);out.morphology={version:VERSION,giver:compatibilityMetadata(giverFamily,g.pose3d),receiver:compatibilityMetadata(receiverFamily,r.pose3d),attachment:{giverHand:gs,receiverHand:rs,wristSeparation:distance(gw,rw)},phaseDContactHint:{requiresPhaseD:true,reason:'paired actors have family-specific reach envelopes; preserve staging centrally'}};return out;
}
function createSystem(presets,rules={}){const idx=familyIndex(presets);return {version:VERSION,rules,presets,index:idx,getFamily(id){const f=idx.get(id);if(!f)throw new Error('Unknown cast family '+id);return f},morphPose(p,idOrFamily,opts){const f=typeof idOrFamily==='string'?this.getFamily(idOrFamily):idOrFamily;return morphPose(p,f,opts)},applyState(s,idOrFamily,opts){const f=typeof idOrFamily==='string'?this.getFamily(idOrFamily):idOrFamily;return applyState(s,f,opts)},applyHandoff(s,giver,receiver,opts){const gf=typeof giver==='string'?this.getFamily(giver):giver,rf=typeof receiver==='string'?this.getFamily(receiver):receiver;return applyHandoff(s,gf,rf,opts)},targetSegmentLengths(idOrFamily){const f=typeof idOrFamily==='string'?this.getFamily(idOrFamily):idOrFamily;return targetSegmentLengths(f)},validateFamily,validatePose,segmentLengths,maxTargetSegmentError:(p,idOrFamily)=>{const f=typeof idOrFamily==='string'?this.getFamily(idOrFamily):idOrFamily;return maxTargetSegmentError(p,f)},visualMetrics:(p,idOrFamily)=>{const f=typeof idOrFamily==='string'?this.getFamily(idOrFamily):idOrFamily;return visualMetrics(p,f)},approximateCOM:(p,idOrFamily)=>{const f=typeof idOrFamily==='string'?this.getFamily(idOrFamily):idOrFamily;return approximateCOM(p,f)},compatibilityMetadata:(idOrFamily,p)=>{const f=typeof idOrFamily==='string'?this.getFamily(idOrFamily):idOrFamily;return compatibilityMetadata(f,p)}}}
return {version:VERSION,JOINTS,PARENT,REFERENCE_SEGMENTS,createSystem,validateFamily,validatePose,morphPose,applyState,applyHandoff,targetSegmentLengths,segmentLengths,maxTargetSegmentError,visualMetrics,approximateCOM,compatibilityMetadata};
});
