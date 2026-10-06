"""Vendor the 'scene' art kit: everyday setting pieces and props a story
needs (pier, well, bench, stage, cage, mug ...) from licence-clean open
icon sets, redrawn as outline line art for the board.

    python3 tools/scene_kit_pack.py <game-icons> <lucide> <iconoir>

game-icons.net (CC BY 3.0, credit in LICENSE-NOTICE.txt): silhouettes on
a black square; the square is dropped and the shapes trace as outlines.
Lucide (ISC) and Iconoir (MIT): stroke icons, copied as-is."""
import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'kits' / 'scene'

GAME = {
    'wooden-pier': ('delapouite', ['pier', 'jetty', 'wharf', 'boardwalk',
                                   'dock', 'quay']),
    'bird-cage': ('delapouite', ['cage', 'birdcage', 'bird cage']),
    'round-straw-bale': ('delapouite', ['bale', 'hay bale', 'hay',
                                        'straw', 'straw bale']),
    'well': ('delapouite', ['well', 'water well', 'village well',
                            'wishing well']),
    'park-bench': ('delapouite', ['bench', 'park bench', 'piano bench',
                                  'pew']),
    'bar-stool': ('delapouite', ['stool', 'bar stool', 'piano stool']),
    'wood-beam': ('delapouite', ['beam', 'wooden beam', 'plank', 'rafter',
                                 'timber']),
    'theater-curtains': ('delapouite', ['stage', 'theater', 'theatre',
                                        'curtain', 'curtains', 'concert']),
    'barn': ('delapouite', ['barn', 'stable', 'farmhouse']),
    'cooking-pot': ('delapouite', ['pot', 'cooking pot', 'stew', 'soup pot',
                                   'cauldron']),
    'greek-temple': ('delapouite', ['town hall', 'city hall', 'courthouse',
                                    'museum', 'temple']),
    'wheelbarrow': ('delapouite', ['wheelbarrow', 'barrow']),
    'watering-can': ('delapouite', ['watering can']),
    'hand-truck': ('delapouite', ['hand truck', 'dolly', 'trolley']),
    'table': ('delapouite', ['table', 'dining table', 'kitchen table',
                             'wooden table']),
    'desk': ('delapouite', ['desk', 'writing desk', 'school desk']),
    'sink': ('caro-asercion', ['sink', 'kitchen sink', 'basin']),
    'bathtub': ('delapouite', ['bathtub', 'bath', 'tub']),
    'fireplace': ('delapouite', ['fireplace', 'hearth']),
    'stairs': ('delapouite', ['stairs', 'staircase', 'steps', 'stairway']),
    'bookshelf': ('delapouite', ['bookshelf', 'bookcase', 'shelf',
                                 'shelves']),
    'tree-swing': ('delapouite', ['swing', 'tree swing', 'rope swing']),
    'kid-slide': ('delapouite', ['slide', 'playground slide', 'playground']),
    'farm-tractor': ('delapouite', ['tractor', 'farm tractor']),
}
ICONOIR = {
    'crib': ['crib', 'cot', 'cradle', 'baby bed'],
}
LUCIDE = {
    'sofa': ['sofa', 'couch', 'settee'],
    'armchair': ['armchair', 'easy chair'],
    'coffee': ['mug', 'cocoa', 'hot chocolate', 'coffee mug', 'cup of cocoa',
               'cup of coffee'],
}


def game_svg(src: str) -> str:
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    paths = re.findall(r'<path[^>]*\sd="([^"]+)"', src)
    paths = [d for d in paths if d.replace(' ', '') not in (
        'M00h512v512H0z',)]
    body = ''.join(f'  <path d="{d}" fill="#F5F0E4"/>\n' for d in paths)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
            f'stroke="#222">\n{body}</svg>\n')


def main(game_root: str, lucide_root: str, iconoir_root: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    idx = OUT / 'index.json'
    man = json.loads(idx.read_text()) if idx.is_file() else {
        'name': 'scene', 'general': True, 'glyphs': {}}
    man['domain'] = ('everyday settings and props of stories: piers, '
                     'wells, benches, stages, barns, pots, furniture')
    man['license'] = ('game-icons.net CC BY 3.0 (Delapouite, Caro Asercion), '
                      'Lucide ISC, Iconoir MIT '
                      'and NexStudio-authored; see LICENSE-NOTICE.txt')
    for slug, (author, kws) in GAME.items():
        src = (Path(game_root) / author / f'{slug}.svg').read_text()
        (OUT / f'{slug}.svg').write_text(game_svg(src))
        man['glyphs'][slug] = {'keywords': kws, 'source': f'game-icons/{author}'}
    for slug, kws in LUCIDE.items():
        src = (Path(lucide_root) / 'icons' / f'{slug}.svg').read_text()
        (OUT / f'{slug}.svg').write_text(src.replace('currentColor', '#222'))
        man['glyphs'][slug] = {'keywords': kws, 'source': 'lucide'}
    for slug, kws in ICONOIR.items():
        src = (Path(iconoir_root) / 'icons' / 'regular' /
               f'{slug}.svg').read_text()
        (OUT / f'{slug}.svg').write_text(src.replace('currentColor', '#222'))
        man['glyphs'][slug] = {'keywords': kws, 'source': 'iconoir'}
    idx.write_text(json.dumps(man, indent=1) + '\n')
    print('scene kit', len(man['glyphs']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
