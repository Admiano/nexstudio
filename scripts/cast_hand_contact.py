"""Keep hands outside the body (and so outside the clothes lying on it).

Works on baked rig channels like cast_seat_pose. Pass 1 poses each frame, finds hand
points that are inside the skin or closer to it than `clearance`, and takes the push
that would lift the deepest one clear along the skin normal. The pushes are smoothed
over time so contacts ease in and out. Pass 2 swings each upper arm about its shoulder
so the wrist moves by that push; the forearm and hand keep their shape.
"""
import bpy,math
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree

HAND=('wrist','finger','metacarpal','thumb')
ARM=HAND+('lowerarm','upperarm','shoulder','clavicle')

def _apply(pb,chans,k):
    for (b,prop),ch in chans.items():
        arr=getattr(pb[b],prop)
        for i,v in ch.items():arr[i]=v[k]
    bpy.context.view_layer.update()

def clear_hands(rig,body,values,frames,clearance=0.015,sigma=3,passes=3,max_swing=.3):
    pb=rig.pose.bones;chans={}
    for (p,i),v in values.items():
        if p.startswith('pose.bones["') and p.split('"')[1] in pb:chans.setdefault((p.split('"')[1],p.rsplit('.',1)[1]),{})[i]=v
    names={g.index:g.name for g in body.vertex_groups}
    def side_part(v,keys):
        tot={}
        for g in v.groups:
            n=names[g.group]
            if any(k in n for k in keys):tot[n[-1]]=tot.get(n[-1],0)+g.weight
        s=max(tot,key=tot.get) if tot else None
        return s if s and tot[s]>.5 else None
    hand={i:side_part(v,HAND) for i,v in enumerate(body.data.vertices)};hand={i:s for i,s in hand.items() if s in ('L','R')}
    arm={i for i,v in enumerate(body.data.vertices) if side_part(v,ARM)}
    masks=[m for m in body.modifiers if m.show_viewport and (m.type=='MASK' or m.name.startswith('Delete.'))]
    for m in masks:m.show_viewport=False
    ad=rig.animation_data;keep=(ad.action,ad.action_slot) if ad else None
    if ad:ad.action=None
    changed=set();r=int(3*sigma)+1;w=[math.exp(-.5*(j/sigma)**2) for j in range(-r,r+1)]
    try:
        for _ in range(passes):
            push={s:[Vector() for _ in frames] for s in 'LR'}
            for k,_ in enumerate(frames):
                _apply(pb,chans,k);d=bpy.context.evaluated_depsgraph_get();e=body.evaluated_get(d);me=e.to_mesh()
                P=[e.matrix_world@v.co for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons if not any(i in arm for i in p.vertices)];e.to_mesh_clear()
                if len(P)!=len(body.data.vertices):raise RuntimeError('CAST_HAND_CONTACT_TOPOLOGY')
                skin=BVHTree.FromPolygons(P,faces);need={'L':(0,None),'R':(0,None)}
                for i,s in hand.items():
                    loc,n,_,dist=skin.find_nearest(P[i],clearance+.05)
                    if loc is None:continue
                    depth=clearance-(P[i]-loc).dot(n)
                    if depth>need[s][0]:need[s]=(depth,n)
                for s in 'LR':
                    if need[s][1] is not None:push[s][k]=rig.matrix_world.inverted().to_3x3()@(need[s][1]*need[s][0])
            if not any(v.length>1e-3 for s in 'LR' for v in push[s]):break
            for s in 'LR':
                raw=push[s];n=len(raw)
                # hold each push across its neighbourhood first so smoothing never under-lifts
                held=[max((raw[min(max(k+j,0),n-1)] for j in range(-r,r+1)),key=lambda v:v.length) for k in range(n)]
                push[s]=[sum((held[min(max(k+j,0),n-1)]*w[j+r] for j in range(-r,r+1)),Vector())/sum(w) for k in range(n)]
            prev={}
            for k,_ in enumerate(frames):
                if not any(push[s][k].length>1e-4 for s in 'LR'):continue
                _apply(pb,chans,k)
                for s in 'LR':
                    v=push[s][k]
                    if v.length<=1e-4:continue
                    ua=pb[f'upperarm01.{s}'];pivot=ua.head.copy();wr=pb[f'wrist.{s}'].head-pivot
                    # a shoulder swing only moves the wrist across the arm, so size the sideways
                    # move so that its component along the push equals the push
                    u=wr.normalized();nv=v.normalized();perp=nv-u*nv.dot(u)
                    if perp.length<1e-3:continue
                    q=wr.rotation_difference(wr+perp.normalized()*(v.length/max(perp.length,.5)))
                    # small swings per pass so a blocked hand never whips across the body
                    if q.angle>max_swing:q=Quaternion(q.axis,max_swing)
                    rot=q.to_matrix().to_4x4()
                    ua.matrix=Matrix.Translation(pivot)@rot@Matrix.Translation(-pivot)@ua.matrix;bpy.context.view_layer.update()
                    for prop in('rotation_quaternion','rotation_euler'):
                        ch=chans.get((ua.name,prop))
                        if not ch:continue
                        val=list(getattr(ua,prop))
                        if prop=='rotation_quaternion':
                            ref=prev.get(ua.name) or [ch[i][k-1] if k else ch[i][k] for i in range(4)]
                            if sum(a*b for a,b in zip(val,ref))<0:val=[-x for x in val]
                            prev[ua.name]=val
                        for i,c in ch.items():c[k]=val[i]
                    changed.add(k)
    finally:
        for m in masks:m.show_viewport=True
        if keep:ad.action,ad.action_slot=keep
    return len(changed)
