"""python -m editorial_plan_compiler <treatment.json> <out_dir>

Writes plan_<aspect>.json per aspect and gate_report.json. Exit code 0 on
PASS, 3 on gate FAIL, 4 when the treatment is outside the bounded vocabulary
(the gate report then carries the coded replan reason for P8).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .compiler import compile_film, write_outputs
from .contracts import TreatmentError


def main(argv: list) -> int:
    if len(argv) < 3:
        sys.stderr.write(__doc__)
        return 2
    treatment_path = Path(argv[1]).resolve()
    out_dir = Path(argv[2]).resolve()
    treatment = json.loads(treatment_path.read_text())
    try:
        result = compile_film(treatment, out_dir / 'work', base_dir=treatment_path.parent)
    except TreatmentError as exc:
        out_dir.mkdir(parents=True, exist_ok=True)
        report = {'status': 'REPLAN', 'code': exc.code, 'detail': exc.detail, 'beat_id': exc.beat_id, 'escalation_scope': 'UPSTREAM_TREATMENT'}
        (out_dir / 'gate_report.json').write_text(json.dumps(report, indent=1))
        print(json.dumps(report))
        return 4
    written = write_outputs(result, out_dir)
    print(json.dumps({'gate': result['gate']['status'], 'failures': result['gate']['failures'][:12], 'warnings': len(result['gate']['warnings']),
                      'duration_ms': result['gate']['duration_ms'], 'written': written}, indent=1))
    return 0 if result['gate']['status'] == 'PASS' else 3


if __name__ == '__main__':
    sys.exit(main(sys.argv))
