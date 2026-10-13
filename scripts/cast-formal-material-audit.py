"""Inspect actual rigged formal garment slots; fail if independent colour isn't possible."""
import bpy,json,sys
from pathlib import Path
kind=sys.argv[sys.argv.index('--')+1]
out=Path(sys.argv[sys.argv.index('--')+2])
name='SCENEBAM_FORMAL_'+kind.upper().replace('-','_')
o=bpy.data.objects.get(name)
if not o or o.type!='MESH':raise RuntimeError('CAST_FORMAL_OBJECT_NOT_FOUND:'+name)
tie=[];fabric=[];other=[]
for slot,m in enumerate(o.data.materials):
 if not m:continue
 lower=m.name.lower().replace(' ','_')
 record={'slot':slot,'material':m.name,'diffuse':[round(float(x),5) for x in m.diffuse_color],
         'faces':sum(poly.material_index==slot for poly in o.data.polygons),
         'nodes':[node.type for node in m.node_tree.nodes] if m.use_nodes and m.node_tree else []}
 if any(w in lower for w in ('necktie','bowtie','bow_tie','tie','cravat')):tie.append(record)
 elif any(w in lower for w in ('button','metal','shoe','sole','skin','shirt','watch','hair','eye','teeth','neck')):other.append(record)
 else:fabric.append(record)
result={'kind':kind,'suit':fabric,'tie':tie,'other':other,'allSlots':len(o.data.materials),'garmentVertices':len(o.data.vertices)}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+'\n')
print('CAST_FORMAL_MATERIAL_INVENTORY',json.dumps(result),flush=True)
if not tie or not fabric:
 print('CAST_FORMAL_COLOUR_ROLE_GATE_FAILED',kind,flush=True)
 sys.exit(22)
