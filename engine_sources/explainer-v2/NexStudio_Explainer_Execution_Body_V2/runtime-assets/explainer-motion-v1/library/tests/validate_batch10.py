from pathlib import Path
import json,sys,re
from collections import Counter
root=Path(__file__).resolve().parents[1];errors=[]
files=sorted((root/'manifests/data-visualisations').glob('*.json'));previews=sorted((root/'previews/data-visualisations').glob('*.html'))
if len(files)!=54:errors.append(f'Expected 54 manifests, found {len(files)}')
if len(previews)!=54:errors.append(f'Expected 54 previews, found {len(previews)}')
ids=[];slugs=[];cats=Counter();subtypes=Counter()
for f in files:
 d=json.loads(f.read_text());ids.append(d.get('id'));slugs.append(d.get('slug'));cats[d.get('category')]+=1;subtypes[d.get('subtype')]+=1
 for k in ['id','name','version','category','subtype','slug','renderer','intents','keywords','paperStyles','aspectRatios','slots','dataSchema','itemLimits','states','duration','motionEnergy','compatibleMotions','soundTags','themeTokens','accessibilityLabel','sampleConfig']:
  if k not in d:errors.append(f'{f.name}: missing {k}')
 if d.get('category') not in ['data-visualisation','workflow-diagram']:errors.append(f'{f.name}: invalid category')
 if sorted(d.get('aspectRatios',[]))!=sorted(['16:9','1:1','9:16']):errors.append(f'{f.name}: ratios incomplete')
 if len(d.get('paperStyles',[]))<4:errors.append(f'{f.name}: paper styles incomplete')
 if len(d.get('compatibleMotions',[]))<3:errors.append(f'{f.name}: compatible motions incomplete')
 if d.get('jsonDriven') is not True or d.get('supportsVariableItems') is not True or d.get('supportsStateVariants') is not True:errors.append(f'{f.name}: JSON/state flags missing')
 if sorted(d.get('states',[]))!=sorted(['ready','empty','loading','unavailable']):errors.append(f'{f.name}: states incomplete')
 if d.get('category')=='data-visualisation':
  if d.get('animatesFromZero') is not True or d.get('usesTabularNumerals') is not True:errors.append(f'{f.name}: data flags missing')
  if sorted(d.get('supportsSigns',[]))!=sorted(['positive','neutral','negative']):errors.append(f'{f.name}: signs incomplete')
  if sorted(d.get('numberFormats',[]))!=sorted(['number','compact','currency','percent']):errors.append(f'{f.name}: formats incomplete')
 else:
  if d.get('animatesFromEmpty') is not True:errors.append(f'{f.name}: workflow empty animation missing')
if len(ids)!=len(set(ids)):errors.append('Duplicate IDs')
if len(slugs)!=len(set(slugs)):errors.append('Duplicate slugs')
if cats['data-visualisation']!=30:errors.append(f'Data count {cats["data-visualisation"]}')
if cats['workflow-diagram']!=24:errors.append(f'Workflow count {cats["workflow-diagram"]}')
index=json.loads((root/'manifests/index.json').read_text());master=Counter(x.get('category') for x in index)
expected={'foundation':40,'paper-object':40,'motion':32,'icon':172,'typography':24,'media-container':24,'data-visualisation':30,'workflow-diagram':24}
for k,v in expected.items():
 if master[k]!=v:errors.append(f'{k}: expected {v}, found {master[k]}')
if len(index)!=386:errors.append(f'Expected registry 386, found {len(index)}')
source=(root/'components/data-visualisations.js').read_text();scene=(root/'runtime/data-scene-demo.js').read_text()
for api in ['create','animate','update','setData','fitText','format','normalise','getDef']:
 if api not in source:errors.append('Missing API '+api)
for banned in ['Math.random(', 'Date.now(', 'repeat: -1','repeat:-1']:
 if banned in source+scene:errors.append('Banned pattern '+banned)
for d in [json.loads(x.read_text()) for x in files]:
 if d['category']=='data-visualisation' and f"case'{d['slug']}'" not in source and d['slug'] not in ['scorecard','kpi-cards','multiple-stat-summary','before-and-after-metric','data-table','matrix','two-axis-comparison']:
  errors.append('Missing data renderer '+d['slug'])
for name,w,h in [('data-story',1920,1080),('agent-workflow',1080,1080),('conversion-story',1080,1920)]:
 t=(root/f'compositions/{name}.html').read_text()
 for attr,val in [('data-composition-id',name),('data-start','0'),('data-duration','14'),('data-track-index','1'),('data-width',str(w)),('data-height',str(h))]:
  if f'{attr}="{val}"' not in t:errors.append(f'{name}: wrong {attr}')
for n in ['creator-growth.json','commerce-performance.json','agent-operations.json','research-orchestration.json','human-approval-pipeline.json','prompt-to-published-output.json']:
 try:json.loads((root/'assets/data'/n).read_text())
 except Exception as e:errors.append(f'{n}: invalid JSON {e}')
pkg=json.loads((root/'package.json').read_text())
if pkg.get('version')!='1.9.0-batch10':errors.append('Package version incorrect')
report={'status':'PASS' if not errors else 'FAIL','manifestCount':len(files),'previewCount':len(previews),'uniqueIds':len(set(ids)),'categoryCounts':dict(cats),'subtypes':dict(subtypes),'masterRegistryCount':len(index),'masterCategoryCounts':dict(master),'sampleDatasets':3,'workflowExamples':3,'errors':errors}
(root/'reports/batch10-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
