"""Run detached jacket experiment, save editable proof, then pass to renderer."""
import bpy, json, sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
from jacket_trial_v2 import build_jacket
argv=sys.argv[sys.argv.index("--")+1:]
gender,output=argv[:2]
record=build_jacket(gender)
dest=Path(output).resolve()
dest.parent.mkdir(parents=True,exist_ok=True)
scene=dest.with_suffix(".blend")
bpy.ops.wm.save_as_mainfile(filepath=str(scene),copy=True,compress=True)
record["proof_scene"]=scene.name
record["blender"]=bpy.app.version_string
(dest.with_suffix(".json")).write_text(json.dumps(record,indent=2))
print("JACKET_V2_EDITABLE_SCENE",scene,flush=True)
