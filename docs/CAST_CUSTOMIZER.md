# Modular presenter customizer

The customizer now renders the original assembled character. Its preview and
saved card use the same scene, garments, rig, camera, shader nodes and contour
passes. Browser canvas layers and multiply-tinted clothing plates are retired.

## Authoritative source

- Modular pipeline: `engine_sources/makehuman-lineart/presenters_v1`, imported
  unchanged from source commit `bf88447b8f898bea078c44b9202cfe2b7ff13be5`.
- Approved appearance: female v3 and male v6 in
  `engine_sources/makehuman-lineart/NexStudio_Presenter_Reference/characters`.
- Original `.blend` files remain unchanged. `approved-polish.json` contains
  measured geometry, transform and shape-key deltas, including the male
  jaw-driven teeth. Regenerate it with `scripts/cast-build-approved-polish.py`
  inside Blender.
- Approved shader nodes are loaded from those reference files. Selected colours
  are then applied through the existing skin, hair and lipstick controls.
  Clothing keeps the approved subtle shading treatment.
- `assets/ASSETS.json` retains the upstream creators, license terms and sources.
  `assets/FILES.json` pins every required file by size and Git blob SHA-1.

The original fitting helper read neutral body vertices even when MakeHuman body
shape targets were active. `shaped_coords` now evaluates the Basis plus active
`$` targets before garment fitting. This prevents the neckline and thigh holes
seen in the previous female assembly. Face expressions and armature deformation
remain the responsibility of the original rig.

## Selection and persistence

`CastSpec` remains the persisted selection. Legacy saved specs normalize to the
original preset defaults. New specs can independently select and colour male
tops, trousers and shoes. Skin, hair, lipstick and garments support six-digit
custom colours. Choosing None keeps neckwear and watches null across save/reopen.
The source version is pinned during normalization.

Both create and update routes validate against the same choice catalog. Mesh
paths, unknown piece fields and unavailable IDs are rejected. Preview routes
require the existing authenticated session and trusted-origin checks.

The full-body customizer lets users inspect clothes and shoes. Production
presenter framing remains governed by the reference's front-facing, hips-up
delivery decisions; this change does not rewrite video delivery compositions.

## Preview runtime

`castRenderConfig` maps a selection to the original `presets.sh`, `female.py`
and `modM.py` pipeline. The default still uses frame 27, Cycles, 12 samples and
50% of the authored 2880 × 4320 output. Freestyle thickness and compositor
Dilate/Erode size scale together according to the reference instructions.
The existing speech action and rig are retained, including closed-mouth and
gesture frames.

The SHA-256 cache key includes source version, rendering version, frame, profile
and visual selections. Name and voice do not affect it. Requests are written
atomically to disk; a Linux `flock` permits one Blender worker per cache. The
queue caps pending looks at 64 and records failures for explicit retry. Polling
can restart a stopped worker. A preview is ready only after its PNG exists.

The browser debounces changes, retains the last completed image while a new look
renders, and ignores stale responses. Save is enabled only when the current
selection's image has loaded. Failure shows a retry control. Cards and reopened
builders reuse completed images.

This preserves source fidelity at the cost of CPU rendering time. New looks on
the verification machine took roughly 45–135 seconds; cached looks return
immediately. Rendering is asynchronous and the UI reports progress. Use a
persistent writable cache on a Linux server. A serverless request runtime that
cannot run Blender or preserve local files is unsuitable for this worker.

## Run locally

```sh
npm ci
npm run cast:assets
export BLENDER_BIN=/absolute/path/to/blender
node --import tsx scripts/cast-warm-defaults.ts
python3 scripts/cast-preview-worker.py --drain
node --import tsx scripts/cast-warm-defaults.ts --check
npm run dev
```

The installer fetches only the required original mesh entries from MakeHuman
Community packs and verifies CRC, byte size and the pinned blob hashes. It skips
the network when all local files already match. Missing or changed source files
fail the build instead of silently substituting geometry.

The Docker runtime installs checksum-pinned Blender 5.2.0 for Linux x86-64,
restores those original meshes and warms both approved defaults during its
build. `CAST_PROJECT_ROOT=/app` anchors the worker and cache because Next's
standalone server changes its working directory.

Optional configuration:

| Variable | Purpose |
| --- | --- |
| `CAST_PROJECT_ROOT` | Project containing scripts and source scenes; required when the server changes cwd. |
| `CAST_PREVIEW_CACHE_DIR` | Writable shared cache directory. |
| `BLENDER_BIN` | Absolute Blender executable path. |
| `PYTHON_BIN` | Python executable, default `python3`. |
| `CAST_RENDER_THREADS` | Blender CPU threads, default 4. |
| `MH_ROOT` | Override for the restored upstream mesh directory. |
| `CAST_PREVIEW_EXTERNAL_WORKER=1` | Disable server auto-start when running `npm run worker:cast` separately. |

## Verification

Run `npm run test:cast`, `npm run typecheck` and `npm run build`. Focused checks
cover source mappings, custom colours, independent pieces, legacy defaults,
None persistence, voice-independent caching, deduplication, retry, capacity,
invalid mesh IDs, worker failure handling and lock release.

Visual and browser verification results are recorded in
`docs/CAST_CUSTOMIZER_VERIFICATION.json`. App screenshots are captured from the
production standalone server using the actual rendered PNG endpoint. Docker
is not available in the verification environment; its renderer, asset installer
and default warm-up commands are exercised individually.
