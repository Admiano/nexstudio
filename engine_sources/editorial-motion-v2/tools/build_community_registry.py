#!/usr/bin/env python3
"""Materialise licence-clean community icon packs into the editorial asset space.

Reads vendored Iconify-format packs (``assets/community/packs/<slug>/icons.json``
+ ``info.json``), keeps icons whose names match the explainer-domain vocabulary,
normalises every colour to ``currentColor`` (the runtime owns ink and accent),
and writes mono SVGs plus a registry carrying source-pack provenance, upstream
licence and sha256 per asset — the same provenance contract as AEV1.

    python3 tools/build_community_registry.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS_DIR = ROOT / 'assets' / 'community' / 'packs'
OUT = ROOT / 'assets' / 'community'

# Explainer-domain vocabulary; an icon is admitted if any token appears in its name.
DOMAINS = {
    'food': 'honey almond nut peanut sugar syrup sweet jar bottle milk egg bread wheat grain apple banana fruit carrot vegetable tomato potato coffee tea cup drink water juice wine beer restaurant chef cook kitchen utensil fork spoon knife pizza cake candy chocolate ice fish meat lemon cherry grape strawberry cookie donut doughnut salad soup bowl plate microwave oven fridge refrigerator snack breakfast lunch dinner burger',
    'health': 'health heart pulse activity stethoscope pill capsule medicine medical doctor nurse hospital clinic syringe vaccine bandage thermometer virus bacteria germ dna tooth dental eye ear brain lung bone weight scale run walk sleep fitness gym yoga wheelchair nutrition vitamin allergy protein blood oxygen',
    'finance': 'money dollar euro yen yuan coin cash wallet bank card credit debit payment pay receipt invoice bill tax chart graph trend percent percentage discount price tag sale cart shop store basket bag gift qr barcode currency exchange savings piggy',
    'time': 'clock time timer watch alarm calendar date hourglass history schedule stopwatch deadline',
    'nature': 'leaf tree plant flower sun moon star stars cloud rain snow drop droplet fire flame wind mountain earth globe world seed sprout forest wave ocean weather recycle eco leafs bug insect bee butterfly bird',
    'people': 'user users person people man woman child baby face smile happy sad angry hand hands thumb like dislike team group family friend human',
    'comms': 'chat message messages mail email inbox phone call reply send share comment notification bell megaphone microphone mic video camera photo image podcast radio',
    'objects': 'lightbulb bulb idea gear gears settings tool tools wrench hammer key lock unlock shield flag target rocket search magnify zoom filter book books file files folder document pen pencil edit write award trophy medal bookmark anchor compass map pin location home house building box package gift puzzle magnet link chain infinity check cross plus minus alert warning info question help ban trash archive clipboard list table layout grid layers stack scale ruler scissors paint palette brush',
    'transport': 'car truck bus train plane ship boat bike bicycle scooter road traffic rocket',
    'tech': 'database server cloud cpu chip code terminal wifi signal antenna broadcast satellite robot ai artificial circuit network connect api plug battery power monitor screen laptop mobile device printer keyboard mouse camera video game controller',
    'emotion': 'spark sparkle sparkles zap bolt lightning magic wand star crown diamond gem fire explosion burst confetti balloon party celebrate mood',
}
_KEYWORDS = {d: set(v.split()) for d, v in DOMAINS.items()}
_COLOUR = re.compile(r'(stroke|fill)="(#[0-9a-fA-F]{3,8}|rgb\([^)]*\)|hsl\([^)]*\)|[a-zA-Z]+)"')
# Names that collide with everyday meaning but pollute coverage (brand glyphs, letters, numbers).
_SKIP = re.compile(r'^(brand-|brand_|letter-|number-|circle-letter|square-letter|circle-number|square-number|[0-9]+$)', re.I)
_MAX_PER_PACK = 700


def _domains_for(name: str) -> list[str]:
    toks = set(re.split(r'[-_]', name))
    hits = [d for d, kws in _KEYWORDS.items() if toks & kws]
    return sorted(hits)


def _svg(prefix: str, name: str, icon: dict, w: int, h: int) -> str:
    body = icon['body']
    # Normalise literal colours to currentColor; iconify stroke packs already use it.
    body = _COLOUR.sub(lambda m: m.group(0) if m.group(2).lower() in ('none', 'currentcolor', 'transparent') else f'{m.group(1)}="currentColor"', body)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">{body}</svg>\n'


def main() -> None:
    registry_assets = []
    for pack_dir in sorted(PACKS_DIR.iterdir()):
        icons_file = pack_dir / 'icons.json'
        info_file = pack_dir / 'info.json'
        if not icons_file.exists():
            continue
        data = json.loads(icons_file.read_text())
        info = json.loads(info_file.read_text()) if info_file.exists() else {}
        prefix = data.get('prefix') or pack_dir.name
        license_info = info.get('license', {})
        license_id = license_info.get('spdx') or info.get('licence', {}).get('spdx') or 'see-pack-LICENSE'
        w, h = int(data.get('width', 24)), int(data.get('height', 24))
        picked = []
        for name, icon in data['icons'].items():
            if _SKIP.match(name):
                continue
            doms = _domains_for(name)
            if not doms:
                continue
            picked.append((name, icon, doms))
        picked.sort()
        picked = picked[:_MAX_PER_PACK]
        out_dir = OUT / 'icons' / prefix
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, icon, doms in picked:
            svg = _svg(prefix, name, icon, w, h)
            dst = out_dir / f'{name}.svg'
            dst.write_text(svg)
            registry_assets.append({
                'id': f'icon.{prefix}.{name}',
                'label': name.replace('-', ' '),
                'family': 'icon',
                'domain': doms[0] if len(doms) == 1 else 'multi',
                'path': str(dst.relative_to(OUT)),
                'sha256': hashlib.sha256(dst.read_bytes()).hexdigest(),
                'source': {
                    'pack': f"{info.get('name', prefix)} (Iconify snapshot)",
                    'asset_id': name,
                    'pack_url': info.get('license', {}).get('url') or info.get('homepage', ''),
                    'sha256': hashlib.sha256(icon['body'].encode()).hexdigest(),
                },
                'license': license_id,
                'eligibility': 'eligible-permissive-license-attribution-optional',
                'tags': sorted(set(re.split(r'[-_]', name)) | set(doms)),
                'affordances': ['placeable', 'pointable'],
            })
        print(f'{prefix}: {len(picked)} icons materialised ({license_id})')
    doc = {
        'schema': 'NexStudioIllustrationRegistryV1',
        'version': 'COMMUNITY-1.0.0-mono',
        'policy': 'P8 references assets by id. The compiler validates the reference; it never searches this catalogue by wording.',
        'colour': 'currentColor only; ink and accent are runtime-owned',
        'count': len(registry_assets),
        'assets': registry_assets,
    }
    (OUT / 'icons-registry.json').write_text(json.dumps(doc, indent=2) + '\n')
    print(f'total {len(registry_assets)} -> assets/community/icons-registry.json')


if __name__ == '__main__':
    main()
