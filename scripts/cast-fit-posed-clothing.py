"""Rebuild posed garment clearance for each requested frame, without accumulation."""
import bpy,os,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def fit_posed_clothing(scene):
    # Evaluated meshes are disposable results. Restore source visibility and
    # remove previous results before evaluating another pose. Source rigs,
    # weights and meshes remain the authority for every frame.
    for result in list(bpy.data.objects):
        source_name=result.get('castFitSource')
        if not source_name:continue
        source=bpy.data.objects.get(source_name)
        if source is not None:source.hide_render=source.get('castFitOriginalHideRender',False)
        mesh=result.data
        bpy.data.objects.remove(result,do_unlink=True)
        if mesh.users==0:bpy.data.meshes.remove(mesh)
    bpy.context.view_layer.update()
    fit_report=[]
    if os.environ['CAST_CHARACTER']=='male':
        garments=[bpy.data.objects.get(x.split('=')[0]) for x in os.environ.get('GARMS','').split(';') if x]
        tops=[o for o in garments if o and not any(k in o.name.lower() for k in ('trouser','jeans','pants','shoe','sneaker'))]
        tucked=bool(tops and 'tucked' in tops[0].name.lower() and 'untucked' not in tops[0].name.lower())
        if tucked:
            deps=bpy.context.evaluated_depsgraph_get();top=tops[0]
            pants=next(o for o in garments if o and any(k in o.name.lower() for k in ('trouser','jeans','pants')))
            pe=pants.evaluated_get(deps);pm=pe.to_mesh();pp=[pe.matrix_world@v.co for v in pm.vertices]
            center=sum(p.x for p in pp)/len(pp)
            waist=max(p.z for p in pp if abs(p.x-center)<0.12)
            pants_tree=BVHTree.FromPolygons(pp,[list(p.vertices) for p in pm.polygons]);pe.to_mesh_clear()
            te=top.evaluated_get(deps);tm=te.to_mesh();tp=[te.matrix_world@v.co for v in tm.vertices]
            middle=sum(p.y for p in tp)/len(tp)
            waist=max(p.z for p in pp if abs(p.x-center)<0.12 and p.y<middle)
            hem=min(p.z for p in tp if abs(p.x-center)<0.12 and p.y<middle);te.to_mesh_clear()
            extension=max(0,hem-waist+0.018)
            if extension>0.12:raise RuntimeError('CAST_TUCKED_HEM_FIT_OUT_OF_BOUNDS')
            fitted_objects=[top]+[o for o in bpy.data.objects if o.get('castGarmentSource')==top.name]
            for ob in fitted_objects:
                evaluated=ob.evaluated_get(deps);fitted=bpy.data.meshes.new_from_object(evaluated,depsgraph=deps);inverse=ob.matrix_world.inverted();adjusted=0
                for v in fitted.vertices:
                    point=ob.matrix_world@v.co
                    weight=max(0,min(1,(hem+0.07-point.z)/0.07))
                    if weight==0:continue
                    point.z-=extension*weight
                    front=point.y<middle;direction=Vector((0,1 if front else -1,0))
                    hit,normal,face,distance=pants_tree.ray_cast(Vector((point.x,-3 if front else 3,point.z)),direction,6)
                    if hit is not None and abs(hit.y-point.y)<0.08:
                        inside=hit.y+(0.006 if front else -0.006)
                        point.y=max(point.y,inside) if front else min(point.y,inside)
                    v.co=inverse@point;adjusted+=1
                if any(not all(math.isfinite(c) for c in v.co) for v in fitted.vertices):raise RuntimeError('CAST_GARMENT_NONFINITE:'+ob.name)
                fitted.update();display=bpy.data.objects.new(ob.name+'.preview-fit',fitted);display.matrix_world=ob.matrix_world.copy()
                for collection in ob.users_collection:collection.objects.link(display)
                display.pass_index=ob.pass_index
                display['castFitSource']=ob.name
                if 'castFitOriginalHideRender' not in ob:ob['castFitOriginalHideRender']=ob.hide_render
                ob.hide_render=True
                fit_report.append({'object':ob.name,'vertexCount':len(fitted.vertices),'adjustedVertices':adjusted,'finite':True,'hemExtension':extension,'preservedWorldAxes':['X']})
                print('POSED_TUCKED_HEM',ob.name,extension,adjusted,flush=True)
        if tops and not tucked:
            # An untucked top hangs over the trousers. Where the posed trouser
            # waist (or the trouser just below the hem) reaches past the top,
            # the top is let out radially to cover it; trousers are untouched.
            top=tops[0];deps=bpy.context.evaluated_depsgraph_get()
            pants=[o for o in garments if o and any(k in o.name.lower() for k in ('trouser','jeans','pants'))]
            pants_points=[];pants_faces=[]
            for o in pants:
                pe=o.evaluated_get(deps);pm=pe.to_mesh();base=len(pants_points)
                pants_points+=[pe.matrix_world@v.co for v in pm.vertices];pants_faces+=[[base+i for i in p.vertices] for p in pm.polygons];pe.to_mesh_clear()
            pants_tree=BVHTree.FromPolygons(pants_points,pants_faces)
            ev=top.evaluated_get(deps);mesh=ev.to_mesh()
            limb=[any(k in g.name.lower() for k in ('arm','wrist','metacarpal','finger','hand','shoulder','clavicle')) for g in top.vertex_groups]
            def limb_weight(v):
                total=sum(g.weight for g in v.groups if g.group<len(limb))
                return sum(g.weight for g in v.groups if g.group<len(limb) and limb[g.group])/total if total else 0
            points=[ev.matrix_world@v.co for v in mesh.vertices];limb_weights=[limb_weight(v) for v in mesh.vertices]
            torso=[list(p.vertices) for p in mesh.polygons if sum(limb_weights[i] for i in p.vertices)/len(p.vertices)<0.5]
            top_tree=BVHTree.FromPolygons(points,torso)
            torso_points=[points[i] for i in {i for f in torso for i in f}]
            ev.to_mesh_clear()
            hem=min(p.z for p in torso_points)
            band=[p for p in torso_points if p.z<hem+0.20]
            center=sum(p.x for p in band)/len(band);middle=sum(p.y for p in band)/len(band)
            def outer_reach(tree,z,radial):
                # Distance from the torso axis to the outermost surface along radial.
                hit,normal,face,distance=tree.ray_cast(Vector((center,middle,z))+radial*0.6,-radial,0.6)
                return None if hit is None else 0.6-distance
            fitted_objects=[top]+[o for o in bpy.data.objects if o.get('castGarmentSource')==top.name]
            for ob in fitted_objects:
                evaluated=ob.evaluated_get(deps);fitted=bpy.data.meshes.new_from_object(evaluated,depsgraph=deps)
                inverse=ob.matrix_world.inverted();adjusted=0;largest=0
                for v in fitted.vertices:
                    point=ob.matrix_world@v.co
                    if not hem-0.02<=point.z<=hem+0.30:continue
                    radial=Vector((point.x-center,point.y-middle,0))
                    if radial.length<1e-6:continue
                    reach=radial.length;radial.normalize()
                    surface=outer_reach(top_tree,point.z,radial)
                    # Only the torso shell moves; sleeves and hands near the hip stay put.
                    if surface is None or abs(reach-surface)>0.03:continue
                    # Cloth hangs from its widest contact and eases in above it,
                    # so the let-out is taken from a vertical neighbourhood.
                    delta=0
                    for step in range(-8,7):
                        z=point.z+step*0.01
                        need=outer_reach(pants_tree,z-0.015,radial) or outer_reach(pants_tree,z,radial)
                        here=outer_reach(top_tree,z,radial) or surface
                        if need is None:continue
                        weight=1 if step>=0 else 1+step/9
                        delta=max(delta,(need+0.010-here)*weight)
                    if 0<delta<0.06:
                        point+=radial*delta;v.co=inverse@point;adjusted+=1;largest=max(largest,delta)
                if any(not all(math.isfinite(c) for c in v.co) for v in fitted.vertices):raise RuntimeError('CAST_GARMENT_NONFINITE:'+ob.name)
                fit_report.append({'object':ob.name,'vertexCount':len(fitted.vertices),'adjustedVertices':adjusted,'finite':True,'maximumLetOutMetres':round(largest,4),'preservedWorldAxes':['Z']})
                fitted.update()
                display=bpy.data.objects.new(ob.name+'.preview-fit',fitted);display.matrix_world=ob.matrix_world.copy()
                for collection in ob.users_collection:collection.objects.link(display)
                display.pass_index=ob.pass_index
                display['castFitSource']=ob.name
                if 'castFitOriginalHideRender' not in ob:ob['castFitOriginalHideRender']=ob.hide_render
                ob.hide_render=True
                print('POSED_TOP_LET_OUT',ob.name,adjusted,'vertices; max',round(largest,4),flush=True)
    return fit_report

fit_report=fit_posed_clothing(bpy.context.scene)

