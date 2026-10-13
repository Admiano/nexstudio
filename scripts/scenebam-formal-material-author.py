"""Author individually tintable suit/tie materials on original connected Blender regions.

Applies ONLY to the six hashed source proof files. Island polygon counts are
strict per-source contracts; a topology change stops output rather than guesses.
This does not certify artistic quality, full-body motion or deployment parity.
"""
import bpy,sys,re,json,hashlib,math
from collections import Counter,defaultdict
from pathlib import Path

arg=sys.argv[sys.argv.index('--')+1:]
look,outdir=arg[:2]
outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True)
name='SCENEBAM_FORMAL_'+look.upper().replace('-','_')
obj=bpy.data.objects.get(name)
if obj is None or obj.type!='MESH':raise RuntimeError('EXPECTED_SOURCE_GARMENT_MISSING:'+name)
if len(bpy.data.objects['Host.rig'].data.bones)!=163:raise RuntimeError('NOT_SCENEBAM_RIG')
if len(obj.data.materials)!=1:raise RuntimeError('SOURCE_GARMENT_CHANGED_MATERIALS')
# Explicit component sizes from the genuine six-outfit production assembly
# inspected on GitHub Actions 38482621380; never reuse on other meshes.
expected={
 'female-double-breasted':{'suit':(1672,1601),'tie':(436,)},
 'female-statement':{'suit':(4103,2008),'tie':(616,)},
 'male-jacket-tie':{'suit':(6267,1094),'tie':(678,382)},
 'male-double-breasted':{'suit':(1672,1601),'tie':(436,)},
 'male-navy-classic':{'suit':(4121,2008),'tie':(616,)},
 'male-dinner-jacket':{'suit':(2666,986),'tie':(580,580,316)},
}
if look not in expected:raise RuntimeError('UNKNOWN_FORMAL_SOURCE')
mesh=obj.data
parent=list(range(len(mesh.vertices)))
def root(v):
 while parent[v]!=v:
  parent[v]=parent[parent[v]];v=parent[v]
 return v
def union(a,b):
 a=root(a);b=root(b)
 if a!=b:parent[max(a,b)]=min(a,b)
for edge in mesh.edges:union(*edge.vertices)
islands=defaultdict(list)
for poly in mesh.polygons:islands[root(poly.vertices[0])].append(poly.index)
counts=Counter(len(v) for v in islands.values())
needed=Counter(expected[look]['suit']+expected[look]['tie'])
for size,num in needed.items():
 if counts[size]<num:raise RuntimeError('ISLAND_TOPOLOGY_CHANGED:'+str((size,num,counts[size])))
def coords_for(polyids):
 vertexids={vertex for i in polyids for vertex in mesh.polygons[i].vertices}
 return [obj.matrix_world@mesh.vertices[i].co for i in vertexids]
chosen={'suit':[],'tie':[]};selected=set()
for role in ('suit','tie'):
 for size in expected[look][role]:
  options=[(key,inds) for key,inds in islands.items() if key not in selected and len(inds)==size]
  if not options:raise RuntimeError('EXPECTED_ROLE_ISLAND_MISSING:'+role+':'+str(size))
  # Tie islands must be located on the upper center chest, rather than
  # buttons or cuffs with accidentally matching polygon counts.
  if role=='tie':
   options=[(key,inds) for key,inds in options if (
    (lambda P: min(p.z for p in P)>1.14 and max(abs(p.x) for p in P)<.11)(coords_for(inds)))]
  if len(options)!=1 and not (role=='tie' and look=='male-dinner-jacket' and size==580 and len(options)==2):
   raise RuntimeError('AMBIGUOUS_ROLE_ISLAND:'+role+':'+str(size)+':'+str(len(options)))
  key,inds=options[0]
  selected.add(key)
  chosen[role].extend(inds)
assert chosen['suit'] and chosen['tie'] and not set(chosen['suit'])&set(chosen['tie'])
# Assign role-targeted copies of the original material to separate polygon
# groups. Original UVs, texture shader, rig, body and other objects persist.
mesh=mesh.copy();obj.data=mesh
old=mesh.materials[0]
for role in ('suit','tie'):
 mat=old.copy()
 mat.name='SCENEBAM_FORMAL_ROLE_'+role.upper()+'_'+look
 mat['scenebamColorRole']=role
 mesh.materials.append(mat)
 index=len(mesh.materials)-1
 for pid in chosen[role]:mesh.polygons[pid].material_index=index
 obj['scenebamSuitTieMasked']=True
