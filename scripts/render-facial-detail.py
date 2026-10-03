"""Render matched actual oral/ear detail from the assembled source scene."""
import bpy,sys,runpy,json
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];character,variant,output=args[:3];frame=int(args[3]) if len(args)>3 else 71;view=args[4] if len(args)>4 else 'mouth';size=int(args[5]) if len(args)>5 else 640
s=bpy.context.scene;s.frame_set(frame);old=s.render.resolution_y*s.render.resolution_percentage/100
b=bpy.data.objects['Host.body'];be=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=be.to_mesh();g=b.vertex_groups['lips' if view=='mouth' else 'ears'].index
pts=[be.matrix_world@v.co for v in me.vertices if any(w.group==g and w.weight>.5 for w in v.groups) and (view=='mouth' or v.co.x>0)]
center=sum(pts,Vector())/len(pts);center.z+=.001
be.to_mesh_clear();
report={}
if variant!='baseline':report=runpy.run_path(str(Path(__file__).with_name('cast-facial-refinement.py')))['apply_facial_refinement'](s,character)
s.frame_set(frame);bpy.context.view_layer.update()
scale=.095 if view=='mouth' else .090
if view=='portrait':center=Vector((-.42,0,1.64 if character=='male' else 1.51));scale=.40 if character=='male' else .54
s.camera.location=center+Vector((0,-5,0));s.camera.rotation_euler=(1.57079632679,0,0);s.camera.data.ortho_scale=scale
s.render.resolution_x=s.render.resolution_y=size;s.render.resolution_percentage=100;s.cycles.samples=128;s.cycles.use_denoising=False;s.cycles.device='CPU';s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
for layer in s.view_layers:
 for lines in layer.freestyle_settings.linesets:lines.linestyle.thickness*=size/old
s.render.filepath=output;Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).with_suffix('.json').write_text(json.dumps({'character':character,'variant':variant,'frame':frame,'view':view,'refinement':report,'cameraLocation':list(s.camera.location),'cameraRotation':list(s.camera.rotation_euler),'orthoScale':s.camera.data.ortho_scale,'size':size},indent=2))
if variant!='baseline':bpy.ops.wm.save_as_mainfile(filepath=str(Path(output).with_suffix('.blend')),compress=True)
bpy.ops.render.render(write_still=True)
