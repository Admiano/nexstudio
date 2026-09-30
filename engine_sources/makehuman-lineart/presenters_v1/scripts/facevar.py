import bpy,os,numpy as np
from mathutils import Vector
_F=os.environ.get('FACE','0')
if _F not in ('0','base',''):
    _E=lambda k,d: float(os.environ.get(k,d))
    _r=bpy.data.objects['Host.rig']; _b=bpy.data.objects['Host.body']
    _r.data.pose_position='REST'; bpy.context.view_layer.update()
    _mw=_b.matrix_world
    _hv=np.array([tuple(_mw@v.co) for v in _b.data.vertices])
    _hd=_hv[_hv[:,2]>1.40]
    CX=float((_hd[:,0].min()+_hd[:,0].max())/2)
    _pu=[]
    for _pn in ('Host.lineart_pupil.L','Host.lineart_pupil.R'):
        _po=bpy.data.objects.get(_pn)
        if _po is not None:
            _pu.append(np.array([tuple(_po.matrix_world@v.co) for v in _po.data.vertices]).mean(0))
    if len(_pu)==2:
        EYEZ=float((_pu[0][2]+_pu[1][2])/2); EYEX=float(abs(_pu[0][0]-_pu[1][0])/2)
    else:
        EYEZ=1.60; EYEX=0.030
    _fr=_hd[_hd[:,1]<-0.08]
    _fm=_fr[abs(_fr[:,0]-CX)<0.045]
    _fm=_fm[_fm[:,2]<EYEZ-0.02]
    CHINZ=float(_fm[:,2].min())
    TOPZ=float(_hd[:,2].max())
    H=TOPZ-CHINZ
    _wj=_fr[(abs(_fr[:,2]-EYEZ-0.015)<0.03)]
    W=float(np.abs(_wj[:,0]-CX).max()) if len(_wj) else 0.10
    def _s(u,a,b):
        t=np.clip((u-a)/max(b-a,1e-9),0,1); return t*t*(3-2*t)
    def _sb(u,a,m,b): return _s(u,a,m)*(1-_s(u,m,b))
    def _g(u,c,s_): return np.exp(-((u-c)/s_)**2)
    def _region(p):
        x,y,z=p; xo=x-CX; xn=abs(xo)/W; zn=(z-CHINZ)/H
        front=_s(-y,0.06,0.12)
        jaw=_sb(xn,0.30,0.65,1.10)*_sb(zn,-0.06,0.12,0.34)*front
        chin=_g(xn,0,0.30)*_sb(zn,-0.25,0.05,0.28)*front
        cheek=_sb(xn,0.45,0.75,1.15)*_sb(zn,0.28,0.42,0.60)*front
        brow=_g(xn,0,0.85)*_g(zn,(EYEZ-CHINZ)/H+0.075/H,0.075)*front
        temple=_sb(xn,0.80,1.00,1.40)*_sb(zn,0.50,0.70,0.92)*front
        eyes=_sb(xn,0.12,0.45,1.05)*_g(zn,(EYEZ-CHINZ)/H,0.06)*front
        front_face=_g(xn,0,0.85)*front
        return dict(jaw=jaw,chin=chin,cheek=cheek,brow=brow,temple=temple,eyes=eyes,face=front_face,H=H,EYEX=EYEX)
    _VAR={
     '1':dict(jaw_in=0.14,chin_dz=-0.0095,cheek_dz=0.0055,brow_dz=-0.005,eyes_w=1.10,face_short=0.0,temple_in=0.06,brow_z=0.78),
     '2':dict(jaw_in=-0.095,chin_dz=0.007,cheek_dy=-0.006,brow_dz=0.0055,eyes_w=0.90,face_short=-0.007,temple_in=-0.055,brow_z=1.25),
     '3':dict(jaw_in=0.07,chin_dz=-0.004,cheek_dz=0.0,brow_dz=0.003,eyes_w=1.04,face_short=0.006,temple_in=0.08,brow_z=0.9),
    }[_F]
    EYE0=0.0
    _SC=lambda v: v*H/0.21
    def _delta(p):
        r=_region(p); x,y,z=p; xo=x-CX
        dx=-xo*(r['jaw']*_VAR.get('jaw_in',0)+r['temple']*_VAR.get('temple_in',0))
        dx+= -np.sign(xo)*abs(xo)*r['eyes']*(1-_VAR.get('eyes_w',1))
        dz=r['chin']*_SC(_VAR.get('chin_dz',0))+r['cheek']*_SC(_VAR.get('cheek_dz',0))+r['brow']*_SC(_VAR.get('brow_dz',0))
        dz+=r['face']*_SC(_VAR.get('face_short',0))*_s((z-CHINZ)/H,0.35,0.9)
        dy=r['cheek']*_SC(_VAR.get('cheek_dy',0))
        return np.array([dx,dy,dz])
    _edit=[]
    for o in bpy.data.objects:
        if not (o.name.startswith('Host.') and o.type=='MESH'): continue
        if 'hair' in o.name or 'ear_' in o.name: continue
        _om=o.matrix_world; _omi=_om.inverted()
        def _tx(seq):
            co=np.zeros(len(seq)*3); seq.foreach_get('co',co); co=co.reshape(-1,3)
            wp=co@np.array(_om)[:3,:3].T+np.array(_om)[:3,3]
            d=np.array([_delta(p) for p in wp])
            co2=np.array([_omi @ Vector(p+d_) for p,d_ in zip(wp,d)])
            seq.foreach_set('co',co2.ravel())
        _tx(o.data.vertices)
        if o.name.startswith('Host.eyebrow'):
            bc=np.zeros(len(o.data.vertices)*3); o.data.vertices.foreach_get('co',bc); bc=bc.reshape(-1,3)
            cz=bc[:,2].mean(); bc[:,2]=cz+(bc[:,2]-cz)*float(_VAR.get('brow_z',1.0))
            o.data.vertices.foreach_set('co',bc.ravel())
            if o.data.shape_keys:
                for k in o.data.shape_keys.key_blocks:
                    kc=np.zeros(len(k.data)*3); k.data.foreach_get('co',kc); kc=kc.reshape(-1,3)
                    kc[:,2]=cz+(kc[:,2]-cz)*float(_VAR.get('brow_z',1.0)); k.data.foreach_set('co',kc.ravel())
        if o.data.shape_keys:
            for k in o.data.shape_keys.key_blocks: _tx(k.data)
        o.data.update(); _edit.append(o.name)
    bpy.context.view_layer.update()
    _r.data.pose_position='POSE'; bpy.context.view_layer.update()
    print('FACEVAR',_F,'edited',len(_edit),'meshes')
