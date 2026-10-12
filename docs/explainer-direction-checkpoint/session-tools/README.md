# Historical session diagnostics

This directory preserves additional development state, not a portable production
entry point:

- `run_live.py`: the original VM-specific diagnostic wrapper, unchanged.
- `kokoro_liam.json`: the original explicit model/config/voice paths and rights
  declaration. No model weights are included.
- `requests/`: the eight recorded requests/responses/transports used by the
  preceding v17 attempt and replayed in the final v18 compiler-fix run, plus
  cache/route metadata.

Some decisions in v17 were already replayed from earlier live attempts. Their
`.cache.json` files retain those historical references. The earlier VM directories
are not all included here. Treat elapsed times for cached requests as replay time,
not fresh inference latency.

The wrapper has hard-coded repository/session paths and relies on local server,
Kokoro and entailment setup. It also reads session-root input files. Do not assume
it runs from this directory as-is. Portability is remaining roadmap work.

For model-free validation and exact-plan rendering, use [RECOVERY.md](../RECOVERY.md).
For fresh authoring, inspect the engine's real CLI and configure the declared
local dependencies explicitly. Neither path grants production authority.
