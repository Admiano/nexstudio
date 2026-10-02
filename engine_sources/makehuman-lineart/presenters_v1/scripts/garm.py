import bpy,sys,os
import numpy as np
sys.path.insert(0,__import__('os').path.join(__import__('os').environ['PV1'],'..','..','scripts'))
import mhclo_fit as F
import bmesh as _bmd
_GR=[__import__('os').environ.get('MH_ROOT','/home/ubuntu/mh_assets')+'/%s/clothes'%d for d in ('shirts01_cc0','shirts02_ccby','shirts03_ccby','pants01_cc0','pants02_ccby','pants03_ccby','shoes01_cc0','shoes02_ccby')]
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
def _fit(path,W):
    sc,refs,_=F.load_mhclo(path)
    if 'x' in sc: return F.fit(path,W)
    sh={}
    for line in open(path):
        p=line.split()
        if p and p[0] in ('l_shear_x','l_shear_y','l_shear_z'): sh[p[0][-1]]=(int(p[1]),int(p[2]),float(p[3]),float(p[4]))
    def s(a,c):
        i,j,u,v=sh[a]; return abs(W[i][c]-W[j][c])/abs(u-v)
    sx,sy,sz=s('x',0),s('y',2),s('z',1)
    from mathutils import Vector as _V
    return [W[a]*u+W[b]*v+W[c]*w+_V((dx*sx,-dz*sz,dy*sy)) for (a,b,c),(u,v,w),(dx,dy,dz) in refs],refs
