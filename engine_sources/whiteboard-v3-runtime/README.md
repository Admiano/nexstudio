# Whiteboard V3 Narration-Timed Runtime (reconstruction)

Runnable reconstruction of the V3 last-mile renderer recorded in provenance as
`pipeline_v3_narration_timed.py` (sha256 `c91f2bc5…f9c34`). The original file was
never persisted; this version rebuilds the documented behavior on top of the
preserved execution body so every render is reproducible from versioned source.

## What it does

`narration-timed plan → semantic compile → persistent board render + camera travel → audio/encode → QA artifacts`

- **Narration is the clock.** Each beat's `duration_seconds` (VO segment) is the scene window; drawing completes inside it and holds — the compiler's per-stroke `drawPlan` plus the comprehension doctrine do the pacing.
- **One evolving board world.** Scenes live at authored board zones; the camera travels between zones (`cluster_travel` 0.62 s moves) and finishes with a pull-back reveal of the whole accumulated board (`giant_board_journey` uses 0.72 s travel).
- **Authored-illustration board renderer.** `v3_board_renderer.py` draws the reel's visual language at explainer grade: real illustrated characters from the shipped Open Peeps pose library (`assets/open_peeps/`, V15/V16 donor lineage of the approved source bundle) rendered as progressive pen strokes with tonal fills (paper skin, ink hair/features, bold accent clothing), a 20-prop filled illustration vocabulary (envelope, document, card stack, funnel, wrench, circled check, chart, clock, phone, laptop, coin, bank, shield, gear, lightbulb, rocket, network, target, question card), thought bubbles, motion marks, ground shadows, notification pings, sparkles, small-caps captions, and an underlined bold headline on warm paper. `svg_paths.py` converts authored SVG paths to sampled polylines for the draw-on. Concepts resolve to visuals noun-first (`customer request` → envelope + ping, `human agent` → person, `AI agent` → robot, `12 min` → clock). No connector lines.
- **Audio finish.** 48 kHz pen/marker SFX bed from `sound_choreographer`, optional VO mixed via ffmpeg `sidechaincompress` (~120 ms attack / 280 ms release) and `loudnorm` to −16 LUFS / −1.5 dBTP.
- **Artifacts.** MP4 (`libx264`, yuv420p, faststart), QA contact sheet, metrics JSON, execution receipt with SHA-256 of every output.

## Second video type: kinetic type

`pipeline_kinetic_timed.py` renders the "sentence-build" caption style as a
sibling type — same plan contract (beats carry `narration`), same word-timing
sync (`--word-timings` makes audio the clock), same encode + QA + receipts.
Text is the visual: each sentence stays laid out while words flip state —
dim future → bold now (key words get a dark highlight box + white text) →
settled ink/accent with a hand-drawn swoosh underline. Emphasis detection is
a deterministic function-word/proper-noun/number rule — no keyword tables,
any domain works. Faces: `grotesk` (vendored Inter, OFL) or `marker`
(PermanentMarker — bridges to the board's hand-drawn identity).

```bash
python engine_sources/whiteboard-v3-runtime/pipeline_kinetic_timed.py \
  engine_sources/whiteboard-v3-runtime/fixtures/kinetic_demo_plan.json \
  --out-dir out/kinetic --ratio 9:16 --voiceover vo.mp3 \
  --word-timings words.json [--face grotesk|marker] [--music]
```

## Requirements

- Python 3.10+, `Pillow`, `ffmpeg`/`ffprobe` on PATH.
- The preserved V3 system package extracted: `python scripts/install-engines.py`
  (produces `engines/whiteboard-v3-system/NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE`).
  Override with `--package-root` or `WHITEBOARD_V3_SYSTEM_PACKAGE`.

## Run

```bash
python engine_sources/whiteboard-v3-runtime/pipeline_v3_narration_timed.py \
  engine_sources/whiteboard-v3-runtime/fixtures/cluster_travel_plan.json \
  --out-dir out/cluster_travel --ratio 16:9
```

Options: `--variant cluster_travel|giant_board_journey`, `--fps 25`,
`--voiceover vo.mp3`, `--keep-frames`, `--package-root`.

## Plan schema — `NexMindWhiteboardV3NarrationTimedPlanV1`

```json
{
  "production_id": "...",
  "camera_variant": "cluster_travel",
  "pacing": {"transition_seconds": 0.62, "board_reveal_seconds": 0.72},
  "voiceover": {"path": "vo.mp3"},
  "beats": [{
    "beat_id": "01_request",
    "start_seconds": 0, "duration_seconds": 4.8,
    "narration": "…",
    "scene": {
      "heroRole": "customer", "supportingRoles": ["request"],
      "semanticRelationships": [{"source": "customer", "target": "request"}],
      "screenCopy": {"primary": "A REQUEST ARRIVES"},
      "persistentObject": {"semanticEntityId": "…"}
    }
  }]
}
```

`scene` fields match the preserved semantic-execution contract consumed by
`whiteboard_compiler` (`heroRole`, `supportingRoles`, `semanticRelationships`,
`screenCopy`, `persistentObject`, `cameraAtom`, `cameraTarget`,
`artExecutionDirectives`, `p8MotionActions`, `brandExecution`).

## Tests

```bash
python -m pytest engine_sources/whiteboard-v3-runtime/tests
```

Covers plan validation, deterministic rendering, golden-frame regression at
fixed timestamps, and an end-to-end encode smoke test (skipped without ffmpeg).
