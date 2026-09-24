"""visemes — VO audio -> mouth-shape timeline via bundled Rhubarb Lip Sync.

    python3 tools/vo/visemes.py vo.wav out_visemes.json

Rhubarb (MIT, bundled binary at tools/vo/bin/rhubarb) emits Preston-Blair
mouth cues A-H,X; we normalize them onto the carrier rig's seven mouth
shapes (rest/mbp/ah/ee/oh/fv/relax). The JSON is consumed per frame by
the figure render paths (req.visemes) — deterministic, no runtime LLM.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

RHUBARB = Path(__file__).resolve().parent / 'bin' / 'rhubarb'

# Preston-Blair -> carrier-rig mouth shapes
# (NEX_MOUTH_MINIMAL keys: REST/MBP/AH/EE/OH/FV/RELAX).
#  A mbp closed | B slight-open | C open | D wide | E fv | F oo/uu | G L | H ee | X rest
SHAPE_MAP = {
    'A': 'mbp', 'B': 'relax', 'C': 'ah', 'D': 'ah', 'E': 'fv',
    'F': 'oh', 'G': 'relax', 'H': 'ee', 'X': 'rest',
}


def viseme_timeline(wav: Path, recognizer='pocketSphinx'):
    """Run rhubarb -> [{start, end, shape, viseme}]."""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'out.json'
        subprocess.run(
            [str(RHUBARB), '--exportFormat', 'json', '-r', recognizer,
             '-o', str(out), str(wav)],
            check=True, capture_output=True)
        cues = json.loads(out.read_text())['mouthCues']
    return [
        {'start': c['start'], 'end': c['end'], 'shape': c['value'],
         'viseme': SHAPE_MAP.get(c['value'], 'rest')}
        for c in cues
    ]


def viseme_at(timeline, t):
    for c in timeline:
        if c['start'] <= t <= c['end']:
            return c['viseme']
    return 'rest'


def main():
    wav, out = Path(sys.argv[1]), Path(sys.argv[2])
    rec = sys.argv[3] if len(sys.argv) > 3 else 'pocketSphinx'
    tl = viseme_timeline(wav, rec)
    out.write_text(json.dumps({'source': 'rhubarb-1.14.0', 'cues': tl}, indent=1))
    print(f'{len(tl)} cues -> {out}')


if __name__ == '__main__':
    main()
