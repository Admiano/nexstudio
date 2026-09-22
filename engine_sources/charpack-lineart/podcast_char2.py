"""Render one Blender Studio character as a line-art podcast guest (v2: face + hands + posture performance).
usage: blender -b <file> --python podcast_char2.py -- <char> <outdir> <fstart> <fend> [still|anim] [closeup]
Deterministic: every control is driven from python curves, no physics/randomness.
"""
import bpy, sys, math, os, time
from mathutils import Matrix, Vector

argv=sys.argv[sys.argv.index('--')+1:]
CHAR, OUT, F0, F1 = argv[0], argv[1], int(argv[2]), int(argv[3])
STILL = len(argv)>4 and argv[4]=='still'
CLOSEUP = 'closeup' in argv
FPS=24
scene=bpy.context.scene

# ---------- character adapters ----------
CH={
 'rain':dict(rig='RIG-rain', seat=('A',-0.62, 35), accent='#2E5EAA',
  props=('Properties_IKFK',{'ik_arm_left':0,'ik_arm_right':0,'ik_leg_left':0,'ik_leg_right':0,'ik_spine':0,'ik_fingers_left':0,'ik_fingers_right':0}),
  charprops=('Properties_Character_Rain',{'Quality':0,'Scarf':False}),
  b=dict(head='FK-Head',neck='FK-Neck',chest='FK-Chest',spine='FK-Spine',pelvis='MSTR-Pelvis',jaw='MSTR-Jaw',
   upperarm='FK-Upperarm.{S}',forearm='FK-Forearm.{S}',hand='FK-Hand.{S}',thigh='FK-Thigh.{S}',shin='FK-Shin.{S}',foot='FK-Foot.{S}',
   finger='FK-{F}{N}.{S}',thumb='FK-Thumb{N}.{S}'),
  face=dict(lid_upper='ACT-Eyelid_Upper.{S}', lid_close=-0.030, brow='MSTR-Eyebrow.{S}', brow_up=0.012,
            eyes='TGT-Eyes', gaze=0.10, mouth='MSTR-Mouth', lip_bot='MSTR-LowerLip', lip_top='MSTR-UpperLip',
            lip_open=0.016, corner='ACT-Lips_Corner.{S}', corner_up=0.008, jaw_sign=-1, jaw_deg=20),
  fingers=('Index','Middle','Ring','Pinky'),
  ink=('hair','eyebrow','eyelash','shoe','jeans','eyedot','gums','tongue','teeth','viewport_black','hairband','laces'),
  accent_mats=('MAT-rain.top',), hide=('GEO-rain-eye_cornea','GEO-rain-scarf'),
  head_mesh='GEO-rain-head', lip_groups=('DEF-Lip_Bot_',), hand_scale=1.0, head_scale=1.22, yaw_bias=0,
  seat_drop=0.12),
 'snow':dict(rig='RIG-Snow', seat=('B',0.62,-35), accent='#B5432B',
  props=('Properties',{'ik_left_upperarm':0,'ik_right_upperarm':0,'ik_left_thigh':0,'ik_right_thigh':0,'ik_spine':0}),
  charprops=('Properties_Character_Snow',{'Quality':0}),
  b=dict(head='FK-Head',neck='FK-Neck',chest='FK-Chest',spine='FK-Spine',pelvis='TORSO-Spine',jaw='Jaw',
   upperarm='FK-UpperArm.{S}',forearm='FK-Forearm.{S}',hand='FK-Wrist.{S}',thigh='FK-Thigh.{S}',shin='FK-Knee.{S}',foot='FK-Foot.{S}',
   finger='FK-Finger_{F}{N}.{S}',thumb='FK-Finger_Thumb{N}.{S}'),
  face=dict(lid_upper='MSTR-Eyelid_Upper.{S}', lid_close=-0.040, brow='MSTR-Eyebrow.{S}', brow_up=0.012,
            eyes='TGT-Eyes', gaze=0.10, mouth='MSTR-Mouth', lip_bot='MSTR-Lip_Bottom', lip_top='MSTR-Lip_Top',
            lip_open=0.010, corner='ACT-Lips_Corner.{S}', corner_up=0.008, jaw_sign=+1, jaw_deg=11),
  fingers=('Index','Middle','Ring','Pinky'),
  ink=('hair','eye_dot','eyes_pupil','eyes_iris','pants','shoe','gums','tongue','teeth','Dots Stroke'),
  accent_mats=('snow.shirt',), hide=('GEO-snow_eye_corneas',),
  head_mesh='GEO-snow-head', lip_groups=(), hand_scale=0.84, head_scale=1.18, yaw_bias=-12,
  seat_drop=0.21),
}[CHAR]
rig=bpy.data.objects[CH['rig']]
B=CH['b']; FC=CH['face']

