# Local explainer narration

Heart, Sky, Sarah, Liam and Adam can run locally using Kokoro ONNX. They are
separate voices from Microsoft's online Emma, Emily, Andrew and Steffan.
Selecting Emma never silently substitutes a local voice.

Install the repository's `requirements.txt` in the render worker's Python
environment. Download the official model and voice files from
[kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1):

- `kokoro-v1.0.onnx`
- `voices-v1.0.bin`

Place both files in `llm/kokoro/` at the repository root, or set
`KOKORO_MODEL_PATH` and `KOKORO_VOICES_PATH` to their absolute paths. The bundle
is ignored by Git. With these files, narration uses the CPU and the bundled
phonemizer without a cloud voice request. `KOKORO_CPU_THREADS=auto` uses the
ONNX runtime's automatic CPU threading; a positive integer overrides it.

Existing hosts without an ONNX bundle retain the original Kokoro `KPipeline`
backend. Caption alignment still uses the existing faster-whisper model;
download/cache that model before working offline.

After an online voice failure, **Change voice and retry** returns to the saved
narration and direction so you can select a local voice without rewriting.

## Microsoft online voices

After installing Python dependencies, run the following using the render
worker's Python interpreter:

```console
python scripts/patch-edge-tts.py
```

This updates the installed library's narration and voice-list endpoints to
`api.msedgeservices.com`. The patch is idempotent and preserves the existing
token calculation, voice selection and speed. Docker builds and the local
Windows stack launcher apply it automatically.

This is an endpoint compatibility patch for the current Microsoft migration,
not an implementation of its new v2 token algorithm. See
[upstream issue 490](https://github.com/rany2/edge-tts/issues/490).
