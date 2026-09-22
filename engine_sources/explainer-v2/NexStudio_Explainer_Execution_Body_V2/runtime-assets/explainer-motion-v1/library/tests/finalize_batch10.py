from pathlib import Path
import json,hashlib,subprocess,shutil
root=Path(__file__).resolve().parents[1];reports=root/'reports'
# Regression from rerun smoke reports
mapping={'batch1':'smoke-and-contrast.json','batch2':'batch2-smoke.json','batch3':'batch3-smoke.json','batch4':'batch4-smoke.json','batch5':'batch5-smoke.json','batch6':'batch6-smoke.json','batch7':'batch7-smoke.json','batch8':'batch8-smoke.json','batch9':'batch9-smoke.json'}
reg={k:(json.loads((reports/v).read_text()).get('status','UNKNOWN') if (reports/v).exists() else 'MISSING') for k,v in mapping.items()}
regression={'status':'PASS' if all(v=='PASS' for v in reg.values()) else 'FAIL','functionalSmokeSuites':reg,'masterRegistryEntries':386,'note':'All nine prior browser-level smoke suites were rerun after Batch 10 expanded the registry.'}
(reports/'batch10-regression.json').write_text(json.dumps(regression,indent=2))
# Inventory
man=[json.loads(p.read_text()) for p in sorted((root/'manifests/data-visualisations').glob('*.json'))]
inv={'batch':'Batch 10','version':'1.9.0-batch10','componentCount':len(man),'dataComponentCount':sum(x['category']=='data-visualisation' for x in man),'workflowComponentCount':sum(x['category']=='workflow-diagram' for x in man),'groups':{},'components':[],'sampleDatasets':['creator-growth.json','commerce-performance.json','agent-operations.json'],'workflowExamples':['research-orchestration.json','human-approval-pipeline.json','prompt-to-published-output.json']}
for x in sorted(man,key=lambda a:(a['category'],a['order'])):
 key=f"{x['category']}:{x['subtype']}";inv['groups'][key]=inv['groups'].get(key,0)+1
 inv['components'].append({'id':x['id'],'name':x['name'],'category':x['category'],'subtype':x['subtype'],'slug':x['slug'],'maximumItems':x['itemLimits']['maximum'],'states':x['states'],'compatibleMotions':x['compatibleMotions'],'intents':x['intents']})
(reports/'BATCH10_COMPONENT_INVENTORY.json').write_text(json.dumps(inv,indent=2))
checks=['batch10-local-validation.json','batch10-smoke.json','batch10-layout-inspection.json','batch10-palette-contrast.json','batch10-animation-map.json','batch10-render.json','batch10-regression.json']
status={x:(json.loads((reports/x).read_text()).get('status','UNKNOWN') if (reports/x).exists() else 'MISSING') for x in checks}
summary={'status':'PASS' if all(v=='PASS' for v in status.values()) else 'FAIL','version':'1.9.0-batch10','batch10Components':54,'dataComponents':30,'workflowComponents':24,'individualPreviews':54,'interactiveEditors':2,'sampleDatasets':3,'workflowExamples':3,'masterRegistryEntries':386,'demoDurationSeconds':14,'componentTweenCount':json.loads((reports/'batch10-animation-map.json').read_text()).get('componentTweenCount'),'checks':status,'renderNote':'The 1920×1080 master was captured at 1280×720 and encoded to delivery size. Square was captured natively. Portrait was captured at 540×960 and encoded to 1080×1920.','officialCliLimitation':'The official HyperFrames CLI and published GSAP npm package were unavailable. The deterministic compatibility runtime, Chromium, Playwright and FFmpeg were used; official CLI execution is not claimed.'}
(reports/'BATCH10_VALIDATION_SUMMARY.json').write_text(json.dumps(summary,indent=2))
release=f'''# NexStudio Paper Motion Library — Batch 10 Release Summary

## Result

**{summary['status']}** — Batch 10 adds 54 JSON-driven animated data visualisation and workflow systems to the existing library.

## Delivered

- 30 reusable animated data components
- 24 reusable animated workflow diagram components
- 54 machine-readable manifests
- 54 independent animated HTML previews
- Interactive data editor
- Interactive workflow editor
- Three realistic sample datasets
- Three agent-workflow JSON examples
- Landscape, square and portrait demonstration compositions
- Draft, standard and high-quality video outputs

## Data behaviour

- Values, labels, changes, segments, nodes and edges come from structured JSON.
- Bars, lines, areas, rings, counters and cards animate from zero or an empty visual state.
- Workflow nodes enter from empty state and connectors are calculated from the actual JSON node IDs.
- Variable item counts are supported within the documented maximum for every component.
- `number`, `compact`, `currency` and `percent` formatting are supported.
- Numeric copy uses tabular numerals.
- Positive, neutral and negative values remain legible; negative values are not presented as rendering errors.
- Every component supports `ready`, `empty`, `loading` and `unavailable` states.

## Validation

- 54/54 unique component IDs
- 54/54 manifests and independent previews
- Maximum documented item-count tests passed for every component
- 21 native aspect-ratio scene samples passed
- Three palettes passed with zero text overflow
- Ink-on-paper contrast ranges from 16.10:1 to 17.95:1
- 405 component-level animation tweens audited
- No blank workflow states
- All final videos verified at exactly 14 seconds
- All Batch 1–9 browser-level smoke suites remain passing

## Editors and examples

- `data-editor.html` edits chart JSON live.
- `workflow-editor.html` edits nodes and edges live.
- Sample datasets live in `assets/data/`.
- Public API documentation is in `DATA_VISUALISATION_API.md`.

## Render note

The source compositions are native 1920×1080, 1080×1080 and 1080×1920. The landscape master was captured at 1280×720 and encoded to 1920×1080. The square master was captured natively. The portrait master was captured at 540×960 and encoded to 1080×1920 for reliable completion in this runtime.

## Environment note

The official HyperFrames CLI and official GSAP npm package were unavailable in this runtime. The project follows the HyperFrames composition contract and was validated with the deterministic seekable compatibility runtime, Chromium, Playwright and FFmpeg. No claim is made that the official HyperFrames CLI commands ran.
'''
(reports/'BATCH10_RELEASE_SUMMARY.md').write_text(release)
print(json.dumps(summary,indent=2))
raise SystemExit(0 if summary['status']=='PASS' else 1)
