import bpy,bmesh,os,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
_E=lambda k,d: float(os.environ.get(k,d))
S=bpy.context.scene
g=bpy.data.objects[os.environ.get('DOBJ','Host.mindfront_f_dress_01')]
rig=bpy.data.objects['Host.rig']; body=bpy.data.objects['Host.body']
_lin=lambda c:(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4)
m=g.data.materials[0]
if m.name=='PEEPS_V2_MUSTARD_JACKET': m=m.copy(); g.data.materials[0]=m
_dc=os.environ.get('DCOL','')
C=np.array([_lin(int(_dc.lstrip('#')[i:i+2],16)/255) for i in (0,2,4)]) if _dc else np.array(list(m.node_tree.nodes['Mix'].inputs[6].default_value)[:3])
_bq=bmesh.new(); _bq.from_mesh(g.data); _bad=[]
for f in _bq.faces:
    vs=[v.co for v in f.verts]; n=f.normal; k=len(vs)
    if k>4 or any(((vs[(i+1)%k]-vs[i]).cross(vs[(i+2)%k]-vs[(i+1)%k])).dot(n)<=1e-12 for i in range(k)): _bad.append(f)
if _bad: bmesh.ops.triangulate(_bq,faces=_bad); _bq.to_mesh(g.data); g.data.update()
_bq.free(); print('DART concave faces triangulated',len(_bad))
F0=S.frame_current; S.frame_set(1)
ssm=[x for x in g.modifiers if x.type=='SUBSURF']
for x in ssm: x.show_viewport=False
dg=bpy.context.evaluated_depsgraph_get(); ge=g.evaluated_get(dg); me=ge.to_mesh()
P=np.array([g.matrix_world@v.co for v in me.vertices]); N=np.array([(g.matrix_world.to_3x3()@v.normal).normalized() for v in me.vertices])
bt=BVHTree.FromPolygons([tuple(p) for p in P],[tuple(p.vertices) for p in me.polygons]); ge.to_mesh_clear()
rs=np.random.RandomState(7); D=rs.normal(size=(14,3)); D/=np.linalg.norm(D,axis=1)[:,None]
ao=np.ones(len(P)); R=_E('AOR','0.08')
for i,(p,n) in enumerate(zip(P,N)):
    h=0.0; nv=Vector(n)
    for d in D:
        dd=Vector(d) if Vector(d).dot(nv)>0 else -Vector(d)
        dd=(dd+nv).normalized()
        if bt.ray_cast(Vector(p)+nv*0.003,dd,R)[0] is not None: h+=1
    ao[i]=1-h/len(D)
at=g.data.attributes.get('dao') or g.data.attributes.new('dao','FLOAT','POINT')
at.data.foreach_set('value',ao.astype(np.float32))
for x in ssm: x.show_viewport=True
print('DART ao mean',round(ao.mean(),3),'min',round(ao.min(),3))
nt=m.node_tree; nt.nodes.clear(); L=nt.links
def nd(t,**k):
    n=nt.nodes.new(t)
    for a,b in k.items(): setattr(n,a,b)
    return n
def mix(a,b,f,bt='MIX'):
    n=nd('ShaderNodeMix',data_type='RGBA',blend_type=bt)
    for s,v in ((6,a),(7,b)):
        if isinstance(v,bpy.types.NodeSocket): L.new(v,n.inputs[s])
        else: n.inputs[s].default_value=(*v,1)
    if isinstance(f,bpy.types.NodeSocket): L.new(f,n.inputs[0])
    else: n.inputs[0].default_value=f
    return n.outputs[2]
def mr(v,a,b,c=0.0,d=1.0):
    n=nd('ShaderNodeMapRange'); L.new(v,n.inputs[0])
    for i,x in zip((1,2,3,4),(a,b,c,d)): n.inputs[i].default_value=x
    return n.outputs[0]
