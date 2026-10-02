"""Bind ribbons to the source rig when Surface Deform rejects a proxy.

Inputs are g (garment), ro (ribbon), rig, sd and the current bind pose.
Interpolated garment skin weights and inverse blended bone transforms place
ribbon vertices in rig rest space. Visible garment topology is untouched.
"""
import bpy,math
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

def bind_garment_lines(garment,ribbon,armature,rejected_modifier):
    deps=bpy.context.evaluated_depsgraph_get();evaluated=garment.evaluated_get(deps);mesh=evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        triangles=[tuple(t.vertices) for t in mesh.loop_triangles]
        points=[evaluated.matrix_world@v.co for v in mesh.vertices]
        tree=BVHTree.FromPolygons(points,triangles,all_triangles=True)
        names={vg.index:vg.name for vg in garment.vertex_groups if vg.name in armature.pose.bones}
        weights=[{names[x.group]:x.weight for x in v.groups if x.group in names and x.weight>0} for v in mesh.vertices]
        transforms={name:armature.pose.bones[name].matrix@armature.data.bones[name].matrix_local.inverted() for name in names.values()}
        inverse_world=armature.matrix_world.inverted();rest=[];bindings=[];reference=[]
        for vertex in ribbon.data.vertices:
            world=ribbon.matrix_world@vertex.co
            reference.append(world.copy())
            hit,normal,face,distance=tree.find_nearest(world,0.025)
            if hit is None:raise RuntimeError('CAST_RIBBON_BIND_TOO_FAR:'+ribbon.name)
            ids=triangles[face];a,b,c=[points[i] for i in ids]
            if (b-a).cross(c-a).length_squared<1e-18:
                nearest=min(ids,key=lambda i:(points[i]-hit).length_squared);blend=weights[nearest]
            else:
                bary=barycentric_transform(hit,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
                mix=[max(0,min(1,v)) for v in bary];total=sum(mix);mix=[v/total for v in mix];blend={}
                for index,factor in zip(ids,mix):
                    for name,weight in weights[index].items():blend[name]=blend.get(name,0)+weight*factor
            total=sum(blend.values())
            if total<=1e-8:raise RuntimeError('CAST_RIBBON_BIND_NO_WEIGHTS:'+ribbon.name)
            blend={name:weight/total for name,weight in blend.items()}
            transform=Matrix([[sum(transforms[name][row][col]*weight for name,weight in blend.items()) for col in range(4)] for row in range(4)])
            local=transform.inverted()@inverse_world@world
            if not all(math.isfinite(v) for v in local):raise RuntimeError('CAST_RIBBON_BIND_NONFINITE')
            rest.append(local);bindings.append(blend)
    finally:evaluated.to_mesh_clear()
    ribbon.modifiers.remove(rejected_modifier)
    for vertex,position in zip(ribbon.data.vertices,rest):vertex.co=position
    for name in sorted({name for binding in bindings for name in binding}):
        group=ribbon.vertex_groups.get(name) or ribbon.vertex_groups.new(name=name)
        for index,binding in enumerate(bindings):
            if name in binding:group.add([index],binding[name],'REPLACE')
    ribbon.parent=armature;ribbon.matrix_parent_inverse=Matrix.Identity(4);ribbon.matrix_basis=Matrix.Identity(4)
    modifier=ribbon.modifiers.new('Cast garment skin binding','ARMATURE');modifier.object=armature
    ribbon['castRibbonBinding']='interpolated-garment-skin-weights'
    ribbon.data.update();bpy.context.view_layer.update()
    check=ribbon.evaluated_get(bpy.context.evaluated_depsgraph_get());result=check.to_mesh()
    try:
        error=max((check.matrix_world@vertex.co-target).length for vertex,target in zip(result.vertices,reference))
        if len(result.vertices)!=len(reference) or error>0.0001:raise RuntimeError('CAST_RIBBON_BIND_POSE_MISMATCH:'+str(error))
        ribbon['castRibbonBindMaxError']=error
    finally:check.to_mesh_clear()
    print('CAST_RIBBON_SKIN_BOUND',garment.name,len(rest),flush=True)

bind_garment_lines(g,ro,rig,sd)
