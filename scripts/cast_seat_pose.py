"""Seated leg shaping on baked rig channels: bring the knees (and feet) together.

A garment that cannot follow open knees (skirts, dresses) asks for a knee gap in hip
widths. Per frame, each thigh swings about the hip so its knee lands at that gap on the
knees' own midline, then each shin swings about the knee for the foot gap; bone lengths
and the feet's orientation are kept. Frames already narrower are left alone, and the
shaping fades in with how seated the frame is (thigh pitch), so standing and walking
frames of a sit-down or stand-up keep their own stance.

With a seat height (from the chair descriptor) the pelvis is placed on the seat and each
leg is solved as a two-bone chain so the feet stay planted on the floor; without one the
hips settle until the feet touch the floor.
"""
import bpy,math
from mathutils import Matrix,Vector

def _seatedness(pb):
    up=Vector((0,0,1));w=1
    for side in 'LR':
        b=pb[f'upperleg01.{side}'];a=math.degrees((b.tail-b.head).angle(-up)) if (b.tail-b.head).length else 0
        w=min(w,max(0,min(1,(a-35)/40)))
    return w

def _swing(pb,top,joint,gap,hw,weight=1):
    jL,jR=pb[joint+'.L'].head.copy(),pb[joint+'.R'].head.copy()
    if gap is None or weight<=0 or (jL-jR).length<=gap*hw:return
    gap=((jL-jR).length+(gap*hw-(jL-jR).length)*weight)/hw
    mid=(jL+jR)/2;ax=(jL-jR).normalized()
    for side,sign in(('L',1),('R',-1)):
        b=pb[f'{top}.{side}'];foot=pb[f'foot.{side}'];keep=foot.matrix.to_3x3()
        pivot=b.head.copy();j=pb[f'{joint}.{side}'].head-pivot
        t=mid+ax*sign*gap*hw/2-pivot;t=t.normalized()*j.length
        r=j.rotation_difference(t).to_matrix().to_4x4()
        b.matrix=Matrix.Translation(pivot)@r@Matrix.Translation(-pivot)@b.matrix;bpy.context.view_layer.update()
        m=keep.to_4x4();m.translation=foot.matrix.translation;foot.matrix=m;bpy.context.view_layer.update()

def _plant(pb,side,target):
    """Two-bone solve (hip, knee, foot) keeping the current bend plane and foot orientation."""
    th,sh,ft=pb[f'upperleg01.{side}'],pb[f'lowerleg01.{side}'],pb[f'foot.{side}']
    H,K,F=th.head.copy(),sh.head.copy(),ft.head.copy();keep=ft.matrix.to_3x3()
    a,b=(K-H).length,(F-K).length;d=max(abs(a-b)+1e-4,min(a+b-1e-4,(target-H).length))
    u=(target-H).normalized();n=(K-H).cross(F-H)
    if n.length<1e-6:return
    v=n.normalized().cross(u);al=math.acos(max(-1,min(1,(a*a+d*d-b*b)/(2*a*d))))
    k2=H+(u*math.cos(al)+v*math.copysign(math.sin(al),(K-H).dot(v)))*a
    r=(K-H).rotation_difference(k2-H).to_matrix().to_4x4()
    th.matrix=Matrix.Translation(H)@r@Matrix.Translation(-H)@th.matrix;bpy.context.view_layer.update()
    K,F=sh.head.copy(),ft.head.copy();r=(F-K).rotation_difference(H+u*d-K).to_matrix().to_4x4()
    sh.matrix=Matrix.Translation(K)@r@Matrix.Translation(-K)@sh.matrix;bpy.context.view_layer.update()
    m=keep.to_4x4();m.translation=ft.matrix.translation;ft.matrix=m;bpy.context.view_layer.update()

def narrow(rig,values,frames,knee_gap,foot_gap=None,seat_height=None,seat_offset=0.09):
    """values: {(data_path,index):[value per frame]} as built by cast-gesture-timeline.py."""
    pb=rig.pose.bones;chans={}
    for (p,i),v in values.items():
        if p.startswith('pose.bones["') and p.split('"')[1] in pb:chans.setdefault((p.split('"')[1],p.rsplit('.',1)[1]),{})[i]=v
    legs=[f'{b}.{s}' for b in('upperleg01','upperleg02','lowerleg01','lowerleg02','foot') for s in 'LR']
    ad=rig.animation_data;keep=(ad.action,ad.action_slot) if ad else None
    if ad:ad.action=None
    prev={};changed=0;bones=rig.data.bones
    floor=min(bones['foot.L'].head_local.z,bones['foot.R'].head_local.z)
    root=chans.get(('root','location'));up_local=bones['root'].matrix_local.to_3x3().inverted()@Vector((0,0,1))
    anchor_xy=None  # seat keeps the pelvis over the same spot for the whole take
    try:
        for k,_ in enumerate(frames):
            for (b,prop),ch in chans.items():
                arr=getattr(pb[b],prop)
                for i,v in ch.items():arr[i]=v[k]
            bpy.context.view_layer.update()
            hw=(pb['upperleg01.L'].head-pb['upperleg01.R'].head).length
            before=(pb['lowerleg01.L'].head-pb['lowerleg01.R'].head).length
            w=_seatedness(pb)
            _swing(pb,'upperleg01','lowerleg01',knee_gap,hw,w);_swing(pb,'lowerleg01','foot',foot_gap,hw,w)
            changed+=(pb['lowerleg01.L'].head-pb['lowerleg01.R'].head).length<before-1e-4
            if seat_height is not None and root:
                # pelvis onto the seat, feet kept where they are, lowest foot on the floor.
                # Root x/y is pinned to the first frame: clips that slide or lift the
                # hips would otherwise walk the seated body off the chair. The pin is
                # unconditional because a seat block means the take is seated throughout.
                cur=(rig.matrix_world@pb['root'].head)
                if anchor_xy is None:anchor_xy=cur.xy.copy()
                inv=rig.matrix_world.inverted().to_3x3()
                feet={sd:pb[f'foot.{sd}'].head.copy() for sd in 'LR'};drop=min(f.z for f in feet.values())-floor
                da=inv@Vector((anchor_xy.x-cur.x,anchor_xy.y-cur.y,seat_height+seat_offset-cur.z))
                d=bones['root'].matrix_local.to_3x3().inverted()@da
                for i in range(3):
                    if i in root:root[i][k]+=d[i]
                pb['root'].location+=d;bpy.context.view_layer.update()
                for sd,f in feet.items():_plant(pb,sd,f-Vector((0,0,drop*w)))
                changed+=1
            # seated feet rest on the floor: the hips settle by however far the feet float
            lift=min(pb['foot.L'].head.z,pb['foot.R'].head.z)-floor
            if seat_height is None and root and w>0 and lift>0:
                d=up_local*(-lift*w)
                for i in range(3):
                    if i in root:root[i][k]+=d[i]
                pb['root'].location+=d;bpy.context.view_layer.update()
            for b in legs:
                for prop in('rotation_quaternion','rotation_euler'):
                    ch=chans.get((b,prop))
                    if not ch:continue
                    val=list(getattr(pb[b],prop))
                    if prop=='rotation_quaternion' and b in prev and sum(x*y for x,y in zip(val,prev[b]))<0:val=[-x for x in val]
                    if prop=='rotation_quaternion':prev[b]=val
                    for i,v in ch.items():v[k]=val[i]
    finally:
        if keep:ad.action,ad.action_slot=keep
    return changed
