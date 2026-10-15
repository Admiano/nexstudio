#!/usr/bin/env python3
"""Fail-closed SceneBam image-level wardrobe coverage QA.

Frozen production proof profile: actual Blender V21 orthographic 420x640 frames.
Look for exposed skin-colored islands inside opaque female trouser areas on
front, 3/4, and gesture frames. This does not certify wider cloth collisions,
character likeness, pose naturalness, or production VM parity.
"""
import json
import sys
from pathlib import Path
from PIL import Image

root = Path(sys.argv[1]) if len(sys.argv)>1 else Path('production-colour')
views = {
    'ORIGINAL-ORIGINAL':(220,255,490,540),
    'threeq-native':(235,265,490,540),
    'pose-338':(220,255,490,540),
    'pose-891':(220,255,490,540),
}
report={}
for variant in ('female-double-breasted','female-statement'):
    report[variant]={}
    for view,(left,right,top,bottom) in views.items():
        file=root/(variant+'-'+view+'.png')
        if not file.is_file():
            raise SystemExit('CAST_FORMAL_ART_PROOF_MISSING:'+str(file))
        with Image.open(file) as src:
            if src.size!=(420,640):
                raise SystemExit('CAST_FORMAL_ART_GATE_CAMERA_CHANGED:'+repr(src.size))
            pixels=src.convert('RGBA').load()
            hits=[]
            for y in range(top,bottom):
                for x in range(left,right):
                    r,g,b,alpha=pixels[x,y]
                    if alpha>=200 and r>175 and r>g>b and .68<g/r<.95 and .64<b/r<.89:
                        hits.append((x,y))
        report[variant][view]={'exposedSkinPixels':len(hits),
                              'bounds':([min(x for x,y in hits),min(y for x,y in hits),
                                         max(x for x,y in hits),max(y for x,y in hits)] if hits else None)}
(root/'art-gate-female-trouser.json').write_text(json.dumps(report,indent=2)+'\n')
print('SCENEBAM_FEMALE_TROUSER_ART_GATE',json.dumps(report),flush=True)
failed=[f'{variant}/{view}={d["exposedSkinPixels"]}' for variant,values in report.items()
        for view,d in values.items() if d['exposedSkinPixels']>20]
if failed:
    raise SystemExit('CAST_FORMAL_ART_EXPOSED_TROUSER_SKIN:'+','.join(failed))
print('CAST_FORMAL_ART_TROUSER_COVERAGE_PASS')