def lin(h):
    r,g,b=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    f=lambda c:c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    return (f(r),f(g),f(b),1)
PAPER=lin('#F6F3EC'); INK=lin('#232220'); ACCENT=lin(CH['accent'])

# ---------- materials -> flat emission ----------
def flat(mat,rgba):
    nt=mat.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value=rgba
    o=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0],o.inputs[0])
for m in bpy.data.materials:
    if not m.node_tree or m.grease_pencil: continue
    n=m.name.lower()
    if m.name in CH['accent_mats']: flat(m,ACCENT)
    elif any(k.lower() in n for k in CH['ink']): flat(m,INK)
    else: flat(m,PAPER)
for name in CH['hide']:
    o=bpy.data.objects.get(name)
    if o: o.hide_render=True
for o in bpy.data.objects:
    if o.type=='LIGHT': o.hide_render=True
    if o.type=='MESH':
        for md in o.modifiers:
            if md.type=='SUBSURF': md.render_levels=min(md.render_levels,1)

# lower lip gets its own (paper) material so the mouth seam renders as a material-border line
def split_lips():
    ob=bpy.data.objects.get(CH['head_mesh'])
    if not ob: print('MISSING head mesh'); return
    me=ob.data
    gidx=[g.index for g in ob.vertex_groups if any(g.name.startswith(p) for p in CH['lip_groups'])]
    if not gidx: return
    lipmat=bpy.data.materials.new('LipPaper'); lipmat.use_nodes=True; flat(lipmat,PAPER)
    if len(me.materials)==0: me.materials.append(None)
    me.materials.append(lipmat); li=len(me.materials)-1
    w=[0.0]*len(me.vertices)
    for v in me.vertices:
        for g in v.groups:
            if g.group in gidx: w[v.index]=max(w[v.index],g.weight)
    n=0
    for p in me.polygons:
        if sum(w[i] for i in p.vertices)/len(p.vertices)>0.45:
            p.material_index=li; n+=1
    print('LIPFACES',n)
if not os.environ.get('NOLIPS'): split_lips()

# ---------- strip shipped animation (keep drivers) ----------
def strip_actions(idb):
    ad=idb.animation_data if idb else None
    if not ad: return
    ad.action=None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for o in bpy.data.objects:
    strip_actions(o)
    if o.type=='MESH': strip_actions(o.data.shape_keys)
if bpy.context.object and bpy.context.object.mode!='OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
for bone_,vals in (CH['props'],CH['charprops']):
    pb=rig.pose.bones.get(bone_)
    if not pb: print('MISSING propbone',bone_); continue
    for k,v in vals.items():
        if k in pb.keys(): pb[k]=type(pb[k])(v)
        else: print('MISSING prop',k)

# ---------- bone helpers ----------
def bone(key,S='L',F='Index',N=1):
    name=B[key].format(S=S,F=F,N=N)
    pb=rig.pose.bones.get(name)
    if pb is None: print('MISSING bone',name)
    return pb
def fbone(key,S='L'):
    pb=rig.pose.bones.get(FC[key].format(S=S))
    if pb is None: print('MISSING face bone',FC[key])
    return pb
