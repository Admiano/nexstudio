import bpy, json, math, os
from pathlib import Path
from mathutils import Quaternion

OUT=Path(os.environ.get("SCAN_OUT","/tmp/native-gesture-scan"))
OUT.mkdir(parents=True,exist_ok=True)
WORDS=Path(os.environ.get("WORDS_JSON",""))
words=json.load(open(WORDS)) if WORDS.exists() else []

scene=bpy.context.scene
rig=bpy.data.objects["Host.rig"]
bones=[
 "clavicle.L","upperarm01.L","lowerarm01.L","wrist.L",
 "clavicle.R","upperarm01.R","lowerarm01.R","wrist.R",
]
headbones=["neck01","head","eye.L","eye.R"]

def q(pb):
    return pb.matrix_basis.to_quaternion().normalized()

# Use a quiet reference frame already observed in the frozen native take.
scene.frame_set(500)
ref={n:q(rig.pose.bones[n]).copy() for n in bones+headbones}

records=[]
prev=None
for fr in range(scene.frame_start,scene.frame_end+1):
    scene.frame_set(fr)
    arm_angles={n:ref[n].rotation_difference(q(rig.pose.bones[n])).angle for n in bones}
    head_angles={n:ref[n].rotation_difference(q(rig.pose.bones[n])).angle for n in headbones}
    # Upper/lower arm motion dominates; clavicle/wrist are bounded support.
    energy=sum(arm_angles[n]*(1.0 if "upperarm" in n or "lowerarm" in n else .45) for n in bones)
    left=sum(arm_angles[n] for n in bones if n.endswith(".L"))
    right=sum(arm_angles[n] for n in bones if n.endswith(".R"))
    attention=sum(head_angles.values())
    velocity=0.0
    if prev:
        velocity=sum(prev[n].rotation_difference(q(rig.pose.bones[n])).angle for n in bones)
    prev={n:q(rig.pose.bones[n]).copy() for n in bones}
    t=(fr-1)/scene.render.fps
    phrase=" ".join(w[2] for w in words if w[0] <= t+0.8 and w[1] >= t-0.8)
    records.append({
      "frame":fr,"time":t,"energy":energy,"velocity":velocity,
      "left":left,"right":right,"asymmetry":abs(left-right),
      "attention":attention,"phrase":phrase
    })

# Smooth energy over ~0.2s and pick well-separated local maxima.
vals=[r["energy"] for r in records]
smooth=[]
for i in range(len(vals)):
    lo=max(0,i-2); hi=min(len(vals),i+3)
    smooth.append(sum(vals[lo:hi])/(hi-lo))
for r,v in zip(records,smooth): r["smooth_energy"]=v
candidates=[]
for i in range(2,len(records)-2):
    v=smooth[i]
    if v>=smooth[i-1] and v>=smooth[i+1] and v>=smooth[i-2] and v>=smooth[i+2]:
        candidates.append(records[i])
candidates.sort(key=lambda r:r["smooth_energy"],reverse=True)
picked=[]
for c in candidates:
    if all(abs(c["frame"]-p["frame"])>=48 for p in picked):
        picked.append(c)
    if len(picked)>=14: break
picked.sort(key=lambda r:r["frame"])

# Also identify quiet native-rest candidates.
quiet=sorted(records,key=lambda r:(r["energy"]+r["velocity"]*1.5))[:30]
quiet_picked=[]
for c in quiet:
    if all(abs(c["frame"]-p["frame"])>=60 for p in quiet_picked):
        quiet_picked.append(c)
    if len(quiet_picked)>=5: break
quiet_picked.sort(key=lambda r:r["frame"])

json.dump({"reference_frame":500,"peaks":picked,"quiet":quiet_picked},open(OUT/"native_gesture_candidates.json","w"),indent=2)

# Render native pose peaks for human visual certification.
scene.render.resolution_x=360
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
if scene.render.engine=="BLENDER_EEVEE_NEXT":
    pass
else:
    try:
        scene.render.engine="BLENDER_EEVEE_NEXT"
    except Exception:
        try:
            scene.cycles.samples=4
        except Exception: pass
for c in picked:
    scene.frame_set(c["frame"])
    scene.render.filepath=str(OUT/f'frame_{c["frame"]:04d}.png')
    bpy.ops.render.render(write_still=True)
    print("GESTURE_CANDIDATE",c["frame"],round(c["time"],2),round(c["smooth_energy"],4),c["phrase"])
print("NATIVE_GESTURE_SCAN_DONE",len(picked),len(quiet_picked),OUT)
