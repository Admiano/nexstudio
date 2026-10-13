#!/usr/bin/env python3
"""Refit original CC0 formal donor garments onto corrected V17 SceneBam Cast character scenes.
Isolated Blender trial; do NOT claim pixel identity to deployed v21 or live approval.
"""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILDER=ROOT/"scripts/illustrated-family/build_formal_cast.py"
SYSTEM=ROOT/"engine_sources/makehuman-lineart/character_system"
CHOICES={"female":"female/sheath/character.blend","male":"male/shirt/character.blend"}
spec=importlib.util.spec_from_file_location("upstream_formal_bank_builder",BUILDER)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def verified_corrected_scene(gender:str,dest:Path):
    relative=CHOICES[gender]
    scene=SYSTEM/"scenes"/relative
    recorded=json.loads((SYSTEM/"scene-verification.json").read_text())
    expected=next((x for x in recorded if x.get("path")=="engine_sources/makehuman-lineart/character_system/scenes/"+relative),None)
    if expected is None:raise RuntimeError("CORRECTED_SCENE_PROVENANCE_MISSING:"+relative)
    dest.mkdir(parents=True,exist_ok=True)
    output=dest/("SCENEBAM_V17_CORRECTED_"+gender+".blend")
    if scene.exists():
        shutil.copyfile(scene,output)
    else:
        parts=sorted(scene.parent.glob("character.blend.part*"))
        if not parts:raise RuntimeError("CORRECTED_SCENE_PARTS_MISSING:"+relative)
        with output.open("wb") as sink:
            for part in parts:
                with part.open("rb") as src:shutil.copyfileobj(src,sink)
    digest=mod.sha256(output)
    if digest!=expected["sha256"]:
        raise RuntimeError("CORRECTED_SCENE_SHA_MISMATCH:"+relative+":"+digest)
    if output.open("rb").read(7)!=b"BLENDER":
        import subprocess
        decoded=output.with_suffix(".decoded.blend")
        with decoded.open("wb") as sink:
            subprocess.run(["zstd","-q","-d","-c",str(output)],stdout=sink,check=True)
        if decoded.open("rb").read(7)!=b"BLENDER":
            raise RuntimeError("CORRECTED_SCENE_DECODING_FAILURE:"+relative)
        decoded.replace(output)
    return output,digest

mod.source_scene=verified_corrected_scene
mod.main()
if "--list" in sys.argv:sys.exit(0)
variant=sys.argv[sys.argv.index("--variant")+1]
folder=Path(sys.argv[sys.argv.index("--output-dir")+1])
p=folder/"build_provenance.json"
r=json.loads(p.read_text())
gender=r["gender"]
relative=CHOICES[gender]
r.update({
 "product":"SceneBam",
 "fitTarget":"Corrected complete Character System V17 source scene, female sheath / male shirt (not v3/v6 raw canonical)",
 "correctedCharacterSource":"engine_sources/makehuman-lineart/character_system/scenes/"+relative,
 "correctedSceneSHA256":r["originalSceneSha256"],
 "notClaimed":["live v21 parity","all apparel contact clearance","deployment","visual approval"],
 "shipped":False,
 "visualAcceptance":"REQUIRES_ART_REVIEW"
})
p.write_text(json.dumps(r,indent=2)+"\n")
print("SCENEBAM_CORRECTED_CHARACTER_FORMAL_REFIT_COMPLETE",variant, r["originalSceneSha256"],flush=True)
