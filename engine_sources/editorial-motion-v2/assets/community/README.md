# assets/community — vendored license-clean asset pool

Mined from global open-source/asset communities to close the v3.1 audit gaps.
Every asset carries source pack, upstream license and sha256 in `manifest.json`
(audio/music/textures/surfaces) or `icons-registry.json` (icons). Icons are
normalised to `currentColor` — ink and accent stay runtime-owned.

## Icons — `icons/` + `icons-registry.json` (5,217 materialised)

| pack | license | origin | count |
|---|---|---|---|
| lucide | ISC | global | 700 |
| icon-park-outline | Apache-2.0 | ByteDance (CN) | 700 |
| tabler | MIT | global | 700 |
| mingcute | Apache-2.0 | MingCute Studio (CN) | 700 |
| ri (Remix Icon) | Apache-2.0 snapshot → now "Remix Icon License v1.0" (free for product use, attribution optional, no standalone resale) | Remix Design (CN) | 700 |
| healthicons | MIT | Resolve to Save Lives | 700 |
| carbon | Apache-2.0 | IBM | 700 |
| ant-design | MIT | Ant Group (CN) | 317 |

Filtered to explainer domains: food, health, finance, time, nature, people,
comms, objects, transport, tech, emotion. Source icon data for all 19,640 icons
lives in `packs/<slug>/icons.json`; re-run `tools/build_community_registry.py`
after editing its `DOMAINS` vocabulary to materialise more.

## Colour art — `colour/` + `colour-registry.json` (12,420 native-colour SVGs)

Rendered as-is (`colour: native`) for the PRODUCT_COLLAGE finish — brand tiles,
emoji, 3D-look emoji and coloured pictograms. Ids: `brand.logos.*`,
`brand.si.*`, `emoji.fluent.*`, `emoji.fluent-flat.*`, `emoji.noto.*`,
`icon.fluent-color.*`, `icon.icon-park-color.*`.

| pack | license | origin | count |
|---|---|---|---|
| simple-icons 16.31.0 | CC0-1.0 | global | 3,460 |
| SVG Logos (gilbarbara/logos) | CC0-1.0 | global | 2,174 |
| IconPark (colour) | Apache-2.0 | ByteDance (CN) | 2,658 |
| Fluent Emoji + Flat | MIT | Microsoft | 2,471 |
| Noto Emoji | Apache-2.0 | Google | 1,458 |
| Fluent UI Color Icons | MIT | Microsoft | 199 |

Brand marks are licence-clean as artwork; trademark use is the film owner's
responsibility (see `trademark_note`). Rebuild with `tools/build_colour_registry.py`.

## Audio — `audio/` (477 files, CC0)

| dir | source | use |
|---|---|---|
| kenney-ui-audio | kenney.nl (CC0) | clicks, switches, rollovers — word-land accents |
| kenney-interface-sounds | kenney.nl (CC0) | UI confirmations — state-change accents |
| kenney-impact-sounds | kenney.nl (CC0) | hits — emphasis/FULL_FRAME_HIT accents |
| kenney-music-jingles | kenney.nl (CC0) | 86 jingles — beat/payoff stingers |
| wooshes-organic | NazdyNate via cc0-sounds.exi.software (CC0) | swish/twirl/whoosh — transition motion |
| paper-cutter | CaptSubtle via cc0-sounds.exi.software (CC0) | paper cuts — TEXT_MASK_WIPE / editorial feel |
| paper-books-writing | bumblebeast via cc0-sounds.exi.software (CC0) | page turns, pencil — editorial texture |

## Music — `music/freepd/` (10 tracks, CC0)

FreePD corpus (Kevin MacLeod public-domain collection) fetched via the
SoundSafari CC0-1.0-Music GitHub corpus. Calm/jazz/ukulele beds for ducking
under voice. Closes the `SILENT_UNTIL_RIGHTS_CLEAN_SOURCE_SELECTED` gap.

## Textures & surfaces — `textures/`, `surfaces/`

- `paper006-color-1k.jpg` + displacement — ambientCG Paper006 (CC0): organic
  paper grain for PAPER-finish stages.
- `grain-fine-256.png`, `dots-24.svg`, `grid-24.svg`, `graph-paper.svg`,
  `hatch-45.svg` — generated in-repo (NexStudio-authored, no license) for
  grain overlay, dot grid, field grid, hatch.

## Easings — `easings.json`

Standard published cubic-bezier constants (easings.net/anime.js, MIT) mapped to
motion roles (enter/exit/emphasize/settle/wipe) + spring parameter presets for
the future physics channel.

## Deliberately not vendored

- **DOVA-SYNDROME, Sound Effect Lab, PeriTune, Amacha** (JP free-music/SFX
  sites): licenses permit use *inside rendered works* but forbid redistributing
  raw files — fine for a render, wrong for a repo.
- **GSAP**: now free post-Webflow but not OSI-licensed.
- **unDraw / Storyset / Blush**: custom licenses prohibit reuse as an asset
  library inside a competing design tool.
- **OpenMoji, Hero Patterns, Subtle Patterns**: CC BY-SA share-alike — usable
  but flag-worthy; skipped for cleaner licenses.
- **Noto CJK variable fonts** (OFL): 20–100 MB per face; only worth it when a
  CJK pipeline is real.
