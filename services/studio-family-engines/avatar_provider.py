"""Talking-avatar video route registry — sibling of audio_provider.py.

Routes are operator-declared subprocesses in ``NEXSTUDIO_AVATAR_ROUTES_JSON``
(same shape as ``NEXSTUDIO_TTS_ROUTES_JSON``). Each route reads a
``NexStudioAvatarProviderRequestV1`` JSON on stdin, renders a talking-avatar
clip from ``payload.imagePath`` + ``payload.audioPath`` (+ optional
``payload.motionHint``), writes an mp4, and prints one JSON line the provider
stores as ``providerEvidence``.

Route declaration example::

    [{"id":"sadtalker-local","priority":20,"commercialUseAllowed":true,
      "timeoutSeconds":3600,
      "command":["python3","engine_sources/editorial-motion-v2/avatar/sadtalker_route.py"]}]

Routes are filtered like audio routes: ``commercialUseAllowed`` must be true
and ``credentialEnv`` (when set) must be populated, so a key-gated route drops
out automatically when its credential is absent.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from contracts import AdapterBlocked


class AvatarRouteUnavailable(RuntimeError):
    pass


def declared_routes(env_name: str = 'NEXSTUDIO_AVATAR_ROUTES_JSON') -> List[Dict[str, Any]]:
    raw = os.environ.get(env_name, '').strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise AdapterBlocked('AVATAR_ROUTE_REGISTRY_INVALID', f'{env_name}:{type(exc).__name__}')
    if isinstance(parsed, dict):
        parsed = parsed.get('routes') or []
    if not isinstance(parsed, list):
        raise AdapterBlocked('AVATAR_ROUTE_REGISTRY_INVALID', f'{env_name}:routes')
    routes = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        rid = str(item.get('id') or '').strip()
        cmd = item.get('command')
        if not rid or not isinstance(cmd, list) or not cmd or not all(isinstance(x, str) and x.strip() for x in cmd):
            continue
        if item.get('commercialUseAllowed') is not True:
            continue
        credential = str(item.get('credentialEnv') or '').strip()
        if credential and not os.environ.get(credential, '').strip():
            continue
        routes.append({**item, 'id': rid, 'priority': int(item.get('priority') or 0), 'command': list(cmd)})
    return sorted(routes, key=lambda x: (-x['priority'], x['id']))


def _probe(path: Path) -> Dict[str, Any]:
    cp = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-show_entries', 'stream=codec_type,width,height,r_frame_rate',
         '-of', 'json', str(path)],
        capture_output=True, text=True)
    if cp.returncode != 0:
        raise AvatarRouteUnavailable('generated video could not be probed')
    try:
        info = json.loads(cp.stdout)
        duration = float(info['format']['duration'])
        v = next(s for s in info['streams'] if s.get('codec_type') == 'video')
        return {'durationSeconds': duration, 'width': int(v['width']), 'height': int(v['height'])}
    except Exception:
        raise AvatarRouteUnavailable('generated video metadata invalid')


def generate_avatar(payload: Dict[str, Any], out: Path) -> Dict[str, Any]:
    """payload: {imagePath, audioPath, motionHint?, options?}; out: normalized mp4 path."""
    routes = declared_routes()
    if not routes:
        raise AvatarRouteUnavailable('NO_DECLARED_AVATAR_ROUTE')
    failures = []
    out.parent.mkdir(parents=True, exist_ok=True)
    for route in routes:
        with tempfile.TemporaryDirectory(prefix='nexstudio-avatar-') as td:
            raw = Path(td) / 'generated-video.mp4'
            env = {
                **os.environ,
                'NEXSTUDIO_AVATAR_OUTPUT_PATH': str(raw),
                'NEXSTUDIO_AVATAR_ROUTE_ID': route['id'],
            }
            request = {
                'schema': 'NexStudioAvatarProviderRequestV1',
                'kind': 'AVATAR',
                'routeId': route['id'],
                'payload': payload,
                'outputPath': str(raw),
                'requirements': {
                    'commercialUseAllowed': True,
                    'noTrainingRightsAssumption': True,
                    'videoWithAudio': True,
                },
            }
            try:
                cp = subprocess.run(
                    route['command'], input=json.dumps(request), text=True,
                    capture_output=True, env=env,
                    timeout=int(route.get('timeoutSeconds') or 1800))
                if cp.returncode != 0:
                    failures.append(f"{route['id']}:exit-{cp.returncode}:{(cp.stderr or '').strip()[-200:]}")
                    continue
                meta = {}
                if cp.stdout.strip():
                    try:
                        meta = json.loads(cp.stdout.strip().splitlines()[-1])
                    except Exception:
                        meta = {}
                generated = Path(str(meta.get('videoPath') or raw))
                if not generated.exists() or generated.stat().st_size <= 1024:
                    failures.append(f"{route['id']}:no-video")
                    continue
                norm = out
                conv = subprocess.run(
                    ['ffmpeg', '-y', '-loglevel', 'error', '-i', str(generated),
                     '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                     '-movflags', '+faststart',
                     '-c:a', 'aac', '-ar', '48000', '-ac', '2', '-b:a', '160k',
                     '-shortest', str(norm)],
                    capture_output=True, text=True)
                if conv.returncode != 0 or not norm.exists():
                    failures.append(f"{route['id']}:normalize-failed")
                    continue
                return {
                    'path': str(norm),
                    'routeId': route['id'],
                    **_probe(norm),
                    'rightsEvidence': meta.get('rightsEvidence') or {
                        'commercialUseAllowed': True,
                        'declaredByOperatorRoute': True,
                    },
                    'providerEvidence': meta.get('providerEvidence') or {},
                }
            except subprocess.TimeoutExpired:
                failures.append(f"{route['id']}:timeout")
            except Exception as exc:
                failures.append(f"{route['id']}:{type(exc).__name__}")
    raise AvatarRouteUnavailable(';'.join(failures) or 'NO_WORKING_AVATAR_ROUTE')
