#!/usr/bin/env python3
"""Bake Noto animated emoji (Lottie) to PNG sprite strips.

Reads <src>/<hex>/lottie.json files (noto-emoji-animation mirror), renders
every frame via python-lottie SVG export + cairosvg at 160px, quantizes to
palette PNG (tRNS alpha), and writes assets/notomoji/<hex>/fNNNN.png +
meta.json + index.json (hex -> tokens from openmoji.json: annotation,
tags, group/subgroup names). Skintone-modifier variants are skipped —
the base emoji covers them.

License: Noto Animated Emoji is CC-BY 4.0 — attribution required where used.
Usage:
    python3 tools/notomoji_pack.py ~/emoji/noto-anim/lottie
"""
import io
import json
import re
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'notomoji'
EMOJI_INDEX = Path.home() / 'emoji' / 'openmoji.json'
SIZE = 160
FPS = 30
SKINTONE = re.compile(r'1f3f[b-f]')


def _hexkey(dirname):
    return dirname.upper().replace('_', '-').replace('-FE0F', '')


def _tokens_for(dirname, emoji_idx):
    toks = set()
    ent = emoji_idx.get(_hexkey(dirname))
    if ent:
        toks.update(w for w in re.split(r'[\s,-]+', ent.get('annotation') or '')
                    if len(w) > 1)
        toks.update(w.strip() for w in (ent.get('tags') or '').split(',')
                    if len(w.strip()) > 1)
        toks.update(ent.get('subgroups') or '')
        grp = (ent.get('group') or '').split('-')
        toks.update(w for w in grp if len(w) > 1)
    # the hex itself stays a valid literal lookup
    toks.add(dirname.lower())
    return sorted(toks)


def bake_one(args):
    src, slug, out_dir = args
    try:
        return _bake(src, slug, out_dir)
    except Exception as exc:                    # noqa: BLE001
        print(f'SKIP {slug}: {exc}', flush=True)
        return slug, 0


def _bake(src, slug, out_dir):
    from PIL import Image
    import lottie
    import cairosvg
    from lottie.exporters.svg import export_svg
    an = lottie.parsers.tgs.parse_tgs(str(src))
    start, end = int(an.in_point), int(an.out_point)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for i in range(start, end + 1):
        b = io.StringIO()
        export_svg(an, b, i)
        png = cairosvg.svg2png(bytestring=b.getvalue().encode(),
                               output_width=SIZE, output_height=SIZE)
        im = Image.open(io.BytesIO(png)).convert('RGBA')
        im.quantize(colors=255, method=Image.FASTOCTREE).save(
            str(out / f'f{n:04d}.png'), optimize=True)
        n += 1
    meta = {'frames': n, 'fps': FPS, 'w': SIZE, 'h': SIZE,
            'loop': True, 'source': 'noto-animated-emoji',
            'license': 'CC-BY-4.0'}
    (out / 'meta.json').write_text(json.dumps(meta))
    return slug, n


def main(src_dir):
    src = Path(src_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    emoji_idx = {e['hexcode']: e for e in json.loads(EMOJI_INDEX.read_text())}
    jobs, idx = [], {}
    for d in sorted(src.iterdir()):
        if not (d / 'lottie.json').is_file() or SKINTONE.search(d.name):
            continue
        slug = d.name
        jobs.append((str(d / 'lottie.json'), slug, str(OUT / slug)))
        idx[slug] = {'tokens': _tokens_for(slug, emoji_idx)}
    print(f'{len(jobs)} emoji to bake', flush=True)
    with Pool(3) as pool:
        done = 0
        for slug, n in pool.imap_unordered(bake_one, jobs):
            done += 1
            if done % 25 == 0 or done == len(jobs):
                print(f'{done}/{len(jobs)} ({slug}: {n}f)', flush=True)
    ipath = OUT / 'index.json'
    if ipath.is_file():
        old = json.loads(ipath.read_text())
        for slug, m in idx.items():
            if slug not in old:
                old[slug] = m
        idx = old
    ipath.write_text(json.dumps(idx, indent=1))
    print(f'wrote {len(idx)} notomoji -> {OUT}')


if __name__ == '__main__':
    main(sys.argv[1])
