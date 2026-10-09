from pathlib import Path
from playwright.sync_api import sync_playwright
from batch14_browser_utils import bundle
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];details={}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage','--allow-file-access-from-files','--autoplay-policy=no-user-gesture-required'])
 pg=b.new_page(viewport={'width':1440,'height':900});es=[];pg.on('pageerror',lambda e:es.append(str(e)));pg.set_content(bundle(root,'sound-audition.html'),wait_until='load');pg.wait_for_timeout(300)
 details['soundCards']=pg.locator('.sound-card').count();details['pairCards']=pg.locator('.audio-pair-card').count()
 if details['soundCards']!=24:errors.append('Explorer did not render 24 sounds')
 if details['pairCards']!=40:errors.append('Explorer did not render 40 pairings')
 pg.fill('#audioSearch','stamp');pg.wait_for_timeout(80);details['stampFilter']=pg.locator('.sound-card').count()
 if details['stampFilter']<1:errors.append('Search failed')
 pg.fill('#audioSearch','');pg.select_option('#audioCategory','paper-foley');pg.wait_for_timeout(80);details['paperFilter']=pg.locator('.sound-card').count()
 if details['paperFilter']<8:errors.append('Category filter failed')
 api=pg.evaluate('''()=>{const r=NexAudio.recommend({tags:['transition.page']});const el=NexAudio.createElement('audio.page-turn-soft',{volume:.8,voiceoverDuckingDb:6,musicDuckingDb:3});return{registry:NexAudio.registry.length,recommend:r[0]?.id,src:el.getAttribute('src'),volume:el.volume,approvedDefault:NexAudio.search({includeCandidates:false}).length}}''')
 details['api']=api
 if api['registry']!=24 or not api['src'] or not (0<api['volume']<.8):errors.append('Audio API failed')
 if api['approvedDefault']!=0:errors.append('Candidate policy failed')
 if es:errors.extend(es)
 pg.close()
 for name in ['paper-foley-demo','ui-sound-demo','transition-sound-demo']:
  rel=f'compositions/{name}.html';pg=b.new_page(viewport={'width':640,'height':640});es=[];pg.on('pageerror',lambda e,es=es:es.append(str(e)));pg.set_content(bundle(root,rel),wait_until='load');pg.wait_for_timeout(80)
  dur=float(pg.locator('[data-composition-id]').get_attribute('data-duration'));blanks=[]
  for t in [0.1,dur*.25,dur*.5,dur*.75,dur-.1]:
   pg.evaluate('(t)=>window.seekComposition(t)',t);mx=pg.evaluate("Math.max(...[...document.querySelectorAll('.demo-scene')].map(x=>parseFloat(getComputedStyle(x).opacity)||0))")
   box=pg.locator('.audio-demo').bounding_box(); text=pg.locator('.demo-title').inner_text();
   if mx<.04 or not box or box['height']<100 or not text.strip():blanks.append(t)
  if blanks:errors.append(name+' blank frames '+str(blanks))
  if es:errors.extend(name+': '+x for x in es)
  details[name]={'duration':dur,'blankSamples':blanks};pg.close()
 b.close()
report={'status':'PASS' if not errors else 'FAIL','details':details,'errors':errors};(root/'reports/batch14-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
