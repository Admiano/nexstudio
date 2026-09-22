from pathlib import Path
import subprocess,json,sys,math,shutil
root=Path(__file__).resolve().parents[1];renders=root/'renders';reports=root/'reports';renders.mkdir(exist_ok=True)
schedules=json.loads((root/'manifests/audio-demo-schedules.json').read_text());audio={m['id']:m for m in json.loads((root/'manifests/audio-index.json').read_text())}

def probe(p):
 try:return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=index,codec_type,width,height,r_frame_rate,nb_frames,sample_rate,channels','-show_entries','format=duration','-of','json',str(p)],text=True))
 except Exception:return None

def render(name,duration,cw,ch,ow,oh,prefix,outname):
 frames=round(duration*30);parts=[]
 for start in range(0,frames,300):
  end=min(frames,start+300);part=Path(f'/tmp/{prefix}-{start}-{end}.avi');parts.append(part)
  if not part.exists():subprocess.run([sys.executable,str(root/'tests/render_audio_demo_chunk.py'),name,str(cw),str(ch),prefix,str(start),str(end)],check=True)
 lst=Path(f'/tmp/{prefix}-concat.txt');lst.write_text(''.join(f"file '{p}'\n" for p in parts));full=Path(f'/tmp/{prefix}-full.avi')
 subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(full)],check=True)
 visual=Path(f'/tmp/{prefix}-visual.mp4');subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(full),'-t',str(duration),'-vf',f'scale={ow}:{oh}:flags=lanczos,fps=30','-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(visual)],check=True)
 events=schedules[name];cmd=['ffmpeg','-y','-loglevel','error','-i',str(visual)];filters=[];labels=[]
 for i,e in enumerate(events,1):
  m=audio[e['audioId']];cmd += ['-i',str(root/m['productionFile'])];ms=max(0,round(e['start']*1000));lab=f'a{i}';filters.append(f'[{i}:a]adelay={ms}|{ms},volume={e["volume"]}[{lab}]');labels.append(f'[{lab}]')
 filters.append(''.join(labels)+f'amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=0.95,atrim=0:{duration}[mix]')
 out=renders/outname;cmd += ['-filter_complex',';'.join(filters),'-map','0:v:0','-map','[mix]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(duration),'-movflags','+faststart',str(out)];subprocess.run(cmd,check=True);return out

outs=[]
outs.append(render('paper-foley-demo',18,640,360,1920,1080,'b14paper','paper-foley-demo-high.mp4'))
outs.append(render('ui-sound-demo',15,540,540,1080,1080,'b14ui','ui-sound-demo-standard.mp4'))
outs.append(render('transition-sound-demo',18,270,480,1080,1920,'b14trans','transition-sound-demo-standard.mp4'))
# derivatives from paper high
for n,w,h,crf,fps in [('paper-foley-demo-standard.mp4',1280,720,23,30),('paper-foley-demo-draft.mp4',854,480,29,24)]:
 subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(outs[0]),'-vf',f'scale={w}:{h}:flags=lanczos,fps={fps}','-c:v','libx264','-preset','veryfast','-crf',str(crf),'-c:a','aac','-b:a','160k','-movflags','+faststart',str(renders/n)],check=True)
expected={'paper-foley-demo-high.mp4':(18,1920,1080),'paper-foley-demo-standard.mp4':(18,1280,720),'paper-foley-demo-draft.mp4':(18,854,480),'ui-sound-demo-standard.mp4':(15,1080,1080),'transition-sound-demo-standard.mp4':(18,1080,1920)};errors=[];info={}
for n,(dur,w,h) in expected.items():
 p=renders/n;d=probe(p);info[n]=d
 if not d:errors.append(n+' missing');continue
 if abs(float(d['format']['duration'])-dur)>.2:errors.append(n+' duration')
 streams=d['streams'];v=next((s for s in streams if s['codec_type']=='video'),{});a=next((s for s in streams if s['codec_type']=='audio'),None)
 if v.get('width')!=w or v.get('height')!=h or v.get('r_frame_rate') not in ('30/1','24/1'):errors.append(n+' video format')
 if not a or a.get('sample_rate')!='48000' or a.get('channels')!=2:errors.append(n+' audio stream')
report={'status':'PASS' if not errors else 'FAIL','outputs':info,'captureMethod':'deterministic 30 fps timeline frames; candidate effects mixed separately with FFmpeg','audioApproval':'candidate/editorial approval pending','errors':errors};(reports/'batch14-render.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
