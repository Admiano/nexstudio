import bpy,os
_w=float(os.environ.get('RLX','1'))
_r=bpy.data.objects['Host.rig']; _ref=bpy.data.objects.get('Ref.rig')
if _ref and _w>0:
    _n=0
    for _s in 'LR':
        for _b in ('clavicle','shoulder01','upperarm01','upperarm02','lowerarm01','lowerarm02','wrist'):
            _pb=_r.pose.bones.get(_b+'.'+_s)
            if not _pb: continue
            _c=_pb.constraints.new('COPY_ROTATION'); _c.name='RELAX'; _c.target=_ref; _c.subtarget=_pb.name
            _c.target_space=_c.owner_space='WORLD'; _c.influence=_w; _n+=1
    print('RELAX arm bones',_n,'influence',_w)
