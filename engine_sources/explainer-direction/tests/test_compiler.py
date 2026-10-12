"""Compiler-only tests. All evidence/audio declarations here are TEST FIXTURES.

No authoring, provider, quality or renderer module is needed for these tests.
These tests do not claim real inference, TTS, perceptual review or creative lock.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from explainer_direction.compiler import compile_score
from explainer_direction.contracts import (
    ALIGNMENT_SCHEMA, ASPECTS, CAPABILITIES, PLAN_JSON_SCHEMA, ScoreError,
    sample_score, validate_plan, validate_score,
)


def actor(aid, kind="shape", **overrides):
    payloads = {
        "shape": {"shape": "circle"}, "text": {"text": "Flow", "purpose": "label"},
        "number": {"unit": "L", "dimension": "volume", "decimals": 0},
        "bar": {"unit": "L", "dimension": "volume", "domain": [0, 40], "orientation": "auto"},
        "axis": {"unit": "L", "dimension": "volume", "domain": [0, 40], "orientation": "auto", "ticks": 4},
        "connector": {"from": "a", "to": "b", "arrow": True, "routing": "elbow"},
        "selector": {"options": ["Initial", "Extended"]},
        "particles": {"count": 8, "arrangement": "grid", "illustrative": True},
        "panel": {}, "group": {"children": ["a", "b"]},
        "image": {"src": "/artwork/compiler-test.png", "mime": "image/png", "fit": "contain",
                  "source": deepcopy(sample_score()["provenance"]["source"])},
    }
    extras = {"shape": {"variant": "circle", "draw": 0, "fill": 0}, "text": {"text": "Flow"},
              "number": {"value": 20}, "bar": {"value": 20, "fill": .5}, "axis": {"draw": 0},
              "connector": {"draw": 0}, "selector": {"selection": 0},
              "particles": {"flow": 0, "fill": 0}, "panel": {"fill": 0}}
    result = {"id": aid, "kind": kind, "role": "primary", "label": "Flow", "meaning": "Illustrative mechanism",
              "evidence_ids": ["before", "after"], "layout": {"anchor": "primary"},
              "payload": payloads[kind], "initial": {"opacity": 1, "position": "home", "reveal": 0,
              "scale": 1, "rotation": 0, "highlight": 0, **extras.get(kind, {})}}
    if kind in ("number", "bar"):
        result["value_binding"] = "before"
    result.update(overrides)
    return result


def score_for(kind="shape"):
    score = sample_score()
    scene = score["scenes"][0]
    scene.update(actors=[actor("target", kind)], relations=[], events=[],
                 composition={"flow": "auto", "density": "balanced"}, timing="authored")
    if kind in ("connector", "group"):
        scene["actors"] += [actor("a"), actor("b")]
        scene["relations"] = [{"id": "process", "kind": "sequence", "from": "a", "to": "b",
                                "evidence_ids": ["before"]}]
    return score


def event(eid, changes, *, verb="update", ms=100, duration=300, dependencies=()):
    result = {"id": eid, "verb": verb, "targets": list(changes),
              "cue": {"kind": "absolute", "ms": ms, "basis": "authored"},
              "duration_ms": duration, "dependencies": list(dependencies), "easing": "ease_in_out",
              "changes": changes, "claim_ids": ["before", "after"], "rationale": "Show a motivated linked state change"}
    bindings = {aid: "after" for aid, props in changes.items() if "value" in props}
    if bindings:
        result["value_bindings"] = bindings
    return result


class RotationAndProfileTests(unittest.TestCase):
    def test_rotation_and_shape_proportion_lower_natively(self):
        import math

        for aspect in ASPECTS:
            score = score_for()
            subject = score["scenes"][0]["actors"][0]
            subject["payload"] = {"shape": "diamond", "aspect_ratio": .1}
            subject["initial"].update(variant="diamond", rotation=-45)
            score["scenes"][0]["events"] = [event("orient", {"target": {"rotation": 90}}, verb="rotate")]
            plan = compile_score(score, aspect)
            target = actors_of(plan)["target"]
            geometry = target["geometry"]
            self.assertAlmostEqual(geometry["width"] / geometry["height"], .1)
            self.assertLess(math.hypot(geometry["width"], geometry["height"]),
                            min(plan["canvas"].values()))
            track, = plan["scenes"][0]["tracks"]
            self.assertEqual((track["property"], track["from"], track["to"], track["verb"]),
                             ("rotation", -45, 90, "rotate"))
            validate_plan(plan)

    def test_rotation_requires_initialized_finite_bounded_state(self):
        for value in (3601, -3601, float("nan"), float("inf")):
            score = score_for()
            score["scenes"][0]["events"] = [event("orient", {"target": {"rotation": value}}, verb="rotate")]
            with self.assertRaises(ScoreError):
                validate_score(score)
        score = score_for()
        del score["scenes"][0]["actors"][0]["initial"]["rotation"]
        score["scenes"][0]["events"] = [event("orient", {"target": {"rotation": 90}}, verb="rotate")]
        with self.assertRaises(ScoreError):
            validate_score(score)

    def test_shape_proportion_rejects_unsupported_values(self):
        for value in (0, .09, 10.01, float("inf")):
            score = score_for()
            score["scenes"][0]["actors"][0]["payload"]["aspect_ratio"] = value
            with self.assertRaises(ScoreError):
                validate_score(score)

    def test_rotation_cannot_reverse_source_bound_physical_ordering(self):
        for initial in (False, True):
            score = score_for("group")
            scene = score["scenes"][0]
            scene["relations"] = [{"id": "ordered", "kind": "left_of", "from": "a",
                                  "to": "b", "evidence_ids": ["before"]}]
            if initial:
                scene["actors"][0]["initial"]["rotation"] = 180
            else:
                scene["events"] = [event("orient", {"target": {"rotation": 180}}, verb="rotate")]
            with self.assertRaisesRegex(ScoreError, "physical ordering group"):
                validate_score(score)


class AttachedConnectorActions(unittest.TestCase):
    def test_connector_cannot_be_moved_as_if_it_were_flowing_material(self):
        for properties in ({"position": "end"}, {"scale": 2}, {"rotation": 90}):
            score = score_for("connector")
            score["scenes"][0]["events"] = [event("bad_material_flow", {"target": properties})]
            with self.assertRaisesRegex(ScoreError, "unsupported kind/property/verb"):
                validate_score(score)

    def test_connector_starts_attached_not_in_an_arbitrary_screen_pose(self):
        for properties in ({"position": "start"}, {"scale": 2}, {"rotation": 90}):
            score = score_for("connector")
            score["scenes"][0]["actors"][0]["initial"].update(properties)
            with self.assertRaisesRegex(ScoreError, "expected constant"):
                validate_score(score)


class PhysicalOrdering(unittest.TestCase):
    def spatial_score(self):
        score = score_for("shape")
        scene = score["scenes"][0]
        scene["actors"] = [actor("ceiling_sensor"), actor("floor_controller")]
        for a in scene["actors"]:
            a["payload"]["shape"] = a["initial"]["variant"] = "rect"
        scene["relations"] = [
            {"id": "signal_up", "kind": "flows_to", "from": "floor_controller",
             "to": "ceiling_sensor", "evidence_ids": ["before"]},
            {"id": "physical_height", "kind": "above", "from": "ceiling_sensor",
             "to": "floor_controller", "evidence_ids": ["before"]},
        ]
        return score

    def test_physical_height_does_not_flip_to_match_signal_direction_or_aspect(self):
        for aspect in ASPECTS:
            plan = compile_score(self.spatial_score(), aspect)
            items = actors_of(plan)
            high, low = items["ceiling_sensor"], items["floor_controller"]
            self.assertLess(high["initial"]["y"] + high["geometry"]["height"] / 2,
                            low["initial"]["y"] + low["geometry"]["height"] / 2)
            self.assertTrue(any("physical axes preserved" in c for c in plan["scenes"][0]["constraints"]))

    def test_left_and_right_remain_physical_axes_in_portrait(self):
        score = self.spatial_score()
        score["scenes"][0]["relations"][1]["kind"] = "left_of"
        for aspect in ASPECTS:
            items = actors_of(compile_score(score, aspect))
            left, right = items["ceiling_sensor"], items["floor_controller"]
            self.assertLess(left["initial"]["x"] + left["geometry"]["width"] / 2,
                            right["initial"]["x"] + right["geometry"]["width"] / 2)

    def test_contradictory_physical_ordering_fails_instead_of_reversing_process_edges(self):
        score = self.spatial_score()
        score["scenes"][0]["relations"].append({
            "id": "contradiction", "kind": "above", "from": "floor_controller",
            "to": "ceiling_sensor", "evidence_ids": ["before"],
        })
        with self.assertRaisesRegex(ScoreError, "dependency cycle"):
            compile_score(score, "9:16")

    def test_global_pose_cannot_override_physical_order(self):
        score = self.spatial_score()
        score["scenes"][0]["actors"][0]["initial"]["position"] = "end"
        with self.assertRaisesRegex(ScoreError, "fitted home pose"):
            compile_score(score, "9:16")
        score["scenes"][0]["actors"][0]["initial"]["position"] = "home"
        score["scenes"][0]["events"] = [event("break_height", {"ceiling_sensor": {"position": "end"}})]
        with self.assertRaisesRegex(ScoreError, "shared physical group"):
            validate_score(score)

    def test_tampered_native_plan_is_rejected(self):
        plan = compile_score(self.spatial_score(), "9:16")
        items = actors_of(plan)
        a, b = items["ceiling_sensor"], items["floor_controller"]
        a["initial"]["y"], b["initial"]["y"] = b["initial"]["y"], a["initial"]["y"]
        with self.assertRaisesRegex(ScoreError, "physical ordering"):
            validate_plan(plan)

    def test_rectangular_entities_are_not_forced_into_tiny_square_icons(self):
        plan = compile_score(self.spatial_score(), "16:9")
        rectangle = actors_of(plan)["ceiling_sensor"]["geometry"]
        self.assertGreater(rectangle["width"], rectangle["height"] * 2)


def reported(score):
    """Explicit UNEVEN token intervals; shape fixture, not actual voice proof."""
    words = score["scenes"][0]["narration"].split()
    intervals = [(73, 190), (247, 601), (670, 712), (813, 901),
                 (1311, 1729), (1791, 2063), (2301, 2709)]
    assert len(words) == len(intervals)
    return {"schema": ALIGNMENT_SCHEMA, "id": "reported_fixture",
            "source": {"provider": "test-fixture-only", "method": "provider_word_timestamps", "audio_sha256": "a" * 64},
            "scenes": [{"scene_id": score["scenes"][0]["id"], "duration_ms": 6000,
                        "words": [{"word": word, "start_ms": start, "end_ms": end}
                                  for word, (start, end) in zip(words, intervals)]}]}


def actors_of(plan, index=0):
    return {item["id"]: item for item in plan["scenes"][index]["actors"]}


def terminal_scene(score):
    first = score["scenes"][0]
    for item in first["actors"]:
        item["retain"] = item["id"]
    second = deepcopy(first)
    second["id"] = "continuation"
    for item in second["actors"]:
        for action in first["events"]:
            item["initial"].update(action["changes"].get(item["id"], {}))
            binding = action.get("value_bindings", {}).get(item["id"])
            if binding:
                item["value_binding"] = binding
    second["events"] = []
    second["composition"]["flow"] = "column"
    score["scenes"].append(second)
    return score


def state_at(scene, ms):
    """Independent plan consumer recomputes state from initial on EACH seek."""
    state = {item["id"]: deepcopy(item["initial"]) for item in scene["actors"]}
    for track in sorted(scene["tracks"], key=lambda t: (t["start_ms"], t["end_ms"])):
        if ms < track["start_ms"]:
            continue
        prop, aid = track["property"], track["actor_id"]
        start, end = track["start_ms"], track["end_ms"]
        if ms >= end or start == end:
            value = track["to"]
        elif track["easing"] == "step":
            value = track["from"]
        else:
            t = (ms - start) / (end - start)
            t = {"linear": lambda x: x, "ease_in": lambda x: x * x,
                 "ease_out": lambda x: 1 - (1 - x) ** 2,
                 "ease_in_out": lambda x: 2 * x * x if x < .5 else 1 - (-2 * x + 2) ** 2 / 2}[track["easing"]](t)
            value = track["from"] + (track["to"] - track["from"]) * t
        state[aid][prop] = value
    return state


class CompilerTests(unittest.TestCase):
    def test_independent_topics_native_validated_json_and_deep_copy(self):
        for topic in ("water", "energy", "travel"):
            score = sample_score(topic)
            snapshot = deepcopy(score)
            for aspect, (width, height) in ASPECTS.items():
                with self.subTest(topic=topic, aspect=aspect):
                    plan = compile_score(score, aspect)
                    self.assertEqual(plan, validate_plan(plan))
                    self.assertEqual(plan, json.loads(json.dumps(plan, allow_nan=False)))
                    self.assertEqual(plan, compile_score(score, aspect))
                    self.assertEqual(plan["canvas"], {"width": width, "height": height})
                    self.assertEqual(plan["direction"]["status"], "DEVELOPMENT_PREFLIGHT")
                    self.assertEqual(plan["direction"]["timing"], "provisional")
                    self.assertEqual(plan["duration_ms"], 6000)
                    self.assertEqual(plan["style"], score["style"])
                    self.assertEqual(plan["evidence"], score["evidence"])
                    self.assertEqual(plan["scenes"][0]["relations"], score["scenes"][0]["relations"])
                    digest = hashlib.sha256(json.dumps(score, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
                    self.assertEqual(plan["direction"]["score_sha256"], digest)
                    plan["scenes"][0]["actors"][0]["initial"]["value"] = -1
                    plan["style"]["family"] = "ember"
            self.assertEqual(score, snapshot)

    def test_native_composition_is_not_crop_or_scaled_landscape(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["actors"] = [actor("a"), actor("b"), actor("c")]
        landscape, portrait, square = [actors_of(compile_score(score, aspect)) for aspect in ASPECTS]
        self.assertLess(landscape["a"]["geometry"]["x"], landscape["b"]["geometry"]["x"])
        self.assertAlmostEqual(landscape["a"]["geometry"]["y"], landscape["b"]["geometry"]["y"])
        self.assertLess(portrait["a"]["geometry"]["y"], portrait["b"]["geometry"]["y"])
        self.assertAlmostEqual(portrait["a"]["geometry"]["x"], portrait["b"]["geometry"]["x"])
        self.assertLess(square["a"]["geometry"]["x"], square["b"]["geometry"]["x"])
        self.assertLess(square["a"]["geometry"]["y"], square["c"]["geometry"]["y"])

    def test_qualitative_topics_share_primitives_not_narration_templates(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["actors"] = [actor("a"), actor("b"), actor("link", "connector")]
        scene["relations"] = [{"id": "cause", "kind": "causes", "from": "a", "to": "b", "evidence_ids": ["before"]}]
        scene["events"] = [event("connect", {"link": {"draw": 1}}, verb="connect")]
        for narration in ("Roots support transport through the plant.", "Cached objects avoid repeated network retrieval."):
            changed = deepcopy(score)
            changed["title"] = narration
            changed["scenes"][0]["narration"] = narration
            for aspect in ASPECTS:
                left, right = compile_score(score, aspect), compile_score(changed, aspect)
                self.assertEqual(actors_of(left), actors_of(right))
                self.assertEqual(left["scenes"][0]["tracks"], right["scenes"][0]["tracks"])

    def test_graph_direction_wins_over_input_array_order(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["actors"] = [actor("b"), actor("a")]
        scene["relations"] = [{"id": "order", "kind": "sequence", "from": "a", "to": "b", "evidence_ids": ["before"]}]
        for flow in ("auto", "row", "column"):
            scene["composition"]["flow"] = flow
            for aspect in ASPECTS:
                resolved = actors_of(compile_score(score, aspect))
                coordinate = "x" if flow == "row" or (flow == "auto" and aspect == "16:9") else "y"
                self.assertLess(resolved["a"]["geometry"][coordinate], resolved["b"]["geometry"][coordinate])

    def test_authored_actor_hint_rank_and_focus(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["actors"] = [actor("a", layout={"anchor": "primary", "rank": 2, "arrangement": "column"}),
                           actor("b", layout={"anchor": "primary", "rank": 0})]
        scene["composition"]["focus"] = "b"
        resolved = actors_of(compile_score(score, "16:9"))
        self.assertLess(resolved["b"]["geometry"]["y"], resolved["a"]["geometry"]["y"])
        scene["actors"][1]["layout"]["arrangement"] = "row"
        with self.assertRaisesRegex(ScoreError, "conflicting actor arrangement"):
            compile_score(score, "16:9")

    def test_composable_groups_containment_and_absolute_child_geometry(self):
        for aspect in ASPECTS:
            score = score_for("group")
            score["scenes"][0]["actors"][0]["layout"]["arrangement"] = "column"
            score["scenes"][0]["events"] = [event("reframe", {"target": {"position": "context", "scale": .8}}, verb="reframe")]
            plan = compile_score(score, aspect)
            resolved = actors_of(plan)
            outer = resolved["target"]["geometry"]
            for aid in ("a", "b"):
                inner = resolved[aid]["geometry"]
                self.assertGreater(inner["x"], outer["x"])
                self.assertGreater(inner["y"], outer["y"])
                self.assertLess(inner["x"] + inner["width"], outer["x"] + outer["width"])
                self.assertLess(inner["y"] + inner["height"], outer["y"] + outer["height"])
            self.assertEqual({t["property"] for t in plan["scenes"][0]["tracks"]}, {"x", "y", "scale"})
            self.assertTrue(all(t["actor_id"] == "target" for t in plan["scenes"][0]["tracks"]))
            # Ordinary panels can contain actors too; not just finished group widgets.
            score = score_for("panel")
            score["scenes"][0]["actors"].append(actor("inside"))
            score["scenes"][0]["relations"] = [{"id": "contain", "kind": "contains", "from": "target", "to": "inside", "evidence_ids": []}]
            resolved = actors_of(compile_score(score, aspect))
            self.assertGreater(resolved["inside"]["geometry"]["x"], resolved["target"]["geometry"]["x"])

    def test_background_motion_and_caption_safe_band(self):
        score = score_for("panel")
        scene = score["scenes"][0]
        scene["actors"][0]["layout"] = {"anchor": "background"}
        scene["actors"] += [actor("illustration"), actor("caption", "text", layout={"anchor": "caption"})]
        scene["events"] = [event("background", {"target": {"position": "end", "reveal": 1, "fill": 1, "opacity": .4}})]
        for aspect, (width, height) in ASPECTS.items():
            plan = compile_score(score, aspect)
            resolved = actors_of(plan)
            background = resolved["target"]["geometry"]
            self.assertEqual([background[k] for k in ("x", "y", "width", "height")], [0, 0, width, height])
            cap, illustration = resolved["caption"]["geometry"], resolved["illustration"]["geometry"]
            self.assertLess(illustration["y"] + illustration["height"], cap["y"])
            self.assertEqual(len(plan["scenes"][0]["tracks"]), 5)
            movement = [track for track in plan["scenes"][0]["tracks"] if track["property"] in ("x", "y")]
            self.assertTrue(any(track["from"] != track["to"] for track in movement))

    def test_shape_metadata_does_not_require_an_unrendered_text_box(self):
        score = score_for("shape")
        scene = score["scenes"][0]
        description = "An extended source-grounded descriptive label for the underlying illustrative process"
        scene["actors"] = [actor(f"shape_{index}", label=description) for index in range(4)]
        scene["actors"].append(actor("caption", "text", label=description,
                                    payload={"text": description, "purpose": "label", "max_lines": 3},
                                    initial={"opacity": 1, "position": "home", "scale": 1,
                                             "highlight": 0, "text": description},
                                    layout={"anchor": "caption"}))
        scene["composition"]["flow"] = "column"
        for aspect in ASPECTS:
            resolved = actors_of(compile_score(score, aspect))
            self.assertNotIn("font_size", resolved["shape_0"]["geometry"])
            self.assertEqual(resolved["shape_0"]["label"], description)
            self.assertGreaterEqual(resolved["caption"]["geometry"]["font_size"], 20)
            self.assertIn("lines", resolved["caption"]["geometry"])

    def test_axis_plot_orientation_and_connector_local_points(self):
        for aspect in ASPECTS:
            score = score_for("axis")
            score["scenes"][0]["actors"].append(actor("mark", "bar"))
            score["scenes"][0]["composition"]["flow"] = "plot"
            plan = compile_score(score, aspect)
            orientation = "vertical" if aspect == "9:16" else "horizontal"
            for item in plan["scenes"][0]["actors"]:
                self.assertEqual(item["payload"]["orientation"], orientation)
            self.assertEqual(len(actors_of(plan)["target"]["geometry"]["points"]), 2)
            connector = actors_of(compile_score(score_for("connector"), aspect))["target"]["geometry"]
            self.assertEqual(len(connector["points"]), 4)
            for point in connector["points"]:
                self.assertGreaterEqual(point["x"], 0)
                self.assertGreaterEqual(point["y"], 0)
                self.assertLessEqual(point["x"], connector["width"])
                self.assertLessEqual(point["y"], connector["height"])

    def test_all_admitted_kind_verb_property_bindings_lower_without_flattening(self):
        values = {"opacity": .7, "reveal": 1, "scale": 1.1, "rotation": 90, "highlight": 1, "position": "focus",
                  "draw": 1, "fill": 1, "flow": .8, "text": "Linked flow", "value": 40,
                  "selection": 1, "variant": "diamond"}
        count = 0
        for kind, properties in CAPABILITIES["event_properties"].items():
            for verb, admitted in CAPABILITIES["verb_properties"].items():
                for prop in set(properties) & set(admitted):
                    count += 1
                    for aspect in ASPECTS:
                        with self.subTest(kind=kind, verb=verb, prop=prop, aspect=aspect):
                            score = score_for(kind)
                            score["scenes"][0]["events"] = [event("action", {"target": {prop: values[prop]}}, verb=verb)]
                            plan = compile_score(score, aspect)
                            target = actors_of(plan)["target"]
                            self.assertEqual(target["kind"], kind)
                            tracks = plan["scenes"][0]["tracks"]
                            self.assertEqual({t["property"] for t in tracks}, {"x", "y"} if prop == "position" else {prop})
                            self.assertTrue(all(t["verb"] == verb for t in tracks))
                            if prop in ("text", "selection", "variant"):
                                self.assertEqual(tracks[0]["easing"], "step")
        self.assertEqual(count, 308)

    def test_synchronized_linked_state_tracks_and_backward_seek_contract(self):
        scene = compile_score(sample_score(), "16:9")["scenes"][0]
        linked = [t for t in scene["tracks"] if t["event_id"] == "linked_change"]
        self.assertEqual({(t["start_ms"], t["end_ms"]) for t in linked}, {(2100, 3000)})
        self.assertEqual({(t["actor_id"], t["property"]) for t in linked},
                         {("readout", "value"), ("readout", "highlight"), ("meter", "value"), ("meter", "fill"), ("stage", "selection")})
        self.assertEqual([t for t in scene["tracks"] if t["event_id"] == "read_change"], [])
        self.assertEqual(state_at(scene, 2550)["readout"]["value"], 30)
        self.assertEqual(state_at(scene, 2550)["meter"]["fill"], .75)
        self.assertEqual(state_at(scene, 2550)["stage"]["selection"], 0)
        forward = state_at(scene, 3000)
        self.assertEqual(forward["stage"]["selection"], 1)
        self.assertEqual(state_at(scene, 0)["readout"]["value"], 20)
        self.assertEqual(state_at(scene, 3000), forward)

    def test_true_reported_word_edges_and_no_fraction_relabelling(self):
        score = sample_score()
        original = deepcopy(score)
        score["scenes"][0]["events"][0]["cue"] = {"kind": "word", "word": "second", "occurrence": 0, "edge": "end", "offset_ms": 13}
        with self.assertRaisesRegex(ScoreError, "actual reported alignment"):
            compile_score(score, "16:9")
        timing = reported(score)
        plan = compile_score(score, "16:9", alignment=timing)
        self.assertEqual(plan["scenes"][0]["events"][0]["start_ms"], 1742)
        self.assertNotIn("alignment", score)
        self.assertEqual(score["scenes"][0]["duration_ms"], original["scenes"][0]["duration_ms"])
        self.assertTrue(any("audio_sha256=" in c for c in plan["scenes"][0]["constraints"]))
        score["scenes"][0]["events"][1]["cue"] = {"kind": "word", "word": "opens", "occurrence": 0, "edge": "end"}
        self.assertEqual(compile_score(score, "16:9", alignment=timing)["direction"]["timing"], "aligned")
        score["scenes"][0]["events"][0]["cue"] = original["scenes"][0]["events"][0]["cue"]
        self.assertEqual(compile_score(score, "16:9", alignment=timing)["direction"]["timing"], "provisional")

    def test_reported_alignment_conflicts_tokens_duration_and_resolved_time_reject(self):
        score = sample_score()
        timing = reported(score)
        bad = deepcopy(timing)
        bad["scenes"][0]["words"][0]["word"] = "fabricated"
        with self.assertRaisesRegex(ScoreError, "complete narration"):
            compile_score(score, "16:9", alignment=bad)
        bad = deepcopy(timing)
        bad["scenes"][0]["duration_ms"] = 6100
        with self.assertRaisesRegex(ScoreError, "bind_alignment"):
            compile_score(score, "16:9", alignment=bad)
        score["alignment"] = timing
        bad = deepcopy(timing)
        bad["id"] = "other"
        with self.assertRaisesRegex(ScoreError, "conflicts"):
            compile_score(score, "16:9", alignment=bad)
        score["scenes"][0]["events"][0]["cue"] = {"kind": "word", "word": "second", "occurrence": 0, "edge": "start",
                                                     "resolved_ms": 999, "alignment_id": timing["id"]}
        with self.assertRaisesRegex(ScoreError, "actual reported interval"):
            compile_score(score, "16:9")

    def test_dependency_delay_and_chronological_terminal_from_values(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["events"] = [event("last", {"target": {"highlight": .2}}, ms=0, dependencies=["first"]),
                           event("first", {"target": {"highlight": 1}}, ms=500)]
        plan = compile_score(score, "1:1")
        actions = plan["scenes"][0]["events"]
        self.assertEqual([(a["id"], a["start_ms"], a["end_ms"]) for a in actions], [("first", 500, 800), ("last", 800, 1100)])
        self.assertEqual([(t["from"], t["to"]) for t in plan["scenes"][0]["tracks"]], [(0, 1), (1, .2)])
        self.assertTrue(any("dependency_delay_ms=800" in c for c in plan["scenes"][0]["constraints"]))

    def test_long_dependency_chain_without_timers(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["events"] = [event("action_" + str(i), {"target": {"highlight": i % 2}}, ms=0, duration=10,
                                 dependencies=[] if i == 0 else ["action_" + str(i - 1)]) for i in range(400)]
        result = compile_score(score, "16:9")
        self.assertEqual(result["scenes"][0]["events"][-1]["end_ms"], 4000)
        self.assertEqual(len(result["scenes"][0]["tracks"]), 400)

    def test_ambiguous_writes_rechecked_after_word_resolution(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["events"] = [event("a", {"target": {"highlight": 1}}, ms=1100, duration=700),
                           event("b", {"target": {"highlight": .5}}, duration=0)]
        scene["events"][1]["cue"] = {"kind": "word", "word": "second", "occurrence": 0, "edge": "start"}
        self.assertEqual(validate_score(score), score)  # unresolved authoring is legal
        with self.assertRaisesRegex(ScoreError, "ambiguous"):
            compile_score(score, "16:9", alignment=reported(score))
        scene["events"][1] = event("b", {"target": {"fill": .5}}, ms=1200)
        self.assertEqual(len(compile_score(score, "16:9")["scenes"][0]["tracks"]), 2)

    def test_transition_outgoing_tails_and_retained_terminal_state_native_reflow(self):
        score = terminal_scene(sample_score())
        for kind in ("cut", "hold", "fade", "wipe"):
            transition = {"kind": kind, "duration_ms": 400 if kind in ("fade", "wipe") else 0}
            if kind == "wipe":
                transition["direction"] = "left"
            score["scenes"][0]["transition"] = transition
            for aspect in ASPECTS:
                plan = compile_score(score, aspect)
                first, second = plan["scenes"]
                self.assertEqual((first["start_ms"], first["end_ms"], second["start_ms"], second["end_ms"]), (0, 6000, 6000, 12000))
                self.assertEqual(first["transition"]["start_ms"], 6000 - transition["duration_ms"])
                self.assertEqual(first["transition"]["end_ms"], 6000)
                self.assertTrue(all(not a["retained"] for a in first["actors"]))
                self.assertTrue(all(a["retained"] for a in second["actors"]))
                self.assertEqual(actors_of(plan, 1)["readout"]["initial"]["value"], 40)
                self.assertEqual(plan["duration_ms"], 12000)
                self.assertEqual(first["actors"][0]["payload"], second["actors"][0]["payload"])
        score["scenes"][1]["actors"][0]["initial"]["value"] = 20
        score["scenes"][1]["actors"][0]["value_binding"] = "before"
        with self.assertRaisesRegex(ScoreError, "previous terminal"):
            compile_score(score, "16:9")

    def test_retained_morphed_shape_keeps_terminal_variant(self):
        score = score_for()
        score["scenes"][0]["events"] = [event("morph", {"target": {"variant": "hexagon"}}, verb="morph")]
        score = terminal_scene(score)
        resolved = actors_of(compile_score(score, "9:16"), 1)["target"]
        self.assertEqual(resolved["initial"]["variant"], "hexagon")
        self.assertEqual(resolved["payload"]["shape"], "circle")

    def test_position_lowers_two_explicit_tracks_at_one_clock(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["actors"][0]["initial"]["position"] = "start"
        scene["events"] = [event("move", {"target": {"position": "end"}}, verb="move")]
        for aspect in ASPECTS:
            plan = compile_score(score, aspect)
            target = actors_of(plan)["target"]
            anchors = target["geometry"]["anchors"]
            self.assertEqual(target["initial"]["x"], anchors["start"]["x"])
            self.assertEqual(target["initial"]["y"], anchors["start"]["y"])
            self.assertNotIn("position", target["initial"])
            for track in plan["scenes"][0]["tracks"]:
                prop = track["property"]
                self.assertEqual(track["from"], anchors["start"][prop])
                self.assertEqual(track["to"], anchors["end"][prop])
                self.assertEqual((track["start_ms"], track["end_ms"]), (100, 400))

    def test_fit_future_text_states_and_long_unicode_without_truncation(self):
        score = score_for("text")
        scene = score["scenes"][0]
        future = "Transport pathways are linked to the changing conditions, not autonomous decoration."
        scene["events"] = [event("words", {"target": {"text": future}})]
        for aspect in ASPECTS:
            resolved = actors_of(compile_score(score, aspect))["target"]
            self.assertGreaterEqual(resolved["geometry"]["font_size"], 20)
            self.assertEqual(compile_score(score, aspect)["scenes"][0]["tracks"][0]["to"], future)
        scene["actors"][0]["initial"]["text"] = "水流机制与路径同步变化"
        self.assertEqual("".join(actors_of(compile_score(score, "1:1"))["target"]["geometry"]["lines"]), "水流机制与路径同步变化")
        scene["actors"][0]["payload"]["max_lines"] = 1
        scene["events"][0]["changes"]["target"]["text"] = "Unrepresentable " * 300
        with self.assertRaisesRegex(ScoreError, "cannot fit all states"):
            compile_score(score, "16:9")

    def test_number_precision_and_missing_data_units_fail_closed(self):
        score = score_for("number")
        score["evidence"][0]["quantity"]["value"] = 20.25
        score["scenes"][0]["actors"][0]["initial"]["value"] = 20.25
        with self.assertRaisesRegex(ScoreError, "round away evidence"):
            compile_score(score, "16:9")
        score["scenes"][0]["actors"][0]["payload"]["decimals"] = 2
        self.assertEqual(actors_of(compile_score(score, "16:9"))["target"]["geometry"]["lines"], ["20.25 L"])
        del score["scenes"][0]["actors"][0]["payload"]["unit"]
        with self.assertRaises(ScoreError):
            compile_score(score, "16:9")

    def test_comparison_semantics_proximity_and_compatible_units(self):
        score = score_for("number")
        scene = score["scenes"][0]
        scene["actors"].append(actor("other", "number"))
        scene["actors"][1]["initial"]["value"] = 40
        scene["actors"][1]["value_binding"] = "after"
        scene["relations"] = [{"id": "compare", "kind": "comparison", "from": "target", "to": "other", "evidence_ids": ["before", "after"]}]
        for aspect in ASPECTS:
            self.assertEqual(compile_score(score, aspect)["scenes"][0]["relations"], scene["relations"])
        score["evidence"][1]["comparison"]["conditions"]["basis"] = "different mechanism"
        with self.assertRaisesRegex(ScoreError, "identical explicit group"):
            compile_score(score, "16:9")

    def test_cycle_feedback_is_radial_but_containment_cycles_fail(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["actors"] = [actor("a"), actor("b"), actor("c")]
        scene["relations"] = [{"id": "rel_" + left, "kind": "causes", "from": left, "to": right, "evidence_ids": ["before"]}
                              for left, right in (("a", "b"), ("b", "c"), ("c", "a"))]
        plan = compile_score(score, "1:1")
        self.assertTrue(any("radial feedback" in c for c in plan["scenes"][0]["constraints"]))
        for relation in scene["relations"]:
            relation["kind"] = "contains"
        with self.assertRaisesRegex(ScoreError, "cyclic containment"):
            compile_score(score, "16:9")

    def test_unknown_capabilities_dependencies_provenance_and_aspects_reject(self):
        mutations = [lambda s: s["scenes"][0]["actors"][0].update(kind="humanoid"),
                     lambda s: s["scenes"][0]["actors"][0]["initial"].update(perspective=1),
                     lambda s: s["scenes"][0]["events"][0].update(verb="dance"),
                     lambda s: s["scenes"][0]["events"][0].update(easing="elastic"),
                     lambda s: s["scenes"][0]["events"][0].update(dependencies=["missing"]),
                     lambda s: s["provenance"].update(status="CREATIVE_LOCKED"),
                     lambda s: s["evidence"][0]["source"].update(commercial_use=False)]
        for mutation in mutations:
            score = sample_score()
            mutation(score)
            with self.assertRaises(ScoreError):
                compile_score(score, "16:9")
        for aspect in ("4:3", None, [], {"aspect": "16:9"}):
            with self.assertRaises(ScoreError):
                compile_score(sample_score(), aspect)
        for source in ("https://example.com/secret.png", "/artwork/../secret.png"):
            score = score_for("image")
            score["scenes"][0]["actors"][0]["payload"]["src"] = source
            with self.assertRaises(ScoreError):
                compile_score(score, "16:9")

    def test_p8_hashes_carried_but_not_certified_and_palette_does_not_drive_geometry(self):
        score = sample_score()
        before = compile_score(score, "16:9")
        score["provenance"].update(mode="p8_bound", status="P8_SEMANTIC_BOUND",
                                   p8={"state_hash": "1" * 64, "board_hash": "2" * 64})
        del score["provenance"]["test_fixture"]
        score["style"]["family"] = "ember"
        score["style"]["palette"]["primary"] = "#FFA000"
        after = compile_score(score, "16:9")
        self.assertEqual(after["provenance"]["p8"], score["provenance"]["p8"])
        self.assertEqual(after["direction"]["status"], "P8_SEMANTIC_BOUND")
        self.assertEqual(actors_of(before), actors_of(after))
        self.assertNotEqual(before["direction"]["score_sha256"], after["direction"]["score_sha256"])

    def test_retention_rechecked_when_unknown_word_timing_becomes_known(self):
        score = sample_score()
        score["scenes"][0]["events"][0]["cue"] = {"kind": "word", "word": "second", "occurrence": 0, "edge": "start"}
        score = terminal_scene(score)
        score["scenes"][1]["actors"][0]["initial"]["value"] = 20
        score["scenes"][1]["actors"][0]["value_binding"] = "before"
        self.assertEqual(validate_score(score), score)
        timing = reported(score)
        timing["scenes"].append({**deepcopy(timing["scenes"][0]), "scene_id": "continuation"})
        with self.assertRaisesRegex(ScoreError, "previous terminal"):
            compile_score(score, "16:9", alignment=timing)

    def test_all_easings_holds_and_authored_timing_are_explicit(self):
        score = score_for()
        scene = score["scenes"][0]
        for easing in CAPABILITIES["easings"]:
            scene["events"] = [event("emphasis", {"target": {"highlight": 1}})]
            scene["events"][0]["easing"] = easing
            hold = event("read", {}, verb="hold", ms=0, duration=1500, dependencies=["emphasis"])
            scene["events"].append(hold)
            plan = compile_score(score, "1:1")
            self.assertEqual(plan["direction"]["timing"], "authored")
            self.assertEqual(plan["scenes"][0]["tracks"][0]["easing"], easing)
            self.assertEqual(plan["scenes"][0]["events"][1]["start_ms"], 400)
            self.assertEqual(len(plan["scenes"][0]["tracks"]), 1)

    def test_explicit_unit_conversion_not_invented_numeric_quantity(self):
        score = score_for("number")
        for record in score["evidence"]:
            record["quantity"]["unit"] = "mL"
            record["claim"] = "Illustrative volume in millilitres."
        number = score["scenes"][0]["actors"][0]
        number["initial"]["value"] = .02
        number["payload"]["decimals"] = 3
        score["scenes"][0]["events"] = [event("conversion", {"target": {"value": .04}})]
        plan = compile_score(score, "16:9")
        self.assertEqual(actors_of(plan)["target"]["geometry"]["lines"], ["0.020 L"])
        self.assertEqual(plan["scenes"][0]["tracks"][0]["to"], .04)
        score["scenes"][0]["events"][0]["changes"]["target"]["value"] = .05
        with self.assertRaisesRegex(ScoreError, "differs from bound evidence"):
            compile_score(score, "16:9")

    def test_all_semantic_composition_flows_and_unsatisfiable_constraints(self):
        score = score_for()
        scene = score["scenes"][0]
        scene["actors"] = [actor("a"), actor("b"), actor("c")]
        for flow in ("auto", "row", "column", "radial", "stack"):
            scene["composition"]["flow"] = flow
            for aspect in ASPECTS:
                plan = compile_score(score, aspect)
                self.assertEqual(plan["scenes"][0]["composition"]["flow"], flow)
                self.assertEqual(len(plan["scenes"][0]["actors"]), 3)
        scene["composition"]["flow"] = "plot"
        with self.assertRaisesRegex(ScoreError, "axis and marks"):
            compile_score(score, "16:9")
        scene["composition"]["flow"] = "auto"
        scene["events"] = [event("bad", {"a": {"fill": 1}}, duration=5900, ms=200)]
        with self.assertRaisesRegex(ScoreError, "exceeds scene duration"):
            compile_score(score, "16:9")
        scene["events"] = [event("bad", {"a": {"fill": 1}})]
        del scene["actors"][0]["initial"]["fill"]
        with self.assertRaisesRegex(ScoreError, "explicit initial"):
            compile_score(score, "16:9")

    def test_dense_selector_and_dimensionless_percent_display(self):
        score = score_for("selector")
        score["scenes"][0]["actors"][0]["payload"]["options"] = [
            "State " + chr(65 + i // 26) + chr(65 + i % 26) for i in range(64)]
        for aspect in ASPECTS:
            compiled = actors_of(compile_score(score, aspect))["target"]
            self.assertEqual(len(compiled["payload"]["options"]), 64)
            self.assertGreaterEqual(compiled["geometry"]["font_size"], 20)
        for unit, value, decimals, displayed in (("1", .2, 1, "0.2"), ("%", 20, 0, "20%")):
            score = score_for("number")
            for record in score["evidence"]:
                record["quantity"].update(unit=unit, dimension="ratio", value=value)
            number = score["scenes"][0]["actors"][0]
            number["payload"].update(unit=unit, dimension="ratio", decimals=decimals)
            number["initial"]["value"] = value
            self.assertEqual(actors_of(compile_score(score, "16:9"))["target"]["geometry"]["lines"], [displayed])

    def test_published_plan_json_schema(self):
        import jsonschema
        validator = getattr(jsonschema, "Draft202012Validator", jsonschema.Draft7Validator)(PLAN_JSON_SCHEMA)
        for aspect in ASPECTS:
            validator.validate(compile_score(sample_score(), aspect))


def material_score(direction="forward", *, grouped=False):
    score = score_for("connector")
    scene = score["scenes"][0]
    material = actor("material", "particles", payload={
        "count": 8, "arrangement": "stream", "illustrative": True,
        "path": {"connector": "target", "direction": direction},
    })
    scene["actors"].append(material)
    for item in scene["actors"]:
        item["initial"]["reveal"] = 1
        for prop in ("fill", "draw"):
            if prop in item["initial"]:
                item["initial"][prop] = 1
    changes = {"material": {"flow": .5}}
    if grouped:
        scene["actors"].append(actor("construct", "group", payload={
            "children": ["a", "b", "target", "material"],
        }, initial={"opacity": 1, "position": "home", "scale": 1, "reveal": 1}))
        changes.update(construct={"scale": .85, "position": "focus"}, a={"scale": 1.3})
    scene["events"] = [event("transport", changes, ms=100, duration=500)]
    return score


class MaterialPathTests(unittest.TestCase):
    def test_native_path_binding_preserves_direction_and_does_not_take_a_layout_slot(self):
        for aspect in ASPECTS:
            baseline = compile_score(score_for("connector"), aspect)
            for direction in ("forward", "reverse"):
                score = material_score(direction)
                plan = compile_score(score, aspect)
                actors = actors_of(plan)
                self.assertEqual(actors["material"]["payload"]["path"],
                                 {"connector": "target", "direction": direction})
                for aid in ("a", "b", "target"):
                    self.assertEqual(actors[aid]["geometry"], actors_of(baseline)[aid]["geometry"])
                path, stream = actors["target"]["geometry"], actors["material"]["geometry"]
                self.assertLess(stream["x"], path["x"])
                self.assertLess(stream["y"], path["y"])
                self.assertGreater(stream["width"], path["width"])
                self.assertGreater(stream["height"], path["height"])
                self.assertEqual(validate_plan(plan), plan)

    def test_path_bindings_fail_closed(self):
        mutations = [
            lambda a: a["payload"]["path"].update(connector="missing"),
            lambda a: a["payload"]["path"].update(connector="a"),
            lambda a: a["payload"]["path"].update(direction="diagonal"),
            lambda a: a["payload"].update(arrangement="radial"),
            lambda a: a["initial"].update(position="focus"),
            lambda a: a["initial"].update(scale=2),
            lambda a: a["initial"].pop("flow"),
        ]
        for mutate in mutations:
            score = material_score()
            mutate(score["scenes"][0]["actors"][-1])
            with self.assertRaises(ScoreError):
                validate_score(score)
        score = material_score()
        score["scenes"][0]["actors"][0]["payload"]["to"] = "material"
        with self.assertRaisesRegex(ScoreError, "own path endpoint"):
            validate_score(score)

    def test_attached_material_cannot_move_independently_of_its_route(self):
        for prop, value in (("position", "focus"), ("scale", 2)):
            score = material_score()
            score["scenes"][0]["events"][0]["changes"]["material"][prop] = value
            with self.assertRaisesRegex(ScoreError, "particle transforms"):
                validate_score(score)
        plan = compile_score(material_score(grouped=True), "9:16")
        for prop in ("x", "y", "scale"):
            broken = deepcopy(plan)
            track = next(t for t in broken["scenes"][0]["tracks"] if t["actor_id"] == "material")
            track.update(property=prop, to=20)
            with self.assertRaisesRegex(ScoreError, "particle transforms"):
                validate_plan(broken)
        broken = deepcopy(plan)
        next(a for a in broken["scenes"][0]["actors"] if a["id"] == "material")["initial"]["x"] += 10
        with self.assertRaisesRegex(ScoreError, "must be home"):
            validate_plan(broken)


if __name__ == "__main__":
    unittest.main()
