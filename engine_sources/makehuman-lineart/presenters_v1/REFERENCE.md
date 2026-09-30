# NexStudio V1 presenters — reference

Two illustrated presenters that share one performance: the female **Host** and the
male presenter (built on the Guest male body and skeleton). Both run the same
frozen gesture, breathing, gaze, blink, expression and lip-sync take
(998 frames @ 24 fps, 41.6 s).

## Saved scenes (`scenes/`)

| File | Contents |
|---|---|
| `BASE_V58.blend` | Source scene (female face polish V58). Every look is built from this. |
| `NEXSTUDIO_V1_FEMALE.blend` | Default female look, ready to render: long hair + gold hoop, auburn, light skin, soft-rose lips, fine gold chain, navy tailored sheath. |
| `NEXSTUDIO_V1_MALE.blend` | Default male look, ready to render: textured quiff, brown hair, tan skin, light-blue untucked shirt + tan trousers + monk straps, dress watch, relaxed arms. |

Both saved scenes render pixel-identical to the live build, and their animation,
shape-key values, `baseAction` and render settings are identical to the base at
frames 27, 56, 338, 891 and 1200.

## Building any look

```bash
source presets.sh
female_look bun D8B77A 9E6B4A B3202A pearls mindfront_f_dress_09 6B2233
./build.sh female /path/OUT.blend

source presets.sh
male_look O4 chrono          # outfit look O1..O5, optional watch override
./build.sh male /path/OUT.blend

# still frames without saving
PCT=50 FR=27,338,891 TAG=look MOD=$PV1/$MODF blender -b scenes/BASE_V58.blend --python $PV1/bodystill.py -- OUTDIR
```

Requires Blender 5.2.x, MakeHuman assets at `$MH_ROOT` (default `/home/ubuntu/mh_assets`).
All colour arguments are 6-digit hex without `#`; any hex works, the presets are the curated set.

## Female options

| Option | Choices |
|---|---|
| Hairstyle + matching earring | `long` + slim gold hoop (tucked behind ear) · `bob` blunt bob + gold bar drop · `bangs` bob with bangs + pearl stud · `bun` sleek bun + statement hoops (both ears) · `braid` side-swept braid + gold teardrop |
| Hair colour (`HCOL`) | auburn (default, empty) · black `1C1714` · dark brown `3B2418` · blonde `D8B77A` · silver grey `B9B8B5` · any hex (darker ends + crown sheen derived automatically) |
| Skin tone (`STONE`) | fair `F7E1D3` · light (default, empty) · medium `E0B48F` · tan/olive `C99A6E` · brown `9E6B4A` · deep `6A4431` · any hex |
| Lipstick (`LIPC`) | soft rose (default, empty) · classic red `B3202A` · berry `8A2A4E` · coral `E0664F` · nude `B8826F` |
| Neckwear (`NECK`) | none · `fine` gold chain · `pendant` gold pendant chain · `pearls` pearl strand · `choker` velvet choker + charm · `scarf` silk neckerchief |
| Dress (`DRESS` / `DCOL`) | `mindfront_f_dress_11` tailored 3/4-sleeve sheath, navy `2B3A5C` · `mindfront_f_dress_09` long-sleeve maxi, burgundy `6B2233` · `mindfront_f_dress_07` sleeveless column midi, sage `7C8C6A` · `punkduck_black_cocktail_dress` knee-length sheath, emerald `1F5C4A` · `punkduck_middle_length_qipao` mandarin-collar midi, dusty rose `B87A7F` |
| Render mode | colour (default) · black-and-white line art (earrings keep their colour) |
| Face (`FACE`, arg 8) | `0` default · `1` defined: slimmer jaw, longer chin, wider eyes, lower flatter brows · `2` soft: rounder face, fuller cheeks, closer eyes, thicker higher brows |

Bun and braid pick up front-readable accents automatically (`hairpeek.py`, `HPK=0` disables): a top-knot peek above the crown for the bun, a tapered strand draped over the front shoulder for the braid. Both are procedurally tinted to `HCOL`.

