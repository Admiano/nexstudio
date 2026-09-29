from pathlib import Path
from playwright.sync_api import sync_playwright
from batch4_browser_utils import bundled_icon_explorer,bundled_aspect_demo,bundled_icon_dock
import json
root=Path(__file__).resolve().parents[1];errors=[];samples=[]

def audit(page,root_sel,selectors,tolerance=5):
    return page.evaluate('''({rootSel,selectors,tolerance})=>{const root=document.querySelector(rootSel),rr=root.getBoundingClientRect();return selectors.flatMap(sel=>[...document.querySelectorAll(sel)].map(e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);const visible=Number(c.opacity)>.03&&c.display!=='none'&&r.width>0&&r.height>0;const issue=visible&&(r.left<rr.left-tolerance||r.top<rr.top-tolerance||r.right>rr.right+tolerance||r.bottom>rr.bottom+tolerance);return {selector:sel,issue,visible,rect:[r.left,r.top,r.right,r.bottom],root:[rr.left,rr.top,rr.right,rr.bottom]}})).filter(x=>x.issue)}''',{'rootSel':root_sel,'selectors':selectors,'tolerance':tolerance})

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    # Explorer at desktop and narrow responsive widths.
    for label,viewport in [('desktop',{'width':1720,'height':1100}),('narrow',{'width':760,'height':1100})]:
        page=b.new_page(viewport=viewport);page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(bundled_icon_explorer(root),wait_until='load')
        result=page.evaluate('''()=>{const body=document.documentElement;const cards=[...document.querySelectorAll('.icon-card')];return {scrollWidth:body.scrollWidth,clientWidth:body.clientWidth,cardIssues:cards.map(c=>{const r=c.getBoundingClientRect(),i=c.querySelector('.nex-icon').getBoundingClientRect();return {id:c.dataset.iconId,issue:i.left<r.left||i.top<r.top||i.right>r.right||i.bottom>r.bottom}}).filter(x=>x.issue)}}''')
        samples.append({'surface':'explorer','viewport':label,**result});page.close()
    # Three real composition sizes at multiple timeline points.
    configs={'landscape':{'width':1920,'height':1080},'square':{'width':1080,'height':1080},'portrait':{'width':1080,'height':1920}}
    for ratio,viewport in configs.items():
        page=b.new_page(viewport=viewport);page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(bundled_aspect_demo(root,ratio),wait_until='load')
        for t in [1.45,2.5,4.2,7.6,8.55]:
            page.evaluate('(t)=>window.seekComposition(t)',t);page.wait_for_timeout(20)
            issues=audit(page,'.icon-demo-canvas',['.icon-demo-layout','.icon-demo-copy','.icon-demo-copy h1','.icon-demo-copy p','.icon-demo-board','.icon-demo-hero','.icon-demo-tests','.icon-demo-panel'],8)
            samples.append({'surface':'aspect','ratio':ratio,'time':t,'issues':issues})
        page.evaluate('window.seekComposition(4.2)');page.wait_for_timeout(20);page.screenshot(path=str(root/f'reports/icon-demo-{ratio}.png'));page.close()
    # Dock scene after entrances and at every semantic selection.
    page=b.new_page(viewport={'width':1920,'height':1080});page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(bundled_icon_dock(root),wait_until='load')
    for t in [1.95,2.45,5.25,8.05,10.9,13.75,16.45,18.9]:
        page.evaluate('(t)=>window.seekComposition(t)',t);page.wait_for_timeout(20)
        issues=audit(page,'.icon-dock-canvas',['.dock-scene-grid','.dock-copy','.dock-workspace','.dock-detail','.paper-icon-dock','.dock-footer','.dock-cursor'],12)
        visible=page.evaluate("()=>[...document.querySelectorAll('.dock-large-item')].filter(x=>Number(getComputedStyle(x).opacity)>.5).length")
        samples.append({'surface':'dock','time':t,'issues':issues,'visibleLargeIcons':visible})
    page.evaluate('window.seekComposition(11.4)');page.wait_for_timeout(20);page.screenshot(path=str(root/'reports/icon-dock-demo.png'));page.close();b.close()
issue_samples=[x for x in samples if x.get('issues')]
scroll_fail=[x for x in samples if x.get('surface')=='explorer' and x.get('scrollWidth',0)>x.get('clientWidth',0)+2]
card_fail=[x for x in samples if x.get('surface')=='explorer' and x.get('cardIssues')]
dock_fail=[x for x in samples if x.get('surface')=='dock' and x.get('visibleLargeIcons')!=1]
status=not errors and not issue_samples and not scroll_fail and not card_fail and not dock_fail
report={'status':'PASS' if status else 'FAIL','pageErrors':errors,'sampleCount':len(samples),'issueSampleCount':len(issue_samples),'horizontalScrollFailures':scroll_fail,'cardFitFailures':card_fail,'dockVisibilityFailures':dock_fail,'samples':samples}
(root/'reports/batch4-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2));raise SystemExit(0 if status else 1)
