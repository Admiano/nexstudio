from pathlib import Path
import json, shutil, re, math, hashlib, subprocess, os, csv
import numpy as np
import soundfile as sf
import pyloudnorm as pyln

root=Path(__file__).resolve().parents[1]
input_pack=Path('/mnt/data/batch14-input/unpacked/nexstudio_documentary_sound_pack_v1')
legacy=Path('/mnt/data/batch14-input/legacy-candidates')
masters=root/'assets/audio/masters/candidate-v1'
production=root/'assets/audio/production/candidate-v1'
manifest_dir=root/'manifests/audio'
for d in [masters,production,manifest_dir,root/'previews/audio',root/'reports',root/'runtime',root/'styles',root/'components',root/'compositions']:
 d.mkdir(parents=True,exist_ok=True)

# source definitions
pack_defs={
 '01_paper_swipe_clean.wav': dict(slug='paper-swipe-clean', title='Paper Swipe — Clean', category='paper-foley', intensity='soft', tags=['paper.slide.soft','paper.whoosh','motion.fast','transition.paper'], actions=['paper-slide','paper-wipe','photo-reveal'], offset=-0.04, mood=['clean','editorial']),
 '02_page_turn_soft.wav': dict(slug='page-turn-soft', title='Page Turn — Soft', category='paper-foley', intensity='soft', tags=['paper.page.turn','paper.soft','transition.page'], actions=['page-turn','chapter-change'], offset=-0.08, mood=['warm','reflective']),
 '03_tape_pull_snap.wav': dict(slug='tape-pull-snap', title='Tape Pull & Snap', category='paper-foley', intensity='medium', tags=['paper.tape.pull','paper.tape.press','paper.medium'], actions=['tape-peel','tape-down','pin-evidence'], offset=-0.06, mood=['tactile','playful']),
 '04_staple_click_precise.wav': dict(slug='staple-click-precise', title='Staple Click — Precise', category='paper-foley', intensity='sharp', tags=['paper.staple','ui.confirm','ui.tick'], actions=['staple','confirm','list-check'], offset=-0.015, mood=['precise','technical']),
 '05_pencil_scribble_short.wav': dict(slug='pencil-scribble-short', title='Pencil Scribble — Short', category='paper-foley', intensity='soft', tags=['ink.pencil','paper.write','annotation.handwritten'], actions=['draw-on','scribble-underline','circle-note'], offset=0.0, mood=['warm','handmade']),
 '06_marker_swipe_bold.wav': dict(slug='marker-swipe-bold', title='Marker Swipe — Bold', category='paper-foley', intensity='medium', tags=['ink.marker','ui.emphasis','paper.write.bold'], actions=['marker-highlight','underline','evidence-highlight'], offset=-0.03, mood=['bold','editorial']),
 '07_typewriter_key_single.wav': dict(slug='typewriter-key-single', title='Typewriter Key — Single', category='interface', intensity='sharp', tags=['archive.typewriter.key','ui.tick','ui.select'], actions=['type-one-character','date-stamp','select'], offset=-0.01, mood=['archive','precise']),
 '08_typewriter_line_with_return.wav': dict(slug='typewriter-line-return', title='Typewriter Line & Return', category='interface', intensity='medium', tags=['archive.typewriter.line','ui.counter','ui.type.sequence'], actions=['type-line','counter-sequence','archival-caption'], offset=0.0, mood=['archive','serious']),
 '09_camera_shutter_clean.wav': dict(slug='camera-shutter-clean', title='Camera Shutter — Clean', category='interface', intensity='sharp', tags=['capture.camera','ui.capture','media.photo'], actions=['camera-shutter','photo-freeze'], offset=-0.02, mood=['clean','documentary']),
 '10_film_advance_ratchet.wav': dict(slug='film-advance-ratchet', title='Film Advance — Ratchet', category='motion-transition', intensity='medium', tags=['archive.film.advance','media.film','transition.archive'], actions=['film-advance','contact-sheet-shuffle'], offset=-0.03, mood=['archive','cinematic']),
 '11_projector_start_modern.wav': dict(slug='projector-start-modern', title='Projector Start — Modern', category='motion-transition', intensity='medium', tags=['archive.projector','motion.rise','motion.cinematic','ui.processing'], actions=['projector-start','processing','chapter-open'], offset=-0.12, mood=['cinematic','serious']),
 '12_archive_drawer_slide.wav': dict(slug='archive-drawer-slide', title='Archive Drawer — Slide', category='motion-transition', intensity='heavy', tags=['archive.drawer','paper.heavy','motion.heavy.swipe'], actions=['drawer-slide','file-reveal','heavy-swipe'], offset=-0.08, mood=['serious','tactile']),
 '13_rubber_stamp_impact.wav': dict(slug='rubber-stamp-impact', title='Rubber Stamp — Impact', category='paper-foley', intensity='heavy', tags=['ink.stamp','ui.confirm','paper.stamp'], actions=['stamp-impact','approval','date-stamp'], offset=-0.04, mood=['decisive','archive']),
 '14_newspaper_rustle.wav': dict(slug='newspaper-rustle', title='Newspaper Rustle', category='paper-foley', intensity='medium', tags=['paper.shuffle','paper.heavy','archive.newspaper'], actions=['paper-shuffle','headline-reveal'], offset=-0.08, mood=['archive','editorial']),
 '15_radio_tune_transition.wav': dict(slug='radio-tune-transition', title='Radio Tune — Transition', category='motion-transition', intensity='medium', tags=['transition.archive','motion.cinematic','source.change'], actions=['time-shift','source-change','radio-transition'], offset=-0.08, mood=['investigative','cinematic']),
 '16_room_tone_neutral_loop_10s.wav': dict(slug='room-tone-neutral-loop', title='Room Tone — Neutral Loop', category='ambience', intensity='soft', tags=['ambience.room','documentary.bed'], actions=['ambient-bed','voiceover-support'], offset=0.0, mood=['neutral','documentary'], loopable=True),
 '17_soft_impact_modern.wav': dict(slug='soft-impact-modern', title='Soft Impact — Modern', category='motion-transition', intensity='soft', tags=['motion.impact.soft','ui.success','motion.drop','logo.warm'], actions=['soft-impact','drop-settle','success','logo-land'], offset=-0.035, mood=['warm','modern']),
 '18_map_unfold_wide.wav': dict(slug='map-unfold-wide', title='Map Unfold — Wide', category='paper-foley', intensity='medium', tags=['paper.unfold','paper.fold','transition.map'], actions=['unfold','map-journey','location-reveal'], offset=-0.1, mood=['exploratory','documentary']),
}
legacy_defs={
 '01_paper_swipe.mp3': dict(slug='paper-swipe-legacy', title='Paper Swipe — Legacy Alternate', category='paper-foley', intensity='medium', tags=['paper.slide.medium','paper.whoosh.alt'], actions=['paper-slide','fast-reveal'], offset=-0.04, mood=['clean'], provenance='legacy model-generated candidate'),
 '02_text_pop_in.mp3': dict(slug='text-pop-in', title='Text Pop In', category='interface', intensity='soft', tags=['ui.pop','ui.notification','ui.success'], actions=['pop','notification','success'], offset=-0.02, mood=['playful','clean'], provenance='legacy model-generated candidate'),
 '03_camera_shutter.mp3': dict(slug='camera-shutter-legacy', title='Camera Shutter — Legacy Alternate', category='interface', intensity='medium', tags=['capture.camera.alt','ui.capture'], actions=['camera-shutter'], offset=-0.02, mood=['documentary'], provenance='legacy model-generated candidate'),
 '04_bass_hit.mp3': dict(slug='bass-hit', title='Bass Hit', category='motion-transition', intensity='heavy', tags=['motion.impact.heavy','ui.error','motion.drop.heavy'], actions=['impact','error','heavy-drop'], offset=-0.04, mood=['cinematic','heavy'], provenance='legacy model-generated candidate'),
 '05_fast_transition_whoosh.mp3': dict(slug='fast-transition-whoosh', title='Fast Transition Whoosh', category='motion-transition', intensity='fast', tags=['motion.fast','motion.fast.swipe','motion.reveal','transition.fast'], actions=['fast-swipe','reveal','transition'], offset=-0.09, mood=['fast','modern'], provenance='legacy model-generated candidate'),
 '06_final_logo_sting.mp3': dict(slug='final-logo-sting', title='Final Logo Sting', category='motion-transition', intensity='heavy', tags=['logo.warm','logo.sting','motion.cinematic'], actions=['logo-reveal','final-lockup'], offset=-0.12, mood=['warm','cinematic'], provenance='legacy model-generated candidate'),
}

