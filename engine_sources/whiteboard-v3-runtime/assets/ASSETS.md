# Vendored assets — provenance & licenses

All assets in this directory are cleared for commercial use without
attribution (CC0 / public domain) or under MIT with the license text kept
alongside. Keep this file updated when adding assets.

## open_peeps/ — 7 authored pose SVGs
- Source: shipped inside the approved V3 source bundle
  `NEXSTUDIO_WHITEBOARD_APPROVED_V3_SOURCE_FOCUSED_2026-09-18.zip`
  (`01_CORE_ASSEMBLED_PACKAGE/.../assets/open_peeps/`).
- License: Open Peeps is CC0 (public domain), © Pablo Stanley.

## peeps/ — full Open Peeps library (205 SVGs)
- Source: extracted from `CeamKrier/react-peeps` (MIT), which redistributes
  the Open Peeps vector set. Part .tsx components were converted to plain
  SVG preserving group/path `translate()` transforms and fill roles
  (`#000000` = ink layer, `#FFFFFF` = paper/skin layer).
- Layout:
  - `parts/pose_standing|pose_sitting|pose_bust/` — body poses (65)
  - `parts/hair/` (51), `parts/face/` (33), `parts/facial_hair/` (16),
    `parts/accessories/` (9)
  - `composed/` — ready-made full figures (standing + sitting, default
    Short hair + Smile face) (24)
  - `cast/` — character variants with distinct hair/face/facial
    hair/accessory combos (8)
- Compose rule (mirrors react-peeps `head/index.tsx`): head group =
  `translate(225 0)` containing hair (no offset), face at
  `translate(159 186)`, facial hair at `translate(123 338)`, accessories at
  `translate(47 241)`. The head/neck silhouette is drawn by the pose's
  paper layer.
- License: Open Peeps artwork CC0; react-peeps source MIT (Cem Krier).

## hand/drawing-hand.png
- Marker-hand overlay sprite, 1069×1472 RGBA, nib tip at ~ (105, 70) in the
  original frame.
- Source: `geeklee/srt-whiteboard-animation` (`assets/drawing-hand.png`),
  MIT license. Barrel branding text removed for commercial neutrality.

## fonts/
- `PermanentMarker.ttf` — © Font Diner, SIL OFL 1.1 (marker-style headline)
- `RockSalt.ttf` — © Sideshow, SIL OFL 1.1 (chalk/marker hand)
- `Caveat.ttf` — © Pablo Impallari, SIL OFL 1.1 (handwriting, variable
  weight)
- `OFL.txt` — the SIL Open Font License text covering the fonts above.
- `hershey_occidental.json` — Hershey single-stroke vector font data
  (public domain; JSON encoding by scruss, dual CC0/WTFPL). 1570 glyphs —
  usable for true stroke-drawn lettering reveals.

## sfx/
- `*.ogg` — Kenney "Interface Sounds" (CC0, kenney.nl), 100-asset pack;
  vendored subset covers pen-scratch strokes (`scratch_*`), reveal ticks
  (`tick_*`, `select_*`, `pluck_*`, `confirmation_*`), notification pings
  (`question_*`, `glass_*`, `bong_*`, `drop_*`). `KENNEY_LICENSE.txt`
  included.
- `whoosh.wav`, `pop.wav` — generated in-repo (numpy synthesis), no
  third-party rights; replaceable with a sourced pack later.
