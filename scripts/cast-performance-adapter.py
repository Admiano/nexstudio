"""Bind the tested director to existing MakeHuman FK bones and native facial keys.

Every action is copied; body/hair/clothing/accessory geometry and materials remain
unchanged. No source-core bone names or generic source handbank are retargeted.
"""
import bpy,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from nex_performance_guards import pg_sample_viseme,pg_number
import nex_performance_logic as logic
VERSION='native-director-v19'
ARM_BASES={'clavicle','shoulder01','upperarm01','upperarm02','lowerarm01','lowerarm02','wrist'}
MOUTH=('!ex-jawOpen','V3_wide','V3_round','V3_closed','V3_FV','A_lowerDown','A_upperUp','A_pucker','A_funnel','A_stretch')
MOUTH_MAP={'REST':{},'MBP':{'V3_closed':.72},'AH':{'!ex-jawOpen':.19,'A_lowerDown':.14,'A_upperUp':.045,'V3_wide':.08},'EE':{'!ex-jawOpen':.085,'V3_wide':.32,'A_stretch':.12},'OH':{'!ex-jawOpen':.13,'V3_round':.40,'A_pucker':.20,'A_funnel':.13},'FV':{'!ex-jawOpen':.04,'V3_FV':.45,'A_lowerDown':.025},'RELAX':{'!ex-jawOpen':.038}}
FACE=('!ex-mouthSmileLeft','!ex-mouthSmileRight','!ex-browInnerUp','!ex-eyeBlinkLeft','!ex-eyeBlinkRight','E_browUp_L','E_browUp_R','E_browDown_L','E_browDown_R','E_browInner_L','E_browInner_R','E_squint_L','E_squint_R','E_eyeWide_L','E_eyeWide_R','E_cheek','E_grin','E_press')
NATIVE_BANK={'male':{'rest':482,'micro_beat':680,'low_offer':680,'precision':520,'contrast':600,'point':970},'female':{'rest':1,'micro_beat':350,'low_offer':350,'precision':30,'contrast':350,'point':350}}

def native_snapshot(scene,rig,frame):
 scene.frame_set(frame);bpy.context.view_layer.update()
 return {p.name:p.matrix_basis.copy() for p in rig.pose.bones}

def is_arm(name):return name.split('.')[0] in ARM_BASES or name.startswith(('finger','metacarpal'))

def pose_q(matrix):return matrix.to_quaternion().normalized()

def pulse(t,start,end,strength=1):
 if end<=start or t<=start or t>=end:return 0
 u=(t-start)/(end-start)
 return (logic.minimum_jerk_blend(u/.42) if u<.42 else 1-logic.minimum_jerk_blend((u-.42)/.58))*strength

def gesture_weight(t,g):
 a,b,c,d=(g[k] for k in ('start','stroke','holdEnd','end'))
 if t<=a or t>=d:return 0
 if t<b:return logic.minimum_jerk_blend((t-a)/max(1e-8,b-a))*g['strength']
 if t<=c:return g['strength']
 return (1-logic.minimum_jerk_blend((t-c)/max(1e-8,d-c)))*g['strength']

def new_action(id,name):
 id.animation_data_create()
 old=id.animation_data.action
 if old:old.use_fake_user=True
 id.animation_data.action=bpy.data.actions.new(name);return old.name if old else None

def delta_world(rig,p,q,axis,angle):
 local=p.bone.matrix_local.to_quaternion().inverted()@Vector(axis)
 return q@Quaternion(local,angle)

