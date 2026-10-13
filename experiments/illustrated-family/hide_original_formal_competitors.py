"""Hide redundant V17 corrected-Cast garment decorations and posed-fit proxies for the disposable CC0 formal refit.

Keeps character body, original rig, hands, face, skin, hair, and shoes. Never edits the canonical scene.
"""
import bpy,json
gender="male" if bpy.data.objects.get("Host.mindfront_male_trousers_2") else "female"
if gender=="male":
    legacy={"Host.elvs_male_shirt_untucked_bd1","Host.mindfront_male_trousers_2"}
else:
    legacy={"Host.mindfront_f_dress_11"}
source_materials=set()
for name in legacy:
    obj=bpy.data.objects.get(name)
    if obj and obj.type=="MESH":
        source_materials.update(m for m in obj.data.materials if m)
sources=set(legacy)
removed=[]
for _ in range(6):
    for ob in bpy.data.objects:
        if ob.type!="MESH" or ob.name.startswith("NEX_V1_CC0_FORMAL_SUIT_") or ob.name in sources:continue
        markers=[ob.get("castFitSource"),ob.get("castGarmentSource"),ob.get("castFitOriginalHideRender")]
        parents=markers[:2]
        if any(isinstance(p,str) and p in sources for p in parents):
            sources.add(ob.name)
for ob in bpy.data.objects:
    if ob.type!="MESH" or ob.name.startswith("NEX_V1_CC0_FORMAL_SUIT_"):continue
    by_source=ob.name in sources or any(ob.name.startswith(name+".") for name in legacy)
    by_material=ob.name!="Host.body" and any(m in source_materials for m in ob.data.materials)
    if by_source or by_material:
        if not ob.hide_render:removed.append({"object":ob.name,"source":ob.get("castGarmentSource"),"fitSource":ob.get("castFitSource"),"materials":[m.name for m in ob.data.materials if m]})
        ob.hide_render=True
        # A V17 source garment may remain visible in viewport, but never in the trial render.
        if ob.name in legacy and not ob.hide_render:
            raise RuntimeError("LEGACY_OUTFIT_NOT_HIDDEN:"+ob.name)
print("SCENEBAM_CORRECTED_HIDE_LEGACY_GARMENTS",json.dumps({"gender":gender,"hidden":removed}),flush=True)
bpy.context.view_layer.update()
