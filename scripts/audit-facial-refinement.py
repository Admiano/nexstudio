"""Check oral restoration, source identity, rig deformation and repeatability."""
import bpy,runpy,sys,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector,Matrix
character,output=sys.argv[sys.argv.index('--')+1:][:2];scene=bpy.context.scene
original=[o for o in scene.objects if o.type=='MESH'];original_keys={o.name:set(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else set() for o in original}
def identity():
 h=hashlib.sha256()
 for o in sorted(original,key=lambda x:x.name):
  h.update(o.name.encode())
  for v in o.data.vertices:
   h.update(struct.pack('3d',*v.co))
   for g in v.groups:
    if o.vertex_groups[g.group].name!='Cast clean temple ends':h.update(struct.pack('if',g.group,g.weight))
  for uv in o.data.uv_layers:
   for p in uv.data:h.update(struct.pack('2f',*p.uv))
  if o.data.shape_keys:
   for k in o.data.shape_keys.key_blocks:
    if k.name not in original_keys[o.name]:continue
    h.update(k.name.encode())
    for v in k.data:h.update(struct.pack('3d',*v.co))
 for rig in [o for o in scene.objects if o.type=='ARMATURE']:
  for bone in rig.data.bones:h.update(bone.name.encode());h.update(struct.pack('6d',*bone.head_local,*bone.tail_local))
 return h.hexdigest()
module=runpy.run_path(str(Path(__file__).with_name('cast-facial-refinement.py')));before=identity();report=module['apply_facial_refinement'](scene,character)
assert identity()==before,'ORIGINAL_ANATOMY_CHANGED'
body=bpy.data.objects['Host.body'];ear_key=body.data.shape_keys.key_blocks.get('Cast V12 balanced ears')
lip_ids=set(module['group_indices'](body,'lips'))
assert all(not any(i in lip_ids for i in p.vertices) for p in body.data.polygons if body.data.materials[p.material_index].name=='Cast V12 oral mucosa'),'ORAL_SHADING_SPILLED_ON_EXTERIOR_LIPS'
if ear_key:
 ear_ids=set(module['group_indices'](body,'ears'));basis=body.data.shape_keys.key_blocks[0]
 assert all((v.co-basis.data[i].co).length<1e-8 for i,v in enumerate(ear_key.data) if i not in ear_ids),'EAR_CORRECTION_CHANGED_FACE_OR_BODY'
 for name in ['!ex-jawOpen','A_pucker','A_upperUp','A_lowerDown']:
  assert body.data.shape_keys.key_blocks.get(name),'ORIGINAL_MOUTH_CONTROL_MISSING'
objects=[o for o in scene.objects if o.name.startswith('Cast V12 oral')];assert len(objects)==3
counts=(len(bpy.data.objects),len(bpy.data.materials),tuple(len(o.data.vertices) for o in objects),len(bpy.data.objects['Host.body'].data.materials))
module['apply_facial_refinement'](scene,character)
assert counts==(len(bpy.data.objects),len(bpy.data.materials),tuple(len(o.data.vertices) for o in objects),len(bpy.data.objects['Host.body'].data.materials)),'REAPPLICATION_MUTATED_TOPOLOGY'
for o in objects:
 o.modifiers['Dental surface refinement'].show_viewport=False
frames=[1,27,71,106,160,260,360,500,650,820,998];maximum=0;movement={};first={}
for f in frames:
 scene.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
 if f==1:assert all(o.hide_render for o in objects),'CLOSED_LIP_ENAMEL_GLINT'
 if f in [27,71,106]:assert not any(o.hide_render for o in objects),'SPEAKING_ANATOMY_HIDDEN'
 for o in objects:
  ev=o.evaluated_get(dg);rig=o.parent;into=rig.matrix_world.inverted()@o.matrix_world;back=into.inverted();posed=[v.co.copy() for v in ev.data.vertices]
  assert len(posed)==len(o.data.vertices)
  for i in range(0,len(posed),max(1,len(posed)//257)):
   v=o.data.vertices[i];rest=v.co.copy()
   if o.data.shape_keys:
    base=o.data.shape_keys.key_blocks[0].data[i].co
    rest=base.copy()
    for k in o.data.shape_keys.key_blocks[1:]:rest+=(k.data[i].co-base)*k.value
   p=Vector((0,0,0));total=0
   for g in v.groups:
    name=o.vertex_groups[g.group].name;m=back@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@into;p+=(m@rest)*g.weight;total+=g.weight
   assert abs(total-1)<.005,'ORAL_WEIGHT_NOT_NORMALIZED'
   error=(p-posed[i]).length;maximum=max(maximum,error);assert error<2e-5,'ORAL_BINDING_MISMATCH'
   assert all(math.isfinite(x) for x in posed[i])
  if o.name not in first:first[o.name]=posed
  movement[o.name]=max(movement.get(o.name,0),max((p-q).length for p,q in zip(posed,first[o.name])))
scene.frame_set(1);fv=body.data.shape_keys.key_blocks['V3_FV'];old_fv=fv.value;fv.value=1;bpy.context.view_layer.update();assert not any(o.hide_render for o in objects),'FV_TEETH_INCORRECTLY_HIDDEN';fv.value=old_fv;scene.frame_set(998)
assert all(v>.001 for v in movement.values()),'ORAL_OBJECT_DID_NOT_MOVE'
assert identity()==before
result={'character':character,'profile':module['PROFILE'],'moduleSHA256':module['MODULE_SHA256'],'sourceIdentityHash':before,'allOriginalMeshCoordinatesKeysWeightsUVsAndRigUnchanged':True,'restoration':report,'reapplicationStable':True,'exteriorLipMucosaExcluded':True,'closedLipVisibilityAndFVExposureVerified':True,'frames':frames,'maximumBindingErrorMetres':maximum,'observedMovementMetres':movement,'attachment':'Original head, jaw and tongue bones; no frame handlers or replacement action'}
Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_text(json.dumps(result,indent=2)+'\n');print('FACIAL_AUDIT_PASS',character,maximum,flush=True)
