import pytest

import plan_author as pa
import sb_activity as A


def _roles(text):
    sc = pa.build_storyboard('## A\n' + text + '\n')['beats'][0]['scene']
    return {r['label']: r for r in [sc['heroRole']] + sc['supportingRoles']}


@pytest.mark.parametrize('lemma,objs,schema', [
    ('drive', [('dobj', 'truck')], 'drive'),
    ('steer', [('dobj', 'car')], 'drive'),
    ('climb', [('dobj', 'mountain')], 'climb'),
    ('scale', [('dobj', 'cliff')], 'climb'),
    ('ride', [('dobj', 'horse')], 'ride'),
    ('ride', [('dobj', 'bicycle')], 'ride'),
    ('swim', [('across', 'lake')], 'swim'),
    ('dig', [('dobj', 'hole')], 'dig'),
    ('sip', [('dobj', 'tea')], 'drink'),
    ('carry', [('dobj', 'box')], 'carry'),
])
def test_verb_resolves_to_motor_schema(lemma, objs, schema):
    assert A.resolve(lemma, objs)['schema'] == schema


def test_abstract_verbs_have_no_activity():
    for v in ('believe', 'seem', 'feel'):
        assert A.resolve(v, [('dobj', 'idea')]) is None
        assert not A.is_physical(v)


@pytest.mark.parametrize('lemma,objs', [
    ('drive', [('dobj', 'truck')]), ('climb', [('dobj', 'mountain')]),
    ('ride', [('dobj', 'horse')]), ('swim', [('across', 'lake')]),
    ('dig', [('dobj', 'hole')]), ('sip', [('dobj', 'tea')]),
    ('carry', [('dobj', 'box')]), ('push', [('dobj', 'cart')]),
])
def test_limbs_meet_their_contacts(lemma, objs):
    got = A.compose(A.resolve(lemma, objs))
    assert got is not None
    strokes, _marks, anch, meta = got
    assert strokes and 'hand_n' in anch
    assert A.contact_error(meta) <= 0.08


def test_seated_actor_then_hands_activity_merge():
    r = _roles('The ranger sat on a bench and read a logbook.')
    assert r['ranger']['activity']['schema'] == 'sit_read'


def test_driver_binds_vehicle_into_the_picture():
    r = _roles('The farmer drove his old truck to the market.')
    act = r['farmer']['activity']
    assert act['schema'] == 'drive' and act['partner'] == 'truck'
    assert r['truck']['attach'] == 'activity'


def test_each_actor_keeps_its_own_activity():
    r = _roles('The girl swam across the lake. A boy rode a horse.')
    assert r['girl']['activity']['schema'] == 'swim'
    assert r['boy']['activity']['schema'] == 'ride'
    assert r['horse']['to'] != r['lake']['to']


def test_hand_schemas_keep_objects_held():
    r = _roles('The hiker carried a heavy box up the road.')
    assert r['box']['attach'] == 'held'
