import copy

import pytest

import plan_author as pa
import pipeline_v3_narration_timed as pipe
import sb_qa
import scene_map

pytestmark = pytest.mark.skipif(not scene_map.available(),
                                reason='spaCy model not installed')

try:
    pipe.resolve_execution_package()
    pipe.load_execution_body()
    HAS_BODY = True
except FileNotFoundError:
    HAS_BODY = False

if HAS_BODY:
    import v3_board_sections as bs


def test_quantities_keep_the_named_subjects_units_and_exact_values():
    chart = pa._quantities(['The small tank holds 40 liters.',
                            'The large tank holds 80 liters.'])
    assert chart is not None
    assert chart['baseline'] == 0
    assert [v['label'] for v in chart['values']] == ['small tank', 'large tank']
    assert [v['value'] for v in chart['values']] == [40, 80]
    assert len({v['unit'] for v in chart['values']}) == 1


def test_values_told_by_time_or_place_chart_against_that_setting():
    chart = pa._quantities(['In March, the valley gets 90 millimeters.',
                            'In April, it gets 120 millimeters.',
                            'By May, the rain climbs to 150 millimeters.'])
    assert chart is not None
    assert [v['label'] for v in chart['values']] == ['March', 'April', 'May']
    assert [v['value'] for v in chart['values']] == [90, 120, 150]
    assert pa._quantities(['In spring it holds 80 percent.',
                           'In spring it holds 35 percent.']) is None
    assert pa._quantities(['It holds 80 percent.',
                           'It holds 35 percent.']) is None


@pytest.mark.parametrize('sentences', [
    ['A tank holds about 40 liters.', 'A barrel holds 80 liters.'],
    ['A tank holds 40 liters.', 'A barrel holds 80 kilograms.'],
    ['A tank holds 40 liters.', 'A barrel costs 80 dollars.'],
    ['A tank holds water.', 'A barrel holds water.'],
    ['A tank holds 20-40 liters.', 'A barrel holds 80 liters.'],
    ['A tank holds -40 liters.', 'A barrel holds 80 liters.'],
    ['A tank holds 0 liters.', 'A barrel holds 0 liters.'],
    ['A panel produces 40 kilowatt hours.', 'A turbine produces 80 megawatt hours.'],
    ['A company earns 40 million dollars.', 'A shop earns 80 dollars.'],
])
def test_chart_never_invents_a_measurement_or_combines_incompatible_units(
        sentences):
    assert pa._quantities(sentences) is None


@pytest.mark.skipif(not HAS_BODY, reason='run scripts/install-engines.py first')
def test_chart_geometry_and_each_bar_follow_the_stated_value():
    plan = pa.build_storyboard(
        '## Storage\nThe small tank holds 40 liters. '
        'The large tank holds 80 liters. Water stays in both tanks.\n')
    beat = plan['beats'][0]
    beat['duration_seconds'] = 12
    words = beat['narration'].split()
    beat['word_times'] = [
        {'word': word, 'start': i * 0.6, 'end': (i + 1) * 0.6}
        for i, word in enumerate(words)]
    wbc, _wbp, _vr, v3r = pipe.load_execution_body()
    plan = pipe.normalize_plan(plan)
    v3r.configure_art(plan)
    plan.update(wbc.compile_whiteboard_plan(plan, {'ratio': '16:9'}))
    flow = bs._build(plan, '16:9')
    sec = next(s for s in flow['sections'] if s.get('qa_quantities'))
    a, b = sec['qa_quantities']
    assert a['bounds'][3] == b['bounds'][3]
    assert (a['bounds'][3] - a['bounds'][1]) / (
        b['bounds'][3] - b['bounds'][1]) == pytest.approx(0.5)
    assert a['start'] == a['said'] < b['start'] == b['said']
    issues = []
    sb_qa._quantitative(issues, 0, plan['beats'][0], sec)
    assert not issues
    tampered = copy.deepcopy(sec)
    tampered['qa_quantities'][0]['bounds'] = b['bounds']
    sb_qa._quantitative(issues, 0, plan['beats'][0], tampered)
    assert any(i['check'] == 'chart-scale' for i in issues)
    tampered = copy.deepcopy(sec)
    chart = next(e['role']['chart'] for e in tampered['qa_els']
                 if e['kind'] == 'quantity-chart')
    chart['values'][0]['source'] = 'The small tank holds 99 liters.'
    issues = []
    sb_qa._quantitative(issues, 0, plan['beats'][0], tampered)
    assert any(i['check'] == 'chart-provenance' for i in issues)


@pytest.mark.skipif(not HAS_BODY, reason='run scripts/install-engines.py first')
@pytest.mark.parametrize('ratio', ['16:9', '9:16', '1:1'])
def test_chart_is_the_bold_hero_of_its_scene_in_every_ratio(ratio):
    plan = pa.build_storyboard(
        '## Storage\nThe small tank holds 40 liters. '
        'The large tank holds 80 liters. Water stays in both tanks.\n')
    wbc, _wbp, _vr, v3r = pipe.load_execution_body()
    plan = pipe.normalize_plan(plan)
    v3r.configure_art(plan)
    plan.update(wbc.compile_whiteboard_plan(plan, {'ratio': ratio}))
    flow = bs._build(plan, ratio)
    sec = next(s for s in flow['sections'] if s.get('qa_quantities'))
    _l, top, _r, bottom = sec['qa_content']
    chart = next(e for e in sec['qa_els'] if e['kind'] == 'quantity-chart')
    x0, y0, x1, y1 = chart['ink']
    assert (y1 - y0) / (bottom - top) >= 0.6
    assert y0 - top <= 0.1 * (bottom - top)
