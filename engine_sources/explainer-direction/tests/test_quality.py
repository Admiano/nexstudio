"""Independent contract-only quality fixtures; never live inference/audio proof."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from explainer_direction.contracts import (
    ASPECTS, PLAN_SCHEMA, ScoreError, sample_score, validate_plan, validate_score,
)
from explainer_direction.quality import (
    audit_aspects, audit_plan, audit_score, structural_signature, validate_observable_actions,
)


class ObservableActions(unittest.TestCase):
    def action_score(self, verb="fill", opacity=1):
        score = sample_score()
        scene = score["scenes"][0]
        meter = next(a for a in scene["actors"] if a["id"] == "meter")
        meter["initial"].update(opacity=opacity, fill=.2)
        scene["events"] = [{
            "id": "perform", "verb": verb, "targets": ["meter"],
            "cue": {"kind": "absolute", "ms": 100, "basis": "authored"},
            "duration_ms": 500, "dependencies": [], "easing": "linear",
            "changes": {"meter": {"fill": .8}}, "claim_ids": ["before"],
            "rationale": "Perform a declared visible state change",
        }]
        return score

    def reveal(self, score, *, ms=100, duration=500):
        scene = score["scenes"][0]
        scene["events"].append({
            "id": "show_meter", "verb": "reveal", "targets": ["meter"],
            "cue": {"kind": "absolute", "ms": ms, "basis": "authored"},
            "duration_ms": duration, "dependencies": [], "easing": "linear",
            "changes": {"meter": {"opacity": 1}}, "claim_ids": ["before"],
            "rationale": "Reveal the performer",
        })

    def test_real_change_does_not_mutate_source_or_certify_creative_quality(self):
        score = self.action_score()
        before = deepcopy(score)
        validate_observable_actions(score, 0)
        self.assertEqual(score, before)

    def test_no_op_is_not_a_performance(self):
        score = self.action_score()
        score["scenes"][0]["events"][0]["changes"]["meter"]["fill"] = .2
        with self.assertRaisesRegex(ScoreError, "only unchanged state"):
            validate_observable_actions(score, 0)

    def test_invisible_performer_is_rejected(self):
        with self.assertRaisesRegex(ScoreError, "no visible declared effect"):
            validate_observable_actions(self.action_score(opacity=0), 0)

    def test_concurrent_reveal_works_independently_of_event_array_order(self):
        score = self.action_score(opacity=0)
        self.reveal(score)
        for _ in range(2):
            validate_observable_actions(score, 0)
            score["scenes"][0]["events"].reverse()

    def test_hidden_preparation_is_not_mistaken_for_visible_filling(self):
        score = self.action_score(opacity=0)
        self.reveal(score, ms=1000)
        with self.assertRaisesRegex(ScoreError, "no visible declared effect"):
            validate_observable_actions(score, 0)
        score["scenes"][0]["events"][0]["verb"] = "update"
        validate_observable_actions(score, 0)

    def test_increasing_verb_cannot_drain_the_actor(self):
        score = self.action_score()
        score["scenes"][0]["events"][0]["changes"]["meter"]["fill"] = .1
        with self.assertRaisesRegex(ScoreError, "verb increases state"):
            validate_observable_actions(score, 0)
        score["scenes"][0]["events"][0]["verb"] = "update"
        validate_observable_actions(score, 0)

    def test_ancestor_mask_is_checked(self):
        score = self.action_score()
        score["scenes"][0]["actors"].append({
            "id": "masked_group", "kind": "group", "role": "primary",
            "label": "Container", "meaning": "Explicit masked parent",
            "evidence_ids": ["before"], "layout": {"anchor": "primary"},
            "payload": {"children": ["meter"]},
            "initial": {"opacity": 0, "position": "home"},
        })
        with self.assertRaisesRegex(ScoreError, "ancestor masks"):
            validate_observable_actions(score, 0)

    def test_group_motion_with_no_visible_descendants_is_rejected(self):
        score = self.action_score(opacity=0)
        scene = score["scenes"][0]
        scene["actors"].append({
            "id": "empty_performer", "kind": "group", "role": "primary",
            "label": "Container", "meaning": "Explicit parent of hidden material",
            "evidence_ids": ["before"], "layout": {"anchor": "primary"},
            "payload": {"children": ["meter"]},
            "initial": {"opacity": 0, "position": "home"},
        })
        scene["events"][0].update(verb="reveal", targets=["empty_performer"],
                                 changes={"empty_performer": {"opacity": 1}})
        with self.assertRaisesRegex(ScoreError, "no visible declared effect"):
            validate_observable_actions(score, 0)


def plan_fixture(score=None, aspect="16:9"):
    """Explicit test lowering, no dependency on compiler or renderer modules."""
    score = deepcopy(score or sample_score())
    width, height = ASPECTS[aspect]
    compiled_scenes, start = [], 0
    seen = set()
    for authored in score["scenes"]:
        actors, tracks, events = [], [], []
        for i, actor in enumerate(authored["actors"]):
            native_row = aspect == "16:9"
            x, y = ((150 + i * 460, 260) if native_row else (140, 150 + i * (350 if aspect == "9:16" else 280)))
            g = {"x": x, "y": y, "width": 390, "height": 260}
            compiled = {k: deepcopy(actor[k]) for k in ("id", "kind", "role", "label", "meaning", "evidence_ids", "payload", "layout")}
            compiled.update(identity=actor["id"], retained=actor["id"] in seen, geometry=g,
                            initial={k: v for k, v in actor["initial"].items() if k != "position"})
            compiled["initial"].update(x=x, y=y)
            if "value_binding" in actor:
                compiled["value_binding"] = actor["value_binding"]
            if actor["kind"] in ("bar", "axis"):
                compiled["payload"]["orientation"] = "horizontal" if native_row else "vertical"
            if actor["kind"] in ("text", "number"):
                g.update(font_size=32, line_height=42, lines=[actor["initial"].get("text", str(actor["initial"].get("value")))])
            if actor["kind"] in ("axis", "connector"):
                g["points"] = [{"x": 0, "y": 0}, {"x": g["width"], "y": g["height"]}]
            seen.add(actor["id"])
            actors.append(compiled)
        ends = {}
        states = {a["id"]: deepcopy(a["initial"]) for a in actors}
        for event in authored["events"]:
            cue = event["cue"]
            local = cue["fraction"] * authored["duration_ms"] if cue["kind"] == "fraction" else cue["ms"]
            begin = max([start + local] + [ends[d] for d in event["dependencies"]])
            end = begin + event["duration_ms"]
            ends[event["id"]] = end
            ce = {k: deepcopy(event[k]) for k in ("id", "verb", "targets", "dependencies", "claim_ids", "rationale")}
            ce.update(start_ms=begin, end_ms=end)
            events.append(ce)
            for aid, changes in event["changes"].items():
                for prop, value in changes.items():
                    if prop == "position":
                        # Native semantic move lowering is explicit, not a hidden timer.
                        for coordinate, amount in (("x", 100), ("y", 80)):
                            tracks.append({"event_id": event["id"], "actor_id": aid, "property": coordinate,
                                           "from": states[aid][coordinate], "to": states[aid][coordinate] + amount,
                                           "start_ms": begin, "end_ms": end, "easing": event["easing"], "verb": event["verb"],
                                           "rationale": event["rationale"], "claim_ids": event["claim_ids"]})
                            states[aid][coordinate] += amount
                        continue
                    tracks.append({"event_id": event["id"], "actor_id": aid, "property": prop,
                                   "from": states[aid][prop], "to": value, "start_ms": begin, "end_ms": end,
                                   "easing": "step" if prop in ("selection", "text", "variant") else event["easing"],
                                   "verb": event["verb"], "rationale": event["rationale"], "claim_ids": event["claim_ids"]})
                    states[aid][prop] = value
        end_scene = start + authored["duration_ms"]
        scene = {k: deepcopy(authored[k]) for k in ("id", "section_id", "intent", "claim_ids", "narration", "relations")}
        scene.update(start_ms=start, end_ms=end_scene, actors=actors, events=events, tracks=tracks,
                     transition={"kind": authored["transition"]["kind"], "start_ms": end_scene - authored["transition"]["duration_ms"], "end_ms": end_scene},
                     composition=deepcopy(authored.get("composition", {"flow": "auto", "density": "balanced"})),
                     constraints=["TEST ONLY native semantic slot placement"])
        if "direction" in authored["transition"]:
            scene["transition"]["direction"] = authored["transition"]["direction"]
        if "motif" in authored:
            scene["motif"] = authored["motif"]
        compiled_scenes.append(scene)
        start = end_scene
    return validate_plan({"schema": PLAN_SCHEMA, "film_id": score["film_id"], "title": score["title"], "aspect": aspect,
                          "canvas": {"width": width, "height": height}, "output": {"fps": 30, "format": "mp4", "background": score["style"]["palette"]["background"]},
                          "duration_ms": start, "style": score["style"], "evidence": score["evidence"], "scenes": compiled_scenes, "provenance": score["provenance"],
                          "direction": {"authority": "P8", "status": score["provenance"]["status"], "timing": "provisional",
                                        "score_sha256": hashlib.sha256(json.dumps(score, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}})


def rename_scene(scene, suffix):
    scene = deepcopy(scene)
    actor_ids = {a["id"]: a["id"] + suffix for a in scene["actors"]}
    event_ids = {e["id"]: e["id"] + suffix for e in scene["events"]}
    scene["id"] += suffix
    for actor in scene["actors"]:
        actor["id"] = actor_ids[actor["id"]]
        if "relative_to" in actor["layout"]:
            actor["layout"]["relative_to"] = actor_ids[actor["layout"]["relative_to"]]
        if "retain" in actor:
            actor["retain"] = actor["id"]
    for relation in scene["relations"]:
        relation["id"] += suffix
        relation["from"], relation["to"] = actor_ids[relation["from"]], actor_ids[relation["to"]]
    for event in scene["events"]:
        event["id"] = event_ids[event["id"]]
        event["targets"] = [actor_ids[a] for a in event["targets"]]
        event["changes"] = {actor_ids[a]: props for a, props in event["changes"].items()}
        event["dependencies"] = [event_ids[d] for d in event["dependencies"]]
        if "value_bindings" in event:
            event["value_bindings"] = {actor_ids[a]: eid for a, eid in event["value_bindings"].items()}
    if "focus" in scene.get("composition", {}):
        scene["composition"]["focus"] = actor_ids[scene["composition"]["focus"]]
    return scene


def qualitative_score(topic):
    """Different mechanisms with no measured-number widgets or template topics."""
    score = sample_score()
    score["film_id"] = "qa_" + topic
    source = score["provenance"]["source"]
    score["evidence"] = [{"id": "mechanism", "claim": "Qualitative illustrative causal mechanism.", "status": "illustrative", "source": deepcopy(source)}]
    scene = score["scenes"][0]
    scene["claim_ids"] = ["mechanism"]
    scene["narration"] = {"plant": "Water enters a root and moves through the stem.", "cache": "An available cached response avoids a repeated lookup.", "lever": "The applied force turns the lever around its pivot."}[topic]
    scene["actors"] = []
    for aid, shape, anchor in (("origin", "circle", "start"), ("destination", "rect", "end")):
        scene["actors"].append({"id": aid, "kind": "shape", "role": "primary", "label": topic + " " + aid,
                                "meaning": "Illustrative causal participant", "evidence_ids": ["mechanism"],
                                "layout": {"anchor": anchor}, "payload": {"shape": shape},
                                "initial": {"opacity": 1, "position": "home", "variant": shape, "fill": 0, "scale": 1}})
    scene["relations"] = [{"id": "causal", "kind": "flows_to" if topic == "plant" else "causes", "from": "origin", "to": "destination", "evidence_ids": ["mechanism"]}]
    scene["events"] = [{"id": "mechanism_change", "verb": "update", "targets": ["origin", "destination"],
                        "cue": {"kind": "fraction", "fraction": .2, "provisional": True}, "duration_ms": 1500,
                        "dependencies": [], "easing": "ease_in_out", "changes": {"origin": {"fill": 1}, "destination": {"fill": 1}},
                        "claim_ids": ["mechanism"], "rationale": "Expose the causal participant states at one linked cue."}]
    scene["composition"] = {"flow": "column" if topic == "plant" else "radial" if topic == "lever" else "row", "density": "balanced", "focus": "destination"}
    return validate_score(score)


def codes(report):
    return {finding["code"] for finding in report["findings"]}


def compared_bars():
    score = sample_score()
    scene = score["scenes"][0]
    scene["events"] = []
    scene["actors"] = [deepcopy(scene["actors"][1]), deepcopy(scene["actors"][1])]
    left, right = scene["actors"]
    left["id"], right["id"] = "litres", "millilitres"
    left["layout"] = {"anchor": "primary"}
    right["layout"] = {"anchor": "secondary"}
    left["evidence_ids"], right["evidence_ids"] = ["before"], ["after"]
    right["payload"]["unit"] = "mL"
    right["payload"]["domain"] = [0, 40000]
    right["initial"]["value"] = 40000
    right["value_binding"] = "after"
    scene["relations"] = [{"id": "compare", "kind": "comparison", "from": "litres", "to": "millilitres", "evidence_ids": ["before", "after"]}]
    scene["composition"]["focus"] = "litres"
    return validate_score(score)


class StructuralQuality(unittest.TestCase):
    def test_arbitrary_topics_and_independent_qualitative_mechanisms(self):
        for score in [sample_score(t) for t in ("water", "energy", "travel")] + [qualitative_score(t) for t in ("plant", "cache", "lever")]:
            with self.subTest(film=score["film_id"]):
                before = deepcopy(score)
                report = audit_score(score)
                self.assertTrue(report["technical_pass"], report)
                self.assertNotIn("NARRATED_CLAIM_WITHOUT_VISIBLE_STATE_CHANGE", codes(report))
                self.assertEqual(score, before)
                self.assertFalse(report["authority"]["creative_lock"])
                self.assertEqual(report["authority"]["certification"], "NOT_CERTIFIED")
                self.assertIn("DEVELOPMENT_ONLY", codes(report))
                self.assertNotIn("quality_score", report)
                json.dumps(report, allow_nan=False)

    def test_labels_palette_and_quantities_do_not_hide_template_reuse(self):
        history = sample_score("water")
        score = sample_score("energy")
        score["title"] = "Different headline"
        score["style"]["family"] = "forest"
        score["style"]["palette"]["primary"] = "#AAFFAA"
        for actor in score["scenes"][0]["actors"]:
            actor["label"] = "A fresh label"
        report = audit_score(score, history=[history])
        self.assertIn("FILM_TEMPLATE_REUSE", codes(report))
        self.assertEqual(report["film_signature"], audit_score(history)["film_signature"])

    def test_actor_ids_order_and_relation_ids_are_not_signature_authority(self):
        score = sample_score()
        original = structural_signature(score["scenes"][0])
        changed = rename_scene(score["scenes"][0], "_renamed")
        changed["actors"].reverse()
        changed["events"][0]["targets"].reverse()
        changed["events"][0]["changes"] = dict(reversed(list(changed["events"][0]["changes"].items())))
        self.assertEqual(original, structural_signature(changed))

    def test_inverse_spatial_spelling_does_not_fake_structural_variety(self):
        for kind, inverse in (("above", "below"), ("left_of", "right_of")):
            scene = sample_score()["scenes"][0]
            scene["relations"].append({
                "id": "physical_relation", "kind": kind, "from": "readout",
                "to": "meter", "evidence_ids": ["before"],
            })
            original = structural_signature(scene)
            relation = scene["relations"][-1]
            relation.update(kind=inverse, **{"from": "meter", "to": "readout"})
            self.assertEqual(original, structural_signature(scene))

    def test_material_relations_composition_and_action_pattern_differ(self):
        score = sample_score()
        initial = audit_score(score)["film_signature"]
        for mutate in (lambda s: s["scenes"][0]["composition"].update(flow="radial"),
                       lambda s: s["scenes"][0]["relations"][0].update(kind="supports"),
                       lambda s: s["scenes"][0]["events"][0]["changes"]["readout"].update(highlight=0)):
            changed = deepcopy(score)
            mutate(changed)
            report = audit_score(changed, history=[score])
            self.assertNotEqual(initial, report["film_signature"])
            self.assertNotIn("FILM_TEMPLATE_REUSE", codes(report))
        self.assertNotEqual(audit_score(qualitative_score("plant"))["film_signature"], audit_score(qualitative_score("cache"))["film_signature"])

    def test_graph_topology_not_just_kind_counts(self):
        score = qualitative_score("plant")
        score["scenes"][0]["actors"].append({**deepcopy(score["scenes"][0]["actors"][1]), "id": "third"})
        score["scenes"][0]["relations"].append({"id": "next", "kind": "flows_to", "from": "destination", "to": "third", "evidence_ids": ["mechanism"]})
        chain = audit_score(score)
        score["scenes"][0]["relations"][1]["from"] = "origin"
        fork = audit_score(score)
        self.assertTrue(chain["technical_pass"])
        self.assertTrue(fork["technical_pass"])
        self.assertNotEqual(chain["film_signature"], fork["film_signature"])

    def test_monotony_three_scenes_and_explicit_motifs(self):
        score = sample_score()
        score["scenes"] = [rename_scene(score["scenes"][0], suffix) for suffix in ("_a", "_b", "_c")]
        report = audit_score(score)
        self.assertIn("SCENE_MONOTONY", codes(report))
        for scene in score["scenes"]:
            scene["motif"] = "Intentional repeated mechanism comparison across the series."
        report = audit_score(score, history=[deepcopy(score)])
        self.assertNotIn("SCENE_MONOTONY", codes(report))
        self.assertNotIn("FILM_TEMPLATE_REUSE", codes(report))
        self.assertIn("INTENTIONAL_HOLD_OR_MOTIF", codes(report))

    def test_still_and_hold_scenes_are_not_forced_into_motion(self):
        for mode in ("still", "hold"):
            score = sample_score()
            scene = score["scenes"][0]
            if mode == "still":
                scene["events"] = []
            else:
                hold = scene["events"][1]
                hold["dependencies"] = []
                scene["events"] = [hold]
            report = audit_score(score, history=[score])
            self.assertTrue(report["technical_pass"])
            self.assertNotIn("NARRATED_CLAIM_WITHOUT_VISIBLE_STATE_CHANGE", codes(report))
            self.assertNotIn("FILM_TEMPLATE_REUSE", codes(report))

    def test_prior_audits_history_and_invalid_entries(self):
        score = sample_score()
        prior = audit_score(score)
        snapshot = deepcopy(prior)
        report = audit_score(score, history=[prior, {}, None])
        self.assertIn("FILM_TEMPLATE_REUSE", codes(report))
        self.assertIn("HISTORY_INVALID", codes(report))
        self.assertEqual(prior, snapshot)
        self.assertIn("HISTORY_INVALID", codes(audit_score(score, history="not-list")))
        self.assertIn("HISTORY_BOUNDED", codes(audit_score(score, history=[prior] * 51)))

    def test_history_plan_detects_same_semantic_template_before_and_after_lowering(self):
        score = sample_score()
        report = audit_score(score, history=[plan_fixture(score)])
        self.assertIn("FILM_TEMPLATE_REUSE", codes(report))

    def test_malformed_report_history_does_not_crash_or_become_accepted_memory(self):
        malformed = {"schema": "explainer-direction.audit/v1", "technical_pass": True,
                     "film_signature": {"digest": "not-a-hash"}, "scene_signatures": [{"digest": []}]}
        self.assertIn("HISTORY_INVALID", codes(audit_score(sample_score(), history=[malformed])))

    def test_nested_group_visibility_and_linked_reveal_mask(self):
        score = qualitative_score("cache")
        scene = score["scenes"][0]
        for actor in scene["actors"]:
            actor["initial"]["reveal"] = 0
        self.assertIn("INVISIBLE_CLAIM_CHANGE", codes(audit_score(score)))
        score = qualitative_score("cache")
        scene = score["scenes"][0]
        def group(aid, children, opacity):
            return {"id": aid, "kind": "group", "role": "primary", "label": "Participants", "meaning": "Illustrative mechanism participants", "evidence_ids": [], "layout": {"anchor": "context"}, "payload": {"children": children}, "initial": {"opacity": opacity, "position": "home"}}
        scene["actors"].extend([group("inner", ["origin", "destination"], 1), group("outer", ["inner"], 0)])
        self.assertIn("INVISIBLE_CLAIM_CHANGE", codes(audit_score(score)))
        scene["events"][0]["targets"].append("outer")
        scene["events"][0]["changes"]["outer"] = {"opacity": 1}
        self.assertNotIn("INVISIBLE_CLAIM_CHANGE", codes(audit_score(score)))

    def test_group_move_is_meaningful_for_evidence_bearing_children(self):
        score = qualitative_score("plant")
        scene = score["scenes"][0]
        scene["actors"].append({"id": "mechanism_group", "kind": "group", "role": "primary", "label": "Participants", "meaning": "Illustrative mechanism group", "evidence_ids": [], "layout": {"anchor": "context"}, "payload": {"children": ["origin", "destination"]}, "initial": {"opacity": 1, "position": "home"}})
        event = scene["events"][0]
        event.update(verb="move", targets=["mechanism_group"], changes={"mechanism_group": {"position": "focus"}})
        report = audit_score(score)
        self.assertTrue(report["technical_pass"])
        self.assertNotIn("NARRATED_CLAIM_WITHOUT_VISIBLE_STATE_CHANGE", codes(report))

    def test_structured_causal_owner_and_surgical_repair_not_story_by_scene(self):
        score = sample_score()
        score["scenes"][0]["events"][0]["changes"]["readout"]["unsupported_property"] = 1
        report = audit_score(score)
        self.assertFalse(report["technical_pass"])
        finding = report["findings"][0]
        self.assertEqual(finding["causal_owner"], "Motion / Performance Director")
        self.assertEqual(finding["code"], "EVENT_MECHANISM_INVALID")
        self.assertIn("$.scenes[0]", finding["path"])
        self.assertTrue(finding["repair"]["preserve_unaffected_decisions"])
        self.assertTrue(finding["repair"]["requires_p8_commit"])
        self.assertEqual(finding["repair"]["scope"], "bounded_local")
        self.assertEqual(report, audit_score(score))

    def test_missing_initial_unknown_verb_bad_dependency_and_easing_fail_closed(self):
        mutations = [lambda s: s["scenes"][0]["actors"][0]["initial"].pop("highlight"),
                     lambda s: s["scenes"][0]["events"][0].update(verb="bounce-card"),
                     lambda s: s["scenes"][0]["events"][0].update(dependencies=["missing"]),
                     lambda s: s["scenes"][0]["events"][0].update(easing="spring")]
        for mutate in mutations:
            score = sample_score()
            mutate(score)
            before = deepcopy(score)
            report = audit_score(score)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["scene_signatures"], [])
            self.assertEqual(score, before)
            self.assertIn("still card", report["findings"][0]["repair"]["hint"])

    def test_raw_values_and_compatible_conditions_are_contract_gates(self):
        score = compared_bars()
        self.assertTrue(audit_score(score)["technical_pass"])
        score["evidence"][1]["comparison"]["conditions"]["basis"] = "different mechanism"
        report = audit_score(score)
        self.assertIn("EVIDENCE_BINDING_INVALID", codes(report))
        self.assertFalse(report["technical_pass"])
        score = sample_score()
        score["scenes"][0]["actors"][0]["initial"]["value"] = 20.00000001
        self.assertFalse(audit_score(score)["technical_pass"])

    def test_displayed_numeric_text_is_evidence_bound(self):
        score = qualitative_score("plant")
        a = score["scenes"][0]["actors"][0]
        a.update(kind="text", payload={"text": "99 L", "purpose": "annotation"}, initial={"opacity": 1, "position": "home", "text": "99 L"})
        score["scenes"][0]["events"] = []
        self.assertIn("EVIDENCE_BINDING_INVALID", codes(audit_score(score)))

    def test_noop_and_background_decorative_changes_are_not_mechanism(self):
        score = sample_score()
        event = score["scenes"][0]["events"][0]
        event["changes"] = {"readout": {"value": 20, "highlight": 0}, "meter": {"value": 20, "fill": .5}, "stage": {"selection": 0}}
        event["value_bindings"] = {"readout": "before", "meter": "before"}
        event["claim_ids"] = ["before"]
        report = audit_score(score)
        self.assertIn("NO_OP_EVENT", codes(report))
        self.assertIn("NARRATED_CLAIM_WITHOUT_VISIBLE_STATE_CHANGE", codes(report))
        score = qualitative_score("cache")
        for actor in score["scenes"][0]["actors"]:
            actor["role"] = "background"
        self.assertIn("NARRATED_CLAIM_WITHOUT_VISIBLE_STATE_CHANGE", codes(audit_score(score)))

    def test_hidden_claim_changes_warn(self):
        score = sample_score()
        for actor in score["scenes"][0]["actors"]:
            actor["initial"]["opacity"] = 0
        report = audit_score(score)
        self.assertIn("INVISIBLE_CLAIM_CHANGE", codes(report))
        self.assertIn("NARRATED_CLAIM_WITHOUT_VISIBLE_STATE_CHANGE", codes(report))

    def test_linked_readout_bar_and_selector_survive_atomic_event(self):
        score = sample_score()
        self.assertNotIn("LINKED_DATA_VIEW_DRIFT", codes(audit_score(score)))
        event = score["scenes"][0]["events"][0]
        event["targets"].remove("meter")
        del event["changes"]["meter"]
        del event["value_bindings"]["meter"]
        self.assertIn("LINKED_DATA_VIEW_DRIFT", codes(audit_score(score)))

    def test_fraction_is_not_word_alignment_and_unresolved_words_remain_gap(self):
        score = sample_score()
        self.assertIn("PROVISIONAL_CUE", codes(audit_score(score)))
        score["scenes"][0]["events"][0]["cue"] = {"kind": "word", "word": "channel", "occurrence": 0, "edge": "start"}
        report = audit_score(score)
        self.assertTrue(report["technical_pass"])
        self.assertIn("ALIGNMENT_REQUIRED", codes(report))
        score["scenes"][0]["events"][0]["cue"].update(resolved_ms=2500, alignment_id="fake")
        self.assertIn("ALIGNMENT_INVALID", codes(audit_score(score)))

    def test_licensing_and_provenance_not_inferred(self):
        score = sample_score()
        del score["evidence"][0]["source"]["commercial_use"]
        self.assertIn("PROVENANCE_INVALID", codes(audit_score(score)))
        score = sample_score()
        score["style"]["typography"]["font_url"] = "https://example.org/font.woff2"
        self.assertFalse(audit_score(score)["technical_pass"])
        score = sample_score()
        score["provenance"].pop("test_fixture")
        self.assertIn("UNDECLARED_FIXTURE_OR_FALLBACK", codes(audit_score(score)))

    def test_development_cannot_claim_creative_lock(self):
        score = sample_score()
        score["provenance"]["status"] = "CREATIVE_LOCKED"
        report = audit_score(score)
        self.assertFalse(report["technical_pass"])
        self.assertFalse(report["authority"]["creative_lock"])

    def test_uncertain_evidence_requires_semantic_review(self):
        score = qualitative_score("cache")
        score["evidence"][0]["status"] = "uncertain"
        self.assertIn("UNCERTAINTY_REVIEW_REQUIRED", codes(audit_score(score)))

    def test_retained_identity_state_continuity_and_failures(self):
        score = sample_score()
        first = score["scenes"][0]
        second = deepcopy(first)
        second["id"] = "retained_second"
        second["events"] = []
        for actor in first["actors"]:
            actor["retain"] = actor["id"]
        second["actors"] = deepcopy(first["actors"])
        for actor in second["actors"]:
            actor["initial"].update(first["events"][0]["changes"][actor["id"]])
            if actor["kind"] in ("number", "bar"):
                actor["value_binding"] = "after"
        score["scenes"].append(second)
        self.assertTrue(audit_score(score)["technical_pass"])
        second["actors"][0]["initial"]["highlight"] = 0
        self.assertIn("RETAINED_IDENTITY_INVALID", codes(audit_score(score)))


class PlanQuality(unittest.TestCase):
    def test_all_aspects_valid_deep_copy_and_no_fallback(self):
        for aspect in ASPECTS:
            plan = plan_fixture(aspect=aspect)
            before = deepcopy(plan)
            report = audit_plan(plan)
            self.assertTrue(report["technical_pass"], report)
            self.assertEqual(plan, before)
            self.assertNotIn("LINKED_DATA_VIEW_DRIFT", codes(report))
            self.assertIn("PLAN_TIMING_NOT_WORD_ALIGNED", codes(report))
            self.assertFalse(report["authority"]["creative_lock"])
            json.dumps(report, allow_nan=False)

    def test_mixed_unit_bar_comparison_normalized_truthfully(self):
        plan = plan_fixture(compared_bars())
        report = audit_plan(plan)
        self.assertTrue(report["technical_pass"])
        self.assertNotIn("COMPARISON_SCALE_GEOMETRY", codes(report))
        plan["scenes"][0]["actors"][1]["payload"]["domain"] = [0, 80000]
        self.assertIn("COMPARISON_SCALE_GEOMETRY", codes(audit_plan(plan)))

    def test_axis_domain_bounds_are_not_fabricated_evidence_quantities(self):
        score = compared_bars()
        for record in score["evidence"]:
            record["quantity"].update(unit="count", dimension="count")
        for actor in score["scenes"][0]["actors"]:
            actor["payload"].update(unit="count", dimension="count", domain=[-.5, 50.5])
            actor["initial"]["value"] = 20 if actor["value_binding"] == "before" else 40
        plan = plan_fixture(validate_score(score))
        self.assertTrue(audit_plan(plan)["technical_pass"])
        self.assertNotIn("COMPARISON_SCALE_GEOMETRY", codes(audit_plan(plan)))

    def test_comparison_physical_length_not_just_domain(self):
        plan = plan_fixture(compared_bars())
        plan["scenes"][0]["actors"][1]["geometry"]["width"] = 600
        self.assertIn("COMPARISON_SCALE_GEOMETRY", codes(audit_plan(plan)))

    def test_invalid_linked_interval_or_missing_target_is_error(self):
        for mutation in (lambda p: p["scenes"][0]["tracks"][0].update(end_ms=3001),
                         lambda p: p["scenes"][0].update(tracks=[t for t in p["scenes"][0]["tracks"] if t["actor_id"] != "meter"]),
                         lambda p: p["scenes"][0]["tracks"][0].update(verb="fill")):
            plan = plan_fixture()
            mutation(plan)
            self.assertFalse(audit_plan(plan)["technical_pass"])
            self.assertIn("EVENT_MECHANISM_INVALID", codes(audit_plan(plan)))

    def test_fitted_text_initial_and_updated_states_checked(self):
        score = qualitative_score("cache")
        actor = score["scenes"][0]["actors"][0]
        actor.update(kind="text", payload={"text": "Ready", "purpose": "annotation", "max_lines": 1}, initial={"opacity": 1, "position": "home", "text": "Ready"})
        score["scenes"][0]["events"][0]["changes"]["origin"] = {"text": "Averylongunbreakablefactualannotationthatmustnotoverflow"}
        plan = plan_fixture(validate_score(score))
        report = audit_plan(plan)
        self.assertTrue(report["technical_pass"])
        self.assertIn("TEXT_WIDTH_ESTIMATE", codes(report))
        plan["scenes"][0]["actors"][0]["geometry"].update(lines=["One", "Two", "Three"], height=60)
        self.assertIn("TEXT_LINE_BOUNDS", codes(audit_plan(plan)))

    def test_canvas_bounds_scale_and_update_motion(self):
        plan = plan_fixture()
        actor = plan["scenes"][0]["actors"][0]
        actor["initial"].update(x=1800, scale=2)
        self.assertIn("ACTOR_BOUNDS", codes(audit_plan(plan)))
        plan = plan_fixture()
        plan["scenes"][0]["actors"][0]["geometry"]["font_size"] = 10
        self.assertIn("TEXT_READABILITY_SIZE", codes(audit_plan(plan)))

    def test_contextual_palette_contrast_against_surface(self):
        plan = plan_fixture()
        actor = plan["scenes"][0]["actors"][0]
        actor["role"] = "muted"
        panel = {"id": "backing", "identity": "backing", "kind": "panel", "role": "surface", "label": "Backing", "meaning": "Local text backing", "evidence_ids": [],
                 "layout": {"anchor": "background"}, "payload": {}, "geometry": deepcopy(actor["geometry"]),
                 "initial": {"opacity": 1, "x": actor["initial"]["x"], "y": actor["initial"]["y"]}, "retained": False}
        plan["scenes"][0]["actors"].insert(0, panel)
        plan["style"]["palette"]["muted"] = "#16364B"
        report = audit_plan(plan)
        self.assertIn("TEXT_PALETTE_CONTRAST", codes(report))
        contrast = next(f for f in report["findings"] if f["code"] == "TEXT_PALETTE_CONTRAST")
        self.assertEqual(contrast["observed"]["backing_role"], "surface")
        self.assertEqual(contrast["causal_owner"], "Art Director")

    def test_connector_endpoint_integrity_and_points_bounds(self):
        plan = plan_fixture(qualitative_score("cache"))
        left, right = plan["scenes"][0]["actors"]
        connector = {"id": "arrow", "identity": "arrow", "kind": "connector", "role": "primary", "label": "Causality", "meaning": "Declared causal arrow", "evidence_ids": ["mechanism"],
                     "layout": {"anchor": "context"}, "payload": {"from": "origin", "to": "destination", "arrow": True},
                     "geometry": {"x": 540, "y": 300, "width": 70, "height": 20, "points": [{"x": 0, "y": 10}, {"x": 70, "y": 10}]},
                     "initial": {"opacity": 1, "x": 540, "y": 300, "draw": 1}, "retained": False}
        plan["scenes"][0]["actors"].append(connector)
        self.assertNotIn("CONNECTOR_RELATIONAL_GEOMETRY", codes(audit_plan(plan)))
        connector["initial"]["y"] = 900
        self.assertIn("CONNECTOR_RELATIONAL_GEOMETRY", codes(audit_plan(plan)))
        connector["geometry"]["points"][1]["x"] = 1000
        self.assertIn("PRIMITIVE_POINTS_BOUNDS", codes(audit_plan(plan)))

    def test_precision_rounding_of_evidence_not_certified_as_exact_display(self):
        plan = plan_fixture()
        plan["evidence"][0]["quantity"]["value"] = 20.25
        for actor in plan["scenes"][0]["actors"][:2]:
            actor["initial"]["value"] = 20.25
        for track in plan["scenes"][0]["tracks"]:
            if track["property"] == "value":
                track["from"] = 20.25
        self.assertIn("DISPLAY_ROUNDING_LOSS", codes(audit_plan(plan)))

    def test_transition_outgoing_tail_and_native_dimensions_enforced(self):
        plan = plan_fixture()
        plan["scenes"][0]["transition"]["end_ms"] = 5900
        self.assertFalse(audit_plan(plan)["technical_pass"])
        plan = plan_fixture()
        plan["canvas"]["width"] = 1080
        self.assertIn("PLAN_BINDING_INVALID", codes(audit_plan(plan)))

    def test_unsupported_kind_and_property_never_become_still_card(self):
        plan = plan_fixture()
        plan["scenes"][0]["actors"][0]["kind"] = "dashboard-widget"
        report = audit_plan(plan)
        self.assertFalse(report["technical_pass"])
        self.assertIsNone(report["film_signature"])
        self.assertEqual(report["scene_signatures"], [])

    def test_cross_aspect_reflow_preserves_semantic_links(self):
        plans = [plan_fixture(aspect=aspect) for aspect in ASPECTS]
        report = audit_aspects(plans)
        self.assertTrue(report["technical_pass"], report)
        self.assertNotIn("ASPECT_REFLOW_NOT_EVIDENCED", codes(report))
        self.assertNotIn("ASPECT_SEMANTIC_DRIFT", codes(report))

    def test_cross_aspect_missing_native_plan_and_relation_drift(self):
        plans = [plan_fixture(aspect=aspect) for aspect in ASPECTS]
        self.assertIn("NATIVE_ASPECT_COVERAGE", codes(audit_aspects(plans[:2])))
        plans[1]["scenes"][0]["relations"] = []
        self.assertIn("ASPECT_SEMANTIC_DRIFT", codes(audit_aspects(plans)))

    def test_cross_aspect_repair_paths_preserve_original_submitted_indexes(self):
        plans = [plan_fixture(aspect=aspect) for aspect in ASPECTS]
        plans[0]["canvas"]["width"] = 1
        plans[2]["scenes"][0]["actors"][2]["payload"]["options"] = ["A", "B"]
        report = audit_aspects(plans)
        drift = next(f for f in report["findings"] if f["code"] == "ASPECT_SEMANTIC_DRIFT")
        self.assertEqual(drift["path"], "$.plans[2]")
        self.assertEqual(drift["repair"]["paths"], ["$.plans[2]"])

    def test_output_background_obeys_declared_style_invariant(self):
        plan = plan_fixture()
        plan["output"]["background"] = "#FFFFFF"
        self.assertIn("OUTPUT_BACKGROUND_STYLE_DRIFT", codes(audit_plan(plan)))

    def test_cross_aspect_normalized_scaling_only_warns_not_bogus_rejection(self):
        plans = [plan_fixture(aspect=aspect) for aspect in ASPECTS]
        reference = plans[0]
        for plan in plans[1:]:
            sx, sy = plan["canvas"]["width"] / 1920, plan["canvas"]["height"] / 1080
            for old, actor in zip(reference["scenes"][0]["actors"], plan["scenes"][0]["actors"]):
                for prop, factor in (("x", sx), ("width", sx), ("y", sy), ("height", sy)):
                    actor["geometry"][prop] = old["geometry"][prop] * factor
                actor["initial"].update(x=actor["geometry"]["x"], y=actor["geometry"]["y"])
        report = audit_aspects(plans)
        self.assertTrue(report["technical_pass"])
        self.assertIn("ASPECT_REFLOW_NOT_EVIDENCED", codes(report))

    def test_cross_aspect_payload_and_state_changes_cannot_silently_drift(self):
        plans = [plan_fixture(aspect=aspect) for aspect in ASPECTS]
        plans[1]["scenes"][0]["actors"][2]["payload"]["options"] = ["Other initial", "Other extended"]
        self.assertIn("ASPECT_SEMANTIC_DRIFT", codes(audit_aspects(plans)))

    def test_possible_text_overlap_is_local_structural_warning(self):
        plan = plan_fixture()
        scene = plan["scenes"][0]
        actor = deepcopy(scene["actors"][0])
        actor.update(id="other_readout", identity="other_readout")
        scene["actors"].append(actor)
        self.assertIn("TEXT_GEOMETRY_OVERLAP", codes(audit_plan(plan)))
        actor["initial"]["opacity"] = 0
        self.assertNotIn("TEXT_GEOMETRY_OVERLAP", codes(audit_plan(plan)))

    def test_image_provenance_and_remote_assets_fail_without_fetching(self):
        plan = plan_fixture(qualitative_score("cache"))
        image = deepcopy(plan["scenes"][0]["actors"][0])
        image.update(id="asset", identity="asset", kind="image", payload={"src": "/assets/test.png", "mime": "image/png", "fit": "contain", "source": deepcopy(plan["provenance"]["source"])}, initial={"opacity": 1, "x": 100, "y": 100})
        plan["scenes"][0]["actors"].append(image)
        self.assertTrue(audit_plan(plan)["technical_pass"])
        image["payload"]["source"]["commercial_use"] = False
        self.assertIn("PROVENANCE_INVALID", codes(audit_plan(plan)))
        image["payload"]["source"]["commercial_use"] = True
        image["payload"]["src"] = "https://example.org/test.png"
        self.assertFalse(audit_plan(plan)["technical_pass"])

    def test_move_requires_both_coordinate_tracks_after_lowering(self):
        score = qualitative_score("plant")
        event = score["scenes"][0]["events"][0]
        event["verb"] = "move"
        event["changes"] = {a: {"position": "focus"} for a in event["targets"]}
        plan = plan_fixture(validate_score(score))
        self.assertTrue(audit_plan(plan)["technical_pass"])
        plan["scenes"][0]["tracks"] = [t for t in plan["scenes"][0]["tracks"] if t["property"] != "y"]
        self.assertIn("POSITION_TRACK_PAIR_MISSING", codes(audit_plan(plan)))

    def test_retained_plan_terminal_state_and_kind_semantics(self):
        score = qualitative_score("plant")
        first = score["scenes"][0]
        second = deepcopy(first)
        second["id"] = "again"
        second["events"] = []
        for actor in first["actors"]:
            actor["retain"] = actor["id"]
        second["actors"] = deepcopy(first["actors"])
        for actor in second["actors"]:
            actor["initial"]["fill"] = 1
        score["scenes"].append(second)
        plan = plan_fixture(validate_score(score))
        self.assertTrue(audit_plan(plan)["technical_pass"])
        plan["scenes"][1]["actors"][0]["initial"]["fill"] = 0
        self.assertIn("RETAINED_IDENTITY_INVALID", codes(audit_plan(plan)))


if __name__ == "__main__":
    unittest.main()
