#!/usr/bin/env python3
"""Bayes base-rate stress video in the unmodified SceneBam Sketch / Data Viz engines.

This is intentionally a hard, realistic subject rather than a fixture that
exercises only a known short sentence. Rendered frames and soundtrack come
from the production editorial compiler and frame-addressable browser runtime.
A Microsoft Andrew cloud synthesis failure aborts: there is NO fallback voice.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from make_reel import build_treatment, style_of
from voice_registry import VOICES

SCRIPT = (
    "Imagine 10,000 people tested for a rare condition. "
    "Only 100 actually have it. The test identifies 99 genuine cases. "
    "Yet 495 healthy people also test positive. "
    "That makes 594 positive results altogether. "
    "But only 99 of those are genuine. "
    "So, when the test is positive, the chance of truly having the condition "
    "is just 16.7 percent. That's the base-rate paradox. "
    "Even a highly sensitive test can produce mostly false alarms "
    "when the condition is rare."
)
ASPECTS = ("9x16", "1x1")
VOICE_ID = "andrew"
VOICE = VOICES[VOICE_ID]["edge"]


def execute(argv, *, cwd=None):
    print("+", " ".join(map(str, argv)), flush=True)
    subprocess.run(list(map(str, argv)), cwd=cwd, check=True)


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


async def microsoft_andrew(mp3_path):
    import edge_tts
    chunks = bytearray()
    boundaries = []
    stream = edge_tts.Communicate(text=SCRIPT, voice=VOICE, rate="-18%")
    async for event in stream.stream():
        if event["type"] == "audio":
            chunks.extend(event["data"])
        elif event["type"] == "WordBoundary":
            boundaries.append({
                "text": event["text"],
                "start_ms": round(event["offset"] / 10000),
                "end_ms": round((event["offset"] + event["duration"]) / 10000),
            })
    print(f"MICROSOFT_ANDREW_RESPONSE: audio_bytes={len(chunks)} word_boundaries={len(boundaries)}", flush=True)
    if len(chunks) < 8000:
        raise RuntimeError("MICROSOFT_ANDREW_REQUIRED: missing real Andrew audio; NO fallback")
    mp3_path.write_bytes(chunks)
    return boundaries


def align_script_tokens(boundaries, duration_ms):
    """Tie the exact source tokens to Edge's measured word-boundary clock.

    The service may expand a written number into several spoken tokens. In
    that case interpolate only across REAL boundary positions and record the
    interpolation in provenance. Never fabricate a different narration.
    """
    tokens = SCRIPT.split()
    n = len(boundaries)
    if n < 10:
        # Some supported Edge TTS transports provide the full real speech
        # stream without word-boundary events. Keep Andrew audio intact and
        # label approximate word scheduling instead of claiming measured sync.
        weights = [max(2, len(token.strip(".,:!?"))) for token in tokens]
        total = sum(weights)
        usable = max(1200, duration_ms - 300)
        cursor = 100.0
        scheduled = []
        for token, weight in zip(tokens, weights):
            span = usable * weight / total
            scheduled.append({
                "text": token, "start_ms": round(cursor),
                "end_ms": min(duration_ms, round(cursor + span * 0.92)),
            })
            cursor += span
        return scheduled, "APPROXIMATE_FROM_VERIFIED_MICROSOFT_ANDREW_AUDIO"
    if abs(n - len(tokens)) > max(12, len(tokens) // 4):
        raise RuntimeError(
            f"EDGE_ALIGNMENT_DIVERGED: {n} service boundaries versus {len(tokens)} script tokens"
        )
    def clock(index):
        index = max(0.0, min(float(n), index))
        lower = min(n - 1, int(index))
        if index >= n:
            return boundaries[-1]["end_ms"]
        part = index - lower
        a = boundaries[lower]["start_ms"]
        b = boundaries[min(n - 1, lower + 1)]["start_ms"]
        return a + (b - a) * part

    words = []
    for i, token in enumerate(tokens):
        if n == len(tokens):
            start = boundaries[i]["start_ms"]
            end = boundaries[i]["end_ms"]
        else:
            start = clock(i * n / len(tokens))
            end = clock((i + 1) * n / len(tokens))
        words.append({
            "text": token,
            "start_ms": max(0, round(start)),
            "end_ms": max(round(start) + 45, min(duration_ms, round(end))),
        })
    source = ("EDGE_MEASURED_WORD_BOUNDARIES" if n == len(tokens)
              else "EDGE_MEASURED_BOUNDARIES_INTERPOLATED_FOR_NUMERIC_TOKENS")
    return words, source


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", required=True, choices=("sketch", "dataviz"))
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    assert VOICE == "en-US-AndrewMultilingualNeural", "SceneBam approved Andrew voice changed"

    film_id = "scenebam-bayes-" + args.style
    fixture = ROOT / "fixtures" / film_id
    fixture.mkdir(parents=True, exist_ok=True)
    out = ROOT / "out" / "bayes-stress" / film_id
    out.mkdir(parents=True, exist_ok=True)
    voice_path = fixture / "voice.mp3"

    # Do not use make_reel's synthetic or espeak fallback; no substitution allowed.
    try:
        boundaries = asyncio.run(microsoft_andrew(voice_path))
    except Exception as exc:
        raise RuntimeError("MICROSOFT_ANDREW_SYNTHESIS_FAILED_NO_SUBSTITUTE") from exc
    info = probe(voice_path)
    duration = round(float(info["format"]["duration"]) * 1000)
    assert duration > 14000 and info["format"].get("size", "0") != "0"
    words, timing_source = align_script_tokens(boundaries, duration)
    (fixture / "alignment.json").write_text(json.dumps({
        "words": words,
        "provenance": timing_source,
        "synthesis": "MICROSOFT_EDGE_NEURAL",
        "voice_id": VOICE_ID,
        "voice_name": VOICE,
    }, indent=2))

    treatment = build_treatment(
        SimpleNamespace(aspects=",".join(ASPECTS)),
        style_of(args.style), words, [], film_id)
    treatment["fps"] = args.fps
    treatment["note"] += (
        "; difficult base-rate stress test; unmodified native engine; "
        f"single intact Andrew master audio, voice={VOICE}; timing={timing_source}"
    )
    (fixture / "treatment.json").write_text(json.dumps(treatment, indent=2))
    # In a stress test, a failed creative gate is meaningful evidence, not
    # permission to replace the script or silently relax the native gate.
    # The compiler still writes real aspect plans on exit code 3.
    compiler = subprocess.run(
        [sys.executable, "-m", "editorial_plan_compiler",
         str(fixture / "treatment.json"), str(out)],
        cwd=ROOT / "compiler", check=False)
    if compiler.returncode not in (0, 3):
        raise RuntimeError(f"NATIVE_COMPILER_ERROR_EXIT_{compiler.returncode}")
    gate_report = json.loads((out / "gate_report.json").read_text())
    print("STRESS_COMPILER_GATE:", json.dumps(gate_report)[:5000], flush=True)

    proofs = {}
    for aspect in ASPECTS:
        plan = out / f"plan_{aspect}.json"
        compiled = json.loads(plan.read_text())
        assert compiled["director_style"] == args.style
        # A FAIL result is retained in the report while the actual movie
        # renders, so the user can judge the original difficult request.
        spoken = " ".join(b.get("narration", "") for b in compiled["beats"])
        for number in ("10,000", "100", "99", "495", "594", "16.7"):
            assert number in spoken, (aspect, "missing source number", number)
        if args.style == "dataviz":
            assert compiled["captions_policy"] == "kinetic"
            assert compiled["captions"] == []
        execute(["node", ROOT / "tools" / "render_reel.js", plan, out,
                 "--fps", args.fps, "--workers", args.workers,
                 "--preset", "ultrafast", "--web-crf", "29"])
        mp4 = out / f"{film_id}_{aspect}_web.mp4"
        assert mp4.stat().st_size > 60000
        video_info = probe(mp4)
        video_stream = next(s for s in video_info["streams"] if s["codec_type"] == "video")
        audio_stream = next(s for s in video_info["streams"] if s["codec_type"] == "audio")
        width, height = video_stream["width"], video_stream["height"]
        assert width < height if aspect == "9x16" else width == height, (aspect,width,height)
        assert audio_stream["codec_name"] == "aac", audio_stream
        render = json.loads((out / f"render_{aspect}.json").read_text())
        assert not render.get("page_errors"), render.get("page_errors")
        assert render.get("captions_burned", 0) == 0 if args.style == "dataviz" else True
        for point in (0.24, 0.52, 0.78):
            shot = out / f"proof_{aspect}_{round(point*100)}.png"
            execute(["ffmpeg", "-y", "-v", "error",
                     "-ss", f"{duration * point / 1000:.2f}", "-i", mp4,
                     "-frames:v", "1", shot])
            assert shot.stat().st_size > 2000
        proofs[aspect] = {
            "video": mp4.name, "width": width, "height": height,
            "file_bytes": mp4.stat().st_size,
            "video_sha256": hashlib.sha256(mp4.read_bytes()).hexdigest(),
            "plan_gate": compiled["gate"]["status"],
            "render_page_errors": render.get("page_errors", []),
            "source_narration_complete": True,
            "frame_previews": 3,
        }

    report = {
        "topic": "Bayes base-rate paradox: 99 true positives vs 495 false positives",
        "style": args.style, "script": SCRIPT, "assumptions": {
            "population": 10000, "prevalence": 0.01, "sensitivity": 0.99,
            "specificity": 0.95, "true_positives": 99,
            "false_positives": 495, "positive_tests": 594,
            "positive_predictive_value": round(99 / 594, 6)
        },
        "voice": {
            "registry_key": VOICE_ID, "microsoft_voice": VOICE,
            "audio_sha256": hashlib.sha256(voice_path.read_bytes()).hexdigest(),
            "duration_ms": duration, "audio_shared_across_aspects": True,
            "alignment_provenance": timing_source,
            "provider_word_boundaries": len(boundaries),
            "voice_substitution_allowed": False,
        },
        "gate_status": gate_report.get("status"), "gate_failures": gate_report.get("failures", []),
        "note": "Native compiler failure is reported, never ignored or called a pass.",
        "videos": proofs,
    }
    (out / "stress_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
