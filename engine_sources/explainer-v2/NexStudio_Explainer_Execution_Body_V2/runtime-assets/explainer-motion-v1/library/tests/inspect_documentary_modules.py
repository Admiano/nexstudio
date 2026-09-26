from pathlib import Path
from playwright.sync_api import sync_playwright
from batch12_browser_utils import harness,bundle_scene,bundle_explorer
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={'components':[],'palettes':{},'scenes':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 pg=b.new_page(viewport={'width':1000,'height':820});pg.set_content(harness(root),wait_until='load')
 for pal in ['warm','cobalt','charcoal']:
  pg.evaluate('(p)=>NexTheme.applyPalette(p)',pal);bad=[]
  for idx in range(32):
   r=pg.evaluate('''({idx,pal})=>{const def=NexDocumentaryModules.registry[idx],make=(seed,n)=>((seed+' ').repeat(Math.ceil(n/(seed.length+1)))).slice(0,n),title=make('DOCUMENTARY HEADING 1986—2026',def.slots.title.maxCharacters),caption=make('Evidence, punctuation, 128,400, and deliberatelylongunbrokenword remain safely contained.',def.slots.caption.maxCharacters),cfg={...def.sampleConfig,title,caption,source:'Primary archive source · Box 128 · Folder 04 · Verified 2026',mood:['warm','serious','investigative','celebratory'][idx%4],style:['clean-editorial','handmade-scrapbook','technical-notebook','bold-paper-collage'][idx%4]};const el=NexDocumentaryModules.create(def,cfg);stage.replaceChildren(el);NexDocumentaryModules.fitText(el);NexDocumentaryModules.layoutConnectors(el);const shell=el.querySelector('.dm-content').getBoundingClientRect(),texts=[...el.querySelectorAll('h1,h2,h3,p,blockquote,span,strong,small,b,.dm-source')].filter(x=>x.offsetParent!==null),overflow=texts.filter(x=>x.scrollWidth>x.clientWidth+3||x.scrollHeight>x.clientHeight+3).map(x=>({tag:x.tagName,cls:x.className,text:x.textContent.slice(0,35),sw:x.scrollWidth,cw:x.clientWidth,sh:x.scrollHeight,ch:x.clientHeight})),outer=[...el.querySelectorAll('.dm-content>*')].filter(x=>{const r=x.getBoundingClientRect();return r.left<shell.left-10||r.right>shell.right+10||r.top<shell.top-10||r.bottom>shell.bottom+10}).map(x=>x.className||x.tagName);return{id:def.id,overflow,outer}}''',{'idx':idx,'pal':pal})
   report['components'].append({'palette':pal,**r})
   if r['overflow'] or r['outer']:bad.append({'id':r['id'],'overflow':r['overflow'],'outer':r['outer']})
  report['palettes'][pal]={'failureCount':len(bad),'failures':bad}
  if bad:errors.append(pal+' component overflow '+','.join(x['id'] for x in bad[:6]))
 pg.close()
 for name,w,h in [('company-history',1920,1080),('investigative-example',1080,1080),('personal-memory',1080,1920)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_scene(root,name),wait_until='load');samples=[]
  for t in [0,.5,3.8,7.3,10.8,14.3,17.8,21.3,24.8,28.5,30]:
   pg.evaluate('(t)=>seekComposition(t)',t)
   r=pg.evaluate('''()=>{const W=innerWidth,H=innerHeight;const bad=[...document.querySelectorAll('.dms-title,.dms-card,.dms-footer')].filter(x=>{if(x.classList.contains('dms-card')&&parseFloat(getComputedStyle(x).opacity)<=.05)return false;const r=x.getBoundingClientRect();return r.left<-6||r.top<-6||r.right>W+6||r.bottom>H+6}).map(x=>x.className);const visible=[...document.querySelectorAll('.dms-card')].filter(x=>parseFloat(getComputedStyle(x).opacity)>.05).length;const textOverflow=[...document.querySelectorAll('.dms-card [data-fit]')].filter(x=>x.scrollWidth>x.clientWidth+3||x.scrollHeight>x.clientHeight+3).map(x=>x.textContent.slice(0,30));return{bad,visible,textOverflow}}''')
   samples.append({'time':t,**r})
  report['scenes'][name]={'width':w,'height':h,'samples':samples}
  if any(x['bad'] or x['textOverflow'] for x in samples):errors.append(name+' layout failure')
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors;(root/'reports/batch12-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'palettes':{k:v['failureCount'] for k,v in report['palettes'].items()},'scenes':{k:{'samples':len(v['samples']),'offCanvas':sum(bool(x['bad']) for x in v['samples']),'textOverflow':sum(bool(x['textOverflow']) for x in v['samples'])} for k,v in report['scenes'].items()},'errors':errors},indent=2));sys.exit(1 if errors else 0)
