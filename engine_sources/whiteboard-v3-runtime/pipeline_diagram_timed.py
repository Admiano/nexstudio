"""Diagram type — narration-timed cumulative annotated-canvas renderer.

Same contract as the whiteboard/kinetic types: a narration-timed plan in,
frames keyed to word timings when given, marker-scratch SFX per actual
pen-down interval, mp4 + QA sheet + metrics + execution receipt out.

    python pipeline_diagram_timed.py plan.json --out-dir out --ratio 16:9 \
        [--voiceover vo.mp3 --word-timings words.json] [--accent #RRGGBB]

Plan: `diagram` block {title, hero, summary}; each beat carries a
`diagram` spec {stage, region, elements[]}. See diagram_renderer.py.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

import pipeline_v3_narration_timed as p3


def _dr():
    # diagram_renderer → v3_board_renderer → whiteboard_pil_adapter resolves
    # only after load_execution_body() has put the runtime dir on sys.path.
    global dr
    if 'dr' not in globals():
        import diagram_renderer
        dr = diagram_renderer
    return dr

VERSION = 'diagram-1.0.0'
RECEIPT_SCHEMA = 'NexMindWhiteboardV3ReconstructedExecutionReceiptV1'


def render_frames(plan: dict, ratio: str, fps: int,
                  ) -> Iterator[tuple[float, object]]:
    """Yield (t_seconds, PIL RGB frame) across the narration timeline."""
    dr = _dr()
    elements, meta = dr.build_elements(plan, ratio)
    beats = plan.get('beats') or []
    if not beats:
        return
    end = (float(beats[-1].get('start_seconds') or 0)
           + float(beats[-1].get('duration_seconds') or 4.0) + 1.0)
    step = 1.0 / fps
    t = 0.0
    while t < end:
        yield t, dr.render_diagram_frame(plan, elements, meta['atlas'],
                                         ratio, t)
        t += step


def _sync_drawplan(plan: dict, meta: dict) -> None:
    """Write per-beat drawPlan entries (element windows + pen spans) into
    sceneSpecs so the sound layer schedules scratches off the same clock
    the renderer uses — including word-aligned beat start times."""
    scenes = plan.get('sceneSpecs') or []
    beats = plan.get('beats') or []
    for i, sc in enumerate(scenes):
        wb = sc.setdefault('whiteboardRuntime', {})
        wb['drawPlan'] = meta['plans'][i] if i < len(meta['plans']) else []
        wb['sceneDuration'] = float(beats[i].get('duration_seconds') or 4.0) \
            if i < len(beats) else 1.0
        wb.setdefault('seed', i + 7)


def render_production(plan: dict, out_dir: Path, ratio: str = '16:9',
                      fps: int = 24,
                      voiceover: Path | None = None,
                      keep_frames: bool = False,
                      accent: str | None = None) -> dict:
    wbc, wbp, snd, v3r = p3.load_execution_body(None)
    if ratio not in wbp.RATIO_SIZES:
        raise p3._err('DIAGRAM_RATIO_UNSUPPORTED', ratio)
    beats = plan.get('beats') or []
    if not beats:
        raise p3._err('DIAGRAM_NO_BEATS', 'plan carries no beats')
    duration = (float(beats[-1].get('start_seconds') or 0)
                + float(beats[-1].get('duration_seconds') or 4.0) + 1.0)

    dr = _dr()
    elements, meta = dr.build_elements(plan, ratio)
    _sync_drawplan(plan, meta)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = str(plan.get('production_id') or 'diagram')
    frames_dir = Path(tempfile.mkdtemp(prefix='diagram-frames-'))
    frame_count = 0
    try:
        for t, frame in render_frames(plan, ratio, fps):
            frame.save(frames_dir / f'f{frame_count:05d}.png')
            frame_count += 1

        ffmpeg = shutil.which('ffmpeg')
        mp4 = out_dir / f'{name}.mp4'
        if ffmpeg:
            vo = None
            vo_spec = plan.get('voiceover') or {}
            vo_path = Path(vo_spec.get('path')) if vo_spec.get('path') else voiceover
            if vo_path and Path(vo_path).exists():
                vo = Path(vo_path)
            sfx = p3.build_sfx(snd, plan, duration,
                               out_dir / f'{name}.sfx.wav')
            p3.encode_mp4(frames_dir, fps, wbp.RATIO_SIZES[ratio],
                          sfx, vo, duration, mp4, ffmpeg)

        times = [float(b.get('start_seconds') or 0)
                 + float(b.get('duration_seconds') or 0) * 0.6
                 for b in beats]
        p3.contact_sheet(frames_dir, times, fps, out_dir / f'{name}_QA.jpg')
    finally:
        if not keep_frames:
            shutil.rmtree(frames_dir, ignore_errors=True)

    metrics = {
        'schema': 'NexMindDiagramMetricsV1',
        'production_id': name,
        'type': 'diagram',
        'ratio': ratio,
        'fps': fps,
        'duration_seconds': round(duration, 3),
        'frame_count': frame_count,
        'element_count': len(elements),
        'beat_count': len(beats),
    }
    (out_dir / f'{name}_METRICS.json').write_text(
        json.dumps(metrics, indent=2) + '\n')

    receipt = {
        'schema': RECEIPT_SCHEMA,
        'renderer': {
            'path': 'engine_sources/whiteboard-v3-runtime/pipeline_diagram_timed.py',
            'version': VERSION,
            'type': 'diagram',
        },
        'production_id': name,
        'ratio': ratio,
        'duration_seconds': round(duration, 3),
        'outputs': {
            f.stem: {'path': str(f), 'sha256': p3._sha256(f)}
            for f in out_dir.glob(f'{name}*') if f.is_file()
        },
    }
    receipt_path = out_dir / f'{name}_EXECUTION_RECEIPT.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description='NexMind diagram-type narration-timed renderer')
    ap.add_argument('plan', help='Plan JSON — beats carry `narration` + '
                                 '`diagram` element specs')
    ap.add_argument('--out-dir', default='out-diagram')
    ap.add_argument('--ratio', default='16:9',
                    choices=['16:9', '1:1', '9:16'])
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--accent', default=None,
                    help='Brand accent hex (e.g. #E11D48) — overrides the '
                         'plan brandAuthority.accent')
    ap.add_argument('--voiceover', default=None)
    ap.add_argument('--word-timings', default=None,
                    help='Word-level timing JSON — audio is the clock')
    ap.add_argument('--keep-frames', action='store_true')
    ap.add_argument('--package-root', default=None)
    a = ap.parse_args(argv)

    plan = p3.load_plan(Path(a.plan))
    if a.accent:
        plan.setdefault('brandExecution', {}).setdefault(
            'brandAuthority', {})['accent'] = a.accent
    if a.word_timings:
        plan = p3.align_beats_to_words(
            plan, p3.load_word_timings(a.word_timings))
    receipt = render_production(
        plan, Path(a.out_dir), ratio=a.ratio, fps=a.fps,
        voiceover=Path(a.voiceover) if a.voiceover else None,
        keep_frames=a.keep_frames, accent=a.accent)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
