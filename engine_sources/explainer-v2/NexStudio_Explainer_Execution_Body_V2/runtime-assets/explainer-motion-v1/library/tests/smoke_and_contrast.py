from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_utils import bundled_explorer
import json, math
root=Path(__file__).resolve().parents[1]
html=bundled_explorer(root)

def rgb_tuple(s):
    vals=[float(x) for x in s.replace('rgba(','').replace('rgb(','').replace(')','').split(',')[:3]]
    return tuple(vals)
def lum(rgb):
    xs=[]
    for c in rgb:
        v=c/255
        xs.append(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)
    return .2126*xs[0]+.7152*xs[1]+.0722*xs[2]
def contrast(a,b):
    l1,l2=lum(a),lum(b); hi,lo=max(l1,l2),min(l1,l2); return (hi+.05)/(lo+.05)
report={'functional':{},'contrast':[],'status':'PASS','errors':[]}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    page=b.new_page(viewport={'width':1440,'height':1000})
    page.set_content(html,wait_until='load')
    report['functional']['componentCount']=page.locator('.card').count()
    report['functional']['filterCounts']={}
    for label,expected in [('Surfaces',8),('Edges',8),('Shadows',6),('Print',6),('Fasteners',12)]:
        page.get_by_role('button',name=label).click()
        count=page.locator('.card').count(); report['functional']['filterCounts'][label]=count
        if count!=expected: report['errors'].append(f'{label}: expected {expected}, got {count}')
    page.get_by_role('button',name='All').click()
    for palette in ['warm','cobalt','charcoal']:
        page.select_option('#paletteSelect',palette)
        body=page.evaluate("()=>{const b=getComputedStyle(document.body),h=getComputedStyle(document.querySelector('.hero h1')),c=getComputedStyle(document.querySelector('.card'));return {bodyBg:b.backgroundColor,heading:h.color,cardBg:c.backgroundColor,cardText:c.color}}")
        r1=contrast(rgb_tuple(body['heading']),rgb_tuple(body['bodyBg']))
        r2=contrast(rgb_tuple(body['cardText']),rgb_tuple(body['cardBg']))
        report['contrast'].append({'palette':palette,'headingOnCanvas':round(r1,2),'cardTextOnCard':round(r2,2)})
        if r1<3 or r2<4.5: report['errors'].append(f'{palette}: contrast below threshold')
    for style in ['clean-editorial','handmade-scrapbook','technical-notebook','bold-paper-collage']:
        page.select_option('#styleSelect',style)
        if page.evaluate('()=>document.documentElement.dataset.paperStyle')!=style:report['errors'].append(f'Style switch failed: {style}')
    page.get_by_role('button',name='Replay visible').click()
    page.wait_for_timeout(150)
    opacity=page.locator('.paper-sheet').first.evaluate('(e)=>getComputedStyle(e).opacity')
    report['functional']['replayTriggered']=float(opacity)<1
    if not report['functional']['replayTriggered']:report['errors'].append('Replay did not trigger')
    b.close()
if report['errors']:report['status']='FAIL'
(root/'reports/smoke-and-contrast.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
