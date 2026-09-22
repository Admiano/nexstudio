# charpack-lineart

Grease-Pencil line-art renderer for the Blender Studio character rigs — ink
outline + flat fills, pose/expression control via CLI args. Developed in the
"Show All 30 Characters" session against the Rain rig; verified to reproduce
`outputs/rain_v25.png` pixel-for-pixel on Blender 5.2.1 LTS.

## Layout

- `render_lineart_gp.py` — headless renderer (bpy script)
- `Rain_x/Rain v3.3/` — Rain character rig, unmodified upstream pack
  (`rain_v3.2.blend` + `textures/`)
- `outputs/` — latest renders: `rain_v25.png` (full), `v25_hands.png` (hand crops)

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

## License

The Rain rig is CC-BY — required credit: **Rain Rig (CC) Blender Foundation |
studio.blender.org** (https://studio.blender.org/characters/rain/v3/).
