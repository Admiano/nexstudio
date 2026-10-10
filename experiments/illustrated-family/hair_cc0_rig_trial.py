"""Unapproved MakeHuman CC0 hair variant on a disposable, already-rigged V1 suit.

Use real .mhclo morph fitting, native Host.rig, existing illustrated hair
material. Never modify the canonical original or generate fake raster hair.
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
gender,render_path,asset_path=args[:3]
assert gender in ("female","male")
base=Path(render_path).resolve();base.parent.mkdir(parents=True,exist_ok=True)
asset=Path(asset_path).resolve()
if not asset.is_file():raise RuntimeError("SELECTED_LICENSED_HAIR_NOT_FOUND")
head="\n".join(asset.read_text(errors="replace").splitlines()[:45]).lower()
import re
allowed=(bool(re.search(r"(?m)^\\s*#\\s*license\\s*:?\\s*cc0\\s*$",head)) or
         (asset.parent.name.startswith("cortu_") and
          "# cortu johnstone - cc0" in head))
if not allowed:
    raise RuntimeError("DONOR_HAIR_WITHOUT_INDIVIDUAL_CC0_DECLARATION:"+asset.name)
repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"engine_sources/makehuman-lineart/scripts"))
import mhclo_fit as F
rig=bpy.data.objects["Host.rig"]
body=bpy.data.objects["Host.body"]
assert len(rig.data.bones)==163 and len(body.data.shape_keys.key_blocks)==34
scene=bpy.context.scene
scene.frame_set(27)
rig.data.pose_position="REST"
bpy.context.view_layer.update()
coords,refs=F.fit(str(asset),F.shaped_coords(body))
_,_,obj_file=F.load_mhclo(str(asset))
objverts,faces=F.load_obj(obj_file)
assert len(coords)==len(objverts) and len(coords)>=90 and len(faces)>=70, "MHCLO_HAIR_FIT_MISMATCH"
originals=[o for o in bpy.data.objects if o.name.startswith("Host.hair_") and o.type=="MESH" and not o.hide_render]
assert len(originals)==1,(gender,[x.name for x in originals])
original=originals[0]
world=original.matrix_world.copy()
mesh=bpy.data.meshes.new("NEX_V1_CC0_HAIR_"+asset.parent.name+"_MESH")
inv=world.inverted()
mesh.from_pydata([inv@p for p in coords],[],faces)
mesh.update()
for f in mesh.polygons:f.use_smooth=True
hair=bpy.data.objects.new("NEX_V1_CC0_HAIR_"+asset.parent.name,mesh)
scene.collection.objects.link(hair)
hair.parent=rig
hair.matrix_world=world
mat=bpy.data.materials.get("LINEART_HAIR_PAPER")
if mat is None:raise RuntimeError("CANONICAL_V1_ILLUSTRATED_HAIR_MATERIAL_MISSING")
mesh.materials.append(mat)
assert "head" in rig.data.bones
vg_head=hair.vertex_groups.new(name="head")
vg_neck=hair.vertex_groups.new(name="neck01") if "neck01" in rig.data.bones else None
# Keep short, bun, and cropped styles attached to the animated head; only a
# tiny lower-neck influence is needed on locks extending below the jaw.
for vertex,p in zip(mesh.vertices,coords):
    if vg_neck is not None and p.z<1.40:
        vg_head.add([vertex.index],.85,"REPLACE")
        vg_neck.add([vertex.index],.15,"REPLACE")
    else:
        vg_head.add([vertex.index],1.0,"REPLACE")
arm=hair.modifiers.new("Original V1 head bone deformation","ARMATURE")
arm.object=rig
sub=hair.modifiers.new("Illustrated hair smoothness trial","SUBSURF")
sub.levels=1;sub.render_levels=1
original.hide_render=True
original.hide_viewport=True
rig.data.pose_position="POSE"
scene.frame_set(27)
bpy.context.view_layer.update()
hair["sourcePack"]="hair01_cc0"
hair["sourceDonor"]=asset.parent.name
hair["license"]="CC0 — explicit in donor .mhclo"
hair["approved"]=False
hair["originalHair"]=original.name
report={
  "gender":gender,"donor":asset.parent.name,
  "originalHair":original.name,"originalHiddenInDisposableScene":True,
  "originalRig":rig.name,"sourceMHClOVertexCount":len(coords),
  "faces":len(faces),"headSkinning":True,
  "originalBodyShapeKeys":len(body.data.shape_keys.key_blocks),
  "suitRetained":"NEX_V1_CC0_FORMAL_SUIT_"+gender.upper() in bpy.data.objects,
  "status":"UNAPPROVED_CC0_HAIR_NEUTRAL_AND_GESTURE_VISUAL_REVIEW_REQUIRED"
}
bpy.ops.wm.save_as_mainfile(filepath=str(base.with_suffix(".blend")),compress=True,copy=True)
base.with_name(base.stem+"-hair.json").write_text(json.dumps(report,indent=2)+"\n")
print("REAL_HAIR_FAMILY_TRIAL_CREATED",json.dumps(report),flush=True)
