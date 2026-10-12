"""Independent-topic TEST fixtures. None are runtime/live authoring fallbacks."""
from copy import deepcopy
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from explainer_direction.authoring import (
    CreativeAuthorityWarning, FAMILY_DIRECTIONS, LocalOpenAIProvider, ProviderError,
    SYSTEM_PROMPT, adapt_asset, author_score, authority_gaps, bind_alignment,
    contrast_ratio, structural_signature,
)
from explainer_direction.contracts import ALIGNMENT_SCHEMA, ScoreError, validate_score


TOPICS = [
    ("fungal transport", "Resource movement connects fungal branches.", "A second branch carries the signal.", "ms", "time", 12, 18),
    ("radio resonance", "The circuit responds to the supplied frequency.", "The tuning changes the response.", "Hz", "frequency", 20, 30),
    ("mediation scheduling", "The initial session occupies the declared interval.", "The follow-up occupies the declared interval.", "min", "time", 4, 8),
]


def source(ident="study"):
    return {"id": ident, "uri": "urn:test-only:" + ident, "locator": "Unit test evidence declaration, not production proof",
            "license": "owned", "commercial_use": True}


def evidence_for(topic=0):
    _, first, second, unit, dimension, left, right = TOPICS[topic]
    return [{"id": "baseline", "claim": first, "status": "supported", "source": source(),
             "quantity": {"value": left, "unit": unit, "dimension": dimension},
             "comparison": {"group": "observations", "conditions": {"basis": "declared test measurement", "window": "same"}}},
            {"id": "updated", "claim": second, "status": "supported", "source": source(),
             "quantity": {"value": right, "unit": unit, "dimension": dimension},
             "comparison": {"group": "observations", "conditions": {"basis": "declared test measurement", "window": "same"}}}]


def style(family="ocean", revision=0):
    return {"family": family, "palette": {
        "background": "#081828" if not revision else "#160A20", "surface": "#16364A" if not revision else "#251431",
        "text": "#F1F8FC", "muted": "#A2B7C7", "primary": "#54D6E5" if not revision else "#F39CD9",
        "secondary": "#6FA9F6", "accent": "#FFCC74", "positive": "#89E7B3", "negative": "#FFA2A2"},
        "typography": {"font_family": "Inter", "font_url": "/engine_sources/editorial-motion-v2/assets/fonts/InterVariable.woff2",
                       "font_license": "OFL-1.1", "headline_size": 64, "body_size": 36, "label_size": 28},
        "strokes": {"width": 3, "corner_radius": 0}, "materials": {"surface": "flat"},
        "motion": {"character": "precise", "easing": "ease_in_out"}}


def actor(ident, kind, payload, initial, evidence_ids=None, role="primary", anchor="primary", **extra):
    return {"id": ident, "kind": kind, "role": role, "label": "Semantic " + ident, "meaning": "An addressable explanation element",
            "evidence_ids": evidence_ids if evidence_ids is not None else ["baseline", "updated"], "layout": {"anchor": anchor},
            "payload": payload, "initial": {"opacity": 1, "position": "home", **initial}, **extra}


def event(ident, verb, changes, cue=None, duration=400, dependencies=None, **extra):
    return {"id": ident, "verb": verb, "targets": list(changes), "cue": cue or {"kind": "fraction", "fraction": .25, "provisional": True},
            "duration_ms": duration, "dependencies": dependencies or [], "easing": "ease_in_out", "changes": changes,
            "claim_ids": ["baseline", "updated"], "rationale": "Make the explanation's relationship visible", **extra}


def creative(request, strategy="mechanism"):
    quantity0, quantity1 = [e["quantity"] for e in request["evidence"]]
    left, right = quantity0["value"], quantity1["value"]
    unit, dimension = quantity0["unit"], quantity0["dimension"]
    scenes = []
    for n in (0, 1):
        sid = "scene_" + str(n)
        suffix = "_" + str(n)
        if strategy == "mechanism":
            a, b, link, caption = [v + suffix for v in ("origin", "destination", "connection", "caption")]
            actors = [actor(a, "shape", {"shape": "circle"}, {"variant": "circle", "draw": 0}, anchor="start"),
                      actor(b, "shape", {"shape": "hexagon"}, {"variant": "hexagon", "draw": 0}, role="secondary", anchor="end"),
                      actor(link, "connector", {"from": a, "to": b, "arrow": True}, {"draw": 0}, role="accent", anchor="center"),
                      actor(caption, "text", {"text": request["evidence"][n]["claim"], "purpose": "annotation"},
                            {"text": request["evidence"][n]["claim"]}, evidence_ids=[request["evidence"][n]["id"]], role="text", anchor="caption")]
            first = event("trace" + suffix, "draw", {a: {"draw": 1}, b: {"draw": 1}, link: {"draw": 1}},
                          {"kind": "word", "word": "move", "occurrence": 0, "edge": "start"})
            hold = event("hold" + suffix, "hold", {}, {"kind": "word", "word": "network", "occurrence": 0, "edge": "end", "offset_ms": 20}, 500, [first["id"]])
            narration = "Signals move through the network."
            relations = [{"id": "flow" + suffix, "kind": "flows_to", "from": a, "to": b, "evidence_ids": ["baseline", "updated"]}]
            events, composition = [first, hold], {"flow": "radial", "density": "balanced", "focus": b}
        else:
            readout, meter, selector, axis = [v + suffix for v in ("readout", "meter", "selector", "axis")]
            actors = [actor(readout, "number", {"unit": unit, "dimension": dimension}, {"value": left}, value_binding="baseline"),
                      actor(meter, "bar", {"unit": unit, "dimension": dimension, "domain": [0, right * 2]}, {"value": left, "fill": .2}, value_binding="baseline", role="secondary"),
                      actor(selector, "selector", {"options": ["Baseline", "Updated"]}, {"selection": 0, "highlight": 0}, role="accent", anchor="context"),
                      actor(axis, "axis", {"domain": [0, right * 2], "unit": unit, "dimension": dimension}, {"draw": 1}, role="muted", anchor="secondary")]
            changes = {readout: {"value": right}, meter: {"value": right, "fill": .8}, selector: {"selection": 1, "highlight": 1}}
            first = event("advance" + suffix, "update", changes, value_bindings={readout: "updated", meter: "updated"})
            events = [first, event("hold" + suffix, "hold", {}, {"kind": "fraction", "fraction": .7, "provisional": True}, 500, [first["id"]])]
            narration = "The readout advances with the selection."
            relations = [{"id": "linked" + suffix, "kind": "connected_to", "from": readout, "to": meter, "evidence_ids": ["baseline", "updated"]}]
            composition = {"flow": "plot", "density": "dense", "focus": meter}
        scenes.append({"id": sid, "section_id": "explanation", "intent": "Make the relationship and its progression clear",
                       "claim_ids": ["baseline", "updated"], "narration": narration, "duration_ms": 4000, "actors": actors,
                       "relations": relations, "events": events, "transition": {"kind": "fade", "duration_ms": 200}, "composition": composition})
    return {"film_id": request.get("film_id", "test_film"), "title": request["brief"], "style": style(request["family"], request["context"].get("palette_revision", 0)),
            "sections": [{"id": "explanation", "title": "Explanation", "intent": "Explain the declared evidence"}], "scenes": scenes}


