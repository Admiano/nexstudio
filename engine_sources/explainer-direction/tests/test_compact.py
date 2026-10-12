"""Compact director fixtures are isolated from live authoring and render proof."""
from copy import deepcopy
from pathlib import Path
import re
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from explainer_direction.authoring import CreativeAuthorityWarning, author_score
from explainer_direction.compact import (
    SCHEMA, _beat_schema, _beats_from_choices, _cue_options, author_compact, lower_beats, lower_scene,
)
from explainer_direction.compiler import compile_score
from explainer_direction.contracts import ALIGNMENT_SCHEMA, ScoreError, validate_score


SOURCE = {"id": "test_declaration", "uri": "urn:test-only:rotor",
          "locator": "Test-only evidence, not a factual citation", "license": "owned", "commercial_use": True}
EVIDENCE = [
    {"id": "connection", "claim": "The rotor of a wind turbine connects to a generator.",
     "status": "supported", "source": SOURCE},
    {"id": "output", "claim": "The generator produces electricity.",
     "status": "supported", "source": SOURCE},
]
GRAPH = {
    "entities": [
        {"id": "rotor", "kind": "device", "label": "Rotor", "evidence_ids": ["connection"]},
        {"id": "generator", "kind": "device", "label": "Generator",
         "evidence_ids": ["connection", "output"]},
        {"id": "electricity", "kind": "energy", "label": "Electricity", "evidence_ids": ["output"]},
    ],
    "facts": [
        {"id": "link", "kind": "connected_to", "from": "rotor", "to": "generator",
         "evidence_ids": ["connection"]},
        {"id": "product", "kind": "produces", "from": "generator", "to": "electricity",
         "evidence_ids": ["output"]},
    ],
    "quantities": [],
}
PALETTE = {"background": "#081828", "surface": "#16364A", "text": "#F1F8FC",
           "muted": "#A2B7C7", "primary": "#54D6E5", "secondary": "#6FA9F6",
           "accent": "#FFCC74", "positive": "#89E7B3", "negative": "#FFA2A2"}


def figure(entity, form="circle", role="primary"):
    return {"entity": entity, "form": form, "role": role, "anchor": "center"}


def beat(word, action, kind, target):
    return {"at": word, "action": action, "target": {"kind": kind, "id": target}}


def direction():
    return {
        "title": "Following the connection",
        "ideas": [
            {"method": "journey", "argument": "Follow a mechanical path from one named device to the next",
             "forms": ["circle", "diamond"], "progression": ["construct", "connect"]},
            {"method": "transformation", "argument": "Show a conversion path ending in the electrical output",
             "forms": ["hexagon", "circle"], "progression": ["reveal", "emphasize"]},
        ],
        "selected": 0, "palette": deepcopy(PALETTE),
        "scenes": [
            {"claims": ["connection"], "intent": "Build the source-stated mechanical connection",
             "narration": "The rotor and generator are now connected as a single mechanism.", "flow": "row",
             "figures": [figure("rotor", "diamond"), figure("generator", "hexagon", "secondary")],
             "facts": ["link"],
             "beats": [beat("rotor", "construct", "entity", "rotor"),
                       beat("generator", "construct", "entity", "generator"),
                       beat("connected", "connect", "fact", "link")], "transition": "cut"},
            {"claims": ["output"], "intent": "Trace the stated electrical output",
             "narration": "The generator and electricity come into view; one produces the other.", "flow": "radial",
             "figures": [figure("generator", "hexagon"), figure("electricity", "circle", "accent")],
             "facts": ["product"],
             "beats": [beat("generator", "construct", "entity", "generator"),
                       beat("electricity", "construct", "entity", "electricity"),
                       beat("produces", "connect", "fact", "product")], "transition": "fade"},
        ],
    }


