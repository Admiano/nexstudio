"""Fail-closed semantic language for an execution-only explainer body.

No model calls, media generation, creative certification or geometry authoring occur
here. JSON Schema is published for providers; validation uses only the stdlib.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, DecimalException
import math
import json
import re
from typing import Any, NoReturn
from urllib.parse import urlsplit

SCORE_SCHEMA = "explainer-direction.score/v1"
PLAN_SCHEMA = "explainer-direction.plan/v1"
ALIGNMENT_SCHEMA = "explainer-direction.alignment/v1"
ASPECTS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
FAMILIES = ("neon", "candy", "forest", "ocean", "ember")
ROLES = ("background", "surface", "text", "muted", "primary", "secondary", "accent", "positive", "negative")
EASINGS = ("linear", "ease_in", "ease_out", "ease_in_out", "step")
ANCHORS = ("home", "focus", "context", "start", "end")
SPATIAL_RELATIONS = {"above": ("y", False), "below": ("y", True),
                     "left_of": ("x", False), "right_of": ("x", True)}
RELATIONS = ("comparison", "causes", "contains", "sequence", "connected_to", "labels", "supports", "flows_to",
             "produces", "stores", "powers", "aligns_with", *SPATIAL_RELATIONS)
LICENSES = ("CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "MIT", "Apache-2.0", "OFL-1.1", "public-domain", "owned", "permission")
# unit -> (dimension, multiplier to canonical unit, additive canonical offset).
# Incompatible currencies are intentionally separate dimensions. No inferred units.
UNIT_TABLE = {
    "1": ("ratio", 1, 0), "%": ("ratio", .01, 0), "count": ("count", 1, 0),
    "ms": ("time", .001, 0), "s": ("time", 1, 0), "min": ("time", 60, 0), "h": ("time", 3600, 0),
    "mm": ("length", .001, 0), "cm": ("length", .01, 0), "m": ("length", 1, 0), "km": ("length", 1000, 0),
    "g": ("mass", .001, 0), "kg": ("mass", 1, 0), "K": ("temperature", 1, 0), "degC": ("temperature", 1, 273.15),
    "USD": ("currency:USD", 1, 0), "EUR": ("currency:EUR", 1, 0),
    "J": ("energy", 1, 0), "kJ": ("energy", 1000, 0), "W": ("power", 1, 0), "kW": ("power", 1000, 0),
    "Pa": ("pressure", 1, 0), "kPa": ("pressure", 1000, 0), "mL": ("volume", .001, 0), "L": ("volume", 1, 0),
    "m/s": ("speed", 1, 0), "km/h": ("speed", 1 / 3.6, 0),
    "byte": ("data", 1, 0), "KB": ("data", 1000, 0), "MB": ("data", 1_000_000, 0), "GB": ("data", 1_000_000_000, 0),
    "Hz": ("frequency", 1, 0), "kHz": ("frequency", 1000, 0),
}
COMMON_PROPERTIES = ("opacity", "reveal", "scale", "rotation", "highlight", "position")
KIND_PROPERTIES = {
    "text": ("text",), "number": ("value",), "shape": ("draw", "fill", "variant"),
    "bar": ("value", "fill"), "axis": ("draw",), "connector": ("draw",),
    "selector": ("selection",), "particles": ("flow", "fill"), "panel": ("fill",),
    "image": (), "group": (),
}
VERB_PROPERTIES = {
    "reveal": ("opacity", "reveal"), "hide": ("opacity", "reveal"), "draw": ("draw",),
    "fill": ("fill",), "grow": ("fill", "value", "scale"),
    "update": ("opacity", "reveal", "scale", "rotation", "highlight", "position", "text", "value", "draw", "fill", "variant", "selection", "flow"),
    "select": ("selection", "highlight"), "highlight": ("highlight", "opacity"),
    "connect": ("draw", "opacity"), "move": ("position",), "rotate": ("rotation",),
    "reframe": ("position", "scale", "rotation"),
    "morph": ("variant", "fill", "scale"), "settle": ("position", "scale", "rotation", "opacity", "highlight"),
    "hold": (),
}
CAPABILITIES: dict[str, Any] = {
    "schema": "explainer-direction.capabilities/v1",
    "kinds": list(KIND_PROPERTIES),
    "properties": {kind: list(COMMON_PROPERTIES + props) for kind, props in KIND_PROPERTIES.items()},
    "event_properties": {
        kind: [p for p in COMMON_PROPERTIES + props
               if kind != "connector" or p not in ("position", "scale", "rotation")]
        for kind, props in KIND_PROPERTIES.items()
    },
    "verbs": list(VERB_PROPERTIES), "verb_properties": {k: list(v) for k, v in VERB_PROPERTIES.items()},
    "easings": list(EASINGS), "relations": list(RELATIONS), "aspects": list(ASPECTS),
    "transitions": ["cut", "fade", "wipe", "hold"],
    "asset_policy": "local raster images with declared commercial-use-safe provenance; no downloads, SVG code or generators",
    "timing_policy": "fraction cues are provisional; unresolved word cues require reported alignment before compilation",
    "spatial_policy": "Evidence-bound above/below/left_of/right_of are physical ordering, not causal flow. Endpoints share a layout scope and use home poses; move a shared group, not the constrained endpoints.",
    "particle_flow_policy": "Material transport uses stream particles with an explicit payload.path {connector: actor ID, direction: forward|reverse}. Flow traverses that connector's native moving route. Unbound streams move only within their own box and cannot represent transport between other actors. Path-bound particles use home/unit scale and initialize flow; move endpoints or groups instead.",
    "rotation_policy": "Rotation is an illustrative signed degree transform around an actor's native box centre, not a measured bearing. Initialize rotation explicitly before animating it. Rotate endpoints or groups, not attached connectors or path-bound material. Do not rotate groups whose descendants have source-bound physical ordering.",
    "authority": "P8; standalone authoring is DEVELOPMENT_PREFLIGHT, never CREATIVE_LOCKED",
}


class ScoreError(ValueError):
    """Contract violation with an addressable path; never a fallback instruction."""
    def __init__(self, message: str, path: str = "$"):
        self.path = path
        super().__init__(f"{path}: {message}")


def _obj(properties, required=None, *, additional=False):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else list(required), "additionalProperties": additional}


def _arr(item, minimum=0, *, unique=False):
    out = {"type": "array", "items": item, "minItems": minimum}
    if unique:
        out["uniqueItems"] = True
    return out


def _enum(values):
    return {"type": "string", "enum": list(values)}


def _num(minimum=None, maximum=None, *, integer=False):
    out = {"type": "integer" if integer else "number"}
    if minimum is not None:
        out["minimum"] = minimum
    if maximum is not None:
        out["maximum"] = maximum
    return out


TEXT = {"type": "string", "minLength": 1, "maxLength": 12000}
ID = {"type": "string", "pattern": r"^[A-Za-z][A-Za-z0-9_.:-]{0,95}$"}
IDS = _arr(ID, unique=True)
SOURCE_JSON_SCHEMA = _obj({"id": ID, "uri": TEXT, "locator": TEXT, "license": _enum(LICENSES), "commercial_use": {"const": True}})
QUANTITY_JSON_SCHEMA = _obj({"value": _num(), "unit": _enum(UNIT_TABLE), "dimension": _enum(sorted({x[0] for x in UNIT_TABLE.values()}))})
EVIDENCE_JSON_SCHEMA = _obj({
    "id": ID, "claim": TEXT, "status": _enum(("supported", "uncertain", "illustrative")), "source": SOURCE_JSON_SCHEMA,
    "quantity": QUANTITY_JSON_SCHEMA,
    "comparison": _obj({"group": ID, "conditions": {"type": "object", "minProperties": 1}}),
}, ("id", "claim", "status", "source"))
STATE_PROPERTIES = {
    **{k: _num(0, 1) for k in ("opacity", "reveal", "highlight", "draw", "fill", "flow")},
    "scale": _num(.05, 8), "rotation": _num(-3600, 3600),
    "position": _enum(ANCHORS), "text": TEXT, "value": _num(),
    "selection": _num(0, 63, integer=True), "variant": _enum(("circle", "rect", "diamond", "hexagon")),
}
STATE_JSON_SCHEMA = _obj(STATE_PROPERTIES, ())
REQUIRED_KIND_PROPERTIES = {"text": ("text",), "number": ("value",), "bar": ("value",),
                            "selector": ("selection",), "shape": ("variant",)}
LAYOUT_JSON_SCHEMA = _obj({
    "anchor": _enum(("primary", "secondary", "context", "caption", "background", "start", "end", "center")),
    "rank": _num(0, 100, integer=True), "relative_to": ID,
    "arrangement": _enum(("auto", "row", "column", "radial", "stack", "plot")),
}, ("anchor",))
DOMAIN = {"type": "array", "items": _num(), "minItems": 2, "maxItems": 2}
PAYLOAD_SCHEMAS = {
    "text": _obj({"text": TEXT, "purpose": _enum(("label", "headline", "annotation", "conclusion", "caption")),
                  "max_lines": _num(1, 8, integer=True), "numeric_role": _enum(("quantity", "ordinal"))}, ("text", "purpose")),
    "number": _obj({"unit": _enum(UNIT_TABLE), "dimension": TEXT, "decimals": _num(0, 6, integer=True)}, ("unit", "dimension")),
    "shape": _obj({"shape": _enum(("circle", "rect", "diamond", "hexagon")),
                   "aspect_ratio": _num(.1, 10)}, ("shape",)),
    "bar": _obj({"domain": DOMAIN, "unit": _enum(UNIT_TABLE), "dimension": TEXT,
                 "orientation": _enum(("auto", "horizontal", "vertical"))}, ("domain", "unit", "dimension")),
    "axis": _obj({"domain": DOMAIN, "unit": _enum(UNIT_TABLE), "dimension": TEXT,
                  "orientation": _enum(("auto", "horizontal", "vertical")), "ticks": _num(2, 12, integer=True)}, ("domain", "unit", "dimension")),
    "connector": _obj({"from": ID, "to": ID, "arrow": {"type": "boolean"}, "routing": _enum(("direct", "elbow"))}, ("from", "to", "arrow")),
    "selector": _obj({"options": {**_arr(TEXT, 1, unique=True), "maxItems": 64}}),
    "particles": _obj({"count": _num(1, 64, integer=True), "arrangement": _enum(("grid", "stream", "radial")),
                       "illustrative": {"const": True},
                       "path": _obj({"connector": ID, "direction": _enum(("forward", "reverse"))})},
                      ("count", "arrangement", "illustrative")),
    "panel": _obj({}),
    "image": _obj({"src": TEXT, "mime": _enum(("image/png", "image/jpeg", "image/webp")), "fit": _enum(("contain", "cover")), "source": SOURCE_JSON_SCHEMA}),
    "group": _obj({"children": _arr(ID, 1, unique=True)}),
}
MEANING_JSON_SCHEMA = _obj({
    "entities": _arr(_obj({
        "id": ID, "kind": _enum(("system", "place", "device", "material", "energy", "signal", "organism", "process", "concept")),
        "label": {"type": "string", "minLength": 1, "maxLength": 120}, "evidence_ids": IDS,
    }), 1),
    "facts": _arr(_obj({
        "id": ID, "kind": _enum(("above", "below", "left_of", "right_of", "flows_to", "causes", "contains", "connected_to", "produces", "stores", "powers", "aligns_with")),
        "from": ID, "to": ID, "evidence_ids": IDS, "carrier": ID, "via": ID,
        "process": ID,
    }, ("id", "kind", "from", "to", "evidence_ids")), 1),
    "quantities": _arr(_obj({"claim_id": ID, "subject": ID})),
})
MEANING_BINDING_JSON_SCHEMA = _obj({"entity": ID, "fact": ID}, ())
ACTOR_JSON_SCHEMA = _obj({
    "id": ID, "kind": _enum(KIND_PROPERTIES), "role": _enum(ROLES), "label": TEXT, "meaning": TEXT,
    "evidence_ids": IDS, "layout": LAYOUT_JSON_SCHEMA, "payload": {"type": "object"},
    "initial": STATE_JSON_SCHEMA, "value_binding": ID, "retain": ID,
    "meaning_binding": MEANING_BINDING_JSON_SCHEMA,
}, ("id", "kind", "role", "label", "meaning", "evidence_ids", "layout", "payload", "initial"))
# Providers can select a kind without being asked for geometry or a finished-scene widget.
ACTOR_JSON_SCHEMA["allOf"] = [
    {"if": {"properties": {"kind": {"const": kind}}}, "then": {"properties": {
        "payload": payload,
        "initial": _obj({p: STATE_PROPERTIES[p] for p in COMMON_PROPERTIES + KIND_PROPERTIES[kind]},
                        ("opacity", "position") + REQUIRED_KIND_PROPERTIES.get(kind, ())),
    }}}
    for kind, payload in PAYLOAD_SCHEMAS.items()
]
for branch in ACTOR_JSON_SCHEMA["allOf"]:
    if branch["if"]["properties"]["kind"]["const"] == "connector":
        initial = branch["then"]["properties"]["initial"]["properties"]
        initial["position"] = {"const": "home"}
        initial["scale"] = {"const": 1}
        initial["rotation"] = {"const": 0}
CUE_JSON_SCHEMA = {"oneOf": [
    _obj({"kind": {"const": "fraction"}, "fraction": _num(0, 1), "provisional": {"const": True}}),
    _obj({"kind": {"const": "absolute"}, "ms": _num(0), "basis": _enum(("authored", "reported_alignment")), "alignment_id": ID}, ("kind", "ms", "basis")),
    _obj({"kind": {"const": "word"}, "word": TEXT, "occurrence": _num(0, integer=True), "edge": _enum(("start", "end")),
          "offset_ms": _num(), "resolved_ms": _num(0), "alignment_id": ID}, ("kind", "word", "occurrence", "edge")),
]}
EVENT_JSON_SCHEMA = _obj({
    "id": ID, "verb": _enum(VERB_PROPERTIES), "targets": IDS, "cue": CUE_JSON_SCHEMA,
    "duration_ms": _num(0), "dependencies": IDS, "easing": _enum(EASINGS),
    "changes": {"type": "object", "additionalProperties": STATE_JSON_SCHEMA},
    "value_bindings": {"type": "object", "additionalProperties": ID}, "claim_ids": IDS, "rationale": TEXT,
}, ("id", "verb", "targets", "cue", "duration_ms", "dependencies", "easing", "changes", "claim_ids", "rationale"))
RELATION_JSON_SCHEMA = _obj({"id": ID, "kind": _enum(RELATIONS), "from": ID, "to": ID, "evidence_ids": IDS})
TRANSITION_JSON_SCHEMA = _obj({"kind": _enum(CAPABILITIES["transitions"]), "duration_ms": _num(0),
                               "direction": _enum(("left", "right", "up", "down"))}, ("kind", "duration_ms"))
COMPOSITION_JSON_SCHEMA = _obj({"flow": _enum(("auto", "row", "column", "radial", "stack", "plot")),
                                "density": _enum(("open", "balanced", "dense")), "focus": ID}, ("flow", "density"))
STYLE_JSON_SCHEMA = _obj({
    "family": _enum(FAMILIES), "palette": _obj({role: {"type": "string", "pattern": r"^#[0-9a-fA-F]{6}$"} for role in ROLES}),
    "typography": _obj({"font_family": TEXT, "font_url": TEXT, "font_license": _enum(("OFL-1.1", "Apache-2.0")),
                         "headline_size": _num(28, 120), "body_size": _num(20, 72), "label_size": _num(16, 64)}),
    "strokes": _obj({"width": _num(.5, 12), "corner_radius": _num(0, 40)}),
    "materials": _obj({"surface": _enum(("flat", "outlined"))}),
    "motion": _obj({"character": _enum(("precise", "calm", "energetic")), "easing": _enum(EASINGS)}),
})
PROVENANCE_JSON_SCHEMA = _obj({
    "mode": _enum(("development", "p8_bound")), "creative_authority": {"const": "P8"},
    "status": _enum(("DEVELOPMENT_PREFLIGHT", "P8_SEMANTIC_BOUND")), "direction_id": ID,
    "source": SOURCE_JSON_SCHEMA,
    "model": _obj({"provider": TEXT, "model": TEXT, "request_id": TEXT}, ("provider", "model")),
    "p8": _obj({"state_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                 "board_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}),
    "test_fixture": {"type": "boolean"},
}, ("mode", "creative_authority", "status", "direction_id", "source"))
WORD_JSON_SCHEMA = _obj({"word": TEXT, "start_ms": _num(0), "end_ms": _num(0)})
ALIGNMENT_JSON_SCHEMA = _obj({
    "schema": {"const": ALIGNMENT_SCHEMA}, "id": ID,
    "source": _obj({"provider": TEXT, "method": _enum(("provider_word_timestamps", "forced_alignment")),
                    "audio_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}),
    "scenes": _arr(_obj({"scene_id": ID, "duration_ms": _num(1), "words": _arr(WORD_JSON_SCHEMA, 1)}), 1),
})
SCENE_JSON_SCHEMA = _obj({
    "id": ID, "section_id": ID, "intent": TEXT, "claim_ids": _arr(ID, 1, unique=True), "narration": TEXT,
    "duration_ms": _num(1, 600000), "actors": _arr(ACTOR_JSON_SCHEMA, 1), "relations": _arr(RELATION_JSON_SCHEMA),
    "events": _arr(EVENT_JSON_SCHEMA), "transition": TRANSITION_JSON_SCHEMA, "composition": COMPOSITION_JSON_SCHEMA,
    "timing": _enum(("provisional", "authored", "aligned")), "motif": TEXT,
}, ("id", "section_id", "intent", "claim_ids", "narration", "duration_ms", "actors", "relations", "events", "transition"))
SCENE_JSON_SCHEMA["properties"]["events"]["maxItems"] = 400
SCORE_JSON_SCHEMA = _obj({
    "schema": {"const": SCORE_SCHEMA}, "film_id": ID, "title": TEXT, "brief": TEXT,
    "evidence": _arr(EVIDENCE_JSON_SCHEMA, 1), "style": STYLE_JSON_SCHEMA,
    "sections": _arr(_obj({"id": ID, "title": TEXT, "intent": TEXT}), 1), "scenes": _arr(SCENE_JSON_SCHEMA, 1),
    "provenance": PROVENANCE_JSON_SCHEMA, "alignment": ALIGNMENT_JSON_SCHEMA,
    "meaning_graph": MEANING_JSON_SCHEMA,
}, ("schema", "film_id", "title", "brief", "evidence", "style", "sections", "scenes", "provenance"))
SCORE_JSON_SCHEMA["$schema"] = "https://json-schema.org/draft/2020-12/schema"

# Compiled coordinates are pixels. Only the compiler, never a creative model,
# supplies geometry or absolute film-time property tracks.
COMPILED_STATE_PROPERTIES = {k: v for k, v in STATE_PROPERTIES.items() if k != "position"}
COMPILED_STATE_PROPERTIES.update({"x": _num(), "y": _num()})
GEOMETRY_JSON_SCHEMA = _obj({
    "x": _num(), "y": _num(), "width": _num(0), "height": _num(0),
    "points": _arr(_obj({"x": _num(), "y": _num()}), 2), "font_size": _num(1), "line_height": _num(1),
    "lines": _arr(TEXT), "anchors": _obj({a: _obj({"x": _num(), "y": _num()}) for a in ANCHORS}),
}, ("x", "y", "width", "height"))
TRACK_JSON_SCHEMA = _obj({
    "event_id": ID, "actor_id": ID, "property": _enum(COMPILED_STATE_PROPERTIES), "from": {}, "to": {},
    "start_ms": _num(0), "end_ms": _num(0), "easing": _enum(EASINGS), "verb": _enum(VERB_PROPERTIES),
    "rationale": TEXT, "claim_ids": IDS,
})
PLAN_ACTOR_JSON_SCHEMA = _obj({
    "id": ID, "identity": ID, "kind": _enum(KIND_PROPERTIES), "role": _enum(ROLES), "label": TEXT, "meaning": TEXT,
    "evidence_ids": IDS, "geometry": GEOMETRY_JSON_SCHEMA, "payload": {"type": "object"},
    "initial": _obj(COMPILED_STATE_PROPERTIES, ("opacity", "x", "y")), "retained": {"type": "boolean"},
    "layout": LAYOUT_JSON_SCHEMA, "value_binding": ID,
    "meaning_binding": MEANING_BINDING_JSON_SCHEMA,
}, ("id", "identity", "kind", "role", "label", "meaning", "evidence_ids", "geometry", "payload", "initial", "retained", "layout"))
PLAN_ACTOR_JSON_SCHEMA["allOf"] = deepcopy(ACTOR_JSON_SCHEMA["allOf"])
for conditional in PLAN_ACTOR_JSON_SCHEMA["allOf"]:
    kind = conditional["if"]["properties"]["kind"]["const"]
    initial_props = {p: COMPILED_STATE_PROPERTIES[p] for p in COMMON_PROPERTIES + KIND_PROPERTIES[kind] if p != "position"}
    initial_props.update({"x": _num(), "y": _num()})
    conditional["then"]["properties"]["initial"] = _obj(initial_props, ("opacity", "x", "y") + REQUIRED_KIND_PROPERTIES.get(kind, ()))
    if kind in ("bar", "axis"):
        payload_schema = conditional["then"]["properties"]["payload"]
        payload_schema["properties"]["orientation"] = _enum(("horizontal", "vertical"))
        payload_schema["required"].append("orientation")
PLAN_EVENT_JSON_SCHEMA = _obj({"id": ID, "verb": _enum(VERB_PROPERTIES), "targets": IDS, "start_ms": _num(0),
                              "end_ms": _num(0), "dependencies": IDS, "claim_ids": IDS, "rationale": TEXT})
PLAN_JSON_SCHEMA = _obj({
    "schema": {"const": PLAN_SCHEMA}, "film_id": ID, "title": TEXT, "aspect": _enum(ASPECTS),
    "canvas": _obj({"width": _num(1, integer=True), "height": _num(1, integer=True)}),
    "output": _obj({"fps": _num(1, 60, integer=True), "format": {"const": "mp4"}, "background": {"type": "string", "pattern": r"^#[0-9a-fA-F]{6}$"}}),
    "duration_ms": _num(1), "style": STYLE_JSON_SCHEMA, "evidence": _arr(EVIDENCE_JSON_SCHEMA, 1),
    "scenes": _arr(_obj({
        "id": ID, "section_id": ID, "intent": TEXT, "claim_ids": IDS, "narration": TEXT,
        "start_ms": _num(0), "end_ms": _num(0), "actors": _arr(PLAN_ACTOR_JSON_SCHEMA, 1),
        "relations": _arr(RELATION_JSON_SCHEMA), "events": _arr(PLAN_EVENT_JSON_SCHEMA), "tracks": _arr(TRACK_JSON_SCHEMA),
        "transition": _obj({"kind": _enum(CAPABILITIES["transitions"]), "start_ms": _num(0), "end_ms": _num(0),
                             "direction": _enum(("left", "right", "up", "down"))}, ("kind", "start_ms", "end_ms")),
        "composition": COMPOSITION_JSON_SCHEMA, "constraints": _arr(TEXT), "motif": TEXT,
    }, ("id", "section_id", "intent", "claim_ids", "narration", "start_ms", "end_ms", "actors", "relations", "events", "tracks", "transition", "composition", "constraints")), 1),
    "provenance": PROVENANCE_JSON_SCHEMA, "meaning_graph": MEANING_JSON_SCHEMA,
    "direction": _obj({"authority": {"const": "P8"}, "status": _enum(("DEVELOPMENT_PREFLIGHT", "P8_SEMANTIC_BOUND")),
                        "score_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "timing": _enum(("provisional", "authored", "aligned"))}),
})
PLAN_JSON_SCHEMA["required"].remove("meaning_graph")
PLAN_JSON_SCHEMA["$schema"] = "https://json-schema.org/draft/2020-12/schema"


def _fail(message, path) -> NoReturn:
    raise ScoreError(message, path)


def _json_safe(value, path="$", depth=0):
    if depth > 50:
        _fail("JSON nesting exceeds 50", path)
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            _fail("text must contain valid Unicode scalar values", path)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        if type(value) is float and not math.isfinite(value):
            _fail("non-finite number", path)
        if abs(value) > 2 ** 53 - 1:
            _fail("number exceeds browser-safe precision/range", path)
        return
    if type(value) is list:
        for i, item in enumerate(value):
            _json_safe(item, f"{path}[{i}]", depth + 1)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                _fail("JSON object keys must be strings", path)
            _json_safe(key, path, depth + 1)
            _json_safe(item, f"{path}.{key}", depth + 1)
        return
    _fail("must contain only JSON-native values", path)


def _check(value, schema, path):
    """Small validator for the exact published schema vocabulary, not general JSON Schema."""
    if "oneOf" in schema:
        matches = 0
        for choice in schema["oneOf"]:
            try:
                _check(value, choice, path)
                matches += 1
            except ScoreError:
                pass
        if matches != 1:
            _fail("must match exactly one admitted cue shape", path)
        return
    expected = schema.get("type")
    if expected is None and "properties" in schema and type(value) is dict:
        expected = "object"
    valid_type = {"object": type(value) is dict, "array": type(value) is list,
                  "string": type(value) is str, "number": type(value) in (int, float),
                  "integer": type(value) is int, "boolean": type(value) is bool,
                  "null": value is None}
    if expected and not valid_type[expected]:
        _fail(f"expected {expected}", path)
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        _fail(f"expected constant {schema['const']!r}", path)
    if "enum" in schema and value not in schema["enum"]:
        _fail(f"unsupported value {value!r}; allowed {schema['enum']}", path)
    if expected == "object":
        props = schema.get("properties", {})
        missing = set(schema.get("required", ())) - set(value)
        if missing:
            _fail(f"missing fields {sorted(missing)}", path)
        if len(value) < schema.get("minProperties", 0):
            _fail("object must not be empty", path)
        if len(value) > schema.get("maxProperties", float("inf")):
            _fail("object has too many fields", path)
        for key, item in value.items():
            if key in props:
                _check(item, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties", True) is False:
                _fail("unknown field", f"{path}.{key}")
            elif type(schema.get("additionalProperties")) is dict:
                _check(item, schema["additionalProperties"], f"{path}.{key}")
    elif expected == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", float("inf")):
            _fail("array length out of bounds", path)
        if schema.get("uniqueItems") and any(item in value[:i] for i, item in enumerate(value)):
            _fail("duplicate array entries", path)
        for i, item in enumerate(value):
            _check(item, schema.get("items", {}), f"{path}[{i}]")
    elif expected == "string":
        if not schema.get("minLength", 0) <= len(value.strip()) <= schema.get("maxLength", float("inf")):
            _fail("string length out of bounds or blank", path)
        if "pattern" in schema and not re.search(schema["pattern"], value):
            _fail("string pattern mismatch", path)
    elif expected in ("integer", "number"):
        if not schema.get("minimum", -float("inf")) <= value <= schema.get("maximum", float("inf")):
            _fail("number out of bounds", path)
    for conditional in schema.get("allOf", ()):
        try:
            _check(value, conditional["if"], path)
        except ScoreError:
            continue
        _check(value, conditional["then"], path)


def _index(items, path):
    result = {}
    for i, item in enumerate(items):
        if item["id"] in result:
            _fail(f"duplicate id {item['id']}", f"{path}[{i}].id")
        result[item["id"]] = item
    return result


def _refs(ids, known, path):
    unknown = set(ids) - set(known)
    if unknown:
        _fail(f"unbound ids {sorted(unknown)}", path)


def _source(source, path, registry=None):
    _check(source, SOURCE_JSON_SCHEMA, path)
    if source["license"] == "permission" and source["locator"].strip().lower() in ("unknown", "none", "n/a"):
        _fail("permission requires an actual rights locator", path)
    if registry is not None:
        previous = registry.get(source["id"])
        if previous is not None and previous != source:
            _fail("stable source id cannot declare conflicting provenance/rights", path)
        registry[source["id"]] = source


def _document_sources(document):
    """One source identity across evidence, supplied art and direction provenance."""
    registry: dict[str, Any] = {}
    for i, record in enumerate(document["evidence"]):
        _source(record["source"], f"$.evidence[{i}].source", registry)
    _source(document["provenance"]["source"], "$.provenance.source", registry)
    for i, scene in enumerate(document["scenes"]):
        for j, actor in enumerate(scene["actors"]):
            if actor["kind"] == "image":
                _source(actor["payload"]["source"], f"$.scenes[{i}].actors[{j}].payload.source", registry)


def _local_uri(uri, path):
    if uri != uri.strip() or any(ord(c) < 32 or ord(c) == 127 for c in uri):
        _fail("local asset paths cannot contain controls or surrounding whitespace", path)
    try:
        parsed = urlsplit(uri)
    except ValueError:
        _fail("malformed local asset URL", path)
    if parsed.scheme or parsed.netloc or "\\" in uri or any(p == ".." for p in parsed.path.split("/")):
        _fail("only local paths/URLs without traversal are admitted", path)
    if parsed.query or parsed.fragment or not parsed.path or "%" in parsed.path:
        _fail("asset path cannot contain query, fragment or encoded traversal", path)


def _font(style, path="$.style.typography.font_url"):
    uri = style["typography"]["font_url"]
    _local_uri(uri, path)
    if not uri.casefold().endswith((".woff2", ".woff", ".ttf", ".otf")):
        _fail("font URL must reference a local font file", path)


def _quantity(quantity, path):
    _check(quantity, QUANTITY_JSON_SCHEMA, path)
    if UNIT_TABLE[quantity["unit"]][0] != quantity["dimension"]:
        _fail("unit does not match declared dimension", path)
    if quantity["dimension"] == "count" and (quantity["value"] < 0 or quantity["value"] != int(quantity["value"])):
        _fail("count must be a non-negative integer", path)


def quantity_in_unit(evidence, unit):
    """Convert an explicit evidence quantity into a compatible admitted unit."""
    _json_safe(evidence, "$.evidence")
    _check(evidence, EVIDENCE_JSON_SCHEMA, "$.evidence")
    if "quantity" not in evidence:
        raise ScoreError("numerical binding requires typed evidence quantity")
    q = evidence["quantity"]
    _quantity(q, "$.quantity")
    if type(unit) is not str or unit not in UNIT_TABLE or UNIT_TABLE[unit][0] != q["dimension"]:
        raise ScoreError("incompatible target unit/dimension")
    if unit == q["unit"]:
        return q["value"]
    _, factor, offset = UNIT_TABLE[q["unit"]]
    _, target_factor, target_offset = UNIT_TABLE[unit]
    converted = (q["value"] * factor + offset - target_offset) / target_factor
    if not math.isfinite(converted) or abs(converted) > 2 ** 53 - 1:
        raise ScoreError("converted quantity exceeds browser-safe numeric range")
    return converted


def validate_evidence(evidence):
    _json_safe(evidence, "$.evidence")
    _check(evidence, _arr(EVIDENCE_JSON_SCHEMA, 1), "$.evidence")
    _index(evidence, "$.evidence")
    sources: dict[str, Any] = {}
    for i, record in enumerate(evidence):
        path = f"$.evidence[{i}]"
        _source(record["source"], path + ".source", sources)
        if "quantity" in record:
            _quantity(record["quantity"], path + ".quantity")
        if "comparison" in record:
            for k, v in record["comparison"]["conditions"].items():
                if not k.strip() or v is None or (type(v) is str and not v.strip()) or v == [] or v == {}:
                    _fail("comparison conditions must be explicit and nonempty", path + ".comparison.conditions")
    return deepcopy(evidence)


def _spatial_constraints(scene, actors, parents, path, *, compiled=False):
    graphs: dict[str, dict[str, list[str]]] = {"x": {}, "y": {}}
    members: set[str] = set()
    scopes = dict(parents)
    for relation in scene["relations"]:
        if relation["kind"] == "contains":
            scopes.setdefault(relation["to"], relation["from"])
    for index, relation in enumerate(scene["relations"]):
        if relation["kind"] not in SPATIAL_RELATIONS:
            continue
        rp = f"{path}.relations[{index}]"
        left, right = relation["from"], relation["to"]
        if scopes.get(left) != scopes.get(right):
            _fail("spatial endpoints require a shared layout scope/group", rp)
        if not relation["evidence_ids"]:
            _fail("physical ordering needs explicit evidence", rp + ".evidence_ids")
        axis, reverse = SPATIAL_RELATIONS[relation["kind"]]
        first, second = (right, left) if reverse else (left, right)
        graphs[axis].setdefault(first, [])
        graphs[axis].setdefault(second, []).append(first)
        members.update((left, right))
        if compiled:
            a, b = actors[first], actors[second]
            extent = "width" if axis == "x" else "height"
            if a["initial"][axis] + a["geometry"][extent] / 2 >= b["initial"][axis] + b["geometry"][extent] / 2:
                _fail("compiled layout reverses declared physical ordering", rp)
    for axis, graph in graphs.items():
        _acyclic(graph, path + ".relations.spatial." + axis)
    ordered_groups = set()
    for aid in members:
        parent = parents.get(aid)
        while parent is not None:
            ordered_groups.add(parent)
            parent = parents.get(parent)
    for aid in ordered_groups:
        if actors[aid]["initial"].get("rotation", 0) != 0:
            _fail("rotation of a physical ordering group is unsupported", path + ".actors." + aid)
    for index, actor in enumerate(scene["actors"]):
        if actor["id"] not in members:
            continue
        ap = f"{path}.actors[{index}]"
        if actor["kind"] == "connector" or actor["layout"]["anchor"] == "background":
            _fail("physical ordering endpoints must be content entities, not paths/backgrounds", ap)
        if not compiled and actor["initial"]["position"] != "home":
            _fail("physical ordering endpoints use their fitted home pose", ap + ".initial.position")
    if compiled:
        for index, track in enumerate(scene["tracks"]):
            if track["actor_id"] in ordered_groups and track["property"] == "rotation" and (track["from"] != 0 or track["to"] != 0):
                _fail("rotation of a physical ordering group is unsupported", f"{path}.tracks[{index}]")
            if track["actor_id"] in members and track["property"] in ("x", "y"):
                _fail("move the shared physical group, not a constrained endpoint", f"{path}.tracks[{index}]")
    else:
        for index, event in enumerate(scene["events"]):
            for aid in ordered_groups & event["changes"].keys():
                if event["changes"][aid].get("rotation", 0) != 0:
                    _fail("rotation of a physical ordering group is unsupported",
                          f"{path}.events[{index}].changes.{aid}.rotation")
            for aid in members & event["changes"].keys():
                if "position" in event["changes"][aid]:
                    _fail("move the shared physical group, not a constrained endpoint",
                          f"{path}.events[{index}].changes.{aid}.position")


def _normal_word(word):
    return re.sub(r"^\W+|\W+$", "", word.casefold(), flags=re.UNICODE)


def _word_intervals(scene, path):
    previous_end = 0
    for j, word in enumerate(scene["words"]):
        if not word["start_ms"] < word["end_ms"] <= scene["duration_ms"] or word["start_ms"] < previous_end:
            _fail("word intervals must be positive, ordered, nonoverlapping and within audio duration", f"{path}.words[{j}]")
        if len(word["word"].split()) != 1 or not _normal_word(word["word"]):
            _fail("each word interval must contain one spoken token", f"{path}.words[{j}]")
        previous_end = word["end_ms"]


def resolve_word_cue(cue, scene_alignment):
    """Return a reported scene-local time; never fabricate or space words uniformly."""
    _json_safe(cue, "$.cue")
    _check(cue, CUE_JSON_SCHEMA["oneOf"][2], "$.cue")
    _json_safe(scene_alignment, "$.scene_alignment")
    _check(scene_alignment, ALIGNMENT_JSON_SCHEMA["properties"]["scenes"]["items"], "$.scene_alignment")
    _word_intervals(scene_alignment, "$.scene_alignment")
    wanted = _normal_word(cue["word"])
    if not wanted or any(c.isspace() for c in cue["word"].strip()):
        raise ScoreError("word cue must name exactly one token")
    matches = [w for w in scene_alignment["words"] if _normal_word(w["word"]) == wanted]
    occurrence = cue["occurrence"]
    if occurrence >= len(matches):
        raise ScoreError("word cue not found in reported alignment")
    resolved = matches[occurrence][cue["edge"] + "_ms"] + cue.get("offset_ms", 0)
    if not 0 <= resolved <= scene_alignment["duration_ms"]:
        raise ScoreError("resolved word cue outside reported audio duration", "$.cue")
    return resolved


def validate_alignment(alignment, score=None):
    _json_safe(alignment, "$.alignment")
    _check(alignment, ALIGNMENT_JSON_SCHEMA, "$.alignment")
    ids = set()
    score_scenes = {s["id"]: s for s in score["scenes"]} if score is not None else None
    for i, scene in enumerate(alignment["scenes"]):
        path = f"$.alignment.scenes[{i}]"
        if scene["scene_id"] in ids:
            _fail("duplicate aligned scene", path)
        ids.add(scene["scene_id"])
        _word_intervals(scene, path)
        if score_scenes is not None:
            if scene["scene_id"] not in score_scenes:
                _fail("alignment references unknown scene", path)
            narration_words = [_normal_word(x) for x in score_scenes[scene["scene_id"]]["narration"].split()]
            reported_words = [_normal_word(x["word"]) for x in scene["words"]]
            if narration_words != reported_words:
                _fail("reported words must match the complete narration token sequence", path)
    if score_scenes is not None and ids != set(score_scenes):
        _fail("alignment must cover every scene exactly once", "$.alignment.scenes")
    return deepcopy(alignment)


def _value_matches(value, record, unit):
    expected = quantity_in_unit(record, unit)
    if unit == record["quantity"]["unit"]:
        return value == expected
    # Absolute roundoff only for explicit conversion. Relative tolerance would
    # silently admit whole invented units at large magnitudes.
    return math.isclose(value, expected, rel_tol=0, abs_tol=1e-9)


def _literal_matches(number, value):
    try:
        return Decimal(number) == Decimal(str(value))
    except DecimalException:
        return False


def _bound_value(actor, value, binding, evidence, claims, path):
    if binding not in evidence or binding not in actor["evidence_ids"] or binding not in claims:
        _fail("value binding must reference actor and scene/event evidence", path)
    record = evidence[binding]
    if record["status"] == "illustrative" and actor["kind"] in ("bar", "number"):
        # Illustrative numerical examples are legal but cannot masquerade as measurements.
        if "illustrative" not in actor["meaning"].casefold():
            _fail("illustrative values must be declared illustrative in actor meaning", path)
    if not _value_matches(value, record, actor["payload"]["unit"]):
        _fail("displayed value differs from bound evidence (after explicit unit conversion)", path)
    if actor["kind"] == "bar":
        low, high = actor["payload"]["domain"]
        if not low <= value <= high:
            _fail("bar value outside explicit domain", path)


def _text_binding(text, actor, evidence, claims, path):
    bindings = set(actor["evidence_ids"]) & set(claims)
    if actor["payload"]["purpose"] != "label" and not bindings:
        _fail("displayed claims/headlines/captions require evidence binding", path)
    number_pattern = r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    clean_text = text.replace(",", "").replace("\u2212", "-")
    numbers = re.findall(number_pattern + r"(?!\d|\.\d)", clean_text)
    aliases = {"°C": "degC", "°F": "degF", "$": "USD", "€": "EUR"}
    unit_pattern = "|".join(re.escape(u) for u in sorted(set(UNIT_TABLE) | set(aliases), key=len, reverse=True) if u != "1")
    units_in_text = [(m.group(1), aliases.get(m.group(2), m.group(2)))
                     for m in re.finditer("(" + number_pattern + r")\s*(" + unit_pattern + r")(?!\w)", clean_text)]
    units_in_text += [(m.group(2), aliases[m.group(1)])
                      for m in re.finditer(r"([$€])\s*(" + number_pattern + r")(?!\d|\.\d)", clean_text)]
    if actor["payload"].get("numeric_role") == "ordinal":
        if actor["payload"]["purpose"] != "label":
            _fail("ordinal exemption is only for process/sequence labels, not measured claims", path)
        if units_in_text or any(not n.lstrip("+").isdigit() or not 1 <= int(n) <= 2 ** 53 - 1 for n in numbers):
            _fail("ordinal labels require positive integral step indices without measured units", path)
        return
    quantities = [evidence[e]["quantity"] for e in bindings if "quantity" in evidence[e]]
    for number in numbers:
        if not any(_literal_matches(number, q["value"]) for q in quantities):
            _fail("numerical text must match typed evidence; use number actors for converted units", path)
    for number, unit in units_in_text:
        if not any(q["unit"] == unit and _literal_matches(number, q["value"]) for q in quantities):
            _fail("numerical text unit/value must match its typed evidence", path)


def _actor(actor, actors, evidence, scene_claims, path, *, initial_variant=True):
    kind = actor["kind"]
    _check(actor["payload"], PAYLOAD_SCHEMAS[kind], path + ".payload")
    _refs(actor["evidence_ids"], scene_claims, path + ".evidence_ids")
    label_payload = {"purpose": "label"}
    if kind == "text" and actor["payload"].get("numeric_role") == "ordinal":
        label_payload["numeric_role"] = "ordinal"
    _text_binding(actor["label"], {"evidence_ids": actor["evidence_ids"], "payload": label_payload}, evidence, scene_claims, path + ".label")
    state = actor["initial"]
    allowed = set(CAPABILITIES["properties"][kind])
    if set(state) - allowed:
        _fail("state property is unsupported for this actor kind", path + ".initial")
    required = {"opacity", "position"}
    required.update(REQUIRED_KIND_PROPERTIES.get(kind, ()))
    if not required <= set(state):
        _fail(f"explicit initial state requires {sorted(required)}", path + ".initial")
    if kind in ("number", "bar", "axis"):
        unit = actor["payload"]["unit"]
        if UNIT_TABLE[unit][0] != actor["payload"]["dimension"]:
            _fail("render payload unit/dimension mismatch", path + ".payload")
        if not actor["evidence_ids"]:
            _fail("data actors require typed evidence", path)
        if any("quantity" not in evidence[e] or evidence[e]["quantity"]["dimension"] != actor["payload"]["dimension"] for e in actor["evidence_ids"]):
            _fail("data actor evidence must share its declared dimension", path)
    if kind in ("axis", "bar") and actor["payload"]["domain"][0] >= actor["payload"]["domain"][1]:
        _fail("domain must have increasing endpoints", path + ".payload.domain")
    if kind in ("number", "bar"):
        if "value_binding" not in actor:
            _fail("explicit initial value_binding required", path)
        _bound_value(actor, state["value"], actor["value_binding"], evidence, scene_claims, path + ".initial.value")
    elif "value_binding" in actor:
        _fail("value_binding is only for number/bar actors", path)
    if kind == "text":
        _text_binding(actor["payload"]["text"], actor, evidence, scene_claims, path + ".payload.text")
        _text_binding(state["text"], actor, evidence, scene_claims, path + ".initial.text")
    if kind == "selector":
        if state["selection"] >= len(actor["payload"]["options"]):
            _fail("selection index out of range", path)
        for i, option in enumerate(actor["payload"]["options"]):
            _text_binding(option, {"evidence_ids": actor["evidence_ids"], "payload": {"purpose": "label"}},
                          evidence, scene_claims, f"{path}.payload.options[{i}]")
    if kind == "shape" and initial_variant and state["variant"] != actor["payload"]["shape"]:
        _fail("initial variant must match shape payload", path)
    if kind == "image":
        _source(actor["payload"]["source"], path + ".payload.source")
        _local_uri(actor["payload"]["src"], path + ".payload.src")
        extension = {"image/png": ".png", "image/jpeg": (".jpg", ".jpeg"), "image/webp": ".webp"}[actor["payload"]["mime"]]
        if not actor["payload"]["src"].casefold().endswith(extension):
            _fail("image extension must agree with admitted raster mime", path + ".payload")
    if kind == "connector":
        _refs([actor["payload"]["from"], actor["payload"]["to"]], actors, path + ".payload")
        if actor["id"] in (actor["payload"]["from"], actor["payload"]["to"]) or actor["payload"]["from"] == actor["payload"]["to"]:
            _fail("connector endpoints must name two distinct other actors", path)
        if state["position"] != "home" or state.get("scale", 1) != 1 or state.get("rotation", 0) != 0:
            _fail("attached connectors use home position, unit scale and zero rotation; move their endpoints or shared group", path + ".initial")
    if kind == "particles" and "path" in actor["payload"]:
        binding = actor["payload"]["path"]
        target = binding["connector"]
        _refs([target], actors, path + ".payload.path.connector")
        if actor["payload"]["arrangement"] != "stream" or actors[target]["kind"] != "connector":
            _fail("path-bound streams require a connector actor", path + ".payload.path")
        if actor["id"] in (actors[target]["payload"]["from"], actors[target]["payload"]["to"]):
            _fail("path-bound material cannot be its own path endpoint", path + ".payload.path")
        if state["position"] != "home" or state.get("scale", 1) != 1 or state.get("rotation", 0) != 0:
            _fail("path-bound particles use home position, unit scale and zero rotation; move endpoints or groups", path + ".initial")
        if "flow" not in state:
            _fail("path-bound particles require initialized flow", path + ".initial.flow")
    if kind == "group":
        _refs(actor["payload"]["children"], actors, path + ".payload.children")
    if kind == "selector" and len(actor["payload"]["options"]) > 64:
        _fail("selector supports at most 64 options", path + ".payload.options")
    if "relative_to" in actor["layout"]:
        _refs([actor["layout"]["relative_to"]], actors, path + ".layout.relative_to")
        if actor["layout"]["relative_to"] == actor["id"]:
            _fail("actor cannot be placed relative to itself", path)
    if "retain" in actor and actor["retain"] != actor["id"]:
        _fail("retained identity must equal stable actor id", path + ".retain")


def _acyclic(graph, path):
    visited = set()
    for root in graph:
        if root in visited:
            continue
        stack = [(root, False)]
        visiting: set[str] = set()
        while stack:
            node, exiting = stack.pop()
            if exiting:
                visiting.remove(node)
                visited.add(node)
                continue
            if node in visiting:
                _fail(f"dependency cycle involving {node}", path)
            if node in visited:
                continue
            visiting.add(node)
            stack.append((node, True))
            stack.extend((child, False) for child in reversed(graph.get(node, ())))


def _provenance(provenance, path):
    _source(provenance["source"], path + ".source")
    if provenance["mode"] == "development":
        if provenance["status"] != "DEVELOPMENT_PREFLIGHT" or "p8" in provenance:
            _fail("development cannot imply P8 approval or creative lock", path)
    elif provenance["status"] != "P8_SEMANTIC_BOUND" or "p8" not in provenance or provenance.get("test_fixture"):
        _fail("P8 binding requires state and board hashes, and cannot be a fixture", path)


def _comparison(relation, actors, evidence, path):
    left, right = actors[relation["from"]], actors[relation["to"]]
    for actor in (left, right):
        if "value_binding" not in actor:
            _fail("comparisons require two typed number/bar actors", path)
    records = [evidence[eid] for a in (left, right) for eid in a["evidence_ids"]]
    if any("quantity" not in record for record in records):
        _fail("comparison evidence must be typed quantities", path)
    if any(record["quantity"]["dimension"] != records[0]["quantity"]["dimension"] for record in records):
        _fail("comparison dimensions are incompatible", path)
    if any("comparison" not in e for e in records) or any(json.dumps(record["comparison"], sort_keys=True) != json.dumps(records[0]["comparison"], sort_keys=True) for record in records):
        _fail("comparison requires identical explicit group and conditions", path)
    if any(e["status"] == "illustrative" for e in records) and any(e["status"] != "illustrative" for e in records):
        _fail("illustrative and measured values cannot be compared as equivalent evidence", path)
    _refs([a["value_binding"] for a in (left, right)], relation["evidence_ids"], path + ".evidence_ids")


def validate_score(score):
    """Validate syntax, evidence bindings and stateful execution; return an isolated copy.

    Word cues may remain unresolved for authoring. A compiler must resolve them
    from validate_alignment data or fail. Holds and intentional motifs are legal.
    """
    _json_safe(score)
    _check(score, SCORE_JSON_SCHEMA, "$")
    evidence = _index(validate_evidence(score["evidence"]), "$.evidence")
    if "meaning_graph" in score:
        from .meaning import validate_meaning
        validate_meaning(score["meaning_graph"], score["evidence"])
    sections = _index(score["sections"], "$.sections")
    _index(score["scenes"], "$.scenes")
    if set(sections) != {s["section_id"] for s in score["scenes"]}:
        _fail("every section must be used; every scene must bind a declared section", "$.sections")
    _provenance(score["provenance"], "$.provenance")
    _document_sources(score)
    _font(score["style"])
    alignment = validate_alignment(score["alignment"], score) if "alignment" in score else None
    alignment_scenes = {s["scene_id"]: s for s in alignment["scenes"]} if alignment else {}
    actor_history: dict[str, Any] = {}
    event_ids: set[str] = set()
    previous_section, closed_sections = None, set()
    for i, scene in enumerate(score["scenes"]):
        path = f"$.scenes[{i}]"
        _refs(scene["claim_ids"], evidence, path + ".claim_ids")
        _text_binding(scene["narration"], {"evidence_ids": scene["claim_ids"], "payload": {"purpose": "caption"}}, evidence, scene["claim_ids"], path + ".narration")
        if scene["section_id"] != previous_section:
            if scene["section_id"] in closed_sections:
                _fail("section scenes must be contiguous", path + ".section_id")
            if previous_section:
                closed_sections.add(previous_section)
            previous_section = scene["section_id"]
        if scene.get("timing") == "aligned":
            if not alignment or scene["duration_ms"] != alignment_scenes[scene["id"]]["duration_ms"]:
                _fail("aligned duration must come from complete reported alignment", path + ".timing")
        transition = scene["transition"]
        if transition["duration_ms"] > scene["duration_ms"]:
            _fail("transition exceeds scene duration", path + ".transition")
        if transition["kind"] in ("cut", "hold") and transition["duration_ms"] != 0:
            _fail("cut/hold transitions have zero duration", path + ".transition")
        if transition["kind"] in ("fade", "wipe") and transition["duration_ms"] <= 0:
            _fail("fade/wipe require positive duration", path + ".transition")
        if transition["kind"] == "wipe" and "direction" not in transition:
            _fail("wipe direction is required", path + ".transition")
        actors = _index(scene["actors"], path + ".actors")
        if "composition" in scene and "focus" in scene["composition"]:
            _refs([scene["composition"]["focus"]], actors, path + ".composition.focus")
        group_graph, layout_graph, parents = {}, {}, {}
        for j, actor in enumerate(scene["actors"]):
            actor_path = f"{path}.actors[{j}]"
            _actor(actor, actors, evidence, scene["claim_ids"], actor_path,
                   initial_variant=actor["id"] not in actor_history)
            if actor["kind"] == "group":
                group_graph[actor["id"]] = actor["payload"]["children"]
                for child in actor["payload"]["children"]:
                    if child in parents:
                        _fail("an actor cannot have multiple group parents", actor_path)
                    parents[child] = actor["id"]
            layout_graph[actor["id"]] = [actor["layout"]["relative_to"]] if "relative_to" in actor["layout"] else []
            if actor["id"] in actor_history:
                old_actor, old_state = actor_history[actor["id"]]
                if not actor.get("retain") or not old_actor.get("retain"):
                    _fail("repeated actor ids require explicit retention in both scenes", actor_path)
                invariant_fields = ("kind", "role", "label", "meaning", "evidence_ids", "payload", "meaning_binding")
                if any(actor.get(k) != old_actor.get(k) for k in invariant_fields):
                    _fail("retained identity/evidence/payload semantics cannot change", actor_path)
                if old_state is not None and actor["initial"] != old_state:
                    _fail("retained actor initial state must equal previous terminal state", actor_path + ".initial")
        _acyclic(group_graph, path + ".actors.group")
        _acyclic(layout_graph, path + ".actors.layout")
        relations = _index(scene["relations"], path + ".relations")
        for j, relation in enumerate(relations.values()):
            rp = f"{path}.relations[{j}]"
            _refs([relation["from"], relation["to"]], actors, rp)
            _refs(relation["evidence_ids"], scene["claim_ids"], rp + ".evidence_ids")
            if relation["from"] == relation["to"]:
                _fail("relations require distinct actors", rp)
            if relation["kind"] == "comparison":
                _comparison(relation, actors, evidence, rp)
        if "meaning_graph" in score:
            from .meaning import validate_construction_bindings
            validate_construction_bindings(scene, score["meaning_graph"], score["evidence"], path)
        _spatial_constraints(scene, actors, parents, path)
        for actor in actors.values():
            if actor["kind"] == "text" and actor["payload"].get("numeric_role") == "ordinal":
                if not any(r["kind"] == "sequence" and actor["id"] in (r["from"], r["to"]) for r in relations.values()):
                    _fail("ordinal labels require an explicit sequence relation", path + ".relations")
        events = _index(scene["events"], path + ".events")
        graph, cue_times = {}, {}
        for j, event in enumerate(scene["events"]):
            ep = f"{path}.events[{j}]"
            if event["id"] in event_ids:
                _fail("event ids must be stable and film-unique", ep + ".id")
            event_ids.add(event["id"])
            _refs(event["targets"], actors, ep + ".targets")
            _refs(event["dependencies"], events, ep + ".dependencies")
            _refs(event["claim_ids"], scene["claim_ids"], ep + ".claim_ids")
            graph[event["id"]] = event["dependencies"]
            if event["duration_ms"] > scene["duration_ms"]:
                _fail("event duration exceeds scene", ep)
            if event["verb"] == "hold":
                if event["changes"] or event.get("value_bindings") or event["duration_ms"] <= 0:
                    _fail("hold preserves state and requires a positive duration", ep)
            elif not event["targets"] or set(event["changes"]) != set(event["targets"]):
                _fail("each linked target requires an explicit nonempty change map", ep)
            if set(event.get("value_bindings", {})) - set(event["changes"]):
                _fail("value binding references an unchanged target", ep)
            for target, changes in event["changes"].items():
                actor = actors[target]
                if not changes:
                    _fail("target change map cannot be empty", ep + ".changes")
                if actor["kind"] == "particles" and "path" in actor["payload"] and set(changes) & {"position", "scale", "rotation"}:
                    _fail("path-bound particle transforms are driven by endpoints or groups", ep + ".changes." + target)
                if set(changes) - set(CAPABILITIES["event_properties"][actor["kind"]]) or set(changes) - set(VERB_PROPERTIES[event["verb"]]):
                    # update is deliberately a linked-state operation: readout, selector,
                    # highlight, fill and marker positions can change on ONE narration cue.
                    if event["verb"] != "update" or set(changes) - set(CAPABILITIES["event_properties"][actor["kind"]]):
                        _fail("unsupported kind/property/verb binding", ep + ".changes." + target)
                if set(changes) - set(actor["initial"]):
                    _fail("every animated property needs an explicit initial value", ep + ".changes." + target)
                if "value" in changes:
                    binding = event.get("value_bindings", {}).get(target)
                    if binding is None:
                        _fail("numerical updates require value_bindings", ep)
                    _bound_value(actor, changes["value"], binding, evidence, event["claim_ids"], ep + ".changes." + target + ".value")
                elif target in event.get("value_bindings", {}):
                    _fail("value binding without numerical update", ep)
                if "text" in changes:
                    _text_binding(changes["text"], actor, evidence, event["claim_ids"], ep + ".changes." + target + ".text")
                if "selection" in changes:
                    if changes["selection"] >= len(actor["payload"]["options"]):
                        _fail("selection index out of range", ep)
                    selected = actor["payload"]["options"][changes["selection"]]
                    _text_binding(selected, {"evidence_ids": actor["evidence_ids"], "payload": {"purpose": "label"}},
                                  evidence, event["claim_ids"], ep + ".changes." + target + ".selection")
            cue = event["cue"]
            if cue["kind"] == "fraction":
                cue_time = cue["fraction"] * scene["duration_ms"]
            elif cue["kind"] == "absolute":
                cue_time = cue["ms"]
                if cue["basis"] == "reported_alignment":
                    if not alignment or cue.get("alignment_id") != alignment["id"]:
                        _fail("reported timing requires matching alignment provenance", ep + ".cue")
                elif "alignment_id" in cue:
                    _fail("authored timing cannot claim alignment provenance", ep + ".cue")
            else:
                if not _normal_word(cue["word"]) or len(cue["word"].split()) != 1:
                    _fail("word cue must name one spoken token", ep + ".cue")
                tokens = [_normal_word(w) for w in scene["narration"].split()]
                if tokens.count(_normal_word(cue["word"])) <= cue["occurrence"]:
                    _fail("word cue not present in narration", ep + ".cue")
                if ("resolved_ms" in cue) != ("alignment_id" in cue):
                    _fail("resolved word time and alignment id must be supplied together", ep + ".cue")
                cue_time = None
                if alignment:
                    cue_time = resolve_word_cue(cue, alignment_scenes[scene["id"]])
                if "resolved_ms" in cue:
                    if not alignment or cue["alignment_id"] != alignment["id"] or cue["resolved_ms"] != cue_time:
                        _fail("resolved word cue must equal actual reported interval edge", ep + ".cue")
            if cue_time is not None and not 0 <= cue_time <= scene["duration_ms"]:
                _fail("cue outside scene duration", ep + ".cue")
            cue_times[event["id"]] = cue_time
        _acyclic(graph, path + ".events.dependencies")
        # Long, legal dependency chains must not become Python recursion errors.
        if len(events) > 400:
            _fail("a scene supports at most 400 authored events", path + ".events")
        times: dict[str, Any] = {}
        def schedule(event_id):
            if event_id in times:
                return times[event_id]
            dep_ends = [schedule(dep) for dep in graph[event_id]]
            cue = cue_times[event_id]
            if cue is None or any(x is None for x in dep_ends):
                times[event_id] = None
            else:
                start = max([cue] + dep_ends)
                end = start + events[event_id]["duration_ms"]
                if end > scene["duration_ms"]:
                    _fail("dependency-resolved event exceeds scene duration", path + ".events")
                times[event_id] = end
            return times[event_id]
        for event_id in events:
            schedule(event_id)
        # Detect ambiguous overlapping writes now when timing is known. A compiler
        # repeats this check after resolving all word cues.
        writes: dict[tuple[str, str], Any] = {}
        for event in events.values():
            if times[event["id"]] is None:
                continue
            end = times[event["id"]]
            start = end - event["duration_ms"]
            for target, changes in event["changes"].items():
                for prop in changes:
                    key = (target, prop)
                    for old_start, old_end, old_id in writes.get(key, []):
                        overlap = max(start, old_start) < min(end, old_end)
                        # An instantaneous write inside a live interpolation still
                        # conflicts even though its interval has zero measure.
                        overlap |= start == end and old_start <= start < old_end
                        overlap |= old_start == old_end and start <= old_start < end
                        simultaneous = start == old_start and (start == end or old_start == old_end)
                        if overlap or simultaneous:
                            _fail(f"ambiguous writes to {target}.{prop} ({old_id}, {event['id']})", path + ".events")
                    writes.setdefault(key, []).append((start, end, event["id"]))
        terminal = {aid: deepcopy(a["initial"]) for aid, a in actors.items()}
        unknown_terminal = set()
        for event in sorted(events.values(), key=lambda e: (times[e["id"]] is None, times[e["id"]] or 0)):
            if times[event["id"]] is None:
                unknown_terminal.update(event["changes"])
            for target, changes in event["changes"].items():
                if (actors[target]["kind"] == "particles" and "path" in actors[target]["payload"]
                        and "flow" in changes and times[event["id"]] is not None and target not in unknown_terminal
                        and changes["flow"] <= terminal[target]["flow"]):
                    _fail("path-bound flow must advance in its declared process direction",
                          path + ".events." + event["id"] + ".changes." + target + ".flow")
                terminal[target].update(changes)
        for actor in actors.values():
            actor_history[actor["id"]] = (actor, None if actor["id"] in unknown_terminal else terminal[actor["id"]])
    return deepcopy(score)


def validate_plan(plan):
    """Validate the frozen execution shape plus deterministic timeline/state safety."""
    _json_safe(plan)
    _check(plan, PLAN_JSON_SCHEMA, "$")
    evidence = _index(validate_evidence(plan["evidence"]), "$.evidence")
    if "meaning_graph" in plan:
        from .meaning import validate_meaning
        validate_meaning(plan["meaning_graph"], plan["evidence"])
    _provenance(plan["provenance"], "$.provenance")
    _document_sources(plan)
    _font(plan["style"])
    if tuple(plan["canvas"][k] for k in ("width", "height")) != ASPECTS[plan["aspect"]]:
        _fail("canvas must match native aspect dimensions", "$.canvas")
    if plan["direction"]["status"] != plan["provenance"]["status"]:
        _fail("direction authority status conflicts with provenance", "$.direction")
    _index(plan["scenes"], "$.scenes")
    previous_end = 0
    identities: dict[str, Any] = {}
    all_event_ids: set[str] = set()
    for i, scene in enumerate(plan["scenes"]):
        path = f"$.scenes[{i}]"
        if scene["start_ms"] != previous_end or scene["end_ms"] <= scene["start_ms"]:
            _fail("scenes must be positive contiguous film-time intervals", path)
        previous_end = scene["end_ms"]
        _refs(scene["claim_ids"], evidence, path + ".claim_ids")
        _text_binding(scene["narration"], {"evidence_ids": scene["claim_ids"], "payload": {"purpose": "caption"}}, evidence, scene["claim_ids"], path + ".narration")
        actors = _index(scene["actors"], path + ".actors")
        events = _index(scene["events"], path + ".events")
        if all_event_ids & set(events):
            _fail("compiled event ids must be film-unique", path + ".events")
        all_event_ids.update(events)
        _refs([scene["composition"]["focus"]] if "focus" in scene["composition"] else [], actors, path + ".composition")
        group_graph, layout_graph, parents = {}, {}, {}
        for j, actor in enumerate(actors.values()):
            ap = f"{path}.actors[{j}]"
            if actor["identity"] != actor["id"]:
                _fail("compiled identity must equal stable actor id", ap + ".identity")
            # Reuse authored semantic checks; geometry lowering must not become
            # a second, weaker route for claims, assets or graph bindings.
            semantic = {k: actor[k] for k in ("id", "kind", "role", "label", "meaning", "evidence_ids", "layout", "payload")}
            if "meaning_binding" in actor:
                semantic["meaning_binding"] = actor["meaning_binding"]
            semantic["initial"] = {k: v for k, v in actor["initial"].items() if k not in ("x", "y")}
            semantic["initial"]["position"] = "home"
            if "value_binding" in actor:
                semantic["value_binding"] = actor["value_binding"]
            _actor(semantic, actors, evidence, scene["claim_ids"], ap,
                   initial_variant=actor["identity"] not in identities)
            if actor["kind"] == "particles" and "path" in actor["payload"]:
                if any(actor["initial"][axis] != actor["geometry"][axis] for axis in ("x", "y")):
                    _fail("path-bound particle initial position must be home", ap + ".initial")
            if actor["kind"] == "group":
                group_graph[actor["id"]] = actor["payload"]["children"]
                for child in actor["payload"]["children"]:
                    if child in parents:
                        _fail("an actor cannot have multiple group parents", ap)
                    parents[child] = actor["id"]
            layout_graph[actor["id"]] = [actor["layout"]["relative_to"]] if "relative_to" in actor["layout"] else []
            if actor["retained"] != (actor["identity"] in identities):
                _fail("retained flag must match prior stable identity", ap)
            if actor["identity"] in identities:
                old, terminal = identities[actor["identity"]]
                if any(old.get(k) != actor.get(k) for k in ("id", "kind", "role", "label", "meaning", "evidence_ids", "payload", "meaning_binding")):
                    _fail("retained semantic identity changed", ap)
                current = {k: v for k, v in actor["initial"].items() if k not in ("x", "y")}
                if current != terminal:
                    _fail("retained initial state must equal previous terminal state (except layout x/y)", ap + ".initial")
            if actor["kind"] in ("text", "number") and not {"font_size", "line_height", "lines"} <= set(actor["geometry"]):
                _fail("text and number geometry must include fitted type metrics", ap + ".geometry")
            if actor["kind"] in ("axis", "connector") and "points" not in actor["geometry"]:
                _fail("line primitives require compiled points", ap + ".geometry")
        _acyclic(group_graph, path + ".actors.group")
        _acyclic(layout_graph, path + ".actors.layout")
        if "meaning_graph" in plan:
            from .meaning import validate_construction_bindings
            validate_construction_bindings(scene, plan["meaning_graph"], plan["evidence"], path)
        graph = {}
        for event in events.values():
            _refs(event["targets"], actors, path + ".events.targets")
            _refs(event["claim_ids"], scene["claim_ids"], path + ".events.claim_ids")
            _refs(event["dependencies"], events, path + ".events.dependencies")
            if not scene["start_ms"] <= event["start_ms"] <= event["end_ms"] <= scene["end_ms"]:
                _fail("event interval outside scene", path + ".events")
            if event["verb"] == "hold" and event["start_ms"] >= event["end_ms"]:
                _fail("hold requires positive duration", path + ".events")
            if event["verb"] != "hold" and not event["targets"]:
                _fail("a non-hold event requires at least one changed target", path + ".events")
            graph[event["id"]] = event["dependencies"]
            if any(events[dep]["end_ms"] > event["start_ms"] for dep in event["dependencies"]):
                _fail("event begins before dependencies complete", path + ".events")
        _acyclic(graph, path + ".events.dependencies")
        writes: dict[tuple[str, str], Any] = {}
        event_tracks: dict[str, list[dict[str, Any]]] = {eid: [] for eid in events}
        for j, track in enumerate(scene["tracks"]):
            tp = f"{path}.tracks[{j}]"
            _refs([track["actor_id"]], actors, tp)
            _refs([track["event_id"]], events, tp)
            actor = actors[track["actor_id"]]
            event = events[track["event_id"]]
            prop = track["property"]
            if actor["kind"] == "connector" and prop in ("x", "y", "scale", "rotation"):
                _fail("attached connector transforms are driven by endpoints or shared groups", tp)
            if actor["kind"] == "particles" and "path" in actor["payload"] and prop in ("x", "y", "scale", "rotation"):
                _fail("path-bound particle transforms are driven by endpoints or shared groups", tp)
            if actor["kind"] == "particles" and "path" in actor["payload"] and prop == "flow" and track["to"] <= track["from"]:
                _fail("path-bound flow must advance in its declared process direction", tp)
            if prop not in actor["initial"]:
                _fail("track lacks explicit initial state", tp)
            if (track["start_ms"], track["end_ms"]) != (event["start_ms"], event["end_ms"]) or track["verb"] != event["verb"]:
                _fail("linked tracks must share event interval and semantic verb", tp)
            if track["actor_id"] not in event["targets"] or track["claim_ids"] != event["claim_ids"] or track["rationale"] != event["rationale"]:
                _fail("track target/claims/rationale must match its semantic event", tp)
            _check(track["from"], COMPILED_STATE_PROPERTIES[prop], tp + ".from")
            _check(track["to"], COMPILED_STATE_PROPERTIES[prop], tp + ".to")
            if prop in ("text", "variant", "selection") and track["easing"] != "step":
                _fail("discrete state tracks require step easing", tp)
            if prop == "text":
                _text_binding(track["to"], actor, evidence, track["claim_ids"], tp)
            if event["verb"] == "hold":
                _fail("hold has no property tracks", tp)
            admitted = set(VERB_PROPERTIES[event["verb"]])
            if "position" in admitted:
                admitted.update(("x", "y"))
            if event["verb"] != "update" and prop not in admitted:
                _fail("unsupported compiled verb/property binding", tp)
            if prop == "value":
                if actor["kind"] == "bar" and not actor["payload"]["domain"][0] <= track["to"] <= actor["payload"]["domain"][1]:
                    _fail("compiled target value outside domain", tp)
                if not any(e in actor["evidence_ids"] and "quantity" in evidence[e] and _value_matches(track["to"], evidence[e], actor["payload"]["unit"]) for e in track["claim_ids"]):
                    _fail("compiled numerical target is unbound", tp)
            if prop == "selection":
                if track["to"] >= len(actor["payload"]["options"]):
                    _fail("compiled selection out of range", tp)
                selected = actor["payload"]["options"][track["to"]]
                _text_binding(selected, {"evidence_ids": actor["evidence_ids"], "payload": {"purpose": "label"}},
                              evidence, track["claim_ids"], tp)
            key = (track["actor_id"], prop)
            writes.setdefault(key, []).append(track)
            event_tracks[track["event_id"]].append(track)
        terminal_states = {aid: {k: v for k, v in actor["initial"].items() if k not in ("x", "y")}
                           for aid, actor in actors.items()}
        for key, tracks in writes.items():
            state = actors[key[0]]["initial"][key[1]]
            end = -1
            previous_start = None
            for track in sorted(tracks, key=lambda t: (t["start_ms"], t["end_ms"])):
                if track["start_ms"] < end or track["start_ms"] == previous_start:
                    _fail("ambiguous overlapping property tracks", path + ".tracks")
                if track["from"] != state:
                    _fail("track from state is not previous deterministic terminal state", path + ".tracks")
                state, end, previous_start = track["to"], track["end_ms"], track["start_ms"]
            if key[1] not in ("x", "y"):
                terminal_states[key[0]][key[1]] = state
        for actor in actors.values():
            identities[actor["identity"]] = (actor, terminal_states[actor["id"]])
        for event in events.values():
            if event["verb"] != "hold" and {t["actor_id"] for t in event_tracks[event["id"]]} != set(event["targets"]):
                _fail("compiled event must retain changes for every linked target", path + ".events")
            for target in event["targets"]:
                position = [t for t in event_tracks[event["id"]]
                            if t["actor_id"] == target and t["property"] in ("x", "y")]
                if position:
                    if len(position) != 2 or {t["property"] for t in position} != {"x", "y"}:
                        _fail("position must lower into both x/y tracks", path + ".tracks")
                    if position[0]["easing"] != position[1]["easing"]:
                        _fail("paired position tracks must share easing", path + ".tracks")
        transition = scene["transition"]
        if not scene["start_ms"] <= transition["start_ms"] <= transition["end_ms"] <= scene["end_ms"]:
            _fail("transition interval outside scene", path + ".transition")
        if transition["end_ms"] != scene["end_ms"]:
            _fail("transition must occupy the outgoing scene tail", path + ".transition")
        if transition["kind"] in ("cut", "hold") and transition["start_ms"] != transition["end_ms"]:
            _fail("cut/hold transitions have zero duration", path + ".transition")
        if transition["kind"] in ("wipe", "fade") and transition["start_ms"] == transition["end_ms"]:
            _fail("animated transition requires positive duration", path + ".transition")
        if transition["kind"] == "wipe" and "direction" not in transition:
            _fail("wipe transition requires direction", path + ".transition")
        relations = _index(scene["relations"], path + ".relations")
        for relation in relations.values():
            _refs([relation["from"], relation["to"]], actors, path + ".relations")
            _refs(relation["evidence_ids"], scene["claim_ids"], path + ".relations.evidence_ids")
            if relation["from"] == relation["to"]:
                _fail("relations require distinct actors", path + ".relations")
            if relation["kind"] == "comparison":
                _comparison(relation, actors, evidence, path + ".relations")
        _spatial_constraints(scene, actors, parents, path, compiled=True)
        for actor in actors.values():
            if actor["kind"] == "text" and actor["payload"].get("numeric_role") == "ordinal":
                if not any(r["kind"] == "sequence" and actor["id"] in (r["from"], r["to"]) for r in relations.values()):
                    _fail("ordinal labels require an explicit sequence relation", path + ".relations")
    if previous_end != plan["duration_ms"]:
        _fail("film duration must equal last scene end", "$.duration_ms")
    return deepcopy(plan)


def sample_score(topic="water"):
    """Deterministic TEST FIXTURE ONLY; never use as a live inference fallback.

    Three unrelated domains exercise the same composable semantics. This helper
    declares illustrative evidence and development provenance, not factual proof.
    """
    topics = {
        "water": ("Water throughput", "Flow increases when the second channel opens.", "L", "volume", 20, 40),
        "energy": ("Stored energy", "Stored energy increases when the second module connects.", "kJ", "energy", 12, 24),
        "travel": ("Travel distance", "Distance increases when the second route extends.", "km", "length", 5, 10),
    }
    if topic not in topics:
        raise ScoreError("sample topic must be water, energy or travel; this is not live authoring")
    title, narration, unit, dimension, low, high = topics[topic]
    source = {"id": "fixture_source", "uri": "test-fixture://contracts", "locator": "Synthetic contract example, not production evidence", "license": "owned", "commercial_use": True}
    evidence = [{"id": eid, "claim": f"Illustrative {dimension} {value} {unit}.", "status": "illustrative", "source": deepcopy(source),
                 "quantity": {"value": value, "unit": unit, "dimension": dimension},
                 "comparison": {"group": "example", "conditions": {"scenario": "illustrative", "basis": "same mechanism"}}}
                for eid, value in (("before", low), ("after", high))]
    state = {"opacity": 1, "position": "home"}
    actors = [
        {"id": "readout", "kind": "number", "role": "primary", "label": title, "meaning": "Illustrative quantity readout", "evidence_ids": ["before", "after"],
         "layout": {"anchor": "primary"}, "payload": {"unit": unit, "dimension": dimension, "decimals": 0}, "initial": {**state, "value": low, "highlight": 0}, "value_binding": "before"},
        {"id": "meter", "kind": "bar", "role": "secondary", "label": "Magnitude", "meaning": "Illustrative magnitude of the same quantity", "evidence_ids": ["before", "after"],
         "layout": {"anchor": "secondary", "relative_to": "readout"}, "payload": {"domain": [0, high], "unit": unit, "dimension": dimension, "orientation": "auto"},
         "initial": {**state, "value": low, "fill": .5}, "value_binding": "before"},
        {"id": "stage", "kind": "selector", "role": "accent", "label": "Active stage", "meaning": "Mechanism stage selector, not a quantitative requirement", "evidence_ids": ["before", "after"],
         "layout": {"anchor": "context"}, "payload": {"options": ["Initial", "Extended"]}, "initial": {**state, "selection": 0}},
    ]
    return validate_score({
        "schema": SCORE_SCHEMA, "film_id": "fixture_" + topic, "title": title, "brief": "Test-only synchronized semantic state change.",
        "evidence": evidence,
        "style": {"family": "ocean", "palette": {"background": "#081828", "surface": "#16364A", "text": "#F1F8FC", "muted": "#A2B7C7", "primary": "#54D6E5", "secondary": "#6FA9F6", "accent": "#FFCC74", "positive": "#89E7B3", "negative": "#FFA2A2"},
                  "typography": {"font_family": "Inter", "font_url": "/engine_sources/editorial-motion-v2/assets/fonts/InterVariable.woff2", "font_license": "OFL-1.1", "headline_size": 64, "body_size": 36, "label_size": 28},
                  "strokes": {"width": 3, "corner_radius": 0}, "materials": {"surface": "flat"}, "motion": {"character": "precise", "easing": "ease_in_out"}},
        "sections": [{"id": "mechanism", "title": "Mechanism", "intent": "Show linked changes, not a still card"}],
        "scenes": [{"id": "change", "section_id": "mechanism", "intent": "Follow a coherent mechanism change", "claim_ids": ["before", "after"], "narration": narration,
                    "duration_ms": 6000, "actors": actors, "relations": [{"id": "readout_labels_meter", "kind": "labels", "from": "readout", "to": "meter", "evidence_ids": ["before", "after"]}],
                    "events": [{"id": "linked_change", "verb": "update", "targets": ["readout", "meter", "stage"], "cue": {"kind": "fraction", "fraction": .35, "provisional": True},
                                "duration_ms": 900, "dependencies": [], "easing": "ease_in_out", "changes": {"readout": {"value": high, "highlight": 1}, "meter": {"value": high, "fill": 1}, "stage": {"selection": 1}},
                                "value_bindings": {"readout": "after", "meter": "after"}, "claim_ids": ["after"], "rationale": "Link readout, magnitude and selector to the same mechanism cue"},
                               {"id": "read_change", "verb": "hold", "targets": ["readout", "meter", "stage"], "cue": {"kind": "absolute", "ms": 3000, "basis": "authored"}, "duration_ms": 2000, "dependencies": ["linked_change"], "easing": "linear", "changes": {}, "claim_ids": ["after"], "rationale": "Allow time to inspect the new state"}],
                    "transition": {"kind": "cut", "duration_ms": 0}, "composition": {"flow": "auto", "density": "balanced", "focus": "meter"}, "timing": "provisional"}],
        "provenance": {"mode": "development", "creative_authority": "P8", "status": "DEVELOPMENT_PREFLIGHT", "direction_id": "contract_fixture", "source": source, "test_fixture": True},
    })
