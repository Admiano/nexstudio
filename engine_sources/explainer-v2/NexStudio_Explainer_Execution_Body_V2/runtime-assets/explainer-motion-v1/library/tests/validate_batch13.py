from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1];errors=[]
required=['hook','question','bold-statement','quote','chapter-opening','problem','solution','feature-introduction','product-demonstration','tutorial-step','numbered-list','comparison','before-and-after','statistic','chart','timeline','process','agent-workflow','tool-stack','file-to-output','prompt-to-result','human-agent-handoff','testimonial','social-proof','comment-or-reaction','profile-introduction','news-update','documentary-evidence','photo-collage','map-or-journey','milestone','recap','call-to-action','credits','logo-reveal','closing-statement']
mdir=root/'manifests/scene-families';pdir=root/'previews/scene-families';mans=[]
for p in sorted(mdir.glob('*.json')):
 try:mans.append(json.loads(p.read_text()))
 except Exception as e:errors.append(f'Invalid manifest {p.name}: {e}')
if len(mans)!=36:errors.append(f'Expected 36 manifests, found {len(mans)}')
if [m.get('slug') for m in mans]!=required:errors.append('Required scene order or inventory mismatch')
if len({m.get('id') for m in mans})!=36:errors.append('Scene IDs are not unique')
if len(list(pdir.glob('*.html')))!=36:errors.append('Expected 36 independent previews')
for m in mans:
 if len(m.get('layoutVariants',[]))<2:errors.append(m['id']+' has fewer than two variants')
 if m.get('paperStyles')!=['clean-editorial','handmade-scrapbook','technical-notebook','bold-paper-collage']:errors.append(m['id']+' paper styles invalid')
 if m.get('motionEnergy')!=['low','medium','high']:errors.append(m['id']+' energy invalid')
 if m.get('aspectRatios')!=['16:9','1:1','9:16']:errors.append(m['id']+' aspect ratios invalid')
 if not (3<=m.get('duration',{}).get('minimum',0)<=m.get('duration',{}).get('maximum',0)<=12):errors.append(m['id']+' duration invalid')
 for k in ['title','body','media','items','data']:
  if k not in m.get('slots',{}):errors.append(m['id']+' missing slot '+k)
 if len(m.get('compatibleTransitions',[]))<5:errors.append(m['id']+' transition compatibility insufficient')
 if not m.get('soundTags'):errors.append(m['id']+' missing sound tags')
 if not m.get('approvedComponents'):errors.append(m['id']+' missing approved components')
index=json.loads((root/'manifests/index.json').read_text())
if len(index)!=482:errors.append(f'Expected registry 482, found {len(index)}')
if sum(x.get('category')=='scene-family' for x in index)!=36:errors.append('Master registry scene count mismatch')
files=['components/scene-rigs.js','runtime/scene-rig-registry.js','runtime/scene-rig-explorer.js','runtime/scene-films.js','styles/scene-rigs.css','styles/scene-explorer.css','styles/scene-films.css','scene-rig-explorer.html','SCENE_RIG_API.md','compositions/creator-explainer.html','compositions/agent-workflow-film.html','compositions/documentary-scrapbook-film.html']
for f in files:
 if not (root/f).exists():errors.append('Missing '+f)
for scene in ['creator-explainer','agent-workflow-film','documentary-scrapbook-film']:
 s=(root/f'compositions/{scene}.html').read_text()
 for token in ['data-composition-id','data-start="0"','data-duration="60"','data-track-index="1"']:
  if token not in s:errors.append(scene+' missing '+token)
source=(root/'components/scene-rigs.js').read_text()
for token in ['NexTypography.create','NexMediaContainers.create','NexDataVisualisations.create','NexCreatorModules.create','NexDocumentaryModules.create','NexPaperObjects.create']:
 if token not in source:errors.append('Scene runtime does not compose approved component API '+token)
report={'status':'PASS' if not errors else 'FAIL','version':'2.1.0-batch13','sceneFamilyCount':len(mans),'layoutVariantCount':sum(len(m.get('layoutVariants',[])) for m in mans),'previewCount':len(list(pdir.glob('*.html'))),'masterRegistryEntries':len(index),'errors':errors}
(root/'reports/batch13-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
