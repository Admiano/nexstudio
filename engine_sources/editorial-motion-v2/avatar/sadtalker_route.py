#!/usr/bin/env python3
"""SadTalker talking-avatar route for Studio's NEXSTUDIO_AVATAR_ROUTES_JSON.

Reads a ``NexStudioAvatarProviderRequestV1`` on stdin, renders a talking-head
clip from ``payload.imagePath`` + ``payload.audioPath`` with the open-weight
SadTalker model (Apache 2.0 — non-commercial restriction removed upstream),
writes an mp4 to ``outputPath``, then prints one JSON line the provider stores
as ``providerEvidence``.

SadTalker is the CPU-capable tier: image + audio -> lip-synced talking head
with pose/expression. It does not read a motion prompt or generate body/hand
gestures — that tier is the video-diffusion routes (Wan2.2-S2V, OmniAvatar,
HeyGen Avatar IV) which need a GPU host or a hosted API. ``payload.motionHint``
is accepted for contract compatibility and recorded as ignored.

Route declaration (default local avatar engine — no credential required)::

    {"id":"sadtalker-local","priority":20,"commercialUseAllowed":true,
     "timeoutSeconds":3600,
     "command":["python3","engine_sources/editorial-motion-v2/avatar/sadtalker_route.py"]}

Environment:

* ``SADTALKER_ROOT``    — path of a SadTalker checkout containing ``inference.py``
                        and ``checkpoints/`` (default ``~/avatar-lab/SadTalker``).
* ``SADTALKER_PYTHON``  — interpreter with torch + SadTalker deps installed
                        (default ``<SADTALKER_ROOT>/../.venv/bin/python``).
* ``SADTALKER_DEVICE``  — ``cpu``/``cuda``; defaults to cuda when the route's
                        torch reports it available.
* ``SADTALKER_TRANSPORT=fixture:<video-file>`` copies a recorded mp4 to
  ``outputPath`` instead of running the model, so the whole route is testable
  without torch or weights (same convention as CHATTERBOX_TRANSPORT).
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List


def fail(code: str, detail: str = '') -> None:
    sys.stderr.write(f'{code} {detail}\n'.strip() + '\n')
    sys.exit(2)


def build_command(root: Path, image: Path, audio: Path, result_dir: Path,
                  options: Dict[str, Any]) -> List[str]:
    device = os.environ.get('SADTALKER_DEVICE', '').strip().lower()
    if not device:
        try:
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        except ImportError:
            device = 'cpu'
    cmd = [
        str(root.parent / '.venv' / 'bin' / 'python')
        if not os.environ.get('SADTALKER_PYTHON')
        else os.environ['SADTALKER_PYTHON'],
        'inference.py',
        '--driven_audio', str(audio),
        '--source_image', str(image),
        '--result_dir', str(result_dir),
        '--checkpoint_dir', str(root / 'checkpoints'),
        '--preprocess', str(options.get('preprocess') or 'full'),
        '--size', str(int(options.get('size') or 256)),
        '--batch_size', str(int(options.get('batchSize') or 1)),
        '--expression_scale', str(float(options.get('expressionScale') or 1.0)),
    ]
    if options.get('still', True):
        cmd.append('--still')
    enhancer = str(options.get('enhancer') or 'gfpgan')
    if enhancer and enhancer != 'none':
        cmd += ['--enhancer', enhancer]
    if device == 'cpu':
        cmd.append('--cpu')
    extra = os.environ.get('SADTALKER_EXTRA_ARGS', '').strip()
    if extra:
        cmd += extra.split()
    return cmd


def newest_mp4(result_dir: Path) -> Path:
    candidates = sorted(result_dir.glob('**/*.mp4'), key=lambda p: p.stat().st_mtime)
    if not candidates:
        fail('SADTALKER_NO_VIDEO', str(result_dir))
    return candidates[-1]


def main() -> None:
    request = json.loads(sys.stdin.read() or '{}')
    if request.get('schema') != 'NexStudioAvatarProviderRequestV1' or request.get('kind') != 'AVATAR':
        fail('UNSUPPORTED_REQUEST')
    payload = request.get('payload') or {}
    out = Path(request.get('outputPath') or os.environ.get('NEXSTUDIO_AVATAR_OUTPUT_PATH') or '')
    if not str(out):
        fail('OUTPUT_PATH_MISSING')
    out.parent.mkdir(parents=True, exist_ok=True)

    evidence: Dict[str, Any] = {'provider': 'sadtalker'}
    transport = os.environ.get('SADTALKER_TRANSPORT', 'live')
    if transport.startswith('fixture:'):
        fixture = Path(transport.split(':', 1)[1])
        if not fixture.exists() or not fixture.is_file():
            fail('SADTALKER_FIXTURE_MISSING', str(fixture))
        shutil.copyfile(fixture, out)
        evidence['source'] = 'SADTALKER_FIXTURE'
    else:
        image = Path(str(payload.get('imagePath') or ''))
        audio = Path(str(payload.get('audioPath') or ''))
        if not image.exists():
            fail('IMAGE_MISSING', str(image))
        if not audio.exists():
            fail('AUDIO_MISSING', str(audio))
        root = Path(os.environ.get('SADTALKER_ROOT') or '~/avatar-lab/SadTalker').expanduser()
        if not (root / 'inference.py').exists():
            fail('SADTALKER_ROOT_MISSING', str(root))
        options = payload.get('options') or {}
        with tempfile.TemporaryDirectory(prefix='sadtalker-') as td:
            cmd = build_command(root, image, audio, Path(td), options)
            cp = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
            if cp.returncode != 0:
                fail('SADTALKER_INFERENCE_FAILED', (cp.stderr or cp.stdout or '')[-600:])
            shutil.copyfile(newest_mp4(Path(td)), out)
        if payload.get('motionHint'):
            evidence['motionHint'] = 'IGNORED_NOT_SUPPORTED_BY_ROUTE'
        evidence.update({'source': 'SADTALKER_LOCAL', 'options': options})

    if not out.exists() or out.stat().st_size <= 1024:
        fail('SADTALKER_NO_VIDEO', str(out))
    print(json.dumps({
        'videoPath': str(out),
        'rightsEvidence': {
            'commercialUseAllowed': True,
            'declaredByOperatorRoute': True,
            'provider': 'sadtalker',
            'licenseBasis': 'MODEL_LICENSE_APACHE_2_0',
        },
        'providerEvidence': evidence,
    }))


if __name__ == '__main__':
    main()
