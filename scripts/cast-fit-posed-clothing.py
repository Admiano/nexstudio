"""Rebuild posed garment clearance for each requested frame, without accumulation."""
import bpy,os,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def _watch_cuff_stop():
    """Posed forearm axis and the watch's elbow-side edge, if a watch is worn."""
    parts=[o for o in bpy.data.objects if o.name.startswith('Host.watch_') and o.type=='MESH' and not o.hide_render and o.parent_type=='BONE']
    if not parts:return None
    rig=parts[0].parent;side=parts[0].parent_bone.rsplit('.',1)[-1];M=rig.matrix_world;pb=rig.pose.bones
    wrist=(M@pb['wrist.'+side].matrix).translation;axis=(wrist-(M@pb['lowerarm01.'+side].matrix).translation).normalized()
    pts=[o.matrix_world@v.co-wrist for o in parts for v in o.data.vertices]
    top=max(-d.dot(axis) for d in pts);u=axis.orthogonal().normalized();w=axis.cross(u);n=32;rim=[0.0]*n;tops=[None]*n
    for d in pts:
        i=int((math.atan2(d.dot(w),d.dot(u))%(2*math.pi))/(2*math.pi)*n)%n;t=-d.dot(axis)
        tops[i]=t if tops[i] is None else max(tops[i],t)
        if t>top-0.008:rim[i]=max(rim[i],(d+axis*d.dot(axis)).length)
    tops=[top if t is None else t for t in tops];tops=[max(tops[i-1],tops[i],tops[(i+1)%n])+0.002 for i in range(n)]
    edge=top+0.002;body=bpy.data.objects.get('Host.body');skin=[0.0]*n
    if body:
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        bvh=BVHTree.FromPolygons([body.matrix_world@v.co for v in me.vertices],[tuple(f.vertices) for f in me.polygons]);ev.to_mesh_clear()
        centre=wrist-axis*(edge+0.004)
        for i in range(n):
            q=2*math.pi*(i+0.5)/n;dr=u*math.cos(q)+w*math.sin(q);hit=bvh.ray_cast(centre+dr*0.09,-dr,0.09)
            if hit[0] is not None:skin[i]=0.09-hit[3]
    return {'wrist':wrist,'axis':axis,'u':u,'w':w,'n':n,'rim':rim,'skin':skin,'edge':edge,'edges':tops,'ease':0.015,'low':None}

