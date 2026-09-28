"""Storyboard scene layouts, marker foley sync and hand sprite contracts."""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent
sys.path.insert(0, str(RUNTIME))

import marker_sfx  # noqa: E402
import pipeline_v3_narration_timed as pipe  # noqa: E402

try:
    pipe.resolve_execution_package()
    HAS_BODY = True
except FileNotFoundError:
    HAS_BODY = False

pytestmark = pytest.mark.skipif(not HAS_BODY,
                                reason='run scripts/install-engines.py first')


def _built(name):
    wbc, _wbp, _, v3r = pipe.load_execution_body()
    import v3_board_sections as bs
    plan = pipe.normalize_plan(
        json.loads((RUNTIME / 'fixtures' / name).read_text()))
    v3r.set_art_kit(plan.get('art_kit'))
    plan.update(wbc.compile_whiteboard_plan(plan, {'ratio': '16:9'}))
    return plan, bs, bs._build(plan, '16:9')


@pytest.mark.parametrize('name, layouts', [
    ('storyboard_edge_plan.json', ['row', 'stair', 'journey', 'focus']),
    ('storyboard_stress_plan.json',
     ['before_after', 'cycle', 'reaction', 'row']),
])
def test_layout_per_relation_and_no_collisions(name, layouts):
    plan, _bs, flow = _built(name)
    assert [s.get('layout') for s in flow['sections']] == layouts
    assert not plan.get('_sb_audit')


def test_divider_only_in_contrast_scenes():
    _plan, _bs, flow = _built('storyboard_edge_plan.json')
    for sec in flow['sections']:
        assert sec['divider'] == (sec['relation'] == 'contrast')


def test_pen_spans_are_ordered_and_bounded():
    plan, bs, _flow = _built('storyboard_edge_plan.json')
    spans = bs.pen_spans(plan, '16:9')
    assert len(spans) > 50
    dur = sum(float(b['duration_seconds']) for b in plan['beats'])
    for (s0, e0, ln), nxt in zip(spans, spans[1:] + [None]):
        assert 0 <= s0 < e0 <= dur + 5 and ln >= 0
        if nxt:
            assert nxt[0] >= s0


def test_marker_foley_silent_between_strokes(tmp_path):
    ev = [{'start': 0.2, 'duration': 0.4, 'length': 300, 'gain': 1.0},
          {'start': 1.5, 'duration': 0.3, 'length': 120, 'gain': 1.0}]
    out = tmp_path / 'm.wav'
    marker_sfx.render(ev, 2.2, out)
    with wave.open(str(out)) as w:
        assert w.getframerate() == marker_sfx.RATE and w.getnchannels() == 1
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32767
    r = marker_sfx.RATE

    def rms(t0, t1):
        return float(np.sqrt(np.mean(a[int(t0 * r):int(t1 * r)] ** 2)))
    assert rms(0.3, 0.5) > 20 * max(rms(0.9, 1.4), 1e-5)
    assert rms(0.0, 0.18) < rms(0.3, 0.5) / 20
    spec = np.abs(np.fft.rfft(a[int(.25 * r):int(.55 * r)])) ** 2
    f = np.fft.rfftfreq(int(.55 * r) - int(.25 * r), 1 / r)
    assert spec[f > 7000].sum() / spec.sum() < 0.03


def test_hand_sprite_keeps_original_size_with_feathered_forearm():
    _wbc, _wbp, _, v3r = pipe.load_execution_body()
    from PIL import Image
    src = Image.open(RUNTIME / 'assets' / 'hand' / 'drawing-hand.png')
    hand = v3r._hand()
    assert hand.size == src.size
    alpha = np.asarray(hand)[..., 3]
    assert alpha[-4:, -4:].max() == 0
