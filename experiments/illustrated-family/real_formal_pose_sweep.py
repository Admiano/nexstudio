"""NexStudio illustrated V1 formal cast: true rig/action 10-frame Blender sweep.

Loads an existing disposable illustrated formal suit .blend. No canonical
asset is edited, no generated art is used. Previews inspect garment stability
at varied original-animation poses; they are not replacement animation tracks.
"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index("--")+1:]
gender,outdir=args[:2]
if gender not in ("female","male"):raise ValueError(gender)
out=Path(outdir).resolve()
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
rig=bpy.data.objects["Host.rig"]
body=bpy.data.objects["Host.body"]
suit=bpy.data.objects["NEX_V1_CC0_FORMAL_SUIT_"+gender.upper()]
if len(rig.data.bones)!=163:raise RuntimeError("ORIGINAL_V1_RIG_BONES_CHANGED")
if not body.data.shape_keys or len(body.data.shape_keys.key_blocks)!=34:
    raise RuntimeError("ORIGINAL_V1_FACE_SHAPE_KEYS_CHANGED")
if not any(m.type=="ARMATURE" and m.object==rig for m in suit.modifiers):
    raise RuntimeError("FORMAL_SUIT_LOST_ORIGINAL_RIG_BINDING")
assert suit["approved"] is False,"Never silently mark experimental costume as approved"
for name in ("Host.V64_dress_lines",) if gender=="female" else ():
    obj=bpy.data.objects.get(name)
    if obj and not obj.hide_render:raise RuntimeError("LEGACY_SKIRT_INK_VISIBLE")

scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=5
scene.cycles.use_denoising=True
scene.render.resolution_x=440
scene.render.resolution_y=700
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True

frames=(27,100,220,338,450,560,700,815,891,980)
wrist_names=[n for n in ("wrist.L","wrist.R") if n in rig.pose.bones]
if len(wrist_names)!=2:raise RuntimeError("ORIGINAL_WRIST_POSE_BONES_MISSING")
info={"gender":gender,"blender":bpy.app.version_string,
      "originalRig":rig.name,"boneCount":len(rig.data.bones),
      "shapeKeyCount":len(body.data.shape_keys.key_blocks),
      "suit":suit.name,"frames":[]}
positions={n:[] for n in wrist_names}
for fr in frames:
    scene.frame_set(fr)
    bpy.context.view_layer.update()
    vertices=[body.matrix_world @ v.co for v in body.data.vertices]
    low=Vector(tuple(min(p[i] for p in vertices) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in vertices) for i in range(3)))
    focus=(low+high)/2
    camera=scene.camera
    camera.location=focus+Vector((0,-5,0.1))
    camera.rotation_euler=(focus-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale=max(1.4,high.z-low.z)*1.30
    wrist={}
    for name in wrist_names:
        point=rig.matrix_world@rig.pose.bones[name].head
        positions[name].append(point.copy())
        wrist[name]=[round(float(v),5) for v in point]
    image=out/f"frame_{fr:04d}.png"
    scene.render.filepath=str(image)
    bpy.ops.render.render(write_still=True)
    if not image.is_file() or image.stat().st_size<4096:raise RuntimeError("POSE_RENDER_MISSING:"+str(image))
    info["frames"].append({"frame":fr,"render":image.name,"bytes":image.stat().st_size,"wristWorld":wrist})
    print("REAL_POSE_SWEEP_IMAGE",gender,fr,image.stat().st_size,flush=True)
span={}
for name,pts in positions.items():
    spread=max((a-b).length for a in pts for b in pts)
    span[name]=round(spread,5)
info["wristMotionSpanMetres"]=span
if max(span.values())<=0.015:
    raise RuntimeError("ORIGINAL_ANIMATED_ACTION_NOT_PLAYING")
info["result"]="PASS_ORIGINAL_RIG_DYNAMIC_ACTION_POSE_SWEEP_NOT_FULL_COLLISION_CERTIFICATION"
(out/"pose_sweep_report.json").write_text(json.dumps(info,indent=2))
print("POSE_SWEEP_VALIDATED",json.dumps({"gender":gender,"span":span,"poses":len(frames)}),flush=True)
