#!/usr/bin/env python3
"""Produce short SceneBam Data Viz + Sketch video-proofs with the actual engine.

Continuous synthetic speech is a deterministic CI test fixture; it is not a
production-quality voice. Approximate word alignment is intentionally labelled.
The renderer and illustration compiler are unmodified production components.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from make_reel import build_treatment, style_of

SCRIPTS = {
    "dataviz": "In January, park visits were 10. In February, they reached 20. In March, they reached 15.",
    "sketch": "A phone sends a message to a server. The server connects to a database.",
}

def run(command, *, cwd=None):
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, check=True)


def duration_ms(audio: Path) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
        check=True, capture_output=True, text=True)
    return int(float(result.stdout.strip()) * 1000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=sorted(SCRIPTS), required=True)
    ap.add_argument("--aspects", default="16x9,9x16,1x1")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", default=str(ROOT / "out" / "recovery-video-proof"))
    args = ap.parse_args()

    stem = "recovery-proof-" + args.style
    fixture = ROOT / "fixtures" / stem
    fixture.mkdir(parents=True, exist_ok=True)
    output = Path(args.out).resolve() / stem
    output.mkdir(parents=True, exist_ok=True)

    script = SCRIPTS[args.style]
    raw_voice = fixture / "voice.wav"
    voice = fixture / "voice.mp3"
    # One intact narration track, never sliced into beats.
    run(["espeak-ng", "-s", "133", "-v", "en-us", "-w", raw_voice, script])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw_voice, "-ar", "48000",
         "-ac", "2", "-b:a", "128k", voice])

    duration = duration_ms(voice)
    tokens = script.split()
    total = sum(max(2, len(w.strip(".,!?"))) for w in tokens)
    cursor = 100.0
    usable = max(1200.0, duration - 280.0)
    words = []
    for i, token in enumerate(tokens):
        weight = max(2, len(token.strip(".,!?")))
        width = usable * weight / total
        words.append({"text": token, "start_ms": round(cursor),
                      "end_ms": round(cursor + width * 0.91)})
        cursor += width

    (fixture / "alignment.json").write_text(
        json.dumps({"words": words, "provenance": "CI_APPROXIMATE_WORD_TIMING"}, indent=2))
    treatment = build_treatment(
        SimpleNamespace(aspects=args.aspects), style_of(args.style), words, [], stem)
    treatment["fps"] = args.fps
    treatment["note"] += "; voice: espeak-ng synthetic continuous master"
    (fixture / "treatment.json").write_text(json.dumps(treatment, indent=2))

    # Native compiler produces aspect-specific plans. Never alter audio duration.
    run([sys.executable, "-m", "editorial_plan_compiler", fixture / "treatment.json", output],
        cwd=ROOT / "compiler")
    for aspect in [a.strip() for a in args.aspects.split(",") if a.strip()]:
        plan = output / ("plan_" + aspect + ".json")
        if args.style == "dataviz":
            authored = json.loads(plan.read_text())
            assert authored['director_style'] == 'dataviz', 'Data Viz direction missing'
            assert authored["captions_policy"] == "kinetic", "No duplicate lower thirds"
            assert authored["captions"] == [], "Compiled karaoke captions forbidden"
            assert all(b["typography"]["blocks"] for b in authored["beats"]), "Missing native text"
            for beat in authored["beats"]:
                phrases = [block["words"] for block in beat["typography"]["blocks"] if block.get("words")]
                for earlier, later in zip(phrases, phrases[1:]):
                    assert later[0]["start_ms"] >= earlier[-1]["start_ms"], (
                        "Data Viz sentence timing restarted at an earlier identical word",
                        earlier[-1], later[0])
        if args.style == 'sketch':
            assert json.loads(plan.read_text())['director_style'] == 'sketch', 'Sketch direction missing'
        run(["node", ROOT / "tools" / "render_reel.js", plan, output,
             "--fps", args.fps, "--workers", args.workers, "--preset", "ultrafast",
             "--web-crf", "29"])
    summary = {
        "style": args.style, "script": script,
        "audio_source": "espeak-ng; continuous full-track voice",
        "alignment": "approximate word timing (render smoke test only)",
        "duration_ms": duration, "aspects": args.aspects.split(","),
        "compiled": True,
    }
    (output / "proof.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
