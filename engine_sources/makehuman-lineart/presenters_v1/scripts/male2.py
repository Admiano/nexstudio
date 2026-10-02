import bpy,os,sys
import numpy as np
from mathutils import Vector
sys.path.insert(0,__import__('os').path.join(__import__('os').environ['PV1'],'..','..','scripts'))
import mhclo_fit as F
if os.environ.get('MALE','1')!='0':
    P='Host.'; H=bpy.data.objects[P+'body']; HR=bpy.data.objects[P+'rig']
    G=bpy.data.objects['Guest.body']; GR=bpy.data.objects['Guest.rig']
    NV=len(H.data.vertices)
    def shaped_local(o):
        kb=o.data.shape_keys.key_blocks; n=len(o.data.vertices); b=np.zeros(n*3); kb[0].data.foreach_get('co',b); c=b.copy(); t=np.zeros(n*3)
        for k in kb[1:]:
            if k.name.startswith('$') and k.value: k.data.foreach_get('co',t); c+=(t-b)*k.value
        return b.reshape(-1,3),c.reshape(-1,3)
    M=np.array(H.matrix_world.inverted()@HR.matrix_world@GR.matrix_world.inverted()@G.matrix_world)
    _,gs=shaped_local(G); gm=gs@M[:3,:3].T+M[:3,3]
    def xfer(o):
        kb=o.data.shape_keys.key_blocks; n=len(o.data.vertices); hb=np.zeros(n*3); kb[0].data.foreach_get('co',hb); t=np.zeros(n*3)
        for k in kb[1:]:
            k.data.foreach_get('co',t)
            if k.name.startswith('$'): k.data.foreach_set('co',gm.ravel()); k.value=0.0
            else: k.data.foreach_set('co',(gm.ravel()+t-hb))
        kb[0].data.foreach_set('co',gm.ravel()); o.data.vertices.foreach_set('co',gm.ravel()); o.data.update()
    xfer(H)
    legs=bpy.data.objects.get(P+'lineart_lower_legs')
    if legs and len(legs.data.vertices)==NV:
        if legs.data.shape_keys: xfer(legs)
        else: legs.data.vertices.foreach_set('co',gm.ravel()); legs.data.update()
    from mathutils import Matrix; RM=Matrix.Identity(4)
    gb={b.name:(RM@b.head_local,RM@b.tail_local,b.matrix_local) for b in GR.data.bones}
    bpy.context.view_layer.objects.active=HR
    with bpy.context.temp_override(active_object=HR,object=HR,selected_objects=[HR]):
        bpy.ops.object.mode_set(mode='EDIT')
        mv=[]
        for b in HR.data.edit_bones:
            h,t,ml=gb[b.name]; mv.append((b.head-h).length); b.head=h; b.tail=t
        bpy.ops.object.mode_set(mode='EDIT')
        rolls={}
        bpy.ops.object.mode_set(mode='OBJECT')
    gr={}
    bpy.context.view_layer.objects.active=GR
    with bpy.context.temp_override(active_object=GR,object=GR,selected_objects=[GR]):
        _h=GR.hide_viewport; GR.hide_viewport=False; GR.hide_set(False)
        bpy.ops.object.mode_set(mode='EDIT'); gr={b.name:b.roll for b in GR.data.edit_bones}; bpy.ops.object.mode_set(mode='OBJECT'); GR.hide_viewport=_h
    bpy.context.view_layer.objects.active=HR
    with bpy.context.temp_override(active_object=HR,object=HR,selected_objects=[HR]):
        bpy.ops.object.mode_set(mode='EDIT')
        for b in HR.data.edit_bones: b.roll=gr[b.name]
        bpy.ops.object.mode_set(mode='OBJECT')
    ang=max((HR.data.bones[n].matrix_local.to_3x3()-GR.data.bones[n].matrix_local.to_3x3()).to_quaternion().angle if False else 0 for n in gb)
    rd=max(max(abs(a-b) for ra,rb in zip(HR.data.bones[n].matrix_local.to_3x3(),GR.data.bones[n].matrix_local.to_3x3()) for a,b in zip(ra,rb)) for n in gb)
    W=F.shaped_coords(H)
    def refit(o,kind,name):
        pts,_=F.fit(F.asset(kind,name),W); m2=o.matrix_world.inverted()
        n=len(o.data.vertices); c0=np.zeros(n*3); o.data.vertices.foreach_get('co',c0); c0=c0.reshape(-1,3)
        if o.data.shape_keys: o.data.shape_keys.key_blocks[0].data.foreach_get('co',c0.ravel()) if False else None
        if o.data.shape_keys:
            b0=np.zeros(n*3); o.data.shape_keys.key_blocks[0].data.foreach_get('co',b0); c0=b0.reshape(-1,3)
        if len(pts)!=n:
            for v,p in zip(o.data.vertices,pts): v.co=m2@p
            o.data.update(); return
        c1=np.array([(m2@p)[:] for p in pts]); d=c1-c0
        for seq in [o.data.vertices]+([k.data for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []):
            k=np.zeros(n*3); seq.foreach_get('co',k); seq.foreach_set('co',(k.reshape(-1,3)+d).ravel())
        o.data.update()
    GM=np.array(HR.matrix_world@GR.matrix_world.inverted())
    def wc(o):
        A=np.array(o.matrix_world); c=np.array([v.co[:] for v in o.data.vertices]); return c@A[:3,:3].T+A[:3,3]
    def gwc(n):
        c=wc(bpy.data.objects['Guest.'+n]); return c@GM[:3,:3].T+GM[:3,3]
    def shift(o,sel,d):
        A=np.array(o.matrix_world.inverted())[:3,:3]; c=np.array([v.co[:] for v in o.data.vertices]); c[sel]+=d@A.T
        o.data.vertices.foreach_set('co',c.ravel()); o.data.update()
    hp=bpy.data.objects[P+'high-poly']; hw=wc(hp); gw=gwc('high-poly'); hx=hw[:,0].mean(); gx=gw[:,0].mean()
    for sg in (1,-1):
        hs=(hw[:,0]-hx)*sg>0; gs=(gw[:,0]-gx)*sg>0; shift(hp,hs,gw[gs].mean(0)-hw[hs].mean(0))
    tb=bpy.data.objects[P+'teeth_base']; shift(tb,slice(None),gwc('teeth_base').mean(0)-wc(tb).mean(0))
    refit(bpy.data.objects[P+'eyebrow001'],'eyebrows','eyebrow001'); refit(bpy.data.objects[P+'eyelashes01'],'eyelashes','eyelashes01')
    print('MALE2 guest chassis: bones moved max %.4f, rest-rot diff %.2e, head z %.3f, wrist.L %s'%(max(mv),rd,(HR.matrix_world@HR.data.bones['head'].head_local).z,tuple(round(x,3) for x in HR.matrix_world@HR.data.bones['wrist.L'].head_local)))
