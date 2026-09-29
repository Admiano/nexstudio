from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];warnings=[]
required=['business-icon-explorer.html','runtime/business-icon-registry.js','components/business-icons.js','runtime/business-icon-explorer.js','styles/business-icons.css','styles/business-explorer.css','styles/business-scenes.css','runtime/business-scene-demo.js','BUSINESS_ICON_API.md','compositions/commerce-workflow.html','compositions/campaign-result.html','compositions/milestone-scene.html']
for f in required:
    if not (root/f).exists():errors.append(f'Missing Batch 7 file: {f}')
files=sorted((root/'manifests/business-icons').glob('*.json'));previews=sorted((root/'previews/business-icons').glob('*.html'));assets=sorted((root/'assets/icons/business-commerce').glob('*.svg'))
if len(files)!=36:errors.append(f'Expected 36 manifests, found {len(files)}')
if len(previews)!=36:errors.append(f'Expected 36 previews, found {len(previews)}')
if len(assets)!=36:errors.append(f'Expected 36 SVG exports, found {len(assets)}')
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
    if d.get('category')!='icon' or d.get('subtype')!='business-commerce':errors.append(f'{f.name}: wrong category/subtype')
    if len(d.get('compatibleMotions',[]))<3:errors.append(f'{f.name}: fewer than 3 motions')
    if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']):errors.append(f'{f.name}: aspect ratios incomplete')
    if sorted(d.get('treatments',[]))!=sorted(['paper-cutout','printed-outline']):errors.append(f'{f.name}: treatments incomplete')
    if not all(d.get(k) is True for k in ['layeredSvg','editable','scalable']):errors.append(f'{f.name}: source flags invalid')
    if len(d.get('keywords',[]))<6 or len(d.get('intents',[]))<2:errors.append(f'{f.name}: weak agent metadata')
    if not d.get('accessibilityLabel'):errors.append(f'{f.name}: missing accessibility label')
if len(ids)!=len(set(ids)):errors.append('Duplicate business icon IDs')
if len(slugs)!=len(set(slugs)):errors.append('Duplicate business icon slugs')
required_bespoke={'revenue','expense','growth','decline','package','shopping-cart','delivery','payment','subscription','target','trophy','milestone','launch','campaign','conversion','funnel','sales','performance','partnership','support'}
if not required_bespoke.issubset(set(bespoke)):errors.append(f'Missing required semantic motion: {sorted(required_bespoke-set(bespoke))}')
if len(bespoke)<20:errors.append(f'Expected at least 20 bespoke motions, found {len(bespoke)}')
index=json.loads((root/'manifests/index.json').read_text());cats={};subtypes={}
for x in index:
    cats[x.get('category')]=cats.get(x.get('category'),0)+1
    if x.get('category')=='icon':subtypes[x.get('subtype')]=subtypes.get(x.get('subtype'),0)+1
if len(index)!=284:errors.append(f'Expected master registry 284, found {len(index)}')
for k,v in {'foundation':40,'paper-object':40,'motion':32,'icon':172}.items():
    if cats.get(k)!=v:errors.append(f'Category {k}: expected {v}, found {cats.get(k)}')
expected_sub={'universal':40,'creator-media':48,'agent-automation':48,'business-commerce':36}
if subtypes!=expected_sub:errors.append(f'Icon subtype counts wrong: {subtypes}')
source=(root/'components/business-icons.js').read_text()
for api in ['create','animate','setState','setTreatment','setSize','update','CombinedTimeline']:
    if api not in source:errors.append(f'Missing business API: {api}')
for layer in ['icon-shadow-layer','icon-paper-layer','icon-symbol-layer','icon-accent-layer','icon-state-layer']:
    if layer not in source:errors.append(f'Missing SVG layer: {layer}')
for slug in required_bespoke:
    if f"case '{slug}'" not in source:errors.append(f'Missing semantic builder: {slug}')
newtext='\n'.join((root/f).read_text(errors='ignore') for f in required if (root/f).exists())+'\n'+source
for banned in ['Math.random(', 'Date.now(', 'repeat: -1','repeat:-1']:
    if banned in newtext:errors.append(f'Banned pattern found: {banned}')
scenes={'commerce-workflow':(1920,1080),'campaign-result':(1080,1080),'milestone-scene':(1080,1920)}
for name,(w,h) in scenes.items():
    text=(root/f'compositions/{name}.html').read_text()
    for attr,val in [('data-composition-id',name),('data-start','0'),('data-duration','10.8'),('data-track-index','1'),('data-width',str(w)),('data-height',str(h))]:
        if f'{attr}="{val}"' not in text:errors.append(f'{name}: wrong/missing {attr}')
    if text.count('data-icon=')!=8:errors.append(f'{name}: expected 8 icon nodes')
pkg=json.loads((root/'package.json').read_text())
if pkg.get('version')!='1.6.0-batch7':errors.append('Package version not advanced to Batch 7')
report={'status':'PASS' if not errors else 'FAIL','manifestCount':len(files),'previewCount':len(previews),'editableSvgCount':len(assets),'uniqueIds':len(set(ids)),'bespokeCount':len(bespoke),'statefulCount':len(stateful),'groups':groups,'masterRegistryCount':len(index),'categoryCounts':cats,'iconSubtypeCounts':subtypes,'errors':errors,'warnings':warnings}
(root/'reports/batch7-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
