import bpy,sys,os
sys.path.insert(0,__import__('os').path.join(__import__('os').environ['PV1'],'..','..','scripts'))
import mhclo_fit as F
_DR=os.environ.get('DRESS','')
_DROOTS=[__import__('os').environ.get('MH_ROOT','/home/ubuntu/mh_assets')+'/dress01_cc0/clothes',__import__('os').environ.get('MH_ROOT','/home/ubuntu/mh_assets')+'/dress02_cc-by/clothes',__import__('os').environ.get('MH_ROOT','/home/ubuntu/mh_assets')+'/dress03_cc-by/clothes']
def _delv(path):
    out,on=[],False
    for line in open(path):
        p=line.split()
        if not p: continue
        if p[0]=='delete_verts': on=True; continue
        if not on: continue
        if not (p[0].isdigit() or p[0]=='-'): break
        i=0
        while i<len(p):
            if i+2<len(p) and p[i+1]=='-': out+=range(int(p[i]),int(p[i+2])+1); i+=3
            else: out.append(int(p[i])); i+=1
    return out
os.environ.setdefault('DOBJ','Host.mindfront_f_dress_01')
if _DR and _DR!='mindfront_f_dress_01':
    P='Host.'; old=bpy.data.objects[P+'mindfront_f_dress_01']; body=bpy.data.objects[P+'body']; rig=old.parent
    path=[os.path.join(r,_DR,_DR+'.mhclo') for r in _DROOTS if os.path.exists(os.path.join(r,_DR,_DR+'.mhclo'))][0]
    W=F.shaped_coords(body); pts,refs=F.fit(path,W); _,_,objp=F.load_mhclo(path); objv,faces=F.load_obj(objp)
    assert len(pts)==len(objv)
    me=bpy.data.meshes.new(P+_DR); me.from_pydata([tuple(p) for p in pts],[],faces); me.update()
    import bmesh as _bmd
    _mn=int(os.environ.get('DMINISL','0'))
    if _mn:
        _bd=_bmd.new(); _bd.from_mesh(me); _bd.verts.ensure_lookup_table(); _seen=set(); _kill=[]
        for _v in _bd.verts:
            if _v.index in _seen: continue
            _st=[_v]; _cp=[]; _seen.add(_v.index)
            while _st:
                _x=_st.pop(); _cp.append(_x)
                for _e in _x.link_edges:
                    _o=_e.other_vert(_x)
                    if _o.index not in _seen: _seen.add(_o.index); _st.append(_o)
            if len(_cp)<_mn: _kill+=_cp
        _keep=[v.index for v in _bd.verts if v not in set(_kill)]
        _bmd.ops.delete(_bd,geom=list(set(_kill)),context='VERTS'); _bd.to_mesh(me); _bd.free()
        pts=[pts[i] for i in _keep]; refs=[refs[i] for i in _keep]
        print('DRESSSWAP removed island verts',len(set(_kill)))
    for p in me.polygons: p.use_smooth=True
    mat=old.data.materials[0].copy(); mat.name='V63_DRESS_'+_DR; me.materials.append(mat)
    g=bpy.data.objects.new(P+_DR,me)
    for c in old.users_collection: c.objects.link(g)
    g.parent=rig; g.matrix_world=old.matrix_world.copy(); mwi=g.matrix_world.inverted()
    for v,p in zip(me.vertices,pts): v.co=mwi@p
    bones={b.name for b in rig.data.bones if b.use_deform}
    gname={x.index:x.name for x in body.vertex_groups if x.name in bones}
    bw={i:[(gname[x.group],x.weight) for x in body.data.vertices[i].groups if x.group in gname] for i in {i for r in refs for i in r[0]}}
    acc={}
    for vi,(ids,ws,_) in enumerate(refs):
        tot={}
        for i,w in zip(ids,ws):
            for gg,gw in bw[i]: tot[gg]=tot.get(gg,0.0)+w*gw
        s=sum(tot.values()) or 1.0
        for gg,gw in tot.items(): acc.setdefault(gg,[]).append((vi,gw/s))
    for gg,items in acc.items():
        vg=g.vertex_groups.new(name=gg)
        for vi,w in items: vg.add([vi],w,'REPLACE')
    a=g.modifiers.new('Armature','ARMATURE'); a.object=rig
    ss=g.modifiers.new('Subsurf','SUBSURF'); ss.levels=ss.render_levels=1
    dv=_delv(path); dg=body.vertex_groups.new(name='Delete.'+_DR); dg.add(dv,1.0,'REPLACE')
    tm=body.modifiers['Delete.mindfront_f_dress_01']
    for m in body.modifiers:
        if m.type=='MASK' and m.vertex_group.startswith('Delete.'): m.show_render=m.show_viewport=False
    mk=body.modifiers.new('Delete.'+_DR,'MASK'); mk.vertex_group=dg.name; mk.invert_vertex_group=tm.invert_vertex_group; mk.threshold=tm.threshold
    while body.modifiers.find(mk.name)>body.modifiers.find(tm.name)+1: body.modifiers.move(body.modifiers.find(mk.name),body.modifiers.find(tm.name)+1)
    old.hide_render=old.hide_viewport=True
    for c in list(old.users_collection):
        if c.name!='Collection': c.objects.unlink(old)
    mc=bpy.data.collections.get('V26_GARMENT_MARKS')
    if mc:
        for o in mc.objects: o.hide_render=o.hide_viewport=True
    os.environ['DOBJ']=g.name
    print('DRESSSWAP',g.name,len(pts),'groups',len(acc),'masked',len(dv))
_DC=os.environ.get('DCOL','')
if _DC:
    _l=lambda c:(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4)
    _c=[_l(int(_DC.lstrip('#')[i:i+2],16)/255) for i in (0,2,4)]
    _o=bpy.data.objects[os.environ['DOBJ']]; _m=_o.data.materials[0]
    if _m.name=='PEEPS_V2_MUSTARD_JACKET': _m=_m.copy(); _o.data.materials[0]=_m
    _mi=[i for i in _m.node_tree.nodes['Mix'].inputs if i.enabled and i.type=='RGBA']
    _mi[0].default_value=(*_c,1); _mi[1].default_value=(*[x*0.72 for x in _c],1)
    print('DCOL',_DC)
