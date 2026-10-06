import json
import sys
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNTIME))
import pipeline_v3_narration_timed as p3  # noqa: E402

p3.load_execution_body(None)
import v3_board_renderer as v3  # noqa: E402

KIT = RUNTIME / 'assets' / 'kits' / 'scene'


def test_every_scene_glyph_draws_and_is_credited():
    man = json.loads((KIT / 'index.json').read_text())
    notice = (KIT / 'LICENSE-NOTICE.txt').read_text()
    for slug, meta in man['glyphs'].items():
        assert v3._strokes_for(('icon', 'kit:scene', slug)), slug
        assert meta['keywords'], slug
        assert slug in notice, slug


@pytest.mark.parametrize('word,art', [
    ('pier', 'wooden-pier'), ('well', 'well'), ('piano bench', 'park-bench'),
    ('stage', 'theater-curtains'), ('hay bale', 'round-straw-bale'),
    ('cage', 'bird-cage'), ('puddles', 'puddle'), ('front row', 'chair-row'),
    ('town hall', 'greek-temple'), ('cocoa', 'coffee'), ('couch', 'sofa'),
    ('kitchen table', 'table'), ('staircase', 'stairs'),
    ('conveyor belt', 'conveyor-belt'),
])
def test_story_things_get_their_own_drawing(word, art):
    assert v3._icon_for(word) == ('icon', 'kit:scene', art)


@pytest.mark.parametrize('word,wrong', [
    ('belt', 'conveyor-belt'), ('hall', 'greek-temple'),
])
def test_a_head_noun_alone_does_not_borrow_a_compound_drawing(word, wrong):
    assert v3._icon_for(word) != ('icon', 'kit:scene', wrong)


def test_named_art_finds_the_glyph_called_by_the_word():
    assert v3._named_art('leather belt') == ('icon', 'phosphor', 'belt')
    assert v3._named_art('well') == ('icon', 'kit:scene', 'well')
    assert v3._named_art('zzzz') is None
