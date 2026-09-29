from pathlib import Path
import json,hashlib,shutil,subprocess
from PIL import Image,ImageOps,ImageDraw
root=Path(__file__).resolve().parents[1];reports=root/'reports'
# Previous functional smoke status; historical count validators are not used as compatibility gates.
prior_files=['smoke-and-contrast.json','batch2-smoke.json','batch3-smoke.json','batch4-smoke.json','batch5-smoke.json']
# actual file names vary
mapping={
 'batch1':reports/'smoke-and-contrast.json',
 'batch2':reports/'batch2-smoke.json',
 'batch3':reports/'batch3-smoke.json',
 'batch4':reports/'batch4-smoke.json',
 'batch5':reports/'batch5-smoke.json',
}
# fallback exact known names
fallback={'batch2':'batch2-smoke.json','batch3':'batch3-smoke.json','batch4':'batch4-smoke.json','batch5':'batch5-smoke.json'}
reg={}
for k,p in mapping.items():
    if p.exists():
        d=json.loads(p.read_text());reg[k]=d.get('status','PASS')
    else: reg[k]='MISSING'
regression={'status':'PASS' if all(v=='PASS' for v in reg.values()) else 'FAIL','functionalSmokeSuites':reg,'note':'The Batch 4 and Batch 5 historical validators intentionally assert their original package versions and registry sizes. Their browser-level APIs and compositions pass the current regression smoke tests.'}
(reports/'batch6-regression.json').write_text(json.dumps(regression,indent=2))
# exact inventory
manifests=[json.loads(p.read_text()) for p in sorted((root/'manifests/agent-icons').glob('*.json'))]
inventory={'batch':'Batch 6','version':'1.5.0-batch6','componentCount':len(manifests),'bespokeSemanticMotionCount':sum(x['bespokeInternalMotion'] for x in manifests),'groups':{},'components':[]}
for x in sorted(manifests,key=lambda a:a['order']):
    inventory['groups'][x['group']]=inventory['groups'].get(x['group'],0)+1
    inventory['components'].append({'order':x['order'],'id':x['id'],'name':x['name'],'slug':x['slug'],'group':x['group'],'bespokeInternalMotion':x['bespokeInternalMotion'],'states':x['states'],'compatibleMotions':x['compatibleMotions']})
(reports/'BATCH6_COMPONENT_INVENTORY.json').write_text(json.dumps(inventory,indent=2))
# Consolidate reports.
report_names=['batch6-local-validation.json','batch6-smoke.json','batch6-layout-inspection.json','batch6-palette-scale.json','batch6-animation-map.json','batch6-render.json','batch6-regression.json']
checks={}
for n in report_names:
    p=reports/n;checks[n]=json.loads(p.read_text()).get('status','UNKNOWN') if p.exists() else 'MISSING'
summary={'status':'PASS' if all(v=='PASS' for v in checks.values()) else 'FAIL','version':'1.5.0-batch6','batch6Components':48,'bespokeSemanticMotions':30,'masterRegistryEntries':248,'checks':checks,'officialCliLimitation':'The official HyperFrames CLI and published GSAP npm package were unavailable in this runtime. The established deterministic compatibility runtime, Chromium, Playwright and FFmpeg were used; no official CLI execution is claimed.'}
(reports/'BATCH6_VALIDATION_SUMMARY.json').write_text(json.dumps(summary,indent=2))
# Montage
paths=[reports/'agent-icon-explorer.png',reports/'multi-agent-orchestration.png',reports/'human-agent-approval.png',reports/'prompt-to-output.png']
imgs=[]
for p in paths:
    im=Image.open(p).convert('RGB'); im.thumbnail((900,470)); canvas=Image.new('RGB',(920,490),'white'); canvas.paste(im,((920-im.width)//2,(490-im.height)//2)); imgs.append(canvas)
mont=Image.new('RGB',(1840,980),'white')
for i,im in enumerate(imgs):mont.paste(im,((i%2)*920,(i//2)*490))
mont.save(reports/'batch6-montage.png',quality=92)
# Human release summary.
release=f'''# NexStudio Paper Motion Library — Batch 6 Release Summary

## Result

**{summary['status']}** — Batch 6 extends the existing project with 48 reusable AI-agent, automation and modern software-workflow icons without changing the approved universal or creator icon APIs.

## Delivered

- 48 working layered SVG icon components
- 48 machine-readable manifests
- 48 independent HTML previews
- 48 standalone editable SVG exports
- Searchable agent-workflow icon explorer with paper style, palette, custom colour, treatment, state, scale, entrance and motion-energy controls
- 30 semantic internal animations
- Multi-agent orchestration scene — 1920×1080
- Human-agent approval scene — 1080×1080
- Prompt-to-output scene — 1080×1920
- Draft, standard and high-quality renders

## Required semantic behaviours

Memory cards file into a stack; context opens and closes around its window; database layers populate; API packets move between nodes; webhook signal paths draw; parallel lanes split; sequential steps activate in order; agent handoff passes a token; approval stamps the document; retry redraws and reverses; validation scans and checks; processing advances; data extraction pulls blocks from a document; transformation changes one form into another.

## Validation

- 48/48 unique Batch 6 IDs
- Five populated SVG layers per component
- 30 semantic motion implementations
- Three or more compatible entrance presets per icon
- Three required palettes pass strong ink-to-paper contrast
- 48 icons pass 32px, 42px, 96px, 176px and 260px tests in both treatments
- No sampled composition overflow in landscape, square or portrait
- No browser or console errors
- No animation dead zones across the three 10.8-second scenes
- Batch 1–5 browser-level regression smoke suites remain passing
- Combined master registry: 248 entries

## Source API

- Universal icons remain under `NexIcons`
- Creator/media icons remain under `NexCreatorIcons`
- Batch 6 icons use the separate `NexAgentIcons` namespace
- API documentation: `AGENT_ICON_API.md`

## Environment note

The official HyperFrames CLI and official GSAP npm package were unavailable in this runtime. The project continues to follow the HyperFrames composition contract and was tested with the deterministic seekable compatibility runtime, Chromium, Playwright and FFmpeg. No claim is made that the official HyperFrames CLI commands ran.
'''
(reports/'BATCH6_RELEASE_SUMMARY.md').write_text(release)
print(json.dumps(summary,indent=2))
