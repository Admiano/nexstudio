"""Audit original V1 hairstyling and head-motion attachments without edits."""
import bpy,json,sys
from pathlib import Path
args=sys.argv[sys.argv.index("--")+1:]
gender,outfile=args[:2]
assert gender in ("female","male")
p=Path(outfile).resolve();p.parent.mkdir(parents=True,exist_ok=True)
rig=bpy.data.objects.get("Host.rig")
body=bpy.data.objects.get("Host.body")
assert rig and body
objs=[]
for obj in bpy.data.objects:
    if "hair" not in obj.name.lower() and "scalp" not in obj.name.lower():
        continue
    objdata={
        "name":obj.name,"type":obj.type,"hidden":obj.hide_render,
        "parent":obj.parent.name if obj.parent else None,
        "parentType":obj.parent_type,"parentBone":obj.parent_bone,
        "collections":[c.name for c in obj.users_collection],
        "materials":[m.name if m else None for m in getattr(obj.data,"materials",[])],
        "rigModifiers":[{"type":m.type,"target":m.object.name if m.type=="ARMATURE" and m.object else None} for m in obj.modifiers if m.type in ("ARMATURE","SHRINKWRAP","MASK")],
    }
    if obj.type=="MESH":
        objdata["vertices"]=len(obj.data.vertices)
        objdata["faces"]=len(obj.data.polygons)
        objdata["groups"]=[g.name for g in obj.vertex_groups][:24]
    objs.append(objdata)
summary={"gender":gender,"scene":bpy.data.filepath,"blender":bpy.app.version_string,
         "rigBones":len(rig.data.bones),
         "shapeKeys":len(body.data.shape_keys.key_blocks),
         "hairCandidates":objs,
         "status":"INSPECTION_ONLY_CANONICAL_SCENES_UNCHANGED"}
p.write_text(json.dumps(summary,indent=2)+"\n")
print("ORIGINAL_V1_HAIR_ATTACHMENTS",gender,len(objs),json.dumps([x["name"] for x in objs]),flush=True)
