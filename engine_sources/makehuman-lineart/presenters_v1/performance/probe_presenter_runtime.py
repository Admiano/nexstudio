import bpy, json, os, re
from pathlib import Path

OUT = Path(os.environ.get("PROBE_OUT", "/tmp/presenter-performance-probe.json"))

def safe(v):
    try:
        json.dumps(v); return v
    except Exception:
        return str(v)

def action_info(a):
    info={"name":a.name,"frame_range":[float(a.frame_range[0]),float(a.frame_range[1])],"fcurves":[]}
    try:
        curves=list(a.fcurves)
    except Exception:
        curves=[]
    for fc in curves:
        pts=[]
        for kp in list(fc.keyframe_points)[:8]:
            pts.append([float(kp.co.x),float(kp.co.y)])
        info["fcurves"].append({
            "data_path":fc.data_path,
            "array_index":int(fc.array_index),
            "keys":len(fc.keyframe_points),
            "sample":pts,
        })
    return info

armatures=[]
for obj in bpy.data.objects:
    if obj.type!="ARMATURE":
        continue
    pose=[]
    for pb in obj.pose.bones:
        pose.append({
            "name":pb.name,
            "parent":pb.parent.name if pb.parent else None,
            "rotation_mode":pb.rotation_mode,
            "constraints":[{"name":c.name,"type":c.type,"influence":float(c.influence)} for c in pb.constraints],
            "custom_properties":sorted([k for k in pb.keys() if k!="_RNA_UI"]),
        })
    armatures.append({
        "object":obj.name,
        "data":obj.data.name,
        "bone_count":len(obj.data.bones),
        "active_action":obj.animation_data.action.name if obj.animation_data and obj.animation_data.action else None,
        "nla_tracks":[{
            "name":t.name,
            "mute":bool(t.mute),
            "strips":[{"name":s.name,"action":s.action.name if s.action else None,
                       "frame_start":float(s.frame_start),"frame_end":float(s.frame_end),
                       "influence":float(s.influence),"blend_type":s.blend_type}
                      for s in t.strips]
        } for t in (obj.animation_data.nla_tracks if obj.animation_data else [])],
        "pose_bones":pose,
    })

shape_keys=[]
for key in bpy.data.shape_keys:
    ad=key.animation_data
    drivers=[]
    if ad:
        for fc in ad.drivers:
            drv=fc.driver
            drivers.append({
                "data_path":fc.data_path,
                "array_index":int(fc.array_index),
                "expression":drv.expression,
                "variables":[{
                    "name":v.name,
                    "type":v.type,
                    "targets":[{
                        "id":getattr(t.id,"name",None) if t.id else None,
                        "data_path":t.data_path,
                        "bone_target":getattr(t,"bone_target","")
                    } for t in v.targets]
                } for v in drv.variables]
            })
    shape_keys.append({
        "name":key.name,
        "blocks":[b.name for b in key.key_blocks],
        "active_action":ad.action.name if ad and ad.action else None,
        "drivers":drivers,
    })

object_drivers=[]
for obj in bpy.data.objects:
    ad=obj.animation_data
    if not ad: continue
    for fc in ad.drivers:
        object_drivers.append({
            "object":obj.name,
            "data_path":fc.data_path,
            "array_index":int(fc.array_index),
            "expression":fc.driver.expression,
        })

materials=[]
for mat in bpy.data.materials:
    nt=mat.node_tree
    if not nt or not nt.animation_data: continue
    ad=nt.animation_data
    mats={"material":mat.name,"action":ad.action.name if ad.action else None,"drivers":[]}
    for fc in ad.drivers:
        mats["drivers"].append({"data_path":fc.data_path,"array_index":int(fc.array_index),"expression":fc.driver.expression})
    if mats["action"] or mats["drivers"]: materials.append(mats)

actions=[action_info(a) for a in bpy.data.actions]

# Summaries aimed at the presenter adapter.
keywords=re.compile(r"(arm|forearm|hand|wrist|finger|thumb|index|middle|ring|pinky|clav|shoulder|neck|head|eye|brow|jaw|mouth|lip|spine|chest|pelvis)",re.I)
relevant_bones=sorted({
    pb["name"] for arm in armatures for pb in arm["pose_bones"] if keywords.search(pb["name"])
})
relevant_paths=[]
for a in actions:
    for fc in a["fcurves"]:
        if keywords.search(fc["data_path"]):
            relevant_paths.append({"action":a["name"],**fc})

scene=bpy.context.scene
result={
    "blender":bpy.app.version_string,
    "blend":bpy.data.filepath,
    "scene":{
        "frame_start":scene.frame_start,
        "frame_end":scene.frame_end,
        "fps":scene.render.fps,
        "current_frame":scene.frame_current,
    },
    "armatures":armatures,
    "actions":actions,
    "shape_keys":shape_keys,
    "object_drivers":object_drivers,
    "material_animation":materials,
    "relevant_bones":relevant_bones,
    "relevant_action_channels":relevant_paths,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2))
print("PRESENTER_PERFORMANCE_PROBE",json.dumps({
    "armatures":[{"object":a["object"],"bones":a["bone_count"],"active_action":a["active_action"],"nla":len(a["nla_tracks"])} for a in armatures],
    "actions":len(actions),
    "shape_keys":len(shape_keys),
    "relevant_bones":len(relevant_bones),
    "relevant_action_channels":len(relevant_paths),
    "out":str(OUT),
}))
