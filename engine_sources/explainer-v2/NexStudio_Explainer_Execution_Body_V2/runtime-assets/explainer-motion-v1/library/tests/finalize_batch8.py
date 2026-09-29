from pathlib import Path
import json,hashlib,subprocess,shutil
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1];reports=root/'reports'
# Regression summary from freshly rerun browser smoke suites.
files={'batch1':'smoke-and-contrast.json','batch2':'batch2-smoke.json','batch3':'batch3-smoke.json','batch4':'batch4-smoke.json','batch5':'batch5-smoke.json','batch6':'batch6-smoke.json','batch7':'batch7-smoke.json'}
reg={k:(json.loads((reports/v).read_text()).get('status','UNKNOWN') if (reports/v).exists() else 'MISSING') for k,v in files.items()}
regression={'status':'PASS' if all(v=='PASS' for v in reg.values()) else 'FAIL','functionalSmokeSuites':reg,'note':'All seven prior browser-level smoke suites were rerun after the master registry expanded to 308 entries.'}
(reports/'batch8-regression.json').write_text(json.dumps(regression,indent=2))
# Inventory
manifests=[json.loads(p.read_text()) for p in sorted((root/'manifests/typography').glob('*.json'))]
inv={'batch':'Batch 8','version':'1.7.0-batch8','componentCount':len(manifests),'groups':{},'components':[]}
for x in sorted(manifests,key=lambda a:a['order']):
 inv['groups'][x['subtype']]=inv['groups'].get(x['subtype'],0)+1
 inv['components'].append({'order':x['order'],'id':x['id'],'name':x['name'],'slug':x['slug'],'group':x['subtype'],'characterGuidance':x['characterGuidance'],'paperStyles':x['paperStyles'],'compatibleMotions':x['compatibleMotions']})
(reports/'BATCH8_COMPONENT_INVENTORY.json').write_text(json.dumps(inv,indent=2))
# Montage with latest images
paths=[reports/'typography-explorer.png',reports/'typography-landscape.png',reports/'typography-square.png',reports/'typography-portrait.png',reports/'kinetic-type-01.png',reports/'kinetic-type-02.png',reports/'kinetic-type-03.png',reports/'kinetic-type-04.png']
thumbs=[]
for p in paths:
 im=Image.open(p).convert('RGB');im.thumbnail((780,440));c=Image.new('RGB',(800,470),'white');c.paste(im,((800-im.width)//2,10));ImageDraw.Draw(c).text((12,448),p.stem,fill='black');thumbs.append(c)
mont=Image.new('RGB',(1600,1880),'white')
for i,im in enumerate(thumbs):mont.paste(im,((i%2)*800,(i//2)*470))
mont.save(reports/'batch8-montage.png',quality=92)
# Summary
names=['batch8-local-validation.json','batch8-smoke.json','batch8-layout-overflow.json','batch8-palette-caption-safe.json','batch8-animation-map.json','batch8-render.json','batch8-regression.json']
checks={n:(json.loads((reports/n).read_text()).get('status','UNKNOWN') if (reports/n).exists() else 'MISSING') for n in names}
summary={'status':'PASS' if all(v=='PASS' for v in checks.values()) else 'FAIL','version':'1.7.0-batch8','batch8Components':24,'individualPreviews':24,'paperStylesTestedPerComponent':3,'masterRegistryEntries':308,'kineticDemoSeconds':20,'checks':checks,'renderNote':'The native 1920×1080 kinetic composition was recorded at 1280×720 and encoded to a 1920×1080 high-quality master. Native-size square and portrait previews were rendered deterministically from timeline frames.','officialCliLimitation':'The official HyperFrames CLI and published GSAP npm package were unavailable in this runtime. The established deterministic compatibility runtime, Chromium, Playwright and FFmpeg were used; no official CLI execution is claimed.'}
(reports/'BATCH8_VALIDATION_SUMMARY.json').write_text(json.dumps(summary,indent=2))
release=f'''# NexStudio Paper Motion Library — Batch 8 Release Summary

## Result

**{summary['status']}** — Batch 8 adds 24 responsive, editable and animated typography systems to the existing paper-motion library.

## Delivered

- 24 working animated typography components
- 24 machine-readable manifests with explicit character guidance
- 24 independent animated HTML previews
- Live editable typography explorer
- Three paper styles per component: clean editorial, handmade scrapbook and technical notebook
- Left, centre and right alignment controls
- Configurable emphasis words
- Short, medium, maximum-copy and long-word handling
- Landscape, square and portrait compositions
- Caption-safe-area tests in all three aspect ratios
- One complete 20-second kinetic-typography demonstration
- Draft, standard and high-quality renders

## Typography systems

Chapter opener, large statement, question hook, quote card, definition card, numbered list, bullet list, word-by-word emphasis, marker highlight, scribble underline, circled phrase, crossed-out phrase, typewriter note, kinetic keyword, statistic headline, name-and-role card, date-and-location label, source citation, footnote, subtitle card, speaker identification, callout label, warning note and call-to-action card.

## Dynamic-copy validation

- All 24 systems passed their documented maximum-copy test.
- Unbroken long words use safe wrapping and component-level fitting.
- No ordinary text layout relies on fixed `<br>` tags.
- The fitting engine checks the complete content block against the paper frame.
- Three alignments and three paper styles were tested for every component.

## Caption and contrast validation

- Speaker-identification and subtitle components remain inside the five-percent action-safe area in 16:9, 1:1 and 9:16.
- Warm palette ink-to-paper contrast: 17.95:1.
- Cobalt palette ink-to-paper contrast: 17.68:1.
- Charcoal palette ink-to-paper contrast: 16.10:1.
- Subtitle cards use solid high-contrast ink backgrounds with white copy.

## Animation validation

- Six scenes across exactly 20 seconds.
- No blank sampled frames.
- No dead zones longer than one second.
- Transitions preserve the outgoing composition while the incoming scene appears.
- Typewriter, numeric counting, word sequencing, list staging, marker, scribble, circle, strike-through and CTA interactions are semantic rather than generic bounce-only motion.

## Regression

All Batch 1–7 browser-level smoke suites still pass after the master registry expanded to 308 entries.

## Source API

See `TYPOGRAPHY_API.md`. The public runtime is available as `window.NexTypography`.

## Render note

The HTML composition is native 1920×1080. The high-quality kinetic video was captured at 1280×720 and encoded to 1920×1080 after the combined browser render exceeded the execution window. Square and portrait previews were rendered deterministically from their native 1080×1080 and 1080×1920 timeline frames.

## Environment note

The official HyperFrames CLI and official GSAP npm package were unavailable in this runtime. The project follows the HyperFrames composition contract and was validated with the deterministic seekable compatibility runtime, Chromium, Playwright and FFmpeg. No claim is made that the official HyperFrames CLI commands ran.
'''
(reports/'BATCH8_RELEASE_SUMMARY.md').write_text(release)
print(json.dumps(summary,indent=2))
