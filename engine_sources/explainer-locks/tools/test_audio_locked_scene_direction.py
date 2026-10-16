#!/usr/bin/env python3
"""Regression tests for voice-locked visual scene direction.

The intact aligned narration, not beat index or artificial end hold, owns
both a drawn subject's first appearance and its animated data state change.
These are executable compiler tests, not screenshot or storyboard guesses.
"""
from __future__ import annotations
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "compiler")]
import make_reel
from scene_director import direct_film
from editorial_plan_compiler.contracts import IllustrationDirective, BeatTreatment
from editorial_plan_compiler.illustration import IllustrationSolver, ENTER_MS
from editorial_plan_compiler.timing import BeatClock, Word


def make_clock(source, *, window=2500):
    words = [Word(word, start, start + 260) for word, start in source]
    return BeatClock(
        beat_id="b01", duration_ms=window, voice_offset_ms=0,
        voice_duration_ms=window-150, words=words,
        landings_ms=[180], landing_source=["WORD"], source="MASTER",
        exit_ms=320)


class AudioLockedSceneDirectionTests(unittest.TestCase):
    def test_named_character_enters_with_spoken_noun_not_first_beat_word(self):
        clock = make_clock([("The", 120), ("courier", 1060),
                            ("carries", 1390), ("parcel", 1750)])
        definition = {
            "form": "OBJECT_STAGE",
            "entities": [{"id": "courier", "kind": "object", "glyph": "TILE",
                          "size": "hero", "label": "courier",
                          "params": {"visual_class": "person", "voice_cued": True}}],
            "relations": [],
            "program": [{"op": "DRAW", "target": "courier",
                         "at": {"word": "courier"}, "duration_ms": 460}],
            "confirmation": False}
        parsed = IllustrationDirective.parse(definition, 1, "b01")
        entities = [{"id": "courier", "params": definition["entities"][0]["params"]}]
        ops, enters, errors = IllustrationSolver.schedule(
            parsed, clock, entities, set(), "b01")
        self.assertFalse(errors)
        self.assertGreater(enters["courier"], 800)
        self.assertLess(enters["courier"], 1120)
        self.assertGreaterEqual(ops[0]["start_ms"], 1000)
        control = dict(entities[0])
        control["params"] = {"visual_class": "person"}
        _, old, old_errors = IllustrationSolver.schedule(
            parsed, clock, [control], set(), "b01")
        self.assertFalse(old_errors)
        self.assertLess(old["courier"], 220)

    def test_spoken_connection_finishes_with_recipient_not_a_disembodied_line(self):
        clock = make_clock([("The", 120), ("courier", 510),
                            ("sends", 1260), ("parcel", 2870),
                            ("to", 3090), ("driver", 4020)], window=6450)
        entities = [
            {"id": ident, "kind": "object", "glyph": "TILE",
             "size": "hero" if i == 0 else "support",
             "label": ident, "phrase": ident,
             "params": {"voice_cued": True,
                        "visual_class": "package" if ident == "parcel" else "person"}}
            for i, ident in enumerate(("courier", "parcel", "driver"))]
        d = {
            "form": "PROCESS_PIPELINE", "entities": entities,
            "relations": [
                {"type": "flows_to", "source": "courier", "target": "parcel"},
                {"type": "flows_to", "source": "parcel", "target": "driver"}],
            "program": [
                *[{"op": "DRAW", "target": name,
                   "at": {"word": name}, "duration_ms": 420,
                   "params": {"voice_sync": True}}
                  for name in ("courier", "parcel", "driver")],
                {"op": "CONNECT", "target": "courier->parcel",
                 "at": {"word": "sends"}, "duration_ms": 370,
                 "params": {"voice_sync": True}},
                {"op": "CONNECT", "target": "parcel->driver",
                 "at": {"word": "to"}, "duration_ms": 370,
                 "params": {"voice_sync": True}}],
            "confirmation": False}
        il = IllustrationDirective.parse(d, 1, "b01")
        scheduled, enters, failures = IllustrationSolver.schedule(
            il, clock, entities, set(), "b01")
        self.assertEqual(failures, [])
        self.assertGreater(enters["parcel"], 2600)
        self.assertGreater(enters["driver"], 3700)
        for connection in (op for op in scheduled if op["op"] == "CONNECT"):
            source, target = connection["target"].split("->")
            latest_visible = max(enters[source]+ENTER_MS,
                                 enters[target]+ENTER_MS)
            self.assertGreaterEqual(connection["end_ms"], latest_visible)
            self.assertTrue(connection["params"]["voice_link_waits_for_endpoint"])
        self.assertLess(scheduled[3]["start_ms"], enters["parcel"])
        self.assertLessEqual(max(o["end_ms"] for o in scheduled), clock.duration_ms)

    def test_late_data_does_not_reveal_before_its_word(self):
        clock = make_clock([("There", 160), ("were", 410),
                            ("only", 900), ("99", 2100)],
                           window=2500)
        definition = {
            "form": "OBJECT_STAGE",
            "entities": [{"id": "value", "kind": "evidence",
                          "glyph": "BAR", "size": "hero",
                          "params": {"value": 99, "level": .99}}],
            "relations": [],
            "program": [{
                "op": "GROW", "target": "value",
                "at": {"word": "99"}, "duration_ms": 620,
                "params": {"voice_sync": True}}],
            "confirmation": False}
        parsed = IllustrationDirective.parse(definition, 1, "b01")
        ents = [{"id": "value", "params": {}}]
        ops, _, errors = IllustrationSolver.schedule(parsed, clock, ents, set(), "b01")
        self.assertFalse(errors, errors)
        self.assertGreaterEqual(ops[0]["start_ms"], 2020)
        self.assertLessEqual(ops[0]["end_ms"], clock.duration_ms)
        self.assertLess(ops[0]["end_ms"]-ops[0]["start_ms"], 620)

    def test_directed_actor_and_data_ops_explicitly_voice_locked(self):
        def shot(text, style):
            words=[{"text":w,"start_ms":i*440,"end_ms":i*440+350}
                   for i,w in enumerate(text.split())]
            return (make_reel.sketch_beat(words,0,1,set(),[]) if style=="sketch"
                    else make_reel.dataviz_beat(words,0,1,[]))
        a=shot("The courier gives a parcel to the driver.", "sketch")
        direct_film("sketch",[a])
        person=[e for e in (a.get("illustration") or {}).get("entities",[])
                if (e.get("params") or {}).get("visual_class")=="person"]
        self.assertTrue(person)
        for ent in person:
            draws=[op for op in a["illustration"]["program"]
                   if op["op"]=="DRAW" and op["target"]==ent["id"]
                   and "word" in op.get("at",{})]
            if draws:
                self.assertTrue(ent["params"].get("voice_cued"))
                self.assertTrue(all(op.get("params",{}).get("voice_sync") for op in draws))
        BeatTreatment.parse(a)
        b=shot("The survey recorded 40 apples, 25 pears, and 30 oranges.", "dataviz")
        direct_film("dataviz",[b])
        cue=[o for o in (b.get("illustration") or {}).get("program",[])
             if o["op"]=="GROW"]
        self.assertTrue(cue)
        self.assertTrue(all(o.get("params",{}).get("voice_sync") for o in cue))
        BeatTreatment.parse(b)

    def test_voice_bound_cue_does_not_add_unspoken_visual_value(self):
        b = {
            "beat_id": "b01", "beat_type": "SETUP",
            "pattern": "PROGRESSIVE_HERO_BUILD", "dominant_layer": "HYBRID",
            "narration": "The researcher describes a hypothetical concept.",
            "display_units":[{"text":"The researcher describes a hypothetical concept.",
                              "role":"hero","reveal":"WORD_CASCADE"}],
            "illustration":{
                "form":"OBJECT_STAGE",
                "entities":[{"id":"concept","kind":"object","glyph":"PILL",
                             "size":"hero","label":"concept","phrase":"concept"}],
                "relations":[],"program":[{"op":"DRAW","target":"concept",
                                           "at":{"word":"concept"},"duration_ms":400}],
                "confirmation":False},
        }
        report=direct_film("sketch",[b])
        self.assertIn("b01",report["sketch_visual_coverage_failures"])
        self.assertEqual(b["narration"],"The researcher describes a hypothetical concept.")


if __name__=="__main__":
    unittest.main()
