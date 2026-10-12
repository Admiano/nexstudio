#!/usr/bin/env python3
"""Build a composable actual Blender V1 illustrated character trial.

One original V1 female or male Host.rig, six verified CC0 suits, optional
individually-licensed CC0 hair source, optional copied hair color and optional
native facial-proportion morph. Nothing edits production or canonical .blends.

Examples:
 python scripts/illustrated-family/build_character_variant.py \
   --outfit female-statement --hair toigo_inverted_bob --color '#343034' \
   --face 1 --hair-root /tmp/cc0-hair-cache --blender /opt/blender/blender \
   --output-dir /tmp/nex-cast-combined

This is an experimental compositor CLI; no live editor/podcast certification.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FORMAL_BUILDER=ROOT/"scripts/illustrated-family/build_formal_cast.py"
EXPERIMENT=ROOT/"experiments/illustrated-family"
PREVIEW=ROOT/"scripts/illustrated-family-preview/quick_preview.py"
NATIVE_FACEVAR=ROOT/"engine_sources/makehuman-lineart/presenters_v1/scripts/facevar.py"
DONOR_INDEX=ROOT/"docs/illustrated-family/hair-inventory/Hair01_CURATED_GEOMETRY_MANIFEST.json"
OUTFITS={
 "female-double-breasted":"female","female-statement":"female",
 "male-jacket-tie":"male","male-double-breasted":"male",
 "male-navy-classic":"male","male-dinner-jacket":"male",
}
HAIRS={
 "female":("original","toigo_inverted_bob","toigo_curled_under_bob",
           "toigo_inverted_bob_with_bangs","toigo_blunt_bob_with_bangs"),
 "male":("original","faydaen_hair_1"),
}
def hashfile(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()
def find_donor(root:Path,name:str)->tuple[Path,dict]:
    manifest=json.loads(DONOR_INDEX.read_text())
    records=[a for a in manifest["assets"] if a["id"]==name]
    if len(records)!=1:raise RuntimeError("UNLICENSED_HAIR_DONOR:"+name)
    record=records[0]
    base=root/"hair" if (root/"hair").is_dir() else root
    # Both the user-supplied cache and the repo's immutable manifest are
    # independently verified before the source can reach Blender.
    mh=base/name/(name+".mhclo")
    obj=base/name/Path(record["objPath"]).name
    for path,expected in ((mh,record["sourceMhcloSha256"]),
                          (obj,record["sourceObjSha256"])):
        if not path.is_file() or hashfile(path)!=expected:
            raise RuntimeError("CC0_HAIR_SOURCE_HASH_MISMATCH:"+str(path))
    return mh,record
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list",action="store_true")
    parser.add_argument("--outfit",choices=sorted(OUTFITS))
    parser.add_argument("--hair",default="original")
    parser.add_argument("--hair-root",type=Path)
    parser.add_argument("--color",default=None,help="Six-character RGB HEX, only for alternate hair")
    parser.add_argument("--face",type=int,choices=(0,1,2),default=0,
                        help="Original native face (0) or proportion trial (1,2)")
    parser.add_argument("--blender",type=Path,default=Path(os.getenv("BLENDER_BIN","blender")))
    parser.add_argument("--archive-cache",type=Path,default=ROOT/".cache/v1-illustrated-cc0-donors")
    parser.add_argument("--offline",action="store_true")
    parser.add_argument("--output-dir",type=Path)
    args=parser.parse_args()
    if args.list:
        print(json.dumps({"outfits":OUTFITS,"hairPerGender":HAIRS,
             "faceOptions":[0,1,2],"colors":"#RRGGBB for alternate mesh only",
             "status":"EXPERIMENTAL_NOT_PRODUCTION"},indent=2))
        return
    if not args.outfit or not args.output_dir:
        parser.error("--outfit and --output-dir required")
    gender=OUTFITS[args.outfit]
    if args.hair not in HAIRS[gender]:
        parser.error("Hair not among individually licensed or visually reviewed options for "+gender)
    if args.color:
        code=args.color
        if args.hair=="original":
            parser.error("A specific CC0 alternate hair is required to tint without changing originals")
        if len(code)!=7 or not code.startswith("#") or any(c not in "0123456789abcdefABCDEF" for c in code[1:]):
            parser.error("--color must be #RRGGBB")
    if args.hair!="original" and not args.hair_root:
        parser.error("--hair-root required for an individually CC0-licensed hair option")
    label=(args.outfit+"__"+args.hair+"__face"+str(args.face)+
           "__"+(args.color[1:].upper() if args.color else "SOURCE")).replace("-","_")
    result=(args.output_dir/label).expanduser().resolve()
    result.mkdir(parents=True,exist_ok=True)
    still=result/(label+"-front.png")
    donor,provenance=(None,None)
    if args.hair!="original":
        donor,provenance=find_donor(args.hair_root.resolve(),args.hair)
    needed=[FORMAL_BUILDER,PREVIEW,EXPERIMENT/"donor_suit_pose_qa.py",
            EXPERIMENT/"wardrobe_threeq.py"]
    if args.face:
        needed += [NATIVE_FACEVAR,EXPERIMENT/"native_face_geometry_before.py",
                   EXPERIMENT/"native_face_geometry_after.py"]
    if donor:
        needed += [EXPERIMENT/"hair_cc0_rig_trial.py"]
    if args.color:
        needed += [EXPERIMENT/"cc0_hair_color_trial.py"]
    for p in needed:
        if not p.is_file():raise RuntimeError("MISSING_REPRODUCIBLE_V1_BUILDER_COMPONENT:"+str(p))
    blender=shutil.which(str(args.blender)) or str(args.blender)
    with tempfile.TemporaryDirectory(prefix="v1-cast-composer-") as tmp:
        work=Path(tmp)
        base=work/"verified-formal"
        cmd=[sys.executable,str(FORMAL_BUILDER),"--variant",args.outfit,
             "--blender",str(blender),"--archive-cache",str(args.archive_cache),
             "--output-dir",str(base)]
        if args.offline:cmd.append("--offline")
        with (result/"base-formal-builder.log").open("w") as log:
            base_run=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=2700)
        if base_run.returncode:
            raise RuntimeError("VERIFIED_FORMAL_BUILDER_FAILED:"+str(base_run.returncode)+
                "\n"+(result/"base-formal-builder.log").read_text(errors="replace")[-3200:])
        source=base/(args.outfit+"-front.blend")
        if not source.is_file():raise RuntimeError("BASE_FORMAL_EDITABLE_SCENE_MISSING")
        base_proof=json.loads((base/"build_provenance.json").read_text())
        scripts=[]
        if args.face:
            scripts.extend([EXPERIMENT/"native_face_geometry_before.py",NATIVE_FACEVAR,
                            EXPERIMENT/"native_face_geometry_after.py"])
        if donor:scripts.append(EXPERIMENT/"hair_cc0_rig_trial.py")
        if args.color:scripts.append(EXPERIMENT/"cc0_hair_color_trial.py")
        scripts.extend([PREVIEW,EXPERIMENT/"wardrobe_threeq.py",
                        EXPERIMENT/"donor_suit_pose_qa.py"])
        if not args.face and donor is None:
            shutil.copyfile(source,still.with_suffix(".blend"))
        run=[str(blender),"-b",str(source),"-t","4","--python-exit-code","1"]
        for path in scripts:run.extend(["--python",str(path)])
        run.extend(["--",gender,str(still),str(donor) if donor else "original",
                    args.color or "SOURCE"])
        env=os.environ.copy()
        env["FACE"]=str(args.face)
        with (result/"composite-blender-render.log").open("w") as log:
            execution=subprocess.run(run,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                                    env=env,timeout=2700)
        if execution.returncode:
            raise RuntimeError("ORIGINAL_RIG_CHARACTER_COMPOSITION_FAILED:"+str(execution.returncode)+
                "\n"+(result/"composite-blender-render.log").read_text(errors="replace")[-3200:])
    output_files=[still,still.with_suffix(".blend"),
                  still.with_name(still.stem.replace("-front","-threeq")+".png"),
                  still.with_name(still.stem.replace("-front","-pose-338")+".png"),
                  still.with_name(still.stem.replace("-front","-pose-891")+".png")]
    for file in output_files:
        if not file.is_file() or file.stat().st_size<4096:
            raise RuntimeError("COMBINED_ORIGINAL_RIG_OUTPUT_MISSING:"+str(file))
    if donor and not still.with_name(still.stem+"-hair.json").exists():
        raise RuntimeError("COMBINED_HAIR_MESH_FIT_REPORT_MISSING")
    if args.face and not still.with_name(still.stem+"-face-measurements.json").exists():
        raise RuntimeError("COMBINED_NATIVE_FACE_MORPH_REPORT_MISSING")
    if args.color and not still.with_name(still.stem+"-color-report.json").exists():
        raise RuntimeError("COMBINED_ALTERNATE_HAIR_COLOR_REPORT_MISSING")
    manifest={
      "schema":"nexstudio.illustrated.v1.composable-original-character-proof/1",
      "outfit":args.outfit,"gender":gender,"hair":args.hair,
      "hairDonorSourceSha256":provenance["sourceMhcloSha256"] if provenance else None,
      "hairSourceLicense":provenance["sourceLicense"] if provenance else None,
      "hairColor":args.color,"nativeFaceMorph":args.face,
      "originalSceneSha256":base_proof["originalSceneSha256"],
      "originalRig":"Host.rig", "sourceBuilder":"scripts/illustrated-family/build_formal_cast.py",
      "blenderVersion":base_proof["blenderVersion"],
      "originalPerformanceActionsReplaced":False,
      "productionStatus":"COMPOSABLE_EDITABLE_REAL_BLENDER_TRIAL_NOT_INTEGRATED",
      "files":[{"name":f.name,"bytes":f.stat().st_size,"sha256":hashfile(f)} for f in output_files]}
    (result/"character-composition-provenance.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("ORIGINAL_V1_FULL_CHARACTER_OPTION_COMPOSED",json.dumps(manifest,indent=2))
if __name__=="__main__":main()
