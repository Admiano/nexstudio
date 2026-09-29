from pathlib import Path
from playwright.sync_api import sync_playwright
from batch6_browser_utils import bundled_agent_scene
import subprocess,json,shutil
root=Path(__file__).resolve().parents[1];raw=root/'renders/playwright-batch6-missing';shutil.rmtree(raw,ignore_errors=True);raw.mkdir(parents=True)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 ctx=b.new_context(viewport={'width':1080,'height':1920},record_video_dir=str(raw),record_video_size={'width':1080,'height':1920})
 page=ctx.new_page();page.set_content(bundled_agent_scene(root,'prompt-to-output'),wait_until='load');page.evaluate("window.__timelines['prompt-to-output'].restart()");page.wait_for_timeout(11250);video=page.video;ctx.close();src=Path(video.path());b.close()
dst=root/'renders/prompt-to-output-master.mp4'
subprocess.run(['ffmpeg','-y','-i',str(src),'-t','10.8','-vf','fps=30','-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(dst)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(dst)