class CompactFixture:
    is_test_fixture = True
    identity = {"provider": "test-only", "model": "test-only-compact"}

    def __init__(self, change=None):
        self.change, self.calls = change, []
        self.last_request_id = "test_request"

    def complete(self, task, request):
        self.calls.append((task, deepcopy(request)))
        if task == "plan_meaning_entities":
            return {"entities": deepcopy(GRAPH["entities"])}
        if task == "plan_meaning_relations":
            return {"facts": deepcopy(GRAPH["facts"]), "quantity_subjects": {}}
        if task == "direct_compact":
            draft = direction()
            if self.change:
                self.change(draft)
            self.draft = deepcopy(draft)
            for scene in draft["scenes"]:
                scene.pop("beats")
            return draft
        if task == "direct_compact_beats":
            return {"beats": {f"{beat['action']}:{beat['target']['id']}": beat["at"]
                              for beat in self.draft["scenes"][request["scene"]["index"]]["beats"]}}
        raise AssertionError("no hidden fallback or further authoring: " + task)


def measured(partial):
    scenes = []
    for scene in partial["scenes"]:
        words = re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", scene["narration"])
        scenes.append({"scene_id": scene["id"], "duration_ms": len(words) * 350 + 350,
                       "words": [{"word": word, "start_ms": i * 350 + 100,
                                  "end_ms": i * 350 + 300} for i, word in enumerate(words)]})
    return {"duration_ms": scenes[-1]["duration_ms"],
            "alignment": {"schema": ALIGNMENT_SCHEMA, "id": "measured_test_alignment",
                          "source": {"provider": "test-only", "method": "provider_word_timestamps",
                                     "audio_sha256": "a" * 64}, "scenes": scenes}}


def authored(provider):
    return author_score("A wind turbine's output", EVIDENCE, provider=provider, compact=True,
                        test_fixture=True, max_repairs=0, prepare_narration=measured,
                        film_id="wind_turbine_unit")


def test_compact_live_boundary_has_no_full_score_or_capability_registry():
    provider = CompactFixture()
    with pytest.warns(CreativeAuthorityWarning, match="DEVELOPMENT_PREFLIGHT"):
        score = authored(provider)
    assert validate_score(score) == score
    assert score["provenance"]["status"] == "DEVELOPMENT_PREFLIGHT"
    assert score["provenance"]["test_fixture"] is True
    assert len(score["scenes"]) == 2
    request = next(r for task, r in provider.calls if task == "direct_compact")
    assert "score_schema" not in request and "capabilities" not in request
    assert "response_schema" in request and request["response_schema"] != SCHEMA
    assert "actors" not in request["response_schema"]["properties"]["scenes"]["items"]["properties"]
    assert "beats" not in request["response_schema"]["properties"]["scenes"]["items"]["properties"]
    assert "aspect_ratio" not in request["response_schema"]["properties"]["scenes"]["items"]["properties"]["figures"]["items"]["properties"]
    assert [task for task, _ in provider.calls][-2:] == ["direct_compact_beats", "direct_compact_beats"]
    for task, motion_request in provider.calls:
        if task == "direct_compact_beats":
            assert "score_schema" not in motion_request and "capabilities" not in motion_request
            choices = motion_request["response_schema"]["properties"]["beats"]["properties"]
            assert all(key.split(":")[0] not in ("transport", "orient") for key in choices)
            assert all(set(cue["enum"]) <= {
                word["word"] if not number else f"{word['word']}#{number}"
                for word in motion_request["words"] for number in ("", "2", "3")
            } and "the" not in cue["enum"] for cue in choices.values())
    assert all(s["timing"] == "aligned" for s in score["scenes"])
    assert all(e["cue"].get("alignment_id") == "measured_test_alignment"
               for s in score["scenes"] for e in s["events"])
    for aspect in ("16:9", "9:16", "1:1"):
        compiled = compile_score(score, aspect=aspect)
        assert compiled["aspect"] == aspect
        assert compiled["direction"]["status"] == "DEVELOPMENT_PREFLIGHT"


