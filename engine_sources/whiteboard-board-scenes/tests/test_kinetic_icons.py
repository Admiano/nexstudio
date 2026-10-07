"""Sparse word icons for kinetic type: concrete nouns only, strict art
match, one per sentence, about one sentence in three, no repeats."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNTIME))

import pipeline_v3_narration_timed as pipe  # noqa: E402

try:
    pipe.resolve_execution_package()
    HAS_BODY = True
except FileNotFoundError:
    HAS_BODY = False

pytestmark = pytest.mark.skipif(not HAS_BODY,
                                reason='run scripts/install-engines.py first')

CONCRETE = ("Mark ties his shoes and checks his watch. He jogs past the park "
            "while the city wakes up. At the halfway point, he stops for a "
            "sip of water from his bottle. The last mile always feels the "
            "hardest. He finishes and smiles.")
ABSTRACT = ("Habits shape most of what we do each day. A habit begins with a "
            "cue, then a routine, then a reward. Over time, the brain learns "
            "to repeat that loop. That is why change feels hard at first.")


@pytest.fixture(scope='module')
def mods():
    pipe.load_execution_body(None)
    import kinetic_icons
    import pipeline_kinetic_timed as kp
    import plan_author as pa
    return kinetic_icons, kp, pa


def _sents(mods, script):
    ki, kp, pa = mods
    plan = pipe.normalize_plan(pa.build_plan(script, vtype='kinetic'))
    assert plan['icons'] == 'auto'
    return kp.sentences(plan, None)


def test_concrete_nouns_only(mods):
    ki = mods[0]
    for w in ('watch', 'bottle', 'pizza', 'football', 'shoes'):
        assert ki.concrete_noun(w), w
    for w in ('trust', 'habit', 'reward', 'plan', 'day', 'farmer'):
        assert not ki.concrete_noun(w), w


def test_verb_use_gets_no_icon(mods):
    ki = mods[0]
    assert not ki.candidates('They watch the sunset'.split())
    assert [c['phrase'] for c in ki.candidates(
        'He checks his watch.'.split())] == ['watch']


def test_concrete_script_is_sparse_and_exact(mods):
    sents, picks, issues = _sents(mods, CONCRETE)
    assert issues == []
    assert 1 <= len(picks) <= -(-len(sents) // 3)
    keys = sorted(picks)
    assert all(b - a > 1 for a, b in zip(keys, keys[1:]))
    for si, r in picks.items():
        w = sents[si]['words'][r['word']]
        assert sents[si]['icon'] is r
        assert r['rank'] <= mods[0].MAX_RANK
    assert {r['phrase'] for r in picks.values()} <= {
        'shoes', 'watch', 'water', 'bottle'}


def test_abstract_script_stays_text(mods):
    _sents_, picks, issues = _sents(mods, ABSTRACT)
    assert picks == {} and issues == []


def test_qa_flags_overuse(mods):
    ki = mods[0]
    sents, picks, _ = _sents(mods, CONCRETE)
    si, row = next(iter(picks.items()))
    bad = dict(picks)
    bad[si + 1] = dict(row, word=0)
    checks = {i['check'] for i in ki.qa(sents, bad)}
    assert {'icon-adjacent', 'icon-repeat'} <= checks


@pytest.mark.parametrize('size', [(540, 960), (960, 540), (720, 720)])
def test_icon_replaces_its_word_inline(mods, size):
    import kinetic_type_renderer as ktr
    sents, picks, _ = _sents(mods, CONCRETE)
    si, r = next(iter(picks.items()))
    spec = ktr.typeset(sents[si], ktr.base_size(*size, 'condensed'),
                       'condensed', size[0], frame_h=size[1])
    slots = [it for line in spec['lines'] for it in line]
    glyph = [it for it in slots if it.get('glyph')]
    assert len(glyph) == 1 and glyph[0]['i'] == r['word']
    assert 'icon_h' not in spec
    specs = [ktr.typeset(s, ktr.base_size(*size, 'condensed'), 'condensed',
                         size[0], frame_h=size[1]) for s in sents]
    w = sents[si]['words'][r['word']]
    t = w['start'] + 0.6
    frame = ktr.render_kinetic_frame(sents, specs, t, size, {}, 'condensed')
    # locate the glyph slot in the frame and check ink lands inside it
    sp = specs[si]
    y = size[1] * 0.46 - sp['block_h'] / 2
    for line in sp['lines']:
        total = sum(it['tw'] for it in line) + sp['gap'] * (len(line) - 1)
        x = (size[0] - total) / 2
        for it in line:
            if it.get('glyph'):
                box = (int(x), int(y), int(x + it['tw']),
                       int(y + sp['size'] * 1.15))
                assert 0 <= box[0] and box[2] <= size[0]
                assert 0 <= box[1] and box[3] <= size[1]
                lo = min(min(px) for px in frame.crop(box).getdata())
                assert lo < 160, 'icon ink drawn in the word slot'
            x += it['tw'] + sp['gap']
        y += sp['lh']
    # nothing above the text block: the icon is not a header
    top = frame.crop((0, 0, size[0], int(size[1] * 0.46
                                        - sp['block_h'] / 2) - 4))
    assert min(min(px) for px in top.getdata()) > 200