def _stop_cuff_at_watch(ob,mesh,stop):
    # A sleeve can't hang through a watch, and a slanted hem shouldn't leave a
    # gap into the sleeve above it: around the wrist, the cuff's lowest edge is
    # brought to the watch's elbow-side edge and gathered onto the wrist.
    if stop is None:return 0
    wrist,axis,edge,ease=stop['wrist'],stop['axis'],stop['edge'],stop['ease']
    u,w,n,rim=stop['u'],stop['w'],stop['n'],stop['rim']
    hits=[]
    for v in mesh.vertices:
        p=ob.matrix_world@v.co;d=p-wrist;t=-d.dot(axis)
        if not -0.08<t<edge+2*ease:continue
        k=(math.atan2(d.dot(w),d.dot(u))%(2*math.pi))/(2*math.pi)*n;reach=stop['skin'][int(k)%n]+0.035 if stop['skin'][int(k)%n] else 0.06
        if (d+axis*d.dot(axis)).length<reach:hits.append((v,p,t,k))
    if stop['low'] is None:
        low=[None]*n
        for _,_,t,k in hits:
            i=int(k)%n;low[i]=t if low[i] is None else min(low[i],t)
        known=[i for i in range(n) if low[i] is not None]
        if not known:return 0
        for i in range(n):
            if low[i] is None:
                a_=max([j for j in known if j<i] or [known[-1]-n]);b_=min([j for j in known if j>i] or [known[0]+n])
                low[i]=low[a_%n]+(low[b_%n]-low[a_%n])*(i-a_)/(b_-a_)
        stop['low']=[(low[i-1]+2*low[i]+low[(i+1)%n])/4 for i in range(n)]
    low=stop['low'];inverse=ob.matrix_world.inverted();moved=0
    for v,p,t,k in hits:
        i=int(k)%n;f=k-int(k);lo=low[i]*(1-f)+low[(i+1)%n]*f
        edge=stop['edges'][i]*(1-f)+stop['edges'][(i+1)%n]*f;top=edge+ease
        if lo>=top:continue
        tt=edge+(max(t,lo)-lo)/(top-lo)*ease if t<top else t
        q=p-axis*(tt-t);d=q-wrist;r=d+axis*d.dot(axis);rr=r.length;fit=stop['skin'][i]+0.004
        if stop['skin'][i]>0 and rr>fit and tt<top:q-=r*((rr-fit)/rr*(1-(tt-edge)/ease))
        if (q-p).length>1e-6:v.co=inverse@q;moved+=1
    return moved

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
            extension=max(0,hem-waist+0.045)
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
            stop=_watch_cuff_stop()
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
                cuff=_stop_cuff_at_watch(ob,fitted,stop)
                if any(not all(math.isfinite(c) for c in v.co) for v in fitted.vertices):raise RuntimeError('CAST_GARMENT_NONFINITE:'+ob.name)
                fit_report.append({'object':ob.name,'vertexCount':len(fitted.vertices),'adjustedVertices':adjusted,'finite':True,'cuffVerticesStoppedAtWatch':cuff,'maximumLetOutMetres':round(largest,4),'preservedWorldAxes':['Z']})
                fitted.update()
                display=bpy.data.objects.new(ob.name+'.preview-fit',fitted);display.matrix_world=ob.matrix_world.copy()
                for collection in ob.users_collection:collection.objects.link(display)
                display.pass_index=ob.pass_index
                display['castFitSource']=ob.name
                if 'castFitOriginalHideRender' not in ob:ob['castFitOriginalHideRender']=ob.hide_render
                ob.hide_render=True
                print('POSED_TOP_LET_OUT',ob.name,adjusted,'vertices; max',round(largest,4),'cuff stopped',cuff,flush=True)
    else:
        # Seated leg folds push skin through a dress where the hem crosses the
        # inseam. Clearance is enforced on the garment only — the posed body is
        # never touched: every garment surface point is kept `margin` outside
        # the body shell. Derived garments (ink lines, trims) get the same push
        # so decoration stays glued to the cloth.
        body=bpy.data.objects.get('Host.body')
        garment_names={x.split('=')[0] for x in os.environ.get('GARMS','').split(';') if x}
        dresses=[o for o in (bpy.data.objects.get(n) for n in garment_names) if o and 'dress' in o.name.lower()]
        if body is not None and dresses:
            deps=bpy.context.evaluated_depsgraph_get()
            # The skin shell is several meshes (body, lower legs, ear fills):
            # all of them collide with the dress.
            skin=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render
                  and not o.get('castFitSource') and not o.get('castGarmentSource')
                  and o.name.startswith('Host.')
                  and any(m and 'SKIN' in m.name.upper() for m in o.data.materials)]
            points=[];faces=[]
            for ob in skin:
                oe=ob.evaluated_get(deps);om=oe.to_mesh();base=len(points)
                points+=[oe.matrix_world@v.co for v in om.vertices]
                faces+=[[base+i for i in p.vertices] for p in om.polygons]
                oe.to_mesh_clear()
            body_tree=BVHTree.FromPolygons(points,faces)
            margin=0.006
            source_names={d.name for d in dresses}
            dress_tree=None;dress_faces=None;dress_pts=None
            for ob in dresses+[o for o in bpy.data.objects if o.get('castGarmentSource') in source_names]:
                if ob.get('castFitSource') is not None or ob.hide_render:continue
                evaluated=ob.evaluated_get(deps);fitted=bpy.data.meshes.new_from_object(evaluated,depsgraph=deps)
                inverse=ob.matrix_world.inverted()
                pts=[ob.matrix_world@v.co for v in fitted.vertices];adjusted=0
                # Clearance is a skirt problem: only verts around the legs move.
                # Bodice and armhole edges keep their authored fit.
                rig=bpy.data.objects.get('Host.rig')
                hip_z=(rig.matrix_world@rig.pose.bones['upperleg01.L'].head).z if rig else 1e9
                def leg_ok(i):
                    return pts[i].z<hip_z+0.08
                derived=ob.get('castGarmentSource') in source_names
                if derived and dress_tree is not None:
                    # Ink on the cloth rides the fitted surface: snap each
                    # vertex onto it (plus a film) so it can't sink under or
                    # float off the shifted dress.
                    for i,point in enumerate(pts):
                        hit=dress_tree.find_nearest(point)
                        if hit[0] is None or hit[3]>0.03:continue
                        q=hit[0]+hit[1]*0.002
                        if (q-point).length>1e-7:pts[i]=q;adjusted+=1
                else:
                    def push_out(i):
                        if not leg_ok(i):return 0
                        point=pts[i];hit=body_tree.find_nearest(point)
                        # Only near misses count: a vertex far inside or far
                        # off the body is sandwiched or hanging free, not
                        # clipping, and yanking it tears the garment.
                        if hit[0] is None or hit[3]>0.02:return 0
                        surface,normal=hit[0],hit[1]
                        signed=(point-surface).dot(normal)
                        if signed<margin:pts[i]=surface+normal*margin;return 1
                        return 0
                    adjusted=sum(push_out(i) for i in range(len(pts)))
                    # Skin can still show through a face whose samples all pass:
                    # probe the centroid, edge midpoints and the inner ring to
                    # the centroid, shifting the face's verts where any probe
                    # sits on/inside the body.
                    for f in fitted.polygons:
                        vs=[vi for vi in f.vertices if leg_ok(vi)]
                        if not vs:continue
                        allv=list(f.vertices)
                        centre=sum((pts[vi] for vi in allv),Vector((0,0,0)))/len(allv)
                        probes=[centre]
                        for i in range(len(allv)):
                            a,b=pts[allv[i]],pts[allv[(i+1)%len(allv)]]
                            probes+=[(a+b)/2,(a*3+b)/4,(a+b*3)/4]
                        probes+=[(pts[vi]+centre)/2 for vi in allv]
                        for probe in probes:
                            hit=body_tree.find_nearest(probe)
                            if hit[0] is None or hit[3]>0.02:continue
                            surface,normal=hit[0],hit[1]
                            signed=(probe-surface).dot(normal)
                            if signed<margin:
                                delta=normal*min(margin-signed,0.05)
                                for vi in vs:pts[vi]+=delta
                    # Face shifts can drag a neighbour vertex back inside; re-pin.
                    for i in range(len(pts)):push_out(i)
                if not derived:
                    dress_pts=pts;dress_faces=[list(f.vertices) for f in fitted.polygons]
                    dress_tree=BVHTree.FromPolygons(pts,dress_faces)
                for i,v in enumerate(fitted.vertices):v.co=inverse@pts[i]
                if any(not all(math.isfinite(c) for c in v.co) for v in fitted.vertices):raise RuntimeError('CAST_GARMENT_NONFINITE:'+ob.name)
                fitted.update()
                display=bpy.data.objects.new(ob.name+'.preview-fit',fitted);display.matrix_world=ob.matrix_world.copy()
                for collection in ob.users_collection:collection.objects.link(display)
                display.pass_index=ob.pass_index
                display['castFitSource']=ob.name
                if 'castFitOriginalHideRender' not in ob:ob['castFitOriginalHideRender']=ob.hide_render
                ob.hide_render=True
                fit_report.append({'object':ob.name,'vertexCount':len(fitted.vertices),'bodyClearanceVertices':adjusted,'finite':True})
                print('POSED_BODY_CLEARANCE',ob.name,adjusted,flush=True)
    fit_report+=_drop_stretched_strokes()
    return fit_report

