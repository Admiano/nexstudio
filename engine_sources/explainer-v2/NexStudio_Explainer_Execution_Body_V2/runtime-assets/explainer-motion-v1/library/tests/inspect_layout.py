from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_utils import bundled_composition
import json
root=Path(__file__).resolve().parents[1]
html=bundled_composition(root)
results=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 for ratio,viewport in [('landscape',{'width':1920,'height':1080}),('square',{'width':1080,'height':1080}),('portrait',{'width':1080,'height':1920})]:
  page=b.new_page(viewport=viewport)
  page.set_content(html,wait_until='load')
  page.evaluate('(ratio)=>document.querySelector("[data-composition-id]").dataset.ratio=ratio',ratio)
  for t in [0.5,3.2,5.9,8.6,11.3,14.4]:
   page.evaluate('(t)=>window.seekComposition(t)',t)
   issues=page.evaluate("()=>{const root=document.querySelector('[data-composition-id]');const rb=root.getBoundingClientRect();return [...document.querySelectorAll('.scene-header,.paper-component,.final-mark,.final-sub')].filter(e=>getComputedStyle(e).opacity>0.02).map(e=>{const r=e.getBoundingClientRect();return {el:e.className,left:r.left,top:r.top,right:r.right,bottom:r.bottom}}).filter(r=>r.left<rb.left-2||r.top<rb.top-2||r.right>rb.right+2||r.bottom>rb.bottom+2)}")
   results.append({'ratio':ratio,'time':t,'issues':issues})
  page.close()
 b.close()
report={'status':'PASS' if not any(x['issues'] for x in results) else 'FAIL','samples':results}
(root/'reports/layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
