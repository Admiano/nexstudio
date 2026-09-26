from pathlib import Path
from playwright.sync_api import sync_playwright
from batch10_browser_utils import component_harness,bundle_scene
import json
root=Path(__file__).resolve().parents[1];errors=[];components=[];scenes=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');pg=b.new_page(viewport={'width':900,'height':650});pg.set_content(component_harness(root),wait_until='load')
 data=pg.evaluate('''()=>NEX_DATA_VISUALISATIONS.map(d=>{stage.innerHTML='';const el=NexDataVisualisations.create(d.id,d.sampleConfig);stage.append(el);const tl=NexDataVisualisations.animate(el,{duration:2.4});const target=el.querySelector('.dv-shell');const semantic=el.querySelector('.dv-bar,.dv-line,.dv-ring-value,.dv-point,.dv-number,.wf-node,.wf-edge,.dv-kpis article,.dv-ranking li,.dv-marker');const frames=[];for(const t of [0,.3,.7,1.2,1.8,2.4]){tl.seek(t);const a=getComputedStyle(target),b=semantic?getComputedStyle(semantic):null;frames.push({t,shellOpacity:Number(a.opacity),shellTransform:a.transform,semanticOpacity:b?Number(b.opacity):null,semanticTransform:b?b.transform:null,number:el.querySelector('.dv-number')?.textContent||null})}const changed=new Set(frames.map(x=>JSON.stringify([x.shellOpacity,x.shellTransform,x.semanticOpacity,x.semanticTransform,x.number]))).size;return {id:d.id,category:d.category,tweens:tl.tweens.length,duration:tl.duration(),changed,frames}})''')
 for x in data:
  if x['changed']<2:errors.append(x['id']+': no sampled animation change')
  if x['tweens']<1:errors.append(x['id']+': no tweens')
 components=data
 for name,w,h in [('data-story',1920,1080),('agent-workflow',1080,1080),('conversion-story',1080,1920)]:
  sp=b.new_page(viewport={'width':w,'height':h});sp.set_content(bundle_scene(root,name),wait_until='load')
  frames=[]
  for i in range(29):
   t=i*.5;f=sp.evaluate('''t=>{seekComposition(Math.min(14,t));const cards=[...document.querySelectorAll('.scene-card')].map(n=>({o:Number(getComputedStyle(n).opacity),tr:getComputedStyle(n).transform}));const numbers=[...document.querySelectorAll('.dv-number')].map(n=>n.textContent);return {t,cards,numbers,title:document.querySelector('.scene-title h1')?.textContent}}''',t);frames.append(f)
  dead=[]
  for i in range(1,len(frames)):
   if json.dumps(frames[i],sort_keys=True)==json.dumps(frames[i-1],sort_keys=True):dead.append(frames[i]['t'])
  # title always keeps scene nonblank, but card motion should progress in every 3-second entry phase.
  if any(not f['title'] for f in frames):errors.append(name+': blank title frame')
  scenes.append({'scene':name,'duration':14,'sampleInterval':.5,'samples':len(frames),'identicalAdjacentSamples':dead,'frames':frames})
  sp.close()
 b.close()
report={'status':'PASS' if not errors else 'FAIL','primitiveComponents':len(components),'componentTweenCount':sum(x['tweens'] for x in components),'components':components,'scenes':scenes,'errors':errors}
(root/'reports/batch10-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'components':len(components),'componentTweenCount':report['componentTweenCount'],'sceneSamples':sum(x['samples'] for x in scenes),'errors':errors},indent=2));raise SystemExit(1 if errors else 0)
