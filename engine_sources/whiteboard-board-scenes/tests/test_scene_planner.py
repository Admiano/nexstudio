import json

import plan_author as pa
import sb_activity as A
import scene_planner as sp


def _scene(text):
    return pa.build_storyboard('## A\n' + text + '\n')['beats'][0]['scene']


def _roles(sc):
    return [sc['heroRole']] + sc['supportingRoles']


def _who(sc, label, k):
    return next(r for r in _roles(sc) if r['label'] == label
                and r.get('moment') == k)


def _plan(moments, place='room', fixtures=()):
    raw = {'place': place, 'fixtures': list(fixtures), 'moments': moments}
    return sp._clean(raw, len(moments))


def _p(name, action, **kw):
    return {'name': name, 'action': action, 'object': kw.get('object', ''),
            'on': kw.get('on', ''), 'with_person': '', 'holding':
            kw.get('holding', ''), 'wearing': kw.get('wearing', ''),
            'expression': kw.get('expression', 'neutral')}


def test_disabled_planner_returns_none(monkeypatch):
    monkeypatch.setenv('NEXSTUDIO_SCENE_LLM', 'off')
    assert sp.plan(['Ann sits.']) is None


def test_cached_plan_is_reused(monkeypatch, tmp_path):
    monkeypatch.setenv('NEXSTUDIO_SCENE_LLM', '')
    monkeypatch.setattr(sp, '_CACHE', str(tmp_path))
    calls = []

    def fake(prompt):
        calls.append(prompt)
        return json.dumps({'place': 'Kitchen!', 'fixtures': ['stove'],
                           'moments': [{'sentence': 0, 'place': '',
                                        'people': [], 'things': []}]})
    monkeypatch.setattr(sp, 'available', lambda: True)
    monkeypatch.setattr(sp, '_complete', fake)
    a = sp.plan(['Ann cooks soup.'])
    b = sp.plan(['Ann cooks soup.'])
    assert a == b and a['place'] == 'kitchen' and len(calls) == 1


def test_clean_drops_bad_moments_and_unknown_actions():
    got = sp._clean({'place': 'x', 'fixtures': [], 'moments': [
        {'sentence': 5, 'people': [], 'things': []},
        {'sentence': 0, 'people': [_p('ann', 'levitate')], 'things': []},
        {'sentence': 0, 'people': [], 'things': []}]}, 1)
    assert len(got['moments']) == 1
    assert got['moments'][0]['people'][0]['action'] == 'stand'


def test_invalid_cache_is_replaced_by_a_complete_plan(monkeypatch, tmp_path):
    monkeypatch.setenv('NEXSTUDIO_SCENE_LLM', '')
    monkeypatch.setattr(sp, '_CACHE', str(tmp_path))
    monkeypatch.setattr(sp, 'available', lambda: True)
    monkeypatch.setattr(sp, '_complete', lambda prompt: json.dumps({
        'place': 'kitchen', 'fixtures': [],
        'moments': [{'sentence': 0, 'people': [], 'things': ['cup']}]}))
    assert sp.plan(['Ann washes a cup.'])['place'] == 'kitchen'
    cache = next(tmp_path.iterdir())
    cache.write_text('{"moments":')
    assert sp.plan(['Ann washes a cup.'])['moments'][0]['things'] == ['cup']
    assert json.loads(cache.read_text())['place'] == 'kitchen'


def test_concrete_things_only():
    for w in ('piano', 'umbrella', 'cup', 'dog', 'bread'):
        assert sp.concrete(w), w
    for w in ('song', 'mistake', 'rhythm', 'knee', 'afternoon', 'joy'):
        assert not sp.concrete(w), w


