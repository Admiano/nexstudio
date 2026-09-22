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
    # 'chip' is the no-art fallback, not a required kind — a fully
    # resolvable plan draws icons only
    assert {'headline', 'hero', 'stage', 'icon', 'callout',
            'arrow', 'summary'} <= kinds


def test_concept_without_art_falls_back_to_chip():
    p3.load_execution_body(None)
    plan = {
        'productionId': 'T', 'beats': [
            {'narration': 'n', 'start_seconds': 0, 'duration_seconds': 4,
             'diagram': {'elements': [
                 {'part': 'xyzzy blorp', 'label': 'THING',
                  'at': 'hero-tl'}]}},
        ],
        'diagram': {'title': 'T', 'hero': 'laptop'},
    }
    elements, _ = pd._dr().build_elements(plan, '16:9')
    chips = [e for e in elements if e['kind'] == 'chip']
    assert len(chips) == 1 and chips[0]['slot'] == 'hero-tl'


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


def test_text_block_is_box_centered(plan):
    dr = pd._dr()
    # the union ink bounds of a two-line block must center on its box
    st = dr._text_block([('CPU', 18.5, 'ink', 1.35, True),
                         ('thinks', 13.0, 'ink', 0.95, False)],
                        50.0, 70.0, gap=9.0)
    xs = [p[0] for s in st for p in s[0]]
    ys = [p[1] for s in st for p in s[0]]
    assert abs((min(xs) + max(xs)) / 2 - 50.0) < 0.5
    assert abs((min(ys) + max(ys)) / 2 - 70.0) < 0.5


def test_drawn_elements_keep_full_ink(plan, built):
    elements, meta = built
    beats = plan['beats']
    t = float(beats[2]['start_seconds']) + 0.01
    layer, _tip = pd._dr().draw_diagram_layer(plan, elements, meta['atlas'],
                                              '16:9', t)
    # elements drawn during earlier beats must NOT fade to pale — count
    # near-pale pixels (the old mute color ~ (212,208,196)) vs ink pixels
    px = layer.load()
    w, h = layer.size
    pale = ink = 0
    for x in range(0, w, 7):
        for y in range(0, h, 7):
            p = px[x, y]
            if p[3] < 40:
                continue
            if p[0] < 90 and p[1] < 90:
                ink += 1
            elif 195 < p[0] < 235 and p[3] > 200:
                pale += 1
    assert ink > 0
    assert pale == 0


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


def test_flow_layout_chains_stage_cells():
    p3.load_execution_body(None)
    plan = p3.load_plan(FIXTURE.parent / 'devin_flow_demo_plan.json')
    elements, meta = pd._dr().build_elements(plan, '16:9')
    kinds = [e['kind'] for e in elements]
    # no hero in flow — beats are stage cells
    assert 'hero' not in kinds
    assert kinds.count('cellbox') == 3
    # connector arrows chain the cells
    assert kinds.count('arrow') >= 2
    # every cell's content stays inside its box
    for i, (cx0, cy0, wc, hc) in enumerate(meta['atlas']['cells']):
        for e in elements:
            if e.get('slot') == f'cell{i}' and e['kind'] != 'stage':
                b = pd._dr()._elem_bounds(e)
                assert b and (cx0 - wc / 2 - 1 <= b[0]
                              and b[2] <= cx0 + wc / 2 + 1
                              and cy0 - hc / 2 - 1 <= b[1]
                              and b[3] <= cy0 + hc / 2 + 1)


def test_erase_transition_fades_prior_beat(plan, built):
    import copy
    dr = pd._dr()
    elements, meta = built
    plan2 = copy.deepcopy(plan)
    plan2['beats'][1]['diagram']['transition'] = 'erase'
    t = plan2['beats'][1]['start_seconds'] + 0.3
    fade = dr.wbp._ease(dr.wbp._clamp(0.3 / 0.7))
    layer, _ = dr.draw_diagram_layer(
        plan2, elements, meta['atlas'], '16:9', t, wipe=(1, fade, 0.7))
    full, _ = dr.draw_diagram_layer(
        plan2, elements, meta['atlas'], '16:9', t)
    # the sweep erases prior ink left of the eraser edge but keeps
    # whatever is right of it — total ink drops without going black
    erase_x = int(layer.width * fade)
    wiped_left = sum(1 for v in layer.crop((0, 0, erase_x, layer.height))
                     .getdata() if v[3] > 128)
    full_left = sum(1 for v in full.crop((0, 0, erase_x, layer.height))
                    .getdata() if v[3] > 128)
    assert wiped_left < full_left
    assert sum(1 for v in layer.getdata() if v[3] > 128) > 0


def test_zoom_transition_settles_to_full_frame(plan, built):
    import copy
    dr = pd._dr()
    elements, meta = built
    plan2 = copy.deepcopy(plan)
    plan2['beats'][1]['diagram']['transition'] = 'zoom'
    b1 = plan2['beats'][1]['start_seconds']
    mid = dr.render_diagram_frame(
        plan2, elements, meta['atlas'], '16:9', b1 + 0.1)
    late = dr.render_diagram_frame(
        plan2, elements, meta['atlas'], '16:9', b1 + 2.0)
    assert mid.size == late.size == (1280, 720)