def source_seated_pose(scene,rig,base,directions):
 # Match the proved source direction of each FK limb to native segment lengths.
 # The environment adapts to this pose. No limb scale or IK contact rescue.
 for name,m in base.items():rig.pose.bones[name].matrix_basis=m
 bpy.context.view_layer.update()
 foot_rotations={side:rig.pose.bones['foot.'+side].matrix.to_quaternion() for side in ('L','R')}
 wrist_rotations={side:rig.pose.bones['wrist.'+side].matrix.to_quaternion() for side in ('L','R')}
 hand_directions={side:(rig.pose.bones['finger3-1.'+side].head-rig.pose.bones['wrist.'+side].head).normalized() for side in ('L','R')}
 hand_across={side:(rig.pose.bones['finger2-1.'+side].head-rig.pose.bones['finger5-1.'+side].head).normalized() for side in ('L','R')}
 for side,s in [('L','l'),('R','r')]:
  # MakeHuman splits each limb into two deformation bones. Align the whole
  # anatomical segment, not the short first twist bone.
  for native,next_joint,source in [('upperleg01','lowerleg01','c_thigh_fk'),('lowerleg01','foot','c_leg_fk')]:
   p=rig.pose.bones[native+'.'+side];data=directions[source+'.'+s]
   target=(Vector(data['tail'])-Vector(data['head'])).normalized();current=(rig.pose.bones[next_joint+'.'+side].head-p.head).normalized()
   delta=current.rotation_difference(target);m=p.matrix.copy();location=m.translation.copy();rotation=delta@m.to_quaternion()
   p.rotation_mode='QUATERNION';p.matrix=Matrix.Translation(location)@rotation.to_matrix().to_4x4();bpy.context.view_layer.update()
  # The native foot bone slopes towards the toes even with a flat sole.
  # Preserve its original world orientation rather than making that bone
  # horizontal, which visibly tips the actual sole upwards.
  p=rig.pose.bones['foot.'+side];location=p.matrix.translation.copy()
  p.rotation_mode='QUATERNION';p.matrix=Matrix.Translation(location)@foot_rotations[side].to_matrix().to_4x4()
  bpy.context.view_layer.update()
  # A contact pose uses a two-link anatomical solve, then stores ordinary FK
  # quaternions. No expression track gains arm IK ownership or limb scaling.
  shoulder=rig.pose.bones['upperarm01.'+side].head.copy()
  elbow=rig.pose.bones['lowerarm01.'+side].head.copy()
  wrist=rig.pose.bones['wrist.'+side].head.copy()
  hip=rig.pose.bones['upperleg01.'+side].head.copy()
  knee=rig.pose.bones['lowerleg01.'+side].head.copy()
  target=hip.lerp(knee,.48 if side=='L' else .53)+Vector((0,0,.065))
  target.x+=(.015 if side=='L' else -.015)
  upper=(elbow-shoulder).length;lower=(wrist-elbow).length
  direction=target-shoulder;distance=direction.length
  if not abs(upper-lower)+.005<distance<upper+lower-.005:raise ValueError('NATIVE_LAP_CONTACT_OUT_OF_REACH')
  unit=direction.normalized();bend=Vector((.6 if side=='L' else -.6,.7,-1))
  bend=(bend-unit*bend.dot(unit)).normalized()
  along=(upper*upper-lower*lower+distance*distance)/(2*distance)
  desired_elbow=shoulder+unit*along+bend*math.sqrt(max(0,upper*upper-along*along))
  body=next(ob for ob in scene.objects if ob.parent==rig and ob.name.startswith('Host.body') and ob.type=='MESH')
  thigh_groups={g.index for g in body.vertex_groups if g.name.startswith('upperleg') and g.name.endswith('.'+side)}
  hand_groups={g.index for g in body.vertex_groups if (g.name.startswith(('finger','metacarpal','wrist'))) and g.name.endswith('.'+side)}
  thigh_vertices={v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in thigh_groups)>.30}
  hand_vertices={v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in hand_groups)>.50}
  # MakeHuman's source body also contains invisible garment/helper cages.
  # Their weights do not make them skin. Honour the native helper mask when
  # constructing the contact surface, even though masks are disabled below
  # to retain stable source vertex indices during evaluation.
  helper_mask=body.modifiers.get('Hide helpers')
  if helper_mask and helper_mask.type=='MASK':
   group=body.vertex_groups.get(helper_mask.vertex_group)
   if group is None:raise ValueError('NATIVE_SKIN_MASK_REQUIRED')
   members={v.index for v in body.data.vertices if any(g.group==group.index and g.weight>helper_mask.threshold for g in v.groups)}
   skin_vertices=set(range(len(body.data.vertices)))-members if helper_mask.invert_vertex_group else members
   thigh_vertices &= skin_vertices;hand_vertices &= skin_vertices
  states=[(m,m.show_viewport) for m in body.modifiers if m.type!='ARMATURE']
  try:
   for m,state in states:m.show_viewport=False
   bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
   def skin_points():
    ev=body.evaluated_get(deps);mesh=ev.to_mesh()
    try:
     if len(mesh.vertices)!=len(body.data.vertices):raise ValueError('NATIVE_CONTACT_TOPOLOGY_CHANGED')
     return [(rig.matrix_world.inverted()@ev.matrix_world)@v.co for v in mesh.vertices]
    finally:ev.to_mesh_clear()
   points=skin_points();polygons=[list(p.vertices) for p in body.data.polygons if all(i in thigh_vertices for i in p.vertices)]
   if not polygons or not hand_vertices:raise ValueError('NATIVE_CONTACT_SKIN_GROUPS_REQUIRED')
   surface=BVHTree.FromPolygons(points,polygons)
   contact_gap=None
   for attempt in range(6):
    direction=target-shoulder;distance=direction.length
    if not abs(upper-lower)+.005<distance<upper+lower-.005:raise ValueError('NATIVE_LAP_CONTACT_OUT_OF_REACH')
    unit=direction.normalized();bend=Vector((.6 if side=='L' else -.6,.7,-1));bend=(bend-unit*bend.dot(unit)).normalized()
    along=(upper*upper-lower*lower+distance*distance)/(2*distance)
    desired_elbow=shoulder+unit*along+bend*math.sqrt(max(0,upper*upper-along*along))
    for native,next_joint,destination in [('upperarm01','lowerarm01',desired_elbow),('lowerarm01','wrist',target)]:
     arm=rig.pose.bones[native+'.'+side];current=rig.pose.bones[next_joint+'.'+side].head-arm.head
     desired=destination-arm.head;delta=current.normalized().rotation_difference(desired.normalized())
     location=arm.matrix.translation.copy();rotation=delta@arm.matrix.to_quaternion()
     arm.rotation_mode='QUATERNION';arm.matrix=Matrix.Translation(location)@rotation.to_matrix().to_4x4();bpy.context.view_layer.update()
    hand=rig.pose.bones['wrist.'+side];forward=Vector((0,-1,-.08)).normalized()
    alignment=hand_directions[side].rotation_difference(forward)
    across=alignment@hand_across[side];across=(across-forward*across.dot(forward)).normalized()
    desired_across=Vector((-1 if side=='L' else 1,0,0))
    roll=math.atan2(forward.dot(across.cross(desired_across)),across.dot(desired_across))
    rotation=Quaternion(forward,roll)@alignment@wrist_rotations[side]
    hand.rotation_mode='QUATERNION';hand.matrix=Matrix.Translation(hand.matrix.translation.copy())@rotation.to_matrix().to_4x4();bpy.context.view_layer.update()
    points=skin_points();gaps=[]
    for index in hand_vertices:
     nearest,normal,face,dist=surface.find_nearest(points[index])
     if nearest is not None and normal.z>.45 and dist<.12:gaps.append((points[index]-nearest).dot(normal))
    if not gaps:raise ValueError('NATIVE_LAP_SURFACE_NOT_FOUND')
    contact_gap=min(gaps)
    if abs(contact_gap-.012)<.003:break
    target.z+=.012-contact_gap
   if contact_gap is None or not .005<=contact_gap<=.020:raise ValueError('NATIVE_LAP_CONTACT_CLEARANCE_FAILED:'+str(contact_gap))
   rig['lapContactGap.'+side]=contact_gap
  finally:
   for m,state in states:m.show_viewport=state
   bpy.context.view_layer.update()
 return {p.name:p.matrix_basis.copy() for p in rig.pose.bones}

