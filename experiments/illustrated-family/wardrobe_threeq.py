"""Real 3/4 camera proof after the front render, using the same scene and style."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
gender,front=argv[:2]
scene=bpy.context.scene
body=bpy.data.objects["Host.body"]
v=[body.matrix_world@pt.co for pt in body.data.vertices]
a=Vector(tuple(min(p[i] for p in v) for i in range(3)))
b=Vector(tuple(max(p[i] for p in v) for i in range(3)))
center=(a+b)*0.5
camera=scene.camera
assert camera is not None
camera.location=center+Vector((1.55,-5,0.12))
camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
path=Path(front).resolve().with_name(Path(front).stem.replace("-front","-threeq")+".png")
scene.render.filepath=str(path)
bpy.ops.render.render(write_still=True)
assert path.is_file() and path.stat().st_size>4096
print("WARDROBE_THREEQ_RENDER_OK",path,flush=True)
