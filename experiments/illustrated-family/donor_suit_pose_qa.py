"""Probe a real fitted MakeHuman suit through the original V1 action frames."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
gender,filename=args[:2]
out=Path(filename).resolve()
s=bpy.context.scene
body=bpy.data.objects["Host.body"]
rig=bpy.data.objects["Host.rig"]
suit=bpy.data.objects["NEX_V1_CC0_FORMAL_SUIT_"+gender.upper()]
assert suit["donorCC0"] and suit["approved"]==False
assert any(m.type=="ARMATURE" and m.object==rig for m in suit.modifiers)
assert len(body.data.shape_keys.key_blocks)==34
s.render.resolution_x=440
s.render.resolution_y=700
s.render.resolution_percentage=100
s.cycles.samples=8
data={"asset":suit["donorName"],"gender":gender,"blender":bpy.app.version_string,
    "performanceAuthority":"original V1 Host", "frames":[]}
for frame in (338,891):
    s.frame_set(frame)
    bpy.context.view_layer.update()
    pts=[body.matrix_world @ v.co for v in body.data.vertices]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    target=(lo+hi)/2
    cam=s.camera
    cam.location=target+Vector((0,-5,0.1))
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=max(1.4,hi.z-lo.z)*1.30
    name=out.with_name(out.stem.replace("-front","-pose-"+str(frame))+".png")
    s.render.filepath=str(name)
    bpy.ops.render.render(write_still=True)
    assert name.exists() and name.stat().st_size>4096
    data["frames"].append({"frame":frame,"render":name.name,"renderBytes":name.stat().st_size})
    print("ACTUAL_SUIT_POSE_RENDER_OK",gender,frame,flush=True)
path=out.with_name(out.stem+"-pose-qa.json")
path.write_text(json.dumps(data,indent=2))
