from pathlib import Path
from playwright.sync_api import sync_playwright
from batch3_browser_utils import bundled_motion_explorer
import json
root=Path(__file__).resolve().parents[1];html=bundled_motion_explorer(root);page_errors=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1920,'height':1080});page.on('pageerror',lambda e:page_errors.append(str(e)));page.on('console',lambda m:page_errors.append('console: '+m.text) if m.type=='error' else None);page.set_content(html,wait_until='load')
 counts={'all':page.locator('.motion-card').count()}
 for subtype in ['entrance','action','ambient','transition']:
  page.locator(f'[data-filter="{subtype}"]').click();counts[subtype]=page.locator('.motion-card').count()
 page.locator('[data-filter="all"]').click()
 result=page.evaluate('''()=>{function snap(el){return JSON.stringify([el,...el.querySelectorAll('*')].slice(0,90).map(n=>{const c=getComputedStyle(n);return [n.tagName,n.className,c.transform,c.opacity,c.clipPath,c.strokeDashoffset,c.backgroundColor,n.textContent]}))}return [...document.querySelectorAll('.motion-card')].map(card=>{const demos=[...card.querySelectorAll('.motion-target-cell')].map(cell=>{const el=[...cell.children].find(x=>x.__tl);const tl=el&&el.__tl;if(!tl)return {ok:false,reason:'timeline missing'};const states=[0,.23,.47,.71,1].map(p=>{tl.seek(tl.duration()*p);return snap(el)});return {ok:new Set(states).size>=2,duration:tl.duration(),states:new Set(states).size}});return {id:card.dataset.motionId,demos}})}''')
 # controls and parameterisation
 page.select_option('#motionStyle','technical-notebook');style=page.evaluate("document.documentElement.dataset.paperStyle")
 page.select_option('#motionPalette','cobalt');palette=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary').trim()")
 page.select_option('#motionRatio','portrait');ratio_count=page.locator('.motion-target-cell[data-ratio="portrait"]').count()
 duration_test=page.evaluate('''()=>{const el=document.createElement('div');el.style.width='100px';el.style.height='100px';document.body.appendChild(el);const a=NexMotion.apply(el,'cut-paper-pop',{duration:.6,energy:'medium'}).duration();const b=NexMotion.apply(el,'cut-paper-pop',{duration:1.4,energy:'medium'}).duration();return {short:a,long:b}}''')
 b.close()
failures=[{'id':r['id'],'demo':i,'data':d} for r in result for i,d in enumerate(r['demos']) if not d['ok']]
status=(not page_errors and counts=={'all':32,'entrance':10,'action':10,'ambient':5,'transition':7} and not failures and style=='technical-notebook' and palette.lower()=='#1456d8' and ratio_count==96 and duration_test['long']>duration_test['short'])
report={'status':'PASS' if status else 'FAIL','pageErrors':page_errors,'filterCounts':counts,'motionCardsTested':len(result),'targetDemosTested':sum(len(x['demos']) for x in result),'failures':failures,'styleSwitch':style,'palettePrimary':palette,'portraitTargetCount':ratio_count,'durationParameterTest':duration_test}
(root/'reports/batch3-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(0 if status else 1)
