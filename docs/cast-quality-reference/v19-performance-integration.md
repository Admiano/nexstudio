# Native continuous-master performance integration V19

The repaired core rejects invalid master timing, incomplete word alignment, nonfinite geometry/attention, and illegal root attention. Speech sampling prioritises hard silence and non-speaker ownership. The executor fits an action into the supplied directive window, rather than letting its original length extend the performance.

The native director reuses the audited conversation floor, reflective response, social/listener events, attention, semantic selection and minimum-jerk transitions. It binds only the existing MakeHuman bones and facial keys. The original appearance meshes and materials are retained. Every request references one unchanged PCM master with exact SHA-256 and duration and complete word/phoneme coverage; WAV identity is verified before baking. Test narration has actual offline English forced word/phoneme alignment, not estimated word durations.

## Admission

- Native front host demonstrations: canonical female bun/cocktail and male polo/short hair; full clips require rendered review.
- Native hand binding: right-hand low micro phrase only. Existing native curves supply the standing phrase; count, precision, contrast, left-hand and physical screen pointing remain closed until separately reviewed. Logical selector support does not admit a physical pose.
- Seated conversation: separate demonstration scene. Original rigged trousers replace a frozen standing preview-fit mesh, rigid footwear follows native feet, native anatomical segments retain their lengths, and the sole keeps its original orientation. Lap contacts use a two-link contact solve baked as FK, with no anatomy scaling. Full-body footwear and seated garment certification remain pending until their rendered review.
- Listener/non-speaker speech closes across every frame, with semantic blinks, small nods/reactions and eyes-leading attention. No sinusoidal arm waving or root attention.
- Prop/screen contact, locomotion, all wardrobe/hair variants and interruption audio performances require separate native proof. Planner tests are not a substitute for those proofs.

## Use

Install `scripts/requirements-performance.txt` with Python 3.12 for local alignment. Blender 5.2 is used for native baking/rendering.

`scripts/cast-performance-align.py master.wav transcript.txt alignment.json` produces complete acoustic word/phoneme timing for a provided WAV and transcript. `cast-performance-director.py request.json plan.json` compiles the continuous master. The native exporter runs inside Blender:

```
blender -b --python scripts/cast-performance-native.py -- approved-native.blend request.json host.blend front
```

`front`, `left3q`, and `right3q` are fixed cameras. The exporter preserves one complete sound strip and packs the master audio.

The existing assembled renderer has an opt-in server-owned `CAST_PERFORMANCE_DIRECTOR_PATH` hook, activated only with `--native-performance`. Inheriting an environment variable cannot change an ordinary cached preview. No client filesystem path is accepted, no preview worker request schema changes, and ordinary previews keep the previous path. Missing native keys, a mismatched character, an altered master, a frame beyond its duration or an uncertified seated preview fails explicitly. This hook does not deploy a production speech/video UI.

## Evidence

See the repaired core, native scene verification JSON, full frame renders, previews and integration status report. The report distinguishes code tests, scene numerical checks and visual admission.
