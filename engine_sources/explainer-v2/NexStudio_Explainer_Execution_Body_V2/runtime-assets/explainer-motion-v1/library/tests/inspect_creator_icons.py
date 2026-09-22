from pathlib import Path
from playwright.sync_api import sync_playwright
from batch5_browser_utils import bundled_creator_explorer,bundled_creator_scene
import json
root=Path(__file__).resolve().parents[1];errors=[];samples=[]
def audit(page,root_sel,selectors,tol=8):
    return page.evaluate('''({rootSel,selectors,tol})=>{const root=document.querySelector(rootSel),rr=root.getBoundingClientRect();return selectors.flatMap(sel=>[...document.querySelectorAll(sel)].map(e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e),visible=Number(c.opacity)>.03&&c.display!=='none'&&r.width>0&&r.height>0;return {selector:sel,visible,issue:visible&&(r.left<rr.left-tol||r.top<rr.top-tol||r.right>rr.right+tol||r.bottom>rr.bottom+tol),rect:[r.left,r.top,r.right,r.bottom],root:[rr.left,rr.top,rr.right,rr.bottom]}})).filter(x=>x.issue)}''',{'rootSel':root_sel,'selectors':selectors,'tol':tol})
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    for label,vp in [('desktop',{'width':1720,'height':1100}),('narrow',{'width':760,'height':1100})]:
        page=b.new_page(viewport=vp);page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(bundled_creator_explorer(root),wait_until='load')
        result=page.evaluate('''()=>{const d=document.documentElement,cards=[...document.querySelectorAll('.icon-card')];return {scrollWidth:d.scrollWidth,clientWidth:d.clientWidth,cardIssues:cards.map(c=>{const r=c.getBoundingClientRect(),i=c.querySelector('.nex-icon').getBoundingClientRect();return {id:c.dataset.iconId,issue:i.left<r.left-8||i.top<r.top-8||i.right>r.right+8||i.bottom>r.bottom+8}}).filter(x=>x.issue)}}''');samples.append({'surface':'explorer','viewport':label,**result});page.close()
    configs=[('creator-workflow',{'width':1920,'height':1080}),('media-production',{'width':1080,'height':1080}),('publishing',{'width':1080,'height':1920})]
    for name,vp in configs:
        page=b.new_page(viewport=vp);page.on('pageerror',lambda e,n=name:errors.append(n+': '+str(e)));page.set_content(bundled_creator_scene(root,name),wait_until='load')
        for t in [.8,1.8,3.6,6.4,8.6,10.0]:
            page.evaluate('(x)=>window.seekComposition(x)',t);page.wait_for_timeout(20)
            issues=audit(page,'.creator-scene',['.creator-scene-layout','.creator-scene-copy','.creator-scene-copy h1','.creator-scene-copy p','.creator-icon-board','.creator-node','.creator-scene-tags'],12)
            nodefit=[] if t<6 else page.evaluate('''()=>[...document.querySelectorAll('.creator-node')].map(n=>{const nr=n.getBoundingClientRect(),i=n.querySelector('.nex-icon').getBoundingClientRect();return {id:n.dataset.icon,issue:i.left<nr.left-20||i.top<nr.top-20||i.right>nr.right+20||i.bottom>nr.bottom+20}}).filter(x=>x.issue)''')
            samples.append({'surface':'scene','name':name,'time':t,'issues':issues,'nodeFit':nodefit})
        page.close()
    b.close()
issues=[x for x in samples if x.get('issues') or x.get('nodeFit')]
scroll=[x for x in samples if x.get('surface')=='explorer' and x.get('scrollWidth',0)>x.get('clientWidth',0)+2]
cards=[x for x in samples if x.get('surface')=='explorer' and x.get('cardIssues')]
status=not errors and not issues and not scroll and not cards
report={'status':'PASS' if status else 'FAIL','pageErrors':errors,'sampleCount':len(samples),'issueSamples':issues,'horizontalScrollFailures':scroll,'cardFitFailures':cards,'samples':samples}
(root/'reports/batch5-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2));raise SystemExit(0 if status else 1)