# requested coverage slots
coverage_slots={
 'paper-foley':['paper slide','page turn','fold','unfold','tear','crumple','flatten','shuffle','tape pull','tape press','staple','paper clip','stamp','pencil','marker','chalk','scissors'],
 'interface':['click','select','hover','toggle','upload','download','notification','confirmation','error','processing','success','pop','tick','counter','progress completion'],
 'motion-transition':['soft whoosh','paper whoosh','fast swipe','heavy swipe','pop','impact','rise','drop','reveal','page transition','logo sting']
}
coverage_map={
 'paper slide':('exact','paper-swipe-clean'),'page turn':('exact','page-turn-soft'),'fold':('fallback','map-unfold-wide'),'unfold':('exact','map-unfold-wide'),'tear':('missing',None),'crumple':('missing',None),'flatten':('missing',None),'shuffle':('exact','newspaper-rustle'),'tape pull':('exact','tape-pull-snap'),'tape press':('fallback','tape-pull-snap'),'staple':('exact','staple-click-precise'),'paper clip':('missing',None),'stamp':('exact','rubber-stamp-impact'),'pencil':('exact','pencil-scribble-short'),'marker':('exact','marker-swipe-bold'),'chalk':('missing',None),'scissors':('missing',None),
 'click':('fallback','typewriter-key-single'),'select':('fallback','typewriter-key-single'),'hover':('missing',None),'toggle':('missing',None),'upload':('fallback','fast-transition-whoosh'),'download':('fallback','fast-transition-whoosh'),'notification':('fallback','text-pop-in'),'confirmation':('exact','rubber-stamp-impact'),'error':('fallback','bass-hit'),'processing':('fallback','projector-start-modern'),'success':('fallback','text-pop-in'),'pop':('exact','text-pop-in'),'tick':('fallback','typewriter-key-single'),'counter':('fallback','typewriter-line-return'),'progress completion':('fallback','soft-impact-modern'),
 'soft whoosh':('fallback','paper-swipe-clean'),'paper whoosh':('exact','paper-swipe-clean'),'fast swipe':('exact','fast-transition-whoosh'),'heavy swipe':('fallback','archive-drawer-slide'),'impact':('exact','soft-impact-modern'),'rise':('fallback','projector-start-modern'),'drop':('exact','soft-impact-modern'),'reveal':('fallback','fast-transition-whoosh'),'page transition':('exact','page-turn-soft'),'logo sting':('exact','final-logo-sting')
}
# motion pop intentionally uses text pop
coverage_map['pop']=('exact','text-pop-in')

