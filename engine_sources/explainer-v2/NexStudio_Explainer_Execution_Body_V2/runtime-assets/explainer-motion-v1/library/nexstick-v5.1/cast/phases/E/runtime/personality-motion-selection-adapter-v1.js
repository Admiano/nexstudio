(function(root){'use strict';
const Q=root.NexMotionQueryV3,S=root.NexMotionSamplerV3,B=root.NexMotionBlendV3;
if(!Q||!S||!B)throw new Error('NexPersonalityMotionSelectionV1 requires NexMotionQueryV3, NexMotionSamplerV3 and NexMotionBlendV3');
const VERSION='1.0.0';
const SAFE_POOLS={
  idle:['UAL_idle','KK_Idle_A','KK_Idle_B'],
  walk:['UAL_walk','UAL_walk_formal','KK_Walking_A','KK_Walking_B','KK_Walking_C'],
  present:['UAL_interact','KK_Interact','KK_Use_Item'],
  conversation:['UAL_talk','UAL_idle','KK_Idle_A','KK_Idle_B','UAL_interact','KK_Interact'],
  run:['UAL_jog','UAL_sprint','KK_Running_A','KK_Running_B']
};
const DEFAULT_BOUNDS={
  gestureAmplitude:[.60,1.40],gestureFrequency:[.50,1.50],idleActivity:[.50,1.50],headTiltTendency:[0,1],
  stanceWidth:[.80,1.20],movementEnergy:[.60,1.40],turnSharpness:[.70,1.30],armSwingScale:[.70,1.30],bodyOpenness:[.65,1.35],
  conversationListenerActivity:[.50,1.50]
};
const FEATURE_KEYS=['gestureAmplitude','gestureFrequency','idleActivity','headTiltTendency','stanceWidth','movementEnergy','turnSharpness','armSwingScale','bodyOpenness','conversationListenerActivity'];
const ACTION_WEIGHTS={
  idle:{idleActivity:2.4,bodyOpenness:1.8,stanceWidth:1.0,headTiltTendency:.55,movementEnergy:.8},
  walk:{movementEnergy:2.4,armSwingScale:2.0,stanceWidth:1.15,turnSharpness:.55,bodyOpenness:.65},
  present:{gestureAmplitude:2.6,bodyOpenness:1.7,movementEnergy:1.2,gestureFrequency:.8,turnSharpness:.45},
  conversation:{gestureFrequency:2.0,gestureAmplitude:1.55,conversationListenerActivity:1.45,bodyOpenness:1.0,idleActivity:.65,headTiltTendency:.4},
  run:{movementEnergy:2.5,armSwingScale:1.4,turnSharpness:.6,stanceWidth:.8}
};
const catalogById=new Map(Q.catalog().map(c=>[c.id,c]));
const profileCache=new Map();
function clamp(v,a=0,b=1){return Math.max(a,Math.min(b,v))}
function fnv1a(s){let h=2166136261>>>0;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)>>>0}return h>>>0}
function tieUnit(s){return fnv1a(s)/4294967295}
function vsub(a,b){return [a[0]-b[0],a[1]-b[1],a[2]-b[2]]}
function vlen(a){return Math.hypot(a[0],a[1],a[2])}
function rel(p,j){return vsub(p[j],p.pelvis)}
function angleShoulder(p){const d=vsub(p.shoulder_l,p.shoulder_r);return Math.atan2(d[2],d[0])}
function unwrapDelta(a,b){let d=a-b;while(d>Math.PI)d-=Math.PI*2;while(d<-Math.PI)d+=Math.PI*2;return d}
function sampleCandidate(c,u){const ref=c.source==='kaykit-v3'?c.clip:c.performance;const t=Math.max(0,Math.min(c.duration-1e-6,c.duration*u));return S.sample(ref,t,{footLock:false}).pose3d}
function profile(c){
  if(profileCache.has(c.id))return profileCache.get(c.id);
  const N=9,poses=[];for(let i=0;i<N;i++)poses.push(sampleCandidate(c,i/(N-1)));
  const dynJ=['wrist_l','wrist_r','elbow_l','elbow_r','ankle_l','ankle_r','head'];
  let travel=0,armTravel=0,turn=0,dirChanges=0,prevV=null,openness=0,stance=0,headTilt=0,gestureExtent=0;
  let minWZ=Infinity,maxWZ=-Infinity;
  for(let i=0;i<N;i++){
    const p=poses[i],sh=Math.max(.05,vlen(vsub(p.shoulder_l,p.shoulder_r))),hip=Math.max(.05,vlen(vsub(p.hip_l,p.hip_r)));
    openness+=vlen(vsub(p.wrist_l,p.wrist_r))/sh;
    stance+=Math.abs(p.ankle_l[0]-p.ankle_r[0])/hip;
    const hn=vsub(p.head,p.neck);headTilt+=Math.abs(hn[0])/Math.max(.03,vlen(hn));
    const wl=rel(p,'wrist_l'),wr=rel(p,'wrist_r');
    gestureExtent+=(vlen(vsub(p.wrist_l,p.chest))+vlen(vsub(p.wrist_r,p.chest)))*.5/sh;
    minWZ=Math.min(minWZ,wl[2],wr[2]);maxWZ=Math.max(maxWZ,wl[2],wr[2]);
    if(i){const q=poses[i-1],dt=Math.max(.001,c.duration/(N-1));
      for(const j of dynJ)travel+=vlen(vsub(rel(p,j),rel(q,j)))/dt;
      armTravel+=(vlen(vsub(rel(p,'wrist_l'),rel(q,'wrist_l')))+vlen(vsub(rel(p,'wrist_r'),rel(q,'wrist_r'))))/dt;
      turn+=Math.abs(unwrapDelta(angleShoulder(p),angleShoulder(q)))/dt;
      const v=vsub(rel(p,'wrist_r'),rel(q,'wrist_r'));if(prevV&&((v[0]*prevV[0]+v[1]*prevV[1]+v[2]*prevV[2])<0))dirChanges++;prevV=v;
    }
  }
  const dur=Math.max(.1,c.duration),raw={
    movementEnergy:travel/((N-1)*dynJ.length),idleActivity:travel/((N-1)*dynJ.length),
    armSwingScale:(maxWZ-minWZ)+armTravel/((N-1)*4),turnSharpness:turn/(N-1),
    gestureAmplitude:gestureExtent/N,gestureFrequency:(dirChanges+armTravel*.2)/dur,
    bodyOpenness:openness/N,stanceWidth:stance/N,headTiltTendency:headTilt/N,
    conversationListenerActivity:(travel/((N-1)*dynJ.length))*.55+(headTilt/N)*.45
  };
  profileCache.set(c.id,raw);return raw;
}
function unitTarget(name,value){const b=DEFAULT_BOUNDS[name]||[0,1];return clamp((value-b[0])/(b[1]-b[0]))}
function normalizedProfiles(candidates){
  const raws=candidates.map(profile),mins={},maxs={};
  for(const k of FEATURE_KEYS){mins[k]=Math.min(...raws.map(r=>r[k]));maxs[k]=Math.max(...raws.map(r=>r[k]))}
  return raws.map(raw=>{const out={};for(const k of FEATURE_KEYS){const span=maxs[k]-mins[k];out[k]=span<1e-9?.5:(raw[k]-mins[k])/span}return out});
}
function keyForAction(action){if(action==='talk')return 'conversation';if(action==='interact'||action==='use_item')return 'present';return action}
function candidatePool(action,req={}){
  const key=keyForAction(action),ids=SAFE_POOLS[key];if(!ids)return [];
  let cs=ids.map(id=>catalogById.get(id)).filter(Boolean);
  if(req.source)cs=cs.filter(c=>c.source===req.source);
  if(req.exclude?.length)cs=cs.filter(c=>!req.exclude.includes(c.id)&&!req.exclude.includes(c.clip)&&!req.exclude.includes(c.performance));
  return cs;
}
function personalityScore(c,norm,key,p,req){
  const weights=ACTION_WEIGHTS[key]||{},targetMap={...p,conversationListenerActivity:p.conversationListenerActivity};let cost=0,ws=0;
  for(const [f,w] of Object.entries(weights)){const target=unitTarget(f,targetMap[f]);cost+=Math.abs(norm[f]-target)*w;ws+=w}
  let score=(c.quality||.88)*.35+(ws?1-cost/ws:0)*5;
  if(key==='walk'&&c.id==='UAL_walk_formal')score+=(p.turnSharpness>=1.08?.24:0)+(p.gestureFrequency<=.8?.16:0);
  if(key==='conversation'&&c.semantic==='talk')score+=(p.gestureFrequency<.95?.22:0);
  if(key==='present'&&c.id==='KK_Use_Item'&&p.gestureAmplitude<.9)score-=.45;
  if(req.currentPose){try{const start=sampleCandidate(c,0),d=B.poseDistance(req.currentPose,start);score-=d*(req.poseWeight||1.6)}catch(_){}}
  score+=(tieUnit(`${req.character||'adult'}|${req.personality||'calm'}|${req.seed??0}|${key}|${c.id}`)-.5)*.006;
  return score;
}
function select(req,p){
  const action=req.action||'idle',key=keyForAction(action);
  if(req.clip||req.performance)return {selected:null,reason:'explicit-motion-request',actionKey:key,ranked:[]};
  const cs=candidatePool(action,req);if(!cs.length)return {selected:null,reason:'no-personality-pool',actionKey:key,ranked:[]};
  const norms=normalizedProfiles(cs),ranked=cs.map((c,i)=>({candidate:c,features:norms[i],rawFeatures:profile(c),score:personalityScore(c,norms[i],key,p,{...req,action:key})}));
  ranked.sort((a,b)=>b.score-a.score||a.candidate.id.localeCompare(b.candidate.id));
  return {selected:ranked[0].candidate,reason:'personality-ranked-authored-motion',actionKey:key,ranked:ranked.map(x=>({id:x.candidate.id,source:x.candidate.source,clip:x.candidate.clip,performance:x.candidate.performance||null,semantic:x.candidate.semantic,score:+x.score.toFixed(6),features:x.features}))};
}
function contract(){return {name:'NexPersonalityMotionSelectionV1',version:VERSION,directJointWrites:false,randomness:false,wallClock:false,proceduralGait:false,sineWavePersonality:false,method:'deterministic ranking of admitted authored/captured motion variants using measured motion features and semantic personality targets',safePools:SAFE_POOLS};}
root.NexPersonalityMotionSelectionV1={version:VERSION,select,profile,candidatePool,contract,_internals:{SAFE_POOLS,ACTION_WEIGHTS,fnv1a,tieUnit,normalizedProfiles}};
})(typeof window!=='undefined'?window:globalThis);
