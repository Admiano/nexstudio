import bpy,numpy as np
from mathutils import Matrix,Vector
_FL=Vector((-0.42,-0.1173,1.5638)); _FI=0.0519
_hr=bpy.data.objects['Host.rig']; bpy.context.view_layer.update()
_o=bpy.data.objects['Host.high-poly']; _A=np.array(_o.matrix_world); _c=np.array([v.co[:] for v in _o.data.vertices])@_A[:3,:3].T+_A[:3,3]
_mx=_c[:,0].mean(); _L=_c[_c[:,0]>_mx].mean(0); _R=_c[_c[:,0]<=_mx].mean(0); _m=Vector((_L+_R)/2); _s=_FI/float(np.linalg.norm(_L-_R))
_T=Matrix.Translation(_FL)@Matrix.Scale(_s,4)@Matrix.Translation(-_m)
_n=[]
for _ob in [o for o in bpy.data.objects if o.name.startswith('Host.') and o.type=='MESH' and o.parent==_hr and o.parent_type=='OBJECT']:
    _mw=_ob.matrix_world.copy(); _To=_mw.inverted()@_T@_mw; _Ta=np.array(_To)
    def _tx(seq):
        c=np.zeros(len(seq)*3); seq.foreach_get('co',c); c=c.reshape(-1,3)@_Ta[:3,:3].T+_Ta[:3,3]; seq.foreach_set('co',c.ravel())
    _tx(_ob.data.vertices)
    if _ob.data.shape_keys:
        for _k in _ob.data.shape_keys.key_blocks: _tx(_k.data)
    _ob.data.update(); _ob.matrix_world=_mw@_To.inverted(); _n.append(_ob.name)
bpy.context.view_layer.update()
print('FACEALIGN scale %.4f shift %s objects %d'%(_s,tuple(round(x,4) for x in (_FL-_m)),len(_n)))
