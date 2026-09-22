"""Golden-frame and contract regression for the kinetic-type renderer."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent
sys.path.insert(0, str(RUNTIME))

import kinetic_type_renderer as ktr  # noqa: E402
import pipeline_v3_narration_timed as pipe  # noqa: E402
import pipeline_kinetic_timed as kpipe  # noqa: E402

try:
    pipe.resolve_execution_package()
    HAS_BODY = True
except FileNotFoundError:
    HAS_BODY = False

pytestmark = pytest.mark.skipif(not HAS_BODY, reason='run scripts/install-engines.py first')

FIXTURE = RUNTIME / 'fixtures' / 'kinetic_demo_plan.json'
GOLDEN = HERE / 'golden_kinetic'
MEAN_ABS_DIFF_TOLERANCE = 6.0


def _plan():
    return pipe.normalize_plan(json.loads(FIXTURE.read_text()))


def _sents(plan):
    """Fixture sentences on a synthetic word clock (0.42 s/word)."""
    word_times = []
    t = 0.0
    for b in plan['beats']:
        for w in str(b['narration']).split():
            word_times.append({'word': w, 'start': t, 'end': t + 0.38})
            t += 0.42
    return ktr.sentence_words(plan, word_times)


def _frame_at(t, face='grotesk', ratio='9:16', theme='light'):
    plan = _plan()
    sents = _sents(plan)
    wbp = pipe.load_execution_body()[1]
    size = wbp.RATIO_SIZES[ratio]
    specs = [ktr.typeset(s, ktr.base_size(*size), face, size[0],
                         frame_h=size[1]) for s in sents]
    return ktr.render_kinetic_frame(sents, specs, t, size, plan, face,
                                  theme=theme)


def _frame_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    return buf.getvalue()


def _mean_abs_diff(a: bytes, b: bytes) -> float:
    from PIL import Image, ImageChops, ImageStat
    ia, ib = Image.open(io.BytesIO(a)).convert('RGB'), Image.open(io.BytesIO(b)).convert('RGB')
    if ia.size != ib.size:
        ib = ib.resize(ia.size)
    return ImageStat.Stat(ImageChops.difference(ia, ib)).mean[0]


# --- contract ---------------------------------------------------------------

def test_emphasis_rules():
    # function words never emphasised
    assert not ktr._emphasized('the', sentence_first=True)
    assert not ktr._emphasized('on', sentence_first=False)
    # open-class words emphasised
    assert ktr._emphasized('spinach', sentence_first=False)
    assert ktr._emphasized('leaf', sentence_first=False)
    # digits always emphasise
    assert ktr._emphasized('16', sentence_first=False)
    # TitleCase mid-sentence = proper noun -> emphasised
    assert ktr._emphasized('Gerber', sentence_first=False)
    # TitleCase at position 0 = sentence capital, not a proper noun -> no
    assert not ktr._emphasized('The', sentence_first=True)


def test_split_sentences():
    s = ktr.split_sentences('One half an apple. 16 blueberries! ok?')
    assert s == ['One half an apple.', '16 blueberries!', 'ok?']


def test_sentence_words_fallback_clock():
    plan = _plan()
    sents = ktr.sentence_words(plan, None)
    assert len(sents) == 4
    for s in sents:
        assert s['end'] > s['start']
        assert len(s['words']) == len(s['text'].split())
        for w in s['words']:
            assert s['start'] <= w['start'] <= w['end'] <= s['end'] + 1e-6


def test_typeset_wraps_and_fits():
    plan = _plan()
    sents = _sents(plan)
    spec = ktr.typeset(sents[0], 96, 'grotesk', 540)
    for line in spec['lines']:
        total = sum(it['tw'] for it in line) + spec['gap'] * (len(line) - 1)
        assert total <= 540 - 2 * 64 + 2


def test_marker_face_renders():
    img = _frame_at(1.0, face='marker')
    from PIL import ImageStat
    assert ImageStat.Stat(img.convert('L')).stddev[0] > 4


def test_dark_theme_renders():
    img = _frame_at(1.0, theme='dark')
    from PIL import ImageStat
    st = ImageStat.Stat(img.convert('L'))
    assert st.mean[0] < 80          # dark background dominates
    assert st.stddev[0] > 4         # but text is present


def test_layout_never_leaves_frame():
    """Every word slot must stay inside the frame at rest AND during the
    entry transition (the rise is capped so tall blocks can't dip below)."""
    plan = _plan()
    sents = _sents(plan)
    wbp = pipe.load_execution_body()[1]
    for ratio, (W, H) in wbp.RATIO_SIZES.items():
        margin = 64
        vmargin = max(48, int(H * 0.08))
        for s in sents:
            spec = ktr.typeset(s, ktr.base_size(W, H), 'grotesk', W,
                               frame_h=H)
            # block fits vertically at rest
            assert spec['block_h'] <= H - 2 * vmargin, (
                ratio, s['text'], spec['block_h'])
            # every line fits horizontally
            for line in spec['lines']:
                total = (sum(it['tw'] for it in line)
                         + spec['gap'] * (len(line) - 1))
                assert total <= W - 2 * margin + 2
            # transition start: entry shift keeps block bottom on-frame
            enter = min(H * 0.30,
                        max(0.0, H * 0.54 - spec['block_h'] / 2 - 8))
            bottom = H * 0.46 + spec['block_h'] / 2 + enter
            assert bottom <= H + 1e-6, (ratio, s['text'], bottom)
            top = H * 0.46 - spec['block_h'] / 2
            assert top >= 0, (ratio, s['text'], top)


# --- determinism + golden frames --------------------------------------------

@pytest.mark.parametrize('t', [1.0, 3.6, 5.9, 8.2])
def test_golden_frame(t):
    got = _frame_bytes(_frame_at(t))
    golden = GOLDEN / f'frame_t{t:.1f}.png'
    if not golden.exists():
        golden.parent.mkdir(exist_ok=True)
        golden.write_bytes(got)
        pytest.fail(f'golden written: {golden.name} — re-run to compare')
    diff = _mean_abs_diff(got, golden.read_bytes())
    assert diff <= MEAN_ABS_DIFF_TOLERANCE, f't={t}s drifted {diff:.2f} vs golden'


def test_render_deterministic():
    a = _frame_bytes(_frame_at(2.0))
    b = _frame_bytes(_frame_at(2.0))
    assert a == b


# --- end-to-end encode ------------------------------------------------------

@pytest.mark.skipif(not __import__('shutil').which('ffmpeg'), reason='ffmpeg required')
def test_end_to_end_encode(tmp_path):
    plan = _plan()
    word_times = []
    t = 0.0
    for b in plan['beats']:
        for w in str(b['narration']).split():
            word_times.append({'word': w, 'start': t, 'end': t + 0.38})
            t += 0.42
    receipt = kpipe.render_production(plan, tmp_path, ratio='9:16', fps=8,
                                      word_times=word_times)
    mp4 = tmp_path / f"{plan['production_id']}.mp4"
    assert mp4.exists() and mp4.stat().st_size > 0
    assert receipt['renderer']['type'] == 'kinetic'
    assert (tmp_path / f"{plan['production_id']}_QA.jpg").exists()