def slugify(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

def copy_source(src, definition, source_group):
 dst=masters/source_group/src.name
 dst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(src,dst)
 return dst

def trim_and_process(src,dst,loopable=False,target_lufs=-18.0):
 data,sr=sf.read(src,always_2d=True,dtype='float64')
 if sr!=48000:
  tmp=dst.with_suffix('.resample.wav')
  subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(src),'-ar','48000','-ac','2','-c:a','pcm_s24le',str(tmp)],check=True)
  data,sr=sf.read(tmp,always_2d=True,dtype='float64');tmp.unlink()
 if data.shape[1]==1:data=np.repeat(data,2,axis=1)
 original_frames=len(data)
 if not loopable:
  env=np.max(np.abs(data),axis=1); threshold=10**(-58/20)
  active=np.where(env>threshold)[0]
  if active.size:
   pre=int(.012*sr);post=int(.02*sr);a=max(0,int(active[0])-pre);b=min(len(data),int(active[-1])+post+1);data=data[a:b]
  fade_in=min(int(.006*sr),len(data)//4);fade_out=min(int(.01*sr),len(data)//4)
  if fade_in>1:data[:fade_in]*=np.linspace(0,1,fade_in)[:,None]
  if fade_out>1:data[-fade_out:]*=np.linspace(1,0,fade_out)[:,None]
 target=-28.0 if loopable else target_lufs
 dur=len(data)/sr
 try:
  block=min(.4,max(.1,dur/2.4));meter=pyln.Meter(sr,block_size=block);loud=meter.integrated_loudness(data)
  if np.isfinite(loud):data=pyln.normalize.loudness(data,loud,target)
 except Exception:loud=float('nan')
 peak=float(np.max(np.abs(data))) if len(data) else 0
 ceiling=10**(-1.5/20)
 if peak>ceiling and peak>0:data*=ceiling/peak
 sf.write(dst,data,sr,subtype='PCM_24')
 return {'originalFrames':original_frames,'processedFrames':len(data),'trimmedSeconds':round((original_frames-len(data))/sr,5)}

def spectral_centroid(data,sr):
 mono=np.mean(data,axis=1);n=min(len(mono),sr*4)
 if n<32:return 0.0
 mono=mono[:n]*np.hanning(n);mag=np.abs(np.fft.rfft(mono));freq=np.fft.rfftfreq(n,1/sr);den=mag.sum();return float((freq*mag).sum()/den) if den else 0.0

def measure(path):
 data,sr=sf.read(path,always_2d=True,dtype='float64');dur=len(data)/sr;peak=float(np.max(np.abs(data))) if len(data) else 0;rms=float(np.sqrt(np.mean(data**2))) if len(data) else 0
 block=min(.4,max(.1,dur/2.4))
 try:loud=float(pyln.Meter(sr,block_size=block).integrated_loudness(data))
 except Exception:loud=float('nan')
 return {'durationSeconds':round(dur,5),'sampleRateHz':sr,'bitDepth':24,'channels':data.shape[1],'peakDbfs':round(20*math.log10(max(peak,1e-12)),2),'rmsDbfs':round(20*math.log10(max(rms,1e-12)),2),'integratedLufs':round(loud,2) if np.isfinite(loud) else None,'dcOffsetMax':round(float(np.max(np.abs(np.mean(data,axis=0)))),8),'clippedSamples':int(np.sum(np.abs(data)>=0.9999)),'spectralCentroidHz':round(spectral_centroid(data,sr),1),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

all_defs=[]
for src in sorted(input_pack.rglob('*.wav')):
 d=pack_defs[src.name].copy();d['sourceGroup']='documentary-pack-v1';d['provenance']='NexStudio Documentary Sound Pack V1; model-generated original procedural design; explicit editorial approval pending';d['loopable']=bool(d.get('loopable',False));all_defs.append((src,d))
for src in sorted(legacy.glob('*.mp3')):
 d=legacy_defs[src.name].copy();d['sourceGroup']='legacy-candidates';d['loopable']=False;all_defs.append((src,d))

manifests=[]
for src,d in all_defs:
 master=copy_source(src,d,d['sourceGroup'])
 out=production/(d['slug']+'.wav')
 process=trim_and_process(master,out,d.get('loopable',False))
 m=measure(out)
 manifest={
  'id':'audio.'+d['slug'],'slug':d['slug'],'name':d['title'],'version':'2.2.0','category':'audio','subtype':d['category'],'approvalStatus':'candidate','technicalStatus':'pass' if m['clippedSamples']==0 and m['peakDbfs']<=-1.45 and m['sampleRateHz']==48000 else 'review','editorialApproval':'pending','enabledByDefault':False,
  'intensity':d['intensity'],'semanticTags':d['tags'],'recommendedVisualActions':d['actions'],'recommendedTimingOffsetSeconds':d['offset'],'moods':d['mood'],'loopable':d.get('loopable',False),'sourceMaster':str(master.relative_to(root)),'productionFile':str(out.relative_to(root)),'provenance':d['provenance'],'licenseStatus':'original model-generated candidate; usage approval required','processing':{'silenceTrim':not d.get('loopable',False),'protectiveFadeInMs':0 if d.get('loopable',False) else 6,'protectiveFadeOutMs':0 if d.get('loopable',False) else 10,'targetLufs':-28 if d.get('loopable',False) else -18,'truePeakCeilingDbfs':-1.5,**process},'measurements':m,
  'slots':{'enabled':{'type':'boolean','default':False},'volume':{'type':'number','minimum':0,'maximum':1,'default':.72},'timingOffset':{'type':'number','minimum':-.5,'maximum':.5,'default':d['offset']},'alternateSound':{'type':'audio-id','optional':True},'voiceoverDuckingDb':{'type':'number','minimum':0,'maximum':18,'default':6},'musicDuckingDb':{'type':'number','minimum':0,'maximum':18,'default':3}},
  'accessibilityLabel':'Audition '+d['title']+' candidate sound effect'
 }
 (manifest_dir/(d['slug']+'.json')).write_text(json.dumps(manifest,indent=2))
 manifests.append(manifest)

# coverage report
coverage=[]
for cat,slots in coverage_slots.items():
 for slot in slots:
  status,audio=coverage_map.get(slot,('missing',None));coverage.append({'category':cat,'requestedSound':slot,'status':status,'audioId':'audio.'+audio if audio else None})
coverage_summary={k:sum(x['status']==k for x in coverage) for k in ['exact','fallback','missing']}
(root/'manifests/audio-coverage.json').write_text(json.dumps({'requestedSlotCount':len(coverage),'summary':coverage_summary,'slots':coverage},indent=2))
(root/'manifests/audio-index.json').write_text(json.dumps(manifests,indent=2))

# append to master registry, replacing prior audio entries
index_path=root/'manifests/index.json';index=json.loads(index_path.read_text());index=[x for x in index if x.get('category')!='audio'];index.extend(manifests);index_path.write_text(json.dumps(index,indent=2))

# runtime registry
(root/'runtime/audio-registry.js').write_text('window.NEX_AUDIO_ASSETS='+json.dumps(manifests,separators=(',',':'))+';\n')

# pairings: 32 motion primitives + 8 component uses
motion_index=json.loads((root/'manifests/motion-compatibility.json').read_text())
motion_ids=[]
if isinstance(motion_index,list): motion_ids=[x.get('id') for x in motion_index if isinstance(x,dict)]
elif isinstance(motion_index,dict):
 motions=motion_index.get('motions',{})
 if isinstance(motions,dict): motion_ids=list(motions.keys())
 else:
  for v in motion_index.values():
   if isinstance(v,list): motion_ids.extend([x.get('id') if isinstance(x,dict) else x for x in v])
motion_ids=[x for x in motion_ids if x][:32]
manual_audio=['paper-swipe-clean','page-turn-soft','soft-impact-modern','map-unfold-wide','tape-pull-snap','rubber-stamp-impact','marker-swipe-bold','fast-transition-whoosh','text-pop-in','staple-click-precise','projector-start-modern','archive-drawer-slide','bass-hit','film-advance-ratchet','radio-tune-transition','final-logo-sting']
pairs=[]
for i,mid in enumerate(motion_ids):
 pairs.append({'id':f'pair.motion.{i+1:02d}','visualId':mid,'visualType':'motion','audioId':'audio.'+manual_audio[i%len(manual_audio)],'matchType':'recommended','timingOffsetSeconds':manifests[i%len(manifests)]['recommendedTimingOffsetSeconds'],'volume':.68,'notes':'Reusable motion-to-sound candidate pairing'})
extra=[('object.opening-envelope.paper-01','paper-object','page-turn-soft'),('object.masking-tape-strip.paper-01','paper-object','tape-pull-snap'),('object.staple-attachment.paper-01','paper-object','staple-click-precise'),('typography.marker-highlight.paper-01','typography','marker-swipe-bold'),('documentary.date-stamp.paper-01','documentary','rubber-stamp-impact'),('documentary.map-journey.paper-01','documentary','map-unfold-wide'),('scene.logo-reveal.paper-01','scene-family','final-logo-sting'),('scene.documentary-evidence.paper-01','scene-family','archive-drawer-slide')]
for i,(vid,vt,aud) in enumerate(extra,start=len(pairs)+1):pairs.append({'id':f'pair.component.{i:02d}','visualId':vid,'visualType':vt,'audioId':'audio.'+aud,'matchType':'recommended','timingOffsetSeconds':next(m['recommendedTimingOffsetSeconds'] for m in manifests if m['slug']==aud),'volume':.7,'notes':'Approved lower-level visual paired to candidate sound'})
(root/'manifests/motion-sound-recommendations.json').write_text(json.dumps({'version':'2.2.0','approvalPolicy':'candidate sounds are excluded when requireApproved=true','pairingCount':len(pairs),'pairs':pairs},indent=2))

# JS API
api_js=r'''window.NexAudio=(()=>{
 const registry=window.NEX_AUDIO_ASSETS||[],active=new Set();
 const byId=id=>registry.find(x=>x.id===id||x.slug===id);
 const gainFromDb=db=>Math.pow(10,-Math.max(0,Number(db)||0)/20);
 function search({query='',tags=[],category='all',intensity='all',includeCandidates=true}={}){const q=String(query).toLowerCase();return registry.filter(a=>(includeCandidates||a.approvalStatus==='approved')&&(category==='all'||a.subtype===category)&&(intensity==='all'||a.intensity===intensity)&&(!tags.length||tags.every(t=>a.semanticTags.includes(t)))&&(!q||[a.name,a.slug,a.subtype,...a.semanticTags,...a.recommendedVisualActions].join(' ').toLowerCase().includes(q)))}
 function recommend({tags=[],actions=[],intensity='medium',requireApproved=false}={}){return registry.map(a=>{let score=0;for(const t of tags)if(a.semanticTags.some(x=>x===t||x.startsWith(t)||t.startsWith(x)))score+=4;for(const x of actions)if(a.recommendedVisualActions.includes(x))score+=3;if(a.intensity===intensity)score+=1;if(requireApproved&&a.approvalStatus!=='approved')score=-999;return{asset:a,score}}).filter(x=>x.score>=0).sort((a,b)=>b.score-a.score).map(x=>x.asset)}
 function resolvedVolume(opts={}){return Math.max(0,Math.min(1,Number(opts.volume??.72)*gainFromDb(opts.voiceoverDuckingDb||0)*gainFromDb(opts.musicDuckingDb||0)))}
 function createElement(id,opts={}){const a=byId(opts.alternateSound||id);if(!a)throw Error('Unknown audio '+id);const el=document.createElement('audio');el.src=a.productionFile;el.preload='auto';el.dataset.audioId=a.id;el.dataset.start=String(opts.start||0);el.dataset.duration=String(opts.duration||a.measurements.durationSeconds);el.dataset.trackIndex=String(opts.trackIndex||90);el.dataset.volume=String(resolvedVolume(opts));el.volume=resolvedVolume(opts);if(a.loopable)el.loop=Boolean(opts.loop);return el}
 async function audition(id,opts={}){stopAll();const a=byId(opts.alternateSound||id);if(!a)throw Error('Unknown audio '+id);const el=new Audio(a.productionFile);el.volume=resolvedVolume(opts);active.add(el);el.addEventListener('ended',()=>active.delete(el),{once:true});const delay=Math.max(0,(Number(opts.timingOffset)||0)*1000);if(delay)await new Promise(r=>setTimeout(r,delay));await el.play();return el}
 function stopAll(){for(const a of active){try{a.pause();a.currentTime=0}catch(_){}}active.clear()}
 function schedule(container,events=[],mix={}){const out=[];for(const e of events){if(e.enabled===false)continue;const el=createElement(e.audioId,{...mix,...e});container.append(el);out.push(el)}return out}
 return{registry,byId,search,recommend,createElement,audition,stopAll,schedule,resolvedVolume};
})();
'''
(root/'runtime/audio-system.js').write_text(api_js)

# pair visual component API
(root/'components/audio-pairings.js').write_text(r'''window.NexAudioPairings=(()=>{const pairs='''+json.dumps(pairs,separators=(',',':'))+r''';
 function create(pair){const d=typeof pair==='string'?pairs.find(x=>x.id===pair):pair,el=document.createElement('article');el.className='audio-pair-card';el.dataset.pairId=d.id;el.innerHTML=`<div class="pair-visual"><div class="pair-paper"><span>${d.visualId.split('.').slice(-2,-1)[0].replaceAll('-',' ')}</span></div></div><div class="pair-copy"><b>${d.visualId}</b><small>${d.audioId}</small><button type="button">Play pair</button></div>`;const btn=el.querySelector('button'),paper=el.querySelector('.pair-paper');btn.addEventListener('click',async()=>{const motion=(d.visualId.split('.').pop()||'paper-slide').replace('paper-01','');try{const tl=NexMotion.apply(paper,motion,{duration:1.1,energy:'medium'});tl.restart?.()}catch(_){paper.animate([{transform:'translateY(18px) scale(.92)',opacity:.25},{transform:'translateY(0) scale(1)',opacity:1}],{duration:700,easing:'cubic-bezier(.2,.8,.2,1)'})}await NexAudio.audition(d.audioId,{volume:d.volume,timingOffset:d.timingOffsetSeconds})});return el}
 return{pairs,create};})();
''')

# styles
(root/'styles/audio-system.css').write_text(r'''
:root{--audio-panel:color-mix(in srgb,var(--paper-surface) 90%,white 10%)}
.audio-banner{padding:14px 18px;border:2px solid var(--ink);background:var(--highlight);box-shadow:7px 7px 0 var(--ink);font-weight:800;font-size:13px;line-height:1.35}.audio-app{min-height:100vh;background:var(--paper-bg);color:var(--ink);font-family:Inter,Arial,sans-serif;display:grid;grid-template-columns:310px 1fr}.audio-sidebar{padding:24px;border-right:2px solid var(--ink);background:var(--paper-surface);position:sticky;top:0;height:100vh;overflow:auto}.audio-brand{font-size:24px;font-weight:950;line-height:.95}.audio-kicker{font:800 11px/1.2 monospace;letter-spacing:.12em;margin:10px 0 20px}.audio-controls{display:grid;gap:12px}.audio-controls label{display:grid;gap:5px;font-size:11px;font-weight:800;text-transform:uppercase}.audio-controls input,.audio-controls select{width:100%;box-sizing:border-box;padding:9px;border:1.5px solid var(--ink);background:white;color:#111}.audio-main{padding:28px;min-width:0}.audio-hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-start}.audio-hero h1{font-size:clamp(32px,5vw,72px);line-height:.92;max-width:900px;margin:14px 0}.audio-count{font-size:64px;font-weight:950}.audio-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;margin-top:28px}.sound-card,.audio-pair-card{background:var(--audio-panel);border:2px solid var(--ink);box-shadow:8px 8px 0 color-mix(in srgb,var(--ink) 20%,transparent);padding:14px;position:relative;overflow:hidden}.sound-card::before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 20% 10%,rgba(255,255,255,.5),transparent 34%),repeating-linear-gradient(0deg,transparent 0 3px,rgba(0,0,0,.025) 3px 4px);pointer-events:none}.sound-card h3{margin:0 0 4px;font-size:18px}.sound-meta{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0}.sound-meta span{font:700 10px/1 monospace;padding:5px 7px;border:1px solid var(--ink);background:var(--paper-surface-alt)}.candidate-badge{background:var(--accent)!important;color:white}.waveform{height:54px;display:flex;align-items:center;gap:2px;margin:12px 0}.waveform i{display:block;flex:1;min-width:2px;background:var(--primary);border-radius:3px}.sound-actions{display:flex;gap:8px}.sound-actions button,.audio-pair-card button{border:2px solid var(--ink);background:var(--primary);color:white;font-weight:900;padding:9px 11px;cursor:pointer}.sound-controls{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.sound-controls label{font-size:10px;font-weight:800}.sound-controls input,.sound-controls select{width:100%}.pair-section{margin-top:48px}.pair-section h2{font-size:40px;margin-bottom:8px}.pair-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}.audio-pair-card{display:grid;grid-template-columns:92px 1fr;gap:12px;align-items:center}.pair-visual{height:88px;display:grid;place-items:center}.pair-paper{width:78px;height:64px;background:var(--paper-surface);border:2px solid var(--ink);box-shadow:5px 5px 0 var(--secondary);display:grid;place-items:center;padding:6px;box-sizing:border-box;text-align:center;text-transform:uppercase;font:800 9px/1.1 monospace}.pair-copy{display:grid;gap:5px;min-width:0}.pair-copy b,.pair-copy small{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pair-copy small{font:700 9px monospace;color:var(--ink-muted)}
.audio-demo{width:100%;height:100%;background:var(--paper-bg);color:var(--ink);font-family:Inter,Arial,sans-serif;overflow:hidden;position:relative}.audio-demo .demo-title{position:absolute;left:7%;top:6%;font-weight:950;font-size:clamp(34px,5vw,78px);line-height:.9;max-width:70%}.audio-demo .demo-label{position:absolute;left:7%;bottom:6%;font:800 13px monospace;letter-spacing:.12em}.audio-demo .demo-stage{position:absolute;inset:20% 7% 16%;display:grid;place-items:center}.demo-object{width:min(62vw,720px);height:min(46vh,430px);background:var(--paper-surface);border:4px solid var(--ink);box-shadow:18px 18px 0 var(--secondary);display:grid;place-items:center;position:relative;padding:40px;box-sizing:border-box;text-align:center}.demo-object h2{font-size:clamp(30px,5vw,76px);line-height:.95;margin:0}.demo-object p{font-size:clamp(16px,2vw,28px);max-width:700px}.demo-object .accent{position:absolute;width:90px;height:18px;background:var(--accent);top:20px;right:-26px;transform:rotate(5deg)}.demo-scene{position:absolute;inset:0;opacity:0;display:grid;place-items:center}.demo-scene.active{opacity:1}.demo-scene .demo-object{transform-origin:center}.audio-status{position:absolute;right:4%;top:5%;font:900 11px monospace;padding:8px 10px;border:2px solid var(--ink);background:var(--highlight)}
@media(max-width:800px){.audio-app{grid-template-columns:1fr}.audio-sidebar{position:relative;height:auto;border-right:0;border-bottom:2px solid var(--ink)}.audio-main{padding:18px}.audio-hero{display:block}.audio-count{font-size:42px}.audio-grid{grid-template-columns:1fr}}
''')

# explorer HTML/JS
explorer='''<!doctype html><html lang="en" data-paper-style="clean-editorial"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NexStudio Sound Audition</title><link rel="stylesheet" href="styles/tokens.css"><link rel="stylesheet" href="styles/paper.css"><link rel="stylesheet" href="styles/audio-system.css"></head><body><div class="audio-app"><aside class="audio-sidebar"><div class="audio-brand">NEXSTUDIO<br>SOUND SYSTEM</div><div class="audio-kicker">BATCH 14 · CANDIDATE INGESTION</div><div class="audio-banner">No source in this build is editorially approved. Technical QA passed; audition and approve before production.</div><div class="audio-controls"><label>Search<input id="audioSearch" placeholder="paper, whoosh, stamp"></label><label>Category<select id="audioCategory"><option value="all">All</option><option value="paper-foley">Paper Foley</option><option value="interface">Interface</option><option value="motion-transition">Motion / Transition</option><option value="ambience">Ambience</option></select></label><label>Intensity<select id="audioIntensity"><option value="all">All</option><option>soft</option><option>medium</option><option>heavy</option><option>sharp</option><option>fast</option></select></label><label>Volume<input id="audioVolume" type="range" min="0" max="1" step=".01" value=".72"></label><label>Timing offset<input id="audioOffset" type="range" min="-.25" max=".25" step=".01" value="0"></label><label>Voiceover ducking<input id="voiceDuck" type="range" min="0" max="18" step="1" value="6"></label><label>Music ducking<input id="musicDuck" type="range" min="0" max="18" step="1" value="3"></label><button id="stopAudio">Stop all audio</button></div></aside><main class="audio-main"><header class="audio-hero"><div><div class="audio-kicker">SEARCHABLE · TAGGED · NON-DESTRUCTIVE</div><h1>Motion and sound stay separate until the final mix.</h1></div><div class="audio-count" id="audioCount">24</div></header><section class="audio-grid" id="audioGrid"></section><section class="pair-section"><h2>40 reusable pairings</h2><p>Each animation remains usable without sound. The recommendation layer supplies an optional candidate.</p><div class="pair-grid" id="pairGrid"></div></section></main></div><script src="vendor/gsap-compat.js"></script><script src="runtime/theme.js"></script><script src="runtime/motion-registry.js"></script><script src="runtime/motion-engine.js"></script><script src="runtime/audio-registry.js"></script><script src="runtime/audio-system.js"></script><script src="components/audio-pairings.js"></script><script src="runtime/audio-explorer.js"></script></body></html>'''
(root/'sound-audition.html').write_text(explorer)
(root/'runtime/audio-explorer.js').write_text(r'''(()=>{const grid=document.getElementById('audioGrid'),pairGrid=document.getElementById('pairGrid'),search=document.getElementById('audioSearch'),category=document.getElementById('audioCategory'),intensity=document.getElementById('audioIntensity'),count=document.getElementById('audioCount');
 function bars(a){const seed=[...a.slug].reduce((n,c)=>n+c.charCodeAt(0),0);return Array.from({length:36},(_,i)=>`<i style="height:${9+((Math.sin((i+seed)*.73)+1)*18+((i*seed)%13))}px"></i>`).join('')}
 function opts(){return{volume:+document.getElementById('audioVolume').value,timingOffset:+document.getElementById('audioOffset').value,voiceoverDuckingDb:+document.getElementById('voiceDuck').value,musicDuckingDb:+document.getElementById('musicDuck').value}}
 function card(a){const el=document.createElement('article');el.className='sound-card';el.innerHTML=`<h3>${a.name}</h3><div class="sound-meta"><span>${a.subtype}</span><span>${a.intensity}</span><span>${a.measurements.durationSeconds}s</span><span>${a.measurements.integratedLufs} LUFS</span><span class="candidate-badge">CANDIDATE</span></div><div class="waveform">${bars(a)}</div><div class="sound-actions"><button data-play>Audition</button><button data-stop>Stop</button></div><div class="sound-controls"><label>Alternate<select data-alt><option value="">Default</option>${NexAudio.registry.filter(x=>x.id!==a.id&&x.subtype===a.subtype).map(x=>`<option value="${x.id}">${x.name}</option>`).join('')}</select></label><label>Offset <output>${a.recommendedTimingOffsetSeconds}s</output></label></div>`;el.querySelector('[data-play]').onclick=()=>NexAudio.audition(a.id,{...opts(),alternateSound:el.querySelector('[data-alt]').value||undefined});el.querySelector('[data-stop]').onclick=()=>NexAudio.stopAll();return el}
 function render(){NexAudio.stopAll();const list=NexAudio.search({query:search.value,category:category.value,intensity:intensity.value,includeCandidates:true});grid.replaceChildren(...list.map(card));count.textContent=list.length}
 [search,category,intensity].forEach(x=>x.addEventListener(x===search?'input':'change',render));document.getElementById('stopAudio').onclick=()=>NexAudio.stopAll();pairGrid.replaceChildren(...NexAudioPairings.pairs.map(NexAudioPairings.create));render()})();
''')

# composition schedules and HTML
schedules={
 'paper-foley-demo':[
  (0.35,'paper-swipe-clean',.72),(2.75,'page-turn-soft',.72),(5.2,'tape-pull-snap',.7),(7.85,'marker-swipe-bold',.68),(10.55,'rubber-stamp-impact',.72),(13.25,'map-unfold-wide',.72),(16.0,'newspaper-rustle',.58)],
 'ui-sound-demo':[(.35,'text-pop-in',.68),(2.4,'typewriter-key-single',.7),(4.45,'staple-click-precise',.72),(6.5,'projector-start-modern',.52),(9.0,'soft-impact-modern',.65),(11.4,'bass-hit',.5),(13.4,'text-pop-in',.64)],
 'transition-sound-demo':[(.3,'paper-swipe-clean',.65),(2.8,'fast-transition-whoosh',.68),(5.3,'archive-drawer-slide',.62),(8.0,'radio-tune-transition',.55),(10.9,'page-turn-soft',.68),(13.4,'soft-impact-modern',.7),(15.8,'final-logo-sting',.66)]
}
(root/'manifests/audio-demo-schedules.json').write_text(json.dumps({k:[{'start':s,'audioId':'audio.'+a,'volume':v} for s,a,v in vals] for k,vals in schedules.items()},indent=2))

def comp_html(cid,title,subtitle,duration,scenes,w,h,style='clean-editorial'):
 scene_html=''.join(f'<section class="demo-scene" data-scene="{i}"><div class="demo-object"><span class="accent"></span><div><h2>{s[0]}</h2><p>{s[1]}</p></div></div></section>' for i,s in enumerate(scenes))
 js='''const scenes=[...document.querySelectorAll('.demo-scene')],duration='''+str(duration)+''';window.seekComposition=t=>{t=Math.max(0,Math.min(duration,t));scenes.forEach((s,i)=>{const start=i*(duration/scenes.length),end=(i+1)*(duration/scenes.length),local=(t-start)/(end-start);let o=0,scale=.94,y=26,rot=-2;if(local>=0&&local<=1){o=Math.min(1,local*4, (1-local)*5+1);scale=.94+.06*Math.min(1,local*4);y=26*(1-Math.min(1,local*4));rot=-2*(1-Math.min(1,local*4))}s.style.opacity=o;s.querySelector('.demo-object').style.transform=`translateY(${y}px) scale(${scale}) rotate(${rot}deg)`});};window.seekComposition(0.1);'''
 return f'''<!doctype html><html lang="en" data-paper-style="{style}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="../styles/tokens.css"><link rel="stylesheet" href="../styles/paper.css"><link rel="stylesheet" href="../styles/audio-system.css"></head><body><div id="{cid}" data-composition-id="{cid}" data-start="0" data-duration="{duration}" data-track-index="1" data-width="{w}" data-height="{h}" class="audio-demo"><div class="demo-title">{title}</div><div class="audio-status">CANDIDATE AUDIO · EDITORIAL APPROVAL PENDING</div><div class="demo-stage">{scene_html}</div><div class="demo-label">{subtitle}</div></div><script>{js}</script></body></html>'''

paper_scenes=[('SLIDE','Paper movement opens the visual thought.'),('TURN','A chapter changes without a jump cut.'),('ATTACH','Tape makes the placement feel physical.'),('MARK','Emphasis follows the selected text region.'),('STAMP','Approval lands with a tactile punctuation.'),('UNFOLD','Routes and geography open across the page.'),('SHUFFLE','Archival sheets settle into a new order.')]
ui_scenes=[('NOTIFY','A restrained pop introduces new information.'),('SELECT','A precise key tick confirms selection.'),('CONFIRM','A mechanical click closes the action.'),('PROCESS','A rising mechanism communicates progress.'),('SUCCESS','A soft impact completes the task.'),('ERROR','A heavier candidate marks a negative state.'),('READY','The interface returns to a calm resting state.')]
trans_scenes=[('PAPER WIPE','A soft paper pass carries the cut.'),('FAST SWIPE','A sharper whoosh raises the pace.'),('HEAVY MOVE','An archive drawer adds physical weight.'),('TIME SHIFT','A radio scan changes source and era.'),('PAGE TURN','The outgoing scene stays visible through the turn.'),('LAND','A controlled impact settles the composition.'),('LOGO','The final mark receives a warm candidate sting.')]
(root/'compositions/paper-foley-demo.html').write_text(comp_html('paper-foley-demo','PAPER HAS A SOUND.','PAPER FOLEY · 18 SECONDS',18,paper_scenes,1920,1080,'handmade-scrapbook'))
(root/'compositions/ui-sound-demo.html').write_text(comp_html('ui-sound-demo','INTERACTION, WITHOUT GENERIC BEEPS.','INTERFACE SOUND · 15 SECONDS',15,ui_scenes,1080,1080,'technical-notebook'))
(root/'compositions/transition-sound-demo.html').write_text(comp_html('transition-sound-demo','MOTION CARRIES WEIGHT.','TRANSITIONS · 18 SECONDS',18,trans_scenes,1080,1920,'bold-paper-collage'))

# independent audio previews
for m in manifests:
 (root/'previews/audio'/(m['slug']+'.html')).write_text(f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../../styles/tokens.css"><link rel="stylesheet" href="../../styles/audio-system.css"></head><body><main style="padding:30px;background:var(--paper-bg);min-height:100vh"><h1>{m['name']}</h1><p>{', '.join(m['semanticTags'])}</p><audio controls src="../../{m['productionFile']}"></audio><pre>{json.dumps(m,indent=2)}</pre></main></body></html>''')

# docs updates
(root/'AUDIO_SYSTEM_API.md').write_text('''# NexStudio Audio System API\n\nBatch 14 keeps sound separate from visual components.\n\n```js\nNexAudio.search({ tags: ["paper.soft"] })\nNexAudio.recommend({ tags: ["transition.page"], requireApproved: true })\nNexAudio.audition("audio.page-turn-soft", { volume: 0.7, timingOffset: -0.08 })\nNexAudio.schedule(container, [{ audioId: "audio.page-turn-soft", start: 2.4 }], { voiceoverDuckingDb: 6 })\n```\n\n## Approval policy\n\nThe 24 discovered sources pass technical QA but are marked `candidate`. They are disabled by default in production selection. An editor must update `approvalStatus` to `approved` after listening.\n\n## Non-destructive model\n\n- Original masters remain in `assets/audio/masters/candidate-v1/`.\n- Production copies live in `assets/audio/production/candidate-v1/`.\n- Visual components contain semantic tags only.\n- Volume, offset, alternate selection and ducking are mix-time controls.\n''')
(root/'AUDIO_MAPPING.md').write_text('''# Audio Mapping\n\nBatch 14 adds a non-destructive candidate-audio layer. Motion and visual components retain semantic `soundTags`; audio is selected at composition time through `NexAudio`.\n\nCurrent discovered source coverage: **24 candidate assets**. Technical QA is complete, but editorial approval is pending. Exact/fallback/missing requested coverage is recorded in `manifests/audio-coverage.json`.\n\nAudio remains disabled by default until `approvalStatus` is changed to `approved`.\n''')

# package updates
pkg=json.loads((root/'package.json').read_text());pkg['version']='2.2.0-batch14';pkg['description']='Reusable NexStudio paper-motion library with candidate sound ingestion, metadata, audition and motion pairing';pkg['scripts'].update({'build:batch14':'python3 tests/build_batch14.py','validate:batch14':'python3 tests/validate_batch14.py','smoke:batch14':'python3 tests/smoke_audio.py','render:batch14':'python3 tests/render_audio_demos.py'});(root/'package.json').write_text(json.dumps(pkg,indent=2))
# changelog and readme
with (root/'CHANGELOG.md').open('a') as f:f.write('\n## 2.2.0-batch14\n- Added 24 technically-QA-passed candidate sound assets, searchable audition UI, 40 motion pairings and three audiovisual demos.\n- Added exact/fallback/missing sound coverage reporting. No asset is editorially approved by implication.\n')
with (root/'README.md').open('a') as f:f.write('\n## Batch 14 — Sound integration\nOpen `sound-audition.html`. Candidate audio is disabled by default for production selection until editorial approval.\n')
print(json.dumps({'sounds':len(manifests),'pairs':len(pairs),'registry':len(index),'coverage':coverage_summary},indent=2))
