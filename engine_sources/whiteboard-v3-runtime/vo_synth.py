"""vo_synth — local $0 voiceover: Kokoro TTS + faster-whisper word timings.

Usage:
    python3 vo_synth.py script.txt out_vo.wav --voice af_sarah --speed 1.0

Writes out_vo.wav (narration) and out_vo_words.json (word timings the
pipelines consume via --word-timings). Both the Kokoro model files and a
whisper model must exist locally; see VO.md for the one-time downloads.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import wave
from pathlib import Path

_DEFAULT_MODEL = Path('/home/ubuntu/voices/kokoro-v0_19.onnx')
_DEFAULT_VOICES = Path('/home/ubuntu/voices/voices.npz')

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



def synth_kokoro(text: str, out_wav: Path, voice: str = 'af_sarah',
                 speed: float = 1.0, model: Path = _DEFAULT_MODEL,
                 voices: Path = _DEFAULT_VOICES) -> Path:
    import numpy as np
    from kokoro_onnx import Kokoro

    kokoro = Kokoro(str(model), str(voices))
    samples, sr = kokoro.create(text, voice=voice, speed=speed,
                                lang='en-us')
    pcm = (np.asarray(samples, dtype=np.float32).clip(-1, 1)
           * 32767).astype(np.int16)
    with wave.open(str(out_wav), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return out_wav


def synth_edge(text: str, out_wav: Path,
               voice: str = 'en-US-EmmaMultilingualNeural',
               speed: float = 1.0) -> Path:
    """Microsoft neural voices via edge-tts: free, no key, needs network."""
    out_wav = Path(out_wav)
    import asyncio
    import subprocess
    import tempfile

    import edge_tts
    heard = []
    words_file = out_wav.with_name(out_wav.stem + '_words.json')
    words_file.unlink(missing_ok=True)

    async def _go(mp3: str) -> None:
        rate = f'{round((speed - 1) * 100):+d}%'
        with open(mp3, 'wb') as audio:
            async for chunk in edge_tts.Communicate(text, voice, rate=rate, boundary='WordBoundary').stream():
                if chunk['type'] == 'audio':
                    audio.write(chunk['data'])
                elif chunk['type'] == 'WordBoundary':
                    heard.append({'word': chunk['text'],
                                  'start': round(chunk['offset'] / 10000000, 3),
                                  'end': round((chunk['offset'] + chunk['duration']) / 10000000, 3)})

    with tempfile.NamedTemporaryFile(suffix='.mp3', dir=out_wav.parent, delete=False) as tmp:
        mp3 = Path(tmp.name)
    try:
        try:
            asyncio.run(asyncio.wait_for(_go(str(mp3)), timeout=90))
        except Exception as error:
            raise RuntimeError(f'NARRATION_PROVIDER_UNAVAILABLE: {voice}') from error
        subprocess.run(
            ['ffmpeg', '-y', '-i', str(mp3), '-ar', '24000', '-ac', '1',
             str(out_wav)], check=True, capture_output=True)
    finally:
        mp3.unlink(missing_ok=True)
    _save_edge_timings(out_wav, words_file, text, heard)
    return out_wav


def align_to_script(heard: list[dict], text: str) -> list[dict]:
    """Script words carrying the recogniser's times: the recogniser may
    mishear ("oilkin" for "oil can"), but the board keys drawings to the
    words actually written, so every script word gets a time."""
    said = text.split()
    norm = [re.sub(r'[^a-z0-9]', '', w.lower()) for w in said]
    got = [re.sub(r'[^a-z0-9]', '', w['word'].lower()) for w in heard]
    sm = difflib.SequenceMatcher(None, norm, got, autojunk=False)
    out: list[dict] = []
    for tag, i0, i1, j0, j1 in sm.get_opcodes():
        if i1 == i0:
            continue
        if j1 > j0:
            t0, t1 = heard[j0]['start'], heard[j1 - 1]['end']
        else:
            t0 = out[-1]['end'] if out else 0.0
            t1 = heard[j0]['start'] if j0 < len(heard) else t0
        step = (t1 - t0) / (i1 - i0)
        for k in range(i1 - i0):
            if tag == 'equal':
                h = heard[j0 + k]
                a, b = h['start'], h['end']
            else:
                a, b = t0 + step * k, t0 + step * (k + 1)
            out.append({'word': said[i0 + k], 'start': round(a, 3),
                        'end': round(b, 3)})
    return out


def _save_edge_timings(wav: Path, output: Path, text: str, heard: list[dict]) -> bool:
    # Missing or incomplete service metadata falls back to the installed model.
    said = text.split()
    normalize = lambda word: re.sub(r'[^a-z0-9]', '', word.lower())
    if not heard or not said or normalize(said[-1]) != normalize(heard[-1]['word']):
        return False
    if len(heard) < len(said) * 0.75:
        return False
    with wave.open(str(wav)) as audio:
        duration = audio.getnframes() / audio.getframerate()
    words = align_to_script(heard, text)
    if any(not 0 <= word['start'] <= word['end'] <= duration + 0.5 or word['start'] > duration for word in words):
        return False
    for word in words:
        word['end'] = min(word['end'], duration)
    output.write_text(json.dumps(words, indent=1))
    return True


def word_timings(wav: Path, out_json: Path,
                 model_size: str = 'base', text: str = '') -> Path:
    cpu_threads = _cpu_threads('WHISPER_CPU_THREADS')
    os.environ.update(_alignment_env(cpu_threads))
    from faster_whisper import WhisperModel

    out_json = Path(out_json)
    local_model = Path(__file__).resolve().parents[2] / 'llm' / 'whisper-small'
    configured = os.environ.get('WHISPER_MODEL_PATH', '').strip()
    selected_model = configured or (str(local_model) if model_size == 'small' and (local_model / 'model.bin').exists() else model_size)
    model = WhisperModel(selected_model, device='cpu', compute_type='int8', cpu_threads=cpu_threads)
    segments, _ = model.transcribe(str(wav), word_timestamps=True)
    words = [{'word': w.word.strip(), 'start': round(w.start, 3),
              'end': round(w.end, 3)}
             for seg in segments for w in (seg.words or [])]
    if text and words:
        words = align_to_script(words, text)
    out_json.write_text(json.dumps(words, indent=1))
    return out_json


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('script', help='narration text file')
    ap.add_argument('out', help='output .wav path')
    ap.add_argument('--engine', choices=('kokoro', 'edge'), default='edge',
                    help='edge = Microsoft neural voices (best $0 quality, '
                         'needs network); kokoro = fully offline')
    ap.add_argument('--voice', default=None,
                    help='engine voice id (kokoro: af_sarah, am_adam, ...; '
                         'edge: en-US-EmmaMultilingualNeural, ...)')
    ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--model', default=str(_DEFAULT_MODEL))
    ap.add_argument('--voices', default=str(_DEFAULT_VOICES))
    ap.add_argument('--whisper-model', default='base')
    args = ap.parse_args()

    out_wav = Path(args.out)
    text = Path(args.script).read_text()
    # authoring hints like [stage: hatch] are markers for plan_author,
    # not narration — never speak them
    text = re.sub(r'\[[^\]]*\]', ' ', text)
    # '# Title' / '## Scene' headings are drawn on the board, not spoken
    text = re.sub(r'(?m)^\s*#.*$', ' ', text).strip()
    if args.engine == 'edge':
        synth_edge(text, out_wav,
                   voice=args.voice or 'en-US-EmmaMultilingualNeural',
                   speed=args.speed)
    else:
        synth_kokoro(text, out_wav, voice=args.voice or 'af_sarah',
                     speed=args.speed, model=Path(args.model),
                     voices=Path(args.voices))
    out_json = out_wav.with_name(out_wav.stem + '_words.json')
    word_timings(out_wav, out_json, model_size=args.whisper_model,
                 text=text)
    print(f'vo: {out_wav}\nwords: {out_json}')


if __name__ == '__main__':
    main()
