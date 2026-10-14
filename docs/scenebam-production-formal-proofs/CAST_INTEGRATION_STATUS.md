# SceneBam Cast: genuine six-outfit formalwear integration (isolated branch)

This work integrates existing fitted CC0 MakeHuman garment geometry, not flat generated images. Preserve the approved male and female SceneBam character rigs, visemes, face and animation library. Original outfits remain selectable.

## Studio integration

- The Cast builder offers two formal suits for the woman and four for the man, with independent suit palette/custom hex and tie palette/custom hex for outfits containing a tie.
- The CastSpec stores `outfit.kind`, `outfit.color` and, when applicable, `outfit.tieColor`. The API schema accepts those keys, and normalization persists them.
- `castRenderConfig` conveys the exact variant and suit/tie hex through a versioned, validated three-key Blender worker environment; preview keys separate distinct suit/tie selections.
- The presenter engine POST route already constructs its request from `castRenderConfig(normalizeCastSpec(member.spec))` and calls `scripts/presenter-job.py`, which consumes the same `cast-preview-render.sh` and `cast-render-assembled.py` pipeline. This provides the integration route for actual video frames; no 2D-only substitution is allowed.
- The fast WebGL live3d manifest does **not yet** contain formal meshes; formal selections deliberately fall back to the actual asynchronous Blender render. Missing proof source files fail, never display unrelated old clothing as if approved.

## Mandatory six source files

Obtain the genuine six-workflow source artifact from [GitHub Actions run 38480065233](https://github.com/Admiano/nexstudio/actions/runs/38480065233); artifact `SCENEBAM_SIX_FORMALS_PRODUCTION_ASSEMBLY_PROOFS`. Do **not** substitute the older V17 standalone files.

```bash
gh run download 38480065233 --repo Admiano/nexstudio \\
 --name SCENEBAM_SIX_FORMALS_PRODUCTION_ASSEMBLY_PROOFS \\
 --dir /tmp/scenebam-formal-proof
python3 scripts/install-scenebam-formal-bank.py \\
 /tmp/scenebam-formal-proof /srv/scenebam/cast-formals-v1
# Set for the Blender preview AND presenter-video production workers:
export CAST_FORMAL_SCENE_DIR=/srv/scenebam/cast-formals-v1
```

The installer independently checks all six authentic Blender scene headers, 163-bone source rig metadata, rest-pose QA, and creates a SHA256 manifest in an atomic new versioned folder. An existing destination is not overwritten.

## Validation gates

1. `npx tsc --noEmit` must pass.
2. `scripts/cast-formal-integration-proof.py` must load each true Blender garment on current assembly, verify rest matrices, recolor the suit and actual tie mesh, and render visually correct frames. Inspect six rendered PNGs; no structural-only approval.
3. Suit and tie must be independently recolorable while shirt, skin, eyes and hair remain unchanged. Verify arm gestures and neckline clearance before shipping.
4. VM hash of the deployed cast binary and render-worker code must be independently compared with target source. **Not yet certified**.
5. Visual approval, collision review, and a live end-to-end presenter video are required before merging/deploying.

**Current status:** isolated integration branch under validation. Do not claim already shipped on live VM.
