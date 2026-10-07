#!/usr/bin/env python3
"""Tag the community SFX pool so the compiler can bind it semantically.

sfx/wooshes: the vendored CC0 organic-whoosh pack was unreachably stored —
no semantic_tag and community-relative paths, which `_merge_community_foley`
cannot resolve (it joins engine-root-relative paths). Give each file the
`motion.ui.whoosh` tag, a real duration and the engine-relative path so it
becomes selectable for WIPE_SWEEP / TRANSITION_SWEEP accents.

Music beds are not touched here: `tools/vendor_music.py` is the one authority
for their measurement (duration, bpm, grid phase, loudness, energy) and moods.

    python3 tools/tag_community_audio.py

Idempotent.
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'assets' / 'community' / 'manifest.json'


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), 'rb') as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    m = json.loads(MANIFEST.read_text())
    wooshes = 0
    for a in m['assets']:
        if 'wooshes-organic' in a['path']:
            rel = a['path'] if a['path'].startswith('assets/community/') else f'assets/community/{a["path"]}'
            a['path'] = rel
            a['semantic_tag'] = 'motion.ui.whoosh'
            a['family'] = 'motion'
            a['duration_s'] = round(_wav_duration(ROOT / rel), 3)
            wooshes += 1
    MANIFEST.write_text(json.dumps(m, indent=1) + '\n')
    print(f'tagged {wooshes} wooshes')


if __name__ == '__main__':
    main()
