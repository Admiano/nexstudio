"""Bank art: open-licensed painted illustrations harvested by tools/bank_index.py.

The concept ladder's painted-art rung — a real picture-book plate (CC BY / PD)
outranks a photograph for the paperbook dialect, and its credit follows it onto
the page so attribution ships in the film.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

INDEX_PATH = Path(__file__).resolve().parents[2] / 'assets' / 'bank' / 'index.json'
STOP = set('''a an and are as at be but by for from had has have her his i in is it its of on or
she so that the their they to was we were with you your he not no my me do does did will would
can could this those these them then than too very just over under again once each all any both
few more most other some such only own same off about into out up down
'''.split())


def _tokens(text: str) -> List[str]:
    out = []
    for t in re.findall(r'[a-zA-Z][a-zA-Z\-\']+', (text or '').lower()):
        t = t.strip("-'")
        if len(t) < 3 or t in STOP:
            continue
        for form in {t, re.sub(r"('s|s'|s|es|ing|ed)$", '', t) if len(t) > 4 else t}:
            if form and form not in STOP and len(form) >= 3:
                out.append(form)
    return sorted(set(out))


class BankArt:
    """Concept → painted plate lookup over the vendored bank. Deterministic: ties break on id."""

    def __init__(self, index_path: Path = INDEX_PATH):
        self.records: Dict[str, Dict[str, Any]] = {}
        self.index: Dict[str, List[str]] = {}
        try:
            doc = json.loads(index_path.read_text())
            self.records = {r['id']: r for r in doc['records']}
            self.index = {k: list(v) for k, v in doc['index'].items()}
        except Exception:
            pass

    @property
    def available(self) -> bool:
        return bool(self.records)

    def find(self, concept: str) -> Optional[Dict[str, Any]]:
        if not self.records:
            return None
        qts = _tokens(concept)
        if not qts:
            return None
        cand = set()
        for t in qts:
            cand.update(self.index.get(t, []))
        if not cand:
            return None
        qset = set(qts)
        best: List[tuple] = []
        for cid in cand:
            r = self.records[cid]
            kws = set(r['kw'])
            inter = qset & kws
            # Coverage of the query, how tight the image's own keyword set is, and a
            # bonus when the whole phrase sits inside the description verbatim.
            cover = len(inter) / len(qset)
            tight = len(inter) / max(1, len(kws))
            phrase = 0.28 if concept.lower() in (r.get('desc') or '').lower() else 0.0
            score = cover * 0.62 + tight * 0.22 + phrase
            best.append((score, cid))
        best.sort(key=lambda x: (-x[0], x[1]))
        if not best or best[0][0] < 0.34:
            return None
        return self.records[best[0][1]]

    def as_plan(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        path = str(Path(__file__).resolve().parents[2] / rec['img'])
        credit = f"{rec['creator']} — “{rec['story']}” ({rec['license']})" if rec.get('creator') else f"{rec['source']} ({rec['license']})"
        return {
            'path': path, 'sha256': rec['sha256'], 'source_size': {'w': rec['w'], 'h': rec['h']},
            'rights': 'BANK', 'license': rec['license'], 'license_url': '', 'source': f"bank:{rec['source']}",
            'source_id': rec['id'], 'landing_url': '', 'title': rec['desc'] or rec['story'], 'creator': rec.get('creator', ''),
            'credit': credit,
        }
