"""Full-timeline checks for the V10 outline and head-bound facial ink."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

s=bpy.context.scene
p='Host' if 'HOST_' in bpy.data.filepath else 'Guest'
body=bpy.data.objects[p+'.body']
rig=bpy.data.objects[p+'.rig']
jaw=bpy.data.objects[p+'.V10_jaw']
face=[o for o in bpy.data.objects if o.name.startswith(p+'.V10_') and o.type=='MESH']
assert len(face)==(5 if p=='Host' else 7)
assert s.frame_end==360 and s.render.fps==24
assert s.render.use_freestyle and s.view_layers[0].use_freestyle
layer=s.view_layers[0]
assert layer.use_pass_object_index
line=layer.freestyle_settings.linesets[0]
assert line.select_border and line.select_by_collection
assert not any(getattr(line,'select_'+name) for name in
               ('silhouette','contour','external_contour','suggestive_contour',
                'crease','ridge_valley','material_boundary','edge_mark'))
assert len(line.collection.all_objects)==1
assert line.collection.all_objects[0].name==p+('.female_elegantsuit01' if p=='Host' else '.male_elegantsuit01')
assert s.compositing_node_group and s.compositing_node_group.name.startswith(p+'_V10_MASK_OUTLINE')
assert body.pass_index==1
assert all(o.parent==rig and o.parent_type=='BONE' and o.parent_bone=='head' for o in face)
assert all(o.visible_camera and not o.visible_shadow and not o.visible_diffuse
           and not o.visible_glossy and not o.visible_transmission
           and not o.visible_volume_scatter for o in face)
assert not jaw.modifiers

head_local=None
max_head_drift=0.
worst_jaw_depth=-1e10
sampled_jaw_hits=0
for frame in range(1,361):
    s.frame_set(frame)
    dep=bpy.context.evaluated_depsgraph_get()
    head=rig.matrix_world@rig.pose.bones['head'].matrix
    local=head.inverted()@jaw.matrix_world.translation
    if head_local is None:head_local=local.copy()
    max_head_drift=max(max_head_drift,(local-head_local).length)
    b=body.evaluated_get(dep)
    inv=b.matrix_world.inverted()
    direction=inv.to_3x3()@Vector((0,1,0))
    for vert in jaw.data.vertices:
        world=jaw.matrix_world@vert.co
        ok,hit,normal,idx=b.ray_cast(inv@Vector((world.x,-5.,world.z)),direction)
        if not ok:continue
        sampled_jaw_hits+=1
        diff=world.y-(b.matrix_world@hit).y
        worst_jaw_depth=max(worst_jaw_depth,diff)
assert max_head_drift<1e-5,max_head_drift
assert worst_jaw_depth<-.001,(p,worst_jaw_depth)
report={'character':p,'frames':360,'fps':24,'mask_outline':True,
        'freestyle_only_fixed_garment_borders':True,
        'head_bound_face_marks':len(face),
        'face_marks_camera_only':True,
        'max_head_anchor_drift_m':round(max_head_drift,7),
        'least_jaw_front_clearance_m':round(-worst_jaw_depth,5),
        'jaw_surface_ray_samples':sampled_jaw_hits}
out=Path(bpy.data.filepath).parent/(p.lower()+'_V10_QA.json')
out.write_text(json.dumps(report,indent=2)+'\n')
print('V10_QA',json.dumps(report),flush=True)
