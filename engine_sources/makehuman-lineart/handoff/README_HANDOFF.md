# MakeHuman / Open Peeps character work — complete handoff

This handoff collects the project work available in this workspace as of 23 September 2026. Extract bundles 01–05 into one directory. They contain editable Blender scenes, original Open Peeps source art, audio, scripts, QA, renders, and the later experimental puppet prototype. Bundles 06–10 carry the optional Blender 5.2.0 Linux installer in five chunks.

## What is actually complete

- `01_Current_Work/V10/`: current Host and Guest Blender scenes, each 360 frames at 24 fps; the original 15-second WAV files; scripts; structural QA; stills; and a **2-second** combined review excerpt with audio. The 15-second performances have **not** been rendered as complete videos. Open the `scenes/V10/` files in Blender.
- `01_Current_Work/experimental_vector_puppet/`: extracted Open Peeps component art, motion-driver JSON, exploratory code and prototype frames. These were a rejected visual experiment, not a finished replacement for the V10 scenes.
- `01_Current_Work/earlier_foundation/MAKEHUMAN_LINEART_FAMILY_V5.blend`: earlier foundation scene. `workspace_v10/` retains extra local scripts, logs, stills, 24-frame PNG sequences and MP4 segments that were not in the V10 review release.
- `02_Open_Peeps_Art/`: the original Flat Assets ZIP, Sketch, Figma and Studio files, extracted reference artwork and indexing/rig notes.
- `03_Original_V9_V10/` and `04_Original_V1_V8/`: prior ZIP releases preserved byte-for-byte.
- `05_Motion_Workspace/`: earlier eight-second silent V1 motion test, editable source, frame sequence, scripts, logs and QA.

## Production status

This is **not a commercial-quality or 90% result**. The V10 pass stabilized some outlines and checked both 360-frame timelines structurally; only sampled frames and a two-second excerpt were visually rendered. The mouth is a simple aperture without convincing lip/teeth/tongue articulation or verified phoneme sync. Hair and eyes, facial acting, garment design and texture, hand ink, posture, gesture timing and transitions still need directed work. The experimental Open Peeps puppet loses too much facial identity and deforms clothing poorly. There is no finished 30-second reel. Rhubarb Lip Sync binaries or output are not present in this workspace.

## Optional Blender installer

Bundles 06–10 each contain one ordered `.partNN` chunk of the original `blender-5.2.0-linux-x64.tar.xz`. Unzip all five alongside each other, then reassemble in order:

```bash
cat blender-5.2.0-linux-x64.tar.xz.part{01..05} > blender-5.2.0-linux-x64.tar.xz
sha256sum blender-5.2.0-linux-x64.tar.xz
tar -xf blender-5.2.0-linux-x64.tar.xz
```

Expected SHA-256: `96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48`. These five bundles are only the unmodified Linux runtime archive, split to meet the 90 MB limit. The source project is in bundles 01–05.

Each ZIP is individually under 90,000,000 bytes and can be opened on its own. No Google Drive copy was made.
