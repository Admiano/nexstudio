import bpy,bmesh,os,numpy as np
from mathutils import Vector,Matrix
_W=os.environ.get('WATCH','')
if _W:
    _E=lambda k,d: float(os.environ.get(k,d))
    S=bpy.context.scene; _r=bpy.data.objects['Host.rig']; _b=bpy.data.objects['Host.body']; _sd=os.environ.get('WSIDE','L')
    _pb=_r.pose.bones; _pbn='lowerarm02.'+_sd if 'lowerarm02.'+_sd in _pb else 'lowerarm01.'+_sd
    _r.data.pose_position='REST'; bpy.context.view_layer.update()
    _M=_r.matrix_world; _wr=_M@_r.data.bones['wrist.'+_sd].head_local; _el=_M@_r.data.bones['lowerarm01.'+_sd].head_local
    _a=(_wr-_el).normalized()
    _lat=Vector((1 if (_wr.x-(_M@_r.data.bones['spine05'].head_local).x)>0 else -1,0,0))
    _d=Vector((0,-1,0))*_E('WFWD','1.0')+_lat*_E('WLAT','0.35'); _d=(_d-_a*_d.dot(_a)).normalized(); _e=_a.cross(_d).normalized()
    from mathutils.bvhtree import BVHTree
    _dg=bpy.context.evaluated_depsgraph_get(); _vs=[]; _fs=[]
    _GK=('shirt','polo','sweat','sweater','tshirt','t-shirt','jacket')
    _vs_s=[]; _fs_s=[]; _vs_g=[]; _fs_g=[]
    for o in [o for o in bpy.data.objects if o.name.startswith('Host.') and o.type=='MESH' and not o.hide_render and (o==_b or any(k in o.name for k in _GK))]:
        ev=o.evaluated_get(_dg); m=ev.to_mesh(); mw=o.matrix_world; n0=len(_vs)
        _vs+= [mw@v.co for v in m.vertices]; _fs+=[tuple(i+n0 for i in pl.vertices) for pl in m.polygons]
        _v2,_f2=(_vs_s,_fs_s) if o==_b else (_vs_g,_fs_g); n2=len(_v2)
        _v2+=[mw@v.co for v in m.vertices]; _f2+=[tuple(i+n2 for i in pl.vertices) for pl in m.polygons]; ev.to_mesh_clear()
    _bt=BVHTree.FromPolygons(_vs,_fs); _bs=BVHTree.FromPolygons(_vs_s,_fs_s); _bg=BVHTree.FromPolygons(_vs_g,_fs_g) if _fs_g else None
    def _covered(t):
        if _bg is None: return 0
        Cc=_wr-_a*t; n=0
        for k in range(24):
            q=-1.05+2.1*k/23; dr=_d*np.cos(q)+_e*np.sin(q)
            hs=_bs.ray_cast(Cc+dr*0.15,-dr,0.15); hg=_bg.ray_cast(Cc+dr*0.15,-dr,0.15)
            rs=0.15-hs[3] if hs[0] is not None else 0.0; rg=0.15-hg[3] if hg[0] is not None else 0.0
            if rg>rs+0.0004: n+=1
        return n
    _seat=_E('WBACK','0.028'); _sleeve=_covered(_seat)>12
    if _sleeve:
        _cuff=None
        for _t in np.arange(_seat-0.006,-0.05,-0.006):
            if _covered(_t)<=4: _cuff=_t; break
        _seat=(_cuff-_E('WSEATM','0.014')) if _cuff is not None else -0.04
    _C0=_wr-_a*_seat
    print('WATCH seat t=%.3f sleeve=%s cuff=%s'%(_seat,_sleeve,_cuff if _sleeve else '-'))
    C=Vector(_C0); NB=72; R=np.full(NB,np.nan)
    for k in range(NB):
        q=-np.pi+2*np.pi*k/NB; dr=_d*np.cos(q)+_e*np.sin(q); hit=_bt.ray_cast(C+dr*0.09,-dr,0.09)
        if hit[0] is not None: R[k]=0.09-hit[3]
    ok=~np.isnan(R); idx=np.arange(NB); R=np.interp(idx,idx[ok],R[ok],period=NB)
    R=np.convolve(np.r_[R[-3:],R,R[:3]],np.ones(5)/5,'same')[3:-3]+_E('WCLR','0.0012')
    print('WATCH section hits',int(ok.sum()),'r min/max %.4f %.4f'%(R.min(),R.max()),'bone',_pbn)
    rf=lambda t: float(np.interp(((t+np.pi)/(2*np.pi)*NB)%NB,np.r_[idx,NB],np.r_[R,R[0]]))
    def mat(n,hexc,em=1.0):
        m=bpy.data.materials.get('W_'+n)
        if m: return m
        m=bpy.data.materials.new('W_'+n); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
        c=[int(hexc[i:i+2],16)/255 for i in (0,2,4)]; c=[x**2.2 for x in c]
        e=nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value=(*c,1); e.inputs['Strength'].default_value=em
        o=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0],o.inputs[0]); return m
    parts=[]
    def obj(name,bm,m):
        me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
        for p in me.polygons: p.use_smooth=True
        ob=bpy.data.objects.new('Host.watch_'+name,me)
        for c in _b.users_collection: c.objects.link(ob)
        ff=bpy.data.collections.get('FACE_FINE')
        if ff and os.environ.get('WLINES','1')=='1' and name.split('_')[0] in ('strap','case','bezel','glass','dial','band','lcd','sub0','sub1','sub2'): ff.objects.link(ob)
        parts.append(ob); return ob
    FR=Matrix((_d,_e,_a)).transposed()
    _Rt=Matrix.Rotation(np.radians(_E('WTILT','10.0')),3,_e)
    _N={'d':_Rt@_d,'e':_Rt@_e,'a':_Rt@_a}; FRt=(_Rt@FR)
    def L(x,y,z): return C+_d*x+_e*y+_a*z
    def Lt(x,y,z): return C+(_Rt@(_d*x+_e*y+_a*z))
    def band(name,w,t,m,z0=0.0,seg=None):
        bm=bmesh.new(); n=64; rows=[]
        for i in range(n):
            q=-np.pi+2*np.pi*i/n; r=rf(q); u=np.cos(q); v=np.sin(q)
            rows.append([bm.verts.new(L(u*rr_,v*rr_,z0+s)) for rr_,s in ((r,-w/2),(r+t,-w/2),(r+t,w/2),(r,w/2))])
        for i in range(n):
            A_,B_=rows[i],rows[(i+1)%n]
            for j in range(4): bm.faces.new((A_[j],B_[j],B_[(j+1)%4],A_[(j+1)%4]))
        return obj(name,bm,m)
    r0=rf(0.0); T=_E('WST','0.0028')
    base=r0+T
    def disk(name,rad,h,m,x0,y=0.0,z=0.0,seg=40,ax='d'):
        bm=bmesh.new(); bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=rad,radius2=rad,depth=h)
        nrm=_N[ax]; q=Vector((0,0,1)).rotation_difference(nrm).to_matrix().to_4x4()
        bmesh.ops.transform(bm,matrix=Matrix.Translation(Lt(x0,y,z))@q,verts=bm.verts); return obj(name,bm,m)
    def box(name,sx,sy,sz,m,x0,y=0.0,z=0.0,rot=0.0,bev=0.0):
        bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1.0)
        bmesh.ops.scale(bm,vec=(sx,sy,sz),verts=bm.verts)
        if bev>0: bmesh.ops.bevel(bm,geom=[e for e in bm.edges if abs(e.verts[0].co.z-e.verts[1].co.z)>1e-6],offset=bev,segments=4,affect='EDGES')
        Rz=Matrix.Rotation(rot,4,'X'); F4=FRt.to_4x4()
        bmesh.ops.transform(bm,matrix=Matrix.Translation(Lt(x0,y,z))@F4@Rz,verts=bm.verts); return obj(name,bm,m)
    def hand(name,ln,wd,ang,m,x0,h=0.0004):
        c,s=np.cos(ang),np.sin(ang)
        bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1.0); bmesh.ops.scale(bm,vec=(h,wd,ln),verts=bm.verts)
        bmesh.ops.translate(bm,vec=(0,0,ln/2),verts=bm.verts)
        Rot=Matrix.Rotation(ang,4,'X'); bmesh.ops.transform(bm,matrix=Matrix.Translation(Lt(x0,0,0))@FRt.to_4x4()@Rot,verts=bm.verts); return obj(name,bm,m)
    ink=mat('ink','141414')
    H12=np.pi
    if _W=='analog':
        band('strap',0.018,T,mat('strap_'+os.environ.get('WSC','6B4226'),os.environ.get('WSC','6B4226')))
        disk('case',0.0175,0.007,mat('steel','B8BCC2'),base+0.0035); disk('dial',0.0152,0.0006,mat('dial','F4F1EA'),base+0.0071)
        for k in range(12): hand('idx%d'%k,0.002,0.0007,H12+k*np.pi/6,ink,base+0.0074) if False else None
        for k in range(12):
            q=H12+k*np.pi/6; box('idx%d'%k,0.0004,0.0006,0.0022 if k%3==0 else 0.0012,ink,base+0.0075,-np.sin(q)*0.0128,np.cos(q)*0.0128,rot=q)
        hand('hr',0.0075,0.0011,H12-np.pi/3*1.0,ink,base+0.0078); hand('mn',0.0115,0.0008,H12+np.pi/3*1.2,ink,base+0.0081); disk('pin',0.0009,0.0012,ink,base+0.0082)
        disk('crown',0.0016,0.0028,mat('steel','B8BCC2'),base+0.0035,0,0.0185,ax='a')
    elif _W=='digital':
        band('strap',0.020,T*1.2,mat('resin','1E1F22'))
        box('case',0.009,0.030,0.034,mat('resin','1E1F22'),base+0.0045,bev=0.006)
        box('lcd',0.0008,0.020,0.016,mat('lcd','A9B3A0'),base+0.0092,bev=0.0015)
        for k,(y,z) in enumerate(((-0.0055,0.0),(-0.002,0.0),(0.002,0.0),(0.0055,0.0))): box('seg%d'%k,0.0004,0.0022,0.0075,mat('lcdink','2A2E28'),base+0.0097,y,z,bev=0.0003)
        box('bar',0.0004,0.016,0.0012,mat('accent',os.environ.get('WAC','D8452B')),base+0.0097,0,-0.0068)
        for y in (-0.016,0.016): box('btn%d'%(y>0),0.003,0.003,0.004,mat('resin','1E1F22'),base+0.004,y,0.008)
    elif _W=='smart':
        band('strap',0.020,T,mat('band_'+os.environ.get('WSC','3F5F7A'),os.environ.get('WSC','3F5F7A')))
        box('case',0.0085,0.034,0.040,mat('alu','9EA3A8'),base+0.0042,bev=0.0075)
        box('glass',0.0008,0.030,0.036,mat('glass','0E1014'),base+0.0086,bev=0.0065)
        box('ring1',0.0004,0.0022,0.012,mat('fit','E0463A'),base+0.0092,-0.004,0.0,rot=0.0,bev=0.0008)
        box('ring2',0.0004,0.0022,0.009,mat('fit2','7ED957'),base+0.0092,0.0,0.0,bev=0.0008)
        box('ring3',0.0004,0.0022,0.006,mat('fit3','3AB8E8'),base+0.0092,0.004,0.0,bev=0.0008)
        disk('crown',0.0017,0.003,mat('alu','9EA3A8'),base+0.004,0,0.021,ax='a')
    elif _W=='chrono':
        band('strap',0.020,T,mat('steel2','A7ABB0'))
        for k in range(9): band('link%d'%k,0.0004,T+0.0003,ink,-0.008+k*0.002) if False else None
        disk('case',0.0205,0.009,mat('steel2','A7ABB0'),base+0.0045); disk('bezel',0.0198,0.0012,mat('bezel','1B1C20'),base+0.0094)
        disk('dial',0.0158,0.0006,mat('dialb','22252B'),base+0.0098)
        for k,(y,z) in enumerate(((0.0,-0.0068),(-0.0068,0.0),(0.0068,0.0))): disk('sub%d'%k,0.0030,0.0004,mat('sub','5A5E66'),base+0.0102,y,z)
        hand('hr',0.008,0.0012,H12-np.pi/3,mat('lume','F2F0E6'),base+0.0106); hand('mn',0.012,0.0009,H12+np.pi/2.5,mat('lume','F2F0E6'),base+0.0109)
        hand('sec',0.013,0.0004,H12+np.pi*0.9,mat('sech',os.environ.get('WAC','D8452B')),base+0.0112); disk('pin',0.001,0.0014,ink,base+0.0112)
        for z in (-0.009,0.009): disk('push%d'%(z>0),0.0014,0.003,mat('steel2','A7ABB0'),base+0.0045,0,0.0205*np.sign(z)*0.0+z*0.0+0.0 if False else z,ax='a') if False else None
        disk('crown',0.0019,0.0032,mat('steel2','A7ABB0'),base+0.0045,0,0.0215,ax='a')
        for y in (-0.011,0.011): disk('push%d'%(y>0),0.0013,0.003,mat('steel2','A7ABB0'),base+0.0045,y,0.0185,ax='a')
    elif _W=='dress':
        band('strap',0.013,T*0.8,mat('lthr_'+os.environ.get('WSC','1A1512'),os.environ.get('WSC','1A1512')))
        disk('case',0.0165,0.0045,mat('rose','C9967A'),base+0.0022); disk('dial',0.0150,0.0004,mat('cream','F1E9D8'),base+0.0045)
        for k in (0,3,6,9):
            q=H12+k*np.pi/6; box('idx%d'%k,0.0003,0.0005,0.0018,mat('rose','C9967A'),base+0.0048,-np.sin(q)*0.0125,np.cos(q)*0.0125,rot=q)
        hand('hr',0.0068,0.0007,H12-np.pi/3,mat('rose','C9967A'),base+0.005); hand('mn',0.0108,0.0005,H12+np.pi/3*1.2,mat('rose','C9967A'),base+0.0052)
        disk('crown',0.0012,0.0022,mat('rose','C9967A'),base+0.0022,0,0.0172,ax='a')
    bpy.context.view_layer.update()
    pbn=_pbn
    for ob in parts:
        mw=ob.matrix_world.copy(); ob.parent=_r; ob.parent_type='BONE'; ob.parent_bone=pbn; bpy.context.view_layer.update(); ob.matrix_world=mw
    _r.data.pose_position='POSE'; bpy.context.view_layer.update()
    print('WATCH',_W,'parts',len(parts),'bone',pbn)