class MockProvider:
    is_test_fixture = True
    identity = {"provider": "test-only-explicit", "model": "mock-structured-direction"}

    def __init__(self, mutate=None):
        self.calls, self.mutate, self.last_request_id = [], mutate, None

    def complete(self, task, request):
        self.calls.append((task, deepcopy(request)))
        self.last_request_id = "test_request_" + str(len(self.calls))
        actual = request.get("original_task", task) if task == "repair" else task
        if actual == "plan_strategies":
            result = {"strategies": [
                {"id": "mechanism", "thesis": "Follow a connection", "rationale": "Relationship precedes measurement",
                 "representation": ["shape", "connector", "text"], "relation_pattern": ["flows_to"], "progression": ["draw", "hold"], "composition": "radial"},
                {"id": "measurement", "thesis": "Observe a coordinated readout", "rationale": "The measured change drives inference",
                 "representation": ["number", "bar", "axis", "selector"], "relation_pattern": ["connected_to"], "progression": ["update", "hold"], "composition": "plot"},
            ]}
        elif actual in ("author_score", "plan_score", "author_scene"):
            result = creative(request, request["strategy"]["id"])
            if actual == "plan_score":
                result["scene_briefs"] = [{k: s[k] for k in ("id", "section_id", "intent", "claim_ids", "duration_ms")} for s in result.pop("scenes")]
            elif actual == "author_scene":
                result = next(s for s in result["scenes"] if s["id"] == request["scene_brief"]["id"])
                result.pop("events")
        elif actual == "author_choreography":
            ids = {a["id"] for a in request["scene_structure"]["actors"]}
            candidates = [
                scene for strategy in ("mechanism", "measurement")
                for scene in creative(request, strategy)["scenes"]
                if scene["id"] == request["scene_brief"]["id"]
            ]
            events = next(scene["events"] for scene in candidates if {a["id"] for a in scene["actors"]} == ids)
            renamed = {event["id"]: request["event_id_prefix"] + event["id"] for event in events}
            for event in events:
                event["id"] = renamed[event["id"]]
                event["dependencies"] = [renamed[dependency] for dependency in event["dependencies"]]
                event.pop("targets")
            result = {"events": events}
        elif actual in ("select_candidate", "select_strategy"):
            result = {"selected_id": "mechanism", "rationale": "Trace causally related actors before exposing detailed measurements",
                      "distinct": True, "authority": "DEVELOPMENT_PREFLIGHT", "findings": [
                          {"strategy_id": "mechanism", "strength": "Trace shows the connection", "risk": "Metaphor remains illustrative"},
                          {"strategy_id": "measurement", "strength": "Linked evidence values", "risk": "Denser narration needs native review"}]}
        else:
            raise AssertionError(actual)
        return self.mutate(task, request, result) if self.mutate else result


def authored(topic=0, provider=None, **options):
    with pytest.warns(CreativeAuthorityWarning, match="DEVELOPMENT_PREFLIGHT"):
        return author_score(TOPICS[topic][0], evidence_for(topic), provider=provider or MockProvider(), test_fixture=True, **options)


@pytest.mark.parametrize("topic", range(3))
@pytest.mark.parametrize("staged", [False, True])
def test_unrelated_topics_joint_authoring_and_real_competition(topic, staged):
    provider = MockProvider()
    evidence = evidence_for(topic)
    original = deepcopy(evidence)
    score = authored(topic, provider, staged=staged, film_id="independent_topic")
    assert validate_score(score) == score
    assert score["evidence"] == evidence == original
    assert score["film_id"] == "independent_topic"
    assert len(score["sections"]) == 1 and len(score["scenes"]) == 2
    assert all(len(s["actors"]) == 4 for s in score["scenes"])
    review = next(r for t, r in provider.calls if t == "select_candidate")
    first, second = [c["score"] for c in review["candidates"]]
    assert structural_signature(first) != structural_signature(second)
    assert second["scenes"][0]["events"][0]["targets"] == ["readout_0", "meter_0", "selector_0"]
    assert score["provenance"]["model"]["model"] == provider.identity["model"]
    assert score["provenance"]["model"]["request_id"] != provider.last_request_id  # author call, NOT selection
    assert score["provenance"]["status"] == "DEVELOPMENT_PREFLIGHT" and "p8" not in score["provenance"]
    assert score["provenance"]["test_fixture"] is True
    score["evidence"][0]["claim"] = "changed"
    assert evidence == original
    if staged:
        assert sum(t == "author_scene" for t, _ in provider.calls) == 4
        assert all("narration" not in b for t, r in provider.calls if t == "plan_score" for b in r.get("scene_briefs", []))


@pytest.mark.parametrize("family", list(FAMILY_DIRECTIONS))
def test_five_contextual_families_coherent_roles_and_brand(family):
    provider = MockProvider()
    score = authored(provider=provider, family=family, context={"palette_revision": 1, "brand": {"palette": {"accent": "#FFF0AA"}}})
    second = authored(family=family)
    assert score["style"]["family"] == family
    assert score["style"]["palette"]["accent"] == "#FFF0AA"
    assert score["style"]["palette"]["primary"] != second["style"]["palette"]["primary"]
    assert structural_signature(score) == structural_signature(second)  # style independent of choreography
    palette = score["style"]["palette"]
    for ground in ("background", "surface"):
        for role in ("text", "muted", "primary", "secondary", "accent", "positive", "negative"):
            assert contrast_ratio(palette[role], palette[ground]) >= (4.5 if role in ("text", "muted") else 3)
    assert all(a["role"] in palette for s in score["scenes"] for a in s["actors"])
    assert provider.calls[0][1]["family_direction"] == FAMILY_DIRECTIONS[family]


def test_context_sources_memory_and_history_preserved_without_truncation():
    provider = MockProvider()
    context = {"audience": "curious specialists", "corpus": [{"id": "first"}, {"id": "middle"}, {"id": "last"}]}
    history = [{"motif": "intentional long hold", "signature": "prior"}]
    memory = {"Account": {"voice": "clear"}, "Brand": {"identity": "immutable"}, "Series": {"motif": "network"}}
    authored(provider=provider, context=context, history=history, memory=memory, sources=[source("corpus")])
    for _, request in provider.calls:
        assert request["context"] == context and request["history"] == history and request["memory"] == memory
        assert request["sources"] == [source("corpus")]
    assert len(context["corpus"]) == 3


def test_bounded_surgical_validation_repair_does_not_reopen_competition():
    def mutate(task, request, result):
        if task == "author_score" and request["strategy"]["id"] == "mechanism":
            result["scenes"][0]["events"][0]["verb"] = "unsupported_trace"
        return result
    provider = MockProvider(mutate)
    authored(provider=provider, max_repairs=1)
    assert [t for t, _ in provider.calls].count("plan_strategies") == 1
    repair = next(r for t, r in provider.calls if t == "repair")
    assert repair["original_task"] == "author_score"
    assert repair["previous_response"]["scenes"][0]["events"][0]["verb"] == "unsupported_trace"
    assert repair["validation_error"]["path"].startswith("$.scenes")
    assert "exact anchor" in repair["repair_policy"]
    assert repair["evidence"] == evidence_for()


@pytest.mark.parametrize("failure", ["kind", "claim", "number", "authority", "contrast", "word", "dependency"])
def test_fail_closed_after_bounded_repairs(failure):
    def mutate(task, request, result):
        actual = request.get("original_task", task)
        if actual != "author_score":
            return result
        s = result["scenes"][0]
        if failure == "kind":
            s["actors"][0]["kind"] = "humanoid"
        elif failure == "claim":
            s["claim_ids"].append("invented")
        elif failure == "number":
            s["narration"] = "The interval is 999 ms."
        elif failure == "authority":
            result["provenance"] = {"status": "CREATIVE_LOCKED"}
        elif failure == "contrast":
            result["style"]["palette"]["text"] = result["style"]["palette"]["background"]
        elif failure == "word":
            s["events"][0]["cue"]["word"] = "missing"
        else:
            s["events"][0]["dependencies"] = ["unknown"]
        return result
    provider = MockProvider(mutate)
    with pytest.raises(ScoreError, match="exhausted 1 structural repairs"):
        author_score("mechanism", evidence_for(), provider=provider, test_fixture=True, max_repairs=1)
    assert len(provider.calls) == 3  # strategies, candidate, one repair
    assert not any(t == "select_candidate" for t, _ in provider.calls)


def test_no_fixtures_in_live_and_no_default_inference(monkeypatch):
    with pytest.raises(ProviderError, match="test fixtures"):
        author_score("live brief", evidence_for(), provider=MockProvider())
    monkeypatch.delenv("EXPLAINER_DIRECTION_BASE_URL", raising=False)
    monkeypatch.delenv("EXPLAINER_DIRECTION_MODEL", raising=False)
    with pytest.raises(ProviderError, match="explicit local"):
        author_score("live brief", evidence_for())
    class Broken:
        identity = {"provider": "declared", "model": "actual"}
        def complete(self, task, request):
            raise ProviderError("provider unavailable")
    with pytest.raises(ProviderError, match="unavailable"):
        author_score("live brief", evidence_for(), provider=Broken())


def test_no_evidence_mutation_via_provider_request():
    class Mutating(MockProvider):
        def complete(self, task, request):
            result = super().complete(task, request)
            request["evidence"][0]["quantity"]["value"] = 12345
            request["authority"]["status"] = "CREATIVE_LOCKED"
            return result
    score = authored(provider=Mutating())
    assert score["evidence"][0]["quantity"]["value"] == 12
    assert score["provenance"]["status"] == "DEVELOPMENT_PREFLIGHT"


