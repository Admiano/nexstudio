"""Unrelated lexical fallbacks must never survive the storyboard gate."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine_sources/whiteboard-board-scenes'))
import pipeline_v3_narration_timed as pipeline
pipeline.load_execution_body()
import v3_board_renderer as renderer
import sb_qa


class ArtworkSelection(unittest.TestCase):
    def test_rejected_candidates_never_return_when_the_visual_model_is_unavailable(self):
        for word, unrelated in [('toothpick', 'wood'), ('mop', 'crown'), ('reef', 'flag-minus')]:
            with self.subTest(word=word), \
                    patch.object(renderer, '_icon_for_lex', return_value=('icon', 'tabler', unrelated)), \
                    patch.object(renderer, '_named_art', return_value=None), \
                    patch.object(renderer, 'kit_exact', return_value=None), \
                    patch.object(renderer, 'sem_rank', return_value=None), \
                    patch.object(renderer, 'art_related', return_value=False), \
                    patch.object(renderer, '_wn_family', return_value=set()):
                self.assertIsNone(renderer.icon_for(word))

    def test_selection_uses_the_same_visual_rank_limit_as_the_ship_gate(self):
        good = ('icon', 'tabler', 'needle')
        with patch.object(renderer, '_icon_for_lex', return_value=good), \
                patch.object(renderer, '_named_art', return_value=good), \
                patch.object(renderer, 'kit_exact', return_value=None), \
                patch.object(renderer, 'art_related', return_value=True), \
                patch.object(renderer, 'sem_rank', return_value=renderer.SEM_BAD_RANK + 1), \
                patch.object(renderer, '_wn_family', return_value=set()):
            self.assertIsNone(renderer.icon_for('needle'))
            failures = []
            sb_qa._semantic(renderer, failures, 0, 'needle', good, 'needle')
            self.assertEqual(failures[0]['check'], 'semantic-art')

    def test_a_valid_alternative_is_selected_and_passes_the_gate(self):
        bad = ('icon', 'tabler', 'crown')
        good = ('icon', 'tabler', 'mop')
        def lexical(concept, exclude=None, depth=0):
            return good if exclude and bad in exclude else bad
        with patch.object(renderer, '_icon_for_lex', side_effect=lexical), \
                patch.object(renderer, '_named_art', return_value=None), \
                patch.object(renderer, 'kit_exact', return_value=None), \
                patch.object(renderer, 'sem_rank', return_value=None), \
                patch.object(renderer, 'art_related', side_effect=lambda phrase, icon: icon == good):
            result = renderer.icon_for('mop')
            self.assertEqual(result, good)
            failures = []
            sb_qa._semantic(renderer, failures, 0, 'mop', result, 'mop')
            self.assertFalse(any(issue['severity'] == 'fail' for issue in failures))

    def test_shared_toothpick_art_is_literal_and_has_drawable_strokes(self):
        renderer.configure_art({'board_layout': 'storyboard', 'beats': []})
        for word in ['toothpick', 'toothpicks', 'wooden toothpick', 'cocktail stick']:
            with self.subTest(word=word):
                result = renderer.icon_for(word)
                self.assertEqual(result, ('icon', 'kit:everyday-tools', 'toothpick'))
                self.assertTrue(renderer._strokes_for(result))
                failures = []
                sb_qa._semantic(renderer, failures, 0, word, result, word)
                self.assertFalse(any(issue['severity'] == 'fail' for issue in failures))

    def test_asset_registry_cannot_select_art_for_only_a_modifier(self):
        bad = ('icon', 'fluent', 'wood')
        good = ('icon', 'phosphor', 'needle')
        used = {'_reg': {'nouns': {'needle': 'sewing needle'}, 'assets': {}}}
        with patch.object(renderer, '_illust_lookup', return_value=bad), \
                patch.object(renderer, '_icon_for', return_value=good) as resolve, \
                patch.object(renderer, 'kit_exact', return_value=None), \
                patch.object(renderer, 'sem_rank', return_value=None), \
                patch.object(renderer, 'art_related', side_effect=lambda phrase, icon: icon == good):
            self.assertEqual(renderer.icon_for('wooden needle', used), good)
            resolve.assert_called_once()

    def test_composed_phrases_reject_unrelated_parts(self):
        bad = ('icon', 'tabler', 'crown')
        with patch.object(renderer, '_icon_for', return_value=bad), \
                patch.object(renderer, 'kit_exact', return_value=None), \
                patch.object(renderer, 'sem_rank', return_value=None), \
                patch.object(renderer, 'art_related', return_value=False):
            self.assertIsNone(renderer._composed_parts(['mop', 'bucket']))


if __name__ == '__main__':
    unittest.main()
