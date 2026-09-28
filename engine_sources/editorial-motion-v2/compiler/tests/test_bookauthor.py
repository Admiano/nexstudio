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
