from editorial_plan_compiler.bookauthor import BookAuthor, edu_of


def test_number_headed_nouns_are_things_and_operators_are_not():
    things = BookAuthor().things('Two more sheep came to play. Five plus two makes seven.')
    assert things == ['sheep']


def test_operands_follow_the_spoken_operator():
    text = 'Two more sheep came to play. Five plus two makes seven.'
    assert edu_of(text, ['sheep']) == {'kind': 'add', 'object': 'sheep', 'a': 5, 'b': 2}


def test_rows_of_things_is_a_multiplication():
    a = BookAuthor()
    text = 'Three rows of apples, four in each row. Three times four is twelve.'
    things = a.things(text)
    assert things == ['apple']
    assert edu_of(text, things)['kind'] == 'multiply'


def test_landforms_are_painted_by_the_scene_not_stickered():
    assert 'hill' not in BookAuthor().things('Sam flew a red kite over the hill.')


def test_irregular_plural_titles():
    assert BookAuthor.title([], {'kind': 'count', 'object': 'sheep'}) == 'Count The Sheep'


def test_undrawable_noun_takes_its_nearest_drawable_ancestor():
    things = BookAuthor().things('Six icicles hung from the roof. Six take away two leaves four.')
    assert things == ['ice', 'house']
    assert edu_of('Six take away two leaves four.', things) == {'kind': 'subtract', 'object': 'ice', 'a': 6, 'b': 2}


def test_landforms_never_take_a_stand_in():
    assert BookAuthor().things('The little cabin sat on the hill.') == ['house']


def test_a_sentence_naming_nothing_continues_the_previous_page():
    g = [[{'text': w} for w in t.split()] for t in ('Six icicles hung from the roof.', 'Six take away two leaves four.')]
    beats = BookAuthor().author(g, 'x')['beats']
    assert beats[1]['page']['edu'] == {'kind': 'subtract', 'object': 'ice', 'a': 6, 'b': 2}


def test_roles_and_parts_print_as_their_next_best_thing():
    a = BookAuthor()
    assert a.things('Her brother poured cocoa into a mug.')[0] == 'boy'
    assert 'house' in a.things('Six icicles hung from the roof.')


def test_a_number_naming_a_printed_set_is_a_count_page():
    assert edu_of('Seven fish swam under the boat.', ['fish', 'boat']) == {'kind': 'count', 'object': 'fish', 'a': 7}
