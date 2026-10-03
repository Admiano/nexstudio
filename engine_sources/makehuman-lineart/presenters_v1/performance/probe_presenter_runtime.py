import bpy, json, os, re
from pathlib import Path

OUT = Path(os.environ.get("PROBE_OUT", "/tmp/presenter-performance-probe.json"))
KEYWORDS=re.compile(r"(arm|forearm|hand|wrist|finger|thumb|index|middle|ring|pinky|clav|shoulder|neck|head|eye|brow|jaw|mouth|lip|spine|chest|pelvis)",re.I)

def fcurve_info(fc):
    pts=[]
    for kp in list(fc.keyframe_points)[:12]:
        pts.append([float(kp.co.x),float(kp.co.y)])
    return {
        "data_path":fc.data_path,
        "array_index":int(fc.array_index),
        "keys":len(fc.keyframe_points),
        "sample":pts,
    }

def action_fcurves(a):
    out=[]
    # Legacy API when present.
    try:
        for fc in a.fcurves:
            out.append({"slot":None,"layer":None,"strip":None,**fcurve_info(fc)})
    except Exception:
        pass
    # Blender 4.4+/5.x layered Action API.
    try:
        slots=list(a.slots)
    except Exception:
        slots=[]
    try:
        layers=list(a.layers)
    except Exception:
        layers=[]
    for li,layer in enumerate(layers):
        try: strips=list(layer.strips)
        except Exception: strips=[]
        for si,strip in enumerate(strips):
            for slot in slots:
                bag=None
                try:
                    bag=strip.channelbag(slot, ensure=False)
                except TypeError:
                    try: bag=strip.channelbag(slot)
                    except Exception: pass
                except Exception:
                    pass
                if bag is None:
                    # Some builds expose channelbags directly.
                    try:
                        for cb in strip.channelbags:
                            if getattr(cb,"slot_handle",None)==getattr(slot,"handle",None):
                                bag=cb; break
                    except Exception:
                        pass
                if bag is None: continue
                try: curves=list(bag.fcurves)
                except Exception: curves=[]
                for fc in curves:
                    out.append({
                        "slot":getattr(slot,"identifier",None) or getattr(slot,"name_display",None) or str(getattr(slot,"handle","")),
                        "slot_target_id_type":getattr(slot,"target_id_type",None),
                        "layer":getattr(layer,"name",str(li)),
                        "strip":getattr(strip,"type",str(si)),
                        **fcurve_info(fc)
                    })
    # De-duplicate if an Action is visible through both APIs.
    seen=set(); uniq=[]
    for x in out:
        k=(x["slot"],x["data_path"],x["array_index"])
        if k not in seen:
            seen.add(k); uniq.append(x)
    return uniq

def action_info(a):
    fc=action_fcurves(a)
    slots=[]
    try:
        for s in a.slots:
            slots.append({
                "identifier":getattr(s,"identifier",None),
                "name_display":getattr(s,"name_display",None),
                "target_id_type":getattr(s,"target_id_type",None),
                "handle":getattr(s,"handle",None),
            })
    except Exception: pass
    return {
        "name":a.name,
        "frame_range":[float(a.frame_range[0]),float(a.frame_range[1])],
        "slots":slots,
        "fcurves":fc,
    }

armatures=[]
for obj in bpy.data.objects:
    if obj.type!="ARMATURE": continue
    ad=obj.animation_data
    pose=[]
    for pb in obj.pose.bones:
        pose.append({
            "name":pb.name,
            "parent":pb.parent.name if pb.parent else None,
            "rotation_mode":pb.rotation_mode,
            "constraints":[{"name":c.name,"type":c.type,"influence":float(c.influence)} for c in pb.constraints],
            "custom_properties":sorted([k for k in pb.keys() if k!="_RNA_UI"]),
            "bone_matrix_local":[list(row) for row in pb.bone.matrix_local],
        })
    armatures.append({
        "object":obj.name,
        "data":obj.data.name,
        "bone_count":len(obj.data.bones),
        "active_action":ad.action.name if ad and ad.action else None,
        "action_slot":getattr(getattr(ad,"action_slot",None),"identifier",None) if ad else None,
        "nla_tracks":[{
            "name":t.name,"mute":bool(t.mute),
            "strips":[{"name":s.name,"action":s.action.name if s.action else None,
                       "frame_start":float(s.frame_start),"frame_end":float(s.frame_end),
                       "influence":float(s.influence),"blend_type":s.blend_type}
                      for s in t.strips]
        } for t in (ad.nla_tracks if ad else [])],
        "pose_bones":pose,
    })

shape_keys=[]
for key in bpy.data.shape_keys:
    ad=key.animation_data
    shape_keys.append({
        "name":key.name,
        "blocks":[b.name for b in key.key_blocks],
        "active_action":ad.action.name if ad and ad.action else None,
        "action_slot":getattr(getattr(ad,"action_slot",None),"identifier",None) if ad else None,
        "drivers":[{
            "data_path":fc.data_path,"array_index":int(fc.array_index),"expression":fc.driver.expression
        } for fc in (ad.drivers if ad else [])],
    })

actions=[action_info(a) for a in bpy.data.actions]
relevant_bones=sorted({pb["name"] for arm in armatures for pb in arm["pose_bones"] if KEYWORDS.search(pb["name"])})
relevant_channels=[{"action":a["name"],**fc} for a in actions for fc in a["fcurves"] if KEYWORDS.search(fc["data_path"])]

# Sample the active Host body action at useful frames to quantify native motion.
host=bpy.data.objects.get("Host.rig")
sample_frames=[1,27,56,101,184,220,338,500,700,891,998]
sample_bones=["clavicle.L","clavicle.R","upperarm01.L","upperarm01.R","lowerarm01.L","lowerarm01.R","wrist.L","wrist.R","neck01","neck02","neck03","head","eye.L","eye.R"]
samples=[]
if host:
    for fr in sample_frames:
        bpy.context.scene.frame_set(fr)
        frame={"frame":fr,"bones":{}}
        for n in sample_bones:
            pb=host.pose.bones.get(n)
            if not pb: continue
            q=pb.matrix_basis.to_quaternion()
            frame["bones"][n]={
                "rotation_quaternion":[float(q.w),float(q.x),float(q.y),float(q.z)],
                "location":[float(x) for x in pb.location],
            }
        samples.append(frame)

scene=bpy.context.scene
result={
    "blender":bpy.app.version_string,
    "blend":bpy.data.filepath,
    "scene":{"frame_start":scene.frame_start,"frame_end":scene.frame_end,"fps":scene.render.fps},
    "armatures":armatures,
    "actions":actions,
    "shape_keys":shape_keys,
    "relevant_bones":relevant_bones,
    "relevant_action_channels":relevant_channels,
    "native_samples":samples,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2))
print("PRESENTER_PERFORMANCE_PROBE",json.dumps({
    "armatures":[{"object":a["object"],"bones":a["bone_count"],"active_action":a["active_action"],"slot":a["action_slot"]} for a in armatures],
    "actions":[{"name":a["name"],"slots":len(a["slots"]),"curves":len(a["fcurves"])} for a in actions],
    "shape_keys":len(shape_keys),
    "relevant_bones":len(relevant_bones),
    "relevant_action_channels":len(relevant_channels),
    "out":str(OUT),
}))
