"""Actual source hair comparison, using identical cameras and frame numbers."""
import bpy,sys,math,runpy,json
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];character,variant,output=args[:3]
size=int(args[3]) if len(args)>3 else 768;frame=int(args[4]) if len(args)>4 else 1
scene=bpy.context.scene;scene.frame_set(frame);old_height=scene.render.resolution_y*scene.render.resolution_percentage/100
report={}
if variant!='baseline':report=runpy.run_path(str(Path(__file__).with_name('cast-hair-groom.py')))['apply_hair_groom'](scene,character,colour=args[5] if len(args)>5 and args[5]!='-' else None,density=float(args[7]) if len(args)>7 else 1)
center=Vector((-.42,0,1.49 if character=='female' else 1.67));scale=.54 if character=='female' else .36
view=args[6] if len(args)>6 else 'front';offset=Vector((0,-5,0)) if view=='front' else Vector((3,-4,0)) if view=='three-quarter' else Vector((5,0,0)) if view=='side' else Vector((0,5,0))
scene.camera.location=center+offset;scene.camera.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=scale
scene.render.resolution_x=scene.render.resolution_y=size;scene.render.resolution_percentage=100;scene.cycles.samples=128 if variant!='baseline' else 64;scene.cycles.use_denoising=False;scene.cycles.device='CPU'
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
for layer in scene.view_layers:
 for lines in layer.freestyle_settings.linesets:lines.linestyle.thickness*=size/old_height
scene.render.filepath=output;Path(output).parent.mkdir(parents=True,exist_ok=True)
Path(output).with_suffix('.json').write_text(json.dumps({'hairGroom':report,'frame':frame,'size':size,'view':view},indent=2))
if variant!='baseline':bpy.ops.wm.save_as_mainfile(filepath=str(Path(output).with_suffix('.blend')),compress=True)
bpy.ops.render.render(write_still=True)
