# Provenance — reconstruction boundary

| Artifact | Identity |
|---|---|
| Original renderer | `…/WHITEBOARD_ELITE_RUNTIME/vendor/pipeline_v3_narration_timed.py` |
| Recorded sha256 | `c91f2bc50cb634c993ff307ef01bb4177d9478a290bf0b4da042adee260f9c34` |
| Standalone source preserved | **no** (`06_provenance/EXACT_ARTIFACT_GAP.json`) |
| This file | reconstruction `3.0.0-reconstruction.1`, in version control |

This module is a reconstruction written from the preserved contracts
(compiler draw plans, board zones, transition frames, sound choreography,
pacing plan fields `cluster_transition_seconds` / `giant_board_travel_seconds`)
and the recorded reference output. It does not claim byte-identical parity
with the original renderer or the TEXTFIX_V2 patch. The reference MP4 and QA
still remain the provenance anchor in the frozen system package; golden frames
for this renderer are stored under `tests/golden/` and pin *this*
implementation against future drift.
