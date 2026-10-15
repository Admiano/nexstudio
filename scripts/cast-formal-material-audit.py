"""Audit authentic formal geometry, connected mesh regions, and UV texture atlas."""
import bpy,json,sys
from pathlib import Path
from collections import defaultdict
kind=sys.argv[sys.argv.index('--')+1]
out=Path(sys.argv[sys.argv.index('--')+2])
name='SCENEBAM_FORMAL_'+kind.upper().replace('-','_')
obj=bpy.data.objects.get(name)
if not obj or obj.type!='MESH':raise RuntimeError('CAST_FORMAL_OBJECT_NOT_FOUND:'+name)
mesh=obj.data
parent=list(range(len(mesh.vertices)))
def find(a):
 while a!=parent[a]:
  parent[a]=parent[parent[a]]
  a=parent[a]
 return a
for edge in mesh.edges:
 a,b=edge.vertices
 x,y=find(a),find(b)
 if x!=y:parent[x]=y
sizes=defaultdict(list)
for i in range(len(mesh.vertices)):sizes[find(i)].append(i)
faces=defaultdict(list)
for idx,poly in enumerate(mesh.polygons):faces[find(poly.vertices[0])].append(idx)
uv=mesh.uv_layers.active
regions=[]
for root,verts in sizes.items():
 pts=[obj.matrix_world@mesh.vertices[i].co for i in verts]
 bounds=[[min(p[a] for p in pts),max(p[a] for p in pts)] for a in range(3)]
 uvpoints=[uv.data[loop].uv[:] for f in faces[root] for loop in mesh.polygons[f].loop_indices] if uv else []
 uvbounds=[[min(p[a] for p in uvpoints),max(p[a] for p in uvpoints)] for a in range(2)] if uvpoints else None
 regions.append({'vertices':len(verts),'faces':len(faces[root]),'bounds':bounds,'uvBounds':uvbounds,
                 'polyIndices':faces[root][:12]})
regions.sort(key=lambda a:a['faces'],reverse=True)
materials=[]
textures=[]
for slot,m in enumerate(mesh.materials):
 if not m:continue
 nd=m.node_tree.nodes if m.use_nodes and m.node_tree else []
 images=[n.image for n in nd if n.type=='TEX_IMAGE' and n.image]
 materials.append({'slot':slot,'material':m.name,'faces':sum(p.material_index==slot for p in mesh.polygons),
                   'nodes':[n.type for n in nd], 'images':[{'name':im.name,'width':im.size[0],'height':im.size[1],'packed':bool(im.packed_file)} for im in images]})
 for im in images:
  if im not in textures:
   textures.append(im)
out.parent.mkdir(parents=True,exist_ok=True)
files=[]
for i,im in enumerate(textures):
 path=out.with_name(out.stem+'-texture'+str(i)+'.png')
 try:
  im.save_render(str(path),scene=bpy.context.scene)
  files.append(str(path))
 except Exception as exc:
  files.append('FAILED:'+str(exc))
report={'kind':kind,'materials':materials,'regions':regions[:100],'regionCount':len(regions),
        'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'textures':files}
out.write_text(json.dumps(report,indent=2)+'\n')
print('CAST_FORMAL_GEOMETRY_AUDIT',json.dumps({'kind':kind,'regions':len(regions),'materialCount':len(materials),
 'largest':regions[:25],'texturePaths':files}),flush=True)