def test_palette_swaps_do_not_make_strategy_or_candidate_competition():
    def repeat_candidates(task, request, result):
        if task == "author_score" or request.get("original_task") == "author_score":
            result = creative(request, "mechanism")
            result["title"] = "Different label"
        return result
    with pytest.raises(ScoreError, match="genuine competition"):
        author_score("brief", evidence_for(), provider=MockProvider(repeat_candidates), test_fixture=True, max_repairs=0)
    def repeat_strategies(task, request, result):
        if task == "plan_strategies":
            result["strategies"][1] = {**result["strategies"][0], "id": "different", "thesis": "Other words"}
        return result
    with pytest.raises(ScoreError, match="distinct semantic"):
        author_score("brief", evidence_for(), provider=MockProvider(repeat_strategies), test_fixture=True, max_repairs=0)

def test_concept_competition_cannot_offer_unexecutable_numeric_or_asset_alternatives():
    evidence = [{"id": "objects", "claim": "The system has two connected objects.",
                 "status": "supported", "source": source(),
                 "quantity": {"value": 2, "unit": "count", "dimension": "count"}}]
    provider = MockProvider()
    with pytest.raises(ScoreError, match="unsupported/empty strategy representation"):
        author_score("brief", evidence, provider=provider, test_fixture=True, max_repairs=0)
    kinds = provider.calls[0][1]["response_schema"]["properties"]["strategies"]["items"]["properties"]["representation"]["items"]["enum"]
    assert "number" in kinds
    assert not {"axis", "bar", "image"} & set(kinds)
    supported = MockProvider()
    with pytest.warns(CreativeAuthorityWarning):
        author_score("brief", evidence_for(), provider=supported, test_fixture=True, max_repairs=0)
    kinds = supported.calls[0][1]["response_schema"]["properties"]["strategies"]["items"]["properties"]["representation"]["items"]["enum"]
    assert {"axis", "bar", "number"} <= set(kinds)


def declared_asset():
    return {"id": "diagram", "kind": "image", "payload": {"src": "/local/diagram.png", "mime": "image/png", "fit": "contain", "source": source("artwork")},
            "affordances": ["reveal", "hold"]}


@pytest.mark.parametrize("composition", ["row", "column", "plot"])
def test_primitive_order_and_layout_swaps_do_not_make_a_new_strategy(composition):
    def permute(task, request, result):
        if task == "plan_strategies":
            other = deepcopy(result["strategies"][0])
            other.update(id="reordered", thesis="New words", composition=composition)
            other["representation"].reverse()
            other["relation_pattern"].reverse()
            result["strategies"][1] = other
        return result
    with pytest.raises(ScoreError, match="distinct semantic"):
        author_score("brief", evidence_for(), provider=MockProvider(permute), test_fixture=True, max_repairs=0)


def test_concept_first_competes_before_authoring_only_the_selected_score():
    provider = MockProvider()
    with pytest.warns(CreativeAuthorityWarning):
        score = author_score("brief", evidence_for(), provider=provider, test_fixture=True, concept_first=True)
    assert [task for task, _ in provider.calls] == ["plan_strategies", "select_strategy", "author_score"]
    assert score["provenance"]["test_fixture"] is True
    request = provider.calls[-1][1]
    assert request["strategy"]["id"] == request["concept_selection"]["selected_id"]
    assert len(request["concept_selection"]["findings"]) == 2


@pytest.mark.parametrize("change", [
    {"selected_id": []}, {"selected_id": "missing"}, {"findings": []},
    {"distinct": False}, {"authority": "CREATIVE_LOCKED"},
])
def test_concept_first_does_not_skip_selection_validation(change):
    def invalid(task, request, result):
        if task == "select_strategy":
            result.update(change)
        return result
    with pytest.raises(ScoreError):
        author_score("brief", evidence_for(), provider=MockProvider(invalid),
                     test_fixture=True, concept_first=True, max_repairs=0)


@pytest.mark.parametrize("value", [None, 1, "yes"])
def test_concept_first_requires_boolean(value):
    with pytest.raises(ScoreError, match="boolean"):
        author_score("brief", evidence_for(), provider=MockProvider(), concept_first=value)


def test_asset_adapter_preserves_licensing_affordances_and_local_payload():
    original = declared_asset()
    adapted = adapt_asset(original, lambda a: {**a, "payload": {**a["payload"], "src": "/resolved/diagram.png"}})
    assert adapted["payload"]["source"] == original["payload"]["source"]
    assert adapted["affordances"] == original["affordances"]
    for change in ({"affordances": ["update"]}, {"payload": {**original["payload"], "source": source("other")}}, {"payload": {**original["payload"], "src": "https://remote/art.png"}}):
        with pytest.raises(ScoreError):
            adapt_asset(original, lambda a: {**a, **change})
    assert original == declared_asset()


def test_undeclared_asset_and_exceeded_affordance_rejected():
    asset = declared_asset()
    def add_image(task, request, result):
        if task == "author_score":
            result["scenes"][0]["actors"].append(actor("art", "image", asset["payload"], {"reveal": 0}, evidence_ids=[]))
            result["scenes"][0]["events"].append(event("image_reveal", "reveal", {"art": {"reveal": 1}}, {"kind": "absolute", "ms": 0, "basis": "authored"}, 100))
        return result
    with pytest.raises(ScoreError, match="absent from declared"):
        author_score("brief", evidence_for(), provider=MockProvider(add_image), test_fixture=True, max_repairs=0)
    score = authored(provider=MockProvider(add_image), library=[asset])
    assert score["scenes"][0]["actors"][-1]["kind"] == "image"
    asset["affordances"] = ["hold"]
    with pytest.raises(ScoreError, match="exceeds asset affordances"):
        author_score("brief", evidence_for(), provider=MockProvider(add_image), test_fixture=True, library=[asset], max_repairs=0)


def alignment_for(score, duration=3000):
    # Explicit uneven reported intervals are TEST DATA, not evidence of TTS.
    words = [("Signals", 30, 100), ("move", 170, 420), ("through", 480, 540), ("the", 580, 610), ("network.", 760, 1100)]
    return {"schema": ALIGNMENT_SCHEMA, "id": "reported_test_alignment",
            "source": {"provider": "test-only-timestamp-input", "method": "provider_word_timestamps", "audio_sha256": "a" * 64},
            "scenes": [{"scene_id": s["id"], "duration_ms": duration,
                        "words": [{"word": w, "start_ms": start, "end_ms": end} for w, start, end in words]} for s in score["scenes"]]}


def test_bind_real_reported_word_edges_not_uniform_spacing():
    score = authored()
    original, alignment = deepcopy(score), alignment_for(score)
    bound = bind_alignment(score, alignment)
    assert score == original
    for scene in bound["scenes"]:
        assert scene["duration_ms"] == 3000 and scene["timing"] == "aligned"
        assert scene["events"][0]["cue"]["resolved_ms"] == 170
        assert scene["events"][1]["cue"]["resolved_ms"] == 1120
        assert all(e["cue"]["alignment_id"] == alignment["id"] for e in scene["events"])
    assert validate_score(bound) == bound


def test_fraction_stays_provisional_even_with_real_alignment():
    score = authored()
    for scene in score["scenes"]:
        scene["events"][0]["cue"] = {"kind": "fraction", "fraction": .2, "provisional": True}
    bound = bind_alignment(score, alignment_for(score))
    assert all(s["timing"] == "provisional" for s in bound["scenes"])
    assert all(s["events"][0]["cue"] == {"kind": "fraction", "fraction": .2, "provisional": True} for s in bound["scenes"])


@pytest.mark.parametrize("fault", ["tokens", "overlap", "missing", "overflow", "fake_method"])
def test_bad_reported_alignment_fails_without_fabrication(fault):
    score, aligned = authored(), None
    aligned = alignment_for(score)
    if fault == "tokens":
        aligned["scenes"][0]["words"][0]["word"] = "Invented"
    elif fault == "overlap":
        aligned["scenes"][0]["words"][1]["start_ms"] = 50
    elif fault == "missing":
        aligned["scenes"].pop()
    elif fault == "overflow":
        aligned["scenes"][0]["duration_ms"] = 1200
    else:
        aligned["source"]["method"] = "uniform_word_spacing"
    with pytest.raises(ScoreError):
        bind_alignment(score, aligned)
    assert "alignment" not in score