def upd(): bpy.context.view_layer.update()

def rots(ops):
    """ops: list of (pb, [(axis,deg),...]) - bones must not be ancestors of each other. One depsgraph update."""
    upd()
    for pb,rl in ops:
        if pb is None: continue
        p=pb.matrix.translation.copy()
        R=Matrix.Identity(4)
        for axis,deg in rl:
            if deg: R=Matrix.Rotation(math.radians(deg),4,axis)@R
        pb.matrix=Matrix.Translation(p)@R@Matrix.Translation(-p)@pb.matrix
def brots(pb,rl):
    """rotate a bone about its OWN current axes (X=flex, Y=twist along bone, Z=abduct), in rig space."""
    if pb is None: return
    upd()
    M=pb.matrix; p=M.translation.copy()
    R=Matrix.Identity(4)
    for axis,deg in rl:
        if not deg: continue
        ax=(M.to_3x3()@Vector((1,0,0) if axis=='X' else (0,1,0) if axis=='Y' else (0,0,1))).normalized()
        R=Matrix.Rotation(math.radians(deg),4,ax)@R
    pb.matrix=Matrix.Translation(p)@R@Matrix.Translation(-p)@M
def move_world(pb,vec):
    upd(); pb.matrix=Matrix.Translation(Vector(vec))@pb.matrix
def local_rot(pb,x=0,y=0,z=0):
    if pb is None: return
    pb.rotation_mode='XYZ'
    pb.rotation_euler=(math.radians(x),math.radians(y),math.radians(z))
def local_loc(pb,x=0,y=0,z=0):
    if pb is None: return
    pb.location=(x,y,z)

# ---------- hand poses: (index, middle, ring, pinky) x (j1,j2,j3) curl degrees; spread deg on j1 ----------
HAND={
 'rest_thigh':   dict(curl=((8,16,10),(12,22,12),(16,26,14),(20,30,16)), spread=(-4,-1,2,5), thumb=(6,4)),
 'relaxed':      dict(curl=((12,22,12),(16,28,16),(20,32,18),(26,36,20)), spread=(-3,0,3,6), thumb=(10,6)),
 'present':      dict(curl=((0,4,2),(3,8,4),(8,12,6),(12,16,8)), spread=(-9,-3,4,10), thumb=(-8,-2)),
 'point_soft':   dict(curl=((0,3,2),(30,42,28),(36,46,32),(40,50,34)), spread=(-4,0,2,4), thumb=(8,14)),
}
def lerp(a,b,u): return a+(b-a)*u
def hand_pose(S,pa,pb_,u,sgn):
    """blend hand pose pa->pb_ by u, applied as LOCAL finger rotations (bend about local X)."""
    A,Bp=HAND[pa],HAND[pb_]
    for i,F in enumerate(CH['fingers']):
        for N in (1,2,3):
            c=lerp(A['curl'][i][N-1],Bp['curl'][i][N-1],u)
            sp=lerp(A['spread'][i],Bp['spread'][i],u) if N==1 else 0
            local_rot(bone('finger',S,F,N),x=c,z=sgn*sp)
    for N in (1,2):
        t=lerp(A['thumb'][N-1],Bp['thumb'][N-1],u)
        local_rot(bone('thumb',S,N=N),x=t)

# ---------- seated posture (asymmetric per character) ----------
side,X,yawdeg=CH['seat']
inward = 1 if side=='A' else -1
rig.rotation_euler=(0,0,math.radians(yawdeg)); rig.location=(X,0,0)
IN = 'L' if inward>0 else 'R'      # arm nearer the partner (gesture arm)
OUTS = 'R' if IN=='L' else 'L'     # far arm, rests on thigh

