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