def test_p8_binding_needs_external_authentication_and_cannot_restyle():
    score = authored()
    del score["provenance"]["test_fixture"]
    score["provenance"].update(mode="p8_bound", status="P8_SEMANTIC_BOUND", p8={"state_hash": "1" * 64, "board_hash": "2" * 64})
    args = (score["brief"], score["evidence"])
    with pytest.raises(ScoreError, match="external authority authentication"):
        author_score(*args, p8_direction=score)
    bound = author_score(*args, p8_direction=score, authority_verifier=lambda s: s["provenance"]["p8"]["state_hash"] == "1" * 64)
    assert bound == score and bound is not score
    assert all("Missing authenticated" not in gap for gap in authority_gaps(bound))
    assert any("No Creative Lock" in gap for gap in authority_gaps(bound))
    with pytest.raises(ScoreError, match="cannot be restyled"):
        author_score(*args, p8_direction=score, authority_verifier=lambda _: True, brand={"palette": {"accent": "#FFF0AA"}})


@contextmanager
def http_server(responder):
    received = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            received.append((self.path, dict(self.headers), payload))
            status, body, headers = responder(payload)
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body.encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port) + "/v1", received
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def envelope(content='{"ok":true}', model="exact-local-model", **extra):
    return json.dumps({"id": "actual-server-request", "model": model,
                       "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": content}}], **extra})


def test_local_http_exact_model_json_format_optional_key_and_no_proxy(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://unavailable.invalid:1")
    monkeypatch.delenv("EXPLAINER_DIRECTION_API_KEY", raising=False)
    with http_server(lambda _: (200, envelope(), {})) as (url, received):
        provider = LocalOpenAIProvider(url, "exact-local-model")
        assert provider.complete("structured_task", {"input": "real JSON"}) == {"ok": True}
        path, headers, payload = received[0]
        assert path == "/v1/chat/completions" and "Authorization" not in headers
        assert payload["model"] == "exact-local-model" and payload["response_format"] == {"type": "json_object"}
        assert payload["messages"][0]["content"] == SYSTEM_PROMPT
        assert json.loads(payload["messages"][1]["content"]) == {"task": "structured_task", "request": {"input": "real JSON"}}
        assert provider.last_request_id == "actual-server-request"


def test_transport_scopes_schema_without_dropping_creative_inputs():
    request = {
        "brief": "An unchanged real brief", "evidence": [{"id": "source"}],
        "context": {"audience": "general"}, "history": [{"motif": "previous"}],
        "score_schema": {"redundant": "whole contract"},
        "response_schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
    }
    original = deepcopy(request)
    with http_server(lambda _: (200, envelope(), {})) as (url, received):
        LocalOpenAIProvider(url, "exact-local-model").complete("plan_strategies", request)
        sent = json.loads(received[0][2]["messages"][1]["content"])
        assert received[0][2]["response_format"] == {
            "type": "json_schema", "json_schema": {
                "name": "explainer_direction", "schema": original["response_schema"], "strict": True,
            },
        }
        assert sent["task"] == "plan_strategies"
        assert "score_schema" not in sent["request"]
        assert list(sent["request"])[0] == "response_schema"
        for key in ("brief", "evidence", "context", "history", "response_schema"):
            assert sent["request"][key] == original[key]
        assert request == original


def test_scene_schema_reaches_repair_sampling_without_a_silent_json_only_retry():
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}
    with http_server(lambda _: (400, '{"error":"schema unsupported"}', {})) as (url, received):
        with pytest.raises(ProviderError):
            LocalOpenAIProvider(url, "exact-local-model").complete("repair", {
                "original_task": "author_scene", "response_schema": schema, "validation_error": {"message": "bad field"},
            })
        assert len(received) == 1
        assert received[0][2]["response_format"]["json_schema"]["schema"] == schema


def test_scoped_palette_repair_chooses_feasible_swatches_without_rewriting_the_film():
    from explainer_direction.authoring import _bounded, _palette_patch

    anchor = {
        "style": {"palette": {"background": "#0a192f", "surface": "#0f2a4c", "secondary": "#0077b6"}},
        "sections": [{"intent": "This creative decision must remain unchanged."}],
    }
    request = {"context": {"brand": {}}, "response_schema": {"type": "object"}}
    role, schema = _palette_patch(request, anchor, "$.style.palette.secondary")
    assert role == "secondary"
    for candidate in schema["properties"]["replacement"]["enum"]:
        assert all(contrast_ratio(candidate, anchor["style"]["palette"][ground]) >= 3 for ground in ("background", "surface"))

    class Provider:
        supports_schema_patch = True

        def complete(self, task, submitted):
            if task == "plan_score":
                return deepcopy(anchor)
            assert task == "repair" and submitted["repair_mode"] == "scoped_patch"
            assert submitted["repair_anchor"] == anchor
            return {"replacement": submitted["response_schema"]["properties"]["replacement"]["enum"][0]}

    def validate(value):
        palette = value["style"]["palette"]
        if any(contrast_ratio(palette["secondary"], palette[ground]) < 3 for ground in ("background", "surface")):
            raise ScoreError("secondary requires 3:1 on both grounds", "$.style.palette.secondary")
        return value

    result = _bounded(Provider(), "plan_score", request, validate, 1)
    expected = deepcopy(anchor)
    expected["style"]["palette"]["secondary"] = schema["properties"]["replacement"]["enum"][0]
    assert result == expected
    assert anchor["style"]["palette"]["secondary"] == "#0077b6"
    assert _palette_patch({"context": {"brand": {"palette": {"secondary": "#0077b6"}}}}, anchor, "$.style.palette.secondary") is None


@pytest.mark.parametrize("roles", [("negative",), ("negative", "muted")])
def test_live_palette_repair_keeps_nearest_valid_colors_without_another_model_call(roles):
    from explainer_direction.authoring import _bounded, _palette_patch

    anchor = {
        "style": {"palette": {
            "background": "#0a1a3a", "surface": "#002b5b",
            **{role: "#cc3333" for role in roles},
        }},
        "sections": [{"intent": "Keep the accepted concept."}],
    }
    request = {"context": {}, "response_schema": {"type": "object"}}
    candidates = {
        role: _palette_patch(request, anchor, "$.style.palette." + role)[1]["properties"]["replacement"]["enum"]
        for role in roles
    }

    class Provider:
        supports_schema_patch = True
        supports_deterministic_palette_repair = True

        def complete(self, task, submitted):
            assert task == "plan_score"
            return deepcopy(anchor)

    def validate(value):
        for role in roles:
            minimum = 4.5 if role == "muted" else 3
            if any(contrast_ratio(value["style"]["palette"][role], value["style"]["palette"][ground]) < minimum
                   for ground in ("background", "surface")):
                raise ScoreError("requires contrast on both grounds", "$.style.palette." + role)
        return value

    result = _bounded(Provider(), "plan_score", request, validate, len(roles))
    for role in roles:
        expected = min(
            candidates[role],
            key=lambda tint: sum(
                (int(tint[i:i + 2], 16) - int("#cc3333"[i:i + 2], 16)) ** 2
                for i in (1, 3, 5)
            ),
        )
        assert result["style"]["palette"][role] == expected
        assert anchor["style"]["palette"][role] == "#cc3333"
        assert all(contrast_ratio(expected, result["style"]["palette"][ground]) >= (4.5 if role == "muted" else 3)
                   for ground in ("background", "surface"))
    assert result["sections"] == anchor["sections"]


def test_scoped_palette_repair_never_accepts_a_value_outside_the_feasible_schema():
    from explainer_direction.authoring import _bounded

    class Provider:
        supports_schema_patch = True

        def complete(self, task, submitted):
            return {"replacement": "#0077b6"}

    def validate(value):
        raise ScoreError("contrast requires repair", "$.style.palette.secondary")

    with pytest.raises(ProviderError, match="response schema"):
        _bounded(Provider(), "plan_score", {"context": {}}, validate, 1, initial_response={
            "style": {"palette": {"background": "#0a192f", "surface": "#0f2a4c", "secondary": "#0077b6"}},
        })


