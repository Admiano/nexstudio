# Illustrated skin V14

The V13 physical skin pass made the characters read as sculpted rubber figures. This revision restores the drawn character direction: restrained coloured plane shading, expressive feature contours and quiet complexion colour. It supersedes the unapproved V13 physical finish.

The skin surface uses emission with camera-relative original surface normals guiding an eased four-stop colour ramp. Shadows carry a restrained warm colour instead of deep grey sculptural cavities. There is no Principled skin, subsurface scattering, surface bump, pore relief, or view-dependent sheen. Small contact shading is limited to 6 mm and 8% influence. Fine pigment variation is limited to 0.994–1.006 in linear colour. Lip colour preserves the original semantic boundary and separate upper/lower colours without gloss. Female blush and eyelid wash are reduced.

The exact selected complexion remains the stored linear base colour for all six presets and custom colours. Original meshes, shape keys, bone weights, UVs, rigs and mouth controls are preserved. Rest-space attributes keep colour accents attached during animation. The refined lateral ear contour cleanup is retained without mesh edits.

Supporting studio lights continue to serve the existing hair and wardrobe. They are reapplied after hair grooming so assembly cannot silently replace the reviewed setup. Skin brightness is governed by the illustrated colour shader, not the physical lights. This pass does not redesign the V11 groom, wardrobe, or V12 dental anatomy.

Cache version: `approved-v3-v6-skin-v14-illustrated-upper-thigh`.

Review helper: `scripts/render-skin-illustrated-review.py`. Run with an assembled production `.blend` and arguments `character output.png frame size view [skinHex]`; views are `front`, `quarter`, `profile`, `detail`, and `skin`. Render checks use the actual Blender scene and original animation.

The accompanying verification JSON records the exact shader checksum, audited geometry, colours, pose frames and completed render files. The visual direction remains subject to the user's review; no numerical aesthetic rating is claimed. This local revision has not been published or deployed.
