
(()=>{
  const TAU=Math.PI*2;
  const AMBER=[1.0,176/255,0.0];
  const presenceControllers=new WeakMap();
  const reduced=()=>window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const stateActivation={idle:.24,listening:.64,speaking:1.08,thinking:1,ready:.36};
  const stateScale={idle:.88,listening:1,speaking:1.045,thinking:.94,ready:.86};
  function sizeCanvas(canvas,cssSize,maxDpr=2){const dpr=Math.min(window.devicePixelRatio||1,maxDpr),px=Math.max(2,Math.round(cssSize*dpr));if(canvas.width!==px||canvas.height!==px){canvas.width=px;canvas.height=px}return {dpr,px}}
  function hostSize(host){return Math.max(18,Math.round(host.getBoundingClientRect().width||parseFloat(getComputedStyle(host).width)||36))}
  function replacementCanvas(host,old){const next=document.createElement('canvas');next.className=old?.className||'';old?.replaceWith(next);return next}
  function visibilityGate(host,onVisible,onHidden){let visible=false;const io=new IntersectionObserver(([entry])=>{const next=!!entry?.isIntersecting;visible=next;if(next)onVisible();else onHidden?.()},{rootMargin:'80px'});io.observe(host);const onDoc=()=>{if(document.hidden)onHidden?.();else if(visible)onVisible()};document.addEventListener('visibilitychange',onDoc);return ()=>{io.disconnect();document.removeEventListener('visibilitychange',onDoc)}}

  function matrixController(host,providedCanvas){
    const canvas=providedCanvas||host.querySelector('canvas');if(!canvas)return null;const ctx=canvas.getContext('2d');if(!ctx)return null;
    let raf=0,last=performance.now(),t=0,amp=.25,scale=.88,vel=0,running=false,voiceLevel=0;
    const orbiters=[{r:.62,s:2.15,p:0,sp:.42},{r:.40,s:-1.65,p:2.1,sp:.36},{r:.80,s:1.1,p:4,sp:.34}];
    function intensity(state,d,nx,ny,time,a){if(state==='listening'){const ripple=.5+.5*Math.sin(d*4.2-time*3);return .32+a*(.34+.38*ripple)}if(state==='speaking'){const voice=.5+.5*Math.sin(time*7.4-d*8.2+nx*1.7);return .34+a*(.43+.31*voice)}if(state==='thinking'){let heat=0;for(const o of orbiters){const ang=time*o.s+o.p,dx=nx-Math.cos(ang)*o.r,dy=ny-Math.sin(ang)*o.r;heat+=Math.exp(-(dx*dx+dy*dy)/(o.sp*o.sp))}return .26+.8*Math.min(1,heat)}if(state==='ready')return .68+.10*Math.cos(d*4-time*.42);return .60+.11*Math.sin(time*1.05-d*2.4)}
    function draw(){const size=hostSize(host),{dpr}=sizeCanvas(canvas,size,3);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,size,size);const state=host.dataset.state||'idle',grid=size<=30?7:size<=40?9:11,half=(grid-1)/2,spacing=(size*.72)/(grid-1),maxR=spacing*.60,c=size/2;ctx.fillStyle='#ffb000';for(let iy=0;iy<grid;iy++)for(let ix=0;ix<grid;ix++){const nx=(ix-half)/half,ny=(iy-half)/half,d=Math.hypot(nx,ny);if(d>1.12)continue;const inten=Math.max(0,Math.min(1,intensity(state,d,nx,ny,t,amp))),r=maxR*Math.exp(-d*d*1.7)*inten*scale;if(r*dpr<.5)continue;ctx.beginPath();ctx.arc(c+(ix-half)*spacing*scale,c+(iy-half)*spacing*scale,r,0,TAU);ctx.fill()}}
    function frame(now){raf=0;if(!running||reduced())return;const dt=Math.min((now-last)/1000,.05);last=now;t+=dt;const state=host.dataset.state||'idle',target=Math.min(1.35,(stateActivation[state]??.3)+voiceLevel*.34),rate=target>amp?.22:.08;amp+=(target-amp)*(1-Math.pow(1-rate,dt*60));voiceLevel*=Math.pow(.84,dt*60);const targetScale=stateScale[state]??.9;vel+=(-180*(scale-targetScale)-26*vel)*dt;scale+=vel*dt;draw();raf=requestAnimationFrame(frame)}
    const start=()=>{if(reduced()){amp=stateActivation[host.dataset.state||'idle']||.3;scale=stateScale[host.dataset.state||'idle']||.9;draw();return}if(running&&raf)return;running=true;last=performance.now();raf=requestAnimationFrame(frame)};
    const stop=()=>{running=false;if(raf){cancelAnimationFrame(raf);raf=0}};
    const ro=new ResizeObserver(()=>draw());ro.observe(host);const ungate=visibilityGate(host,start,stop);
    return {setState(v){host.dataset.state=v;if(reduced())draw();else if(running&&!raf)raf=requestAnimationFrame(frame)},setLevel(v){voiceLevel=Math.max(0,Math.min(1,Number(v)||0));if(reduced())draw();else if(running&&!raf)raf=requestAnimationFrame(frame)},dispose(){stop();ungate();ro.disconnect()}};
  }

  const FLUID_VERT='attribute vec2 a_pos; void main(){ gl_Position=vec4(a_pos,0.0,1.0); }';
  const FLUID_FRAG=`
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec2 u_resolution;uniform float u_time;uniform float u_activation;uniform vec3 u_color;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}float noise(vec2 p){vec2 i=floor(p),f=fract(p),u=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),u.x),mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.,1.)),u.x),u.y);}float fbm(vec2 p){float v=0.,a=.6;for(int i=0;i<4;i++){v+=a*noise(p);p=p*2.03+2.7;a*=.5;}return v;}
void main(){vec2 uv=gl_FragCoord.xy/u_resolution.xy;float t=u_time*(.14+.16*u_activation);vec2 d=vec2(sin(t)+.58*sin(t*1.73+1.3),cos(t*.82)+.56*cos(t*1.31+2.1));vec2 p=vec2(uv.x*1.72,uv.y*1.04)+d*(.34+.43*u_activation);vec2 q=vec2(fbm(p+d),fbm(p+vec2(3.2,1.5)-d));float f=fbm(p+(1.0+.5*u_activation)*q);float bottom=clamp(1.-uv.y,0.,1.);float anchor=smoothstep(0.,.28,uv.y);float shade=clamp(bottom+(f-.5)*(.55+.55*u_activation)*anchor,0.,1.);vec3 white=vec3(1.,.992,.94);vec3 light=mix(white,u_color,.34+.18*u_activation);vec3 dark=mix(u_color,vec3(.36,.20,0.),.24);vec3 col=white;col=mix(col,light,smoothstep(.24,.50,shade));col=mix(col,dark,smoothstep(.56,.90,shade));float radial=distance(uv,vec2(.5));float edge=1.-smoothstep(.475,.505,radial);float rim=smoothstep(.48,.43,radial)-smoothstep(.43,.35,radial);col+=vec3(1.,.77,.25)*rim*(.12+.18*u_activation);gl_FragColor=vec4(col*edge,edge);}`;
  function compile(gl,type,src){const sh=gl.createShader(type);if(!sh)return null;gl.shaderSource(sh,src);gl.compileShader(sh);if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS)){console.warn('NexMind presence shader',gl.getShaderInfoLog(sh));gl.deleteShader(sh);return null}return sh}
  function fluidController(host){
    let canvas=host.querySelector('canvas');if(!canvas)return null;const gl=canvas.getContext('webgl',{antialias:true,alpha:true});if(!gl){host.dataset.renderer='matrix';return matrixController(host,canvas)}
    const prog=gl.createProgram(),v=compile(gl,gl.VERTEX_SHADER,FLUID_VERT),f=compile(gl,gl.FRAGMENT_SHADER,FLUID_FRAG);
    const fail=()=>{try{if(prog)gl.deleteProgram(prog);if(v)gl.deleteShader(v);if(f)gl.deleteShader(f)}catch{}canvas=replacementCanvas(host,canvas);host.dataset.renderer='matrix';return matrixController(host,canvas)};
    if(!prog||!v||!f)return fail();gl.attachShader(prog,v);gl.attachShader(prog,f);gl.linkProgram(prog);if(!gl.getProgramParameter(prog,gl.LINK_STATUS))return fail();gl.useProgram(prog);host.dataset.renderer='fluid';
    const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);const pos=gl.getAttribLocation(prog,'a_pos');gl.enableVertexAttribArray(pos);gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);const uRes=gl.getUniformLocation(prog,'u_resolution'),uTime=gl.getUniformLocation(prog,'u_time'),uAct=gl.getUniformLocation(prog,'u_activation'),uColor=gl.getUniformLocation(prog,'u_color');gl.uniform3f(uColor,...AMBER);
    let raf=0,startAt=performance.now(),act=stateActivation[host.dataset.state||'idle']||.3,running=false,voiceLevel=0;
    function resize(){const size=hostSize(host),{px}=sizeCanvas(canvas,size,2);gl.viewport(0,0,px,px);gl.uniform2f(uRes,px,px)}
    function render(now){raf=0;if(!running&&!reduced())return;const target=Math.min(1.4,(stateActivation[host.dataset.state||'idle']||.3)+voiceLevel*.34);act+=(target-act)*.075;voiceLevel*=.92;gl.uniform1f(uTime,reduced()?0:(now-startAt)/1000);gl.uniform1f(uAct,act);gl.drawArrays(gl.TRIANGLES,0,6);if(running&&!reduced())raf=requestAnimationFrame(render)}
    const start=()=>{resize();if(reduced()){running=false;render(startAt);return}if(running&&raf)return;running=true;raf=requestAnimationFrame(render)};const stop=()=>{running=false;if(raf){cancelAnimationFrame(raf);raf=0}};
    const ro=new ResizeObserver(resize);ro.observe(host);const ungate=visibilityGate(host,start,stop);
    return {setState(v){host.dataset.state=v;if(reduced())render(startAt)},setLevel(v){voiceLevel=Math.max(0,Math.min(1,Number(v)||0));if(reduced())render(startAt)},dispose(){stop();ungate();ro.disconnect();gl.deleteBuffer(b);gl.deleteProgram(prog);gl.deleteShader(v);gl.deleteShader(f)}};
  }
  function initOne(host){if(presenceControllers.has(host))return;host.dataset.renderer=host.dataset.mode==='fluid'?'pending':'matrix';const c=(host.dataset.mode==='fluid'?fluidController(host):matrixController(host));if(c)presenceControllers.set(host,c)}
  function initAll(root=document){root.querySelectorAll('[data-nx-presence]').forEach(initOne)}
  window.initNexMindPresence=initAll;
  window.setNexMindPresenceState=(root,state)=>{const node=typeof root==='string'?document.querySelector(root):root;if(!node)return;const targets=node.matches?.('[data-nx-presence]')?[node]:[...node.querySelectorAll('[data-nx-presence]')];targets.forEach(el=>{el.dataset.state=state;presenceControllers.get(el)?.setState(state)})};
  window.setNexMindPresenceLevel=(root,level)=>{const node=typeof root==='string'?document.querySelector(root):root;if(!node)return;const targets=node.matches?.('[data-nx-presence]')?[node]:[...node.querySelectorAll('[data-nx-presence]')];targets.forEach(el=>presenceControllers.get(el)?.setLevel?.(level))};
  function orchestrate(){
    initAll();
    const mind=document.getElementById('mindStage');if(mind){new MutationObserver(()=>{const step=mind.dataset.step||'understand',st=step==='understand'?'listening':step==='resolve'?'ready':'thinking';window.setNexMindPresenceState(mind,st)}).observe(mind,{attributes:true,attributeFilter:['data-step','class']})}
    const prod=document.getElementById('productionStage');if(prod){new MutationObserver(()=>window.setNexMindPresenceState(prod,prod.dataset.phase==='finish'?'ready':'thinking')).observe(prod,{attributes:true,attributeFilter:['data-phase','class']})}
    const rev=document.getElementById('revisionOverlay'),input=document.getElementById('revisionInstruction'),btn=document.querySelector('.revision-review-btn');if(rev)new MutationObserver(()=>{if(rev.classList.contains('open'))window.setNexMindPresenceState(rev,'listening')}).observe(rev,{attributes:true,attributeFilter:['class']});if(input){input.addEventListener('focus',()=>window.setNexMindPresenceState(rev,'listening'));input.addEventListener('input',()=>window.setNexMindPresenceState(rev,input.value.trim()?'listening':'idle'))}if(btn)btn.addEventListener('click',()=>{window.setNexMindPresenceState(rev,'thinking');setTimeout(()=>window.setNexMindPresenceState(rev,'ready'),520)});
    const think=document.getElementById('pwThinking');if(think)new MutationObserver(()=>{if(think.classList.contains('on'))window.setNexMindPresenceState(think,'thinking')}).observe(think,{attributes:true,attributeFilter:['class']});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',orchestrate,{once:true});else orchestrate();
})();
