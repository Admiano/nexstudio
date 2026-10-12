"""Test actual animation frames on V1 jacket V4. Only the experiment scene is changed."""
import bpy, json, sys
from mathutils import Vector
from pathlib import Path

args=sys.argv[sys.argv.index('--')+1:]
gender,front=args[:2]
base=Path(front).resolve()
scene=bpy.context.scene
body=bpy.data.objects["Host.body"]
rig=bpy.data.objects["Host.rig"]
jacket=bpy.data.objects["NEX_V1_TAILORED_JACKET_V4_"+gender.upper()]
assert body and rig and jacket
assert any(m.type == "ARMATURE" and m.object == rig for m in jacket.modifiers)
assert len(body.data.shape_keys.key_blocks)==34, "Canonical face shape-key inventory changed"
src=bpy.data.objects[jacket["sourceGarment"]]
assert not src.hide_render, "Original outfit hidden"
assert jacket["approved"] is False
scene.render.resolution_x=440
scene.render.resolution_y=700
scene.render.resolution_percentage=100
scene.cycles.samples=8

def evaluated_bbox(obj):
    de=bpy.context.evaluated_depsgraph_get()
    ev=obj.evaluated_get(de)
    pts=[ev.matrix_world@Vector(x) for x in ev.bound_box]
    return {
        "min":[round(min(p[i] for p in pts),4) for i in range(3)],
        "max":[round(max(p[i] for p in pts),4) for i in range(3)]
    }

report={"geometry":"V4", "gender":gender,"blender":bpy.app.version_string,
        "rig":rig.name,"source_object":src.name,
        "underlayer_visible":True,
        "shape_key_count":len(body.data.shape_keys.key_blocks),
        "frames":[]}
for frame in (338,891):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    bpts=[body.matrix_world@v.co for v in body.data.vertices]
    lo=Vector(tuple(min(p[i] for p in bpts) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in bpts) for i in range(3)))
    center=(lo+hi)*.5
    cam=scene.camera
    cam.location=center+Vector((0,-5,0.1))
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=max(1.4,hi.z-lo.z)*1.30
    pose=base.with_name(base.stem.replace("-front","-pose-"+str(frame))+".png")
    scene.render.filepath=str(pose)
    bpy.ops.render.render(write_still=True)
    assert pose.is_file() and pose.stat().st_size>4096
    report["frames"].append({
        "frame":frame,"image":pose.name,"jacket_bounds":evaluated_bbox(jacket),
        "source_bounds":evaluated_bbox(src),"camera":"front",
        "jacket_rigged":True
    })
    print("JACKET_POSE_RENDER_OK",gender,frame,pose.name,flush=True)
qa=base.with_name(base.stem+"-pose-qa.json")
qa.write_text(json.dumps(report,indent=2))
print("JACKET_V4_PERFORMANCE_STATIC_QA_DONE",qa.name,flush=True)
