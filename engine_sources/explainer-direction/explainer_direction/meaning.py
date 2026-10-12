"""Typed meaning before representation; local drafts are not factual approval."""
from __future__ import annotations

from copy import deepcopy

from .contracts import MEANING_JSON_SCHEMA, ScoreError, _check, _refs, validate_evidence

ENTITY_KINDS = ("system", "place", "device", "material", "energy", "signal", "organism", "process", "concept")
FACT_KINDS = ("above", "below", "left_of", "right_of", "flows_to", "causes", "contains",
              "connected_to", "produces", "stores", "powers", "aligns_with")
PHYSICAL = {"system", "place", "device", "organism"}
CARRIERS = {"material", "energy", "signal"}


def entity_claims(graph):
    """Definition provenance plus the explicit facts in which an entity participates."""
    sources = {e["id"]: set(e["evidence_ids"]) for e in graph["entities"]}
    for fact in graph["facts"]:
        for field in ("from", "to", "carrier", "via", "process"):
            if field in fact:
                sources[fact[field]].update(fact["evidence_ids"])
    return sources


def spatial_support_claims(claim_ids, graph):
    """A process scene also needs the sourced spatial constraints on its endpoints."""
    referenced: set[str] = set()
    for fact in graph["facts"]:
        if set(claim_ids) & set(fact["evidence_ids"]):
            referenced.update(fact[field] for field in ("from", "to", "carrier", "via", "process") if field in fact)
    support = set()
    for fact in graph["facts"]:
        if fact["kind"] in ("above", "below", "left_of", "right_of") and {fact["from"], fact["to"]} <= referenced:
            support.update(fact["evidence_ids"])
    return sorted(support - set(claim_ids))

def validate_meaning_entities(entities, evidence):
    """Entity stage of the graph: unique, typed, claim-provenanced."""
    _check(entities, MEANING_JSON_SCHEMA["properties"]["entities"], "$.meaning.entities")
    records = {r["id"]: r for r in validate_evidence(evidence)}
    seen = set()
    for i, entity in enumerate(entities):
        path = f"$.meaning.entities[{i}]"
        if entity["id"] in seen:
            raise ScoreError("duplicate semantic entity", path + ".id")
        _refs(entity["evidence_ids"], records, path + ".evidence_ids")
        if not entity["evidence_ids"]:
            raise ScoreError("entity needs claim provenance", path + ".evidence_ids")
        seen.add(entity["id"])
    return deepcopy(entities)


