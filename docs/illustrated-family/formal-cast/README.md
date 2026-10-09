# NexStudio V1 — Illustrated formal cast expansion

**Branch:** `work/illustrated-family-expansion-v1` (experimental; not merged into production).

## What actually exists

This is an **additional wardrobe bank for the two existing original characters**, not six new character identities. The canonical female/male scenes, rigs and performance actions remain unchanged. Six real CC0 MakeHuman clothing meshes are fitted to the same original `Host.rig`, with female CC0 flats and existing V1 male shoes. Each uses source UV textures and existing illustrated contour styling.

[Six-variant real Blender contact sheet](../qa/six-authentic-illustrated-formal-cast-variants.png) · [Female 10-pose integrity sheet](../gesture-qa/female-actual-rig-gesture-sweep.png) · [Male 10-pose integrity sheet](../gesture-qa/male-actual-rig-gesture-sweep.png)

The original scenes use Zstandard-packed `.blend` bytes despite the filename. Never edit them directly. The scripts decode into isolated disposable copies.

## Rebuild on a Linux machine

Requirements: exact SHA-verified Blender 5.2.0 LTS, `zstd`, Linux EGL libraries, Python 3, and access to upstream CC0 donor archives.

To see supported names:

```bash
python scripts/illustrated-family/build_formal_cast.py --list
```

For one original-rig variant:

```bash
python scripts/illustrated-family/build_formal_cast.py \
  --variant female-double-breasted \
  --blender /path/to/blender \
  --archive-cache /tmp/nex-v1-cast-archives \
  --output-dir /tmp/nex-v1-female-formal
```

Six names: `female-double-breasted`, `female-statement`, `male-jacket-tie`, `male-double-breasted`, `male-navy-classic`, `male-dinner-jacket`.

All six full editable proof scenes, front/three-quarter previews, two action-frame previews per suit, and SHA-256 provenance are produced by the GitHub workflow [V1 formal cast complete reproducible six-variant bank](../../../.github/workflows/illustrated-formal-six-build-bank.yml). The workflow uploads the **large editable Blender scenes as an artifact** while committing only lightweight verified PNG previews and JSONs in `docs/illustrated-family/formal-bank/`. Its BANK_MANIFEST.json is the source of truth for which variants rebuilt successfully.

Actual continuous-motion proof workflow: [V1 real moving formal presenter preview](../../../.github/workflows/illustrated-real-motion-clip.yml). It uses the existing original action's frame timing and is a silent gesture test, not a generated talking performance.

## Verified complete six-outfit handoff

On 2026-10-09 the recovery verifier passed all six canonical-rig outfits built by run `38003760983`. It independently checked 30 generated file hashes (one editable scene plus four PNGs per variant) and **reopened every saved compressed .blend in checksum-verified Blender 5.2.0** to confirm the 163-bone original `Host.rig`.

- **[Compact verified editable scene bank (~126 MB)](https://github.com/Admiano/nexstudio/actions/runs/38004823946/artifacts/11650637868)** — preferred user handoff; includes exactly 6 editable `.blend`, 24 real PNGs, per-outfit SHA provenance and full manifest. The earlier ~248 MB [source build artifact](https://github.com/Admiano/nexstudio/actions/runs/38003760983/artifacts/11650990397) contained unnecessary `.blend1` backups and logs. Both expire under GitHub Actions retention.
- [Source-generated six-variant BANK_MANIFEST.json](../formal-bank/BANK_MANIFEST.json) — verified individual hashes and source identifiers.
- [Individual first-person Blender previews](../formal-bank/) — four PNG render views per variant and separate provenance.
- [Moving female original-gesture MP4](../motion-proofs/female-actual-original-gesture.mp4) · [Moving male original-gesture MP4](../motion-proofs/male-actual-original-gesture.mp4) — both 4.25-second contiguous original-performance snippets, silent.
- [All six suits × ten original poses mechanical QA summary](../formal-bank-geometry-qa/QA_SUMMARY.json) — structural pass; **not** a full visual collision certification.
- [Three-quarter depth-corrected face experiment](../face-surface-trials/female-resolute-threeq.png) — **unapproved** until blink/visemes integrate correctly.

These are still **experimental V1 clothing presets**, not a production deployment or six different people. The missing collision and continuous-production acceptance gates remain in force.

## QA decisions

**Validated so far:** Source license and exact archive SHA, unmodified original rig presence, original body shape keys, original arms and garment skinning, 10 original-action frame renders for the first female and male formalwear, and one standalone reproducible formal builder example. More builds/render jobs must complete before marking them validated.

**Not yet approved:** seamless all-action collision behavior; extraordinary gestures/contact poses; a full-length speaking performance with synchronised audio and mouth; all camera angles, color-consistency and clothing intersections; authored face alternatives (their three-quarter registration remains problematic). Existing performance clips must not be replaced or deleted.

**Release rule:** Do not merge this branch as production-ready on successful CI alone. Review actual PNG/MP4 artifacts. Do not call these new distinct personalities or 'new cast faces' until real identity swaps are visually and morph-validated.

## Source provenance

Official source records: [suits01](../SUITS01_DONOR_PROVENANCE.md) and `experiments/illustrated-family/formal-wardrobe-trial-manifest.json`. Donor author Margaret Toigo (MRT), CC0 as recorded in each donor `.mhclo`. This CC0 license applies to donor clothes and flats only, **not** automatically to the original character scenes.
