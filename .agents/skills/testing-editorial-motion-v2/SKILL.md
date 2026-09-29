---
name: testing-editorial-motion-v2
description: How to end-to-end test the editorial-motion v2 engine (compile→render→verify) in nexstudio — render pipeline invocation, plan layout, coordinate/timing conventions, ROUTE voice wiring, and audio verification.
---

# Testing editorial-motion v2 (engine_sources/editorial-motion-v2)

## E2E entry point
`python3 tools/regression_pack.py --fixture <name> --aspects 16x9 --out out/e2e` compiles the treatment, renders real frames + mp4 via `tools/render_reel.js` (frame range sharded across headless Chrome workers), mixes audio, and gates pixel health (blank/frozen/page-errors/music/captions/native-profile). Fixtures = `fixtures/<name>/treatment.json`; aspect plans land in `<out>/<fixture>/plan_<aspect>.json`, frames in `frames_<aspect>/fNNNNN.jpg` (q100; `--frame-format png` for lossless), mixed track in `audio_<aspect>.wav`, render manifest in `render_<aspect>.json`.

## Environment
- node is NOT on PATH by default: `export PATH=$HOME/.nvm/versions/node/v24.19.0/bin:$PATH`.
- Chrome runs with CDP at http://localhost:29229; tools/test_runtime.js attaches to it. render_reel.js prefers a Chrome binary (`--chrome`, `CHROME_PATH`, or `google-chrome` on PATH) and launches N isolated headless workers (`--workers`, default min(8, cores)); only without a binary does it fall back to the CDP browser with one foreground worker. Don't run two CDP consumers at once — a CDP render needs foreground (`page.bringToFront`).
- render_reel.js writes `<film>_<aspect>.mp4` (CRF 20 master) and `<film>_<aspect>_web.mp4` (CRF 23 playback; `--web-crf 0` to skip); `render_<aspect>.json` carries `render.{capture_s,encode_s,total_s,workers}` and `mp4_bytes` for benchmarking.
- pytest/scientific python lives at `/home/ubuntu/.pyenv/versions/3.12.13/bin/python` (system `python3` is 3.10 stdlib-only; routes declared with `python3` in NEXSTUDIO_*_ROUTES_JSON must therefore be stdlib-only).
- python3 has numpy+PIL+pytest; ffmpeg/ffprobe on PATH. Sound accents only bind if a sound library resolves — `compiler/../sound-library/` or `engines/sound/NexStudio_Sound_Library_V2_Production` under the repo root, or `NEXSTUDIO_SOUND_LIBRARY_ROOT`. Without it plans get `SOUND_LIBRARY_MISSING` and zero accents.

## Compiled-plan layout (needed to write probes)
- Illustration ops live at `beat.illustration.program` in the **treatment**, but at `beat.illustration.ops` in the **compiled plan** (top-level `illustration.ops` is empty in treatments). Ops carry `start_ms`/`end_ms` **beat-local**; film time = `beat.start_ms + op.start_ms`.
- `plan.canvas` (e.g. 1280×720) vs `plan.output` (e.g. 1920×1080, `scale: 1.5`): entity/relation bboxes are canvas coords; rendered frames are output-sized → multiply by `output.scale` for pixel regions.
- Accents: `beat.sound.accents` entries have `beat_at_ms` and `film_at_ms`, `asset_id`, `path`, `sha256`, `license`, `gain_db`. `beat.sound.silenced` lists out-competed candidate events — a silenced event still proves the compiler emitted the candidate.
- Accent law constants in `compiler/editorial_plan_compiler/sound.py`: `MAX_ACCENTS_PER_BEAT=3`, `MIN_ACCENT_GAP_MS=220`.
- `plan.music` carries `status` (BOUND_CC0), `asset_id`, `moods`, `bpm`, `mood_request`, `sha256`, `path`.