POSTURE={
 # arm: uaY(drop from T), uaZ(elbow fwd), faX(bend), faZ(drift in), handX, handY, handZ
 'rain':dict(spine_x=-5, chest_z=6, chest_x=2,
             arm_in =(86,-24,-38,0,-10,70,0), arm_out=(80,-36,-56,-10,-14,70,10),
             leg_in=(-84,88), leg_out=(-92,96), leg_z=(4,-6), pelvis_yaw=-4),
 'snow':dict(spine_x=-9, chest_z=8, chest_x=3,
             arm_in =(84,-28,-34,2,-8,70,0), arm_out=(88,-24,-30,-6,-12,70,6),
             leg_in=(-80,84), leg_out=(-90,98), leg_z=(8,-4), pelvis_yaw=5),
}[CHAR]
if os.environ.get('POST'):
    import json; POSTURE.update(json.loads(os.environ['POST']))
GESTV=dict(ua=(30,-14), fa=(-52,10), h=(-15,-95,0))
if os.environ.get('GESTV'):
    import json; GESTV.update(json.loads(os.environ['GESTV']))

def base_pose():
    for pb in rig.pose.bones: pb.matrix_basis=Matrix.Identity(4)
    upd()
    pelvis=bone('pelvis')
    pz=pelvis.matrix.translation.z
    drop=0.43
    move_world(pelvis,(0,0,-drop))
    P=POSTURE
    rots([(pelvis,[('Z',inward*P['pelvis_yaw'])])])
    legs=[]; shins=[]
    for S in ('L','R'):
        sgn = 1 if S=='L' else -1
        th,sh=(P['leg_in'] if S==IN else P['leg_out'])
        legs.append((bone('thigh',S),[('X',th),('Z',sgn*(P['leg_z'][0] if S==IN else P['leg_z'][1]))]))
        shins.append((bone('shin',S),[('X',sh)]))
    rots(legs); rots(shins)
    uas=[]; fas=[]; hds=[]
    for S in ('L','R'):
        sgn = 1 if S=='L' else -1
        uaY,uaZ,faX,faZ,hX,hY,hZ=(P['arm_in'] if S==IN else P['arm_out'])
        uas.append((bone('upperarm',S),[('Y',sgn*uaY),('Z',sgn*uaZ)]))
        fas.append((bone('forearm',S),[('X',faX),('Z',sgn*faZ)]))
        hds.append((bone('hand',S),[('X',hX),('Y',hY),('Z',sgn*hZ)]))
    rots(uas); rots(fas); rots(hds)
    for S in ('L','R'):
        sgn = 1 if S=='L' else -1
        hand_pose(S,'rest_thigh' if S==OUTS else 'relaxed','relaxed',0,sgn)
        bone('hand',S).scale=(CH['hand_scale'],)*3
    rots([(bone('spine'),[('X',P['spine_x'])])])
    rots([(bone('chest'),[('Z',inward*P['chest_z']),('X',P['chest_x'])])])
    bone('head').scale=(CH['head_scale'],)*3
    upd()
    return pz-drop

seat_z=base_pose()

# ---------- set pieces: stool + mic (unchanged from v1) ----------
def cyl(name,r,depth,loc,rot=(0,0,0),mat=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r,depth=depth,location=loc,rotation=rot,vertices=24)
    o=bpy.context.object; o.name=name
    if mat: o.data.materials.append(mat)
    return o
