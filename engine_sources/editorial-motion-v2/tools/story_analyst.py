#!/usr/bin/env python3
"""story_analyst.py — LLM story analyst for the reel pipeline.

Replaces the keyword-bank auto-treatment with a real editorial pass. The analyst
reads the script (plus its word alignment groups), authors the film's arc —
scene list, entity/metaphor inventory, motif — and emits beats inside the
NexStudioEditorialTreatmentV2 vocabulary. A deterministic conformer then rebuilds
every beat from the authored decisions against the VO's verbatim words, so the
treatment the compiler sees is always valid by construction — the LLM chooses,
it never hand-types the contract.

Provider-neutral: any OpenAI-compatible chat/completions endpoint. Config
follows the NEXMIND_* lane convention used by the rest of the studio:

  NEXMIND_STORY_ANALYST_MODEL          model name (required for live calls)
  NEXMIND_STORY_ANALYST_BASE_URL       default https://api.openai.com/v1
  NEXMIND_STORY_ANALYST_API_KEY_ENV    env var holding the key (default NEXMIND_API_KEY)
  NEXMIND_API_KEY / OPENAI_API_KEY     key value
  STORY_ANALYST_REPLAY                 path to a recorded analyst payload — replay it
                                       verbatim instead of calling a provider (tests,
                                       offline runs, debugging a bad output)

Modes (make_reel --analyst): keywords = legacy bank path; llm = analyst or fail;
auto = analyst when configured, keyword path otherwise.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(ROOT / "compiler"))

from editorial_plan_compiler import contracts as c  # noqa: E402


class AnalystUnavailable(RuntimeError):
    """No provider configured / provider unreachable."""


class AnalystInvalid(RuntimeError):
    """The model answered, but the payload could not be conformed."""


# ---------------------------------------------------------------- config

def _env(*names: str) -> str:
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    return ""


def analyst_config() -> Dict[str, Any]:
    return {
        "model": _env("NEXMIND_STORY_ANALYST_MODEL", "OPENAI_MODEL"),
        "base_url": (_env("NEXMIND_STORY_ANALYST_BASE_URL", "OPENAI_BASE_URL")
                     or "https://api.openai.com/v1").rstrip("/"),
        "key_env": _env("NEXMIND_STORY_ANALYST_API_KEY_ENV") or "NEXMIND_API_KEY",
        "replay": _env("STORY_ANALYST_REPLAY"),
        "timeout_s": float(_env("NEXMIND_STORY_ANALYST_TIMEOUT_S") or "120"),
    }


def _api_key(cfg: Dict[str, Any]) -> str:
    return _env(cfg["key_env"], "NEXMIND_API_KEY", "OPENAI_API_KEY")


def analyst_available() -> bool:
    cfg = analyst_config()
    if cfg["replay"]:
        return Path(cfg["replay"]).exists()
    return bool(cfg["model"] and _api_key(cfg))


def analyst_mode(args: Any) -> str:
    m = str(getattr(args, "analyst", "") or "").strip().lower()
    if not m:
        m = _env("STUDIO_ANALYST", "STUDIO_ANALYST_MODE") or "auto"
    return m if m in ("auto", "llm", "keywords") else "auto"


# ---------------------------------------------------------------- registries

def _registry_ids() -> set:
    """Every asset_ref the compiler can resolve — used to keep authored refs real."""
    ids = set()
    for p in [ROOT / "assets" / "illustration" / "registry.json",
              ROOT / "assets" / "community" / "icons-registry.json",
              ROOT / "assets" / "community" / "colour-registry.json"]:
        try:
            for a in json.loads(p.read_text())["assets"]:
                ids.add(a["id"])
        except Exception:
            continue
    return ids


# ---------------------------------------------------------------- prompt

PATTERN_HINTS = {
    "PROGRESSIVE_HERO_BUILD": "hero grows while supports arrive around it",
    "PHRASE_REPLACEMENT": "a hero phrase is swapped out mid-beat",
    "HERO_SCALE_PROMOTION": "a quiet element is promoted to hero",
    "HERO_TO_EVIDENCE_HANDOFF": "type makes the claim, media proves it",
    "EVIDENCE_PERSISTENCE_CARRIER": "an exhibit stays on stage while new beats land",
    "ANCHORED_SCREENSHOT_PROOF": "media pinned with callouts",
    "SEQUENTIAL_SUPPORT_LIST": "supports land one at a time",
    "QUIET_SUPPORT_AFTER_HERO": "understated tail after the claim",
    "CONTRAST_RECONFIGURATION": "two readings rearrange into the true one",
    "PROCESS_RAIL": "steps on a rail/pipeline",
    "WORD_OBJECT_BRIDGE": "a word becomes the object it names",
    "OBJECT_LED_TRANSITION": "an object carries the eye into the next beat",
    "PAYOFF_LOCKUP": "the final image/type locks up as the takeaway",
    "CTA_LOCKUP": "closing ask",
    "CONTROLLED_EMPTY_SPACE": "near-empty stage, one element carries the pause",
}

FORM_HINTS = {
    "OBJECT_STAGE": "objects staged on a field (1+ entities)",
    "PROCESS_PIPELINE": "ordered flow of steps (2+, needs a relation)",
    "RELATIONSHIP": "things linked/compared (2+, needs a relation)",
    "STATE_TRANSFORMATION": "A turns into B (needs a transforms_into relation)",
    "COMPARISON": "side by side (needs a compares relation)",
    "DATA_VISUAL": "a number drawn (needs CHART_LINE or BAR entity)",
    "CALLOUT_LENS": "a lens scans details (needs a LENS entity + a TRAVEL op)",
    "SIGNAL": "a pulse/emission (needs a RING entity)",
}

_OPS_LINE = ", ".join(c.OPS) + " (CONNECT/STRIKE/INK/DIM/TRACE/SETTLE may also target a declared relation as 'src->dst')"
_FORMS_LINE = "; ".join(f"{k} — {v}" for k, v in FORM_HINTS.items())
_PATTERNS_LINE = "; ".join(f"{k} — {v}" for k, v in PATTERN_HINTS.items())

SYSTEM_PROMPT = """You are the story analyst for NexStudio's editorial reel engine — a director
who turns a spoken script into a treatment of timed beats. You author decisions;
a deterministic compiler owns geometry, timing and rendering.

