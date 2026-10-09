"""Small real-Blender baseline render for fast visual validation, no source edits."""
import bpy, sys, json
from pathlib import Path
from mathutils import Vector

argv=sys.argv[sys.argv.index("--")+1:]
gender,output=argv[0],Path(argv[1]).resolve()
assert gender in ("female","male")
output.parent.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
body=bpy.data.objects["Host.body"]
rig=bpy.data.objects["Host.rig"]
scene.frame_set(27)
bpy.context.view_layer.update()
for o in bpy.data.objects:
    if o.name.startswith(("Guest.","Ref.")):
        o.hide_render=True
verts=[body.matrix_world@v.co for v in body.data.vertices]
mn=Vector(tuple(min(p[i] for p in verts) for i in range(3)))
mx=Vector(tuple(max(p[i] for p in verts) for i in range(3)))
center=(mn+mx)*.5
height=max(1.4,mx.z-mn.z)
camdata=bpy.data.cameras.new("V1 QUICK PROOF CAMERA")
cam=bpy.data.objects.new("V1 QUICK PROOF CAMERA",camdata)
scene.collection.objects.link(cam)
camdata.type='ORTHO'
camdata.ortho_scale=height*1.30
cam.location=center+Vector((0,-5,.1))
cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
scene.camera=cam
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=3
scene.cycles.use_denoising=True
scene.render.resolution_x=440
scene.render.resolution_y=700
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
scene.render.filepath=str(output)
bpy.ops.render.render(write_still=True)
assert output.is_file() and output.stat().st_size>4096, "Missing actual rendered image"
print("QUICK_REAL_RENDER_OK",output,"BYTES",output.stat().st_size,flush=True)
