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
    # Distinct locomotion and explicit short gestures. A narrated RUN must
    # never silently degrade into WALK; no state is inferred from context.
    ("RUN", r"runs?|sprints?|dashes?"),
    ("WALK", r"walks?|moves?|approaches?|steps?"),
    ("TURN", r"turns?|rotates?|faces?"),
    ("POINT", r"points?|indicates?"),
    ("OFFER", r"carries|carry|sends?|hands?|gives?|delivers?|passes?|offers?"),
    ("RECEIVE", r"receives?|accepts?|takes?|catches?"),
    ("INSPECT", r"checks?|inspects?|examines?|reads?|looks?|watches?"),
    ("PRESENT", r"shows?|presents?|explains?|teaches?|demonstrates?"),
    ("AGREE", r"agrees?|nods?|confirms?"),
    ("LISTEN", r"listens?|hears?"),
    ("JUMP", r"jumps?|leaps?"),
    ("WAVE", r"waves?|greets?"),
    ("WRITE", r"writes?|signs?|draws?"),
    ("LIFT", r"lifts?|raises?|hoists?"),
    ("STOP", r"stops?|halts?"),
    ("CONNECT", r"connects?|links?|attaches?"),
    ("REPAIR", r"repairs?|replaces?|fixes?"),
    ("TEST", r"tests?|verifies?"),
    ("ASK", r"asks?|questions?"),
    ("SHRUG", r"shrugs?"),
    ("CLAP", r"claps?|applauds?"),
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
        # A coordinating "and" does not end the subject: "driver turns
        # toward the door and points" is TWO gestures by the SAME driver.
        # An explicit new noun subject after "and the ..." is never borrowed.
        clause = re.split(r"[.!?;]|\b(?:but|while|when)\b", after, maxsplit=1, flags=re.I)[0]
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
        # A continuous subject can execute more than one explicitly spoken
        # action (e.g. "The courier walks then waves"). The old adapter
        # dropped every action after the first. Do not follow a new named
        # grammatical subject or invent transitional actions.
        action_words = [(candidate, leading.start(1))]
        remainder = clause[leading.end():]
        next_action = re.compile(
            r"\b(?:and\s+then|and|then)\s+"
            r"(?:(?:carefully|quickly|slowly|also|briefly)\s+){0,2}"
            r"([A-Za-z][A-Za-z'-]*)", re.I)
        for later in next_action.finditer(remainder):
            verb = later.group(1)
            if next((name for name, pattern in STATE_ACTIONS
                     if re.fullmatch(pattern, verb, re.I)), None):
                action_words.append((verb, leading.end() + later.start(1)))
        # A cue's own state travels with the op. Repeated verbs can be
        # disambiguated by their exact source-word index on the voice clock.
        for spoken, character_offset in action_words:
            mode = next((name for name, pattern in STATE_ACTIONS
                        if re.fullmatch(pattern, spoken, re.I)), None)
            if mode is None or len(il.get("program") or []) >= 10:
                continue
            # Exact 0-based spoken token position, not first vague
            # occurrence of "walks" or "points" in another clause.
            absolute = match.end() + character_offset
            word_index = len(narration[:absolute].split())
            spoken_tokens = narration.split()
            if word_index >= len(spoken_tokens) or (
                    re.sub(r"[^a-z0-9]", "", spoken_tokens[word_index].lower())
                    != re.sub(r"[^a-z0-9]", "", spoken.lower())):
                continue
            locomotion = mode in ("WALK", "RUN")
            action_ms = (920 if mode == "RUN" else
                         860 if mode == "WALK" else
                         740 if mode in ("JUMP", "TURN") else 600)
            stages = (["IDLE", "START_MOVE", mode, "END_MOVE", "IDLE"]
                      if locomotion else
                      ["IDLE", "ANTICIPATE", mode, "RECOVER", "IDLE"])
            il.setdefault("program", []).append({
                "op": "SETTLE", "target": ent["id"],
                "at": {"word": spoken}, "duration_ms": action_ms,
                "params": {"actor_action": True, "actor_state": mode,
                           "actor_state_path": stages, "voice_sync": True,
                           "word_index": word_index},
            })
            touched.append({"actor": ident, "state": mode, "word": spoken})
    return touched


def ensure_source_count_visual(beat: dict) -> bool:
    """Visualize literal integer counts using exact base-ten place values.

    The Sketch director calls this only when it otherwise has a text-only
    scene. This is a semantic, script-agnostic final realization, not a
    hardcoded Bayes exception. A count must be explicitly measured in source.
    """
    narration = beat["narration"]
    digits = list(re.finditer(r"(?<![\w\d,.])([1-9]\d{0,2})(?![\w\d,.])", narration))
    if len(digits) != 1:
        return False
    number = int(digits[0].group(1))
    # Neither arbitrary identifiers, dates, percentages nor currency become
    # false population counts. A nearby source noun or explicit anaphora is
    # the licence for an accurate place-value object.
    if re.search(r"[$£€₦]|\b(?:19|20)\d\d\b", narration):
        return False
    around = narration[max(0,digits[0].start()-28):digits[0].end()+45]
    if re.search(r"\b(?:percent|per cent|percentage|years? old)\b|%", around, re.I):
        return False
    if not re.search(
            r"\b(cases?|results?|people|patients?|tests?|items?|volunteers?|"
            r"workers?|units?|orders?|calls?|users?|objects?|responses?|"
            r"requests?|messages?|records?|events?|of those|of these|of them)\b",
            narration, re.I):
        return False
    source_word=digits[0].group(1)
    graphic_id="source_place_values"
    beat["illustration"]={
        "form":"OBJECT_STAGE",
        "entities":[{"id":graphic_id,"kind":"evidence","glyph":"BASE10_TALLY",
                     "size":"hero","params":{"value":number}}],
        "relations":[],
        "program":[
            {"op":"DRAW","target":graphic_id,
             "at":{"word":source_word},"duration_ms":260},
            {"op":"GROW","target":graphic_id,
             "at":{"word":source_word},"duration_ms":620},
        ],
        "confirmation":False,
    }
    beat.pop("data",None)
    beat["dominant_layer"]="HYBRID"
    beat["director_evidence"]=[{
        "beat_id":beat["beat_id"],"source":source_word,
        "value":str(number),"unit":"count",
    }]
    return True