lv=np.array([_E('LVX','-0.35'),_E('LVY','-0.75'),_E('LVZ','0.56')]); lv/=np.linalg.norm(lv)
geo=nd('ShaderNodeNewGeometry'); vm=nd('ShaderNodeVectorMath',operation='DOT_PRODUCT'); L.new(geo.outputs['Normal'],vm.inputs[0]); vm.inputs[1].default_value=tuple(lv)
dot=vm.outputs['Value']
sh=C*np.array([_E('DSR','0.52'),_E('DSG','0.54'),_E('DSB','0.64')]); hi=np.clip(C*_E('DHI','1.45'),0,1); deep=C*_E('DDP','0.34')
c=mix(tuple(sh),tuple(C),mr(dot,_E('DL0','-0.22'),_E('DL1','0.10')))
c=mix(c,tuple(hi),mr(dot,_E('DH0','0.50'),_E('DH1','0.85'),0,_E('DHF','0.35')))
lw=nd('ShaderNodeLayerWeight'); lw.inputs[0].default_value=0.5
c=mix(c,tuple(sh),mr(lw.outputs['Facing'],0.55,1.0,0,_E('DEF','0.45')))
aa=nd('ShaderNodeAttribute',attribute_name='dao')
c=mix(c,tuple(deep),mr(aa.outputs['Fac'],_E('DA0','0.45'),1.0,_E('DAF','0.75'),0))
em=nd('ShaderNodeEmission'); L.new(c,em.inputs['Color']); out=nd('ShaderNodeOutputMaterial'); L.new(em.outputs[0],out.inputs['Surface'])
# ---- line art ribbons on evaluated (subsurf) surface ----
dg=bpy.context.evaluated_depsgraph_get(); ge=g.evaluated_get(dg)
bm=bmesh.new(); bm.from_object(g,dg); bm.transform(g.matrix_world); bm.verts.ensure_lookup_table(); bm.normal_update()
bv=BVHTree.FromBMesh(bm)
strokes=[]  # (points, normals, width, taper, material)
def smooth(a,k=3):
    a=np.array(a)
    for _ in range(k): a[1:-1]=0.25*a[:-2]+0.5*a[1:-1]+0.25*a[2:]
    return a
def resamp(pts,step,closed=False):
    pts=np.array(pts).reshape(-1,3)
    if len(pts)<2: return pts
    if closed: pts=np.vstack([pts,pts[:1]])
    d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
    n=max(3,int(d[-1]/step)); t=np.linspace(0,d[-1],n)
    return np.array([np.interp(t,d,pts[:,k]) for k in range(3)]).T
def onsurf(pts):
    P2=[];N2=[]
    for p in pts:
        q,n,_,_=bv.find_nearest(Vector(p))
        if q is None: continue
        P2.append(np.array(q)); N2.append(np.array(n))
    return np.array(P2),np.array(N2)
# boundary loops -> inset topstitch
be=[e for e in bm.edges if e.is_boundary]; adj={}
for e in be:
    a,b=e.verts; adj.setdefault(a.index,[]).append(b.index); adj.setdefault(b.index,[]).append(a.index)
seen=set(); loops=[]
for s in adj:
    if s in seen: continue
    lp=[s]; seen.add(s); cur=s
    while True:
        nx=[x for x in adj[cur] if x not in seen]
        if not nx: break
        cur=nx[0]; seen.add(cur); lp.append(cur)
    loops.append(lp)
INS=_E('DINS','0.013'); nst=0
for lp in loops:
    if len(lp)<12: continue
    pts=[]
    for vi in lp:
        v=bm.verts[vi]; d=Vector()
        for e in v.link_edges:
            if not e.is_boundary: d+=(e.other_vert(v).co-v.co).normalized()
        pts.append(np.array(v.co+(d.normalized()*INS if d.length>1e-6 else Vector())))
    ln=sum(np.linalg.norm(np.diff(np.array(pts),axis=0),axis=1))
    if ln<0.08: continue
    q=resamp(smooth(pts+pts[:1],4)[:-1],0.006,True); q,nn=onsurf(q)
    strokes.append((q,nn,_E('DSTW','0.0010'),False,1)); nst+=1
