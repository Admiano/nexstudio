#!/usr/bin/env python3
"""Generate a VO track for a fixture using a studio voice.

Voices come from tools/voice_registry.py across three engines: local Kokoro-82M
(CPU, Apache 2.0), Microsoft Edge neural voices (edge-tts, free cloud endpoint),
and Chatterbox-Turbo clones (MIT, needs `pip install chatterbox-tts`).

Usage:
  python3 tools/generate_voice.py --script "A few years ago, ..." --voice andrew --out fixtures/ai-leverage
  python3 tools/generate_voice.py --script-file script.txt --voice heart --out fixtures/my-film

Produces <out>/voice.mp3 and <out>/alignment.json (faster-whisper word timings),
the two files a MASTER-voice treatment expects.
"""
import argparse, json, subprocess, sys
from pathlib import Path

from voice_registry import VOICES, ENGINE_ROOT


def _synth_kokoro(text: str, entry: dict, out_wav: Path):
    from kokoro import KPipeline
    import numpy as np, soundfile as sf
    pipe = KPipeline(lang_code=entry["lang"], repo_id="hexgrad/Kokoro-82M")
    audio = np.concatenate([a for _, _, a in pipe(text, voice=entry["kokoro"])])
    sf.write(str(out_wav), audio, 24000)
    return len(audio) / 24000


def _synth_edge(text: str, entry: dict, out_wav: Path):
    tmp_mp3 = out_wav.with_suffix(".edge.mp3")
    subprocess.run(
        [sys.executable, "-m", "edge_tts", "--text", text, "--voice", entry["edge"],
         "--write-media", str(tmp_mp3)],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(tmp_mp3), "-ar", "24000", str(out_wav)],
        check=True,
    )
    tmp_mp3.unlink(missing_ok=True)
    import soundfile as sf
    return len(sf.read(str(out_wav))[0]) / 24000


def _synth_chatterbox(text: str, entry: dict, out_wav: Path):
    try:
        from chatterbox.tts_turbo import ChatterboxTurboTTS
    except ImportError:
        sys.exit("chatterbox-tts not installed on this host (pip install chatterbox-tts)")
    import torchaudio as ta
    ref = ENGINE_ROOT / entry["ref"]
    if not ref.exists():
        sys.exit(f"clone reference missing: {ref}")
    model = ChatterboxTurboTTS.from_pretrained(device="cpu")
    wav = model.generate(text, audio_prompt_path=str(ref))
    ta.save(str(out_wav), wav, model.sr)
    return wav.shape[-1] / model.sr


def synth(text: str, voice: str, out_wav: Path):
    entry = VOICES[voice]
    engine = entry["engine"]
    if engine == "kokoro":
        return _synth_kokoro(text, entry, out_wav)
    if engine == "edge":
        return _synth_edge(text, entry, out_wav)
    if engine == "chatterbox":
        return _synth_chatterbox(text, entry, out_wav)
    sys.exit(f"unknown engine for voice {voice}: {engine}")


def align(wav: Path, out_json: Path):
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(wav), word_timestamps=True)
    words = []
    for seg in segments:
        for w in seg.words:
            words.append({"text": w.word, "start_ms": round(w.start * 1000), "end_ms": round(w.end * 1000)})
    out_json.write_text(json.dumps({"words": words}, indent=1))
    return len(words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", help="VO script text")
    ap.add_argument("--script-file", help="Path to a text file with the VO script")
    ap.add_argument("--voice", required=True, choices=sorted(VOICES))
    ap.add_argument("--out", required=True, help="Fixture dir (or any dir) to write voice.mp3 + alignment.json")
    args = ap.parse_args()

    text = args.script or (Path(args.script_file).read_text() if args.script_file else None)
    if not text or not text.strip():
        sys.exit("Provide --script or --script-file")
    text = text.strip()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    wav, mp3, ali = out / "voice.wav", out / "voice.mp3", out / "alignment.json"

    dur = synth(text, args.voice, wav)
    n = align(wav, ali)

    import subprocess
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "4", str(mp3)], check=True)
    print(f"voice={args.voice} dur={dur:.1f}s words={n} -> {mp3} + {ali}")


if __name__ == "__main__":
    main()
