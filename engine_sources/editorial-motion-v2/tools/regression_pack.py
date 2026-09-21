#!/usr/bin/env python3
"""Regression pack: render every fixture film in every aspect and gate the result.

For each fixture x aspect the pack compiles the plan, renders frames + mp4 via
tools/render_reel.js, then measures the rendered frames and applies the film
gates:

  gate_report.status == PASS            (compiler legibility/voice gates)
  blank_ms      <= BLANK_MAX_MS         (frames with near-zero content std)
  frozen_ms     <= FROZEN_RUN_MAX_MS    (longest run of pixel-identical frames)
  manifest.page_errors == 0
  manifest.audio.music present          (music bed bound)
  manifest.captions_burned > 0            (or captions_policy == kinetic: words live on canvas)
  manifest.native_profile == true
  manifest.authorship.findings == []       (no generated-look tells: empty chassis, icon under-fill /
                                            overflow, orphan connectors, static holds)
  manifest.audio.loudness               (measured master: integrated within LOUDNESS_TOL_LU of target,
                                            true peak under the ceiling — no clipping)

Usage:
  python3 tools/regression_pack.py                    # all fixtures, all aspects
  python3 tools/regression_pack.py --fixture honey-nut --aspects 16x9
  python3 tools/regression_pack.py --fps 15 --out out/regression --skip-render
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODE = str(Path.home() / '.nvm/versions/node/v24.19.0/bin/node')

BLANK_MAX_MS = 400          # grain/dot-grid floor keeps "rest" frames alive; blank = dead pixels
BLANK_STD = 1.5
FROZEN_RUN_MAX_MS = 200
FROZEN_DIFF = 0.1
LOUDNESS_TOL_LU = 1.5
PEAK_TOL_DB = 0.3


def fixtures(root: Path):
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / 'treatment.json').exists():
            yield d.name, d / 'treatment.json'
    for f in sorted(root.glob('*.treatment.json')):
        yield f.name[: -len('.treatment.json')], f


def compile_fixture(treatment: Path, outdir: Path):
    p = subprocess.run(
        [sys.executable, '-m', 'editorial_plan_compiler', str(treatment), str(outdir)],
        cwd=ROOT / 'compiler', capture_output=True, text=True)
    if p.returncode not in (0, 3):
        raise RuntimeError(p.stdout + p.stderr)
    return json.load(open(outdir / 'gate_report.json'))


def render(plan: Path, outdir: Path, fps: int):
    p = subprocess.run([NODE, str(ROOT / 'tools/render_reel.js'), str(plan), str(outdir), '--fps', str(fps)],
                       cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-2000:] or p.stdout[-2000:])
    return json.load(open(outdir / f'render_{plan.stem.split("_")[-1]}.json'))


def measure_frames(frames_dir: Path, fps: int):
    from PIL import Image
    import numpy as np

    files = sorted(frames_dir.glob('f*.png'))
    prev, stds, diffs = None, [], []
    for f in files:
        a = np.asarray(Image.open(f).convert('L').resize((160, 90)), dtype=np.float32)
        stds.append(float(a.std()))
        diffs.append(float(np.abs(a - prev).mean()) if prev is not None else 1.0)
        prev = a
    frame_ms = 1000 / fps

    def longest_run(flags):
        best = cur = 0
        for v in flags:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        return best

    blank = [s < BLANK_STD for s in stds]
    frozen = [d < FROZEN_DIFF for d in diffs]
    return {
        'frames': len(files),
        'blank_ms': round(sum(blank) * frame_ms),
        'blank_longest_ms': round(longest_run(blank) * frame_ms),
        'frozen_longest_ms': round(longest_run(frozen) * frame_ms),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--fixture', action='append')
    ap.add_argument('--aspects', default='16x9,1x1,9x16')
    ap.add_argument('--fps', type=int, default=15)
    ap.add_argument('--out', default=str(ROOT / 'out' / 'regression'))
    ap.add_argument('--skip-render', action='store_true')
    args = ap.parse_args()

    # resolve() because compile_fixture hands outdir to a subprocess with a different cwd —
    # a relative --out would split the compile tree from the render tree.
    root_out = Path(args.out).resolve()
    root_out.mkdir(parents=True, exist_ok=True)
    aspects = args.aspects.split(',')
    wanted = set(args.fixture or [])
    report = {'schema': 'EditorialRegressionPackV1', 'fps': args.fps, 'films': []}
    failures = 0

    for name, treatment in fixtures(ROOT / 'fixtures'):
        if wanted and name not in wanted:
            continue
        film_out = root_out / name
        gate = compile_fixture(treatment, film_out)
        film = {'film': name, 'aspects': {}, 'gate': gate['status']}
        for aspect in aspects:
            plan = film_out / f'plan_{aspect}.json'
            manifest_path = film_out / f'render_{aspect}.json'
            manifest = None
            if not args.skip_render or not manifest_path.exists():
                render(plan, film_out, args.fps)
            manifest = json.load(open(manifest_path))
            metrics = measure_frames(film_out / f'frames_{aspect}', args.fps)
            checks = {
                'gate_pass': gate['status'] == 'PASS',
                'blank_ms_ok': metrics['blank_ms'] <= BLANK_MAX_MS,
                'frozen_ok': metrics['frozen_longest_ms'] <= FROZEN_RUN_MAX_MS,
                'no_page_errors': manifest.get('page_errors') == [],
                'music_bound': bool((manifest.get('audio') or {}).get('music')),
                'captions': manifest.get('captions_burned', 0) > 0 or manifest.get('captions_policy') == 'kinetic',
                'native_profile': manifest.get('native_profile') is True,
            }
            loud = (manifest.get('audio') or {}).get('loudness') or {}
            checks['loudness_on_target'] = bool(loud) and abs(loud['integrated_lufs'] - loud['target_lufs']) <= LOUDNESS_TOL_LU
            checks['no_clipping'] = bool(loud) and loud['true_peak_dbtp'] <= loud['ceiling_dbtp'] + PEAK_TOL_DB
            metrics['loudness'] = loud
            metrics['groove'] = (manifest.get('audio') or {}).get('groove')
            authorship = manifest.get('authorship') or {}
            # Each tell is its own check so the report names the rule that tripped, not a blanket flag.
            if not authorship:
                checks['authorship_evidence'] = False
            for code in authorship.get('codes', []):
                checks[f'authorship:{code}'] = False
            metrics['authorship_findings'] = [
                f"{f['code']}:{f['beat_id']}:{f['id']}@{f['first_ms']}ms" for f in authorship.get('findings', [])]
            metrics['static_hold_longest_ms'] = authorship.get('longest_static_hold_ms')
            film['aspects'][aspect] = {'checks': checks, 'metrics': metrics, 'mp4': manifest['mp4'],
                                       'mp4_sha256': manifest['mp4_sha256']}
            failures += sum(1 for ok in checks.values() if not ok)
        report['films'].append(film)

    report['failures'] = failures
    (root_out / 'report.json').write_text(json.dumps(report, indent=2))
    for film in report['films']:
        for aspect, r in film['aspects'].items():
            bad = [k for k, ok in r['checks'].items() if not ok]
            m = r['metrics']
            lo = m.get('loudness') or {}
            gr = m.get('groove') or {}
            print(f"{film['film']:>18} {aspect}  blank={m['blank_ms']}ms frozen={m['frozen_longest_ms']}ms"
                  f" hold={m.get('static_hold_longest_ms')}ms  {lo.get('integrated_lufs')}LUFS tp={lo.get('true_peak_dbtp')}"
                  f" grid={gr.get('on_grid_ratio')}  {'PASS' if not bad else 'FAIL ' + ','.join(bad)}")
            for f in m.get('authorship_findings', []):
                print(f"{'':>18}   {f}")
    print(f"failures: {failures}")
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
