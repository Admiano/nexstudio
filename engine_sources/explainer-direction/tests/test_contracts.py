"""Contract fixtures are illustrative test inputs, never live provider outputs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from explainer_direction.contracts import (
    ALIGNMENT_JSON_SCHEMA, ALIGNMENT_SCHEMA, ASPECTS, CAPABILITIES,
    EVIDENCE_JSON_SCHEMA, PLAN_JSON_SCHEMA, PLAN_SCHEMA,
    SCORE_JSON_SCHEMA, ScoreError, quantity_in_unit, resolve_word_cue, sample_score,
    validate_alignment, validate_evidence, validate_plan, validate_score, VERB_PROPERTIES,
)


def reported_alignment(score):
    """Uneven timing fixture; expressly not production voice/alignment evidence."""
    words = score["scenes"][0]["narration"].split()
    intervals = []
    start = 100
    for i, word in enumerate(words):
        end = start + 90 + (i % 3) * 35
        intervals.append({"word": word, "start_ms": start, "end_ms": end})
        start = end + 15 + (i % 2) * 20
    return {"schema": ALIGNMENT_SCHEMA, "id": "test_alignment",
            "source": {"provider": "test-only", "method": "provider_word_timestamps", "audio_sha256": "a" * 64},
            "scenes": [{"scene_id": "change", "duration_ms": 6000, "words": intervals}]}


def fixture_plan(topic="water"):
    """Directly exercises the frozen plan contract without relying on a compiler."""
    score = sample_score(topic)
    authored = score["scenes"][0]
    actors = []
    for i, actor in enumerate(authored["actors"]):
        compiled = {k: deepcopy(actor[k]) for k in ("id", "kind", "role", "label", "meaning", "evidence_ids", "payload", "layout")}
        compiled.update({"identity": actor["id"], "retained": False,
                         "geometry": {"x": 150 + i * 400, "y": 220, "width": 320, "height": 240},
                         "initial": {k: v for k, v in actor["initial"].items() if k != "position"}})
        compiled["initial"].update({"x": compiled["geometry"]["x"], "y": compiled["geometry"]["y"]})
        if actor["kind"] in ("bar", "axis"):
            compiled["payload"]["orientation"] = "horizontal"
        if actor["kind"] == "number":
            compiled["geometry"].update({"font_size": 64, "line_height": 76, "lines": [str(actor["initial"]["value"])]})
        if "value_binding" in actor:
            compiled["value_binding"] = actor["value_binding"]
        actors.append(compiled)
    events, tracks = [], []
    for event in authored["events"]:
        start, end = (2100, 3000) if event["verb"] == "update" else (3000, 5000)
        events.append({k: deepcopy(event[k]) for k in ("id", "verb", "targets", "dependencies", "claim_ids", "rationale")})
        events[-1].update({"start_ms": start, "end_ms": end})
        for target, changes in event["changes"].items():
            actor = next(a for a in actors if a["id"] == target)
            for prop, value in changes.items():
                tracks.append({"event_id": event["id"], "actor_id": target, "property": prop,
                               "from": actor["initial"][prop], "to": value, "start_ms": start, "end_ms": end,
                               "easing": "step" if prop == "selection" else event["easing"], "verb": event["verb"],
                               "claim_ids": event["claim_ids"], "rationale": event["rationale"]})
    scene = {k: deepcopy(authored[k]) for k in ("id", "section_id", "intent", "claim_ids", "narration", "relations", "composition")}
    scene.update({"start_ms": 0, "end_ms": 6000, "actors": actors, "events": events, "tracks": tracks,
                  "transition": {"kind": "cut", "start_ms": 6000, "end_ms": 6000}, "constraints": ["Preserve labels relation"]})
    return {"schema": PLAN_SCHEMA, "film_id": score["film_id"], "title": score["title"], "aspect": "16:9",
            "canvas": {"width": 1920, "height": 1080}, "output": {"fps": 30, "format": "mp4", "background": "#081828"},
            "duration_ms": 6000, "style": score["style"], "evidence": score["evidence"], "scenes": [scene], "provenance": score["provenance"],
            "direction": {"authority": "P8", "status": "DEVELOPMENT_PREFLIGHT", "timing": "provisional",
                          "score_sha256": hashlib.sha256(json.dumps(score, sort_keys=True).encode()).hexdigest()}}


class ScoreContracts(unittest.TestCase):
    def setUp(self):
        self.score = sample_score()
        self.scene = self.score["scenes"][0]
        self.event = self.scene["events"][0]
        self.actor = self.scene["actors"][0]

    def rejects(self, fragment=None):
        with self.assertRaises(ScoreError) as caught:
            validate_score(self.score)
        if fragment:
            self.assertIn(fragment, str(caught.exception))

    def test_independent_topics_and_deep_copy(self):
        for topic in ("water", "energy", "travel"):
            score = sample_score(topic)
            self.assertEqual(validate_score(score), score)
            validated = validate_score(score)
            validated["evidence"][0]["claim"] = "changed"
            self.assertNotEqual(validated, score)
            self.assertTrue(score["provenance"]["test_fixture"])
            self.assertEqual(score["provenance"]["status"], "DEVELOPMENT_PREFLIGHT")
        with self.assertRaises(ScoreError):
            sample_score("unsupported_live_topic")

    def test_json_round_trip_and_capabilities(self):
        self.assertEqual(validate_score(json.loads(json.dumps(self.score))), self.score)
        self.assertEqual(set(CAPABILITIES["kinds"]), {"text", "number", "shape", "bar", "axis", "connector", "selector", "particles", "panel", "image", "group"})
        self.assertEqual(len(ASPECTS), 3)

    def test_fails_closed_unknown_fields_and_geometry(self):
        self.actor["geometry"] = {"x": 20}
        self.rejects("unknown field")

    def test_reject_non_json_nan_boolean_number_and_tuple(self):
        for invalid in (float("nan"), float("inf"), True, (1, 2), 2 ** 10000):
            with self.subTest(invalid=invalid):
                self.score = sample_score()
                self.score["scenes"][0]["duration_ms"] = invalid
                self.rejects()

    def test_duplicate_evidence_and_scene_ids(self):
        self.score["evidence"].append(deepcopy(self.score["evidence"][0]))
        self.rejects("duplicate id")
        self.score = sample_score()
        self.score["scenes"].append(deepcopy(self.score["scenes"][0]))
        self.rejects("duplicate id")

    def test_unbound_narrated_number(self):
        self.scene["narration"] = "The mechanism reports 99 L."
        self.rejects("numerical text")

    def test_unbound_scene_claim(self):
        self.scene["claim_ids"].append("invented")
        self.rejects("unbound ids")

    def test_unbound_actor_evidence(self):
        self.actor["evidence_ids"].append("invented")
        self.rejects("unbound ids")

    def test_quantity_dimension_and_unit(self):
        self.score["evidence"][0]["quantity"]["dimension"] = "mass"
        self.rejects("unit does not match")
        self.score = sample_score()
        self.score["evidence"][0]["quantity"]["unit"] = "mystery"
        self.rejects("unsupported")

    def test_count_is_not_a_fraction_or_negative(self):
        for value in (.5, -1):
            evidence = deepcopy(self.score["evidence"])
            evidence[0]["quantity"] = {"value": value, "unit": "count", "dimension": "count"}
            with self.assertRaisesRegex(ScoreError, "count must"):
                validate_evidence(evidence)

    def test_unit_conversion_and_affine_temperature(self):
        evidence = deepcopy(self.score["evidence"][0])
        evidence["quantity"] = {"value": 2, "unit": "h", "dimension": "time"}
        self.assertEqual(quantity_in_unit(evidence, "min"), 120)
        evidence["quantity"] = {"value": 0, "unit": "degC", "dimension": "temperature"}
        self.assertAlmostEqual(quantity_in_unit(evidence, "K"), 273.15)
        with self.assertRaises(ScoreError):
            quantity_in_unit(evidence, "USD")

    def test_converted_actor_values_are_explicit_and_bound(self):
        for actor in self.scene["actors"][:2]:
            actor["payload"]["unit"] = "mL"
            actor["initial"]["value"] *= 1000
        self.scene["actors"][1]["payload"]["domain"] = [0, 40000]
        self.event["changes"]["readout"]["value"] = 40000
        self.event["changes"]["meter"]["value"] = 40000
        validate_score(self.score)

    def test_initial_displayed_value_mismatch(self):
        self.actor["initial"]["value"] = 999
        self.rejects("differs from bound evidence")

    def test_missing_initial_binding(self):
        del self.actor["value_binding"]
        self.rejects("value_binding")

    def test_event_displayed_value_and_event_claim_binding(self):
        self.event["changes"]["readout"]["value"] = 999
        self.rejects("differs from bound evidence")
        self.event["changes"]["readout"]["value"] = 40
        self.event["claim_ids"] = ["before"]
        self.rejects("value binding")

    def test_missing_numerical_event_binding(self):
        del self.event["value_bindings"]["readout"]
        self.rejects("value_bindings")

    def test_unknown_kind_property_easing_and_verb(self):
        cases = (("kind", "dashboard"), ("role", "magical"))
        for key, value in cases:
            original = self.actor[key]
            self.actor[key] = value
            self.rejects("unsupported")
            self.actor[key] = original
        self.event["easing"] = "spring_timer"
        self.rejects("unsupported")
        self.event["easing"] = "linear"
        self.event["verb"] = "cinematic_something"
        self.rejects("unsupported")

    def test_kind_specific_properties_and_explicit_initial(self):
        self.event["changes"]["stage"]["fill"] = 1
        self.rejects("unsupported kind/property")
        del self.event["changes"]["stage"]["fill"]
        del self.actor["initial"]["highlight"]
        self.rejects("explicit initial")

    def test_linked_changes_share_one_cue(self):
        validate_score(self.score)
        self.assertEqual(len(self.event["targets"]), 3)
        del self.event["changes"]["stage"]
        self.rejects("each linked target")

    def test_holds_are_preserved_without_motion(self):
        hold = self.scene["events"][1]
        self.scene["events"] = [hold]
        hold["dependencies"] = []
        output = validate_score(self.score)
        self.assertEqual(output["scenes"][0]["events"][0]["changes"], {})
        self.scene["events"] = []
        validate_score(self.score)

    def test_hold_cannot_write_state(self):
        self.scene["events"][1]["changes"] = {"readout": {"highlight": 0}}
        self.rejects("hold preserves")

    def test_dependencies_unknown_self_cycle_and_long_chain(self):
        self.event["dependencies"] = ["missing"]
        self.rejects("unbound")
        self.event["dependencies"] = ["linked_change"]
        self.rejects("cycle")
        self.event["dependencies"] = ["read_change"]
        self.rejects("cycle")
        self.event["dependencies"] = []
        self.scene["events"][1]["duration_ms"] = 4000
        self.rejects("exceeds scene")

    def test_dependency_delays_are_explicit_contract_semantics(self):
        self.scene["events"][1]["cue"]["ms"] = 0
        validate_score(self.score)  # hold starts at dependency end 3000, ends 5000

    def test_ambiguous_writes_rejected(self):
        conflicting = deepcopy(self.event)
        conflicting["id"] = "conflict"
        self.scene["events"].append(conflicting)
        self.rejects("ambiguous writes")

    def test_fraction_is_never_falsely_word_aligned(self):
        self.event["cue"]["provisional"] = False
        self.rejects("cue shape")

    def test_unresolved_word_cue_is_valid_authoring(self):
        self.event["cue"] = {"kind": "word", "word": "second", "occurrence": 0, "edge": "start"}
        validate_score(self.score)
        self.event["cue"]["word"] = "invented"
        self.rejects("not present in narration")

    def test_resolved_word_requires_reported_alignment(self):
        self.event["cue"] = {"kind": "word", "word": "second", "occurrence": 0, "edge": "start", "resolved_ms": 1000, "alignment_id": "made_up"}
        self.rejects("actual reported")

    def test_complete_real_alignment_binding(self):
        alignment = reported_alignment(self.score)
        cue = {"kind": "word", "word": "second", "occurrence": 0, "edge": "start", "offset_ms": 10}
        cue["resolved_ms"] = resolve_word_cue(cue, alignment["scenes"][0])
        cue["alignment_id"] = alignment["id"]
        self.score["alignment"] = alignment
        self.scene["timing"] = "aligned"
        self.event["cue"] = cue
        validate_score(self.score)
        cue["resolved_ms"] += 1
        self.rejects("actual reported")

    def test_alignment_nonuniform_word_timing_and_exact_narration(self):
        alignment = reported_alignment(self.score)
        validate_alignment(alignment, self.score)
        self.assertGreater(len({w["end_ms"] - w["start_ms"] for w in alignment["scenes"][0]["words"]}), 1)
        alignment["scenes"][0]["words"][0]["word"] = "fabrication"
        with self.assertRaisesRegex(ScoreError, "complete narration"):
            validate_alignment(alignment, self.score)

    def test_alignment_overlap_and_missing_scene(self):
        alignment = reported_alignment(self.score)
        alignment["scenes"][0]["words"][1]["start_ms"] = 100
        with self.assertRaisesRegex(ScoreError, "nonoverlapping"):
            validate_alignment(alignment, self.score)
        alignment = reported_alignment(self.score)
        alignment["scenes"][0]["scene_id"] = "other"
        with self.assertRaisesRegex(ScoreError, "unknown scene"):
            validate_alignment(alignment, self.score)

    def test_reported_absolute_cue_not_a_fake_alignment(self):
        self.event["cue"] = {"kind": "absolute", "ms": 2100, "basis": "reported_alignment", "alignment_id": "unreported"}
        self.rejects("matching alignment provenance")

    def test_retained_identity_and_terminal_state(self):
        for actor in self.scene["actors"]:
            actor["retain"] = actor["id"]
        next_scene = deepcopy(self.scene)
        next_scene["id"] = "retained"
        next_scene["events"] = []
        for actor in next_scene["actors"]:
            actor["initial"].update(self.event["changes"][actor["id"]])
            if "value_binding" in actor:
                actor["value_binding"] = "after"
        self.score["scenes"].append(next_scene)
        validate_score(self.score)
        next_scene["actors"][0]["meaning"] = "Illustrative new identity"
        self.rejects("retained identity")
        next_scene["actors"][0]["meaning"] = self.actor["meaning"]
        next_scene["actors"][0]["initial"]["highlight"] = 0
        self.rejects("previous terminal")

    def test_repeated_actors_without_retention_rejected(self):
        next_scene = deepcopy(self.scene)
        next_scene["id"] = "next"
        next_scene["events"] = []
        self.score["scenes"].append(next_scene)
        self.rejects("explicit retention")

    def test_comparison_compatible_units_conditions_and_dimension(self):
        left, right = self.scene["actors"][:2]
        right["initial"]["value"] = 40
        right["value_binding"] = "after"
        self.scene["relations"] = [{"id": "compare", "kind": "comparison", "from": left["id"], "to": right["id"], "evidence_ids": ["before", "after"]}]
        validate_score(self.score)
        self.score["evidence"][1]["comparison"]["conditions"]["basis"] = "different"
        self.rejects("identical explicit")

    def test_comparison_missing_context_and_mixed_units(self):
        self.scene["relations"][0]["kind"] = "comparison"
        validate_score(self.score)
        del self.score["evidence"][0]["comparison"]
        self.rejects("identical explicit")
        self.score = sample_score()
        self.score["scenes"][0]["actors"][1]["payload"]["dimension"] = "mass"
        self.rejects("unit/dimension")

    def test_noncommercial_and_unproven_asset_sources_fail(self):
        for license_value in ("CC-BY-NC-4.0", "unknown"):
            self.score["evidence"][0]["source"]["license"] = license_value
            self.rejects("unsupported")
        self.score["evidence"][0]["source"]["license"] = "owned"
        self.score["evidence"][0]["source"]["commercial_use"] = False
        self.rejects("constant")

    def test_development_cannot_promote_itself_to_creative_lock(self):
        self.score["provenance"]["status"] = "CREATIVE_LOCKED"
        self.rejects("unsupported")
        self.score["provenance"]["status"] = "P8_SEMANTIC_BOUND"
        self.rejects("development cannot")
        self.score["provenance"]["mode"] = "p8_bound"
        self.rejects("P8 binding requires")

    def test_p8_semantic_binding_does_not_claim_lock(self):
        self.score["provenance"].update({"mode": "p8_bound", "status": "P8_SEMANTIC_BOUND", "p8": {"state_hash": "a" * 64, "board_hash": "b" * 64}})
        del self.score["provenance"]["test_fixture"]
        validate_score(self.score)

    def test_style_font_local_only_and_no_artist_pixel_layout(self):
        self.score["style"]["typography"]["font_url"] = "https://fonts.example/font.woff2"
        self.rejects("only local")
        self.score = sample_score()
        self.score["scenes"][0]["actors"][0]["layout"]["x"] = 123
        self.rejects("unknown field")

    def test_group_and_layout_cycles(self):
        self.actor["layout"]["relative_to"] = "meter"
        self.rejects("cycle")
        self.actor["layout"].pop("relative_to")
        self.scene["actors"].append({"id": "container", "kind": "group", "role": "surface", "label": "Parts", "meaning": "Shared mechanism group", "evidence_ids": [], "layout": {"anchor": "center"}, "payload": {"children": ["container"]}, "initial": {"opacity": 1, "position": "home"}})
        self.rejects("cycle")

    def test_vector_connector_and_background_panel_vocabulary(self):
        state = {"opacity": 1, "position": "home"}
        for kind, payload, extra in (
            ("shape", {"shape": "circle"}, {"variant": "circle", "draw": 0, "fill": 0}),
            ("panel", {}, {"fill": 1, "reveal": 0}),
            ("particles", {"count": 8, "arrangement": "stream", "illustrative": True}, {"flow": 0, "fill": 1}),
            ("connector", {"from": "readout", "to": "meter", "arrow": True}, {"draw": 0}),
            ("axis", {"domain": [0, 40], "unit": "L", "dimension": "volume"}, {"draw": 0}),
        ):
            self.scene["actors"].append({"id": kind + "_test", "kind": kind, "role": "background" if kind == "panel" else "accent", "label": kind, "meaning": "Illustrative mechanism part", "evidence_ids": ["before", "after"], "layout": {"anchor": "background" if kind == "panel" else "context"}, "payload": payload, "initial": {**state, **extra}})
        validate_score(self.score)

    def test_local_images_only_and_license_required(self):
        image = {"id": "art", "kind": "image", "role": "primary", "label": "Art", "meaning": "Supplied art", "evidence_ids": [], "layout": {"anchor": "context"},
                 "payload": {"src": "/assets/owned.png", "mime": "image/png", "fit": "contain", "source": deepcopy(self.score["provenance"]["source"])}, "initial": {"opacity": 1, "position": "home"}}
        self.scene["actors"].append(image)
        validate_score(self.score)
        for src in ("https://example.com/image.png", "../image.png", "/assets/%2e%2e/image.png", "/assets/script.svg"):
            image["payload"]["src"] = src
            self.rejects()

    def test_text_numerical_truth_and_ordinal_sequences(self):
        text = {"id": "annotation", "kind": "text", "role": "text", "label": "Label", "meaning": "Bound annotation", "evidence_ids": ["before"], "layout": {"anchor": "caption"},
                "payload": {"text": "20 L", "purpose": "annotation"}, "initial": {"opacity": 1, "position": "home", "text": "20 L"}}
        self.scene["actors"].append(text)
        validate_score(self.score)
        text["initial"]["text"] = "99 L"
        self.rejects("numerical text")
        text["payload"] = {"text": "Step 1", "purpose": "label", "numeric_role": "ordinal"}
        text["initial"]["text"] = "Step 1"
        self.rejects("sequence relation")
        self.scene["relations"].append({"id": "process_step", "kind": "sequence", "from": "annotation", "to": "stage", "evidence_ids": []})
        validate_score(self.score)

    def test_large_quantities_do_not_admit_relative_error_as_new_claims(self):
        for record, value in zip(self.score["evidence"], (10 ** 12, 2 * 10 ** 12)):
            record["quantity"]["value"] = value
        for actor in self.scene["actors"][:2]:
            actor["initial"]["value"] = 10 ** 12
            self.event["changes"][actor["id"]]["value"] = 2 * 10 ** 12
        self.scene["actors"][1]["payload"]["domain"] = [0, 2 * 10 ** 12]
        validate_score(self.score)
        self.actor["initial"]["value"] += 1
        self.rejects("differs from bound evidence")
        self.actor["initial"]["value"] -= 1
        self.scene["narration"] = "The quantity is 1000000000001 L."
        self.rejects("numerical text")

    def test_currency_and_temperature_text_units_cannot_be_laundered(self):
        for text in ("The cost is $20.", "The cost is €20.", "The temperature is 20 °C."):
            with self.subTest(text=text):
                self.scene["narration"] = text  # typed evidence is volume, not these units
                self.rejects("unit/value")

    def test_invalid_unicode_is_not_browser_safe_json(self):
        self.actor["label"] = "bad\ud800label"
        self.rejects("Unicode")

    def test_source_ids_cannot_change_provenance(self):
        self.score["evidence"][1]["source"]["uri"] = "test-fixture://different-origin"
        self.rejects("source id")
        self.score = sample_score()
        self.score["provenance"]["source"]["license"] = "CC0-1.0"
        self.rejects("source id")

    def test_blank_comparison_conditions_rejected(self):
        self.score["evidence"][0]["comparison"]["conditions"]["population"] = "   "
        self.rejects("explicit and nonempty")

    def test_selector_options_are_evidence_bound_text(self):
        self.scene["actors"][2]["payload"]["options"] = ["20 L", "40 L"]
        validate_score(self.score)
        self.scene["actors"][2]["payload"]["options"][1] = "99 L"
        self.rejects("numerical text")

    def test_morphed_shape_can_retain_its_terminal_variant(self):
        shape = {"id": "mechanism", "kind": "shape", "role": "primary", "label": "State",
                 "meaning": "Illustrative state change", "evidence_ids": ["before", "after"],
                 "layout": {"anchor": "center"}, "payload": {"shape": "circle"},
                 "initial": {"opacity": 1, "position": "home", "variant": "circle"}, "retain": "mechanism"}
        self.scene["actors"] = [shape]
        self.scene["relations"] = []
        self.scene["composition"].pop("focus")
        self.scene["events"] = [{"id": "morph_state", "verb": "morph", "targets": ["mechanism"],
                                 "cue": {"kind": "absolute", "ms": 500, "basis": "authored"},
                                 "duration_ms": 500, "dependencies": [], "easing": "linear",
                                 "changes": {"mechanism": {"variant": "diamond"}},
                                 "claim_ids": ["after"], "rationale": "Change the visible mechanism state"}]
        second = deepcopy(self.scene)
        second["id"] = "continued"
        second["events"] = []
        second["actors"][0]["initial"]["variant"] = "diamond"
        self.score["scenes"].append(second)
        validate_score(self.score)
        shape["initial"]["variant"] = "hexagon"
        self.rejects("initial variant")

    def test_instant_write_inside_active_animation_is_ambiguous(self):
        instant = deepcopy(self.event)
        instant.update({"id": "instant", "duration_ms": 0,
                        "cue": {"kind": "absolute", "ms": 2500, "basis": "authored"}})
        self.scene["events"].append(instant)
        self.rejects("ambiguous writes")

    def test_local_paths_cannot_contain_controls_or_malformed_url(self):
        for uri in ("/assets/font\x00.woff2", "/assets/font\n.woff2", "//[bad/font.woff2"):
            with self.subTest(uri=uri):
                self.score["style"]["typography"]["font_url"] = uri
                self.rejects("local")

    def test_ordinal_labels_cannot_launder_measured_values(self):
        text = {"id": "step", "kind": "text", "role": "text", "label": "Step",
                "meaning": "Process step", "evidence_ids": [], "layout": {"anchor": "context"},
                "payload": {"text": "Step 1", "purpose": "label", "numeric_role": "ordinal"},
                "initial": {"opacity": 1, "position": "home", "text": "Step 1"}}
        self.scene["actors"].append(text)
        self.scene["relations"].append({"id": "sequence", "kind": "sequence", "from": "step",
                                        "to": "stage", "evidence_ids": []})
        validate_score(self.score)
        for invalid in ("99 L", "Stage -1", "Step 2.5"):
            with self.subTest(invalid=invalid):
                text["payload"]["text"] = invalid
                text["initial"]["text"] = invalid
                self.rejects("ordinal")

    def test_selected_option_must_bind_the_event_evidence(self):
        self.scene["actors"][2]["payload"]["options"] = ["20 L", "40 L"]
        validate_score(self.score)
        self.event["claim_ids"] = ["before"]
        self.event["targets"] = ["stage"]
        self.event["changes"] = {"stage": {"selection": 1}}
        self.event.pop("value_bindings")
        self.rejects("numerical text")

    def test_public_helpers_fail_closed_with_invalid_inputs(self):
        for unit in ([], True, "invalid"):
            with self.subTest(unit=unit):
                with self.assertRaises(ScoreError):
                    quantity_in_unit(self.score["evidence"][0], unit)
        record = deepcopy(self.score["evidence"][0])
        record["quantity"]["value"] = 2 ** 10000
        with self.assertRaises(ScoreError):
            quantity_in_unit(record, "L")
        cue = {"kind": "word", "word": "second", "occurrence": -1, "edge": "start"}
        with self.assertRaises(ScoreError):
            resolve_word_cue(cue, reported_alignment(self.score)["scenes"][0])
        cue["occurrence"] = 0
        cue["offset_ms"] = -60000
        with self.assertRaisesRegex(ScoreError, "outside"):
            resolve_word_cue(cue, reported_alignment(self.score)["scenes"][0])

    def test_qualitative_mechanisms_do_not_require_data_widgets_or_sentence_scenes(self):
        topics = (
            ("Plant transport", "A transport path links the root to the leaf.", "The path now carries material."),
            ("Cache reuse", "A cache path links stored content to a request.", "The request now reuses stored content."),
        )
        for title, narration, conclusion in topics:
            with self.subTest(topic=title):
                score = sample_score()
                score["title"] = title
                score["evidence"] = [{"id": "mechanism_claim", "claim": narration, "status": "illustrative",
                                      "source": deepcopy(score["provenance"]["source"])}]
                scene = score["scenes"][0]
                scene["claim_ids"] = ["mechanism_claim"]
                scene["narration"] = narration
                scene["composition"] = {"flow": "radial", "density": "balanced", "focus": "path"}
                payloads = {
                    "origin": ("shape", {"shape": "circle"}, {"variant": "circle", "highlight": 0}),
                    "destination": ("shape", {"shape": "hexagon"}, {"variant": "hexagon", "highlight": 0}),
                    "path": ("connector", {"from": "origin", "to": "destination", "arrow": True}, {"draw": 0}),
                    "material": ("particles", {"count": 6, "arrangement": "stream", "illustrative": True}, {"flow": 0}),
                    "context": ("panel", {}, {"reveal": 0}),
                    "annotation": ("text", {"text": narration, "purpose": "annotation"}, {"text": narration}),
                }
                scene["actors"] = [
                    {"id": aid, "kind": kind, "role": "background" if aid == "context" else "primary",
                     "label": aid, "meaning": "Illustrative " + title + " mechanism part", "evidence_ids": ["mechanism_claim"],
                     "layout": {"anchor": "background" if aid == "context" else "context"},
                     "payload": payload, "initial": {"opacity": 1, "position": "home", **initial}, "retain": aid}
                    for aid, (kind, payload, initial) in payloads.items()]
                scene["relations"] = [{"id": "transfer", "kind": "flows_to", "from": "origin", "to": "destination",
                                       "evidence_ids": ["mechanism_claim"]}]
                changes = {"origin": {"highlight": 1}, "destination": {"highlight": 1}, "path": {"draw": 1},
                           "material": {"flow": 1}, "context": {"reveal": 1}, "annotation": {"text": conclusion}}
                scene["events"] = [{"id": "trace_mechanism", "verb": "update", "targets": list(changes),
                                     "cue": {"kind": "fraction", "fraction": .25, "provisional": True}, "duration_ms": 1000,
                                     "dependencies": [], "easing": "ease_in_out", "changes": changes,
                                     "claim_ids": ["mechanism_claim"], "rationale": "Link visible transfer, path, annotation and context"}]
                second = deepcopy(scene)
                second.update(id="inspect_mechanism", narration=conclusion, events=[])
                for actor in second["actors"]:
                    actor["initial"].update(changes[actor["id"]])
                score["scenes"].append(second)
                validated = validate_score(score)
                self.assertEqual(len(validated["scenes"]), 2)
                self.assertNotIn("number", {a["kind"] for a in scene["actors"]})
                self.assertNotIn("bar", {a["kind"] for a in scene["actors"]})

    def test_long_dependency_chain_is_valid_and_bounded(self):
        self.scene["events"] = [
            {"id": f"hold_{i}", "verb": "hold", "targets": [],
             "cue": {"kind": "absolute", "ms": 0, "basis": "authored"},
             "duration_ms": 1, "dependencies": [f"hold_{i + 1}"] if i < 399 else [],
             "easing": "linear", "changes": {}, "claim_ids": [],
             "rationale": "Preserve a deliberate authored inspection interval"}
            for i in range(400)]
        validate_score(self.score)
        extra = deepcopy(self.scene["events"][0])
        extra["id"] = "extra"
        self.scene["events"].append(extra)
        self.rejects("array length")

    def test_every_admitted_kind_property_and_verb_has_an_explicit_state(self):
        payloads = {
            "text": {"text": "Illustrative change", "purpose": "annotation"},
            "number": {"unit": "L", "dimension": "volume"},
            "shape": {"shape": "circle"},
            "bar": {"unit": "L", "dimension": "volume", "domain": [0, 40]},
            "axis": {"unit": "L", "dimension": "volume", "domain": [0, 40]},
            "connector": {"from": "readout", "to": "meter", "arrow": True},
            "selector": {"options": ["Initial", "Extended"]},
            "particles": {"count": 8, "arrangement": "radial", "illustrative": True},
            "panel": {},
            "image": {"src": "/assets/owned.png", "mime": "image/png", "fit": "contain",
                      "source": deepcopy(self.score["provenance"]["source"])},
            "group": {"children": ["readout", "meter"]},
        }
        initials = {"opacity": 1, "reveal": 0, "scale": 1, "rotation": 0, "highlight": 0, "position": "home",
                    "text": "Illustrative change", "value": 20, "draw": 0, "fill": 0,
                    "variant": "circle", "selection": 0, "flow": 0}
        targets = {"opacity": 0, "reveal": 1, "scale": 1.2, "rotation": -90, "highlight": 1, "position": "focus",
                   "text": "Illustrative conclusion", "value": 40, "draw": 1, "fill": 1,
                   "variant": "hexagon", "selection": 1, "flow": 1}
        for kind, properties in CAPABILITIES["properties"].items():
            for verb, admitted in VERB_PROPERTIES.items():
                for prop in set(CAPABILITIES["event_properties"][kind]) & set(admitted):
                    with self.subTest(kind=kind, verb=verb, property=prop):
                        score = sample_score()
                        actor = {"id": "subject", "kind": kind, "role": "accent", "label": "Subject",
                                 "meaning": "Illustrative mechanism state", "evidence_ids": ["before", "after"],
                                 "layout": {"anchor": "primary"}, "payload": payloads[kind],
                                 "initial": {p: initials[p] for p in properties}}
                        if kind in ("bar", "number"):
                            actor["value_binding"] = "before"
                        scene = score["scenes"][0]
                        scene["actors"].append(actor)
                        scene["events"] = [{"id": "change_state", "verb": verb, "targets": ["subject"],
                                             "cue": {"kind": "absolute", "ms": 0, "basis": "authored"},
                                             "duration_ms": 500, "dependencies": [], "easing": "linear",
                                             "changes": {"subject": {prop: targets[prop]}}, "claim_ids": ["after"],
                                             "rationale": "Expose the mechanism state coherently"}]
                        if prop == "value":
                            scene["events"][0]["value_bindings"] = {"subject": "after"}
                        validate_score(score)

    def test_wipe_and_transition_duration(self):
        self.scene["transition"] = {"kind": "wipe", "duration_ms": 300, "direction": "up"}
        validate_score(self.score)
        del self.scene["transition"]["direction"]
        self.rejects("wipe direction")


class PlanContracts(unittest.TestCase):
    def test_plan_deepcopy_all_topics_and_native_aspects(self):
        for topic in ("water", "energy", "travel"):
            for aspect, (width, height) in ASPECTS.items():
                plan = fixture_plan(topic)
                plan["aspect"] = aspect
                plan["canvas"] = {"width": width, "height": height}
                self.assertEqual(validate_plan(plan), plan)
                self.assertIsNot(validate_plan(plan), plan)

    def test_compiled_auto_orientation_is_not_executable(self):
        plan = fixture_plan()
        plan["scenes"][0]["actors"][1]["payload"]["orientation"] = "auto"
        with self.assertRaisesRegex(ScoreError, "unsupported"):
            validate_plan(plan)

    def test_native_canvas_fails(self):
        plan = fixture_plan()
        plan["aspect"] = "9:16"
        with self.assertRaisesRegex(ScoreError, "native aspect"):
            validate_plan(plan)

    def test_outside_interval_and_wrong_from_rejected(self):
        plan = fixture_plan()
        plan["scenes"][0]["tracks"][0]["end_ms"] = 7000
        with self.assertRaisesRegex(ScoreError, "share event interval"):
            validate_plan(plan)
        plan = fixture_plan()
        plan["scenes"][0]["tracks"][0]["from"] = 0
        with self.assertRaisesRegex(ScoreError, "previous deterministic"):
            validate_plan(plan)

    def test_invalid_numeric_target_and_discrete_easing(self):
        plan = fixture_plan()
        plan["scenes"][0]["tracks"][0]["to"] = 99
        with self.assertRaisesRegex(ScoreError, "unbound"):
            validate_plan(plan)
        plan = fixture_plan()
        track = next(t for t in plan["scenes"][0]["tracks"] if t["property"] == "selection")
        track["easing"] = "linear"
        with self.assertRaisesRegex(ScoreError, "step easing"):
            validate_plan(plan)

    def test_lost_linked_target_rejected(self):
        plan = fixture_plan()
        plan["scenes"][0]["tracks"] = [t for t in plan["scenes"][0]["tracks"] if t["actor_id"] != "stage"]
        with self.assertRaisesRegex(ScoreError, "every linked target"):
            validate_plan(plan)

    def test_hold_cannot_become_a_track(self):
        plan = fixture_plan()
        track = plan["scenes"][0]["tracks"][1]
        hold = plan["scenes"][0]["events"][1]
        track.update({"event_id": hold["id"], "verb": "hold", "start_ms": hold["start_ms"], "end_ms": hold["end_ms"], "rationale": hold["rationale"]})
        with self.assertRaisesRegex(ScoreError, "hold has no"):
            validate_plan(plan)

    def test_plan_cannot_bypass_semantic_actor_validation(self):
        cases = (
            ("label", lambda a: a.update(label="99 L"), "numerical text"),
            ("selector", lambda a: a["payload"].update(options=["Initial", "99 L"]), "numerical text"),
            ("binding", lambda a: a.update(value_binding="before"), "only for number/bar"),
            ("identity", lambda a: a.update(identity="another_identity"), "stable actor id"),
        )
        for name, mutation, error in cases:
            with self.subTest(name=name):
                plan = fixture_plan()
                actor = plan["scenes"][0]["actors"][2]
                mutation(actor)
                with self.assertRaisesRegex(ScoreError, error):
                    validate_plan(plan)

    def test_plan_group_connector_and_layout_bindings(self):
        for kind, payload, geometry, error in (
            ("group", {"children": ["added"]}, {}, "cycle"),
            ("connector", {"from": "missing", "to": "meter", "arrow": True},
             {"points": [{"x": 0, "y": 0}, {"x": 100, "y": 100}]}, "unbound"),
            ("panel", {}, {}, "relative to itself"),
        ):
            with self.subTest(kind=kind):
                plan = fixture_plan()
                actor = deepcopy(plan["scenes"][0]["actors"][2])
                actor.update(id="added", identity="added", kind=kind, payload=payload,
                             initial={"x": 100, "y": 100, "opacity": 1})
                actor["geometry"].update(geometry)
                if kind == "panel":
                    actor["layout"]["relative_to"] = "added"
                plan["scenes"][0]["actors"].append(actor)
                with self.assertRaisesRegex(ScoreError, error):
                    validate_plan(plan)

    def test_plan_retained_nonposition_state_is_not_reset(self):
        plan = fixture_plan()
        next_scene = deepcopy(plan["scenes"][0])
        next_scene.update(id="next", start_ms=6000, end_ms=12000, events=[], tracks=[])
        next_scene["transition"] = {"kind": "cut", "start_ms": 12000, "end_ms": 12000}
        for actor in next_scene["actors"]:
            actor["retained"] = True
            for track in plan["scenes"][0]["tracks"]:
                if track["actor_id"] == actor["id"]:
                    actor["initial"][track["property"]] = track["to"]
            if "value_binding" in actor:
                actor["value_binding"] = "after"
            actor["initial"]["x"] += 10  # semantic reflow between scene compositions is legal
        plan["scenes"].append(next_scene)
        plan["duration_ms"] = 12000
        validate_plan(plan)
        next_scene["actors"][2]["initial"]["selection"] = 0
        with self.assertRaisesRegex(ScoreError, "previous terminal state"):
            validate_plan(plan)

    def test_compiled_transition_occupies_outgoing_tail(self):
        plan = fixture_plan()
        plan["scenes"][0]["transition"] = {"kind": "fade", "start_ms": 100, "end_ms": 500}
        with self.assertRaisesRegex(ScoreError, "outgoing scene tail"):
            validate_plan(plan)

    def test_empty_nonhold_event_cannot_pass(self):
        plan = fixture_plan()
        plan["scenes"][0]["tracks"] = []
        plan["scenes"][0]["events"][0]["targets"] = []
        with self.assertRaisesRegex(ScoreError, "non-hold.*target"):
            validate_plan(plan)

    def test_compiled_relations_distinct_and_unique(self):
        plan = fixture_plan()
        relation = plan["scenes"][0]["relations"][0]
        relation["to"] = relation["from"]
        with self.assertRaisesRegex(ScoreError, "distinct actors"):
            validate_plan(plan)
        plan = fixture_plan()
        plan["scenes"][0]["relations"].append(deepcopy(plan["scenes"][0]["relations"][0]))
        with self.assertRaisesRegex(ScoreError, "duplicate id"):
            validate_plan(plan)

    def test_plan_font_extension_and_image_mime_are_checked(self):
        plan = fixture_plan()
        plan["style"]["typography"]["font_url"] = "/assets/code.js"
        with self.assertRaisesRegex(ScoreError, "local font file"):
            validate_plan(plan)
        plan = fixture_plan()
        actor = plan["scenes"][0]["actors"][2]
        actor.update(kind="image", initial={"x": 100, "y": 100, "opacity": 1},
                     payload={"src": "/assets/code.svg", "mime": "image/png", "fit": "contain",
                              "source": deepcopy(plan["provenance"]["source"])})
        plan["scenes"][0]["events"] = []
        plan["scenes"][0]["tracks"] = []
        with self.assertRaisesRegex(ScoreError, "extension"):
            validate_plan(plan)

    def test_large_compiled_targets_are_exactly_bound(self):
        plan = fixture_plan()
        plan["evidence"][1]["quantity"]["value"] = 10 ** 12
        plan["scenes"][0]["actors"][1]["payload"]["domain"] = [0, 10 ** 12]
        for track in plan["scenes"][0]["tracks"]:
            if track["property"] == "value":
                track["to"] = 10 ** 12
        validate_plan(plan)
        plan["scenes"][0]["tracks"][0]["to"] += 1
        with self.assertRaisesRegex(ScoreError, "unbound"):
            validate_plan(plan)

    def test_compiled_selected_option_is_event_evidence_bound(self):
        plan = fixture_plan()
        plan["scenes"][0]["actors"][2]["payload"]["options"] = ["20 L", "40 L"]
        validate_plan(plan)
        event = plan["scenes"][0]["events"][0]
        event["targets"] = ["stage"]
        event["claim_ids"] = ["before"]
        plan["scenes"][0]["tracks"] = [t for t in plan["scenes"][0]["tracks"] if t["actor_id"] == "stage"]
        plan["scenes"][0]["tracks"][0]["claim_ids"] = ["before"]
        with self.assertRaisesRegex(ScoreError, "numerical text"):
            validate_plan(plan)

    def test_position_tracks_require_a_coherent_pair(self):
        plan = fixture_plan()
        scene = plan["scenes"][0]
        actor = scene["actors"][0]
        event = deepcopy(scene["events"][0])
        event.update(id="move_readout", verb="move", targets=[actor["id"]], dependencies=[])
        scene["events"].append(event)
        for prop in ("x", "y"):
            scene["tracks"].append({
                "event_id": event["id"], "actor_id": actor["id"], "property": prop,
                "from": actor["initial"][prop], "to": actor["initial"][prop] + 10,
                "start_ms": event["start_ms"], "end_ms": event["end_ms"],
                "easing": "ease_out", "verb": "move",
                "claim_ids": event["claim_ids"], "rationale": event["rationale"],
            })
        validate_plan(plan)
        missing = deepcopy(plan)
        missing["scenes"][0]["tracks"].pop()
        with self.assertRaisesRegex(ScoreError, "both x/y"):
            validate_plan(missing)
        plan["scenes"][0]["tracks"][-1]["easing"] = "linear"
        with self.assertRaisesRegex(ScoreError, "share easing"):
            validate_plan(plan)

    def test_json_schema_is_valid_and_matches_fixtures(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("optional preinstalled jsonschema is unavailable")
        # The system ships an older jsonschema; our published vocabulary is
        # compatible with draft 7 as well as 2020-12.
        Validator = getattr(jsonschema, "Draft202012Validator", jsonschema.Draft7Validator)
        for schema in (SCORE_JSON_SCHEMA, PLAN_JSON_SCHEMA, ALIGNMENT_JSON_SCHEMA, EVIDENCE_JSON_SCHEMA):
            Validator.check_schema(schema)
        for topic in ("water", "energy", "travel"):
            Validator(SCORE_JSON_SCHEMA).validate(sample_score(topic))
            Validator(PLAN_JSON_SCHEMA).validate(fixture_plan(topic))
            Validator(ALIGNMENT_JSON_SCHEMA).validate(reported_alignment(sample_score(topic)))
            for record in sample_score(topic)["evidence"]:
                Validator(EVIDENCE_JSON_SCHEMA).validate(record)
        invalid = sample_score()
        invalid["scenes"][0]["actors"][0]["payload"]["unexpected"] = "code"
        self.assertTrue(list(Validator(SCORE_JSON_SCHEMA).iter_errors(invalid)))
        for mutate in (
            lambda a: a["initial"].update(fill=1),
            lambda a: a["initial"].pop("selection"),
        ):
            invalid = sample_score()
            mutate(invalid["scenes"][0]["actors"][2])
            self.assertTrue(list(Validator(SCORE_JSON_SCHEMA).iter_errors(invalid)))
            invalid = fixture_plan()
            mutate(invalid["scenes"][0]["actors"][2])
            self.assertTrue(list(Validator(PLAN_JSON_SCHEMA).iter_errors(invalid)))


if __name__ == "__main__":
    unittest.main()