def test_local_transport_limits_are_explicit_and_validated(monkeypatch):
    monkeypatch.setenv("EXPLAINER_DIRECTION_TIMEOUT_SECONDS", "600")
    monkeypatch.setenv("EXPLAINER_DIRECTION_MAX_TOKENS", "8000")
    provider = LocalOpenAIProvider("http://localhost:8788", "declared-local-model")
    assert (provider.timeout, provider.max_tokens) == (600, 8000)
    monkeypatch.setenv("EXPLAINER_DIRECTION_MAX_TOKENS", "not an integer")
    with pytest.raises(ProviderError):
        LocalOpenAIProvider("http://localhost:8788", "declared-local-model")
    monkeypatch.setenv("EXPLAINER_DIRECTION_MAX_TOKENS", "8000")
    monkeypatch.setenv("EXPLAINER_DIRECTION_TIMEOUT_SECONDS", "inf")
    with pytest.raises(ProviderError):
        LocalOpenAIProvider("http://localhost:8788", "declared-local-model")


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf"), 3601, "120"])
def test_local_transport_rejects_unbounded_or_invalid_timeout(timeout):
    with pytest.raises(ProviderError, match="timeout"):
        LocalOpenAIProvider("http://localhost:8788", "declared-local-model", timeout=timeout)


def test_local_transport_admits_explicit_slow_cpu_timeout():
    provider = LocalOpenAIProvider("http://localhost:8788", "declared-local-model", timeout=1800)
    assert provider.timeout == 1800


@pytest.mark.parametrize("response", [envelope(model="wrong-model"), envelope(content="not JSON"), envelope(content='{"a":1,"a":2}'),
                                    envelope(content='{"a":NaN}'), envelope(content="[]"),
                                    envelope(choices=[{"finish_reason": "length", "message": {"content": "{}"}}])])
def test_local_http_rejects_identity_truncation_and_non_json(response):
    with http_server(lambda _: (200, response, {})) as (url, received):
        provider = LocalOpenAIProvider(url, "exact-local-model")
        with pytest.raises(ProviderError):
            provider.complete("task", {})
        assert len(received) == 1 and provider.last_request_id is None


def test_local_http_rejects_redirects_without_following_or_retries():
    with http_server(lambda _: (307, "", {"Location": "https://remote.invalid/v1/chat/completions"})) as (url, received):
        with pytest.raises(ProviderError, match="redirects"):
            LocalOpenAIProvider(url, "exact-local-model").complete("task", {})
        assert len(received) == 1


@pytest.mark.parametrize("url", ["https://remote.example/v1", "http://192.168.1.1:8000/v1", "file:///tmp/model", "http://localhost:80/v1?key=x", "http://user:pass@localhost/v1", "http://localhost/other"])
def test_no_remote_default_or_unsafe_provider_urls(url):
    with pytest.raises(ProviderError):
        LocalOpenAIProvider(url, "exact-local-model")


@pytest.mark.parametrize("option", [{"candidate_count": 1}, {"max_repairs": 9}, {"max_repairs": True}, {"staged": "yes"}, {"brand": {"palette": {"unknown": "#FFFFFF"}}},
                                    {"unknown": True}, {"provider_identity": {"provider": "test-only-explicit", "model": "fabricated-identity"}}])
def test_invalid_inputs_fail_closed(option):
    with pytest.raises((ScoreError, ProviderError)):
        author_score("brief", evidence_for(), provider=MockProvider(), test_fixture=True, **option)


def test_larger_repair_budget_is_explicit_and_still_bounded():
    assert validate_score(authored(max_repairs=8))


def test_impossible_brand_contrast_is_not_silently_corrected():
    with pytest.raises(ScoreError, match="contrast"):
        author_score("brief", evidence_for(), provider=MockProvider(), test_fixture=True, max_repairs=0,
                     brand={"palette": {"text": "#081828", "background": "#081828"}})


def test_repair_cannot_rewrite_unaffected_creative_decisions():
    def mutate(task, request, result):
        if task == "author_score":
            result["scenes"][0]["events"][0]["verb"] = "unsupported"
        elif task == "repair":
            result["title"] = "Unrequested new story"
        return result
    provider = MockProvider(mutate)
    with pytest.raises(ScoreError, match="unaffected decisions"):
        author_score("brief", evidence_for(), provider=provider, test_fixture=True, max_repairs=1)
    assert provider.calls[-1][1]["repair_anchor"]["title"] == "brief"
    assert provider.calls[-1][1]["repair_scope"].startswith("$.scenes[0]")


def test_signatures_ignore_actor_order_labels_palette_and_ids_but_keep_topology():
    score = authored()
    rearranged = deepcopy(score)
    for scene in rearranged["scenes"]:
        scene["actors"].reverse()
        scene["relations"].reverse()
        for a in scene["actors"]:
            a["label"] = "Different metadata"
    rearranged["title"] = "Changed title"
    rearranged["style"] = style(revision=1)
    assert structural_signature(score) == structural_signature(rearranged)
    changed = deepcopy(score)
    changed["scenes"][0]["relations"][0]["kind"] = "supports"
    assert structural_signature(score) != structural_signature(changed)
    changed = deepcopy(score)
    changed["scenes"][0]["actors"][2]["payload"].update({"from": "destination_0", "to": "origin_0"})
    assert structural_signature(score) != structural_signature(changed)


def test_staged_outline_repairs_invalid_style_before_authoring_scenes():
    def mutate(task, request, result):
        if task == "plan_score":
            result["style"]["typography"]["font_url"] = "https://hosted.invalid/font.woff2"
        return result
    provider = MockProvider(mutate)
    authored(provider=provider, staged=True, max_repairs=1)
    for i, (task, request) in enumerate(provider.calls):
        if task == "repair":
            assert request["original_task"] == "plan_score"
            assert request["repair_scope"] == "$.style.typography.font_url"
            assert provider.calls[i - 1][0] == "plan_score"
            assert provider.calls[i + 1][0] == "author_scene"


def test_repeated_word_occurrence_case_punctuation_edge_and_offset_are_exact():
    score = authored()
    aligned = alignment_for(score)
    for scene, reported in zip(score["scenes"], aligned["scenes"]):
        scene["narration"] = "Move, move through the network."
        scene["events"][0]["cue"] = {"kind": "word", "word": "MOVE", "occurrence": 1, "edge": "end", "offset_ms": 15}
        reported["words"][0]["word"] = "Move,"
    bound = bind_alignment(score, aligned)
    assert all(s["events"][0]["cue"]["resolved_ms"] == 435 for s in bound["scenes"])
    assert all(s["timing"] == "aligned" for s in bound["scenes"])


def test_real_alignment_rechecks_retained_terminal_state_continuity():
    score = authored()
    first, second = score["scenes"]
    original = first["actors"][0]
    original["retain"] = original["id"]
    second["actors"][0] = deepcopy(original)
    second["actors"][0]["initial"]["draw"] = 1
    second["actors"][2]["payload"]["from"] = original["id"]
    second["relations"][0]["from"] = original["id"]
    change = second["events"][0]["changes"].pop("origin_1")
    change["draw"] = 0
    second["events"][0]["changes"][original["id"]] = change
    second["events"][0]["targets"][0] = original["id"]
    bound = bind_alignment(score, alignment_for(score))
    assert bound["scenes"][1]["actors"][0]["initial"]["draw"] == 1
    second["actors"][0]["initial"]["draw"] = 0
    # Word-cue terminal state is unknown before reported audio. Binding must
    # actually rerun continuity checks, not mark an unresolved score aligned.
    assert validate_score(score) == score
    with pytest.raises(ScoreError, match="terminal state"):
        bind_alignment(score, alignment_for(score))


def test_full_local_http_staged_authoring_protocol_is_explicit_test_evidence():
    mock = MockProvider()
    def respond(payload):
        task = json.loads(payload["messages"][1]["content"])
        result = mock.complete(task["task"], task["request"])
        return 200, envelope(content=json.dumps(result), id="http_call_" + str(len(mock.calls))), {}
    class TestHTTPProvider(LocalOpenAIProvider):
        is_test_fixture = True
    with http_server(respond) as (url, received):
        score = authored(provider=TestHTTPProvider(url, "exact-local-model"), staged=True)
        assert len(received) == 12  # planning, two outlines, four construction/motion pairs, selection
        assert score["provenance"]["model"] == {"provider": "openai-compatible-local", "model": "exact-local-model", "request_id": "http_call_6"}
        assert score["provenance"]["test_fixture"] is True
        assert score["provenance"]["status"] == "DEVELOPMENT_PREFLIGHT"


