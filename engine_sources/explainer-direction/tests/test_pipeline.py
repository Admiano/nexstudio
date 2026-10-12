"""Explicit synthetic provider tests. None of these voices prove production TTS."""
from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

ENGINE = Path(__file__).resolve().parents[1]
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))
from explainer_direction import audio  # noqa: E402
from explainer_direction.authoring import bind_alignment  # noqa: E402
from explainer_direction.compiler import compile_score  # noqa: E402
from explainer_direction.contracts import sample_score, validate_score, ScoreError  # noqa: E402

spec = importlib.util.spec_from_file_location("direction_pipeline_tests", ENGINE / "tools/make_film.py")
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
spec = importlib.util.spec_from_file_location("direction_adapter_tests", REPO / "services/studio-family-engines/explainer_direction_adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

PROOF_ROOT = Path("/home/ubuntu/vid_study/explainer_direction")
SOURCE = {"id": "fixture_audio", "uri": "test-fixture://pipeline", "locator": "Synthetic sine-wave tests, not speech or rights proof",
          "license": "owned", "commercial_use": True}


def sine(path, milliseconds):
    samples = bytearray()
    for n in range(round(milliseconds * 24)):
        value = int(5000 * math.sin(n * 2 * math.pi * 220 / 24000))
        samples.extend(value.to_bytes(2, "little", signed=True))
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
        wav.writeframes(samples)


def reported(text):
    t, words = 80, []
    for index, token in enumerate(text.split()):
        end = t + 100 + index * 23
        words.append({"word": token, "start_ms": t, "end_ms": end})
        t = end + 71
    return words


class FixtureTTS:
    is_test_fixture = True

    def __init__(self, milliseconds=6000, aligned=True, corrupt=None):
        self.milliseconds, self.aligned, self.corrupt = milliseconds, aligned, corrupt

    def synthesize(self, text, output, *, scene_id, film_id):
        sine(output, self.milliseconds)
        alignment = {"provider": "test-fixture-tts", "method": "provider_word_timestamps", "audio_sha256": audio.sha256(output),
                     "words": reported(text)} if self.aligned else None
        if self.corrupt and alignment:
            alignment.update(self.corrupt)
        return {"audio_path": str(output), "source": SOURCE, "provider": "test-fixture-tts", "route": "synthetic-test-only",
                "local": True, "alignment": alignment, "test_fixture": True}


class FixtureAligner:
    is_test_fixture = True

    def align(self, text, path, *, scene_id):
        return {"provider": "test-fixture-aligner", "method": "forced_alignment", "audio_sha256": audio.sha256(path), "words": reported(text)}


class FixtureAuthor:
    is_test_fixture = True
    identity = {"provider": "fixture-author", "model": "test-only"}

    def complete(self, task, request):
        if task == "plan_strategies":
            return {"strategies": [{"id": name, "thesis": "Test a mechanism", "rationale": "Explicit test-only competition",
                     "representation": ["number", "bar", "selector"], "relation_pattern": [rel], "progression": ["update", "hold"],
                     "composition": flow} for name, rel, flow in (("a", "labels", "row"), ("b", "supports", "column"))]}
        if task == "author_score":
            score = sample_score("water")
            score["film_id"] = request.get("film_id", "fixture_author")
            score["scenes"][0]["relations"][0]["kind"] = request["strategy"]["relation_pattern"][0]
            score["scenes"][0]["composition"]["flow"] = request["strategy"]["composition"]
            return {k: score[k] for k in ("film_id", "title", "style", "sections", "scenes")}
        if task == "plan_score":
            score = self.complete("author_score", request)
            score["scene_briefs"] = [{k: scene[k] for k in ("id", "section_id", "intent", "claim_ids", "duration_ms")}
                                    for scene in score.pop("scenes")]
            return score
        if task == "author_scene":
            scene = self.complete("author_score", request)["scenes"][0]
            scene.pop("events")
            return scene
        if task == "author_choreography":
            events = self.complete("author_score", request)["scenes"][0]["events"]
            names = {event["id"]: request["event_id_prefix"] + event["id"] for event in events}
            for event in events:
                event["id"] = names[event["id"]]
                event["dependencies"] = [names[name] for name in event["dependencies"]]
                event.pop("targets")
            return {"events": events}
        if task in ("select_candidate", "select_strategy"):
            return {"selected_id": "a", "distinct": True, "authority": "DEVELOPMENT_PREFLIGHT", "rationale": "Tests only",
                    "findings": [{"strategy_id": s["id"], "strength": "Linked semantic state", "risk": "No production inference proof"} for s in request["strategies"]]}
        raise AssertionError(task)


def fake_render(plan, output, **kwargs):
    output.mkdir()
    audio.write_json(output / "test-only-render.json", {"fixture": True, "plan_sha256": audio.sha256(plan)})
    return {"test_fixture": True}


def p8_score():
    score = sample_score("water")
    score["provenance"].pop("test_fixture")
    score["provenance"].update(mode="p8_bound", status="P8_SEMANTIC_BOUND", p8={"state_hash": "a" * 64, "board_hash": "b" * 64})
    return validate_score(score)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pipeline-fixture-", dir=PROOF_ROOT)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def voice(self, score=None, provider=None, **options):
        return audio.produce_voice(score or sample_score("water"), self.root / "voice", provider or FixtureTTS(), test_fixture=True, **options)

    def film(self, score=None, **options):
        return pipeline.run_pipeline(output=self.root / "film", score=score or sample_score("water"),
                  voice_provider=FixtureTTS(), test_fixture=True, renderer=fake_render, **options)

    def test_inventory_hashes_nested_manifests_and_fails_symlink_with_manifest(self):
        out = self.root / "inventory"
        nested = out / "sub"
        nested.mkdir(parents=True)
        audio.write_json(out / "manifest.json", {"final":True})
        audio.write_json(nested / "manifest.json", {"nested":True})
        self.assertEqual([r["path"] for r in pipeline._inventory(out)], ["sub/manifest.json"])
        target = self.root / "external.txt"
        target.write_text("Explicit test-only escape", encoding="utf-8")
        def escape_renderer(plan, output, **kwargs):
            result = fake_render(plan, output, **kwargs)
            (output / "escape.txt").symlink_to(target)
            return result
        with self.assertRaisesRegex(pipeline.PipelineError, "OUTPUT_SNAPSHOT_ESCAPE"):
            pipeline.run_pipeline(output=self.root / "escaping-film", score=sample_score(), voice_provider=FixtureTTS(),
                                  renderer=escape_renderer, test_fixture=True)
        failed = pipeline.json_file(self.root / "escaping-film/manifest.json")
        self.assertEqual(failed["status"], "FAILED")
        self.assertTrue(any("OUTPUT_SNAPSHOT_ESCAPE" in e["message"] for e in failed["errors"]))

    def test_three_unrelated_topics_native_semantics_and_hashes(self):
        for topic in ("water", "energy", "travel"):
            with self.subTest(topic=topic):
                out = self.root / topic
                manifest = pipeline.run_pipeline(output=out, score=sample_score(topic), voice_provider=FixtureTTS(),
                            test_fixture=True, renderer=fake_render)
                self.assertEqual(manifest["status"], "TEST_FIXTURE_RENDER_READY")
                self.assertFalse(manifest["authority"]["creative_lock"])
                self.assertFalse(manifest["authority"]["public_dispatch_enabled"])
                self.assertEqual(len(manifest["renders"]), 3)
                self.assertTrue(manifest["voice"]["alignment_complete"])
                self.assertTrue(any("provisional" in g for g in manifest["gaps"]))
                for record in manifest["artifacts"]:
                    self.assertEqual(audio.sha256(out / record["path"]), record["sha256"])
                plans = [pipeline.json_file(out / f"plan-{a.replace(':','x')}.json") for a in manifest["aspects"]]
                self.assertEqual({(p["canvas"]["width"], p["canvas"]["height"]) for p in plans}, {(1920,1080),(1080,1920),(1080,1080)})
                self.assertEqual([p["scenes"][0]["events"][0]["start_ms"] for p in plans], [2100] * 3)
                self.assertEqual([p["duration_ms"] for p in plans], [6000] * 3)

    def test_live_authoring_uses_explicit_test_provider_only(self):
        score = sample_score("water")
        result = pipeline.run_pipeline(output=self.root / "film", brief="Test-only cache transport", evidence=score["evidence"],
                 provider=FixtureAuthor(), voice_provider=FixtureTTS(), renderer=fake_render, test_fixture=True, film_id="fixture_author")
        self.assertEqual(result["film_id"], "fixture_author")
        actual = pipeline.json_file(self.root / "film/authored-score.json")
        self.assertEqual(actual["brief"], "Test-only cache transport")
        self.assertTrue(actual["provenance"]["test_fixture"])

    def test_test_injection_is_not_live_mode(self):
        with self.assertRaisesRegex(pipeline.PipelineError, "TEST_ONLY"):
            pipeline.run_pipeline(output=self.root / "bad", score=sample_score(), voice_provider=FixtureTTS(), renderer=fake_render)
        with self.assertRaisesRegex(audio.AudioError, "TEST_PROVIDER"):
            audio.produce_voice(sample_score(), self.root / "bad", FixtureTTS())

    def test_audio_exact_pcm_and_word_cue_from_uneven_edges(self):
        score = sample_score("water")
        score["scenes"][0]["events"][0]["cue"] = {"kind": "word", "word": "second", "occurrence": 0, "edge": "start"}
        voice = self.voice(score, FixtureTTS(6000.375))
        bound = bind_alignment(score, voice["alignment"])
        word = next(w for w in reported(score["scenes"][0]["narration"]) if w["word"] == "second")
        self.assertEqual(bound["scenes"][0]["duration_ms"], 6001)
        self.assertEqual(bound["scenes"][0]["events"][0]["cue"]["resolved_ms"], word["start_ms"])
        plan = compile_score(bound, "9:16")
        self.assertEqual(plan["scenes"][0]["events"][0]["start_ms"], word["start_ms"])
        self.assertEqual(voice["alignment"]["source"]["audio_sha256"], audio.sha256(voice["path"]))
        self.assertAlmostEqual(audio.duration_ms(voice["path"]), 6001, places=2)
        self.assertGreater(voice["segments"][0]["pad_ms"], 0)
        self.assertLess(voice["segments"][0]["pad_ms"], 1)

    def test_multiscene_audio_order_and_master_alignment(self):
        score = sample_score("water")
        second = deepcopy(score["scenes"][0])
        second["id"] = "later"
        second["composition"]["focus"] += "_later"
        for actor in second["actors"]:
            actor["id"] += "_later"
            if actor["layout"].get("relative_to"):
                actor["layout"]["relative_to"] += "_later"
        for rel in second["relations"]:
            rel["id"] += "_later"
            rel["from"] += "_later"
            rel["to"] += "_later"
        for event in second["events"]:
            event["id"] += "_later"
            event["targets"] = [t + "_later" for t in event["targets"]]
            event["changes"] = {k + "_later": v for k,v in event["changes"].items()}
            event["dependencies"] = [d + "_later" for d in event["dependencies"]]
            if "value_bindings" in event:
                event["value_bindings"] = {k + "_later": v for k,v in event["value_bindings"].items()}
        score["scenes"].append(second)
        voice = self.voice(validate_score(score))
        self.assertEqual(audio.duration_ms(voice["path"]), 12000)
        self.assertEqual([s["scene_id"] for s in voice["alignment"]["scenes"]], ["change", "later"])
        plan = compile_score(bind_alignment(score, voice["alignment"]), "16:9")
        self.assertEqual(plan["scenes"][1]["start_ms"], 6000)

    def test_missing_alignment_fails_closed(self):
        with self.assertRaisesRegex(audio.AudioError, "REAL_WORD_ALIGNMENT_UNAVAILABLE"):
            self.voice(provider=FixtureTTS(aligned=False))

    def test_real_shape_forced_aligner_test_only(self):
        voice = self.voice(provider=FixtureTTS(aligned=False), aligner=FixtureAligner())
        self.assertEqual(voice["alignment"]["source"]["method"], "forced_alignment")
        self.assertIn("test-fixture", voice["alignment"]["source"]["provider"])

    def test_unaligned_explicit_gap_and_no_word_cue(self):
        result = pipeline.run_pipeline(output=self.root / "film", score=sample_score(), voice_provider=FixtureTTS(aligned=False),
                   allow_unaligned=True, test_fixture=True, renderer=fake_render)
        self.assertFalse(result["voice"]["alignment_complete"])
        self.assertTrue(any("no complete" in g for g in result["gaps"]))

    def test_unaligned_cannot_fake_word_cue(self):
        score = sample_score()
        score["scenes"][0]["events"][0]["cue"] = {"kind": "word", "word": "second", "occurrence": 0, "edge": "start"}
        with self.assertRaisesRegex(audio.AudioError, "REAL_WORD_ALIGNMENT"):
            self.voice(score, FixtureTTS(aligned=False), allow_unaligned=True)

    def test_invalid_alignment_hash_schedule_and_token_coverage(self):
        for index, corrupt in enumerate(({"audio_sha256": "f" * 64}, {"method": "EVEN_SCHEDULE_FROM_GENERATED_AUDIO"},
                         {"words": [{"word": "invented", "start_ms": 0, "end_ms": 100}]})):
            with self.subTest(corrupt=corrupt), self.assertRaises((audio.AudioError, ScoreError)):
                audio.produce_voice(sample_score(), self.root / str(index), FixtureTTS(corrupt=corrupt), test_fixture=True)

    def test_tts_shorter_than_actions_is_not_stretched(self):
        with self.assertRaises(ScoreError):
            pipeline.run_pipeline(output=self.root / "film", score=sample_score(), voice_provider=FixtureTTS(3000),
                                 test_fixture=True, renderer=fake_render)
        manifest = pipeline.json_file(self.root / "film/manifest.json")
        self.assertEqual(manifest["status"], "FAILED")
        self.assertTrue((self.root / "film/voice/voice.wav").is_file())
        self.assertEqual(audio.duration_ms(self.root / "film/voice/voice.wav"), 3000)

    def test_short_and_full_proof_require_real_duration(self):
        for proof in ("short", "full"):
            with self.subTest(proof=proof), self.assertRaisesRegex(pipeline.PipelineError, "PROOF_REQUIRES"):
                pipeline.run_pipeline(output=self.root / proof, score=sample_score(), voice_provider=FixtureTTS(),
                                      proof=proof, renderer=fake_render, test_fixture=True)

    def test_score_inputs_not_mutated_or_restyled(self):
        score = sample_score()
        original = deepcopy(score)
        self.film(score)
        self.assertEqual(score, original)
        for name, options in (("id", {"film_id": "different"}), ("family", {"family": "neon"}), ("brief", {"brief": "changed"})):
            with self.subTest(name=name), self.assertRaises(pipeline.PipelineError):
                pipeline.run_pipeline(output=self.root / name, score=score, voice_provider=FixtureTTS(), test_fixture=True,
                                      renderer=fake_render, **options)

    def test_reused_output_and_inside_git_rejected(self):
        self.film()
        with self.assertRaises(FileExistsError):
            self.film()
        with self.assertRaisesRegex(pipeline.PipelineError, "OUTSIDE_GIT"):
            pipeline.run_pipeline(output=ENGINE / "forbidden-output", score=sample_score(), voice_provider=FixtureTTS())

    def test_aspects_invalid_and_subset_has_gap(self):
        for values in ([], ["16:9", "16:9"], ["4:3"], "9:16, 1:1"):
            with self.subTest(values=values), self.assertRaises(pipeline.PipelineError):
                pipeline._aspects(values)
        result = self.film(aspects=["1:1"])
        self.assertTrue(any("not all three" in g for g in result["gaps"]))

    def test_p8_hash_structure_never_grants_authority(self):
        with self.assertRaisesRegex(pipeline.PipelineError, "P8_CALLER_AUTHENTICATION"):
            pipeline.run_pipeline(output=self.root / "film", score=p8_score(), voice_provider=FixtureTTS())
        self.assertFalse(pipeline.json_file(self.root / "film/manifest.json")["authority"]["caller_authenticated"])

    def test_p8_sound_has_separate_exact_authority_not_score_only(self):
        score = p8_score()
        sound = {"cues": [{"event_id":"linked_change", "semantic_tag":"ui.select", "asset_id":"operator-selected",
                           "gain":.2, "rationale":"Actual selector switch"}]}
        with self.assertRaisesRegex(pipeline.PipelineError, "P8_SOUND_DIRECTION_CALLER_AUTHENTICATION_REQUIRED"):
            pipeline.run_pipeline(output=self.root / "missing-sound-authority", score=score,
                                  voice_provider=FixtureTTS(), authority_verifier=lambda s: s == score,
                                  sound_direction=sound)
        packets = []
        def deny(packet):
            packets.append(deepcopy(packet))
            packet["sound_direction"]["cues"][0]["gain"] = 9
            return False
        with self.assertRaisesRegex(pipeline.PipelineError, "P8_SOUND_DIRECTION_CALLER_AUTHENTICATION_REQUIRED"):
            pipeline.run_pipeline(output=self.root / "denied-sound", score=score,
                                  voice_provider=FixtureTTS(), authority_verifier=lambda s: s == score,
                                  sound_direction=sound, sound_authority_verifier=deny)
        self.assertEqual(packets, [{"score": score, "sound_direction": sound}])
        self.assertEqual(sound["cues"][0]["gain"], .2)

    def test_adapter_authenticates_whole_exact_packet(self):
        score = p8_score()
        request = {"schema": "StudioExplainerDirectionRequestV1", "semanticDirection": score, "evidence": deepcopy(score["evidence"]),
                   "brief": score["brief"], "outputDirectory": str(self.root / "film")}
        seen = []
        with self.assertRaisesRegex(adapter.DirectionAdapterBlocked, "FIXTURE_VOICE"):
            adapter.build_internal_evidence(request, authority_verifier=lambda packet: seen.append(packet) or True, voice_provider=FixtureTTS())
        self.assertEqual(seen, [request])
        with self.assertRaisesRegex(adapter.DirectionAdapterBlocked, "AUTHENTICATION_FAILED"):
            adapter.build_internal_evidence(request, authority_verifier=lambda _: False)
        request["evidence"][0]["claim"] = "tampered"
        with self.assertRaisesRegex(adapter.DirectionAdapterBlocked, "MATCH_EXACTLY"):
            adapter.build_internal_evidence(request, authority_verifier=lambda _: True)
        self.assertFalse(adapter.capabilities()["public_dispatch_enabled"])

    def test_adapter_development_and_unknown_fields_rejected(self):
        score = sample_score()
        packet = {"schema": "StudioExplainerDirectionRequestV1", "semanticDirection": score, "evidence": score["evidence"],
                  "brief": score["brief"], "outputDirectory": str(self.root / "film")}
        with self.assertRaisesRegex(adapter.DirectionAdapterBlocked, "AUTHENTICATED_P8"):
            adapter.build_internal_evidence(packet, authority_verifier=lambda _: True)
        packet["creativeLocked"] = True
        with self.assertRaisesRegex(adapter.DirectionAdapterBlocked, "EXACT_REQUEST"):
            adapter.build_internal_evidence(packet, authority_verifier=lambda _: True)

    def test_renderer_failure_retains_failure_manifest_and_exact_artifacts(self):
        def fail(*a, **k):
            raise pipeline.PipelineError("Explicit test capture failure")
        with self.assertRaisesRegex(pipeline.PipelineError, "capture failure"):
            pipeline.run_pipeline(output=self.root / "film", score=sample_score(), voice_provider=FixtureTTS(),
                                  renderer=fail, test_fixture=True)
        manifest = pipeline.json_file(self.root / "film/manifest.json")
        self.assertEqual(manifest["status"], "FAILED")
        self.assertTrue(manifest["errors"])
        self.assertTrue(manifest["artifacts"])

    def test_kokoro_reports_actual_token_edges_not_uniform_schedule(self):
        tokens = [SimpleNamespace(text="Can't", whitespace="", start_ts=.11, end_ts=.55),
                  SimpleNamespace(text=",", whitespace=" ", start_ts=None, end_ts=None),
                  SimpleNamespace(text="wait", whitespace="", start_ts=.91, end_ts=1.04),
                  SimpleNamespace(text=".", whitespace="", start_ts=None, end_ts=None)]
        words = audio.kokoro_reported_words(tokens)
        self.assertEqual(words, [{"word": "Can't,", "start_ms": 110, "end_ms": 550}, {"word": "wait.", "start_ms": 910, "end_ms": 1040}])
        with self.assertRaisesRegex(audio.AudioError, "TIMING_MISSING"):
            audio.kokoro_reported_words([SimpleNamespace(text="missing", whitespace=" ", start_ts=None, end_ts=None)])

    def test_kokoro_uninstalled_weights_fail_no_download(self):
        with self.assertRaisesRegex(audio.AudioError, "EXPLICIT_LOCAL_CONFIG"):
            audio.KokoroLocalTTS({})
        with self.assertRaisesRegex(audio.AudioError, "LOCAL_MODEL"):
            audio.KokoroLocalTTS({"id": "local", "model_path": str(self.root / "missing"), "config_path": str(self.root / "missing"),
                    "voice_path": str(self.root / "missing"), "source": SOURCE, "language": "a"})

    def test_cli_help_and_no_implicit_local_route(self):
        command = [sys.executable, str(ENGINE / "tools/make_film.py")]
        help_result = subprocess.run(command + ["--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        for flag in ("--brief", "--evidence", "--family", "--context", "--aspects", "--out", "--film-id", "--score"):
            self.assertIn(flag, help_result.stdout)
        source = self.root / "score.json"
        audio.write_json(source, sample_score())
        result = subprocess.run(command + ["--score", str(source), "--out", str(self.root / "film")], capture_output=True, text=True,
                      env={**os.environ, "NEXSTUDIO_TTS_ROUTES_JSON": "[]"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("NO_DECLARED_LOCAL_ROUTE", result.stderr)
        self.assertFalse((self.root / "film").exists())

    def test_strict_route_registry_no_espeak_remote_fixture_or_rights_fallback(self):
        for route in ({"id":"bad","command":["espeak"],"local":True,"commercialUseAllowed":True},
                      {"id":"bad","command":[sys.executable],"commercialUseAllowed":True},
                      {"id":"bad","command":[sys.executable],"local":True,"commercialUseAllowed":False},
                      {"id":"bad","command":[sys.executable],"local":True,"commercialUseAllowed":True,"test_fixture":True}):
            with self.subTest(route=route), patch.dict(os.environ, {"NEXSTUDIO_TTS_ROUTES_JSON": json.dumps([route])}), self.assertRaises(audio.AudioError):
                audio.DeclaredLocalTTS("bad", SOURCE)

    def test_declared_command_protocol_and_real_shape_timing_is_test_only(self):
        script = self.root / "fixture-command.py"
        script.write_text('''import sys,json,math,wave,hashlib
r=json.load(sys.stdin);p=r['payload'];out=r['outputPath']
assert r['schema']=='NexStudioAudioProviderRequestV1' and r['requirements']['noSyntheticAlignment']
with wave.open(out,'wb') as w:
 w.setparams((1,2,24000,0,'NONE','not compressed'))
 w.writeframes(b''.join(int(4000*math.sin(n*2*math.pi*220/24000)).to_bytes(2,'little',signed=True) for n in range(144000)))
t=80;words=[]
for i,x in enumerate(p['text'].split()):
 e=t+100+i*23;words.append(dict(word=x,start_ms=t,end_ms=e));t=e+71
print(json.dumps(dict(audioPath=out,rightsEvidence=dict(commercialUseAllowed=True),providerEvidence=dict(provider='declared-test'),alignment=dict(provider='declared-test',method='provider_word_timestamps',audio_sha256=hashlib.sha256(open(out,'rb').read()).hexdigest(),words=words))))
''')
        route = {"id":"explicit-test-command", "local":True, "commercialUseAllowed":True, "provider":"declared-test",
                 "source":SOURCE, "command":[sys.executable,str(script)]}
        class TestCommand(audio.DeclaredLocalTTS):
            is_test_fixture = True
        with patch.dict(os.environ, {"NEXSTUDIO_TTS_ROUTES_JSON":json.dumps([route])}):
            voice = self.voice(provider=TestCommand("explicit-test-command"))
        self.assertTrue(voice["ledger"]["test_fixture"])
        self.assertTrue(voice["ledger"]["alignment_complete"])

    def test_sound_library_selection_is_semantic_licensed_and_hash_bound(self):
        root = audio.SOUND_ROOT
        registry = pipeline.json_file(root / "manifests/NEXSTUDIO_SOUND_V2_REGISTRY.json")
        asset = next(a for a in registry["assets"] if a["semanticTag"] == "ui.select" and a["license"] == "CC0-1.0" and a["selectable"])
        plan = compile_score(sample_score(), "1:1")
        direction = {"cues":[{"event_id":"linked_change", "semantic_tag":asset["semanticTag"], "asset_id":asset["assetId"],
                             "gain":.2, "rationale":"Punctuate actual selector change, not every animation"}]}
        declared = audio.bind_sound_direction(plan, direction, self.root / "sound")
        tracks = pipeline.json_file(declared)["tracks"]
        self.assertEqual(tracks[0]["start_ms"], 3000)  # selector step switches at event end
        self.assertEqual(tracks[0]["source"]["license"], "CC0-1.0")
        self.assertEqual(audio.sha256(tracks[0]["path"]), asset["productionSha256"])
        self.assertTrue(pipeline.json_file(self.root / "sound/sound-ledger.json")["bindings"][0]["license_sha256"])
        direction["cues"][0]["event_id"] = "read_change"
        with self.assertRaisesRegex(audio.AudioError, "SEMANTIC_EVENT_MISMATCH"):
            audio.bind_sound_direction(plan, direction, self.root / "bad-sound")

    def test_silence_default_music_explicit_rights_and_no_truncation(self):
        plan = compile_score(sample_score(), "16:9")
        self.assertEqual(pipeline.json_file(audio.bind_sound_direction(plan, {}, self.root / "silence")), {"tracks":[]})
        clip = self.root / "owned-test.wav"
        sine(clip, 1000)
        music = {"music":[{"path":str(clip),"source":SOURCE,"sha256":audio.sha256(clip),"start_ms":5000,"gain":.1,
                           "rationale":"Explicit owned test tone, not commercial music proof"}]}
        declaration = audio.bind_sound_direction(plan, music, self.root / "music")
        self.assertEqual(pipeline.json_file(declaration)["tracks"][0]["role"], "music")
        music["music"][0]["start_ms"] = 5500
        with self.assertRaisesRegex(audio.AudioError, "MUST_FIT_FILM"):
            audio.bind_sound_direction(plan, music, self.root / "long")
        music["music"][0]["sha256"] = "f" * 64
        with self.assertRaisesRegex(audio.AudioError, "HASH_MISMATCH"):
            audio.bind_sound_direction(plan, music, self.root / "hash")

    def test_live_staged_pipeline_prepares_voice_before_motion_and_reuses_original_bytes(self):
        class Author(FixtureAuthor):
            def __init__(self):
                self.motion = []

            def complete(self, task, request):
                if task == "author_choreography":
                    self.motion.append(deepcopy(request))
                result = super().complete(task, request)
                if task == "author_choreography":
                    result["events"][-1]["cue"] = {"kind": "absolute", "ms": 2100, "basis": "authored"}
                    result["events"][-1]["duration_ms"] = 500
                return result

        class Voice(FixtureTTS):
            def __init__(self):
                super().__init__(milliseconds=3200)
                self.calls = 0

            def synthesize(self, *args, **kwargs):
                self.calls += 1
                return super().synthesize(*args, **kwargs)

        provider, voice = Author(), Voice()
        out = self.root / "staged-film"
        result = pipeline.run_pipeline(output=out, brief="Explain the declared water measurements.",
                                      evidence=sample_score("water")["evidence"], provider=provider,
                                      voice_provider=voice, staged=True, concept_first=True,
                                      test_fixture=True, renderer=fake_render)
        self.assertEqual(result["status"], "TEST_FIXTURE_RENDER_READY")
        self.assertEqual(voice.calls, 1)
        self.assertEqual(provider.motion[0]["scene_structure"]["duration_ms"], 3200)
        self.assertEqual(provider.motion[0]["voice_timing"]["words"], reported(provider.motion[0]["scene_structure"]["narration"]))
        self.assertEqual(audio.sha256(out / "prepared-voice-001/000-raw.wav"),
                         audio.sha256(out / "voice/000-raw.wav"))
        self.assertEqual(pipeline.json_file(out / "score.json")["scenes"][0]["duration_ms"], 3200)

    def test_staged_voice_cache_preserves_bytes_and_rejects_changed_text_or_raw_audio(self):
        cached = audio.CachedLocalVoice(FixtureTTS())
        raw = self.root / "prepared.wav"
        first = cached.synthesize("An explicit test narration.", raw, scene_id="scene", film_id="test")
        raw_hash = audio.sha256(raw)
        first["route"] = "mutated caller metadata"
        copy = self.root / "final.wav"
        final = cached.synthesize("An explicit test narration.", copy, scene_id="scene", film_id="test")
        self.assertEqual(audio.sha256(copy), raw_hash)
        self.assertEqual(final["audio_path"], str(copy))
        self.assertNotEqual(final["route"], first["route"])
        self.assertTrue(cached.is_test_fixture)
        with self.assertRaisesRegex(audio.AudioError, "STAGED_VOICE_IDENTITY_OR_AUDIO_CHANGED"):
            cached.synthesize("Different narration.", self.root / "changed.wav", scene_id="scene", film_id="test")
        with self.assertRaisesRegex(audio.AudioError, "STAGED_VOICE_IDENTITY_OR_AUDIO_CHANGED"):
            cached.synthesize("An explicit test narration.", raw, scene_id="scene", film_id="test")
        raw.write_bytes(b"Changed original raw audio")
        with self.assertRaisesRegex(audio.AudioError, "STAGED_VOICE_IDENTITY_OR_AUDIO_CHANGED"):
            cached.synthesize("An explicit test narration.", self.root / "corrupt.wav", scene_id="scene", film_id="test")

    def test_actual_all_aspect_mp4_frames_audio_fixture_evidence(self):
        # Durable artifacts outside git; synthetic audio is loudly labeled.
        root = Path(tempfile.mkdtemp(prefix="pipeline-render-fixture-", dir=PROOF_ROOT))
        registry = pipeline.json_file(audio.SOUND_ROOT / "manifests/NEXSTUDIO_SOUND_V2_REGISTRY.json")
        asset = next(a for a in registry["assets"] if a["semanticTag"] == "ui.select" and a["license"] == "CC0-1.0" and a["selectable"])
        sound = {"cues": [{"event_id": "linked_change", "semantic_tag": "ui.select", "asset_id": asset["assetId"],
                           "gain": .2, "rationale": "Explicit test-only punctuation of selector state at its actual switch"}]}
        result = pipeline.run_pipeline(output=root / "film", score=sample_score("energy"), voice_provider=FixtureTTS(),
                                      test_fixture=True, fps=1, sound_direction=sound)
        self.assertEqual(result["status"], "TEST_FIXTURE_RENDER_READY")
        self.assertEqual(len(result["renders"]), 3)
        for rendered in result["renders"]:
            self.assertEqual(rendered["frames"], 6)
            self.assertEqual(rendered["movie_sha256"], audio.sha256(rendered["movie"]))
            self.assertTrue(any(s["codec_type"] == "audio" for s in rendered["probe"]["streams"]))
            rm = pipeline.json_file(rendered["render_manifest"])
            self.assertNotEqual(rm["frames"][0]["sha256"], rm["frames"][-1]["sha256"])
            self.assertEqual([a["start_ms"] for a in rm["audio"] if a["role"] == "sound"], [3000])
            # Independently reject plausible but incomplete renderer evidence.
            plan_path = root / "film" / ("plan-" + rendered["aspect"].replace(":", "x") + ".json")
            bad = deepcopy(rm)
            bad["frames"] = bad["frames"][:-1]
            bad["frame_count"] -= 1
            with self.assertRaisesRegex(pipeline.PipelineError, "RENDER_FRAMES_INCOMPLETE"):
                pipeline._verify_render(pipeline.json_file(plan_path), plan_path, Path(rendered["movie"]).parent,
                                        bad, result["voice"]["audio_sha256"])
        print("PIPELINE_FIXTURE_MEDIA=" + str(root / "film/manifest.json"))


if __name__ == "__main__":
    unittest.main()
