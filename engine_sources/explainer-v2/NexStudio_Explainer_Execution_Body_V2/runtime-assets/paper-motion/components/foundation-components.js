window.NexFoundation = (()=>{
  const registry=window.NEX_FOUNDATIONS||[];
  function sampleText(def){ if(def.subtype==='print') return '<div class="content"><div class="title">Printed<br>Motion</div><div class="meta">INK / PAPER / SIGNAL</div></div><div class="grain"></div>'; return '<div class="content"><div class="title">NEX<br>PAPER</div><div class="meta">'+def.name.toUpperCase()+'</div></div><div class="grain"></div>'; }
  function create(defOrId,config={}){
    const def=typeof defOrId==='string'?registry.find(x=>x.id===defOrId):defOrId;
    if(!def) throw new Error('Unknown foundation component');
    const wrap=document.createElement('div');wrap.className=`paper-component ${def.cssClass}`;wrap.dataset.componentId=def.id;wrap.dataset.subtype=def.subtype;wrap.setAttribute('role','img');wrap.setAttribute('aria-label',def.accessibilityLabel);
    wrap.style.setProperty('--local-scale',config.scale||1);
    if(def.subtype==='fastener'){
      wrap.innerHTML=`<div class="fastener-stage"><div class="content" style="position:absolute;inset:24px;display:flex;flex-direction:column;justify-content:space-between"><div class="title" style="font:900 22px/1 var(--display-font)">PINNED<br>IDEA</div><div class="meta" style="font:700 11px var(--mono-font);color:var(--ink-muted)">${def.name.toUpperCase()}</div></div><div class="fastener ${def.cssClass}">${def.id.includes('label')?'APPROVED':''}</div><div class="grain"></div></div>`;
    } else wrap.innerHTML=`<div class="paper-sheet">${sampleText(def)}</div>`;
    return wrap;
  }
  function animate(el,energy='medium'){
    const scale={low:.82,medium:1,high:1.18}[energy]||1; const dur={low:1.35,medium:1,high:.78}[energy]||1;
    const target=el.querySelector('.paper-sheet,.fastener-stage'); const detail=el.querySelector('.fastener,.grain');
    const tl=gsap.timeline({paused:true,defaults:{ease:'power3.out'}});
    tl.fromTo(target,{opacity:0,y:36*scale,scale:.9,rotation:-2*scale},{opacity:1,y:0,scale:1,rotation:0,duration:.65*dur,ease:'back.out(1.7)'},.08);
    if(detail) tl.fromTo(detail,{opacity:0,rotation:-8*scale,scale:.82},{opacity:1,rotation:0,scale:1,duration:.5*dur,ease:'expo.out'},.24);
    return tl;
  }
  return {registry,create,animate};
})();