@pytest.mark.parametrize("change,expected", [
    (lambda draft: draft["scenes"][0]["figures"][0].update(entity="background"),
     "unsupported value 'background'"),
    (lambda draft: draft["scenes"][0]["beats"][2].update(action="transport"),
     "missing fields.*connect:link"),
    (lambda draft: draft["scenes"][0]["beats"][2]["target"].update(id="rotor"),
     "missing fields.*connect:link"),
    (lambda draft: draft["scenes"][0].update(narration="rotor generator connects"),
     "complete natural sentence"),
    (lambda draft: draft["ideas"][1].update(forms=["circle", "diamond"],
                                           progression=["construct", "connect"]),
     "repeat representation"),
])
def test_compact_rejects_invalid_direction_without_substituting_cards(change, expected):
    provider = CompactFixture(change)
    with pytest.raises(ScoreError, match=expected):
        authored(provider)
    assert [task for task, _ in provider.calls][:3] == [
        "plan_meaning_entities", "plan_meaning_relations", "direct_compact",
    ]


def test_timed_compact_rejects_timestamp_cues_before_lowering():
    provider = CompactFixture(lambda draft: draft["scenes"][0]["beats"][0].update(at="0:00"))
    with pytest.raises(ScoreError, match="unsupported value '0:00'"):
        authored(provider)


def test_compact_word_cues_normalize_provider_punctuation_and_count_occurrences():
    draft = direction()["scenes"][0]
    draft["narration"] = "The rotor connects to a generator; this rotor is connected to it."
    alignment = measured({"scenes": [{"id": "scene_0", "narration": draft["narration"]}]})["alignment"]["scenes"][0]
    for word in alignment["words"]:
        if word["word"] in ("rotor", "generator"):
            word["word"] += "."
    assert _cue_options(alignment).count("rotor") == 1
    assert "rotor#2" in _cue_options(alignment)
    schema = _beat_schema(draft, GRAPH, alignment)["properties"]["beats"]
    assert set(schema["required"]) == {"construct:rotor", "construct:generator", "connect:link"}
    assert schema["maxProperties"] == len(schema["properties"])
    assert "reveal:rotor" not in schema["properties"]
    choices = {"beats": {"construct:rotor": "rotor", "construct:generator": "generator",
                          "connect:link": "connected", "emphasize:rotor": "rotor#2"}}
    draft["beats"] = _beats_from_choices(choices, draft, alignment)
    scene, registry = lower_scene(draft, GRAPH, 0)
    scene["duration_ms"] = alignment["duration_ms"]
    lowered = lower_beats(draft, scene, registry, GRAPH, alignment)
    assert lowered["events"][2]["cue"] == {
        "kind": "word", "word": "rotor", "occurrence": 1, "edge": "start",
    }


def test_compact_coincident_actions_preserve_both_changes_in_one_event():
    draft = direction()["scenes"][0]
    alignment = measured({"scenes": [{"id": "scene_0", "narration": draft["narration"]}]})["alignment"]["scenes"][0]
    choices = {"beats": {"construct:rotor": "rotor", "emphasize:rotor": "rotor",
                          "construct:generator": "generator", "connect:link": "connected"}}
    draft["beats"] = _beats_from_choices(choices, draft, alignment)
    scene, registry = lower_scene(draft, GRAPH, 0)
    scene["duration_ms"] = alignment["duration_ms"]
    lowered = lower_beats(draft, scene, registry, GRAPH, alignment)
    assert len(lowered["events"]) == 3
    first = lowered["events"][0]
    assert first["changes"][registry[0]["rotor"]["id"]] == {
        "opacity": 1, "draw": 1, "fill": 1, "highlight": 1,
    }
    assert first["rationale"].endswith("construct + emphasize")
    assert first["duration_ms"] >= 120


def test_compact_lowering_still_rejects_a_duplicate_no_op():
    draft = direction()["scenes"][0]
    draft["beats"].append(beat("mechanism", "connect", "fact", "link"))
    alignment = measured({"scenes": [{"id": "scene_0", "narration": draft["narration"]}]})["alignment"]["scenes"][0]
    scene, registry = lower_scene(draft, GRAPH, 0)
    scene["duration_ms"] = alignment["duration_ms"]
    with pytest.raises(ScoreError, match="beat has no visible change"):
        lower_beats(draft, scene, registry, GRAPH, alignment)


def test_compact_measures_voice_before_requesting_motion():
    provider = CompactFixture()
    durations = []
    def measured_first(partial):
        assert not any(task == "direct_compact_beats" and request["scene"]["index"] == len(partial["scenes"]) - 1
                       for task, request in provider.calls)
        result = measured(partial)
        durations.append(result["duration_ms"])
        return result
    with pytest.warns(CreativeAuthorityWarning):
        author_score("test", EVIDENCE, provider=provider, compact=True, test_fixture=True,
                     max_repairs=0, prepare_narration=measured_first)
    assert len(durations) == 2


