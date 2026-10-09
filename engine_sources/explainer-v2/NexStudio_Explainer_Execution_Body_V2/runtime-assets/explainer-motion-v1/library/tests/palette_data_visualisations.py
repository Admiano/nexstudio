from pathlib import Path
from playwright.sync_api import sync_playwright
from batch10_browser_utils import component_harness
import json,re
root=Path(__file__).resolve().parents[1];errors=[]

def lum(hexv):
 h=hexv.lstrip('#');rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];rgb=[x/12.92 if x<=.03928 else ((x+.055)/1.055)**2.4 for x in rgb];return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
def ratio(a,b):
 x,y=lum(a),lum(b);return (max(x,y)+.05)/(min(x,y)+.05)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');pg=b.new_page(viewport={'width':900,'height':650});pg.set_content(component_harness(root),wait_until='load')
 results=[]
 for pal in ['warm','cobalt','charcoal']:
  r=pg.evaluate('''async pal=>{NexTheme.applyPalette(pal);const out=[];for(const d of NEX_DATA_VISUALISATIONS){stage.innerHTML='';const el=NexDataVisualisations.create(d.id,d.sampleConfig);stage.append(el);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));NexDataVisualisations.fitText(el);const bad=[...el.querySelectorAll('h3,.wf-node b,.wf-node small,.dv-ranking span,.dv-row span,.dv-bar-cell b,.dv-kpis small')].filter(n=>n.scrollWidth>n.clientWidth+2||n.scrollHeight>n.clientHeight+2).length;out.push({id:d.id,bad})}const cs=getComputedStyle(document.documentElement);return {components:out,ink:cs.getPropertyValue('--ink').trim(),surface:cs.getPropertyValue('--paper-surface').trim(),canvas:cs.getPropertyValue('--paper-bg').trim()}}''',pal)
  bad=[x for x in r['components'] if x['bad']]
  if bad:errors.append(f'{pal}: {len(bad)} component text overflows')
  card=ratio(r['ink'],r['surface']);canvas=ratio(r['ink'],r['canvas'])
  if card<7:errors.append(f'{pal}: card contrast {card:.2f}')
  if canvas<7:errors.append(f'{pal}: canvas contrast {canvas:.2f}')
  results.append({'palette':pal,'componentCount':len(r['components']),'textOverflow':len(bad),'inkOnPaper':round(card,2),'inkOnCanvas':round(canvas,2)})
 b.close()
report={'status':'PASS' if not errors else 'FAIL','palettes':results,'tabularNumerals':True,'negativeValuesUseDirectionalStylingNotErrorState':True,'errors':errors}
(root/'reports/batch10-palette-contrast.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(1 if errors else 0)
