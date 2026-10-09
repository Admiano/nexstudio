> Superseded: the final implementation and current validation are documented in [../cast-customizer-review/README.md](../cast-customizer-review/README.md). The text and patches below preserve unfinished experiments only; do not apply them over the final implementation.

# Unfinished customizer follow-up — recovery checkpoint

The follow-up requested on 2026-10-02 is **not accepted or implemented on this branch yet**. These files preserve prepared code and decisions after the execution workspace disconnected with environment_offline during final clothing work. This checkpoint does not change the running app. The previous implementation at 76e6e21081c96f1236502289bdfdefe9aeddfe5f remains the application code.

## Confirmed requirements

- Preserve the approved female v3 and male v6, existing meshes, shading, rig and actions.
- Repair male clothes that appear torn; inspect every available combination.
- The user explicitly confirmed upper-thigh-upwards main framing.
- Faces, hair, garments, shoes and accessories use small readable images. Colours remain rounded swatches.
- Use the newest ten environments from the GitHub reference.
- Do not use image generation. Thumbnails are exact existing render pixels.

## Prepared image selector

OptionImage.tsx.txt and option-images.css.txt contain the prepared component/styles. Restore them to src/studio-v2/cast/OptionImage.tsx and the end of src/studio-v2/nexstudio-v2.css.

In CastView.tsx replace text tiles with OptionImage inside cast-image-options:

| Catalog | character / category / option |
|---|---|
| Woman, Man | corresponding character / character / corresponding character |
| FACES | selected character / face / f.id |
| hairStyles(character) | selected character / hair / h.key; retain the existing note |
| NECKS | female / neck / n.key; None persists null |
| FEM_DRESSES | female / dress / o.key |
| MALE_OUTFITS | male / top / o.key |
| MALE_BOTTOMS | male / bottom / b.key; use independent patchPieces |
| MALE_SHOES | male / shoes / b.key; use independent patchPieces |
| WATCHES | male / watch / w.key; None persists null |

Preserve labels, aria-pressed and existing selection functions. Character group also gets cast-character-options. Lipstick becomes identity-color swatches with aria-label/title equal to l.label and --c equal to l.hex; preserve custom HEX controls. Keep trouser/shoe groups outside the Top colour group.

Restore build-cast-option-thumbnails.py.txt to scripts/build-cast-option-thumbnails.py. Install Pillow, render the named full-body looks and six square faces, then supply their absolute PNG paths through --sources. The script writes 50 SVG files containing actual 224px WEBP pixels plus provenance/crop records. The source accessory sheets already exist in the pinned repo.

Named sources: female-approved, male-approved, female-bob-maxi, female-bangs-column, female-bun-cocktail, female-braid-qipao, male-bald, male-crop-polo, male-afro-tee, male-braids-knit, male-swept-fisherman, five default male ensembles listed in the script, and female/male-face-0/1/2. Use repaired male-approved and male ensemble renders for thumbnails. Older unchanged hair/dress crops can be reused with hashes. Face heads were rendered and visually inspected successfully; their camera values below avoid cropped chins.

## Framing changes

In castRenderConfig include framing: 'upper-thigh' and resolutionPercentage: 50. Change CAST_RENDER_VERSION and the Python worker's RENDER_VERSION together; use a fresh version after final clothing repair to avoid experimental caches. The local intermediate version was approved-v3-v6-fit-v4-upper-thigh.

Worker validation must require framing == 'upper-thigh', and its test fixture must include that field.

After the original assembler and approved polish run, before frame/render settings in scripts/cast-render-assembled.py:

~~~python
if config.get('framing') == 'upper-thigh' and '--full-body' not in args:
    female = os.environ['CAST_CHARACTER'] == 'female'
    scene.camera.location = (-0.42, -5.0, 1.21 if female else 1.29)
    scene.camera.rotation_euler = (1.5707963, 0, 0)
    scene.camera.data.ortho_scale = 1.10 if female else 1.18
    scene.render.resolution_x = 2160
    scene.render.resolution_y = 2880
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'
if '--headshot' in args:
    scene.camera.location = (-0.42, -5.0, 1.55 if os.environ['CAST_CHARACTER'] == 'female' else 1.64)
    scene.camera.rotation_euler = (1.5707963, 0, 0)
    scene.camera.data.ortho_scale = 0.50
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'
~~~

Main output is 1080×1440. Keep current Freestyle/compositor scaling with actual image height. --full-body retains the original camera for garment thumbnails and QA.

## Clothing investigation — final repair still required

The old waistband deletion in presenters_v1/scripts/garm.py removes vertices at a bind-pose hem and opens seams after subdivision/posing. Keep the complete waistband and its deformation weights.

