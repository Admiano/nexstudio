"""Read-only material segmentation audit of real SceneBam production-assembled formals."""
import bpy, sys, json
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:]
look,out=args[:2]
name='SCENEBAM_FORMAL_'+look.upper().replace('-','_')
obj=bpy.data.objects.get(name)
if obj is None:raise RuntimeError('FORMAL_GARMENT_MISSING:'+name)
counts={}
for poly in obj.data.polygons:
    counts[poly.material_index]=counts.get(poly.material_index,0)+1
materials=[]
for i,mat in enumerate(obj.data.materials):
    if not mat:continue
    nodes=[]
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type in ('BSDF_PRINCIPLED','EMISSION'):
                field='Base Color' if node.type=='BSDF_PRINCIPLED' else 'Color'
                socket=node.inputs.get(field)
                nodes.append({'type':node.type,'name':node.name,'hasColorSocket':bool(socket),'colorLinked':bool(socket and socket.is_linked)})
    materials.append({'slot':i,'name':mat.name,'polygons':counts.get(i,0),'role':mat.get('scenebamColorRole'),'nodes':nodes,'diffuseColor':list(mat.diffuse_color)})
# Determine whether the original source has separately assignable garment islands.
parent=list(range(len(obj.data.vertices)))
def root(v):
    while parent[v]!=v:
        parent[v]=parent[parent[v]]
        v=parent[v]
    return v
def union(a,b):
    a=root(a);b=root(b)
    if a!=b:parent[max(a,b)]=min(a,b)
for edge in obj.data.edges:union(*edge.vertices)
components={}
for face in obj.data.polygons:
    k=root(face.vertices[0]);t=components.setdefault(k,{'polygons':0,'vertices':set()})
    t['polygons']+=1;t['vertices'].update(face.vertices)
islands=[]
for item in components.values():
    idx=list(item['vertices'])
    coords=[obj.matrix_world@obj.data.vertices[n].co for n in idx]
    bounds=[[round(min(p[d] for p in coords),4),round(max(p[d] for p in coords),4)] for d in range(3)]
    islands.append({'polygons':item['polygons'],'vertices':len(idx),'worldBoundsXYZ':bounds})
islands.sort(key=lambda x:x['polygons'],reverse=True)
report={'look':look,'garmentObject':name,'vertexCount':len(obj.data.vertices),'materialSlots':materials,'islandCount':len(islands),'largestIslands':islands[:18],'armatureModifiers':sum(m.type=='ARMATURE' for m in obj.modifiers),'rigBones':len(bpy.data.objects['Host.rig'].data.bones)}
Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(report,indent=2)+'\n');print('SCENEBAM_FORMAL_INSPECT',json.dumps(report),flush=True)
