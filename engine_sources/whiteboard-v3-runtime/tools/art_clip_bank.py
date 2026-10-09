"""Build assets/semantic/art_clip.npz: CLIP image embedding of every
drawable glyph, rendered through v3_board_renderer's stroke path."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_clip  # noqa: E402
import pipeline_v3_narration_timed as pv  # noqa: E402
pv.load_execution_body()
import v3_board_renderer as vr  # noqa: E402

SKIP = ('animicon', 'notomoji')


def main(update=False):
    keys, ims = [], []
    have = set()
    if update and art_clip.BANK.is_file():
        z = np.load(art_clip.BANK, allow_pickle=False)
        old_keys, old_emb = list(z['keys']), z['emb']
        have = set(old_keys)
    for (d, slug) in sorted(vr._icon_index()):
        if d in SKIP or f'{d}|{slug}' in have:
            continue
        try:
            st = vr._strokes_for(('icon', d, slug))
        except Exception:
            continue
        if not st or st is vr.PROPS.get('tile'):
            continue
        im = art_clip.raster(st)
        if im is not None:
            keys.append(f'{d}|{slug}')
            ims.append(im)
    embs = [old_emb] if have else []
    keys = (old_keys if have else []) + keys
    for i in range(0, len(ims), 64):
        embs.append(art_clip.image_embs(ims[i:i + 64]))
        print(i, len(ims), flush=True)
    art_clip.BANK.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(art_clip.BANK, keys=np.array(keys),
                        emb=np.concatenate(embs).astype(np.float16))
    print('banked', len(keys))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--sheet':
        from PIL import Image
        names = sys.argv[2:]
        tiles = [art_clip.raster(vr._strokes_for(tuple(n.split(':'))))
                 for n in names]
        sheet = Image.new('RGB', (224 * len(tiles), 224), 'white')
        for i, t in enumerate(tiles):
            if t:
                sheet.paste(t, (224 * i, 0))
        sheet.save('/tmp/sheet.png')
    else:
        main(update='--update' in sys.argv[1:])
