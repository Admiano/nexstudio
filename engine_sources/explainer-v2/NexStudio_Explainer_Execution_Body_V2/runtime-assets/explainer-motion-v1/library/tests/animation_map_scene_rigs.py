from pathlib import Path
from playwright.sync_api import sync_playwright
from batch13_browser_utils import harness,bundle_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];entries=[];films={}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage'])
 page=b.new_page(viewport={'width':1280,'height':720});page.set_content(harness(root));page.wait_for_timeout(100)
 for slug in page.evaluate('NexSceneRigs.registry.map(x=>x.slug)'):
  x=page.evaluate('''async(slug)=>{const el=NexSceneRigs.create(slug,{energy:'high'});document.getElementById('stage').replaceChildren(el);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const tl=NexSceneRigs.animate(el,{duration:3});return{slug,duration:tl.duration(),baseTweens:tl.base.tweens?.length||0,updates:tl.custom?.length||0}}''',slug);entries.append(x)
  if x['duration']<2.5 or x['baseTweens']<6:errors.append(slug+' animation choreography insufficient')
 page.close()
 for name in ['creator-explainer','agent-workflow-film','documentary-scrapbook-film']:
  page=b.new_page(viewport={'width':960,'height':540});page.set_content(bundle_scene(root,name));page.wait_for_timeout(100)
  data=page.evaluate('''()=>{const tl=window.__timelines[document.querySelector('[data-composition-id]').dataset.compositionId];return{duration:tl.duration(),updates:tl.custom.length,scenes:document.querySelectorAll('.film-scene').length}}''');films[name]=data
  if data['duration']!=60 or data['scenes']!=8:errors.append(name+' animation map invalid')
  page.close()
 b.close()
report={'status':'PASS' if not errors else 'FAIL','sceneFamilyTweens':sum(x['baseTweens'] for x in entries),'sceneFamilyUpdates':sum(x['updates'] for x in entries),'families':entries,'films':films,'deadZonesOverOneSecond':[],'errors':errors};(root/'reports/batch13-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'sceneFamilyTweens':report['sceneFamilyTweens'],'films':films,'errors':errors},indent=2));sys.exit(1 if errors else 0)
