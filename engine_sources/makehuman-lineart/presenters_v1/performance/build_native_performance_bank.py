import bpy, json, os
from pathlib import Path

HERE=Path(__file__).resolve().parent
BANK_PATH=Path(os.environ.get("NEX_NATIVE_BANK", HERE/"native_performance_bank.json"))
OUT=Path(os.environ.get("NEX_BANK_BLEND_OUT", "/tmp/BASE_V58_NATIVE_BANK.blend"))
bank=json.load(open(BANK_PATH))
rig=bpy.data.objects["Host.rig"]
scene=bpy.context.scene
ad=rig.animation_data_create()
source=bpy.data.actions.get(bank["sourceAction"])
if source is None:
    raise RuntimeError("missing source action "+bank["sourceAction"])
ad.action=source

ARM_BASE=["clavicle","shoulder01","upperarm01","upperarm02","lowerarm01","lowerarm02","wrist"]
ARM_BONES=[f"{n}.{s}" for s in ("L","R") for n in ARM_BASE]
FINGERS=[f"finger{digit}-{seg}.{s}" for s in ("L","R") for digit in range(1,6) for seg in range(1,4)]
SUPPORT=["spine03","spine04","spine05"]
ATTENTION=["neck01","neck02","neck03","head","eye.L","eye.R"]
SCOPES={
  "gesture":ARM_BONES+FINGERS+SUPPORT,
  "attention":ATTENTION,
  "rest":ARM_BONES+FINGERS+SUPPORT+ATTENTION,
}

def capture(pb):
    if pb.rotation_mode=="QUATERNION":
        return ("rotation_quaternion", tuple(pb.rotation_quaternion))
    if pb.rotation_mode=="AXIS_ANGLE":
        return ("rotation_axis_angle", tuple(pb.rotation_axis_angle))
    return ("rotation_euler", tuple(pb.rotation_euler))

def set_value(pb,prop,value):
    v=getattr(pb,prop)
    for i,x in enumerate(value): v[i]=x

def all_fcurves(action):
    out=[]
    try: out.extend(list(action.fcurves))
    except Exception: pass
    try: slots=list(action.slots); layers=list(action.layers)
    except Exception: return out
    for layer in layers:
        for strip in layer.strips:
            for slot in slots:
                try: bag=strip.channelbag(slot,ensure=False)
                except TypeError:
                    try: bag=strip.channelbag(slot)
                    except Exception: bag=None
                except Exception: bag=None
                if bag:
                    try: out.extend(list(bag.fcurves))
                    except Exception: pass
    # unique
    seen=set(); uniq=[]
    for fc in out:
        k=(fc.data_path,fc.array_index)
        if k not in seen: seen.add(k); uniq.append(fc)
    return uniq

created=[]
for semantic,variants in bank["entries"].items():
    for spec in variants:
        bones=[n for n in SCOPES[spec["scope"]] if rig.pose.bones.get(n)]
        samples=[]
        ad.action=source
        for srcfr in range(int(spec["start"]),int(spec["end"])+1):
            scene.frame_set(srcfr)
            samples.append({n:capture(rig.pose.bones[n]) for n in bones})
        name="NEX_NATIVE_"+semantic+"__"+spec["id"]
        old=bpy.data.actions.get(name)
        if old:
            bpy.data.actions.remove(old)
        ad.action=None
        # Let Blender 5 create the correct layered Action/slot on first key.
        new_action=None
        for i,sample in enumerate(samples,1):
            for n,(prop,value) in sample.items():
                pb=rig.pose.bones[n]
                set_value(pb,prop,value)
                pb.keyframe_insert(data_path=prop,frame=i,group=n)
            if new_action is None and ad.action:
                new_action=ad.action
                new_action.name=name
        if new_action is None:
            raise RuntimeError("failed to create native action "+name)
        for fc in all_fcurves(new_action):
            for kp in fc.keyframe_points:
                kp.interpolation="LINEAR"
        new_action["NEX_SEMANTIC"]=semantic
        new_action["NEX_VARIANT_ID"]=spec["id"]
        new_action["NEX_SOURCE_ACTION"]=source.name
        new_action["NEX_SOURCE_START"]=int(spec["start"])
        new_action["NEX_SOURCE_PEAK"]=int(spec["peak"])
        new_action["NEX_SOURCE_END"]=int(spec["end"])
        new_action["NEX_SCOPE"]=spec["scope"]
        new_action["NEX_DOMINANT_HAND"]=spec["dominantHand"]
        spec["action"]=name
        spec["frames"]=len(samples)
        created.append({"semantic":semantic,"id":spec["id"],"action":name,"frames":len(samples),"bones":len(bones)})

ad.action=source
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
manifest=OUT.with_suffix(".json")
manifest.write_text(json.dumps({"schema":bank["schema"],"created":created,"bank":bank},indent=2))
print("NATIVE_BANK_BUILT",json.dumps({"actions":len(created),"out":str(OUT),"manifest":str(manifest)}))
