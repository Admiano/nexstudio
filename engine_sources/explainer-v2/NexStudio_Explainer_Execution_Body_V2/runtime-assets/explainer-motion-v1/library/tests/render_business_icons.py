from pathlib import Path
from playwright.sync_api import sync_playwright
from batch7_browser_utils import bundled_business_scene
import subprocess,shutil,json
root=Path(__file__).resolve().parents[1]
raw=root/'renders/playwright-batch7';shutil.rmtree(raw,ignore_errors=True);raw.mkdir(parents=True)
outputs=[]
def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True).strip())
def encode(src,dst,dur=10.8,scale=None,crf='20',preset='medium',fps=30):
    filters=[]
    if scale:filters.append(f'scale={scale}')
    filters.append(f'fps={fps}')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(src),'-t',str(dur),'-vf',','.join(filters),'-c:v','libx264','-preset',preset,'-crf',str(crf),'-pix_fmt','yuv420p','-movflags','+faststart',str(dst)],check=True);outputs.append(str(dst))
def record(browser,name,w,h,record_w=None,record_h=None):
    rw,rh=record_w or w,record_h or h
    ctx=browser.new_context(viewport={'width':rw,'height':rh},record_video_dir=str(raw),record_video_size={'width':rw,'height':rh})
    page=ctx.new_page();page.set_content(bundled_business_scene(root,name),wait_until='load');page.evaluate('(n)=>window.__timelines[n].restart()',name);page.wait_for_timeout(11250);video=page.video;ctx.close();return Path(video.path())
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    commerce_src=record(browser,'commerce-workflow',1920,1080)
    campaign_src=record(browser,'campaign-result',1080,1080)
    # Lower-resolution browser capture avoids Chromium video-capture stalls at native portrait size.
    # The HTML source and layout tests remain native 1080x1920.
    milestone_src=record(browser,'milestone-scene',1080,1920,720,1280)
    browser.close()
masters={
 'commerce-workflow':root/'renders/commerce-workflow-master.mp4',
 'campaign-result':root/'renders/campaign-result-master.mp4',
 'milestone-scene':root/'renders/milestone-scene-master.mp4',
}
encode(commerce_src,masters['commerce-workflow'],crf='18')
encode(campaign_src,masters['campaign-result'],crf='18')
encode(milestone_src,masters['milestone-scene'],scale='1080:1920',crf='18')
shutil.copy2(masters['commerce-workflow'],root/'renders/commerce-workflow-high.mp4');outputs.append(str(root/'renders/commerce-workflow-high.mp4'))
encode(masters['commerce-workflow'],root/'renders/commerce-workflow-standard.mp4',scale='1280:-2',crf='23',preset='veryfast')
encode(masters['commerce-workflow'],root/'renders/commerce-workflow-draft.mp4',scale='854:-2',crf='29',preset='ultrafast',fps=24)
encode(masters['campaign-result'],root/'renders/campaign-result-standard.mp4',crf='21')
encode(masters['milestone-scene'],root/'renders/milestone-scene-standard.mp4',crf='21')
report={'status':'PASS','duration':10.8,'outputs':outputs,'portraitCapture':'Native 1080x1920 source and layout; 720x1280 browser capture upscaled to 1080x1920 for the MP4.','verifiedDurations':{Path(x).name:duration(Path(x)) for x in outputs}}
(root/'reports/batch7-render.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
