from pathlib import Path
from playwright.sync_api import sync_playwright
from batch11_browser_utils import bundle_scene
import subprocess,shutil,json
root=Path(__file__).resolve().parents[1];raw=root/'renders/playwright-batch11';raw.mkdir(parents=True,exist_ok=True);renders=root/'renders';reports=root/'reports';D=12.0

def probe(p):
 if not p.exists():return None
 try:
  d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate','-show_entries','format=duration','-of','json',str(p)],text=True));s=d['streams'][0];return {'duration':float(d['format']['duration']),'width':int(s['width']),'height':int(s['height']),'fps':s['r_frame_rate']}
 except:return None

def valid(p,w,h,tol=.12):
 i=probe(p);return bool(i and abs(i['duration']-D)<=tol and i['width']==w and i['height']==h)

def record(browser,name,w,h):
 dst=raw/f'{name}.webm';i=probe(dst)
 if i and i['duration']>=D-.1:return dst
 ctx=browser.new_context(viewport={'width':w,'height':h},record_video_dir=str(raw),record_video_size={'width':w,'height':h});pg=ctx.new_page();pg.set_content(bundle_scene(root,name),wait_until='load');pg.wait_for_timeout(250);pg.evaluate('(n)=>window.__timelines[n].restart()',name);pg.wait_for_timeout(12550);v=pg.video;ctx.close();src=Path(v.path());
 if src!=dst:shutil.move(str(src),str(dst))
 return dst

def encode(src,dst,w,h,crf='21',preset='medium',fps=30):
 if valid(dst,w,h):return
 subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(src),'-t',str(D),'-vf',f'scale={w}:{h},fps={fps}','-c:v','libx264','-preset',preset,'-crf',str(crf),'-pix_fmt','yuv420p','-movflags','+faststart',str(dst)],check=True)
need1=not valid(renders/'creator-growth-recap-high.mp4',1920,1080);need2=not valid(renders/'sponsorship-announcement-standard.mp4',1080,1080);need3=not valid(renders/'publishing-workflow-standard.mp4',1080,1920)
s1=s2=s3=None
if need1 or need2 or need3:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
  if need1:s1=record(b,'creator-growth-recap',1280,720)
  if need2:s2=record(b,'sponsorship-announcement',720,720)
  if need3:s3=record(b,'publishing-workflow',540,960)
  b.close()
if need1:encode(s1,renders/'creator-growth-recap-high.mp4',1920,1080,'18')
encode(renders/'creator-growth-recap-high.mp4',renders/'creator-growth-recap-standard.mp4',1280,720,'23','veryfast')
encode(renders/'creator-growth-recap-high.mp4',renders/'creator-growth-recap-draft.mp4',854,480,'29','ultrafast',24)
if need2:encode(s2,renders/'sponsorship-announcement-standard.mp4',1080,1080,'21')
if need3:encode(s3,renders/'publishing-workflow-standard.mp4',1080,1920,'21')
outs={'creator-growth-recap-high.mp4':(1920,1080),'creator-growth-recap-standard.mp4':(1280,720),'creator-growth-recap-draft.mp4':(854,480),'sponsorship-announcement-standard.mp4':(1080,1080),'publishing-workflow-standard.mp4':(1080,1920)}
details={n:probe(renders/n) for n in outs};errors=[n for n,(w,h) in outs.items() if not valid(renders/n,w,h)]
for n in ['creator-growth-recap-high.mp4','sponsorship-announcement-standard.mp4','publishing-workflow-standard.mp4']:
 subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','11.3','-i',str(renders/n),'-frames:v','1',str(reports/(n.replace('.mp4','-late.png')))],check=True)
report={'status':'PASS' if not errors else 'FAIL','duration':D,'outputs':details,'sourceCompositions':{'creator-growth-recap':'1920x1080','sponsorship-announcement':'1080x1080','publishing-workflow':'1080x1920'},'captureNotes':{'creator-growth-recap':'1280x720 capture encoded to 1920x1080','sponsorship-announcement':'720x720 capture encoded to 1080x1080','publishing-workflow':'540x960 capture encoded to 1080x1920'},'lateFramesVerified':3,'errors':errors}
(reports/'batch11-render.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(1 if errors else 0)
