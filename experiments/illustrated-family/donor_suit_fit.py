"""NexStudio: authentic CC0 MakeHuman formal-suit donor fitting proof.

Preserves all canonical character data. Source garment visibility only changes
inside a decoded, disposable Blender scene, never in original repositories.
Requires official archive, sha256 externally verified in the workflow.
"""
import bpy, json, sys, os, math
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index("--")+1:]
gender,render_path,mhclo_path=args[:3]
if gender not in ("female","male"):raise ValueError(gender)
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/"engine_sources/makehuman-lineart/scripts"))
import mhclo_fit as F

source=Path(mhclo_path).resolve()
if not source.is_file():raise RuntimeError("DONOR_MHCLO_MISSING: "+str(source))
header="\n".join(source.read_text(errors="replace").splitlines()[:28])
if not any("license cc0" in x.lower() for x in header.splitlines()):
    raise RuntimeError("DONOR_MISSING_AUTHORITATIVE_CC0_HEADER")
scene=bpy.context.scene
body=bpy.data.objects["Host.body"]
rig=bpy.data.objects["Host.rig"]
scene.frame_set(27)
rig.data.pose_position="REST"
bpy.context.view_layer.update()
if not (body.data.shape_keys and len(body.data.shape_keys.key_blocks)==34):
    raise RuntimeError("CANONICAL_BODY_FACE_KEYS_INVALID")
W=F.shaped_coords(body)
locations,refs=F.fit(str(source),W)
_,_,obj_path=F.load_mhclo(str(source))
old_vertices,faces=F.load_obj(obj_path)
if len(locations)!=len(old_vertices):
    raise RuntimeError("MHCLO_FIT_VERTEX_TOPOLOGY_MISMATCH")
if not faces or not refs:raise RuntimeError("DONOR_GEOMETRY_EMPTY")
if max(i for ids,ws,offset in refs for i in ids)>=len(W):
    raise RuntimeError("DONOR_BODY_BASE_INDEX_INVALID")
first=bpy.data.objects["Host.mindfront_f_dress_11" if gender=="female" else "Host.elvs_male_shirt_untucked_bd1"]
basis=first.matrix_world.copy()
mesh=bpy.data.meshes.new("V1_CC0_MAKEHUMAN_"+gender+"_SUIT_MESH")
inverse=basis.inverted()
mesh.from_pydata([inverse@p for p in locations],[],faces)
mesh.update()
for poly in mesh.polygons:poly.use_smooth=True
garment=bpy.data.objects.new("NEX_V1_CC0_FORMAL_SUIT_"+gender.upper(),mesh)
scene.collection.objects.link(garment)
garment.parent=rig
garment.matrix_world=basis
bones={b.name for b in rig.data.bones if b.use_deform}
known={g.index:g.name for g in body.vertex_groups if g.name in bones}
used={i for ids,ws,offset in refs for i in ids}
weights={i:[(known[g.group],g.weight) for g in body.data.vertices[i].groups
            if g.group in known] for i in used}
acc={}
for vi,(ids,ws,offset) in enumerate(refs):
    totals={}
    for i,w in zip(ids,ws):
        for name,weight in weights[i]:
            totals[name]=totals.get(name,0.0)+w*weight
    total=sum(totals.values()) or 1
    for name,weight in totals.items():
        if weight>1e-5:acc.setdefault(name,[]).append((vi,weight/total))
for name,items in acc.items():
    g=garment.vertex_groups.new(name=name)
    for vi,weight in items:g.add([vi],weight,"REPLACE")
arm=garment.modifiers.new("Original Host rig","ARMATURE")
arm.object=rig
sub=garment.modifiers.new("Soft illustrated folds","SUBSURF")
sub.levels=1
sub.render_levels=1
colors={"female":(0.22,0.26,0.37,1),"male":(0.16,0.21,0.28,1)}
color=colors[gender]
material=bpy.data.materials.new("V1_CC0_SUITS01_MATTE_"+gender)
material.diffuse_color=color
material.use_nodes=True
nodes=material.node_tree.nodes
nodes.clear()
o=nodes.new("ShaderNodeOutputMaterial")
diff=nodes.new("ShaderNodeBsdfPrincipled")
diff.inputs["Base Color"].default_value=color
diff.inputs["Roughness"].default_value=.92
diff.inputs["Metallic"].default_value=0
material.node_tree.links.new(diff.outputs["BSDF"],o.inputs["Surface"])
mesh.materials.append(material)
# Source intact. Hide only the original wardrobe of this disposable TEST scene.
oldnames=(
    ["Host.mindfront_f_dress_11"] if gender=="female" else
    ["Host.elvs_male_shirt_untucked_bd1","Host.mindfront_male_trousers_2",
     "Host.mindfront_shoes_monk_strap_male"]
)
hidden=[]
for name in oldnames:
    target=bpy.data.objects.get(name)
    if target:
        target.hide_render=True
        hidden.append(name)
if gender=="male":
    for name in ("Host.lineart_shoe.L","Host.lineart_shoe.R"):
        target=bpy.data.objects.get(name)
        if target:target.hide_render=True;hidden.append(name)
marks=bpy.data.collections.get("V26_GARMENT_MARKS")
if marks:
    for ob in marks.objects:ob.hide_render=True
rig.data.pose_position="POSE"
scene.frame_set(27)
bpy.context.view_layer.update()
garment["donorCC0"]=True
garment["donorName"]=source.parent.name
garment["donorAuthor"]="Margaret Toigo / MRT"
garment["originalActionsPreserved"]=True
garment["approved"]=False
report={
    "gender":gender,"asset":source.parent.name,"donorCC0Header":True,
    "sourceAuthor":"MRT / Margaret Toigo",
    "inputSourceScene":bpy.data.filepath,
    "blender":bpy.app.version_string,
    "fittedVertices":len(mesh.vertices),"faces":len(mesh.polygons),
    "rig":rig.name,"boneWeightGroups":len(acc),
    "bodyShapeKeysPreserved":len(body.data.shape_keys.key_blocks),
    "hiddenOriginalWardrobeInDisposableScene":hidden,
    "sourceAssetsInRepoUnchanged":True,
    "status":"UNAPPROVED_REAL_MAKEHUMAN_SUIT_FIT_PROOF",
    "fitPipeline":"NexStudio mhclo_fit.py; original Host armature and weights",
}
out=Path(render_path).resolve()
out.parent.mkdir(parents=True,exist_ok=True)
sc=out.with_suffix(".blend")
bpy.ops.wm.save_as_mainfile(filepath=str(sc),copy=True,compress=True)
report["editableSceneFile"]=sc.name
out.with_suffix(".json").write_text(json.dumps(report,indent=2))
print("REAL_CC0_SUIT_FIT_OK",json.dumps(report),flush=True)
