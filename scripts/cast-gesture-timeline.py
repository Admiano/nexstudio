"""Assemble a new rig action from named clips of the original take.

Usage: blender -b scene.blend --python cast-gesture-timeline.py -- timeline.json out.blend
timeline.json: {"sequence": [{"clip": "welcome"}, {"idle": 36}, ...], "idleBase": optional Mixamo clip idles play on (seated)}
The original action is left untouched; the new action is assigned to the rig.
"""
import bpy,sys,json,math,hashlib,struct
from mathutils import Vector
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];timeline_path,out=args[:2]
LIB=json.loads((Path(__file__).resolve().parents[1]/'engine_sources/makehuman-lineart/character_system/gesture-clips.json').read_text())
timeline=json.loads(Path(timeline_path).read_text())
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE' and o.animation_data and o.animation_data.action and o.animation_data.action.name==LIB['source']['action'])
src=rig.animation_data.action;src_slot=rig.animation_data.action_slot

def channelbag(action,slot):
    for layer in action.layers:
        for strip in layer.strips:
            cb=strip.channelbag(slot)
            if cb:return cb
    raise RuntimeError('NO_CHANNELBAG:'+action.name)
def digest(cb):
    h=hashlib.sha256()
    for fc in sorted(cb.fcurves,key=lambda f:(f.data_path,f.array_index)):
        h.update(f'{fc.data_path}[{fc.array_index}]'.encode())
        for k in fc.keyframe_points:h.update(struct.pack('dd',*k.co))
    return h.hexdigest()
source=channelbag(src,src_slot);before=digest(source)
blend=int(timeline.get('blendFrames',LIB['blendFrames']))

chan={(fc.data_path,fc.array_index):fc for fc in source.fcurves}
rest_frame=LIB['idle']['ranges'][0][0]
def default(key):
    fc=chan.get(key)
    if fc:return fc.evaluate(rest_frame)
    return 1.0 if key[0].endswith(('rotation_quaternion','scale')) and (key[1]==0 or key[0].endswith('scale')) else 0.0
def source_sampler(fn):
    return lambda key,k:(chan[key].evaluate(fn(k)) if key in chan else default(key))
MX=None;mx_cache={}
def mixamo_sampler(clip,sp):
    """Retargeted Mixamo clip; channels it does not drive hold the idle pose."""
    global MX
    if MX is None:
        sys.path.insert(0,str(Path(__file__).resolve().parent));import cast_mixamo_retarget as mod
        MX=(mod,mod.load(Path(__file__).resolve().parents[1]/LIB['mixamo']['library']))
    mod,lib=MX
    if clip['mixamo'] not in mx_cache:mx_cache[clip['mixamo']]=mod.retarget(rig,lib,clip['mixamo'],rest_frame,bpy.context.scene,LIB['mixamo'].get('gain'),LIB['mixamo'].get('hold'),{'left':'Right','right':'Left'}.get(clip.get('hands')),LIB['mixamo'].get('smooth',0),bool(clip.get('legs')),anchor=clip.get('posture')=='seated')
    vals=mx_cache[clip['mixamo']];a,b=clip.get('frames',[1,lib['clips'][clip['mixamo']]['frames']])
    pad=int(LIB['mixamo'].get('padFrames',0));last=(b-a)/sp
    def sample(key,k):
        if key not in vals:return default(key)
        # pad frames hold the first/last pose so long blends fit around short clips
        x=a-1+min(max(k-pad,0),last)*sp;i=min(int(x),b-2);t=x-i;v=vals[key];return v[i]*(1-t)+v[i+1]*t
    return sample,a,b
