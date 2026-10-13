# Local whiteboard setup

Install `requirements.txt` in the render worker's Python environment, then run:

```console
python scripts/install-engines.py --only whiteboard-v3-system
python scripts/install-whiteboard-language.py
python scripts/install-narration-model.py
python scripts/patch-edge-tts.py
```

The engine installer handles Windows paths longer than 260 characters. The
language installer puts WordNet in `llm/nltk/` by default, or in `NLTK_DATA` or
the directory passed with `--data-dir`. Docker and the local Windows stack
launcher install these dependencies during setup.

WordNet is extracted onto that drive so the planner's dictionary lookups
don't repeatedly decompress the downloaded archive. Artwork lookup only
compares meanings close enough to qualify under the existing ranking rule.

The timing installer reuses an existing cached small Whisper model when
available, copying it to `llm/whisper-small/`, or downloads it onto that drive.
Set `WHISPER_MODEL_PATH` to use another installed timing model. Failed word
timing stops the production with a visible error so the ending isn't cut off
by estimated timestamps.

Kinetic renders put temporary frames beside the output on the render drive.
Whiteboard narration also keeps its temporary audio there. Word timing uses
the CPU with int8 computation and all available CPUs by default; set
`WHISPER_CPU_THREADS` to a positive integer to override the thread count.

Microsoft voices use the service's word timing messages when available, so
they can skip local speech recognition. Incomplete timing metadata uses the
installed model. Native library thread settings are only overridden when
`WHISPER_CPU_THREADS` is explicitly set to a positive integer.

After a failed production, **Review direction and retry** preserves the
narration, voice, duration and whiteboard settings.
