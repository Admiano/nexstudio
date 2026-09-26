from pathlib import Path
import json,sys
from collections import Counter
root=Path(__file__).resolve().parents[1];errors=[];warnings=[]
required=['media-container-explorer.html','runtime/media-container-registry.js','runtime/media-container-explorer.js','runtime/media-scene-demo.js','components/media-containers.js','styles/media-containers.css','styles/media-explorer.css','styles/media-scenes.css','MEDIA_CONTAINER_API.md','compositions/product-demo.html','compositions/creator-profile.html','compositions/photo-story.html']
for f in required:
    if not (root/f).exists():errors.append('Missing '+f)
files=sorted((root/'manifests/media').glob('*.json'));previews=sorted((root/'previews/media').glob('*.html'))
if len(files)!=24:errors.append(f'Expected 24 manifests, found {len(files)}')
if len(previews)!=24:errors.append(f'Expected 24 previews, found {len(previews)}')
ids=[];slugs=[];subtypes=Counter();required_fields=['id','name','version','category','subtype','slug','renderer','order','intents','keywords','paperStyles','aspectRatios','acceptedMedia','mediaSlots','slots','duration','motionEnergy','compatibleMotions','defaultMotion','soundTags','themeTokens','accessibilityLabel','replaceable','editable','scalable','agentSelection','contentAnimationIndependent','supportsLocalMedia','supportsConfigurableCrop','supportsFocalPoint','supportsBorderStyle']
for f in files:
    d=json.loads(f.read_text());ids.append(d.get('id'));slugs.append(d.get('slug'));subtypes[d.get('subtype')]+=1
    for k in required_fields:
        if k not in d:errors.append(f'{f.name}: missing {k}')
    if d.get('category')!='media-container':errors.append(f'{f.name}: wrong category')
    if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']):errors.append(f'{f.name}: ratios incomplete')
    if len(d.get('paperStyles',[]))<4:errors.append(f'{f.name}: styles incomplete')
    if len(d.get('compatibleMotions',[]))<3:errors.append(f'{f.name}: motions incomplete')
    if not d.get('acceptedMedia'):errors.append(f'{f.name}: no media types')
    for flag in ['replaceable','editable','scalable','agentSelection','contentAnimationIndependent','supportsLocalMedia','supportsConfigurableCrop','supportsFocalPoint','supportsBorderStyle']:
        if d.get(flag) is not True:errors.append(f'{f.name}: {flag} not true')
if len(ids)!=len(set(ids)):errors.append('Duplicate IDs')
if len(slugs)!=len(set(slugs)):errors.append('Duplicate slugs')
index=json.loads((root/'manifests/index.json').read_text());cats=Counter(x.get('category') for x in index)
expected={'foundation':40,'paper-object':40,'motion':32,'icon':172,'typography':24,'media-container':24}
for k,v in expected.items():
    if cats[k]!=v:errors.append(f'{k}: expected {v}, found {cats[k]}')
if len(index)!=332:errors.append(f'Expected registry 332, found {len(index)}')
source=(root/'components/media-containers.js').read_text()
for api in ['create','animate','replaceMedia','update','setCrop','setFocalPoint','setBorder','setStyle','fitText','getDef']:
    if api not in source:errors.append('Missing API '+api)
for slug in slugs:
    if f"case'{slug}'" not in source:errors.append('Missing renderer '+slug)
for banned in ['Math.random(', 'Date.now(', 'repeat: -1','repeat:-1']:
    if banned in source+(root/'runtime/media-scene-demo.js').read_text():errors.append('Banned pattern '+banned)
# inserted media must not be directly targeted by component animation
anim=source[source.find('function animate'):source.find('function replaceMedia')]
if "querySelector('.media-asset')" in anim or 'querySelectorAll(\'.media-asset\')' in anim:errors.append('Animation directly targets inserted media')
scenes={'product-demo':(1920,1080),'creator-profile':(1080,1080),'photo-story':(1080,1920)}
for name,(w,h) in scenes.items():
    t=(root/f'compositions/{name}.html').read_text()
    for attr,val in [('data-composition-id',name),('data-start','0'),('data-duration','12'),('data-track-index','1'),('data-width',str(w)),('data-height',str(h))]:
        if f'{attr}="{val}"' not in t:errors.append(f'{name}: wrong {attr}')
pkg=json.loads((root/'package.json').read_text())
if pkg.get('version')!='1.8.0-batch9':errors.append('Package version incorrect')
report={'status':'PASS' if not errors else 'FAIL','manifestCount':len(files),'previewCount':len(previews),'uniqueIds':len(set(ids)),'subtypes':dict(subtypes),'masterRegistryCount':len(index),'categoryCounts':dict(cats),'errors':errors,'warnings':warnings}
(root/'reports/batch9-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
