import io
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "compiler"))

import make_reel
from editorial_plan_compiler.contracts import FilmTreatment
from editorial_plan_compiler.illustration import IllustrationRegistry, IllustrationSolver
from editorial_plan_compiler.motion import camera_move
from editorial_plan_compiler.authorities import kinetic_typography_performance_authority_v3 as ktp
from editorial_plan_compiler.compiler import BeatCompiler
from editorial_plan_compiler.timing import beat_clock, synthesise_alignment, normalise


class SketchPreviewTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "requires FFmpeg")
    def test_encoded_preview_keeps_full_video_duration_and_original_audio(self):
        from PIL import Image

        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            original, exported = directory / "original.mp4", directory / "exported.mp4"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=blue:s=64x36:r=15:d=10.266667,"
                            "drawbox=color=white:t=fill:enable='lt(t,0.3)'",
                            "-f", "lavfi", "-i", "sine=frequency=440:duration=10.262",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                            str(original)], check=True)
            for i in range(20):
                Image.new("RGB", (64, 36), "blue").save(directory / f"f{i:05d}.jpg")
            plan = {"beats": [{"duration_ms": 2914, "words": [{"start_ms": 350}],
                               "ensemble": {"hold_window": {"start_ms": 950, "end_ms": 1150}},
                               "illustration": {"ops": [
                {"op": "DRAW", "end_ms": 790},
            ]}}]}
            make_reel.sketch_posterize(directory, original, exported,
                                      directory / "cover.jpg", plan, 15)
            durations, audio_hashes = [], []
            for path in (original, exported):
                data = json.loads(subprocess.check_output([
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=duration", "-of", "json", str(path)],
                    text=True))
                durations.append(float(data["streams"][0]["duration"]))
                audio_hashes.append(subprocess.check_output([
                    "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a",
                    "-c:a", "pcm_s16le", "-f", "hash", "-"], text=True))
            self.assertAlmostEqual(*durations, delta=1 / 15)
            self.assertEqual(*audio_hashes)
            image = Image.open(io.BytesIO(subprocess.check_output([
                "ffmpeg", "-v", "error", "-i", str(exported), "-frames:v", "1",
                "-f", "image2pipe", "-vcodec", "png", "-"]))).convert("RGB")
            red, _green, blue = image.getpixel((32, 18))
            self.assertLess(red, 20)
            self.assertGreater(blue, 200)

    def test_preview_uses_finished_opening_not_last_scene_and_preserves_audio_timing(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for i in range(20):
                (directory / f"f{i:05d}.jpg").write_bytes(str(i).encode())
            cover = directory / "cover.jpg"
            plan = {"beats": [{"duration_ms": 1100, "words": [{"start_ms": 250}],
                               "ensemble": {"hold_window": {"start_ms": 910, "end_ms": 1080}},
                               "illustration": {"ops": [
                {"op": "DRAW", "end_ms": 290},
                {"op": "INK", "end_ms": 900},
            ]}}]}
            with patch.object(make_reel.subprocess, "run") as run:
                make_reel.sketch_posterize(directory, "original.mp4", "out.mp4", cover, plan, 10)
            self.assertEqual(b"10", cover.read_bytes())
            command = run.call_args.args[0]
            self.assertIn("[0:v][1:v]overlay=shortest=1:enable='lt(t,0.250000)'[v]", command)
            self.assertNotIn("-t", command)
            self.assertNotIn("-shortest", command)
            self.assertEqual("copy", command[command.index("-c:a") + 1])
            self.assertNotIn("xfade", " ".join(command))
            self.assertNotIn("adelay", " ".join(command))

    def test_preview_never_samples_the_next_beat(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for i in range(20):
                (directory / f"f{i:05d}.jpg").write_bytes(str(i).encode())
            cover = directory / "cover.jpg"
            plan = {"beats": [{"duration_ms": 300, "words": [{"start_ms": 100}],
                               "ensemble": {"hold_window": {"start_ms": 180, "end_ms": 250}},
                               "illustration": {"ops": [
                {"op": "DRAW", "end_ms": 150},
            ]}}]}
            with patch.object(make_reel.subprocess, "run"):
                make_reel.sketch_posterize(directory, "original.mp4", "out.mp4", cover, plan, 10)
            self.assertEqual(b"2", cover.read_bytes())

    def test_preview_rejects_beats_without_a_completed_frame(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "f00000.jpg").write_bytes(b"opening")
            plan = {"beats": [{"duration_ms": 300, "words": [{"start_ms": 100}],
                               "ensemble": {"hold_window": {"start_ms": 220, "end_ms": 260}}}]}
            with self.assertRaisesRegex(ValueError, "completed first-scene frame"):
                make_reel.sketch_posterize(tmp, "original.mp4", "out.mp4",
                                          Path(tmp) / "cover.jpg", plan, 10)

    def test_preview_requires_actual_rendered_frames(self):
        with TemporaryDirectory() as tmp:
            plan = {"beats": [{"duration_ms": 1000, "illustration": {"ops": []}}]}
            with self.assertRaisesRegex(ValueError, "requires rendered opening frames"):
                make_reel.sketch_posterize(tmp, "original.mp4", "out.mp4",
                                         Path(tmp) / "cover.jpg", plan, 15)


def author(script, style="sketch"):
    words, t = [], 0
    for text in script.split():
        words.append({"text": text, "start_ms": t, "end_ms": t + 400})
        t += 480 + (600 if make_reel.CLAUSE_END.search(text) else 0)
    film = make_reel.build_treatment(SimpleNamespace(aspects="16x9"),
                                     make_reel.style_of(style), words, [], "sketch-test")
    FilmTreatment.parse(film)
    return film


class SketchAuthoringTests(unittest.TestCase):
    def test_short_spoken_claims_share_context_and_keep_every_word(self):
        for sentences in (
            ("A pump sends water.", "The water enters a tank.", "The tank feeds a house."),
            ("A printer prints a page.", "The page goes to a tray.", "The tray holds the document."),
        ):
            with self.subTest(sentences=sentences):
                stream, t = [], 0
                for si, sentence in enumerate(sentences):
                    for wi, word in enumerate(sentence.split()):
                        duration = 440 if si == 0 and wi == len(sentence.split()) - 1 else 200
                        stream.append({"text": word, "start_ms": t, "end_ms": t + duration})
                        t += duration
                    t += 460
                groups = make_reel.sketch_groups(stream)
                self.assertEqual(2, len(groups))
                self.assertEqual(sentences[0], " ".join(w["text"] for w in groups[0]))
                self.assertEqual(" ".join(sentences[1:]), " ".join(w["text"] for w in groups[1]))
                self.assertEqual(stream, [w for g in groups for w in g])

    def test_source_linked_transfer_chain_keeps_one_visual_story(self):
        text = "A pump sends water to a tank. The tank feeds a house."
        stream = [{"text": w, "start_ms": i * 280, "end_ms": i * 280 + 210}
                  for i, w in enumerate(text.split())]
        groups = make_reel.sketch_groups(stream)
        self.assertEqual(len(groups), 1, "Dependent source actions need continuous visual causality")
        self.assertEqual(" ".join(w["text"] for group in groups for w in group), text)
        beat = make_reel.sketch_beat(groups[0], 0, 1, set(), [])
        self.assertEqual(beat["narration"], text)
        self.assertGreaterEqual(len(beat["illustration"]["relations"]), 2)
        edges = {(x["source"], x["target"]) for x in beat["illustration"]["relations"]}
        self.assertIn(("sk_pump", "sk_water"), edges)
        self.assertIn(("sk_water", "sk_tank"), edges, "The narrated water must reach the tank")
        self.assertIn(("sk_tank", "sk_house"), edges)
        named = {e.get("phrase"): e["glyph"] for e in beat["illustration"]["entities"]}
        self.assertEqual(named.get("pump"), "PUMP")
        self.assertEqual(named.get("tank"), "TANK")
        # A water transfer is a mechanical action, not anonymous pill text.
        self.assertEqual(named.get("water"), "TILE")
        FilmTreatment.parse(author(text))

    def test_native_solver_accepts_authored_forms_without_empty_satellites(self):
        solver = IllustrationSolver("16x9", (1920, 1080), IllustrationRegistry(), {}, {},
                                    "#2f6fb3", collage=True, finish="PRODUCT_COLLAGE")
        zone = {"x": 96, "y": 390, "w": 1728, "h": 594}
        for script in ("The server connects to a database.",
                       "A phone sends a message to a server.",
                       "A device sends an instruction to a printer.",
                       "A pencil is lighter than a brick.",
                       "A note becomes a list."):
            with self.subTest(script=script):
                beat = FilmTreatment.parse(author(script)).beats[0]
                placed, failures = solver.layout(beat.illustration, zone, beat.beat_id)
                self.assertFalse(failures)
                self.assertEqual(len(beat.illustration.entities), len(placed))

    def test_claims_and_negation_are_visible_without_fabricated_connectors(self):
        script = ("A policy can improve access without solving every problem. "
                  "Lower costs do not necessarily mean better service.")
        film = author(script)
        self.assertEqual(2, len(film["beats"]))
        self.assertEqual(script, " ".join(b["narration"] for b in film["beats"]))
        for beat in film["beats"]:
            self.assertEqual(beat["narration"],
                             " ".join(u["text"] for u in beat["display_units"]))
            self.assertEqual(1, sum(u["role"] == "hero" for u in beat["display_units"]))
            self.assertTrue(all(u["reveal"] == "WORD_CASCADE" for u in beat["display_units"]))
        self.assertEqual("RELATIONSHIP", film["beats"][0]["illustration"]["form"])
        self.assertEqual("sk_access", film["beats"][0]["illustration"]["relations"][0]["target"])
        self.assertEqual("COMPARISON", film["beats"][1]["illustration"]["form"])
        self.assertEqual("compares", film["beats"][1]["illustration"]["relations"][0]["type"])
        self.assertIn("not necessarily", " ".join(u["text"] for u in film["beats"][1]["display_units"]))
        ops = film["beats"][1]["illustration"]["program"]
        self.assertFalse(any(p["op"] == "INK" and p["target"] == "sk_better_service" for p in ops))
        self.assertTrue(any(p["op"] == "DIM" and "->" in p["target"] for p in ops))
        parsed = FilmTreatment.parse(film)
        for beat in parsed.beats:
            perf = ktp.compile_performance(beat.beat_type, "16x9", 4000,
                                           [u.ktp_unit() for u in beat.units], object_present=True)
            self.assertEqual(beat.narration, " ".join(b["text"] for b in
                                                    sorted(perf["text_blocks"], key=lambda b: b["unit_index"])))

    def test_process_and_relationship_use_existing_native_forms_and_carry(self):
        beats = author("A sensor sends a signal to an app. "
                       "The sensor then connects to the app.")["beats"]
        self.assertEqual("PROCESS_PIPELINE", beats[0]["illustration"]["form"])
        self.assertEqual("RELATIONSHIP", beats[1]["illustration"]["form"])
        self.assertEqual([("sk_sensor", "sk_signal"), ("sk_signal", "sk_app")],
                         [(r["source"], r["target"]) for r in beats[0]["illustration"]["relations"]])
        self.assertEqual({"from_beat": "b01", "entities": ["sk_app", "sk_sensor"]},
                         beats[1]["illustration"]["carry"])
        self.assertFalse(any(p["op"] == "DRAW" for p in beats[1]["illustration"]["program"]))

    def test_unpictured_flow_payload_uses_source_label_and_connects_before_destination(self):
        for script, noun in (("The database sends a result to the phone.", "result"),
                             ("A device sends an instruction to a printer.", "instruction")):
            with self.subTest(script=script):
                beat = author(script)["beats"][0]["illustration"]
                payload = next(e for e in beat["entities"] if e["phrase"] == noun)
                self.assertEqual(("PILL", noun, None),
                                 (payload["glyph"], payload["label"], payload.get("asset_ref")))
                connectors = [p for p in beat["program"] if p["op"] == "CONNECT"]
                self.assertEqual([{"word": "sends"}, {"word": noun}],
                                 [p["at"] for p in connectors])

    def test_unpictured_concepts_are_label_carriers_not_empty_shapes(self):
        for script in ("A policy can improve access without solving every problem.",
                       "Plants make seeds, but not every visit succeeds.",
                       "The printer sends an unknown instruction to the server."):
            with self.subTest(script=script):
                for beat in author(script)["beats"]:
                    for entity in beat["illustration"]["entities"]:
                        self.assertNotEqual("NODE", entity["glyph"])
                        if entity["kind"] != "evidence" and not entity.get("asset_ref"):
                            self.assertEqual("PILL", entity["glyph"])
                            self.assertTrue(entity["label"])

    def test_existing_carrier_attachment_and_transfer_generalise_beyond_bees(self):
        for script, carrier, host, destination, verb, move in (
            ("Pollen sticks to the bee. The bee carries pollen to another flower.",
             "pollen", "bee", "another_flower", "sticks", "carries"),
            ("A label attaches to the package. The package carries the label to a depot.",
             "label", "package", "depot", "attaches", "carries"),
        ):
            with self.subTest(script=script):
                stream, t = [], 0
                for word in script.split():
                    stream.append({"text": word, "start_ms": t, "end_ms": t + 200})
                    t += 200 + (460 if make_reel.CLAUSE_END.search(word) else 0)
                film = make_reel.build_treatment(SimpleNamespace(aspects="16x9,9x16,1x1"),
                                                 make_reel.style_of("sketch"), stream, [], "carrier-test")
                self.assertEqual(1, len(film["beats"]))
                beat = film["beats"][0]
                self.assertEqual(script, beat["narration"])
                ill = beat["illustration"]
                self.assertEqual("PROCESS_PIPELINE", ill["form"])
                self.assertEqual([("sk_" + host, "sk_" + carrier, "connects"),
                                  ("sk_" + carrier, "sk_" + destination, "flows_to")],
                                 [(r["source"], r["target"], r["type"]) for r in ill["relations"]])
                self.assertEqual("PILL", next(e for e in ill["entities"]
                                              if e["id"] == "sk_" + carrier)["glyph"])
                self.assertFalse(any(e["glyph"] == "NODE" for e in ill["entities"]))
                self.assertEqual([{"word": verb}, {"word": move}],
                                 [op["at"] for op in ill["program"] if op["op"] == "CONNECT"])
                self.assertEqual([("sk_" + carrier, verb), ("sk_" + destination, move)],
                                 [(op["target"], op["at"]["word"])
                                  for op in ill["program"] if op["op"] == "INK"])
                FilmTreatment.parse(film)

    def test_outcome_carries_only_positive_source_claims(self):
        beat = author("Pollination helps plants make seeds, but not every visit succeeds.")["beats"][0]
        ill = beat["illustration"]
        self.assertEqual("PROCESS_PIPELINE", ill["form"])
        self.assertEqual(["sk_pollination", "sk_plants", "sk_seeds"],
                         [e["id"] for e in ill["entities"]])
        self.assertEqual([("sk_pollination", "sk_plants"), ("sk_plants", "sk_seeds")],
                         [(r["source"], r["target"]) for r in ill["relations"]])
        self.assertIn("not every visit succeeds", " ".join(u["text"] for u in beat["display_units"]))

    def test_kinetic_emphasis_uses_spoken_source_without_repeated_anchor_or_truncation(self):
        for script in (
            "A battery sends energy to a lamp.",
            "A battery can't store unlimited energy.",
            "Lower costs do not necessarily mean better service.",
            "A valve reduces the flow.",
        ):
            with self.subTest(script=script):
                beat = author(script)["beats"][0]
                units = beat["display_units"]
                self.assertEqual(script, " ".join(u["text"] for u in units))
                self.assertEqual(2, len(units))
                self.assertTrue(all(u["reveal"] == "WORD_CASCADE" for u in units))
                self.assertFalse(units[0]["can_promote"])
                self.assertTrue(units[1]["can_promote"])
                self.assertGreater(units[1]["emphasis"], units[0]["emphasis"])
                self.assertNotIn(make_reel.word_key(units[1]["anchor_word"]),
                                 [make_reel.word_key(w) for w in units[0]["text"].split()])
                perf = ktp.compile_performance(beat["beat_type"], "16x9", 4000,
                                               [u.ktp_unit() for u in FilmTreatment.parse(author(script)).beats[0].units],
                                               object_present=True)
                self.assertEqual(script, " ".join(b["text"] for b in
                                                sorted(perf["text_blocks"], key=lambda b: b["unit_index"])))
                sizes = {b["unit_index"]: b["font_scale"] for b in perf["text_blocks"]}
                self.assertGreater(sizes[1], sizes[0])
                if "can't" in script:
                    self.assertIn("can't", units[1]["stress"])

    def test_native_cascade_matches_every_spoken_word_including_repeated_nouns(self):
        script = "A pump sends water to a pipe. The pipe carries water to a tank."
        film = FilmTreatment.parse(author(script))
        compiler = BeatCompiler(film, "16x9", None)
        for beat in film.beats:
            clock = beat_clock(beat.beat_id, [u.text for u in beat.units],
                               [u.anchor_word for u in beat.units],
                               synthesise_alignment(beat.narration, "kinetic"), "FIXTURE")
            blocks = [{"unit_index": i, "fit": {"lines": [u.text]}}
                      for i, u in enumerate(beat.units)]
            compiler._word_cascade(beat, blocks, [], clock)
            revealed = [w for block in blocks for w in block["words"]]
            self.assertEqual([normalise(w.text) for w in clock.words],
                             [normalise(w["text"]) for w in revealed])
            self.assertEqual([w.start_ms for w in clock.words],
                             [w["start_ms"] for w in revealed])
            self.assertTrue(all(b["reveal"] == "WORD_CASCADE" for b in blocks))

    def test_conjoined_action_does_not_turn_the_previous_destination_into_the_actor(self):
        script = "A server sends a result to a phone and feeds the result to the phone."
        words = [{"text": word} for word in script.split()]
        entities = make_reel.sketch_entities(words, [])
        stages = make_reel.sketch_action_stages(script, entities)
        self.assertEqual(["sk_server", "sk_server"], [stage[0]["id"] for stage in stages])
        self.assertEqual(["sk_phone", "sk_phone"], [stage[2]["id"] for stage in stages])

    def test_another_referent_keeps_the_literal_icon_but_not_the_same_identity(self):
        beats = author("A bee visits a flower. The bee carries pollen to another flower.")["beats"]
        first = next(e for e in beats[0]["illustration"]["entities"] if e["id"] == "sk_flower")
        second = next(e for e in beats[1]["illustration"]["entities"]
                      if e["id"] == "sk_another_flower")
        self.assertEqual(first["asset_ref"], second["asset_ref"])
        self.assertNotIn("sk_flower", beats[1]["illustration"]["carry"]["entities"])

    def test_comparison_and_transformation_only_follow_positive_source(self):
        self.assertEqual("COMPARISON", author(
            "A pencil is lighter than a brick.")["beats"][0]["illustration"]["form"])
        self.assertEqual("STATE_TRANSFORMATION", author(
            "A note becomes a list.")["beats"][0]["illustration"]["form"])
        self.assertEqual("OBJECT_STAGE", author(
            "A note does not become a list.")["beats"][0]["illustration"]["form"])
        self.assertEqual("OBJECT_STAGE", author(
            "A paper sheet becomes stiffer.")["beats"][0]["illustration"]["form"])
        reverse = author("A message sends a result to a phone.")["beats"][0]
        self.assertEqual("sk_phone", reverse["illustration"]["relations"][-1]["target"])

    def test_asr_word_spacing_does_not_break_source_actions(self):
        script = "The server connects to a database."
        words = [{"text": " " + text, "start_ms": i * 480, "end_ms": i * 480 + 400}
                 for i, text in enumerate(script.split())]
        film = make_reel.build_treatment(SimpleNamespace(aspects="16x9"),
                                         make_reel.style_of("sketch"), words, [], "asr-test")
        self.assertEqual(script, film["beats"][0]["narration"])
        self.assertEqual("RELATIONSHIP", film["beats"][0]["illustration"]["form"])
        FilmTreatment.parse(film)

    def test_literal_registered_artwork_never_uses_wrong_bank_alias(self):
        entities = author("A phone sends a message to a server.")["beats"][0]["illustration"]["entities"]
        self.assertEqual(["phone", "message", "server"], [e["phrase"] for e in entities])
        self.assertEqual(["icon.icon-park-outline.phone", "icon.icon-park-outline.message",
                          "icon.icon-park-outline.server"], [e["asset_ref"] for e in entities])
        self.assertIsNone(make_reel.sketch_asset("river bank", "A river bank floods."))

    def test_existing_artwork_precedes_text_without_confusing_umbrella_with_shadow(self):
        from editorial_plan_compiler.illustration import IllustrationRegistry

        beat = author("A tree makes shade for seedlings, but not every seed can grow without sunlight.")["beats"][0]
        entities = beat["illustration"]["entities"]
        tree = next(e for e in entities if e["phrase"] == "tree")
        shade = next(e for e in entities if e["phrase"] == "shade")
        self.assertEqual(("TILE", "icon.icon-park-color.tree"),
                         (tree["glyph"], tree["asset_ref"]))
        self.assertEqual(("PILL", "shade", None),
                         (shade["glyph"], shade["label"], shade.get("asset_ref")))
        art = IllustrationRegistry().resolve(tree["asset_ref"], beat["beat_id"])
        self.assertEqual("Apache-2.0", art["license"])
        self.assertEqual("icon.icon-park-color.seedling",
                         make_reel.sketch_asset("seedlings", "Seedlings need sunlight."))
        self.assertEqual("icon.icon-park-color.tree",
                         make_reel.sketch_asset("trees", "Trees make shade."))
        self.assertEqual("icon.icon-park-color.lamp",
                         make_reel.sketch_asset("lamp", "A lamp turns on."))

    def test_new_subject_has_native_cut_and_repeated_subject_keeps_carry(self):
        beats = author("A phone sends a message to a server. "
                       "The server connects to a database. "
                       "A mountain is taller than a bicycle.")["beats"]
        self.assertEqual("hard", beats[0]["cut"])
        self.assertIn("carry", beats[1]["illustration"])
        self.assertEqual("hard", beats[1]["cut"])
        parsed = FilmTreatment.parse(author("A phone sends a message to a server. "
                                           "The server connects to a database."))
        self.assertEqual("cut", camera_move(parsed.beats[0], parsed.beats[1],
                                            "SETTLE_CUT", 0, False)["move"])

    def test_interface_is_not_selected_for_unrelated_claims(self):
        abstract = author("The paper dries and becomes stiffer.")["beats"][0]
        self.assertFalse(any("field" in (e.get("label") or "") for e in abstract["illustration"]["entities"]))
        interface = author("Type oak into the search field.")["beats"][0]
        self.assertEqual("OBJECT_STAGE", interface["illustration"]["form"])
        self.assertIn("oak", interface["narration"])
        self.assertFalse(interface["illustration"]["relations"])

    def test_no_model_fallback_never_semantically_guesses_an_asset(self):
        with patch.object(make_reel, "_SKETCH_NLP", False):
            beat = author("A policy can improve access.")["beats"][0]
        self.assertTrue(all(e.get("asset_ref") is None for e in beat["illustration"]["entities"]))
        self.assertTrue(all((e.get("label") or "") in "a policy can improve access."
                            for e in beat["illustration"]["entities"]))

    def test_untouched_styles_retain_generic_authoring(self):
        for name in ("photo_story", "emoji", "journey", "collage"):
            with self.subTest(style=name):
                beat = author("The team builds an app.", name)["beats"][0]
                self.assertEqual(make_reel.display_units([
                    {"text": t, "start_ms": i * 480, "end_ms": i * 480 + 400}
                    for i, t in enumerate("The team builds an app.".split())
                ], {"team", "app"})[0]["text"], beat["display_units"][0]["text"])


if __name__ == "__main__":
    unittest.main()
