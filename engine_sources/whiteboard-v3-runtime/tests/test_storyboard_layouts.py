"""Storyboard scene layouts, marker foley sync and hand sprite contracts."""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent
sys.path.insert(0, str(RUNTIME))

import marker_sfx  # noqa: E402
import pipeline_v3_narration_timed as pipe  # noqa: E402

try:
    pipe.resolve_execution_package()
    HAS_BODY = True
except FileNotFoundError:
    HAS_BODY = False

pytestmark = pytest.mark.skipif(not HAS_BODY,
                                reason='run scripts/install-engines.py first')


def _built(name):
    wbc, _wbp, _, v3r = pipe.load_execution_body()
    import v3_board_sections as bs
    plan = pipe.normalize_plan(
        json.loads((RUNTIME / 'fixtures' / name).read_text()))
    v3r.set_art_kit(plan.get('art_kit'))
    plan.update(wbc.compile_whiteboard_plan(plan, {'ratio': '16:9'}))
    return plan, bs, bs._build(plan, '16:9')


def test_word_alignment_recovers_after_spoken_number_replaces_written_words():
    plan = {'beats': [
        {'narration': 'I pay ten dollars. The wallet splits it.',
         'duration_seconds': 9},
        {'narration': 'Anyone trades from a phone.',
         'duration_seconds': 9},
    ]}
    transcript = [
        {'word': word, 'start': i * 0.4, 'end': i * 0.4 + 0.3}
        for i, word in enumerate(
            'I pay $10 The wallet splits it Anyone trades from a phone'.split())
    ]
    aligned = pipe.align_beats_to_words(plan, transcript)
    first, second = aligned['beats']
    assert first['word_times'][-1][0] == 'it'
    assert second['word_times'][0][0] == 'anyone'
    assert second['start_seconds'] < 3.0
    assert second['start_seconds'] >= first['start_seconds'] + first['duration_seconds']


def test_attached_prop_draws_when_it_is_spoken():
    _plan, bs, _flow = _built('storyboard_edge_plan.json')
    host = {'it': {'label': 'piece'}, 'kids': [
        {'it': {'label': 'wallet'}}]}
    windows = {id(host): (1.0, 4.0)}
    cues = []
    bs._sb_word_cues([host], [('wallet', 1.2, 1.4),
                              ('piece', 3.0, 3.2)],
                     1.0, 4.0, 4.0, windows, cues)
    assert windows[id(host)][0] == 1.2


def test_storyboard_keeps_opening_title_and_overlapping_scene_handoffs():
    plan, _bs, flow = _built('storyboard_edge_plan.json')
    title = flow['title_item']
    assert title['kind'] == 'title'
    assert title['groups'][0][2] <= plan['beats'][0]['duration_seconds']
    assert all(not sec['title_st'] for sec in flow['sections'])
    assert title['fade'][1] <= flow['sections'][1]['t_window'][0]
    for scene, next_scene in zip(flow['sections'], flow['sections'][1:]):
        next_start = next_scene['t_window'][0]
        assert scene['fade'][0] < next_start < scene['fade'][1]


def test_crypto_phone_depicts_mobile_trading():
    _wbc, _wbp, _, v3r = pipe.load_execution_body()
    v3r.set_art_kit('crypto')
    icon = v3r._icon_for('phone')
    assert icon == ('icon', 'kit:crypto', 'phone')
    assert v3r._dir_strokes(icon[1], icon[2])


@pytest.mark.parametrize('name, layouts', [
    ('storyboard_edge_plan.json', ['row', 'stair', 'journey', 'focus']),
    ('storyboard_stress_plan.json',
     ['before_after', 'cycle', 'reaction', 'row']),
])
def test_layout_per_relation_and_no_collisions(name, layouts):
    plan, _bs, flow = _built(name)
    assert [s.get('layout') for s in flow['sections']] == layouts
    assert not plan.get('_sb_audit')


def test_divider_only_in_contrast_scenes():
    _plan, _bs, flow = _built('storyboard_edge_plan.json')
    for sec in flow['sections']:
        assert sec['divider'] == (sec['relation'] == 'contrast')


def test_pen_spans_are_ordered_and_bounded():
    plan, bs, _flow = _built('storyboard_edge_plan.json')
    spans = bs.pen_spans(plan, '16:9')
    assert len(spans) > 50
    dur = sum(float(b['duration_seconds']) for b in plan['beats'])
    for (s0, e0, ln), nxt in zip(spans, spans[1:] + [None]):
        assert 0 <= s0 < e0 <= dur + 5 and ln >= 0
        if nxt:
            assert nxt[0] >= s0


