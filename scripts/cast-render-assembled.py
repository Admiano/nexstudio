"""Render the original assembled scene; optionally save its existing rig/action."""
import json,os,sys,time
from pathlib import Path
import bpy
args=sys.argv[sys.argv.index('--')+1:];request_file,output_file=map(Path,args[:2]);config=json.loads(request_file.read_text())['config']
source=Path(os.environ['PV1']);entry=source/os.environ['MODF'];started=time.monotonic()
exec(compile(entry.read_text(),str(entry),'exec'),globals())
polish_entry=Path(__file__).with_name('cast-apply-approved.py');exec(compile(polish_entry.read_text(),str(polish_entry),'exec'),globals())
scene=bpy.context.scene
for layer in scene.view_layers:
    for lines in layer.freestyle_settings.linesets:
        if lines.collection:lines.collection.use_fake_user=True
scene.frame_set(config['frame']);scene.render.resolution_percentage=config['resolutionPercentage'];scene.render.image_settings.file_format='PNG'
height=scene.render.resolution_y*scene.render.resolution_percentage/100
for layer in scene.view_layers:
    for lines in layer.freestyle_settings.linesets:lines.linestyle.thickness*=height/4320
if scene.compositing_node_group is not None:
    for node in scene.compositing_node_group.nodes:
        if node.type=='DILATEERODE':node.inputs['Size'].default_value=max(1,round(node.inputs['Size'].default_value*height/2160))
if '--scene-output' in args:bpy.ops.wm.save_as_mainfile(filepath=args[args.index('--scene-output')+1],compress=True)
output_file.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(output_file)
if '--assemble-only' not in args:bpy.ops.render.render(write_still=True)
metadata={'sourceVersion':config['sourceVersion'],'renderVersion':config['renderVersion'],'frame':scene.frame_current,'seconds':round(time.monotonic()-started,2),'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'engine':scene.render.engine,'samples':scene.cycles.samples,'camera':scene.camera.name,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma}
output_file.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n');print('CAST_ASSEMBLED_RENDER',json.dumps(metadata),flush=True)
