"""Read-only census for leftover V1 dress proxy lines in alternative suit outfits."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
p=Path(sys.argv[sys.argv.index("--")+1]).resolve()
p.parent.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene
s.frame_set(27)
bpy.context.view_layer.update()
entries=[]
for ob in sorted(bpy.data.objects,key=lambda x:x.name):
    if not ob.name.startswith("Host.") or ob.type!="MESH":continue
    box=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    if not box:continue
    low=min(x.z for x in box);high=max(x.z for x in box)
    interesting=(low<.95 and high>.50 and any(abs(x.x+.42)<.30 for x in box))
    if not interesting and not any(w in ob.name.lower() for w in ("dress","cloth","hem","skirt","lineart","garment")):continue
    entries.append({"name":ob.name,
      "hideRender":ob.hide_render, "hideViewport":ob.hide_viewport,
      "hasBodyArmature":any(m.type=="ARMATURE" for m in ob.modifiers),
      "vertexCount":len(ob.data.vertices),
      "bbox":[round(low,4),round(high,4)],
      "collectionNames":[c.name for c in ob.users_collection],
      "materials":[m.name if m else None for m in ob.data.materials[:3]],
      "parents":ob.parent.name if ob.parent else None})
report={"scene":bpy.data.filepath,"frame":s.frame_current,
        "items":entries,"total":len(entries),"blender":bpy.app.version_string}
p.write_text(json.dumps(report,indent=2))
for e in entries:print("FEMALE_LAYER_DIAGNOSTIC",e["name"],e["hideRender"],e["bbox"],e["collectionNames"],flush=True)
