from pathlib import Path
from playwright.sync_api import sync_playwright
from batch8_browser_utils import bundle
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];palette_results=[];safe_results=[]
def lum(hexv):
 h=hexv.lstrip('#');rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];v=[x/12.92 if x<=.03928 else ((x+.055)/1.055)**2.4 for x in rgb];return .2126*v[0]+.7152*v[1]+.0722*v[2]
def ratio(a,b):
 la,lb=lum(a),lum(b);return (max(la,lb)+.05)/(min(la,lb)+.05)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 page=b.new_page(viewport={'width':1600,'height':1000});page.set_content(bundle(root,'typography-explorer.html'),wait_until='load')
 for name,pal in {'warm':('#171419','#FFFDF8'),'cobalt':('#11182A','#FFFFFF'),'charcoal':('#171717','#F8F2E8')}.items():
  page.evaluate('(n)=>NexTheme.applyPalette(n)',name)
  data=page.evaluate('''()=>{const host=document.createElement('div');host.style.cssText='position:absolute;left:-10000px;top:0';document.body.appendChild(host);let count=0,subtitle=null;for(const d of NexTypography.registry){const c=NexTypography.create(d,{title:'Readable type',body:'Contrast remains strong.',meta:'NEXSTUDIO'});host.appendChild(c);NexTypography.fitText(c);count++;if(d.slug==='subtitle-card'){const p=c.querySelector('.type-paper');subtitle={bg:getComputedStyle(p).backgroundColor,color:getComputedStyle(c.querySelector('.type-body')).color}}c.remove()}host.remove();return{count,subtitle}}''')
  r=ratio(*pal);palette_results.append({'palette':name,'components':data['count'],'inkOnPaperRatio':round(r,2),'subtitle':data['subtitle']})
  if r<7:errors.append(f'{name} ink contrast below 7:1: {r}')
 # Safe-area placements at all ratios
 for w,h,label in [(1920,1080,'16:9'),(1080,1080,'1:1'),(1080,1920,'9:16')]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle(root,'typography-explorer.html'),wait_until='load');result=pg.evaluate('''([w,h])=>{document.body.innerHTML='<div id="safe" style="position:fixed;inset:5%;display:flex;flex-direction:column;justify-content:space-between;align-items:center"></div>';const safe=document.querySelector('#safe'),a=NexTypography.create('speaker-identification',{title:'MAYA CHEN',body:'Product narrator',meta:'VOICE 01'}),c=NexTypography.create('subtitle-card',{body:'Caption-safe copy remains inside the five-percent action-safe area.',meta:'VOICE 01'});a.style.setProperty('--type-width',Math.min(620,w*.72)+'px');a.style.setProperty('--type-height',Math.min(340,h*.3)+'px');c.style.setProperty('--type-width',Math.min(760,w*.82)+'px');c.style.setProperty('--type-height',Math.min(250,h*.22)+'px');safe.append(a,c);NexTypography.fitText(a);NexTypography.fitText(c);const sr=safe.getBoundingClientRect(),items=[a,c].map(e=>{const p=e.querySelector('.type-paper').getBoundingClientRect();return{id:e.dataset.slug,left:p.left,top:p.top,right:p.right,bottom:p.bottom,inside:p.left>=sr.left-1&&p.top>=sr.top-1&&p.right<=sr.right+1&&p.bottom<=sr.bottom+1}});return{safe:{left:sr.left,top:sr.top,right:sr.right,bottom:sr.bottom},items}}''',[w,h]);safe_results.append({'ratio':label,'width':w,'height':h,**result});
  if not all(x['inside'] for x in result['items']):errors.append(f'{label} caption safe-area failure')
  pg.close()
 b.close()
report={'status':'PASS' if not errors else 'FAIL','paletteTests':palette_results,'captionSafeAreaTests':safe_results,'errors':errors};(root/'reports/batch8-palette-caption-safe.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
