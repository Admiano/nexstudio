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
