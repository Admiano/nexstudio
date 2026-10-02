# Female cosmetics, lipstick and earring refinement — V10

V9 closeups retained a thick black outer lip ribbon, nearly invisible makeup,
flat lipstick, and a gold hoop set behind the visible ear. V10 removes the lip
ribbon from rendering, increases complexion-specific makeup coverage, refines
the lip finish and attaches a slimmer gold hoop to the drawn lobe. It also
strengthens the anatomical skin texture on the existing female and male meshes.

## Female appearance

The 171 mouth-ribbon polygons in `Host.V59_face_frame` receive a transparent
material. Their geometry, shape keys, drivers and weights are retained. Eye
art, eyebrows, nose detail, hairline and the original face cage are preserved.
The existing semantic lip boundary supplies a narrow feathered cosmetic edge.

Upper and lower lips use separate complexion-specific pigments. Fine,
irregular vertical relief is 0.022 mm high, with restrained pigment variation.
The lower lip has a stronger satin response than the upper lip. Soft rose uses
the palette below; Classic red, Berry, Coral, Nude and custom hex choices
retain their explicit selected colour as the underlying lower-lip pigment.

The vertex-parented painted mouth interior previously covered the original
teeth during speech. It is hidden. The original rigged teeth are visible with
soft ivory directional shading and posed oral contact shadows. No replacement
mouth or facial geometry is introduced.

| Complexion | Skin | Blush | Eye wash | Upper lip | Lower lip | Maximum blush / eye coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Fair | F7E1D3 | D78E91 | A9827A | B6757F | CF9196 | 33% / 34% |
| Light | F1D7C8 | C9797E | 987261 | B76C76 | C78086 | 35% / 36% |
| Medium | E0B48F | B76D61 | 966B55 | AC6461 | C47F72 | 37% / 38% |
| Tan | C99A6E | A65F49 | 8D5E44 | 9A5450 | B97065 | 40% / 40% |
| Brown | 9E6B4A | A65F5B | 865A4D | 82434C | AD6972 | 45% / 42% |
| Deep | 6A4431 | AE626A | 8B5A59 | 70404F | 9E6574 | 48% / 44% |

These are feathered anatomical masks, not uniform foundation coverage. A
subtle cheek illumination layer supplements the warm lid and cheek pigments.
Custom skin colours retain their exact base and use the closest palette.

## Earrings and skin

The hoop remains parented to the original head bone. Its attachment is derived
from the visible lobe in hoop-local coordinates, placing it on the ear's front
surface instead of approximately 16 mm behind it. The previous enlarged black
rim is hidden. The gold wire is 0.85 mm thick; its outside dimensions are
15.7 × 19.7 mm. Curved analytical studio reflections replace the flat yellow
emission colour while preserving the approved portrait lighting. Reapplying
the upgrade does not shrink or move the ring again.

Face and body skin retain deterministic rest-space pores at approximately
0.43 mm spacing. Pore relief increases to 0.12 mm, with 0.065 mm irregular
microrelief and two scales of bounded pigment variation. Pores remain excluded
from lips and nails. The existing anatomical neck, knuckle, palm and nail
masks are retained for both sexes. The source body's 19,158 vertices, UVs,
weights, shape keys and rig are unchanged; only the authorized hoop mesh
coordinates change.

The renderer remains in the established illustrated Cast style. The gold uses
analytical reflections rather than a photographic environment/PBR workflow.
Fine skin and lip details need close rendering to assess. Review images are
actual Blender renders of the approved assets; no generated character images
are used.

## Integration and verification

The customizer, worker and reference requests now use
`approved-v3-v6-beauty-v10-upper-thigh`, invalidating preceding appearance cache
keys. The source version remains `bf88447b8f898bea078c44b9202cfe2b7ff13be5`.
The new `cast-female-beauty.py` module is invoked by the existing skin pass.

- Source assembly through `cast-quality-reference.py --assemble-only` verifies
  the production entry point, new cache version, original body vertex count,
  transparent mouth artwork and head-parented hoop.
- Blender audits verify all six complexions per sex, stable reapplication,
  exact base colours, unchanged original cage/key/weight/UV/rig data excluding
  authorized hoop geometry, and finite posed body geometry across 59 frames
  per sex. Rest texture coordinates remain stable through animation.
- Female audits additionally check all 171 transparent lip polygons, preserved
  non-lip ink, hidden hoop rim, head-bone parenting, stable hoop vertices and an
  explicit red lipstick override.
- Render-config checks cover twelve distinct complexion configurations,
  all thirty female skin/lip preset combinations and custom colours. Two
  worker tests cover rendering flags, version agreement and failure handling.
- Final visual checks cover six female complexions, four explicit lipstick
  choices, relaxed/open/puckered mouth poses and a male texture closeup. Each
  render records the skin source SHA-256 so mixed intermediate iterations are
  excluded from final review boards.

The full application build is not run in this restored source-render workspace.
This is a draft source-rendering upgrade, not a deployed application change.

## Reproduce

```bash
python3 scripts/cast-quality-reference.py --character female --output-dir /tmp/cast-v10-female --blender /path/to/blender
python3 scripts/cast-quality-reference.py --character male --output-dir /tmp/cast-v10-male --blender /path/to/blender
```

For detailed views, open an assembled scene and run `render-skin-detail.py`
with character, `texture`, view, output, skin hex, frame and output size.
Supported views include `skin-close`, `lips`, `neck`, `hand`, `palm`, `face` and
`upper-thigh`. For an explicit lip selection, set `CAST_LIP_HEX`. Compare with
V9 using its saved assembled scene and the `baseline` variant at the same
camera, frame and size.