mp=bpy.data.materials.new('SetPaper'); mp.use_nodes=True; flat(mp,PAPER)
mi=bpy.data.materials.new('SetInk'); mi.use_nodes=True; flat(mi,INK)
pel_w=rig.matrix_world@bone('pelvis').matrix.translation
seat_z-=CH['seat_drop']
cyl('stool_seat',0.21,0.05,(pel_w.x,pel_w.y+0.06,seat_z-0.02),mat=mp)
cyl('stool_post',0.03,seat_z-0.05,(pel_w.x,pel_w.y+0.06,(seat_z-0.05)/2),mat=mp)
cyl('stool_base',0.19,0.03,(pel_w.x,pel_w.y+0.06,0.015),mat=mp)
head_w=rig.matrix_world@bone('head').matrix.translation
mic_x=head_w.x+inward*0.30; mic_z=head_w.z+0.02; my=head_w.y-0.22
cyl('mic_cap',0.035,0.11,(mic_x,my,mic_z),rot=(0,math.radians(90),0),mat=mi)
stand_x=head_w.x+inward*0.50; stand_top=mic_z-0.55
cyl('mic_stand',0.012,stand_top,(stand_x,my,stand_top/2),mat=mp)
cyl('mic_base',0.14,0.025,(stand_x,my,0.012),mat=mp)
d=Vector((mic_x-stand_x,0,mic_z-stand_top)); L=d.length
cyl('mic_boom',0.008,L,(stand_x+d.x/2,my,stand_top+d.z/2),rot=(0,math.atan2(d.x,d.z),0),mat=mp)

