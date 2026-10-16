"""SceneBam repertoire: source-verifiable, executable editorial scene archetypes.

These are not style labels or marketing templates. Each detected opportunity has
a native illustration compiler realization, semantic constraints, and anchors to
the original narration. Unrecognized content remains with the existing engine.
All new scenes use the current validated glyph/form/operation vocabulary.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any

# The production renderer can draw all of these with different underlying
# topologies, geometry and motion. Styles further specialise physical object
# stories versus source-accurate evidence.
EXECUTABLE_SCENES = {
    "dataviz": (
        "source_stat", "comparison_bars", "temporal_line", "share_donut",
        "population_subset", "cross_beat_comparison", "categorical_columns",
        "categorical_table", "completion_meter", "milestone_timeline",
        "spoken_process", "verbal_versus", "editorial_magnification",
    ),
    "sketch": (
        "person_performance", "population_tableau", "document_handling",
        "source_object_stage", "causal_connection", "object_transport",
        "state_transformation", "physical_comparison", "narrated_process",
        "highlighted_subject", "negated_subject", "editorial_magnification",
        "spoken_process", "verbal_versus",
    ),
}
# These are scene *recipes*, distinct from the eight low-level topology forms.


def _glyph(id: str, glyph: str, params: dict | None = None, label: str = "") -> dict:
    params = dict(params or {})
    # Large open editorial fields, not the old small glossy dashboard tiles.
    # The renderer and geometry solver honour this execution directive.
    if glyph in ("DATA_BARS", "DATA_TABLE", "TIMELINE", "FLOW_STEPS", "VS_CARDS", "PROGRESS"):
        params["editorial_field"] = True
    out = {"id": id, "kind": "evidence", "glyph": glyph, "size": "hero",
           "params": params}
    if label:
        out["label"] = label
    return out


def _op(name: str, target: str, word: str, duration: int = 460, **fields) -> dict:
    return {"op": name, "target": target, "at": {"word": word},
            "duration_ms": duration, **fields}


def _narrated_stage_ops(beat: dict, glyphs: list[dict],
                         ops: list[dict]) -> list[dict]:
    """Progress real SVG bars, rows, steps and evidence *as each is spoken*.

    The master voice remains continuous. This method only supplies native
    illustration operation anchors; the compiler maps original narration words
    to the recorded speech clock. Neither video time nor source values are
    hardcoded.
    """
    if len(glyphs) != 1:
        return ops
    graphic = glyphs[0]
    kind = graphic["glyph"]
    cues = []
    source_words = beat["narration"].split()
    if kind in ("DATA_BARS", "DATA_TABLE"):
        cues = [str(q.get("anchor") or q["source"].split()[0])
                for q in _qs(beat) if q.get("source")]
    elif kind == "TIMELINE":
        cues = [event["label"] for event in graphic["params"]["events"]]
    elif kind == "FLOW_STEPS":
        cues = [m.group() for m in re.finditer(
            r"\b(first|second|third|fourth|then|next|finally)\b",
            beat["narration"], re.I)]
    elif kind == "VS_CARDS":
        cues = [card["title"].split()[0] for card in graphic["params"]["cards"]]
    if not (2 <= len(cues) <= 8):
        return ops
    # An anchor absent from the actual recorded words cannot be silently
    # converted to an arbitrary timestamp; use the original program instead.
    lexical = {re.sub(r"[^a-z0-9]", "", w.lower()) for w in source_words}
    if any(re.sub(r"[^a-z0-9]", "", cue.lower()) not in lexical for cue in cues):
        return ops
    # Consecutive small steps reveal exact matching evidence pieces as voice
    # reaches their source. setGrow(k) in the original native runtime already
    # reveals progressive chart components; these ops become its timeline.
    result = [op for op in ops if op["op"] != "GROW"]
    n = len(cues)
    # Bind the precise occurrence in the spoken master word stream. This
    # matters for repeated labels such as "in 2020 ... in 2021" and avoids
    # the global find-first-word ambiguity that revealed steps too soon.
    normalize = lambda word: re.sub(r"[^a-z0-9%]", "", word.lower())
    cursor = 0
    for index, cue in enumerate(cues):
        cue_key = normalize(cue)
        if kind in ("DATA_BARS", "DATA_TABLE") and index < len(_qs(beat)):
            explicit = _qs(beat)[index].get("word_start")
        else:
            explicit = None
        if (isinstance(explicit, int) and 0 <= explicit < len(source_words)
                and normalize(source_words[explicit]) == cue_key
                and explicit >= cursor):
            at_index = explicit
        else:
            at_index = next((i for i in range(cursor, len(source_words))
                             if normalize(source_words[i]) == cue_key), None)
        if at_index is None:
            # A semantic claim without a verifiable word anchor must never
            # receive a fabricated millisecond or appear as a late surprise.
            return ops
        result.append({"op": "GROW", "target": graphic["id"],
                       "at": {"word": cue}, "duration_ms": 320,
                       "from": round(index/n, 5),
                       "to": round((index+1)/n, 5),
                       "params": {"word_index": at_index}})
        cursor = at_index + 1
    return result


def _commit(beat: dict, glyphs: list[dict], ops: list[dict], *,
            form: str = "OBJECT_STAGE", relations: list[dict] | None = None,
            evidence: list[dict] | None = None) -> None:
    ops = _narrated_stage_ops(beat, glyphs, ops)
    beat["illustration"] = {"form": form, "entities": glyphs,
                            "relations": relations or [], "program": ops,
                            "confirmation": False}
    beat.pop("data", None)  # mutually exclusive composer roles
    beat["dominant_layer"] = "HYBRID"
    if evidence:
        # Single-beat evidence and multi-beat evidence use the same auditable
        # source identifier schema; never leave provenance orphaned.
        beat["director_evidence"] = [
            {"beat_id": beat["beat_id"], **item} for item in evidence]


def _qs(beat: dict) -> list[dict]:
    return list((beat.get("data_claim") or {}).get("quantities") or [])


def _positive(q: dict) -> Decimal | None:
    if q.get("qualifier") or q.get("signed"):
        return None
    try:
        x = Decimal(str(q["value"]))
    except (KeyError, InvalidOperation):
        return None
    return x if x.is_finite() and x > 0 else None


def _label(q: dict) -> str:
    """Non-inferred measurement/category already adjacent to a numeric source."""
    label = re.sub(r"[^a-zA-Z0-9 ]", " ", q.get("label") or "").strip()
    stop = {"the", "and", "of", "about", "than", "with", "from", "are",
            "were", "was", "there", "for", "each", "after", "before",
            "between", "this", "that", "those", "these", "more", "less"}
    words = [w for w in label.split() if w.lower() not in stop]
    return " ".join(words[:2])


def _category_rows(beat: dict) -> list[tuple[str, Decimal, str]]:
    qs = _qs(beat)
    if not (3 <= len(qs) <= 6):
        return []
    if len({q.get("unit", "") for q in qs}) != 1 or any(q.get("period") for q in qs):
        return []
    result = []
    for q in qs:
        number = _positive(q)
        label = _label(q)
        if number is None or not label or len(label) > 16:
            return []
        result.append((label, number, q["source"]))
    if len({r[0].lower() for r in result}) != len(result):
        return []
    values = [r[1] for r in result]
    if min(values) / max(values) < Decimal(".05"):
        return []   # The renderer would exaggerate extremely small bars.
    return result


def _events(beat: dict) -> list[tuple[str, str]]:
    """2-5 year-labelled clauses only, each with a distinct source event."""
    text = beat["narration"]
    m = list(re.finditer(r"\b(?:in|during|by)\s+((?:19|20)\d{2})\b", text, re.I))
    if not (2 <= len(m) <= 5):
        return []
    years = [int(x.group(1)) for x in m]
    if len(set(years)) != len(years) or years != sorted(years):
        return []
    out = []
    for i, item in enumerate(m):
        tail = text[item.end(): m[i+1].start() if i+1 < len(m) else len(text)]
        tail = re.split(r"[.;]", tail)[0].strip(" ,.:-")
        words = re.findall(r"[A-Za-z][A-Za-z'-]*", tail)
        if not (2 <= len(words) <= 10):
            return []
        out.append((item.group(1), " ".join(words[:3])))
    return out


def _steps(beat: dict) -> list[str]:
    text = beat["narration"]
    marks = list(re.finditer(r"\b(first|second|third|fourth|then|next|finally)\b", text, re.I))
    if len(marks) < 2 or len(marks) > 5:
        return []
    # Do not turn a casual subordinate "then" into a fake procedure.
    if marks[0].start() > 8 and not re.search(r"\b(steps?|stages?|process|sequence|procedure)\b", text, re.I):
        return []
    spans = []
    for i, item in enumerate(marks):
        tail = text[item.start(): marks[i+1].start() if i+1 < len(marks) else len(text)]
        words = re.findall(r"[A-Za-z][A-Za-z'-]*", tail)
        if len(words) < 3:
            return []
        # The visual step must state a useful ACTION + OBJECT, not merely
        # "First wash the" or "Then replace the". These words are selected
        # verbatim from the corresponding spoken clause, never generated.
        content = words[1:]  # drop spoken ordinal/connector
        cutoff = next((i for i, w in enumerate(content)
                       if w.lower() in ("because", "before", "after", "under", "during")),
                      len(content))
        content = [w for w in content[:cutoff]
                   if w.lower() not in ("the", "a", "an", "this", "that", "those", "these")
                   and not (w.lower().endswith("ly") and len(w) > 6)]
        if len(content) < 2:
            return []
        caption = content[:3]
        if len(" ".join(caption)) > 18:
            caption = [content[0], content[-1]]
        if len(" ".join(caption)) > 18:
            return []
        spans.append(" ".join(caption))
    return spans


def _versus(beat: dict) -> tuple[str, str] | None:
    text = beat["narration"]
    if _qs(beat):
        return None
    marker = re.search(r"\b(?:versus|vs\.?|compared with|compared to)\b", text, re.I)
    if not marker:
        return None
    # Small nonnumeric source nouns anchored to both sides; never hallucinate
    # a brand or concept missing from the narration.
    left = re.findall(r"[A-Za-z][A-Za-z'-]*", text[:marker.start()])
    right = re.findall(r"[A-Za-z][A-Za-z'-]*", text[marker.end():])
    if not left or not right:
        return None
    a = " ".join(left[-2:]); b = " ".join(right[:2])
    if a.lower() == b.lower() or len(a) > 18 or len(b) > 18:
        return None
    return a, b


def _focus(beat: dict) -> str | None:
    # Explicit call to inspect a named phrase, not a guess that every claim
    # deserves a magnifying glass.
    match = re.search(r"\b(?:look closely at|zoom in on|focus on|inspect)\s+(?:the\s+|a\s+|an\s+)?([A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,2})", beat["narration"], re.I)
    if not match:
        return None
    # Stop at the next purpose/preposition, not at the arbitrary third token.
    # "warning label to confirm" is a source-named warning label, NOT a
    # three-word object called "warning label to".
    phrase = re.split(r"\b(?:to|so|because|when|while|for|and|that)\b",
                      match.group(1), maxsplit=1, flags=re.I)[0].strip()
    return phrase or None


def _progress(beat: dict) -> dict | None:
    qs = _qs(beat)
    if len(qs) != 1 or qs[0].get("unit") != "%":
        return None
    x = _positive(qs[0])
    if x is None or x > 100:
        return None
    text = beat["narration"]
    if not re.search(r"\b(completed?|finished?|achieved?|progress|capacity|filled?|goal|target)\b", text, re.I):
        return None
    return qs[0]


def _source_overlay_target(beat: dict) -> dict | None:
    il = beat.get("illustration") or {}
    if il.get("form") != "OBJECT_STAGE" or il.get("carry") or il.get("persist_to") or il.get("relations"):
        return None
    ents = [e for e in (il.get("entities") or []) if e.get("kind") == "object"]
    if len(ents) == 1:
        return ents[0]
    # A source may contain incidental words alongside exactly ONE real object.
    # Carry the identifiable drawing, not a text collage of those adjectives.
    drawn = [e for e in ents if e.get("asset_ref") or
             (e.get("params") or {}).get("visual_class")]
    if len(drawn) == 1:
        return drawn[0]
    if not drawn:
        return None
    # Multiple illustrated nouns may be present, but the *imperative* has a
    # single directly named object. "Never use the damaged receipt because
    # the delivery..." must mark the RECEIPT, not the incidental delivery.
    # An instruction naming two objects stays uncommitted rather than
    # arbitrarily choosing the first.
    source = beat["narration"]
    imperative = re.search(
        r"\b(?:never\s+use|do\s+not\s+use|don't\s+use|avoid|"
        r"prohibit|forbid|circle|highlight|mark|identify|single\s+out)\b",
        source, re.I)
    if not imperative:
        return None
    instruction = re.split(r"\b(?:because|so that|so the|which|whereas)\b",
                           source[imperative.end():], maxsplit=1, flags=re.I)[0]
    named = [e for e in drawn
             if e.get("phrase") and re.search(
                 r"\b"+re.escape(e["phrase"])+r"\b", instruction, re.I)]
    return named[0] if len(named) == 1 else None


def _safe_overlay(beat: dict, *, block: bool) -> bool:
    il = beat.get("illustration") or {}
    if il.get("form") != "OBJECT_STAGE" or il.get("carry") or il.get("persist_to"):
        return False
    target = _source_overlay_target(beat)
    if not target:
        return False
    ents = [target]
    name = target.get("phrase") or ""
    if not name or not re.search(rf"\b{re.escape(name)}\b", beat["narration"], re.I):
        return False
    # A negated *claim* does not imply the physical object is banned.
    text = beat["narration"]
    if block:
        if not re.search(rf"\b(?:do not|don't|never|avoid|prohibit|forbid)\s+(?:use|select|choose|open|install|connect)\b", text, re.I):
            return False
        graphic, typ, form, op = "PROHIBIT", "blocks", "OBJECT_STAGE", "DRAW"
    else:
        if not re.search(r"\b(highlight|circle|mark|point out|identify|single out)\b", text, re.I):
            return False
        graphic, typ, form, op = "MARK_CIRCLE", "marks", "OBJECT_STAGE", "TRACE"
    mark = "director_overlay"
    target_cue = name.split()[0]
    current = ([op for op in (il.get("program") or []) if op.get("target") == target["id"]]
               if len(il.get("entities") or []) == 1 else
               [_op("DRAW", target["id"], target_cue, 460)])
    if len(current) >= 9:
        return False
    ents.append(_glyph(mark, graphic))
    il["entities"] = ents
    il["relations"] = (il.get("relations") or []) + [
        {"type": typ, "source": mark, "target": target["id"]}]
    il["program"] = current + [_op(op, mark, target_cue)]
    beat["illustration"] = il
    return True


def candidates(style: str, beat: dict) -> list[tuple[str, float, tuple[str, ...]]]:
    """Only return opportunities that have a real executable native scene."""
    ans: list[tuple[str, float, tuple[str, ...]]] = []
    rows = _category_rows(beat)
    if style == "dataviz":
        if rows:
            evidence = tuple(r[2] for r in rows)
            if re.search(r"\b(table|tabulated|ledger|report|breakdown)\b", beat["narration"], re.I) and len(rows) <= 5:
                ans.append(("categorical_table", 1.65, evidence))
            if re.search(r"\b(rank|ranking|highest|lowest|top|bottom|compare|versus)\b", beat["narration"], re.I):
                ans.append(("categorical_columns", 1.52, evidence))
            else:
                ans.append(("categorical_columns", 1.45, evidence))
        progress = _progress(beat)
        if progress:
            ans.append(("completion_meter", 1.57, (progress["source"],)))
        events = _events(beat)
        if events and not rows and (beat.get("data_claim") or {}).get("kind") != "TREND":
            ans.append(("milestone_timeline", 1.40, tuple(e[0] for e in events)))
    if style in ("dataviz", "sketch"):
        steps = _steps(beat)
        if steps:
            ans.append(("spoken_process", 1.48 if style == "sketch" else 1.35, tuple(steps)))
        comparison = _versus(beat)
        if comparison:
            ans.append(("verbal_versus", 1.14, comparison))
        focus = _focus(beat)
        if focus:
            ans.append(("editorial_magnification", 1.12, (focus,)))
    if style == "sketch":
        il = beat.get("illustration") or {}
        if _source_overlay_target(beat):
            if re.search(r"\b(?:do not|don't|never|avoid|prohibit|forbid)\s+(?:use|select|choose|open|install|connect)\b", beat["narration"], re.I):
                ans.append(("negated_subject", 1.18, ()))
            elif re.search(r"\b(highlight|circle|mark|point out|identify|single out)\b", beat["narration"], re.I):
                ans.append(("highlighted_subject", 1.18, ()))
    return ans


def realize(family: str, beat: dict, *, style: str | None = None) -> bool:
    """Realize precisely one selected family using the native contract.

    The film director owns the selection; the renderer owns every pixel.
    """
    text = beat["narration"]
    first = text.split()[0]
    qs = _qs(beat)
    if family == "categorical_columns":
        rows = _category_rows(beat)
        if not rows:
            return False
        graphic = _glyph("scene_categories", "DATA_BARS",
                         {"series": [{"label": label, "value": float(value),
                                      "value_text": source} for label, value, source in rows]})
        # Every bar follows its OWN source quantity, instead of sweeping
        # all six data values when only the first/last number was spoken.
        # word_index disambiguates repeated numbers in the intact voice.
        stages = [_op("GROW", graphic["id"], str(q["anchor"]), 320,
                      params={"stage_index": i, "word_index": int(q["word_start"])},
                      to=(i+1)/len(qs))
                  for i, q in enumerate(qs)]
        _commit(beat, [graphic],
                [_op("DRAW", graphic["id"], first, 220)] + stages,
                evidence=[{"source": s, "value": str(v), "label": l} for l, v, s in rows])
        return True
    if family == "categorical_table":
        rows = _category_rows(beat)
        if not rows or len(rows) > 5:
            return False
        graphic = _glyph("scene_table", "DATA_TABLE",
                         {"rows": [[label, str(value)] for label, value, _ in rows]})
        stages = [_op("GROW", graphic["id"], str(q["anchor"]), 300,
                      params={"stage_index": i, "word_index": int(q["word_start"])},
                      to=(i+1)/len(qs))
                  for i, q in enumerate(qs)]
        _commit(beat, [graphic],
                [_op("DRAW", graphic["id"], first, 220)] + stages,
                evidence=[{"source": s, "value": str(v), "label": l} for l, v, s in rows])
        return True
    if family == "completion_meter":
        q = _progress(beat)
        if not q:
            return False
        value = _positive(q)
        graphic = _glyph("scene_progress", "PROGRESS",
                         {"level": float(value / 100), "right": q["source"]})
        _commit(beat, [graphic], [
            _op("DRAW", graphic["id"], first, 250),
            _op("GROW", graphic["id"], str(q.get("anchor") or first), 540)],
            evidence=[{"source": q["source"], "value": str(value), "unit": "%"}])
        return True
    if family == "milestone_timeline":
        events = _events(beat)
        if not events:
            return False
        graphic = _glyph("scene_timeline", "TIMELINE",
                         {"events": [{"label": year, "sub": subtitle}
                                     for year, subtitle in events]})
        _commit(beat, [graphic],
                [_op("DRAW", graphic["id"], first, 220)] +
                [_op("GROW", graphic["id"], year, 310,
                     params={"stage_index": i}, to=(i+1)/len(events))
                 for i, (year, _) in enumerate(events)],
                evidence=[{"source": y, "event": e} for y, e in events])
        return True
    if family == "spoken_process":
        steps = _steps(beat)
        if not steps:
            return False
        graphic = _glyph("scene_steps", "FLOW_STEPS",
                         {"steps": [{"label": step} for step in steps]})
        # Process-heavy scenes have multiple spoken clauses. Show their three
        # sentences sequentially, never make a 17+-word hero that violates
        # the native legibility floor. Source copy stays VERBATIM.
        positions = list(re.finditer(r"\b(first|second|third|fourth|then|next|finally)\b", text, re.I))
        if positions and positions[0].start() == 0 and 2 <= len(positions) <= 5:
            units = []
            for idx, match in enumerate(positions):
                ending = positions[idx+1].start() if idx + 1 < len(positions) else len(text)
                phrase = text[match.start():ending].strip()
                if not phrase:
                    continue
                units.append({
                    "text": phrase,
                    "role": "hero" if idx == len(positions)-1 else "support",
                    "anchor_word": phrase.split()[0],
                    "emphasis": .88 if idx == len(positions)-1 else .62,
                    "semantic_role": "punch" if idx == len(positions)-1 else "setup",
                    "can_promote": idx == len(positions)-1,
                    "reveal": "WORD_CASCADE",
                    "stress": [],
                })
            if len(units) == len(positions) and " ".join(
                    unit["text"] for unit in units) == text:
                beat["display_units"] = units
        cues = list(re.finditer(
            r"\b(first|second|third|fourth|then|next|finally)\b", text, re.I))
        _commit(beat, [graphic],
                [_op("DRAW", graphic["id"], first, 220)] +
                [_op("GROW", graphic["id"], m.group(0), 320,
                     params={"stage_index": i,
                             "word_index": len(text[:m.start()].split())},
                     to=(i+1)/len(cues))
                 for i, m in enumerate(cues)],
                evidence=[{"source": step} for step in steps])
        return True
    if family == "verbal_versus":
        pair = _versus(beat)
        if not pair:
            return False
        graphic = _glyph("scene_versus", "VS_CARDS",
                         {"cards": [{"title": pair[0]}, {"title": pair[1]}]})
        pair_words = [pair[0].split()[0], pair[1].split()[0]]
        anchors = [next((i for i, w in enumerate(text.split())
                         if w.lower().strip(".,;:") == phrase.lower()), 0)
                   for phrase in pair_words]
        _commit(beat, [graphic],
                [_op("DRAW", graphic["id"], first, 220)] +
                [_op("GROW", graphic["id"], pair_words[i], 330,
                     params={"stage_index": i, "word_index": anchors[i]},
                     to=(i+1)/2)
                 for i in range(2)],
                evidence=[{"source": s} for s in pair])
        return True
    if family == "editorial_magnification":
        phrase = _focus(beat)
        if not phrase:
            return False
        if style == "sketch":
            # Sketch must magnify REAL pictorial evidence, not typeset a
            # magnifying-glass card around exactly the same headline.
            # Reuse a drawn source entity first. Only when necessary build a
            # native physical subject from the existing reviewed noun taxonomy.
            il = beat.get("illustration") or {}
            available = [
                e for e in (il.get("entities") or [])
                if e.get("phrase", "").lower() == phrase.lower() and
                (e.get("asset_ref") or (e.get("params") or {}).get("visual_class"))
            ]
            from make_reel import STYLES
            taxonomy = STYLES.get("sketch_visual_classes") or {}
            kind = next((klass for klass, terms in taxonomy.items()
                         if phrase.lower() in terms and
                         klass in ("document", "list", "package", "person")), None)
            if kind is not None:
                # The licensed pictorial taxonomy is the visual authority for
                # a named source item. Retain its mandatory source noun, but
                # do not print it as a duplicate illustrated-object caption.
                # A former registered TILE icon would otherwise mask the
                # reviewed source-specific procedural drawing.
                subject = {
                    "id": available[0]["id"] if available else "director_focus_subject",
                    "kind": "object", "glyph": "TILE", "size": "hero",
                    "phrase": phrase.lower(), "label": phrase.lower(),
                    "params": {"visual_class": kind, "caption_suppressed": True}}
            elif available and available[0].get("asset_ref"):
                subject = dict(available[0])
                subject.pop("label", None)
            else:
                # No source-supported physical subject: do not fabricate one
                # merely so the film can have a magnifying-glass animation.
                return False
            subject["size"] = "hero"
            lens_id = "director_focus_lens"
            subject_word = phrase.split()[0]
            lens = {"id": lens_id, "kind": "evidence",
                    "glyph": "LENS", "size": "support"}
            _commit(
                beat, [subject, lens], [
                    _op("DRAW", lens_id, first, 230),
                    _op("DRAW", subject["id"], subject_word, 360),
                    _op("TRAVEL", lens_id, phrase.split()[-1], 560,
                        params={"over": [subject["id"]]}),
                ], form="CALLOUT_LENS",
                relations=[{"type": "scans", "source": lens_id,
                            "target": subject["id"]}],
                evidence=[{"source": phrase}])
            return True
        graphic = _glyph("scene_magnification", "MAGNIFY",
                         {"text": phrase, "zoom": 1.7})
        _commit(beat, [graphic], [
            _op("DRAW", graphic["id"], first, 240),
            _op("GROW", graphic["id"], phrase.split()[0], 850)],
            evidence=[{"source": phrase}])
        return True
    if family == "negated_subject":
        return _safe_overlay(beat, block=True)
    if family == "highlighted_subject":
        return _safe_overlay(beat, block=False)
    return False
