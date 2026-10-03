# Cast V11 hair grooms

The approved hairstyle meshes previously used an emission grade, broad painted highlights and Freestyle strand marks. V11 adds real tapered native hair curves with Huang fibre scattering over those silhouettes. Both sexes retain their approved faces, body anatomy, complexion/makeup treatment, accessories, wardrobe and animation.

## Style coverage

| Character | Style | Construction |
| --- | --- | --- |
| Female | Long | Flow over the existing locks, finer ends, local ear tuck |
| Female | Bob | Recovered source UVs guide the straight fibres |
| Female | Fringe | Source UVs distinguish the fringe and side sections |
| Female | Bun | Scalp flow toward the bun and winding fibres around it |
| Female | Braid | Source UVs guide fibres through the woven bundles |
| Male | Afro | 42,000 coiled fibres, stable curl-clump carrier displacement, anatomical nape trim |
| Male | Crop | Short swept fibres over the approved crop |
| Male | Quiff | Lifted front fibres flowing over the crown |
| Male | Braided rows | Source UVs follow the woven bundles; burgundy dye stays at the ends |
| Male | Swept | Source UVs follow the swept sections |
| Male | Bald | Skin treatment retained; no groom is created |

The other styles contain approximately 17,000–26,000 fibres each. Fine fibres use 32–58 µm radii; a smaller set of thicker guide fibres supplies readable strand bundles within the illustrated style. All fibres taper. Sparse raised fibres and small deviations break the shell-like silhouette.

The original OBJ importer discarded corner UVs. The groom restores them by vertex IDs, including safe handling of caps appended by the importer. The built-in long mesh has no restored OBJ in this source package and uses a geometric guide field. The afro uses actual coil geometry rather than an embossed cap texture.

## Colour, lighting and attachment

All five female and five male colour presets, plus custom colours, reuse the same deterministic groom. Root/tip pigment and individual fibre variation retain the selected colour family. The burgundy dye uses a rest-space attribute tied to the hairstyle height, so it remains at the ends rather than recolouring every short segment across the scalp.

A hidden point mesh inherits the existing hair's head, neck and spine weights. A geometry-node modifier reads its posed positions into the native curves. There are no frame handlers, external simulations or new rig bones. Long hair retains the original weighted movement; this is not a new physical hair simulation.

The new fibres use calibrated studio lights. Compositor denoising is masked to hair object index 11; the anatomical skin's unfiltered texture and illustrated facial artwork remain intact. The production profile uses at least 128 samples with bounded bounce counts.

The former Freestyle strand/lock marks and painted `Host.hp_*` hair hints are hidden. Those hints caused floating bun/braid discs in oblique views. The outer hair contour is thinner. Only the hairline components of the face-frame drawing become transparent; lip and eye artwork retain their V10 treatment.

The long style also fixes two concrete fit defects: the original tuck affected 771 vertices well below the ear, and its clothing collision target still named an old hidden dress. The tuck now fades within 55 mm below the ear centre and the collision target follows the selected dress. Original body geometry is untouched. Small hair carriers receive subdivision level 2.

## Verification

- Ten actual 800 × 800 style renders use the identical current groom module. See `v11-render-verification.json` for counts, image hashes, cameras and build metadata.
- Actual review renders also cover all ten colour presets, bald, and speaking frames 71 and 106 for both characters. Before/after frames use matching cameras and resolution.
- Fresh female and male source assemblies pass through the production entry point with the V11 cache version and complete original rig/action.
- All eleven selections pass source-identity, colour and reapplication checks. Each haired style is checked over eleven speaking/head frames spanning 1–998, with 257 sampled points per frame. Native curve positions exactly follow the bound deformation mesh; rest coordinates and dye attributes remain stable.
- Attachment audits use 8% groom density for speed; the style renders use full production density. See `v11-hair.audit.json` for scope and individual results.
- Original body/face/wardrobe cages, shape keys, weights, non-hair UVs and rig bones are unchanged. Authorized hair changes are recovered UVs, the static long-hair tuck key, materials, visibility, modifiers and new groom objects.
- Focused configuration checks cover twelve complexion configurations, thirty skin/lip combinations and custom colours. The worker tests verify fixed server-side quality flags, stale V10 profile rejection and failure/lock handling.
- No full application build was run in this restored source-render workspace. This is a draft source upgrade, not a merged or deployed application change.

## Reproduce

```bash
python3 scripts/cast-quality-reference.py --character female \
  --output-dir /tmp/cast-v11-female --blender /path/to/blender --assemble-only
python3 scripts/cast-quality-reference.py --character male \
  --output-dir /tmp/cast-v11-male --blender /path/to/blender --assemble-only
```

Omit `--assemble-only` to render the production upper-thigh frame. `--no-hair` gives the preceding hair construction while keeping the skin/beauty upgrade. `render-hair-detail.py` creates fixed front or oblique head comparisons. `audit-hair-groom.py` checks a clean assembled selection.

The worker and customizer share `approved-v3-v6-hair-v11-upper-thigh`. Worker startup overrides cannot disable the versioned groom.
