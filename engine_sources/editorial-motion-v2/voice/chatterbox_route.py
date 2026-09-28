#!/usr/bin/env python3
"""Chatterbox text-to-speech route for Studio's NEXSTUDIO_TTS_ROUTES_JSON.

Reads a ``NexStudioAudioProviderRequestV1`` on stdin, synthesises speech with
Resemble AI's open-weight Chatterbox models (MIT license), writes the audio to
``outputPath`` and a scheduled character alignment to
``payload.alignmentOutputPath`` (or ``<outputPath>.alignment.json``), then
prints one JSON line the provider stores as ``providerEvidence``.

Chatterbox emits no measured word timestamps, so the sidecar schedules the
characters evenly across the *generated* audio's real duration; provenance
records ``alignmentSource: EVEN_SCHEDULE_FROM_GENERATED_AUDIO`` so nobody
mistakes it for measured alignment.

Route declaration (default voice engine — no credential required):

    {"id":"chatterbox-turbo","priority":20,"commercialUseAllowed":true,
     "timeoutSeconds":600,
     "command":["python3","engine_sources/editorial-motion-v2/voice/chatterbox_route.py"]}

Requires ``pip install chatterbox-tts`` (pulls torch; GPU host recommended).
Environment:

* ``CHATTERBOX_MODEL``        — ``turbo`` (default), ``standard``, or ``multilingual``.
* ``CHATTERBOX_DEVICE``       — ``cuda``/``cpu``; defaults to cuda when available.
* ``CHATTERBOX_VOICE_PROMPT`` — default reference clip for voice cloning when
  ``payload.voiceId`` does not name one.
* ``CHATTERBOX_TRANSPORT=fixture:<audio-file>`` copies a recorded audio file to
  ``outputPath`` instead of running the model, so the whole route is testable
  without torch or weights.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any, Dict, Optional

MODEL_ENGINES = {
    'turbo': ('chatterbox.tts_turbo', 'ChatterboxTurboTTS'),
    'standard': ('chatterbox.tts', 'ChatterboxTTS'),
    'multilingual': ('chatterbox.mtl_tts', 'ChatterboxMultilingualTTS'),
}
ALIGNMENT_SOURCE = 'EVEN_SCHEDULE_FROM_GENERATED_AUDIO'


def fail(code: str, detail: str = '') -> None:
    sys.stderr.write(f'{code} {detail}\n'.strip() + '\n')
    sys.exit(2)


def load_engine(model_key: str):
    spec = MODEL_ENGINES.get(model_key)
    if not spec:
        fail('CHATTERBOX_MODEL_UNKNOWN', model_key)
    module_name, class_name = spec
    try:
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
    except ImportError as exc:
        fail('CHATTERBOX_PACKAGE_MISSING', f'{module_name}: {exc}')
    device = os.environ.get('CHATTERBOX_DEVICE', '').strip()
    if not device:
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        except ImportError:
            device = 'cpu'
    try:
        model = cls.from_pretrained(device=device)
    except Exception as exc:
        fail('CHATTERBOX_MODEL_LOAD_FAILED', f'{model_key}: {type(exc).__name__} {exc}')
    return model, device


def synthesise(model, text: str, payload: Dict[str, Any], out: Path) -> None:
    settings = payload.get('voiceSettings') or {}
    kwargs: Dict[str, Any] = {}
    voice_prompt = str(payload.get('voiceId') or os.environ.get('CHATTERBOX_VOICE_PROMPT') or '').strip()
    if voice_prompt:
        kwargs['audio_prompt_path'] = voice_prompt
    for param, env_name in (('exaggeration', 'CHATTERBOX_EXAGGERATION'), ('cfg_weight', 'CHATTERBOX_CFG_WEIGHT'), ('temperature', 'CHATTERBOX_TEMPERATURE')):
        value = settings.get(param)
        if value is None:
            raw = os.environ.get(env_name, '').strip()
            value = float(raw) if raw else None
        if value is not None:
            kwargs[param] = value
    language = str(payload.get('languageId') or payload.get('language') or os.environ.get('CHATTERBOX_LANGUAGE') or '').strip()
    if language:
        kwargs['language_id'] = language
    accepted = set(inspect.signature(model.generate).parameters)
    kwargs = {k: v for k, v in kwargs.items() if k in accepted}
    try:
        wav = model.generate(text, **kwargs)
    except Exception as exc:
        fail('CHATTERBOX_GENERATE_FAILED', f'{type(exc).__name__} {exc}')
    import torchaudio as ta
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out if out.suffix.lower() == '.wav' else Path(f'{out}.wav')
    ta.save(str(tmp), wav, model.sr)
    if tmp != out:
        shutil.copyfile(tmp, out)
        tmp.unlink()


def probe_duration(path: Path) -> float:
    try:
        with wave.open(str(path), 'rb') as wf:
            return wf.getnframes() / float(wf.getframerate())
    except Exception:
        pass
    cp = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                         '-of', 'default=nw=1:nk=1', str(path)], capture_output=True, text=True)
    if cp.returncode != 0:
        fail('AUDIO_DURATION_UNKNOWN', str(path))
    try:
        return float(cp.stdout.strip())
    except ValueError:
        fail('AUDIO_DURATION_UNKNOWN', str(path))
    raise AssertionError('unreachable')


def schedule_alignment(text: str, duration: float) -> Dict[str, Any]:
    """Even per-word character schedule over the real audio duration.

    Word timing is proportional to word length with short gaps, so caption
    anchors land plausibly; provenance marks it as scheduled, never measured.
    """
    tokens = text.split()
    if not tokens:
        return {'characters': [], 'character_start_times_seconds': [], 'character_end_times_seconds': [], 'scheduled': True}
    gap = min(0.06, duration * 0.02)
    usable = max(0.01, duration - gap * (len(tokens) - 1))
    total_chars = sum(max(1, len(tok)) for tok in tokens)
    chars, starts, ends = [], [], []
    t = 0.0
    for tok in tokens:
        per_char = (usable * max(1, len(tok)) / total_chars) / max(1, len(tok))
        for ch in tok:
            chars.append(ch)
            starts.append(round(t, 4))
            t += per_char
            ends.append(round(t, 4))
        chars.append(' ')
        starts.append(round(t, 4))
        t += gap
        ends.append(round(t, 4))
    if chars and chars[-1] == ' ':
        chars.pop()
        starts.pop()
        ends.pop()
    if ends:
        scale = duration / ends[-1] if ends[-1] > 0 else 1.0
        starts = [round(min(x * scale, duration), 4) for x in starts]
        ends = [round(min(x * scale, duration), 4) for x in ends]
    return {
        'characters': chars,
        'character_start_times_seconds': starts,
        'character_end_times_seconds': ends,
        'scheduled': True,
    }


def write_alignment(path: Path, text: str, duration: float, meta: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        'schema': 'ChatterboxScheduledAlignmentV1',
        'text': text,
        'alignmentSource': ALIGNMENT_SOURCE,
        **meta,
        'alignment': schedule_alignment(text, duration),
    }, indent=1))


def main() -> None:
    request = json.loads(sys.stdin.read() or '{}')
    if request.get('schema') != 'NexStudioAudioProviderRequestV1' or request.get('kind') != 'TTS':
        fail('UNSUPPORTED_REQUEST')
    payload = request.get('payload') or {}
    text = ' '.join(str(payload.get('text') or '').split())
    if not text:
        fail('TEXT_MISSING')
    out = Path(request.get('outputPath') or os.environ.get('NEXSTUDIO_AUDIO_OUTPUT_PATH') or '')
    if not str(out):
        fail('OUTPUT_PATH_MISSING')
    alignment_out = Path(payload.get('alignmentOutputPath') or f'{out}.alignment.json')

    model_key = os.environ.get('CHATTERBOX_MODEL', 'turbo').strip().lower() or 'turbo'
    transport = os.environ.get('CHATTERBOX_TRANSPORT', 'live')
    evidence: Dict[str, Any] = {'provider': 'chatterbox', 'model': model_key}
    if transport.startswith('fixture:'):
        fixture = Path(transport.split(':', 1)[1])
        if not fixture.exists() or not fixture.is_file():
            fail('CHATTERBOX_FIXTURE_MISSING', str(fixture))
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fixture, out)
        evidence['source'] = 'CHATTERBOX_FIXTURE'
    else:
        model, device = load_engine(model_key)
        synthesise(model, text, payload, out)
        evidence.update({'source': 'CHATTERBOX_TTS_LOCAL', 'device': device})

    if not out.exists() or out.stat().st_size <= 44:
        fail('CHATTERBOX_NO_AUDIO', str(out))
    duration = probe_duration(out)
    evidence['durationSeconds'] = round(duration, 4)
    write_alignment(alignment_out, text, duration, {'model': model_key})
    evidence['alignmentPath'] = str(alignment_out)
    evidence['alignmentSource'] = ALIGNMENT_SOURCE
    evidence['alignmentSha256'] = hashlib.sha256(alignment_out.read_bytes()).hexdigest()

    print(json.dumps({
        'audioPath': str(out),
        'rightsEvidence': {
            'commercialUseAllowed': True,
            'declaredByOperatorRoute': True,
            'provider': 'chatterbox',
            'licenseBasis': 'MODEL_LICENSE_MIT',
        },
        'providerEvidence': evidence,
    }))


if __name__ == '__main__':
    main()
