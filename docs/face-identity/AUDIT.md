# Task 01 — Baseline Audit + Facial Identity Feasibility

Branch: `devin/1791559620-face-identity-audit` (from `devin/20261006-board-scenes-option` @ ab0cb0775)
Scope: audit only + non-destructive still-render proof. No canonical asset was modified; all experiments write to separate output `.blend` files.

## A. Technical audit — verified facts (traced in the actual files, not docs)

### Canonical scenes
- `engine_sources/makehuman-lineart/presenters_v1/scenes/NEXSTUDIO_V1_FEMALE.blend`, `NEXSTUDIO_V1_MALE.blend` (Host + Guest pairs), plus `BASE_V58.blend`, `scenes/V9-V11/*_FULLBODY_15S_*.blend`, and the outfit library `character_system/scenes/{male,female}/<outfit>/character.blend` (male: bald, fisherman, fixed-left-3q, knit, native, polo, shirt, tee; female: cocktail, column, fixed-left-3q, maxi, native, qipao, sheath).

### Face system structure (probed with Blender Python in this repo's scenes)
- Each scene has `Host` + `Guest` characters; each `*.rig` armature = 163 bones (male also `Ref.rig`).
- `Host.body` ≈ 19k verts, 34 shape keys: `$md-*` MakeHuman demographic morphs, `!ex-*` expressions (`mouthSmileL/R`, `jawOpen`, `browInnerUp`, `eyeBlinkL/R`), `V3_*` visemes (`wide/round/closed/FV`), `E_*` refinements, `A_*` mouth controls. Mirrored key sets on `Host.V59_face_art` / `V59_face_frame` (~1282 verts, 29–30 keys) — the drawn ink feature layer. `Guest.body` = 14 keys (subset).
- Supporting mouth/feature meshes: `V11_mouth_interior`, `V11_teeth`, `V11_tongue`, `V9_lip_bound_aperture`, `eyebrow001` (14 `F_*` keys), `eyelashes01` (7 `F_*` keys), `teeth_base`.

### Rig / skinning (probed)
- 295 vertex groups incl. head-region `head, jaw, lips, ears, neck01-03, joint-head(-2), joint-jaw, joint-mouth, joint-l/r-eye(+target), helper-*`; face layer adds `orbicularis03/04.L/R`, `oculi01.L/R`, `risorius`, `eye.L/R`.
- Parenting (important for identity morphs):
  - `V10_ear_L/R`, `V10_jaw`, `V10_nose_L/R` = BONE-parented to `head` (8–14 verts each).
  - `V59_face_art/frame`, hair, `eyebrow001`, `teeth_base` = OBJECT-parented to rig + ARMATURE modifier.
  - `lineart_pupil.L/R` = 3-vertex-parented to `Host.high-poly` (`eye.L/R` groups).
  - `V9`/`V11` mouth pieces = VERTEX-parented to `Host.body` — they rigidly follow their single parent vertex, **not** the surrounding field (this is the one real constraint found).
- Head vgroup bbox (female, world): x ±0.114, y [-0.167, 0.054], z [1.424, 1.681]; `head` bone at (-0.42, -0.038, 1.516).

### Performance pipeline (faces are animated by shape-key fcurves, not bones)
- `scripts/cast_lip_phonemes.py` animates `V3_*`/`A_*`/`!ex-jawOpen`; `scripts/cast-gesture-timeline.py` keyframes shape keys and applies `!ex-jawOpen` to every mesh that has that key.
- **Verified:** lip sync and expressions read shape-key VALUES at render time; additive identity keys (`id_*`, value baked or keyable) compose without touching any `!ex-*`/`V3_*`/`A_*` channel. Baseline + variants render identically registered — no tearing after the mouth-region guard (below).
- Render: CYCLES, ortho `LINEART_CAMERA`, `LINEART_SOFTBOX` 240 W; `presenters_v1/scripts/headstill.py` already exists for head-cropped stills.

### Code surface already built for this
- `src/lib/cast-presets.ts`: `CastSpec.face: FaceId` ∈ {0,1,2} already exists in the spec; `scripts/cast-live3d-build.py` consumes `{c}-face{spec['face']}-{o}` GLBs. **Three face-slot support was designed in, but no `*-face*.glb` geometry exists in the repo** — the artifacts were generated historically and never committed. Morph-based keys fill exactly this slot.

## B. Experiment performed (evidence: stills + .blend test scenes)

