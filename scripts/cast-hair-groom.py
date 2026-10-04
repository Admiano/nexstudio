"""Deterministic, rig-bound fibre grooms over the approved hair silhouettes.

Native Cycles hair curves carry tapered radii and a Huang fibre BSDF. A hidden
point mesh inherits the source hair's bone weights; geometry nodes read its
posed positions, so the groom follows the existing action without handlers.
"""
import bpy, math, random, bisect, os, time, hashlib
from array import array
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

PROFILE='fibre-groom-v16-ear-contour'
MODULE_SHA256=hashlib.sha256(open(__file__,'rb').read()).hexdigest()
STYLE_NAMES={'culturalibre':'long','with_bangs':'bangs','blunt_bob':'bob','bun_brown':'bun','french_braid':'braid','afro01':'afro','short01':'crop','maxwell':'quiff','braided_rows':'braids','grump':'swept'}

def linear_hex(value):
    v=value.lstrip('#');rgb=[int(v[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb)

def restore_source_uv(source):
    """Recover corner UVs discarded by the original OBJ assembler.

    Vertex-ID lookup also handles the few caps appended by holes_fill. Those
    caps get zero UVs and retain the analytic guide field.
    """
    root=__import__('pathlib').Path(__file__).resolve().parents[1]/'engine_sources/makehuman-lineart/assets'
    key=source.name.removeprefix('Host.hair_').split('.')[0]
    folder=next(iter(root.glob('*/hair/'+key)),None)
    if folder is None:return 0
    obj=next(iter(folder.glob('*.obj')),None)
    if obj is None:return 0
    uv=[];faces={}
    for line in obj.read_text().splitlines():
        a=line.split()
        if not a:continue
        if a[0]=='vt':uv.append(tuple(float(x) for x in a[1:3]))
        if a[0]=='f':
            corners=[x.split('/') for x in a[1:]]
            if not all(len(c)>1 and c[1] for c in corners):continue
            ids=[int(c[0])-1 for c in corners]
            faces[tuple(sorted(ids))]={i:uv[int(c[1])-1] for i,c in zip(ids,corners)}
    layer=source.data.uv_layers.get('Cast original hair UV') or source.data.uv_layers.new(name='Cast original hair UV')
    count=0
    for poly in source.data.polygons:
        mapping=faces.get(tuple(sorted(poly.vertices)))
        if not mapping:continue
        for li in poly.loop_indices:layer.data[li].uv=mapping[source.data.loops[li].vertex_index]
        count+=1
    source.data.update();return count


def uv_guide(triangle,points,mesh,style,normal,center):
    if not mesh.uv_layers:return None
    uv=[Vector(mesh.uv_layers.active.data[i].uv) for i in triangle.loops]
    a,b,c=[points[i] for i in triangle.vertices];x=uv[1]-uv[0];y=uv[2]-uv[0]
    det=x.x*y.y-y.x*x.y
    if abs(det)<1e-10:return None
    du=((b-a)*y.y-(c-a)*x.y)/det;dv=((c-a)*x.x-(b-a)*y.x)/det
    reference=flow((a+b+c)/3,normal,style,center)
    if style in ('bob','bangs','swept'):direction=dv
    elif style in ('braid','braids'):
        # Source braid islands unwrap the woven bundles. Follow their length
        # coordinate, which follows the crossings instead of slicing them.
        direction=du if abs(du.normalized().dot(reference))>abs(dv.normalized().dot(reference)) else dv
    else:return None
    if direction.length<1e-7:return None
    direction.normalize()
    return direction if direction.dot(reference)>=0 else -direction

def flow(p,n,style,center):
    q=p-center
    if style in ('quiff','swept','crop'):
        # Swept ridges lift from the front, follow the crown and settle behind.
        d=Vector((.45 if style=='quiff' else -.6, 1.0, -.20))
        if q.z<-.045:d=Vector((q.x*.4,q.y*.3,-1))
    elif style=='bun':
        # Draw the scalp sections toward the rear bun, rather than downward.
        d=Vector((-.35*q.x, .9, .18 if q.z<.02 else -.12))
        if q.y>.13:
            axis=Vector((0,1,0));d=axis.cross(q-Vector((0,.16,.035)))
    elif style in ('braid','braids'):
        d=Vector((q.x*.7,1.0,-.5)) if q.z>-.02 else Vector((0,.2,-1))
    else:
        d=Vector((q.x*2.0,q.y*.9,-.26))
        if q.z<-.08:d=Vector((.13*math.sin(q.z*28),0,-1))
    d-=n*d.dot(n)
    if d.length<1e-5:d=n.cross(Vector((0,1,0)))
    if d.length<1e-5:d=Vector((1,0,0))
    return d.normalized()

def dye_amount(point,center):
    value=max(0,min(1,(center.z-.045-point.z)/.13))
    return value*value*(3-2*value)


def set_hair_colour(scene,colour,dye_hex=''):
    """Palette changes share one groom and never regenerate random fibres."""
    rgb=linear_hex(colour);dye=linear_hex(dye_hex) if dye_hex else None
    for mat in bpy.data.materials:
        if not mat.use_nodes:continue
        t=mat.node_tree;grade=t.nodes.get('Root to tip pigment');core=t.nodes.get('Core pigment');tip=t.nodes.get('Predetermined tip dye');enable=t.nodes.get('Enable tip dye')
        if grade:
            grade.inputs[1].default_value=(*[x*.70 for x in rgb],1);grade.inputs[2].default_value=(*[min(1,x*1.08) for x in rgb],1)
            tip.inputs[2].default_value=(*(dye or rgb),1)
        if core:
            core.inputs[1].default_value=(*[x*.55 for x in rgb],1);core.inputs[2].default_value=(*[x*.55 for x in (dye or rgb)],1)
        if enable:enable.inputs[1].default_value=1 if dye else 0
    return {'baseHex':colour,'tipDyeHex':dye_hex,'baseLinear':list(rgb)}

def hair_material(rgb,dye=None):
    mat=bpy.data.materials.new('Cast V11 physical fibres');mat.use_nodes=True
    t=mat.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial')
    h=t.nodes.new('ShaderNodeBsdfHairPrincipled');h.name='Huang fibre scattering';h.model='HUANG';h.parametrization='COLOR'
    h.inputs['Roughness'].default_value=.43;h.inputs['Aspect Ratio'].default_value=.85
    if h.inputs.get('Random Color'):h.inputs['Random Color'].default_value=.13
    if h.inputs.get('Random Roughness'):h.inputs['Random Roughness'].default_value=.14
    h.inputs['IOR'].default_value=1.55
    for name,value in [('Reflection',.65),('Secondary Reflection',.8),('Transmission',.8)]:
        next(i for i in h.inputs if i.name==name).default_value=value
    info=t.nodes.new('ShaderNodeHairInfo');info.name='Individual fibre variation'
    t.links.new(info.outputs['Random'],h.inputs['Random'])
    grade=t.nodes.new('ShaderNodeMixRGB');grade.name='Root to tip pigment';grade.blend_type='MIX'
    grade.inputs[1].default_value=(*[x*.70 for x in rgb],1);grade.inputs[2].default_value=(*tuple(min(1,x*1.08) for x in rgb),1)
    t.links.new(info.outputs['Intercept'],grade.inputs[0])
    variance=t.nodes.new('ShaderNodeMapRange');variance.name='Fibre pigment variation';variance.inputs['To Min'].default_value=.65;variance.inputs['To Max'].default_value=1.35;t.links.new(info.outputs['Random'],variance.inputs['Value'])
    varied=t.nodes.new('ShaderNodeMixRGB');varied.blend_type='MULTIPLY';varied.inputs[0].default_value=1;t.links.new(grade.outputs[0],varied.inputs[1]);t.links.new(variance.outputs[0],varied.inputs[2])
    pigment=t.nodes.new('ShaderNodeAttribute');pigment.attribute_name='cast_groom_dye'
    enable=t.nodes.new('ShaderNodeMath');enable.name='Enable tip dye';enable.operation='MULTIPLY';enable.inputs[1].default_value=1 if dye else 0;t.links.new(pigment.outputs['Fac'],enable.inputs[0])
    mix=t.nodes.new('ShaderNodeMixRGB');mix.name='Predetermined tip dye';mix.inputs[2].default_value=(*(dye or rgb),1);t.links.new(enable.outputs[0],mix.inputs[0]);t.links.new(varied.outputs[0],mix.inputs[1]);t.links.new(mix.outputs[0],h.inputs['Color'])
    t.links.new(h.outputs[0],out.inputs['Surface']);mat['castGroomProfile']=PROFILE
    return mat

def core_material(rgb,style,dye=None):
    mat=bpy.data.materials.new('Cast V11 lock interior');mat.use_nodes=True
    t=mat.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial');b=t.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value=(*[x*.55 for x in rgb],1);
    pigment=t.nodes.new('ShaderNodeAttribute');pigment.attribute_name='cast_groom_dye'
    enable=t.nodes.new('ShaderNodeMath');enable.name='Enable tip dye';enable.operation='MULTIPLY';enable.inputs[1].default_value=1 if dye else 0;t.links.new(pigment.outputs['Fac'],enable.inputs[0])
    grade=t.nodes.new('ShaderNodeMixRGB');grade.name='Core pigment';grade.inputs[1].default_value=(*[x*.55 for x in rgb],1);grade.inputs[2].default_value=(*[x*.55 for x in (dye or rgb)],1);t.links.new(enable.outputs[0],grade.inputs[0]);t.links.new(grade.outputs[0],b.inputs['Base Color']);b.inputs['Roughness'].default_value=.84 if style=='afro' else .65
    b.inputs['Anisotropic'].default_value=.65;b.inputs['Specular IOR Level'].default_value=.2
    a=t.nodes.new('ShaderNodeAttribute');a.attribute_name='cast_groom_tangent';t.links.new(a.outputs['Vector'],b.inputs['Tangent'])
    edge=t.nodes.new('ShaderNodeAttribute');edge.attribute_name='cast_groom_edge'
    fade=t.nodes.new('ShaderNodeMath');fade.operation='MULTIPLY';fade.use_clamp=True;fade.inputs[1].default_value=400;t.links.new(edge.outputs['Fac'],fade.inputs[0])
    tr=t.nodes.new('ShaderNodeBsdfTransparent');mix=t.nodes.new('ShaderNodeMixShader');t.links.new(fade.outputs[0],mix.inputs[0]);t.links.new(tr.outputs[0],mix.inputs[1]);t.links.new(b.outputs[0],mix.inputs[2]);t.links.new(mix.outputs[0],out.inputs[0]);return mat

def bind_curves(scene,source,paths,radii,material,center):
    """Pointwise source weights, stored in a mesh usable by the existing rig."""
    vertices=[p for path in paths for p in path]
    inv=source.matrix_world.inverted();local=[inv@p for p in vertices]
    mesh=bpy.data.meshes.new('Cast groom deformation points');mesh.from_pydata(local,[],[]);mesh.update()
    helper=bpy.data.objects.new('Cast groom rig binding',mesh);scene.collection.objects.link(helper)
    helper.parent=source.parent;helper.matrix_world=source.matrix_world.copy();helper.hide_render=True;helper.display_type='WIRE'
    helper['castGroomBinding']=True;helper['sourceHair']=source.name
    kd=KDTree(len(source.data.vertices))
    for v in source.data.vertices:kd.insert(source.matrix_world@v.co,v.index)
    kd.balance()
    names={g.index:g.name for g in source.vertex_groups if g.name in source.parent.data.bones}
    groups={name:helper.vertex_groups.new(name=name) for name in names.values()}
    bins={name:{} for name in groups}
    for i,p in enumerate(vertices):
        _,j,_=kd.find(p);weights={names[g.group]:g.weight for g in source.data.vertices[j].groups if g.group in names}
        total=sum(weights.values())
        if total<1e-6:weights={'head':1};total=1
        for name,w in weights.items():
            weight=round(w/total,3);bins[name].setdefault(weight,[]).append(i)
    for name,values in bins.items():
        for w,indices in values.items():groups[name].add(indices,w,'REPLACE')
    arm=helper.modifiers.new('Original presenter skeleton','ARMATURE');arm.object=source.parent
    if any(k in source.name for k in ('culturalibre','blunt_bob')):
        clear=helper.modifiers.new('Follow posed hair sheet clearance','SHRINKWRAP');clear.target=source;clear.wrap_method='NEAREST_SURFACEPOINT';clear.wrap_mode='OUTSIDE';clear.offset=.0004
    cu=bpy.data.hair_curves.new('Cast groom fibres');cu.add_curves([len(p) for p in paths])
    cu.position_data.foreach_set('vector',array('f',(x for p in local for x in p)))
    rad=cu.attributes.new('radius','FLOAT','POINT');rad.data.foreach_set('value',array('f',radii))
    pigment=cu.attributes.new('cast_groom_dye','FLOAT','POINT');pigment.data.foreach_set('value',array('f',(dye_amount(p,center) for p in vertices)))
    cu.materials.append(material)
    obj=bpy.data.objects.new('Cast V11 '+source.name+' fibres',cu);scene.collection.objects.link(obj)
    obj.parent=source.parent;obj.matrix_world=source.matrix_world.copy();obj['castGroomProfile']=PROFILE;obj['sourceHair']=source.name
    ng=bpy.data.node_groups.new('Cast source-weighted groom deformation','GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=ng.nodes;links=ng.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput')
    oi=nodes.new('GeometryNodeObjectInfo');oi.transform_space='RELATIVE';oi.inputs['Object'].default_value=helper
    pos=nodes.new('GeometryNodeInputPosition');idx=nodes.new('GeometryNodeInputIndex');sample=nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT'
    links.new(oi.outputs['Geometry'],sample.inputs['Geometry']);links.new(pos.outputs[0],sample.inputs['Value']);links.new(idx.outputs[0],sample.inputs['Index'])
    setpos=nodes.new('GeometryNodeSetPosition');links.new(inp.outputs[0],setpos.inputs['Geometry']);links.new(sample.outputs[0],setpos.inputs['Position']);links.new(setpos.outputs[0],out.inputs[0])
    mod=obj.modifiers.new('Follow source head, neck and shoulders','NODES');mod.node_group=ng
    return obj,helper

def studio_lights(scene,center):
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.06
    for ob in scene.objects:
        if ob.type=='LIGHT' and not ob.get('castGroomLight'):ob.data.energy*=.22
    for name,offset,power,size in [('key',(-.55,-.75,.55),8.4,.75),('fill',(.65,-.4,.15),2.6,.8),('rim',(.25,.5,.5),7.0,.55)]:
        data=bpy.data.lights.new('Cast fibre '+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new('Cast fibre '+name,data);scene.collection.objects.link(ob);ob.location=center+Vector(offset)
        ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler();ob['castGroomLight']=True

def feather_core_ends(source,center):
    usage={}
    for poly in source.data.polygons:
        for edge in poly.edge_keys:usage[edge]=usage.get(edge,0)+1
    indices={i for edge,count in usage.items() if count==1 for i in edge if (source.matrix_world@source.data.vertices[i].co).z<center.z-.05}
    attr=source.data.attributes.get('cast_groom_edge') or source.data.attributes.new('cast_groom_edge','FLOAT','POINT')
    if not indices:
        for item in attr.data:item.value=.01
        return
    kd=KDTree(len(indices))
    for j,i in enumerate(indices):kd.insert(source.matrix_world@source.data.vertices[i].co,j)
    kd.balance()
    for v,item in zip(source.data.vertices,attr.data):
        p=source.matrix_world@v.co;distance=kd.find(p)[2]
        item.value=distance if p.z<center.z-.04 else .01

def hair_denoising(scene):
    """Denoise physical fibre scattering only; retain the skin's pore treatment."""
    scene.cycles.use_denoising=False;scene.cycles.samples=max(scene.cycles.samples,128)
    scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.01
    scene.cycles.sample_clamp_indirect=2;scene.cycles.sample_clamp_direct=5
    scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=3;scene.cycles.transmission_bounces=4
    layer=scene.view_layers[0];layer.use_pass_object_index=True;layer.cycles.denoising_store_passes=True
    t=scene.compositing_node_group
    if t is None:return
    r=next((n for n in t.nodes if n.type=='R_LAYERS'),None)
    if r is None:return
    original_links=list(r.outputs['Image'].links)
    den=t.nodes.new('CompositorNodeDenoise');den.name='Cast physical hair denoising';den.inputs['Prefilter'].default_value='Accurate'
    t.links.new(r.outputs['Image'],den.inputs['Image']);t.links.new(r.outputs['Denoising Normal'],den.inputs['Normal']);t.links.new(r.outputs['Denoising Albedo'],den.inputs['Albedo'])
    mask=t.nodes.new('CompositorNodeIDMask');mask.inputs['Index'].default_value=11;mask.inputs['Anti-Alias'].default_value=True;t.links.new(r.outputs['Object Index'],mask.inputs['ID value'])
    mix=t.nodes.new('ShaderNodeMix');mix.data_type='RGBA';mix.name='Retain unfiltered skin and illustrated face'
    t.links.new(mask.outputs[0],mix.inputs[0]);t.links.new(r.outputs['Image'],mix.inputs[6]);t.links.new(den.outputs['Image'],mix.inputs[7])
    for link in original_links:t.links.new(mix.outputs[2],link.to_socket)

def soften_ink(scene,style):
    for layer in scene.view_layers:
        for lines in layer.freestyle_settings.linesets:
            if lines.name in ('HAIR_STRANDS','HAIR_LOCKS'):lines.show_render=False
            if lines.name=='HAIR_OUTER':lines.linestyle.thickness*=.4
    for ob in scene.objects:
        if ob.name.startswith(('Host.ink_hair_lock_','Host.hp_')):ob.hide_render=True
    # Replace only the contiguous thick forehead/temple hairline ribbon.
    # Mouth and eye drawing live in the same mesh and retain their materials.
    ob=bpy.data.objects.get('Host.V59_face_frame')
    if ob and not ob.hide_render:
        mat=bpy.data.materials.new('Cast groom hairline feather');mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial');tr=t.nodes.new('ShaderNodeBsdfTransparent');t.links.new(tr.outputs[0],out.inputs[0])
        slot=len(ob.data.materials);ob.data.materials.append(mat)
        me=ob.data;adj={p.index:set() for p in me.polygons};vf={}
        for p in me.polygons:
            for i in p.vertices:vf.setdefault(i,[]).append(p.index)
        for polygons in vf.values():
            for i in polygons:adj[i].update(polygons)
        seen=set()
        for i in adj:
            if i in seen:continue
            queue=[i];seen.add(i);component=[]
            while queue:
                j=queue.pop();component.append(j)
                for k in adj[j]-seen:seen.add(k);queue.append(k)
            ids={v for j in component for v in me.polygons[j].vertices};pts=[me.vertices[i].co for i in ids]
            if len(component)>60 and max(p.z for p in pts)>1.54 and min(p.y for p in pts)<-.075:
                for j in range(min(component),min(len(me.polygons),max(component)+13)):me.polygons[j].material_index=slot

def refine_ear_clearance(source,body,style):
    """Keep ear clearance local; preserve tied and short source silhouettes."""
    if style not in ('long','bob','bangs'):return {'applied':False,'style':style}
    ears=body.vertex_groups.get('ears')
    ep=[v.co.copy() for v in body.data.vertices if ears and any(g.group==ears.index and g.weight>.5 for g in v.groups)]
    if not ep:return {'applied':False}
    changes=0;maximum=0.0
    if source.data.shape_keys:
        basis=source.data.shape_keys.key_blocks[0];tuck=source.data.shape_keys.key_blocks.get('V60_tuck')
        if tuck:
            for a,b in zip(basis.data,tuck.data):
                # The old tuck pushes X outward in direct proportion to Y.
                # Retain the sweep behind the ear while removing this wing.
                delta=b.co-a.co
                if abs(delta.x)>1e-7:
                    maximum=max(maximum,abs(delta.x));weight=min(1,abs(delta.y)/.055)
                    ear_z=sum(e.z for e in ep)/len(ep)
                    taper=max(0,min(1,(ear_z+.035-a.co.z)/.035));taper=taper*taper*(3-2*taper)
                    weight*=taper
                    b.co.x=a.co.x-math.copysign(.025*weight,a.co.x)
                    b.co.y=a.co.y+min(.045,max(0,delta.y))*taper;changes+=1
    for mod in source.modifiers:
        if mod.type!='SHRINKWRAP' or not mod.target or mod.target.name!=body.name:continue
        # The scalp wrap used to project the whole sheet onto the ear ridge.
        # Fade that wrap around each ear, with its original weight elsewhere.
        old=source.vertex_groups.get(mod.vertex_group) if mod.vertex_group else None
        oldweights={v.index:next((g.weight for g in v.groups if old and g.group==old.index),0) for v in source.data.vertices} if old else None
        group=source.vertex_groups.get('Cast V16 '+mod.name) or source.vertex_groups.new(name='Cast V16 '+mod.name)
        for v in source.data.vertices:
            closest=min(ep,key=lambda e:(e-v.co).length_squared)
            dx=abs(v.co.x-closest.x);dy=abs(v.co.y-closest.y);dz=abs(v.co.z-closest.z)
            def fade(t):
                t=max(0,min(1,t));return t*t*(3-2*t)
            release=(1-fade(dx/.045))*(1-fade(dy/.070))*(1-fade(dz/.050))
            weight=(oldweights[v.index] if oldweights is not None else 1)*(1-release)
            group.add([v.index],weight,'REPLACE')
        mod.vertex_group=group.name
    source.data.update()
    return {'applied':True,'style':style,'outwardTuckVertices':changes,'maxOutwardCorrectionMetres':maximum,'scope':'loose hair only'}

def apply_hair_groom(scene,character,style=None,colour=None,density=1.0):
    started=time.monotonic();previous=scene.frame_current
    existing=next((o for o in scene.objects if o.get('castGroomProfile')==PROFILE),None)
    colour=colour or os.environ.get('HCOL') or ('9A4A2E' if character=='female' else '5A3A24')
    if existing:
        palette=set_hair_colour(scene,colour,os.environ.get('HDYE',''));return {'enabled':True,'profile':PROFILE,'reused':True,'object':existing.name,'palette':palette}
    if style=='bald':return {'enabled':True,'profile':PROFILE,'style':'bald','fibres':0}
    source=next((o for o in scene.objects if o.type=='MESH' and not o.hide_render and o.name.startswith('Host.hair_') and any(m and m.name=='LINEART_HAIR_PAPER' for m in o.data.materials)),None)
    if source is None:return {'enabled':True,'profile':PROFILE,'style':'bald','fibres':0}
    style=style or next((v for k,v in STYLE_NAMES.items() if k in source.name),'long')
    for modifier in source.modifiers:
        if modifier.type=='SUBSURF' and len(source.data.vertices)<7000:
            modifier.levels=max(modifier.levels,2);modifier.render_levels=max(modifier.render_levels,2)
    if style=='bun':
        body=bpy.data.objects['Host.body'];ears=body.vertex_groups.get('ears')
        ear_points=[body.matrix_world@v.co for v in body.data.vertices if ears and any(g.group==ears.index and g.weight>.5 for g in v.groups)]
        if ear_points:
            floor=min(p.z for p in ear_points)-.012
            group=source.vertex_groups.get('Cast clean bun nape') or source.vertex_groups.new(name='Cast clean bun nape')
            keep=[v.index for v in source.data.vertices if (source.matrix_world@v.co).z>=floor]
            group.remove(list(range(len(source.data.vertices))));group.add(keep,1,'REPLACE')
            mask=source.modifiers.get('Cast clean bun nape') or source.modifiers.new('Cast clean bun nape','MASK');mask.vertex_group=group.name
            with bpy.context.temp_override(object=source,active_object=source):bpy.ops.object.modifier_move_to_index(modifier=mask.name,index=0)
            print('BUN_NAPE_MASK',floor,len(source.data.vertices)-len(keep),flush=True)
    tuck_report=None
    if style=='long' and source.data.shape_keys and source.data.shape_keys.key_blocks.get('V60_tuck'):
        body=bpy.data.objects['Host.body'];ear_group=body.vertex_groups['ears'].index
        ear_points=[v.co for v in body.data.vertices if v.co.x>0 and any(g.group==ear_group and g.weight>.5 for g in v.groups)]
        ear_z=sum(p.z for p in ear_points)/len(ear_points)
        basis=source.data.shape_keys.key_blocks['Basis'];tuck=source.data.shape_keys.key_blocks['V60_tuck'];changed=0
        for base,target in zip(basis.data,tuck.data):
            t=max(0,min(1,(base.co.z-(ear_z-.055))/.055));weight=t*t*(3-2*t)
            if weight<1 and (target.co-base.co).length>1e-7:
                target.co=base.co+(target.co-base.co)*weight;changed+=1
        source.data.update();tuck_report={'lowerHairReleasedVertices':changed,'earZoneRestZ':ear_z,'fadeBelowEarMetres':.055}
    contour_report=refine_ear_clearance(source,bpy.data.objects['Host.body'],style)
    collision_targets=[]
    if style in ('bob','bangs','quiff','swept','crop','braids','afro','bun'):
        for m in list(source.modifiers):
            if m.type=='SHRINKWRAP' and m.target and (m.target.name!='Host.body' or (character=='male' and m.name.startswith('V26_clear_body'))):
                collision_targets.append([m.target.name,'not needed above shoulders']);source.modifiers.remove(m)
    if style=='long':
        garment=bpy.data.objects.get(os.environ.get('DOBJ','')) or next((o for o in scene.objects if not o.hide_render and any(m.name=='Cast garment edge thickness' for m in o.modifiers)),None)
        if garment:
            for m in source.modifiers:
                if m.type=='SHRINKWRAP' and m.target and m.target.name!='Host.body':
                    collision_targets.append([m.target.name,garment.name]);m.target=garment
    if style=='afro':
        texture=bpy.data.textures.new('Cast afro curl clumps','CLOUDS');texture.noise_scale=.012;texture.noise_depth=1
        displacement=source.modifiers.new('Natural curl-clump silhouette','DISPLACE');displacement.texture=texture;displacement.strength=.0035;displacement.mid_level=.5
        with bpy.context.temp_override(object=source,active_object=source):bpy.ops.object.modifier_move_to_index(modifier=displacement.name,index=0)
    uv_faces=restore_source_uv(source)
    scene.frame_set(1);rig=source.parent;old_pose=rig.data.pose_position;rig.data.pose_position='REST';bpy.context.view_layer.update()
    ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    pts=[ev.matrix_world@v.co for v in me.vertices];tri=[tuple(t.vertices) for t in me.loop_triangles]
    tree=BVHTree.FromPolygons(pts,tri,all_triangles=True)
    center=Vector((sum(p.x for p in pts)/len(pts),.018,max(p.z for p in pts)-.105))
    normals=[t.normal.copy() for t in me.loop_triangles];matrix=ev.matrix_world.to_3x3().inverted().transposed()
    normals=[(matrix@n).normalized() for n in normals]
    uv_fields=[uv_guide(t,pts,me,style,n,center) for t,n in zip(me.loop_triangles,normals)]
    nape=None
    if style in ('afro','bun'):
        body=bpy.data.objects['Host.body'];ears=body.vertex_groups['ears'].index;be=body.evaluated_get(bpy.context.evaluated_depsgraph_get());bm=be.to_mesh()
        ep=[be.matrix_world@v.co for v in bm.vertices if any(g.group==ears and g.weight>.5 for g in v.groups)]
        nape=min(p.z for p in ep)+(.01 if style=='afro' else -.012) if ep else center.z-.075;be.to_mesh_clear()
    areas=[];valid=[];area=0
    for i,(a,b,c) in enumerate(tri):
        p=(pts[a]+pts[b]+pts[c])/3;normal=normals[i]
        outward=p-center
        if normal.dot(outward)<-.015 or (style in ('afro','bun') and p.z<nape):continue
        size=(pts[b]-pts[a]).cross(pts[c]-pts[a]).length*.5
        if size<1e-12:continue
        area+=size;areas.append(area);valid.append(i)
    rng=random.Random(113+sum(ord(c) for c in style));count=int((42000 if style=='afro' else 26000 if character=='female' else 18000)*density)
    paths=[];radii=[];hem_z=min(p.z for p in pts)
    def trace(p,n,sign,steps,step):
        path=[];last=None;index=tree.find_nearest(p)[2]
        for j in range(steps):
            tangent=(uv_fields[index] or flow(p,n,style,center))*sign
            if last is not None and tangent.dot(last)<0:tangent=-tangent
            hit,nn,index,dist=tree.find_nearest(p+tangent*step)
            if hit is None or dist>step*.7 or nn.dot(n)<-.2 or (hit-p).length<step*.3:break
            p=hit;n=nn;last=tangent
            path.append((p.copy(),n.copy()))
        return path
    for k in range(count):
        index=valid[bisect.bisect_left(areas,rng.random()*area)];a,b,c=tri[index]
        u=math.sqrt(rng.random());v=rng.random();p=pts[a]*(1-u)+pts[b]*u*(1-v)+pts[c]*u*v;n=normals[index]
        if style=='afro':
            tangent=n.cross(Vector((0,0,1)))
            if tangent.length<.01:tangent=n.cross(Vector((0,1,0)))
            tangent.normalize();side=n.cross(tangent);radius=rng.uniform(.001,.003);turns=rng.uniform(2.2,3.7);height=rng.uniform(.003,.008)
            path=[]
            for j in range(36):
                t=j/35;phase=t*math.tau*turns;path.append(p+n*(.00025+t*height)+radius*(tangent*math.cos(phase)+side*math.sin(phase)))
        else:
            primary=k%7==0
            length=(.65 if primary else .15) if character=='female' else (.16 if primary else .07);step=.0025
            steps=int(length/step/2);before=trace(p,n,-1,steps,step);after=trace(p,n,1,steps,step)
            samples=list(reversed(before))+[(p,n)]+after
            if len(samples)<5:continue
            if style not in ('bob','bangs') and after and len(after)<steps and samples[-1][0].z<center.z-.08:
                q,nn=samples[-1];d=flow(q,nn,style,center);length=rng.uniform(.001,.005)
                samples.extend([(q+d*length*f,nn) for f in (.35,.70,1)])
            # Low-frequency grouping and small fibre irregularity break sheet highlights.
            phase=rng.random()*math.tau;lift=rng.uniform(.00015,.00065);path=[]
            for j,(q,nn) in enumerate(samples):
                t=j/max(1,len(samples)-1);tangent=flow(q,nn,style,center);side=nn.cross(tangent)
                wav=.00012*math.sin(t*math.tau*1.2+phase)
                extra=(.00065*math.sin(t*math.pi)**2 if k%67==0 else 0)
                path.append(q+nn*(lift+extra)+side*wav)
        if style in ('bob','bangs','long') and any(q.z<hem_z-.002 for q in path):continue
        if style=='bun' and any(q.z<nape-.002 for q in path):continue
        paths.append(path)
        radius=rng.uniform(.000090,.000135) if k%7==0 else rng.uniform(.000030,.000052)
        for j in range(len(path)):
            t=j/max(1,len(path)-1);radii.append(radius*min(1,.20+6*t,.08+6*(1-t)))
    ev.to_mesh_clear()
    rgb=linear_hex(colour)
    dye=linear_hex(os.environ['HDYE']) if os.environ.get('HDYE') else None
    material=hair_material(rgb,dye);obj,helper=bind_curves(scene,source,paths,radii,material,center)
    tangent=source.data.attributes.get('cast_groom_tangent') or source.data.attributes.new('cast_groom_tangent','FLOAT_VECTOR','POINT')
    inv=source.matrix_world.inverted().to_3x3()
    for v,item in zip(source.data.vertices,tangent.data):
        p=source.matrix_world@v.co;n=(source.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();item.vector=inv@flow(p,n,style,center)
    pigment=source.data.attributes.get('cast_groom_dye') or source.data.attributes.new('cast_groom_dye','FLOAT','POINT')
    for v,item in zip(source.data.vertices,pigment.data):item.value=dye_amount(source.matrix_world@v.co,center)
    feather_core_ends(source,center)
    if style=='afro':
        for v,item in zip(source.data.vertices,source.data.attributes['cast_groom_edge'].data):
            p=source.matrix_world@v.co;item.value=min(item.value,max(0,p.z-nape))
    source.data.materials.clear();source.data.materials.append(core_material(rgb,style,dye));source['castGroomCore']=True;source.pass_index=11;obj.pass_index=11
    soften_ink(scene,style);studio_lights(scene,center);hair_denoising(scene)
    rig.data.pose_position=old_pose;scene.frame_set(previous);bpy.context.view_layer.update()
    report={'enabled':True,'profile':PROFILE,'style':style,'sourceHair':source.name,'object':obj.name,'binding':helper.name,'fibres':len(paths),'points':len(radii),'radiusMetres':[min(radii),max(radii)],'napeRestZ':nape,'earTuckRefinement':tuck_report,'earContour':contour_report,'collisionTargetsRepaired':collision_targets,'sourceUVFacesRestored':uv_faces,'surfaceArea':area,'colour':colour,'tipDye':os.environ.get('HDYE',''),'physicalShader':'Huang','boneGroups':list(helper.vertex_groups.keys()),'seconds':round(time.monotonic()-started,2),'codeSHA256':MODULE_SHA256}
    obj['castGroomReport']=str(report);print('CAST_HAIR_GROOM',report,flush=True);return report
