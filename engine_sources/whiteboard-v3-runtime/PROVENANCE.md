# Provenance — reconstruction boundary

| Artifact | Identity |
|---|---|
- `v3_board_sections.py` — sha256 `25ebc37572067e309b25707d9521846ca89461185349fcaa67cb343c222e5f0c`
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
| `pipeline_v3_narration_timed.py` (whiteboard pipeline) | `88bd20621f7609d45224f01a341d233274e0d3e23f71a63da817b64e8019b0fe` |
| `v3_board_renderer.py` (whiteboard draw layer) | `926b8a2181ec8ff83e2caf244f60f2fb143a5019bb75022fc0026055fcfa9128` |
| `pipeline_kinetic_timed.py` (kinetic pipeline) | `29a54f01900001b42fc89275df131847b74067f379ad7cc96cba9a74191d0e89` |
| `kinetic_type_renderer.py` (kinetic draw layer) | `602a0fddd86b2f3347ac203b0f2c46e9173c5902d7f90361b699e41978f881be` |
| `pipeline_diagram_timed.py` (diagram pipeline) | `c00cf324b135932cf071206c52f993cf8a4c1e788ede8ae6fe0caaad658c5f48` |
| `diagram_renderer.py` (diagram draw layer) | `8d8858c35fb3050e82de7513e57e535d62f3c599f2ac84a6eae5d32fe57f097e` |
| `plan_author.py` (script→plan decision layer) | `9913a725b7b8ea3fc76e79e33f6f2d34bbe87c9f758bc6ba58627bc0ca3d0372` |
| `vo_synth.py` (edge/kokoro VO + timings) | `3e51653659e0cc56fd4bf4439906bacd4e788b6506ab1e1b3b6b9e500b106466` |
| `review_page.py` / `render_queue.py` | `17272c67991b19d10b22e327b3ff8410c5fb100522ddfb9e9301e6262c87dd8d` / `d9465acd46896c29dc3620a9be69115fa2faee9748b2be12cdbb09f2460d8630` |
| `tools/nexstick/mocap.cjs` | nexstick motion bridge (mocap->paperbook rig proof) | `db0c394d4c1c98016f686248808e4101c72623b2a0a53b008a9c2d3e4e94a543` |
| `tools/nexstick/mocap_rig.cjs` | nexstick motion bridge (mocap->paperbook rig proof) | `ec629c049e4c740f8a010d31f43fd4087373b780c2ab6e7977153a4362336353` |
| `tools/nexstick/walk_proof3.py` | nexstick motion bridge (mocap->paperbook rig proof) | `513b574787af34dc50a82d91626f12d73b7291f5b88e2ac19763eecb88c157f6` |
| `tools/paper_cast/line_cast.py` | paper-cast line-art tracer (silhouette union, fills, hatching) | `3a43f15b05450dd3b909d8cc242e76bae0a7c50b729c34e5134e57ac3d2492ee` |
| `tools/paper_cast/paperbook-figure.js` | paperbook figure renderer (vendored; + bend-crease/finger detail for line-art figures) | `e5e77ffe2f590c88e8e575434384d378b2fe16aef82fba7cf11f01a5eb77b500` |
