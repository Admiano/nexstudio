from pathlib import Path
from playwright.sync_api import sync_playwright
from batch11_browser_utils import harness,bundle_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={'components':[],'scenes':{},'palettes':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 pg=b.new_page(viewport={'width':900,'height':700});pg.set_content(harness(root),wait_until='load')
 for pal in ['warm','cobalt','charcoal']:
  pg.evaluate('(p)=>NexTheme.applyPalette(p)',pal);bad=[]
  for idx in range(28):
   r=pg.evaluate('''({idx,pal})=>{const def=NexCreatorModules.registry[idx],el=NexCreatorModules.create(def,{contentLength:'long',style:idx%4===0?'clean-editorial':idx%4===1?'handmade-scrapbook':idx%4===2?'technical-notebook':'bold-paper-collage',caption:'This longer creator-facing description demonstrates safe wrapping, punctuation, numbers such as 128,400, and a deliberatelylongunbrokenwordthatmustremaincontainedinsideitsassignedpapercomponent.'});stage.replaceChildren(el);NexCreatorModules.fitText(el);const shell=el.querySelector('.cm-shell').getBoundingClientRect();const texts=[...el.querySelectorAll('h2,h3,p,span,strong,small,b,button')].filter(x=>x.offsetParent!==null);const overflow=texts.filter(x=>!x.classList.contains('cm-big-count')&&(x.scrollWidth>x.clientWidth+3||x.scrollHeight>x.clientHeight+3)).map(x=>({tag:x.tagName,text:x.textContent.slice(0,40),sw:x.scrollWidth,cw:x.clientWidth,sh:x.scrollHeight,ch:x.clientHeight}));const outer=[...el.querySelectorAll('.cm-content>*')].filter(x=>{const r=x.getBoundingClientRect();return r.left<shell.left-4||r.right>shell.right+4||r.top<shell.top-4||r.bottom>shell.bottom+4}).map(x=>x.className||x.tagName);return{id:def.id,overflow,outer,contentLength:el.dataset.contentLength,style:el.dataset.style}}''',{'idx':idx,'pal':pal})
   report['components'].append({'palette':pal,**r})
   if r['overflow'] or r['outer']:bad.append(r['id'])
  report['palettes'][pal]={'failures':bad}
  if bad:errors.append(pal+' overflow: '+','.join(bad[:8]))
 pg.close()
 for name,w,h in [('creator-growth-recap',1920,1080),('sponsorship-announcement',1080,1080),('publishing-workflow',1080,1920)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_scene(root,name),wait_until='load');samples=[]
  for t in [0,.4,1.5,3.2,5.8,8.2,10.5,12]:
   pg.evaluate('(t)=>seekComposition(t)',t)
   r=pg.evaluate('''()=>{const W=innerWidth,H=innerHeight;const bad=[...document.querySelectorAll('.cms-title,.cms-card,.cms-footer')].filter(x=>{if(x.classList.contains('cms-card')&&parseFloat(getComputedStyle(x).opacity)<=.05)return false;const r=x.getBoundingClientRect();return r.left<-4||r.top<-4||r.right>W+4||r.bottom>H+4}).map(x=>x.className);const visible=[...document.querySelectorAll('.cms-card')].filter(x=>parseFloat(getComputedStyle(x).opacity)>.05).length;return{bad,visible}}''')
   samples.append({'time':t,**r})
  report['scenes'][name]={'width':w,'height':h,'samples':samples}
  if any(x['bad'] for x in samples):errors.append(name+' off canvas')
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors;(root/'reports/batch11-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'paletteFailures':report['palettes'],'scenes':{k:{'samples':len(v['samples']),'offCanvas':sum(bool(x['bad']) for x in v['samples'])} for k,v in report['scenes'].items()},'errors':errors},indent=2));sys.exit(1 if errors else 0)
