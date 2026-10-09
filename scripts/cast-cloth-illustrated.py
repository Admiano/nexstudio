"""Illustrated fabric and a covered neckline on the original rigged garments.

Only selected clothing and its seam proxies are modified. Rest cages remain
available in Basis; body, face, skin, hair, lights and original rig are untouched.
"""
import bpy,os,math,hashlib,runpy,bmesh,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
PROFILE='illustrated-fabric-v15'
MODULE_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
DEFAULTS={'mindfront_f_dress_09':'6B2233','mindfront_f_dress_11':'2B3A5C','mindfront_f_dress_07':'7C8C6A','punkduck_black_cocktail_dress':'1F5C4A','punkduck_middle_length_qipao':'B87A7F','namuhekam_male_polo_shirt':'2E3A55','mindfront_male_trousers_1':'3A3A40','toigo_basic_tucked_t-shirt':'EDEBE6','elvs_jeans_straight_leg':'2E3A55','elvs_male_shirt_untucked_bd1':'A9C4DE','mindfront_male_trousers_2':'B59A6E','mindfront_knitted_sweater_01':'6B2E2E','punkduck_male_classic_jeans':'3A4660','toigo_fisherman_sweater':'D8CFBE','toigo_wool_pants':'3A3A40'}
def linear(h):
    c=[int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)
def smooth(v):
    v=max(0,min(1,v));return v*v*(3-2*v)
def colours():
    result=dict(DEFAULTS)
    if os.environ.get('CAST_DRESS') and os.environ.get('CAST_DRESS_HEX'):result[os.environ['CAST_DRESS']]=os.environ['CAST_DRESS_HEX']
    for item in os.environ.get('CAST_GARMENTS','').replace(';',',').split(','):
        if '=' in item:
            name,h=item.split('=',1);result[name.removeprefix('Host.')]=h
    return result

def fabric_for(name):
    if 'shoe' in name:return 'leather'
    if 'sneaker' in name:return 'canvas'
    if any(s in name for s in ('knitted','fisherman')):return 'knit'
    if 'jeans' in name:return 'denim'
    if 'wool' in name:return 'wool'
    if 't-shirt' in name:return 'jersey'
    if 'polo' in name:return 'pique'
    if any(s in name for s in ('qipao','cocktail')):return 'fine satin'
    return 'woven crepe' if 'dress' in name else 'woven cotton'

