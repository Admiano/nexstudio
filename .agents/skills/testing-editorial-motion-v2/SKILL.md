---
name: testing-editorial-motion-v2
description: How to end-to-end test the editorial-motion v2 engine (compile→render→verify) in nexstudio — render pipeline invocation, plan layout, coordinate/timing conventions, and audio verification.
---

# Testing editorial-motion v2 (engine_sources/editorial-motion-v2)

## E2E entry point
`python3 tools/regression_pack.py --fixture <name> --aspects 16x9 --out out/e2e` compiles the treatment, renders real frames + mp4 via `tools/render_reel.js` (frame range sharded across headless Chrome workers), mixes audio, and gates pixel health (blank/frozen/page-errors/music/captions/native-profile). Fixtures = `fixtures/<name>/treatment.json`; aspect plans land in `<out>/<fixture>/plan_<aspect>.json`, frames in `frames_<aspect>/fNNNNN.jpg` (q100; `--frame-format png` for lossless), mixed track in `audio_<aspect>.wav`, render manifest in `render_<aspect>.json`.

## Environment
- node is NOT on PATH by default: `export PATH=$HOME/.nvm/versions/node/v24.19.0/bin:$PATH`.
- Chrome runs with CDP at http://localhost:29229; tools/test_runtime.js attaches to it. render_reel.js prefers a Chrome binary (`--chrome`, `CHROME_PATH`, or `google-chrome` on PATH) and launches N isolated headless workers (`--workers`, default min(8, cores)); only without a binary does it fall back to the CDP browser with one foreground worker. Don't run two CDP consumers at once — a CDP render needs foreground (`page.bringToFront`).
- render_reel.js writes `<film>_<aspect>.mp4` (CRF 20 master) and `<film>_<aspect>_web.mp4` (CRF 23 playback; `--web-crf 0` to skip); `render_<aspect>.json` carries `render.{capture_s,encode_s,total_s,workers}` and `mp4_bytes` for benchmarking.
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

## make_reel.py (script/voice → rendered reels)
`python3 tools/make_reel.py --script-file s.txt --style tiles --media img.png --aspects 16x9 --out <dir> --film-id <id>` creates `fixtures/<id>/` (voice.mp3, alignment.json, treatment.json, storyboard.json when analyst-authored), then shells `regression_pack.py --fixture <id>` and writes `<dir>/manifest.json` (`treatment_source`, `storyboard`, `outputs.<aspect>` poster mp4s).
- **Voice deps**: `make_voice` needs `kokoro` (synth) + `faster_whisper` (align). If absent, stub `make_reel.make_voice`: espeak-ng to a wav (blueprint installs espeak-ng), loudnorm+mp3 via ffmpeg, and a deterministic fake-words alignment (~330ms/word, +700ms after `.!?` — the same timing `compiler/tests/test_story_analyst.py::fake_words` uses, so clause grouping matches what analyst replay fixtures were authored against).
- **Story analyst**: `--analyst auto|llm|keywords` (or `STUDIO_ANALYST`); `STORY_ANALYST_REPLAY=<payload.json>` replays a recorded payload — fixtures are `compiler/tests/fixtures/story_analyst/*.json` wrapped as `{script, payload}`; use each fixture's own `script` as `--script-file` so conformed groups align. `--media` files become `media1..N` in order; analyst `media_ref`/`media.asset_id` must match those ids. `auto` falls back to keywords with a log line; `llm` exits 1 cleanly when unconfigured.
- Standalone: `python3 tools/story_analyst.py --selftest` (config/availability), `--script-file --alignment --replay --style --out` writes treatment.json + storyboard.json without rendering.
- **Known crash**: `runtime/editorial-runtime.js` `iconGeometry()` calls `hostM.inverse()` unguarded — an entity at `scale(0)` (e.g. the pre-op window of an analyst `GROW` op, which conforms with `from:0`) makes the CTM singular and `inspect()` throws `InvalidStateError: matrix is not invertible`, killing the render mid-capture. If renders die this way, bisect the failing seek with a playwright probe that calls `window.__em2.seek(t)` then `window.__em2.inspect()` per frame.

## Devin Secrets Needed
None.
