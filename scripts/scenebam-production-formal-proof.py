"""QA-only SceneBam production-assembled character + CC0 formal garment render.

Run AFTER SceneBam's existing cast-quality-reference.py has assembled the actual
production worker appearance in an isolated .blend at frame 27. Never mutate
canonical sources, publish outfit selectors, or claim VM parity without a live hash.
"""
import bpy, json, math, sys, hashlib
from pathlib import Path
from mathutils import Vector

arg = sys.argv[sys.argv.index('--') + 1:]
variant, original, output = arg[:3]
output = Path(output).resolve()
output.mkdir(parents=True, exist_ok=True)
character = variant.split('-')[0]
assert character in ('female','male')
rig = bpy.data.objects.get('Host.rig')
body = bpy.data.objects.get('Host.body')
assert rig is not None and body is not None
assert len(rig.data.bones) == 163, 'PRODUCTION_RIG_NOT_EXPECTED_163_BONES'
assert body.data.shape_keys and len(body.data.shape_keys.key_blocks) >= 34

base_file = bpy.data.filepath
source_name = 'NEX_V1_CC0_FORMAL_SUIT_' + character.upper()
with bpy.data.libraries.load(str(Path(original).resolve()), link=False) as (src, dst):
    assert source_name in src.objects, 'DONOR_GARMENT_NOT_IN_SOURCE_SCENE'
    assert 'Host.rig' in src.objects, 'REFIT_RIG_NOT_IN_SOURCE_SCENE'
    dst.objects = [source_name, 'Host.rig']
new_garment = next((o for o in dst.objects if o and o.name.startswith(source_name)), None)
source_rig = next((o for o in dst.objects if o and o.type=='ARMATURE'), None)
assert new_garment is not None and source_rig is not None
assert len(source_rig.data.bones)==len(rig.data.bones)
error = 0.0
for bone in rig.data.bones:
    other = source_rig.data.bones.get(bone.name)
    assert other is not None, 'RIG_BONE_ABSENT:' + bone.name
    error = max(error, max(abs(a-b) for rowa,rowb in zip(bone.matrix_local,other.matrix_local) for a,b in zip(rowa,rowb)))
assert error < 1e-4, 'FORMAL_DONOR_RIG_REST_MISMATCH:' + str(error)
assert new_garment.get('donorCC0') is True
assert any(m.type=='ARMATURE' for m in new_garment.modifiers)
assert len(new_garment.data.vertices)>1000
assert len(new_garment.vertex_groups)>20
# Remap world placement relative to the validated donor rig. The old absolute
# position put garment meshes alongside SceneBam's assembled performers.
old_pose_matrix = rig.matrix_world @ source_rig.matrix_world.inverted_safe() @ new_garment.matrix_world.copy()
for mod in new_garment.modifiers:
    if mod.type=='ARMATURE': mod.object=rig
new_garment.parent=rig
new_garment.matrix_world=old_pose_matrix
bpy.context.scene.collection.objects.link(new_garment)
new_garment.name = 'SCENEBAM_FORMAL_' + variant.upper().replace('-','_')
new_garment['scenebamExperimental'] = True
new_garment['scenebamSourceStatus'] = 'APPROVED_V3_V6_SOURCE__LIVE_VM_UNVERIFIED'

selected = ['Host.mindfront_f_dress_11'] if character=='female' else ['Host.elvs_male_shirt_untucked_bd1', 'Host.mindfront_male_trousers_2']
hidden=[]
for ob in list(bpy.data.objects):
    if ob == new_garment or ob == rig or ob == body: continue
    if ob.type != 'MESH':continue
    n = ob.name
    track = [ob.get('castFitSource'),ob.get('castGarmentSource'),ob.get('castGarmentProxySource')]
    is_source = any(n==src or n.startswith(src+'.') for src in selected)
    is_derived = any(str(ref).startswith(src) for src in selected for ref in track if ref)
    is_lines = character=='female' and (n.startswith('Host.V64_dress_lines') or n.startswith('Host.V26_garment'))
    if is_source or is_derived or is_lines:
        ob.hide_render=True
        hidden.append(n)
marks = bpy.data.collections.get('V26_GARMENT_MARKS')
if marks:
    for ob in marks.objects:
        ob.hide_render=True
        hidden.append(ob.name)
if source_rig.users == 0:
    bpy.data.objects.remove(source_rig,do_unlink=True)
bpy.context.view_layer.update()

sc=bpy.context.scene
sc.render.engine='CYCLES'
sc.cycles.samples=8
sc.cycles.use_denoising=True
sc.render.resolution_x=540
sc.render.resolution_y=800
sc.render.resolution_percentage=100
sc.render.film_transparent=True
sc.render.image_settings.file_format='PNG'
sc.render.image_settings.color_mode='RGBA'
sc.camera.location=(-.42,-5.0,1.1)
sc.camera.rotation_euler=(math.pi/2,0,0)
sc.camera.data.type='ORTHO'
sc.camera.data.ortho_scale=2.0
sc.view_settings.view_transform='Standard'

frames=(1,27,56,125,234,338,451,568,710,891)
checks=[]
for frame in frames:
    sc.frame_set(frame)
    bpy.context.view_layer.update()
    ob=new_garment.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ob.to_mesh()
    assert mesh and len(mesh.vertices)>1000
    points=[ob.matrix_world@v.co for v in mesh.vertices]
    assert all(all(math.isfinite(float(v)) for v in p) for p in points)
    lo=[min(p[k] for p in points) for k in range(3)]
    hi=[max(p[k] for p in points) for k in range(3)]
    assert all(0.025 < hi[k]-lo[k] < 4 for k in range(3))
    checks.append({'frame':frame,'evaluatedVertices':len(points),'bounds':[lo,hi]})
    ob.to_mesh_clear()

sc.frame_set(27)
bpy.ops.wm.save_as_mainfile(filepath=str(output/(variant+'-production-assembled.blend')), compress=True)
views=[('front',27,False),('threeq',27,True),('pose-338',338,False),('pose-891',891,False)]
files=[]
for name,frame,threeq in views:
    sc.frame_set(frame)
    sc.camera.location=(-2.3,-4.6,1.1) if threeq else (-.42,-5.0,1.1)
    sc.camera.rotation_euler=(Vector((-.42,0,1.1))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(output/(variant+'-'+name+'.png'))
    bpy.ops.render.render(write_still=True)
    p=Path(sc.render.filepath)
    assert p.stat().st_size > 10000, 'EMPTY_PRODUCTION_RENDER:' + name
    files.append({'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
report={'variant':variant,'baseScene':base_file,'workerAssembled':True,'previewQuality':'technical_preview_540x800_8_cycles_samples',
    'liveVMParityCertified':False,'exactLiveVMHashProvided':False,
    'sourceRigRestMaxError':error,'productionRigBones':len(rig.data.bones),
    'productionBodyShapeKeys':len(body.data.shape_keys.key_blocks),
    'garmentVertexCount':len(new_garment.data.vertices),
    'garmentWeightGroups':len(new_garment.vertex_groups),
    'hiddenPreviousClothing':hidden,'framesChecked':checks,
    'renders':files,'collisionCertified':False,'artApproved':False,
    'status':'REPO_PRODUCTION_ASSEMBLY_QA__VM_NOT_VERIFIED'}
(output/'production-proof.json').write_text(json.dumps(report,indent=2)+'\n')
print('SCENEBAM_PRODUCTION_FORMAL_REPRO_PASS',variant,json.dumps({'images':len(files),'rig':len(rig.data.bones),'restError':error}),flush=True)
