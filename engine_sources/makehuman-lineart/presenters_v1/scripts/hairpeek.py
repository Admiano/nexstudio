# Adds front-readable hair hints for styles whose detail sits behind the head
# (bun, braid) or reads as a solid cap (side-swept). Procedural - no asset deps.
# Env: HAIR (style id), HCOL (hair hex, matched automatically), HPK=0 disables.
import bpy,os,bmesh
import numpy as np
from mathutils import Matrix
if os.environ.get('HPK','1')!='0':
    _HAIR=os.environ.get('HAIR','')
    _rig=bpy.data.objects.get('Host.rig')
    def _parent(ob,bone):
        if _rig and bone in _rig.data.bones:
            mw=ob.matrix_world.copy()
            ob.parent=_rig;ob.parent_type='BONE';ob.parent_bone=bone
            bpy.context.view_layer.update()
            ob.matrix_world=mw
    def _tube(P,r,mat,name,bone,closed=False):
        cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=2
        sp=cu.splines.new('POLY');sp.points.add(len(P)-1)
        for i,p in enumerate(P): sp.points[i].co=(p[0],p[1],p[2],1)
        sp.use_cyclic_u=closed
        cu.bevel_depth=r;cu.bevel_resolution=1;cu.resolution_u=1
        ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob)
        ob.data.materials.append(mat);_parent(ob,bone)
        return ob
    def _ell(name,c,r,scale,mat,bone):
        me=bpy.data.meshes.new(name);bm=bmesh.new()
        bmesh.ops.create_uvsphere(bm,u_segments=16,v_segments=12,radius=r)
        bmesh.ops.scale(bm,vec=scale,verts=bm.verts)
        bmesh.ops.translate(bm,vec=c,verts=bm.verts)
        bm.to_mesh(me);bm.free();me.materials.append(mat)
        ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
        _parent(ob,bone);return ob
    _ink=bpy.data.materials.get('ink') or bpy.data.materials.get('Ink')
    if _ink is None:
        _ink=bpy.data.materials.new('ink');_ink.diffuse_color=(0.05,0.05,0.06,1)
    _hx=os.environ.get('HCOL','') or '6B4230'
    _l=lambda c:(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4)
    _hc=[_l(int(_hx.lstrip('#')[i:i+2],16)/255) for i in (0,2,4)]
    _hm=bpy.data.materials.new('hair.peek');_hm.use_nodes=True
    _nt=_hm.node_tree;_nt.nodes.clear()
    _e=_nt.nodes.new('ShaderNodeEmission');_e.inputs['Color'].default_value=(*_hc,1);_e.inputs['Strength'].default_value=1.0
    _o=_nt.nodes.new('ShaderNodeOutputMaterial');_nt.links.new(_e.outputs[0],_o.inputs[0])
    _b=bpy.data.objects['Host.body'];_mw=_b.matrix_world
    _hv=np.array([tuple(_mw@v.co) for v in _b.data.vertices]);_hd=_hv[_hv[:,2]>1.40]
    CX=float((_hd[:,0].min()+_hd[:,0].max())/2); _TOP=float(_hd[:,2].max())
    if 'elvs_grump_hair' in _HAIR:
        # hairline + part strokes break the cap silhouette - traced off the real hair mesh
        _hmesh=None
        for o in bpy.data.objects:
            if 'hair' in o.name.lower() and o.type=='MESH' and 'ink' not in o.name and 'hp_' not in o.name:
                _hmesh=o;break
        if _hmesh is not None:
            _v=np.array([tuple(_hmesh.matrix_world@p.co) for p in _hmesh.data.vertices])
            pts=[]
            for x0 in np.linspace(CX-0.055,CX+0.055,13):
                _q=_v[abs(_v[:,0]-x0)<0.012]
                _q=_q[_q[:,1]<-0.10]
                if len(_q): pts.append((x0,_q[:,1].min()-0.003,_q[:,2].min()-0.004))
            if len(pts)>4:
                _tube(pts,0.0007,_ink,'Host.hp_hairline','head')
                _tube([(pts[-4][0],pts[-4][1]-0.002,pts[-4][2]+0.02*u) for u in np.linspace(0,1,5)],0.0005,_ink,'Host.hp_part','head')
    if 'bun' in _HAIR:
        # small knot peeking above the crown so the bun reads from the front
        _ell('Host.hp_bun',(CX+0.012,0.005,_TOP+0.008),0.033,(1.0,0.85,0.78),_hm,'head')
        th=np.linspace(0,2*np.pi,24)
        _tube([(CX+0.012+0.032*np.cos(t),-0.004,_TOP+0.010+0.024*np.sin(t)) for t in th],0.0008,_ink,'Host.hp_bun_rim','head',closed=True)
    if 'french_braid' in _HAIR:
        # tapered strand emerging at the right neck side, draping over the front shoulder
        P=[(CX+0.058-0.015*u, -0.075-0.095*np.sin(u*1.35), _TOP-0.24-0.55*u) for u in np.linspace(0,1,9)]
        for i,p in enumerate(P[:-1]):
            r=0.0155*(1-0.55*i/(len(P)-1))
            _ell('Host.hp_braid_%d'%i,tuple(p),r,(0.8,0.7,1.15),_hm,'head' if i<3 else 'neck01')
            _tube([tuple(p),( (p[0]+P[i+1][0])/2,(p[1]+P[i+1][1])/2,(p[2]+P[i+1][2])/2 )],0.0006,_ink,'Host.hp_braid_ink%d'%i,'head' if i<3 else 'neck01')
    print('HAIRPEEK',_HAIR)
