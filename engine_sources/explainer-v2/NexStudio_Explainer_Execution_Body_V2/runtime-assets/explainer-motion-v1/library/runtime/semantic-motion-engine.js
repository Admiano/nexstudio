/* Semantic motion translates authored actor/target actions into deterministic,
 * seekable DOM/SVG changes. It never invents content or uses wall-clock state. */
window.NexSemanticMotion=(()=>{
 const clamp=(value,min=0,max=1)=>Math.max(min,Math.min(max,value));
 const safe=value=>String(value||'').replace(/[^a-zA-Z0-9_-]/g,'-');
 const ease={
  precise:p=>1-Math.pow(1-p,3),
  educational:p=>p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2,
  playful:p=>{const c=1.35;return 1+(c+1)*Math.pow(p-1,3)+c*Math.pow(p-1,2)},
  energetic:p=>1-Math.pow(2,-10*p),
  technical:p=>p,
  calm:p=>-(Math.cos(Math.PI*p)-1)/2,
  'organic-controlled':p=>p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2,
 };
 const entity=(root,id)=>{const key=safe(id),nodes=[...root.querySelectorAll('[data-entity-id],[data-semantic-type]')];return nodes.find(node=>node.dataset.entityId===key||node.dataset.semanticType===key)||null};
 const paths=target=>target?[...(target.matches?.('path,line,polyline')?[target]:target.querySelectorAll('path,line,polyline'))]:[];
 const lengthOf=path=>{try{return path.getTotalLength?.()||320}catch(_){return 320}};
 const preparePath=path=>{const length=lengthOf(path);path.style.strokeDasharray=String(length);path.style.strokeLinecap='round';return length};
 const setPathProgress=(target,progress)=>paths(target).forEach(path=>{const length=preparePath(path);path.style.strokeDashoffset=String(length*(1-progress));path.style.opacity=String(progress>.001?1:0)});
 const setChildrenProgress=(target,progress)=>{const pieces=[...target.querySelectorAll('[data-motion-piece]')],children=pieces.length?pieces:[...target.children];(children.length?children:[target]).forEach((child,index)=>{const local=clamp(progress*(children.length+1)-index*.22);child.style.opacity=String(local);if(local>=.999){child.style.removeProperty('transform');child.style.removeProperty('transform-box');child.style.removeProperty('transform-origin');return}child.style.transformBox='fill-box';child.style.transformOrigin='center';child.style.transform=`scale(${.15+.85*local})`})};
 function applyAction(target,action,progress){
  const p=(ease[action.easingProfile]||ease.educational)(clamp(progress));
  target.dataset.motionAction=action.action;
  if(['extend','branch','connect','travel'].includes(action.action)){setPathProgress(target,p);return}
  if(action.action==='flow'){
   setPathProgress(target,p);
   target.style.opacity=String(p);
   target.style.transform=`translate(${action.direction==='right'?(-24+24*p):action.direction==='left'?(24-24*p):0}px,${action.direction==='down'?(-28+28*p):action.direction==='up'?(28-28*p):0}px)`;
   return;
  }
  if(action.action==='fall'){
   target.style.opacity=String(p);
   target.style.transform=`translateY(${(-95+95*p)}px)`;
   return;
  }
  if(action.action==='rise'){
   target.style.opacity=String(p);
   target.style.transform=`translateY(${(70-70*p)}px)`;
   return;
  }
  if(action.action==='open'){
   setPathProgress(target,p);
   target.style.opacity=String(p);
   return;
  }
  if(action.action==='unfold'){
   target.style.opacity=String(p);
   setChildrenProgress(target,p);
   return;
  }
  if(action.action==='orient-toward'){
   target.style.transformOrigin='50% 70%';
   target.style.transform=`rotate(${(1-p)*-5}deg)`;
   return;
  }
  if(action.action==='absorb'){
   target.style.transformOrigin='center';
   target.style.transform=`scale(${1+p*.055})`;
   target.style.filter=`saturate(${1+p*.22})`;
   return;
  }
  if(action.action==='pulse'||action.action==='transfer'){
   const wave=Math.sin(p*Math.PI);
   target.style.transformOrigin='center';
   target.style.transform=`scale(${1+wave*.075})`;
   target.style.filter=`brightness(${1+wave*.18})`;
   return;
  }
  if(action.action==='grow'||action.action==='assemble'||action.action==='transform'){
   target.style.opacity=String(p);
   target.style.transformOrigin='center';
   target.style.transform=`scale(${.78+.22*p})`;
   return;
  }
  if(action.action==='reveal'||action.action==='enter'||action.action==='replace'){
   target.style.opacity=String(p);
   target.style.transformOrigin='center';
   target.style.transform=`translateY(${(1-p)*18}px) scale(${.94+.06*p})`;
   return;
  }
  if(action.action==='highlight'||action.action==='scan'||action.action==='accumulate'){
   target.style.opacity=String(.35+.65*p);
   target.style.filter=`brightness(${1+p*.2}) saturate(${1+p*.16})`;
   return;
  }
  target.style.opacity=String(p);
 }
 function create(rig,plan,options={}){
  const timeline=NexMotion.createTimeline();
  if(!plan)return timeline;
  const construction=rig.querySelector('.nex-visual-construction');
  if(!construction)return timeline;
  const reduce=options.reducedMotion===true||matchMedia('(prefers-reduced-motion: reduce)').matches;
  const firstByActor=new Map();
  plan.actions.forEach(item=>firstByActor.set(item.actor,Math.min(firstByActor.get(item.actor)??Infinity,item.startSec)));
  plan.actions.forEach(item=>{
   const target=entity(construction,item.actor);
   if(!target)return;
   const preserved=plan.reducedMotionPlan?.preserveActions?.includes(item.id);
   if(reduce&&!preserved)return;
   const duration=reduce?Math.min(.18,item.durationSec):item.durationSec;
   timeline.addUpdate(item.startSec,duration,(progress,_raw,time)=>{
    if(time<item.startSec&&firstByActor.get(item.actor)!==item.startSec)return;
    applyAction(target,item,time<item.startSec?0:progress);
   },'none');
  });
  const cameraTarget=rig.querySelector('.sr-slot[data-part="construction"] .sr-part-frame')||construction;
  const camera=plan.cameraPlan;
  if(camera&&camera.action!=='hold')timeline.addUpdate(camera.startSec,reduce?Math.min(.18,camera.durationSec):camera.durationSec,(progress)=>{
   const p=ease.calm(progress),from=camera.scaleFrom??1,to=camera.scaleTo??1;
   const scale=from+(to-from)*p,x=(camera.translateXPercent??0)*p,y=(camera.translateYPercent??0)*p;
   cameraTarget.style.transformOrigin='50% 50%';
   cameraTarget.style.transform=`translate(${x}%,${y}%) scale(${scale})`;
  },'none');
  timeline.seek(0);
  construction.dataset.semanticMotion='ready';
  construction.__semanticMotionTimeline=timeline;
  return timeline;
 }
 return {create,applyAction,capabilities:['path-draw','growth','branching','flow','organic-unfold','continuity-camera']};
})();