# designed folds/darts from pose landmarks
pb=rig.pose.bones; W=rig.matrix_world
J=lambda b,t=0:np.array(W@(pb[b].tail if t else pb[b].head))
cx=(J('upperleg01.L')[0]+J('upperleg01.R')[0])/2
zb=(J('breast.L',1)[2]+J('breast.R',1)[2])/2; zh=J('upperleg01.L')[2]; zk=J('lowerleg01.L')[2]
tg={x.index for x in body.vertex_groups if x.name.startswith(('spine','pelvis','breast'))}
bmw=body.evaluated_get(dg).to_mesh(); BP=np.array([body.matrix_world@v.co for v in bmw.vertices])
tor=np.array([sum(gg.weight for gg in v.groups if gg.group in tg)>0.6 for v in body.data.vertices]) if len(body.data.vertices)==len(BP) else np.ones(len(BP),bool)
body.evaluated_get(dg).to_mesh_clear()
def hw(z):
    sel=tor&(np.abs(BP[:,2]-z)<0.012)
    if z<zh-0.05 or sel.sum()<4:
        sel=(np.abs(BP[:,2]-z)<0.012)&(np.abs(BP[:,0]-cx)<0.24)
    return max(0.06,np.abs(BP[sel,0]-cx).max()) if sel.sum() else 0.15
hz=[p[2] for p in (np.array(v.co) for v in bm.verts)]; zhem=min(hz)+0.03
hj=abs(J('upperleg01.L')[0]-cx); zw=zh+_E('DZW','0.42')*(zb-zh)
_hz=[zhem-1,zk,zh,zw,zb,zb+1]; _hv=[1.55*hj,1.60*hj,1.85*hj,1.35*hj,1.55*hj,1.55*hj]
hw=lambda z: float(np.interp(z,_hz,_hv))
print('DART land zb',round(zb,3),'zw',round(zw,3),'zh',round(zh,3),'zk',round(zk,3),'hem',round(zhem,3),'hj',round(hj,3))
def fstroke(uz,side,w,mat=0,fixed=False,near=None):
    pts=[]
    for u,z in uz:
        x=(cx+side*u*hw(z)) if not fixed else u
        loc,n,_,_=bv.ray_cast(Vector((x,-3,z)),Vector((0,1,0)),10)
        if loc is None or abs(loc[1]-J('spine03')[1])>0.35:
            if len(pts)>2: break
            continue
        if near is not None and np.linalg.norm(np.array(loc)-near)>0.05:
            if len(pts)>2: break
            continue
        pts.append(np.array(loc))
    if len(pts)<3: return
    q=resamp(smooth(pts,2),0.005); q,nn=onsurf(q)
    if len(q)>3: strokes.append((q,nn,w,True,mat))
def dot(x,z,r,mat=1):
    if os.environ.get('DBTN','1')=='0': return
    pts=[]
    for u in np.linspace(x-r,x+r,5):
        loc,n,_,_=bv.ray_cast(Vector((u,-3,z)),Vector((0,1,0)),10)
        if loc is None: return
        pts.append(np.array(loc))
    q,nn=onsurf(np.array(pts)); strokes.append((q,nn,r*2.0,True,mat))
