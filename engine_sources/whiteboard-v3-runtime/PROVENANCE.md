# Provenance — reconstruction boundary

| Artifact | Identity |
|---|---|
- `v3_board_sections.py` — sha256 `ed0547f48bc00d93438a7244bda37f0c9c4e70cf144135258df09a8704e44f06`
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
| `pipeline_v3_narration_timed.py` (whiteboard pipeline) | `9d6603b08a6f7803b96a81afd840cd0ccc2c1bb5630c8b20f165a137379bd264` |
| `v3_board_renderer.py` (whiteboard draw layer) | `1b82bfcd540c65865d7515d8ca0f354fade14e03482b454472b1ec63b7d3f076` |
| `pipeline_kinetic_timed.py` (kinetic pipeline) | `29a54f01900001b42fc89275df131847b74067f379ad7cc96cba9a74191d0e89` |
| `kinetic_type_renderer.py` (kinetic draw layer) | `602a0fddd86b2f3347ac203b0f2c46e9173c5902d7f90361b699e41978f881be` |
| `pipeline_diagram_timed.py` (diagram pipeline) | `c00cf324b135932cf071206c52f993cf8a4c1e788ede8ae6fe0caaad658c5f48` |
| `diagram_renderer.py` (diagram draw layer) | `8d8858c35fb3050e82de7513e57e535d62f3c599f2ac84a6eae5d32fe57f097e` |
| `plan_author.py` (script→plan decision layer) | `9913a725b7b8ea3fc76e79e33f6f2d34bbe87c9f758bc6ba58627bc0ca3d0372` |
| `vo_synth.py` (edge/kokoro VO + timings) | `3e51653659e0cc56fd4bf4439906bacd4e788b6506ab1e1b3b6b9e500b106466` |
| `review_page.py` / `render_queue.py` | `17272c67991b19d10b22e327b3ff8410c5fb100522ddfb9e9301e6262c87dd8d` / `d9465acd46896c29dc3620a9be69115fa2faee9748b2be12cdbb09f2460d8630` |
| `tools/nexstick/mocap.cjs` | nexstick motion bridge (mocap->paperbook rig proof) | `db0c394d4c1c98016f686248808e4101c72623b2a0a53b008a9c2d3e4e94a543` |
| `tools/nexstick/mocap_rig.cjs` | nexstick motion bridge (mocap->paperbook rig proof) | `c516720538ec072d8323a0dd9969df1f9c9869cd6526504f2efd0b04d944f06c` |
| `tools/nexstick/walk_proof3.py` | nexstick motion bridge (mocap->paperbook rig proof) | `513b574787af34dc50a82d91626f12d73b7291f5b88e2ac19763eecb88c157f6` |
| `tools/paper_cast/line_cast.py` | paper-cast line-art tracer (silhouette union, fills, hatching) | `3a43f15b05450dd3b909d8cc242e76bae0a7c50b729c34e5134e57ac3d2492ee` |
| `tools/paper_cast/paperbook-figure.js` | paperbook figure renderer (vendored; + bend-crease/finger detail for line-art figures) | `6df839b773241c40d6f1791110e29ed2e7e8f73ac2842e8e13a236ddf45b523e` |
| `tools/nexstick/bvh_to_vault.py` | CMU BVH -> V5 vault converter (FK, joint map, foot contacts) | `af117dfbc64dc8d260b5e52731b60fbbdeb126282aa477aef0daf129d4458b86` |
| `tools/nexstick/cmu_sampler.cjs` | CMU vault sampler (V5 sample contract; +NEX performance vault merge) | `67dab3c3fab3980b39b455114e4b386e8bb4e8619e746f72aab6e128e1757744` |
| `tools/nexstick/compiled/cmu_motion_vault_v5.json` | 64-clip CMU corpus (free-for-all-uses license) | `806de412cf227a1866990b46e09a708581e493c5fbce614a9c092b79f3e98e3d` |
| `tools/paper_cast/paper-cast-rig.js` | Paper-cast rig: articulated figure builder (+ world pitch/root transform for floor & air poses) | `819b50feb27ab3c5661719046b1ee485ccd57a7f4a5dfc24b86fd6a28aab653a` |
| `tools/nexstick/ek_pose_clips.py` | Everkinetic canonical keypose -> vault FK generator (CC BY-SA 4.0) | `1900285b742c10a667e6e0def196cea56b584bc1eea1bb564754a7091508ac72` |
| `tools/nexstick/compiled/exercise_vault_v5.json` | 18 exercise rep-cycle clips (Everkinetic pose reference, CC BY-SA 4.0) | `f21f64bf5e5cc2ee81b4636099b1bc9630ebb9da290b14fb193416f8b3048542` |
| `tools/paper_cast/cast-wardrobe.js` | cast wardrobe (body-axis garment paths) | `16018c7c3633c0d4bf2d7e9e640b02ae60aeac18a691657a209aea5c70d1f350` |
| `tools/nexstick/skin_rig.cjs` | skin-on-skeleton renderer: true-joint masses, real-depth occlusion sort |
| `tools/nexstick/fig_motion.py` | board bridge: clip_select→skin_rig strip renderer (cairosvg PNG tiles, cached) | `844991fe040c0e56f1fef21a1658e7d93f4770e420b9bf5b5c20c079c96fff24` | `0bd128ce5ce779d147fed7418484cbfdd0043ad5329594d6df98057495795806` |
| `tools/vo/visemes.py` | rhubarb bridge — VO wav to viseme timeline (Preston-Blair -> cast-face) | `43c6dbc64883af40334f8962a2dbb0b08946f99e329ca2779aa96031b9985a26` |
| `tools/nexstick/fx_marks.cjs` | cartoon mark layer: velocity speed lines, impact bursts, foot-plant dust | `e0dce5bde5eceffc823eaa078ea3e7071aadd597adf36502a38ba7c2647b8749` |
| `tools/nexstick/clip_select.cjs` | narration text -> vault clip pattern table (260+ clips) | `72fbb3cd9e59a05fef0f174cff74a32412a15c7dc10a89694109171dd3fe528b` |
| `tools/nexstick/bake_blend_vault.py` | Blender .blend -> V5 vault action baker (PERFORMANCE_CARRIER rigs) | `b8029a278ba97f5b4f30172636eba7890154745b98cf9a6f1b56883bfdab9d21` |
| `tools/nexstick/compiled/nex_vault_v5.json` | 182 authored actions from the NexMind performance-carrier rigs (internal) | `e6982c7aacea2b7f07e49dbf134d4640fb02cbcb628a1a88e08abf8821cea3fa` |
| `tools/nexstick/compiled/mouth_shapes.json` | 7 viseme mouth loops baked from NEX_MOUTH_MINIMAL (internal) | `f55a341bf3b6b38133e2b5a0252b232a22457f32a34c9251dbcda3d07ee37659` |
