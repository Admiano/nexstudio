from pathlib import Path
import json,sys,re
root=Path(__file__).resolve().parents[1];errors=[]
required=['social-post','thread','comment-exchange','creator-profile','subscriber-counter','view-counter','engagement-summary','content-calendar','publishing-checklist','thumbnail-selector','video-chapters','newsletter-card','podcast-episode','blog-article','community-poll','question-and-answer-card','testimonial','review','user-generated-content-frame','reaction-panel','creator-collaboration','sponsorship-card','brand-partnership','campaign-result','affiliate-result','link-in-bio-screen','call-to-follow','call-to-subscribe']
mdir=root/'manifests/creator-modules';pdir=root/'previews/creator-modules';mans=[]
for p in sorted(mdir.glob('*.json')):
 try:mans.append(json.loads(p.read_text()))
 except Exception as e:errors.append(f'Invalid manifest {p.name}: {e}')
if len(mans)!=28:errors.append(f'Expected 28 manifests, found {len(mans)}')
ids=[x.get('id') for x in mans];slugs=[x.get('slug') for x in mans]
if len(set(ids))!=28:errors.append('Manifest IDs are not unique')
if slugs!=required:errors.append('Required module order or inventory mismatch')
if len(list(pdir.glob('*.html')))!=28:errors.append('Expected 28 independent previews')
for m in mans:
 for k in ['platformNeutral','authorizedLogoSlot','replaceableContent','composedFromLowerLevelComponents']:
  if m.get(k) is not True:errors.append(f"{m.get('id')} missing {k}")
 if m.get('thirdPartyLogosBakedIn') is not False:errors.append(f"{m.get('id')} third-party logo flag invalid")
 if m.get('contentStates')!=['short','medium','long']:errors.append(f"{m.get('id')} content states invalid")
 if len(m.get('aspectRatios',[]))!=3:errors.append(f"{m.get('id')} aspect ratios invalid")
 if len(m.get('compatibleMotions',[]))<3:errors.append(f"{m.get('id')} motion compatibility insufficient")
 if not m.get('accessibilityLabel'):errors.append(f"{m.get('id')} accessibility label missing")
index=json.loads((root/'manifests/index.json').read_text())
if len(index)!=414:errors.append(f'Expected master registry 414, found {len(index)}')
if sum(x.get('category')=='creator-module' for x in index)!=28:errors.append('Master registry creator-module count mismatch')
files=['components/creator-modules.js','runtime/creator-module-registry.js','runtime/creator-module-explorer.js','runtime/creator-module-scenes.js','styles/creator-modules.css','styles/creator-module-explorer.css','styles/creator-module-scenes.css','creator-module-explorer.html','CREATOR_MODULE_API.md','compositions/creator-growth-recap.html','compositions/sponsorship-announcement.html','compositions/publishing-workflow.html']
for f in files:
 if not (root/f).exists():errors.append('Missing '+f)
source='\n'.join((root/f).read_text().lower() for f in ['components/creator-modules.js','runtime/creator-module-registry.js','styles/creator-modules.css'])
for brand in ['instagram','tiktok','twitter','facebook','youtube','linkedin']:
 if brand in source:errors.append('Baked platform reference: '+brand)
for scene in ['creator-growth-recap','sponsorship-announcement','publishing-workflow']:
 s=(root/f'compositions/{scene}.html').read_text()
 for token in ['data-composition-id','data-start="0"','data-duration="12"','data-track-index="1"']:
  if token not in s:errors.append(f'{scene} missing {token}')
report={'status':'PASS' if not errors else 'FAIL','version':'2.0.0-batch11','moduleCount':len(mans),'previewCount':len(list(pdir.glob('*.html'))),'masterRegistryEntries':len(index),'errors':errors}
(root/'reports/batch11-local-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
