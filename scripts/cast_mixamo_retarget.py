"""Map Mixamo motion (see cast-mixamo-extract.py) onto a MakeHuman Host.rig.

Each Mixamo bone drives one rig bone plus rigid followers. The rig is first
posed into the Mixamo rest (T-pose) by aligning bone directions, then every
frame applies the stored world-space rotation delta and converts it back to the
rig's local channels, so the same library fits any presenter body.
"""
import gzip,json
from mathutils import Quaternion,Matrix,Vector

def load(path):
    with gzip.open(path,'rt') as fh:return json.load(fh)

def target_map():
    m={'Spine':('spine04','spine02',['spine03']),'Spine1':('spine02','spine01',[]),'Spine2':('spine01','neck01',[]),
       'Neck':('neck01','head',['neck02','neck03']),'Head':('head',None,[])}
    m['Hips']=('root','spine04',['spine05','pelvis.L','pelvis.R'])
    for s,x in(('Left','L'),('Right','R')):
        m[f'{s}UpLeg']=(f'upperleg01.{x}',f'lowerleg01.{x}',[f'upperleg02.{x}'])
        m[f'{s}Leg']=(f'lowerleg01.{x}',f'foot.{x}',[f'lowerleg02.{x}'])
        m[f'{s}Foot']=(f'foot.{x}',None,[])
        m[f'{s}Shoulder']=(f'clavicle.{x}',f'upperarm01.{x}',[f'shoulder01.{x}'])
        m[f'{s}Arm']=(f'upperarm01.{x}',f'lowerarm01.{x}',[f'upperarm02.{x}'])
        m[f'{s}ForeArm']=(f'lowerarm01.{x}',f'wrist.{x}',[f'lowerarm02.{x}'])
        m[f'{s}Hand']=(f'wrist.{x}',f'finger3-1.{x}',[f'metacarpal{i}.{x}' for i in range(1,5)])
        for n,f in enumerate(('Thumb','Index','Middle','Ring','Pinky'),1):
            for i in(1,2,3):m[f'{s}Hand{f}{i}']=(f'finger{n}-{i}.{x}',f'finger{n}-{i+1}.{x}' if i<3 else None,[])
    return m

def _frame(d,side):
    d=d.normalized();y=(side-d*side.dot(d)).normalized();return Matrix((d,y,d.cross(y))).transposed()

def _hand(src):
    return 'Left' if src.startswith('Left') else 'Right' if src.startswith('Right') else None

def retarget(rig,lib,key,rest_frame,scene,gain=None,hold=None,idle_side=None,smooth=0,legs=False):
    """Return {(data_path,index):[value per clip frame]} for the driven rig bones.
    gain scales a Mixamo bone's world delta, keyed without side ('Shoulder': .6).
    hold pulls a bone's pose toward the presenter's idle pose (Head .5 keeps gaze near
    camera); idle_side ('Left'/'Right', hold 'idleArm') does the same for the arm a
    one-handed clip does not use, so it stops sagging with the source torso.
    smooth is a Gaussian sigma in frames that removes mocap jitter.
    legs drives hips, legs and hip translation (seated, walking, weight shift);
    otherwise the presenter stays planted on the idle pose below the spine."""
    clip=lib['clips'][key];n=clip['frames'];bones=rig.data.bones;rq=rig.matrix_world.to_quaternion()
    mw=rig.matrix_world;head=lambda b:mw@bones[b].head_local
    def tdir(b,end):return (head(end)-head(b)) if end else (mw@bones[b].tail_local-head(b))
    lower=lambda k:k=='Hips' or k.endswith(('UpLeg','Leg','Foot'))
    tmap={k:v for k,v in target_map().items() if k in clip['q'] and v[0] in bones and (legs or not lower(k))}
    swing,driver={},{}
    for src,(tb,end,follow) in tmap.items():
        sd=Vector(lib['rest'][src]['dir']);td=tdir(tb,end);h=_hand(src)
        if h and (src.endswith('Hand') or 'Hand' in src):
            x='L' if h=='Left' else 'R'
            ss=Vector(lib['rest'][f'{h}Hand']['side']);ts=head(f'finger5-1.{x}')-head(f'finger2-1.{x}')
            r=(_frame(sd,ss)@_frame(td,ts).inverted()).to_quaternion()
        else:r=td.normalized().rotation_difference(sd.normalized())
        for b in [tb]+[f for f in follow if f in bones]:swing[b]=r;driver[b]=src
    rest_w={b:(mw@bones[b].matrix_local).to_quaternion() for b in swing}
    M={b:swing[b]@rest_w[b] for b in swing}
    cur=scene.frame_current;scene.frame_set(rest_frame)
    idle_pose={pb.name:pb.matrix.to_quaternion() for pb in rig.pose.bones}
    idle_basis={pb.name:(pb.rotation_quaternion.copy(),pb.rotation_euler.copy()) for pb in rig.pose.bones}
    scene.frame_set(cur)
    order=[];stack=[b for b in bones if b.parent is None]
    while stack:
        b=stack.pop(0);order.append(b);stack[:0]=list(b.children)
    driven=[b for b in order if b.name in swing]
    out={};prev={}
    for f in range(n):
        pose=dict(idle_pose)
        for b in driven:
            q=Quaternion(clip['q'][driver[b.name]][4*f:4*f+4]);g=(gain or {}).get(driver[b.name].replace('Left','').replace('Right',''),1)
            if g!=1:q=Quaternion((1,0,0,0)).slerp(q,g)
            W=q@M[b.name];src=driver[b.name];h=(hold or {}).get(src.replace('Left','').replace('Right',''),0)
            if idle_side and src.startswith(idle_side):h=max(h,(hold or {}).get('idleArm',.8))
            pose[b.name]=(rq.inverted()@W).slerp(idle_pose[b.name],h) if h else rq.inverted()@W
        for b in driven:
            pb=rig.pose.bones[b.name];rl=b.matrix_local.to_quaternion()
            if b.parent:
                pl=b.parent.matrix_local.to_quaternion();basis=rl.inverted()@pl@pose[b.parent.name].inverted()@pose[b.name]
            else:basis=rl.inverted()@pose[b.name]
            path=f'pose.bones["{b.name}"]'
            if pb.rotation_mode=='QUATERNION':
                ref=prev.get(b.name,idle_basis[b.name][0])
                if basis.dot(ref)<0:basis.negate()
                prev[b.name]=basis;vals=tuple(basis);p=path+'.rotation_quaternion'
            else:
                e=basis.to_euler(pb.rotation_mode,prev.get(b.name,idle_basis[b.name][1]));prev[b.name]=e;vals=tuple(e);p=path+'.rotation_euler'
            for i,v in enumerate(vals):out.setdefault((p,i),[]).append(v)
    if legs and clip.get('hips') and 'root' in bones:
        # hip offset scaled by hip height, expressed in the root bone's rest frame
        k=(mw@bones['root'].head_local).z/max(.1,lib['rest']['Hips']['pos'][2]);R=bones['root'].matrix_local.to_3x3().inverted()
        hp=clip['hips']
        for f in range(n):
            d=R@(rq.inverted()@Vector(hp[3*f:3*f+3]))*k
            for i in range(3):out.setdefault(('pose.bones["root"].location',i),[]).append(d[i])
    if smooth>0:
        import numpy as np
        r=int(3*smooth)+1;k=np.exp(-.5*(np.arange(-r,r+1)/smooth)**2);k/=k.sum()
        for ch,v in out.items():
            out[ch]=np.convolve(np.pad(np.asarray(v),r,mode='edge'),k,mode='valid').tolist()
    return out
