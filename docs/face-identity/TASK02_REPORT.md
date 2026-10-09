# Task 02 — Distinct Illustrated Facial Identities: technical report

Branch: `devin/1791559620-face-identity-audit` (continuing from Task 01 commit 7c3830872)
Result: baseline + 3 recognizably different identities per gender, real Cycles stills, same hair/skin/lighting/expression per gender. Canonical assets untouched.

## 1. Why Task 01 morphs looked like the same person

Two findings:

- **Identity lives in the drawn ink, not the 3D silhouette.** In this style the readable face is `V59_face_art`/`V59_face_frame` (eye/brow/nose/lip/jawline strokes) plus `eyebrow001`/`eyelashes01`/`lineart_pupil.*`. Task 01 only moved head geometry — the drawn features stayed identical, so every variant read as the same person.
- **A latent render bug hid the finding.** The canonical scene stores its look as NONZERO shape-key values (`E_browUp_L/R=0.5`, `!ex-browInnerUp=0.15`, `!ex-mouthSmile*=0.5`, `$md-*` demographics ≈1). Task 01's render loop zeroed every key on participating meshes for "baseline", silently removing brows/smile and the female demographic morph — early v2 renders looked browless until canonical values were preserved (`base_vals` snapshot; only `id_*` keys toggle).

## 2. What was built (`scripts/experiments/face-identity-morphs.py` v2)

Two deformation systems, both baked as ONE additive `id_<name>` shape key per mesh (composes with `!ex-*`/`V3_*`/`A_*`/`E_*`/`$md-*` unchanged):

- **Structural field** — gaussian landmark fields on `body` (gated by `head` vgroup), `high-poly`/`lineart_*` (gated 0.20 m head radius), `V10_*` marks: skull width, forehead height, face length, jaw width, chin projection/length, cheek fullness, eye spacing/size on the skin.
- **Feature transforms on the drawn layers** — verts segmented per feature, then per-feature transforms:
  - eyes (size scale about `eye.L/R` anchors, spacing, tilt): art verts claimed by muscle vgroups (`oculi*`/`orbicularis03-04`) UNION a tight position gauss, then clipped by a hard radial gate (0.022–0.034 m) so vgroup claims can't pull stray strokes across the face; `lineart_pupil.*` and `eyelashes01` get the same eye transform.
  - brows: `eyebrow001` as its own mesh — thickness (z-scale about per-side anchors), arch (parabolic z), height, angle shear.
  - nose (width, length, tip projection): `levator05` vgroup ∪ tight box+gauss near `noseC`.
  - lips (width): `lips`/`oris*` vgroups ∪ gauss at `mouthC`, hard-gated; applied COHERENTLY to `body` lip verts and all vertex-parented mouth pieces via a shared `lip_vec` (see §3).
  - ears: `V10_ear_L/R` scale/position.
  - Per-vertex winner-take-all across feature segs — no double-displacement.

## 3. Mouth-attachment limitation — resolved (isolated + reversible)

Task 01's gap came from V9/V11 pieces rigidly tracking ONE parent body vertex while surrounding lips deformed. v2:

- `V9_lip_bound_aperture`, `V11_mouth_interior/teeth/tongue`, `teeth_base` are participants again, evaluated at their EFFECTIVE world position = parent-vertex world position + local coords. (Discovered `matrix_world` is stale for vertex-parented objects in background mode — `vertex_parent_offset()` derives it from `ob.parent_vertices` on the parent mesh; deltas write straight to local coords, which is also what vertex parenting adds at render time.)
- Lip transforms are applied through ONE shared `lip_vec` to drawn lips, body lip verts, and every mouth piece — they move together.
- Empirical bound: `lip_full` and `mouth_pos` beyond ±0.002 still separate upper/lower lip enough to expose the interior on the male head → excluded from shipped params; `lip_width` ±4–5 mm and all non-lip params are tear-free in every still shipped.
- Reversible by construction: it's a shape key on each piece; set to 0 → canonical.

