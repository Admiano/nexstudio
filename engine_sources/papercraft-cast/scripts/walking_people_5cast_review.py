#!/usr/bin/env python3
"""Fast read-only audit of five Walking People. Export PNG + JSON, never source files."""
import bpy, os, json, hashlib
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
src=root/'assets/walking-people-pack/WalkingPeoplepack2024.fbx'
out=Path(os.environ.get('WALKING_PROOF_OUTPUT','walking-people-fast-preview'));out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(src),use_anim=True)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert meshes,'Walking People FBX contained no mesh objects'
textures=list(src.parent.glob('gihapeopletex*.jpg'))
for im in bpy.data.images:
    name=Path(im.filepath.replace(chr(92),'/')).name.lower()
    match=next((f for f in textures if f.name.lower()==name),None)
    if match:im.filepath=str(match);im.reload()
pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
mn=Vector([min(p[i] for p in pts) for i in range(3)]);mx=Vector([max(p[i] for p in pts) for i in range(3)])
cen=(mn+mx)*.5;extent=mx-mn;span=max(extent.z,extent.x*1.4,extent.y*1.4,.1)
report={'source':'WalkingPeoplepack2024.fbx','bytes':src.stat().st_size,
 'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'mesh_count':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),
 'polygons':sum(len(o.data.polygons) for o in meshes),
 'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)} for o in meshes],
 'armatures':[{'name':o.name,'bones':len(o.data.bones)} for o in arms],
 'actions':len(bpy.data.actions),'source_textures_found':[p.name for p in textures],
 'images':[{'name':im.name,'loaded':bool(im.has_data)} for im in bpy.data.images],
 'geometry_unchanged':True,'source_character_count':'NOT VERIFIED: mesh count is not wearer count',
 'license':'CGTrader royalty-free no AI: no training; no source redistribution',
 'visual_review':'SOURCE AUDIT ONLY; no paper or rigging certification'}
(out/'WALKING_PACK_FAST_AUDIT.json').write_text(json.dumps(report,indent=2))
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE'
scene.display.shading.show_cavity=True
scene.render.resolution_x=720;scene.render.resolution_y=680;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
camd=bpy.data.cameras.new('AuditCamera');cam=bpy.data.objects.new('AuditCamera',camd);scene.collection.objects.link(cam)
camd.type='ORTHO';camd.ortho_scale=span*1.22;scene.camera=cam
for label,angle in [('FRONT',(0,-1,.08)),('THREE_QUARTER',(1,-1,.15)),('PROFILE',(1,0,.15))]:
 cam.location=cen+Vector(angle).normalized()*span*2.5
 cam.rotation_euler=(cen-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(out/('SOURCE_'+label+'.png'));bpy.ops.render.render(write_still=True)

# Individual source cast audit. No paper modifiers or deformation; all five
# original figures rendered from their actual, unchanged mesh geometry.
individual=[]
scene.display.shading.background_type='VIEWPORT'
scene.display.shading.background_color=(.88,.84,.80)
for name in ('woman1','man1','woman2','woman3','woman4'):
    obj=next(o for o in meshes if o.name==name)
    for item in meshes:item.hide_render=(item!=obj)
    points=[obj.matrix_world@Vector(c) for c in obj.bound_box]
    a=Vector([min(v[i] for v in points) for i in range(3)])
    b=Vector([max(v[i] for v in points) for i in range(3)])
    mid=(a+b)*.5
    h=max(.01,(b-a).z)
    directions={'THREE_QUARTER':Vector((1,-1,.15)),
                'FRONT':Vector((0,-1,.08))}
    for typ,d in directions.items():
        camd.ortho_scale=h*1.20
        cam.location=mid+d.normalized()*h*2.5
        cam.rotation_euler=(mid-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out/(name+'_SOURCE_'+typ+'.png'))
        bpy.ops.render.render(write_still=True)
        individual.append(name+'_SOURCE_'+typ+'.png')
    head_center=Vector((mid.x,mid.y,a.z+h*.84))
    camd.ortho_scale=h*.44
    cam.location=head_center+Vector((1,-1,.14)).normalized()*h*2.5
    cam.rotation_euler=(head_center-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/(name+'_SOURCE_HEAD.png'))
    bpy.ops.render.render(write_still=True)
    individual.append(name+'_SOURCE_HEAD.png')
report['individual_cast_proof']=individual
report['donor_suitability']='Only visual/static body assessment. No rigs imported.'
(out/'WALKING_PACK_FIVE_CAST_AUDIT.json').write_text(json.dumps(report,indent=2))

print('SOURCE_AUDIT',report['mesh_count'],report['vertices'],report['polygons'],len(arms))