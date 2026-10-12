"""NexStudio V1 opt-in illustration material pass on an isolated CC0 formal suit."""
import bpy, json, sys
from pathlib import Path

args=sys.argv[sys.argv.index("--")+1:]
gender,render_path=args[:2]
suit=bpy.data.objects.get("NEX_V1_CC0_FORMAL_SUIT_"+gender.upper())
rig=bpy.data.objects.get("Host.rig")
if not suit or not rig:raise RuntimeError("FIT_SUITE_OR_ORIGINAL_RIG_MISSING")
assert suit.get("approved") is False
mat=suit.active_material
assert mat and mat.use_nodes
nodes=mat.node_tree.nodes
links=mat.node_tree.links
tex=next((n for n in nodes if n.type=="TEX_IMAGE"),None)
em=next((n for n in nodes if n.type=="EMISSION"),None)
if tex is None or em is None:raise RuntimeError("UV_TEXTURED_DONOR_MATERIAL_MISSING")
# Tone down visually noisy photograph-based textures without painting over
# original tie and lapel UV atlas details or changing geometry/armatures.
for link in list(em.inputs["Color"].links):links.remove(link)
hsv=nodes.new("ShaderNodeHueSaturation")
hsv.name="Nex V1 restrained hand-painted fabric grade"
hsv.inputs["Hue"].default_value=.5
hsv.inputs["Saturation"].default_value=.70 if gender=="female" else .54
hsv.inputs["Value"].default_value=1.0
links.new(tex.outputs["Color"],hsv.inputs["Color"])
links.new(hsv.outputs["Color"],em.inputs["Color"])
# Original illustrated Ink/Freestyle collections are the authoritative style,
# not newly generated image overlays. Enroll only the disposable donor mesh.
registered=[]
for group_name in ("GARMENT_SILHOUETTE","PEEPS_CONTOUR_SOURCES"):
    collection=bpy.data.collections.get(group_name)
    if collection is not None and suit.name not in collection.objects:
        collection.objects.link(suit)
        registered.append(group_name)
bpy.context.view_layer.update()
suit["trialV1IllustratedFinish"]=True
report={
 "gender":gender,
 "asset":suit["donorName"],
 "fabricGrade":"UV_original_texture_desaturated",
 "saturation":hsv.inputs["Saturation"].default_value,
 "freestyleCollections":registered,
 "originalV1Rig":rig.name,
 "canonicalSourceUnchanged":True,
 "status":"UNAPPROVED_ILLUSTRATED_FINISH_SIDE_BY_SIDE_QA",
}
out=Path(render_path).resolve()
out.with_suffix(".blend").parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix(".blend")),copy=True,compress=True)
out.with_name(out.stem+"-illustrated-grade.json").write_text(json.dumps(report,indent=2))
print("CC0_ILLUSTRATED_FINISH_APPLIED",json.dumps(report),flush=True)
