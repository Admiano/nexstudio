"""Bank ingestion: harvest open-licensed illustration banks into assets/bank.

Sources (clones under $NEXSTUDIO_BANKS or /home/ubuntu/banks):
  pb-imagebank      Pratham/StoryWeaver — per-image description + illustrator + CC BY/PD
  asp-imagebank     African Storybook — per-story license table (BY kept, NC dropped)
  gsn-imagebank     Global Storybooks — same table format, same filter
  asp-imagebank-new asp colourized variants — same story licensing
  bookdash-books    Book Dash — per-image alt text = description, book title = story

Emits assets/bank/index.json (records + inverted keyword index) and vendored
images under assets/bank/img/<source>/<story>_<file>.jpg downscaled to <=760px.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_IMG = ROOT / 'assets' / 'bank' / 'img'
OUT_INDEX = ROOT / 'assets' / 'bank' / 'index.json'
BANKS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/ubuntu/banks')
MAX_EDGE = 760
JPEG_Q = 78

STOP = set('''a an and are as at be but by for from had has have her his i in is it its
of on or she so that the their they to was we were with you your he not no my me do does did
will would can could this those these them then than too very just over under again once each
all any both few more most other some such only own same off about into out up down
'''.split())

KEEP_LICENSE = re.compile(r'((cc[\s-]*)?by\b|public.?domain|cc0|\bpd\b)', re.I)
DROP_LICENSE = re.compile(r'by[\s-]*nc|by[\s-]*sa|by[\s-]*nd|all rights', re.I)


def tokens(text: str) -> List[str]:
    out = []
    for t in re.findall(r'[a-zA-Z][a-zA-Z\-\']+', (text or '').lower()):
        t = t.strip("-'")
        if len(t) < 3 or t in STOP:
            continue
        for form in {t, re.sub(r"('s|s'|s|es|ing|ed)$", '', t) if len(t) > 4 else t}:
            if form and form not in STOP and len(form) >= 3:
                out.append(form)
    return sorted(set(out))


def license_ok(raw: str) -> bool:
    if DROP_LICENSE.search(raw):
        return False
    return bool(KEEP_LICENSE.search(raw))


def norm_license(raw: str) -> str:
    r = raw.strip()
    m = re.search(r'by[\s-]*(\d\.\d)', r, re.I)
    if re.search(r'public.?domain', r, re.I):
        return 'PD'
    if re.search(r'cc0', r, re.I):
        return 'CC0'
    return f'CC BY {m.group(1)}' if m else 'CC BY'


def vendor(src: Path, dst_name: str) -> Optional[Tuple[str, str, int, int]]:
    """Downscale + store; returns (repo-rel img path, sha256, w, h)."""
    dst = OUT_IMG / dst_name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        try:
            im = Image.open(src).convert('RGB')
        except Exception:
            return None
        w, h = im.size
        if max(w, h) > MAX_EDGE:
            k = MAX_EDGE / max(w, h)
            im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=JPEG_Q, optimize=True)
    else:
        try:
            im = Image.open(dst)
        except Exception:
            return None
        w, h = im.size
    sha = hashlib.sha256(dst.read_bytes()).hexdigest()[:16]
    rel = str(dst.relative_to(ROOT))
    return rel, sha, w, h


def parse_story_table(md: str) -> Dict[str, Dict[str, str]]:
    """`NNNN | _Title_ | **Illustrator** | License` → {story_id: {title, illustrator, license}}"""
    stories: Dict[str, Dict[str, str]] = {}
    for ln in md.splitlines():
        m = re.match(r'^\s*(\d{3,4})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$', ln)
        if not m:
            continue
        sid, title, illustrator, lic = m.groups()
        title = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', title)  # [text](url) → text
        title = re.sub(r'[_*<>{}[\]()]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        illustrator = re.sub(r'[*_]', ' ', illustrator).strip()
        illustrator = re.sub(r'\s+', ' ', illustrator)
        stories[sid] = {'title': title, 'illustrator': illustrator, 'license': lic}
    return stories


def harvest_pb(bank: Path, recs: List[Dict]) -> None:
    meta_dir = bank / 'metadata'
    img_dir = bank / 'medium'
    for md_file in sorted(meta_dir.glob('*.md')):
        sid = md_file.stem
        text = md_file.read_text(encoding='utf-8', errors='replace')
        m = re.search(r'story \[([^\]]+)\]', text) or re.search(r'story (.*?) by', text)
        story_title = (m.group(1) if m else sid).strip()
        for ln in text.splitlines():
            r = re.match(r'^\s*(\S+\.(?:jpg|jpeg|png))\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*$', ln)
            if not r:
                continue
            fname, desc, illustrator, lic = r.groups()
            if not license_ok(lic):
                continue
            src = img_dir / sid / fname
            if not src.exists():
                continue
            v = vendor(src, Path('pb') / f'{sid}_{Path(fname).stem}.jpg')
            if not v:
                continue
            rel, sha, w, h = v
            recs.append({
                'id': f'pb:{sid}/{Path(fname).stem}', 'img': rel, 'source': 'pb-imagebank',
                'story': story_title, 'desc': desc.strip(), 'creator': illustrator.strip(),
                'license': norm_license(lic), 'sha256': sha, 'w': w, 'h': h,
                'kw': tokens(f'{desc} {story_title}'),
            })


def harvest_story_table(bank: Path, src_name: str, img_root: Path, recs: List[Dict], sub: str = '') -> None:
    stories = parse_story_table((bank / 'README.md').read_text(encoding='utf-8', errors='replace'))
    for story_dir in sorted(img_root.iterdir()):
        if not story_dir.is_dir():
            continue
        sid = story_dir.name
        st = stories.get(sid)
        if not st or not license_ok(st['license']):
            continue
        for img in sorted(story_dir.iterdir()):
            if img.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
                continue
            v = vendor(img, Path(src_name) / f'{sid}_{img.stem}.jpg')
            if not v:
                continue
            rel, sha, w, h = v
            recs.append({
                'id': f'{src_name}:{sid}/{img.stem}', 'img': rel, 'source': src_name,
                'story': st['title'], 'desc': st['title'], 'creator': st['illustrator'],
                'license': norm_license(st['license']), 'sha256': sha, 'w': w, 'h': h,
                'kw': tokens(st['title']),
            })


def harvest_bookdash(bank: Path, recs: List[Dict]) -> None:
    lic = 'CC BY 4.0'
    for book in sorted(bank.iterdir()):
        if not book.is_dir() or book.name.startswith('.'):
            continue
        lang = book / 'en'
        if not (lang / 'index.md').exists():
            continue
        text = (lang / 'index.md').read_text(encoding='utf-8', errors='replace')
        mt = re.search(r'^title:\s*(.+)$', text, re.M)
        title = (mt.group(1).strip() if mt else book.name.replace('-', ' '))
        creators = ' / '.join(sorted(set(
            re.findall(r'(?:Illustrat\w+|Author|Written by|Drawn by)[:\s]+([^<\n]+)', text))))[:200]
        for m in re.finditer(r'!\[([^\]]*)\]\(\{\{\s*site\.image-set\s*\}\}/([^\)]+)\)', text):
            alt, fname = m.group(1), m.group(2).strip()
            src = lang / 'images' / fname
            if not src.exists():
                continue
            v = vendor(src, Path('bookdash') / f'{book.name}_{Path(fname).stem}.jpg')
            if not v:
                continue
            rel, sha, w, h = v
            recs.append({
                'id': f'bookdash:{book.name}/{Path(fname).stem}', 'img': rel, 'source': 'bookdash',
                'story': title, 'desc': alt.strip(), 'creator': creators or 'Book Dash',
                'license': lic, 'sha256': sha, 'w': w, 'h': h,
                'kw': tokens(f'{alt} {title}'),
            })


def harvest_sidecars(bank: Path, src_name: str, recs: List[Dict]) -> None:
    """Lane dirs holding <file>.jpg + <file>.json sidecars (met-oa, maps)."""
    for meta_file in sorted(bank.rglob('*.json')):
        try:
            meta = json.loads(meta_file.read_text())
        except Exception:
            continue
        f = str(meta.get('file') or meta_file.stem + '.jpg')
        src = (bank / f) if '/' in f else meta_file.with_name(f)
        if not src.exists():
            continue
        lic = meta.get('license', '')
        if not license_ok(lic):
            continue
        dst_name = Path(src_name) / f'{meta.get("lane", src_name)}_{src.stem}{src.suffix}'
        if src.suffix.lower() == '.svg':
            dst = OUT_IMG / dst_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                dst.write_text(src.read_text())
            v = (str(dst.relative_to(ROOT)), hashlib.sha256(dst.read_bytes()).hexdigest()[:16],
                 int(meta.get('w') or 0), int(meta.get('h') or 0))
        else:
            v = vendor(src, dst_name)
        if not v:
            continue
        rel, sha, w, h = v
        kw = tokens(f"{meta.get('desc','')} {meta.get('title','')} {meta.get('lane','')}")
        try:
            from harvest_met import QUERIES
            lane_qs = QUERIES.get(meta.get('lane', ''), [])
            title_toks = set(tokens(meta.get('title') or ''))
            kw = sorted(set(kw) | {t for q in lane_qs for t in tokens(q) if t in title_toks})
        except Exception:
            pass
        recs.append({
            'id': str(meta.get('id') or f'{src_name}:{src.stem}'), 'img': rel, 'source': src_name,
            'story': meta.get('lane') or src_name, 'desc': (meta.get('desc') or meta.get('title') or '').strip(),
            'creator': (meta.get('creator') or '').strip(),
            'license': norm_license(lic) if lic != 'CC0' else 'CC0', 'sha256': sha, 'w': w, 'h': h,
            'kw': kw,
        })


def main() -> None:
    recs: List[Dict] = []
    harvest_pb(BANKS / 'pb-imagebank', recs)
    harvest_story_table(BANKS / 'asp-imagebank', 'asp', BANKS / 'asp-imagebank' / 'medium', recs)
    harvest_story_table(BANKS / 'gsn-imagebank', 'gsn', BANKS / 'gsn-imagebank', recs)
    if (BANKS / 'asp-imagebank-new' / 'col' / 'large').exists():
        # Same story licensing as asp — colourized variants.
        harvest_story_table(BANKS / 'asp-imagebank', 'aspnew', BANKS / 'asp-imagebank-new' / 'col' / 'large', recs)
    harvest_bookdash(BANKS / 'bookdash-books', recs)
    if (BANKS / 'met-oa').exists():
        harvest_sidecars(BANKS / 'met-oa', 'met', recs)
    if (BANKS / 'maps').exists():
        harvest_sidecars(BANKS / 'maps', 'maps', recs)
    inv: Dict[str, List[str]] = {}
    for r in recs:
        for t in r['kw']:
            inv.setdefault(t, []).append(r['id'])
    OUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_INDEX.write_text(json.dumps({
        'version': 1, 'count': len(recs),
        'sources': sorted({r['source'] for r in recs}),
        'records': recs, 'index': {k: sorted(v) for k, v in sorted(inv.items())},
    }, ensure_ascii=False))
    total = sum(f.stat().st_size for f in OUT_IMG.rglob('*.jpg'))
    print(f'records={len(recs)} tokens={len(inv)} img_bytes={total >> 20}MB')
    from collections import Counter
    print(Counter(r['source'] for r in recs))


if __name__ == '__main__':
    main()
