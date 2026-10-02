#!/usr/bin/env python3
"""render_queue — batch render runner.

Consumes a directory of plans and renders each through the diagram
pipeline (the other types are planned). A plan file may sit next to its
audio companions:
    my_plan.json        plan (required)
    my_plan_vo.wav      voiceover for that plan (optional)
    my_plan_words.json  word timings           (optional)

Usage:
    python3 render_queue.py queue_dir/ [--ratio 16:9] [--accent #0052FF]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def run_queue(queue_dir: Path, ratio: str = '16:9',
              accent: str | None = None) -> dict:
    import pipeline_v3_narration_timed as p3
    import pipeline_diagram_timed as pd

    p3.load_execution_body(None)
    results = []
    plans = sorted(queue_dir.glob('*.json'))
    plans = [p for p in plans
             if not p.stem.endswith(('_words', '_receipt', '_metrics'))]
    for pf in plans:
        plan = p3.load_plan(pf)
        name = plan.get('production_id') or pf.stem
        out_dir = queue_dir / pf.stem
        vo = pf.with_name(pf.stem + '_vo.wav')
        t0 = time.time()
        try:
            receipt = pd.render_production(
                plan, out_dir, ratio=ratio,
                voiceover=vo if vo.exists() else None,
                accent=accent)
            results.append({'plan': pf.name, 'ok': True,
                            'out': str(out_dir),
                            'duration_s': receipt['duration_seconds'],
                            'elapsed_s': round(time.time() - t0, 1)})
        except Exception as e:
            results.append({'plan': pf.name, 'ok': False,
                            'error': f'{type(e).__name__}: {e}'})
    report = {'schema': 'NexMindRenderQueueV1', 'queue': str(queue_dir),
              'ratio': ratio, 'results': results}
    (queue_dir / 'QUEUE_REPORT.json').write_text(
        json.dumps(report, indent=2) + '\n')
    return report


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('queue_dir')
    ap.add_argument('--ratio', default='16:9')
    ap.add_argument('--accent', default=None)
    args = ap.parse_args(argv)
    report = run_queue(Path(args.queue_dir), ratio=args.ratio,
                       accent=args.accent)
    ok = sum(1 for r in report['results'] if r['ok'])
    print(f"{ok}/{len(report['results'])} rendered -> "
          f"{Path(args.queue_dir) / 'QUEUE_REPORT.json'}")
    return 0 if ok == len(report['results']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
