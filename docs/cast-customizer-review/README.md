# Cast customizer follow-up

Implemented on the PR #58 branch, 2026-10-02. This supersedes the experiments in `docs/cast-customizer-pending`.

## Result

- Preserve original female v3 and male v6 source Blender scenes; all eleven source .blend files remain byte-identical.
- Retain trouser waistband topology and deformation weights. Bounded garment coverage masks remove covered body intersections while protecting hands/head and boundary rings.
- Fit evaluated trouser surfaces and their ink stitching beneath untucked tops using depth-only adjustments. Extend the tucked tee's lower hem to meet the posed waistband. These are per-frame preview-render fits; they do not add a video animation handler.
- Render main previews at 1080×1440 with upper-thigh framing and a fresh cache version `approved-v3-v6-fit-v6-upper-thigh`.
- Include 50 image selectors made from actual source renders/contact sheets, with labels and selected states; keep colours as rounded swatches and custom HEX inputs.
- Include the exact ten stylized backgrounds from `devin/1790707046-presenters-v1`, each with its independently composed landscape, square and portrait plate. Persist environment/format independently of the character render cache.

## Verification

- Inspected all 25 male top/trouser combinations at frame 27 after final fitting, plus frames 338 and 891 for all five default ensembles. Frame 1 assembly metadata also checks finite fitted geometry.
- Visually inspected 50 thumbnail crops and the environment plates. `public/cast/options/SOURCES.json` records provenance, source hashes and crops.
- `npm run test:cast`, `npm run typecheck`, production build, Python compilation and `git diff --check` passed. Production build retains its existing dynamic worker tracing warning.
- All 99 pinned MakeHuman assets match their installation provenance.

## Remaining acceptance work

Actual signed-in desktop/mobile UI, save/reopen/reload and deployment acceptance are not verified. The accessible deployed preview still serves the older branch. Local browser/database setup was unavailable, so render contact sheets are evidence of the renderer and assets, not app screenshots. Do not label this deployed or fully accepted until those checks pass.