@pytest.mark.parametrize("bad_asset", [{"id": []}, {"id": "bad", "kind": "image", "payload": {}, "affordances": []}])
def test_invalid_library_shape_has_addressable_contract_failure(bad_asset):
    with pytest.raises(ScoreError):
        author_score("brief", evidence_for(), provider=MockProvider(), test_fixture=True, library=[bad_asset])


def test_source_conflicts_and_unlicensed_art_fail_closed():
    conflict = {**source(), "uri": "urn:different-source"}
    with pytest.raises(ScoreError, match="conflicting source"):
        author_score("brief", evidence_for(), provider=MockProvider(), test_fixture=True, sources=[conflict], max_repairs=0)
    asset = declared_asset()
    asset["payload"]["source"]["commercial_use"] = False
    with pytest.raises(ScoreError):
        adapt_asset(asset)


def test_http_environment_routes_and_optional_key(monkeypatch):
    with http_server(lambda _: (200, envelope(), {})) as (url, received):
        monkeypatch.setenv("EXPLAINER_DIRECTION_BASE_URL", url)
        monkeypatch.setenv("EXPLAINER_DIRECTION_MODEL", "exact-local-model")
        monkeypatch.setenv("EXPLAINER_DIRECTION_API_KEY", "explicit-test-key")
        assert LocalOpenAIProvider().complete("task", {}) == {"ok": True}
        assert received[0][1]["Authorization"] == "Bearer explicit-test-key"


def test_staged_scene_repair_resolves_partial_score_paths_without_replanning():
    def mutate(task, request, result):
        if task == "author_choreography":
            result["events"][0]["verb"] = "unsupported"
        return result
    provider = MockProvider(mutate)
    score = authored(provider=provider, staged=True, max_repairs=1)
    assert validate_score(score) == score
    tasks = [task for task, _ in provider.calls]
    assert tasks.count("plan_strategies") == 1
    assert tasks.count("plan_score") == 2
    assert tasks.count("repair") == 4
    for task, request in provider.calls:
        if task == "repair":
            assert request["original_task"] == "author_choreography"
            assert request["repair_scope"].startswith("$.scenes[")
            assert set(request["repair_anchor"]) == {"events"}
            assert "events" not in request["scene_structure"]


@pytest.mark.parametrize("permanent", [False, True])
def test_staged_assembly_competition_repair_keeps_original_task_and_exact_anchor(permanent):
    def mutate(task, request, result):
        if task == "plan_strategies":
            representations = sorted(set().union(*(s["representation"] for s in result["strategies"])))
            for strategy in result["strategies"]:
                strategy["representation"] = representations
        if task == "author_scene" and request["strategy"]["id"] == "measurement":
            result = next(s for s in creative(request, "mechanism")["scenes"] if s["id"] == request["scene_brief"]["id"])
            result.pop("events")
        if permanent and task == "repair" and request.get("original_task") == "author_score":
            result = creative(request, "mechanism")
        return result
    provider = MockProvider(mutate)
    if permanent:
        with pytest.raises(ScoreError, match="exhausted 2 structural repairs"):
            author_score("brief", evidence_for(), provider=provider, test_fixture=True, staged=True, max_repairs=2)
    else:
        assert validate_score(authored(provider=provider, staged=True, max_repairs=2))
    repair_requests = [r for t, r in provider.calls if t == "repair"]
    assert len(repair_requests) == (2 if permanent else 1)
    assert all(r["original_task"] == "author_score" and r["repair_scope"] == "$.scenes" for r in repair_requests)
    assert all(r["repair_anchor"] == repair_requests[0]["repair_anchor"] for r in repair_requests)
    assert [t for t, _ in provider.calls].count("plan_strategies") == 1
    assert [t for t, _ in provider.calls].count("plan_score") == 2


