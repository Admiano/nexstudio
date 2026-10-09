# NexStudio V2 — Signature Sculpted Female Experiment

**Checkpoint:** 2026-10-09, **Rev08.** Status: **real Blender prototype, NOT artistically approved**.

Protected isolated branch forked from `devin/20261006-board-scenes-option`. The V1 character system, original MakeHuman archive and parallel paper-character work remain unchanged.

## Source and reconstruction
- Blender 5.2.0 was recovered from the user's Library and used for every delivered still.
- Female character donor: `NEXSTUDIO_V18_FEMALE_NATIVE_SCENES.zip` → `native/female/native/refined.blend`.
- Inspected technical base: **163 bones**, **19,158 skin vertices**, **35 facial shape keys**.
- Hybrid approach: inherited source rig and body topology, separate procedural V2 geometry/materials.

## Milestone evidence
- **Visual Rev08:** different continuous sculptural hair sheet (3,500 verts), coat with distinct sleeves and panels, slim continuous custom boot upper and outsole; saved and reopened as an editable `.blend`.
- **Seven native Blender/Cycles previews:** neutral front, 3/4, side, face, hair, coat and mesh-edge QA. No image generation.
- **Head binding proof:** 21 earlier hair meshes and 12 facial overlays were attached to the inherited head bone without measurable neutral displacement. The latest smoother hair study uses fewer meshes and preserves its head attachment.
- **Separate Rev07 sleeve experiment:** 800 total garment vertices across four sleeve/cuff meshes received V1 source weights, with no visible neutral-render regression. The posed sleeve moves with the arm, **but the jacket shoulder and seam clearances are not solved**. This experiment is **not merged into the Rev08 visual candidate**.
- **Integrity:** 52 objects; recoverable source body/rig; two new boot meshes; no required external bitmap files; seven verified view renders.

## Deliverable
A **46,175,197-byte verified ZIP** named `NEXSTUDIO_V2_SIGNATURE_FEMALE_REV08_CHECKPOINT_20261009.zip`, containing editable visual and rigging-test scenes, Blender construction/QA scripts, full native previews, rigging stills, provenance and technical reports, is provided as a ChatGPT conversation attachment. The archive passed a complete ZIP CRC integrity check. **The binary ZIP and `.blend` files are NOT uploaded to GitHub.** These branch docs identify the deliverable, they do not substitute for it.

## Quality gate — still BLOCKED
The face is predominantly a restyled source face, not a distinctive premium sculpt; the coat remains too rigid; hair and costume need professional surface design. New outfit skinning, collisions, expressive visemes, poses, modular DNA, export and production integrations are NOT certified. Do not merge this prototype into V1, publish it as final, or claim it matches the image benchmark. Keep developing the hero until the user approves the visual design.

## Reproduction
Open the package's `scenes/NEX_V2_SIGNATURE_FEMALE_REV08_SHOES_TEST.blend` in Blender 5.2+, use the camera `REVIEW_CAMERA`. See `reports/REV08_CHECKPOINT_REPORT.md` for exact code sequence, QA tests, asset provenance and limitations.