The engine draws kinetic type plus illustration entities (icons, paper tiles,
chips, media frames, charts). Every entity must carry visible content:
`asset_ref` (a real registry id — DO NOT invent ids; use `concept` instead),
`concept` (<=40 chars naming the depicted thing — resolved by the compiler to
the best icon / rights-clean photo / typeset word; this is the normal path and
the one to prefer for anything metaphorical), or an inside label on a CHIP.
Glyph rule: `concept` rides on TILE/BADGE/CHIP only (they can typeset a word);
bare ICON is only for a real `asset_ref`, so prefer TILE unless attaching media.

Rules:
- Group partition: `groups` are indices into the clause list; every clause index
  must be covered exactly once, in order. Merge adjacent clauses into one beat
  when the thought spans them; never reorder.
- Narration is rebuilt verbatim from the groups — never write narration text.
- display_units.text must be verbatim words from the beat's clauses (a phrase
  slice). Max 5 units, at most 3 heroes. stress/mute words must appear in the
  unit text. anchor_word must be a word in the narration (or omit it).
- Give most beats an illustration (the film needs >=60% visual density) and
  prefer `concept`-carrying entities over empty housings. Max 7 entities,
  at most 2 heroes. Labels: <=3 words, no leading article, never repeating a
  display unit's text.
- program ops: target an entity id, or `src->dst` for a declared relation with
  CONNECT-family ops (CONNECT STRIKE INK DIM TRACE SETTLE). `at` is exactly one
  of {"word": <word from the beat's narration>}, {"unit": <display-unit index>},
  {"offset_ms": <int>}. duration_ms 120..4000. At least one op, at most ten.
- TRAVEL needs params.over = [entity ids]. COUNT takes params.count 1..12.
- beat_type arc: open with HOOK, build with SETUP/EXPLANATION/CONTRAST/PROOF/
  REFRAME/EMPHASIS/LIST, land on PAYOFF or CTA. Vary `pattern` — a film where
  every beat uses the same pattern reads as templated.
- `figure` (a still person) only on beats about a human state; requires
  justification. `data` only when the narration cites a number. `media`
  references only ids from the supplied media_library, when present.
- Performer option: if the script suits a recurring character, declare it in
  `cast` (id -> {posture, head?, face?, skin?}) and set `figure.character` to
  that id — the figure then keeps ONE identity across beats while its face
  still tracks the beat's emotion. With a cast member you may also add:
  `track` {enter: left|right|none, exit: left|right|none} (it walks on/off the
  stage between scenes), `prop` {concept, hand: left|right|auto} (a thing it
  holds — e.g. a magnifier, a gift box), and `states` (<=3) each {at: {word|
  offset_ms}, pose?, face?, head?} to morph its body/expression mid-beat.
  `pose`/`face` at figure level pin exact part ids when you know them.
- Author the arc, not just the beats: `film.motif` is ONE recurring visual idea
  (e.g. a question mark, a seed that grows) that pays off at the end; `scenes`
  group beats into authored moments with a setting and a visual_metaphor each;
  `entities` is the metaphor inventory — concept -> what it stands for.
- Author the film's WORLD, not just its beats: `film.brand` is the palette you
  choose for THIS script's register — ink/paper/accent hex colours and finish
  (EDITORIAL_FLAT | PAPER | PRODUCT_COLLAGE) — plus `film.world`: `grain`
  picks the overlay texture and `motif` {concept, corner} stamps the film's
  signature mark in a corner of every beat (the thread the viewer follows
  between scenes). A film that looks like every other film is a failure.
- `mood` picks the music bed; choose from the enum.

Output: one JSON object only."""


def _user_payload(script: str, groups: List[List[Dict[str, Any]]], style: Dict[str, Any],
                  media_ids: List[str], registry_ids: set) -> Dict[str, Any]:
    return {
        "script": script,
        "voice_duration_ms": groups[-1][-1]["end_ms"] if groups else 0,
        "clauses": [{"index": i,
                     "text": " ".join(w["text"] for w in g).strip(),
                     "start_ms": g[0]["start_ms"], "end_ms": g[-1]["end_ms"],
                     "words": [w["text"].strip() for w in g]} for i, g in enumerate(groups)],
        "style": {"id": style["id"], "finish": style.get("finish"), "palette": style.get("palette")},
        "media_library": media_ids,
        "vocabulary": {
            "beat_types": list(c.BEAT_TYPES),
            "patterns": PATTERN_HINTS,
            "dominant_layers": list(c.DOMINANT_LAYERS),
            "forms": FORM_HINTS,
            "entity_kinds": list(c.ENTITY_KINDS), "glyphs": list(c.GLYPHS),
            "entity_sizes": list(c.ENTITY_SIZES),
            "relation_types": list(c.RELATION_TYPES), "relation_styles": list(c.RELATION_STYLES),
            "ops": c.OPS, "op_defaults_ms": c.OP_DEFAULT_MS,
            "unit_roles": list(c.UNIT_ROLES), "semantic_roles": list(c.SEMANTIC_ROLES),
            "reveal_modes": list(c.REVEAL_MODES), "media_roles": list(c.MEDIA_ROLES),
            "data_kinds": list(c.DATA_KINDS), "figure_postures": list(c.FIGURE_POSTURES),
            "figure_facings": list(c.FIGURE_FACINGS), "moods": list(c.FILM_MOODS),
            "concept_glyphs": list(c.CONCEPT_GLYPHS),
            "figure_track_sides": list(c.FIGURE_TRACK_SIDES), "figure_hands": list(c.FIGURE_HANDS),
            "world_grains": list(c.WORLD_GRAINS), "world_corners": list(c.WORLD_CORNERS),
            "finishes": list(c.FINISHES),
        },
        "registry_asset_count": len(registry_ids),
        "output_contract": {
            "film": {"thesis": "str", "motif": "str <=40 chars", "mood": "one of moods", "note": "str",
                      "brand": {"ink": "#hex", "paper": "#hex", "accent": "#hex|null",
                                "finish": "EDITORIAL_FLAT|PAPER|PRODUCT_COLLAGE"},
                      "world": {"grain": "enum", "motif": {"concept": "str<=40", "corner": "enum"}}},
            "cast": {"character_id": {"posture": "enum", "head": "part id|null",
                                       "face": "part id|null", "skin": "tone|null"}},
            "scenes": [{"name": "str", "covers": ["beat index 1-based"], "setting": "str",
                        "visual_metaphor": "str"}],
            "beats": [{"groups": [0], "beat_type": "enum", "pattern": "enum",
                        "dominant_layer": "enum", "energy": 0.0, "complexity": 0.0,
                        "display_units": [{"text": "verbatim phrase", "role": "enum",
                                            "semantic_role": "enum", "emphasis": 0.0,
                                            "stress": ["word"], "anchor_word": "word"}],
                        "figure": {"valence": -1.0, "arousal": 0.0, "posture": "enum",
                                    "energy": 0.0, "formality": 0.0, "facing": "enum",
                                    "justification": "str", "character": "cast id|null",
                                    "track": {"enter": "enum", "exit": "enum"},
                                    "prop": {"concept": "str<=40", "hand": "enum"},
                                    "states": [{"at": {"word": "w"} | {"offset_ms": 0},
                                               "pose": "id|null", "face": "id|null"}],
                                    "pose": "id|null", "face": "id|null"} ,
                        "data": {"kind": "enum", "value": "str", "label": "str"},
                        "media": {"asset_id": "from media_library", "role": "enum"},
                        "illustration": {"form": "enum",
                                          "entities": [{"id": "str", "kind": "enum", "glyph": "enum",
                                                         "size": "enum", "label": "str|null",
                                                         "concept": "str<=40", "asset_ref": "registry id|null",
                                                         "media_ref": "media id|null"}],
                                          "relations": [{"type": "enum", "source": "id", "target": "id",
                                                          "style": "link|dash|arc"}],
                                          "program": [{"op": "enum", "target": "id or a->b",
                                                        "at": {"word": "narration word"},
                                                        "duration_ms": 500}]},
                        "metaphor": "one line — the visual argument"}],
            "entities": [{"concept": "str", "as": "what it stands for", "introduced": "b05"}],
        },
    }


# ---------------------------------------------------------------- provider

def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def call_analyst(payload: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return the analyst payload — live provider, or replay file when set."""
    cfg = cfg or analyst_config()
    if cfg["replay"]:
        p = Path(cfg["replay"])
        if not p.exists():
            raise AnalystUnavailable(f"STORY_ANALYST_REPLAY not found: {p}")
        doc = json.loads(p.read_text())
        # a fixture may wrap the analyst payload next to its script
        if isinstance(doc, dict) and isinstance(doc.get("payload"), dict):
            return doc["payload"]
        return doc
    if not cfg["model"]:
        raise AnalystUnavailable("NEXMIND_STORY_ANALYST_MODEL not set")
    key = _api_key(cfg)
    if not key:
        raise AnalystUnavailable(f"no API key in ${cfg['key_env']} (or NEXMIND_API_KEY/OPENAI_API_KEY)")
    body = json.dumps({
        "model": cfg["model"],
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
    }).encode()
    req = urllib.request.Request(
        f"{cfg['base_url']}/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout_s"]) as r:
            doc = json.loads(r.read().decode())
    except Exception as e:
        raise AnalystUnavailable(f"provider call failed: {e}") from e
    try:
        return _extract_json(doc["choices"][0]["message"]["content"])
    except Exception as e:
        raise AnalystInvalid(f"provider returned unparseable content: {e}") from e


