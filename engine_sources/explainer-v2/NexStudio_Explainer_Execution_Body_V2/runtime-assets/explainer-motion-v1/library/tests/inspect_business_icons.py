from pathlib import Path
from playwright.sync_api import sync_playwright
from batch7_browser_utils import bundled_business_explorer,bundled_business_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];scenes={}
configs={'commerce-workflow':(1920,1080),'campaign-result':(1080,1080),'milestone-scene':(1080,1920)}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    ep=b.new_page(viewport={'width':1720,'height':1050});ep.set_content(bundled_business_explorer(root),wait_until='load');ep.screenshot(path=str(root/'reports/business-icon-explorer.png'),full_page=True);ep.close()
    for name,(w,h) in configs.items():
        pg=b.new_page(viewport={'width':w,'height':h});local=[];pg.on('pageerror',lambda e,local=local:local.append(str(e)));pg.set_content(bundled_business_scene(root,name),wait_until='load')
        samples=[]
        for t in [0,.6,1.7,3.1,5.7,7.5,9.2,10.75]:
            pg.evaluate(f'seekComposition({t})')
            audit=pg.evaluate('''()=>{const root=document.querySelector('.business-scene'),rr=root.getBoundingClientRect();const bad=[];for(const el of root.querySelectorAll('.business-layout,.business-copy,.business-board,.business-node,.nex-business-icon,h1,p,.business-tags')){const r=el.getBoundingClientRect(),s=getComputedStyle(el);if(s.opacity==='0'||r.width===0||r.height===0)continue;if(r.left<rr.left-2||r.top<rr.top-2||r.right>rr.right+2||r.bottom>rr.bottom+2)bad.push({cls:el.className||el.tagName,left:r.left,top:r.top,right:r.right,bottom:r.bottom});}return {bad,root:[rr.width,rr.height],icons:document.querySelectorAll('.nex-business-icon').length}}''')
            samples.append({'t':t,**audit})
        pg.evaluate('seekComposition(5.7)');pg.screenshot(path=str(root/f'reports/{name}.png'))
        pg.evaluate('seekComposition(10.5)');pg.screenshot(path=str(root/f'reports/{name}-late.png'))
        scenes[name]={'viewport':[w,h],'samples':samples,'browserErrors':local}
        if local or any(s['bad'] for s in samples):errors.append(f'{name}: browser/layout issue')
        pg.close()
    b.close()
report={'status':'PASS' if not errors else 'FAIL','scenes':scenes,'errors':errors}
(root/'reports/batch7-layout-inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'errors':errors,'sampleCount':sum(len(x['samples']) for x in scenes.values())},indent=2));sys.exit(1 if errors else 0)
