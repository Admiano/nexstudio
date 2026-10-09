"""Blender hook: build isolated rigged waistcoat trial before rendering."""
import bpy, json, sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from wardrobe_trial import build_waistcoat
args=sys.argv[sys.argv.index("--")+1:]
gender,output=args[:2]
assert gender in ("female","male")
report=build_waistcoat(gender)
base=Path(output).resolve()
base.parent.mkdir(parents=True,exist_ok=True)
scene_path=base.with_name(base.stem+".blend")
bpy.ops.wm.save_as_mainfile(filepath=str(scene_path),compress=True,copy=True)
report["scene_path"]=str(scene_path)
report["blender"]=bpy.app.version_string
report["source_scene"]=bpy.data.filepath
report["render_image"]=str(base)
base.with_suffix(".json").write_text(json.dumps(report,indent=2))
print("WARDROBE_PROOF_SCENE_SAVED",scene_path,flush=True)
