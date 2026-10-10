# NexStudio Illustrated V1 — Visual Hair Trial Decisions

**All trials use original V1 163-bone Host rigs with 34 body shape keys, and are NOT approved production presets.** Working branch: `work/illustrated-family-expansion-v1`.

## 2026-10-09 initial visual QA on real Blender renders

| Trial | Original source and permission | Rig/pose proof | Three-quarter visual result | Decision |
|---|---|---|---|---|
| Female `toigo_blunt_bob_with_bangs` | MRT, individual `.mhclo` header CC0 | Actual Blender front, 3/4, original poses 338/891; 2,665 fitted hair vertices | Head framing works, but overly uniform helmet-like hair surface and sparse illustration strands | **CANDIDATE / NOT SHIPPABLE WITHOUT ART PASS** |
| Male `cortu_short_messy_hair` | Cortu Johnstone, explicitly CC0 in `.mhclo` comments | Actual Blender front, 3/4, original poses 338/891; 832 fitted hair vertices | Long faceted fringe covers both eyes and part of nose; facial readability fails | **REJECT** |

[Female close-up front](hair-trial-previews/female-hair-front-head-front.png) · [Female close-up three-quarter](hair-trial-previews/female-hair-front-head-threeq.png) · [Male failed front](hair-trial-previews/male-hair-front-head-front.png) · [Male failed three-quarter](hair-trial-previews/male-hair-front-head-threeq.png).

The male test must never be auto-installed as a new user-facing option simply because its original rig connection and rendering passed. Seek a **genuinely shorter CC0 haircut**, not a superficial name-based substitution.

## Hair release rules

1. Keep original `Host.hair_culturalibre_hair_01` (female) and `Host.hair_elvs_maxwell_hair` (male) selectable, and original character assets unchanged.
2. Only use donors whose **individual** source-file license allows reuse; nominal archive `hair01_cc0.zip` also contains AGPL-3 individual assets. See [per-source hair provenance](Hair01_PROVENANCE_AND_RELEASE_GATES.md).
3. Approve only after **front, three-quarter, close-up, original gesture** preview visual inspection, including visible eyebrows, eyes, jawline and hairline, without off-body/camera-facing flat overlays.
4. Test hair/head attachment in motion and confirm no facial expression/blink/viseme occlusion before integrating user-facing presets.
5. Mark any unapproved scripted style or failed 3D hair trial as experimental. Do not claim a new identity merely from a wardrobe or haircut variation.

## Next experiment

A Blender-only surface measured ink-strand trial for the female bob is in `experiments/illustrated-family/bob_surface_strands_trial.py`, tested by `.github/workflows/illustrated-bob-authored-strands.yml`. It may be rejected if the actual rendering looks worse.

## 2026-10-10 verified real Blender follow-up

These are all separately rendered by Blender, not generated concept art. They use the immutable original rigs and the validated licensed donor meshes.

| Donor | Real preview | Actual visual finding | Release status |
|---|---|---|---|
| `toigo_inverted_bob` (female) | [Three-quarter](hair-next-candidates/toigo_inverted_bob/female-hair-front-head-threeq.png) · [Presenter gesture](hair-next-candidates/toigo_inverted_bob/female-hair-pose-891.png) | Best new silhouette: visible eyes and brows, asymmetrical shape, clear haircut identity. Lower neck lock has an overly sharp extension; inspect shoulder/head rotations | **PROMISING, NOT APPROVED** |
| `faydaen_hair_1` (male) | [Three-quarter](hair-next-candidates/faydaen_hair_1/male-hair-front-head-threeq.png) · [Presenter gesture](hair-next-candidates/faydaen_hair_1/male-hair-pose-891.png) | Eyes visible. Raised rear hair and side locks read as an expressive/character-specific long hairstyle, not a clean short professional cut | **OPTIONAL STYLE CANDIDATE, NOT APPROVED** |
| `cortu_strawberry_cloud_hair` (male) | [Three-quarter](hair-next-candidates/cortu_strawberry_cloud_hair/male-hair-front-head-threeq.png) | Oversized neck/shoulder mass, uneven hard edges, reduced illustrated elegance | **REJECT** |
| `toigo_blunt_bob_with_bangs` 3D curved strand second pass (female) | [Three-quarter](hair-curved-v2-previews/female-hair-front-head-threeq.png) · [Front](hair-curved-v2-previews/female-hair-front-head-front.png) | More natural and subtler strokes than the earlier straight-line pass, but surface still feels smooth and somewhat helmet-like | **CONTINUE ART DIRECTION; NOT APPROVED** |

No approved presets are altered. Do not silently promote the rejected cloud or short messy male hairstyle as selectable alternatives.

