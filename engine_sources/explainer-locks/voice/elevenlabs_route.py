#!/usr/bin/env python3
"""ElevenLabs text-to-speech route for Studio's NEXSTUDIO_TTS_ROUTES_JSON.

Reads a ``NexStudioAudioProviderRequestV1`` on stdin, calls
``POST /v1/text-to-speech/{voice_id}/with-timestamps``, writes the audio to
``outputPath`` and the character alignment to ``payload.alignmentOutputPath``
(or ``<outputPath>.alignment.json``), then prints one JSON line the provider
stores as ``providerEvidence``.

Route declaration (the credential is read from the environment, never from
the request):

    {"id":"elevenlabs","priority":10,"commercialUseAllowed":true,
     "credentialEnv":"ELEVENLABS_API_KEY","timeoutSeconds":120,
     "command":["python3","engine_sources/editorial-motion-v2/voice/elevenlabs_route.py"]}

``ELEVENLABS_TRANSPORT=fixture:<dir>`` replays a recorded response from
``<dir>/<sha256(text)[:16]>.json`` instead of calling the network, so the
whole route is testable without a key.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict

API = 'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps'
DEFAULT_MODEL = 'eleven_multilingual_v2'
OUTPUT_FORMAT = 'mp3_44100_128'


def fail(code: str, detail: str = '') -> None:
    sys.stderr.write(f'{code} {detail}\n'.strip() + '\n')
    sys.exit(2)


def call_api(text: str, voice_id: str, model_id: str, key: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps({'text': text, 'model_id': model_id, 'voice_settings': settings}).encode()
    req = urllib.request.Request(
        API.format(voice_id=voice_id) + f'?output_format={OUTPUT_FORMAT}',
        data=body,
        headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=110) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        fail('ELEVENLABS_HTTP_ERROR', f'{exc.code} {exc.read()[:300]!r}')
    except urllib.error.URLError as exc:
        fail('ELEVENLABS_UNREACHABLE', str(exc.reason))
    raise AssertionError('unreachable')


def fixture_response(text: str, fixture_dir: Path) -> Dict[str, Any]:
    key = hashlib.sha256(text.encode()).hexdigest()[:16]
    path = fixture_dir / f'{key}.json'
    if not path.exists():
        fail('ELEVENLABS_FIXTURE_MISSING', str(path))
    return json.loads(path.read_text())


def main() -> None:
    request = json.loads(sys.stdin.read() or '{}')
    if request.get('schema') != 'NexStudioAudioProviderRequestV1' or request.get('kind') != 'TTS':
        fail('UNSUPPORTED_REQUEST')
    payload = request.get('payload') or {}
    text = ' '.join(str(payload.get('text') or '').split())
    if not text:
        fail('TEXT_MISSING')
    voice_id = str(payload.get('voiceId') or os.environ.get('ELEVENLABS_VOICE_ID') or '').strip()
    if not voice_id:
        fail('VOICE_ID_MISSING', 'payload.voiceId or ELEVENLABS_VOICE_ID')
    model_id = str(payload.get('modelId') or os.environ.get('ELEVENLABS_MODEL_ID') or DEFAULT_MODEL)
    out = Path(request.get('outputPath') or os.environ.get('NEXSTUDIO_AUDIO_OUTPUT_PATH') or '')
    if not str(out):
        fail('OUTPUT_PATH_MISSING')
    alignment_out = Path(payload.get('alignmentOutputPath') or f'{out}.alignment.json')

    transport = os.environ.get('ELEVENLABS_TRANSPORT', 'live')
    if transport.startswith('fixture:'):
        data = fixture_response(text, Path(transport.split(':', 1)[1]))
        source = 'ELEVENLABS_RECORDED_RESPONSE'
    else:
        key = os.environ.get('ELEVENLABS_API_KEY', '').strip()
        if not key:
            fail('ELEVENLABS_API_KEY_MISSING')
        settings = payload.get('voiceSettings') or {'stability': 0.45, 'similarity_boost': 0.8, 'style': 0.25, 'use_speaker_boost': True}
        data = call_api(text, voice_id, model_id, key, settings)
        source = 'ELEVENLABS_LIVE'

    audio_b64 = data.get('audio_base64')
    alignment = data.get('normalized_alignment') or data.get('alignment')
    if not audio_b64 or not alignment:
        fail('ELEVENLABS_RESPONSE_INCOMPLETE', 'audio_base64 and alignment required')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(audio_b64))
    alignment_out.parent.mkdir(parents=True, exist_ok=True)
    alignment_out.write_text(json.dumps({'schema': 'ElevenLabsCharacterAlignmentV1', 'text': text, 'voice_id': voice_id, 'model_id': model_id, 'alignment': alignment}, indent=1))
    print(json.dumps({
        'audioPath': str(out),
        'rightsEvidence': {'commercialUseAllowed': True, 'declaredByOperatorRoute': True, 'provider': 'elevenlabs', 'licenseBasis': 'OPERATOR_SUBSCRIPTION'},
        'providerEvidence': {'provider': 'elevenlabs', 'source': source, 'voiceId': voice_id, 'modelId': model_id, 'alignmentPath': str(alignment_out),
                             'alignmentSha256': hashlib.sha256(alignment_out.read_bytes()).hexdigest(), 'characterCount': len(alignment.get('characters') or [])},
    }))


if __name__ == '__main__':
    main()
