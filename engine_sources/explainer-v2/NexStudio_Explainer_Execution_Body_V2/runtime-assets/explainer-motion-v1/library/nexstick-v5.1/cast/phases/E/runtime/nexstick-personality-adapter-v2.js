(function(root){'use strict';
const E=root.NexPerformanceUnifiedV5,Sel=root.NexPersonalityMotionSelectionV1;
if(!E||!Sel)throw new Error('NexStickPersonalityAdapterV2 requires NexPerformanceUnifiedV5 and NexPersonalityMotionSelectionV1');
const VERSION='2.0.0-unified-v5';
const PRESETS={
 calm:{gestureAmplitude:.82,gestureFrequency:.78,idleActivity:.72,headTiltTendency:.28,gazeHoldDuration:2.2,reactionLatency:.24,stanceWidth:.96,movementEnergy:.78,turnSharpness:.86,armSwingScale:.85,bodyOpenness:.95,handRestOpenness:.95,nodFrequency:2,conversationListenerActivity:.82,movementTempoBias:.88,anticipationAmplitude:.85,settleDuration:1.25},
 cheerful:{gestureAmplitude:1.15,gestureFrequency:1.18,idleActivity:1.10,headTiltTendency:.55,gazeHoldDuration:1.3,reactionLatency:.13,stanceWidth:1,movementEnergy:1.10,turnSharpness:1.05,armSwingScale:1.08,bodyOpenness:1.18,handRestOpenness:1.18,nodFrequency:6,conversationListenerActivity:1.15,movementTempoBias:1.08,anticipationAmplitude:1.05,settleDuration:.92},
 confident:{gestureAmplitude:1.12,gestureFrequency:.95,idleActivity:.84,headTiltTendency:.18,gazeHoldDuration:2.4,reactionLatency:.10,stanceWidth:1.12,movementEnergy:1.08,turnSharpness:1.18,armSwingScale:1.05,bodyOpenness:1.25,handRestOpenness:1.12,nodFrequency:3,conversationListenerActivity:.92,movementTempoBias:1.04,anticipationAmplitude:.95,settleDuration:1},
 shy:{gestureAmplitude:.72,gestureFrequency:.68,idleActivity:.62,headTiltTendency:.62,gazeHoldDuration:.85,reactionLatency:.34,stanceWidth:.86,movementEnergy:.72,turnSharpness:.82,armSwingScale:.76,bodyOpenness:.72,handRestOpenness:.78,nodFrequency:2,conversationListenerActivity:.72,movementTempoBias:.90,anticipationAmplitude:.78,settleDuration:1.3},
 energetic:{gestureAmplitude:1.32,gestureFrequency:1.40,idleActivity:1.42,headTiltTendency:.42,gazeHoldDuration:.90,reactionLatency:.07,stanceWidth:1.06,movementEnergy:1.38,turnSharpness:1.25,armSwingScale:1.28,bodyOpenness:1.20,handRestOpenness:1.22,nodFrequency:8,conversationListenerActivity:1.32,movementTempoBias:1.22,anticipationAmplitude:1.22,settleDuration:.72},
 serious:{gestureAmplitude:.90,gestureFrequency:.72,idleActivity:.64,headTiltTendency:.08,gazeHoldDuration:2.6,reactionLatency:.18,stanceWidth:1.04,movementEnergy:.90,turnSharpness:1.12,armSwingScale:.88,bodyOpenness:.92,handRestOpenness:.85,nodFrequency:1,conversationListenerActivity:.76,movementTempoBias:.96,anticipationAmplitude:.92,settleDuration:1.2},
 playful:{gestureAmplitude:1.28,gestureFrequency:1.35,idleActivity:1.28,headTiltTendency:.78,gazeHoldDuration:.95,reactionLatency:.09,stanceWidth:1.02,movementEnergy:1.25,turnSharpness:1.16,armSwingScale:1.20,bodyOpenness:1.24,handRestOpenness:1.27,nodFrequency:9,conversationListenerActivity:1.30,movementTempoBias:1.14,anticipationAmplitude:1.25,settleDuration:.82},
 authoritative:{gestureAmplitude:1.15,gestureFrequency:.78,idleActivity:.70,headTiltTendency:.10,gazeHoldDuration:2.8,reactionLatency:.09,stanceWidth:1.18,movementEnergy:1.05,turnSharpness:1.25,armSwingScale:1,bodyOpenness:1.30,handRestOpenness:1.08,nodFrequency:2,conversationListenerActivity:.70,movementTempoBias:1,anticipationAmplitude:1,settleDuration:1.15},
 warm:{gestureAmplitude:1.05,gestureFrequency:1.05,idleActivity:.90,headTiltTendency:.48,gazeHoldDuration:1.8,reactionLatency:.14,stanceWidth:.98,movementEnergy:.98,turnSharpness:.95,armSwingScale:.98,bodyOpenness:1.20,handRestOpenness:1.22,nodFrequency:5,conversationListenerActivity:1.28,movementTempoBias:1,anticipationAmplitude:1.05,settleDuration:1.05},
 reserved:{gestureAmplitude:.76,gestureFrequency:.62,idleActivity:.56,headTiltTendency:.16,gazeHoldDuration:1.7,reactionLatency:.28,stanceWidth:.90,movementEnergy:.70,turnSharpness:.88,armSwingScale:.78,bodyOpenness:.78,handRestOpenness:.76,nodFrequency:1,conversationListenerActivity:.64,movementTempoBias:.86,anticipationAmplitude:.80,settleDuration:1.35}
};
const SAFE_TEMPO_ACTIONS=new Set(['idle','walk','present','conversation','talk','run','reach','captured_reach','interact','use_item']);
const CONTACT_LOCKED_ACTIONS=new Set(['pickup','place','handoff','handoff_pair','sit','sit_idle','sit_talk','stand','carry','sit_to_walk']);
const ONESHOT_ENVELOPE_ACTIONS=new Set(['present','reach','captured_reach','pickup','place','handoff','handoff_pair','sit','stand','sit_to_walk']);
function clamp(v,a=0,b=1){return Math.max(a,Math.min(b,v))}
function getPreset(name){const p=PRESETS[name||'calm'];if(!p)throw new Error(`Unknown NexStick personality preset: ${name}`);return {...p}}
function normalizeAction(a){if(a==='present')return 'interact';if(a==='reach')return 'captured_reach';return a}
function selectionRequest(req,personality){return {...req,personality,action:req.action||'idle'}}
function applySelectedMotion(adapted,selected){if(!selected)return adapted;if(selected.source==='kaykit-v3')return {...adapted,clip:selected.clip};return {...adapted,clip:selected.performance||selected.clip,performance:selected.performance||selected.clip}}
function baseDurationFor(action,adapted,req){if(action==='handoff'||action==='handoff_pair')return req.duration||1.7;return E.actionDuration(adapted)}
function actionIsLoopingSelection(sel){return !!sel?.selected?.loop}
function plan(req={}){
  const personality=req.personality||'calm',profile=getPreset(personality),publicAction=req.action||'idle';
  const sel=Sel.select(selectionRequest(req,personality),profile),baseAction=normalizeAction(publicAction);
  let adapted={...req,action:baseAction};delete adapted.personality;delete adapted.character;delete adapted.seed;
  adapted=applySelectedMotion(adapted,sel.selected);
  const baseDuration=Math.max(.001,baseDurationFor(publicAction,adapted,req));
  const loopish=actionIsLoopingSelection(sel)||['idle','walk','conversation','talk','run'].includes(publicAction);
  const timingLocked=req.timingLocked===true||req.duration!=null;
  const tempoEligible=SAFE_TEMPO_ACTIONS.has(publicAction)&&!timingLocked;
  const tempo=tempoEligible?profile.movementTempoBias:1;
  const coreDuration=baseDuration/tempo;
  const oneShot=ONESHOT_ENVELOPE_ACTIONS.has(publicAction)&&!loopish;
  const leadIn=(oneShot&&!timingLocked)?profile.reactionLatency:0;
  const settleTail=(oneShot&&!timingLocked)?.14*profile.settleDuration:0;
  const duration=leadIn+coreDuration+settleTail;
  return {version:VERSION,personality,character:req.character||'adult',seed:req.seed??0,publicAction,baseAction,profile,selection:sel,adaptedRequest:adapted,baseDuration,coreDuration,duration,leadIn,settleTail,tempo,tempoEligible,contactLocked:CONTACT_LOCKED_ACTIONS.has(publicAction),timingLocked,blocked:false};
}
function coreMap(p,t){const tt=clamp(+t||0,0,p.duration);if(tt<p.leadIn)return {region:'lead-in',baseTime:0,coreProgress:0};if(tt>=p.leadIn+p.coreDuration)return {region:'settle',baseTime:Math.max(0,p.baseDuration-1e-6),coreProgress:1};const ct=tt-p.leadIn,bt=clamp(ct*p.tempo,0,p.baseDuration);return {region:'core',baseTime:bt,coreProgress:clamp(bt/p.baseDuration)}}
function sampleBase(p,baseTime){if(p.publicAction==='handoff'||p.publicAction==='handoff_pair')return E.handoffPair(baseTime,p.adaptedRequest);return E.sample(p.adaptedRequest,baseTime)}
function safeHandRest(state,p){
  if(!state||state.blocked||p.contactLocked)return state;
  const a=p.publicAction;if(!['idle','conversation','talk'].includes(a)||!state.hands)return state;
  const open=p.profile.handRestOpenness>=1.10;if(!open)return state;
  const hands={...state.hands};for(const side of ['left','right'])if(hands[side]&&['relaxed','open'].includes(hands[side].pose))hands[side]={...hands[side],pose:'open'};
  return {...state,hands};
}
function attentionIntent(p,t,map){
  const pr=p.profile,a=p.publicAction,conversation=['conversation','talk','handoff','handoff_pair'].includes(a),presentation=['present','interact'].includes(a),target=conversation?'partner':presentation?'audience':a==='pickup'||a==='reach'?'task':'forward';
  const interval=pr.nodFrequency>0?60/pr.nodFrequency:Infinity,phase=((String(p.seed).split('').reduce((s,c)=>s+c.charCodeAt(0),0)%1000)/1000)*Math.min(interval,4),local=Math.max(0,(+t||0)-p.leadIn),pulse=conversation&&Number.isFinite(interval)&&local>=phase&&((local-phase)%interval)<.12;
  return {target,gazeHoldSeconds:pr.gazeHoldDuration,reactionLatencySeconds:pr.reactionLatency,headTiltTendency:pr.headTiltTendency,nodFrequencyPerMinute:pr.nodFrequency,nodCue:pulse,listenerActivity:pr.conversationListenerActivity,region:map.region,directJointWrite:false};
}
function annotate(state,p,t,map){
  let s=safeHandRest(state,p);if(!s||typeof s!=='object')return s;
  const selected=p.selection.selected;
  return {...s,engine:s.engine||E.version,action:p.publicAction,time:+t||0,duration:p.duration,progress:p.duration?clamp((+t||0)/p.duration):0,personality:{version:VERSION,preset:p.personality,character:p.character,seed:p.seed,parameters:{...p.profile},motionSelection:{reason:p.selection.reason,selected:selected?{id:selected.id,source:selected.source,clip:selected.clip,performance:selected.performance||null,semantic:selected.semantic}:null,ranked:p.selection.ranked.slice(0,5)},timing:{region:map.region,baseTime:map.baseTime,leadIn:p.leadIn,coreDuration:p.coreDuration,settleTail:p.settleTail,tempo:p.tempo,contactLocked:p.contactLocked},gestureIntent:{amplitude:p.profile.gestureAmplitude,frequency:p.profile.gestureFrequency,anticipationAmplitude:p.profile.anticipationAmplitude,bodyOpenness:p.profile.bodyOpenness,handRestOpenness:p.profile.handRestOpenness,directJointWrite:false},restIntent:{stanceWidth:p.profile.stanceWidth,bodyOpenness:p.profile.bodyOpenness,handRestOpenness:p.profile.handRestOpenness,directJointWrite:false},attention:attentionIntent(p,t,map),invariants:{phaseEJointWrites:false,v5PerformanceAuthority:true,ownershipCoreUnmodified:true,contactCoreUnmodified:true,gripCoreUnmodified:true,seatSupportCoreUnmodified:true,footSupportCoreUnmodified:true}}};
}
function samplePlan(p,t){const map=coreMap(p,t),base=sampleBase(p,map.baseTime);return annotate(base,p,t,map)}
function sample(req,t){return samplePlan(plan(req),t)}
function handoffPair(t,spec={}){return sample({...spec,action:'handoff'},t)}
function actionDuration(req={}){return plan(req).duration}
function contract(){return {name:'NexStickPersonalityAdapterV2',version:VERSION,phase:'NEXSTICK MASTER V2 / PERSONALITY',requires:'NexPerformanceUnifiedV5@5.1.0-skin-safe-angular-continuity',owns:['personality preset semantics','admitted authored-motion variant scoring','safe timing envelope','gesture/rest/attention intents'],doesNotOwn:['morphology','clothing','occupational casting','joint puppeteering','body motion synthesis','contact solving','grip solving','seat support','foot support','object ownership'],determinism:'character + personality + action + seed + time',safety:{directJointWrites:false,randomMotion:false,wallClock:false,randomJitter:false,constantBounce:false,sineWaveAnimation:false,contactAndOwnershipRemainV5Authoritative:true}}}
root.NexStickPersonalityAdapterV2={version:VERSION,presets:PRESETS,getPreset,plan,samplePlan,sample,handoffPair,actionDuration,contract,_internals:{coreMap,normalizeAction,SAFE_TEMPO_ACTIONS,CONTACT_LOCKED_ACTIONS}};
})(typeof window!=='undefined'?window:globalThis);
