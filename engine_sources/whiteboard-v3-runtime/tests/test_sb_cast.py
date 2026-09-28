import sb_cast


def test_emotion_from_context_words():
    assert sb_cast.emotion_for({'annotate': 'FOMO'}) == 'excited'
    assert sb_cast.emotion_for({'annotate': 'PANIC'}) == 'panic'
    assert sb_cast.emotion_for({'annotate': 'you stay rational'}) == 'calm'
    assert sb_cast.emotion_for({'label': 'nurse',
                                'annotate': 'overworked and tired'}) == 'defeated'
    assert sb_cast.emotion_for({'label': 'driver'}) == 'neutral'


def test_explicit_emotion_wins():
    assert sb_cast.emotion_for({'annotate': 'PANIC', 'emotion': 'calm'}) == 'calm'


def test_every_emotion_builds_a_still():
    for emo in sb_cast.EMOTIONS:
        for flip in (False, True):
            body, marks, head = sb_cast.figure(emo, flip)
            assert body and all(len(s[0]) >= 2 for s in body + marks)
            assert head[0] < head[2] and head[1] < head[3]


def test_outfit_from_role_words():
    assert sb_cast.outfit_for('farmer')['hat'] == 'straw'
    assert sb_cast.outfit_for('lawyer')['torso'] == 'tie'
    assert sb_cast.outfit_for('fisherman')['hat'] == 'bucket'
    assert sb_cast.outfit_for('pilot')['hat'] == 'pilot'
    assert sb_cast.outfit_for('park ranger')['hat'] == 'ranger'
    assert sb_cast.outfit_for('commuter') == {}


def test_engaged_figures_build_for_every_outfit():
    for pat, fit in sb_cast._OUTFITS:
        for act in ('reach', 'hold', 'point', ''):
            body, _m, _h = sb_cast.figure('content', True, act, outfit=fit)
            assert body
