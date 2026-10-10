"""Genuine LINEART_HAIR_PAPER palette swap trial on licensed V1 hair meshes.

Makes a dedicated material copy for the selected real hair without recoloring
the canonical hidden original. No mesh or original animation edits.
"""
import bpy,sys,json,math
from pathlib import Path
args=sys.argv[sys.argv.index("--")+1:]
gender,outfile=args[:2]
# Standalone swatch trials pass a color as argument 3; the combined character
# builder passes [gender, output, certified_source_mhclo, color] instead.
hexcode=args[3] if len(args)>=4 else args[2]
assert gender in ("female","male")
assert len(hexcode)==7 and hexcode.startswith("#") and all(ch in "0123456789abcdefABCDEF" for ch in hexcode[1:])
hair=[x for x in bpy.data.objects if x.type=="MESH" and x.name.startswith("NEX_V1_CC0_HAIR_") and not x.hide_render]
if len(hair)!=1:raise RuntimeError("ONE_SELECTED_LICENSED_HAIR_REQUIRED")
hair=hair[0]
original=bpy.data.objects[hair["originalHair"]]
assert original.hide_render
rig=bpy.data.objects["Host.rig"];body=bpy.data.objects["Host.body"]
assert len(rig.data.bones)==163 and len(body.data.shape_keys.key_blocks)==34
base=hair.data.materials[0]
assert base and base.node_tree and "Mix" in base.node_tree.nodes and "Mix.001" in base.node_tree.nodes
mat=base.copy()
mat.name="NEX_V1_CC0_ALTERNATE_HAIR_COLOR_"+hexcode[1:].upper()
hair.data.materials[0]=mat
def linear(x):
    v=int(x,16)/255
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
B=[linear(hexcode[i:i+2]) for i in (1,3,5)]
E=[c*.68 for c in B]
S=[min(c*2.2,c+(1-c)*.45)+.03 for c in B]
n=mat.node_tree.nodes
m0=[x for x in n["Mix"].inputs if x.enabled]
m1=[x for x in n["Mix.001"].inputs if x.enabled]
assert len(m0)>=3 and len(m1)>=3
m0[1].default_value=(*B,1)
m0[2].default_value=(*E,1)
m1[2].default_value=(*S,1)
mat.diffuse_color=(*B,1)
assert original.data.materials[0]!=mat
out=Path(outfile).resolve();out.parent.mkdir(parents=True,exist_ok=True)
report={"gender":gender,"fittedHair":hair.name,"originalStillExists":original.name,
        "alternateMaterial":mat.name,"originalMaterial":original.data.materials[0].name,
        "colorHex":hexcode,"sourceRigPreserved":True,"boneCount":len(rig.data.bones),
        "faceKeys":len(body.data.shape_keys.key_blocks),
        "sourceMaterialCopiedNotEdited":True,
        "productionStatus":"EXPERIMENTAL_COLOR_PALETTE_ONLY_VISUAL_QA_REQUIRED"}
bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix(".blend")),copy=True,compress=True)
out.with_name(out.stem+"-color-report.json").write_text(json.dumps(report,indent=2)+"\n")
print("REAL_ORIGINAL_RIG_HAIR_COLOR_SWATCH",json.dumps(report),flush=True)
