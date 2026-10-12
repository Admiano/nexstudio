"""Native, deterministic lowering of semantic scores; no creative/model fallbacks.

The solver consumes actor/layout/relationship graphs, never narration keywords.
Geometry is canvas-native and every admitted state change remains addressable.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import math
from typing import NoReturn
import unicodedata

from .contracts import (
    ASPECTS, PLAN_SCHEMA, ScoreError, resolve_word_cue, validate_alignment,
    validate_plan, validate_score,
)

__all__ = ["compile_score"]

_DIRECTIONAL = {"sequence", "causes", "flows_to"}
_DISCRETE = {"text", "selection", "variant"}
_ANCHOR_ORDER = {"start": 0, "primary": 1, "center": 2, "secondary": 3,
                 "end": 4, "context": 5, "caption": 6, "background": 7}


def _error(message, path) -> NoReturn:
    raise ScoreError(message, path)


def _rect(x, y, width, height):
    return {"x": round(x, 6), "y": round(y, 6),
            "width": round(width, 6), "height": round(height, 6)}


def _inset(box, pad):
    return _rect(box["x"] + pad, box["y"] + pad,
                 max(0, box["width"] - 2 * pad), max(0, box["height"] - 2 * pad))


def _weight(actor, focus):
    # Hierarchy is semantic, not a huge implicit headline over a small widget.
    weight = {"primary": 1.4, "secondary": 1.15, "context": .8,
              "caption": .65}.get(actor["layout"]["anchor"], 1)
    if actor["id"] == focus:
        weight *= 1.3
    if actor["kind"] in ("group", "panel", "image", "particles"):
        weight *= 1.2
    return weight


def _split(ids, box, flow, actors, focus, gap, weights_override=None):
    """Constraint cells, not finished scenes. No aspect crop or narration dispatch."""
    if not ids:
        return {}
    if len(ids) == 1:
        return {ids[0]: deepcopy(box)}
    weights = [weights_override[aid] if weights_override and aid in weights_override
               else _weight(actors[aid], focus) for aid in ids]
    out = {}
    if flow in ("row", "column"):
        horizontal = flow == "row"
        extent = box["width" if horizontal else "height"] - gap * (len(ids) - 1)
        if extent <= 0:
            _error("composition cannot fit actor spacing; reduce density", "$.scenes.composition")
        position = box["x" if horizontal else "y"]
        for aid, weight in zip(ids, weights):
            size = extent * weight / sum(weights)
            out[aid] = (_rect(position, box["y"], size, box["height"]) if horizontal
                        else _rect(box["x"], position, box["width"], size))
            position += size + gap
    elif flow == "radial":
        # Fit nonoverlapping boxes around an ellipse. Fail excessive node counts,
        # rather than collapse a requested radial representation to tiny cards.
        count = len(ids)
        radius_x, radius_y = box["width"] * .34, box["height"] * .34
        size = min(box["width"], box["height"]) * min(.28, 1.45 / count)
        if size < 96:
            _error("radial constraint has too many actors for readable native slots", "$.scenes.composition")
        for index, aid in enumerate(ids):
            angle = -math.pi / 2 + 2 * math.pi * index / count
            out[aid] = _rect(box["x"] + box["width"] / 2 + radius_x * math.cos(angle) - size / 2,
                             box["y"] + box["height"] / 2 + radius_y * math.sin(angle) - size / 2,
                             size, size)
    elif flow == "stack":
        # Overlap is only admitted when explicitly requested by semantic layout.
        step = min(box["width"], box["height"]) * .1 / max(1, len(ids) - 1)
        for index, aid in enumerate(ids):
            out[aid] = _rect(box["x"] + step * index, box["y"] + step * index,
                             box["width"] - step * (len(ids) - 1),
                             box["height"] - step * (len(ids) - 1))
    else:
        # Square/compact native composition uses rows of variable-width cells,
        # not a scaled landscape strip. Last rows use all available width.
        cols = max(1, math.ceil(math.sqrt(len(ids) * box["width"] / max(1, box["height"]))))
        cols = min(cols, len(ids))
        rows = math.ceil(len(ids) / cols)
        row_height = (box["height"] - gap * (rows - 1)) / rows
        if row_height <= 0:
            _error("compact constraint cannot fit rows", "$.scenes.composition")
        for row in range(rows):
            members = ids[row * cols:(row + 1) * cols]
            band = _rect(box["x"], box["y"] + row * (row_height + gap), box["width"], row_height)
            out.update(_split(members, band, "row", actors, focus, gap, weights_override))
    return out


def _ordered(ids, actors):
    return sorted(ids, key=lambda aid: (actors[aid]["layout"].get("rank", 0),
                                       _ANCHOR_ORDER[actors[aid]["layout"]["anchor"]], ids.index(aid)))


def _physical_arrange(ids, box, flow, actors, relations, focus, gap, aspect, constraints):
    from .contracts import SPATIAL_RELATIONS
    physical = [r for r in relations if r["kind"] in SPATIAL_RELATIONS
                and r["from"] in ids and r["to"] in ids]
    if not physical:
        return None
    neighbours: dict[str, set[str]] = {aid: set() for aid in ids}
    for relation in physical:
        neighbours[relation["from"]].add(relation["to"])
        neighbours[relation["to"]].add(relation["from"])
    components, visited = [], set()
    for aid in ids:
        if aid in visited:
            continue
        pending, members = [aid], []
        while pending:
            member = pending.pop(0)
            if member in visited:
                continue
            visited.add(member)
            members.append(member)
            pending.extend(other for other in ids if other in neighbours[member] and other not in visited)
        components.append(members)
    native = "row" if aspect == "16:9" else "column" if aspect == "9:16" else "compact"
    representatives = [members[0] for members in components]
    weights = {members[0]: sum(_weight(actors[aid], focus) for aid in members) for members in components}
    cells = _split(representatives, box, native if flow == "auto" else flow,
                   actors, focus, gap, weights)
    out = {}
    for members in components:
        if len(members) == 1:
            out[members[0]] = cells[members[0]]
            continue
        levels = {}
        for axis in ("x", "y"):
            graph: dict[str, set[str]] = {aid: set() for aid in members}
            for relation in physical:
                direction, reverse = SPATIAL_RELATIONS[relation["kind"]]
                if direction != axis or relation["from"] not in graph:
                    continue
                first, second = ((relation["to"], relation["from"]) if reverse
                                 else (relation["from"], relation["to"]))
                graph[second].add(first)
            ranks: dict[str, int] = {}
            while len(ranks) < len(members):
                ready = [aid for aid in members if aid not in ranks and graph[aid] <= ranks.keys()]
                if not ready:
                    _error("contradictory physical ordering", "$.scenes.relations")
                for aid in ready:
                    ranks[aid] = max((ranks[other] + 1 for other in graph[aid]), default=0)
            levels[axis] = ranks
        cell = cells[members[0]]
        columns, rows = max(levels["x"].values()) + 1, max(levels["y"].values()) + 1
        width = (cell["width"] - gap * (columns - 1)) / columns
        height = (cell["height"] - gap * (rows - 1)) / rows
        if min(width, height) <= 0:
            _error("physical ordering cannot fit readable native cells", "$.scenes.relations")
        buckets: dict[tuple[int, int], list[str]] = {}
        for aid in members:
            buckets.setdefault((levels["x"][aid], levels["y"][aid]), []).append(aid)
        for (column, row), occupants in buckets.items():
            rectangle = _rect(cell["x"] + column * (width + gap),
                              cell["y"] + row * (height + gap), width, height)
            out.update(_split(occupants, rectangle, native, actors, focus, gap / 2))
    constraints.append("physical axes preserved independently of causal/process flow")
    return out


def _arrange(ids, box, flow, actors, relations, focus, gap, aspect, constraints):
    ids = _ordered(ids, actors)
    if len(ids) <= 1:
        return _split(ids, box, "row", actors, focus, gap)
    physical = _physical_arrange(ids, box, flow, actors, relations, focus, gap, aspect, constraints)
    if physical is not None:
        return physical
    graph: dict[str, set[str]] = {aid: set() for aid in ids}
    for relation in relations:
        if relation["kind"] in _DIRECTIONAL and relation["from"] in graph and relation["to"] in graph:
            graph[relation["to"]].add(relation["from"])
    for aid in ids:
        other = actors[aid]["layout"].get("relative_to")
        if other in graph:
            graph[aid].add(other)
    remaining, semantic_order = set(ids), []
    levels: dict[str, int] = {}
    while remaining:
        ready = [aid for aid in ids if aid in remaining and graph[aid] <= set(levels)]
        if not ready:
            break
        for aid in ready:
            levels[aid] = max((levels[p] + 1 for p in graph[aid]), default=0)
            remaining.remove(aid)
            semantic_order.append(aid)
    if not remaining:
        ids = semantic_order
    elif flow not in ("auto", "radial"):
        _error("cyclic semantic relationships conflict with linear arrangement", "$.scenes.composition")
    if flow == "plot":
        # Axis is a shared semantic scaffold, not a per-value dashboard widget.
        axes = [aid for aid in ids if actors[aid]["kind"] == "axis"]
        marks = [aid for aid in ids if aid not in axes]
        if not axes or not marks:
            _error("plot arrangement requires addressable axis and marks", "$.scenes.composition")
        axis_space = min(box["width"], box["height"]) * .16
        if aspect == "9:16":
            axis_box = _rect(box["x"], box["y"], axis_space, box["height"])
            mark_box = _rect(box["x"] + axis_space + gap, box["y"],
                             box["width"] - axis_space - gap, box["height"])
            marks_flow = "column"
        else:
            axis_box = _rect(box["x"], box["y"] + box["height"] - axis_space, box["width"], axis_space)
            mark_box = _rect(box["x"], box["y"], box["width"], box["height"] - axis_space - gap)
            marks_flow = "row"
        constraints.append("plot: axis scaffold and independently addressable marks")
        return {**_split(axes, axis_box, marks_flow, actors, focus, gap),
                **_split(marks, mark_box, marks_flow, actors, focus, gap)}
    hints = {actors[aid]["layout"].get("arrangement", "auto") for aid in ids
             if actors[aid]["kind"] != "group"}
    hints.discard("auto")
    if flow == "auto" and hints:
        if len(hints) != 1:
            _error("conflicting actor arrangement constraints; use explicit groups", "$.scenes.actors.layout")
        flow = next(iter(hints))
        constraints.append("actor arrangement hint:" + flow)
        if flow == "plot":
            return _arrange(ids, box, flow, actors, relations, focus, gap, aspect, constraints)
    if remaining and flow not in ("auto", "radial"):
        _error("cyclic semantic relationships conflict with actor arrangement hint", "$.scenes.actors.layout")
    if flow != "auto":
        constraints.append("authored arrangement:" + flow)
        return _split(ids, box, flow, actors, focus, gap)
    # Feedback is represented as a cycle, never arbitrarily broken into a DAG.
    if remaining:
        constraints.append("cyclic semantic graph: radial feedback arrangement")
        return _split(ids, box, "radial", actors, focus, gap)
    native = "row" if aspect == "16:9" else "column" if aspect == "9:16" else "compact"
    if max(levels.values()) > 0:
        bands = [[aid for aid in ids if levels[aid] == rank] for rank in range(max(levels.values()) + 1)]
        # Square keeps graph order, but uses alternating compact bands instead
        # of a portrait/landscape strip disguised by scale.
        lane_flow = "row" if aspect == "16:9" else "column"
        representatives = [band[0] for band in bands]
        cells = _split(representatives, box, lane_flow, actors, focus, gap)
        out = {}
        for band in bands:
            across = "column" if lane_flow == "row" else "row"
            out.update(_split(band, cells[band[0]], across, actors, focus, gap))
        constraints.append("graph layers:" + ";".join(",".join(band) for band in bands) + "; native=" + lane_flow)
        return out
    # Nondirectional relations constrain proximity, not invented process order.
    # Pack connected components as constructs before allocating isolated actors.
    neighbours: dict[str, set[str]] = {aid: set() for aid in ids}
    for relation in relations:
        if relation["from"] in neighbours and relation["to"] in neighbours:
            neighbours[relation["from"]].add(relation["to"])
            neighbours[relation["to"]].add(relation["from"])
    components, visited = [], set()
    for root in ids:
        if root in visited:
            continue
        pending, members = [root], []
        while pending:
            aid = pending.pop(0)
            if aid in visited:
                continue
            visited.add(aid)
            members.append(aid)
            pending.extend(other for other in ids if other in neighbours[aid] and other not in visited)
        components.append(members)
    if len(components) > 1 and any(len(members) > 1 for members in components):
        representatives = [members[0] for members in components]
        cells = _split(representatives, box, native, actors, focus, gap)
        out = {}
        for members in components:
            out.update(_split(members, cells[members[0]], native, actors, focus, gap / 2))
        constraints.append("relationship proximity components:" + ";".join(",".join(members) for members in components))
        return out
    constraints.append("native independent/comparison arrangement:" + native)
    return _split(ids, box, native, actors, focus, gap)


def _glyph_width(character):
    # A conservative portable upper bound, intentionally not an invented
    # browser measurement. Exact encoded-media readability remains review work.
    if unicodedata.combining(character):
        return 0
    if unicodedata.east_asian_width(character) in ("W", "F"):
        return 1.1
    if character.isspace():
        return .36
    if character in "ilI.,:;!'|`":
        return .4
    if character in "MW@%&":
        return 1.05
    return .8 if character.isupper() else .7


def _width(text, size):
    return sum(_glyph_width(c) for c in text) * size


def _wrap(text, size, width):
    lines = []
    for paragraph in text.splitlines() or [text]:
        current = ""
        for word in paragraph.split():
            if _width(word, size) > width:
                if current:
                    lines.append(current)
                    current = ""
                chunk = ""
                for char in word:
                    if chunk and _width(chunk + char, size) > width:
                        lines.append(chunk)
                        chunk = ""
                    chunk += char
                current = chunk
            elif current and _width(current + " " + word, size) > width:
                lines.append(current)
                current = word
            else:
                current = (current + " " + word).strip()
        if current:
            lines.append(current)
    return lines


def _number_text(value, payload, path):
    decimals = payload.get("decimals", 0)
    formatted = f"{value:.{decimals}f}"
    if Decimal(formatted) != Decimal(str(value)):
        _error("number decimals would round away evidence; declare sufficient precision", path)
    unit = payload["unit"]
    return formatted + ("" if unit == "1" else "%" if unit == "%" else " " + unit)


def _texts(actor, events):
    texts = [actor["label"]]
    kind = actor["kind"]
    if kind == "text":
        texts += [actor["payload"]["text"], actor["initial"]["text"]]
        texts += [event["changes"][actor["id"]]["text"] for event in events
                  if "text" in event["changes"].get(actor["id"], {})]
    elif kind == "number":
        values = [actor["initial"]["value"]]
        values += [event["changes"][actor["id"]]["value"] for event in events
                   if "value" in event["changes"].get(actor["id"], {})]
        texts += [_number_text(value, actor["payload"], "$.actors." + actor["id"] + ".payload.decimals") for value in values]
    elif kind == "selector":
        texts += actor["payload"]["options"]
    elif kind in ("bar", "axis"):
        texts += [str(value) + " " + actor["payload"]["unit"] for value in actor["payload"]["domain"]]
    return texts


def _fit(actor, geometry, events, typography, constraints):
    kind = actor["kind"]
    purpose = actor["payload"].get("purpose", "label")
    desired = (typography["headline_size"] if kind == "number" or purpose in ("headline", "conclusion")
               else typography["body_size"] if kind == "text" and purpose in ("annotation", "caption")
               else typography["label_size"])
    minimum = min(desired, 24 if kind == "number" or purpose in ("headline", "conclusion") else 20)
    # Primitive labels share fitting metrics, without making a text card actor.
    max_lines = actor["payload"].get("max_lines", 3 if kind != "text" else 6)
    width = geometry["width"] - 24
    height = geometry["height"] - 24
    texts = _texts(actor, events)
    if kind == "number":
        # Label plus a truthful unsplit value readout must coexist.
        max_lines = 3
    fitted = None
    for size in range(math.floor(desired), math.ceil(minimum) - 1, -1):
        wrapped = [_wrap(text, size, width) for text in texts]
        if width <= 0 or height <= 0:
            break
        all_fit = all(lines and len(lines) <= max_lines and len(lines) * size * 1.24 <= height
                      and all(_width(line, size) <= width for line in lines) for lines in wrapped)
        if kind == "number":
            all_fit &= all(_width(text, size) <= width for text in texts[1:])
            all_fit &= (len(wrapped[0]) + 1) * size * 1.24 <= height
        if kind == "selector":
            # Options are addressable rows/cells, not a forced single column.
            # Test conservative native grids as well as the aggregate label.
            option_fit = False
            options = actor["payload"]["options"]
            for columns in range(1, min(8, len(options)) + 1):
                rows = math.ceil(len(options) / columns)
                cell_width = geometry["width"] / columns - 24
                cell_height = geometry["height"] / rows - 12
                lines = [_wrap(text, size, cell_width) for text in options]
                if all(items and len(items) <= 2 and len(items) * size * 1.24 <= cell_height
                       and all(_width(line, size) <= cell_width for line in items) for items in lines):
                    option_fit = True
                    break
            all_fit &= option_fit
        if all_fit:
            fitted = size
            break
    if fitted is None:
        _error("readable text/label constraint cannot fit all states for " + actor["id"], "$.scenes.actors.geometry")
    initial_text = (actor["initial"]["text"] if kind == "text" else
                    _number_text(actor["initial"]["value"], actor["payload"], "$.actors.payload") if kind == "number"
                    else actor["label"])
    geometry.update(font_size=fitted, line_height=round(fitted * 1.24, 6),
                    lines=_wrap(initial_text, fitted, width))
    constraints.append(f"fit:{actor['id']}:all {len(texts)} label/state strings; size={fitted}; portable conservative metrics")


def _edge(box, other):
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    dx = other["x"] + other["width"] / 2 - cx
    dy = other["y"] + other["height"] / 2 - cy
    if dx == dy == 0:
        _error("connector endpoints have coincident centers", "$.scenes.actors.geometry")
    factor = min(box["width"] / (2 * abs(dx)) if dx else math.inf,
                 box["height"] / (2 * abs(dy)) if dy else math.inf)
    return {"x": cx + dx * factor, "y": cy + dy * factor}


def _anchors(geometry, canvas, safe, aspect, background=False):
    x, y, width, height = (geometry[key] for key in ("x", "y", "width", "height"))
    if background:
        # Full-bleed artwork has no free safe-band space. Semantic movement
        # therefore uses intentional canvas-clipped offsets, not five identical
        # anchors that silently erase an authored background move.
        dx, dy = (width * .12, 0) if aspect == "16:9" else (0, height * .12)
        return {"home": {"x": x, "y": y}, "focus": {"x": x, "y": y},
                "context": {"x": round(x + width * .08, 6), "y": round(y + height * .08, 6)},
                "start": {"x": round(x - dx, 6), "y": round(y - dy, 6)},
                "end": {"x": round(x + dx, 6), "y": round(y + dy, 6)}}
    left, top = safe["x"], safe["y"]
    right = safe["x"] + safe["width"] - width
    bottom = safe["y"] + safe["height"] - height
    # Background slots are full bleed; all anchors remain full-bleed compatible.
    if width > safe["width"] or height > safe["height"]:
        left, top, right, bottom = 0, 0, canvas[0] - width, canvas[1] - height
    center = {"x": round((left + right) / 2, 6), "y": round((top + bottom) / 2, 6)}
    return {"home": {"x": x, "y": y}, "focus": center,
            "context": {"x": round(right, 6), "y": round(bottom, 6)},
            "start": {"x": round(left, 6), "y": center["y"] if aspect == "16:9" else round(top, 6)},
            "end": {"x": round(right, 6), "y": center["y"] if aspect == "16:9" else round(bottom, 6)}}


def _compose(scene, aspect, style):
    canvas = ASPECTS[aspect]
    width, height = canvas
    margin = min(canvas) * .055
    safe = _rect(margin, margin, width - 2 * margin, height - 2 * margin)
    composition = deepcopy(scene.get("composition", {"flow": "auto", "density": "balanced"}))
    focus = composition.get("focus")
    gap = min(canvas) * {"open": .045, "balanced": .03, "dense": .018}[composition["density"]]
    actors = {actor["id"]: actor for actor in scene["actors"]}
    constraints = [f"native:{aspect}:{width}x{height}; safe_margin={margin}",
                   "hierarchy:semantic anchors/rank/focus; no narration template selection"]
    parent = {}
    children: dict[str, list[str]] = {aid: [] for aid in actors}
    for actor in actors.values():
        if actor["kind"] == "group":
            for child in actor["payload"]["children"]:
                parent[child] = actor["id"]
                children[actor["id"]].append(child)
    for relation in scene["relations"]:
        constraints.append(f"relation:{relation['id']}:{relation['kind']}:{relation['from']}->{relation['to']}")
        if relation["kind"] == "contains":
            outer, inner = relation["from"], relation["to"]
            if inner in parent and parent[inner] != outer:
                _error("containment conflicts with explicit group parent", "$.scenes.relations")
            if inner not in parent:
                parent[inner] = outer
                children[outer].append(inner)
    # Reject impossible containment before entering the hierarchical solver.
    for aid in actors:
        seen, current = set(), aid
        while current in parent:
            if current in seen:
                _error("cyclic containment has no finite native geometry", "$.scenes.relations")
            seen.add(current)
            current = parent[current]
    attached = {aid for aid, actor in actors.items()
                if actor["kind"] == "connector" or actor["kind"] == "particles" and "path" in actor["payload"]}
    background = [aid for aid in actors if actors[aid]["layout"]["anchor"] == "background" and aid not in parent and aid not in attached]
    captions = [aid for aid in actors if actors[aid]["layout"]["anchor"] == "caption" and aid not in parent and aid not in attached]
    roots = [aid for aid in actors if aid not in parent and aid not in background + captions
             and aid not in attached]
    slots = {aid: _rect(0, 0, width, height) for aid in background}
    content = deepcopy(safe)
    if captions:
        caption_height = min(safe["height"] * .3, max(style["typography"]["body_size"] * 4, height * .12))
        caption_box = _rect(safe["x"], safe["y"] + safe["height"] - caption_height, safe["width"], caption_height)
        slots.update(_split(captions, caption_box, "column", actors, focus, gap / 2))
        content["height"] -= caption_height + gap
        constraints.append("caption safe band reserved only for authored caption actors")
    # Lift edges through explicit groups/containment: relationships between
    # children still constrain their root constructs and each nested graph.
    def sibling_edges(ids):
        members = set(ids)
        def lift(aid):
            while aid not in members and aid in parent:
                aid = parent[aid]
            return aid if aid in members else None
        edges = []
        for relation in scene["relations"]:
            left, right = lift(relation["from"]), lift(relation["to"])
            if left and right and left != right:
                edges.append({**relation, "from": left, "to": right})
        # Nondirectional components stay adjacent without changing their meaning
        # into causality/process constraints.
        adjacent: dict[str, set[str]] = {aid: set() for aid in ids}
        for edge in edges:
            adjacent[edge["from"]].add(edge["to"])
            adjacent[edge["to"]].add(edge["from"])
        ordered, visited = [], set()
        for root in _ordered(ids, actors):
            pending = [root]
            while pending:
                aid = pending.pop(0)
                if aid in visited:
                    continue
                visited.add(aid)
                ordered.append(aid)
                pending.extend(other for other in ids if other in adjacent[aid] and other not in visited)
        return ordered, edges
    if roots:
        ordered, edges = sibling_edges(roots)
        slots.update(_arrange(ordered, content, composition["flow"], actors, edges, focus, gap, aspect, constraints))
    pending = list(background + roots + captions)
    while pending:
        aid = pending.pop(0)
        nested = [child for child in children[aid] if child not in attached]
        if not nested:
            continue
        slot = slots[aid]
        inset = min(slot["width"], slot["height"]) * (.18 if actors[aid]["kind"] == "shape" else .08)
        inner = _inset(slot, max(18, inset))
        flow = actors[aid]["layout"].get("arrangement", "auto")
        ordered, edges = sibling_edges(nested)
        slots.update(_arrange(ordered, inner, flow, actors, edges, focus, gap / 2, aspect, constraints))
        pending.extend(nested)
        constraints.append("containment:" + aid + ":" + ",".join(nested) + "; absolute child coordinates")
    geometry = {}
    payloads = {}
    for actor in actors.values():
        aid, kind = actor["id"], actor["kind"]
        payload = deepcopy(actor["payload"])
        if aid in attached:
            payloads[aid] = payload
            continue
        if aid not in slots:
            _error("actor has no solvable semantic slot: " + aid, "$.scenes.actors.layout")
        box = deepcopy(slots[aid])
        if kind in ("bar", "axis"):
            if payload.get("orientation", "auto") == "auto":
                payload["orientation"] = "vertical" if aspect == "9:16" else "horizontal"
            if kind == "bar" and not children[aid]:
                if payload["orientation"] == "horizontal":
                    thickness = min(160, box["height"] * .55)
                    box = _rect(box["x"], box["y"] + (box["height"] - thickness) / 2, box["width"], thickness)
                else:
                    thickness = min(180, box["width"] * .55)
                    box = _rect(box["x"] + (box["width"] - thickness) / 2, box["y"], thickness, box["height"])
            if kind == "axis":
                box["points"] = ([{"x": 12, "y": box["height"] / 2}, {"x": box["width"] - 12, "y": box["height"] / 2}]
                                 if payload["orientation"] == "horizontal" else
                                 [{"x": box["width"] / 2, "y": box["height"] - 12}, {"x": box["width"] / 2, "y": 12}])
            constraints.append("orientation:" + aid + ":" + payload["orientation"] + "; explicit unit/domain")
        if kind == "shape" and not children[aid] and aid not in background:
            if "aspect_ratio" in payload:
                ratio = payload["aspect_ratio"]
                height = min(box["height"], box["width"] / ratio) * .85
                width = height * ratio
                box = _rect(box["x"] + (box["width"] - width) / 2,
                            box["y"] + (box["height"] - height) / 2, width, height)
            elif payload["shape"] == "rect":
                box = _inset(box, min(box["width"], box["height"]) * .075)
            else:
                size = min(box["width"], box["height"]) * .85
                box = _rect(box["x"] + (box["width"] - size) / 2, box["y"] + (box["height"] - size) / 2, size, size)
            angles = [actor["initial"].get("rotation", 0)]
            angles.extend(e["changes"][aid]["rotation"] for e in scene["events"]
                          if aid in e["changes"] and "rotation" in e["changes"][aid])
            if any(angle != 0 for angle in angles):
                extent = math.hypot(box["width"], box["height"])
                factor = min(1, min(slots[aid]["width"], slots[aid]["height"]) * .85 / extent)
                width, height = box["width"] * factor, box["height"] * factor
                box = _rect(box["x"] + (box["width"] - width) / 2,
                            box["y"] + (box["height"] - height) / 2, width, height)
                constraints.append("rotation envelope fitted:" + aid)
        if kind in ("text", "number", "bar", "axis", "selector"):
            _fit(actor, box, scene["events"], style["typography"], constraints)
        geometry[aid], payloads[aid] = box, payload
    # Connectors can reference other connectors. Resolve graph order or fail
    # unsupported geometric cycles; never replace the connection by a card.
    unresolved = [aid for aid in actors if actors[aid]["kind"] == "connector"]
    while unresolved:
        ready = [aid for aid in unresolved if all(payloads[aid][key] in geometry for key in ("from", "to"))]
        if not ready:
            _error("cyclic connector geometry cannot resolve endpoints", "$.scenes.actors.payload")
        for aid in ready:
            payload = payloads[aid]
            left, right = geometry[payload["from"]], geometry[payload["to"]]
            start, end = _edge(left, right), _edge(right, left)
            points = [start, end]
            if payload.get("routing", "direct") == "elbow":
                if aspect == "9:16":
                    mid = (start["y"] + end["y"]) / 2
                    points = [start, {"x": start["x"], "y": mid}, {"x": end["x"], "y": mid}, end]
                else:
                    mid = (start["x"] + end["x"]) / 2
                    points = [start, {"x": mid, "y": start["y"]}, {"x": mid, "y": end["y"]}, end]
            x, y = min(p["x"] for p in points), min(p["y"] for p in points)
            # Nonzero bounds permit reveal/scale for an exactly straight line.
            box = _rect(x - 2, y - 2, max(p["x"] for p in points) - x + 4, max(p["y"] for p in points) - y + 4)
            box["points"] = [{"x": round(p["x"] - box["x"], 6), "y": round(p["y"] - box["y"], 6)} for p in points]
            geometry[aid] = box
            unresolved.remove(aid)
            constraints.append("connector:" + aid + ":boundary endpoints; local points; routing=" + payload.get("routing", "direct"))
    padding = max(4, style["strokes"]["width"] * 2)
    for aid in attached:
        if actors[aid]["kind"] != "particles":
            continue
        binding = payloads[aid]["path"]
        route = geometry[binding["connector"]]
        geometry[aid] = _rect(route["x"] - padding, route["y"] - padding,
                              route["width"] + 2 * padding, route["height"] + 2 * padding)
        constraints.append(f"material-path:{aid}:{binding['connector']}:{binding['direction']}; native route, no independent slot")
    for aid, box in geometry.items():
        box["anchors"] = _anchors(box, canvas, content, aspect, background=aid in background)
        if box["width"] <= 0 or box["height"] <= 0:
            _error("zero-area actor geometry", "$.scenes.actors.geometry")
    return geometry, payloads, composition, constraints


def _schedule(scene, alignment_scene, offset, constraints):
    events = {event["id"]: event for event in scene["events"]}
    intervals: dict[str, tuple[float, float]] = {}
    order = []
    while len(intervals) < len(events):
        ready = [event for event in scene["events"] if event["id"] not in intervals
                 and all(dep in intervals for dep in event["dependencies"])]
        if not ready:
            _error("event dependency cycle", "$.scenes.events.dependencies")
        for event in ready:
            cue = event["cue"]
            if cue["kind"] == "word":
                if alignment_scene is None:
                    _error("word cue requires actual reported alignment", "$.scenes.events.cue")
                cue_ms = resolve_word_cue(cue, alignment_scene)
                basis = "reported_word_edge"
            elif cue["kind"] == "fraction":
                cue_ms, basis = cue["fraction"] * scene["duration_ms"], "provisional_fraction"
            else:
                cue_ms, basis = cue["ms"], cue["basis"]
            start = max([cue_ms] + [intervals[dep][1] for dep in event["dependencies"]])
            end = start + event["duration_ms"]
            if end > scene["duration_ms"]:
                _error("dependency-resolved event exceeds scene duration", "$.scenes.events")
            intervals[event["id"]] = (start, end)
            order.append(event["id"])
            constraints.append(f"cue:{event['id']}:{basis}:scene_ms={cue_ms}; dependency_delay_ms={start - cue_ms}")
            for aid, binding in event.get("value_bindings", {}).items():
                constraints.append(f"value_binding:{event['id']}:{aid}={binding}")
    order_index = {eid: index for index, eid in enumerate(order)}
    order.sort(key=lambda eid: (intervals[eid][0], intervals[eid][1], order_index[eid]))
    compiled = []
    for eid in order:
        event = events[eid]
        compiled.append({**{key: deepcopy(event[key]) for key in
                           ("id", "verb", "targets", "dependencies", "claim_ids", "rationale")},
                         "start_ms": offset + intervals[eid][0], "end_ms": offset + intervals[eid][1]})
    return compiled


def _tracks(scene, events, actors):
    authored = {event["id"]: event for event in scene["events"]}
    states = {actor["id"]: deepcopy(actor["initial"]) for actor in actors}
    by_actor = {actor["id"]: actor for actor in actors}
    tracks = []
    for event in events:
        source = authored[event["id"]]
        for aid, changes in source["changes"].items():
            lowered = {}
            for prop, target in changes.items():
                if prop == "position":
                    lowered.update(by_actor[aid]["geometry"]["anchors"][target])
                else:
                    lowered[prop] = target
            for prop, target in lowered.items():
                track = {"event_id": event["id"], "actor_id": aid, "property": prop,
                         "from": deepcopy(states[aid][prop]), "to": deepcopy(target),
                         "start_ms": event["start_ms"], "end_ms": event["end_ms"],
                         "easing": "step" if prop in _DISCRETE else source["easing"],
                         **{key: deepcopy(event[key]) for key in ("verb", "rationale", "claim_ids")}}
                tracks.append(track)
                states[aid][prop] = deepcopy(target)
    return tracks


def compile_score(score, aspect, alignment=None):
    """Return a validated JSON plan, or ScoreError; never fabricate voice timing.

    Reported alignment may be supplied explicitly or already bound on the score.
    Durations must already equal reported audio duration (use bind_alignment for
    retiming). The canonical hash binds the validated score including alignment.
    All geometry and timing are deterministic and inputs are never mutated.
    """
    if not isinstance(aspect, str) or aspect not in ASPECTS:
        _error("unsupported native aspect", "$.aspect")
    candidate = deepcopy(score)
    if alignment is not None:
        if not isinstance(candidate, dict):
            _error("score must be an object", "$")
        if "alignment" in candidate and candidate["alignment"] != alignment:
            _error("explicit alignment conflicts with bound score alignment", "$.alignment")
        candidate["alignment"] = deepcopy(alignment)
    validated = validate_score(candidate)
    reported = validate_alignment(validated["alignment"], validated) if "alignment" in validated else None
    aligned_scenes = {item["scene_id"]: item for item in reported["scenes"]} if reported else {}
    for scene in validated["scenes"]:
        if reported and scene["duration_ms"] != aligned_scenes[scene["id"]]["duration_ms"]:
            _error("score duration differs from reported audio; bind_alignment before compilation", "$.scenes.duration_ms")
    score_hash = hashlib.sha256(json.dumps(validated, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False).encode("utf-8")).hexdigest()
    has_fraction = any(event["cue"]["kind"] == "fraction" for scene in validated["scenes"] for event in scene["events"])
    speech_only = reported and all(event["cue"]["kind"] == "word" or
                                  (event["cue"]["kind"] == "absolute" and event["cue"]["basis"] == "reported_alignment")
                                  for scene in validated["scenes"] for event in scene["events"])
    timing = ("provisional" if has_fraction else "aligned" if speech_only else
              "authored" if all(scene.get("timing", "provisional") in ("authored", "aligned")
                               for scene in validated["scenes"]) else "provisional")
    width, height = ASPECTS[aspect]
    plan = {"schema": PLAN_SCHEMA, "film_id": validated["film_id"], "title": validated["title"],
            "aspect": aspect, "canvas": {"width": width, "height": height},
            "output": {"fps": 30, "format": "mp4", "background": validated["style"]["palette"]["background"]},
            "duration_ms": sum(scene["duration_ms"] for scene in validated["scenes"]),
            "style": deepcopy(validated["style"]), "evidence": deepcopy(validated["evidence"]),
            "scenes": [], "provenance": deepcopy(validated["provenance"]),
            "direction": {"authority": "P8", "status": validated["provenance"]["status"],
                          "score_sha256": score_hash, "timing": timing}}
    if "meaning_graph" in validated:
        plan["meaning_graph"] = deepcopy(validated["meaning_graph"])
    seen, offset = set(), 0
    for scene in validated["scenes"]:
        geometry, payloads, composition, constraints = _compose(scene, aspect, validated["style"])
        if reported:
            source = reported["source"]
            constraints.append(f"alignment:{reported['id']}:{source['provider']}:{source['method']}; audio_sha256={source['audio_sha256']}")
        actors = []
        for actor in scene["actors"]:
            aid = actor["id"]
            initial = {key: deepcopy(value) for key, value in actor["initial"].items() if key != "position"}
            initial.update(geometry[aid]["anchors"][actor["initial"]["position"]])
            compiled = {**{key: deepcopy(actor[key]) for key in
                           ("id", "kind", "role", "label", "meaning", "evidence_ids", "layout")},
                        "identity": aid, "geometry": geometry[aid], "payload": payloads[aid],
                        "initial": initial, "retained": aid in seen}
            if "meaning_binding" in actor:
                compiled["meaning_binding"] = deepcopy(actor["meaning_binding"])
            if "value_binding" in actor:
                compiled["value_binding"] = actor["value_binding"]
            actors.append(compiled)
            seen.add(aid)
        events = _schedule(scene, aligned_scenes.get(scene["id"]), offset, constraints)
        end = offset + scene["duration_ms"]
        transition = {"kind": scene["transition"]["kind"],
                      "start_ms": end - scene["transition"]["duration_ms"], "end_ms": end}
        if "direction" in scene["transition"]:
            transition["direction"] = scene["transition"]["direction"]
        compiled_scene = {**{key: deepcopy(scene[key]) for key in
                             ("id", "section_id", "intent", "claim_ids", "narration", "relations")},
                          "start_ms": offset, "end_ms": end, "actors": actors, "events": events,
                          "tracks": _tracks(scene, events, actors), "transition": transition,
                          "composition": composition, "constraints": constraints}
        if "motif" in scene:
            compiled_scene["motif"] = scene["motif"]
        plan["scenes"].append(compiled_scene)
        offset = end
    # Frozen validator repeats evidence, overlap, retention, event and state
    # continuity checks on the executable boundary, not just authored syntax.
    return validate_plan(plan)
