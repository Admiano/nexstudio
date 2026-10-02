import bpy,os,bmesh,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
_E=lambda k,d: float(os.environ.get(k,d))
_NW=os.environ.get('NECK','')
if _NW:
    _r=bpy.data.objects['Host.rig']; _b=bpy.data.objects['Host.body']; _dr=bpy.data.objects[os.environ.get('DOBJ','Host.mindfront_f_dress_01')]
    _dg=bpy.context.evaluated_depsgraph_get()
    _T=[BVHTree.FromObject(o.evaluated_get(_dg),_dg) for o in (_b,_dr)]
    _Mi=[o.matrix_world for o in (_b,_dr)]
    _nb=_r.pose.bones['neck01']; _nc=_r.matrix_world@_nb.head; _nt=_r.matrix_world@_nb.tail
    def _hit(z,th,off):
        d=Vector((np.sin(th),-np.cos(th),0)); a=_nc+(_nt-_nc)*((z-_nc.z)/max(_nt.z-_nc.z,1e-6)); a=Vector((a.x,a.y,z))
        o=a+d*0.35; best=None
        for t,M in zip(_T,_Mi):
            Mi=M.inverted(); lo=Mi@o; ld=(Mi.to_3x3()@(-d)).normalized()
            p,n,i,dist=t.ray_cast(lo,ld,1.0)
            if p is not None:
                wp=M@p
                if best is None or (wp-o).length<(best-o).length: best=wp
        return (best if best is not None else a)+d*off
    def _mat(name,rgb):
        m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
        e=nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value=(*rgb,1); o=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0],o.inputs[0]); return m
    _ink=bpy.data.materials['V59_INK'] if 'V59_INK' in bpy.data.materials else bpy.data.materials['LINEART_EYE_INK']
    _gold=bpy.data.materials.get('V60_GOLD') or _mat('V62_GOLD',(0.80,0.55,0.20))
    _col=[c for c in _b.users_collection]
    def _link(ob,bone):
        for c in _col: c.objects.link(ob)
        ob.parent=_r; ob.parent_type='BONE'; ob.parent_bone=bone; bpy.context.view_layer.update(); ob.matrix_world=Matrix.Identity(4)
        ex=bpy.data.collections.get('NO_HEAD_OUTLINE')
        if ex: ex.objects.link(ob)
        return ob
    def _tube(P,r,mat,name,bone,n=8,closed=False):
        bm=bmesh.new(); rings=[]; N=len(P)
        for i,p in enumerate(P):
            t=((P[(i+1)%N] if closed else P[min(i+1,N-1)])-(P[(i-1)%N] if closed else P[max(i-1,0)])).normalized()
            a=Vector((0,0,1)).cross(t); a=a.normalized() if a.length>1e-6 else Vector((1,0,0)); b2=t.cross(a)
            rr=r[i] if hasattr(r,'__len__') else r
            rings.append([bm.verts.new(p+(a*np.cos(2*np.pi*j/n)+b2*np.sin(2*np.pi*j/n))*rr) for j in range(n)])
        for i in range(N if closed else N-1):
            for j in range(n): bm.faces.new((rings[i][j],rings[(i+1)%N][j],rings[(i+1)%N][(j+1)%n],rings[i][(j+1)%n]))
        if not closed:
            for rg in (rings[0],rings[-1]): bm.faces.new(rg)
        me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
        return _link(bpy.data.objects.new(name,me),bone)
    def _sph(c,r,mat,name,bone,sq=(1,0.7,1)):
        bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=20,v_segments=10,radius=1.0)
        for v in bm.verts: v.co=Vector((c[0]+v.co.x*r*sq[0],c[1]+v.co.y*r*sq[1],c[2]+v.co.z*r*sq[2]))
        me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
        return _link(bpy.data.objects.new(name,me),bone)
    _K=_E('NRIM','0.0005'); _BK=Vector((0,0.0012,0))
    def _path(zb,drop,p,off,n=96):
        th=np.linspace(-np.pi,np.pi,n,endpoint=False)
        return [_hit(zb-drop*((1+np.cos(t))/2)**p,t,off) for t in th]
    def _chain(P,r,name,bone,closed=True):
        _tube(P,r,_gold,name,bone,closed=closed); _tube([q+_BK for q in P],r+_K,_ink,name+'_rim',bone,closed=closed)
    zb=_nc.z+_E('NZB','0.030')
    if _NW=='fine':
        _chain(_path(zb,_E('NDROP','0.045'),1.6,0.0030),0.0010,'Host.V62_neck_chain','spine01')
    elif _NW=='pendant':
        P=_path(zb,_E('NDROP','0.066'),1.8,0.0030); _chain(P,0.0010,'Host.V62_neck_chain','spine01')
        f=P[len(P)//2]; bail=f+Vector((0,-0.001,-0.003)); _sph(bail,0.0018,_gold,'Host.V62_bail','spine01'); _sph(bail+_BK,0.0018+_K,_ink,'Host.V62_bail_rim','spine01')
        c=f+Vector((0,-0.0015,-0.013)); _sph(c,0.0065,_gold,'Host.V62_pendant','spine01',(1,0.45,1.45)); _sph(c+_BK,0.0065+_K*1.4,_ink,'Host.V62_pendant_rim','spine01',(1,0.45,1.42))
        _sph(c+Vector((-0.0022,-0.003,0.003)),0.0016,_mat('V62_GOLD_HI',(1.0,0.9,0.6)),'Host.V62_pendant_hi','spine01')
    elif _NW=='pearls':
        pr=_E('PR','0.0036'); P=_path(zb,_E('NDROP','0.045'),1.5,pr+0.0015,400)
        L=np.cumsum([0]+[(P[i+1]-P[i]).length for i in range(len(P)-1)]); pm=_mat('V62_PEARL',(0.95,0.92,0.85)); hi=bpy.data.materials.get('LINEART_WHITE') or pm
        k=0
        for s in np.arange(0,L[-1],pr*2.05):
            i=int(np.searchsorted(L,s)); i=min(i,len(P)-1); q=P[i]
            if q.y>_nc.y+0.01: continue
            _sph(q,pr,pm,'Host.V62_pearl_%03d'%k,'spine01',(1,1,1)); _sph(q+_BK*1.2,pr+_K,_ink,'Host.V62_pearl_rim_%03d'%k,'spine01',(1,1,1))
            _sph(q+Vector((-pr*0.35,-pr*0.8,pr*0.35)),pr*0.25,hi,'Host.V62_pearl_hi_%03d'%k,'spine01',(1,1,1)); k+=1
    elif _NW=='choker':
        zc=_nc.z+_E('CHZ','0.035'); hw=_E('CHW','0.006'); vel=_mat('V62_VELVET',(0.035,0.03,0.035))
        th=np.linspace(-np.pi,np.pi,96,endpoint=False)
        bm=bmesh.new(); T=[bm.verts.new(_hit(zc+hw,t,0.0022)) for t in th]; B=[bm.verts.new(_hit(zc-hw,t,0.0022)) for t in th]
        for i in range(len(th)): j=(i+1)%len(th); bm.faces.new((T[i],T[j],B[j],B[i]))
        me=bpy.data.meshes.new('V62_choker'); bm.to_mesh(me); bm.free(); me.materials.append(vel); _link(bpy.data.objects.new('Host.V62_choker',me),'neck01')
        f=_hit(zc-hw,0,0.0035); _tube([f+Vector((0,0,0.0015)),f+Vector((0,0,-0.004))],0.0007,_gold,'Host.V62_choker_link','neck01')
        c=f+Vector((0,-0.0008,-0.0085)); _sph(c,0.0038,_gold,'Host.V62_choker_charm','neck01',(1,0.5,1)); _sph(c+_BK,0.0038+_K,_ink,'Host.V62_choker_charm_rim','neck01',(1,0.5,1))
    elif _NW=='scarf':
        silk=_mat('V62_SILK',tuple(_E(k,d) for k,d in (('SCR','0.72'),('SCG','0.20'),('SCB','0.15'))))
        silk2=_mat('V62_SILK_SH',tuple(_E(k,d)*0.72 for k,d in (('SCR','0.72'),('SCG','0.20'),('SCB','0.15'))))
        zc=_nc.z+_E('SCZ','0.030'); hw=_E('SCW','0.0085'); th=np.linspace(-np.pi,np.pi,96,endpoint=False)
        bm=bmesh.new(); T=[bm.verts.new(_hit(zc+hw+0.004*np.cos(t)*0,t,0.004)) for t in th]; B=[bm.verts.new(_hit(zc-hw-0.006*((1+np.cos(t))/2)**2,t,0.005)) for t in th]
        for i in range(len(th)): j=(i+1)%len(th); bm.faces.new((T[i],T[j],B[j],B[i]))
        me=bpy.data.meshes.new('V62_scarf_band'); bm.to_mesh(me); bm.free(); me.materials.append(silk); _link(bpy.data.objects.new('Host.V62_scarf_band',me),'neck01')
        _tube([q.co if hasattr(q,'co') else q for q in [_hit(zc+hw,t,0.0045) for t in th]],0.0009,_ink,'Host.V62_scarf_top','neck01',closed=True)
        _tube([_hit(zc-hw-0.006*((1+np.cos(t))/2)**2,t,0.0055) for t in th],0.0009,_ink,'Host.V62_scarf_bot','neck01',closed=True)
        for fi,t0 in enumerate(np.linspace(-0.8,0.3,6)):
            _tube([_hit(zc+hw*(0.8-1.6*u),t0+0.12*u,0.0052) for u in np.linspace(0,1,6)],0.00045,_ink,'Host.V62_scarf_fold%d'%fi,'neck01')
        ka=_E('SKA','0.55'); kc=_hit(zc-hw*0.3,ka,0.009)
        _sph(kc,0.011,silk,'Host.V62_scarf_knot','neck01',(1,0.75,0.85)); _sph(kc+_BK,0.011+_K*1.6,_ink,'Host.V62_scarf_knot_rim','neck01',(1,0.75,0.84))
        for tn,(dx,L) in enumerate(((0.012,0.05),(-0.004,0.042))):
            P=[]; W=[]
            for s in np.linspace(0,1,14):
                z=kc.z-0.006-L*s; t=ka+dx*s*25
                P.append(_hit(z,t,0.006+0.002*tn)); W.append(0.009*(1-s)+0.0012)
            bm=bmesh.new(); lr=[]
            for p,w in zip(P,W):
                lr.append((bm.verts.new(p+Vector((-w,0,0))),bm.verts.new(p+Vector((w,0,0)))))
            for i in range(len(lr)-1): bm.faces.new((lr[i][0],lr[i][1],lr[i+1][1],lr[i+1][0]))
            me=bpy.data.meshes.new('V62_scarf_tail%d'%tn); bm.to_mesh(me); bm.free(); me.materials.append(silk if tn==0 else silk2)
            _link(bpy.data.objects.new('Host.V62_scarf_tail%d'%tn,me),'neck01')
            ed=[p+Vector((-w,-0.0006,0)) for p,w in zip(P,W)]+[P[-1]+Vector((0,-0.0006,-0.003))]+[p+Vector((w,-0.0006,0)) for p,w in reversed(list(zip(P,W)))]
            _tube(ed,0.0008,_ink,'Host.V62_scarf_tail_ink%d'%tn,'neck01')
            _tube([p+Vector((0,-0.0007,0)) for p in P[2:-3]],0.0004,_ink,'Host.V62_scarf_tail_fold%d'%tn,'neck01')
    print('NECK',_NW,'zb',round(zb,3),'objs',len([o for o in bpy.data.objects if o.name.startswith('Host.V62_')]))
