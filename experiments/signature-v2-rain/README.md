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


## 2026-10-12 — facial / hair art iteration (Rev25–Rev29)

**STATUS: Rev27 preferred experimental face / light-groom scene; Rev29 remains unapproved smaller-eye alternative.** These are genuine Blender 5.2 editable derivative scenes, not AI-generated reference renders, and are not production-ready.

- Rev25 attempted continuous five-ring sleeve taper: **rejected** after native 3/4 render showed awkward cuff transition and persistent hard shoulder.
- Rev26 applied controlled jaw/cheekbone/nose/chin and brow changes to original Rain facial topology: 3,815 vertices changed, max magnitude 0.00921 m, applied same per-vertex displacement to all 25 shape keys.
- Rev27 removed twelve heavy face-framing sheets, retaining eight groups of real strand-based groom mesh. Exported 41,904 shape-key delta components from Rev24 and Rev27: maximum difference **1×10^-7 m**. This checks morph offset preservation, NOT functional lip-sync or driver execution. Actual 12° FK-Head local-Z head-pose test with all eight retained groups passed and rendered; no hair secondary physics.
- Rev28 diagnostic renders disabled coat shell, sleeves and lapels independently and confirmed that much of the pointed shoulder originates in the **coat body shell**. A 172-vertex smoothed top-shell adjustment was **rejected** because it introduced visual defects without solving the silhouette.
- Rev29 eye-region and eyeball/lashes/cornea reshaping candidate was saved independently. Real front and 3/4 face renders produced. A test assigning the original `EyelidsClose.L/R` shape keys to 1.0 did NOT visually demonstrate a blink; the candidate is NOT promoted to the preferred scene pending rig-level control tests.
- Independent Blender 5.2 reopen audits passed for both Rev27 and Rev29: **2,166 rig bones, 25 head shape keys, 6,395 face vertices, four wardrobe collections, four packed image textures, zero missing external bitmap files**, eight edited head-parented groom groups.
- New downloadable checkpoint ZIP: **`NEXSTUDIO_RAIN_V2_REV29_ART_FACIAL_CANDIDATES_CHECKPOINT_20261012.zip`**, **67,730,363 bytes**, 56 ZIP entries, full CRC test passed. SHA-256: `e908a39a340a56f3201b3bff108218c57ba8969379f84b1f5a89d862ac56588d`. Delivered as ChatGPT file (binary files **not** committed to GitHub).
- Package also includes the independent true Blender facial comparison board and construction diagnostic board, Rev27 and Rev29 separate portable .blend scenes, scripts and test reports.

**Priority remaining:** high-end facial identity and sculpted hairline, redesign coat shoulders and sleeve seams with true tailored construction, run functional eyelid/blink/lip-speech and body-gesture tests, outfit collision, exports, then NexStudio integration. Do not merge this experiment into existing V1 or original Rain source.


## 2026-10-12 follow-up — Rev30–Rev32 integrated shoulder study

**Rev31 is the preferred new geometry checkpoint; Rev32 cuff-weight experiment rejected.**

- Primary starting point: Rev27 face and eight fine-groom groups, preserving original Rain rig, its 25 face shape keys and four modular wardrobe collections. Rev29 smaller-eye candidate was not silently merged because eyelid closure had not been verified.
- Geometric diagnosis: Rev27 coat upper shell is **12 contiguous loops of 81 vertices**, while each independently skinned sleeve has **five loops of 33 vertices**. Shoulder cap protrusion comes from the combination of ring profiles, not just single shoulder points. A focused sleeve-only or shell-only displacement had created visible gaps in prior revisions.
- **Rev30:** uniformly scaled upper sleeve ring cross sections (factors **0.72/0.78/0.86/0.95/1.00**) and gently tapered top shell loops (first six multipliers **1.00/0.96/0.948/0.969/0.989/1.00**), keeping all original faces and deform weights.
- **Rev31:** used a Kabsch estimate of the *actually evaluated* original Rain sleeve ring transformations to convert desired posed-world shoulder inset to local rest-space offsets. Upper arm cap moved inward ~0.043m and down ~0.024m; following ring inward ~0.012m and down ~0.008m. The real native Blender 3/4 and shoulder-detail renders show a visibly softer top-arm silhouette. Pattern/seam/shoulder joins remain visibly rough.
- Armature stress pose: IK-Hand.L/R each moved outward 0.13 local X and upward 0.15 local Z. Both sleeves visibly deformed; selected vertex motions **0.041–0.082 m**. Sleeve cuff, arm exposure and garment intersections are **not** production-ready.
- **Rev32 rejected:** increased sleeve terminal-ring hand weighting from 0.15 to 0.52; the actual side-by-side arm stress render produced no meaningful improvement.
- Rev31 independently reopened in Blender **5.2** and structural assertions passed: 2,166 bones, 25 facial shape keys, 6,395 face vertices, original 972 coat shell vertices and 165 vertices on each original sleeve; all sleeve/coat skin groups resolve to bones; eight additional hair grooms parented to DEF-Head; all four wardrobe collections; four packed textures; no missing external image dependencies.
- Sampled FK-Head 12-degree control motion: sampled original head point **0.006858m** displacement; all eight groom samples moved **0.045233–0.083792m**. This shows attachment only, not hair simulation.
- Deliverable: `NEXSTUDIO_RAIN_V2_REV31_SHOULDER_GEOMETRY_CHECKPOINT_20261012.zip` (30,939,242 bytes), 20 entries, full ZIP CRC check passed, SHA-256 `216de8525c732d422d9f1b31520777bff1cdf15c2fcc7f92342e5d2eb8c31731`. The working `.blend` is 26,012,885 bytes. Binary deliverables were shared in ChatGPT, **not committed to GitHub**.