# ---------------------------------------------------------------- conformer

def _norm_seq(text: str) -> List[str]:
    return c._norm_words(text)


def _enum(v: Any, allowed, default):
    s = str(v or "").strip()
    for cand in (s, s.upper(), s.lower()):
        if cand in allowed:
            return cand
    return default


def _clamp(v: Any, lo: float = 0.0, hi: float = 1.0, default: float = 0.5) -> float:
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return default


def _titleish_id(raw: Any, fallback: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", str(raw or "").strip()).strip("_")
    return s or fallback


# Glyphs with a designed inside-label box (mirrors illustration.LABEL_CARRIERS);
# labels on anything else render 'below' across layout cells the conformer can't
# predict — the gate flags them, so non-carriers keep the concept's typeset word
# instead.
LABEL_CARRIER_GLYPHS = ("PILL", "CARD", "CALLOUT", "STICKY", "CHIP")
LABEL_MAX_CHARS = 14
LABEL_MAX_WORD_CHARS = 9


def _strip_article(label: str) -> str:
    words = label.split()
    while words and words[0].lower() in c.LABEL_ARTICLES:
        words = words[1:]
    return " ".join(words)


def _fix_label(raw: Any, unit_word_sets: List[list], glyph: str) -> Optional[str]:
    label = _strip_article(" ".join(str(raw or "").split()))
    if not label:
        return None
    words = _norm_seq(label)
    if len(words) > c.LABEL_MAX_WORDS:
        label = " ".join(label.split()[: c.LABEL_MAX_WORDS])
        words = _norm_seq(label)
    for uw in unit_word_sets:
        if words == uw or (len(words) >= 2 and any(uw[i:i + len(words)] == words
                                                   for i in range(len(uw) - len(words) + 1))):
            return None
    if glyph not in LABEL_CARRIER_GLYPHS:
        return None
    if len(label) > LABEL_MAX_CHARS or len(words) > 2 or any(len(w) > LABEL_MAX_WORD_CHARS for w in words):
        return None
    return label or None


def _conform_entity(raw: Dict[str, Any], taken: set, unit_word_sets: List[list],
                    media_ids: set, registry_ids: set) -> Optional[Dict[str, Any]]:
    eid = _titleish_id(raw.get("id"), f"e{len(taken) + 1}")
    while eid in taken:
        stem = re.sub(r"_\d+$", "", eid)
        n = 2
        while f"{stem}_{n}" in taken:
            n += 1
        eid = f"{stem}_{n}"
    kind = _enum(raw.get("kind"), c.ENTITY_KINDS, "object")
    glyph = _enum(raw.get("glyph"), c.GLYPHS, "TILE")
    size = _enum(raw.get("size"), c.ENTITY_SIZES, "support")
    label = _fix_label(raw.get("label"), unit_word_sets, glyph)
    concept = " ".join(str(raw.get("concept") or "").split()) or None
    asset_ref = str(raw.get("asset_ref") or "").strip() or None
    if asset_ref and asset_ref not in registry_ids:
        asset_ref = None
    if concept:
        if len(concept) > 40:
            concept = " ".join(concept.split())[:40].rsplit(" ", 1)[0] or concept[:40]
        if glyph not in c.CONCEPT_GLYPHS:
            glyph = "ICON"  # concept resolves onto ICON/TILE/BADGE/CHIP only
    media_ref = str(raw.get("media_ref") or "").strip() or None
    if media_ref and media_ref not in media_ids:
        media_ref = None
    params = dict(raw.get("params") or {}) if isinstance(raw.get("params"), dict) else {}
    if "chassis" in params and glyph != "MEDIA":
        params.pop("chassis")
    if glyph == "MEDIA" and "chassis" in params and str(params["chassis"]) not in c.CHASSIS:
        params.pop("chassis")
    if "level" in params:
        params["level"] = _clamp(params["level"], 0.0, 1.0)
    if "count" in params:
        try:
            params["count"] = max(1, min(12, int(params["count"]))) if glyph == "NODE" else max(1, int(params["count"]))
        except (TypeError, ValueError):
            params.pop("count")
    if "lines" in params:
        try:
            params["lines"] = max(0, min(4, int(params["lines"])))
        except (TypeError, ValueError):
            params.pop("lines")
    if "tone" in params and str(params["tone"]) not in ("light", "dark"):
        params.pop("tone")
    # glyph-specific hard requirements
    if glyph == "MEDIA" and not media_ref:
        glyph = "TILE"
    if glyph == "ICON" and not asset_ref and not concept:
        concept = label or eid.replace("_", " ")
    if glyph == "ICON" and not asset_ref:
        # a bare ICON must resolve to a real registry mark or the compile gate
        # fails CONCEPT_UNRESOLVED — ICONs cannot typeset. A TILE runs the same
        # concept ladder (named mark -> CC0 photo -> typeset word) and always lands.
        glyph = "TILE"
    if glyph == "CHART_LINE":
        pts = params.get("points")
        if not (isinstance(pts, list) and len(pts) >= 2):
            glyph, params = "TILE", {}
        else:
            params["points"] = [_clamp(p) for p in pts]
    if glyph == "COUNTER":
        if "count" not in params:
            params["count"] = 3
        for k in ("prefix", "suffix", "caption"):
            if k in params:
                params[k] = str(params[k])[:24]
    # carrier housings (TILE/BADGE/CHIP) are never staged empty: derive a concept
    # from the label/id when no mark was authored
    if glyph in c.CARRIER_GLYPHS:
        carries = asset_ref or concept or (label and glyph in c.INSIDE_LABEL_GLYPHS)
        if not carries:
            concept = label or eid.replace("_", " ")
    out = {"id": eid, "kind": kind, "glyph": glyph, "size": size}
    if label:
        out["label"] = label
    if asset_ref:
        out["asset_ref"] = asset_ref
    if media_ref:
        out["media_ref"] = media_ref
    if concept:
        out["concept"] = concept
    if params:
        out["params"] = params
    taken.add(eid)
    return out


def _conform_program(raw_ops: Any, ids: set, relations: List[Dict[str, Any]],
                     narration_words: set, n_units: int) -> List[Dict[str, Any]]:
    ops = []
    rel_pairs = {(r["source"], r["target"]) for r in relations}
    for raw in (raw_ops or [])[:10]:
        if not isinstance(raw, dict):
            continue
        op = str(raw.get("op") or "").upper()
        if op not in c.OPS:
            op = "DRAW"
        target = str(raw.get("target") or "").strip()
        if "->" in target or op == "CONNECT":
            s, _, t = [x.strip() for x in target.partition("->")]
            if not t:
                continue
            if (s, t) not in rel_pairs:
                continue
            if op not in ("CONNECT", "STRIKE", "INK", "DIM", "TRACE", "SETTLE"):
                op = "CONNECT"
            target = f"{s}->{t}"
        elif target not in ids:
            continue
        at = dict(raw.get("at") or {})
        keys = [k for k in ("word", "unit", "offset_ms") if k in at]
        fixed_at: Dict[str, Any] = {}
        if "word" in keys:
            w = str(at["word"]).strip()
            wnorm = c._norm(w) or w.lower()
            fixed_at = {"word": w} if (wnorm in narration_words or w in narration_words) else {}
        if not fixed_at and "unit" in keys:
            try:
                u = int(at["unit"])
                if 0 <= u < n_units:
                    fixed_at = {"unit": u}
            except (TypeError, ValueError):
                pass
        if not fixed_at and "offset_ms" in keys:
            try:
                fixed_at = {"offset_ms": max(0, int(at["offset_ms"]))}
            except (TypeError, ValueError):
                pass
        if not fixed_at:
            fixed_at = {"unit": 0} if n_units else {"offset_ms": 0}
        try:
            dur = int(raw.get("duration_ms") or c.OP_DEFAULT_MS[op])
        except (TypeError, ValueError):
            dur = c.OP_DEFAULT_MS[op]
        dur = max(120, min(4000, dur))
        params = dict(raw.get("params") or {}) if isinstance(raw.get("params"), dict) else {}
        if params.get("wipe") and op not in ("DRAW", "CONNECT"):
            params.pop("wipe")
        if op == "TRAVEL":
            over = [o for o in (params.get("over") or []) if o in ids]
            if not over:
                over = [i for i in ids if i != target][:1]
            params["over"] = over
        if op == "COUNT":
            try:
                params["count"] = max(1, min(12, int(params.get("count") or 3)))
            except (TypeError, ValueError):
                params["count"] = 3
        o = {"op": op, "target": target, "at": fixed_at, "duration_ms": dur}
        if params:
            o["params"] = params
        try:
            o["from"], o["to"] = float(raw.get("from", 0.0)), float(raw.get("to", 1.0))
        except (TypeError, ValueError):
            pass
        ops.append(o)
    return ops


def _conform_illustration(raw: Any, unit_word_sets: List[list], narration_words: set,
                          n_units: int, media_ids: set, registry_ids: set,
                          earlier: Dict[str, set]) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    form = _enum(raw.get("form"), c.ILLUSTRATION_FORMS, "OBJECT_STAGE")
    taken: set = set()
    entities = []
    for e in (raw.get("entities") or [])[:12]:
        if isinstance(e, dict):
            ent = _conform_entity(e, taken, unit_word_sets, media_ids, registry_ids)
            if ent:
                entities.append(ent)
    # cap 7 — keep heroes first, then author order
    if len(entities) > 7:
        rank = {"hero": 0, "support": 1, "minor": 2}
        keep = set(e["id"] for e in sorted(entities, key=lambda x: rank.get(x["size"], 1))[:7])
        entities = [e for e in entities if e["id"] in keep]
    heroes = [i for i, e in enumerate(entities) if e["size"] == "hero"]
    for i in heroes[2:]:
        entities[i]["size"] = "support"
    if len(entities) < c.FORM_MIN_ENTITIES[form]:
        form = "OBJECT_STAGE"
    if not entities:
        return None
    ids = {e["id"] for e in entities}
    relations = []
    for r in (raw.get("relations") or []):
        if not isinstance(r, dict):
            continue
        t = _enum(r.get("type"), c.RELATION_TYPES, "connects")
        s, tg = str(r.get("source") or "").strip(), str(r.get("target") or "").strip()
        if s in ids and tg in ids and s != tg:
            rel = {"type": t, "source": s, "target": tg}
            st = r.get("style")
            if st is not None and str(st).lower() in c.RELATION_STYLES:
                rel["style"] = str(st).lower()
            relations.append(rel)
    if form in ("PROCESS_PIPELINE", "RELATIONSHIP") and not relations:
        order = [e["id"] for e in entities]
        relations = [{"type": "connects", "source": order[i - 1], "target": order[i]}
                     for i in range(1, len(order))]
    if form == "STATE_TRANSFORMATION" and not any(r["type"] == "transforms_into" for r in relations):
        order = [e["id"] for e in entities]
        if len(order) >= 2:
            relations.append({"type": "transforms_into", "source": order[0], "target": order[1]})
        else:
            form = "OBJECT_STAGE"
    if form == "COMPARISON" and not any(r["type"] == "compares" for r in relations):
        order = [e["id"] for e in entities]
        if len(order) >= 2:
            relations.append({"type": "compares", "source": order[0], "target": order[1]})
        else:
            form = "OBJECT_STAGE"
    ops = _conform_program(raw.get("program"), ids, relations, narration_words, n_units)
    if form == "CALLOUT_LENS":
        if not any(e["glyph"] == "LENS" for e in entities):
            form = "OBJECT_STAGE"
        elif not any(o["op"] == "TRAVEL" for o in ops):
            lens = next(e["id"] for e in entities if e["glyph"] == "LENS")
            other = next((e["id"] for e in entities if e["id"] != lens), lens)
            ops.append({"op": "TRAVEL", "target": lens, "at": {"unit": 0} if n_units else {"offset_ms": 0},
                        "duration_ms": c.OP_DEFAULT_MS["TRAVEL"], "params": {"over": [other]}})
    if form == "SIGNAL" and not any(e["glyph"] == "RING" for e in entities):
        form = "OBJECT_STAGE"
    if form == "DATA_VISUAL" and not any(e["glyph"] in ("CHART_LINE", "BAR") for e in entities):
        form = "OBJECT_STAGE"
    if not ops:
        first = next(iter(narration_words), None)
        ops = [{"op": "DRAW", "target": e["id"],
                "at": {"word": first} if first else {"unit": 0}, "duration_ms": c.OP_DEFAULT_MS["DRAW"]}
               for e in entities[:4]] or []
    out: Dict[str, Any] = {"form": form, "entities": entities, "relations": relations, "program": ops}
    carry = raw.get("carry") or {}
    if isinstance(carry, dict):
        src = str(carry.get("from_beat") or "").strip()
        ces = [str(x) for x in (carry.get("entities") or [])]
        ces = [x for x in ces if x in ids and src in earlier and x in earlier[src]]
        if ces and src in earlier:
            out["carry"] = {"from_beat": src, "entities": ces}
    persist = str(raw.get("persist_to") or "").strip()
    if persist:
        out["persist_to"] = persist
    return out


def _conform_units(raw_units: Any, narration_words: set) -> List[Dict[str, Any]]:
    units = []
    for u in (raw_units or []):
        if not isinstance(u, dict):
            continue
        text = " ".join(str(u.get("text") or "").split())
        words = _norm_seq(text)
        if not words or not set(words) <= narration_words:
            continue
        un: Dict[str, Any] = {"text": text}
        r = _enum(u.get("role"), c.UNIT_ROLES, "support")
        un["role"] = r
        un["semantic_role"] = _enum(u.get("semantic_role"), c.SEMANTIC_ROLES,
                                    "statement" if r == "hero" else "setup")
        un["emphasis"] = _clamp(u.get("emphasis", 0.9 if r == "hero" else 0.5))
        unit_set = set(words)
        stress = [w for w in (u.get("stress") or []) if str(w).strip() and c._norm(str(w)) in unit_set]
        if stress:
            un["stress"] = stress
        mute = [w for w in (u.get("mute") or []) if str(w).strip() and c._norm(str(w)) in unit_set]
        if mute:
            un["mute"] = mute
        anchor = str(u.get("anchor_word") or "").strip()
        if anchor and (c._norm(anchor) in narration_words or anchor in narration_words):
            un["anchor_word"] = anchor
        if "reveal" in u and u["reveal"] is not None:
            rv = _enum(u["reveal"], c.REVEAL_MODES, None)
            if rv:
                un["reveal"] = rv
        rg = u.get("replace_group")
        if rg:
            un["replace_group"] = str(rg)
        if u.get("italic"):
            un["italic"] = True
        if "can_promote" in u:
            un["can_promote"] = bool(u["can_promote"])
        units.append(un)
        if len(units) >= 5:
            break
    heroes = [i for i, u in enumerate(units) if u["role"] == "hero"]
    for i in heroes[3:]:
        units[i]["role"] = "support"
    # the typography authority indexes the promoted hero; a unit list with no
    # hero crashes it — promote the strongest unit so every beat has one
    if units and not any(u["role"] == "hero" for u in units):
        lead = max(range(len(units)), key=lambda i: units[i].get("emphasis", 0))
        units[lead]["role"] = "hero"
    return units


def _absorb_media(illus: Dict[str, Any], media: Dict[str, Any], taken_extra: str = "") -> Dict[str, Any]:
    """Beat-level media joins the illustration as a MEDIA entity (contract rule:
    media and data belong inside the illustration, not beside it)."""
    ids = {e["id"] for e in illus["entities"]}
    eid = media["asset_id"] if media["asset_id"] not in ids else f"{media['asset_id']}_{taken_extra}"
    if len(illus["entities"]) >= 7:
        minors = [i for i, e in enumerate(illus["entities"]) if e["size"] == "minor"]
        if not minors:
            return illus
        illus["entities"].pop(minors[-1])
        ids.discard(eid)
    ent = {"id": eid, "kind": "evidence", "glyph": "MEDIA",
           "size": "support", "media_ref": media["asset_id"],
           "params": {"chassis": "card"}}
    illus["entities"].append(ent)
    if not any(o["target"] == eid for o in illus["program"]) and len(illus["program"]) < 10:
        illus["program"].append({"op": "DRAW", "target": eid,
                                 "at": {"offset_ms": 0}, "duration_ms": c.OP_DEFAULT_MS["DRAW"]})
    return illus


def _absorb_data(illus: Dict[str, Any], data: Dict[str, Any], unit_word_sets: List[list]) -> Dict[str, Any]:
    """Beat-level data joins the illustration as a COUNTER (numeric) or CHIP
    (short label)."""
    ids = {e["id"] for e in illus["entities"]}
    eid = "datum" if "datum" not in ids else f"datum_{len(ids)}"
    if len(illus["entities"]) >= 7:
        return illus
    value = data.get("value", "")
    try:
        count = int(re.sub(r"[^0-9]", "", value) or "0") or None
    except (TypeError, ValueError):
        count = None
    if count is not None and 1 <= count <= 999:
        params: Dict[str, Any] = {"count": max(1, min(12, count)) if count <= 12 else 12}
        cap = str(data.get("label") or "")[:10]
        if cap:
            params["caption"] = cap
        ent = {"id": eid, "kind": "object", "glyph": "COUNTER", "size": "support", "params": params}
    else:
        label = _fix_label(value or data.get("label"), unit_word_sets, "CHIP") or "data"
        ent = {"id": eid, "kind": "object", "glyph": "CHIP", "size": "support", "label": label}
    illus["entities"].append(ent)
    if not any(o["target"] == eid for o in illus["program"]) and len(illus["program"]) < 10:
        op = "COUNT" if ent["glyph"] == "COUNTER" else "DRAW"
        illus["program"].append({"op": op, "target": eid, "at": {"offset_ms": 0},
                                 "duration_ms": c.OP_DEFAULT_MS[op],
                                 **({"params": {"count": ent["params"]["count"]}} if op == "COUNT" else {})})
    return illus


def conform(payload: Dict[str, Any], groups: List[List[Dict[str, Any]]],
            style: Dict[str, Any], film_id: str, aspects: List[str],
            media_library: List[Dict[str, Any]], registry_ids: set) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Analyst payload -> (treatment, storyboard). Raises AnalystInvalid if unusable."""
    if not isinstance(payload, dict) or not isinstance(payload.get("beats"), list):
        raise AnalystInvalid("payload has no beats[]")
    media_ids = {m["asset_id"] for m in media_library}
    media_kinds = {m["asset_id"]: m.get("kind", "IMAGE") for m in media_library}
    cast: Dict[str, Dict[str, Any]] = {}
    for cid, m in (payload.get("cast") or {}).items():
        mid = str(cid).strip()
        if not mid or len(cast) >= c.CAST_MEMBER_CAP or not isinstance(m, dict):
            continue
        member = {"posture": _enum(m.get("posture"), c.FIGURE_POSTURES, "standing")}
        for pin in ("head", "face", "skin", "garment"):
            if str(m.get(pin) or "").strip():
                member[pin] = str(m[pin]).strip()
        cast[mid] = member
    group_texts = [" ".join(w["text"] for w in g).strip() for g in groups]
    group_word_sets = [set(_norm_seq(t)) for t in group_texts]
    used: set = set()
    beats: List[Dict[str, Any]] = []
    earlier_illustrations: Dict[str, set] = {}
    metaphors: Dict[str, str] = {}
    next_idx = 0

    def filler_beat(gi: int, bid: str) -> Dict[str, Any]:
        # an unconsumed clause still needs a beat — quiet text-only carry-through
        return {"beat_id": bid, "beat_type": "EXPLANATION", "pattern": "PROGRESSIVE_HERO_BUILD",
                "dominant_layer": "TEXT", "narration": group_texts[gi], "energy": 0.5,
                "complexity": 0.4, "display_units": [{"text": group_texts[gi], "role": "hero",
                                                      "semantic_role": "statement", "emphasis": 0.8}]}

    raw_beats = [b for b in payload["beats"] if isinstance(b, dict)]
    for rb in raw_beats:
        gidx = [int(g) for g in (rb.get("groups") or []) if isinstance(g, int) or (isinstance(g, float) and g.is_integer()) or (isinstance(g, str) and g.isdigit())]
        gidx = [g for g in gidx if 0 <= g < len(groups)]
        if not gidx or min(gidx) < next_idx:
            if not gidx:
                gidx = [next_idx] if next_idx < len(groups) else []
            else:
                gidx = list(range(next_idx, max(gidx) + 1))
        gidx = [g for g in gidx if g >= next_idx]
        if not gidx:
            continue
        while next_idx < min(gidx):
            bid = f"b{len(beats) + 1:02d}"
            beats.append(filler_beat(next_idx, bid))
            used.add(next_idx)
            next_idx += 1
        bid = f"b{len(beats) + 1:02d}"
        narration = " ".join(group_texts[g] for g in gidx).strip()
        nwords: set = set()
        for g in gidx:
            nwords |= group_word_sets[g]
        units = _conform_units(rb.get("display_units"), nwords)
        if not units:
            units = [{"text": narration, "role": "hero", "emphasis": 0.8, "semantic_role": "statement"}]
        unit_word_sets = [_norm_seq(u["text"]) for u in units]
        illus = _conform_illustration(rb.get("illustration"), unit_word_sets, nwords,
                                      len(units), media_ids, registry_ids, earlier_illustrations)
        figure = None
        rf = rb.get("figure")
        if isinstance(rf, dict) and str(rf.get("justification") or "").strip():
            figure = {"valence": max(-1.0, min(1.0, float(rf.get("valence", 0) or 0))),
                      "arousal": _clamp(rf.get("arousal", 0.5)),
                      "posture": _enum(rf.get("posture"), c.FIGURE_POSTURES, "standing"),
                      "energy": _clamp(rf.get("energy", 0.5)),
                      "formality": _clamp(rf.get("formality", 0.5)),
                      "facing": _enum(rf.get("facing"), c.FIGURE_FACINGS, "TOWARD_TEXT"),
                      "justification": " ".join(str(rf["justification"]).split())}
            char = str(rf.get("character") or "").strip()
            if char and char in cast:
                figure["character"] = char
            rt = rf.get("track")
            if isinstance(rt, dict):
                track = {k: _enum(rt.get(k), c.FIGURE_TRACK_SIDES, "none") for k in ("enter", "exit")}
                if track["enter"] != "none" or track["exit"] != "none":
                    figure["track"] = track
            rp = rf.get("prop")
            if isinstance(rp, dict):
                concept = " ".join(str(rp.get("concept") or "").split())[:40]
                if concept:
                    figure["prop"] = {"concept": concept, "hand": _enum(rp.get("hand"), c.FIGURE_HANDS, "auto")}
            rs = rf.get("states")
            if isinstance(rs, list):
                states = []
                for st in rs[:3]:
                    if not isinstance(st, dict) or not any(st.get(k) for k in ("pose", "face", "head")):
                        continue
                    at = st.get("at") or {}
                    if "word" in at and str(at["word"]).lower() in nwords:
                        states.append({"at": {"word": str(at["word"])},
                                       **{k: str(st[k]) for k in ("pose", "face", "head") if st.get(k)}})
                    elif "offset_ms" in at:
                        try:
                            states.append({"at": {"offset_ms": max(0, int(at["offset_ms"]))},
                                           **{k: str(st[k]) for k in ("pose", "face", "head") if st.get(k)}})
                        except (TypeError, ValueError):
                            pass
                if states:
                    figure["states"] = states
            for pin in ("pose", "face"):
                if str(rf.get(pin) or "").strip():
                    figure[pin] = str(rf[pin]).strip()
        data = None
        rd = rb.get("data")
        if isinstance(rd, dict) and str(rd.get("value") or "").strip():
            data = {"kind": _enum(rd.get("kind"), c.DATA_KINDS, "STAT"),
                    "value": " ".join(str(rd["value"]).split())}
            if str(rd.get("label") or "").strip():
                data["label"] = " ".join(str(rd["label"]).split())
            if rd.get("secondary"):
                data["secondary"] = str(rd["secondary"])
        media = None
        rm = rb.get("media")
        if isinstance(rm, dict) and str(rm.get("asset_id") or "") in media_ids:
            media = {"asset_id": str(rm["asset_id"]),
                     "role": _enum(rm.get("role"), c.MEDIA_ROLES, "EVIDENCE")}
            f = rm.get("focus")
            if isinstance(f, dict) and all(k in f for k in ("x", "y", "w", "h")):
                media["focus"] = {k: _clamp(f[k]) for k in ("x", "y", "w", "h")}
            if rm.get("persist_to"):
                media["persist_to"] = str(rm["persist_to"])
            tr = rm.get("trim")
            if isinstance(tr, dict):
                try:
                    s0, e0 = float(tr.get("start", 0)), float(tr.get("end", 0))
                    if e0 > s0 and media_kinds.get(media["asset_id"]) == "VIDEO":
                        media["trim"] = {"start": s0, "end": e0}
                except (TypeError, ValueError):
                    pass
        # media and data live inside the illustration as MEDIA/CHART entities
        if illus is not None and media is not None:
            illus = _absorb_media(illus, media, taken_extra=bid)
            media = None
        if illus is not None and data is not None:
            illus = _absorb_data(illus, data, unit_word_sets)
            data = None
        layer = _enum(rb.get("dominant_layer"), c.DOMINANT_LAYERS, None)
        # a TEXT-led beat may carry a figure or media, not both — promote to EVIDENCE
        if media and figure and layer in (None, "TEXT"):
            layer = "EVIDENCE"
        if layer == "QUIET":
            units = units[:1]
            figure = media = data = None
            illus = None
        if layer == "ILLUSTRATION" and not illus:
            layer = "HYBRID" if units else None
        if layer == "HYBRID" and not illus:
            layer = "TEXT"
        if layer == "EVIDENCE" and not media:
            layer = None
        if layer == "DATA" and not data:
            layer = None
        if layer == "FIGURE" and not figure:
            layer = None
        btype = _enum(rb.get("beat_type"), c.BEAT_TYPES, "EXPLANATION")
        pattern = _enum(rb.get("pattern"), c.PATTERNS, "PROGRESSIVE_HERO_BUILD")
        if layer is None:
            layer = c.PATTERN_LAYER.get(pattern, "TEXT")
            if layer == "ILLUSTRATION" and not illus:
                layer = "HYBRID" if units else "TEXT"
            if layer == "HYBRID" and (not units or not illus):
                layer = "TEXT" if units else "ILLUSTRATION"
        beat: Dict[str, Any] = {"beat_id": bid, "beat_type": btype, "pattern": pattern,
                                 "dominant_layer": layer, "narration": narration,
                                 "energy": _clamp(rb.get("energy", 0.6)),
                                 "complexity": _clamp(rb.get("complexity", 0.45)),
                                 "display_units": units}
        if figure:
            beat["figure"] = figure
        if media:
            beat["media"] = media
        if data:
            beat["data"] = data
        if illus:
            if "persist_to" in illus:
                tgt = str(illus["persist_to"])
                # persist targets a *later* beat id; LLM writes 1-based intent loosely
                if not re.fullmatch(r"b\d+", tgt):
                    illus.pop("persist_to")
            beat["illustration"] = illus
            earlier_illustrations[bid] = {e["id"] for e in illus["entities"]}
        feats = rb.get("features")
        if isinstance(feats, dict):
            beat["features"] = {str(k): _clamp(v) for k, v in feats.items() if isinstance(v, (int, float))}
        if rb.get("min_duration_ms"):
            try:
                beat["min_duration_ms"] = max(0, int(rb["min_duration_ms"]))
            except (TypeError, ValueError):
                pass
        if str(rb.get("cut") or "") == "hard":
            beat["cut"] = "hard"
        if str(rb.get("metaphor") or "").strip():
            metaphors[bid] = " ".join(str(rb["metaphor"]).split())
        beats.append(beat)
        for g in gidx:
            used.add(g)
        next_idx = max(gidx) + 1
    while next_idx < len(groups):
        bid = f"b{len(beats) + 1:02d}"
        beats.append(filler_beat(next_idx, bid))
        used.add(next_idx)
        next_idx += 1
    if not beats:
        raise AnalystInvalid("no beats could be conformed")
    # persist_to only valid when pointing at a later beat
    order = [b["beat_id"] for b in beats]
    for b in beats:
        il = b.get("illustration")
        if il and il.get("persist_to"):
            t = il["persist_to"]
            if t not in order or order.index(t) <= order.index(b["beat_id"]):
                il.pop("persist_to")
        if b.get("media") and b["media"].get("persist_to"):
            t = b["media"]["persist_to"]
            if t not in order or order.index(t) < order.index(b["beat_id"]):
                b["media"].pop("persist_to")
    film = payload.get("film") if isinstance(payload.get("film"), dict) else {}
    mood = _enum(film.get("mood"), c.FILM_MOODS, None)
    note = str(film.get("note") or "").strip()
    treatment = {
        "schema": "NexStudioEditorialTreatmentV2",
        "film_id": film_id,
        "note": note or "story-analyst authored",
        "aspects": aspects, "fps": 30,
        "brand": {**style.get("palette", {}), "finish": style.get("finish", "EDITORIAL_FLAT")},
        "typography": {"reveal": style.get("reveal", "WORD_CASCADE"), "tonal_ink": 0.42,
                        "min_visual_share": 0.6},
        "voice": {"source": "MASTER", "audio_path": "voice.mp3",
                  "alignment_path": "alignment.json", "head_pad_ms": 350},
        "media_library": media_library,
        "beats": beats,
    }
    if mood:
        treatment["mood"] = mood
    if cast:
        treatment["cast"] = cast
    # The world bible: the analyst's authored look overrides the style preset — each colour is
    # validated as a hex swatch and the finish/grain confined to their enums; anything else the
    # model writes falls back to the preset rather than breaking the contract.
    rb = film.get("brand")
    if isinstance(rb, dict):
        brand = dict(treatment["brand"])
        for k in ("ink", "paper", "accent"):
            v = str(rb.get(k) or "").strip()
            if re.fullmatch(r"#[0-9a-fA-F]{3,8}", v):
                brand[k] = v
        fin = _enum(rb.get("finish"), c.FINISHES, None)
        if fin:
            brand["finish"] = fin
        treatment["brand"] = brand
    rw = film.get("world")
    if isinstance(rw, dict):
        world: Dict[str, Any] = {}
        grain = _enum(rw.get("grain"), c.WORLD_GRAINS, None)
        if grain:
            world["grain"] = grain
        rm = rw.get("motif")
        if isinstance(rm, dict):
            concept = " ".join(str(rm.get("concept") or "").split())[:40]
            corner = _enum(rm.get("corner"), c.WORLD_CORNERS, "bottom-right")
            if concept:
                world["motif"] = {"concept": concept, "corner": corner}
        if world:
            treatment["world"] = world
    storyboard = {
        "schema": "NexStudioStoryboardV1",
        "film_id": film_id,
        "arc": {
            "thesis": str(film.get("thesis") or "").strip(),
            "motif": str(film.get("motif") or "").strip() or None,
            "mood": mood,
            "beat_arc": {b["beat_id"]: b["beat_type"] for b in beats},
        },
        "scenes": [s for s in (payload.get("scenes") or []) if isinstance(s, dict)],
        "entities": [e for e in (payload.get("entities") or []) if isinstance(e, dict)],
        "cast": cast or None,
        "world": treatment.get("world"),
        "metaphors": metaphors,
    }
    return treatment, storyboard


# ---------------------------------------------------------------- top-level

def build_llm_treatment(script: str, words: List[Dict[str, Any]], groups: List[List[Dict[str, Any]]],
                        style: Dict[str, Any], media_library: List[Dict[str, Any]], film_id: str,
                        aspects: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Full pass: prompt -> provider -> conform -> contract check. Returns (treatment, storyboard).
    media_library entries are the same dicts make_reel builds (asset_id/kind/path/width/height)."""
    registry_ids = _registry_ids()
    media_ids = [m["asset_id"] for m in media_library]
    payload = _user_payload(script, groups, style, media_ids, registry_ids)
    raw = call_analyst(payload)
    treatment, storyboard = conform(raw, groups, style, film_id, aspects, media_library, registry_ids)
    try:
        c.FilmTreatment.parse(treatment)
    except c.TreatmentError as e:
        raise AnalystInvalid(f"conformed treatment rejected: {e.code}: {e.detail}") from e
    return treatment, storyboard


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Story analyst — self-test / replay driver")
    ap.add_argument("--selftest", action="store_true", help="print config + availability")
    ap.add_argument("--script"); ap.add_argument("--script-file")
    ap.add_argument("--alignment", help="alignment.json (words[] with text/start_ms/end_ms)")
    ap.add_argument("--replay", help="recorded analyst payload (same as STORY_ANALYST_REPLAY)")
    ap.add_argument("--style", default="tiles")
    ap.add_argument("--out", required=False, help="dir for treatment.json + storyboard.json")
    args = ap.parse_args()
    if args.replay:
        os.environ["STORY_ANALYST_REPLAY"] = args.replay
    cfg = analyst_config()
    if args.selftest:
        print(json.dumps({"available": analyst_available(),
                          "model": cfg["model"] or None, "base_url": cfg["base_url"],
                          "key_env": cfg["key_env"], "replay": cfg["replay"] or None}, indent=1))
        return
    if not args.out:
        sys.exit("--out required unless --selftest")
    sys.path.insert(0, str(TOOLS))
    import importlib
    mr = importlib.import_module("make_reel")
    words = json.loads(Path(args.alignment).read_text())["words"] if args.alignment else []
    if not words:
        text = args.script or Path(args.script_file).read_text()
        t = 0
        for w in text.split():
            words.append({"text": w, "start_ms": t, "end_ms": t + 300}); t += 330
    groups = mr.chunk_beats(words)
    style = mr.style_of(args.style)
    treatment, storyboard = build_llm_treatment(
        args.script or (Path(args.script_file).read_text() if args.script_file else ""),
        words, groups, style, [], "analyst-selftest", ["16x9", "1x1", "9x16"])
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "treatment.json").write_text(json.dumps(treatment, indent=1))
    (out / "storyboard.json").write_text(json.dumps(storyboard, indent=1))
    print(f"wrote {out}/treatment.json + storyboard.json — beats: {len(treatment['beats'])}")


if __name__ == "__main__":
    main()
