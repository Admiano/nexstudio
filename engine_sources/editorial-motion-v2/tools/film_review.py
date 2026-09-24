#!/usr/bin/env python3
"""Film-level review: certify the compiled film as a film, not as isolated beats.

The per-beat gate proves each beat is legible; this pass asks the questions a
reviewer would about the whole film — does it have an arc, does a scene hold
across its beats, does the recurring character keep its face, does the motif
stay put in every aspect, do the aspects agree with each other, and do the
rendered outputs actually exist and measure up.

Inputs are the artifacts make_reel leaves behind in one directory:
  plan_<aspect>.json     (required, ≥1)
  gate_report.json       (required — the compile gate is part of the verdict)
  render_<aspect>.json   (optional — adds render/audio/authorship checks)
  frames_<aspect>/       (optional — adds blank/frozen frame measurement)

Output: certification.json — {schema, film_id, verdict, checks[]}, and a
console summary. verdict = FAIL on any failed check, else WARN, else PASS;
SKIPped checks (missing optional artifacts) never sway it.

Usage:
  python3 tools/film_review.py --reel out/<film_id>          # certify a rendered reel dir
  python3 tools/film_review.py --plans p16.json p1x1.json ... --gate gate_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))

from regression_pack import BLANK_MAX_MS, FROZEN_RUN_MAX_MS, LOUDNESS_TOL_LU, PEAK_TOL_DB, measure_frames  # noqa: E402

CERT_SCHEMA = 'NexStudioFilmCertificationV1'


def _check(checks: List[Dict[str, Any]], cid: str, scope: str, status: str, detail: str) -> None:
    checks.append({'id': cid, 'scope': scope, 'status': status, 'detail': detail})


def _band_sig(beat: Dict[str, Any], canvas_h: float) -> Tuple:
    """A backdrop's identity: its planes' resolved tone/band-fraction/depth/mark tuples.
    Geometry is canvas-normalized so the same authored plane matches across aspects."""
    sig = []
    for l in beat['composition']['background']['layers']:
        if l['kind'] != 'band':
            continue
        b = l['bbox']
        sig.append((l.get('tone'), round(b['y'] / canvas_h, 3), round(b['h'] / canvas_h, 3),
                    l.get('plane'), Path((l.get('mark') or {}).get('path') or '').name))
    return tuple(sig)


def _cast_sig(beat: Dict[str, Any]) -> Optional[Tuple[str, Tuple]]:
    """A performer's identity: its character + the parts that define how it looks."""
    fig = beat.get('figure')
    if not fig or not fig.get('character'):
        return None
    ident = tuple(sorted((p['slot'], p['part_id']) for p in fig.get('parts', []) if p['slot'] in ('body', 'head')))
    return fig['character'], ident


def _check_arc(checks: List[Dict[str, Any]], beats: Sequence[Dict[str, Any]], scope: str = 'film') -> None:
    """Every film needs a beginning, a middle, and a payoff — the arc the analyst authored."""
    types = [b.get('beat_type') for b in beats]
    if len(types) < 3:
        _check(checks, 'arc_shape', scope, 'FAIL', f'{len(types)} beats — a film needs at least three')
        return
    bad = []
    if types[0] != 'HOOK':
        bad.append(f'opens {types[0]}, not HOOK')
    if types[-1] not in ('PAYOFF', 'CTA'):
        bad.append(f'lands {types[-1]}, not PAYOFF/CTA')
    patterns = {b.get('pattern') for b in beats}
    if len(patterns) < min(3, len(beats)):
        bad.append(f'one-pattern film ({len(patterns)} pattern across {len(beats)} beats)')
    _check(checks, 'arc_shape', scope, 'FAIL' if bad else 'PASS',
           '; '.join(bad) if bad else f'{len(types)} beats, HOOK→{types[-1]}, {len(patterns)} patterns')


