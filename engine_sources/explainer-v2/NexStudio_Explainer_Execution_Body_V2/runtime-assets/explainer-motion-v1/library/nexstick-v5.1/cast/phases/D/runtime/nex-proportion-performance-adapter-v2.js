(function(root){'use strict';
const E=root.NexPerformanceUnifiedV5,U=root.NexStickmanUtilsV2,NS=root.NexStickman;
if(!E||!U||!NS) throw new Error('Phase D V2 requires NexPerformance Unified V5 globals');
const VERSION='2.1.0-unified-v5.1';
const CORRECTION_CAP=0.035;
const REF=NS.corpus.segmentLengthReference;
const PAIRS=Object.keys(REF).map(k=>k.split('->'));
const CHILDREN={}; for(const [a,b] of PAIRS)(CHILDREN[a]||(CHILDREN[a]=[])).push(b);
const GROUPS={
 arm:new Set(['shoulder_l->elbow_l','elbow_l->wrist_l','shoulder_r->elbow_r','elbow_r->wrist_r']),
 leg:new Set(['hip_l->knee_l','knee_l->ankle_l','hip_r->knee_r','knee_r->ankle_r']),
 torso:new Set(['pelvis->spine','spine->chest','chest->neck','neck->head']),
 shoulder:new Set(['chest->clavicle_l','clavicle_l->shoulder_l','chest->clavicle_r','clavicle_r->shoulder_r','pelvis->hip_l','pelvis->hip_r']),
 foot:new Set(['ankle_l->toe_l','ankle_r->toe_r'])
};
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const clone=x=>JSON.parse(JSON.stringify(x));
const dist=(a,b)=>U.len(U.sub(a,b));
const vec=(v,d=[0,0,0])=>Array.isArray(v)&&v.length===3?v.map(Number):d.slice();
function scaleForPair(pair,m){ if(m.segmentScales&&Number.isFinite(m.segmentScales[pair]))return m.segmentScales[pair]; if(GROUPS.arm.has(pair))return m.armScale; if(GROUPS.leg.has(pair))return m.legScale; if(GROUPS.torso.has(pair))return m.torsoScale; if(GROUPS.shoulder.has(pair))return m.shoulderScale||m.heightScale; if(GROUPS.foot.has(pair))return m.footScale||m.legScale; return m.heightScale; }
function validateMorphology(m){
 if(!m||typeof m!=='object')return {ok:false,failure:'MORPHOLOGY_REQUIRED'};
 for(const k of ['heightScale','armScale','legScale','torsoScale']) if(!Number.isFinite(+m[k])) return {ok:false,failure:'MORPHOLOGY_SCALE_REQUIRED',field:k};
 const ranges={heightScale:[.45,1.4],armScale:[.45,1.4],legScale:[.45,1.4],torsoScale:[.55,1.35],shoulderScale:[.65,1.4],footScale:[.6,1.35]};
 for(const [k,[a,b]] of Object.entries(ranges)) if(m[k]!=null&&(+m[k]<a||+m[k]>b))return {ok:false,failure:'MORPHOLOGY_SCALE_OUT_OF_RANGE',field:k,value:+m[k],range:[a,b]};
 return {ok:true};
}
function targetLengths(m){return Object.fromEntries(Object.entries(REF).map(([k,v])=>[k,v*scaleForPair(k,m)]));}
function directionBias(dir,pair,mod,action){let d=dir.slice();
 if(pair.startsWith('pelvis->hip_')){const rest=['idle','conversation','carry'].includes(action)?(mod.restingStanceScale||1):1;d[0]*=(mod.stepWidthScale||1)*rest;}
 if((GROUPS.arm.has(pair))&&['walk','run'].includes(action)) d[2]*=mod.armSwingScale||1;
 if((GROUPS.arm.has(pair))&&['conversation','dance'].includes(action)){d[0]*=mod.gestureAmplitudeScale||1;d[2]*=mod.gestureAmplitudeScale||1;}
 return U.unit(d);
}
function reconstruct(canon,m,mod,action,origin=[0,0,0]){
 const out={}; const root0=canon.root||[0,0,0],pel0=canon.pelvis||[0,.87,0];
 out.root=U.add(root0,origin);
 const rp=U.sub(pel0,root0), ps=m.legScale||m.heightScale;
 out.pelvis=U.add(out.root,[rp[0]*m.heightScale,rp[1]*ps+(mod.pelvisHeightBiasM||0),rp[2]*m.heightScale+(mod.comBiasForwardM||0)]);
 const lengths=targetLengths(m);
 function walk(parent){for(const child of (CHILDREN[parent]||[])){const pair=parent+'->'+child,d=directionBias(U.sub(canon[child],canon[parent]),pair,mod,action);out[child]=U.add(out[parent],U.mul(d,lengths[pair]));walk(child)}}
 walk('pelvis');
 return {pose:out,lengths};
}
function translatePose(p,d){return U.translatePose(p,d)}
function floorAnchor(pose,canon,action,floorY,m){
 if(!['idle','walk','run','conversation','dance','carry','press','pickup','place','stand'].includes(action))return {pose,applied:false,delta:[0,0,0]};
 const cmin=Math.min(canon.ankle_l?.[1]??99,canon.ankle_r?.[1]??99,canon.toe_l?.[1]??99,canon.toe_r?.[1]??99);
 if(action==='run'&&cmin>.19)return {pose,applied:false,delta:[0,0,0],reason:'flight_phase'};
 const tmin=Math.min(pose.ankle_l[1],pose.ankle_r[1],pose.toe_l[1],pose.toe_r[1]);
 const target=floorY+Math.max(0.018,cmin*(m.footScale||m.legScale)); const dy=target-tmin;
 return {pose:translatePose(pose,[0,dy,0]),applied:Math.abs(dy)>1e-9,delta:[0,dy,0]};
}
function actorLocalPoint(world,origin,m,kind='hand',mod={}){
 const q=U.sub(world,origin),hs=Math.max(.45,kind==='seat'?m.legScale:m.heightScale),handTarget=clamp(.90+.10*(mod.handTargetScale||1),.93,1.02),rs=Math.max(.45,kind==='hand'?m.armScale*handTarget:m.heightScale);
 return [q[0]/rs,q[1]/hs,q[2]/rs];
}
function proxyRequest(req,m,origin,mod){const r=clone(req);r.action=req.action;
 if(r.grip?.position)r.grip.position=actorLocalPoint(r.grip.position,origin,m,'hand',mod);
 if(r.button?.position)r.button.position=actorLocalPoint(r.button.position,origin,m,'hand',mod);
 if(r.gazeTarget){const q=U.sub(r.gazeTarget,origin),gy=Math.max(.45,m.heightScale*clamp(.90+.10*(mod.headGazeHeightScale||1),.94,1.02));r.gazeTarget=[q[0]/Math.max(.45,m.heightScale),q[1]/gy,q[2]/Math.max(.45,m.heightScale)];}
 if(r.seat?.seatCenter){r.seat.seatCenter=actorLocalPoint(r.seat.seatCenter,origin,m,'seat',mod);r.seat.floorY=(r.seat.floorY??0-origin[1])/m.legScale;r.seat.ankleHeight=(r.seat.ankleHeight??.103)/(m.footScale||m.legScale);}
 return r;
}
function actionMap(a){return ({low_pickup:'pickup',table_pickup:'pickup',high_reach:'high_reach',heavy_carry:'carry',conversation:'conversation'}[a]||a)}
function pickupTierLabel(y){y=+y||0;if(y<=.28)return 'floor';if(y<=.74)return y<=.36?'low':'mid';if(y<.86)return 'table';return 'high'}
function wristKey(side){return side==='left'?'wrist_l':'wrist_r'}
function shoulderKey(side){return side==='left'?'shoulder_l':'shoulder_r'}
function elbowKey(side){return side==='left'?'elbow_l':'elbow_r'}
function stageUpperBodyToward(pose,side,target,maxStage=.03){
 const sh=shoulderKey(side),el=elbowKey(side),wk=wristKey(side),armMax=dist(pose[sh],pose[el])+dist(pose[el],pose[wk]),d0=dist(pose[sh],target);
 if(d0<=armMax+2e-5)return {ok:true,pose,stageMeters:0,postStageReachM:d0,armMaxM:armMax,mode:'none'};
 const dir=U.unit(U.sub(target,pose[sh])),shoulderOffset=U.sub(pose[sh],pose.chest),desiredShoulder=U.sub(target,U.mul(dir,armMax-2e-5));let desiredChest=U.sub(desiredShoulder,shoulderOffset);
 const L1=dist(pose.pelvis,pose.spine),L2=dist(pose.spine,pose.chest),rMin=Math.abs(L1-L2)+1e-6,rMax=L1+L2-1e-6;
 function projectAnnulus(point){const v=U.sub(point,pose.pelvis),r=U.len(v),fallback=U.unit(U.sub(pose.chest,pose.pelvis)),u=r>1e-9?U.unit(v):fallback;return U.add(pose.pelvis,U.mul(u,clamp(r,rMin,rMax)));}
 desiredChest=projectAnnulus(desiredChest);
 let delta=U.sub(desiredChest,pose.chest),stage=U.len(delta);if(stage>maxStage){desiredChest=U.add(pose.chest,U.mul(U.unit(delta),maxStage));desiredChest=projectAnnulus(desiredChest);delta=U.sub(desiredChest,pose.chest);stage=U.len(delta);}
 const sol=U.setChain(pose,'pelvis','spine','chest',desiredChest);if(!sol.ok)return {ok:false,pose,reason:'TORSO_CHAIN_CANNOT_STAGE',detail:sol,maxStage,reachableAnnulus:[rMin,rMax]};
 const p=sol.pose,actualDelta=U.sub(p.chest,pose.chest);for(const k of ['neck','head','clavicle_l','shoulder_l','elbow_l','wrist_l','clavicle_r','shoulder_r','elbow_r','wrist_r'])p[k]=U.add(pose[k],actualDelta);
 const d=dist(p[sh],target),need=Math.max(0,d-armMax);return {ok:need<=2e-5,pose:p,reason:need<=2e-5?null:'UPPER_BODY_STAGE_RESIDUAL',need,stageMeters:U.len(actualDelta),maxStage,postStageReachM:d,armMaxM:armMax,mode:'analytic-minimum-reach'};
}
function stageShoulderGirdleToward(pose,side,target,maxStage=.04){
 const ck='clavicle_'+(side==='left'?'l':'r'),sh=shoulderKey(side),el=elbowKey(side),wk=wristKey(side),armMax=dist(pose[sh],pose[el])+dist(pose[el],pose[wk]),d=dist(pose[sh],target),need=Math.max(0,d-armMax);
 if(need<=2e-5)return {ok:true,pose,stageMeters:0,postStageReachM:d,armMaxM:armMax};
 if(maxStage<=1e-8)return {ok:false,reason:'SHOULDER_GIRDLE_STAGE_EXCEEDS_BOUND',need,maxStage};
 const oldShoulder=pose[sh].slice(),dir=U.unit(U.sub(target,oldShoulder)),requested=Math.min(maxStage,need+2e-5);let shoulderTarget=U.add(oldShoulder,U.mul(dir,requested));
 const L1=dist(pose.chest,pose[ck]),L2=dist(pose[ck],pose[sh]),cv=U.sub(shoulderTarget,pose.chest),r=U.len(cv),rMin=Math.abs(L1-L2)+1e-6,rMax=L1+L2-1e-6;
 if(r<rMin||r>rMax)shoulderTarget=U.add(pose.chest,U.mul(U.unit(cv),clamp(r,rMin,rMax)));
 const sol=U.setChain(pose,'chest',ck,sh,shoulderTarget);if(!sol.ok)return {ok:false,reason:'SHOULDER_GIRDLE_CANNOT_STAGE',detail:sol,need,maxStage,reachableAnnulus:[rMin,rMax]};
 const p=sol.pose,delta=U.sub(p[sh],oldShoulder),actual=U.len(delta);p[el]=U.add(pose[el],delta);p[wk]=U.add(pose[wk],delta);
 const post=dist(p[sh],target);return {ok:post<=armMax+2e-5,pose:p,stageMeters:actual,delta,postStageReachM:post,armMaxM:armMax,reason:post<=armMax+2e-5?null:'SHOULDER_GIRDLE_RESIDUAL'};
}
function stageSupportedBodyToward(pose,side,target,maxStage=.08){
 const sh=shoulderKey(side),el=elbowKey(side),wk=wristKey(side),armMax=dist(pose[sh],pose[el])+dist(pose[el],pose[wk]),d=dist(pose[sh],target),need=Math.max(0,d-armMax-CORRECTION_CAP+2e-5);
 if(need<=0)return {ok:true,pose,stageMeters:0,postStageReachM:d,armMaxM:armMax};
 const desired=Math.min(maxStage,need),dir=U.unit(U.sub(target,pose[sh])),bodyKeys=['pelvis','spine','chest','neck','head','clavicle_l','shoulder_l','elbow_l','wrist_l','clavicle_r','shoulder_r','elbow_r','wrist_r','hip_l','knee_l','ankle_l','toe_l','hip_r','knee_r','ankle_r','toe_r'];
 for(let scale=1,tries=0;tries<7;tries++,scale*=.6){const delta=U.mul(dir,desired*scale),p=clone(pose),ankles={l:pose.ankle_l.slice(),r:pose.ankle_r.slice()},toes={l:pose.toe_l.slice(),r:pose.toe_r.slice()};for(const k of bodyKeys)p[k]=U.add(pose[k],delta);let ok=true;
  for(const s of ['l','r']){const sol=stableFamilyLeg(p,s,ankles[s],pose);if(!sol.ok){ok=false;break;}Object.assign(p,sol.pose);p['toe_'+s]=toes[s].slice();}
  if(!ok)continue;const post=dist(p[sh],target);if(post<d-1e-8)return {ok:true,pose:p,stageMeters:U.len(delta),delta,postStageReachM:post,armMaxM:armMax,feetHeld:true,mode:'supported-pelvis-leg-stage'};
 }
 return {ok:false,pose,reason:'SUPPORTED_BODY_STAGE_UNREACHABLE',need,maxStage,postStageReachM:d,armMaxM:armMax};
}
function solveArmWithFinalResidual(pose,side,target,cap=CORRECTION_CAP){const sh=shoulderKey(side),el=elbowKey(side),wk=wristKey(side),L1=dist(pose[sh],pose[el]),L2=dist(pose[el],pose[wk]),d=dist(pose[sh],target),rMin=Math.abs(L1-L2)+1e-6,rMax=L1+L2-1e-6;if(d>=rMin&&d<=rMax){const s=U.setChain(pose,sh,el,wk,target);if(s.ok)return {ok:true,pose:s.pose,residualM:dist(s.pose[wk],target),clamped:false};}const residual=d>rMax?d-rMax:rMin-d;if(residual>cap+1e-9)return {ok:false,residualM:residual,cap,reach:d,reachableAnnulus:[rMin,rMax]};const dir=d>1e-9?U.unit(U.sub(target,pose[sh])):U.unit(U.sub(pose[wk],pose[sh])),r=clamp(d,rMin,rMax),reachable=U.add(pose[sh],U.mul(dir,r));const s=U.setChain(pose,sh,el,wk,reachable);if(!s.ok)return {ok:false,residualM:residual,cap,detail:s,reach:d,reachableAnnulus:[rMin,rMax]};return {ok:true,pose:s.pose,residualM:dist(s.pose[wk],target),clamped:true,requestedTarget:target,reachableTarget:reachable};}
function correctWrist(pose,side,target,semanticCap=CORRECTION_CAP,stageCap=.12){
 const wk=wristKey(side),gap=dist(pose[wk],target);if(gap<=1e-8)return {pose,gap,semanticRetargetMeters:0,finalResidualM:0,applied:false,upperBodyStageMeters:0,supportedBodyStageMeters:0};
 let exact=U.setChain(pose,shoulderKey(side),elbowKey(side),wk,target);if(exact.ok)return {pose:exact.pose,gap,semanticRetargetMeters:gap,semanticCap,finalResidualM:dist(exact.pose[wk],target),applied:true,upperBodyStageMeters:0,supportedBodyStageMeters:0};
 const stage=stageUpperBodyToward(pose,side,target,stageCap),torsoPose=stage.pose||pose,supported=stageSupportedBodyToward(torsoPose,side,target,Math.min(.10*stageCap/.35,.10));
 const candidates=[{pose:pose,name:'none',stageM:0},{pose:torsoPose,name:'torso',stageM:stage.stageMeters||0},{pose:supported.pose||torsoPose,name:'torso+supported',stageM:(stage.stageMeters||0)+(supported.stageMeters||0)}];
 candidates.sort((a,b)=>dist(a.pose[shoulderKey(side)],target)-dist(b.pose[shoulderKey(side)],target));
 for(const c of candidates){exact=U.setChain(c.pose,shoulderKey(side),elbowKey(side),wk,target);if(exact.ok)return {pose:exact.pose,gap,semanticRetargetMeters:gap,semanticCap,finalResidualM:dist(exact.pose[wk],target),applied:true,upperBodyStageMeters:c.name==='torso'||c.name==='torso+supported'?(stage.stageMeters||0):0,supportedBodyStageMeters:c.name==='torso+supported'?(supported.stageMeters||0):0,stageMode:c.name};const bounded=solveArmWithFinalResidual(c.pose,side,target,CORRECTION_CAP);if(bounded.ok&&bounded.residualM<=CORRECTION_CAP+1e-9)return {pose:bounded.pose,gap,semanticRetargetMeters:gap,semanticCap,finalResidualM:bounded.residualM,applied:true,upperBodyStageMeters:c.name==='torso'||c.name==='torso+supported'?(stage.stageMeters||0):0,supportedBodyStageMeters:c.name==='torso+supported'?(supported.stageMeters||0):0,reachableClampApplied:!!bounded.clamped,stageMode:c.name};}
 const best=candidates[0],attempt=solveArmWithFinalResidual(best.pose,side,target,CORRECTION_CAP);return {blocked:true,failure:'BODY_REPOSITION_REQUIRED',detail:exact,gap,stage,supported,bestStageMode:best.name,finalResidualAttempt:attempt,requestBodyReposition:true};
}
function desiredPickupWrist(req){if(!req.grip?.position)return null;const n=U.unit(req.grip.approachNormal||[0,0,-1]),off=+(req.grip.palmOffset??.075);return U.add(req.grip.position,U.mul(n,off));}
function desiredPressWrist(req,state){if(!req.button?.position)return null;const n=U.unit(req.button.normal||[0,0,-1]),depth=+(req.button.depth??.012),amount=state.button?.pressAmount||0,hand=+(req.button.handLength??.105),depressed=U.sub(req.button.position,U.mul(n,depth*amount));return U.add(depressed,U.mul(n,hand));}
function supportSegmentError(pose,lengths){let worst=0,pair=null;for(const [k,L] of Object.entries(lengths)){const [a,b]=k.split('->');const e=Math.abs(dist(pose[a],pose[b])-L);if(e>worst){worst=e;pair=k}}return {worst,pair};}
function comfortReachScale(mod){return clamp(.82+.10*(mod.reachEnvelopeScale||1)+.08*(mod.interactionDistanceScale||1),.84,1.14);}
function applySwingFootClearance(pose,canon,action,mod){if(!['walk','run'].includes(action))return {pose,applied:false,deltaM:0};const scale=mod.footClearanceScale||1;if(Math.abs(scale-1)<1e-9)return {pose,applied:false,deltaM:0};const yl=Math.min(canon.ankle_l?.[1]??99,canon.toe_l?.[1]??99),yr=Math.min(canon.ankle_r?.[1]??99,canon.toe_r?.[1]??99),swing=yl>yr?'l':'r',support=swing==='l'?'r':'l',ak='ankle_'+swing,toe='toe_'+swing,base=Math.max(0,(canon[ak]?.[1]??0)-Math.min(canon['ankle_'+support]?.[1]??0,canon['toe_'+support]?.[1]??0));if(base<.025)return {pose,applied:false,deltaM:0,reason:'contact_or_double_support'};const delta=clamp(base*(scale-1),-.025,.025);if(Math.abs(delta)<1e-6)return {pose,applied:false,deltaM:0};const target=U.add(pose[ak],[0,delta,0]),before=pose[ak].slice(),sol=stableFamilyLeg(pose,swing,target,pose);if(!sol.ok)return {pose,applied:false,deltaM:0,reason:'leg_chain_bound'};let p=sol.pose,actual=U.sub(p[ak],before);p[toe]=U.add(p[toe],actual);return {pose:p,applied:true,deltaM:actual[1],swingSide:swing};}
function estimateReach(req,m,mod,origin){const idle=E.sample({action:'idle'},0);const rec=reconstruct(idle.pose3d,m,mod,'idle',origin).pose;const side=req.activeHand||'right',sh=rec[shoulderKey(side)],target=req.grip?desiredPickupWrist(req):req.button?desiredPressWrist(req,{button:{pressAmount:0}}):req.target;
 if(!target)return {reachable:true,reason:'NO_EXPLICIT_EFFECTOR_TARGET'}; const physical=(REF[shoulderKey(side)+'->'+elbowKey(side)]||.274)*m.armScale+(REF[elbowKey(side)+'->'+wristKey(side)]||.273)*m.armScale,max=physical*comfortReachScale(mod); const d=dist(sh,target),vertical=Math.abs(target[1]-sh[1]);
 if(vertical>max+CORRECTION_CAP)return {reachable:false,failure:'VERTICAL_TARGET_UNREACHABLE',distance:d,maxReach:max,verticalDelta:vertical,repositionPossible:false};
 if(d<=max+CORRECTION_CAP)return {reachable:true,distance:d,maxReach:max,margin:max-d};
 const h=[target[0]-sh[0],0,target[2]-sh[2]],hm=U.len(h),allowedH=Math.sqrt(Math.max(0,max*max-(target[1]-sh[1])**2)),need=Math.max(0,hm-allowedH*.92);const shift=hm>1e-9?U.mul(U.unit(h),need):[0,0,0];
 return {reachable:false,failure:'BODY_REPOSITION_REQUIRED',distance:d,maxReach:max,repositionPossible:true,recommendedOriginShift:shift};
}
function seatReachability(req,m,mod){if(!req.seat?.seatCenter)return {reachable:true};const floor=req.seat.floorY??0,h=req.seat.seatCenter[1]-floor,ideal=.48*m.legScale,ratio=h/Math.max(.15,ideal),approachScale=mod?.seatApproachScale||1,sitDepthScale=mod?.sitDepthScale||1;if(ratio<.62)return {reachable:false,failure:'CHAIR_TOO_LOW_FOR_MORPHOLOGY',seatHeight:h,ideal,ratio,approachScale,sitDepthScale};if(ratio>1.38)return {reachable:false,failure:'CHAIR_TOO_HIGH_FOR_FLOOR_AWARE_SEAT',seatHeight:h,ideal,ratio,approachScale,sitDepthScale};return {reachable:true,seatHeight:h,ideal,ratio,approachScale,sitDepthScale,recommendedApproachDistanceM:.55*m.heightScale*approachScale};}
function reachability(req,m,mod,origin){const a=actionMap(req.action),comfort=comfortReachScale(mod);if(['sit','stand','sit_idle'].includes(a))return seatReachability(req,m,mod);if(a==='carry'&&req.grip?.object?.size){const dims=req.grip.object.size.map(Number),largest=Math.max(...dims),arm=(REF['shoulder_r->elbow_r']+REF['elbow_r->wrist_r'])*m.armScale,maxProp=arm*1.72*clamp(.90+.10*(mod.reachEnvelopeScale||1),.94,1.02);if(largest>maxProp)return {reachable:false,failure:'PROP_TOO_LARGE_FOR_CARRY_ENVELOPE',largestDimension:largest,maxSupportedDimension:maxProp};}if(a==='pickup'&&req.grip?.position){const target=desiredPickupWrist(req),local=U.sub(target,origin),h=Math.hypot(local[0],local[2]),floor=req.floorY??origin[1],maxH=.90*Math.max(.55,m.heightScale)*comfort,maxY=floor+1.26*m.heightScale*clamp(.90+.10*(mod.reachEnvelopeScale||1),.94,1.02);if(target[1]<floor-.03)return {reachable:false,failure:'TARGET_BELOW_FLOOR',target};if(h>maxH)return {reachable:false,failure:'BODY_REPOSITION_REQUIRED',repositionPossible:true,recommendedOriginShift:U.mul(U.unit([local[0],0,local[2]]),Math.max(0,h-maxH*.9))};if(target[1]>maxY)return {reachable:false,failure:'VERTICAL_TARGET_UNREACHABLE',targetY:target[1],maxY,repositionPossible:false};return {reachable:true,reason:target[1]<=floor+.52*m.heightScale?'WHOLE_BODY_LOW_PICKUP_ENVELOPE':'AUTHORED_PICKUP_DONOR_ENVELOPE',horizontalDistance:h,maxHorizontal:maxH,maxY,reachEnvelopeScale:mod.reachEnvelopeScale,interactionDistanceScale:mod.interactionDistanceScale};}if(a==='press'&&req.button?.position){const p=req.button.position,local=U.sub(p,origin),h=Math.hypot(local[0],local[2]),floor=req.floorY??origin[1],maxH=.86*Math.max(.55,m.heightScale)*comfort,maxY=floor+1.34*m.heightScale*clamp(.90+.10*(mod.reachEnvelopeScale||1),.94,1.02);if(p[1]<floor+.15*m.heightScale||p[1]>maxY)return {reachable:false,failure:'VERTICAL_TARGET_UNREACHABLE',targetY:p[1],maxY};if(h>maxH)return {reachable:false,failure:'BODY_REPOSITION_REQUIRED',repositionPossible:true};return {reachable:true,reason:'PRESS_DONOR_STAGING_ENVELOPE',reachEnvelopeScale:mod.reachEnvelopeScale,interactionDistanceScale:mod.interactionDistanceScale};}if(req.target)return estimateReach(req,m,mod,origin);return {reachable:true,interactionDistanceScale:mod.interactionDistanceScale};}
function needsSemanticContactRetarget(mapped,phase){if(mapped==='pickup')return ['pregrasp','contact','close'].includes(phase||'');if(mapped==='place')return ['precontact','release'].includes(phase||'');return false;}
function restoreWorldInteraction(state,req,pose,side){const out=state;if(req.grip?.position&&out.prop){const n=U.unit(req.grip.approachNormal||[0,0,-1]),off=+(req.grip.palmOffset??.075),handOffset=U.mul(n,-off);if(out.prop.owner==='world')out.prop.position=req.grip.position.slice();else out.prop.position=U.add(pose[wristKey(side)],handOffset);out.prop.handOffset=handOffset;}
 if(req.button?.position&&out.button){out.button.position=req.button.position.slice();const n=U.unit(req.button.normal||[0,0,-1]),depth=+(req.button.depth??.012),amt=out.button.pressAmount||0;out.button.depressedPosition=U.sub(req.button.position,U.mul(n,depth*amt));}
 return out;}
function bindSeat(pose,seat,m,mod){const ch=clone(seat||{}),center=vec(ch.seatCenter,[0,.48,0]),normal=U.unit(vec(ch.seatNormal,[0,1,0])),forward=U.unit(vec(ch.seatForward,[0,0,1])),floor=+(ch.floorY??0),clear=+(ch.pelvisClearance??(.06*m.heightScale)),ankleH=+(ch.ankleHeight??(.103*(m.footScale||m.legScale))),depth=+(ch.depth??.44),depthOffset=clamp(((mod?.sitDepthScale||1)-1)*depth*.28,-.04,.04),targetPelvis=U.add(U.add(center,U.mul(forward,depthOffset)),U.mul(normal,clear));let p=translatePose(pose,U.sub(targetPelvis,pose.pelvis)),feet={};for(const side of ['l','r']){const ak='ankle_'+side,toe='toe_'+side,before=p[ak].slice(),target=[p[ak][0],floor+ankleH,p[ak][2]],sol=stableFamilyLeg(p,side,target,p);feet[side]={ok:sol.ok,reason:sol.reason||null,target};if(!sol.ok)return {blocked:true,failure:'CHAIR_BINDING_LEG_UNREACHABLE',side,detail:sol};p=sol.pose;const d=U.sub(p[ak],before);p[toe]=U.add(p[toe],d);}const butt=U.sub(p.pelvis,U.mul(normal,clear)),bc=U.sub(butt,center),gap=Math.abs(bc[0]*normal[0]+bc[1]*normal[1]+bc[2]*normal[2]);return {blocked:false,pose:p,seat:{...ch,seatCenter:center,pelvisClearance:clear,ankleHeight:ankleH,depth,depthOffset},contactGap:gap,feet,targetPelvis,depthOffset,recommendedApproachDistanceM:.55*m.heightScale*(mod?.seatApproachScale||1)};}
function previewRetarget(coreState,m,mod,mapped,origin,floor){const rec=reconstruct(coreState.pose3d,m,mod,mapped,origin);const anch=floorAnchor(rec.pose,coreState.pose3d,mapped,floor,m);return {pose:anch.pose,rec,anch};}
function calibratedCoreSample(coreReq,req,m,mod,origin,mapped,coreT){const state=E.sample(coreReq,coreT);return {state,coreReq,iterations:0,lastGap:null};}
function sample(input,t,library){const family=input.family,m=input.morphology,req=clone(input.request||{}),v=validateMorphology(m);if(!v.ok)return {engine:'NexStickCastPhaseD',version:VERSION,blocked:true,failure:v.failure,diagnostics:v};const mod=library?.families?.[family];if(!mod)return {engine:'NexStickCastPhaseD',version:VERSION,blocked:true,failure:'UNKNOWN_FAMILY_MODIFIER',family};
 const origin=vec(req.actorOrigin);const mapped=actionMap(req.action);
 const rr=reachability(req,m,mod,origin);if(!rr.reachable)return {engine:'NexStickCastPhaseD',version:VERSION,action:req.action,blocked:true,failure:rr.failure,reachability:rr,requestBodyReposition:rr.repositionPossible===true};
 let coreReq=proxyRequest({...req,action:mapped},m,origin,mod);let pickupDonorTier=mapped==='pickup'&&coreReq.grip?.position?pickupTierLabel(coreReq.grip.position[1]):null;if(req.action==='heavy_carry'){coreReq.grip=coreReq.grip||{};coreReq.grip.loadClass='heavy'}
 const cadence=['walk','run'].includes(mapped)?mod.cadenceBias:1,personalityScale=Number.isFinite(req.timeScale)?req.timeScale:1,totalTimeScale=clamp(cadence*personalityScale,.55,1.65);coreReq.timeScale=totalTimeScale; if(['walk','run'].includes(mapped)){const explicit=Number.isFinite(req.speedMps),base=mapped==='walk'?1.1:2.1,worldSpeed=explicit?req.speedMps:(base*(mod.strideLengthScale||1));coreReq.worldSpeedMps=worldSpeed;coreReq.speedMps=worldSpeed/totalTimeScale;} const coreT=(+t||0);
 const calibrated=calibratedCoreSample(coreReq,req,m,mod,origin,mapped,coreT);coreReq=calibrated.coreReq;let state=calibrated.state; if(!state||state.blocked)return {...state,engine:'NexStickCastPhaseD',phaseDVersion:VERSION,sourceEngine:'5.1.0-skin-safe-angular-continuity',family,coreFailure:state?.failure,calibration:{iterations:calibrated.iterations,lastGap:calibrated.lastGap}};
 const floorCheck=req.seat?.floorY??req.floorY??origin[1];if(['press','pickup','place','stand','carry'].includes(mapped)){const minFoot=Math.min(state.pose3d.ankle_l[1],state.pose3d.ankle_r[1],state.pose3d.toe_l[1],state.pose3d.toe_r[1]);if(minFoot<floorCheck-.006)return {engine:'NexStickCastPhaseD',version:VERSION,action:req.action,blocked:true,failure:'CORE_SUPPORT_CONTACT_CONFLICT',sourceEngine:'5.1.0-skin-safe-angular-continuity',diagnostics:{coreMinFootY:minFoot,floorY:floorCheck,penetrationM:floorCheck-minFoot,coreContact:state.contact},visibleFailure:true};}
 if(['walk','run'].includes(mapped)){state.coreTime=coreT;state.time=+t||0;}
 const rec=reconstruct(state.pose3d,m,mod,mapped,origin);let pose=rec.pose;const footClearance=applySwingFootClearance(pose,state.pose3d,mapped,mod);pose=footClearance.pose;const floor=req.seat?.floorY??req.floorY??origin[1];let anch=floorAnchor(pose,state.pose3d,mapped,floor,m);pose=anch.pose;let seatBinding=null;if(['sit','stand','sit_idle'].includes(mapped)&&req.seat){seatBinding=bindSeat(pose,req.seat,m,mod);if(seatBinding.blocked)return {engine:'NexStickCastPhaseD',version:VERSION,action:req.action,blocked:true,failure:seatBinding.failure,seatBinding};pose=seatBinding.pose;state.seat=seatBinding.seat;state.contact={...(state.contact||{}),gap:seatBinding.contactGap};anch={pose,applied:true,delta:[0,0,0],reason:'seat_binding_supersedes_floor_anchor'};}
 const side=req.activeHand||'right';let correction={applied:false,gap:0};
 if(needsSemanticContactRetarget(mapped,state.phase)){const target=desiredPickupWrist(req);if(target){correction=correctWrist(pose,side,target,.65*m.armScale,.35*m.heightScale);if(correction.blocked)return {engine:'NexStickCastPhaseD',version:VERSION,action:req.action,blocked:true,failure:correction.failure,correction,reachability:rr};pose=correction.pose;}}
 if(mapped==='press'&&['orient','press','hold'].includes(state.phase)){const target=desiredPressWrist(req,state);if(target){correction=correctWrist(pose,side,target,.65*m.armScale,.35*m.heightScale);if(correction.blocked)return {engine:'NexStickCastPhaseD',version:VERSION,action:req.action,blocked:true,failure:correction.failure,correction,reachability:rr};pose=correction.pose;}}
 state.pose3d=pose;restoreWorldInteraction(state,req,pose,side);if(state.prop?.position&&mapped==='carry')state.prop.position=U.add(state.prop.position,[origin[0],origin[1]+(mod.propCarryHeightBiasM||0),origin[2]]);
 const seg=supportSegmentError(pose,rec.lengths);if(seg.worst>1.5e-6)return {engine:'NexStickCastPhaseD',version:VERSION,action:req.action,blocked:true,failure:'TARGET_SEGMENT_LENGTH_DRIFT',metrics:{segment:seg}};
 return {...state,engine:'NexStickCastPhaseD',phaseDVersion:VERSION,sourceEngine:'5.1.0-skin-safe-angular-continuity',family,morphologyId:m.id,originalAction:req.action,blocked:false,adaptation:{modifiers:clone(mod),cadenceApplied:cadence,timeScaleApplied:totalTimeScale,strideScaleApplied:['walk','run'].includes(mapped)?mod.strideLengthScale:1,footClearanceApplied:footClearance,restingStanceScaleApplied:['idle','conversation','carry'].includes(mapped)?mod.restingStanceScale:1,handTargetScaleApplied:mod.handTargetScale,headGazeHeightScaleApplied:mod.headGazeHeightScale,turnRadiusScale:mod.turnRadiusScale,interactionDistanceScale:mod.interactionDistanceScale,reachEnvelopeScale:mod.reachEnvelopeScale,floorAnchor:anch,seatBinding:seatBinding&&{contactGap:seatBinding.contactGap,feet:seatBinding.feet,targetPelvis:seatBinding.targetPelvis,depthOffset:seatBinding.depthOffset,recommendedApproachDistanceM:seatBinding.recommendedApproachDistanceM},finalContactCorrection:correction,targetSegmentError:seg,reachability:rr,targetCalibration:{iterations:calibrated.iterations,lastGapBeforeFinalCorrection:calibrated.lastGap,pickupDonorTier},hardSafety:{fixedTargetSegmentLengths:true,maxFinalContactCorrectionMeters:CORRECTION_CAP,noLimbStretch:true,noOwnershipTeleport:true,noFootTeleport:true,failClosed:true}}};
}
function handoffPair(input,t,library){const family=input.family,m=input.morphology,v=validateMorphology(m);if(!v.ok)return {blocked:true,failure:v.failure};const mod=library?.families?.[family];if(!mod)return {blocked:true,failure:'UNKNOWN_FAMILY_MODIFIER'};const spec=clone(input.spec||{}),preferred=1.12*(mod.partnerSpacingScale||1),minPartner=Math.max(.42*m.heightScale,preferred*.58),maxPartner=preferred*1.42;if(Number.isFinite(spec.partnerDistanceM)){if(spec.partnerDistanceM<minPartner)return {engine:'NexStickCastPhaseD',version:VERSION,action:'handoff_pair',blocked:true,failure:'PARTNER_TOO_CLOSE',partnerDistanceM:spec.partnerDistanceM,minPartner};if(spec.partnerDistanceM>maxPartner)return {engine:'NexStickCastPhaseD',version:VERSION,action:'handoff_pair',blocked:true,failure:'PARTNER_TOO_FAR_BODY_REPOSITION_REQUIRED',partnerDistanceM:spec.partnerDistanceM,maxPartner,requestBodyReposition:true};}const core=E.handoffPair(t,spec);if(core.blocked)return {...core,engine:'NexStickCastPhaseD',phaseDVersion:VERSION};
 const contact=E.handoffPair(.9,spec);const rg=reconstruct(contact.actors.giver.pose3d,m,mod,'handoff_pair',[0,0,0]),rr=reconstruct(contact.actors.receiver.pose3d,m,mod,'handoff_pair',[0,0,0]);const gh=rg.pose[wristKey(spec.giverHand||'right')],rh=rr.pose[wristKey(spec.receiverHand||'left')],mid=U.mix(gh,rh,.5),gd=U.sub(mid,gh),rd=U.sub(mid,rh);
 const gnow=reconstruct(core.actors.giver.pose3d,m,mod,'handoff_pair',gd),rnow=reconstruct(core.actors.receiver.pose3d,m,mod,'handoff_pair',rd);const gseg=supportSegmentError(gnow.pose,gnow.lengths),rseg=supportSegmentError(rnow.pose,rnow.lengths);const gap=dist(gnow.pose[wristKey(spec.giverHand||'right')],rnow.pose[wristKey(spec.receiverHand||'left')]);const sep=dist(gnow.pose.pelvis,rnow.pose.pelvis);
 if(core.phase==='shared_contact'&&gap>CORRECTION_CAP)return {engine:'NexStickCastPhaseD',version:VERSION,action:'handoff_pair',blocked:true,failure:'HANDOFF_CONTACT_GAP_AFTER_RETARGET',gap,cap:CORRECTION_CAP};if(sep<.50*m.heightScale)return {engine:'NexStickCastPhaseD',version:VERSION,action:'handoff_pair',blocked:true,failure:'PARTNER_SPACING_COLLAPSED',pelvisSeparation:sep};
 core.actors.giver.pose3d=gnow.pose;core.actors.receiver.pose3d=rnow.pose;core.pelvisSeparation=sep;if(core.prop?.position){if(core.prop.owner==='shared')core.prop.position=U.mix(gnow.pose[wristKey(spec.giverHand||'right')],rnow.pose[wristKey(spec.receiverHand||'left')],.5);else if(core.prop.owner==='giver')core.prop.position=gnow.pose[wristKey(spec.giverHand||'right')];else if(core.prop.owner==='receiver')core.prop.position=rnow.pose[wristKey(spec.receiverHand||'left')];}
 return {...core,engine:'NexStickCastPhaseD',phaseDVersion:VERSION,sourceEngine:'5.1.0-skin-safe-angular-continuity',family,blocked:false,adaptation:{partnerSpacingScale:mod.partnerSpacingScale,preStagingOffsets:{giver:gd,receiver:rd},sharedContactGap:gap,targetSegmentError:{giver:gseg,receiver:rseg},hardSafety:{ownershipTruthInherited:true,noOwnershipTeleport:true,noLimbStretch:true}}};
}

function stableFamilyLeg(pose,side,target,referencePose){const hip='hip_'+side,knee='knee_'+side,ak='ankle_'+side,A=pose[hip],B=pose[knee],C=pose[ak],T=target,ref=referencePose||pose,l1=U.len(U.sub(B,A)),l2=U.len(U.sub(C,B)),at=U.sub(T,A),d0=U.len(at);if(d0<1e-10)return {ok:false,reason:'degenerate_target',pose};if(d0>l1+l2+1e-8||d0<Math.abs(l1-l2)-1e-8)return {ok:false,reason:'unreachable_chain_geometry',pose,reach:d0,max:l1+l2,min:Math.abs(l1-l2)};const e=U.unit(at),x=(l1*l1-l2*l2+d0*d0)/(2*d0),h=Math.sqrt(Math.max(0,l1*l1-x*x));let rv=U.sub(ref["knee_"+side]||B,ref["hip_"+side]||A),perp=U.sub(rv,U.mul(e,U.dot(rv,e)));if(U.len(perp)<1e-8){const cur=U.sub(B,A);perp=U.sub(cur,U.mul(e,U.dot(cur,e)))}if(U.len(perp)<1e-8){let n=U.cross(e,U.sub(C,B));if(U.len(n)<1e-8)n=[0,0,1];perp=U.cross(n,e)}perp=U.unit(perp);const joint=U.add(U.add(A,U.mul(e,x)),U.mul(perp,h)),out=Object.fromEntries(Object.entries(pose).map(([k,v])=>[k,Array.isArray(v)?v.slice():v]));out[knee]=joint;out[ak]=T.slice();return {ok:true,pose:out,stableBendPlane:true}}
const ADAPTED_GROUNDED=new Set(['idle','walk','run','turn','conversation','talk','interact','use_item','pickup','place','press','carry','stand','sit','sit_idle','sit_talk','high_reach','captured_reach','give_capture','typing_leanback','presenter_papers','documentary_acting','phone_talk','walk_carry']);
function groundAdaptedLegs(pose,action,floorY=0){
 if(!ADAPTED_GROUNDED.has(action))return {pose,applied:false,corrections:[]};
 let p=Object.fromEntries(Object.entries(pose).map(([k,v])=>[k,Array.isArray(v)?v.slice():v])),corrections=[];
 const globalMin=Math.min(p.ankle_l[1],p.ankle_r[1],p.toe_l[1],p.toe_r[1]);
 if(globalMin>floorY+.085)return {pose:p,applied:false,corrections,reason:'flight_phase'};
 const target=floorY+.008;
 for(const side of ['l','r']){
   const ak='ankle_'+side,toe='toe_'+side,hip='hip_'+side,knee='knee_'+side,min=Math.min(p[ak][1],p[toe][1]);
   if(min>=target)continue;
   const oldA=p[ak].slice(),oldT=p[toe].slice(),goal=U.add(oldA,[0,target-min,0]),sol=stableFamilyLeg(p,side,goal,p);
   if(!sol.ok)return {blocked:true,failure:'FAMILY_SUPPORT_LEG_GROUND_IK_FAILED',side,detail:sol,pose:p,corrections};
   p=sol.pose;const d=U.sub(p[ak],oldA);p[toe]=U.add(oldT,d);corrections.push({side,deltaY:d[1]});
 }
 return {pose:p,applied:corrections.length>0,corrections};
}

function inheritCoreFootPlants(pose,state,m,mod,action){
 if(state?.lowerBodyStabilization?.mode==='stationary-capture-fixed-pelvis-and-stance'&&!state?.transition){return {pose,applied:[{side:'l',ok:true,weight:1,requestedWeight:1,source:'stationary-performance-family-reconstruction'},{side:'r',ok:true,weight:1,requestedWeight:1,source:'stationary-performance-family-reconstruction'}],footPlant:{l:1,r:1},directFamilyStance:true};}
 let p=pose,applied=[],plantOut={l:0,r:0};const plant=state?.footPlant||{};
 const metaFor=side=>{const t=(state?.transitionFootLock||[]).find(x=>x.side===side&&x.ok!==false);if(t)return {anchor:t.target,referencePose3d:t.referencePose3d,source:'transition'};const c=(state?.contactPins?.applied||[]).find(x=>x.side===side&&x.ok!==false);return c?{anchor:c.anchor,referencePose3d:c.referencePose3d,source:'donor'}:null};
 for(const side of ['l','r']){
   const requested=clamp(Number(plant[side])||0,0,1);if(requested<.20)continue;
   const ak='ankle_'+side,toe='toe_'+side,hip='hip_'+side,knee='knee_'+side,meta=metaFor(side);let target=null;
   if(meta?.referencePose3d&&meta?.anchor){const rr=reconstruct(meta.referencePose3d,m,mod,action,[0,0,0]).pose,coreRef=meta.referencePose3d[ak],delta=coreRef?U.sub(meta.anchor,coreRef):[0,0,0];target=U.add(rr[ak],delta);}else if(state.pose3d?.[ak])target=state.pose3d[ak].slice();
   if(!target){applied.push({side,ok:false,weight:0,requestedWeight:requested,reason:'NO_CONTACT_TARGET'});continue;}
   const natural=p[ak].slice(),goal=U.mix(natural,target,requested),oldToe=p[toe].slice(),refPoseForIK=meta?.referencePose3d?reconstruct(meta.referencePose3d,m,mod,action,[0,0,0]).pose:p;let w=requested,sol=null,g=goal;for(let tries=0;tries<7;tries++){sol=stableFamilyLeg(p,side,g,refPoseForIK||p);if(sol.ok)break;w*=.55;g=U.mix(natural,target,w);}if(!sol?.ok){applied.push({side,ok:false,weight:0,requestedWeight:requested,reason:sol?.reason||'UNREACHABLE'});continue;}
   p=sol.pose;const d=U.sub(p[ak],natural);p[toe]=U.add(oldToe,d);plantOut[side]=w;applied.push({side,ok:true,weight:w,requestedWeight:requested,target:g,source:meta?.source||'fallback'});
 }
 return {pose:p,applied,footPlant:plantOut};
}
function adaptedSeatContact(pose,seat,m){
 if(!seat?.seatCenter)return null;const center=vec(seat.seatCenter,[0,.48,0]),normal=U.unit(vec(seat.seatNormal,[0,1,0])),clear=+(seat.pelvisClearance??(.06*m.heightScale)),butt=U.sub(pose.pelvis,U.mul(normal,clear)),d=U.sub(butt,center);return {gapM:Math.abs(d[0]*normal[0]+d[1]*normal[1]+d[2]*normal[2]),butt,center,clearanceM:clear};
}
function adaptState(input,state,library){
 const family=input.family,m=input.morphology,req=clone(input.request||{}),v=validateMorphology(m);if(!v.ok)return {blocked:true,failure:v.failure,diagnostics:v};
 const mod=library?.families?.[family];if(!mod)return {blocked:true,failure:'UNKNOWN_FAMILY_MODIFIER',family};if(!state||state.blocked||!state.pose3d)return state;
 const mapped=actionMap(req.action||state.action||state.originalAction||'idle'),floor=req.seat?.floorY??req.floorY??0,origin=state.pose3d.root?.slice?.()||[0,0,0];
 const rr=reachability(req,m,mod,origin);if(!rr.reachable)return {blocked:true,failure:rr.failure,engine:'NexStickCastPhaseD',phaseDVersion:VERSION,sourceEngine:'5.1.0-skin-safe-angular-continuity',family,reachability:rr,requestBodyReposition:rr.repositionPossible===true};
 const rec=reconstruct(state.pose3d,m,mod,mapped,[0,0,0]);let pose=rec.pose;
 const clearance=applySwingFootClearance(pose,state.pose3d,mapped,mod);pose=clearance.pose;const inheritedPlants=inheritCoreFootPlants(pose,state,m,mod,mapped);pose=inheritedPlants.pose;
 const support=groundAdaptedLegs(pose,mapped,floor);if(support.blocked)return {...support,engine:'NexStickCastPhaseD',phaseDVersion:VERSION,sourceEngine:'5.1.0-skin-safe-angular-continuity',family};pose=support.pose;
 const side=req.activeHand||'right';let correction={applied:false,gap:0};
 if(needsSemanticContactRetarget(mapped,state.phase)){const target=desiredPickupWrist(req);if(target){correction=correctWrist(pose,side,target,.65*m.armScale,.35*m.heightScale);if(correction.blocked)return {...correction,blocked:true,engine:'NexStickCastPhaseD',phaseDVersion:VERSION,family};pose=correction.pose;}}
 if(mapped==='press'&&['orient','press','hold'].includes(state.phase||'')){const target=desiredPressWrist(req,state);if(target){correction=correctWrist(pose,side,target,.65*m.armScale,.35*m.heightScale);if(correction.blocked)return {...correction,blocked:true,engine:'NexStickCastPhaseD',phaseDVersion:VERSION,family};pose=correction.pose;}}
 let out={...state,pose3d:pose,footPlant:inheritedPlants.footPlant};restoreWorldInteraction(out,req,pose,side);
 if(out.prop?.position&&mapped==='carry'&&out.prop.owner!=='world')out.prop.position=U.add(pose[wristKey(side)],out.prop.handOffset||[0,0,0]);
 const seg=supportSegmentError(pose,rec.lengths);if(seg.worst>1.5e-6)return {blocked:true,failure:'TARGET_SEGMENT_LENGTH_DRIFT',engine:'NexStickCastPhaseD',phaseDVersion:VERSION,family,metrics:{segment:seg}};
 const seatContact=adaptedSeatContact(pose,req.seat,m);
 return {...out,engine:'NexStickCastPhaseD',phaseDVersion:VERSION,sourceEngine:'5.1.0-skin-safe-angular-continuity',family,morphologyId:m.id,blocked:false,adaptation:{...(state.adaptation||{}),mode:'post-continuity-state-retarget',rootPreserved:true,worldFacingPreserved:true,ownershipHistoryPreserved:true,modifiers:clone(mod),footClearanceApplied:clearance,inheritedCoreFootPlants:inheritedPlants,supportLegGroundIK:support,finalContactCorrection:correction,seatContact,targetSegmentError:seg,hardSafety:{fixedTargetSegmentLengths:true,maxFinalContactCorrectionMeters:CORRECTION_CAP,noLimbStretch:true,noOwnershipTeleport:true,noRootWarp:true,failClosed:true}}};
}
function contract(){return {name:'NexStickCastPhaseDProportionPerformanceAdapter',version:VERSION,scope:'thin-proportion-aware-performance-adaptation',requires:'NexPerformanceUnifiedV5@5.1.0-skin-safe-angular-continuity',owns:['bounded semantic performance modifiers','Phase-C morphology consumption','reachability/fail-closed staging','target-length retarget reconstruction','post-continuity family state retarget','partner/seat/prop spatial adaptation metadata'],doesNotOwn:['raw morphology','body geometry authoring','core motion generation','new animation libraries','storyboard','Director'],hardRules:{fixedSegmentLengths:true,maxFinalContactCorrectionMeters:CORRECTION_CAP,noLimbStretch:true,noOwnershipTeleport:true,noFootTeleport:true,chairBindingTruth:true,unreachable:'FAIL_CLOSED_OR_REQUEST_BODY_REPOSITION'}}}
root.NexStickCastPhaseDV2={version:VERSION,sample,adaptState,handoffPair,reachability,validateMorphology,targetLengths,contract};
})(typeof window!=='undefined'?window:globalThis);
