# Cast skin texture, makeup, neck, and hand appearance — V9

The V8 complexion-derived skin pass preserved the chosen colours and removed
painted shadows, but lacked surface texture. V9 adds anatomically localized
surface detail to the same approved male and female characters. The default
female Soft rose preset now uses a different sheer makeup palette for each
predetermined complexion. Explicit lipstick presets and custom hex choices
remain overrides.

## Surface treatment

- Deterministic pores at approximately 0.43 mm spacing, with irregular grain,
  fine relief, and bounded pigment variation. Pore depressions are 0.095 mm;
  they affect the lighting normal and have a restrained pigment response.
- Coordinates are attached to the source mesh in rest space, measured in
  metres, and interpolate through the existing armature and subdivision.
  They do not use world position and therefore move with the character.
- A broad satin response is stronger around the forehead and nose, with
  separate nail and lip response. Lips have fine vertical striations rather
  than facial pores. Nail surfaces are excluded from pore relief.
- The selected skin hex remains the base colour on all exposed skin materials,
  including ears and lower legs. Custom skin colours use the nearest makeup
  palette while retaining their exact base colour.
- Local contact shading uses the current posed surface. Neck relief follows
  the sternocleidomastoid region, throat prominence, and suprasternal hollow,
  with restrained anterior flexion folds. The anterior mask is rig-bound.
- Hands have localized joint folds, two palmar flexion folds, knuckle warmth,
  palmar pigmentation, translucent nail beds, and small distal nail edges.
  These are surface changes; no cage vertices, UVs, weights, shape keys,
  bones, animation, or approved clothing geometry are changed.

## Female palettes

All values below are authored sRGB colours; they are converted to linear RGB
before blending. Cheek and eyelid layers are sheer, spatially localized masks.

| Skin | Base | Blush | Eye wash | Upper lip | Lower lip | Blush / eye coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Fair | F7E1D3 | D09A91 | A5867D | AA756D | BE8A80 | 13% / 10% |
| Light | F1D7C8 | C18C7B | 9C7C6D | A66F64 | B98072 | 14% / 11% |
| Medium | E0B48F | B97862 | 8A6755 | 985E50 | AF7462 | 15% / 12% |
| Tan | C99A6E | A8654E | 79543F | 874F40 | A36851 | 17% / 13% |
| Brown | 9E6B4A | A65E50 | 674436 | 75443D | 935C50 | 20% / 14% |
| Deep | 6A4431 | 985451 | 59372F | 573531 | 754B43 | 23% / 16% |

Coverage is the maximum mask weight, not a flat layer over the face. The
existing semantic lip boundary and upper/lower lip contour are preserved.
Male lips remain complexion-relative and receive no makeup.

## Rendering and integration

The portrait renderer uses emission-based directional shading to preserve the
approved illustrated character identity. Its automatic denoising previously
removed genuine fine skin detail because the material lacks a suitable
BSDF albedo guide. V9 retains sampled surface detail with denoising disabled
and a minimum of 64 samples. Fine pores remain intentionally subtle at the
normal upper-thigh preview scale and are best assessed in the close renders.
This is an anatomical skin treatment within the established illustrated art
style; it does not replace the approved characters with photographic assets.

Both the customizer and worker use
`approved-v3-v6-skin-v9-upper-thigh`, producing new cache keys. The worker fixes
all required quality flags at startup. The source version remains
`bf88447b8f898bea078c44b9202cfe2b7ff13be5`.

## Reproduce

```bash
python3 scripts/cast-quality-reference.py --character female --output-dir /tmp/cast-v9-female --blender /path/to/blender
python3 scripts/cast-quality-reference.py --character male --output-dir /tmp/cast-v9-male --blender /path/to/blender
```

`--no-skin` isolates the original authored skin treatment; the V8/V9 review
comparisons instead start from the saved V8 assembled reference scenes.
`scripts/render-skin-detail.py` accepts character, variant (`baseline` or
`texture`), view (`face`, `skin-close`, `neck`, `hand`, `palm`, `upper-thigh`),
output, optional skin hex, frame, and size. It fixes camera scale and rescales
line widths once from the source scene's actual output height.

## Validation

Blender 5.2.0 LTS is the source render runtime. The audit checks all six tones
for both characters, stable reapplication, unchanged source geometry, UVs,
weights, shape keys, and rig, and finite geometry over 59 animation frames per
character. It also checks that rest texture coordinates remain unchanged
through those poses and that an explicit female red lipstick override retains
its selected lower-lip colour. The render-config test exercises twelve distinct
complexion configurations, custom skin colours, natural default makeup, and
explicit lipstick colours. Worker tests verify required flags, cache version
agreement, invalid input rejection, failure reporting, and lock release.

In identical forehead crops, the standard deviation of fine image detail
(pixel values minus a 1.2 px Gaussian blur) increased from 0.135 to 0.932
for the female and from 0.126 to 0.902 for the male on an 8-bit scale. This
checks that exported surface detail survives; it is not a realism score.

Review images are actual Blender renders. No generated or substituted
character images are used. This branch is a draft source-rendering upgrade;
it has not been merged into the application or deployed.
