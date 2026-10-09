#!/usr/bin/env python3
"""Materialise licence-clean *colour* art (brand logos, colour emoji, colour UI icons) into
``assets/community/colour/`` with a registry the compiler can resolve by id.

Unlike ``build_community_registry.py`` (mono line icons normalised to ``currentColor``),
these packs keep their native colours: brand marks carry the brand hex, emoji keep their
palette, two-tone icon sets keep their fills. The runtime renders them as-is and only
animates opacity/scale.

Input: a harvest directory holding Iconify-format npm packages (``<slug>/package/icons.json``
+ ``info.json``) and the ``simple-icons`` npm package (``si-src/package/icons/*.svg`` +
``data/simple-icons.json`` for hex/title).

    python3 tools/build_colour_registry.py /path/to/harvest/npm
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'community'
COLOUR_DIR = OUT / 'colour'

# Emoji variants that add bulk without adding meaning for explainer reels.
_SKIP_EMOJI = re.compile(r'(skin-tone|^flag-|-flag$|regional-indicator|keycap|-tone-|light-skin|medium-skin|dark-skin|^family|^couple|^kiss|holding-hands|^man-|^woman-|^person-|^men-|^women-|^people-)')
# Iconify packs: (slug, family, id prefix, filter, per-pack cap).
PACKS = [
    ('logos', 'brand', 'brand.logos', None, None),
    ('noto', 'emoji', 'emoji.noto', _SKIP_EMOJI, None),
    ('fluent-emoji-flat', 'emoji', 'emoji.fluent-flat', _SKIP_EMOJI, None),
    ('fluent-emoji', 'emoji3d', 'emoji.fluent', _SKIP_EMOJI, 700),
    ('fluent-color', 'colour-icon', 'icon.fluent-color', None, None),
    ('icon-park', 'colour-icon', 'icon.icon-park-color', None, None),
]
# fluent-emoji (gradient/3D style) is ~28KB per icon; keep the object/nature/tech vocabulary, drop faces.
_FLUENT3D_KEEP = re.compile(
    r'(rocket|light-bulb|gear|hammer|wrench|key|lock|shield|trophy|medal|crown|gem|star|sparkles|fire|bolt|zap|high-voltage|'
    r'brain|robot|alien|ghost|magic|crystal|hourglass|alarm|watch|clock|calendar|chart|bar-chart|money|dollar|coin|credit-card|'
    r'bank|briefcase|package|box|shopping|cart|bag|gift|balloon|party|confetti|megaphone|loud|bell|mail|envelope|inbox|'
    r'laptop|computer|desktop|keyboard|mouse|printer|phone|mobile|camera|video|film|television|radio|headphone|microphone|'
    r'speaker|musical|guitar|piano|drum|book|books|notebook|memo|page|scroll|newspaper|pencil|pen|paint|palette|artist|'
    r'scissors|paperclip|pushpin|link|chain|magnet|compass|globe|world|map|earth|mountain|volcano|sun|moon|cloud|rain|snow|'
    r'rainbow|umbrella|leaf|seedling|herb|tree|cactus|flower|blossom|sunflower|rose|tulip|mushroom|apple|banana|lemon|grape|'
    r'strawberry|cherry|peach|pineapple|avocado|carrot|corn|bread|croissant|cheese|pizza|burger|hamburger|taco|sushi|coffee|'
    r'tea|beer|wine|cocktail|cake|cookie|doughnut|candy|chocolate|honey|milk|egg|car|taxi|bus|truck|bicycle|scooter|train|'
    r'airplane|ship|anchor|sailboat|house|office|hospital|school|factory|castle|tent|stadium|heart|thumbs|clap|handshake|'
    r'muscle|eye|eyes|ear|nose|tooth|bone|dna|microscope|telescope|test-tube|pill|syringe|stethoscope|thermometer|battery|'
    r'plug|satellite|antenna|hole|puzzle|dice|joystick|game|target|dart|bow|trophy|medal|flag|ticket|label|bookmark|'
    r'wastebasket|toolbox|screwdriver|nut|bolt|gear|link|chains|ladder|fishing|mirror|window|door|bed|couch|chair|toilet|'
    r'shower|bathtub|soap|sponge|bucket|broom|basket|thread|yarn|safety-pin|hook|shopping-bags|receipt|ledger|clipboard|'
    r'card-index|file|folder|calendar|spiral|abacus|input|button|check|cross|question|exclamation|warning|recycling|'
    r'infinity|hundred|graduation|glasses|top-hat|crown|ring|lipstick|watch|dress|shirt|jeans|shoe|boot|sock|backpack|'
    r'luggage|hiking|umbrella|mountain|beach|desert|island|park|fountain|bridge|night|city|sunrise|sunset|sparkle|comet|'
    r'meteor|milky|glowing|dizzy|collision|speech|thought|bubble|hourglass|stopwatch|timer|mantelpiece)'
)
_ID_ATTR = re.compile(r'\bid="([^"]+)"')


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _svg(body: str, w: int, h: int) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}">{body}</svg>\n'


def _entry(aid: str, label: str, family: str, dst: Path, source: dict, license_id: str, tags: list[str], extra: dict | None = None) -> dict:
    e = {
        'id': aid,
        'label': label,
        'family': family,
        'domain': 'multi',
        'path': str(dst.relative_to(OUT)),
        'sha256': _sha(dst.read_bytes()),
        'source': source,
        'license': license_id,
        'eligibility': 'eligible-permissive-license-attribution-optional' if license_id != 'CC0-1.0' else 'eligible-public-domain',
        'colour': 'native',
        'tags': sorted(set(tags)),
        'affordances': ['placeable', 'pointable'],
    }
    if extra:
        e.update(extra)
    return e


def build_iconify(harvest: Path, assets: list[dict]) -> None:
    for slug, family, prefix, skip, cap in PACKS:
        pkg = harvest / slug / 'package'
        icons_file = pkg / 'icons.json'
        if not icons_file.exists():
            print(f'{slug}: missing at {icons_file}, skipped')
            continue
        data = json.loads(icons_file.read_text())
        info = json.loads((pkg / 'info.json').read_text()) if (pkg / 'info.json').exists() else {}
        meta = json.loads((pkg / 'package.json').read_text())
        license_id = (info.get('license') or {}).get('spdx') or meta.get('license') or 'see-pack-LICENSE'
        w, h = int(data.get('width', 24)), int(data.get('height', 24))
        out_dir = COLOUR_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        names = sorted(data['icons'])
        if skip is not None:
            names = [n for n in names if not skip.search(n)]
        if slug == 'fluent-emoji':
            names = [n for n in names if _FLUENT3D_KEEP.search(n)]
        if slug == 'fluent-color':
            # One entry per icon: the largest pixel-size master (names end in -16/-20/-24/-28/-32/-48).
            best: dict[str, tuple[int, str]] = {}
            for n in names:
                m = re.match(r'(.*)-(\d+)$', n)
                base, size = (m.group(1), int(m.group(2))) if m else (n, 0)
                if base not in best or size > best[base][0]:
                    best[base] = (size, n)
            names = sorted(n for _, n in best.values())
        if cap:
            names = names[:cap]
        for name in names:
            icon = data['icons'][name]
            iw, ih = int(icon.get('width', w)), int(icon.get('height', h))
            dst = out_dir / f'{name}.svg'
            dst.write_text(_svg(icon['body'], iw, ih))
            assets.append(_entry(
                f'{prefix}.{name}', name.replace('-', ' '), family, dst,
                {'pack': f"{info.get('name', slug)} (@iconify-json/{slug} {meta.get('version')})", 'asset_id': name,
                 'pack_url': (info.get('author') or {}).get('url') or (info.get('license') or {}).get('url', ''),
                 'sha256': _sha(icon['body'].encode())},
                license_id, re.split(r'[-_]', name) + [family],
            ))
        print(f'{slug}: {len(names)} colour assets ({license_id})')


def build_simple_icons(harvest: Path, assets: list[dict]) -> None:
    pkg = harvest / 'si-src' / 'package'
    data_file = pkg / 'data' / 'simple-icons.json'
    if not data_file.exists():
        print('simple-icons: missing, skipped')
        return
    meta = json.loads((pkg / 'package.json').read_text())
    entries = json.loads(data_file.read_text())
    entries = entries if isinstance(entries, list) else entries['icons']
    out_dir = COLOUR_DIR / 'simple-icons'
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for it in entries:
        slug = it['slug']
        src = pkg / 'icons' / f'{slug}.svg'
        if not src.exists():
            continue
        raw = src.read_bytes()
        dst = out_dir / f'{slug}.svg'
        # simple-icons ships a single path; keep it currentColor so the runtime can paint brand hex or ink.
        dst.write_bytes(raw)
        aliases = it.get('aliases') or {}
        tags = [slug, it['title'].lower()] + [a.lower() for a in aliases.get('aka', [])] + [a.lower() for a in aliases.get('old', [])]
        assets.append(_entry(
            f'brand.si.{slug}', it['title'], 'brand', dst,
            {'pack': f"simple-icons {meta.get('version')} (npm)", 'asset_id': slug, 'pack_url': it.get('source', 'https://simpleicons.org'), 'sha256': _sha(raw)},
            meta.get('license') or 'CC0-1.0', tags,
            {'colour': 'brand', 'brand_hex': f"#{it['hex']}"},
        ))
        n += 1
    print(f'simple-icons: {n} brand marks (CC0-1.0, brand hex carried)')


def main() -> None:
    harvest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'harvest2' / 'npm'
    assets: list[dict] = []
    build_iconify(harvest, assets)
    build_simple_icons(harvest, assets)
    doc = {
        'schema': 'NexStudioIllustrationRegistryV1',
        'version': 'COMMUNITY-1.0.0-colour',
        'policy': 'P8 references assets by id. The compiler validates the reference; it never searches this catalogue by wording.',
        'colour': "native art; entries with colour='brand' are single-path marks painted with brand_hex (or ink on dark bodies)",
        'trademark_note': 'Brand marks are licence-clean (CC0/MIT) as artwork; trademark use is the film owner\'s responsibility.',
        'count': len(assets),
        'assets': assets,
    }
    (OUT / 'colour-registry.json').write_text(json.dumps(doc, indent=1) + '\n')
    print(f'total {len(assets)} -> assets/community/colour-registry.json')


if __name__ == '__main__':
    main()
