from pathlib import Path
from playwright.sync_api import sync_playwright
from batch12_browser_utils import harness,bundle_explorer,bundle_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={'components':{},'features':{},'explorer':{},'scenes':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 pg=b.new_page(viewport={'width':1100,'height':850});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None);pg.set_content(harness(root),wait_until='load')
 data=pg.evaluate('''()=>NexDocumentaryModules.registry.map(def=>{const e=NexDocumentaryModules.create(def,{mood:['warm','serious','investigative','celebratory'][def.order%4]});stage.replaceChildren(e);const tl=NexDocumentaryModules.animate(e,{duration:2.2,energy:'high'});const states=[0,.25,.7,1.35,2.2,3.4].map(t=>{tl.seek(t);const s=getComputedStyle(e.querySelector('.dm-shell'));return s.transform+'|'+s.opacity+'|'+[...e.querySelectorAll('.dm-connectors path,.dm-route,.dm-redact,mark')].map(x=>getComputedStyle(x).strokeDashoffset+'|'+getComputedStyle(x).opacity+'|'+getComputedStyle(x).backgroundSize).join(';')});return{id:def.id,distinct:new Set(states).size,text:e.innerText.length,media:e.querySelectorAll('img').length,source:e.querySelectorAll('.dm-source').length,mood:e.dataset.mood}})''')
 if len(data)!=32:errors.append('Component count mismatch')
 for x in data:
  if x['distinct']<3:errors.append(x['id']+' insufficient animation states')
  if x['text']<1:errors.append(x['id']+' missing visible content')
 report['components']={'count':len(data),'browserErrors':errs,'minimumDistinct':min(x['distinct'] for x in data),'moods':sorted(set(x['mood'] for x in data))}
 if errs:errors.extend(errs)
 # semantic features
 feat=pg.evaluate('''()=>{const red=NexDocumentaryModules.create('module.documentary.redacted-document.paper-01',{redactions:true});stage.replaceChildren(red);const a=NexDocumentaryModules.animate(red);a.seek(1.4);const shown=[...red.querySelectorAll('.dm-redact')].every(x=>parseFloat(getComputedStyle(x).opacity)>.5);const no=NexDocumentaryModules.setRedactions(red,false);stage.replaceChildren(no);const b=NexDocumentaryModules.animate(no);b.seek(1.4);const hidden=[...no.querySelectorAll('.dm-redact')].every(x=>parseFloat(getComputedStyle(x).opacity)<.2);const hi=NexDocumentaryModules.create('module.documentary.highlighted-passage.paper-01');stage.replaceChildren(hi);const c=NexDocumentaryModules.animate(hi);c.seek(1.5);const mark=hi.querySelector('mark');const board=NexDocumentaryModules.create('module.documentary.investigation-board.paper-01');stage.replaceChildren(board);NexDocumentaryModules.layoutConnectors(board);const paths=[...board.querySelectorAll('.dm-connectors path')];const map=NexDocumentaryModules.create('module.documentary.map-journey.paper-01',{routeLabels:['A','B','C']});stage.replaceChildren(map);return{shown,hidden,highlight:!!mark,connectorCount:paths.length,connectorBound:paths.every(x=>x.getAttribute('d')&&x.getAttribute('d').startsWith('M')),routeLabels:map.querySelectorAll('.dm-map span').length,api:['setMedia','setRoute','setRedactions','layoutConnectors'].every(k=>typeof NexDocumentaryModules[k]==='function')}}''')
 report['features']=feat
 if not all([feat['shown'],feat['hidden'],feat['highlight'],feat['connectorBound'],feat['api']]) or feat['routeLabels']!=3:errors.append('Semantic feature audit failed')
 pg.close()
 pg=b.new_page(viewport={'width':1600,'height':1000});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None);pg.set_content(bundle_explorer(root),wait_until='load');pg.wait_for_timeout(500);cards=pg.locator('.documentary-card').count();pg.fill('#search','redacted');pg.wait_for_timeout(200);visible=pg.locator('.documentary-card').count();pg.fill('#search','');pg.click('[data-filter="citation"]');pg.wait_for_timeout(200);filtered=pg.locator('.documentary-card').count();pg.select_option('#mood','investigative');pg.select_option('#palette','charcoal');pg.select_option('#energy','high');pg.wait_for_timeout(250);report['explorer']={'cards':cards,'redactedResults':visible,'citationResults':filtered,'browserErrors':errs}
 if cards!=32 or visible<1 or filtered<3:errors.append('Explorer filtering failed')
 if errs:errors.extend(errs)
 pg.close()
 for name,w,h in [('company-history',1920,1080),('investigative-example',1080,1080),('personal-memory',1080,1920)]:
  pg=b.new_page(viewport={'width':w,'height':h});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None);pg.set_content(bundle_scene(root,name),wait_until='load');mods=pg.locator('.nex-documentary-module').count();states=[];visible=[]
  for t in [0,.5,3.8,7.3,10.8,14.3,17.8,21.3,24.8,28.5,30]:
   pg.evaluate('(t)=>seekComposition(t)',t);states.append(pg.evaluate('''()=>[...document.querySelectorAll('.dms-card')].map(x=>getComputedStyle(x).transform+'|'+getComputedStyle(x).opacity).join(';')'''));visible.append(pg.evaluate('''()=>[...document.querySelectorAll('.dms-card')].filter(x=>parseFloat(getComputedStyle(x).opacity)>.05).length'''))
  report['scenes'][name]={'modules':mods,'distinctStates':len(set(states)),'visibleProgression':visible,'browserErrors':errs}
  if mods!=8 or len(set(states))<7 or max(visible)<7:errors.append(name+' composition failed')
  if errs:errors.extend(errs)
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors;(root/'reports/batch12-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