def cloth_material(mat,h,fabric):
    mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();N=t.nodes;L=t.links
    def node(typ,name):
        n=N.new(typ);n.name=name;return n
    def calc(operation,a,b=None,name='Fabric arithmetic'):
        n=node('ShaderNodeMath',name);n.operation=operation
        for i,v in enumerate([a,b]):
            if v is None:continue
            if isinstance(v,(int,float)):n.inputs[i].default_value=v
            else:L.new(v,n.inputs[i])
        return n.outputs[0]
    base=linear(h);geo=node('ShaderNodeNewGeometry','Drawn fold normals')
    dot=node('ShaderNodeVectorMath','Broad painted fold light');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(-.38,-.82,.43);L.new(geo.outputs['Normal'],dot.inputs[0])
    remap=node('ShaderNodeMapRange','Fold light domain');remap.clamp=True;remap.inputs['From Min'].default_value=-1;remap.inputs['From Max'].default_value=1;L.new(dot.outputs['Value'],remap.inputs[0])
    ramp=node('ShaderNodeValToRGB','Fabric colour planes');ramp.color_ramp.interpolation='EASE'
    factors=[(0,.48),(.30,.61),(.48,.72),(.62,.83),(.78,.94),(1,1.03)]
    for el in list(ramp.color_ramp.elements)[2:]:ramp.color_ramp.elements.remove(el)
    for i,(pos,v) in enumerate(factors):
        e=ramp.color_ramp.elements[i] if i<2 else ramp.color_ramp.elements.new(pos);e.position=pos;e.color=(*[min(1,c*v) for c in base],1)
    L.new(remap.outputs[0],ramp.inputs[0])
    rest=node('ShaderNodeAttribute','Fabric attached coordinates');rest.attribute_name='cast_cloth_rest'
    xyz=node('ShaderNodeSeparateXYZ','Weft and warp');L.new(rest.outputs['Vector'],xyz.inputs[0])
    # Pigment marks follow the fitted resting mesh, with no raised bump or gloss.
    pitch={'knit':.0045,'denim':.0019,'wool':.0023,'jersey':.0015,'pique':.0022,'fine satin':.0012}.get(fabric,.0017)
    across=calc('MULTIPLY',xyz.outputs['X'],2*math.pi/pitch)
    vertical=calc('MULTIPLY',xyz.outputs['Z'],2*math.pi/pitch)
    if fabric=='denim':across=calc('ADD',across,vertical)
    warp=calc('SINE',across);weft=calc('SINE',vertical)
    pattern=calc('MULTIPLY',warp,weft)
    if fabric=='knit':pattern=calc('ADD',calc('MULTIPLY',warp,.75),calc('MULTIPLY',weft,.25))
    amp={'knit':.075,'denim':.055,'wool':.045,'jersey':.025,'pique':.04,'fine satin':.015,'leather':0,'canvas':.025}.get(fabric,.035)
    pigment=calc('ADD',1,calc('MULTIPLY',pattern,amp),'Restrained yarn pigment')
    noise=node('ShaderNodeTexNoise','Fine textile irregularity');noise.inputs['Scale'].default_value=450;noise.inputs['Detail'].default_value=1.4;noise.inputs['Roughness'].default_value=.6;L.new(rest.outputs['Vector'],noise.inputs[0])
    grain=calc('ADD',.982,calc('MULTIPLY',noise.outputs['Fac'],.036));pigment=calc('MULTIPLY',pigment,grain)
    ao=node('ShaderNodeAmbientOcclusion','Small fabric contact shadows');ao.samples=16;ao.inputs['Distance'].default_value=.012
    contact=calc('ADD',.92,calc('MULTIPLY',ao.outputs['AO'],.08));pigment=calc('MULTIPLY',pigment,contact)
    multiply=node('ShaderNodeMixRGB','Drawn fabric finish');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1;L.new(ramp.outputs[0],multiply.inputs[1]);L.new(pigment,multiply.inputs[2])
    emission=node('ShaderNodeEmission','Illustrated fabric');emission.inputs['Strength'].default_value=1;L.new(multiply.outputs[0],emission.inputs[0]);out=node('ShaderNodeOutputMaterial','Fabric output');L.new(emission.outputs[0],out.inputs['Surface'])
    mat['castClothProfile']=PROFILE;mat['castClothBaseHex']=h;mat['castFabric']=fabric

