#!/usr/bin/env python3
"""Rebuild real NexStudio V1 formal cast trials from original 163-bone characters.

Example:
  python scripts/illustrated-family/build_formal_cast.py --list
  python scripts/illustrated-family/build_formal_cast.py \
      --variant female-double-breasted --blender /opt/blender/blender \
      --output-dir /tmp/formal-proof

This is an isolated trial builder; it never modifies canonical .blend sources,
their rigs, performance actions, existing cast presets, or production services.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SUITS_URL="https://files2.makehumancommunity.org/asset_packs/suits01/suits01_cc0.zip"
SUITS_SHA="2b1d8676f3863b188e9eea98c1d8f234543d54c440e791d92b819f8ee1861f19"
SHOES_URL="https://files2.makehumancommunity.org/asset_packs/shoes01/shoes01_cc0.zip"
SHOES_SHA="ded3f70428505eabbf1f6d7b5f61196a7366ef20757103d276ad0ed336c35ada"
VARIANTS={
 "female-double-breasted":("female","toigo_female_double-breasted_suit"),
 "female-statement":("female","toigo_female_suit_2"),
 "male-jacket-tie":("male","toigo_male_suit_tie_and_jacket"),
 "male-double-breasted":("male","toigo_male_double-breasted_suit"),
 "male-navy-classic":("male","toigo_male_suit_3"),
 "male-dinner-jacket":("male","toigo_suit_with_dinner_jacket"),
}
SCENE_DIR=ROOT/"engine_sources/makehuman-lineart/presenters_v1/scenes"
EXPERIMENT=ROOT/"experiments/illustrated-family"
PREVIEW=ROOT/"scripts/illustrated-family-preview/quick_preview.py"

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()

def obtain_archive(url:str,digest:str,store:Path,offline:bool)->Path:
    store.mkdir(parents=True,exist_ok=True)
    archive=store/url.rsplit("/",1)[-1]
    if not archive.is_file():
        if offline:raise RuntimeError("ARCHIVE_MISSING_OFFLINE:"+str(archive))
        tmp=archive.with_suffix(archive.suffix+".part")
        try:
            with urllib.request.urlopen(url,timeout=90) as src,tmp.open("wb") as out:
                shutil.copyfileobj(src,out)
            tmp.replace(archive)
        finally:
            if tmp.exists():tmp.unlink()
    actual=sha256(archive)
    if actual!=digest:
        raise RuntimeError(f"ARCHIVE_SHA256_MISMATCH:{archive.name}:{actual}")
    return archive

def extract_verified(archive:Path,destination:Path)->None:
    destination.mkdir(parents=True,exist_ok=True)
    resolved=destination.resolve()
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            candidate=(destination/item.filename).resolve()
            if candidate!=resolved and resolved not in candidate.parents:
                raise RuntimeError("UNSAFE_UPSTREAM_ARCHIVE_PATH:"+item.filename)
        z.extractall(destination)

def verify_blender(binary:Path)->str:
    result=subprocess.run([str(binary),"--version"],capture_output=True,text=True,check=True)
    line=result.stdout.splitlines()[0]
    if not line.startswith("Blender 5.2.0"):
        raise RuntimeError("BLENDER_VERSION_NOT_CERTIFIED:"+line)
    return line

def source_scene(gender:str,dest:Path)->tuple[Path,str]:
    packed=SCENE_DIR/f"NEXSTUDIO_V1_{gender.upper()}.blend"
    if not packed.is_file():raise FileNotFoundError(packed)
    header=packed.open("rb").read(7)
    output=dest/f"canonical-original-{gender}.blend"
    if header==b"BLENDER":
        shutil.copyfile(packed,output)
    else:
        try:
            with output.open("wb") as sink:
                subprocess.run(["zstd","-q","-d","-c",str(packed)],stdout=sink,check=True)
        except FileNotFoundError as e:
            raise RuntimeError("ZSTANDARD_BINARY_REQUIRED_FOR_REPO_SOURCE") from e
        if output.open("rb").read(7)!=b"BLENDER":
            raise RuntimeError("SOURCE_SCENE_DECOMPRESSION_FAILURE")
    return output,sha256(packed)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--list",action="store_true",help="Print supported trials and exit")
    p.add_argument("--variant",choices=sorted(VARIANTS))
    p.add_argument("--blender",type=Path,default=Path(os.environ.get("BLENDER_BIN","blender")))
    p.add_argument("--output-dir",type=Path)
    p.add_argument("--archive-cache",type=Path,default=ROOT/".cache/v1-illustrated-cc0-donors")
    p.add_argument("--offline",action="store_true",help="Never download missing archives")
    args=p.parse_args()
    if args.list:
        print(json.dumps({k:{"gender":v[0],"donor":v[1],"status":"experimental_not_integrated"} for k,v in VARIANTS.items()},indent=2))
        return
    if not args.variant or args.output_dir is None:
        p.error("--variant and --output-dir are required without --list")
    blender=shutil.which(str(args.blender)) or str(args.blender)
    name=verify_blender(Path(blender))
    gender,donor=VARIANTS[args.variant]
    output=args.output_dir.expanduser().resolve()
    output.mkdir(parents=True,exist_ok=True)
    for path in [EXPERIMENT/"donor_suit_fit_uv.py",
                 EXPERIMENT/"shoe_female_cc0_fit.py",
                 EXPERIMENT/"suit_illustrated_finish_trial.py",
                 EXPERIMENT/"wardrobe_threeq.py",
                 EXPERIMENT/"donor_suit_pose_qa.py",PREVIEW]:
        if not path.is_file():raise RuntimeError("BUILDER_SCRIPT_MISSING:"+str(path))
    suits=obtain_archive(SUITS_URL,SUITS_SHA,args.archive_cache,args.offline)
    shoes=obtain_archive(SHOES_URL,SHOES_SHA,args.archive_cache,args.offline)
    with tempfile.TemporaryDirectory(prefix="nexstudio-formal-") as tmp:
        work=Path(tmp)
        scene,scene_hash=source_scene(gender,work)
        extract_verified(suits,work/"suits01")
        extract_verified(shoes,work/"shoes01")
        garment=work/"suits01/clothes"/donor/(donor+".mhclo")
        flats=work/"shoes01/clothes/toigo_ballet_flats/toigo_ballet_flats.mhclo"
        for asset in (garment,flats):
            if not asset.is_file():raise RuntimeError("PINNED_DONOR_ASSET_NOT_IN_ARCHIVE:"+str(asset))
            if "# license CC0" not in asset.read_text(errors="replace")[:1500]:
                raise RuntimeError("UPSTREAM_ASSET_CC0_HEADER_MISSING:"+asset.name)
        still=output/(args.variant+"-front.png")
        command=[
            str(blender),"-b",str(scene),"-t","4","--python-exit-code","1",
            "--python",str(EXPERIMENT/"donor_suit_fit_uv.py"),
            "--python",str(EXPERIMENT/"shoe_female_cc0_fit.py"),
            "--python",str(EXPERIMENT/"suit_illustrated_finish_trial.py"),
            "--python",str(PREVIEW),
            "--python",str(EXPERIMENT/"wardrobe_threeq.py"),
            "--python",str(EXPERIMENT/"donor_suit_pose_qa.py"),
            "--",gender,str(still),str(garment),str(flats),
        ]
        with (output/"blender-render.log").open("w") as log:
            subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=2400)
    files=[still,
          still.with_suffix(".blend"),
          output/(args.variant+"-threeq.png"),
          output/(args.variant+"-pose-338.png"),
          output/(args.variant+"-pose-891.png")]
    for file in files:
        if not file.is_file() or file.stat().st_size<4096:
            raise RuntimeError("EXPECTED_ACTUAL_BLENDER_PROOF_MISSING:"+str(file))
    summary={
        "variant":args.variant,"gender":gender,"donor":donor,
        "upstreamArchiveSha256":{"suits":SUITS_SHA,"shoes":SHOES_SHA},
        "originalSceneSha256":scene_hash,
        "blenderVersion":name,
        "outputStatus":"REAL_GEOMETRY_PROOF_UNAPPROVED_NOT_IN_PRODUCTION",
        "files":[{"name":f.name,"bytes":f.stat().st_size,"sha256":sha256(f)} for f in files]
    }
    (output/"build_provenance.json").write_text(json.dumps(summary,indent=2))
    print("NEXSTUDIO_REAL_V1_FORMAL_CAST_BUILT",json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
