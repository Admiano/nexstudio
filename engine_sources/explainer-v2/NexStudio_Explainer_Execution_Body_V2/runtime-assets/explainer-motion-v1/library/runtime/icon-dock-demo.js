(() => {
 const canvas=document.querySelector('#icon-dock-demo'),dock=document.querySelector('#paperIconDock'),largeStage=document.querySelector('#dockLargeStage'),cursor=document.querySelector('#dockCursor'),ring=document.querySelector('#dockClickRing');
 const phases=[
  {slug:'search',time:2.35,title:'Find anything.',body:'The lens draws itself, the handle settles, and the paper state becomes active.',code:'NexIcons.animate(icon, { motion: "cut-paper-pop" })'},
  {slug:'upload',time:5.15,title:'Move files in.',body:'The arrow rises from its tray while brand tokens recolour every editable SVG layer.',code:'NexIcons.create("upload", { treatment: "paper-cutout" })'},
  {slug:'save',time:7.95,title:'Keep the work.',body:'The slot, label and confirmation mark animate independently inside one reusable component.',code:'NexIcons.setState(icon, "completed")'},
  {slug:'share',time:10.8,title:'Connect the story.',body:'Three paper nodes and their link animate semantically—not as a generic bouncing symbol.',code:'manifest.intents = ["share_content"]'},
  {slug:'favourite',time:13.65,title:'Mark what matters.',body:'Active and completed states are semantic inputs, not manually edited SVG files.',code:'icon.dataset.state = "active"'},
  {slug:'bookmark',time:16.35,title:'Return to it.',body:'The same icon remains crisp at UI scale and expressive at full-screen video scale.',code:'size: 42 | 96 | 220'}
 ];
 const dockSlugs=['home','search','edit','upload','save','share','favourite','bookmark','settings'];
 const dockIcons=new Map(),largeIcons=new Map();
 dockSlugs.forEach((slug,i)=>{const slot=document.createElement('div');slot.className='dock-slot';slot.dataset.slug=slug;slot.dataset.short=slug.toUpperCase();const icon=NexIcons.create(slug,{size:54,state:'inactive',treatment:i%3===0?'printed-outline':'paper-cutout'});slot.appendChild(icon);dock.appendChild(slot);dockIcons.set(slug,{slot,icon});});
 phases.forEach((phase,i)=>{const wrap=document.createElement('div');wrap.className='dock-large-item';wrap.dataset.slug=phase.slug;const icon=NexIcons.create(phase.slug,{size:265,state:'active',treatment:i%2?'printed-outline':'paper-cutout'});wrap.appendChild(icon);largeStage.appendChild(wrap);largeIcons.set(phase.slug,{wrap,icon});});
 const master=NexMotion.createTimeline();
 master.fromTo('.dock-kicker',{opacity:0,y:20},{opacity:1,y:0,duration:.5,ease:'power2.out'},.16);master.fromTo('.dock-copy h1',{opacity:0,y:68,scale:.96},{opacity:1,y:0,scale:1,duration:.9,ease:'power3.out'},.28);master.fromTo('.dock-copy p',{opacity:0,y:26},{opacity:1,y:0,duration:.6,ease:'power2.out'},.78);master.fromTo('.dock-stat span',{opacity:0,y:22},{opacity:1,y:0,duration:.55,ease:'back.out(1.7)',stagger:.09},1.08);master.fromTo('.dock-workspace',{opacity:0,x:75,rotation:1.5},{opacity:1,x:0,rotation:0,duration:.9,ease:'expo.out'},.42);master.fromTo('.paper-icon-dock',{opacity:0,y:90,scale:.92},{opacity:1,y:0,scale:1,duration:.75,ease:'back.out(1.7)'},.72);
 dockIcons.forEach(({icon},slug)=>{const child=NexIcons.animate(icon,{motion:'cut-paper-pop',duration:.78,energy:'medium'});const idx=dockSlugs.indexOf(slug);master.addUpdate(1.0+idx*.07,child.duration(),p=>child.seek(p*child.duration()),'none')});
 phases.forEach((phase,i)=>{const {icon}=largeIcons.get(phase.slug),child=NexIcons.animate(icon,{motion:i%2?'paper-slide':'scale-bounce',duration:1.35,energy:'medium'});master.addUpdate(phase.time,child.duration(),p=>child.seek(p*child.duration()),'none')});
 const title=document.querySelector('#dockDetailTitle'),body=document.querySelector('#dockDetailBody'),index=document.querySelector('#dockDetailIndex'),code=document.querySelector('#dockDetailCode');
 master.addUpdate(0,19.4,(p,raw,now)=>{
  let current=phases[0],phaseIndex=0;for(let i=0;i<phases.length;i++)if(now>=phases[i].time){current=phases[i];phaseIndex=i}
  dockIcons.forEach(({slot,icon},slug)=>{const active=slug===current.slug;slot.classList.toggle('active',active);NexIcons.setState(icon,active?'active':'inactive')});
  largeIcons.forEach(({wrap},slug)=>{const active=slug===current.slug;wrap.style.opacity=active?'1':'0';wrap.style.transform=active?'scale(1)':'scale(.86)'});
  const local=Math.max(0,now-current.time),fade=clamp(local/.25);title.textContent=current.title;body.textContent=current.body;index.textContent=`0${phaseIndex+1} / ${current.slug.toUpperCase()}`;code.textContent=current.code;[title,body,index,code].forEach(el=>el.style.opacity=String(fade));
  const active=dockIcons.get(current.slug)?.slot;if(active){const cr=canvas.getBoundingClientRect(),r=active.getBoundingClientRect(),x=r.left-cr.left+r.width*.55,y=r.top-cr.top+r.height*.48;cursor.style.transform=`translate(${x}px,${y}px) rotate(${-5+fade*5}deg)`;ring.style.left=`${x}px`;ring.style.top=`${y}px`;const pulse=Math.max(0,1-local/.48);ring.style.opacity=String(pulse*.82);ring.style.transform=`translate(-50%,-50%) scale(${.25+(1-pulse)*1.2})`}
  canvas.style.setProperty('--dock-progress',String(clamp(now/19.4)));
 },'none');
 master.fromTo(cursor,{opacity:0,scale:.55},{opacity:1,scale:1,duration:.45,ease:'back.out(1.7)'},1.85);master.addUpdate(18.25,1.1,p=>{canvas.style.opacity=String(1-p*.12);document.querySelector('.dock-workspace').style.transform=`scale(${1-.025*p})`},'power2.out');master.seek(0);window.__timelines=window.__timelines||{};window.__timelines['icon-dock-demo']=master;window.seekComposition=t=>master.seek(t);window.playComposition=()=>master.restart();
 function clamp(v,a=0,b=1){return Math.min(b,Math.max(a,v))}
})();