# ---------- performance score (deterministic) ----------
def smooth(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def ease_out_back(t,s=1.4):   # overshoot then settle, 0..1
    t=max(0,min(1,t)); t-=1
    return t*t*((s+1)*t+s)+1
def bump(t,t0,dur):
    u=(t-t0)/dur
    return 0 if u<0 or u>1 else math.sin(math.pi*u)

speaker_first = (side=='A')
# speech turns: (start,end)
TURN = (0.0,2.55) if speaker_first else (2.85,5.0)
def speaking(t): return TURN[0]<=t<=TURN[1]

# syllables: (onset, dur, viseme, stress)  viseme: A open, E wide, O round, M closed, F narrow-open
def syllables(t0):
    pat=[(0.00,.14,'M',0),(0.14,.16,'A',1),(0.30,.12,'E',0),(0.42,.10,'M',0),(0.52,.18,'O',1),(0.70,.12,'A',0),
         (0.82,.10,'F',0),(0.92,.16,'E',1),(1.08,.22,'M',0),  # pause
         (1.30,.14,'A',0),(1.44,.12,'O',0),(1.56,.16,'A',1),(1.72,.12,'M',0),(1.84,.14,'E',0),(1.98,.16,'A',1),
         (2.14,.12,'O',0),(2.26,.16,'M',0)]
    return [(t0+o,d,v,s) for o,d,v,s in pat]
SYL=syllables(TURN[0])
VIS={'A':(1.0,0.0,0.6),'E':(0.55,0.35,0.5),'O':(0.7,-0.35,0.3),'M':(0.0,0.0,0.0),'F':(0.35,-0.1,0.9)}  # jaw, width, lower-lip

def mouth_state(t):
    """returns jaw(0..1), width(-1..1), lip(0..1) blended across syllables with coarticulation."""
    if not speaking(t): return 0.0,0.0,0.0
    j=w=l=0.0; wsum=0.0
    for o,d,v,s in SYL:
        c=o+d*0.45; sig=d*0.55
        k=math.exp(-((t-c)/sig)**2)
        J,W,Lp=VIS[v]; amp=0.75+0.35*s
        j+=k*J*amp; w+=k*W; l+=k*Lp; wsum+=k
    if wsum<1e-6: return 0.0,0.0,0.0
    return min(1,j/max(wsum,0.8)), w/max(wsum,0.8), min(1,l/max(wsum,0.8))

STRESS=[o for o,d,v,s in SYL if s]
# gesture beats: shoulder-led present gesture on the first stressed syllable group, second smaller beat later
GEST=[(STRESS[0]-0.25,'present',1.0,1.5),(STRESS[3]-0.2,'present',0.55,1.0)] if speaker_first else \
     [(STRESS[0]-0.25,'present',0.9,1.4),(STRESS[3]-0.2,'point_soft',0.5,0.9)]

def gesture(t):
    """returns (amp, pose, phase u) shoulder-led with anticipation, overshoot, hold drift, settle."""
    best=(0.0,'present',0.0)
    for t0,pose,amp,total in GEST:
        u=t-t0
        if u<0 or u>total: continue
        ant=0.12; stroke=0.30; hold=total-ant-stroke-0.42; rel=0.42
        if u<ant: a=-0.10*math.sin(math.pi*u/ant)             # anticipation dip
        elif u<ant+stroke: a=ease_out_back((u-ant)/stroke,1.2) # stroke with overshoot
        elif u<ant+stroke+hold: a=1.0-0.06*(u-ant-stroke)/max(hold,1e-3)  # slow drift during hold
        else: a=0.94*(1-smooth((u-ant-stroke-hold)/rel))       # settle
        best=(a*amp,pose,u)
    return best

def head_state(t):
    sp=speaking(t)
    base_yaw = (12 if sp else 16)+CH['yaw_bias']     # + body yaw 35 => ~50 deg to partner
    yaw=inward*(base_yaw+2.0*math.sin(t*0.9+(0 if speaker_first else 1.7)))
    pitch=1.5*math.sin(t*1.4)
    if sp:
        for o,d,v,s in SYL:
            if s: pitch+=4.5*bump(t,o-0.08,0.42)         # emphasis nod on stressed syllables
        # tiny turn-away while 'thinking' at turn start, then re-engage
        yaw-=inward*8*bump(t,TURN[0]-0.15,0.6)
    else:
        # listener: two agreeing nods during the partner's stressed syllables, small lean-in
        other=(2.85,5.0) if speaker_first else (0.0,2.55)
        for tn in (other[0]+0.9,other[0]+1.75):
            pitch+=6*bump(t,tn,0.5)-2.5*bump(t,tn+0.45,0.3)
    roll=inward*1.5*math.sin(t*0.7)
    return yaw,pitch,roll

BLINKS=[0.35,1.9,3.6,4.7] if speaker_first else [0.7,2.55,2.95,4.3]
def blink(t):
    b=0.0
    for tb in BLINKS:
        u=t-tb
        if 0<=u<0.07: b=max(b,smooth(u/0.07))
        elif 0.07<=u<0.20: b=max(b,1-smooth((u-0.07)/0.13))
    return b

def gaze(t):
    """eye target offset (x toward partner, z up) in rig units; saccades at fixed beats."""
    x=inward*0.35; z=-0.05
    for ts,dx,dz in ((TURN[0]-0.1,-0.5,0.4),(TURN[0]+1.15,0.3,-0.3),(TURN[1]+0.2,0.0,0.3)):
        k=bump(t,ts,0.45)
        x+=inward*dx*k; z+=dz*k
    return x,z

def brows(t):
    sp=speaking(t)
    up=0.0
    if sp:
        for o,d,v,s in SYL:
            if s: up+=0.7*bump(t,o-0.12,0.5)
        up+=0.5*bump(t,TURN[0]-0.1,0.7)
    else:
        other=(2.85,5.0) if speaker_first else (0.0,2.55)
        up+=0.6*bump(t,other[0]+0.85,0.7)
    return min(1,up)

def breathe(t): return 0.5*math.sin(t*1.9)

# ---------- apply per frame ----------
def apply(t):
    base_pose()
    yaw,pitch,roll=head_state(t)
    rots([(bone('chest'),[('X',breathe(t))])])
    rots([(bone('neck'),[('Z',yaw*0.35),('X',pitch*0.3)])])
    rots([(bone('head'),[('Z',yaw*0.65),('X',pitch*0.7),('Y',roll)])])
    # face
    jaw,width,lip=mouth_state(t)
    b=blink(t); gx,gz=gaze(t); br=brows(t)
    for S in ('L','R'):
        local_loc(fbone('lid_upper',S),y=FC['lid_close']*b)
        local_loc(fbone('brow',S),y=FC['brow_up']*(br-0.15))
        local_loc(fbone('corner',S),y=FC['corner_up']*(0.35 if not speaking(t) else 0.1+0.3*max(0,width)))
    local_loc(fbone('eyes'),x=FC['gaze']*gx,z=FC['gaze']*gz)
    m=fbone('mouth'); m.scale=(1+0.22*width,1,1)
    local_loc(fbone('lip_bot'),y=-FC['lip_open']*lip)
    local_loc(fbone('lip_top'),y=FC['lip_open']*0.35*jaw)
    j=bone('jaw'); local_rot(j,x=FC['jaw_sign']*FC['jaw_deg']*jaw)
    # gesture arm (shoulder leads, forearm follows, wrist last; fingers open into pose)
    a,pose,u=gesture(t)
    if os.environ.get('FORCEA'): a=float(os.environ['FORCEA']); pose='present'; u=1.0
    if a!=0:
        S=IN; sgn=1 if S=='L' else -1
        lag_f=max(0,min(1,(u-0.06)/0.34)); lag_w=max(0,min(1,(u-0.12)/0.34))
        af=a*(0.5+0.5*lag_f); aw=a*(0.4+0.6*lag_w)
        G=GESTV
        rots([(bone('upperarm',S),[('Z',sgn*G['ua'][0]*a),('Y',sgn*G['ua'][1]*a)])])
        rots([(bone('forearm',S),[('X',G['fa'][0]*af),('Z',sgn*G['fa'][1]*af)])])
        brots(bone('hand',S),[('Y',sgn*G['h'][1]*aw),('X',G['h'][0]*aw),('Z',sgn*G['h'][2]*aw)])
        hand_pose(S,'relaxed',pose,max(0,min(1,aw/0.9)),sgn)
    if os.environ.get('FING'):
        fx=float(os.environ['FING'])
        for S in ('L','R'):
            for F in CH['fingers']:
                for N in (1,2,3): local_rot(bone('finger',S,F,N),x=fx)
            for N in (1,2): local_rot(bone('thumb',S,N=N),x=fx)
    upd()

# ---------- line art ----------
bpy.ops.object.select_all(action='DESELECT')
gd=bpy.data.grease_pencils.new('LineArt'); gp=bpy.data.objects.new('LineArt',gd); scene.collection.objects.link(gp)
gd.layers.new('Lines'); lm=bpy.data.materials.new('LineInk'); bpy.data.materials.create_gpencil_data(lm); gd.materials.append(lm)
lm.grease_pencil.color=INK
mod=gp.modifiers.new('LineArt','LINEART'); mod.source_type='SCENE'; mod.target_layer='Lines'; mod.target_material=lm
mod.use_crease=True; mod.crease_threshold=math.radians(130); mod.use_intersection=True; mod.use_material=True; mod.use_edge_overlap=True
for a in ('thickness','line_thickness'):
    if hasattr(mod,a): setattr(mod,a,5)

# ---------- camera / output ----------
cd=bpy.data.cameras.new('cam'); cam=bpy.data.objects.new('cam',cd); scene.collection.objects.link(cam); scene.camera=cam
if CLOSEUP:
    hw=rig.matrix_world@bone('head').matrix.translation
    cam.location=(hw.x+inward*0.12,-2.7,hw.z-0.14); cam.rotation_euler=(math.radians(90),0,0); cd.lens=80
else:
    cam.location=(0.0,-4.6,1.0); cam.rotation_euler=(math.radians(89.5),0,0); cd.lens=58
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1920; scene.render.resolution_y=1080; scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
scene.frame_set(F0); scene.render.fps=FPS
if hasattr(scene,'eevee'): scene.eevee.taa_render_samples=4

os.makedirs(OUT,exist_ok=True)
for f in range(F0,F1+1):
    t=f/FPS
    t0=time.time(); apply(t); tp=time.time()-t0
    scene.render.filepath=os.path.join(OUT,f'{CHAR}_{f:04d}.png')
    t0=time.time(); bpy.ops.render.render(write_still=True); print('FRAME',f,'pose %.1fs render %.1fs'%(tp,time.time()-t0),flush=True)
    if STILL: break
print('DONE')
