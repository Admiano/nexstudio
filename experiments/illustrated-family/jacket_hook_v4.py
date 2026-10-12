"""Generate V4 jacket only from a disposable canonical Blender scene."""
import bpy, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from jacket_trial_v4 import build_jacket
args=sys.argv[sys.argv.index("--")+1:]
gender,render_path=args[:2]
record=build_jacket(gender)
out=Path(render_path).resolve()
out.parent.mkdir(parents=True,exist_ok=True)
saved=out.with_suffix(".blend")
bpy.ops.wm.save_as_mainfile(filepath=str(saved),copy=True,compress=True)
record["editable_proof_file"]=saved.name
record["blender"]=bpy.app.version_string
record["render_is_approved"]=False
record["requires_performance_check"]=True
out.with_suffix(".json").write_text(json.dumps(record,indent=2))
print("JACKET_V4_BUILD_AND_SCENE_OK",str(saved),flush=True)
