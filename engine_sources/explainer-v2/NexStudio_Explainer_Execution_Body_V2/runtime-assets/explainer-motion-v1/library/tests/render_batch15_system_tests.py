from pathlib import Path
import subprocess,json,sys
root=Path(__file__).resolve().parents[1];renders=root/'renders';reports=root/'reports';renders.mkdir(exist_ok=True)
audio={m['id']:m for m in json.loads((root/'manifests/audio-index.json').read_text())}
schedules=json.loads((root/'manifests/final-system-test-audio-schedules.json').read_text())
films={
 'final-creator-system-test':('creator-explainer-high.mp4','final-creator-system-test-provisional-audio.mp4',1920,1080),
 'final-agent-system-test':('agent-workflow-film-standard.mp4','final-agent-system-test-provisional-audio.mp4',1080,1080),
 'final-documentary-system-test':('documentary-scrapbook-film-standard.mp4','final-documentary-system-test-provisional-audio.mp4',1080,1920),
}
def run(cmd):subprocess.run(cmd,check=True)
def probe(path):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=index,codec_type,width,height,r_frame_rate,sample_rate,channels','-show_entries','format=duration','-of','json',str(path)],text=True))
outputs={};errors=[]
for key,(visual_name,out_name,w,h) in films.items():
 visual=renders/visual_name;out=renders/out_name
 if not visual.exists():errors.append(f'{visual_name} missing');continue
 cmd=['ffmpeg','-y','-loglevel','error','-i',str(visual)]
 filters=[];labels=[]
 # quiet room tone loop candidate bed
 room=audio['audio.room-tone-neutral-loop'];cmd+=['-stream_loop','-1','-i',str(root/room['productionFile'])]
 filters.append('[1:a]atrim=0:60,volume=0.055,afade=t=in:st=0:d=1,afade=t=out:st=58.5:d=1.5[bed]');labels.append('[bed]')
 for i,e in enumerate(schedules[key],start=2):
  m=audio[e['audioId']];cmd+=['-i',str(root/m['productionFile'])];ms=max(0,round(e['start']*1000));lab=f'a{i}'
  filters.append(f'[{i}:a]adelay={ms}|{ms},volume={e["volume"]},aformat=sample_rates=48000:channel_layouts=stereo[{lab}]');labels.append(f'[{lab}]')
 filters.append(''.join(labels)+f'amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=0.93,atrim=0:60[mix]')
 cmd += ['-filter_complex',';'.join(filters),'-map','0:v:0','-map','[mix]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t','60','-metadata','comment=PROVISIONAL CANDIDATE AUDIO - EDITORIAL APPROVAL PENDING','-movflags','+faststart',str(out)]
 run(cmd)
 d=probe(out);outputs[out_name]=d
 dur=float(d['format']['duration']);v=next((s for s in d['streams'] if s['codec_type']=='video'),{});a=next((s for s in d['streams'] if s['codec_type']=='audio'),{})
 if abs(dur-60)>.15 or v.get('width')!=w or v.get('height')!=h or a.get('sample_rate')!='48000' or a.get('channels')!=2:errors.append(out_name+' invalid')
report={'status':'PASS' if not errors else 'FAIL','audioApproval':'PROVISIONAL_CANDIDATE_ONLY','productionReady':False,'outputs':outputs,'voiceoverTimingPlaceholders':[f'assets/voiceover/{k}.json' for k in films],'errors':errors}
(reports/'batch15-render.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
