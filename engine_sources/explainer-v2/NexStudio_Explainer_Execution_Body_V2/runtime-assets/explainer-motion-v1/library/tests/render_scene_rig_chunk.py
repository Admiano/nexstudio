from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess,sys,time
from batch13_browser_utils import bundle_scene
root=Path(__file__).resolve().parents[1]
name=sys.argv[1];w=int(sys.argv[2]);h=int(sys.argv[3]);prefix=sys.argv[4];chunk=int(sys.argv[5])
start=chunk*300;end=start+300;out=Path(f'/tmp/{prefix}-{chunk}.avi')
enc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-vcodec','mjpeg','-framerate','30','-i','-','-frames:v','300','-c:v','copy',str(out)],stdin=subprocess.PIPE)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage'])
 pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_scene(root,name),wait_until='load');pg.wait_for_timeout(80);pg.evaluate('(t)=>window.seekComposition(t)',start/30)
 for i in range(start,end):
  pg.evaluate('(t)=>window.seekComposition(t)',i/30);enc.stdin.write(pg.screenshot(type='jpeg',quality=64,animations='disabled'))
 b.close()
enc.stdin.close();sys.exit(enc.wait())
