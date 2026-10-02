# hairline + lip outline
SF=len(F)
_sv=[(m,m.show_viewport) for m in body.modifiers if m.type in ('MASK','SUBSURF')]
for m,_ in _sv: m.show_viewport=False
bpy.context.view_layer.update(); _dg=bpy.context.evaluated_depsgraph_get()
_em=body.evaluated_get(_dg).to_mesh(); EV0=np.array([v.co[:] for v in _em.vertices]); body.evaluated_get(_dg).to_mesh_clear()
for m,f in _sv: m.show_viewport=f
bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get()
from mathutils.kdtree import KDTree as _KD
def _front(x,z,b):
    h=b.ray_cast(Vector((x,-0.5,z)),Vector((0,1,0))); return h
if E('LO','1')>0:
    lm=np.zeros(len(co)); me.attributes['lipmask'].data.foreach_get('value',lm)
    TH=E('LTH','0.0'); seg={}; ept={}
    for p in me.polygons:
        vs=list(p.vertices)
        if not all(keep[i] for i in vs): continue
        c=co[vs].mean(0)
        if abs(c[0])>0.03 or c[1]>-0.09 or not (1.465<c[2]<1.50): continue
        cr_=[]
        for i in range(len(vs)):
            u,v=vs[i],vs[(i+1)%len(vs)]
            if (lm[u]-TH)*(lm[v]-TH)<0:
                e=(min(u,v),max(u,v)); t=(TH-lm[e[0]])/(lm[e[1]]-lm[e[0]]); ept[e]=EV0[e[0]]*(1-t)+EV0[e[1]]*t; cr_.append(e)
        if len(cr_)==2:
            seg.setdefault(cr_[0],[]).append(cr_[1]); seg.setdefault(cr_[1],[]).append(cr_[0])
    loops=[]; used=set()
    for st in seg:
        if st in used: continue
        L=[st]; used.add(st); cur=st
        while True:
            nx=[n for n in seg[cur] if n not in used]
            if not nx: break
            cur=nx[0]; used.add(cur); L.append(cur)
        loops.append(np.array([ept[e] for e in L]))
    loops.sort(key=len,reverse=True)
    print('LIP loops',[len(l) for l in loops[:5]],[round(float(l[:,1].mean()),3) for l in loops[:5]])
    np.save(__import__('os').environ.get('PV1_TMP','/tmp')+'/loops.npy',np.array(loops,dtype=object),allow_pickle=True)
    LIPV=np.array(sorted({i for e in ept for i in e})); LIPR=[len(V),None]
    for L in loops[:int(E('LNL','1'))]:
        cl=np.linalg.norm(L[0]-L[-1])<0.004
        if cl: L=np.vstack([L,L[:1]])
        L=smooth(L,int(E('LSM','2'))); L=resample(L,160)
        ribbon(L+np.array([0,-E('LOFF','0.0006'),0]),np.tile([0,-1,0],(len(L),1)),lambda t: E('LOW','0.0015'))
    LIPR[1]=len(V)
if E('HB','1')>0:
    hair=bpy.data.objects[os.environ.get('HOBJ','Host.hair_culturalibre_hair_01')]; hb=BVHTree.FromObject(hair,dg)
    cx,cz=0.0,E('HCZ','1.535'); runs=[[]]
    for a in np.radians(np.linspace(-E('HA','140'),E('HA','140'),240)):
        got=None
        for r in np.arange(0.01,0.16,0.0004):
            x=cx+r*np.sin(a); z=cz+r*np.cos(a)
            hbo=_front(x,z,bvh); hh=_front(x,z,hb)
            if hh[0] is not None and (hbo[0] is None or hh[3]<hbo[3]-1e-4): got=np.array(hh[0][:]); break
            if hbo[0] is None and hh[0] is None: break
        if got is None or (runs[-1] and np.linalg.norm(got-runs[-1][-1])>E('HJ','0.008')): runs.append([])
        if got is not None: runs[-1].append(got)
    for R in runs:
        if len(R)<8: continue
        P=smooth(np.array(R),int(E('HSM','6'))); P=resample(P,max(20,len(R))); P=P+np.array([0,-E('HOFF','0.0015'),0])
        ribbon(P,np.tile([0,-1,0],(len(P),1)),lambda t: E('HBW','0.0019')*min(1,min(t,1-t)/0.08+0.3))
        print('HB run',len(R))
print('MR',[ (n.name,[round(i.default_value,3) for i in n.inputs[1:5]]) for n in bpy.data.materials['PEEPS_V2_WARM_SKIN'].node_tree.nodes if n.type=='MAP_RANGE'])
