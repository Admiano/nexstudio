"""Bind supplied recordings to P8-authored speech without choosing or rewriting it."""
import hashlib
import json
import math
from pathlib import Path
import subprocess

from contracts import AdapterBlocked


def recorded_segments(request, beats):
    bindings = (request.get('executionPlan') or {}).get('executionBindings')
    if bindings is None:
        bindings = request.get('executionBindings') or {}
    contract = bindings.get('recordedNarration')
    if contract is None:
        return None
    if not isinstance(contract, dict) or contract.get('schema') != 'StudioRecordedNarrationV1':
        raise AdapterBlocked('RECORDED_NARRATION_CONTRACT_INVALID')
    segments = contract.get('segments')
    if not isinstance(segments, list) or not segments:
        raise AdapterBlocked('RECORDED_NARRATION_CONTRACT_INVALID', 'segments')
    voiced = {b['beat_id']: b for b in beats if b.get('narration_mode') == 'VOICEOVER'}
    resolved = {}
    for segment in segments:
        if not isinstance(segment, dict):
            raise AdapterBlocked('RECORDED_NARRATION_CONTRACT_INVALID', 'segment')
        ident = segment.get('beatId')
        if not isinstance(ident, str) or ident not in voiced or ident in resolved:
            raise AdapterBlocked('RECORDED_NARRATION_BEAT_MISMATCH', str(ident))
        if segment.get('text') != voiced[ident].get('narration_text'):
            raise AdapterBlocked('RECORDED_NARRATION_TEXT_MISMATCH', ident)
        path = Path(str(segment.get('path') or ''))
        if not path.is_absolute() or not path.is_file():
            raise AdapterBlocked('RECORDED_NARRATION_SOURCE_MISSING', ident)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != segment.get('sha256'):
            raise AdapterBlocked('RECORDED_NARRATION_SOURCE_CHANGED', ident)
        rights = segment.get('rightsEvidence')
        if not isinstance(rights, dict) or not rights.get('source') or not rights.get('authorization'):
            raise AdapterBlocked('RECORDED_NARRATION_RIGHTS_MISSING', ident)
        try:
            probe = json.loads(subprocess.check_output(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(path)], text=True))
            duration = float(probe['format']['duration'])
        except (subprocess.CalledProcessError, ValueError, KeyError):
            raise AdapterBlocked('RECORDED_NARRATION_AUDIO_INVALID', ident)
        if not math.isfinite(duration) or duration <= 0:
            raise AdapterBlocked('RECORDED_NARRATION_AUDIO_INVALID', ident)
        resolved[ident] = {'path': str(path), 'sha256': digest, 'durationSeconds': duration,
                           'routeId': 'SUPPLIED_RECORDED_NARRATION', 'rightsEvidence': rights}
    if set(resolved) != set(voiced):
        raise AdapterBlocked('RECORDED_NARRATION_BEAT_MISMATCH', 'Every VOICEOVER beat needs its exact supplied recording')
    return resolved
