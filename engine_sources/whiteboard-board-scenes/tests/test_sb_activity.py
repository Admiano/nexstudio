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


_BOX = [([(0.0, 0.0), (40.0, 0.0), (40.0, 40.0), (0.0, 40.0), (0.0, 0.0)],
         'ink', 1.0, False)]


@pytest.mark.parametrize('lemma,objs,roles', [
    ('pour', [('dobj', 'tea'), ('into', 'cup')],
     {'theme': 'tea', 'goal': 'cup'}),
    ('pour', [('dobj', 'water'), ('from', 'bucket'), ('onto', 'plant')],
     {'theme': 'water', 'source': 'bucket', 'goal': 'plant'}),
    ('water', [('dobj', 'plant'), ('with', 'hose')],
     {'goal': 'plant', 'instrument': 'hose'}),
    ('fill', [('dobj', 'bucket'), ('with', 'water')],
     {'goal': 'bucket', 'theme': 'water'}),
    ('watch', [('dobj', 'ship'), ('from', 'window')],
     {'theme': 'ship', 'vantage': 'window'}),
    ('load', [('dobj', 'sack'), ('onto', 'cart'), ('with', 'pitchfork')],
     {'theme': 'sack', 'goal': 'cart', 'instrument': 'pitchfork'}),
])
def test_sentence_roles_are_kept(lemma, objs, roles):
    assert A.resolve(lemma, objs)['roles'] == roles


def test_watcher_partner_is_what_is_watched_not_the_window():
    sp = A.resolve('watch', [('from', 'window'), ('dobj', 'ship')])
    assert sp['schema'] == 'look' and sp['partner'] == 'ship'


def test_vehicle_as_destination_is_not_driven():
    assert A.resolve('carry', [('dobj', 'box'), ('into', 'truck')])[
        'schema'] == 'carry'
    assert A.resolve('walk', [('to', 'car')])['schema'] == 'walk'
    assert A.resolve('drive', [('dobj', 'truck')])['schema'] == 'drive'


@pytest.mark.parametrize('label,kind', [
    ('window', 'opening'), ('doorway', 'opening'), ('microscope', 'optic'),
    ('binoculars', 'optic'), ('hut', 'place'), ('deck', 'place')])
def test_vantage_kind(label, kind):
    assert A.vantage_kind(label) == kind


def test_every_role_is_drawn_in_the_picture():
    for lemma, objs in (('pour', [('dobj', 'tea'), ('into', 'cup')]),
                        ('watch', [('from', 'window'), ('dobj', 'ship')]),
                        ('load', [('dobj', 'sack'), ('onto', 'cart'),
                                  ('with', 'pitchfork')])):
        sp = A.resolve(lemma, objs)
        got = A.compose(sp, _BOX if sp['partner'] else None,
                        role_arts={r: _BOX for r in sp['roles']})
        meta = got[3]
        assert meta['roles'] and all(meta['roles'].values()), (lemma, meta)
        assert A.contact_error(meta) <= 0.08


def test_pour_stream_lands_in_the_destination():
    sp = A.resolve('pour', [('dobj', 'tea'), ('into', 'cup')])
    meta = A.compose(sp, None, role_arts={'goal': _BOX})[3]
    names = {n for n, _a, _t in meta['contacts']}
    assert 'stream' in names and A.contact_error(meta) <= 0.02


def test_watcher_is_framed_by_the_window():
    sp = A.resolve('watch', [('from', 'window'), ('dobj', 'ship')])
    meta = A.compose(sp, _BOX, role_arts={'vantage': _BOX})[3]
    view = [(a, t) for n, a, t in meta['contacts'] if n == 'view']
    assert view and view[0][0] == view[0][1]


def test_missing_role_art_is_reported_not_hidden():
    sp = A.resolve('pour', [('dobj', 'tea'), ('into', 'cup')])
    assert A.compose(sp, None)[3]['roles'] == {'goal': False,
                                               'theme': True}


def test_facial_expression_is_not_an_activity_instrument():
    for expression in ('smile', 'frown', 'grin'):
        spec = A.resolve('sit', [('on', 'bench'), ('with', expression)])
        assert 'instrument' not in spec['roles']


def test_kneeling_posture_survives_later_hand_work():
    kneel = A.resolve('kneel', [('beside', 'bicycle')])
    fix = A.resolve('fix', [('dobj', 'wheel'), ('with', 'wrench')])
    merged = A.merge(kneel, fix)
    assert merged['schema'] == 'fix'
    assert merged['posture'] == 'kneel'


def test_boat_and_car_have_distinct_terrain():
    boat = A.resolve('drive', [('dobj', 'ferry'), ('across', 'bay')])
    car = A.resolve('drive', [('dobj', 'car'), ('across', 'bay')])
    assert 'bay' in boat['absorb']
    assert 'bay' not in car['absorb']


def test_activity_backdrop_stays_at_the_figure_scale():
    art = [([(0, 0), (2, 0), (2, 1), (0, 1)], 'ink', 1, False)]
    strokes, _marks, _anchors, meta = A.compose(
        A.resolve('kneel'), backdrop=[art], backdrop_sizes=[0.52])
    bounds = A._bbox(strokes)
    assert meta['backdrop'] == 1
    assert bounds[2] - bounds[0] < 2 * A.H
    assert bounds[3] - bounds[1] < 2 * A.H


def test_opening_a_building_draws_an_access_door():
    spec = A.resolve('open', [('dobj', 'workshop')])
    assert spec['kind'] == 'building'
    strokes, _marks, anchors, meta = A.compose(spec)
    assert meta['placed'] and meta['partner_bounds']
    assert A.contact_error(meta) <= 0.08
    x0, y0, x1, y1 = meta['partner_bounds']
    hand = anchors['hand_n']
    assert x0 <= hand[0] <= x1 and y0 <= hand[1] <= y1
    assert A._bbox(strokes)[3] - A._bbox(strokes)[1] < 2 * A.H


def test_water_source_is_drawn_as_a_local_patch():
    spec = A.resolve('lift', [('dobj', 'bucket'), ('from', 'pond')])
    strokes, _marks, _anchors, meta = A.compose(spec)
    assert meta['roles']['source']
    water = [s for s in strokes if s[1] == A.C['water']]
    assert water
    bounds = A._bbox(water)
    assert 0 < bounds[2] - bounds[0] <= 1.2 * A.H
    assert 0 < bounds[3] - bounds[1] < 0.2 * A.H


def test_plan_keeps_role_objects_attached_to_the_actor():
    rs = _roles('The keeper pours hot tea into three cups.')
    act = rs['keeper']['activity']
    assert act['schema'] == 'pour'
    assert act['roles'].get('goal') == rs['cup']['label']
    assert rs['cup']['attach'] == 'activity'
    rs = _roles('The fisherman watches the ship from the window.')
    act = rs['fisherman']['activity']
    assert act['roles'].get('vantage') == 'window'
    assert act['partner'] == 'ship'


def test_role_filled_by_the_scene_setting_is_left_to_the_backdrop():
    sc = pa.build_storyboard(
        '## A\nThe girl walks to the river with a jug. '
        'She fills the jug with water from the river.\n')['beats'][0]['scene']
    if sc.get('setting') != 'river':
        pytest.skip('setting not inferred as river')
    for r in [sc['heroRole']] + sc['supportingRoles']:
        act = r.get('activity') or {}
        assert 'river' not in (act.get('roles') or {}).values()
        assert 'river' not in (act.get('roles_lost') or {}).values()
