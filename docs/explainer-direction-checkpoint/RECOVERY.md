# Checkpoint recovery and replay

This checkpoint preserves the **failed development result**, not an accepted film.
Start with the [scope and roadmap](README.md) and [original visual audit](evidence/visual-audit.md).

## 1. Recover the code and records

Check out the checkpoint commit/branch in the NexStudio repository. Commands below
assume the shell's working directory is the repository root.

The engine lives in `engine_sources/explainer-direction`; the internal adapter is
`services/studio-family-engines/explainer_direction_adapter.py`. It is not registered
for public dispatch.

The archive contains 17 original evidence files plus `inventory.json`. The original
production manifest refers to the original VM's absolute paths and all 1,526
artifacts. Most original frames and intermediate normalized audio are deliberately
not committed. Use the selected-file inventory to validate this Git archive.

## 2. Verify evidence integrity

Run from the repository root:

```sh
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path("docs/explainer-direction-checkpoint/evidence")
inventory = json.loads((root / "inventory.json").read_text())
for item in inventory["files"]:
    path = root / item["path"]
    data = path.read_bytes()
    assert len(data) == item["bytes"], path
    assert hashlib.sha256(data).hexdigest() == item["sha256"], path

manifest = json.loads((root / "manifest.json").read_text())
voice_hash = hashlib.sha256((root / "voice.wav").read_bytes()).hexdigest()
assert voice_hash == manifest["voice"]["audio_sha256"]
assert voice_hash == json.loads((root / "voice-meta.json").read_text())["audio_sha256"]
names = {"16:9": "landscape", "9:16": "portrait", "1:1": "square"}
for render in manifest["renders"]:
    path = root / f"lightning-thunder-{names[render['aspect']]}.mp4"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == render["movie_sha256"]
print("All 17 archived evidence files verified; original voice/movie hashes match.")
PY
```

This checks identity, not visual correctness, source truth or production authority.

## 3. Validate the frozen score and native plans

No model or TTS inference is required:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$PWD/engine_sources/explainer-direction" \
python3 - <<'PY'
import json
from pathlib import Path
from explainer_direction.contracts import validate_score, validate_plan

root = Path("docs/explainer-direction-checkpoint/evidence")
score = validate_score(json.loads((root / "score.json").read_text()))
assert score["provenance"]["status"] == "DEVELOPMENT_PREFLIGHT"
for name in ("plan-16x9.json", "plan-9x16.json", "plan-1x1.json"):
    plan = validate_plan(json.loads((root / name).read_text()))
    print(name, plan["aspect"], plan["canvas"], plan["duration_ms"])
print("Contracts valid. The archived visual verdict remains FAILED.")
PY
```

The code's tested environment uses Python 3.12.13, Node 24.19.0, Chrome and ffmpeg.
The contract-only validator also uses system Python in the renderer.

## 4. Inspect the saved films

Open/download the three MP4 files linked in the main document. They are the exact
audited films, with native audio. The PNG contact sheet is supplementary; it does
not replace watching the temporal result.

The supplied WAV is real measured Kokoro Liam narration, not synthetic fixture
audio. Its model/voice provenance is recorded in `voice-meta.json` and the ledger.
The four source sentences are a narrowly disclosed quotation mode.

## 5. Rerender one exact native plan

This is a **render replay**, not fresh authoring and not a new creative proof.
It uses the saved plan and exact measured narration. No local LLM, Kokoro weights
or NLI weights are needed for this operation.

Prerequisites:

- A Node executable, system Python 3, Chrome/Chromium, `ffmpeg` and `ffprobe`.
- The declared Inter font at its repository asset path.
- The existing sibling renderer dependency
  `engine_sources/explainer-locks/node_modules/playwright-core`.

If that dependency is absent, inspect the sibling `package.json` and install its
declared dependencies with `npm install` in that directory. This checkpoint does
not change the sibling package or its renderer.

Run from the repository root, with a fresh output under your existing home directory:

```sh
REPO="$PWD"
OUT="$HOME/explainer-checkpoint-replay-$(date +%s)"
node "$REPO/engine_sources/explainer-direction/tools/render.cjs" \
  --plan "$REPO/docs/explainer-direction-checkpoint/evidence/plan-16x9.json" \
  --voice "$REPO/docs/explainer-direction-checkpoint/evidence/voice.wav" \
  --voice-meta "$REPO/docs/explainer-direction-checkpoint/evidence/voice-meta.json" \
  --chrome "$(command -v google-chrome)" \
  --out "$OUT" \
  --workers 2
```

Choose `plan-9x16.json` or `plan-1x1.json` for the other native formats. Supply an
explicit installed Chrome/Chromium path if `google-chrome` is not available.
Rendering writes frames, the encoded film and a new render manifest outside Git.
Never reuse an existing output directory.

Pinned environments are needed for strict pixel reproducibility. Chrome,
font rendering or ffmpeg differences can alter frame/encoded hashes; the supplied
original files remain the evidence of the original run.

## 6. Fresh automatic authoring is a separate operation

The current `tools/make_film.py` exposes `--compact` and
`--source-quote-narration`. Its local provider and voice dependencies must be
configured explicitly; see the [engine README](../../engine_sources/explainer-direction/README.md).

The original session used a diagnostic wrapper with split local-model routing,
logged requests, exact-request replay and a local entailment veto. The unchanged
VM-specific wrapper and recorded requests are preserved separately under
[session-tools](session-tools/README.md); model weights are not included. That
wrapper is historical state, not a portable entry point. The public CLI is not
a claim of byte-identical reauthoring.

Use `lightning_evidence.json` and `lightning_context.json` to inspect the proof's
inputs. A fresh acceptance test must use an unrelated topic and actual source
records. Do not present frozen plan replay as general automatic-authoring success.

## 7. Next work

Start at roadmap M1: effective visibility, relationally safe focus movement,
attached labels and connector preservation. Keep the archived failure unchanged.
Fix the mechanism generally, then demonstrate it on a fresh unrelated topic.
