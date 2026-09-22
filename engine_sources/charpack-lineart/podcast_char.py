"""Render one Blender Studio character as a line-art podcast guest.
usage: blender -b <file> --python podcast_char.py -- <char> <outdir> <fstart> <fend> [still]
Deterministic: every control is keyed from python curves, no physics/randomness.
"""
import bpy, sys, math, json, os
from mathutils import Matrix, Vector, Euler

argv=sys.argv[sys.argv.index('--')+1:]
CHAR, OUT, F0, F1 = argv[0], argv[1], int(argv[2]), int(argv[3])
STILL = len(argv)>4 and argv[4]=='still'
FPS=24
scene=bpy.context.scene

# ---------- character adapters ----------
CH={
 'rain':dict(rig='RIG-rain', seat=('A',-0.62, 35), accent='#2E5EAA',
  props=('Properties_IKFK',{'ik_arm_left':0,'ik_arm_right':0,'ik_leg_left':0,'ik_leg_right':0,'ik_spine':0,'ik_fingers_left':0,'ik_fingers_right':0}),
  charprops=('Properties_Character_Rain',{'Quality':0,'Scarf':False}),
  b=dict(head='FK-Head',neck='FK-Neck',chest='FK-Chest',spine='FK-Spine',pelvis='MSTR-Pelvis',jaw='MSTR-Jaw',
   upperarm='FK-Upperarm.{S}',forearm='FK-Forearm.{S}',hand='FK-Hand.{S}',thigh='FK-Thigh.{S}',shin='FK-Shin.{S}',foot='FK-Foot.{S}',
   finger='FK-{F}{N}.{S}',thumb='FK-Thumb{N}.{S}',brow='MSTR-Eyebrow.{S}'),
  fingers=('Index','Middle','Ring','Pinky'),
  ink=('hair','eyebrow','eyelash','shoe','jeans','eyedot','gums','tongue','viewport_black','hairband','laces'),
  accent_mats=('MAT-rain.top',), hide=('GEO-rain-eye_cornea','GEO-rain-teeth_upper','GEO-rain-teeth_lower','GEO-rain-scarf'),
  seat_drop=0.12),
 'snow':dict(rig='RIG-Snow', seat=('B',0.62,-35), accent='#B5432B',
  props=('Properties',{'ik_left_upperarm':0,'ik_right_upperarm':0,'ik_left_thigh':0,'ik_right_thigh':0,'ik_spine':0}),
  charprops=('Properties_Character_Snow',{'Quality':0}),
  b=dict(head='FK-Head',neck='FK-Neck',chest='FK-Chest',spine='FK-Spine',pelvis='TORSO-Spine',jaw='Jaw',
   upperarm='FK-UpperArm.{S}',forearm='FK-Forearm.{S}',hand='FK-Wrist.{S}',thigh='FK-Thigh.{S}',shin='FK-Knee.{S}',foot='FK-Foot.{S}',
   finger='FK-Finger_{F}{N}.{S}',thumb='FK-Finger_Thumb{N}.{S}',brow='MSTR-Eyebrow.{S}'),
  fingers=('Index','Middle','Ring','Pinky'),
  ink=('hair','eye_dot','eyes_pupil','eyes_iris','pants','shoe','gums','tongue','Dots Stroke'),
  accent_mats=('snow.shirt',), hide=('GEO-snow_eye_corneas','GEO-snow-teeth_upper','GEO-snow-teeth_lower'),
  seat_drop=0.21),
}[CHAR]
rig=bpy.data.objects[CH['rig']]
B=CH['b']

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

# ---------- strip any shipped animation so python owns every control ----------
def strip_actions(idb):
    ad=idb.animation_data if idb else None
    if not ad: return
    ad.action=None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)   # keep drivers: they own IK/FK switching
for o in bpy.data.objects:
    strip_actions(o)
    if o.type=='MESH': strip_actions(o.data.shape_keys)
# ---------- rig props ----------
if bpy.context.object and bpy.context.object.mode!='OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
for bone,vals in (CH['props'],CH['charprops']):
    pb=rig.pose.bones.get(bone)
    if not pb: print('MISSING propbone',bone); continue
    for k,v in vals.items():
        if k in pb.keys(): pb[k]=type(pb[k])(v)
        else: print('MISSING prop',k)

# ---------- bone helpers ----------
def bone(key,S='L',F='Index',N=1):
    name=B[key].format(S=S,F=F,N=N)
    if name.startswith('@child:'):
        parent=rig.pose.bones[name[7:]]
        kids=[c for c in parent.children if not c.name.startswith(('DEF','MCH','ORG'))]
        return kids[0] if kids else None
    pb=rig.pose.bones.get(name)
    if pb is None: print('MISSING bone',name)
    return pb

def upd(): bpy.context.view_layer.update()

def rot_world(pb,axis,deg,pivot=None):
    """rotate a pose bone about an armature-space axis through its head (or pivot)."""
    if pb is None or deg==0: return
    upd()
    p=pb.matrix.translation.copy() if pivot is None else pivot
    R=Matrix.Translation(p)@Matrix.Rotation(math.radians(deg),4,axis)@Matrix.Translation(-p)
    pb.matrix=R@pb.matrix
    upd()

def move_world(pb,vec):
    if pb is None: return
    upd(); pb.matrix=Matrix.Translation(Vector(vec))@pb.matrix; upd()

def scale_bone(pb,s):
    if pb is None: return
    pb.scale=(s,s,s) if not isinstance(s,tuple) else s

