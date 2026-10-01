import bpy, json, math, os, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
BANK_PATH=Path(os.environ.get("NEX_NATIVE_BANK", HERE/"native_performance_bank.json"))
PLAN_PATH=Path(os.environ["NEX_PERFORMANCE_PLAN"])
OUT=Path(os.environ.get("NEX_PERFORMANCE_OUT","/tmp/NEX_PRESENTER_PERFORMANCE.blend"))
bank=json.load(open(BANK_PATH))
plan=json.load(open(PLAN_PATH))

FORBIDDEN=re.compile(r"(pose3d|skeleton|joint(?:write|writes|coordinate|coordinates)?|shoulder.*coord|elbow.*coord|wrist.*coord|finger.*coord|rawsvg|svggeometry)",re.I)
def walk(x,path="root"):
    if isinstance(x,dict):
        for k,v in x.items():
            if FORBIDDEN.search(k): raise ValueError(f"{path}.{k}: raw physical control is forbidden")
            walk(v,f"{path}.{k}")
    elif isinstance(x,list):
        for i,v in enumerate(x): walk(v,f"{path}[{i}]")
walk(plan)
if plan.get("schemaVersion")!="1.0.0": raise ValueError("schemaVersion must be 1.0.0")
if not plan.get("performanceBeats"): raise ValueError("performanceBeats required")
if not (float(plan.get("duration",0))>0): raise ValueError("duration must be >0")

rig=bpy.data.objects["Host.rig"]
scene=bpy.context.scene
fps=scene.render.fps
ad=rig.animation_data_create()
source=bpy.data.actions.get(bank["sourceAction"])
if source is None: raise RuntimeError("source action missing")

# Resolve generated same-rig actions by the custom metadata written by builder.
actions={}
for a in bpy.data.actions:
    sem=a.get("NEX_SEMANTIC")
    vid=a.get("NEX_VARIANT_ID")
    if sem and vid: actions[(str(sem),str(vid))]=a
if not actions: raise RuntimeError("native semantic bank has not been built")

for t in list(ad.nla_tracks):
    if t.name.startswith("NEX_PERF_"): ad.nla_tracks.remove(t)
ad.action=None

duration=float(plan["duration"])
scene.frame_start=1
scene.frame_end=max(2,int(round(duration*fps))+1)

rest_spec=bank["entries"]["REST"][0]
rest_action=actions[("REST",rest_spec["id"])]
rest_track=ad.nla_tracks.new(); rest_track.name="NEX_PERF_REST"
rest_len=max(1,float(rest_action.frame_range[1]-rest_action.frame_range[0]+1))
cursor=scene.frame_start
idx=0
while cursor<=scene.frame_end:
    strip=rest_track.strips.new(f"REST_{idx:03d}",int(cursor),rest_action)
    strip.action_frame_start=float(rest_action.frame_range[0])
    strip.action_frame_end=float(rest_action.frame_range[1])
    strip.extrapolation="NOTHING"
    cursor=int(math.floor(strip.frame_end))+1
    idx+=1

gesture_track=ad.nla_tracks.new(); gesture_track.name="NEX_PERF_GESTURES"
attention_track=ad.nla_tracks.new(); attention_track.name="NEX_PERF_ATTENTION"
cooldown={}
placed=[]

def semantic_for(beat):
    g=beat.get("gesture") or {}
    raw=(g.get("gestureClass") or beat.get("semanticIntent") or "").strip().lower()
    for key,target in bank.get("fallbacks",{}).items():
        if key in raw: return target
    if "agree" in raw: return "AGREE_NOD"
    if "listen" in raw: return "LISTEN_ATTENTIVE"
    if "look" in raw or "think" in raw: return "LOOK_SIDE"
    return None

def choose_variant(semantic,dominant):
    variants=bank["entries"][semantic]
    matches=[v for v in variants if dominant in (None,"none") or v["dominantHand"] in (dominant,"both","none")]
    pool=matches or variants
    n=cooldown.get(semantic,0)
    v=pool[n%len(pool)]
    cooldown[semantic]=n+1
    return v

def add_strip(track,semantic,spec,startf,endf,label):
    action=actions[(semantic,spec["id"])]
    startf=max(scene.frame_start,int(round(startf)))
    endf=min(scene.frame_end,int(round(endf)))
    if endf<=startf+1: return
    strip=track.strips.new(label,startf,action)
    src_len=max(1.0,float(action.frame_range[1]-action.frame_range[0]+1))
    target_len=max(2.0,float(endf-startf+1))
    strip.action_frame_start=float(action.frame_range[0])
    strip.action_frame_end=float(action.frame_range[1])
    strip.scale=target_len/src_len
    strip.extrapolation="NOTHING"
    strip.blend_type="REPLACE"
    strip.use_auto_blend=False
    strip.blend_in=min(4.0,target_len*.12)
    strip.blend_out=min(5.0,target_len*.15)
    placed.append({"track":track.name,"semantic":semantic,"variant":spec["id"],"frameStart":startf,"frameEnd":endf,"action":action.name})

last_end=-1
for i,beat in enumerate(plan["performanceBeats"]):
    bs=float(beat["startTime"]); be=float(beat["endTime"])
    if bs<0 or be<=bs or be>duration+1e-6 or bs<last_end-1e-6:
        raise ValueError(f"beat[{i}] invalid/overlapping range")
    last_end=be
    g=beat.get("gesture") or {"suppress":True}
    semantic=semantic_for(beat)

    # Attention is independent from the arm gesture and may remain active on
    # suppressed/still beats.
    intent=(beat.get("semanticIntent") or "").lower()
    gaze=(beat.get("gaze") or {}).get("targetType","")
    att=None
    if "agree" in intent: att="AGREE_NOD"
    elif "listen" in intent: att="LISTEN_ATTENTIVE"
    elif "look" in intent or "think" in intent or gaze=="away": att="LOOK_SIDE"
    if att:
        spec=choose_variant(att,"none")
        add_strip(attention_track,att,spec,bs*fps+1,be*fps+1,f"A{i:02d}_{att}")

    if g.get("suppress",False): continue
    if semantic in ("AGREE_NOD","LISTEN_ATTENTIVE","LOOK_SIDE",None): continue
    spec=choose_variant(semantic,g.get("dominantHand"))
    stroke=g.get("strokeTime")
    if stroke is not None:
        start=(float(stroke)-float(g.get("preparation",0)))*fps+1
        end=(float(stroke)+float(g.get("hold",0))+float(g.get("recovery",0)))*fps+1
    else:
        start=bs*fps+1; end=be*fps+1
    add_strip(gesture_track,semantic,spec,start,end,f"G{i:02d}_{semantic}")

scene["NEX_PERFORMANCE_PLAN_SCHEMA"]="1.0.0"
scene["NEX_PERFORMANCE_ADAPTER"]="MAKEHUMAN_NATIVE_V1"
scene["NEX_PERFORMANCE_PLACED"]=len(placed)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
report=OUT.with_suffix(".json")
report.write_text(json.dumps({"status":"PASS","duration":duration,"fps":fps,"placed":placed},indent=2))
print("PERFORMANCE_PLAN_APPLIED",json.dumps({"placed":len(placed),"out":str(OUT),"report":str(report)}))
