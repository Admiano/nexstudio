import bpy,numpy as np,os
_b=bpy.data.objects['Host.eyebrow001']; _me=_b.data; _n=len(_me.vertices)
_c=np.zeros(_n*3); _me.vertices.foreach_get('co',_c); _c=_c.reshape(-1,3)
_ax=np.abs(_c[:,0]); _bins=np.linspace(_ax.min(),_ax.max(),13); _i=np.clip(np.digitize(_ax,_bins)-1,0,11)
_mid=np.array([_c[_i==k,2].mean() if (_i==k).any() else 0 for k in range(12)])[_i]
_t=(_ax-_ax.min())/(_ax.max()-_ax.min()+1e-9)
_th=float(os.environ.get('MBTH','1.45')); _dz=np.zeros_like(_c); _dz[:,2]=(_c[:,2]-_mid)*(_th-1)-float(os.environ.get('MBIN','0.0015'))*(1-_t)**2
for _seq in [_me.vertices]+([k.data for k in _me.shape_keys.key_blocks] if _me.shape_keys else []):
    _k=np.zeros(_n*3); _seq.foreach_get('co',_k); _seq.foreach_set('co',(_k.reshape(-1,3)+_dz).ravel())
_me.update(); print('MALEBROW',_n,'thick',_th)
