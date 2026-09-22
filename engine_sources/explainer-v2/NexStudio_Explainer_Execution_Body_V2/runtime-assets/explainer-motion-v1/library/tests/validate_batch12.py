from pathlib import Path
import json,sys,re
root=Path(__file__).resolve().parents[1];errors=[]
required=['archival-photograph','document-reveal','newspaper-clipping','typed-letter','handwritten-note','date-stamp','location-stamp','evidence-label','redacted-document','highlighted-passage','quoted-passage','timeline-wall','investigation-board','relationship-map','photo-collage','memory-montage','chapter-divider','flashback-frame','then-versus-now','map-journey','event-sequence','character-introduction','object-close-up','historical-statistic','source-card','footnote-card','interview-quotation','audio-transcript-card','newspaper-headline','endnote','credits-page','closing-reflection']
mdir=root/'manifests/documentary-modules';pdir=root/'previews/documentary-modules';mans=[]
for p in sorted(mdir.glob('*.json')):
 try:mans.append(json.loads(p.read_text()))
 except Exception as e:errors.append(f'Invalid manifest {p.name}: {e}')
if len(mans)!=32:errors.append(f'Expected 32 manifests, found {len(mans)}')
if [m.get('slug') for m in mans]!=required:errors.append('Required module order or inventory mismatch')
if len({m.get('id') for m in mans})!=32:errors.append('Documentary IDs are not unique')
if len(list(pdir.glob('*.html')))!=32:errors.append('Expected 32 independent previews')
for m in mans:
 if m.get('moods')!=['warm','serious','investigative','celebratory']:errors.append(m['id']+' mood support invalid')
 if m.get('configurableMood') is not True:errors.append(m['id']+' missing configurableMood')
 if len(m.get('aspectRatios',[]))!=3:errors.append(m['id']+' aspect ratios invalid')
 if len(m.get('compatibleMotions',[]))<3:errors.append(m['id']+' motion compatibility insufficient')
 if not m.get('accessibilityLabel'):errors.append(m['id']+' accessibility label missing')
 if not m.get('slots',{}).get('source',{}).get('editable'):errors.append(m['id']+' source slot is not editable')
index=json.loads((root/'manifests/index.json').read_text())
if len(index)!=446:errors.append(f'Expected registry 446, found {len(index)}')
if sum(x.get('category')=='documentary-module' for x in index)!=32:errors.append('Master registry documentary count mismatch')
files=['components/documentary-modules.js','runtime/documentary-module-registry.js','runtime/documentary-module-explorer.js','runtime/documentary-scenes.js','styles/documentary-modules.css','styles/documentary-module-explorer.css','styles/documentary-scenes.css','documentary-module-explorer.html','DOCUMENTARY_MODULE_API.md','compositions/company-history.html','compositions/investigative-example.html','compositions/personal-memory.html']
for f in files:
 if not (root/f).exists():errors.append('Missing '+f)
for scene in ['company-history','investigative-example','personal-memory']:
 s=(root/f'compositions/{scene}.html').read_text()
 for token in ['data-composition-id','data-start="0"','data-duration="30"','data-track-index="1"']:
  if token not in s:errors.append(scene+' missing '+token)
source=(root/'components/documentary-modules.js').read_text()
for token in ['setRedactions','layoutConnectors','setMedia','setRoute','dm-route','dm-connectors','mark']:
 if token not in source:errors.append('Runtime missing '+token)
report={'status':'PASS' if not errors else 'FAIL','version':'2.0.0-batch12','moduleCount':len(mans),'previewCount':len(list(pdir.glob('*.html'))),'masterRegistryEntries':len(index),'errors':errors}
(root/'reports/batch12-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
