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
    if not re.search(r"\b(only|just|merely|out of|subset|a fraction of)\b", narration, re.I):
        return False
    if not re.search(r"\b(inside|among|within|of those|of these|of them|of that group|of the group|in that group|out of|population|subset)\b", narration, re.I):
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
    # Comparing coffee sales with muffin sales is NOT a part/whole inference,
    # even when both sentences mention the same shop. Require the explicitly
    # counted population noun to recur inside the proposed subset scene.
    group_label = str(a.get("label") or "").lower()
    counted_nouns = {w for w in re.findall(r"[a-z]+", group_label)
                     if len(w) > 3 and (w not in _STOP or w in ("people", "person"))}
    mentioned = set(re.findall(r"[a-z]+", narration.lower()))
    # Explicit "of those are..." is a reference to the most recently
    # introduced count. Require the copula immediately after the pronoun;
    # "of those muffins" is NOT an automatic reference to prior coffee.
    anaphora = re.search(
        r"\bof\s+(?:those|these|them)\s+(?:are|were|is|was|have|had)\b",
        narration, re.I)
    if anaphora:
        return True
    if not counted_nouns or not (counted_nouns & mentioned):
        return False
    return bool(_terms(prev["narration"]) & _terms(narration))


def _mature_sketch_action(beat: dict) -> bool:
    """A real native acted relationship outranks replacement by text widgets.

    This is a conservative evidence gate, not a hardcoded subject/story list:
    require at least TWO independently picturable source objects and a real
    relational physical operation addressed to the source graph. Two word
    pills connected by a line are not a mature illustrated performance.
    """
    il = beat.get("illustration") or {}
    entities = il.get("entities") or []
    if len(entities) < 2:
        return False
    picturable = {
        e.get("id") for e in entities
        if e.get("asset_ref") or e.get("media_ref") or
        e.get("glyph") in ("PUMP", "TANK", "VESSEL") or
        (e.get("params") or {}).get("visual_class") in (
            "document", "list", "package", "population")
    }
    if len(picturable) < 2:
        return False
    relations = {
        (r.get("source"), r.get("target"))
        for r in (il.get("relations") or [])
        if r.get("source") in picturable and r.get("target") in picturable
    }
    if not relations:
        return False
    ops = il.get("program") or []
    return any(
        op.get("op") in ("CONNECT", "TRAVEL", "SWAP", "EMIT")
        for op in ops
    )


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
            whole, part = Decimal(str(a["value"])), Decimal(str(b["value"]))
            exact_grid = (whole >= 100 and whole % 100 == 0
                          and (part * 100) % whole == 0)
            ans.append(Opportunity("population_grid" if exact_grid else "population_subset",
                                   1.55 if exact_grid else 1.48,
                                   (a["source"], b["source"])))
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
    # Native graphical recipes outrank generic word staging ONLY when the
    # source supplies all their entities, values and narrative conditions.
    # No fabricated nouns, numbered scenes, or per-topic exception tables.
    from scene_repertoire import candidates as executable_candidates
    native_acted_story = style == "sketch" and _mature_sketch_action(beat)
    # A label-only step diagram, versus card or magnifier must NEVER replace
    # the original acted story when the legacy author already supplies
    # multiple drawable entities connected by meaningful native motion.
    # Retain the candidate on weaker/unillustrated source scenes, where it
    # can genuinely improve explanation. This decision is script-agnostic.
    reductive_overrides = {
        "spoken_process", "verbal_versus", "editorial_magnification"
    }
    ans.extend(Opportunity(family, score, evidence)
               for family, score, evidence in executable_candidates(style, beat)
               if not (native_acted_story and family in reductive_overrides))
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
    # A crowd deserves a population depiction, not an automatic donut.
    # 100 graphical cells must be integer-exact; nondivisible source ratios
    # remain true proportions in the existing DONUT renderer.
    exact_grid = (a >= 100 and a % 100 == 0 and (b * 100) % a == 0)
    glyph = "POPULATION_GRID" if exact_grid else "DONUT"
    population_params = ({"total": int(a), "part": int(b),
                          "level": float(b / a), "count": int(b)}
                         if exact_grid else {"level": float(b / a), "count": int(b)})
    current["illustration"] = {
        "form": "OBJECT_STAGE", "entities": [{
            "id": "director_population_subset", "kind": "evidence",
            "glyph": glyph, "size": "hero",
            **({} if exact_grid else {"label": "of " + number_text}),
            "params": population_params}],
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


def direct_scene_positions(style: str, beats: list[dict],
                           plan: list[Opportunity]) -> list[dict[str, str]]:
    """Choose a film-wide *spatial* grammar with aspect-native reading order.

    Distinct scene intent drives positions: dense evidence earns the dominant
    canvas before its annotation; causal/process stories usually introduce the
    text first. A global beam balances clarity with visual repetition. It
    does not assign placement by script topic, fixed beat index, or template ID.
    """
    if not beats:
        return []
    result = [{} for _ in beats]
    proof = {"evidence_compare", "evidence_bridge", "evidence_trend",
             "part_to_whole", "population_subset", "population_grid",
             "categorical_columns", "categorical_table", "completion_meter",
             "milestone_timeline"}
    mechanism = {"mechanism", "spoken_process", "physical_stage",
                 "highlighted_subject", "negated_subject"}
    def needs_wide_evidence(b: dict) -> bool:
        il = b.get("illustration") or {}
        entities = il.get("entities") or []
        # Three+ physical subjects / connectors cannot be compressed to one
        # half of a landscape canvas without losing their nouns and motion.
        # Keep full-width story space for dense *graph topology*, not only
        # numeric trend lines. Two-object portraits can still alternate
        # text-left and text-right.
        if len(entities) >= 3 and il.get("form") in (
                "PROCESS_PIPELINE", "RELATIONSHIP", "STATE_TRANSFORMATION",
                "COMPARISON"):
            return True
        for entity in entities:
            g = entity.get("glyph")
            params = entity.get("params") or {}
            if (g == "CHART_LINE" and len(params.get("points") or []) >= 5 or
                g == "DATA_BARS" and len(params.get("series") or []) >= 5 or
                g == "DATA_TABLE" and len(params.get("rows") or []) >= 5 or
                g == "TIMELINE" and len(params.get("events") or []) >= 5):
                return True
        return False

    for aspect in ("1x1", "9x16", "16x9"):
        names = ("TEXT_LEFT", "TEXT_RIGHT") if aspect == "16x9" else ("TEXT_TOP", "TEXT_BOTTOM")
        wide = {i for i,b in enumerate(beats) if aspect == "16x9" and
                needs_wide_evidence(b)}
        beam = [(0.0, ())]
        for i, (b, p) in enumerate(zip(beats, plan)):
            if not b.get("illustration") or i in wide:
                # The authored source has no independent evidence layer:
                # preserve its native typography-only composition.
                continue
            words = len(b["narration"].split())
            new = []
            for score, path in beam:
                for side in names:
                    text_first = side in ("TEXT_LEFT", "TEXT_TOP")
                    value = .0
                    if p.family in proof:
                        value += (.36 if not text_first else -.12)
                    if p.family in mechanism:
                        value += (.40 if text_first else -.08)
                    if p.family in ("resolve", "editorial_reveal",
                                    "editorial_magnification"):
                        value += (.17 if text_first else .08)
                    if words >= 19:
                        value += (.17 if text_first else 0)
                    if p.family in ("population_grid", "evidence_trend"):
                        value += (.26 if not text_first else 0)
                    if path and path[-1] == side:
                        value -= .27
                    if len(path) >= 2 and path[-1] == path[-2] == side:
                        value -= .38
                    if i > 0 and b.get("illustration", {}).get("carry"):
                        # The same evidence does not teleport across a
                        # continuing scene. Reuse its prior placement.
                        if path and path[-1] != side:
                            value -= 3.0
                    new.append((score+value, path+(side,)))
            beam = sorted(new, key=lambda entry:(-entry[0], entry[1]))[:14]
        active = [i for i,b in enumerate(beats)
                  if b.get("illustration") and i not in wide]
        sides = beam[0][1]
        for i, side in zip(active, sides):
            result[i][aspect] = side
        for i in wide:
            result[i][aspect] = "EVIDENCE_WIDE"
    return result


def restore_kinetic_hierarchy(beat: dict) -> None:
    """Restage an unbroken sentence as differently weighted spoken thoughts.

    No subtitles, no per-script templates, no rewritten narration. Reintroduce
    support-vs-hero typographic contrast with word-level entrances. The former
    12+-word single-hero block caused the same two large lines in every scene.
    Keep established multi-unit explanations (trends / process) unchanged.
    """
    units = beat.get("display_units") or []
    if len(units) != 1 or units[0].get("role") != "hero":
        return
    words = beat["narration"].split()
    n = len(words)
    if n < 9:
        return
    # Keep the number of display units low enough to preserve native readable
    # type size; support/hero size differentiation does the editorial work.
    lo, hi = max(3, int(n * .30)), min(n - 3, int(n * .68))
    if lo > hi:
        return
    cue = re.compile(r"^(?:because|although|however|whereas|while|before|after|"
                     r"therefore|instead|but|yet|so|then|which|when|to)$", re.I)
    natural = [(abs(k - n * .50), k) for k in range(lo, hi+1)
               if cue.fullmatch(words[k].strip(".,;:!?")) or
               words[k-1].endswith((",", ";", ":"))]
    cut = min(natural)[1] if natural else min(hi, max(lo, n//2))
    first, second = words[:cut], words[cut:]
    if not first or not second:
        return
    # Promote the source's central actionable claim, not incidental sentence
    # fragments. Early negations/actions, or an early measurement, are heroes;
    # otherwise setup leads to the eventual narrated finding.
    early = " ".join(first).lower()
    early_action = bool(re.search(r"\b(never|do not|avoid|circle|highlight|"
                                  r"send|sends|carry|carries|connect|connects|"
                                  r"transfer|transfers|look closely|zoom|inspect)\b", early))
    early_number = any(re.search(r"\d", w) for w in first)
    later_number = any(re.search(r"\d", w) for w in second)
    hero_first = (early_action or early_number) and not later_number
    new = []
    for i, phrase in enumerate((first, second)):
        hero = (i == 0) if hero_first else (i == 1)
        new.append({
            "text": " ".join(phrase),
            "role": "hero" if hero else "support",
            "anchor_word": phrase[0],
            "emphasis": .94 if hero else .52,
            "semantic_role": "punch" if hero else "setup",
            "can_promote": hero, "reveal": "WORD_CASCADE",
            "stress": [w for w in phrase if re.search(r"\d",w)]})
    if " ".join(u["text"] for u in new) == beat["narration"]:
        beat["display_units"] = new


def direct_spoken_stat_typography(beat: dict) -> None:
    """Small narrated lead-in -> large source measurement, timed independently.

    A seven-word sentence should not always become two uniform full-width
    rows. Give the meaning-carrying numerical assertion the typographic
    emphasis, on the same exact source word that animates the numeric graphic.
    Neither audio nor authored wording is replaced or shortened.
    """
    units = beat.get("display_units") or []
    measures = _measures(beat)
    if len(units) != 1 or len(measures) != 1 or units[0].get("role") != "hero":
        return
    words = beat["narration"].split()
    q = measures[0]
    idx = q.get("word_start")
    if not isinstance(idx, int) or not (2 <= idx <= min(7,len(words)-2)):
        return
    if not (5 <= len(words) <= 11):
        return
    # Approximate or negated values should retain the original grammatical
    # qualifier rather than receive a false precise-stat punch.
    if q.get("qualifier") or q.get("signed"):
        return
    first, second = words[:idx], words[idx:]
    if not first or not second:
        return
    new = [
        {"text": " ".join(first), "role": "support",
         "anchor_word": first[0], "emphasis": .48,
         "semantic_role": "setup", "can_promote": False,
         "reveal": "WORD_CASCADE", "stress": []},
        {"text": " ".join(second), "role": "hero",
         "anchor_word": second[0], "emphasis": .96,
         "semantic_role": "proof", "can_promote": True,
         "reveal": "WORD_CASCADE",
         "stress": [second[0]]}]
    if " ".join(u["text"] for u in new) == beat["narration"]:
        beat["display_units"] = new


def time_subject_arrivals(beat: dict) -> None:
    """Use the original source noun as the entry cue for drawn actors/objects.

    Existing generic Sketch stage creators previously DRAW every person and
    prop on the first word; relations might animate later, but the film had
    already shown the complete scene. Preserve explicit transformation and
    carry programs; only retime the generic early DRAW entrance for newly
    introduced standalone objects.
    """
    il = beat.get("illustration") or {}
    # A continuing Sketch scene may retain two figures while introducing a
    # THIRD character. Never retime the carried bodies, but the new participant
    # still belongs to the spoken noun rather than the beginning of the cut.
    carried = set((il.get("carry") or {}).get("entities") or [])
    narration = beat["narration"]
    for ent in il.get("entities") or []:
        if ent.get("id") in carried or ent.get("kind") not in ("object", "agent"):
            continue
        phrase = str(ent.get("phrase") or ent.get("label") or "")
        if not phrase:
            continue
        m = re.search(r"\b" + re.escape(phrase) + r"\b", narration, re.I)
        if not m:
            continue
        # Anchors are guaranteed verbatim tokens in the narration, not
        # semantic guesses: e.g. 'driver' enters on DRIVER, not 'The'.
        word = narration[m.start():m.end()].split()[0]
        # The native compiler schedules operations in authoring order, NOT
        # necessarily word order. If a recurring noun's DRAW follows a later
        # source object, a plain word anchor can silently bind to its SECOND
        # occurrence (e.g. first "Pollen" appears at 0.1s, yet its sprite
        # was arriving at 3.3s). The documented native word_index contract
        # pins the initial drawing to the EXACT first source occurrence.
        first_index = len(narration[:m.start()].split())
        narration_words = narration.split()
        exact_source_index = (
            first_index < len(narration_words) and
            re.sub(r"[^a-z0-9%]", "", word.lower()) ==
            re.sub(r"[^a-z0-9%]", "", narration_words[first_index].lower())
        )
        for op in il.get("program") or []:
            if op.get("op") == "DRAW" and op.get("target") == ent.get("id"):
                op["at"] = {"word": word}
                if exact_source_index:
                    op.setdefault("params", {})["word_index"] = first_index
                op["duration_ms"] = max(280, min(560, int(op.get("duration_ms", 480))))
                # The compiler's old scheduling put EVERY new object on stage
                # inside the lead-in, long before its source noun was spoken.
                # Mark genuinely sourced DRAWs for voice-governed arrival.
                ent.setdefault("params", {})["voice_cued"] = True


def _sketch_has_meaningful_visual(beat: dict) -> bool:
    """No typography-only card can masquerade as a Sketch scene.

    Words inside shapes are not pictorial evidence. Genuine drawing, a
    timed relation with at least two source endpoints, or a voice-built
    evidence diagram counts. An unillustratable claim must be replanned,
    not supplied a false person, object, or decorative fake.
    """
    il = beat.get("illustration") or {}
    entities = il.get("entities") or []
    if not entities:
        return False
    graphic_glyphs = {
        "VESSEL", "PUMP", "TANK", "ICON", "MEDIA", "CHART_LINE",
        "RING", "BAR", "DONUT", "PROGRESS", "POPULATION_GRID", "BASE10_TALLY",
        "DATA_BARS", "DATA_TABLE", "TIMELINE", "FLOW_STEPS",
        "SQUIGGLE",
        # Text inside a magnifier or VS monogram cards is NOT a physical
        # drawing. Those styles may exist in Data Viz, but cannot satisfy the
        # strict no-text-only Sketch illustration obligation.
    }
    for e in entities:
        if e.get("asset_ref") or e.get("media_ref"):
            return True
        if (e.get("params") or {}).get("visual_class"):
            return True
        if e.get("glyph") in graphic_glyphs:
            return True
    relation_ids = {e.get("id") for e in entities}
    if (len(relation_ids) >= 2 and any(
        r.get("source") in relation_ids and r.get("target") in relation_ids
        for r in (il.get("relations") or [])
    ) and any(op.get("op") in ("CONNECT", "TRAVEL", "SWAP")
              for op in il.get("program") or [])):
        return True
    return False


def direct_film(style: str, beats: list[dict]) -> dict[str, Any]:
    """Apply a cross-beat film plan through the existing renderer contract."""
    plan = plan_film(style, beats)
    entries = []
    for i, (beat, selected) in enumerate(zip(beats, plan)):
        family = selected.family
        from scene_repertoire import realize as realize_scene
        realized = realize_scene(family, beat, style=style)
        # Existing cinema patterns and beat types are native contract values.
        if family in ("evidence_compare", "contrast", "evidence_bridge"):
            beat["pattern"] = "CONTRAST_RECONFIGURATION"
            if i not in (0, len(beats) - 1):
                beat["beat_type"] = "CONTRAST"
        elif family == "mechanism":
            beat["pattern"] = "PROCESS_RAIL"
        elif family in ("evidence_trend", "part_to_whole", "subset_explanation", "population_subset", "population_grid"):
            beat["pattern"] = "HERO_TO_EVIDENCE_HANDOFF"
            if i not in (0, len(beats) - 1):
                beat["beat_type"] = "PROOF"
        elif family in ("resolve",):
            beat["pattern"] = "PAYOFF_LOCKUP"
        elif family in ("evidence_stat", "evidence_in_context"):
            beat["pattern"] = "WORD_OBJECT_BRIDGE"
        elif family == "physical_stage":
            beat["pattern"] = "OBJECT_LED_TRANSITION"
        elif realized:
            # Each realised family has a genuinely different native diagram
            # program, not a decorative alias of the former object stage.
            beat["pattern"] = ("PROCESS_RAIL" if family == "spoken_process"
                               else "CONTRAST_RECONFIGURATION" if family == "verbal_versus"
                               else "HERO_TO_EVIDENCE_HANDOFF")
            if i not in (0, len(beats)-1):
                beat["beat_type"] = "PROOF"
        elif family == "editorial_reveal":
            beat["pattern"] = "PROGRESSIVE_HERO_BUILD"
        if family == "evidence_bridge" and i:
            _bridge(beats[i-1], beat)
        if family in ("population_subset", "population_grid") and i:
            _subset(beats[i-1], beat)
        if style in ("sketch", "dataviz"):
            if style == "dataviz":
                direct_spoken_stat_typography(beat)
            restore_kinetic_hierarchy(beat)
            # A spoken noun/measurement is the timing authority for both the
            # kinetic sentence and its scene's state changes. Compiler may
            # shorten an overlong effect but must NEVER move it earlier than
            # that source word to satisfy a synthetic end-of-beat hold.
            for cue in (beat.get("illustration") or {}).get("program") or []:
                if "word" in (cue.get("at") or {}):
                    cue.setdefault("params", {})["voice_sync"] = True
        if style == "sketch":
            from sketch_actor_states import ensure_source_count_visual
            # Whiteboard cast is the ONLY authorized actor source. The earlier
            # source-person SVG and sketch_actor_states SETTLE adapter are a
            # separate stand-in, not the real Whiteboard/NexStick runtime.
            # Fail closed until a source-backed Whiteboard adapter is genuinely
            # integrated and tested. Never silently draw this generic actor.
            synthetic_people = [
                ent.get("id", "<unknown>")
                for ent in (beat.get("illustration") or {}).get("entities", [])
                if ((ent.get("params") or {}).get("visual_class") == "person" or
                    (ent.get("params") or {}).get("actor_identity") or
                    (ent.get("params") or {}).get("actor_state"))
            ]
            if synthetic_people:
                raise RuntimeError(
                    "SCENEBAM_WHITEBOARD_CHARACTER_INTEGRATION_REQUIRED: "
                    "Sketch refused unapproved procedural person(s) "
                    + ", ".join(synthetic_people)
                    + "; supply an authenticated native Whiteboard cast bridge "
                    "before rendering actors. No substitute character allowed."
                )
            # Retain non-human source-grounded drawing and data choreography.
            if not _sketch_has_meaningful_visual(beat):
                ensure_source_count_visual(beat)
            time_subject_arrivals(beat)
            actor_actions = []
        else:
            actor_actions = []
        entries.append({
            "beat_id": beat["beat_id"], "family": family,
            "evidence": list(selected.evidence),
            "source_beat_ids": [e["beat_id"] for e in beat.get("director_evidence", [])],
            "form": (beat.get("illustration") or {}).get("form"),
            "actor_actions": actor_actions})
    text_only = []
    if style == "sketch":
        text_only = [b["beat_id"] for b in beats
                     if not _sketch_has_meaningful_visual(b)]
        for beat in beats:
            # Film authoring remains inspectable; the compiler's real render
            # quality gate refuses missing visual subjects. This is neither
            # a pass nor a silent text-card fallback.
            beat.setdefault("features", {})["sketch_visual_coverage"] = (
                0.0 if beat["beat_id"] in text_only else 1.0)
    # Realization must precede composition: the chosen repertoire family
    # can replace an initial generic illustration with a new evidence scene.
    positions = direct_scene_positions(style, beats, plan)
    for beat, entry, layout in zip(beats, entries, positions):
        if layout:
            beat["director_layout"] = layout
            entry["director_layout"] = layout
    return {"version": "SCENEBAM_FILM_DIRECTOR_V1", "style": style,
            "scenes": entries, "global_lookahead": len(beats),
            "explanation_map": build_explanation_map(beats),
            "source_integrity": "verbatim_narration_and_source_tracked_quantities",
            "sketch_visual_coverage_failures": text_only}