def fit_cloth(ob,body,covered):
    keyname='Cast V15 covered tailored fit' if covered else 'Cast V15 fabric ease'
    if ob.data.shape_keys and ob.data.shape_keys.key_blocks.get(keyname):return {'reused':True,'key':keyname}
    points=[ob.matrix_world@v.co for v in ob.data.vertices];cx=body.matrix_world.translation.x
    body_coords=runpy.run_path(str(Path(__file__).with_name('cast-facial-refinement.py')))['shaped_coordinates'](body)
    bpoints=[body.matrix_world@Vector(p) for p in body_coords]
    skin_group=body.vertex_groups['body'].index
    skin_ids={v.index for v in body.data.vertices if any(g.group==skin_group and g.weight>.5 for g in v.groups)}
    faces=[tuple(p.vertices) for p in body.data.polygons if all(i in skin_ids for i in p.vertices)]
    bvh=BVHTree.FromPolygons(bpoints,faces,all_triangles=False)
    lifted={}
    if covered:
        bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
        rim={v.index for v in bm.verts if any(e.is_boundary for e in v.link_edges) and abs(points[v.index].x-cx)<.165 and points[v.index].y<-.027 and 1.10<points[v.index].z<1.405}
        # Boundary points are ordered by their original connected edge path.
        adj={i:[e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges if e.is_boundary and e.other_vert(bm.verts[i]).index in rim] for i in rim}
        starts=[i for i in rim if len(adj[i])==1];start=min(starts,key=lambda i:points[i].x)
        path=[];cur=start;prev=None
        while cur not in path:
            path.append(cur);nxt=[i for i in adj[cur] if i!=prev]
            if not nxt:break
            prev,cur=cur,nxt[0]
        if len(path)!=len(rim):raise RuntimeError('COVERED_NECKLINE_BOUNDARY_DISCONNECTED')
        arc=np.r_[0,np.cumsum([(points[a]-points[b]).length for a,b in zip(path,path[1:])])];arc/=arc[-1]
        displacement=np.zeros((len(points),3));fixed=np.zeros(len(points),bool)
        region=np.array([p.y<.015 and abs(p.x-cx)<.177 and 1.065<p.z<1.416 for p in points])
        fixed[~region]=True
        for i,t in zip(path,arc):
            q=points[i].copy();q.x=cx+(t-.5)*.318;q.z=1.355+.029*((t-.5)*2)**2
            hit=bvh.ray_cast(Vector((q.x,-.5,q.z)),Vector((0,1,0)),.8)
            if hit[0]:q.y=hit[0].y-.005
            displacement[i]=q-points[i];fixed[i]=True;lifted[i]=q
        edges=np.array([(e.vertices[0],e.vertices[1]) for e in ob.data.edges]);aa=np.r_[edges[:,0],edges[:,1]];bb=np.r_[edges[:,1],edges[:,0]];degree=np.bincount(aa,minlength=len(points))
        for iteration in range(600):
            total=np.zeros_like(displacement);np.add.at(total,aa,displacement[bb]);new=total/np.maximum(degree[:,None],1);displacement[~fixed]=new[~fixed]
        for i in np.where(region)[0]:
            q=points[i]+Vector(displacement[i]);hit=bvh.ray_cast(Vector((q.x,-.5,q.z)),Vector((0,1,0)),.8)
            if hit[0]:q.y=min(q.y,hit[0].y-.005)
            lifted[i]=q
        bm.free()
    if not ob.data.shape_keys:ob.shape_key_add(name='Basis',from_mix=False)
    key=ob.shape_key_add(name=keyname,from_mix=False);key.value=1
    changed={};reweights={};maxmove=0
    for i,p in enumerate(points):
        q=p.copy();x=p.x-cx
        if i in lifted:
            q=lifted[i]
            if (q-p).length>.012:
                nearest=bvh.find_nearest(q)
                if nearest[0]:reweights[i]=nearest[2]
        # Ease the front panel across the bust: remove the cleft without
        # changing shoulder, armhole, waist or cuff anchoring.
        if ob.name.lower().find('dress')>=0 and 1.105<p.z<1.28 and p.y<-.085 and abs(x)<.13:
            w=smooth((p.z-1.105)/.055)*smooth((1.28-p.z)/.035)*smooth((.13-abs(x))/.045)
            target=-.177-.004*(1-min(abs(x)/.13,1))
            q.y-=min(.014,max(0,q.y-target))*w
        delta=q-p
        if delta.length>1e-7:
            key.data[i].co=ob.matrix_world.inverted()@q;changed[i]=q;maxmove=max(maxmove,delta.length)
    # Vertices lifted into the upper chest follow upper chest weights instead
    # of retaining breast influence. No changes are made to the body rig.
    rig_names=set(body.parent.data.bones.keys());weights={}
    for i,faceid in reweights.items():
        poly=faces[faceid];q=changed[i];dist=[1/max((bpoints[j]-q).length,1e-5)**2 for j in poly];total=sum(dist);row={}
        for j,a in zip(poly,dist):
            for g in body.data.vertices[j].groups:
                name=body.vertex_groups[g.group].name
                if name in rig_names:row[name]=row.get(name,0)+g.weight*a/total
        norm=sum(row.values())
        if norm:weights[i]={name:v/norm for name,v in row.items()}
    targets=[ob]+[p for p in bpy.data.objects if p.get('castGarmentProxySource')==ob.name and len(p.data.vertices)==len(points)]
    for target in targets:
        if target!=ob:
            if not target.data.shape_keys:target.shape_key_add(name='Basis',from_mix=False)
            pk=target.shape_key_add(name=keyname,from_mix=False);pk.value=1
            for i,q in changed.items():pk.data[i].co=target.matrix_world.inverted()@q
        for i,row in weights.items():
            for group in target.vertex_groups:
                if group.name in rig_names:group.remove([i])
            for name,w in row.items():
                group=target.vertex_groups.get(name) or target.vertex_groups.new(name=name);group.add([i],w,'REPLACE')
        target.data.update()
    attr=ob.data.attributes.get('cast_cloth_rest') or ob.data.attributes.new('cast_cloth_rest','FLOAT_VECTOR','POINT')
    for i,p in enumerate(points):attr.data[i].vector=changed.get(i,p)
    return {'key':keyname,'changedVertices':len(changed),'upperChestWeightTransfers':len(weights),'maximumDisplacementMetres':maxmove,'seamProxies':len(targets)-1,'basisPreserved':True,'coveredNeckline':covered}

