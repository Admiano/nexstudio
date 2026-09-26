/* Adapter keeps RC1 scene families closed-world while allowing a plan to
 * replace generic demo modules with a deterministic primitive composition. */
(()=>{
 const api=window.NexSceneRigs;if(!api||api.__visualConstructionAdapter)return;
 const originalCreate=api.create;
 api.create=(def,config={})=>{
  const el=originalCreate(def,config);
  const plan=config.visualConstruction;
  if(!plan||!window.NexVisualConstructions)return el;
  el.dataset.visualDominance=config.visualDominance||plan.dominanceMode||'hybrid';
  if(plan.continuity){el.dataset.continuityObjectId=plan.continuity.objectId;el.dataset.continuityState=plan.continuity.state;}
  el.querySelectorAll('.sr-slot[data-part="media"],.sr-slot[data-part="data"],.sr-slot[data-part="workflow"]').forEach(node=>node.remove());
  const layout=el.querySelector('.sr-layout');if(!layout)return el;
  /* scene-rigs.js now understands the construction slot natively. Older
   * registry snapshots may not, so only add it when the slot is absent. */
  if(!layout.querySelector('.sr-slot[data-part="construction"]')){
   const slot=document.createElement('div');slot.className='sr-slot sr-slot-construction';slot.dataset.part='construction';slot.dataset.slug=plan.constructionId||'visual-construction';
   slot.append(window.NexVisualConstructions.create(plan));layout.insertBefore(slot,layout.firstElementChild);
  }
  const set=(node,key,value)=>node?.style.setProperty(key,value,'important');
  const construction=layout.querySelector('.sr-slot[data-part="construction"]');
  const typography=layout.querySelector('.sr-slot[data-part="typography"]');
  const icon=layout.querySelector('.sr-slot[data-part="icon"]');
  // Scene-rig slot borders and indexes are authoring scaffolds. They are not
  // audience content and must never leak into an encoded production frame.
  el.querySelectorAll('.sr-slot').forEach(slot=>{set(slot,'border','0');set(slot,'box-shadow','none');set(slot,'background','transparent');set(slot,'padding','0');set(slot,'overflow','visible')});
  el.querySelectorAll('.sr-index').forEach(node=>set(node,'display','none'));
  /* A construction is the explanation, so list/card scaffolding from the
   * selected RC1 typography variant must not compete with it.  Keep the
   * authored headline, while treating body/list/meta fields as optional
   * editorial support for visual-led scenes. */
  if(typography){
   typography.querySelectorAll('ol.type-list,ul.type-list,.type-body,.type-meta,.type-kicker,.type-subtitle').forEach(node=>{node.style.setProperty('display','none','important')});
  }
  set(layout,'grid-template-rows','1fr');set(layout,'gap','0');
  if(plan.dominanceMode==='typography-led'){
   set(layout,'grid-template-columns','.85fr 1.15fr');
   set(construction,'position','absolute');set(construction,'right','0');set(construction,'left','auto');set(construction,'top','0');set(construction,'bottom','auto');set(construction,'width','57%');set(construction,'height','100%');set(construction,'grid-column','2');set(construction,'grid-row','1');
   set(typography,'position','relative');set(typography,'left','auto');set(typography,'top','auto');set(typography,'width','100%');set(typography,'height','100%');set(typography,'grid-column','1');set(typography,'grid-row','1');
  } else {
   set(layout,'grid-template-columns','1fr');
   set(construction,'position','absolute');set(construction,'inset','0');set(construction,'width','100%');set(construction,'height','100%');set(construction,'grid-column','1');set(construction,'grid-row','1');
   set(typography,'position','absolute');set(typography,'left','2%');set(typography,'top','0');set(typography,'width','42%');set(typography,'height','38%');set(typography,'grid-column','1');set(typography,'grid-row','1');
  }
  set(icon,'position','absolute');set(icon,'right','2%');set(icon,'left','auto');set(icon,'top','auto');set(icon,'bottom','1%');set(icon,'width','11%');set(icon,'height','16%');
  const frame=construction?.querySelector('.sr-part-frame');if(frame){set(frame,'inset','0');set(frame,'transform','none');}
  const visual=construction?.querySelector('.nex-visual-construction');if(visual){set(visual,'width','100%');set(visual,'height','100%');}
  api.fit(el);return el;
 };
 api.__visualConstructionAdapter=true;
})();
