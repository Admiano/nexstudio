"""Scene map: who does what to whom, which way things change, and how."""
import pytest

import scene_map as sm

pytestmark = pytest.mark.skipif(not sm.available(),
                                reason='spaCy model not installed')


def _ev(m, lemma):
    return next(e for e in m['events'] if e['lemma'] == lemma)


def _lab(m, eid):
    return m['entities'][eid]['label'] if eid is not None else None


def test_subject_object_and_coordination():
    m = sm.parse('A hopeful trader sips coffee and opens her laptop.', {})
    sip, opn = _ev(m, 'sip'), _ev(m, 'open')
    assert (_lab(m, sip['agent']), _lab(m, sip['patient'])) == (
        'trader', 'coffee')
    assert (_lab(m, opn['agent']), _lab(m, opn['patient'])) == (
        'trader', 'laptop')
    assert {'word': 'hopeful', 'kind': 'quality', 'of': 0} in m['states']


def test_verb_read_as_noun_is_repaired():
    m = sm.parse('The price jumps and she cheers.', {'she': 'trader'})
    assert _ev(m, 'jump')['kind'] == 'rise'
    m = sm.parse('The alarm rings and the firefighters grab their helmets.',
                 {})
    grab = _ev(m, 'grab')
    assert _lab(m, grab['agent']) == 'firefighter'
    assert _lab(m, grab['patient']) == 'helmet'


def test_gendered_pronouns_follow_the_right_person():
    carry: dict = {}
    sm.parse('The baker mixes flour.', carry)
    sm.parse('She kneads the dough.', carry)
    sm.parse('An old neighbor arrives.', carry)
    sm.parse('He hands the stove to the baker.', carry)
    m = sm.parse('She lights the flame.', carry)
    assert _lab(m, _ev(m, 'light')['agent']) == 'baker'


def test_possessive_and_group_keep_singular_referent():
    carry = {}
    sm.parse('Asha opens the workshop.', carry)
    sm.parse('Her two assistants carry a toolbox.', carry)
    sm.parse('Asha and her assistants wave from the doorway.', carry)
    m = sm.parse('She closes the door.', carry)
    assert _lab(m, _ev(m, 'close')['agent']) == 'asha'
    assert carry['they'] == 'assistant'


def test_gendered_people_remain_distinct_after_an_interaction():
    carry = {}
    sm.parse('A woman greets a man.', carry)
    m = sm.parse('He sits on the bench.', carry)
    assert _lab(m, _ev(m, 'sit')['agent']) == 'man'
    m = sm.parse('She waves from the doorway.', carry)
    assert _lab(m, _ev(m, 'wave')['agent']) == 'woman'


def test_named_subject_restores_gendered_reference_after_another_female():
    carry = {}
    sm.parse('Rita, a female librarian, walks with a girl and a boy.', carry)
    sm.parse('The girl reads a book.', carry)
    sm.parse('Rita opens the door with the children.', carry)
    m = sm.parse('She carries a basket.', carry)
    assert _lab(m, _ev(m, 'carry')['agent']) == 'rita'


@pytest.mark.parametrize('sent,lemma,kind,way', [
    ('She panics as the chart crashes.', 'crash', 'destroy', 'down'),
    ('She panics as the chart crashes.', 'panic', 'fear', ''),
    ('A small boat drifts toward the reef.', 'drift', 'move', ''),
    ('He thinks about the ships.', 'think', 'think', ''),
    ('She dreams of happy customers.', 'dream', 'think', ''),
    ('The vintner picks ripe grapes.', 'pick', 'act', ''),
    ('The cashier hands a loaf to a customer.', 'hand', 'transfer', ''),
    ('Sales jump before noon.', 'jump', 'rise', 'up'),
])
def test_event_kinds(sent, lemma, kind, way):
    ev = _ev(sm.parse(sent, {}), lemma)
    assert (ev['kind'], ev['dir']) == (kind, way)


def test_prepositions_datives_and_negation():
    m = sm.parse('A small boat drifts toward the reef.', {})
    assert [(p, _lab(m, e)) for p, e in _ev(m, 'drift')['preps']] == [
        ('toward', 'reef')]
    m = sm.parse('A vet nurse gives the puppy a small injection.', {})
    give = _ev(m, 'give')
    assert _lab(m, give['agent']) == 'vet nurse'
    assert ('to', 1) in give['preps'] and _lab(m, 1) == 'puppy'
    rise = _ev(sm.parse('The dough stops rising.', {}), 'rise')
    assert rise['neg'] and rise['dir'] == ''


def test_partitive_draws_members_and_plural_words_keep_meaning():
    m = sm.parse('She dreams of a line of happy customers.', {})
    line = next(e for e in m['entities'] if e['head'] == 'line')
    assert _lab(m, line['partitive']) == 'customer'
    m = sm.parse('The keeper climbs the stairs and sorts letters.', {})
    heads = {e['head'] for e in m['entities']}
    assert {'stairs', 'letter'} <= heads


def test_counted_physical_things_keep_their_exact_count():
    m = sm.parse('Maya pours water into three cups.', {})
    cups = next(e for e in m['entities'] if e['head'] == 'cup')
    assert cups['count'] == 3


def test_qualified_group_members_keep_their_own_actions():
    m = sm.parse('The older apprentice holds a flashlight while '
                 'the younger apprentice brings a pump.', {})
    assert _lab(m, _ev(m, 'hold')['agent']) == 'older apprentice'
    assert _lab(m, _ev(m, 'bring')['agent']) == 'younger apprentice'


def test_determined_argument_is_a_noun_and_prepositions_link():
    m = sm.parse('A student in another country can buy the same token '
                 'from his laptop.', {})
    buy = _ev(m, 'buy')
    assert (_lab(m, buy['agent']), _lab(m, buy['patient'])) == (
        'student', 'token')
    links = {(_lab(m, a), p, _lab(m, b)) for a, p, b in m['links']}
    assert ('student', 'in', 'country') in links
    assert ('token', 'from', 'laptop') in links


def test_of_links_owner_but_not_partitives():
    m = sm.parse('The token follows the price of the real stock.', {})
    links = {(_lab(m, a), p, _lab(m, b)) for a, p, b in m['links']}
    assert ('price', 'of', 'stock') in links
    m = sm.parse('He eats a piece of bread.', {})
    assert not any(p == 'of' for _, p, _ in m['links'])
