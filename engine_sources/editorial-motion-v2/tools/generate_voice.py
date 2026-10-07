#!/usr/bin/env python3
"""Generate a VO track for a fixture using embedded Kokoro-82M (CPU, no API).

Usage:
  python3 tools/generate_voice.py --script "A few years ago, ..." --voice bm_george --out fixtures/ai-leverage
  python3 tools/generate_voice.py --script-file script.txt --voice af_bella --out fixtures/my-film

Produces <out>/voice.mp3 and <out>/alignment.json (faster-whisper word timings),
the two files a MASTER-voice treatment expects.
"""
import argparse, json, sys
from pathlib import Path

VOICES = {
    # US
    "af_bella": "a", "af_sarah": "a", "am_onyx": "a", "am_adam": "a",
    # UK
    "bf_emma": "b", "bf_isabella": "b", "bm_george": "b", "bm_lewis": "b",
}


def synth(text: str, voice: str, out_wav: Path):
    from kokoro import KPipeline
    import numpy as np, soundfile as sf
    pipe = KPipeline(lang_code=VOICES[voice], repo_id="hexgrad/Kokoro-82M")
    audio = np.concatenate([a for _, _, a in pipe(text, voice=voice)])
    sf.write(str(out_wav), audio, 24000)
    return len(audio) / 24000


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