def apply_cloth_appearance(scene,character):
    palette=colours();body=bpy.data.objects['Host.body'];rows=[]
    garments=[o for o in scene.objects if o.type=='MESH' and (not o.hide_render or o.get('castFitOriginalHideRender') is False) and o.name.removeprefix('Host.') in palette and any(m and m.name.startswith(('V63_DRESS_','V70_G_')) for m in o.data.materials)]
    for ob in garments:
        asset=ob.name.removeprefix('Host.');h=palette[asset];fabric=fabric_for(asset)
        covered=asset=='mindfront_f_dress_09'
        rebuild=covered and not (ob.data.shape_keys and ob.data.shape_keys.key_blocks.get('Cast V15 covered tailored fit'))
        if rebuild:
            for old in list(scene.objects):
                if old.get('castGarmentSource')==ob.name or old.get('castGarmentProxySource')==ob.name:bpy.data.objects.remove(old,do_unlink=True)
        fit=fit_cloth(ob,body,covered) if character=='female' else None
        if rebuild:
            source=Path(os.environ['PV1'])/'dressart.py'
            previous={k:os.environ.get(k) for k in ('DOBJ','DCOL','DSTW','DOFF','DFW','DINS')}
            os.environ.update(DOBJ=ob.name,DCOL=h,DSTW='0.0005',DOFF='0.0008',DFW='0.0010',DINS='0.005')
            thickness=[m for m in ob.modifiers if m.type=='SOLIDIFY' and m.show_viewport]
            for m in thickness:m.show_viewport=False
            try:runpy.run_path(str(source))
            finally:
                for m in thickness:m.show_viewport=True
            for proxy in scene.objects:
                if proxy.get('castGarmentProxySource')==ob.name:
                    for m in proxy.modifiers:
                        if m.type=='SOLIDIFY':proxy.modifiers.remove(m)
            for k,v in previous.items():
                if v is None:os.environ.pop(k,None)
                else:os.environ[k]=v
            fit['seamsRebuilt']=True
            fit['seamProxies']=sum(p.get('castGarmentProxySource')==ob.name for p in scene.objects)
        if not ob.data.attributes.get('cast_cloth_rest'):
            attr=ob.data.attributes.new('cast_cloth_rest','FLOAT_VECTOR','POINT')
            for v,d in zip(ob.data.vertices,attr.data):d.vector=ob.matrix_world@v.co
        for mat in ob.data.materials:
            if mat and mat.name.startswith(('V63_DRESS_','V70_G_')):cloth_material(mat,h,fabric)
        for lines in scene.objects:
            if lines.get('castGarmentSource')!=ob.name:continue
            for slot in lines.material_slots:
                if not slot.material:continue
                old=slot.material
                if old.get('castClothProfile')==PROFILE:mat=old
                else:
                    mat=old.copy();mat.name='Cast V15 '+asset+' '+old.name;mat['castClothProfile']=PROFILE
                mat.use_nodes=True
                for n in mat.node_tree.nodes:
                    if n.type=='EMISSION':n.inputs['Color'].default_value=(*[c*(.32 if 'INK' in old.name else .62) for c in linear(h)],1)
                slot.material=mat
        rows.append({'object':ob.name,'baseHex':h,'fabric':fabric,'fit':fit})
    bpy.context.view_layer.update();scene['castClothProfile']=PROFILE
    return {'profile':PROFILE,'codeSHA256':MODULE_SHA256,'garments':rows,'skinHairRigUnchanged':True}
