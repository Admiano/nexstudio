import sys
import unittest
import math
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "compiler")]

import make_reel
from editorial_plan_compiler.contracts import BeatTreatment, TreatmentError
from editorial_plan_compiler.illustration import IllustrationRegistry, IllustrationSolver
from editorial_plan_compiler.timing import Word, window_clock
from editorial_plan_compiler.authorities import kinetic_typography_performance_authority_v3 as ktp


def authored(text):
    words = [{"text": word, "start_ms": i * 360, "end_ms": i * 360 + 300}
             for i, word in enumerate(text.split())]
    beat = make_reel.dataviz_beat(words, 0, 1, [])
    BeatTreatment.parse(beat)
    return beat


class DataVizAuthoringTests(unittest.TestCase):
    def test_comparison_has_exact_labels_and_shared_zero_scale(self):
        beat = authored("Rent rose from 900 dollars to 1,200 dollars.")
        bars = beat["illustration"]["entities"]
        self.assertEqual([e["label"] for e in bars], ["Before $900", "After $1,200"])
        self.assertEqual([e["params"]["level"] for e in bars], [0.75, 1.0])
        self.assertEqual(beat["data_claim"]["kind"], "COMPARISON")
        self.assertEqual([q["source"] for q in beat["data_claim"]["quantities"]], ["900 dollars", "1,200 dollars"])
        self.assertEqual({op["at"]["word"] for op in beat["illustration"]["program"] if "word" in op["at"]},
                         {"900", "1,200"})

    def test_before_measure_remains_visible_until_next_claim(self):
        beat = authored("Rent rose from 900 dollars to 1,200 dollars.")
        bars = beat["illustration"]["entities"]
        fade = [o for o in beat["illustration"]["program"] if o["op"] == "DIM"]
        self.assertEqual(1, len(fade))
        self.assertEqual(bars[0]["id"], fade[0]["target"])
        self.assertEqual(1.0, fade[0]["from"],
                         "A future change must not hide the first bar before it is spoken")
        self.assertEqual(0.66, fade[0]["to"])
        self.assertEqual("1,200", fade[0]["at"]["word"])

    def test_source_verbs_produce_only_truthful_comparison_direction(self):
        higher = authored("Rent rose from 900 dollars to 1,200 dollars.")
        bars = higher["illustration"]["entities"]
        self.assertEqual(bars[1]["params"]["change_direction"], "up")
        lower = authored("Rent fell from 1,200 dollars to 900 dollars.")
        self.assertEqual(lower["illustration"]["entities"][1]["params"]["change_direction"], "down")
        neutral = authored("Rent moved from 900 dollars to 1,200 dollars.")
        self.assertNotIn("change_direction", neutral["illustration"]["entities"][1]["params"])
        contradictory = authored("Rent rose from 1,200 dollars to 900 dollars.")
        self.assertNotIn("change_direction", contradictory["illustration"]["entities"][1]["params"])
        higher["illustration"]["entities"][1]["params"]["change_direction"] = "down"
        with self.assertRaises(TreatmentError):
            BeatTreatment.parse(higher)

    def test_long_claim_keeps_every_word_and_measure(self):
        text = "Imagine a neighborhood bookstore's weekly sales rising from 40 books to 60 books over the summer."
        beat = authored(text)
        units = beat["display_units"]
        self.assertEqual(" ".join(u["text"] for u in units), text)
        self.assertTrue(all(len(u["text"].split()) <= 10 for u in units))
        self.assertEqual({u["reveal"] for u in units}, {"WORD_CASCADE"})
        self.assertEqual([e["label"] for e in beat["illustration"]["entities"]], ["Before 40 books", "After 60 books"])

    def test_number_words_and_decimal_values(self):
        beat = authored("Prices climbed from one point two dollars to one point eight dollars.")
        self.assertEqual([q["value"] for q in beat["data_claim"]["quantities"]], ["1.2", "1.8"])
        self.assertEqual([e["label"] for e in beat["illustration"]["entities"]], ["Before $1.2", "After $1.8"])
        exact = authored("The error rate was about 2.5 percent last month.")
        self.assertNotIn("illustration", exact)
        self.assertEqual(exact["data"]["kind"], "STAT")
        self.assertEqual(exact["data"]["value"], "2.5%")
        self.assertIn("about", exact["data"]["label"].lower())
        self.assertEqual(exact["dominant_layer"], "DATA")

    def test_single_stat_without_decorative_bar(self):
        beat = authored("Twenty-five trains arrived this morning.")
        self.assertEqual(beat["data_claim"]["kind"], "STAT")
        self.assertEqual([e["glyph"] for e in beat["illustration"]["entities"]], ["COUNTER"])
        self.assertEqual(beat["illustration"]["entities"][0]["params"]["count"], 25)
        self.assertEqual(beat["display_units"][0]["text"], beat["narration"])
        self.assertEqual(beat["display_units"][0]["reveal"], "WORD_CASCADE")

    def test_share_fills_only_from_supplied_numerator(self):
        beat = authored("A survey found 30 percent prefer buses.")
        self.assertEqual(beat["data_claim"]["kind"], "SHARE")
        self.assertEqual(beat["illustration"]["entities"][0]["glyph"], "DONUT")
        self.assertEqual(beat["illustration"]["entities"][0]["params"]["level"], .3)
        self.assertEqual(beat["illustration"]["entities"][0]["params"]["suffix"], "%")
        growth = authored("Inflation increased 30 percent.")
        self.assertEqual([e["glyph"] for e in growth["illustration"]["entities"]], ["COUNTER"])
        for text in ("We saw 12 in the first year and 18 in the second year.",
                     "We stored 10 books in boxes and shipped 20 books."):
            self.assertNotEqual(authored(text)["data_claim"]["kind"], "SHARE")
        self.assertEqual(authored("Three residents out of ten residents prefer walking.")["data_claim"]["kind"],
                         "SHARE")

    def test_trend_only_for_supplied_evenly_spaced_dates(self):
        text = "In 2021 sales were 10, in 2022 they were 20, and in 2023 they were 30."
        beat = authored(text)
        self.assertEqual(beat["data_claim"]["kind"], "TREND")
        self.assertEqual([q["value"] for q in beat["data_claim"]["quantities"]], ["10", "20", "30"])
        self.assertEqual(beat["illustration"]["entities"][0]["params"]["points"], [1 / 3, 2 / 3, 1])
        uneven = text.replace("2022", "2024")
        self.assertNotIn("CHART_LINE", [e["glyph"] for e in authored(uneven).get("illustration", {}).get("entities", [])])
        no_dates = authored("The cups held 10, 20 and 30.")
        self.assertNotIn("CHART_LINE", [e["glyph"] for e in no_dates.get("illustration", {}).get("entities", [])])
        mixed = authored("In 2021 books were 10; in 2022 chairs were 20; in 2023 shoes were 30.")
        self.assertNotIn("CHART_LINE", [e["glyph"] for e in mixed.get("illustration", {}).get("entities", [])])

    def test_trend_annotations_are_source_values_not_pill_buttons(self):
        beat = authored("In January, park visits were 10. In February, they reached 20. In March, they reached 15.")
        self.assertEqual(beat["data_claim"]["kind"], "TREND")
        entities = beat["illustration"]["entities"]
        chart = next(e for e in entities if e["glyph"] == "CHART_LINE")
        self.assertEqual(chart["params"]["value_labels"], ["10", "20", "15"])
        datums = [e for e in entities if e["glyph"] == "PILL"]
        self.assertEqual([e["label"] for e in datums], ["Jan", "Feb", "Mar"])
        self.assertTrue(all(e["params"].get("plain_datum") is True for e in datums))
        self.assertEqual(len(datums), len(chart["params"]["points"]))

    def test_metric_label_is_source_exact_and_optional(self):
        source = authored(
            "In January, park visits were 10. In February, they reached 20. In March, they reached 15.")
        chart = next(e for e in source["illustration"]["entities"] if e["glyph"] == "CHART_LINE")
        self.assertEqual(chart["params"]["metric_label"], "park visits")
        contradiction = deepcopy(source)
        changed = next(e for e in contradiction["illustration"]["entities"] if e["glyph"] == "CHART_LINE")
        changed["params"]["metric_label"] = "daily revenue"
        with self.assertRaises(TreatmentError):
            BeatTreatment.parse(contradiction)
        fabricated = deepcopy(source)
        changed = next(e for e in fabricated["illustration"]["entities"] if e["glyph"] == "CHART_LINE")
        changed["params"]["metric_label"] = "these are all the different visits"
        with self.assertRaises(TreatmentError):
            BeatTreatment.parse(fabricated)

    def test_invalid_annotation_sizes_fail_closed(self):
        beat = authored("In 2021 sales were 10, in 2022 they were 20, and in 2023 they were 30.")
        chart = beat["illustration"]["entities"][0]
        chart["params"]["value_labels"] = ["10"]
        with self.assertRaises(TreatmentError):
            BeatTreatment.parse(beat)
        chart["params"]["value_labels"] = ["10", "20", "30"]
        badge = next(e for e in beat["illustration"]["entities"] if e["glyph"] == "PILL")
        badge["params"]["plain_datum"] = "yes"
        with self.assertRaises(TreatmentError):
            BeatTreatment.parse(beat)

    def test_non_numeric_fallback_and_spoken_steps(self):
        steps = authored("First inspect the pump, then replace the valve.")
        self.assertEqual(steps["data"]["kind"], "SEQUENCE")
        self.assertEqual(steps["data"]["value"], "First inspect the pump | then replace the valve")
        other = authored("The tree casts shade across the path.")
        self.assertNotIn("data", other)
        self.assertTrue(other["illustration"]["entities"])
        self.assertNotIn("NODE", [e["glyph"] for e in other["illustration"]["entities"]])

    def test_zero_negative_and_small_ratios_do_not_create_fake_bars(self):
        for sentence in ("Rent fell from 20 dollars to zero dollars.",
                         "Costs moved from 900 dollars to 1 dollar.",
                         "Revenue moved from minus five dollars to two dollars."):
            beat = authored(sentence)
            self.assertNotIn("BAR", [e["glyph"] for e in beat.get("illustration", {}).get("entities", [])])
            self.assertIn("data", beat)
        self.assertEqual(authored("The balance was 0 dollars.")["data"]["value"], "$0")

    def test_precision_signs_and_incompatible_units_stay_exact(self):
        for sentence, value in (("The reading was 1.0 seconds.", "1.0 seconds"),
                                ("The change was +5 dollars.", "$+5"),
                                ("The change was plus five dollars.", "$+5")):
            beat = authored(sentence)
            self.assertNotIn("illustration", beat)
            self.assertEqual(beat["data"]["value"], value)
        mixed = authored("We shipped 30 books in 60 days.")
        self.assertEqual([q["unit"] for q in mixed["data_claim"]["quantities"]], ["", "days"])
        self.assertNotIn("illustration", mixed)
        discount = authored("The fare is 30 percent cheaper.")
        self.assertEqual(discount["data_claim"]["kind"], "STAT")

    def schedule(self, text, width=400, height=300):
        words = [{"text": word, "start_ms": 1000 + i * 360, "end_ms": 1300 + i * 360}
                 for i, word in enumerate(text.split())]
        beat = make_reel.dataviz_beat(words, 0, 1, [])
        parsed = BeatTreatment.parse(beat)
        clock = window_clock("b01", [u["text"] for u in beat["display_units"]],
                             [u["anchor_word"] for u in beat["display_units"]],
                             [Word(**w) for w in words], words[-1]["end_ms"] + 1600, "TEST")
        ents = [{**e, "params": e.get("params", {}),
                 "bbox": {"x": 0, "y": 0, "w": width, "h": height}} for e in beat["illustration"]["entities"]]
        ops, enter, failures = IllustrationSolver.schedule(parsed.illustration, clock, ents, set(), "b01")
        self.assertFalse(failures)
        for e in ents:
            e.update(enter_ms=enter[e["id"]], enter_duration_ms=240)
        return beat, parsed, clock, ents, ops

    def test_confirmation_is_opted_out_not_zeroed_or_replaced(self):
        _beat, parsed, clock, ents, ops = self.schedule("Rent rose from 900 dollars to 1,200 dollars.")
        end = max(o["end_ms"] for o in ops)
        quiet = IllustrationSolver._decorate(ops, ents, [], clock.duration_ms - 400, parsed.illustration, end)
        self.assertNotIn("EMIT", [o["op"] for o in ops + quiet])
        parsed.illustration.confirmation = True
        default = IllustrationSolver._decorate(ops, ents, [], clock.duration_ms - 400, parsed.illustration, end)
        self.assertIn("EMIT", [o["op"] for o in default])
        invalid = deepcopy(_beat)
        invalid["illustration"]["confirmation"] = "false"
        with self.assertRaises(TreatmentError):
            BeatTreatment.parse(invalid)

    def test_repeated_values_and_multiword_numbers_finish_at_their_own_words(self):
        for text in ("Prices moved from 20 dollars to 20 dollars.",
                     "Prices rose from twenty five dollars to fifty dollars."):
            _beat, _parsed, clock, _ents, ops = self.schedule(text)
            growth = [o for o in ops if o["op"] == "GROW"]
            self.assertGreater(growth[1]["end_ms"], growth[0]["end_ms"])
            for o in growth:
                i = o["params"]["word_index"] + o["params"]["word_span"] - 1
                self.assertEqual(o["end_ms"], clock.words[i].end_ms)

    def test_line_points_land_at_actual_vertices_in_every_geometry(self):
        text = "In 2021 sales were 10; in 2022 they were 40; and in 2023 they were 20."
        for width, height in ((500, 240), (400, 400), (220, 500)):
            _beat, _parsed, clock, _ents, ops = self.schedule(text, width, height)
            growth = [o for o in ops if o["op"] == "GROW"]
            lengths = [math.hypot(width / 2, height * .9 * delta) for delta in (.75, -.5)]
            self.assertAlmostEqual(growth[1]["to"], lengths[0] / sum(lengths))
            self.assertEqual([growth[0]["to"], growth[-1]["to"]], [0, 1])
            for o in growth:
                i = o["params"]["word_index"] + o["params"]["word_span"] - 1
                self.assertEqual(o["end_ms"], clock.words[i].end_ms)
            early_periods = [o for o in ops if o["op"] == "DIM" and o["target"].startswith("point")]
            self.assertEqual(len(early_periods), 3)
            self.assertTrue(all(o["start_ms"] <= clock.words[0].end_ms for o in early_periods))
            markers = [o for o in ops if o["op"] == "SETTLE" and o["target"].startswith("point")]
            self.assertEqual([o["end_ms"] for o in markers], [o["end_ms"] for o in growth])

    def test_dated_sentences_form_one_supplied_trend(self):
        text = "In January park visits were 10. In February they reached 20. In March they reached 15."
        words = [{"text": w, "start_ms": i * 500, "end_ms": i * 500 + 400}
                 for i, w in enumerate(text.split())]
        groups = make_reel.dataviz_groups(words)
        self.assertEqual(len(groups), 1)
        beat = make_reel.dataviz_beat(groups[0], 0, 1, [])
        self.assertEqual(beat["data_claim"]["kind"], "TREND")
        self.assertEqual([e["label"] for e in beat["illustration"]["entities"][1:]],
                         ["Jan", "Feb", "Mar"])
        self.assertEqual(" ".join(u["text"] for u in beat["display_units"]), text)
        self.assertLessEqual(len(beat["display_units"]), 5)
        BeatTreatment.parse(beat)

    def test_only_source_related_followups_keep_the_chart(self):
        source = authored("A survey found 30 percent prefer walking.")
        followup = authored("That share describes the sample, not the whole city.")
        followup["beat_id"] = "b02"
        other = authored("The tree casts shade across the path.")
        other["beat_id"] = "b03"
        beats = [source, followup, other]
        make_reel.dataviz_continuity(beats)
        self.assertEqual(source["illustration"]["persist_to"], "b02")
        self.assertEqual(followup["illustration"]["carry"],
                         {"from_beat": "b01", "entities": ["datum1"]})
        self.assertNotIn("GROW", [o["op"] for o in followup["illustration"]["program"]])
        self.assertEqual(followup["data_context_from"], "b01")
        self.assertIn("illustration", other)
        for b in beats:
            BeatTreatment.parse(b)

    def test_kinetic_authority_keeps_every_source_unit_in_all_aspects(self):
        for text in (
            "In January, park visits were 10. In February, they reached 20. In March, they reached 15.",
            "Imagine a neighborhood bookstore weekly sales rising from 40 books to 60 books over the summer.",
            "A local survey found 30 percent of residents prefer walking.",
            "The reading was about 2.5 seconds, not necessarily a permanent improvement.",
        ):
            beat = BeatTreatment.parse(authored(text))
            for aspect in ("16x9", "9x16", "1x1"):
                perf = ktp.compile_performance(beat.beat_type, aspect, 9000,
                                               [u.ktp_unit() for u in beat.units], object_present=True)
                self.assertEqual(sorted(b["unit_index"] for b in perf["text_blocks"]),
                                 list(range(len(beat.units))))

    def test_line_labels_reserve_space_above_native_caption_floor_only_when_requested(self):
        beat = authored("In 2021 sales were 10; in 2022 they were 40; and in 2023 they were 20.")
        il = BeatTreatment.parse(beat).illustration
        solver = IllustrationSolver.__new__(IllustrationSolver)
        solver.caption_floor = 840
        zone = {"x": 260, "y": 500, "w": 740, "h": 430}
        safe = solver._data_layout(il.entities, zone, False, il.label_space)
        default = solver._data_layout(il.entities, zone, False)
        for e in il.entities[1:]:
            self.assertLessEqual(safe[e.id]["y"] + safe[e.id]["h"], solver.caption_floor)
            self.assertGreater(default[e.id]["y"] + default[e.id]["h"], solver.caption_floor)

    def test_timeline_vertices_align_with_month_labels_in_square_layout(self):
        beat = authored("In January park visits were 10. In February they reached 20. In March they reached 15.")
        il = BeatTreatment.parse(beat).illustration
        solver = IllustrationSolver("1x1", (1080, 1080), IllustrationRegistry(), {}, {}, None)
        entities, failures = solver.layout(il, {"x": 260, "y": 496.6, "w": 746, "h": 433.4}, "b01")
        self.assertFalse(failures)
        chart = next(e for e in entities if e["glyph"] == "CHART_LINE")
        labels = [e for e in entities if e["glyph"] == "PILL"]
        centers = [e["bbox"]["x"] + e["bbox"]["w"] / 2 for e in labels]
        for i, x in enumerate(centers):
            self.assertAlmostEqual(chart["bbox"]["x"] + chart["bbox"]["w"] * i / (len(labels) - 1),
                                   x, delta=.2)


if __name__ == "__main__":
    unittest.main()
