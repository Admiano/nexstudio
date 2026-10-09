"""Still Open Peeps figure resolution from a P8 figure directive.

Selection scores the artwork's authored emotion/posture vectors against the
directive's continuous values (valence, arousal, energy, formality). Tag words
in the library metadata are never consulted — topic words do not choose people.
The result is an exact, hashed part list the renderer composes verbatim.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .contracts import Brand, FigureDirective

PEEPS = Path(__file__).resolve().parents[2] / 'assets' / 'peeps'
INDEX = json.loads((PEEPS / 'parts-index.json').read_text())
SEMANTICS = json.loads((PEEPS / 'semantics.json').read_text())
PARTS: Dict[str, Dict[str, Dict[str, Any]]] = {group: {p['id']: p for p in items} for group, items in INDEX['parts'].items()}

# Novelty faces/heads are excluded from editorial casting by default.
EXCLUDED_FACES = {'monster', 'cyclops', 'angry-with-fang', 'blank', 'eating-happy', 'with-mask-calm', 'with-mask-cheers', 'with-mask-smile'}
EXCLUDED_POSES = {'standing-robot-dance-1', 'standing-robot-dance-2', 'standing-robot-dance-3', 'standing-polka-dots', 'sitting-bike'}
EXCLUDED_HEADS = {'bear', 'doctor-nurse-2', 'doctor-nurse-3'}

# Open Peeps garment colours -> editorial palette roles. Skin (#d08b5b) is remapped to the chosen tone.
GARMENT_SOURCE = ['#9ddadb', '#ffcf77', '#8fa7df', '#78e185', '#9fd8e5', '#e86bbb', '#fdea6b', '#ec7495', '#ba98de', '#ff8181', '#ff6c6c', '#c93305', '#d6b370', '#ecdcbf', '#e8e1e1', '#e6e6e6']
GREYS = ['#d9d9d7', '#bfbfbd', '#e6e6e4', '#cfcfcd']


def _hash(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _score_face(face_id: str, d: FigureDirective) -> float:
    m = SEMANTICS['face'].get(face_id)
    if not m or face_id in EXCLUDED_FACES:
        return -1
    return 1 - (0.62 * abs(m['valence'] - d.valence) / 2 + 0.38 * abs(m['arousal'] - d.arousal))


def _score_pose(pose_id: str, d: FigureDirective) -> float:
    m = SEMANTICS['pose'].get(pose_id)
    if not m or pose_id in EXCLUDED_POSES or m['posture'] != d.posture:
        return -1
    return 1 - (0.55 * abs(m['energy'] - d.energy) + 0.45 * abs(m['formality'] - d.formality))


def _pick(candidates: List[tuple], seed: str) -> str:
    """Best score wins; near-ties (within 0.04) rotate deterministically by seed so a film is not one face."""
    ranked = sorted(candidates, key=lambda x: (-x[0], x[1]))
    top = [c for c in ranked if c[0] >= ranked[0][0] - 0.04]
    return top[int(_hash(seed) * len(top)) % len(top)][1]


class FigurePartError(ValueError):
    """A pinned cast/state part is not in the Open Peeps index — surfaces as a beat gate failure."""


def _part_exists(group: str, part_id: Optional[str], beat_id: str) -> None:
    if part_id and part_id not in PARTS[group]:
        raise FigurePartError(f'FIGURE_PART_UNKNOWN:{group}/{part_id} (beat {beat_id})')


def _score_pose_for(pose_id: str, d: FigureDirective, posture: str) -> float:
    m = SEMANTICS['pose'].get(pose_id)
    if not m or pose_id in EXCLUDED_POSES or m['posture'] != posture:
        return -1
    return 1 - (0.55 * abs(m['energy'] - d.energy) + 0.45 * abs(m['formality'] - d.formality))


def resolve_state_parts(st: Dict[str, Any], comp: Dict[str, Any], posture: str, beat_id: str) -> List[Dict[str, Any]]:
    """Part swaps for one performer state: pose→body slot, face→face slot, head→head slot.
    Returns plan part records shaped exactly like the base parts so the runtime can hot-swap."""
    swaps = []
    for slot, key, group in (('body', 'pose', 'pose'), ('face', 'face', 'face'), ('head', 'head', 'head')):
        pid = str(st.get(key) or '').strip() or None
        if not pid:
            continue
        _part_exists(group, pid, beat_id)
        if group == 'pose' and SEMANTICS['pose'].get(pid, {}).get('posture') not in (None, posture):
            raise FigurePartError(f'FIGURE_POSE_POSTURE_MISMATCH:{pid} wants {SEMANTICS["pose"][pid]["posture"]}, state plays on {posture} (beat {beat_id})')
        p = PARTS[group][pid]
        frame = comp['slots'][slot]
        swaps.append({'slot': slot, 'part_id': pid, 'file': p['file'], 'sha256': _sha(PEEPS / p['file']),
                      'frame': {'x': frame['x'], 'y': frame['y'], 'w': frame['width'], 'h': frame['height']},
                      'source_size': {'w': p['width'], 'h': p['height']}})
    return swaps


def resolve_figure(d: FigureDirective, beat_id: str, film_id: str, brand: Brand, facing_left: bool,
                   cast_member: Any = None, character: Optional[str] = None) -> Dict[str, Any]:
    # A cast member reseeds identity to the character (not the beat), so head/skin/garment stay the
    # same person on every beat they play; only the face may still track the beat's emotion.
    seed = f'{film_id}:cast:{character}' if character else f'{film_id}:{beat_id}'
    member = cast_member if character else None
    face = (member and member.face) or d.face or _pick([(_score_face(f, d), f) for f in PARTS['face']], seed + ':face')
    posture = (member.posture if member and member.posture else d.posture)
    pose = d.pose or _pick([(_score_pose_for(p, d, posture), p) for p in PARTS['pose']], seed + ':pose')
    for pid, group in ((face, 'face'), (pose, 'pose')):
        _part_exists(group, pid, beat_id)
    if SEMANTICS['pose'].get(pose, {}).get('posture') not in (None, posture):
        raise FigurePartError(f'FIGURE_POSE_POSTURE_MISMATCH:{pose} wants {SEMANTICS["pose"][pose]["posture"]}, figure plays {posture} (beat {beat_id})')
    heads = [h for h in PARTS['head'] if h not in EXCLUDED_HEADS]
    head = (member.head if member and member.head else None) or heads[int(_hash(seed + ':head') * len(heads)) % len(heads)]
    _part_exists('head', head, beat_id)
    tones = SEMANTICS['skinTones']['palette']
    tone = (member.skin if member and member.skin else None) or tones[int(_hash(seed + ':skin') * len(tones)) % len(tones)]
    comp = INDEX['compositions'][posture]

    palette = {SEMANTICS['skinTones']['source']: tone, '#000000': brand.ink, '#221e1f': brand.ink, '#231f20': brand.ink}
    order = sorted(GARMENT_SOURCE, key=lambda c: _hash(seed + c))
    for i, src in enumerate(order):
        if i == 0 and brand.accent:
            palette[src] = brand.accent
        else:
            palette[src] = GREYS[i % len(GREYS)]

    parts = []
    for slot, part_id in (('body', pose), ('head', head), ('face', face)):
        p = PARTS['pose' if slot == 'body' else slot][part_id]
        frame = comp['slots'][slot]
        parts.append({
            'slot': slot,
            'part_id': part_id,
            'file': p['file'],
            'sha256': _sha(PEEPS / p['file']),
            'frame': {'x': frame['x'], 'y': frame['y'], 'w': frame['width'], 'h': frame['height']},
            'source_size': {'w': p['width'], 'h': p['height']},
        })
    x0 = min(pt['frame']['x'] for pt in parts)
    y0 = min(pt['frame']['y'] for pt in parts)
    x1 = max(pt['frame']['x'] + pt['frame']['w'] for pt in parts)
    y1 = max(pt['frame']['y'] + pt['frame']['h'] for pt in parts)
    face_meta = SEMANTICS['face'][face]
    pose_meta = SEMANTICS['pose'][pose]
    return {
        'library': 'OPEN_PEEPS',
        'still': True,
        'framing': 'FULL_BODY',
        'posture': posture,
        'character': character,
        'composition': {'view_box': [x0, y0, x1 - x0, y1 - y0], 'aspect': round((x1 - x0) / (y1 - y0), 4), 'posture': posture},
        'parts': parts,
        'palette': palette,
        'mirror': facing_left,
        'facing': d.facing,
        'emotion': {'face': face, 'label': face_meta['emotion'], 'valence': face_meta['valence'], 'arousal': face_meta['arousal']},
        'pose': {'id': pose, 'energy': pose_meta['energy'], 'formality': pose_meta['formality']},
        'justification': d.justification,
        'directive': {'valence': d.valence, 'arousal': d.arousal, 'energy': d.energy, 'formality': d.formality},
    }
