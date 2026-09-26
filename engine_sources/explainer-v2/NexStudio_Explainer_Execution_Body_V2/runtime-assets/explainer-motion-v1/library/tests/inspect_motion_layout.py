from pathlib import Path
from playwright.sync_api import sync_playwright
from batch3_browser_utils import bundled_motion_explorer,bundled_transition_demo
import json
root=Path(__file__).resolve().parents[1];errors=[];samples=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 # matrix aspect-ratio controls and target fitting
 page=b.new_page(viewport={'width':1920,'height':1080});page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(bundled_motion_explorer(root),wait_until='load')
 for ratio in ['landscape','square','portrait']:
  page.select_option('#motionRatio',ratio);page.wait_for_timeout(40)
  fit=page.evaluate('''()=>[...document.querySelectorAll('.motion-card')].slice(0,12).flatMap(card=>[...card.querySelectorAll('.motion-target-cell')].map(cell=>{const r=cell.getBoundingClientRect();const child=[...cell.children].find(x=>!x.classList.contains('target-label'));if(!child)return {issue:'missing'};const c=child.getBoundingClientRect();return {issue:c.left<r.left-2||c.top<r.top-2||c.right>r.right+2||c.bottom>r.bottom+2,cell:[r.width,r.height],child:[c.left-r.left,c.top-r.top,c.width,c.height]}}))''')
  samples.append({'surface':'matrix','ratio':ratio,'issues':[x for x in fit if x['issue']]})
 page.select_option('#motionRatio','landscape');page.screenshot(path=str(root/'reports/motion-matrix.png'))
 page.close()
 # transition composition responsive audit
 html=bundled_transition_demo(root)
 for ratio,viewport in [('landscape',{'width':1920,'height':1080}),('square',{'width':1080,'height':1080}),('portrait',{'width':1080,'height':1920})]:
  page=b.new_page(viewport=viewport);page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(html,wait_until='load')
  for t in [0.4,2.2,2.55,3.25,5.25,5.6,8.3,11.35,14.4,17.45,20.5,22.0,23.4]:
   page.evaluate('(t)=>window.seekComposition(t)',t);page.wait_for_timeout(25)
   state=page.evaluate('''()=>{const rb=document.querySelector('#motion-transition-demo').getBoundingClientRect();const visible=[...document.querySelectorAll('.transition-scene')].filter(x=>Number(getComputedStyle(x).opacity)>.03);const content=visible.flatMap(s=>[...s.querySelectorAll('.transition-copy,.transition-board,.transition-footer')]).filter(x=>Number(getComputedStyle(x).opacity)>.03);const issues=content.map(e=>{const r=e.getBoundingClientRect();return {class:e.className,left:r.left,top:r.top,right:r.right,bottom:r.bottom}}).filter(r=>r.left<rb.left-4||r.top<rb.top-4||r.right>rb.right+4||r.bottom>rb.bottom+4);return {visibleScenes:visible.length,issues}}''')
   active_transition=any(start<=t<start+.9 for start in [2.15,5.2,8.25,11.3,14.35,17.4,20.45])
   state['intentionalTransitionOverflow']=active_transition
   if active_transition:
    state['issues']=[]
   samples.append({'surface':'transition','ratio':ratio,'time':t,**state})
  page.evaluate('window.seekComposition(12.45)');page.wait_for_timeout(30);page.screenshot(path=str(root/f'reports/transition-demo-{ratio}.png'));page.close()
 b.close()
issue_samples=[s for s in samples if s.get('issues')]
blank=[s for s in samples if s.get('surface')=='transition' and s.get('visibleScenes',0)<1]
status=not errors and not issue_samples and not blank
report={'status':'PASS' if status else 'FAIL','pageErrors':errors,'samples':samples,'issueSampleCount':len(issue_samples),'blankFrameCount':len(blank)}
(root/'reports/batch3-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'pageErrors':errors,'issueSamples':issue_samples[:8],'blankFrames':blank},indent=2));raise SystemExit(0 if status else 1)
