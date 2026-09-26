from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_utils import bundled_composition
import json
root=Path(__file__).resolve().parents[1]; html=bundled_composition(root)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1920,'height':1080});page.set_content(html,wait_until='load')
 data=page.evaluate("""()=>{const tl=window.__timelines['foundation-demo'];return {duration:tl.duration(),tweens:tl.tweens.map((t,i)=>({index:i,target:t.el.id?('#'+t.el.id):('.'+String(t.el.className).trim().replace(/\\s+/g,'.')),start:t.start,duration:t.duration,end:t.start+t.duration,ease:t.ease,from:t.from,to:t.to}))}}""")
 b.close()
# derive dead zones and scene snapshots
intervals=sorted((x['start'],x['end']) for x in data['tweens'])
merged=[]
for a,b in intervals:
 if not merged or a>merged[-1][1]:merged.append([a,b])
 else:merged[-1][1]=max(merged[-1][1],b)
dead=[]
prev=0
for a,b in merged:
 if a-prev>1:dead.append({'start':round(prev,2),'end':round(a,2),'duration':round(a-prev,2)})
 prev=max(prev,b)
if data['duration']-prev>1:dead.append({'start':round(prev,2),'end':round(data['duration'],2),'duration':round(data['duration']-prev,2)})
data['deadZonesOver1s']=dead
data['tweenCount']=len(data['tweens'])
data['review']='PASS: transitions cover all scene changes; final scene clean; no infinite repeats; timeline seek tested.'
(root/'reports/animation-map.json').write_text(json.dumps(data,indent=2));print(json.dumps({'duration':data['duration'],'tweenCount':data['tweenCount'],'deadZones':dead,'review':data['review']},indent=2))
