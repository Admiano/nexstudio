#!/usr/bin/env python3
"""Create internal, reduced-density editable art-study scene for original licensed
Walking People. FOR PRIVATE USER DEVELOPMENT ONLY; never commit binary output.
No full original source, nor source JPG atlas or scanned texture material retained.
"""
import bpy,hashlib,json,os
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
FBX=ROOT/'assets/walking-people-pack/WalkingPeoplepack2024.fbx'
OUT=Path(os.getenv('WALKING_INTERNAL_OUTPUT','walking-people-internal-review'))
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX),use_anim=False)
donors={o.name:o for o in bpy.context.scene.objects if o.type=='MESH' and o.name in ('man1','woman1')}
assert len(donors)==2,list(donors)
stats=[]
copies=[]
for ix,name in enumerate(('man1','woman1')):
    source=donors[name]
    copy=source.copy(); copy.data=source.data.copy()
    bpy.context.scene.collection.objects.link(copy)
    copy.name='PRIVATE_PAPER_ART_BASE_'+name.upper()
    w=copy.matrix_world.copy()
    copy.parent=None;copy.matrix_world=w
    for m in list(copy.modifiers):copy.modifiers.remove(m)
    bef=len(copy.data.polygons)
    dec=copy.modifiers.new('Density reduction for PRIVATE modeling reference','DECIMATE')
    dec.ratio=.125
    for o in bpy.context.selected_objects:o.select_set(False)
    copy.select_set(True)
    bpy.context.view_layer.objects.active=copy
    bpy.ops.object.modifier_apply(modifier=dec.name)
    copy.select_set(False)
    # Crucial: detached sample textures and original source material remain
    # on upstream GitHub branch, not in this internal editable study file.
    copy.data.materials.clear()
    mat=bpy.data.materials.new('PRIVATE_NeutralPaper_'+name)
    mat.diffuse_color=(.69,.55,.40,1) if name=='woman1' else (.72,.66,.55,1)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value=mat.diffuse_color
        bsdf.inputs['Roughness'].default_value=.95
    copy.data.materials.append(mat)
    for face in copy.data.polygons:face.use_smooth=False
    # Separate display placement; original full mesh is not modified.
    copy.location.x += (-1.35 if name=='man1' else 1.35)
    copies.append(copy)
    stats.append({'donor':name,'original_triangles':bef,'private_reduced_triangles':len(copy.data.polygons),'vertices':len(copy.data.vertices)})
for obj in list(bpy.data.objects):
    if obj not in copies:bpy.data.objects.remove(obj,do_unlink=True)
for im in list(bpy.data.images):
    bpy.data.images.remove(im,do_unlink=True)
# Avoid retaining source-fidelity meshes as unused datablocks.
for mesh in list(bpy.data.meshes):
    if mesh.users==0:bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users==0:bpy.data.materials.remove(mat)
for ob in copies: ob.hide_render=False
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_cavity=True
scene.display.shading.background_type='VIEWPORT'
scene.display.shading.background_color=(.84,.81,.77)
mn=Vector([min((o.matrix_world@Vector(v))[k] for o in copies for v in o.bound_box) for k in range(3)])
mx=Vector([max((o.matrix_world@Vector(v))[k] for o in copies for v in o.bound_box) for k in range(3)])
mid=(mn+mx)/2;size=max((mx-mn).x,(mx-mn).z,(mx-mn).y,.1)
camdata=bpy.data.cameras.new('Front review camera');camdata.type='ORTHO';camdata.ortho_scale=size*1.2
cam=bpy.data.objects.new('Front review camera',camdata);scene.collection.objects.link(cam)
cam.location=mid+Vector((1,-1,.12)).normalized()*size*2.5
cam.rotation_euler=(mid-cam.location).to_track_quat('-Z','Y').to_euler()
scene.camera=cam
scene.render.resolution_x=1000;scene.render.resolution_y=760
scene.render.resolution_percentage=100
scene.render.filepath=str(OUT/'PRIVATE_EDITABLE_BASE_BLENDER_PREVIEW.png')
bpy.ops.render.render(write_still=True)
p=OUT/'PRIVATE_USER_WORKING_COPY_RIG_FREE.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(p))
test=[o for o in bpy.data.objects if o.type=='MESH']
assert len(test)==2,len(test)
assert len(bpy.data.images)==0,len(bpy.data.images)
details={'source_sha256':hashlib.sha256(FBX.read_bytes()).hexdigest(),
  'licensed_asset':'CGTrader Walking People Pack: user-controlled source',
  'usage':'Only private artistic R&D; not for upload to public repo or asset marketplace',
  'original_full_resolution_geometry_excluded':True,
  'original_texture_atlas_images_excluded':True,
  'no_armature':True,'models':stats,'reopened':True,'blend_file':p.name,
  'quality_gate':'UNAPPROVED paper; these are geometry donors only'}
(OUT/'PRIVATE_EDITABLE_SOURCE_AUDIT.json').write_text(json.dumps(details,indent=2))
print('PRIVATE_USER_STUDY_VALID',json.dumps(details))
