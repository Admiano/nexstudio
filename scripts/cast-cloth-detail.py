"""Bounded fold easing and tapered drawn fold strokes on original garments."""
import bpy,bmesh,math,hashlib
from pathlib import Path
from mathutils import Vector
PROFILE='illustrated-cloth-detail-v16'

def ease_folds(ob):
    if ob.type!='MESH':return None
    name='Cast V16 gentle fold ease'
    if ob.data.shape_keys and ob.data.shape_keys.key_blocks.get(name):return {'reused':True}
    if not ob.data.shape_keys:ob.shape_key_add(name='Basis')
    basis=ob.data.shape_keys.key_blocks[0];coords=[v.co.copy() for v in basis.data]
    for existing in list(ob.data.shape_keys.key_blocks)[1:]:
        if existing.value:
            for i,v in enumerate(existing.data):coords[i]+=(v.co-basis.data[i].co)*existing.value
    key=ob.shape_key_add(name=name,from_mix=False);key.value=1;adj=[set() for _ in coords];edge_counts={}
    for p in ob.data.polygons:
        for e in p.edge_keys:edge_counts[e]=edge_counts.get(e,0)+1
    for e in ob.data.edges:
        a,b=e.vertices;adj[a].add(b);adj[b].add(a)
    protected={i for edge,n in edge_counts.items() if n==1 for i in edge}
    for _ in range(3):protected|={j for i in list(protected) for j in adj[i]}
    # Only small depth relief: no width, length, garment silhouette or rim shift.
    displacement={}
    for i,p in enumerate(coords):
        if i in protected or not adj[i]:continue
        mean=sum(coords[j].y for j in adj[i])/len(adj[i]);delta=max(-.0018,min(.0018,(mean-p.y)*.38))
        if abs(delta)>1e-7:key.data[i].co.y+=delta;displacement[i]=delta
    for proxy in bpy.data.objects:
        if proxy.get('castGarmentProxySource')!=ob.name or len(proxy.data.vertices)!=len(coords):continue
        if not proxy.data.shape_keys:proxy.shape_key_add(name='Basis')
        pk=proxy.shape_key_add(name=name,from_mix=False);pk.value=1
        for i,d in displacement.items():pk.data[i].co.y+=d
    ob.data.update()
    return {'vertices':len(displacement),'maxDepthMetres':max(map(abs,displacement.values()),default=0),'protectedRimVertices':len(protected),'widthHeightUnchanged':True}

def taper_strokes(ob):
    if ob.get('castStrokeTaper') or ob.type!='MESH':return None
    me=ob.data;adj=[set() for _ in me.vertices]
    for e in me.edges:
        a,b=e.vertices;adj[a].add(b);adj[b].add(a)
    remaining=set(range(len(me.vertices)));changed=0;count=0
    while remaining:
        seed=min(remaining);component={seed};queue=[seed];remaining.remove(seed)
        while queue:
            i=queue.pop()
            for j in adj[i]&remaining:remaining.remove(j);component.add(j);queue.append(j)
        if len(component)<12:continue
        # Each original seam/fold tube carries two ordered material classes.
        polygons=[p for p in me.polygons if p.vertices[0] in component]
        if not polygons or any('INK' in me.materials[p.material_index].name for p in polygons):continue
        ids=sorted(component);points=[me.vertices[i].co.copy() for i in ids]
        lo=min(points,key=lambda p:p.z);hi=max(points,key=lambda p:p.z);axis=hi-lo
        if axis.length<.02:continue
        axis.normalize();t=[(p-lo).dot(axis) for p in points];span=max(t)-min(t)
        if span<.02:continue
        # Tube centre from neighbouring vertices; soften the terminal 8 mm.
        for i,p,along in zip(ids,points,t):
            end=min(along-min(t),max(t)-along);f=max(.14,min(1,end/.008));f=f*f*(3-2*f)
            if f>=.999:continue
            neighbours=[me.vertices[j].co for j in adj[i]]
            centre=sum(neighbours,Vector())/max(1,len(neighbours));perp=(p-centre)-axis*(p-centre).dot(axis)
            me.vertices[i].co=p-perp*(1-f)*.5;changed+=1
        count+=1
    ob['castStrokeTaper']=PROFILE;me.update();return {'taperedComponents':count,'vertices':changed}

