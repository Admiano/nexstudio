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
 if hexcode=='ORIGINAL':
  assert blend is None,'NATIVE_UV_COLOUR_RESET_APPLIED_TINT'
  assert any(n.type=='TEX_IMAGE' and n.image and n.image.packed_file for n in material.node_tree.nodes),'NATIVE_UV_TEXTURE_MISSING'
 else:
  assert blend is not None
  expected=adapter['_colour'](hexcode)
  assert all(abs(float(a)-float(b))<.0001 for a,b in zip(blend.inputs[2].default_value,expected))
 assert any(m.type=='ARMATURE' and m.object==bpy.data.objects['Host.rig'] for m in obj.modifiers)
assert report['restError']<1e-4
assert report['torsoXDeviation']<=0.12,report
if variant.startswith('female'):
 leg_ink=bpy.data.objects.get('Host.lineart_lower_legs')
 assert leg_ink is not None and leg_ink.hide_render,'CAST_FORMAL_LEGACY_LOWER_LEG_OVERLAY_STILL_VISIBLE'
 assert 'Host.lineart_lower_legs' in report['hiddenOriginalGarments'],'CAST_FORMAL_CULPRIT_NOT_RECORDED'

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
report.update({'output':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'renderSamples':8,'testFrame':27,'nativeUVRestored':suit=='ORIGINAL' and tie=='ORIGINAL'})
# Diagnostic-only isolation of flesh-coloured pixels in two female trouser variants.
# Never alter the approved garment/character or treat this as a fit repair.
if os.environ.get('SCENEBAM_FORMAL_OBJECT_ID_DIAGNOSTICS')=='1' and variant.startswith('female') and suit=='ORIGINAL' and tie=='ORIGINAL':
    from collections import Counter
    from mathutils import Vector
    camera=scene.camera
    corners=camera.data.view_frame(scene=scene)
    xmin,xmax=min(p.x for p in corners),max(p.x for p in corners)
    ymin,ymax=min(p.y for p in corners),max(p.y for p in corners)
    depsgraph=bpy.context.evaluated_depsgraph_get()
    direction=camera.matrix_world.to_quaternion() @ Vector((0,0,-1))
    samples=[]
    # These coordinates were measured on raw 420 x 640 real frames.
    for py in (505,510,515,520,525):
        for px in (225,230,234,238,242):
            u=(px+0.5)/420
            v=(py+0.5)/640
            origin=camera.matrix_world @ Vector((xmin+u*(xmax-xmin),ymax-v*(ymax-ymin),0))
            hit,location,normal,face_index,hit_object,_=scene.ray_cast(depsgraph,origin,direction,distance=100)
            mat=None
            if hit and hit_object.type=='MESH':
                evaluated=hit_object.evaluated_get(depsgraph)
                mesh_hit=evaluated.to_mesh()
                try:
                    if face_index>=0 and face_index<len(mesh_hit.polygons):
                        slot=mesh_hit.polygons[face_index].material_index
                        if slot<len(hit_object.material_slots) and hit_object.material_slots[slot].material:
                            mat=hit_object.material_slots[slot].material.name
                finally:
                    evaluated.to_mesh_clear()
            samples.append({'x':px,'y':py,'object':hit_object.name if hit else None,'material':mat})
    body=bpy.data.objects['Host.body']
    old_hidden=body.hide_render
    body.hide_render=True
    scene.render.filepath=str(dest/(variant+'-diagnostic-body-hidden.png'))
    bpy.ops.render.render(write_still=True)
    body.hide_render=old_hidden
    scene.render.filepath=str(target)
    report['skinGapDiagnostic']={'samples':samples,'bodyHiddenFrame':variant+'-diagnostic-body-hidden.png',
                                  'rayHitCounts':dict(Counter(x['object'] for x in samples))}
    # A ray-cast can hit hide_render objects, so a ray hit is not reliable
    # evidence of which surface contributes a rendered pixel. Render a
    # reversible Object Info colour-ID pass with all real visibility rules.
    # This is diagnostic evidence only: it cannot alter shipped textures.
    import colorsys
    palette={}
    original_colors={}
    candidates=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
    for n,o in enumerate(sorted(candidates,key=lambda x:x.name)):
        rgb=colorsys.hsv_to_rgb((n*0.61803398875)%1.0,0.84,0.94)
        original_colors[o.name]=tuple(o.color)
        o.color=(*rgb,1.0)
        palette[o.name]=list(rgb)
    id_material=bpy.data.materials.new('SCENEBAM_FORMAL_QA_ONLY_OBJECT_ID')
    id_material.use_nodes=True
    nodes=id_material.node_tree.nodes
    nodes.clear()
    info=nodes.new('ShaderNodeObjectInfo')
    emiss=nodes.new('ShaderNodeEmission')
    output=nodes.new('ShaderNodeOutputMaterial')
    id_material.node_tree.links.new(info.outputs['Color'],emiss.inputs['Color'])
    id_material.node_tree.links.new(emiss.outputs['Emission'],output.inputs['Surface'])
    layer=scene.view_layers[0]
    original_override=layer.material_override
    original_freestyle=scene.render.use_freestyle
    try:
        layer.material_override=id_material
        scene.render.use_freestyle=False
        scene.render.filepath=str(dest/(variant+'-diagnostic-object-ids.png'))
        bpy.ops.render.render(write_still=True)
    finally:
        layer.material_override=original_override
        scene.render.use_freestyle=original_freestyle
        scene.render.filepath=str(target)
        for name,rgba in original_colors.items():
            bpy.data.objects[name].color=rgba
        bpy.data.materials.remove(id_material)
    (dest/(variant+'-diagnostic-object-palette.json')).write_text(json.dumps(palette,indent=2)+'\n')
    report['skinGapDiagnostic']['objectIdImage']=variant+'-diagnostic-object-ids.png'
    report['skinGapDiagnostic']['objectIdPalette']=variant+'-diagnostic-object-palette.json'

if len(args)>4 and args[4]=='poses':
 # Genuine proof of the same rigged garment in three-quarter and gesture
 # frames. No new assets or generated character imagery.
 scene.camera.location=(-2.3,-4.6,1.13)
 scene.camera.rotation_euler=(Vector((-.42,0,1.13))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(dest/(variant+'-threeq-native.png'))
 bpy.ops.render.render(write_still=True)
 scene.camera.location=(-.42,-5.0,1.13)
 scene.camera.rotation_euler=(Vector((-.42,0,1.13))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
 for frame in (338,891):
  scene.frame_set(frame)
  scene.render.filepath=str(dest/(variant+'-pose-'+str(frame)+'.png'))
  bpy.ops.render.render(write_still=True)
 report['poseRenders']=[variant+'-threeq-native.png',variant+'-pose-338.png',variant+'-pose-891.png']
(dest/(variant+'-'+suit+'-'+tie+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print('CAST_FORMAL_INDEPENDENT_MATERIAL_RENDER_PASS',variant,suit,tie,flush=True)
