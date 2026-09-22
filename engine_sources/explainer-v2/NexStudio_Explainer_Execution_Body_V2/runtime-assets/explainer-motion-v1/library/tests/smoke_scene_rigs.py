from pathlib import Path
from playwright.sync_api import sync_playwright
from batch13_browser_utils import harness,bundle_explorer,bundle_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];details={}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage'])
 page=b.new_page(viewport={'width':1280,'height':800});js_errors=[];page.on('pageerror',lambda e:js_errors.append(str(e)));page.set_content(harness(root));page.wait_for_timeout(150)
 result=page.evaluate('''async()=>{const out=[];for(const def of NexSceneRigs.registry){for(const variant of ['A','B']){const el=NexSceneRigs.create(def,{variant,style:'clean-editorial',energy:'medium'});document.getElementById('stage').replaceChildren(el);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const approved=[...el.querySelectorAll('[data-component-id]')].filter(x=>x!==el);const tl=NexSceneRigs.animate(el,{duration:2});tl.seek(1.1);out.push({id:def.id,variant,slots:el.querySelectorAll('.sr-slot').length,approved:approved.length,opacity:getComputedStyle(el.querySelector('.sr-shell')).opacity});} }return out}''')
 if len(result)!=72:errors.append('Expected 72 scene/variant smoke results')
 for r in result:
  if r['slots']!=4 or r['approved']<3:errors.append(r['id']+' '+r['variant']+' lower-component composition failed')
 page.close()
 # explorer filters
 page=b.new_page(viewport={'width':1440,'height':900});page.set_content(bundle_explorer(root));page.wait_for_timeout(250)
 if page.locator('.scene-card').count()!=36:errors.append('Explorer did not render 36 scene families')
 page.fill('#sceneSearch','handoff');page.wait_for_timeout(80);details['handoffFilter']=page.locator('.scene-card').count()
 if details['handoffFilter']<1:errors.append('Search filter failed')
 page.fill('#sceneSearch','');page.select_option('#sceneIntent','documentary');page.wait_for_timeout(80);details['documentaryFilter']=page.locator('.scene-card').count()
 if details['documentaryFilter']<4:errors.append('Intent filter failed')
 page.close()
 # films and transition overlap
 for name,size in [('creator-explainer',(1280,720)),('agent-workflow-film',(900,900)),('documentary-scrapbook-film',(540,960))]:
  page=b.new_page(viewport={'width':size[0],'height':size[1]});es=[];page.on('pageerror',lambda e,es=es:es.append(str(e)));page.set_content(bundle_scene(root,name));page.wait_for_timeout(200)
  if page.locator('.film-scene').count()!=8:errors.append(name+' missing film scenes')
  if name not in page.evaluate('Object.keys(window.__timelines||{})'):errors.append(name+' timeline missing')
  blanks=[]; overlaps=[]
  for t in [0.2,6.8,7.2,7.7,14.4,22.0,30.0,45.0,59.2]:
   page.evaluate('(t)=>window.seekComposition(t)',t)
   vals=page.evaluate("[...document.querySelectorAll('.film-scene')].map(x=>parseFloat(getComputedStyle(x).opacity)||0)")
   if max(vals)<.05:blanks.append(t)
   if t in [6.8,7.2,14.4] and sum(v>.05 for v in vals)>=2:overlaps.append(t)
  if blanks:errors.append(name+' blank frames '+str(blanks))
  if len(overlaps)<2:errors.append(name+' transitions did not preserve overlapping scenes')
  if es:errors.extend(name+': '+e for e in es)
  details[name]={'blankSamples':blanks,'overlapSamples':overlaps}
  page.close()
 if js_errors:errors.extend(js_errors)
 b.close()
report={'status':'PASS' if not errors else 'FAIL','sceneVariantTests':len(result),'details':details,'errors':errors};(root/'reports/batch13-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
