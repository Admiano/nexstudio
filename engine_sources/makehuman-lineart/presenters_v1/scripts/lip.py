import bpy,os
_lx=os.environ.get('LIPC','')
if _lx:
    _l=lambda c:(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4)
    _c=[_l(int(_lx.lstrip('#')[i:i+2],16)/255) for i in (0,2,4)]
    _m=[i for i in bpy.data.materials['PEEPS_V2_WARM_SKIN'].node_tree.nodes['Mix.002'].inputs if i.enabled and i.type=='RGBA']
    _m[0].default_value=(*[x*0.82 for x in _c],1); _m[1].default_value=(*_c,1)
    print('LIPC',_lx,[round(x,3) for x in _c])
