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
