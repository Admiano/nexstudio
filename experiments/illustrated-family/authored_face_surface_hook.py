"""Generate isolated illustrated-face edit and record shape-key preservation."""
import bpy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from authored_face_surface_trial import build_identity
args=sys.argv[sys.argv.index("--")+1:]
gender,style,dst=args[:3]
report=build_identity(style,gender)
out=Path(dst).resolve()
out.parent.mkdir(parents=True,exist_ok=True)
blend=out.with_suffix(".blend")
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True,copy=True)
report["editable_scene"]=blend.name
(out.with_suffix(".json")).write_text(json.dumps(report,indent=2))
print("SURFACE_REGISTERED_FACE_PROOF_SCENE_SAVED",blend,flush=True)
