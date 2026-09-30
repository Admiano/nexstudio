import plan_author as pa
import sb_activity
import sb_cast


def test_explicit_female_and_male_words():
    assert sb_cast.look_for({'label': 'woman'})['sex'] == 'f'
    assert sb_cast.look_for({'label': 'mother'})['sex'] == 'f'
    assert sb_cast.look_for({'label': 'man'})['sex'] == 'm'
    assert sb_cast.look_for({'label': 'father'})['sex'] == 'm'


def test_label_beats_pronoun_vote_and_role_gender_is_used():
    assert sb_cast.look_for({'label': 'girl', 'gender': 'm'})['sex'] == 'f'
    assert sb_cast.look_for({'label': 'pilot', 'gender': 'f'})['sex'] == 'f'
    assert sb_cast.look_for({'label': 'pilot'})['sex'] == 'm'


def test_women_have_no_beard_and_look_is_deterministic():
    for lab in ('woman', 'nurse', 'farmer', 'pilot', 'chef'):
        a = sb_cast.look_for({'label': lab, 'gender': 'f'})
        assert a['beard'] in (None, '', 'none')
        assert a == sb_cast.look_for({'label': lab, 'gender': 'f'})


def test_rugged_trades_get_facial_hair_more_than_formal_jobs():
    rugged = ('farmer', 'fisherman', 'blacksmith', 'lumberjack', 'sailor',
              'carpenter', 'miner', 'shepherd')
    formal = ('lawyer', 'banker', 'accountant', 'judge', 'clerk',
              'manager', 'doctor', 'pilot')

    def bearded(labs):
        return sum(sb_cast.look_for({'label': x})['beard']
                   not in (None, '', 'none') for x in labs)
    assert bearded(rugged) > bearded(formal)


def test_hair_styles_vary_across_cast():
    labs = ('woman', 'mother', 'nurse', 'teacher', 'sister', 'queen',
            'aunt', 'lady')
    styles = {sb_cast.look_for({'label': x, 'gender': 'f'})['hair']
              for x in labs}
    assert len(styles) >= 3


def test_children_are_flagged_and_smaller():
    assert sb_cast.look_for({'label': 'girl'})['child']
    assert sb_cast.look_for({'label': 'little boy'})['child']
    assert sb_cast.look_for({'label': 'baker', 'age': 'child'})['child']
    assert not sb_cast.look_for({'label': 'farmer'})['child']
    assert 0.5 < sb_cast.CHILD_SCALE < 0.8


def test_female_and_male_figures_draw_differently():
    f = dict(sb_cast.outfit_for('farmer'),
             **sb_cast.look_for({'label': 'farmer', 'gender': 'f'}))
    m = dict(sb_cast.outfit_for('farmer'),
             **sb_cast.look_for({'label': 'farmer', 'gender': 'm'}))
    bf = sb_cast.figure('neutral', outfit=f)[0]
    bm = sb_cast.figure('neutral', outfit=m)[0]
    assert bf != bm


def test_pronouns_bind_sex_and_both_sexes_share_a_scene():
    sb = pa.build_storyboard(
        '## Market\nThe farmer loaded the cart with apples. She drove it '
        'to the market. The baker waved at the farmer and he bought a '
        'crate. His little son carried a basket.\n')
    roles = [r for b in sb['beats'] for r in
             [b['scene']['heroRole']] + b['scene']['supportingRoles']
             if r.get('icon') == 'person']
    sex = {r['label']: sb_cast.look_for(r)['sex'] for r in roles}
    assert sex.get('farmer') == 'f'
    assert sex.get('baker') == 'm'
    son = [r for r in roles if r['label'] == 'son']
    assert son and sb_cast.look_for(son[0])['child']


def test_second_climb_surface_becomes_backdrop():
    spec = sb_activity.resolve('climb', [('dobj', 'ladder'),
                                         ('into', 'apple tree')])
    assert spec['partner'] == 'ladder'
    assert 'apple tree' in spec['setting']
    assert 'apple tree' not in spec['absorb']
    tree = [([(0.0, 0.0), (0.0, -100.0)], 'ink', 3.0, False)]
    plain = sb_activity.compose(spec)
    backed = sb_activity.compose(spec, backdrop=[tree])
    assert backed[3]['backdrop'] == 1
    assert len(backed[0]) > len(plain[0])
    assert sb_activity.contact_error(backed[3]) <= 0.08


def test_noun_labels_are_short():
    def lab(label, ann):
        r = {'label': label, 'annotate': ann, 'icon': 'x'}
        pa._noun_labels([{'scene': {'heroRole': r, 'supportingRoles': []}}])
        return r.get('annotate')
    assert lab('ladder', 'climbed tall ladder') == 'tall ladder'
    assert lab('wheelbarrow', 'pushed wheelbarrow apples') == \
        'pushed wheelbarrow'
    assert lab('sun', 'went down') is None
    assert len((lab('basket', 'dropped them basket') or '').split()) <= 2


def test_activity_partner_is_not_drawn_twice():
    roles = [{'label': 'driver', 'icon': 'person', 'moment': 0},
             {'label': 'truck', 'icon': 'x', 'moment': 0},
             {'label': 'driver', 'icon': 'person', 'moment': 1,
              'activity': {'schema': 'drive', 'partner': 'truck'},
              'target': 3},
             {'label': 'truck', 'icon': 'x', 'moment': 1,
              'attach': 'activity', 'to': 2}]
    pa._one_drawing(roles)
    assert [r['label'] for r in roles].count('truck') == 1
    assert roles[1]['target'] == 2 and roles[2]['to'] == 1
    assert roles[1]['activity']['partner'] == roles[2]['label']
