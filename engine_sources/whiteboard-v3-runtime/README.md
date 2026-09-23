# Whiteboard V3 Narration-Timed Runtime (reconstruction)

Runnable reconstruction of the V3 last-mile renderer recorded in provenance as
`pipeline_v3_narration_timed.py` (sha256 `c91f2bc5…f9c34`). The original file was
never persisted; this version rebuilds the documented behavior on top of the
preserved execution body so every render is reproducible from versioned source.

## What it does

`narration-timed plan → semantic compile → persistent board render + camera travel → audio/encode → QA artifacts`

- **Narration is the clock.** Each beat's `duration_seconds` (VO segment) is the scene window; drawing completes inside it and holds — the compiler's per-stroke `drawPlan` plus the comprehension doctrine do the pacing.
- **One evolving board world — the giant-board journey (default).** One continuous drawing on a huge canvas: a hand-lettered heading inks first, then every element (icon + caption + marks) is drawn one at a time along a flowing left-to-right path that wraps row to row, while the camera chases the pen tip and glides to the next element as a gap approaches. The finish is a pull-out reveal of the literal infographic the video traveled. `cluster_travel` (shared-zone scenes, mosaic reveal) remains available via plan `camera_variant` or `--variant`.
- **Authored-illustration board renderer.** `v3_board_renderer.py` draws the reel's visual language at explainer grade: real illustrated characters from the shipped Open Peeps pose library (`assets/open_peeps/`, V15/V16 donor lineage of the approved source bundle) rendered as progressive pen strokes with tonal fills (paper skin, ink hair/features, bold accent clothing), a 20-prop filled illustration vocabulary (envelope, document, card stack, funnel, wrench, circled check, chart, clock, phone, laptop, coin, bank, shield, gear, lightbulb, rocket, network, target, question card), thought bubbles, motion marks, ground shadows, notification pings, sparkles, small-caps captions, and an underlined bold headline on white paper. `svg_paths.py` converts authored SVG paths to sampled polylines for the draw-on. Concepts resolve to visuals noun-first (`customer request` → envelope + ping, `human agent` → person, `AI agent` → robot, `12 min` → clock). No connector lines.
- **Audio finish.** 48 kHz pen/marker SFX bed from `sound_choreographer`, optional VO mixed via ffmpeg `sidechaincompress` (~120 ms attack / 280 ms release) and `loudnorm` to −16 LUFS / −1.5 dBTP.
- **Artifacts.** MP4 (`libx264`, yuv420p, faststart), QA contact sheet, metrics JSON, execution receipt with SHA-256 of every output.

## Second video type: kinetic type

`pipeline_kinetic_timed.py` renders the "sentence-build" caption style as a
sibling type — same plan contract (beats carry `narration`), same word-timing
sync (`--word-timings` makes audio the clock), same encode + QA + receipts.
Text is the visual: each sentence stays laid out while words flip state —
dim future → bold now (key words get a dark highlight box + white text) →
settled ink/accent with a hand-drawn swoosh underline. Emphasis detection is
a deterministic function-word/proper-noun/number rule plus a per-sentence
cap — no keyword tables, any domain works. Faces: `condensed` (default —
vendored Barlow Condensed, OFL; the heavy condensed display face that
fills lines at 9:16), `grotesk` (vendored Inter), or `marker`
(PermanentMarker — bridges to the board's hand-drawn identity).
Word-state changes are eased: the highlight box grows in with a slight
overshoot, the active-word pop settles with a small dip, sentence
transitions ease in-out, and the swoosh draws in with eased progress.
Themes:
`light` (white paper) or `dark` (near-black, accent highlight box).
`--accent #RRGGBB` recolors the brand accent (swooshes, settled key words,
highlight box) — defaults to the plan's `brandAuthority.accent` (#0052FF).
Every word is guaranteed on-frame — the typesetter auto-shrinks to fit
width and height, and the sentence-entry rise is capped so tall blocks
never dip below the frame edge.

```bash
python engine_sources/whiteboard-v3-runtime/pipeline_kinetic_timed.py \
  engine_sources/whiteboard-v3-runtime/fixtures/kinetic_demo_plan.json \
  --out-dir out/kinetic --ratio 9:16 --voiceover vo.mp3 \
  --word-timings words.json [--face grotesk|marker] \
  [--theme light|dark] [--accent #RRGGBB] [--watermark TEXT] [--music]
```

### Diagram type — cumulative annotated canvas

`pipeline_diagram_timed.py` renders the "build-the-diagram" explainer style
(reference: annotated whiteboard explainers). One persistent board:
hand-lettered headline + accent underline on top, a hero illustration at
center, then each beat adds elements — numbered stage labels, icons,
callout chips with pin arrows, connector arrows — that draw on
stroke-by-stroke. Elements of earlier beats stay on the board muted while
the active beat draws in full ink/accent; an optional summary strip closes
the piece. Same plan contract, word-timing sync, per-stroke scratch SFX,
encode + QA + receipts. Elements are declared per beat under `diagram`
(see `fixtures/diagram_demo_plan.json`); art resolves through the same
asset registry — unresolved concepts fall back to lettered chips (the
hybrid artist slot).

```bash
python engine_sources/whiteboard-v3-runtime/pipeline_diagram_timed.py \
  engine_sources/whiteboard-v3-runtime/fixtures/diagram_demo_plan.json \
  --out-dir out/diagram --ratio 16:9 --voiceover vo.mp3 \
  --word-timings words.json [--theme light|dark] [--accent #RRGGBB]
```

Both renderers default to white paper + black ink. `--theme dark` swaps to
a black board with white ink (the hand sprite is unchanged); `--accent`
recolors brand accents, and `--page-size N` re-inserts erase page turns
every N flow cells (9:16 defaults to 3 per scene).

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
