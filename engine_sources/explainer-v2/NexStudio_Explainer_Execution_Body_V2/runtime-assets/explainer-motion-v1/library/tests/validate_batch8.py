from pathlib import Path
import json,sys,re
root=Path(__file__).resolve().parents[1];errors=[];warnings=[]
required=['typography-explorer.html','runtime/typography-registry.js','runtime/typography-samples.js','components/typography.js','styles/typography.css','styles/typography-explorer.css','styles/typography-scenes.css','runtime/kinetic-typography-demo.js','TYPOGRAPHY_API.md','compositions/typography-landscape.html','compositions/typography-square.html','compositions/typography-portrait.html','compositions/kinetic-typography-demo.html']
for f in required:
    if not (root/f).exists():errors.append(f'Missing Batch 8 file: {f}')
files=sorted((root/'manifests/typography').glob('*.json'));previews=sorted((root/'previews/typography').glob('*.html'))
if len(files)!=24:errors.append(f'Expected 24 manifests, found {len(files)}')
if len(previews)!=24:errors.append(f'Expected 24 previews, found {len(previews)}')
ids=[];slugs=[];groups={}
required_fields=['id','name','version','category','subtype','slug','renderer','order','intents','keywords','paperStyles','aspectRatios','slots','characterGuidance','duration','motionEnergy','compatibleMotions','defaultMotion','soundTags','themeTokens','accessibilityLabel','responsiveText','editable','scalable','agentSelection']
for f in files:
    try:d=json.loads(f.read_text())
    except Exception as e:errors.append(f'Invalid JSON {f.name}: {e}');continue
    for k in required_fields:
        if k not in d:errors.append(f'{f.name}: missing {k}')
    ids.append(d.get('id'));slugs.append(d.get('slug'));groups[d.get('subtype')]=groups.get(d.get('subtype'),0)+1
    if d.get('category')!='typography':errors.append(f'{f.name}: wrong category')
    if len(d.get('paperStyles',[]))<3:errors.append(f'{f.name}: fewer than three paper styles')
    if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']):errors.append(f'{f.name}: aspect ratios incomplete')
    if len(d.get('compatibleMotions',[]))<3:errors.append(f'{f.name}: fewer than three motions')
    if not d.get('characterGuidance'):errors.append(f'{f.name}: missing character guidance')
    if not all(d.get(k) is True for k in ['responsiveText','editable','scalable']):errors.append(f'{f.name}: source flags invalid')
    for slot,spec in d.get('slots',{}).items():
        if spec.get('type')=='string' and not spec.get('maxCharacters'):errors.append(f'{f.name}: {slot} missing maxCharacters')
if len(ids)!=len(set(ids)):errors.append('Duplicate typography IDs')
if len(slugs)!=len(set(slugs)):errors.append('Duplicate typography slugs')
index=json.loads((root/'manifests/index.json').read_text());cats={}
for x in index:cats[x.get('category')]=cats.get(x.get('category'),0)+1
expected={'foundation':40,'paper-object':40,'motion':32,'icon':172,'typography':24}
for k,v in expected.items():
    if cats.get(k)!=v:errors.append(f'Category {k}: expected {v}, found {cats.get(k)}')
if len(index)!=308:errors.append(f'Expected master registry 308, found {len(index)}')
source=(root/'components/typography.js').read_text()
for api in ['create','fitText','animate','update','setStyle','setAlignment']:
    if api not in source:errors.append(f'Missing typography API: {api}')
for slug in slugs:
    if f"case'{slug}'" not in source:errors.append(f'Missing renderer/animation case: {slug}')
if '<br>' in source or '<br />' in source:errors.append('Fixed br tag found in typography source')
alltext='\n'.join((root/f).read_text(errors='ignore') for f in required if (root/f).exists())+'\n'+source
for banned in ['Math.random(', 'Date.now(', 'repeat: -1','repeat:-1']:
    if banned in alltext:errors.append(f'Banned pattern found: {banned}')
scenes={'typography-landscape':(1920,1080,8),'typography-square':(1080,1080,8),'typography-portrait':(1080,1920,8),'kinetic-typography-demo':(1920,1080,20)}
for name,(w,h,dur) in scenes.items():
    text=(root/f'compositions/{name}.html').read_text()
    for attr,val in [('data-composition-id',name),('data-start','0'),('data-duration',str(dur)),('data-track-index','1'),('data-width',str(w)),('data-height',str(h))]:
        if f'{attr}="{val}"' not in text:errors.append(f'{name}: wrong/missing {attr}')
pkg=json.loads((root/'package.json').read_text())
if pkg.get('version')!='1.7.0-batch8':errors.append('Package version not advanced to Batch 8')
report={'status':'PASS' if not errors else 'FAIL','manifestCount':len(files),'previewCount':len(previews),'uniqueIds':len(set(ids)),'groups':groups,'masterRegistryCount':len(index),'categoryCounts':cats,'errors':errors,'warnings':warnings}
(root/'reports/batch8-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
