#!/usr/bin/env python3
"""NexStudio whiteboard job runner.

One production request -> VO (Microsoft edge-tts) -> plan -> one render per
aspect -> manifest.json the /api/v1/whiteboards route collects.

    python3 tools/nexstudio_job.py --script script.txt --type kinetic \
        --theme light --accent '#2f6fb3' --voice emma \
        --aspects '16:9,1x1,9:16' --out out/job --job-id wb-abc12345
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

VOICES = {
    "emma": "en-US-EmmaMultilingualNeural",
    "ava": "en-US-AvaMultilingualNeural",
    "andrew": "en-US-AndrewMultilingualNeural",
    "brian": "en-US-BrianMultilingualNeural",
    "sonia": "en-GB-SoniaNeural",
    "natasha": "en-AU-NatashaNeural",
}

PIPELINES = {
    "kinetic": "pipeline_kinetic_timed.py",
    "board": "pipeline_v3_narration_timed.py",
}


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if proc.returncode != 0:
        raise RuntimeError(f"STAGE_FAILED {Path(cmd[1]).name}: {proc.stderr[-1500:]}")
    return proc


def build_voice(args, script_text: str | None, work: Path) -> tuple[Path, Path | None]:
    vo_wav = work / "vo.wav"
    if args.voice_file:
        src = Path(args.voice_file)
        if src.suffix.lower() == ".wav":
            shutil.copy(src, vo_wav)
        else:
            sh(["ffmpeg", "-y", "-i", str(src), "-ar", "24000", "-ac", "1", str(vo_wav)])
        return vo_wav, None

    import vo_synth
    # authoring hints like [stage: hatch] steer the plan, not the narration
    text = re.sub(r"\[[^\]]*\]", " ", script_text or "").strip()
    if not text:
        raise RuntimeError("VOICE_REQUIRED: script produced no narration text")
    vo_synth.synth_edge(text, vo_wav, voice=VOICES[args.voice])
    words = work / "vo_words.json"
    try:
        vo_synth.word_timings(vo_wav, words)
        return vo_wav, words
    except Exception:
        return vo_wav, None


def build_plan(args, script_text: str, work: Path) -> Path:
    import plan_author
    plan = plan_author.build_plan(
        script_text,
        vtype="whiteboard" if args.type == "board" else "kinetic",
        title=args.title,
    )
    plan_path = work / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=1))
    return plan_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--script", help="narration script text file (one beat per line)")
    ap.add_argument("--voice-file", help="uploaded narration audio; replaces TTS")
    ap.add_argument("--voice", default="emma", choices=sorted(VOICES))
    ap.add_argument("--type", required=True, choices=sorted(PIPELINES))
    ap.add_argument("--theme", default="light", choices=("light", "dark"))
    ap.add_argument("--accent", default=None, help="highlight hex color (kinetic)")
    ap.add_argument("--title", default="NEXSTUDIO")
    ap.add_argument("--aspects", default="16:9,1x1,9:16")
    ap.add_argument("--out", required=True)
    ap.add_argument("--job-id", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="wbjob-", dir=out))

    script_text = Path(args.script).read_text() if args.script else None
    if not script_text and not args.voice_file:
        raise RuntimeError("SCRIPT_REQUIRED: send --script or --voice-file")

    vo_wav, words_json = build_voice(args, script_text, work)
    plan_path = build_plan(args, script_text or "", work)

    pipeline = ROOT / PIPELINES[args.type]
    outputs: dict[str, str] = {}
    for aspect in [a.strip() for a in args.aspects.split(",") if a.strip()]:
        ratio_dir = out / aspect.replace(":", "x")
        cmd = [sys.executable, str(pipeline), str(plan_path),
               "--out-dir", str(ratio_dir), "--ratio", aspect,
               "--theme", args.theme, "--voiceover", str(vo_wav)]
        if words_json:
            cmd += ["--word-timings", str(words_json)]
        if args.accent:
            cmd += ["--accent", args.accent]
        sh(cmd, cwd=ROOT)
        mp4s = sorted(ratio_dir.glob("*.mp4"))
        if mp4s:
            outputs[aspect] = str(mp4s[0])

    (out / "manifest.json").write_text(json.dumps(
        {"jobId": args.job_id, "outputs": outputs}, indent=1))
    print(json.dumps({"ok": True, "outputs": outputs}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"WHITEBOARD_JOB_FAILED: {e}", file=sys.stderr)
        raise SystemExit(1)
