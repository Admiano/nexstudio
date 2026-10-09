import bpy, numpy as np, os, bmesh
from mathutils import Vector, Matrix
_E=lambda k,d: float(os.environ.get(k,d))
_b=bpy.data.objects['Host.body']; _h=bpy.data.objects[os.environ.get('HOBJ','Host.hair_culturalibre_hair_01')]; _r=bpy.data.objects['Host.rig']
_gi=_b.vertex_groups['ears'].index
_ec=np.array([v.co[:] for v in _b.data.vertices if any(g.group==_gi and g.weight>0.5 for g in v.groups)])
_sd=_E('ESIDE','1')
_q=_ec[_ec[:,0]*_sd>0]
_ctr=_q.mean(0); _lobe=_q[_q[:,2].argmin()]
print('EAR ctr',_ctr.round(4),'lobe',_lobe.round(4),'n',len(_q))
# hair tuck shape key (static, value 1)
if _E('TUCK','1')>0:
    if not _h.data.shape_keys: _h.shape_key_add(name='Basis',from_mix=False)
    _k=_h.shape_key_add(name='V60_tuck',from_mix=False)
    _hc=np.array([v.co[:] for v in _h.data.vertices])
    _z=_hc[:,2]-_ctr[2]
    _wz=np.interp(_z,[-_E('TZB','0.20'),-_E('TZF','0.05'),0.03,_E('TZT','0.08')],[0,1,1,0])
    _wx=np.clip((_hc[:,0]*_sd-0.035)/0.02,0,1)
    _w=_wz*_wx
    _ed=np.zeros(len(_h.data.edges)*2,int); _h.data.edges.foreach_get('vertices',_ed); _ed=_ed.reshape(-1,2)
    for _it in range(int(_E('TSM','12'))):
        _acc=np.zeros(len(_w)); _cnt=np.zeros(len(_w))
        np.add.at(_acc,_ed[:,0],_w[_ed[:,1]]); np.add.at(_acc,_ed[:,1],_w[_ed[:,0]])
        np.add.at(_cnt,_ed[:,0],1); np.add.at(_cnt,_ed[:,1],1)
        _w=0.5*_w+0.5*_acc/np.maximum(_cnt,1)
    _w=_w*_w*(3-2*_w)
    _yt=_ctr[1]+_E('TY','0.035')
    _new=_hc.copy()
    if _E('TMODE','1')>0:
        _dl=np.maximum(0,_yt-np.percentile(_hc[_w>0.5,1],float(os.environ.get('TPC','10'))))
        _dy=np.maximum(np.minimum(_dl,np.maximum(0,_yt-_hc[:,1])*_E('TKEEP','0.0')+_dl),0)
    else:
        _dy=np.maximum(0,_yt-_hc[:,1])
    _new[:,1]=_hc[:,1]+_w*_dy
    _new[:,0]=_hc[:,0]+_sd*_w*_dy*_E('TX','0.25')
    _k.data.foreach_set('co',_new.ravel()); _k.value=1.0
    print('EAR tuck verts',int((_w>0.05).sum()))
# earring
_gm=bpy.data.materials.new('V60_GOLD'); _gm.use_nodes=True; _nt=_gm.node_tree; _nt.nodes.clear()
_em=_nt.nodes.new('ShaderNodeEmission'); _em.inputs['Color'].default_value=(0.83,0.60,0.22,1)
_o=_nt.nodes.new('ShaderNodeOutputMaterial'); _nt.links.new(_em.outputs[0],_o.inputs[0])
_me=bpy.data.meshes.new('V60_earring'); _bm=bmesh.new()
_RR=_E('HR','0.011'); _rr=_E('HW','0.0014')
bmesh.ops.create_cone(_bm,cap_ends=True,segments=4,radius1=0.0001,radius2=0.0001,depth=0.0001) if False else None
# hoop torus in XZ plane (facing camera)
_ns,_nr=48,10; _vs=[]
for i in range(_ns):
    a=2*np.pi*i/_ns; c=Vector((np.cos(a)*_RR*0.8,0,np.sin(a)*_RR))
    for j in range(_nr):
        t=2*np.pi*j/_nr; n=Vector((np.cos(a)*np.cos(t)*0.8,np.sin(t),np.sin(a)*np.cos(t)))
        _vs.append(_bm.verts.new(c+n.normalized()*_rr))
for i in range(_ns):
    for j in range(_nr):
        a=i*_nr+j; b_=((i+1)%_ns)*_nr+j; c_=((i+1)%_ns)*_nr+(j+1)%_nr; d_=i*_nr+(j+1)%_nr
        _bm.faces.new((_vs[a],_vs[b_],_vs[c_],_vs[d_]))
