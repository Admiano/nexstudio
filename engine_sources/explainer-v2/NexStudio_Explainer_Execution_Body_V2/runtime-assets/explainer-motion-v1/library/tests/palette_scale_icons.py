from pathlib import Path
from playwright.sync_api import sync_playwright
from batch4_browser_utils import bundled_icon_explorer
import json,math
root=Path(__file__).resolve().parents[1];errors=[];samples=[]

def luminance(hexv):
    h=hexv.lstrip('#'); rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    vals=[v/12.92 if v<=.03928 else ((v+.055)/1.055)**2.4 for v in rgb]
    return .2126*vals[0]+.7152*vals[1]+.0722*vals[2]
def contrast(a,b):
    l1,l2=sorted([luminance(a),luminance(b)],reverse=True);return (l1+.05)/(l2+.05)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1720,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(bundled_icon_explorer(root),wait_until='load')
    for palette in ['warm','cobalt','charcoal']:
        page.select_option('#iconPalette',palette)
        vars=page.evaluate("()=>Object.fromEntries(['--ink','--paper-surface','--primary','--secondary','--accent'].map(k=>[k,getComputedStyle(document.documentElement).getPropertyValue(k).trim()]))")
        ratios={'inkOnPaper':contrast(vars['--ink'],vars['--paper-surface'])}
        samples.append({'type':'palette','palette':palette,'vars':vars,'contrast':ratios})
        page.screenshot(path=str(root/f'reports/icon-palette-{palette}.png'),full_page=False)
    for treatment in ['paper-cutout','printed-outline']:
        page.select_option('#iconTreatment',treatment)
        for size in [32,42,96,176,260]:
            result=page.evaluate('''({size,treatment})=>{const host=document.createElement('div');host.style.cssText='position:fixed;left:-10000px;top:0;display:flex;gap:12px;align-items:flex-start';document.body.appendChild(host);const out=NexIcons.registry.map(def=>{const icon=NexIcons.create(def,{size,treatment,state:def.states.includes('completed')?'completed':'active'});host.appendChild(icon);const r=icon.getBoundingClientRect(),svg=icon.querySelector('svg').getBoundingClientRect();const parts=[...icon.querySelectorAll('.icon-symbol-layer > *')].map(x=>x.getBoundingClientRect());const issue=Math.abs(r.width-size)>.6||Math.abs(r.height-size)>.6||svg.left<r.left-1||svg.top<r.top-1||svg.right>r.right+1||svg.bottom>r.bottom+1||parts.some(p=>p.left<r.left-10||p.top<r.top-10||p.right>r.right+10||p.bottom>r.bottom+10);return {id:def.id,width:r.width,height:r.height,issue}});host.remove();return out}''',{'size':size,'treatment':treatment})
            samples.append({'type':'scale','treatment':treatment,'size':size,'issues':[x for x in result if x['issue']]})
    b.close()
contrast_fail=[x for x in samples if x['type']=='palette' and x['contrast']['inkOnPaper']<7]
scale_fail=[x for x in samples if x['type']=='scale' and x['issues']]
status=not errors and not contrast_fail and not scale_fail
report={'status':'PASS' if status else 'FAIL','pageErrors':errors,'paletteTests':3,'scaleCombinations':10,'iconsPerScale':40,'contrastFailures':contrast_fail,'scaleFailures':scale_fail,'samples':samples}
(root/'reports/batch4-palette-scale.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2));raise SystemExit(0 if status else 1)
