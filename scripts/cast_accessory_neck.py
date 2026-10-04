import bpy,os,bmesh,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
_E=lambda k,d: float(os.environ.get(k,d))
_NW=os.environ.get('NECK','')
if _NW and _NW != 'none':
    _r=bpy.data.objects['Host.rig']; _b=bpy.data.objects['Host.body']; _dr=bpy.data.objects[os.environ.get('DOBJ','Host.mindfront_f_dress_01')]
    _dg=bpy.context.evaluated_depsgraph_get()
    _skin=next((o for o in bpy.data.objects if o.name.startswith('Cast accessory skin target V17') and o.type=='MESH'),_b)
    _T=[BVHTree.FromObject(o.evaluated_get(_dg),_dg) for o in (_skin,_dr)]
    _Mi=[o.matrix_world for o in (_skin,_dr)]
    _nb=_r.pose.bones['neck01']; _nc=_r.matrix_world@_nb.head; _nt=_r.matrix_world@_nb.tail
    def _hit(z,th,off):
        d=Vector((np.sin(th),-np.cos(th),0));a=_nc+(_nt-_nc)*((z-_nc.z)/max(_nt.z-_nc.z,1e-6));a=Vector((a.x,a.y,z))
        hits=[]
        # Shoot outwards from the neck centre. An outside-in ray can hit the
        # far shoulder before the neck and make jewellery bridge open space.
        for t,M in zip(_T,_Mi):
            Mi=M.inverted();p,n,i,dist=t.ray_cast(Mi@a,(Mi.to_3x3()@d).normalized(),.17)
            hits.append(M@p if p is not None else None)
        best=hits[0]
        if hits[1] is not None and (best is None or 0<(hits[1]-best).dot(d)<.015):best=hits[1]
        if best is None:raise RuntimeError('NECK_SURFACE_FIT_MISSING: '+str((z,th)))
        return best+d*off
    from cast_accessory_finish import finish_material,make_tube,fit_neck_attachment
    def _mat(name,rgb):
        # Original colours are linear; keep their authored palette.
        srgb=[12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055 for c in rgb]
        hx=''.join('%02X'%max(0,min(255,round(c*255))) for c in srgb)
        kind='pearl' if 'PEARL' in name else 'silk' if 'SILK' in name else 'velvet' if 'VELVET' in name else 'metal'
        return finish_material('V17_'+name,hx,kind)
    _ink=bpy.data.materials['V59_INK'] if 'V59_INK' in bpy.data.materials else bpy.data.materials['LINEART_EYE_INK']
    _gold=finish_material('V17_NECK_GOLD','CBA654','metal')
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
        for polygon in me.polygons: polygon.use_smooth=True
        return _link(bpy.data.objects.new(name,me),bone)
    def _sph(c,r,mat,name,bone,sq=(1,0.7,1)):
        bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=20,v_segments=10,radius=1.0)
        for v in bm.verts: v.co=Vector((c[0]+v.co.x*r*sq[0],c[1]+v.co.y*r*sq[1],c[2]+v.co.z*r*sq[2]))
        me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
        for polygon in me.polygons: polygon.use_smooth=True
        return _link(bpy.data.objects.new(name,me),bone)
    _K=_E('NRIM','0.00015'); _BK=Vector((0,0.0012,0))
    def _path(zb,drop,p,off,n=96):
        th=np.linspace(-np.pi,np.pi,n,endpoint=False)
        return [_hit(zb-drop*((1+np.cos(t))/2)**p,t,off) for t in th]
    def _chain(P,r,name,bone,closed=True):
        # Interlocking oval links sampled by arc length, never spaced by vertex count.
        Q=P+[P[0]] if closed else P
        lengths=np.cumsum([0]+[(Q[i+1]-Q[i]).length for i in range(len(Q)-1)])
        count=max(16,round(lengths[-1]/.00215));step=lengths[-1]/count
        all_verts=[];all_faces=[]
        for i in range(count):
            distance=i*step;k=min(len(Q)-2,max(0,int(np.searchsorted(lengths,distance)-1)))
            t=(distance-lengths[k])/max(1e-8,lengths[k+1]-lengths[k]);center=Q[k].lerp(Q[k+1],t)
            tangent=(Q[k+1]-Q[k]).normalized();normal=Vector((0,0,1))-tangent*tangent.z
            if normal.length<1e-6:normal=Vector((1,0,0))-tangent*tangent.x
            normal.normalize();cross=tangent.cross(normal).normalized();angle=np.pi/2*(i%2)+.25
            normal=normal*np.cos(angle)+cross*np.sin(angle)
            points=[center+tangent*np.cos(q)*.0014+normal*np.sin(q)*.00080 for q in np.linspace(0,2*np.pi,20,endpoint=False)]
            ob=make_tube(name+'_link',points,.00024,_gold,closed=True,collection=_col[0],sides=8)
            offset=len(all_verts);all_verts.extend(v.co.copy() for v in ob.data.vertices);all_faces.extend(tuple(offset+v for v in poly.vertices) for poly in ob.data.polygons)
            mesh=ob.data;bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(all_verts,[],all_faces);mesh.materials.append(_gold);mesh.update()
        for poly in mesh.polygons:poly.use_smooth=True
        _link(bpy.data.objects.new(name,mesh),bone)
    zb=_nc.z+_E('NZB','0.030')
    if _NW=='fine':
        _chain(_path(zb,_E('NDROP','0.045'),1.6,0.0030),0.0010,'Host.V62_neck_chain','spine01')
    elif _NW=='pendant':
        P=_path(zb,_E('NDROP','0.066'),1.8,0.0030); _chain(P,0.0010,'Host.V62_neck_chain','spine01')
        f=P[len(P)//2]; bail=_hit(f.z-.003,0,.0045); _sph(bail,0.0018,_gold,'Host.V62_bail','spine01'); _sph(bail+_BK,0.0018+_K,_ink,'Host.V62_bail_rim','spine01')
        c=_hit(f.z-.013,0,.0065); _sph(c,0.0065,_gold,'Host.V62_pendant','spine01',(1,0.45,1.45)); _sph(c+_BK,0.0065+_K*1.4,_ink,'Host.V62_pendant_rim','spine01',(1,0.45,1.42))
        _setting=[c+Vector((np.cos(q)*.0065,-.0032,np.sin(q)*.0094)) for q in np.linspace(0,2*np.pi,80,endpoint=False)]
        _tube(_setting,.00035,finish_material('V17_SETTING_EDGE','E2C781','metal'),'Host.V62_pendant_setting','spine01',n=12,closed=True)
        _engraving=[c+Vector((np.cos(q)*.0049,-.00215,np.sin(q)*.0072)) for q in np.linspace(0,2*np.pi,80,endpoint=False)]
        _tube(_engraving,.00014,finish_material('V17_GOLD_ETCH','9A7B36','metal'),'Host.V62_pendant_etch','spine01',n=8,closed=True)
    elif _NW=='pearls':
        pr=_E('PR','0.0036'); P=_path(zb,_E('NDROP','0.045'),1.5,pr+0.0020,800)
        L=np.cumsum([0]+[(P[i+1]-P[i]).length for i in range(len(P)-1)]); pm=_mat('V62_PEARL',(0.95,0.92,0.85)); hi=bpy.data.materials.get('LINEART_WHITE') or pm
        k=0
        for s in np.arange(0,L[-1],pr*2.10):
            i=int(np.searchsorted(L,s)); i=min(i,len(P)-1); q=P[i]
            if q.y>_nc.y+0.01: continue
            _sph(q,pr,pm,'Host.V62_pearl_%03d'%k,'spine01',(1,1,1)); None
            k+=1
    elif _NW=='choker':
        zc=_nc.z+_E('CHZ','0.035'); hw=_E('CHW','0.005'); vel=finish_material('V17_VELVET','211D25','velvet')
        th=np.linspace(-np.pi,np.pi,96,endpoint=False)
        bm=bmesh.new(); T=[bm.verts.new(_hit(zc+hw,t,0.0022)) for t in th]; B=[bm.verts.new(_hit(zc-hw,t,0.0022)) for t in th]
        for i in range(len(th)): j=(i+1)%len(th); bm.faces.new((T[i],T[j],B[j],B[i]))
        me=bpy.data.meshes.new('V62_choker'); bm.to_mesh(me); bm.free(); me.materials.append(vel); _link(bpy.data.objects.new('Host.V62_choker',me),'neck01')
        f=_hit(zc-hw,0,0.0035); _tube([f+Vector((0,0,0.0015)),f+Vector((0,0,-0.004))],0.0007,_gold,'Host.V62_choker_link','neck01')
        c=_hit(f.z-.0085,0,.0050); _sph(c,0.0038,_gold,'Host.V62_choker_charm','neck01',(1,0.5,1)); _sph(c+_BK,0.0038+_K,_ink,'Host.V62_choker_charm_rim','neck01',(1,0.5,1))
    elif _NW=='scarf':
        silk=_mat('V62_SILK',tuple(_E(k,d) for k,d in (('SCR','0.72'),('SCG','0.20'),('SCB','0.15'))))
        silk2=_mat('V62_SILK_SH',tuple(_E(k,d)*0.72 for k,d in (('SCR','0.72'),('SCG','0.20'),('SCB','0.15'))))
        zc=_nc.z+_E('SCZ','0.030'); hw=_E('SCW','0.0085'); th=np.linspace(-np.pi,np.pi,96,endpoint=False)
        bm=bmesh.new(); strips=[]; V=10
        def silk_surface(t,u):
            z=zc+hw*(1-2*u)-.006*((1+np.cos(t))/2)**2*u
            ripple=.0008*np.sin(t*8+u*1.5)*np.sin(np.pi*u)+.00035*np.sin(t*3)
            return _hit(z,t,.004+.001*u+ripple)
        for t in th:strips.append([bm.verts.new(silk_surface(t,j/V)) for j in range(V+1)])
        for i in range(len(th)):
            k=(i+1)%len(th)
            for j in range(V):bm.faces.new((strips[i][j],strips[k][j],strips[k][j+1],strips[i][j+1]))
        me=bpy.data.meshes.new('V62_scarf_band');bm.to_mesh(me);bm.free();me.materials.append(silk);_link(bpy.data.objects.new('Host.V62_scarf_band',me),'neck01')
        _tube([q.co if hasattr(q,'co') else q for q in [_hit(zc+hw,t,0.0045) for t in th]],0.00030,_ink,'Host.V62_scarf_top','neck01',closed=True)
        _tube([_hit(zc-hw-0.006*((1+np.cos(t))/2)**2,t,0.0055) for t in th],0.00030,_ink,'Host.V62_scarf_bot','neck01',closed=True)
        for fi,t0 in enumerate(np.linspace(-0.85,0.28,5)):
            _tube([silk_surface(t0+.06*np.sin(np.pi*u),u)+Vector((0,-.00035,0)) for u in np.linspace(.13,.83,16)],0.00016,silk2,'Host.V62_scarf_fold%d'%fi,'neck01')
        ka=_E('SKA','0.55'); kc=_hit(zc-hw*0.3,ka,0.009)
        _sph(kc,.009,silk,'Host.V62_scarf_knot','neck01',(1.18,.73,.74))
        for fi,shift in enumerate([-.0030,.0017]):
            fold=[kc+Vector((shift+.0023*np.sin(q),-.0066*np.sin(q),.0066*np.cos(q))) for q in np.linspace(.22,np.pi-.22,32)]
            _tube(fold,.00019,silk2,'Host.V62_scarf_knot_fold%d'%fi,'neck01')
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
            _tube(ed,0.00030,_ink,'Host.V62_scarf_tail_ink%d'%tn,'neck01')
            _tube([p+Vector((0,-0.0007,0)) for p in P[2:-3]],0.00016,silk2,'Host.V62_scarf_tail_fold%d'%tn,'neck01')
    print('NECK',_NW,'zb',round(zb,3),'objs',len([o for o in bpy.data.objects if o.name.startswith('Host.V62_')]))


    for _o in [o for o in bpy.data.objects if o.name.startswith('Host.V62_')]:
        if _o.type=='MESH':
            for _pl in _o.data.polygons:_pl.use_smooth=True
            if _o.name.startswith(('Host.V62_choker','Host.V62_scarf')) and any(k in _o.name for k in ('band','tail','choker')) and not any(k in _o.name for k in ('ink','fold','link','charm')):
                solid=_o.modifiers.new('V17 fabric edge thickness','SOLIDIFY');solid.thickness=.0004;solid.offset=0
                smooth=_o.modifiers.new('V17 soft fabric edge','BEVEL');smooth.width=.00025;smooth.segments=3
    fit_neck_attachment([o for o in bpy.data.objects if o.name.startswith('Host.V62_')],_r)