def _drop_stretched_strokes(limit=3.0):
    """Ink strokes bound to a garment span the gap when a limb lifts away from the torso; drop faces stretched past `limit`× their rest length."""
    import bmesh
    report=[];deps=bpy.context.evaluated_depsgraph_get()
    for ob in [o for o in bpy.data.objects if o.type=='MESH' and o.get('castGarmentSource') and 'castStrokeTaper' in o]:
        shown=next((o for o in bpy.data.objects if o.get('castFitSource')==ob.name and not o.hide_render),None)
        if shown is None and ob.hide_render:continue
        source=shown or ob
        mesh=bpy.data.meshes.new_from_object(source.evaluated_get(deps),depsgraph=deps) if shown is None else shown.data
        rest=ob.data
        if len(mesh.vertices)!=len(rest.vertices):
            if shown is None:bpy.data.meshes.remove(mesh)
            continue
        bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
        bad=[f for f in bm.faces if any((e.verts[0].co-e.verts[1].co).length>limit*max((rest.vertices[e.verts[0].index].co-rest.vertices[e.verts[1].index].co).length,1e-6) for e in f.edges)]
        if not bad:
            bm.free()
            if shown is None:bpy.data.meshes.remove(mesh)
            continue
        bmesh.ops.delete(bm,geom=bad,context='FACES_ONLY');bm.to_mesh(mesh);bm.free();mesh.update()
        if shown is None:
            shown=bpy.data.objects.new(ob.name+'.preview-fit',mesh);shown.matrix_world=ob.matrix_world.copy()
            for collection in ob.users_collection:collection.objects.link(shown)
            shown.pass_index=ob.pass_index;shown['castFitSource']=ob.name
            if 'castFitOriginalHideRender' not in ob:ob['castFitOriginalHideRender']=ob.hide_render
            ob.hide_render=True
        report.append({'object':ob.name,'droppedStretchedStrokeFaces':len(bad)})
        print('POSED_STROKES_DROPPED',ob.name,len(bad),flush=True)
    return report

fit_report=fit_posed_clothing(bpy.context.scene)

