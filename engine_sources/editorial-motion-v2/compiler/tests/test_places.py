from editorial_plan_compiler.places import BY_NAME, covered, place_of, story_places


def test_named_places_pick_their_own_environment():
    cases = {
        'On the farm, a tractor rolled past the barn.': 'farm',
        'At the airport, a plane waited on the runway.': 'airport',
        'In the stadium, the striker kicked the ball into the goal.': 'stadium',
        'That night, a rocket flew into space.': 'space',
        'The boat rocked in the harbour.': 'harbour',
        'A camel walked across the desert.': 'desert',
    }
    for text, want in cases.items():
        assert place_of(text, None) == want, text


def test_interior_words_move_the_story_inside_the_right_room():
    assert place_of('At school, the teacher wrote on the chalkboard.', None) == 'classroom'
    assert place_of('Back home, Sam fell asleep in bed.', None) == 'bedroom'
    assert place_of('Inside the kitchen, Grandma baked bread.', None) == 'kitchen'
    assert place_of('She lit the lamp by the window.', 'cottage') == 'home'
    assert place_of('Outside, the snowman melted.', 'home') == 'cottage'


def test_place_carries_to_pages_that_name_none_and_winter_sticks():
    where = story_places(['Snow covered the cabin on the mountain.', 'A bird sang.', 'In summer the farm was green.'])
    assert [w.place for w in where] == ['cottage', 'cottage', 'farm']
    assert [w.winter for w in where] == [True, True, False]
    assert where[0].far == ('mountains',)


def test_a_painted_place_answers_its_own_nouns():
    farm = covered('farm')
    assert {'farm', 'barn', 'silo', 'tractor', 'fence'} <= farm
    assert {'house', 'window', 'room'} <= covered('home')
    assert 'mountain' in covered('cottage', ('mountains',))
    assert all(p.dressing or p.painter == 'underwater' for p in BY_NAME.values())
