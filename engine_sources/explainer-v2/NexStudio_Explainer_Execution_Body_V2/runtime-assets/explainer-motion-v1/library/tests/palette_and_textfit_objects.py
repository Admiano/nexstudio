from pathlib import Path
from playwright.sync_api import sync_playwright
from batch2_browser_utils import bundled_object_composition,bundled_object_explorer
import json,math
root=Path(__file__).resolve().parents[1]
def lum(hexv):
    h=hexv.lstrip('#');rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];rgb=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb];return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
def contrast(a,b):
    x,y=lum(a),lum(b);return (max(x,y)+.05)/(min(x,y)+.05)
report={'palettes':[],'textFit':{},'errors':[]}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 # palette tests on composition
 html=bundled_object_composition(root)
 for name in ['warm','cobalt','charcoal']:
  page=b.new_page(viewport={'width':1280,'height':720});page.on('pageerror',lambda e:report['errors'].append(str(e)));page.set_content(html,wait_until='load');page.evaluate('(n)=>NexTheme.applyPalette(n)',name);page.evaluate('(t)=>window.seekComposition(t)',6.1);page.wait_for_timeout(50)
  vals=page.evaluate("()=>{const s=getComputedStyle(document.documentElement);return {ink:s.getPropertyValue('--ink').trim(),paper:s.getPropertyValue('--paper-surface').trim(),bg:s.getPropertyValue('--paper-bg').trim(),primary:s.getPropertyValue('--primary').trim(),secondary:s.getPropertyValue('--secondary').trim(),accent:s.getPropertyValue('--accent').trim()}}")
  vals['inkPaperContrast']=round(contrast(vals['ink'],vals['paper']),2);vals['inkBgContrast']=round(contrast(vals['ink'],vals['bg']),2);vals['pass']=vals['inkPaperContrast']>=4.5 and vals['inkBgContrast']>=4.5
  page.screenshot(path=str(root/f'reports/batch2-palette-{name}.png'));report['palettes'].append({'name':name,**vals});page.close()
 # max-copy fitting across text-bearing objects
 page=b.new_page(viewport={'width':1600,'height':1000});page.set_content(bundled_object_explorer(root),wait_until='load')
 fit=page.evaluate('''()=>{const host=document.createElement('div');host.style.cssText='position:absolute;left:-10000px;top:0;width:1200px;display:flex;flex-wrap:wrap';document.body.appendChild(host);let checked=0,overflows=[];for(const d of NexPaperObjects.registry){if(d.subtype==='attachment')continue;const maxTitle=d.slots.title?.maxCharacters||44,maxBody=d.slots.body?.maxCharacters||180;const e=NexPaperObjects.create(d,{title:'W'.repeat(maxTitle),body:'Reusable dynamic paper content '.repeat(Math.ceil(maxBody/31)).slice(0,maxBody)});host.appendChild(e);NexPaperObjects.fitText(e);for(const x of e.querySelectorAll('[data-fit]')){checked++;if(x.scrollHeight>x.clientHeight+4||x.scrollWidth>x.clientWidth+4)overflows.push({id:d.id,text:x.textContent.slice(0,30),sw:x.scrollWidth,cw:x.clientWidth,sh:x.scrollHeight,ch:x.clientHeight})}}host.remove();return {checked,overflows}}''')
 report['textFit']=fit;page.close();b.close()
report['status']='PASS' if all(x['pass'] for x in report['palettes']) and not report['textFit'].get('overflows') and not report['errors'] else 'FAIL'
(root/'reports/batch2-palette-textfit.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'palettes':report['palettes'],'textFitChecked':report['textFit'].get('checked'),'textOverflows':len(report['textFit'].get('overflows',[])),'errors':report['errors']},indent=2));raise SystemExit(0 if report['status']=='PASS' else 1)
