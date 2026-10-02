# Cast skin and ear appearance pass

The v8 cache profile replaces stacked painted skin shading with one live surface treatment derived from the selected complexion. The original female v3 and male v6 remain the character authorities.

- Broad key and fill follow the camera portrait setup, with smooth normal falloff.
- Short local occlusion uses an 18 mm distance and 16% maximum contact weight. No fixed skin-colour overlay or screen-white highlight is retained.
- The anatomical lip mask and lip contour remain. Female lipstick retains the chosen palette; male natural lips follow the complexion, with a warmer relationship on fair skin. Cheek warmth is restrained and derived from the same complexion.
- Body, exposed lower-leg skin and drawn female ear share the selected linear-sRGB base. The default Light complexion is now passed explicitly as F1D7C8 instead of inheriting the baked reference value.
- The male's V60 fill, inner curve and outer outline are hidden. Its original rigged ear and original V10 contour remain; no character geometry is rescaled. Female earrings and ear construction remain.
- The actual renderer uses at least 32 samples. App and worker use `approved-v3-v6-skin-v8-upper-thigh`; the worker forces the profile independently of startup environment, and rejects client-injected flags.

## Evidence

The two assembled default characters rendered at 1080 x 1440 from the upper thigh upwards. A control with `--no-skin` keeps the preceding garment/hair finish for the before-and-after comparison. Six exact catalogue complexions were rendered on each character. Eight additional facial pose renders cover frames 300, 450, 600 and 750.

Both original approved scenes passed 59 body-pose samples each, from frames 1 through 987. Material reapplication remains stable across six tones. Source vertex/shape-key coordinates, rest bones and object/mesh/action counts remain unchanged. Those checks establish identity preservation and finite body geometry, not all-clothing animation acceptance.

The worker's two existing tests pass with the skin flag included in its fixed server profile. A direct execution of the real TypeScript config modules passed all 12 character/complexion combinations and app/worker version agreement. A full application build and live signed-in acceptance were not run in this pass.

Original recovered MakeHuman assets (99 files) match their recorded Git blob hashes. The original Blender scenes are unchanged. The source-recovery workflow was temporary and is removed from the final change.

## Reproduce

`python3 scripts/cast-quality-reference.py --character male --output-dir /path/to/review --blender /path/to/blender`

Add `--no-skin` to isolate the prior skin treatment while retaining the garment/hair finish. For the identity audit, open the original approved female v3 or male v6 scene with Blender and run `scripts/audit-skin-appearance.py -- female|male /path/to/audit.json`.

## Remaining work

This pass does not certify 9+ across all five commercial-readiness areas. Clothing construction, sleeves/shoulders, hairstyle and accessory combinations, hand contact, full-resolution continuous motion and deployed desktop/mobile acceptance remain separate work. These changes require merging and coordinated app/worker deployment before they appear live.