def test_compact_narration_veto_stops_before_voice_or_motion():
    provider = CompactFixture(lambda draft: draft["scenes"][0].update(
        narration="The rotor connects to a generator producing millions of units each second."))
    def judge(premise, hypothesis):
        assert "millions" not in premise
        return ({"entailment": .01, "neutral": .98, "contradiction": .01} if "millions" in hypothesis
                else {"entailment": 1, "neutral": 0, "contradiction": 0})
    def no_voice(partial):
        raise AssertionError("rejected narration must not reach voice")
    with pytest.raises(ScoreError, match="cannot support narration"):
        author_score("test", EVIDENCE, provider=provider, compact=True, test_fixture=True,
                     max_repairs=0, source_judge=judge, prepare_narration=no_voice)
    assert len(provider.calls) == 3


def test_compact_word_range_is_enforced_in_generation_schema():
    provider = CompactFixture()
    with pytest.raises(ScoreError, match="string pattern mismatch"):
        author_score("test", EVIDENCE, provider=provider, compact=True, test_fixture=True,
                     max_repairs=0, context={"narration_target_words": "45 to 55"},
                     prepare_narration=measured)
    schema = provider.calls[-1][1]["response_schema"]["properties"]["scenes"]
    assert schema["minItems"] == schema["maxItems"] == 2
    assert schema["items"]["properties"]["narration"]["type"] == "string"
    import re
    pattern = schema["items"]["properties"]["narration"]["pattern"]
    for count in (23, 27):
        assert re.fullmatch(pattern, " ".join(["word"] * count) + ".")
    for count in (22, 28):
        assert not re.fullmatch(pattern, " ".join(["word"] * count) + ".")
    assert not re.fullmatch(pattern, " ".join(["word.,"] * 23))
    assert schema["items"]["properties"]["claims"]["minItems"] == 1


def test_compact_balances_four_source_claims_over_two_scenes():
    provider = CompactFixture()
    extra = deepcopy(EVIDENCE)
    for record in extra:
        record["id"] += "_extra"
    common = {
        "brief": "test", "family": "ocean", "family_direction": "test",
        "context": {"narration_target_words": "45 to 55"}, "brand": {},
        "evidence": EVIDENCE + extra, "meaning_graph": GRAPH,
    }
    with pytest.raises(ScoreError, match="array length"):
        author_compact(provider, common, {"direction_id": "test"}, measured, 0)
    schema = provider.calls[-1][1]["response_schema"]["properties"]["scenes"]
    assert schema["items"]["properties"]["claims"]["minItems"] == 2
    assert schema["items"]["properties"]["claims"]["maxItems"] == 2


def test_compact_narration_repair_requests_only_the_rejected_words():
    class RepairFixture(CompactFixture):
        def complete(self, task, request):
            if task == "repair":
                self.calls.append((task, deepcopy(request)))
                assert request["original_task"] == "direct_compact"
                assert request["repair_scope"] == "$.scenes[0].narration"
                assert isinstance(request["invalid_value"], str)
                assert [claim["id"] for claim in request["accepted_scene_claims"]] == ["connection"]
                assert request["scene_intent"] == direction()["scenes"][0]["intent"]
                assert "previous_response" not in request and "score_schema" not in request
                return {"replacement": direction()["scenes"][0]["narration"]}
            return super().complete(task, request)
    fixture = RepairFixture(lambda draft: draft["scenes"][0].update(
        narration=draft["scenes"][0]["narration"].rstrip(".")))
    with pytest.warns(CreativeAuthorityWarning):
        score = author_score("test", EVIDENCE, provider=fixture, compact=True, test_fixture=True,
                             max_repairs=1, prepare_narration=measured)
    assert score["scenes"][0]["narration"] == direction()["scenes"][0]["narration"]


