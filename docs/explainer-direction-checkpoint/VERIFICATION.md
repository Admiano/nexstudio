# Checkpoint verification

Verification date: 12 October 2026.

These checks verify the saved infrastructure and records. They **do not change**
the failed visual verdict, grant creative approval or establish production readiness.

## Executed checks

| Check | Result | Boundary |
|---|---|---|
| Python engine suite | 388 passed; 1,292 subtests passed; 2 authority warnings; 35.06 seconds | Includes explicitly labelled fixture/mechanical tests, not fresh live authoring. |
| Node runtime suite | 14 passed; 0 failed; about 44.05 seconds | Real headless captures/encoding of technical fixtures, not reference-level film acceptance. |
| Ruff | Selected correctness rules `E9,F63,F7,F82` passed | Not a claim of full formatting/style compliance. |
| Mypy | No issues found in 9 source files | Gradual checking with missing imports ignored; not strict proof of all untyped function bodies. |
| Saved proof integrity | All 17 selected original file hashes match; voice/three movie hashes match the original manifest | Integrity, not creative quality. |
| Frozen contracts/media | Score and three native plans validate; ffprobe confirms native canvases, 491 frames and AAC audio | Temporal visual failures remain. |
| Documentation links | All current local Markdown file links resolve | Links/whitespace checked on the final staged checkpoint. |
| Original proof | Three existing native films, real measured voice and failed visual audit preserved | No new model run or replacement film produced for this documentation task. |

There is no repository pre-commit configuration or active default pre-commit hook
in the inspected checkout. No application UI-driven testing was requested or run.
Existing public dispatch and locked engines were not modified.

Before publishing, the staged checkpoint is also checked for local Markdown link
resolution, whitespace errors, excluded caches/weights/dependencies, and obvious
embedded credential patterns. These are targeted checks, not a comprehensive
security audit.

## Commands

Executed from the repository root on the existing VM:

```sh
PYTHONDONTWRITEBYTECODE=1 \
/home/ubuntu/.pyenv/versions/3.12.13/bin/python \
  -m pytest -q -p no:cacheprovider \
  engine_sources/explainer-direction/tests

/home/ubuntu/.nvm/versions/node/v24.19.0/bin/node \
  --test engine_sources/explainer-direction/tests/test_runtime.cjs

/home/ubuntu/.pyenv/versions/3.12.13/bin/python \
  -m ruff check \
  engine_sources/explainer-direction/explainer_direction \
  engine_sources/explainer-direction/tools \
  engine_sources/explainer-direction/tests \
  services/studio-family-engines/explainer_direction_adapter.py \
  --select E9,F63,F7,F82

/home/ubuntu/.pyenv/versions/3.12.13/bin/python \
  -m mypy engine_sources/explainer-direction/explainer_direction \
  --ignore-missing-imports
```

Runtime-test artifacts were created outside Git in a separate labelled fixture
directory. The archive in this checkpoint is the previous actual lightning film,
not those runtime-test fixtures.

## Authority warnings

The two Python warnings explicitly state that development authoring lacks
authenticated P8 semantic authority, independent native-media review, human
calibration, Creative Lock and public/commercial approval. They are expected
boundary disclosures, not approvals.

## Current quality limitation

The archived film still has an empty opening, collapse-prone focus shifts,
detached labels, weak process representation, a misleading sound-wave label and
no developed sound-design layer. Preserving it as a checkpoint does not repair it.
