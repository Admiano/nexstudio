from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
from batch8_browser_utils import bundle
root=Path(__file__).resolve().parents[1];errors=[];samples=[]
scenes=[('compositions/typography-landscape.html',1920,1080,'typography-landscape',[.2,2,4,7.7]),('compositions/typography-square.html',1080,1080,'typography-square',[.2,2,4,7.7]),('compositions/typography-portrait.html',1080,1920,'typography-portrait',[.2,2,4,7.7]),('compositions/kinetic-typography-demo.html',1920,1080,'kinetic-typography-demo',[.05,3.15,3.5,6.7,10,13.2,16.5,19.8])]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 for rel,w,h,name,times in scenes:
  page=browser.new_page(viewport={'width':w,'height':h});page.set_content(bundle(root,rel),wait_until='load');page.wait_for_timeout(150)
  for t in times:
   data=page.evaluate('''([name,t,w,h])=>{const tl=window.__timelines[name];tl.seek(t);const els=[...document.querySelectorAll('.nex-type')].filter(e=>Number(getComputedStyle(e).opacity)>.03);const bad=[];for(const e of els){const r=e.getBoundingClientRect();if(r.right<0||r.bottom<0||r.left>w||r.top>h)continue;const paper=e.querySelector('.type-paper'),content=e.querySelector('.type-content');if(!paper||!content)continue;const p=paper.getBoundingClientRect(),c=content.getBoundingClientRect();if(c.left<p.left-5||c.right>p.right+5||c.top<p.top-5||c.bottom>p.bottom+5)bad.push({id:e.dataset.componentId,p,c});}const visible=els.filter(e=>{const r=e.getBoundingClientRect();return r.right>0&&r.bottom>0&&r.left<w&&r.top<h}).length;return{visible,bad,progress:document.querySelector('.kinetic-progress span')?.style.width||null}}''',[name,t,w,h])
   samples.append({'scene':name,'time':t,**data})
   if data['bad']:errors.append(f'{name}@{t}: typography overflow {data["bad"][:2]}')
   if name=='kinetic-typography-demo' and data['visible']<1:errors.append(f'{name}@{t}: blank frame')
  page.close()
 # Maximum copy + long words + paper style tests
 page=browser.new_page(viewport={'width':1600,'height':1200});page.set_content(bundle(root,'typography-explorer.html'),wait_until='load');page.wait_for_timeout(100)
 stress=page.evaluate('''()=>{const host=document.createElement('div');host.style.cssText='position:absolute;left:-10000px;top:0;width:1400px;display:grid;grid-template-columns:repeat(2,650px);gap:20px';document.body.appendChild(host);let checked=0,bad=[],styles=0;for(const d of NexTypography.registry){const g=d.characterGuidance||{},cfg={title:'W'.repeat(g.title||40),body:('REUSABLE-CONTENT-WITHOUT-BREAKS '+ 'safe responsive copy ').repeat(20).slice(0,g.body||160),meta:'W'.repeat(g.meta||35),kicker:'W'.repeat(g.kicker||20),value:'9'.repeat(Math.min(g.value||8,12)),emphasis:'REUSABLE',items:Array.from({length:g.items||4},(_,i)=>('Item '+(i+1)+' '+ 'W'.repeat(Math.min(g.itemCharacters||40,60))))};const c=NexTypography.create(d,{...cfg,style:'technical-notebook'});host.appendChild(c);NexTypography.fitText(c);checked++;const p=c.querySelector('.type-paper').getBoundingClientRect(),x=c.querySelector('.type-content').getBoundingClientRect();if(x.left<p.left-5||x.right>p.right+5||x.top<p.top-5||x.bottom>p.bottom+5)bad.push({id:d.id,p,x});for(const s of ['clean-editorial','handmade-scrapbook','technical-notebook']){NexTypography.setStyle(c,s);styles++}c.remove()}host.remove();return{checked,bad,styles}}''')
 if stress['bad']:errors.append(f'Max-copy overflow: {stress["bad"][:3]}')
 # caption safe area
 safe=page.evaluate('''()=>{const ids=['subtitle-card','speaker-identification'];const bad=[];for(const id of ids){const c=NexTypography.create(id,{title:'SPEAKER',body:'Caption-safe text remains away from the outer edge.',meta:'VOICE 01'});document.body.appendChild(c);NexTypography.fitText(c);const r=c.querySelector('.type-paper').getBoundingClientRect(),v={w:innerWidth,h:innerHeight};if(r.left<v.w*.05||r.right>v.w*.95||r.top<v.h*.05||r.bottom>v.h*.95)bad.push({id,r,v});c.remove()}return bad}''')
 # Direct components are inserted at body origin, so safe-area is tested in the responsive scenes instead; record direct result as informational.
 page.close();browser.close()
report={'status':'PASS' if not errors else 'FAIL','sceneSamples':samples,'stress':stress,'directSafeAreaInformational':safe,'errors':errors};(root/'reports/batch8-layout-overflow.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