**Production blockers:** face identity, hair sculpt and secondary motion, tailored upper garment construction, arm/shoulder deformation and collision, verified blinking/lip sync and studio integration. Do not present these renders as finished.


## Rev33 preferred styling checkpoint — 2026-10-12

**Rev33 is the latest, visual-only preference over Rev31 and Rev27; still not production ready.**

- Built on Rev31's revised 12-loop coat shell and 5-loop sleeves with restrained editorial color palette for seven NEX wool/panel materials.
- Added native Blender shader-node micro-textile noise and bump for more natural cloth surface response. No binary or image-generation substitutions. Procedural fabric surfaces stay editable in the Rev33 Blender scene.
- Actual Cycles renders compare original Rev27, Rev31 shoulder reconstruction, and the Rev33 front/three-quarter/shoulder/IK-arm-motion pass.
- Rev33 reopened in Blender 5.2 and passed same independent structural and motion checks as Rev31: 2,166 rig bones, 25 facial shape keys, 6,395 head vertices, 8 added bone-parented groom groups, four wardrobe modules, 4 packed bitmap images, no missing image dependencies, coat and sleeves retained all skin-bone group names.
- Rev32 increased cuff hand-weight contribution but stress-test images showed no useful improvement; **rejected**. Cuff exposure, seam continuity, facial redesign, improved hairstyle and full dialogue/performance certification remain open.
- New delivered checkpoint archive: `NEXSTUDIO_RAIN_V2_REV33_GEOMETRY_TEXTILE_CHECKPOINT_20261012.zip` — 58,588,369 bytes, 26 ZIP entries, CRC check passed, SHA-256 `98bee5d22390c989a414fa8d1c9d9cf315da01971a0e2d7a837f544e75afcc3c`. Includes separate, editable Rev31 and Rev33 scenes, QA, Blender scripts, and genuine preview stills. **ZIP and .blend binary files delivered in ChatGPT, not committed to GitHub.**

The artwork remains prototype-level. Do not merge or publicly release as a finished NexStudio character.


## 2026-10-12 — Rev34–36: pose-fitted sleeves and sculpted knit collar

**New preferred experimental checkpoint: Rev36**. Local Blender package is delivered through the conversation, not committed as binary to GitHub. Rev33 remains intact. Rev35 is the sleeve-only fallback.

- **Root cause identified**: original Rev33 sleeves were five 33-point rings that folded back after rig skinning; apparent cuff and shoulder positions could not be fixed by changing only wrist weights.
- **Rev34**: replaced each sleeve with a continuous 9×32-ring / 288-vertex / 256-quad arm-fitted garment mesh, retaining the genuine Rain armature deform-group names and existing armature modifier. Inverted blended deform-bone matrices and iterated against evaluated **B-Bone** deformation until the greatest neutral pose fitting error was **0.000134m** on L and **0.000114m** on R.
- **Rev35**: refined continuous deep-blue wool material, restrained shoulder accents and dark integrated cuff hems; hid obsolete independent piping whose positions no longer matched the new cuffs. Real Blender Cycles neutral front/3/4 and arm-stress images verified.
- **Rev36**: replaced the rigid 196-vertex collar with a fitted 640-vertex 8×80-rib mockneck, skinned to `DEF-Spine3` and `DEF-Neck`, with a slight lowered front neckline. Inverse fitting converged below **0.000087m** on the neutral posed mesh. Real `FK-Neck` 12° test moved a collar sample **0.007014m**.
- **Quantitative neutral cuff-to-wrist center distance**: old Rev33 **0.07193m**, new Rev35/36 **0.04395m**, on each wrist. With IK hands moved outward local X ±0.13 and upward local Z 0.15, old Rev33 **0.06568m**, new **0.03918m**. These are measured geometric center distances, not skin-collision distances.
- Rev36 independent reopening Blender audit: **2,166 rig bones**, **25 head shape keys**, **8 parented hair meshes**, **4 wardrobe collections**, **288 sleeve vertices per sleeve**, **640 knit collar vertices**, **4 packed images**, no missing external image assets. Original assets remain untouched. Full cloth and animation certification is **NOT** claimed.
- Final downloadable archive **`NEXSTUDIO_RAIN_V2_REV36_TAILORED_SLEEVES_NECK_CHECKPOINT_20261012.zip`**, **54,497,487 bytes**, 25 ZIP entries, CRC integrity PASS. SHA-256: `76346d572258e5536284446e4304413195c18959cc89cc1bdb7413bf8720cd48`. Includes editable Rev35/Rev36 .blend, Blender native progress board, real front/3/4/stress renders, scripts and QA.
- Primary remaining blockers: high-end facial identity, non-rigid hairstyle with proper groom, authentic upper coat-to-sleeve seams and lapels, broader arm gesture and cloth collisions, blink/lip sync, NexStudio app integration. The new long sleeves improve fit but still have visible seams.

No merge to NexStudio V1 and no changes to original Rain files.

- **Rev37 exploratory lapel smoothing REJECTED**: applying Catmull–Clark smoothing to the original three-panel lapel surfaces rounded them into unsupported floating flaps. The Rev36 independently tailored sleeve and collar checkpoint remains the preferred candidate; no Rev37 replacement/merge was made. Correct next step is constructing actual garment-connected lapel surfaces, not applying smoothing alone.
