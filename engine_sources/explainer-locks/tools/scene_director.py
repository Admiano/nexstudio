"""Film-level, source-grounded scene director for SceneBam Sketch and Data Viz.

Select a whole-film visual argument before turning beats into compiler directives.
No subject- or script-specific routes. Decisions are bounded by the actual native
illustration contract. The evidence ledger prevents invented cross-scene measures.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Any

_CONTRAST = re.compile(r"\b(yet|but|however|whereas|while|versus|vs\.?|compared|instead|rather)\b", re.I)
_PROCESS = re.compile(r"\b(because|causes?|produces?|transfers?|flows?|feeds?|passes?|leads? to|results? in|therefore|then)\b", re.I)
_SHARE = re.compile(r"\b(out of|in every|among|of all|share of|fraction|portion|percent|percentage)\b", re.I)
_TIME = re.compile(r"\b(19\d\d|20\d\d|january|february|march|april|may|june|july|august|september|october|november|december)\b", re.I)
_STOP = frozenset("""the a an it is are was were to of by as with in on for and or but if that this these those
people person thing number numbers data year years percent percentage about only just also then
there here they them their from into how why what when where than more less same very""".split())


def _terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower())
            if len(w) > 3 and w not in _STOP}


def _measures(beat: dict) -> list[dict]:
    return (beat.get("data_claim") or {}).get("quantities") or []


def _quantity(beat: dict) -> dict | None:
    qs = _measures(beat)
    if len(qs) != 1:
        return None
    q = qs[0]
    if q.get("qualifier") or q.get("signed") or q.get("role", "measure") != "measure":
        return None
    try:
        number = Decimal(str(q["value"]))
    except (KeyError, InvalidOperation):
        return None
    if not number.is_finite() or number <= 0:
        return None
    return q


@dataclass(frozen=True)
class Opportunity:
    family: str
    score: float
    evidence: tuple[str, ...] = ()


def _bridge_eligible(prev: dict, current: dict) -> bool:
    """Conservative film-level comparison of values already SPOKEN in adjacent beats."""
    if not _CONTRAST.search(current["narration"]):
        return False
    a, b = _quantity(prev), _quantity(current)
    if a is None or b is None or a.get("unit") != b.get("unit"):
        return False
    # Never silently treat a monetary amount as comparable with a percentage,
    # nor draw a physically exaggerated sub-two-percent bar.
    av, bv = Decimal(str(a["value"])), Decimal(str(b["value"]))
    if min(av, bv) / max(av, bv) < Decimal(".02"):
        return False
    # The repeated topical term is evidence of continuity. A conjunction alone
    # never licenses comparing unrelated numbers.
    if not (_terms(prev["narration"]) & _terms(current["narration"])):
        return False
    # A trend line cannot be rewritten as an unrelated two-number bar chart.
    if any((beat.get("data_claim") or {}).get("kind") not in ("STAT", "SHARE")
           for beat in (prev, current)):
        return False
    return True


def _subset_eligible(prev: dict, current: dict) -> bool:
    """A numerator is part of the earlier whole only with explicit group language."""
    narration = current["narration"]
    if not re.search(r"\\b(only|just|merely|out of|subset|a fraction of)\\b", narration, re.I):
        return False
    if not re.search(r"\\b(inside|among|within|of those|of these|of them|of that group|of the group|in that group|out of|population|subset)\\b", narration, re.I):
        return False
    a, b = _quantity(prev), _quantity(current)
    if not a or not b or a.get("unit") != b.get("unit") or a.get("unit") == "%":
        return False
    whole, part = Decimal(str(a["value"])), Decimal(str(b["value"]))
    if whole != whole.to_integral_value() or part != part.to_integral_value():
        return False
    if whole < 20 or part < 1 or part >= whole:
        return False
    ratio = part / whole
    if not Decimal(".005") <= ratio <= Decimal(".75"):
        return False
    return bool(_terms(prev["narration"]) & _terms(narration))


def _opportunities(style: str, beat: dict, prev: dict | None, index: int,
                   count: int) -> list[Opportunity]:
    ill = beat.get("illustration") or {}
    form = ill.get("form")
    kind = (beat.get("data_claim") or {}).get("kind")
    narration = beat["narration"]
    n = len(_measures(beat))
    ans = [Opportunity("editorial_reveal", .28)]
    if index == 0:
        ans.append(Opportunity("establish", .50))
    if index == count - 1:
        ans.append(Opportunity("resolve", .76))
    if _CONTRAST.search(narration):
        ans.append(Opportunity("contrast", .58))
    if _PROCESS.search(narration):
        ans.append(Opportunity("mechanism", .65))
    if form in ("PROCESS_PIPELINE", "RELATIONSHIP", "STATE_TRANSFORMATION"):
        ans.append(Opportunity("mechanism", .89, (form,)))
    if form == "COMPARISON":
        ans.append(Opportunity("contrast", .88, (form,)))
    if style == "dataviz":
        if kind == "TREND" and form == "DATA_VISUAL":
            ans.append(Opportunity("evidence_trend", 1.3, tuple(q["source"] for q in _measures(beat))))
        elif kind == "COMPARISON" and form == "DATA_VISUAL":
            ans.append(Opportunity("evidence_compare", 1.22, tuple(q["source"] for q in _measures(beat))))
        elif kind == "SHARE":
            ans.append(Opportunity("part_to_whole", 1.04, tuple(q["source"] for q in _measures(beat))))
        elif kind == "STAT" and n == 1:
            ans.append(Opportunity("evidence_stat", .82, (_measures(beat)[0]["source"],)))
        if prev and _subset_eligible(prev, beat):
            a, b = _quantity(prev), _quantity(beat)
            ans.append(Opportunity("population_subset", 1.48, (a["source"], b["source"])))
        if prev and _bridge_eligible(prev, beat):
            a, b = _quantity(prev), _quantity(beat)
            ans.append(Opportunity("evidence_bridge", 1.42, (a["source"], b["source"])))
    else:
        if form in ("OBJECT_STAGE", "SIGNAL"):
            ents = ill.get("entities") or []
            if any(e.get("asset_ref") or e.get("params", {}).get("visual_class") for e in ents):
                ans.append(Opportunity("physical_stage", .72))
            if _SHARE.search(narration):
                ans.append(Opportunity("subset_explanation", .71))
            if n:
                ans.append(Opportunity("evidence_in_context", .59))
    return ans


def plan_film(style: str, beats: list[dict]) -> list[Opportunity]:
    """Small beam search optimizes the WHOLE sequence, not the first matching regex.

    Candidate fitness is balanced against same-family repetition and film pacing.
    The planner cannot choose an unsupported native visual; realizers below make
    only contract-valid operations, and never mutate the spoken text.
    """
    if style not in ("sketch", "dataviz"):
        return []
    if not beats:
        return []
    beam: list[tuple[float, tuple[Opportunity, ...]]] = [(0., ())]
    for i, beat in enumerate(beats):
        prev = beats[i-1] if i else None
        opportunities = _opportunities(style, beat, prev, i, len(beats))
        next_beam = []
        for score, path in beam:
            for cand in opportunities:
                penalty = 0.
                if path and path[-1].family == cand.family:
                    penalty += .30
                if len(path) >= 2 and path[-2].family == path[-1].family == cand.family:
                    penalty += .47
                # An outcome should become evidence, not another generic word
                # card, when the script actually contains supported numbers.
                if style == "dataviz" and _measures(beat) and cand.family in ("editorial_reveal", "establish"):
                    penalty += .55
                if i == len(beats)-1 and cand.family == "resolve" and len(_measures(beat)) > 0:
                    penalty -= .10
                next_beam.append((score + cand.score - penalty, path + (cand,)))
        beam = sorted(next_beam, key=lambda item: (-item[0], tuple(x.family for x in item[1])))[:24]
    return list(beam[0][1])


def _bar_label(beat: dict, q: dict) -> str:
    """Only original source terms, never model-generated names for the datum."""
    phrase = str(q.get("label") or "").strip(" .,;:")
    words = [w for w in re.findall(r"[A-Za-z]+", phrase) if w.lower() not in _STOP]
    if not words:
        # A label-free bar is preferable to an invented unit or false category.
        return ""
    return " ".join(words[:2])


def _bridge(prev: dict, current: dict) -> bool:
    if not _bridge_eligible(prev, current):
        return False
    a, b = _quantity(prev), _quantity(current)
    av, bv = Decimal(str(a["value"])), Decimal(str(b["value"]))
    scale = max(av, bv)
    # Two independent source measures share a true zero baseline and the same
    # maximum. Do not infer increase/decrease or fabricate a percentage.
    ents = []
    for idx, (q, val, beat) in enumerate(((a, av, prev), (b, bv, current)), 1):
        label = _bar_label(beat, q)
        # Retain the exact source numeric datum; no approximation or suffix.
        val_text = format(val, ",f").rstrip("0").rstrip(".") if "." in format(val, "f") else format(val, ",f")
        label = (label + " " + val_text).strip()
        ents.append({"id": f"director_bar_{idx}", "kind": "evidence",
                     "glyph": "BAR", "size": "support", "label": label,
                     "params": {"level": float(val / scale), "value": float(val)}})
    token = current["narration"].split()[0]
    cue = str(b.get("anchor") or token)
    current["illustration"] = {
        "form": "DATA_VISUAL", "entities": ents, "relations": [],
        "program": [
            {"op": "DRAW", "target": ents[0]["id"], "at": {"word": token}, "duration_ms": 220},
            {"op": "GROW", "target": ents[0]["id"], "at": {"word": token},
             "duration_ms": 380, "to": ents[0]["params"]["level"]},
            {"op": "DRAW", "target": ents[1]["id"], "at": {"word": cue}, "duration_ms": 220},
            {"op": "GROW", "target": ents[1]["id"], "at": {"word": cue},
             "duration_ms": 360, "to": ents[1]["params"]["level"]},
            {"op": "INK", "target": ents[1]["id"], "at": {"word": cue}, "duration_ms": 300},
        ], "confirmation": False}
    current.pop("data", None)
    current["dominant_layer"] = "HYBRID"
    # Retain provenance in the authored treatment for audits; the native
    # compiler only uses its recognized fields and never changes source words.
    current["director_evidence"] = [
        {"beat_id": prev["beat_id"], "source": a["source"], "value": a["value"], "unit": a.get("unit", "")},
        {"beat_id": current["beat_id"], "source": b["source"], "value": b["value"], "unit": b.get("unit", "")}]
    return True


def _subset(prev: dict, current: dict) -> bool:
    if not _subset_eligible(prev, current):
        return False
    whole, part = _quantity(prev), _quantity(current)
    a, b = Decimal(str(whole["value"])), Decimal(str(part["value"]))
    token = current["narration"].split()[0]
    cue = str(part.get("anchor") or token)
    # Original population is the denominator: only the *actual* share grows.
    # Source values remain discrete integers; no invented percentage or cases.
    number_text = format(a, ",.0f")
    current["illustration"] = {
        "form": "OBJECT_STAGE", "entities": [{
            "id": "director_population_subset", "kind": "evidence",
            "glyph": "DONUT", "size": "hero",
            "label": "out of " + number_text,
            "params": {"level": float(b / a), "count": int(b)}}],
        "relations": [],
        "program": [
            {"op": "DRAW", "target": "director_population_subset",
             "at": {"word": token}, "duration_ms": 260},
            {"op": "GROW", "target": "director_population_subset",
             "at": {"word": cue}, "duration_ms": 480,
             "to": float(b / a)},
            {"op": "COUNT", "target": "director_population_subset",
             "at": {"word": cue}, "duration_ms": 460}],
        "confirmation": False}
    current.pop("data", None)
    current["dominant_layer"] = "HYBRID"
    current["director_evidence"] = [
        {"beat_id": prev["beat_id"], "source": whole["source"], "value": whole["value"], "unit": whole.get("unit", "")},
        {"beat_id": current["beat_id"], "source": part["source"], "value": part["value"], "unit": part.get("unit", "")}]
    return True


def build_explanation_map(beats: list[dict]) -> dict[str, Any]:
    """Auditable full-film claim chain. No paraphrased or invented thesis."""
    nodes = []
    edges = []
    for i, beat in enumerate(beats):
        terms = sorted(_terms(beat["narration"]))
        relations = (beat.get("illustration") or {}).get("relations") or []
        nodes.append({"beat_id": beat["beat_id"], "claim": beat["narration"],
                      "terms": terms,
                      "quantities": [{"source": q["source"], "value": q["value"],
                                      "unit": q.get("unit", "")} for q in _measures(beat)],
                      "relations": [{"source": r["source"], "target": r["target"],
                                     "type": r["type"]} for r in relations]})
        for old in nodes[max(0, i-3):i]:
            common = sorted(set(terms) & set(old["terms"]))
            if common:
                edges.append({"from": old["beat_id"], "to": beat["beat_id"],
                              "type": "source_term_recurrence", "terms": common[:8]})
    return {"opening_claim": nodes[0]["claim"] if nodes else "",
            "closing_claim": nodes[-1]["claim"] if nodes else "",
            "claims": nodes, "connections": edges}


def direct_film(style: str, beats: list[dict]) -> dict[str, Any]:
    """Apply a cross-beat film plan through the existing renderer contract."""
    plan = plan_film(style, beats)
    entries = []
    for i, (beat, selected) in enumerate(zip(beats, plan)):
        family = selected.family
        # Existing cinema patterns and beat types are native contract values.
        if family in ("evidence_compare", "contrast", "evidence_bridge"):
            beat["pattern"] = "CONTRAST_RECONFIGURATION"
            if i not in (0, len(beats) - 1):
                beat["beat_type"] = "CONTRAST"
        elif family == "mechanism":
            beat["pattern"] = "PROCESS_RAIL"
        elif family in ("evidence_trend", "part_to_whole", "subset_explanation", "population_subset"):
            beat["pattern"] = "HERO_TO_EVIDENCE_HANDOFF"
            if i not in (0, len(beats) - 1):
                beat["beat_type"] = "PROOF"
        elif family in ("resolve",):
            beat["pattern"] = "PAYOFF_LOCKUP"
        elif family in ("evidence_stat", "evidence_in_context"):
            beat["pattern"] = "WORD_OBJECT_BRIDGE"
        elif family == "physical_stage":
            beat["pattern"] = "OBJECT_LED_TRANSITION"
        elif family == "editorial_reveal":
            beat["pattern"] = "PROGRESSIVE_HERO_BUILD"
        if family == "evidence_bridge" and i:
            _bridge(beats[i-1], beat)
        if family == "population_subset" and i:
            _subset(beats[i-1], beat)
        entries.append({
            "beat_id": beat["beat_id"], "family": family,
            "evidence": list(selected.evidence),
            "source_beat_ids": [e["beat_id"] for e in beat.get("director_evidence", [])],
            "form": (beat.get("illustration") or {}).get("form")})
    return {"version": "SCENEBAM_FILM_DIRECTOR_V1", "style": style,
            "scenes": entries, "global_lookahead": len(beats),
            "explanation_map": build_explanation_map(beats),
            "source_integrity": "verbatim_narration_and_source_tracked_quantities"}