def test_scene_sampling_schema_enforces_kind_and_approved_evidence():
    from explainer_direction.authoring import _scene_response_schema

    jsonschema = pytest.importorskip("jsonschema")
    scene_brief = {"id": "scene_one", "claim_ids": ["supported"], "duration_ms": 5000}
    outline = {"scene_briefs": [scene_brief, {**scene_brief, "id": "scene_two"}]}
    schema = _scene_response_schema(
        scene_brief, outline, {"context": {"target_seconds": 20}, "library": []}
    )
    actor_schema = schema["properties"]["actors"]["items"]
    assert "oneOf" in actor_schema and len(actor_schema["oneOf"]) > 5
    assert not any(
        variant["properties"]["kind"]["const"] == "image"
        for variant in actor_schema["oneOf"]
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    validate = jsonschema.Draft202012Validator(actor_schema).is_valid
    actor = {
        "id": "field", "kind": "panel", "role": "background",
        "label": "Ground", "meaning": "Visual setting",
        "evidence_ids": ["supported"], "layout": {"anchor": "background"},
        "payload": {}, "initial": {"opacity": 1, "position": "home"},
    }
    assert validate(actor)
    bad_state = deepcopy(actor)
    bad_state["initial"]["value"] = 0
    assert not validate(bad_state)
    bad_payload = deepcopy(actor)
    bad_payload["payload"]["custom_svg_path"] = "M0 0"
    assert not validate(bad_payload)
    bad_claim = deepcopy(actor)
    bad_claim["evidence_ids"] = ["not_authorized_for_this_scene"]
    assert not validate(bad_claim)
    assert schema["properties"]["narration"]["maxLength"] == 360


def test_compact_prompt_keeps_unrolled_sampling_and_equivalent_actor_contract():
    from explainer_direction.authoring import _compact_prompt_schema, _scene_response_schema

    jsonschema = pytest.importorskip("jsonschema")
    brief = {"id": "scene_one", "claim_ids": ["supported"], "duration_ms": 5000}
    schema = _scene_response_schema(
        brief, {"scene_briefs": [brief]}, {"context": {}, "library": []}
    )["properties"]["actors"]["items"]
    original = deepcopy(schema)
    compact = _compact_prompt_schema(schema)
    assert len(json.dumps(compact)) < len(json.dumps(schema))
    assert "$defs" in compact
    jsonschema.Draft202012Validator.check_schema(compact)
    actor = {
        "id": "field", "kind": "panel", "role": "background",
        "label": "Ground", "meaning": "Visual setting",
        "evidence_ids": ["supported"], "layout": {"anchor": "background"},
        "payload": {}, "initial": {"opacity": 1, "position": "home"},
    }
    invalid = deepcopy(actor)
    invalid["initial"]["value"] = 0
    for sample in (actor, invalid):
        assert jsonschema.Draft202012Validator(schema).is_valid(sample) == (
            jsonschema.Draft202012Validator(compact).is_valid(sample)
        )
    with http_server(lambda _: (200, envelope(), {})) as (url, received):
        LocalOpenAIProvider(url, "exact-local-model").complete("author_scene", {
            "response_schema": schema, "brief": "unaltered",
        })
        payload = received[0][2]
        assert payload["response_format"]["json_schema"]["schema"] == original
        sent = json.loads(payload["messages"][1]["content"])["request"]
        assert sent["response_schema"] == compact
        assert sent["brief"] == "unaltered"
    assert schema == original


def test_prompt_compaction_does_not_touch_literals_or_existing_references():
    from explainer_direction.authoring import _compact_prompt_schema

    schema = {"const": {"properties": {"not_a_schema": {"type": "integer"}}}}
    assert _compact_prompt_schema(schema) == schema
    referenced = {"$defs": {"value": {"type": "string"}}, "$ref": "#/$defs/value"}
    assert _compact_prompt_schema(referenced) == referenced


def test_construction_grammar_bounds_words_identity_and_quantitative_capabilities():
    from explainer_direction.authoring import _scene_construction_schema

    jsonschema = pytest.importorskip("jsonschema")
    brief = {"id": "scene_one", "section_id": "section_one", "intent": "Explain storage",
             "claim_ids": ["supported"], "duration_ms": 1000}
    schema = _scene_construction_schema(brief, {"scene_briefs": [brief]}, {
        "context": {"target_seconds": 1}, "library": [], "evidence": [{"id": "supported"}],
    })
    jsonschema.Draft202012Validator.check_schema(schema)
    assert "events" not in schema["properties"] and "events" not in schema["required"]
    assert schema["properties"]["claim_ids"] == {"const": ["supported"]}
    kinds = {variant["properties"]["kind"]["const"] for variant in schema["properties"]["actors"]["items"]["oneOf"]}
    assert not kinds & {"image", "number", "bar", "axis"}
    validate = jsonschema.Draft202012Validator(schema["properties"]["narration"]).is_valid
    assert validate("Store water uphill.")
    assert validate("Store the water high uphill.")
    assert not validate('Store "water" uphill.')
    assert not validate("It stores energy,_READY_0")
    assert not validate("It stores energy")


def test_speech_budget_counts_punctuation_separated_words():
    from explainer_direction.authoring import _speech_word_count

    assert _speech_word_count("Pumped storage works like a water battery. It stores energy,Moves,then,returns,when,needed.") == 15
    assert _speech_word_count("It stores energy, then releases it.") == 6
    assert _speech_word_count("The 2.5-hour battery holds 1,000 units.") == 7


def test_scene_repairs_replace_only_each_failing_field():
    from explainer_direction.authoring import _bounded, _scene_construction_schema, _speech_word_count

    request = {"context": {"target_seconds": 2}, "library": [], "evidence": evidence_for(),
               "brief": "test", "family": "ocean", "prior_scenes": []}
    scene = creative(request)["scenes"][0]
    scene.pop("events")
    scene["narration"] = "Words,joined,with,commas,still,count,as,spoken,words."
    scene["actors"][0]["layout"]["relative_to"] = "missing_actor"
    brief = {k: scene[k] for k in ("id", "section_id", "intent", "claim_ids", "duration_ms")}
    request.update(scene_brief=brief, outline={"scene_briefs": [brief]})
    request["response_schema"] = _scene_construction_schema(brief, request["outline"], request)

    class Patches:
        supports_schema_patch = True
        is_test_fixture = True
        identity = {"provider": "test", "model": "test"}

        def __init__(self):
            self.calls = []

        def complete(self, task, data):
            assert task == "repair"
            self.calls.append(deepcopy(data))
            assert set(data["response_schema"]["properties"]) == {"replacement"}
            if data["repair_scope"].endswith(".narration"):
                return {"replacement": ["Signals", "move."]}
            return {"replacement": scene["actors"][-1]["id"]}

    def validate(value):
        if _speech_word_count(value["narration"]) > 6:
            raise ScoreError("narration exceeds speech budget", "$.scenes[0].narration")
        if value["actors"][0]["layout"]["relative_to"] == "missing_actor":
            raise ScoreError("unknown reference", "$.scenes[0].actors[0].layout.relative_to")
        return value

    provider = Patches()
    result = _bounded(provider, "author_scene", request, validate, 2, initial_response=scene)
    assert len(provider.calls) == 2
    assert result["narration"] == "Signals move."
    expected = deepcopy(scene)
    expected["narration"] = "Signals move."
    expected["actors"][0]["layout"]["relative_to"] = scene["actors"][-1]["id"]
    assert result == expected
    assert provider.calls[0]["speech_budget"]["maximum_words"] == 6
    assert provider.calls[0]["response_schema"]["properties"]["replacement"]["maxItems"] == 6
    assert provider.calls[0]["response_schema"]["properties"]["replacement"]["items"]["maxLength"] == 32
    assert "scene_structure" not in provider.calls[0]
    assert provider.calls[1]["scene_structure"]["narration"] == "Signals move."
    assert all("repair_anchor" not in call and "previous_response" not in call for call in provider.calls)


def test_spoken_word_repair_normalizes_punctuation_without_packing_words():
    from explainer_direction.authoring import _bounded, _scene_construction_schema

    request = {"context": {"target_seconds": 2}, "library": [], "evidence": evidence_for(),
               "brief": "test", "family": "ocean", "prior_scenes": []}
    scene = creative(request)["scenes"][0]
    scene.pop("events")
    scene["narration"] = "This introduction is far too long for the allotted speech."
    brief = {k: scene[k] for k in ("id", "section_id", "intent", "claim_ids", "duration_ms")}
    request.update(scene_brief=brief, outline={"scene_briefs": [brief]})
    request["response_schema"] = _scene_construction_schema(brief, request["outline"], request)

    class Repair:
        supports_schema_patch = True

        def __init__(self, replacement):
            self.replacement = replacement

        def complete(self, task, data):
            assert task == "repair"
            return {"replacement": self.replacement}

    def validate(value):
        if value["narration"] == scene["narration"]:
            raise ScoreError("speech budget", "$.scenes[0].narration")
        return value

    assert _bounded(Repair(["Energy", "moves", "through", "water"]), "author_scene",
                    request, validate, 1, initial_response=scene)["narration"] == "Energy moves through water."
    with pytest.raises(ProviderError, match="spoken-word budget"):
        _bounded(Repair(["Energy moves", "through", "water"]), "author_scene",
                 request, validate, 1, initial_response=scene)
    with pytest.raises(ProviderError, match="spoken-word budget"):
        _bounded(Repair(["energyandwaterandenergyandwaterandenergy"]), "author_scene",
                 request, validate, 1, initial_response=scene)


def test_multiple_unbound_layout_hints_share_a_field_only_repair():
    from explainer_direction.authoring import _bounded, _scene_construction_schema

    request = {"context": {"target_seconds": 8}, "library": [], "evidence": evidence_for(),
               "brief": "test", "family": "ocean", "prior_scenes": []}
    scene = creative(request)["scenes"][0]
    scene.pop("events")
    for actor in scene["actors"]:
        actor["layout"]["relative_to"] = "imaginary_canvas"
    brief = {k: scene[k] for k in ("id", "section_id", "intent", "claim_ids", "duration_ms")}
    request.update(scene_brief=brief, outline={"scene_briefs": [brief]})
    request["response_schema"] = _scene_construction_schema(brief, request["outline"], request)

    class Repair:
        supports_schema_patch = True

        def complete(self, task, data):
            assert task == "repair"
            assert data["repair_fields"] == [
                {"actor_id": actor["id"], "field": "layout.relative_to"} for actor in scene["actors"]
            ]
            fields = data["response_schema"]["properties"]["replacement"]["properties"]
            previous = set()
            for actor in scene["actors"]:
                choices = fields[actor["id"]].get("oneOf", [{}])[0].get("enum", [])
                assert set(choices) <= previous
                previous.add(actor["id"])
            return {"replacement": {actor["id"]: None for actor in scene["actors"]}}

    def validate(value):
        for index, actor in enumerate(value["actors"]):
            if actor["layout"].get("relative_to") == "imaginary_canvas":
                raise ScoreError("unbound reference", f"$.scenes[0].actors[{index}].layout.relative_to")
        return value

    expected = deepcopy(scene)
    for actor in expected["actors"]:
        actor["layout"].pop("relative_to")
    assert _bounded(Repair(), "author_scene", request, validate, 1, initial_response=scene) == expected


def test_scene_layout_repair_can_explicitly_remove_only_an_invalid_optional_reference():
    from explainer_direction.authoring import _bounded, _scene_construction_schema

    request = {"context": {"target_seconds": 8}, "library": [], "evidence": evidence_for(),
               "brief": "test", "family": "ocean", "prior_scenes": []}
    scene = creative(request)["scenes"][0]
    scene.pop("events")
    root = scene["actors"][0]
    root["layout"]["relative_to"] = "background"
    for child in scene["actors"][1:]:
        child["layout"]["relative_to"] = root["id"]
    brief = {k: scene[k] for k in ("id", "section_id", "intent", "claim_ids", "duration_ms")}
    request.update(scene_brief=brief, outline={"scene_briefs": [brief]})
    request["response_schema"] = _scene_construction_schema(brief, request["outline"], request)

    class Patch:
        supports_schema_patch = True
        is_test_fixture = True
        identity = {"provider": "test", "model": "test"}

        def complete(self, task, data):
            assert task == "repair"
            assert set(data["response_schema"]["properties"]) == {"replacement"}
            assert data["response_schema"]["properties"]["replacement"] == {"type": "null"}
            return {"replacement": None}

    def validate(value):
        ids = {actor["id"]: actor for actor in value["actors"]}
        if value["actors"][0]["layout"].get("relative_to") == "background":
            raise ScoreError("unbound id background", "$.scenes[0].actors[0].layout.relative_to")
        for actor in value["actors"]:
            seen = set()
            current = actor
            while "relative_to" in current["layout"]:
                assert current["id"] not in seen
                seen.add(current["id"])
                current = ids[current["layout"]["relative_to"]]
        return value

    expected = deepcopy(scene)
    expected["actors"][0]["layout"].pop("relative_to")
    assert _bounded(Patch(), "author_scene", request, validate, 1, initial_response=scene) == expected


def test_scene_grammar_disallows_nonquantitative_value_bindings():
    from explainer_direction.authoring import _scene_construction_schema

    jsonschema = pytest.importorskip("jsonschema")
    request = {"context": {"target_seconds": 8}, "library": [], "evidence": evidence_for(),
               "brief": "test", "family": "ocean"}
    brief = {"id": "scene_0", "section_id": "explanation", "intent": "Represent supported changes",
             "claim_ids": ["baseline", "updated"], "duration_ms": 4000}
    schema = _scene_construction_schema(brief, {"scene_briefs": [brief]}, request)
    branches = {branch["properties"]["kind"]["const"]: branch
                for branch in schema["properties"]["actors"]["items"]["oneOf"]}
    for kind, branch in branches.items():
        assert ("value_binding" in branch["properties"]) == (kind in ("number", "bar"))
        assert ("value_binding" in branch["required"]) == (kind in ("number", "bar"))
        jsonschema.Draft202012Validator.check_schema(branch)
    sample = creative(request, "mechanism")["scenes"][0]["actors"][0]
    sample["value_binding"] = "baseline"
    assert not jsonschema.Draft202012Validator(branches["shape"]).is_valid(sample)
    sample.pop("value_binding")
    assert jsonschema.Draft202012Validator(branches["shape"]).is_valid(sample)


def test_motion_grammar_rejects_unknown_actors_uninitialized_properties_and_invented_values():
    from explainer_direction.authoring import _choreography_response_schema, _compact_prompt_schema

    jsonschema = pytest.importorskip("jsonschema")
    request = {"evidence": evidence_for(), "library": [], "family": "ocean", "context": {}, "brief": "Test"}
    scene = creative(request, "measurement")["scenes"][0]
    schema = _choreography_response_schema(scene, request, "s0_")
    for branch in schema["properties"]["events"]["items"]["oneOf"]:
        assert branch["properties"]["claim_ids"]["maxItems"] == len(scene["claim_ids"])
        assert branch["properties"]["dependencies"]["items"] == branch["properties"]["id"]
        assert branch["properties"]["claim_ids"]["items"] == {"enum": scene["claim_ids"]}
    compact = _compact_prompt_schema(schema)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator.check_schema(compact)
    candidate = deepcopy(scene["events"][0])
    candidate["id"] = "s0_advance"
    candidate.pop("targets")
    valid = {"events": [candidate]}
    assert jsonschema.Draft202012Validator(schema).is_valid(valid)
    assert jsonschema.Draft202012Validator(compact).is_valid(valid)
    following = deepcopy(candidate)
    following["id"] = "s0_follow"
    following["dependencies"] = ["s0_advance"]
    assert jsonschema.Draft202012Validator(schema).is_valid({"events": [candidate, following]})
    assert jsonschema.Draft202012Validator(compact).is_valid({"events": [candidate, following]})
    cases = []
    wrong_actor = deepcopy(valid)
    wrong_actor["events"][0]["changes"]["baseline"] = {"opacity": 1}
    cases.append(wrong_actor)
    wrong_property = deepcopy(valid)
    wrong_property["events"][0]["changes"]["readout_0"]["flow"] = .5
    cases.append(wrong_property)
    uninitialized = deepcopy(valid)
    uninitialized["events"][0]["changes"]["readout_0"]["highlight"] = 1
    cases.append(uninitialized)
    unbound_value = deepcopy(valid)
    unbound_value["events"][0]["changes"]["readout_0"]["value"] = 123456
    cases.append(unbound_value)
    wrong_verb = deepcopy(valid)
    wrong_verb["events"][0]["verb"] = "reveal"
    cases.append(wrong_verb)
    other_scene = deepcopy(valid)
    other_scene["events"][0]["dependencies"] = ["s1_advance"]
    cases.append(other_scene)
    evidence_as_dependency = deepcopy(valid)
    evidence_as_dependency["events"][0]["dependencies"] = [scene["claim_ids"][0]]
    cases.append(evidence_as_dependency)
    fake_alignment = deepcopy(valid)
    fake_alignment["events"][0]["cue"] = {"kind": "absolute", "ms": 0, "basis": "reported_alignment"}
    cases.append(fake_alignment)
    redundant_target = deepcopy(valid)
    redundant_target["events"][0]["targets"] = ["baseline"]
    cases.append(redundant_target)
    repeated_evidence = deepcopy(valid)
    repeated_evidence["events"][0]["claim_ids"] = ["baseline"] * 3
    cases.append(repeated_evidence)
    for invalid in cases:
        assert not jsonschema.Draft202012Validator(schema).is_valid(invalid)
        assert not jsonschema.Draft202012Validator(compact).is_valid(invalid)


def test_prepared_voice_timing_bounds_motion_before_authoring_and_preserves_raw_audio(tmp_path):
    import wave

    from explainer_direction.audio import CachedLocalVoice, produce_voice, sha256
    from explainer_direction.authoring import _choreography_response_schema

    jsonschema = pytest.importorskip("jsonschema")

    class Voice:
        is_test_fixture = True

        def __init__(self):
            self.calls = 0

        def synthesize(self, text, output, *, scene_id, film_id):
            self.calls += 1
            with wave.open(str(output), "wb") as target:
                target.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                target.writeframes(b"\x00\x00" * (24 * 3200))
            words = [{"word": word, "start_ms": 100 + i * 200, "end_ms": 200 + i * 200}
                     for i, word in enumerate(text.split())]
            return {
                "audio_path": str(output),
                "source": source("test_only_voice"),
                "provider": "test-fixture-tts",
                "route": "synthetic-test-only",
                "local": True,
                "alignment": {
                    "provider": "test-fixture-tts",
                    "method": "provider_word_timestamps",
                    "audio_sha256": sha256(output),
                    "words": words,
                },
                "test_fixture": True,
            }

    provider = MockProvider()
    voice = Voice()
    cached = CachedLocalVoice(voice)
    durations = []

    def prepare(partial):
        index = len(partial["scenes"])
        result = produce_voice(partial, tmp_path / f"prepared-{index}", cached, test_fixture=True)
        durations.append(result["segments"][-1]["duration_ms"])
        return {"duration_ms": durations[-1], "alignment": result["alignment"]}

    score = authored(provider=provider, staged=True, concept_first=True, prepare_narration=prepare)
    assert durations == [3200, 3200]
    assert [scene["duration_ms"] for scene in score["scenes"]] == durations
    requests = [request for task, request in provider.calls if task == "author_choreography"]
    assert len(requests) == 2
    for request, scene in zip(requests, score["scenes"]):
        assert request["scene_structure"]["duration_ms"] == 3200
        assert request["voice_timing"]["duration_ms"] == 3200
        schema = _choreography_response_schema(request["scene_structure"], request, request["event_id_prefix"])
        assert request["response_schema"] == schema
        first, hold = [deepcopy(event) for event in scene["events"]]
        for event in (first, hold):
            event.pop("targets")
        assert jsonschema.Draft202012Validator(schema).is_valid({"events": [first, hold]})
        for branch in schema["properties"]["events"]["items"]["oneOf"]:
            assert branch["properties"]["cue"]["oneOf"][2]["properties"]["occurrence"]["maximum"] == 0
    final = produce_voice(score, tmp_path / "final", cached, test_fixture=True)
    bind_alignment(score, final["alignment"])
    assert voice.calls == 2
    assert [sha256(record["raw_path"]) for record in final["segments"]] == [
        sha256(tmp_path / "prepared-1/000-raw.wav"),
        sha256(tmp_path / "prepared-2/001-raw.wav"),
    ]


def test_choreography_cannot_change_accepted_construction_or_replan():
    def mutate(task, request, result):
        if task == "author_choreography":
            result["actors"] = []
        return result
    provider = MockProvider(mutate)
    score = authored(provider=provider, staged=True, max_repairs=1)
    assert all(scene["actors"] for scene in score["scenes"])
    motion_requests = [request for task, request in provider.calls if task == "author_choreography"]
    repairs = [request for task, request in provider.calls if task == "repair"]
    assert len(motion_requests) == len(repairs) == 4
    for request, repair in zip(motion_requests, repairs):
        assert request["scene_structure"] == repair["scene_structure"]
        assert repair["original_task"] == "author_choreography"
    assert sum(task == "plan_strategies" for task, _ in provider.calls) == 1
