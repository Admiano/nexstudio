"""Story mode: stories are told as panels of people doing things, with
their cast, feelings and contact; arrows only where a relation is stated."""
import pytest

import plan_author
import scene_map as sm
import sb_cast
import sb_qa
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


def _board(plan, ratio='16:9'):
    import copy
    import pipeline_v3_narration_timed as pipe
    try:
        wbc, _a, _b, v3r = pipe.load_execution_body()
    except FileNotFoundError:
        pytest.skip('run scripts/install-engines.py first')
    import v3_board_sections as bs
    p = pipe.normalize_plan(copy.deepcopy(plan))
    v3r.configure_art(p)
    p.update(wbc.compile_whiteboard_plan(p, {'ratio': ratio}))
    return p, bs._build(p, ratio)


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


def test_story_moments_share_a_readable_stage_and_retire_previous_actors(plan):
    _p, flow = _board(plan)
    secs = [s for s in flow['sections'] if 'qa_els' in s]
    for sec in secs:
        assert sec['composition'] == 'stage'
        assert len({p['rect'] for p in sec['qa_panels']}) == 1
        actors = [e for e in sec['qa_els'] if e['kind'] == 'person']
        assert min(e['ink'][3] - e['ink'][1] for e in actors) > 75
        items = [i for i in sec['items2'] if 'moment' in i]
        moments = sorted({i['moment'] for i in items})
        for moment in moments[:-1]:
            current = [i for i in items if i['moment'] == moment]
            following = [i for i in items if i['moment'] == moment + 1]
            if following:
                next_start = min(g[1] for i in following for g in i['groups'])
                assert all(i['fade'][1] <= next_start + 0.02 for i in current)


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


def test_only_collectives_of_people_become_groups():
    assert sm.people_group('crew') and sm.people_group('family')
    assert not sm.people_group('table') and not sm.people_group('array')


def test_table_is_never_cast_as_people():
    import plan_author
    p = plan_author.build_storyboard(
        "# Lunch\n\n## Noon\nTwo friends walk into the cafe. They sit at "
        "the table and share a sandwich. The waiter brings them tea. "
        "Both friends laugh.\n", title='Lunch')
    for b in p['beats']:
        sc = b['scene']
        for r in [sc['heroRole']] + sc['supportingRoles']:
            if r['label'] == 'table':
                assert r.get('icon') != 'person' and not r.get('group')


def test_story_keeps_all_people_and_counted_objects_in_a_moment():
    import plan_author
    beat = plan_author.build_storyboard(
        '## Break\nMaya, Jo and Lee pour water into three cups.')['beats'][0]
    roles = [beat['scene']['heroRole']] + beat['scene']['supportingRoles']
    assert {r['label'] for r in roles if r['icon'] == 'person'} >= {
        'maya', 'jo', 'lee'}
    assert next(r for r in roles if r['label'] == 'cup')['count'] == 3


def test_named_building_gets_a_generic_room_backdrop():
    import v3_board_sections as sections
    floor, solid = 650, []
    art = sections._sb_room('town hall', (80, 180, 1100, 700),
                            floor, solid, 7)
    assert art


def test_group_members_keep_distinct_props_and_cast_identities():
    import plan_author
    beat = plan_author.build_storyboard(
        '## Workshop\nTwo assistants carry a toolbox. '
        'The older assistant holds a flashlight while the younger '
        'assistant brings a pump.')['beats'][0]
    roles = [beat['scene']['heroRole']] + beat['scene']['supportingRoles']
    people = [r for r in roles if r['icon'] == 'person'
              and r['moment'] == 1 and r.get('activity')]
    assert len(people) == 2
    assert len({r['cast_key'] for r in people}) == 2
    first = {r['cast_key'] for r in roles if r['icon'] == 'person'
             and r['moment'] == 0}
    assert {r['cast_key'] for r in people} == first
    assert {r['activity']['partner'] for r in people} == {'flashlight', 'pump'}


def test_hand_work_retains_the_narrated_kneeling_posture_in_the_plan():
    import plan_author
    beat = plan_author.build_storyboard(
        '## Workshop\nNina kneels beside the cart and repairs '
        'the wheel with a wrench.')['beats'][0]
    roles = [beat['scene']['heroRole']] + beat['scene']['supportingRoles']
    actor = next(r for r in roles if r['icon'] == 'person')
    assert actor['activity']['schema'] == 'fix'
    assert actor['activity']['posture'] == 'kneel'
    assert actor['activity']['roles']['instrument'] == 'wrench'


def test_hand_work_preserves_the_object_the_actor_kneels_beside():
    import plan_author
    scene = plan_author.build_storyboard(
        '## Workshop\nNina kneels beside the cart and repairs '
        'the wheel with a wrench.')['beats'][0]['scene']
    roles = [scene['heroRole']] + scene['supportingRoles']
    actor = next(r for r in roles if r['icon'] == 'person')
    cart = next(r for r in roles if r['label'] == 'cart')
    assert 'cart' in actor['activity']['setting']
    assert cart['attach'] == 'behind'
    assert roles[cart['to']] is actor


def test_weather_outside_does_not_move_people_out_of_the_building():
    import plan_author
    plan = plan_author.build_storyboard(
        '## Arrival\nNina enters the museum.\n\n## Break\n'
        'Rain falls outside the window as Nina sits at a table.')
    assert plan['beats'][0]['scene']['places'] == ['museum']
    assert plan['beats'][1]['scene']['places'] == ['museum']


