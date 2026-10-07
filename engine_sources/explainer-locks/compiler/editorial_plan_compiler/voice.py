"""Per-beat narration audio and character alignment.

Three sources, all producing the same ElevenLabs ``with-timestamps`` alignment
shape so the rest of the compiler never knows which one ran:

* ``RECORDED`` — alignment (and optionally audio) captured from a real
  ElevenLabs response and stored next to the treatment. Deterministic tests.
* ``ROUTE``    — Studio's ``NEXSTUDIO_TTS_ROUTES_JSON`` mechanism; the
  ElevenLabs route in ``voice/elevenlabs_route.py`` writes the alignment
  sidecar and reports it through ``providerEvidence.alignmentPath``.
* ``FIXTURE``  — synthesised cadence, silent audio. Never commercial output;
  provenance marks the film ``FIXTURE_TIMING``.
* ``MASTER``   — one continuous audio file plus one whole-script alignment;
  resolved by ``master_timeline.resolve_master`` (the compiler dispatches
  there before this module is consulted).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .contracts import BeatTreatment, TreatmentError
from .timing import synthesise_alignment

SOURCES = ('RECORDED', 'ROUTE', 'FIXTURE', 'MASTER')


@dataclass
class VoiceSegment:
    beat_id: str
    source: str
    alignment: Optional[Dict[str, Any]]
    audio_path: Optional[str]
    audio_sha256: Optional[str]
    duration_ms: int
    evidence: Dict[str, Any]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _alignment_ms(al: Dict[str, Any]) -> int:
    ends = al.get('character_end_times_seconds') or []
    return int(round(max(ends) * 1000)) if ends else 0


def _silence(out: Path, ms: int) -> Optional[Path]:
    if not shutil.which('ffmpeg'):
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    cp = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                         '-t', f'{max(ms, 1) / 1000:.3f}', '-c:a', 'pcm_s24le', str(out)], capture_output=True, text=True)
    return out if cp.returncode == 0 and out.exists() else None


def _studio_audio_provider():
    here = Path(__file__).resolve()
    candidates = [p / 'services' / 'studio-family-engines' / 'audio_provider.py' for p in here.parents]
    for c in candidates:
        if c.exists():
            spec = importlib.util.spec_from_file_location('studio_audio_provider', c)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise TreatmentError('STUDIO_AUDIO_PROVIDER_NOT_FOUND', 'services/studio-family-engines/audio_provider.py is required for ROUTE voice')


def resolve_voice(beats: List[BeatTreatment], voice_cfg: Dict[str, Any], work_dir: Path, base_dir: Path, film_id: str) -> List[VoiceSegment]:
    source = str(voice_cfg.get('source') or 'FIXTURE').upper()
    if source not in SOURCES:
        raise TreatmentError('VOICE_SOURCE_UNKNOWN', source)
    segments: List[VoiceSegment] = []
    recorded: Dict[str, Any] = voice_cfg.get('segments') or {}
    provider = _studio_audio_provider() if source == 'ROUTE' else None
    for b in beats:
        if not b.narration:
            segments.append(VoiceSegment(b.beat_id, 'NONE', None, None, None, 0, {'reason': 'BEAT_HAS_NO_NARRATION'}))
            continue
        if source == 'RECORDED':
            rec = recorded.get(b.beat_id)
            if not rec or not rec.get('alignment_path'):
                raise TreatmentError('RECORDED_ALIGNMENT_MISSING', 'RECORDED voice needs an alignment for every narrated beat', b.beat_id)
            al_path = (base_dir / rec['alignment_path']).resolve()
            alignment = json.loads(al_path.read_text())
            alignment = alignment.get('alignment', alignment)
            spoken = ''.join(alignment['characters']).strip()
            if ' '.join(spoken.split()) != b.narration:
                raise TreatmentError('RECORDED_ALIGNMENT_TEXT_MISMATCH', 'alignment characters do not spell the beat narration', b.beat_id)
            audio = (base_dir / rec['audio_path']).resolve() if rec.get('audio_path') else None
            ms = _alignment_ms(alignment)
            if audio is None:
                audio = _silence(work_dir / 'voice' / f'{b.beat_id}.wav', ms)
            segments.append(VoiceSegment(b.beat_id, 'RECORDED', alignment, str(audio) if audio else None, _sha(audio) if audio else None, ms,
                                         {'alignment_path': str(al_path), 'alignment_sha256': _sha(al_path), 'audio_is_placeholder': not rec.get('audio_path')}))
        elif source == 'ROUTE':
            out = work_dir / 'voice' / f'{b.beat_id}.wav'
            out.parent.mkdir(parents=True, exist_ok=True)
            payload = {'text': b.narration, 'voiceId': voice_cfg.get('voice_id'), 'modelId': voice_cfg.get('model_id'), 'beatId': b.beat_id, 'filmId': film_id}
            res = provider.generate_audio('TTS', payload, out)
            al_path = res.get('providerEvidence', {}).get('alignmentPath')
            if not al_path or not Path(al_path).exists():
                raise TreatmentError('ROUTE_ALIGNMENT_MISSING', f"route {res.get('routeId')} returned no character alignment", b.beat_id)
            alignment = json.loads(Path(al_path).read_text())
            alignment = alignment.get('alignment', alignment)
            segments.append(VoiceSegment(b.beat_id, 'ROUTE', alignment, res['path'], _sha(Path(res['path'])), int(float(res['durationSeconds']) * 1000),
                                         {'route_id': res.get('routeId'), 'rights': res.get('rightsEvidence'), 'provider': res.get('providerEvidence')}))
        else:
            alignment = synthesise_alignment(b.narration, f'{film_id}:{b.beat_id}', float(voice_cfg.get('words_per_second') or 2.6))
            ms = _alignment_ms(alignment)
            audio = _silence(work_dir / 'voice' / f'{b.beat_id}.wav', ms)
            segments.append(VoiceSegment(b.beat_id, 'FIXTURE', alignment, str(audio) if audio else None, _sha(audio) if audio else None, ms,
                                         {'reason': 'FIXTURE_TIMING', 'audio_is_placeholder': True}))
    return segments
