"""Wrapped board scenes reserve space even when their drawings have no labels."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine_sources/whiteboard-board-scenes'))
import pipeline_v3_narration_timed as pipeline
pipeline.load_execution_body()
import v3_board_sections as board


class WhiteboardLayout(unittest.TestCase):
    def elements(self):
        # One large hero and four narrow supporting drawings: the composition
        # that wraps to multiple rows on square and portrait boards.
        return [dict(kind='art', box=box, label=[], rel=1.0) for box in [
            (0, 0, 300, 250),
            (330, 125, 390, 250),
            (420, 232, 480, 250),
            (510, 190, 570, 250),
            (600, 175, 660, 250),
        ]]

    def test_unlabelled_wrapped_rows_have_clearance_and_stay_inside_the_board(self):
        for width, height in [(600, 460), (440, 600)]:
            with self.subTest(width=width, height=height):
                elements = self.elements()
                board._sb_fill(elements, (0, 0, width, height), lambda element: 0)
                boxes = [element['box'] for element in elements]
                self.assertGreater(len({round(box[3], 3) for box in boxes}), 1)
                for index, box in enumerate(boxes):
                    self.assertGreaterEqual(box[0], 0)
                    self.assertGreaterEqual(box[1], 0)
                    self.assertLessEqual(box[2], width)
                    self.assertLessEqual(box[3], height)
                    for other in boxes[index + 1:]:
                        self.assertFalse(board._sb_ovl(box, other, 2.0), (box, other))


if __name__ == '__main__':
    unittest.main()
