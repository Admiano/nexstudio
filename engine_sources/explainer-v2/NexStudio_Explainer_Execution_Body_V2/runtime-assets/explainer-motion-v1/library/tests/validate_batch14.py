from pathlib import Path
import json,sys,hashlib
import soundfile as sf
root=Path(__file__).resolve().parents[1];errors=[]
mdir=root/'manifests/audio';mans=[]
for p in sorted(mdir.glob('*.json')):
 try:mans.append(json.loads(p.read_text()))
 except Exception as e:errors.append(f'Invalid {p.name}: {e}')
if len(mans)!=24:errors.append(f'Expected 24 discovered candidate sounds, found {len(mans)}')
if len({m.get('id') for m in mans})!=24:errors.append('Audio IDs not unique')
for m in mans:
 for key in ['sourceMaster','productionFile','provenance','semanticTags','recommendedVisualActions','recommendedTimingOffsetSeconds','measurements','approvalStatus','technicalStatus']:
  if key not in m:errors.append(m.get('id','?')+' missing '+key)
 for k in ['sourceMaster','productionFile']:
  p=root/m.get(k,'')
  if not p.exists():errors.append(m.get('id','?')+' missing file '+k)
 if m.get('approvalStatus')!='candidate':errors.append(m.get('id','?')+' incorrectly promoted beyond candidate')
 if m.get('technicalStatus')!='pass':errors.append(m.get('id','?')+' did not pass technical QA')
 me=m.get('measurements',{})
 if me.get('sampleRateHz')!=48000 or me.get('channels')!=2 or me.get('bitDepth')!=24:errors.append(m.get('id','?')+' format mismatch')
 if me.get('clippedSamples')!=0 or (me.get('peakDbfs') or 0)>-1.45:errors.append(m.get('id','?')+' clipping/peak failure')
coverage=json.loads((root/'manifests/audio-coverage.json').read_text());pairs=json.loads((root/'manifests/motion-sound-recommendations.json').read_text())
if coverage.get('requestedSlotCount')!=43:errors.append('Coverage must contain 43 requested slots')
if pairs.get('pairingCount')<40 or len(pairs.get('pairs',[]))<40:errors.append('Fewer than 40 pairings')
index=json.loads((root/'manifests/index.json').read_text())
if len(index)!=506:errors.append(f'Expected registry 506, found {len(index)}')
if sum(x.get('category')=='audio' for x in index)!=24:errors.append('Master registry audio count mismatch')
for f in ['runtime/audio-registry.js','runtime/audio-system.js','runtime/audio-explorer.js','components/audio-pairings.js','styles/audio-system.css','sound-audition.html','AUDIO_SYSTEM_API.md','manifests/audio-demo-schedules.json']:
 if not (root/f).exists():errors.append('Missing '+f)
for n,d,w,h in [('paper-foley-demo',18,1920,1080),('ui-sound-demo',15,1080,1080),('transition-sound-demo',18,1080,1920)]:
 p=root/f'compositions/{n}.html'
 if not p.exists():errors.append('Missing '+str(p));continue
 s=p.read_text()
 for token in [f'data-composition-id="{n}"',f'data-duration="{d}"',f'data-width="{w}"',f'data-height="{h}"','window.seekComposition']:
  if token not in s:errors.append(n+' missing '+token)
report={'status':'PASS' if not errors else 'FAIL','version':'2.2.0-batch14','candidateSoundCount':len(mans),'approvedSoundCount':sum(m.get('approvalStatus')=='approved' for m in mans),'pairingCount':len(pairs.get('pairs',[])),'masterRegistryEntries':len(index),'coverageSummary':coverage.get('summary'),'editorialApprovalRequired':True,'errors':errors}
(root/'reports/batch14-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
