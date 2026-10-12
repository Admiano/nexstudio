"""Contract-only technical preflight, not perceptual judging or creative authority.

No providers, renderer, assets, fixtures or fallback implementations are invoked.
Findings identify a causal owner and a bounded *proposal* for local repair; this
module never rewrites an accepted score. Signatures intentionally omit wording,
actor IDs, evidence quantities and role colours, retaining the executable graph.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
import unicodedata
from typing import Any

from .contracts import (
    ASPECTS, PLAN_SCHEMA, SCORE_SCHEMA, UNIT_TABLE, ScoreError,
    resolve_word_cue, validate_plan, validate_score,
)

AUDIT_SCHEMA = "explainer-direction.audit/v1"
SIGNATURE_SCHEMA = "explainer-direction.structure/v1"
_LIMITATIONS = [
    "Technical and structural checks are not independent native audio/visual review, human calibration, public shipping approval or Creative Lock.",
    "Source rights, factual entailment, model/audio authenticity and P8 state/board hashes require external verification; declarations are not proof.",
    "Text width and visibility checks are conservative geometry estimates, not measured font rasterization or encoded-frame perceptual evidence.",
    "A single plan cannot prove native reflow across aspects or runtime backward-seek fidelity; audit_aspects compares submitted contract plans only.",
]


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _finding(report, code, severity, owner, path, message, *, scene=None,
             actors=(), events=(), observed=None, hint="Inspect only the implicated decision."):
    item = {
        "code": code, "severity": severity, "causal_owner": owner, "path": path,
        "message": message, "scene_id": scene, "actor_ids": sorted(set(actors)),
        "event_ids": sorted(set(events)), "observed": deepcopy(observed or {}),
        "repair": {"scope": "bounded_local", "paths": [path], "hint": hint,
                   "preserve_unaffected_decisions": True, "requires_p8_commit": True},
    }
    item["id"] = "finding_" + _hash(item)[:16]
    report["findings"].append(item)


def _new_report(kind):
    return {"schema": AUDIT_SCHEMA, "kind": kind, "film_id": None,
            "status": "fail", "technical_pass": False, "findings": [],
            "scene_signatures": [], "film_signature": None,
            "authority": {"creative_authority": "P8", "certification": "NOT_CERTIFIED",
                          "creative_lock": False, "external_review_required": True},
            "limitations": list(_LIMITATIONS)}


def _finish(report):
    counts = Counter(f["severity"] for f in report["findings"])
    report["counts"] = {key: counts[key] for key in ("error", "warning", "info")}
    report["technical_pass"] = not counts["error"]
    report["status"] = "fail" if counts["error"] else "warnings" if counts["warning"] else "pass"
    return report


def _contract_issue(error):
    """Route by cause, never infer Story ownership from scene/beat metadata."""
    message = str(error).lower()
    if "position must lower into both x/y" in message:
        return "POSITION_TRACK_PAIR_MISSING", "Storyboard Compiler"
    if any(word in message for word in ("retained", "retention", "identity", "terminal state")):
        return "RETAINED_IDENTITY_INVALID", "Motion / Performance Director"
    if any(word in message for word in ("commercial", "license", "source", "provenance", "raster", "image src", "local font")):
        return "PROVENANCE_INVALID", "Art Director / Source Intelligence"
    if any(word in message for word in ("alignment", "word cue", "reported timing")):
        return "ALIGNMENT_INVALID", "Sound Direction / Alignment Integration"
    if any(word in message for word in ("geometry", "canvas", "orientation", "transition", "contiguous")):
        return "PLAN_BINDING_INVALID", "Storyboard Compiler"
    if any(word in message for word in ("quantity", "numerical", "numeric", "comparison", "dimension", "unit", "value binding", "value_binding", "bound evidence", "unbound")):
        return "EVIDENCE_BINDING_INVALID", "Source Intelligence / Story Director"
    if any(word in message for word in ("track", "event", "dependency", "dependencies", "property", "animated", "easing", "verb", "hold", "change map", "writes")):
        return "EVENT_MECHANISM_INVALID", "Motion / Performance Director"
    if any(word in message for word in ("authority", "p8", "creative_locked")):
        return "AUTHORITY_INVALID", "P8 Integration"
    return "CONTRACT_INVALID", "Execution Contract Adapter"


def _validated(document, validator, report):
    try:
        return validator(document)
    except ScoreError as error:
        code, owner = _contract_issue(error)
        _finding(report, code, "error", owner, error.path, str(error),
                 hint="Repair this contract violation in place. Unsupported intent must fail/replan; never replace it with a still card or fixture.")
        return None


def _direction(before, after, prop):
    if before == after:
        return "same"
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return "increase" if after > before else "decrease"
    # Text wording, selection names and shape variants do not hide choreography.
    return "change" if prop in ("text", "selection", "position") else [before, after]


def _representation(actor):
    payload, kind = actor["payload"], actor["kind"]
    out = {"kind": kind}
    if kind == "text":
        out.update(purpose=payload["purpose"], numeric_role=payload.get("numeric_role"))
    elif kind == "shape":
        out["shape"] = payload["shape"]
    # Pixel orientation can be a native lowering of auto; semantic layout/flow
    # carries composition rather than making aspect resolution hide repetition.
    elif kind == "particles":
        out.update(arrangement=payload["arrangement"], count=payload["count"])
    elif kind == "selector":
        out["options"] = len(payload["options"])
    elif kind == "image":
        out["fit"] = payload["fit"]
    return out


def _scene_structure(scene):
    """ID/order-independent coloured graph refinement (not graph-isomorphism proof)."""
    nodes, edges = {}, []
    actors = {a["id"]: a for a in scene["actors"]}
    duration = scene.get("duration_ms", scene.get("end_ms", 0) - scene.get("start_ms", 0))
    focus = scene.get("composition", {}).get("focus")
    for actor in actors.values():
        key = "actor:" + actor["id"]
        layout = actor["layout"]
        nodes[key] = {"representation": _representation(actor),
                      "layout": {k: layout[k] for k in ("anchor", "rank", "arrangement") if k in layout},
                      "focus": actor["id"] == focus,
                      "state_properties": sorted((set(actor["initial"]) - {"x", "y"}) | {"position"})}
        if "relative_to" in layout:
            edges.append((key, "layout_relative", "actor:" + layout["relative_to"]))
        if actor["kind"] == "group":
            edges.extend((key, "group_child", "actor:" + c) for c in actor["payload"]["children"])
        if actor["kind"] == "connector":
            for endpoint in ("from", "to"):
                edges.append((key, "connector_" + endpoint, "actor:" + actor["payload"][endpoint]))
    for relation in scene["relations"]:
        kind, first, second = relation["kind"], relation["from"], relation["to"]
        if kind in ("below", "right_of"):
            kind = {"below": "above", "right_of": "left_of"}[kind]
            first, second = second, first
        edges.append(("actor:" + first, "relation:" + kind, "actor:" + second))
    states = {aid: deepcopy(a["initial"]) for aid, a in actors.items()}
    event_nodes = {}
    tracks = defaultdict(list)
    for track in scene.get("tracks", []):
        tracks[track["event_id"]].append(track)
    for event in scene["events"]:
        key = "event:" + event["id"]
        cue = event.get("cue", {})
        if "start_ms" in event:
            phase = round((event["start_ms"] - scene["start_ms"]) / duration, 1)
            length = event["end_ms"] - event["start_ms"]
        else:
            phase = round(cue.get("fraction", cue.get("ms", cue.get("resolved_ms", 0)) / duration), 1) if cue["kind"] != "word" else "word"
            length = event["duration_ms"]
        event_nodes[key] = {"verb": event["verb"], "phase": phase, "duration_fraction": round(length / duration, 1)}
        edges.extend((key, "depends", "event:" + dep) for dep in event["dependencies"])
        if "changes" in event:
            for target, changes in event["changes"].items():
                pattern = [(p, _direction(states[target][p], v, p), "step" if p in ("text", "variant", "selection") else event["easing"]) for p, v in sorted(changes.items())]
                edges.append((key, "changes:" + json.dumps(pattern, sort_keys=True), "actor:" + target))
                states[target].update(changes)
        else:
            by_target = defaultdict(list)
            for track in tracks[event["id"]]:
                by_target[track["actor_id"]].append(track)
            for target, target_tracks in by_target.items():
                pattern = [(t["property"], _direction(t["from"], t["to"], t["property"]), t["easing"]) for t in target_tracks if t["property"] not in ("x", "y")]
                positions = [t for t in target_tracks if t["property"] in ("x", "y")]
                if positions:
                    pattern.append(("position", "change" if any(t["from"] != t["to"] for t in positions) else "same", positions[0]["easing"]))
                edges.append((key, "changes:" + json.dumps(sorted(pattern), sort_keys=True), "actor:" + target))
        if event["verb"] == "hold":
            edges.extend((key, "holds", "actor:" + t) for t in event["targets"])
    nodes.update(event_nodes)
    colours = {key: _hash(value) for key, value in nodes.items()}
    adjacent = defaultdict(list)
    for source, relation, target in edges:
        adjacent[source].append(("out", relation, target))
        adjacent[target].append(("in", relation, source))
    for _ in range(min(len(nodes), 8)):
        colours = {key: _hash([colours[key], sorted((direction, relation, colours[other]) for direction, relation, other in adjacent[key])]) for key in nodes}
    composition = scene.get("composition", {"flow": "auto", "density": "balanced"})
    return {"nodes": sorted(colours.values()),
            "edges": sorted((colours[s], label, colours[t]) for s, label, t in edges),
            "composition": {k: composition[k] for k in ("flow", "density")},
            "transition": {k: scene["transition"][k] for k in ("kind", "direction") if k in scene["transition"]}}


def structural_signature(scene):
    """Return an opaque structural fingerprint of a scene from a validated contract.

    Labels, palette, evidence values and IDs are excluded. Native pixel geometry
    is intentionally separate from the semantic composition signature. This is a
    repetition indicator, not a novelty/taste score or canonical-isomorphism test.
    """
    structure = _scene_structure(scene)
    return {"schema": SIGNATURE_SCHEMA, "digest": _hash(structure), "structure": structure}


def _signatures(document, report):
    sequence, previous_section = [], None
    previous_actors: set[str] = set()
    for scene in document["scenes"]:
        signature = structural_signature(scene)
        report["scene_signatures"].append({"scene_id": scene["id"], **signature})
        scene_actors = {a["id"] for a in scene["actors"]}
        sequence.append({"digest": signature["digest"], "section_boundary": scene["section_id"] != previous_section, "retained_actor_count": len(scene_actors & previous_actors)})
        previous_section = scene["section_id"]
        previous_actors.update(scene_actors)
    report["film_signature"] = {"schema": SIGNATURE_SCHEMA, "digest": _hash(sequence), "sequence": sequence}


def _intentional(scene):
    return bool(scene.get("motif")) or not scene["events"] or all(e["verb"] == "hold" for e in scene["events"])


def _repetition(document, report, history):
    groups = defaultdict(list)
    for i, signature in enumerate(report["scene_signatures"]):
        if not _intentional(document["scenes"][i]):
            groups[signature["digest"]].append(i)
    for indices in groups.values():
        if len(indices) >= 3:
            _finding(report, "SCENE_MONOTONY", "warning", "Visual Concept / Motion Director", "$.scenes",
                     "Several scenes reuse the same relation/composition/action structure; changed labels or colours are not variation.",
                     observed={"scene_ids": [document["scenes"][i]["id"] for i in indices]},
                     hint="Ask the owning P8 slot whether repetition is intentional. If not, vary only the implicated representation, relation, composition or action progression; preserve style and accepted evidence.")
    if history is None:
        return
    if not isinstance(history, (list, tuple)):
        _finding(report, "HISTORY_INVALID", "warning", "Creative Memory Adapter", "$.history", "History must be a list of validated scores/plans or prior audit reports.")
        return
    if len(history) > 50:
        _finding(report, "HISTORY_BOUNDED", "info", "Creative Memory Adapter", "$.history", "Only the most recent 50 history entries are compared.", observed={"provided": len(history)})
    for offset, entry in enumerate(history[-50:]):
        index = max(0, len(history) - 50) + offset
        path = f"$.history[{index}]"
        prior = None
        if isinstance(entry, dict) and entry.get("schema") in (SCORE_SCHEMA, PLAN_SCHEMA):
            try:
                prior_doc = (validate_score if entry["schema"] == SCORE_SCHEMA else validate_plan)(entry)
                prior = _new_report("history")
                _signatures(prior_doc, prior)
            except ScoreError:
                pass
        elif isinstance(entry, dict) and entry.get("schema") == AUDIT_SCHEMA and entry.get("technical_pass") is True:
            prior = entry
        def valid_digest(value):
            return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
        if not prior or not isinstance(prior.get("film_signature"), dict) or not valid_digest(prior["film_signature"].get("digest")) or not isinstance(prior.get("scene_signatures"), list) or not all(isinstance(s, dict) and valid_digest(s.get("digest")) for s in prior["scene_signatures"]):
            _finding(report, "HISTORY_INVALID", "warning", "Creative Memory Adapter", path, "History entry is not an accepted contract or technical audit signature; it was not treated as creative evidence.")
            continue
        if prior["film_signature"].get("digest") == report["film_signature"]["digest"] and not all(_intentional(s) for s in document["scenes"]):
            _finding(report, "FILM_TEMPLATE_REUSE", "warning", "Visual Concept Director / Creative Memory", "$.scenes",
                     "History contains the same ordered structural film signature despite any wording or palette changes.",
                     observed={"history_index": index, "digest": report["film_signature"]["digest"]},
                     hint="Keep accepted evidence/style; request a bounded P8 review of the reused choreography, or declare a genuine intentional motif with its reason.")
        else:
            digests = {s.get("digest") for s in prior["scene_signatures"] if isinstance(s, dict)}
            repeated = [s["id"] for s, sig in zip(document["scenes"], report["scene_signatures"]) if sig["digest"] in digests and not _intentional(s)]
            if repeated:
                _finding(report, "SCENE_HISTORY_REUSE", "warning", "Visual Concept Director / Creative Memory", "$.scenes",
                         "Some scenes repeat a historical semantic construction.", observed={"history_index": index, "scene_ids": repeated},
                         hint="Review only these repeated constructions; a recurring motif may be intentional and needs no forced replacement.")


def _provenance(document, report):
    provenance = document["provenance"]
    report["film_id"] = document["film_id"]
    report["authority"]["direction_status"] = provenance["status"]
    if provenance["mode"] == "development":
        _finding(report, "DEVELOPMENT_ONLY", "info", "P8 Integration", "$.provenance", "Standalone development/preflight evidence is not creative lock or P8 human calibration.")
    sources = [e["source"] for e in document["evidence"]] + [provenance["source"]]
    sources.extend(a["payload"]["source"] for s in document["scenes"] for a in s["actors"] if a["kind"] == "image")
    fixture_uris = [s["uri"] for s in sources if s["uri"].casefold().startswith(("test-fixture:", "fixture:", "synthetic:"))]
    model = provenance.get("model", {})
    fixture_model = any(token in (model.get("provider", "") + " " + model.get("model", "")).casefold() for token in ("test-fixture", "fixture-provider", "recordedmodelprovider"))
    if (fixture_uris or fixture_model) and not (provenance["mode"] == "development" and provenance.get("test_fixture") is True):
        _finding(report, "UNDECLARED_FIXTURE_OR_FALLBACK", "error", "Provider / P8 Integration", "$.provenance",
                 "Explicit fixture provenance cannot masquerade as live inference or P8-bound production.", observed={"fixture_sources": fixture_uris},
                 hint="Fail this live route. Declare test-only development fixtures honestly or supply actual configured inference/evidence; do not fabricate an output.")
    if provenance.get("test_fixture"):
        _finding(report, "TEST_FIXTURE_ONLY", "info", "Provider Integration", "$.provenance.test_fixture", "Declared fixture is functional QA only, never live production proof.")
    uncertain = [e["id"] for e in document["evidence"] if e["status"] == "uncertain"]
    if uncertain:
        _finding(report, "UNCERTAINTY_REVIEW_REQUIRED", "warning", "Story Director / Source Intelligence", "$.evidence", "Uncertain claims require explicit contextual framing and semantic review, not deterministic entailment certification.", observed={"evidence_ids": uncertain}, hint="Review only the uncertain claims and their narration/labels; preserve supported evidence.")


def _luminance(colour):
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in channels]
    return sum(x * weight for x, weight in zip(linear, (.2126, .7152, .0722)))


def _contrast(foreground, background):
    a, b = sorted((_luminance(foreground), _luminance(background)))
    return (b + .05) / (a + .05)


def _palette(document, report, compiled=False):
    palette = document["style"]["palette"]
    for i, scene in enumerate(document["scenes"]):
        actors = {a["id"]: a for a in scene["actors"]}
        for j, actor in enumerate(scene["actors"]):
            if actor["kind"] not in ("text", "number", "selector"):
                continue
            background_role = "background"
            relative = actors.get(actor["layout"].get("relative_to"))
            if relative and relative["kind"] == "panel":
                background_role = relative["role"]
            if compiled:
                g = actor["geometry"]
                center = (actor["initial"]["x"] + g["width"] / 2, actor["initial"]["y"] + g["height"] / 2)
                for panel in scene["actors"][:j]:
                    if panel["kind"] != "panel" or panel["initial"]["opacity"] < 1 or panel["initial"].get("fill", 1) < 1:
                        continue
                    pg = panel["geometry"]
                    if panel["initial"]["x"] <= center[0] <= panel["initial"]["x"] + pg["width"] and panel["initial"]["y"] <= center[1] <= panel["initial"]["y"] + pg["height"]:
                        background_role = panel["role"]
            size = actor.get("geometry", {}).get("font_size", document["style"]["typography"]["label_size"])
            required = 3 if size >= 24 else 4.5
            ratio = _contrast(palette[actor["role"]], palette[background_role])
            if ratio < required:
                _finding(report, "TEXT_PALETTE_CONTRAST", "warning", "Art Director", f"$.scenes[{i}].actors[{j}]",
                         "Declared text-role colour has low contrast against its contextual backing role; encoded frames still need review.", scene=scene["id"], actors=[actor["id"]],
                         observed={"role": actor["role"], "backing_role": background_role, "contrast_ratio": round(ratio, 3), "reference_minimum": required},
                         hint="Adjust only the implicated role/backing contrast or local text treatment through P8 Art; do not rotate the whole palette or change choreography.")


def _score_times(score, scene):
    alignment_scene = next((s for s in score.get("alignment", {}).get("scenes", []) if s["scene_id"] == scene["id"]), None)
    events = {e["id"]: e for e in scene["events"]}
    times: dict[str, tuple[float, float] | None] = {}
    def visit(eid):
        if eid in times:
            return times[eid]
        event, cue = events[eid], events[eid]["cue"]
        deps = [visit(d) for d in event["dependencies"]]
        if cue["kind"] == "fraction":
            start = cue["fraction"] * scene["duration_ms"]
        elif cue["kind"] == "absolute":
            start = cue["ms"]
        else:
            start = resolve_word_cue(cue, alignment_scene) if alignment_scene else None
        if start is None or any(d is None for d in deps):
            times[eid] = None
        else:
            begin = max([start] + [d[1] for d in deps])
            times[eid] = (begin, begin + event["duration_ms"])
        return times[eid]
    for eid in events:
        visit(eid)
    return times


def validate_observable_actions(score, scene_index):
    """Check declared action effects, not factual entailment or rendered quality."""
    document = validate_score(score)
    scene = document["scenes"][scene_index]
    actors = {a["id"]: a for a in scene["actors"]}
    times = _score_times(document, scene)
    if any(interval is None for interval in times.values()):
        return
    resolved = {eid: interval for eid, interval in times.items() if interval is not None}
    states = {aid: deepcopy(a["initial"]) for aid, a in actors.items()}
    parents = {child: a["id"] for a in actors.values() if a["kind"] == "group"
               for child in a["payload"]["children"]}
    writes: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    ordered = sorted(enumerate(scene["events"]), key=lambda pair: resolved[pair[1]["id"]][0])
    for index, event in ordered:
        if event["verb"] == "hold":
            continue
        path = f"$.scenes[{scene_index}].events[{index}]"
        if not any(states[aid][prop] != target for aid, changes in event["changes"].items()
                   for prop, target in changes.items()):
            raise ScoreError("non-hold action writes only unchanged state; use a motivated hold", path)
        for aid, changes in event["changes"].items():
            for prop, target in changes.items():
                before = states[aid][prop]
                if event["verb"] in ("reveal", "draw", "fill", "grow") and target < before:
                    raise ScoreError("this verb increases state; use update/hide for a decreasing change", path + ".changes." + aid + "." + prop)
                if event["verb"] == "hide" and target > before:
                    raise ScoreError("hide cannot increase visibility", path + ".changes." + aid + "." + prop)
                start, end = resolved[event["id"]]
                writes[aid, prop].append({"start": start, "end": end, "from": before,
                                         "to": target, "easing": event["easing"]})
                states[aid][prop] = target

    def positive(aid, prop, at):
        value = actors[aid]["initial"].get(prop, 1)
        for track in writes.get((aid, prop), []):
            if at < track["start"]:
                break
            if at >= track["end"]:
                value = track["to"]
            elif at == track["start"] or track["easing"] == "step":
                return track["from"] > 0
            else:
                return max(track["from"], track["to"]) > 0
        return value > 0

    def visible_chain(aid, at):
        while aid is not None:
            if not all(positive(aid, prop, at) for prop in ("opacity", "reveal")):
                return False
            aid = parents.get(aid)
        return True

    for index, event in ordered:
        if event["verb"] == "hold":
            continue
        start, end = resolved[event["id"]]
        for aid in event["changes"]:
            # Invisible preparation may legitimately feed a later reveal.
            if event["verb"] in ("update", "settle", "move", "reframe", "morph"):
                window_end = scene["duration_ms"]
            else:
                window_end = end
            leaves, pending = [], [aid]
            while pending:
                member = pending.pop()
                if actors[member]["kind"] == "group":
                    pending.extend(actors[member]["payload"]["children"])
                else:
                    leaves.append(member)
            chain = set()
            for leaf in leaves:
                parent = leaf
                while parent is not None:
                    chain.add(parent)
                    parent = parents.get(parent)
            boundaries = {start, window_end}
            for member in chain:
                for prop in ("opacity", "reveal"):
                    for track in writes.get((member, prop), []):
                        boundaries.update(t for t in (track["start"], track["end"])
                                          if start <= t <= window_end)
            points = sorted(boundaries)
            samples = points + [(a + b) / 2 for a, b in zip(points, points[1:])]
            if not any(visible_chain(leaf, at) for at in samples for leaf in leaves):
                raise ScoreError("action has no visible declared effect, including ancestor masks",
                                 f"$.scenes[{scene_index}].events[{index}].changes.{aid}")


def _mechanisms(document, report, compiled=False):
    for i, scene in enumerate(document["scenes"]):
        path = f"$.scenes[{i}]"
        actors = {a["id"]: a for a in scene["actors"]}
        times = ({e["id"]: (e["start_ms"], e["end_ms"]) for e in scene["events"]} if compiled else _score_times(document, scene))
        meaningful, claimed, noops = set(), set(), []
        state = {aid: deepcopy(a["initial"]) for aid, a in actors.items()}
        parents = {child: a["id"] for a in actors.values() if a["kind"] == "group" for child in a["payload"]["children"]}
        def visible_at_cue(aid, changes):
            while aid is not None:
                properties = changes.get(aid, {})
                for prop in ("opacity", "reveal"):
                    before = state[aid].get(prop, 1)
                    if max(before, properties.get(prop, before)) <= 0:
                        return False
                aid = parents.get(aid)
            return True
        def participants(aid):
            pending, members = [aid], []
            while pending:
                member = pending.pop()
                members.append(member)
                if actors[member]["kind"] == "group":
                    pending.extend(actors[member]["payload"]["children"])
            return members
        event_changes: dict[str, dict[str, dict[str, Any]]] = {}
        ordered = sorted(scene["events"], key=lambda e: (times[e["id"]] is None, (times[e["id"]] or (0, 0))[0]))
        for event in ordered:
            if event["verb"] == "hold":
                continue
            if compiled:
                changes: dict[str, dict[str, Any]] = defaultdict(dict)
                for track in scene["tracks"]:
                    if track["event_id"] == event["id"]:
                        changes[track["actor_id"]][track["property"]] = track["to"]
            else:
                changes = event["changes"]
            event_changes[event["id"]] = changes
            different = {target for target, props in changes.items() if any(state[target][p] != v for p, v in props.items())}
            if not different:
                noops.append(event["id"])
            for target in different:
                for participant in participants(target):
                    actor = actors[participant]
                    visible = visible_at_cue(participant, changes)
                    evidence_linked = set(actor["evidence_ids"]) & set(event["claim_ids"])
                    if not visible and evidence_linked:
                        _finding(report, "INVISIBLE_CLAIM_CHANGE", "warning", "Motion / Performance Director", path + ".events", "A factual state change is masked by the actor or an ancestor's declared opacity/reveal at the cue.", scene=scene["id"], actors=[participant], events=[event["id"]], hint="Reveal the implicated actor/group at the causal cue or move the claim cue; preserve unrelated tracks.")
                    if visible:
                        meaningful.add(participant)
                        if actor["role"] != "background" and evidence_linked:
                            claimed.add(participant)
            for target, props in changes.items():
                state[target].update(props)
        if noops:
            _finding(report, "NO_OP_EVENT", "warning", "Motion / Performance Director", path + ".events", "Non-hold events write only unchanged state; this is not meaningful synchronized animation.", scene=scene["id"], events=noops, hint="Correct only these target states, or express intended stillness as an explicit motivated hold.")
        if _intentional(scene):
            _finding(report, "INTENTIONAL_HOLD_OR_MOTIF", "info", "Editorial / Rhythm Director", path,
                     "An explicit motif or still/hold scene is allowed; no perpetual-motion quota is imposed.", scene=scene["id"])
        elif not claimed:
            _finding(report, "NARRATED_CLAIM_WITHOUT_VISIBLE_STATE_CHANGE", "warning", "Motion / Performance Director", path + ".events",
                     "No non-background evidence-bearing actor changes visibly during this narrated claim; decorative motion is not a mechanism.", scene=scene["id"], actors=meaningful,
                     hint="Review the claimed mechanism's local cue/targets with P8 Motion. Add the intended semantic change or an honest intentional hold, not decorative wiggles.")
        if not compiled:
            for j, event in enumerate(scene["events"]):
                cue = event["cue"]
                if cue["kind"] == "fraction":
                    _finding(report, "PROVISIONAL_CUE", "info", "Sound Direction / Alignment Integration", path + f".events[{j}].cue", "Fraction timing is provisional, not word-aligned audio evidence.", scene=scene["id"], events=[event["id"]])
                elif cue["kind"] == "word" and times[event["id"]] is None:
                    _finding(report, "ALIGNMENT_REQUIRED", "warning", "Sound Direction / Alignment Integration", path + f".events[{j}].cue", "This word cue is legal authoring but cannot execute without real reported alignment.", scene=scene["id"], events=[event["id"]], hint="Bind the actual provider/forced-alignment word intervals. Never synthesize uniform word times.")
        # Same-data redundant views must change together, not comparisons of different data.
        for relation in scene["relations"]:
            if relation["kind"] not in ("labels", "connected_to", "supports"):
                continue
            left, right = actors[relation["from"]], actors[relation["to"]]
            if left["kind"] not in ("number", "bar") or right["kind"] not in ("number", "bar") or left.get("value_binding") != right.get("value_binding"):
                continue
            for event in scene["events"]:
                changes = event_changes.get(event["id"], {})
                a = "value" in changes.get(left["id"], {})
                b = "value" in changes.get(right["id"], {})
                if a != b:
                    _finding(report, "LINKED_DATA_VIEW_DRIFT", "warning", "Motion / Performance Director", path + ".events", "Related redundant readout/magnitude views update separately and may show contradictory states.", scene=scene["id"], actors=[left["id"], right["id"]], events=[event["id"]], hint="Link the implicated data views in one event with explicit evidence bindings; keep unrelated comparison views independent.")


def audit_score(score, history=None):
    """Return structured technical findings; invalid contracts fail, never fall back.

    history: at most the latest 50 scores, plans or successful audit reports. Exact
    graph-signature reuse produces warnings, never a scalar creative score. Input
    and historical decisions are not mutated. Unresolved word cues remain a
    visible execution-readiness gap; honest fraction cues remain provisional.
    """
    report = _new_report("score")
    document = _validated(score, validate_score, report)
    if document is None:
        return _finish(report)
    _provenance(document, report)
    _signatures(document, report)
    _palette(document, report)
    _mechanisms(document, report)
    _repetition(document, report, history)
    return _finish(report)


def _advance(text, font_size):
    # Deliberately heuristic: no remote/local font loading or legal certification.
    width = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        width += (1 if unicodedata.east_asian_width(char) in ("W", "F") else .32 if char.isspace() or char in "ilI.,:;'|!" else .85 if char in "MW@%" else .58) * font_size
    return width


def _text_variants(actor, tracks):
    if actor["kind"] == "text":
        return [actor["initial"]["text"]] + [t["to"] for t in tracks if t["property"] == "text"]
    if actor["kind"] == "number":
        decimals, unit = actor["payload"].get("decimals", 0), actor["payload"]["unit"]
        values = [actor["initial"]["value"]] + [t["to"] for t in tracks if t["property"] == "value"]
        suffix = "" if unit == "1" else " " + unit
        return [f"{v:.{decimals}f}{suffix}" for v in values]
    return []


def _geometry(document, report):
    canvas = document["canvas"]
    for i, scene in enumerate(document["scenes"]):
        tracks_by_actor = defaultdict(list)
        for track in scene["tracks"]:
            tracks_by_actor[track["actor_id"]].append(track)
        for j, actor in enumerate(scene["actors"]):
            path, g = f"$.scenes[{i}].actors[{j}].geometry", actor["geometry"]
            tracks = tracks_by_actor[actor["id"]]
            xs = [actor["initial"]["x"]] + [t[v] for t in tracks if t["property"] == "x" for v in ("from", "to")]
            ys = [actor["initial"]["y"]] + [t[v] for t in tracks if t["property"] == "y" for v in ("from", "to")]
            scales = [actor["initial"].get("scale", 1)] + [t[v] for t in tracks if t["property"] == "scale" for v in ("from", "to")]
            max_scale = max(scales)
            margin_x, margin_y = g["width"] * (max_scale - 1) / 2, g["height"] * (max_scale - 1) / 2
            if min(xs) - margin_x < -.01 or min(ys) - margin_y < -.01 or max(xs) + g["width"] + margin_x > canvas["width"] + .01 or max(ys) + g["height"] + margin_y > canvas["height"] + .01:
                _finding(report, "ACTOR_BOUNDS", "warning", "Storyboard Compiler", path, "Actor motion/scale endpoint envelope extends outside the native canvas; intentional exits require exact-frame review.", scene=scene["id"], actors=[actor["id"]], observed={"canvas": canvas, "x_extent": [min(xs) - margin_x, max(xs) + g["width"] + margin_x], "y_extent": [min(ys) - margin_y, max(ys) + g["height"] + margin_y]}, hint="Refit only this actor/anchor envelope natively for the aspect, preserving its relations. Do not crop the landscape plan.")
            if g["width"] <= 0 or g["height"] <= 0:
                _finding(report, "ZERO_RENDER_BOUNDS", "warning", "Storyboard Compiler", path, "A zero-area primitive may not render its intended semantic state.", scene=scene["id"], actors=[actor["id"]])
            points = g.get("points", [])
            if any(p["x"] < 0 or p["y"] < 0 or p["x"] > g["width"] or p["y"] > g["height"] for p in points):
                _finding(report, "PRIMITIVE_POINTS_BOUNDS", "warning", "Storyboard Compiler", path + ".points", "Compiled local line points escape their declared actor slot.", scene=scene["id"], actors=[actor["id"]])
            if actor["kind"] not in ("text", "number"):
                continue
            lines, font, line_height = g["lines"], g["font_size"], g["line_height"]
            if not lines or len(lines) * line_height > g["height"] + .01 or line_height < font:
                _finding(report, "TEXT_LINE_BOUNDS", "warning", "Storyboard Compiler", path, "Declared fitted text lines/line height do not fit the slot height.", scene=scene["id"], actors=[actor["id"]], observed={"line_count": len(lines), "line_height": line_height, "font_size": font, "slot_height": g["height"]}, hint="Refit only this actor's text states and caption hierarchy; do not shrink all text or rewrite accepted claims.")
            maximum_lines = actor["payload"].get("max_lines", 1 if actor["kind"] == "number" else 8)
            overflow = []
            for text in _text_variants(actor, tracks):
                if actor["kind"] == "number":
                    estimated_lines = 1
                    widest = _advance(text, font)
                else:
                    estimated_lines, used, widest = 1, 0, 0
                    for word in text.split():
                        word_width = _advance(word, font)
                        if used and used + _advance(" ", font) + word_width > g["width"]:
                            estimated_lines, used = estimated_lines + 1, word_width
                        else:
                            used += (_advance(" ", font) if used else 0) + word_width
                        widest = max(widest, word_width)
                if widest > g["width"] or estimated_lines > maximum_lines or estimated_lines * line_height > g["height"]:
                    overflow.append({"characters": len(text), "estimated_lines": estimated_lines, "widest_run_px": round(widest, 2)})
            if overflow or any(_advance(line, font) > g["width"] for line in lines):
                _finding(report, "TEXT_WIDTH_ESTIMATE", "warning", "Storyboard Compiler", path, "One or more possible text/value states risk overflow by a conservative advance estimate; confirm actual local-font frames.", scene=scene["id"], actors=[actor["id"]], observed={"risk_states": overflow}, hint="Fit the longest implicated state, including numeric unit suffixes and updates, in this native slot. Preserve other accepted layout decisions.")
            if font < 16 * min(canvas["width"], canvas["height"]) / 1080:
                _finding(report, "TEXT_READABILITY_SIZE", "warning", "Art Director / Storyboard Compiler", path + ".font_size", "Fitted text is below a conservative native-resolution readability reference.", scene=scene["id"], actors=[actor["id"]], observed={"font_size": font}, hint="Increase only this fitted text or reflow its local graph; verify the exact native output.")
            if actor["kind"] == "number":
                decimals = actor["payload"].get("decimals", 0)
                values = [actor["initial"]["value"]] + [t["to"] for t in tracks if t["property"] == "value"]
                if any(float(f"{v:.{decimals}f}") != v for v in values):
                    _finding(report, "DISPLAY_ROUNDING_LOSS", "warning", "Art Director / Source Intelligence", path, "Declared numeric formatting rounds an evidence-bound endpoint; displayed precision needs explicit semantic review.", scene=scene["id"], actors=[actor["id"]], hint="Increase only this number actor's precision or get an explicit evidence-backed rounding decision; never alter raw evidence.")
        text_actors = [a for a in scene["actors"] if a["kind"] in ("text", "number") and a["initial"]["opacity"] > 0 and a["initial"].get("reveal", 1) > 0]
        for j, left in enumerate(text_actors):
            for right in text_actors[j + 1:]:
                lg, rg, ls, rs = left["geometry"], right["geometry"], left["initial"], right["initial"]
                overlap_w = max(0, min(ls["x"] + lg["width"], rs["x"] + rg["width"]) - max(ls["x"], rs["x"]))
                overlap_h = max(0, min(ls["y"] + lg["height"], rs["y"] + rg["height"]) - max(ls["y"], rs["y"]))
                area = min(lg["width"] * lg["height"], rg["width"] * rg["height"])
                if area and overlap_w * overlap_h / area > .2:
                    _finding(report, "TEXT_GEOMETRY_OVERLAP", "warning", "Storyboard Compiler", f"$.scenes[{i}].actors", "Visible fitted text slots substantially overlap; intentional typography must be checked in exact frames.", scene=scene["id"], actors=[left["id"], right["id"]], observed={"overlap_fraction_of_smaller_slot": round(overlap_w * overlap_h / area, 3)}, hint="Resolve only these fitted text slots/anchors in the native composition; preserve illustration, style and accepted semantic links.")
        _relational_geometry(document, scene, i, report)


def _distance_to_rect(point, actor):
    g, state = actor["geometry"], actor["initial"]
    x, y = state["x"], state["y"]
    return math.hypot(max(x - point[0], 0, point[0] - x - g["width"]), max(y - point[1], 0, point[1] - y - g["height"]))


def _relational_geometry(document, scene, index, report):
    actors = {a["id"]: a for a in scene["actors"]}
    for actor in actors.values():
        if actor["kind"] != "connector":
            continue
        g = actor["geometry"]
        endpoints = [(actor["initial"]["x"] + p["x"], actor["initial"]["y"] + p["y"]) for p in (g["points"][0], g["points"][-1])]
        distances = [_distance_to_rect(p, actors[actor["payload"][key]]) for p, key in zip(endpoints, ("from", "to"))]
        tolerance = max(12, document["style"]["strokes"]["width"] * 4)
        if any(d > tolerance for d in distances):
            _finding(report, "CONNECTOR_RELATIONAL_GEOMETRY", "warning", "Storyboard Compiler", f"$.scenes[{index}].actors", "A connector's endpoint geometry does not reach its declared semantic endpoint actor.", scene=scene["id"], actors=[actor["id"], actor["payload"]["from"], actor["payload"]["to"]], observed={"endpoint_distance_px": distances, "tolerance_px": tolerance}, hint="Reroute only the connector for this native aspect, preserving its semantic endpoints and evidence.")
    for relation in scene["relations"]:
        if relation["kind"] != "comparison":
            continue
        pair = [actors[relation[k]] for k in ("from", "to")]
        if not all(a["kind"] == "bar" for a in pair):
            continue
        left, right = pair
        unit = left["payload"]["unit"]
        domains = []
        for actor in pair:
            # Domains are axis bounds, NOT reported evidence quantities: a count
            # axis may legitimately extend below zero or use half-count padding.
            _, multiplier, offset = UNIT_TABLE[actor["payload"]["unit"]]
            _, target_multiplier, target_offset = UNIT_TABLE[unit]
            domains.append([(value * multiplier + offset - target_offset) / target_multiplier for value in actor["payload"]["domain"]])
        lengths = [a["geometry"]["width" if a["payload"]["orientation"] == "horizontal" else "height"] for a in pair]
        compatible = all(math.isclose(a, b, rel_tol=0, abs_tol=1e-9) for a, b in zip(*domains))
        if not compatible or pair[0]["payload"]["orientation"] != pair[1]["payload"]["orientation"] or not math.isclose(*lengths, rel_tol=.01, abs_tol=1):
            _finding(report, "COMPARISON_SCALE_GEOMETRY", "warning", "Storyboard Compiler / Art Director", f"$.scenes[{index}].relations", "Compared bars do not share a unit-normalized domain and physical scale; correct evidence alone does not make lengths comparable.", scene=scene["id"], actors=[left["id"], right["id"]], observed={"domains_in_unit": domains, "unit": unit, "lengths_px": lengths}, hint="Normalize only the compared bars' explicit domains and native lengths using declared conversion; keep conditions, evidence and unrelated actors unchanged.")


def audit_plan(plan):
    """Audit one frozen compiled plan without importing the unfinished compiler.

    Contracts enforce linked intervals, retained terminal state, capabilities,
    evidence/units/licensing and no executable/fallback payloads. Additional
    checks inspect geometry, possible text states, contrast and relational scale.
    This neither executes the browser nor certifies its implementation fidelity.
    """
    report = _new_report("plan")
    document = _validated(plan, validate_plan, report)
    if document is None:
        return _finish(report)
    _provenance(document, report)
    _signatures(document, report)
    _palette(document, report, compiled=True)
    _mechanisms(document, report, compiled=True)
    _geometry(document, report)
    if document["output"]["background"].casefold() != document["style"]["palette"]["background"].casefold():
        _finding(report, "OUTPUT_BACKGROUND_STYLE_DRIFT", "warning", "Storyboard Compiler / Art Director", "$.output.background", "Output backing differs from the declared background role; contextual contrast and style coherence are not preserved automatically.", observed={"output_background": document["output"]["background"], "role_background": document["style"]["palette"]["background"]}, hint="Restore only the output backing to the approved role palette or obtain a bounded P8 Art decision; do not cycle palette families.")
    for i, scene in enumerate(document["scenes"]):
        for event in scene["events"]:
            for target in event["targets"]:
                coordinates = {t["property"] for t in scene["tracks"] if t["event_id"] == event["id"] and t["actor_id"] == target and t["property"] in ("x", "y")}
                if coordinates and coordinates != {"x", "y"}:
                    _finding(report, "POSITION_TRACK_PAIR_MISSING", "error", "Storyboard Compiler", f"$.scenes[{i}].tracks", "Semantic position lowering must retain both linked x/y tracks, even if one coordinate is unchanged.", scene=scene["id"], actors=[target], events=[event["id"]], hint="Restore only the missing coordinate track at the same cue/from/to interval. Do not drop an axis or invent hidden runtime defaults.")
    if document["direction"]["timing"] != "aligned":
        _finding(report, "PLAN_TIMING_NOT_WORD_ALIGNED", "info", "Sound Direction / Alignment Integration", "$.direction.timing", "Plan timing is declared authored/provisional, not real word-aligned voice evidence.")
    else:
        _finding(report, "ALIGNMENT_AUTHENTICITY_EXTERNAL", "info", "Sound Direction / Alignment Integration", "$.direction.timing", "The plan's aligned declaration still requires verification against actual reported audio/word bytes; plan shape alone cannot authenticate it.")
    _repetition(document, report, None)
    return _finish(report)


def audit_aspects(plans):
    """Compare all three submitted native contract plans; never generate missing ones.

    Semantic actor/relationship/event links must survive aspect-specific layout.
    Equal normalized geometry is flagged as possible scaling, not proof of wrong
    creative direction. A relation may legitimately have different pixel routing.
    """
    report = _new_report("aspects")
    if not isinstance(plans, (list, tuple)):
        _finding(report, "ASPECT_PLANS_INVALID", "error", "Storyboard Compiler", "$", "Provide a list of native plans.")
        return _finish(report)
    documents, aspects, submitted_indices = [], [], []
    for i, plan in enumerate(plans):
        child = audit_plan(plan)
        for finding in child["findings"]:
            copied = deepcopy(finding)
            copied["path"] = f"$.plans[{i}]" + copied["path"][1:]
            copied["repair"]["paths"] = [copied["path"]]
            copied["id"] = "finding_" + _hash({k: v for k, v in copied.items() if k != "id"})[:16]
            report["findings"].append(copied)
        if child["technical_pass"]:
            documents.append(validate_plan(plan))
            aspects.append(plan["aspect"])
            submitted_indices.append(i)
    if Counter(aspects) != Counter(ASPECTS.keys()):
        _finding(report, "NATIVE_ASPECT_COVERAGE", "error", "Storyboard Compiler", "$.plans", "Exactly one native plan per 16:9, 9:16 and 1:1 is required for cross-aspect integrity checks.", observed={"submitted_valid_aspects": aspects}, hint="Compile only the missing/duplicate aspect using the semantic graph; never resize/crop an existing plan as a fallback.")
    if not documents:
        return _finish(report)
    reference = documents[0]
    report["film_id"] = reference["film_id"]
    def actor_semantics(actor):
        out = {k: deepcopy(actor[k]) for k in ("id", "identity", "kind", "label", "meaning", "meaning_binding", "role", "evidence_ids", "retained", "value_binding", "layout", "payload") if k in actor}
        out["initial"] = {k: v for k, v in actor["initial"].items() if k not in ("x", "y")}
        # Auto axis orientation and connector routing legitimately lower natively.
        if actor["kind"] in ("bar", "axis"):
            out["payload"].pop("orientation", None)
        if actor["kind"] == "connector":
            out["payload"].pop("routing", None)
        return out
    def semantic(plan):
        return {"film_id": plan["film_id"], "evidence": plan["evidence"], "meaning_graph": plan.get("meaning_graph"), "style": plan["style"], "duration_ms": plan["duration_ms"], "provenance": plan["provenance"], "direction": plan["direction"],
                "scenes": [{"id": s["id"], "section_id": s["section_id"], "narration": s["narration"], "claim_ids": s["claim_ids"], "relations": sorted(s["relations"], key=lambda r: r["id"]), "events": s["events"], "transition": s["transition"],
                            "actors": sorted([actor_semantics(a) for a in s["actors"]], key=lambda a: a["id"]),
                            "tracks": sorted([{k: t[k] for k in ("event_id", "actor_id", "property", "from", "to", "start_ms", "end_ms", "easing", "verb", "claim_ids")} for t in s["tracks"] if t["property"] not in ("x", "y")], key=lambda t: (t["event_id"], t["actor_id"], t["property"]))} for s in plan["scenes"]]}
    baseline = semantic(reference)
    def geometry(plan):
        w, h = plan["canvas"]["width"], plan["canvas"]["height"]
        return [[(a["id"], round(a["geometry"]["x"] / w, 4), round(a["geometry"]["y"] / h, 4), round(a["geometry"]["width"] / w, 4), round(a["geometry"]["height"] / h, 4)) for a in sorted(s["actors"], key=lambda a: a["id"])] for s in plan["scenes"]]
    for i, document in zip(submitted_indices[1:], documents[1:]):
        if semantic(document) != baseline:
            _finding(report, "ASPECT_SEMANTIC_DRIFT", "error", "Storyboard Compiler", f"$.plans[{i}]", "Evidence, identities, relations or linked state/timing differ between native aspect plans.", observed={"reference_aspect": reference["aspect"], "aspect": document["aspect"]}, hint="Restore only the lost semantic binding in this aspect; native layout may change, approved meaning may not.")
        elif geometry(document) == geometry(reference):
            _finding(report, "ASPECT_REFLOW_NOT_EVIDENCED", "warning", "Storyboard Compiler", f"$.plans[{i}].scenes", "Identical normalized slots suggest resized composition, not demonstrated graph-native reflow; deliberate invariant layouts remain possible.", observed={"reference_aspect": reference["aspect"], "aspect": document["aspect"]}, hint="Review native graph fitting and exact readable output only for this aspect; do not force arbitrary movement merely to change the signature.")
    return _finish(report)
