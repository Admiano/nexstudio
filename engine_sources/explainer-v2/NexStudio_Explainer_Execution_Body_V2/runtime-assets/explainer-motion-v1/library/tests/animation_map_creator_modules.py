from pathlib import Path
from playwright.sync_api import sync_playwright
from batch11_browser_utils import harness,bundle_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={'components':[],'scenes':{},'componentTweenCount':0}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 pg=b.new_page(viewport={'width':1000,'height':700});pg.set_content(harness(root),wait_until='load')
 data=pg.evaluate('''()=>NexCreatorModules.registry.map(def=>{const e=NexCreatorModules.create(def);stage.append(e);const tl=NexCreatorModules.animate(e,{duration:1.8,energy:'high'});const states=[0,.15,.4,.75,1.2,1.8,2.5].map(t=>{tl.seek(t);const shell=getComputedStyle(e.querySelector('.cm-shell'));return shell.transform+'|'+shell.opacity+'|'+[...e.querySelectorAll('[data-count],.cm-poll i,.cm-checklist li')].map(x=>getComputedStyle(x).transform+'|'+x.textContent).join(',')});const out={id:def.id,duration:tl.duration(),distinct:new Set(states).size,tweens:tl.items?tl.items.length:states.length};e.remove();return out})''')
 report['components']=data;report['componentTweenCount']=sum(x['tweens'] for x in data)
 if any(x['distinct']<3 or x['duration']<=0 for x in data):errors.append('Component animation lacks distinct states')
 pg.close()
 for name,w,h in [('creator-growth-recap',1920,1080),('sponsorship-announcement',1080,1080),('publishing-workflow',1080,1920)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_scene(root,name),wait_until='load');states=[]
  for t in [0,.5,1,2,3,4,5,6,7,8,9,10,11,12]:
   pg.evaluate('(t)=>seekComposition(t)',t);states.append(pg.evaluate('''()=>JSON.stringify([...[...document.querySelectorAll('.cms-card')].map(x=>getComputedStyle(x).transform+'|'+getComputedStyle(x).opacity),...[...document.querySelectorAll('[data-count]')].map(x=>x.textContent)])'''))
  dead=[[i-1,i] for i in range(1,len(states)) if states[i]==states[i-1]]
  report['scenes'][name]={'samples':len(states),'distinct':len(set(states)),'deadIntervals':dead}
  if dead:errors.append(name+' sampled dead intervals '+str(dead))
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors;(root/'reports/batch11-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'componentTweenCount':report['componentTweenCount'],'scenes':report['scenes'],'errors':errors},indent=2));sys.exit(1 if errors else 0)
