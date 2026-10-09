"""Nonrender structural action sweep of all real fitted NexStudio V1 suits.

Does NOT claim collision certification. Checks original rig preservation,
actual wrist motion, finite evaluated garment geometry and sensible bounds
through ten poses of the existing V1 action.
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
gender,outfile=args[:2]
assert gender in ("female","male")
target=Path(outfile).resolve();target.parent.mkdir(parents=True,exist_ok=True)
rig=bpy.data.objects["Host.rig"]
body=bpy.data.objects["Host.body"]
suit=bpy.data.objects["NEX_V1_CC0_FORMAL_SUIT_"+gender.upper()]
assert len(rig.data.bones)==163,"ORIGINAL_RIG_BONE_COUNT_CHANGED"
assert len(body.data.shape_keys.key_blocks)==34,"ORIGINAL_BODY_SHAPE_KEYS_CHANGED"
assert any(m.type=="ARMATURE" and m.object==rig for m in suit.modifiers),"SUIT_BINDING_LOST"
assert suit.get("approved") is False,"EXPERIMENT_IMPROPERLY_MARKED_APPROVED"
frames=(27,100,220,338,450,560,700,815,891,980)
report={"gender":gender,"donor":suit.get("donorName"),"sourceScene":bpy.data.filepath,
        "rigName":rig.name,"boneCount":len(rig.data.bones),
        "shapeKeyCount":len(body.data.shape_keys.key_blocks),
        "blender":bpy.app.version_string,"frames":[]}
p0=None
motions=[]
for frame in frames:
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    evaluated=suit.evaluated_get(dg)
    mesh=evaluated.to_mesh()
    if mesh is None or len(mesh.vertices)<1500:raise RuntimeError("EVALUATED_SUIT_MESH_MISSING")
    coords=[evaluated.matrix_world@v.co for v in mesh.vertices]
    if not all(math.isfinite(t) for pt in coords for t in pt):
        evaluated.to_mesh_clear()
        raise RuntimeError("NONFINITE_ANIMATED_SUIT_VERTEX")
    lo=[min(pt[i] for pt in coords) for i in range(3)]
    hi=[max(pt[i] for pt in coords) for i in range(3)]
    extent=[hi[i]-lo[i] for i in range(3)]
    if max(extent)>4 or any(k<.01 for k in extent):
        evaluated.to_mesh_clear()
        raise RuntimeError(f"ANIMATED_SUIT_INVALID_EXTENT:{frame}:{extent}")
    frame_vertices=len(mesh.vertices)
    evaluated.to_mesh_clear()
    wrists={}
    for bone_name in ("wrist.L","wrist.R"):
        assert bone_name in rig.pose.bones,"ORIGINAL_WRIST_MISSING"
        p=rig.matrix_world@rig.pose.bones[bone_name].head
        wrists[bone_name]=[float(round(t,5)) for t in p]
        if p0 is None:motions.append((bone_name,[]))
    report["frames"].append({
        "frame":frame,"evaluatedVertices":frame_vertices,
        "worldBoundsMin":[round(x,5) for x in lo],
        "worldBoundsMax":[round(x,5) for x in hi],
        "worldExtents":[round(x,5) for x in extent],
        "wristWorld":wrists})
    print("FORMAL_BANK_POSE_CHECKED",gender,frame,frame_vertices,flush=True)
    if p0 is None:p0=wrists
movement=max(
    math.dist(p0[name],info["wristWorld"][name])
    for info in report["frames"] for name in ("wrist.L","wrist.R"))
if movement<0.04:raise RuntimeError("STATIC_GESTURE_ACTION_ON_EXPECTED_V1_TIMELINE")
report["maxDisplacementFromBaseMetres"]=round(movement,5)
report["status"]="PASS_RIG_DYNAMIC_GEOMETRY_FINITE_NOT_COLLISION_CERTIFICATION"
target.write_text(json.dumps(report,indent=2)+"\n")
print("FORMAL_BANK_GEOMETRY_SWEEP_PASS",gender,report["donor"],movement,flush=True)
