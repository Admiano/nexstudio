from pathlib import Path
from playwright.sync_api import sync_playwright
from batch9_browser_utils import bundle_media_scene,bundle_media_explorer
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={'scenes':{},'explorer':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 # explorer max-copy and all palettes/source types
 page=b.new_page(viewport={'width':1720,'height':1100});page.set_content(bundle_media_explorer(root),wait_until='load');page.wait_for_timeout(600)
 tests=[]
 for palette in ['warm','cobalt','charcoal']:
  page.select_option('#mediaPalette',palette);fail=[]
  for defn in json.loads((root/'runtime/media-container-registry.js').read_text().split('=',1)[1].rstrip('\n;')):
   title='W'*defn['slots']['title']['maxCharacters'];body=('Long copy, numbers 12,345.67 and punctuation! '*20)[:defn['slots']['body']['maxCharacters']];meta='M'*defn['slots']['meta']['maxCharacters']
   result=page.evaluate('''([id,title,body,meta])=>{const d=NexMediaContainers.getDef(id),e=NexMediaContainers.create(d,{media:{type:'image',src:'data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"80\" height=\"80\"><rect width=\"80\" height=\"80\" fill=\"purple\"/></svg>'},title,body,meta});document.body.append(e);NexMediaContainers.fitText(e);const bad=[...e.querySelectorAll('.media-title,.media-body,.media-meta')].some(n=>n.scrollWidth>n.clientWidth+2||n.scrollHeight>n.clientHeight+2);e.remove();return bad}''',[defn['slug'],title,body,meta])
   if result:fail.append(defn['id'])
  tests.append({'palette':palette,'failures':fail})
 report['explorer']['maxCopy']=tests
 if any(x['failures'] for x in tests):errors.append('Text overflow in explorer')
 for name,w,h in [('product-demo',1920,1080),('creator-profile',1080,1080),('photo-story',1080,1920)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_media_scene(root,name),wait_until='load');pg.wait_for_timeout(400);samples=[]
  for t in [0,.5,1.2,2.8,5.6,8.6,11.9]:
   pg.evaluate('(t)=>seekComposition(t)',t)
   d=pg.evaluate('''()=>{const W=innerWidth,H=innerHeight;return[...document.querySelectorAll('.scene-item')].map(x=>{const r=x.getBoundingClientRect();return{id:x.dataset.container,x:r.x,y:r.y,right:r.right,bottom:r.bottom,off:r.right<0||r.bottom<0||r.x>W||r.y>H}})}''')
   samples.append({'t':t,'offscreen':[x['id'] for x in d if x['off']]})
  report['scenes'][name]=samples
  if any(s['offscreen'] for s in samples):errors.append(name+' offscreen')
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors
(root/'reports/batch9-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