def test_multinoun_buildings_use_the_whole_place_name():
    assert sb_story.place_kind('town hall') == 'town hall'
    assert sb_story.place_kind('living room') == 'living'
    assert sb_story.place_kind('workbench') == ''


def test_weather_cessation_clears_weather_from_later_moments():
    import plan_author
    plan = plan_author.build_storyboard(
        '## Outside\nRain falls as Nina walks along the road. '
        'When the rain stops, she rides a scooter.')
    scene = plan['beats'][0]['scene']
    roles = [scene['heroRole']] + scene['supportingRoles']
    assert any(r['label'] == 'rain' and r['moment'] == 0 for r in roles)
    assert not any(r['label'] == 'rain' and r['moment'] == 1 for r in roles)


def test_held_devices_are_not_hidden_as_another_clothing_sense():
    assert not sb_story.is_worn('pump')
    assert sb_story.is_worn('hat')


def test_two_people_carry_one_shared_prop_with_contacts():
    import plan_author
    plan = plan_author.build_storyboard(
        '## Carrying\nTwo porters carry a chest to a table.')
    _p, flow = _board(plan)
    sec = next(s for s in flow['sections'] if s.get('qa_els'))
    people = [e for e in sec['qa_els'] if e['kind'] == 'person']
    props = [e for e in sec['qa_els'] if e['role']['label'] == 'chest']
    assert len(people) == 2 and len(props) == 1
    issues, _scenes = sb_qa.visual(plan)
    assert any(i['check'] == 'shared-contact' and i['severity'] == 'info'
               for i in issues)
    assert not any(i['severity'] == 'fail' for i in issues)


def test_actor_scale_survives_a_change_in_scene_density():
    import plan_author
    plan = plan_author.build_storyboard(
        '## Alone\nNina walks along a road.\n'
        '## Together\nNina walks along the road with two porters.')
    _p, flow = _board(plan)
    figures = [e for sec in flow['sections'] for e in sec.get('qa_els', ())
               if e['kind'] == 'person' and e['role']['label'] == 'nina']
    assert len(figures) == 2
    heights = [e['ink'][3] - e['ink'][1] for e in figures]
    assert abs(heights[0] - heights[1]) < 2.0


def test_figure_unit_stays_fixed_when_a_dense_picture_has_fixed_gaps():
    import plan_author
    plan = plan_author.build_storyboard(
        '## Survey\nLena walks along a river with a girl and a boy. '
        'Lena watches two geese through binoculars.\n'
        '## Return\nLena waves from a doorway.')
    _p, flow = _board(plan)
    units = [e['figure_unit'] for sec in flow['sections']
             for e in sec.get('qa_els', ())
             if e['kind'] == 'person' and e['role']['label'] == 'lena']
    assert len(units) == 3
    assert max(units) - min(units) < 0.1


def test_weather_outside_a_window_is_composed_into_the_window():
    import plan_author
    sc = plan_author.build_storyboard(
        '## Cabin\nRain falls outside a window as Nina sits at a table.'
    )['beats'][0]['scene']
    roles = [sc['heroRole']] + sc['supportingRoles']
    weather = next(r for r in roles if r['label'] == 'rain')
    assert weather['attach'] == 'in'
    assert roles[weather['to']]['label'] == 'window'


def test_children_reuse_previously_named_individuals():
    plan = plan_author.build_storyboard(
        '## Garden\nRita, a female gardener, walks with a girl and a boy. '
        'The children sit on a bench. Rita sits beside them and laughs.')
    scene = plan['beats'][0]['scene']
    roles = [scene['heroRole']] + scene['supportingRoles']
    children = [r for r in roles if r.get('group') == 'child']
    assert {r['cast_key'] for r in children} == {'girl', 'boy'}
    for r in children:
        original = next(p for p in roles if p['label'] == r['cast_key'])
        assert sb_cast.look_for(r) == sb_cast.look_for(original)
    adult = next(r for r in roles if r['label'] == 'rita'
                 and r['moment'] == 2)
    assert adult.get('attach') != 'beside'
    _p, flow = _board(plan)
    sec = next(s for s in flow['sections'] if s.get('qa_els'))
    figures = [e for e in sec['qa_els'] if e['kind'] == 'person'
               and e['role']['label'] == 'rita']
    assert len(figures) == 2
    assert abs(figures[0]['figure_unit'] - figures[1]['figure_unit']) < 0.1
    assert not any(i.get('label') == 'callout' for i in sec['items2'])


@pytest.mark.parametrize('ratio', ['16:9', '9:16', '1:1'])
def test_a_lone_story_picture_fills_its_space_in_every_ratio(ratio):
    import plan_author
    plan = plan_author.build_storyboard('## Walk\nNina walks along a road.')
    _p, flow = _board(plan, ratio)
    sec = next(s for s in flow['sections'] if s.get('qa_els'))
    _l, top, _r, bottom = sec['qa_content']
    ink = [e['ink'] for e in sec['qa_els'] if e.get('ink')]
    y0 = min(i[1] for i in ink)
    y1 = max(i[3] for i in ink)
    assert (y1 - y0) / (bottom - top) >= 0.5
    centre = (y0 + y1) / 2
    assert abs(centre - (top + bottom) / 2) <= 0.2 * (bottom - top)