obj['scenebamMaskMethod']='explicit-validated-topology-islands'
for role in ('suit','tie'):
 if not any(m and m.get('scenebamColorRole')==role for m in mesh.materials):
  raise RuntimeError('ROLE_TAGGING_FAILED:'+role)
# Preserve rest shape and original render scene before experimental recoloring.
sourcefile=outdir/(look+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(sourcefile),compress=True)
source_sha=hashlib.sha256(sourcefile.read_bytes()).hexdigest()

def linear(hexstr):
 v=[int(hexstr[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v)
def tune(role,color):
 mat=next(m for m in mesh.materials if m and m.get('scenebamColorRole')==role)
 mat.use_nodes=True
 tree=mat.node_tree
 emission=next((n for n in tree.nodes if n.type=='EMISSION'),None)
 if not emission or not emission.inputs['Color'].is_linked:raise RuntimeError('SOURCE_TEXTURE_GRAPH_CHANGED')
 oldlink=emission.inputs['Color'].links[0]
 upstream=oldlink.from_socket
 tree.links.remove(oldlink)
 gray=tree.nodes.new('ShaderNodeRGBToBW');gray.name='SceneBam preserve original fabric detail'
 tree.links.new(upstream,gray.inputs['Color'])
 shade=tree.nodes.new('ShaderNodeMapRange');shade.name='SceneBam wardrobe luminance';shade.clamp=True
 shade.inputs['From Min'].default_value=.02
 shade.inputs['From Max'].default_value=.8
 shade.inputs['To Min'].default_value=.36
 shade.inputs['To Max'].default_value=1.05
 tree.links.new(gray.outputs['Val'],shade.inputs['Value'])
 mix=tree.nodes.new('ShaderNodeMixRGB');mix.name='SceneBam selectable '+role+' color';mix.blend_type='MULTIPLY'
 mix.inputs[0].default_value=1
 mix.inputs[1].default_value=(*linear(color),1)
 tree.links.new(shade.outputs['Result'],mix.inputs[2])
 tree.links.new(mix.outputs['Color'],emission.inputs['Color'])
 return mix
shader={role:tune(role,col) for role,col in (('suit','283C72'),('tie','8E2B42'))}
scene=bpy.context.scene
scene.frame_set(27)
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
scene.render.resolution_x=540;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.film_transparent=True;scene.render.image_settings.color_mode='RGBA'
scene.render.image_settings.file_format='PNG'
output=[]
for take,suit,tie in [('A','283C72','8E2B42'),('B','283C72','D5C8A8'),('C','8D2B48','D5C8A8')]:
 shader['suit'].inputs[1].default_value=(*linear(suit),1)
 shader['tie'].inputs[1].default_value=(*linear(tie),1)
 path=outdir/(look+'-'+take+'.png')
 scene.render.filepath=str(path)
 bpy.ops.render.render(write_still=True)
 if path.stat().st_size<10000:raise RuntimeError('COLOR_TEST_RENDER_EMPTY')
 output.append({'variant':take,'suitHex':suit,'tieHex':tie,'render':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
report={'source':look,'blendFile':sourcefile.name,'blendSHA256':source_sha,
 'garmentVertexCount':len(mesh.vertices),'garmentFaces':len(mesh.polygons),
 'roles':{role:{'polygonCount':len(chosen[role]),'connectedIslands':len(expected[look][role])} for role in chosen},
 'untouchedMaterialFaces':len(mesh.polygons)-len(chosen['suit'])-len(chosen['tie']),
 'rigBones':163,'sourceTexturePreserved':True,'output':output,
 'liveVmHashMatched':False,'artApproved':False,'fullCollisionCertified':False}
(outdir/(look+'-palette-report.json')).write_text(json.dumps(report,indent=2)+'\n')
print('SCENEBAM_FORMAL_PALETTE_PROOF',json.dumps(report),flush=True)
