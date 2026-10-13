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
report={'look':look,'garmentObject':name,'vertexCount':len(obj.data.vertices),'materialSlots':materials,'armatureModifiers':sum(m.type=='ARMATURE' for m in obj.modifiers),'rigBones':len(bpy.data.objects['Host.rig'].data.bones)}
Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(report,indent=2)+'\n');print('SCENEBAM_FORMAL_INSPECT',json.dumps(report),flush=True)