_bm.to_mesh(_me); _bm.free()
_eo=bpy.data.objects.new('Host.V60_earring',_me); _me.materials.append(_gm)
for c in _b.users_collection: c.objects.link(_eo)
_li=[v.index for v in _b.data.vertices if any(g.group==_gi and g.weight>0.5 for g in v.groups)]
_li=[i for i in _li if _b.data.vertices[i].co.x*_sd>0]
_li=min(_li,key=lambda i:_b.data.vertices[i].co.z)
_sv=[(m,m.show_viewport) for m in _b.modifiers if m.type in ('MASK','SUBSURF')]
for m,_ in _sv: m.show_viewport=False
bpy.context.view_layer.update(); _dg=bpy.context.evaluated_depsgraph_get(); _be=_b.evaluated_get(_dg); _em2=_be.to_mesh()
_lw=_b.matrix_world@_em2.vertices[_li].co; _be.to_mesh_clear()
for m,f in _sv: m.show_viewport=f
_eo.location=_lw+Vector((_sd*_E('EX','0.002'),_E('EY','0.004'),-_RR+_E('EZ','0.001')))
print('EAR lobe world',tuple(round(x,4) for x in _lw),'frame',bpy.context.scene.frame_current)
bpy.context.view_layer.update()
_bn=_r.pose.bones['head']
_mw=_eo.matrix_world.copy()
_eo.parent=_r; _eo.parent_type='BONE'; _eo.parent_bone='head'
bpy.context.view_layer.update()
_eo.matrix_world=_mw
[print('EARLS',l.name,l.show_render,l.select_by_collection,l.collection and l.collection.name,l.collection_negation) for l in bpy.context.view_layer.freestyle_settings.linesets]
print('EAR ring at',tuple(round(x,4) for x in _eo.matrix_world.translation))

def _tube(P,r,mat,name,n=10):
    P=[Vector(p) for p in P]; bm=bmesh.new(); rings=[]
    for i,p in enumerate(P):
        t=(P[min(i+1,len(P)-1)]-P[max(i-1,0)]).normalized()
        a=Vector((0,1,0)).cross(t); a=a.normalized() if a.length>1e-6 else Vector((1,0,0)); b2=t.cross(a)
        rings.append([bm.verts.new(p+(a*np.cos(2*np.pi*j/n)+b2*np.sin(2*np.pi*j/n))*r) for j in range(n)])
    for i in range(len(rings)-1):
        for j in range(n): bm.faces.new((rings[i][j],rings[i+1][j],rings[i+1][(j+1)%n],rings[i][(j+1)%n]))
    for rg in (rings[0],rings[-1]): bm.faces.new(rg)
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    ob=bpy.data.objects.new(name,me)
    for c in _b.users_collection: c.objects.link(ob)
    mw=Matrix.Identity(4); ob.parent=_r; ob.parent_type='BONE'; ob.parent_bone='head'
    bpy.context.view_layer.update(); ob.matrix_world=mw
    _ex=bpy.data.collections.get('NO_HEAD_OUTLINE')
    if _ex: _ex.objects.link(ob)
    return ob
_ink=bpy.data.materials['V59_INK'] if 'V59_INK' in bpy.data.materials else bpy.data.materials['LINEART_EYE_INK']
# hoop ink rim: dark ring slightly behind and thicker
_rim=_eo.copy(); _rim.data=_eo.data.copy(); _rim.data.materials.clear(); _rim.data.materials.append(_ink); _rim.name='Host.V60_earring_rim'
for c in _eo.users_collection: c.objects.link(_rim)
_rim.parent=_eo
if os.environ.get('CAST_QUALITY_PILOT')=='1':
    # A rim copied from a bone-parented earring is now an object child.
    # Retaining BONE parenting asks a mesh for a nonexistent head bone.
    _rim.parent_type='OBJECT'; _rim.parent_bone=''
_rim.matrix_parent_inverse=Matrix.Identity(4); _rim.location=(0,_E('RY','0.003'),0); _rim.rotation_euler=(0,0,0); _rim.scale=(1,1,1)
_rs=_E('RS','1.0')
for v in _rim.data.vertices:
    pass
import math
_ns,_nr=48,10
for i in range(_ns):
    a=2*np.pi*i/_ns; c=Vector((np.cos(a)*_RR*0.8,0,np.sin(a)*_RR))
    for j in range(_nr):
        v=_rim.data.vertices[i*_nr+j]; d=(v.co-c); d=Vector((d.x*_E('RWF','1.9'),d.y*0.3,d.z*_E('RWF','1.9'))); v.co=c+d
