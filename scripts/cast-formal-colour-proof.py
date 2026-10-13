"""Actual Blender production-assembled cast proof of independently coloured UV suit/tie.
Runs on baseline V3/V6 production assembly; never a generated concept image.
"""
import bpy,os,sys,json,runpy,hashlib,math
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]
variant,suit,tie,dest=args[:4]
dest=Path(dest).resolve()
dest.mkdir(parents=True,exist_ok=True)
os.environ['CAST_CHARACTER']=variant.split('-')[0]
scene=bpy.context.scene
adapter=runpy.run_path(str(Path(__file__).with_name('cast-apply-formal.py')))
report=adapter['apply_formal'](scene,variant,suit,tie)
name='SCENEBAM_FORMAL_'+variant.upper().replace('-','_')
obj=bpy.data.objects[name]
assert len(obj.material_slots)==3
assert all(count>0 for count in [len(report['materialsByRole']['suit']),len(report['materialsByRole']['tie'])])
for role,slot,hexcode in [('suit',1,suit),('tie',2,tie)]:
 material=obj.data.materials[slot]
 blend=next((n for n in material.node_tree.nodes if n.name=='SCENEBAM_FORMAL_'+role.upper()+'_UV_COLOUR'),None)
 assert blend is not None
 expected=adapter['_colour'](hexcode)
 assert all(abs(float(a)-float(b))<.0001 for a,b in zip(blend.inputs[2].default_value,expected))
 assert any(m.type=='ARMATURE' and m.object==bpy.data.objects['Host.rig'] for m in obj.modifiers)
assert report['restError']<1e-4

scene.frame_set(27)
scene.render.engine='CYCLES'
scene.cycles.samples=8
scene.cycles.use_denoising=True
scene.render.resolution_x=420
scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.camera.location=(-.42,-5.0,1.13)
scene.camera.rotation_euler=(Vector((-.42,0,1.13))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.type='ORTHO'
scene.camera.data.ortho_scale=1.65
scene.view_settings.view_transform='Standard'
target=dest/(variant+'-'+suit+'-'+tie+'.png')
scene.render.filepath=str(target)
bpy.ops.render.render(write_still=True)
assert target.stat().st_size>10000
report.update({'output':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'renderSamples':8,'testFrame':27})
(dest/(variant+'-'+suit+'-'+tie+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print('CAST_FORMAL_INDEPENDENT_MATERIAL_RENDER_PASS',variant,suit,tie,flush=True)
