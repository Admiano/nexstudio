"""Blender proof that formal selection goes through the native garment pipeline.

Source is an authentic assembled V3/V6 candidate rig, not a generated mock.
One proof for each real suit; no live-VM certification implied.
"""
import bpy,os,sys,runpy,json,hashlib
from pathlib import Path
variant,suit,tie,destination=sys.argv[sys.argv.index('--')+1:][:4]
os.environ.update(CAST_CHARACTER=variant.split('-')[0],
    CAST_FORMAL_ID=variant,CAST_FORMAL_SUIT_HEX=suit,CAST_FORMAL_TIE_HEX=tie,
    CAST_FINISH_UPGRADE='1',CAST_CLOTH_APPEARANCE='1',
    CAST_GARMENT_STRUCTURE_PILOT='1')
root=Path(__file__).resolve().parent
scene=bpy.context.scene
def load(name):
    return runpy.run_path(str(root/name))
report=load('cast-apply-formal.py')['apply_formal'](scene,variant,suit,tie)
selected=report['selectedGarment']
assert report['nativeWardrobe']
assert selected==os.environ['DOBJ']==os.environ['GARMS'].split('=')[0]
finish=load('cast-finish-upgrade.py')['finish_report']
structure=load('cast-garment-structure.py')['structure_report']
cloth=load('cast-cloth-illustrated.py')['apply_cloth_appearance'](scene,os.environ['CAST_CHARACTER'])
detail=load('cast-cloth-detail.py')['apply_cloth_detail'](scene)
for frame in (27,338,891):
    scene.frame_set(frame)
    fit=load('cast-fit-posed-clothing.py')['fit_report']
    match=[x for x in fit if x.get('object')==selected]
    assert len(match)==1 and match[0]['evaluatedPoseFrame']==frame,fit
    assert match[0]['poseEvaluatedOnSharedRig'] and not match[0]['collisionCertified']
    assert selected in {x['object'] for x in finish['fabrics']}
    assert selected in {x['object'] for x in structure}
    assert selected in {x['object'] for x in cloth['garments']}
    assert selected in {x['object'] for x in detail['garments']}
    garment=bpy.data.objects[selected]
    assert not garment.hide_render and garment.get('castWardrobeOriginalUV')
    assert garment.parent==bpy.data.objects['Host.rig']
    assert any(m.type=='ARMATURE' and m.object==garment.parent for m in garment.modifiers)
    assert not any(x.get('castFitSource')==selected for x in scene.objects), 'ANIMATED_GARMENT_REPLACED_WITH_STATIC_MESH'
    assert match[0]['animatedSourcePreserved'] and not match[0]['bakedStillMesh']
    bpy.context.view_layer.update()
destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
# Actual render from the new native path, not the old post-pipeline donor preview.
# Restore the approved preview pose through the same evaluated fitter.
scene.frame_set(27)
preview_fit=load('cast-fit-posed-clothing.py')['fit_report']
assert any(row.get('object')==selected and row.get('evaluatedPoseFrame')==27 for row in preview_fit)
assert not any(obj.get('castFitSource')==selected for obj in scene.objects), 'CONTINUOUS_MOTION_GARMENT_BAKED'
scene.render.engine='CYCLES'
scene.cycles.samples=8
scene.cycles.use_denoising=True
scene.render.resolution_x=420
scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
from mathutils import Vector
scene.camera.location=(-.42,-5.0,1.13)
scene.camera.rotation_euler=(Vector((-.42,0,1.13))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.type='ORTHO'
scene.camera.data.ortho_scale=1.65
scene.view_settings.view_transform='Standard'
image_path=destination.with_suffix('.png')
scene.render.filepath=str(image_path)
bpy.ops.render.render(write_still=True)
assert image_path.is_file() and image_path.stat().st_size>10000,'CAST_NATIVE_RENDER_MISSING'
result={'variant':variant,'selectedGarment':selected,'nativePipeline':True,
        'selectionStage':'before-stable-finish','sharedStages':['cast-finish-upgrade','cast-garment-structure','cast-cloth-illustrated','cast-cloth-detail','cast-fit-posed-clothing'],
        'poseFrames':[27,338,891],'nativePreviewPNG':image_path.name,
        'nativePreviewSHA256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'fabric':finish,'structure':structure,
        'cloth':cloth,'detail':detail,'formal':report,'collisionCertified':False}
destination.write_text(json.dumps(result,indent=2,default=str)+'\n')
print('CAST_NATIVE_WARDROBE_PIPELINE_PASS',variant,flush=True)
