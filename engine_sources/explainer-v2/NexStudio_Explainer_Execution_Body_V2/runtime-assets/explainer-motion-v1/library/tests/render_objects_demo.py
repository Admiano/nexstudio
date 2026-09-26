from pathlib import Path
from playwright.sync_api import sync_playwright
from batch2_browser_utils import bundled_object_composition
import subprocess,shutil,json
root=Path(__file__).resolve().parents[1];html=bundled_object_composition(root);video_dir=root/'renders/playwright-batch2';shutil.rmtree(video_dir,ignore_errors=True);video_dir.mkdir(parents=True)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');ctx=b.new_context(viewport={'width':1920,'height':1080},record_video_dir=str(video_dir),record_video_size={'width':1920,'height':1080});page=ctx.new_page();page.set_content(html,wait_until='load');page.evaluate("window.__timelines['paper-objects-demo'].restart()");page.wait_for_timeout(20200);video=page.video;ctx.close();b.close();raw=Path(video.path())
high=root/'renders/paper-objects-demo-high.mp4';standard=root/'renders/paper-objects-demo-standard.mp4';draft=root/'renders/paper-objects-demo-draft.mp4'
subprocess.run(['ffmpeg','-y','-i',str(raw),'-vf','fps=30','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(high)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg','-y','-i',str(high),'-vf','scale=1280:-2,fps=30','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(standard)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg','-y','-i',str(high),'-vf','scale=854:-2,fps=24','-c:v','libx264','-preset','ultrafast','-crf','30','-pix_fmt','yuv420p','-movflags','+faststart',str(draft)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
report={'status':'PASS','duration':20,'outputs':[str(high),str(standard),str(draft)],'raw':str(raw)};(root/'reports/batch2-render.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
