# Whiteboard V3 Narration-Timed Runtime (reconstruction)

Runnable reconstruction of the V3 last-mile renderer recorded in provenance as
`pipeline_v3_narration_timed.py` (sha256 `c91f2bc5…f9c34`). The original file was
never persisted; this version rebuilds the documented behavior on top of the
preserved execution body so every render is reproducible from versioned source.

## What it does

`narration-timed plan → semantic compile → persistent board render + camera travel → audio/encode → QA artifacts`

- **Narration is the clock.** Each beat's `duration_seconds` (VO segment) is the scene window; drawing completes inside it and holds — the compiler's per-stroke `drawPlan` plus the comprehension doctrine do the pacing.
- **One evolving board world.** Scenes live at authored board zones; the camera travels between zones (`cluster_travel` 0.62 s moves) and finishes with a pull-back reveal of the whole accumulated board (`giant_board_journey` uses 0.72 s travel).
- **Skin resolution shim.** `whiteboard_pil_adapter._semantic_prim` is wrapped so known noun classes (person, phone, document, screen, package, wallet, queue…) resolve to the preserved pictogram skins instead of the generic object rect — approximating the V3 icon vocabulary without editing frozen source.
- **Audio finish.** 48 kHz pen/marker SFX bed from `sound_choreographer`, optional VO mixed via ffmpeg `sidechaincompress` (~120 ms attack / 280 ms release) and `loudnorm` to −16 LUFS / −1.5 dBTP.
- **Artifacts.** MP4 (`libx264`, yuv420p, faststart), QA contact sheet, metrics JSON, execution receipt with SHA-256 of every output.

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
