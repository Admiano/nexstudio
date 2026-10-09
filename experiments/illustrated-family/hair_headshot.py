"""One fixed FRONT headshot and one fixed THREE-QUARTER headshot, real Blender."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
gender,dst,donor=args[:3]
scene=bpy.context.scene
body=bpy.data.objects["Host.body"]
rig=bpy.data.objects["Host.rig"]
for ob in bpy.data.objects:
    if ob.name.startswith(("Guest.","Ref.")):ob.hide_render=True
# Head group occupies the same geometry and space for each variant.
head_group=body.vertex_groups.get("head")
assert head_group,"No head skin region"
head_group_i=head_group.index
points=[]
for v in body.data.vertices:
    if any(g.group==head_group_i and g.weight>.15 for g in v.groups):
        points.append(body.matrix_world@v.co)
assert points
mi=Vector([min(p[k] for p in points) for k in range(3)])
ma=Vector([max(p[k] for p in points) for k in range(3)])
target=(mi+ma)*.5
camera_data=bpy.data.cameras.new("NEX_ID_FACE_PROOF_CAMERA")
camera=bpy.data.objects.new("NEX_ID_FACE_PROOF_CAMERA",camera_data)
scene.collection.objects.link(camera)
camera_data.type="ORTHO"
camera_data.ortho_scale=.34
scene.camera=camera
scene.render.engine="CYCLES"
scene.cycles.device="CPU";scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=560;scene.render.resolution_y=560
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
h=560
for layer in scene.view_layers:
    for ls in layer.freestyle_settings.linesets:
        ls.linestyle.thickness*=h/4320
if scene.compositing_node_group:
    for node in scene.compositing_node_group.nodes:
        if node.type=="DILATEERODE":
            node.inputs["Size"].default_value=max(1,round(node.inputs["Size"].default_value*h/2160))
base=Path(dst).resolve()
for kind,offset in (("front",Vector((0,-4,0))),("threeq",Vector((1.65,-4,0)))):
    camera.location=target+offset
    camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
    output=base.with_name(base.stem+"-head-"+kind+".png")
    scene.render.filepath=str(output)
    bpy.ops.render.render(write_still=True)
    assert output.is_file() and output.stat().st_size>9000
    print("ACTUAL_CC0_HAIR_HEAD_RENDER_OK",gender,kind,str(output),output.stat().st_size,flush=True)
