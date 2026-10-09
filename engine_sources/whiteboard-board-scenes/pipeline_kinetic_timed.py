#!/usr/bin/env python3
"""Kinetic-type video pipeline — narration-timed sentence builds.

A sibling type to the whiteboard board renderer: same plan->render->mix->QA
flow, same word-timing sync (`align_beats_to_words`), same audio encode and
receipts. Only the frame stage differs — text IS the visual, so frames come
from `kinetic_type_renderer` (typeset sentences, word states, emphasis
treatments) instead of stroke drawing.

CLI:
    python3 pipeline_kinetic_timed.py plan.json --out-dir out \
        --ratio 9:16 --voiceover vo.wav --word-timings words.json \
        [--face grotesk|marker] [--music] [--keep-frames]
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator

import pipeline_v3_narration_timed as core
import kinetic_icons
import kinetic_type_renderer as ktr

VERSION = 'kinetic-1.0.0'
RECEIPT_SCHEMA = 'NexMindWhiteboardV3ReconstructedExecutionReceiptV1'


def icons_mode(plan: dict, icons: str | None = None) -> str:
    mode = icons or plan.get('icons') or 'off'
    if mode not in ('auto', 'off'):
        raise core._err('KINETIC_ICONS_MODE', mode)
    return mode


def sentences(plan: dict, word_times: list[dict] | None,
              icons: str | None = None):
    """Kinetic sentences plus the sparse icon picks and their QA."""
    sents = ktr.sentence_words(plan, word_times)
    picks: dict = {}
    if icons_mode(plan, icons) == 'auto' and sents:
        picks = kinetic_icons.select(sents)
        kinetic_icons.apply(sents, picks)
    return sents, picks, kinetic_icons.qa(sents, picks) if picks else []


def render_frames(plan: dict, ratio: str, fps: int, face: str,
                  word_times: list[dict] | None = None,
                  theme: str = 'light', watermark: str | None = None,
                  accent: str | None = None,
                  icons: str | None = None,
                  ) -> Iterator[tuple[float, object]]:
    """Yield (t_seconds, PIL RGB frame) across the narration timeline."""
    from PIL import Image  # noqa: F401  (frame contract)
    wbp = core.load_execution_body(None)[1]
    size = wbp.RATIO_SIZES[ratio]
    sents, _picks, _issues = sentences(plan, word_times, icons)
    specs = [ktr.typeset(s, ktr.base_size(*size, face), face, size[0],
                         frame_h=size[1])
             for s in sents]
    if not sents:
        return
    step = 1.0 / fps
    end = sents[-1]['end'] + 0.9  # settle hold on the last sentence
    t = 0.0
    while t < end:
        yield t, ktr.render_kinetic_frame(sents, specs, t, size, plan, face,
                                          theme=theme, watermark=watermark,
                                          accent=accent)
        t += step


def render_production(plan: dict, out_dir: Path, ratio: str = '9:16',
                      fps: int = 24, face: str = 'condensed',
                      voiceover: Path | None = None,
                      word_times: list[dict] | None = None,
                      music: bool = False,
                      keep_frames: bool = False,
                      theme: str = 'light',
                      watermark: str | None = None,
                      accent: str | None = None,
                      icons: str | None = None) -> dict:
    wbc, wbp, snd, _v3r = core.load_execution_body(None)
    if ratio not in wbp.RATIO_SIZES:
        raise core._err('KINETIC_RATIO_UNSUPPORTED', ratio)
    sents, picks, icon_issues = sentences(plan, word_times, icons)
    if not sents:
        raise core._err('KINETIC_NO_SENTENCES',
                        'plan carries no narration text')
    duration = sents[-1]['end'] + 0.9

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = str(plan.get('production_id') or 'kinetic')
    frames_dir = Path(tempfile.mkdtemp(prefix='kinetic-frames-'))
    frame_count = 0
    try:
        for t, frame in render_frames(plan, ratio, fps, face, word_times,
                                      theme=theme, watermark=watermark,
                                      accent=accent, icons=icons):
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
            music_wav = (core.build_music(duration, out_dir / f'{name}.music.wav')
                         if music else None)
            core.encode_mp4(frames_dir, fps, wbp.RATIO_SIZES[ratio],
                            None, vo, duration, mp4, ffmpeg,
                            music_wav=music_wav)

        times = [s['start'] + (s['end'] - s['start']) * 0.6 for s in sents]
        core.contact_sheet(frames_dir, times, fps,
                           out_dir / f'{name}_QA.jpg')
    finally:
        if not keep_frames:
            shutil.rmtree(frames_dir, ignore_errors=True)

    metrics = {
        'schema': 'NexMindKineticTypeMetricsV1',
        'production_id': name,
        'type': 'kinetic',
        'face': face,
        'ratio': ratio,
        'fps': fps,
        'duration_seconds': round(duration, 3),
        'frame_count': frame_count,
        'sentence_count': len(sents),
        'word_count': sum(len(s['words']) for s in sents),
        'icons': [{'sentence': si, 'word': wi, 'phrase': r['phrase'],
                   'art': f"{r['icon'][1]}/{r['icon'][2]}",
                   'clip_rank': r['rank'], 'clip_sim': r['sim'],
                   'floor': bool(r.get('floor')),
                   'at_seconds': round(
                       sents[si]['words'][r['word']]['start'], 3)}
                  for si, rows in picks.items()
                  for wi, r in rows.items()],
        'icon_issues': icon_issues,
    }
    (out_dir / f'{name}_METRICS.json').write_text(
        json.dumps(metrics, indent=2) + '\n')

    receipt = {
        'schema': RECEIPT_SCHEMA,
        'renderer': {
            'path': 'engine_sources/whiteboard-v3-runtime/pipeline_kinetic_timed.py',
            'version': VERSION,
            'type': 'kinetic',
        },
        'production_id': name,
        'ratio': ratio,
        'duration_seconds': round(duration, 3),
        'outputs': {
            f.stem: {'path': str(f), 'sha256': core._sha256(f)}
            for f in out_dir.glob(f'{name}*') if f.is_file()
        },
    }
    receipt_path = out_dir / f'{name}_EXECUTION_RECEIPT.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description='NexMind kinetic-type narration-timed renderer')
    ap.add_argument('plan', help='Plan JSON — beats carry `narration` text')
    ap.add_argument('--out-dir', default='out-kinetic')
    ap.add_argument('--ratio', default='9:16',
                    choices=['16:9', '1:1', '9:16'])
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--face', default='condensed',
                    choices=sorted(ktr._FACES),
                    help='Display face: condensed (default, Barlow Condensed '
                         'ExtraBold emph), grotesk (Inter), marker (hand)')
    ap.add_argument('--theme', default='light', choices=sorted(ktr._THEMES),
                    help='Background theme: white paper or near-black')
    ap.add_argument('--watermark', default=None,
                    help='Optional small centered footer (brand/channel name)')
    ap.add_argument('--accent', default=None,
                    help='Brand accent hex (e.g. #E11D48) — overrides the '
                         'plan brandAuthority.accent; drives swooshes, '
                         'settled key words and the highlight box')
    ap.add_argument('--voiceover', default=None)
    ap.add_argument('--word-timings', default=None,
                    help='Word-level timing JSON (whisper verbose_json, '
                         'ElevenLabs, or flat [{word,start,end}]); audio is '
                         'the clock — each sentence keys to spoken words')
    ap.add_argument('--icons', default=None, choices=['auto', 'off'],
                    help='Sparse word icons on concrete key words '
                         '(default: plan `icons`, else off)')
    ap.add_argument('--music', action='store_true',
                    help='Add the generated ambient bed under the VO')
    ap.add_argument('--keep-frames', action='store_true')
    a = ap.parse_args(argv)

    plan = core.load_plan(Path(a.plan))
    word_times = core.load_word_timings(a.word_timings) if a.word_timings else None
    if word_times:
        plan = core.align_beats_to_words(plan, word_times)
    receipt = render_production(
        plan, Path(a.out_dir), ratio=a.ratio, fps=a.fps, face=a.face,
        voiceover=Path(a.voiceover) if a.voiceover else None,
        word_times=word_times, music=a.music, keep_frames=a.keep_frames,
        theme=a.theme, watermark=a.watermark, accent=a.accent,
        icons=a.icons)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
