from pathlib import Path
from playwright.sync_api import sync_playwright
from batch13_browser_utils import harness,bundle_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];samples=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage'])
 for label,size in [('landscape',(1280,720)),('square',(900,900)),('portrait',(540,960))]:
  page=b.new_page(viewport={'width':size[0],'height':size[1]});page.set_content(harness(root));page.wait_for_timeout(100)
  for defn in page.evaluate('NexSceneRigs.registry.map(x=>x.slug)'):
   r=page.evaluate('''async(args)=>{const el=NexSceneRigs.create(args.slug,{variant:args.variant,style:args.style,title:'SUPERCALIFRAGILISTICEXPIALIDOCIOUS STORY STRUCTURE',body:'Maximum copy remains inside the scene while responsive lower components preserve their approved proportions and labels.'});document.getElementById('stage').replaceChildren(el);el.style.width=args.w+'px';el.style.height=args.h+'px';await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));NexSceneRigs.fit(el);const er=el.getBoundingClientRect(),vp={w:innerWidth,h:innerHeight};const bad=[...el.querySelectorAll('.sr-kicker,.sr-index')].filter(n=>n.scrollWidth>n.clientWidth+2||n.scrollHeight>n.clientHeight+2).length;return{left:er.left,top:er.top,right:er.right,bottom:er.bottom,bad,slots:el.querySelectorAll('.sr-slot').length}}''',{'slug':defn,'variant':'B','style':'technical-notebook','w':size[0]*.9,'h':size[1]*.84})
   if r['left']<-2 or r['top']<-2 or r['right']>size[0]+2 or r['bottom']>size[1]+2 or r['bad']:errors.append(label+' '+defn+' layout failure '+str(r))
  samples.append({'format':label,'families':36,'viewport':size});page.close()
 # film native layout at hero/transition/late frames
 for name,size in [('creator-explainer',(1920,1080)),('agent-workflow-film',(1080,1080)),('documentary-scrapbook-film',(1080,1920))]:
  page=b.new_page(viewport={'width':size[0],'height':size[1]});page.set_content(bundle_scene(root,name));page.wait_for_timeout(100)
  for t in [1,15.5,30.2,59.5]:
   page.evaluate('(t)=>window.seekComposition(t)',t)
   out=page.evaluate('''()=>{const active=[...document.querySelectorAll('.film-scene')].filter(x=>parseFloat(getComputedStyle(x).opacity)>.05);return active.map(x=>{const r=x.querySelector('.nex-scene-rig').getBoundingClientRect();return{l:r.left,t:r.top,r:r.right,b:r.bottom}})}''')
   if not out:errors.append(name+' no active scene at '+str(t))
   for r in out:
    if r['l']<-4 or r['t']<-4 or r['r']>size[0]+4 or r['b']>size[1]+4:errors.append(name+' offcanvas at '+str(t))
  page.close()
 b.close()
report={'status':'PASS' if not errors else 'FAIL','responsiveSamples':samples,'filmAspectRatios':['1920x1080','1080x1080','1080x1920'],'errors':errors};(root/'reports/batch13-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