def test_plan_replaces_verb_only_reading_with_context():
    sc = _scene('Leo sits at the organ. He plays a hymn.')
    leo = _who(sc, 'leo', 1)
    plan = _plan([{'sentence': 0, 'people': [_p('leo', 'sit')],
                   'things': []},
                  {'sentence': 1, 'people': [_p('leo', 'play',
                                                object='organ')],
                   'things': ['organ']}], fixtures=['organ'])
    sp.apply(sc, plan, ['Leo sits at the organ.', 'He plays a hymn.'])
    act = leo['activity']
    assert act['schema'] == 'play' and act['kind'] == 'keyboard'
    organ = next(r for r in _roles(sc) if r['label'] == 'organ'
                 and r.get('moment') == 1)
    assert organ.get('to') == _roles(sc).index(leo)
    hymn = [r for r in _roles(sc) if r['label'] == 'hymn']
    assert all(r.get('absorbed') for r in hymn)


def test_own_body_gesture_not_an_object():
    sents = ['Sam sits on a stool.', 'Sam taps the beat on his knee.']
    sc = _scene(' '.join(sents))
    sp.apply(sc, _plan([{'sentence': 0, 'people': [_p('sam', 'sit')],
                         'things': []},
                        {'sentence': 1, 'people': [
                            _p('sam', 'tap', object='knee')],
                         'things': []}]), sents)
    sam = _who(sc, 'sam', 1)
    assert sam['activity']['schema'] == 'tap'
    assert sam['activity'].get('partner') is None
    shown = [r['label'] for r in _roles(sc) if r.get('icon') != 'person'
             and not r.get('absorbed') and not r.get('body_part')]
    assert not {'knee', 'beat', 'tap'} & set(shown)


def test_planner_never_adds_people_or_drops_narrated_ones():
    sents = ['Nora sits beside her uncle.']
    sc = _scene(sents[0])
    before = {r['label'] for r in _roles(sc) if r.get('icon') == 'person'}
    notes = sp.apply(sc, _plan([{'sentence': 0, 'people': [
        _p('nora', 'sit'), _p('stranger', 'wave')], 'things': []}]), sents)
    after = {r['label'] for r in _roles(sc) if r.get('icon') == 'person'}
    assert before == after and 'uncle' in after
    assert {'reject': 'person', 'moment': 0, 'name': 'stranger'} in notes


def test_fixture_needs_a_narrated_thing_and_skips_unrelated_places():
    sents = ['Ivy walks to the piano teacher.', 'She waves.']
    sc = _scene(' '.join(sents))
    sp.apply(sc, _plan([{'sentence': 0, 'people': [_p('ivy', 'walk')],
                         'things': []},
                        {'sentence': 1, 'people': [_p('ivy', 'wave')],
                         'things': []}], fixtures=['piano']), sents)
    assert not any(r['label'] == 'piano' for r in _roles(sc))


def test_implied_things_are_capped():
    sents = ['Kai waits at the bus stop in the rain.']
    sc = _scene(sents[0])
    n0 = len(_roles(sc))
    sp.apply(sc, _plan([{'sentence': 0, 'people': [
        _p('kai', 'stand', holding='umbrella')],
        'things': ['bench', 'sign', 'lamp', 'bag']}]), sents)
    added = [r for r in _roles(sc)[n0:]]
    assert len(added) <= sp._MAX_IMPLIED
    assert any(r['label'] == 'umbrella' and r.get('attach') == 'held'
               for r in added)


def test_gestures_are_drawn_standing_and_seated():
    for g in sorted(A.GESTURES):
        for posture in ('', 'sit'):
            spec = A.resolve(g, (), posture, schema=g)
            got = A.compose(spec, None)
            assert got is not None, (g, posture)
            assert A.contact_error(got[3]) is None or \
                A.contact_error(got[3]) < 0.06, (g, posture)


def test_play_without_instrument_context_keeps_plan_schema():
    spec = A.resolve('play', [('dobj', 'piano')], '', schema='play')
    assert spec['schema'] == 'play' and spec['kind'] == 'keyboard'


def test_incomplete_model_response_is_not_cached(monkeypatch, tmp_path):
    monkeypatch.setenv('NEXSTUDIO_SCENE_LLM', '')
    monkeypatch.setattr(sp, '_CACHE', str(tmp_path))
    monkeypatch.setattr(sp, 'available', lambda: True)
    monkeypatch.setattr(sp, '_complete', lambda prompt: json.dumps({
        'place': 'studio', 'fixtures': [], 'moments': [
            {'sentence': 0, 'people': [], 'things': []}]}))
    assert sp.plan(['Jo arrives.', 'She waves.']) is None
    assert not list(tmp_path.iterdir())


