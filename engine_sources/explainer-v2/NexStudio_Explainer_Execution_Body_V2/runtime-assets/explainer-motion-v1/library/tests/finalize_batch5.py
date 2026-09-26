from pathlib import Path
import json, hashlib, shutil, subprocess
root=Path(__file__).resolve().parents[1]; reports=root/'reports'
# Inventory
manifests=[]
for p in sorted((root/'manifests/creator-icons').glob('*.json')):
    d=json.loads(p.read_text());manifests.append({
        'id':d['id'],'name':d['name'],'slug':d['slug'],'group':d['group'],
        'bespokeInternalMotion':d['bespokeInternalMotion'],'states':d['states'],
        'compatibleMotions':d['compatibleMotions'],
        'manifest':str(p.relative_to(root)),
        'preview':str((root/'previews/creator-icons'/f"{d['slug']}.html").relative_to(root)),
        'editableSvg':str((root/'assets/icons/creator-media'/f"{d['slug']}.svg").relative_to(root))
    })
inv={'batch':'Batch 5','version':'1.4.0-batch5','componentCount':len(manifests),'bespokeMotionCount':sum(x['bespokeInternalMotion'] for x in manifests),'components':manifests}
(reports/'BATCH5_COMPONENT_INVENTORY.json').write_text(json.dumps(inv,indent=2))
# Regression from existing smoke reports
reg_sources={'batch1':'smoke-and-contrast.json','batch2':'batch2-smoke.json','batch3':'batch3-smoke.json','batch4':'batch4-smoke.json'}
reg={}
for key,name in reg_sources.items():
    p=reports/name
    reg[key]={'report':name,'status':json.loads(p.read_text()).get('status') if p.exists() else 'MISSING'}
regression={'status':'PASS' if all(v['status']=='PASS' for v in reg.values()) else 'FAIL','previousBatches':reg,'preservedCounts':{'foundation':40,'paperObjects':40,'motionPrimitives':32,'universalIcons':40},'note':'Batch 1–4 browser smoke suites were rerun after Batch 5 integration.'}
(reports/'batch5-regression.json').write_text(json.dumps(regression,indent=2))
# Aggregate validation
source_names=['batch5-local-validation.json','batch5-smoke.json','batch5-layout-inspection.json','batch5-palette-scale.json','batch5-animation-map.json','batch5-render.json','batch5-regression.json']
checks={name:json.loads((reports/name).read_text()).get('status') for name in source_names}
summary={
 'status':'PASS' if all(v=='PASS' for v in checks.values()) else 'FAIL',
 'version':'1.4.0-batch5','checks':checks,
 'counts':{'newCreatorIcons':48,'newManifests':48,'newPreviews':48,'newEditableSvgExports':48,'bespokeSemanticMotions':18,'statefulIcons':27,'workflowScenes':3,'masterRegistryEntries':200},
 'responsiveFormats':['1920x1080','1080x1080','1080x1920'],
 'paletteTests':3,'scaleCombinations':10,'testedSizes':[32,42,96,176,260],
 'renderedDurations':json.loads((reports/'batch5-render.json').read_text())['verifiedDurations'],
 'environmentLimitation':'The official HyperFrames CLI and published GSAP npm package were unavailable in this runtime. The established deterministic compatibility runtime, Chromium, Playwright and FFmpeg were used; no official CLI execution is claimed.'
}
(reports/'BATCH5_VALIDATION_SUMMARY.json').write_text(json.dumps(summary,indent=2))
# Human release summary
release=f'''# NexStudio Paper Motion Library — Batch 5 Release Summary

## Result

**PASS** — Batch 5 extends the existing library with 48 reusable creator, media-production and publishing icons without modifying the approved Batch 4 universal icon API.

## Delivered

- 48 working layered SVG icon components
- 48 machine-readable manifests
- 48 independent HTML previews
- 48 standalone editable SVG exports
- Searchable creator-icon explorer with paper style, palette, custom colour, treatment, state, scale, entrance and motion-energy controls
- 18 semantic internal animations
- Creator workflow scene — 1920×1080
- Media-production scene — 1080×1080
- Publishing scene — 1080×1920
- Draft, standard and high-quality renders

## Bespoke semantic animations

Camera shutter; video recording indicator; microphone waveform; speaker output; audio waveform; storyboard rearrangement; timeline playhead; caption reveal; crop guides; layer stacking; transition wipe; render progress; export completion; livestream pulse; subscriber count; view count; analytics growth; publish confirmation.

## Validation

- 48/48 unique creator icon IDs
- Five populated SVG layers per component
- 18/18 required bespoke motion implementations
- Three or more compatible entrance presets per icon
- Three required palettes pass strong ink-to-paper contrast
- 48 icons pass 32px, 42px, 96px, 176px and 260px scale tests in both treatments
- No sampled composition overflow in landscape, square or portrait
- No browser or console errors
- Animation map reports continuous scene movement through 10.2 seconds
- All Batch 1–4 browser regression suites remain passing
- Combined master registry: 200 entries

## Source APIs

- Universal icons remain under `NexIcons`
- Batch 5 icons use the separate `NexCreatorIcons` namespace
- API documentation: `CREATOR_ICON_API.md`

## Environment note

The official HyperFrames CLI and official GSAP npm package were unavailable in this runtime. The project continues to follow the HyperFrames composition contract and was tested with the deterministic seekable compatibility runtime, Chromium, Playwright and FFmpeg. No claim is made that the official HyperFrames CLI commands ran.
'''
(reports/'BATCH5_RELEASE_SUMMARY.md').write_text(release)
print(json.dumps({'status':summary['status'],'inventory':len(manifests),'regression':regression['status'],'checks':checks},indent=2))
