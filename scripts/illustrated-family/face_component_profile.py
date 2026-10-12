"""Read-only component map of canonical illustrated facial ink (head stills authority)."""
import bpy, json, sys, collections
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
gender,out=argv[0],Path(argv[1]).resolve()
out.parent.mkdir(parents=True,exist_ok=True)
rig=bpy.data.objects["Host.rig"]
wanted=[n for n in bpy.data.objects if n.name.startswith("Host.") and
    (any(s in n.name.lower() for s in ("v59_face","eyebrow","eyelash","pupil","v10_nose","v10_jaw",
                                        "mouth","lip","ear")))]
def box(ps):
    return [round(min(p[k] for p in ps),5) for k in range(3)]+[round(max(p[k] for p in ps),5) for k in range(3)]
def map_mesh(o):
    vertices=o.data.vertices
    adj=[[] for _ in range(len(vertices))]
    for e in o.data.edges:
        a,b=e.vertices
        adj[a].append(b);adj[b].append(a)
    remaining=set(range(len(vertices)))
    comps=[]
    while remaining:
        start=next(iter(remaining));todo=[start];remaining.remove(start);inds=[]
        while todo:
            v=todo.pop();inds.append(v)
            for j in adj[v]:
                if j in remaining:remaining.remove(j);todo.append(j)
        ps=[o.matrix_world@vertices[i].co for i in inds]
        most=collections.Counter()
        for vi in inds:
            for g in vertices[vi].groups:
                try:most[o.vertex_groups[g.group].name]+=g.weight
                except:pass
        comps.append({"vertexCount":len(inds),
                      "boundsXYZ":box(ps),
                      "centerXYZ":[round(sum(p[k] for p in ps)/len(ps),5) for k in range(3)],
                      "dominantGroups":[k for k,_ in most.most_common(6)]})
    return {"name":o.name,"meshVertices":len(vertices),"faces":len(o.data.polygons),
            "components":sorted(comps,key=lambda a:a["vertexCount"],reverse=True)[:90],
            "shapeKeys":[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],
            "parent":o.parent.name if o.parent else None,"parentType":o.parent_type,
            "materialNames":[m.name for m in o.data.materials if m]}
report={"gender":gender,"scene":bpy.data.filepath,"blender":bpy.app.version_string,
        "headBone":list(rig.pose.bones["head"].head),"eyeBones":{},
        "objects":[map_mesh(o) for o in wanted if o.type=="MESH"]}
for key in ("eye.L","eye.R","head","jaw"):
    if key in rig.pose.bones:
        p=rig.matrix_world@rig.pose.bones[key].head
        report["eyeBones"][key]=list(p)
out.write_text(json.dumps(report,indent=2))
print("REAL_FACE_COMPONENT_PROFILE",gender,len(report["objects"]),out,flush=True)
