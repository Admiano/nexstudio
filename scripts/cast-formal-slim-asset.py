"""Export ONLY the authentic CC0 tailored suit, 163-bone rest rig and packed texture.
Keep shape, UVs, weights and material. No base body or transient baked scene.
"""
import bpy,sys,hashlib,json
from pathlib import Path

original,variant,destination=sys.argv[sys.argv.index('--')+1:][:3]
name='SCENEBAM_FORMAL_'+variant.upper().replace('-','_')
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(Path(original).resolve()),link=False) as (src,dst):
    assert name in src.objects and 'Host.rig' in src.objects
    dst.objects=[name,'Host.rig']
garment=next((o for o in dst.objects if o and o.name.startswith(name)),None)
rig=next((o for o in dst.objects if o and o.type=='ARMATURE'),None)
assert garment and rig and garment.type=='MESH'
assert len(rig.data.bones)==163
assert len(garment.data.materials)==1 and garment.data.uv_layers.active
for obj in (rig,garment):
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_render=False
    obj.hide_viewport=False
garment.parent=rig
for modifier in garment.modifiers:
    if modifier.type=='ARMATURE':modifier.object=rig
rig.animation_data_clear()
garment.animation_data_clear()
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file:
        image.pack()
assert any(image.packed_file for image in bpy.data.images)
file=Path(destination).resolve()
file.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
assert file.stat().st_size<95000000
result={'variant':variant,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
        'bytes':file.stat().st_size,'meshVertices':len(garment.data.vertices),
        'meshFaces':len(garment.data.polygons),'restBoneCount':len(rig.data.bones),
        'packedTextures':[image.name for image in bpy.data.images if image.packed_file]}
print('CAST_FORMAL_LIGHTWEIGHT_SOURCE_VERIFIED',json.dumps(result),flush=True)
