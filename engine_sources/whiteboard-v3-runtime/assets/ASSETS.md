# Vendored assets — provenance & licenses

All assets in this directory are cleared for commercial use without
attribution (CC0 / public domain) or under MIT with the license text kept
alongside. Keep this file updated when adding assets.

## custom/ — bespoke illustrations (the per-label "aha" path)

Any label can get custom art: drop a stroke-only SVG at
`assets/custom/<slug>.svg` where slug is the lowercased label with
non-alphanumerics → `-`. `icon_for` resolves bespoke art ahead of every
generic vocabulary path (full-label slug first, then last-word slug).

Recipe: `python3 tools/vectorize_sketch.py art.png --name my-concept`
(vtracer converts commissioned/hand-drawn/AI line art to strokes).
Source art must be black marker lines on white, no fills — like the
`bee-swarm.svg` and `crowded-platform.svg` demos in this directory,
which were AI-generated and vectorized as pipeline demos.

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
- `inter/` — Inter v4.1 Regular/Bold/Black TTFs — © Rasmus Andersson,
  SIL OFL 1.1 (`inter/LICENSE.txt` included). The kinetic-type renderer's
  grotesk display face; vendored so kinetic reels need no system fonts.
- `barlow-condensed/` — Barlow Condensed Regular/Bold/ExtraBold TTFs —
  © The Barlow Project Authors, SIL OFL 1.1 (`barlow-condensed/OFL.txt`,
  from github.com/jpt/barlow via google/fonts). The kinetic renderer's
  default `--face condensed` display face; Regular carries plain text and
  ExtraBold carries active/emphasized words — the heavy condensed display
  look that fills lines at 9:16.
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

## ctrlv/ — scene vignettes (1,019 SVGs)
- Source: ctrlv.design illustration catalog (`js/illustrations-data.js`),
  extracted to per-illustration SVGs + `index.json` (title/tags search
  index). CSS color variables resolved to ink `#1A1A17` / paper `#F5F0E4`.
- License: CC0 public domain — commercial use, no attribution.
- Role: scene-level vignette layer — descriptive labels ('fire rescue',
  'crypto wallet', 'delivery truck fleet') match via title+tags when a
  meaningful word anchors the match and the art carries enough ink to read
  at icon scale (`_illust_lookup` + `_illust_ink`).

## flowbite/ — scene vignettes (54 SVGs)
- Source: `themesberg/flowbite-illustrations` (MIT, Themesberg), light/outline
  variants only. People-in-context scenes (tutoring, shopping, repairing…).

## doodles/ — sketchy figures (31 SVGs)
- Source: Open Doodles by Pablo Stanley (opendoodles.com), CC0.
- Loose hand-drawn figures — the closest match to the whiteboard aesthetic;
  also the fallback actor art for action-word labels ('runner', 'reader',
  'dancer').

## icons/tabler/
- `tabler-nodes-outline.json`, `icons.json` — Tabler Icons v3.35.0
  (MIT, © Paweł Kuna; npm package `@tabler/icons`). 4,964 stroke-style
  outline icons as inline path data + a category/tag search index. This is
  the domain-agnostic vocabulary layer: any concept label (animals,
  healthcare, forestry, transport, finance…) resolves to a drawn icon via
  the tag index; unresolvable labels fall back to a lettered card —
  never a blank tile. `LICENSE` included.

### icons/phosphor + icons/fluent + semantic/
- `assets/phosphor/` — Phosphor Icons regular weight, 1,512 SVGs. MIT.
- `assets/fluent/` — Microsoft Fluent Emoji "High Contrast" line-art variant,
  1,285 SVGs + index.json (CLDR name/keywords/group per emoji). MIT.
- `assets/semantic/synonyms.json` — WordNet-derived lemma relations
  (~49k entries: synonyms + hypernyms + hyponyms + entailments, one hop,
  single-token lemmas). Vendored snapshot — deterministic, no runtime dep.
  Princeton WordNet license (free for commercial use).

### sfx/
- `marker-real-bed-48k.wav` — real board-drawing strokes extracted from
  user-supplied Freesound recording 'blackboard4' (freesound id 19968).
  Freesound community uploads are CC0/CC-BY — verify attribution need
  before commercial release; drop-in replaceable via ROLE_FILE patch.
- `marker-scratch-bed-48k.wav` — synthesized fallback bed.
- `pencil-bed-48k.wav`, `pen-cap-48k.wav` — preserved-runtime audio assets.


### icons/openmoji
- `assets/openmoji/` — 473 people/activity line-art glyphs (base set;
  skin-tone variants dropped), flattened to stroke-only paths by
  `tools/openmoji_pack.py` + `index.json` (slug → tokens/annotation/group).
  OpenMoji project, CC BY-SA 4.0 — attribution required in any shipped
  video that draws them (see `assets/openmoji/LICENSE-NOTICE.txt`).
  Downloadable set: https://github.com/hfg-gmuend/openmoji/releases

### icons/animicons
- `assets/animicons/` — 79 self-animating icon sprite strips (useAnimations
  Lottie set) baked by `tools/animicons_pack.py`; `index.json` maps slug →
  lookup tokens. Icons marked `animicon` play their own animation inside
  their draw window instead of stroking on. CC-BY 4.0 — attribution
  required in shipped video (see `assets/animicons/LICENSE-NOTICE.txt`).

### fx particle marks
- `assets/fx/` — 29 Kenney Particle Pack sprites (CC0) rebaked to 128px
  alpha PNGs (luminance→alpha); `index.json` maps mark names (spark,
  star, magic, smoke, glow, trail, twirl, ring, slash, dust...) to
  variants. 'fx' groups paste them alpha-tinted in the accent color at
  an icon's corner — upgrade of the procedural sparkle marks.

### icons/notomoji
- `assets/notomoji/` — Noto animated emoji (CC-BY 4.0) baked by
  `tools/notomoji_pack.py` to 160px palette PNG strips + index.json.
  609 base emoji baked (skin-tone variant dirs skipped); joins the
  sprite-slot path alongside animicons — naming a notomoji slug in an
  icon slot plays the animated emoji.

### characters/proto (the whiteboard cast)
- `tools/nexstick/baked/PROTO_*/` — RGS_Dev 'Animated Prototype
  Character' pack (CC0, user-supplied zip; https://rgsdev.itch.io/).
  `tools/nexstick/proto_pack.py` imports each action set to baked dirs:
  PROTO_IDLE/WALK/RUN/JUMP/ROLL/SLIDE/ATTACK/HIT/DEATH plus weapon
  variants (PROTO_SWORD_*, PROTO_PISTOL_*, PROTO_RIFLE_*).
- `tools/nexstick/baked/PROTO_EX_*/` — the exercise set drawn from
  `compiled/exercise_vault_v5.json` by `tools/nexstick/proto_rig.py` in
  the same proto style (circle head, tapered torso, stick limbs, dot
  hands, shoe tips). 18 clips (push-up, plank, burpee, squat, lunge,
  deadlift, jumping jack, bear crawl, mountain climber, dips, curls,
  presses, pulls, bird-dog, glute bridge, sit-up, kettlebell swing,
  downward dog). Per the cast's charter only exercise motions are added
  to what the pack already has.
- `fig_motion.resolve_clip` prefers the proto cast for say-resolved
  clips via `_PROTO_ALIASES`; plans may also name PROTO_* clips
  verbatim in beat.figure.
