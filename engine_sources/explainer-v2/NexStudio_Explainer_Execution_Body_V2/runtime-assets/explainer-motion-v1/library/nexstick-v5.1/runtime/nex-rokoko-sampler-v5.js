(function(root){'use strict';
const V=root.NexRokokoMotionVaultV5,U=root.NexStickmanUtilsV2;if(!V||!U)throw new Error('Rokoko V5 sampler dependencies missing');
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function idx(ts,t){let lo=0,hi=ts.length;while(lo<hi){const m=(lo+hi)>>1;if(ts[m]<=t)lo=m+1;else hi=m}return Math.max(0,Math.min(ts.length-2,lo-1))}
function mirrorPose(pose){const o={};for(const [n,p0] of Object.entries(pose)){const p=[-p0[0],p0[1],p0[2]];let target=n;if(n.endsWith('_l'))target=n.slice(0,-2)+'_r';else if(n.endsWith('_r'))target=n.slice(0,-2)+'_l';o[target]=p}return o}
function activeSegment(segs,t){for(const s of segs||[])if(t>=s.start-1e-9&&t<=s.end+1e-9)return s;return null}
const smooth=x=>{x=clamp(x,0,1);return x*x*(3-2*x)};
function contactWeight(seg,t){const d=Math.max(0,seg.end-seg.start),r=Math.min(.10,d*.22);if(r<=1e-9)return 1;return Math.min(smooth((t-seg.start)/r),smooth((seg.end-t)/r))}
function resolve(ref){if(V.clips[ref])return ref;return Object.keys(V.clips).find(k=>V.clips[k].semantic===ref)||null}
function contactState(c,t,mirror){const active=[],plant={l:0,r:0};for(const side of ['l','r']){const src=mirror?(side==='l'?'r':'l'):side,seg=activeSegment(c.contacts?.[src],t);if(!seg)continue;let anchor=seg.anchor.slice();if(mirror)anchor[0]*=-1;const w=contactWeight(seg,t);plant[side]=w;active.push({side,sourceSide:src,weight:w,anchor,sourceSegment:[seg.start,seg.end]});}return {active,plant}}
function sample(ref,t,opts={}){const k=resolve(ref);if(!k)return{blocked:true,failure:'ROKOKO_UNKNOWN_CLIP',ref};const c=V.clips[k],tt=clamp(+t||0,0,c.duration),i=idx(c.times,tt),a=c.times[i],b=c.times[i+1],w=b===a?0:(tt-a)/(b-a);let pose={};for(let j=0;j<V.joints.length;j++){const n=V.joints[j],p0=c.frames[i][j],p1=c.frames[i+1][j];pose[n]=[p0[0]+(p1[0]-p0[0])*w,p0[1]+(p1[1]-p0[1])*w,p0[2]+(p1[2]-p0[2])*w]}const mirror=!!opts.mirror;if(mirror)pose=mirrorPose(pose);const cs=contactState(c,tt,mirror);return{engine:'NexRokokoSamplerV5',action:c.semantic,time:tt,duration:c.duration,pose3d:pose,hands:{left:{pose:'relaxed',orientation:'edge-left'},right:{pose:'relaxed',orientation:'edge-right'}},motion:{source:'rokoko-captured',clip:k,semantic:c.semantic,sourceFile:c.sourceFile,license:c.license,mirrored:mirror},donorContacts:cs.active,footPlant:cs.plant,capturedYawDeltaDeg:(mirror?-1:1)*(c.yawDeltaDeg||0),blocked:false}}
function duration(ref){const k=resolve(ref);return k?V.clips[k].duration:0}
function meta(ref){const k=resolve(ref);if(!k)return null;const c=V.clips[k];return{id:k,semantic:c.semantic,duration:c.duration,yawDeltaDeg:c.yawDeltaDeg||0,sourceFile:c.sourceFile,tags:c.tags||[]}}
function catalog(){return Object.keys(V.clips).map(meta)}
root.NexRokokoSamplerV5={version:'5.1.0-contact-metadata',sample,duration,meta,catalog,resolve};
})(typeof window!=='undefined'?window:globalThis);