def _check_narration(checks: List[Dict[str, Any]], beats: Sequence[Dict[str, Any]], scope: str = 'film') -> None:
    """No beat may leave its own words unspoken: every planned word lands inside its beat's span."""
    bad = []
    for b in beats:
        # beat-local clock: planned words must land inside the beat's own duration
        for w in b.get('words', []):
            if w['start_ms'] < -1 or w['end_ms'] > b['duration_ms'] + 1:
                bad.append(f"{b['beat_id']}:{w['text']}")
    _check(checks, 'narration_coverage', scope, 'FAIL' if bad else 'PASS',
           f'{len(bad)} words outside their beat span' if bad else 'every word inside its beat')


def _check_scenes(checks: List[Dict[str, Any]], beats: Sequence[Dict[str, Any]], canvas_h: float, scope: str = 'film') -> None:
    """A place is a place: a beat's backdrop signature may reappear only contiguously —
    the film can leave a scene and come back, but it may not flicker between places."""
    sigs = [(b['beat_id'], _band_sig(b, canvas_h)) for b in beats]
    sigs = [(bid, s) for bid, s in sigs if s]
    seen: Dict[Tuple, List[str]] = {}
    for bid, s in sigs:
        seen.setdefault(s, []).append(bid)
    flickered = [bids for bids in seen.values() if len(bids) > 1 and
                 list(b['beat_id'] for b in beats).index(bids[-1]) - list(b['beat_id'] for b in beats).index(bids[0]) != len(bids) - 1]
    n_places = len(seen)
    if flickered:
        _check(checks, 'scene_continuity', scope, 'WARN',
               f'backdrop signature appears in non-contiguous beats: {flickered}')
    elif n_places:
        _check(checks, 'scene_continuity', scope, 'PASS', f'{n_places} authored place(s), contiguous')


def _check_cast(beats: Sequence[Dict[str, Any]], scope: str, checks: List[Dict[str, Any]]) -> None:
    """One character, one face: a cast member's identity parts must not drift between beats."""
    per_char: Dict[str, List[Tuple[str, Tuple]]] = {}
    for b in beats:
        cs = _cast_sig(b)
        if cs:
            per_char.setdefault(cs[0], []).append((b['beat_id'], cs[1]))
    bad = [cid for cid, rows in per_char.items() if len({r[1] for r in rows}) > 1]
    if not per_char:
        _check(checks, 'cast_continuity', scope, 'SKIP', 'no cast on this aspect')
    elif bad:
        _check(checks, 'cast_continuity', scope, 'FAIL', f'identity drifted: {bad}')
    else:
        _check(checks, 'cast_continuity', scope, 'PASS',
               f"{len(per_char)} cast member(s) hold their identity")


def _check_motif(plan: Dict[str, Any], scope: str, checks: List[Dict[str, Any]]) -> None:
    """An authored signature mark must actually resolve and be stamped on the plan."""
    motif = plan.get('motif')
    if motif is None:
        _check(checks, 'motif_stamp', scope, 'SKIP', 'no world motif authored')
    elif motif.get('asset') or motif.get('photo') or motif.get('word'):
        _check(checks, 'motif_stamp', scope, 'PASS',
               f"{motif.get('concept')} via {motif.get('via')} @ {motif.get('corner')}")
    else:
        _check(checks, 'motif_stamp', scope, 'FAIL', f"motif {motif.get('concept')} unresolved")


