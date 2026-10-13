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
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

from voice_registry import VOICES, ENGINE_ROOT

def _cpu_threads(name: str) -> int:
    setting = os.environ.get(name, '').strip().lower()
    if not setting or setting == 'auto':
        return max(1, len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1))
    count = int(setting)
    if count < 1:
        raise ValueError(f'{name} must be auto or a positive integer')
    return count


def _alignment_env(threads: int) -> dict:
    env = dict(os.environ)
    if os.environ.get('WHISPER_CPU_THREADS', '').strip().lower() not in ('', 'auto'):
        env.update({name: str(threads) for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')})
    return env



def _synth_kokoro(text: str, entry: dict, out_wav: Path, speed: float = 1.0):
    # A downloaded ONNX bundle keeps these voices fully local, including the
    # phonemizer. The original KPipeline remains available on existing hosts.
    bundle = ENGINE_ROOT.parents[1] / "llm" / "kokoro"
    model = Path(os.environ.get("KOKORO_MODEL_PATH", "").strip() or bundle / "kokoro-v1.0.onnx")
    voices = Path(os.environ.get("KOKORO_VOICES_PATH", "").strip() or bundle / "voices-v1.0.bin")
    configured = bool(os.environ.get("KOKORO_MODEL_PATH", "").strip() or os.environ.get("KOKORO_VOICES_PATH", "").strip())
    if configured or model.exists() or voices.exists():
        if not model.is_file() or not voices.is_file():
            raise RuntimeError("NARRATION_LOCAL_UNAVAILABLE: Kokoro model and voices files are required")
        import onnxruntime as rt
        from kokoro_onnx import Kokoro
        import soundfile as sf
        options = rt.SessionOptions()
        if os.environ.get("KOKORO_CPU_THREADS", "").strip().lower() not in ("", "auto"):
            options.intra_op_num_threads = _cpu_threads("KOKORO_CPU_THREADS")
        session = rt.InferenceSession(str(model), sess_options=options, providers=["CPUExecutionProvider"])
        pipe = Kokoro.from_session(session, str(voices))
        audio, sample_rate = pipe.create(text, voice=entry["kokoro"], speed=speed,
                                         lang="en-gb" if entry["lang"] == "b" else "en-us")
        sf.write(str(out_wav), audio, sample_rate)
        return len(audio) / sample_rate
    from kokoro import KPipeline
    import numpy as np, soundfile as sf
    pipe = KPipeline(lang_code=entry["lang"], repo_id="hexgrad/Kokoro-82M")
    audio = np.concatenate([a for _, _, a in pipe(text, voice=entry["kokoro"], speed=speed)])
    sf.write(str(out_wav), audio, 24000)
    return len(audio) / 24000


def _synth_edge(text: str, entry: dict, out_wav: Path, speed: float = 1.0):
    tmp_mp3 = out_wav.with_suffix(".edge.mp3")
    cmd = [sys.executable, "-m", "edge_tts", "--text", text, "--voice", entry["edge"],
           "--write-media", str(tmp_mp3)]
    if abs(speed - 1.0) > 0.01:
        rate = round((speed - 1.0) * 100)
        cmd += [f"--rate={rate:+d}%"]
    for attempt in range(3):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if result.returncode == 0:
                break
            detail = result.stderr or ""
            retryable = bool(re.search(r"WSServerHandshakeError: (403|429|500|502|503|504)\b", detail)) or any(
                reason in detail for reason in ("NoAudioReceived", "ClientConnectorError", "TimeoutError")
            )
        except subprocess.TimeoutExpired:
            detail = "Narration request timed out."
            retryable = True
        if not retryable or attempt == 2:
            print(detail, file=sys.stderr)
            raise RuntimeError(f"NARRATION_PROVIDER_UNAVAILABLE: {entry['edge']}")
        print(f"[voice] narration request failed; retrying the same voice ({attempt + 1}/2)", flush=True)
        time.sleep(attempt + 1)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(tmp_mp3), "-ar", "24000", str(out_wav)],
        check=True,
    )
    tmp_mp3.unlink(missing_ok=True)
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(out_wav)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip() or 0.0)


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


def synth(text: str, voice: str, out_wav: Path, speed: float = 1.0):
    entry = VOICES[voice]
    engine = entry["engine"]
    if engine == "kokoro":
        return _synth_kokoro(text, entry, out_wav, speed=speed)
    if engine == "edge":
        return _synth_edge(text, entry, out_wav, speed=speed)
    if engine == "chatterbox":
        return _synth_chatterbox(text, entry, out_wav)
    sys.exit(f"unknown engine for voice {voice}: {engine}")


def align(wav: Path, out_json: Path):
    cpu_threads = _cpu_threads("WHISPER_CPU_THREADS")
    local_model = ENGINE_ROOT.parents[1] / "llm" / "whisper-small"
    model_path = os.environ.get("WHISPER_MODEL_PATH", "").strip() or (str(local_model) if (local_model / "model.bin").exists() else "small")
    helper = os.environ.get("WHISPER_PYTHON")
    if helper:
        code = (
            "import json,os,sys\n"
            "from faster_whisper import WhisperModel\n"
            "m = WhisperModel(os.environ['WHISPER_MODEL_PATH'], device='cpu', compute_type='int8', cpu_threads=int(sys.argv[3]))\n"
            "segs,_ = m.transcribe(sys.argv[1], word_timestamps=True)\n"
            "ws=[{'text':w.word,'start_ms':round(w.start*1000),'end_ms':round(w.end*1000)} for s in segs for w in s.words]\n"
            "open(sys.argv[2],'w').write(json.dumps({'words':ws},indent=1))\n"
            "print(len(ws))\n"
        )
        env = dict(_alignment_env(cpu_threads), WHISPER_MODEL_PATH=model_path)
        r = subprocess.run([helper, "-c", code, str(wav), str(out_json), str(cpu_threads)], env=env, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr or r.stdout, file=sys.stderr)
            raise RuntimeError("NARRATION_ALIGNMENT_FAILED: could not prepare narration timing")
        return int((r.stdout or "0").strip() or 0)
    os.environ.update(_alignment_env(cpu_threads))
    from faster_whisper import WhisperModel
    model = WhisperModel(model_path, device="cpu", compute_type="int8", cpu_threads=cpu_threads)
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
