#!/usr/bin/env python3
"""Verify the six immutable real Blender formalwear sources bundled into SceneBam.

No network at build time. Never substitute an unknown donor or generated image.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'engine_sources/makehuman-lineart/assets/cast-formals'
META=ROOT/'config/scenebam-formal-assets.json'
REQUIRED={'female-double-breasted','female-statement','male-jacket-tie',
          'male-double-breasted','male-navy-classic','male-dinner-jacket'}
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()
def main():
    if not META.is_file():
        raise SystemExit('CAST_FORMAL_ASSET_MANIFEST_MISSING')
    m=json.loads(META.read_text())
    if set(m.get('files',{}))!=REQUIRED:
        raise SystemExit('CAST_FORMAL_ASSET_MANIFEST_INCOMPLETE')
    for variant,pin in m['files'].items():
        path=TARGET/(variant+'.blend')
        if len(pin)!=64 or not path.is_file() or digest(path)!=pin:
            raise SystemExit('CAST_FORMAL_ASSET_HASH_MISMATCH:'+variant)
    print('CAST_FORMAL_SIX_BLENDER_ASSETS_VERIFIED')
if __name__=='__main__':main()
