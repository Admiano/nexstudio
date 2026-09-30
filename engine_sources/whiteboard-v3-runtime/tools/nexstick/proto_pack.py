#!/usr/bin/env python3
"""proto_pack — import the RGS_Dev 'Animated Prototype Character' pack
(CC0, License.txt in the zip) into nexstick baked-sprite dirs.

Each action set becomes tools/nexstick/baked/PROTO_<ACTION>/ (base set)
or PROTO_<SET>_<ACTION>/ (weapon sets) holding fNNNN.png frames trimmed
to the clip's union alpha bbox plus a meta.json. These play through
fig_motion.get_strip like any baked clip; comic panels pick a single
posed frame.

Usage: python3 tools/proto_pack.py [pack_root]
       default: ~/proto_char/Animated Prototype Character
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PACK = Path(sys.argv[1] if len(sys.argv) > 1 else
            Path.home() / 'proto_char' / 'Animated Prototype Character')
OUT = HERE / 'baked'
SETS = {'Base Character': 'PROTO', 'Sword': 'PROTO_SWORD',
        'Pistol': 'PROTO_PISTOL', 'Rifle': 'PROTO_RIFLE'}
# the pack ships keyframes, not a fixed-rate capture — 8fps is the
# slow-stick idiom these strips were authored for
PACK_FPS = 8.0


def _actions(d: Path) -> dict[str, list[Path]]:
    acts: dict[str, list[Path]] = {}
    for p in d.glob('*.png'):
        m = re.match(r'(.+?) \((\d+)\)\.png$', p.name)
        if m:
            acts.setdefault(m.group(1), []).append((int(m.group(2)), p))
    return {a: [p for _, p in sorted(v)] for a, v in acts.items()}


def main() -> int:
    made = []
    for set_name, prefix in SETS.items():
        sd = PACK / set_name
        if not sd.is_dir():
            continue
        for act, files in sorted(_actions(sd).items()):
            clip = f'{prefix}_{act.upper()}'
            imgs = [Image.open(f).convert('RGBA') for f in files]
            # union alpha bbox — keeps frame-to-frame registration for
            # cycles while dropping the pack's dead 512px margin
            box = None
            for im in imgs:
                b = im.getchannel('A').getbbox()
                box = (b if box is None else
                       (min(box[0], b[0]), min(box[1], b[1]),
                        max(box[2], b[2]), max(box[3], b[3])))
            if not box:
                continue
            pad = 4
            box = (max(0, box[0] - pad), max(0, box[1] - pad),
                   min(imgs[0].width, box[2] + pad),
                   min(imgs[0].height, box[3] + pad))
            d = OUT / clip
            d.mkdir(parents=True, exist_ok=True)
            for i, im in enumerate(imgs):
                im.crop(box).save(d / f'f{i:04d}.png')
            (d / 'meta.json').write_text(json.dumps({
                'clip': clip, 'frames': len(imgs), 'fps': PACK_FPS,
                'res': [box[2] - box[0], box[3] - box[1]],
                'cam': 'side', 'proto': True,
                'source': 'rgs-proto', 'license': 'CC0'}, indent=1))
            made.append(clip)
    print(f'{len(made)} proto clips -> {OUT}')
    print('\n'.join(made))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
