'use strict';
/**
 * NexStick Mesh Deformer V1
 * NexStudio-owned deterministic 2D surface deformation adapter.
 * It does NOT own motion. It consumes projected NexPerformance/NexStick joints
 * and builds continuous volume-preserving ribbons through bend joints.
 *
 * Architectural reference only: Stretchy Studio's permissive MIT CPU vertex
 * skinning / joint-weighting approach. No Stretchy source is vendored here.
 */
const VERSION='1.0.0-authored-ribbon-skin';
const EPS=1e-7;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const mix=(a,b,t)=>({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,depth:(a.depth||0)+((b.depth||0)-(a.depth||0))*t});
const sub=(a,b)=>({x:a.x-b.x,y:a.y-b.y});
const add=(a,b,s=1)=>({x:a.x+b.x*s,y:a.y+b.y*s});
const length=v=>Math.hypot(v.x,v.y);
const norm=v=>{const L=Math.max(EPS,length(v));return{x:v.x/L,y:v.y/L};};
const perp=v=>({x:-v.y,y:v.x});
const dot=(a,b)=>a.x*b.x+a.y*b.y;
const f=n=>(+n).toFixed(2);
function quad(a,c,b,t){const u=1-t;return{x:u*u*a.x+2*u*t*c.x+t*t*b.x,y:u*u*a.y+2*u*t*c.y+t*t*b.y,depth:(a.depth||0)*u*u+2*u*t*(c.depth||0)+(b.depth||0)*t*t};}
function qder(a,c,b,t){return{x:2*(1-t)*(c.x-a.x)+2*t*(b.x-c.x),y:2*(1-t)*(c.y-a.y)+2*t*(b.y-c.y)};}
function bendAngle(a,j,b){const u=norm(sub(a,j)),v=norm(sub(b,j));return Math.acos(clamp(dot(u,v),-1,1));}
function centerline(a,j,b,steps=14){
  // Preserve authored segment lengths and localize curvature to the bend.
  // This avoids the rubber-hose bowing produced by a whole-limb Bézier.
  const v1=norm(sub(j,a)),v2=norm(sub(b,j));
  const l1=Math.max(EPS,length(sub(j,a))),l2=Math.max(EPS,length(sub(b,j)));
  const k=Math.min(l1,l2)*.18;
  const p1=add(j,v1,-k),p2=add(j,v2,k),out=[];
  const nStraight=Math.max(3,Math.floor((steps-5)/2));
  for(let i=0;i<=nStraight;i++){
    const t=i/nStraight,p=mix(a,p1,t);out.push({p,tangent:v1,u:(l1-k)*t/(l1+l2)});
  }
  const curveSteps=5;
  for(let i=1;i<=curveSteps;i++){
    const t=i/curveSteps,p=quad(p1,j,p2,t),d=qder(p1,j,p2,t);
    const approx=(l1-k)+2*k*t;
    out.push({p,tangent:norm(d),u:clamp(approx/(l1+l2),0,1)});
  }
  for(let i=1;i<=nStraight;i++){
    const t=i/nStraight,p=mix(p2,b,t);out.push({p,tangent:v2,u:clamp(((l1+k)+(l2-k)*t)/(l1+l2),0,1)});
  }
  // Normalize u exactly from 0..1 for radius interpolation.
  const N=out.length-1;out.forEach((x,i)=>x.u=i/Math.max(1,N));
  return out;
}
function radiusAt(u,r0,rj,r1,bendRad,volumePreserve=.12){
  let r=u<=.5?r0+(rj-r0)*(u/.5):rj+(r1-rj)*((u-.5)/.5);
  const joint=Math.exp(-Math.pow((u-.5)/.16,2));
  // add a restrained bulge around the joint to avoid collapsing/candy-wrapper bends.
  const bend=Math.max(0,(Math.PI-bendRad)/Math.PI);
  r*=1+joint*bend*volumePreserve;
  return r;
}
function ribbon(a,j,b,{r0=8,rj=7.5,r1=7,steps=14,volumePreserve=.12}={}){
  const ang=bendAngle(a,j,b),line=centerline(a,j,b,steps),left=[],right=[];
  let prevN=null;
  for(const s of line){
    let n=perp(s.tangent);
    if(prevN&&dot(n,prevN)<0)n={x:-n.x,y:-n.y};
    prevN=n;
    const r=radiusAt(s.u,r0,rj,r1,ang,volumePreserve);
    left.push(add(s.p,n,r));right.push(add(s.p,n,-r));
  }
  const points=left.concat(right.reverse());
  const d=`M ${f(points[0].x)} ${f(points[0].y)} `+points.slice(1).map(p=>`L ${f(p.x)} ${f(p.y)}`).join(' ')+` Z`;
  return {d,points,left,right:right.slice().reverse(),centerline:line,bendAngleRad:ang};
}
function ribbonSvg(a,j,b,opts={}){
  const r=ribbon(a,j,b,opts);
  const attrs=opts.attrs||'';
  return `<path ${attrs} d="${r.d}" fill="${opts.fill||'#ddd'}" stroke="${opts.stroke||'#292522'}" stroke-width="${opts.strokeWidth??1.4}" stroke-linejoin="round"/>`;
}
/** Axis-projection weights useful for importing arbitrary layered art. */
function axisWeights(vertices,start,joint,{blendZone=40}={}){
  const axis=norm(sub(joint,start));
  return vertices.map(v=>{
    const proj=(v.x-joint.x)*axis.x+(v.y-joint.y)*axis.y;
    return clamp(proj/Math.max(1,blendZone)+.5,0,1);
  });
}
/** Applies a joint delta to a mesh using smooth axis weights. */
function deformVertices(vertices,start,joint,angleRad,opts={}){
  const weights=opts.weights||axisWeights(vertices,start,joint,opts),c=Math.cos(angleRad),s=Math.sin(angleRad);
  return vertices.map((v,i)=>{
    const w=weights[i],a=angleRad*w,ca=Math.cos(a),sa=Math.sin(a),x=v.x-joint.x,y=v.y-joint.y;
    return {...v,x:joint.x+x*ca-y*sa,y:joint.y+x*sa+y*ca,weight:w};
  });
}
function contract(){return {name:'NexStickMeshDeformerV1',version:VERSION,authority:'surface-only',mutatesMotion:false,inputs:['projected joint anchors','authored layer geometry'],outputs:['continuous ribbon mesh/path','optional vertex weights'],features:['continuous elbow/knee skin','axis weights','joint volume preservation','deterministic seek-safe geometry'],forbidden:['motion synthesis','joint retarget authority','world contact correction']};}
module.exports={version:VERSION,contract,ribbon,ribbonSvg,axisWeights,deformVertices,_math:{clamp,mix,sub,add,length,norm,perp,dot,bendAngle,centerline}};
