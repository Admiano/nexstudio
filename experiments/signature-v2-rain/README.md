# NexStudio V2 — Rain-derived signature character experiment

**Status: SOURCE RECOVERED; BLENDER PROTOTYPE AND MODULAR RENDERS VERIFIED.**  
Last technical checkpoint: 2026-10-10 (local working runtime).

## Real asset source

- Verified original scene on `main`: [rain_v3.2.blend](https://github.com/Admiano/nexstudio/blob/main/engine_sources/charpack-lineart/Rain_x/Rain%20v3.3/rain_v3.2.blend)
- Verified source folder includes **22 named texture files**: [Rain v3.3 source folder](https://github.com/Admiano/nexstudio/tree/main/engine_sources/charpack-lineart/Rain_x/Rain%20v3.3).
- Blender scene SHA-256 observed by successful GitHub Actions verification: `831ab6d837c679040285862b15dc9ee5180b018442a88aeaf92aaa7509b80258`.
- Source retrieved as a verified ZIP via [GitHub Actions export run #38005157040](https://github.com/Admiano/nexstudio/actions/runs/38005157040); source archive included scene and textures.
- License: **CC BY 4.0**, attribution **Rain Rig © Blender Foundation | studio.blender.org**.

## Verified local Blender milestones

- Loaded genuine Rain `rain_v3.2.blend` in Blender **5.2.0 LTS** and rendered source baseline front / 3-quarter / side / facial views.
- Found true IK hand controls and lowered the original T-pose arms; hand angle adjustment verified.
- Created multiple independently editable prototype scenes Rev01–Rev10. Original Rain source on `main` was **not modified**.
- Constructed stylized hair extensions, sapphire knit, geometric wool coat with sleeves/lapels, red boots and selectable material colors. The original Rain facial geometry remains, avoiding falsely claiming a new mature facial sculpt.
- **2,166 original rig bones**, **25 original head shape keys**, **10,256 body vertices** preserved in portable checkpoint.
- Assigned **25 new skinned mesh objects** to genuine Rain deform bones; every referenced vertex group matched an existing rig bone.
- Fixed duplicate vertex group bug before verifying structural shoulder/forearm sleeve-weight transfers. Neutral and outward/upward IK movement renders produced; cuff/armpit intersections still require correction.
- Moved new assets into four independent Blender collections: `COAT`, `HAIR`, `BASE_KNIT`, `BOOTS`. Three genuine renders demonstrate default coat, coat removed, and a second colorway.
- Verified original Rain facial control drivers respond to mouth-corner and eyelid rig controls. This does **not** certify natural dialogue performance.
- Built portable `.blend` scenes with packed image assets and local downloaded ZIPs containing scripts, audited QA and genuine Blender render previews.

## Art quality / blockers — do not claim finished

- Reference-level elegant editorial identity is **not reached**. Face still resembles Rain and extensions have flat ribbon-like hair strands.
- Coat is still too polygonally assembled; shoulder/cuff anatomy, cloth deformation, garment intersections, fabric folds and rig continuity remain production blockers.
- No speech/lip-sync, full animation, pose-library, long hair simulation, cloth physics or export certification.
- CloudRig's embedded Python scripts are disabled by Blender's safe startup setting in background tests. Test with controlled/trusted runtime before shipping.

## Local packaged artifacts (from review checkpoint)

- `NEXSTUDIO_RAIN_V2_REV09_CHARACTER_CHECKPOINT_20261010.zip` — verified portable Rev09 Blender scene, scripts and QA, ZIP CRC passed.
- `NEXSTUDIO_RAIN_V2_REV10_MODULAR_20261010.zip` — verified deliverable: 17 ZIP entries, 21,078,617 bytes, ZIP CRC passed; four modular collections and three real Blender renders. SHA-256: `34a5bc60a47da4aa1288a356b55a9fb3483a11d3215cf654852750408f61b277`.
- `Rain_v3.2_original_scene_and_textures.zip` — source and textures from original `main` tree.

Note: binary Blender checkpoint ZIPs are delivered as ChatGPT workspace files and **are not committed to this GitHub branch**. This experimental branch contains provenance/docs/export workflow, not a production character asset. V1 and paper character assets remain untouched.


## 2026-10-12 — Rev19 genuine Blender render checkpoint (separate from Rev10)

The previous Rev13 hair panels were too geometrically rigid. Visual experiments Rev14–Rev16 were rejected: Rev14 eyebrows became occluded; Rev15 hair had flat pillars; Rev16 rounded volumes resembled horns. Rev17 replaced those with 860 physically editable strand meshes; Rev18 added 550 face-framing strands; Rev19 improved crown/groom palette and matte oxblood materials. All builds used the real **Rain v3.2 Blender scene** through the portable Rev13 checkpoint, without modifying the official source or V1 project.

Rev19 QA was done in **Blender 5.2.0 LTS** on an actually reopened scene:
- 2,166 source rig bones retained
- 25 head shape keys retained
- Four source modular collections retained
- Eight new groom mesh objects; 265,760 vertices total; all eight have genuine `DEF-Head` vertex group and valid `ARMATURE` modifier
- Four image assets packed, no missing unpacked bitmap references
- A 12° FK-Head representative pose displaces one Rev19 hair layer **0.03355m** and Rain head **0.014629m**. The other seven new hair meshes were disabled for viewport performance; **a full dense-groom head-pose test timed out** and is NOT certified.

Checkpoint in ChatGPT workspace: `NEXSTUDIO_RAIN_V2_REV19_CHARACTER_PROGRESS_CHECKPOINT_20261012.zip` (53,639,655 bytes; 38 CRC-verified ZIP entries; SHA-256 `ba80ed7ea0e56e99c13205f80c953ea76dee4ba560f15d83980e63aaec8730dd`). Contains two editable Blender scenes (Rev17 short groom and Rev19 long groom), scripts, Blender-rendered front/profile/face comparison imagery, reopening QA, the representative pose test, and checksum manifest. **The binary package is not stored in this GitHub branch**.

**Not finished or ready to ship:** distinctive mature facial identity, realistic integrated hairline and natural groom, proper tailored cloth construction and arm/cuff seams, full animation and audio/lip-sync certification, and integration into NexStudio. Reject false claims that this equals target-reference quality.


## Revision 24 update — 2026-10-12

**Development checkpoint, not production release.** The source was recovered from `main/engine_sources/charpack-lineart/Rain_x/Rain v3.3/rain_v3.2.blend`. Original Rain and V1 sources remain untouched.

- Rev20 sculpted shoulder-cap attempt **rejected** (visible geometry gaps and poor folds); Rev19 sleeve construction remains. Rev21-22 improved hair-root matching and added 12 curved layered mesh locks. Rev21 applied subtle same-delta edits to 3,057 face vertices across all shape keys. Rev23 slimmed the existing eyebrow mesh without removing its armature.
- Rev24 performs a structural performance improvement: all **20 extra hair mesh groups (269,108 total vertices)** had single **100%-DEF-Head** weights. Replaced redundant armature modifiers with equivalent `DEF-Head` bone parenting. Neutral sampled point error **4.88e-7 m**.
- **Full visible 20/20-groom** rigid-follow verification: `FK-Head` **local-Z head tilt +12°** (not yaw), min/new hair group displacement 0.025162 m, max 0.045563 m, original head displacement 0.014855 m; pose evaluation **0.123 s** on the Blender 5.2 test runtime. The old full dense-groom pose evaluation timed out before optimization. No independent hair physics is claimed.
- Produced 13 genuine Blender-rendered head-tilt sequence frames, plus GIF and MP4 previews. All hair groups enabled during the frames. The Rev24 neutral scene reopens with **2,166 bones, 25 head shape keys, 20 head-parented groom objects, 4 preserved wardrobe modules, four packed bitmap assets and no missing unpacked file images**.
- The last checkpoint ZIP, **`NEXSTUDIO_RAIN_V2_REV24_RIG_GROOM_CHECKPOINT_20261012.zip`**, is delivered to the user via the ChatGPT working file environment. **36,921,790 bytes**, **38 entries**, ZIP CRC test passed. SHA-256: `5812ced6a4ee63f5c514eeacd9bf0b5f6c928ceee37b92e03373b43e36653513`. The ZIP and binary `.blend` are **not committed here**.

**Remaining art and production blockers:** Rain's distinctive face still looks like Rain, hair is rigidly head-following and lacks professional groom/secondary motion, coat shoulder and sleeve/cuff tailoring remains flawed, full speaking/presenter animations and garment collision tests absent. Embedded CloudRig scripts were skipped by Blender's safe startup mode; external engine integration not attempted. This branch remains isolated; do not merge into V1.