def lerp(a,b,n=12): return [(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for t in np.linspace(0,1,n)]
def curve(ctrl,n=16):
    c=np.array(ctrl,float); out=[]
    for t in np.linspace(0,1,n):
        q=c.copy()
        while len(q)>1: q=q[:-1]*(1-t)+q[1:]*t
        out.append(tuple(q[0]))
    return out
def lerp(a,b,n=12): return [(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for t in np.linspace(0,1,n)]
def curve(ctrl,n=16):
    c=np.array(ctrl,float); out=[]
    for t in np.linspace(0,1,n):
        q=c.copy()
        while len(q)>1: q=q[:-1]*(1-t)+q[1:]*t
        out.append(tuple(q[0]))
    return out

_nm=g.name.lower(); ROLE='pants' if any(k in _nm for k in ('trouser','jeans','pants')) else ('shoe' if any(k in _nm for k in ('shoe','sneaker')) else 'top')
GV=np.array([v.co[:] for v in bm.verts]); ztop=GV[:,2].max(); zbot=GV[:,2].min()
def gw(z):
    sel=(np.abs(GV[:,2]-z)<0.01)&(np.abs(GV[:,0]-cx)<_E('GWX','0.2'))
    return (GV[sel,0].min(),GV[sel,0].max()) if sel.sum()>3 else (cx-0.1,cx+0.1)
def hline(z,w,mat=1,f=0.85,n=24):
    x0,x1=gw(z); m=(x0+x1)/2; h=(x1-x0)/2*f
    fstroke([(m-h+2*h*t,z) for t in np.linspace(0,1,n)],1,w,mat,fixed=True)
FW=_E('DFW','0.0024')
_PCOV=os.environ.get('PCOV_'+g.name)=='1'
if ROLE=='pants':
    for sd,s in (('L',1),('R',-1)):
        kx=J('lowerleg01.'+sd)[0]
        fstroke([(kx+0.004*s,z) for z in np.linspace(ztop-0.20,zbot+0.05,30)],1,FW*0.45,1,fixed=True)
        if _PCOV: continue
        x0,x1=gw(ztop-0.03); ex=x1 if s>0 else x0
        fstroke(curve([(ex-s*0.055,ztop-0.025),(ex-s*0.03,ztop-0.06),(ex-s*0.004,ztop-0.10)]),1,FW*0.8,0,fixed=True)
    if not _PCOV:
        fstroke(curve([(cx+0.018,ztop-0.03),(cx+0.020,ztop-0.12),(cx+0.004,ztop-0.16)]),1,FW*0.8,1,fixed=True)
        hline(ztop-0.035,FW*0.7,1,0.92)
elif ROLE=='top':
    # Only tailored shirts have authored torso darts. Cotton and knit tops
    # must not inherit the same long decorative strokes.
    if os.environ.get('CAST_QUALITY_PILOT')!='1' or 'shirt_untucked' in _nm or 'bd' in _nm:
        for s in (1,-1): fstroke(curve([(0.62,zb-0.06),(0.58,(zb+zw)/2),(0.52,zw-0.04)]),s,FW*0.6)
    if 'shirt_untucked' in _nm or 'bd' in _nm:
        fstroke([(cx-0.010,z) for z in np.linspace(ztop-0.10,zbot+0.02,36)],1,FW*0.55,0,fixed=True)
        fstroke([(cx+0.012,z) for z in np.linspace(ztop-0.10,zbot+0.02,36)],1,FW*0.45,1,fixed=True)
        for z in np.linspace(ztop-0.13,zbot+0.07,6):
            dot(cx+0.001,z,0.0021,1)
        px=cx+_E('PKX','0.085'); pz=zb+0.02
        fstroke([(px-0.035,pz),(px-0.035,pz-0.06),(px-0.02,pz-0.072),(px+0.02,pz-0.072),(px+0.035,pz-0.06),(px+0.035,pz)],1,FW*0.7,1,fixed=True)
    elif 'polo' in _nm:
        fstroke([(cx+0.004,z) for z in np.linspace(ztop-0.09,ztop-0.20,12)],1,FW*0.45,0,fixed=True)
        for z in (ztop-0.12,ztop-0.17): dot(cx+0.012,z,0.0021,1)
        hline(zbot+0.03,FW*0.5,1)
    elif 'sweater' in _nm or 'knit' in _nm:
        hline(zbot+0.045,FW*0.55,1)
    elif 'hood' in _nm:
        fstroke([(cx+0.002,z) for z in np.linspace(ztop-0.12,zbot+0.02,36)],1,FW*1.0,0,fixed=True)
        for s in (1,-1): fstroke(curve([(cx+s*0.07,zw+0.02),(cx+s*0.10,zw-0.05),(cx+s*0.13,zw-0.09)]),1,FW*0.8,1,fixed=True)
        hline(zbot+0.05,FW*0.7,1)
    else:
        pass
if ROLE=='top':
    # elbow folds on sleeves
    for sd in ('L','R'):
        e=J('lowerarm01.'+sd)
        loc,n,_,_=bv.ray_cast(Vector((e[0],-3,e[2])),Vector((0,1,0)),10)
        if loc is None or np.linalg.norm(np.array(loc)-e)>0.07: continue
        for dz,dx,ln in ((0.006,0.0,0.030),):
            fstroke([(e[0]+dx+(t-0.5)*ln,e[2]+dz+0.007*math.sin(t*math.pi)) for t in np.linspace(0,1,10)],1,FW*0.8,1,fixed=True,near=e)
print('DART stitches',nst,'strokes',len(strokes)-nst)
# build ribbon mesh
V=[];Fc=[];mids=[]
OFF=_E('DOFF','0.0012')
for q,nn,w,tap,mat in strokes:
    if len(q)<3: continue
    t=np.gradient(q,axis=0); t/=np.linalg.norm(t,axis=1)[:,None]+1e-9
    sdv=np.cross(nn,t); sdv/=np.linalg.norm(sdv,axis=1)[:,None]+1e-9
    k=len(q); s=np.linspace(0,1,k)
    ww=w*(np.clip(np.sin(np.pi*s),0,1)**0.7*0.9+0.1) if tap else np.full(k,w)
    b=len(V)
    for i in range(k):
        p=q[i]+nn[i]*OFF; V.append(tuple(p+sdv[i]*ww[i]/2)); V.append(tuple(p-sdv[i]*ww[i]/2))
    for i in range(k-1):
        Fc.append((b+2*i,b+2*i+1,b+2*i+3,b+2*i+2)); mids.append(mat)
bm.free()
rm=bpy.data.meshes.new('V64_dress_lines'); rm.from_pydata(V,[],Fc); rm.update()
ink=bpy.data.materials['PEEPS_V5_INK']; tm=ink.copy(); tm.name='V64_TOPSTITCH'
tm.node_tree.nodes['Emission'].inputs['Color'].default_value=(*(C*_E('DTS','0.45')),1)
rm.materials.append(ink); rm.materials.append(tm)
for p,mi in zip(rm.polygons,mids): p.material_index=mi
ro=bpy.data.objects.new('Host.V64_dress_lines',rm)
ro['castGarmentSource']=g.name
for cl in g.users_collection: cl.objects.link(ro)
px=g.copy(); px.data=g.data.copy(); px.name='Host.V64_sd_proxy'
for cl in g.users_collection: cl.objects.link(px)
for x in px.modifiers:
    if x.type=='ARMATURE': x.object=rig
px.modifiers.new('Tri','TRIANGULATE'); px.hide_render=True; px.data.materials.clear()
for cl in list(px.users_collection):
    if cl.name!='Collection': cl.objects.unlink(px)
bpy.context.view_layer.update()
sd=ro.modifiers.new('SD','SURFACE_DEFORM'); sd.target=px; sd.falloff=4
with bpy.context.temp_override(object=ro,active_object=ro,selected_objects=[ro]):
    bpy.ops.object.surfacedeform_bind(modifier='SD')
if not sd.is_bound and os.environ.get('CAST_QUALITY_PILOT')=='1':
    from pathlib import Path
    binder=Path(os.environ['PV1']).parents[3]/'scripts/cast-bind-garment-lines.py'
    exec(compile(binder.read_text(),str(binder),'exec'),globals())
print('DART ribbons',g.name,len(V),'bound',ro.get('castRibbonBinding') or sd.is_bound)
S.frame_set(F0)
