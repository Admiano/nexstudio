_E=lambda k,d: float(os.environ.get(k,d))
_ls=fs.linesets
for _n in ('HEAD_OUTLINE','HAIR_OUTER','FACE_FINE','HEAD_FEATURES','HEAD_NOSE','HAIR_LOCKS'):
    for _m in _ls[_n].linestyle.thickness_modifiers:
        _m.influence=_E('TAPI','0') if _m.type=='ALONG_STROKE' else 0.0
_ls['HEAD_OUTLINE'].linestyle.thickness=_E('LW','4.5'); _ls['HAIR_OUTER'].linestyle.thickness=_E('LW','4.5')
_ls['FACE_FINE'].linestyle.thickness=_E('FW','3.6'); _ls['HEAD_FEATURES'].linestyle.thickness=_E('FW','3.6'); _ls['HEAD_NOSE'].linestyle.thickness=_E('FW','3.6')
_hl=_ls['HAIR_LOCKS']; _hl.linestyle.thickness=_E('HLW','3.6'); _hl.linestyle.length_min=_E('HLMIN','1500'); _hl.show_render=_E('HLON','1')>0
print('LINES ok')
if _E('HAIRFF','1')<1:
    _h=bpy.data.objects[os.environ.get('HOBJ','Host.hair_culturalibre_hair_01')]
    if _h.name in bpy.data.collections['FACE_FINE'].objects: bpy.data.collections['FACE_FINE'].objects.unlink(_h)
if _E('HOFM','1')<1: _ls['HEAD_OUTLINE'].select_by_face_marks=False
_ls['HAIR_OUTER'].select_silhouette=_E('HOSIL','0')>0
if _E('HAIRFF','1')<1:
    _nc=bpy.data.collections.new('NO_HEAD_OUTLINE'); _nc.objects.link(bpy.data.objects[os.environ.get('HOBJ','Host.hair_culturalibre_hair_01')])
    if _E('EXHP','0')>0: _nc.objects.link(bpy.data.objects['Host.high-poly'])
    _ls['HEAD_OUTLINE'].collection=_nc; _ls['HEAD_OUTLINE'].collection_negation='EXCLUSIVE'
if _E('HAIRFF','1')<1 and _E('ARTX','1')>0:
    _nc.objects.link(bpy.data.objects['Host.V59_face_art'])
    for _n in ('HEAD_FEATURES','HEAD_NOSE'):
        _ls[_n].select_by_collection=True; _ls[_n].collection=_nc; _ls[_n].collection_negation='EXCLUSIVE'
if _E('LUN','1')>0:
    _b=bpy.data.objects['Host.body']; _me=_b.data; _fa=_me.attributes['freestyle_face']
    _m=np.zeros(len(_me.polygons),bool); _fa.data.foreach_get('value',_m)
    _c=np.zeros(len(_me.polygons)*3); _me.polygons.foreach_get('center',_c); _c=_c.reshape(-1,3)
    _s=_m&(np.abs(_c[:,0])<_E('LUX','0.032'))&(_c[:,2]>_E('LUZ0','1.458'))&(_c[:,2]<_E('LUZ1','1.492'))&(_c[:,1]<-0.09)
    _m[_s]=False; _fa.data.foreach_set('value',_m); print('LUN',int(_s.sum()))
if _E('SPLIT','1')>0:
    import bmesh
    _a=bpy.data.objects['Host.V59_face_art']; _f=_a.copy(); _f.data=_a.data.copy(); _f.name='Host.V59_face_frame'
    for _c2 in _a.users_collection: _c2.objects.link(_f)
    if _f.animation_data:
        for _d in list(_f.animation_data.drivers):
            if _d.data_path=='hide_render': _f.animation_data.drivers.remove(_d)
    _f.hide_render=False
    for _o,_keep in ((_a,lambda i:i<SF),(_f,lambda i:i>=SF)):
        _bm=bmesh.new(); _bm.from_mesh(_o.data); _bm.faces.ensure_lookup_table()
        bmesh.ops.delete(_bm,geom=[x for x in _bm.faces if not _keep(x.index)],context='FACES_ONLY'); _bm.to_mesh(_o.data); _bm.free()
    print('SPLIT',len(_a.data.polygons),len(_f.data.polygons),_f.data.shape_keys.key_blocks.__len__() if _f.data.shape_keys else 0, bool(_f.data.shape_keys and _f.data.shape_keys.animation_data and len(_f.data.shape_keys.animation_data.drivers)))
if _E('JAWM','1')>0 and _E('HOFM','1')>0:
    _b=bpy.data.objects['Host.body']; _me=_b.data; _fa=_me.attributes['freestyle_face']
    _m=np.zeros(len(_me.polygons),bool); _fa.data.foreach_get('value',_m)
    _c=np.zeros(len(_me.polygons)*3); _me.polygons.foreach_get('center',_c); _c=_c.reshape(-1,3)
    _s=(np.abs(_c[:,0])>_E('JX','0.035'))&(_c[:,2]>1.38)&(_c[:,2]<1.60); _m[_s]=True; _fa.data.foreach_set('value',_m); print('JAWM',int(_s.sum()))
_ls['HAIR_OUTER'].linestyle.length_min=_E('HOLM','0')
