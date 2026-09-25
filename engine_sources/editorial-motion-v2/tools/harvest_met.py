"""Harvest Met Museum Open Access (CC0) artworks into banks/met-oa/.

One-time fetch — the harvested files are vendored by bank_index.py like any
other bank, so renders stay offline-deterministic afterward.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/ubuntu/banks/met-oa')
API = 'https://collectionapi.metmuseum.org/public/collection/v1'
UA = {'User-Agent': 'nexstudio-editorial-motion/2.0 (open access harvest)'}

# Curated lanes: history + art registers a storybook film might need.
QUERIES = {
    'ukiyo-e': ['ukiyo-e wave', 'hiroshige', 'hokusai'],
    'manuscript': ['illuminated manuscript', 'book of hours'],
    'map': ['map', 'atlas', 'cartouche'],
    'egypt': ['egyptian', 'pharaoh', 'hieroglyph'],
    'greece': ['greek vase', 'amphora'],
    'rome': ['roman bust', 'roman mosaic'],
    'china': ['chinese painting', 'calligraphy'],
    'india': ['mughal painting', 'indian miniature'],
    'medieval': ['tapestry', 'medieval', 'armor', 'knight'],
    'islamic': ['islamic', 'persian miniature', 'arabesque'],
    'science': ['telescope', 'astrolabe', 'skeleton', 'fossil'],
    'africa': ['african mask', 'bronze benin'],
    'ocean': ['ship', 'sea monster', 'whale'],
    'animals': ['durer rhinoceros', 'animal print'],
    'portrait': ['portrait', 'queen', 'king', 'emperor'],
    'war': ['battle', 'sword', 'cannon'],
    'myth': ['dragon', 'phoenix', 'goddess'],
    'music': ['violin', 'lute', 'drum', 'trumpet'],
    'writing': ['scroll', 'manuscript page', 'letter'],
    'architecture': ['cathedral', 'temple', 'castle', 'pyramid'],
}
PER_LANE = 14  # objects per lane


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    seen = set()
    n = 0
    for lane, queries in QUERIES.items():
        got = 0
        for q in queries:
            if got >= PER_LANE:
                break
            try:
                s = get(f'{API}/search?q={urllib.request.quote(q)}&hasImages=true')
            except Exception:
                continue
            for oid in (s.get('objectIDs') or [])[:160]:
                if got >= PER_LANE:
                    break
                if oid in seen:
                    continue
                if (OUT / lane / f'{oid}.json').exists():
                    seen.add(oid)
                    got += 1
                    continue
                try:
                    o = get(f'{API}/objects/{oid}')
                except Exception:
                    time.sleep(1.2)
                    continue
                time.sleep(0.35)  # Met API rate limit
                if not o.get('isPublicDomain') or not o.get('primaryImageSmall'):
                    continue
                title = (o.get('title') or q).strip()
                artist = (o.get('artistDisplayName') or '').strip()
                date = (o.get('objectDate') or '').strip()
                dst = OUT / lane / f'{oid}.jpg'
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists():
                    try:
                        urllib.request.urlretrieve(o['primaryImageSmall'], dst)
                    except Exception:
                        continue
                    time.sleep(0.15)
                meta = {'id': f'met:{oid}', 'lane': lane, 'title': title,
                        'creator': artist or o.get('culture') or o.get('department') or 'The Met',
                        'license': 'CC0', 'desc': f"{title} {date} {o.get('culture','')} {o.get('medium','')}".strip(),
                        'file': str(dst.relative_to(OUT)), 'w': 0, 'h': 0}
                (OUT / lane / f'{oid}.json').write_text(json.dumps(meta))
                seen.add(oid)
                got += 1
                n += 1
                time.sleep(0.35)
            time.sleep(0.3)
        print(f'{lane}: {got}', flush=True)
    print(f'total={n}')


if __name__ == '__main__':
    main()
