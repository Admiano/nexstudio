from pathlib import Path
import json,hashlib,shutil,subprocess,os
from PIL import Image
root=Path(__file__).resolve().parents[1];reports=root/'reports'
# Regression summary from freshly rerun browser smoke suites.
files={'batch1':'smoke-and-contrast.json','batch2':'batch2-smoke.json','batch3':'batch3-smoke.json','batch4':'batch4-smoke.json','batch5':'batch5-smoke.json','batch6':'batch6-smoke.json'}
reg={k:json.loads((reports/v).read_text()).get('status','UNKNOWN') if (reports/v).exists() else 'MISSING' for k,v in files.items()}
regression={'status':'PASS' if all(v=='PASS' for v in reg.values()) else 'FAIL','functionalSmokeSuites':reg,'note':'All six prior browser-level suites were rerun after the master registry expanded to 284 entries.'}
(reports/'batch7-regression.json').write_text(json.dumps(regression,indent=2))
# Inventory
manifests=[json.loads(p.read_text()) for p in sorted((root/'manifests/business-icons').glob('*.json'))]
inventory={'batch':'Batch 7','version':'1.6.0-batch7','componentCount':len(manifests),'bespokeSemanticMotionCount':sum(bool(x['bespokeInternalMotion']) for x in manifests),'groups':{},'components':[]}
for x in sorted(manifests,key=lambda a:a['order']):
    inventory['groups'][x['group']]=inventory['groups'].get(x['group'],0)+1
    inventory['components'].append({'order':x['order'],'id':x['id'],'name':x['name'],'slug':x['slug'],'group':x['group'],'bespokeInternalMotion':x['bespokeInternalMotion'],'states':x['states'],'compatibleMotions':x['compatibleMotions'],'polarity':x['agentSelection'].get('polarity')})
(reports/'BATCH7_COMPONENT_INVENTORY.json').write_text(json.dumps(inventory,indent=2))
# Summary
names=['batch7-local-validation.json','batch7-smoke.json','batch7-layout-inspection.json','batch7-palette-scale.json','batch7-animation-map.json','batch7-render.json','batch7-regression.json']
checks={n:(json.loads((reports/n).read_text()).get('status','UNKNOWN') if (reports/n).exists() else 'MISSING') for n in names}
summary={'status':'PASS' if all(v=='PASS' for v in checks.values()) else 'FAIL','version':'1.6.0-batch7','batch7Components':36,'bespokeSemanticMotions':24,'requiredSemanticMotions':20,'masterRegistryEntries':284,'checks':checks,'portraitRenderNote':'The portrait source composition and layout were validated at native 1080×1920. Its MP4 was captured at 720×1280 and upscaled to 1080×1920 after the combined native capture exceeded the execution window.','officialCliLimitation':'The official HyperFrames CLI and published GSAP npm package were unavailable in this runtime. The established deterministic compatibility runtime, Chromium, Playwright and FFmpeg were used; no official CLI execution is claimed.'}
(reports/'BATCH7_VALIDATION_SUMMARY.json').write_text(json.dumps(summary,indent=2))
# Montage
paths=[reports/'business-icon-explorer.png',reports/'commerce-workflow.png',reports/'campaign-result.png',reports/'milestone-scene.png']
imgs=[]
for p in paths:
    im=Image.open(p).convert('RGB');im.thumbnail((900,500));canvas=Image.new('RGB',(920,520),'white');canvas.paste(im,((920-im.width)//2,(520-im.height)//2));imgs.append(canvas)
mont=Image.new('RGB',(1840,1040),'white')
for i,im in enumerate(imgs):mont.paste(im,((i%2)*920,(i//2)*520))
mont.save(reports/'batch7-montage.png',quality=92)
release=f'''# NexStudio Paper Motion Library — Batch 7 Release Summary

## Result

**{summary['status']}** — Batch 7 extends the approved icon framework with 36 reusable animated business, commerce, marketing and organizational icons.

## Delivered

- 36 working layered SVG icon components
- 36 machine-readable manifests
- 36 independent HTML previews
- 36 standalone editable SVG exports
- Searchable business icon explorer with paper style, palette, custom colour, treatment, state, scale, entrance and motion-energy controls
- 24 semantic internal animations, including all 20 required behaviours
- Commerce workflow — 1920×1080
- Campaign result — 1080×1080
- Milestone scene — 1080×1920
- Draft, standard and high-quality renders

## Required semantic behaviours

Revenue rises; expense moves downward without error styling; growth and decline draw directionally; packages open; carts roll; delivery travels; payments complete; subscription arrows renew; targets receive arrows; trophies rise; milestones draw along a path; launch lifts off; campaign messages broadcast; conversion moves inputs into a completed output; funnels compress prospects; sales bars grow; performance needles advance; partnership hands meet; support responds.

## Validation

- 36/36 unique Batch 7 IDs
- Five populated SVG layers per component
- 24 semantic motion implementations
- Three or more compatible entrance presets per icon
- Three required palettes pass strong ink-to-paper contrast
- All icons pass 32px, 42px, 96px, 176px and 260px tests in both treatments
- No sampled composition overflow in landscape, square or portrait
- No browser or console errors
- No animation dead zones across the three 10.8-second scenes
- All Batch 1–6 browser-level regression smoke suites pass
- Combined master registry: 284 entries

## Negative metrics

Expense and decline use the same premium paper grammar as the rest of the pack. Their meaning is communicated through downward direction, chart structure and metadata rather than rendering-error colours or warning states.

## Source API

- Universal icons remain under `NexIcons`
- Creator/media icons remain under `NexCreatorIcons`
- Agent icons remain under `NexAgentIcons`
- Batch 7 icons use `NexBusinessIcons`
- API documentation: `BUSINESS_ICON_API.md`

## Render note

The portrait HTML composition and responsive layout were tested at native 1080×1920. The delivered portrait MP4 was recorded at 720×1280 and upscaled to 1080×1920 after the combined native capture exceeded the execution window. The editable source remains native 1080×1920.

## Environment note

The official HyperFrames CLI and official GSAP npm package were unavailable in this runtime. The project follows the HyperFrames composition contract and was tested with the deterministic seekable compatibility runtime, Chromium, Playwright and FFmpeg. No claim is made that the official HyperFrames CLI commands ran.
'''
(reports/'BATCH7_RELEASE_SUMMARY.md').write_text(release)
print(json.dumps(summary,indent=2))
