# Cast plate pipeline — handoff

How the browser-side Cast builder gets its layered character plates, and how to
re-bake them after touching the character system. READ `presenters_v1/REFERENCE.md`
first — this doc only covers the plate pipeline on top of it.

## Prerequisites

- Blender 5.2.x headless (the compositor API used here is 5.2-specific).
- Python deps for the packer: `pip install numpy pillow scipy OpenEXR`.
- The MakeHuman asset library: clone the `mh-assets` branch of this repo and
  point `MH_ROOT` at it:
  ```bash
  git clone --single-branch -b mh-assets https://github.com/Admiano/nexstudio mh_assets
  export MH_ROOT=$PWD/mh_assets
  ```

## What the plates are

The Cast builder (`src/studio-v2/cast/` in the app) draws a presenter live by
stacking ~9 transparent PNG plates per option pick: body -> lips -> watch ->
outfit -> neck -> earring -> hair -> hands. Each plate is a 720x1080 RGBA PNG in
`public/cast/`. Every plate ships **only pixels the authored render itself
attributed to that plate's objects** — nothing is synthesized, nothing is cut
out of a flattened composite. A composite of the extracted plates reproduces
the authored look render to within option-swap pixels (~2-8k px of 777k).

## Bake

`castbake3.py` renders the full scene per look and writes, per shot:
- `<shot>.png` — the visible render (1440x2160, frame 27, Cycles 12 samples,
  freestyle at authored weight, film transparent)
- `z_<shot>.exr` — multipart EXR with Depth + three cryptomatte object-ID parts
- `plates.json` — manifest mapping each plate name -> source shot + keep-list
  of `bpy` object names

```bash
cd engine_sources/makehuman-lineart
export PV1=$PWD/presenters_v1/scripts MH_ROOT=/path/to/mh_assets
source $PV1/env.sh

# one LOOK per invocation:
LOOK=fem_long   OUT=/path/to/bakeout blender -b presenters_v1/scenes/BASE_V58.blend \
  --python presenters_v1/scripts/castbake3.py
```

| LOOK | what it bakes |
|---|---|
| `fem_{long,bob,bangs,bun,braid}` | one hairstyle look: outfit + earring + all 5 hair colors + the shared neck plate renders |
| `male_O1..O5` | one ensemble: outfit + all 5 hair colors + bodyset |
| `male_watch_o1..o5` | the 5 watch plates seated for that outfit (cuff-aware) |
| `fem_body` / `male_body` | 18 nude renders: 3 faces x 6 skins (whole-chassis plates + hands masks) |
| `fem_hands` / `male_hands` | hand-hull JSONs only (no renders; run once, outputs are stable) |

STONE is pinned to `E0B48F` inside the bake so look renders compare equal to
the `medium` body plate.

## Pack

`castpack4.py` reads `BAKE_OUT` (default `/home/ubuntu/work/castbake3`):
extracts each plate by cryptomatte object id, ships bodies whole, builds the
hands layer per outfit + skin, and writes the finished set to `PLATE_DST`
(default `public/cast/` in the app checkout).

```bash
BAKE_OUT=/path/to/bakeout PLATE_DST=/path/to/nexstudio/public/cast \
  python3 presenters_v1/scripts/castpack4.py
```

Then bump `PLATE_V` in `src/studio-v2/cast/spec.ts` (e.g. `v8` -> `v9`) so
browsers drop cached plates, and commit `public/cast/` + `spec.ts`.

## Verify before shipping

Compose each look from plates and diff against the authored look render
(`<bakeout>/fem_look_<style>.png` flattened onto the cream background —
the renders have a transparent film). Expect ~2-8k differing px (the option
swaps a look doesn't share, plus 1-2 px ink edges). A diff in the tens of
thousands means a layer is eating pixels — check the body plate first:
garment `Delete.*` MASK modifiers on `Host.body` must be off for nude
renders (castbake3 handles this) or covered skin regions ship empty.

## Gotchas that cost real time

- The EXRs are **multipart**: read parts via `OpenEXR.File(path).parts`
  (`p.name()` is a method; channels are lowercase `crypto.r` etc.).
  `InputFile` reads part 0 only.
- Crypto ids: manifest hex -> `np.uint32(int(h,16)).view(np.float32)`,
  not `bytes.fromhex`.
- Freestyle strokes carry no crypto id. Ink ships only where it sits on a
  kept surface or overhangs kept content near empty background — face-art
  strokes under hair, and strokes behind garments, must die.
- The wig meshes contain a recessed face-shell. Solo renders expose it;
  only crypto extraction keeps it out of the hair plate.
- `Host.V64_sd_proxy` renders nothing — "no crypto id" warnings for it are
  expected, not a bug.