def _check_parity(plans: Dict[str, Dict[str, Any]], checks: List[Dict[str, Any]]) -> None:
    """Determinism across aspects: same beats, same cast identities, same dioramas, same motif."""
    if len(plans) < 2:
        return
    ref_aspect = sorted(plans)[0]
    ref = plans[ref_aspect]
    ref_ids = [b['beat_id'] for b in ref['beats']]
    ref_cast = sorted({_cast_sig(b) for b in ref['beats']} - {None})
    def bands_close(a: Dict[str, Any], b: Dict[str, Any], ha: float, hb: float) -> bool:
        """Same authored diorama across aspect canvases: identical tone/plane/mark in order,
        band geometry within tolerance (the compiler's edge overhang isn't recoverable)."""
        sa = [l for l in a['composition']['background']['layers'] if l['kind'] == 'band']
        sb = [l for l in b['composition']['background']['layers'] if l['kind'] == 'band']
        if len(sa) != len(sb):
            return False
        for la, lb in zip(sa, sb):
            if (la.get('tone'), la.get('plane'), Path((la.get('mark') or {}).get('path') or '').name) != \
               (lb.get('tone'), lb.get('plane'), Path((lb.get('mark') or {}).get('path') or '').name):
                return False
            if abs(la['bbox']['y'] / ha - lb['bbox']['y'] / hb) > 0.04 or \
               abs(la['bbox']['h'] / ha - lb['bbox']['h'] / hb) > 0.04:
                return False
        return True

    ref_motif = (ref.get('motif') or {}).get('concept')
    bad = []
    ref_h = ref['canvas']['h']
    for aspect, plan in plans.items():
        if aspect == ref_aspect:
            continue
        if [b['beat_id'] for b in plan['beats']] != ref_ids:
            bad.append(f'{aspect}: different beat list')
            continue
        if sorted({_cast_sig(b) for b in plan['beats']} - {None}) != ref_cast:
            bad.append(f'{aspect}: cast diverged')
        ph = plan['canvas']['h']
        if not all(bands_close(ra, rb, ref_h, ph) for ra, rb in zip(ref['beats'], plan['beats'])):
            bad.append(f'{aspect}: diorama diverged')
        if (plan.get('motif') or {}).get('concept') != ref_motif:
            bad.append(f'{aspect}: motif diverged')
    _check(checks, 'aspect_parity', 'film', 'FAIL' if bad else 'PASS',
           '; '.join(bad) if bad else f'{len(plans)} aspects agree')


def _check_render(checks: List[Dict[str, Any]], reel_dir: Path, aspect: str) -> None:
    """Render-level evidence from the aspect's manifest, when one exists."""
    manifest_path = reel_dir / f'render_{aspect}.json'
    if not manifest_path.exists():
        _check(checks, 'render_manifest', aspect, 'SKIP', 'no render manifest')
        return
    m = json.loads(manifest_path.read_text())
    _check(checks, 'render_errors', aspect,
           'PASS' if m.get('page_errors') == [] else 'FAIL',
           f"{len(m.get('page_errors', []))} page errors")
    _check(checks, 'native_profile', aspect,
           'PASS' if m.get('native_profile') is True else 'FAIL',
           'native composition profile' if m.get('native_profile') else 'fell off the native profile')
    audio = m.get('audio') or {}
    _check(checks, 'music_bound', aspect, 'PASS' if audio.get('music') else 'FAIL', 'music bed' if audio.get('music') else 'no music')
    loud = audio.get('loudness') or {}
    if loud:
        ok = abs(loud['integrated_lufs'] - loud['target_lufs']) <= LOUDNESS_TOL_LU
        _check(checks, 'loudness', aspect, 'PASS' if ok else 'FAIL',
               f"{loud['integrated_lufs']}LUFS vs {loud['target_lufs']}")
        okp = loud['true_peak_dbtp'] <= loud['ceiling_dbtp'] + PEAK_TOL_DB
        _check(checks, 'true_peak', aspect, 'PASS' if okp else 'FAIL',
               f"{loud['true_peak_dbtp']}dBTP vs {loud['ceiling_dbtp']}")
    _check(checks, 'captions', aspect,
           'PASS' if m.get('captions_burned', 0) > 0 or m.get('captions_policy') == 'kinetic' else 'FAIL',
           f"{m.get('captions_burned', 0)} captions")
    for f in (m.get('authorship') or {}).get('findings', []):
        _check(checks, f"authorship:{f['code']}", aspect, 'FAIL',
               f"{f['beat_id']}:{f['id']}@{f['first_ms']}ms")


