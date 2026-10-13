#!/usr/bin/env python3
"""Contact sheet from genuine Blender renders on corrected-character scenes only."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(sys.argv[1])
names=("female-double-breasted","female-statement","male-jacket-tie","male-double-breasted","male-navy-classic","male-dinner-jacket")
rows=[]
W,H=1980,1500
out=Image.new("RGB",(W,H),"#f7f7f6")
d=ImageDraw.Draw(out)
d.text((30,20),"SceneBam — CORRECTED V17 CHARACTERS — Blender formalwear refit",fill="#111111")
d.text((30,43),"These are the corrected self-contained Cast scenes, NOT v3/v6 raw base; NOT certified live v21 parity",fill="#555555")
for i,name in enumerate(names):
    folder=root/name
    meta=json.loads((folder/"build_provenance.json").read_text())
    qa=json.loads((folder/"current-rig-qa.json").read_text())
    assert meta["correctedCharacterSource"].startswith("engine_sources/makehuman-lineart/character_system/scenes/")
    assert qa["status"].startswith("STRUCTURAL_QA_PASS")
    images=[]
    for j,shot in enumerate(("front","threeq","pose-338","pose-891")):
        path=folder/(name+"-"+shot+".png")
        raw=path.read_bytes()
        assert raw.startswith(b"\\x89PNG\\r\\n\\x1a\\n")
        images.append({"name":path.name,"sha256":hashlib.sha256(raw).hexdigest()})
        if j<2:
            im=Image.open(path).convert("RGBA")
            im.thumbnail((280,620))
            x=20+325*i+(280-im.width)//2
            y=75+650*j
            out.paste(im,(x,y),im)
    d.text((25+325*i,1430),name,fill="#111111")
    rows.append({"variant":name,"source":meta["correctedCharacterSource"],"sha256":meta["correctedSceneSHA256"],"QA":qa["status"],"images":images})
out.save(root/"SCENEBAM_CORRECTED_CAST_SIX_FORMAL_REAL_BLENDER_PREVIEWS.png")
(root/"SCENEBAM_CORRECTED_CHARACTER_FIT_MANIFEST.json").write_text(json.dumps({"source":"Corrected V17 self-contained character_system scenes","liveParity":"UNVERIFIED","visualApproval":"PENDING","results":rows},indent=2))
print("CORRECTED_CHARACTER_RENDER_CONTACT_SHEET_OK",root,flush=True)
