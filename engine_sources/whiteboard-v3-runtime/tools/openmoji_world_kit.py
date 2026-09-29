#!/usr/bin/env python3
"""General-world art kit from the OpenMoji colour set.

Keeps concrete things (objects, places, vehicles, animals, plants, food,
activities, OpenMoji extras), drops faces, people, flags and skin-tone
variants, flattens each glyph (transforms baked, shapes to polylines) and
writes assets/kits/world/<slug>.svg plus a kit manifest. Kit art renders
with its own flat colours under ink outlines. Slugs already authored in
another kit are skipped so bespoke art keeps priority.

License: OpenMoji is CC BY-SA 4.0 (hfg-gmuend) — attribution required.
Usage:
    python3 tools/openmoji_world_kit.py ~/emoji/color ~/emoji/openmoji.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from openmoji_pack import flatten_svg, _slug  # noqa: E402

GROUPS = ('objects', 'travel-places', 'animals-nature', 'food-drink',
          'activities', 'extras-openmoji', 'extras-unicode')
SKIP_SUB = ('flag', 'time', 'clock', 'keycap', 'hand', 'face', 'person',
            'family', 'emotion', 'zodiac', 'arrow', 'av-symbol',
            'alphanum', 'geometric', 'math', 'punctuation', 'currency',
            'other-symbol', 'gender', 'religion', 'warning')
# people draw through the character system, never as an emoji glyph
PEOPLE = {'person', 'people', 'man', 'woman', 'men', 'women', 'human',
          'boy', 'girl', 'child', 'baby', 'adult', 'worker', 'explorer',
          'dj', 'barista', 'gardener', 'aromantic'}
KIT = ROOT / 'assets' / 'kits'
OUT = KIT / 'world'
# OpenMoji's neutral light grey reads as faded ink on cream paper
RECOLOR = {'#d0cfce': '#ffffff'}
STOP = {'the', 'and', 'with', 'in', 'on', 'of', 'a', 'an', 'for', 'to',
        'emoji', 'openmoji'}
ANY_STROKE = re.compile(r'stroke="(#[0-9A-Fa-f]{3,6})"')


def _taken():
    out = set()
    for kd in KIT.iterdir():
        if kd.name != 'world' and (kd / 'index.json').is_file():
            out |= set(json.loads((kd / 'index.json').read_text())
                       .get('glyphs', {}))
    return out


def main(src_dir, index_json):
    src = Path(src_dir)
    meta = json.loads(Path(index_json).read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    taken = _taken()
    glyphs = {}
    for e in meta:
        sub = e.get('subgroups') or ''
        if e['group'] not in GROUPS or e.get('skintone') \
                or any(s in sub for s in SKIP_SUB):
            continue
        f = src / f"{e['hexcode']}.svg"
        if not f.is_file():
            continue
        slug = _slug(e['annotation'].replace('’', "'").replace("'", ''))
        if not slug or slug in taken or slug in glyphs \
                or PEOPLE & set(slug.split('-')):
            continue
        els = flatten_svg(f)
        if not els:
            continue
        parts = []
        for pts, fill, closed in els:
            fill = RECOLOR.get(str(fill).lower(), fill)
            fill_attr = '' if fill in ('default', None, 'none') \
                else f' fill="{fill}"'
            d = 'M' + 'L'.join(f"{x:.1f} {y:.1f}" for x, y in pts) \
                + ('Z' if closed else '')
            parts.append(f'<path d="{d}"{fill_attr}/>')
        (OUT / f'{slug}.svg').write_text(
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 72 72'>"
            + ''.join(parts) + '</svg>')
        name = [w for w in slug.split('-') if w not in STOP]
        tags = [t.strip().lower() for t in
                f"{e.get('tags') or ''},{e.get('openmoji_tags') or ''}"
                .split(',') if t.strip()]
        glyphs[slug] = {
            'keywords': sorted(set(name) | {t for t in tags
                                            if t not in STOP}),
            'annotation': e['annotation'],
            'hexcode': e['hexcode'],
            'colors': True,
        }
    (OUT / 'index.json').write_text(json.dumps({
        'name': 'world',
        'domain': 'general objects, places, animals, food (OpenMoji)',
        'license': 'CC BY-SA 4.0 — OpenMoji, hfg-gmuend',
        'glyphs': glyphs}, indent=1))
    (OUT / 'LICENSE-NOTICE.txt').write_text(
        (ROOT / 'assets' / 'openmoji' / 'LICENSE-NOTICE.txt').read_text())
    print(f'wrote {len(glyphs)} glyphs -> {OUT}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
