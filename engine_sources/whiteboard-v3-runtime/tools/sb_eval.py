"""Held-out storyboard evaluation: author plans for a directory of unseen
scripts and score the system (not any one reel) on context coverage.

    python3 tools/sb_eval.py fixtures/eval_scripts [--json out.json]

Per cast member: is an occupation dressed for its job, and does a doer
engage its object. Per drawing: exact kit art, curated fallback, library
fallback, or generic. No rendering, so the whole set runs in seconds."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plan_author as pa  # noqa: E402
import sb_cast  # noqa: E402

_WORKER = {'worker.n.01', 'professional.n.01', 'skilled_worker.n.01',
           'employee.n.01', 'expert.n.01', 'official.n.01', 'serviceman.n.01',
           'leader.n.01', 'scientist.n.01', 'performer.n.01',
           'athlete.n.01', 'craftsman.n.01'}


def _occupation(label: str) -> bool:
    """WordNet says this person noun names a job."""
    if pa._wn is None:
        return False
    for s in pa._wn.synsets(pa._lemma(label.split()[-1]), 'n')[:2]:
        if any(h.name() in _WORKER for p in s.hypernym_paths() for h in p):
            return True
    return False


def _does(role: dict) -> bool:
    """The narration has this person acting on something right after it."""
    sent = str(role.get('narration') or '')
    m = re.search(r'\b' + re.escape(role['label'].split()[-1]) + r"s?\b"
                  r"\s+(\w+)", sent, re.I)
    if not m or pa._wn is None:
        return False
    v = m.group(1).lower()
    return bool(pa._wn.synsets(v, 'v')) and v not in {
        'feels', 'feel', 'is', 'are', 'was', 'were', 'has', 'have', 'smiles'}


def _norm(s: str) -> str:
    return re.sub(r'[^a-z]', '', s.lower()).rstrip('s')


def _literal(art_name: str, label: str) -> bool:
    """A library drawing named for the word itself ('contract' for
    contract): a literal depiction, though not authored kit art."""
    return _norm(art_name) in {_norm(label), _norm(label.split()[-1])}


def evaluate(scripts: list[Path]) -> dict:
    import pipeline_v3_narration_timed as p3
    p3.load_execution_body(None)
    import v3_board_renderer as v3r
    rows, tot = [], {'cast': 0, 'jobs': 0, 'dressed': 0, 'doers': 0,
                     'engaged': 0, 'art': 0, 'exact': 0, 'literal': 0,
                     'curated': 0,
                     'library': 0, 'loose': 0, 'generic': 0}
    for sp in scripts:
        plan = pa.build_storyboard(sp.read_text(encoding='utf-8'))
        for b in plan['beats']:
            sc = b['scene']
            for r in [sc['heroRole']] + list(sc.get('supportingRoles', [])):
                rec = {'script': sp.stem, 'beat': b['beat_id'],
                       'label': r['label']}
                if r['icon'] == 'person':
                    tot['cast'] += 1
                    fit = sb_cast.outfit_for(r.get('outfit'), r['label'],
                                             r.get('concept'))
                    rec['outfit'] = fit
                    if _occupation(r['label']):
                        tot['jobs'] += 1
                        tot['dressed'] += bool(fit)
                        rec['job'] = True
                    if _does(dict(r, narration=b['narration'])):
                        tot['doers'] += 1
                        ok = r.get('action') in sb_cast.ENGAGED and bool(
                            r.get('target') is not None
                            or r.get('action') == 'hold')
                        tot['engaged'] += ok
                        rec['doer'], rec['action'] = True, r.get('action')
                        rec['target'] = r.get('target')
                else:
                    tot['art'] += 1
                    ic = v3r._icon_for(str(r['icon']))
                    if ic in (None, 'card', 'tile') or v3r._is_emblem(ic):
                        how = 'generic'
                    elif ic == v3r.kit_exact(str(r['icon']).lower()):
                        how = 'exact'
                    elif isinstance(ic, tuple) and (
                            ic[0] == 'custom'
                            or str(ic[1]).startswith('kit:')):
                        how = 'curated'
                    elif isinstance(ic, tuple) and _literal(
                            str(ic[-1]), r['label']):
                        how = 'literal'
                    elif v3r.art_related(str(r['icon']), ic):
                        how = 'library'
                    else:
                        how = 'loose'
                    tot[how] += 1
                    rec.update(art=str(ic), via=how)
                rows.append(rec)

    def pct(a, b):
        return round(100.0 * tot[a] / tot[b], 1) if tot[b] else 100.0
    score = {'dressed_jobs_%': pct('dressed', 'jobs'),
             'engaged_doers_%': pct('engaged', 'doers'),
             'exact_art_%': pct('exact', 'art'),
             'exact_or_literal_art_%': round(
                 pct('exact', 'art') + pct('literal', 'art'), 1),
             'non_generic_art_%': round(100 - pct('generic', 'art'), 1),
             'meaning_related_art_%': round(
                 100 - pct('generic', 'art') - pct('loose', 'art'), 1)}
    return {'scripts': len(scripts), 'totals': tot, 'score': score,
            'rows': rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('dir')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    res = evaluate(sorted(Path(a.dir).glob('*.txt')))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({'scripts': res['scripts'], **res['score'],
                      **res['totals']}, indent=1))
    for r in res['rows']:
        miss = (r.get('job') and not r.get('outfit')) or (
            r.get('doer') and not r.get('target') and r.get('action') != 'hold'
        ) or r.get('via') in ('generic', 'loose')
        if miss:
            print('  MISS', r['script'], r['beat'], r['label'],
                  {k: r[k] for k in ('action', 'target', 'art', 'via')
                   if k in r})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
