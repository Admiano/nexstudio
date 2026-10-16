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
            ("The teacher points at the report.", "teacher", "PRESENT", "points"),
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
                self.assertTrue(any(o["op"]=="SETTLE" and o["target"]==entity["id"]
                                    and o["at"]=={"word":word} and
                                    o.get("params",{}).get("actor_action") is True
                                    for o in b["illustration"]["program"]))
                BeatTreatment.parse(b)

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
        with self.assertRaisesRegex(ValueError, "SKETCH_VISUAL_SUBJECT_REQUIRED"):
            direct_film("sketch", [beat])

    def test_film_director_integrates_identity_and_script_actions(self):
        b=shot("The nurse inspects the document.")
        report=direct_film("sketch",[b])
        self.assertIn({"actor":"nurse","state":"INSPECT","word":"inspects"},
                      report["scenes"][0]["actor_actions"])
        BeatTreatment.parse(b)

if __name__=="__main__":
    unittest.main()
