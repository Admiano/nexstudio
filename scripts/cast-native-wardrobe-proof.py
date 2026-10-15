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
    assert garment.hide_render and garment.get('castWardrobeOriginalUV')
    visual=next(x for x in scene.objects if x.get('castFitSource')==selected)
    assert not visual.hide_render and len(visual.data.materials)==len(garment.data.materials)
    bpy.context.view_layer.update()
destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
result={'variant':variant,'selectedGarment':selected,'nativePipeline':True,
        'selectionStage':'before-stable-finish','sharedStages':['cast-finish-upgrade','cast-garment-structure','cast-cloth-illustrated','cast-cloth-detail','cast-fit-posed-clothing'],
        'poseFrames':[27,338,891],'fabric':finish,'structure':structure,
        'cloth':cloth,'detail':detail,'formal':report,'collisionCertified':False}
destination.write_text(json.dumps(result,indent=2,default=str)+'\n')
print('CAST_NATIVE_WARDROBE_PIPELINE_PASS',variant,flush=True)
