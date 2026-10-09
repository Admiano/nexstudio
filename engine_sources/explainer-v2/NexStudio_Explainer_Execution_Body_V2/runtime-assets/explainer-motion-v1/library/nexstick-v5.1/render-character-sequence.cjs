'use strict';
const fs=require('fs');
const path=require('path');
const Cast=require(path.join(__dirname,'cast/runtime/nexstick-cast-v2.js'));
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const familyId=input.familyId||'neutral_adult';
const personality=input.personality||'warm';
const roleTags=Array.isArray(input.roleTags)&&input.roleTags.length?input.roleTags:['helper'];
const action=input.action||'idle';
const palette=input.palette&&typeof input.palette==='object'?input.palette:undefined;
const requestedFrames=Math.max(3,Math.min(12,Number(input.frameCount)||7));
let probe=Cast.sample({familyId,personality,roleTags,action,palette},0);
if(!probe||probe.blocked){process.stdout.write(JSON.stringify({ok:false,failure:probe?.failure||'NEXSTICK_SAMPLE_BLOCKED',action,familyId}));process.exit(0)}
let duration=Number(probe.duration);
if(!Number.isFinite(duration)||duration<=0)duration=action==='walk'?1.333333373:1.6;
duration=Math.max(.35,Math.min(2.8,duration));
const frames=[];
for(let i=0;i<requestedFrames;i++){
  const t=duration*(i/(requestedFrames-1));
  const state=Cast.sample({familyId,personality,roleTags,action,palette},t);
  if(!state||state.blocked){process.stdout.write(JSON.stringify({ok:false,failure:state?.failure||'NEXSTICK_FRAME_BLOCKED',frame:i,action,familyId}));process.exit(0)}
  const svg=Cast.render(state,{width:360,height:440,viewFamily:input.viewFamily||'near-front',palette});
  frames.push({t:Number(t.toFixed(6)),dataUrl:'data:image/svg+xml;base64,'+Buffer.from(svg).toString('base64')});
}
process.stdout.write(JSON.stringify({ok:true,version:Cast.version,action,familyId,personality,roleTags,durationSec:duration,frames}));
