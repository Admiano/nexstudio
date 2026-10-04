"""Render the original assembled scene; optionally save its existing rig/action."""
import json,os,sys,time,runpy
from pathlib import Path
import bpy
args=sys.argv[sys.argv.index('--')+1:];request_file,output_file=map(Path,args[:2]);config=json.loads(request_file.read_text())['config']
source=Path(os.environ['PV1']);entry=source/os.environ['MODF'];started=time.monotonic()
# Versioned server-side finish profile. Reference tooling can explicitly turn
# these off for a baseline; clients cannot inject these environment keys.
for flag in ('CAST_QUALITY_PILOT','CAST_FINISH_UPGRADE','CAST_GARMENT_STRUCTURE_PILOT','CAST_SKIN_APPEARANCE','CAST_HAIR_GROOM','CAST_FACIAL_REFINEMENT','CAST_CLOTH_APPEARANCE'):
    os.environ.setdefault(flag,'1')
if os.environ.get('CAST_QUALITY_PILOT') == '1':
    # Rest-pose AO is already followed by live material AO in the approved
    # grade; avoid multiplying two different occlusion treatments.
    os.environ.update(DAF='0', DEF='0.18', DHF='0.12',
                      DSR='0.68', DSG='0.70', DSB='0.76', DHI='1.20',
                      DSTW='0.0006', DOFF='0.0006', DTS='0.60', DFW='0.0016')
if os.environ.get('CAST_FINISH_UPGRADE') == '1':
    os.environ['DBTN']='1'
exec(compile(entry.read_text(),str(entry),'exec'),globals())
polish_entry=Path(__file__).with_name('cast-apply-approved.py');exec(compile(polish_entry.read_text(),str(polish_entry),'exec'),globals())
finish_entry=Path(__file__).with_name('cast-finish-upgrade.py')
exec(compile(finish_entry.read_text(),str(finish_entry),'exec'),globals())
structure_entry=Path(__file__).with_name('cast-garment-structure.py')
exec(compile(structure_entry.read_text(),str(structure_entry),'exec'),globals())
scene=bpy.context.scene
if config.get('framing') == 'upper-thigh' and '--full-body' not in args:
    female = os.environ['CAST_CHARACTER'] == 'female'
    scene.camera.location = (-0.42, -5.0, 1.21 if female else 1.29)
    scene.camera.rotation_euler = (1.5707963, 0, 0)
    scene.camera.data.ortho_scale = 1.10 if female else 1.18
    scene.render.resolution_x = 2160
    scene.render.resolution_y = 2880
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'
if '--headshot' in args:
    scene.camera.location = (-0.42, -5.0, 1.55 if os.environ['CAST_CHARACTER'] == 'female' else 1.64)
    scene.camera.rotation_euler = (1.5707963, 0, 0)
    scene.camera.data.ortho_scale = 0.50
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'

skin_report={'enabled':False}
if os.environ.get('CAST_SKIN_APPEARANCE')=='1':
    import runpy
    bpy.context.view_layer.update()
    skin_module=runpy.run_path(str(Path(__file__).with_name('cast-skin-appearance.py')))
    skin_report=skin_module['apply_skin_appearance'](scene,os.environ['CAST_CHARACTER'],os.environ.get('CAST_SKIN_HEX',''))

hair_report={'enabled':False}
if os.environ.get('CAST_HAIR_GROOM')=='1':
    import runpy
    hair_module=runpy.run_path(str(Path(__file__).with_name('cast-hair-groom.py')))
    hair_report=hair_module['apply_hair_groom'](scene,os.environ['CAST_CHARACTER'],style=os.environ['CAST_HAIR_STYLE'])

facial_report={'enabled':False}
if os.environ.get('CAST_FACIAL_REFINEMENT')=='1':
    import runpy
    facial_report=runpy.run_path(str(Path(__file__).with_name('cast-facial-refinement.py')))['apply_facial_refinement'](scene,os.environ['CAST_CHARACTER'])

# Hair grooming installs its legacy fibre lamps and denoising profile. Apply
# the supporting studio rig last to keep hair and wardrobe lighting stable.
# Skin uses its own restrained illustrated colour shading.
if os.environ.get('CAST_SKIN_APPEARANCE')=='1':
    skin_report['lights']=skin_module['apply_portrait_lighting'](scene)
    skin_report['contours']=skin_module['refine_face_contours'](scene)
    scene.cycles.use_denoising=True

cloth_report={'enabled':False}
if os.environ.get('CAST_CLOTH_APPEARANCE')=='1':
    import runpy
    cloth_report=runpy.run_path(str(Path(__file__).with_name('cast-cloth-illustrated.py')))['apply_cloth_appearance'](scene,os.environ['CAST_CHARACTER'])

cloth_detail_report={}
if os.environ.get('CAST_CLOTH_APPEARANCE')=='1':
    cloth_detail_report=runpy.run_path(str(Path(__file__).with_name('cast-cloth-detail.py')))['apply_cloth_detail'](scene)

for layer in scene.view_layers:
    for lines in layer.freestyle_settings.linesets:
        if lines.collection:lines.collection.use_fake_user=True
scene.frame_set(config['frame']);scene.render.resolution_percentage=config['resolutionPercentage'];scene.render.image_settings.file_format='PNG'
fit_entry=Path(__file__).with_name('cast-fit-posed-clothing.py');exec(compile(fit_entry.read_text(),str(fit_entry),'exec'),globals())
accessory_report=runpy.run_path(str(Path(__file__).with_name('cast_accessory_quality.py')))['apply_accessory_quality'](scene,os.environ['CAST_CHARACTER'])
height=scene.render.resolution_y*scene.render.resolution_percentage/100
for layer in scene.view_layers:
    for lines in layer.freestyle_settings.linesets:lines.linestyle.thickness*=height/4320
if scene.compositing_node_group is not None:
    for node in scene.compositing_node_group.nodes:
        if node.type=='DILATEERODE':node.inputs['Size'].default_value=max(1,round(node.inputs['Size'].default_value*height/2160))
if '--scene-output' in args:bpy.ops.wm.save_as_mainfile(filepath=args[args.index('--scene-output')+1],compress=True)
output_file.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(output_file)
if '--assemble-only' not in args:bpy.ops.render.render(write_still=True)
metadata={'accessories':accessory_report,'clothDetail':cloth_detail_report,'clothAppearance':cloth_report,'facialRefinement':facial_report,'hairGroom':hair_report,'skinAppearance':skin_report,'finishUpgrade':finish_report,'garmentStructure':structure_report,'clothingFit':fit_report,'sourceVersion':config['sourceVersion'],'renderVersion':config['renderVersion'],'frame':scene.frame_current,'seconds':round(time.monotonic()-started,2),'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'engine':scene.render.engine,'samples':scene.cycles.samples,'camera':scene.camera.name,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma}
output_file.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n');print('CAST_ASSEMBLED_RENDER',json.dumps(metadata),flush=True)

if '--motion-proof' in args:
    motion_entry=Path(__file__).with_name('cast-motion-proof.py')
    exec(compile(motion_entry.read_text(),str(motion_entry),'exec'),globals())

