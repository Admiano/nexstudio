"""Hermetic tests for avatar_provider — uses the route's fixture transport so
no torch/weights/GPU are needed (same convention as CHATTERBOX_TRANSPORT)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from avatar_provider import AvatarRouteUnavailable, declared_routes, generate_avatar  # noqa: E402

ROUTE_SCRIPT = Path(__file__).parent.parent.parent / 'engine_sources' / 'editorial-motion-v2' / 'avatar' / 'sadtalker_route.py'


@pytest.fixture
def fixture_video(tmp_path: Path) -> Path:
    clip = tmp_path / 'fixture.mp4'
    cp = subprocess.run(
        ['ffmpeg', '-y', '-loglevel', 'error',
         '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=10',
         '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
         '-pix_fmt', 'yuv420p', '-shortest', str(clip)],
        capture_output=True, text=True)
    assert cp.returncode == 0 and clip.exists()
    return clip


def test_declared_routes_empty(monkeypatch):
    monkeypatch.delenv('NEXSTUDIO_AVATAR_ROUTES_JSON', raising=False)
    assert declared_routes() == []


def test_declared_routes_filters_and_sorts(monkeypatch):
    registry = json.dumps([
        {'id': 'noncommercial', 'priority': 99, 'commercialUseAllowed': False, 'command': ['true']},
        {'id': 'gated', 'priority': 50, 'commercialUseAllowed': True, 'credentialEnv': 'MISSING_KEY_XYZ', 'command': ['true']},
        {'id': 'low', 'priority': 1, 'commercialUseAllowed': True, 'command': ['true']},
        {'id': 'high', 'priority': 20, 'commercialUseAllowed': True, 'command': ['true']},
    ])
    monkeypatch.setenv('NEXSTUDIO_AVATAR_ROUTES_JSON', registry)
    assert [r['id'] for r in declared_routes()] == ['high', 'low']


def test_generate_avatar_fixture_route(monkeypatch, tmp_path, fixture_video):
    registry = json.dumps([{
        'id': 'sadtalker-local', 'priority': 20, 'commercialUseAllowed': True,
        'timeoutSeconds': 120,
        'command': [sys.executable, str(ROUTE_SCRIPT)],
    }])
    monkeypatch.setenv('NEXSTUDIO_AVATAR_ROUTES_JSON', registry)
    monkeypatch.setenv('SADTALKER_TRANSPORT', f'fixture:{fixture_video}')
    out = tmp_path / 'avatar.mp4'
    res = generate_avatar({'imagePath': 'unused.png', 'audioPath': 'unused.wav'}, out)
    assert res['routeId'] == 'sadtalker-local'
    assert out.exists() and out.stat().st_size > 1024
    assert res['durationSeconds'] == pytest.approx(1.0, abs=0.2)
    assert res['width'] == 320 and res['height'] == 240
    assert res['rightsEvidence']['commercialUseAllowed'] is True
    assert res['providerEvidence']['source'] == 'SADTALKER_FIXTURE'


def test_generate_avatar_no_routes(monkeypatch, tmp_path):
    monkeypatch.delenv('NEXSTUDIO_AVATAR_ROUTES_JSON', raising=False)
    with pytest.raises(AvatarRouteUnavailable, match='NO_DECLARED_AVATAR_ROUTE'):
        generate_avatar({'imagePath': 'x.png', 'audioPath': 'x.wav'}, tmp_path / 'o.mp4')
