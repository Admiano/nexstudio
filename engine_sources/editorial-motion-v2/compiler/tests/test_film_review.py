"""Film-level certification (tools/film_review.py): the whole-film review that runs
after compile — arc shape, scene continuity, cast identity, motif stamp, aspect
parity, render evidence. Plans alone certify without render artifacts (render/frame
checks report SKIP, never FAIL).
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "compiler"))
sys.path.insert(0, str(Path(__file__).parent))

import film_review  # noqa: E402
import story_analyst  # noqa: E402
import make_reel  # noqa: E402
from editorial_plan_compiler.compiler import compile_film  # noqa: E402
from test_story_analyst import conform_fixture, fake_words, make_fixture_dir  # noqa: E402

ASPECTS = ["16x9", "1x1", "9x16"]


def compile_to_reel(treatment, fixture_dir, tmp_path):
    """compile_film into a reel-shaped dir: plan_<aspect>.json + gate_report.json."""
    out = tmp_path / "reel"
    out.mkdir(exist_ok=True)
    result = compile_film(treatment, out, fixture_dir)
    for aspect, plan in result["plans"].items():
        (out / f"plan_{aspect}.json").write_text(json.dumps(plan))
    (out / "gate_report.json").write_text(json.dumps(result["gate"]))
    return out


def check(cert, cid, scope=None):
    rows = [c for c in cert["checks"] if c["id"] == cid and (scope is None or c["scope"] == scope)]
    assert rows, f"check {cid} ({scope}) absent"
    return rows


def test_diorama_reel_certifies(tmp_path):
    """The Phase-05 diorama film carries every film-level property to certification."""
    fx, words, groups, treatment, storyboard = conform_fixture("diorama")
    fdir = make_fixture_dir(tmp_path, words)
    reel = compile_to_reel(treatment, fdir, tmp_path)
    cert = film_review.certify(reel, [], reel / "gate_report.json")
    assert cert["schema"] == "NexStudioFilmCertificationV1"
    assert cert["verdict"] == "PASS", [c for c in cert["checks"] if c["status"] == "FAIL"]
    # the checks that make it a film review and not a beat gate
    assert check(cert, "compile_gate")[0]["status"] == "PASS"
    assert check(cert, "arc_shape")[0]["status"] == "PASS"
    assert check(cert, "narration_coverage")[0]["status"] == "PASS"
    sc = check(cert, "scene_continuity")[0]
    assert sc["status"] == "PASS" and "2 authored place" in sc["detail"]
    for aspect in ASPECTS:
        assert check(cert, "cast_continuity", aspect)[0]["status"] == "PASS"
        assert check(cert, "motif_stamp", aspect)[0]["status"] == "PASS"
    assert check(cert, "aspect_parity")[0]["status"] == "PASS"
    # no renders were produced — evidence checks must SKIP, not fail
    assert check(cert, "render_manifest", "1x1")[0]["status"] == "SKIP"


def test_certification_catches_cast_drift(tmp_path):
    """A performer whose identity part changes mid-film must fail cast_continuity."""
    fx, words, groups, treatment, _ = conform_fixture("diorama")
    fdir = make_fixture_dir(tmp_path, words)
    reel = compile_to_reel(treatment, fdir, tmp_path)
    plan_path = reel / "plan_16x9.json"
    plan = json.loads(plan_path.read_text())
    fig_beat = next(b for b in plan["beats"] if b.get("figure"))
    head = next(p for p in fig_beat["figure"]["parts"] if p["slot"] == "head")
    head["part_id"] = "different-head"  # tamper: identity drifted
    plan_path.write_text(json.dumps(plan))
    cert = film_review.certify(reel, [], reel / "gate_report.json")
    assert cert["verdict"] == "FAIL"
    assert check(cert, "cast_continuity", "16x9")[0]["status"] == "FAIL"
    assert check(cert, "aspect_parity")[0]["status"] == "FAIL"  # 1x1/9x16 disagree with the tampered plan


def test_certification_catches_arc_break(tmp_path):
    """A film that never lands a payoff is not a film."""
    fx, words, groups, treatment, _ = conform_fixture("diorama")
    fdir = make_fixture_dir(tmp_path, words)
    reel = compile_to_reel(treatment, fdir, tmp_path)
    for p in reel.glob("plan_*.json"):
        plan = json.loads(p.read_text())
        plan["beats"][-1]["beat_type"] = "SETUP"  # the payoff never lands
        p.write_text(json.dumps(plan))
    cert = film_review.certify(reel, [], reel / "gate_report.json")
    assert cert["verdict"] == "FAIL"
    assert check(cert, "arc_shape")[0]["status"] == "FAIL"
