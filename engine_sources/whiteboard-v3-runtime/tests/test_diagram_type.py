"""Diagram type — cumulative annotated-canvas renderer tests."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pipeline_v3_narration_timed as p3  # noqa: E402
import pipeline_diagram_timed as pd  # noqa: E402

FIXTURE = (Path(__file__).resolve().parent.parent
           / 'fixtures' / 'diagram_demo_plan.json')


@pytest.fixture(scope='module')
def plan():
    p3.load_execution_body(None)
    return p3.load_plan(FIXTURE)


@pytest.fixture(scope='module')
def built(plan):
    return pd._dr().build_elements(plan, '16:9')


def test_elements_cover_every_beat(built):
    elements, meta = built
    beats_seen = {e['beat'] for e in elements}
    assert beats_seen == {0, 1, 2}
    kinds = {e['kind'] for e in elements}
    assert {'headline', 'hero', 'stage', 'icon', 'chip', 'callout',
            'arrow', 'summary'} <= kinds


def test_windows_stay_inside_beat_span(plan, built):
    elements, meta = built
    for e in elements:
        dur = plan['beats'][e['beat']]['duration_seconds']
        assert 0 <= e['start'] < e['end'] <= dur + 1e-6


def test_drawplan_mirrors_element_windows(built):
    elements, meta = built
    by_beat = {}
    for e in elements:
        by_beat.setdefault(e['beat'], []).append(e)
    for bi, specs in enumerate(meta['plans']):
        els = by_beat.get(bi, [])
        assert len(specs) == len(els)
        for spec, e in zip(specs, els):
            assert abs(spec['start'] - e['start']) < 1e-6
            assert abs(spec['end'] - e['end']) < 1e-6
            # every stroke has a pen-down interval inside the window
            assert len(spec['pen']) == len(e['strokes'])
            for a, b in spec['pen']:
                assert e['start'] - 1e-6 <= a < b <= e['end'] + 1e-6


def test_all_ink_stays_on_board(plan, built):
    elements, meta = built
    z = pd._dr()._zone('16:9')
    for e in elements:
        for st in e['strokes']:
            absolute = st[4] if len(st) > 4 else False
            for px, py in st[0]:
                x = px if absolute else e['center'][0] + px * e['size']
                y = py if absolute else e['center'][1] + py * e['size']
                assert abs(x) <= z['w'] * 0.52, (e['kind'], x, z['w'])
                assert abs(y) <= z['h'] * 0.52, (e['kind'], y, z['h'])


def test_past_beats_mute_and_persistent_never(plan, built):
    elements, meta = built
    # force active beat = 2 by rendering at its start
    beats = plan['beats']
    t = float(beats[2]['start_seconds']) + 0.01
    layer, _tip = pd._dr().draw_diagram_layer(plan, elements, meta['atlas'],
                                           '16:9', t)
    assert layer.getbbox() is not None


@pytest.mark.parametrize('ratio', ['16:9', '1:1', '9:16'])
def test_renders_in_all_ratios(plan, ratio):
    elements, meta = pd._dr().build_elements(plan, ratio)
    img = pd._dr().render_diagram_frame(plan, elements, meta['atlas'],
                                     ratio, 21.0)
    assert img.size == p3.load_execution_body(None)[1].RATIO_SIZES[ratio]
    # ink present — a blank frame would have ~no dark pixels
    px = img.convert('L')
    assert min(px.getdata()) < 120


def test_cli_smoke(tmp_path):
    out = tmp_path / 'd'
    rc = pd.main([str(FIXTURE), '--out-dir', str(out), '--ratio', '16:9',
                  '--fps', '8'])
    assert rc == 0
    receipt = json.loads((out / 'NEXMIND_DIAGRAM_DEMO_EXECUTION_RECEIPT.json')
                         .read_text())
    assert receipt['renderer']['type'] == 'diagram'
    assert receipt['duration_seconds'] > 15
