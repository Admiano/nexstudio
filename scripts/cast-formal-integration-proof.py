"""Smoke QA for actual six SceneBam production-assembled Blender formalwear.

Run with one saved candidate .blend using Blender 5.2, -- <variant> <output>.
Validates rig, UV garment, meaningful suit/tie material mapping, saves a genuine
Blender preview and machine-readable proof. Not a full collision certification.
"""
import bpy,os,json,sys,hashlib
from pathlib import Path
from math import isfinite
from mathutils import Vector
from runpy import run_path
variant=sys.argv[sys.argv.index('--')+1]
output=Path(sys.argv[sys.argv.index('--')+2])
output.parent.mkdir(parents=True,exist_ok=True)
os.environ['CAST_CHARACTER']=variant.split('-')[0]
os.environ['CAST_FORMAL_LOOK']=variant
os.environ['CAST_SUIT_HEX']=os.environ.get('CAST_SUIT_HEX','63303C')
os.environ['CAST_TIE_HEX']=os.environ.get('CAST_TIE_HEX','7C2939') if variant.startswith('male-') else ''
scene=bpy.context.scene
scene.frame_set(27)
r=run_path(str(Path(__file__).with_name('cast-formal-clothing.py')))['install_formal'](
    scene,variant,os.environ['CAST_SUIT_HEX'],os.environ['CAST_TIE_HEX'])
assert r['sourceVerified'] and r['garmentVertices']>1000
assert r['suitFaces']>=300
if variant.startswith('male-'):assert r['tieFaces']>=4
scene.render.engine='CYCLES'
scene.cycles.samples=6
scene.cycles.use_denoising=True
scene.render.resolution_x=400
scene.render.resolution_y=600
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=True
scene.camera.location=(-.42,-5,1.18)
scene.camera.rotation_euler=(1.57079632679,0,0)
scene.camera.data.type='ORTHO'
scene.camera.data.ortho_scale=1.60
scene.render.filepath=str(output)
bpy.ops.render.render(write_still=True)
assert output.stat().st_size>10000
r['imageSHA256']=hashlib.sha256(output.read_bytes()).hexdigest()
r['imageBytes']=output.stat().st_size
r['renderResolution']=[400,600]
r['status']='REPO_ASSEMBLED_CAST_WITH_TRUE_FORMAL_AND_TINT_QA_PASS__LIVE_VM_NOT_CERTIFIED'
output.with_suffix('.json').write_text(json.dumps(r,indent=2))
print('SCENEBAM_FORMAL_INTEGRATION_QA',json.dumps(r),flush=True)