def key_all(frame):
    for pb in rig.pose.bones:
        if pb.rotation_mode=='QUATERNION': pb.keyframe_insert('rotation_quaternion',frame=frame)
        else: pb.keyframe_insert('rotation_euler',frame=frame)
        pb.keyframe_insert('location',frame=frame); pb.keyframe_insert('scale',frame=frame)

# ---------- base seated pose ----------
side,X,yawdeg=CH['seat']
inward = 1 if side=='A' else -1           # +1: partner is to +X
rig.rotation_euler=(0,0,math.radians(yawdeg)); rig.location=(X,0,0)

def base_pose():
    for pb in rig.pose.bones:
        pb.matrix_basis=Matrix.Identity(4)
    upd()
    pelvis=bone('pelvis')
    pz=(rig.matrix_world.inverted()@(rig.matrix_world@pelvis.matrix.translation)).z
    drop=0.43
    move_world(pelvis,(0,0,-drop))
    for S in ('L','R'):
        th=bone('thigh',S); sh=bone('shin',S)
        rot_world(th,'X',-88)
        rot_world(sh,'X',+92)
        sgn = 1 if S=='L' else -1
        ua=bone('upperarm',S); fa=bone('forearm',S); hd=bone('hand',S)
        rot_world(ua,'Y',sgn*72)          # drop arm from T-pose
        rot_world(ua,'Z',sgn*-8)          # elbows slightly forward
        rot_world(fa,'X',-78)             # forearm forward, resting toward lap
        rot_world(fa,'Z',sgn*-25)         # hands drift toward centre
        rot_world(hd,'X',-10)
        for F in CH['fingers']:
            for N in (1,2,3):
                pb=bone('finger',S,F,N); rot_world(pb,'X',-22 if N>1 else -14, None)
        rot_world(bone('thumb',S,N=1),'Z',sgn*18)
    # torso lean toward partner, slight forward
    rot_world(bone('spine'),'X',-6); rot_world(bone('chest'),'Z',inward*8)
    # Peeps proportion push: bigger head
    scale_bone(bone('head'),1.22)
    upd()
    return pz-drop

seat_z=base_pose()

# ---------- set pieces in the character's own space: stool + mic ----------
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

# ---------- performance curves (deterministic) ----------
def smooth(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def pulse(t,t0,dur):  # 0..1..0 bump
    u=(t-t0)/dur
    return 0 if u<0 or u>1 else math.sin(math.pi*u)
speaker_first = (side=='A')
def is_speaking(t):
    return (t<2.4) if speaker_first else (t>=2.4)
def perf(t):
    speak=is_speaking(t)
    # head: listen -> mostly toward partner; speak -> partner but with emphasis nods
    yaw = inward*(28 if not speak else 22) + inward*4*math.sin(t*1.3)
    pitch = 2.5*math.sin(t*2.1) + (6*pulse(t,0.6,0.5)+5*pulse(t,1.5,0.45) if speak else 4*pulse(t,3.2,0.6))
    # jaw from a pseudo-speech envelope while speaking
    jaw = 0
    if speak:
        env=abs(math.sin(t*9.0))*0.6+abs(math.sin(t*13.7))*0.4
        jaw=9*env*smooth((t-(0 if speaker_first else 2.4))/0.25)
    # gesture: speaker raises inward hand, palm open, then settles
    g = pulse(t,0.4,1.7) if speaker_first else pulse(t,2.8,1.7)
    g = smooth(g) if speak else 0
    # listener: small agreeing nod + breathing
    breathe = 0.6*math.sin(t*1.9)
    return yaw,pitch,jaw,g,breathe

def apply(t):
    base_pose()
    yaw,pitch,jaw,g,breathe=perf(t)
    rot_world(bone('chest'),'X',breathe)
    rot_world(bone('neck'),'Z',yaw*0.35)
    hd=bone('head'); rot_world(hd,'Z',yaw*0.65); rot_world(hd,'X',pitch)
    rot_world(bone('jaw'),'X',jaw)
    for S in ('L','R'):
        rot_world(bone('brow',S),'X',0)
    # gesture hand = the hand nearer the partner (screen-inward)
    S = 'L' if inward>0 else 'R'; sgn = 1 if S=='L' else -1
    ua=bone('upperarm',S); fa=bone('forearm',S); hdn=bone('hand',S)
    rot_world(ua,'Z',sgn*-28*g); rot_world(ua,'Y',sgn*-18*g)
    rot_world(fa,'X',-55*g); rot_world(fa,'Z',sgn*20*g)
    rot_world(hdn,'X',18*g); rot_world(hdn,'Y',sgn*30*g)
    for F in CH['fingers']:
        for N in (1,2,3):
            rot_world(bone('finger',S,F,N),'X',+20*g)   # open the hand
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
# hand-drawn feel: slight thickness variation + tiny noise

# ---------- camera / output ----------
cd=bpy.data.cameras.new('cam'); cam=bpy.data.objects.new('cam',cd); scene.collection.objects.link(cam); scene.camera=cam
cam.location=(0.0,-4.6,1.0); cam.rotation_euler=(math.radians(89.5),0,0); cd.lens=58
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1920; scene.render.resolution_y=1080; scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
scene.frame_set(F0); scene.render.fps=FPS
if hasattr(scene,'eevee'):
    scene.eevee.taa_render_samples=4

os.makedirs(OUT,exist_ok=True)
import time
for f in range(F0,F1+1):
    t=f/FPS
    apply(t)
    scene.render.filepath=os.path.join(OUT,f'{CHAR}_{f:04d}.png')
    t0=time.time(); bpy.ops.render.render(write_still=True); print('FRAME',f,'%.1fs'%(time.time()-t0),flush=True)
    if STILL: break
print('DONE')
