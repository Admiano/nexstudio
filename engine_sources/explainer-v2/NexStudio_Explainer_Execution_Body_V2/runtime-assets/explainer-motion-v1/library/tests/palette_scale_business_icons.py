from pathlib import Path
from playwright.sync_api import sync_playwright
from batch7_browser_utils import bundled_business_explorer
import json,sys,re
root=Path(__file__).resolve().parents[1];errors=[];tests=[]
def lum(hexv):
    h=hexv.lstrip('#'); rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    return .2126*vals[0]+.7152*vals[1]+.0722*vals[2]
def ratio(a,b):
    x,y=lum(a),lum(b);return (max(x,y)+.05)/(min(x,y)+.05)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');pg=b.new_page(viewport={'width':1700,'height':1000});pg.set_content(bundled_business_explorer(root),wait_until='load')
    palette_data={}
    for pal in ['warm','cobalt','charcoal']:
        pg.select_option('#businessPalette',pal)
        colors=pg.evaluate('''()=>{const s=getComputedStyle(document.documentElement);return {ink:s.getPropertyValue('--ink').trim(),paper:s.getPropertyValue('--paper-surface').trim(),primary:s.getPropertyValue('--primary').trim(),secondary:s.getPropertyValue('--secondary').trim(),accent:s.getPropertyValue('--accent').trim()}}''')
        palette_data[pal]={**colors,'contrast':ratio(colors['ink'],colors['paper'])}
        if palette_data[pal]['contrast']<4.5:errors.append(f'{pal}: insufficient ink/paper contrast')
        pg.screenshot(path=str(root/f'reports/business-palette-{pal}.png'))
    for treatment in ['paper-cutout','printed-outline']:
      pg.select_option('#businessTreatment',treatment)
      for size in ['32','42','96','176','260']:
        pg.evaluate(f"document.querySelector('#businessSize').innerHTML += '<option value=\"{size}\">{size}</option>'" if size not in ['42','96','176'] else 'void 0')
        pg.select_option('#businessSize',size)
        data=pg.evaluate('''()=>[...document.querySelectorAll('.nex-icon')].map(x=>{const r=x.getBoundingClientRect(),svg=x.querySelector('svg').getBoundingClientRect();return {id:x.dataset.iconId,w:r.width,h:r.height,svg:[svg.left,svg.top,svg.right,svg.bottom],box:[r.left,r.top,r.right,r.bottom],layers:x.querySelectorAll('svg>g').length}})''')
        bad=[x['id'] for x in data if abs(x['w']-float(size))>1.5 or abs(x['h']-float(size))>1.5 or x['layers']<5]
        tests.append({'treatment':treatment,'size':int(size),'count':len(data),'bad':bad})
        if bad:errors.append(f'{treatment} {size}: {len(bad)} bad icons')
    b.close()
report={'status':'PASS' if not errors else 'FAIL','palettes':palette_data,'scaleTests':tests,'errors':errors}
(root/'reports/batch7-palette-scale.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'paletteCount':len(palette_data),'scaleTests':len(tests),'errors':errors},indent=2));sys.exit(1 if errors else 0)
