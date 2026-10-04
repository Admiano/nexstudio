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
            top=tops[0];deps=bpy.context.evaluated_depsgraph_get();ev=top.evaluated_get(deps);mesh=ev.to_mesh()
            points=[ev.matrix_world@v.co for v in mesh.vertices]
            tree=BVHTree.FromPolygons(points,[list(p.vertices) for p in mesh.polygons])
            center=sum(p.x for p in points)/len(points);middle=sum(p.y for p in points)/len(points)
            hem=min(p.z for p in points if abs(p.x-center)<0.12)
            ev.to_mesh_clear()
            pants=[o for o in garments if o and any(k in o.name.lower() for k in ('trouser','jeans','pants'))]
            fitted_objects=pants+[o for o in bpy.data.objects if o.get('castGarmentSource') in {p.name for p in pants}]
            for ob in fitted_objects:
                evaluated=ob.evaluated_get(deps);fitted=bpy.data.meshes.new_from_object(evaluated,depsgraph=deps)
                inverse=ob.matrix_world.inverted();adjusted=0
                for v in fitted.vertices:
                    point=ob.matrix_world@v.co
                    if point.z<=hem+0.006:continue
                    front=point.y<middle;direction=Vector((0,1 if front else -1,0))
                    hit,normal,face,distance=tree.ray_cast(Vector((point.x,-3 if front else 3,point.z)),direction,6)
                    if hit is None or abs(hit.y-point.y)>0.10:continue
                    inside=hit.y+(0.012 if front else -0.012)
                    if (front and point.y<inside) or (not front and point.y>inside):
                        point.y=inside;v.co=inverse@point;adjusted+=1
                if any(not all(math.isfinite(c) for c in v.co) for v in fitted.vertices):raise RuntimeError('CAST_GARMENT_NONFINITE:'+ob.name)
                fit_report.append({'object':ob.name,'vertexCount':len(fitted.vertices),'adjustedVertices':adjusted,'finite':True,'preservedWorldAxes':['X','Z']})
                fitted.update()
                display=bpy.data.objects.new(ob.name+'.preview-fit',fitted);display.matrix_world=ob.matrix_world.copy()
                for collection in ob.users_collection:collection.objects.link(display)
                display.pass_index=ob.pass_index
                display['castFitSource']=ob.name
                if 'castFitOriginalHideRender' not in ob:ob['castFitOriginalHideRender']=ob.hide_render
                ob.hide_render=True
                print('POSED_DEPTH_FIT',ob.name,adjusted,'vertices; x/z preserved',flush=True)
    return fit_report

fit_report=fit_posed_clothing(bpy.context.scene)

