# charpack-lineart

Grease-Pencil line-art renderer for the Blender Studio character rigs — ink
outline + flat fills, pose/expression control via CLI args. Developed in the
"Show All 30 Characters" session against the Rain rig; verified to reproduce
`outputs/rain_v25.png` pixel-for-pixel on Blender 5.2.1 LTS.

## Layout

- `render_lineart_gp.py` — headless stills renderer (bpy script)
- `podcast_char.py` / `podcast_char2.py` — line-art podcast performers
  (recovered verbatim from the podcast session): deterministic python curves
  driving the CloudRig controls — seats, 3/4 heads, gaze saccades, blinks,
  brows, visemes, finger chains, shoulder-led gesture arm, listener nods,
  breathing. v2 adds face + hands + posture performance (`still`/`anim`,
  `closeup` modes; adapters for `rain` and `snow`). Per-frame:
  `blender -b <char.blend> --python podcast_char2.py -- <char> <outdir> <f0> <f1>`
- `rain_performer.py` — front-facing presenter (Synthesia-style avatar).
  Score-driven: a JSON list of timed speech segments goes through a
  VITA-grammar semantic director (stillness-first, <=2 deliberate
  gestures/10s, >=3s spacing, avoid-repeat-last-3, torso->shoulder->elbow->
  wrist flow lag, hands subordinate to face, hand-safety zone) that
  schedules parametric gestures (wave/present/emphasis/question/ack) over
  an always-on idle layer (breathing, weight shift, gaze saccades, blinks,
  viseme lipsync from generated syllable timing, per-segment moods).
  Uses the v26 palm/arm proportion fixes (PALM_THIN/HAND_SCALE).
  `scores/demo_presenter.json` is the reference score.
  `blender -b "Rain_x/Rain v3.3/rain_v3.2.blend" --python rain_performer.py --
   scores/demo_presenter.json <outdir> [still] [bust|waist|closeup] [f0 f1]`
- `Rain_x/Rain v3.3/` — Rain character rig, unmodified upstream pack
  (`rain_v3.2.blend` + `textures/`); podcast_char2 also needs the Snow rig
  (download from studio.blender.org/characters/snow)
- `outputs/` — latest renders: `rain_v26.png` (full), `v26_hands.png` (hand crops),
  `rain_v25.png` / `v25_hands.png` (pre-palm-proportion pass, kept for reference),
  `performer_demo/` — rain_performer sample frames

## Usage

```bash
blender -b "Rain_x/Rain v3.3/rain_v3.2.blend" --factory-startup \
  --python render_lineart_gp.py -- out.png 0.33
```

Args after `--` (positional, all optional with tuned defaults):

| # | arg | default | meaning |
|---|-----|---------|---------|
| 0 | out_png | /tmp/rain_gp.png | output path |
| 1 | crop_bottom_frac | 0.42 | bottom crop fraction |
| 2 | EYELID_DROP | -0.007 | lid lower/raise |
| 3 | PUPIL_SCALE | 2.4 | pupil size factor |
| 4 | HEAD_TILT | 3.0 | head tilt deg |
| 5 | UA_ANGLE | 80.0 | upper-arm drop deg |
| 6 | PRONATE | 32.0 | forearm pronation deg |
| 7 | BROW_THIN | 0.62 | brow thickness factor |
| 8 | LIP_W | 0.4 | lip line weight |
| 9 | LIP_TICK | 1.0 | mouth corner tick |
| 10 | LIP_SEAM_WHITE | 1 | seam faces skin-white |
| 11 | mode | — | `face` or `hands` pass |
| 12+ | LIP_OCC, SMILE_UP/OUT, LIP_TUBE, HAIR_GREY/CREASE, HAND_CREASE, PONY_SWING, ELBOW_BEND, ARM_SLIM, FORE_TWIST, WRIST_LEAN | see header | pose/detail tuning |
| 24 | PALM_THIN | 0.65 | palm depth scale, rest space — the rig's palm is ~0.63× as deep as it is wide vs a ~0.35 canon; 0.65 pulls palm+finger skin toward the palm plane |
| 25 | HAND_SCALE | 0.92 | uniform whole-hand scale — stock hand/forearm is 0.80 (top of the 0.72–0.78 canon); 0.92 → 158mm hand, 0.74× forearm |

## License

The Rain rig is CC-BY — required credit: **Rain Rig (CC) Blender Foundation |
studio.blender.org** (https://studio.blender.org/characters/rain/v3/).
