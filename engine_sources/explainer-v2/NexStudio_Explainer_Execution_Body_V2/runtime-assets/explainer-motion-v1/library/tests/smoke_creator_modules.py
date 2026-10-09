from pathlib import Path
from playwright.sync_api import sync_playwright
from batch11_browser_utils import harness,bundle_explorer,bundle_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={'components':{},'explorer':{},'scenes':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 # component API
 pg=b.new_page(viewport={'width':1200,'height':900});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
 pg.set_content(harness(root),wait_until='load')
 data=pg.evaluate('''()=>NexCreatorModules.registry.map(def=>{const states={};for(const length of ['short','medium','long']){const e=NexCreatorModules.create(def,{contentLength:length,logoSrc:'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="70"><rect width="100" height="70" fill="gold"/><text x="50" y="44" text-anchor="middle">OK</text></svg>'});stage.append(e);const tl=NexCreatorModules.animate(e,{duration:1.8,energy:'high'});const samples=[0,.3,.8,1.5,2.5].map(t=>{tl.seek(t);const s=getComputedStyle(e.querySelector('.cm-shell'));return s.transform+'|'+s.opacity});states[length]={distinct:new Set(samples).size,text:e.innerText.length,icons:e.querySelectorAll('.nex-creator-icon').length,logo:e.querySelectorAll('.cm-logo').length};e.remove()}return{id:def.id,states}})''')
 for x in data:
  if any(v['distinct']<3 for v in x['states'].values()):errors.append(x['id']+' animation lacks states')
  if any(v['text']<1 for v in x['states'].values()):errors.append(x['id']+' missing content')
 report['components']={'count':len(data),'browserErrors':errs,'allStates':True,'semanticLowerLevelIcons':sum(max(v['icons'] for v in x['states'].values()) for x in data)}
 if len(data)!=28:errors.append('Component count mismatch')
 if errs:errors.extend(errs)
 pg.close()
 # explorer
 pg=b.new_page(viewport={'width':1600,'height':1000});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None);pg.set_content(bundle_explorer(root),wait_until='load');pg.wait_for_timeout(400)
 cards=pg.locator('.cm-card').count();pg.fill('#search','sponsorship');visible=pg.locator('.cm-card:not([hidden])').count();pg.select_option('#style','technical-notebook');pg.select_option('#palette','cobalt');pg.select_option('#energy','high');pg.select_option('#length','long');pg.wait_for_timeout(300);count=pg.locator('#count').inner_text();
 report['explorer']={'cards':cards,'sponsorshipResults':visible,'counter':count,'browserErrors':errs}
 if cards!=28 or visible<1:errors.append('Explorer filtering failed')
 if errs:errors.extend(errs)
 pg.close()
 # scenes
 for name,w,h in [('creator-growth-recap',1920,1080),('sponsorship-announcement',1080,1080),('publishing-workflow',1080,1920)]:
  pg=b.new_page(viewport={'width':w,'height':h});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None);pg.set_content(bundle_scene(root,name),wait_until='load');mods=pg.locator('.nex-creator-module').count();states=[]
  for t in [0,.5,2,4,6,8,10,12]:pg.evaluate('(t)=>seekComposition(t)',t);states.append(pg.evaluate('''()=>[...document.querySelectorAll('.cms-card')].map(x=>getComputedStyle(x).transform+'|'+getComputedStyle(x).opacity).join(';')'''))
  report['scenes'][name]={'modules':mods,'distinctStates':len(set(states)),'browserErrors':errs}
  if mods<2 or len(set(states))<4:errors.append(name+' scene not sufficiently animated')
  if errs:errors.extend(errs)
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors;(root/'reports/batch11-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
