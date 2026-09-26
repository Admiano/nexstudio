from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
from batch15_browser_utils import bundle
root=Path(__file__).resolve().parents[1];reports=root/'reports';errors=[];data={}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage','--allow-file-access-from-files','--autoplay-policy=no-user-gesture-required'])
 page=b.new_page(viewport={'width':1600,'height':1000});page_errors=[];page.on('pageerror',lambda e:page_errors.append(str(e)))
 page.set_content(bundle(root,'master-explorer.html',strip_iframe=True),wait_until='load');page.wait_for_timeout(100);main_frame=page.frames[1] if len(page.frames)>1 else None
 if main_frame:main_frame.set_content(bundle(root,'master-preview.html'),wait_until='load')
 page.wait_for_timeout(400)
 data['inventoryText']=page.locator('.inventory-count strong').inner_text();data['firstPageCards']=page.locator('.asset-card').count();data['apiStatus']=page.locator('#apiResponse').inner_text()
 page.locator('#q').fill('paper swipe');page.wait_for_timeout(100);data['paperSwipeResults']=page.locator('.asset-card').count()
 page.locator('#q').fill('mobile phone');page.wait_for_timeout(100)
 if page.locator('.asset-card').count():page.locator('.asset-card').first.click()
 page.locator('#paperStyle').select_option('handmade-scrapbook');page.locator('#aspectRatio').select_option('9:16');page.locator('#copy').fill('Replaceable creator story');page.wait_for_timeout(100)
 data['selectedId']=page.locator('.detail .id').inner_text() if page.locator('.detail .id').count() else ''
 page.locator('#runApi').click();resp=page.locator('#apiResponse').inner_text();data['audioBlocked']='blocked-no-approved-audio' in resp
 page.screenshot(path=str(reports/'master-explorer.png'),full_page=True)
 if page_errors:errors.extend(page_errors)
 page.close()
 # preview runtime separately
 pg=b.new_page(viewport={'width':900,'height':600});pe=[];pg.on('pageerror',lambda e:pe.append(str(e)));pg.set_content(bundle(root,'master-preview.html'),wait_until='load');pg.wait_for_timeout(100)
 entry=json.loads((root/'manifests/master-agent-registry.json').read_text())['entries'];entry=next(x for x in entry if x['id']=='media.mobile-phone.paper-01')
 pg.evaluate('(x)=>render(x.entry,x.config)',{'entry':entry,'config':{'paperStyle':'handmade-scrapbook','motionEnergy':'medium','duration':2,'copy':'Replaceable creator story','media':(root/'assets/media/vertical-paper-demo.mp4').as_uri() if (root/'assets/media/vertical-paper-demo.mp4').exists() else (root/'assets/media/website-screenshot.svg').as_uri()}});pg.wait_for_timeout(250)
 data['previewChildren']=pg.locator('#mount > *').count();data['previewText']=pg.locator('#mount').inner_text()[:200]
 pg.screenshot(path=str(reports/'master-preview-mobile.png'))
 if data['previewChildren']==0:errors.append('preview empty')
 if pe:errors.extend(pe)
 pg.close();b.close()
if data.get('inventoryText')!='506':errors.append('inventory count mismatch')
if data.get('firstPageCards')!=60:errors.append('pagination mismatch')
if not data.get('audioBlocked'):errors.append('audio approval gate failed')
report={'status':'PASS' if not errors else 'FAIL','data':data,'errors':errors};(reports/'batch15-master-explorer-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
