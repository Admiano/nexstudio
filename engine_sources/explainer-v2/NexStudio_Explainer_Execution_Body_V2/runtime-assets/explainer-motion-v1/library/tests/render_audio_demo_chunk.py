from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess,sys
from batch14_browser_utils import bundle
root=Path(__file__).resolve().parents[1]
name=sys.argv[1];w=int(sys.argv[2]);h=int(sys.argv[3]);prefix=sys.argv[4];start=int(sys.argv[5]);end=int(sys.argv[6]);frames=end-start
out=Path(f'/tmp/{prefix}-{start}-{end}.avi')
enc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-vcodec','mjpeg','-framerate','30','-i','-','-frames:v',str(frames),'-c:v','copy',str(out)],stdin=subprocess.PIPE)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage','--allow-file-access-from-files'])
 pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle(root,f'compositions/{name}.html'),wait_until='load');pg.wait_for_timeout(60)
 for i in range(start,end):
  pg.evaluate('(t)=>window.seekComposition(t)',i/30);enc.stdin.write(pg.screenshot(type='jpeg',quality=72,animations='disabled'))
 b.close()
enc.stdin.close();sys.exit(enc.wait())
