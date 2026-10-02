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