The `lip_full`-is-always-last-field assumption is gone — fields are explicitly tagged (`struct`/`mouth`) and selected by tag, not position.

## 4. Identity prototypes (`scripts/experiments/face-identities.json`)

Same param set drives both genders; names are identities, not descriptors:

| | Structure | Drawn features |
|---|---|---|
| **MIRA** | long oval, high forehead, narrow chin, smaller ears | larger wide-set eyes, thin high-arched brows, narrow short nose, wider mouth |
| **THEA** | round broad face, low forehead, full cheeks | close-set almond/tilted eyes, thick straight low brows, broad nose, wider lips, larger ears |
| **RHEA** | angular square face, strong jaw + chin | narrow deep-set downturned eyes, thick angled brows, long projecting nose, thin narrow mouth |

Each differs in skull silhouette, face thirds, AND the drawn feature set — reads as three different cast members in the same style, not rescaled baselines (see sheets).

## 5. Evidence produced

`experiments/face-identity-task02/`: `female.blend`, `male.blend` (editable; `id_mira/thea/rhea` keys on 20 meshes each), per-shot PNGs, `female_front_sheet.png`, `female_threeq_sheet.png`, `male_front_sheet.png`, `male_threeq_sheet.png`, `mixed_front_sheet.png` (all 8, same scale).

## 6. Honest status vs claims

- Shape keys: every deformation above is ONE additive `id_<name>` key per mesh — no topology or rig changes.
- Separate feature meshes: none needed; all variation rides on existing meshes. Brow/lash/pupil meshes are reused as-is.
- Face/ink alignment: held in all shipped stills (verified visually, front + ¾).
- Defects observed and fixed in-loop: brow-arch field overflow, vgroup-claimed stray strokes (hard radial gates), male mouth tear at `lip_full`/`mouth_pos` (params removed; pieces now track via effective world position).
- Reproducibility: pure JSON params → deterministic keys; rerunning the script on any updated canonical .blend regenerates the identities.
- **Untested (per spec, no animation):** expression/viseme playback over the morphed identities. Keys are additive and orthogonal by construction, but lip-curve changes could interact with viseme extremes — registration under performance must be verified in a later task before production use. Neutral-still alignment ≠ performance compatibility.
- Practical distinct-count claim from Task 01 (6–10/gender) is hereby REVISED downward: feature-transform headroom on one topology supports a convincing **~4–6 distinct faces per gender**; beyond that, variants start recombining the same feature vocabulary. Hair/accessory variation (out of scope here) is the cheap multiplier.

## 7. Preservation

Read-only as before; all writes to `out/faceid2/*.blend`. Nothing merged, deployed, animated, or integrated into the cast pipeline. Stopping here for review.

# V3 addendum — after review feedback ("still the same person")

Reviewer verdict on the v2 sheets: variants still read as one person; eyebrow changes read as "eyebrows removed". This section records what v3 changed, what it achieved, and the honest ceiling.

## 8. What v3 did (same script + params, no new topology)

- **Much stronger structural fields**: head_width up to ±0.22, forehead ±0.06, face_len ±0.14, jaw_width ±0.035 with wider radii (0.05–0.06 m) so the jawline/chin/cheek **ink on `V59_face_frame`** moves with the skin — previously the silhouette field barely reached the drawn contour.
- **Feature re-draw via curve retarget** (`retarget_eyes`): eye-region art verts are moved to the nearest point on a per-identity parametric outline (`round` / `upturned` / `narrow` / `almond`, scaled by eye_w/eye_h, tilted), capped at 3.5 mm/vert to avoid rim kinks. This reshapes the stroke itself, not just its scale — the mechanism needed for "different drawings" on shared topology.
- **Brow visibility restored**: thickness kept ≥ baseline-ish (−0.25 / +0.9 / +0.45) with distinct arch/height/angle — v2's −0.85 thickness + arch changes had rendered brows effectively invisible.
- **Artifact gates**: feature-seg claims below 0.12 are snapped to zero (small edge verts were the source of stray cheek/eye strokes); `lip_corner`/`lip_shape_z` and `ear_size` beyond ±0.2 were dropped — corner hooks and extreme ear transforms produced readable defects on the male head.

