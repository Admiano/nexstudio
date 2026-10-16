#!/usr/bin/env python3
"""Native Sketchbook-inspired actor state integration; no invented performance."""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"tools"),str(ROOT/"compiler")]
import make_reel
from sketch_actor_states import bind_actor_performances
from scene_director import direct_film
from editorial_plan_compiler.contracts import BeatTreatment


def shot(text):
    words=[{"text":w,"start_ms":i*480,"end_ms":i*480+360}
           for i,w in enumerate(text.split())]
    return make_reel.sketch_beat(words,0,1,set(),[])


class NativeSketchActorStatesTests(unittest.TestCase):
    def test_explicit_actor_verbs_produce_distinct_voice_anchored_states(self):
        cases=[
            ("The driver carries the parcel.", "driver", "OFFER", "carries"),
            ("The nurse inspects the document.", "nurse", "INSPECT", "inspects"),
            ("The courier walks toward the customer.", "courier", "WALK", "walks"),
            ("The teacher points at the report.", "teacher", "POINT", "points"),
            ("The courier runs toward the customer.", "courier", "RUN", "runs"),
            ("The driver turns toward the door.", "driver", "TURN", "turns"),
            ("The nurse listens to the patient.", "nurse", "LISTEN", "listens"),
            ("The courier waves to the driver.", "courier", "WAVE", "waves"),
            ("The nurse writes a note.", "nurse", "WRITE", "writes"),
            ("The driver lifts the parcel.", "driver", "LIFT", "lifts"),
            ("The teacher stops the group.", "teacher", "STOP", "stops"),
            ("The mechanic agrees with the driver.", "mechanic", "AGREE", "agrees"),
        ]
        for source, actor, state, word in cases:
            with self.subTest(source=source):
                b=shot(source)
                actions=bind_actor_performances(b)
                self.assertTrue(any(a["actor"]==actor and a["state"]==state
                                    and a["word"]==word for a in actions),actions)
                entity=next(e for e in b["illustration"]["entities"]
                            if e.get("phrase")==actor)
                self.assertEqual(entity["params"]["actor_identity"],actor)
                self.assertEqual(entity["params"]["actor_state"],state)
                cues = [o for o in b["illustration"]["program"]
                        if o["op"] == "SETTLE" and o["target"] == entity["id"]
                        and o["at"] == {"word": word}
                        and o.get("params", {}).get("actor_action") is True]
                self.assertEqual(len(cues), 1)
                cue = cues[0]
                self.assertIn(cue["duration_ms"], (600, 740, 860, 920))
                stages = cue["params"]["actor_state_path"]
                self.assertEqual(stages[0], "IDLE")
                self.assertEqual(stages[-1], "IDLE")
                self.assertEqual(stages[2], state)
                if state in ("WALK", "RUN"):
                    self.assertEqual(stages[1:4],
                                     ["START_MOVE", state, "END_MOVE"])
                else:
                    self.assertEqual(stages[1:4],
                                     ["ANTICIPATE", state, "RECOVER"])
                BeatTreatment.parse(b)

    def test_walk_then_wave_is_two_distinct_source_word_states(self):
        beat = shot("The courier walks then waves to the driver.")
        actions = bind_actor_performances(beat)
        self.assertEqual(actions, [
            {"actor": "courier", "state": "WALK", "word": "walks"},
            {"actor": "courier", "state": "WAVE", "word": "waves"}])
        actor = next(e for e in beat["illustration"]["entities"]
                     if e.get("phrase") == "courier")
        actions_ops = [op for op in beat["illustration"]["program"]
                       if op["target"] == actor["id"]
                       and op.get("params", {}).get("actor_action")]
        self.assertEqual(len(actions_ops), 2)
        self.assertEqual([op["at"]["word"] for op in actions_ops],
                         ["walks", "waves"])
        self.assertEqual([op["params"]["actor_state"] for op in actions_ops],
                         ["WALK", "WAVE"])
        self.assertEqual([op["params"]["actor_state_path"] for op in actions_ops],
                         [["IDLE","START_MOVE","WALK","END_MOVE","IDLE"],
                          ["IDLE","ANTICIPATE","WAVE","RECOVER","IDLE"]])
        self.assertTrue(all(op["params"]["voice_sync"] for op in actions_ops))
        self.assertEqual(beat["narration"], "The courier walks then waves to the driver.")
        BeatTreatment.parse(beat)

    def test_new_subject_does_not_inherit_actor_gestures(self):
        beat = shot("The courier walks and the driver waves.")
        actions = bind_actor_performances(beat)
        self.assertFalse(any(a["actor"] == "courier" and a["state"] == "WAVE"
                             for a in actions))
        BeatTreatment.parse(beat)

    def test_two_coordinated_actions_belong_to_the_same_explicit_actor(self):
        for speech, who, expected in [
            ("The driver turns toward the loading platform and points at the document.",
             "driver", [("TURN", "turns"), ("POINT", "points")]),
            ("The technician connects the pump and tests the pressure.",
             "technician", [("CONNECT", "connects"), ("TEST", "tests")]),
            ("The nurse inspects the folder and writes a note.",
             "nurse", [("INSPECT", "inspects"), ("WRITE", "writes")]),
            ("The mechanic repairs the pump and checks the valve.",
             "mechanic", [("REPAIR", "repairs"), ("INSPECT", "checks")]),
        ]:
            with self.subTest(speech=speech):
                b=shot(speech)
                perf=bind_actor_performances(b)
                own=[x for x in perf if x["actor"]==who]
                self.assertEqual([(x["state"],x["word"]) for x in own], expected)
                actions=[o for o in b["illustration"]["program"]
                         if o.get("params",{}).get("actor_action")
                         and o["target"]=="sk_"+who]
                self.assertEqual([o["params"]["actor_state"] for o in actions],
                                 [x[0] for x in expected])
                for o in actions:
                    index=o["params"]["word_index"]
                    self.assertEqual(b["narration"].split()[index].strip(".,!?").lower(),
                                     o["at"]["word"].lower())
                    self.assertTrue(o["params"]["voice_sync"])
                BeatTreatment.parse(b)

    def test_new_subject_never_steals_second_actor_action(self):
        b=shot("The courier walks and the driver waves to the customer.")
        perf=bind_actor_performances(b)
        self.assertNotIn(("courier", "WAVE"),
                         {(e["actor"], e["state"]) for e in perf})
        self.assertIn(("driver", "WAVE"),
                      {(e["actor"], e["state"]) for e in perf})

    def test_duplicate_spoken_verb_has_distinct_voice_indices(self):
        b=shot("The courier walks then waves and walks toward the depot.")
        perf=bind_actor_performances(b)
        self.assertEqual([e["state"] for e in perf
                          if e["actor"]=="courier"], ["WALK","WAVE","WALK"])
        ops=[o for o in b["illustration"]["program"]
             if o.get("params",{}).get("actor_action")
             and o["target"]=="sk_courier"]
        indices=[o["params"]["word_index"] for o in ops]
        self.assertEqual(len(indices), 3)
        self.assertEqual(sorted(indices),indices)
        self.assertEqual(len(set(indices)),3)
        BeatTreatment.parse(b)

    def test_actor_actions_schedule_on_separate_spoken_words(self):
        from editorial_plan_compiler.timing import Word, BeatClock
        from editorial_plan_compiler.illustration import IllustrationSolver
        from editorial_plan_compiler.contracts import IllustrationDirective
        beat = shot("The courier walks then waves to the driver.")
        bind_actor_performances(beat)
        il = IllustrationDirective.parse(beat["illustration"],
                                         len(beat["display_units"]), beat["beat_id"])
        words = [Word(token, 100 + i * 480, 100 + i*480 + 280)
                 for i, token in enumerate(beat["narration"].split())]
        clock = BeatClock(beat_id=beat["beat_id"], duration_ms=4100,
                          voice_offset_ms=0, voice_duration_ms=3800,
                          words=words, landings_ms=[180] * len(beat["display_units"]),
                          landing_source=["WORD"]*len(beat["display_units"]),
                          source="MASTER", exit_ms=220)
        scheduled, _, errors = IllustrationSolver.schedule(
            il, clock, beat["illustration"]["entities"], set(), beat["beat_id"])
        self.assertEqual(errors, [])
        ops = [op for op in scheduled if op["op"] == "SETTLE"
               and op["params"].get("actor_action")]
        self.assertEqual(len(ops), 2)
        self.assertEqual([o["params"]["actor_state"] for o in ops],
                         ["WALK","WAVE"])
        onset = {w.text: w.start_ms for w in words}
        for word, op in zip(("walks","waves"), ops):
            self.assertGreaterEqual(op["start_ms"], onset[word]-100)
            self.assertLessEqual(op["start_ms"], onset[word]+60)
        self.assertLess(ops[0]["start_ms"], ops[1]["start_ms"])

    def test_recipient_does_not_act_as_source(self):
        b=shot("The courier gives a package to the driver.")
        actions=bind_actor_performances(b)
        self.assertTrue(any(a["actor"]=="courier" for a in actions))
        self.assertFalse(any(a["actor"]=="driver" for a in actions))
        BeatTreatment.parse(b)

    def test_state_direction_requires_source_named_person(self):
        b=shot("The pump sends water into the tank.")
        actions=bind_actor_performances(b)
        self.assertEqual(actions,[])
        BeatTreatment.parse(b)

    def test_sketch_refuses_word_only_card(self):
        beat = {
            "beat_id": "b01", "narration": "A hypothetical concept is mentioned.",
            "beat_type": "SETUP", "pattern": "PROGRESSIVE_HERO_BUILD",
            "dominant_layer": "HYBRID",
            "display_units": [{
                "text": "A hypothetical concept is mentioned.",
                "role": "hero", "anchor_word": "A", "reveal": "WORD_CASCADE"}],
            "illustration": {
                "form": "OBJECT_STAGE",
                "entities": [{"id":"concept","kind":"object","glyph":"PILL",
                              "size":"hero","label":"concept","phrase":"concept"}],
                "relations": [], "program": [
                    {"op":"DRAW","target":"concept",
                     "at":{"word":"concept"},"duration_ms":420}],
                "confirmation":False},
        }
        report = direct_film("sketch", [beat])
        self.assertEqual(report["sketch_visual_coverage_failures"], ["b01"])
        self.assertEqual(beat["features"]["sketch_visual_coverage"], 0.0)
        self.assertEqual(beat["narration"], "A hypothetical concept is mentioned.")

    def test_unillustrated_exact_counts_gain_native_visual_without_false_people(self):
        for claim, count in [
            ("The test identifies 99 genuine cases.", 99),
            ("That makes 594 positive results altogether.", 594),
            ("But only 99 of those are genuine.", 99),
        ]:
            with self.subTest(claim=claim):
                beat = shot(claim)
                report = direct_film("sketch", [beat])
                self.assertEqual(report["sketch_visual_coverage_failures"], [])
                visual = beat["illustration"]["entities"]
                self.assertEqual(visual[0]["glyph"], "BASE10_TALLY")
                self.assertEqual(visual[0]["params"]["value"], count)
                self.assertEqual(beat["narration"], claim)
                BeatTreatment.parse(beat)

    def test_film_director_integrates_identity_and_script_actions(self):
        b=shot("The nurse inspects the document.")
        report=direct_film("sketch",[b])
        self.assertIn({"actor":"nurse","state":"INSPECT","word":"inspects"},
                      report["scenes"][0]["actor_actions"])
        BeatTreatment.parse(b)

if __name__=="__main__":
    unittest.main()
