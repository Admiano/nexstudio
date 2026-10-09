# Cast finish upgrade

The renderer now uses the versioned `approved-v3-v6-finish-v7-upper-thigh` finish profile. The approved female v3 and male v6 remain the identity authority. All eleven original Blender files and all 99 downloaded source asset files retain their verified hashes. No generated or replacement characters are used.

The server worker fixes the quality settings independently of its startup environment. Clients cannot inject those settings. The matching app and worker cache version invalidates preceding renders. These code changes still require deployment and signed-in app acceptance; the version change does not deploy the application.

## Implemented changes

- Single live garment contact shade replaces duplicated rest-pose/live occlusion. Skin and face grading remains the approved reference.
- Hair gradients and fabric grain use stored mesh coordinates so their placement follows rig deformation instead of world height.
- Existing long/bob/bangs/braid hair boundaries receive a restrained end refinement, bounded to 4 mm per source vertex. Original hair identity, weights and animation are retained.
- Fabric classes use different restrained grain amplitudes. This is stylized surface detail, not woven geometry or cloth simulation.
- Button-down fasteners are visible and follow the garment's existing seam binding. Generic long torso darts are omitted from cotton/knit tops.
- Sleeve ends use a complete rigged skin target with 1.8 mm outside clearance. The target is internal and invisible; hands and original skin are retained.
- Collars, cuffs and hems use inward 0.8 mm thickness after deformation and subdivision. Bounded normal offsets replace unbounded miter compensation, which produced spikes on the fisherman sweater and maxi dress.
- Copied earring rims use valid object parenting. Non-manifold trouser seam proxies use interpolated rig-weight binding with a checked bind-pose residual.
- Every pose rebuilds disposable fitted display meshes from the original rig. Source meshes do not accumulate corrections.

## Verification

The wardrobe matrix covers all 25 male top/trouser combinations and five dresses at frame 27. Its initial visual review detected shell spikes on the fisherman sweater and maxi dress. Those six entries were corrected and rerendered; the affected source assets were retained. The resulting contact sheets are visual evidence, not a claim that every catalogue combination passes every animation frame.

The reference pair passed 120 pose samples from frames 240 through 597. Checks cover finite geometry, unchanged source coordinates, stable object/mesh counts and valid visible bone parents. The sleeve audit also compares corrected and uncorrected evaluated geometry and rejects displacement over 12 mm. The final audit recorded a maximum 8.54 mm sleeve correction and 1.59 mm sampled seam separation across all three male seam objects; the woman's sampled seam separation remained below 0.8 mm. Report filenames identify the audited revision; avoid applying old mesh hashes to later button or shell refinements.

Native source-rate clips use frames 300–347 at 24 fps, 540×720 and 16 samples. These clips predate the final sleeve-seam proxy correction. They are motion diagnostics, not full-resolution commercial deliverables or evidence for that later correction. Frame-27 worker previews use the actual 1080×1440 application profile.

## Reproduce

```sh
python3 scripts/cast-quality-reference.py --character male --output-dir /path/to/review --blender /path/to/blender
python3 scripts/cast-quality-matrix.py --output-dir /path/to/wardrobe --blender /path/to/blender
```

Use `--baseline` for the preceding appearance, or `--no-upgrade` / `--no-structure` to isolate a diagnostic change. Add `--motion 300 347 1` for a source-rate motion sequence. Matrix requests, logs and metadata record each exact garment combination. `--only male-5-1 female-2` rerenders selected entries and merges their evidence at the same pose.

## Commercial readiness limits

This upgrade does not establish 9+ across all five original readiness areas. Remaining acceptance work includes authored shoulder/sleeve shape and weight corrections, further hair silhouette work, detailed fabric construction, hand-contact pose correction, full-resolution temporal line inspection, all hairstyle/face/accessory/recolour combinations, refreshed option thumbnails and signed-in desktop/mobile save/reopen acceptance. The existing thumbnails retain their exact approved-source provenance but predate this finish profile.

Restoring discarded source fastener components was rejected because it produced severe deformation. An outward garment shell was also rejected because it obscured seam ribbons. The implemented construction uses the retained garment surfaces and bounded inward thickness.