## 9. Result and honest assessment

- Shipped v3 sheets: `female_front/threeq_sheet.png`, `male_front/threeq_sheet.png`, `mixed_front_sheet.png` + `*_identities_v3.blend`.
- Achieved: each identity now differs in silhouette (long-oval / round-full / square-jawed), eye shape, brow silhouette, nose line, and mouth line — systematic, reproducible variation on one topology.
- **Ceiling (the deliverable the spec anticipated in §6 of the task):** parametric deformation of a single drawn topology tops out at "systematically different proportions/features of the same cast family". It CANNOT produce "completely different people" for two structural reasons: (a) every variant shares the same stroke inventory, line weight, and feature placement grammar — the flat illustrated style compresses identity signals into those few strokes; (b) the face fill, hair, ears and frame are identical by constraint, so remaining sameness dominates perception.
- **Recommended targeted hybrid (spec-sanctioned):** keep the v3 structural field for the head shape; replace the ~6 highest-signal drawn features with authored variants as separate feature meshes — eye outline set (2–3 drawing styles), brow mesh variants, nose contour variants, mouth line variants — in the same ink material, same muscle vgroups (`oculi*`, `oris*`, `levator05`) so expressions/visemes keep working. Feature meshes are authored per-identity and swapped per variant (the `face: 0|1|2` slot already exists in `CastSpec`), instead of deforming one shared drawing. Estimated effort: 3–4 feature-mesh variants per feature per gender, authored once, reused across the whole cast.
- Remaining minor defects in v3 stills: small residual stroke marks near the eye rim on the male (retarget clamp byproducts), faint nasolabial line shifts near the mouth on all variants (intended corner-line movement, reads as style-consistent).
- Unchanged: nothing merged/deployed/animated; performance compatibility still untested (stills only, per spec).

## §10 — Task 03 resolution: use the system's own face variants (FACE env)

After three rejected custom approaches (parametric morphs, ink-segment remaps, authored
replacement strokes), the correct path turned out to be the system's own character
pipeline: `presenters_v1/scripts/facevar.py` implements designed face variants driven
by the `FACE` env var (0 default / 1 defined / 2 soft / 3 unused). It applies authored
structural deltas — jaw ±14%, chin ±9 mm, cheeks, brow placement, eye width ±10%,
face length, temples — to every `Host.*` mesh **including all shape-key data**, in
rest pose, so the variant persists through expressions and visemes by construction.

The assembled-render wrapper `scripts/cast-preview-render.sh` hardcoded `FACE=0`;
it now passes `${CAST_FACE:-0}` (behaviour unchanged when unset). Building
`CAST_FACE=1|2` through `scripts/build-character-system.py` — the same builder that
produces the canonical presenters — yields the headshots in `out/faces/`:

- female: `female_{front,threeq}_sheet.png`; male: `male_{front,threeq}_sheet.png`
- FACE 1 (defined): narrower jaw, shorter chin, lifted cheeks, lower-set brows, wider eyes.
- FACE 2 (soft): broader/rounder head, longer chin, recessed cheeks, raised brows, narrower eyes.
- Request configs: `scripts/experiments/face-requests/{female,male}_f{0,1,2}.json`
- Editable .blends: `out/faces/*.blend` (untracked, ~70 MB each).

FACE 2 already reads as a different person; FACE 1 is a milder sibling variant.
The `_VAR` table in `facevar.py` accepts new entries ('3', '4', ...) with stronger
params — additional distinct faces through the same original mechanism, and each
face pairs with the system's own hair/skin/outfit options to form full cast members.
