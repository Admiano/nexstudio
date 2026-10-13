"""SceneBam source-refit formalwear structural QA; NOT automatic aesthetic acceptance."""
import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
gender,variant,output=argv[0],argv[1],Path(argv[2])
rig=bpy.data.objects.get("Host.rig")
body=bpy.data.objects.get("Host.body")
garment=bpy.data.objects.get("NEX_V1_CC0_FORMAL_SUIT_"+gender.upper())
assert rig and rig.type=="ARMATURE", "APPROVED_HOST_RIG_MISSING"
assert body and body.type=="MESH", "APPROVED_BODY_MISSING"
assert garment and garment.type=="MESH", "FITTED_NEW_FORMAL_GARMENT_MISSING"
assert len(rig.data.bones)==163, f"BONE_COUNT_DRIFT:{len(rig.data.bones)}"
assert body.data.shape_keys and len(body.data.shape_keys.key_blocks)==34, "BODY_SHAPEKEY_DRIFT"
assert len(garment.data.vertices)>1000 and len(garment.data.polygons)>1000, "DONOR_MESH_EMPTY"
assert len([m for m in garment.modifiers if m.type=="ARMATURE" and m.object==rig])==1, "RIG_BINDING_INVALID"
assert garment.get("donorCC0") is True, "DONOR_LICENSE_MARKER_MISSING"
assert garment.get("approved") is False, "FALSE_APPROVAL_STATUS"
assert any(m.type=="SUBSURF" for m in garment.modifiers), "GARMENT_FINISH_MISSING"
assert sum(len(v.groups)>0 for v in garment.data.vertices)>len(garment.data.vertices)*.95, "LOOSE_UNWEIGHTED_VERTICES"
assert rig.data.pose_position in ("POSE","REST")
actions={a.name:(len(a.fcurves) if hasattr(a,"fcurves") else -1) for a in bpy.data.actions}
frames=[]
for frame in (1,27,56,125,234,338,451,568,710,891):
    rig.data.pose_position="POSE"
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    evaluated=garment.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    if not mesh or not mesh.vertices:raise RuntimeError("EMPTY_EVALUATED_FORMAL_AT_"+str(frame))
    points=[evaluated.matrix_world@v.co for v in mesh.vertices]
    if not all(all(math.isfinite(float(x)) for x in p) for p in points):
        raise RuntimeError("NONFINITE_GARMENT_DEFORMATION_AT_"+str(frame))
    lo=[min(p[i] for p in points) for i in range(3)]
    hi=[max(p[i] for p in points) for i in range(3)]
    spans=[hi[i]-lo[i] for i in range(3)]
    if min(spans)<0.03 or max(spans)>4:raise RuntimeError(f"IMPOSSIBLE_GARMENT_BOUNDS:{frame}:{spans}")
    frames.append({"frame":frame,"vertices":len(mesh.vertices),"worldBounds":[lo,hi],"spans":spans})
    evaluated.to_mesh_clear()
out={
"variant":variant,
"gender":gender,
"status":"STRUCTURAL_QA_PASS__VISUAL_COLLISION_AND_LIVE_INTEGRATION_NOT_CERTIFIED",
"rigBones":len(rig.data.bones),
"bodyShapeKeys":len(body.data.shape_keys.key_blocks),
"actionCount":len(actions),
"actionNames":sorted(actions),
"donor":garment.get("donorName"),
"garmentVertices":len(garment.data.vertices),
"garmentFaces":len(garment.data.polygons),
"garmentWeightGroups":len(garment.vertex_groups),
"testedFrames":frames,
"warnings":["Finite rig evaluations are not hand/body/chair intersection tests","Real rendered front/three-quarter and two gesture frames still require visual review","Current approved v3/v6 scene geometry is not proof of deployment in the SceneBam live service"],
}
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(out,indent=2)+"\n")
print("SCENEBAM_REFIT_STRUCTURAL_QA_PASS",variant,len(frames),flush=True)