_MG=[x.split('=') for x in os.environ.get('MG','').split(',') if x]
if _MG:
    P='Host.'; old=bpy.data.objects[P+'mindfront_f_dress_01']; body=bpy.data.objects[P+'body']; rig=old.parent
    legs=bpy.data.objects.get(P+'lineart_lower_legs')
    tm=body.modifiers['Delete.mindfront_f_dress_01']
    for m in body.modifiers:
        if m.type=='MASK' and m.vertex_group.startswith('Delete.'): m.show_render=m.show_viewport=False
    W=F.shaped_coords(body)
    bones={b.name for b in rig.data.bones if b.use_deform}
    gname={x.index:x.name for x in body.vertex_groups if x.name in bones}
    made=[]
    for _gn,_col in _MG:
        path=[os.path.join(r,_gn,_gn+'.mhclo') for r in _GR if os.path.exists(os.path.join(r,_gn,_gn+'.mhclo'))][0]
        pts,refs=_fit(path,W); _,_,objp=F.load_mhclo(path); objv,faces=F.load_obj(objp)
        me=bpy.data.meshes.new(P+_gn); me.from_pydata([tuple(p) for p in pts],[],faces); me.update()
        _bd=_bmd.new(); _bd.from_mesh(me); _bd.verts.ensure_lookup_table(); _seen=set(); _kill=[]
        _mn=int(os.environ.get('GMINISL','60'))
        for _v in _bd.verts:
            if _v.index in _seen: continue
            _st=[_v]; _cp=[]; _seen.add(_v.index)
            while _st:
                _x=_st.pop(); _cp.append(_x)
                for _e in _x.link_edges:
                    _o=_e.other_vert(_x)
                    if _o.index not in _seen: _seen.add(_o.index); _st.append(_o)
            _cc=np.array([pts[_x.index][:] for _x in _cp]) if len(_cp)<400 else None
            if len(_cp)<_mn or (_cc is not None and np.linalg.norm(_cc.max(0)-_cc.min(0))<float(os.environ.get('GBTN','0.022'))): _kill+=_cp
        _ks=set(_kill); _keep=[v.index for v in _bd.verts if v not in _ks]
        if _kill: _bmd.ops.delete(_bd,geom=list(_ks),context='VERTS')
        _bd.to_mesh(me); _bd.free(); pts=[pts[i] for i in _keep]; refs=[refs[i] for i in _keep]
        for p in me.polygons: p.use_smooth=True
        mat=old.data.materials[0].copy(); mat.name='V70_G_'+_gn; me.materials.append(mat)
        g=bpy.data.objects.new(P+_gn,me)
        for c in old.users_collection: c.objects.link(g)
        g.parent=rig; g.matrix_world=old.matrix_world.copy(); mwi=g.matrix_world.inverted()
        for v,p in zip(me.vertices,pts): v.co=mwi@p
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
        dv=_delv(path)
        for ob in (body,legs):
            if ob is None or len(ob.data.vertices)!=len(body.data.vertices) or not dv: continue
            dg=ob.vertex_groups.new(name='Delete.'+_gn); dg.add(dv,1.0,'REPLACE')
            mk=ob.modifiers.new('Delete.'+_gn,'MASK'); mk.vertex_group=dg.name; mk.invert_vertex_group=tm.invert_vertex_group; mk.threshold=tm.threshold
            ss0=[m for m in ob.modifiers if m.type=='SUBSURF']
            if ss0:
                while ob.modifiers.find(mk.name)>ob.modifiers.find(ss0[0].name): ob.modifiers.move(ob.modifiers.find(mk.name),ob.modifiers.find(mk.name)-1)
        if any(k in _gn for k in ('shoe','sneaker')):
            for n in ('Host.lineart_shoe.L','Host.lineart_shoe.R'):
                o=bpy.data.objects.get(n)
                if o: o.hide_render=o.hide_viewport=True
        made.append((g.name,_col)); print('GARM',g.name,len(pts),'groups',len(acc),'masked',len(dv),'islands-removed',len(_ks))
    old.hide_render=old.hide_viewport=True
    for c in list(old.users_collection):
        if c.name!='Collection': c.objects.unlink(old)
    mc=bpy.data.collections.get('V26_GARMENT_MARKS')
    if mc:
        for o in mc.objects: o.hide_render=o.hide_viewport=True
    # Never delete the trouser waistband at a bind-pose shirt hem.
    # Complete topology and deformation weights are needed through animation.
    _tops=[bpy.data.objects[n] for n,_ in made if not any(k in n.lower() for k in ('trouser','jeans','pants','shoe','sneaker')) and 'tucked-' not in n.lower() and not ('tucked' in n.lower() and 'untucked' not in n.lower())]
    from mathutils import Vector
    # Bounded surface coverage supplements garments with missing body masks.
    from mathutils.bvhtree import BVHTree
    _covered=set()
    _protected={g.index for g in body.vertex_groups if any(k in g.name.lower() for k in ('hand','finger','thumb','head','neck'))}
    _bodypts=[body.matrix_world@v.co for v in body.data.vertices]
    for _name,_ in made:
        if any(k in _name.lower() for k in ('shoe','sneaker')):continue
        _ob=bpy.data.objects[_name];_pts=[_ob.matrix_world@v.co for v in _ob.data.vertices]
        _tree=BVHTree.FromPolygons(_pts,[list(p.vertices) for p in _ob.data.polygons],all_triangles=False)
        for _v,_point in zip(body.data.vertices,_bodypts):
            if any(g.group in _protected and g.weight>0.1 for g in _v.groups):continue
            for _direction in (Vector((0,1,0)),Vector((0,-1,0))):
                _hit,_normal,_index,_distance=_tree.ray_cast(_point-_direction*0.05,_direction,0.10)
                if _hit is not None:_covered.add(_v.index);break
    _boundary=set()
    for _edge in body.data.edges:
        _a,_b=_edge.vertices
        if (_a in _covered)!=(_b in _covered):_boundary.update((_a,_b))
    _covered-=_boundary
    if _covered:
        for _ob in (body,legs):
            if _ob is None or len(_ob.data.vertices)!=len(body.data.vertices):continue
            _group=_ob.vertex_groups.new(name='Delete.FittedGarmentCoverage');_group.add(sorted(_covered),1.0,'REPLACE')
            _mask=_ob.modifiers.new('Delete.FittedGarmentCoverage','MASK');_mask.vertex_group=_group.name;_mask.invert_vertex_group=tm.invert_vertex_group;_mask.threshold=tm.threshold
            _ss=[m for m in _ob.modifiers if m.type=='SUBSURF']
            if _ss:
                while _ob.modifiers.find(_mask.name)>_ob.modifiers.find(_ss[0].name):_ob.modifiers.move(_ob.modifiers.find(_mask.name),_ob.modifiers.find(_mask.name)-1)
        print('GARMENT_BODY_COVERAGE',len(_covered),flush=True)
    os.environ['DOBJ']=made[0][0]
    os.environ['GARMS']=';'.join('%s=%s'%x for x in made)
