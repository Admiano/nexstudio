import bpy,os,numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
E=lambda k,d: float(os.environ.get(k,d))
S=bpy.context.scene; fs=S.view_layers[0].freestyle_settings
body=bpy.data.objects['Host.body']; me=body.data; rig=body.parent
co=np.array([v.co[:] for v in me.vertices]); vn=np.array([v.normal[:] for v in me.vertices])
mk=[m for m in body.modifiers if m.type=='MASK' and m.name=='Hide helpers'][0]
gi=body.vertex_groups[mk.vertex_group].index
ing=np.zeros(len(co),bool)
for v in me.vertices:
    for g in v.groups:
        if g.group==gi and g.weight>0.5: ing[v.index]=True
keep=~ing if mk.invert_vertex_group else ing
kp=[p for p in me.polygons if all(keep[i] for i in p.vertices)]
BF=int(E('BF','1')); S.frame_set(BF); rig.data.pose_position='REST'; bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
bvh=BVHTree.FromObject(body,dg)
def smooth(P,it=3):
    P=P.copy()
    for _ in range(it): P[1:-1]=0.5*P[1:-1]+0.25*(P[:-2]+P[2:])
    return P
def resample(P,n):
    d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]; t=np.linspace(0,d[-1],n)
    return np.stack([np.interp(t,d,P[:,k]) for k in range(3)],1)
def ray(xz):
    out=[];nrm=[]
    for x,z in xz:
        h=bvh.ray_cast(Vector((x,-0.5,z)),Vector((0,1,0)))
        if h[0] is None: continue
        out.append(h[0][:]); nrm.append(h[1][:])
    return np.array(out),np.array(nrm)
