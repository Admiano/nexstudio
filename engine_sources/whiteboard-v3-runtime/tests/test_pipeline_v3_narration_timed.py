"""Golden-frame and contract regression for the reconstructed V3 renderer."""
from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent
sys.path.insert(0, str(RUNTIME))

import pipeline_v3_narration_timed as pipe  # noqa: E402

try:
    pipe.resolve_execution_package()
    HAS_BODY = True
except FileNotFoundError:
    HAS_BODY = False

pytestmark = pytest.mark.skipif(not HAS_BODY, reason='run scripts/install-engines.py first')

FIXTURE = RUNTIME / 'fixtures' / 'cluster_travel_plan.json'
GOLDEN = HERE / 'golden'
# Frames are deterministic (seeded board world); golden tolerance absorbs only
# cross-platform font rasterization drift.
MEAN_ABS_DIFF_TOLERANCE = 6.0


def _plan(**over):
    plan = json.loads(FIXTURE.read_text())
    beats = plan['beats'][:2]
    for b, dur in zip(beats, (1.6, 1.6)):
        b['duration_seconds'] = dur
        b['start_seconds'] = 0.0 if b is beats[0] else 1.6
    plan['beats'] = beats
    plan['pacing']['board_reveal_seconds'] = 0.4
    plan.update(over)
    return pipe.normalize_plan(plan)


def _frame_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    return buf.getvalue()


def _compiled(over=None):
    wbc, wbp, _, v3r = pipe.load_execution_body()
    plan = _plan(**(over or {}))
    compiled = wbc.compile_whiteboard_plan(plan, {'ratio': '16:9'})
    plan.update(compiled)
    return plan, wbp, v3r


def _render_at(plan, v3r, t):
    beats, scenes = plan['beats'], plan['sceneSpecs']
    trans = plan['pacing']['transition_seconds']
    idx = 0
    for i, b in enumerate(beats):
        if b['start_seconds'] <= t:
            idx = i
    local = t - beats[idx]['start_seconds']
    if idx > 0 and local < trans:
        return v3r.render_transition_frame(scenes[idx - 1], scenes[idx], plan, '16:9', local / trans)
    return v3r.render_scene_frame(scenes[idx], plan, '16:9', scene_time=local)


def _mean_abs_diff(a: bytes, b: bytes) -> float:
    from PIL import Image, ImageChops, ImageStat
    ia, ib = Image.open(io.BytesIO(a)).convert('RGB'), Image.open(io.BytesIO(b)).convert('RGB')
    if ia.size != ib.size:
        ib = ib.resize(ia.size)
    return ImageStat.Stat(ImageChops.difference(ia, ib)).mean[0]


# --- contract ---------------------------------------------------------------

def test_plan_requires_beats():
    with pytest.raises(ValueError, match='WHITEBOARD_V3_BEATS_REQUIRED'):
        pipe.normalize_plan({'production_id': 'x'})


def test_plan_narration_is_clock():
    plan = _plan()
    assert plan['executionMode'] == 'WHITEBOARD_SEMANTIC_GRAPH'
    assert all(s['executionMode'] == 'WHITEBOARD_SEMANTIC_GRAPH' for s in plan['sceneSpecs'])
    assert plan['beats'][1]['start_seconds'] == pytest.approx(1.6)
    assert plan['durationSeconds'] == pytest.approx(3.6)


def test_compile_produces_board_world_and_drawplan():
    plan, _, _ = _compiled()
    assert plan['whiteboardBoardWorld']['persistent'] is True
    zones = [s['whiteboardRuntime']['boardZone'] for s in plan['sceneSpecs']]
    assert len({(z['x'], z['y']) for z in zones}) == len(zones)
    for s in plan['sceneSpecs']:
        assert s['whiteboardRuntime']['drawPlan']


# --- determinism + golden frames --------------------------------------------

@pytest.mark.parametrize('t', [0.8, 1.7, 2.4, 3.4])
def test_golden_frame(t):
    plan, _, v3r = _compiled()
    img = _render_at(plan, v3r, t)
    got = _frame_bytes(img)
    golden = GOLDEN / f'frame_t{t:.1f}.png'
    if not golden.exists():
        golden.write_bytes(got)
        pytest.fail(f'golden written: {golden.name} — re-run to compare')
    diff = _mean_abs_diff(got, golden.read_bytes())
    assert diff <= MEAN_ABS_DIFF_TOLERANCE, f't={t}s drifted {diff:.2f} vs golden'


def test_render_deterministic():
    p1, _, v3r = _compiled()
    p2, _, _ = _compiled()
    a = _frame_bytes(_render_at(p1, v3r, 0.9))
    b = _frame_bytes(_render_at(p2, v3r, 0.9))
    assert a == b


# --- end-to-end encode ------------------------------------------------------

@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='ffmpeg required')
def test_end_to_end_encode(tmp_path):
    plan = _plan()
    receipt = pipe.render_production(plan, tmp_path, ratio='16:9', fps=8)
    mp4 = tmp_path / f"{plan['production_id']}.mp4"
    assert mp4.exists() and mp4.stat().st_size > 0
    probe = shutil.which('ffprobe')
    if probe:
        out = json.loads(__import__('subprocess').run(
            [probe, '-v', 'quiet', '-print_format', 'json', '-show_format', str(mp4)],
            capture_output=True, text=True).stdout)
        assert float(out['format']['duration']) == pytest.approx(plan['durationSeconds'], abs=0.6)
    assert receipt['renderer']['reconstruction'] is True
    assert (tmp_path / f"{plan['production_id']}_QA.jpg").exists()


# --- themes -----------------------------------------------------------------

def test_default_palette_is_white_paper_black_ink(tmp_path, monkeypatch):
    plan_file = tmp_path / 'plan.json'
    bare = _plan()
    bare.pop('brandExecution', None)
    plan_file.write_text(json.dumps(bare))
    loaded = pipe.load_plan(plan_file)
    brand = loaded['brandExecution']['brandAuthority']
    assert brand['background'] == '#FFFFFF'
    assert brand['ink'] == '#1A1A17'
    assert brand['accent'] == '#1A1A17'


def test_dark_theme_swaps_paper_and_ink():
    plan = _plan()
    pipe.apply_theme(plan, 'dark')
    brand = plan['brandExecution']['brandAuthority']
    assert brand['background'] == '#121211'
    assert brand['ink'] == '#F5F4EF'
    assert brand['accent'] == brand['ink']
    pipe.apply_theme(plan, 'light')
    assert plan['brandExecution']['brandAuthority']['background'] == '#FFFFFF'