Earring colours are fixed per hairstyle. Dresses carry derived light/shadow and sheen plus inked seams, darts, hems and fold lines.

## Male options

| Look | Hair | Hair colour | Skin | Outfit | Watch |
|---|---|---|---|---|---|
| `O1` | short afro `afro01` | black `1C1714` | deep `5C3A28` | navy polo · charcoal trousers · brown Oxfords | classic analog |
| `O2` | short crop `short01` | blonde `C9A366` | fair `E3B994` | white tucked T-shirt · straight-leg jeans · white sneakers | sport digital |
| `O3` | textured quiff `elvs_maxwell_hair` | brown `5A3A24` | tan `C99A6E` | light-blue untucked button-down · tan trousers · monk straps | dress watch |
| `O4` | braids `elvs_braided_rows` | black + burgundy dye `141212`/`8A1F3C` | brown `8D5A3F` | burgundy knit sweater · jeans · sneakers | smartwatch |
| `O5` | side-swept `elvs_grump_hair` | grey/silver `8F9096` | medium `B07F57` | cream fisherman sweater · charcoal wool trousers · Oxfords | chronograph |

- Hair colour set: black, blonde, brown, black with coloured dye (`HDYE`, any hex), grey/silver; any hairstyle takes any colour.
- Watches (`WATCH`): `analog`, `digital`, `smart`, `chrono`, `dress`, on the left wrist, bound to the forearm.
  When a long sleeve covers the default seat, the band slides onto the bare wrist past the
  cuff automatically (sleeve coverage is ray-cast along the arm; `WSEATM` sets how far past
  the cuff edge it rests). `WTILT` tilts the face toward the dial side, `WBACK`, `WFWD`,
  `WLAT`, `WCLR`, `WST`, `WSIDE` tune the fit as before.
- No suits, no neckwear.
- Relaxed arms: the male arm chain (clavicle → wrist) copies the female arm angles every frame
  (`malerelax_pre.py` + `malerelax.py`), because the Guest skeleton's rest angles differ. The shared action is untouched. Set `RLX=0` to disable.
- Faces (`FACE`, arg 3): `0` default · `1` defined: slimmer jaw, longer chin, wider eyes, lower flatter brows · `2` soft: rounder face, fuller cheeks, closer eyes, thicker higher brows. Same set as the female.
- `male_mix TOP[=hex] BOTTOM[=hex] SHOES[=hex] [HAIR] [HCOL] [SKIN] [WATCH] [FACE]` free-mixes any garments with per-piece recolor (see presets.sh for the piece list).
- Side-swept (`elvs_grump_hair`, O5) gets a traced hairline + part stroke so it stops reading as a cap.
- Voice: `audio/male56_am_michael.mp3` (Kokoro `am_michael`), phrase-fitted to the female timing in `audio/words56.json` by `scripts/male_voice_tts.py`.
  "one, plan it" (~1.8×), "Right here." (~1.6×) and "Not at all." (~1.5×) are sped up.

## Pipeline (scripts/)

- Female: `female.py` = `dressswap` → `modH` (hairswap, face line art, ear/earrings, strands) → `lip` → `neck` → `skintone` → `dressart` → `haircol`.
- Male: `modM.py` = `malerelax_pre` → `male2` (Guest body + skeleton into Host-named objects) → `malebrow` → `facealign` → `garm` (garment fit + layering) → `modH` → `lip` → `skintone` → `haircol` → `garmall`/`garmart` (garment shading + line art) → `facerestore` → `watch` → `malerelax`.
- `save.py` bakes a look into a .blend; `bodystill.py`/`headstill.py` render stills; `greyperf.py` renders the grey front+side performance review.

## Known limits

- Female: bun and braid read mostly from behind; the pearl stud is small at full-body distance; neckerchief reads a little flat.
- Male: analog watch dial is edge-on from some angles; chronograph subdials read as white spots; side-swept hair reads slightly like a cap.
- Faces are single-identity for V1 (more female faces planned for V1.1).
