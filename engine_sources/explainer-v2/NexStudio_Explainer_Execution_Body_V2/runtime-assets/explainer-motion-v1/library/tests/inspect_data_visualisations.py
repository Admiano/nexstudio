from pathlib import Path
from playwright.sync_api import sync_playwright
from batch10_browser_utils import component_harness,bundle_scene
import json
root=Path(__file__).resolve().parents[1];errors=[];checks=[]
manifests=[json.loads(x.read_text()) for x in sorted((root/'manifests/data-visualisations').glob('*.json'))]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 page=browser.new_page(viewport={'width':820,'height':620});page.set_content(component_harness(root),wait_until='load')
 for d in manifests:
  cfg=json.loads(json.dumps(d['sampleConfig']));mx=d['itemLimits']['maximum']
  if d['category']=='data-visualisation':
   src=cfg.get('items') or [{'label':'Metric','value':10,'change':2}]
   cfg['items']=[dict(src[i%len(src)],label=f'I{i+1}',value=(-1 if i%5==0 else 1)*(10+i*7)) for i in range(mx)]
  else:
   cfg['nodes']=[{'id':f'n{i+1}','label':f'Step {i+1}','type':'agent' if i%3==0 else 'step'} for i in range(mx)]
   cfg['edges']=[{'from':f'n{i+1}','to':f'n{i+2}'} for i in range(mx-1)]
  res=page.evaluate('''async({id,cfg})=>{stage.innerHTML='';const el=NexDataVisualisations.create(id,cfg);stage.append(el);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));NexDataVisualisations.fitText(el);const tl=NexDataVisualisations.animate(el,{duration:2});tl.seek(tl.duration());const shell=el.querySelector('.dv-shell').getBoundingClientRect();const bad=[];el.querySelectorAll('h3,.wf-node b,.wf-node small,.dv-ranking span,.dv-row span,.dv-bar-cell b,.dv-bar-cell span,.dv-kpis small,.dv-kpis strong').forEach(n=>{if(n.scrollWidth>n.clientWidth+2||n.scrollHeight>n.clientHeight+2)bad.push({text:n.textContent,sw:n.scrollWidth,cw:n.clientWidth,sh:n.scrollHeight,ch:n.clientHeight})});const out=[...el.querySelectorAll('.wf-node,.dv-bar-cell,.dv-kpis article,.dv-ranking li,.dv-row,.dv-marker')].filter(n=>{const r=n.getBoundingClientRect();return r.left<shell.left-3||r.right>shell.right+3||r.top<shell.top-3||r.bottom>shell.bottom+3}).length;const nodes=[...el.querySelectorAll('.wf-node')].map(n=>n.getBoundingClientRect());let overlaps=0;for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j],area=Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left))*Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));if(area>20)overlaps++}return {bad,out,overlaps,rect:{w:el.getBoundingClientRect().width,h:el.getBoundingClientRect().height}}}''',{'id':d['id'],'cfg':cfg})
  checks.append({'id':d['id'],'maxItems':mx,**res})
  if res['bad']:errors.append(f"{d['id']}: {len(res['bad'])} text overflows at maximum items")
  if res['out']:errors.append(f"{d['id']}: {res['out']} children outside shell")
  if res['overlaps']:errors.append(f"{d['id']}: {res['overlaps']} workflow node overlaps")
 # responsive scenes at sampled times
 scene_checks=[]
 for name,w,h in [('data-story',1920,1080),('agent-workflow',1080,1080),('conversion-story',1080,1920)]:
  sp=browser.new_page(viewport={'width':w,'height':h});sp.set_content(bundle_scene(root,name),wait_until='load');
  for t in [0,.4,2.5,5.5,8.5,11.5,13.8]:
   r=sp.evaluate('''t=>{seekComposition(t);const body={left:0,top:0,right:innerWidth,bottom:innerHeight};const bad=[...document.querySelectorAll('.scene-card,.nex-dv')].filter(n=>{const r=n.getBoundingClientRect();return r.left<-5||r.right>innerWidth+5||r.top<-5||r.bottom>innerHeight+5}).length;const texts=[...document.querySelectorAll('.scene-title h1,.scene-title small,.dv-head h3,.wf-node b')].filter(n=>n.scrollWidth>n.clientWidth+2).length;const visible=[...document.querySelectorAll('.scene-card')].filter(n=>Number(getComputedStyle(n).opacity)>.05).length;return {bad,texts,visible}}''',t)
   scene_checks.append({'scene':name,'time':t,**r})
   if r['bad']:errors.append(f'{name}@{t}: {r["bad"]} off-canvas')
   if r['texts']:errors.append(f'{name}@{t}: {r["texts"]} text overflow')
  sp.close()
 browser.close()
report={'status':'PASS' if not errors else 'FAIL','maximumItemComponents':len(checks),'sceneSamples':len(scene_checks),'componentChecks':checks,'sceneChecks':scene_checks,'errors':errors}
(root/'reports/batch10-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'maximumItemComponents':len(checks),'sceneSamples':len(scene_checks),'errors':errors},indent=2));raise SystemExit(1 if errors else 0)