def cr(pts,n=40):
    P=np.array(pts,float); P=np.vstack([2*P[0]-P[1],P,2*P[-1]-P[-2]]); out=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1:i+3]
        for t in np.linspace(0,1,n//(len(P)-3)+2)[:-1]:
            out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    out.append(P[-2]); return np.array(out)
V=[];F=[];RB=[]
OFF=E('OFF','0.0007')
def ribbon(P,N,wfun):
    P=np.asarray(P,float); N=np.asarray(N,float); N/=np.linalg.norm(N,axis=1)[:,None]
    T=np.gradient(P,axis=0); T/=np.linalg.norm(T,axis=1)[:,None]+1e-12
    Sd=np.cross(T,N); Sd/=np.linalg.norm(Sd,axis=1)[:,None]+1e-12
    n=len(P); t=np.linspace(0,1,n); w=np.array([wfun(x) for x in t])
    base=len(V); Q=P+N*OFF; RB.append(base)
    for i in range(n):
        V.append(Q[i]+Sd[i]*w[i]/2); V.append(Q[i]-Sd[i]*w[i]/2)
    for i in range(n-1): F.append((base+2*i,base+2*i+2,base+2*i+3,base+2*i+1))
    for end,sgn in ((0,-1),(n-1,1)):
        c=len(V); V.append(Q[end]); ring=[]
        for k in range(7):
            a=np.pi*k/6; d=np.cos(a)*Sd[end]+np.sin(a)*T[end]*sgn; V.append(Q[end]+d*w[end]/2); ring.append(len(V)-1)
        for k in range(6): F.append((c,ring[k],ring[k+1]))
W=E('W','0.0015')
taper=lambda a=0.35: (lambda t: W*(a+(1-a)*np.sin(np.pi*t)**0.6))
def surf(idx,it=3,n=40,fwd=0.4):
    P=smooth(co[idx],it); P=resample(P,n)
    N=np.array([vn[np.linalg.norm(co[idx]-p,axis=1).argmin()] for p in P]); N=N+np.array([0,-fwd,0]); return P,N
cnt_r=0
# eyes: visible-opening contour from front raycasts (eyeball vs lid)
hp=bpy.data.objects['Host.high-poly']; hm=hp.data
hbvh=BVHTree.FromObject(hp,dg)
def rayF(xz):
    out=[];nrm=[]
    for x,z in xz:
        hs=[h for h in (bvh.ray_cast(Vector((x,-0.5,z)),Vector((0,1,0))),hbvh.ray_cast(Vector((x,-0.5,z)),Vector((0,1,0)))) if h[0] is not None]
        if not hs: continue
        h=min(hs,key=lambda h:h[3]); out.append((h[0]+Vector((0,-E('EOFF','0.0006'),0)))[:]); nrm.append((0,-1,0))
    return np.array(out),np.array(nrm)
def front(bv,x,z):
    h=bv.ray_cast(Vector((x,-0.5,z)),Vector((0,1,0))); return h[3] if h[0] is not None else 9
for s in (1,-1):
    X=np.arange(0.006,0.046,0.00025)*s; Z=np.arange(1.548,1.584,0.0002); top=[];bot=[]
    for x in X:
        vis=[z for z in Z if front(hbvh,x,z)<front(bvh,x,z)-1e-5]
        if len(vis)>2: top.append((x,max(vis)+0.0002)); bot.append((x,min(vis)-0.0002))
    top.sort(key=lambda p:abs(p[0])); bot.sort(key=lambda p:abs(p[0]))
    print('EYE',s,len(top),top[0],top[-1])
    T=np.array(top); ax=np.abs(T[:,0]); cf=np.polyfit(ax,T[:,1],4); a0,a1=ax.min(),ax.max()
    xs_=np.linspace(a0,a1,40); zs_=np.polyval(cf,xs_)
    sl=(zs_[-1]-zs_[-4])/(xs_[-1]-xs_[-4]); fx=np.linspace(0,E('FLX','0.0045'),8)[1:]
    xs_=np.r_[xs_,a1+fx]; zs_=np.r_[zs_,zs_[-1]+sl*fx+E('FLZ','0.0030')*(fx/fx[-1])**1.6]
    P,N=rayF(list(zip(s*xs_,zs_))); P=smooth(P,2)
    P=resample(P,48); N=np.tile([0,-1,0],(48,1))
    ribbon(P,N,lambda t: W*E('LIDW','1.45')*(0.35+0.65*np.sin(np.pi*min(1,t*1.25))**0.5) if t<0.8 else W*E('LIDW','1.45')*max(0.1,(1-t)/0.2))
    B_=np.array(bot); bx=np.abs(B_[:,0]); cb=np.polyfit(bx,B_[:,1],4); xb=np.linspace(bx.min(),bx.max(),40); P,N=rayF(list(zip(s*xb,np.polyval(cb,xb)))); P=smooth(P,2); a_=int(len(P)*E('LLA','0.3')); P,N=P[a_:],N[a_:]
    ribbon(P,N+[0,-0.3,0],lambda t: W*E('LLW','0.6')*np.sin(np.pi*t)**0.7+1e-5)
# nose
def draw2d(pts,wf,n=30):
    C=cr(pts,n); P,N=ray([(c[0],c[1]) for c in C]); ribbon(smooth(P,1),N+[0,-0.3,0],wf)
for s in ():
    draw2d([(s*0.0092,1.5185),(s*0.0126,1.5148),(s*0.0133,1.5100),(s*0.0112,1.5064),(s*0.0078,1.5057)],taper(0.3))
0 and draw2d([(-0.0050,1.5062),(-0.0026,1.5040),(0,1.5034),(0.0026,1.5040),(0.0050,1.5062)],taper(0.3))
0 and draw2d([(0.0048,1.5525),(0.0058,1.5450),(0.0069,1.5330),(0.0074,1.5230)],lambda t: W*0.9*(0.2+0.8*np.sin(np.pi*t)**0.5))
exec(open(__import__('os').environ['PV1']+'/sect.py').read())
# skin ribbons to body: copy nearest-vertex shape deltas + armature weights
from mathutils.kdtree import KDTree
sv=[(m,m.show_viewport) for m in body.modifiers if m.type in ('MASK','SUBSURF')]
for m,_ in sv: m.show_viewport=False
bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get()
em=body.evaluated_get(dg).to_mesh(); EV=np.array([v.co[:] for v in em.vertices]); body.evaluated_get(dg).to_mesh_clear()
for m,f in sv: m.show_viewport=f
assert len(EV)==len(co)
delta=EV-co
fz=np.where(keep&(co[:,2]>1.42))[0]
kd=KDTree(len(fz))
for j,i in enumerate(fz): kd.insert(EV[i],j)
kd.balance()
A=np.array(V); NN=[];WW=[]
for p in A:
    r=kd.find_n(p,4); idx=np.array([fz[x[1]] for x in r]); d=np.array([x[2] for x in r]); w=1/(d+2e-4); NN.append(idx); WW.append(w/w.sum())
NN=np.array(NN); WW=np.array(WW)
if 'LIPR' in globals() and LIPR[1]:
    _kl=KDTree(len(LIPV))
    for j,i in enumerate(LIPV): _kl.insert(EV[i],j)
    _kl.balance()
    for vi in range(LIPR[0],LIPR[1]):
        r=_kl.find_n(A[vi],int(E('LNN','2'))); idx=[LIPV[x[1]] for x in r]; d=np.array([x[2] for x in r]); w=1/(d+2e-4)
        idx=(idx*4)[:4]; w=np.resize(w,4)*np.r_[np.ones(len(r)),np.zeros(4)][:4]; NN[vi]=idx; WW[vi]=w/w.sum()
blend=lambda D: (D[NN]*WW[:,:,None]).sum(1)
BV=A-blend(delta)
for k_,f_ in enumerate(F):
    n_=np.cross(A[f_[1]]-A[f_[0]],A[f_[2]]-A[f_[0]])
    if n_[1]>0: F[k_]=tuple(reversed(f_))
rm=bpy.data.meshes.new('V59_face_art'); rm.from_pydata([tuple(v) for v in BV],[],F); rm.update()
ink=bpy.data.materials['LINEART_EYE_INK'].copy(); ink.name='V59_INK'; ink.node_tree.nodes['Emission'].inputs['Color'].default_value=(0.012,0.012,0.012,1); rm.materials.append(ink)
ob=bpy.data.objects.new('Host.V59_face_art',rm); bpy.data.collections['Collection'].objects.link(ob)
ob.parent=rig; ob.matrix_parent_inverse=body.matrix_parent_inverse.copy(); ob.matrix_basis=body.matrix_basis.copy()
ob.shape_key_add(name='Basis',from_mix=False)
sk=body.data.shape_keys; nk=0
for kb in sk.key_blocks[1:]:
    K=np.zeros(len(co)*3); kb.data.foreach_get('co',K); D=K.reshape(-1,3)-co
    if np.abs(D[fz]).max()<1e-7: continue
    nb_=ob.shape_key_add(name=kb.name,from_mix=False); nb_.slider_min=kb.slider_min; nb_.slider_max=kb.slider_max
    nb_.data.foreach_set('co',(BV+blend(D)).ravel())
    fc=nb_.driver_add('value'); dr=fc.driver; dr.type='AVERAGE'; v_=dr.variables.new(); v_.type='SINGLE_PROP'
    v_.targets[0].id_type='KEY'; v_.targets[0].id=sk; v_.targets[0].data_path='key_blocks["%s"].value'%kb.name; nk+=1
gw={}
for vi,(idx,w) in enumerate(zip(NN,WW)):
    for i,wi in zip(idx,w):
        for g in me.vertices[i].groups:
            gw.setdefault(g.group,{}); gw[g.group][vi]=gw[g.group].get(vi,0)+g.weight*wi
for gidx,dd in gw.items():
    vg=ob.vertex_groups.new(name=body.vertex_groups[gidx].name)
    for vi,wt in dd.items():
        if wt>1e-4: vg.add([vi],wt,'REPLACE')
bam=[m for m in body.modifiers if m.type=='ARMATURE'][0]
am=ob.modifiers.new('Armature','ARMATURE'); am.object=rig; am.use_deform_preserve_volume=bam.use_deform_preserve_volume
rig.data.pose_position='POSE'; bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get(); ev=ob.evaluated_get(dg).to_mesh()
print('ART keys',nk,'groups',len(gw))
print('ART verts',len(V))
# line system: uniform even lines, features from art
bpy.data.objects['Host.eyelashes01'].hide_render=True
bm=bpy.data.materials['V57_BROW']; bm.node_tree.nodes['Emission'].inputs['Color'].default_value=(0.02,0.015,0.012,1)
fs.linesets['HEAD_NOSE'].linestyle.thickness=E('NW','2.2')
bpy.data.collections['FACE_FINE'].objects.unlink(bpy.data.objects['Host.eyebrow001'])
fs.linesets['FACE_FINE'].linestyle.thickness=E('MW','2.4')
LW=E('LW','2.8')
fs.linesets['HEAD_OUTLINE'].linestyle.thickness=LW; fs.linesets['HAIR_OUTER'].linestyle.thickness=LW
hl=fs.linesets['HAIR_LOCKS'].linestyle; hl.thickness=E('HLW','2.2'); hl.length_min=E('HLMIN','380')
print('ART done')

