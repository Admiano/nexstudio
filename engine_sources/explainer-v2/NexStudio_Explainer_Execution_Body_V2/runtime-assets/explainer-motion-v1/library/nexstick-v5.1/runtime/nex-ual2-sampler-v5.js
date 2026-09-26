(function(root){'use strict';
const V=root.NexUAL2MotionVaultV5,U=root.NexStickmanUtilsV2;
if(!V||!U) throw new Error('UAL2 V5 sampler dependencies missing');
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]],mul=(a,s)=>[a[0]*s,a[1]*s,a[2]*s];
function binaryIndex(times,t){let lo=0,hi=times.length;while(lo<hi){const m=(lo+hi)>>1;if(times[m]<=t)lo=m+1;else hi=m}return Math.max(0,Math.min(times.length-2,lo-1))}
function mirrorPose(pose){const o={};for(const [n,p0] of Object.entries(pose)){const p=[-p0[0],p0[1],p0[2]];let target=n;if(n.endsWith('_l'))target=n.slice(0,-2)+'_r';else if(n.endsWith('_r'))target=n.slice(0,-2)+'_l';o[target]=p}return o}
function activeSegment(segs,t){for(const s of segs||[])if(t>=s.start-1e-9&&t<=s.end+1e-9)return s;return null}
const smooth=x=>{x=clamp(x,0,1);return x*x*(3-2*x)};
function contactWeight(seg,t){const d=Math.max(0,seg.end-seg.start),r=Math.min(.08,d*.25);if(r<=1e-9)return 1;return Math.min(smooth((t-seg.start)/r),smooth((seg.end-t)/r))}
function resolve(ref){if(V.clips[ref])return ref;const key=Object.keys(V.clips).find(k=>V.clips[k].semantic===ref);return key||null}
function contactState(c,tt,cycleOffset,mirror){const active=[],plant={l:0,r:0};for(const side of ['l','r']){const src=mirror?(side==='l'?'r':'l'):side,seg=activeSegment(c.contacts?.[src],tt);if(!seg)continue;let anchor=add(seg.anchor,cycleOffset);if(mirror)anchor=[-anchor[0],anchor[1],anchor[2]];const w=contactWeight(seg,tt);plant[side]=w;active.push({side,sourceSide:src,weight:w,anchor,sourceSegment:[seg.start,seg.end]});}return {active,plant}}
function sample(ref,t,opts={}){const key=resolve(ref);if(!key)return {blocked:true,failure:'UAL2_UNKNOWN_CLIP',ref};const c=V.clips[key],raw=Math.max(0,+t||0),loop=opts.loop??c.loop;let cycle=0,tt=raw;if(loop&&c.duration>0){cycle=Math.floor(raw/c.duration);tt=raw-cycle*c.duration}else tt=clamp(raw,0,c.duration);const i=binaryIndex(c.times,tt),a=c.times[i],b=c.times[i+1],w=b===a?0:(tt-a)/(b-a);let pose={};for(let j=0;j<V.joints.length;j++){const n=V.joints[j],p0=c.frames[i][j],p1=c.frames[i+1][j];pose[n]=[p0[0]+(p1[0]-p0[0])*w,p0[1]+(p1[1]-p0[1])*w,p0[2]+(p1[2]-p0[2])*w]}let cycleOffset=loop?mul(c.rootDelta||[0,0,0],cycle):[0,0,0];const mirror=!!opts.mirror;if(cycle)pose=U.translatePose(pose,cycleOffset);if(mirror){pose=mirrorPose(pose);cycleOffset=[-cycleOffset[0],cycleOffset[1],cycleOffset[2]]}const cs=contactState(c,tt,cycleOffset,mirror);return {engine:'NexUAL2SamplerV5',action:c.semantic,time:raw,duration:c.duration,pose3d:pose,hands:{left:{pose:'relaxed',orientation:'edge-left'},right:{pose:'relaxed',orientation:'edge-right'}},motion:{source:'ual2-standard',license:'CC0-1.0',clip:key,semantic:c.semantic},donorContacts:cs.active,footPlant:cs.plant,blocked:false}}
function duration(ref){const k=resolve(ref);return k?V.clips[k].duration:0}
function catalog(){return Object.entries(V.clips).map(([id,c])=>({id,semantic:c.semantic,duration:c.duration,loop:c.loop,source:c.source,license:c.license,tags:c.tags}))}
root.NexUAL2SamplerV5={version:'5.1.0-contact-metadata',sample,duration,catalog,resolve};
})(typeof window!=='undefined'?window:globalThis);
