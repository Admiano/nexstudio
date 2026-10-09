import numpy as np
_b=bpy.data.objects['Host.body']; _me=_b.data
_fa=_me.attributes['freestyle_face']; _m=np.zeros(len(_me.polygons),bool); _fa.data.foreach_get('value',_m)
_c=np.zeros(len(_me.polygons)*3); _me.polygons.foreach_get('center',_c); _c=_c.reshape(-1,3)
_z0,_z1=float(os.environ.get('PZ0','1.493')),float(os.environ.get('PZ1','1.5035'))
_s=_m&(np.abs(_c[:,0])<float(os.environ.get('PX','0.013')))&(_c[:,2]>_z0)&(_c[:,2]<_z1)&(_c[:,1]<-0.1)
_m[_s]=False; _fa.data.foreach_set('value',_m); print('FIX unmark',int(_s.sum()))
_sk=_b.data.shape_keys
def _blink(ob,expr):
    fc=ob.driver_add('hide_render'); d=fc.driver; d.type='SCRIPTED'; d.expression=expr
    for n,k in (('a','!ex-eyeBlinkLeft'),('b','!ex-eyeBlinkRight')):
        v=d.variables.new(); v.name=n; v.type='SINGLE_PROP'; v.targets[0].id_type='KEY'; v.targets[0].id=_sk; v.targets[0].data_path='key_blocks["%s"].value'%k
_blink(bpy.data.objects['Host.high-poly'],'max(a,b)>0.55')
_blink(bpy.data.objects['Host.V59_face_art'],'max(a,b)>0.55')
_blink(bpy.data.objects['Host.eyelashes01'],'max(a,b)<=0.55')
