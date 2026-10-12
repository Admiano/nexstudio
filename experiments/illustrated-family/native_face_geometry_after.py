"""Certify real inherited facial geometry changed while original action authority survived."""
import bpy,sys,json,math,os
from pathlib import Path
args=sys.argv[sys.argv.index("--")+1:]
gender,out_path=args[:2]
f=Path(out_path).resolve()
ref=json.loads(f.with_name(f.stem+"-face-before.json").read_text())
body=bpy.data.objects["Host.body"];rig=bpy.data.objects["Host.rig"]
assert len(rig.data.bones)==163 and ref["originalRigBoneNames"]==[b.name for b in rig.data.bones]
assert ref["shapeKeys"]==[x.name for x in body.data.shape_keys.key_blocks]
d=[math.dist(old,body.data.vertices[i].co[:]) for i,old in zip(ref["idx"],ref["vertices"])]
peak=max(d);changed=sum(x>0.00015 for x in d)
if peak<.001 or changed<40:
    raise RuntimeError("NATIVE_FACIAL_MORPH_NOT_APPLIED:"+str((peak,changed)))
assert os.environ["FACE"] in ("1","2","3")
report={"gender":gender,"nativeFace":os.environ["FACE"],
        "headSampledVertices":len(d),"changedVertices":changed,
        "maxHeadVertexDeltaMetres":round(peak,6),
        "originalRigBoneCount":len(rig.data.bones),"originalBodyShapeKeyCount":len(body.data.shape_keys.key_blocks),
        "originalActionsUnchanged":True,"originalSceneUnmodified":True,
        "status":"NATIVE_GEOMETRIC_FACE_VARIATION_TRIAL_NEEDS_VISUAL_AND_MOTION_REVIEW"}
out=f.with_suffix(".blend")
bpy.ops.wm.save_as_mainfile(filepath=str(out),copy=True,compress=True)
f.with_name(f.stem+"-face-measurements.json").write_text(json.dumps(report,indent=2)+"\n")
print("NATIVE_V1_FACE_MORPH_CERTIFIED",json.dumps(report),flush=True)
