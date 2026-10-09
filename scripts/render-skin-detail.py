"""Actual source-scene comparisons at fixed portrait and anatomical crop scales."""
import sys,json,runpy,math
from pathlib import Path
import bpy
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
character,variant,view,output=args[:4]
tone=args[4] if len(args)>4 else ''
frame=int(args[5]) if len(args)>5 else 27
scene=bpy.context.scene;scene.frame_set(frame)
old_height=scene.render.resolution_y*scene.render.resolution_percentage/100
body=bpy.data.objects['Host.body'];rig=body.parent
scene.camera.rotation_euler=(math.pi/2,0,0)
if view=='face':
    center=Vector((-.42,0,1.55 if character=='female' else 1.64));scale=.50
elif view=='skin-close':
    center=Vector((-.42,0,1.535 if character=='female' else 1.635));scale=.205
elif view=='lips':
    center=Vector((-.42,0,1.499 if character=='female' else 1.60));scale=.080
elif view=='neck':
    center=rig.matrix_world@Vector(rig.data.bones['neck01'].head_local);center.z+=.01;scale=.255
elif view in ('hand','palm'):
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    names=['wrist.L']+['finger%d-%d.L'%(i,j) for i in range(1,6) for j in range(1,4)]
    groups={body.vertex_groups[n].index for n in names}
    pts=[ev.matrix_world@v.co for v in ev.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.80]
    center=sum(pts,Vector())/len(pts);scale=.19
else:
    center=Vector((-.42,0,1.21 if character=='female' else 1.29));scale=1.10 if character=='female' else 1.18
scene.camera.location=center+Vector((0,-5,0));scene.camera.data.ortho_scale=scale
if view=='palm':
    scene.camera.location=center+Vector((.4,-4,2));scene.camera.rotation_euler=(center-scene.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
report={}
if variant!='baseline':
    report=runpy.run_path(str(Path(__file__).with_name('cast-skin-appearance.py')))['apply_skin_appearance'](scene,character,tone)
size=int(args[6]) if len(args)>6 else 1024
scene.render.resolution_x=scene.render.resolution_y=size
scene.render.resolution_percentage=100
scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.cycles.device='CPU'
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
for layer in scene.view_layers:
    for lines in layer.freestyle_settings.linesets:lines.linestyle.thickness*=size/old_height
if scene.compositing_node_group:
    for n in scene.compositing_node_group.nodes:
        if n.type=='DILATEERODE':n.inputs['Size'].default_value=max(1,round(n.inputs['Size'].default_value*size/old_height))
scene.render.filepath=output;Path(output).parent.mkdir(parents=True,exist_ok=True)
Path(output).with_suffix('.json').write_text(json.dumps({'skin':report,'frame':frame,'cameraCenter':list(center),'scale':scale},indent=2))
bpy.ops.render.render(write_still=True)
