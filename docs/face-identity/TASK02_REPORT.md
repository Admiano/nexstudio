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
