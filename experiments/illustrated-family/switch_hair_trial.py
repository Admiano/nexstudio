"""Toggle original and individually licensed trial hair on a saved V1 character.

Only affects a disposable proof scene. Keeps both original/alternate meshes,
original 163-bone Host.rig, facial shape keys and actions. No geometry edits.
Usage: ... --python switch_hair_trial.py --python quick_preview.py --
          female proofs/test.png original|alternate
"""
import bpy,sys,json
from pathlib import Path
args=sys.argv[sys.argv.index("--")+1:]
gender,dest,mode=args[:3]
if gender not in ("female","male") or mode not in ("original","alternate"):
    raise RuntimeError("SWAP_REQUIRES_GENDER_AND_ORIGINAL_OR_ALTERNATE")
out=Path(dest).resolve();out.parent.mkdir(parents=True,exist_ok=True)
rig=bpy.data.objects["Host.rig"]
body=bpy.data.objects["Host.body"]
assert len(rig.data.bones)==163 and len(body.data.shape_keys.key_blocks)==34
alternates=[o for o in bpy.data.objects if o.name.startswith("NEX_V1_CC0_HAIR_") and o.type=="MESH"]
assert len(alternates)==1,(mode,[o.name for o in alternates])
trial=alternates[0]
original=bpy.data.objects.get(trial["originalHair"])
assert original is not None and original.type=="MESH",trial["originalHair"]
assert trial["approved"] is False
assert any(m.type=="ARMATURE" and m.object==rig for m in trial.modifiers)
assert any(m.type=="ARMATURE" and m.object==rig for m in original.modifiers)
assert original.data.vertices and trial.data.vertices
# Hide all source hair objects, including legacy male inactive ones, then
# make exactly one selected original or verified alternate visibly active.
for obj in bpy.data.objects:
    if obj.type=="MESH" and (obj.name.startswith("Host.hair_") or obj.name.startswith("NEX_V1_CC0_HAIR_")):
        obj.hide_render=True
        obj.hide_viewport=True
chosen=original if mode=="original" else trial
chosen.hide_render=False
chosen.hide_viewport=False
assert sum(1 for o in (original,trial) if not o.hide_render)==1
bpy.context.scene.frame_set(27)
bpy.context.view_layer.update()
report={"gender":gender,"active":chosen.name,"mode":mode,
        "retainedOriginal":original.name,"retainedTrial":trial.name,
        "originalVertices":len(original.data.vertices),
        "trialVertices":len(trial.data.vertices),
        "originalRig":rig.name,"rigBones":len(rig.data.bones),
        "bodyMorphKeys":len(body.data.shape_keys.key_blocks),
        "sceneAuthority":"isolated experimental V1 saved scene",
        "originalMotionActionsUnchanged":True,
        "status":"PASS_REVERSIBLE_HAIR_MESH_SWITCH_UNAPPROVED_VISUAL_TRIAL"}
bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix(".blend")),copy=True,compress=True)
out.with_name(out.stem+"-switch-report.json").write_text(json.dumps(report,indent=2)+"\n")
print("REAL_V1_HAIR_SWAP_CLEAN_SWITCH",json.dumps(report),flush=True)
