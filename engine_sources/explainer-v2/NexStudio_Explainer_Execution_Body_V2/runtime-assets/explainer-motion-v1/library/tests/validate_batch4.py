from pathlib import Path
import json,re,sys
root=Path(__file__).resolve().parents[1];errors=[];warnings=[]
required=['icon-explorer.html','runtime/icon-registry.js','components/universal-icons.js','runtime/icon-explorer.js','styles/icons.css','styles/icon-explorer.css','styles/icon-composition.css','styles/icon-dock.css','runtime/icon-aspect-demo.js','runtime/icon-dock-demo.js','compositions/universal-icons-landscape.html','compositions/universal-icons-square.html','compositions/universal-icons-portrait.html','compositions/icon-dock-demo.html']
for f in required:
    if not (root/f).exists(): errors.append(f'Missing Batch 4 file: {f}')
files=sorted((root/'manifests/icons').glob('*.json'))
if len(files)!=40: errors.append(f'Expected 40 icon manifests, found {len(files)}')
previews=sorted((root/'previews/icons').glob('*.html'))
if len(previews)!=40: errors.append(f'Expected 40 individual previews, found {len(previews)}')
svg_assets=sorted((root/'assets/icons/universal').glob('*.svg'))
if len(svg_assets)!=40: errors.append(f'Expected 40 editable SVG assets, found {len(svg_assets)}')
ids=[];slugs=[];bespoke=[];stateful=[]
required_fields=['id','name','version','category','subtype','slug','renderer','intents','keywords','paperStyles','aspectRatios','slots','duration','motionEnergy','compatibleMotions','defaultMotion','states','treatments','soundTags','themeTokens','accessibilityLabel','layeredSvg','editable','scalable','bespokeInternalMotion','agentSelection']
for f in files:
    try:d=json.loads(f.read_text())
    except Exception as e: errors.append(f'Invalid JSON {f.name}: {e}');continue
    for k in required_fields:
        if k not in d: errors.append(f'{f.name}: missing {k}')
    ids.append(d.get('id'));slugs.append(d.get('slug'))
    if d.get('category')!='icon' or d.get('subtype')!='universal': errors.append(f'{f.name}: wrong category/subtype')
    if len(d.get('compatibleMotions',[]))<3: errors.append(f'{f.name}: fewer than three motion presets')
    if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']): errors.append(f'{f.name}: incomplete aspect ratios')
    if sorted(d.get('treatments',[]))!=sorted(['paper-cutout','printed-outline']): errors.append(f'{f.name}: incomplete treatments')
    if not all(d.get(k) is True for k in ['layeredSvg','editable','scalable']): errors.append(f'{f.name}: layered/editable/scalable flags invalid')
    if not d.get('accessibilityLabel'): errors.append(f'{f.name}: empty accessibility label')
    if len(d.get('keywords',[]))<5 or len(d.get('intents',[]))<2: errors.append(f'{f.name}: weak agent metadata')
    if d.get('bespokeInternalMotion'): bespoke.append(d.get('slug'))
    if 'completed' in d.get('states',[]): stateful.append(d.get('slug'))
if len(ids)!=len(set(ids)): errors.append('Duplicate icon IDs')
if len(slugs)!=len(set(slugs)): errors.append('Duplicate icon slugs')
expected_bespoke={'search','save','share','download','upload','refresh','lock','unlock','check','warning','calendar','clock','play','favourite','bookmark'}
if set(bespoke)!=expected_bespoke: errors.append(f'Bespoke set mismatch: {sorted(bespoke)}')
index=json.loads((root/'manifests/index.json').read_text());cats={}
for x in index: cats[x.get('category')]=cats.get(x.get('category'),0)+1
if len(index)!=152: errors.append(f'Expected master registry 152, found {len(index)}')
expected_cats={'foundation':40,'paper-object':40,'motion':32,'icon':40}
for k,v in expected_cats.items():
    if cats.get(k)!=v: errors.append(f'Category {k}: expected {v}, found {cats.get(k)}')
source=(root/'components/universal-icons.js').read_text()
for api in ['create','animate','setState','setTreatment','setSize','update','CombinedTimeline']:
    if api not in source: errors.append(f'Missing icon API: {api}')
for layer in ['icon-shadow-layer','icon-paper-layer','icon-symbol-layer','icon-accent-layer','icon-state-layer']:
    if layer not in source: errors.append(f'Missing SVG layer: {layer}')
for slug in expected_bespoke:
    if f"case '{slug}'" not in source: errors.append(f'Missing bespoke animation builder: {slug}')
new_text='\n'.join((root/f).read_text(errors='ignore') for f in required if (root/f).exists())+'\n'+source
for banned in ['Math.random(', 'Date.now(', 'repeat: -1','repeat:-1']:
    if banned in new_text: errors.append(f'Banned pattern found: {banned}')
for ratio,(w,h) in {'landscape':(1920,1080),'square':(1080,1080),'portrait':(1080,1920)}.items():
    text=(root/f'compositions/universal-icons-{ratio}.html').read_text()
    for attr,val in [('data-composition-id',None),('data-start','0'),('data-duration','8.7'),('data-track-index','1'),('data-width',str(w)),('data-height',str(h))]:
        if attr not in text: errors.append(f'{ratio} composition missing {attr}')
        if val and f'{attr}="{val}"' not in text: errors.append(f'{ratio} composition has wrong {attr}')
dock=(root/'compositions/icon-dock-demo.html').read_text()
for attr in ['data-composition-id','data-start','data-duration','data-track-index','data-width','data-height']:
    if attr not in dock: errors.append(f'Dock composition missing {attr}')
package=json.loads((root/'package.json').read_text())
if package.get('version')!='1.3.0-batch4': errors.append('Package version not advanced to Batch 4')
report={'status':'PASS' if not errors else 'FAIL','iconManifestCount':len(files),'previewCount':len(previews),'editableSvgAssetCount':len(svg_assets),'uniqueIconIds':len(set(ids)),'bespokeMotionCount':len(bespoke),'completedStateCount':len(stateful),'masterRegistryCount':len(index),'categoryCounts':cats,'errors':errors,'warnings':warnings}
(root/'reports/batch4-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
