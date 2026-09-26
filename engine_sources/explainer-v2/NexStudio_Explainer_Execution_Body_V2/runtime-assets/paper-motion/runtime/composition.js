(() => {
 const root=document.querySelector('[data-composition-id="foundation-demo"]');
 const ratio=new URLSearchParams(location.search).get('ratio')||root.dataset.ratio||'landscape'; root.dataset.ratio=ratio;
 const categories=[
  {scene:'#scene1',ids:NexFoundation.registry.filter(x=>x.subtype==='surface').slice(0,5)},
  {scene:'#scene2',ids:NexFoundation.registry.filter(x=>x.subtype==='edge').slice(0,5)},
  {scene:'#scene3',ids:NexFoundation.registry.filter(x=>x.subtype==='shadow').slice(0,5)},
  {scene:'#scene4',ids:NexFoundation.registry.filter(x=>x.subtype==='print').slice(0,5)},
  {scene:'#scene5',ids:NexFoundation.registry.filter(x=>x.subtype==='fastener').slice(0,5)}
 ];
 categories.forEach(cat=>{const row=document.querySelector(cat.scene+' .row');cat.ids.forEach(def=>row.appendChild(NexFoundation.create(def)));});
 const tl=gsap.timeline({paused:true});
 const starts=[0,2.7,5.4,8.1,10.8];
 categories.forEach((cat,idx)=>{const s=starts[idx],scene=document.querySelector(cat.scene);tl.fromTo(scene,{opacity:0,x:80},{opacity:1,x:0,duration:.55,ease:'power3.out'},s+.1);tl.fromTo(cat.scene+' .scene-header',{opacity:0,y:38},{opacity:1,y:0,duration:.55,ease:'expo.out'},s+.16);tl.fromTo(cat.scene+' .paper-component',{opacity:0,y:65,scale:.78,rotation:-4},{opacity:1,y:0,scale:1,rotation:0,duration:.72,ease:'back.out(1.7)',stagger:.09},s+.26);if(idx<categories.length-1){tl.fromTo(`#wipe${idx+1}`,{x:-2200,rotation:-2},{x:2200,rotation:1,duration:.62,ease:'power2.inOut'},s+2.17);tl.fromTo(scene,{opacity:1},{opacity:0,duration:.01,ease:'none'},s+2.76);}});
 tl.fromTo('#wipe5',{x:-2200,rotation:-2},{x:2200,rotation:1,duration:.62,ease:'power2.inOut'},13.0);
 tl.fromTo('#scene5',{opacity:1},{opacity:0,duration:.01,ease:'none'},13.32);
 tl.fromTo('#finalScene',{opacity:0,x:80},{opacity:1,x:0,duration:.6,ease:'power3.out'},13.33);tl.fromTo('.final-mark',{opacity:0,y:75,scale:.86,rotation:-2},{opacity:1,y:0,scale:1,rotation:0,duration:.9,ease:'back.out(1.7)'},13.52);tl.fromTo('.final-sub',{opacity:0,y:30},{opacity:1,y:0,duration:.65,ease:'expo.out'},13.90);
 window.__timelines=window.__timelines||{};window.__timelines['foundation-demo']=tl;
 const params=new URLSearchParams(location.search);if(params.has('t')){tl.seek(Number(params.get('t')))}else if(params.get('autoplay')==='1'){tl.play()}else{tl.seek(0)}
 window.seekComposition=t=>tl.seek(t);
})();
