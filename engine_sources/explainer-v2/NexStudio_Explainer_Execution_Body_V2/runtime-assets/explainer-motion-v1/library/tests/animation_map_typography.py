from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
from batch8_browser_utils import bundle
root=Path(__file__).resolve().parents[1];errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=browser.new_page(viewport={'width':1920,'height':1080});page.set_content(bundle(root,'compositions/kinetic-typography-demo.html'),wait_until='load')
 data=page.evaluate('''()=>{const tl=window.__timelines['kinetic-typography-demo'],samples=[];for(let t=.05;t<=20;t+=.25){tl.seek(t);const vis=[...document.querySelectorAll('.kinetic-scene')].filter(e=>Number(getComputedStyle(e).opacity)>.03).length;const animated=[...document.querySelectorAll('.nex-type,.type-word,.kinetic-transition')].filter(e=>{const s=getComputedStyle(e);return s.transform!=='none'||Number(s.opacity)<.999}).length;samples.push({t:Number(t.toFixed(2)),vis,animated})}return{duration:tl.duration(),samples,sceneCount:document.querySelectorAll('.kinetic-scene').length,transitionCount:document.querySelectorAll('.kinetic-transition').length}}''')
 browser.close()
if abs(data['duration']-20)>.01:errors.append(f"Timeline duration {data['duration']}")
if data['sceneCount']!=6:errors.append('Expected six kinetic scenes')
if any(x['vis']<1 for x in data['samples']):errors.append('Blank frame detected')
# Detect any >1s span with no transformed/faded elements.
run=0;maxrun=0
for x in data['samples']:
 run=run+1 if x['animated']==0 else 0;maxrun=max(maxrun,run)
if maxrun*.25>1:errors.append(f'Dead zone {maxrun*.25}s')
report={'status':'PASS' if not errors else 'FAIL','duration':data['duration'],'sceneCount':data['sceneCount'],'sampleCount':len(data['samples']),'maxDeadZoneSeconds':maxrun*.25,'samples':data['samples'],'errors':errors};(root/'reports/batch8-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2));sys.exit(1 if errors else 0)