_eo.data.materials[0]=_gm
if bpy.data.collections.get('NO_HEAD_OUTLINE'): bpy.data.collections['NO_HEAD_OUTLINE'].objects.link(_rim)
# ear outline from evaluated ear silhouette
_sv=[(m,m.show_viewport) for m in _b.modifiers if m.type in ('MASK','SUBSURF')]
for m,_ in _sv: m.show_viewport=False
bpy.context.view_layer.update(); _dg=bpy.context.evaluated_depsgraph_get(); _be=_b.evaluated_get(_dg); _em3=_be.to_mesh()
_ids=[v.index for v in _b.data.vertices if any(g.group==_gi and g.weight>0.3 for g in v.groups) and v.co.x*_sd>0]
_W=np.array([(_b.matrix_world@_em3.vertices[i].co)[:] for i in _ids]); _be.to_mesh_clear()
for m,f in _sv: m.show_viewport=f
_cx=(_b.matrix_world@Vector((0,0,0))).x
_px=(_W[:,0]-_cx)*_sd
_zmin,_zmax=_W[:,2].min(),_W[:,2].max()
_mid=(_W[:,2]>_zmin+0.25*(_zmax-_zmin))&(_W[:,2]<_zmax-0.25*(_zmax-_zmin))
_xin=np.percentile(_px[_mid],float(os.environ.get('EPIN','15'))); _xout=_px.max()
_zc=(_zmin+_zmax)/2+_E('EZC','0.0'); _rx=(_xout-_xin)+_E('EPR','0.006'); _rz=(_zmax-_zmin)/2*_E('ERZ','0.95')
_yl=_W[:,1].min()-_E('EYO','0.002')
_th=np.radians(np.linspace(_E('EA0','105'),-_E('EA1','115'),60))
_rxs=_rx*(1+_E('ELB','0.15')*np.clip(-np.sin(_th),0,1))
_pts=np.stack([_cx+(_xin+_rxs*np.cos(_th))*_sd,np.full(len(_th),_yl),_zc+_rz*np.sin(_th)],1)
_eol=_tube(_pts,_E('EOR','0.0011'),_ink,'Host.V60_ear_line')
_sk=bpy.data.materials.new('V60_EAR_SKIN'); _sk.use_nodes=True; _snt=_sk.node_tree; _snt.nodes.clear()
_se=_snt.nodes.new('ShaderNodeEmission'); _se.inputs['Color'].default_value=(_E('ESR','0.80'),_E('ESG','0.60'),_E('ESB','0.50'),1)
_so=_snt.nodes.new('ShaderNodeOutputMaterial'); _snt.links.new(_se.outputs[0],_so.inputs[0])
_bm2=bmesh.new(); _cv=_bm2.verts.new((_cx+(_xin-0.004)*_sd,_yl+0.0006,_zc)); _rv=[_bm2.verts.new((p[0],p[1]+0.0006,p[2])) for p in _pts]
for i in range(len(_rv)-1): _bm2.faces.new((_cv,_rv[i],_rv[i+1]))
_dm=bpy.data.meshes.new('V60_ear_fill'); _bm2.to_mesh(_dm); _bm2.free(); _dm.materials.append(_sk)
_do=bpy.data.objects.new('Host.V60_ear_fill',_dm)
for c in _b.users_collection: c.objects.link(_do)
_do.parent=_r; _do.parent_type='BONE'; _do.parent_bone='head'; bpy.context.view_layer.update(); _do.matrix_world=Matrix.Identity(4)
if bpy.data.collections.get('NO_HEAD_OUTLINE'): bpy.data.collections['NO_HEAD_OUTLINE'].objects.link(_do)
_th2=np.radians(np.linspace(80,-70,40)); _ir=_E('EIR','0.55')
_inner=np.stack([_cx+(_xin+_rx*_E('EIC','0.3')+_rx*_ir*np.cos(_th2))*_sd,np.full(len(_th2),_yl-0.0003),_zc+0.1*_rz+_rz*_ir*np.sin(_th2)],1)
if _E('EINNER','1')>0: _tube(_inner,_E('EOR','0.0011')*0.7,_ink,'Host.V60_ear_inner')
print('EAR shape xin',round(_xin,4),'xout',round(_xout,4),'rx',round(_rx,4),'rz',round(_rz,4))
bpy.context.view_layer.update()
for _n in ('Host.V60_ear_line','Host.V60_ear_inner','Host.V60_ear_fill','Host.V60_earring'):
    _o2=bpy.data.objects.get(_n)
    if _o2:
        _bb=np.array([(_o2.matrix_world@Vector(c))[:] for c in _o2.bound_box]); print('EARDBG',_n,_bb.min(0).round(4),_bb.max(0).round(4),len(_o2.data.polygons),_o2.hide_render,[c.name for c in _o2.users_collection])
