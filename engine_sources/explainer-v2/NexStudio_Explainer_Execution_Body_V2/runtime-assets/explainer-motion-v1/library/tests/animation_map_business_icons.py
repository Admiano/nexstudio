from pathlib import Path
from playwright.sync_api import sync_playwright
from batch7_browser_utils import bundled_business_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];maps={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    for name in ['commerce-workflow','campaign-result','milestone-scene']:
        pg=b.new_page(viewport={'width':1920 if name=='commerce-workflow' else 1080,'height':1920 if name=='milestone-scene' else 1080});pg.set_content(bundled_business_scene(root,name),wait_until='load')
        rows=[];last=None;dead=[];start_dead=None
        for i in range(109):
            t=round(i*.1,2);pg.evaluate(f'seekComposition({t})')
            snap=pg.evaluate('''()=>JSON.stringify([...document.querySelectorAll('.business-node,.nex-business-icon,.icon-symbol-layer *')].slice(0,260).map(n=>{const c=getComputedStyle(n),r=n.getBoundingClientRect();return [n.className,c.transform,c.opacity,c.strokeDashoffset,Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]}))''')
            changed=last is not None and snap!=last;rows.append({'t':t,'changed':changed})
            if i>0 and not changed and start_dead is None:start_dead=t-.1
            if changed and start_dead is not None:
                if t-start_dead>1.0:dead.append([start_dead,t])
                start_dead=None
            last=snap
        if start_dead is not None and 10.8-start_dead>1.0:dead.append([start_dead,10.8])
        maps[name]={'duration':10.8,'samples':109,'changedSamples':sum(x['changed'] for x in rows),'deadZonesOverOneSecond':dead}
        if dead:errors.append(f'{name}: dead zones {dead}')
        pg.close()
    b.close()
report={'status':'PASS' if not errors else 'FAIL','scenes':maps,'errors':errors,'tweenEstimate':36*2+24*2+3*5}
(root/'reports/batch7-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
