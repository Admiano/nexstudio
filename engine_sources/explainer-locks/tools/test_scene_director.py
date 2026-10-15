#!/usr/bin/env python3
"""General-purpose film director, data provenance and compiler contract tests."""
import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "compiler")]

import make_reel
from scene_director import direct_film, plan_film, _bridge_eligible
from editorial_plan_compiler.contracts import BeatTreatment, FilmTreatment


def words(text):
    return [{"text": token, "start_ms": i * 480, "end_ms": i * 480 + 380}
            for i, token in enumerate(text.split())]


def data_beat(text, i, count):
    beat = make_reel.dataviz_beat(words(text), i, count, [])
    BeatTreatment.parse(beat)
    return beat


class SceneDirectorTests(unittest.TestCase):
    def test_evidence_bridge_reuses_only_exact_spoken_source_values(self):
        examples = (
            ("The test identified 99 genuine cases.",
             "Yet the test returned 495 healthy positives.", 99., 495.),
            ("Our service recorded 24 incidents.",
             "But the service resolved 36 incidents.", 24., 36.),
            ("This factory shipped 120 boxes.",
             "However the factory shipped 180 boxes.", 120., 180.))
        for first, second, a, b in examples:
            with self.subTest(first=first):
                beats = [data_beat(first, 0, 2), data_beat(second, 1, 2)]
                original_narration = [beat["narration"] for beat in beats]
                report = direct_film("dataviz", beats)
                bridge = beats[1]
                self.assertEqual([p["family"] for p in report["scenes"]][-1], "evidence_bridge")
                self.assertEqual(bridge["illustration"]["form"], "DATA_VISUAL")
                bars = bridge["illustration"]["entities"]
                self.assertEqual([e["glyph"] for e in bars], ["BAR", "BAR"])
                self.assertEqual([e["params"]["value"] for e in bars], [a, b])
                self.assertEqual([e["params"]["level"] for e in bars], [a / max(a, b), b / max(a, b)])
                self.assertEqual([s["value"] for s in bridge["director_evidence"]], [str(int(a)), str(int(b))])
                self.assertEqual([beat["narration"] for beat in beats], original_narration)
                self.assertNotIn("data", bridge)
                BeatTreatment.parse(bridge)

    def test_population_subset_uses_only_observed_whole_and_part(self):
        examples = [
            ("Imagine 10,000 people tested for a rare condition.",
             "Inside that group of people, only 100 have the condition.", 10000, 100),
            ("The study enrolled 800 volunteers.",
             "Among those volunteers only 120 finished the study.", 800, 120),
        ]
        for first, second, whole, part in examples:
            with self.subTest(first=first):
                beats = [data_beat(first, 0, 2), data_beat(second, 1, 2)]
                narration = [b["narration"] for b in beats]
                result = direct_film("dataviz", beats)
                self.assertEqual(result["scenes"][-1]["family"], "population_grid")
                evidence = beats[1]["director_evidence"]
                self.assertEqual([int(e["value"]) for e in evidence], [whole, part])
                entity = beats[1]["illustration"]["entities"][0]
                self.assertEqual(entity["glyph"], "POPULATION_GRID")
                self.assertAlmostEqual(entity["params"]["level"], part / whole)
                self.assertEqual(entity["params"]["count"], part)
                self.assertEqual([b["narration"] for b in beats], narration)
                self.assertEqual(len(result["explanation_map"]["claims"]), 2)
                BeatTreatment.parse(beats[1])

    def test_anaphora_preserves_previous_denominator_exactly(self):
        examples = [
            ("The survey logged 594 positive results.",
             "But only 99 of those are genuine.", 594, 99),
            ("The study counted 800 volunteers.",
             "Only 120 of them were selected.", 800, 120),
        ]
        for first, second, whole, part in examples:
            with self.subTest(first=first):
                beats = [data_beat(first, 0, 2), data_beat(second, 1, 2)]
                report = direct_film("dataviz", beats)
                exact_grid = whole % 100 == 0 and (part * 100) % whole == 0
                self.assertEqual(report["scenes"][-1]["family"],
                                 "population_grid" if exact_grid else "population_subset")
                self.assertEqual([int(x["value"]) for x in beats[1]["director_evidence"]],
                                 [whole, part])
                ent = beats[1]["illustration"]["entities"][0]
                self.assertEqual(ent["glyph"], "POPULATION_GRID" if exact_grid else "DONUT")
                self.assertAlmostEqual(ent["params"]["level"], part / whole)
                self.assertEqual(ent["params"]["count"], part)
                BeatTreatment.parse(beats[1])
        # Deictic wording with an intervening named different product is not
        # allowed to imply that muffins are part of a coffee denominator.
        beats = [data_beat("The cafe sold 1000 coffees.", 0, 2),
                 data_beat("Only 40 of those muffins were sold.", 1, 2)]
        direct_film("dataviz", beats)
        self.assertNotIn("director_evidence", beats[1])

    def test_population_subset_requires_explicit_group_membership(self):
        pairs = [
            ("The cafe sold 1,000 coffees.", "Only 40 muffins were sold inside the cafe."),
            ("The app gained 300 users.", "Only 100 dollars remained in the account."),
            ("We employed 100 staff.", "Only 120 of those staff attended."),
            ("We surveyed 200 patients.", "We found 40 positive tests."),
        ]
        for first, second in pairs:
            with self.subTest(first=first):
                beats = [data_beat(first, 0, 2), data_beat(second, 1, 2)]
                direct_film("dataviz", beats)
                self.assertNotEqual(beats[1].get("illustration", {}).get("entities", [{}])[0].get("id"),
                                    "director_population_subset")

    def test_unrelated_numbers_never_bridge(self):
        examples = [
            ("The turbine produced 40 kilowatts.", "Yet the library received 70 books."),
            ("The service handled 100 requests.", "The service processed 120 requests."),
            ("Our rate was 20 percent.", "Yet our rate reached 400 dollars."),
            ("The count was 1000 cars.", "But the count was 1 car."),
            ("We observed about 100 cases.", "Yet we confirmed 90 cases."),
        ]
        for a, b in examples:
            with self.subTest(a=a):
                beats = [data_beat(a, 0, 2), data_beat(b, 1, 2)]
                self.assertFalse(_bridge_eligible(*beats))
                direct_film("dataviz", beats)
                self.assertNotIn("director_evidence", beats[1])
                BeatTreatment.parse(beats[1])

    def test_planner_does_not_mutate_input_or_depend_on_specific_topic(self):
        subjects = [
            ["A server sends a file to a database.", "The database receives the file."],
            ["A pump feeds water into a tank.", "The tank fills with water."],
            ["The price rose from 20 dollars to 40 dollars.",
             "Afterwards it reached 45 dollars."],
            ["This experiment tracked 35 volunteers.",
             "However the experiment excluded 12 volunteers."],
        ]
        for style in ("sketch", "dataviz"):
            for lines in subjects:
                with self.subTest(style=style, lines=lines):
                    fn = make_reel.sketch_beat if style == "sketch" else make_reel.dataviz_beat
                    beats = [fn(words(line), i, len(lines), set(), []) if style == "sketch"
                             else fn(words(line), i, len(lines), [])
                             for i, line in enumerate(lines)]
                    original = copy.deepcopy(beats)
                    p1, p2 = plan_film(style, beats), plan_film(style, beats)
                    self.assertEqual(p1, p2)
                    self.assertEqual(beats, original)
                    self.assertEqual(len(p1), len(lines))
                    result = direct_film(style, beats)
                    self.assertEqual(len(result["scenes"]), len(lines))
                    for beat in beats:
                        BeatTreatment.parse(beat)

    def test_sketch_real_population_art_is_tied_to_explicit_source_group(self):
        examples = [
            "Imagine 10,000 people tested for a rare condition.",
            "The survey included 800 volunteers.",
            "We interviewed 50 patients in the clinic.",
            "A crowd watched the teacher."
        ]
        for sentence in examples:
            with self.subTest(sentence=sentence):
                entities = make_reel.sketch_entities(words(sentence), [])
                pictured = [e for e in entities if e.get("params", {}).get("visual_class") == "population"]
                self.assertTrue(pictured, "A source-named collective must not collapse into typography")
                self.assertTrue(all(e["glyph"] == "TILE" and e["phrase"] in sentence.lower()
                                    and "asset_ref" not in e
                                    for e in pictured))
                beat = make_reel.sketch_beat(words(sentence), 0, 1, set(), [])
                self.assertTrue(any(e.get("params", {}).get("visual_class") == "population"
                                    for e in beat["illustration"]["entities"]))
                BeatTreatment.parse(beat)
        # Singular role is a single figure; abstract/statistical words are not people.
        person = make_reel.sketch_entities(words("A doctor holds a test."), [])
        self.assertFalse(any(e.get("params", {}).get("visual_class") == "population" for e in person))
        abstract = make_reel.sketch_entities(words("The model contains 5 categories."), [])
        self.assertFalse(any(e.get("params", {}).get("visual_class") == "population" for e in abstract))

    def test_sketch_pictured_subject_takes_stage_not_untyped_filler(self):
        for sentence in [
            "Imagine 10,000 people tested for a rare condition.",
            "Inside that enormous group of people, only 100 actually have the condition.",
            "Yet 495 healthy people also test positive.",
        ]:
            with self.subTest(sentence=sentence):
                beat = make_reel.sketch_beat(words(sentence), 0, 1, set(), [])
                visual = beat["illustration"]["entities"]
                self.assertEqual(len(visual), 1)
                self.assertEqual(visual[0]["params"]["visual_class"], "population")
                self.assertEqual(visual[0]["size"], "hero")
                self.assertEqual(visual[0]["glyph"], "TILE")
                self.assertEqual(beat["narration"], sentence)
                BeatTreatment.parse(beat)
        # Non-visual source nouns still work as faithful labelled actors in
        # transfer chains, and explicit comparisons keep both endpoints.
        action = make_reel.sketch_beat(
            words("A pump feeds water into a tank."), 0, 1, set(), [])
        self.assertEqual(action["illustration"]["form"], "PROCESS_PIPELINE")
        BeatTreatment.parse(action)

    def test_existing_native_integration_reports_scene_choices(self):
        script = ("The service processed 40 requests. "
                  "Yet the service rejected 20 requests. "
                  "The team reviewed those decisions.")
        w = words(script)
        for style in ("sketch", "dataviz"):
            with self.subTest(style=style):
                treatment = make_reel.build_treatment(
                    SimpleNamespace(aspects="9x16,1x1"),
                    make_reel.style_of(style), w, [], "native-director-smoke")
                self.assertEqual(treatment["director_report"]["style"], style)
                self.assertEqual(len(treatment["director_report"]["scenes"]), len(treatment["beats"]))
                self.assertIn("film_scene_director_v1=True", treatment["note"])
                self.assertEqual(" ".join(b["narration"] for b in treatment["beats"]), script)
                FilmTreatment.parse(treatment)

    def test_stat_callouts_extract_source_predicate_not_disclaimer(self):
        for sentence, label in [
            ("But only 99 of those are genuine.", "genuine"),
            ("Yet just 12 of these are defective.", "defective"),
            ("However only 6 of them are approved.", "approved"),
        ]:
            with self.subTest(sentence=sentence):
                beat = data_beat(sentence, 0, 1)
                self.assertEqual(beat["data_claim"]["quantities"][0]["label"], label)
                counters = [e for e in beat["illustration"]["entities"] if e["glyph"] == "COUNTER"]
                self.assertEqual(len(counters), 1)
                self.assertEqual(counters[0]["params"]["caption"], label)
                BeatTreatment.parse(beat)

    def test_no_invented_numeric_direction_or_percentage(self):
        beats = [data_beat("The depot moved 50 parcels.", 0, 2),
                 data_beat("But the depot moved 30 parcels.", 1, 2)]
        direct_film("dataviz", beats)
        bars = beats[1]["illustration"]["entities"]
        self.assertEqual([e["params"]["value"] for e in bars], [50, 30])
        self.assertTrue(all("change_direction" not in e["params"] for e in bars))
        self.assertTrue(all("%" not in e["label"] for e in bars))
        BeatTreatment.parse(beats[1])


if __name__ == "__main__":
    unittest.main()
