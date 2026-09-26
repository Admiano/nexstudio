from pathlib import Path
from playwright.sync_api import sync_playwright
from batch2_browser_utils import bundled_object_composition
import json
root=Path(__file__).resolve().parents[1];html=bundled_object_composition(root)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1920,'height':1080});page.set_content(html,wait_until='load')
 data=page.evaluate('''()=>{const tl=window.__timelines['paper-objects-demo'];const tweens=tl.tweens.map((t,i)=>({index:i,start:+t.start.toFixed(3),end:+(t.start+t.duration).toFixed(3),duration:+t.duration.toFixed(3),target:t.el.dataset.componentId||t.el.id||t.el.className,ease:t.ease,properties:Object.keys(t.to).filter(k=>!['duration','ease','stagger'].includes(k))})).sort((a,b)=>a.start-b.start);let cursor=0,dead=[];for(const t of tweens){if(t.start-cursor>1)dead.push({from:+cursor.toFixed(2),to:+t.start.toFixed(2),duration:+(t.start-cursor).toFixed(2)});cursor=Math.max(cursor,t.end)}return {duration:tl.duration(),tweenCount:tweens.length,deadZones:dead,tweens}}''')
 b.close()
data['status']='PASS' if data['tweenCount']>=60 and not data['deadZones'] else 'FAIL';(root/'reports/batch2-animation-map.json').write_text(json.dumps(data,indent=2));print(json.dumps({k:v for k,v in data.items() if k!='tweens'},indent=2));raise SystemExit(0 if data['status']=='PASS' else 1)
