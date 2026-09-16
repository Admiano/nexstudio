# Editorial Motion v3 — install and operate

Everything in this folder is the system: compiler, runtime, assets, fonts, schemas,
fixtures, tools and the proof renders. No other part of NexStudio is required to compile
and render a film.

## 1. Requirements

| Need | Version used | Why |
| --- | --- | --- |
| Python | 3.10+ (stdlib only for compile) | `editorial_plan_compiler` |
| `pytest` | 7+ | compiler suite |
| `Pillow` | 10+ | only `tools/make_fixture_assets.py` and the offline Open Peeps rig tool |
| Node.js | 18+ | runtime tests and renderer |
| `playwright-core` | 1.47.2 (`npm install`) | drives Chrome for tests and frame capture |
| Chrome / Chromium | 120+ (new headless) | executes the runtime; screenshots frames |
| `ffmpeg` + `ffprobe` | 4.4+ | media probing/normalising, audio mix, MP4 encode |

```bash
cd editorial-motion-v2
python3 -m pip install pytest pillow
npm install                       # playwright-core only
```

Browser: either point at a binary (`CHROME_PATH=/usr/bin/chromium`) or at an already
running Chrome with remote debugging (`CDP_URL=http://localhost:9222`; start one with
`chromium --headless=new --remote-debugging-port=9222`). Every tool accepts both.

## 2. Smoke test (5 minutes)

```bash
python3 -m pytest -q compiler/tests                                   # 31 passed
cd compiler && python3 -m editorial_plan_compiler ../fixtures/water-to-thirsty/treatment.json ../out/water && cd ..
CHROME_PATH=/usr/bin/chromium node tools/test_runtime.js              # ~318 checks, all three aspects
CHROME_PATH=/usr/bin/chromium node tools/render_reel.js out/water/plan_9x16.json out/water/render_9x16
```

`render_9x16/` then holds `fixture-water-to-thirsty_9x16.mp4`, `contact_9x16.png`,
`transitions_9x16.png`, `captions_9x16.srt`, `audio_9x16.wav`, every frame as PNG and
`render_9x16.json` (plan hash, mp4 hash, page errors, `native_profile`). Expected against
`reports/water-to-thirsty/`.

## 3. Producing a film

```
treatment.json  --compile-->  plan_9x16.json / plan_1x1.json / plan_16x9.json + gate_report.json
plan_<aspect>.json  --render-->  MP4 + sheets + manifest
```

1. **Author the treatment** (this is NexMind P8's job in Studio; by hand for a test).
   Schema: `schema/NexStudioEditorialTreatmentV2.schema.json`. Study
   `fixtures/water-to-thirsty/treatment.json` — film-level `brand` (`ink`, `paper`, `accent`),
   `typography`, `voice`, `media_library`; every beat carries:
   - `narration` (what the voice says) and `display_units[]` (display copy, role
     `hero|support|qualifier`, `anchor_word`, `semantic_role`, optional `stress` words and
     `replace_group`) — display copy is never rewritten;
   - `beat_type`, `dominant_layer`, `pattern`, `energy`, `complexity`, optional `min_duration_ms`;
   - optional `illustration`: `form`, `entities[]` (`kind`, `glyph`, `size`, `label`,
     `asset_ref`, `params`), `relations[]`, `program[]` of ops each anchored to exactly one of
     `{"word": ...}`, `{"unit": n}`, `{"offset_ms": n}`, plus `carry_from` / `persist_to`;
   - optional `figure` (still full-body Open Peeps: emotion, posture, facing, justification),
     `media` (an upload anchored to the claim naming it), `data`.
   - `voice.source`: `RECORDED` (alignment + audio you already have), `ROUTE` (ElevenLabs via
     Studio's `NEXSTUDIO_TTS_ROUTES_JSON`, see `voice/elevenlabs_route.py`), or `FIXTURE`
     (synthetic cadence, never commercial output).
   Icons: only `asset_ref` values present in `assets/illustration/registry.json` resolve.
   Run `python3 tools/build_illustration_registry.py` after adding SVGs to `assets/illustration/aev1/`.

2. **Compile** — `cd compiler && python3 -m editorial_plan_compiler <treatment.json> <out_dir>`.
   Exit `0` PASS, `3` gate FAIL (`gate_report.json` lists coded failures per aspect/beat),
   `4` treatment outside the vocabulary (coded replan reason for P8). Nothing is auto-fixed.

3. **Render** — `node tools/render_reel.js <plan_<aspect>.json> <out_dir>` once per aspect.
   Exit `2` if the page raised any error. Output MP4 sizes: 1080x1920, 1080x1080, 1920x1080.

4. **Preview interactively** — serve the folder (`python3 -m http.server 8080`) and open
   `http://localhost:8080/compositions/player.html?plan=../out/water/plan_9x16.json`
   for a seekable player.

## 4. Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `CHROME_PATH` | tests, renderer | launch this Chrome binary headless |
| `CDP_URL` | tests, renderer | attach to a running Chrome instead (default `http://localhost:29229`) |
| `NEXSTUDIO_SOUND_LIBRARY_ROOT` | compiler | override the Sound Library V2 root for accent one-shots; default is the bundled `sound-library/` (absent = silent accents, `SOUND_LIBRARY_MISSING` warning, still PASS) |
| `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID` | `voice/elevenlabs_route.py` | live voice with character timestamps |
| `ELEVENLABS_TRANSPORT=fixture:<dir>` | route | replay recorded responses (tests) |

## 5. Laws the code enforces (do not work around them)

- The runtime never reads narration, never infers, never routes keyword→icon and has no
  fallback art; unsupported plan data fails closed. Creative decisions live in the treatment.
- Each aspect is authored natively from its own composition authority — never a crop/scale of another.
- Monochrome ink; the single `brand.accent` may appear only through state-change ops
  (`FILL/INK/CONNECT/EMIT/TRAVEL/GROW/SWAP/STRIKE/COUNT`). The runtime suite asserts this.
- Copy is fitted with real font metrics; a word that cannot fit fails (`TYPE_WORD_TOO_WIDE`) rather than being shrunk below the floor or broken.
- Every frame is `f(plan, t_ms)`; seeking anywhere yields the identical frame.
- Media, icons, fonts and voice carry sha256 + licence provenance into the plan.

## 6. Contents

```
compiler/editorial_plan_compiler/   contracts, timing, typefit, illustration, figures, media, sound, voice, compiler, schemas
compiler/editorial_plan_compiler/authorities/   vendored NexMind planning authorities (+ AUTHORITY_PROVENANCE.json)
compiler/tests/                     pytest suite
runtime/editorial-runtime.js        EDITORIAL_RUNTIME_V3.0 (execution only)
compositions/player.html            seekable player used by tests and renderer
styles/                             player CSS
assets/fonts | assets/illustration | assets/peeps
schema/                             7 JSON Schemas (regenerate: cd compiler && python3 -m editorial_plan_compiler.schemas)
fixtures/water-to-thirsty           benchmark treatment + recorded voice alignment/audio
fixtures/reply-speed.treatment.json + fixtures/assets   upload-media fixture
tools/                              test_runtime.js, render_reel.js, registry/fixture builders, vendor_authorities.py, import-open-peeps.py
voice/elevenlabs_route.py           TTS route
sound-library/                      Sound Library V2 (269 CC0 one-shots + registry, licences, SHA256SUMS); music slot stays silent until a rights-clean source is chosen
reports/                            proof renders (gate reports, contact sheets, transition strips, manifests)
EXECUTION_AUTHORITY.json            authority boundary declaration
```
