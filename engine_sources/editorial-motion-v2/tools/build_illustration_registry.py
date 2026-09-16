#!/usr/bin/env python3
"""Build the illustration asset registry from the AEV1 curated pack.

Only line assets with recorded commercial eligibility and no trademark risk are
admitted (icons, literal props, visual metaphors, mechanism heroes, environment
fragments). Characters are excluded: figures come from Open Peeps. Every colour
is normalised to ``currentColor`` so the runtime owns ink and accent.

    python3 tools/build_illustration_registry.py [--pack <aev1 dir>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT.parents[1] / 'engines' / 'editorial' / 'explainer-motion' / 'faceless-public-levels-v1' / 'assets' / 'aev1-curated-200'
OUT = ROOT / 'assets' / 'illustration'
FAMILIES = {'icon', 'literal-prop', 'visual-metaphor', 'mechanism-hero', 'environment-fragment'}
COLOUR = re.compile(r'(stroke|fill)="(#[0-9a-fA-F]{3,8}|rgb\([^)]*\)|[a-zA-Z]+)"')


def normalise(svg: str) -> str:
    def repl(m: re.Match) -> str:
        attr, val = m.group(1), m.group(2)
        if val.lower() in ('none', 'transparent'):
            return m.group(0)
        return f'{attr}="currentColor"'
    svg = COLOUR.sub(repl, svg)
    svg = re.sub(r'<metadata[^>]*/>', '', svg)
    return svg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--pack', default=str(DEFAULT_PACK))
    args = ap.parse_args()
    pack = Path(args.pack)
    manifest = json.loads((pack / 'manifest.json').read_text())
    (OUT / 'aev1').mkdir(parents=True, exist_ok=True)
    assets = []
    for a in manifest['assets']:
        if a['family'] not in FAMILIES or a.get('trademarkRisk') or not a.get('commercialEligibility', '').startswith('eligible'):
            continue
        src = pack / a['file']
        if not src.exists():
            continue
        rid = a['sourceRegistryId']
        dst = OUT / 'aev1' / f'{rid}.svg'
        dst.write_text(normalise(src.read_text()))
        assets.append({
            'id': rid, 'label': a['label'], 'family': a['family'], 'domain': a.get('domain'),
            'path': str(dst.relative_to(OUT)), 'sha256': hashlib.sha256(dst.read_bytes()).hexdigest(),
            'source': {'pack': manifest['package'], 'asset_id': a['assetId'], 'sha256': hashlib.sha256(src.read_bytes()).hexdigest()},
            'license': a['sourceLicense'], 'eligibility': a['commercialEligibility'],
            'tags': sorted(set(a.get('semanticTags', []))), 'affordances': sorted(set(a.get('interactionModes', []))),
        })
    doc = {
        'schema': 'NexStudioIllustrationRegistryV1',
        'version': f"AEV1-{manifest.get('version')}-mono",
        'policy': 'P8 references assets by id. The compiler validates the reference; it never searches this catalogue by wording.',
        'colour': 'currentColor only; ink and accent are runtime-owned',
        'count': len(assets),
        'assets': assets,
    }
    (OUT / 'registry.json').write_text(json.dumps(doc, indent=2) + '\n')
    print(f'{len(assets)} assets -> {OUT / "registry.json"}')


if __name__ == '__main__':
    main()
