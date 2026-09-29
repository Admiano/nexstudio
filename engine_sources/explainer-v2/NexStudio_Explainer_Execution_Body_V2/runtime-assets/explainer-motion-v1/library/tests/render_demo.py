from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_utils import bundled_composition
import subprocess, shutil, json, time
root=Path(__file__).resolve().parents[1]
html=bundled_composition(root)
video_dir=root/'renders/playwright'; shutil.rmtree(video_dir,ignore_errors=True);video_dir.mkdir(parents=True)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 context=browser.new_context(viewport={'width':1920,'height':1080},record_video_dir=str(video_dir),record_video_size={'width':1920,'height':1080})
 page=context.new_page(); page.set_content(html,wait_until='load')
 page.evaluate("document.querySelector('[data-composition-id]').dataset.ratio='landscape'; window.__timelines['foundation-demo'].restart()")
 page.wait_for_timeout(16600)
 video=page.video
 context.close(); browser.close()
 raw=Path(video.path())
out=root/'renders/foundation-demo-high.mp4'
subprocess.run(['ffmpeg','-y','-i',str(raw),'-vf','fps=30','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg','-y','-i',str(out),'-vf','scale=1280:-2,fps=30','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(root/'renders/foundation-demo-standard.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg','-y','-i',str(out),'-vf','scale=854:-2,fps=24','-c:v','libx264','-preset','ultrafast','-crf','30','-pix_fmt','yuv420p','-movflags','+faststart',str(root/'renders/foundation-demo-draft.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'duration':16,'outputs':[str(out),str(root/'renders/foundation-demo-standard.mp4'),str(root/'renders/foundation-demo-draft.mp4')],'raw':str(raw)},indent=2))
