---
name: testing-editorial-motion-v2
description: How to end-to-end test the editorial-motion v2 engine (compile→render→verify) in nexstudio — render pipeline invocation, plan layout, coordinate/timing conventions, and audio verification.
---

# Testing editorial-motion v2 (engine_sources/editorial-motion-v2)

## E2E entry point
`python3 tools/regression_pack.py --fixture <name> --aspects 16x9 --out out/e2e` compiles the treatment, renders real frames + mp4 via `tools/render_reel.js` over CDP, mixes audio, and gates pixel health (blank/frozen/page-errors/music/captions/native-profile). Fixtures = `fixtures/<name>/treatment.json`; aspect plans land in `<out>/<fixture>/plan_<aspect>.json`, frames in `frames_<aspect>/fNNNNN.png`, mixed track in `audio_<aspect>.wav`, render manifest in `render_<aspect>.json`.

## Environment
- node is NOT on PATH by default: `export PATH=$HOME/.nvm/versions/node/v24.19.0/bin:$PATH`.
- Chrome runs with CDP at http://localhost:29229; render_reel.js and tools/test_runtime.js attach to it (or set CHROME_PATH to launch headless instead). Don't run two CDP consumers at once — the render needs foreground (`page.bringToFront`).
- python3 has numpy+PIL+pytest; ffmpeg/ffprobe on PATH. Sound accents only bind if a sound library resolves — `compiler/../sound-library/` or `engines/sound/NexStudio_Sound_Library_V2_Production` under the repo root, or `NEXSTUDIO_SOUND_LIBRARY_ROOT`. Without it plans get `SOUND_LIBRARY_MISSING` and zero accents.

## Compiled-plan layout (needed to write probes)
- Illustration ops live at `beat.illustration.program` in the **treatment**, but at `beat.illustration.ops` in the **compiled plan** (top-level `illustration.ops` is empty in treatments). Ops carry `start_ms`/`end_ms` **beat-local**; film time = `beat.start_ms + op.start_ms`.
- `plan.canvas` (e.g. 1280×720) vs `plan.output` (e.g. 1920×1080, `scale: 1.5`): entity/relation bboxes are canvas coords; rendered frames are output-sized → multiply by `output.scale` for pixel regions.
- Accents: `beat.sound.accents` entries have `beat_at_ms` and `film_at_ms`, `asset_id`, `path`, `sha256`, `license`, `gain_db`. `beat.sound.silenced` lists out-competed candidate events — a silenced event still proves the compiler emitted the candidate.
- Accent law constants in `compiler/editorial_plan_compiler/sound.py`: `MAX_ACCENTS_PER_BEAT=3`, `MIN_ACCENT_GAP_MS=220`.
- `plan.music` carries `status` (BOUND_CC0), `asset_id`, `moods`, `bpm`, `mood_request`, `sha256`, `path`.

## Runtime probing (in-page)
`tools/test_runtime.js` shows the pattern: serve the repo over a tiny http server (`/fs/<abs>` for out-of-tree paths), mount `runtime/editorial-runtime.js`, `EditorialRuntime.createEditorialFilm(plan, mount, {fontBase, assetUrl})`, `await film.ready`, then `film.seek(ms)` is deterministic; entity video nodes are found via `[data-media-asset="<asset_id>"] video`. Video currentTime contract: `currentTime ≈ trim.start + (lt − enter_ms)/1000`.

## Verifying rendered output
- Wipe/pixel claims: measure dark-pixel density `(img < ~120).mean()` inside scaled stroke bboxes at pre/mid/post-op film times; wiped strokes must return to baseline while non-wiped controls stay elevated.
- Audio: `wave`+numpy on `audio_<aspect>.wav` — compare 150ms RMS at each accent's `film_at_ms` vs a window ~300ms before; `render_<aspect>.json` `audio.accents` must equal the plan's accent total (render throws on missing file/sha256/license, so a PASS means every bound accent was mixed).
- `compiler/tests` via `cd compiler && python3 -m pytest -q tests`; runtime suite via `node tools/test_runtime.js` (8 fixtures × 3 aspects).

## Devin Secrets Needed
None.
