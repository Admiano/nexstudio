"""Source-bound actor performance for native two-dimensional Sketch.

Design reference: swift502/Sketchbook's explicit Idle, start-walk, Walk,
Sprint, and other character-state transitions. This is an original, small
2D scene adapter; it does NOT copy Sketchbook's Three.js/cannon physics or
invent any motions absent from the spoken narration.

Identity is keyed to a recurring source-named actor. Animation onset is keyed
to the spoken action word using the same voice word clock as graphics/text.
"""
from __future__ import annotations
import re

STATE_ACTIONS = (
    ("WALK", r"walks?|runs?|moves?|approaches?|steps?"),
    ("OFFER", r"carries|carry|sends?|hands?|gives?|delivers?|passes?|offers?"),
    ("RECEIVE", r"receives?|accepts?|takes?|catches?"),
    ("INSPECT", r"checks?|inspects?|examines?|reads?|looks?|watches?"),
    ("PRESENT", r"points?|shows?|presents?|explains?|teaches?|demonstrates?"),
    ("AGREE", r"agrees?|nods?|confirms?"),
    ("JUMP", r"jumps?|leaps?"),
)
# Every state has an explicit rest. Source actions are transient performances,
# not a new character identity per scene. No unrelated action is ever inferred.
REST = "IDLE"


def bind_actor_performances(beat: dict) -> list[dict]:
    il = beat.get("illustration") or {}
    if not il.get("entities"):
        return []
    narration = beat["narration"]
    touched = []
    for ent in il["entities"]:
        params = ent.get("params") or {}
        if params.get("visual_class") != "person" or ent.get("kind") not in ("object", "agent"):
            continue
        phrase = ent.get("phrase") or ent.get("label") or ""
        if not phrase:
            continue
        match = re.search(r"\b" + re.escape(phrase) + r"\b", narration, re.I)
        if not match:
            continue
        ident = re.sub(r"[^a-z0-9]+", "_", phrase.lower()).strip("_")
        params["actor_identity"] = ident
        params["actor_state"] = REST
        # Actor must be the grammatical subject of the verb. A courier
        # gives a parcel TO a driver: don't animate the driver giving.
        after = narration[match.end():]
        clause = re.split(r"[.!?;]|\b(?:and|but|while|when)\b", after, maxsplit=1, flags=re.I)[0]
        leading = re.match(r"^\s+(?:carefully\s+|then\s+|also\s+|now\s+|quickly\s+|slowly\s+){0,3}([A-Za-z][A-Za-z'-]*)", clause)
        if not leading:
            ent["params"] = params
            continue
        candidate = leading.group(1)
        state = next((s for s, pattern in STATE_ACTIONS
                      if re.fullmatch(pattern, candidate, re.I)), None)
        if state is None:
            ent["params"] = params
            continue
        params["actor_state"] = state
        ent["params"] = params
        # A real native actor stage has a voice-triggered, seek-safe onset.
        # SETTLE is existing compiler grammar and does not add off-script VO.
        if len(il.get("program") or []) >= 11:
            continue
        il.setdefault("program", []).append({
            "op": "SETTLE", "target": ent["id"],
            "at": {"word": candidate}, "duration_ms": 480,
            "params": {"actor_action": True},
        })
        touched.append({"actor":ident,"state":state,"word":candidate})
    return touched
