from pathlib import Path
from playwright.sync_api import sync_playwright
from batch6_browser_utils import bundled_agent_scene
import subprocess,shutil,sys
root=Path(__file__).resolve().parents[1]
name=sys.argv[1];w=int(sys.argv[2]);h=int(sys.argv[3]);raw=root/f'renders/capture-{name}';shutil.rmtree(raw,ignore_errors=True);raw.mkdir(parents=True)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');ctx=b.new_context(viewport={'width':w,'height':h},record_video_dir=str(raw),record_video_size={'width':w,'height':h});page=ctx.new_page();page.set_content(bundled_agent_scene(root,name),wait_until='load');page.evaluate('(n)=>window.__timelines[n].restart()',name);page.wait_for_timeout(11250);video=page.video;ctx.close();src=Path(video.path());b.close()
dst=root/f'renders/{name}-master.mp4';subprocess.run(['ffmpeg','-y','-i',str(src),'-t','10.8','-vf','fps=30','-c:v','libx264','-preset','ultrafast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(dst)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);print(dst)
