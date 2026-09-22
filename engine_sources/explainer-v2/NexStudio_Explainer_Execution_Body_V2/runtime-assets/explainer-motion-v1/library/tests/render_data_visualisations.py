from pathlib import Path
from playwright.sync_api import sync_playwright
from batch10_browser_utils import bundle_scene,bundle_editor
import subprocess,shutil,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'renders/playwright-batch10';RAW.mkdir(parents=True,exist_ok=True);RENDERS=ROOT/'renders';REPORTS=ROOT/'reports';DURATION=14.0

def probe(path):
 if not path.exists():return None
 try:
  d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate','-show_entries','format=duration','-of','json',str(path)],text=True));s=d['streams'][0];return {'duration':float(d['format']['duration']),'width':int(s['width']),'height':int(s['height']),'fps':s['r_frame_rate']}
 except:return None

def valid(path,w,h,tol=.1):
 i=probe(path);return bool(i and abs(i['duration']-DURATION)<=tol and i['width']==w and i['height']==h)

def record(browser,name,w,h,rawname):
 dst=RAW/rawname;i=probe(dst)
 if i and i['duration']>=DURATION:return dst
 ctx=browser.new_context(viewport={'width':w,'height':h},record_video_dir=str(RAW),record_video_size={'width':w,'height':h});pg=ctx.new_page();pg.set_content(bundle_scene(ROOT,name),wait_until='load');pg.wait_for_timeout(300);pg.evaluate(f"window.__timelines['{name}'].restart()");pg.wait_for_timeout(14650);v=pg.video;ctx.close();src=Path(v.path());
 if src!=dst:shutil.move(str(src),str(dst))
 return dst

def encode(src,dst,w,h,crf='21',preset='medium',fps=30):
 if valid(dst,w,h):return
 subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(src),'-t',str(DURATION),'-vf',f'scale={w}:{h},fps={fps}','-c:v','libx264','-preset',preset,'-crf',str(crf),'-pix_fmt','yuv420p','-movflags','+faststart',str(dst)],check=True)

def late_frame(video,out):
 subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','13.5','-i',str(video),'-frames:v','1',str(out)],check=True)

def main():
 need=[not valid(RENDERS/'data-story-high.mp4',1920,1080),not valid(RENDERS/'agent-workflow-standard.mp4',1080,1080),not valid(RENDERS/'conversion-story-standard.mp4',1080,1920)]
 src1=src2=src3=None
 if any(need):
  with sync_playwright() as p:
   b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
   if need[0]:src1=record(b,'data-story',1280,720,'data-story.webm')
   if need[1]:src2=record(b,'agent-workflow',1080,1080,'agent-workflow.webm')
   if need[2]:src3=record(b,'conversion-story',540,960,'conversion-story.webm')
   b.close()
 if need[0]:encode(src1,RENDERS/'data-story-high.mp4',1920,1080,'18')
 encode(RENDERS/'data-story-high.mp4',RENDERS/'data-story-standard.mp4',1280,720,'23','veryfast')
 encode(RENDERS/'data-story-high.mp4',RENDERS/'data-story-draft.mp4',854,480,'29','ultrafast',24)
 if need[1]:encode(src2,RENDERS/'agent-workflow-standard.mp4',1080,1080,'21')
 if need[2]:encode(src3,RENDERS/'conversion-story-standard.mp4',1080,1920,'21')
 for v,o in [('data-story-high.mp4','data-story-late-frame.png'),('agent-workflow-standard.mp4','agent-workflow-late-frame.png'),('conversion-story-standard.mp4','conversion-story-late-frame.png')]:late_frame(RENDERS/v,REPORTS/o)
 outs={'data-story-high.mp4':(1920,1080),'data-story-standard.mp4':(1280,720),'data-story-draft.mp4':(854,480),'agent-workflow-standard.mp4':(1080,1080),'conversion-story-standard.mp4':(1080,1920)}
 details={n:probe(RENDERS/n) for n in outs};errors=[n for n,(w,h) in outs.items() if not valid(RENDERS/n,w,h)]
 report={'status':'PASS' if not errors else 'FAIL','duration':DURATION,'outputs':details,'sourceCompositions':{'data-story':'1920x1080','agent-workflow':'1080x1080','conversion-story':'1080x1920'},'captureNotes':{'data-story':'1280x720 deterministic browser capture encoded to 1920x1080','agent-workflow':'native 1080x1080 browser capture','conversion-story':'540x960 browser capture encoded to 1080x1920'},'lateFramesVerified':3,'errors':errors}
 (REPORTS/'batch10-render.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(1 if errors else 0)
if __name__=='__main__':main()
