"""Story mode: stories are told as panels of people doing things, with
their cast, feelings and contact; arrows only where a relation is stated."""
import pytest

import scene_map as sm
import sb_cast
import sb_story

pytestmark = pytest.mark.skipif(not sm.available(),
                                reason='spaCy model not installed')

STORY = ['Her two little boys run into the kitchen.',
         'The older boy reads a picture book at the table.',
         'The younger boy sits on her lap and eats a slice of bread.',
         'Grace laughs and hugs them both.']
EXPLAIN = ['A tokenized stock is a digital token that represents one share.',
           'The custodian holds the real share in a vault.',
           'Each token is backed by that share.',
           'Investors can trade tokens on a blockchain.']


def _maps(sents):
    carry: dict = {}
    return [sm.parse(s, carry) for s in sents]


def test_story_and_explainer_are_told_apart():
    assert sb_story.is_story_scene(_maps(STORY), {'grace'})
    assert not sb_story.is_story_scene(_maps(EXPLAIN), set())


SCRIPT = """# Sunday at the Farm

## Morning Chores
Old Samuel walks into the barn at dawn. His two granddaughters follow him with a basket. The younger girl sits on his knee and laughs. The older girl feeds the hens.

## Evening
That night Samuel reads them a story by the fire. Both girls fall asleep with a smile.
"""


@pytest.fixture(scope='module')
def plan():
    import plan_author
    return plan_author.build_storyboard(SCRIPT, title='Sunday at the Farm')


def _roles(plan, bi):
    sc = plan['beats'][bi]['scene']
    return sc, [sc['heroRole']] + sc['supportingRoles']


def test_story_plan_is_story_without_graph(plan):
    assert plan['mode'] == 'story'
    for bi in range(len(plan['beats'])):
        sc, _rs = _roles(plan, bi)
        assert sc['mode'] == 'story' and 'graph' not in sc


def test_quantified_group_is_distinct_members(plan):
    _sc, rs = _roles(plan, 0)
    girls = [r for r in rs if r.get('moment') == 1
             and r['icon'] == 'person' and r['label'] == 'granddaughter']
    assert {r.get('cast_key') for r in girls} == {'granddaughter#1',
                                                 'granddaughter#2'}
    assert all(r.get('gender') == 'f' for r in girls)


def test_older_and_younger_keep_their_member_and_lap(plan):
    _sc, rs = _roles(plan, 0)
    young = next(r for r in rs if r.get('moment') == 2
                 and r['label'] == 'girl')
    old = next(r for r in rs if r.get('moment') == 3
               and r['label'] == 'girl')
    assert young['cast_key'] != old['cast_key']
    assert young.get('lap_of') in ('samuel', 'old samuel')
    assert young.get('emotion') == 'laugh'


def test_sleep_with_a_smile_is_drawn_asleep(plan):
    _sc, rs = _roles(plan, 1)
    girls = [r for r in rs if r.get('moment') == 1 and r['label'] == 'girl']
    assert len(girls) >= 2 or any(r.get('group') for r in girls)
    assert all(r.get('emotion') == 'sleep' for r in girls)


def test_narrated_feelings_are_drawable():
    assert set(sb_story._EMO_VERB.values()) | set(
        sb_story._EMO_ADJ.values()) <= set(sb_cast.EMOTIONS)


def test_places_imply_rooms():
    assert sb_story.place_kind('kitchen') == 'kitchen'
    assert sb_story._room_of('bed') == 'bedroom'
    assert sb_story.place_kind('table') == ''


def test_stressed_hands_go_to_the_head():
    import sb_activity
    spec = sb_activity.resolve('sit', [('on', 'sofa')], '')
    _st, _m, anch, _meta = sb_activity.compose(spec, None, 'stressed')
    hx, hy = anch['head']
    r = anch['head_r']
    for k in ('hand_n', 'hand_f'):
        x, y = anch[k]
        assert abs(x - hx) < r * 1.4 and abs(y - hy) < r * 1.2


def _board(plan):
    import copy
    import pipeline_v3_narration_timed as pipe
    try:
        wbc, _a, _b, v3r = pipe.load_execution_body()
    except FileNotFoundError:
        pytest.skip('run scripts/install-engines.py first')
    import v3_board_sections as bs
    p = pipe.normalize_plan(copy.deepcopy(plan))
    v3r.configure_art(p)
    p.update(wbc.compile_whiteboard_plan(p, {'ratio': '16:9'}))
    return p, bs._build(p, '16:9')


def test_story_board_is_panels_without_arrows(plan):
    p, flow = _board(plan)
    secs = [s for s in flow['sections'] if 'qa_els' in s]
    assert secs and all(s.get('layout') == 'panels' for s in secs)
    assert all(not s.get('qa_arrows') for s in secs)
    assert all(len(s['qa_panels']) == len({
        int((e['role'] or {}).get('moment') or 0) for e in s['qa_els']})
        for s in secs)
    lap = [e for s in secs for e in s['qa_els'] if e.get('on_lap')]
    assert lap, 'the lap sitter is drawn on the lap'


EXPLAINER = """# How Solar Power Works

## From Sunlight to Socket
Sunlight hits a solar panel on the roof. The panel turns that light into electricity. An inverter changes the current so the house can use it. Extra power flows to the grid, and the utility pays the owner a credit.
"""


def test_explainer_keeps_semantic_arrows_with_provenance():
    import plan_author
    p = plan_author.build_storyboard(EXPLAINER, title='Solar')
    assert p['mode'] == 'explain'
    assert all(b['scene'].get('mode') != 'story' for b in p['beats'])
    _p, flow = _board(p)
    secs = [s for s in flow['sections'] if 'qa_els' in s]
    arrows = [a for s in secs for a in s.get('qa_arrows') or ()]
    assert arrows, 'stated flows draw arrows'
    assert all(a == 'flow' or a.startswith(('edge:', 'cycle', 'before'))
               for a in arrows)
