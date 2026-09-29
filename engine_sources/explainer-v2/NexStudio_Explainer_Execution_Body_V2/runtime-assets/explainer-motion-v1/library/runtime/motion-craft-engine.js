/* Deterministic execution layer for semantic motion. NexMind supplies actions;
 * this runtime supplies reusable physical performances without topic branches. */
window.NexMotionCraft=(()=>{
 const clamp=(value,min=0,max=1)=>Math.max(min,Math.min(max,Number(value)||0));
 const ease={
  precise:p=>1-Math.pow(1-p,3),
  educational:p=>p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2,
  playful:p=>{const c=1.25;return 1+(c+1)*Math.pow(p-1,3)+c*Math.pow(p-1,2)},
  energetic:p=>p===1?1:1-Math.pow(2,-10*p),
  technical:p=>p,
  calm:p=>-(Math.cos(Math.PI*p)-1)/2,
  'organic-controlled':p=>p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2,
 };
 const registry={
   'organic-path-grow':{action:'grow',visualClasses:['organic-path','branching-path','linear-path'],easing:'organic-controlled',continuity:true},
   'continuity-transform':{action:'transform',visualClasses:['organic-object','organic-path','branching-path','group'],easing:'organic-controlled',continuity:true},
   'positive-growth-delta':{action:'grow',visualClasses:['organic-object','organic-path','branching-path','group'],easing:'organic-controlled',continuity:true},
  'linear-extension':{action:'extend',visualClasses:['linear-path','organic-path','connector'],easing:'precise',continuity:true},
   'staggered-branch':{action:'branch',visualClasses:['branching-path','organic-path','group'],easing:'organic-controlled',continuity:true},
   'attached-unfold':{action:'unfold',visualClasses:['organic-object','organic-path','attached-surface','group'],easing:'organic-controlled',continuity:true},
   'anchor-flow':{action:'flow',visualClasses:['particle','transfer-object','organic-object','group'],easing:'precise',continuity:false},
   'flow-to':{action:'flow',visualClasses:['particle','field','transfer-object','organic-object','group'],easing:'precise',continuity:false},
  'receiver-absorb':{action:'absorb',visualClasses:['organic-object','container','node','group'],easing:'organic-controlled',continuity:true},
  'pivot-unfold':{action:'unfold',visualClasses:['organic-object','organic-path','attached-surface','group'],easing:'organic-controlled',continuity:true},
  'target-orient':{action:'orient-toward',visualClasses:['organic-object','organic-path','arrow','icon'],easing:'calm',continuity:true},
  'causal-reveal':{action:'reveal',visualClasses:['group','illustration','media','object'],easing:'educational',continuity:true},
  'scale-settle':{action:'transform',visualClasses:['group','organic-object','node','document'],easing:'organic-controlled',continuity:true},
  'pulse-response':{action:'pulse',visualClasses:['organic-object','node','field','group'],easing:'organic-controlled',continuity:true},
  'precise-transfer':{action:'transfer',visualClasses:['particle','node','transfer-object','group'],easing:'precise',continuity:false},
   'assemble-highlight':{action:'assemble',visualClasses:['group','node','data-series','organic-object'],easing:'educational',continuity:true},
   'cause-and-effect-performance':{action:'assemble',visualClasses:['group','node','data-series','organic-object'],easing:'educational',continuity:true},
 };
 const safe=value=>String(value||'').replace(/[^a-zA-Z0-9_-]/g,'-');
 const findEntity=(root,id)=>{if(!root||!id)return null;const key=safe(id);return [...root.querySelectorAll('[data-entity-id],[data-semantic-type]')].find(node=>node.dataset.entityId===key||node.dataset.semanticType===key)||null};
 const pieces=(target,selector)=>target?[...target.querySelectorAll(selector||'[data-motion-piece]')]:[];
 const paths=target=>target?[...(target.matches?.('path,line,polyline')?[target]:target.querySelectorAll('path,line,polyline'))]:[];
 const pathLength=path=>{try{return Number(path.getTotalLength?.()||320)}catch(_){return 320}};
 const draw=(path,p)=>{const length=pathLength(path);path.style.strokeDasharray=String(length);path.style.strokeDashoffset=String(length*(1-clamp(p)));path.style.opacity=String(clamp(p)>0.001?1:0)};
 const parsed=(value,fallback)=>{const parts=String(value||'').split(',').map(Number);return parts.length===2&&parts.every(Number.isFinite)?{x:parts[0],y:parts[1]}:fallback};
 const anchor=(node,name)=>parsed(node?.dataset?.[`anchor${String(name||'center').replace(/-([a-z])/g,(_,c)=>c.toUpperCase()).replace(/^./,c=>c.toUpperCase())}`],null)||({x:(node?.getBoundingClientRect?.().left||0)+(node?.getBoundingClientRect?.().width||0)/2,y:(node?.getBoundingClientRect?.().top||0)+(node?.getBoundingClientRect?.().height||0)/2});
 const rectCenter=node=>{const r=node?.getBoundingClientRect?.();return r?{x:r.left+r.width/2,y:r.top+r.height/2}:{x:0,y:0}};
 const applyTransform=(node,value)=>{if(node)node.style.transform=value};
 const pivotOrigin=node=>{if(!node)return;const x=Number(node.dataset?.pivotX),y=Number(node.dataset?.pivotY);node.style.transformBox='view-box';node.style.transformOrigin=Number.isFinite(x)&&Number.isFinite(y)?`${x}px ${y}px`:'50% 90%'};
 const organicPaths=target=>paths(target).filter(path=>path.dataset.motionPiece!=='flow-path');
 const primaryPaths=target=>organicPaths(target).filter(path=>['primary-root','primary-stem','primary-shoot'].includes(path.dataset.motionPiece||''));
 const characterFrame=(actor,progress)=>{if(!actor||actor.dataset.characterSkinSequence!=='true')return;const frames=[...actor.querySelectorAll('[data-character-skin-frame]')];if(frames.length<2)return;const index=Math.max(0,Math.min(frames.length-1,Math.round(clamp(progress)*(frames.length-1))));frames.forEach((frame,i)=>{frame.style.opacity=i===index?'1':'0'});actor.dataset.characterSkinFrame=String(index);};
 const branchPaths=target=>organicPaths(target).filter(path=>path.dataset.motionPiece==='root-branch'||path.dataset.motionPiece==='branch');
 function apply(performance, actor, target, progress, context){
  const p=clamp(progress), profile=performance.easingProfile||registry[performance.variant]?.easing||'educational', q=ease[profile]?ease[profile](p):p;
  if(!actor)return;
  characterFrame(actor,q);
  const carry=actor.dataset.continuityCarry==='true';
  const rewinding=Boolean(context?.rewind);
  if(p<=0&&actor.dataset.motionPerformance&&actor.dataset.motionPerformance!==performance.id){
   if(!rewinding)return;
   if(performance.variant==='staggered-branch'){
    const allLeaves=pieces(actor,'[data-motion-piece="leaf"]'),newLeaves=allLeaves.filter(leaf=>leaf.dataset.continuityRole==='new'),leafPieces=newLeaves.length?newLeaves:allLeaves;
    if(leafPieces.length)leafPieces.forEach(leaf=>{leaf.style.opacity='0';pivotOrigin(leaf);applyTransform(leaf,'rotate(-16deg) scale(.3,.72)')});
    else (branchPaths(actor).length?branchPaths(actor):[]).forEach(path=>draw(path,0));
   }
   return;
  }
  if(p>0){actor.dataset.motionAction=performance.action;actor.dataset.motionPerformance=performance.id;}
  if(performance.variant==='continuity-transform'){
    // A continuity transform evolves an already-established visual state. It
    // must never erase/re-draw the actor's internal SVG paths: doing so makes
    // organic objects, documents, nodes, etc. disappear before they transform.
    actor.style.opacity='1';actor.style.transformOrigin='center';applyTransform(actor,`scale(${.96+.04*q})`);return;
  }
  if(performance.variant==='organic-path-grow'||performance.variant==='linear-extension'){
    const selected=primaryPaths(actor).length?primaryPaths(actor):organicPaths(actor);
    selected.forEach(path=>draw(path,q));
    actor.style.opacity='1';
    return;
  }
  if(performance.variant==='staggered-branch'||performance.variant==='attached-unfold'){
    const allLeaves=pieces(actor,'[data-motion-piece="leaf"]'),newLeaves=allLeaves.filter(leaf=>leaf.dataset.continuityRole==='new'),leafPieces=newLeaves.length?newLeaves:allLeaves;
   if(leafPieces.length){
    const stagger=.12,span=1+stagger*Math.max(0,leafPieces.length-1);
    leafPieces.forEach((leaf,index)=>{const local=clamp(q*span-index*stagger);pivotOrigin(leaf);applyTransform(leaf,`rotate(${(1-local)*(-16+index*2)}deg) scale(${.3+.7*local},${.72+.28*local})`);leaf.style.opacity=String(local)});
    return;
   }
   const selected=branchPaths(actor).length?branchPaths(actor):organicPaths(actor);
   selected.forEach((path,index)=>draw(path,ease[profile]?ease[profile](clamp(p*1.36-index*.18)):clamp(p*1.36-index*.18)));
   return;
  }
  if(performance.variant==='anchor-flow'||performance.variant==='flow-to'||performance.variant==='precise-transfer'){
   if(p<=0){if(!carry&&actor.dataset.representation!=='sun'&&actor.dataset.visualClass!=='field')actor.style.opacity='0';return}
   if(carry){actor.style.opacity='1';return}
   if(actor.dataset.representation==='sun'||actor.dataset.visualClass==='field'){const connectors=[...(context.construction?.querySelectorAll?.(`[data-motion-connector][data-source="${performance.actor}"]`)||[])];connectors.forEach(connector=>{const visible=q<.84?q:Math.max(0,1-(q-.84)/.16);connector.style.opacity=String(visible);const flow=connector.querySelector('[data-motion-piece="flow-path"]');if(flow)draw(flow,q)});return}
   if(['branching-path','organic-path','linear-path'].includes(actor.dataset.visualClass||'')){const connectors=[...(context.construction?.querySelectorAll?.(`[data-motion-connector][data-source="${performance.actor}"]`)||[])];connectors.forEach(connector=>{const visible=q<.84?q:Math.max(0,1-(q-.84)/.16);connector.style.opacity=String(visible);const flow=connector.querySelector('[data-motion-piece="flow-path"]');if(flow)draw(flow,q)});return}
   const source=anchor(actor,performance.sourceAnchor||'entry'), receiver=performance.target?findEntity(context.construction,performance.target):null, destination=receiver?anchor(receiver,performance.targetAnchor||'attachment',):rectCenter(receiver||actor);
   const dx=destination.x-source.x,dy=destination.y-source.y;
   applyTransform(actor,`translate3d(${dx*q}px,${dy*q}px,0)`);
   const visible=q<.84?Math.min(1,.36+.64*q):Math.max(0,1-(q-.84)/.16);
   actor.style.opacity=String(visible);
   const particlePieces=pieces(actor,'[data-motion-piece="droplet"]');
   if(particlePieces.length)particlePieces.forEach((piece,index)=>{const local=clamp(q*1.35-index*.18);piece.style.opacity=String(q<.84?Math.min(1,.32+.68*local):Math.max(0,1-(q-.84)/.16))});
   const flowPaths=paths(actor).filter(path=>path.dataset.motionPiece==='flow-path');flowPaths.forEach(path=>draw(path,q));
   const connectors=[...(context.construction?.querySelectorAll?.(`[data-motion-connector][data-source="${performance.actor}"][data-target="${performance.target||''}"]`)||[])];connectors.forEach(connector=>{connector.style.opacity=String(visible);const flow=connector.querySelector('[data-motion-piece="flow-path"]');if(flow)draw(flow,q)});
   return;
  }
  if(performance.variant==='receiver-absorb'){
   actor.style.transformOrigin='center';
   applyTransform(actor,`scale(${1+q*.055})`);
   actor.style.filter=`saturate(${1+q*.18}) brightness(${1+q*.04})`;
   if(performance.target){const source=findEntity(context.construction,performance.target);if(source){source.style.opacity=String(1-q);applyTransform(source,`scale(${1-q*.25})`)}}
   return;
  }
  if(performance.variant==='pivot-unfold'||performance.variant==='attached-unfold'){
   const allLeaves=pieces(actor,'[data-motion-piece="leaf"]'),newLeaves=allLeaves.filter(leaf=>leaf.dataset.continuityRole==='new'),leaves=newLeaves.length?newLeaves:allLeaves;
   const targets=leaves.length?leaves:[actor],stagger=.12,span=1+stagger*Math.max(0,targets.length-1);
   targets.forEach((leaf,index)=>{const local=clamp(q*span-index*stagger);pivotOrigin(leaf);applyTransform(leaf,`rotate(${(1-local)*(-18+index*3)}deg) scale(${.32+.68*local},${.72+.28*local})`);leaf.style.opacity=String(local)});
   return;
  }
  if(performance.variant==='target-orient'){
   const receiver=performance.target?findEntity(context.construction,performance.target):null,from=rectCenter(actor),to=rectCenter(receiver||actor),angle=Math.max(-16,Math.min(16,Math.atan2(to.y-from.y,to.x-from.x)*180/Math.PI-90));
   actor.style.transformOrigin='50% 82%';applyTransform(actor,`rotate(${angle*q}deg)`);return;
  }
  if(performance.variant==='causal-reveal'){
   const crack=actor.querySelector('[data-motion-piece="crack"]');
   if(crack){draw(crack,q);crack.style.opacity=String(q)}
   actor.style.opacity=String(.28+.72*q);return;
  }
  if(performance.variant==='pulse-response'){
   const wave=Math.sin(q*Math.PI);actor.style.transformOrigin='center';applyTransform(actor,`scale(${1+wave*.065})`);actor.style.filter=`brightness(${1+wave*.15}) saturate(${1+wave*.12})`;return;
  }
  if(performance.variant==='cause-and-effect-performance'){
   const wave=Math.sin(q*Math.PI);actor.style.transformOrigin='center';applyTransform(actor,`scale(${1+wave*.045})`);actor.style.filter=`brightness(${1+wave*.12}) saturate(${1+wave*.08})`;
   if(target){target.style.opacity=String(Math.min(1,q));target.style.transformOrigin='center';applyTransform(target,`scale(${.72+.28*q})`)}
   return;
  }
  if(performance.variant==='positive-growth-delta'){
   const all=primaryPaths(actor).length?primaryPaths(actor):organicPaths(actor),fresh=all.filter(path=>path.dataset.continuityRole==='new'),selected=fresh.length?fresh:[];
   selected.forEach(path=>draw(path,q));actor.style.opacity='1';actor.style.transformOrigin='center';
   const wave=Math.sin(q*Math.PI);applyTransform(actor,`scale(${1+wave*.035})`);return;
  }
  if(performance.variant==='assemble-highlight'||performance.variant==='scale-settle'){
   if(carry){actor.style.opacity='1';return}
   const wave=performance.variant==='scale-settle'?q:Math.sin(q*Math.PI);actor.style.transformOrigin='center';applyTransform(actor,`scale(${performance.variant==='scale-settle'?(.9+.1*wave):(1+wave*.035)})`);actor.style.opacity=actor.dataset.continuityHero?'1':String(.2+.8*q);const produced=performance.target?findEntity(context.construction,performance.target):null;if(produced&&!produced.dataset.continuityCarry){produced.style.opacity=String(q);produced.style.transformOrigin='center';produced.style.transform=`scale(${.88+.12*q})`}if(performance.variant==='scale-settle')primaryPaths(actor).forEach(path=>draw(path,q));return;
  }
  actor.style.opacity=String(q);
 }
 function applyCamera(camera,rig,progress){
  if(!camera||!rig||camera.action==='hold')return;
  const target=findEntity(rig,camera.target),construction=rig.querySelector('.nex-visual-construction')||rig;if(!construction)return;
  const p=ease[camera.easingProfile]?ease[camera.easingProfile](clamp(progress)):clamp(progress),scale=(camera.scaleFrom??1)+((camera.scaleTo??1)-(camera.scaleFrom??1))*p;
   const x=(camera.translateXPercent||0)*p,y=(camera.translateYPercent||0)*p;construction.dataset.cameraTarget=camera.target||'';construction.dataset.cameraActionExpected=String(camera.cameraActionExpected!==false);construction.dataset.cameraActionExecuted=String(camera.cameraActionExpected===false||Math.abs(x)+Math.abs(y)+Math.abs(scale-(camera.scaleFrom??1))>.001);construction.dataset.cameraTravelDistance=String(Math.sqrt(Math.pow(scale-(camera.scaleFrom??1),2)+Math.pow(x/100,2)+Math.pow(y/100,2)));construction.dataset.cameraTargetTrackingError=String(camera.cameraTargetTrackingError??0);construction.style.transformOrigin='50% 50%';applyTransform(construction,`translate(${x}%,${y}%) scale(${scale})`);
 }
 function create(rig,plan,options={}){
  const timeline=NexMotion.createTimeline();if(!rig||!plan)return timeline;
  const construction=rig.querySelector('.nex-visual-construction')||rig;
  const reduced=options.reducedMotion===true;
  const frameRate=Number(plan.frameRate||30);
  const duration=Number(plan.durationFrames||0)/frameRate;
  const context={construction};
  [...construction.querySelectorAll('[data-motion-connector]')].forEach(connector=>{connector.style.opacity='0';const flow=connector.querySelector('[data-motion-piece="flow-path"]');if(flow)draw(flow,0)});
  (plan.performances||[]).forEach(performance=>{
   const actor=findEntity(construction,performance.actor);if(!actor)return;
   const carry=actor.dataset.continuityCarry==='true';
   if(performance.variant==='continuity-transform'){
    // Preserve the actor's settled visual pixels at frame zero; the transform
    // itself is an identity-preserving morph/scale, not a path reveal.
    actor.style.opacity='1';if(carry)actor.dataset.motionCarryPreserved='true';
   } else if(performance.variant==='organic-path-grow'||performance.variant==='linear-extension'||performance.variant==='positive-growth-delta'){
    if(carry)actor.dataset.motionCarryPreserved='true';
    const all=primaryPaths(actor).length?primaryPaths(actor):organicPaths(actor),selected=performance.variant==='positive-growth-delta'?all.filter(path=>path.dataset.continuityRole==='new'):all;selected.forEach(path=>draw(path,0));
   } else if(performance.variant==='staggered-branch'||performance.variant==='attached-unfold'){
    if(carry){actor.dataset.motionCarryPreserved='true';}else{
    const allLeaves=pieces(actor,'[data-motion-piece="leaf"]'),newLeaves=allLeaves.filter(leaf=>leaf.dataset.continuityRole==='new'),leafPieces=newLeaves.length?newLeaves:allLeaves;
    if(leafPieces.length)leafPieces.forEach(leaf=>{leaf.style.opacity='0';pivotOrigin(leaf);applyTransform(leaf,'rotate(-16deg) scale(.3,.72)')});
    else (branchPaths(actor).length?branchPaths(actor):organicPaths(actor)).forEach(path=>draw(path,0));
    }
   } else if(performance.variant==='pivot-unfold'){
    if(carry){actor.dataset.motionCarryPreserved='true';}else{
    const allLeaves=pieces(actor,'[data-motion-piece="leaf"]'),newLeaves=allLeaves.filter(leaf=>leaf.dataset.continuityRole==='new'),leafPieces=newLeaves.length?newLeaves:allLeaves;
    (leafPieces.length?leafPieces:[actor]).forEach(leaf=>{leaf.style.opacity='0';pivotOrigin(leaf);applyTransform(leaf,'rotate(-16deg) scale(.3,.72)')});
    }
   } else if(performance.variant==='anchor-flow'||performance.variant==='flow-to'||performance.variant==='precise-transfer'){
    // Transfer actors are causal content. They must not be visible during the
    // incoming scene before their event window; environmental sources such as
    // the sun remain present while their connector is animated.
    if(!carry&&actor.dataset.representation!=='sun'&&actor.dataset.visualClass!=='field')actor.style.opacity='0';
   } else if(performance.variant==='assemble-highlight'||performance.variant==='cause-and-effect-performance'){
    const produced=performance.target?findEntity(construction,performance.target):null;
    if(produced&&!produced.dataset.continuityCarry)produced.style.opacity='0';
   } else if(performance.variant==='causal-reveal'){
    const crack=actor.querySelector('[data-motion-piece="crack"]');if(crack){crack.style.opacity='0';draw(crack,0)}
   }
   const start=Number(performance.startFrame||0)/frameRate,d=Number(performance.durationFrames||1)/frameRate;
   timeline.addUpdate(start,reduced?Math.min(.16,d):d,(progress,raw,time,previous)=>apply(performance,actor,performance.target?findEntity(construction,performance.target):null,progress,{...context,rewind:Number(time)<Number(previous)-0.0001}),'none');
  });
  const camera=plan.cameraPerformance;
  if(camera&&camera.action!=='hold'){
   const start=Number(camera.startFrame||0)/frameRate,d=Number(camera.durationFrames||1)/frameRate;
   timeline.addUpdate(start,reduced?Math.min(.16,d):d,(progress)=>applyCamera(camera,rig,progress),'none');
  }
  timeline.seek(0);construction.dataset.motionPerformance='ready';construction.dataset.motionCraftVersion=plan.version||'explainer-motion-craft.v1';construction.__motionPerformanceTimeline=timeline;return timeline;
 }
 return {create,apply,applyCamera,registry,capabilities:['anchor-continuity','organic-path-growth','staggered-branch','causal-flow','pivot-unfold','target-orient','deterministic-seek']};
})();
