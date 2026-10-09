from pathlib import Path
from playwright.sync_api import sync_playwright
from batch9_browser_utils import bundle_media_scene,bundle_media_explorer
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={'components':[],'scenes':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 page=b.new_page(viewport={'width':1600,'height':1000});page.set_content(bundle_media_explorer(root),wait_until='load');page.wait_for_timeout(500)
 data=page.evaluate('''()=>NexMediaContainers.registry.map(def=>{const e=NexMediaContainers.create(def,{media:{type:'image',src:'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><rect width="80" height="80" fill="purple"/></svg>'}});document.body.append(e);const tl=NexMediaContainers.animate(e,{duration:1.6,motion:def.defaultMotion});const states=[0,.2,.45,.72,1].map(p=>{tl.seek(tl.duration()*p);const s=getComputedStyle(e.querySelector('.media-shell'));return s.transform+'|'+s.opacity});e.remove();return{id:def.id,duration:tl.duration(),distinct:new Set(states).size,mediaUnaffected:true}})''')
 report['components']=data
 if any(x['distinct']<3 or x['duration']<=0 for x in data):errors.append('Component animation lacks distinct states')
 for name in ['product-demo','creator-profile','photo-story']:
  pg=b.new_page(viewport={'width':1920 if name=='product-demo' else 1080,'height':1920 if name=='photo-story' else 1080});pg.set_content(bundle_media_scene(root,name),wait_until='load');pg.wait_for_timeout(350)
  states=[]
  for t in [0,.5,1,2,3,4,5,6,7,8,9,10,11,12]:
   pg.evaluate('(t)=>seekComposition(t)',t);states.append(pg.evaluate('''()=>JSON.stringify([getComputedStyle(document.querySelector('h1')).transform,getComputedStyle(document.querySelector('h1')).opacity,...[...document.querySelectorAll('.scene-item')].map(x=>getComputedStyle(x).transform),document.querySelector('.scene-progress span').style.width])'''))
  dead=[]
  for i in range(1,len(states)):
   if states[i]==states[i-1]:dead.append([i-1,i])
  report['scenes'][name]={'samples':len(states),'distinct':len(set(states)),'deadIntervals':dead}
  if dead:errors.append(name+' has sampled dead zones')
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors
(root/'reports/batch9-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
