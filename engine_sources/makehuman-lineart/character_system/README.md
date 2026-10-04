# Corrected NexStudio character system

This is the illustrated MakeHuman character system with the approved skin, facial anatomy, hair, clothing and accessories, the anatomical watch correction, and the restored original gesture and facial take. Its original performance is `Host.rigAction.001` plus `baseAction`: 998 frames at 24 fps. The same original animation-curve digest is verified in every scene after saving and reopening.

## Contents

- 15 self-contained editable Blender scenes: seven female looks/views and eight male looks/views. Five female dress variants, five male garment variants, the canonical looks, the male bald look and separate fixed left three-quarter views are included.
- The existing customization builders, source meshes, asset provenance, procedural appearance modules, three face choices, six skin presets and custom colours, five female hairstyles, six male hairstyle choices, clothing pieces, neckwear, earrings and five watches.
- Existing Cast UI/configuration, preview worker and baked option assets on this branch. The preview cache version changes so an old assembled image cannot be reused for this corrected profile.
- Actual original-gesture and before/after watch previews; scene verification and complete file hashes.

The V19 directing/adapter/exporter integration, its voice alignment dependencies and test podcast are absent. Copied V18/V19 action variations are removed from the packaged scenes. The appearance module retains hand contours, garment relief and lip-seal geometry without copying or editing rig/face action curves. It accepts no semantic gesture plan.

The watch generator uses the anatomical dorsal hand normal projected perpendicular to the forearm. It applies to analog, digital, smart, chronograph and dress watches. The case, dial and details remain one rigid assembly attached to the native lower-arm bone; visibility changes naturally with the wrist and camera.

## Open and render

Use Blender 5.2.0 LTS. Open `scenes/female/native/character.blend` or `scenes/male/native/character.blend`. Textures used by the saved scenes are packed. Other outfit scenes are listed in `scene-verification.json`.

From the repository/package root:

```bash
BLENDER_BIN=/path/to/blender python3 scripts/render-character-system.py --character male --frame 600 --output out/male-front.png
BLENDER_BIN=/path/to/blender python3 scripts/render-character-system.py --character female --view left-3q --frame 350 --output out/female-left-3q.png
BLENDER_BIN=/path/to/blender python3 scripts/render-character-system.py --character female --style qipao --frame 140 --output out/qipao.png
```

These render separate fixed views and evaluate the original frame times. Saved garment fitting runs before rendering. No camera orbit, audio modification or replacement gesture processing is used.

## Rebuild a customized look

`requests/female.json` and `requests/male.json` contain default versioned configuration examples. The existing Cast `castRenderConfig` function creates the same configuration for other choices. All fitting assets are included under `../assets`; `ASSETS.json` retains credits/licenses and `FILES.json` pins the original source asset blobs. Additional male hair sources retain their `.mhclo` author/license headers.

Use the included wrapper, which validates and exports the request configuration:

```bash
BLENDER_BIN=/path/to/blender python3 scripts/build-character-system.py --request engine_sources/makehuman-lineart/character_system/requests/male.json --output out/custom.png --scene-output out/custom.blend
```

The source builder and packaged native scenes retain the original performance. The old `presenters_v1/build.sh` remains a historical V1 baseline; use the current assembled renderer for the updated appearance.

## Validation scope

All 15 scenes were saved/reopened with exact original action equality, ten finite-pose samples each and packed used textures. All 99 pinned original fitting assets were hash-verified. Fresh female and male builds and the Cast mapping/cache/worker checks are recorded in `validation.json`.

Existing visual QA and current watch previews are retained. These checks do not certify every possible combination of face, hair, outfit, colour, frame and camera for collisions, nor do they establish long-form narration alignment. This package introduces no new performance system and does not claim a website or worker-service deployment.
### Large-scene materialization

Five female scenes exceed the GitHub connector blob limit. Their exact `.blend` bytes are stored as 25 MiB `.partNN` files with SHA-256 entries in `scene-parts.json`. Run `python3 materialize-scenes.py` from this directory to reconstruct the original `character.blend` files before opening them in Blender.
