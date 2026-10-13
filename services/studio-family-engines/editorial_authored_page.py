"""Lossless binding of explicitly authored typography to the native page body.

This port accepts a bounded, unambiguous legacy Art declaration. It never treats
the scene's purpose/reveal prose as display copy, invents text, or drops a prop.
"""
from copy import deepcopy
import re
from canonical import stable
from contracts import AdapterReplan, creative_replan_request, rational_seconds


def fail(code, detail):
    raise AdapterReplan(code,detail,creative_replan_request(
        escalation_scope="ART_AND_COMPOSITION_STRATEGY",
        invalidate_slots=["art_direction","storyboard","cinematography","editorial_rhythm","motion_performance","sound_direction"],
        issue=detail,revision_plan="Provide exact authored page copy, one explicit vacancy/insertion, and executable page actions and sound targets.",
        quality_reason=code,constraints=["Do not invent display copy or omit authored elements."]))


def bind_authored_page(board):
    art=board.get("authored_art") or {}
    form=art.get("form_request") or {}
    representation=str(form.get("representation") or "")
    if "authored body copy is exactly:" not in representation.lower():
        return None
    match=re.search(r"authored body copy is exactly:\s*[‘\"](.*?)[’\"](?=\s|$)",representation,re.I|re.S)
    if not match: fail("EDITORIAL_AUTHORED_COPY_AMBIGUOUS","Exact quoted page copy is required.")
    lines=match.group(1).split(" / ")
    if len(lines)<2 or any(not line.strip() for line in lines):
        fail("EDITORIAL_AUTHORED_COPY_AMBIGUOUS","Page copy must contain explicit nonempty lines.")
    gaps=[(index,m.start(),m.end()) for index,line in enumerate(lines) for m in re.finditer(r" {2,}",line)]
    word=re.search(r"\b([\w-]+) later fills that vacancy\b",representation)
    if len(gaps)!=1 or not word:
        fail("EDITORIAL_AUTHORED_VACANCY_AMBIGUOUS","Exactly one authored blank interval and an explicit insertion word are required.")
    insertion=word.group(1)
    index,start,end=gaps[0]
    operations=" ".join(str(x) for x in form.get("required_operations") or [])
    if not all(term in operations.lower() for term in ("scroll","halt","re-break")):
        fail("EDITORIAL_AUTHORED_PAGE_OPERATION_UNSUPPORTED","Native page requires explicitly directed scroll, halt and re-break operations.")
    beats=board["beats"]
    segments=[];cursor=0.;arrival=None;halt=None;source_bindings=[];sound_sync={}
    supported={"REFRAME_CONTENT","SETTLE","TYPE_REVEAL","REVEAL"}
    audio_roles={"silence","single dry sound-library tick","weighted sound impact","final silence"}
    page_roles={"uniform text block","even margins","paper field","unemphasized authored vacancy",
        "continuous uniform page","halted page","surrounding uniform lines","re-breaking surrounding lines",
        "re-aligned column","unchanged surrounding copy","re-pointed line endings"}
    for beat in beats:
        bid=beat["beat_id"];edit=beat.get("editorial") or {}
        duration=rational_seconds(edit.get("duration"),1)
        canonical=cursor
        # rational_seconds clamps durations; use exact rational arithmetic for starts.
        if isinstance(edit.get("start"),dict):
            st=edit["start"];canonical=float(st["value"])/float(st["rate"])
        if abs(canonical-cursor)>.001:
            fail("EDITORIAL_AUTHORED_PAGE_TIMELINE_UNSUPPORTED","Page requires contiguous canonical beat timing: "+bid)
        actions=beat.get("motion_actions") or []
        verbs=[str((a.get("execution") or {}).get("resolved_verb") or a.get("requested_verb")) for a in actions]
        if not actions or any(a.get("performer_class")!="SCENE_GRAPH" for a in actions) or any(v not in supported for v in verbs):
            fail("EDITORIAL_AUTHORED_PAGE_MOTION_UNSUPPORTED","Unsupported page motion: "+bid)
        if any(v in {"REVEAL","TYPE_REVEAL"} for v in verbs):
            if arrival is not None: fail("EDITORIAL_AUTHORED_VACANCY_AMBIGUOUS","Multiple insertion beats require an explicit richer page contract.")
            rate=float((edit.get("duration") or {}).get("rate") or 1)
            arrival=cursor+float(edit.get("action_frame") or 0)/rate
            reveal_end=cursor+float(edit.get("settle_frame") or 0)/rate
            reveal_end=min(cursor+duration,max(arrival+.001,reveal_end))
        if halt is None and "SETTLE" in verbs: halt=cursor
        camera=(beat.get("camera") or {}).get("camera_atom") or {}
        if camera.get("atom") not in {"TRACK","FOLLOW","HOLD"}:
            fail("EDITORIAL_AUTHORED_PAGE_CAMERA_UNSUPPORTED","Native reading page supports TRACK/FOLLOW/HOLD: "+bid)
        for role in beat.get("supporting_assets") or []:
            if not isinstance(role,str): fail("EDITORIAL_SUPPORT_BINDING_UNAVAILABLE",bid+": explicit page support label required")
            label=role.lower().strip()
            if label in page_roles: kind="AUTHORED_PAGE_LAYOUT"
            elif label in audio_roles and beat.get("sound_events"): kind="DIRECTED_SOUND"
            else: fail("EDITORIAL_SUPPORT_BINDING_UNAVAILABLE",bid+":"+role)
            source_bindings.append({"beatId":bid,"sourceLabel":role,"bindingKind":kind})
        segments.append({"beatId":bid,"start":cursor,"end":cursor+duration,"verbs":verbs,
            "actionIds":[a["action_id"] for a in actions],"camera":deepcopy(camera),"editorial":deepcopy(edit),
            "adapterTrace":{"creativeChoiceIntroduced":False,"sourceBeatId":bid}})
        cursor+=duration
    if halt is None or arrival is None or halt>arrival:
        fail("EDITORIAL_AUTHORED_PAGE_MOTION_UNSUPPORTED","Scroll, halt and insertion must be directed in that order.")
    for beat,segment in zip(beats,segments):
        for event in beat.get("sound_events") or []:
            if event.get("kind")=="SILENCE": continue
            target=str(event.get("sync_target") or "")
            if target==f"line break in {beat['beat_id']}" and "REFRAME_CONTENT" in segment["verbs"]:
                # A crossing authored line is a shared native visual/audio event.
                at=segment["start"]+(segment["end"]-segment["start"])/2
            elif target in {f"{insertion} lands into authored vacancy",f"the instant {insertion} appears in the authored vacancy and the surrounding lines re-break"}: at=arrival
            else:
                # Existing explicit action IDs and beat boundaries retain their binding.
                continue
            sound_sync[event["event_id"]]={"syncTarget":target,"at":at,"sourceBeatId":beat["beat_id"]}
    spec={"schema":"StudioEditorialAuthoredPageV1","lines":lines,"vacancy":{"lineIndex":index,"start":start,"end":end},
        "insertion":insertion,"scrollEnd":halt,"arrival":arrival,"revealEnd":reveal_end,
        "duration":cursor,"scenes":segments,"supportBindings":source_bindings,"soundSync":sound_sync,
        "sourceArtHash":stable(art),"sourceBoardHash":stable(board),"copyAuthority":"P8_AUTHORED_ART_ONLY"}
    spec["pageHash"]=stable(spec)
    return spec
