# NexStudio presenter reference

State of the two presenters as of 2026-09-30. Everything here is a working
copy; the originally delivered `NEXSTUDIO_V1_MALE.blend` and
`NEXSTUDIO_V1_FEMALE.blend` were never modified.

## Current character files

| File | Contents |
| --- | --- |
| `characters/NEXSTUDIO_V1_MALE_v6.blend` | Watch removed; thinner brows; larger irises; mouth stray strokes off; hair strand texture; softened armpit shading; teeth and mouth interior refitted so the closed lips read as one seam; subtle shading baked into skin, shirt, trousers, shoes and hair. |
| `characters/NEXSTUDIO_V1_FEMALE_v3.blend` | Appearance as approved, plus the hair hem sculpted into strand tips with groove separation, and subtle shading baked into skin, dress and hair. |

## Shipping decisions

- Front-facing only. Side and 3/4 views were rendered, reviewed and rejected.
- Seated pose was tested and dropped.
- Framing is hips-up (slightly below the hips) with both hands always visible,
  presenter centred, roughly half the frame left clear for kinetic subtitles
  and infographics.
- Delivery sizes: 1920x1080, 1080x1080, 1080x1920.
- Male hair options offered: quiff and bald. Afro and culturalibre are removed
  from the offered set (meshes remain in the file) because of missing side and
  crown coverage.
- No watch.
- No black contour anywhere inside the mouth: teeth, tongue and mouth interior
  are excluded from the contour pass.

## Shading

Every material in these files is a flat Emission shader, so a surface renders
the same value regardless of which way it faces. `scripts/render_shaded.py`
adds, per material group, a soft key-light gradient, contact shading in the
crevices and a restrained highlight, then feeds the result back into the
emission colour. Ink and line-art materials are left flat so the drawn lines
stay crisp.

Approved level: subtle (`level = 1.0`).

| Group | Materials | Character of the treatment |
| --- | --- | --- |
| Skin | `PEEPS_V2_WARM_SKIN`, `V60_EAR_SKIN` | Warm shadow tint, contact shading under the jaw, inside the collar and between the fingers, faint sheen on forehead, nose and cheekbones. |
| Garments | `V70_G_elvs_male_shirt_untucked_bd1`, `V70_G_mindfront_male_trousers_2`, `V70_G_mindfront_shoes_monk_strap_male`, `V63_DRESS_mindfront_f_dress_11` | Cooler shadow tint, wider contact distance, very low highlight so fabric turns without looking wet. |
| Hair | `LINEART_HAIR_PAPER` | Narrow warm sheen band along the strand direction. A wide or white band desaturates the hair into a grey cap and must be avoided. |

`scripts/bake_shading.py` writes those node chains into a new `.blend`. A baked
file rendered at `level 0` is pixel-identical to the source file rendered at
`level 1`, which is how the bake was verified.

Levels 0, 1 and 2 of the skin-only comparison that produced this decision are
in `previews/shading_ladder/`.

## Line weight

Two ink settings are defined in pixels at the character files' native
2880x4320 output, so both must follow render height or the outlines read far
too heavy:

- Freestyle lineset thickness scales by `height / 4320`, applied to every
  lineset, not just one.
- The character compositor's contour Dilate/Erode size scales by
  `height / 2160`, floor of 1.

Missing the second one is what produced the heavy neck outline: skin and
collar pass-index boundaries meet there, so the contour concentrates at the
neck. Both are applied by `scripts/render_shaded.py` and
`scripts/render_presenter_alpha_v2.py`.

## Backgrounds

Ten scenes, stable IDs: `living_room`, `home_office`, `creator_studio`,
`workplace`, `cafe`, `kitchen`, `library`, `classroom`, `terrace`,
`neutral_studio`. Each exists in two catalogs — photographic realism and a
character-matched illustrated version — with a dedicated composition per
aspect ratio rather than a crop of one wide image, which is what caused the
earlier vertical tiling in portrait.

Background cards must not light the presenter: the card material routes
through `Light Path -> Is Camera Ray` so it is visible to the camera and casts
nothing. Skipping this washed the female presenter out.

Catalogs ship separately as `NexStudio_Realistic_Background_Catalog.zip` and
`NexStudio_Illustrated_Background_Catalog.zip`. Their composites still use the
pre-shading presenters and need rebuilding against the files above.

## Rendering notes

CPU-only box, no GPU: roughly 7 seconds a frame, so a 720p 5-second reel takes
8-10 minutes at best. Eevee is slower than Cycles in software mode (53s vs 32s
a frame, measured). A modest GPU renders this scene at 0.3-0.5s a frame, which
is the real fix for both drafts and production.

## Open items

- Rebuild both background catalogs with the shaded presenters.
- Garment shading gains least on the male shirt, which already carried painted
  gradients; the garment level can be pushed on its own if more sculpting is
  wanted.
- Optional skin tone presets per character are proposed but not built.
- Afro and culturalibre need real sculpting before they can be offered.
