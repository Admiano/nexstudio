import bpy, numpy as np, os, bmesh
from mathutils import Vector, Matrix
_sides=[float(s) for s in os.environ.get('SIDES','1').split(',')]
_tuck0=os.environ.get('TUCK','1'); _est=os.environ.get('EST','hoop')
for _si,_side in enumerate(_sides):
    os.environ['ESIDE']=str(_side); os.environ['TUCK']=_tuck0 if _si==0 else '0'
    exec(open(__import__('os').environ['PV1']+'/ear.py').read())
    _ink=bpy.data.materials['V59_INK'] if 'V59_INK' in bpy.data.materials else bpy.data.materials['LINEART_EYE_INK']
    def _sph(c,r,sz,mat,name):
        bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=24,v_segments=12,radius=1.0)
        for v in bm.verts: v.co=Vector((c[0]+v.co.x*r,c[1]+v.co.y*r*0.6,c[2]+v.co.z*r*sz))
        me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
        ob=bpy.data.objects.new(name,me)
        for cc in _b.users_collection: cc.objects.link(ob)
        ob.parent=_r; ob.parent_type='BONE'; ob.parent_bone='head'; bpy.context.view_layer.update(); ob.matrix_world=Matrix.Identity(4)
        return ob
    if _est!='hoop':
        _top=_lw+Vector((_sd*_E('EX','0.002'),_E('EY','0.004')-0.001,_E('EZ','0.001')))
        for _o in (_rim,_eo): bpy.data.objects.remove(_o)
        _R=_E('EOR','0.0016'); _k=_E('RIMK','0.0010'); _bk=Vector((0,_E('RIMB','0.0010'),0))
        if _est=='bar':
            L=_E('BARL','0.024'); P=[_top+Vector((0,0,-L*t)) for t in np.linspace(0,1,12)]
            _tube(P,_E('BARW','0.0015'),_gm,'Host.V61_ear_bar'); _tube([p+_bk for p in P],_E('BARW','0.0015')+_k,_ink,'Host.V61_ear_bar_rim')
            e=P[-1]+Vector((0,0,-0.0025)); _sph(e,0.0026,1.0,_gm,'Host.V61_ear_ball'); _sph(e+_bk,0.0026+_k,1.0,_ink,'Host.V61_ear_ball_rim')
            _sph(_top,0.0018,1.0,_gm,'Host.V61_ear_post'); _sph(_top+_bk,0.0018+_k,1.0,_ink,'Host.V61_ear_post_rim')
        elif _est=='stud':
            _pm=bpy.data.materials.get('V61_PEARL') or bpy.data.materials.new('V61_PEARL'); _pm.use_nodes=True; _pn=_pm.node_tree; _pn.nodes.clear()
            _pe=_pn.nodes.new('ShaderNodeEmission'); _pe.inputs['Color'].default_value=(0.97,0.94,0.88,1); _po=_pn.nodes.new('ShaderNodeOutputMaterial'); _pn.links.new(_pe.outputs[0],_po.inputs[0])
            c=_top+Vector((0,0,-_E('STZ','0.001'))); r=_E('STR','0.0042')
            _sph(c,r,1.0,_pm,'Host.V61_ear_pearl'); _sph(c+_bk,r+_k,1.0,_ink,'Host.V61_ear_pearl_rim')
            _sph(c+Vector((-0.0013*_sd,-0.003,0.0013)),r*0.28,1.0,bpy.data.materials['LINEART_WHITE'] if 'LINEART_WHITE' in bpy.data.materials else _pm,'Host.V61_ear_pearl_hi')
        elif _est=='drop':
            L=_E('DRL','0.010'); P=[_top+Vector((0,0,-L*t)) for t in np.linspace(0,1,8)]
            _tube(P,0.0008,_gm,'Host.V61_ear_chain'); _tube([p+_bk for p in P],0.0008+_k,_ink,'Host.V61_ear_chain_rim')
            r=_E('DRR','0.0045'); c=P[-1]+Vector((0,0,-r*1.5))
            _sph(c,r,1.55,_gm,'Host.V61_ear_drop'); _sph(c+_bk,r+_k,1.55+_k/r,_ink,'Host.V61_ear_drop_rim')
            _sph(_top,0.0018,1.0,_gm,'Host.V61_ear_post'); _sph(_top+_bk,0.0018+_k,1.0,_ink,'Host.V61_ear_post_rim')
    _sfx='_R' if _side>0 else '_L'
    for _o in list(bpy.data.objects):
        if (_o.name.startswith('Host.V60_') or _o.name.startswith('Host.V61_')) and not _o.name[-2:] in ('_R','_L'):
            _o.name=_o.name+_sfx
    print('EAR2 side',_side,'style',_est)
