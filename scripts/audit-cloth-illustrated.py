import bpy,sys,json,runpy,hashlib,os,math,numpy as np,struct
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];sex,out=args[:2];s=bpy.context.scene
req=Path(bpy.data.filepath).with_name('request.json');os.environ.update(json.loads(req.read_text())['config']['env']);os.environ.setdefault('PV1',str(Path(os.environ['CAST_SOURCE_DIR'])/'scripts'))
def protected():
 h=hashlib.sha256()
 def meta(value):h.update(json.dumps(value,sort_keys=True).encode())
 def positions(collection,property='co'):
  a=np.empty(len(collection)*3,dtype=np.float64);collection.foreach_get(property,a);h.update(a.tobytes())
 for o in s.objects:
  if o.name=='Host.body' or o.type in ('ARMATURE','CURVES') or 'hair' in o.name.lower() or o.name.startswith(('Cast V12 oral','Host.V59_face')):
   meta([o.name,o.type,list(map(list,o.matrix_world))])
   if o.type=='MESH':
    positions(o.data.vertices)
    for v in o.data.vertices:
     for g in v.groups:h.update(struct.pack('if',g.group,g.weight))
    if o.data.shape_keys:
     for k in o.data.shape_keys.key_blocks:meta([k.name,k.value]);positions(k.data)
   if o.type=='ARMATURE':meta([(b.name,list(map(list,b.matrix_local)),b.parent.name if b.parent else None) for b in o.data.bones])
   if o.type=='CURVES':positions(o.data.position_data,'vector')
 for m in bpy.data.materials:
  if m.name in ('PEEPS_V2_WARM_SKIN','V60_EAR_SKIN','LINEART_SKIN_WHITE','LINEART_HAIR_PAPER'):
   meta([m.name,[(n.name,n.type,[(i.name,list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if hasattr(i,'default_value')]) for n in m.node_tree.nodes]])
 return h.hexdigest()
s.frame_set(1);before=protected();module=runpy.run_path(str(Path(__file__).with_name('cast-cloth-illustrated.py')));report=module['apply_cloth_appearance'](s,sex);assert before==protected(),'LOCKED_BODY_HAIR_CHANGED'
rest={r['object']:hashlib.sha256(b''.join(bytes(str(list(v.vector)),'utf8') for v in bpy.data.objects[r['object']].data.attributes['cast_cloth_rest'].data)).hexdigest() for r in report['garments']}
count=(len(bpy.data.objects),len(bpy.data.materials));module['apply_cloth_appearance'](s,sex);assert before==protected();assert count==(len(bpy.data.objects),len(bpy.data.materials)),'CLOTH_REAPPLICATION_LEAK'
rows=[]
for frame in [1,27,71,338,891]:
 s.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get()
 for r in report['garments']:
  ob=bpy.data.objects[r['object']];eval=ob.evaluated_get(dg);mesh=eval.to_mesh()
  assert all(math.isfinite(v) for p in mesh.vertices for v in p.co),'NONFINITE_POSED_CLOTH'
  assert rest[ob.name]==hashlib.sha256(b''.join(bytes(str(list(v.vector)),'utf8') for v in ob.data.attributes['cast_cloth_rest'].data)).hexdigest(),'FABRIC_PATTERN_SLIDES'
  rows.append({'frame':frame,'garment':ob.name,'evaluatedVertices':len(mesh.vertices)});eval.to_mesh_clear()
for r in report['garments']:
 for mat in bpy.data.objects[r['object']].data.materials:
  assert mat['castClothBaseHex']==r['baseHex']
  assert not any(n.type in ('BSDF_PRINCIPLED','BUMP','LAYER_WEIGHT') for n in mat.node_tree.nodes),'RUBBER_SURFACE_REINTRODUCED'
customs=['4F7A93','D5C6AA','291D32']
if sex=='female':os.environ['CAST_DRESS_HEX']=customs[0]
else:os.environ['CAST_GARMENTS']=','.join(r['object'].removeprefix('Host.')+'='+customs[i%3] for i,r in enumerate(report['garments']))
custom=module['apply_cloth_appearance'](s,sex)
for i,r in enumerate(custom['garments']):
 assert r['baseHex']==customs[0 if sex=='female' else i%3], 'CUSTOM_CLOTHING_COLOUR_LOST'
s.frame_set(1);bpy.context.view_layer.update()
assert before==protected(),'CUSTOM_COLOUR_TOUCHED_SKIN_HAIR_RIG'
Path(out).write_text(json.dumps({'character':sex,'protectedSHA256':before,'skinHairRigMaterialsUnchanged':True,'idempotent':True,'customClothingColoursPreserved':True,'restSpacePatternsStable':True,'posedGarments':rows,'appearance':report},indent=2));print('CLOTH_AUDIT_PASSED',sex,flush=True)
