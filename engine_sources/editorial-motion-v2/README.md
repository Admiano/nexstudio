# Editorial Motion v3

Text-led editorial films with script-contextual illustration, authored natively for 9:16, 1:1
and 16:9. Monochrome ink on paper with one brand accent reserved for state changes.
Setup and operating instructions: `INSTALL.md`.

```
NexMind P8 treatment decision (structured, per beat)
  -> editorial_plan_compiler (packaged bundle authorities, deterministic gates)
  -> plan_<aspect>.json  x3  (+ gate_report.json)
  -> runtime/editorial-runtime.js  (execution-only, frame-addressable)
  -> MP4 x3 + captions + audio mix + contact sheets + transition strips + render manifest
```

Authority boundaries (see `EXECUTION_AUTHORITY.json`):

- **P8 owns creative direction.** The treatment names, per beat, the dominant layer
  (`TEXT | ILLUSTRATION | HYBRID | EVIDENCE | FIGURE | DATA | QUIET`), the reference pattern,
  the display copy (never rewritten), stressed words / replacement groups, the illustration
  program (form, entities, relations, word-anchored operations, carry-over) and any figure,
  media or data directive with its justification.
- **The compiler realises decisions.** It never reads script wording to route layout,
  motif, icon, figure or sound. Anything outside the bounded vocabulary raises a coded
  `TreatmentError` that P8 must replan; there is no house fallback.
- **The runtime executes plan data.** Every frame is a pure function of `(plan, t_ms)`;
  seeking is deterministic and the renderer screenshots each frame time.

## Layout

| Path | What |
| --- | --- |
| `compiler/editorial_plan_compiler/` | Treatment contracts, timing, type fitting, illustration solver (`illustration.py`), figures, sound binding, voice, plan compiler, JSON schema generator |
| `assets/illustration/` | AEV1 icon bank + `registry.json` (path, sha256, licence per `asset_ref`); rebuilt by `tools/build_illustration_registry.py` |
| `compiler/editorial_plan_compiler/authorities/` | Bundle planning authorities vendored from `EDITORIAL_TEXT_LED_BUNDLE_SOURCE.zip` with `AUTHORITY_PROVENANCE.json` (source/vendored hashes and the exact modification per file) |
| `runtime/editorial-runtime.js` + `compositions/player.html` | Plan executor and seekable player |
| `voice/elevenlabs_route.py` | `NEXSTUDIO_TTS_ROUTES_JSON` route: ElevenLabs `/with-timestamps` -> audio + character alignment; `ELEVENLABS_TRANSPORT=fixture:<dir>` replays recorded responses |
| `assets/fonts/` | Inter (OFL) and JetBrains Mono (Apache-2.0) with measured metrics |
| `assets/peeps/` | Open Peeps part library (full-body, still) extracted by `tools/import-open-peeps.py` |
| `schema/` | Explicit JSON Schemas for treatment, semantic beat, plan, alignment, sound events, media provenance, native-aspect composition |
| `fixtures/` | `water-to-thirsty/` (10 beats, recorded voice alignment + audio slices, six illustration forms, one still figure) and `reply-speed.treatment.json` (12 beats, fixture voice timings, one image + one video upload) |
| `reports/<fixture>/` | Gate report, render manifests, contact sheets and transition strips for each fixture across all three aspects |

## Run

```bash
cd engine_sources/editorial-motion-v2
python3 -m pytest -q compiler/tests                       # compiler + schema suite
cd compiler && python3 -m editorial_plan_compiler ../fixtures/water-to-thirsty/treatment.json ../out/water && cd ..
export CHROME_PATH=/path/to/chromium NODE_PATH=/path/with/playwright-core
node tools/test_runtime.js                                # browser runtime suite, all three aspects
for a in 9x16 1x1 16x9; do node tools/render_reel.js out/water/plan_$a.json out/water/render_$a; done
```

Exit codes from the compiler: `0` PASS, `3` gate FAIL, `4` treatment outside the vocabulary
(`gate_report.json` then carries the coded replan reason).

Regenerate schemas after a contract change: `cd compiler && python3 -m editorial_plan_compiler.schemas`
(a test fails when the checked-in files are stale). Re-vendor authorities from the bundle:
`python3 tools/vendor_authorities.py <bundle_root>`.

## Voice, music, sound

- Voice is the clock: word landings come from ElevenLabs character alignment. Fixture
  mode uses authored word timings; live mode needs only `ELEVENLABS_API_KEY` and the route
  declaration in `NEXSTUDIO_TTS_ROUTES_JSON` (see the route docstring).
- Music is an authored plan slot and is **silent by default**; unresolved or unlicensed
  music is never selected.
- Sound accents bind to visible events only (Sound Library V2 law): max 3 per beat,
  >= 220 ms apart, admitted assets only, deterministic selection, silence is valid.

## Media and figures

- Uploaded images/videos are probed (`ffprobe`), hashed, normalised when the browser
  cannot decode them (video -> muted VP9/WebM, image -> PNG) and placed only inside a
  governed evidence container anchored to the claim that names them. Missing media fails
  the compile; nothing is substituted.
- Open Peeps figures are still, full-body, and appear only when the treatment justifies
  emphasis; emotion, posture and facing are authored per beat and validated against the
  library.

## Not certified

`commercialCreativeCertification` is `false`. This is an execution system under P8; it makes
no claim about the creative quality of any given treatment.
