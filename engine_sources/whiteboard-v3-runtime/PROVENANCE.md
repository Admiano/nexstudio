# Provenance — reconstruction boundary

| Artifact | Identity |
|---|---|
- `v3_board_sections.py` — sha256 `c41e91537f1946ac35c76a3dd0389dae8e2d2b138748c822984266e4ef561731`
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

## Runtime artifact preservation — this system

Every renderer this system depends on is recorded here with its sha256,
committed to version control, and covered by golden frames + tests — the
preservation treatment the original V3 renderer never received. Update
the hashes whenever a file changes (or run `sha256sum <files>`).

| Artifact | sha256 |
|---|---|
| `pipeline_v3_narration_timed.py` (whiteboard pipeline) | `5b867b24358a124bc5c15f0f95798b8dc49de3ca9085c9f4cc78dc0193ac66a3` |
| `v3_board_renderer.py` (whiteboard draw layer) | `5aa5c42892433544fdf43998edffc5e4022475bf81053898c13a15e8df529333` |
| `pipeline_kinetic_timed.py` (kinetic pipeline) | `29a54f01900001b42fc89275df131847b74067f379ad7cc96cba9a74191d0e89` |
| `kinetic_type_renderer.py` (kinetic draw layer) | `602a0fddd86b2f3347ac203b0f2c46e9173c5902d7f90361b699e41978f881be` |
| `pipeline_diagram_timed.py` (diagram pipeline) | `c00cf324b135932cf071206c52f993cf8a4c1e788ede8ae6fe0caaad658c5f48` |
| `diagram_renderer.py` (diagram draw layer) | `8d8858c35fb3050e82de7513e57e535d62f3c599f2ac84a6eae5d32fe57f097e` |
| `plan_author.py` (script→plan decision layer) | `4d00affadd892722c668977862ef321d561a20c2062af847ca9c164dfb0c41de` |
| `vo_synth.py` (edge/kokoro VO + timings) | `3e51653659e0cc56fd4bf4439906bacd4e788b6506ab1e1b3b6b9e500b106466` |
| `review_page.py` / `render_queue.py` | `17272c67991b19d10b22e327b3ff8410c5fb100522ddfb9e9301e6262c87dd8d` / `d9465acd46896c29dc3620a9be69115fa2faee9748b2be12cdbb09f2460d8630` |
