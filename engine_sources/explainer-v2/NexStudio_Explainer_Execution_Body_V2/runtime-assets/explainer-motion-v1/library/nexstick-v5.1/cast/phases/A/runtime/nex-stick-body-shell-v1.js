(function(root){'use strict';
const NS=root.NexStickman,H=root.NexStickmanHandLibrary;
if(!NS||!H)throw new Error('NexStickBodyShellV1 requires NexStickman + NexStickmanHandLibrary (load V4 bundle first)');
const VERSION='1.0.0-body-shell';
const DEFAULT_PROFILE=Object.freeze({
  id:'neutral_base_v1',
  torso:{shoulderPadM:.028,hipPadM:.045,minShoulderHalfM:.16,minHipHalfM:.14,waistTaper:.86},
  limbRadiusM:{upperArm:.045,forearm:.040,thigh:.065,calf:.052,neck:.043},
  hand:{scale:1.34,palmExpandPx:1.5,fingerWidthM:.017},
  foot:{widthM:.078,toeExpandM:.018},
  head:{radiusXM:.100,radiusYM:.125},
  outlineM:.012
});
const DEFAULT_STYLE=Object.freeze({fill:'#d8d4cc',outline:'#1c1b1a',feature:'#1c1b1a',contextFill:'#eeeae2',contextAccent:'#8f79dc',background:'#ffffff'});
const clone=o=>JSON.parse(JSON.stringify(o));
const merge=(a,b)=>{const out=clone(a);for(const [k,v] of Object.entries(b||{})){if(v&&typeof v==='object'&&!Array.isArray(v)&&out[k]&&typeof out[k]==='object')out[k]={...out[k],...v};else out[k]=v}return out};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const f=n=>(+n).toFixed(2).replace(/\.00$/,'');
const mid=(a,b)=>({x:(a.x+b.x)/2,y:(a.y+b.y)/2,depth:(a.depth+b.depth)/2});
const len=(a,b)=>Math.hypot(b.x-a.x,b.y-a.y);
const unit=(a,b)=>{const d=Math.max(1e-9,len(a,b));return {x:(b.x-a.x)/d,y:(b.y-a.y)/d}};
const add=(a,b,s=1)=>({x:a.x+b.x*s,y:a.y+b.y*s});
function torsoGeom(P,profile,scale){
  const top=mid(P.shoulder_l,P.shoulder_r),bottom=mid(P.hip_l,P.hip_r),axis=unit(bottom,top),perp={x:-axis.y,y:axis.x};
  const shoulderHalf=Math.max(profile.torso.minShoulderHalfM*scale,len(P.shoulder_l,P.shoulder_r)/2+profile.torso.shoulderPadM*scale);
  const hipHalf=Math.max(profile.torso.minHipHalfM*scale,len(P.hip_l,P.hip_r)/2+profile.torso.hipPadM*scale);
  const waistC={x:top.x+(bottom.x-top.x)*.62,y:top.y+(bottom.y-top.y)*.62};
  const waistHalf=(shoulderHalf+(hipHalf-shoulderHalf)*.62)*profile.torso.waistTaper;
  const tl=add(top,perp,shoulderHalf),tr=add(top,perp,-shoulderHalf),wl=add(waistC,perp,waistHalf),wr=add(waistC,perp,-waistHalf),bl=add(bottom,perp,hipHalf),br=add(bottom,perp,-hipHalf);
  const d=`M ${f(tl.x)} ${f(tl.y)} Q ${f(wl.x)} ${f(wl.y)} ${f(bl.x)} ${f(bl.y)} Q ${f(bottom.x)} ${f(bottom.y+hipHalf*.10)} ${f(br.x)} ${f(br.y)} Q ${f(wr.x)} ${f(wr.y)} ${f(tr.x)} ${f(tr.y)} Q ${f(top.x)} ${f(top.y-shoulderHalf*.08)} ${f(tl.x)} ${f(tl.y)} Z`;
  return {path:d,points:{top,waist:waistC,bottom,tl,tr,wl,wr,bl,br},depth:(P.shoulder_l.depth+P.shoulder_r.depth+P.hip_l.depth+P.hip_r.depth)/4,shoulderHalf,hipHalf,waistHalf};
}
const SEGMENTS=[
  ['upper_arm_l','shoulder_l','elbow_l','upperArm'],['forearm_l','elbow_l','wrist_l','forearm'],
  ['upper_arm_r','shoulder_r','elbow_r','upperArm'],['forearm_r','elbow_r','wrist_r','forearm'],
  ['thigh_l','hip_l','knee_l','thigh'],['calf_l','knee_l','ankle_l','calf'],
  ['thigh_r','hip_r','knee_r','thigh'],['calf_r','knee_r','ankle_r','calf']
];
function segmentGeom(P,profile,scale){return SEGMENTS.map(([id,a,b,r])=>({id,a,b,p1:P[a],p2:P[b],radiusM:profile.limbRadiusM[r],widthPx:profile.limbRadiusM[r]*2*scale,depth:(P[a].depth+P[b].depth)/2}))}
function handGeom(P,side,state,profile){
  const s=side==='left'?'l':'r',w=P['wrist_'+s],e=P['elbow_'+s],ang=Math.atan2(w.y-e.y,w.x-e.x)*180/Math.PI+90,pose=state?.pose||'relaxed',ori=state?.orientation||'palm-front',tpl=H[pose]?.[ori]||H.relaxed['palm-front'];
  return {id:'hand_'+s,anchor:{x:w.x,y:w.y,depth:w.depth},rotationDeg:ang,scale:profile.hand.scale,pose,orientation:ori,palm:tpl.palm,fingers:tpl.fingers,depth:w.depth};
}
function tx(p,h){const a=h.rotationDeg*Math.PI/180,c=Math.cos(a),s=Math.sin(a),x=p[0]*h.scale,y=p[1]*h.scale;return {x:h.anchor.x+x*c-y*s,y:h.anchor.y+x*s+y*c}}
function footGeom(P,side,profile,scale){const s=side==='left'?'l':'r',a=P['ankle_'+s],t=P['toe_'+s],d=unit(a,t),p={x:-d.y,y:d.x},back=profile.foot.toeExpandM*scale*.35,front=profile.foot.toeExpandM*scale,w=profile.foot.widthM*scale/2;return {id:'foot_'+s,ankle:a,toe:t,depth:(a.depth+t.depth)/2,polygon:[add(add(a,d,-back),p,w),add(add(t,d,front),p,w*.78),add(add(t,d,front),p,-w*.78),add(add(a,d,-back),p,-w)]}}
function geometry(state,opts={}){
  if(!state||state.blocked||!state.pose3d)return {blocked:true,failure:state?.failure||'MISSING_POSE'};
  const profile=merge(DEFAULT_PROFILE,opts.profile),w=opts.width||640,h=opts.height||540,scale=opts.scale||260,camera={origin:opts.origin||[w*.5,h-48],scale,yaw_deg:opts.yawDeg??-14,pitch_deg:opts.pitchDeg||0,root_center:opts.rootCenter!==false};
  const P=NS.project(state.pose3d,camera),torso=torsoGeom(P,profile,scale),segments=segmentGeom(P,profile,scale),hands={left:handGeom(P,'left',state.hands?.left,profile),right:handGeom(P,'right',state.hands?.right,profile)},feet={left:footGeom(P,'left',profile,scale),right:footGeom(P,'right',profile,scale)};
  const head={id:'head',center:P.head,rx:profile.head.radiusXM*scale,ry:profile.head.radiusYM*scale,depth:P.head.depth};
  const neck={id:'neck',p1:P.neck,p2:P.head,widthPx:profile.limbRadiusM.neck*2*scale,depth:(P.neck.depth+P.head.depth)/2};
  const anchors={};for(const [k,v] of Object.entries(P))anchors[k]={x:v.x,y:v.y,depth:v.depth,world:state.pose3d[k]?.slice?.()||null};
  anchors.torso_top={...torso.points.top};anchors.waist={...torso.points.waist};anchors.torso_bottom={...torso.points.bottom};
  const guides={neckline:{left:torso.points.tl,right:torso.points.tr,center:P.neck},waistline:{left:torso.points.wl,right:torso.points.wr,center:torso.points.waist},hipline:{left:torso.points.bl,right:torso.points.br,center:torso.points.bottom},wrists:{left:P.wrist_l,right:P.wrist_r},ankles:{left:P.ankle_l,right:P.ankle_r}};
  const regions={torso,neck,head,...Object.fromEntries(segments.map(s=>[s.id,s])),hand_l:hands.left,hand_r:hands.right,foot_l:feet.left,foot_r:feet.right};
  return {version:VERSION,blocked:false,width:w,height:h,camera,profile,projected:P,regions,anchors,guides,torso,segments,hands,feet,head,neck,torsoDepth:torso.depth};
}
function lineLayer(s,style,profile,scale){const outline=Math.max(1.4,profile.outlineM*scale);return `<g class="nxc-region nxc-${esc(s.id)}" data-region="${esc(s.id)}" data-depth="${f(s.depth)}"><line x1="${f(s.p1.x)}" y1="${f(s.p1.y)}" x2="${f(s.p2.x)}" y2="${f(s.p2.y)}" stroke="${style.outline}" stroke-width="${f(s.widthPx+outline*2)}" stroke-linecap="round"/><line x1="${f(s.p1.x)}" y1="${f(s.p1.y)}" x2="${f(s.p2.x)}" y2="${f(s.p2.y)}" stroke="${style.fill}" stroke-width="${f(s.widthPx)}" stroke-linecap="round"/></g>`}
function neckLayer(n,style,profile,scale){return lineLayer({...n,id:'neck'},style,profile,scale)}
function footLayer(ft,style,profile,scale){const outline=Math.max(1.4,profile.outlineM*scale),pts=ft.polygon.map(p=>`${f(p.x)},${f(p.y)}`).join(' ');return `<polygon class="nxc-region nxc-${ft.id}" data-region="${ft.id}" points="${pts}" fill="${style.fill}" stroke="${style.outline}" stroke-width="${f(outline)}" stroke-linejoin="round"/>`}
function handLayer(side,h,style,profile,scale){const outline=Math.max(1.15,profile.outlineM*scale*.72),palm=h.palm.map(p=>tx(p,h)).map(p=>`${f(p.x)},${f(p.y)}`).join(' ');let m=`<polygon data-part="palm" points="${palm}" fill="${style.fill}" stroke="${style.outline}" stroke-width="${f(outline)}" stroke-linejoin="round"/>`;const fw=Math.max(2.6,profile.hand.fingerWidthM*scale);for(const [name,arr] of Object.entries(h.fingers)){const pts=arr.map(p=>tx(p,h)).map(p=>`${f(p.x)},${f(p.y)}`).join(' ');m+=`<polyline data-finger="${esc(name)}" points="${pts}" fill="none" stroke="${style.outline}" stroke-width="${f(fw+outline*1.5)}" stroke-linecap="round" stroke-linejoin="round"/><polyline data-finger-fill="${esc(name)}" points="${pts}" fill="none" stroke="${style.fill}" stroke-width="${f(fw)}" stroke-linecap="round" stroke-linejoin="round"/>`}return `<g class="nxc-region nxc-hand-${side}" data-region="hand_${side==='left'?'l':'r'}" data-pose="${esc(h.pose)}">${m}</g>`}
function contextMarkup(state,g,style){let out='';const projectWorld=p=>NS.project({root:state.pose3d.root,x:p},{...g.camera,root_center:g.camera.root_center}).x;if(state.prop?.position){const q=projectWorld(state.prop.position),sx=Math.max(14,(state.prop.size?.[0]||.12)*g.camera.scale),sy=Math.max(9,(state.prop.size?.[1]||state.prop.size?.[2]||.08)*g.camera.scale*.7);out+=`<rect data-context="prop" x="${f(q.x-sx/2)}" y="${f(q.y-sy/2)}" width="${f(sx)}" height="${f(sy)}" rx="6" fill="${style.contextAccent}" stroke="${style.outline}" stroke-width="2.5"/>`;}if(state.seat){const c=state.seat.seatCenter||[0,.48,0],q=projectWorld(c),sw=(state.seat.width||.5)*g.camera.scale,sh=.055*g.camera.scale;out+=`<g data-context="seat"><rect x="${f(q.x-sw/2)}" y="${f(q.y-sh/2)}" width="${f(sw)}" height="${f(sh)}" rx="4" fill="${style.contextFill}" stroke="${style.outline}" stroke-width="2.5"/><line x1="${f(q.x-sw*.42)}" y1="${f(q.y+sh/2)}" x2="${f(q.x-sw*.42)}" y2="${f(q.y+.46*g.camera.scale)}" stroke="${style.outline}" stroke-width="3"/><line x1="${f(q.x+sw*.42)}" y1="${f(q.y+sh/2)}" x2="${f(q.x+sw*.42)}" y2="${f(q.y+.46*g.camera.scale)}" stroke="${style.outline}" stroke-width="3"/></g>`;}return out}
function render(state,opts={}){
  const g=geometry(state,opts);if(g.blocked)return `<svg xmlns="http://www.w3.org/2000/svg" width="${opts.width||640}" height="${opts.height||540}"><text x="20" y="40">BLOCKED: ${esc(g.failure)}</text></svg>`;
  const style={...DEFAULT_STYLE,...(opts.style||{})},profile=g.profile,scale=g.camera.scale,outline=Math.max(1.4,profile.outlineM*scale),back=[],front=[];
  for(const s of g.segments)(s.depth<g.torsoDepth?back:front).push(s);back.sort((a,b)=>a.depth-b.depth);front.sort((a,b)=>a.depth-b.depth);
  const torso=`<path class="nxc-region nxc-torso" data-region="torso" d="${g.torso.path}" fill="${style.fill}" stroke="${style.outline}" stroke-width="${f(outline)}" stroke-linejoin="round"/>`;
  const head=`<ellipse class="nxc-region nxc-head" data-region="head" cx="${f(g.head.center.x)}" cy="${f(g.head.center.y)}" rx="${f(g.head.rx)}" ry="${f(g.head.ry)}" fill="${style.fill}" stroke="${style.outline}" stroke-width="${f(outline)}"/>`;
  const eyesY=g.head.center.y-g.head.ry*.08,eyeSep=g.head.rx*.32,mouthY=g.head.center.y+g.head.ry*.34;
  const face=opts.face===false?'':`<g class="nxc-face" data-layer="face"><circle cx="${f(g.head.center.x-eyeSep)}" cy="${f(eyesY)}" r="2.7" fill="${style.feature}"/><circle cx="${f(g.head.center.x+eyeSep)}" cy="${f(eyesY)}" r="2.7" fill="${style.feature}"/><path d="M ${f(g.head.center.x-g.head.rx*.25)} ${f(mouthY)} Q ${f(g.head.center.x)} ${f(mouthY+g.head.ry*.06)} ${f(g.head.center.x+g.head.rx*.25)} ${f(mouthY)}" fill="none" stroke="${style.feature}" stroke-width="2.5" stroke-linecap="round"/></g>`;
  const context=opts.context===false?'':contextMarkup(state,g,style);
  const backFeet=[],frontFeet=[];for(const ft of Object.values(g.feet))(ft.depth<g.torsoDepth?backFeet:frontFeet).push(ft);
  const body=`${context}<g data-layer="body-back">${backFeet.map(x=>footLayer(x,style,profile,scale)).join('')}${back.map(x=>lineLayer(x,style,profile,scale)).join('')}</g><g data-layer="body-core">${torso}${neckLayer(g.neck,style,profile,scale)}${head}</g><g data-layer="body-front">${front.map(x=>lineLayer(x,style,profile,scale)).join('')}${frontFeet.map(x=>footLayer(x,style,profile,scale)).join('')}${handLayer('left',g.hands.left,style,profile,scale)}${handLayer('right',g.hands.right,style,profile,scale)}</g>${face}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${g.width}" height="${g.height}" viewBox="0 0 ${g.width} ${g.height}" data-nexstick-body-shell="${VERSION}"><rect width="100%" height="100%" fill="${style.background}"/>${body}</svg>`;
}
function contract(){return {name:'NexStickBodyShellV1',version:VERSION,scope:'render-surface-only',mutatesMotion:false,owns:['neutral body surface','body-region geometry','body-layer ordering','clothing attachment guides'],doesNotOwn:['motion','morphology presets','clothing','personality','roles','storyboard','director'],requiredInput:['pose3d'],optionalInput:['hands','prop','seat'],regions:['head','neck','torso','upper_arm_l','forearm_l','upper_arm_r','forearm_r','thigh_l','calf_l','thigh_r','calf_r','hand_l','hand_r','foot_l','foot_r'],layerOrder:['body-back','body-core','body-front','face'],clothingIntegration:{readFrom:'geometry(state, opts)',stableGuides:['neckline','waistline','hipline','wrists','ankles'],mustNotModifyPose:true}}}
root.NexStickBodyShellV1={version:VERSION,DEFAULT_PROFILE,DEFAULT_STYLE,geometry,render,contract};
})(typeof window!=='undefined'?window:globalThis);
