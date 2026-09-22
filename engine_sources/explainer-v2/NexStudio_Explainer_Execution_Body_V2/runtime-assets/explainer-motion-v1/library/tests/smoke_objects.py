from pathlib import Path
from playwright.sync_api import sync_playwright
from batch2_browser_utils import bundled_object_explorer
import json
root=Path(__file__).resolve().parents[1];html=bundled_object_explorer(root);errors=[];console=[];results={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    page=b.new_page(viewport={'width':1600,'height':1000})
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:console.append(m.text) if m.type=='error' else None)
    page.set_content(html,wait_until='load');page.wait_for_timeout(300)
    results['initialCards']=page.locator('.card').count();results['components']=page.locator('.paper-object').count()
    results['manifestButtons']=page.locator('.inspect').count()
    page.fill('#searchInput','envelope');page.wait_for_timeout(100);results['envelopeSearch']=page.locator('.card').count()
    page.fill('#searchInput','');page.select_option('#styleSelect','technical-notebook');page.select_option('#paletteSelect','cobalt');page.select_option('#energySelect','high');page.select_option('#ratioSelect','portrait');page.fill('#sampleTitle','DYNAMIC TITLE THAT FITS');page.fill('#sampleBody','This longer editable body is replaced live without opening the component source code.');page.wait_for_timeout(250)
    results['style']=page.locator('html').get_attribute('data-paper-style');results['portraitFrames']=page.locator('.object-preview-frame[data-ratio="portrait"]').count()
    page.click('.replay');page.wait_for_timeout(150)
    page.click('.inspect');results['manifestOpen']='open' in (page.locator('#manifestPanel').get_attribute('class') or '')
    # direct API and attachments
    api=page.evaluate('''()=>{const host=document.createElement('div');document.body.appendChild(host);const base=NexPaperObjects.create('object.rectangular-card.paper-01',{title:'HOST'});host.appendChild(base);const a=NexPaperObjects.attachTo(base,'object.masking-tape.paper-01',{left:30,top:-10});return {registry:NexPaperObjects.registry.length,attached:a.classList.contains('attached-object'),text:base.textContent.includes('HOST')}}''')
    results['api']=api
    # all renderers created and have visible geometry
    results['allGeometry']=page.evaluate('''()=>NexPaperObjects.registry.every(d=>{const e=NexPaperObjects.create(d,{title:'TEST',body:'Reusable object'});document.body.appendChild(e);const r=e.getBoundingClientRect();const ok=r.width>100&&r.height>80;e.remove();return ok})''')
    page.screenshot(path=str(root/'reports/object-explorer.png'),full_page=False)
    b.close()
status=(results.get('initialCards')==40 and results.get('components')==40 and results.get('envelopeSearch',0)>=2 and results.get('style')=='technical-notebook' and results.get('manifestOpen') and results.get('api',{}).get('attached') and results.get('allGeometry') and not errors and not console)
report={'status':'PASS' if status else 'FAIL','results':results,'pageErrors':errors,'consoleErrors':console}
(root/'reports/batch2-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(0 if status else 1)
