# Illustrated presenter backgrounds

This is the character-matched companion to the separate photographic background catalog. The photographic files are unchanged. Both catalogs use the same ten scene IDs, so a scene can switch visual style without changing its name.

The room plates use simplified matte forms, selective ink edges, soft cel shading, restrained painted texture, and a subtle blue-gray accent. This gives the drawn presenters a consistent surrounding style while retaining recognizable contemporary spaces. They are generated illustrations rather than photos or 3D sets.

| Scene ID | Setting |
| --- | --- |
| `living_room` | Contemporary living room |
| `home_office` | Home office |
| `creator_studio` | Creator studio |
| `workplace` | Modern workplace |
| `cafe` | Neighborhood café |
| `kitchen` | Contemporary kitchen |
| `library` | Library and study |
| `classroom` | Training classroom |
| `terrace` | Garden terrace |
| `neutral_studio` | Neutral illustrated studio |

## Use

Pick `assets/<format>/<scene_id>.jpg` using the video's output aspect:

| Format | Final RGB asset | Independently composed source |
| --- | --- | --- |
| `landscape` | 1920 × 1080 | `masters/<scene_id>.png` |
| `square` | 1080 × 1080 | `variants/<scene_id>_square_source.png` |
| `portrait` | 1080 × 1920 | `variants/<scene_id>_portrait_source.png` |

`manifest.json` lists all IDs, output sizes, files, and sources. Use the exact matching format; do not stretch or tile an image. In portrait, keep the presenter centered and allow the room's defining details to appear at the edges. `neutral_studio` can receive a gentle outfit-aware tint; the nine recognizable rooms should keep their natural colors.

Alpha composite the presenter over the selected plate. For a Blender background card instead, multiply emission strength by **Light Path → Is Camera Ray**, so the plate cannot wash out the character. The original character assets were not edited.

Presenter ink is defined in pixels at the character file's native 2880x4320 output, so scale Freestyle lineset thickness by `height / 4320` and the character compositor's contour Dilate/Erode size by `height / 2160` with a floor of 1, then render the plate at delivery resolution.

`previews/contact_<format>.jpg` shows each scene behind both presenters. Individual JPGs and the six transparent preview overlays are also included. The characters in the previews use fast draft renders; the final background assets are at the dimensions above. Regenerate assets and previews using Pillow and `python prepare_assets.py`, then `python make_previews.py`.
