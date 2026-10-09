#!/usr/bin/env python3
"""Bake useAnimations Lottie icons to PNG sprite frames.

Reads lottie JSONs (downloaded from the react-useanimations npm package),
renders every frame via python-lottie SVG export + cairosvg, and writes
assets/animicons/<slug>/fNNNN.png + meta.json (fig_motion-compatible
sprite-strip contract) + index.json (slug -> tokens for icon lookup).

License: useAnimations is CC-BY 4.0 — attribution required where used.
Usage:
    python3 tools/animicons_pack.py ~/emoji/useanimations
"""
import io
import json
import re
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'animicons'
SIZE = 240
FPS = 30

# concept aliases so whiteboard narration lands on the animated set
ALIAS = {
    'checkmark': 'check done yes correct success complete tick',
    'activity': 'pulse heartbeat health activity vitals',
    'settings': 'gear settings options config',
    'settings2': 'gear settings options config cog',
    'alertTriangle': 'warning alert caution danger',
    'alertCircle': 'warning alert info notice',
    'arrowDown': 'down arrow decrease drop fall lower',
    'arrowUp': 'up arrow increase rise raise grow',
    'arrowRight': 'right arrow forward next go',
    'arrowLeft': 'left arrow back previous',
    'download': 'download save get receive',
    'upload': 'upload send share publish',
    'menu': 'hamburger menu navigation list',
    'search': 'search find magnifier lookup',
    'trash': 'delete remove trash bin',
    'edit': 'edit write pencil pen modify',
    'edit2': 'edit write pencil pen modify',
    'edit3': 'edit write pencil pen modify',
    'heart': 'heart love like favorite',
    'star': 'star favorite rating featured',
    'bell': 'bell notification alarm alert ring',
    'bookmark': 'bookmark save keep tag',
    'calendar': 'calendar date schedule day',
    'clock': 'clock time watch timer',
    'lock': 'lock secure security private padlock',
    'unlock': 'unlock open access public',
    'eye': 'eye view see watch look',
    'eyeOff': 'hidden hide invisible private',
    'loading': 'loading spinner wait progress working',
    'loader': 'loading spinner wait progress working',
    'maximize': 'fullscreen expand maximize enlarge',
    'minimize': 'shrink minimize contract smaller',
    'play': 'play start video media',
    'pause': 'pause stop wait hold',
    'skipForward': 'skip forward next fast',
    'skipBack': 'skip back previous rewind',
    'volume': 'volume sound audio speaker',
    'volume2': 'volume sound audio speaker loud',
    'volumeX': 'mute silent quiet volume off',
    'wifi': 'wifi wireless internet network signal',
    'wifiOff': 'offline disconnected wifi off',
    'zoomIn': 'zoom magnify enlarge closer',
    'zoomOut': 'zoom out shrink farther',
    'infinity': 'infinity infinite endless forever loop',
    'power': 'power on off start shutdown button',
    'radio': 'radio broadcast fm audio',
    'film': 'film movie video cinema',
    'copy': 'copy duplicate clone paste',
    'folder': 'folder directory files',
    'helpCircle': 'help question support faq',
    'home': 'home house main',
    'mail': 'email mail message letter inbox',
    'mapPin': 'location map pin place marker',
    'mic': 'microphone mic voice record audio',
    'micOff': 'microphone mute mic off',
    'moon': 'moon night dark sleep',
    'sun': 'sun day light bright morning',
    'toggleLeft': 'toggle switch left off',
    'toggleRight': 'toggle switch right on',
    'userPlus': 'user add person invite signup',
    'userMinus': 'user remove person delete',
    'userX': 'user remove person delete block',
    'userCheck': 'user verified person approved',
    'users': 'users people team group community',
    'video': 'video camera record film',
    'videoOff': 'video camera off',
    'github': 'github code git repository',
    'facebook': 'facebook social meta',
    'instagram': 'instagram social photo',
    'linkedin': 'linkedin social work professional',
    'twitter': 'twitter social tweet bird',
    'youtube': 'youtube video play',
    'twitch': 'twitch stream live',
    'codepen': 'codepen code demo',
    'codesandbox': 'codesandbox code demo',
    'dribbble': 'dribbble design',
    'figma': 'figma design tool',
    'framer': 'framer design prototype',
    'gitlab': 'gitlab git repository',
    'slack': 'slack chat message work',
    'trello': 'trello board kanban tasks',
    'chrome': 'chrome browser google',
    'airplay': 'airplay cast screen share',
    'archive': 'archive box storage old',
    'attach': 'attach paperclip attachment file',
    'behance': 'behance design portfolio',
    'cast': 'cast screen airplay chromecast',
    'command': 'command key apple mac',
    'enter': 'enter key keyboard return',
    'filePlus': 'file add new document create',
    'frame': 'frame crop border region',
    'grip': 'grip drag handle move',
    'move': 'move drag arrows position',
    'scissors': 'scissors cut trim split',
    'skip': 'skip next forward jump',
    'vibrate': 'vibrate buzz phone haptic',
    'visibility': 'visibility eye show view',
    'finger-down': 'finger point down tap press',
    'finger-up': 'finger point up tap press',
    'expand': 'expand grow enlarge bigger',
    'contract': 'contract shrink collapse smaller',
    'zoom': 'zoom magnify search enlarge',
}


def _camel_tokens(slug):
    words = re.sub(r'([a-z])([A-Z])', r'\1-\2', slug).lower().split('-')
    return set(words)


def bake_one(args):
    src, slug, out_dir = args
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
        cairosvg.svg2png(bytestring=b.getvalue().encode(),
                         write_to=str(out / f'f{n:04d}.png'),
                         output_width=SIZE, output_height=SIZE)
        n += 1
    meta = {'frames': n, 'fps': FPS, 'w': SIZE, 'h': SIZE,
            'loop': False, 'source': 'useAnimations', 'license': 'CC-BY-4.0'}
    (out / 'meta.json').write_text(json.dumps(meta))
    return slug, n


def main(src_dir):
    src = Path(src_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    jobs, idx = [], {}
    for f in sorted(src.glob('*.json')):
        slug = f.stem
        jobs.append((str(f), slug, str(OUT / slug)))
        toks = _camel_tokens(slug) | set(ALIAS.get(slug, '').split())
        idx[slug] = {'tokens': sorted(t for t in toks if len(t) > 1)}
    with Pool(3) as pool:
        for slug, n in pool.imap_unordered(bake_one, jobs):
            print(f'{slug}: {n} frames', flush=True)
    # merge into any curated index — hand-edited tokens win
    ipath = OUT / 'index.json'
    if ipath.is_file():
        old = json.loads(ipath.read_text())
        for slug, m in idx.items():
            if slug not in old:
                old[slug] = m
        idx = old
    ipath.write_text(json.dumps(idx, indent=1))
    print(f'wrote {len(idx)} animicons -> {OUT}')


if __name__ == '__main__':
    main(sys.argv[1])
