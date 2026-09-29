import bpy, sys, os, numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0,__import__('os').path.join(__import__('os').environ['PV1'],'..','..','scripts'))
import mhclo_fit as F
_HAIR=os.environ.get('HAIR','')
if _HAIR and _HAIR!='culturalibre_hair_01':
    P='Host.'; old=bpy.data.objects[P+'hair_culturalibre_hair_01']; body=bpy.data.objects[P+'body']; rig=old.parent
    W=F.shaped_coords(body)
    path=F.asset('hair',_HAIR); pts,_=(_fit if '_fit' in globals() else F.fit)(path,W); _,_,objp=F.load_mhclo(path); objv,faces=F.load_obj(objp)
    assert len(pts)==len(objv)
    me=bpy.data.meshes.new(P+_HAIR); me.from_pydata([tuple(p) for p in pts],[],faces); me.update()
    import bmesh as _bmf
    _b0=_bmf.new(); _b0.from_mesh(me); _r0=_bmf.ops.holes_fill(_b0,edges=_b0.edges[:],sides=int(os.environ.get('HHOLE','8'))); _b0.to_mesh(me); _b0.free()
    print('HAIRSWAP holes filled',len(_r0['faces']))
    for p in me.polygons: p.use_smooth=True
    me.materials.append(old.data.materials[0])
    hair=bpy.data.objects.new(P+'hair_'+_HAIR,me)
    for c in old.users_collection: c.objects.link(hair)
    hair.parent=rig; hair.matrix_world=old.matrix_world.copy(); mwi=hair.matrix_world.inverted()
    for v,p in zip(me.vertices,pts): v.co=mwi@p
    arm=hair.modifiers.new('Armature','ARMATURE'); arm.object=rig
    ss=hair.modifiers.new('Subsurf','SUBSURF'); ss.levels=ss.render_levels=1
    old.hide_render=True; old.hide_viewport=True
    for c in list(old.users_collection):
        if c.name in ('HAIR_LINES','FACE_FINE'): c.objects.unlink(old)
    S=bpy.context.scene; S.frame_set(1); bpy.context.view_layer.update()
    rest={b:(rig.matrix_world@rig.data.bones[b].head_local).z for b in ('head','neck01','spine05')}
    top=rest['head']+0.04; low=rest['spine05']
    solids=[body,bpy.data.objects[os.environ.get('DOBJ',P+'mindfront_f_dress_01')]]
    dg=bpy.context.evaluated_depsgraph_get()
    ev=body.evaluated_get(dg); bm_=ev.to_mesh()
    bt=BVHTree.FromPolygons([ev.matrix_world@v.co for v in bm_.vertices],[tuple(p.vertices) for p in bm_.polygons]); ev.to_mesh_clear()
    gh=hair.vertex_groups.new(name='head'); gn=hair.vertex_groups.new(name='neck01'); gc=hair.vertex_groups.new(name='spine05')
    gl=hair.vertex_groups.new(name='hair_lower'); gd=hair.vertex_groups.new(name='hair_hidden')
    mw=hair.matrix_world; hidden=0
    for v in me.vertices:
        p=mw@v.co; z=p.z; u=min(1.0,max(0.0,(top-z)/(top-low))); u=u*u*(3-2*u)
        gh.add([v.index],1.0-u,'REPLACE'); gn.add([v.index],0.6*u,'REPLACE'); gc.add([v.index],0.4*u,'REPLACE')
        if u>0: gl.add([v.index],1.0,'REPLACE')
        loc,nor,_,_=bt.find_nearest(p,0.05)
        if loc is not None and z<rest['head'] and (p-loc).dot(nor)<-0.008: gd.add([v.index],1.0,'REPLACE'); hidden+=1
    import bmesh as _bmm
    _bm=_bmm.new(); _bm.from_mesh(me); _seen=set(); _small=[]
    for _v in _bm.verts:
        if _v.index in _seen: continue
        _st=[_v]; _cp=[]; _seen.add(_v.index)
        while _st:
            _x=_st.pop(); _cp.append(_x.index)
            for _e in _x.link_edges:
                _o=_e.other_vert(_x)
                if _o.index not in _seen: _seen.add(_o.index); _st.append(_o)
        if len(_cp)<int(os.environ.get('HMINISL','12')): _small+=_cp
    _bm.free()
    if _small: gd.add(_small,1.0,'REPLACE')
    print('HAIRSWAP small islands verts',len(_small))
    mk=hair.modifiers.new('V26_hide_inner','MASK'); mk.vertex_group='hair_hidden'; mk.invert_vertex_group=True
    for o in solids:
        sw=hair.modifiers.new('V26_clear_'+o.name.split('.')[-1],'SHRINKWRAP'); sw.target=o; sw.wrap_method='NEAREST_SURFACEPOINT'; sw.wrap_mode='OUTSIDE'; sw.offset=0.006; sw.vertex_group='hair_lower'
    order=['Armature','V26_hide_inner','Subsurf']+['V26_clear_'+o.name.split('.')[-1] for o in solids]
    for i,n in enumerate(order):
        with bpy.context.temp_override(object=hair): bpy.ops.object.modifier_move_to_index(modifier=n,index=i)
    if float(os.environ.get('HSCALP','1'))>0:
        sw=hair.modifiers.new('V61_clear_scalp','SHRINKWRAP'); sw.target=body; sw.wrap_method='NEAREST_SURFACEPOINT'; sw.wrap_mode='OUTSIDE'; sw.offset=float(os.environ.get('HSOFF','0.003'))
    os.environ['HOBJ']=hair.name
    print('HAIRSWAP',hair.name,len(me.vertices),'hidden',hidden)