Depth-only PROJECT shrinkwrap after trouser subdivision closed the default shirt seam without moving the crotch towards the nearest shirt hem. Choose the object's local axis most aligned with world Y; enable projection in both directions and bound its distance. Nearest-surface pants fitting pulled the crotch upwards and exposed skin, so do not reuse it.

A first depth fit with negative offset closed most seams but knit + straight jeans / wool trousers still showed skin at the left waist. The fisherman also needed attention. Some garments lack MakeHuman delete_verts body masks. Body skin intersecting intact clothes can therefore look like holes.

Experiments that should **not** be shipped:
- Unbounded body clearance: snapped waist vertices towards distant surfaces through open body masks.
- Body clearance alone: moved trousers outside the fisherman sweater.
- Mutual top/pants constraints and additional top subdivision: produced waist overlap and exposed shoulder skin. Those render matrices are failed experiments, not acceptance evidence.

The pending approach is intact garments, bounded depth fitting underneath an untucked top, and body occlusion for the covered regions. Candidate coverage: use the original fitted garment surfaces to find body vertices underneath clothes via front/back depth rays; protect hand/finger/thumb/head groups and retain the boundary ring at cuffs/necklines; add a body MASK before subdivision, using the original mask inversion convention. Keep all source Blender files and garment topology unchanged. A -0.02 covered-trouser offset was proposed but **not render verified** before disconnection. Validate the masks and clothing clearance rather than assuming they work.

Do not claim all clothes are fixed until final rendering passes.

## Required final verification

1. Render all 5 male tops × all 5 trousers at frame 27 and inspect waist, crotch, cuffs and shoulders. Cover custom colours, selected watches and hairstyles as well.
2. Check finite posed garment geometry at frames 1, 27, 338 and 891; actually render 338/891 for the five default male ensembles.
3. Regenerate affected option thumbnails and inspect them at their actual control size. All 50 paths must load, and selected state must be readable.
4. Run npm run test:cast, npm run typecheck, and a production build. For the disposable local verification runtime only, STUDIO_TRUST_SECRET=studio-v1-local-development-only supplies the required fixture.
5. Capture actual production standalone app screenshots at desktop 1440×1000 and a fresh mobile 390×844 browser context. Test save/reopen/reload, custom colours, None accessories, independent male pieces and voice.
6. Test a genuinely uncached current-profile request through the production worker, ready image loading and Save gating.
7. Update verification docs and PR #58 around the final behaviour; publish implementation only after review. Save/share actual new screenshots, not experimental renders.

Local prepared selector/type checks, focused Cast tests and production build passed before the final clothing approach. All eleven original Blender files matched Git HEAD hashes. These are partial results: new desktop/mobile checks and the last clothing repair did not finish. Earlier verification in CAST_CUSTOMIZER_VERIFICATION.json belongs to the previous implementation and must not be presented as proof of this follow-up.

Use at most two Blender rendering processes on an 8GB machine; production remains one worker through flock. Rendering can take 25–120+ seconds depending on the selection. Do not claim instant new-look rendering.

## Missing exact environments

The newest engine_sources/makehuman-lineart/NexStudio_Presenter_Reference/REFERENCE.md at source bf88447b8f898bea078c44b9202cfe2b7ff13be5 names:

living_room, home_office, creator_studio, workplace, cafe, kitchen, library, classroom, terrace, neutral_studio.

It points to separate NexStudio_Realistic_Background_Catalog.zip and NexStudio_Illustrated_Background_Catalog.zip archives, including composition-specific files. Neither archive nor the ten source images was present in the checked GitHub trees, branches, PR attachments/releases or available files. Do not invent replacement backgrounds or display a working picker with missing images. Obtain these exact archives, then wire selection, spec persistence and camera-ray-only background compositing per the reference.

## Workspace recovery

The disconnected workspace was /workspace/scratch/edfddd45f850; the repo was nexstudio on codex/cast-source-rendering. Prepared app files were local only. If the workspace returns, inspect git status first. Do not reapply duplicate CSS or duplicate body mask groups.

Transient renders and scripts were in cast-review-v2, source-review, preview-runtime and cast-customizer-updated. final-looks contained 25 outfits and six corrected face renders, but later review rejected fisherman overlaps. outfit-combinations.png was a diagnostic matrix and must be regenerated after the final repair. No fresh final screenshots were published.

The last attempted command was a proposed body-coverage refactor plus another fisherman render; its completion could not be verified after environment_offline. Restore from this checkpoint if those local files cannot be recovered. Preserve the approved source already in PR #58; do not restart character design.
