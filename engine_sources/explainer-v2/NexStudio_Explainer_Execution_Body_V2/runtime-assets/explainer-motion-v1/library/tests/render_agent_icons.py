from pathlib import Path
from playwright.sync_api import sync_playwright
from batch6_browser_utils import bundled_agent_scene
import subprocess,shutil,json
root=Path(__file__).resolve().parents[1];raw=root/'renders/playwright-batch6';shutil.rmtree(raw,ignore_errors=True);raw.mkdir(parents=True);outputs=[];fallback=[]
def duration(path):
    out=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True).strip();return float(out)
def encode(src,dst,dur,scale=None,crf='20',preset='medium',fps=30):
    cmd=['ffmpeg','-y','-i',str(src),'-t',str(dur)];filters=[]
    if scale:filters.append(f'scale={scale}')
    filters.append(f'fps={fps}');cmd+=['-vf',','.join(filters),'-c:v','libx264','-preset',preset,'-crf',str(crf),'-pix_fmt','yuv420p','-movflags','+faststart',str(dst)];subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);outputs.append(str(dst))
def deterministic(browser,name,vp,dst,crf='19'):
    frames=raw/f'{name}-frames';shutil.rmtree(frames,ignore_errors=True);frames.mkdir();page=browser.new_page(viewport=vp);page.set_content(bundled_agent_scene(root,name),wait_until='load');fps=30;total=10.8;count=round(total*fps)
    for i in range(count):
        page.evaluate('(x)=>window.seekComposition(x)',i/fps);page.screenshot(path=str(frames/f'{i:05d}.png'))
    page.close();subprocess.run(['ffmpeg','-y','-framerate',str(fps),'-i',str(frames/'%05d.png'),'-c:v','libx264','-preset','medium','-crf',crf,'-pix_fmt','yuv420p','-movflags','+faststart',str(dst)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);outputs.append(str(dst));fallback.append(name)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    configs={'multi-agent-orchestration':(1920,1080),'human-agent-approval':(1080,1080),'prompt-to-output':(1080,1920)};masters={}
    for name,(w,h) in configs.items():
        ctx=b.new_context(viewport={'width':w,'height':h},record_video_dir=str(raw),record_video_size={'width':w,'height':h});page=ctx.new_page();page.set_content(bundled_agent_scene(root,name),wait_until='load');page.evaluate('(n)=>window.__timelines[n].restart()',name);page.wait_for_timeout(11250);video=page.video;ctx.close();src=Path(video.path());dst=root/f'renders/{name}-master.mp4';encode(src,dst,10.8,crf='18',preset='medium',fps=30)
        if duration(dst)<10.5:
            dst.unlink(missing_ok=True);outputs.remove(str(dst));deterministic(b,name,{'width':w,'height':h},dst,'18')
        masters[name]=dst
    b.close()
main=masters['multi-agent-orchestration'];high=root/'renders/multi-agent-orchestration-high.mp4';standard=root/'renders/multi-agent-orchestration-standard.mp4';draft=root/'renders/multi-agent-orchestration-draft.mp4'
shutil.copy2(main,high);outputs.append(str(high));encode(main,standard,10.8,scale='1280:-2',crf='23',preset='veryfast',fps=30);encode(main,draft,10.8,scale='854:-2',crf='29',preset='ultrafast',fps=24)
for name in ['human-agent-approval','prompt-to-output']:
    src=masters[name];dst=root/f'renders/{name}-standard.mp4';encode(src,dst,10.8,crf='21',preset='medium',fps=30)
report={'status':'PASS','duration':10.8,'outputs':outputs,'fallbackFrameRenders':fallback,'verifiedDurations':{Path(x).name:duration(Path(x)) for x in outputs if Path(x).exists()}}
(root/'reports/batch6-render.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