def validate_meaning(graph, evidence):
    """Validate bindings and physical types, not whether prose entails a fact.

    Independently sourced semantic review is still required before a production
    claim. Quantities omitted here cannot be visualized as measured actor values.
    """
    _check(graph, MEANING_JSON_SCHEMA, "$.meaning")
    records = {r["id"]: r for r in validate_evidence(evidence)}
    entities = {e["id"]: e for e in validate_meaning_entities(graph["entities"], evidence)}
    facts = {}
    for i, fact in enumerate(graph["facts"]):
        path = f"$.meaning.facts[{i}]"
        if fact["id"] in facts:
            raise ScoreError("duplicate semantic fact", path + ".id")
        _refs((fact["from"], fact["to"]), entities, path)
        _refs(fact["evidence_ids"], records, path + ".evidence_ids")
        if fact["from"] == fact["to"] or not fact["evidence_ids"]:
            raise ScoreError("fact needs distinct endpoints and claim provenance", path)
        if fact["kind"] in ("above", "below", "left_of", "right_of", "flows_to"):
            if any(entities[fact[field]]["kind"] not in PHYSICAL for field in ("from", "to")):
                raise ScoreError("spatial and physical-flow endpoints must be physical entities", path)
        if fact["kind"] == "flows_to":
            if "carrier" not in fact or entities.get(fact["carrier"], {}).get("kind") not in CARRIERS:
                raise ScoreError("transport needs an admitted material, signal or energy carrier", path + ".carrier")
            if fact["carrier"] in (fact["from"], fact["to"]):
                raise ScoreError("transport carrier cannot be a route endpoint", path + ".carrier")
            if "via" in fact:
                _refs([fact["via"]], entities, path + ".via")
                if entities[fact["via"]]["kind"] not in PHYSICAL or fact["via"] in (fact["from"], fact["to"]):
                    raise ScoreError("intermediate route must be a distinct physical entity", path + ".via")
            if "process" in fact:
                _refs([fact["process"]], entities, path + ".process")
                if entities[fact["process"]]["kind"] != "process":
                    raise ScoreError("transport activity must be an admitted process", path + ".process")
        elif "carrier" in fact or "via" in fact or "process" in fact:
            raise ScoreError("only physical transport accepts carrier/via/process", path)
        if fact["kind"] == "causes" and entities[fact["to"]]["kind"] not in ("process", "concept"):
            raise ScoreError("causation targets a process or outcome, not the existence of material or energy", path)
        if fact["kind"] == "produces" and entities[fact["from"]]["kind"] not in PHYSICAL | {"process"}:
            raise ScoreError("physical producers or processes produce outputs; material does not create energy", path)
        if fact["kind"] in ("contains", "connected_to", "stores") and entities[fact["from"]]["kind"] not in PHYSICAL:
            raise ScoreError("a physical entity must contain, connect or store", path)
        if fact["kind"] == "connected_to" and entities[fact["to"]]["kind"] not in PHYSICAL:
            raise ScoreError("physical connection needs physical endpoints", path)
        if fact["kind"] == "stores" and entities[fact["to"]]["kind"] not in CARRIERS:
            raise ScoreError("a store retains material, energy or signal", path)
        if fact["kind"] == "powers" and (entities[fact["from"]]["kind"] != "energy"
                                         or entities[fact["to"]]["kind"] not in PHYSICAL | {"process"}):
            raise ScoreError("energy powers a device, physical system or process", path)
        if fact["kind"] == "aligns_with" and (
                entities[fact["from"]]["kind"] not in PHYSICAL
                or entities[fact["to"]]["kind"] not in PHYSICAL | CARRIERS | {"concept"}):
            raise ScoreError("orientation aligns a physical entity with a physical entity, field/carrier or direction", path)
        facts[fact["id"]] = fact
    bound = set()
    for i, quantity in enumerate(graph["quantities"]):
        path = f"$.meaning.quantities[{i}]"
        _refs([quantity["claim_id"]], records, path + ".claim_id")
        _refs([quantity["subject"]], entities, path + ".subject")
        if "quantity" not in records[quantity["claim_id"]]:
            raise ScoreError("only a typed quantity can bind a measured subject", path)
        if quantity["claim_id"] not in entities[quantity["subject"]]["evidence_ids"]:
            raise ScoreError("quantity's subject must carry its evidence", path)
        if quantity["claim_id"] in bound:
            raise ScoreError("duplicate quantity binding", path)
        bound.add(quantity["claim_id"])
    return deepcopy(graph)