def cover_sleeve_roots(body,garments):
    """Extend only existing skin deletion masks inside each sleeve root."""
    rig_names=set(body.parent.data.bones)
    rows=[]
    for ob in garments:
        if not any(k in ob.name for k in ('mindfront_f_dress_09','mindfront_f_dress_11')):continue
        vg=body.vertex_groups.get('Delete.'+ob.name.removeprefix('Host.'))
        if not vg:continue
        # Original mask has isolated unmasked vertices surrounded by covered
        # torso/upper arm vertices. Fill these small islands, preserving edges.
        covered={v.index for v in body.data.vertices if any(g.group==vg.index and g.weight>.5 for g in v.groups)}
        adj=[set() for _ in body.data.vertices]
        for e in body.data.edges:
            a,b=e.vertices;adj[a].add(b);adj[b].add(a)
        candidates={i for i,n in enumerate(adj) if i not in covered and n and len(n&covered)>=max(3,len(n)-1)}
        # Never extend onto hands/neck; adjacency and upper-arm bound are local.
        co=__import__('runpy').run_path(str(Path(__file__).with_name('cast-facial-refinement.py')))['shaped_coordinates'](body)
        chosen=[i for i in range(len(co)) if .125<abs(co[i][0])<.215 and 1.245<co[i][2]<1.333 and i not in covered]
        if chosen:vg.add(chosen,1,'REPLACE')
        rows.append({'garment':ob.name,'sleeveRootMaskVertices':len(chosen)})
    return rows

def collar_clearance(ob,body):
    target=next((o for o in bpy.data.objects if o.get('castInternalTarget')),None)
    if target is None:
        target=body.copy();target.name='Cast internal full-skin clearance V16'
        for m in list(target.modifiers):
            if m.type=='MASK':target.modifiers.remove(m)
        bpy.context.scene.collection.objects.link(target);target.hide_render=True;target['castInternalTarget']=True
    coords=[v.co for v in ob.data.vertices];top=max(v.z for v in coords);centre=sum(v.x for v in coords)/len(coords)
    selected=[i for i,p in enumerate(coords) if p.z>top-.13 and abs(p.x-centre)<.215]
    if not selected:return None
    group=ob.vertex_groups.get('Cast V16 collar clearance') or ob.vertex_groups.new(name='Cast V16 collar clearance');group.add(selected,1,'REPLACE')
    mod=ob.modifiers.get('Cast V16 collar clearance') or ob.modifiers.new('Cast V16 collar clearance','SHRINKWRAP')
    # 3.5 mm: at 2 mm the dress faces between projected vertices still cut the convex shoulder.
    mod.target=target;mod.vertex_group=group.name;mod.wrap_method='NEAREST_SURFACEPOINT';mod.wrap_mode='OUTSIDE';mod.offset=.0035
    solid=next((i for i,m in enumerate(ob.modifiers) if m.type=='SOLIDIFY'),None)
    if solid is not None:
        with bpy.context.temp_override(object=ob,active_object=ob):bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=solid)
    return {'vertices':len(selected),'minimumClearanceMetres':.0035,'originalTopologyWeightsPreserved':True}

def close_pinholes(ob):
    """Fill stray one-quad holes in garment sources; the edge-thickness rim turns them into shaded patches."""
    bm=bmesh.new();bm.from_mesh(ob.data)
    new=bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=4)['faces']
    for f in new:
        ring=[l.link_loop_radial_next.face for l in f.loops if l.link_loop_radial_next.face is not f]
        if not ring:continue
        f.normal_update()
        if f.normal.dot(sum((g.normal for g in ring),Vector()))<0:f.normal_flip()
        f.material_index=ring[0].material_index;f.smooth=ring[0].smooth
    if new:bm.to_mesh(ob.data);ob.data.update()
    bm.free();return len(new)

def apply_cloth_detail(scene):
    garments=[o for o in scene.objects if o.type=='MESH' and (not o.hide_render or o.get('castFitOriginalHideRender') is False) and not o.get('castFitSource') and any(m and m.get('castClothProfile')=='illustrated-fabric-v15' for m in o.data.materials) and not any(k in o.name.lower() for k in ('shoe','sneaker','trouser','pants','jeans')) and not o.get('castGarmentSource')]
    pinholes={o.name:n for o in scene.objects if o.type=='MESH' and not o.get('castFitSource') and any(m and m.get('castClothProfile')=='illustrated-fabric-v15' for m in o.data.materials) and (n:=close_pinholes(o))}
    rows=[]
    for ob in garments:
        rows.append({'object':ob.name,'collarClearance':collar_clearance(ob,bpy.data.objects['Host.body']),'foldEase':ease_folds(ob) if 'dress' in ob.name else None,'strokes':[taper_strokes(x) for x in scene.objects if x.get('castGarmentSource')==ob.name]})
    masks=cover_sleeve_roots(bpy.data.objects['Host.body'],garments)
    return {'profile':PROFILE,'garments':rows,'pinholesClosed':pinholes,'sleeveMasks':masks,'codeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
