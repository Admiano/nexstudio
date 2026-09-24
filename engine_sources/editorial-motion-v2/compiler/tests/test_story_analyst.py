"""Story analyst (tools/story_analyst.py): recorded analyst payloads must conform
to NexStudioEditorialTreatmentV2 and pass the compiler gate, and hostile/malformed
payloads must be repaired rather than crash. No provider is touched — payloads are
replayed from tests/fixtures/story_analyst/."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "compiler"))

import make_reel  # noqa: E402
import story_analyst  # noqa: E402
from editorial_plan_compiler.compiler import compile_film  # noqa: E402
from editorial_plan_compiler.contracts import FilmTreatment  # noqa: E402

FX = Path(__file__).parent / "fixtures" / "story_analyst"
ASPECTS = ["16x9", "1x1", "9x16"]


def fake_words(script: str):
    """Deterministic synthetic alignment: ~330ms per word, 700ms beat gap after a
    sentence end — enough structure for chunk_beats to group on clauses."""
    words, t = [], 0
    for w in script.split():
        end = t + 300
        words.append({"text": w, "start_ms": t, "end_ms": end})
        t = end + (700 if w.endswith((".", "!", "?")) else 30)
    return words


def make_fixture_dir(tmp_path: Path, words, media_png: bool = False) -> Path:
    d = tmp_path / "fixture"
    d.mkdir(parents=True, exist_ok=True)
    (d / "alignment.json").write_text(json.dumps({"words": words}))
    total_s = (words[-1]["end_ms"] + 1200) / 1000
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=mono", "-t", f"{total_s}", "-b:a", "128k",
                    str(d / "voice.mp3")], check=True)
    if media_png:
        (d / "media").mkdir(exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                        "color=c=sienna:s=320x240", "-frames:v", "1",
                        str(d / "media" / "product.png")], check=True)
    return d


def conform_fixture(name: str, media=None):
    fx = json.loads((FX / f"{name}.json").read_text())
    words = fake_words(fx["script"])
    groups = make_reel.chunk_beats(words)
    style = make_reel.style_of("tiles")
    registry = story_analyst._registry_ids()
    treatment, storyboard = story_analyst.conform(
        fx["payload"], groups, style, f"analyst-{name}", ASPECTS,
        media or [], registry)
    return fx, words, groups, treatment, storyboard


def gate_for(treatment, fixture_dir, tmp_path):
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return compile_film(treatment, work, fixture_dir)


EMBER_MEDIA = [{"asset_id": "media1", "kind": "IMAGE", "path": "media/product.png",
                "width": 320, "height": 240}]


@pytest.mark.parametrize("name", ["purpose", "ember", "zkproof"])
def test_diverse_scripts_conform_and_gate_pass(name, tmp_path):
    media = EMBER_MEDIA if name == "ember" else None
    fx, words, groups, treatment, storyboard = conform_fixture(name, media=media)
    # the conformed treatment must be contract-valid on its own
    FilmTreatment.parse(treatment)
    fdir = make_fixture_dir(tmp_path, words, media_png=bool(media))
    (fdir / "treatment.json").write_text(json.dumps(treatment))
    result = gate_for(treatment, fdir, tmp_path)
    assert result["gate"]["status"] == "PASS", result["gate"]["failures"]
    # arc shape: multi-beat, opens HOOK, lands PAYOFF/CTA, motif authored
    beats = treatment["beats"]
    assert len(beats) >= 4
    assert beats[0]["beat_type"] == "HOOK"
    assert beats[-1]["beat_type"] in ("PAYOFF", "CTA")
    assert storyboard["schema"] == "NexStudioStoryboardV1"
    assert storyboard["arc"]["motif"]
    assert storyboard["scenes"]
    # narration coverage: every aligned word is spoken inside exactly one beat
    spoken = " ".join(b["narration"] for b in beats)
    assert set(story_analyst._norm_seq(spoken)) >= set(
        story_analyst._norm_seq(" ".join(w["text"] for w in words)))
    # analyst-authored beats are illustration-led, not keyword-icon layouts
    visual_share = sum(1 for b in beats if b.get("illustration")) / len(beats)
    assert visual_share >= 0.8
    assert len({b["pattern"] for b in beats}) >= 3  # not one pattern repeated


def test_malformed_payload_is_repaired(tmp_path):
    fx, words, groups, treatment, storyboard = conform_fixture("messy")
    FilmTreatment.parse(treatment)
    fdir = make_fixture_dir(tmp_path, words)
    (fdir / "treatment.json").write_text(json.dumps(treatment))
    result = gate_for(treatment, fdir, tmp_path)
    assert result["gate"]["status"] == "PASS", result["gate"]["failures"]
    beats = treatment["beats"]
    # group coverage stays exact despite gaps/dropped beats
    covered = set(story_analyst._norm_seq(" ".join(b["narration"] for b in beats)))
    scripted = set(t for w in fx["script"].split() for t in story_analyst._norm_seq(w))
    assert scripted <= covered
    assert len(beats) == len(groups)


def test_conform_group_partition(tmp_path):
    """A payload that skips a group leaves no narration unsaid."""
    fx, words, groups, treatment, _ = conform_fixture("purpose")
    assert len(treatment["beats"]) == len(groups)
    narrations = [b["narration"] for b in treatment["beats"]]
    joined = story_analyst._norm_seq(" ".join(narrations))
    scripted = story_analyst._norm_seq(" ".join(w["text"] for w in words))
    assert joined == scripted


def test_replay_mode_roundtrips(monkeypatch, tmp_path):
    replay = FX / "purpose.json"
    monkeypatch.setenv("STORY_ANALYST_REPLAY", str(replay))
    fx = json.loads(replay.read_text())
    words = fake_words(fx["script"])
    groups = make_reel.chunk_beats(words)
    style = make_reel.style_of("tiles")
    treatment, storyboard = story_analyst.build_llm_treatment(
        fx["script"], words, groups, style, [], "analyst-replay", ASPECTS)
    FilmTreatment.parse(treatment)
    assert storyboard["arc"]["beat_arc"]


def test_no_provider_raises_unavailable(monkeypatch):
    for k in ("STORY_ANALYST_REPLAY", "NEXMIND_STORY_ANALYST_MODEL", "OPENAI_MODEL",
              "NEXMIND_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(story_analyst.AnalystUnavailable):
        story_analyst.call_analyst({})
    assert not story_analyst.analyst_available()


def test_analyst_mode_parsing():
    class A:
        pass
    a = A(); a.analyst = "llm"
    assert story_analyst.analyst_mode(a) == "llm"
    a.analyst = None
    assert story_analyst.analyst_mode(a) == "auto"
    a.analyst = "weird"
    assert story_analyst.analyst_mode(a) == "auto"


def test_empty_payload_is_invalid():
    with pytest.raises(story_analyst.AnalystInvalid):
        story_analyst.conform({}, [], {}, "x", ASPECTS, [], set())
    with pytest.raises(story_analyst.AnalystInvalid):
        story_analyst.conform({"beats": "nope"}, [], {}, "x", ASPECTS, [], set())


def test_performer_cast_conforms_and_gates(tmp_path):
    """Phase 03 performer: cast identity + track/prop/states must survive conform,
    validate against the contract, and pass the compile gate."""
    fx, words, groups, treatment, storyboard = conform_fixture("performer")
    FilmTreatment.parse(treatment)
    assert treatment["cast"]["scout"]["head"] == "bun-2"
    assert storyboard["cast"]["scout"]["posture"] == "standing"
    beats = treatment["beats"]
    figures = [b["figure"] for b in beats if b.get("figure")]
    assert all(f.get("character") == "scout" for f in figures)
    assert beats[0]["figure"]["track"] == {"enter": "left", "exit": "none"}
    assert beats[1]["figure"]["prop"]["concept"] == "magnifying glass"
    assert beats[2]["figure"]["states"][0]["face"] == "concerned"
    assert beats[4]["figure"]["face"] == "smile"
    fdir = make_fixture_dir(tmp_path, words)
    result = gate_for(treatment, fdir, tmp_path)
    assert result["gate"]["status"] == "PASS", result["gate"]["failures"]
    plans = result["plans"]["16x9"]["beats"]
    b2 = next(b for b in plans if b["beat_id"] == "b02")
    fig = b2["figure"]
    assert fig["character"] == "scout"
    prop = fig["prop"]
    assert prop["hand"] == "right"
    assert prop["asset"] or prop["photo"] or prop["word"]  # resolved somewhere on the ladder
    b3 = next(b for b in plans if b["beat_id"] == "b03")
    states = b3["figure"]["states"]
    assert 1 <= len(states) <= 3
    assert all(s["at_ms"] > 0 and s["swaps"] for s in states)
    # identity persistence: the cast seed makes the head identical across beats
    heads = {p["part_id"] for p in fig["parts"] if p["slot"] == "head"}
    assert heads == {"bun-2"}
    b5 = next(b for b in plans if b["beat_id"] == "b05")
    assert {p["part_id"] for p in b5["figure"]["parts"] if p["slot"] == "head"} == heads
    assert b5["figure"]["track"]["enter"] == "right"


def test_world_bible_conforms_and_gates(tmp_path):
    """Phase 04 world bible: authored palette + grain + motif mark must survive conform,
    validate against the contract, and land identically in every aspect's plan."""
    fx, words, groups, treatment, storyboard = conform_fixture("world")
    FilmTreatment.parse(treatment)
    # authored brand wins over the style preset
    assert treatment["brand"]["ink"] == "#16212e"
    assert treatment["brand"]["paper"] == "#efe7d3"
    assert treatment["brand"]["accent"] == "#d98a2b"
    assert treatment["brand"]["finish"] == "PAPER"
    assert treatment["world"]["grain"] == "hatch-45"
    assert treatment["world"]["motif"]["concept"] == "paper boat"
    assert storyboard["world"]["motif"]["concept"] == "paper boat"
    fdir = make_fixture_dir(tmp_path, words)
    result = gate_for(treatment, fdir, tmp_path)
    assert result["gate"]["status"] == "PASS", result["gate"]["failures"]
    for aspect, plan in result["plans"].items():
        m = plan.get("motif")
        assert m and m["corner"] == "top-right" and m["concept"] == "paper boat"
        assert m["asset"] or m["photo"] or m["word"]
        assert "hatch-45" in (plan["surfaces"]["grain"]["path"] if plan["surfaces"]["grain"] else "")
        assert plan["brand"]["ink"] == "#16212e"


