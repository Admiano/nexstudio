from pathlib import Path
from playwright.sync_api import sync_playwright
from batch14_browser_utils import bundle
import subprocess
root=Path(__file__).resolve().parents[1];reports=root/'reports'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage','--allow-file-access-from-files'])
 pg=b.new_page(viewport={'width':1440,'height':1000});pg.set_content(bundle(root,'sound-audition.html'),wait_until='load');pg.wait_for_timeout(500);pg.screenshot(path=str(reports/'sound-audition.png'),full_page=True);pg.close()
 for name,size,t in [('paper-foley-demo',(1280,720),13.5),('ui-sound-demo',(900,900),9.2),('transition-sound-demo',(540,960),15.9)]:
  pg=b.new_page(viewport={'width':size[0],'height':size[1]});pg.set_content(bundle(root,f'compositions/{name}.html'),wait_until='load');pg.evaluate('(t)=>window.seekComposition(t)',t);pg.screenshot(path=str(reports/(name+'.png')));pg.close()
 b.close()
subprocess.run(['/opt/imagemagick/bin/montage',str(reports/'paper-foley-demo.png'),str(reports/'ui-sound-demo.png'),str(reports/'transition-sound-demo.png'),'-thumbnail','520x520','-background','#eee4cf','-gravity','center','-extent','540x540','-tile','3x1','-geometry','+18+18',str(reports/'batch14-montage.png')],check=True)
