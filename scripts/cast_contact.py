"""Per-frame contact awareness for seated renders: hands rest ON things.

Runs inside the render loop after the garment refit (runpy). Skin verts whose
dominant vertex group is a wrist/lowerarm/finger/metacarpal bone are tested
against a collider tree built from the posed scene: the chair mesh, and the
non-arm faces of every visible Host.* mesh (a hand cannot collide with its own
forearm, but it does collide with lap, torso and the other arm).

Any mover vert found inside a collider (or closer than `margin`) accumulates a
push-out request on its dominant pose bone; the averaged correction is applied
as a small bone translation, capped so a bad cluster cannot launch the arm.
Up to 4 passes per frame; corrections live only for this frame's render.
"""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ARM_PARTS=('wrist','lowerarm','finger','metacarpal')
MARGIN=0.003
MAX_PUSH=0.025
PASSES=4

s=bpy.context.scene
rig=bpy.data.objects.get('Host.rig')
if rig is None:raise RuntimeError('CONTACT_NO_RIG')

def _arm_bone(vgname):
    n=vgname.lower()
    return any(n.startswith(p+'.') or n==p for p in ARM_PARTS)

def _dominant(v,obj):
    best=None;bw=0.0
    for g in v.groups:
        if g.group<len(obj.vertex_groups) and g.weight>bw:
            bw=g.weight;best=obj.vertex_groups[g.group].name
    return best

def _colliders():
    """World-space BVH over chair + non-arm faces of all visible Host meshes."""
    deps=bpy.context.evaluated_depsgraph_get()
    pts=[];faces=[]
    def add(ob,me,mw,mask):
        base=len(pts)
        pts.extend(mw@v.co for v in me.vertices)
        for f in me.polygons:
            if mask is None or all(mask[i] for i in f.vertices):
                faces.append([base+i for i in f.vertices])
    for ob in s.objects:
        if ob.type!='MESH' or ob.hide_render:continue
        if ob.get('castFitSource') or ob.get('castGarmentSource'):continue
        if ob.name=='modern_arm_chair_01':
            add(ob,ob.data,ob.matrix_world,None)
            continue
        if not ob.name.startswith('Host.'):continue
        ev=ob.evaluated_get(deps);me=ev.to_mesh()
        if not me.vertices:ev.to_mesh_clear();continue
        # exclude faces made entirely of arm-vert material from colliders;
        # keep everything else so lap/torso/other arm stop the hand.
        non_arm=[_dominant(v,ob) is None or not _arm_bone(_dominant(v,ob)) for v in me.vertices]
        add(ob,me,ev.matrix_world,non_arm)
        ev.to_mesh_clear()
    if not faces:return None
    return BVHTree.FromPolygons(pts,faces)

def _movers():
    """Arm-dominated skin verts -> (world pos, dominant bone)."""
    deps=bpy.context.evaluated_depsgraph_get()
    out=[]
    for ob in s.objects:
        if ob.type!='MESH' or ob.hide_render or not ob.name.startswith('Host.'):continue
        if ob.get('castFitSource') or ob.get('castGarmentSource'):continue
        ev=ob.evaluated_get(deps);me=ev.to_mesh()
        mw=ev.matrix_world
        for v in me.vertices:
            b=_dominant(v,ob)
            if b and _arm_bone(b):out.append((mw@v.co,b))
        ev.to_mesh_clear()
    return out

colliders=_colliders()
if colliders is None:print('CONTACT_SKIP no colliders')
else:
    bones=rig.pose.bones
    inv_rig=rig.matrix_world.inverted().to_3x3()
    for _pass in range(PASSES):
        movers=_movers()
        corr={}
        hits=0
        for p,b in movers:
            hit=colliders.find_nearest(p)
            if hit[0] is None or hit[3]>0.025:continue
            surface,normal=hit[0],hit[1]
            signed=(p-surface).dot(normal)
            if signed>=MARGIN:continue
            push=min(MARGIN-signed,MAX_PUSH)
            corr.setdefault(b,[Vector((0,0,0)),0]);corr[b][0]+=normal*push;corr[b][1]+=1;hits+=1
        if not hits:
            if _pass==0:print('CONTACT_CLEAN',flush=True)
            break
        applied=0
        for b,(vec,n) in corr.items():
            if b not in bones:continue
            delta=vec/n
            if delta.length>MAX_PUSH:delta=delta.normalized()*MAX_PUSH
            pb=bones[b]
            # world-space correction -> armature space -> bone-local pose translation
            local=pb.bone.matrix_local.to_3x3().inverted()@(inv_rig@delta)
            pb.location+=local;applied+=1
        bpy.context.view_layer.update()
        print(f'CONTACT_FIX pass{_pass} movers={hits} bones={applied}',flush=True)
