#!/usr/bin/env python3
"""Fail-closed image-level SceneBam wardrobe regression test.

Detect clearly wrong flesh-colored fragments inside the leg of the female suit
on the frozen 420x640, frame-27, front camera production-colour proof.
This is NOT a general body intersection or design-quality certification.
"""
import json
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(sys.argv[1]) if len(sys.argv)>1 else Path('production-colour')
FEMALE = ('female-double-breasted','female-statement')
REPORT = {}
for variant in FEMALE:
    name = ROOT/(variant+'-ORIGINAL-ORIGINAL.png')
    if not name.is_file():
        raise SystemExit('CAST_FORMAL_ART_PROOF_MISSING:'+str(name))
    with Image.open(name) as src:
        if src.size != (420,640):
            raise SystemExit('CAST_FORMAL_ART_GATE_CAMERA_CHANGED:'+repr(src.size))
        pix=src.convert('RGBA').load()
        holes=[]
        # Fixed screen-space patch: thigh fabric, below the hands and jacket,
        # away from any legitimately exposed human skin on the actual V21 host.
        for y in range(490,540):
            for x in range(220,255):
                r,g,b,alpha=pix[x,y]
                if alpha>=200 and r>175 and r>g>b and .68 < g/r < .95 and .64 < b/r < .89:
                    holes.append((x,y))
        REPORT[variant]={'fleshTintPixels':len(holes),
                         'bbox':[min((x for x,y in holes),default=-1),
                                 min((y for x,y in holes),default=-1),
                                 max((x for x,y in holes),default=-1),
                                 max((y for x,y in holes),default=-1)]}
(ROOT/'art-gate-female-trouser.json').write_text(json.dumps(REPORT,indent=2)+'\n')
print('SCENEBAM_FEMALE_TROUSER_ART_GATE',json.dumps(REPORT),flush=True)
for variant,entry in REPORT.items():
    # A few edge pixels are tolerated for antialiasing; a >20-pixel exposed
    # skin island inside opaque formal trousers is not.
    if entry['fleshTintPixels']>20:
        raise SystemExit('CAST_FORMAL_ART_EXPOSED_TROUSER_SKIN:'+variant+':'+str(entry['fleshTintPixels']))
print('CAST_FORMAL_ART_TROUSER_COVERAGE_PASS')