def prepare_seated_bindings(scene,rig):
 """Restore rigged garment authority and attach rigid footwear to native feet.

 Frozen preview-fit meshes contain a single standing pose. They must never
 masquerade as animated garment geometry. Originals remain recoverable.
 """
 repairs=[]
 for ob in list(scene.objects):
  source_name=ob.get('castFitSource')
  if not source_name:continue
  source=bpy.data.objects.get(source_name)
  if source is None or source.parent!=rig:continue
  ob.hide_render=True;source.hide_render=source.get('castFitOriginalHideRender',False)
  repairs.append({'object':ob.name,'source':source.name,'repair':'restore original weighted garment'})
 for ob in list(scene.objects):
  if ob.parent!=rig or ob.type!='MESH' or ob.hide_render:continue
  if 'lineart_shoe.' in ob.name and ob.parent_type!='BONE':
   side='L' if 'shoe.L' in ob.name else 'R'
   mw=ob.matrix_world.copy();ob.parent_type='BONE';ob.parent_bone='foot.'+side
   bpy.context.view_layer.update();ob.matrix_world=mw;bpy.context.view_layer.update()
   repairs.append({'object':ob.name,'repair':'rigid native foot binding','bone':ob.parent_bone})
 return repairs

def bake_actor(scene,rig,body,plan,*,fps=24,frame0=1,seated_directions=None):
 if rig.type!='ARMATURE' or not body.data.shape_keys:raise ValueError('NATIVE_RIG_AND_FACE_REQUIRED')
 sex=plan['character'];bank=NATIVE_BANK[sex];initial_action=rig.animation_data.action
 rest=native_snapshot(scene,rig,bank['rest']);poses={name:native_snapshot(scene,rig,frame) for name,frame in bank.items() if name!='rest'}
 # Capture posed source quaternions before dropping old speech/gesture curves.
 scene.frame_set(bank['rest']);bpy.context.view_layer.update();shape=body.data.shape_keys
 binding_repairs=prepare_seated_bindings(scene,rig) if plan['posture']=='seated' else []
 if any(shape.key_blocks.get(k) is None for k in MOUTH+FACE):raise ValueError('NATIVE_FACE_CONTROL_MISSING')
 originals={'rig':new_action(rig,plan['actor_id']+' • Native Performance V19'),'face':new_action(shape,plan['actor_id']+' • Face and Speech V19')}
 if rig.animation_data.nla_tracks:
  for tr in rig.animation_data.nla_tracks:tr.mute=True
 if shape.animation_data.nla_tracks:
  for tr in shape.animation_data.nla_tracks:tr.mute=True
 for p in rig.pose.bones:
  for c in p.constraints:
   if c.name=='RELAX':c.influence=0
 if plan['posture']=='seated':
  if not seated_directions:raise ValueError('PROVED_SEATED_SOURCE_REQUIRED')
  rest=source_seated_pose(scene,rig,rest,seated_directions)
  # A seated phrase starts and returns to the verified lap contact, rather
  # than interpolating towards a standing wrist destination inside a thigh.
  for variant in ('micro_beat','low_offer'):
   pose={name:matrix.copy() for name,matrix in rest.items()}
   for name,angle in [('upperarm01.R',-10),('lowerarm01.R',-8)]:
    matrix=pose[name];q=delta_world(rig,rig.pose.bones[name],pose_q(matrix),(1,0,0),math.radians(angle))
    location,rotation,scale=matrix.decompose();pose[name]=Matrix.LocRotScale(location,q,scale)
   poses[variant]=pose
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 duration=pg_number(plan['duration'],'duration',positive=True);last=frame0+math.ceil(duration*fps)-1
 controlled={p.name for p in rig.pose.bones if is_arm(p.name) or p.name in ['head','neck01','neck02','neck03','spine01','eye.L','eye.R']}
 # Lower-body support is a constant native pose, never owned by attention.
 for name,m in rest.items():
  p=rig.pose.bones[name];p.matrix_basis=m
  p.keyframe_insert('location',frame=frame0);p.keyframe_insert('rotation_quaternion',frame=frame0);p.keyframe_insert('scale',frame=frame0)
 records=[];gaze=0;eye_gaze=0;gaze_pitch=0
 bpy.context.view_layer.update()
 head_position=rig.matrix_world@rig.pose.bones['head'].head
 base_forward=rig.matrix_world.to_quaternion()@Vector((0,-1,0))
 base_yaw=math.atan2(base_forward.x,-base_forward.y)
 def target_angle(position):
  direction=Vector(position)-head_position
  angle=math.atan2(direction.x,-direction.y)-base_yaw
  return (angle+math.pi)%(2*math.pi)-math.pi
 for frame in range(frame0,last+1):
  t=(frame-frame0)/fps
  quats={n:pose_q(rest[n]) for n in controlled}
  for g in plan['gestures']:
   w=gesture_weight(t,g)
   if not w:continue
   for n in controlled:
    if is_arm(n) and n.endswith('.'+g['side'][0].upper()):quats[n]=quats[n].slerp(pose_q(poses[g['variant']][n]),w)
  own=any(a<=t<b for a,b in plan['speaker_active_windows'])
  active=[e for e in plan['social'] if e['start']<=t<e['end']]
  # Deliberate attention state. Small release is tied to a semantic/listener event.
  target_position=list(scene.camera.location)
  if plan['camera_relationship']!='direct_presenter':
   recipient=plan.get('recipient_id')
   if recipient not in plan.get('targets',{}):raise ValueError('ACTUAL_CONVERSATION_TARGET_REQUIRED')
   target_position=plan['targets'][recipient]
  target_yaw=target_angle(target_position)
  current_attention=[e for e in plan['attention'] if e['start']<=t<e['end']]
  if current_attention:
   target=current_attention[-1]['parameters']['target']
   if target['type']=='object':
    if target['id'] not in plan.get('targets',{}):raise ValueError('ACTUAL_CONTENT_TARGET_REQUIRED')
    target_yaw=target_angle(plan['targets'][target['id']])
   elif target['type']=='away':target_yaw-=math.radians(7)
  for e in active:
   if e['intent'] in ('THINK_BEFORE_ANSWER','LISTENER_GAZE_RELEASE','SOCIAL_DOUBT'):target_yaw*=.35;target_yaw+=math.radians(-7);gaze_pitch=math.radians(-2)
  if not any(e['intent'] in ('THINK_BEFORE_ANSWER','LISTENER_GAZE_RELEASE','SOCIAL_DOUBT') for e in active):gaze_pitch*=.8
  # Critically bounded event-target response, with eyes arriving first.
  gaze+=(target_yaw-gaze)*.16
  eye_gaze+=(target_yaw-eye_gaze)*.38
  for name,factor,limit,axis in [('eye.L',.45,18,(0,0,1)),('eye.R',.45,18,(0,0,1)),('head',.36,15,(0,0,1)),('neck01',.12,5,(0,0,1)),('neck02',.07,3,(0,0,1))]:
   p=rig.pose.bones[name];quats[name]=delta_world(rig,p,quats[name],axis,max(-math.radians(limit),min(math.radians(limit),(eye_gaze if name.startswith('eye.') else gaze)*factor)))
  nod=0;roll=0;brow=0;squint=0;smile=.035
  for e in active:
   v=pulse(t,e['start'],e['end'])
   if e['intent'] in ('SOCIAL_AGREE','BACKCHANNEL','SOCIAL_ACKNOWLEDGE'):nod+=math.radians(2.1)*v
   if e['intent']=='SOCIAL_DISAGREE':roll+=math.radians(1.3)*v;brow+=.09*v
   if e['intent'] in ('LISTENER_CONSIDER','THINK_BEFORE_ANSWER'):brow+=.075*v;squint+=.07*v
   if e['intent']=='LISTENER_REACTION':brow+=.10*v
  quats['head']=delta_world(rig,rig.pose.bones['head'],quats['head'],(1,0,0),nod+gaze_pitch*.4)
  quats['head']=delta_world(rig,rig.pose.bones['head'],quats['head'],(0,1,0),roll)
  # Blinks occur at semantic boundaries and long listening releases, not a sine oscillator.
  blink_times=[]
  blink_times += [b['end']+.06 for b in plan['beats']]
  blink_times += [e['start']+.10 for e in plan['social'] if e['intent'] in ('LISTENER_SETTLE','LISTENER_GAZE_RELEASE','THINK_BEFORE_ANSWER')]
  blink=max([pulse(t,x-.065,x+.10) for x in blink_times]+[0])
  for n,q in quats.items():
   if not all(math.isfinite(v) for v in q):raise ValueError('NONFINITE_NATIVE_QUATERNION')
   p=rig.pose.bones[n];p.rotation_quaternion=q;p.keyframe_insert('rotation_quaternion',frame=frame)
  for key in MOUTH+FACE:shape.key_blocks[key].value=0
  state=pg_sample_viseme(plan['speech'],t,own)
  for key,val in MOUTH_MAP[state['viseme']].items():shape.key_blocks[key].value=val*state['intensity']
  shape.key_blocks['!ex-mouthSmileLeft'].value=smile;shape.key_blocks['!ex-mouthSmileRight'].value=smile*.90
  for key in ['E_browInner_L','E_browInner_R']:shape.key_blocks[key].value=brow
  for key in ['E_squint_L','E_squint_R']:shape.key_blocks[key].value=squint
  shape.key_blocks['!ex-eyeBlinkLeft'].value=blink;shape.key_blocks['!ex-eyeBlinkRight'].value=blink
  for key in MOUTH+FACE:shape.key_blocks[key].keyframe_insert('value',frame=frame)
  records.append({'frame':frame,'seconds':t,'speaker':own,'viseme':state['viseme'],'jaw':shape.key_blocks['!ex-jawOpen'].value,'gesture':any(gesture_weight(t,g)>0 for g in plan['gestures'])})
 # Linear baked curves: no Bezier overshoot can reopen lips during a silence.
 for id in [rig,shape]:
  for layer in id.animation_data.action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:
      for k in curve.keyframe_points:k.interpolation='LINEAR'
 scene.frame_start=frame0;scene.frame_end=last;scene.render.fps=int(fps);scene.render.fps_base=1
 text=bpy.data.texts.get(plan['actor_id']+'_PERFORMANCE_PLAN.json') or bpy.data.texts.new(plan['actor_id']+'_PERFORMANCE_PLAN.json');text.clear();text.write(json.dumps(plan,indent=2))
 rig['nativePerformanceVersion']=VERSION;rig['nativePerformanceActorId']=plan['actor_id']
 return {'version':VERSION,'character':sex,'actor_id':plan['actor_id'],'frames':len(records),'archives':originals,'records':records,'lowerBodyStaticSupport':True,'mouthOwnershipEnforced':True,'audioRetimed':False,'nativeBank':bank,'bindingRepairs':binding_repairs}
