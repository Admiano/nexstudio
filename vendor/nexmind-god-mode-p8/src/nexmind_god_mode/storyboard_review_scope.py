"""The key-state gate reviews realization, before Editorial and Sound author plans."""
from copy import deepcopy
from typing import Any, Dict


# These codes describe missing downstream fields, never a creative contradiction.
_PENDING_FIELD_CODES = {
    "KEY_STATE_SOUND_PENDING": "sound_intent",
    "SOUND_DIRECTIVE_UNRESOLVED_IN_STORYBOARD": "sound_intent",
    "SOUND_DIRECTOR_UNRESOLVED_ALL_BEATS": "sound_intent",
    "SOUND_INTENT_UNRESOLVED_ON_ALL_BEATS": "sound_intent",
    "KEY_STATE_TIMING_PENDING": "vo_span",
    "VO_SPAN_OBJECT_EMPTY_ON_ALL_BEATS": "vo_span",
    "VO_SPAN_OBJECTS_EMPTY": "vo_span",
}
_FIELD_OWNERS = {"sound_intent": "SOUND_DIRECTION", "vo_span": "EDITORIAL_RHYTHM"}


def key_state_review_scope(board: Dict[str, Any]) -> Dict[str, Any]:
    beats = board.get("beats") or []
    key_state = board.get("schema") == "NexMindCanonicalStoryboardV1"
    pending = {
        "sound_intent": [b["beat_id"] for b in beats if key_state and b.get("sound_intent") == "UNRESOLVED_SOUND_DIRECTOR"],
        "vo_span": [b["beat_id"] for b in beats if key_state and "vo_span" in b and b["vo_span"] == {}],
    }
    return {
        "stage": "KEY_STATE_STORYBOARD",
        "artifact_schema": board.get("schema"),
        "pending_fields": pending,
        "field_owners": deepcopy(_FIELD_OWNERS),
        "downstream_departments": ["CINEMATOGRAPHY", "EDITORIAL_RHYTHM", "MOTION_PERFORMANCE", "SOUND_DIRECTION"],
        "law": [
            "This is a static key-state rehearsal, not a final execution storyboard. Review the authored Visual/Art realization, copy, hierarchy, settled states, continuity and brief fidelity.",
            "The compiler deliberately emits UNRESOLVED_SOUND_DIRECTOR in sound_intent. Sound Direction has not run. Empty vo_span is expected when no spans were supplied; Editorial/Rhythm authors binding durations downstream.",
            "Missing downstream plans in the listed pending_fields are advisory checks for their owning departments, not blockers for Visual Concept or Art. Use KEY_STATE_SOUND_PENDING or KEY_STATE_TIMING_PENDING with blocking=false if recording them.",
            "Do not ask Visual/Art to fill these compiler-owned fields or reroute them upstream. Preserve the approved creative work while later departments resolve their own plans.",
            "A contradictory or infeasible authored sound/timing requirement, narration change, impossible recording fit, wrong copy, weak key state, unsupported form or other material current-stage defect still blocks. Use a specific defect code, not a pending-field code.",
            "Temporal and Sound gates, rendering checks and final media reviews must still validate the completed plans. Advancing this rehearsal does not grant Creative Lock.",
        ],
    }


def scope_key_state_review(review: Dict[str, Any], board: Dict[str, Any]) -> Dict[str, Any]:
    """Defer only diagnosed placeholders confirmed in the actual key-state board.

    Unknown findings, missing blocking metadata, REJECT and LOW confidence retain
    their existing strict verdict behavior under calibrate_review. No prose-only
    'sound' or 'timing' heuristic can turn a real defect into a deferred check.
    """
    out = deepcopy(review)
    scope = key_state_review_scope(board)
    all_ids = [b["beat_id"] for b in board.get("beats") or []]
    adjustments = []
    for issue in out.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        field = _PENDING_FIELD_CODES.get(str(issue.get("code") or "").upper())
        if field is None or not isinstance(issue.get("blocking"), bool):
            continue
        ids = issue.get("beat_ids", all_ids)
        if not isinstance(ids, list) or not ids or not all(bid in scope["pending_fields"][field] for bid in ids):
            continue
        adjustments.append({"original_issue": deepcopy(issue), "field": field,
                            "beat_ids": deepcopy(ids), "owner_department": _FIELD_OWNERS[field]})
        issue.update(blocking=False, owner_department=_FIELD_OWNERS[field],
                     deferred_to_stage=_FIELD_OWNERS[field],
                     scope_reason="Expected compiler placeholder at the key-state gate; validate the downstream authored plan.")
    if adjustments:
        out["deferred_department_checks"] = list(out.get("deferred_department_checks") or []) + adjustments
        # Keep downstream requests out of the next upstream director's repair brief.
        if out.get("verdict") == "REVISE":
            active = [x for x in out.get("issues") or [] if not isinstance(x, dict) or x.get("blocking") is not False]
            if active:
                out["revision_brief"] = "Resolve the current key-state defects only: " + " ".join(
                    next((str(x[k]) for k in ("required_change", "required_fix", "repair", "detail", "message", "issue", "code") if x.get(k)), "Resolve the material key-state defect.")
                    if isinstance(x, dict) else str(x) for x in active)
        out["notes"] = (str(out.get("notes") or "") + " Expected downstream placeholders retained as deferred department checks.").strip()
    return out
