#!/usr/bin/env python3
"""Build a review sheet using only genuine rendered Blender PNGs, never synthesis."""
import sys, json, hashlib, base64
from pathlib import Path
root=Path(sys.argv[1])
names=("female-double-breasted","female-statement","male-jacket-tie","male-double-breasted","male-navy-classic","male-dinner-jacket")
rows=[]
for name in names:
    folder=root/name
    meta=json.loads((folder/"build_provenance.json").read_text())
    qa=json.loads((folder/"current-rig-qa.json").read_text())
    assert meta["variant"]==name
    assert meta["approvedCharacterSource"].endswith(("_v3.blend","_v6.blend"))
    assert len(qa["testedFrames"])==10 and qa["status"].startswith("STRUCTURAL_QA_PASS")
    images=[]
    for suffix in ("front","threeq","pose-338","pose-891"):
        p=folder/f"{name}-{suffix}.png"
        assert p.is_file() and p.read_bytes()[:8]==b"\x89PNG\r\n\x1a\n"
        images.append({"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    rows.append({"name":name,"gender":meta["gender"],"approvedSource":meta["approvedCharacterSource"],"approvedSourceSHA256":meta["approvedCharacterSourceSha256"],"qa":qa["status"],"images":images})
(root/"CURRENT_SOURCE_REAL_REFIT_PROVENANCE.json").write_text(json.dumps({"claim":"Six existing CC0 garments rebuilt against v3/v6 current approved body source in Blender","notClaimed":"Live deployment, pixel identity to v21 renderer, body/contact clearance, final visual art approval","results":rows},indent=2)+"\n")
try:
    from PIL import Image,ImageDraw,ImageFont
except ImportError:
    Image=None
if Image is not None:
    W,H=2000,1400
    sheet=Image.new("RGB",(W,H),"#F6F5F3")
    draw=ImageDraw.Draw(sheet)
    draw.text((36,24),"SceneBam — Real Blender formalwear fitted to the upgraded approved cast",fill="#171717")
    draw.text((36,51),"Current approved v3/v6 body sources; visual collision approval and v21 deployment NOT certified",fill="#565656")
    for col,name in enumerate(names):
        x=25+col*330
        for row,suffix in enumerate(("front","threeq")):
            im=Image.open(root/name/f"{name}-{suffix}.png").convert("RGBA")
            im.thumbnail((292,580))
            ox=x+(292-im.width)//2
            oy=92+row*625+(565-im.height)//2
            sheet.paste(im,(ox,oy),im)
        draw.text((x,1320),name,fill="#151515")
    path=root/"SCENEBAM_REAL_CURRENT_CAST_SIX_OUTFIT_PREVIEWS.png"
    sheet.save(path)
    print("REAL_RENDER_SHEET",path,flush=True)
else:
    W,H=2000,1400
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="1400" viewBox="0 0 2000 1400">','<rect width="2000" height="1400" fill="#f6f5f3"/>','<text x="36" y="40" fill="#171717" font-size="25">SceneBam — Real approved-body Blender formalwear</text>','<text x="36" y="68" fill="#565656" font-size="17">Structural QA only; live deployment / collisions unverified</text>']
    for col,name in enumerate(names):
        x=25+col*330
        for row,suffix in enumerate(("front","threeq")):
            data=base64.b64encode((root/name/f"{name}-{suffix}.png").read_bytes()).decode("ascii")
            svg.append(f'<image x="{x}" y="{95+row*620}" width="290" height="580" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>')
        svg.append(f'<text x="{x}" y="1350" fill="#171717" font-size="17">{name}</text>')
    svg.append("</svg>")
    p=root/"SCENEBAM_REAL_CURRENT_CAST_SIX_OUTFIT_PREVIEWS.svg"
    p.write_text("\n".join(svg))
    print("REAL_RENDER_SHEET",p,flush=True)
