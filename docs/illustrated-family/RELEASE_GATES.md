# NexStudio V1 Illustrated Family — Non-Destructive Release Gates

Source authority: `devin/20261006-board-scenes-option` at `1216552afc8eb1a756ee5451f8949a9cde39bd5e`.

**All V2 paper/graphic-sculpted character investigations are separate.** Do not replace the original V1 female/male rigs, mouth, actions, hair, textures, props, watch or footwear as a side effect of a wardrobe or face experiment.

## Actual, independently verifiable proofs required

1. Reproduce from original Zstandard-compressed `NEXSTUDIO_V1_FEMALE.blend` and `NEXSTUDIO_V1_MALE.blend`, decoded to disposable working copies.
2. Use checksum-verified **Blender 5.2.0 LTS**; save the source hash, new Blender scene, and PNGs from Blender—not synthetic concepts or screenshots of generated artwork.
3. Render **both genders**, matching-camera **front** and **three-quarter**, plus the existing authored action at **frames 338 and 891**. Check frames for sleeve/hand intersections, neck/clavicle crossing, dropped buttons, open front, and floating or broken lapels.
4. Retain original performance actions, armature, body and facial shape-key inventories. A preserved list alone is not proof of animated compatibility; test poses and later moving action playback.
5. New clothing must have a continuous intentional silhouette on the front, visible side and back, clean cuff/hem/collar structure, correct overlap with the original shirt/dress and no surface-penetration artifacts.
6. Ink and fabric must match the approved illustrated family: ink lines are resolution-aware; no triangle fan wireframe visible as accidental diamonds; no faceted floating chest stickers.
7. Existing outfit remains selectable; **no canonical scene or production integration should change** while a trial is unapproved.
8. Preserve each source asset's license and attribution. None of these experiments should be described as CC0 if they inherit a CC-BY clothing mesh.

## Current experiment dispositions

| Experiment | Result | Release decision |
|---|---|---|
| Waistcoat V1 | Flat, unconvincing front patches | REJECT |
| Jacket V2 | More torso coverage, but cardigan-like and short | REJECT |
| Jacket V3 | Subtle lapels, still reads as overlay | REJECT |
| Jacket V4 | Armature follows selected action frames 338 and 891, but angular lapel facets and odd male front | REJECT for integration |
| Jacket V5 | Better perimeter anchoring but lapels still read as flat hanging straps | REJECT for integration |
| Real MakeHuman suits01 CC0 — six formal wardrobe choices | All 6 recreated and reopened in Blender 5.2.0; individual hashes verified; source UV textures, finished real shoes, front/three-quarter and pose 338/891; 6 × 10 original gesture frame geometric evaluations; 4.25s original-action moving MP4s for both canonical hosts | **PASSED structural/reproducibility/animation sampling; NOT production approved**. Needs hard collision, expression and presentation/podcast end-to-end acceptance |
| New expressive/resolute/thoughtful faces | Actual drawn-eye/brow/nose stills, but face-line registration wrong in 3/4 and blink/visemes unproven | REJECT for integration pending repair |

| Licensed Hair01 donor choices | Individual MHClO audit of 25 assets found 11 explicitly CC0, 10 AGPL-3 and 4 other/unclear; 11 CC0 geometry-only meshes cached; 7 new hair forms rendered, front/head 3/4 and gestures | **2 strongest female bob shapes retained as candidates; male eye-obstructing or malformed choices REJECTED** |
| Same-rig reversible hair selector | Original and fitted alternate active in separate saved scenes; both real meshes preserved; both gender rigs remain 163 bones/34 body shape keys; actual Blender front and 3/4 previews published | **PASS Blender experiment only; NOT wired into public NexStudio UI** |
| New original-illustration hair color swatches | Charcoal, caramel, near-black, silver re-rendered on fitted original 3D hair; copied native hair materials preserve original material and rig | **PASS technical customization; visual approval by palette and character still pending** |
| Original inherited native face morphs 1 and 2 | 4 independently rebuilt male/female faces with measured 7.6–10.9mm max head-vertex displacement; preserved 163-bone rigs, 34 facial morph keys, original performance action positions | **PASS geometric modification, but too subtle at full-body scale to classify as new identities; closeup QA required** |

## Current verified handoff (experimental, isolated)

- [Six independently validated original-rig editable outfits](https://github.com/Admiano/nexstudio/actions/runs/38004823946/artifacts/11650637868) (compact, temporary GitHub artifact).
- [Six-outfit manifest](formal-bank/BANK_MANIFEST.json), [60/60 original-frame geometric integrity report](formal-bank-geometry-qa/QA_SUMMARY.json), and [original female/male 4.25s Blender motion clips](motion-proofs/).
- [Original vs alternative hairstyle switches](hair-switch-proof/), [curated individually permitted CC0 hair geometry](hair-inventory/Hair01_CURATED_GEOMETRY_MANIFEST.json), [source-licensed hairstyle visual verdicts](HAIR_VARIANT_VISUAL_QA.md), and [hair color Blender renders](hair-color-trials/).
- [Inherited native facial geometry change measurements and samples](native-face-morph-trials/); **not proof of new visual identities**.

**Blocked before production:** full-body/hand/cloth contact collision reviews, facial-expression/blink/viseme tests, two-person podcast continuity testing, more distinguishable faces, and actual NexStudio character-preset UI integration. No new original character family is production-shipped by these experiments.

Do not mark V5 approved simply because a Blender job exits successfully. Publish the individual actual PNGs, scene proof, and report and **inspect** the result before any claim of V1 readiness.
