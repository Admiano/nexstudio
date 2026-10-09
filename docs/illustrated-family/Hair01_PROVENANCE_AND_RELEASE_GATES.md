# NexStudio illustrated V1 — hair donor research & integrity boundary

**Stage:** real-Blender variant tests, no production installation.

**Original rig authority:** original MakeHuman-based V1 female/male source; each has a 163-bone `Host.rig` and 34 body morph keys. Female current hairstyle is `Host.hair_culturalibre_hair_01`, male current hairstyle is `Host.hair_elvs_maxwell_hair`. Both are preserved on the original scenes.

**Authoritative Hair 01 donor archive:** `https://files2.makehumancommunity.org/asset_packs/hair01/hair01_cc0.zip`, ZIP SHA-256 `49445d69848a313ec41a9970f6a0fe4bcf925c9f1c6ef40a76f119c2e07940c9`.

## Licensing qualification — essential

**Do not conclude that every file inside a nominally CC0 asset pack is CC0.** Individual internal source headers conflict with the pack title:

- `toigo_blunt_bob_with_bangs.mhclo`: `# author MRT`, `# license CC0` — allowed for CC0 trial.
- `toigo_blunt_bob.mhclo`: `# author MRT`, `# license CC0` — allowed for CC0 trial but not currently rendered.
- `cortu_short_messy_hair.mhclo`: `# Cortu Johnstone - CC0` — explicit CC0 declaration in header, allowed for isolated CC0 trial.
- `rehmanpolanski_hair_bun_brown.mhclo`: `# license AGPL3` — **EXCLUDED**.
- `culturalibre_hair_02.mhclo`: `# license AGPL3` — **EXCLUDED**.
- `elvs_french_braid_variation.mhclo`: `# license AGPL3` — **EXCLUDED**.

This is a license-compatibility filter for the donor assets only, not a statement about the license of the existing saved V1 character files or their embedded components. Do not redistribute original V1 rig under an invented CC0 license.

## Trial recipe and release boundaries

CC0 replacements are built from the real MakeHuman `.mhclo` fit onto original shaped body vertices, use original V1 line-art hair material and the unmodified `Host.rig` head/neck bones, then save an independent experimental `.blend` and actual Blender-rendered front, three-quarter, close headshots, pose338 and pose891 PNGs. No external image generation.

**Release gates:** review silhouette, ear/scalp penetration, jaw/eye occlusion, neck movement, flat-shaded illustration finish and multiple extreme gesture frames. An accepted license, successful render or unchanged rig inventory alone never approves a hairstyle. Keep previous hairstyles selectable and do not merge new hairstyles into production until the visual and animation checks pass.

The initial experiment workflow is [V1 genuine CC0 alternate hairstyles on original character rigs](../../../.github/workflows/illustrated-alternate-hair-real-proofs.yml). Individual published test previews, when validated, belong under `docs/illustrated-family/hair-trial-previews/`.
