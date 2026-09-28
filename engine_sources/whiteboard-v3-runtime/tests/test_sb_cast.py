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
