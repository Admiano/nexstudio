#!/usr/bin/env python3
"""Restore checksum-pinned SceneBam formal Blender sources for preview + video.

The release is generated from the actual production-assembled V3/V6 cast proof;
the archived binary payload never comes from image generation or a demo mock.
Fail closed on network, missing assets and checksum mismatches.
"""
import hashlib,json,os,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
META=ROOT/'config/scenebam-formal-assets.json'
TARGET=ROOT/'engine_sources/makehuman-lineart/assets/cast-formals'
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
    manifest=json.loads(META.read_text())
    archive=manifest.get('archiveSha256','')
    files=manifest.get('files',{})
    if not archive or len(archive)!=64 or set(files)!=REQUIRED:
        raise SystemExit('CAST_FORMAL_ASSET_MANIFEST_UNPINNED')
    TARGET.mkdir(parents=True,exist_ok=True)
    if all((TARGET/(name+'.blend')).is_file() and digest(TARGET/(name+'.blend'))==files[name] for name in REQUIRED):
        print('CAST_FORMAL_ASSETS_VERIFIED',len(REQUIRED))
        return
    url=manifest['url']
    if not url.startswith('https://github.com/Admiano/nexstudio/releases/download/'):
        raise SystemExit('CAST_FORMAL_ASSET_URL_NOT_TRUSTED')
    tmp=TARGET.parent/'.cast-formals-download.tmp'
    try:
        with urllib.request.urlopen(url,timeout=240) as response,tmp.open('wb') as out:
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                out.write(chunk)
        if digest(tmp)!=archive:
            raise RuntimeError('CAST_FORMAL_ARCHIVE_SHA256_MISMATCH')
        with tarfile.open(tmp,mode='r:gz') as tar:
            names={p.name for p in tar.getmembers()}
            if names != {name+'.blend' for name in REQUIRED}:
                raise RuntimeError('CAST_FORMAL_ARCHIVE_UNEXPECTED_CONTENT')
            for m in tar.getmembers():
                if not m.isfile() or m.name not in names or m.size>128*1024*1024:
                    raise RuntimeError('CAST_FORMAL_ARCHIVE_UNSAFE_ENTRY')
                src=tar.extractfile(m)
                if not src:raise RuntimeError('CAST_FORMAL_ARCHIVE_READ_FAILED')
                path=TARGET/m.name;pending=path.with_suffix('.pending')
                with pending.open('wb') as out:
                    while True:
                        chunk=src.read(1024*1024)
                        if not chunk:break
                        out.write(chunk)
                if digest(pending)!=files[m.name[:-6]]:
                    pending.unlink(missing_ok=True)
                    raise RuntimeError('CAST_FORMAL_BLEND_SHA256_MISMATCH:'+m.name)
                pending.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    print('CAST_FORMAL_ASSETS_INSTALLED',len(REQUIRED))
if __name__=='__main__':main()
