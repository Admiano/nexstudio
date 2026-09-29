from pathlib import Path
from playwright.sync_api import sync_playwright
from batch5_browser_utils import bundled_creator_explorer
import json
root=Path(__file__).resolve().parents[1];errors=[];samples=[]
def lum(h):
    h=h.lstrip('#');rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];v=[x/12.92 if x<=.03928 else ((x+.055)/1.055)**2.4 for x in rgb];return .2126*v[0]+.7152*v[1]+.0722*v[2]
def contrast(a,b):
    l1,l2=sorted([lum(a),lum(b)],reverse=True);return (l1+.05)/(l2+.05)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1720,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(bundled_creator_explorer(root),wait_until='load')
    for pal in ['warm','cobalt','charcoal']:
        page.select_option('#creatorPalette',pal);vars=page.evaluate("()=>Object.fromEntries(['--ink','--paper-surface','--primary','--secondary','--accent'].map(k=>[k,getComputedStyle(document.documentElement).getPropertyValue(k).trim()]))");samples.append({'type':'palette','palette':pal,'vars':vars,'contrast':contrast(vars['--ink'],vars['--paper-surface'])});page.screenshot(path=str(root/f'reports/creator-palette-{pal}.png'))
    for treatment in ['paper-cutout','printed-outline']:
        for size in [32,42,96,176,260]:
            result=page.evaluate('''({size,treatment})=>{const host=document.createElement('div');host.style.cssText='position:fixed;left:-10000px;top:0;display:flex;gap:10px';document.body.appendChild(host);const out=NexCreatorIcons.registry.map(def=>{const icon=NexCreatorIcons.create(def,{size,treatment,state:def.states.includes('completed')?'completed':'active'});host.appendChild(icon);const r=icon.getBoundingClientRect(),s=icon.querySelector('svg').getBoundingClientRect(),parts=[...icon.querySelectorAll('.icon-symbol-layer > *')].filter(x=>getComputedStyle(x).display!=='none').map(x=>x.getBoundingClientRect());return {id:def.id,issue:Math.abs(r.width-size)>.7||Math.abs(r.height-size)>.7||s.left<r.left-1||s.top<r.top-1||s.right>r.right+1||s.bottom>r.bottom+1||parts.some(p=>p.left<r.left-12||p.top<r.top-12||p.right>r.right+12||p.bottom>r.bottom+12)}});host.remove();return out}''',{'size':size,'treatment':treatment});samples.append({'type':'scale','size':size,'treatment':treatment,'issues':[x for x in result if x['issue']]})
    b.close()
cf=[x for x in samples if x['type']=='palette' and x['contrast']<7];sf=[x for x in samples if x['type']=='scale' and x['issues']];status=not errors and not cf and not sf
report={'status':'PASS' if status else 'FAIL','pageErrors':errors,'paletteTests':3,'scaleCombinations':10,'iconsPerScale':48,'contrastFailures':cf,'scaleFailures':sf,'samples':samples}
(root/'reports/batch5-palette-scale.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2));raise SystemExit(0 if status else 1)
