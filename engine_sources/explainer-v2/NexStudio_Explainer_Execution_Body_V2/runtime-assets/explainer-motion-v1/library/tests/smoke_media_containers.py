from pathlib import Path
from playwright.sync_api import sync_playwright
from batch9_browser_utils import bundle_media_explorer,bundle_media_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];report={}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 page=b.new_page(viewport={'width':1720,'height':1100});local=[]
 page.on('pageerror',lambda e:local.append(str(e)));page.on('console',lambda m:local.append(m.text) if m.type=='error' else None)
 page.set_content(bundle_media_explorer(root),wait_until='load');page.wait_for_timeout(800)
 structure=page.evaluate('''()=>[...document.querySelectorAll('.media-card')].map(card=>{const el=card.querySelector('.nex-media'),def=NexMediaContainers.getDef(card.dataset.mediaId);return{id:def.id,slug:def.slug,shell:!!el.querySelector('.media-shell'),media:el.querySelectorAll('.media-asset,.media-placeholder').length,aria:el.getAttribute('aria-label'),motions:def.compatibleMotions.length,independent:def.contentAnimationIndependent}})''')
 page.select_option('#mediaType','mobile-phone');page.select_option('#mediaSource','video');page.select_option('#mediaCrop','contain');page.fill('#mediaFocalX','25');page.fill('#mediaFocalY','70');page.select_option('#mediaBorder','pinned');page.select_option('#mediaStyle','technical-notebook');page.select_option('#mediaPalette','cobalt');page.select_option('#mediaEnergy','high');page.wait_for_timeout(250)
 controls=page.evaluate('''()=>{const x=NexMediaExplorer.live,a=x.querySelector('.media-asset');return{slug:x.dataset.slug,tag:a.tagName,fit:getComputedStyle(a).objectFit,pos:getComputedStyle(a).objectPosition,border:x.dataset.border,style:document.documentElement.dataset.paperStyle,primary:getComputedStyle(document.documentElement).getPropertyValue('--primary').trim(),energy:getComputedStyle(document.documentElement).getPropertyValue('--motion-scale').trim()}}''')
 api=page.evaluate('''()=>{let e=NexMediaContainers.create('browser-window',{media:{type:'image',src:'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" fill="purple"/></svg>'}});document.body.append(e);NexMediaContainers.setCrop(e,'contain');NexMediaContainers.setFocalPoint(e,22,77);NexMediaContainers.setBorder(e,'torn');let n=NexMediaContainers.replaceMedia(e,{type:'transparent-png',src:'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><circle cx="20" cy="20" r="18" fill="orange"/></svg>'});let u=NexMediaContainers.update(n,{title:'Updated title'});let tl=NexMediaContainers.animate(u,{duration:1.4,motion:'unfold'});tl.seek(.7);const result={fit:getComputedStyle(u.querySelector('.media-asset')).objectFit,pos:getComputedStyle(u.querySelector('.media-asset')).objectPosition,border:u.dataset.border,title:u.querySelector('.media-title')?.textContent,duration:tl.duration(),changed:getComputedStyle(u.querySelector('.media-shell')).transform!=='none',api:['create','animate','replaceMedia','update','setCrop','setFocalPoint','setBorder','setStyle','fitText','getDef'].every(k=>typeof NexMediaContainers[k]==='function')};u.remove();return result}''')
 report['explorer']={'count':len(structure),'badShell':[x['id'] for x in structure if not x['shell']],'missingMedia':[x['id'] for x in structure if x['media']<1],'missingAria':[x['id'] for x in structure if not x['aria']],'badMotions':[x['id'] for x in structure if x['motions']<3],'notIndependent':[x['id'] for x in structure if not x['independent']],'controls':controls,'api':api,'errors':local}
 if local or len(structure)!=24 or any(report['explorer'][k] for k in ['badShell','missingMedia','missingAria','badMotions','notIndependent']):errors.append('Explorer structure failure')
 if controls['slug']!='mobile-phone' or controls['tag']!='VIDEO' or controls['fit']!='contain' or controls['pos']!='25% 70%' or controls['border']!='pinned' or not api['api'] or api['fit']!='contain' or api['pos']!='22% 77%' or api['border']!='torn':errors.append('Replacement controls/API failure')
 for name,w,h in [('product-demo',1920,1080),('creator-profile',1080,1080),('photo-story',1080,1920)]:
  pg=b.new_page(viewport={'width':w,'height':h});le=[];pg.on('pageerror',lambda e,le=le:le.append(str(e)));pg.on('console',lambda m,le=le:le.append(m.text) if m.type=='error' else None)
  pg.set_content(bundle_media_scene(root,name),wait_until='load');pg.wait_for_timeout(450)
  snaps=[]
  for t in [0,.7,2.4,5.9,8.8,11.8]:
   pg.evaluate('(t)=>seekComposition(t)',t);snaps.append(pg.evaluate('''()=>({visible:[...document.querySelectorAll('.nex-media')].filter(x=>getComputedStyle(x).opacity!=='0').length,blank:[...document.querySelectorAll('.media-window')].filter(x=>!x.querySelector('.media-asset,.media-placeholder,.media-document-lines,.media-waveform,.media-body,.media-bubble')).length,transforms:[...document.querySelectorAll('.media-shell')].map(x=>getComputedStyle(x).transform)})'''))
  d=pg.evaluate('''()=>{const r=document.querySelector('.media-scene'),tl=window.__timelines[r.id];return{id:r.id,duration:tl.duration(),containers:document.querySelectorAll('.nex-media').length,assets:[...document.querySelectorAll('.media-asset')].map(x=>({tag:x.tagName,ok:x.tagName==='VIDEO'?true:x.complete&&x.naturalWidth>0}))}}''');d['snaps']=snaps;d['errors']=le;report[name]=d
  if le or d['duration']!=12 or d['containers']!=3 or not all(a['ok'] for a in d['assets']) or any(s['visible']<3 for s in snaps[1:]):errors.append(name+' scene failure')
  pg.close()
 b.close()
report['status']='PASS' if not errors else 'FAIL';report['errors']=errors
(root/'reports/batch9-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