def test_required_things_are_not_truncated():
    things = ['cup', 'plate', 'fork', 'spoon', 'bowl', 'pan', 'jug', 'knife']
    got = sp._clean({'moments': [
        {'sentence': 0, 'things': things}]}, 1)
    assert got['moments'][0]['things'] == things


def test_another_persons_action_cannot_be_assigned_to_a_named_bystander():
    sent = 'Lena drinks tea while Omar waits beside a table.'
    sc = _scene(sent)
    plan = _plan([{'sentence': 0, 'place': 'room', 'people': [
        _p('omar', 'drink', object='cup', holding='cup')], 'things': []}])
    notes = sp.apply(sc, plan, [sent])
    omar = _who(sc, 'omar', 0)
    assert (omar.get('activity') or {}).get('schema') != 'drink'
    assert any(n.get('reject') == 'unstated-action' for n in notes)


def test_an_invented_location_does_not_replace_the_narrated_workplace():
    sents = ['Lena sits in a workshop.', 'She fixes a bicycle.']
    sc = _scene(' '.join(sents))
    places = list(sc['places'])
    plan = _plan([{'sentence': k, 'place': 'street', 'people': [],
                   'things': []} for k in range(2)], place='street')
    sp.apply(sc, plan, sents)
    assert sc['places'] == places
    assert all(place != 'outdoor' for place in sc['places'])


def test_context_can_correct_a_valid_but_wrong_template():
    sents = ['Sam taps the rhythm on his knee.']
    sc = _scene(sents[0])
    sam = next(r for r in _roles(sc) if r['label'] == 'sam')
    sam['activity'] = {'schema': 'cut', 'kind': '', 'lemma': 'tap',
                       'via': 'wordnet', 'partner': 'knife'}
    sp.apply(sc, _plan([{'sentence': 0, 'people': [
        _p('sam', 'tap')], 'things': []}]), sents)
    assert sam['activity']['schema'] == 'tap'
    assert sam['activity']['via'] == 'scene-plan'


def test_fixtures_persist_only_in_their_location():
    sents = ['Lena reads a book in bed.', 'She smiles.',
             'She walks into the garden.']
    sc = _scene(' '.join(sents))
    plan = _plan([
        {'sentence': 0, 'place': 'bedroom',
         'people': [_p('lena', 'read', object='book')], 'things': ['bed']},
        {'sentence': 1, 'place': 'bedroom',
         'people': [_p('lena', 'stand')], 'things': []},
        {'sentence': 2, 'place': 'garden',
         'people': [_p('lena', 'walk')], 'things': []}],
        place='bedroom', fixtures=['bed'])
    sp.apply(sc, plan, sents)
    assert any(r['label'] == 'bed' and r.get('moment') == 1
               for r in _roles(sc))
    assert not any(r['label'] == 'bed' and r.get('moment') == 2
                   for r in _roles(sc))
    assert sc['places'] == ['bedroom', 'bedroom', 'outdoor']


def test_mentions_match_nouns_not_prefixes():
    assert sp._mentioned('cup', 'She washes two cups.')
    assert not sp._mentioned('car', 'She carries a basket.')


def test_planned_pouring_preserves_source_and_destination():
    sents = ['Nora pours tea from a teapot into a cup.']
    sc = _scene(sents[0])
    person = next(r for r in _roles(sc) if r['label'] == 'nora')
    person['activity'] = A.resolve('pour', [
        ('dobj', 'tea'), ('from', 'teapot'), ('into', 'cup')])
    sp.apply(sc, _plan([{'sentence': 0, 'people': [
        _p('nora', 'pour', object='tea')], 'things': ['teapot', 'cup']}]),
        sents)
    assert person['activity']['roles'] == {
        'theme': 'tea', 'source': 'teapot', 'goal': 'cup'}
