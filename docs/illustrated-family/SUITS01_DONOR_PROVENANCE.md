# Real MakeHuman suit donor — provenance and fit-trial contract

- **Upstream:** https://static.makehumancommunity.org/assets/assetpacks/suits01.html
- **Exact archive:** https://files2.makehumancommunity.org/asset_packs/suits01/suits01_cc0.zip
- **Archive SHA-256 (download verified on GitHub Actions):** `2b1d8676f3863b188e9eea98c1d8f234543d54c440e791d92b819f8ee1861f19`
- **Compressed archive:** approximately 40 MB, containing 67 entries.
- **Attribution:** Margaret Toigo / MRT.
- **Asset license:** each of the eight `.mhclo` files explicitly declares `# license CC0`. Keep that direct header proof instead of assuming license from a directory name.

## Eight actual downloadable garment candidates

| Package asset directory | Intended style |
|---|---|
| `toigo_female_double-breasted_suit` | Female double-breasted business suit |
| `toigo_female_suit` | Female formal suit |
| `toigo_female_suit_2` | Alternate female suit |
| `toigo_male_double-breasted_suit` | Male double-breasted suit |
| `toigo_male_suit_3` | Male suit variant |
| `toigo_male_suit_tie_and_jacket` | Male formal jacket with tie |
| `toigo_suit_with_dinner_jacket` | Dinner jacket suit |
| `toigo_suit_with_jacket_and_bowtie` | Jacket with bowtie |

## Implementation boundary

**Do not** copy an arbitrary rendered image to the rig. Import the real `.mhclo` with the existing V1 fitting code `engine_sources/makehuman-lineart/scripts/mhclo_fit.py`, use the matching upstream OBJ topology, transfer weights from the canonical Host.body and bind the new garment to `Host.rig`. The canonical Blender files are Zstandard-packed and must be decoded to disposable .blend copies first. The existing face and original performance actions must remain unchanged.

First material/geometry smoke trials:

- `female` → `toigo_female_double-breasted_suit`
- `male` → `toigo_male_suit_tie_and_jacket`

Save and inspect actual front, three-quarter, 338 and 891 frames. If the garments clip through the body or source clothing and the result cannot be fixed with bounded fit adjustments, report the failure; no production integration without valid previews.

**Status:** source archive, hash, internal CC0 headers verified. Actual character fit and action compatibility are experimental until the corresponding Blender Actions run passes visual QA.
