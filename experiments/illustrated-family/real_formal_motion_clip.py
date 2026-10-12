"""Render a true 4–5 s sampled segment of canonical V1 presenter animation.

The approved Host rig's existing action is the time authority. Frame sampling is
integer-strided at the original FPS (do not interpolate unrelated static poses).
No audio/music is fabricated. Uses previously fitted disposable formal .blend.
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
gender,directory=args[:2]
assert gender in ("female","male")
out=Path(directory).resolve();out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
rig=bpy.data.objects["Host.rig"]
body=bpy.data.objects["Host.body"]
suit=bpy.data.objects["NEX_V1_CC0_FORMAL_SUIT_"+gender.upper()]
assert len(rig.data.bones)==163
assert body.data.shape_keys and len(body.data.shape_keys.key_blocks)==34
assert any(m.type=="ARMATURE" and m.object==rig for m in suit.modifiers)
assert not bool(suit["approved"])
fps=scene.render.fps/scene.render.fps_base
assert fps>=12
stride=max(1,round(fps/12))
frames=list(range(840,941,stride))
assert len(frames)>=30
output_fps=fps/stride

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
h=scene.render.resolution_y
for layer in scene.view_layers:
    for lines in layer.freestyle_settings.linesets:
        lines.linestyle.thickness *= h/4320
if scene.compositing_node_group is not None:
    for node in scene.compositing_node_group.nodes:
        if node.type=="DILATEERODE":
            node.inputs["Size"].default_value=max(1,round(node.inputs["Size"].default_value*h/2160))
scene.frame_set(frames[0])
bpoints=[body.matrix_world@v.co for v in body.data.vertices]
low=Vector(tuple(min(p[i] for p in bpoints) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in bpoints) for i in range(3)))
center=(hi+low)/2
cam=scene.camera
cam.location=center+Vector((0,-5,.1))
cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.ortho_scale=max(1.4,hi.z-low.z)*1.3
wrist_names=["wrist.L","wrist.R"]
for name in wrist_names:assert name in rig.pose.bones
first_wrist=None
max_motion=0
for i,frame in enumerate(frames):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    now=[rig.matrix_world@rig.pose.bones[name].head for name in wrist_names]
    if first_wrist is None:first_wrist=[v.copy() for v in now]
    max_motion=max(max_motion,*[(p-q).length for p,q in zip(first_wrist,now)])
    dest=out/f"frame_{i:04d}.png"
    scene.render.filepath=str(dest)
    bpy.ops.render.render(write_still=True)
    assert dest.is_file() and dest.stat().st_size>4096
    print("REAL_ANIMATION_FRAME",gender,frame,i,flush=True)
if max_motion<.025:raise RuntimeError("NO_REAL_GESTURE_MOTION_ACROSS_SEGMENT")
report={"gender":gender,"blender":bpy.app.version_string,
    "sourceFrames":frames,"sourceFps":fps,"sampleStride":stride,
    "outputFps":output_fps,"durationSeconds":len(frames)/output_fps,
    "maxWristMotionMetres":max_motion,
    "originalRigBones":len(rig.data.bones),"bodyShapeKeys":len(body.data.shape_keys.key_blocks),
    "timeAuthority":"Original V1 Host action, frame time retained",
    "audio":"No narration provided; silent performance validation only",
    "status":"EXPERIMENTAL_REAL_ANIMATED_PRESENTATION_NOT_RELEASE_CERTIFIED"}
(out/"animation_provenance.json").write_text(json.dumps(report,indent=2)+"\n")
print("REAL_ANIMATION_RENDER_DONE",json.dumps({k:report[k] for k in ("gender","sourceFps","sampleStride","outputFps","durationSeconds","maxWristMotionMetres")}),flush=True)
