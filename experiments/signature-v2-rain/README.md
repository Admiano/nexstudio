# NexStudio V2 — Rain v3 acquisition-gated experiment

**Status 2026-10-09: SOURCE BLOCKED. NO RAIN MODEL OR RAIN-BASED RENDER IS CLAIMED.**

Rain v3 is the selected new chassis. This branch is isolated from all V1 assets and the prior MakeHuman-based Rev08/V2 visual prototype.

Official source: https://studio.blender.org/characters/rain/v3/  
License: CC BY 4.0; retain **Rain Rig © Blender Foundation | studio.blender.org** attribution for derived assets.

Verified local work:
- Blender **5.2.0 LTS** runs successfully.
- Searched the Library (1,502 ZIP/.blend entries), connected Google Drive and `Admiano/nexstudio`; no source file named Rain was found in accessible results.
- Found a public **v2.6** archive on Packt GitHub but did not substitute it for the selected v3.
- Attempts to download binary Rain source via the available environment failed.
- Implemented a source-gated Blender 5.2 bootstrap toolchain: safe ZIP intake, native scene inspection for rig/bones/body meshes/shape keys/images, review-camera/lighting setup, four genuine Blender render slots and isolated `.blend` copy.
- QA: Python scripts compiled; a real Blender dry-run with the earlier **non-Rain** female .blend was rejected and **did not produce misleading character renders**.
- Tested pipeline scripts and audit report are packaged in the ChatGPT attachment `NEXSTUDIO_V2_RAIN_SOURCE_GATED_BOOTSTRAP_20261009.zip` (11,422 bytes, SHA-256 `53ae60927d4efdaa20ad39475a214d29e973adccc1b40f4a3c1359e868f379c3`). Binary ZIP is not committed to this branch.

**Blocking input:** acquire the authentic free Rain v3 ZIP or `.blend` from the official source and make it available to the model's working container. The prototype can only be built once the source is inspectable.

Next after asset intake: run rig audit; render untouched Rain baseline; inspect facial/hair/wardrobe geometry; create original NexStudio head/hair/coat in an isolated scene; bind new geometry to Rain deform skeleton; perform pose, face, garments and profile-angle QA. Do not treat onboarding scripts as an implemented visual character.

Do not merge into V1 and do not reuse Rev08 meshes as a fake Rain substitute.