## Voice / TTS route testing (voice.source=ROUTE)
- `resolve_voice` (`compiler/editorial_plan_compiler/voice.py`) dispatches per-beat narration to `services/studio-family-engines/audio_provider.py::generate_audio`, which reads `NEXSTUDIO_TTS_ROUTES_JSON`, filters `commercialUseAllowed`+`credentialEnv`, tries routes in `-priority` order, and normalizes output to 48kHz stereo `pcm_s24le` at the caller's `out` path.
- Routes run inside `generate_audio`'s TemporaryDirectory, deleted on return — a route must honor `payload.alignmentOutputPath` (voice.py sends `<out>.alignment.json`) so its alignment sidecar survives; a dangling `providerEvidence.alignmentPath` REPLANs `ROUTE_ALIGNMENT_MISSING`.
- Provenance lands at `plan.voice.segments[].evidence.{route_id,rights,provider}` and `plan.provenance.voice_timing`; per-beat word timings in `plan.beats[].words` come from the route's reported alignment sidecar.
- Route commands in `.env.example` are repo-root-relative — run the compiler with cwd=repo root (regression_pack runs with cwd=compiler, which breaks relative route commands), or declare absolute paths in your routes JSON.
- `CHATTERBOX_TRANSPORT=fixture:<audio-file>` replays a file instead of running chatterbox-tts/torch (not installed on test box); its alignment is marked `alignmentSource: EVEN_SCHEDULE_FROM_GENERATED_AUDIO`. Good speech fixture source: `fixtures/vo-joe/voice.mp3` (real VO); cut ~4s with ffmpeg for per-beat use.
- Route failure path: no transport + package missing → route exit 2 `CHATTERBOX_PACKAGE_MISSING` → `generate_audio` raises `AudioRouteUnavailable('<route>:exit-2')` → coded `NARRATION_ROUTE_UNAVAILABLE` REPLAN (TreatmentError in the compiler; `AdapterReplan` in `sound_mix.py`).

## Runtime probing (in-page)
`tools/test_runtime.js` shows the pattern: serve the repo over a tiny http server (`/fs/<abs>` for out-of-tree paths), mount `runtime/editorial-runtime.js`, `EditorialRuntime.createEditorialFilm(plan, mount, {fontBase, assetUrl})`, `await film.ready`, then `film.seek(ms)` is deterministic; entity video nodes are found via `[data-media-asset="<asset_id>"] video`. Video currentTime contract: `currentTime ≈ trim.start + (lt − enter_ms)/1000`.

## Verifying rendered output
- Wipe/pixel claims: measure dark-pixel density `(img < ~120).mean()` inside scaled stroke bboxes at pre/mid/post-op film times; wiped strokes must return to baseline while non-wiped controls stay elevated.
- Audio: `wave`+numpy on `audio_<aspect>.wav` — compare 150ms RMS at each accent's `film_at_ms` vs a window ~300ms before; `render_<aspect>.json` `audio.accents` must equal the plan's accent total (render throws on missing file/sha256/license, so a PASS means every bound accent was mixed).
- Voice truth in the mp4: `render_reel.js` always writes `stems_<aspect>/{voice,sfx,music}.wav`; `manifest.audio.loudness.voice_lufs` > ~-60 means a real voice bus (silence ≈ -70). Strongest check: RMS of `voice.wav` inside each narrated beat's `[start_ms, start_ms+duration_ms]` window (expect ≈ -20s dB for speech) vs windows outside all segments (expect ≈ -180 dB digital silence); the mp4's aac track can be extracted and windowed the same way. `ffmpeg -i <mp4> -filter_complex showwavespic -frames:v 1 waveform.png` gives a visual.
- `compiler/tests` via `cd compiler && python3 -m pytest -q tests`; runtime suite via `node tools/test_runtime.js` (8 fixtures × 3 aspects).

## Devin Secrets Needed
None. (A real `ELEVENLABS_API_KEY` would additionally exercise the premium route priority path; without it the route is correctly skipped by `credentialEnv` gating.)
