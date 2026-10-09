"""Audit source identity, palette mapping and groom attachment over speaking poses."""
import bpy,runpy,sys,hashlib,struct,json,math,os
from pathlib import Path
from mathutils import Vector
character,style,output=sys.argv[sys.argv.index('--')+1:][:3]
module=runpy.run_path(str(Path(__file__).with_name('cast-hair-groom.py')));scene=bpy.context.scene
original=[o for o in scene.objects if o.type=='MESH']
def identity():
 h=hashlib.sha256()
 for o in sorted(original,key=lambda x:x.name):
  h.update(o.name.encode())
  for v in o.data.vertices:
   h.update(struct.pack('3d',*v.co))
   for g in v.groups:h.update(struct.pack('if',g.group,g.weight))
  if not o.name.startswith('Host.hair_'):
   for uv in o.data.uv_layers:
    for point in uv.data:h.update(struct.pack('2f',*point.uv))
  if o.data.shape_keys:
   for key in o.data.shape_keys.key_blocks:
    if o.name.startswith('Host.hair_') and key.name=='V60_tuck':continue
    h.update(key.name.encode())
    for p in key.data:h.update(struct.pack('3d',*p.co))
 for rig in [o for o in scene.objects if o.type=='ARMATURE']:
  for b in rig.data.bones:h.update(b.name.encode());h.update(struct.pack('6d',*b.head_local,*b.tail_local))
 return h.hexdigest()
before=identity();os.environ['HDYE']='';report=module['apply_hair_groom'](scene,character,style=style,density=.08)
assert identity()==before,'SOURCE_CAGE_KEYS_WEIGHTS_OR_RIG_CHANGED'
if style=='bald':
 assert report['fibres']==0 and not any(o.get('castGroomProfile') for o in scene.objects)
 Path(output).write_text(json.dumps({'style':style,'character':character,'sourceIdentityUnchanged':True,'baldHasNoFibres':True},indent=2));print('HAIR_AUDIT_PASS',style);raise SystemExit(0)
curve=bpy.data.objects[report['object']];binding=bpy.data.objects[report['binding']]
counts=(len(bpy.data.objects),len(bpy.data.materials),len(curve.data.points));nodes=[len(m.node_tree.nodes) for m in (curve.data.materials[0],bpy.data.objects[report['sourceHair']].data.materials[0])]
colours=['9A4A2E','1C1714','3B2418','D8B77A','B9B8B5'] if character=='female' else ['1C1714','C9A366','5A3A24','141212','8F9096']
palettes=[]
for c in colours+['3D6581']:
 dye='8A1F3C' if character=='male' and c=='141212' else '';mapping=module['set_hair_colour'](scene,c,dye)
 material=curve.data.materials[0];t=material.node_tree
 expected=module['linear_hex'](c)
 assert all(abs(a-b*.7)<1e-7 for a,b in zip(t.nodes['Root to tip pigment'].inputs[1].default_value,expected))
 assert t.nodes['Enable tip dye'].inputs[1].default_value==(1 if dye else 0)
 palettes.append(mapping)
assert counts==(len(bpy.data.objects),len(bpy.data.materials),len(curve.data.points))
assert nodes==[len(m.node_tree.nodes) for m in (curve.data.materials[0],bpy.data.objects[report['sourceHair']].data.materials[0])]
module['apply_hair_groom'](scene,character,style=style)
assert counts==(len(bpy.data.objects),len(bpy.data.materials),len(curve.data.points))
rest=[tuple(curve.data.position_data[i].vector) for i in range(0,len(curve.data.points),max(1,len(curve.data.points)//257))]
pigment=[p.value for p in curve.data.attributes['cast_groom_dye'].data]
frames=[1,27,71,106,160,260,360,500,650,820,998];maximum=0;movement=0;first=None
for frame in frames:
 scene.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get();ev=curve.evaluated_get(dg);helper=binding.evaluated_get(dg)
 values=[]
 for i in range(0,len(curve.data.points),max(1,len(curve.data.points)//257)):
  p=ev.data.points[i].position;q=helper.data.vertices[i].co
  assert all(math.isfinite(x) for x in p)
  error=(p-q).length;maximum=max(maximum,error);assert error<2e-6,'GROOM_BINDING_SLIPPED'
  values.append(p.copy())
 if first is None:first=values
 else:movement=max(movement,max((p-q).length for p,q in zip(values,first)))
assert maximum<2e-6 and movement>.001
assert rest==[tuple(curve.data.position_data[i].vector) for i in range(0,len(curve.data.points),max(1,len(curve.data.points)//257))]
assert pigment==[p.value for p in curve.data.attributes['cast_groom_dye'].data]
assert identity()==before
result={'character':character,'style':style,'sourceIdentityHash':before,'sourceIdentityUnchanged':True,'identityScope':'All original mesh cages and weights, original non-hair UVs and shape keys, original rig bones; static long-hair V60_tuck refinement and recovered hair UVs are authorized changes','auditDensity':.08,'groom':report,'paletteMaps':palettes,'reapplicationStable':True,'restCoordinatesAndDyeStable':True,'frames':frames,'sampledPointsPerFrame':len(first),'maximumBindingErrorMetres':maximum,'maximumObservedMovementMetres':movement,'deformation':'Existing head, neck and spine weights; no simulated hair physics'}
Path(output).write_text(json.dumps(result,indent=2)+'\n');print('HAIR_AUDIT_PASS',character,style,len(frames),flush=True)
