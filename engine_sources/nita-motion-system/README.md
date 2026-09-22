# NITA COMPLETE CHARACTER + MOTION SYSTEM PACKAGE

## Authority
This package is intentionally based on ONE character authority only:
`01_CURRENT_CHARACTER/NITA_CERT_V4_3_FULL_RENDER_CANDIDATE.blend`

No historical Nita/Vita checkpoint `.blend` files are included.

## What is included
- Current bright Nita/Vita character authority and complete embedded animation/action data.
- `NITA_CURRENT_MOTION_ACTION_BANK.blend`: actions-only extraction made directly from the current checkpoint; no historical scene/character payload.
- Full current action inventory: 306 actions.
- Current semantic presenter router and external performance planning / QA runtime files used to govern motion selection and validation.
- Current acting/collision/provenance/action-integrity QA.
- Exact locked Bella certification audio plus its authority JSON.
- The Vita/Nita performance-direction authority.

## Motion categories in the current checkpoint
{
  "other_motion_specialist": 160,
  "gaze_head_attention": 28,
  "living_body_rest": 15,
  "gesture_presenter_phrase": 78,
  "face_expression_viseme": 25
}

## Historical comparison
Older Nita checkpoints were inspected only to check for unique missing motion. Their files were NOT packaged. Historical-only action names were all superseded by current actions; therefore no older checkpoint payload was extracted. See `PACKAGE_SCOPE_AND_SUPERSESSION.json`.

## Explicit exclusions
Blender binaries, render frames, diagnostic videos, render logs/caches, unrelated characters, generic NexStudio assets, and unrelated application/business files are not included.

---

## Provenance

Imported verbatim from the "Import Character in Blender" session artifact
(`NITA_COMPLETE_CHARACTER_MOTION_SYSTEM_FINAL.zip`) on 2026-09-22 — the
character/motion IP was previously only on session VMs. Motion categories:
78 gesture_presenter_phrase, 28 gaze_head_attention, 15 living_body_rest,
25 face_expression_viseme, 160 other specialist, across 306 embedded actions.
The front-facing router + unified runtime are the gesture/emote grammar
reference for camera-facing (Synthesia-style) presenters.
