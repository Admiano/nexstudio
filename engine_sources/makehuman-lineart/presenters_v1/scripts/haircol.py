import bpy,os
_hx=os.environ.get('HCOL','')
if _hx:
    _l=lambda c:(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4)
    _b=[_l(int(_hx.lstrip('#')[i:i+2],16)/255) for i in (0,2,4)]
    _e=[c*0.68 for c in _b]
    _s=[min(c*2.2,c+(1-c)*0.45)+0.03 for c in _b]
    _dx=os.environ.get('HDYE','')
    if _dx: _e=[_l(int(_dx.lstrip('#')[i:i+2],16)/255) for i in (0,2,4)]
    _nt=bpy.data.materials['LINEART_HAIR_PAPER'].node_tree.nodes
    _m0=[i for i in _nt['Mix'].inputs if i.enabled]; _m1=[i for i in _nt['Mix.001'].inputs if i.enabled]
    _m0[1].default_value=(*_b,1); _m0[2].default_value=(*_e,1); _m1[2].default_value=(*_s,1)
    import numpy as _np
    _hp=bpy.data.objects['Host.high-poly']; _A=_np.array(_hp.matrix_world); _c=_np.array([v.co[:] for v in _hp.data.vertices])@_A[:3,:3].T+_A[:3,3]
    _gx=_c[:,0].mean(); _L=_c[_c[:,0]>_gx].mean(0); _R=_c[_c[:,0]<=_gx].mean(0); _ez=(_L[2]+_R[2])/2; _k=float(_np.linalg.norm(_L-_R))/0.0519
    _mp=lambda z: _ez+(z-1.5638)*_k
    for _n in ('Map Range','Map Range.001','Map Range.002'):
        for _i in ('From Min','From Max'): _nt[_n].inputs[_i].default_value=_mp(_nt[_n].inputs[_i].default_value)
    if _dx:
        _nt['Map Range.002'].inputs['From Min'].default_value=_ez+float(os.environ.get('DYZ0','0.02'))
        _nt['Map Range.002'].inputs['From Max'].default_value=_ez+float(os.environ.get('DYZ1','0.085'))
        _nt['Math.002'].inputs[1].default_value=float(os.environ.get('DYK','1.0'))
    print('HAIRMAP eye z %.4f k %.3f dye %s'%(_ez,_k,_dx))
    print('HAIRCOL',_hx,[round(x,3) for x in _b])
