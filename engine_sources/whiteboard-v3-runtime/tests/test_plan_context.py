import pytest

import plan_author as pa


def test_unlisted_verbs_pose_by_meaning():
    # none of these verbs are in the cue tables
    for sent, pose in (('the chef chops onions', 'reach'),
                       ('the vendor sells fish', 'offer'),
                       ('the dispatcher answers the phone', 'point'),
                       ('workers spread the beans', 'reach')):
        low = sent.split()
        assert pa._verb_pose(low, 1)[0] == pose


def test_stative_verbs_do_not_pose():
    assert pa._verb_pose('the goalkeeper feels sad'.split(), 1) is None


def test_multi_sentence_scene_keeps_every_moment():
    sb = pa.build_storyboard(
        '## Step\nA baker kneads the dough on the table. '
        'She slides the loaf into the oven.\n')
    sc = sb['beats'][0]['scene']
    roles = [sc['heroRole']] + sc['supportingRoles']
    assert sc['relation'] == 'story'
    assert {r.get('moment') for r in roles} == {0, 1}
    assert len(roles) >= 4
    assert any(r.get('annotate') for r in roles)


def test_what_happens_is_drawn():
    sb = pa.build_storyboard(
        '## Up\nA trader watches the chart. The chart jumps.\n\n'
        '## Down\nThe analyst panics as the chart crashes.\n')
    up, down = (b['scene'] for b in sb['beats'])
    icons = lambda sc: [r['icon'] for r in [sc['heroRole']]
                        + sc['supportingRoles']]
    assert 'trend up' in icons(up)
    assert 'trend down' in icons(down)
    assert any(r.get('bubble') == 'exclaim'
               for r in [down['heroRole']] + down['supportingRoles'])


def _roles(sent):
    sc = pa.build_storyboard('## A\n' + sent + '\n')['beats'][0]['scene']
    return {r['label']: r for r in [sc['heroRole']] + sc['supportingRoles']}


def test_target_stays_in_the_actors_clause():
    r = _roles('The judge reads the verdict and the family feels relieved.')
    assert r['judge']['target'] == 'verdict'


def test_piece_of_material_draws_the_material():
    r = _roles('The geologist holds a small nugget of gold.')
    assert 'nugget' not in r and r['gold'].get('attach') == 'held'


def test_tools_named_by_agent_or_verb_are_held():
    assert _roles('The guitarist plays for a cheering crowd.')[
        'guitar'].get('attach') == 'held'
    assert _roles('The carpenter saws the plank.')['saw'].get(
        'attach') == 'held'
    assert pa._verb_tool('hammer') == 'hammer'
    assert pa._verb_tool('feel') == ''


def test_script_heading_is_the_title():
    sb = pa.build_storyboard('# How Bread Is Made\n## Dough\n'
                             'A baker kneads the dough.\n')
    assert sb['title'] == 'How Bread Is Made'


def test_long_scene_draws_every_sentence():
    para = ('A farmer walks to the barn. He feeds the cows. '
            'The dog chases a cat. A truck arrives at the gate. '
            'The driver loads the milk. The sun sets over the hills. '
            'The farmer rests on the porch.')
    sc = pa.build_storyboard('## Day\n' + para + '\n')['beats'][0]['scene']
    roles = [sc['heroRole']] + sc['supportingRoles']
    assert len(sc['moments']) == 6
    assert {r.get('moment') for r in roles} == set(range(6))
    ats = [m['at'] for m in sc['moments']]
    assert ats[0] == 0.0 and ats == sorted(ats) and ats[-1] < 1.0


def test_merge_moments_keeps_all_words():
    s = ['a b', 'c', 'd e f', 'g', 'h i', 'j', 'k l m']
    out = pa._merge_moments(s, 6)
    assert len(out) == 6 and ' '.join(out).split() == ' '.join(s).split()


def _graph(text):
    sc = pa.build_storyboard(text)['beats'][0]['scene']
    roles = [sc['heroRole']] + sc['supportingRoles']
    return sc, roles


def test_explainer_scene_becomes_a_linked_diagram():
    sc, roles = _graph(
        '## Seeds\nA farmer sells grain to a mill. The mill turns the grain '
        'into flour. A bakery buys the flour from the mill. The bread '
        'reaches the shop in the town.\n')
    assert sc['layout'] == 'graph'
    edges = sc['graph']['edges']
    labs = [r['label'] for r in roles]
    names = {(labs[e['from']], labs[e['to']]) for e in edges}
    assert len(edges) >= 3
    assert all(e['from'] != e['to'] for e in edges)
    assert any('mill' in pair for pair in names)
    for r in roles:
        ann = str(r.get('annotate') or '')
        assert not ann or ann.split()[0] not in ('sells', 'buys', 'turns')


def test_diagram_merges_one_person_under_two_names():
    sc, roles = _graph(
        '## Care\nMaria trusts the nurse. The nurse checks the chart. '
        'If she loses the chart, the doctor reads a copy.\n')
    if sc.get('layout') != 'graph':
        pytest.skip('scene drawn as a story')
    labs = [r['label'] for r in roles]
    assert all(labs[e['from']] != 'doctor' or e['text'] != 'loses'
               for e in sc['graph']['edges'])


def test_physical_story_stays_a_story():
    sc, _ = _graph(
        '## Tea\nGrandma pours tea from the pot into a cup. Her grandson '
        'sits by the window and watches the ship. He drinks the tea.\n')
    assert sc.get('layout') != 'graph'
