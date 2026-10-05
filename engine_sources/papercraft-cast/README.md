# papercraft-cast

Faceted "folded paper" character bust renderer. Turns a stylized 3D
character into a low-poly papercraft plate: designed facets, matte kraft
paper surface with fiber bump, crease darkening, seamless studio backdrop.

Produced in the "papercraft characters like the reference images" session —
verdict: passes the "really close" bar on the user's reference set.

## The recipe

1. **Chassis must be stylized-authored geometry.** The look lives in the
   mesh: caricature proportions + authored fold planes. Decimating a
   realistic body never reaches it (verified across ~15 attempts).
   Working chassis today:
   - `assets/rain/rain_v3.2.blend` — Blender Studio "Rain" rig (CC-BY,
     attribution required). Rendered head+chest; rig scripts are disabled
     on this branch so bones cannot be reposed headless — crop, don't pose.
   - `assets/quaternius/*.glb` — Quaternius characters (CC0). Painted
     features via separate materials; options vary per pack.
2. `scripts/rain_paper.py <out.png> [decimate_ratio]` — Rain pipeline:
   hides GP/nomask/cornea helpers, strips Subsurf, Decimate COLLAPSE ~0.22
   + Triangulate, flat shade, `paperize()` every material (keeps authored
   textures, kraft multiply, Pointiness crease ramp, kraft normal map,
   warm skin multiply), studio 3-area-light + gradient wall, bust framing.
3. `scripts/render_q2.py <glb> <out.png>` — glTF pipeline: material-split
   pieces (paper-piece illusion via micro-rotations), palette tints
   (Skin→kraft, Hair→navy, clothes→khaki), same lighting.
4. `scripts/assemble_paper.py` — MakeHuman fallback: proxy bodies
   (female1605/male1591) + garment/hair/skin options from `origin/mh-assets`.
   Reads: realistic proportions; keep for coverage, not hero shots.

## Assets & licenses

| Path | Source | License |
| --- | --- | --- |
| `assets/rain/` | Blender Studio Rain v3.2 char pack (textures included, `TEX-rain_eyes.png` repainted: blue iris → dark almond) | CC-BY 4.0 — attribute "Rain – Blender Studio" |
| `assets/quaternius/` | Poly Pizza mirrors of Quaternius models | CC0 / Public Domain |
| `assets/kraft/` | ambientCG Paper001 1K maps | CC0 |

## Known gaps (vs the reference plates)

- Eyes render as lit spheres (repainted dark almond); true flat painted
  almonds would need eye-region flattening on the head mesh.
- Arms are T-posed; cloudrig scripts are disabled so bones can't pose
  headless — the crop is the workaround. Enable scripts to pose properly.
- Layered folded-sheet construction is only approximated (material-split
  + micro-rotation on the glTF path).

## Running headless

```bash
blender -b --python scripts/rain_paper.py -- out.png 0.22
blender -b --python scripts/render_q2.py -- assets/quaternius/q_casual.glb out.png
```

Cycles, 48–64 samples, ~30–90s/frame on CPU. EEVEE works for previews
(`'BLENDER_EEVEE'` on Blender 5.2.1 — not `BLENDER_EEVEE_NEXT`).

## Wiring into cast

Intended as a third look family next to line-art + presenters: same
spec → blender render queue, `style: papercraft`, chassis option
(`rain` | `quaternius:<file>` | `mh:<proxy>`), palette tints per material
name. `scripts/*.py` are already option-driven; a `cast.facet` manifest
entry can mirror paper-cast-v1's facet taxonomy (roles, ageBands,
formality) onto chassis+palette choices.

## Wiring into cast (third look family)

- `manifests/papercraft-facets.json` — the manifest: chassis table (id → source
  asset, renderer script, presentation, license, decimate default), named
  skinTones / wardrobePalettes / hairPalette, rolesToChassis map, framing
  (currently `bust` only) and renderProfile. Mirrors paper-cast-v1's
  `cast-facets.json` style.
- `manifests/cast.papercraft.schema.json` — the queue spec schema. A plate
  request = `{style: "papercraft", chassis: {id}, look: {skinTone,
  wardrobePalette, hairColor, paletteOverrides}, framing, output}`.
- `manifests/cast.papercraft.example.json` — a working example spec.
- `scripts/papercraft_cast.py` — the driver: resolves the spec's chassis via
  the manifest, then shells out to the matching renderer:

      python3 scripts/papercraft_cast.py <spec.json> [--dry-run]

  `look.paletteOverrides` (material-fragment → [r,g,b] tint) is passed to
  render_q2.py through $PAPER_PALETTE; rain_paper.py keeps its texture-driven
  skin/hair tones (the palette knobs are currently no-ops on the rain chassis —
  listed as a known gap).

The MH fallback (`assemble_paper.py`) reads option args directly:
`out.png HAIR SKIN BODY GARMENT GTEX HCOL HTEX HTINT` — the spec format does
not yet cover per-asset selection for that chassis.
