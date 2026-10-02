# Commercial quality reference pass

This is an opt-in development pass, not a 9/10 release claim. The approved female v3 and male v6 remain the identity authority. No generated images or replacement characters are used.

## First reference pair

- Woman: original long hair, navy sheath dress, original face and skin palette.
- Man: original quiff, blue button-down, tan trousers, brown monk straps.

## Implemented candidates

`CAST_QUALITY_PILOT=1` disables duplicated rest-pose garment occlusion while retaining short-range live contact shading, reduces stitching weight/offset, and makes the male strand-detail colour follow the selected hair palette. Copied earring rims use explicit object parenting instead of requesting a nonexistent bone on their mesh parent. Generic long torso darts are omitted from cotton/knit tops, while tailored shirt darts remain.

`CAST_GARMENT_STRUCTURE_PILOT=1` adds an inward 0.8 mm garment shell after rig deformation/subdivision for physical collar, cuff and hem edges. It does not rewrite source meshes or weights. This is a separate candidate and must be evaluated in motion before activation.

The fitter is callable for each frame. It discards the previous evaluated display meshes, restores source visibility, and evaluates the original rig again. It does not accumulate corrections into source geometry. `scripts/cast-motion-proof.py` produces a continuous, source-timed proxy sequence with finite garment checks and object/mesh count guards. The proxy uses 540×720, 16 samples and every third source frame; it is defect-inspection evidence, not a final-quality video.

Production defaults do not enable either pilot flag. The existing renderer cache version remains unchanged until a candidate is accepted and propagated through the complete option catalogue.

## Required release gates

| Area | Required evidence |
|---|---|
| Appearance | Stable hair silhouette, palette-consistent strands, readable eyes/mouth/teeth through speech, and identity consistency across face/skin variants. |
| Fit | Natural shoulder/armhole/cuff/hem shapes; no visible holes, clothing intersections or crotch distortion through the representative action set. |
| Finish | Fabric-specific shading and seam construction; no duplicated dark occlusion, floating ribbons, jagged boundaries or temporal shimmer. |
| Hands/contact | Anatomical wrists and fingers; sleeve clearance; intended clothing contact without penetration or hovering. |
| Catalogue consistency | Every selectable garment/accessory and relevant combination passes the same still/motion criteria, including recolouring and all preview formats. |

Remaining work includes source garment shape/weight corrections, hair-end silhouette cleanup, sleeve/hand contact refinement, fabric-specific detail, complete catalogue propagation, full-quality motion and signed-in app acceptance. The initial shading and edge-construction candidates alone do not complete these gates.

Rejected experiment: an outward shell obscured the existing stitching ribbons. The structure candidate uses an inward shell, preserving the authored outer surface and visible seam work.

Motion investigation: the trouser line proxy has non-manifold edges, so its Surface Deform modifier reports `bound False`. An opt-in fallback interpolates the garment skin weights at each ribbon point, inverts the blended bind-pose transforms, and binds the ribbons to the same rig. Its bind-pose residual must be below 0.1 mm; source garment topology is untouched. This fallback requires verification before acceptance.

## Verified stitching fallback

The reference trousers' rig-weight binding passed 120 samples from frames 240–597 (step 3). Across the sampled ribbon vertices, the maximum nearest-surface separation was 0.000652591 m (0.653 mm). Twenty-three visible/source meshes remained finite and byte-identical at the vertex-coordinate level; fitted object and mesh counts stayed stable. `male-binding-verification.json` contains per-frame results and mesh hashes. These are deformation/attachment checks, not a claim that every hand/clothing contact is visually accepted.

Reproduce the reference using `python3 scripts/cast-quality-reference.py --character male --output-dir /path/to/review --blender /path/to/blender --structure`. Add `--motion 240 597 3` for the continuous proxy. Use `--baseline` for the preceding production appearance. The output folder contains logs, request, assembled scene and render metadata.

## First-pass visual evidence and limits

Both initial material-pass motion sequences completed all 120 renders (15 seconds per character at the source-derived 8 fps proxy rate). The diagnostic combines those original-action sequences side by side. It predates the subsequent hair-detail recolouring, earring-parent correction, edge-thickness and stitching-binding refinements; do not present it as a final candidate reel. Latest frame-27 and frame-338 reference renders exercise the newer candidates.

The woman also passed a 120-pose finite-geometry/source-preservation audit with valid visible bone parents. All eleven original source .blend files match their Git blob hashes; see `source-verification.json`.

The button-down pilot deliberately bypasses the production material's rest-pose occlusion override, which otherwise reintroduces the baked dark patches after assembly. It retains the selected hue and uses a restrained normal gradient plus short-range live contact shade. Skin and face material grading remains the approved reference.

This is the first engineering milestone. It has not achieved the requested 9+ across all five areas. Hair-end silhouettes, natural shoulder/sleeve shapes, fabric-specific construction, hand/contact poses, full-quality temporal line stability and the rest of the wardrobe still need correction and acceptance. The latest pilot changes are not activated in the app or deployed.
