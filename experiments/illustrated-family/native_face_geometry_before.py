"""Snapshot actual V1 head geometry before applying inherited native facevar."""
import bpy,sys,json,os
from pathlib import Path
args=sys.argv[sys.argv.index("--")+1:]
gender,out_path=args[:2]
assert gender in ("female","male")
bpy.context.scene.frame_set(27)
bpy.context.view_layer.update()
body=bpy.data.objects["Host.body"]
rig=bpy.data.objects["Host.rig"]
assert len(rig.data.bones)==163
assert body.data.shape_keys and len(body.data.shape_keys.key_blocks)==34
idx=[v.index for v in body.data.vertices
     if (body.matrix_world@v.co).z>1.34 and (v.index%3==0)]
if len(idx)<100:raise RuntimeError("INSUFFICIENT_ACTUAL_FACE_VERTICES")
f=Path(out_path).resolve()
f.parent.mkdir(parents=True,exist_ok=True)
ref={"gender":gender,"face":os.environ.get("FACE",""),
     "idx":idx,"vertices":[list(body.data.vertices[i].co) for i in idx],
     "shapeKeys":[x.name for x in body.data.shape_keys.key_blocks],
     "originalRigBoneNames":[b.name for b in rig.data.bones]}
f.with_name(f.stem+"-face-before.json").write_text(json.dumps(ref))
print("NATIVE_FACE_CAPTURED_CANONICAL_GEOMETRY",gender,len(idx),flush=True)
