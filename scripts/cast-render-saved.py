"""Evaluate original action, fit saved garments and render a fixed view."""
import bpy,sys,os,runpy,math
from pathlib import Path
from mathutils import Vector
character,view,frame,output=sys.argv[sys.argv.index('--')+1:]
s=bpy.context.scene
os.environ['CAST_CHARACTER']=character
os.environ['GARMS']=';'.join(o.name for o in s.objects if o.type=='MESH' and not o.get('castGarmentSource') and not o.get('castFitSource') and (not o.hide_render or o.get('castFitOriginalHideRender') is False) and any(m and m.get('castFabric') for m in o.data.materials))
s.frame_set(int(frame));bpy.context.view_layer.update()
runpy.run_path(str(Path(__file__).with_name('cast-fit-posed-clothing.py')))
target=Vector((-.42,0,1.21 if character=='female' else 1.29))
angle=math.radians(35 if view=='left-3q' else 0)
s.camera.location=target+Vector((5*math.sin(angle),-5*math.cos(angle),0))
s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.camera.data.ortho_scale=1.50 if character=='female' else 1.60
height=s.render.resolution_y*s.render.resolution_percentage/100
s.render.resolution_x=900;s.render.resolution_y=1200;s.render.resolution_percentage=100
for style in bpy.data.linestyles:style.thickness*=1200/height
if s.compositing_node_group:
 for n in s.compositing_node_group.nodes:
  if n.type=='DILATEERODE' and n.inputs.get('Size'):n.inputs['Size'].default_value=max(1,round(n.inputs['Size'].default_value*1200/height))
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
s.render.use_freestyle=False;s.render.use_border=False;s.render.film_transparent=True
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.render.filepath=output;bpy.ops.render.render(write_still=True)
