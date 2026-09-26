from pathlib import Path
from playwright.sync_api import sync_playwright
from batch12_browser_utils import harness,bundle_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={'components':{},'scenes':{}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 pg=b.new_page(viewport={'width':1100,'height':850});pg.set_content(harness(root),wait_until='load')
 data=pg.evaluate('''()=>NexDocumentaryModules.registry.map(def=>{const e=NexDocumentaryModules.create(def);stage.replaceChildren(e);const tl=NexDocumentaryModules.animate(e,{duration:2.4,energy:'medium'});const semantic={connectors:e.querySelectorAll('.dm-connectors path,.dm-route').length,redactions:e.querySelectorAll('.dm-redact').length,highlights:e.querySelectorAll('mark').length,waveBars:e.querySelectorAll('.dm-wave i').length,counter:e.querySelectorAll('[data-count]').length};return{id:def.id,tweens:tl.base.tweens.length,duration:tl.duration(),semantic}})''')
 report['components']={'count':len(data),'totalTweens':sum(x['tweens'] for x in data),'minimumTweens':min(x['tweens'] for x in data),'maximumTweens':max(x['tweens'] for x in data),'items':data}
 if len(data)!=32 or min(x['tweens'] for x in data)<2:errors.append('Component animation coverage insufficient')
 pg.close()
 for name,w,h in [('company-history',1920,1080),('investigative-example',1080,1080),('personal-memory',1080,1920)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_scene(root,name),wait_until='load')
  m=pg.evaluate('''(name)=>{
    const master=window.__timelines[name];
    const cards=[...document.querySelectorAll('.nex-documentary-module')];
    const intervals=master.base.tweens.map(t=>[t.start,t.start+t.duration*(1+t.repeat)]);
    cards.forEach((e,i)=>{
      const offset=.2+i*3.45;
      const tweens=(e.__tl&&e.__tl.base&&e.__tl.base.tweens)||[];
      tweens.forEach(t=>intervals.push([offset+t.start,offset+t.start+t.duration*(1+t.repeat)]));
    });
    const uncovered=[];
    for(let t=0;t<30;t+=.25){if(!intervals.some(([a,z])=>t>=a&&t<=z))uncovered.push(Number(t.toFixed(2)))}
    let longest=0,current=0;
    for(let t=0;t<30;t+=.25){if(uncovered.includes(Number(t.toFixed(2)))){current+=.25;longest=Math.max(longest,current)}else current=0}
    const moduleTweens=cards.reduce((n,e)=>n+(((e.__tl&&e.__tl.base&&e.__tl.base.tweens)||[]).length),0);
    return{masterTweens:master.base.tweens.length,moduleTweens,totalTweens:master.base.tweens.length+moduleTweens,longestDeadZone:longest,uncoveredSamples:uncovered.slice(0,20)};
  }''',name)
  report['scenes'][name]=m
  if m['longestDeadZone']>1:errors.append(name+' dead zone exceeds one second')
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors;(root/'reports/batch12-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'componentTweens':report['components']['totalTweens'],'scenes':report['scenes'],'errors':errors},indent=2));sys.exit(1 if errors else 0)
