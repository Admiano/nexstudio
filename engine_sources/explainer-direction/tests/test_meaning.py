"""Synthetic meaning-bound scenes verify contracts, never production quality."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from explainer_direction.authoring import (MEANING_REVIEW_SYSTEM_PROMPT, MEANING_SYSTEM_PROMPT, SYSTEM_PROMPT, ProviderError, _explicit_transport_evidence, _fully_attested_orientation, _meaning_relation_schema,
                                          _validate_transport_source_alignment, _joint_process_entities,
                                          _plan_meaning, _scene_construction_schema, task_system_prompt,
                                          _explicit_direction_concept, _explicit_orientation_evidence,
                                          _review_meaning_graph, _schema, _unique_facts)
from explainer_direction.compiler import compile_score
from explainer_direction.contracts import ScoreError, _check, sample_score, validate_plan, validate_score
from explainer_direction.meaning import entity_claims, spatial_support_claims, validate_meaning
from explainer_direction.quality import audit_aspects
from explainer_direction.source_grounding import check_source_facts


def meaning_score():
    score = sample_score()
    source = deepcopy(score["evidence"][0]["source"])
    score["evidence"] = [
        {"id": "reservoir_count", "claim": "Two reservoirs occupy different elevations.",
         "status": "supported", "source": source,
         "quantity": {"value": 2, "unit": "count", "dimension": "count"}},
        {"id": "transfer", "claim": "Water is pumped from the lower reservoir to the upper reservoir.",
         "status": "supported", "source": source},
    ]
    graph = {
        "entities": [
            {"id": "system", "kind": "system", "label": "Reservoir pair", "evidence_ids": ["reservoir_count"]},
            {"id": "upper", "kind": "place", "label": "Upper reservoir", "evidence_ids": ["reservoir_count", "transfer"]},
            {"id": "lower", "kind": "place", "label": "Lower reservoir", "evidence_ids": ["reservoir_count", "transfer"]},
            {"id": "water", "kind": "material", "label": "Water", "evidence_ids": ["transfer"]},
        ],
        "facts": [
            {"id": "elevation", "kind": "above", "from": "upper", "to": "lower", "evidence_ids": ["reservoir_count"]},
            {"id": "charging", "kind": "flows_to", "from": "lower", "to": "upper",
             "carrier": "water", "evidence_ids": ["transfer"]},
        ],
        "quantities": [{"claim_id": "reservoir_count", "subject": "system"}],
    }
    score["meaning_graph"] = graph
    scene = score["scenes"][0]
    scene["claim_ids"] = ["reservoir_count", "transfer"]
    scene["narration"] = "Water is pumped uphill between the reservoirs."
    scene["intent"] = "Make upward material transport visible."
    scene["events"] = []
    scene["composition"] = {"flow": "column", "density": "balanced", "focus": "upper_actor"}
    scene["actors"] = []
    for key in ("upper", "lower"):
        scene["actors"].append({
            "id": key + "_actor", "kind": "shape", "role": "primary",
            "label": graph["entities"][1 if key == "upper" else 2]["label"],
            "meaning": "Physical reservoir", "meaning_binding": {"entity": key},
            "evidence_ids": ["reservoir_count", "transfer"], "layout": {"anchor": "primary"},
            "payload": {"shape": "rect"}, "initial": {"opacity": 1, "position": "home", "variant": "rect"},
        })
    scene["actors"] += [
        {"id": "pipe", "kind": "connector", "role": "secondary", "label": "Upward water path",
         "meaning": "Physical charging path", "meaning_binding": {"fact": "charging"},
         "evidence_ids": ["transfer"], "layout": {"anchor": "context"},
         "payload": {"from": "lower_actor", "to": "upper_actor", "arrow": True, "routing": "elbow"},
         "initial": {"opacity": 1, "position": "home", "draw": 1}},
        {"id": "material", "kind": "particles", "role": "accent", "label": "Water",
         "meaning": "Schematic transported water, not a measured count", "meaning_binding": {"entity": "water"},
         "evidence_ids": ["transfer"], "layout": {"anchor": "context"},
         "payload": {"count": 8, "arrangement": "stream", "illustrative": True,
                     "path": {"connector": "pipe", "direction": "forward"}},
         "initial": {"opacity": 1, "position": "home", "flow": 0, "fill": 1}},
    ]
    scene["relations"] = [
        {"id": "height_relation", "kind": "above", "from": "upper_actor", "to": "lower_actor",
         "evidence_ids": ["reservoir_count"]},
    ]
    return score


def test_meaning_and_bindings_survive_native_compilation():
    score = meaning_score()
    assert validate_score(score) == score
    plans = [compile_score(score, aspect) for aspect in ("16:9", "9:16", "1:1")]
    assert audit_aspects(plans)["technical_pass"]
    for plan in plans:
        assert plan["meaning_graph"] == score["meaning_graph"]
        assert validate_plan(plan) == plan
        assert [a["meaning_binding"] for a in plan["scenes"][0]["actors"]] == [
            a["meaning_binding"] for a in score["scenes"][0]["actors"]
        ]


@pytest.mark.parametrize("field,value,fragment", [
    ("from", "water", "physical entities"),
    ("to", "lower", "distinct endpoints"),
    ("carrier", "upper", "carrier"),
    ("via", "water", "physical entity"),
    ("via", "lower", "distinct physical"),
])
def test_invalid_meaning_route_types_fail_closed(field, value, fragment):
    score = meaning_score()
    score["meaning_graph"]["facts"][1][field] = value
    with pytest.raises(ScoreError, match=fragment):
        validate_meaning(score["meaning_graph"], score["evidence"])


@pytest.mark.parametrize("binding", [{}, {"entity": "water", "fact": "charging"}, {"entity": "missing"}])
def test_actor_needs_one_known_meaning(binding):
    score = meaning_score()
    score["scenes"][0]["actors"][-1]["meaning_binding"] = binding
    with pytest.raises(ScoreError):
        validate_score(score)


def test_count_cannot_measure_a_different_entity_even_with_correct_units():
    score = meaning_score()
    actor = score["scenes"][0]["actors"][0]
    actor.update(kind="bar", meaning="Upper water level", evidence_ids=["reservoir_count"],
                 value_binding="reservoir_count")
    actor["payload"] = {"domain": [0, 3], "unit": "count", "dimension": "count", "orientation": "vertical"}
    actor["initial"] = {"opacity": 1, "position": "home", "value": 2}
    with pytest.raises(ScoreError, match="quantity bound to the depicted entity"):
        validate_score(score)


def test_wrong_carrier_and_reverse_process_are_rejected():
    score = meaning_score()
    score["meaning_graph"]["entities"].append({
        "id": "power", "kind": "energy", "label": "Electricity", "evidence_ids": ["transfer"],
    })
    material = score["scenes"][0]["actors"][-1]
    material["meaning_binding"]["entity"] = "power"
    with pytest.raises(ScoreError, match="declared carrier"):
        validate_score(score)
    material["meaning_binding"]["entity"] = "water"
    material["payload"]["path"]["direction"] = "reverse"
    with pytest.raises(ScoreError, match="contradicts the physical process"):
        validate_score(score)


def test_reversed_connector_can_preserve_forward_physical_process():
    score = meaning_score()
    pipe = score["scenes"][0]["actors"][2]
    pipe["payload"]["from"], pipe["payload"]["to"] = pipe["payload"]["to"], pipe["payload"]["from"]
    score["scenes"][0]["actors"][-1]["payload"]["path"]["direction"] = "reverse"
    assert validate_score(score)


def test_missing_spatial_fact_cannot_become_a_silent_layout_choice():
    score = meaning_score()
    score["scenes"][0]["relations"] = []
    with pytest.raises(ScoreError, match="required spatial fact") as error:
        validate_score(score)
    assert error.value.path == "$.scenes[0].relations"


def test_quantity_binding_requires_a_measured_claim():
    score = meaning_score()
    score["meaning_graph"]["quantities"] = [{"claim_id": "transfer", "subject": "water"}]
    with pytest.raises(ScoreError, match="typed quantity"):
        validate_score(score)


def test_unknown_compiled_meaning_cannot_slip_past_authored_validation():
    plan = compile_score(meaning_score(), "9:16")
    plan["scenes"][0]["actors"][0]["meaning_binding"] = {"entity": "water"}
    with pytest.raises(ScoreError):
        validate_plan(plan)


def test_selected_representation_is_an_executable_boundary():
    score = meaning_score()
    scene = score["scenes"][0]
    scene_brief = {key: scene[key] for key in ("id", "section_id", "intent", "claim_ids", "duration_ms")}
    request = {"evidence": score["evidence"], "library": [], "context": {}, "meaning_graph": score["meaning_graph"],
               "strategy": {"representation": ["shape", "particles", "connector"]}}
    schema = _scene_construction_schema(scene_brief, {}, request)
    structure = {key: deepcopy(value) for key, value in scene.items() if key != "events"}
    _check(structure, schema, "$.scene")
    kinds = {branch["properties"]["kind"]["const"] for branch in schema["properties"]["actors"]["items"]["oneOf"]}
    assert kinds == {"shape", "particles", "connector", "text"}
    assert "bar" not in kinds and "number" not in kinds
    structure["actors"][0]["meaning_binding"] = {"entity": "unadmitted"}
    with pytest.raises(ScoreError):
        _check(structure, schema, "$.scene")


LIVE_ENTITIES = [
    {"id": "reservoir_pair", "kind": "system", "label": "Two reservoirs", "evidence_ids": ["reservoirs"]},
    {"id": "upper_reservoir", "kind": "place", "label": "Upper reservoir", "evidence_ids": ["reservoirs", "charge", "discharge"]},
    {"id": "lower_reservoir", "kind": "place", "label": "Lower reservoir", "evidence_ids": ["reservoirs", "charge", "discharge"]},
    {"id": "pump_turbine", "kind": "device", "label": "Pump-turbine", "evidence_ids": ["charge", "discharge"]},
    {"id": "water", "kind": "material", "label": "Water", "evidence_ids": ["charge", "discharge"]},
    {"id": "electricity", "kind": "energy", "label": "Electricity", "evidence_ids": ["charge", "discharge"]},
]


def live_evidence():
    source = deepcopy(sample_score()["evidence"][0]["source"])
    claims = {"reservoirs": "Two reservoirs at different elevations.",
              "charge": "Electricity pumps water from the lower to the upper reservoir.",
              "discharge": "Water moves down through a turbine, generating electricity."}
    evidence = [{"id": k, "claim": v, "status": "supported", "source": source} for k, v in claims.items()]
    evidence[0]["quantity"] = {"value": 2, "unit": "count", "dimension": "count"}
    return evidence


class StagedMeaningProvider:
    is_test_fixture = True

    def __init__(self, relations):
        self.relations, self.calls = relations, []

    def complete(self, task, request):
        self.calls.append((task, deepcopy(request)))
        actual = request.get("original_task", task)
        if actual == "plan_meaning_entities":
            return {"entities": deepcopy(LIVE_ENTITIES)}
        return deepcopy(self.relations.pop(0))


def test_relation_schema_cannot_express_recorded_live_carrier_endpoint_graph():
    evidence = live_evidence()
    schema = _meaning_relation_schema(evidence, LIVE_ENTITIES)
    recorded = {"facts": [{"id": "charge_flow", "kind": "flows_to", "from": "electricity", "to": "water",
                           "evidence_ids": ["charge"], "carrier": "pump_turbine", "via": "pump_turbine"}],
                "quantity_subjects": {"reservoirs": "upper_reservoir"}}
    with pytest.raises(ScoreError):
        _check(recorded, schema, "$.meaning")
    corrected = {"facts": [{"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir", "to": "upper_reservoir",
                            "evidence_ids": ["charge"], "carrier": "water", "via": "pump_turbine"},
                           {"id": "generation", "kind": "produces", "from": "pump_turbine", "to": "electricity",
                            "evidence_ids": ["discharge"]}],
                 "quantity_subjects": {"reservoirs": "reservoir_pair"}}
    _check(corrected, schema, "$.meaning")
    flow = next(b for b in schema["properties"]["facts"]["items"]["oneOf"]
                if b["properties"]["kind"].get("enum") == ["flows_to"])
    assert set(flow["properties"]["from"]["enum"]) <= {"reservoir_pair", "upper_reservoir", "lower_reservoir", "pump_turbine"}
    assert flow["properties"]["carrier"]["enum"] == ["water", "electricity"]
    assert schema["properties"]["quantity_subjects"]["properties"]["reservoirs"]["enum"] == ["reservoir_pair"]


def test_source_grounded_qualitative_alignment_is_not_transport_or_measured_bearing():
    source = deepcopy(live_evidence()[0]["source"])
    evidence = [{"id": "orientation", "status": "supported", "source": source,
                 "claim": "A pivoting magnetized needle aligns with the local horizontal direction of Earth's magnetic field."}]
    entities = [
        {"id": "needle", "kind": "device", "label": "magnetized needle", "evidence_ids": ["orientation"]},
        {"id": "direction", "kind": "concept",
         "label": "the local horizontal direction of Earth's magnetic field", "evidence_ids": ["orientation"]},
        {"id": "field", "kind": "energy", "label": "Earth's magnetic field", "evidence_ids": ["orientation"]},
        {"id": "land", "kind": "place", "label": "land", "evidence_ids": ["orientation"]},
    ]
    relation = {"id": "orientation_fact", "kind": "aligns_with", "from": "needle", "to": "direction",
                "evidence_ids": ["orientation"]}
    graph = {"entities": entities, "facts": [relation], "quantities": []}
    schema = _meaning_relation_schema(evidence, entities)
    assert not any("flows_to" in b["properties"]["kind"]["enum"]
                   for b in schema["properties"]["facts"]["items"]["oneOf"])
    _check({"facts": [relation], "quantity_subjects": {}}, schema, "$.meaning")
    validate_meaning(graph, evidence)
    check_source_facts(graph, evidence, lambda premise, hypothesis: {
        "entailment": .9 if "aligns with" in premise and "aligns with" in hypothesis else 0,
        "neutral": .05, "contradiction": .05,
    })
    for from_id, to_id in (("field", "needle"), ("direction", "needle"), ("needle", "needle")):
        unsupported = {**relation, "from": from_id, "to": to_id}
        with pytest.raises(ScoreError):
            validate_meaning({**graph, "facts": [unsupported]}, evidence)
        if from_id != to_id:
            with pytest.raises(ScoreError):
                _check({"facts": [unsupported], "quantity_subjects": {}}, schema, "$.meaning")


def test_literal_storage_claim_limits_stored_carrier_without_affecting_transport():
    evidence = live_evidence() + [
        {"id": "storage", "claim": "The system stores energy.", "status": "supported",
         "source": deepcopy(live_evidence()[0]["source"])}
    ]
    entities = LIVE_ENTITIES + [
        {"id": "energy", "kind": "energy", "label": "energy", "evidence_ids": ["storage"]}
    ]
    schema = _meaning_relation_schema(evidence, entities)
    branches = schema["properties"]["facts"]["items"]["oneOf"]
    stores = next(b for b in branches if b["properties"]["kind"]["enum"] == ["stores"])
    flow = next(b for b in branches if b["properties"]["kind"]["enum"] == ["flows_to"])
    assert stores["properties"]["to"]["enum"] == ["energy"]
    assert set(flow["properties"]["carrier"]["enum"]) == {"water", "electricity", "energy"}
    incorrect = {"facts": [{"id": "stored", "kind": "stores", "from": "reservoir_pair",
                            "to": "electricity", "evidence_ids": ["storage"]}],
                 "quantity_subjects": {"reservoirs": "reservoir_pair"}}
    with pytest.raises(ScoreError):
        _check(incorrect, schema, "$.meaning")


def test_transport_corroboration_requires_carrier_movement_not_mention():
    evidence = live_evidence()
    charge = next(record for record in evidence if record["id"] == "charge")
    charge["claim"] = "Electricity is used to pump water from the lower reservoir into the upper reservoir."
    graph = {"entities": LIVE_ENTITIES}
    flow = {"kind": "flows_to", "from": "lower_reservoir", "to": "upper_reservoir",
            "carrier": "water", "evidence_ids": ["charge"]}
    assert _explicit_transport_evidence(flow, graph, evidence)
    flow["carrier"] = "electricity"
    assert not _explicit_transport_evidence(flow, graph, evidence)
    flow["carrier"] = "water"
    charge["claim"] = "Water is pumped from the lower reservoir into the upper reservoir."
    assert _explicit_transport_evidence(flow, graph, evidence)


def test_cited_transport_segments_bind_to_the_same_driving_activity_and_direction():
    evidence = live_evidence()
    next(r for r in evidence if r["id"] == "charge")["claim"] = (
        "Charging pumps water from the lower reservoir into the upper reservoir."
    )
    graph = {"entities": LIVE_ENTITIES + [
        {"id": "charging_process", "kind": "process", "label": "charging", "evidence_ids": ["charge"]},
        {"id": "discharging_process", "kind": "process", "label": "discharging", "evidence_ids": ["discharge"]},
    ], "facts": [
        {"id": "charge_first", "kind": "flows_to", "from": "lower_reservoir", "to": "pump_turbine",
         "carrier": "water", "process": "charging_process", "evidence_ids": ["charge"]},
        {"id": "charge_second", "kind": "flows_to", "from": "pump_turbine", "to": "upper_reservoir",
         "carrier": "water", "process": "charging_process", "evidence_ids": ["charge"]},
        {"id": "discharge_first", "kind": "flows_to", "from": "upper_reservoir", "to": "pump_turbine",
         "carrier": "water", "process": "discharging_process", "evidence_ids": ["discharge"]},
        {"id": "discharge_second", "kind": "flows_to", "from": "pump_turbine", "to": "lower_reservoir",
         "carrier": "water", "process": "discharging_process", "evidence_ids": ["discharge"]},
    ]}
    _validate_transport_source_alignment(graph, evidence)
    mixed = deepcopy(graph)
    mixed["facts"][0]["process"] = "discharging_process"
    mixed["facts"][0]["evidence_ids"].append("discharge")
    with pytest.raises(ScoreError, match="conflicts with cited activity"):
        _validate_transport_source_alignment(mixed, evidence)
    backward = deepcopy(graph)
    backward["facts"][3]["process"] = "charging_process"
    backward["facts"][3]["evidence_ids"] = ["charge"]
    with pytest.raises(ScoreError, match="returns to the source"):
        _validate_transport_source_alignment(backward, evidence)


def test_staged_meaning_repairs_relations_without_redrafting_entities():
    evidence = live_evidence()
    bad = {"facts": [{"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir", "to": "lower_reservoir",
                      "evidence_ids": ["charge"], "carrier": "water"}],
           "quantity_subjects": {"reservoirs": "reservoir_pair"}}
    good = {"facts": [{"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir", "to": "upper_reservoir",
                       "evidence_ids": ["charge"], "carrier": "water", "via": "pump_turbine"}],
            "quantity_subjects": {"reservoirs": "reservoir_pair"}}
    provider = StagedMeaningProvider([bad, good])
    graph = _plan_meaning(provider, {"evidence": evidence}, evidence, 2)
    assert graph["entities"] == LIVE_ENTITIES
    assert graph["quantities"] == [{"claim_id": "reservoirs", "subject": "reservoir_pair"}]
    assert [task for task, _ in provider.calls] == ["plan_meaning_entities", "plan_meaning_relations", "repair"]
    assert provider.calls[2][1]["meaning_entities"] == LIVE_ENTITIES


def test_staged_meaning_rejects_missing_quantity_answer():
    evidence = live_evidence()
    partial = {"facts": [{"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir", "to": "upper_reservoir",
                          "evidence_ids": ["charge"], "carrier": "water"}], "quantity_subjects": {}}
    with pytest.raises(ScoreError, match="exhausted"):
        _plan_meaning(StagedMeaningProvider([partial, partial]), {"evidence": evidence}, evidence, 1)


def test_meaning_uses_source_only_inputs_and_not_visual_instruction():
    evidence = live_evidence()
    valid = {"facts": [{"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir", "to": "upper_reservoir",
                       "evidence_ids": ["charge"], "carrier": "water"}], "quantity_subjects": {"reservoirs": "reservoir_pair"}}
    provider = StagedMeaningProvider([valid])
    _plan_meaning(provider, {"evidence": evidence, "brief": "Invent a metaphor that is not a fact.",
                            "capabilities": {"visual": "irrelevant"},
                            "context": {"art_direction": "irrelevant"}}, evidence, 0)
    for task, request in provider.calls:
        assert "capabilities" not in request and "context" not in request and "brief" not in request
        assert task_system_prompt(task, request) == MEANING_SYSTEM_PROMPT
    assert task_system_prompt("repair", {"original_task": "plan_meaning_relations"}) == MEANING_SYSTEM_PROMPT
    assert task_system_prompt("review_meaning", {}) == MEANING_REVIEW_SYSTEM_PROMPT
    assert task_system_prompt("author_scene", {}) == SYSTEM_PROMPT


def test_meaning_scoped_patch_preserves_other_facts_and_quantity_decisions():
    evidence = live_evidence()
    fact = {"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir", "to": "upper_reservoir",
            "evidence_ids": ["charge"], "carrier": "water"}
    other = {"id": "elevation", "kind": "above", "from": "upper_reservoir", "to": "lower_reservoir",
             "evidence_ids": ["reservoirs"]}
    bad = {"facts": [{**fact, "to": "lower_reservoir"}, other],
           "quantity_subjects": {"reservoirs": "reservoir_pair"}}

    class PatchProvider(StagedMeaningProvider):
        supports_schema_patch = True

        def complete(self, task, request):
            if task == "repair":
                self.calls.append((task, deepcopy(request)))
                assert request["repair_mode"] == "scoped_patch"
                return {"replacement": fact}
            return super().complete(task, request)

    provider = PatchProvider([bad])
    graph = _plan_meaning(provider, {"evidence": evidence}, evidence, 1)
    assert graph["facts"] == [fact, other]
    assert graph["quantities"] == [{"claim_id": "reservoirs", "subject": "reservoir_pair"}]


def test_causation_does_not_create_carrier_and_material_does_not_produce_energy():
    evidence = live_evidence()
    entities = LIVE_ENTITIES + [
        {"id": "pumping", "kind": "process", "label": "Pumping water",
         "evidence_ids": ["charge"]},
    ]
    schema = _meaning_relation_schema(evidence, entities)
    for wrong in (
        {"id": "power_creates_water", "kind": "causes", "from": "electricity",
         "to": "water", "evidence_ids": ["charge"]},
        {"id": "water_creates_electricity", "kind": "produces", "from": "water",
         "to": "electricity", "evidence_ids": ["discharge"]},
    ):
        graph = {"entities": entities, "facts": [wrong], "quantities": []}
        with pytest.raises(ScoreError):
            validate_meaning(graph, evidence)
        with pytest.raises(ScoreError):
            _check({"facts": [wrong], "quantity_subjects": {"reservoirs": "reservoir_pair"}}, schema, "$.meaning")
    for supported in (
        {"id": "energy_input", "kind": "powers", "from": "electricity",
         "to": "pump_turbine", "evidence_ids": ["charge"]},
        {"id": "generation", "kind": "produces", "from": "pump_turbine",
         "to": "electricity", "evidence_ids": ["discharge"]},
        {"id": "pumping_link", "kind": "causes", "from": "electricity",
         "to": "pumping", "evidence_ids": ["charge"]},
    ):
        validate_meaning({"entities": entities, "facts": [supported], "quantities": []}, evidence)
        _check({"facts": [supported], "quantity_subjects": {"reservoirs": "reservoir_pair"}}, schema, "$.meaning")


def test_transport_process_is_not_route_endpoint():
    evidence = live_evidence()
    entities = LIVE_ENTITIES + [{"id": "pumping", "kind": "process",
                                 "label": "Pumping water", "evidence_ids": ["charge"]}]
    valid = {"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir",
             "to": "upper_reservoir", "carrier": "water", "via": "pump_turbine",
             "process": "pumping", "evidence_ids": ["charge"]}
    graph = {"entities": entities, "facts": [valid], "quantities": []}
    validate_meaning(graph, evidence)
    schema = _meaning_relation_schema(evidence, entities)
    _check({"facts": [valid], "quantity_subjects": {"reservoirs": "reservoir_pair"}}, schema, "$.meaning")
    for broken in ({**valid, "process": "pump_turbine"},
                   {**valid, "from": "pumping"}):
        with pytest.raises(ScoreError):
            validate_meaning({**graph, "facts": [broken]}, evidence)
        with pytest.raises(ScoreError):
            _check({"facts": [broken], "quantity_subjects": {"reservoirs": "reservoir_pair"}},
                   schema, "$.meaning")


def test_missing_counted_collection_is_appended_without_rewriting_entities():
    evidence = live_evidence()
    initial = [e for e in LIVE_ENTITIES if e["id"] != "reservoir_pair"]
    addition = {"id": f"semantic_addition_{len(initial)}", "kind": "system",
                "label": "reservoirs", "evidence_ids": ["reservoirs"]}
    facts = [{"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir",
              "to": "upper_reservoir", "evidence_ids": ["charge"], "carrier": "water"}]

    class AppendProvider:
        is_test_fixture = True
        supports_schema_patch = True

        def __init__(self):
            self.calls = []

        def complete(self, task, request):
            self.calls.append((task, deepcopy(request)))
            if task == "plan_meaning_entities":
                return {"entities": deepcopy(initial)}
            if task == "repair":
                assert request["repair_mode"] == "scoped_append"
                assert request["accepted_entities"] == initial
                return {"new_entity": deepcopy(addition)}
            return {"facts": deepcopy(facts), "quantity_subjects": {"reservoirs": addition["id"]}}

    provider = AppendProvider()
    graph = _plan_meaning(provider, {}, evidence, 1)
    assert graph["entities"] == [*initial, addition]
    assert graph["quantities"] == [{"claim_id": "reservoirs", "subject": addition["id"]}]
    assert [name for name, _ in provider.calls] == [
        "plan_meaning_entities", "repair", "plan_meaning_relations",
    ]


def test_explicitly_stored_carrier_needs_a_separate_sourced_entity():
    from explainer_direction.authoring import _explicit_stored_carrier

    evidence = {"id": "storage", "claim": "The system stores energy and releases it.",
                "quantity": None}
    entities = [{"id": "electricity", "kind": "energy", "label": "Electricity",
                 "evidence_ids": ["storage"]}]
    with pytest.raises(ScoreError, match="stored carrier energy"):
        _explicit_stored_carrier(evidence, entities)
    entities.append({"id": "stored_energy", "kind": "energy", "label": "Stored energy",
                     "evidence_ids": ["storage"]})
    _explicit_stored_carrier(evidence, entities)


def test_review_cannot_rewrite_explicitly_sourced_transport_on_false_alarm():
    evidence = live_evidence()
    evidence[1]["claim"] = "Electricity pumps water from the lower reservoir into the upper reservoir."
    flow = {"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir",
            "to": "upper_reservoir", "evidence_ids": ["charge"], "carrier": "water"}

    class FalseReview(StagedMeaningProvider):
        is_test_fixture = False
        supports_schema_patch = True

        def complete(self, task, request):
            if task == "review_meaning":
                self.calls.append((task, deepcopy(request)))
                return {"verdict": "revise", "issues": [{
                    "claim_id": "charge", "fact_id": request["meaning_graph"]["facts"][0]["id"],
                    "category": "wrong_direction", "evidence_quote": evidence[1]["claim"],
                    "explanation": "The valid direction is purportedly incorrect.",
                }]}
            return super().complete(task, request)

    provider = FalseReview([{"facts": [flow], "quantity_subjects": {"reservoirs": "reservoir_pair"}}])
    with pytest.raises(ProviderError, match="directly attested transport"):
        _plan_meaning(provider, {}, evidence, 2)
    assert [task for task, _ in provider.calls] == [
        "plan_meaning_entities", "plan_meaning_relations", "review_meaning", "review_meaning",
    ]
    assert provider.calls[-1][1]["meaning_graph"] == provider.calls[-2][1]["meaning_graph"]
    assert provider.calls[-1][1]["invalid_review"]["issues"][0]["category"] == "wrong_direction"


def test_false_transport_review_is_retried_not_accepted_or_used_to_rewrite_graph():
    evidence = live_evidence()
    evidence[1]["claim"] = "Water is pumped from the lower reservoir into the upper reservoir."
    flow = {"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir",
            "to": "upper_reservoir", "evidence_ids": ["charge"], "carrier": "water"}

    class CorrectedReview(StagedMeaningProvider):
        is_test_fixture = False

        def complete(self, task, request):
            if task == "review_meaning":
                self.calls.append((task, deepcopy(request)))
                if "invalid_review" in request:
                    return {"verdict": "accept", "issues": []}
                return {"verdict": "revise", "issues": [{
                    "claim_id": "charge", "fact_id": request["meaning_graph"]["facts"][0]["id"],
                    "category": "wrong_direction",
                    "evidence_quote": evidence[1]["claim"],
                    "explanation": "An invalid complaint about the explicitly attested direction.",
                }]}
            return super().complete(task, request)

    provider = CorrectedReview([{"facts": [flow], "quantity_subjects": {"reservoirs": "reservoir_pair"}}])
    graph = _plan_meaning(provider, {}, evidence, 1)
    assert graph["facts"] == [flow]
    assert [task for task, _ in provider.calls].count("review_meaning") == 2
    assert all(task != "repair" for task, _ in provider.calls)
    attested = provider.calls[-1][1]["source_attested_routes"]
    assert len(attested) == 1 and attested[0]["fact_id"] == "review_fact_0"
    assert attested[0]["evidence"][0]["claim"] == evidence[1]["claim"]


def test_source_veto_deletes_only_rejected_fact_without_asking_model_to_replace_it():
    evidence = live_evidence()
    flow = {"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir",
            "to": "upper_reservoir", "evidence_ids": ["charge"], "carrier": "water"}
    unsupported = {"id": "unsupported", "kind": "connected_to", "from": "lower_reservoir",
                   "to": "upper_reservoir", "evidence_ids": ["charge"]}

    class NoOpRepair(StagedMeaningProvider):
        is_test_fixture = False
        supports_schema_patch = True

        def complete(self, task, request):
            if task == "review_meaning":
                rejected = next((f for f in request["meaning_graph"]["facts"]
                                 if f["kind"] == "connected_to"), None)
                if rejected is None:
                    return {"verdict": "accept", "issues": []}
                return {"verdict": "revise", "issues": [{
                    "claim_id": "charge", "fact_id": rejected["id"], "category": "unsupported_relation",
                    "evidence_quote": evidence[1]["claim"],
                    "explanation": "The proposed fact must be revised.",
                }]}
            if task == "repair":
                raise AssertionError("a deletion-only source veto must not ask the model")
            return super().complete(task, request)

    provider = NoOpRepair([{"facts": [flow, unsupported], "quantity_subjects": {"reservoirs": "reservoir_pair"}}])
    assert _plan_meaning(provider, {}, evidence, 2)["facts"] == [flow]


def test_independent_source_veto_is_atomic_and_does_not_approve_causes_or_contains():
    score = meaning_score()
    graph, evidence = score["meaning_graph"], score["evidence"]
    probes = []

    def judge(premise, hypothesis):
        probes.append((premise, hypothesis))
        if "via pump" in hypothesis:
            return {"entailment": .001, "neutral": .999, "contradiction": 0}
        return {"entailment": .999, "neutral": .001, "contradiction": 0}

    check_source_facts(graph, evidence, judge)
    assert len(probes) == 2
    assert "Two reservoirs" in probes[0][0] and "Water is pumped" in probes[0][0]
    annotated = deepcopy(graph)
    annotated["entities"].append({
        "id": "pump", "kind": "device", "label": "pump", "evidence_ids": ["transfer"],
    })
    annotated["facts"][1]["via"] = "pump"
    with pytest.raises(ScoreError, match="charging.via"):
        check_source_facts(annotated, evidence, judge)
    assert "via pump" in probes[-1][1]

    causal = {"entities": [
        {"id": "charging", "kind": "process", "label": "charging", "evidence_ids": ["charge"]},
        {"id": "discharging", "kind": "process", "label": "discharging", "evidence_ids": ["discharge"]},
    ], "facts": [{"id": "bad", "kind": "causes", "from": "charging", "to": "discharging",
                  "evidence_ids": ["charge", "discharge"]}]}
    claims = [{"id": "charge", "claim": "Charging moves water uphill."},
              {"id": "discharge", "claim": "Discharging moves water downhill."}]
    with pytest.raises(ScoreError, match="not source-stated causation"):
        check_source_facts(causal, claims, judge)
    causal["entities"][0].update(id="storage", kind="system", label="storage")
    causal["entities"][1].update(id="electricity", kind="energy", label="electricity")
    causal["facts"][0].update(kind="contains", **{"from": "storage", "to": "electricity"})
    claims[0]["claim"] = "Storage stores energy."
    with pytest.raises(ScoreError, match="not evidence of physical containment"):
        check_source_facts(causal, claims, judge)


def test_unsupported_meaning_fact_can_be_removed_without_rewriting_valid_fact():
    from explainer_direction.authoring import _bounded
    evidence = live_evidence()
    good = {"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir",
            "to": "upper_reservoir", "evidence_ids": ["charge"], "carrier": "water"}
    bad = {"id": "invented", "kind": "connected_to", "from": "pump_turbine",
           "to": "reservoir_pair", "evidence_ids": ["discharge"]}
    request = {"response_schema": _meaning_relation_schema(evidence, LIVE_ENTITIES)}

    class Repair(StagedMeaningProvider):
        supports_schema_patch = True

        def complete(self, task, requested):
            if task == "repair":
                assert requested["response_schema"]["properties"]["replacement"] == {"type": "null"}
                return {"replacement": None}
            return super().complete(task, requested)

    provider = Repair([{"facts": [good, bad], "quantity_subjects": {"reservoirs": "reservoir_pair"}}])

    def validate(response):
        if any(f["id"] == "invented" for f in response["facts"]):
            raise ScoreError("source preflight cannot support invented: ungrounded", "$.meaning.facts[1]")
        return response

    answer = _bounded(provider, "plan_meaning_relations", request, validate, 1)
    assert answer["facts"] == [good]
    assert [task for task, _ in provider.calls] == ["plan_meaning_relations"]


def test_static_alignment_is_not_causation_or_storage_even_with_confident_nli():
    graph = {"entities": [
        {"id": "wind", "kind": "material", "label": "wind", "evidence_ids": ["orientation"]},
        {"id": "alignment", "kind": "process", "label": "vane alignment", "evidence_ids": ["orientation"]},
        {"id": "vane", "kind": "device", "label": "wind vane", "evidence_ids": ["orientation"]},
    ], "facts": [{"id": "invented", "kind": "causes", "from": "wind", "to": "alignment",
                  "evidence_ids": ["orientation"]}]}
    evidence = [{"id": "orientation", "claim": "A wind vane aligns with the direction of local wind."}]
    def judge(premise, hypothesis):
        return {"entailment": .999, "neutral": .001, "contradiction": 0}
    with pytest.raises(ScoreError, match="not source-stated causation"):
        check_source_facts(graph, evidence, judge)
    graph["facts"][0].update(kind="stores", **{"from": "vane", "to": "wind"})
    with pytest.raises(ScoreError, match="not source-stated storage"):
        check_source_facts(graph, evidence, judge)
    graph["facts"][0].update(kind="causes", **{"from": "wind", "to": "alignment"})
    evidence[0]["claim"] = "Wind can change the orientation of a wind vane."
    check_source_facts(graph, evidence, judge)


def test_orientation_citations_are_checked_independently():
    graph = {"entities": [
        {"id": "vane", "kind": "device", "label": "wind vane", "evidence_ids": ["orientation"]},
        {"id": "direction", "kind": "concept", "label": "direction of local wind", "evidence_ids": ["orientation"]},
    ], "facts": [{"id": "alignment", "kind": "aligns_with", "from": "vane", "to": "direction",
                  "evidence_ids": ["orientation", "other"]}]}
    evidence = [{"id": "orientation", "claim": "A wind vane aligns with the direction of local wind."},
                {"id": "other", "claim": "A wind vane rotates on a bearing."}]
    def judge(premise, hypothesis):
        return {"entailment": .999 if "aligns" in premise else .001,
                "neutral": .001 if "aligns" in premise else .999, "contradiction": 0}
    with pytest.raises(ScoreError, match="cannot support alignment"):
        check_source_facts(graph, evidence, judge)
    graph["facts"][0]["evidence_ids"] = ["orientation"]
    check_source_facts(graph, evidence, judge)


def test_live_meaning_review_rejects_missing_fact_before_scene_authoring():
    evidence = live_evidence()
    flow = {"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir",
            "to": "upper_reservoir", "evidence_ids": ["charge"], "carrier": "water"}
    height = {"id": "height", "kind": "above", "from": "upper_reservoir",
              "to": "lower_reservoir", "evidence_ids": ["reservoirs", "charge"]}

    class ReviewingProvider(StagedMeaningProvider):
        is_test_fixture = False

        def complete(self, task, request):
            if task == "review_meaning":
                self.calls.append((task, deepcopy(request)))
                if not any(f["kind"] == "above" for f in request["meaning_graph"]["facts"]):
                    return {"verdict": "revise", "issues": [{
                        "claim_id": "reservoirs", "fact_id": None,
                        "category": "missing_relation", "evidence_quote": evidence[0]["claim"],
                        "explanation": "Reservoirs occupy different elevations but no height relation is recorded.",
                    }]}
                return {"verdict": "accept", "issues": []}
            return super().complete(task, request)

    initial = {"facts": [flow], "quantity_subjects": {"reservoirs": "reservoir_pair"}}
    revised = {"facts": [flow, height], "quantity_subjects": {"reservoirs": "reservoir_pair"}}
    class ScopedReviewProvider(ReviewingProvider):
        supports_schema_patch = True

        def complete(self, task, request):
            if task == "repair":
                self.calls.append((task, deepcopy(request)))
                assert request["repair_mode"] == "scoped_append"
                assert request["accepted_facts"] == [flow]
                return {"new_fact": height}
            return super().complete(task, request)

    provider = ScopedReviewProvider([initial, revised])
    graph = _plan_meaning(provider, {"evidence": evidence}, evidence, 1)
    assert graph["facts"] == revised["facts"] and graph["entities"] == LIVE_ENTITIES
    assert [task for task, _ in provider.calls] == [
        "plan_meaning_entities", "plan_meaning_relations", "review_meaning", "repair", "review_meaning",
    ]
    for task, request in provider.calls:
        assert "context" not in request
        expected = MEANING_REVIEW_SYSTEM_PROMPT if task == "review_meaning" else MEANING_SYSTEM_PROMPT
        assert task_system_prompt(task, request) == expected


def test_definition_and_relation_provenance_can_differ_without_losing_spatial_support():
    score = meaning_score()
    for entity in score["meaning_graph"]["entities"]:
        if entity["id"] in ("upper", "lower"):
            entity["evidence_ids"] = ["reservoir_count"]
    validate_meaning(score["meaning_graph"], score["evidence"])
    claims = entity_claims(score["meaning_graph"])
    assert claims["upper"] == claims["lower"] == {"reservoir_count", "transfer"}
    assert spatial_support_claims(["transfer"], score["meaning_graph"]) == ["reservoir_count"]
    assert spatial_support_claims(["reservoir_count"], score["meaning_graph"]) == []
    for aspect in ("16:9", "9:16", "1:1"):
        validate_plan(compile_score(score, aspect))


@pytest.mark.parametrize("claim,label", [
    ("A wind vane aligns with the local direction of the wind.",
     "local direction of the wind"),
    ("A camera points along the forward direction of the robot, not toward a location.",
     "forward direction of the robot"),
])
def test_source_stated_direction_is_a_separate_literal_concept(claim, label):
    record = {"id": "orientation", "claim": claim}
    participant = {"id": "physical", "kind": "device", "label": "physical participant",
                   "evidence_ids": ["orientation"]}
    with pytest.raises(ScoreError, match="literal direction concept"):
        _explicit_direction_concept(record, [participant])
    direction = {"id": "direction", "kind": "concept", "label": label,
                 "evidence_ids": ["orientation"]}
    assert _explicit_direction_concept(record, [participant, direction]) == "direction"
    with pytest.raises(ScoreError):
        _explicit_direction_concept(record, [participant, {**direction, "kind": "place"}])


def test_literal_source_attested_orientation_is_preverified_but_other_facts_remain_under_review():
    claim = "A wind vane aligns with the local direction of the wind, not toward a single point."
    evidence = [{"id": "orientation", "claim": claim, "status": "supported",
                 "source": deepcopy(sample_score()["evidence"][0]["source"])}]
    graph = {"entities": [
        {"id": "vane", "kind": "device", "label": "wind vane", "evidence_ids": ["orientation"]},
        {"id": "wind", "kind": "material", "label": "wind", "evidence_ids": ["orientation"]},
        {"id": "direction", "kind": "concept", "label": "local direction of the wind",
         "evidence_ids": ["orientation"]},
    ], "facts": [{"id": "alignment", "kind": "aligns_with", "from": "vane", "to": "direction",
                 "evidence_ids": ["orientation"]}], "quantities": []}
    assert _explicit_orientation_evidence(graph["facts"][0], graph, evidence)
    assert not _explicit_orientation_evidence({**graph["facts"][0], "to": "wind"}, graph, evidence)
    assert not _explicit_orientation_evidence({**graph["facts"][0], "evidence_ids": []}, graph, evidence)
    assert _fully_attested_orientation(graph["facts"][0], graph, evidence)
    wrong_subject = deepcopy(graph)
    wrong_subject["entities"][0]["label"] = "weather vane"
    assert not _fully_attested_orientation(graph["facts"][0], wrong_subject, evidence)
    assert not _fully_attested_orientation({**graph["facts"][0], "evidence_ids": ["orientation", "other"]},
                                          graph, evidence)
    graph["facts"].append({"id": "unsupported", "kind": "causes", "from": "wind", "to": "vane",
                           "evidence_ids": ["orientation"]})
    issue = {"claim_id": "orientation", "fact_id": "unsupported", "category": "unsupported_relation",
             "evidence_quote": claim, "explanation": "Wind is not claimed to cause the vane itself."}

    class Reviewer:
        def __init__(self):
            self.calls = []

        def complete(self, task, request):
            assert task == "review_meaning"
            self.calls.append(deepcopy(request))
            return {"verdict": "revise", "issues": [{**issue, "fact_id": "review_fact_1"}]}

    reviewer = Reviewer()
    schema = _schema({"verdict": {"enum": ["accept", "revise"]},
                      "issues": {"type": "array", "maxItems": 1, "items": _schema({
                          "claim_id": {"enum": ["orientation"]},
                          "fact_id": {"enum": ["unsupported"]},
                          "category": {"enum": ["unsupported_relation"]},
                          "evidence_quote": {"type": "string", "minLength": 3},
                          "explanation": {"type": "string", "minLength": 8},
                      })}})
    assert _review_meaning_graph(reviewer, {"evidence": evidence}, graph, schema)["issues"] == [issue]
    assert len(reviewer.calls) == 1
    assert reviewer.calls[0]["meaning_graph"] == {
        **graph, "facts": [{**fact, "id": f"review_fact_{i}"} for i, fact in enumerate(graph["facts"])]}
    assert reviewer.calls[0]["source_attested_orientations"][0]["fact_id"] == "review_fact_0"


def test_equivalent_facts_coalesce_but_different_provenance_or_process_does_not():
    fact = {"id": "first", "kind": "flows_to", "from": "lower", "to": "upper",
            "carrier": "water", "evidence_ids": ["charge"]}
    duplicate = {**fact, "id": "duplicate"}
    other_source = {**fact, "id": "other_source", "evidence_ids": ["discharge"]}
    process = {**fact, "id": "process", "process": "pumping"}
    assert _unique_facts([fact, duplicate, other_source, process]) == [fact, other_source, process]


@pytest.mark.parametrize("veto", ["review", "nli"])
def test_review_repair_uses_original_indices_after_equivalent_facts_coalesce(veto):
    evidence = live_evidence()
    valid = {"id": "charge_flow", "kind": "flows_to", "from": "lower_reservoir",
             "to": "upper_reservoir", "carrier": "water", "evidence_ids": ["charge"]}
    duplicate = {**valid, "id": "duplicate"}
    unsupported = {"id": "unsupported", "kind": "connected_to", "from": "lower_reservoir",
                   "to": "upper_reservoir", "evidence_ids": ["charge"]}

    class ReviewedDuplicates(StagedMeaningProvider):
        is_test_fixture = False
        supports_schema_patch = True

        def complete(self, task, request):
            if task == "review_meaning":
                self.calls.append((task, deepcopy(request)))
                branches = request["response_schema"]["properties"]["issues"]["items"]["oneOf"]
                assert all("duplicate" not in branch["properties"]["fact_id"]["enum"] for branch in branches)
                claims = {record["id"]: record["claim"] for record in evidence}
                assert all(branch["properties"]["evidence_quote"]["const"]
                           == claims[branch["properties"]["claim_id"]["const"]] for branch in branches)
                if len(request["meaning_graph"]["facts"]) == 1:
                    return {"verdict": "accept", "issues": []}
                return {"verdict": "revise", "issues": [{
                    "claim_id": "charge", "fact_id": request["meaning_graph"]["facts"][1]["id"],
                    "category": "unsupported_relation", "evidence_quote": evidence[1]["claim"],
                    "explanation": "Transport does not establish a direct physical connection.",
                }]}
            if task == "repair":
                self.calls.append((task, deepcopy(request)))
                assert request["repair_scope"] == "$.meaning.facts[2]"
                assert request["invalid_item"] == unsupported
                _check({"replacement": None}, request["response_schema"], "$.repair")
                with pytest.raises(ScoreError):
                    _check({"replacement": valid}, request["response_schema"], "$.repair")
                return {"replacement": None}
            return super().complete(task, request)

    provider = ReviewedDuplicates([{"facts": [valid, duplicate, unsupported],
                                   "quantity_subjects": {"reservoirs": "reservoir_pair"}}])
    def judge(premise, hypothesis):
        rejected = "connected to" in hypothesis
        return {"entailment": 0.01 if rejected else 0.98,
                "neutral": 0.01, "contradiction": 0.98 if rejected else 0.01}

    graph = _plan_meaning(provider, {}, evidence, 1,
                          source_judge=judge if veto == "nli" else None)
    assert graph["facts"] == [valid]


@pytest.mark.parametrize("claim", [
    "Compression and release produce a pressure pulse.",
    "This compression and release together produce a pressure pulse.",
])
def test_joint_process_preserves_its_source_stated_cause_before_nli(claim):
    evidence = [{"id": "joint_output", "claim": claim, "status": "supported",
                 "source": deepcopy(sample_score()["evidence"][0]["source"])}]
    graph = {
        "entities": [
            {"id": "compression", "kind": "process", "label": "rapid compression",
             "evidence_ids": ["joint_output"]},
            {"id": "release", "kind": "process", "label": "release of the gas",
             "evidence_ids": ["joint_output"]},
            {"id": "joint", "kind": "process", "label": "compression and release",
             "evidence_ids": ["joint_output"]},
            {"id": "pulse", "kind": "signal", "label": "pressure pulse",
             "evidence_ids": ["joint_output"]},
        ],
        "facts": [{"id": "output", "kind": "produces", "from": "joint", "to": "pulse",
                   "evidence_ids": ["joint_output"]}],
        "quantities": [],
    }
    calls = []
    def overconfident(premise, hypothesis):
        calls.append((premise, hypothesis))
        return {"entailment": .99, "neutral": .005, "contradiction": .005}

    assert validate_meaning(graph, evidence) == graph
    check_source_facts(graph, evidence, overconfident)
    assert calls[-1][1] == "compression and release produces pressure pulse."
    for constituent in ("compression", "release"):
        split = deepcopy(graph)
        split["facts"][0]["from"] = constituent
        before = len(calls)
        with pytest.raises(ScoreError, match="joint process"):
            check_source_facts(split, evidence, overconfident)
        assert len(calls) == before
    individual = deepcopy(evidence)
    individual[0]["claim"] += " Release independently produces the pulse."
    split["facts"][0]["from"] = "release"
    check_source_facts(split, individual, overconfident)


def test_joint_source_normalization_preserves_original_participants_without_inventing_facts():
    source = deepcopy(sample_score()["evidence"][0]["source"])
    evidence = [
        {"id": "compression", "claim": "The gas undergoes rapid compression.",
         "status": "supported", "source": source},
        {"id": "release", "claim": "The gas is released.",
         "status": "supported", "source": source},
        {"id": "joint", "claim": "This compression and release produce a pressure pulse.",
         "status": "supported", "source": source},
    ]
    entities = [
        {"id": "compression", "kind": "process", "label": "rapid compression of gas",
         "evidence_ids": ["compression"]},
        {"id": "release", "kind": "process", "label": "release of gas",
         "evidence_ids": ["release"]},
    ]
    normalized = _joint_process_entities(entities, evidence)
    assert normalized[:2] == entities and len(entities) == 2
    combined = normalized[-1]
    assert combined["kind"] == "process" and combined["label"] == "compression and release"
    assert combined["evidence_ids"] == ["joint"]
    assert combined["id"].startswith("source_joint_")
    assert _joint_process_entities(normalized, evidence) == normalized
    assert _joint_process_entities(list(reversed(entities)), evidence)[-1] == combined
    physical = deepcopy(entities)
    physical[0]["kind"] = "device"
    assert _joint_process_entities(physical, evidence) == physical
    ambiguous = deepcopy(evidence)
    ambiguous[-1]["claim"] += " Compression separately produces a pulse."
    assert _joint_process_entities(entities, ambiguous) == entities


def test_deterministic_source_deletions_do_not_consume_model_repair_budget(monkeypatch):
    from explainer_direction import authoring

    class NoModel:
        supports_schema_patch = True

        def complete(self, *args, **kwargs):
            raise AssertionError("deterministic deletion must not call the model")

    def veto(response):
        for index, fact in enumerate(response["facts"]):
            if fact["id"].startswith("bad"):
                raise ScoreError("source veto", f"$.meaning.facts[{index}]")
        return response

    def patch(task, request, response, path, exc):
        index = int(path.rsplit("[", 1)[1].rstrip("]"))
        return "facts", index, {"properties": {"replacement": {"type": "null"}}}

    monkeypatch.setattr(authoring, "_meaning_value_patch", patch)
    initial = {"facts": [{"id": f"bad_{n}"} for n in range(5)] + [{"id": "kept"}]}
    result = authoring._bounded(NoModel(), "plan_meaning_relations", {}, veto, 0, initial)
    assert result == {"facts": [{"id": "kept"}]}


def test_joint_source_cause_requires_a_fact_even_when_a_reviewer_would_accept():
    source = deepcopy(sample_score()["evidence"][0]["source"])
    evidence = [{"id": "joint", "claim": "Compression and release produce a pressure pulse.",
                 "status": "supported", "source": source},
                {"id": "baseline", "claim": "A pump causes compression.",
                 "status": "supported", "source": source}]
    baseline = {"id": "baseline_fact", "kind": "causes", "from": "pump",
                "to": "compression", "evidence_ids": ["baseline"]}
    class JointFixture:
        is_test_fixture = True
        supports_schema_patch = True
        def __init__(self):
            self.calls = []
        def complete(self, task, request):
            self.calls.append(task)
            if task == "plan_meaning_entities":
                return {"entities": [
                    {"id": name, "kind": kind, "label": label, "evidence_ids": cites}
                    for name, kind, label, cites in [
                        ("compression", "process", "Compression", ["joint", "baseline"]),
                        ("release", "process", "Release", ["joint"]),
                        ("pulse", "signal", "Pressure pulse", ["joint"]),
                        ("pump", "device", "Pump", ["baseline"])]]}
            if task == "plan_meaning_relations":
                return {"facts": [baseline], "quantity_subjects": {}}
            assert task == "repair" and request["repair_mode"] == "scoped_append"
            assert request["accepted_facts"] == [baseline]
            joint = request["meaning_entities"][-1]
            assert joint["label"] == "Compression and release"
            return {"new_fact": {"id": "joint_output", "kind": "produces",
                                 "from": joint["id"], "to": "pulse", "evidence_ids": ["joint"]}}
    fixture = JointFixture()
    with pytest.raises(ScoreError, match="missing_relation"):
        _plan_meaning(fixture, {}, evidence, 0)
    fixture = JointFixture()
    graph = _plan_meaning(fixture, {}, evidence, 1)
    assert graph["facts"][1]["from"].startswith("source_joint_")
    assert fixture.calls == ["plan_meaning_entities", "plan_meaning_relations", "repair"]


@pytest.mark.parametrize("reply_id", ["review_fact_0", "causes_2"])
def test_review_ids_are_neutral_and_vetoes_map_back_without_mutating_the_graph(reply_id):
    evidence = [{"id": "output", "claim": "A generator produces electricity."}]
    graph = {"entities": [
        {"id": "generator", "kind": "device", "label": "Generator", "evidence_ids": ["output"]},
        {"id": "electricity", "kind": "energy", "label": "Electricity", "evidence_ids": ["output"]}],
        "facts": [{"id": "causes_2", "kind": "produces", "from": "generator", "to": "electricity",
                   "evidence_ids": ["output"]}], "quantities": []}
    original = deepcopy(graph)
    issue = {"claim_id": "output", "fact_id": "causes_2", "category": "unsupported_relation",
             "evidence_quote": evidence[0]["claim"], "explanation": "A source reviewer veto."}
    schema = _schema({"verdict": {"enum": ["accept", "revise"]},
                      "issues": {"type": "array", "maxItems": 1, "items": _schema({
                          key: {"const": value} for key, value in issue.items()})}})
    class Reviewer:
        def complete(self, task, request):
            assert task == "review_meaning"
            assert request["meaning_graph"]["facts"] == [
                {**original["facts"][0], "id": "review_fact_0"}]
            assert request["evidence"] == evidence
            properties = request["response_schema"]["properties"]["issues"]["items"]["properties"]
            assert properties["fact_id"] == {"const": "review_fact_0"}
            return {"verdict": "revise", "issues": [{**issue, "fact_id": reply_id}]}
    if reply_id == "causes_2":
        with pytest.raises(ProviderError, match="malformed"):
            _review_meaning_graph(Reviewer(), {"evidence": evidence}, graph, schema)
    else:
        assert _review_meaning_graph(Reviewer(), {"evidence": evidence}, graph, schema)["issues"] == [issue]
    assert graph == original and schema["properties"]["issues"]["items"]["properties"]["fact_id"] == {
        "const": "causes_2"}