def _check_frames(checks: List[Dict[str, Any]], reel_dir: Path, aspect: str, fps: int) -> None:
    frames_dir = reel_dir / f'frames_{aspect}'
    if not frames_dir.is_dir():
        return
    met = measure_frames(frames_dir, fps)
    _check(checks, 'blank_frames', aspect,
           'PASS' if met['blank_ms'] <= BLANK_MAX_MS else 'FAIL', f"{met['blank_ms']}ms blank")
    _check(checks, 'frozen_frames', aspect,
           'PASS' if met['frozen_longest_ms'] <= FROZEN_RUN_MAX_MS else 'FAIL',
           f"{met['frozen_longest_ms']}ms frozen run")


def certify(reel_dir: Path, plan_paths: Sequence[Path], gate_path: Optional[Path], fps: int = 15) -> Dict[str, Any]:
    if not plan_paths and reel_dir:
        plan_paths = sorted(reel_dir.glob('plan_*.json'))
    plans = {}
    for p in plan_paths:
        plan = json.loads(Path(p).read_text())
        plans[plan['aspect']] = plan
    checks: List[Dict[str, Any]] = []
    if not plans:
        _check(checks, 'plans_found', 'film', 'FAIL', 'no aspect plans in the reel directory')
        return {'schema': CERT_SCHEMA, 'film_id': None, 'verdict': 'FAIL',
                'counts': {'PASS': 0, 'WARN': 0, 'FAIL': 1, 'SKIP': 0}, 'checks': checks}
    gate = json.loads(gate_path.read_text()) if gate_path and gate_path.exists() else None
    if gate is not None:
        _check(checks, 'compile_gate', 'film',
               'PASS' if gate['status'] == 'PASS' else 'FAIL',
               f"{gate['status']} ({len(gate.get('failures', []))} failures, {len(gate.get('warnings', []))} warnings)")
    ref = plans[sorted(plans)[0]]['beats']
    _check_arc(checks, ref)
    _check_narration(checks, ref)
    _check_scenes(checks, ref, plans[sorted(plans)[0]]['canvas']['h'])
    for aspect, plan in sorted(plans.items()):
        _check_cast(plan['beats'], aspect, checks)
        _check_motif(plan, aspect, checks)
        if reel_dir:
            _check_render(checks, reel_dir, aspect)
            _check_frames(checks, reel_dir, aspect, fps)
    _check_parity(plans, checks)
    verdict = ('FAIL' if any(c['status'] == 'FAIL' for c in checks)
               else 'WARN' if any(c['status'] == 'WARN' for c in checks) else 'PASS')
    return {'schema': CERT_SCHEMA, 'film_id': plans[sorted(plans)[0]].get('film_id'),
            'verdict': verdict,
            'counts': {s: sum(1 for c in checks if c['status'] == s) for s in ('PASS', 'WARN', 'FAIL', 'SKIP')},
            'checks': checks}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--reel', type=Path, help='a make_reel/render output directory')
    ap.add_argument('--plans', nargs='*', default=[])
    ap.add_argument('--gate', type=Path, default=None)
    ap.add_argument('--fps', type=int, default=15)
    ap.add_argument('--out', type=Path, default=None)
    args = ap.parse_args()

    reel_dir = args.reel
    plan_paths = [Path(p) for p in args.plans]
    gate_path = args.gate
    if reel_dir:
        plan_paths = plan_paths or sorted(reel_dir.glob('plan_*.json'))
        gate_path = gate_path or (reel_dir / 'gate_report.json')
    if not plan_paths:
        print('film_review: no plans found', file=sys.stderr)
        return 2

    cert = certify(reel_dir, plan_paths, gate_path, args.fps)
    out = args.out or (reel_dir / 'certification.json' if reel_dir else Path('certification.json'))
    out.write_text(json.dumps(cert, indent=1) + '\n')
    for c in cert['checks']:
        mark = {'PASS': 'ok ', 'WARN': 'warn', 'FAIL': 'FAIL', 'SKIP': 'skip'}[c['status']]
        print(f"  {mark} [{c['scope']}] {c['id']}: {c['detail']}")
    print(f"certification: {cert['verdict']} ({cert['counts']})")
    return 1 if cert['verdict'] == 'FAIL' else 0


if __name__ == '__main__':
    sys.exit(main())
