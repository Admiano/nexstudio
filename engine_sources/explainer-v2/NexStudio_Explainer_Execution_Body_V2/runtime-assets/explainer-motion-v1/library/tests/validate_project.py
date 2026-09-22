from pathlib import Path
import json,re,sys
root=Path(__file__).resolve().parents[1]
errors=[];warnings=[]
required=['DESIGN.md','LIBRARY_CONTRACT.md','MANIFEST_SCHEMA.md','MOTION_RULES.md','AUDIO_MAPPING.md','CHANGELOG.md','index.html','styles/tokens.css','runtime/foundation-registry.js','compositions/foundation-demo.html']
for f in required:
 if not (root/f).exists(): errors.append(f'Missing required file: {f}')
manifest_files=list((root/'manifests/components').glob('*.json'))
if len(manifest_files)!=40: errors.append(f'Expected 40 component manifests, found {len(manifest_files)}')
ids=[]
for f in manifest_files:
 try:d=json.loads(f.read_text())
 except Exception as e: errors.append(f'Invalid JSON {f.name}: {e}');continue
 for k in ['id','name','version','category','subtype','paperStyles','aspectRatios','duration','compatibleMotions','soundTags','themeTokens','accessibilityLabel']:
  if k not in d: errors.append(f'{f.name}: missing {k}')
 ids.append(d.get('id'))
 if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']):errors.append(f'{f.name}: aspect ratios incomplete')
if len(ids)!=len(set(ids)):errors.append('Duplicate component IDs')
index=json.loads((root/'manifests/index.json').read_text())
foundation_index=[x for x in index if x.get('category')=='foundation']
if len(foundation_index)!=len(manifest_files):errors.append('Foundation entries missing from combined manifest index')
text='\n'.join(p.read_text(errors='ignore') for p in root.rglob('*') if p.is_file() and p.suffix in {'.js','.html','.css'})
for banned in ['Math.random(', 'Date.now(', 'repeat: -1', 'repeat:-1']:
 if banned in text:errors.append(f'Banned non-deterministic pattern found: {banned}')
comp=(root/'compositions/foundation-demo.html').read_text()
for attr in ['data-composition-id','data-start','data-duration','data-track-index']:
 if attr not in comp: errors.append(f'Composition missing {attr}')
js=(root/'runtime/composition.js').read_text()
if "window.__timelines" not in js:errors.append('Timeline registry missing')
if 'paused:true' not in js.replace(' ',''):errors.append('Timeline does not start paused')
css=(root/'styles/tokens.css').read_text()
for token in ['--paper-bg','--paper-surface','--paper-surface-alt','--ink','--ink-muted','--primary','--secondary','--accent','--highlight','--shadow-color','--shadow-opacity','--grain-opacity','--outline-width']:
 if token not in css:errors.append(f'Missing token {token}')
report={'status':'PASS' if not errors else 'FAIL','manifestCount':len(manifest_files),'uniqueIds':len(set(ids)),'errors':errors,'warnings':warnings}
(root/'reports/local-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
sys.exit(1 if errors else 0)
