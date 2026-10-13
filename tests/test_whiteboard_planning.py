"""Fallback planning keeps grammatical lists and valid lexical artwork."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('NLTK_DATA', str(ROOT / 'llm/nltk'))
sys.path.insert(0, str(ROOT / 'engine_sources/whiteboard-board-scenes'))
import plan_author as author
import pipeline_v3_narration_timed as pipe
pipe.load_execution_body()
import v3_board_renderer as renderer


class WhiteboardPlanning(unittest.TestCase):
    def test_verbs_and_adverbs_do_not_become_drawing_roles(self):
        for words, index in [(['pumped', 'in', 'creating', 'pressure'], 2),
                             (['quality', 'ensuring', 'a', 'game'], 1),
                             (['mixed', 'together'], 1)]:
            self.assertFalse(author._noun_in_context(words, index, set()))
        self.assertTrue(author._noun_in_context(['the', 'bottle'], 1, set()))

    def test_comma_separated_materials_are_not_a_compound_or_a_person(self):
        with patch.object(author.scene_map, 'parse', return_value=None):
            plan = author.build_storyboard('Rubber, polyester, and latex are mixed together.')
        scene = plan['beats'][0]['scene']
        roles = [scene['heroRole'], *scene['supportingRoles']]
        self.assertEqual({r['label'] for r in roles}, {'rubber', 'polyester', 'latex'})
        self.assertTrue(all(r['icon'] != 'person' for r in roles))
        self.assertEqual(plan['art_kit'], 'materials')

    def test_lexically_related_fallback_works_without_clip(self):
        bad = ('icon', 'tabler', 'unrelated')
        good = ('icon', 'phosphor', 'bottle')
        with patch.object(renderer, '_icon_for_lex', side_effect=[bad, good]), \
             patch.object(renderer, 'sem_rank', return_value=None), \
             patch.object(renderer, '_named_art', return_value=None), \
             patch.object(renderer, 'art_related', side_effect=lambda phrase, art: art == good):
            self.assertEqual(renderer._icon_for('bottle'), good)


if __name__ == '__main__':
    unittest.main()
