window.NexMotion = (() => {
  const registry=window.NEX_MOTIONS||[];
  const easeFns={
    none:t=>t, linear:t=>t,
    'power1.out':t=>1-(1-t)*(1-t),
    'power2.out':t=>1-Math.pow(1-t,3),
    'power2.inOut':t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,
    'power3.out':t=>1-Math.pow(1-t,4),
    'power3.inOut':t=>t<.5?8*Math.pow(t,4):1-Math.pow(-2*t+2,4)/2,
    'expo.out':t=>t===1?1:1-Math.pow(2,-10*t),
    'back.out(1.7)':t=>{const c1=1.7,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)},
    'sine.inOut':t=>-(Math.cos(Math.PI*t)-1)/2
  };
  const energyMap={low:{amp:.72,time:1.18,cycles:2},medium:{amp:1,time:1,cycles:3},high:{amp:1.28,time:.82,cycles:4}};
  const q=t=>typeof t==='string'?document.querySelector(t):t;
  const clamp=(v,a=0,b=1)=>Math.min(b,Math.max(a,v));
  const ease=(name,p)=>(easeFns[name]||easeFns['power2.out'])(clamp(p));
  function posValue(pos,cursor=0){if(typeof pos==='number')return pos;if(pos==null)return cursor;if(typeof pos==='string'){if(pos.startsWith('+='))return cursor+Number(pos.slice(2));if(pos.startsWith('-='))return cursor-Number(pos.slice(2));}return cursor}
  class MotionTimeline{
    constructor(opts={}){this.base=gsap.timeline({paused:true,defaults:opts.defaults||{}});this.custom=[];this.cursor=0;this.now=0;this.paused=true;this.timer=null;this.labels={};}
    addLabel(name,pos){this.labels[name]=posValue(pos,this.cursor);if(this.base.addLabel)this.base.addLabel(name,this.labels[name]);return this}
    _pos(pos){if(typeof pos==='string'&&this.labels[pos]!=null)return this.labels[pos];return posValue(pos,this.cursor)}
    _add(method,target,a,b,pos){const p=this._pos(pos);if(method==='fromTo')this.base.fromTo(target,a,b,p);else this.base[method](target,a,p);const vars=method==='fromTo'?b:a;const d=Number(vars?.duration||0),delay=Number(vars?.delay||0),repeat=Math.max(0,Number(vars?.repeat||0));this.cursor=Math.max(this.cursor,p+delay+d*(1+repeat));return this}
    from(target,vars,pos){return this._add('from',target,vars,null,pos)}
    to(target,vars,pos){return this._add('to',target,vars,null,pos)}
    fromTo(target,a,b,pos){return this._add('fromTo',target,a,b,pos)}
    set(target,vars,pos){const p=this._pos(pos);this.base.set(target,vars,p);this.cursor=Math.max(this.cursor,p);return this}
    addUpdate(start,duration,fn,easing='none'){start=this._pos(start);duration=Math.max(0,Number(duration)||0);this.custom.push({start,duration,fn,easing});this.cursor=Math.max(this.cursor,start+duration);return this}
    duration(){return Math.max(this.cursor,Number(this.base.duration?.()||0))}
    seek(t){this.now=clamp(Number(t)||0,0,this.duration());this.base.seek(this.now);for(const u of this.custom){const raw=u.duration===0?(this.now>=u.start?1:0):clamp((this.now-u.start)/u.duration);u.fn(ease(u.easing,raw),raw,this.now)}return this}
    time(v){return v==null?this.now:this.seek(v)}
    progress(v){return v==null?(this.duration()?this.now/this.duration():0):this.seek(v*this.duration())}
    pause(){if(this.timer)cancelAnimationFrame(this.timer);this.timer=null;this.paused=true;return this}
    play(from){if(from!=null)this.seek(from);this.pause();this.paused=false;const startValue=this.now,startTime=performance.now(),total=this.duration();const tick=now=>{if(this.paused)return;const t=startValue+(now-startTime)/1000;if(t>=total){this.seek(total);this.pause();return}this.seek(t);this.timer=requestAnimationFrame(tick)};this.timer=requestAnimationFrame(tick);return this}
    restart(){this.seek(0);return this.play()}
    kill(){return this.pause()}
  }
  function getDef(id){if(typeof id==='object')return id;return registry.find(x=>x.id===id||x.key===id)||null}
  function effectLayer(target,className,tag='div'){
    let el=target.querySelector?.(`:scope > [data-motion-layer="${className}"]`);
    if(!el){el=document.createElement(tag);el.dataset.motionLayer=className;el.className=`motion-layer ${className}`;target.appendChild(el)}return el;
  }
  function ensurePositioned(el){const cs=getComputedStyle(el);if(cs.position==='static')el.style.position='relative';if(cs.overflow==='visible'&&!el.classList.contains('motion-allow-overflow'))el.style.overflow='hidden'}
  function optionsFor(def,options={}){const energy=energyMap[options.energy||options.motionEnergy||'medium']||energyMap.medium;const intensity=Number(options.intensity??1)*energy.amp;const duration=Number(options.duration??def.duration.recommended)*energy.time;return {def,energy,intensity,duration,delay:Number(options.delay||0),ease:options.ease||options.easing||def.defaultEase||'power2.out',cycles:Math.max(1,Math.floor(options.cycles||energy.cycles)),...options}}
  function addCycles(tl,target,frames,start,duration,cycles,easeName='sine.inOut'){
    const seg=duration/(frames.length*cycles);let at=start;
    for(let c=0;c<cycles;c++)for(const vars of frames){tl.to(target,{...vars,duration:seg,ease:easeName},at);at+=seg}
  }
  function drawPaths(target,tl,o,start){let paths=[];if(target.matches?.('path'))paths=[target];else paths=[...target.querySelectorAll?.('svg path, path')||[]];if(!paths.length){const svg=effectLayer(target,'motion-draw-layer','svg');svg.setAttribute('viewBox','0 0 300 180');svg.innerHTML='<path d="M18 125 C70 18 152 171 282 49"/>';paths=[svg.querySelector('path')]}paths.forEach((path,i)=>{let len=300;try{len=path.getTotalLength()||300}catch(_){}path.style.strokeDasharray=String(len);tl.addUpdate(start+i*.05,o.duration*.9,(p)=>{path.style.strokeDashoffset=String(len*(1-p));path.style.opacity=String(p)},o.ease)});}
  function apply(target,id,options={}){
    target=q(target);const def=getDef(id);if(!target||!def)throw new Error(`Unknown motion or target: ${id}`);if(def.subtype==='transition')throw new Error('Use NexMotion.transition() for scene transitions.');ensurePositioned(target);const o=optionsFor(def,options),tl=new MotionTimeline({defaults:{ease:o.ease}}),s=o.delay,d=o.duration,a=o.intensity;target.dataset.activeMotion=def.id;target.style.transformOrigin=options.transformOrigin||'50% 50%';
    const builders={
      'cut-paper-pop':()=>{tl.fromTo(target,{opacity:0,scale:.34,rotation:-6*a,x:-12*a,y:18*a},{opacity:1,scale:1.06,rotation:1.2*a,x:0,y:0,duration:d*.72,ease:'back.out(1.7)'},s);tl.to(target,{scale:1,rotation:0,duration:d*.28,ease:'power2.out'},s+d*.72)},
      'paper-slide':()=>tl.fromTo(target,{opacity:0,x:-105*a,y:16*a,rotation:-2*a},{opacity:1,x:0,y:0,rotation:0,duration:d,ease:o.ease},s),
      'drop-and-settle':()=>{tl.fromTo(target,{opacity:0,y:-145*a,rotation:6*a,scale:.94},{opacity:1,y:8*a,rotation:-1.2*a,scale:1.02,duration:d*.68,ease:'back.out(1.7)'},s);tl.to(target,{y:0,rotation:0,scale:1,duration:d*.32,ease:'power2.out'},s+d*.68)},
      'unfold':()=>{target.style.transformOrigin=options.transformOrigin||'0% 50%';tl.fromTo(target,{opacity:0,scaleX:.08,scaleY:.92,rotationY:-72*a,skewY:-4*a},{opacity:1,scaleX:1,scaleY:1,rotationY:0,skewY:0,duration:d,ease:'power2.inOut'},s)},
      'peel-reveal':()=>{const peel=effectLayer(target,'motion-peel-layer');tl.fromTo(target,{opacity:.2,scale:.97},{opacity:1,scale:1,duration:d*.65,ease:'power2.out'},s+d*.2);tl.fromTo(peel,{opacity:1,x:0,y:0,rotation:0,scale:1},{opacity:0,x:115*a,y:-55*a,rotation:24*a,scale:.82,duration:d,ease:o.ease},s)},
      'stamp-impact':()=>{const ring=effectLayer(target,'motion-impact-ring');tl.fromTo(target,{opacity:0,scale:1.85,rotation:-5*a},{opacity:1,scale:.93,rotation:1.2*a,duration:d*.58,ease:'power3.out'},s);tl.to(target,{scale:1,rotation:0,duration:d*.42,ease:'back.out(1.7)'},s+d*.58);tl.fromTo(ring,{opacity:.75,scale:.2},{opacity:0,scale:1.55,duration:d*.58,ease:'power2.out'},s+d*.28)},
      'draw-on':()=>drawPaths(target,tl,o,s),
      'ink-reveal':()=>{const ink=effectLayer(target,'motion-ink-mask');tl.addUpdate(s,d,(p)=>{ink.style.clipPath=`inset(0 ${100-p*100}% 0 0 round 18px)`;ink.style.opacity=String(p<.98?1:0);target.style.setProperty('--motion-reveal',String(p));target.style.opacity=String(.25+.75*p)},o.ease)},
      'scale-bounce':()=>{tl.fromTo(target,{opacity:0,scale:.18,rotation:-3*a},{opacity:1,scale:1.09,rotation:.8*a,duration:d*.72,ease:'back.out(1.7)'},s);tl.to(target,{scale:1,rotation:0,duration:d*.28,ease:'power2.out'},s+d*.72)},
      'page-flip':()=>{target.style.transformOrigin=options.transformOrigin||'0% 50%';tl.fromTo(target,{opacity:0,rotationY:-92*a,x:-25*a,scale:.98},{opacity:1,rotationY:0,x:0,scale:1,duration:d,ease:'power2.inOut'},s)},
      'pulse':()=>addCycles(tl,target,[{scale:1+.075*a},{scale:1}],s,d,Math.max(1,Math.min(2,o.cycles)),'sine.inOut'),
      'wiggle':()=>addCycles(tl,target,[{rotation:-3.5*a,x:-2*a},{rotation:3.5*a,x:2*a},{rotation:0,x:0}],s,d,Math.max(1,Math.min(2,o.cycles)),'sine.inOut'),
      'tick-confirm':()=>{const badge=effectLayer(target,'motion-confirm-layer');badge.innerHTML='<svg viewBox="0 0 80 80"><circle cx="40" cy="40" r="34"/><path d="M22 41 L34 53 L59 27"/></svg>';const circle=badge.querySelector('circle'),path=badge.querySelector('path');[circle,path].forEach(x=>{let len=180;try{len=x.getTotalLength()||180}catch(_){}x.style.strokeDasharray=String(len);tl.addUpdate(s,d*.72,p=>{x.style.strokeDashoffset=String(len*(1-p));x.style.opacity=String(p)},'power2.out')});tl.fromTo(badge,{opacity:0,scale:.45,rotation:-10},{opacity:1,scale:1,rotation:0,duration:d,ease:'back.out(1.7)'},s)},
      'numeric-count':()=>{let el=target.matches?.('[data-motion-number]')?target:target.querySelector?.('[data-motion-number]');if(!el){el=effectLayer(target,'motion-counter-badge');el.dataset.motionNumber=String(options.to??100)}const raw=String(el.dataset.motionNumber||options.to||el.textContent||'100'),to=Number(String(raw).replace(/[^0-9.-]/g,''))||100,from=Number(options.from||0),prefix=options.prefix??(raw.match(/^\D+/)?.[0]||''),suffix=options.suffix??(raw.match(/\D+$/)?.[0]||'');tl.addUpdate(s,d,p=>{const value=from+(to-from)*p;el.textContent=`${prefix}${options.decimals?value.toFixed(options.decimals):Math.round(value).toLocaleString()}${suffix}`},o.ease)},
      'colour-fill':()=>{const fill=effectLayer(target,'motion-colour-fill');fill.style.background=options.color||'var(--primary)';tl.addUpdate(s,d,p=>{fill.style.clipPath=`inset(0 ${100-p*100}% 0 0)`;fill.style.opacity=String(.84*p)},o.ease)},
      'rotate':()=>{tl.fromTo(target,{rotation:Number(options.fromRotation||0)},{rotation:Number(options.toRotation??360)*a,duration:d,ease:o.ease},s);tl.set(target,{rotation:0},s+d)},
      'open-and-close':()=>{target.style.transformOrigin=options.transformOrigin||'0% 50%';tl.to(target,{rotationY:-72*a,scaleX:.84,duration:d*.42,ease:'power2.inOut'},s);tl.to(target,{rotationY:0,scaleX:1,duration:d*.58,ease:'power2.inOut'},s+d*.42)},
      'connect':()=>{let from=target.querySelector?.('[data-connect-from]'),to=target.querySelector?.('[data-connect-to]');if(!from||!to){const nodes=effectLayer(target,'motion-connect-nodes');nodes.innerHTML='<i data-connect-from></i><i data-connect-to></i>';from=nodes.children[0];to=nodes.children[1]}const svg=effectLayer(target,'motion-connect-layer','svg');svg.setAttribute('viewBox','0 0 300 180');svg.innerHTML='<path/>';const path=svg.querySelector('path');const updatePath=()=>{const r=target.getBoundingClientRect(),a=from.getBoundingClientRect(),b=to.getBoundingClientRect();const x1=(a.left+a.width/2-r.left)/Math.max(r.width,1)*300,y1=(a.top+a.height/2-r.top)/Math.max(r.height,1)*180,x2=(b.left+b.width/2-r.left)/Math.max(r.width,1)*300,y2=(b.top+b.height/2-r.top)/Math.max(r.height,1)*180;path.setAttribute('d',`M${x1} ${y1} C${x1+65} ${y1-42} ${x2-65} ${y2+42} ${x2} ${y2}`)};updatePath();let len=340;try{len=path.getTotalLength()||340}catch(_){}path.style.strokeDasharray=String(len);tl.addUpdate(s,d,p=>{updatePath();path.style.strokeDashoffset=String(len*(1-p));path.style.opacity=String(p)},o.ease)},
      'marker-highlight':()=>{let el=target.matches?.('[data-motion-type="text"],[data-motion-type="caption"]')?target:(target.querySelector?.('[data-motion-type="text"],[data-motion-type="caption"],h1,h2,h3,p')||target);ensurePositioned(el);const mark=effectLayer(el,'motion-marker-layer');tl.addUpdate(s,d,p=>{mark.style.transform=`scaleX(${p}) rotate(${-1.2*a}deg)`;mark.style.opacity=String(.78*p)},o.ease)},
      'type-or-write':()=>{let el=target.matches?.('[data-motion-type="text"],[data-motion-type="caption"]')?target:(target.querySelector?.('[data-motion-type="text"],[data-motion-type="caption"],h1,h2,h3,p')||target);const value=options.text??el.dataset.motionText??el.textContent;el.dataset.motionText=value;tl.addUpdate(s,d,p=>{el.textContent=value.slice(0,Math.round(value.length*p));el.style.opacity=String(p===0?0:1)},'none')},
      'paper-flutter':()=>addCycles(tl,target,[{rotationX:1.4*a,rotationY:-1.1*a,rotation:-.7*a},{rotationX:-1.1*a,rotationY:1.3*a,rotation:.6*a},{rotationX:0,rotationY:0,rotation:0}],s,d,o.cycles,'sine.inOut'),
      'subtle-float':()=>addCycles(tl,target,[{y:-8*a,rotation:.45*a},{y:2*a,rotation:-.25*a},{y:0,rotation:0}],s,d,o.cycles,'sine.inOut'),
      'shadow-breathing':()=>{const shadow=effectLayer(target,'motion-shadow-layer');tl.addUpdate(s,d,p=>{const wave=(1-Math.cos(p*Math.PI*2*o.cycles))/2;shadow.style.transform=`translate(-50%,-50%) scale(${.84+.2*wave*a})`;shadow.style.opacity=String(.12+.18*wave)},'none')},
      'grain-drift':()=>{let grain=target.querySelector?.('.object-grain,.grain');if(!grain)grain=effectLayer(target,'motion-grain-layer');tl.addUpdate(s,d,p=>{const x=Math.sin(p*Math.PI*2*o.cycles)*9*a,y=Math.cos(p*Math.PI*2*o.cycles)*6*a;grain.style.transform=`translate(${x}px,${y}px)`;grain.style.opacity=String(.12+.08*Math.sin(p*Math.PI*2*o.cycles)**2)},'none')},
      'ink-jitter':()=>{const frames=[];for(let i=0;i<o.cycles;i++)frames.push({x:(i%2?-1:1)*1.4*a,rotation:(i%2?-1:1)*.45*a},{x:0,rotation:0});addCycles(tl,target,frames,s,d,1,'sine.inOut')}
    };
    const fn=builders[def.key];if(!fn)throw new Error(`Motion builder missing: ${def.key}`);fn();tl.seek(0);target.__nexMotionTimeline=tl;return tl;
  }
  function prepareScenePair(outgoing,incoming){outgoing=q(outgoing);incoming=q(incoming);if(!outgoing||!incoming)throw new Error('Transition requires outgoing and incoming scenes');const parent=outgoing.parentElement;if(parent!==incoming.parentElement)throw new Error('Transition scenes must share a parent');ensurePositioned(parent);parent.style.perspective='1400px';[outgoing,incoming].forEach(x=>{x.style.position='absolute';x.style.inset='0';x.style.width='100%';x.style.height='100%';x.style.transformOrigin='50% 50%';x.style.backfaceVisibility='hidden'});return {outgoing,incoming,parent}}
  function switchAt(tl,start,duration,outgoing,incoming,at=.5){tl.addUpdate(start,duration,(p)=>{if(p<at){outgoing.style.opacity='1';incoming.style.opacity='0'}else{outgoing.style.opacity='0';incoming.style.opacity='1'}},'none')}
  function transition(outgoing,incoming,id,options={}){
    const def=getDef(id);if(!def||def.subtype!=='transition')throw new Error(`Unknown transition: ${id}`);const pair=prepareScenePair(outgoing,incoming),o=optionsFor(def,options),tl=new MotionTimeline(),s=o.delay,d=o.duration,a=o.intensity,{parent}=pair;outgoing=pair.outgoing;incoming=pair.incoming;const overlay=effectLayer(parent,`transition-${def.key}`);overlay.classList.add('transition-motion-layer');
    const builders={
      'page-turn':()=>{incoming.style.opacity='1';incoming.style.zIndex='1';outgoing.style.zIndex='2';outgoing.style.transformOrigin='0% 50%';tl.fromTo(outgoing,{opacity:1,rotationY:0,x:0},{opacity:1,rotationY:-98*a,x:-42*a,duration:d,ease:'power2.inOut'},s);tl.addUpdate(s,d,p=>{overlay.style.opacity=String(Math.sin(p*Math.PI)*.55);overlay.style.transform=`translateX(${-10+65*p}%)`},'none');tl.addUpdate(s,d,p=>{outgoing.style.opacity=String(p<.98?1:0);incoming.style.opacity='1'},'none')},
      'paper-wipe':()=>{tl.fromTo(overlay,{opacity:1,x:-2200,rotation:-2*a},{opacity:1,x:2200,rotation:1*a,duration:d,ease:'power3.inOut'},s);switchAt(tl,s,d,outgoing,incoming,.49)},
      'torn-paper-reveal':()=>{incoming.style.opacity='1';incoming.style.zIndex='1';outgoing.style.zIndex='2';tl.addUpdate(s,d,p=>{incoming.style.opacity='1';outgoing.style.clipPath=`inset(0 ${p*101}% 0 0)`;overlay.style.transform=`translateX(${p*112-8}%)`;overlay.style.opacity=String(p<.98?1:0)},o.ease)},
      'collage-push':()=>{const dist=parent.clientWidth*.56*a;incoming.style.opacity='1';incoming.style.zIndex='1';outgoing.style.zIndex='2';tl.fromTo(outgoing,{x:0,rotation:0,scale:1},{x:-dist,rotation:-5*a,scale:.95,duration:d,ease:'expo.out'},s);tl.fromTo(incoming,{x:dist,rotation:5*a,scale:.95},{x:0,rotation:0,scale:1,duration:d,ease:'expo.out'},s);tl.addUpdate(s,d,p=>{incoming.style.opacity='1';outgoing.style.opacity=String(p<.96?1:0)},'none')},
      'tape-peel':()=>{incoming.style.opacity='1';incoming.style.zIndex='1';outgoing.style.zIndex='2';tl.addUpdate(s,d,()=>{incoming.style.opacity='1'},'none');tl.fromTo(overlay,{opacity:1,x:0,y:0,rotation:-2,scaleX:1},{opacity:.2,x:620*a,y:-160*a,rotation:26*a,scaleX:.45,duration:d*.46,ease:'power3.out'},s);tl.fromTo(outgoing,{opacity:1,y:0,rotationX:0,scale:1},{opacity:0,y:-260*a,rotationX:28*a,scale:.94,duration:d*.65,ease:'power3.inOut'},s+d*.28)},
      'card-stack-shuffle':()=>{const dist=parent.clientWidth*.66*a;incoming.style.opacity='1';incoming.style.zIndex='1';outgoing.style.zIndex='2';tl.addUpdate(s,d,()=>{incoming.style.opacity='1'},'none');tl.fromTo(outgoing,{x:0,y:0,rotation:0,scale:1},{x:dist,y:-80*a,rotation:12*a,scale:.9,duration:d,ease:'back.out(1.7)'},s);tl.fromTo(incoming,{x:-parent.clientWidth*.16*a,y:65*a,rotation:-5*a,scale:.9},{x:0,y:0,rotation:0,scale:1,duration:d,ease:'back.out(1.7)'},s);tl.addUpdate(s,d,p=>{outgoing.style.opacity=String(p<.94?1:0)},'none')},
      'crumple-transition':()=>{incoming.style.opacity='0';incoming.style.zIndex='2';outgoing.style.zIndex='1';tl.fromTo(outgoing,{opacity:1,scale:1,rotation:0},{opacity:0,scale:.08,rotation:-28*a,duration:d*.58,ease:'power2.inOut'},s);tl.fromTo(overlay,{opacity:0,scale:.25,rotation:-25},{opacity:1,scale:1,rotation:8,duration:d*.38,ease:'back.out(1.7)'},s+d*.28);tl.to(overlay,{opacity:0,scale:.35,rotation:30,duration:d*.34,ease:'power2.in'},s+d*.62);tl.fromTo(incoming,{opacity:0,scale:.68,rotation:8*a},{opacity:1,scale:1,rotation:0,duration:d*.48,ease:'back.out(1.7)'},s+d*.52)}
    };const fn=builders[def.key];if(!fn)throw new Error(`Transition builder missing: ${def.key}`);fn();tl.seek(0);parent.__nexMotionTimeline=tl;return tl;
  }
  function createTimeline(options={}){return new MotionTimeline(options)}
  return {registry,getDef,apply,transition,createTimeline,MotionTimeline};
})();