def test_marker_foley_silent_between_strokes(tmp_path):
    ev = [{'start': 0.2, 'duration': 0.4, 'length': 300, 'gain': 1.0},
          {'start': 1.5, 'duration': 0.3, 'length': 120, 'gain': 1.0}]
    out = tmp_path / 'm.wav'
    marker_sfx.render(ev, 2.2, out)
    with wave.open(str(out)) as w:
        assert w.getframerate() == marker_sfx.RATE and w.getnchannels() == 1
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32767
    r = marker_sfx.RATE

    def rms(t0, t1):
        return float(np.sqrt(np.mean(a[int(t0 * r):int(t1 * r)] ** 2)))
    assert rms(0.3, 0.5) > 20 * max(rms(0.9, 1.4), 1e-5)
    assert rms(0.0, 0.18) < rms(0.3, 0.5) / 20
    spec = np.abs(np.fft.rfft(a[int(.25 * r):int(.55 * r)])) ** 2
    f = np.fft.rfftfreq(int(.55 * r) - int(.25 * r), 1 / r)
    assert spec[f > 7000].sum() / spec.sum() < 0.6


def test_hand_sprite_keeps_original_size_with_feathered_forearm():
    _wbc, _wbp, _, v3r = pipe.load_execution_body()
    from PIL import Image
    src = Image.open(RUNTIME / 'assets' / 'hand' / 'drawing-hand.png')
    hand = v3r._hand()
    assert hand.size == src.size
    alpha = np.asarray(hand)[..., 3]
    assert alpha[-4:, -4:].max() == 0


def _wordnet():
    try:
        from nltk.corpus import wordnet
        wordnet.synsets('dog')
        return True
    except (ImportError, LookupError):
        return False


@pytest.mark.skipif(not _wordnet(), reason='nltk wordnet corpus missing')
@pytest.mark.parametrize('concept, want', [
    ('oncologist', 'person'),
    ('sourdough', 'bread'),
    ('glacier', 'ice'),
    ('tuba', 'trumpet'),
    ('sedan', 'car'),
])
def test_unknown_concepts_fall_back_to_closest_drawing(concept, want):
    _wbc, _wbp, _, v3r = pipe.load_execution_body()
    v3r.set_art_kit(None)
    v3r.set_context('')
    v3r.set_ink_only(False)
    ic = v3r._icon_for(concept)
    name = ic if isinstance(ic, str) else ic[-1]
    assert name == want


@pytest.mark.skipif(not _wordnet(), reason='nltk wordnet corpus missing')
def test_script_context_and_ink_only_pick_drawable_sense():
    _wbc, _wbp, _, v3r = pipe.load_execution_body()
    v3r.set_art_kit(None)
    v3r.set_ink_only(True)
    v3r.set_context('')
    assert v3r._icon_for('queen')[-1] == 'chess-queen'
    v3r.set_context('the bees in a colony serve their queen inside the hive')
    ic = v3r._icon_for('queen')
    assert 'chess' not in ic[-1]
    for c in ('bee', 'drought', 'queen'):
        assert not v3r._is_sprite(v3r._icon_for(c))
    v3r.set_context('')
    v3r.set_ink_only(False)


def test_marker_foley_has_no_tonal_peak(tmp_path):
    ev = [{'start': 0.1 + 0.5 * i, 'duration': 0.35, 'length': 300 + 200 * i}
          for i in range(8)]
    out = tmp_path / 'm.wav'
    marker_sfx.render(ev, 4.5, out)
    with wave.open(str(out)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32767
    spec = np.abs(np.fft.rfft(a)) ** 2
    f = np.fft.rfftfreq(len(a), 1 / marker_sfx.RATE)
    edges = 1000 * 2 ** (np.arange(-6, 25) / 6)
    band = [10 * np.log10(spec[(f >= lo) & (f < hi)].mean())
            for lo, hi in zip(edges[:-1], edges[1:])]
    prominence = [band[i] - (band[i - 1] + band[i + 1]) / 2
                  for i in range(1, len(band) - 1)]
    assert max(prominence) < 4.0
    assert spec[f > 7000].sum() / spec.sum() < 0.6