def validate_construction_bindings(scene, graph, evidence, base="$.scene"):
    """The visual scene cannot silently turn a counted entity into a measurement."""
    meanings = validate_meaning(graph, evidence)
    entities = {e["id"]: e for e in meanings["entities"]}
    facts = {f["id"]: f for f in meanings["facts"]}
    sources = entity_claims(meanings)
    quantities = {q["claim_id"]: q["subject"] for q in meanings["quantities"]}
    actors = {a["id"]: a for a in scene["actors"]}
    if len(actors) != len(scene["actors"]):
        raise ScoreError("duplicate visual actor", base + ".actors")
    physical_actors: dict[str, list[str]] = {}
    for i, actor in enumerate(scene["actors"]):
        path = f"{base}.actors[{i}]"
        binding = actor.get("meaning_binding")
        if not isinstance(binding, dict) or set(binding) != {"entity"} and set(binding) != {"fact"}:
            raise ScoreError("visual actor needs an exact entity or fact binding", path + ".meaning_binding")
        if "entity" in binding:
            key = binding["entity"]
            _refs([key], entities, path + ".meaning_binding.entity")
            provenance = sources[key]
            if actor["kind"] in ("shape", "image", "group"):
                physical_actors.setdefault(key, []).append(actor["id"])
        else:
            key = binding["fact"]
            _refs([key], facts, path + ".meaning_binding.fact")
            provenance = facts[key]["evidence_ids"]
        if not actor["evidence_ids"] or not set(actor["evidence_ids"]) <= set(provenance):
            raise ScoreError("visual actor claims differ from the bound meaning", path + ".evidence_ids")
        if actor["kind"] in ("bar", "number", "axis"):
            candidates = [actor["value_binding"]] if actor["kind"] != "axis" else actor["evidence_ids"]
            if not any(claim in quantities and binding == {"entity": quantities[claim]} for claim in candidates):
                raise ScoreError("measured actor needs a quantity bound to the depicted entity", path)
        if actor["kind"] == "connector" and (
            "fact" not in binding or facts[key]["kind"] not in (
                "flows_to", "connected_to", "causes", "produces", "stores", "powers",
            )
        ):
            raise ScoreError("connector needs an explicit link or process fact", path + ".meaning_binding")
    for i, actor in enumerate(scene["actors"]):
        if actor["kind"] != "connector":
            continue
        path = f"{base}.actors[{i}]"
        fact = facts[actor["meaning_binding"]["fact"]]
        source, target = (actors[actor["payload"][field]] for field in ("from", "to"))
        left, right = source["meaning_binding"].get("entity"), target["meaning_binding"].get("entity")
        if fact["kind"] == "flows_to":
            chain = [fact["from"]] + ([fact["via"]] if "via" in fact else []) + [fact["to"]]
            if not any((left, right) in ((a, b), (b, a)) for a, b in zip(chain, chain[1:])):
                raise ScoreError("route does not attach adjacent physical process entities", path + ".payload")
        elif None in (left, right) or left not in (fact["from"], fact["to"]) or right not in (fact["from"], fact["to"]):
            raise ScoreError("link endpoints do not depict their fact", path + ".payload")
    for i, actor in enumerate(scene["actors"]):
        if actor["kind"] != "particles" or "path" not in actor["payload"]:
            continue
        path = f"{base}.actors[{i}].payload.path"
        route = actors[actor["payload"]["path"]["connector"]]
        fact = facts[route["meaning_binding"]["fact"]]
        if fact["kind"] != "flows_to" or actor["meaning_binding"] != {"entity": fact["carrier"]}:
            raise ScoreError("path material must depict the process's declared carrier", path)
        left, right = (actors[route["payload"][field]]["meaning_binding"]["entity"] for field in ("from", "to"))
        itinerary = [fact["from"]] + ([fact["via"]] if "via" in fact else []) + [fact["to"]]
        forward = (left, right) in tuple(zip(itinerary, itinerary[1:]))
        expected = "forward" if forward else "reverse"
        if actor["payload"]["path"]["direction"] != expected:
            raise ScoreError("particle direction contradicts the physical process", path + ".direction")
    for i, relation in enumerate(scene["relations"]):
        if relation["kind"] not in ("above", "below", "left_of", "right_of", "flows_to", "aligns_with"):
            continue
        left = actors[relation["from"]]["meaning_binding"].get("entity")
        right = actors[relation["to"]]["meaning_binding"].get("entity")
        if not any(f["kind"] == relation["kind"] and
                   f["from"] == left and f["to"] == right and
                   set(relation["evidence_ids"]) <= set(f["evidence_ids"])
                   for f in facts.values()):
            raise ScoreError("spatial/process relation lacks an exact meaning fact",
                             f"{base}.relations[{i}]")
    for fact in facts.values():
        if fact["kind"] not in ("above", "below", "left_of", "right_of"):
            continue
        if fact["from"] not in physical_actors or fact["to"] not in physical_actors:
            continue
        if not any(r["kind"] == fact["kind"] and
                   r["from"] in physical_actors[fact["from"]] and
                   r["to"] in physical_actors[fact["to"]]
                   for r in scene["relations"]):
            raise ScoreError("depicted physical entities lost their required spatial fact",
                             base + ".relations")
    return deepcopy(scene)
