"""Render an illustrated review view from an assembled production scene.

blender -b assembled.blend --python scripts/render-skin-illustrated-review.py -- male portrait.png 1 1024 front
Views: front, quarter, profile, skin. Optional final argument: complexion hex.
"""
import bpy,sys,runpy,json,hashlib,os
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];sex,output=args[:2];frame=int(args[2]) if len(args)>2 else 1;size=int(args[3]) if len(args)>3 else 512;view=args[4] if len(args)>4 else 'front';tone=args[5] if len(args)>5 else ''
s=bpy.context.scene;old=s.render.resolution_y*s.render.resolution_percentage/100;s.frame_set(frame)
s.camera.location=(-.42,-5,1.64 if sex=='male' else 1.51);s.camera.rotation_euler=(1.57079632679,0,0);s.camera.data.ortho_scale=.40 if sex=='male' else .54
if view=='detail':s.camera.data.ortho_scale=.22
if view=='skin':s.camera.data.ortho_scale=.08;s.camera.location.x-=.035;s.camera.location.z-=.02
if view not in ('front','detail','skin'):
 target=Vector((-.42,0,1.64 if sex=='male' else 1.51));delta=Vector((2.5,-4.330127,0)) if view=='quarter' else Vector((5,-.10,0));s.camera.location=target+delta;s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
p=Path(args[args.index('--skin-module')+1]) if '--skin-module' in args else Path(__file__).with_name('cast-skin-appearance.py');report=runpy.run_path(str(p))['apply_skin_appearance'](s,sex,tone)
s.render.resolution_x=s.render.resolution_y=size;s.render.resolution_percentage=100;s.cycles.samples=64 if size<768 else 128;s.cycles.use_denoising=True;s.cycles.device='CPU';s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
for layer in s.view_layers:
 for lines in layer.freestyle_settings.linesets:lines.linestyle.thickness*=size/old
if s.compositing_node_group:
 for n in s.compositing_node_group.nodes:
  if n.type=='DILATEERODE':n.inputs['Size'].default_value=max(1,round(n.inputs['Size'].default_value*size/old))
if view=='skin':s.render.use_freestyle=False
s.render.filepath=output;Path(output).parent.mkdir(parents=True,exist_ok=True)
Path(output).with_suffix('.json').write_text(json.dumps({'character':sex,'frame':frame,'view':view,'size':size,'samples':s.cycles.samples,'freestyle':s.render.use_freestyle,'skin':report},indent=2))
if '--save' in args:bpy.ops.wm.save_as_mainfile(filepath=str(Path(output).with_suffix('.blend')),compress=True)
bpy.ops.render.render(write_still=True)