def test_world_bible_defaults_clean(tmp_path):
    """Absent a world block nothing changes — surfaces keep the default grain."""
    fx, words, groups, treatment, _ = conform_fixture("purpose")
    assert "world" not in treatment
    fdir = make_fixture_dir(tmp_path, words)
    result = gate_for(treatment, fdir, tmp_path)
    assert result["gate"]["status"] == "PASS"
    assert result["plans"]["16x9"].get("motif") is None
    assert "grain-fine" in result["plans"]["16x9"]["surfaces"]["grain"]["path"]


def test_performer_unknown_character_dropped(tmp_path):
    """A figure referencing a cast member that was not declared must lose the
    reference, not fail: contract parse raises PERFORMER_CHARACTER_UNKNOWN otherwise."""
    fx, words, groups, treatment, _ = conform_fixture("performer")
    treatment["cast"].pop("scout")
    with pytest.raises(Exception):
        FilmTreatment.parse(treatment)
    # conform-time repair: unknown character simply isn't carried
    fx2, words2, groups2, treatment2, _ = conform_fixture("performer")
    payload = dict(fx2["payload"])
    payload["cast"] = {}
    t2, _sb = story_analyst.conform(payload, groups2, make_reel.style_of("tiles"),
                                  "analyst-perf2", ASPECTS, [], story_analyst._registry_ids())
    assert all(not b.get("figure") or "character" not in b["figure"] for b in t2["beats"])
