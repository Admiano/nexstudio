"""Validate the illustrated finish against an actual assembled character."""
import bpy,runpy,sys,json,hashlib,struct,math
from pathlib import Path
sex,out=sys.argv[sys.argv.index('--')+1:][:2];scene=bpy.context.scene
module=runpy.run_path(str(Path(__file__).with_name('cast-skin-appearance.py')))
meshes=[o for o in scene.objects if o.type=='MESH'];rigs=[o for o in scene.objects if o.type=='ARMATURE']
def geometry_identity():
 h=hashlib.sha256()
 for ob in sorted(meshes,key=lambda o:o.name):
  h.update(ob.name.encode())
  for v in ob.data.vertices:
   h.update(struct.pack('3d',*v.co))
   for g in v.groups:h.update(struct.pack('if',g.group,g.weight))
  for uv in ob.data.uv_layers:
   for v in uv.data:h.update(struct.pack('2f',*v.uv))
  if ob.data.shape_keys:
   for key in ob.data.shape_keys.key_blocks:
    h.update(key.name.encode())
    for v in key.data:h.update(struct.pack('3d',*v.co))
 for rig in rigs:
  for b in rig.data.bones:h.update(b.name.encode());h.update(struct.pack('6d',*b.head_local,*b.tail_local))
 return h.hexdigest()
before=geometry_identity();rows=[]
for hx in module['MAKEUP']:
 report=module['apply_skin_appearance'](scene,sex,hx)
 mat=bpy.data.materials['PEEPS_V2_WARM_SKIN'];tree=mat.node_tree;skin=tree.nodes['Illustrated skin output'];output=tree.nodes['Material Output']
 assert output.inputs['Surface'].links[0].from_node==skin,'ILLUSTRATED_OUTPUT_MISSING'
 assert not any(n.type in ('BSDF_PRINCIPLED','BSDF_GLOSSY','BUMP') for n in tree.nodes),'PHYSICAL_SKIN_REMAINED'
 assert all(abs(a-b)<1e-7 for a,b in zip(mat['castSkinBase'],module['linear_rgb'](hx))),'SELECTED_COMPLEXION_CHANGED'
 assert tree.nodes.get('Painted shadow midtone and light') and tree.nodes.get('Original lip boundary')
 assert all(not m['pores'] and not m['viewDependentSheen'] for m in report['materials'])
 rows.append({'hex':hx,'palette':report['makeup'],'baseLinear':list(mat['castSkinBase'])})
lights=[o for o in scene.objects if o.name.startswith('Cast skin V13 ')];assert len(lights)==3
counts=(len(bpy.data.objects),len(bpy.data.materials),len(bpy.data.materials['PEEPS_V2_WARM_SKIN'].node_tree.nodes))
module['apply_skin_appearance'](scene,sex,'F1D7C8');assert counts==(len(bpy.data.objects),len(bpy.data.materials),len(bpy.data.materials['PEEPS_V2_WARM_SKIN'].node_tree.nodes)),'NON_IDEMPOTENT_FINISH'
fixed=[tuple(o.location) for o in lights];attributes=bpy.data.objects['Host.body'].data.attributes
rest_hash=hashlib.sha256(b''.join(struct.pack('3d',*v.vector) for v in attributes['cast_skin_rest'].data)).hexdigest()
for frame in [1,27,71,106,260,500,998]:
 scene.frame_set(frame);module['apply_skin_appearance'](scene,sex,'F1D7C8')
 assert fixed==[tuple(o.location) for o in lights],'POSE_CHANGED_LIGHTING'
 assert rest_hash==hashlib.sha256(b''.join(struct.pack('3d',*v.vector) for v in attributes['cast_skin_rest'].data)).hexdigest(),'POSE_CHANGED_TEXTURE_COORDINATES'
if sex=='female':
 custom=module['linear_rgb']('AF756B');module['apply_skin_appearance'](scene,sex,'9E6B4A',lip_hex='AF756B');got=bpy.data.materials['PEEPS_V2_WARM_SKIN']['castLipColors'];assert all(abs(a-b)<1e-7 for a,b in zip(got[3:],custom)),'CUSTOM_LIP_COLOUR_LOST'
module['apply_skin_appearance'](scene,sex,'987765');assert all(abs(a-b)<1e-7 for a,b in zip(bpy.data.materials['PEEPS_V2_WARM_SKIN']['castSkinBase'],module['linear_rgb']('987765'))),'CUSTOM_SKIN_COLOUR_LOST'
assert geometry_identity()==before,'SOURCE_GEOMETRY_OR_RIG_CHANGED'
result=dict(character=sex,profile=module['PROFILE'],codeSHA256=hashlib.sha256(Path(__file__).with_name('cast-skin-appearance.py').read_bytes()).hexdigest(),sourceMeshKeysWeightsUVsAndBonesUnchanged=True,physicalSkinRemoved=True,poreReliefRemoved=True,viewDependentSheenRemoved=True,sourceGeometrySHA256=before,complexions=rows,customColoursPreserved=True,reapplicationStable=True,textureCoordinatesStableDuringAnimation=True,lightingStableAcrossFrames=True,frames=[1,27,71,106,260,500,998])
Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(result,indent=2)+'\n');print('SKIN_APPEARANCE_AUDIT_PASS',sex,flush=True)
