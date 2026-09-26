from pathlib import Path
from playwright.sync_api import sync_playwright
from batch2_browser_utils import bundled_object_composition
import json
root=Path(__file__).resolve().parents[1];html=bundled_object_composition(root);samples=[];page_errors=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 for ratio,viewport in [('landscape',{'width':1920,'height':1080}),('square',{'width':1080,'height':1080}),('portrait',{'width':1080,'height':1920})]:
  page=b.new_page(viewport=viewport);page.on('pageerror',lambda e:page_errors.append(str(e)));page.set_content(html,wait_until='load');page.evaluate('(r)=>document.querySelector("[data-composition-id]").dataset.ratio=r',ratio)
  for t in [0.7,2.4,4.7,6.7,9.0,11.1,13.3,15.2,17.4,19.1]:
   page.evaluate('(t)=>window.seekComposition(t)',t);page.wait_for_timeout(30)
   state=page.evaluate('''()=>{const root=document.querySelector('[data-composition-id]'),rb=root.getBoundingClientRect();const visible=[...document.querySelectorAll('.scene-copy,.scene-board>.paper-object,.final-object-title,.final-object-sub')].filter(e=>getComputedStyle(e).opacity>.03);const issues=visible.map(e=>{const r=e.getBoundingClientRect();return {id:e.dataset.componentId||e.className,left:r.left,top:r.top,right:r.right,bottom:r.bottom}}).filter(r=>r.left<rb.left-3||r.top<rb.top-3||r.right>rb.right+3||r.bottom>rb.bottom+3);return {visible:visible.length,issues}}''')
   samples.append({'ratio':ratio,'time':t,**state})
  page.screenshot(path=str(root/f'reports/object-demo-{ratio}.png'))
  page.close()
 b.close()
status=not page_errors and not any(s['issues'] for s in samples)
report={'status':'PASS' if status else 'FAIL','pageErrors':page_errors,'samples':samples}
(root/'reports/batch2-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'pageErrors':page_errors,'issueSamples':[s for s in samples if s['issues']]},indent=2));raise SystemExit(0 if status else 1)