`scripts/experiments/face-identity-morphs.py` builds landmark anchors (head vgroup bbox, lips/jaw/ears groups, nose strip, `eye.L/R` bone heads, cheek/jaw extremes), composes a gaussian-weighted delta field from a JSON parameter set (`scripts/experiments/face-variants.json`), applies the SAME world-space field as one additive `id_<name>` shape key to every participating mesh (17 objects: body, high-poly, lineart_*, V59_face_art/frame, eyebrow001, eyelashes01, V10_ear/jaw/nose), then saves to a NEW .blend and renders baseline + variants × {front, three-quarter} (Cycles, 32 samples + denoise, ortho, consistent camera/lights/neutral expression).

Participation gating: `body` via `head` vgroup mask; `high-poly`/`lineart_*` via 0.20 m radius around head center (so `lineart_shoe.*`, `lineart_lower_legs` are unaffected); small feature meshes ungated.

Constraint found and handled: the V9/V11 mouth pieces are vertex-parented to a single body vertex — structural fields crossing the lip region tear the mouth (verified visually). Two guards: (a) all non-lip fields are suppressed inside a 4 cm gaussian zone around the lip anchor; (b) `teeth_base` and `lip_full` were dropped from the experiment — morphing mouth interior/teeth is never needed for identity.

Results — `experiments/face-identity/`:
- `female.blend`, `male.blend` (editable test scenes; `id_*` keys at value 1 baked into renders, can be re-keyed)
- `female_front_sheet.png`, `female_threeq_sheet.png`, `male_front_sheet.png`, `male_threeq_sheet.png` (labeled baseline + 3 variants)
- per-shot PNGs under `female/`, `male/`

Visible differences confirmed (front views): A–angular smaller eyes / longer narrower face / heavier jaw; B–slim narrower skull, longer nose, wider eye spacing; C–soft rounder/wider head, larger eyes, higher brows, fuller cheeks. All layers (ink lines, pupils, brows, lashes, earrings, hair) stay registered — no tears, no offset artifacts.

## C. Feasibility recommendation

**Recommended: additive shape-key morphs (option A), not multi-head meshes.**

- Cheapest sound architecture: zero new rigs, zero new skin weights, zero changes to `cast_lip_phonemes.py`/`cast-gesture-timeline.py`/presets pipeline. One key per identity composes with every `!ex-*`/`V3_*`/`A_*` channel by construction.
- Reproducible: identities are parameter sets in `face-variants.json` — versioned, reviewable, cheap to regenerate on every canonical .blend update.
- Fits the existing `face: 0|1|2` CastSpec slot directly (id key = face index), including the historical `-faceN-` GLB naming the build script already expects.
- Multi-head (option B) is unnecessary cost: duplicate skinning + per-head hair re-fitting + per-head expression key-set maintenance for a line-art style where the drawn features — not raw topology — carry identity. Morphs move those drawn layers in lockstep (verified).
- Hybrid only where morphs can't reach: hairline/hair silhouette and truly different topology (e.g. hooked nose profile, strong brow ridge) — those are per-identity *mesh additions* (new `V10_*` mark meshes or hair variants), not new heads.

**Practical identity count:** the style hides fine structure — distinctiveness comes from feature placement + silhouette. Comfortably **6–10 clearly distinct faces per gender** on one topology before param sets start colliding visually; more with hair variation. Honest limit observed: subtlety is inherent — the illustrated style compresses geometry differences, so param sets need to be bold (as in variant C) and should be validated per-variant by a still render like the ones shipped here.

**Per-video cost: none.** Keys are static per cast selection; no runtime morphing.

## D. Preservation report

Read-only (inspected, never saved over):
- `presenters_v1/scenes/*.blend` (V1 male/female canonical), `character_system/scenes/**`, `scenes/V9-V11/**` — opened with `blender -b`, all writes went to `out/faceid/*.blend`.
- `scripts/cast_lip_phonemes.py`, `scripts/cast-gesture-timeline.py`, `scripts/cast-live3d-build.py`, `src/lib/cast-presets.ts`, `scripts/build-character-system.py` — read only.
- Rigs, skins, `!ex-*`/`V3_*`/`E_*`/`A_*` key sets, gestures/motion libraries, hair, clothing, accessories, skin-tone presets: untouched.

New files only (this branch):
- `scripts/experiments/face-identity-morphs.py`, `scripts/experiments/face-variants.json`
- `experiments/face-identity/` — 2 test .blends + rendered stills + labeled sheets
- `docs/face-identity/AUDIT.md` (this file)

No merges to the baseline branch; nothing deployed; no animation/video renders were produced (stills only, per spec).

## E. Stopping point (per spec)

Audit + isolated commit + still-image evidence delivered. Awaiting review/approval before any production implementation of identity morphs (e.g. wiring `id_*` keys into the cast build/bake path or generating the committed `-faceN-` GLB set).
