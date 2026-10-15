"""SceneBam quality director: source claims and strict family isolation."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "compiler")]

import make_reel
from editorial_plan_compiler.contracts import FilmTreatment, TreatmentError


def words(script):
    return [{"text": token, "start_ms": i * 360, "end_ms": i * 360 + 290}
            for i, token in enumerate(script.split())]


def treatment(style, script):
    return make_reel.build_treatment(
        SimpleNamespace(aspects="16x9"), make_reel.style_of(style),
        words(script), [], "quality-director-test-" + style)


class StyleScopedDirectorTests(unittest.TestCase):
    def test_only_dataviz_has_explicit_kinetic_caption_authority(self):
        visual = treatment("dataviz",
            "In January, visits were 10. In February, they reached 20. In March, they reached 15.")
        self.assertEqual(visual["director_style"], "dataviz")
        self.assertEqual(visual["caption_policy"], "kinetic")
        parsed = FilmTreatment.parse(visual)
        self.assertEqual(parsed.director_style, "dataviz")
        self.assertEqual(parsed.caption_policy, "kinetic")

        sketch = treatment("sketch", "A phone sends a message to a server.")
        self.assertEqual(sketch["director_style"], "sketch")
        self.assertNotIn("caption_policy", sketch)
        self.assertEqual(FilmTreatment.parse(sketch).director_style, "sketch")

    def test_other_style_treatments_do_not_opt_into_new_director(self):
        for family in ("photo_story", "emoji", "journey", "collage"):
            with self.subTest(family=family):
                result = treatment(family, "A person opens a book at a desk.")
                self.assertNotIn("director_style", result)
                self.assertNotIn("caption_policy", result)

    def test_ambiguous_style_or_captions_fail_closed(self):
        base = treatment("sketch", "A server connects to a database.")
        base["director_style"] = "other-style"
        with self.assertRaises(TreatmentError):
            FilmTreatment.parse(base)
        visual = treatment("dataviz", "Sales rose from 10 dollars to 20 dollars.")
        visual["caption_policy"] = "burned"
        with self.assertRaises(TreatmentError):
            FilmTreatment.parse(visual)

    def test_trend_values_are_literal_and_datum_shapes_are_not_buttons(self):
        cases = [
            ("In January, visits were 10. In February, they reached 20. In March, they reached 15.",
             ["10", "20", "15"]),
            ("In 2021 sales were 10, in 2022 they were 20, and in 2023 they were 30.",
             ["10", "20", "30"]),
        ]
        for script, expected in cases:
            with self.subTest(script=script):
                beat = make_reel.dataviz_beat(words(script), 0, 1, [])
                chart = next(e for e in beat["illustration"]["entities"] if e["glyph"] == "CHART_LINE")
                self.assertEqual(chart["params"]["value_labels"], expected)
                self.assertTrue(all(e["params"].get("plain_datum") is True
                    for e in beat["illustration"]["entities"] if e["glyph"] == "PILL"))


if __name__ == "__main__":
    unittest.main()
