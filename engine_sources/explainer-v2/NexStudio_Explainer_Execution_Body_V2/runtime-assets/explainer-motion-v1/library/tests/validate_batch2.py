from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1]
errors=[];warnings=[]
required=['index.html','foundation-explorer.html','components/paper-objects.js','styles/objects.css','styles/object-composition.css','runtime/object-registry.js','runtime/object-explorer.js','runtime/object-demo.js','compositions/paper-objects-demo.html']
for f in required:
    if not (root/f).exists(): errors.append(f'Missing required Batch 2 file: {f}')
files=sorted((root/'manifests/objects').glob('*.json'))
if len(files)!=40:errors.append(f'Expected 40 object manifests, found {len(files)}')
ids=[];renderers=[];bespoke=0;attachments=0
for f in files:
    try:d=json.loads(f.read_text())
    except Exception as e:errors.append(f'Invalid JSON {f.name}: {e}');continue
    for k in ['id','name','version','category','subtype','renderer','paperStyles','aspectRatios','slots','duration','motionEnergy','compatibleMotions','defaultMotion','soundTags','themeTokens','accessibilityLabel']:
        if k not in d:errors.append(f'{f.name}: missing {k}')
    ids.append(d.get('id'));renderers.append(d.get('renderer'))
    if len(d.get('compatibleMotions',[]))<3:errors.append(f'{f.name}: fewer than 3 compatible motions')
    if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']):errors.append(f'{f.name}: aspect ratios incomplete')
    if d.get('bespokeMotion'):bespoke+=1
    if d.get('attachable'):attachments+=1
if len(ids)!=len(set(ids)):errors.append('Duplicate object IDs')
if len(renderers)!=len(set(renderers)):errors.append('Duplicate object renderers')
if bespoke<10:errors.append(f'Expected at least 10 bespoke motions, found {bespoke}')
if attachments!=6:errors.append(f'Expected 6 independent attachments, found {attachments}')
previews=list((root/'previews/objects').glob('*.html'))
if len(previews)!=40:errors.append(f'Expected 40 individual object previews, found {len(previews)}')
index=json.loads((root/'manifests/index.json').read_text())
if len([x for x in index if x.get('category') in {'foundation','paper-object'}])!=80:errors.append(f'Expected 80 preserved Batch 1-2 entries, found {len([x for x in index if x.get("category") in {"foundation","paper-object"}])}')
text='\n'.join(p.read_text(errors='ignore') for p in root.rglob('*') if p.is_file() and p.suffix in {'.js','.html','.css'})
for banned in ['Math.random(', 'Date.now(', 'repeat: -1','repeat:-1']:
    if banned in text:errors.append(f'Banned pattern found: {banned}')
for api in ['create','animate','attachTo','fitText']:
    if api not in (root/'components/paper-objects.js').read_text():errors.append(f'Missing public API: {api}')
comp=(root/'compositions/paper-objects-demo.html').read_text()
for attr in ['data-composition-id','data-start','data-duration','data-track-index','data-width','data-height']:
    if attr not in comp:errors.append(f'Demo composition missing {attr}')
js=(root/'runtime/object-demo.js').read_text().replace(' ','')
if 'window.__timelines' not in js:errors.append('Object demo timeline registry missing')
if 'paused:true' not in js:errors.append('Object demo timeline does not start paused')
report={'status':'PASS' if not errors else 'FAIL','objectManifestCount':len(files),'combinedRegistryCount':len(index),'uniqueObjectIds':len(set(ids)),'individualPreviews':len(previews),'bespokeMotionCount':bespoke,'attachmentCount':attachments,'errors':errors,'warnings':warnings}
(root/'reports/batch2-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
