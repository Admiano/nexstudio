from pathlib import Path
from playwright.sync_api import sync_playwright
from batch4_browser_utils import bundled_aspect_demo,bundled_icon_dock
import subprocess,shutil,json
root=Path(__file__).resolve().parents[1];raw_dir=root/'renders/playwright-batch4';shutil.rmtree(raw_dir,ignore_errors=True);raw_dir.mkdir(parents=True)
outputs=[]

def encode(src,dst,duration,scale=None,crf='20',preset='medium',fps=30):
    cmd=['ffmpeg','-y','-i',str(src),'-t',str(duration)]
    filters=[]
    if scale: filters.append(f'scale={scale}')
    filters.append(f'fps={fps}')
    cmd += ['-vf',','.join(filters),'-c:v','libx264','-preset',preset,'-crf',str(crf),'-pix_fmt','yuv420p','-movflags','+faststart',str(dst)]
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);outputs.append(str(dst))

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    # Exact aspect-ratio demonstration compositions.
    configs={'landscape':(1920,1080),'square':(1080,1080),'portrait':(1080,1920)}
    for ratio,(w,h) in configs.items():
        ctx=browser.new_context(viewport={'width':w,'height':h},record_video_dir=str(raw_dir),record_video_size={'width':w,'height':h});page=ctx.new_page();page.set_content(bundled_aspect_demo(root,ratio),wait_until='load');page.evaluate(f"window.__timelines['universal-icons-{ratio}'].restart()");page.wait_for_timeout(9100);video=page.video;ctx.close();raw=Path(video.path());dst=root/f'renders/universal-icons-{ratio}-standard.mp4';encode(raw,dst,8.7,crf='20',preset='medium',fps=30)
    # Full icon dock reel.
    ctx=browser.new_context(viewport={'width':1920,'height':1080},record_video_dir=str(raw_dir),record_video_size={'width':1920,'height':1080});page=ctx.new_page();page.set_content(bundled_icon_dock(root),wait_until='load');page.evaluate("window.__timelines['icon-dock-demo'].restart()");page.wait_for_timeout(19850);video=page.video;ctx.close();raw=Path(video.path());
    high=root/'renders/icon-dock-demo-high.mp4';standard=root/'renders/icon-dock-demo-standard.mp4';draft=root/'renders/icon-dock-demo-draft.mp4'
    encode(raw,high,19.4,crf='17',preset='medium',fps=30);encode(high,standard,19.4,scale='1280:-2',crf='24',preset='veryfast',fps=30);encode(high,draft,19.4,scale='854:-2',crf='30',preset='ultrafast',fps=24)
    browser.close()
report={'status':'PASS','aspectDuration':8.7,'dockDuration':19.4,'outputs':outputs,'rawDirectory':str(raw_dir)}
(root/'reports/batch4-render.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
