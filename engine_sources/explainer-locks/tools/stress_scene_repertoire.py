#!/usr/bin/env python3
"""Native SceneBam scene-richness proof, voiced by registered Microsoft Andrew.

Exercises multiple semantic scene families in actual films, never a fake UI or
manually drawn screenshot. The production treatment builder and original
compiler/renderer decide every scene. Report includes scene diversity and
source/authoring quality; no automatic claim of commercial readiness.
"""
import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import stress_bayes_andrew as voice_driver
from make_reel import build_treatment,style_of

SCRIPTS={
    "dataviz": (
        "First sort the packages, then scan the labels, finally load the trucks. "
        "In 2020 the depot opened and in 2022 the depot expanded and in 2024 the fleet doubled. "
        "The depot recorded 40 cars, 25 vans, and 30 buses. "
        "The report breakdown included 30 trucks, 20 vans, and 15 cars. "
        "The installation project is now 72 percent complete. "
        "Electric vans versus diesel trucks. "
        "Look closely at the charging port."
    ),
    "sketch": (
        "A courier carefully sends a sealed parcel to a driver at the main dispatch station. "
        "The driver carries that same parcel to a waiting customer before the next delivery begins. "
        "A technician then connects the pump to the water tank so the pressure can stabilize. "
        "Never use the damaged receipt because it is not a valid record of that delivery. "
        "Circle the safety document so the team can identify the approved inspection record. "
        "Look closely at the warning label to confirm the instruction written on the equipment. "
        "First inspect the machine carefully, then replace the worn seal, finally test the pump under normal pressure. "
        "The courier walks toward the driver as the next shipment arrives at the loading station. "
        "The courier walks then waves to the driver before greeting the waiting customer. "
        "The driver turns toward the loading platform and points at the delivery document. "
        "A crowd gathers outside the depot to watch the restored delivery system start operating again."
    ),
}
ASPECTS=("1x1",)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--style",choices=("dataviz","sketch"),required=True)
    ap.add_argument("--fps",type=int,default=24)
    ap.add_argument("--workers",type=int,default=2)
    args=ap.parse_args()

    film_id="scenebam-repertoire-"+args.style
    text=SCRIPTS[args.style]
    voice_driver.SCRIPT=text   # use the exact same, verified voice synth + aligner
    assert voice_driver.VOICE=="en-US-AndrewMultilingualNeural"
    fixture=ROOT/"fixtures"/film_id
    out=ROOT/"out"/"repertoire-stress"/film_id
    fixture.mkdir(parents=True,exist_ok=True)
    out.mkdir(parents=True,exist_ok=True)
    audio=fixture/"voice.mp3"
    # Microsoft Edge TTS occasionally returns an empty transport response.
    # Retry the SAME approved neural voice; never substitute another speaker.
    boundaries=None
    for attempt in range(1,5):
        try:
            boundaries=asyncio.run(voice_driver.microsoft_andrew(audio))
            break
        except Exception as exc:
            if attempt==4:
                raise RuntimeError("APPROVED_ANDREW_AUDIO_UNAVAILABLE") from exc
            print("ANDREW_NETWORK_RETRY",attempt,str(exc),flush=True)
            time.sleep(2*attempt)
    assert boundaries is not None
    info=voice_driver.probe(audio)
    duration_ms=round(float(info["format"]["duration"])*1000)
    if duration_ms < 17000: raise RuntimeError("REPERTOIRE_AUDIO_TOO_SHORT")
    words,alignment_source=voice_driver.align_script_tokens(boundaries,duration_ms)
    (fixture/"alignment.json").write_text(json.dumps({
        "words":words,"provenance":alignment_source,
        "voice_id":"andrew","voice_name":voice_driver.VOICE},indent=2))
    treatment=build_treatment(SimpleNamespace(aspects=",".join(ASPECTS)),
                              style_of(args.style),words,[],film_id)
    treatment["fps"]=args.fps
    (fixture/"treatment.json").write_text(json.dumps(treatment,indent=2))
    director=treatment["director_report"]
    choices=Counter(s["family"] for s in director["scenes"])
    print("DIVERSE_SCENE_SELECTION",dict(choices),flush=True)
    if args.style=="sketch":
        actor_events=[event for scene in director["scenes"]
                      for event in scene.get("actor_actions",[])]
        observed={(event["actor"],event["state"]) for event in actor_events}
        required={("courier","WALK"),("courier","WAVE"),
                  ("driver","TURN"),("driver","POINT"),
                  ("technician","CONNECT")}
        if not required.issubset(observed):
            raise RuntimeError("SKETCH_NATIVE_ACTOR_STATES_NOT_DIRECTED: "+repr(actor_events))
        for beat in treatment["beats"]:
            for op in (beat.get("illustration") or {}).get("program",[]):
                if op.get("params",{}).get("actor_action"):
                    assert op["at"].get("word") in beat["narration"].split()
                    assert op["params"]["voice_sync"]
    # A single generated card repeated N times would fail this evidence gate.
    if len(choices) < 3:
        raise RuntimeError("DIVERSITY_GATE_INSUFFICIENT_SCENE_FAMILIES")

    compiler=subprocess.run([sys.executable,"-m","editorial_plan_compiler",
                             str(fixture/"treatment.json"),str(out)],
                             cwd=ROOT/"compiler",check=False)
    if compiler.returncode not in (0,3):
        raise RuntimeError(f"NATIVE_COMPILER_EXIT_{compiler.returncode}")
    gate=json.loads((out/"gate_report.json").read_text())
    recordings={}
    for aspect in ASPECTS:
        plan=out/("plan_"+aspect+".json")
        if not plan.exists(): raise RuntimeError("COMPILER_PLAN_MISSING")
        compiled=json.loads(plan.read_text())
        assert compiled["director_style"]==args.style
        actual_source=" ".join(b["narration"] for b in compiled["beats"])
        assert actual_source==text
        if args.style=="dataviz":
            assert compiled["captions_policy"]=="kinetic" and compiled["captions"]==[]
        actor_snapshots = []
        if args.style=="sketch":
            # Render must use the same spoken-clock cues from the accepted
            # compilation. Audit repeated verbs, actor identity, no overlaps,
            # no anticipatory animation, and the actual voice-word offset.
            checked_states=set()
            for b in compiled["beats"]:
                words=b["words"]
                illustrated=b.get("illustration") or {}
                persons={ent["id"]: ent.get("params", {}).get("actor_identity")
                         for ent in illustrated.get("entities", [])
                         if ent.get("params", {}).get("visual_class")=="person"}
                by_actor={}
                for op in illustrated.get("ops", []):
                    prm=op.get("params") or {}
                    if not prm.get("actor_action"):
                        continue
                    identity=persons.get(op["target"])
                    if not identity or not prm.get("voice_sync"):
                        raise RuntimeError("ACTOR_CUE_NOT_SOURCE_BOUND")
                    idx=prm.get("word_index")
                    if not isinstance(idx,int) or idx<0 or idx>=len(words):
                        raise RuntimeError("ACTOR_WORD_INDEX_INVALID")
                    normalize=lambda s: "".join(x for x in s.lower() if x.isalnum())
                    if normalize(words[idx]["text"]) != normalize(op["anchor"]["word"]):
                        raise RuntimeError("ACTOR_WORD_NOT_MATCHED")
                    # The native scheduler anchors to source word -60ms, and
                    # the first-frame minimum lead-in is 110ms.
                    expected=max(110,words[idx]["start_ms"]-60)
                    if abs(op["start_ms"]-expected)>4:
                        raise RuntimeError("ACTOR_WORD_DESYNCHRONIZED")
                    by_actor.setdefault(op["target"],[]).append(op)
                    checked_states.add((identity,prm["actor_state"]))
                    if prm["actor_state"] in ("WALK","WAVE","TURN","POINT","CONNECT"):
                        actor_snapshots.append((b["start_ms"]+op["start_ms"]+
                                                min(180,(op["end_ms"]-op["start_ms"])//2),
                                                identity+"_"+prm["actor_state"]))
                for cues in by_actor.values():
                    cues.sort(key=lambda o:o["start_ms"])
                    for earlier,later in zip(cues,cues[1:]):
                        if earlier["end_ms"]>later["start_ms"]:
                            raise RuntimeError("OVERLAPPING_ACTOR_STATES")
            if not required.issubset(checked_states):
                raise RuntimeError("ACTOR_STATES_NOT_IN_COMPILED_VIDEO: "+str(checked_states))
        voice_driver.execute(["node",ROOT/"tools"/"render_reel.js",plan,out,
                              "--fps",args.fps,"--workers",args.workers,
                              "--preset","ultrafast","--web-crf","29"])
        video=out/(film_id+"_"+aspect+"_web.mp4")
        if not video.exists() or video.stat().st_size < 50000:
            raise RuntimeError("NATIVE_VIDEO_MISSING")
        streams=voice_driver.probe(video)["streams"]
        vid=next(s for s in streams if s["codec_type"]=="video")
        aud=next(s for s in streams if s["codec_type"]=="audio")
        assert vid["width"]==vid["height"] and aud["codec_name"]=="aac"
        rend=json.loads((out/("render_"+aspect+".json")).read_text())
        assert not rend.get("page_errors"),rend.get("page_errors")
        for position in (0.24,0.52,0.78):
            image=out/("proof_"+aspect+"_"+str(round(position*100))+".png")
            voice_driver.execute(["ffmpeg","-y","-v","error","-ss",
                                  f"{duration_ms*position/1000:.3f}","-i",video,
                                  "-frames:v","1",image])
        if args.style=="sketch":
            # Exact render-frame evidence of the source action, not a fake
            # standalone character image. The MP4's audio remains intact.
            for stamp, name in actor_snapshots[:8]:
                image=out/("actor_"+aspect+"_"+name+".png")
                voice_driver.execute(["ffmpeg","-y","-v","error","-ss",
                                      f"{stamp/1000:.3f}","-i",video,
                                      "-frames:v","1",image])
                if image.stat().st_size<2000:
                    raise RuntimeError("ACTOR_ACTION_FRAME_EMPTY")
        recordings[aspect]={
            "filename":video.name,"sha256":hashlib.sha256(video.read_bytes()).hexdigest(),
            "bytes":video.stat().st_size,"size":[vid["width"],vid["height"]],
            "gate":compiled["gate"]["status"],"page_errors":[]}
    report={
        "style":args.style,"script":text,"director_scene_count":len(director["scenes"]),
        "actor_sync_verified_against_supplied_word_clock":args.style=="sketch",
        "word_clock_is_measured":alignment_source=="EDGE_MEASURED_WORD_BOUNDARIES",
        "scene_types":dict(choices),"source_integrity":True,
        "microsoft_voice":voice_driver.VOICE,"alignment":alignment_source,
        "native_compiler_gate":gate.get("status"),"compiler_failures":gate.get("failures",[]),
        "videos":recordings}
    (out/"repertoire_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__":
    main()
