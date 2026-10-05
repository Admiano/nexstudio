# papercraft-cast

Faceted "folded paper" character renderer. Turns a stylized 3D
character into a low-poly papercraft plate: designed facets, matte kraft
paper surface with fiber bump, crease darkening, seamless studio backdrop.
Busts and full-body plates.

Produced in the "papercraft characters like the reference images" session —
verdict: passes the "really close" bar on the user's reference set.

## Generated chassis (full-body, highest fidelity)

`assets/gen/casual30_shape.glb` — man ~30s, tee + trousers, real
folded-sheet geometry. Produced by **Hunyuan3D-2.1** (`tencent/Hunyuan3D-2.1`
HF Space, free ZeroGPU tier — no local GPU needed): feed an authored
concept image (`assets/gen/concept_fullbody.png`) to `/shape_generation`,
get a GLB back in ~30s.

Pipeline: concept image (generate or author) → Hunyuan `/shape_generation`
→ `scripts/render_gen_fullbody.py IN.glb CONCEPT.png OUT.png DECIMATE`.

The render script:
- normalizes to ~1.75m, flat shades, strips Hunyuan's rembg artifacts
  (floor slab faces: `|nz|>0.9` in the slab z-band, plus rim-band faces)
- separates head faces (world z > 1.44) into their own object and decimates
  it harder (0.04) than the body (0.03) — big planar brow/cheek facets
- creates `projUV` + UVProject modifier — an ortho projector camera facing
  the figure re-projects the concept image onto the mesh (the GLB has no
  UVs, so the concept supplies the palette for free)
- **per-facet flat color bake** — after applying the decimate+UVProject
  modifiers, each face's projected texels are area-averaged (centroid +
  loop UVs + edge midpoints) into a `paperCol` corner color attribute.
  Every facet renders as ONE flat paper tone — the folded-paper-piece
  construction of the reference plates. Note: attribute values are read
  as linear in the shader, so sRGB texels are stored as `v**2.2`.
  Faces whose samples are >50% dark deepen toward dark-brown — subtle
  implied eye-zone shading on the planar mask face (appliqué pieces and
  concept-painted features both failed; eyes stay authored, not pasted)
- paperize(): baked `paperCol` (or concept texture fallback) × kraft
  multiply 0.45, HueSat 1.28, RGBCurve S-curve, Pointiness crease ramp,
  AO 0.028, rear-third multiply-darken (the mesh's back rim shows as pale
  behind the silhouette otherwise), kraft normal map 0.65
- 3-area-light studio + seamless gradient wall, Cycles 96spp, exposure
  -0.45, AgX Medium High Contrast

**Modularity / color swaps**: the mesh carries no color of its own — the
concept image IS the palette. Recolor garment regions in the concept
(PIL mask on the tee/trouser hues) and re-render; no mesh regeneration
needed. `look.conceptImage` in the spec overrides the concept per request.
`assets/gen/concept_fullbody_navy.png` is a worked example (navy tee,
brown trousers).

Hunyuan3D-2 is under the Tencent Community License — check attribution
terms for generated outputs before shipping renders externally.

## The recipe

1. **Chassis must be stylized-authored geometry.** The look lives in the
   mesh: caricature proportions + authored fold planes. Decimating a
   realistic body never reaches it (verified across ~15 attempts).
   Working chassis today:
   - `assets/gen/casual30_shape.glb` — Hunyuan3D-generated folded-sheet
     geometry (see "Generated chassis" above); full-body, highest fidelity
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
| `assets/gen/` | Hunyuan3D-2.1 generated mesh + authored concept images | Tencent Community License — verify terms |
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
blender -b --python scripts/render_gen_fullbody.py -- \
    assets/gen/casual30_shape.glb assets/gen/concept_fullbody.png out.png 0.03
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

## Sheet pass (v2 render recipe)

`rain_paper.py` now builds the folded-sheet look procedurally:

- per-part decimate — head/body 0.45 (smoother skin like the refs), eyes 0.7,
  garment/hair/scarf pieces at the spec's ratio (default 0.15)
- per-piece `SOLIDIFY` (0.0025, offset -0.6) — real paper edge thickness on
  every garment/hair/scarf object; works on Rain's .blend meshes (the earlier
  shrapnel failure was glTF-specific)
- `ShaderNodeAmbientOcclusion` (distance 0.012) multiplied into base color —
  deep crease shadows in fold valleys and layer contact; eye/cornea/gums
  materials are exempt
- eyes: `GEO-rain-eyes` slots replaced by a pure Emission material
  (0.035, 0.028, 0.024 @ 0.55) — flat dark-almond with no specular, matching
  the references' painted eyes
