from pathlib import Path
import json,re,sys
root=Path(__file__).resolve().parents[1];errors=[];warnings=[]
required=['motion-explorer.html','runtime/motion-registry.js','runtime/motion-engine.js','runtime/motion-matrix.js','runtime/transition-demo.js','styles/motion.css','styles/motion-matrix.css','styles/transition-composition.css','compositions/transition-demo.html','manifests/motion-compatibility.json']
for f in required:
    if not (root/f).exists():errors.append(f'Missing Batch 3 file: {f}')
files=sorted((root/'manifests/motions').glob('*.json'))
if len(files)!=32:errors.append(f'Expected 32 motion manifests, found {len(files)}')
ids=[];keys=[];subtypes={};
for f in files:
    try:d=json.loads(f.read_text())
    except Exception as e:errors.append(f'Invalid JSON {f.name}: {e}');continue
    for k in ['id','name','version','category','subtype','key','intents','keywords','paperStyles','aspectRatios','slots','duration','motionEnergy','compatibleTargets','defaultEase','soundTags','themeTokens','accessibilityLabel','deterministic','seekable','finite']:
        if k not in d:errors.append(f'{f.name}: missing {k}')
    ids.append(d.get('id'));keys.append(d.get('key'));subtypes[d.get('subtype')]=subtypes.get(d.get('subtype'),0)+1
    if len(d.get('compatibleTargets',[]))<3:errors.append(f'{f.name}: fewer than 3 target types')
    if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']):errors.append(f'{f.name}: incomplete aspect ratios')
    if set(d.get('slots',{}))<={'duration','delay','intensity','easing'}:pass
    else:errors.append(f'{f.name}: missing control slots')
    if not all(d.get(k) is True for k in ['deterministic','seekable','finite']):errors.append(f'{f.name}: deterministic/seekable/finite flags invalid')
    if d.get('subtype')=='transition' and not d.get('preservesOutgoingUntilStart'):errors.append(f'{f.name}: transition preservation flag missing')
expected={'entrance':10,'action':10,'ambient':5,'transition':7}
if subtypes!=expected:errors.append(f'Wrong subtype counts: {subtypes}')
if len(ids)!=len(set(ids)):errors.append('Duplicate motion IDs')
if len(keys)!=len(set(keys)):errors.append('Duplicate motion keys')
compat=json.loads((root/'manifests/motion-compatibility.json').read_text())
if len(compat.get('motions',{}))!=32:errors.append('Compatibility registry does not contain 32 motions')
index=json.loads((root/'manifests/index.json').read_text());cats={}
for x in index:cats[x.get('category')]=cats.get(x.get('category'),0)+1
if len(index)<112:errors.append(f'Expected at least 112 master registry entries, found {len(index)}')
if cats.get('foundation')!=40 or cats.get('paper-object')!=40 or cats.get('motion')!=32:errors.append(f'Prior/new category counts invalid: {cats}')
engine=(root/'runtime/motion-engine.js').read_text()
for api in ['apply','transition','createTimeline','MotionTimeline']:
    if api not in engine:errors.append(f'Missing public motion API: {api}')
for object_specific in ['object.rectangular-card','sticky-note','speech-bubble.paper']:
    if object_specific in engine:errors.append(f'Motion engine improperly hardcodes artwork: {object_specific}')
all_text='\n'.join(p.read_text(errors='ignore') for p in root.rglob('*') if p.is_file() and p.suffix in {'.js','.html','.css'} and p.name!='gsap-compat.batch2.js')
for banned in ['Math.random(', 'Date.now(', 'repeat: -1','repeat:-1']:
    if banned in all_text:errors.append(f'Banned pattern found: {banned}')
comp=(root/'compositions/transition-demo.html').read_text()
for attr in ['data-composition-id','data-start','data-duration','data-track-index','data-width','data-height']:
    if attr not in comp:errors.append(f'Transition composition missing {attr}')
if 'window.__timelines' not in (root/'runtime/transition-demo.js').read_text():errors.append('Transition demo is not registered')
report={'status':'PASS' if not errors else 'FAIL','motionManifestCount':len(files),'subtypeCounts':subtypes,'masterRegistryCount':len(index),'categoryCounts':cats,'uniqueMotionIds':len(set(ids)),'compatibilityEntries':len(compat.get('motions',{})),'errors':errors,'warnings':warnings}
(root/'reports/batch3-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