def test_compact_reports_independent_source_and_endpoint_errors_before_voice():
    def invalid(draft):
        draft["scenes"][0]["narration"] = "The rotor performs magical work."
        draft["scenes"][1]["figures"] = [figure("electricity")]

    class RepairFixture(CompactFixture):
        def complete(self, task, request):
            if task == "repair":
                self.calls.append((task, deepcopy(request)))
                assert request["repair_scope"] == "$.scenes"
                assert "cannot support narration" in request["validation_error"]
                assert "depict both endpoints" in request["validation_error"]
                assert not any(t == "direct_compact_beats" for t, _ in self.calls)
                scenes = direction()["scenes"]
                for scene in scenes:
                    scene.pop("beats")
                return {"replacement": scenes}
            return super().complete(task, request)

    def judge(premise, hypothesis):
        return {"entailment": 0 if "magical" in hypothesis else 1, "neutral": .9, "contradiction": 0}

    fixture = RepairFixture(invalid)
    with pytest.warns(CreativeAuthorityWarning):
        score = author_score("test", EVIDENCE, provider=fixture, compact=True, test_fixture=True,
                             max_repairs=1, source_judge=judge, prepare_narration=measured)
    assert len(score["scenes"]) == 2
    assert len([t for t, _ in fixture.calls if t == "repair"]) == 1


def test_explicit_source_quotation_preserves_words_and_builds_fact_endpoints():
    quoted = deepcopy(EVIDENCE)
    quoted[0]["claim"] = (
        "The rotor of a wind turbine connects to a generator. This physical "
        "connection joins the turning rotor to the generator, so the devices are connected.")
    quoted[1]["claim"] = (
        "The generator is linked to electricity as its output. The generator and "
        "its electricity are separate parts of this explanation. The generator produces electricity.")

    def visual_direction(draft):
        draft["scenes"][0]["figures"] = [figure("rotor")]
        draft["scenes"][1]["figures"] = [figure("electricity")]
        for scene in draft["scenes"]:
            for key in ("claims", "narration", "facts", "beats"):
                scene.pop(key)

    class QuotedFixture(CompactFixture):
        def complete(self, task, request):
            if task == "direct_compact":
                draft = direction()
                self.draft = deepcopy(draft)
                visual_direction(draft)
                self.calls.append((task, deepcopy(request)))
                return draft
            return super().complete(task, request)

    provider = QuotedFixture()
    common = {
        "brief": "test", "family": "ocean", "family_direction": "test",
        "context": {"narration_target_words": "45 to 55"}, "brand": {},
        "evidence": quoted, "meaning_graph": GRAPH,
    }
    result = author_compact(provider, common, {"direction_id": "test", "mode": "development",
                            "creative_authority": "P8", "status": "DEVELOPMENT_PREFLIGHT",
                            "model": provider.identity, "source": SOURCE}, measured, 0,
                            source_quote_narration=True)
    assert [scene["narration"] for scene in result["scenes"]] == [quoted[0]["claim"], quoted[1]["claim"]]
    assert [scene["claim_ids"] for scene in result["scenes"]] == [["connection"], ["output"]]
    assert all(len(scene["relations"]) == 1 for scene in result["scenes"])
    assert {actor["meaning_binding"]["entity"] for actor in result["scenes"][1]["actors"]
            if "entity" in actor["meaning_binding"]} == {"generator", "electricity"}
    request = next(request for task, request in provider.calls if task == "direct_compact")
    assert "narration" not in request["response_schema"]["properties"]["scenes"]["items"]["properties"]
    assert [block["claims"][0]["claim"] for block in request["source_quote_scenes"]] == [
        quoted[0]["claim"], quoted[1]["claim"],
    ]


def test_source_quotation_rejects_evidence_that_cannot_fit_requested_duration():
    provider = CompactFixture()
    common = {
        "brief": "test", "family": "ocean", "family_direction": "test",
        "context": {"narration_target_words": "45 to 55"}, "brand": {},
        "evidence": EVIDENCE, "meaning_graph": GRAPH,
    }
    with pytest.raises(ScoreError, match="source quotation cannot cover"):
        author_compact(provider, common, {"direction_id": "test"}, measured, 0,
                       source_quote_narration=True)
    assert provider.calls == []
