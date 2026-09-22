from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];warnings=[]
required=['creator-icon-explorer.html','runtime/creator-icon-registry.js','components/creator-icons.js','runtime/creator-icon-explorer.js','styles/creator-icons.css','styles/creator-explorer.css','styles/creator-scenes.css','runtime/creator-scene-demo.js','CREATOR_ICON_API.md','compositions/creator-workflow.html','compositions/media-production.html','compositions/publishing.html']
for f in required:
    if not (root/f).exists():errors.append(f'Missing Batch 5 file: {f}')
files=sorted((root/'manifests/creator-icons').glob('*.json'));previews=sorted((root/'previews/creator-icons').glob('*.html'));assets=sorted((root/'assets/icons/creator-media').glob('*.svg'))
if len(files)!=48:errors.append(f'Expected 48 manifests, found {len(files)}')
if len(previews)!=48:errors.append(f'Expected 48 previews, found {len(previews)}')
if len(assets)!=48:errors.append(f'Expected 48 SVG exports, found {len(assets)}')
ids=[];slugs=[];bespoke=[];groups={};stateful=[]
required_fields=['id','name','version','category','subtype','group','slug','renderer','intents','keywords','paperStyles','aspectRatios','slots','duration','motionEnergy','compatibleMotions','defaultMotion','states','treatments','soundTags','themeTokens','accessibilityLabel','layeredSvg','editable','scalable','bespokeInternalMotion','agentSelection']
for f in files:
    try:d=json.loads(f.read_text())
    except Exception as e:errors.append(f'Invalid JSON {f.name}: {e}');continue
    for k in required_fields:
        if k not in d:errors.append(f'{f.name}: missing {k}')
    ids.append(d.get('id'));slugs.append(d.get('slug'));groups[d.get('group')]=groups.get(d.get('group'),0)+1
    if d.get('bespokeInternalMotion'):bespoke.append(d.get('slug'))
    if 'completed' in d.get('states',[]):stateful.append(d.get('slug'))
    if d.get('category')!='icon' or d.get('subtype')!='creator-media':errors.append(f'{f.name}: wrong category/subtype')
    if len(d.get('compatibleMotions',[]))<3:errors.append(f'{f.name}: fewer than 3 motions')
    if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']):errors.append(f'{f.name}: aspect ratios incomplete')
    if sorted(d.get('treatments',[]))!=sorted(['paper-cutout','printed-outline']):errors.append(f'{f.name}: treatments incomplete')
    if not all(d.get(k) is True for k in ['layeredSvg','editable','scalable']):errors.append(f'{f.name}: source flags invalid')
    if len(d.get('keywords',[]))<5 or len(d.get('intents',[]))<2:errors.append(f'{f.name}: weak agent metadata')
    if not d.get('accessibilityLabel'):errors.append(f'{f.name}: missing accessibility label')
if len(ids)!=len(set(ids)):errors.append('Duplicate creator icon IDs')
if len(slugs)!=len(set(slugs)):errors.append('Duplicate creator icon slugs')
expected={'camera','video-camera','microphone','speaker','audio-waveform','storyboard','timeline','caption','crop','layers','transition','render','export','livestream','subscriber','view-count','analytics','publish'}
if set(bespoke)!=expected:errors.append(f'Bespoke set mismatch: {sorted(bespoke)}')
index=json.loads((root/'manifests/index.json').read_text());cats={};subtypes={}
for x in index:
    cats[x.get('category')]=cats.get(x.get('category'),0)+1
    if x.get('category')=='icon':subtypes[x.get('subtype')]=subtypes.get(x.get('subtype'),0)+1
if len(index)!=200:errors.append(f'Expected master registry 200, found {len(index)}')
for k,v in {'foundation':40,'paper-object':40,'motion':32,'icon':88}.items():
    if cats.get(k)!=v:errors.append(f'Category {k}: expected {v}, found {cats.get(k)}')
if subtypes!={'universal':40,'creator-media':48}:errors.append(f'Icon subtype counts wrong: {subtypes}')
source=(root/'components/creator-icons.js').read_text()
for api in ['create','animate','setState','setTreatment','setSize','update','CombinedTimeline']:
    if api not in source:errors.append(f'Missing creator API: {api}')
for layer in ['icon-shadow-layer','icon-paper-layer','icon-symbol-layer','icon-accent-layer','icon-state-layer']:
    if layer not in source:errors.append(f'Missing SVG layer: {layer}')
for slug in expected:
    if f"case '{slug}'" not in source:errors.append(f'Missing bespoke builder: {slug}')
newtext='\n'.join((root/f).read_text(errors='ignore') for f in required if (root/f).exists())+'\n'+source
for banned in ['Math.random(', 'Date.now(', 'repeat: -1','repeat:-1']:
    if banned in newtext:errors.append(f'Banned pattern found: {banned}')
scenes={'creator-workflow':(1920,1080,'16:9'),'media-production':(1080,1080,'1:1'),'publishing':(1080,1920,'9:16')}
for name,(w,h,ratio) in scenes.items():
    text=(root/f'compositions/{name}.html').read_text()
    for attr,val in [('data-composition-id',name),('data-start','0'),('data-duration','10.2'),('data-track-index','1'),('data-width',str(w)),('data-height',str(h))]:
        if f'{attr}="{val}"' not in text:errors.append(f'{name}: wrong/missing {attr}')
    if text.count('data-icon=')!=7:errors.append(f'{name}: expected 7 icon nodes')
pkg=json.loads((root/'package.json').read_text())
if pkg.get('version')!='1.4.0-batch5':errors.append('Package version not advanced to Batch 5')
report={'status':'PASS' if not errors else 'FAIL','manifestCount':len(files),'previewCount':len(previews),'editableSvgCount':len(assets),'uniqueIds':len(set(ids)),'bespokeCount':len(bespoke),'statefulCount':len(stateful),'groups':groups,'masterRegistryCount':len(index),'categoryCounts':cats,'iconSubtypeCounts':subtypes,'errors':errors,'warnings':warnings}
(root/'reports/batch5-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