mixamo_keys=set()
items=[]
for i,step in enumerate(timeline['sequence']):
    sp=float(timeline.get('style',{}).get('speed',1))
    if 'clip' in step:
        clip=LIB['clips'][step['clip']]
        if 'mixamo' in clip:
            csp=sp*clip.get('tempo',1);fn,a,b=mixamo_sampler(clip,csp);mixamo_keys|=set(mx_cache[clip['mixamo']])
            items.append(('clip',step['clip'],fn,max(2,round((b-a)/csp))+2*int(LIB['mixamo'].get('padFrames',0))))
        else:
            a,b=clip['frames'];items.append(('clip',step['clip'],source_sampler(lambda k,a=a,sp=sp:a+k*sp),round((b-a+1)/sp)))
    elif 'source' in step:
        a,b=step['source'];items.append(('source',f'source{a}-{b}',source_sampler(lambda k,a=a:a+k),b-a+1))
    elif 'idle' in step and (step.get('base') or timeline.get('idleBase')):
        # idle on a Mixamo base clip (e.g. seated), played back and forth
        base=LIB['clips'][step.get('base') or timeline['idleBase']];fn,a,b=mixamo_sampler(base,1);mixamo_keys|=set(mx_cache[base['mixamo']])
        n=int(step['idle'])+48;span=max(1,b-a);pad=int(LIB['mixamo'].get('padFrames',0))
        items.append(('idle',f'idle{n}',lambda key,k,fn=fn,span=span,pad=pad:fn(key,pad+(k%span if (k//span)%2==0 else span-k%span)),n))
    elif 'idle' in step:
        a,b=LIB['idle']['ranges'][step.get('range',0)];n=int(step['idle'])+48;span=b-a
        items.append(('idle',f'idle{n}',source_sampler(lambda k,a=a,span=span:a+(k%span if (k//span)%2==0 else span-k%span)),n))
    else:raise ValueError('BAD_STEP:'+json.dumps(step))
keys=list(chan)+sorted(mixamo_keys-set(chan))
# Root continuity: each clip's horizontal root path starts where the previous one
# ended, so a seated clip after a sit-down stays on the seat instead of sliding.
ROOT=[('pose.bones["root"].location',i) for i in range(3)]
if all(k in keys for k in ROOT) and 'root' in rig.data.bones:
    up=rig.data.bones['root'].matrix_local.to_3x3().inverted()@Vector((0,0,1));up.normalize()
    off=Vector((0,0,0))
    for i in range(1,len(items)):
        pk,pn,pf,pl=items[i-1];k,nm,fn,n=items[i]
        end=Vector([pf(key,pl-1) for key in ROOT])+off;start=Vector([fn(key,0) for key in ROOT])
        d=end-start;off=d-up*d.dot(up)
        items[i]=(k,nm,(lambda key,kk,fn=fn,o=off.copy():fn(key,kk)+(o[key[1]] if key in ROOT else 0)),n)
# Blend length per join grows with how far apart the two poses are, so a clip
# that ends mid-gesture eases back instead of snapping.
def join(a,b):
    (fa,ka),(fb,kb)=a,b
    diff=max(abs(fa(key,ka)-fb(key,kb)) for key in keys if 'rotation' in key[0])
    return math.ceil(diff/float(timeline.get('blendRadPerFrame',.025)))
joins=[0]+[min(max(blend,join((p[2],p[3]-1),(q[2],0))),24,p[3]//2,q[3]//2) for p,q in zip(items,items[1:])]+[0]
# idle holds keep their requested length outside the blends
items=[(k,nm,fn,(int(timeline['sequence'][i]['idle'])+joins[i]+joins[i+1] if k=='idle' else n)) for i,(k,nm,fn,n) in enumerate(items)]
placed=[];t=1
for i,(kind,name,fn,n) in enumerate(items):
    t-=joins[i];placed.append((t,n,fn,name,joins[i],joins[i+1]));t+=n
total=placed[-1][0]+placed[-1][1]-1
smooth=lambda x:x*x*(3-2*x)
def weights(frame):
    out=[]
    for start,n,fn,name,bin_,bout in placed:
        k=frame-start
        if not 0<=k<n:continue
        w=1.0
        if bin_ and k<bin_:w=smooth((k+1)/(bin_+1))
        if bout and k>=n-bout:w=1-smooth((k-(n-bout)+1)/(bout+1))
        out.append((w,fn,k))
    s=sum(o[0] for o in out);return [(w/s,fn,k) for w,fn,k in out]

name=timeline.get('name','gestureTimeline')
act=bpy.data.actions.new(f'Host.{name}');slot=act.slots.new(id_type='OBJECT',name=rig.name)
cb=act.layers.new('Layer').strips.new(type='KEYFRAME').channelbag(slot,ensure=True)
frames=range(1,total+1);plan=[weights(f) for f in frames]
values={}
for key in keys:
    values[key]=[sum(w*fn(key,k) for w,fn,k in p) for p in plan]
# gesture size: scale arm channels about the resting pose
size=float(timeline.get('style',{}).get('size',1))
if size!=1:
    arm=('clavicle','shoulder01','upperarm','lowerarm','wrist')
    for key in keys:
        bone=key[0].split('"')[1] if '"' in key[0] else ''
        if not bone.startswith(arm):continue
        r=default(key);vals=values[key]
        for i,v in enumerate(vals):vals[i]=r+size*(v-r)
for (path,idx),vals in list(values.items()):
    if path.endswith('rotation_quaternion') and idx==0:
        group=[values.get((path,i)) for i in range(4)]
        if all(group):
            for f in range(len(vals)):
                n=math.sqrt(sum(g[f]**2 for g in group)) or 1
                for g in group:g[f]/=n
seat=timeline.get('seat') or {}
seated_frames=0
if seat.get('kneeGap'):
    sys.path.insert(0,str(Path(__file__).resolve().parent));import cast_seat_pose
    seated_frames=cast_seat_pose.narrow(rig,values,frames,float(seat['kneeGap']),seat.get('footGap'))
def idle_layer(cfg):
    import random
    rng=random.Random(int(cfg.get('seed',1)));fps=LIB['source']['fps']
    def noise(amp,lo=.05,hi=.22):
        waves=[(rng.uniform(lo,hi),rng.uniform(0,2*math.pi),rng.uniform(.5,1)) for _ in range(3)];norm=sum(w[2] for w in waves)
        return lambda f:amp*sum(a*math.sin(2*math.pi*fr*f/fps+ph) for fr,ph,a in waves)/norm
    breath,sway=float(cfg.get('breath',1)),float(cfg.get('sway',1))
    period=rng.uniform(3.6,4.6)*fps;bph=rng.uniform(0,2*math.pi)
    br=lambda f:breath*.006*math.sin(2*math.pi*f/period+bph)
    side,twist,lean=noise(.03*sway),noise(.022*sway),noise(.01*sway)
    nod,tilt=noise(.012*sway,.08,.3),noise(.01*sway,.08,.3)
    # bone -> per-frame local (x forward bend, y twist, z side bend) offsets
    # MakeHuman chain runs root>spine05 (pelvis)>...>spine01 (chest)>neck01
    quat={'spine05':lambda f:(lean(f),twist(f)*.5,side(f)),'spine03':lambda f:(0,twist(f)*.5,0),'spine01':lambda f:(br(f),0,0)}
    euler={'neck01':lambda f:(nod(f)-lean(f)-1.7*br(f),0,tilt(f)-side(f)*.6)}
    from mathutils import Quaternion,Euler
    touched=[]
    for bone,fn in quat.items():
        path=f'pose.bones["{bone}"].rotation_quaternion';ch=[values.get((path,i)) for i in range(4)]
        if not all(ch):continue
        for k,f in enumerate(frames):
            q=Quaternion([c[k] for c in ch])@Euler(fn(f),'XYZ').to_quaternion()
            for i in range(4):ch[i][k]=q[i]
        touched.append(bone)
    for bone,fn in euler.items():
        path=f'pose.bones["{bone}"].rotation_euler'
        for i in range(3):
            ch=values.get((path,i))
            if ch is None:continue
            for k,f in enumerate(frames):ch[k]+=fn(f)[i]
        touched.append(bone)
    return touched
idle_bones=idle_layer(timeline['idleLayer']) if timeline.get('idleLayer') else []
for (path,idx),vals in values.items():
    fc=cb.fcurves.new(path,index=idx);fc.keyframe_points.add(len(vals))
    co=[c for f,v in zip(frames,vals) for c in (f,v)];fc.keyframe_points.foreach_set('co',co)
    for k in fc.keyframe_points:k.interpolation='LINEAR'
    fc.update()
act.use_fake_user=True
def face_copy():
    face=bpy.data.actions.get(LIB['source'].get('faceAction','baseAction'))
    keys=[k for k in bpy.data.shape_keys if k.animation_data and k.animation_data.action==face]
    if not face or not keys:return None
    copy=face.copy();copy.name=f'Face.{name}';copy.use_fake_user=True
    for k in keys:k.animation_data.action=copy
    return copy
def set_curves(action,curves):
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    key=fc.data_path.split('"')[1]
                    if key not in curves:continue
                    fc.keyframe_points.clear();fc.keyframe_points.add(total)
                    fc.keyframe_points.foreach_set('co',[c for fr in range(1,total+1) for c in (fr,curves[key][fr])]);fc.update()
def blink_layer(cfg,action):
    """Replace the baked blinks with seeded ones."""
    import random
    rng=random.Random(int(cfg.get('seed',1))+101);fps=LIB['source']['fps']
    curve=[0.0]*(total+2);f=rng.uniform(.6,2.0)*fps;events=[]
    while f<total-6:
        events.append(int(f))
        for k,v in enumerate((.35,.85,1,.75,.4,.12)):
            if int(f)+k<=total:curve[int(f)+k]=max(curve[int(f)+k],v)
        f+=(rng.uniform(.3,.6) if rng.random()<.15 else rng.uniform(2.2,5.5))*fps
    set_curves(action,{'!ex-eyeBlinkLeft':curve,'!ex-eyeBlinkRight':curve})
    return events
def lip_layer(cfg,action):
    """Drive the existing mouth shape keys from Rhubarb mouth cues (local, CPU)."""
    cues=json.loads(Path(cfg['rhubarb']).read_text())['mouthCues'];fps=LIB['source']['fps']
    shapes=LIB['visemes'];keys=sorted({k for v in shapes.values() for k in v})
    lead=int(cfg.get('leadFrames',1));start=int(cfg.get('startFrame',1))
    target={k:[0.0]*(total+2) for k in keys}
    for c in cues:
        a=start+round(c['start']*fps)-lead;b=start+round(c['end']*fps)-lead
        for fr in range(max(1,a),min(total,b)+1):
            for k in keys:target[k][fr]=min(1.0,shapes[c['value']].get(k,0.0)*(float(cfg.get('mouthOpen',1)) if k=='!ex-jawOpen' else 1))
    # two-pole smoothing toward each target: soft co-articulation, no pops
    out={};a=float(cfg.get('response',.5))
    for k in keys:
        v1=v2=0.0;row=[0.0]*(total+2)
        for fr in range(1,total+1):
            v1+=a*(target[k][fr]-v1);v2+=a*(v1-v2);row[fr]=v2
        out[k]=row
    set_curves(action,out);return len(cues)
face=face_copy() if (timeline.get('idleLayer') or timeline.get('lipSync') or 'expressions' in timeline) else None
blinks=blink_layer(timeline['idleLayer'],face) if face and timeline.get('idleLayer') else []
cues=lip_layer(timeline['lipSync'],face) if face and timeline.get('lipSync') else 0
def expression_layer(events,action):
    """Smile/brow envelopes over a resting baseline; overlapping events take the max."""
    curves={k:[v]*(total+2) for k,v in LIB.get('expressionBaseline',{}).items()}
    for e in events:
        row=curves.setdefault(e['shape'],[0.0]*(total+2));n=max(4,int(e['frames']));up=max(2,n//4)
        for k in range(n):
            f=int(e['at'])-up+k
            if 1<=f<=total:
                x=k/up if k<up else 1-(k-up)/(n-up)
                row[f]=max(row[f],float(e['amount'])*smooth(max(0.0,min(1.0,x))))
    set_curves(action,curves);return len(events)
expressions=expression_layer(timeline['expressions'],face) if face and 'expressions' in timeline else 0
rig.animation_data.action=act;rig.animation_data.action_slot=slot
s=bpy.context.scene;s.frame_start=1;s.frame_end=total
if digest(source)!=before:raise RuntimeError('SOURCE_ACTION_MUTATED')
report={'action':act.name,'frames':total,'seconds':round(total/LIB['source']['fps'],2),'sourceDigest':before[:16],'idleLayer':idle_bones,'blinks':blinks,'lipSyncCues':cues,'expressions':expressions,'seatNarrowedFrames':seated_frames,
        'sequence':[{'name':n,'start':st,'frames':l,'blendIn':bi} for st,l,_,n,bi,_ in placed]}
bpy.ops.wm.save_as_mainfile(filepath=out,copy=True)
print('GESTURE_TIMELINE',json.dumps(report),flush=True)
