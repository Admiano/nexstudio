"""Who a verb moves on a printed page."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from editorial_plan_compiler.directing import direct  # noqa: E402

ZONE = {'x': 0, 'y': 0, 'w': 1000, 'h': 600}


def _run(text, concepts):
    words = [{'text': w, 'start_ms': 200 * k, 'end_ms': 200 * k + 180} for k, w in enumerate(text.split())]
    ents = [{'id': c, 'concept': c, 'bbox': {'x': 100 + 300 * k, 'y': 300, 'w': 200, 'h': 200}}
            for k, c in enumerate(concepts)]
    rec = direct(ents, ZONE, 4000, words, text, 'b01')
    return {e['id']: e['kind'] for e in rec['events']}


def test_a_person_acts_through_what_they_handle():
    acts = _run('Her brother poured cocoa into a mug.', ['boy', 'mug'])
    assert 'boy' not in acts and acts.get('mug') == 'fill'


def test_opening_a_part_the_book_does_not_draw_leaves_the_next_verb():
    acts = _run('Then the owl opened its wings and flew into the woods.', ['owl'])
    assert acts == {'owl': 'fly'}


def test_a_place_after_a_preposition_is_never_the_subject():
    acts = _run('A crab crept onto the rock and hid.', ['crab', 'rock'])
    assert 'rock' not in acts and 'crab' in acts
