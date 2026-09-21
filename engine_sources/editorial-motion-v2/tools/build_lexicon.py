#!/usr/bin/env python3
"""Materialise the noun lexicon the asset finder walks (synonyms + hypernym chains).

Source: Princeton WordNet 3.1 database files (data.noun / index.noun / cntlist.rev), licence
"WordNet 3.0 License" (BSD-style, redistribution permitted with notice). Only nouns are kept
and only what the finder needs: per lemma the sense-ordered synsets, per synset its lemmas,
hypernyms and lexicographer file (the domain: artifact, food, state...), and the SemCor tag
count that ranks a lemma's everyday senses first.

    python3 tools/build_lexicon.py /path/to/WordNet-3.1/dict

Writes assets/community/lexicon/noun-lexicon.json.gz (+ LICENSE + info.json with the source
tarball sha256). The compiler reads only that file; the WordNet tree is never shipped.
"""
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'assets' / 'community' / 'lexicon'

WORDNET_LICENSE = """WordNet 3.1 Copyright 2011 by Princeton University. All rights reserved.

THIS SOFTWARE AND DATABASE IS PROVIDED "AS IS" AND PRINCETON UNIVERSITY MAKES NO REPRESENTATIONS OR
WARRANTIES, EXPRESS OR IMPLIED. BY WAY OF EXAMPLE, BUT NOT LIMITATION, PRINCETON UNIVERSITY MAKES NO
REPRESENTATIONS OR WARRANTIES OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE
OF THE LICENSED SOFTWARE, DATABASE OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD PARTY PATENTS,
COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.

The name of Princeton University or Princeton may not be used in advertising or publicity pertaining
to distribution of the software and/or database. Title to copyright in this software, database and
any associated documentation shall at all times remain with Princeton University and LICENSEE agrees
to preserve same.
"""


def _parse_data_noun(path: Path):
    synsets = {}
    with path.open(encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if line.startswith('  '):
                continue
            head, _, gloss = line.partition('|')
            parts = head.split()
            off = parts[0]
            lex_file = int(parts[1])
            w_cnt = int(parts[3], 16)
            lemmas = [parts[4 + 2 * i].lower() for i in range(w_cnt)]
            i = 4 + 2 * w_cnt
            p_cnt = int(parts[i])
            i += 1
            hyper = []
            for _ in range(p_cnt):
                sym, target, pos = parts[i], parts[i + 1], parts[i + 2]
                if sym in ('@', '@i') and pos == 'n':
                    hyper.append(target)
                i += 4
            synsets[off] = {'l': lemmas, 'h': hyper, 'f': lex_file}
    return synsets


def _parse_index_noun(path: Path):
    index = {}
    with path.open(encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if line.startswith('  '):
                continue
            parts = line.split()
            lemma = parts[0].lower()
            synset_cnt = int(parts[2])
            p_cnt = int(parts[3])
            offsets = parts[4 + p_cnt + 2: 4 + p_cnt + 2 + synset_cnt]
            index[lemma] = offsets
    return index


def _parse_cntlist(path: Path):
    """cntlist.rev: sense_key sense_number tag_cnt — everyday senses have tags, rare ones do not.
    Returns per-lemma tag counts by sense number (1-based position in index.noun order)."""
    counts = defaultdict(dict)
    if not path.exists():
        return counts
    with path.open(encoding='utf-8', errors='replace') as fh:
        for line in fh:
            key, num, cnt = line.split()
            lemma, _, rest = key.partition('%')
            if rest.startswith('1:'):
                counts[lemma.lower()][int(num)] = counts[lemma.lower()].get(int(num), 0) + int(cnt)
    return counts


def build(dict_dir: Path, tarball: Path = None) -> Path:
    synsets = _parse_data_noun(dict_dir / 'data.noun')
    index = _parse_index_noun(dict_dir / 'index.noun')
    counts = _parse_cntlist(dict_dir / 'cntlist.rev')
    doc = {
        'schema': 'NexStudioNounLexiconV1',
        'source': 'Princeton WordNet 3.1 (nouns only)',
        'license': 'WordNet 3.0 License',
        'synsets': synsets,
        'index': index,
        'tagged': {k: [v.get(i + 1, 0) for i in range(len(index[k]))] for k, v in counts.items() if k in index},
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / 'noun-lexicon.json.gz'
    with gzip.open(out, 'wt', encoding='utf-8', compresslevel=9) as fh:
        json.dump(doc, fh, separators=(',', ':'))
    (OUT_DIR / 'LICENSE').write_text(WORDNET_LICENSE)
    info = {
        'schema': 'NexStudioLexiconInfoV1',
        'source': {'pack': 'WordNet 3.1', 'url': 'https://wordnet.princeton.edu/', 'files': ['data.noun', 'index.noun', 'cntlist.rev']},
        'license': 'WordNet 3.0 License',
        'synsets': len(synsets),
        'lemmas': len(index),
        'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
    }
    if tarball and tarball.exists():
        info['source']['tarball_sha256'] = hashlib.sha256(tarball.read_bytes()).hexdigest()
    (OUT_DIR / 'info.json').write_text(json.dumps(info, indent=2) + '\n')
    return out


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = Path(sys.argv[1])
    tb = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    p = build(d, tb)
    print(p, f'{p.stat().st_size / 1e6:.1f} MB')
