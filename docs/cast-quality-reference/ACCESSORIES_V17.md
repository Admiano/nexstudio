# Illustrated accessories V17

Rebuild the existing five watch and five neck selections after the approved illustrated skin, hair and clothing passes. Earrings retain the existing hair-linked five silhouettes. Source bodies, facial shape keys, rig and animation actions are preserved.

## Detail

- Analog and dress watches: fine dial markings, machined bezel edges, attachment lugs, side crowns and stitched leather.
- Digital and smart watches: rounded cases, readable 10:08 displays, actual activity arcs for smart.
- Chronograph: minute scale, three subdials, separate hands, crown/pushers and bracelet joints.
- Neck jewellery: interlocking oval links, whole pearls, fitted pendant setting, fine metal shading and restrained highlights.
- Earrings: clasps/posts, pearl settings and a true tapered teardrop.
- Neckerchief/choker: fabric edge thickness, softer edges and distinct fabric finishes.

## Fitting

The V17 neck target copies the source body, preserves the `Hide helpers` mask, removes only clothing masks, and evaluates subdivision at the final render level. Inside-out radial rays avoid picking the opposite shoulder. Accessories bind with Surface Deform to follow the skin while retaining volume. Previous full-skin clearance targets contained internal helper geometry and must not be used as jewellery fitting targets. Watches retain the original rigid lower-arm attachment.

## Source checkpoint

This change also restores the final saved V14–V16 renderer modules from `NEXSTUDIO_V16_SOURCE_AND_VERIFICATION.zip`, because the GitHub checkpoint contained V12 while the approved V16 scene bundle already used the later illustrated passes. The preserved skin source SHA256 is `1b67dfa4d71eebd2c2a2a1033c862b080881cd833eee7595b3e2af7addfa3402`. Render cache version becomes `approved-v3-v6-accessories-v17a-upper-thigh`.

## Review scope

The review images are actual fixed-camera Blender renders of the saved V16 scenes, with front and angled views kept separate. Accessory detail uses the cocktail female and polo male scenes for a consistent comparison. Numerical motion checks verify finite evaluated geometry and unchanged body/facial source data; they do not constitute exhaustive collision certification or a full application build. Native scenes and verification reports accompany the preview set. Ten accessory selections were sampled at 125 poses in total, and one representative selection was assembled on each of the ten outfits at three additional poses. The refined scarf was checked again at its 12 sampled poses. Worker tests and the existing complexion/cache configuration test pass; full application dependencies were not installed in this verification workspace.

## Watch alignment correction

V17a places the face, case and strap on the same default axis. Optional tilt rotates about the case centre instead of the wrist centre, so its radial offset cannot shift the face towards twelve o’clock. All five case centres are checked against the band centre along the forearm; dial/screen centres are checked against the case face normal. Front and fixed-angle images are rendered again, and the native chronograph scene is rebuilt.
