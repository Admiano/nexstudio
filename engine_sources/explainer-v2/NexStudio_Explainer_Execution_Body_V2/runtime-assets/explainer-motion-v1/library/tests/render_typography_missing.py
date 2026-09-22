from pathlib import Path
from playwright.sync_api import sync_playwright
from batch8_browser_utils import bundle
import subprocess,shutil,json
root=Path(__file__).resolve().parents[1];base=root/'renders/batch8-frames';shutil.rmtree(base,ignore_errors=True);base.mkdir(parents=True)
def render_frames(browser,rel,name,w,h,out):
 d=base/name;d.mkdir();page=browser.new_page(viewport={'width':w,'height':h});page.set_content(bundle(root,rel),wait_until='load');fps=15;frames=8*fps
 for i in range(frames):
  t=i/fps;page.evaluate('''([n,t])=>window.__timelines[n].seek(t)''',[name,t]);page.screenshot(path=str(d/f'{i:04d}.jpg'),type='jpeg',quality=88)
 page.close();subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(fps),'-i',str(d/'%04d.jpg'),'-vf','minterpolate=fps=30:mi_mode=blend','-t','8','-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 render_frames(b,'compositions/typography-square.html','typography-square',1080,1080,root/'renders/typography-square-standard.mp4')
 render_frames(b,'compositions/typography-portrait.html','typography-portrait',1080,1920,root/'renders/typography-portrait-standard.mp4')
 b.close()
print('PASS')
