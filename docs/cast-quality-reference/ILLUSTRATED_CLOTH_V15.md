# Illustrated wardrobe V15

V14 skin and V11 hair are the approved visual reference. The clothing pass leaves
those source modules, facial anatomy, body cages, body shape keys and original
armatures unchanged. V15 updates all five female dresses and the ten independently
selectable male tops and bottoms, with selected male footwear shaded as leather
or canvas.

The previous broad screened highlights and view-dependent edge darkening made
fabric appear smooth and rubbery. Selected garment materials now use restrained
painted colour planes, short-range contact shadows and pigment weave attached to
rest coordinates. Cotton, crepe, pique, jersey, knit, wool, denim and satin have
different pattern scales and strengths. No physical gloss, scattering or raised
micro-bump is introduced. Exact preset and custom base colours remain the input.

The burgundy long-sleeve maxi retains its source garment and rig. Its original
low opening becomes a covered, shallow bateau neckline using an additive garment
shape key. A connected neckline boundary and harmonic panel deformation preserve
the original Basis cage. New upper-chest weights are interpolated from the actual
body skin surface, excluding MakeHuman helper cages. Seam artwork is rebuilt on
the revised fitted garment and bound to a proxy without thickness modifiers.
Other female dresses receive at most 14 mm of front-panel ease at the bust.

The versioned worker applies clothing before posed garment clearance. Reviews of
saved scenes also update materials shared with fitted preview meshes, so hidden
source trousers receive the same finish. Server-owned feature flags cannot be
set by client requests. The preview version changes to
`approved-v3-v6-cloth-v15-illustrated-upper-thigh` to invalidate old renders.

## Review and validation

See `v15-cloth-verification.json` for actual rendered images, checksums and audit
results. Clothing audits compare protected geometry, skin/hair materials, bones
and hair curves before and after the clothing pass. They check reapplication,
rest-coordinate stability, custom garment colours and finite evaluated meshes
at frames 1, 27, 71, 338 and 891. The maxi also has visual three-quarter and
speaking-pose reviews. Existing renderer configuration, complexion, queue and
worker tests remain required.

V14 skin SHA256:
`1b67dfa4d71eebd2c2a2a1033c862b080881cd833eee7595b3e2af7addfa3402`.

Changes are a reviewable local source patch and Blender scenes. They have not
been published, merged or deployed. Original source assets remain unchanged.
Female source footwear is retained; this pass concentrates on dresses, their
necklines and the selectable male wardrobe. Blender scenes include the original
rig/action; production renders rebuild pose-specific clearance for each frame.
