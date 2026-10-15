#!/usr/bin/env python3
"""Executable scene repertoire contract tests: no renamed generic placeholders."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"tools"),str(ROOT/"compiler")]
import make_reel
from scene_repertoire import EXECUTABLE_SCENES, candidates, realize
from scene_director import direct_film
from editorial_plan_compiler.contracts import BeatTreatment, FilmTreatment


def tokens(text):
    return [{"text": w, "start_ms": i*480, "end_ms": i*480+360}
            for i,w in enumerate(text.split())]


def beat(text,style="dataviz"):
    ww=tokens(text)
    return (make_reel.dataviz_beat(ww,0,1,[]) if style=="dataviz"
            else make_reel.sketch_beat(ww,0,1,set(),[]))


class RepertoireTests(unittest.TestCase):
    def test_native_catalogue_is_nontrivial_and_has_distinct_visual_grammars(self):
        self.assertGreaterEqual(len(EXECUTABLE_SCENES["dataviz"]),12)
        self.assertGreaterEqual(len(EXECUTABLE_SCENES["sketch"]),12)
        self.assertGreaterEqual(len(set(EXECUTABLE_SCENES["dataviz"]) |
                                    set(EXECUTABLE_SCENES["sketch"])),19)

    def test_each_executable_data_scene_validates_against_native_compiler(self):
        cases = [
            ("Breakdown: 40 apples, 25 bananas, and 30 oranges.", "categorical_columns", "DATA_BARS"),
            ("The report breakdown includes 40 apples, 25 bananas, and 30 oranges.", "categorical_table", "DATA_TABLE"),
            ("The construction project is 65 percent complete.", "completion_meter", "PROGRESS"),
            ("In 2020 the project started; in 2022 the project expanded; in 2024 the project shipped.", "milestone_timeline", "TIMELINE"),
            ("First wash the rice, then boil the water, finally add the rice.", "spoken_process", "FLOW_STEPS"),
            ("Solar panels versus wind turbines.", "verbal_versus", "VS_CARDS"),
            ("Look closely at the pressure valve.", "editorial_magnification", "MAGNIFY"),
        ]
        forms=set()
        for source,family,glyph in cases:
            with self.subTest(family=family):
                b=beat(source)
                offered=[o[0] for o in candidates("dataviz",b)]
                self.assertIn(family,offered, f"not offered for source {source!r}: {offered}")
                self.assertTrue(realize(family,b))
                ent=b["illustration"]["entities"]
                self.assertEqual(len(ent),1)
                self.assertEqual(ent[0]["glyph"],glyph)
                self.assertEqual(b["narration"],source)
                self.assertNotIn("data",b)
                forms.add(glyph)
                BeatTreatment.parse(b)
        self.assertEqual(len(forms),7)

    def test_all_new_data_scene_families_are_eligible_for_director(self):
        cases=[
            ("40 apples, 25 bananas, and 30 oranges.", "categorical_columns"),
            ("The report breakdown has 40 apples, 25 bananas, and 30 oranges.", "categorical_table"),
            ("The campaign is 72 percent complete.", "completion_meter"),
            ("In 2021 the website launched; in 2023 the website expanded.", "milestone_timeline"),
            ("First sort the beans, then roast the beans, finally pack the beans.", "spoken_process"),
            ("Bread versus biscuits.", "verbal_versus"),
            ("Focus on the service token.", "editorial_magnification"),
        ]
        for source, expected in cases:
            with self.subTest(expected=expected):
                b=beat(source)
                plan=direct_film("dataviz",[b])
                self.assertEqual(plan["scenes"][0]["family"],expected)
                self.assertNotEqual(b["pattern"],"PROGRESSIVE_HERO_BUILD")
                BeatTreatment.parse(b)

    def test_sketch_real_visual_markup_is_not_applied_to_negated_claims(self):
        cases=[
            ("Never use the receipt.", "negated_subject", "PROHIBIT","blocks"),
            ("Circle the receipt.", "highlighted_subject", "MARK_CIRCLE","marks"),
            ("First sort the notes, then file the notes.", "spoken_process", "FLOW_STEPS",None),
        ]
        for source,family,glyph,relation in cases:
            with self.subTest(family=family):
                b=beat(source,"sketch")
                self.assertIn(family,[o[0] for o in candidates("sketch",b)])
                self.assertTrue(realize(family,b))
                ent=b["illustration"]["entities"]
                self.assertEqual(ent[-1]["glyph"],glyph)
                if relation:
                    self.assertEqual(b["illustration"]["relations"][-1]["type"],relation)
                BeatTreatment.parse(b)
        for source in ("The receipt was never received.",
                       "The report did not prove the result."):
            b=beat(source,"sketch")
            self.assertNotIn("negated_subject",[o[0] for o in candidates("sketch",b)])

    def test_reject_unsupported_categories_and_progress_conclusions(self):
        data=[
            "The product contains 40 apples and 25 oranges.",
            "The report lists 40 apples, 25 bananas, and 30 oranges in 2021.",
            "The offer sold about 40 apples, 25 bananas, and 30 oranges.",
            "The cost is 62 percent higher than last year.",
            "Inflation reached 80 percent.",
            "In 2023 we launched; in 2022 we grew.",
            "A stone is different from water.",
        ]
        for text in data:
            with self.subTest(text=text):
                b=beat(text)
                offered={x[0] for x in candidates("dataviz",b)}
                if "contains 40" in text or "about 40" in text or "2021" in text:
                    self.assertNotIn("categorical_columns",offered)
                if "percent" in text:
                    self.assertNotIn("completion_meter",offered)
                if "In 2023" in text:
                    self.assertNotIn("milestone_timeline",offered)

    def test_real_build_treatment_keeps_the_approved_contract(self):
        scripts=[
            "First sort the seeds, then plant the seeds, finally water the seeds.",
            "The renovation project is 70 percent complete.",
            "The results show 40 apples, 25 bananas, and 30 oranges.",
        ]
        for script in scripts:
            with self.subTest(script=script):
                film=make_reel.build_treatment(SimpleNamespace(aspects="16x9,9x16,1x1"),
                                            make_reel.style_of("dataviz"),
                                            tokens(script), [], "scene-repertoire-check")
                FilmTreatment.parse(film)
                self.assertEqual(" ".join(b["narration"] for b in film["beats"]),script)
                self.assertEqual(film["director_report"]["global_lookahead"],len(film["beats"]))


if __name__=="__main__":
    unittest.main()
