# SceneBam Cast: six formal looks with independent suit and tie colors

Status: **integration branch, gated; not a live feature until installed and certified**.

## User-facing contract

Cast → New avatar / Edit avatar → Formal suits. Two female looks (double-breasted,
statement) and four male looks (jacket & tie, double-breasted, navy classic,
dinner jacket). Each look has a separate suit and tie palette, including custom
six-digit hex controls. These values persist as `outfit.kind`, `outfit.color`
and `outfit.tieColor` in the saved CastSpec and are passed to production as
`CAST_FORMAL_LOOK`, `CAST_SUIT_HEX` and `CAST_TIE_HEX`.

Existing casual clothes and characters are unchanged. In the Cast builder the
new formal selectors stay visibly disabled until genuine deployable Blender
assets are available. No fake outfit thumbnail, no quiet fallback to the
existing shirt, and no saved selection without a real rendered preview.

## Asset gate

Install six rigorously source-verified edited Blender scenes under
`SCENEBAM_FORMAL_ASSET_ROOT` (default:
`engine_sources/makehuman-lineart/out/scenebam-formal`):

- `female-double-breasted.blend`
- `female-statement.blend`
- `male-jacket-tie.blend`
- `male-double-breasted.blend`
- `male-navy-classic.blend`
- `male-dinner-jacket.blend`

Each blend **must** contain the corresponding single original rigged donor mesh
`SCENEBAM_FORMAL_FEMALE_DOUBLE_BREASTED`, etc., and a compatible
`Host.rig`. The garment's material slots must have EXPLICIT independent
`scenebamColorRole: "suit" | "tie"` custom properties. The importer refuses
assets missing either role, mismatching the 163-bone rig, or using a linked
shader input that would ignore the chosen color. A single flat color on the
entire suit is never accepted as independent tie coloring.

The file `manifest.json` must be generated **only after** verification:

```json
{
  "castSourceVersion": "bf88447b8f898bea078c44b9202cfe2b7ff13be5",
  "liveVmHashMatched": false,
  "validated": {
    "female:formal-double-breasted": {
      "sha256": "<64-character SHA256 of its .blend after role tagging>",
      "independentSuitAndTie": false,
      "rigAndMotion": false
    }
  }
}
```

The shown values **do not unlock** the UI. After hashing each real .blend and
passing both independent color checks and rig/motion validation, assign the
matching hashes, set those per-look booleans true, and independently verify
that the deployed live VM is serving this exact Cast source build before
setting `liveVmHashMatched` true. Unverified files are not made available.
The API checks file bytes against the manifest hash and rejects absent assets.

## Production rendering

`scripts/cast-render-assembled.py` assembles the existing production character
using its untouched rig, appearance controls, and original actions. It then
calls `scripts/cast-formal-wardrobe.py` for selected formal looks. That routine
links the actual garment from the certified source, checks the armature rest
matrices, rebinds the garment's armature modifier, keeps the existing host and
hides the superseded original default clothing/proxies. It recolors only
explicitly tagged suit and tie material slots. Failed compatibility or missing
roles **fails the render** rather than silently substituting older assets.

The same `cast-render-assembled.py` path powers preview assembly and
`scripts/presenter-job.py`'s actual video production. This means the saved
outfit choices flow from Cast to the production-scene assembly.

The live 3D WebGL stage does not yet have baked formal parts; while selecting a
formal look the Cast builder deliberately falls back to the actual queued
Blender preview for the exact chosen suit/tie palette. It never claims the
old GLB is wearing the formal suit.

## Still to certify before release

1. Get six production-assembled garment source scenes from the successful
   `work/scenebam-production-assembly-formals-20261013` Blender workflow, not
   the old V17 baseline package.
2. Hash-match the **live VM deployment** and the source build; make separate
   material groups/masks for both colors, using the production art files.
3. Perform controlled independent color A/B renders for **every** look, then
   test speaker gesture ranges, shoulder/neck, sleeve cuffs, clipping, seated
   framing, dialogue and motion continuity.
4. Populate the manifest with reproducible evidence and install all six
   `.blend` files onto the production render worker(s).
5. Run `npm run test:cast`, `npm run typecheck`, and representative actual
   preview/video jobs. Review the real renders and then merge/deploy.

No confirmation of VM parity, art acceptance, collision clearance, or
production deployment is asserted in this integration branch.
