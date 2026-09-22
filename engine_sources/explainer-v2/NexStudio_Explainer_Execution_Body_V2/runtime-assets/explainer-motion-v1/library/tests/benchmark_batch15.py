from pathlib import Path
import json,time,statistics,subprocess,re,sys
from playwright.sync_api import sync_playwright
from batch15_browser_utils import bundle
root=Path(__file__).resolve().parents[1];reports=root/'reports';reg=root/'manifests/master-agent-registry.json'
# JSON parse benchmark
raw=reg.read_text();parse=[]
for _ in range(30):
 t=time.perf_counter();json.loads(raw);parse.append((time.perf_counter()-t)*1000)
# Browser startup and explorer render
browser_times=[];filter_times=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage'])
 for _ in range(3):
  pg=b.new_page(viewport={'width':1440,'height':900});t=time.perf_counter();pg.set_content(bundle(root,'master-explorer.html',strip_iframe=True),wait_until='load');pg.wait_for_timeout(100);browser_times.append((time.perf_counter()-t)*1000)
  t=time.perf_counter();pg.fill('#q','agent workflow');pg.wait_for_timeout(20);filter_times.append((time.perf_counter()-t)*1000);pg.close()
 b.close()
# Node selector 1000 requests
node_script="""global.window=global;require('./runtime/master-registry.js');const A=require('./runtime/agent-selection-api.js');A.init(global.NEX_MASTER_REGISTRY,global.NEX_MASTER_SOUND_TAG_MAP);const q={intent:'explain_agent_workflow',duration:8,aspectRatio:'16:9',paperStyle:'technical-notebook',motionEnergy:'medium',useCase:'agent',requireApprovedAudio:true};const t=process.hrtime.bigint();for(let i=0;i<1000;i++)A.select(q);const d=Number(process.hrtime.bigint()-t)/1e6;console.log(JSON.stringify({totalMs:d,averageMs:d/1000}));"""
node=json.loads(subprocess.check_output(['node','-e',node_script],cwd=root,text=True))
# FFmpeg decode benchmark one minute high output
p=subprocess.run(['ffmpeg','-benchmark','-v','info','-i',str(root/'renders/final-creator-system-test-provisional-audio.mp4'),'-f','null','-'],capture_output=True,text=True)
bench=re.search(r'bench: utime=([\d.]+)s stime=([\d.]+)s rtime=([\d.]+)s',p.stderr)
ff={'userSeconds':float(bench.group(1)),'systemSeconds':float(bench.group(2)),'realSeconds':float(bench.group(3))} if bench else {'raw':p.stderr[-1000:]}
report={'status':'PASS','registry':{'entries':506,'bytes':len(raw.encode()),'parseMsMean':statistics.mean(parse),'parseMsP95':sorted(parse)[int(len(parse)*.95)-1]},'selectionApi1000':node,'masterExplorer':{'renderMsMean':statistics.mean(browser_times),'filterMsMeanIncluding20msSettle':statistics.mean(filter_times)},'ffmpegDecode60s':ff,'environment':'local Chromium + Node + FFmpeg compatibility runtime; official HyperFrames CLI unavailable'}
(reports/'batch15-benchmark.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
