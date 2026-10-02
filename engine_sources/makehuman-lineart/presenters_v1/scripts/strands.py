import bpy, numpy as np, os
_E=lambda k,d: float(os.environ.get(k,d))
_hn=os.environ.get('HOBJ','Host.hair_culturalibre_hair_01')
_h=bpy.data.objects[_hn]; _me=_h.data
_nv=len(_me.vertices)
_co=np.zeros(_nv*3); _me.vertices.foreach_get('co',_co); _co=_co.reshape(-1,3)
_M=np.array(_h.matrix_world); _W=_co@_M[:3,:3].T+_M[:3,3]
_no=np.zeros(_nv*3); _me.vertices.foreach_get('normal',_no); _no=_no.reshape(-1,3)@_M[:3,:3].T
_no/=np.linalg.norm(_no,axis=1)[:,None]+1e-12
_ed=np.zeros(len(_me.edges)*2,int); _me.edges.foreach_get('vertices',_ed); _ed=_ed.reshape(-1,2)
_hid=np.zeros(_nv,bool)
if 'hair_hidden' in _h.vertex_groups:
    _gi=_h.vertex_groups['hair_hidden'].index
    for v in _me.vertices:
        for g in v.groups:
            if g.group==_gi and g.weight>0.5: _hid[v.index]=True
_adj=[[] for _ in range(_nv)]
for k,(a,b) in enumerate(_ed): _adj[a].append((b,k)); _adj[b].append((a,k))
_front=(_no[:,1]<-_E('SFR','0.15'))&~_hid
def _walk(s,sign):
    out=[]; cur=s; seen={s}
    for _ in range(400):
        best=None;bd=_E('SDOT','0.55')
        for o,k in _adj[cur]:
            if o in seen or _hid[o]: continue
            d=_W[o]-_W[cur]; L=np.linalg.norm(d)
            if L<1e-9: continue
            g=-d[2]/L*sign
            if g>bd: bd=g;best=(o,k)
        if best is None: break
        out.append(best[1]); cur=best[0]; seen.add(cur)
    return out
_rng=np.random.default_rng(int(_E('SSEED','7')))
_fx=_W[_front]; _fi=np.where(_front)[0]
_x0,_x1=_fx[:,0].min(),_fx[:,0].max(); _z0,_z1=_fx[:,2].min(),_fx[:,2].max()
_nx=int(_E('SNX','16')); _nz=int(_E('SNZ','3'))
_mark=np.zeros(len(_ed),bool); _used=np.zeros(_nv,bool); _nch=0
for zi in range(_nz):
    for xi in range(_nx):
        x=_x0+(xi+0.5+_rng.uniform(-0.3,0.3))*(_x1-_x0)/_nx
        z=_z1-(zi+0.35+_rng.uniform(-0.15,0.15))*(_z1-_z0)/(_nz+0.3)
        d=(_fx[:,0]-x)**2+(_fx[:,2]-z)**2; s=_fi[np.argmin(d)]
        if _used[s] or d.min()>0.02**2: continue
        ch=_walk(s,-1)[::-1]+_walk(s,1)
        if len(ch)<int(_E('SMIN','5')): continue
        n=len(ch); a=int(_rng.uniform(0,_E('SCUT','0.25'))*n); b=n-int(_rng.uniform(0,_E('SCUT','0.25'))*n)
        ch=ch[a:b]
        for k in ch: _mark[k]=True; _used[_ed[k]]=True
        _nch+=1
_att=_me.attributes.get('freestyle_edge') or _me.attributes.new('freestyle_edge','BOOLEAN','EDGE')
_att.data.foreach_set('value',_mark)
_me.update()
_vl=bpy.context.view_layer; _fs=_vl.freestyle_settings
_ref=_fs.linesets['HAIR_LOCKS']
_ls=_fs.linesets.get('HAIR_STRANDS') or _fs.linesets.new('HAIR_STRANDS')
_ls.select_by_visibility=True; _ls.visibility='VISIBLE'
_ls.select_by_edge_types=True
for a in ('silhouette','border','crease','ridge_valley','suggestive_contour','material_boundary','contour','external_contour'): setattr(_ls,'select_'+a,False)
_ls.select_edge_mark=True
_ls.select_by_face_marks=False
_ls.select_by_collection=True; _ls.collection=bpy.data.collections['HAIR_LINES']; _ls.collection_negation='INCLUSIVE'
_st=_ref.linestyle.copy(); _st.name='HAIR_STRANDS_STYLE'; _ls.linestyle=_st
_st.thickness=_E('SW','3.2'); _st.length_min=0
try: _st.use_length_min=False
except Exception: pass
_ls.show_render=True
print('STRANDS',_hn,'front',int(_front.sum()),'chains',_nch,'edges',int(_mark.sum()))
